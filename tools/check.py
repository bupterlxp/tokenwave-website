#!/usr/bin/env python3
"""Site-wide QA: every internal href/src/background-image must resolve to a file.

Also flags leftover template signatures that should not survive M3.
Run:  python3 tools/check.py
"""

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN = ["Space Mono", "SpaceMono", "unipat", "typewriter", "dict-entry"]

errors = []
pages = sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("benchmarks/*.html")) + sorted(ROOT.glob("blog/*.html"))

ref_pat = re.compile(r"""(?:href|src)=["']([^"']+)["']|background-image:\s*url\(['"]?([^'")]+)['"]?\)""")

for page in pages:
    text = page.read_text(encoding="utf-8")
    rel = page.relative_to(ROOT)

    for name in FORBIDDEN:
        if name in text:
            errors.append(f"{rel}: forbidden signature {name!r}")

    for m in ref_pat.finditer(text):
        raw = m.group(1) or m.group(2)
        if not raw or raw.startswith(("http://", "https://", "mailto:", "#", "data:")):
            continue
        target = unquote(urlparse(raw).path)
        resolved = (page.parent / target).resolve()
        if not resolved.exists():
            errors.append(f"{rel}: broken ref -> {raw}")

# Cross-checks: every benchmark JSON has a page and an image; sitemap covers all pages
import json  # noqa: E402

benches = sorted((ROOT / "data" / "benchmarks").glob("*.json"))
for f in benches:
    d = json.loads(f.read_text(encoding="utf-8"))
    fs = d["slug"].replace("_", "-")
    if not (ROOT / "benchmarks" / f"{fs}.html").exists():
        errors.append(f"data: missing page for {d['slug']}")
    if not (ROOT / d["image"]).exists():
        errors.append(f"data: missing image {d['image']}")

sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
for page in pages:
    rel = str(page.relative_to(ROOT))
    needle = "tokenwave.ai/" if rel == "index.html" else f"tokenwave.ai/{rel}"
    if needle not in sitemap:
        errors.append(f"sitemap: missing {rel}")

if errors:
    print(f"FAILED — {len(errors)} problems:")
    for e in errors:
        print("  " + e)
    sys.exit(1)

print(f"OK — {len(pages)} pages checked, all internal refs resolve, no forbidden signatures, sitemap complete.")
