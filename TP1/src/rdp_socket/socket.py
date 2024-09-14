from socket import socket, AF_INET, SOCK_DGRAM, timeout
from .packet import PKT_HEADER_SIZE, Packet


def _sendall(skt: socket, data: bytes, addr):
    skt.sendto(data, addr)
    # sent = 0
    # while sent < len(data):
    #     sent += skt.sendto(data[sent:], addr)
    #     print(sent)


class RdpSocket:
    def __init__(self, peer_addr):
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._peer_addr = peer_addr

    @classmethod
    def connect(cls, ip: str, port: int):
        self = cls((ip, port))

        while True:
            syn_pkt = Packet.syn_pkt()
            _sendall(self._skt, syn_pkt.encode(), self.peer_addr())

            try:
                self._skt.settimeout(10)
                header, peer_addr = self._skt.recvfrom(PKT_HEADER_SIZE)
            except timeout:
                continue

            pkt = Packet.from_header(header)
            if pkt.is_syn() and pkt.is_ack():
                self._peer_addr = peer_addr
                break

        return self

    def peer_addr(self):
        return self._peer_addr

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
        self._skt.close()


class RdpListener:
    def __init__(self, port: int):
        self._skt = socket(AF_INET, SOCK_DGRAM)
        self._skt.bind(("127.0.0.1", port))

    @classmethod
    def _create_stream(cls, peer_addr):
        stream = RdpSocket(peer_addr)
        syn_ack = Packet.syn_ack_pkt()
        _sendall(stream._skt, syn_ack.encode(), peer_addr)
        return stream

    def accept(self) -> RdpSocket:
        while True:
            try:
                header, addr = self._skt.recvfrom(PKT_HEADER_SIZE)
            except:
                continue

            pkt = Packet.from_header(header)
            if pkt.is_syn() and not pkt.is_ack():
                return self._create_stream(addr)

    def __iter__(self):
        while True:
            yield self.accept()
