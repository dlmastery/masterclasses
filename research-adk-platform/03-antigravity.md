# 03 — Google Antigravity: the agentic development platform (state as of 2026-10-23)

> Scope: Antigravity IDE (Nov 2025), Antigravity 2.0 desktop app / CLI / SDK / IDE extensions (May 2026 onward), artifacts and the review loop, browser agent, models, rules/skills/subagents/hooks/sidecars, and how it relates to Gemini CLI, Jules, Firebase Studio and ADK.
> Research note: the web-search budget for this session ran out, so every fact here comes from **direct fetches of primary pages** (antigravity.google, developers.googleblog.com, codelabs.developers.google.com, adk.dev, google.github.io/agents-cli, github.com/google-gemini/gemini-cli, jules.google, firebase.studio). Items I could not re-check are marked **[UNVERIFIED]**.

---

## 1. Timeline and rename history

| Date | Event | Source |
|---|---|---|
| 2025-05-19 | Jules launched (async cloud coding agent, Google Labs) | https://jules.google/docs/changelog/ |
| 2025 (mid) | Gemini CLI launched, open source, Apache-2.0. By May 2026 it had 100k+ GitHub stars and 6,000 merged PRs | https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/ |
| 2025-07 | Google licensed Windsurf tech and hired its leadership. Widely reported as the origin of the Antigravity team **[UNVERIFIED in this pass]** | press |
| **2025-11-18** | **"Introducing Google Antigravity, a new era in AI-assisted software development"**: IDE + Agent Manager, public preview, free for individuals, macOS/Windows/Linux, launched with Gemini 3 | https://antigravity.google/blog/introducing-google-antigravity |
| 2025-11-20 | Developers Blog: "Build with Google Antigravity, our new agentic development platform". Nano Banana Pro added to Antigravity the same day | https://developers.googleblog.com/en/build-with-google-antigravity-our-new-agentic-development-platform/ |
| 2025-12-17 | Gemini 3 Flash in Antigravity | antigravity.google/blog/gemini-3-flash-in-google-antigravity |
| 2026-02-19 | Gemini 3.1 Pro in Antigravity | antigravity.google/blog/gemini-3-1-pro-in-google-antigravity |
| **2026-05-19 (I/O 2026)** | **Antigravity 2.0** (standalone desktop app, no IDE), **Antigravity CLI** (`agy`), **Antigravity SDK** (`pip install google-antigravity`), Gemini 3.5 Flash, Antigravity in Gemini Enterprise, plan changes, Gemini CLI transition announced | antigravity.google/blog/introducing-google-antigravity-2 and the posts dated the same day |
| 2026-06-18 | Gemini CLI and the Gemini Code Assist IDE extensions **stop serving consumer tiers** (free, Google AI Pro/Ultra, Code Assist for individuals). Enterprise Code Assist Standard/Enterprise is unaffected | Developers Blog (above). The gemini-cli README says: "Gemini CLI was replaced by Antigravity CLI on June 18th, 2026." |
| 2026-07-21 | Gemini 3.6 Flash | antigravity blog |
| 2026-08-12 | Custom agents (`.agents/agents/*.md`) | antigravity.google/blog/introducing-custom-agents |
| 2026-08-20 | IDE extensions (VS Code, Visual Studio, JetBrains, Zed, Xcode). Antigravity bundled into Gemini Enterprise Standard/Plus | /blog/antigravity-ide-extensions, /blog/antigravity-enterprise |
| 2026-08-21 | Remote Control (drive local sessions from a browser at antigravity.google.com) | /blog/remote-control-for-antigravity |
| 2026-08-27 | Teamwork (`/teamwork-preview`), a multi-agent propose/critique/refine framework | /blog/teamwork-when-ai-becomes-a-research-partner |
| 2026-09-01 | Gemini 3.8 Flash | antigravity blog |
| 2026-09-28 | Custom agents shipped inside Google plugins (Firebase, Flutter, Play) | /blog/custom-agents-in-google-plugins |
| 2026-10-07 | App v2.21.1: "Scheduled Tasks" renamed **"Automations"** | /docs/changelog |
| 2026-10-13 | Gemini 4 Argon in Antigravity (Pro/Ultra/Enterprise; App + CLI, **not** the IDE) | /blog/gemini-4-argon-in-google-antigravity |
| 2026-10-19 | **Legacy IDE "workflows" stop working.** They must be migrated to Skills | /docs/migration/workflows-to-skills/ |
| 2026-10-22 | App v2.26.0 (latest at time of writing) | /docs/changelog |
| 2026-11-02 | Claude Sonnet/Opus 4.6 and GPT-OSS 120B are scheduled for removal | /docs/models |
| 2027-03-22 | Firebase Studio sunset. The notice says "Move your code to Google AI Studio or Google Antigravity" | https://firebase.studio/ |

