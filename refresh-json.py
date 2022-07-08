#!/usr/bin/env python3

import json
import glob

for file in glob.glob("*.json"):
    j = open(file)
    j = json.load(j)

    with open(file, "w") as  f:
        json.dump(j, f, indent=4, sort_keys=True, ensure_ascii=False)
