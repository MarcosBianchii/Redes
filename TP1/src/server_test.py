import signal
from sys import argv
from rdp_socket.socket import RdpListener

if len(argv) < 2:
    print("No me diste el puerto")
    exit(1)

puerto = int(argv[1])
listener = RdpListener.bind(puerto)
print(f"Escuchando en el puerto: {puerto}")


def close_listener(sig, frame):
    listener.close()
    exit(0)


signal.signal(signal.SIGINT, close_listener)


for stream in listener:
    print(f"Me llego una coneccion de: {stream.peer_addr()}")
    stream.close()

listener.close()