**Naming to get right on slides**
- "Agent Manager" (Nov 2025 IDE surface, also called "Manager", "mission control") → **Antigravity 2.0** standalone app (May 2026). The 2.0 post says a future IDE release will remove the Agent Manager from the IDE. In the CLI, `/agents` opens an "Agent Manager panel".
- "Workflows" (`.agents/workflows/*.md`) → **Skills** (`SKILL.md`, Agent Skills open standard adopted May 2026).
- "Gemini CLI extensions" → **Antigravity plugins** (`agy plugin import gemini`).
- "Scheduled Tasks" → **Automations** (Oct 7, 2026). Built-in cron background processes are **Sidecars**.
- Enterprise channel: "Gemini Enterprise" (the former Agentspace) and "Gemini Enterprise Agent Platform" (the name the Antigravity pages use for the Google Cloud platform; formerly Vertex AI). Covered in file 01/02 of this research set.

---

## 2. The product family (Oct 2026)

| Surface | What it is | Key facts |
|---|---|---|
| **Antigravity App (2.0)** | Standalone, agent-first desktop "command center", with no IDE | Projects (multi-folder, own permissions), conversations, subagents, Automations, Remote Control, Review pane with Git, embedded terminal, generative-UI HTML artifacts. Runs on macOS (Apple Silicon/Intel), Windows, Linux and Googlebook |
| **Antigravity IDE** | The original Nov 2025 editor + Agent Manager (VS Code-based; fork lineage widely reported) | Tab completions, inline commands, side-panel agent, browser subagent. IDE versions v1.11.2–v2.5.5 are listed in the changelog |
| **Antigravity CLI** | `agy`, terminal-first, built in **Go**. Shares the harness and settings with the App | Install: `curl -fsSL https://antigravity.google/cli/install.sh \| bash` (macOS/Linux), `irm https://antigravity.google/cli/install.ps1 \| iex` (Windows) |
| **Antigravity SDK** | Python `google.antigravity`, Apache-2.0, preview since 2026-05-19 | Same runtime as the App and CLI. Default model Gemini 3.5 Flash at launch |
| **IDE extensions** | "Google Antigravity" extension for VS Code, Visual Studio, JetBrains (2026.2.1+), Zed, Xcode (27 beta 6+) | Share conversations and customizations with the App |
| **Remote Control** | Drive a local or cloud machine's session from any browser | Push notifications when an agent needs input |

The docs overview describes a single agent harness that is **co-trained with Gemini models** and runs every surface. The CLI blog says permissions set in one surface apply to the others. Conversations are not shared by default, but CLI conversations can be viewed in the App via `@conversation`.

---

## 3. The four tenets (Nov 2025 launch) and the core loop

From https://antigravity.google/blog/introducing-google-antigravity:
1. **Trust.** Tool calls are grouped into *tasks* with summaries. The agent shows **Artifacts** rather than raw logs ("Verify with Artifacts, not logs", Developers Blog).
2. **Autonomy.** Two surfaces. The **Editor view** handles synchronous work. The **Manager** is a "mission control" for spawning and observing many agents across workspaces in parallel.
3. **Feedback.** Asynchronous comments on artifacts work like Google Docs comments, plus select-and-comment on screenshots. They are incorporated **without stopping** the agent.
4. **Self-improvement.** A **knowledge base** that agents read from and write to (snippets, architecture, step sequences), visible in the Agent Manager. *Status in 2.0:* the current docs nav does not list "Knowledge". The 2.0 equivalents appear to be rules, skills and the Teamwork "shared knowledge directory". **[UNVERIFIED whether Knowledge Items still ship in 2.0]**

**Architecture flow (diagram in words): "Plan → Act → Verify → Review"**
User prompt → (optional `/grill-me` clarifying Qs) → agent in **Planning mode** writes **Task list** + **Implementation plan** artifact → **review gate** (artifact review policy: *Request review* = halt; *Always proceed* = skip) → user comments inline → agent revises plan or proceeds → agent edits code (diff artifact), runs terminal (sandboxed per permission preset), opens **browser subagent** to test localhost → captures **screenshots + browser recording** → writes **Walkthrough** artifact → user reviews diffs in Review pane → commit via integrated Git.

