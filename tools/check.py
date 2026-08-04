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
pages = (sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("benchmarks/*.html"))
         + sorted(ROOT.glob("research/*.html")))

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

# The homepage mission is deliberate brand copy, not generated filler. Keep the
# three messages present even when asset fingerprints are refreshed.
home = (ROOT / "index.html").read_text(encoding="utf-8")
for phrase in (
    "Our mission:",
    "AI-powered workflows",
    "every industry",
    "A data flywheel",
    "digital-worker revolution",
    "unleashing productivity",
    "intelligence emerges",
    "tokens flow and communicate",
    "unlocking productivity",
):
    if phrase not in home:
        errors.append(f"index.html: missing homepage mission phrase {phrase!r}")
if not (ROOT / "static" / "images" / "og-mission.png").is_file():
    errors.append("index.html: missing mission social card static/images/og-mission.png")

# Research is English-only, and Careers evidence cards intentionally omit live
# leaderboard leaders/scores. Those details belong on benchmark detail pages.
han = re.compile(r"[\u4e00-\u9fff]")
for research_page in [ROOT / "research.html", *sorted((ROOT / "research").glob("*.html"))]:
    research_text = research_page.read_text(encoding="utf-8")
    if han.search(research_text):
        errors.append(f"{research_page.relative_to(ROOT)}: contains Chinese copy")
careers_text = (ROOT / "careers.html").read_text(encoding="utf-8")
if '<span class="lead">' in careers_text:
    errors.append("careers.html: evidence cards must not show SOTA model names or scores")

# Cross-checks: every published benchmark has a page, every record has an image,
# and the sitemap covers canonical pages (not compatibility redirects).
import json  # noqa: E402

bench_files = sorted((ROOT / "data" / "benchmarks").glob("*.json"))
benches = {d["slug"]: d for f in bench_files
           for d in [json.loads(f.read_text(encoding="utf-8"))]}
careers = json.loads((ROOT / "data" / "careers.json").read_text(encoding="utf-8"))["careers"]
posts = [json.loads(f.read_text(encoding="utf-8"))
         for f in (ROOT / "data" / "blog").glob("*.json")]
research = json.loads((ROOT / "data" / "research.json").read_text(encoding="utf-8"))
published = ({s for career in careers for s in career["benchmarks"]}
             | {post["benchmark"] for post in posts}
             | {item["slug"] for item in research["featured"]})

paper_types = {"benchmark", "benchmark_system", "system", "model", "training", "data"}
benchmark_types = {"benchmark", "benchmark_system"}

for d in benches.values():
    fs = d["slug"].replace("_", "-")
    page = ROOT / "benchmarks" / f"{fs}.html"
    if d["slug"] in published and not page.exists():
        errors.append(f"data: missing page for {d['slug']}")
    if d["slug"] not in published and page.exists():
        errors.append(f"data: unpublished page was not removed for {d['slug']}")
    if not (ROOT / d["image"]).exists():
        errors.append(f"data: missing image {d['image']}")

    if d["slug"] not in published:
        continue

    paper_type = d.get("paper_type")
    if paper_type not in paper_types:
        errors.append(f"data: {d['slug']} has invalid or missing paper_type {paper_type!r}")
    if len(d.get("abstract", "")) < 500:
        errors.append(f"data: {d['slug']} abstract is too brief")
    for field, minimum in (("contributions", 4), ("method", 5), ("metrics", 3), ("figures", 2)):
        if len(d.get(field, [])) < minimum:
            errors.append(f"data: {d['slug']} needs at least {minimum} {field} entries")
    for figure in d.get("figures", []):
        image = figure.get("image", "")
        if not image or not (ROOT / image).is_file():
            errors.append(f"data: {d['slug']} has missing paper figure {image!r}")
        if not figure.get("caption"):
            errors.append(f"data: {d['slug']} has an uncaptioned paper figure")

    leaderboard = d.get("leaderboard", [])
    if paper_type in benchmark_types and not leaderboard:
        errors.append(f"data: benchmark paper {d['slug']} has no leaderboard")
    if paper_type not in benchmark_types and leaderboard:
        errors.append(f"data: non-benchmark paper {d['slug']} must not expose a leaderboard")
    if leaderboard:
        ranks = [row.get("rank") for row in leaderboard]
        scores = [row.get("score") for row in leaderboard]
        valid_ranks = (ranks and ranks[0] == 1
                       and all(isinstance(rank, int) for rank in ranks)
                       and all(left <= right for left, right in zip(ranks, ranks[1:]))
                       and all(rank <= index for index, rank in enumerate(ranks, start=1)))
        if not valid_ranks:
            errors.append(f"data: {d['slug']} leaderboard ranks are malformed")
        if all(isinstance(score, (int, float)) for score in scores):
            if any(left < right for left, right in zip(scores, scores[1:])):
                errors.append(f"data: {d['slug']} leaderboard is not sorted high to low")
        if not d.get("leaderboard_metric") or not d.get("leaderboard_note"):
            errors.append(f"data: {d['slug']} leaderboard lacks metric or setting note")

sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
for page in pages:
    rel = str(page.relative_to(ROOT))
    if rel in {"benchmarks.html", "blog.html"}:
        continue
    needle = "tokenwave.ai/" if rel == "index.html" else f"tokenwave.ai/{rel}"
    if needle not in sitemap:
        errors.append(f"sitemap: missing {rel}")

if errors:
    print(f"FAILED — {len(errors)} problems:")
    for e in errors:
        print("  " + e)
    sys.exit(1)

print(f"OK — {len(pages)} pages checked, all internal refs resolve, no forbidden signatures, sitemap complete.")
