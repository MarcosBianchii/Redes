from __future__ import annotations
from typing import Iterator

UDP_HEADER_SIZE = 8
RDP_HEADER_SIZE = 4
MAX_SEG_SIZE = 8  # 2 ** 16 - UDP_HEADER_SIZE
RDP_DATA_SIZE = MAX_SEG_SIZE - RDP_HEADER_SIZE
MAX_SEQ_NUM = 2 ** 24

ACK_MASK = 1 << 7
SYN_MASK = 1 << 6
LST_MASK = 1 << 5

"""
                           RDP HEADER

                     1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|A|S|L|         |                                               |
|C|Y|S|  FLAGS  |                    SEQ NUM                    |
|K|N|T|         |                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
.                             DATA                              .
.                                                               .

"""


class SegmentBuilder:
    def __init__(self):
        self._ack = False
        self._syn = False
        self._lst = False
        self._seq_num = 0
        self._data = bytes()

    def ack(self, value: bool) -> SegmentBuilder:
        self._ack = value
        return self

    def syn(self, value: bool) -> SegmentBuilder:
        self._syn = value
        return self

    def lst(self, value: bool) -> SegmentBuilder:
        self._lst = value
        return self

    def seq_num(self, value: int) -> SegmentBuilder:
        self._seq_num = value
        return self

    def data(self, value: bytes) -> SegmentBuilder:
        self._data = value
        return self

    def build(self) -> Segment:
        return Segment(self._ack, self._syn, self._lst, self._seq_num, self._data)


class Segment:
    def __init__(self, ack: bool, syn: bool, lst: bool, seq_num: int, data: bytes):
        self._ack = ack
        self._syn = syn
        self._lst = lst
        self._seq_num = seq_num
        self._data = data

    @classmethod
    def from_bytes(cls, seg_bytes: bytes) -> Segment:
        flags = seg_bytes[0]
        ack = flags & ACK_MASK != 0
        syn = flags & SYN_MASK != 0
        lst = flags & LST_MASK != 0
        seq_num = int.from_bytes(seg_bytes[1:4], "big")
        data = seg_bytes[RDP_HEADER_SIZE:]
        return cls.builder()  \
            .ack(ack)         \
            .syn(syn)         \
            .lst(lst)         \
            .seq_num(seq_num) \
            .data(data)       \
            .build()

    @classmethod
    def builder(cls) -> SegmentBuilder:
        return SegmentBuilder()

    @classmethod
    def ack_seg(cls, seq_num: int) -> Segment:
        return cls.builder()  \
            .seq_num(seq_num) \
            .ack(True)        \
            .build()

    @classmethod
    def syn_seg(cls) -> Segment:
        return cls.builder()  \
            .syn(True)        \
            .build()

    @classmethod
    def syn_ack_seg(cls) -> Segment:
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

    def seq_num(self) -> int:
        return self._seq_num

    def unwrap(self) -> bytes:
        return self._data

    @classmethod
    def _seg_data_size_chunks(cls, data: bytes) -> Iterator[bytes]:
        for i in range(0, len(data), RDP_DATA_SIZE):
            bot = i
            top = min(i + RDP_DATA_SIZE, len(data))
            yield data[bot:top]

    @classmethod
    def make_segments(cls, data: bytes, seq_ofs: int) -> Iterator[Segment]:
        lst_pos = (len(data) - 1) // RDP_DATA_SIZE
        for i, data in enumerate(cls._seg_data_size_chunks(data)):
            yield cls.builder()       \
                .lst(i == lst_pos)    \
                .seq_num(seq_ofs + i) \
                .data(data)           \
                .build()

    def encode(self) -> bytes:
        """
        Turns the segment into bytes
        """
        ack = ACK_MASK * self.is_ack()
        syn = SYN_MASK * self.is_syn()
        lst = LST_MASK * self.is_lst()
        flags = int.to_bytes(ack | syn | lst, 1, "big")
        seq_num = self.seq_num().to_bytes(3, "big")
        return flags + seq_num + self.unwrap()

    def __str__(self) -> str:
        return f"ack: {self._ack}, syn: {self._syn}, lst: {self._lst}, seq_num: {self._seq_num}"
