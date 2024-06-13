#!/usr/bin/python

import argparse

from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import Host
from mininet.topo import Topo
from stratum import StratumBmv2Switch

CPU_PORT = 255


class IPv4Host(Host):
    """Host that can be configured with an IPv4 gateway (default route).
    """

    def config(self, mac=None, ip=None, defaultRoute=None, lo='up', gw=None,
               **_params):
        super(IPv4Host, self).config(mac, ip, defaultRoute, lo, **_params)
        self.cmd('ip -4 addr flush dev %s' % self.defaultIntf())
        self.cmd('ip -6 addr flush dev %s' % self.defaultIntf())
        self.cmd('ip -4 link set up %s' % self.defaultIntf())
        self.cmd('ip -4 addr add %s dev %s' % (ip, self.defaultIntf()))
        if gw:
            self.cmd('ip -4 route add default via %s' % gw)
        # Disable offload
        for attr in ["rx", "tx", "sg"]:
            cmd = "/sbin/ethtool --offload %s %s off" % (
                self.defaultIntf(), attr)
            self.cmd(cmd)

        def updateIP():
            return ip.split('/')[0]

        self.defaultIntf().updateIP = updateIP


class CustomTopo(Topo):
    """2x2 fabric topology with IPv4 hosts"""

    def __init__(self, *args, **kwargs):
        Topo.__init__(self, *args, **kwargs)

        h1 = self.addHost('h10', cls=IPv4Host, ip="192.168.1.2/24", mac="00:00:00:00:01:00")
        h2 = self.addHost('h11', cls=IPv4Host, ip="192.168.1.3/24", mac="00:00:00:00:02:00")
        h3 = self.addHost('h20', cls=IPv4Host, ip="192.168.1.4/24", mac="00:00:00:00:03:00")
        h4 = self.addHost('h21', cls=IPv4Host, ip="192.168.1.5/24", mac="00:00:00:00:04:00")
        h5 = self.addHost('h30', cls=IPv4Host, ip="192.168.1.6/24", mac="00:00:00:00:05:00")
        h6 = self.addHost('h31', cls=IPv4Host, ip="192.168.1.7/24", mac="00:00:00:00:06:00")
        h7 = self.addHost('h40', cls=IPv4Host, ip="192.168.1.8/24", mac="00:00:00:00:07:00")
        h8 = self.addHost('h41', cls=IPv4Host, ip="192.168.1.9/24", mac="00:00:00:00:08:00")
        # self.hosts = [h1, h2, h3, h4, h5, h6, h7, h8]

        s0 = self.addSwitch('s0', cls=StratumBmv2Switch, cpuport=CPU_PORT)
        s1 = self.addSwitch('s1', cls=StratumBmv2Switch, cpuport=CPU_PORT)
        s2 = self.addSwitch('s2', cls=StratumBmv2Switch, cpuport=CPU_PORT)
        s3 = self.addSwitch('s3', cls=StratumBmv2Switch, cpuport=CPU_PORT)
        s4 = self.addSwitch('s4', cls=StratumBmv2Switch, cpuport=CPU_PORT)

        self.addLink(h1, s1, port2=1)
        self.addLink(h2, s1, port2=2)
        
        self.addLink(h3, s2, port2=1)
        self.addLink(h4, s2, port2=2)
        
        self.addLink(h5, s3, port2=1)
        self.addLink(h6, s3, port2=2)
        
        self.addLink(h7, s4, port2=1)
        self.addLink(h8, s4, port2=2)
        
        self.addLink(s0, s1, port1=1, port2=3)
        self.addLink(s0, s2, port1=2, port2=3)
        self.addLink(s0, s3, port1=3, port2=3)
        self.addLink(s0, s4, port1=4, port2=3)
        
        self.addLink(s1, s2, port1=5, port2=4)
        self.addLink(s2, s3, port1=5, port2=4)
        self.addLink(s3, s4, port1=5, port2=4)
        self.addLink(s4, s1, port1=5, port2=4)


def main():
    net = Mininet(topo=CustomTopo(), controller=None)
    net.start()
    CLI(net)
    net.stop()
    print '#' * 80
    print 'ATTENTION: Mininet was stopped! Perhaps accidentally?'
    print 'No worries, it will restart automatically in a few seconds...'
    print 'To access again the Mininet CLI, use `make mn-cli`'
    print 'To detach from the CLI (without stopping), press Ctrl-D'
    print 'To permanently quit Mininet, use `make stop`'
    print '#' * 80


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Mininet topology script for 2x2 fabric with stratum_bmv2 and IPv4 hosts')
    args = parser.parse_args()
    setLogLevel('info')

    main()
