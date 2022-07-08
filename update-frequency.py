#!/usr/bin/env python3

import collections
import datetime
import json
import shutil
import statistics

with open("info.json") as f:
    info = json.load(f)

dates = [i["date"] for i in info.values()]
dates = [datetime.datetime.strptime(i, "%Y-%m-%d") for i in dates]
dates = set(dates)
dates = sorted(dates)

dt = max(dates) - min(dates)
print("Mean overall interval:", dt / len(dates))

intervals = zip(dates, dates[1:])
intervals = [(j - i).days for (i,j) in intervals]
intervals = sorted(intervals)

print("Media interval:", statistics.median(intervals))

interval_frequencies = collections.Counter(intervals)
max_interval = max(interval_frequencies.values())
term_width = shutil.get_terminal_size().columns - 3

print("Interval distribution")
for interval in range(max(interval_frequencies.keys()) + 1):
    count = interval_frequencies.get(interval, 0)
    width = int(round(term_width * (count / max_interval), 0))
    print(f"{interval:02d}", "*" * width)
