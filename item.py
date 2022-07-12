#!/usr/bin/env python3

import collections
import functools
import json
import pathlib

from model import SiteModelInfo
from human_sort import human_sort

class SiteInfo(collections.UserDict):

    def __init__(self, site_id, config, root):

        self.site_id = site_id
        self.config = config
        self.root = root

        self.site_name = self.config["name"]
        if "show_dates" in self.config.get("tags", []):
            self.site_name += f" ({self.config['dates'][0] or ''}–{self.config['dates'][1] or ''})"

        self.data = {}

        primary_info_file = self.root/self.config["primary_info_file"]
        with primary_info_file.open() as file:
            info = json.load(file)

        for item_id, item_data in info.items():

            if "item_id" in item_data:
                item_id = item_data["item_id"]
                item_data.pop("item_id")

            if item_id in self.data:
                raise Exception(f"Multiple values for item id {item_id}")

            self.data[item_id] = Item(item_id, item_data)

        for extra_info_file in self.config.get("extra_info_files", []):
            extra_info_file = self.root/extra_info_file

            with extra_info_file.open() as file:
                info = json.load(file)

                for item_id, item_data in info.items():

                    if "item_id" in item_data:
                        new_item_id = item_data["item_id"]
                        self.data[new_item_id] = self.data.pop(item_id)
                        self.data[new_item_id].item_id = new_item_id
                        item_data.pop("item_id")
                        item_id = new_item_id

                    if item_id in self.data:
                        self.data[item_id].update(Item(item_id, item_data))
                    else:
                        self.data[item_id] = Item(item_id, item_data)

        for item_id, item in self.data.items():
            item["internal_url"] = site_id + "/index.html" + "#" + item_id
            item["site_id"] = site_id
            item["site_name"] = self.site_name

    def __iter__(self):
        for item_id, _ in sorted(self.data.items(), key=lambda i: human_sort(i[1].get("sort_as", i[0]))):
            yield item_id

    def sort_item_ids(self, item_ids):
        return sorted(item_ids, key=lambda item_id: self.data[item_id].get("sort_as", item_id))

    def latest_video(self):
        videos = [k for k, v in self.data.items() if "duration" in v["size"]]
        videos = [k for k in videos if "date" in self.data[k]]
        return max(videos, key=lambda k: self.data[k]["date"])

    def latest_photo(self):
        photos = [k for k, v in self.data.items() if "images" in v["size"]]
        photos = [k for k in photos if "date" in self.data[k]]
        return max(photos, key=lambda k: self.data[k]["date"])

class Item(collections.UserDict):
    mandatory_keys = tuple()
    optional_keys = {
            "description": "",
            "name": "",
            "previews": [],
            "date": "",
            "url": "",
            "archive_url": "",
            "size": {},
            "sort_as": "",
            "price": None
            }
    all_keys = set(mandatory_keys + tuple(optional_keys.keys()))


    def __init__(self, item_id, data):
        if not set(data.keys()).issubset(self.all_keys):
            raise Exception(f"{self.__class__.__name__} initialised with unknown keys {set(data.keys()) - self.all_keys}")

        self.item_id = item_id
        self.data = data

        if "size" in self.data:
            size = self.data.pop("size")
            self.data["size"] = {}

            for key, value in size.items():
                self.data["size"][key] = Size(value)

    @property
    def sort_key(self):
        return self.data.get("sort_as", self.item_id)

class Size:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        if isinstance(self.data, dict):
            if "units" in self.data:
                return str(self.data["size"]) + " " + self.data["units"]
            else:
                return str(self.data["size"])
        else:
            return str(self.data)

if __name__ == "__main__":
    site = SiteInfo("/Users/benzlock/Desktop/mhg1o/canon/data/zlata.de/iamflexigirl.com/config.json")
    print(tuple(iter(site)))
