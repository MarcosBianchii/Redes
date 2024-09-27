from .logger import Logger


class VerboseLogger(Logger):
    def connection_established(self, addr: tuple[str, int]):
        print(f"[CONN] Established connection with {addr[0]}:{addr[1]}")

    def awaiting_connections(self, addr: tuple[str, int]):
        print(f"[CONN] Awaiting connections at: {addr[0]}:{addr[1]}")

    def _seg_kind(self, seg) -> str:
        kind = ""
        if seg.is_syn():
            kind += "SYN"
        if seg.is_ack():
            kind += "ACK"
        elif seg.is_fin():
            kind += "FIN"
        elif not seg.is_syn() and not seg.is_ack():
            kind += "SEG"

        return kind

    def recv(self, seg):
        kind = self._seg_kind(seg)
        print(f"[RECV] {kind}({seg.seq_num()})")

    def send(self, seg):
        kind = self._seg_kind(seg)
        print(f"[SEND] {kind}({seg.seq_num()})")

    def timeout(self, msg: str):
        print(f"[TOUT] {msg}")
