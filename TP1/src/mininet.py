from mininet.topo import Topo
from mininet.link import TCLink


class PacketLoss(Topo):
    def __init__(self):
        super().__init__(self)

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')

        s1 = self.addSwitch('s1')

        self.addLink(h1, s1, cls=TCLink, loss=0)
        self.addLink(h2, s1, cls=TCLink, loss=10)
        self.addLink(h3, s1, cls=TCLink, loss=10)
        self.addLink(h4, s1, cls=TCLink, loss=10)
        self.addLink(h5, s1, cls=TCLink, loss=10)


topos = {'packet-loss': (lambda: PacketLoss())}
