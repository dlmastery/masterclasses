export const meta = {
  name: 'deck-generate',
  description: 'Generate animated 60-slide decks: one architect per deck, then parallel slide writers, then per-chapter QA/fix',
  phases: [
    { title: 'Outline', detail: 'one architect per deck designs 60 slides in ~10 chapters' },
    { title: 'Write', detail: 'one writer per chapter (or per N slides), all decks in parallel' },
    { title: 'Stitch', detail: 'only when slidesPerWriter > 0: one editor per chapter joins the chunks' },
    { title: 'QA', detail: 'per chapter: build, automated QA, screenshot review, fix' },
  ],
}

// args = decks.example.json plus optional "slidesPerWriter".
//   slidesPerWriter: 0 (default) -> one writer per chapter (~30 writers for 3 decks). This is the mode that ran.
//   slidesPerWriter: 2           -> one writer per 2 slides (~90 writers) + a stitcher per chapter. Faster; not yet run end to end.
// Run: Workflow({ scriptPath: '<this file>', args: <config object> })
const ROOT = args.root
const PER = args.slidesPerWriter || 0
const pad = (n) => String(n).padStart(2, '0')

const OUTLINE_SCHEMA = {
  type: 'object',
  properties: {
    chapters: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          num: { type: 'integer' },
          name: { type: 'string' },
          tone: { type: 'string' },
          research_files: { type: 'array', items: { type: 'string' } },
          slides: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                file: { type: 'string' }, id: { type: 'string' }, title: { type: 'string' },
                content: { type: 'string' }, visual: { type: 'string' }, code: { type: 'string' },
              },
              required: ['file', 'id', 'title', 'content', 'visual'],
            },
          },
        },
        required: ['num', 'name', 'tone', 'research_files', 'slides'],
      },
    },
  },
  required: ['chapters'],
}

const architect = (d) => agent(`You are the course architect for an animated 60-slide lecture deck.
Deck key: ${d.key}. Title: "${d.title}".
Brief: ${d.brief}

1. Read ${ROOT}/engine/AUTHORING.md completely (the slide contract: components, diagrams, animation, ASD-STE100 writing, interview lens).
2. Skim ALL research files in: ${d.research.map((r) => ROOT + '/' + r.dir).join(', ')} (read headings, key facts, slide ideas; read deeply where needed). A file named CRITIC-corrections.md or 09-critic-corrections.md, if present, overrides other files.
3. Design exactly 60 slides in 9-11 chapters with a strong teaching flow: first principles -> mechanisms -> building -> advanced/state of the art -> production -> open challenges. Chapter 0 = 2-3 opening slides (a striking opening slide with a self-animating hero diagram, a "map of the course" slide). Every other chapter starts with ONE chapter-opener slide (class chapter) and ends with ONE interview slide (.qa). Never use the words "zero to hero" or "masterclass". Title of each slide states the point (sentence case).
4. For each slide specify: file name "cNN-MM-slug.html" (NN = chapter 2-digit, MM = slide 2-digit within chapter), id "${d.key}-cNN-slug" (MUST start with "${d.key}-cNN-"), title, content (dense: the exact facts, numbers, comparisons, code idea, sources/URLs to cite, interview angle), visual (the diagram/SVG and its step-by-step animation build), code (which real snippet, from which research file, or empty).
5. research_files per chapter: the 2-5 research file paths (absolute) a writer must read for that chapter.
6. Write the outline also as readable Markdown to ${ROOT}/decks/${d.key}/OUTLINE.md, and write ${ROOT}/decks/${d.key}/meta.json as {"title": ${JSON.stringify(d.title)}, "description": ${JSON.stringify(d.description)}}.
Return the outline via the structured output.`, { label: `architect:${d.key}`, phase: 'Outline', schema: OUTLINE_SCHEMA, agentType: 'general-purpose' })

