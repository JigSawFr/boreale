#!/usr/bin/env python3
"""Writes each project's README banner, branding/banners/<project>.svg.

    python3 tools/make_banners.py

One template for every project (branding/README.md): the night, the aurora,
the project's mark (library/boreale-site/assets/marks/), its name, what it
does, and Boréale's mark and name in a corner. node tools/export-branding.mjs renders the PNGs.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKS = ROOT / "library/boreale-site/assets/marks"
OUT = ROOT / "branding/banners"

PROJECTS = {
    "playguard": ("PlayGuard", "Nintendo Switch parental controls, right on the console"),
    "playshelf": ("PlayShelf", "Your game library, on the console"),
    "aurore": ("Aurore", "A Switch-like interface for your app, on every screen"),
}


def inner(svg: str, prefix: str) -> str:
    """A mark's drawing, its ids made unique so several marks share one file."""
    body = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    for name in set(re.findall(r'id="([^"]+)"', body)):
        body = body.replace(f'id="{name}"', f'id="{prefix}-{name}"').replace(f"url(#{name})", f"url(#{prefix}-{name})")
    return body.strip()


TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="320" viewBox="0 0 1280 320">
  <!-- {name}'s README banner, written by tools/make_banners.py: the night, the aurora, its mark, its name, what it does, and Boréale's mark and name in a pill. Sora. -->
  <defs>
    <linearGradient id="word" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00FFCC"/><stop offset="0.55" stop-color="#33BBFF"/><stop offset="1" stop-color="#8A5CFF"/></linearGradient>
    <linearGradient id="c1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#00FFCC" stop-opacity="0"/><stop offset="1" stop-color="#00FFCC" stop-opacity="0.3"/></linearGradient>
    <linearGradient id="c2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#33BBFF" stop-opacity="0"/><stop offset="1" stop-color="#33BBFF" stop-opacity="0.22"/></linearGradient>
    <linearGradient id="c3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8A5CFF" stop-opacity="0"/><stop offset="1" stop-color="#8A5CFF" stop-opacity="0.24"/></linearGradient>
    <filter id="soft"><feGaussianBlur stdDeviation="12"/></filter>
  </defs>
  <rect width="1280" height="320" rx="24" fill="#0B1424"/>
  <g filter="url(#soft)">
    <path d="M0 170 C 220 110, 420 190, 640 130 S 1040 80, 1280 120 L 1280 10 C 1040 -10, 860 60, 640 30 S 220 0, 0 60 Z" fill="url(#c1)"/>
    <path d="M0 130 C 260 90, 480 150, 700 110 S 1080 60, 1280 90 L 1280 0 L 0 0 Z" fill="url(#c2)"/>
    <path d="M0 100 C 300 60, 520 120, 760 80 S 1100 40, 1280 60 L 1280 0 L 0 0 Z" fill="url(#c3)"/>
  </g>
  <g fill="#E8EEF7"><circle cx="80" cy="40" r="1.4" opacity="0.7"/><circle cx="300" cy="28" r="1.2" opacity="0.5"/><circle cx="520" cy="54" r="1.6" opacity="0.7"/><circle cx="760" cy="22" r="1.1" opacity="0.5"/><circle cx="980" cy="48" r="1.5" opacity="0.7"/><circle cx="1180" cy="30" r="1.2" opacity="0.6"/></g>
  <svg x="72" y="76" width="168" height="168" viewBox="0 0 256 256">{mark}</svg>
  <text x="276" y="172" font-family="Sora" font-weight="700" font-size="76" letter-spacing="-2.5" fill="#E8EEF7">{name}</text>
  <rect x="280" y="192" width="72" height="5" rx="2.5" fill="url(#word)"/>
  <text x="278" y="236" font-family="Sora" font-weight="300" font-size="28" fill="#E8EEF7">{tagline}</text>
  <rect x="1060" y="28" width="192" height="52" rx="26" fill="#0E1A33" stroke="#22324F" stroke-width="2"/>
  <svg x="1072" y="36" width="36" height="36" viewBox="0 0 256 256">{boreale}</svg>
  <text x="1118" y="62" font-family="Sora" font-weight="400" font-size="20" fill="#A9B6CC">by <tspan font-weight="700" fill="#E8EEF7">Boréale</tspan></text>
</svg>
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    boreale = inner((MARKS / "boreale.svg").read_text(encoding="utf-8"), "b")
    for key, (name, tagline) in PROJECTS.items():
        mark = inner((MARKS / f"{key}.svg").read_text(encoding="utf-8"), "m")
        (OUT / f"{key}.svg").write_text(TEMPLATE.format(name=name, tagline=tagline, mark=mark, boreale=boreale), encoding="utf-8")
        print(f"branding/banners/{key}.svg")


if __name__ == "__main__":
    main()
