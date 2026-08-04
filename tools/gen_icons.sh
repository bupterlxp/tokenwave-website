#!/bin/sh
# Rasterize favicon assets from the SVG source. Requires rsvg-convert.
# The social card at static/images/og-default.png is a curated 1200x630 image
# and is intentionally not overwritten by this icon helper.
set -e
cd "$(dirname "$0")/.."

rsvg-convert -w 192 -h 192 static/favicon.svg -o static/favicon-192.png
rsvg-convert -w 180 -h 180 static/favicon.svg -o static/apple-touch-icon.png

ls -la static/favicon-192.png static/apple-touch-icon.png static/images/og-default.png
