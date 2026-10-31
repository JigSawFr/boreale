# Boréale's brand

The look shared by Boréale and its projects. PlayGuard's and PlayShelf's own marks live in their repositories (`branding/`); they follow the same rules.

## The name

**Boréale** (with its accent; `boreale` in addresses and code). It closes a line already in the code: [borealis](https://github.com/natinusala/borealis), the UI library, then **Aurore**, its fork, the light rising on it, then **Boréale**, the whole sky the projects live in. The projects keep their names: Boréale is the house, not a new name for them.

The tagline is **Homebrew for the long nights** (*Du homebrew pour les longues nuits*): boreal nights last for months, and so do evenings of play.

## The marks

Every mark follows one rule, set by PlayGuard's and PlayShelf's: **a frame in the aurora's colours around the night, one drawing in snow inside**.

| File | What | Where |
|---|---|---|
| `mark.svg` | The sky's circle, an aurora crossing it, the pole star | Headers, the site, avatars |
| `mark-small.svg` | The circle and the star, without the aurora | Under 24 px: favicons |
| `icon.svg` | The mark on the abyss, in a rounded tile | App and touch icons |
| `mark-mono-white.svg`, `mark-mono-black.svg` | The mark in one colour, the night left empty | What prints or engraves one ink, services that want a one-colour icon |
| `wordmark.svg`, `wordmark-light.svg` | "Boréale" in Sora 700, underlined by the aurora | On the night, on light grounds |
| `aurore-mark.svg` | Aurore's mark, drawn after its app icon: the frame, an aurora over the mountains | Aurore's card, its site |
| `social-preview.svg` | The night, the aurora, the mark, the name, the tagline | Shared links, GitHub's social preview |

`banners/` holds each project's README banner, all from one template (`python3 tools/make_banners.py`): the night, the aurora, the project's mark, its name, what it does, and "by Boréale" with the mark in a corner. PlayGuard and PlayShelf keep a copy of theirs in their own `branding/`, rendered for their README at twice the size; Aurore's README keeps a banner of its own, and boreale-ha's a two-line one ("Boréale / for Home Assistant").

`png/` holds them rendered (`node tools/export-branding.mjs`, which also writes the site's icons and preview).

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
