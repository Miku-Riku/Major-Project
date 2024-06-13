package org.onosproject.major.shank.cli;

import org.apache.karaf.shell.api.action.Argument;
import org.apache.karaf.shell.api.action.Command;
import org.apache.karaf.shell.api.action.Completion;
import org.apache.karaf.shell.api.action.lifecycle.Service;
import org.onosproject.cli.AbstractShellCommand;
import org.onosproject.cli.net.HostIdCompleter;
import org.onosproject.major.shank.MetricsComponent;
import org.onosproject.net.Host;
import org.onosproject.net.HostId;
import org.onosproject.net.host.HostService;

@Service
@Command(scope = "onos", name = "start-rec", description = "Start recording CPU usage along the path of mentioned src and dst")
public class AddRecorder extends AbstractShellCommand {

    @Argument(index = 0, name = "src", description = "Source MacAddress", required = true, multiValued = false)
    @Completion(HostIdCompleter.class)
    String src = null;

    @Argument(index = 1, name = "dst", description = "Destination MacAddress", required = true, multiValued = false)
    @Completion(HostIdCompleter.class)
    String dst = null;

    @Override
    protected void doExecute() {
        if (src == null && dst == null) {
            print("Mention src and dst MacAddress");
            return;
        }

        HostService hostService = get(HostService.class);
        MetricsComponent metricsComponent = get(MetricsComponent.class);

        Host srcHost = hostService.getHost(HostId.hostId(src));
        if (srcHost == null) {
            print("No such src host: '%s'", src);
            return;
        }
        Host dstHost = hostService.getHost(HostId.hostId(dst));
        if (dstHost == null) {
            print("No such dst host: '%s'", dst);
            return;
        }

        metricsComponent.enableRecording(srcHost, dstHost);
        print("Started recording CPU for %s - %s", srcHost.id(), dstHost.id());
    }
}
