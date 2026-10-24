---
name: lecture-deck-factory
description: Build deeply researched, heavily animated 60-slide lecture decks (plain HTML + GSAP, white professional look, ASD-STE100 writing, codelab/repo citations, interview Q&A per chapter) with parallel agent teams, then publish them to GitHub Pages. Use when the user asks for a new animated slideshow / lecture deck / course deck on a technical topic, or wants to add a deck to the dlmastery/masterclasses repo.
---

# Lecture deck factory

This is how the decks in **dlmastery/masterclasses** were made (Oct 2026: Google ADK 2.0, RAG, and Customizing AI). Repeat these steps for a new topic.

**The kit is the repo.** Engine, build, QA and preview are already in https://github.com/dlmastery/masterclasses. Do not rebuild them. Only add a new deck folder and its research.

```
engine/deck.js, deck.css   runtime: steps, self-drawing diagrams, wires, count-ups, code focus, outline, notes, theme
engine/AUTHORING.md        THE slide contract. Every architect, writer and QA agent reads it first.
decks/<key>/meta.json      {"title", "description"}
decks/<key>/OUTLINE.md     written by the architect
decks/<key>/slides/cNN-MM-slug.html   one file per slide
research-<key>/*.md        research notes + CRITIC-corrections.md (overrides the others)
build.mjs                  node build.mjs [key]  -> docs/<key>/index.html + docs/index.html landing page
serve.mjs                  node serve.mjs 8766   -> local preview of docs/
qa.mjs                     node qa.mjs <key> [idPrefix] -> qa/<key>/report.json + one PNG per slide
skills/lecture-deck-factory/templates/   the two workflow scripts + a real config
```

## The pipeline

| Phase | Agents | Output | Time it took |
|---|---|---|---|
| 0. Preflight | you | login works, network OK, repo cloned, `npm install` | 2 min |
| 1. Research | 1 per topic (8–12 per deck), all decks in parallel | `research-<key>/NN-topic.md` | 26 min for research + critic together (27 agents) |
| 2. Critic | 1 per deck | `CRITIC-corrections.md` + 60-slide arc | (included above) |
| 3. Outline | 1 architect per deck | `OUTLINE.md`, `meta.json`, structured outline | ~10+ min (the serial bottleneck) |
| 4. Write | 1 per chapter (or per 2 slides) | slide files | not measured yet |
| 5. Stitch | 1 per chapter, only when chunked | consistent chapter | not run yet |
| 6. QA | 1 per chapter, pipelined right after its writer | fixed slides, clean `report.json` | not measured yet |
| 7. Publish | you | commit + push; Pages serves `/docs` | 1 min |

While phases 1–2 run, you (the main session) work on anything else that's needed, e.g. engine features. Never write slides yourself in the main session while writers run.

## Step 0: Preflight (do not skip — this failed once)

1. Make a test call that reaches the API. On 2026-10-23 **all 18 research agents failed** because Avast WebShield blocked `api.anthropic.com` and the login had expired. Fix login (`/login`) and the network block first. Do not fan out until one agent call works.
2. `git clone https://github.com/dlmastery/masterclasses && cd masterclasses && npm install`. Playwright uses the local Chromium in `%LOCALAPPDATA%/ms-playwright` (run `npx playwright install chromium` if it is missing).
3. In the clone: `git config user.name dlmastery`, `git config user.email <your email>`, `git config core.autocrlf false`. (The first commit failed because no git identity was set.)
4. Start the preview: `node serve.mjs 8766` and a rebuild loop (`node build.mjs` every 20 s). Give the user the links: `http://localhost:8766/<key>/`.
5. Only one session may own a deck folder. If another Claude session is already building, do not start writers from a second session — they overwrite each other's slide files.

## Step 1: Write the deck config

Copy `templates/decks.example.json` and edit it. One entry per deck:

- `key`: short deck id (`adk`, `rag`, `custom`). Slide ids must start with `<key>-cNN-`.
- `title`, `description`: show on the landing page.
- `brief`: the user's request, rewritten as explicit demands. Put in every "must" the user said (e.g. "latest Oct 2026 only, classic ReAct only as one line of history", "code about every second slide", "quote codelabs with URLs").
- `ctx`: one sentence that tells researchers what the deck is.
- `research`: one or more `{dir, topics}`. Each topic is `[file-stem, dense prompt]`. Good topics name the exact products, papers, APIs, versions and codelab searches to cover. 8–12 topics per deck. The example file has the 42 real topics used for the three decks.
- `today`: the current date. Researchers use it to reject stale material.

## Step 2: Research + critic

```
Workflow({ scriptPath: "skills/lecture-deck-factory/templates/research.workflow.js", args: <config> })
```