const writer = (d, ch, slides, part) => agent(`You write ${part ? `part ${part} of ` : ''}chapter ${ch.num} of an animated lecture deck. Quality bar: the best technical course a student has ever seen — deep, precise, beautiful, interview-ready.
Deck: "${d.title}" (key ${d.key}). Deck brief: ${d.brief}

Steps:
1. Read ${ROOT}/engine/AUTHORING.md completely and follow it exactly. Look at the example slides in ${ROOT}/decks/_demo/slides/ for markup.
2. Read ${ROOT}/decks/${d.key}/OUTLINE.md for the whole-deck flow (do not duplicate other chapters${part ? ' or the other parts of this chapter' : ''}).
3. Read these research files fully: ${ch.research_files.join(', ')}. Use only facts, numbers, code and URLs found there. Leave out anything marked [UNVERIFIED].
4. The whole chapter ${ch.num} "${ch.name}" (tone ${ch.tone}) is: ${JSON.stringify(ch.slides.map((s) => s.title))}.
Write ONLY these slides, each as its own file in ${ROOT}/decks/${d.key}/slides/ using exactly these file names and ids:
${JSON.stringify(slides, null, 1)}
Rules: chapter-opener slides use class "slide chapter" with .ch-num showing the chapter number and a .display title. Every slide has a meaningful animated build (steps, self-drawing diagrams with :flow wires, code focus walk-throughs, count-ups, or a Deck.register SVG/gsap hook). ${part ? 'Make at least 1 bespoke Deck.register animation if your slides include the chapter\'s key concept.' : 'At least 1 bespoke Deck.register animation in this chapter.'} Frequent real code snippets with data-focus walk-throughs. Cite codelabs/repos/docs/papers with .cite links. ASD-STE100 writing (>=80%). Data-dense but within 1392x740. Speaker notes in every slide. Do not edit any other file. Do not edit the engine.
5. Build and check: run \`node ${ROOT}/build.mjs ${d.key}\` and fix any error in your files.
Return a short list of the files you wrote.`, { label: `write:${d.key}:c${pad(ch.num)}${part ? `:p${part}` : ''}`, phase: 'Write', agentType: 'general-purpose' })

const stitcher = (d, ch) => agent(`You are the chapter editor for chapter ${ch.num} "${ch.name}" of "${d.title}" (key ${d.key}). Several writers wrote its slides in parallel: ${ROOT}/decks/${d.key}/slides/c${pad(ch.num)}-*.html.
1. Read ${ROOT}/engine/AUTHORING.md and ${ROOT}/decks/${d.key}/OUTLINE.md.
2. Read every slide of this chapter in order. Make it read as one chapter: remove repeated definitions, use one term per concept, keep analogies and running examples consistent, make each slide hand off to the next, keep one bespoke Deck.register animation for the key concept, keep tones consistent.
3. Edit only this chapter's files. Run \`node ${ROOT}/build.mjs ${d.key}\`.
Return a short list of changes.`, { label: `stitch:${d.key}:c${pad(ch.num)}`, phase: 'Stitch', agentType: 'general-purpose' })

const qa = (d, ch) => agent(`You are the QA + polish editor for chapter ${ch.num} "${ch.name}" of the deck "${d.title}" (key ${d.key}). Slide files: ${ROOT}/decks/${d.key}/slides/c${pad(ch.num)}-*.html.
1. Read ${ROOT}/engine/AUTHORING.md.
2. Run: \`cd ${ROOT} && node build.mjs ${d.key} && node qa.mjs ${d.key} ${d.key}-c${pad(ch.num)}-\` (timeout ~5 min). It writes ${ROOT}/qa/${d.key}/report.json (issues for this chapter) and screenshots ${ROOT}/qa/${d.key}/NN-<id>.png (each slide at its final step). If qa.mjs itself fails or hangs, skip it and review the HTML by careful reading instead (note that in your reply).
3. Open (Read) EVERY screenshot of this chapter's slides and judge it like a top presentation designer: overflow, overlaps, crowding, misaligned diagrams, tiny or clipped text, empty areas, weak hierarchy, wires crossing through nodes, unreadable labels.
4. Fix every issue in the slide files (only this chapter's files). Also fix: missing animation build, hype words, non-STE sentences, missing notes, missing citations, broken code escaping.
5. Re-run build + qa and re-check screenshots. Repeat up to 3 times until clean.
Return: a short summary of what you fixed and any remaining problems.`, { label: `qa:${d.key}:c${pad(ch.num)}`, phase: 'QA', agentType: 'general-purpose' })

const chunks = (arr, n) => Array.from({ length: Math.ceil(arr.length / n) }, (_, i) => arr.slice(i * n, i * n + n))

const writeChapter = async (d, ch) => {
  if (!PER) return writer(d, ch, ch.slides, 0)
  const parts = chunks(ch.slides, PER)
  await parallel(parts.map((s, i) => () => writer(d, ch, s, i + 1)))
  return stitcher(d, ch)
}

const results = await pipeline(
  args.decks,
  (d) => architect(d),
  (outline, d) => {
    if (!outline || !outline.chapters) { log(`${d.key}: architect failed`); return null }
    const n = outline.chapters.reduce((a, c) => a + c.slides.length, 0)
    log(`${d.key}: outline ready — ${outline.chapters.length} chapters, ${n} slides. Writing all chapters in parallel.`)
    return pipeline(outline.chapters, (ch) => writeChapter(d, ch), (w, ch) => qa(d, ch))
  },
)

return results.map((r, i) => ({ deck: args.decks[i].key, chapters: r ? r.length : 0, qa: r ? r.map((x) => (x ? String(x).slice(0, 600) : null)) : null }))
