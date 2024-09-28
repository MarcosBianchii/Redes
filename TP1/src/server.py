from lib.rdp.socket import RdpListener, RdpStream, Hangup
from lib.config import ServerConfig
from lib.message import Message
from threading import Thread
from sys import argv
import signal
import os


def handle_client(stream: RdpStream, storage: str, winsize: int):
    try:
        msg_bytes = stream.recv(winsize)
    except Hangup:
        stream.close()
        return

    msg = Message.from_bytes(msg_bytes)
    path = msg.path()

    if msg.is_upload():
        try:
            os.makedirs(storage, exist_ok=True, mode=0o777)
            with open(storage + path, "wb") as f:
                f.write(msg.unwrap())
                response = Message.ok(path, bytes())
        except OSError as e:
            response = Message.error(path, f"OSError raised: {e}".encode())

    elif msg.is_download():
        try:
            with open(storage + path, "rb") as f:
                response = Message.ok(path, f.read())
        except OSError:
            response = Message.error(path, b"The file does not exist")

    else:
        response = Message.error(path, b"Invalid request method")

    try:
        stream.send(response.encode(), winsize)
    except Hangup:
        pass

    stream.close()


if __name__ == "__main__":
    config = ServerConfig(argv)

    log = config.verbose()
    ip, port = config.addr()
    listener = RdpListener.bind(ip, port, log=log)
    threads = []

    def close_listener(sig, frame):
        listener.close()
        for thread in threads:
            thread.join()

        exit(0)

    signal.signal(signal.SIGINT, close_listener)
    storage = config.storage()
    winsize = config.winsize()

    for stream in listener:
        thread = Thread(target=handle_client, args=(stream, storage, winsize))
        threads.append(thread)
        thread.start()
