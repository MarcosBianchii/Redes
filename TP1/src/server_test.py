import signal
from sys import argv
from rdp_socket.socket import RdpListener

if len(argv) < 2:
    print(f"Use: python3 {argv[0]} <port>")
    exit(1)

puerto = int(argv[1])
listener = RdpListener.bind("127.0.0.1", puerto)
print(f"Escuchando en el puerto: {puerto}")


def close_listener(sig, frame):
    listener.close()
    exit(0)


signal.signal(signal.SIGINT, close_listener)


for stream in listener:
    print(f"Me llego una coneccion de: {stream.peer_addr()}")

    with open("rdp_socket/socket.py") as f:
        data = f.read()

    stream.send(data.encode())
    stream.close()
