# The website

Boréale's website, <https://boreale.dev/>: the projects, what they share, what they do not do. English at the root, French in `/fr/`; one dark look (the brand stands on the night, `branding/README.md`).

## How it is made

`tools/build_site.py <out-dir>` (Python 3, nothing to install) writes the pages:

- `template.html`: the page around the content (head, header, footer). Its aurora (`hero.html` under it) is `canvas#sky`, drawn by `assets/site.js`; without script, or with less motion asked, `assets/site.css`'s gradient or a still frame stands in.
- `home.html` and `hero.html`: the home page; `lost.html`: `404.html`, served at any address.
- `i18n/<language>.json`: each `{{key}}`'s text, one catalog per language (`en.json` the reference). A new language is a catalog and its entry in `LANGUAGES`.
- The projects' links are in `build_site.py` (`PROJECTS`): they move to `guard.`, `shelf.` and `aurore.boreale.dev` once those are served.
- `assets/`: the CSS, the script, the marks, the icons, the social preview and the fonts (SIL Open Font License), served with the site so that no visitor's browser asks anyone else for anything.
- A **Content-Security-Policy** on every page (a `<meta>`: GitHub Pages sends no headers): only the site's own files, no inline script or style.
- `SITE_URL` is the site's address (`https://boreale.dev/` by default).

## Checks

`tools/check_site.py <site>`: the catalogs have the same keys, no `{{key}}` is left, every link to the site and every `#anchor` leads somewhere, and nothing the Content-Security-Policy blocks is on a page.

## Publishing

`.github/workflows/site.yml` builds and checks the site for each pull request and for main, and publishes main's on GitHub Pages.

Once, in the repository's settings: *Pages › Build and deployment › Source: GitHub Actions*, then *Custom domain: boreale.dev* and *Enforce HTTPS*. At the registrar, the apex's `A` and `AAAA` records point to GitHub Pages, and `www` is a `CNAME` to `jigsawfr.github.io`.
