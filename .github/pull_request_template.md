<!--
The title is a conventional commit with a scope (feat(site): …, fix(branding): …).
-->

## What this changes, and why

<!-- The diff says what; this says what it is for. -->

## How it was verified

<!-- Beyond CI: the pages looked at, on a phone and a desktop. -->

## Checklist

- [ ] `python3 tools/build_site.py build && python3 tools/check_site.py build` pass
- [ ] A text added to one catalog (`site/i18n/`) is in every one
- [ ] A mark changed: its PNGs rendered again (`node tools/export-branding.mjs`)
