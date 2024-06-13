import sys
import time

from hdrs import Records, RecordData, scapy

dst_mac=sys.argv[1]

def main():
    pkt = scapy.Ether(dst=dst_mac, src=scapy.get_if_hwaddr("eth0")) / \
        Records(records=0)
    
    while True:
        try:
            scapy.sendp(pkt, iface="eth0")
            time.sleep(0.1)
        except KeyboardInterrupt:
            sys.exit()


if __name__ == "__main__":
    main()
