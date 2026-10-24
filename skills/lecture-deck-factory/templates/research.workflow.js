export const meta = {
  name: 'deck-research',
  description: 'Deep research for one or more lecture decks: parallel topic researchers, then one accuracy critic per deck',
  phases: [
    { title: 'Research', detail: 'one researcher per topic, all decks in parallel' },
    { title: 'Critic', detail: 'one completeness + accuracy critic per deck' },
  ],
}

// args = the JSON in decks.example.json: { root, today, decks: [{ key, ctx, research: [{ dir, topics: [[file, prompt], ...] }] }] }
// Run: Workflow({ scriptPath: '<this file>', args: <config object> })
const ROOT = args.root
const TODAY = args.today

const RULES = `
Today is ${TODAY}. Use WebSearch and WebFetch heavily (load via ToolSearch "select:WebSearch,WebFetch"). Prefer PRIMARY sources: official docs, GitHub repos (README, CHANGELOG, releases, source), arXiv papers, codelabs.developers.google.com, official blogs, conference talks on YouTube. Newest material first; older techniques only as history.
RULES:
- Verify every API name, class name, import path, CLI command, paper title/year and benchmark number. State version numbers. Mark uncertain items [UNVERIFIED]. Never invent.
- Capture REAL short code snippets (5-25 lines) adapted from official docs/codelabs/repos, each with its source URL.
- For every codelab, repo, paper or video cited: exact title + URL.
- Write a dense, structured Markdown file at the path given (use the Write tool), 1500-4000 words: key facts, dates, numbers, code, step-by-step flows (diagrams in words), quotable lines (with source), real-world examples (companies/products), likely interview questions with crisp answers, and a "Slide ideas" section (6-10 slides: title + which visual/animation explains it best).
- Final reply: a 10-line summary + the file path.
`

phase('Research')
const jobs = args.decks.flatMap((d) => d.research.flatMap((r) => r.topics.map(([key, prompt]) => ({ d, dir: r.dir, key, prompt }))))
const results = await parallel(jobs.map((j) => () =>
  agent(`You are a research agent for ${j.d.ctx}\n${RULES}\nWrite your file to: ${ROOT}/${j.dir}/${j.key}.md\n\nTopic: ${j.prompt}`,
    { label: `${j.dir}:${j.key}`, phase: 'Research', agentType: 'general-purpose' })
))
const ok = results.filter(Boolean).length
log(`Research done: ${ok}/${jobs.length}`)
if (ok === 0) return { error: 'all researchers failed: check login / network (see SKILL.md, Lessons)' }

phase('Critic')
const critics = await parallel(args.decks.map((d) => () => {
  const dirs = d.research.map((r) => `${ROOT}/${r.dir}`)
  return agent(`You are the completeness + accuracy critic for ${d.ctx}\n${RULES}
The web-search budget may already be low: prefer direct WebFetch of known primary URLs (PyPI JSON API, GitHub API / raw files, arXiv API, official docs) over searches.
Read ALL markdown files in: ${dirs.join(', ')}. Then:
1. List contradictions between files and resolve each against the primary source.
2. Find important missing topics for a complete course and research them.
3. Double-check the most important version numbers, dates, benchmark numbers and codelab URLs (a URL counts as verified only if it returns 200; compare with a made-up path as a 404 control).
Write ${dirs[0]}/CRITIC-corrections.md: corrections table, gap research, and a recommended 60-slide narrative arc (first principles -> state of the art) in 8-10 sections, with one line per slide.`,
    { label: `critic:${d.key}`, phase: 'Critic', agentType: 'general-purpose' })
}))

return { ok, total: jobs.length, critics: critics.map((c) => (c ? c.slice(0, 1500) : null)) }
