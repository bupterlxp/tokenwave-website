#!/usr/bin/env python3
"""Generate content-specific benchmark artwork.

Every benchmark gets a bespoke poster-style scene drawn with one shared
visual language: bold 7px ink outlines, flat domain accent colors, large
focal compositions that stay readable down to ~92px wide (the smallest
placement on the site).  Scenes are composed from the primitive kit below;
coverage is explicit — a new benchmark must define its own scene.

Run:
    python3 tools/gen_images.py --force   # redraw every asset
    python3 tools/gen_images.py --check   # validate coverage and freshness
"""

import json
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "benchmarks"
OUT = ROOT / "static" / "images" / "benchmarks"
FORCE = "--force" in sys.argv
CHECK = "--check" in sys.argv

W, H = 480, 360
BG = "#F4F6FB"        # matches the site's --tile-bg light well exactly
INK = "#26313F"       # primary outline
SOFT = "#C9D4E2"      # secondary structure / hairlines
TLINE = "#A9B6C8"     # placeholder text strokes
WHITE = "#FFFFFF"
GREEN = "#059669"
RED = "#DC2626"
AMBER = "#D97706"
STK = 7               # primary stroke width
S2 = 4.5              # secondary stroke width

DOMAIN_PALETTES = {
    "llm": ("#2563EB", "#0D9488"),
    "agent": ("#2563EB", "#7C3AED"),
    "multimodal": ("#4F46E5", "#C026D3"),
    "aigc": ("#7C3AED", "#DB2777"),
}

SANS = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONO = "'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', monospace"


def fmt(v):
    """Compact number formatting for path data."""
    r = round(float(v), 1)
    return str(int(r)) if r == int(r) else f"{r:g}"


# ── primitive kit ────────────────────────────────────────────────────────

def path(d, w=STK, stroke=INK, fill="none", dash=None, op=None, cap="round"):
    s = f'<path d="{d}" fill="{fill}"'
    if stroke:
        s += (f' stroke="{stroke}" stroke-width="{fmt(w)}"'
              f' stroke-linecap="{cap}" stroke-linejoin="round"')
    if dash:
        s += f' stroke-dasharray="{dash}"'
    if op:
        s += f' opacity="{op}"'
    return s + "/>"


def rrect(x, y, w, h, r=16, fill=WHITE, stroke=INK, sw=STK, dash=None, op=None):
    s = (f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" '
         f'rx="{fmt(r)}" fill="{fill}"')
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{fmt(sw)}" stroke-linejoin="round"'
    if dash:
        s += f' stroke-dasharray="{dash}"'
    if op:
        s += f' opacity="{op}"'
    return s + "/>"


def circle(cx, cy, r, fill, stroke=None, sw=STK, op=None, dash=None):
    s = f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{fmt(sw)}"'
    if dash:
        s += f' stroke-dasharray="{dash}"'
    if op:
        s += f' opacity="{op}"'
    return s + "/>"


def seg(x1, y1, x2, y2, color=INK, w=STK, dash=None, op=None):
    return path(f"M {fmt(x1)} {fmt(y1)} L {fmt(x2)} {fmt(y2)}", w, color,
                dash=dash, op=op)


def text(x, y, s, size=26, fill=INK, weight=700, anchor="middle", font=SANS,
         spacing=None):
    extra = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{fmt(x)}" y="{fmt(y)}" text-anchor="{anchor}" '
            f'font-family="{font}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}"{extra}>{escape(str(s))}</text>')


def tline(x, y, length, w=7, color=TLINE, op=None):
    """One placeholder text line."""
    return seg(x, y, x + length, y, color, w, op=op)


def halo(cx, cy, rx, ry, color, op=.07):
    return (f'<ellipse cx="{fmt(cx)}" cy="{fmt(cy)}" rx="{fmt(rx)}" '
            f'ry="{fmt(ry)}" fill="{color}" opacity="{op}"/>')


def arrow(x1, y1, x2, y2, bend=0, color=INK, w=STK, dash=None, op=None):
    """Chunky arrow with an explicit filled head; bend > 0 curves left."""
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1
    nx, ny = -dy / length, dx / length
    cx, cy = mx + nx * bend, my + ny * bend
    hd = math.atan2(y2 - cy, x2 - cx)
    hl = 3.0 * w
    ex, ey = x2 - math.cos(hd) * hl * .72, y2 - math.sin(hd) * hl * .72
    parts = [path(f"M {fmt(x1)} {fmt(y1)} Q {fmt(cx)} {fmt(cy)} {fmt(ex)} {fmt(ey)}",
                  w, color, dash=dash, op=op)]
    hw = 1.35 * w
    b1x = x2 - math.cos(hd) * hl + math.sin(hd) * hw
    b1y = y2 - math.sin(hd) * hl - math.cos(hd) * hw
    b2x = x2 - math.cos(hd) * hl - math.sin(hd) * hw
    b2y = y2 - math.sin(hd) * hl + math.cos(hd) * hw
    parts.append(path(f"M {fmt(x2)} {fmt(y2)} L {fmt(b1x)} {fmt(b1y)} "
                      f"L {fmt(b2x)} {fmt(b2y)} Z", w * .55, color, fill=color, op=op))
    return "\n".join(parts)


def window(x, y, w, h, bar=36, r=18, sw=STK, dots=True, fill=WHITE):
    parts = [rrect(x, y, w, h, r, fill=fill, sw=sw)]
    parts.append(seg(x + 2, y + bar, x + w - 2, y + bar, SOFT, S2))
    if dots:
        for i, c in enumerate(("#F87171", "#FBBF24", "#34D399")):
            parts.append(circle(x + 24 + i * 19, y + bar / 2, 5.5, c))
    return "\n".join(parts)


def doc(x, y, w, h, fold=30, lines=(), r=8, sw=STK, lc=TLINE, lw=7, fill=WHITE):
    """Document with folded top-right corner; lines = (dy, x0frac, x1frac)."""
    d = (f"M {fmt(x + r)} {fmt(y)} H {fmt(x + w - fold)} L {fmt(x + w)} {fmt(y + fold)} "
         f"V {fmt(y + h - r)} Q {fmt(x + w)} {fmt(y + h)} {fmt(x + w - r)} {fmt(y + h)} "
         f"H {fmt(x + r)} Q {fmt(x)} {fmt(y + h)} {fmt(x)} {fmt(y + h - r)} "
         f"V {fmt(y + r)} Q {fmt(x)} {fmt(y)} {fmt(x + r)} {fmt(y)} Z")
    parts = [path(d, sw, INK, fill=fill)]
    parts.append(path(f"M {fmt(x + w - fold)} {fmt(y)} V {fmt(y + fold)} H {fmt(x + w)}",
                      sw, INK))
    for dy, f0, f1 in lines:
        parts.append(seg(x + w * f0, y + dy, x + w * f1, y + dy, lc, lw))
    return "\n".join(parts)


def bubble(x, y, w, h, r=18, tail="bl", fill=WHITE, stroke=INK, sw=STK):
    tw, th = 24, 20
    if tail == "bl":
        t0, tip = x + 30, x + 22
        bottom = (f"H {fmt(t0 + tw)} L {fmt(tip)} {fmt(y + h + th)} L {fmt(t0)} {fmt(y + h)} "
                  f"H {fmt(x + r)}")
    elif tail == "br":
        t0 = x + w - 30 - tw
        bottom = (f"H {fmt(x + w - 30)} L {fmt(x + w - 22)} {fmt(y + h + th)} "
                  f"L {fmt(t0)} {fmt(y + h)} H {fmt(x + r)}")
    else:
        bottom = f"H {fmt(x + r)}"
    d = (f"M {fmt(x + r)} {fmt(y)} H {fmt(x + w - r)} Q {fmt(x + w)} {fmt(y)} "
         f"{fmt(x + w)} {fmt(y + r)} V {fmt(y + h - r)} Q {fmt(x + w)} {fmt(y + h)} "
         f"{fmt(x + w - r)} {fmt(y + h)} {bottom} Q {fmt(x)} {fmt(y + h)} {fmt(x)} "
         f"{fmt(y + h - r)} V {fmt(y + r)} Q {fmt(x)} {fmt(y)} {fmt(x + r)} {fmt(y)} Z")
    return path(d, sw, stroke, fill=fill)


