from rdp_socket.socket import RdpListener

listener = RdpListener(12003)
for stream in listener:
    print(f"me llego una coneccion de: {stream.peer_addr()}")
    stream.close()
