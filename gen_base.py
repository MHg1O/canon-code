#!/usr/bin/env python3

import json
import flask
import pathlib
import itertools
import operator

app = flask.Flask("canon")
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

root = pathlib.Path("/Users/benzlock/Desktop/mhg1o/canon")

order = [
    "Flex-Mania",
    "Satyridae",
    "Zlata.de",
    "Topflexmodels",
    "Flexshow",
    "Crystal Lizard",
    "FlexFlicks",
    "Watch4Fetish",
    "CrazyFetishPass",
    "TotalToning",
    "Other"
    ]

if __name__ == "__main__":
    with (root/"site-info.json").open() as file:
        site_info = json.load(file)

    for k, v in site_info.items():
        if "wip" in v.get("tags", []):
            continue
        index = root/"html"/"sites"/k/"index.html"
        if not index.exists():
            print(f"warning: index for {k} seems to have moved ({index} does not exist)")

    site_info = sorted(site_info.items(), key=lambda s: order.index(s[1]["family"]))
    site_info = itertools.groupby(site_info, lambda s: s[1]["family"])

    with app.app_context():
        with open(root/"html"/"index.html", "w") as file:
            file.write(flask.render_template("index.html", site_info=site_info))
