#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_ARP = 0x806;

const bit<16> ARP_OPER_REQUEST   = 1;
const bit<16> ARP_OPER_REPLY     = 2;

typedef bit<9>  egress_spec_t;
typedef bit<32> ip4Addr_t;
typedef bit<48> macAddr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header arp_t {
    bit<16>   hardwareType;
    bit<16>   protocolType;
    bit<8>    hardwareLen;
    bit<8>    protocolLen;
    bit<16>   opCode;
    macAddr_t senderHwAddr;
    ip4Addr_t senderIpAddr;
    macAddr_t targetHwAddr;
    ip4Addr_t targetIpAddr;
}

struct metadata {
    ip4Addr_t dstIp;
}

struct headers {
    ethernet_t ethernet;
    arp_t      arp;
    ipv4_t     ipv4;
}

parser L3_Parser(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            TYPE_ARP: parse_arp;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        meta.dstIp = hdr.ipv4.dstAddr;
        transition accept;
    }

    state parse_arp {
        packet.extract(hdr.arp);
        meta.dstIp = hdr.arp.targetIpAddr;
        transition accept;
    }
}

control L3_VerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {}
}

control L3_Ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action set_dst_egress(egress_spec_t port) {
        standard_metadata.egress_spec = port;
    }

    action ipv4_forward(macAddr_t dstAddr) {
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action arp_reply(macAddr_t srcAddr) {
        standard_metadata.egress_spec = standard_metadata.ingress_port;
        hdr.ethernet.dstAddr = hdr.ethernet.srcAddr;
        hdr.ethernet.srcAddr = srcAddr;

        hdr.arp.targetHwAddr = hdr.arp.senderHwAddr;
        hdr.arp.senderHwAddr = srcAddr;

        ip4Addr_t tmp = hdr.arp.targetIpAddr;
        hdr.arp.targetIpAddr = hdr.arp.senderIpAddr;
        hdr.arp.senderIpAddr = tmp;

        hdr.arp.opCode = ARP_OPER_REPLY;
    }

    action forward(macAddr_t macAddr) {
        if (hdr.arp.isValid() && hdr.arp.opCode == ARP_OPER_REQUEST) {
            arp_reply(macAddr);
        } else if (hdr.ipv4.isValid()) {
            ipv4_forward(macAddr);
        }
    }

    table ipv4_lpm {
        key = {
            meta.dstIp: lpm;
        }
        actions = {
            set_dst_egress;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    table mac_table {
        key = {
            meta.dstIp: exact;
        }
        actions = {
            forward;
            drop;
        }
        size = 1024;
        default_action = drop();
    }

    apply {
        ipv4_lpm.apply();
        mac_table.apply();
    }
}

control L3_Egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    apply {}
}

control L3_ComputeChecksum(inout headers hdr, inout metadata meta) {
    apply {
        update_checksum(
            hdr.ipv4.isValid(),
            {
                hdr.ipv4.version,
                hdr.ipv4.ihl,
                hdr.ipv4.diffserv,
                hdr.ipv4.totalLen,
                hdr.ipv4.identification,
                hdr.ipv4.flags,
                hdr.ipv4.fragOffset,
                hdr.ipv4.ttl,
                hdr.ipv4.protocol,
                hdr.ipv4.srcAddr,
                hdr.ipv4.dstAddr
            },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16
        );
    }
}

control L3_Deparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.arp);
    }
}

V1Switch(
    L3_Parser(),
    L3_VerifyChecksum(),
    L3_Ingress(),
    L3_Egress(),
    L3_ComputeChecksum(),
    L3_Deparser()
) main;
