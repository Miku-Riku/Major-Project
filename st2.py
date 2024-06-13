from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.log import setLogLevel, info
from mininet.cli import CLI

net = Mininet()

# Adding routers
r1 = net.addSwitch('r1', ip='10.0.0.1/24', dpid="0000000000001000")
r2 = net.addSwitch('r2', ip='10.1.0.1/24', dpid="0000000000002000")
r3 = net.addSwitch('r3', ip='10.2.0.1/24', dpid="0000000000003000")
r4 = net.addSwitch('r4', ip='10.3.0.1/24', dpid="0000000000004000")

# Linking routers
net.addLink(r1, r2, port1=2, port2=2, intfName1='r1-eth2', intfName2='r2-eth2')
net.addLink(r1, r3, port1=3, port2=2, intfName1='r1-eth3', intfName2='r3-eth2')
net.addLink(r3, r4, port1=3, port2=2, intfName1='r3-eth3', intfName2='r4-eth2')
net.addLink(r2, r4, port1=3, port2=3, intfName1='r2-eth3', intfName2='r4-eth3')

# Adding switches
s1 = net.addSwitch('s1', dpid="0000000000000050", mac='00:00:00:10:00:00')
s2 = net.addSwitch('s2', dpid="0000000000000060", mac='00:00:00:20:00:00')
s3 = net.addSwitch('s3', dpid="0000000000000070", mac='00:00:00:30:00:00')
s4 = net.addSwitch('s4', dpid="0000000000000080", mac='00:00:00:40:00:00')

# Linking switches to routers
net.addLink(s1, r1, port1=3, port2=1, intfName1='s1-eth3', intfName2='r1-eth1')
net.addLink(s2, r2, port1=3, port2=1, intfName1='s2-eth3', intfName2='r2-eth1')
net.addLink(s3, r3, port1=3, port2=1, intfName1='s3-eth3', intfName2='r3-eth1')
net.addLink(s4, r4, port1=3, port2=1, intfName1='s4-eth3', intfName2='r4-eth1')

# Adding hosts
h1 = net.addHost(name='h1', ip='10.0.0.10/24',
                 defaultRoute='via 10.0.0.1', mac='00:00:00:00:00:01')
h11 = net.addHost(name='h11', ip='10.0.0.11/24',
                  defaultRoute='via 10.0.0.1', mac='00:00:00:00:00:11')
h2 = net.addHost(name='h2', ip='10.1.0.10/24',
                 defaultRoute='via 10.1.0.1', mac='00:00:00:00:00:02')
h22 = net.addHost(name='h22', ip='10.1.0.11/24',
                  defaultRoute='via 10.1.0.1', mac='00:00:00:00:00:22')
h3 = net.addHost(name='h3', ip='10.2.0.10/24',
                 defaultRoute='via 10.2.0.1', mac='00:00:00:00:00:03')
h33 = net.addHost(name='h33', ip='10.2.0.11/24',
                  defaultRoute='via 10.2.0.1', mac='00:00:00:00:00:33')
h4 = net.addHost(name='h4', ip='10.3.0.10/24',
                 defaultRoute='via 10.3.0.1', mac='00:00:00:00:00:04')
h44 = net.addHost(name='h44', ip='10.3.0.11/24',
                  defaultRoute='via 10.3.0.1', mac='00:00:00:00:00:44')

# Linking hosts to switches
net.addLink(h1, s1, intfName1='h1-eth1', intfName2='s1-eth1', port1=1, port2=1)
net.addLink(h11, s1, intfName1='h11-eth1',
            intfName2='s1-eth2', port1=1, port2=2)
net.addLink(h2, s2, intfName1='h2-eth1', intfName2='s2-eth1', port1=1, port2=1)
net.addLink(h22, s2, intfName1='h22-eth1',
            intfName2='s2-eth2', port1=1, port2=2)
net.addLink(h3, s3, intfName1='h3-eth1', intfName2='s3-eth1', port1=1, port2=1)
net.addLink(h33, s3, intfName1='h33-eth1',
            intfName2='s3-eth2', port1=1, port2=2)
net.addLink(h4, s4, intfName1='h4-eth1', intfName2='s4-eth1', port1=1, port2=1)
net.addLink(h44, s4, intfName1='h44-eth1',
            intfName2='s4-eth2', port1=1, port2=2)

net.build()

# sudo ./pox/pox.py log.level --DEBUG samples.pretty_log openflow.of_01 --port=6633 --address=127.0.0.1 forwarding.l2_learning
# sudo ./pox/pox.py log.level --DEBUG samples.pretty_log openflow.of_01 --port=6634 --address=127.0.0.1 forwarding.l3_learning

cl2 = net.addController(
    name="cl2", controller=RemoteController, ip='127.0.0.1', port=6633)
cl3 = net.addController(
    name="cl3", controller=RemoteController, ip='127.0.0.1', port=6634)

s1.start([cl2])
s2.start([cl2])
s3.start([cl2])
s4.start([cl2])

r1.start([cl3])
r2.start([cl3])
r3.start([cl3])
r4.start([cl3])

nodes = [h1, h11, h2, h22, h3, h33, h4, h44]
for x in nodes:
    for y in nodes:
        if x.name == y.name:
            continue
        x.cmd(f'ping -c1 -W.1 {y.name}')

CLI(net)
net.stop()
