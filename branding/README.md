# Boréale's brand

The look shared by Boréale and its projects, kept here once: every project's mark, icon, wordmarks, README banner and social preview, from one set of templates, copied into the projects' repositories from here.

## The kit

Every mark follows one rule, set by PlayGuard's and PlayShelf's: **a frame in the aurora's colours around the night, one drawing in snow inside**.

One folder per product: `boreale`, `playguard`, `playshelf`, `aurore`, `ha` (Boréale for Home Assistant), `atlas`. Each holds the same files:

| File | What | Where |
|---|---|---|
| `mark.svg` | **Drawn by hand.** The frame and the drawing, flat | Headers, site menus, cards, favicons, the banner |
| `icon.svg` | The mark's frame around a night sky: the aurora's curtain and line, the mountains for some, the drawing in snow with a soft glow. Full-bleed | App, store, console and touch icons, the social preview |
| `wordmark.svg`, `wordmark-light.svg` | The name in Sora 700, underlined by the aurora, in snow or in night | Loading screens, on the night, on light grounds |
| `banner.svg` | The night, the aurora, the mark, the name, what it does, "by Boréale" in a pill ("part of Boréale" for a tool) | The README's top |
| `social-preview.svg` | The aurora's curtain, the icon, the name, what it does, what it has, "by Boréale" | GitHub's social preview (Settings › General), the site's `og:image` |
| `png/` | All of them rendered: `icon-{1024,512,256,192}.png`, `icon-256.jpg` (the Switch's homebrew icon), `apple-touch-icon.png`, `icon-tile-{512,256}.png` (rounded on a transparent ground, where nothing rounds it), `mark-{512,256}.png`, `wordmark{,-light}.png` (720 × 176), `banner.png` (2560 × 640), `social-preview.png` (1280 × 640), `favicon.ico` (16, 32, 48) | |

The tools, `lantern` (Lantern SDK), `kit` (boreale-kit) and `link` (boreale-link), are parts of the products, not brands of their own: a mark, a banner and a social preview saying "part of Boréale", rendered to `mark-{512,256}.png`, `banner.png` and `social-preview.png`; no icon, wordmark nor favicon. The sites' menus show Lantern's mark, not the libraries'.

Boréale's own folder adds `mark-small.svg` (the circle and the star, under 24 px: favicons) and `mark-mono-white.svg`, `mark-mono-black.svg` (one ink, the night left empty). At the root, `badge-ai.svg` ("human-led · AI-assisted", the projects' README badge linking to boreale.dev's `how/`).

Only the marks and the icons' drawings are drawn by hand; the rest is written by `tools/brand.py`, whose table holds each project's name, line and features. To change or add a project:

1. Its mark in `branding/<project>/mark.svg`, its icon's frame and drawing and its texts in `tools/brand.py`.
2. `python3 tools/brand.py` writes the SVGs (`--check` says if one is out of date), `node tools/export-branding.mjs [project]` the PNGs.
3. `python3 tools/sync_branding.py ../<repository>` copies them into a project's checkout, at the paths it reads them from (its table, `TARGETS`); `boreale-site` takes every mark for the sites' menus. A pull request in each repository then carries them.

What a repository draws only for itself stays its own: PlayGuard's store pictures and splash screens, the Home Assistant logos, Aurore's platform icons (rendered from its kit icon by its `tools/render_icons.mjs`), the themes' pictures.

- **Always on the night.** The mark stands on the night's blue; on a light ground it keeps its dark tile.
- **One gradient, one direction.** Aurora green top left, violet bottom right. Never reversed, no colour added.
- **Room around it**: a quarter of its width at least.

## The colours

| Name | Hex | For |
|---|---|---|
| Abyss | `#0B1424` | Dark page grounds |
| Night | `#0E1A33` | Tiles, cards, inside the marks |
| Snow | `#E8EEF7` | Text on the night, the drawings in the marks |
| Mist | `#A9B6CC` | Secondary text |
| Aurora | `#00FFCC` | Accent, active state |
| Ice | `#33BBFF` | Links, the gradient's middle |
| Violet | `#8A5CFF` | The gradient's end |

The gradient: aurora at 0 %, ice at 55–65 %, violet at 100 %. On a page, about 60 % abyss, 20 % night, 12 % snow, 6 % aurora: the night takes the room, the aurora comes in touches.

## The type

- **Sora** (600–700, tracking −2 to −3 %): names, headings, figures. Already PlayGuard's and PlayShelf's wordmarks.
- **Figtree** (400–600): running text.
- **JetBrains Mono** (400–500): addresses, commands, versions, labels.

All three under the SIL Open Font License, served with the site (`site/assets/fonts/`), never from a font service. The sites' language menus add a fourth, for their flags only: `twemoji-flags.woff2`, the fifteen cut out of Twemoji's (CC-BY 4.0), served the same way.

## The tone

Calm and precise, like a friend who knows their console. Say what a feature gives the person, not how it is built; say plainly what the projects do not do (no piracy, no service that distributes games without the rights) and the risks (custom firmware, at your own risk). One aurora per page, no more.

- Yes: *No phone app. No Nintendo account. No internet.* · *Your game library, on the console.*
- No: *The ultimate next-gen Switch experience!* · *Unlock unlimited free games.*
