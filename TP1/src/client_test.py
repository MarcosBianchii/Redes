from rdp_socket.socket import RdpSocket

socket = RdpSocket.connect("127.0.0.1", 12003)
print(f"Me conecte a: {socket.peer_addr()}")
socket.close()
