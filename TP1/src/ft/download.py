from lib.config import DownloadConfig
from rdp.socket import RdpStream
from lib.message import Message
from sys import argv
import os


if __name__ == "__main__":
    config = DownloadConfig(argv)

    log = config.verbose()
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
