// Automated slide QA: node qa.mjs <deck> [slideIdPrefix]
// Opens docs/<deck>/ at 1600x900, visits every slide at its final step, and reports:
// canvas overflow, clipped panels/code, overlapping diagram nodes, missing wire ids, console errors.
// Writes qa/<deck>/report.json and one screenshot per slide (qa/<deck>/<id>.png).
import { chromium } from "playwright";
import { mkdirSync, writeFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { homedir } from "node:os";
import { spawn } from "node:child_process";

const deckName = process.argv[2];
const only = process.argv[3] || "";
if (!deckName) { console.error("usage: node qa.mjs <deck> [idPrefix]"); process.exit(1); }
const ROOT = new URL(".", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const OUT = join(ROOT, "qa", deckName);
mkdirSync(OUT, { recursive: true });

// find a local chromium
const pw = join(homedir(), "AppData", "Local", "ms-playwright");
const dirs = readdirSync(pw).filter((d) => /^chromium-\d+$/.test(d)).sort().reverse();
const exe = join(pw, dirs[0], "chrome-win64", "chrome.exe");

const port = 8800 + Math.floor((process.pid % 150));
const srv = spawn(process.execPath, [join(ROOT, "serve.mjs"), String(port)], { stdio: "ignore" });
await new Promise((r) => setTimeout(r, 700));

console.log("launching", exe, "port", port);
const browser = await chromium.launch({ executablePath: exe, headless: true, timeout: 60000 });
console.log("browser up");
const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });
const consoleErrors = [];
page.on("console", (m) => { if (m.type() === "error" && !/favicon/.test(m.text())) consoleErrors.push(m.text()); });
page.on("pageerror", (e) => consoleErrors.push("pageerror: " + e.message));

await page.goto(`http://localhost:${port}/${deckName}/`, { waitUntil: "load", timeout: 60000 });
console.log("page loaded");
await page.waitForFunction(() => window.Deck && Deck.index >= 0, null, { timeout: 15000 });
console.log("deck ready");
await page.evaluate(() => { gsap.globalTimeline.timeScale(40); });

const n = await page.evaluate(() => Deck.slides.length);
console.log("slides", n);
const report = { deck: deckName, slides: n, issues: [], consoleErrors };

