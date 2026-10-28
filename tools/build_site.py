#!/usr/bin/env python3
"""Builds boreale.dev into <out-dir> (site/README.md).

    python3 tools/build_site.py <out-dir>

site/template.html is the page around site/hero.html and site/home.html (the
home page: its hero under the aurora, then the rest), site/legal.html (legal/:
privacy and legal notice) or site/lost.html (404.html); each {{key}} is the
key's text in the language's catalog, site/i18n/<language>.json. English is at
the root, French in fr/.

The projects' releases come from GitHub's API at each build: the latest
version on each card, the latest releases on the home page and in feed.atom.
GITHUB_TOKEN, when set, lifts the API's rate limit; SITE_OFFLINE=1 builds
without them (the cards then show no version, the home page no releases).
SITE_STRICT=1 fails the build when they cannot be read, rather than publish
a site without them (main's workflow: the site already served stays).
SITE_URL is the site's address (https://boreale.dev/ by default).
build.sha256 is a hash of everything built, for the workflow to tell whether
a scheduled build has anything new to publish.
"""
import hashlib
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
SUMMARY_LENGTH = 280  # a release's lede, at most (feed.atom, the home page)

# Each project: its repository, and where its card leads per language: its
# site at its sub-domain of boreale.dev, and its simulator or demo there.
PROJECTS = {
    "playguard": {"name": "PlayGuard", "repo": "PlayGuard",
                  "url": {"en": "https://guard.boreale.dev/", "fr": "https://guard.boreale.dev/fr/"},
                  "try": {"en": "https://guard.boreale.dev/simulator/?lang=en-US",
                          "fr": "https://guard.boreale.dev/simulator/?lang=fr"}},
    "playshelf": {"name": "PlayShelf", "repo": "PlayShelf",
                  "url": {"en": "https://shelf.boreale.dev/", "fr": "https://shelf.boreale.dev/fr/"},
                  "try": {"en": "https://shelf.boreale.dev/simulator/?lang=en-US",
                          "fr": "https://shelf.boreale.dev/simulator/?lang=fr"}},
    "aurore": {"name": "Aurore", "repo": "Aurore",
               "url": {"en": "https://aurore.boreale.dev/", "fr": "https://aurore.boreale.dev/fr/"},
               "try": {"en": "https://aurore.boreale.dev/demo/", "fr": "https://aurore.boreale.dev/demo/?lang=fr"}},
}

# The pages other than 404.html, by their path under each language's folder.
PAGES = {"": "home.html", "legal/": "legal.html"}

MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
}

LOCALES = {}  # each language's og:locale (its catalog's og_locale), at main()

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
        except Exception as error:  # the site still builds, without them, unless strict
            if os.environ.get("SITE_STRICT") == "1":
                sys.exit(f"build_site: {project['name']}'s releases not read ({error}), nothing built")
            print(f"build_site: {project['name']}'s releases not read ({error})", file=sys.stderr)
            continue
        for r in listed:
            if r.get("draft") or r.get("prerelease") or not r.get("published_at"):
                continue
            found.append({
                "project": key, "name": project["name"], "version": r["tag_name"].lstrip("v"),
                "url": r["html_url"], "date": datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")),
                "summary": summary(r.get("body") or ""),
            })
    return sorted(found, key=lambda r: r["date"], reverse=True)


def summary(notes: str) -> str:
    """A release in a few words, as plain text: the first paragraph of its
    notes (Markdown) that is only text, the projects' highlights' lede, not
    their headings, download links (HTML), lists or quotes."""
    notes = re.sub(r"<!--.*?-->", " ", notes.replace("\r\n", "\n"), flags=re.S)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", notes)]
    text = next((p for p in paragraphs if p and not re.match(r"(#|<|>|[-*+]\s|\||!\[|---|\d+\.\s)", p)), "")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)  # images: nothing
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # [text](link): its text
    text = " ".join(re.sub(r"[`*_]", "", text).split())
    if len(text) > SUMMARY_LENGTH:
        text = text[:SUMMARY_LENGTH].rsplit(" ", 1)[0] + " …"
    return text


def day(date: datetime, language: str) -> str:
    month = MONTHS[language][date.month - 1]
    return f"{date.day} {month} {date.year}"


