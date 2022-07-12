#!/usr/bin/env python3

import collections
import datetime
import itertools
import json
import pathlib
import random
import string
import subprocess
import urllib

import click
import flask
import markdown

from model import ModelInfo, SiteModelInfo, UserDictJSONEncoder, pattern_filter
from item import SiteInfo
from relation import RelationInfo

from human_sort import human_sort

global_config = pathlib.Path("/Users/benzlock/Desktop/mhg1o/canon/config.json")
root = global_config.parent
global_config = json.loads(global_config.read_text())

app = flask.Flask("MH's index", template_folder=root/"templates")
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

@app.template_filter("markdown")
def markdown_filter(md):
    return markdown.markdown(md, extensions=["footnotes"])

PRIVATE_WEBSITES = {"vk.com", "facebook.com"}

def load_site_config(config_location):
    if str(config_location).startswith("$extra_configs/"):
        return global_config["extra_configs"][config_location.removeprefix("$extra_configs/")]
    else:
        with (root/config_location).open() as file:
            return json.load(file)

def load_site(config_location):
    with config_location.open() as file:
        config = json.load(file)
        site_root = config_location.parent

    for _, site_configs in global_config["families"].items():
        for site_id, _config_location in site_configs.items():
            if config_location.resolve() == (root/_config_location).resolve():
                return SiteInfo(site_id, config, site_root)

def model_image_func(depth):
    def model_image(model_id):
        if (root/global_config["static_files"]/"model-images"/f"{model_id}.jpg").exists():
            return (depth * "../") + f"static/model-images/{model_id}.jpg"
        else:
            return (depth * "../") + f"static/default-model-img.jpg"

    return model_image

def load_site_configs():
    "returns a mapping of site family names to lists of site configs"
    families = collections.defaultdict(dict)

    for family, site_configs in global_config["families"].items():
        for site_id, site_config in site_configs.items():
            families[family][site_id] = load_site_config(site_config)

    return families

def load_all_sites():
    "returns a mapping of site IDs to Site objects"
    sites = {}

    for family, site_configs in global_config["families"].items():
        for site_id, site_config_file in site_configs.items():
            site_config = load_site_config(site_config_file)

            if "wip" in site_config.get("tags", []):
                continue
            else:
                site = load_site(root/site_config_file)

            sites[site_id] = site
    return sites

def model_page(model, appearances, private):
    return flask.render_template(
            "model.html",
            model=model,
            appearances=appearances,
            get_model_image=model_image_func(depth=2),
            private=private
            )

def models_page(family_models, all_models, private_models):

    def grouper(iterable, n, fillvalue=None):
        "Collect data into non-overlapping fixed-length chunks or blocks"
        # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
        args = [iter(iterable)] * n
        return itertools.zip_longest(*args, fillvalue=fillvalue)

    model_image = model_image_func(2)

    for k, v in family_models.items():
        family_models[k] = grouper(sorted(v, key=lambda m: m.model_id), 4)

    return flask.render_template(
            "models.html",
            family_models=family_models,
            all_models=all_models,
            model_image=model_image,
            private_models=private_models
            )

def site_page(site, notes):

    IMAGE_EXTENSIONS = {".gif", ".jpg", ".jpeg", ".JPG", ".png"}

    ri = RelationInfo(root/global_config["relations_dir"], load_all_sites())

    mi = ModelInfo(root/global_config["models_file"])

    if "models_file" in site.config:
        models_file = site.root/site.config["models_file"]
    else:
        models_file = None
    models = SiteModelInfo(models_file, mi, tuple(site.keys()))

    def is_image(url):
        url = urllib.parse.urlparse(url)
        return any(url.path.endswith(ext) for ext in IMAGE_EXTENSIONS)

    return flask.render_template(
            "site.html",
            site=site,
            notes=notes,
            is_image=is_image,
            generated=datetime.datetime.now(),
            data_updated=site.config.get("data_updated", None),
            shortcuts=site.config.get("shortcuts", []),
            relations=ri,
            models=models
            )

def base_page(families):
    return flask.render_template("index.html", families=families)

