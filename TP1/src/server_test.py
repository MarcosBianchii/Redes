import signal
from sys import argv
from rdp.socket import RdpListener

if len(argv) < 2 or ":" not in argv[1]:
    print(f"Use: python3 {argv[0]} <ip:port>")
    exit(1)

ip, port = argv[1].split(":")
listener = RdpListener.bind(ip, int(port))
print(f"Listening on port: {port}")


def close_listener(sig, frame):
    listener.close()
    exit(0)


signal.signal(signal.SIGINT, close_listener)


for stream in listener:
    print(f"New connection arrived from: {stream.peer_addr()}")

    data = stream.recv()
    print(f"Recibi: {data.decode()}")

    stream.send("Mensaje de servidor a cliente".encode())

    data = stream.recv()
    print(f"Recibi: {data.decode()}")

    stream.close()
