#!/usr/bin/env python3
"""Scrape the Benchmark Hub source site into data/ JSON files.

Source: https://steven47521.github.io/Paper_visualization_v2
Outputs (single source of truth for build.py):
    data/benchmarks/<slug>.json   one file per benchmark (PRD schema v1)
    data/models.json              model id -> {name, org, color}

Network access is cached under tools/.cache/ so re-runs are offline-safe (R4).
Run:  python3 tools/scrape.py [--refresh]
"""

import html as htmlmod
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://steven47521.github.io/Paper_visualization_v2"
ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / ".cache"
DATA = ROOT / "data"

REFRESH = "--refresh" in sys.argv


# ── fetching with retry + cache ──────────────────────────────────────────────

def fetch(path: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^a-z0-9_]+", "_", path.strip("/").lower()) or "index"
    cached = CACHE / f"{key}.html"
    if cached.exists() and not REFRESH:
        return cached.read_text(encoding="utf-8")
    url = BASE + path
    last_err = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "tokenwave-scraper/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8")
            cached.write_text(text, encoding="utf-8")
            return text
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


# ── generic HTML helpers ─────────────────────────────────────────────────────

def strip_tags(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = htmlmod.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _unpack_prop(v):
    if isinstance(v, list) and len(v) == 2 and isinstance(v[0], int):
        t, val = v
        if t == 0:
            return {k: _unpack_prop(x) for k, x in val.items()} if isinstance(val, dict) else val
        if t == 1:
            return [_unpack_prop(x) for x in val]
        return val
    return v


def astro_islands(page: str) -> list:
    """Unpack every astro-island props attribute ([type, value] tuples)."""
    out = []
    for m in re.finditer(r'props="([^"]*)"', page):
        raw = json.loads(htmlmod.unescape(m.group(1)))
        out.append({k: _unpack_prop(v) for k, v in raw.items()})
    return out


def astro_island_props(page: str, key: str) -> dict:
    """First astro-island whose props contain `key`."""
    for isl in astro_islands(page):
        if key in isl:
            return isl
    return {}


def section(page: str, heading: str) -> str:
    """Return the <section> whose h2/h3 text equals `heading`."""
    pat = re.compile(
        r"<section[^>]*>(?:(?!</section>).)*?<h[23][^>]*>\s*" + re.escape(heading) + r"\s*</h[23]>.*?</section>",
        re.S,
    )
    m = pat.search(page)
    return m.group(0) if m else ""


# ── per-page parsers ─────────────────────────────────────────────────────────

def parse_meta_bar(page: str) -> dict:
    m = re.search(r'benchmark-meta-bar.*?</div>', page, re.S)
    out = {}
    if m:
        for label, val in re.findall(r'<span class="opacity-80">([^<]+):</span>([^<]*)</?span', m.group(0)):
            out[label.strip().lower()] = strip_tags(val)
    return out


def parse_actions(page: str) -> dict:
    """Hero action buttons: 'Code & website' / 'Paper' links."""
    links = {"paper": None, "code": None}
    header = page.split("benchmark-abstract", 1)[0]
    for url, label in re.findall(r'<a href="(https?://[^"]+)"[^>]*class="benchmark-action-btn[^"]*"[^>]*>\s*([^<]+?)\s*</a>', header):
        label_l = strip_tags(label).lower()
        if "paper" in label_l:
            links["paper"] = url
        elif "code" in label_l or "website" in label_l:
            links["code"] = url
    return links


def parse_pdf(page):
    m = re.search(r'<a href="(https?://[^"]+\.pdf[^"]*)"', page)
    return m.group(1) if m else None


def parse_abstract(page: str) -> str:
    sec = section(page, "Abstract")
    ps = re.findall(r"<p>(.*?)</p>", sec, re.S)
    return " ".join(strip_tags(p) for p in ps)


def parse_contributions(page):
    m = re.search(r'<ul class="benchmark-contrib-list[^"]*">(.*?)</ul>', page, re.S)
    if not m:
        return []
    return [strip_tags(li) for li in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)]


def parse_method(page):
    """Paragraphs between the Method heading and the Evaluation Metrics block."""
    m = re.search(r'bench-method-heading.*?benchmark-prose[^>]*>(.*?)</div>', page, re.S)
    if not m:
        return []
    return [strip_tags(p) for p in re.findall(r"<p>(.*?)</p>", m.group(1), re.S)]


