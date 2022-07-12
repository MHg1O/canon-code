# MH's index

This document describes MHg1O's index system. At a high level, it is a way of representing information about paysites that can be translated into a HTML-based index using a program that comes with the system.

## Conceptual model

This system was designed for modelling contortion paysites, and it is probably easier to understand the design decisions that have been made if you first understand what it is we are trying to represent.
 * The central object that we are concerned with is the "item": this is something like a photoset or a video, or both at the same time. Items have attributes like a name, a description, a date of release, and so on. Each item belongs to exactly one site.
 Items may be related to other items. This usually means that either:
   1. the items are a matching video/photoset pair (e.g. zlata.de z18-05 and 601-74), or
   2. the items are different releases of the same video/photoset (e.g. the version of video 406-02 released on zlata.de on 2013-02-02, and the version released on the zlata.de Clips4Sale page on 2018-11-02)
 * Items are grouped into sites. A site is typically a Web site or a specific page on a site such as Clips4Sale or OnlyFans. Sites come and go, so each site may have a time period associated with it: Zlata.de from 2016 to the present day is considered a different site to Zlata.de from 2010 to 2016.
 * Sites are grouped into families of sites.
 * Parallel to items, sites, and site families, there are models. Each item may be associated with any number of models that the item features.

## Storing information

Information about items, sites, site families, and models is stored in JSON files. The system makes some assumptions about how these files are arranged, which will be stated in the sections below. Everything in the system is organised relative to a directory referred to as the `root`.

### The master config

This is the file that organises sites into families. It should be located at `<root>/config.json`, and has the following keys:
 * `families`: a mapping of human-readable site family names to the corresponding site config files; the addresses of these config files are assumed to be relative to `root`.
 * `extra_configs`: a mapping of site internal IDs to their config data; the structure a site's config data is described below. This doesn't provide any new functionality, but I like to use it to store configs for work-in-progress indices that don't deserve their own file yet.

A master config may look something like this:

```JSON
{
  "families": {
    "Zlata.de": [
      "./data/zlata.de/zlatexa.com/config.json"
    ]
  },
  "extra_configs": {
    "zlata.de/zlata.de-4": {
      "name": "Zlata.de",
      "dates": [2016, null],
      "tags": ["wip", "show_dates"]
    }
  }
}
```

### Site configs

Each site has its own config file. There is some flexibility about where site configs can be stored, but the system was designed with the following structure in mind:

```
root
├── config.json
├── <family-1>
│   ├── <site-1>
│   │   ├── config.json
│   │   └── info.json
│   └── <site-2>
│       ├── config.json
│       └── info.json
├── <family-2>
...
└── html
```

This is important because each site has an internal ID that is used to decide where to place the index that is generated for it. The internal ID of a site is `<second parent of config file>/<first parent of config file>`; for example, the internal ID of the site described by `root/<family-1>/<site-2>/config.json` is `<family-1>/site-2>`. The index for each site is generated at `root/html/sites/<site internal id>.html`.

Each item also has full item ID, which is `<site internal ID>/<item id>`. If `<family-1>/<site-2>` contains an item with ID 100-01, its full item ID would be `<family-1>/<site-2>/100-01`.

A site config file contains some information about a site and specifies where the files with the information about its items are located. Each site config file contains a mapping with the following keys:
 * `name` is the name of the site; this may be different to its URL. The site with URL `flexshow.com` has name `Flexshow`.
 * `url` is the URL of the site on the Web. This URL should be live, so a site like `twist-me.com` which has been offline since 2009 should not have a URL specified.
 * `dates` is a list contains the years between which the site was active. Twist-me, mentioned above, was active between 2006 and 2009, so its dates would be `[2006, 2009]`. We can use null values for open intervals:
   * the current version of zlata.de has dates `[2016, null]`, meaning "2016 until now"
   * the first version of cl-studio.com has dates `[null, 2015]`, meaning "until 2015"
 * `tags` is a list of tags that store information about the site. The following tags are recognised:
   * `show_dates` indicates that when the `name` of a site is displayed, its dates should be displayed as well. This allows us to differentiate between Zlata.de (2010–2016) and Zlata.de (2016–)
   * `wip` indicates that the index for the site is still a work in progress; there will be no link to the site's index on the home page.
   * `ppv` indicates that a site is pay-per-view. This is mostly a cosmetic feature; its only effect is to display the flying money emoji (💸) on the home page next to the site's name
   * `subset` indicates that only a subset of the items on the site are indexed. This is useful for contortion-related items on sites that are not wholly contortion-focused.
