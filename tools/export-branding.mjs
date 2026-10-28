// Renders branding/*.svg to the PNGs that need one (branding/png/, site/assets/),
// with the fonts the site serves, in a headless Chromium.
//
//   node tools/export-branding.mjs
//
// Needs Playwright (npm i -g playwright, then npx playwright install chromium).
import { readFileSync, mkdirSync } from "node:fs";
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
  ["branding/social-preview.svg", "branding/png/social-preview.png", 1280, 640],
  ["branding/social-preview.svg", "site/assets/social-preview.png", 1280, 640],
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
  await page.locator("svg").first().screenshot({ path: join(root, out), omitBackground: true });
  console.log(`${out} (${width}×${height})`);
}
await browser.close();
