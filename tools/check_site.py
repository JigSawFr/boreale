#!/usr/bin/env python3
"""Checks a built boreale.dev (tools/build_site.py) and its sources.

    python3 tools/check_site.py <site-dir>

- every catalog of site/i18n/ has the same keys as en.json, none empty;
- no {{key}} left in a page;
- every link and image to the site leads to a file, and every #anchor to an id;
- nothing the Content-Security-Policy blocks: no inline script, no <style>,
  no style="" attribute, nothing loaded from another site.
"""
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.problems = set(), [], []
        self.in_script = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if "style" in a:
            self.problems.append(f"style attribute on <{tag}>")
        if tag == "style":
            self.problems.append("<style> element")
        if tag == "script":
            if not a.get("src"):
                self.problems.append("inline <script>")
            self.links.append(("src", a.get("src") or ""))
        for name in ("href", "src"):
            if name in a and not (tag == "script" and name == "src"):
                self.links.append((name, a[name]))


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    site = Path(sys.argv[1])
    errors = []

    catalogs = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "site/i18n").glob("*.json"))}
    reference = set(catalogs["en"])
    for lang, catalog in catalogs.items():
        for key in sorted(reference - set(catalog)):
            errors.append(f"i18n/{lang}.json: no {key}")
        for key in sorted(set(catalog) - reference):
            errors.append(f"i18n/{lang}.json: {key} is not in en.json")
        for key, text in catalog.items():
            if key not in ("home", "other_href") and not str(text).strip():
                errors.append(f"i18n/{lang}.json: {key} is empty")

    pages = sorted(site.rglob("*.html"))
    if not pages:
        errors.append(f"no page in {site}")
    for path in pages:
        name = path.relative_to(site)
        html = path.read_text(encoding="utf-8")
        if "{{" in html:
            errors.append(f"{name}: a {{{{key}}}} is left")
        parsed = Page()
        parsed.feed(html)
        errors += [f"{name}: {p}" for p in parsed.problems]
        for attr, link in parsed.links:
            url = urlparse(link)
            if url.scheme in ("http", "https", "mailto"):
                if attr == "src":
                    errors.append(f"{name}: loads {link} from another site")
                continue
            if name.name == "404.html" and url.path.startswith("/"):
                target = site / url.path.lstrip("/")  # served from the site's root
            else:
                target = (path.parent / url.path).resolve() if url.path else path
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{name}: {link} leads nowhere")
                continue
            if url.fragment and target == path and url.fragment not in parsed.ids:
                errors.append(f"{name}: #{url.fragment} is not on the page")

    for e in errors:
        print(f"check_site: {e}")
    if errors:
        sys.exit(1)
    print(f"check_site: {len(pages)} pages, {len(catalogs)} catalogs, nothing wrong")


if __name__ == "__main__":
    main()
