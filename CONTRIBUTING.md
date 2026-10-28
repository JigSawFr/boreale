# Contributing

Boréale's site and brand: a change is a pull request against `main`, its title a conventional commit with a scope (`feat(site): …`, `fix(branding): …`), its description following `.github/pull_request_template.md`. CI builds and checks each one (`.github/workflows/site.yml`).

## Before a pull request

```sh
SITE_OFFLINE=1 python3 tools/build_site.py build   # without GitHub's API
python3 tools/check_site.py build
python3 tools/site_layout.py build                 # Playwright for Python; else CI runs it
```

Then a look at the pages (`python3 -m http.server -d build 8000`) on a phone and a desktop.

## A text

Every text is in `site/i18n/<language>.json`: a key added to `en.json` is added to every catalog (`check_site.py` fails otherwise). `title` and `description` are plain text (they are attributes too); the others may hold HTML.

## A language

A new catalog in `site/i18n/`, its code in `LANGUAGES` (`tools/build_site.py`) and in `SITE` (`site/assets/lang.js`), and its `<link hreflang>` comes with it. The header's link goes to the other language: with a third, the header needs a choice of them.

## A mark

The SVGs in `branding/` are the sources: `python3 tools/make_banners.py` writes the projects' banners from them, then `node tools/export-branding.mjs` renders the PNGs and the site's icons again (Playwright). The PNGs go in the same pull request as their SVG.

## What the site does not do

No script, style, font or image from another site, no inline script or style (the Content-Security-Policy refuses them), no cookie, nothing that follows a visitor from one site to another.
