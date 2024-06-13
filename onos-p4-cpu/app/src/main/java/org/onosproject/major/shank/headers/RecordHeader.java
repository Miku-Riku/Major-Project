package org.onosproject.major.shank.headers;

import org.onlab.packet.BasePacket;
import org.onlab.packet.Deserializer;
import org.onlab.packet.PacketUtils;

import java.nio.ByteBuffer;

public class RecordHeader extends BasePacket {

    public static final int NUM_RECORDS_LENGTH = 1;
    public static final int ETH_TYPE_LENGTH = 2;
    public static final int RECORD_HEADER_LENGTH = NUM_RECORDS_LENGTH + ETH_TYPE_LENGTH;

    protected int numberOfRecords;
    protected short ethType;

    public RecordHeader() {
        numberOfRecords = 0;
    }

    public short getEthType() {
        return ethType;
    }

    public void setEthType(short ethType) {
        this.ethType = ethType;
    }

    public int getNumberOfRecords() {
        return numberOfRecords;
    }

    public void setNumberOfRecords(byte numberOfRecords) {
        this.numberOfRecords = Byte.toUnsignedInt(numberOfRecords);
    }

    @Override
    public byte[] serialize() {
        return new byte[0];
    }

    public static Deserializer<RecordHeader> deserializer() {
        return (data, offset, length) -> {
            PacketUtils.checkInput(data, offset, length, RECORD_HEADER_LENGTH);

            byte[] payloadData = new byte[NUM_RECORDS_LENGTH];
            ByteBuffer bb = ByteBuffer.wrap(data, offset, length);

            RecordHeader recordHeader = new RecordHeader();
            bb.get(payloadData);
            recordHeader.setNumberOfRecords(payloadData[0]);
            recordHeader.setEthType(bb.getShort());
            return recordHeader;
        };
    }
}
