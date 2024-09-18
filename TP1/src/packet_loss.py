from mininet.topo import Topo
from mininet.link import TCLink


class PacketLoss(Topo):
    def __init__(self):
        super().__init__(self)

        # Add hosts and switches
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        s1 = self.addSwitch('s1')

        # Add links
        self.addLink(h2, s1, cls=TCLink, loss=0)
        self.addLink(h1, s1, cls=TCLink, loss=20)


topos = {'packet-loss': (lambda: PacketLoss())}
