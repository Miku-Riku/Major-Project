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


class Runner:
    def __init__(self, p4_list, switches):
        self.p4_switch_classes = {}
        self.p4_list = p4_list
        self.switches = switches
        self.cwd = os.getcwd()
        self.log_dir = os.path.join(self.cwd, "logs")
        self.pcap_dir = os.path.join(self.cwd, "pcaps")

        mret = os.system("mkdir -p build pcaps logs")
        if mret != 0:
            print(f"Unable to make dirs")
            exit(-1)

        for p4 in p4_list:
            switch_json = f"build/{p4}.json"
            self.p4_switch_classes[f"{p4}"] = configureP4Switch(
                sw_path="simple_switch_grpc",
                json_path=switch_json,
                log_console=True,
                pcap_dump=self.pcap_dir,
                modules=["extern/cpu.so"],
            )

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

        f = open("records/cpu.csv", "w")
        f.write("")
        f.close()

        print("Starting mininet CLI")
        CLI(self.net)
        self.net.stop()

    def configure_topo(self):
        topo = Topo()

        h1 = topo.addHost("h10", ip="192.168.1.2/24", mac="00:00:00:00:01:00")
        h2 = topo.addHost("h11", ip="192.168.1.3/24", mac="00:00:00:00:02:00")
        h3 = topo.addHost("h20", ip="192.168.1.4/24", mac="00:00:00:00:03:00")
        h4 = topo.addHost("h21", ip="192.168.1.5/24", mac="00:00:00:00:04:00")
        h5 = topo.addHost("h30", ip="192.168.1.6/24", mac="00:00:00:00:05:00")
        h6 = topo.addHost("h31", ip="192.168.1.7/24", mac="00:00:00:00:06:00")
        h7 = topo.addHost("h40", ip="192.168.1.8/24", mac="00:00:00:00:07:00")
        h8 = topo.addHost("h41", ip="192.168.1.9/24", mac="00:00:00:00:08:00")
        self.hosts = [h1, h2, h3, h4, h5, h6, h7, h8]

        s0 = topo.addSwitch(
            "s0",
            log_file="%s/%s.log" % (self.log_dir, "s0"),
            cls=self.p4_switch_classes["l2"],
        )
        s1 = topo.addSwitch(
            "s1",
            log_file="%s/%s.log" % (self.log_dir, "s1"),
            cls=self.p4_switch_classes["l2"],
        )
        s2 = topo.addSwitch(
            "s2",
            log_file="%s/%s.log" % (self.log_dir, "s2"),
            cls=self.p4_switch_classes["l2"],
        )
        s3 = topo.addSwitch(
            "s3",
            log_file="%s/%s.log" % (self.log_dir, "s3"),
            cls=self.p4_switch_classes["l2"],
        )
        s4 = topo.addSwitch(
            "s4",
            log_file="%s/%s.log" % (self.log_dir, "s4"),
            cls=self.p4_switch_classes["l2"],
        )

        topo.addLink(h1, s1, port2=1)
        topo.addLink(h2, s1, port2=2)

        topo.addLink(h3, s2, port2=1)
        topo.addLink(h4, s2, port2=2)

        topo.addLink(h5, s3, port2=1)
        topo.addLink(h6, s3, port2=2)

        topo.addLink(h7, s4, port2=1)
        topo.addLink(h8, s4, port2=2)

        topo.addLink(s0, s1, port1=1, port2=3)
        topo.addLink(s0, s2, port1=2, port2=3)
        topo.addLink(s0, s3, port1=3, port2=3)
        topo.addLink(s0, s4, port1=4, port2=3)

        self.net = Mininet(topo=topo, link=TCLink, host=P4Host, controller=None)
        self.net.start()

    def fill_arp_table(self, host_name):
        hosts = [
            ("h10", "192.168.1.2", "00:00:00:00:01:00"),
            ("h11", "192.168.1.3", "00:00:00:00:02:00"),
            ("h20", "192.168.1.4", "00:00:00:00:03:00"),
            ("h21", "192.168.1.5", "00:00:00:00:04:00"),
            ("h30", "192.168.1.6", "00:00:00:00:05:00"),
            ("h31", "192.168.1.7", "00:00:00:00:06:00"),
            ("h40", "192.168.1.8", "00:00:00:00:07:00"),
            ("h41", "192.168.1.9", "00:00:00:00:08:00"),
        ]
        for name, ip, mac in hosts:
            if name == host_name:
                continue
            self.net[host_name].cmd(f"arp -i eth0 -s {ip} {mac}")

    def configure_hosts(self):
        for host_name in ["h10", "h11", "h20", "h21", "h30", "h31", "h40", "h41"]:
            self.net[host_name].cmd("ip route add 192.168.1.0/24 dev eth0")
            self.fill_arp_table(host_name)

    def configure_switches(self):
        for sw in self.switches:
            sw_obj = self.net[sw]
            runtime_json = f"topo/{sw}_runtime.json"
            print(
                "Configuring switch %s using P4Runtime with file %s"
                % (sw, runtime_json)
            )

            with open(runtime_json, "r") as sw_conf_file:
                outfile = "%s/%s-p4runtime-requests.txt" % (self.log_dir, sw)
                simple_controller.program_switch(
                    addr="127.0.0.1:%d" % sw_obj.grpc_port,
                    device_id=sw_obj.device_id,
                    sw_conf_file=sw_conf_file,
                    workdir=os.getcwd(),
                    proto_dump_fpath=outfile,
                    runtime_json=runtime_json,
                )


Runner(p4_list=["l2"], switches=["s0", "s1", "s2", "s3", "s4"]).run()
