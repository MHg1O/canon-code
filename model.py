#!/usr/bin/env python3

import collections
import fnmatch
import itertools
import json
import math
import pathlib

from levenshtein import levenshtein

def preprocess_pattern(pat):
    out = [""]

    options = []
    processing_option = False

    for c in pat:
        if c == "}":
            processing_option = False
            out = [i + j for i, j in itertools.product(out, options)]
        elif c == "{":
            processing_option = True
            options = [""]
        elif processing_option and c == ",":
            options += [""]
        elif processing_option and c != ",":
            options[-1] += c
        else:
            out = [s + c for s in out]

    return out

def pattern_match(name, pat):
    patterns = preprocess_pattern(pat)
    return any(fnmatch.fnmatch(name, p) for p in patterns)

def pattern_filter(names, pat):
    return filter(lambda name: pattern_match(pat, name), names)

def min_substring_distance(a, b, ignore_case=True):
    if len(a) == len(b):
        sml = a
        lng = b
    else:
        sml = min(a, b, key=len)
        lng = max(a, b, key=len)

    if ignore_case:
        sml = sml.lower()
        lng = lng.lower()

    d = levenshtein(sml, lng[:len(sml)])

    for i in range(len(lng) - len(sml)):
        d = min(d, levenshtein(sml, lng[i:i+len(sml)]))
    return d

class ModelInfo(collections.UserDict):

    def __init__(self, info_file):
        self.info_file = info_file
        with open(info_file) as file:
            info = json.load(file)

        self.data = {}

        for model_id, model_data in info.items():

            self.data[model_id] = Model(model_id, model_data)

    def extensive_name_search(self, query):
        best_results = collections.defaultdict(lambda: math.inf)

        for model in self.values():
            if "alt_spelling" in model:
                d = min_substring_distance(model["alt_spelling"], query)
                best_results[model.model_id] = min(d, best_results[model.model_id])

            if "display_name" in model:
                d = min_substring_distance(model["display_name"], query)
                best_results[model.model_id] = min(d, best_results[model.model_id])

            if "aliases" in model:
                for alias in model["aliases"]:
                    d = min_substring_distance(alias, query)
                    best_results[model.model_id] = min(d, best_results[model.model_id])

            if not model["name"].startswith("$"):
                d = min_substring_distance(model["name"], query)
                best_results[model.model_id] = min(d, best_results[model.model_id])

        results = [(self.data[model_id], score) for (model_id, score) in best_results.items()]
        results = sorted(results, key=lambda r: r[1])
        return results[:5]

    def find_by_name(self, name):
        matches = set()

        for model in self.data.values():
            if model["name"] == name:
                matches.add(model)

        return matches

    def fuzzy_find_by_name(self, name):
        names = [m["name"] for m in self.data.values()]
        names = sorted(names, key=lambda x: levenshtein(name, x))
        return names

    def fuzzy_get_model_id(self, query):
        if query in self.data:
            return query
        else:
            matches = self.find_by_name(query)
            if len(matches) == 0:
                closest = self.fuzzy_find_by_name(query)[0]
                raise Exception(f"No matches for {repr(query)}. Did you mean {repr(closest)}?")
            elif len(matches) == 1:
                return tuple(matches)[0].model_id
            else:
                raise Exception(f"Too many matches for {repr(query)}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            js = json.dumps(self.data, cls=UserDictJSONEncoder, ensure_ascii=False, indent=4, sort_keys=True)
            with open(self.info_file, "w") as file:
                file.write(js)
        else:
            print(f"ModelInfo encountered an exception and has exited without writing to the info file ({self.info_file})")

class Model(collections.UserDict):
    mandatory_keys = ("name", "biography", "links")
    optional_keys = ("alt_spelling", "display_name", "aliases")
    all_keys = set(mandatory_keys + optional_keys)

    def __init__(self, model_id, data):
        if not set(data.keys()).issubset(self.all_keys):
            raise Exception(f"{self.__class__.__name__} initialised with unknown keys {all_keys - set(data.keys())}")

        self.model_id = model_id
        self.data = data

    def __hash__(self):
        return int.from_bytes(bytes(self.model_id, "utf-8"), "big")

    @property
    def links_block(self):
        return "\n".join(" * " + L for L in self.data["links"])

    @property
    def display_name(self):
        if "display_name" in self.data:
            return self.data["display_name"]
        else:
            return self.data["name"]

class SiteModelInfo:

    class ModelsToItems:

        def __init__(self, site_models, item_ids):
            self.site_models = site_models
            self.item_ids = item_ids

            self.models_to_items = {}

        def __getitem__(self, model_id):
            if model_id not in self.models_to_items:
                self.models_to_items[model_id] = []

                patterns = []
                for p in self.site_models[model_id]:
                    if isinstance(p, str):
                        patterns += [p]
                    elif isinstance(p, dict):
                        patterns += p["items"]
                    else:
                        raise Exception()

                for pattern in patterns:
                    if pattern in self.item_ids:
                        self.models_to_items[model_id] += [pattern]
                    elif (matches := pattern_filter(self.item_ids, pattern)):
                        self.models_to_items[model_id] += matches
                    else:
                        raise Exception(f"{pattern} matched no items")

            self.models_to_items[model_id] = self.models_to_items[model_id]
            return self.models_to_items[model_id]

        def __contains__(self, model_id):
            return self.site_models.__contains__(model_id)

        def __iter__(self):
            return self.site_models.__iter__()

    class ItemsToModels:

        Credit = collections.namedtuple("Credit", ("model_name", "model_id"))

        def __init__(self, site_models, item_ids, model_info):
            self.site_models = site_models
            self.item_ids = item_ids
            self.model_info = model_info

            self.items_to_models = {}

        def __getitem__(self, item_id):
            if item_id not in self.items_to_models:
                self.items_to_models[item_id] = []
                for model_id in self.site_models:

                    for p in self.site_models[model_id]:
                        model_name = self.model_info[model_id].display_name
                        if isinstance(p, str):
                            patterns = [p]
                            credit = self.Credit(model_name, model_id)
                        elif isinstance(p, dict):
                            patterns = p["items"]

                            if "credited_as" in p:
                                model_name += f" (as {p['credited_as']})"
                            if "display_name" in p:
                                raise Exception()
                            credit = self.Credit(model_name, model_id)
                        else:
                            raise Exception()

                        for pattern in patterns:
                            if pattern_match(item_id, pattern):
                                self.items_to_models[item_id] += [credit]
                                break

            self.items_to_models[item_id] = sorted(self.items_to_models[item_id])
            return self.items_to_models[item_id]

    def __init__(self, models_file, model_info, item_ids):

        if models_file is None:
            site_models = {}
        else:
            if isinstance(models_file, str):
                models_file = pathlib.Path(models_file)

            with models_file.open() as file:
                site_models = json.load(file)

        self.models = self.ModelsToItems(site_models, item_ids)
        self.items = self.ItemsToModels(site_models, item_ids, model_info)

class UserDictJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, collections.UserDict):
            return o.data
        else:
            return super().default(self, o)

if __name__ == "__main__":
    with ModelInfo("/Users/benzlock/Desktop/mhg1o/canon/model-info.json") as mi:
        mi["065omr9X"]["name"] = "Iryna Vaschenko"
