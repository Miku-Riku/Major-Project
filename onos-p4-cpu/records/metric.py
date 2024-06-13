import time
import socket
import subprocess

UDP_IP = "172.24.0.3"
UDP_PORT = 4445

pid_map = {}
switches = ["s0", "s1", "s2", "s3", "s4"]
sockets = {}
for s in switches:
    sockets[s] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ps = subprocess.Popen(
        "ps aux | grep %s | grep stratum | awk '{print $2}'" % s,
        stdout=subprocess.PIPE,
        shell=True,
    )
    (pOp, e) = ps.communicate()
    ps.wait()

    pid_map[s] = {"pid": str(pOp).split("\n")[0], "cpu": 0}

print("PIDs: ", pid_map)

while True:
    try:
        for k, v in pid_map.items():
            proc = subprocess.Popen(
                "top -b -n 1 -p %s | tail -n 1 | awk '{print $9}'" % v["pid"],
                stdout=subprocess.PIPE,
                shell=True,
            )
            (op, err) = proc.communicate()
            proc.wait()

            cpu = str(op).split("\n")[0]
            try:
                pid_map[k]["cpu"] = int(round(float(cpu)))
            except:
                pid_map[k]["cpu"] = 0

        for s in switches:
            sockets[s].sendto(
                ("device:%s,%s" % (s, str(pid_map[s]["cpu"]))).encode(),
                (UDP_IP, UDP_PORT),
            )

        time.sleep(0.01)
    except KeyboardInterrupt:
        for s in switches:
            sockets[s].close()
        exit(0)
