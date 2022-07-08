#!/usr/bin/env zsh

if [[ $# -ne 2 ]]; then
    echo "takes two args"
    exit 1
fi

if [[ ! -f $2 ]]; then
    echo "$2 does not exist"
    exit 1
fi

magick convert $2 -resize x300 -gravity center -background white -extent 200x300 /Users/benzlock/Desktop/mhg1o/canon/static/model-images/$1.jpg
