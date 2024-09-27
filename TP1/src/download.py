from lib.config import DownloadConfig
from lib.rdp.socket import RdpStream
from lib.message import Message
from sys import argv
import os


if __name__ == "__main__":
    config = DownloadConfig(argv)

    log = config.verbose()
    ip, port = config.addr()
    stream = RdpStream.connect(ip, port, log=log)

    name = config.name()
    msg = Message.download(name)
    stream.send(msg.encode())
    res = stream.recv()
    stream.close()

    msg = Message.from_bytes(res)
    if msg.is_error():
        print(msg.unwrap().decode())
        exit(1)

    dst = config.dst()
    os.makedirs(dst, exist_ok=True)
    with open(dst + "/" + name, "wb") as f:
        f.write(msg.unwrap())