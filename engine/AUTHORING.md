# Slide authoring contract

Read this file completely before you write a slide. Every slide in every deck follows it.

## 1. What a slide file is

- One file = one or more `<section class="slide">` elements. Path: `decks/<deck>/slides/NN-name.html` (NN sorts the order).
- The canvas is **1600 × 900 px**. The engine scales it to the screen. Padding is 84px top, 104px left/right, 76px bottom. The usable area is about **1392 × 740 px**. Content that overflows is a defect. Count your lines.
- Required attributes on each section: `id` (unique, kebab-case, prefixed with the deck key e.g. `adk-graph-routing`), `data-tone` (one of `agent tool state model human risk` — sets the accent colour of the slide), `data-title` (short name for the outline drawer).
- Put presenter notes in `<aside class="notes">…</aside>` inside the section (3–6 sentences: what to say, one analogy, one likely student question).
- Optional per-slide JS: a `<script>` after the section that calls `Deck.register("<id>", { enter(slide, step){}, step(slide, n, animate){}, leave(slide){} })`. `gsap` and `SplitText` are global. Kill your own loops in `leave`.

**Never** add slide numbers, running headers, running footers, logos, page counters, "Agenda" boilerplate, or the words "zero to hero" or "masterclass".

## 2. Visual language (already styled — use the classes, do not restyle)

The background is white. Code blocks are dark. Accents are semantic. **Colour always means the same thing:**

| Tone | Means | Node class | Panel class | Tag class | Text class |
|---|---|---|---|---|---|
| agent (blue) | agent, orchestrator, retriever, planner | `n-agent` | `k-agent` | `t-agent` | `c-agent` |
| tool (amber) | tool, function, API, external system | `n-tool` | `k-tool` | `t-tool` | `c-tool` |
| state (green) | state, session, memory, index, data, dataset | `n-state` | `k-state` | `t-state` | `c-state` |
| model (coral) | LLM / model call, training | `n-model` | `k-model` | `t-model` | `c-model` |
| human (violet) | user, human-in-the-loop, annotator | `n-human` | `k-human` | `t-human` | `c-human` |
| risk (red) | failure mode, attack, anti-pattern | `n-risk` | `k-risk` | `t-risk` | `c-risk` |

Type: `.display` (chapter/opening only), `.title` (one per slide, ≤ 2 lines, sentence case, states the point — "Parallel branches share one session state", not "Parallel agents"), `h3`, `h4`, `.lede`, `p`, `.small`, `.tiny`.

Layout: `.row`, `.grid.g2|g3|g4|g5|g-12|g-21|g-32|g-23`, `.stack`, `.stack.lg`, `.fill` (take remaining height), `.push` (push to bottom), `.vs` (left / mid / right comparison).

Components:
- `.panel` (+ `.k-<tone>`, `.tight`, `.flat`, `.hot`)
- `.tag` (+ `.t-<tone>`, `.new` for "new in 2025/2026") inside `.tags`
- `.stat` with `.n[data-to][data-dec][data-pre][data-suf]` and `.l` — numbers count up
- `.quote` — a short real quote; always with a `.cite` under it
- `.cite.codelab | .cite.repo | .cite.doc | .cite.video | .cite.paper` — `<a class="cite codelab" href="URL" target="_blank" rel="noopener"><b>Codelab</b>&nbsp;Exact codelab title</a>`. Use real, verified URLs from the research files only.
- `.code-wrap` > `.code-head` (filename) + `pre.code[data-lang=python|bash|json|yaml][data-focus="1:3-5, 2:8-9"]` > `code`. Max ~20 lines at 18px, ~24 lines with `.sm`, ~28 with `.xs`. Escape `<` as `&lt;` and `&` as `&amp;` inside code.
- `.code-wrap.term` + `pre.code[data-lang=bash]` — lines starting `$ ` get a prompt.
- `table.t` (rows can take `data-on="2:hot"`)
- `ul.ticks`, `ol.seq` (numbered circles — **only** for real sequences), `ul.clean`
- `.callout.pitfall | .callout.insight | .callout.tip`
- `.qa` > `.q` + `.a` — interview question and model answer
- `.legend` > `span.l-<tone>`
- `.bar > i` with `style="--v:72%"` and `data-fx="bar"` — animated bar
- `.badge-new` — small "NEW" mark after a heading

