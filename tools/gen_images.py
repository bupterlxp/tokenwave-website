#!/usr/bin/env python3
"""Generate deterministic "paper figure" SVG artwork for benchmarks lacking one.

Family style (matches the 8 hand-drawn originals):
    480x360 canvas, white ground, thin gray frame, grayscale ink with a single
    accent color, monospace annotations, and a bottom "Figure 1:" caption.

Archetype is chosen by subcategory semantics; bar/curve archetypes are driven
by the benchmark's real leaderboard scores. Seeded by slug -> idempotent.

Run:  python3 tools/gen_images.py [--force]
"""

import hashlib
import json
import math
import sys
from pathlib import Path
from random import Random
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "benchmarks"
OUT = ROOT / "static" / "images" / "benchmarks"

FORCE = "--force" in sys.argv

MONO = "Menlo, Consolas, monospace"
INK_DARK, INK, INK_MID, INK_SOFT, INK_FAINT = "#374151", "#475569", "#6b7280", "#9ca3af", "#e5e7eb"
ACCENTS = ["#2563eb", "#0891b2", "#7c3aed", "#059669", "#d97706"]

FOCUS_EN = json.loads((ROOT / "data" / "focus_en.json").read_text(encoding="utf-8"))


def focus_of(d):
    override = FOCUS_EN.get(d["slug"], {})
    return override.get("focus") or d["at_a_glance"].get("focus") or d["subcategory"]


def rng_for(slug):
    seed = int(hashlib.sha256(slug.encode()).hexdigest()[:12], 16)
    return Random(seed)


def txt(x, y, s, size=10, fill=INK_MID, anchor="middle", bold=False):
    w = ' font-weight="bold"' if bold else ""
    a = f' text-anchor="{anchor}"' if anchor else ""
    return (f'<text x="{x}" y="{y}"{a} font-family="{MONO}" '
            f'font-size="{size}" fill="{fill}"{w}>{escape(s)}</text>')


GEN_MARK = "<!-- tokenwave:generated -->"


def frame(inner, caption):
    cap = caption if len(caption) <= 64 else caption[:61].rstrip() + "..."
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 360">\n'
        f"{GEN_MARK}\n"
        '<rect width="480" height="360" fill="#ffffff"/>\n'
        f'<rect x="14" y="14" width="452" height="300" fill="none" stroke="{INK_FAINT}" stroke-width="1.5" rx="6"/>\n'
        + inner +
        f'\n{txt(240, 345, "Figure 1: " + cap, size=12.5, fill=INK_MID)}\n'
        "</svg>"
    )


def top_scores(d, n=6):
    rows = [r for r in d["leaderboard"] if isinstance(r.get("score"), (int, float))][:n]
    return rows


# ── archetypes ───────────────────────────────────────────────────────────────

def arch_bars(rng, d, accent):
    """Descending bars from real leaderboard scores."""
    rows = top_scores(d, 6)
    scores = [r["score"] for r in rows] or [70, 55, 43, 30]
    lo, hi = min(scores), max(scores)
    span = (hi - lo) or 1
    n = len(scores)
    x0, y0, x1 = 78, 252, 442
    bw = min(34, int((x1 - x0 - 14) / n) - 12)
    step = (x1 - x0 - 20) / n
    parts = [
        f'<line x1="{x0-10}" y1="72" x2="{x0-10}" y2="{y0}" stroke="{INK_SOFT}" stroke-width="1.5"/>',
        f'<line x1="{x0-10}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{INK_SOFT}" stroke-width="1.5"/>',
    ]
    for i, s in enumerate(scores):
        h = 28 + (s - lo) / span * 128
        x = x0 + i * step
        op = 1.0 - i * (0.55 / max(n - 1, 1))
        parts.append(f'<rect x="{x:.0f}" y="{y0-h:.1f}" width="{bw}" height="{h:.1f}" fill="{accent}" opacity="{op:.2f}" rx="2"/>')
    parts.append(txt(x0 + bw / 2, y0 - 28 - (scores[0]-lo)/span*128 - 10, f"{scores[0]:g}", size=10, fill=accent, bold=True))
    metric = d.get("leaderboard_metric") or "score"
    parts.append(txt((x0 + x1) / 2, y0 + 20, f"top {n} models, {metric}", size=10, fill=INK_SOFT))
    parts.append(txt(x0 - 10, 58, d["subcategory"].lower(), size=11, fill=INK_DARK, anchor="", bold=True))
    return "\n".join(parts)


