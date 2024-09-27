from lib.rdp.socket import RdpListener, RdpStream
from lib.config import ServerConfig
from multiprocessing import Process
from lib.message import Message
from sys import argv
import signal
import os


def handle_client(stream: RdpStream, storage: str, winsize: int):
    msg_bytes = stream.recv(winsize)
    msg = Message.from_bytes(msg_bytes)
    path = msg.path()

    if msg.is_upload():
        try:
            os.makedirs(storage, exist_ok=True)
            with open(storage + path, "wb") as f:
                f.write(msg.unwrap())
                response = Message.ok(path, bytes())
        except OSError as e:
            response = Message.error(f"OSError raised: {e}".encode())

    elif msg.is_download():
        try:
            with open(storage + path, "rb") as f:
                response = Message.ok(path, f.read())
        except OSError:
            response = Message.error(path, b"The file does not exist")

    else:
        response = Message.error(path, b"Invalid request method")

    stream.send(response.encode(), winsize)
    stream.close()


if __name__ == "__main__":
    config = ServerConfig(argv)

    log = config.verbose()
    ip, port = config.addr()
    listener = RdpListener.bind(ip, port, log=log)
    childs = []

    def close_listener(sig, frame):
        listener.close()
        for process in childs:
            process.join()

        exit(0)

    signal.signal(signal.SIGINT, close_listener)
    storage = config.storage()
    winsize = config.winsize()

    for stream in listener:
        child = Process(target=handle_client, args=(stream, storage, winsize))
        childs.append(child)
        child.start()