## 3. Diagrams (the main teaching tool)

```html
<div class="diagram" style="width:900px;height:520px"
     data-wires="user>root:flow{human}; root>a@1 [route]; root>b@1; a>merge@2:flow{state}; b>merge@2:dash; merge>root@3:bend60 [result]">
  <div class="group g-agent" style="left:250px;top:120px;width:420px;height:300px" data-step="1"><span class="gl">ParallelAgent</span></div>
  <div class="node n-human pill" id="user" style="left:0;top:220px"><span class="nt">User</span></div>
  <div class="node n-agent" id="root" style="left:300px;top:20px;width:220px"><span class="nt">Coordinator</span><span class="ns">LlmAgent</span></div>
  <div class="node n-tool" id="a" style="left:280px;top:180px;width:180px" data-step="1" data-fx="pop" data-on="3:dim"><span class="nt">Search</span></div>
  …
</div>
```

- Nodes: `.node.n-<tone>` (+ `.pill`, `.round`, `.ghost`), absolutely positioned with `left/top` in px inside the diagram; give a `width`. Inside: `.nt` (name) and `.ns` (mono subtitle).
- Groups: `.group.g-<tone>` with `.gl` label — a dashed container (e.g. a workflow agent, a vector DB, a training loop).
- Wires (in `data-wires`, `;`-separated): `a>b` arrow, `a<>b` two-way, `a--b` no arrow. Modifiers: `@n` appear at step n, `:flow` animated pulses travel along the wire, `:dash`, `{tone}` colour, `[label]`, `:bend60` / `:bend-60` curve, `:lr :rl :tb :bt :rt :lb …` force sides (from-side, to-side).
- Wires only connect `.node` elements by `id`. Leave ≥ 60px gaps between nodes so the curves read clearly. Keep the label short (≤ 18 chars).
- `data-on="n:hot"` highlights a node at step n; `data-on="n:dim"` fades it; `data-until="n"` hides it from step n.
- For anything a node graph cannot show (vector spaces, token streams, loss curves, chunk boundaries, attention, confusion matrices, drift histograms, reward curves), draw **inline SVG** and animate it: `data-fx="draw"` on an `<svg>` draws all its strokes; or use a `Deck.register` hook with gsap for a bespoke animation.

## 4. Animation requirements — every slide moves with purpose

Every slide **must** have a meaningful animated build. Motion explains; it never decorates. Use at least two of:
1. **Progressive disclosure** with `data-step="n"`: the slide tells its story in 2–6 steps (presenter presses → to advance). Example: show the problem, then the mechanism, then the code, then the pitfall.
2. **Self-drawing diagrams** with step-gated wires and `:flow` pulses that show data moving.
3. **Code walk-throughs** with `data-focus` bands that move line by line in sync with explanatory panels.
4. **Count-up numbers** (`.stat .n[data-to]`) for benchmark results and costs.
5. **Bespoke SVG/gsap animation** via `Deck.register` for the key concept of a section (at least 1 in every 4 slides). Examples: points clustering in an embedding space; a query vector finding its nearest neighbours; a document splitting into chunks; a loss curve being drawn; a reward signal flowing back; a graph executing node by node with a moving token; a state object updating key by key; a confusion matrix filling; two distributions drifting apart.

`data-fx` values: `up` (default), `fade`, `left`, `right`, `scale`, `pop`, `blur`, `draw`, `type` (typewriter), `count`, `mask` (line mask; titles get this automatically), `stagger` (children one by one), `bar`, `none`.
Titles animate automatically. Do not put `data-step` on the title.

## 5. Writing: ASD-STE100 Simplified Technical English (≥ 80% of sentences)

- One idea per sentence. Procedural sentences ≤ 20 words; descriptive ≤ 25 words.
- Active voice. Imperative for instructions ("Set `output_key`. The next agent reads it from state.").
- One word = one meaning. Use the same term every time. No idioms, no hype words ("revolutionary", "powerful", "seamless", "unlock", "leverage", "game-changer").
- Use articles ("the", "a"). Use simple verbs: use, make, get, set, send, read, write, show, stop, start, find, keep, give, do.
- Technical names (class names, papers, products) are allowed as technical names.
- Tables, lists and diagrams carry the density. Prose is short.

