#!/usr/bin/env python3

import collections
import fnmatch
import functools
import json
import os
import pathlib

from dict_merge import dict_merge
from human_sort import human_sort
from get_files import get_file_list

Model = collections.namedtuple("Model", ("model_id", "name"))

root = pathlib.Path("/Users/benzlock/Desktop/mhg1o/canon")

def get_sort_key(item_id, item):
    if "sort_as" in item:
        return item["sort_as"].lower()
    else:
        return item.get("item_id", item_id).lower()

def object_pairs_hook(ordered_pairs):
    """Reject duplicate keys."""
    d = {}
    for k, v in ordered_pairs:
        if k in d:
           raise ValueError("duplicate key: %r" % (k,))
        else:
           d[k] = v
    return d

def get_related():
    relations = {}
    for relation_file in get_file_list(pathlib.Path(root/"relations")):
        if relation_file.suffix != ".json":
            continue
        with relation_file.open() as file:
            relations_raw = json.load(file)

            for prefix, relations_list in relations_raw.items():
                prefix = prefix.split("/")
                for relation in relations_list:
                    relation = [(*prefix, *item.split("/")) for item in relation]
                    relation = set(relation)

                    for item_id in relation:
                        (r := relation.copy()).remove(item_id)
                        relations["/".join(item_id)] = sorted(list(r), key=human_sort)
    return relations

def load_info(location: pathlib.Path):

    info = {}
    for info_file in location.glob("info*.json"):
        with info_file.open() as file:
            this_file_info = json.load(file, object_pairs_hook=object_pairs_hook)
            dict_merge(info, this_file_info)

    model_info_file = root/"model-info.json"
    with model_info_file.open() as file:
        model_info = json.load(file)

    models_file = location/"models.json"
    if models_file.exists():
        with models_file.open() as file:
            site_models = json.load(file)
    else:
        site_models = {}

    relations = get_related()

    for item_id, data in tuple(info.items()):
        if "item_id" in data:
            info.pop(item_id)
            info[data["item_id"]] = data

    for item_id, data in info.items():
        if "size" in data:
            new_size = {}
            for size_key, size_value in data["size"].items():
                if isinstance(size_value, dict):
                    new_size[size_key] = size_value["size"]
                    if "units" in size_value:
                        new_size[size_key] += " " + size_value["units"]
                else:
                    new_size[size_key] = size_value
            data["size"] = new_size

        for model_id, model_item_ids in site_models.items():
            for item_id_pattern in model_item_ids:
                if fnmatch.fnmatch(item_id, item_id_pattern):
                    data["model"] = data.get("model", []) + [Model(model_id, model_info[model_id]["name"])]

        full_item_id = os.path.join(location.parent.name, location.name, item_id)
        data["related"] = relations.get(full_item_id, [])


    info = dict(sorted(info.items(), key=human_sort))
    return info

