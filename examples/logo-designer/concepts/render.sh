#!/usr/bin/env bash
# usage: render.sh CONCEPT.svg...   (run from anywhere; paths may be relative)
#   -> ../renders/sheet-<names>.png (per concept row: light 256 | dark 256 | 32px x4 | 16px x8 light/dark)
# Requires: rsvg-convert, ImageMagick (magick).
# Note: the -font path below is the macOS system Helvetica; on other platforms
# point -font at any available sans-serif font file.
set -e
here=$(cd "$(dirname "$0")" && pwd)
out="$here/../renders"; mkdir -p "$out"
rows=()
names=()
for arg in "$@"; do
  svg="$arg"
  n=$(basename "$svg" .svg)
  names+=("$n")
  sed 's/#0A0A0A/#FAFAFA/g' "$svg" > "$out/$n-dark.svg"
  rsvg-convert -w 256 -h 256 -b '#FAFAFA' "$svg" -o "$out/$n-l256.png"
  rsvg-convert -w 256 -h 256 -b '#0A0A0A' "$out/$n-dark.svg" -o "$out/$n-d256.png"
  rsvg-convert -w 32 -h 32 -b '#FAFAFA' "$svg" -o "$out/$n-l32.png"
  rsvg-convert -w 16 -h 16 -b '#FAFAFA' "$svg" -o "$out/$n-l16.png"
  rsvg-convert -w 16 -h 16 -b '#0A0A0A' "$out/$n-dark.svg" -o "$out/$n-d16.png"
  magick "$out/$n-l32.png" -filter point -resize 800% "$out/$n-l32x.png"
  magick "$out/$n-l16.png" -filter point -resize 1600% "$out/$n-l16x.png"
  magick "$out/$n-d16.png" -filter point -resize 1600% "$out/$n-d16x.png"
  magick "$out/$n-l256.png" "$out/$n-d256.png" "$out/$n-l32x.png" "$out/$n-l16x.png" "$out/$n-d16x.png" -bordercolor '#888888' -border 2 +append \
    -gravity North -background '#111111' -splice 0x70 -font /System/Library/Fonts/Helvetica.ttc -fill white -pointsize 28 -annotate +12+48 "$n" "$out/$n-row.png"
  rows+=("$out/$n-row.png")
done
name=$(IFS=-; echo "${names[*]}")
magick "${rows[@]}" -gravity center -background '#111111' -append "$out/sheet-$name.png"
echo "$out/sheet-$name.png"
