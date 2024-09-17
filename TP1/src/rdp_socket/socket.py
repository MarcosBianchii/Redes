from __future__ import annotations
from typing import Iterator
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from .packet import Packet, MAX_PKT_SIZE, RDP_HEADER_SIZE

TIMEOUT = 0.2


class RdpSocket:
    def __init__(self, peer_addr: tuple[str, int]):
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._peer_addr = peer_addr

    @classmethod
    def connect(cls, ip: str, port: int) -> RdpSocket:
        """
        Establishes a new connection to a RdpListener
        """
        self = cls((ip, port))
        syn_pkt = Packet.syn_pkt()
        syn_bytes = syn_pkt.encode()
        self._skt.settimeout(TIMEOUT)

        while True:
            self._sendall(syn_bytes)
            try:
                # Wait for SYNACK from the new connection
                pkt_bytes, peer_addr = self._skt.recvfrom(RDP_HEADER_SIZE)
            except timeout:
                continue

            pkt = Packet.from_bytes(pkt_bytes)
            if pkt.is_syn() and pkt.is_ack():
                self._peer_addr = peer_addr
                break

        # Send ACK
        ack = Packet.ack_pkt(0)
        self._sendall(ack.encode())
        return self

    def _sendall(self, data: bytes):
        """
        Sends all the contents in `data` through the socket
        """
        sent = 0
        while sent < len(data):
            sent += self._skt.sendto(data[sent:], self.peer_addr())

    def _recv_from_peer(self) -> bytes:
        """
        Read the socket for the next message from our peer connection
        """
        while True:
            pkt, addr = self._skt.recvfrom(MAX_PKT_SIZE)
            if self.peer_addr() == addr:
                return pkt

    def recv(self) -> bytes:
        """
        Blocks the main thread until a new message arrives through the socket
        """
        self.settimeout(None)
        data = bytes()
        ack_num = -1

        while True:
            pkt_bytes = self._recv_from_peer()
            pkt = Packet.from_bytes(pkt_bytes)
            if pkt.is_syn() and pkt.is_ack():
                # Our handshake ACK didn't reach
                # the other side, resend and retry
                ack_pkt = Packet.ack_pkt(0)
                self._sendall(ack_pkt.encode())
                continue

            if pkt.is_ack() or pkt.is_syn():
                # A lost packet
                continue

            if pkt.seq_num() == ack_num:
                continue

            # Respond with an ACK of this pkt
            ack_pkt = Packet.ack_pkt(pkt.seq_num())
            self._sendall(ack_pkt.encode())
            ack_num = pkt.seq_num()

            # Take the pkt data
            data += pkt.data()
            if pkt.is_lst():
                break

        return data

    def send(self, data: bytes):
        """
        Sends the bytes in `data` through the socket
        """
        self.settimeout(TIMEOUT)

        for pkt in Packet.make_pkts(data):
            pkt_bytes = pkt.encode()
            while True:
                self._sendall(pkt_bytes)
                try:
                    pkt_bytes = self._recv_from_peer()
                except timeout:
                    continue

                response = Packet.from_bytes(pkt_bytes)
                if response.is_syn() and response.is_ack():
                    # Our handshake ACK didn't reach
                    # the other side, resend and retry
                    ack_pkt = Packet.ack_pkt(0)
                    self._sendall(ack_pkt.encode())
                    return self.send(data)

                if response.is_ack_of(pkt):
                    break

    def peer_addr(self) -> tuple[str, int]:
        return self._peer_addr

    def settimeout(self, timeout: float):
        self._skt.settimeout(timeout)

    def close(self):
        self._skt.close()


class RdpListener:
    def __init__(self, addr: tuple[str, int]):
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._skt.bind(addr)
        self._conns = set()

    @classmethod
    def bind(cls, ip: str, port: int) -> RdpListener:
        """
        Creates a new RdpListener and binds it to the given address
        """
        return cls((ip, port))

    def accept(self) -> RdpSocket:
        """
        Blocks the main thread until a new connection arrives to this socket
        and returns a new `RdpSocket` which links to that connection
        """
        while True:
            # Wait for SYN packets for new connections
            pkt_bytes, peer_addr = self._skt.recvfrom(RDP_HEADER_SIZE)
            pkt = Packet.from_bytes(pkt_bytes)
            if pkt.is_syn() and peer_addr not in self._conns:
                self._conns.add(peer_addr)
                break

        # Send SYNACK to peer from a new socket
        stream = RdpSocket(peer_addr)
        syn_ack = Packet.syn_ack_pkt()
        syn_ack_bytes = syn_ack.encode()
        stream.settimeout(TIMEOUT)

        while True:
            stream._sendall(syn_ack_bytes)
            try:
                # Wait to receive ACK of SYNACK
                pkt_bytes = stream._recv_from_peer()
            except timeout:
                continue

            pkt = Packet.from_bytes(pkt_bytes)
            if pkt.is_ack_of(syn_ack):
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
