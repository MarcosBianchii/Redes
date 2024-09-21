from __future__ import annotations
from enum import Enum

"""
        UPLOAD                      DOWNLOAD

   UP /file_name\ndata           DOWN /file_name

"""


class Method(Enum):
    UPLOAD = 0
    DOWNLOAD = 1
    ERROR = 2
    OK = 3

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


class InvalidMethodField(Exception):
    pass


class MessageBuilder:
    def __init__(self):
        self._method = Method.DOWNLOAD
        self._path = "/"
        self._data = bytes()

    def method(self, value: Method) -> MessageBuilder:
        self._method = value
        return self

    def path(self, value: str) -> MessageBuilder:
        self._path = "/" + value
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
        match data[:method_len].decode():
            case "UP":
                nl = data.index(b"\n")
                path = data[method_len + 1:nl].decode()
                data = data[nl + 1:]
                return cls(Method.UPLOAD, path, data)

            case "DOWN":
                path = data[method_len + 1:].decode()
                return cls(Method.DOWNLOAD, path, bytes())

            case "ERR":
                path = data[method_len + 1:nl].decode()
                data = data[nl + 1:]
                return cls(Method.ERROR, path, data)

            case "OK":
                nl = data.index(b"\n")
                path = data[method_len + 1:nl].decode()
                data = data[nl + 1:]
                return cls(Method.OK, path, data)

            case _:
                raise InvalidMethodField()

    @classmethod
    def builder(cls) -> MessageBuilder:
        return MessageBuilder()

    @classmethod
    def ok(cls, path: str, data: bytes) -> Message:
        return cls.builder()   \
            .method(Method.OK) \
            .path(path)        \
            .data(data)        \
            .build()

    @classmethod
    def error(cls, path: str, msg: str) -> Message:
        return cls.builder()      \
            .method(Method.ERROR) \
            .path(path)           \
            .data(msg.encode())   \
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
        path = self._path.encode()
        encoding = str(self._method).encode() + b" " + path

        if self.is_upload() or self.is_ok() or self.is_error():
            encoding += b"\n" + self._data

        return encoding

    def __str__(self) -> str:
        return f"{self._method} {self._path} {len(self._data)}"
