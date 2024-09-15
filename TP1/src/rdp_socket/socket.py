from __future__ import annotations
from typing import Iterator
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from .packet import PKT_HEADER_SIZE, Packet

SYN_TIMEOUT = 1
ACK_TIMEOUT = 1


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

        while True:
            syn_pkt = Packet.syn_pkt()
            _sendall(self._skt, syn_pkt.encode(), self.peer_addr())

            try:
                self._skt.settimeout(SYN_TIMEOUT)
                header, peer_addr = self._skt.recvfrom(PKT_HEADER_SIZE)
            except timeout:
                continue

            pkt = Packet.from_header(header)
            if pkt.is_syn() and pkt.is_ack():
                self._peer_addr = peer_addr
                break

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
        for pkt in Packet.make_pkts(data):
            pkt_bytes = pkt.encode()
            while True:
                _sendall(self._skt, pkt_bytes, self.peer_addr())

                try:
                    self.settimeout(ACK_TIMEOUT)
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

    @classmethod
    def _create_stream(cls, peer_addr) -> RdpSocket:
        stream = RdpSocket(peer_addr)
        syn_ack = Packet.syn_ack_pkt()
        _sendall(stream._skt, syn_ack.encode(), peer_addr)
        return stream

    def close(self):
        self._skt.close()

    def accept(self) -> RdpSocket:
        """
        Blocks the main thread until a new connection arrives to this socket
        and returns a new `RdpSocket` which links to that connection
        """
        while True:
            try:
                header, addr = self._skt.recvfrom(PKT_HEADER_SIZE)
            except KeyboardInterrupt:
                self.close()
                raise
            except:
                continue

            pkt = Packet.from_header(header)
            if pkt.is_syn() and not pkt.is_ack():
                return self._create_stream(addr)

    def __iter__(self) -> Iterator[RdpSocket]:
        """
        Returns an iterator over incoming connections
        """
        while True:
            yield self.accept()