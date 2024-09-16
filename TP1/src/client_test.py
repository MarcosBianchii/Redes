from rdp_socket.socket import RdpSocket
from sys import argv

if len(argv) < 2:
    print(f"Use: python3 {argv[0]} <port>")
    exit(1)

puerto = int(argv[1])
socket = RdpSocket.connect("127.0.0.1", puerto)
print(f"Me conecte a: {socket.peer_addr()}")


with open("rdp_socket/socket.py") as f:
    data = f.read()

socket.send(data.encode())
socket.close()
