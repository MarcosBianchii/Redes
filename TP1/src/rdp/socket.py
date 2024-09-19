from __future__ import annotations
from typing import Iterator
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from .segment import Segment, MAX_SEG_SIZE, RDP_HEADER_SIZE, MAX_SEQ_NUM

TIMEOUT = 0.5
MAX_RETRY_COUNT = 10


class RdpStream:
    def __init__(self, peer_addr: tuple[str, int]):
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._peer_addr = peer_addr
        self._seq_ofs = 0
        self._ack_ofs = 0

    @classmethod
    def connect(cls, ip: str, port: int) -> RdpStream:
        """
        Establishes a new connection to a RdpListener
        """
        self = cls((ip, port))
        syn_seg = Segment.syn_seg()
        syn_bytes = syn_seg.encode()
        self._skt.settimeout(TIMEOUT)

        while True:
            self._sendall(syn_bytes)
            try:
                # Wait for SYNACK from the new connection
                seg_bytes, peer_addr = self._skt.recvfrom(RDP_HEADER_SIZE)
            except timeout:
                continue

            seg = Segment.from_bytes(seg_bytes)
            if seg.is_syn() and seg.is_ack():
                self._peer_addr = peer_addr
                break

        # Send ACK
        ack_seg = Segment.ack_seg(0)
        self._sendall(ack_seg.encode())
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
            seg, addr = self._skt.recvfrom(MAX_SEG_SIZE)
            if self.peer_addr() == addr:
                return seg

    def _advance_seq_ofs(self, quantity: int):
        self._seq_ofs = (self._seq_ofs + quantity) % MAX_SEQ_NUM

    def _advance_ack_ofs(self, quantity: int):
        self._ack_ofs = (self._ack_ofs + quantity) % MAX_SEQ_NUM

    def recv(self) -> bytes:
        """
        Blocks the main thread until a new message arrives through the socket
        """
        self.settimeout(None)
        data = bytes()

        while True:
            seg_bytes = self._recv_from_peer()
            seg = Segment.from_bytes(seg_bytes)
            print(f"[RECV] SEG({seg.seq_num()}), expected: {self._ack_ofs}")
            if seg.is_syn() and seg.is_ack():
                # Our handshake ACK didn't reach
                # the other side, resend and retry
                ack_seg = Segment.ack_seg(0)
                self._sendall(ack_seg.encode())
                continue

            # Lost segment
            if seg.is_syn() or seg.is_ack():
                continue

            # Only ACK segments that are less
            # than or equal to the ACK offset
            if seg.seq_num() <= self._ack_ofs:
                ack_seg = Segment.ack_seg(seg.seq_num())
                print(f"[SEND] ACK({ack_seg.seq_num()})")
                self._sendall(ack_seg.encode())

                if seg.seq_num() == self._ack_ofs:
                    self._advance_ack_ofs(1)

                    # Take the seg data
                    data += seg.unwrap()
                    if seg.is_lst():
                        break

        return data

    def send(self, data: bytes):
        """
        Sends the bytes in `data` through the socket
        """
        self.settimeout(TIMEOUT)
        retries = 0

        for seg in Segment.make_segments(data, self._seq_ofs):
            seg_bytes = seg.encode()
            while True:
                if seg.is_lst() and retries == MAX_RETRY_COUNT:
                    break

                print(f"[SEND] SEG({seg.seq_num()})")
                self._sendall(seg_bytes)
                try:
                    seg_bytes = self._recv_from_peer()
                except timeout:
                    retries += 1
                    continue

                res = Segment.from_bytes(seg_bytes)
                if res.is_syn() and res.is_ack():
                    # Our handshake ACK didn't reach
                    # the other end, resend and retry
                    ack_seg = Segment.ack_seg(0)
                    self._sendall(ack_seg.encode())
                    return self.send(data)

                if res.is_ack() and res.seq_num() < self._seq_ofs:
                    # The last ACK of the previous call to recv
                    # didn't reach the other end, send ACK
                    ack_seg = Segment.ack_seg(res.seq_num())
                    self._sendall(ack_seg.encode())

                if res.is_ack() and res.seq_num() == self._seq_ofs:
                    print(f"[RECV] ACK({seg.seq_num()})")
                    self._advance_seq_ofs(1)
                    retries = 0
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

    def accept(self) -> RdpStream:
        """
        Blocks the main thread until a new connection arrives to this socket
        and returns a new `RdpStream` which links to that connection
        """
        while True:
            # Wait for SYN segments for new connections
            seg_bytes, peer_addr = self._skt.recvfrom(RDP_HEADER_SIZE)
            seg = Segment.from_bytes(seg_bytes)
            if seg.is_syn() and peer_addr not in self._conns:
                self._conns.add(peer_addr)
                break

        # Send SYNACK to peer from a new socket
        stream = RdpStream(peer_addr)
        syn_ack = Segment.syn_ack_seg()
        syn_ack_bytes = syn_ack.encode()
        stream.settimeout(TIMEOUT)

        while True:
            stream._sendall(syn_ack_bytes)
            try:
                # Wait to receive ACK of SYNACK
                seg_bytes = stream._recv_from_peer()
            except timeout:
                continue

            seg = Segment.from_bytes(seg_bytes)
            if seg.is_ack() and seg.seq_num() == 0:
                break

        return stream

    def __iter__(self) -> Iterator[RdpStream]:
        """
        Returns an iterator over incoming connections
        """
        while True:
            yield self.accept()

    def close(self):
        self._skt.close()
