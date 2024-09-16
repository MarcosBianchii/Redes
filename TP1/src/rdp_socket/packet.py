from __future__ import annotations
from typing import Iterator

UDP_HEADER_SIZE = 8
RDP_HEADER_SIZE = 8
MAX_PKT_SIZE = 16  # 2 ** 16 - UDP_HEADER_SIZE
RDP_DATA_SIZE = MAX_PKT_SIZE - RDP_HEADER_SIZE

ACK_MASK = 1 << 15
SYN_MASK = 1 << 14
LST_MASK = 1 << 13

"""
                            RDP HEADER

                     1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               |A|S|L|                         |
|         RESERVED              |C|Y|S|       RESERVED          |
|                               |K|N|T|                         |
+-------------------------------+-+-+-+-------------------------+
|                            SEQ NUM                            |
+---------------------------------------------------------------+
|                                                               |
.                              DATA                             .
.                                                               .

"""


class InvalidHeaderSize(Exception):
    def __str__(self) -> str:
        return f"The size of the header is not {RDP_HEADER_SIZE}"


class PacketBuilder:
    def __init__(self):
        self._ack = False
        self._syn = False
        self._lst = False
        self._seq_num = 0
        self._data = bytes()

    def ack(self, value: bool) -> PacketBuilder:
        self._ack = value
        return self

    def syn(self, value: bool) -> PacketBuilder:
        self._syn = value
        return self

    def lst(self, value: bool) -> PacketBuilder:
        self._lst = value
        return self

    def seq_num(self, value: int) -> PacketBuilder:
        self._seq_num = value
        return self

    def data(self, value: bytes) -> PacketBuilder:
        self._data = value
        return self

    def build(self) -> Packet:
        return Packet(self._ack, self._syn, self._lst, self._seq_num, self._data)


class Packet:
    def __init__(self, ack: bool, syn: bool, lst: bool, seq_num: int, data: bytes):
        self._ack = ack
        self._syn = syn
        self._lst = lst
        self._seq_num = seq_num
        self._data = data

    @classmethod
    def from_bytes(cls, pkt_bytes: bytes) -> Packet:
        flags = int.from_bytes(pkt_bytes[2:4], "big")
        ack = flags & ACK_MASK != 0
        syn = flags & SYN_MASK != 0
        lst = flags & LST_MASK != 0
        seq_num = int.from_bytes(pkt_bytes[4:8], "big")
        data = pkt_bytes[RDP_HEADER_SIZE:]
        return cls.builder()  \
            .ack(ack)         \
            .syn(syn)         \
            .lst(lst)         \
            .seq_num(seq_num) \
            .data(data)       \
            .build()

    @classmethod
    def builder(cls) -> PacketBuilder:
        return PacketBuilder()

    @classmethod
    def ack_pkt(cls, seq_num: int) -> Packet:
        return cls.builder()  \
            .seq_num(seq_num) \
            .ack(True)        \
            .build()

    @classmethod
    def syn_pkt(cls) -> Packet:
        return cls.builder()  \
            .syn(True)        \
            .build()

    @classmethod
    def syn_ack_pkt(cls) -> Packet:
        return cls.builder()  \
            .ack(True)        \
            .syn(True)        \
            .build()

    def is_syn(self) -> bool:
        return self._syn

    def is_ack(self) -> bool:
        return self._ack

    def is_lst(self) -> bool:
        return self._lst

    def is_ack_of(self, pkt: Packet) -> bool:
        return self.is_ack() and self._seq_num == pkt._seq_num

    def seq_num(self) -> int:
        return self._seq_num

    def data(self) -> bytes:
        return self._data

    @classmethod
    def _RDP_DATA_SIZE_chunks(cls, data: bytes) -> Iterator[bytes]:
        for i in range(0, len(data), RDP_DATA_SIZE):
            bot = i
            top = min(i + RDP_DATA_SIZE, len(data))
            yield data[bot:top]

    @classmethod
    def make_pkts(cls, data: bytes) -> Iterator[Packet]:
        lst_pos = (len(data) - 1) // RDP_DATA_SIZE
        for seq_num, data in enumerate(cls._RDP_DATA_SIZE_chunks(data)):
            yield cls.builder()          \
                .lst(seq_num == lst_pos) \
                .seq_num(seq_num)        \
                .data(data)              \
                .build()

    def encode(self) -> bytes:
        """
        Turns the packet into bytes
        """
        ack = ACK_MASK * self.is_ack()
        syn = SYN_MASK * self.is_syn()
        lst = LST_MASK * self.is_lst()
        flags = int.to_bytes(ack | syn | lst, 2, "big")
        seq_num = self._seq_num.to_bytes(4, "big")
        return int.to_bytes(0, 2, "big") + flags + seq_num + self.data()

    def __str__(self) -> str:
        return f"ack: {self._ack}, syn: {self._syn}, lst: {self._lst}, seq_num: {self._seq_num}"
