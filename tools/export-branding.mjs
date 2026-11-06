// Renders every project's branding (branding/<project>/*.svg, written by
// tools/brand.py) to the same set of PNGs, branding/<project>/png/, with the
// fonts the sites serve, in a headless Chromium; then boreale.dev's own icons
// (site/assets/).
//
//   node tools/export-branding.mjs [project…]
//
// Needs Playwright with its Chromium (npm i -g playwright, npx playwright
// install chromium) and the submodule (git submodule update --init).
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const fonts = join(root, "library/boreale-site/assets/fonts");
const branding = join(root, "branding");

// What every project gets: [source svg, output, width, height, scale].
// The README banner at twice its size, for sharp screens; icon-256.jpg is the
// Switch's homebrew icon (an NRO's: 256 × 256, JPEG).
const SET = [
  ["icon.svg", "icon-1024.png", 1024, 1024],
  ["icon.svg", "icon-512.png", 512, 512],
  ["icon.svg", "icon-256.png", 256, 256],
  ["icon.svg", "icon-256.jpg", 256, 256],
  ["icon.svg", "icon-192.png", 192, 192],
  ["icon.svg", "apple-touch-icon.png", 180, 180],
  ["mark.svg", "mark-512.png", 512, 512],
  ["mark.svg", "mark-256.png", 256, 256],
  ["wordmark.svg", "wordmark.png", 720, 176],
  ["wordmark-light.svg", "wordmark-light.png", 720, 176],
  ["banner.svg", "banner.png", 1280, 320, 2],
  ["social-preview.svg", "social-preview.png", 1280, 640],
  ["mark-mono-white.svg", "mark-mono-white-512.png", 512, 512],
  ["mark-mono-black.svg", "mark-mono-black-512.png", 512, 512],
];

// Inlined: a page set from a string may not read file:// URLs.
const face = (family, file, weight) =>
  `@font-face{font-family:"${family}";src:url("data:font/woff2;base64,${readFileSync(join(fonts, file)).toString("base64")}") format("woff2");font-weight:${weight};}`;
const css = face("Sora", "sora.woff2", "100 800") + face("JetBrains Mono", "jetbrains-mono.woff2", "100 800") +
  "html,body{margin:0;background:transparent}svg{display:block}";

const browser = await chromium.launch();
const pages = new Map();
async function render(svgPath, width, height, scale = 1, type = "png") {
  if (!pages.has(scale)) pages.set(scale, await browser.newPage({ deviceScaleFactor: scale }));
  const page = pages.get(scale);
  const svg = readFileSync(svgPath, "utf8").replace(/width="\d+" height="\d+"/, `width="${width}" height="${height}"`);
  await page.setViewportSize({ width, height });
  await page.setContent(`<!doctype html><style>${css}</style>${svg}`);
  await page.evaluate(() => Promise.all(["300 20px Sora", "400 20px Sora", "700 20px Sora", "20px 'JetBrains Mono'"].map((f) => document.fonts.load(f))));
  return page.locator("body > svg").first().screenshot(type === "jpeg" ? { type, quality: 95 } : { omitBackground: true });
}

// An ICO holding PNGs as they are (a format every browser reads since 2006).
function ico(pngs, sizes) {
  const head = Buffer.alloc(6 + 16 * pngs.length);
  head.writeUInt16LE(0, 0); head.writeUInt16LE(1, 2); head.writeUInt16LE(pngs.length, 4);
  let offset = head.length;
  pngs.forEach((png, i) => {
    const at = 6 + 16 * i;
    head.writeUInt8(sizes[i], at); head.writeUInt8(sizes[i], at + 1);
    head.writeUInt16LE(1, at + 4); head.writeUInt16LE(32, at + 6);
    head.writeUInt32LE(png.length, at + 8); head.writeUInt32LE(offset, at + 12);
    offset += png.length;
  });
  return Buffer.concat([head, ...pngs]);
}

const wanted = process.argv.slice(2);
const projects = readdirSync(branding, { withFileTypes: true })
  .filter((d) => d.isDirectory() && existsSync(join(branding, d.name, "mark.svg")))
  .map((d) => d.name)
  .filter((p) => !wanted.length || wanted.includes(p));

for (const project of projects) {
  const dir = join(branding, project);
  mkdirSync(join(dir, "png"), { recursive: true });
  for (const [src, out, width, height, scale = 1] of SET) {
    if (!existsSync(join(dir, src))) continue;
    const type = out.endsWith(".jpg") ? "jpeg" : "png";
    writeFileSync(join(dir, "png", out), await render(join(dir, src), width, height, scale, type));
    console.log(`branding/${project}/png/${out}`);
  }
  // favicon.ico: the small mark where there is one (under 24 px), else the mark.
  const small = join(dir, existsSync(join(dir, "mark-small.svg")) ? "mark-small.svg" : "mark.svg");
  const sizes = [16, 32, 48];
  const pngs = [];
  for (const n of sizes) pngs.push(await render(small, n, n));
  writeFileSync(join(dir, "png", "favicon.ico"), ico(pngs, sizes));
  console.log(`branding/${project}/png/favicon.ico`);
}
await browser.close();

// boreale.dev's own: its icons, its favicons and its preview.
if (projects.includes("boreale")) {
  const png = join(branding, "boreale/png");
  for (const f of ["icon-512.png", "icon-192.png", "apple-touch-icon.png", "social-preview.png", "favicon.ico"]) {
    copyFileSync(join(png, f), join(root, "site/assets", f));
  }
  copyFileSync(join(branding, "boreale/mark-small.svg"), join(root, "site/assets/favicon.svg"));
  console.log("site/assets/ (icons, favicons, social preview)");
}
