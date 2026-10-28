// Renders branding/*.svg to the PNGs that need one (branding/png/, site/assets/),
// with the fonts the site serves, in a headless Chromium.
//
//   node tools/export-branding.mjs
//
// Needs Playwright (npm i -g playwright, then npx playwright install chromium).
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const fonts = join(root, "site/assets/fonts");

// [source svg, output png, width, height]
const exports = [
  ["branding/mark.svg", "branding/png/mark-512.png", 512, 512],
  ["branding/mark.svg", "branding/png/mark-256.png", 256, 256],
  ["branding/mark-small.svg", "branding/png/mark-small-64.png", 64, 64],
  ["branding/icon.svg", "branding/png/icon-1024.png", 1024, 1024],
  ["branding/icon.svg", "site/assets/icon-512.png", 512, 512],
  ["branding/icon.svg", "site/assets/icon-192.png", 192, 192],
  ["branding/icon.svg", "site/assets/apple-touch-icon.png", 180, 180],
  ["branding/wordmark.svg", "branding/png/wordmark.png", 720, 176],
  ["branding/wordmark-light.svg", "branding/png/wordmark-light.png", 720, 176],
  ["branding/aurore-mark.svg", "branding/png/aurore-mark-256.png", 256, 256],
  ["branding/mark-mono-white.svg", "branding/png/mark-mono-white-512.png", 512, 512],
  ["branding/mark-mono-black.svg", "branding/png/mark-mono-black-512.png", 512, 512],
  ["branding/banners/playguard.svg", "branding/png/banner-playguard.png", 1280, 320],
  ["branding/banners/playshelf.svg", "branding/png/banner-playshelf.png", 1280, 320],
  ["branding/banners/aurore.svg", "branding/png/banner-aurore.png", 1280, 320],
  ["branding/social-preview.svg", "branding/png/social-preview.png", 1280, 640],
  ["branding/social-preview.svg", "site/assets/social-preview.png", 1280, 640],
  // favicon.ico's sizes, from the small mark (below)
  ["branding/mark-small.svg", "branding/png/favicon-16.png", 16, 16],
  ["branding/mark-small.svg", "branding/png/favicon-32.png", 32, 32],
  ["branding/mark-small.svg", "branding/png/favicon-48.png", 48, 48],
];

// Inlined: a page set from a string may not read file:// URLs.
const face = (family, file, weight) =>
  `@font-face{font-family:"${family}";src:url("data:font/woff2;base64,${readFileSync(join(fonts, file)).toString("base64")}") format("woff2");font-weight:${weight};}`;
const css = face("Sora", "sora.woff2", "100 800") + face("JetBrains Mono", "jetbrains-mono.woff2", "100 800") +
  "html,body{margin:0;background:transparent}svg{display:block}";

const browser = await chromium.launch();
const page = await browser.newPage();
for (const [src, out, width, height] of exports) {
  const svg = readFileSync(join(root, src), "utf8").replace(/width="\d+" height="\d+"/, `width="${width}" height="${height}"`);
  await page.setViewportSize({ width, height });
  await page.setContent(`<!doctype html><style>${css}</style>${svg}`);
  await page.evaluate(() => Promise.all(["300 20px Sora", "700 20px Sora", "20px 'JetBrains Mono'"].map((f) => document.fonts.load(f))));
  mkdirSync(dirname(join(root, out)), { recursive: true });
  await page.locator("body > svg").first().screenshot({ path: join(root, out), omitBackground: true });
  console.log(`${out} (${width}×${height})`);
}
await browser.close();

// site/assets/favicon.ico for the browsers that ask for /favicon.ico: an ICO
// holding the three PNGs as they are (a format every browser reads since 2006).
const sizes = [16, 32, 48];
const pngs = sizes.map((n) => readFileSync(join(root, `branding/png/favicon-${n}.png`)));
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
writeFileSync(join(root, "site/assets/favicon.ico"), Buffer.concat([head, ...pngs]));
console.log("site/assets/favicon.ico (16, 32, 48)");
