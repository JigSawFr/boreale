#!/usr/bin/env python3
"""Builds boreale.dev into <out-dir> (site/README.md).

    python3 tools/build_site.py <out-dir>

site/template.html is the page around site/hero.html and site/home.html (the
home page: its hero under the aurora, then the rest) or site/lost.html
(404.html); each {{key}} is the key's text in the language's catalog,
site/i18n/<language>.json. English is at the root, French in fr/.

The projects' releases come from GitHub's API at each build: the latest
version on each card, the latest releases on the home page and in feed.atom.
GITHUB_TOKEN, when set, lifts the API's rate limit; SITE_OFFLINE=1 builds
without them (the cards then show no version, the home page no releases).
SITE_URL is the site's address (https://boreale.dev/ by default).
"""
import html
import json
import os
import re
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SITE_URL = os.environ.get("SITE_URL", "https://boreale.dev/").rstrip("/") + "/"
LANGUAGES = ["en", "fr"]  # the first one at the root
OWNER = "JigSawFr"
RELEASES_SHOWN = 5

# Each project: its repository, and where its card leads per language. Their
# sites move to guard., shelf. and aurore.boreale.dev once those are served.
PROJECTS = {
    "playguard": {"name": "PlayGuard", "repo": "PlayGuard",
                  "url": {"en": "https://playguard.link/", "fr": "https://playguard.link/fr/"}},
    "playshelf": {"name": "PlayShelf", "repo": "PlayShelf",
                  "url": {"en": "https://jigsawfr.github.io/PlayShelf/", "fr": "https://jigsawfr.github.io/PlayShelf/fr/"}},
    "aurore": {"name": "Aurore", "repo": "Aurore",
               "url": {"en": "https://github.com/JigSawFr/Aurore", "fr": "https://github.com/JigSawFr/Aurore"}},
}

MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
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


def releases() -> list:
    """The projects' published releases, the newest first (none offline)."""
    if os.environ.get("SITE_OFFLINE") == "1":
        return []
    found = []
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "boreale-site"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    for key, project in PROJECTS.items():
        url = f"https://api.github.com/repos/{OWNER}/{project['repo']}/releases?per_page=10"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as answer:
                listed = json.load(answer)
        except Exception as error:  # the site still builds, without them
            print(f"build_site: {project['name']}'s releases not read ({error})", file=sys.stderr)
            continue
        for r in listed:
            if r.get("draft") or r.get("prerelease") or not r.get("published_at"):
                continue
            found.append({
                "project": key, "name": project["name"], "version": r["tag_name"].lstrip("v"),
                "url": r["html_url"], "date": datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")),
            })
    return sorted(found, key=lambda r: r["date"], reverse=True)


def day(date: datetime, language: str) -> str:
    month = MONTHS[language][date.month - 1]
    return f"{date.day} {month} {date.year}"


def news(found: list, language: str, catalog: dict, root: str) -> str:
    """The home page's latest releases, or nothing without any."""
    if not found:
        return ""
    items = "".join(
        f'<li><a href="{html.escape(r["url"])}">{r["name"]} {html.escape(r["version"])}</a>'
        f'<time datetime="{r["date"].date().isoformat()}">{day(r["date"], language)}</time></li>'
        for r in found[:RELEASES_SHOWN])
    return (f'<section id="releases">\n      <div class="section-head">\n'
            f'        <span class="eyebrow">{catalog["news_eyebrow"]}</span>\n'
            f'        <h2>{catalog["news_title"]}</h2>\n      </div>\n'
            f'      <ul class="releases">{items}</ul>\n'
            f'      <p class="feed"><a href="{root}feed.atom" type="application/atom+xml">{catalog["news_feed"]}</a></p>\n'
            f'    </section>')


