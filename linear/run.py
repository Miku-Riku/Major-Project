import sys
import os

sys.path.append("..")

from time import sleep
from core.p4runtime_lib import simple_controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import RemoteController
from core.p4_mininet import P4Host
from core.run_exercise import configureP4Switch


class Runner:
    """
    Topology:
                    [r1]
                    /  \\
                   /    \\ 
           [s1] ---      `--- [s2]
           /  \\              /  \\
        [h1]  [h2]         [h3]  [h4]
    (192.168.1.0/24)      (10.0.0.0/24)
    """

    def __init__(self, p4_list, switches):
        self.p4_switch_classes = {}
        self.p4_list = p4_list
        self.switches = switches
        self.cwd = os.getcwd()
        self.log_dir = os.path.join(self.cwd, 'logs')
        self.pcap_dir = os.path.join(self.cwd, 'pcaps')

        ret = os.system("mkdir -p build pcaps logs")
        if ret != 0:
            print(f"Unable to make folders")
            exit(-1)

        for p4 in p4_list:
            cmd = f"p4c-bm2-ss --p4v 16 --p4runtime-files build/{p4}.p4.p4info.txt -o build/{p4}.json {p4}.p4"
            print(cmd)

            ret = os.system(cmd)
            if ret != 0:
                print(f"Unable to compile {p4}.p4")
                exit(-1)

            switch_json = f"build/{p4}.json"
            self.p4_switch_classes[f"{p4}"] = configureP4Switch(sw_path='simple_switch_grpc',
                                                                json_path=switch_json,
                                                                log_console=True,
                                                                pcap_dump=self.pcap_dir)

    def run(self):
        self.configure_topo()
        sleep(1)

        self.configure_hosts()
        self.configure_switches()

        sleep(1)

        for s in self.net.switches:
            s.describe()

        for h in self.net.hosts:
            h.describe()

        print("Starting mininet CLI")
        CLI(self.net)
        self.net.stop()

        print("\n==== CLEANING ====\n")
        os.system("mn -c")

    def configure_topo(self):
        topo = Topo()

        h1 = topo.addHost('h1', ip="192.168.1.2/24", mac="00:00:00:00:01:00")
        h2 = topo.addHost('h2', ip="192.168.1.3/24", mac="00:00:00:00:02:00")
        h3 = topo.addHost('h3', ip="10.0.0.2/24", mac="00:00:00:00:03:00")
        h4 = topo.addHost('h4', ip="10.0.0.3/24", mac="00:00:00:00:04:00")

        r1 = topo.addSwitch('r1', dpid="1000000000000000", log_file="%s/%s.log" % (self.log_dir, 'r1'),
                            cls=self.p4_switch_classes['l3'])
        s1 = topo.addSwitch('s1', dpid="0000000000000001", log_file="%s/%s.log" % (self.log_dir, 's1'),
                            cls=self.p4_switch_classes['l2'])
        s2 = topo.addSwitch('s2', dpid="0000000000000002", log_file="%s/%s.log" % (self.log_dir, 's2'),
                            cls=self.p4_switch_classes['l2'])

        topo.addLink(s1, r1, port1=1, port2=1)
        topo.addLink(s2, r1, port1=1, port2=2)

        topo.addLink(h1, s1, port2=2)
        topo.addLink(h2, s1, port2=3)

        topo.addLink(h3, s2, port2=2)
        topo.addLink(h4, s2, port2=3)

        self.net = Mininet(topo=topo, link=TCLink, host=P4Host, controller=None)
        self.net.start()

    def configure_hosts(self):
        self.net['h1'].cmd("route add default gw 192.168.1.1 dev eth0")
        self.net['h2'].cmd("route add default gw 192.168.1.1 dev eth0")

        self.net['h3'].cmd("route add default gw 10.0.0.1 dev eth0")
        self.net['h4'].cmd("route add default gw 10.0.0.1 dev eth0")

    def configure_switches(self):
        for sw in self.switches:
            sw_obj = self.net[sw]
            runtime_json = f'topo/{sw}_runtime.json'
            print('Configuring switch %s using P4Runtime with file %s' % (sw, runtime_json))

            with open(runtime_json, 'r') as sw_conf_file:
                outfile = '%s/%s-p4runtime-requests.txt' % (self.log_dir, sw)
                simple_controller.program_switch(
                    addr='127.0.0.1:%d' % sw_obj.grpc_port,
                    device_id=sw_obj.device_id,
                    sw_conf_file=sw_conf_file,
                    workdir=os.getcwd(),
                    proto_dump_fpath=outfile,
                    runtime_json=runtime_json
                )


Runner(p4_list=['l2', 'l3'], switches=['r1', 's1', 's2']).run()
