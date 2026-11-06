#!/usr/bin/env python3
"""Checks a built boreale.dev (tools/build_site.py) and its sources.

    python3 tools/check_site.py <site-dir>

- what every one of Boréale's sites passes (library/boreale-site,
  boreale_site.check): no {{key}} left, links and #anchors that lead
  somewhere, links out by the rule "liens sortants anonymes" and their UTM
  tags, the page chrome (one header with the menu of the sites, no pill, the
  footer linking to every site), nothing the Content-Security-Policy blocks, Umami's tracker, no
  e-mail address, the schema.org data read as JSON;
- the catalogs of site/i18n/ and boreale-site's: the same keys as en-US.json,
  none empty (but fr.json's legal_translation: the French legal page is the
  original), no common text repeated here;
- boreale-site's colours (the :root of boreale.css, every site's) equal branding/tokens.json's;
- feed.atom and sitemap.xml read as XML, manifest.webmanifest's icons are there.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "library" / "boreale-site"))
import boreale_site as boreale  # noqa: E402
from boreale_site import check  # noqa: E402


def token_errors() -> list[str]:
    """The colours of boreale-site's boreale.css (every site's :root) against
    branding/tokens.json, the brand's one source: a site's colour that drifts."""
    tokens = json.loads((ROOT / "branding" / "tokens.json").read_text(encoding="utf-8"))["colours"]
    css = (ROOT / "library" / "boreale-site" / "assets" / "boreale.css").read_text(encoding="utf-8")
    root = css[css.index(":root {"):].split("}", 1)[0]
    found = dict(re.findall(r"--(abyss|night|snow|mist|aurora|ice|violet):\s*(#[0-9a-fA-F]{6})", root))
    return [f"boreale.css: --{name} is {found.get(name)}, branding/tokens.json says {value}"
            for name, value in tokens.items() if found.get(name, "").lower() != value.lower()]


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    site = Path(sys.argv[1])
    errors = boreale.check_catalogs(ROOT / "site" / "i18n", optional={"fr": {"legal_translation"}})
    found, pages = check.pages(site, boreale.Site("boreale", os.environ.get("SITE_URL")), chrome=True, cta=False)
    errors += found
    errors += token_errors()

    for name in ("feed.atom", "sitemap.xml"):
        try:
            ElementTree.parse(site / name)
        except (OSError, ElementTree.ParseError) as error:
            errors.append(f"{name}: {error}")
    try:
        icons = json.loads((site / "manifest.webmanifest").read_text(encoding="utf-8"))["icons"]
        errors += [f"manifest.webmanifest: {i['src']} leads nowhere" for i in icons if not (site / i["src"]).exists()]
    except (OSError, ValueError, KeyError) as error:
        errors.append(f"manifest.webmanifest: {error}")

    for e in errors:
        print(f"check_site: {e}")
    if errors:
        sys.exit(1)
    print(f"check_site: {pages} pages, {len(boreale.CODES)} catalogs, nothing wrong")


if __name__ == "__main__":
    main()
