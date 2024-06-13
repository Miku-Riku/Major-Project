# SDN - ONOS - P4 CPU utilization

## Introduction

This document describes the steps to monitor the CPU utilization of a P4 switch using ONOS.
Additionally re-routing the packets based on the CPU utilization of the switch using Floyd Warshall algorithm.

Reference: [ONOS Ngsdn](https://github.com/opennetworkinglab/ngsdn-tutorial)

## Prerequisites

- Docker
- Docker Compose
- Python
- Make
- Java (JDK 11)
- Maven
- IDE (IntelliJ IDEA / VS Code)

## Topology

![topology](image.png)

Switches: 5
- s0 - AA:00:00:00:00:00
- s1 - 11:00:00:00:00:00
- s2 - 22:00:00:00:00:00
- s3 - 33:00:00:00:00:00
- s4 - 44:00:00:00:00:00

Hosts: 8
- h10 - 00:00:00:00:00:01
- h11 - 00:00:00:00:00:02
- h20 - 00:00:00:00:00:03
- h21 - 00:00:00:00:00:04
- h30 - 00:00:00:00:00:05
- h31 - 00:00:00:00:00:06
- h40 - 00:00:00:00:00:07
- h41 - 00:00:00:00:00:08

## Setup the environment

- Clone the repository
    ```bash
    git clone https://github.com/shank03/Major-Project.git
    cd Major-Project/sdn-p4-cpu
    ```
- Get docker dependencies
    ```bash
    make deps
    ```

## Run the code

- Run the container and wait for it to finish
    ```bash
    make check
    ```
- Connect to mininet cli
    ```bash
    make mn-cli
    ...
    mininet> pingall # should ping all hosts
    ```
- Enter into hosts, here we will enter `h10` and `h30` for demonstration
    ```bash
    screen -m util/mn-cmd h10

    # Other terminal
    screen -m util/mn-cmd h30
    ```
- In `h10` terminal, run the following command
    ```bash
    python /records/send.py h10-eth0 00:00:00:00:05:00
    ```
- In `h30` terminal, run the following command
    ```bash
    python /records/receive.py h30-eth0
    ```
    You should be able to see the packets received in `h30` terminal.
- Now open mininet cli in another terminal and run the following command
    ```bash
    mininet> iperf <s> <d>
    ```
    changing `<s>` and `<d>` should reflect the CPU utilization metrics in `h30` terminal.