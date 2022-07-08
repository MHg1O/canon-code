#!/usr/bin/env python3

import json
import sys

for file in sys.argv[1:]:
    with open(file) as f:
        info = json.load(f)

        for v in info.values():
            if "url" in v:
                print(v["url"])
