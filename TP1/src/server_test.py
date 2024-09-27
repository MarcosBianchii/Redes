from lib.rdp.socket import RdpListener
from sys import argv
import signal

if len(argv) < 2 or ":" not in argv[1]:
    print(f"Use: python3 {argv[0]} <ip:port>")
    exit(1)

ip, port = argv[1].split(":")
listener = RdpListener.bind(ip, int(port), log=True)


def close_listener(sig, frame):
    listener.close()
    exit(0)


signal.signal(signal.SIGINT, close_listener)


for stream in listener:
    data = stream.recv(winsize=10)
    print(data.decode())

    stream.close()
