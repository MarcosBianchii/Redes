from rdp.socket import RdpListener, RdpStream
from lib.message import Message
from threading import Thread
from sys import argv
import signal
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
        self._storage = "storage"

        i = 1
        while i < len(args):
            match args[i]:
                case "-h" | "--help":
                    print(f"""
usage : {argv[0]} [-h] [-v | -q] [-H ADDR] [-p PORT] [-s DIRPATH]

optional arguments:
    -h , --help     show this help message and exit
    -v , --verbose  increase output verbosity
    -q , --quiet    decrease output verbosity
    -H , --host     service IP address
    -p , --port     service port
    -s , --storage  storage dir path
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

                case "-s" | "--storage":
                    try:
                        self._storage = args[i + 1]
                        i += 1
                    except IndexError:
                        raise InvalidArguments(
                            f"No storage specified after: {args[i]}"
                        )

                case _:
                    raise InvalidArguments(f"{i}'th argument is invalid")

            i += 1

    def addr(self) -> tuple[str, int]:
        return self._host, self._port

    def log(self) -> bool:
        return self._verbosity

    def storage(self) -> str:
        return self._storage


def handle_client(stream: RdpStream, storage: str):
    msg_bytes = stream.recv()
    msg = Message.from_bytes(msg_bytes)

    path = msg.path()
    if msg.is_upload():
        try:
            os.makedirs(storage, exist_ok=True)
            with open(storage + path, "wb") as f:
                ok = Message.ok(path, bytes())
                stream.send(ok.encode())
                f.write(msg.unwrap())

        except OSError:
            error = Message.error(
                path, "There was a problem saving the file".encode())
            stream.send(error.encode())

    elif msg.is_download():
        try:
            with open(storage + path, "rb") as f:
                ok = Message.ok(path, f.read())
                stream.send(ok.encode())

        except OSError:
            error = Message.error(path, "The file does not exist".encode())
            stream.send(error.encode())

    else:
        error = Message.error(path, "Invalid request method".encode())
        stream.send(error.encode())

    stream.close()


if __name__ == "__main__":
    config = Config(argv)

    log = config.log()
    ip, port = config.addr()
    listener = RdpListener.bind(ip, port, log=log)
    threads = []

    # Handle SIGINT
    def close_listener(sig, frame):
        listener.close()
        for thread in threads:
            thread.join()

        exit(0)

    signal.signal(signal.SIGINT, close_listener)

    for stream in listener:
        thread = Thread(target=handle_client, args=(stream, config.storage()))
        threads.append(thread)
        thread.start()
