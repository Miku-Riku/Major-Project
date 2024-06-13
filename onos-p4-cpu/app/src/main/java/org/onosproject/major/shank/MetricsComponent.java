/*
 * Copyright 2019-present Open Networking Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.onosproject.major.shank;

import org.apache.commons.lang3.tuple.Pair;
import org.onlab.packet.MacAddress;
import org.onosproject.core.ApplicationId;
import org.onosproject.major.shank.common.Utils;
import org.onosproject.mastership.MastershipService;
import org.onosproject.net.DeviceId;
import org.onosproject.net.PortNumber;
import org.onosproject.net.config.NetworkConfigService;
import org.onosproject.net.device.DeviceEvent;
import org.onosproject.net.device.DeviceListener;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.flow.*;
import org.onosproject.net.flow.criteria.PiCriterion;
import org.onosproject.net.group.GroupService;
import org.onosproject.net.intf.InterfaceService;
import org.onosproject.net.pi.model.PiActionId;
import org.onosproject.net.pi.model.PiActionParamId;
import org.onosproject.net.pi.model.PiMatchFieldId;
import org.onosproject.net.pi.runtime.PiAction;
import org.onosproject.net.pi.runtime.PiActionParam;
import org.osgi.service.component.annotations.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.SocketException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Vector;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import static org.onosproject.major.shank.AppConstants.INITIAL_SETUP_DELAY;

/**
 * App component that configures devices to provide L2 bridging capabilities.
 */
@Component(
        immediate = true,
        // *** TODO EXERCISE 4
        // Enable component (enabled = true)
        enabled = true
)
public class MetricsComponent {

    private final Logger log = LoggerFactory.getLogger(getClass());

    private final DeviceListener deviceListener = new InternalDeviceListener();

    private ApplicationId appId;

    //--------------------------------------------------------------------------
    // ONOS CORE SERVICE BINDING
    //
    // These variables are set by the Karaf runtime environment before calling
    // the activate() method.
    //--------------------------------------------------------------------------

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private DeviceService deviceService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private InterfaceService interfaceService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private NetworkConfigService configService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private FlowRuleService flowRuleService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private GroupService groupService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private MastershipService mastershipService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    private MainComponent mainComponent;

    //--------------------------------------------------------------------------
    // COMPONENT ACTIVATION.
    //
    // When loading/unloading the app the Karaf runtime environment will call
    // activate()/deactivate().
    //--------------------------------------------------------------------------

    private final HashMap<DeviceId, Pair<MacAddress, Integer>> swIds = new HashMap<>();
    private final int[][] swPorts = new int[5][5];
    private final ExecutorService executorService = Executors.newSingleThreadExecutor();

    private DatagramSocket socket;

    @Activate
    protected void activate() {
        appId = mainComponent.getAppId();
        populateSwIds();

        // Register listeners to be informed about device and host events.
        deviceService.addListener(deviceListener);
        // Schedule set up of existing devices. Needed when reloading the app.
        mainComponent.scheduleTask(this::setUpAllDevices, INITIAL_SETUP_DELAY);

        try {
            socket = new DatagramSocket(4445);
            log.info("Listening for metrics on port {}", socket.getLocalPort());
        } catch (SocketException e) {
            throw new RuntimeException(e);
        }

        executorService.execute(this::metricListener);

        log.info("Started");
    }

    @Deactivate
    protected void deactivate() {
        deviceService.removeListener(deviceListener);
        executorService.shutdown();

        log.info("Stopped");
    }

    //--------------------------------------------------------------------------
    // METHODS TO COMPLETE.
    //
    // Complete the implementation wherever you see TODO.
    //--------------------------------------------------------------------------

    /**
     * Sets up everything necessary to support L2 bridging on the given device.
     *
     * @param deviceId the device to set up
     */
    private void setUpDevice(DeviceId deviceId) {
        final String tableId = "EgressPipeImpl.sw_metric";

        Pair<MacAddress, Integer> metric = swIds.get(deviceId);
        if (metric == null) {
            metric = Pair.of(MacAddress.valueOf("FF:FF:FF:FF:FF:FF"), 0);
        }

//        log.info("Updating metric rule for {} with {}", deviceId, metric.getRight());

        final PiCriterion hostMacCriterion = PiCriterion.builder()
                .matchExact(
                        PiMatchFieldId.of("hdr.ethernet.ether_type"),
                        AppConstants.ETHER_TYPE_PROBE)
                .build();

        // Action: set output port
        final PiAction action = PiAction.builder()
                .withId(PiActionId.of("EgressPipeImpl.set_metrics"))
                .withParameters(List.of(
                        new PiActionParam(
                                PiActionParamId.of("dpid"),
                                metric.getLeft().toBytes()),
                        new PiActionParam(
                                PiActionParamId.of("cpu"),
                                metric.getRight())
                ))
                .build();
        // ---- END SOLUTION ----

        // Forge flow rule.
        final FlowRule rule = Utils.buildFlowRule(
                deviceId, appId, tableId, hostMacCriterion, action);

        // Insert.
        flowRuleService.applyFlowRules(rule);
    }