for (let i = 0; i < n; i++) {
  const id = await page.evaluate((i) => Deck.slides[i].id, i);
  if (only && !id.startsWith(only)) continue;
  await page.evaluate((i) => Deck.go(i, "max", -1), i);
  await page.waitForTimeout(260);
  const res = await page.evaluate((i) => {
    const s = Deck.slides[i];
    const out = [];
    const deck = document.querySelector(".deck").getBoundingClientRect();
    const sc = deck.width / 1600;
    const rel = (r) => ({ x: (r.left - deck.left) / sc, y: (r.top - deck.top) / sc, r: (r.right - deck.left) / sc, b: (r.bottom - deck.top) / sc });
    const visible = (el) => { const cs = getComputedStyle(el); return cs.visibility !== "hidden" && +cs.opacity > 0.05 && cs.display !== "none"; };
    // 1. canvas overflow
    s.querySelectorAll("*").forEach((el) => {
      if (el.closest(".notes") || el.closest("svg") && el.tagName !== "svg") return;
      if (!visible(el)) return;
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) return;
      const q = rel(r);
      if (q.r > 1604 || q.b > 884 || q.x < -4 || q.y < -4) {
        const txt = (el.textContent || "").trim().slice(0, 50);
        out.push({ type: "overflow", el: el.tagName.toLowerCase() + "." + [...el.classList].join("."), box: [q.x, q.y, q.r, q.b].map(Math.round), text: txt });
      }
    });
    // 2. clipped content
    s.querySelectorAll(".panel, pre.code, .node, .qa .a, .callout, td").forEach((el) => {
      if (!visible(el)) return;
      if (el.scrollHeight > el.clientHeight + 4 || el.scrollWidth > el.clientWidth + 4) {
        out.push({ type: "clipped", el: el.tagName.toLowerCase() + "." + [...el.classList].join("."), size: [el.clientWidth, el.clientHeight, el.scrollWidth, el.scrollHeight], text: (el.textContent || "").trim().slice(0, 50) });
      }
    });
    // 3. node overlap
    s.querySelectorAll(".diagram").forEach((d) => {
      const nodes = [...d.querySelectorAll(".node")].filter(visible);
      for (let a = 0; a < nodes.length; a++) for (let b = a + 1; b < nodes.length; b++) {
        const A = nodes[a].getBoundingClientRect(), B = nodes[b].getBoundingClientRect();
        const ix = Math.min(A.right, B.right) - Math.max(A.left, B.left), iy = Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top);
        if (ix > 6 && iy > 6) out.push({ type: "node-overlap", a: nodes[a].id, b: nodes[b].id });
      }
      // 4. wires to missing ids
      (d.dataset.wires || "").split(";").forEach((w) => {
        const m = w.trim().match(/^([\w-]+)\s*(<?>|<?->|--)\s*([\w-]+)/);
        if (!m) { if (w.trim()) out.push({ type: "wire-syntax", wire: w.trim() }); return; }
        [m[1], m[3]].forEach((nid) => { if (!d.querySelector("#" + CSS.escape(nid))) out.push({ type: "wire-missing-node", id: nid }); });
      });
    });
    // 4b. v2 layout checks: sparse slide, long title, too much prose, qa slide in a main deck
    let maxB = 0;
    s.querySelectorAll("*").forEach((el) => { if (el.closest(".notes") || !visible(el)) return; const r = el.getBoundingClientRect(); if (r.width && r.height) maxB = Math.max(maxB, rel(r).b); });
    if (!s.classList.contains("chapter") && maxB < 620) out.push({ type: "sparse", note: `content ends at y=${Math.round(maxB)} (use the space: bigger diagram/code)` });
    const t = s.querySelector(".title");
    if (t && t.getBoundingClientRect().height / sc > 110) out.push({ type: "long-title", note: "title wraps to 3+ lines" });
    const prose = [...s.querySelectorAll("p, li, .lede, .callout, .panel > span")].filter((e) => !e.closest("pre, table, .gotcha, .paper, .notes")).map((e) => e.textContent).join(" ").split(/\s+/).filter(Boolean).length;
    if (prose > 110) out.push({ type: "wordy", note: `${prose} words of prose` });
    if (!/-interview$/.test(document.location.pathname.replace(/\/$/, "")) && s.querySelector(".qa")) out.push({ type: "qa-in-main-deck" });
    // 5. slide hygiene
    if (!s.querySelector(".title, .display")) out.push({ type: "no-title" });
    if (!s.dataset.tone) out.push({ type: "no-tone" });
    const steps = s._max || 0;
    const hasHook = !!s.querySelector("[data-fx], .diagram, [data-to], pre[data-focus], svg");
    return { id: s.id, steps, hasHook, title: (s.querySelector(".title, .display")?.textContent || "").trim().slice(0, 90), issues: out };
  }, i);
  await page.screenshot({ path: join(OUT, `${String(i + 1).padStart(2, "0")}-${id}.png` ) });
  if (res.issues.length) report.issues.push(res);
  if (!res.steps && !res.hasHook) report.issues.push({ id: res.id, issues: [{ type: "static-slide", note: "no steps and no animated diagram/numbers/code" }] });
  process.stdout.write(`${i + 1}/${n} ${id} ${res.issues.length ? "ISSUES " + res.issues.length : "ok"}\n`);
}
report.consoleErrors = consoleErrors;
writeFileSync(join(OUT, "report.json"), JSON.stringify(report, null, 2));
console.log(`\n${report.issues.length} slides with issues, ${consoleErrors.length} console errors -> ${join(OUT, "report.json")}`);
await browser.close();
srv.kill();
