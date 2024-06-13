from scapy import all as scapy

TYPE_REC = 0x819


class Records(scapy.Packet):
    fields_desc = [scapy.ByteField("records", 0)]


class RecordData(scapy.Packet):
    fields_desc = [scapy.MACField("dpid", 0), scapy.ByteField("cpu", 0), scapy.LongField("timestamp", 0)]


scapy.bind_layers(scapy.Ether, Records, type=TYPE_REC)
scapy.bind_layers(Records, RecordData)
scapy.bind_layers(RecordData, RecordData)
