#!/usr/bin/env python3

import collections
import datetime
import fnmatch
import itertools
import json
import pathlib
import random
import string
import subprocess
import sys
import urllib.parse

import bs4
import click
import flask

from human_sort import human_sort

import load_info
from gen_base import order as SITE_ORDER

root = pathlib.Path("/Users/benzlock/Desktop/mhg1o/canon")
with (root/"site-info.json").open() as file:
    site_info = json.load(file)

app = flask.Flask("MH's index", template_folder=root/"templates")
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True
app.config["SERVER_NAME"] = "mhg1o.tk/canon"

IMAGE_EXTENSIONS = {".gif", ".jpg", ".jpeg", ".JPG"}

PRIVATE_SITES = {"www.facebook.com", "facebook.com", "www.vk.com", "vk.com"}

def grouper(iterable, n, fillvalue=None):
    "Collect data into non-overlapping fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

def get_model_images(model_id):
    images = []

    if (root/"static"/"model-images"/(model_id+".jpg")).exists():
        images += ["../../static/model-images/" + model_id + ".jpg"]
    else:
        images += ["../../static/default-model-img.jpg"]

    if (root/"static"/"alt-model-images"/(model_id+".jpg")).exists():
        images += ["../../static/alt-model-images/" + model_id + ".jpg"]
    else:
        images += ["../../static/default-model-img.jpg"]

    return images

@app.route("/sites/<family>/<site>")
def preview(family, site):
    location = root/"data"/family/site
    info = load_info.load_info(location)
    items = info.items()

    site_internal_id = f"{family}/{site}"

    def get_item_name(family, site, item_id):
        site_name = site_info[f"{family}/{site}"]["name"]
        return site_name + " " + item_id

    if site_internal_id in site_info:
        site_name = site_info[site_internal_id]["name"]
    else:
        print(site_internal_id, "is not yet registered in site-info.json")
        name = site

    if (location/"notes.json").exists():
        with (location/"notes.json").open() as file:
            notes = json.load(file)
    else:
        notes = []

    def is_image(url):
        url = urllib.parse.urlparse(url)
        return any(url.path.endswith(ext) for ext in IMAGE_EXTENSIONS)

    return flask.render_template(
            "site.html",
            name=site_name,
            generated=datetime.datetime.now(),
            notes=notes,
            items=items,
            is_image=is_image,
            get_item_name=get_item_name
            )

@app.route("/models")
def models_page(private_models):
    with (root/"model-info.json").open() as file:
        model_info = json.load(file)

    Model = collections.namedtuple("Model", ("model_id", "name", "image", "alt_image", "is_private"))
    models = {}
    for model_id in model_info:
        models[model_id] = Model(
                model_id,
                model_info[model_id].get("name", model_id),
                *get_model_images(model_id),
                model_id in private_models
                )

    families = {family: set() for family in SITE_ORDER}
    families["Other"] = set(models.values())
    for site_internal_id in site_info:
        site_models_file = root/"data"/site_internal_id/"models.json"
        if not site_models_file.exists():
            continue
        with site_models_file.open() as file:
            site_models = json.load(file)
        for model_id in site_models:
            model = models[model_id]
            families[site_info[site_internal_id]["family"]].add(model)
            families["Other"].discard(model)

    for family, models in families.items():
        models = sorted(models)
        models = grouper(models, 4, None)
        families[family] = models

    return flask.render_template(
            "models.html",
            families=families
            )

@app.route("/models/<model_id>.html")
def model_page(model_id, private=False):
    with (root/"model-info.json").open() as file:
        info = json.load(file)

    model_info = info[model_id]

    if not private:
        public_links = []

        def contains_private_link(s):
            soup = bs4.BeautifulSoup(s, "html.parser")
            for a in soup.find_all("a"):
                if a.get("href"):
                    url = urllib.parse.urlparse(a.get("href"))
                    if url.netloc in PRIVATE_SITES:
                        return True
            return False

        for l in model_info["links"]:
            if not contains_private_link(l):
                public_links += [l]
        model_info["links"] = public_links
        model_info["biography"] = ""

    appearances = collections.defaultdict(list)
    site_names = {}

    Item = collections.namedtuple("Item", ("family", "site", "item_id", "name"))

    for site_internal_id in site_info:
        site_models_file = root/"data"/site_internal_id/"models.json"
        if not site_models_file.exists():
            continue
        with site_models_file.open() as file:
            site_models = json.load(file)
        if model_id not in site_models:
            continue

        this_site_info = load_info.load_info(root/"data"/site_internal_id)
        family, site = site_internal_id.split("/")

        site_appearances = []
        for item_id_glob in site_models[model_id]:
            matches = fnmatch.filter(this_site_info.keys(), item_id_glob)
            if not matches:
                print("glob", item_id_glob, "matched no items")
            matches = [Item(family, site, i, this_site_info[i].get("name", None)) for i in matches]
            site_appearances += matches

        site_names[site_internal_id] = site_info[site_internal_id]["name"]
        site_appearances = sorted(site_appearances, key=lambda i: human_sort(this_site_info[i.item_id].get("sort_key", i.item_id)))
        appearances[site_internal_id] = site_appearances

    return flask.render_template(
            "model.html",
            **model_info,
            model_id=model_id,
            appearances=appearances,
            site_names=site_names,
            image=get_model_images(model_id)[0],
            private=private
            )

