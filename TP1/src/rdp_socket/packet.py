from __future__ import annotations
from typing import Iterator

PKT_HEADER_SIZE = 8
MAX_PKT_SIZE = 2 ** 16
PKT_DATA_SIZE = MAX_PKT_SIZE - PKT_HEADER_SIZE

ACK_MASK = 1 << 15
SYN_MASK = 1 << 14

"""
                            RDP HEADER

                     1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               |A|S|                           |
|             SIZE              |C|Y|         RESERVED          |
|                               |K|N|                           |
+-------------------------------+-+-+---------------------------+
|                            SEQ NUM                            |
+---------------------------------------------------------------+
|                                                               |
.                              DATA                             .
.                                                               .

"""


class InvalidHeaderSize(Exception):
    def __str__(self) -> str:
        return f"The size of the header is not {PKT_HEADER_SIZE}"


class PacketBuilder:
    def __init__(self):
        self._ack = False
        self._syn = False
        self._seq_num = 0
        self._data = bytes()

    def ack(self, value: bool) -> PacketBuilder:
        self._ack = value
        return self

    def syn(self, value: bool) -> PacketBuilder:
        self._syn = value
        return self

    def seq_num(self, value: int) -> PacketBuilder:
        self._seq_num = value
        return self

    def data(self, value: bytes) -> PacketBuilder:
        self._data = value
        return self

    def build(self) -> Packet:
        size = PKT_HEADER_SIZE + len(self._data)
        return Packet(size, self._ack, self._syn, self._seq_num, self._data)


class Packet:
    def __init__(self, size: int, ack: bool, syn: bool, seq_num: int, data: bytes):
        self._size = size
        self._ack = ack
        self._syn = syn
        self._seq_num = seq_num
        self._data = data

    @classmethod
    def from_header(cls, header: bytes) -> Packet:
        """
        Creates an empty header packet from header bytes
        """
        if len(header) != PKT_HEADER_SIZE:
            raise InvalidHeaderSize()

        size = int.from_bytes(header[0:2], "big")
        flags = int.from_bytes(header[2:4], "big")
        ack = flags & ACK_MASK != 0
        syn = flags & SYN_MASK != 0
        seq_num = int.from_bytes(header[4:8], "big")
        return cls(size, ack, syn, seq_num, bytes())

    @classmethod
    def builder(cls) -> PacketBuilder:
        return PacketBuilder()

    @classmethod
    def syn_pkt(cls) -> Packet:
        return cls.builder() \
            .syn(True)       \
            .build()

    @classmethod
    def syn_ack_pkt(cls) -> Packet:
        return cls.builder() \
            .ack(True)       \
            .syn(True)       \
            .build()

    def is_syn(self) -> bool:
        return self._syn

    def is_ack(self) -> bool:
        return self._ack

    def is_ack_of(self, pkt: Packet) -> bool:
        return self.is_ack() and self._seq_num == pkt._seq_num

    @classmethod
    def _pkt_data_size_chunks(cls, data: bytes) -> Iterator[bytes]:
        for i in range(0, len(data), PKT_DATA_SIZE):
            bot = i
            top = min(i + PKT_DATA_SIZE, len(data))
            yield data[bot:top]

    @classmethod
    def make_pkts(cls, data: bytes) -> Iterator[Packet]:
        for seq_num, pkt_data in enumerate(cls._pkt_data_size_chunks(data)):
            yield cls.builder()   \
                .seq_num(seq_num) \
                .data(pkt_data)   \
                .build()

    def encode(self) -> bytes:
        """
        Turns the packet into bytes
        """
        size = self._size.to_bytes(2, "big")
        flags = (ACK_MASK * self._ack) | (SYN_MASK * self._syn)
        flags = int.to_bytes(flags, 2, "big")
        seq_num = self._seq_num.to_bytes(4, "big")
        return size + flags + seq_num + self._data

    def __str__(self) -> str:
        return f"size: {self._size}, ack: {self._ack}, syn: {self._syn}, seq_num: {self._seq_num}"
