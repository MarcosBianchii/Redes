from __future__ import annotations
from .segment import Segment, MAX_SEG_SIZE, RDP_HEADER_SIZE, MAX_SEQ_NUM
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from .log.verbose import VerboseLogger
from heapq import heappush, heappop
from .log.quiet import QuietLogger
from typing import Iterator
from time import time

TIMEOUT = 0.075
MAX_RETRY_COUNT = 20


class RdpStream:
    def __init__(self, peer_addr: tuple[str, int], log: bool):
        self._log = VerboseLogger() if log else QuietLogger()
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._addr = self._skt.getsockname()
        self._peer_addr = peer_addr
        self._seq_ofs = 0

    @classmethod
    def connect(cls, ip: str, port: int, log: bool = False) -> RdpStream:
        """
        Establishes a new connection to a RdpListener.
        """
        self = cls((ip, port), log)
        syn_seg = Segment.syn_seg()
        self._skt.settimeout(TIMEOUT)

        while True:
            self._sendall(syn_seg)
            try:
                # Wait for SYNACK from the new connection.
                seg_bytes, peer_addr = self._skt.recvfrom(RDP_HEADER_SIZE)
            except timeout:
                continue

            seg = Segment.from_bytes(seg_bytes)
            self._log.recv(seg)

            if seg.is_syn() and seg.is_ack():
                self._peer_addr = peer_addr
                break

        ack_seg = Segment.ack_seg(0)
        self._sendall(ack_seg)
        self._log.connection_established(peer_addr)
        return self

    def _sendall(self, seg: Segment):
        """
        Sends all the contents in `data` through the socket.
        """
        data = seg.encode()
        self._log.send(seg)
        sent = 0
        while sent < len(data):
            sent += self._skt.sendto(data[sent:], self.peer_addr())

    def _recv_from_peer(self) -> bytes:
        """
        Read the socket for the next message from our peer connection.
        """
        while True:
            seg, addr = self._skt.recvfrom(MAX_SEG_SIZE)
            if self.peer_addr() == addr:
                return seg

    def _recv_seg(self) -> Segment:
        """
        Blocks the main thread until a new segment arrives through the socket.
        If a SYNACK segment arrives will try and finish establishing the
        connection with the other end.
        """
        seg_bytes = self._recv_from_peer()
        seg = Segment.from_bytes(seg_bytes)
        self._log.recv(seg)

        if seg.is_syn() and seg.is_ack():
            # Our handshake ACK didn't reach
            # the other side, resend and retry.
            ack_seg = Segment.ack_seg(0)
            self._sendall(ack_seg)
            return self._recv_seg()

        return seg

    def _advance_seq_ofs(self, quantity: int):
        self._seq_ofs = (self._seq_ofs + quantity) % MAX_SEQ_NUM

    def recv(self, winsize: int = 1) -> bytes:
        """
        locks the main thread until a new segment arrives through the socket.
        """
        self.settimeout(None)
        already_received = set()
        data = bytearray()
        received = []

        while True:
            seg = self._recv_seg()

            if not seg.is_ack() and seg.seq_num() < self._seq_ofs + winsize:
                ack_seg = Segment.ack_seg(seg.seq_num())
                self._sendall(ack_seg)

                if seg.seq_num() not in already_received:
                    already_received.add(seg.seq_num())
                    heappush(received, (seg.seq_num(), seg))

                while received and received[0][0] == self._seq_ofs:
                    self._advance_seq_ofs(1)
                    _, seg = heappop(received)

                    data.extend(seg.unwrap())
                    if seg.is_lst():
                        return data

    def send(self, data: bytes, winsize: int = 1):
        """
        Sends the bytes in `data` through the socket.
        """
        self.settimeout(TIMEOUT)
        segs_to_send = list(Segment.make_segments(data, self._seq_ofs))
        winsize = min(winsize, len(segs_to_send))
        send_time = [0] * len(segs_to_send)
        retries = [-1] * len(segs_to_send)
        max_retry = 0

        a = 0
        b = winsize
        ackd = set()

        while max_retry < MAX_RETRY_COUNT:
            now = time()
            for i in range(a, b):
                if now - send_time[i] >= TIMEOUT:
                    self._sendall(segs_to_send[i])
                    send_time[i] = now
                    retries[i] += 1
                    max_retry = max(max_retry, retries[i])

            try:
                res = self._recv_seg()
            except timeout:
                continue

            if res.is_ack() and res.seq_num() < self._seq_ofs + winsize:
                ackd.add(res.seq_num())

                if res.seq_num() == self._seq_ofs:
                    ackds = 0
                    while self._seq_ofs in ackd:
                        ackd.remove(self._seq_ofs)
                        ackds += 1

                    a += ackds
                    self._advance_seq_ofs(ackds)
                    b = min(b + ackds, len(segs_to_send))

                    if segs_to_send[a - 1].is_lst():
                        break

            if not res.is_ack():
                if res.seq_num() < self._seq_ofs:
                    # The other side is still sending a data
                    # segment from a previous call to recv.
                    ack_seg = Segment.ack_seg(res.seq_num())
                    self._sendall(ack_seg)
                else:
                    # We didn't receive their last ACK
                    # and are still trying to send the
                    # last segment.
                    self._advance_seq_ofs(len(segs_to_send) - a)
                    return

    def addr(self) -> tuple[str, int]:
        return self._addr

    def peer_addr(self) -> tuple[str, int]:
        return self._peer_addr

    def settimeout(self, timeout: float):
        self._skt.settimeout(timeout)

    def close(self):
        self._skt.close()


class RdpListener:
    def __init__(self, addr: tuple[str, int], log: bool):
        self._log = VerboseLogger() if log else QuietLogger()
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._skt.bind(addr)
        self._conns = set()
        self._addr = addr

    @classmethod
    def bind(cls, ip: str, port: int, log: bool = False) -> RdpListener:
        """
        Creates a new `RdpListener` and binds it to the given address.
        """
        return cls((ip, port), log)

    def accept(self) -> RdpStream:
        """
        Blocks the main thread until a new connection arrives to this socket
        and returns a new `RdpStream` which links to that connection.
        """
        self._log.awaiting_connections(self.addr())

        while True:
            # Wait for SYN segments for new connections
            seg_bytes, peer_addr = self._skt.recvfrom(RDP_HEADER_SIZE)
            seg = Segment.from_bytes(seg_bytes)
            self._log.recv(seg)

            if seg.is_syn() and peer_addr not in self._conns:
                self._conns.add(peer_addr)
                break

        # Send SYNACK to peer from a new socket
        stream = RdpStream(peer_addr, isinstance(self._log, VerboseLogger))
        syn_ack_seg = Segment.syn_ack_seg()
        stream.settimeout(TIMEOUT)

        while True:
            stream._sendall(syn_ack_seg)
            try:
                # Wait to receive ACK of SYNACK
                seg_bytes = stream._recv_from_peer()
            except timeout:
                continue

            seg = Segment.from_bytes(seg_bytes)
            self._log.recv(seg)

            if seg.is_ack() and seg.seq_num() == 0:
                break

        self._log.connection_established(peer_addr)
        return stream

    def __iter__(self) -> Iterator[RdpStream]:
        """
        Returns an iterator over incoming connections.
        """
        while True:
            yield self.accept()

    def addr(self) -> tuple[str, int]:
        return self._addr

    def close(self):
        self._skt.close()
