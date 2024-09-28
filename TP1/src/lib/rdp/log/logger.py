from abc import abstractmethod


class Logger:
    @abstractmethod
    def connection_established(self, addr: tuple[str, int]):
        pass

    @abstractmethod
    def awaiting_connections(self, addr: tuple[str, int]):
        pass

    @abstractmethod
    def recv(self, seg):
        pass

    @abstractmethod
    def send(self, seg):
        pass
