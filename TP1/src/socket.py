from socket import socket, AF_INET, SOCK_DGRAM


class RdpStream:
    def __init__(self, ip: str, port: int):
        self._peer_addr = (ip, port)
        self._skt = socket(AF_INET, SOCK_DGRAM)

    def recv(self, size: int):
        """
        Blocks the main thread until `size` amounts of data arrive through the socket
        """
        pass

    def send(self, readable: bytes) -> int:
        """
        Sends the `readable` data through the socket

        Returns the amount of data sent
        """
        pass

    def sendall(self, readable: bytes):
        """
        Makes sure to send all the content in `readable` through the socket
        """
        pass

    def close(self):
        """
        Closes the connection
        """
        pass


class RdpListener:
    def __init__(self, port: int):
        self._addr = ("127.0.0.1", port)
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._skt.bind(self._addr)

    def accept(self):
        """
        Blocks the main thread until a new connection arrives
        """
        pass

    def incoming(self):
        """
        Returns an iterator of incoming connections
        """
        while True:
            yield self.accept()
