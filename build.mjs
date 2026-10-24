// Build every deck in decks/<name>/ into docs/<name>/index.html (GitHub Pages serves /docs).
// Usage: node build.mjs            -> all decks
//        node build.mjs adk        -> one deck
import { readFileSync, writeFileSync, readdirSync, mkdirSync, copyFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const ROOT = new URL(".", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const DECKS = join(ROOT, "decks");
const OUT = join(ROOT, "docs");
const only = process.argv[2];

const HEAD = (meta) => `<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${meta.title}</title>
<meta name="description" content="${meta.description}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 rx=%278%27 fill=%27%232557e8%27/%3E%3Ccircle cx=%2716%27 cy=%2716%27 r=%276%27 fill=%27white%27/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300..800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../engine/deck.css">
${meta.css ? `<style>\n${meta.css}\n</style>` : ""}
</head>
<body>
<div class="stage">
<div class="deck">
`;

const TAIL = (scripts) => `
</div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.13.0/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/SplitText.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js" data-manual></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-yaml.min.js"></script>
<script src="../engine/deck.js"></script>
${scripts}
</body>
</html>
`;

mkdirSync(join(OUT, "engine"), { recursive: true });
for (const f of ["deck.css", "deck.js"]) copyFileSync(join(ROOT, "engine", f), join(OUT, "engine", f));

const built = [];
for (const name of readdirSync(DECKS)) {
  if (only && name !== only) continue;
  const dir = join(DECKS, name);
  const metaPath = join(dir, "meta.json");
  if (!existsSync(metaPath)) continue;
  const meta = JSON.parse(readFileSync(metaPath, "utf8"));
  if (existsSync(join(dir, "deck.css"))) meta.css = readFileSync(join(dir, "deck.css"), "utf8");
  const files = readdirSync(join(dir, "slides")).filter((f) => f.endsWith(".html")).sort();
  let body = "", scripts = "";
  for (const f of files) {
    let html = readFileSync(join(dir, "slides", f), "utf8");
    // move <script> blocks to the end so they run after the engine loads
    html = html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, (m) => { scripts += `\n<!-- ${f} -->\n${m}\n`; return ""; });
    body += `\n<!-- ${f} -->\n${html.trim()}\n`;
  }
  const count = (body.match(/<section\b[^>]*class="[^"]*\bslide\b/g) || []).length;
  mkdirSync(join(OUT, name), { recursive: true });
  writeFileSync(join(OUT, name, "index.html"), HEAD(meta) + body + TAIL(scripts));
  built.push({ name, meta, count });
  console.log(`built ${name}: ${files.length} files, ${count} slides`);
}

// landing page listing all decks
const all = readdirSync(DECKS).filter((n) => existsSync(join(DECKS, n, "meta.json"))).map((n) => ({ name: n, meta: JSON.parse(readFileSync(join(DECKS, n, "meta.json"), "utf8")) }));
writeFileSync(join(OUT, "index.html"), `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lecture decks</title>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300..800&display=swap" rel="stylesheet">
<style>
:root{--bg:#ffffff;--ink:#0f1430;--ink2:#333a5e;--muted:#646b8f;--line:rgba(22,32,90,.12);--a:#2557e8}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0b1030;--ink:#eef0fb;--ink2:#c3c9e8;--muted:#8d96c4;--line:rgba(173,186,255,.16);--a:#7fa8ff}}
body{margin:0;min-height:100vh;background:var(--bg);color:var(--ink);font-family:Geist,system-ui,sans-serif;padding:clamp(24px,7vw,96px) 16px}
main{max-width:1040px;margin:0 auto}
h1{font-family:Geist;font-weight:600;font-size:clamp(40px,7vw,84px);line-height:.95;letter-spacing:-.03em;margin:0 0 18px}
p{color:var(--ink2);font-size:19px;line-height:1.5;max-width:640px}
ul{list-style:none;padding:0;margin:48px 0 0;display:grid;gap:14px}
a{display:block;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:18px;padding:24px 26px;transition:border-color .2s,transform .2s}
a:hover{border-color:var(--a);transform:translateY(-2px)}
a b{display:block;font-family:Geist;font-weight:600;font-size:28px;letter-spacing:-.01em;margin-bottom:6px}
a span{color:var(--muted);font-size:17px;line-height:1.45}
</style></head><body><main>
<h1>Lecture decks</h1>
<p>Animated lecture decks. Use the arrow keys or a presentation clicker to move through each slide and its steps. Press O for the outline.</p>
<ul>
${all.map((d) => `<li><a href="${d.name}/"><b>${d.meta.title}</b><span>${d.meta.description}</span></a></li>`).join("\n")}
</ul>
</main></body></html>
`);
console.log("landing page written");
