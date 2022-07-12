#!/usr/bin/env python3

import collections
import json
import pathlib

import item

from human_sort import human_sort
from get_files import get_file_list

class RelationInfo(collections.UserDict):

    def __init__(self, root, sites):
        if isinstance(root, str):
            root = pathlib.Path(root)

        self.data = {}

        self.sites = sites
        self.root = root

        for relation_file in get_file_list(root):
            if relation_file.suffix != ".json":
                continue
            with relation_file.open() as file:
                relations = json.load(file)

            for prefix, relations_list in relations.items():
                prefix = prefix.split("/")

                for items in relations_list:
                    items = [(*prefix, *item.split("/")) for item in items]
                    items = [("/".join(i[:2]), "/".join(i[2:])) for i in items]
                    items = set(items)

                    for item_id in items:
                        (r := items.copy()).remove(item_id)

                        self.data[item_id] = sorted(list(r), key=human_sort)

    def __getitem__(self, key):

        for site_id, item_id in self.data[key]:

            yield self.sites[site_id][item_id]

    def __contains__(self, key):
        return key in self.data

if __name__ == "__main__":
    ri = RelationInfo("/Users/benzlock/Desktop/mhg1o/canon/relations")
