#!/usr/bin/env python3
"""Copies Boréale's brand kit (branding/<project>/) into the projects'
repositories, at the paths each one reads them from.

    python3 tools/sync_branding.py <repository>…           # copies
    python3 tools/sync_branding.py --check <repository>…   # fails on a difference

<repository> is a checkout whose folder is named as below (../PlayGuard,
~/src/boreale-ha…). Run python3 tools/brand.py and node tools/export-branding.mjs
first. What a repository draws only for itself (PlayGuard's store pictures,
the Home Assistant logos, Aurore's platform icons) stays its own.
"""
from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRANDING = ROOT / "branding"

PROJECTS = ("boreale", "playguard", "playshelf", "aurore", "ha", "atlas", "lantern")

# The site icons every site serves from its assets.
def site_icons(project: str, assets: str) -> dict[str, str]:
    return {
        f"{assets}/favicon.svg": f"{project}/mark.svg",
        f"{assets}/favicon.ico": f"{project}/png/favicon.ico",
        f"{assets}/icon-192.png": f"{project}/png/icon-192.png",
        f"{assets}/icon-512.png": f"{project}/png/icon-512.png",
        f"{assets}/apple-touch-icon.png": f"{project}/png/apple-touch-icon.png",
    }


# Each repository: {its path: the kit's path, under branding/}.
TARGETS: dict[str, dict[str, str]] = {
    "boreale-site": {f"assets/marks/{p}.svg": f"{p}/mark.svg" for p in PROJECTS},
    "PlayGuard": {
        "branding/icon.svg": "playguard/icon.svg",
        "branding/mark.svg": "playguard/mark.svg",
        "icon.jpg": "playguard/png/icon-256.jpg",
        "resources/img/wordmark.png": "playguard/png/wordmark.png",
        "resources/img/wordmark-light.png": "playguard/png/wordmark-light.png",
        "images/apple-touch-icon.png": "playguard/png/apple-touch-icon.png",
        "images/icon-192.png": "playguard/png/icon-192.png",
        "images/icon-512.png": "playguard/png/icon-512.png",
        "images/social-preview.png": "playguard/png/social-preview.png",
        ".github/readme/banner.png": "playguard/png/banner.png",
    },
    "PlayShelf": {
        "branding/icon.svg": "playshelf/icon.svg",
        "branding/mark.svg": "playshelf/mark.svg",
        "icon.jpg": "playshelf/png/icon-256.jpg",
        "resources/img/wordmark.png": "playshelf/png/wordmark.png",
        "resources/img/wordmark-light.png": "playshelf/png/wordmark-light.png",
        "images/apple-touch-icon.png": "playshelf/png/apple-touch-icon.png",
        "images/icon-192.png": "playshelf/png/icon-192.png",
        "images/icon-512.png": "playshelf/png/icon-512.png",
        ".github/readme/social-preview.png": "playshelf/png/social-preview.png",
        ".github/readme/banner.png": "playshelf/png/banner.png",
    },
    "Aurore": {
        ".github/branding/icon.svg": "aurore/icon.svg",
        ".github/branding/icon.png": "aurore/png/icon-256.png",
        ".github/branding/social-preview.png": "aurore/png/social-preview.png",
        ".github/readme/banner.png": "aurore/png/banner.png",
    },
    "boreale-ha": {
        "branding/icon.svg": "ha/icon.svg",
        "branding/mark.svg": "ha/mark.svg",
        "custom_components/boreale/brand/icon.png": "ha/png/icon-256.png",
        "custom_components/boreale/brand/icon@2x.png": "ha/png/icon-512.png",
        ".github/readme/icon.png": "ha/png/icon-512.png",
        ".github/readme/banner.png": "ha/png/banner.png",
        ".github/readme/social-preview.png": "ha/png/social-preview.png",
        "site/assets/social-preview.png": "ha/png/social-preview.png",
        **site_icons("ha", "site/assets"),
    },
    "Atlas": {
        ".github/readme/banner.png": "atlas/png/banner.png",
        "site/assets/social-preview.png": "atlas/png/social-preview.png",
        **site_icons("atlas", "site/assets"),
    },
    "lantern-sdk": {
        ".github/readme/banner.png": "lantern/png/banner.png",
    },
}


def main(argv: list[str]) -> int:
    check = "--check" in argv
    repos = [Path(a).expanduser().resolve() for a in argv if a != "--check"]
    if not repos:
        print(__doc__, file=sys.stderr)
        return 2
    differ = []
    for repo in repos:
        files = TARGETS.get(repo.name)
        if files is None:
            print(f"{repo.name}: not a project of the kit ({', '.join(TARGETS)})", file=sys.stderr)
            return 2
        for dest, src in files.items():
            source, target = BRANDING / src, repo / dest
            if check:
                if not target.exists() or not filecmp.cmp(source, target, shallow=False):
                    differ.append(f"{repo.name}/{dest}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                print(f"{repo.name}/{dest}")
    if differ:
        print("Not the kit's (python3 tools/sync_branding.py):\n  " + "\n  ".join(differ), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
