#!/usr/bin/env bash

for dir in */; do
    [ -d "$dir" ] || continue

    for f in "$dir"/*.iff; do
        [ -e "$f" ] || continue  # Skip if no .iff files in the directory

        ffmpeg -y -i "$f" "${f%.bmp}.png"
    done
done
