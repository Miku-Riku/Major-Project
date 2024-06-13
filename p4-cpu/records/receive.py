from hdrs import RecordData, Records, scapy

def expand(x):
    yield x
    while x.payload:
        x = x.payload
        yield x


def handle_pkt(pkt, f):
    if RecordData in pkt:
        data_layers = [l for l in expand(pkt) if l.name == "RecordData"]
        print("")
        for sw in data_layers:
            print(f"dpid: {sw.dpid}; cpu: {sw.cpu}; time: {sw.timestamp}")
            f.write(f"{sw.dpid},{sw.cpu},{sw.timestamp}\n")


def main():
    f = open("records/cpu.csv", "+a")

    iface = "eth0"
    print(f"sniffing on {iface}")
    try:
        scapy.sniff(iface=iface, prn=lambda x: handle_pkt(x, f))
    except KeyboardInterrupt:
        f.close()


if __name__ == "__main__":
    main()
