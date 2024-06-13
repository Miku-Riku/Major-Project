import pandas as pd
import sys
from matplotlib import pyplot as plt

csvFile = sys.argv[1]

if csvFile is None or len(csvFile) == 0:
    print("Please provide a CSV file to generate the graph.")
    sys.exit(1)

df = pd.read_csv(
    csvFile,
    names=["SrcMac", "DstMac", "Provider", "Switch", "CPU", "Timestamp"],
)
print("CSV contents: ", df)

plt.figure(figsize=(14, 7))

id = csvFile.split("-")[1].split(".")[0]

for srcMac, data in df.groupby("SrcMac"):
    for dstMac, data in df.groupby("DstMac"):
        for switch, data in df.groupby("Switch"):
            plt.plot(
                data["Timestamp"],
                data["CPU"],
                linestyle="solid",
                marker=".",
                label=switch,
            )

        plt.xlabel("Time in milliseconds")
        plt.ylabel("CPU Usage in %")
        plt.legend()
        plt.grid(True)
        plt.savefig("records/cpu-%s-%s-%s.png" % (id, srcMac, dstMac))
