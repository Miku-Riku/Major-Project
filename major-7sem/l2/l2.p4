#include <core.p4>
#include <v1model.p4>

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
    apply { }
}

control L2_Ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action mac_forward(egress_spec_t port) {
        standard_metadata.egress_spec = port;
    }

    table ethernet_exact {
        key = {
            hdr.ethernet.dstAddr: exact;
        }
        actions = {
            mac_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    apply {
        if (hdr.ethernet.isValid()) {
            ethernet_exact.apply();
        }
    }
}

control L2_Egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    apply {  }
}

control L2_ComputeChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}

control L2_Deparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        // packet.emit(hdr.ipv4);
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
