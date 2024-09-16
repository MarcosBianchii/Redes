import signal
from sys import argv
from rdp_socket.socket import RdpListener

if len(argv) < 2:
    print(f"Use: python3 {argv[0]} <port>")
    exit(1)

puerto = int(argv[1])
listener = RdpListener.bind(puerto)
print(f"Escuchando en el puerto: {puerto}")


def close_listener(sig, frame):
    print("Cerre el listener socket")
    listener.close()
    exit(0)


signal.signal(signal.SIGINT, close_listener)


for stream in listener:
    print(f"Me llego una coneccion de: {stream.peer_addr()}")
    stream.close()
