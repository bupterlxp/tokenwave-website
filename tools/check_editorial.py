#!/usr/bin/env python3
"""Mechanical QA for data/editorial/*.json (the LLM-written layer).

Checks shape, language, bounds, and that the leaderboard leader is cited
with its exact score in `reading`. Complements the adversarial review that
runs at write time.

Run:  python3 tools/check_editorial.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "data" / "benchmarks"
ED = ROOT / "data" / "editorial"

CJK = re.compile(r"[一-鿿]")
TAGS = re.compile(r"<[a-zA-Z/][^>]*>")

errors = []
warnings = []


def err(slug, msg):
    errors.append(f"{slug}: {msg}")


def warn(slug, msg):
    warnings.append(f"{slug}: {msg}")


bench_files = sorted(BENCH.glob("*.json"))
for bf in bench_files:
    b = json.loads(bf.read_text(encoding="utf-8"))
    slug = b["slug"]
    ef = ED / f"{slug}.json"
    if not ef.exists():
        err(slug, "missing editorial file")
        continue
    try:
        e = json.loads(ef.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        err(slug, f"invalid JSON: {ex}")
        continue

    for key in ("slug", "tagline", "stats", "overview", "why", "reading"):
        if key not in e:
            err(slug, f"missing key {key!r}")
    if e.get("slug") != slug:
        err(slug, f"slug mismatch: {e.get('slug')!r}")

    tl = e.get("tagline", "")
    if not (50 <= len(tl) <= 130):
        warn(slug, f"tagline length {len(tl)} outside 50-130")
    if tl.endswith("."):
        warn(slug, "tagline ends with a period")

    stats = e.get("stats", [])
    if not (3 <= len(stats) <= 4):
        err(slug, f"stats has {len(stats)} tiles (want 3-4)")
    for s in stats:
        if not s.get("value") or not s.get("label"):
            err(slug, f"stat tile missing value/label: {s}")

    for key, lo, hi in (("overview", 2, 3), ("why", 1, 2), ("reading", 1, 2)):
        paras = e.get(key, [])
        if not (lo <= len(paras) <= hi):
            err(slug, f"{key} has {len(paras)} paragraphs (want {lo}-{hi})")
        for p in paras:
            words = len(p.split())
            if words < 25 or words > 130:
                warn(slug, f"{key} paragraph of {words} words")

    blob = json.dumps(e, ensure_ascii=False)
    if CJK.search(blob):
        err(slug, "contains CJK characters")
    if TAGS.search(blob):
        err(slug, "contains HTML tags")

    # Leader citation: reading must mention leaderboard[0]'s model and score
    if b["leaderboard"]:
        lead = b["leaderboard"][0]
        reading = " ".join(e.get("reading", []))
        score_str = f"{lead['score']:g}"
        if score_str not in reading:
            err(slug, f"reading does not cite leader score {score_str}")
        # accept partial model-name match (e.g. "Claude Sonnet 4" for full variant names)
        name_bits = [w for w in re.split(r"[\s\-]+", lead["model"]) if len(w) > 1]
        if name_bits and not any(bit.lower() in reading.lower() for bit in name_bits):
            err(slug, f"reading does not mention leader model {lead['model']!r}")

print(f"editorial files: {sum(1 for _ in ED.glob('*.json')) if ED.exists() else 0} / {len(bench_files)}")
if warnings:
    print(f"\n{len(warnings)} warnings:")
    for w in warnings:
        print("  ~ " + w)
if errors:
    print(f"\nFAILED — {len(errors)} errors:")
    for e in errors:
        print("  ✗ " + e)
    sys.exit(1)
print("\nOK — all editorial files pass mechanical checks.")
