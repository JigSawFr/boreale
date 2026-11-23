<!--
The title is a conventional commit with a scope: feat(site): …, fix(branding): …, docs(github): …
-->

## ✨ At a glance

<!-- One or two sentences: what a visitor or a maintainer sees differently after this change. -->

## 💡 Why

<!-- The reason the change is needed. The diff says what; this says what it is for. -->

## 🔧 What changes

<!-- The main parts of the diff, in a short list. Name any page, mark or catalog touched. -->

-

## 🖼️ Before / After

<!-- For a visual change only: the same page or mark, before and after, phone (390 px) and desktop (1280 px). Delete the table otherwise. -->

| | Before | After |
|---|---|---|
| Phone (390 px) | | |
| Desktop (1280 px) | | |

## ✅ Checked

CI already runs the build, the brand check (`tools/brand.py --check`), the site check (`tools/check_site.py`) and the layout check (Playwright, axe-core).

Not covered by CI, checked by hand:

- [ ] A mark changed: its PNGs rendered again with `node tools/export-branding.mjs`, in this pull request
- [ ] A page changed: looked at on a phone and a desktop, screenshots above
- [ ] A new text: translated into the fifteen catalogs, and the translation reads naturally
