# Lecture decks

Animated lecture decks built on one shared engine (GSAP + Prism, plain HTML):

- **adk**: Google ADK 2.0, workflows, and agentic design patterns
- **rag**: RAG state of the art and agentic RAG
- **custom**: Customizing modern AI (SFT, RL, RAG) and data-centric AI

Live: https://dlmastery.github.io/masterclasses/

## Layout
- `engine/`: deck runtime (`deck.js`, `deck.css`) and the slide authoring contract (`AUTHORING.md`)
- `decks/<name>/slides/*.html`: slide sources
- `docs/`: built output, served by GitHub Pages
- `research*/`: source research notes and critic corrections

## Commands
```
npm install
node build.mjs [deck]     # build into docs/
node serve.mjs 8766       # local preview
node qa.mjs <deck>        # automated slide QA
```
Keys: → / Space next, ← back, O outline, N notes, F fullscreen, T theme.
