import sys
import time

from hdrs import Records, RecordData, scapy

ifname = sys.argv[1]
dst_mac = sys.argv[2]


def main():
    pkt = scapy.Ether(dst=dst_mac, src=scapy.get_if_hwaddr(ifname)) / Records(records=0)

    while True:
        try:
            scapy.sendp(pkt, iface=ifname)
            time.sleep(0.5)
        except KeyboardInterrupt:
            sys.exit()


if __name__ == "__main__":
    main()
