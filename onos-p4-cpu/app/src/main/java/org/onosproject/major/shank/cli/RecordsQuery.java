package org.onosproject.major.shank.cli;

import org.apache.commons.lang3.tuple.Pair;
import org.apache.karaf.shell.api.action.Argument;
import org.apache.karaf.shell.api.action.Command;
import org.apache.karaf.shell.api.action.Completion;
import org.apache.karaf.shell.api.action.lifecycle.Service;
import org.onosproject.cli.AbstractShellCommand;
import org.onosproject.cli.net.DeviceIdCompleter;
import org.onosproject.cli.net.HostIdCompleter;
import org.onosproject.major.shank.common.MetricRecorder;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onosproject.net.Host;
import org.onosproject.net.HostId;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.host.HostService;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@Command(scope = "onos", name = "records", description = "Get CPU records of switches based on srcMac, dstMac and provider")
public class RecordsQuery extends AbstractShellCommand {

    @Argument(index = 0, name = "src", description = "Source MacAddress", required = false, multiValued = false)
    @Completion(HostIdCompleter.class)
    String src = null;

    @Argument(index = 1, name = "dst", description = "Destination MacAddress", required = false, multiValued = false)
    @Completion(HostIdCompleter.class)
    String dst = null;

    @Argument(index = 2, name = "provider", description = "Provider switch", required = false, multiValued = false)
    @Completion(DeviceIdCompleter.class)
    String provider = null;

    @Override
    protected void doExecute() {
        if (src == null && dst == null) {
            print("Mention at least either for src or dst host id");
            return;
        }

        DeviceService deviceService = get(DeviceService.class);
        HostService hostService = get(HostService.class);

        Device device;
        if (provider != null) {
            device = deviceService.getDevice(DeviceId.deviceId(provider));
            if (device == null) {
                print("Device not found: '%s'", provider);
                return;
            }
        } else {
            device = null;
        }

        Host srcHost, dstHost;
        if (src != null) {
            srcHost = hostService.getHost(HostId.hostId(src));
            if (srcHost == null) {
                print("Source host not found: '%s'", src);
                return;
            }
        } else {
            srcHost = null;
        }
        if (dst != null) {
            dstHost = hostService.getHost(HostId.hostId(dst));
            if (dstHost == null) {
                print("Destination host not found: '%s'", dst);
                return;
            }
        } else {
            dstHost = null;
        }

        List<MetricRecorder.Record> op = MetricRecorder.getDbRecords()
                .entrySet()
                .stream()
                .filter(pairListEntry -> {
                    if (srcHost != null) {
                        if (dstHost != null) {
                            return pairListEntry.getKey().equals(Pair.of(srcHost.mac(), dstHost.mac()));
                        }
                        return pairListEntry.getKey().getLeft().equals(srcHost.mac());
                    }
                    return false;
                })
                .map(Map.Entry::getValue)
                .reduce(new ArrayList<>(), (acc, records) -> {
                    acc.addAll(
                            records.stream()
                                    .filter(record -> {
                                        if (device != null) {
                                            return record.getProvider().equals(device.id());
                                        }
                                        return true;
                                    })
                                    .collect(Collectors.toList())
                    );
                    return acc;
                });

        op.sort((o1, o2) -> o1.getTimestamp() > o2.getTimestamp() ? 1 : 0);

        for (MetricRecorder.Record record : op) {
            print("DPID: %s; CPU: %s; Timestamp: %s", record.getDpid(), record.getCpu(), record.getTimestamp());
        }
        print("-------------------");
    }
}
