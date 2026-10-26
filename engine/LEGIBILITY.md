# Legibility rules (v3). These override AUTHORING.md section 9 wherever they conflict.

The v2 slides failed because each slide tried to hold a whole lab: 25-35 lines of code at 13px,
5-9 panels, captions, output, links, and a diagram, all on one 1600x900 canvas. A projected slide
must be readable from the back of a room. One slide = one idea = one focal element.

## Hard limits (qa.mjs enforces them; a slide with any of these issues is not done)
- **Code**: at most 16 lines per code block, font size 17px or more (the default `pre.code` is 18px; `.sm` = 16px is the minimum and only for a second, small block). Lines at most ~70 characters, so they fit without shrinking. Never set `font-size` below 16px on code, or below 14px on anything, in a per-slide `<style>`.
- **Panels**: at most 3 top-level panels per slide (a code block, an output pane, a diagram/SVG, a gotcha card, a paper card, a steps rail, a table each count as one). Title and kicker do not count. Typical good shapes:
  - code (left, 60%) + animated diagram or output (right)
  - big diagram/SVG (full width) + one caption line
  - bad code / good code + one delta line
  - one paper card + one chart that shows its number
- **No overflow, no clipping, no text outside its box, no wire through a label or a node.**
- **Prose**: at most 35 words on the slide outside code. One caption region; captions change per step with `data-step="k" data-until="k+1"`.
- **Cites/links**: at most one `.cites` row, at the bottom, one or two links.

## Whole programs live in the repo, not on the slide
- Put every complete, runnable lab file in `labs/adk/<lab-folder>/` (for example `labs/adk/lab1-refund-tools/agent.py`, plus a short `README.md` with the pinned install line, env vars and the run command). Copy the code exactly from the current slides and the research; do not invent APIs.
- The slide shows only the excerpt that carries the idea (the 6-16 lines that matter), with `# ...` where you cut. Put the full path in the code head: `labs/adk/lab1-refund-tools/agent.py · excerpt`.
- If a lab step needs more than one excerpt, make more slides. Splitting one crowded slide into 2 or 3 clear slides is the expected fix. The deck may grow to ~140 slides.

## One running scenario
- One company for the whole ADK deck: **Acme**. Teams may differ (Acme refund desk, Acme claims desk, Acme back office), but never Northwind or another name. Order ids keep the form `A-1001`.

## Motion
- Keep a step build on every slide (3+ steps) and keep or improve the bespoke `Deck.register` hooks. When you split a slide, give each new slide its own id and move or rewrite its hook so it targets only elements on that slide.
- Animated state must match the code (counts only rise, a join shows 1/3, 2/3, 3/3, etc.).

## Correctness
- `research-v2/adk/00-VERIFIED.md` overrides everything else. Keep google-adk 2.13.0, `gemini-3.5-flash`, `GOOGLE_GENAI_USE_ENTERPRISE`. Do not change an API you have not verified there.
- Example output that was not executed stays labelled `illustrative`.
