from lib.message import Message, Method
from rdp.socket import RdpStream
from sys import argv
import os


class InvalidArguments(Exception):
    def __init__(self, msg: str):
        self._msg = msg

    def __str__(self) -> str:
        return self._msg


class Config:
    def __init__(self, args: list[str]):
        self._verbosity = False
        self._host = "127.0.0.1"
        self._port = 12000
        self._dst = "."
        self._name = None

        i = 1
        while i < len(args):
            match args[i]:
                case "-h" | "--help":
                    print(f"""
usage : {argv[0]} [-h] [-v | -q] [-H ADDR] [-p PORT] [-d FILEPATH] [-n FILENAME]

optional arguments:
    -h, --help     show this help message and exit
    -v, --verbose  increase output verbosity
    -q, --quiet    decrease output verbosity
    -H, --host     server IP address
    -p, --port     server port
    -d, --dst      destination file path
    -n, --name     file name
""")
                    exit(0)

                case "-v" | "--verbose":
                    self._verbosity = True

                case "-q" | "--quiet":
                    self._verbosity = False

                case "-H" | "--host":
                    try:
                        self._host = args[i + 1]
                        i += 1
                    except IndexError:
                        raise InvalidArguments(
                            f"No host specified after: {args[i]}")

                case "-p" | "--port":
                    try:
                        self._port = int(args[i + 1])
                        i += 1
                    except IndexError:
                        raise InvalidArguments(
                            f"No port specified after: {args[i]}"
                        )

                case "-d" | "--dst":
                    try:
                        self._dst = args[i + 1]
                        i += 1
                    except IndexError:
                        raise InvalidArguments(
                            f"No dst directory specified after: {args[i]}"
                        )

                case "-n" | "--name":
                    try:
                        self._name = args[i + 1]
                        i += 1
                    except IndexError:
                        raise InvalidArguments(
                            f"No file name specified after: {args[i]}"
                        )

                case _:
                    raise InvalidArguments(f"{i}'th argument is invalid")

            i += 1

        if self._name == None:
            raise InvalidArguments("No file name was specified")

    def addr(self) -> tuple[str, int]:
        return self._host, self._port

    def log(self) -> bool:
        return self._verbosity

    def name(self) -> str:
        return self._name

    def dst(self) -> str:
        return self._dst


if __name__ == "__main__":
    config = Config(argv)

    log = config.log()
    ip, port = config.addr()
    stream = RdpStream.connect(ip, port, log=log)

    msg = Message.download(config.name())
    stream.send(msg.encode())
    res = stream.recv()
    stream.close()

    dst = config.dst()
    msg = Message.from_bytes(res)
    os.makedirs(dst, exist_ok=True)
    with open(dst + msg.path(), "wb") as f:
        f.write(msg.unwrap())
