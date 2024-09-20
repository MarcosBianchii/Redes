from mininet.topo import Topo
from mininet.link import TCLink

"""
              Net Topology

            40%           20%
    [h1] --------- [X] --------- [h2]

"""


class PacketLoss(Topo):
    def __init__(self):
        super().__init__(self)

        # Add hosts and switches
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        s1 = self.addSwitch('s1')

        # Add links
        self.addLink(h2, s1, cls=TCLink, loss=40)
        self.addLink(h1, s1, cls=TCLink, loss=10)


topos = {'packet-loss': (lambda: PacketLoss())}