def news(found: list, language: str, catalog: dict, root: str) -> str:
    """The home page's latest releases, or nothing without any."""
    if not found:
        return ""
    items = "".join(
        f'<li><img src="{root}assets/marks/{r["project"]}.svg" alt="" width="28" height="28">'
        f'<a href="{html.escape(r["url"])}">{r["name"]} {html.escape(r["version"])}</a>'
        f'<time datetime="{r["date"].date().isoformat()}">{day(r["date"], language)}</time>'
        # The notes are in English: their lede only on the English page.
        + (f'<p>{html.escape(r["summary"])}</p>' if r["summary"] and language == "en" else "") + "</li>"
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


def attribute(text: str) -> str:
    """A text for a double-quoted attribute (the apostrophes left as they are)."""
    return html.escape(text, quote=False).replace('"', "&quot;")


def indexing(url: str, path: str, lost: bool) -> str:
    """The canonical address and the other languages' for search engines; a
    page that is not there (404.html) is kept out of their index instead."""
    if lost:
        return '<meta name="robots" content="noindex">'
    lines = [f'<link rel="canonical" href="{url}">']
    lines += [f'<link rel="alternate" hreflang="{lang}" href="{address(lang, path)}">' for lang in LANGUAGES]
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{address(LANGUAGES[0], path)}">')
    return "\n".join(lines)


def folder(language: str) -> str:
    """A language's folder: none for the first one, at the root."""
    return "" if language == LANGUAGES[0] else f"{language}/"


def address(language: str, path: str = "") -> str:
    """A page's address in a language (its home page without a path)."""
    return SITE_URL + folder(language) + path


def page(language: str, catalog: dict, hero: str, body: str, root: str, url: str, title: str,
         found: list, path: str = "", first_visit: bool = False, lost: bool = False) -> str:
    values = dict(catalog)
    # The catalogs' texts may hold HTML (hero_title's <em>), but these two are
    # also in attributes (content="..."): plain text, escaped.
    values["description"] = attribute(catalog["description"])
    title = attribute(title)
    latest = {}
    for r in found:
        latest.setdefault(r["project"], r["version"])
    for key, project in PROJECTS.items():
        values[f"{key}_url"] = project["url"][language]
        values[f"{key}_try"] = project["try"][language]
        values[f"{key}_version"] = (f' · <span class="version">{html.escape(latest[key])}</span>' if key in latest
                                    else f' · {catalog["no_release"]}' if found else "")
    # The header's language link leads to the same page in the other language.
    values["other_href"] = folder(catalog["other_lang"]) + path
    # The root's home page sends a first visit to the browser's language (assets/lang.js).
    values["first_visit"] = " data-first-visit" if first_visit else ""
    # 404.html at the root sends a visitor reading another language to that
    # language's (assets/lang.js); the site's address path tells it where.
    values["lost"] = f' data-lost="{root}"' if lost and language == LANGUAGES[0] else ""
    values["indexing"] = indexing(url, path, lost)
    values["og_alternates"] = "\n".join(
        f'<meta property="og:locale:alternate" content="{LOCALES[lang]}">' for lang in LANGUAGES if lang != language)
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
        f"    <updated>{r['date'].isoformat()}</updated>\n"
        + (f"    <summary>{html.escape(r['summary'])}</summary>\n" if r["summary"] else "")
        + "  </entry>\n"
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


def security(now: datetime) -> str:
    """.well-known/security.txt (RFC 9116): where to report a flaw privately.
    It expires a year after the month it was built in, so that a daily build
    changes it only once a month."""
    expires = now.replace(year=now.year + 1, month=now.month, day=1, hour=0, minute=0, second=0, microsecond=0)
    return (f"Contact: https://github.com/{OWNER}/boreale/security/advisories/new\n"
            f"Expires: {expires.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
            "Preferred-Languages: en, fr\n"
            f"Canonical: {SITE_URL}.well-known/security.txt\n")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    out = Path(sys.argv[1])
    found = releases()  # first: a strict build that fails leaves <out-dir> as it was
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SITE / "assets", out / "assets")

    hero = (SITE / "hero.html").read_text(encoding="utf-8")
    bodies = {path: (SITE / name).read_text(encoding="utf-8") for path, name in PAGES.items()}
    lost = (SITE / "lost.html").read_text(encoding="utf-8")
    base = urlparse(SITE_URL).path  # 404.html is served at any depth
    catalogs = {lang: json.loads((SITE / "i18n" / f"{lang}.json").read_text(encoding="utf-8")) for lang in LANGUAGES}
    LOCALES.update({lang: catalog["og_locale"] for lang, catalog in catalogs.items()})
    for lang, catalog in catalogs.items():
        for path, body in bodies.items():
            where = folder(lang) + path
            root = "../" * where.count("/")
            home = not path
            (out / where).mkdir(parents=True, exist_ok=True)
            (out / where / "index.html").write_text(
                page(lang, catalog, hero if home else "", body, root, SITE_URL + where,
                     catalog["title"] if home else catalog[f"{path.strip('/')}_page_title"], found, path=path,
                     first_visit=home and lang == LANGUAGES[0]),
                encoding="utf-8")
        # 404.html for each language: GitHub Pages serves the root's at any
        # address, which sends a visitor reading another language to theirs.
        (out / folder(lang) / "404.html").write_text(
            page(lang, catalog, "", lost, base, SITE_URL, catalog["lost_page_title"], found, lost=True),
            encoding="utf-8")
    first = catalogs[LANGUAGES[0]]

    (out / "feed.atom").write_text(feed(found, first), encoding="utf-8")
    (out / "manifest.webmanifest").write_text(manifest(first), encoding="utf-8")
    shutil.copy(SITE / "assets" / "favicon.ico", out / "favicon.ico")  # asked for at the root by old browsers
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    (out / ".well-known").mkdir()
    (out / ".well-known" / "security.txt").write_text(security(datetime.now(timezone.utc)), encoding="utf-8")
    # Each page in each language, with every language's (search engines read hreflang there too).
    urls = ""
    for path in PAGES:
        alternates = "".join(
            f'    <xhtml:link rel="alternate" hreflang="{lang}" href="{address(lang, path)}"/>\n' for lang in LANGUAGES)
        urls += "".join(f"  <url>\n    <loc>{address(lang, path)}</loc>\n{alternates}  </url>\n" for lang in LANGUAGES)
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
        f' xmlns:xhtml="http://www.w3.org/1999/xhtml">\n{urls}</urlset>\n', encoding="utf-8")
    (out / ".nojekyll").touch()
    # What was built, as one hash: the scheduled builds publish only when it
    # differs from the one served (.github/workflows/site.yml).
    digest = hashlib.sha256()
    for path in sorted(p for p in out.rglob("*") if p.is_file()):
        digest.update(path.relative_to(out).as_posix().encode() + b"\0" + path.read_bytes())
    (out / "build.sha256").write_text(digest.hexdigest() + "\n", encoding="utf-8")
    print(f"build_site: {', '.join(LANGUAGES)} in {out} for {SITE_URL}, {len(found)} release(s)")


if __name__ == "__main__":
    main()
