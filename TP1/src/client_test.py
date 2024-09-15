from rdp_socket.socket import RdpSocket
from sys import argv

if len(argv) < 2:
    print("No me diste el puerto")
    exit(1)

puerto = int(argv[1])
socket = RdpSocket.connect("127.0.0.1", puerto)
print(f"Me conecte a: {socket.peer_addr()}")
socket.close()
