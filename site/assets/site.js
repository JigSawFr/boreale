// boreale.dev: the aurora behind the header and the hero (canvas#sky). Three
// soft curtains in the brand's colours under a few stars, drawn once at load;
// they move only while the page is visible and the visitor has not asked for
// less motion. Without script, site.css's gradient stands in.
(function () {
  const canvas = document.getElementById("sky");
  if (!canvas || !canvas.getContext) return;
  const ctx = canvas.getContext("2d");
  // The curtains are drawn here at a quarter of the size, then laid on the
  // sky blurred and scaled up in one go: blurring each strip would be slow.
  const glow = document.createElement("canvas");
  const gtx = glow.getContext("2d");
  const still = window.matchMedia("(prefers-reduced-motion: reduce)");
  const curtains = [
    { rgb: [0, 255, 204], y: 0.34, amp: 0.08, freq: 1.2, speed: 0.00012, height: 0.42, alpha: 0.34 },
    { rgb: [51, 187, 255], y: 0.26, amp: 0.06, freq: 1.7, speed: -0.00009, height: 0.34, alpha: 0.26 },
    { rgb: [138, 92, 255], y: 0.18, amp: 0.05, freq: 0.9, speed: 0.00007, height: 0.3, alpha: 0.26 },
  ];
  let w = 0, h = 0, stars = [];

  function size() {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    w = canvas.clientWidth; h = canvas.clientHeight;
    canvas.width = Math.max(1, Math.round(w * ratio));
    canvas.height = Math.max(1, Math.round(h * ratio));
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    glow.width = Math.max(1, Math.round(w / 4));
    glow.height = Math.max(1, Math.round(h / 4));
    let seed = 7; // the same stars at each load
    const random = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    stars = Array.from({ length: Math.round((w * h) / 2600) }, () => ({
      x: random() * w, y: random() * h * 0.75, r: random() * 1.1 + 0.2, a: random() * 0.6 + 0.2,
    }));
  }

  function draw(t) {
    const gw = glow.width, gh = glow.height;
    gtx.globalCompositeOperation = "source-over";
    gtx.clearRect(0, 0, gw, gh);
    gtx.globalCompositeOperation = "lighter";
    const step = Math.max(2, gw / 120);
    for (const c of curtains) {
      const [r, g, b] = c.rgb;
      const phase = t * c.speed;
      for (let x = -step; x < gw + step; x += step) {
        const u = x / gw;
        const base = gh * (c.y + c.amp * Math.sin((u * c.freq + phase) * 2 * Math.PI) + 0.03 * Math.sin(u * 17 + phase * 20));
        const length = gh * c.height * (0.6 + 0.4 * Math.sin(u * 9 + phase * 11));
        const flicker = 0.65 + 0.35 * Math.sin(u * 31 + phase * 40);
        const fill = gtx.createLinearGradient(0, base - length, 0, base);
        fill.addColorStop(0, `rgba(${r}, ${g}, ${b}, 0)`);
        fill.addColorStop(0.75, `rgba(${r}, ${g}, ${b}, ${c.alpha * flicker * 0.6})`);
        fill.addColorStop(1, `rgba(${r}, ${g}, ${b}, ${c.alpha * flicker})`);
        gtx.fillStyle = fill;
        gtx.fillRect(x, base - length, step + 1, length);
      }
    }

    ctx.fillStyle = "#0b1424";
    ctx.fillRect(0, 0, w, h);
    ctx.filter = "blur(8px)"; // where the browser can; scaling up softens it anyway
    ctx.drawImage(glow, 0, 0, w, h);
    ctx.filter = "none";
    for (const s of stars) {
      ctx.fillStyle = `rgba(232, 238, 247, ${s.a})`;
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 2 * Math.PI); ctx.fill();
    }
  }

  let frame = 0;
  function loop(t) { draw(t); frame = requestAnimationFrame(loop); }
  function start() {
    cancelAnimationFrame(frame);
    if (still.matches || document.hidden) draw(0);
    else frame = requestAnimationFrame(loop);
  }

  size();
  start();
  window.addEventListener("resize", () => { size(); draw(performance.now()); });
  document.addEventListener("visibilitychange", start);
  still.addEventListener("change", start);
})();