def arch_curves(rng, d, accent):
    """Two performance curves degrading over a horizontal dimension."""
    x0, x1, y0, y1 = 66, 434, 246, 84
    parts = [
        f'<line x1="{x0}" y1="{y1-8}" x2="{x0}" y2="{y0}" stroke="{INK_SOFT}" stroke-width="1.5"/>',
        f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{INK_SOFT}" stroke-width="1.5"/>',
    ]
    for k, (color, dash, drop) in enumerate([(accent, "", 0.35), (INK_SOFT, ' stroke-dasharray="6 4"', 0.72)]):
        pts = []
        for i in range(9):
            fx = i / 8
            base = 1 - (fx ** (1.6 + k * 0.5)) * drop
            jitter = (rng.random() - 0.5) * 0.05
            fy = min(1.0, max(0.0, base + jitter))
            pts.append((x0 + fx * (x1 - x0 - 10), y0 - fy * (y0 - y1)))
        dstr = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts)
        parts.append(f'<path d="{dstr}" stroke="{color}" stroke-width="2"{dash} fill="none"/>')
        px, py = pts[-1]
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{color}"/>')
    parts.append(txt(x0 - 4, y1 - 18, d.get("leaderboard_metric") or "score", size=10, fill=INK_MID, anchor=""))
    parts.append(txt((x0 + x1) / 2, y0 + 20, "difficulty / context scale →", size=10, fill=INK_SOFT))
    parts.append(txt(x1 - 6, y1 + 4, "frontier", size=10, fill=accent, anchor="end", bold=True))
    return "\n".join(parts)


