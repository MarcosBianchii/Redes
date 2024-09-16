from __future__ import annotations
from typing import Iterator
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from .packet import PKT_HEADER_SIZE, Packet

ACK_TIMEOUT = 0.1
SYN_ACK_TIMEOUT = 0.1
SYN_ACK_DUP_TIMEOUT = ACK_TIMEOUT + SYN_ACK_TIMEOUT


def _sendall(skt: socket, data: bytes, addr):
    sent = 0
    while sent < len(data):
        sent += skt.sendto(data[sent:], addr)


class RdpSocket:
    def __init__(self, peer_addr):
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._peer_addr = peer_addr

    @classmethod
    def connect(cls, ip: str, port: int) -> RdpSocket:
        """
        Establishes a new connection to a RdpListener
        """
        self = cls((ip, port))

        # Send SYN
        syn_pkt = Packet.syn_pkt()
        syn_bytes = syn_pkt.encode()
        self._skt.settimeout(SYN_ACK_TIMEOUT)

        while True:
            _sendall(self._skt, syn_bytes, self.peer_addr())
            try:
                # Receive SYN + ACK
                header, peer_addr = self._skt.recvfrom(PKT_HEADER_SIZE)
                pkt = Packet.from_header(header)
                if pkt.is_syn() and pkt.is_ack():
                    self._peer_addr = peer_addr
                    break
            except timeout:
                continue

        # Send ACK
        ack_pkt = Packet.ack_pkt()
        ack_bytes = ack_pkt.encode()
        self._skt.settimeout(SYN_ACK_DUP_TIMEOUT)

        while True:
            _sendall(self._skt, ack_bytes, self.peer_addr())
            try:
                # Don't receive anything for SYN_ACK_DUP_TIMEOUT
                header = self._skt.recv(PKT_HEADER_SIZE)
            except timeout:
                break

            pkt = Packet.from_header(header)
            if not pkt.is_syn() or not pkt.is_ack():
                raise Exception(f"Received ({pkt}) unexpectedly")

            # Received a duplicated SYN + ACK packet, which
            # means our last ACK never reached the other end

        return self

    def peer_addr(self):
        return self._peer_addr

    def recv(self, size: int) -> bytes:
        """
        Blocks the main thread until `size` amounts of data arrive through the socket
        """
        pass

    def send(self, data: bytes):
        """
        Sends the bytes in `data` through the socket
        """
        self.settimeout(ACK_TIMEOUT)

        for pkt in Packet.make_pkts(data):
            pkt_bytes = pkt.encode()
            while True:
                _sendall(self._skt, pkt_bytes, self.peer_addr())

                try:
                    header = self._skt.recv(PKT_HEADER_SIZE)
                except timeout:
                    continue

                response = Packet.from_header(header)
                if response.is_ack_of(pkt):
                    break

    def settimeout(self, timeout: float):
        self._skt.settimeout(timeout)

    def close(self):
        self._skt.close()


class RdpListener:
    def __init__(self, port: int):
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._skt.bind(("127.0.0.1", port))

    @classmethod
    def bind(cls, port: int):
        return cls(port)

    def accept(self) -> RdpSocket:
        """
        Blocks the main thread until a new connection arrives to this socket
        and returns a new `RdpSocket` which links to that connection
        """
        while True:
            # Wait for SYN packets from other sockets
            header, peer_addr = self._skt.recvfrom(PKT_HEADER_SIZE)
            pkt = Packet.from_header(header)
            if pkt.is_syn():
                break

        # Create new socket and send SYN + ACK
        stream = RdpSocket(peer_addr)
        syn_ack = Packet.syn_ack_pkt()
        syn_ack_bytes = syn_ack.encode()
        stream.settimeout(ACK_TIMEOUT)

        while True:
            _sendall(stream._skt, syn_ack_bytes, stream.peer_addr())
            try:
                # Receive ACK
                header = stream._skt.recv(PKT_HEADER_SIZE)
            except timeout:
                continue

            pkt = Packet.from_header(header)
            if pkt.is_ack():
                break

        return stream

    def __iter__(self) -> Iterator[RdpSocket]:
        """
        Returns an iterator over incoming connections
        """
        while True:
            yield self.accept()

    def close(self):
        self._skt.close()
