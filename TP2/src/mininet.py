from mininet.topo import Topo


"""
H1 -[1]+                                              +[2]- H3
       +- S1 -[2]-[1]- S2 -[2]-[1]- ... -[2]-[1]- SN -+
H2 -[3]+                                              +[3]- H4
"""


class Chain(Topo):
    def __init__(self, n: int, **opts):
        super(self.__class__, self).__init__(self, opts)

        if n < 1:
            raise ValueError("n must be a positive number")

        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")
        h4 = self.addHost("h4")

        switches = [self.addSwitch(f"s{i + 1}") for i in range(n)]
        self.addLink(h1, switches[0])

        for i in range(1, n):
            self.addLink(switches[i - 1], switches[i])

        self.addLink(h2, switches[0])
        self.addLink(h3, switches[-1])
        self.addLink(h4, switches[-1])


topos = {"chain": Chain}
