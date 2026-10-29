<div align="center">

<img src="branding/png/social-preview.png" alt="Boréale" width="100%">

### Homebrew for the long nights

**[boreale.dev](https://boreale.dev/)** · **[PlayGuard](https://github.com/JigSawFr/PlayGuard)** · **[PlayShelf](https://github.com/JigSawFr/PlayShelf)** · **[Aurore](https://github.com/JigSawFr/Aurore)**

</div>

---

Boréale is the home of a few open-source projects for the Nintendo Switch: **PlayGuard** (parental controls on the console), **PlayShelf** (your game library on the console) and **Aurore** (the borealis fork both are built with). The name closes a line that was already in the code: borealis, then Aurore, then Boréale.

This repository holds:

- **[`branding/`](branding/README.md)**: the marks, the wordmarks, the colours, the type and the tone shared by every project, as SVG and PNG.
- **[`site/`](site/README.md)**: the website at <https://boreale.dev/>, in the consoles' fifteen languages. The projects' sites are its sub-domains: <https://guard.boreale.dev/> (PlayGuard), <https://shelf.boreale.dev/> (PlayShelf) and <https://aurore.boreale.dev/> (Aurore).

## Build the site

```sh
python3 tools/build_site.py build     # the pages, in build/
python3 tools/check_site.py build     # links, catalogs, Content-Security-Policy
python3 tools/site_layout.py build    # phones to desktop, and axe (Playwright for Python)
python3 -m http.server -d build 8000  # then http://localhost:8000/
```

Python 3 and nothing else. `node tools/export-branding.mjs` renders the PNGs again from the SVGs (Playwright).

## License

The code and the pages: **GPLv3**, as PlayGuard, PlayShelf and Aurore (see [`LICENSE`](LICENSE)). The fonts in `site/assets/fonts/` are under the **SIL Open Font License** (their `OFL-*.txt`), except the language menu's flags (`twemoji-flags.woff2`, cut out of Twemoji's): **CC-BY 4.0** (`LICENSE-twemoji-flags.txt`). The marks and the names Boréale, PlayGuard, PlayShelf and Aurore identify these projects: use them to point to the projects, not for your own.

<sub>Not affiliated with or endorsed by Nintendo. Nintendo Switch is a trademark of Nintendo.</sub>
