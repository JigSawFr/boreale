#!/usr/bin/env python3
"""Builds boreale.dev into <out-dir> (site/README.md).

    python3 tools/build_site.py <out-dir>

site/template.html is the page around site/hero.html and site/home.html (the
home page: its hero under the aurora, then the rest), site/legal.html (legal/:
privacy and legal notice) or site/lost.html (404.html); each {{key}} is the
key's text in the language's catalog, site/i18n/<language>.json. The
consoles' fifteen languages (LANGUAGES): English at the root, each other one
in its folder (fr/, fr-ca/, de/ ... zh-hant/).

site/support.html is support/: how to donate (GitHub Sponsors, Ko-fi) and
the hardware the donations buy to test on.

site/insights.html is insights/: a pointer to Atlas's own site
(https://atlas.boreale.dev/, ATLAS), where PlayInsights' data now lives,
kept so that its old links still lead somewhere.

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
# What Boréale's sites share (library/boreale-site, a submodule): the
# languages, the header's menus, the links out and their UTM tags, the
# common texts and assets.
sys.path.insert(0, str(ROOT / "library" / "boreale-site"))
import boreale_site as boreale  # noqa: E402
from boreale_site import CODES, OG_LOCALES, attribute, fill, folder, html_lang  # noqa: E402

BOREALE = boreale.Site("boreale", os.environ.get("SITE_URL"))
SITE_URL = BOREALE.url
# The language the legal texts are written in, the others translating it
# (legal_translation, said on the other languages' legal page).
ORIGINAL = "fr"
OWNER = "JigSawFr"
RELEASES_SHOWN = 5
# versions.json's schema: {"schema": 1, "projects": {project: "vX"}}, read by
# PlayGuard's, PlayShelf's and Aurore's builds (versions_of()), which also read
# the flat {project: "vX"} of before.
VERSIONS_SCHEMA = 1
SUMMARY_LENGTH = 280  # a release's lede, at most (feed.atom, the home page)

# Each project: its repository, its site at its sub-domain of boreale.dev
# (the same language folders as this one's), and its simulator or demo there.
PROJECTS = {
    "playguard": {"name": "PlayGuard", "repo": "PlayGuard", "site": "https://guard.boreale.dev/",
                  "try": "https://guard.boreale.dev/simulator/"},
    "playshelf": {"name": "PlayShelf", "repo": "PlayShelf", "site": "https://shelf.boreale.dev/",
                  "try": "https://shelf.boreale.dev/simulator/"},
    "aurore": {"name": "Aurore", "repo": "Aurore", "site": "https://aurore.boreale.dev/",
               "try": "https://aurore.boreale.dev/demo/"},
}
# The languages of Aurore's demo menu (web/page/index.html): for another one,
# the demo opens in the browser's language.
DEMO_LANGUAGES = {"fr", "de", "es", "it", "nl", "pt-BR", "ru", "ja", "ko", "zh-Hans", "zh-Hant"}


def project_url(key: str, language: str) -> str:
    """A project's site in a language: the same folder as this site's."""
    return PROJECTS[key]["site"] + folder(language)


def try_url(key: str, language: str) -> str:
    """A project's simulator (or Aurore's demo) in a language: the apps'
    codes (en-US for English)."""
    if key == "aurore":
        return PROJECTS[key]["try"] + (f"?lang={language}" if language in DEMO_LANGUAGES else "")
    return PROJECTS[key]["try"] + f"?lang={language}"


# The pages other than 404.html, by their path under each language's folder.
PAGES = {"": "home.html", "support/": "support.html", "legal/": "legal.html", "insights/": "insights.html"}

# Atlas, the open data PlayShelf reads (https://github.com/JigSawFr/Atlas),
# and Lantern, the protocol between library servers and console homebrews
# (https://github.com/JigSawFr/lantern): their own sites, each language in
# the same folder as here, under the home page's projects ("open data and
# protocols", lighter cards) with their explorer and specification.
ATLAS = "https://atlas.boreale.dev/"
LANTERN = "https://lantern.boreale.dev/"


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


def news(found: list, language: str, catalog: dict, root: str) -> str:
    """The home page's latest releases, or nothing without any: a list,
    drawn by site.css as a timeline (the dates beside a line of aurora, a
    dot on it for each release)."""
    if not found:
        return ""
    items = "".join(
        f'<li><img src="{root}assets/marks/{r["project"]}.svg" alt="" width="28" height="28">'
        f'<a href="{html.escape(r["url"])}">{r["name"]} {html.escape(r["version"])}</a>'
        f'<time datetime="{r["date"].date().isoformat()}">{boreale.day(r["date"], language)}</time>'
        # The notes are in English: their lede only on the English page.
        + (f'<p>{html.escape(r["summary"])}</p>' if r["summary"] and language == "en-US" else "") + "</li>"
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
            {"@type": "WebSite", "name": "Boréale", "url": SITE_URL, "inLanguage": html_lang(language),
             "publisher": {"@id": SITE_URL + "#boreale"}},
        ],
    }
    for key, project in PROJECTS.items():
        item = {"@type": "SoftwareApplication" if key != "aurore" else "SoftwareSourceCode",
                "name": project["name"], "url": project_url(key, language),
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
         found: list, path: str = "", first_visit: bool = False, lost: bool = False) -> str:
    values = dict(catalog)
    # The catalogs' texts may hold HTML (hero_title's <em>), but these two are
    # also in attributes (content="..."): plain text, escaped.
    values["description"] = attribute(catalog["description"])
    title = attribute(title)
    latest = {}
    for r in found:
        latest.setdefault(r["project"], r["version"])
    for key in PROJECTS:
        values[f"{key}_url"] = project_url(key, language)
        values[f"{key}_try"] = try_url(key, language)
        values[f"{key}_version"] = (f' · <span class="version">{html.escape(latest[key])}</span>' if key in latest
                                    else f' · {catalog["no_release"]}' if found else "")
    # The legal page's texts are translations of the French one, which
    # prevails: each other language says so under its lede, with a link to it.
    values["legal_translation"] = ("" if language == ORIGINAL else
                                   f'<p class="translation">{catalog["legal_translation"]}</p>')
    values["lang"] = html_lang(language)
    values["home"] = folder(language)
    values["og_locale"] = OG_LOCALES[language]
    # The header's languages: this page in each (none for 404.html, which
    # is at any address).
    values["languages"] = BOREALE.languages(language, catalog, root, path if not lost else "")
    # The root's home page sends a first visit to the browser's language (assets/lang.js).
    values["first_visit"] = " data-first-visit" if first_visit else ""
    # 404.html at the root sends a visitor reading another language to that
    # language's (assets/lang.js); the site's address path tells it where.
    values["lost"] = f' data-lost="{root}"' if lost and language == CODES[0] else ""
    values["indexing"] = BOREALE.indexing(language, path, lost)
    # The home page (the one with a hero): site.css's showcase, the night
    # going on down it.
    values["page_class"] = ' class="home"' if hero else ""
    values["og_alternates"] = "\n".join(
        f'<meta property="og:locale:alternate" content="{OG_LOCALES[code]}">' for code in CODES if code != language)
    values.update(root=root, site=SITE_URL, url=url, title=title)
    values["switcher"] = BOREALE.switcher(language, catalog, root, latest)
    values["audience"] = BOREALE.audience(root)
    values["news"] = news(found, language, catalog, root)
    values["atlas_url"] = ATLAS + folder(language)
    values["atlas_try"] = ATLAS + folder(language) + "explore/"
    values["lantern_url"] = LANTERN + folder(language)
    values["lantern_try"] = LANTERN + folder(language) + "spec/"
    values["jsonld"] = structured(language, catalog, found)
    values["hero"] = fill(hero, values)
    values["body"] = fill(body, values)
    return BOREALE.links_out(fill((SITE / "template.html").read_text(encoding="utf-8"), values))


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
    boreale.copy_assets(out)

    hero = (SITE / "hero.html").read_text(encoding="utf-8")
    bodies = {path: (SITE / name).read_text(encoding="utf-8") for path, name in PAGES.items()}
    lost = (SITE / "lost.html").read_text(encoding="utf-8")
    base = urlparse(SITE_URL).path  # 404.html is served at any depth
    catalogs = boreale.catalogs(SITE / "i18n")
    for lang, catalog in catalogs.items():
        for path, body in bodies.items():
            where = folder(lang) + path
            root = "../" * where.count("/")
            home = not path
            (out / where).mkdir(parents=True, exist_ok=True)
            (out / where / "index.html").write_text(
                page(lang, catalog, hero if home else "", body, root, SITE_URL + where,
                     catalog["title"] if home else catalog[f"{path.strip('/')}_page_title"], found, path=path,
                     first_visit=home and lang == CODES[0]),
                encoding="utf-8")
        # 404.html for each language: GitHub Pages serves the root's at any
        # address, which sends a visitor reading another language to theirs.
        (out / folder(lang) / "404.html").write_text(
            page(lang, catalog, "", lost, base, SITE_URL, catalog["lost_page_title"], found, lost=True),
            encoding="utf-8")
    first = catalogs[CODES[0]]

    (out / "feed.atom").write_text(feed(found, first), encoding="utf-8")
    # The projects' latest releases, for the menu of Boréale's sites in the
    # projects' own sites, read when they are built.
    latest = {}
    for r in found:
        latest.setdefault(r["project"], r["version"])
    versions = {"schema": VERSIONS_SCHEMA, "projects": latest}
    (out / "versions.json").write_text(json.dumps(versions, indent=1) + "\n", encoding="utf-8")
    (out / "manifest.webmanifest").write_text(manifest(first), encoding="utf-8")
    shutil.copy(SITE / "assets" / "favicon.ico", out / "favicon.ico")  # asked for at the root by old browsers
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    (out / ".well-known").mkdir()
    (out / ".well-known" / "security.txt").write_text(security(datetime.now(timezone.utc)), encoding="utf-8")
    # Each page in each language, with every language's (search engines read hreflang there too).
    (out / "sitemap.xml").write_text(BOREALE.sitemap(PAGES), encoding="utf-8")
    (out / ".nojekyll").touch()
    # What was built, as one hash: the scheduled builds publish only when it
    # differs from the one served (.github/workflows/site.yml).
    (out / "build.sha256").write_text(boreale.digest(out) + "\n", encoding="utf-8")
    print(f"build_site: {len(CODES)} languages in {out} for {SITE_URL}, {len(found)} release(s)")


if __name__ == "__main__":
    main()