def arch_graph(rng, d, accent):
    """Small agent/tool topology graph."""
    cx, cy = 240, 168
    hubs = [(cx, cy)]
    n = 7
    parts = []
    nodes = []
    for i in range(n):
        a = (i / n) * 2 * math.pi + rng.random() * 0.5
        r = 78 + rng.random() * 34
        nodes.append((cx + r * math.cos(a), cy + r * math.sin(a) * 0.72))
    for i, (nx, ny) in enumerate(nodes):
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{INK_FAINT}" stroke-width="1.5"/>')
    for i in range(3):
        a, b = rng.sample(range(n), 2)
        parts.append(f'<line x1="{nodes[a][0]:.1f}" y1="{nodes[a][1]:.1f}" x2="{nodes[b][0]:.1f}" y2="{nodes[b][1]:.1f}" stroke="{INK_FAINT}" stroke-width="1" stroke-dasharray="4 4"/>')
    for i, (nx, ny) in enumerate(nodes):
        if i < 2:
            parts.append(f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="9" fill="{accent}" opacity="0.85"/>')
        else:
            parts.append(f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="7" fill="#ffffff" stroke="{INK}" stroke-width="2"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="13" fill="{INK}"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="#ffffff"/>')
    parts.append(txt(cx, cy + 36, "agent", size=10, fill=INK_MID))
    parts.append(txt(cx, 66, f"{d['at_a_glance'].get('models_scored', len(d['leaderboard']))} models · multi-hop evidence", size=11, fill=INK_DARK, bold=True))
    return "\n".join(parts)


def arch_grid(rng, d, accent):
    """Evaluation matrix with highlighted cells."""
    cols, rows_n = 8, 5
    cell, gap = 32, 8
    gx = 240 - (cols * cell + (cols - 1) * gap) / 2
    gy = 92
    parts = []
    for r in range(rows_n):
        for c in range(cols):
            v = rng.random()
            op = 0.10 if v < 0.55 else (0.32 if v < 0.8 else 0.72)
            parts.append(f'<rect x="{gx + c*(cell+gap):.0f}" y="{gy + r*(cell+gap):.0f}" width="{cell}" height="{cell}" fill="{accent}" opacity="{op:.2f}" rx="5"/>')
    parts.append(txt(240, 76, f"{d['subcategory'].lower()} · per-dimension scores", size=11, fill=INK_DARK, bold=True))
    parts.append(txt(240, gy + rows_n * (cell + gap) + 16, "dimensions ×  models", size=10, fill=INK_SOFT))
    return "\n".join(parts)


def arch_timeline(rng, d, accent):
    """Long-horizon timeline with dispersed evidence markers."""
    x0, x1, y = 62, 438, 176
    parts = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{INK_SOFT}" stroke-width="2"/>']
    for i in range(11):
        tx = x0 + i * (x1 - x0) / 10
        parts.append(f'<line x1="{tx:.0f}" y1="{y-5}" x2="{tx:.0f}" y2="{y+5}" stroke="{INK_SOFT}" stroke-width="1.2"/>')
    marks = sorted(rng.sample(range(1, 10), 3))
    prev = None
    for m in marks:
        tx = x0 + m * (x1 - x0) / 10
        parts.append(f'<circle cx="{tx:.0f}" cy="{y}" r="7" fill="{accent}" opacity="0.85"/>')
        if prev is not None:
            midx = (prev + tx) / 2
            parts.append(f'<path d="M {prev:.0f} {y-11} C {midx:.0f} {y-86} {midx:.0f} {y-86} {tx:.0f} {y-11}" stroke="{accent}" stroke-width="1.8" fill="none" stroke-dasharray="5 4"/>')
        prev = tx
    parts.append(txt(x0, y + 26, "0:00", size=10, fill=INK_SOFT, anchor=""))
    parts.append(txt(x1, y + 26, "long horizon", size=10, fill=INK_SOFT, anchor="end"))
    parts.append(txt(240, 84, "evidence dispersed in time", size=11, fill=INK_DARK, bold=True))
    parts.append(txt(240, 244, "sampling shortcuts break across spans", size=10, fill=INK_MID))
    return "\n".join(parts)


def arch_flow(rng, d, accent):
    """Pipeline boxes with arrows (instruction / workflow benchmarks)."""
    labels = ["input", "plan", "act", "verify"]
    bw, bh, gap = 82, 46, 22
    total = len(labels) * bw + (len(labels) - 1) * gap
    x0, y = 240 - total / 2, 134
    parts = []
    for i, lab in enumerate(labels):
        bx = x0 + i * (bw + gap)
        last = i == len(labels) - 1
        fill = accent if last else "#ffffff"
        stroke = accent if last else INK
        tcol = "#ffffff" if last else INK_DARK
        parts.append(f'<rect x="{bx:.0f}" y="{y}" width="{bw}" height="{bh}" fill="{fill}" opacity="{0.9 if last else 1}" stroke="{stroke}" stroke-width="2" rx="8"/>')
        parts.append(txt(bx + bw / 2, y + bh / 2 + 4, lab, size=11, fill=tcol, bold=last))
        if not last:
            ax = bx + bw
            parts.append(f'<path d="M {ax+3:.0f} {y+bh/2} L {ax+gap-6:.0f} {y+bh/2}" stroke="{INK_MID}" stroke-width="2"/>')
            parts.append(f'<path d="M {ax+gap-10:.0f} {y+bh/2-5} L {ax+gap-4:.0f} {y+bh/2} L {ax+gap-10:.0f} {y+bh/2+5}" fill="none" stroke="{INK_MID}" stroke-width="2"/>')
    loop_x = x0 + 2 * bw + 1.5 * gap
    parts.append(f'<path d="M {x0+3.5*bw+3*gap-24:.0f} {y+bh+6} C {loop_x:.0f} {y+bh+56} {x0+bw:.0f} {y+bh+56} {x0+bw/2:.0f} {y+bh+8}" stroke="{INK_SOFT}" stroke-width="1.6" stroke-dasharray="5 4" fill="none"/>')
    parts.append(txt(240, y + bh + 66, "iterate until constraints hold", size=10, fill=INK_MID))
    parts.append(txt(240, 92, d["subcategory"].lower(), size=11, fill=INK_DARK, bold=True))
    return "\n".join(parts)


def arch_wave(rng, d, accent):
    """Waveform + frame strip (audio-video / omni benchmarks)."""
    x0, x1 = 66, 414
    yw = 128
    parts = []
    n = 44
    for i in range(n):
        h = 8 + abs(math.sin(i * 0.55)) * 42 * (0.5 + rng.random() * 0.5)
        bx = x0 + i * (x1 - x0) / n
        parts.append(f'<rect x="{bx:.1f}" y="{yw-h/2:.1f}" width="4" height="{h:.1f}" fill="{accent}" opacity="0.75" rx="2"/>')
    fy = 196
    for i in range(6):
        fx = x0 + i * 60
        parts.append(f'<rect x="{fx:.0f}" y="{fy}" width="48" height="34" fill="none" stroke="{INK}" stroke-width="1.6" rx="4"/>')
        parts.append(f'<circle cx="{fx+14:.0f}" cy="{fy+12}" r="4" fill="{INK_SOFT}"/>')
        parts.append(f'<path d="M {fx+6:.0f} {fy+28} L {fx+20:.0f} {fy+16} L {fx+32:.0f} {fy+24} L {fx+42:.0f} {fy+14}" stroke="{INK_SOFT}" stroke-width="1.5" fill="none"/>')
    parts.append(f'<line x1="{x0+150}" y1="{yw+30}" x2="{x0+150}" y2="{fy-6}" stroke="{INK_FAINT}" stroke-width="1.5" stroke-dasharray="4 4"/>')
    parts.append(txt(240, 74, "hear it  ×  see it  — one answer", size=11, fill=INK_DARK, bold=True))
    parts.append(txt(240, 260, "audio-visual alignment over time", size=10, fill=INK_MID))
    return "\n".join(parts)


def arch_docs(rng, d, accent):
    """Stacked document cards (knowledge / QA benchmarks)."""
    parts = []
    for i, (dx, dy, rot) in enumerate([(-16, 14, -4), (0, 7, 2), (16, 0, 0)]):
        bx, by = 150 + dx, 82 + dy
        op = [0.35, 0.6, 1.0][i]
        parts.append(f'<g transform="rotate({rot} {bx+62} {by+80})" opacity="{op}">'
                     f'<rect x="{bx}" y="{by}" width="124" height="160" fill="#ffffff" stroke="{INK}" stroke-width="2" rx="6"/>'
                     + "".join(f'<line x1="{bx+16}" y1="{by+26+j*18}" x2="{bx+108}" y2="{by+26+j*18}" stroke="{INK_FAINT}" stroke-width="3"/>' for j in range(7))
                     + "</g>")
    parts.append(f'<circle cx="330" cy="160" r="46" fill="none" stroke="{accent}" stroke-width="3"/>')
    parts.append(f'<line x1="362" y1="194" x2="396" y2="228" stroke="{accent}" stroke-width="5" stroke-linecap="round"/>')
    parts.append(txt(330, 165, "?", size=30, fill=accent, bold=True))
    parts.append(txt(240, 62, focus_of(d).lower()[:44], size=11, fill=INK_DARK, bold=True))
    parts.append(txt(240, 282, "long-tail expertise, verified answers", size=10, fill=INK_MID))
    return "\n".join(parts)


def arch_chat(rng, d, accent):
    """Dialogue bubbles (role-play / multi-turn benchmarks)."""
    parts = []
    bubbles = [(76, 76, 196, False), (208, 128, 190, True), (76, 180, 168, False), (232, 232, 166, True)]
    for bx, by, w, right in bubbles:
        fill = accent if right else "#ffffff"
        stroke = accent if right else INK
        op = 0.85 if right else 1
        parts.append(f'<rect x="{bx}" y="{by}" width="{w}" height="40" fill="{fill}" opacity="{op}" stroke="{stroke}" stroke-width="1.8" rx="14"/>')
        lc = "#ffffff" if right else INK_FAINT
        parts.append(f'<line x1="{bx+18}" y1="{by+16}" x2="{bx+w-18}" y2="{by+16}" stroke="{lc}" stroke-width="3" opacity="0.8"/>')
        parts.append(f'<line x1="{bx+18}" y1="{by+27}" x2="{bx+w-44}" y2="{by+27}" stroke="{lc}" stroke-width="3" opacity="0.5"/>')
    parts.append(txt(404, 96, "role", size=10, fill=INK_MID))
    parts.append(f'<circle cx="404" cy="118" r="14" fill="none" stroke="{INK}" stroke-width="2"/>')
    parts.append(f'<path d="M 390 152 C 390 136 418 136 418 152" stroke="{INK}" stroke-width="2" fill="none"/>')
    parts.append(txt(240, 62, "stay in character, turn after turn", size=11, fill=INK_DARK, bold=True))
    return "\n".join(parts)


def arch_scatter(rng, d, accent):
    """Scatter + frontier (math / reasoning benchmarks)."""
    x0, x1, y0, y1 = 70, 430, 250, 82
    parts = [
        f'<line x1="{x0}" y1="{y1-6}" x2="{x0}" y2="{y0}" stroke="{INK_SOFT}" stroke-width="1.5"/>',
        f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{INK_SOFT}" stroke-width="1.5"/>',
    ]
    best = []
    for _ in range(26):
        fx, fy = rng.random(), rng.random()
        px = x0 + 14 + fx * (x1 - x0 - 30)
        py = y0 - 12 - (fy * 0.75 * (1 - 0.4 * (1 - fx))) * (y0 - y1 - 20)
        r = 3 + rng.random() * 2.5
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r:.1f}" fill="{INK_SOFT}" opacity="0.55"/>')
        best.append((px, py))
    hull = sorted(best)[-5:]
    hx, hy = hull[-1]
    parts.append(f'<path d="M {x0+16} {y0-30} C 180 {y1+30} 320 {y1+10} {x1-16} {y1+16}" stroke="{accent}" stroke-width="2" fill="none" stroke-dasharray="6 4"/>')
    parts.append(f'<circle cx="{x1-26}" cy="{y1+22}" r="6" fill="{accent}"/>')
    parts.append(txt(x1 - 26, y1 + 6, "frontier", size=10, fill=accent, bold=True))
    parts.append(txt((x0+x1)/2, y0 + 20, "problem difficulty →", size=10, fill=INK_SOFT))
    parts.append(txt(x0 - 4, y1 - 16, "solve rate", size=10, fill=INK_MID, anchor=""))
    return "\n".join(parts)


ARCH_BY_SUBCAT = {
    "Code Agent": arch_flow,
    "Search Agent": arch_graph,
    "Multimodal Agent": arch_graph,
    "Image Understanding": arch_grid,
    "Video Captioning": arch_timeline,
    "Long Video Understanding": arch_timeline,
    "Omni Understanding": arch_wave,
    "Knowledge": arch_docs,
    "Reasoning": arch_scatter,
    "Long Context": arch_curves,
    "Safety": arch_bars,
    "Instruction Following": arch_flow,
    "Role-playing": arch_chat,
    "Math": arch_scatter,
    "Text-to-Audio-Video": arch_wave,
}


def caption_for(d):
    return f"{focus_of(d).rstrip('.')}."


def main():
    count = 0
    for f in sorted(DATA.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        out = OUT / f"{d['slug'].replace('_', '-')}.svg"
        if out.exists():
            # Never touch hand-drawn artwork; regenerate our own only with --force
            if GEN_MARK not in out.read_text(encoding="utf-8"):
                continue
            if not FORCE:
                continue
        rng = rng_for(d["slug"])
        accent = ACCENTS[rng.randrange(len(ACCENTS))]
        arch = ARCH_BY_SUBCAT.get(d["subcategory"], arch_bars)
        svg = frame(arch(rng, d, accent), caption_for(d))
        out.write_text(svg + "\n", encoding="utf-8")
        count += 1
        print(f"  {out.name:<28} {arch.__name__[5:]:<9} {accent}")
    print(f"generated {count} SVGs (hand-drawn files untouched)")


if __name__ == "__main__":
    main()
