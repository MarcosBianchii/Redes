import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import EthAddr, IPAddr
from pox.lib.util import dpidToStr
from pox.lib.revent import *
from pox.core import core
import json

TCP = 6
UDP = 17

log = core.getLogger()


class Firewall(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        self._rules = self.read_rules("rules.json")
        log.debug("Enabling Firewall Module")

    def _handle_ConnectionUp(self, event):
        sw_id = event.dpid

        for rule in self._rules:
            if sw_id in rule["switches"]:
                self.install_rule(event, rule)

        log.debug(f"Firewall rules installed on {dpidToStr(event.dpid)}")

    def install_rule(self, event, rule):
        matching = of.ofp_match()
        tp_proto = {
            "tcp": TCP,
            "udp": UDP,
        }

        # Transport Layer
        if "tp_src" in rule:
            matching.tp_src = rule["tp_src"]
        if "tp_dst" in rule:
            matching.tp_dst = rule["tp_dst"]

        # Network Layer
        if "nw_src" in rule:
            matching.nw_src = IPAddr(rule["nw_src"])
        if "nw_dst" in rule:
            matching.nw_dst = IPAddr(rule["nw_dst"])
        if "tp_proto" in rule:
            matching.nw_proto = tp_proto[rule["tp_proto"].lower()]

        # Data Link Layer
        if "dl_src" in rule:
            matching.dl_src = EthAddr(rule["dl_src"])
        if "dl_dst" in rule:
            matching.dl_dst = EthAddr(rule["dl_dst"])

        # Solo IP
        matching.dl_type = 0x800

        msg = of.ofp_flow_mod()
        msg.match = matching
        event.connection.send(msg)

    def read_rules(self, path):
        with open(path) as f:
            return json.load(f)


def launch():
    core.registerNew(Firewall)
