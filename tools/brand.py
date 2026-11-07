#!/usr/bin/env python3
"""Boréale's brand kit: writes every project's icon, wordmarks, README banner
and social preview from its mark, all from one set of templates.

    python3 tools/brand.py            # writes branding/<project>/*.svg
    python3 tools/brand.py --check    # fails if one of them is not up to date

The hand-drawn sources are each project's mark (branding/<project>/mark.svg)
and, below, its icon's drawing; everything else is written here, so that a
rule of branding/README.md changes in one place. node tools/export-branding.mjs
renders the PNGs, python3 tools/sync_branding.py copies them into the projects.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRANDING = ROOT / "branding"

# The colours (branding/README.md, "The colours").
ABYSS, NIGHT, SNOW, MIST = "#0B1424", "#0E1A33", "#E8EEF7", "#A9B6CC"
AURORA, ICE, VIOLET = "#00FFCC", "#33BBFF", "#8A5CFF"

# The frames, in the marks' 256 units.
SQUARE = "M58 40 L 198 40 Q 214 40 214 56 L 214 200 Q 214 216 198 216 L 58 216 Q 42 216 42 200 L 42 56 Q 42 40 58 40 Z"
SHIELD = "M128 42 C 154 54, 180 60, 204 60 L 204 126 C 204 172, 174 200, 128 218 C 82 200, 52 172, 52 126 L 52 60 C 76 60, 102 54, 128 42 Z"
HOUSE = "M128 42 L 212 110 L 212 198 Q 212 214 196 214 L 60 214 Q 44 214 44 198 L 44 110 Z"
CIRCLE = "M128 40 A 88 88 0 1 1 127.99 40 Z"

# The aurora's line across an icon's sky.
HIGH = "M40 120 C 80 92, 110 128, 148 100 S 196 74, 220 84"
LOW = "M44 134 C 80 104, 108 144, 146 116 S 196 90, 214 100"

MOUNTAINS = (
    f'<path d="M20 230 L 20 192 L 66 166 L 90 182 L 124 156 L 164 188 L 188 174 L 236 202 L 236 230 Z" fill="#0A1020"/>'
    f'<path d="M66 166 L 76 172 L 70 176 Z M124 156 L 136 166 L 126 168 Z" fill="#1F3355"/>'
)


def snow(d: str, width: float = 0, fill: bool = True, extra: str = "") -> str:
    """A path in snow: filled, stroked, or both."""
    f = SNOW if fill else "none"
    s = f' stroke="{SNOW}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"' if width else ""
    return f'<path d="{d}" fill="{f}"{s}{extra}/>'


# Each project: its name, its wordmark, what it does (the banner's line, the
# social preview's), what it has (the social preview's last line), and its
# icon: the frame, the aurora's line, the mountains or not, the drawing in snow
# (lit by a soft glow unless glow is False). A tool (tool=True) is a part of
# the products, not a brand of its own: a mark, a banner and a social preview
# with "part of Boréale", no icon nor wordmark files. A Switch homebrew
# (console=True) also gets icon-console.svg, its HOME menu icon with its name,
# its mark scaled by console (as wide and tall as the others' to the eye: a
# mark drawn larger in its file, PlayGuard's at 1.3, takes less).
PROJECTS: dict[str, dict] = {
    "boreale": dict(
        name="Boréale",
        tagline="Homebrew for the long nights",
        features="PlayGuard · PlayShelf · Aurore · Atlas · Lantern · Boréale for HA",
        frame=CIRCLE, line=LOW, mountains=True,
        glyph=snow("M128 64 C 132 90, 138 96, 160 100 C 138 104, 132 110, 128 136 C 124 110, 118 104, 96 100 C 118 96, 124 90, 128 64 Z"),
    ),
    "playguard": dict(
        name="PlayGuard", console=0.5,
        tagline="Nintendo Switch parental controls, right on the console",
        features="Play-time limits · PIN · Restrictions · Activity · Network clock",
        frame=SHIELD, line=LOW, mountains=True,
        glyph=snow("M107.84 102 L 154.88 130 L 107.84 158 Z", 8),
    ),
    "playshelf": dict(
        name="PlayShelf", console=0.62,
        tagline="Your game library, on the console",
        features="Browse · Install · Pause and resume · Your own server",
        frame=SQUARE, line=HIGH, mountains=False, glow=False,
        glyph=(
            f'<g fill="#0A1020" stroke="#2A3F66" stroke-width="2">'
            '<rect x="62" y="74" width="26" height="40" rx="5"/><rect x="94" y="84" width="22" height="30" rx="5"/>'
            '<rect x="150" y="70" width="28" height="44" rx="5"/><rect x="70" y="134" width="30" height="44" rx="5"/>'
            '<rect x="126" y="142" width="22" height="36" rx="5"/><rect x="154" y="132" width="26" height="46" rx="5"/></g>'
            '<path d="M52 118 L 204 118 M52 182 L 204 182" stroke="url(#i-colour)" stroke-width="9" stroke-linecap="round" filter="url(#i-line-glow)" opacity="0.8"/>'
            '<path d="M52 118 L 204 118 M52 182 L 204 182" stroke="url(#i-colour)" stroke-width="7" stroke-linecap="round"/>'
        ),
    ),
    "aurore": dict(
        name="Aurore",
        tagline="A Switch-like interface for your app, on every screen",
        features="Android · iOS · Windows · macOS · Linux · PS4 · PS Vita · Nintendo Switch · New 3DS",
        frame=SQUARE, line=LOW, mountains=True, glyph="",
    ),
    "ha": dict(
        name="Boréale for HA",
        tagline="Your Switch homebrews, at home",
        features="Play time · Limits · Extra time · Bedtime · Statistics · Local MQTT",
        frame=HOUSE, line=HIGH, mountains=False, scale=0.8,
        glyph=(
            f'<rect x="74" y="124" width="108" height="62" rx="14" fill="none" stroke="{SNOW}" stroke-width="10"/>'
            + snow("M98 126 L 98 184 M158 126 L 158 184", 8, fill=False)
        ),
    ),
    "atlas": dict(
        name="Atlas",
        tagline="A map of every game, on every platform",
        features="Renown · Trends · Games alike · What comes next · Open data, every day",
        frame=SQUARE, line=HIGH, mountains=False, scale=0.8,
        glyph=(
            snow("M70 88 L 104 76 L 152 92 L 186 80 L 186 172 L 152 184 L 104 168 L 70 180 Z M104 76 L 104 168 M152 92 L 152 184", 12, fill=False)
            + snow("M128 106 L 132 118 L 144 119 L 135 127 L 138 139 L 128 132 L 118 139 L 121 127 L 112 119 L 124 118 Z")
        ),
    ),
    "lantern": dict(
        name="Lantern",
        tagline="One protocol between your homebrews and your own server",
        features="Open protocol · Specification · SDK · Bridge · Any server",
        frame=SQUARE, line=HIGH, mountains=False, scale=0.8,
        glyph=(
            snow("M114 78 A 14 14 0 0 1 142 78", 10, fill=False)
            + snow("M106 84 L 150 84 L 162 98 L 94 98 Z", 6)
            + f'<rect x="102" y="106" width="52" height="64" rx="8" fill="none" stroke="{SNOW}" stroke-width="12"/>'
            + snow("M128 118 C 137 128, 140 136, 140 144 A 12 12 0 0 1 116 144 C 116 136, 119 128, 128 118 Z")
            + f'<rect x="92" y="178" width="72" height="12" rx="6" fill="{SNOW}"/>'
        ),
    ),
    "sdk": dict(
        name="Lantern SDK",
        tagline="Speak Lantern from your homebrew, in six languages",
        features="C++23 · C · Python · TypeScript · Rust · Go · Conformance tests",
        frame=SQUARE, line=HIGH, mountains=False, scale=0.8,
        glyph=(
            '<g transform="translate(-10 0)">' + snow("M104 84 A 12 12 0 0 1 128 84", 9, fill=False)
            + snow("M98 90 L 134 90 L 144 102 L 88 102 Z", 5)
            + f'<rect x="96" y="108" width="44" height="54" rx="7" fill="none" stroke="{SNOW}" stroke-width="10"/>'
            + snow("M118 118 C 126 127, 128 133, 128 139 A 10 10 0 0 1 108 139 C 108 133, 110 127, 118 118 Z")
            + f'<rect x="88" y="168" width="60" height="10" rx="5" fill="{SNOW}"/>' + '</g>'
            + snow("M164 116 L 152 134 L 164 152 M190 116 L 202 134 L 190 152", 9, fill=False)
        ),
    ),
    "bridge": dict(
        name="Lantern Bridge",
        tagline="Your Ownfoil, AeroFoil or Tinfoil library, spoken in Lantern",
        features="Ownfoil · AeroFoil · Tinfoil shops · Plain folders · Read-only",
        frame=SQUARE, line=HIGH, mountains=False, scale=0.8,
        glyph=(
            snow("M80 150 Q 128 84 176 150", 12, fill=False)
            + f'<rect x="66" y="150" width="124" height="12" rx="6" fill="{SNOW}"/>'
            + snow("M104 125 L 104 150 M128 112 L 128 150 M152 125 L 152 150", 8, fill=False)
        ),
    ),
    "kit": dict(
        name="boreale-kit", tool=True,
        tagline="The C++23 library the Boréale apps share",
        features="Inside PlayGuard and PlayShelf · Network · Updates · Logs · Diagnostics · Shared screens",
        frame=SQUARE, line=HIGH, mountains=False, scale=0.8,
        glyph=(
            snow("M128 76 L 184 104 L 128 132 L 72 104 Z", 10)
            + snow("M72 134 L 128 162 L 184 134 M72 162 L 128 190 L 184 162", 12, fill=False)
        ),
    ),
    "link": dict(
        name="boreale-link", tool=True,
        tagline="The remote link the Boréale homebrews share",
        features="Inside PlayGuard and PlayShelf · MQTT 5.0 · TLS · JSON · C, no allocation",
        frame=SQUARE, line=HIGH, mountains=False, scale=0.8,
        glyph=(
            f'<g transform="rotate(-45 128 128)" fill="none" stroke="{SNOW}" stroke-width="12">'
            '<rect x="60" y="106" width="80" height="44" rx="22"/><rect x="116" y="106" width="80" height="44" rx="22"/></g>'
        ),
    ),
}

GRADIENT = (f'<stop offset="0" stop-color="{AURORA}"/><stop offset="0.6" stop-color="{ICE}"/>'
            f'<stop offset="1" stop-color="{VIOLET}"/>')
DIAGONAL = (f'<stop offset="0" stop-color="{AURORA}"/><stop offset="0.65" stop-color="{ICE}"/>'
            f'<stop offset="1" stop-color="{VIOLET}"/>')


def icon(key: str) -> str:
    p = PROJECTS[key]
    frame, line = p["frame"], p["line"]
    glyph = p["glyph"]
    if glyph and "scale" in p:  # a mark's drawing, made room for the sky
        k = p["scale"]
        glyph = f'<g transform="translate(128 132) scale({k}) translate(-128 -132)">{glyph}</g>'
    if glyph and p.get("glow", True):
        glyph = f'<g filter="url(#i-soft)" opacity="0.5">{glyph}</g>{glyph}'
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <!-- {p["name"]}'s icon, written by tools/brand.py: its mark's frame in the aurora's colours around a night sky, the aurora, its drawing in snow. Full-bleed: the consoles, the stores and the phones round its corners; <image href="icon.svg"> elsewhere rounds them itself. -->
  <defs>
    <linearGradient id="i-night" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0A1020"/><stop offset="1" stop-color="#16203A"/></linearGradient>
    <linearGradient id="i-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0B1430"/><stop offset="1" stop-color="#132A44"/></linearGradient>
    <linearGradient id="i-colour" x1="0" y1="0" x2="1" y2="0">{GRADIENT}</linearGradient>
    <linearGradient id="i-frame-colour" x1="0" y1="0" x2="1" y2="1">{DIAGONAL}</linearGradient>
    <linearGradient id="i-rise" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset="0.25" stop-color="#fff" stop-opacity="0.75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <pattern id="i-rays" width="9" height="256" patternUnits="userSpaceOnUse"><rect width="9" height="256" fill="#fff" opacity="0.55"/><rect x="2" width="4" height="256" fill="#fff"/></pattern>
    <filter id="i-ray-blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.6 0"/></filter>
    <mask id="i-curtain-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="256"><g filter="url(#i-ray-blur)"><rect width="256" height="256" fill="url(#i-rays)"/></g></mask>
    <filter id="i-glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="7"/></filter>
    <filter id="i-line-glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>
    <filter id="i-soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>
    <clipPath id="i-frame"><path d="{frame}"/></clipPath>
    <mask id="i-fade" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="256"><path d="{line} L 230 20 L 26 20 Z" fill="url(#i-rise)"/></mask>
  </defs>
  <rect width="256" height="256" fill="url(#i-night)"/>
  <g clip-path="url(#i-frame)">
    <rect width="256" height="256" fill="url(#i-sky)"/>
    <circle cx="80" cy="72" r="1.8" fill="{SNOW}"/><circle cx="178" cy="70" r="1.5" fill="{SNOW}" opacity="0.8"/>
    <circle cx="128" cy="62" r="1.2" fill="{SNOW}" opacity="0.6"/><circle cx="156" cy="84" r="1" fill="{SNOW}" opacity="0.5"/>
    <g mask="url(#i-fade)"><rect x="20" y="20" width="216" height="200" fill="url(#i-colour)" mask="url(#i-curtain-mask)"/></g>
    <path d="{line}" fill="none" stroke="url(#i-colour)" stroke-width="6" filter="url(#i-line-glow)"/>
    <path d="{line}" fill="none" stroke="url(#i-colour)" stroke-width="3" stroke-linecap="round"/>
    {MOUNTAINS if p["mountains"] else ""}{glyph}
  </g>
  <path d="{frame}" fill="none" stroke="url(#i-frame-colour)" stroke-width="10" stroke-linejoin="round" filter="url(#i-glow)" opacity="0.6"/>
  <path d="{frame}" fill="none" stroke="url(#i-frame-colour)" stroke-width="8" stroke-linejoin="round"/>
</svg>
"""



