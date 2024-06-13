import sys
import os
from time import sleep

sys.path.append("..")

from core.p4runtime_lib import simple_controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.topo import Topo
from core.p4_mininet import P4Host
from core.run_exercise import configureP4Switch

class Runner():
    def __init__(self, p4_list, switches):
        self.p4_switch_classes = {}
        self.p4_list = p4_list
        self.switches = switches
        self.cwd = os.getcwd()
        self.log_dir = os.path.join(self.cwd, 'logs')
        self.pcap_dir = os.path.join(self.cwd, 'pcaps')

        mret = os.system("mkdir -p build pcaps logs")
        if mret != 0:
            print(f"Unable to make dirs")
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
        h2 = topo.addHost('h2', ip="10.0.0.2/24", mac="00:00:00:00:02:00")
        self.hosts = [h1, h2]

        r1 = topo.addSwitch('r1', log_file="%s/%s.log" %(self.log_dir, 'r1'), cls=self.p4_switch_classes['l3'])
        topo.addLink(h1, r1, port2=1)
        topo.addLink(h2, r1, port2=2)

        self.net = Mininet(topo=topo, link=TCLink, host=P4Host, controller=None)
        self.net.start()

    def configure_hosts(self):
        self.net['h1'].cmd("route add default gw 192.168.1.1 dev eth0")
        self.net['h1'].cmd("arp -i eth0 -s 192.168.1.1 00:00:00:00:01:10")

        self.net['h2'].cmd("route add default gw 10.0.0.1 dev eth0")
        self.net['h2'].cmd("arp -i eth0 -s 10.0.0.1 00:00:00:00:02:10")

    def configure_switches(self):
        for sw in self.switches:
            sw_obj = self.net[sw]
            runtime_json = f'topo/{sw}_runtime.json'
            print('Configuring switch %s using P4Runtime with file %s' % (sw, runtime_json))
            
            with open(runtime_json, 'r') as sw_conf_file:
                outfile = '%s/%s-p4runtime-requests.txt' %(self.log_dir, sw)
                simple_controller.program_switch(
                    addr='127.0.0.1:%d' % sw_obj.grpc_port,
                    device_id=sw_obj.device_id,
                    sw_conf_file=sw_conf_file,
                    workdir=os.getcwd(),
                    proto_dump_fpath=outfile,
                    runtime_json=runtime_json
                )

Runner(p4_list=['l3'], switches=['r1']).run()