---

## 4. Artifacts: what they are, the review loop, and the policies

- **Types (launch):** task lists, implementation plans, walkthroughs, screenshots, browser recordings (Developers Blog, 2025-11-20).
- **Types (2026 docs):** rich Markdown plans, code diffs, architecture diagrams, images, browser recordings (https://antigravity.google/docs/artifacts). Since App v2.11.0 (2026-08-26) there are also **generative-UI inline HTML artifacts** (KaTeX, Chart.js, Plotly). Since v2.13.0 there is a virtualized viewer for large artifacts.
- The Getting Started codelab names the file `implementation_plan.md`. Task List, Implementation Plan, Walkthrough, Code diffs and Screenshots show in the **Auxiliary Pane**.
- **Plan review flow** (https://antigravity.google/docs/implementation-plan/): `/plan` → plan artifact → comment ("reduce scope", "change stack") → **Proceed**, or **Review** to submit all comments as one feedback message → the agent revises and re-requests review, or starts implementing.
- **Artifact review policy** (Settings › Agent; https://antigravity.google/docs/artifact-review/): `Request review` (recommended) | `Always proceed`. v2.17.0 (2026-09-22) added a separate **Plan Review Policy** setting.
- **CLI:** `/artifact` lists artifacts and lets you approve, reject or open them. A status-bar notification appears when approval is needed.

**Original Nov 2025 IDE onboarding options [UNVERIFIED in this pass; from the 2025 codelab version]:** a development-mode choice (Agent-driven / Agent-assisted / Review-driven / Custom), a terminal execution policy (Off / Auto / Turbo), a review policy (Always proceed / Agent decides / Request review), and the conversation modes **Planning** vs **Fast**.

---

## 5. Browser agent

From https://antigravity.google/docs/ide/browser:
- A **Browser Subagent** opens, reads and controls a **local Chrome**. Typical uses are testing dev sites, reading docs and automating tasks.
- It captures **screenshots** and saves **action videos as interactive artifacts** (browser recordings).
- Security: a two-layer **URL allowlist/denylist** and an **isolated Chrome profile** separate from your personal one. You can disable it with Settings › Browser › Browser Tools.
- In 2.0 you enable it explicitly with **`/browser`**, which "requires Google Chrome browser to be your default browser to start a debugging session" (Getting Started codelab).
- Model used by the browser subagent: **[UNVERIFIED]** (launch coverage said a Gemini computer-use model).

---

## 6. Models (from https://antigravity.google/docs/models, Oct 2026)

| Model | Reasoning levels | Plans |
|---|---|---|
| **Gemini 4 Argon** | High | AI Pro, Ultra, Enterprise. **Not in the IDE** |
| Gemini 3.8 Flash | Low/Med/High | All plans incl. Free & AI Plus |
| Gemini 3.7 Flash, 3.6 Flash, 3.1 Pro | L/M/H (3.1 Pro: Low/High) | Enterprise only |
| Claude Sonnet 5.5 / Opus 5.5 (Thinking) | — | AI Pro (non-trial), Ultra, Enterprise. Enterprise access goes through ADC to a Vertex project with access (App v2.24.0) |
| Claude Sonnet/Opus 4.6, GPT-OSS 120B | — | Removed **2026-11-02** |
| Nano Banana 2 | — | Image generation for mockups and diagrams. Not user-selectable |

At launch (Nov 2025) the lineup was Gemini 3 Pro, Claude Sonnet 4.5 and GPT-OSS. Rate limits refreshed **every 5 hours** and scaled with work done rather than prompt count.

**Plans (2026-05-19, /blog/changes-to-antigravity-plans):** Google AI Pro is $20/mo. A new Ultra tier is $100/mo with **5×** Pro tokens. Ultra at $200/mo (down from $250) has **20×**. Flash and Pro now draw from one shared pool billed at API pricing. Non-Gemini models keep a separate fixed limit. AI credits now serve only as overage. **Enterprise:** included in Gemini Enterprise Standard/Plus (2026-08-20). It adds budget caps in Cloud Billing, shared token pools, one-toggle audit logging (prompts, tool executions, artifacts), WIF + ADC sign-in, regional inference (US/EU/Global, v2.5.0), and a commitment that customer code is never used to train base models.

**Numbers worth quoting (Gemini 4 Argon post, 2026-10-13):** 100K+ Alphabet users use Argon in internal Antigravity monthly. Over 4 weeks, agentic code rose **35%** and post-submit rollbacks fell **30%**. Bug triage closed 97 of 134 bugs (72.4%) in under 3 hours. A Fortran→Rust migration ran 1.8× faster. Financial planning turned 15.5 human-direction hours into about 335 human-equivalent hours across 80 workflows. AirAsia CTO: more than 50% of production QA code is generated with Antigravity (enterprise post).

---

## 7. Customization layer: rules, skills, custom agents, hooks, sidecars, MCP, plugins

### 7.1 Rules (https://antigravity.google/docs/rules)
- Workspace: `AGENTS.md` / `GEMINI.md` at any directory level, `.agents/AGENTS.md`, and `.agents/rules/*.md` (legacy `.agent/rules`). Rules are loaded walking up from each touched file. They are cumulative, and the most specific one wins.
- Global: `~/.gemini/GEMINI.md`, `~/.gemini/config/AGENTS.md`, and `~/.gemini/config/rules/*.md` (frontmatter required).
- Frontmatter: `trigger: always_on | model_decision | glob | manual`, plus `description` and `globs`. Note that camelCase `alwaysOn` is **silently discarded**, which is a classic failure mode.
- Limits: **24 KB per file** and a **20,000-token aggregate** budget for always-on rules. When the budget is exceeded, the largest files are demoted to pointers. Includes use `@[label](path)`.

```markdown
---
trigger: glob
globs: "**/agents/*.py"
description: ADK agent conventions
---
Always define `root_agent`; use `output_key` for state handoff; never hardcode API keys.
```
*(Illustrative example built from the documented keys.)*

### 7.2 Skills (https://antigravity.google/docs/skills)
- A folder containing `SKILL.md` (frontmatter `name` optional, `description` required) plus optional `scripts/`, `examples/` and `resources/`.
- Paths: `.agents/skills/<name>/` (workspace), `~/.gemini/config/skills/<name>/` (App/IDE global), `~/.gemini/antigravity-cli/skills/` (CLI global).
- **Progressive disclosure:** the agent sees name and description at start, reads the full `SKILL.md` when relevant, then executes it.
- Workflows→Skills migration: run `/migrate-workflows`, or run `mkdir -p .agents/skills/deploy-staging` and move the file to `SKILL.md`. Invocation stays `/<name>`. If names collide, the skill wins. **Workflows stopped working 2026-10-19.**

### 7.3 Custom agents / subagents (https://antigravity.google/docs/subagents)
- Files: `.agents/agents/<name>.md` or `.agents/agents/<name>/agent.md`, `~/.gemini/config/agents/`, and `plugins/<p>/agents/`.
- Frontmatter keys: `name`, `description`, `tools`, `mainAgent` (default true), `subagent` (default true; makes the agent callable via `invoke_subagent`), `model` (`inherit|flash|pro`), `commandExecutionPolicy` (`off|auto|eager|sandbox`, default `sandbox`), `mcpServers`, `skills`/`plugins`. Blog examples also use `permissionMode` (`acceptEdits`, `plan`), and the changelog adds `inheritCustomizations` (v2.9.1) and hooks in custom agents (v2.17.0).
- Workspace modes for subagents: `branch` (an isolated **git worktree**), `inherit`, `share`. Worktrees are cleaned up when a subagent is killed.
- Gotcha: a **misspelled tool name can hang the subagent**.

Verbatim example from https://antigravity.google/blog/introducing-custom-agents:
```markdown
---
name: dependency-modernizer
description: Upgrades packages and confirms tests pass.
model: flash
tools:
  - view_file
  - replace_file_content
  - run_command
skills:
  - skills/package-upgrade-rules
mainAgent: true
subagent: true
permissionMode: acceptEdits
commandExecutionPolicy: auto
---
# Core Instructions
Check config files, update target dependencies, run tests, and verify the build.
```
Run it with `agy --agent dependency-modernizer`. The Play plugin's read-only verifier agent (`permissionMode: plan`, `model: gemini-3.8-flash`) ends every report with **APPROVED / CONDITIONAL / BLOCKED**, which makes it a ready-made "verifier gate" example.

### 7.4 Lifecycle hooks (https://antigravity.google/docs/hooks): this is where verifiers plug in
- Files: `.agents/hooks.json` (workspace; takes precedence) and `~/.gemini/config/hooks.json` (global). In the CLI, `/hooks` inspects them.
- Events: `SessionStart`, `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, `Stop`.
- Handler: `{type:"command", command, timeout(30s default)}`. `PreToolUse`/`PostToolUse` take an array of `{matcher: <regex on tool name>, hooks:[...]}`.
- Hooks control the agent through **JSON on stdout**, not exit codes:
  - `PreToolUse` → `decision`: `allow | auto_approve | deny | ask | force_ask | deny_unless_prior_grant`, plus `reason`, `overwrite` (patch args) and `permissionOverrides`.
  - `PreInvocation`/`SessionStart` → `injectSteps` (`systemMessage`, `userMessage`, `ephemeralMessage`, `toolCall`).
  - `PostInvocation` → `terminationBehavior: force_continue | terminate`.
  - **`Stop` → `decision: "continue"` keeps the loop running and injects `reason`.** This is the hook for "don't stop until tests pass" loop engineering. The input `fullyIdle` flag says whether background tasks have finished.

Sketch of a per-step verifier (structure follows the documented schema; script name illustrative):
```json
{
  "verify-tests": {
    "enabled": true,
    "Stop": [ { "type": "command", "command": "python .agents/verify.py", "timeout": 120 } ],
    "PreToolUse": [ { "matcher": "run_command", "hooks": [ { "command": "python .agents/guard.py" } ] } ]
  }
}
```
Here `verify.py` runs `pytest` / `adk eval`. On failure it prints `{"decision":"continue","reason":"3 eval cases failed: ..."}`.

### 7.5 Sidecars / Automations (https://antigravity.google/docs/sidecars/)
Verbatim hourly agent:
```json
{
  "description": "Hourly agent to triage review requests.",
  "builtin": "schedule",
  "args": ["0 * * * *", "agentapi", "new-conversation", "Give me a summary of incoming review requests."]
}
```
Each sidecar lives at `~/.gemini/config/sidecars/<id>/sidecar.json`, with `restart_policy: always|on-failure|never`. Sidecars are disabled by default and are enabled in `~/.gemini/config/config.json`. The UI path is `/schedule`. Automations default to Gemini 3.5 Flash, and since v2.24.0 you can choose Flash Lite, Flash or Pro.

### 7.6 MCP and plugins
- MCP config: `~/.gemini/config/mcp_config.json` (global) and `.agents/mcp_config.json` (workspace). Remote servers use **`serverUrl`**, which replaces Gemini CLI's `url`/`httpUrl`.
- **Build with Google plugins** (Settings › Customizations): Firebase, Google Cloud, Antigravity SDK, Android CLI, Dart/Flutter, Chrome DevTools, Data Agent Kit, Maps, Science, Modern Web. The **Google Developer Knowledge MCP server** installs separately from the MCP Store. A plugin marketplace exists since v2.18.1.

### 7.7 Permissions / sandbox (https://antigravity.google/docs/permissions)
- App presets: **Request Review / Default / Auto (Preview) / Turbo**. The terminal sandbox is on for Default and Auto. Under Default, sandboxed commands have **no network access**.
- Lists: Deny > Ask > Allow.
- CLI `toolPermission`: `request-review` (default), `proceed-in-sandbox`, `always-proceed` (`--dangerously-skip-permissions`), `strict`. `agentMode`: `auto`, `accept-edits`.

---

## 8. Antigravity SDK (agent harness as a library)

From https://antigravity.google/blog/introducing-google-antigravity-sdk (verbatim):
```bash
pip install google-antigravity
```
```python
from google.antigravity import Agent, LocalAgentConfig

config = LocalAgentConfig()
async with Agent(config) as agent:
    response = await agent.chat("What files are in the current directory?")
    print(await response.text())
```
- Policies: `from google.antigravity.hooks.policy import deny, allow, ask_user`. Shell access is denied by default (`confirm_run_command()`), and `policy.allow_all()` makes the agent fully autonomous.
- Hooks come in three classes: **Inspect** (non-blocking), **Decide** (blocking; policies are built on this) and **Transform** (modifying). There are nine hook points, including tool-error recovery and context compaction.
- Other features: built-in tools, Python functions, MCP servers (stdio/SSE/Streamable HTTP), skills via `skills_paths`, subagents, thinking levels MINIMAL–HIGH, `structured_output()`, `conversation_id` persistence and `usage_metadata`.
- Roadmap: a remote harness on Google Cloud via the Interactions API, TypeScript/Go, Gemma, plugins.
- **SDK vs ADK.** The Antigravity SDK programs a *coding/computer-use agent harness*. ADK 2.0 is the *framework for building your own production agents* (graph workflows, evals, deploy to Agent Runtime). The SDK page does not mention ADK. Treat them as complementary.

---

## 9. How teams use Antigravity to build ADK 2.0 agents

1. **Give the coding agent ADK expertise** (https://adk.dev/tutorials/coding-with-ai/):
   - Run `uvx google-agents-cli setup`. This installs Agents CLI plus ADK skills (scaffolding, eval, deploy, tracing, Python API quick reference) into Antigravity CLI, Claude Code, Codex and others.
   - **ADK Docs MCP server.** In Antigravity go to agent panel › … › Manage MCP Servers › View raw config and add:
   ```json
   {"mcpServers":{"adk-docs-mcp":{"command":"uvx","args":["--from","mcpdoc","--with","mcp<2","mcpdoc","--urls","AgentDevelopmentKit:https://adk.dev/llms.txt","--transport","stdio"]}}}
   ```
   - The docs index lives at `https://adk.dev/llms.txt` and `https://adk.dev/llms-full.txt`. Note that google.github.io/adk-docs now 301-redirects to **adk.dev**.
2. **Scaffold:** `agents-cli create -d agent_runtime` (deployment targets `agent_runtime | cloud_run | gke | none`; flags include `--adk`, `--prototype`, `--session-type`, `--bq-analytics`, `--agent-gateway`). Source: https://google.github.io/agents-cli/cli/
3. **Plan in Antigravity:** `/grill-me` → `/plan` → review the `implementation_plan.md` with comments → Proceed. A glob rule for `agents/**` encodes ADK conventions.
4. **Loop with verifiers:** a `Stop` hook runs `agents-cli eval run --dataset ...`. A failing metric returns `decision:"continue"`. A read-only `eval-critic` custom agent (`permissionMode: plan`) emits APPROVED/BLOCKED.
5. **Iterate locally:** `agents-cli playground`, `agents-cli run "hi" --mode adk`. Then use `agents-cli eval generate | grade | compare BASELINE CANDIDATE | analyze | optimize`.
6. **Ship:** `agents-cli deploy -d agent_runtime --project P --region R`, then `agents-cli publish gemini --registration-type a2a|adk` to register in Gemini Enterprise.
7. **Operate:** a Sidecar/Automation runs nightly regression evals (`0 2 * * *`). Remote Control lets you approve fixes from your phone.

---

## 10. Relationship map: Gemini CLI, Jules, Firebase Studio, AI Studio

- **Gemini CLI → Antigravity CLI.** On 2026-05-19 the Developers Blog post "An important update: Transitioning Gemini CLI to Antigravity CLI" (Dmitry Lyalin, Taylor Mullen) announced the move. Consumer tiers were cut off on **2026-06-18**. Enterprise Code Assist Standard/Enterprise, and Gemini CLI used with paid Gemini / Agent Platform API keys, continue. The Antigravity CLI "took inspiration from core Gemini CLI product and harness components" and is written in Go. Migration (https://antigravity.google/docs/cli/gcli-migration):
  - `GEMINI.md`/`AGENTS.md` are still read.
  - MCP moves to `mcp_config.json`.
  - Extensions become plugins via `agy plugin import gemini`, and custom commands become skills.
  - `.gemini/skills/` becomes `.agents/skills/` (manual move).
  - Session tokens move to the OS keyring.
  - The gemini-cli README says Gemini CLI "has not been optimized for Gemini 4 Argon."
- **Jules.** An *asynchronous cloud* agent: GitHub repo → Cloud VM → plan → PR. It remains a separate Google Labs product, with Jules Tools CLI (`@google/jules`, 2025-10-02), a REST API (2025-10-03), a Critic agent, a Planning Critic (2026-01-26, **9.5% fewer task failures**), CI Fixer (2026-02-19) and Gemini 3.1 Pro (2026-03-09). Limits are 15/100/300 tasks per day on the free/Pro/Ultra plans. Contrast: Antigravity runs **local-first** (your machine, Remote Control), while Jules runs **cloud VMs + PRs**. The Jules changelog does not mention Antigravity.
- **Firebase Studio.** A cloud IDE with an App Prototyping agent, sunset **2027-03-22**. Users are told to move to Google AI Studio or Antigravity. The Antigravity docs nav has a "Firebase Studio" migration page, which I could not fetch **[UNVERIFIED]**. Firebase capability now ships as the **Firebase plugin** with a Security Rules custom agent.
- **AI Studio.** The browser "vibe-coding" and prompt surface. Antigravity is the pro desktop/CLI path.

---

## 11. Design patterns Antigravity embodies (for the "loop / graph / verifier" part of the deck)

| Pattern | Antigravity mechanism |
|---|---|
| **Plan-then-execute with human gate** | `/plan` + Request review policy + Proceed/Review buttons |
| **Clarify-first** | `/grill-me` |
| **Run-to-completion loop** | `/goal` (no intermediate input) + `Stop` hook `decision:"continue"` |
| **Per-step verifier / guard** | `PreToolUse` decisions (`deny`, `force_ask`, `overwrite`) and `PostToolUse` logging |
| **Critic / falsifier** | Teamwork patterns: Iterative coding, Distributed coding with critic review, Long Proof with paired **falsifiers**, Self-Verification, Document review |
| **Orchestrator–worker graph** | Dynamic subagents in git worktrees. Teamwork Long Proof runs subproblems in **topological order** and independent nodes in parallel |
| **Context engineering** | Progressive-disclosure skills, `model_decision` rules, 20k rule budget, `/compact` |
| **Evidence over logs** | Artifacts: screenshots, recordings, walkthroughs, diffs |
| **Scheduled agents** | Sidecars/Automations (cron) |
| **Least privilege** | Sandbox presets, scoped `tools`, `permissionMode: plan` read-only auditors |

Teamwork numbers: 7 open math/TCS problems solved (6 confirmed by experts; a 40-page proof verified in Lean); TCSBench **71%**; a RISC-V OoO simulator at **0.71%** average cycle error vs BOOM; Eigen and ParlayHash patches merged upstream.

---

## 12. Codelabs and tutorials (exact titles)

- **Getting Started with Google Antigravity**: https://codelabs.developers.google.com/getting-started-google-antigravity (now covers 2.0: Projects, Slash Commands, Scheduling, MCP, Artifacts, IDE, Skills)
- **Hands-on with Antigravity CLI**: https://codelabs.developers.google.com/antigravity-cli-hands-on
- **Build and Deploy to Google Cloud with Antigravity**: https://codelabs.developers.google.com/build-and-deploy-gcp-with-antigravity (GCS → Pub/Sub → Cloud Run (Python) → BigQuery pipeline. Uses `/grill-me` and `./scripts/deploy.sh`)
- ADK "Code with AI" guide: https://adk.dev/tutorials/coding-with-ai/
- Agents CLI docs: https://google.github.io/agents-cli/
- YouTube channel: https://www.youtube.com/@googleantigravity
- Docs: https://antigravity.google/docs/overview and changelog https://antigravity.google/docs/changelog

---

## 13. Failure modes and gotchas

1. **Silent config drops.** A rule with an invalid `trigger` (e.g. `alwaysOn`) or missing frontmatter is discarded without any error.
2. **Hung subagent** from a misspelled tool name in `tools`.
3. **Rule budget overflow.** Past 20k tokens, the largest always-on rules become pointers, so the agent "forgets" conventions.
4. **Legacy paths.** `.agent/` vs `.agents/`, and `~/.gemini/antigravity/skills` (legacy). CLI global skills live in a *different* dir (`~/.gemini/antigravity-cli/skills/`) from the App's.
5. **Workflows dead since 2026-10-19.** Old tutorials using `.agents/workflows` no longer work.
6. **Sandbox has no network** under Default, so `pip install` or deploy commands prompt or fail.
7. **`--dangerously-skip-permissions` / Turbo** can run destructive commands. Prefer `proceed-in-sandbox`.
8. **Model availability churn.** Argon is not in the IDE. 4.6-generation Claude and GPT-OSS are removed 2026-11-02. Gemini CLI is cut off for consumers.
9. **Browser subagent** needs Chrome as the default browser, and allowlist misconfiguration blocks testing.
10. **Prompt injection via browsed pages or MCP.** The mitigations are the URL denylist, the isolated profile, and admin MCP restrictions (enterprise).

---

## 14. Interview questions (crisp answers)

1. **What is Antigravity in one line?** Google's agent-first development platform: an App, CLI, IDE, extensions and SDK on one Gemini-co-trained harness, where you manage agents and review *artifacts* rather than babysitting a chat.
2. **Agent Manager vs Antigravity 2.0?** The Agent Manager was the IDE's mission-control surface (Nov 2025). 2.0 (May 19, 2026) spun it out into a standalone app without an IDE, organized by multi-folder *Projects*.
3. **Why artifacts?** Trust at scale. Reviewing a plan, diff, screenshot or recording is cheaper than reading tool logs, and comments feed back asynchronously.
4. **How do you force an agent not to stop until tests pass?** A `Stop` hook that runs the tests and returns `{"decision":"continue","reason":...}` (or use `/goal`).
5. **Skill vs rule vs custom agent?** A rule is always-on or conditional guidance. A skill is an on-demand capability folder (progressive disclosure). A custom agent is a scoped persona with its own system prompt, tools, model and permissions, usable as a main agent or a subagent.
6. **How do parallel subagents avoid clobbering each other?** The `branch` workspace mode gives each one an isolated git worktree that is created and cleaned up automatically.
7. **What happened to Gemini CLI?** It was replaced by Antigravity CLI (`agy`, Go) for consumer tiers on 2026-06-18. Enterprise use continues. Migrate with `agy plugin import gemini`.
8. **Antigravity vs Jules?** Antigravity is local-first, interactive or async, multi-surface. Jules is cloud-VM, GitHub-PR-centric, and async.
9. **Antigravity SDK vs ADK?** The SDK scripts Google's coding-agent harness. ADK builds and deploys your own agents (graph workflows, evals, Agent Runtime). Use Antigravity plus Agents CLI skills to *write* ADK agents.
10. **Enterprise controls?** WIF/ADC sign-in, regional inference, sandbox and MCP/browser restrictions, Cloud Billing budgets, audit logs of prompts, tools and artifacts, and no training on customer code.

---

## 15. Slide ideas (with the animation that explains each)

1. **"From autocomplete to mission control."** A timeline (Tab completion → chat sidebar → Agent Manager Nov 2025 → Antigravity 2.0 May 2026 → Argon Oct 2026). *Animation:* the IDE window shrinks into a tile while a grid of agent cards expands around it.
2. **The four tenets.** Trust / Autonomy / Feedback / Self-improvement as four pillars. *Animation:* each pillar lights up as an example appears (artifact, parallel agents, comment bubble, knowledge item).
3. **One harness, five surfaces.** A hub (agent harness + Gemini) with spokes to App, CLI, IDE, extensions and SDK. *Animation:* a settings change on one spoke pulses to all the others (shared permissions).
4. **The artifact review loop.** Plan → comment → revise → proceed → walkthrough. *Animation:* a comment bubble drops onto the plan, the plan redraws, and a "Proceed" stamp appears, without the agent's progress bar ever pausing.
5. **Browser-in-the-loop verification.** Code edit → `npm run dev` → browser subagent clicks → screenshot and recording artifact. *Animation:* a cursor ghost-clicks the UI and a film strip slides into the artifact pane.
6. **Hooks as per-step verifiers.** The agent loop as a circle with six hook points. *Animation:* a `PreToolUse` gate turns red on `rm -rf` (deny); at `Stop`, a failing test bounces the token back into the loop ("continue").
7. **Subagents and worktrees as a graph.** A main agent fans out to 3 subagents, each on its own git branch, which merge back. *Animation:* the branches sprout, run in parallel, and fold into a single diff.
8. **Teamwork: propose / falsify / synthesize.** Candidate strategies each paired with a falsifier, feeding into a synthesis tree. *Animation:* refuted routes fade but keep their objection tags, which flow into the final node.
9. **Building an ADK 2.0 agent with Antigravity.** `uvx google-agents-cli setup` → `/plan` → code → `agents-cli eval run` → Stop-hook gate → `agents-cli deploy -d agent_runtime` → `publish gemini`. *Animation:* a conveyor belt where a red eval light holds the package until it turns green.
10. **Google dev-tool map 2026.** A 2×2 with Local↔Cloud on one axis and Interactive↔Async on the other: Antigravity App/IDE (local, interactive), Antigravity CLI/Automations (local, async), Jules (cloud, async), AI Studio (cloud, interactive). Gemini CLI and Firebase Studio are shown greyed out with sunset dates. *Animation:* the sunset products slide off the map into the Antigravity quadrant.
