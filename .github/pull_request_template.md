<!--
The title is a conventional commit with a scope (feat(site): …, fix(branding): …).
-->

## What this changes, and why

<!-- The diff says what; this says what it is for. -->

## How it was verified

<!-- Beyond CI: the pages looked at, on a phone and a desktop. -->

## Checklist

- [ ] `python3 tools/build_site.py build && python3 tools/check_site.py build` pass
- [ ] `library/boreale-site/tools/site_layout.py build` passes, or CI runs it (Playwright, axe-core)
- [ ] A text added to `en.json` is in all 15 catalogs (`site/i18n/`), translated
- [ ] A mark changed: its PNGs rendered again (`node tools/export-branding.mjs`)