    private void metricListener() {
        while (true) {
            try {
                byte[] buffer = new byte[255];
                DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                socket.receive(packet);

//                int port = packet.getPort();
//                log.info("Received packet from port {}", port);

                String[] fields = toData(packet.getData()).split(",");
                DeviceId deviceId = DeviceId.deviceId(fields[0]);
                int cpuInfo = Math.min(250, Integer.parseInt(fields[1]));

                Pair<MacAddress, Integer> metric = swIds.get(deviceId);
                if (metric == null) {
                    continue;
                }
                swIds.put(deviceId, Pair.of(metric.getLeft(), cpuInfo));
                setUpDevice(deviceId);

//                updateCongestionFlows();
            } catch (Exception e) {
                log.error("Error while parsing metric", e);
                break;
            }
        }
    }

    private String toData(byte[] buff) {
        StringBuilder builder = new StringBuilder();
        for (byte b : buff) {
            if (b == 0) continue;
            builder.append((char) b);
        }
        return builder.toString();
    }

    private static final int INF = 511;

    private void updateCongestionFlows() {
        boolean applyCongestionFlow = false;
        int[] swm = new int[5];
        for (Map.Entry<DeviceId, Pair<MacAddress, Integer>> entry : swIds.entrySet()) {
            String id = entry.getKey().toString();
            Pair<MacAddress, Integer> metric = entry.getValue();
            swm[Integer.parseInt(id.substring(id.length() - 1))] = metric.getRight();
            applyCongestionFlow = applyCongestionFlow || metric.getRight() > 80;
        }

        if (!applyCongestionFlow) {
            L2BridgingComponent.deviceFlows
                    .forEach((hostMac, flows) ->
                            flows.forEach((p) ->
                                    L2BridgingComponent.updateFlowRule(
                                            flowRuleService,
                                            p.getRight(),
                                            hostMac,
                                            p.getLeft(),
                                            appId
                                    )
                            )
                    );
            return;
        }

        FloydWarshallNetwork network = getNetwork(swm);

        L2BridgingComponent.deviceFlows.forEach((hostMac, flows) -> {
            int dst = Utils.getSwitchIdFromHostMac(hostMac);
            if (dst == 0) return;
            flows.forEach((p) -> {
                int src = Utils.getSwitchIdFromDeviceId(p.getRight());
                if (src == 0) return;
                if (src == dst) return;

                Vector<Integer> path = network.getPath(src, dst);
                if (path == null || path.size() < 3) {
                    return;
                }

                for (int i = 0; i < path.size() - 1; i++) {
                    Integer sw = path.get(i);
                    Integer swNext = path.get(i + 1);

                    L2BridgingComponent.updateFlowRule(
                            flowRuleService,
                            DeviceId.deviceId("device:s" + sw),
                            hostMac,
                            PortNumber.portNumber(swPorts[sw][swNext]),
                            appId
                    );
                }
            });
        });
    }

    private static FloydWarshallNetwork getNetwork(int[] swm) {
        FloydWarshallNetwork network = new FloydWarshallNetwork(
                new int[][]{
                        //       0,     1,      2,      3,      4
                        /* 0 */ {0, swm[1], swm[2], swm[3], swm[4]},
                        /* 1 */ {swm[0], 0, swm[2], INF, swm[4]},
                        /* 2 */ {swm[0], swm[1], 0, swm[3], INF},
                        /* 3 */ {swm[0], INF, swm[2], 0, swm[4]},
                        /* 4 */ {swm[0], swm[1], INF, swm[3], 0},
                }
        );
        network.compute();
        return network;
    }

    static class FloydWarshallNetwork {
        private static final int MAX_N = 5;

