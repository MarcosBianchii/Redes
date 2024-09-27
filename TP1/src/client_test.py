from lib.rdp.socket import RdpStream
from sys import argv

if len(argv) < 2 or ":" not in argv[1]:
    print(f"Use: python3 {argv[0]} <ip:port>")
    exit(1)

ip, port = argv[1].split(":")
stream = RdpStream.connect(ip, int(port), log=True)

with open("lorem_ipsum.txt", "r") as f:
    text = f.read()
    stream.send(text.encode(), winsize=10)

stream.close()