def parse_metrics(page):
    out = []
    for block in re.findall(r'<div class="benchmark-metric-row">(.*?)</div>\s*</div>', page, re.S):
        name = re.search(r"<h4[^>]*>(.*?)</h4>", block, re.S)
        badge = re.search(r'benchmark-metric-badge[^>]*>(.*?)</span>', block, re.S)
        ps = [strip_tags(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", block, re.S)]
        note = ps[0] if ps else ""
        rng = None
        for p in ps:
            rm = re.search(r"Score Range:\s*(\[[^\]]+\])", p)
            if rm:
                rng = rm.group(1)
                if p == note:
                    note = ""
        direction = "higher"
        if badge and "lower" in badge.group(1).lower():
            direction = "lower"
        out.append({
            "name": strip_tags(name.group(1)) if name else "",
            "direction": direction,
            "range": rng,
            "note": note,
        })
    return out


def parse_leaderboard(page: str) -> dict:
    props = astro_island_props(page, "rows")
    cols = props.get("columns", [])
    rows = props.get("rows", [])
    score_key = next((c["key"] for c in cols if c["key"].startswith("score")), None)
    metric_label = next((c["label"] for c in cols if c["key"] == score_key), None)
    entries = []
    for i, r in enumerate(rows):
        entries.append({
            "rank": i + 1,
            "model_id": r.get("model_id"),
            "model": r.get("model_name"),
            "org": r.get("org"),
            "color": r.get("color"),
            "score": r.get(score_key),
            "source": r.get("source"),
            "date": None if r.get("date") in ("-", "", None) else r.get("date"),
        })
    note = ""
    m = re.search(r'bench-lb-heading.*?</div>\s*<p[^>]*>(.*?)</p>', page, re.S)
    if m:
        note = strip_tags(m.group(1))
    return {"metric": metric_label, "note": note, "entries": entries}


def parse_figures(page: str, slug: str) -> list:
    """Paper-figure strip (present on a few pages): download images locally."""
    props = astro_island_props(page, "figures")
    figs = props.get("figures", [])
    out = []
    for f in figs:
        src = f.get("src", "")
        fname = src.rsplit("/", 1)[-1]
        if not fname:
            continue
        local_dir = ROOT / "static" / "images" / "benchmarks" / slug.replace("_", "-")
        local_dir.mkdir(parents=True, exist_ok=True)
        local = local_dir / fname
        if not local.exists():
            url = BASE + src.replace("/Paper_visualization_v2", "", 1)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "tokenwave-scraper/1.0"})
                with urllib.request.urlopen(req, timeout=30) as r:
                    local.write_bytes(r.read())
            except Exception as e:  # noqa: BLE001
                print(f"    figure download failed ({fname}): {e}")
                continue
        out.append({
            "image": f"static/images/benchmarks/{slug.replace('_', '-')}/{fname}",
            "caption": f.get("caption", ""),
        })
    return out


def parse_at_a_glance(page: str) -> dict:
    sec = section(page, "At a Glance")
    out = {}
    for dt, dd in re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>", sec, re.S):
        out[strip_tags(dt).lower().replace(" ", "_")] = strip_tags(dd)
    return out


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    compare_page = fetch("/en/compare/")
    props = astro_island_props(compare_page, "models")
    models = props.get("models", [])
    bench_index = props.get("benchmarkScores", [])
    if not models or not bench_index:
        raise RuntimeError("compare page props missing models/benchmarkScores")

    (DATA / "benchmarks").mkdir(parents=True, exist_ok=True)
    DATA.joinpath("models.json").write_text(
        json.dumps({m["id"]: {"name": m["name"], "org": m["org"], "color": m["color"]} for m in models},
                   indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"models.json: {len(models)} models")

    ok, bad = 0, []
    for b in sorted(bench_index, key=lambda x: x["benchmark_id"]):
        slug, l1 = b["benchmark_id"], b["l1_id"]
        try:
            page = fetch(f"/en/{l1}/{slug}/")
            meta = parse_meta_bar(page)
            lb = parse_leaderboard(page)
            glance = parse_at_a_glance(page)
            record = {
                "slug": slug,
                "name": b["benchmark_name"],
                "domain": l1,
                "domain_name": b["l1_name"],
                "subcategory": b["l2_name"],
                "abstract": parse_abstract(page),
                "contributions": parse_contributions(page),
                "method": parse_method(page),
                "metrics": parse_metrics(page),
                "leaderboard": lb["entries"],
                "leaderboard_metric": lb["metric"],
                "leaderboard_note": lb["note"],
                "at_a_glance": {
                    "focus": glance.get("focus"),
                    "primary_metric": glance.get("primary_metric") or meta.get("primary metric"),
                    "setting": glance.get("displayed_setting"),
                    "models_scored": int(meta.get("models scored", len(lb["entries"]) or 0)),
                    "data_updated": meta.get("data updated"),
                },
                "links": {**parse_actions(page), "pdf": parse_pdf(page)},
                "figures": parse_figures(page, slug),
                "image": f"static/images/benchmarks/{slug.replace('_', '-')}.svg",
            }
            out = DATA / "benchmarks" / f"{slug}.json"
            out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
            ok += 1
            print(f"  {slug:<22} lb={len(lb['entries']):>2}  metrics={len(record['metrics'])}  "
                  f"contrib={len(record['contributions'])}  method={len(record['method'])}")
        except Exception as e:  # noqa: BLE001
            bad.append((slug, str(e)))
            print(f"  {slug:<22} FAILED: {e}")

    print(f"\nscraped {ok}/{len(bench_index)} benchmarks -> data/benchmarks/")
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