* `data_updated` is the datetime when the data for this site was last updated (i.e. the last time when the site was checked for new items). It only really makes sense to use this for sites that are still being updated, otherwise it is useless information. The value of this key is displayed at the top of the site's index page.
* `notes` is a list of notes to be displayed at the top of the site index file
* `shortcuts` is a list of shortcuts that will be added at the top of the site's index page. The following shortcuts are recognised:
  * `latest_video`: the item with the most recent release date whose `size` contains `duration`
  * `latest_photo`: the item with the most recent release date whose `size` contains `images`
 * `primary_info_file` is the address of the "base" site info file, given relative to the parent directory of the site's config file.
 * `extra_info_files` is a list of extra info files. The relationship between the primary info file and extra info files is described below.
 * `models_file` is the file that specifies which models appear in each item.

`name` and `primary_info_file` are required, the rest of the keys are optional.

### Model files

Each site may have a model file that maps model IDs to the list of items that they appear in. More specifically, each key is a model ID, and each value is one of the following:
 * a list of item IDs, or
 * a dictionary containing the following keys:
   * `items`: a list of item IDs
   * `credited_as`: a name that will appear in parentheses after the model's name
   * `display_name`: a name that will appear instead of the model's name

The values in a list of item IDs can use a limited form of shell-style globbing. Specifically:
 * `*` matches zero or more of any character; on its own, this will match any item ID. We can also use it more carefully: `FELICIA v-*` will match `FELICIA v-01`, `FELICIA v-02`, and so on.
 * `?` matches precisely one of any character. The pattern above can be replaced with `FELICIA v-??` to match `FELICIA v-01` but not `FELICIA v-1`.

An example of a model file is given below:

```JSON
{
  "anna-svirina": [...],
  "julia-günthel": {"display_name": "Zlata", "items": [...]},
  "anna-buleeva": {"credited_as": "Kate", "items": [...]}
}
```

On the site index page,
 * Anna Svirina will have her displayed normally,
 * Julia Günthel's name will be displayed as Zlata,
 * Anna Buleeva's name will be displayed as "Anna Buleeva (as Kate)"

Note that a model can have both a `credited_as` and a `display_name`.

### Site info files

These files are probably the most important part of the entire system; they store information about items. Each site info file is a mapping from item IDs to dictionaries that may have the following keys:
 * `name` is the name of the item.
 * `description` is a textual description of the item. This can contain HTML markup, which will be displayed correctly on the site index page.
 * `date` is the date when the item was released.
 * `url` is the item's URL on the Web. This should be used for sites where each item has a dedicated page (e.g. zlata.de), and not sites where multiple items are displayed on the same page (e.g. collection.flex-mania.net).
 * `archive_url` is an analog of `url` for offline sites where the item's page has been archived, such as on the Wayback Machine.
 * `price` is the price of pay-per-view items, in USD.
 * `previews` is a list of preview image or video URLs.
 * `size` is another dictionary containing information about the "size" of the item; each key in the dictionary is a type of size such as "resolution", "duration", "images", etc. The value can be given in two ways:
   * directly, e.g. `{"images": "159"}`
   * with a unit, e.g. `{"duration": {"size": "6", "units": "minutes"}}`. This has almost no practical use—while the site's index page is being generated, the size and the units are concatenated—but it may be useful if the info file is being processed by another program.
 * `item_id` is a new item ID that overwrites the key of this object. References (such as in a model file) to item IDs must be to the "new" item ID, not the overwritten one.