if __name__ == "__main__":
    @click.group()
    def cli():
        pass

    @cli.command()
    @click.argument("models", nargs=-1)
    @click.option("--private", is_flag=True)
    def models(models, private):
        if not models:
            with (root/"model-info.json").open() as file:
                model_info = json.load(file)
            models = sorted(model_info.keys())

        private_models_file = root/".private-models"
        private_models = set(private_models_file.read_text().splitlines())
        for model_id in models:
            if private:
                private_models.add(model_id)
            else:
                private_models.discard(model_id)
        private_models_file.write_text("\n".join(private_models))

        with app.app_context():
            (root/"html"/"models"/"index.html").write_text(models_page(private_models))

        for model_id in models:
            if private:
                print(f"\033[31m{model_id}\033[m")
            else:
                print(model_id)
            with app.app_context():
                page = model_page(model_id, private)
            (root/"html"/"models"/(model_id + ".html")).write_text(page)

    @cli.command()
    @click.argument("model_ids", nargs=-1)
    def model(model_ids):
        if not model_ids:
            with (root/"model-info.json").open() as file:
                model_ids = json.load(file).keys()

        for model_id in model_ids:
            print(model_id)
            file = root/"html"/"models"/(model_id+".html")

            with app.app_context():
                file.write_text(model_page(model_id))

    @cli.command()
    @click.argument("family", required=True)
    @click.argument("site", required=True)
    @click.argument("item_id", required=True)
    @click.argument("model_name", required=True)
    def set_model(family, site, item_id, model_name):
        item_ids = item_id.split(",")
        models_file = root/"data"/family/site/"models.json"

        with models_file.open() as file:
            site_models = json.load(file)

        with (root/"model-info.json").open() as file:
            model_info = json.load(file)

        info = load_info.load_info(root/"data"/family/site)
        for item_id in item_ids:
            if item_id not in info:
                print(item_id, "not found")

        model_names = collections.defaultdict(set)
        for model_id in model_info:
            name = model_info[model_id]["name"]
            model_names[name].add(model_id)

        if len(model_names[model_name]) > 1:
            print(model_name, "is a duplicate name:", model_names[model_name])
            return

        if model_name in model_names:
            model_id = model_name
        if model_names[model_name]:
            model_id = tuple(model_names[model_name])[0]
        else:
            print("no model found with name", model_name)
            return

        for item_id in item_ids:
            if model_id in site_models:
                if item_id in site_models[model_id]:
                    print("Item", item_id, "already registered for model", model_name)
                else:
                    print(model_id, "added to", item_id)
                    site_models[model_id] += [item_id]
            else:
                print(model_id, "added to", item_id)
                site_models[model_id] = [item_id]

        with models_file.open("w") as file:
            json.dump(site_models, file, indent=4)

    @cli.command()
    @click.argument("name", required=False, nargs=1)
    def new_model(name=None):
        id_chars = string.ascii_letters + string.digits
        model_id = random.sample(id_chars, 8)
        model_id = "".join(model_id)

        if name is None:
            name = "#" + model_id

        info_file = root/"model-info.json"
        with info_file.open() as file:
            model_info = json.load(file)

        model_info[model_id] = {
                "name": name,
                "biography": "<h2>Biography</h2>",
                "links": [],
                }

        with info_file.open("w") as file:
            json.dump(model_info, file, indent=4, sort_keys=True, ensure_ascii=False)

        print("added model", model_id)

    @cli.command()
    @click.argument("locations", nargs=-1)
    def site_preview(locations):
        locations = locations or ["."]
        for location in locations:
            location = pathlib.Path(location).absolute()
            family, site = location.parts[-2:]

            with app.app_context():
                site_preview = preview(family, site)

            dest = root/"html"/"sites"/family/site/"index.html"

            if not dest.parent.exists():
                dest.parent.mkdir(parents=True)
            dest.write_text(site_preview)

            subprocess.run("pbcopy", input=bytes(dest.as_uri(), "utf-8"))

    cli()
