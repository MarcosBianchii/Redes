from .logger import Logger


class QuietLogger(Logger):
    def connection_established(self, addr: tuple[str, int]):
        pass

    def awaiting_connections(self, addr: tuple[str, int]):
        pass

    def recv(self, seg):
        pass

    def send(self, seg):
        pass
