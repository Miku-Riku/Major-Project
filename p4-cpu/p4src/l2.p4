#include <core.p4>
#include <v1model.p4>

#include "../extern/cpu.p4"

#define MAX_REC 5

const bit<16> TYPE_REC = 0x819;

typedef bit<9> egress_spec_t;
typedef bit<32> ip4Addr_t;
typedef bit<48> macAddr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16> etherType;
}

header records_t {
    bit<8> records;
}

header record_data_t {
    macAddr_t dpid;
    bit<8> cpu;
    bit<64> timestamp;
}

struct parse_data_t {
    bit<8> remaining;
}

struct metadata {
    parse_data_t parse_data;
}

struct headers {
    ethernet_t ethernet;
    records_t records;
    record_data_t[MAX_REC] data;
}

parser L2_Parser(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select (hdr.ethernet.etherType) {
            TYPE_REC: parse_record;
            default: accept;
        }
    }

    state parse_record {
        packet.extract(hdr.records);
        meta.parse_data.remaining = hdr.records.records + 1;
        transition select (hdr.records.records) {
            0: accept;
            default: parse_record_data;
        }
    }

    state parse_record_data {
        packet.extract(hdr.data.next);
        meta.parse_data.remaining = meta.parse_data.remaining - 1;
        transition select (meta.parse_data.remaining) {
            0: accept;
            default: parse_record_data;
        }
    }
}

control L2_VerifyChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}

control L2_Ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action fwd_main() {
        standard_metadata.egress_spec = (egress_spec_t)3;
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
            fwd_main;
            drop;
            NoAction;
        }
        size = 1024;
        // default_action = drop();
    }

    apply {
        if (hdr.ethernet.isValid()) {
            ethernet_exact.apply();
        }
    }
}

control L2_Egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    action set_metrics(macAddr_t dpid, bit<8> sw) {
        hdr.data[0].dpid = dpid;
        set_cpu(hdr.data[0].cpu, sw);
        hdr.data[0].timestamp = (bit<64>)standard_metadata.egress_global_timestamp;
    }

    table sw_metrics {
        actions = {
            set_metrics;
            NoAction;
        }
        default_action = NoAction;
    }

    apply { 
        if (hdr.records.isValid()) {
            hdr.data.push_front(1);
            hdr.data[0].setValid();
            sw_metrics.apply();
            hdr.records.records = hdr.records.records + 1;
        }
    }
}

control L2_ComputeChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}

control L2_Deparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.records);
        packet.emit(hdr.data);
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
