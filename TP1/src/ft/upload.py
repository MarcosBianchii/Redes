from sys import argv
from lib.message import Message, Method
from rdp.socket import RdpStream


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
        self._src = "."
        self._name = None

        i = 1
        while i < len(args):
            match args[i]:
                case "-h" | "--help":
                    print(f"""
usage : {argv[0]} [-h] [-v | -q] [-H ADDR] [-p PORT] [-s FILEPATH] [-n FILENAME]

optional arguments:
    -h, --help     show this help message and exit
    -v, --verbose  increase output verbosity
    -q, --quiet    decrease output verbosity
    -H, --host     server IP address
    -p, --port     server port
    -s, --src      source file path
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

                case "-s" | "--src":
                    try:
                        self._src = args[i + 1]
                        i += 1
                    except IndexError:
                        raise InvalidArguments(
                            f"No src directory specified after: {args[i]}"
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

    def path(self) -> tuple[str, str]:
        return self._src, self._name


if __name__ == "__main__":
    config = Config(argv)

    src, name = config.path()
    with open(src + "/" + name, "rb") as f:
        data = f.read()

    log = config.log()
    ip, port = config.addr()
    stream = RdpStream.connect(ip, port, log=log)

    msg = Message.upload(name, data)
    stream.send(msg.encode())
    res = stream.recv()
    stream.close()

    msg = Message.from_bytes(res)
    if msg.is_error():
        print(msg.unwrap().decode())
