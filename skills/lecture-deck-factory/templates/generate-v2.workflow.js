export const meta = {
  name: 'deck-generate-v2',
  description: 'Rebuild one deck as 100 hands-on slides (architect -> 2-slide writers -> chapter stitch -> chapter QA) plus its separate interview deck',
  phases: [
    { title: 'Outline', detail: 'deck architect (100 slides) and interview architect in parallel' },
    { title: 'Write', detail: 'one writer per 2 slides, all chapters in parallel' },
    { title: 'Stitch', detail: 'one editor per chapter makes the chunks one chapter' },
    { title: 'QA', detail: 'per chapter: build, qa.mjs, screenshot review, fix' },
    { title: 'Audit', detail: 'deck-level mix audit against the v2 rules' },
  ],
}

// args: { root, key, title, description, brief, research: [abs dirs, v2 dir first], oldOutline, interviewOld }
const ROOT = args.root
const K = args.key
const IK = `${K}-interview`
const pad = (n) => String(n).padStart(2, '0')
const PER = 2

const SLIDE = {
  type: 'object',
  properties: {
    file: { type: 'string' }, id: { type: 'string' },
    type: { type: 'string', enum: ['lab', 'buildup', 'gotcha', 'paper', 'industry', 'practices', 'concept', 'chapter', 'opening', 'qa', 'whiteboard', 'debug'] },
    title: { type: 'string' },
    content: { type: 'string' },
    visual: { type: 'string' },
    code: { type: 'string' },
  },
  required: ['file', 'id', 'type', 'title', 'content', 'visual'],
}
const OUTLINE = {
  type: 'object',
  properties: {
    chapters: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          num: { type: 'integer' }, name: { type: 'string' }, tone: { type: 'string' },
          scenario: { type: 'string' },
          research_files: { type: 'array', items: { type: 'string' } },
          slides: { type: 'array', items: SLIDE },
        },
        required: ['num', 'name', 'tone', 'scenario', 'research_files', 'slides'],
      },
    },
  },
  required: ['chapters'],
}

const READ = `Read ${ROOT}/engine/AUTHORING.md completely — section 9 (v2 rules) overrides the rest. Look at ${ROOT}/decks/_demo/slides/06-handson.html and 07-buildup.html for the v2 component markup.`
const USER = `The user's verdict on version 1: "too much theory, no actual examples ... make it really hands on with code samples, more concrete, more best practices, more gotchas / challenges, more industry practices, more arxiv papers from the last 3 months ... more animation, more visual". Treat this as the top requirement.`

const architect = () => agent(`You are the course architect for the 100-slide v2 rewrite of the deck "${args.title}" (key ${K}).
${USER}
Brief: ${args.brief}
1. ${READ}
2. Read ${args.research[0]}/00-VERIFIED.md first, then every file in ${args.research[0]}. Skim the older research in ${args.research.slice(1).join(', ')} and the v1 outline ${args.oldOutline} (keep its good structure; fix its theory-heavy parts).
3. Design EXACTLY 100 slides in 10-12 chapters that follow the section 9.2 mix (>=60 code slides, >=30 lab slides in 6-10 labs, >=12 gotcha, >=10 paper (2026-07-23..2026-10-23 only, from the verified list), >=8 industry, >=6 practices, <=12 concept, 0 qa). Chapter 0 = 2 opening slides (type opening). Each other chapter: 1 chapter opener (type chapter), then hands-on slides. Each chapter has ONE named running business scenario that its labs grow step by step.
4. Per slide: file "cNN-MM-slug.html", id "${K}-cNN-slug" (must start with "${K}-cNN-"), type, title (<= 70 chars, states the point), content (dense and concrete: exact code to show and from which research file + lab, the output, the numbers, the gotcha text, the paper id + number, the company + numbers, the citations), visual (the diagram or bespoke animation and its step-by-step build), code (the snippet source or empty).
5. research_files per chapter: 2-6 absolute paths (v2 files first).
6. Write ${ROOT}/decks/${K}/OUTLINE.md (readable, with a mix-count table at the top) and ${ROOT}/decks/${K}/meta.json = {"title": ${JSON.stringify(args.title)}, "description": ${JSON.stringify(args.description)}}.
Return the outline via structured output.`, { label: `architect:${K}`, phase: 'Outline', schema: OUTLINE, agentType: 'general-purpose' })

const iarchitect = () => agent(`You are the architect of the separate interview deck for "${args.title}" (deck key ${IK}).
1. ${READ} Section 9.6 defines this deck.
2. Read the old interview slides ${args.interviewOld} (keep the best questions), ${args.research[0]}/00-VERIFIED.md, and the gotchas/industry/arxiv files in ${args.research[0]}.
3. Design 24-30 slides in 4-6 chapters: chapter 0 = 1 opening slide; each chapter = 1 opener + qa slides (3 Q&A pairs each, types qa) + 1 whiteboard slide (system-design prompt + animated reference architecture) + 1 debug slide (buggy code, answer step highlights the bug). Files "cNN-MM-slug.html", ids "${IK}-cNN-slug".
4. Write ${ROOT}/decks/${IK}/OUTLINE.md and ${ROOT}/decks/${IK}/meta.json = {"title": ${JSON.stringify('Interview drills: ' + args.title)}, "description": "Interview questions, system-design whiteboards and debug-this drills for the deck."}.
Return the outline via structured output.`, { label: `architect:${IK}`, phase: 'Outline', schema: OUTLINE, agentType: 'general-purpose' })