- Researchers write 1500–4000-word Markdown notes with verified facts, versions, numbers, real code with source URLs, quotes, interview Q&A and "Slide ideas".
- The critic reads all of a deck's files, resolves contradictions against primary sources, fills gaps and writes `CRITIC-corrections.md` plus a 60-slide arc.
- **The web-search budget is shared and ran out during the critic pass.** The critic prompt tells it to prefer direct fetches of primary URLs (PyPI JSON API, GitHub API/raw files, arXiv API). Items it can't check stay marked `[UNVERIFIED]`, and writers leave them out.
- What the critics caught (so trust them over single files): the docs pages lagged behind PyPI/CHANGELOG (Python floor, task mode in graphs). A default value was a docs example, not the source default (RetryConfig 3 vs 5). A codelab URL returned 404. A repo had been renamed (adk-samples → adk-recipes). A spec path had changed (agent-card.json). A quote was misquoted. A model ID had been retired. 20–29 corrections per deck.
- Want a second wave on a gap? Run a small extra research workflow into another dir (as with `research-frontier`, `research-adk-platform`) and add that dir to the deck's `research` list.

## Step 3: Generate (outline → write → QA)

```
Workflow({ scriptPath: "skills/lecture-deck-factory/templates/generate.workflow.js", args: { ...config, slidesPerWriter: 0 } })
```

- **Architect** (1 per deck): reads `AUTHORING.md` and all the research, then designs exactly 60 slides in 9–11 chapters. Chapter 0 is the opening plus a course map. Each other chapter has an opener first and an interview `.qa` slide last. For each slide it specifies the file, id, a title that states the point, dense content, the visual with its animation build, and the code. It also picks the research files per chapter.
- **Writers** read the contract, the demo slides, `OUTLINE.md` and their research files, write only their files, and run `build.mjs`.
- **QA** runs `build.mjs` + `qa.mjs` for its chapter, reads every screenshot like a designer, fixes problems, and repeats up to 3 times.
- `pipeline()` means each deck's writers start as soon as *its* outline is ready, and each chapter's QA starts as soon as *its* writer is done. Nothing waits for the slowest deck.
- **More parallelism:** `slidesPerWriter: 2` gives ~90 writers instead of ~30, plus a stitcher per chapter that removes repeats and aligns terms and analogies. It is ~3× faster to write. This mode has not yet been run end to end, so check the first chapter's output. One writer per slide (`1`) is fastest but chapters lose their thread.
- The architect is the serial bottleneck (~10 min, very long output). Don't restart it. If you need speed there, split it in two: an arc architect (chapters + slide titles), then a detailer per chapter in parallel.

## Step 4: Publish

```
node build.mjs && git add -A && git commit -m "Add <key> deck" && git push
```

The repo is public, and GitHub Pages serves `main:/docs` at **https://dlmastery.github.io/masterclasses/<key>/**. The landing page lists every deck automatically. `.gitignore` excludes `node_modules/`, `qa/`, `.playwright-mcp/` and `.claude/`. Scan for secrets before every push to a public repo.

For a brand-new repo instead: `gh repo create <owner>/<name> --public --source=. --push`, then `gh api -X POST repos/<owner>/<name>/pages -f "source[branch]=main" -f "source[path]=/docs"`.

## Rules that every deck keeps (they live in AUTHORING.md — edit them there)

- 1600×900 canvas with a usable 1392×740 area. No slide numbers, headers, footers or logos.
- Colour is semantic: blue agent, amber tool, green state/data, coral model, violet human, red risk.
- Every slide moves with purpose: steps, self-drawing diagrams with `:flow` wires, code focus walk-throughs, count-ups, and a bespoke `Deck.register` SVG/GSAP animation in at least 1 of every 4 slides. Animations are deterministic (no `Math.random`) and render correctly when going backwards.
- ≥80% ASD-STE100 sentences, no hype words, and titles that state the point.
- Facts, numbers, code and URLs come only from the research files. Codelabs are quoted with `.cite` links.
- Every chapter ends with an interview slide (3–4 Q&A pairs, with answers revealed one step at a time).
- Never use the words "zero to hero" or "masterclass" on slides (the repo name is fine).

## Lessons

- **Status pings:** a recurring ping asks for a 2–4 line status. Answer from the files on disk and the workflow journals (`~/.claude/projects/<proj>/<session>/subagents/workflows/<run>/journal.jsonl`), never from memory.
- **qa.mjs hung** at first. It needed an explicit local Chromium path, step logging, and `gsap.globalTimeline.timeScale(40)` so builds finish fast. Chapter openers with only entrance animations were wrongly flagged as "static", so the check now accepts any `data-fx`, diagram, count-up, code focus or SVG.
- **The served stylesheet failed** once because the tiny server reset connections. `serve.mjs` now uses `no-store` and simple file reads.
- **Several briefs in a row** marked "slideshow1": treat each as its own deck on the shared engine, and ask the user once whether one replaces another.
- **Commit early.** Push the engine and research before writing starts so nothing is lost. Push again after each deck's QA phase.
