#!/usr/bin/env python3
"""Builds boreale.dev into <out-dir> (site/README.md).

    python3 tools/build_site.py <out-dir>

site/template.html is the page around site/hero.html and site/home.html (the
home page: its hero under the aurora, then the rest), site/legal.html (legal/:
privacy and legal notice) or site/lost.html (404.html); each {{key}} is the
key's text in the language's catalog, site/i18n/<language>.json. The
consoles' fifteen languages (LANGUAGES): English at the root, each other one
in its folder (fr/, fr-ca/, de/ ... zh-hant/).

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
# The consoles' languages, as PlayGuard's, PlayShelf's and Aurore's sites
# have them: the catalog's code (site/i18n/<code>.json), the site's folder
# ('' for the root, the first one), the name in its own words, the html lang.
LANGUAGES = [
    ("en", "", "English", "en"),
    ("fr", "fr", "Français", "fr"),
    ("fr-CA", "fr-ca", "Français (Canada)", "fr-CA"),
    ("de", "de", "Deutsch", "de"),
    ("es", "es", "Español", "es"),
    ("es-419", "es-419", "Español (Latinoamérica)", "es-419"),
    ("it", "it", "Italiano", "it"),
    ("nl", "nl", "Nederlands", "nl"),
    ("pt", "pt", "Português", "pt-PT"),
    ("pt-BR", "pt-br", "Português (Brasil)", "pt-BR"),
    ("ru", "ru", "Русский", "ru"),
    ("ja", "ja", "日本語", "ja"),
    ("ko", "ko", "한국어", "ko"),
    ("zh-Hans", "zh-hans", "简体中文", "zh-Hans"),
    ("zh-Hant", "zh-hant", "繁體中文", "zh-Hant"),
]
CODES = [code for code, _, _, _ in LANGUAGES]
# The language the legal texts are written in, the others translating it
# (legal_translation, said on the other languages' legal page).
ORIGINAL = "fr"
# Each language's flag in the language menu (fonts/twemoji-flags.woff2 draws
# them the same everywhere, Windows included): the country of the console's
# language, Mexico for Latin America's Spanish, Taiwan for Traditional Chinese.
FLAGS = {"en": "US", "fr": "FR", "fr-CA": "CA", "de": "DE", "es": "ES", "es-419": "MX", "it": "IT", "nl": "NL",
         "pt": "PT", "pt-BR": "BR", "ru": "RU", "ja": "JP", "ko": "KR", "zh-Hans": "CN", "zh-Hant": "TW"}
# Open Graph's name of each language.
OG_LOCALES = {"en": "en_US", "fr": "fr_FR", "fr-CA": "fr_CA", "de": "de_DE", "es": "es_ES", "es-419": "es_LA",
              "it": "it_IT", "nl": "nl_NL", "pt": "pt_PT", "pt-BR": "pt_BR", "ru": "ru_RU", "ja": "ja_JP",
              "ko": "ko_KR", "zh-Hans": "zh_CN", "zh-Hant": "zh_TW"}
OWNER = "JigSawFr"
RELEASES_SHOWN = 5
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



# Links out say nothing of the visit (workbench rule "liens sortants
# anonymes"): the page sends no referrer (template.html's meta), a link to a
# third party carries rel="noreferrer"; a link to *.boreale.dev or to
# github.com/JigSawFr keeps the origin alone (referrerpolicy="strict-origin"),
# so GitHub's traffic insights still see our sites.
LINK_OUT = re.compile(r'<a\b[^<>]*?\bhref="(https?://[^"]*)"[^<>]*>')


def own_site(url: str) -> bool:
    u = urlparse(url)
    host = (u.hostname or "").lower()
    return host == "boreale.dev" or host.endswith(".boreale.dev") or \
        (host == "github.com" and u.path.lower().startswith("/jigsawfr"))


def link_out(tag: str, url: str) -> str:
    tag = re.sub(r'\sreferrerpolicy="[^"]*"', "", tag)
    rel = re.search(r'\srel="([^"]*)"', tag)
    words = [w for w in (rel.group(1).split() if rel else []) if w != "noreferrer"]
    if rel:
        tag = tag[:rel.start()] + tag[rel.end():]
    if own_site(url):
        extra = ' referrerpolicy="strict-origin"'
    else:
        words.append("noreferrer")
        extra = ""
    if words:
        extra = f' rel="{" ".join(words)}"' + extra
    return tag[:-1] + extra + ">"


def links_out(text: str) -> str:
    return LINK_OUT.sub(lambda m: link_out(m.group(0), m.group(1)), text)


def project_url(key: str, language: str) -> str:
    """A project's site in a language: the same folder as this site's."""
    return PROJECTS[key]["site"] + folder(language)


def try_url(key: str, language: str) -> str:
    """A project's simulator (or Aurore's demo) in a language: the apps'
    codes (en-US for English)."""
    if key == "aurore":
        return PROJECTS[key]["try"] + (f"?lang={language}" if language in DEMO_LANGUAGES else "")
    return PROJECTS[key]["try"] + f"?lang={'en-US' if language == 'en' else language}"


def flag(language: str) -> str:
    """A language's flag, two regional indicator letters, for the eyes only."""
    emoji = "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in FLAGS[language])
    return f'<span class="flag" aria-hidden="true">{emoji}</span>'