        private final int[][] graph = new int[MAX_N][MAX_N];
        private final int[][] subSeq = new int[MAX_N][MAX_N];

        int V;

        FloydWarshallNetwork(int[][] graph) {
            V = graph.length;
            for (int i = 0; i < V; i++) {
                for (int j = 0; j < V; j++) {
                    this.graph[i][j] = graph[i][j];
                    subSeq[i][j] = this.graph[i][j] == INF ? -1 : j;
                }
            }
        }

        void compute() {
            for (int k = 0; k < V; k++) {
                for (int i = 0; i < V; i++) {
                    for (int j = 0; j < V; j++) {
                        if (graph[i][k] == INF || graph[k][j] == INF) {
                            continue;
                        }
                        if (graph[i][j] > graph[i][k] + graph[k][j]) {
                            graph[i][j] = graph[i][k] + graph[k][j];
                            subSeq[i][j] = subSeq[i][k];
                        }
                    }
                }
            }
        }

        Vector<Integer> getPath(int u, int v) {
            if (subSeq[u][v] == -1) {
                return new Vector<>();
            }

            Vector<Integer> path = new Vector<>();
            path.add(u);
            while (u != v) {
                u = subSeq[u][v];
                path.add(u);
            }
            return path;
        }
    }

//--------------------------------------------------------------------------
// EVENT LISTENERS
//
// Events are processed only if isRelevant() returns true.
//--------------------------------------------------------------------------

    /**
     * Listener of device events.
     */
    public class InternalDeviceListener implements DeviceListener {

        @Override
        public boolean isRelevant(DeviceEvent event) {
            switch (event.type()) {
                case DEVICE_ADDED:
                case DEVICE_AVAILABILITY_CHANGED:
                    break;
                default:
                    // Ignore other events.
                    return false;
            }
            // Process only if this controller instance is the master.
            final DeviceId deviceId = event.subject().id();
            return mastershipService.isLocalMaster(deviceId);
        }

        @Override
        public void event(DeviceEvent event) {
            final DeviceId deviceId = event.subject().id();
            if (deviceService.isAvailable(deviceId)) {
                // A P4Runtime device is considered available in ONOS when there
                // is a StreamChannel session open and the pipeline
                // configuration has been set.

                // Events are processed using a thread pool defined in the
                // MainComponent.
                mainComponent.getExecutorService().execute(() -> {
                    log.info("{} event! deviceId={}", event.type(), deviceId);

                    setUpDevice(deviceId);
                });
            }
        }
    }

//--------------------------------------------------------------------------
// UTILITY METHODS
//--------------------------------------------------------------------------

    /**
     * Sets up L2 bridging on all devices known by ONOS and for which this ONOS
     * node instance is currently master.
     * <p>
     * This method is called at component activation.
     */
    private void setUpAllDevices() {
        deviceService.getAvailableDevices().forEach(device -> {
            if (mastershipService.isLocalMaster(device.id())) {
                log.info("*** MetricsComp - Starting initial set up for {}...", device.id());
                setUpDevice(device.id());
            }
        });
    }

    private void populateSwIds() {
        swIds.put(DeviceId.deviceId("device:s0"), Pair.of(MacAddress.valueOf("AA:00:00:00:00:00"), 0));
        swIds.put(DeviceId.deviceId("device:s1"), Pair.of(MacAddress.valueOf("11:00:00:00:00:00"), 0));
        swIds.put(DeviceId.deviceId("device:s2"), Pair.of(MacAddress.valueOf("22:00:00:00:00:00"), 0));
        swIds.put(DeviceId.deviceId("device:s3"), Pair.of(MacAddress.valueOf("33:00:00:00:00:00"), 0));
        swIds.put(DeviceId.deviceId("device:s4"), Pair.of(MacAddress.valueOf("44:00:00:00:00:00"), 0));

        swPorts[0][1] = 1;
        swPorts[0][2] = 2;
        swPorts[0][3] = 3;
        swPorts[0][4] = 4;

        swPorts[1][0] = 3;
        swPorts[1][2] = 5;
        swPorts[1][4] = 4;

        swPorts[2][0] = 3;
        swPorts[2][1] = 4;
        swPorts[2][3] = 5;

        swPorts[3][0] = 3;
        swPorts[3][2] = 4;
        swPorts[3][4] = 5;

        swPorts[4][0] = 3;
        swPorts[4][1] = 5;
        swPorts[4][3] = 4;
    }
}
