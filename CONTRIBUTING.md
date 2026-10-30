# Contributing

Boréale's site and brand: a change is a pull request against `main`, its title a conventional commit with a scope (`feat(site): …`, `fix(branding): …`), its description following `.github/pull_request_template.md`. CI builds and checks each one (`.github/workflows/site.yml`).

## Before a pull request

What Boréale's sites share (the languages, the header's menus, the rules for links out, the fonts and marks) is [boreale-site](https://github.com/JigSawFr/boreale-site), the submodule `library/boreale-site`: clone with `--recurse-submodules`, or `git submodule update --init` after. A change to it goes there first.

```sh
SITE_OFFLINE=1 python3 tools/build_site.py build   # without GitHub's API
python3 tools/check_site.py build
python3 library/boreale-site/tools/site_layout.py build   # Playwright for Python; else CI runs it
```

Then a look at the pages (`python3 -m http.server -d build 8000`) on a phone and a desktop.

## A text

Every text is in `site/i18n/<language>.json`: a key added to `en.json` is added, translated, to all fifteen catalogs (`check_site.py` fails otherwise), with the apps' names for their screens and features and each language's typography (`site/README.md`). `title` and `description` are plain text (they are attributes too); the others may hold HTML.

## A language

The site has the consoles' fifteen, as the apps and the projects' sites do. A new one is added to every site at once, in boreale-site (`LANGUAGES`, `FLAGS`, `OG_LOCALES`, `MONTHS`/`DATES`, `assets/lang.js`, the flags' font, its common catalog), then here: its catalog in `site/i18n/`; the header's menu, its `<link hreflang>` and the sitemap come with it. The projects' sites have the same folders, which the menu of Boréale's sites and the cards lead to.

## A mark

The SVGs in `branding/` are the sources: `python3 tools/make_banners.py` writes the projects' banners from them, then `node tools/export-branding.mjs` renders the PNGs and the site's icons again (Playwright). The PNGs go in the same pull request as their SVG.

## What the site does not do

No script, style, font or image from another site, no inline script or style (the Content-Security-Policy refuses them), no cookie, nothing that follows a visitor from one site to another.