def languages(language: str, catalog: dict, root: str, path: str) -> str:
    """The header's languages: a button with the page's, and under it their
    menu (a popover, as the menu of Boréale's sites), this page in each, its
    own marked. Choosing one keeps it (assets/lang.js)."""
    name = next(n for c, _, n, _ in LANGUAGES if c == language)
    options = "\n".join(
        f'        <li><a href="{root}{folder(c)}{path}" data-lang="{d or c}" lang="{hl}" hreflang="{hl}"'
        f'{' aria-current="true"' if c == language else ""}>{flag(c)}{html.escape(n)}</a></li>'
        for c, d, n, hl in LANGUAGES)
    label = catalog["language"]
    return (f'<div class="settings">\n'
            f'      <button class="lang-button" type="button" popovertarget="languages" aria-label="{label} · {html.escape(name)}">'
            f'{flag(language)}<span class="lang-name">{html.escape(name)}</span>'
            f'<span class="lang-code">{language.split("-")[0].upper()}</span>'
            f'<svg class="chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>\n'
            f'      <ul id="languages" class="langs" popover aria-label="{label}">\n{options}\n      </ul>\n    </div>')

# Boréale's sites, in the header's menu (switcher()): the same in each site,
# each in its catalog's language where it has it. boreale.dev first, then
# the homebrew, then the libraries, each group under its catalog's title.
SITES = [(None, [("boreale", "Boréale", "https://boreale.dev/")]),
         ("sites_homebrew", [("playguard", "PlayGuard", "https://guard.boreale.dev/"),
                             ("playshelf", "PlayShelf", "https://shelf.boreale.dev/")]),
         ("sites_libraries", [("aurore", "Aurore", "https://aurore.boreale.dev/")])]


def switcher(language: str, catalog: dict, root: str, latest: dict) -> str:
    """The header's name, a button that opens the menu of Boréale's sites
    (the same in the four sites: site.css's and site.js's "site switcher"),
    this one marked and leading home, each with its latest release
    (`latest`). A popover: the browser closes it on Esc or a click elsewhere."""
    label = catalog["sites_label"]
    groups = []
    for title, sites in SITES:
        items = []
        for key, name, url in sites:
            here = key == "boreale"
            href = f"{root}{folder(language)}" if here else url + folder(language)
            soon = f'<em class="soon">{catalog["sites_soon"]}</em>' if key == "playshelf" else ""
            version = f' <span class="sites-version">{html.escape(latest[key])}</span>' if key in latest else ""
            current = ' aria-current="true"' if here else ""
            items.append(f'<li><a href="{href}"{current}>'
                         f'<img src="{root}assets/marks/{key}.svg" alt="" width="36" height="36">'
                         f'<span><strong>{name}{version}</strong><small>{catalog[f"sites_{key}"]}</small></span>{soon}</a></li>')
        heading = f'<p class="sites-title">{catalog[title]}</p>' if title else ""
        groups.append(f'        {heading}<ul>\n          ' + "\n          ".join(items) + '\n        </ul>')
    return (f'<div class="switcher">\n'
            f'      <button class="brand switch" type="button" popovertarget="sites" aria-label="Boréale · {label}">'
            f'<img src="{root}assets/marks/boreale.svg" alt="" width="34" height="34">Boréale'
            f'<svg class="chevron" viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></button>\n'
            f'      <div id="sites" class="sites" popover aria-label="{label}">\n'
            + "\n".join(groups) + '\n      </div>\n    </div>')


# The pages other than 404.html, by their path under each language's folder.
PAGES = {"": "home.html", "legal/": "legal.html", "insights/": "insights.html"}

# Atlas, the open data PlayShelf reads (https://github.com/JigSawFr/Atlas):
# its own site, each language in the same folder as here.
ATLAS = "https://atlas.boreale.dev/"

