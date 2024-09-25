from __future__ import annotations
from enum import Enum

"""
                       UPLOAD                        DOWNLOAD

                 UP /file_name\ndata             DOWN /file_name\n



                         OK                           ERROR

                 OK /file_name\ndata           ERR /file_name\ndata
"""


class Method(Enum):
    UPLOAD = 0
    DOWNLOAD = 1
    ERROR = 2
    OK = 3

    @classmethod
    def from_str(cls, s: str) -> Method:
        match s:
            case "UP":
                return cls.UPLOAD
            case "DOWN":
                return cls.DOWNLOAD
            case "OK":
                return cls.OK
            case "ERR":
                return cls.ERROR
            case _:
                raise ValueError("Invalid method field")

    def __str__(self) -> str:
        match self:
            case Method.UPLOAD:
                return "UP"
            case Method.DOWNLOAD:
                return "DOWN"
            case Method.ERROR:
                return "ERR"
            case Method.OK:
                return "OK"

    def encode(self) -> bytes:
        return str(self).encode()


class MessageBuilder:
    def __init__(self):
        self._method = Method.DOWNLOAD
        self._path = "/"
        self._data = bytes()

    def method(self, value: Method) -> MessageBuilder:
        self._method = value
        return self

    def path(self, value: str) -> MessageBuilder:
        if value[0] != "/":
            value = "/" + value

        self._path = value
        return self

    def data(self, value: bytes) -> MessageBuilder:
        self._data = value
        return self

    def build(self) -> Message:
        return Message(self._method, self._path, self._data)


class Message:
    def __init__(self, method: Method, path: str, data: bytes):
        self._method = method
        self._path = path
        self._data = data

    @classmethod
    def from_bytes(cls, data: bytes) -> Message:
        method_len = data.index(b" ")
        method = data[:method_len].decode()
        nl = data.index(b"\n")
        path = data[method_len + 1:nl].decode()
        data = data[nl + 1:]

        return cls.builder()                 \
            .method(Method.from_str(method)) \
            .path(path)                      \
            .data(data)                      \
            .build()

    @classmethod
    def builder(cls) -> MessageBuilder:
        return MessageBuilder()

    @classmethod
    def upload(cls, path: str, data: bytes) -> Message:
        return cls.builder()       \
            .method(Method.UPLOAD) \
            .path(path)            \
            .data(data)            \
            .build()

    @classmethod
    def download(cls, path: str) -> Message:
        return cls.builder()         \
            .method(Method.DOWNLOAD) \
            .path(path)              \
            .build()

    @classmethod
    def ok(cls, path: str, data: bytes) -> Message:
        return cls.builder()   \
            .method(Method.OK) \
            .path(path)        \
            .data(data)        \
            .build()

    @classmethod
    def error(cls, path: str, data: bytes) -> Message:
        return cls.builder()      \
            .method(Method.ERROR) \
            .path(path)           \
            .data(data)           \
            .build()

    def is_upload(self) -> bool:
        return self._method == Method.UPLOAD

    def is_download(self) -> bool:
        return self._method == Method.DOWNLOAD

    def is_ok(self) -> bool:
        return self._method == Method.OK

    def is_error(self) -> bool:
        return self._method == Method.ERROR

    def path(self) -> str:
        return self._path

    def unwrap(self) -> bytes:
        return self._data

    def encode(self) -> bytes:
        """
        Turns the message into bytes
        """
        path = self._path.encode()
        return self._method.encode() + b" " + path + b"\n" + self._data

    def __str__(self) -> str:
        return f"{self._method} {self._path} {len(self._data)}"
