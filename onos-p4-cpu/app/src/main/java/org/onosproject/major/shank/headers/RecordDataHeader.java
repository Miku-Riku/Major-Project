package org.onosproject.major.shank.headers;

import org.onlab.packet.BasePacket;
import org.onlab.packet.Deserializer;
import org.onlab.packet.MacAddress;
import org.onlab.packet.PacketUtils;

import java.math.BigInteger;
import java.nio.ByteBuffer;

public class RecordDataHeader extends BasePacket {

    public static final int SWITCH_DPID_LENGTH = 6;
    public static final int CPU_USAGE_LENGTH = 1;
    public static final int TIMESTAMP_LENGTH = 8;
    public static final int RECORD_DATA_HEADER_LENGTH = SWITCH_DPID_LENGTH + CPU_USAGE_LENGTH + TIMESTAMP_LENGTH;

    protected MacAddress dpid;
    protected int cpuUsage;
    protected long timestamp;

    public RecordDataHeader() {
        dpid = MacAddress.ZERO;
        cpuUsage = 0;
        timestamp = 0;
    }

    public MacAddress getDpid() {
        return dpid;
    }

    public int getCpuUsage() {
        return cpuUsage;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public void setDpid(byte[] dpid) {
        this.dpid = MacAddress.valueOf(dpid);
    }

    public void setCpuUsage(byte cpuUsage) {
        this.cpuUsage = Byte.toUnsignedInt(cpuUsage);
    }

    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }

    @Override
    public byte[] serialize() {
        return new byte[0];
    }

    public static Deserializer<RecordDataHeader> deserializer() {
        return (data, offset, length) -> {
            PacketUtils.checkInput(data, offset, length, RECORD_DATA_HEADER_LENGTH);

            byte[] macData = new byte[SWITCH_DPID_LENGTH];
            byte[] cpuData = new byte[CPU_USAGE_LENGTH];
            byte[] timestampData = new byte[TIMESTAMP_LENGTH];

            ByteBuffer bb = ByteBuffer.wrap(data, offset, length);
            bb.get(macData);
            bb.get(cpuData);
            bb.get(timestampData);

            RecordDataHeader recordData = new RecordDataHeader();
            recordData.setDpid(macData);
            recordData.setCpuUsage(cpuData[0]);
            recordData.setTimestamp(new BigInteger(timestampData).longValue());
            return recordData;
        };
    }
}
