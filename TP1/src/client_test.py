from rdp_socket.socket import RdpSocket

socket = RdpSocket.connect("127.0.0.1", 12003)
print(f"me llego una coneccion de: {socket.peer_addr()}")
socket.close()
