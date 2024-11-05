# Reliable Data Protocol (RDP)

#### Mininet
```sh
sudo mn --custom mininet.py --topo=packet-loss
```

#### Wireshark
```sh
sudo wireshark -X lua_script:rdp_dissector.lua
```

#### Server
```sh
python3 server.py -v -H <host> -w <n>
```

#### Upload
```sh
python3 upload.py -v -H <host> -s <src> -n <file_name> -w <n>
```

#### Download
```sh
python3 download.py -v -H <host> -d <dst> -n <file_name> -w <n>
```