## 6. Depth and density — this is an expert course that also prepares students for interviews

- Each content slide teaches a **mechanism**, not a slogan: how it works inside, why it was designed this way, what it costs, when it fails, what to use instead.
- Use **real numbers** (versions, dates, benchmark scores, token costs, latency, dataset sizes) from the research files. Never invent numbers, APIs, URLs, or quotes. If the research marks something `[UNVERIFIED]`, leave it out.
- Use **current APIs and current practice (Oct 2026)**. Present older techniques (e.g. classic ReAct prompting) only as one line of history or as a contrast, then show what replaced them.
- **Codelabs, repos, docs, papers**: every technical section cites the real sources with `.cite` links (exact titles). Quote codelabs where useful with a `.quote` + `.cite.codelab`.
- **Interview lens**: every chapter ends with one interview slide: 3–4 `.qa` pairs (question visible, each answer revealed by its own step). Questions are the kind asked at Google, Anthropic, OpenAI, Meta and top startups for AI engineer / ML engineer roles: design trade-offs, failure modes, "how would you…", numbers to know.
- Put a `.callout.pitfall` on slides where engineers make a common mistake.
- Real-world examples: name the company/product and the outcome when the research supports it.

## 7. Quality checklist (check each slide before you finish)

- [ ] Fits 1392 × 740. No text below y = 824. No overlaps between nodes.
- [ ] One clear title that states the point.
- [ ] 2–6 steps of progressive disclosure, or a bespoke animation, or both.
- [ ] Semantic colours used correctly.
- [ ] ≥ 80% STE sentences. No hype words.
- [ ] Facts and links come from the research files.
- [ ] Notes written.
- [ ] Valid HTML; every `id` used in `data-wires` exists inside that diagram.

## 8. Worked example: a bespoke animation hook

```html
<section class="slide" id="rag-nn-search" data-tone="state" data-title="Nearest-neighbour search">
  <h2 class="title">A query finds its nearest chunks by angle, not by words</h2>
  <div class="grid g-32 fill">
    <svg class="interactive" id="rag-nn-svg" viewBox="0 0 800 560" width="800" height="560"></svg>
    <div class="stack lg">
      <p data-step="1">Each chunk becomes a point. Similar meaning gives nearby points.</p>
      <p data-step="2">The query becomes a point in the same space.</p>
      <p data-step="3">The index returns the <b>k</b> points with the highest cosine similarity.</p>
    </div>
  </div>
</section>
<script>
(() => {
  const NS = "http://www.w3.org/2000/svg";
  let pts = [], q, rays = [];
  Deck.register("rag-nn-search", {
    enter(slide) {
      const svg = slide.querySelector("#rag-nn-svg");
      svg.innerHTML = "";
      pts = Array.from({ length: 60 }, (_, i) => {
        const c = document.createElementNS(NS, "circle");
        const cx = 400 + Math.cos(i * 2.4) * (60 + (i * 37) % 220), cy = 280 + Math.sin(i * 2.4) * (40 + (i * 53) % 200);
        c.setAttribute("cx", cx); c.setAttribute("cy", cy); c.setAttribute("r", 7);
        c.setAttribute("fill", "var(--state)"); c.setAttribute("opacity", .55);
        svg.appendChild(c); return c;
      });
      gsap.from(pts, { scale: 0, transformOrigin: "center", duration: .6, stagger: .012, ease: "back.out(2)" });
    },
    step(slide, n, animate) {
      // build state for step n; must be correct when jumping straight to any step
    },
    leave() { gsap.killTweensOf(pts); }
  });
})();
</script>
```

Rules for hooks: deterministic (no `Math.random()` — use index-based maths so the slide looks the same every time); `step()` must render the correct state for any `n` (the presenter can go backward); use CSS variables (`var(--state)`) for colour so the theme works; keep each loop in `gsap` so `leave()` can kill it.
