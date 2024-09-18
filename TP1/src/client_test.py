from rdp.socket import RdpStream
from sys import argv

if len(argv) < 2 or ":" not in argv[1]:
    print(f"Use: python3 {argv[0]} <ip:port>")
    exit(1)

ip, port = argv[1].split(":")
stream = RdpStream.connect(ip, int(port))
print(f"Connected to: {stream.peer_addr()}")

# with open("rdp/socket.py") as f:
#     data = f.read()
#     stream.send(data.encode())

stream.send("Primer mensaje enviado".encode())

data = stream.recv()
print(f"Recibi: {data.decode()}")

stream.send("Segundo mensaje, es mas largo".encode())

stream.close()