def structured(language: str, catalog: dict, found: list) -> str:
    """schema.org data for search engines: Boréale and its projects."""
    latest = {}
    for r in found:
        latest.setdefault(r["project"], r["version"])
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": SITE_URL + "#boreale", "name": "Boréale", "url": SITE_URL,
             "logo": SITE_URL + "assets/icon-512.png", "sameAs": [f"https://github.com/{OWNER}"]},
            {"@type": "WebSite", "name": "Boréale", "url": SITE_URL, "inLanguage": language,
             "publisher": {"@id": SITE_URL + "#boreale"}},
        ],
    }
    for key, project in PROJECTS.items():
        item = {"@type": "SoftwareApplication" if key != "aurore" else "SoftwareSourceCode",
                "name": project["name"], "url": project["url"][language],
                "description": catalog[f"{key}_text"], "license": "https://www.gnu.org/licenses/gpl-3.0.html",
                "codeRepository" if key == "aurore" else "sameAs": f"https://github.com/{OWNER}/{project['repo']}",
                "publisher": {"@id": SITE_URL + "#boreale"}}
        if key != "aurore":
            item.update(applicationCategory="GameApplication", operatingSystem="Nintendo Switch (custom firmware)")
        if key in latest:
            item["softwareVersion"] = latest[key]
        data["@graph"].append(item)
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'<script type="application/ld+json">{text}</script>'


def page(language: str, catalog: dict, hero: str, body: str, root: str, url: str, title: str,
         found: list, first_visit: bool = False) -> str:
    values = dict(catalog)
    latest = {}
    for r in found:
        latest.setdefault(r["project"], r["version"])
    for key, project in PROJECTS.items():
        values[f"{key}_url"] = project["url"][language]
        values[f"{key}_version"] = f' · <span class="version">{html.escape(latest[key])}</span>' if key in latest else ""
    # The root's home page sends a first visit to the browser's language (assets/lang.js).
    values["first_visit"] = " data-first-visit" if first_visit else ""
    values.update(root=root, site=SITE_URL, url=url, title=title)
    values["news"] = news(found, language, catalog, root)
    values["jsonld"] = structured(language, catalog, found)
    values["hero"] = fill(hero, values)
    values["body"] = fill(body, values)
    return fill((SITE / "template.html").read_text(encoding="utf-8"), values)


def feed(found: list, catalog: dict) -> str:
    """feed.atom: the projects' releases, the newest first."""
    now = (found[0]["date"] if found else datetime.now(timezone.utc)).isoformat(timespec="seconds")
    entries = "".join(
        f"  <entry>\n    <title>{r['name']} {html.escape(r['version'])}</title>\n"
        f'    <link href="{html.escape(r["url"])}"/>\n    <id>{html.escape(r["url"])}</id>\n'
        f"    <updated>{r['date'].isoformat()}</updated>\n  </entry>\n"
        for r in found[:20])
    return ('<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">\n'
            f"  <title>Boréale</title>\n  <subtitle>{html.escape(catalog['feed_subtitle'])}</subtitle>\n"
            f'  <link href="{SITE_URL}"/>\n  <link rel="self" href="{SITE_URL}feed.atom"/>\n'
            f"  <id>{SITE_URL}</id>\n  <updated>{now}</updated>\n"
            f"  <author><name>{OWNER}</name></author>\n  <icon>{SITE_URL}assets/favicon.svg</icon>\n"
            f"{entries}</feed>\n")


def manifest(catalog: dict) -> str:
    return json.dumps({
        "name": "Boréale", "short_name": "Boréale", "description": catalog["description"],
        "start_url": "/", "display": "browser", "background_color": "#0b1424", "theme_color": "#0b1424",
        "icons": [{"src": "assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
                  {"src": "assets/favicon.svg", "sizes": "any", "type": "image/svg+xml"}],
    }, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1])
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SITE / "assets", out / "assets")
    found = releases()

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
            page(lang, catalog, hero, home, root, SITE_URL + folder, catalog["title"], found, first_visit=not folder),
            encoding="utf-8")
    first = catalogs[LANGUAGES[0]]
    (out / "404.html").write_text(
        page(LANGUAGES[0], first, "", lost, base, SITE_URL, first["lost_page_title"], found), encoding="utf-8")

    (out / "feed.atom").write_text(feed(found, first), encoding="utf-8")
    (out / "manifest.webmanifest").write_text(manifest(first), encoding="utf-8")
    shutil.copy(SITE / "assets" / "favicon.ico", out / "favicon.ico")  # asked for at the root by old browsers
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    urls = "".join(
        f"  <url><loc>{SITE_URL}{'' if lang == LANGUAGES[0] else lang + '/'}</loc></url>\n" for lang in LANGUAGES)
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")
    (out / ".nojekyll").touch()
    print(f"build_site: {', '.join(LANGUAGES)} in {out} for {SITE_URL}, {len(found)} release(s)")


if __name__ == "__main__":
    main()
