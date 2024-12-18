from __future__ import annotations
from typing import Iterator

MAX_SEG_SIZE = 1028
RDP_HEADER_SIZE = 4
RDP_DATA_SIZE = MAX_SEG_SIZE - RDP_HEADER_SIZE
MAX_SEQ_NUM = 2 ** 24

ACK_MASK = 1 << 7
SYN_MASK = 1 << 6
LST_MASK = 1 << 5
FIN_MASK = 1 << 4
SAC_MASK = 1 << 3

"""
                           RDP HEADER

                     1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|A|S|L|F|S|     |                                               |
|C|Y|S|I|A|FLAGS|                    SEQ NUM                    |
|K|N|T|N|C|     |                                               |
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
        self._fin = False
        self._sac = False
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

    def fin(self, value: bool) -> SegmentBuilder:
        self._fin = value
        return self

    def sac(self, value: bool) -> SegmentBuilder:
        self._sac = value
        return self

    def seq_num(self, value: int) -> SegmentBuilder:
        self._seq_num = value
        return self

    def data(self, value: bytes) -> SegmentBuilder:
        self._data = value
        return self

    def build(self) -> Segment:
        return Segment(self._ack, self._syn, self._lst, self._fin, self._sac, self._seq_num, self._data)


class Segment:
    def __init__(self, ack: bool, syn: bool, lst: bool, fin: bool, sac: bool, seq_num: int, data: bytes):
        self._ack = ack
        self._syn = syn
        self._lst = lst
        self._fin = fin
        self._sac = sac
        self._seq_num = seq_num
        self._data = data

    @classmethod
    def from_bytes(cls, seg_bytes: bytes) -> Segment:
        flags = seg_bytes[0]
        ack = flags & ACK_MASK != 0
        syn = flags & SYN_MASK != 0
        lst = flags & LST_MASK != 0
        fin = flags & FIN_MASK != 0
        sac = flags & SAC_MASK != 0
        seq_num = int.from_bytes(seg_bytes[1:4], "big")
        data = seg_bytes[RDP_HEADER_SIZE:]
        return cls.builder()  \
            .ack(ack)         \
            .syn(syn)         \
            .lst(lst)         \
            .fin(fin)         \
            .sac(sac)         \
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

    @classmethod
    def fin_seg(cls, seq_num: int) -> Segment:
        return cls.builder()  \
            .fin(True)        \
            .seq_num(seq_num) \
            .build()

    @classmethod
    def sac_seg(cls, seq_num: int) -> Segment:
        return cls.builder()  \
            .sac(True)        \
            .seq_num(seq_num) \
            .build()

    def is_syn(self) -> bool:
        return self._syn

    def is_ack(self) -> bool:
        return self._ack

    def is_lst(self) -> bool:
        return self._lst

    def is_fin(self) -> bool:
        return self._fin

    def is_sac(self) -> bool:
        return self._sac

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
        data = bytearray()

        ack = ACK_MASK * self.is_ack()
        syn = SYN_MASK * self.is_syn()
        lst = LST_MASK * self.is_lst()
        fin = FIN_MASK * self.is_fin()
        sac = SAC_MASK * self.is_sac()
        flags = int.to_bytes(ack | syn | lst | fin | sac, 1, "big")
        data.extend(flags)

        seq_num = self.seq_num().to_bytes(3, "big")
        data.extend(seq_num)

        data.extend(self.unwrap())
        return data
