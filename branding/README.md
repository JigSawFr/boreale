# Boréale's brand

The look shared by Boréale and its projects, kept here once: every project's mark, icon, wordmarks, README banner and social preview, from one set of templates, copied into the projects' repositories from here.

## The kit

Every mark follows one rule, set by PlayGuard's and PlayShelf's: **a frame in the aurora's colours around the night, one drawing in snow inside**.

One folder per product: `boreale`, `playguard`, `playshelf`, `aurore`, `ha` (Boréale for Home Assistant), `atlas`. Each holds the same files:

| File | What | Where |
|---|---|---|
| `mark.svg` | **Drawn by hand.** The frame and the drawing, flat | Headers, site menus, cards, favicons, the banner |
| `mark-small.svg` | The mark under 24 px: a heavier frame and drawing, no aurora | Favicons (`favicon.ico` is drawn from it) |
| `mark-mono-white.svg`, `mark-mono-black.svg` | The mark in one ink, the night left empty | What prints or engraves one colour; Android's themed icon; Home Assistant's monochrome icons |
| `icon.svg` | The mark's frame around a night sky: the aurora's curtain and line, the mountains for some, the drawing in snow with a soft glow. Full-bleed | App, store and touch icons; the console's where there is no `icon-console.svg`, the social preview |
| `icon-console.svg` | Switch homebrews only (PlayGuard, PlayShelf): the night sky and the aurora over the whole square, the mark lifted by a shadow, the name in Sora 700 beneath, as the console's other homebrews show theirs. Full-bleed | The HOME menu icon (`png/icon-256.jpg`, the repository's `icon.jpg`) |
| `wordmark.svg`, `wordmark-light.svg` | The name in Sora 700, underlined by the aurora, in snow or in night | Loading screens, on the night, on light grounds |
| `banner.svg` | The night, the aurora, the mark, the name, what it does, "by Boréale" in a pill ("part of Boréale" for a tool) | The README's top |
| `social-preview.svg` | The aurora's curtain, the icon, the name, what it does, what it has, "by Boréale" | GitHub's social preview (Settings › General), the site's `og:image` |
| `png/` | All of them rendered: `icon-{1024,512,256,192}.png`, `icon-256.jpg` (the Switch's homebrew icon, from `icon-console.svg` where there is one), `apple-touch-icon.png`, `icon-tile-{512,256}.png` (rounded on a transparent ground, where nothing rounds it), `mark-{512,256}.png`, `mark-mono-{white,black}-512.png`, `wordmark{,-light}.png` (720 × 176), `banner.png` (2560 × 640), `social-preview.png` (1280 × 640), `favicon.ico` (16, 32, 48) | |

The tools, `kit` (boreale-kit) and `link` (boreale-link), are parts of the products, not brands of their own: a mark, a banner and a social preview saying "part of Boréale", rendered to `mark-{512,256}.png`, `banner.png` and `social-preview.png`; no icon, wordmark nor favicon. `lantern` (Lantern), `sdk` (Lantern SDK) and `bridge` (Lantern Bridge) are brands with their own site (decision of 2026-11-06): icon, wordmark and favicon like the products; the menus show them, not the tools.

Boréale's own `mark-small.svg` (the circle and the star) and `mark-mono-*.svg` are drawn by hand; the other products' are written by `tools/brand.py`. At the root, `tokens.json` (`schema` 1) and `tokens.css` hold the colours, the gradient, the fonts and the contrasts below, for the sites and the themes to read instead of copying them; `aurora-loader.svg` (the loading animation: three curtains of the gradient swaying, 3 s loop, still under `prefers-reduced-motion`, for the apps' loading and splash screens and the sites' waits); and `badge-ai.svg` ("human-led · AI-assisted", the projects' README badge linking to boreale.dev's `how/`).

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

What may sit on what (WCAG contrast; `tokens.json` has the ratios):

| Ink | On abyss | On night | Use |
|---|---|---|---|
| Snow | 15.8 | 14.8 | Any text |
| Mist | 9.0 | 8.4 | Secondary text |
| Aurora | 14.2 | 13.3 | Accent, active state, short text |
| Ice | 8.5 | 8.0 | Links |
| Violet | 4.4 | 4.2 | **Large text and graphics only**, never a paragraph |

Abyss on snow (15.8) and on aurora (14.2) read too: the ink of a light ground or of a button.

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