# A release's date as each language writes it, short: its months, and where
# the day, the month and the year go ({d} {m} {y}; by number in Chinese,
# Japanese and Korean).
_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"]
_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "fr": _FR, "fr-CA": _FR,
    "de": ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez."],
    "es": _ES, "es-419": _ES,
    "it": ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"],
    "nl": ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"],
    "pt": _PT, "pt-BR": _PT,
    "ru": ["янв.", "февр.", "мар.", "апр.", "мая", "июн.", "июл.", "авг.", "сент.", "окт.", "нояб.", "дек."],
}
DATES = {"de": "{d}. {m} {y}", "ja": "{y}年{n}月{d}日", "zh-Hans": "{y}年{n}月{d}日", "zh-Hant": "{y}年{n}月{d}日",
         "ko": "{y}. {n}. {d}."}  # else "{d} {m} {y}"

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
    month = MONTHS[language][date.month - 1] if language in MONTHS else ""
    return DATES.get(language, "{d} {m} {y}").format(d=date.day, m=month, n=date.month, y=date.year)


def news(found: list, language: str, catalog: dict, root: str) -> str:
    """The home page's latest releases, or nothing without any: a list,
    drawn by site.css as a timeline (the dates beside a line of aurora, a
    dot on it for each release)."""
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


def attribute(text: str) -> str:
    """A text for a double-quoted attribute (the apostrophes left as they are)."""
    return html.escape(text, quote=False).replace('"', "&quot;")


def indexing(url: str, path: str, lost: bool) -> str:
    """The canonical address and the other languages' for search engines; a
    page that is not there (404.html) is kept out of their index instead."""
    if lost:
        return '<meta name="robots" content="noindex">'
    lines = [f'<link rel="canonical" href="{url}">']
    lines += [f'<link rel="alternate" hreflang="{hl}" href="{address(code, path)}">' for code, _, _, hl in LANGUAGES]
    lines.append(f'<link rel="alternate" hreflang="x-default" href="{address(CODES[0], path)}">')
    return "\n".join(lines)


def folder(language: str) -> str:
    """A language's folder: none for the first one, at the root."""
    d = next(d for c, d, _, _ in LANGUAGES if c == language)
    return f"{d}/" if d else ""


def html_lang(language: str) -> str:
    """A language's code for html's lang and hreflang (pt-PT for pt)."""
    return next(hl for c, _, _, hl in LANGUAGES if c == language)


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
    values["languages"] = languages(language, catalog, root, path if not lost else "")
    # The root's home page sends a first visit to the browser's language (assets/lang.js).
    values["first_visit"] = " data-first-visit" if first_visit else ""
    # 404.html at the root sends a visitor reading another language to that
    # language's (assets/lang.js); the site's address path tells it where.
    values["lost"] = f' data-lost="{root}"' if lost and language == CODES[0] else ""
    values["indexing"] = indexing(url, path, lost)
    # The home page (the one with a hero): site.css's showcase, the night
    # going on down it.
    values["page_class"] = ' class="home"' if hero else ""
    values["og_alternates"] = "\n".join(
        f'<meta property="og:locale:alternate" content="{OG_LOCALES[code]}">' for code in CODES if code != language)
    values.update(root=root, site=SITE_URL, url=url, title=title)
    values["switcher"] = switcher(language, catalog, root, latest)
    values["news"] = news(found, language, catalog, root)
    values["atlas_url"] = ATLAS + folder(language)
    values["jsonld"] = structured(language, catalog, found)
    values["hero"] = fill(hero, values)
    values["body"] = fill(body, values)
    return links_out(fill((SITE / "template.html").read_text(encoding="utf-8"), values))


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
    catalogs = {code: json.loads((SITE / "i18n" / f"{code}.json").read_text(encoding="utf-8")) for code in CODES}
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
    (out / "versions.json").write_text(json.dumps(latest, indent=1) + "\n", encoding="utf-8")
    (out / "manifest.webmanifest").write_text(manifest(first), encoding="utf-8")
    shutil.copy(SITE / "assets" / "favicon.ico", out / "favicon.ico")  # asked for at the root by old browsers
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    (out / ".well-known").mkdir()
    (out / ".well-known" / "security.txt").write_text(security(datetime.now(timezone.utc)), encoding="utf-8")
    # Each page in each language, with every language's (search engines read hreflang there too).
    urls = ""
    for path in PAGES:
        alternates = "".join(
            f'    <xhtml:link rel="alternate" hreflang="{hl}" href="{address(code, path)}"/>\n' for code, _, _, hl in LANGUAGES)
        alternates += f'    <xhtml:link rel="alternate" hreflang="x-default" href="{address(CODES[0], path)}"/>\n'
        urls += "".join(f"  <url>\n    <loc>{address(code, path)}</loc>\n{alternates}  </url>\n" for code in CODES)
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
    print(f"build_site: {len(CODES)} languages in {out} for {SITE_URL}, {len(found)} release(s)")


if __name__ == "__main__":
    main()
