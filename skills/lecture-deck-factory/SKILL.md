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

## Version 2 (hands-on rewrite, 2026-10-23 evening)

The user rejected v1 (60 slides) as "too much theory, no actual examples", with quiz slides mixed in and weak animation. What changed:

- **Engine:** wire labels are placed on their curve where they hit no node or other label, with a background pill on a top SVG layer. Titles are 42 px and at most 70 characters. New components: `.kicker`, `.lab-head`, `.code-wrap.out` output pane, `.gotcha`, `.paper`, `.code-wrap.bad/.good`, `.steps-rail`, `ul.checks`, `.delta`. Reference slides: `decks/_demo/slides/06-handson.html`, `07-buildup.html`.
- **Contract:** `engine/AUTHORING.md` section 9 sets the slide types (lab, build-up, gotcha, paper, industry, practices, concept, chapter) and the mix per 100 slides: ≥60 with code, ≥30 lab slides in 6–10 scenario labs, ≥12 gotcha, ≥10 papers from the last 3 months, ≥8 industry, ≥6 practices, no quiz slides.
- **QA additions** in `qa.mjs`: `sparse` (content ends above y=620), `long-title`, `wordy` (>110 words of prose), `qa-in-main-deck`.
- **Interview Q&A** moved to its own deck per topic (`<key>-interview`): Q&A, whiteboard and debug-this slides.
- **Research v2** (`research-v2/<key>/`): per deck, 3 arXiv sweeps (last 3 months, via the arXiv API sorted by submittedDate), 4 lab researchers (complete code, verified against the library source on GitHub), 1 gotchas, 1 industry, then a verifier that writes `00-VERIFIED.md`. One workflow per deck, run as 3 workflows at once, because each workflow caps at 16 concurrent agents.
- **Generation v2:** `templates/generate-v2.workflow.js`. The deck architect and the interview architect run in parallel, then one writer per 2 slides, a stitcher per chapter, QA per chapter, and a final mix audit. Run one workflow per deck.
- **PyPI is blocked by Avast HTTPS scanning** (certificate UnknownIssuer for uv and pip). Do not bypass it. Verify APIs against GitHub source through WebFetch instead. If local execution is needed, ask the user to allow PyPI in Avast.
- Archive the old version before regenerating (`git tag`, then `git mv decks/<key>/slides archive/v1/<key>/`). Don't push `docs/` until the new deck passes QA, so the public site keeps showing the old version.

## Zero-context review panel (user guidance, 2026-10-23)

The user asked for "a good verifier with zero context, on taste" and "QA on content as well: teacher shoes, student shoes". Every chapter now goes through this after the normal QA:

1. **Capture what the audience sees.** `node qa.mjs <key> <key>-cNN- --frames` saves one PNG per build step (`NN-<id>-sK.png`), the final frame (`NN-<id>.png`), `notes-<prefix>.json` (speaker notes) and `report-<prefix>.json` (one report per chapter, so parallel chapters don't overwrite each other).
2. **Three judges in parallel, with ZERO context.** They get no AUTHORING rules, no outline, no research and no authorship. That way they judge the slides the way a real audience would, not against our own checklist. Prompts are in `templates/panel-prompts.js`.
   - **Designer (taste):** world-class presentation designer. Scores hierarchy, space, legibility, diagram quality, the motion story across the build frames, and polish. Gives exact fixes.
   - **Teacher:** must teach the chapter tomorrow. Sees the frames and the speaker notes. Checks flow, that prerequisites come before use, one idea per slide, concrete examples, misconceptions and usable notes. Fact-checks doubtful claims on the web and lists `factual_errors` with evidence.
   - **Student:** engineer with 2 years of Python, new to the topic. Says where they got lost, what is missing to reproduce the code next Monday (install, version, env var, file, output), and the question they would ask.
3. **Fix with context.** A separate fixer (which does read AUTHORING.md and the research) applies every defect scored below **8/10** and every factual error. On disagreements, the student wins on clarity, the teacher on correctness and flow, the designer on layout and motion. It re-shoots the frames.
4. **Loop:** the panel judges again, up to 2 rounds, until no slide is below 8 and there are no factual errors. Remaining low scores are logged, never dropped silently.

Wired into `templates/generate-v2.workflow.js` as the `Panel` and `Fix` phases, pipelined per chapter: a chapter enters the panel as soon as its own QA is done.

**Rules of thumb:**
- Never give a judge the rules it is checking against. Zero context is what makes it a real verifier.
- Judges see every build step, not only the final frame. Motion is part of the quality.
- Keep judging and fixing in separate agents. A judge that also fixes stops being critical.
- Score scale: 7 = a solid conference talk, 9 = the best talk of the year. The pass mark is 8.