def console_icon(key: str) -> str:
    """The HOME menu icon of a Switch homebrew: the night sky and the aurora
    over the whole square, the mark lifted by its shadow, the name in Sora
    700 beneath, as the console's other homebrews show theirs."""
    p = PROJECTS[key]
    line = p["line"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <!-- {p["name"]}'s HOME menu icon (icon.jpg), written by tools/brand.py: the night sky and the aurora's curtain over the whole square, its mark lifted by a shadow, its name in Sora 700. Everywhere else, icon.svg. -->
  <defs>
    <linearGradient id="c-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0B1430"/><stop offset="0.7" stop-color="#1A3557"/><stop offset="1" stop-color="#0A1020"/></linearGradient>
    <linearGradient id="c-colour" x1="0" y1="0" x2="1" y2="0">{GRADIENT}</linearGradient>
    <linearGradient id="c-rise" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0.9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <pattern id="c-rays" width="9" height="256" patternUnits="userSpaceOnUse"><rect width="9" height="256" fill="#fff" opacity="0.55"/><rect x="2" width="4" height="256" fill="#fff"/></pattern>
    <filter id="c-ray-blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.6 0"/></filter>
    <mask id="c-curtain" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="256"><g filter="url(#c-ray-blur)"><rect width="256" height="256" fill="url(#c-rays)"/></g></mask>
    <mask id="c-fade" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="256"><path d="M0 128 C 60 88, 110 138, 170 98 S 240 68, 256 78 L 256 0 L 0 0 Z" fill="url(#c-rise)"/></mask>
    <filter id="c-blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
    <filter id="c-shadow" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity="0.55"/></filter>
  </defs>
  <rect width="256" height="256" fill="url(#c-sky)"/>
  <g mask="url(#c-fade)"><rect width="256" height="256" fill="url(#c-colour)" opacity="0.8" mask="url(#c-curtain)"/></g>
  <g mask="url(#c-fade)" filter="url(#c-blur)"><rect width="256" height="256" fill="url(#c-colour)" opacity="0.35"/></g>
  <circle cx="40" cy="30" r="1.5" fill="{SNOW}"/><circle cx="214" cy="146" r="1.2" fill="{SNOW}" opacity="0.7"/><circle cx="30" cy="160" r="1" fill="{SNOW}" opacity="0.5"/>
  <g filter="url(#c-shadow)" transform="translate(128 102) scale({p["console"]}) translate(-128 -130)">{inner(mark(key), "c")}</g>
  <text x="128" y="224" text-anchor="middle" font-family="Sora" font-weight="700" font-size="34" letter-spacing="-0.8" fill="{SNOW}">{p["name"]}</text>
</svg>
"""

# The marks under 24 px and in one ink, for each product (Boréale's are drawn
# by hand): the mark's frame and drawing, bolder and without the aurora for the
# small one, in one ink with the night left empty for the other (what prints,
# engraves, or Android's themed icon takes). `draw(ink, t)` is the drawing in
# one ink, t the weight added.
def _playguard(ink: str, t: int) -> str:
    return f'<path d="M108 98 L 156 130 L 108 162 Z" fill="{ink}" stroke="{ink}" stroke-width="{10 + t}" stroke-linejoin="round"/>'


def _playshelf(ink: str, t: int) -> str:
    return (f'<path d="M68 112 L 188 112 M68 176 L 188 176" stroke="{ink}" stroke-width="{14 + t}" stroke-linecap="round"/>'
            f'<path d="M76 98 L 76 72 M100 98 L 100 82 M150 98 L 150 68 M86 162 L 86 132 M134 162 L 134 140 M160 162 L 160 130" stroke="{ink}" stroke-width="{16 + t}" stroke-linecap="round"/>')


def _aurore(ink: str, t: int) -> str:
    return (f'<path d="M40 150 C 80 132, 120 150, 150 128 S 196 100, 216 104" fill="none" stroke="{ink}" stroke-width="{10 + t}" stroke-linecap="round"/>'
            f'<path d="M40 216 L 40 200 L 84 164 L 106 184 L 140 146 L 186 192 L 216 172 L 216 216 Z" fill="{ink}"/>')


def _ha(ink: str, t: int) -> str:
    return (f'<rect x="74" y="120" width="108" height="62" rx="14" fill="none" stroke="{ink}" stroke-width="{10 + t}"/>'
            f'<path d="M98 122 L 98 180 M158 122 L 158 180" stroke="{ink}" stroke-width="{8 + t}" stroke-linecap="round"/>')


def _atlas(ink: str, t: int) -> str:
    return (f'<path d="M70 88 L 104 76 L 152 92 L 186 80 L 186 172 L 152 184 L 104 168 L 70 180 Z M104 76 L 104 168 M152 92 L 152 184" fill="none" stroke="{ink}" stroke-width="{12 + t}" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<path d="M128 106 L 132 118 L 144 119 L 135 127 L 138 139 L 128 132 L 118 139 L 121 127 L 112 119 L 124 118 Z" fill="{ink}"/>')


# frame, how it is drawn (a path, or Aurore's rounded square), the drawing,
# a transform for the drawing and the frame together.
SMALL = {
    "playguard": (SHIELD, _playguard, 'transform="translate(128 130) scale(1.3) translate(-128 -130)"'),
    "playshelf": (SQUARE, _playshelf, ""),
    "aurore": (None, _aurore, ""),
    "ha": (HOUSE, _ha, ""),
    "atlas": (SQUARE, _atlas, ""),
}
AURORE_FRAME = 'x="42" y="42" width="172" height="172" rx="34"'


def _frame(key: str, fill: str, stroke: str, width: int) -> str:
    frame = SMALL[key][0]
    attrs = f'fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round"'
    return f"<rect {AURORE_FRAME} {attrs}/>" if frame is None else f'<path d="{frame}" {attrs}/>'


def _clip(key: str, body: str) -> str:
    """Aurore's mountains stay inside its pane."""
    return f'<g clip-path="url(#pane)">{body}</g>' if key == "aurore" else body


def mark_small(key: str) -> str:
    """The mark under 24 px (favicons): a heavier frame, a heavier drawing, no aurora."""
    _, draw, _ = SMALL[key]
    transform = 'transform="translate(128 130) scale(1.15) translate(-128 -130)"' if key == "playguard" else ""
    name = PROJECTS[key]["name"]
    pane = '<clipPath id="pane"><rect x="50" y="50" width="156" height="156" rx="26"/></clipPath>' if key == "aurore" else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <!-- {name}'s mark under 24 px (favicons), written by tools/brand.py: a heavier frame and drawing than the mark's, no aurora. -->
  <defs><linearGradient id="colour" x1="0" y1="0" x2="1" y2="1">{DIAGONAL}</linearGradient>{pane}</defs>
  <g {transform}>
  {_frame(key, NIGHT, "url(#colour)", 26)}
  {_clip(key, draw(SNOW, 0 if key == "playshelf" else 5))}
  </g>
</svg>
"""


def mark_mono(key: str, ink: str, label: str) -> str:
    """The mark in one ink, the night left empty."""
    _, draw, transform = SMALL[key]
    name = PROJECTS[key]["name"]
    pane = '<defs><clipPath id="pane"><rect x="50" y="50" width="156" height="156" rx="26"/></clipPath></defs>' if key == "aurore" else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <!-- {name}'s mark in one colour ({label}), written by tools/brand.py, for what prints or engraves one ink and for Android's themed icon: the frame and the drawing, the night left empty. -->
  {pane}
  <g {transform}>
  {_frame(key, "none", ink, 16)}
  {_clip(key, draw(ink, 0))}
  </g>
</svg>
"""


def wordmark(key: str, light: bool) -> str:
    """The name in Sora 700, underlined by the aurora: snow for the night, the
    night for light grounds. 360 × 88 units, a transparent ground."""
    p = PROJECTS[key]
    ink, ground = (ABYSS, "light grounds") if light else (SNOW, "the night")
    size = 60 if len(p["name"]) <= 10 else 40
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="176" viewBox="0 0 360 88">
  <!-- {p["name"]}'s wordmark for {ground}, written by tools/brand.py: the name in Sora 700, underlined by the aurora's colours. -->
  <defs><linearGradient id="w-word" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{AURORA}"/><stop offset="0.55" stop-color="{ICE}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient></defs>
  <text x="180" y="56" text-anchor="middle" font-family="Sora" font-weight="700" font-size="{size}" letter-spacing="-1.5" fill="{ink}">{p["name"]}</text>
  <rect x="150" y="80" width="60" height="4" rx="2" fill="url(#w-word)"/>
</svg>
"""


def inner(svg: str, prefix: str) -> str:
    """A drawing's body, its ids made unique so several share one file."""
    body = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    for name in sorted(set(re.findall(r'id="([^"]+)"', body))):
        body = body.replace(f'id="{name}"', f'id="{prefix}-{name}"').replace(f"url(#{name})", f"url(#{prefix}-{name})")
    return body.strip()


def mark(key: str) -> str:
    return (BRANDING / key / "mark.svg").read_text(encoding="utf-8")


def by_boreale(right: int, y: int, tool: bool = False) -> str:
    """Boréale's mark and name in a pill, its right edge at right: "by
    Boréale" for a product, "part of Boréale" for a tool."""
    words, w = ("part of", 236) if tool else ("by", 192)
    return (f'<g transform="translate({right - w} {y})">'
            f'<rect width="{w}" height="52" rx="26" fill="{NIGHT}" stroke="#22324F" stroke-width="2"/>'
            f'<svg x="12" y="8" width="36" height="36" viewBox="0 0 256 256">{inner(mark("boreale"), "b")}</svg>'
            f'<text x="58" y="34" font-family="Sora" font-weight="400" font-size="20" fill="{MIST}">{words} <tspan font-weight="700" fill="{SNOW}">Boréale</tspan></text></g>')


def banner(key: str) -> str:
    p = PROJECTS[key]
    pill = "" if key == "boreale" else by_boreale(1252, 28, p.get("tool", False))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="320" viewBox="0 0 1280 320">
  <!-- {p["name"]}'s README banner, written by tools/brand.py: the night, the aurora, its mark, its name, what it does, and Boréale's mark and name in a pill. Sora. -->
  <defs>
    <linearGradient id="word" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{AURORA}"/><stop offset="0.55" stop-color="{ICE}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>
    <linearGradient id="c1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{AURORA}" stop-opacity="0"/><stop offset="1" stop-color="{AURORA}" stop-opacity="0.3"/></linearGradient>
    <linearGradient id="c2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ICE}" stop-opacity="0"/><stop offset="1" stop-color="{ICE}" stop-opacity="0.22"/></linearGradient>
    <linearGradient id="c3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{VIOLET}" stop-opacity="0"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0.24"/></linearGradient>
    <filter id="soft"><feGaussianBlur stdDeviation="12"/></filter>
  </defs>
  <rect width="1280" height="320" rx="24" fill="{ABYSS}"/>
  <g filter="url(#soft)">
    <path d="M0 170 C 220 110, 420 190, 640 130 S 1040 80, 1280 120 L 1280 10 C 1040 -10, 860 60, 640 30 S 220 0, 0 60 Z" fill="url(#c1)"/>
    <path d="M0 130 C 260 90, 480 150, 700 110 S 1080 60, 1280 90 L 1280 0 L 0 0 Z" fill="url(#c2)"/>
    <path d="M0 100 C 300 60, 520 120, 760 80 S 1100 40, 1280 60 L 1280 0 L 0 0 Z" fill="url(#c3)"/>
  </g>
  <g fill="{SNOW}"><circle cx="80" cy="40" r="1.4" opacity="0.7"/><circle cx="300" cy="28" r="1.2" opacity="0.5"/><circle cx="520" cy="54" r="1.6" opacity="0.7"/><circle cx="760" cy="22" r="1.1" opacity="0.5"/><circle cx="980" cy="48" r="1.5" opacity="0.7"/><circle cx="1180" cy="30" r="1.2" opacity="0.6"/></g>
  <svg x="72" y="76" width="168" height="168" viewBox="0 0 256 256">{inner(mark(key), "m")}</svg>
  <text x="276" y="172" font-family="Sora" font-weight="700" font-size="76" letter-spacing="-2.5" fill="{SNOW}">{p["name"]}</text>
  <rect x="280" y="192" width="72" height="5" rx="2.5" fill="url(#word)"/>
  <text x="278" y="236" font-family="Sora" font-weight="300" font-size="28" fill="{SNOW}">{p["tagline"]}</text>
  {pill}
</svg>
"""


def social(key: str) -> str:
    p = PROJECTS[key]
    wave = "M0 330 C 220 220, 440 360, 700 270 S 1100 180, 1280 230"
    pill = "" if key == "boreale" else by_boreale(1240, 572, p.get("tool", False))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640">
  <!-- {p["name"]}'s social preview (1280 × 640: GitHub's Settings › General, the site's og:image), written by tools/brand.py: the aurora's curtain over the night, the icon, the name, what it does, what it has, and Boréale's pill. Sora. -->
  <defs>
    <linearGradient id="s-sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0A1020"/><stop offset="1" stop-color="#141B2E"/></linearGradient>
    <linearGradient id="s-word" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{AURORA}"/><stop offset="0.55" stop-color="{ICE}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>
    <linearGradient id="s-colour" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{AURORA}" stop-opacity="0"/><stop offset="0.25" stop-color="{AURORA}"/><stop offset="0.65" stop-color="{ICE}"/><stop offset="0.9" stop-color="{VIOLET}"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient>
    <linearGradient id="s-rise" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0.9"/><stop offset="0.3" stop-color="#fff" stop-opacity="0.5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <pattern id="s-rays" width="14" height="640" patternUnits="userSpaceOnUse"><rect width="14" height="640" fill="#fff" opacity="0.5"/><rect x="3.5" width="6.3" height="640" fill="#fff"/></pattern>
    <filter id="s-soft" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="4.2 2"/></filter>
    <filter id="s-line" x="-10%" y="-100%" width="120%" height="300%"><feGaussianBlur stdDeviation="6"/></filter>
    <mask id="s-rays-mask" maskUnits="userSpaceOnUse" x="0" y="0" width="1280" height="640"><rect width="1280" height="640" fill="url(#s-rays)" filter="url(#s-soft)"/></mask>
    <mask id="s-fade" maskUnits="userSpaceOnUse" x="0" y="0" width="1280" height="640"><path d="{wave} L 1280 0 L 0 0 Z" fill="url(#s-rise)"/></mask>
    <clipPath id="s-tile"><rect x="560" y="110" width="160" height="160" rx="36"/></clipPath>
  </defs>
  <rect width="1280" height="640" fill="url(#s-sky)"/>
  <g opacity="0.55">
    <g mask="url(#s-fade)"><rect width="1280" height="640" fill="url(#s-colour)" mask="url(#s-rays-mask)"/></g>
    <path d="{wave}" fill="none" stroke="url(#s-colour)" stroke-width="10" filter="url(#s-line)"/>
    <path d="{wave}" fill="none" stroke="url(#s-colour)" stroke-width="2.5" opacity="0.8"/>
  </g>
  <g fill="{SNOW}">
    <circle cx="140" cy="60" r="1.6" opacity="0.7"/><circle cx="1130" cy="70" r="1.4" opacity="0.8"/>
    <circle cx="1200" cy="520" r="1.2" opacity="0.6"/><circle cx="90" cy="560" r="1.2" opacity="0.5"/>
    <circle cx="640" cy="40" r="1.3" opacity="0.6"/><circle cx="980" cy="600" r="1" opacity="0.5"/>
  </g>
  <g clip-path="url(#s-tile)"><svg x="560" y="110" width="160" height="160" viewBox="0 0 256 256">{inner(icon(key), "i")}</svg></g>
  <text x="640" y="400" text-anchor="middle" font-family="Sora" font-weight="700" font-size="104" letter-spacing="-2.5" fill="{SNOW}">{p["name"]}</text>
  <rect x="580" y="424" width="120" height="5" rx="2.5" fill="url(#s-word)"/>
  <text x="640" y="484" text-anchor="middle" font-family="Sora" font-size="30" fill="{MIST}">{p["tagline"]}</text>
  <text x="640" y="548" text-anchor="middle" font-family="Sora" font-size="22" fill="#6F7E99">{p["features"]}</text>
  {pill}
</svg>
"""


# The colours and fonts as data (branding/tokens.json, `schema` 1) and as CSS
# variables (branding/tokens.css), for the sites and themes that read them
# instead of copying the codes. Grounds and inks, with their contrast.
COLOURS = {
    "abyss": ABYSS, "night": NIGHT, "snow": SNOW, "mist": MIST,
    "aurora": AURORA, "ice": ICE, "violet": VIOLET,
}
FONTS = {
    "display": "Sora", "text": "Figtree", "mono": "JetBrains Mono",
}
PAIRS = [  # (ink, ground): what is allowed to sit on what
    ("snow", "abyss"), ("snow", "night"), ("mist", "abyss"), ("mist", "night"),
    ("aurora", "abyss"), ("aurora", "night"), ("ice", "abyss"), ("ice", "night"),
    ("violet", "abyss"), ("violet", "night"), ("abyss", "snow"), ("abyss", "aurora"),
]


def luminance(hex_colour: str) -> float:
    def channel(v: int) -> float:
        c = v / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(ink: str, ground: str) -> float:
    a, b = sorted((luminance(COLOURS[ink]), luminance(COLOURS[ground])), reverse=True)
    return (a + 0.05) / (b + 0.05)


def tokens_json() -> str:
    import json
    data = {
        "schema": 1,
        "colours": COLOURS,
        "gradient": {"direction": "135deg", "stops": [[AURORA, 0], [ICE, 0.65], [VIOLET, 1]]},
        "fonts": FONTS,
        "contrast": [
            {"ink": i, "ground": g, "ratio": round(contrast(i, g), 2),
             "text": "AAA" if contrast(i, g) >= 7 else "AA" if contrast(i, g) >= 4.5 else "large only" if contrast(i, g) >= 3 else "no"}
            for i, g in PAIRS
        ],
        "projects": [k for k, p in PROJECTS.items() if not p.get("tool")],
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def tokens_css() -> str:
    lines = [f"  --{name}: {value};" for name, value in COLOURS.items()]
    lines.append(f"  --gradient: linear-gradient(135deg, {AURORA} 0%, {ICE} 65%, {VIOLET} 100%);")
    lines += [f'  --font-{role}: "{name}", system-ui, sans-serif;' if role != "mono" else f'  --font-{role}: "{name}", ui-monospace, monospace;'
              for role, name in FONTS.items()]
    return ("/* Boréale's colours and fonts, written by tools/brand.py (branding/tokens.json holds the same). */\n"
            ":root {\n" + "\n".join(lines) + "\n}\n")


def loader() -> str:
    """The aurora's loading animation (branding/aurora-loader.svg): three
    curtains of the gradient swaying over a line, 3 s loop, no script, on a
    transparent ground. Under prefers-reduced-motion it stands still."""
    def band(y: int, op: float, dur: str, delay: str) -> str:
        a = f"M0 {y} C 50 {y - 40}, 90 {y + 40}, 128 {y} S 206 {y - 40}, 256 {y}"
        b = f"M0 {y} C 50 {y + 40}, 90 {y - 40}, 128 {y} S 206 {y + 40}, 256 {y}"
        return (f'<path d="{a}" fill="none" stroke="url(#g)" stroke-width="22" stroke-linecap="round" opacity="{op}">'
                f'<animate attributeName="d" dur="{dur}" begin="{delay}" repeatCount="indefinite" calcMode="spline" '
                f'keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1" values="{a};{b};{a}"/></path>')
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img" aria-label="Loading">\n'
        "<!-- SPDX-License-Identifier: GPL-3.0-or-later. Written by tools/brand.py. -->\n"
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{AURORA}"/>'
        f'<stop offset="0.65" stop-color="{ICE}"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient></defs>\n'
        + band(104, 0.45, "3s", "0s") + "\n" + band(128, 0.8, "3s", "-1s") + "\n" + band(152, 0.45, "3s", "-2s") + "\n"
        "<style>@media (prefers-reduced-motion: reduce) { animate { display: none } }</style>\n</svg>\n")


def outputs() -> dict[Path, str]:
    files: dict[Path, str] = {BRANDING / "tokens.json": tokens_json(), BRANDING / "tokens.css": tokens_css(),
                                  BRANDING / "aurora-loader.svg": loader()}
    for key in PROJECTS:
        d = BRANDING / key
        if not PROJECTS[key].get("tool"):
            files[d / "icon.svg"] = icon(key)
            files[d / "wordmark.svg"] = wordmark(key, light=False)
            files[d / "wordmark-light.svg"] = wordmark(key, light=True)
        if PROJECTS[key].get("console"):
            files[d / "icon-console.svg"] = console_icon(key)
        if key in SMALL:
            files[d / "mark-small.svg"] = mark_small(key)
            files[d / "mark-mono-white.svg"] = mark_mono(key, "#FFFFFF", "white")
            files[d / "mark-mono-black.svg"] = mark_mono(key, "#000000", "black")
        files[d / "banner.svg"] = banner(key)
        files[d / "social-preview.svg"] = social(key)
    return files


def main(argv: list[str]) -> int:
    check = "--check" in argv
    stale = []
    for path, text in outputs().items():
        rel = path.relative_to(ROOT)
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(str(rel))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            print(rel)
    if stale:
        print("Not up to date (python3 tools/brand.py):\n  " + "\n  ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