When the information about a site is being loaded by the system, the primary info file is loaded first, with information in secondary files overwriting information in the primary file. This is done on a per-key, basis, not a per-item basis, so if the primary info file contains `{"001": {"date": "2011-04-26", "price": "19.99"}}` and a secondary info file contains `{"001": {"price": "24.99}}`, the final value seen by the program will be equivalent to `{"001": {"date": "2011-04-26", "price": "24.99"}}`. The value of `price` in the secondary info file overwrites the value in the primary info file, but the value of `date` has remained, even though the item in the secondary info file has no such key.

### The model info file

Information about models is all stored in one file, assumed to be at `root/model-info.json`. This is a mapping of model IDs (by default, eight-character-long strings with uppercase letters, lowercase letters, and numbers, but you can use anything) to dictionaries containing information about them. The following keys are supported:
 * `name` is the model's name.
 * `biography` is intended to be a biography, but it can be anything; the content of this field is trusted, so if it contains HTML markup, this will be displayed by your browser.
 * `links` is a list of relevant links; these are also trusted.
 * `alt_spelling` is an alternative (usually Cyrillic) spelling of the model's name.
 * `aliases` is a list of other names that the model has been known by.

```JSON
{
  "0RAGna1P": {
    "name": "Anna Buleeva",
    "aliases": [
      "Maya Petrushina",
      "Kate"
    ],
    "alt_spelling": "Анна Булеева",
    "biography": "<h2>Biography</h2>Anna Buleeva is a Russian freelance contortionist based in New York City.",
    "links": [
      "<a href='https://www.facebook.com/...'>Anna Vladimirovna</a> on Facebook",
      "<a href='https://www.instagram.com/annavladiii/'>@annavladiii</a> on Instagram",

    ]
  }
}
```

`name`, `biography`, and `links` are required, the other keys are optional. When a new model is created by the CLI, these have the following defaults:
 * `name`: `#<model ID>`
 * `biography`: `<h2>Biography</h2>`
 * `links`: an empty list

By default, model pages are generated in "private mode", meaning that the biography is not displayed, and items in `links` are not displayed if they contain links to vk.com and facebook.com.

Each model may also have an image. For a model with ID `<model ID>`, this is located at `root/static/model-images/<model ID>.jpg`. If no such image exists, `root/static/default-model-img.jpg` is used instead.

### Relation files

Any file with a .json extension in `root/relations` and its subdirectories is treated as a relation file; these specify which files are related to one another.

There are typically a large number of relations, and instead of storing them all in a single file, it may be useful to store them in files that mirror the structure of your site info files, e.g. if you have a config file at `root/data/zlata.de/zlata.de-4/config.json`, you can store relations for that site at `root/relations/zlata.de/zlata.de-4.json`.

A relation file contains a dictionary where values are lists of related items (identified by their full item IDs; these are explained above) and keys are possibly empty prefixes for those item IDs. For example:

```JSON
{
  "zlata.de": [
    [
      "]iamflexigirl.com/004-03",
      "zlata.de-4/z19-10"
    ]
  ],
  "zlata.de/iamflexigirl.com": [
    [
      "v001-82",
      "004-04"
    ],
    [
      "v001-79",
      "004-06"
    ]
  ]
}
```

When the file above is loaded, the item ID `v001-82` is expanded to `zlata.de/iamflexigirl.com/v001-82`. This is useful because it allows us to uniquely identify items and specify relations between sites, even if items on the two sites may have duplicate item IDs.

Importantly, each item ID should only appear once. When the relation file below is loaded, some of the relations will be lost.

```JSON
{
  "zlata.de/iamflexigirl.com": [
    [
      "004-03",
      "v001-77"
    ]
  ],
  "zlata.de": [
    [
      "iamflexigirl.com/004-03",
      "zlata.de-4/z19-10"
    ]
  ]
}
```

## TODO

 * use markdown in model info file biographies and links
 * specify the location of relation files, the model file in global config
 * document the CLI
