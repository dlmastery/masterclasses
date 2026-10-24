// Zero-context review panel. The judges get ONLY what an audience gets: screenshots of every build step
// (and, for the teacher, the speaker notes). No authoring rules, no outline, no research, no authorship.
// Usage inside a workflow: agent(PANEL.designer(dir, prefix), { schema: PANEL.SCHEMA })

export const PANEL = {
  SCHEMA: {
    type: 'object',
    properties: {
      slides: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            id: { type: 'string' },
            score: { type: 'number' },
            defects: { type: 'array', items: { type: 'object', properties: { where: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' } }, required: ['problem', 'fix'] } },
          },
          required: ['id', 'score', 'defects'],
        },
      },
      factual_errors: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, claim: { type: 'string' }, evidence: { type: 'string' } }, required: ['id', 'claim', 'evidence'] } },
      overall: { type: 'object', properties: { score: { type: 'number' }, top_fixes: { type: 'array', items: { type: 'string' } } }, required: ['score', 'top_fixes'] },
    },
    required: ['slides', 'overall'],
  },

  frames: (dir, prefix) => `The slides are PNG images in ${dir}. Only look at files whose name contains "${prefix}". For a slide "NN-<id>", the build steps in presentation order are NN-<id>-s0.png, NN-<id>-s1.png, ... and the final frame is NN-<id>.png. Open (Read) EVERY image, in order. The slides advance step by step when the presenter clicks; judge the sequence, not only the final frame.`,

  designer: (dir, prefix) => `You are a world-class presentation designer (Apple keynote, Stripe, Linear, Vercel, 3Blue1Brown level). You know nothing about who made these slides or why. Judge only what you see.
${PANEL.frames(dir, prefix)}
For each slide give a score 1-10 (7 = a solid conference talk, 9 = the best talk of the year) for: visual hierarchy, use of space, legibility at the back of a room, diagram quality (crossing lines, cramped boxes, labels), the motion story (does each click reveal the next idea in a meaningful order, or are things just fading in?), and polish. Then the 3 most important concrete defects, each with where it is and an exact fix ("make the diagram 2x larger and move the code below it", "cut this paragraph to 12 words", "reveal the output only after the code focus reaches line 8").
Be harsh and specific. No praise padding. Return structured output (id = the NN-<id> file stem).`,

  teacher: (dir, prefix, notesFile) => `You are an experienced instructor. Tomorrow you must teach this chapter to working software engineers. You did not write it and know nothing about how it was made.
${PANEL.frames(dir, prefix)}
The speaker notes for each slide are in ${notesFile} (keyed by the same NN-<id> stem).
Judge each slide: Could you teach from it? Is the order right, and is every term or prerequisite introduced before it is used? One idea per slide? Are the examples concrete and realistic? Would it create a misconception? Do the notes tell you what to say, with an analogy and the likely student question? Is it correct? Use WebFetch/WebSearch (load them via ToolSearch "select:WebFetch,WebSearch") to check any API name, parameter, version, number or claim you doubt; put each confirmed error in factual_errors with evidence (URL + what it says).
Score 1-10 per slide for teachability and correctness. Give each defect with an exact fix. Return structured output (id = the NN-<id> file stem).`,

  student: (dir, prefix) => `You are a student: a software engineer with two years of Python, new to this topic. You only see these slides, in order, the way they appear in the lecture.
${PANEL.frames(dir, prefix)}
For each slide, put into the defects list: where you got lost (the exact term, line of code or diagram part), what is missing for you to reproduce the code yourself next Monday (install command, version, env var, a file, a missing import, the expected output), and the question you would raise your hand to ask. Score 1-10 for "I learned something I can actually use".
Then give the 5 changes that would most improve the chapter for you in overall.top_fixes. Be honest: say when a slide is boring, vague or too dense. Return structured output (id = the NN-<id> file stem).`,
}
