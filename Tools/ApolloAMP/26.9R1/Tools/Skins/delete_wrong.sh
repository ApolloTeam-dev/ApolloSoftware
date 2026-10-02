#!/usr/bin/env bash

for dir in */; do
    [ -d "$dir" ] || continue

    find "$dir" -type f -name '*.iff.png' -delete
done
