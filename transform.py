#!/usr/bin/env python3

import json
import os
import sys

files = sys.argv[1:]

if not files:
    print("argument pls")

for file in files:
    j = open(file)
    j = json.load(j)

    backup_name = "backup-" + file
    if not os.path.isfile(backup_name):
        with open(backup_name, "w") as f:
            json.dump(j, f)

    for item_id in j:
        if "size" in j[item_id]:
            new_size = {}

            for s in j[item_id]["size"]:
                new_size[s["type"]] = {"size": s["size"]}

                if "units" in s:
                    new_size[s["type"]]["units"] = s["units"]

            j[item_id]["size"] = new_size

    with open(file, "w") as f:
        json.dump(j, f, indent=4, ensure_ascii=False, sort_keys=True)
