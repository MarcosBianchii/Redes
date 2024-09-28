from __future__ import annotations
from .segment import Segment, MAX_SEG_SIZE, RDP_HEADER_SIZE, MAX_SEQ_NUM
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from .log.verbose import VerboseLogger
from typing import Iterator, Optional
from .log.quiet import QuietLogger
from time import time

TIMEOUT = 0.08
MAX_TIMEOUT_COUNT = 20


class Hangup(Exception):
    pass


class RdpStream:
    def __init__(self, peer_addr: tuple[str, int], log: bool):
        self._log = VerboseLogger() if log else QuietLogger()
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._addr = self._skt.getsockname()
        self._peer_addr = peer_addr
        self._closed = False
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

    def _validate_open(self):
        if self._closed:
            raise Hangup("The socket has already been closed")

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

    def _settimeout(self, timeout: Optional[float]):
        self._skt.settimeout(timeout)

    def recv(self, winsize: int = 1) -> bytes:
        """
        Blocks the main thread until a new segment arrives through the socket.
        """
        self._validate_open()
        self._settimeout(None)
        data = bytearray()
        received = {}

        while True:
            seg = self._recv_seg()

            if seg.is_fin():
                raise Hangup("The other end closed the connection")

            if not seg.is_ack() and seg.seq_num() < self._seq_ofs + winsize:
                ack_seg = Segment.ack_seg(seg.seq_num())
                self._sendall(ack_seg)

                received[seg.seq_num()] = seg
                while self._seq_ofs in received:
                    seg = received.pop(self._seq_ofs)
                    self._advance_seq_ofs(1)
                    data.extend(seg.unwrap())
                    if seg.is_lst():
                        return data

    def send(self, data: bytes, winsize: int = 1):
        """
        Sends the bytes in `data` through the socket.
        """
        self._validate_open()
        segs_to_send = list(Segment.make_segments(data, self._seq_ofs))
        winsize = min(winsize, len(segs_to_send))
        send_time = [0] * len(segs_to_send)

        a = 0
        b = winsize
        ackd = set()

        while True:
            self._settimeout(None)
            for i in range(a, b):
                seg = segs_to_send[i]
                if seg.seq_num() not in ackd:
                    now = time()
                    if now - send_time[i] >= TIMEOUT:
                        self._sendall(seg)
                        send_time[i] = now

            try:
                self._settimeout(TIMEOUT)
                res = self._recv_seg()
            except timeout:
                continue

            if res.is_ack() and res.seq_num() < self._seq_ofs + winsize:
                ackd.add(res.seq_num())

                if res.seq_num() == self._seq_ofs:
                    while self._seq_ofs in ackd:
                        ackd.remove(self._seq_ofs)
                        self._advance_seq_ofs(1)
                        a += 1
                        b = min(b + 1, len(segs_to_send))

                    if segs_to_send[a - 1].is_lst():
                        return

            elif not res.is_ack():
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
        self._validate_open()
        return self._addr

    def peer_addr(self) -> tuple[str, int]:
        self._validate_open()
        return self._peer_addr

    def close(self):
        if self._closed:
            return

        fin_seg = Segment.fin_seg(self._seq_ofs)
        timeouts = 0

        while timeouts < MAX_TIMEOUT_COUNT:
            self._settimeout(None)
            self._sendall(fin_seg)

            try:
                self._settimeout(TIMEOUT)
                res = self._recv_seg()
                timeouts = 0
            except timeout:
                timeouts += 1
                continue

            if res.is_fin():
                ack_seg = Segment.ack_seg(res.seq_num())
                self._sendall(ack_seg)
                break

            if res.is_ack() and res.seq_num() == fin_seg.seq_num():
                break

        self._closed = True
        self._skt.close()


class RdpListener:
    def __init__(self, addr: tuple[str, int], log: bool):
        self._log = VerboseLogger() if log else QuietLogger()
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._skt.bind(addr)
        self._logging = log
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
        stream = RdpStream(peer_addr, log=self._logging)
        syn_ack_seg = Segment.syn_ack_seg()

        while True:
            stream._settimeout(None)
            stream._sendall(syn_ack_seg)
            try:
                # Wait to receive ACK of SYNACK
                stream._settimeout(TIMEOUT)
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
