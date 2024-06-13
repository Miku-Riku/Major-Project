import pandas as pd
from matplotlib import pyplot as plt

df = pd.read_csv("records/cpu.csv", names=["Switch", "CPU", "Timestamp"])
print("CSV contents: ", df)

plt.figure(figsize=(14, 7))

for switch, data in df.groupby("Switch"):
    plt.plot(data["Timestamp"], data["CPU"], linestyle='solid', marker='.', label=switch)

plt.xlabel("Time in milliseconds")
plt.ylabel("CPU Usage in %")
plt.legend()
plt.grid(True)
plt.savefig("records/cpu.png")
