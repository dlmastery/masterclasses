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

Type: `.display` (chapter/opening only), `.title` (one per slide, ≤ 70 characters, one line preferred, never 3 lines, sentence case, states the point — "Parallel branches share one session state", not "Parallel agents"), `h3`, `h4`, `.lede`, `p`, `.small`, `.tiny`.

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
- **No interview / quiz slides in the main decks.** Interview Q&A lives in its own deck (`<key>-interview`). See section 9.
- Put a `.callout.pitfall` on slides where engineers make a common mistake.
- Real-world examples: name the company/product and the outcome when the research supports it.

## 7. Quality checklist (check each slide before you finish)

- [ ] Matches the v2 slide types and mix in section 9.
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


## 9. Version 2 rules (Oct 2026 rewrite) — these override anything above

The first version was rejected: "too much theory, no actual examples". Every deck is now **hands-on first**. Theory appears only as the short mechanism that explains the code on the same slide.

### 9.1 Slide types (use the `.kicker` line above the title to name the type)

| Type | Kicker | Must contain |
|---|---|---|
| **Lab** | `<span class="pill">Lab N</span> scenario · step k of m` | `.lab-head` with the run command, a complete code block with `data-focus` walk-through (2–4 focus steps), an `.code-wrap.out` output pane, a `.steps-rail` or short panel that explains the focused lines. |
| **Build-up** | `Build` | One feature added to the running scenario: a `.code-wrap.bad` / `.code-wrap.good` before/after pair, or a diff-like walk-through, and the measured effect (`.delta`). |
| **Gotcha** | `<span class="pill">Gotcha</span> area` | 1–3 `.gotcha` cards (Symptom / Cause / Fix, exact error text when the research has it) and the fix in code. |
| **Paper** | `<span class="pill">arXiv</span> Mon 2026` | 1–3 `.paper` cards for papers from **2026-07-23 .. 2026-10-23** only (id, title, finding with the exact number, "what to change on Monday"), plus an animated diagram of the method. |
| **Industry** | `<span class="pill">In production</span> Company` | Named company/product, its architecture as an animated diagram, scale/cost/quality numbers, the lesson, `.cite`. |
| **Practices** | `Best practices` | `ul.checks` (✓ do / ✕ don't) with 6–10 specific, testable items, each with a short reason; optionally a config/code snippet. |
| **Concept** | (none) | Only when a mechanism must be seen: a large bespoke animation (`Deck.register`) that shows the mechanism moving, plus ≤ 3 short lines. |
| **Chapter opener** | — | `class="slide chapter"`, the chapter number, a `.display` title, one lede line, and a self-animating mini-diagram of what the chapter builds. |

### 9.2 Mix per 100-slide deck (the architect plans to these numbers)

- ≥ 60 slides show real code (Lab + Build-up + Gotcha fixes + Practices with config).
- ≥ 30 Lab slides, organised as 6–10 labs. Each lab is a sequence of 3–6 slides on ONE named business scenario (e.g. "Acme refunds agent", "HR policy search", "support-ticket triage") that grows step by step.
- ≥ 12 Gotcha slides, ≥ 10 Paper slides (last 3 months), ≥ 8 Industry slides, ≥ 6 Practices slides.
- ≤ 12 Concept slides. ≤ 11 chapter openers. 0 interview slides.

### 9.3 Code rules

- Code is complete: real imports, real names, no `...` in the visible lines unless you mark an omitted block with a comment. 12–28 lines per block (`.sm`/`.xs` sizes). Show the pinned versions in `.lab-head` (e.g. `google-adk==2.13.0`).
- Use only code that the research marks VERIFIED (`research-v2/<key>/00-VERIFIED.md`) or that comes from an official codelab/quickstart/sample with its URL. Never put "check the exact kwarg names" on a slide: if you are not sure, do not show it.
- Every lab slide has an output pane. Label illustrative output in its head (`output · illustrative`).
- Use `.ok`, `.err`, `.dim` spans in output panes. Show the real error text on gotcha slides.

### 9.4 Animation and visuals (more motion, bigger visuals)

- Every slide has ≥ 3 build steps or a bespoke animation, usually both.
- ≥ 1 in every 3 slides has a bespoke `Deck.register` gsap/SVG animation: tokens moving through a graph, state keys updating, a vector finding neighbours, chunks splitting, a loss/reward curve drawing, a confusion matrix filling, a request trace waterfall, a retry/backoff timeline, a cache hit/miss counter, a judge score distribution, etc.
- Diagrams are large: when a slide has a diagram, it takes ≥ 40% of the canvas. Leave ≥ 80 px between nodes. ≤ 7 labelled wires per diagram. Labels ≤ 16 characters. Route wires with `:lr`/`:tb` and `:bendN` so they do not cross nodes.
- Code walk-throughs move with the explanation: each `data-focus` step reveals the matching `.steps-rail` item (same step number).
- Text budget: ≤ 45 words of prose per slide outside code, tables and cards.

### 9.5 Sources

- Research for v2: `research-v2/<key>/*.md` (labs, recent arXiv, gotchas, industry) and `00-VERIFIED.md` (overrides everything). The older research folders are background.
- Cite every lab (codelab/quickstart/repo), every paper (arXiv id) and every case (company post) with `.cite` links.

### 9.6 Interview deck (`<key>-interview`)

- 20–30 slides. Chapter openers per topic area, then `.qa` slides with 3 Q&A pairs each (each answer is its own step), plus "whiteboard" slides: a system-design prompt and an animated reference architecture, and "debug this" slides: a code block with a bug, the answer step highlights it with `data-focus`.
- Questions match what Google, Anthropic, OpenAI, Meta and top startups ask AI/ML engineers in 2026: trade-offs, failure modes, numbers to know, "how would you build…".

### 9.7 What the zero-context panel caught in v1 (do not repeat)

- **Animated state must match the code and the claim.** Counters only go up in a loop (round 1, 2, 3). A join shows 1/3, 2/3, 3/3. A concurrency cap of 2 shows 2 running and 2 queued. If the slide says "checks 10 rules", show 10 or say "5 of 10".
- **Every name in a code block is defined or imported**, or stubbed in one visible line (`Feedback = ...`). No undefined `process_input`, `fallback` or `coder_agent`. Use one name per thing (not `make_uppercase` and `make_upper_case`).
- **Loops in code really stop and re-check:** show the bound and the final verification.
- **One caption per region per step.** When captions replace each other in the same place, give each `data-step="k" data-until="k+1"`. The engine now shows exactly one. Don't add a second pill on top of an existing wire label: highlight the wire instead.
- **One slide = one idea.** Don't hide a second slide behind the last click. Split it.
- **A "run it Monday" block on the first slide of every lab:** pinned install line, env vars, folder tree.
- **Versions on slides match the version the chapter uses** (e.g. "tested on google-adk 2.13.0").
- No meta text on slides ("pattern composed from verified APIs", "adapted, check kwargs").
