import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

conn = sqlite3.connect("steam.db")
df = pd.read_sql_query("SELECT * FROM player_counts_local", conn)
print(df.shape)
print(df.head())

not_zeros = df[df["player_count"] != 0]
print(not_zeros.shape)

df["local_time"] = pd.to_datetime(df["local_time"])
df["hour"] = df["local_time"].dt.hour
naraka_not_zeros = df[(df["game_name"] == "NARAKA: BLADEPOINT") & (df["player_count"] != 0)]
hourly = naraka_not_zeros.groupby("hour")["player_count"].agg(["mean", "count"]).round()
average_players_thousands = hourly["mean"]/1000
print(hourly)

colors = ["#ef86e4" if c < 3 else "#2a78d6" for c in hourly["count"]]

fig, ax = plt.subplots(figsize=(10,5))           
ax.bar(hourly.index, average_players_thousands, color=colors)   
ax.legend(handles=[
    Patch(color="#2a78d6", label="3+ samples"),
    Patch(color="#ef86e4", label="Fewer than 3 samples (less reliable)"),
])
ax.set_xticks(range(24))           
ax.set_title("NARAKA: BLADEPOINT · average online players by hour")
ax.set_xlabel("hour(UTC+8)")
ax.set_ylabel("Average players (thousands)")
fig.savefig("charts/naraka_hourly.png", dpi=150)           