def film(x, y, w, h, accent, play=True, r=14, sw=STK, frames=3):
    parts = [rrect(x, y, w, h, r, sw=sw)]
    n = max(3, int(w // 46))
    step = (w - 32) / (n - 1) if n > 1 else 0
    for i in range(n):
        hx = x + 16 + i * step - 6
        parts.append(rrect(hx, y + 9, 13, 9, 3, fill="#D6DEEA", stroke=None))
        parts.append(rrect(hx, y + h - 18, 13, 9, 3, fill="#D6DEEA", stroke=None))
    for i in range(1, frames):
        fx = x + w * i / frames
        parts.append(seg(fx, y + 26, fx, y + h - 26, SOFT, 4.5))
    if play:
        cx, cy = x + w / 2, y + h / 2
        parts.append(path(f"M {fmt(cx - 13)} {fmt(cy - 19)} L {fmt(cx + 21)} {fmt(cy)} "
                          f"L {fmt(cx - 13)} {fmt(cy + 19)} Z", 6, accent, fill=accent))
    return "\n".join(parts)


def wave(cx, cy, w, n, colors, seed=0, hmin=16, hmax=68, bw=10):
    gap = (w - n * bw) / (n - 1)
    parts = []
    for i in range(n):
        h = hmin + (hmax - hmin) * (0.3 + 0.7 * abs(math.sin(i * 0.93 + seed * 1.7)))
        bx = cx - w / 2 + i * (bw + gap)
        parts.append(rrect(bx, cy - h / 2, bw, h, bw / 2,
                           fill=colors[i % len(colors)], stroke=None))
    return "\n".join(parts)


def shield(cx, cy, s, fill=WHITE, stroke=INK, sw=STK):
    d = (f"M {fmt(cx - .82 * s)} {fmt(cy - .58 * s)} L {fmt(cx)} {fmt(cy - .8 * s)} "
         f"L {fmt(cx + .82 * s)} {fmt(cy - .58 * s)} V {fmt(cy + .1 * s)} "
         f"C {fmt(cx + .82 * s)} {fmt(cy + .55 * s)} {fmt(cx + .4 * s)} {fmt(cy + .82 * s)} "
         f"{fmt(cx)} {fmt(cy + s)} "
         f"C {fmt(cx - .4 * s)} {fmt(cy + .82 * s)} {fmt(cx - .82 * s)} {fmt(cy + .55 * s)} "
         f"{fmt(cx - .82 * s)} {fmt(cy + .1 * s)} Z")
    return path(d, sw, stroke, fill=fill)


def check(cx, cy, r=27, ring=True):
    parts = []
    if ring:
        parts.append(circle(cx, cy, r + 5, BG))
    parts.append(circle(cx, cy, r, GREEN))
    k = r / 27
    parts.append(path(f"M {fmt(cx - 11 * k)} {fmt(cy + 1 * k)} L {fmt(cx - 3 * k)} "
                      f"{fmt(cy + 10 * k)} L {fmt(cx + 13 * k)} {fmt(cy - 9 * k)}",
                      6.5 * k, "#fff"))
    return "\n".join(parts)


def cross(cx, cy, r=22, color=RED, ring=True):
    parts = []
    if ring:
        parts.append(circle(cx, cy, r + 5, BG))
    parts.append(circle(cx, cy, r, color))
    k = r / 22 * 8
    parts.append(path(f"M {fmt(cx - k)} {fmt(cy - k)} L {fmt(cx + k)} {fmt(cy + k)} "
                      f"M {fmt(cx + k)} {fmt(cy - k)} L {fmt(cx - k)} {fmt(cy + k)}",
                      6 * r / 22, "#fff"))
    return "\n".join(parts)


def bang(cx, cy, r=22, color=AMBER, ring=True):
    parts = []
    if ring:
        parts.append(circle(cx, cy, r + 5, BG))
    parts.append(circle(cx, cy, r, color))
    k = r / 22
    parts.append(seg(cx, cy - 9 * k, cx, cy + 2 * k, "#fff", 6.5 * k))
    parts.append(circle(cx, cy + 10 * k, 3.6 * k, "#fff"))
    return "\n".join(parts)


def loupe(cx, cy, r, ang=42, sw=9, glass=.8):
    a = math.radians(ang)
    x1, y1 = cx + math.cos(a) * (r + 2), cy + math.sin(a) * (r + 2)
    x2, y2 = cx + math.cos(a) * (r + 30 + r * .22), cy + math.sin(a) * (r + 30 + r * .22)
    parts = [circle(cx, cy, r, WHITE, INK, sw, op=None)]
    parts[0] = circle(cx, cy, r, f"rgba(255,255,255,{glass})", INK, sw)
    parts.append(seg(x1, y1, x2, y2, INK, sw + 6))
    return "\n".join(parts)


def chip(cx, cy, s, accent):
    half = s / 2
    parts = []
    for off in (-s * .26, 0, s * .26):
        parts.append(seg(cx + off, cy - half - 14, cx + off, cy - half, SOFT, 6))
        parts.append(seg(cx + off, cy + half, cx + off, cy + half + 14, SOFT, 6))
        parts.append(seg(cx - half - 14, cy + off, cx - half, cy + off, SOFT, 6))
        parts.append(seg(cx + half, cy + off, cx + half + 14, cy + off, SOFT, 6))
    parts.append(rrect(cx - half, cy - half, s, s, s * .18))
    parts.append(rrect(cx - half * .5, cy - half * .5, s * .5, s * .5, s * .09,
                       fill=accent, stroke=accent, sw=5, op=None))
    inner = parts.pop()
    parts.append(rrect(cx - half * .5, cy - half * .5, s * .5, s * .5, s * .09,
                       fill="none", stroke=accent, sw=5))
    parts.append(circle(cx, cy, s * .08, accent))
    return "\n".join(parts)


def funnel(cx, cy, w, h, sw=STK):
    y0, y1, y2 = cy - h / 2, cy + h * .12, cy + h / 2
    xw, xn = w / 2, w * .12
    d = (f"M {fmt(cx - xw)} {fmt(y0)} H {fmt(cx + xw)} L {fmt(cx + xn)} {fmt(y1)} "
         f"V {fmt(y2)} H {fmt(cx - xn)} V {fmt(y1)} Z")
    return path(d, sw, INK, fill=WHITE)


def cyl(cx, cy, w, h, accent, sw=STK):
    rx, ry = w / 2, w * .17
    parts = [path(f"M {fmt(cx - rx)} {fmt(cy - h / 2)} V {fmt(cy + h / 2)} "
                  f"A {fmt(rx)} {fmt(ry)} 0 0 0 {fmt(cx + rx)} {fmt(cy + h / 2)} "
                  f"V {fmt(cy - h / 2)}", sw, INK, fill=WHITE)]
    parts.append(f'<ellipse cx="{fmt(cx)}" cy="{fmt(cy - h / 2)}" rx="{fmt(rx)}" '
                 f'ry="{fmt(ry)}" fill="{accent}" opacity=".15" stroke="{INK}" '
                 f'stroke-width="{fmt(sw)}"/>')
    parts.append(path(f"M {fmt(cx - rx)} {fmt(cy)} A {fmt(rx)} {fmt(ry)} 0 0 0 "
                      f"{fmt(cx + rx)} {fmt(cy)}", S2, SOFT))
    return "\n".join(parts)


def pin(cx, cy, s, color):
    """Map pin, tip at (cx, cy)."""
    r = s
    hy = cy - 1.75 * r
    d = (f"M {fmt(cx)} {fmt(cy)} C {fmt(cx - .9 * r)} {fmt(cy - .85 * r)} "
         f"{fmt(cx - r)} {fmt(cy - 1.3 * r)} {fmt(cx - r)} {fmt(hy + .45 * r)} "
         f"A {fmt(r)} {fmt(r)} 0 1 1 {fmt(cx + r)} {fmt(hy + .45 * r)} "
         f"C {fmt(cx + r)} {fmt(cy - 1.3 * r)} {fmt(cx + .9 * r)} {fmt(cy - .85 * r)} "
         f"{fmt(cx)} {fmt(cy)} Z")
    return path(d, 5, color, fill=color) + circle(cx, hy + .13 * r, r * .34, WHITE)


def clockface(cx, cy, r, sw=STK):
    parts = [circle(cx, cy, r, WHITE, INK, sw)]
    for a in range(4):
        rad = math.radians(a * 90)
        parts.append(seg(cx + math.cos(rad) * (r - 5), cy + math.sin(rad) * (r - 5),
                         cx + math.cos(rad) * (r - 12), cy + math.sin(rad) * (r - 12),
                         SOFT, 4.5))
    parts.append(path(f"M {fmt(cx)} {fmt(cy)} V {fmt(cy - r * .55)} "
                      f"M {fmt(cx)} {fmt(cy)} L {fmt(cx + r * .42)} {fmt(cy + r * .24)}",
                      6, INK))
    return "\n".join(parts)


def cursor(x, y, s=1.0):
    d = (f"M {fmt(x)} {fmt(y)} L {fmt(x + 12 * s)} {fmt(y + 33 * s)} "
         f"L {fmt(x + 17 * s)} {fmt(y + 20 * s)} L {fmt(x + 31 * s)} {fmt(y + 17 * s)} Z")
    return path(d, 5, BG, fill=INK)


def zh(cx, cy, s, color, w=None):
    """The character 中 drawn as strokes (no CJK font dependency)."""
    w = w or max(6, s * .17)
    parts = [rrect(cx - s * .6, cy - s * .38, s * 1.2, s * .76, s * .06,
                   fill="none", stroke=color, sw=w)]
    parts.append(seg(cx, cy - s * .9, cx, cy + s * .9, color, w))
    return "\n".join(parts)


def turnstile(cx, cy, s, color, w=None):
    """The ⊢ turnstile drawn as strokes."""
    w = w or max(8, s * .18)
    return (seg(cx - s * .34, cy - s, cx - s * .34, cy + s, color, w) + "\n" +
            seg(cx - s * .34, cy, cx + s * .66, cy, color, w))


def notepair(cx, cy, s, color):
    parts = []
    for hx, hy in ((cx - s * .42, cy + s * .55), (cx + s * .5, cy + s * .42)):
        parts.append(f'<ellipse cx="{fmt(hx)}" cy="{fmt(hy)}" rx="{fmt(s * .26)}" '
                     f'ry="{fmt(s * .19)}" fill="{color}" '
                     f'transform="rotate(-18 {fmt(hx)} {fmt(hy)})"/>')
    x1, x2 = cx - s * .42 + s * .24, cx + s * .5 + s * .24
    parts.append(path(f"M {fmt(x1)} {fmt(cy + s * .5)} V {fmt(cy - s * .62)} "
                      f"L {fmt(x2)} {fmt(cy - s * .78)} V {fmt(cy + s * .37)}",
                      s * .11, color))
    parts.append(path(f"M {fmt(x1)} {fmt(cy - s * .62)} L {fmt(x2)} {fmt(cy - s * .78)}",
                      s * .3, color, cap="butt"))
    return "\n".join(parts)


def heart(cx, cy, s, fill):
    d = (f"M {fmt(cx)} {fmt(cy + s * .85)} C {fmt(cx - s * 1.25)} {fmt(cy + s * .05)} "
         f"{fmt(cx - s * .78)} {fmt(cy - s * .92)} {fmt(cx)} {fmt(cy - s * .28)} "
         f"C {fmt(cx + s * .78)} {fmt(cy - s * .92)} {fmt(cx + s * 1.25)} "
         f"{fmt(cy + s * .05)} {fmt(cx)} {fmt(cy + s * .85)} Z")
    return path(d, 5, fill, fill=fill)


def mask(cx, cy, s, fill, mood="smile", rot=0):
    parts = [f'<g transform="rotate({rot} {fmt(cx)} {fmt(cy)})">']
    parts.append(rrect(cx - s * .62, cy - s * .8, s * 1.24, s * 1.6, s * .56, fill=fill))
    for ex in (cx - s * .27, cx + s * .27):
        parts.append(f'<ellipse cx="{fmt(ex)}" cy="{fmt(cy - s * .22)}" '
                     f'rx="{fmt(s * .15)}" ry="{fmt(s * .1)}" fill="{INK}"/>')
    if mood == "smile":
        parts.append(path(f"M {fmt(cx - s * .3)} {fmt(cy + s * .22)} "
                          f"Q {fmt(cx)} {fmt(cy + s * .52)} {fmt(cx + s * .3)} "
                          f"{fmt(cy + s * .22)}", 6, INK))
    else:
        parts.append(path(f"M {fmt(cx - s * .3)} {fmt(cy + s * .42)} "
                          f"Q {fmt(cx)} {fmt(cy + s * .18)} {fmt(cx + s * .3)} "
                          f"{fmt(cy + s * .42)}", 6, INK))
    parts.append("</g>")
    return "\n".join(parts)


def tablegrid(x, y, w, h, rows, cols, accent, hl=(), sw=STK, header=True):
    hh = h / (rows + 1) if header else 0
    parts = [rrect(x, y, w, h, 12, sw=sw)]
    if header:
        parts.append(path(f"M {fmt(x + 12)} {fmt(y)} H {fmt(x + w - 12)} Q {fmt(x + w)} "
                          f"{fmt(y)} {fmt(x + w)} {fmt(y + 12)} V {fmt(y + hh)} H {fmt(x)} "
                          f"V {fmt(y + 12)} Q {fmt(x)} {fmt(y)} {fmt(x + 12)} {fmt(y)} Z",
                          0, None, fill=accent, op=.14))
    for r, c in hl:
        parts.append(rrect(x + c * w / cols + 5, y + hh + r * (h - hh) / rows + 5,
                           w / cols - 10, (h - hh) / rows - 10, 7,
                           fill=accent, stroke=None, op=.22))
    for i in range(1, cols):
        parts.append(seg(x + w * i / cols, y + hh, x + w * i / cols, y + h - 3, SOFT, 4))
    start = 0 if header else 1
    for j in range(start, rows):
        yy = y + hh + j * (h - hh) / rows
        parts.append(seg(x + 3, yy, x + w - 3, yy, SOFT, 4))
    return "\n".join(parts)


def folder(x, y, w, h, accent, sw=STK):
    d = (f"M {fmt(x)} {fmt(y + h - 10)} V {fmt(y + 10)} Q {fmt(x)} {fmt(y)} "
         f"{fmt(x + 10)} {fmt(y)} H {fmt(x + w * .36)} L {fmt(x + w * .46)} "
         f"{fmt(y + 16)} H {fmt(x + w - 10)} Q {fmt(x + w)} {fmt(y + 16)} {fmt(x + w)} "
         f"{fmt(y + 26)} V {fmt(y + h - 10)} Q {fmt(x + w)} {fmt(y + h)} "
         f"{fmt(x + w - 10)} {fmt(y + h)} H {fmt(x + 10)} Q {fmt(x)} {fmt(y + h)} "
         f"{fmt(x)} {fmt(y + h - 10)} Z")
    return path(d, sw, INK, fill=WHITE)


def globe(cx, cy, r, accent, sw=STK):
    parts = [circle(cx, cy, r, WHITE, INK, sw)]
    parts.append(f'<ellipse cx="{fmt(cx)}" cy="{fmt(cy)}" rx="{fmt(r * .45)}" '
                 f'ry="{fmt(r)}" fill="none" stroke="{SOFT}" stroke-width="4.5"/>')
    parts.append(seg(cx - r, cy, cx + r, cy, SOFT, 4.5))
    parts.append(circle(cx + r * .38, cy - r * .34, r * .16, accent))
    return "\n".join(parts)


def gear(cx, cy, r, color, sw=6):
    parts = []
    for i in range(8):
        a = math.radians(i * 45)
        parts.append(seg(cx + math.cos(a) * r * .78, cy + math.sin(a) * r * .78,
                         cx + math.cos(a) * (r + 4), cy + math.sin(a) * (r + 4),
                         color, sw + 3))
    parts.append(circle(cx, cy, r * .78, WHITE, color, sw))
    parts.append(circle(cx, cy, r * .3, "none", color, sw))
    return "\n".join(parts)


def mountain_photo(x, y, w, h, accent, r=12, sw=STK, sun=True):
    parts = [rrect(x, y, w, h, r, sw=sw)]
    d = (f"M {fmt(x + w * .08)} {fmt(y + h * .82)} L {fmt(x + w * .36)} {fmt(y + h * .38)} "
         f"L {fmt(x + w * .55)} {fmt(y + h * .62)} L {fmt(x + w * .72)} {fmt(y + h * .42)} "
         f"L {fmt(x + w * .92)} {fmt(y + h * .82)}")
    parts.append(path(d, 6, INK))
    if sun:
        parts.append(circle(x + w * .72, y + h * .26, min(w, h) * .1, accent))
    return "\n".join(parts)


def group(rot, cx, cy, *parts):
    return (f'<g transform="rotate({rot} {fmt(cx)} {fmt(cy)})">'
            + "\n".join(parts) + "</g>")


# ── scenes ───────────────────────────────────────────────────────────────
# Each scene fills the 480x360 canvas with one bold focal composition.

def s_acadreason(a, b):
    return [
        halo(230, 180, 200, 150, a),
        group(-7, 130, 170, doc(58, 82, 148, 190, lines=((44, .16, .8), (72, .16, .68),
                                                         (100, .16, .76), (128, .16, .6)))),
        doc(112, 92, 148, 190, lines=((46, .16, .8), (74, .16, .66), (102, .16, .78),
                                      (130, .16, .58), (158, .16, .7))),
        circle(352, 82, 12, b), circle(408, 128, 9, a), circle(378, 60, 7, SOFT),
        seg(352, 82, 320, 118, SOFT, 4.5), seg(408, 128, 348, 152, SOFT, 4.5),
        loupe(300, 190, 66),
        path("M 268 176 L 296 176 M 268 200 L 310 200 M 268 224 L 288 224", 7, a),
        check(392, 268),
    ]


def s_artifactsbench(a, b):
    return [
        halo(250, 180, 210, 150, a),
        rrect(64, 62, 190, 150, 16, fill=INK, stroke=None),
        tline(88, 100, 90, 7, "#8CA0B8"), tline(88, 128, 130, 7, "#5E7490"),
        tline(88, 156, 70, 7, a), tline(88, 184, 108, 7, "#5E7490"),
        window(150, 112, 250, 186),
        rrect(180, 190, 30, 78, 8, fill=a, stroke=None),
        rrect(224, 214, 30, 54, 8, fill=b, stroke=None),
        rrect(268, 172, 30, 96, 8, fill=a, stroke=None, op=.55),
        seg(176, 272, 372, 272, SOFT, 5),
        cursor(322, 226, 1.15),
        check(404, 96),
    ]


def s_autokaggle(a, b):
    return [
        halo(240, 185, 205, 152, a),
        tablegrid(52, 62, 158, 124, 3, 3, a),
        arrow(216, 122, 254, 134, -12, a, 8),
        chip(304, 130, 104, a),
        arrow(304, 190, 304, 218, 0, a, 8),
        doc(248, 222, 110, 106, fold=22, lines=((36, .18, .76), (58, .18, .6),
                                                (80, .18, .7))),
        circle(394, 280, 33, WHITE, AMBER, 7),
        path("M 376 253 L 366 222 M 412 253 L 422 222", 8, AMBER),
        text(394, 291, "1", 29, AMBER),
    ]


def s_automv(a, b):
    return [
        halo(230, 180, 210, 150, b),
        wave(128, 180, 150, 9, (a, b), seed=2, hmin=22, hmax=118, bw=11),
        arrow(214, 132, 252, 112, 12, b, 7),
        arrow(214, 228, 252, 248, -12, b, 7),
        film(252, 74, 180, 96, a, play=False),
        film(252, 190, 180, 96, b, play=True),
    ]


def s_chinese_safetyqa(a, b):
    return [
        halo(240, 185, 190, 160, a),
        shield(240, 180, 118, fill=WHITE),
        zh(240, 168, 52, a, 11),
        arrow(64, 110, 132, 142, 16, SOFT, 6, dash="2 14"),
        arrow(64, 260, 132, 230, -16, SOFT, 6, dash="2 14"),
        check(322, 274),
    ]


def s_chinese_simpleqa(a, b):
    return [
        halo(220, 170, 200, 150, a),
        bubble(62, 70, 208, 128, tail="bl"),
        zh(128, 134, 40, INK, 9),
        text(206, 152, "?", 54, a),
        arrow(232, 236, 296, 236, -26, a, 8),
        doc(228, 258, 76, 76, fold=18, lines=((28, .2, .74), (48, .2, .58))),
        bubble(306, 176, 132, 84, tail="br", fill="#E7EEFB", stroke=a),
        tline(330, 210, 76, 8, a),
        tline(330, 232, 52, 8, a),
        check(424, 286),
    ]


def s_cii_bench(a, b):
    return [
        halo(220, 190, 205, 150, a),
        mountain_photo(58, 108, 196, 152, a),
        circle(292, 96, 7, SOFT), circle(316, 74, 10, SOFT),
        bubble(268, 52, 168, 120, r=34, tail=None),
        heart(330, 104, 26, b),
        text(388, 126, "?", 46, a),
        tline(96, 292, 120, 8, SOFT),
    ]


def s_code_simpleqa(a, b):
    return [
        halo(230, 172, 205, 150, a),
        window(64, 58, 260, 200),
        text(148, 192, "{", 78, SOFT, font=MONO),
        text(194, 188, "?", 64, a, font=MONO),
        text(240, 192, "}", 78, SOFT, font=MONO),
        rrect(238, 236, 78, 46, 12, fill=WHITE),
        text(277, 267, "EN", 25, INK, font=MONO),
        rrect(328, 236, 78, 46, 12, fill=a, stroke=None),
        zh(367, 259, 16, WHITE, 6),
        check(396, 92),
    ]


def s_codeeditorbench(a, b):
    return [
        halo(230, 180, 210, 150, a),
        window(56, 58, 302, 226),
        seg(207, 110, 207, 262, SOFT, 4),
        tline(84, 128, 96), tline(84, 158, 74), tline(84, 188, 88), tline(84, 218, 60),
        tline(236, 128, 92), tline(236, 158, 70, 7, GREEN), tline(236, 188, 84),
        tline(236, 218, 78, 7, GREEN),
        rrect(189, 138, 36, 36, 10, fill=RED, stroke=None),
        seg(198, 156, 216, 156, "#fff", 6.5),
        rrect(189, 196, 36, 36, 10, fill=GREEN, stroke=None),
        seg(198, 214, 216, 214, "#fff", 6.5),
        seg(207, 205, 207, 223, "#fff", 6.5),
        check(400, 250),
    ]


def s_codetracer(a, b):
    pts = [(112, 226), (172, 226), (172, 168), (238, 168), (238, 214), (304, 214)]
    d = "M " + " L ".join(f"{x} {y}" for x, y in pts)
    return [
        halo(230, 180, 210, 150, a),
        window(56, 58, 300, 224),
        path(d, 6, SOFT),
        circle(112, 226, 12, WHITE, a, 6), circle(172, 168, 12, WHITE, a, 6),
        circle(238, 214, 12, WHITE, a, 6),
        circle(304, 214, 15, "#FBE3E3", RED, 6),
        circle(304, 214, 34, "none", RED, 5, dash="4 10"),
        loupe(330, 246, 52),
        cross(304, 214, 15, ring=False),
    ]


def s_conceptmath(a, b):
    link = lambda x1, y1, x2, y2: path(f"M {x1} {y1} V {(y1 + y2) / 2} "
                                       f"H {x2} V {y2}", 6, SOFT)
    return [
        halo(240, 180, 200, 150, a),
        link(240, 118, 138, 196), link(240, 118, 342, 196),
        link(138, 244, 90, 288), link(138, 244, 194, 288),
        link(342, 244, 294, 288), link(342, 244, 390, 288),
        rrect(186, 56, 108, 62, 16),
        text(240, 100, "x²", 32, a, font=MONO),
        rrect(96, 196, 84, 48, 14), rrect(300, 196, 84, 48, 14),
        tline(118, 220, 40), tline(322, 220, 40),
        circle(90, 296, 17, WHITE, INK, 6), circle(194, 296, 17, WHITE, INK, 6),
        circle(294, 296, 17, WHITE, INK, 6),
        circle(390, 296, 20, "#FBE3E3", RED, 6),
        circle(390, 296, 34, "none", RED, 5, dash="4 10"),
    ]


def s_cot_error_detection(a, b):
    xs = [58, 128, 198, 268, 338, 408]
    ys = [128, 96, 128, 100, 132, 104]
    parts = [halo(240, 170, 210, 150, a)]
    for (x1, y1), (x2, y2) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        parts.append(seg(x1, y1, x2, y2, SOFT, 6))
    for i, (x, y) in enumerate(zip(xs, ys)):
        if i == 3:
            continue
        parts.append(circle(x, y, 15, WHITE, a, 6.5))
    parts.append(path("M 58 128 C 58 240 180 250 240 250", 6, SOFT, dash="1 14"))
    parts.append(cross(268, 100, 17))
    parts.append(loupe(268, 178, 58))
    parts.append(seg(246, 168, 262, 168, RED, 7))
    parts.append(seg(246, 192, 290, 192, TLINE, 7))
    return parts


def s_criticlean(a, b):
    return [
        halo(220, 180, 200, 150, a),
        doc(64, 56, 190, 244, lines=((92, .16, .78), (126, .16, .62), (194, .16, .7),
                                     (228, .16, .5))),
        turnstile(126, 108, 22, a),
        path("M 94 216 q 10 -9 20 0 q 10 9 20 0 q 10 -9 20 0 q 10 9 20 0", 6, RED),
        loupe(310, 152, 58),
        bang(310, 152, 17, RED, ring=False),
        arrow(300, 222, 268, 250, -18, b, 7),
        check(392, 268),
    ]


def s_dr3_eval(a, b):
    return [
        halo(240, 190, 205, 150, a),
        rrect(76, 96, 74, 56, 12), path("M 90 138 L 106 116 L 120 130 L 132 112", 5.5, a),
        wave(113, 208, 72, 5, (b,), seed=1, hmin=12, hmax=40, bw=8),
        arrow(158, 130, 186, 154, -10, SOFT, 6),
        arrow(158, 210, 186, 192, 10, SOFT, 6),
        rrect(176, 108, 148, 148, 18),
        path("M 216 108 V 88 C 216 62 264 62 264 88 V 108", 8, INK),
        rrect(226, 158, 28, 34, 8, fill=a, stroke=None),
        circle(240, 170, 5, WHITE),
        arrow(330, 182, 358, 182, 0, a, 8),
        doc(356, 96, 108, 168, fold=24, lines=((44, .18, .76), (72, .18, .6),
                                               (128, .18, .7))),
        rrect(376, 190, 14, 14, 4, fill=b, stroke=None),
        rrect(430, 134, 14, 14, 4, fill=b, stroke=None),
        check(444, 286, 25),
    ]


def s_edgebench(a, b):
    steps = "M 96 268 H 152 V 232 H 208 V 244 H 260 V 186 H 316 V 196 H 368 V 128 H 414"
    return [
        halo(250, 190, 205, 150, a),
        seg(72, 66, 72, 292, SOFT, 5), seg(72, 292, 428, 292, SOFT, 5),
        path(steps, 9, a),
        circle(414, 128, 11, b),
        seg(152, 292, 152, 300, SOFT, 4.5), seg(260, 292, 260, 300, SOFT, 4.5),
        seg(368, 292, 368, 300, SOFT, 4.5),
        clockface(128, 108, 40),
    ]


def s_finder(a, b):
    return [
        halo(220, 185, 205, 150, a),
        seg(226, 128, 296, 96, SOFT, 5), seg(238, 170, 300, 170, SOFT, 5),
        loupe(160, 172, 78),
        text(160, 196, "?", 64, a),
        group(6, 344, 96, doc(300, 56, 90, 82, fold=20, lines=((30, .2, .72),
                                                               (52, .2, .56)))),
        doc(312, 130, 118, 168, fold=26, lines=()),
        rrect(332, 168, 13, 13, 4, fill=a, stroke=None), tline(356, 175, 52),
        rrect(332, 200, 13, 13, 4, fill=a, stroke=None), tline(356, 207, 40),
        rrect(332, 232, 13, 13, 4, fill=a, stroke=None), tline(356, 239, 48),
        check(424, 292, 25),
    ]


def s_formalmath(a, b):
    return [
        halo(230, 180, 200, 155, a),
        turnstile(118, 150, 84, INK, 17),
        seg(268, 96, 332, 132, SOFT, 6), seg(396, 96, 332, 132, SOFT, 6),
        seg(332, 132, 332, 196, SOFT, 6),
        circle(268, 90, 20, WHITE, a, 6.5), circle(396, 90, 20, WHITE, a, 6.5),
        circle(332, 138, 20, WHITE, a, 6.5),
        text(268, 99, "1", 22, a), text(396, 99, "2", 22, a),
        text(332, 147, "3", 22, a),
        check(332, 234, 34),
        tline(96, 282, 130, 8, SOFT),
        tline(96, 306, 86, 8, SOFT),
    ]


def s_fullstack_bench(a, b):
    return [
        halo(240, 180, 205, 155, a),
        path("M 152 202 C 152 240 176 252 210 252", 7, SOFT),
        path("M 330 252 C 364 252 388 240 388 216", 7, SOFT),
        window(56, 56, 192, 146, bar=30),
        tline(80, 116, 90), tline(80, 144, 120), tline(80, 172, 70),
        rrect(210, 224, 120, 56, 16, fill=a, stroke=a),
        rrect(210, 224, 120, 56, 16, fill="none", stroke=a),
        text(270, 260, "API", 26, WHITE, font=MONO),
        cyl(388, 130, 92, 96, b),
        path("M 248 128 H 342", 7, SOFT),
        check(420, 280),
    ]


def s_hellobench(a, b):
    lines = [(50 + i * 27, .17, .8 - (i % 3) * .1) for i in range(9)]
    return [
        halo(240, 180, 195, 155, a),
        doc(152, 42, 180, 276, fold=30, lines=lines),
        path("M 178 66 C 260 96 200 150 246 190 C 286 226 232 258 264 292",
             8, a, op=.85),
        circle(178, 66, 9, a), circle(264, 292, 9, a),
        path("M 352 116 C 396 130 396 200 352 216", 5.5, b, dash="4 10"),
        seg(340, 108, 358, 124, b, 5.5), seg(358, 108, 340, 124, b, 5.5),
    ]


def s_if_vidcap(a, b):
    return [
        halo(230, 175, 205, 150, a),
        film(66, 58, 268, 138, a),
        rrect(88, 232, 250, 64, 16, fill="#E7EEFB", stroke=a),
        tline(112, 256, 150, 8, a), tline(112, 278, 106, 8, a),
        rrect(356, 92, 58, 58, 14),
        rrect(370, 106, 13, 13, 4, fill=b, stroke=None),
        rrect(370, 128, 13, 13, 4, fill=b, stroke=None),
        seg(390, 112, 402, 112, TLINE, 5), seg(390, 134, 402, 134, TLINE, 5),
        check(384, 264),
    ]


def s_ii_bench(a, b):
    return [
        mountain_photo(158, 52, 164, 118, a, sun=True),
        seg(48, 196, 432, 196, INK, 6, dash="14 14"),
        path("M 118 196 L 240 330 L 362 196 Z", 6.5, a, fill=a, op=.14),
        path("M 118 196 L 240 330 L 362 196", 6.5, a),
        text(240, 268, "?", 56, a),
    ]


def s_inverse_ifeval(a, b):
    return [
        halo(240, 185, 210, 150, a),
        path("M 52 232 H 420", 9, SOFT, dash="16 16"),
        cross(424, 232, 17, color="#B7C3D4", ring=True),
        path("M 52 232 C 150 232 170 226 218 186 C 262 150 300 120 372 108",
             10, a),
        arrow(372, 108, 396, 102, 0, a, 10),
        doc(168, 92, 96, 84, fold=20, lines=((32, .2, .72), (54, .2, .5))),
        bang(184, 106, 15, b, ring=True),
        check(430, 92),
    ]


def s_iv_bench(a, b):
    return [
        halo(240, 180, 210, 150, a),
        film(170, 128, 246, 112, a, play=False),
        circle(375, 184, 28, "none", b, 6, dash="5 10"),
        group(-8, 122, 160,
              rrect(58, 84, 128, 152, 10),
              path("M 74 178 L 106 134 L 130 158 L 148 128 L 170 178", 6, INK),
              circle(150, 118, 10, a),
              seg(74, 206, 140, 206, TLINE, 8)),
        path("M 148 246 C 220 296 316 268 362 214", 6.5, b, dash="2 12"),
        arrow(362, 214, 366, 208, 0, b, 6.5),
    ]


def s_kor_bench(a, b):
    return [
        halo(230, 180, 205, 150, a),
        rrect(58, 54, 168, 118, 18),
        path("M 92 100 L 110 76 L 128 100 Z", 6, a),
        path("M 152 88 H 190", 6, INK), path("M 178 76 L 192 88 L 178 100", 6, INK),
        rrect(92, 122, 36, 26, 7, fill=b, stroke=None, op=.8),
        circle(160, 135, 13, "none", b, 6),
        seg(226, 132, 280, 158, SOFT, 6),
        circle(294, 166, 16, WHITE, a, 6.5),
        seg(310, 174, 344, 196, SOFT, 6),
        circle(358, 204, 16, WHITE, a, 6.5),
        seg(360, 220, 340, 258, SOFT, 6),
        rrect(288, 258, 84, 56, 14, fill=a, stroke=a),
        text(330, 296, "A", 30, WHITE),
    ]


def s_korgym(a, b):
    return [
        halo(235, 182, 205, 152, a),
        tablegrid(58, 70, 180, 180, 3, 3, a, header=False),
        circle(88, 160, 15, a),
        circle(148, 220, 15, a),
        rrect(193, 85, 30, 30, 7, fill=b, stroke=None),
        arrow(258, 112, 324, 128, -26, a, 9),
        arrow(340, 240, 274, 226, -26, b, 9),
        chip(366, 180, 108, a),
    ]


def s_lime(a, b):
    dots = [(168, 60), (212, 44), (258, 62), (302, 46), (196, 88), (250, 92),
            (296, 86), (338, 66), (146, 92)]
    parts = [halo(240, 185, 195, 155, a)]
    for i, (x, y) in enumerate(dots):
        parts.append(circle(x, y, 10, a if i % 3 else SOFT))
    parts.append(funnel(240, 178, 236, 152))
    parts.append(seg(180, 122, 300, 122, SOFT, 5))
    parts.append(circle(240, 286, 10, a)), parts.append(circle(212, 306, 10, a))
    parts.append(circle(268, 306, 10, a))
    parts.append(rrect(184, 322, 112, 14, 7, fill=SOFT, stroke=None))
    parts.append(cross(376, 130, 15, color="#B7C3D4"))
    parts.append(circle(376, 96, 10, SOFT))
    return parts


def s_longform_rewardbench(a, b):
    return [
        halo(240, 180, 200, 155, a),
        seg(240, 84, 240, 296, INK, 9),
        path("M 168 312 H 312", 9, INK),
        group(-8, 240, 96,
              seg(112, 96, 368, 96, INK, 9),
              seg(112, 96, 112, 128, SOFT, 6), seg(368, 96, 368, 128, SOFT, 6),
              path("M 68 128 H 156 L 142 168 H 82 Z", 6, INK, fill=WHITE),
              path("M 324 128 H 412 L 398 168 H 338 Z", 6, INK, fill=WHITE),
              doc(76, 60, 72, 92, fold=16, lines=((28, .2, .72), (46, .2, .56),
                                                  (64, .2, .66))),
              doc(332, 76, 72, 76, fold=16, lines=((26, .2, .7), (44, .2, .52)))),
        circle(240, 96, 15, a),
        text(112, 232, "A", 30, a), text(368, 218, "B", 30, TLINE),
    ]


def s_m2rc_eval(a, b):
    return [
        halo(230, 180, 210, 152, a),
        window(56, 56, 252, 214),
        tline(84, 122, 120), tline(84, 152, 84),
        rrect(84, 176, 152, 46, 12, fill="none", stroke=SOFT, sw=5, dash="6 10"),
        tline(84, 246, 96),
        rrect(322, 148, 116, 60, 12, fill="#E7EEFB", stroke=a),
        tline(344, 170, 60, 7, a), tline(344, 190, 42, 7, a),
        arrow(318, 210, 250, 202, 20, a, 8),
        check(404, 92),
    ]


def s_mammoth2(a, b):
    return [
        halo(250, 190, 205, 155, a),
        group(-6, 108, 96, doc(52, 52, 116, 88, fold=20, lines=((30, .18, .74),
                                                                (52, .18, .58)))),
        doc(96, 82, 116, 88, fold=20, lines=((30, .18, .74), (52, .18, .58))),
        funnel(240, 178, 190, 140),
        circle(214, 130, 8, a), circle(252, 118, 8, b), circle(282, 136, 8, a),
        arrow(240, 252, 240, 282, 0, a, 8),
        rrect(300, 218, 132, 84, 14),
        rrect(288, 236, 132, 84, 14),
        tline(310, 272, 76, 8), tline(310, 296, 56, 8),
        text(374, 166, "10M", 52, b),
    ]


def s_mceval(a, b):
    parts = [halo(240, 180, 195, 160, a)]
    for i in range(8):
        ang = math.radians(i * 45 - 90)
        x, y = 240 + math.cos(ang) * 122, 180 + math.sin(ang) * 112
        parts.append(seg(240 + math.cos(ang) * 62, 180 + math.sin(ang) * 58,
                         x - math.cos(ang) * 20, y - math.sin(ang) * 20, SOFT, 5))
        parts.append(circle(x, y, 17, WHITE, (a, b)[i % 2], 6))
    parts.append(rrect(178, 122, 124, 116, 24))
    parts.append(text(240, 196, "</>", 40, a, font=MONO))
    parts.append(rrect(322, 250, 64, 42, 21, fill=b, stroke=None))
    parts.append(text(354, 279, "40", 26, WHITE))
    return parts


def s_mm_browsecomp(a, b):
    return [
        halo(230, 180, 210, 150, a),
        window(54, 54, 288, 226),
        rrect(80, 116, 108, 78, 10), path("M 94 178 L 122 140 L 144 162 L 158 144 "
                                          "L 172 178", 5.5, INK),
        circle(158, 134, 8, a),
        rrect(206, 116, 112, 78, 10),
        path("M 248 138 L 284 155 L 248 172 Z", 5, b, fill=b),
        tline(82, 226, 160), tline(82, 252, 118),
        loupe(322, 226, 62),
        check(408, 82),
    ]


def s_mt_bench_101(a, b):
    return [
        halo(230, 180, 205, 155, a),
        bubble(58, 52, 164, 66, tail="bl"),
        tline(84, 86, 96),
        bubble(120, 148, 178, 66, tail="bl", fill="#E7EEFB", stroke=a),
        tline(146, 182, 108, 7, a),
        bubble(184, 246, 190, 66, tail="bl"),
        tline(210, 280, 120),
        rrect(354, 84, 82, 108, 14),
        rrect(370, 102, 12, 12, 4, fill=a, stroke=None), tline(392, 108, 28),
        rrect(370, 130, 12, 12, 4, fill=a, stroke=None), tline(392, 136, 22),
        rrect(370, 158, 12, 12, 4, fill=SOFT, stroke=None), tline(392, 164, 26),
        check(408, 268),
    ]


def s_mt_video_bench(a, b):
    return [
        halo(240, 175, 210, 150, a),
        film(64, 52, 300, 120, a, play=False),
        circle(114, 112, 17, "none", b, 6), circle(214, 112, 17, "none", b, 6),
        circle(314, 112, 17, "none", b, 6),
        path("M 114 172 V 216", 5.5, b, dash="2 10"),
        path("M 214 172 V 232", 5.5, b, dash="2 10"),
        path("M 314 172 V 216", 5.5, b, dash="2 10"),
        bubble(58, 220, 122, 58, tail=None), tline(80, 250, 78),
        bubble(178, 236, 122, 58, tail=None, fill="#E7EEFB", stroke=a),
        tline(200, 266, 78, 7, a),
        bubble(298, 220, 122, 58, tail=None), tline(320, 250, 78),
    ]


def s_mtu_bench(a, b):
    return [
        halo(240, 180, 205, 155, a),
        seg(176, 140, 126, 104, SOFT, 7), seg(306, 140, 354, 104, SOFT, 7),
        seg(176, 222, 126, 258, SOFT, 7, dash="7 11"),
        seg(306, 222, 354, 258, SOFT, 7, dash="7 11"),
        bubble(158, 132, 164, 96, r=22, tail="bl"),
        tline(184, 168, 112, 8), tline(184, 192, 76, 8),
        gear(106, 86, 28, a),
        globe(376, 86, 33, b),
        cyl(106, 278, 66, 58, a),
        rrect(338, 250, 80, 58, 12, fill=INK, stroke=None),
        text(364, 288, "$", 26, "#7EE7B8", font=MONO),
        seg(382, 284, 402, 284, "#8CA0B8", 5),
    ]


def s_multi_docker_eval(a, b):
    box = lambda x, y: [rrect(x, y, 128, 64, 12),
                        circle(x + 24, y + 32, 8, GREEN),
                        tline(x + 44, y + 24, 60, 6), tline(x + 44, y + 44, 40, 6)]
    return [
        halo(250, 180, 205, 155, a),
        doc(54, 74, 122, 180, fold=24, lines=((44, .18, .7), (72, .18, .56),
                                              (100, .18, .66), (128, .18, .5))),
        text(115, 240, "yml", 24, a, font=MONO),
        seg(176, 130, 226, 108, SOFT, 6), seg(176, 180, 226, 180, SOFT, 6),
        seg(176, 230, 226, 252, SOFT, 6),
        seg(290, 140, 290, 168, a, 6), seg(290, 232, 290, 260, a, 6),
        *box(226, 76), *box(258, 168), *box(226, 260),
        check(420, 96),
    ]


def s_mvu_eval(a, b):
    return [
        halo(230, 180, 210, 150, a),
        film(54, 56, 204, 100, a, play=False),
        film(54, 204, 204, 100, b, play=False),
        path("M 262 106 C 308 106 314 156 338 170", 7, a),
        path("M 262 254 C 308 254 314 204 338 190", 7, b),
        loupe(352, 178, 52),
        bubble(368, 252, 100, 56, tail=None, fill="#E7EEFB", stroke=a),
        tline(388, 281, 60, 7, a),
    ]


def s_nl2repo_bench(a, b):
    tag = lambda x, y, c: [rrect(x, y, 118, 42, 10, fill=WHITE),
                           rrect(x + 12, y + 12, 18, 18, 5, fill=c, stroke=None),
                           tline(x + 44, y + 21, 56, 7)]
    return [
        halo(240, 185, 210, 150, a),
        doc(54, 62, 138, 200, fold=26, lines=((52, .18, .76), (80, .18, .6),
                                              (108, .18, .7), (136, .18, .52))),
        tline(79, 90, 62, 9, a),
        arrow(200, 162, 240, 162, 0, a, 8),
        folder(248, 78, 182, 208, a),
        *tag(272, 118, a), *tag(272, 172, b), *tag(272, 226, GREEN),
        check(416, 286),
    ]


def s_omni_math(a, b):
    return [
        halo(220, 190, 200, 155, a),
        path("M 170 84 L 66 282 H 274 Z", 8, a),
        seg(170, 84, 170, 282, SOFT, 5, dash="8 10"),
        circle(170, 84, 11, a), circle(66, 282, 11, a), circle(274, 282, 11, a),
        text(342, 186, "∑", 88, b),
        circle(384, 268, 34, WHITE, AMBER, 7),
        path("M 366 240 L 356 208 M 402 240 L 412 208", 8, AMBER),
        text(384, 280, "1", 30, AMBER),
    ]


def s_omnibench(a, b):
    src = lambda y, inner: [rrect(64, y, 96, 68, 14)] + inner
    return [
        halo(260, 180, 200, 155, a),
        path("M 160 96 C 220 96 220 150 258 162", 6, SOFT),
        path("M 160 180 H 250", 6, SOFT),
        path("M 160 264 C 220 264 220 210 258 198", 6, SOFT),
        *src(62, [text(112, 108, "Tt", 30, a)]),
        *src(146, [path("M 78 196 L 98 168 L 114 184 L 126 170 L 144 196", 5.5, INK),
                   circle(128, 164, 6, a)]),
        *src(230, [wave(112, 264, 64, 5, (b,), seed=3, hmin=12, hmax=40, bw=7)]),
        chip(310, 180, 112, a),
        arrow(374, 180, 404, 180, 0, a, 8),
        bubble(388, 146, 76, 52, tail=None, fill="#E7EEFB", stroke=a),
        tline(404, 172, 44, 7, a),
    ]


def s_omnicap_if(a, b):
    return [
        halo(230, 180, 210, 150, a),
        film(58, 54, 204, 104, a),
        wave(160, 208, 200, 11, (a, b), seed=4, hmin=12, hmax=46, bw=8),
        rrect(300, 62, 130, 96, 16),
        rrect(318, 82, 13, 13, 4, fill=b, stroke=None), tline(342, 88, 60),
        rrect(318, 110, 13, 13, 4, fill=b, stroke=None), tline(342, 116, 46),
        arrow(240, 252, 240, 252, 0, a, 0),
        rrect(96, 252, 288, 60, 16, fill="#E7EEFB", stroke=a),
        tline(122, 274, 180, 8, a), tline(122, 296, 130, 8, a),
        check(384, 282),
    ]


def s_omnivideobench(a, b):
    parts = [
        halo(240, 180, 210, 150, a),
        film(62, 58, 286, 112, a, play=False),
        wave(205, 248, 286, 15, (a, b), seed=5, hmin=14, hmax=64, bw=9),
    ]
    for x in (120, 205, 290):
        parts.append(seg(x, 174, x, 212, SOFT, 5, dash="2 10"))
    parts.append(bubble(366, 92, 76, 54, tail=None, fill="#E7EEFB", stroke=a))
    parts.append(text(404, 128, "?", 32, a))
    return parts


def s_opencodeinterpreter(a, b):
    return [
        halo(230, 180, 210, 155, a),
        window(56, 54, 250, 208, fill=INK, dots=True),
        text(82, 128, "$", 26, "#7EE7B8", font=MONO, anchor="start"),
        tline(112, 120, 96, 7, "#8CA0B8"),
        tline(82, 158, 130, 7, "#5E7490"),
        tline(82, 218, 100, 7, "#F49E9E"),
        tline(82, 246, 130, 7, "#7EE7B8"),
        path("M 336 128 C 402 142 414 234 348 262 C 296 284 250 254 246 216",
             10, a),
        arrow(246, 216, 244, 196, 0, a, 10),
        check(404, 82),
    ]


def s_opencoder(a, b):
    return [
        halo(240, 180, 210, 155, a),
        path("M 44 96 C 120 96 130 152 172 166", 9, a, op=.85),
        path("M 44 180 H 168", 9, b, op=.85),
        path("M 44 264 C 120 264 130 208 172 194", 9, a, op=.55),
        chip(232, 180, 118, a),
        seg(296, 148, 336, 128, SOFT, 6), seg(296, 212, 336, 232, SOFT, 6),
        rrect(336, 96, 96, 64, 14), text(384, 138, "7B", 28, INK, font=MONO),
        rrect(336, 200, 96, 64, 14), text(384, 242, "8B", 28, INK, font=MONO),
        check(430, 262, 23),
    ]


def s_oprover(a, b):
    return [
        halo(240, 180, 200, 155, a),
        arrow(306, 106, 366, 168, -34, a, 8),
        arrow(326, 268, 180, 272, -44, b, 8),
        arrow(112, 194, 182, 98, -40, a, 8),
        doc(196, 44, 96, 92, fold=20, lines=((64, .2, .72),)),
        turnstile(240, 78, 17, a, 7.5),
        chip(378, 218, 100, a),
        circle(124, 244, 44, WHITE, INK, 7),
        path("M 104 244 L 118 259 L 146 226", 9, GREEN),
    ]


def s_ouro(a, b):
    parts = [halo(240, 180, 195, 160, a)]
    parts.append(path("M 240 68 A 112 112 0 1 0 352 180", 9, a))
    parts.append(arrow(352, 180, 352, 162, 0, a, 9))
    for i in range(6):
        ang = math.radians(i * 60 - 90)
        x, y = 240 + math.cos(ang) * 112, 180 + math.sin(ang) * 112
        parts.append(rrect(x - 30, y - 19, 60, 38, 12, fill=WHITE, sw=6))
        parts.append(seg(x - 12, y, x + 12, y, a, 6))
    parts.append(circle(240, 180, 50, WHITE, INK, 7))
    parts.append(text(240, 194, "t", 44, b, font=MONO))
    parts.append(rrect(348, 282, 66, 40, 20, fill=b, stroke=None))
    parts.append(text(381, 309, "×N", 24, WHITE, font=MONO))
    return parts


def s_owl(a, b):
    rack = lambda y, on: [rrect(64, y, 158, 48, 10),
                          circle(88, y + 24, 7, GREEN if on else SOFT),
                          tline(108, y + 24, 84, 6)]
    return [
        halo(240, 185, 205, 155, a),
        *rack(64, True), *rack(122, False), *rack(180, True),
        bang(222, 146, 22, RED),
        arrow(230, 234, 260, 250, -12, a, 7),
        doc(262, 96, 122, 180, fold=24, lines=()),
        circle(288, 140, 11, "none", a, 5), tline(310, 140, 48),
        circle(288, 180, 11, "none", a, 5), tline(310, 180, 40),
        circle(288, 220, 11, "none", a, 5), tline(310, 220, 46),
        check(414, 276),
    ]


def s_roleagent(a, b):
    return [
        halo(240, 180, 210, 150, a),
        doc(52, 68, 122, 176, fold=24, lines=((48, .18, .74), (76, .18, .58),
                                              (104, .18, .68), (132, .18, .5))),
        tline(74, 96, 56, 9, a),
        arrow(180, 156, 208, 156, 0, SOFT, 7),
        mask(262, 158, 74, "#E7EEFB", mood="smile", rot=-4),
        arrow(322, 132, 352, 118, 10, SOFT, 7),
        bubble(342, 130, 104, 62, tail="bl", fill=WHITE),
        tline(362, 156, 62, 7),
        tline(362, 174, 44, 7),
        check(400, 274),
    ]


def s_rolellm(a, b):
    return [
        halo(220, 180, 205, 155, a),
        mask(196, 172, 92, WHITE, mood="frown", rot=8),
        mask(148, 178, 92, "#E7EEFB", mood="smile", rot=-8),
        bubble(300, 96, 138, 78, tail="bl", fill=WHITE),
        tline(322, 128, 86, 7), tline(322, 148, 62, 7),
        rrect(300, 226, 62, 46, 12), text(331, 258, "Aa", 24, a),
        rrect(374, 226, 62, 46, 12),
        seg(390, 242, 422, 242, b, 6), seg(390, 256, 414, 256, b, 6),
    ]


def s_safedialbench(a, b):
    return [
        halo(270, 180, 195, 160, a),
        bubble(46, 76, 108, 56, tail=None),
        bang(72, 104, 13, RED, ring=False),
        tline(96, 104, 38, 7),
        bubble(46, 226, 108, 56, tail=None),
        bang(72, 254, 13, RED, ring=False),
        tline(96, 254, 38, 7),
        path("M 158 104 C 196 104 214 118 228 134", 6.5, RED),
        path("M 228 134 C 224 118 216 104 200 88", 6.5, RED, dash="3 10"),
        path("M 158 254 C 196 254 214 240 228 224", 6.5, RED),
        path("M 228 224 C 224 240 216 254 200 270", 6.5, RED, dash="3 10"),
        shield(300, 180, 112, fill=WHITE),
        path("M 262 180 L 288 208 L 340 148", 10, GREEN),
    ]


def s_scalelong(a, b):
    return [
        halo(230, 185, 210, 150, a),
        film(64, 56, 118, 74, a, play=False),
        film(64, 148, 208, 74, a, play=False),
        film(64, 240, 310, 74, b, play=False),
        circle(322, 277, 24, "none", b, 6, dash="4 9"),
        clockface(404, 108, 44),
    ]


def s_supergpqa(a, b):
    parts = [halo(240, 180, 200, 160, a)]
    for i in range(8):
        ang = math.radians(i * 45 - 90)
        x, y = 240 + math.cos(ang) * 128, 180 + math.sin(ang) * 116
        parts.append(seg(240 + math.cos(ang) * 70, 180 + math.sin(ang) * 64,
                         x - math.cos(ang) * 26, y - math.sin(ang) * 24, SOFT, 5))
        parts.append(rrect(x - 30, y - 21, 60, 42, 13, fill=WHITE,
                           stroke=(a, b)[i % 2], sw=6))
        parts.append(tline(x - 14, y, 28, 6))
    parts.append(rrect(172, 116, 136, 128, 26))
    parts.append(text(240, 208, "?", 66, a))
    return parts


def s_swe_compass(a, b):
    parts = [halo(240, 182, 195, 160, a)]
    parts.append(circle(240, 182, 120, WHITE, INK, 8))
    parts.append(circle(240, 182, 97, "none", SOFT, 4.5))
    for i in range(8):
        ang = math.radians(i * 45)
        r1 = 97 if i % 2 else 86
        parts.append(seg(240 + math.cos(ang) * r1, 182 + math.sin(ang) * r1,
                         240 + math.cos(ang) * 110, 182 + math.sin(ang) * 110,
                         INK if i % 2 == 0 else SOFT, 5.5))
    ang = math.radians(-52)
    nx, ny = math.cos(ang), math.sin(ang)
    px, py = -ny, nx
    parts.append(path(f"M {fmt(240 + nx * 92)} {fmt(182 + ny * 92)} "
                      f"L {fmt(240 + px * 21)} {fmt(182 + py * 21)} "
                      f"L {fmt(240 - px * 21)} {fmt(182 - py * 21)} Z",
                      5, a, fill=a))
    parts.append(path(f"M {fmt(240 - nx * 92)} {fmt(182 - ny * 92)} "
                      f"L {fmt(240 + px * 21)} {fmt(182 + py * 21)} "
                      f"L {fmt(240 - px * 21)} {fmt(182 - py * 21)} Z",
                      5, SOFT, fill=SOFT))
    parts.append(circle(240, 182, 27, WHITE, INK, 7))
    parts.append(text(240, 191, "</>", 24, b, font=MONO))
    return parts


def s_t2av_compass(a, b):
    return [
        halo(250, 180, 205, 152, a),
        rrect(44, 146, 152, 68, 16),
        tline(66, 172, 86, 8, a), tline(66, 192, 56, 8),
        arrow(202, 168, 234, 132, 14, SOFT, 7),
        arrow(202, 194, 234, 230, -14, SOFT, 7),
        film(240, 58, 190, 108, a, play=True),
        wave(335, 250, 190, 11, (a, b), seed=6, hmin=16, hmax=60, bw=9),
        seg(452, 122, 452, 238, b, 6),
        seg(438, 122, 452, 122, b, 6), seg(438, 238, 452, 238, b, 6),
        circle(452, 180, 9, b),
    ]


def s_tablebench(a, b):
    return [
        halo(230, 180, 210, 155, a),
        tablegrid(56, 58, 264, 220, 3, 4, a, hl=((0, 1), (1, 2), (2, 3))),
        path("M 155 128 V 182 H 221 V 236 H 287", 8, b),
        circle(155, 128, 11, b), circle(287, 236, 11, b),
        arrow(324, 250, 356, 262, -10, a, 7),
        rrect(356, 238, 76, 52, 14, fill=a, stroke=a),
        text(394, 273, "42", 28, WHITE, font=MONO),
        check(404, 92),
    ]


def s_tvir(a, b):
    return [
        halo(240, 180, 200, 155, a),
        group(4, 320, 180, doc(230, 66, 180, 236, fold=30)),
        doc(120, 52, 190, 256, fold=30, lines=((46, .15, .8), (68, .15, .64))),
        rrect(148, 138, 82, 60, 8), path("M 158 186 L 178 158 L 194 174 L 202 162 "
                                         "L 216 186", 5, INK),
        tline(244, 152, 44, 6), tline(244, 172, 36, 6),
        rrect(286, 146, 11, 11, 3, fill=a, stroke=None),
        tline(148, 226, 134, 6), tline(148, 248, 100, 6),
        rrect(148, 268, 40, 22, 5, fill=b, stroke=None, op=.75),
        rrect(196, 274, 40, 16, 5, fill=b, stroke=None, op=.45),
        rrect(290, 250, 11, 11, 3, fill=a, stroke=None),
    ]


def s_usb(a, b):
    tile = lambda x, inner: [rrect(x, 54, 92, 66, 14)] + inner
    return [
        halo(240, 195, 195, 160, a),
        *tile(102, [text(148, 100, "Tt", 30, a)]),
        *tile(194, [path("M 210 106 L 228 80 L 242 94 L 252 82 L 268 106", 5.5, INK),
                    circle(254, 76, 6, b)]),
        *tile(286, [wave(332, 87, 60, 5, (b,), seed=2, hmin=10, hmax=38, bw=7)]),
        shield(240, 208, 124, fill=WHITE),
        path("M 200 208 L 228 238 L 284 174", 11, GREEN),
    ]


def s_vidcapbench(a, b):
    bars = [(112, 96, a), (140, 66, b), (168, 84, a), (196, 48, b)]
    return [
        halo(220, 180, 210, 150, a),
        film(54, 92, 232, 138, a),
        rrect(316, 84, 122, 160, 16),
        *[seg(340, y, 340 + w, y, c, 9) for y, w, c in bars],
        *[circle(340 + w, y, 7, c) for y, w, c in bars],
        rrect(96, 262, 150, 40, 12, fill="#E7EEFB", stroke=a),
        tline(118, 282, 106, 7, a),
        check(400, 278),
    ]


def s_vidic(a, b):
    frame = lambda x, hl: [
        rrect(x, 96, 168, 126, 12),
        path(f"M {x + 18} {96 + 100} L {x + 58} {96 + 46} L {x + 90} {96 + 78} "
             f"L {x + 112} {96 + 54} L {x + 146} {96 + 100}", 6, INK),
        circle(x + 126, 96 + 30, 10, a if not hl else b),
    ]
    return [
        halo(240, 180, 210, 150, a),
        *frame(52, False),
        *frame(260, True),
        circle(386, 126, 24, "none", RED, 6, dash="5 9"),
        seg(240, 120, 240, 200, SOFT, 5, dash="6 8"),
        rrect(210, 244, 60, 46, 12, fill=b, stroke=None),
        text(240, 276, "Δ", 28, WHITE),
        tline(120, 258, 0, 0),
        bubble(96, 252, 92, 50, tail=None, fill=WHITE),
        tline(114, 277, 56, 7),
        bubble(304, 252, 92, 50, tail=None, fill="#F7E7EA", stroke=b),
        tline(322, 277, 56, 7, b),
    ]


def s_web_compass(a, b):
    return [
        halo(230, 180, 205, 155, a),
        window(58, 58, 244, 200),
        circle(180, 178, 62, WHITE, SOFT, 5),
        path("M 180 128 L 196 178 L 180 228 L 164 178 Z", 5, a, fill=a),
        circle(180, 178, 9, WHITE, INK, 5),
        path("M 330 120 C 396 138 404 226 342 254 C 300 272 264 254 252 226",
             9, b),
        arrow(252, 226, 248, 208, 0, b, 9),
        check(398, 86),
    ]


def s_workflow_gym(a, b):
    return [
        window(46, 44, 388, 272, bar=38),
        rrect(66, 100, 92, 196, 12, fill="#EDF1F8", stroke=None),
        rrect(80, 118, 64, 12, 6, fill=a, stroke=None, op=.8),
        rrect(80, 146, 64, 12, 6, fill=SOFT, stroke=None),
        rrect(80, 174, 64, 12, 6, fill=SOFT, stroke=None),
        rrect(176, 100, 118, 88, 12),
        tline(192, 132, 80, 6), tline(192, 154, 56, 6),
        rrect(310, 156, 108, 92, 12),
        tline(326, 190, 70, 6), tline(326, 212, 48, 6),
        path("M 112 124 C 200 124 130 144 235 144 S 260 202 330 202", 7, b,
             dash="1 13"),
        cursor(330, 196, 1.1),
        *[circle(92 + i * 26, 278, 5.5, a if i < 5 else SOFT) for i in range(8)],
        check(400, 278, 24),
    ]


def s_worldtravel(a, b):
    return [
        path("M 56 92 L 178 64 V 268 L 56 296 Z", 6.5, INK, fill=WHITE),
        path("M 178 64 L 302 92 V 296 L 178 268 Z", 6.5, INK, fill="#EDF1F8"),
        path("M 302 92 L 424 64 V 268 L 302 296 Z", 6.5, INK, fill=WHITE),
        path("M 96 236 C 140 170 208 214 246 152 C 276 106 330 140 368 118",
             7, a, dash="1 15"),
        pin(96, 244, 15, a),
        pin(246, 162, 15, b),
        pin(368, 128, 15, GREEN),
        rrect(342, 200, 96, 84, 12, fill=WHITE),
        seg(342, 228, 438, 228, a, 6),
        *[circle(366 + i * 24, 250, 5, SOFT) for i in range(4)],
        *[circle(366 + i * 24, 268, 5, SOFT) for i in range(3)],
    ]


def s_yue(a, b):
    return [
        halo(240, 180, 205, 155, a),
        doc(50, 62, 126, 196, fold=24, lines=((48, .18, .74), (76, .18, .6),
                                              (104, .18, .7), (132, .18, .54),
                                              (160, .18, .64))),
        notepair(240, 160, 62, INK),
        wave(352, 128, 152, 9, (a,), seed=7, hmin=14, hmax=58, bw=9),
        wave(352, 232, 152, 9, (b,), seed=9, hmin=14, hmax=58, bw=9),
        seg(300, 290, 404, 290, SOFT, 5),
        text(352, 314, "", 1),
    ]


SCENES = {
    "acadreason": s_acadreason, "artifactsbench": s_artifactsbench,
    "autokaggle": s_autokaggle, "automv": s_automv,
    "chinese_safetyqa": s_chinese_safetyqa, "chinese_simpleqa": s_chinese_simpleqa,
    "cii_bench": s_cii_bench, "code_simpleqa": s_code_simpleqa,
    "codeeditorbench": s_codeeditorbench, "codetracer": s_codetracer,
    "conceptmath": s_conceptmath, "cot_error_detection": s_cot_error_detection,
    "criticlean": s_criticlean, "dr3_eval": s_dr3_eval, "edgebench": s_edgebench,
    "finder": s_finder, "formalmath": s_formalmath,
    "fullstack_bench": s_fullstack_bench, "hellobench": s_hellobench,
    "if_vidcap": s_if_vidcap, "ii_bench": s_ii_bench,
    "inverse_ifeval": s_inverse_ifeval, "iv_bench": s_iv_bench,
    "kor_bench": s_kor_bench, "korgym": s_korgym, "lime": s_lime,
    "longform_rewardbench": s_longform_rewardbench, "m2rc_eval": s_m2rc_eval,
    "mammoth2": s_mammoth2, "mceval": s_mceval, "mm_browsecomp": s_mm_browsecomp,
    "mt_bench_101": s_mt_bench_101, "mt_video_bench": s_mt_video_bench,
    "mtu_bench": s_mtu_bench, "multi_docker_eval": s_multi_docker_eval,
    "mvu_eval": s_mvu_eval, "nl2repo_bench": s_nl2repo_bench,
    "omni_math": s_omni_math, "omnibench": s_omnibench,
    "omnicap_if": s_omnicap_if, "omnivideobench": s_omnivideobench,
    "opencodeinterpreter": s_opencodeinterpreter, "opencoder": s_opencoder,
    "oprover": s_oprover, "ouro": s_ouro, "owl": s_owl,
    "roleagent": s_roleagent, "rolellm": s_rolellm,
    "safedialbench": s_safedialbench, "scalelong": s_scalelong,
    "supergpqa": s_supergpqa, "swe_compass": s_swe_compass,
    "t2av_compass": s_t2av_compass, "tablebench": s_tablebench, "tvir": s_tvir,
    "usb": s_usb, "vidcapbench": s_vidcapbench, "vidic": s_vidic,
    "web_compass": s_web_compass, "workflow_gym": s_workflow_gym,
    "worldtravel": s_worldtravel, "yue": s_yue,
}

# Accessible name + description per benchmark (title/desc in the SVG).
VISUAL_SPECS = {
    "acadreason": ("ACADREASON", "A magnifier over research papers gathering citations into a synthesis."),
    "artifactsbench": ("ArtifactsBench", "Code becoming an interactive browser artifact checked visually."),
    "autokaggle": ("AutoKaggle", "Raw tables flowing through a model into a validated submission."),
    "automv": ("AutoMV", "A song waveform aligned to storyboard film frames."),
    "chinese_safetyqa": ("Chinese SafetyQA", "A shield bearing the character zhong deflecting unsafe prompts."),
    "chinese_simpleqa": ("Chinese SimpleQA", "A Chinese question answered concisely with a cited source."),
    "cii_bench": ("CII-Bench", "A Chinese image read for emotion and implied meaning."),
    "code_simpleqa": ("CodeSimpleQA", "Bilingual programming questions grounded in code facts."),
    "codeeditorbench": ("CodeEditorBench", "Code revised through a visible diff and accepted by tests."),
    "codetracer": ("CodeTracer", "An execution trace with the first faulty state located."),
    "conceptmath": ("ConceptMath", "A concept tree exposing one weak concept."),
    "cot_error_detection": ("Long CoT Error Detection", "A long reasoning chain with the earliest error marked."),
    "criticlean": ("CriticLean", "A Lean proof reviewed by a critic and rechecked."),
    "dr3_eval": ("DR3-Eval", "Multimodal evidence processed in a sealed environment into a cited report."),
    "edgebench": ("EdgeBench", "An agent's competence climbing over a long training horizon."),
    "finder": ("FINDER", "A research query expanded into sources and an evidence checklist."),
    "formalmath": ("FormalMATH", "A theorem's proof tree verified by the compiler."),
    "fullstack_bench": ("FullStack Bench", "A frontend, API, and database verified end to end."),
    "hellobench": ("HelloBench", "A long document held together by a coherence thread."),
    "if_vidcap": ("IF-VidCap", "A video captioned under explicit format constraints."),
    "ii_bench": ("II-Bench", "An image whose larger meaning hides below the surface."),
    "inverse_ifeval": ("Inverse IFEval", "An instruction overriding a conflicting learned prior."),
    "iv_bench": ("IV-Bench", "A reference image grounding evidence from a long video."),
    "kor_bench": ("KOR-Bench", "Novel symbolic rules applied through a reasoning chain."),
    "korgym": ("KORGym", "An agent acting on a game board and learning from feedback."),
    "lime": ("LIME", "A large sample pool filtered into a compact benchmark."),
    "longform_rewardbench": ("Long-form RewardBench", "Two long responses weighed by a reward judge."),
    "m2rc_eval": ("M2RC-Eval", "Repository context completing a missing code region."),
    "mammoth2": ("MAmmoTH2", "Web documents refined into ten million instruction pairs."),
    "mceval": ("McEval", "Code tasks evaluated across forty programming languages."),
    "mm_browsecomp": ("MM-BrowseComp", "A browsing agent combining page, image, and video evidence."),
    "mt_bench_101": ("MT-Bench-101", "A multi-turn conversation carrying growing constraints."),
    "mt_video_bench": ("MT-Video-Bench", "Multiple dialogue turns pointing at different video moments."),
    "mtu_bench": ("MTU-Bench", "One request orchestrating many tools."),
    "multi_docker_eval": ("Multi-Docker-Eval", "A Compose file instantiating healthy connected services."),
    "mvu_eval": ("MVU-Eval", "Evidence retrieved and compared across several videos."),
    "nl2repo_bench": ("NL2Repo-Bench", "A specification expanding into a full repository."),
    "omni_math": ("Omni-MATH", "Olympiad mathematics across algebra, geometry, and number theory."),
    "omnibench": ("OmniBench", "Text, image, and audio combined by one tri-modal model."),
    "omnicap_if": ("OmniCap-IF", "Video and audio captioned under content instructions."),
    "omnivideobench": ("OmniVideoBench", "Synchronized visual and audio streams queried together."),
    "opencodeinterpreter": ("OpenCodeInterpreter", "Code generated, executed, and repaired in a loop."),
    "opencoder": ("OpenCoder", "Raw code refined into an open model family."),
    "oprover": ("OProver", "A Lean proof attempt cycling through compiler feedback."),
    "ouro": ("Ouro", "A shared transformer block looping at variable depth per token."),
    "owl": ("OWL", "An IT alert resolved through a runbook."),
    "roleagent": ("RoleAgent", "A script becoming persona memory and role dialogue."),
    "rolellm": ("RoleLLM", "Character knowledge and style conditioning role-play."),
    "safedialbench": ("SafeDialBench", "Multi-turn jailbreak attempts deflected by a safety shield."),
    "scalelong": ("ScaleLong", "Evidence spread across second, minute, and hour-long videos."),
    "supergpqa": ("SuperGPQA", "Expert questions spanning hundreds of disciplines."),
    "swe_compass": ("SWE-Compass", "A compass steering software-engineering agent work."),
    "t2av_compass": ("T2AV-Compass", "A prompt generating synchronized video and audio."),
    "tablebench": ("TableBench", "A reasoning path crossing a complex table to a result."),
    "tvir": ("TVIR", "Text and visual evidence interleaved into a cited report."),
    "usb": ("USB", "Text, image, and audio attacks covered by one safety shield."),
    "vidcapbench": ("VidCapBench", "A video caption scored across quality dimensions."),
    "vidic": ("ViDiC", "Two similar videos compared to describe their differences."),
    "web_compass": ("WebCompass", "Browser artifacts generated, edited, and repaired."),
    "workflow_gym": ("Workflow-GYM", "A GUI workflow executed step by step to a deliverable."),
    "worldtravel": ("WorldTravel", "A travel route checked against real-world constraints."),
    "yue": ("YuE", "Lyrics becoming aligned vocal and accompaniment tracks."),
}


def render(slug, record):
    a, b = DOMAIN_PALETTES.get(record["domain"], DOMAIN_PALETTES["llm"])
    name, desc = VISUAL_SPECS[slug]
    scene = "\n".join(SCENES[slug](a, b))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<!-- tokenwave:generated:v5 slug={slug} -->
<title id="title">{escape(name)} benchmark illustration</title>
<desc id="desc">{escape(desc)}</desc>
<rect width="{W}" height="{H}" fill="{BG}"/>
{scene}
</svg>
'''


def load_records():
    records = {}
    for path_ in sorted(DATA.glob("*.json")):
        data = json.loads(path_.read_text(encoding="utf-8"))
        records[data["slug"]] = data
    return records


def main():
    records = load_records()
    missing = sorted(set(records) - set(SCENES))
    unknown = sorted(set(SCENES) - set(records))
    if missing or unknown:
        raise SystemExit(f"visual coverage error — missing={missing}, unknown={unknown}")

    rendered = {slug: render(slug, records[slug]) for slug in sorted(records)}

    if CHECK:
        stale = []
        for slug, svg in rendered.items():
            out = OUT / f"{slug.replace('_', '-')}.svg"
            if not out.exists() or out.read_text(encoding="utf-8") != svg:
                stale.append(out.name)
        if stale:
            raise SystemExit("stale benchmark artwork: " + ", ".join(stale))
        print(f"OK — {len(rendered)} bespoke visual scenes are complete and fresh.")
        return

    OUT.mkdir(parents=True, exist_ok=True)
    written = 0
    for slug, svg in rendered.items():
        out = OUT / f"{slug.replace('_', '-')}.svg"
        if out.exists() and not FORCE:
            continue
        out.write_text(svg, encoding="utf-8")
        written += 1
    print(f"generated {written} of {len(rendered)} bespoke SVG scenes")


if __name__ == "__main__":
    main()
