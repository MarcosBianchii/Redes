from lib.rdp.socket import RdpListener, RdpStream
from lib.config import ServerConfig
from lib.message import Message
from threading import Thread
from sys import argv
import signal
import os


def handle_client(stream: RdpStream, storage: str):
    msg_bytes = stream.recv()
    msg = Message.from_bytes(msg_bytes)
    path = msg.path()

    if msg.is_upload():
        ok = Message.ok(path, bytes())
        stream.send(ok.encode())

        os.makedirs(storage, exist_ok=True)
        with open(storage + path, "wb") as f:
            f.write(msg.unwrap())

    elif msg.is_download():
        try:
            with open(storage + path, "rb") as f:
                ok = Message.ok(path, f.read())
                stream.send(ok.encode())
        except OSError:
            error = Message.error(path, b"The file does not exist")
            stream.send(error.encode())

    else:
        error = Message.error(path, b"Invalid request method")
        stream.send(error.encode())

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

    for stream in listener:
        thread = Thread(target=handle_client, args=(stream, config.storage()))
        threads.append(thread)
        thread.start()
