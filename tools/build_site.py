#!/usr/bin/env python3
"""Builds boreale.dev into <out-dir> (site/README.md).

    python3 tools/build_site.py <out-dir>

site/template.html is the page around site/hero.html and site/home.html (the
home page: its hero under the aurora, then the rest) or site/lost.html
(404.html); each {{key}} is the key's text in the language's catalog,
site/i18n/<language>.json. English is at the root, French in fr/.
SITE_URL is the site's address (https://boreale.dev/ by default).
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SITE_URL = os.environ.get("SITE_URL", "https://boreale.dev/").rstrip("/") + "/"
LANGUAGES = ["en", "fr"]  # the first one at the root

# Where each project's card leads, per language. Their sites move to
# guard., shelf. and aurore.boreale.dev once those are served.
PROJECTS = {
    "playguard_url": {"en": "https://playguard.link/", "fr": "https://playguard.link/fr/"},
    "playshelf_url": {"en": "https://jigsawfr.github.io/PlayShelf/", "fr": "https://jigsawfr.github.io/PlayShelf/fr/"},
    "aurore_url": {"en": "https://github.com/JigSawFr/Aurore", "fr": "https://github.com/JigSawFr/Aurore"},
}

KEY = re.compile(r"\{\{([a-z0-9_]+)\}\}")


def fill(text: str, values: dict) -> str:
    def one(match):
        key = match.group(1)
        if key not in values:
            sys.exit(f"build_site: no text for {{{{{key}}}}}")
        return values[key]
    # Twice: a text may hold a key ({{root}} in home.html's links).
    return KEY.sub(one, KEY.sub(one, text))


def page(language: str, catalog: dict, hero: str, body: str, root: str, url: str, title: str,
         first_visit: bool = False) -> str:
    values = dict(catalog)
    # The root's home page sends a first visit to the browser's language (assets/lang.js).
    values["first_visit"] = " data-first-visit" if first_visit else ""
    values.update({k: v[language] for k, v in PROJECTS.items()})
    values.update(root=root, site=SITE_URL, url=url, title=title)
    values["hero"] = fill(hero, values)
    values["body"] = fill(body, values)
    return fill((SITE / "template.html").read_text(encoding="utf-8"), values)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1])
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SITE / "assets", out / "assets")

    hero = (SITE / "hero.html").read_text(encoding="utf-8")
    home = (SITE / "home.html").read_text(encoding="utf-8")
    lost = (SITE / "lost.html").read_text(encoding="utf-8")
    base = urlparse(SITE_URL).path  # 404.html is served at any depth
    catalogs = {lang: json.loads((SITE / "i18n" / f"{lang}.json").read_text(encoding="utf-8")) for lang in LANGUAGES}
    for lang, catalog in catalogs.items():
        folder = "" if lang == LANGUAGES[0] else f"{lang}/"
        root = "../" * folder.count("/")
        (out / folder).mkdir(parents=True, exist_ok=True)
        (out / folder / "index.html").write_text(
            page(lang, catalog, hero, home, root, SITE_URL + folder, catalog["title"], first_visit=not folder),
            encoding="utf-8")
    first = catalogs[LANGUAGES[0]]
    (out / "404.html").write_text(page(LANGUAGES[0], first, "", lost, base, SITE_URL, first["lost_page_title"]), encoding="utf-8")

    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    urls = "".join(
        f"  <url><loc>{SITE_URL}{'' if lang == LANGUAGES[0] else lang + '/'}</loc></url>\n" for lang in LANGUAGES)
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")
    (out / ".nojekyll").touch()
    print(f"build_site: {', '.join(LANGUAGES)} in {out} for {SITE_URL}")


if __name__ == "__main__":
    main()