const writer = (deck, ch, slides, part) => agent(`You write slides ${part} of chapter ${ch.num} "${ch.name}" (tone ${ch.tone}) of the deck "${deck === K ? args.title : 'Interview drills: ' + args.title}" (key ${deck}).
${USER}
1. ${READ}
2. Read ${ROOT}/decks/${deck}/OUTLINE.md (whole-deck flow) and these research files fully: ${ch.research_files.join(', ')}. Also ${args.research[0]}/00-VERIFIED.md. Use only facts, numbers, code and URLs from them; skip [UNVERIFIED] items.
3. Chapter scenario: ${ch.scenario}. The whole chapter: ${JSON.stringify(ch.slides.map((s) => `${s.type}: ${s.title}`))}.
4. Write ONLY these slides, each as its own file in ${ROOT}/decks/${deck}/slides/ with exactly these file names and ids:
${JSON.stringify(slides, null, 1)}
Follow section 9 strictly: .kicker by slide type; complete verified code with data-focus walk-through and a synced .steps-rail; output pane on labs; gotcha/paper/checks components; >= 3 build steps; a bespoke Deck.register animation on at least one of your slides (deterministic, correct for any step, killed in leave()); big diagrams with >= 80 px gaps and short wire labels; <= 45 words of prose; title <= 70 chars; .cite links; speaker notes (3-6 sentences). Fill the canvas (content should reach y >= 650) without overflowing 1392x740.
5. Do not edit any other file. Run \`node ${ROOT}/build.mjs ${deck}\` and fix errors in your files.
Return the list of files you wrote.`, { label: `write:${deck}:c${pad(ch.num)}:p${part}`, phase: 'Write', agentType: 'general-purpose' })

const stitcher = (deck, ch) => agent(`You are the chapter editor for chapter ${ch.num} "${ch.name}" of deck key ${deck}. Writers wrote its slides in parallel: ${ROOT}/decks/${deck}/slides/c${pad(ch.num)}-*.html.
1. ${READ} Read ${ROOT}/decks/${deck}/OUTLINE.md.
2. Read every slide of the chapter in order. Make it one chapter: the running scenario "${ch.scenario}" grows lab by lab with consistent names, variables, file names and versions; no repeated definitions; one term per concept; each slide hands off to the next; kickers numbered consistently (Lab N · step k of m).
3. Edit only this chapter's files. Run \`node ${ROOT}/build.mjs ${deck}\`.
Return a short list of changes.`, { label: `stitch:${deck}:c${pad(ch.num)}`, phase: 'Stitch', agentType: 'general-purpose' })

const qa = (deck, ch) => agent(`You are the QA + polish editor for chapter ${ch.num} "${ch.name}" of deck key ${deck}. Files: ${ROOT}/decks/${deck}/slides/c${pad(ch.num)}-*.html.
1. ${READ}
2. Run: \`cd ${ROOT} && node build.mjs ${deck} && node qa.mjs ${deck} ${deck}-c${pad(ch.num)}-\` (timeout ~5 min). It writes ${ROOT}/qa/${deck}/report.json and screenshots ${ROOT}/qa/${deck}/NN-<id>.png at each slide's final step. If qa.mjs fails or hangs, review the HTML by careful reading (say so in your reply).
3. Read EVERY screenshot of this chapter and judge it like a top presentation designer and a senior engineer: overflow, overlaps, wires crossing nodes or labels, crowding, sparse slides, small diagrams, weak hierarchy, code that is incomplete or would not run, missing output pane, too much prose, long titles, missing animation.
4. Fix every issue in this chapter's files only. Re-run build + qa and re-check screenshots. Up to 3 rounds until report.json shows no issues for this chapter.
Return a summary of fixes and any remaining problems.`, { label: `qa:${deck}:c${pad(ch.num)}`, phase: 'QA', agentType: 'general-purpose' })

const chunks = (arr, n) => Array.from({ length: Math.ceil(arr.length / n) }, (_, i) => arr.slice(i * n, i * n + n))

const runDeck = (deck, outline) => {
  if (!outline || !outline.chapters) { log(`${deck}: architect failed`); return null }
  const n = outline.chapters.reduce((a, c) => a + c.slides.length, 0)
  log(`${deck}: outline ready — ${outline.chapters.length} chapters, ${n} slides`)
  return pipeline(outline.chapters,
    async (ch) => {
      await parallel(chunks(ch.slides, PER).map((s, i) => () => writer(deck, ch, s, i + 1)))
      return stitcher(deck, ch)
    },
    (st, ch) => qa(deck, ch))
}

phase('Outline')
const [main, inter] = await Promise.all([
  architect().then((o) => runDeck(K, o)),
  iarchitect().then((o) => runDeck(IK, o)),
])

phase('Audit')
const audit = await agent(`You audit the finished deck ${ROOT}/decks/${K}/slides against ${ROOT}/engine/AUTHORING.md section 9.2. Count slides by kicker/type, slides with code (pre.code), Deck.register hooks, .qa slides (must be 0), paper slides with ids in the 2026-07-23..2026-10-23 window. Run \`cd ${ROOT} && node build.mjs ${K} && node qa.mjs ${K}\` and summarise report.json. Fix small problems directly (any slide). Return a table of counts vs targets and a list of remaining issues.`, { label: `audit:${K}`, phase: 'Audit', agentType: 'general-purpose' })

return { main: main ? main.length : 0, interview: inter ? inter.length : 0, audit: audit ? audit.slice(0, 2000) : null }