if __name__ == "__main__":

    @click.group()
    def cli():
        pass

    @cli.command()
    @click.argument("models", nargs=-1)
    @click.option("--private", is_flag=True)
    def model(models, private):
        mi = ModelInfo(root/global_config["models_file"])
        sites = load_all_sites()

        site_model_infos = {}
        for site_id in sites:
            if site_id not in site_model_infos:
                if "models_file" in sites[site_id].config:
                    models_file = sites[site_id].root/sites[site_id].config["models_file"]
                else:
                    models_file = None

                site_model_infos[site_id] = SiteModelInfo(models_file, mi, tuple(sites[site_id].keys()))

        site_ids = [list(sites.keys()) for _, sites in global_config["families"].items()]
        site_ids = sum(site_ids, start=[])

        if models:
            model_ids =  [mi.fuzzy_get_model_id(query) for query in models]
            model_list = [mi[model_id] for model_id in model_ids]
        else:
            model_list = list(mi.values())

        with (root/global_config["private_models_file"]).open() as file:
            private_models = set(json.load(file))
        if private:
            private_models = private_models | set(m.model_id for m in model_list)
        else:
            private_models = private_models - set(m.model_id for m in model_list)
        with (root/global_config["private_models_file"]).open("w") as file:
            json.dump(sorted(private_models), file, indent=4)

        ItemLink = collections.namedtuple("ItemLink", ("item_id", "sort_key", "internal_url", "name"))
        for model in model_list:
            appearances = {}

            for site_id, site in sites.items():
                if model.model_id in site_model_infos[site_id].models:
                    items = []
                    for item_id in site_model_infos[site_id].models[model.model_id]:
                        url = "../sites/" + site[item_id]["internal_url"]
                        item_link = ItemLink(item_id, site[item_id].sort_key, url, site[item_id].get("name", None))
                        items += [item_link]
                    appearances[site.site_name] = sorted(items, key=lambda i: human_sort(i.sort_key))

            links = []
            for link in model["links"]:
                if not any(p in link for p in PRIVATE_WEBSITES):
                    links += [link]
            model["links"] = links

            with app.app_context():
                page = model_page(model, appearances, private)
            dest = (root/global_config["index_root"]/"models"/(model.model_id + ".html"))
            dest.write_text(page)
            subprocess.run("pbcopy", input=bytes(dest.as_uri(), "utf-8"))
            print(model.model_id)

    @cli.command()
    @click.argument("model_name")
    def edit_model(model_name):
        with ModelInfo(root/global_config["models_file"]) as mi:
            model_id = mi.fuzzy_get_model_id(model_name)

            data = json.dumps(mi[model_id], cls=UserDictJSONEncoder, ensure_ascii=False, indent=4)

            new_data = click.edit(data, require_save=False, extension=".json")

            new_data = json.loads(new_data)
            mi[model_id] = new_data

    @cli.command()
    @click.argument("model_name")
    def edit_model_bio(model_name):
        with ModelInfo(root/global_config["models_file"]) as mi:
            model_id = mi.fuzzy_get_model_id(model_name)
            biography = mi[model_id]["biography"]

            new_biography = click.edit(biography, require_save=False, extension=".md")
            mi[model_id]["biography"] = new_biography

    @cli.command()
    def models_base():
        mi = ModelInfo(root/global_config["models_file"])

        sites = load_all_sites()
        family_models = collections.defaultdict(set)
        with (root/global_config["private_models_file"]).open() as file:
            private_models = set(json.load(file))

        for family, site_ids in global_config["families"].items():
            for site_id in site_ids:

                if site_id not in sites:
                    continue

                if "models_file" in sites[site_id].config:
                    models_file = sites[site_id].root/sites[site_id].config["models_file"]
                else:
                    models_file = None

                site_model_info = SiteModelInfo(models_file, mi, tuple(sites[site_id].keys()))

                for model_id in site_model_info.models:
                    family_models[family].add(mi[model_id])

        present = set.union(*family_models.values())
        for model in mi.values():
            if model not in present:
                family_models[None].add(model)

        with app.app_context():
            page = models_page(family_models, tuple(mi.values()), private_models)

        (root/global_config["index_root"]/"models"/"index.html").write_text(page)

    @cli.command()
    @click.argument("configs", nargs=-1, type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path))
    def site(configs):

        for config in configs:
            site = load_site(config)

            with app.app_context():
                page = site_page(site, [])

            dest = root/global_config["index_root"]/"sites"/site.site_id/"index.html"

            if not dest.parent.exists():
                dest.parent.mkdir(parents=True)

            dest.write_text(page)
            subprocess.run("pbcopy", input=bytes(dest.as_uri(), "utf-8"))

    @cli.command()
    def base():

        families = load_site_configs()

        for family, site_configs in families.items():
            for site_id, site_config in site_configs.items():
                if "wip" not in site_config.get("tags", []) and not (root/"html"/"sites"/site_id/"index.html").exists():
                    raise Exception(f"index for {site_id} seems to have moved: its index page is not in the expected location")

        with app.app_context():
            page = base_page(families)

        (root/global_config["index_root"]/"index.html").write_text(page)

    @cli.command()
    @click.argument("site_id", required=True)
    @click.argument("patterns", required=True)
    @click.argument("model_query", required=True)
    @click.option("--display-name")
    @click.option("--credited-as")
    def set_model(site_id, patterns, model_query, display_name, credited_as):
        mi = ModelInfo(root/global_config["models_file"])
        model_id = mi.fuzzy_get_model_id(model_query)

        for family, site_configs in global_config["families"].items():
            if site_id in site_configs:
                site = load_site(root/site_configs[site_id])
                break

        if "models_file" not in site.config:
            raise Exception(f"site {site_id} has no model file")
        models_file = site.root/site.config["models_file"]
        with models_file.open() as file:
            info = json.load(file)

        # TODO do not split on commas inside { }
        patterns = patterns.split(",")
        for pattern in patterns:
            if not tuple(pattern_filter(site, pattern)):
                raise Exception(f"{pattern} matches nothing")

            if model_id in info:
                if display_name is None and credited_as is None:
                    if pattern in info[model_id]:
                        raise Exception(f"{pattern} already registered")

                    info[model_id] += [pattern]
                else:
                    for credit in info[model_id]:
                        if isinstance(credit, str):
                            continue

                        if credit.get("display_name", None) == display_name and credit.get("credited_as", None) == credited_as:
                            if pattern in credit["items"]:
                                raise Exception(f"{pattern} already registered")

                            credit["items"] += [pattern]
                            break
                    else:
                        C = {"items": [pattern]}
                        if display_name is not None:
                            C["display_name"] = display_name
                        if credited_as is not None:
                            C["credited_as"] = credited_as

                        info[model_id] += [C]
            elif display_name is None and credited_as is None:
                info[model_id] = [pattern]
            else:
                info[model_id] = {"items": [pattern]}
                if display_name is not None:
                    info[model_id]["display_name"] = display_name
                if credited_as is not None:
                    info[model_id]["credited_as"] = credited_as

        # TODO ensure that the item id actually matches something
        js = json.dumps(info, indent=4, sort_keys=True)

        with models_file.open("w") as file:
            file.write(js)

    @cli.command()
    @click.argument("name", required=False, nargs=1)
    def new_model(name=None):
        id_chars = string.ascii_letters + string.digits
        gen_model_id = lambda: "".join(random.choices(id_chars, k=8))

        with ModelInfo(root/global_config["models_file"]) as mi:
            while (model_id := gen_model_id()) in mi:
                pass

            if name is None:
                name = "$" + model_id

            mi[model_id] = {
                    "name": name,
                    "biography": "## Biography",
                    "links": [],
                    }

        print(f"added model {model_id}")

    @cli.command()
    @click.argument("model_query")
    @click.argument("image", type=click.Path(exists=True, dir_okay=False))
    def prep_model_img(model_query, image):
        mi = ModelInfo(root/global_config["models_file"])
        model_id = mi.fuzzy_get_model_id(model_query)

        r = subprocess.run(
                [
                    "magick", "convert", image,
                    "-resize", "x300",
                    "-gravity", "center",
                    "-background", "white",
                    "-extent", "200x300",
                    "-"
                    ],
                stdout=subprocess.PIPE
                )
        (root/global_config["static_files"]/"model-images"/(model_id+".jpg")).write_bytes(r.stdout)

    cli()

