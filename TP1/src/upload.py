from lib.rdp.socket import RdpStream
from lib.config import UploadConfig
from lib.message import Message
from sys import argv

if __name__ == "__main__":
    config = UploadConfig(argv)

    src = config.src()
    name = config.name()
    with open(src + "/" + name, "rb") as f:
        data = f.read()

    log = config.verbose()
    ip, port = config.addr()
    stream = RdpStream.connect(ip, port, log=log)

    msg = Message.upload(name, data)
    stream.send(msg.encode())
    res = stream.recv()
    stream.close()

    msg = Message.from_bytes(res)
    if msg.is_error():
        print(msg.unwrap().decode())
