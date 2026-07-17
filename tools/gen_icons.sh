#!/bin/sh
# Rasterize brand assets from SVG sources. Requires rsvg-convert (brew install librsvg).
#   static/favicon.svg               -> favicon-192.png, apple-touch-icon.png (180)
#   tools/templates/og-default.svg   -> static/images/og-default.png (1200x630)
set -e
cd "$(dirname "$0")/.."

rsvg-convert -w 192 -h 192 static/favicon.svg -o static/favicon-192.png
rsvg-convert -w 180 -h 180 static/favicon.svg -o static/apple-touch-icon.png
rsvg-convert -w 1200 -h 630 tools/templates/og-default.svg -o static/images/og-default.png

ls -la static/favicon-192.png static/apple-touch-icon.png static/images/og-default.png
