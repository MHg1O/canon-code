#!/usr/bin/env python3

import json
import sys
import pathlib
import collections

models_file = pathlib.Path("./models.json")

for file in sys.argv[1:]:
    with open(file) as file:
        info = json.load(file)

    models = collections.defaultdict(lambda: list())
    model_ids = {}
    for item_id, v in info.items():
        if "model" in v:

            for model in v["model"]:
                if model in model_ids:
                    models[model_ids[model]] += [item_id]
                else:
                    model_id = input(model + " ")
                    model_ids[model] = model_id
                    models[model_id] += [item_id]

    with models_file.open("w") as models_file:
        json.dump(models, models_file, indent=4)
