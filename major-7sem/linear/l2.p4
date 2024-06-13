#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;

typedef bit<9> egress_spec_t;
typedef bit<32> ip4Addr_t;
typedef bit<48> macAddr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16> etherType;
}

struct metadata {
    /* empty */
}

struct headers {
    ethernet_t ethernet;
}

parser L2_Parser(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition accept;
    }
}

control L2_VerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {}
}

control L2_Ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action multicast() {
        standard_metadata.mcast_grp = 1;
    }

    action mac_forward(egress_spec_t port) {
        standard_metadata.egress_spec = port;
    }

    table mac_table {
        key = {
            hdr.ethernet.dstAddr: exact;
        }
        actions = {
            multicast;
            mac_forward;
            drop;
            NoAction;
        }
        size = 1024;
    }

    apply {
        if (hdr.ethernet.isValid()) {
            if (hdr.ethernet.dstAddr == 48w0xFFFFFFFFFF) {
                multicast();
            } else {
                mac_table.apply();
            }
        }
    }
}

control L2_Egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    
    action drop() {
        mark_to_drop(standard_metadata);
    }

    apply {
        if (standard_metadata.egress_port == standard_metadata.ingress_port) {
            drop();
        }
    }
}

control L2_ComputeChecksum(inout headers hdr, inout metadata meta) {
    apply {}
}

control L2_Deparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
    }
}

V1Switch(
    L2_Parser(),
    L2_VerifyChecksum(),
    L2_Ingress(),
    L2_Egress(),
    L2_ComputeChecksum(),
    L2_Deparser()
) main;
