from threading import Thread
import signal
from sys import argv
from rdp.socket import RdpListener

if len(argv) < 2 or ":" not in argv[1]:
    print(f"Use: python3 {argv[0]} <ip:port>")
    exit(1)

ip, port = argv[1].split(":")
listener = RdpListener.bind(ip, int(port), log=True)
threads: list[Thread] = []


# Handle SIGINT
def close_listener(sig, frame):
    listener.close()
    for thread in threads:
        thread.join()

    exit(0)


signal.signal(signal.SIGINT, close_listener)


for stream in listener:
    thread = Thread(target=lambda stream: stream.recv(), args=(stream, ))
    thread.start()
    threads.append(thread)
