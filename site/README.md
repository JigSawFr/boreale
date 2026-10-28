# The website

Boréale's website, <https://boreale.dev/>: the projects, what they share, what they do not do. English at the root, French in `/fr/`; one dark look (the brand stands on the night, `branding/README.md`).

A first visit to the root goes to the browser's language when the site has it; the header's language link changes it, and the choice is kept (`assets/lang.js`, `boreale-lang` in the browser's storage).

## How it is made

`tools/build_site.py <out-dir>` (Python 3, nothing to install) writes the pages:

- `template.html`: the page around the content (head, header, footer). Its aurora (`hero.html` under it) is `canvas#sky`, drawn by `assets/site.js` at 30 frames a second, and not at all while it is scrolled out of view; without script, or with less motion asked, `assets/site.css`'s gradient or a still frame stands in.
- `home.html` and `hero.html`: the home page; `lost.html`: `404.html` in each language, kept out of search engines. GitHub Pages serves the root's at any address; it sends a visitor to the French one when the address is in `/fr/`, or French was chosen, or the browser prefers it (`assets/lang.js`).
- `i18n/<language>.json`: each `{{key}}`'s text, one catalog per language (`en.json` the reference). A new language is a catalog and its entry in `LANGUAGES`.
- The projects' links are in `build_site.py` (`PROJECTS`): PlayGuard at `guard.boreale.dev`, PlayShelf at `shelf.boreale.dev`, Aurore at `aurore.boreale.dev`.
- **The projects' releases**, read from GitHub's API at each build: the latest version on each card, the five latest releases on the home page, the last twenty in `feed.atom` with the start of their notes. `GITHUB_TOKEN` lifts the API's anonymous limit; `SITE_OFFLINE=1` builds without them (no version, no releases section); `SITE_STRICT=1` fails when they cannot be read rather than build without them (main's workflow).
- **For search engines**: schema.org data on each page (Boréale, its site, each project and its latest version), each page's languages (`hreflang`, in the pages and in `sitemap.xml`), `robots.txt`, the social preview with its locales; `manifest.webmanifest` and `favicon.ico` (written by `tools/export-branding.mjs`) for browsers.
- `assets/`: the CSS, the script, the marks, the icons, the social preview and the fonts (SIL Open Font License), served with the site so that no visitor's browser loads anything from anyone else.
- **The audience**, counted by Umami Cloud (<https://cloud.umami.is>): `assets/umami.js` is its tracker, served with the site, that sends each page seen to `gateway.umami.is`, without cookie, and only from `boreale.dev` (not from a preview or a local copy). It is a copy: take it again from <https://cloud.umami.is/script.js> when Umami changes it.
- A **Content-Security-Policy** on every page (a `<meta>`: GitHub Pages sends no headers): only the site's own files, no inline script or style; the one address it may send to is Umami's (`connect-src`).
- `SITE_URL` is the site's address (`https://boreale.dev/` by default).
- `build.sha256`: a hash of everything built, for the workflow to tell whether a scheduled build has anything new.

## Checks

- `tools/check_site.py <site>`: the catalogs have the same keys, no `{{key}}` is left, every link to the site and every `#anchor` leads somewhere, nothing the Content-Security-Policy blocks is on a page, and the schema.org data, the feed and the manifest read.
- `tools/site_layout.py <site>` (Playwright for Python): every page on two phones, a phone in landscape, a tablet and a desktop: none wider than the screen, no target under 24px, no script that throws, and nothing axe-core finds against WCAG 2.2 AA (`SITE_AXE=<axe.min.js>`).

## Publishing

`.github/workflows/site.yml` builds and checks the site for each pull request and for main, and publishes main's on GitHub Pages. It runs again once a day, and on a `repository_dispatch` of type `release`, so the versions follow the projects' releases (those publish only when the site built differs from the one served, by `build.sha256`; on main, releases GitHub cannot give fail the build, and the site served stays): a project's release workflow can send one with a token allowed to (`gh api repos/JigSawFr/boreale/dispatches -f event_type=release`).

Once, in the repository's settings: *Pages › Build and deployment › Source: GitHub Actions*, then *Custom domain: boreale.dev* and *Enforce HTTPS*. At the registrar, the apex's `A` and `AAAA` records point to GitHub Pages, and `www` is a `CNAME` to `jigsawfr.github.io`.
