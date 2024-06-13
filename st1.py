from mininet.net import Mininet
from mininet.node import Controller, RemoteController , OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info

import os

# sudo ./pox/pox.py log.level --DEBUG openflow.of_01 --port=6633 --address=127.0.0.1 forwarding.l2_learning

net = Mininet(switch = OVSSwitch, waitConnected = True )

# Add hosts
h1 = net.addHost('h1', mac="10:00:00:00:00:00")
h2 = net.addHost('h2', mac="20:00:00:00:00:00")
h3 = net.addHost('h3', mac="30:00:00:00:00:00")
h4 = net.addHost('h4', mac="40:00:00:00:00:00")

# Add switch
s1 = net.addSwitch('s1', dpid="0000000000000001", mac="00:00:00:00:00:01", protocols="OpenFlow13" )
s2 = net.addSwitch('s2',  dpid="0000000000000002", mac="00:00:00:00:00:02", protocols="OpenFlow13" )

# Add links
net.addLink(h1, s1, port1=1, port2=1) # connect h1 to s1
net.addLink(h2, s1, port1=1, port2=2) # connect h2 to s1
net.addLink(h3, s2, port1=1, port2=1) # connect h3 to s2
net.addLink(h4, s2, port1=1, port2=2) # connect h4 to s2
net.addLink(s1, s2, port1=3, port2=3) # connect s1 to s2

cl2 = net.addController(name="cl2", controller=RemoteController, ip='127.0.0.1', port=6633)
net.start()
net.pingAll()
CLI(net)
net.stop()

print("\n==== CLEANING ====\n")
os.system("mn -c")
