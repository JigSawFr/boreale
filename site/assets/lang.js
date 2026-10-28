// The language at a first visit: the English home page (the root, marked
// data-first-visit) sends a visitor whose browser prefers French to /fr/,
// unless a language was chosen before. Choosing one in the header keeps it.
// The page not found (404.html) follows the same choice.
// Loaded in <head>, before the page is drawn, so the move shows nothing.
(function () {
  const KEY = "boreale-lang";
  const SITE = ["en", "fr"]; // the languages the site has; the first at the root
  let chosen = null;
  try { chosen = localStorage.getItem(KEY); } catch (e) { /* storage refused: no memory */ }

  const root = document.documentElement;
  const browser = () => (navigator.languages || [navigator.language || ""])
    .map((l) => String(l).toLowerCase().split("-")[0])
    .find((l) => SITE.includes(l));
  if (root.hasAttribute("data-first-visit") && !chosen) {
    const wanted = browser();
    if (wanted && wanted !== SITE[0]) {
      location.replace(`${wanted}/${location.hash}`);
      return;
    }
  }

  // A page that is not there: GitHub Pages serves the root's 404.html (in
  // the first language, data-lost holding the site's path) at any address.
  // It sends to the 404.html of the language the address is in (/fr/...),
  // else of the one chosen, else of the browser's.
  const base = root.getAttribute("data-lost");
  if (base !== null) {
    const inPath = location.pathname.startsWith(base) && location.pathname.slice(base.length).split("/")[0];
    const wanted = SITE.includes(inPath) ? inPath : SITE.includes(chosen) ? chosen : browser();
    if (wanted && wanted !== SITE[0]) {
      location.replace(`${base}${wanted}/404.html`);
      return;
    }
  }

  document.addEventListener("click", (event) => {
    const link = event.target.closest && event.target.closest("a[hreflang]");
    if (!link) return;
    try { localStorage.setItem(KEY, link.getAttribute("hreflang")); } catch (e) { /* idem */ }
  });
})();
