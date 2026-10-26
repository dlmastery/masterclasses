# Customizing modern AI: SFT, RL, RAG and data-centric AI (v2, hands-on)

Deck key: `custom`. 100 slides in 12 chapters (00 opening + 11 content chapters). Rewrite after the v1 verdict: "too much theory, no actual examples". Every content chapter is built around one runnable lab on one named Acme business scenario, followed by gotchas, an arXiv card from 2026-07-23..2026-10-23 (verified list in `research-v2/custom/00-VERIFIED.md`) and a production case. Code comes only from the VERIFIED labs in `research-v2/custom/` (trl 1.16.0, peft 0.21.2, transformers 5.20.2, google-genai 2.33.0, openai 3.37.0, pandera 0.34.1, evidently 0.7.23, cleanlab 2.9.0, scikit-learn 1.9.1, datasketch 2.0.0, krippendorff 0.9.0, statsmodels 0.15.0, ragas 0.4.3, distilabel 1.5.3). Outputs marked RAN/REAL/captured are real; others are labelled `output · illustrative` on the slide.

## Mix (section 9.2 targets)

| Type | Count | Target |
|---|---|---|
| lab | 42 | >= 30 (6-10 labs) |
| buildup | 4 | - |
| gotcha | 12 | >= 12 |
| paper | 12 | >= 10 |
| industry | 8 | >= 8 |
| practices | 6 | >= 6 |
| concept | 3 | <= 12 |
| chapter | 11 | <= 11 |
| opening | 2 | 2 |
| **code slides** (lab + buildup + gotcha + practices with config) | 63 | >= 60 |
| qa | 0 | 0 |
| **total** | 100 | 100 |

Labs: 10 labs, one per content chapter C02-C11, 3-5 slides each.

## Chapters and running scenarios

| Ch | Chapter | Tone | Slides | Scenario |
|---|---|---|---|---|
| 00 | Opening | `model` | 2 | Acme Commerce & Insurance: one company, ten production problems (refunds desk, claims desk, support tickets, HR policy assistant). Every lab in the deck solves one of them. |
| 01 | Choose the lever: context, RAG, SFT or RL | `agent` | 7 | Acme support desk: refund answers are wrong in two ways (missing policy facts, and an off-brand, unstructured format). Decide which lever fixes which failure before anyone trains. |
| 02 | SFT with TRL and LoRA | `model` | 10 | Acme refunds assistant: Qwen3-0.6B + LoRA on the 2,992 REFUND rows of the Bitext customer-support dataset (26,872 rows, CDLA-Sharing-1.0), masked correctly, merged, verified and served; then the same data on Vertex Gemini and the Gemma 4 path with Unsloth. |
| 03 | QLoRA and honest before/after evaluation | `model` | 9 | Acme claims desk: turn free-text adjuster notes into strict JSON {loss_type, severity, needs_adjuster, policy_section} with Qwen3-4B-Instruct-2507 in 4-bit NF4, then measure base vs tuned on the same quantized weights. |
| 04 | Rewards you can unit-test | `tool` | 9 | Acme refunds desk: a refund-decision agent answers <answer>{decision, refund_amount, reason}</answer>; gold labels come from the policy engine. Write the reward once, unit-test it on CPU, and run it unchanged on TRL, OpenAI graders and Vertex Gemini RFT. |
| 05 | GRPO with a verifier | `model` | 11 | Acme claims back-office: RL-train Qwen2.5-0.5B-Instruct + LoRA to compute claim payouts (deductible -> coinsurance share -> policy limit) with a procedural generator that gives exact gold answers; then add a gated brevity reward, KL on/off and a reward-hacking tripwire. |
| 06 | Preference tuning with DPO and reward models | `human` | 8 | Acme support QA team marks replies as on-brand (empathetic, specific, takes action) or off-brand (dismissive, blames the customer). Align the support assistant with DPO + LoRA, read the DPO logs correctly, and train a reward model when you need a learned reward. |
| 07 | Dataset contracts, coverage and active learning | `state` | 7 | Acme claims intake: reject or quarantine a bad nightly batch before it reaches the fraud-model training table, then decide which claims senior adjusters (100 labels/day) should label next. |
| 08 | Drift, leakage, calibration and cost | `risk` | 8 | Acme refund-fraud model: watch refund-request drift (September vs October holiday promo), prove the validation does not leak customers or the future, calibrate the scores, and set the hold threshold from a $15 / $120 cost matrix at 2% production prevalence. |
| 09 | Ticket triage: drift gate, label noise, route or defer | `human` | 8 | Acme support-ticket triage (billing / login / outage / shipping): a weekly Evidently gate holds retraining when the ticket mix shifts, cleanlab ranks the vendor's ~8% wrong labels for a 200-ticket review, and an 8-class router auto-routes only when that is cheaper than human triage. |
| 10 | Synthetic data and RAG eval sets with verification | `state` | 10 | Acme HR policy assistant (RAG over PTO, parental-leave and expense policies): synthesize a RAG eval set with ragas, reject ungrounded, closed-book and duplicate items, decontaminate train vs test with MinHash, and correct the LLM judge's biased pass rate with human labels. |
| 11 | Eval design, the quality card and open challenges | `tool` | 11 | Acme claims-extraction agent release: report the pass rate per line of business x language with honest CIs, compare v1 vs v2 on the same 400 golden cases, and ship only when a versioned quality card passes its release gate in CI. |

## Chapter 00: Opening

Tone: `model`

**Scenario.** Acme Commerce & Insurance: one company, ten production problems (refunds desk, claims desk, support tickets, HR policy assistant). Every lab in the deck solves one of them.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/custom/industry.md
- C:/Users/evija/googleadk2.0/research-custom/01-customization-map.md

### 00.01 [opening] Same base models for everyone: your data, rewards and evals make yours

- File: `c00-01-hero.html`
- Id: `custom-c00-hero`

**Content.** .display deck title 'Customizing modern AI: SFT, RL, RAG and data-centric AI'. One .lede (<= 25 words): 'Everyone rents the same base models. This course shows, in code, how to change what they know, how they behave, and how you prove it.' Three tags: Weights (SFT, DPO, GRPO: t-model), Context (RAG, retrieval subagents: t-agent), Data (contract, label, dedup, synthesize, evaluate: t-state). Three proof stats (.stat count-up, from industry.md): Cursor real-time RL: a new Composer checkpoint every ~5 h from user traffic (A2); Databricks KARL: Opus-level score at under $0.10 per query (A6); Shopify Sidekick: judge kappa 0.02 -> 0.61 before any GRPO run (A8). Small line: 'Tested on trl 1.16.0, peft 0.21.2, transformers 5.20.2 (Oct 2026)'. Notes: the course is code-first; every lab is runnable; numbers come from 00-VERIFIED.md and industry.md; no hype words.

**Visual and animation.** Self-animating hero (Deck.register, gsap timeline, loop killed in leave). Centre coral node 'Base model'. Left: a green ring of 7 dots labelled contract, label, dedup, synthesize, verify, eval, card; a highlight travels round the ring (index-based). Right: three arms out of the base model to 'SFT / LoRA' (coral), 'GRPO / DPO' (coral), 'RAG' (blue), each ending in a violet pill 'Acme product'. :flow pulses travel ring -> base -> arms. At 2.4 s the three .stat counters count up under the diagram (5 h, $0.10, 0.61). Steps: 0 = auto build; 1 = stats emphasised.

### 00.02 [opening] Ten labs, four Acme teams, one pipeline from decision to release gate

- File: `c00-02-lab-map.html`
- Id: `custom-c00-lab-map`

**Content.** Course map as a grid of 10 lab cards, grouped by Acme team. Refunds desk: Lab 1 LoRA SFT refunds assistant (C02), Lab 3 unit-tested refund rewards on TRL / OpenAI / Vertex (C04). Claims desk: Lab 2 QLoRA claims JSON extractor (C03), Lab 4 GRPO claims payout calculator (C05), Lab 6 claims intake contract + active learning (C07), Lab 10 claims-agent slices + quality card (C11). Support: Lab 5 DPO on-brand replies (C06), Lab 8 ticket triage drift gate + cleanlab + route-or-defer (C09). Risk: Lab 7 refund-fraud drift, leakage, calibration, cost threshold (C08). HR: Lab 9 HR policy RAG eval set, dedup, judge correction (C10). Under the grid: one pinned install line per stack (HF: trl==1.16.0 peft==0.21.2 transformers==5.20.2; data: pandera[pandas]==0.34.1 evidently==0.7.23 cleanlab==2.9.0 scikit-learn==1.9.1; Python 3.12). Each chapter ends with gotchas, a recent arXiv card (Jul-Oct 2026) and a production case.

**Visual and animation.** Bespoke build (Deck.register): an Acme org chart with 4 team nodes (refunds amber, claims green, support blue, HR violet). Step 1: team nodes pop. Step 2: the 10 lab cards fly out from their team node into a 5x2 grid, each with its chapter number. Step 3: a coral line runs left to right under the grid labelled 'decide -> train -> reward -> data -> eval -> release gate' and lights each card in chapter order. Step 4: the pin line types in (data-fx=type).

## Chapter 01: Choose the lever: context, RAG, SFT or RL

Tone: `agent`

**Scenario.** Acme support desk: refund answers are wrong in two ways (missing policy facts, and an off-brand, unstructured format). Decide which lever fixes which failure before anyone trains.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/industry.md
- C:/Users/evija/googleadk2.0/research-v2/custom/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-sft.md
- C:/Users/evija/googleadk2.0/research-v2/custom/gotchas.md
- C:/Users/evija/googleadk2.0/research-custom/01-customization-map.md

### 01.01 [chapter] Choose the lever before you train

- File: `c01-01-chapter.html`
- Id: `custom-c01-chapter`

**Content.** Chapter 01. .display 'Choose the lever'. Lede: 'Knowledge failures go to context and retrieval. Behaviour failures go to weights. Measure first.' Scenario line: Acme support desk, refund answers fail in two different ways.

**Visual and animation.** Self-animating mini-diagram: a red 'failure' card splits into two cards, 'missing fact' (blue, flows to RAG node) and 'wrong format / tone' (coral, flows to SFT/RL node). Loop pulses along both wires.

### 01.02 [concept] Climb the ladder one rung at a time; the eval decides each step

- File: `c01-02-ladder.html`
- Id: `custom-c01-ladder`

**Content.** Concept slide, <= 3 short lines. Ladder (research-custom/01 §1.2): prompt/context -> long context -> RAG -> SFT (LoRA) -> DPO -> RL/RFT. Each rung shows data needed and upfront cost: context = 20+ eval cases (OpenAI guidance); SFT = 50-500 examples to start; DPO = chosen/rejected pairs; RL = prompts + a reward function, no gold outputs. Line 1: 'Knowledge goes to RAG, behaviour goes to tuning.' Line 2: 'If every rollout fails, do SFT first; above 95% reward, RFT is not needed' (AWS Bedrock RFT pre-check, gotchas.md H3). Line 3: 'Icelandic grammar task: fine-tuned GPT-4 87 BLEU, adding RAG dropped it to 83' (OpenAI accuracy guide, research-custom/01 §1.1).

**Visual and animation.** Large bespoke animation (Deck.register, >= 60% canvas). A ladder of 6 rungs drawn bottom-up (data-fx draw). A red failure token for the Acme refund bot enters at the bottom. Step 1: the eval gauge (0-100) beside the ladder reads 41% at 'prompt'. Step 2: token climbs to RAG; the token's 'missing fact' half turns green, gauge 63%. Step 3: token climbs to SFT; 'format' half turns green, gauge 85%. Step 4: a coral bracket marks DPO/RL as 'only with a reward you trust'. Numbers on the gauge are illustrative and labelled so. Each rung shows a small cost bar (hours / days / GPU-days).

### 01.03 [industry] Databricks Genie Code beat general agents with context, not training

- File: `c01-03-context-first.html`
- Id: `custom-c01-context-first`

**Content.** Kicker: In production · Databricks (Jul 2026, vendor-reported; industry.md A7). Eval: 401 internal data tasks, 20-minute budget, independent judge. Genie Code 76.6% at $0.55 mean cost per task vs best general coding agent 72.1% at $1.09; 8.3 tool calls per task (fewest). Gain came from semantic search over the catalog + persistent memory of tables, not fine-tuning; 'Accuracy and cost did not trade off'. Second card: Google Cloud NextNet (Feb 2025, A19) tuned Gemini Flash: accuracy +80%, cost -90%, latency -60%, partly by shrinking the prompt template from 2,000 to 200 tokens. Lesson line: fix context first; tune when the failure is behaviour, cost or latency. .cite links: databricks.com/blog/why-frontier-data-agent-outperforms-general-coding-agents-quality-and-cost ; cloud.google.com/transform/top-five-gen-ai-tuning-use-cases-gemini-hundreds-of-orgs.

**Visual and animation.** Animated architecture diagram (>= 45% width): user -> Genie agent -> two tool nodes 'catalog semantic search' and 'table memory' (green state) -> answer; :flow pulses step 1. Step 2: two horizontal bar pairs grow (accuracy 76.6 vs 72.1; cost $0.55 vs $1.09) with .stat count-up. Step 3: NextNet card slides in with a prompt bar shrinking from 2,000 to 200 tokens (gsap width tween) and three deltas (+80%, -90%, -60%).

### 01.04 [paper] Teaching new facts through SFT raises hallucination: retrieve them

- File: `c01-04-facts-not-weights.html`
- Id: `custom-c01-facts-not-weights`

**Content.** Kicker: arXiv Aug-Oct 2026. Three .paper cards. (1) 2608.30987 'Stick to What You Know: Knowledge-Aligned SFT' (31 Aug 2026): SFT targets that need knowledge the base model lacks drive hallucination; 'Recall Rewrite' keeps only claims the base can consistently recall and reduced factual hallucination on WildHalu/Biography (Qwen3 4B, OLMo 3 7B). Monday: put refund-policy numbers in RAG, use SFT for format and tone. (2) 2607.21861 'Data Quality over Capacity' (23 Jul 2026): curating documents into canonical short answers moved closed-book LoRA QA from 57.7% to 85.7%. Monday: if you must internalize documents, curate the targets first. (3) 2610.11132 'SFT-as-Context' (8 Oct 2026): the parent model reads the SFT model's answer as context; within 2.2 pp of SFT on AIME24/LiveCodeBench and within 2.2 pp of the parent on general capability, 19 pairs, 11 benchmarks. Monday: route domain + general questions through base(prompt + adapter draft).

**Visual and animation.** Animated method diagram for card 1: a bar of 10 SFT target claims; step 1 each claim is probed against the base model (8 small dots per claim, green = recalled, red = not); step 2 claims with mostly-red dots fade out ('Recall Rewrite' filter); step 3 a hallucination meter drops. Card 2 animates a bar 57.7 -> 85.7 (count-up). Card 3 shows two nodes 'SFT model draft' -> 'parent model' with a :flow wire. Cards appear one per step (3 steps).

### 01.05 [industry] In 2026 teams train small specialists around a frontier base

- File: `c01-05-who-trains.html`
- Id: `custom-c01-who-trains`

**Content.** Kicker: In production · 2025-2026 roll-up (industry.md summary table). Five rows, each lever + number + date: Cursor real-time RL from user traffic, ~5 h cycle, edit persists +2.28%, dissatisfied follow-ups -3.13%, latency -10.3% (Mar 2026); Vercel v0 AutoFix (Fireworks RFT): 86.14% error-free at 8,130 chars/s vs gemini-2.5-flash 559 chars/s (Jun 2025); Chroma Context-1: 20B retrieval subagent (gpt-oss-20b + LoRA, SFT then CISPO RL), BrowseComp-Plus 0.96, up to 10x faster (Mar 2026); Ramp Fast Ask: 35B RL subagent 'beat Opus at spreadsheet search', 27% faster than Haiku (Jul 2026, primary facts only); Intercom Fin Apex 1.0: 73.1% resolution vs 71.1% GPT-5.4 (vendor-reported, Mar 2026). Lesson: keep a swappable frontier model; train a small, fast specialist for one workflow. .cite each source URL from industry.md.

**Visual and animation.** Bespoke animation: a central blue node 'frontier model (swappable)'. Five specialist satellite nodes (coral) dock around it one per step (Cursor, Vercel, Chroma, Ramp, Intercom), each with its number counting up on a tag. Final step: a dashed ring 'your harness' draws around the whole system. <= 7 wires, labels <= 16 chars.

### 01.06 [gotcha] Managed tuning can vanish: keep data, graders and evals portable

- File: `c01-06-vendor-exit.html`
- Id: `custom-c01-vendor-exit`

**Content.** Kicker: Gotcha · managed services (Oct 2026). Three .gotcha cards from gotchas.md H4/H2 and lab-rl Lab 7 status. (1) Symptom: RFT job on o4-mini rejected. Cause: OpenAI 'is winding down the fine-tuning platform'; o4-mini-2025-04-16 and its fine-tunes shut down 2026-10-23 (today); last new jobs 2027-01-06; graders deprecated. Fix: keep the grader as plain Python. (2) Symptom: Vertex Gemini RFT result cannot go to production. Cause: Pre-GA, 'may not be used for commercial or production purposes', 'do not use proprietary, sensitive, or other confidential data'; v1beta1 only. Fix: prototype only, plan the GA migration. (3) Symptom: Fireworks managed RFT 'no longer accepts new RFT jobs'. Fix: portable assets = dataset JSONL + reward code + eval set. Show the fix code: the same refund grader as a vendor-neutral function that runs in TRL, OpenAI python graders and Vertex code-execution rewards.

**Visual and animation.** Bespoke animation: three vendor tiles (OpenAI, Vertex RFT, Fireworks). Step 1: OpenAI tile gets a red 'shut down 2026-10-23' stamp; step 2 Vertex tile shows an amber 'Pre-GA' band; step 3 Fireworks tile greys out. Step 4: a green folder 'refunds/' slides in with three files (train.jsonl, grade.py, eval.jsonl) and arrows fan out from grade.py to three backends (TRL, OpenAI, Vertex) to show portability.

**Code.**

```text
From lab-rl.md Lab 7 GRADE_SRC (verified, openai 3.37.0 python grader contract). Show 14 lines:
import json, re
def grade(sample, item) -> float:
    m = re.search(r'\{.*\}', sample['output_text'], re.DOTALL)
    if not m:
        return 0.0
    try:
        out = json.loads(m.group(0))
    except Exception:
        return 0.0
    if out.get('decision') != item['gold_decision']:
        return 0.0
    try:
        ok = abs(float(out.get('refund_amount', -1)) - float(item['gold_amount'])) <= 0.01
    except (TypeError, ValueError):
        ok = False
    return 1.0 if ok else 0.5
Plus folder tree: refunds/{train.jsonl, val.jsonl, grade.py, eval_set_<sha>.jsonl}.
```

### 01.07 [practices] Eight checks that pick the lever before any GPU hour

- File: `c01-07-lever-checks.html`
- Id: `custom-c01-lever-checks`

**Content.** Best practices, ul.checks with reasons (industry.md Part D items 1-6, gotchas H3, research-custom/01 §1.2). Do: (1) Build 20-50 eval tasks from real failures first (Anthropic 'Demystifying evals', Jan 2026). (2) Label each failure 'knowledge' or 'behaviour'; knowledge -> context/RAG. (3) Try context engineering first (Genie Code: +4.5 pts at half the cost). (4) Check pass@k > 0 on your prompts before RL: 'RFT requires that the model can produce at least one correct solution among several attempts' (AWS Nova). (5) Start RFT with 100-200 examples (AWS). (6) Screen candidate base models before paying for RL (arXiv 2610.10478: base-model screens rank 10 pairs in close agreement with post-trained SWE-bench pass@1). (7) Prefer on-policy distillation when a strong teacher exists (Thinking Machines: 1,800 vs 17,920 GPU-h). Don't: (8) Do not SFT new facts (2608.30987). (9) Do not RFT when reward is already > 95% (Bedrock). (10) Do not lock data into one vendor format.

**Visual and animation.** ul.checks with data-fx stagger, 3 build steps (do items, then don't items, then a small decision tree that draws itself on the right: 'reward always 0?' -> SFT first; 'reward > 95%?' -> stop; else -> RFT). The tree uses 4 nodes and 3 labelled wires.

## Chapter 02: SFT with TRL and LoRA

Tone: `model`

**Scenario.** Acme refunds assistant: Qwen3-0.6B + LoRA on the 2,992 REFUND rows of the Bitext customer-support dataset (26,872 rows, CDLA-Sharing-1.0), masked correctly, merged, verified and served; then the same data on Vertex Gemini and the Gemma 4 path with Unsloth.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-sft.md
- C:/Users/evija/googleadk2.0/research-v2/custom/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/custom/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/custom/arxiv-sft-rl.md
- C:/Users/evija/googleadk2.0/research-custom/02-sft.md

### 02.01 [chapter] SFT with TRL and LoRA

- File: `c02-01-chapter.html`
- Id: `custom-c02-chapter`

**Content.** Chapter 02. .display 'SFT with TRL and LoRA'. Lede: 'Train only on assistant tokens, train all linear layers, and prove the merge did not change behaviour.' Scenario: Acme refunds assistant on 2,992 Bitext REFUND rows.

**Visual and animation.** Self-animating mini-diagram: a token stream where user tokens are grey and assistant tokens glow coral; the coral tokens flow into a thin 'LoRA A x B' pair beside a frozen base block; loop.

### 02.02 [lab] Look before you train: print exactly which tokens SFT learns from

- File: `c02-02-lab1-mask.html`
- Id: `custom-c02-lab1-mask`

**Content.** Kicker: Lab 1 Acme refunds assistant · step 1 of 5. 'Run it Monday' block: pip install "trl==1.16.0" "peft==0.21.2" "transformers==5.20.2" "datasets==5.1.0" "accelerate==1.15.0" "bitsandbytes==0.50.2" "torch==2.14.1"; Python >= 3.11; env: HF_TOKEN optional; folder tree refunds_sft/{lab1_inspect_mask.py, lab2_sft_lora_refund.py, lab5_merge_and_verify.py}. Code = lab-sft Lab 1 (VERIFIED trl 1.16.0) with the messages swapped to a refund exchange (system = the refund SYSTEM string from Lab 2; user 'I returned order {{Order Number}} two weeks ago, where is my money?'; assistant reply made up for the lab). Focus 1: get_training_chat_template(tok) returns TRL's patched qwen3_training.jinja (None means already training-ready). Focus 2: apply_chat_template(..., return_dict=True, return_assistant_tokens_mask=True). Focus 3: the span printer. Output pane (illustrative): 'TRL patched the template: True', 'Original == patched rendering: False', 'tokens=118 trained=46 (39%)', then mask .. / TRAIN >> spans; TRAIN spans include '<think>\n\n</think>\n\n' and '<|im_end|>'. Steps-rail: why orig != patched (stock Qwen3 template drops earlier <think> blocks); why <|im_end|> must be inside the TRAIN span (or the model never learns to stop); enable_thinking=False makes inference prefill the empty think block. Pitfall callout: Gemma 4 is NOT in TRL's patch list -> ValueError 'The chat template is not training-compatible...'; fix in C02 slide 09 (Unsloth) or C03 (prompt-completion). Best practice: run this as CI; fail if any row has sum(mask)==0. Cite: TRL docs 'SFT Trainer' https://huggingface.co/docs/trl/sft_trainer.

**Visual and animation.** Right column: bespoke token-strip animation (Deck.register). The rendered chat is drawn as ~60 small token boxes in rows. Step 1 (focus 1): all boxes grey. Step 2 (focus 2): assistant boxes flip to coral one by one (stagger) while a counter counts 0 -> 46 of 118. Step 3 (focus 3): the two '<|im_end|>' boxes pulse to show the stop token is trained. Step 4: output pane appears with ok/dim spans.

**Code.**

```text
lab-sft.md Lab 1 lab1_inspect_mask.py (full 35 lines; messages list replaced by 3 refund turns). data-focus="1:7-8, 2:13-16, 3:18-25".
```

### 02.03 [lab] One SFTConfig: assistant-only loss, BFD packing, bf16, all-linear LoRA

- File: `c02-03-lab1-config.html`
- Id: `custom-c02-lab1-config`

**Content.** Kicker: Lab 1 Acme refunds assistant · step 2 of 5. .lab-head run: python lab2_sft_lora_refund.py (multi-GPU: accelerate launch --num_processes 2 ...). Code = lab-sft Lab 2 lab2_sft_lora_refund.py (VERIFIED trl 1.16.0, peft 0.21.2, transformers 5.20.2): load Bitext, filter category == 'REFUND' (2,992 rows, 3 intents), to_messages, train_test_split(0.05, seed 42), SFTConfig(model_init_kwargs={'dtype': torch.bfloat16}, assistant_only_loss=True, max_length=1024, packing=True, packing_strategy='bfd', learning_rate=2e-4, num_train_epochs=2, per_device_train_batch_size=8, gradient_accumulation_steps=2, lr_scheduler_type='cosine', warmup_steps=0.03, eval_steps=50, save_steps=50, load_best_model_at_end=True), LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules='all-linear', task_type='CAUSAL_LM'), SFTTrainer(model='Qwen/Qwen3-0.6B', ..., peft_config=...). Focus walk-through: (1) dtype: string ids load in float32 unless set (sft_trainer.py:544-546); (2) assistant_only_loss + bfd packing switches on padding-free mode; packing wants FlashAttention ('kernels-community/flash-attn2' on Ampere+); (3) lr 2e-4 = ~10x the SFTConfig default 2e-5 (LoRA Without Regret); warmup_steps float in [0,1) = ratio in transformers v5; (4) target_modules='all-linear' (default for qwen3 is only q_proj, v_proj). Output pane (illustrative): 'trainable params: 10,092,544 || all params: 606,142,464 || trainable%: 1.6650'. Best practice: hold out by intent, not only at random.

**Visual and animation.** Code left (.code.xs, 26 lines) with 4 data-focus bands; steps-rail right with 4 items revealed in sync. Under the rail a bespoke mini-diagram: Qwen3 block with 28 layers; on focus 4 seven small LoRA badges (q,k,v,o,gate,up,down) light up on every layer and a counter rolls to 10,092,544 (vs a greyed 2,293,760 for q/v only).

**Code.**

```text
lab-sft.md Lab 2 lab2_sft_lora_refund.py lines 1-40 (show SYSTEM, load/filter, to_messages, SFTConfig, LoraConfig, SFTTrainer, train, save_model). data-focus="1:21, 2:22-25, 3:26-31, 4:36-37".
```

### 02.04 [lab] Read the run: loss, token accuracy and the 40 MB adapter

- File: `c02-04-lab1-run.html`
- Id: `custom-c02-lab1-run`

**Content.** Kicker: Lab 1 Acme refunds assistant · step 3 of 5. .lab-head: python lab2_sft_lora_refund.py | tee train.log. Show the last 8 lines of the script (trainer.train(), trainer.save_model('qwen3-0.6b-refund-lora/final'), print(trainer.evaluate())) and a terminal output pane labelled 'output · illustrative' (lab-sft Lab 2): {'loss': 1.912, 'grad_norm': 1.21, 'entropy': 1.64, 'num_tokens': 81920.0, 'mean_token_accuracy': 0.611, 'epoch': 0.09} ... {'eval_loss': 0.583, 'eval_mean_token_accuracy': 0.842, 'epoch': 1.0} ... {'train_runtime': 610.2, 'train_loss': 0.71} {'eval_loss': 0.561, 'eval_mean_token_accuracy': 0.848}. Steps-rail: entropy / mean_token_accuracy / num_tokens are TRL's extra metrics; save_model writes adapter_model.safetensors + adapter_config.json (~40 MB, not the base); eval_packing defaults to packing so eval loss uses the same token layout. Errors panel (exact strings): 'ValueError: --load_best_model_at_end requires the saving steps to be a multiple of the evaluation steps' -> make save_steps a multiple of eval_steps. Pitfall: lower eval_loss is not the selection metric (link to C02 slide 10 paper).

**Visual and animation.** Bespoke loss-curve animation (Deck.register, SVG ~55% width): train loss path draws from 1.91 down to ~0.7 over 2 epochs; eval_loss dots appear at 0.583 and 0.561; mean_token_accuracy line rises 0.61 -> 0.85 on a second axis. Step 1 draw train loss; step 2 eval dots + count-up labels; step 3 an adapter file icon '40 MB' drops beside a greyed '1.2 GB base' icon.

**Code.**

```text
lab-sft.md Lab 2 lines 38-41 plus the Expected output block.
```

### 02.05 [lab] Merge the adapter, then assert the greedy tokens did not change

- File: `c02-05-lab1-merge.html`
- Id: `custom-c02-lab1-merge`

**Content.** Kicker: Lab 1 Acme refunds assistant · step 4 of 5. .lab-head: python lab5_merge_and_verify.py. Code = lab-sft Lab 5 lab5_merge_and_verify.py (VERIFIED peft 0.21.2): load base in bf16 (never 4-bit), PeftModel.from_pretrained(base, ADAPTER).eval(), ref_logits, merged = peft_model.merge_and_unload(safe_merge=True, progressbar=True) (not in-place: use the return value), new_logits, diff = max |ref - new|, same_argmax = torch.equal(argmax), assert same_argmax, save_pretrained, generate. Output (illustrative): 'Unloading and merging model: 100% 198/198', 'max |logit diff| = 0.0625  same greedy tokens: True', then the refund reply keeping {{Order Number}}. Steps-rail: (1) safe_merge=True checks NaNs -> 'NaNs detected in the merged weights. The adapter default seems to be broken'; (2) merging into bnb 4-bit layers warns 'Merge lora module to 4-bit linear may get different generations due to rounding errors.'; (3) gate on the decision (greedy token), not bit equality, because bf16 re-rounds W + BA*alpha/r. Error: AttributeError: 'Qwen3ForCausalLM' object has no attribute 'merge_and_unload' -> call it on the PeftModel.

**Visual and animation.** Bespoke animation: two logit bar charts (before merge / after merge) for the first 5 output positions; step 1 bars draw; step 2 a diff strip appears showing tiny deltas (max 0.0625); step 3 the argmax bar in each position glows green and a green check 'same greedy tokens' stamps; step 4 the merged model file icon drops into a 'ship' box.

**Code.**

```text
lab-sft.md Lab 5 lab5_merge_and_verify.py (full 30 lines). data-focus="1:8-9, 2:17, 3:21-24".
```

### 02.06 [lab] Serve one base with many adapters on vLLM, merge only for the edge

- File: `c02-06-lab1-serve.html`
- Id: `custom-c02-lab1-serve`

**Content.** Kicker: Lab 1 Acme refunds assistant · step 5 of 5. .code-wrap.term with the verified commands (lab-sft Lab 5 Run): '$ vllm serve ./qwen3-0.6b-refund-merged --served-model-name refund-agent' (option A merged), '$ vllm serve Qwen/Qwen3-0.6B --enable-lora --lora-modules refund=./qwen3-0.6b-refund-lora/final --max-lora-rank 16' (option B multi-LoRA), and the curl to /v1/chat/completions with model 'refund'. Pinned: vllm==0.32.0 in a separate serving env (training env note: trl[vllm] pins vllm<=0.31.0). Steps-rail: LoRAConfig.max_lora_rank defaults to 16 and max_loras to 1 -> raise both for more/larger adapters; one base + N adapters costs about one base model of VRAM; ship adapters for many tenants, merge only for GGUF/edge. Output pane (illustrative): JSON chat completion with the refund reply. Pitfalls: garbage '<think>' text at inference -> build prompts with enable_thinking=False (matches Lab 1 mask); transformers v5 module renames can break adapters in vLLM (PEFT #3896) -> serve with --model-impl transformers or add a CI step that compares logprobs in the serving engine (gotchas A6).

**Visual and animation.** Large diagram (>= 50% canvas, data-wires): client pills 'refunds UI' and 'shipping UI' -> vLLM node (tool) -> base Qwen3-0.6B (model) with two adapter nodes 'refund' and 'shipping' (coral, small) docked to it. Step 1 base + server; step 2 refund adapter pops, :flow request pulse from refunds UI routes through 'refund'; step 3 shipping adapter pops and a second pulse routes to it; step 4 a VRAM meter shows ~1 base + 2 x ~40 MB.

**Code.**

```text
lab-sft.md Lab 5 Run block (bash, 5 lines).
```

### 02.07 [gotcha] Three silent SFT defaults: q/v-only LoRA, float32, renamed kwargs

- File: `c02-07-silent-defaults.html`
- Id: `custom-c02-silent-defaults`

**Content.** Kicker: Gotcha · TRL 1.16 / PEFT 0.21 / transformers 5.20. Three .gotcha cards. (1) Symptom: adapter trains but underperforms; print_trainable_parameters shows 2,293,760 (0.38%). Cause: no target_modules -> PEFT default for qwen3 is ['q_proj','v_proj'] (constants.py:104). Fix: target_modules='all-linear' -> 10,092,544 (1.67%). (2) Symptom: OOM or 2x memory with no warning. Cause: SFTTrainer/GRPOTrainer load a string model id in float32 unless model_init_kwargs={'dtype': torch.bfloat16}. Fix: set dtype and log next(model.parameters()).dtype at step 0. (3) Symptom: copied tutorial fails. Exact errors: "TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'tokenizer'" -> processing_class=tok; "TypeError: SFTConfig.__init__() got an unexpected keyword argument 'max_seq_length'" -> max_length; "... unexpected keyword argument 'warmup_ratio'" -> warmup_steps=0.03 (float = ratio). Also: PPO removed in TRL v1.13.0 ('cannot import name PPOTrainer'). Fix code: a .code-wrap.bad (old tutorial call) / .code-wrap.good (TRL 1.16 call) pair.

**Visual and animation.** Left: three gotcha cards appear one per step. Right: bespoke animation of a 28-layer stack; step 1 only q and v badges light (2.29M counter), step 2 all 7 badges light (10.09M); step 3 a memory bar halves when dtype flips float32 -> bf16; step 4 the bad/good code pair slides in with red strike-through on 'tokenizer=', 'max_seq_length=', 'warmup_ratio='.

**Code.**

```text
Bad (pre-1.0 tutorial): SFTTrainer(model, tokenizer=tok, args=SFTConfig(max_seq_length=1024, warmup_ratio=0.03), ...). Good (lab-sft Lab 2): SFTConfig(model_init_kwargs={'dtype': torch.bfloat16}, max_length=1024, warmup_steps=0.03, ...); SFTTrainer(model='Qwen/Qwen3-0.6B', processing_class=tok, args=args, peft_config=LoraConfig(r=16, lora_alpha=32, target_modules='all-linear', task_type='CAUSAL_LM')).
```

### 02.08 [buildup] Same refund data, no GPUs: managed SFT on gemini-3.5-flash

- File: `c02-08-vertex-managed.html`
- Id: `custom-c02-vertex-managed`

**Content.** Kicker: Build. Feature added: the managed path for the same 2,992 refund rows. .code-wrap.bad/.good framed as 'open-weights path (Labs 1-5)' vs 'managed path'. Good = lab-sft Lab 7 lab7_vertex_gemini_sft.py (VERIFIED google-genai 2.33.0): env GOOGLE_CLOUD_LOCATION=us (Gemini 3+: us/eu multi-region only), GOOGLE_GENAI_USE_ENTERPRISE=True; to_gemini() rows with systemInstruction + contents (user/model parts); client.tunings.tune(base_model='gemini-3.5-flash', training_dataset=types.TuningDataset(gcs_uri=...), config=types.CreateTuningJobConfig(tuned_model_display_name='refund-agent-v1', validation_dataset=..., epoch_count=3, adapter_size=types.AdapterSize.ADAPTER_SIZE_FOUR, learning_rate_multiplier=1.0)); poll job.has_ended; call job.tuned_model.endpoint with ThinkingConfig(thinking_level=ThinkingLevel.MINIMAL). Output (illustrative): JOB_STATE_PENDING -> RUNNING -> SUCCEEDED projects/.../locations/us/endpoints/... .delta badges: '0 GPUs', 'adapter sizes 1/2/4/8/16', 'val cap 5,000', 'no SLA'. Limits: 131,072 tokens per example, 1 GB JSONL; SFT 'is not a Covered Service'. Pitfalls: wrong region -> JOB_STATE_FAILED; pydantic.ValidationError when training_dataset is a raw string; one concurrent tuning job by default (global quota). Best practice: read job.tuning_data_stats.supervised_tuning_data_stats (total_billable_token_count, total_truncated_example_count, dropped_example_reasons): truncation is a cost leak and a quality leak. Cite codelab 'Fine-tune Gemini on Gemini Enterprise Agent Platform' https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/9-ai-finetuning/finetune-gemini-vertex-ai.

**Visual and animation.** Bespoke job-state animation: a horizontal track PENDING -> RUNNING -> SUCCEEDED; a job token moves along it while a mini table of tuning_data_stats fills key by key (billable tokens, truncated 0, dropped 0). Step 1 code focus on to_gemini; step 2 tune(); step 3 state track; step 4 delta badges.

**Code.**

```text
lab-sft.md Lab 7 lab7_vertex_gemini_sft.py (full 44 lines, .xs). data-focus="1:12-15, 2:21-32, 3:33-35, 4:37-41".
```

### 02.09 [buildup] Gemma 4 breaks TRL masking; Unsloth train_on_responses_only fixes it

- File: `c02-09-unsloth-gemma4.html`
- Id: `custom-c02-unsloth-gemma4`

**Content.** Kicker: Build. Feature added: the Gemma 4 E2B path on a free T4 for Acme's ticket-triage labels from the same Bitext dataset ({category, intent} JSON). .code-wrap.bad: SFTConfig(assistant_only_loss=True) on google/gemma-4-E2B-it -> "ValueError: The chat template is not training-compatible (missing prefix-preservation or {% generation %} markers) and patching is not supported for this template." (TRL 1.16 patches gemma/gemma3, not Gemma 4). .code-wrap.good: lab-sft Lab 6 (VERIFIED on unsloth main, PyPI 2026.10.8): from unsloth import FastModel FIRST; FastModel.from_pretrained('unsloth/gemma-4-E2B-it', max_seq_length=1024, load_in_4bit=True); get_peft_model(r=16, lora_alpha=16, lora_dropout=0); get_chat_template(tokenizer, chat_template='gemma-4') (markers <|turn> ... <turn|>, not Gemma 3 <start_of_turn>); trainer = train_on_responses_only(trainer); save_pretrained_gguf(..., quantization_method='Q8_0'). .delta: the official notebook printed 'Trainable parameters = 12,668,928 of 5,135,846,944 (0.25% trained)' at r=8. Pitfalls: 'Unsloth: Could not auto-detect chat template structure - pass instruction_part and response_part.' -> instruction_part='<|turn>user\n', response_part='<|turn>model\n'; GGUF export after wrapping with raw PeftModel.from_pretrained silently ships the base (unsloth #11698) -> load the adapter via FastModel.from_pretrained(adapter_dir) and probe 3 prompts in llama.cpp. Cite notebook Gemma4_(E2B)-Text.ipynb in github.com/unslothai/notebooks.

**Visual and animation.** Before/after split. Step 1 bad code with the red ValueError in an .err output pane. Step 2 good code. Step 3 bespoke token-strip: a Gemma 4 turn '<|turn>user ... <turn|> <|turn>model {json} <turn|>' where user tokens fade to grey (-100) and only the JSON label stays coral. Step 4 delta badge and a GGUF file icon 'Q8_0'.

**Code.**

```text
lab-sft.md Lab 6 lab6_unsloth_gemma4_triage.py (show lines 1-14 model/peft/template and 26-33 trainer, train_on_responses_only, save). Bad snippet: 3 lines SFTConfig(assistant_only_loss=True) with model='google/gemma-4-E2B-it'.
```

### 02.10 [paper] Pick SFT checkpoints by generated accuracy, not by validation loss

- File: `c02-10-select-checkpoints.html`
- Id: `custom-c02-select-checkpoints`

**Content.** Kicker: arXiv Sep-Oct 2026. Three .paper cards. (1) 2609.36569 'From Checkpoint Variation to Selection Gains in SFT' (29 Sep 2026): across 60 math SFT trajectories, generation-based selection beats matched NLL selection by 0.71 and 0.85 pp; 32 -> ~305 validation items adds ~0.3 pp; gain over keeping the final checkpoint 'unresolved'. Monday: score checkpoints with the task metric on >= 300 items. (2) 2609.01244 'Post-Training Science for SFT' (1 Sep 2026): one-lever-at-a-time sweeps on 4 real customer datasets, Qwen3/Llama up to 235B MoE, LoRA and full FT; asks 'whether validation loss ... faithfully ranks downstream quality'. Monday: sweep LR first. (3) 2610.25497 'Self-Distillation for SFT' (18 Oct 2026): teacher = same model with the gold answer in context, forward KL to an EMA teacher; better new-task accuracy and less general-benchmark loss than SFT (Qwen, Llama). Tie-in: the Lab 1 sweep table (illustrative): r64_lr5e-4 has the lowest eval_loss 0.548 but intent_exact 0.921 < r16_lr2e-4 0.934.

**Visual and animation.** Method animation for card 1: 6 checkpoint dots along a training timeline; step 1 an NLL bar under each dot picks the lowest-loss checkpoint (blue ring); step 2 a generated-accuracy bar under each dot picks a different checkpoint (green ring) with '+0.71-0.85 pp'. Step 3: the sweep table (3 rows) appears with the lowest-loss row flagged 'not the best task score'.

## Chapter 03: QLoRA and honest before/after evaluation

Tone: `model`

**Scenario.** Acme claims desk: turn free-text adjuster notes into strict JSON {loss_type, severity, needs_adjuster, policy_section} with Qwen3-4B-Instruct-2507 in 4-bit NF4, then measure base vs tuned on the same quantized weights.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-sft.md
- C:/Users/evija/googleadk2.0/research-v2/custom/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/custom/arxiv-sft-rl.md
- C:/Users/evija/googleadk2.0/research-v2/custom/00-VERIFIED.md

### 03.01 [chapter] QLoRA and honest before/after evaluation

- File: `c03-01-chapter.html`
- Id: `custom-c03-chapter`

**Content.** Chapter 03. .display 'QLoRA, then prove it'. Lede: 'A 4B model fits a 16 GB GPU in NF4. The adapter counts only when the same weights score better with it on.' Scenario: Acme claims notes -> strict JSON.

**Visual and animation.** Self-animating mini-diagram: a 16-bit weight block compresses into a 4-bit block (NF4 label); a small coral adapter toggles on/off with a switch icon; a JSON-valid gauge moves between 0.6 and 1.0 with the switch; loop.

### 03.02 [lab] Prompt-completion rows mask the prompt for any chat template

- File: `c03-02-lab2-data.html`
- Id: `custom-c03-lab2-data`

**Content.** Kicker: Lab 2 Acme claims extractor · step 1 of 4. Run it Monday: same pin line as Lab 1; GPU 16-24 GB (T4 16 GB works with per_device_train_batch_size=2); files claims_train.jsonl / claims_val.jsonl / claims_test.jsonl (test never used for training or checkpoint selection); folder tree. Show one JSONL row (lab-sft Lab 3; example row made up for the lab, not real data): prompt = [system 'Extract the claim as JSON with keys loss_type, severity, needs_adjuster, policy_section.', user 'Insured reports burst pipe in upstairs bathroom 03/10, ceiling collapsed in kitchen, family staying with relatives.'], completion = [assistant '{"loss_type": "water", "severity": "high", "needs_adjuster": true, "policy_section": "Coverage A - Dwelling"}']. Steps-rail: completion_only_loss=None resolves to True when both prompt and completion columns exist (sft_trainer.py:959-963); works for Gemma 4 too because no {% generation %} tag is needed; error 'ValueError: A formatting function was provided while completion_only_loss=True, which is incompatible.' -> drop formatting_func. Output pane: python -c load_dataset(...); print(ds) showing train/test splits with columns ['prompt','completion'] (illustrative).

**Visual and animation.** Bespoke animation: the JSONL row is drawn as two coloured bands, prompt (grey) and completion (coral). Step 1 the row types in; step 2 the prompt band receives a '-100' stamp per token (mask) while the completion band stays lit; step 3 a mini comparison: 'assistant_only_loss needs template markers' (red, Gemma 4 x) vs 'prompt-completion needs nothing' (green check).

**Code.**

```text
lab-sft.md Lab 3 JSONL example row + 3-line load_dataset snippet from lab3_qlora_claims.py line 7.
```

### 03.03 [lab] QLoRA in one trainer call: NF4, double quant, paged 8-bit Adam

- File: `c03-03-lab2-qlora.html`
- Id: `custom-c03-lab2-qlora`

**Content.** Kicker: Lab 2 Acme claims extractor · step 2 of 4. .lab-head: python lab3_qlora_claims.py ; second terminal: nvidia-smi --query-gpu=memory.used --format=csv -l 5. Code = lab-sft Lab 3 lab3_qlora_claims.py (VERIFIED trl 1.16.0, transformers 5.20.2): BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16); SFTConfig(lr 1e-4, 3 epochs, batch 4 x accum 4, optim='paged_adamw_8bit', eval/save per epoch); SFTTrainer(model='Qwen/Qwen3-4B-Instruct-2507', quantization_config=bnb, peft_config=LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules='all-linear')). Focus: (1) nf4 must be set: BitsAndBytesConfig default is 'fp4' and double_quant False, while the TRL CLI ModelConfig defaults to nf4 -> script and CLI 'QLoRA' quietly differ; (2) quantization_config goes on the trainer (TRL injects it into model_init_kwargs; setting both -> ValueError); no device_map needed; (3) TRL casts adapter params to bf16 for quantized models, no prepare_model_for_kbit_training call. T4 note: bf16=False, fp16=True, compute dtype float16 (SFTConfig defaults bf16=True). Cite: 'Fine-Tune Gemma using Hugging Face Transformers and QloRA' https://ai.google.dev/gemma/docs/core/huggingface_text_finetune_qlora.

**Visual and animation.** Code left with 3 focus bands; right: bespoke VRAM stack animation. A 16 GB bar fills with blocks: base weights bf16 (~8 GB) -> compressed to NF4 (~2.3 GB) on focus 1; double-quant constants shrink a sliver on focus 1b; optimizer states block goes 'paged' (dashed, partly offloaded) on focus 3; activations block. Labels show the bar staying under 16 GB. Block sizes are labelled 'approx.'.

**Code.**

```text
lab-sft.md Lab 3 lab3_qlora_claims.py (full 33 lines). data-focus="1:9-14, 2:28-32, 3:22-24".
```

### 03.04 [lab] 33 million trainable parameters steer a 4-billion-parameter model

- File: `c03-04-lab2-run.html`
- Id: `custom-c03-lab2-run`

**Content.** Kicker: Lab 2 Acme claims extractor · step 3 of 4. Output pane 'output · illustrative' (lab-sft Lab 3; the parameter count is exact arithmetic from config.json and was recomputed by the verifier): 'trainable params: 33,030,144 || all params: ~4.06B || trainable%: ~0.8', {'loss': 0.902, 'mean_token_accuracy': 0.79, 'epoch': 0.1}, {'eval_loss': 0.142, 'eval_mean_token_accuracy': 0.957, 'epoch': 1.0}. Show the arithmetic as a small table: r x (in + out) summed over q, k, v, o, gate, up, down x 36 layers = 33,030,144. Steps-rail: eval_loss 0.142 still allows trailing prose after the JSON, so the next step measures schema validity; AQLoRA (arXiv 2608.23816, 24 Aug 2026): 'QLoRA saves memory but not time'; keeping the highest-NF4-error layers in fp16 trains 11.3 +/- 2.3% faster, and its choice matches Unsloth's dynamic-4bit list. Error on T4: bf16 not supported (exact text unverified, so show only the fix: bf16=False, fp16=True).

**Visual and animation.** Bespoke animation: a 36-layer column; each layer gets 7 small adapter chips as a counter accumulates r*(in+out) per module up to 33,030,144 (count-up with data-to). Step 2: a pie 0.8% coral vs 99.2% grey frozen. Step 3: eval_loss sparkline draws to 0.142 with a red caption 'loss is not the task metric'.

**Code.**

```text
lab-sft.md Lab 3 Expected output block (4 lines) + param arithmetic table.
```

### 03.05 [lab] Same weights, adapter off then on: JSON validity 0.615 to 0.995

- File: `c03-05-lab2-before-after.html`
- Id: `custom-c03-lab2-before-after`

**Content.** Kicker: Lab 2 Acme claims extractor · step 4 of 4. .lab-head: python lab4_eval_before_after.py | tee eval_report.txt. Code = lab-sft Lab 4 lab4_eval_before_after.py (VERIFIED peft 0.21.2): load base NF4 + PeftModel.from_pretrained(base, ADAPTER).eval(); generate() with apply_chat_template(add_generation_prompt=True, return_dict=True), do_sample=False, decode only new tokens out[0, enc['input_ids'].shape[1]:]; score() counts json_valid and per-field accuracy, catching JSONDecodeError; 'with model.disable_adapter(): before = score()'; after = score(). Output (illustrative, n=200): json_valid base=0.615 tuned=0.995 delta=+0.380; acc_loss_type 0.540 -> 0.930 (+0.390); acc_severity 0.385 -> 0.840 (+0.455); acc_needs_adjuster 0.470 -> 0.905 (+0.435). Steps-rail: disable_adapter keeps quantization noise identical in both arms, so the delta isolates the adapter; greedy decoding overrides Qwen's generation_config (do_sample true, temperature 0.6); 'json.decoder.JSONDecodeError: Extra data' on the base model is expected and counted invalid. Error: 'ValueError: Target modules {...} not found in the base model' -> load the base named in adapter_config.json base_model_name_or_path. Best practice: also run a general-capability regression (lm-eval MMLU/IFEval) on both arms; add a slice table by loss_type and note length (feeds C11).

**Visual and animation.** Bespoke animation: a toggle switch 'adapter OFF/ON' above four paired horizontal bars (json_valid, loss_type, severity, needs_adjuster). Step 1 code focus on disable_adapter; step 2 OFF bars grow (grey); step 3 switch flips ON and coral bars grow with .delta badges (+0.380, +0.390, +0.455, +0.435); step 4 a callout 'n=200: add CIs in C11'.

**Code.**

```text
lab-sft.md Lab 4 lab4_eval_before_after.py (full 36 lines, .xs). data-focus="1:15-20, 2:22-35, 3:37-40".
```

### 03.06 [gotcha] QLoRA traps: fp4 by default, 4-bit merges drift, exports ship the base

- File: `c03-06-qlora-defaults.html`
- Id: `custom-c03-qlora-defaults`

**Content.** Kicker: Gotcha · QLoRA and export. Three .gotcha cards. (1) Symptom: 'QLoRA' run is worse than the paper recipe. Cause: BitsAndBytesConfig defaults bnb_4bit_quant_type='fp4' and use_double_quant=False (transformers 5.20.2 quantization_config.py:440-452). Fix: set nf4 + double quant explicitly. (2) Symptom: after merge_adapter(); unmerge_adapter() on a 4-bit model the base weights drift further each cycle (PEFT #3878). Cause: merging into 4-bit re-quantizes (lossy). Fix: reload the base for A/B, merge into a bf16 copy for export; checksum dequantized weights before and after. (3) Symptom: exported GGUF answers exactly like the base model (unsloth #11698). Cause: save_pretrained_gguf is bound to the base object, so wrapping with PeftModel.from_pretrained bypasses the merge. Fix: load the adapter dir with FastModel.from_pretrained and run 3 probe prompts on the GGUF. Related: merged Gemma 4 gave garbled output while the adapter-only save worked (unsloth #7318) -> compare merged vs adapter perplexity on 50 held-out rows (within ~1%).

**Visual and animation.** Three cards revealed per step. Right side bespoke animation: a weight histogram (bf16) that, on each merge/unmerge cycle (step 2), snaps to 16 NF4 levels and shifts a little (3 cycles, deterministic offsets), with a drift counter. Step 3: a GGUF file icon whose probe answers match the base (red equals sign) then, after the fix, differ (green).

**Code.**

```text
Fix code (lab-sft Lab 3 + Lab 5): bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16)  # export: base = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16); merged = PeftModel.from_pretrained(base, ADAPTER).merge_and_unload(safe_merge=True).
```

### 03.07 [gotcha] DPO loss stuck at 0.6931 means LoRA touched almost nothing

- File: `c03-07-lora-coverage.html`
- Id: `custom-c03-lora-coverage`

**Content.** Kicker: Gotcha · PEFT target modules (gotchas.md A4). Symptom: a DPO-LoRA run on nvidia/NVIDIA-Nemotron-Nano-9B-v2 finished 25/25 steps; loss stayed at 0.6931 (= ln 2) on every step; HumanEval 0.0% (0/164). Cause: PEFT default targets for nemotron_h are attention projections only, 4 of 56 layers; the other 52 are Mamba layers (in_proj, out_proj). PEFT raises only when no target matches; a partial match is silent (PEFT #3658, open). Fix: list hybrid module names explicitly and assert per-layer coverage (code). Second card: wrong adapter loads with no warning and strict=True is ignored (PEFT #3804, open; PR #3832) -> diff adapter keys against model keys with safetensors and add a golden-output test (adapter answers must differ from base on 5 prompts). Detect early: DPO loss exactly ln 2 = policy equals reference.

**Visual and animation.** Bespoke animation: 56 thin layer bars (attention layers blue, Mamba layers green). Step 1: only 4 bars light coral (default targets) and a DPO loss line stays flat at 0.6931 (draws). Step 2: the assert fires (red 'LoRA on 4 layers only'). Step 3: after listing in_proj/out_proj, all 56 light and the loss line bends down.

**Code.**

```text
gotchas.md A4 coverage assert (6 lines): from peft import get_peft_model; m = get_peft_model(model, cfg); m.print_trainable_parameters(); hit = {n.split('.lora_A')[0] for n, _ in m.named_parameters() if 'lora_A' in n}; layers = {int(n.split('layers.')[1].split('.')[0]) for n in hit if 'layers.' in n}; assert len(layers) == model.config.num_hidden_layers, f'LoRA on {len(layers)} layers only'. Plus A5 key diff (5 lines).
```

### 03.08 [paper] SFT on a reasoning model can erase its reasoning: constrain the update

- File: `c03-08-forgetting.html`
- Id: `custom-c03-forgetting`

**Content.** Kicker: arXiv Jul-Sep 2026. Three .paper cards. (1) 2609.25618 'Reasoning-Preserving Fine-Tuning of Post-RL LLMs with Null-Basis LoRA' (22 Sep 2026): plain LoRA SFT on post-RL models drops reasoning from 63.8% to 8.3% (3B) and 80.1% to 9.4% (1.5B); NB-LoRA restricts updates to the null space of reasoning activations, matches LoRA on the task, keeps reasoning near pre-FT levels, 6.3x faster than the compared method (verifier-confirmed via HTML). Monday: when you SFT a thinking model like Qwen3, re-run a reasoning benchmark on both arms. (2) 2607.23711 'The Intruder Threshold' (26 Jul 2026): predicts which LoRA layers grow forgetting-driving intruder dimensions; lowering alpha or LR is the robust fix. (3) 2607.21351 'How Much Can a LoRA Adapter Memorize?' (23 Jul 2026): LoRA stores 2-3.4 bits per parameter; at equal accuracy SFT memorizes ~3x more example-specific information than GRPO. Monday: add a general-capability regression to the Lab 2 before/after script.

**Visual and animation.** Method animation for NB-LoRA: a 2D plane with a grey 'reasoning activations' subspace arrow; step 1 a plain LoRA update arrow points partly along it (reasoning bar 63.8 -> 8.3 drains red); step 2 the update is projected onto the orthogonal null space (arrow rotates to perpendicular, reasoning bar stays full); step 3 cards 2 and 3 appear with count-ups (2-3.4 bits/param, 3x).

### 03.09 [practices] Ten SFT rules that each prevent a failure we saw in code

- File: `c03-09-sft-checklist.html`
- Id: `custom-c03-sft-checklist`

**Content.** Best practices (lab-sft §10, verified). ul.checks, each with a reason: (1) Pin trl/peft/transformers/torch and pass dtype (float32 default doubles memory). (2) Prove the mask in CI: fail if any row has sum(mask)==0 or the TRAIN span does not end with the stop token. (3) target_modules='all-linear' (Qwen3/Llama/Gemma3 default is q,v only). (4) LoRA LR 1e-4..2e-4 and set alpha explicitly: TRL CLI 16/32/0.05 vs PEFT 8/8/0.0 vs Unsloth 16/16 ('my r=16 is not your r=16'). (5) QLoRA = nf4 explicitly; merge into bf16. (6) Select checkpoints on the task metric (2609.36569); gate deploys on adapter on/off deltas. (7) Do not inject facts via SFT (2608.30987); use RAG. (8) Train and serve with the same think-block convention; on Vertex use thinking_level MINIMAL. (9) Serve adapters with multi-LoRA; merge only for GGUF/edge. (10) Managed tuning: check region us/eu, the 5,000-example validation cap, truncation stats, no SLA. Config snippet: the TRL CLI YAML (refund_sft.yaml) with use_peft, lora_target_modules: all-linear, assistant_only_loss: true, warmup_steps: 0.03.

**Visual and animation.** Two-column checks list (stagger, 3 steps: rules 1-5, rules 6-10, then the YAML slides in from the right with data-focus on the 4 critical keys). A small table 'defaults differ' (TRL CLI / PEFT / Unsloth: r, alpha, dropout) builds row by row.

**Code.**

```text
lab-sft.md Lab 8 refund_sft.yaml (21 lines). data-focus="1:6-7, 2:10-11".
```

## Chapter 04: Rewards you can unit-test

Tone: `tool`

**Scenario.** Acme refunds desk: a refund-decision agent answers <answer>{decision, refund_amount, reason}</answer>; gold labels come from the policy engine. Write the reward once, unit-test it on CPU, and run it unchanged on TRL, OpenAI graders and Vertex Gemini RFT.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-rl.md
- C:/Users/evija/googleadk2.0/research-v2/custom/industry.md
- C:/Users/evija/googleadk2.0/research-v2/custom/arxiv-sft-rl.md
- C:/Users/evija/googleadk2.0/research-v2/custom/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/custom/00-VERIFIED.md

### 04.01 [chapter] Rewards you can unit-test

- File: `c04-01-chapter.html`
- Id: `custom-c04-chapter`

**Content.** Chapter 04. .display 'Rewards you can unit-test'. Lede: 'A reward function is code. Test it with a known hack before it meets a GPU.' Scenario: Acme refund-decision agent.

**Visual and animation.** Self-animating mini-diagram: a completion card enters a 'reward()' tool node; three test tubes (good / hack / broken) feed it in a loop and each gets a score tag 1.0 / 0.0 / 0.0; a green CI check pulses.

### 04.02 [concept] GRPO scores answers against their group, so cheap partial credit wins

- File: `c04-02-group-advantage.html`
- Id: `custom-c04-group-advantage`

**Content.** Concept slide, <= 3 lines. Line 1: GRPO samples 8 completions per prompt and uses (reward - group mean) / group std as the advantage (scale_rewards='group', TRL 1.16 default). Line 2: if all 8 score the same, the advantage is 0 and there is no gradient (logged as frac_reward_zero_std). Line 3: a 0.5 that costs zero tokens beats a 0.0 inside the group, so the policy learns the hack unless partial credit is gated on validity.

**Visual and animation.** Large bespoke animation (Deck.register). Eight rollout cards in a row for one refund prompt. Step 1: rewards drop onto each card (1.0, 0.0, 0.5, 0.0, 0.0, 1.0, 0.0, 0.0). Step 2: a horizontal mean line draws at the group mean; arrows grow up/down from each card = advantage (green up, red down). Step 3: the 0.5 card is revealed as the hack '{"decision": "approve"} approve deny escalate'; its green arrow pulses (it is reinforced). Step 4: switch to the gated reward; the hack card falls to 0.0 and its arrow turns red. Step 5: all 8 cards set to 0.0; all arrows vanish and a counter 'frac_reward_zero_std +1' ticks. Deterministic values, step() renders any n.

### 04.03 [lab] Two refund rewards in TRL's signature: format and gated decision

- File: `c04-03-lab3-rewards.html`
- Id: `custom-c04-lab3-rewards`

**Content.** Kicker: Lab 3 Acme refund-decision agent · step 1 of 4. Run it Monday: Python >= 3.11 only, no packages for the test; the same functions plug into GRPOTrainer unchanged (trl==1.16.0). Folder tree refunds_rl/{refund_rewards.py, tests/test_rewards.py}. Code = lab-rl Lab 1 refund_rewards.py (RAN by the verifier, output identical): ANSWER_RE, _parse(), format_reward(completions, **kwargs) -> 0.2 if the answer block parses with the 3 keys and a valid decision; decision_reward(completions, gold_decision, gold_amount, **kwargs) -> None when no gold label, 0.0 unless schema-valid and decision matches, 1.0 if amount within $0.01, else 0.5. Focus: (1) c[0]['content'] for conversational completions; **kwargs required (TRL passes prompts, completion_ids, trainer_state, log_extra, log_metric, every dataset column); (2) named params receive dataset columns with the same name; (3) the schema gate 'not REQUIRED <= obj.keys()'; (4) None -> NaN -> TRL skips that reward for the row; zip(strict=True). Steps-rail matches each focus.

**Visual and animation.** Code left (.sm, 28 lines visible: helper + both rewards), 4 focus bands; right: steps-rail plus a small diagram: dataset row columns (prompt, gold_decision, gold_amount) flow as wires into the decision_reward node parameters by name (3 wires, labels = column names).

**Code.**

```text
lab-rl.md Lab 1 refund_rewards.py lines 1-50 (without __main__). data-focus="1:22-29, 2:32, 3:40-42, 4:36-38".
```

### 04.04 [lab] The unit test caught a hack: schema-less answers scored 0.5

- File: `c04-04-lab3-selftest.html`
- Id: `custom-c04-lab3-selftest`

**Content.** Kicker: Lab 3 Acme refund-decision agent · step 2 of 4. .lab-head: python refund_rewards.py. Show the __main__ block: good, wrong_amt, hack ('<answer>{"decision": "approve"}</answer> approve deny escalate'), broken ('Sure! I approved it.'). Output pane (RAN, exact): 'format  : [0.2, 0.2, 0.0, 0.0]', 'decision: [1.0, 0.5, 0.0, 0.0]', 'no-label: [None]'. Then a .code-wrap.bad showing the first draft output 'decision: [1.0, 0.5, 0.5, 0.0]' (no REQUIRED gate) -> the hack earned 0.5. Second output pane: TRL built-ins (RAN from v1.16.0 source): think_format_reward -> [1.0, 0.0] (regex demands the completion START with <think>); get_soft_overlong_punishment(max_completion_len=512, soft_punish_cache=128) on lengths 300/448/480/512/600 -> [0.0, -0.5, -0.75, -1.0, -1.0] (linear ramp from 384 to 512, DAPO Eq. 13). Best practice: tests/test_rewards.py with >= 1 known hack per reward: 'right key, no answer', 'keyword stuffing', 'empty JSON', 'answer in the wrong tag'.

**Visual and animation.** Bespoke animation: four completion cards slide into a reward machine one per step and receive score tags (from the exact output). Step 5: the 'draft' toggle flips back to the old reward and the hack card's tag changes 0.0 -> 0.5 in red ('caught in CI'). Then a small ramp chart for the soft overlong penalty draws (0 to -1 between 384 and 512 tokens) with the 5 test points dropping onto it.

**Code.**

```text
lab-rl.md Lab 1 __main__ block (8 lines) + the TRL built-ins snippet (6 lines).
```

### 04.05 [lab] Same logic as an OpenAI multi-grader: test locally, validate, run

- File: `c04-05-lab3-openai-graders.html`
- Id: `custom-c04-lab3-openai-graders`

**Content.** Kicker: Lab 3 Acme refund-decision agent · step 3 of 4. Run it Monday: pip install "openai==3.37.0"; export OPENAI_API_KEY. Status banner (V-doc): 'OpenAI is winding down the fine-tuning platform'; RFT only for o4-mini, which shuts down 2026-10-23; teach it as 'graders are reward functions'. Code = lab-rl Lab 7 lab7_openai_graders.py (VERIFIED openai 3.37.0): GRADE_SRC python grader grade(sample, item) -> 0 / 0.5 / 1; tag = string_check ilike {{sample.output_text}} vs {{item.policy_id}}; grader = {'type':'multi', 'graders': {'policy': policy, 'tag': tag}, 'calculate_output': '0.8 * policy + 0.2 * tag'}; exec(GRADE_SRC, ns) local test; client.fine_tuning.alpha.graders.validate(grader=grader); .run(grader=grader, model_sample=sample, item=item). Output: 'local policy score: 1.0' (RAN); then illustrative 'reward: 1.0 sub: {'policy': 1.0, 'tag': 1.0} errors: MetadataErrors(formula_parse_error=False, ..., python_grader_runtime_error=False)'. Self-check: 0.8*1.0 + 0.2*1.0 = 1.0. Extra local tests (RAN): wrong amount 0.5; 'I approve it' 0.0; deny 0.0; reasoning before JSON 1.0. Steps-rail: python grader limits (256 kB, no network, 2 min, 2 GB RAM; import requests fails -> score 0); formula variable names must match grader keys (formula_parse_error); SDK typing gotcha: MultiGraderParam.graders is typed as a single grader, the docs use a dict; follow the docs.

**Visual and animation.** Bespoke animation: a tree with root 'refund_grader (multi)' and two leaves 'policy (python)' and 'tag (string_check)'; step 1 local exec lights the python leaf with 1.0; step 2 validate -> green check on root; step 3 run -> sub_rewards flow up as numbers, the formula 0.8*1.0 + 0.2*1.0 animates to 1.0; step 4 a red 'shut down 2026-10-23' ribbon crosses the 'jobs.create' box (job creation shown greyed).

**Code.**

```text
lab-rl.md Lab 7 lab7_openai_graders.py lines 1-36 (omit the LAUNCH_RFT block, mention it in notes). data-focus="1:5-21, 2:22-26, 3:31-36".
```

### 04.06 [lab] Vertex Gemini RFT: validate_reward is CI for your reward function

- File: `c04-06-lab3-vertex-rft.html`
- Id: `custom-c04-lab3-vertex-rft`

**Content.** Kicker: Lab 3 Acme refund-decision agent · step 4 of 4. Run it Monday: pip install "google-genai==2.33.0"; gcloud auth application-default login; GOOGLE_CLOUD_PROJECT, RFT_BUCKET; Pre-GA (not for production or confidential data), us-central1/europe-west4, v1beta1 only. Code = lab-rl Lab 8 lab8_vertex_rft.py (VERIFIED google-genai 2.33.0): EVALUATE_SRC evaluate(example, response) returns -1.0 unparseable, -0.5 wrong decision, 0.25 wrong amount, 1.0 correct (clipped to [-1, 1]); SingleReinforcementTuningRewardConfig(reward_name='refund_policy', code_execution_reward_scorer=ReinforcementTuningCodeExecutionRewardScorer(python_code_snippet=EVALUATE_SRC)); client.tunings.validate_reward(parent=..., sample_response=sample, example=example, single_reward_config=reward); optional tune(method='REINFORCEMENT_TUNING', batch_size=32, samples_per_prompt=16, thinking_level='MINIMAL'). Output: local evaluate() tests (RAN) 1.0 / 0.25 / -0.5 / -1.0; illustrative 'overall_reward: 1.0 | details: {'refund_policy': ReinforcementTuningRewardInfo(reward=1.0, error_status=None, ...)}'. Steps-rail: return a low value, never crash ('If more than 80% of your reward invocations are errored ... the tuning job is stopped automatically'); batch_size x samples_per_prompt must be divisible by 16 and <= 8,192 (32 x 16 = 512); sandbox 100 s, 1 CPU, 1 GB; watch /learnable_prompt_ratio (Vertex analogue of 1 - frac_reward_zero_std). Pitfall: forcing api_version='v1' returns jobs with RFT fields missing.

**Visual and animation.** Bespoke animation: a number line from -1 to +1; four test responses drop onto it at -1.0, -0.5, 0.25, 1.0 (one per step, colour red -> green). Step 5: a batch grid 32 x 16 fills (512 cells) and a '/ 16 OK' check appears; a gauge 'errored invocations' with a red line at 80% shows the auto-stop rule.

**Code.**

```text
lab-rl.md Lab 8 lab8_vertex_rft.py lines 1-49 (validation part; tune() block shown as 8 greyed lines). data-focus="1:9-28, 2:29-32, 3:42-45".
```

### 04.07 [gotcha] A constant answer earns the class prior: return 'billing' scores 0.25

- File: `c04-07-code-reward-floor.html`
- Id: `custom-c04-code-reward-floor`

**Content.** Kicker: Gotcha · code-execution rewards (lab-rl Lab 3, RAN by the verifier). Context: the same desk routes tickets with a generated route_ticket(subject, body); reward = fraction of hidden unit tests passed in a subprocess. Output pane (exact): 'metric code/timeout_rate 0.25' and '[1.0, 0.25, 0.0, 0.0]' for good keyword router / lazy constant / while True loop / no code. Three .gotcha cards: (1) Symptom: reward 0.25 for a program that does nothing. Cause: the class prior over 4 balanced queues. Fix: balance hidden tests, subtract the constant-baseline score, log a code/hardcoded_return_rate metric. (2) Symptom: training hangs, rollout step takes minutes. Cause: no timeout, a while True sample blocks the reward. Fix: subprocess.run([sys.executable, '-I', path, t], cwd=tmpdir, timeout=5), count timeouts via log_metric, use async def rewards. (3) Symptom: reward is memorizable. Cause: hidden tests also appear in the prompt. Fix: shots, hidden = rows[:3], rows[3:]. Note: subprocess with -I is a teaching sandbox, not a security boundary; use containers/gVisor/Firecracker for untrusted code. Paper hook: 2610.28707 SimHack (20 Oct 2026, Google) predicts hacking onset to 11.3% median relative error; curricula train 96.6% longer without hacking.

**Visual and animation.** Bespoke animation: four candidate programs run in four sandbox boxes in parallel; a timer bar fills in each; the loop box hits the 5 s line and turns red 'timeout'; scores stamp in. Step 3: a bar for 'constant baseline 0.25' appears as a dashed floor line under all rewards; step 4 subtracting it re-centres the scores.

**Code.**

```text
lab-rl.md Lab 3 code_reward.py unit_test_reward() lines 15-37 (subprocess + timeout + log_metric) as the fix; bad: the lazy candidate "def route_ticket(subject, body):\n    return 'billing'".
```

### 04.08 [industry] Shopify Sidekick built judge agreement first, then gated GRPO rewards

- File: `c04-08-shopify-gated.html`
- Id: `custom-c04-shopify-gated`

**Content.** Kicker: In production · Shopify Sidekick (Aug 2025, industry.md A8). Architecture: single-agent loop; tool count 0-20 fine, 20-50 blurred, 50+ hard to reason about; 'just-in-time instructions' returned with tool data instead of a giant system prompt. Eval first: ground-truth sets (GTX) sampled from real merchant conversations, >= 3 product experts per conversation, agreement by Cohen kappa / Kendall tau / Pearson; judge prompts iterated until kappa rose from 0.02 to 0.61 against a human-human ceiling of 0.69; LLM merchant simulator replays real goals. Training: GRPO with N-stage gated rewards: procedural checks (syntax, schema) first, then LLM-judge semantics. Hacks found: opt-out (explains why it can't help), tag hacking (customer_tags CONTAINS 'enabled' instead of customer_account_status = 'ENABLED'), hallucinated IDs and enum values. After fixes: syntax validity ~93% -> ~99%, judge correlation 0.66 -> 0.75. Quote: 'Vibe testing... is not going to cut it.' .cite https://shopify.engineering/building-production-ready-agentic-systems.

**Visual and animation.** Animated diagram: merchant pill -> Sidekick agent -> tools; below, the reward pipeline as a 2-stage gate: 'procedural checks' (amber) -> 'LLM judge' (blue) -> reward; a rollout token passes stage 1 or is stopped (red). Step 2: kappa thermometer climbs 0.02 -> 0.61 with a dashed ceiling at 0.69. Step 3: the three hack cards drop in. Step 4: two count-ups 93 -> 99% and 0.66 -> 0.75.

### 04.09 [paper] Verifiers fail by structure: side effects and constraint-only wins

- File: `c04-09-verifier-noise.html`
- Id: `custom-c04-verifier-noise`

**Content.** Kicker: arXiv Oct 2026. Three .paper cards. (1) 2610.17824 'Checking the Checkers' (13 Oct 2026): synthesis of 58 RLVR verifier-noise studies; error structure matters more than error rate; learnable false positives cause plateaus or collapse; under KL or a fixed budget, random errors also lower final accuracy. Monday: measure your verifier's FP/FN on 200 hand-labelled rollouts (TRL issue #7747 shows noisy verifiers change which groups survive zero-variance filtering). (2) 2610.09142 'Finding Side-Effect Loopholes in Verifiable Rewards' (6 Oct 2026): verifiers that check only the requested change pass runs with unrequested side effects; one count assertion per template rejected all six duplicates. Monday: assert route_ticket does not mutate globals or write files. (3) 2610.19525 CaLIF (14 Oct 2026): plain IF-RLVR lowers response quality 4.51 -> 2.96 while satisfying constraints; a reference-likelihood band raises constraint satisfaction 26.98 -> 34.64 and keeps quality at 4.59. Monday: every format reward needs a 'did it still answer?' term.

**Visual and animation.** Method animation for CaLIF: a log-likelihood number line with three zones (red 'quality risk' < l0, green 'desired' l0..l1, red 'likelihood inflation' > l1); rollout dots fall onto it one by one and colour by zone; step 2 a bar pair 4.51 -> 2.96 (IF-RLVR) vs 4.59 (CaLIF). Card 2 shows a mini diff with an unrequested file write highlighted red. Cards appear one per step.

**Code.**

```text
arxiv-sft-rl.md #6 calif_reward sketch (7 lines, labelled 'sketch from the paper, not official code').
```

## Chapter 05: GRPO with a verifier

Tone: `model`

**Scenario.** Acme claims back-office: RL-train Qwen2.5-0.5B-Instruct + LoRA to compute claim payouts (deductible -> coinsurance share -> policy limit) with a procedural generator that gives exact gold answers; then add a gated brevity reward, KL on/off and a reward-hacking tripwire.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-rl.md
- C:/Users/evija/googleadk2.0/research-v2/custom/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-v2/custom/arxiv-sft-rl.md
- C:/Users/evija/googleadk2.0/research-v2/custom/industry.md
- C:/Users/evija/googleadk2.0/research-v2/custom/gotchas.md

### 05.01 [chapter] GRPO with a verifier

- File: `c05-01-chapter.html`
- Id: `custom-c05-chapter`

**Content.** Chapter 05. .display 'GRPO with a verifier'. Lede: 'A generator with exact answers, a math verifier, and four metrics that tell you if RL is learning or hacking.' Scenario: Acme claims payout calculator.

**Visual and animation.** Self-animating mini-diagram: prompt -> 8 rollouts fan out -> verifier tool node -> rewards -> advantages flow back to the policy; a reward curve sparkline rises in a loop.

### 05.02 [lab] A claims generator gives exact gold answers and difficulty control

- File: `c05-02-lab4-generator.html`
- Id: `custom-c05-lab4-generator`

**Content.** Kicker: Lab 4 Acme claims payout calculator · step 1 of 5. Run it Monday: Linux + one 24 GB GPU; python -m venv; pip install "trl[peft,math_verify]==1.16.0" "transformers==5.20.2" "peft==0.21.2" "datasets==5.1.0" "accelerate==1.15.0" "math-verify==0.9.0" "trackio==0.43.0"; optional vllm==0.31.0 (not 0.32.0: trl[vllm] pins <=0.31.0); HF_TOKEN optional. Folder tree claims_rl/{claims_data.py, lab2_grpo_claims.py, lab4_rewards.py, lab4_kl_length.py}. Code = lab-rl Lab 2 claims_data.py (VERIFIED; SYSTEM fixed to a raw string by the verifier): SYSTEM = r'You are a claims adjuster. Think briefly, then give the payout as \boxed{number}.'; make_claim(rng): damage randrange(500, 20000, 50), deductible in {250, 500, 1000}, share in {70, 80, 90, 100}%, limit in {5000, 10000, 15000}; payout = min(max(damage - deductible, 0) * share / 100, limit); returns prompt messages + 'solution' (accuracy_reward reads the solution column). Output (RAN, seed=7): 'Damage $8750. Deductible $250. Insurer pays 100% ... capped at $15000 -> 8500', '$1700 ... 70% ... -> 1015', '$15400 ... 80% ... capped at $5000 -> 5000', '$2700 ... $500 ... -> 2200'. Steps-rail: exact gold = no label noise in the reward; held-out seed 99 for eval; difficulty mix matters in low-data RLVR (2610.25812).

**Visual and animation.** Bespoke animation: a payout 'pipe' with three valves (deductible, share %, limit cap). For each of the 4 sample claims (one per step), a damage bar flows through: shrinks by the deductible, scales by share, then is clipped at the limit (the 15400 case visibly hits the cap at 5000). The final number stamps as the gold 'solution'.

**Code.**

```text
lab-rl.md Lab 2 claims_data.py (full 20 lines). data-focus="1:5, 2:7-12, 3:13-16".
```

### 05.03 [lab] GRPOConfig for LoRA: 4 prompts x 8 generations, DAPO loss, no KL

- File: `c05-03-lab4-config.html`
- Id: `custom-c05-lab4-config`

**Content.** Kicker: Lab 4 Acme claims payout calculator · step 2 of 5. .lab-head: python lab2_grpo_claims.py (multi-GPU: accelerate launch --num_processes 2 ...). Code = lab-rl Lab 2 lab2_grpo_claims.py (VERIFIED trl 1.16.0): GRPOConfig(model_init_kwargs={'dtype': 'bfloat16'}, learning_rate=1e-5 (~10x the 1e-6 full-FT default), per_device_train_batch_size=8, gradient_accumulation_steps=4, num_generations=8, max_completion_length=256, loss_type='dapo', beta=0.0, mask_truncated_completions=True, reward_weights=[1.0, 0.5], max_steps=300, eval_steps=50, log_completions=True, report_to='trackio'); GRPOTrainer(model='Qwen/Qwen2.5-0.5B-Instruct', reward_funcs=[accuracy_reward, get_soft_overlong_punishment(max_completion_len=256, soft_punish_cache=64)], peft_config=LoraConfig(r=16, lora_alpha=32, target_modules='all-linear')). Focus: (1) generation_batch_size = per_device x processes x grad-accum = 32 completions = 4 prompts x 8, must divide by num_generations; (2) accuracy_reward uses math-verify and only accepts LaTeX-anchored answers (boxed first), returns None when gold cannot parse (row skipped, not 0); (3) soft overlong: 0 up to 192 tokens, linear to -1 at 256; mask_truncated_completions excludes cut-off answers (DAPO); (4) loss_type='dapo', beta=0.0 are the TRL 1.16 defaults written out: no reference model, no kl metric.

**Visual and animation.** Code left (.sm) with 4 focus bands; right: bespoke 'batch anatomy' animation: 32 completion slots arranged as 4 prompt rows x 8; focus 1 fills them; focus 2 each slot gets a verifier tick or cross; focus 3 slots longer than 192 tokens shade amber and those at 256 get a 'masked' hatch; focus 4 a greyed 'reference model' box with 'beta=0 -> not loaded'.

**Code.**

```text
lab-rl.md Lab 2 lab2_grpo_claims.py (full 36 lines). data-focus="1:10-13, 2:27, 3:14-15, 4:16".
```

### 05.04 [lab] Four GRPO metrics tell you if RL is learning, stuck or truncating

- File: `c05-04-lab4-metrics.html`
- Id: `custom-c05-lab4-metrics`

**Content.** Kicker: Lab 4 Acme claims payout calculator · step 3 of 5. Output pane 'output · illustrative' (metric keys verified in grpo_trainer.py): {'completions/mean_length': 141.2, 'completions/clipped_ratio': 0.06, 'rewards/accuracy_reward/mean': 0.31, 'rewards/soft_overlong_punishment_reward/mean': -0.04, 'reward': 0.29, 'reward_std': 0.38, 'frac_reward_zero_std': 0.25, 'entropy': 0.62} ... later {'rewards/accuracy_reward/mean': 0.66, 'completions/mean_length': 118.5, 'frac_reward_zero_std': 0.47}. Steps-rail (one per metric): (1) rewards/accuracy_reward/mean should rise; (2) frac_reward_zero_std = share of groups whose 8 samples scored the same -> zero advantage; rising toward 1.0 means the data became too easy or stayed too hard -> re-mix difficulty; (3) completions/clipped_ratio rising = answers hit the cap -> raise the cap or the length penalty; (4) entropy falling fast = collapse risk. Best practice: before RL, sample the base model 8x per prompt and drop 0/8 and 8/8 prompts; 2610.25325 'Where Groups Split' (18 Oct 2026): a short probe run predicts which prompts stay informative better than the base pass rate. Gotcha line: math-verify on Windows falls back to multiprocessing timeouts ('huge performance penalty') -> run on Linux, WSL2 or Colab.

**Visual and animation.** Bespoke dashboard animation (Deck.register, 4 small multiples, >= 55% canvas): accuracy reward line draws 0.31 -> 0.66; frac_reward_zero_std line 0.25 -> 0.47 with an amber threshold band; clipped_ratio stays near 0.06 under a 10% red line; entropy line descends gently. Each panel draws on its own step (4 steps) in sync with the steps-rail. Values follow the illustrative log; axes labelled 'illustrative'.

**Code.**

```text
lab-rl.md Lab 2 Expected output block (6 lines).
```

### 05.05 [lab] Pay for brevity only when the payout is right, and ramp it in

- File: `c05-05-lab4-gated-brevity.html`
- Id: `custom-c05-lab4-gated-brevity`

**Content.** Kicker: Lab 4 Acme claims payout calculator · step 4 of 5. .lab-head: python lab4_rewards.py. Code = lab-rl Lab 4 lab4_rewards.py (VERIFIED, regex bug fixed by the verifier, RAN): BOX_RE = re.compile(r'\\boxed\{([^{}]*)\}'); _is_correct(text, gold); gated_brevity_reward(completions, completion_ids, solution, trainer_state=None, log_metric=None, target_tokens=120, warmup_steps=50, **kwargs): ramp = min(1, step / warmup); wrong answers get 0.0 (counted in brevity/gated_frac); correct get ramp * max(0, 1 - len(ids) / (2 * target_tokens)). Output (RAN, exact): 'brevity/gated_frac 0.3333333333333333', 'brevity/ramp 0.5', '[0.4166666666666667, 0.0, 0.08333333333333331]' -> short correct earns credit, short wrong \boxed{1} earns nothing, long correct earns little; all halved at step 25 of a 50-step warm-up. Steps-rail: trainer_state is passed to every reward (curricula without a custom trainer); gating = minimal TAG-style anchor on correctness (2610.21404). Gotcha: a dataset column named like a reward kwarg (e.g. target_tokens) silently overrides the default with a list -> 'TypeError: unsupported operand type(s) for *: int and list'.

**Visual and animation.** Bespoke 2x2 animation: grid (correct / wrong) x (short / long). Step 1 the three test completions drop into their cells with the exact rewards. Step 2 a warm-up ramp dial turns from 0 to 0.5 at step 25 and the bars scale accordingly. Step 3 the 'wrong + short' cell is crossed out with 'no auxiliary-only credit'.

**Code.**

```text
lab-rl.md Lab 4 lab4_rewards.py (full 32 lines). data-focus="1:4, 2:16-18, 3:20-24".
```

### 05.06 [lab] Run KL on and off, and stop training when accuracy falls

- File: `c05-06-lab4-kl-tripwire.html`
- Id: `custom-c05-lab4-kl-tripwire`

**Content.** Kicker: Lab 4 Acme claims payout calculator · step 5 of 5. .code-wrap.term: '$ python lab4_kl_length.py 0.0' (run A, TRL default) and '$ python lab4_kl_length.py 0.04' (run B). Code = lab-rl Lab 4 lab4_kl_length.py (VERIFIED trl 1.16.0, transformers 5.20.2): class HackTripwire(TrainerCallback) with on_log reading logs['rewards/accuracy_reward/mean'], best_acc tracking, bad counter, control.should_training_stop = self.bad >= self.patience; GRPOConfig(beta=BETA, reward_weights=[1.0, 0.3], multi_objective_aggregation='normalize_then_sum', max_completion_length=384, run_name=f'kl{BETA}'); GRPOTrainer(reward_funcs=[accuracy_reward, gated_brevity_reward], callbacks=[HackTripwire()]). Output (illustrative): 'run kl0.0  step 300: rewards/accuracy_reward/mean 0.71  completions/mean_length 96   entropy 0.31' vs 'run kl0.04 step 300: ... 0.68  ... 121  entropy 0.47  kl 0.012' and a sample tripwire line '[tripwire] step 180: accuracy 0.612 < best 0.690'. Steps-rail: with LoRA, KL costs almost no memory (reference = adapter disabled); normalize_then_sum z-scores each reward in its group before weighting (GDPO-style); kl only appears when beta != 0; rule of thumb: verifiable reward -> beta 0.0, learned/judge reward -> beta > 0. Errors: 'ValueError: Number of reward weights (3) must match number of reward functions (2)'; OOM with beta > 0 and no LoRA (a full reference model loads).

**Visual and animation.** Bespoke animation: two overlaid run curves (kl0.0 coral, kl0.04 blue) for accuracy, length and entropy, drawing over 300 steps; step 3 a separate synthetic 'hacking' curve where total reward rises while accuracy falls, and the tripwire callback icon fires 3 times (patience 3) then a red STOP flag drops at the step. Curves labelled illustrative.

**Code.**

```text
lab-rl.md Lab 4 lab4_kl_length.py (full 40 lines, .xs). data-focus="1:11-23, 2:29-34, 3:36-41".
```

### 05.07 [gotcha] One missing backslash made the brevity reward zero for every sample

- File: `c05-07-boxed-regex.html`
- Id: `custom-c05-boxed-regex`

**Content.** Kicker: Gotcha · regex in rewards (found by the verifier, 00-VERIFIED.md corrections 1-3). Card 1: Symptom: brevity/gated_frac stays 1.0, brevity reward is always 0. Cause: BOX_RE = re.compile(r'\boxed\{...\}') -> in a raw regex, \b is a word boundary, so the pattern needs 'oxed' after a boundary and never matches a real '\boxed{8500}'. Verifier test: old pattern on real text [], fixed ['8500']. Fix: r'\\boxed\{([^{}]*)\}'. Card 2: Symptom: the self-test passed anyway. Cause: the test strings were non-raw, so '\b' was a backspace (\x08) and matched the broken pattern. Fix: raw strings in tests: r'...so \boxed{8500}'. Card 3: Symptom: the policy is told to answer in a garbled format. Cause: SYSTEM was a non-raw string, so the prompt held '\x08oxed{number}' (checked with repr). Fix: SYSTEM = r'... \boxed{number}.' and print(repr(SYSTEM)) in CI. Lesson: test rewards on real model output, not on strings that share the bug.

**Visual and animation.** Bespoke animation: the string '...so \boxed{8500}' rendered as characters. Step 1: the broken regex cursor scans, treats '\b' as a boundary marker (red caret) and fails at 'b'. Step 2: the non-raw test string shows '\b' collapsing into a single backspace glyph and 'matching' (false green). Step 3: the fixed regex highlights '\boxed{' and captures '8500' (green). Step 4: bad/good code pair.

**Code.**

```text
Bad: BOX_RE = re.compile(r'\boxed\{([^{}]*)\}'); comps = [[{'content': '...so \boxed{8500}'}]]. Good (lab-rl Lab 4): BOX_RE = re.compile(r'\\boxed\{([^{}]*)\}'); comps = [[{'content': r'...so \boxed{8500}'}]]; assert BOX_RE.findall(r'so \boxed{8500}') == ['8500'].
```

### 05.08 [gotcha] First GRPO run errors: batch divisibility, float32 OOM, vLLM pin

- File: `c05-08-grpo-first-run.html`
- Id: `custom-c05-grpo-first-run`

**Content.** Kicker: Gotcha · TRL GRPO 1.16. Three .gotcha cards with exact text. (1) 'ValueError: generation_batch_size (6) must be divisible by num_generations (8).' and 'GRPO requires at least 2 generations per prompt to calculate the advantages.' Cause: advantages are computed within a group, so a batch must hold whole groups. Fix: per_device x GPUs x grad-accum is a multiple of num_generations (1 GPU x 8 x 1, or 4 GPUs x 4 x 1 with num_generations=16). (2) 'torch.OutOfMemoryError ... Tried to allocate 3.81 GiB' on an 80 GB H100 for a 4B model (TRL #6684). Cause: float32 by default: 16.1 GB weights + 16.1 GB grads + 32.2 GB AdamW states ~ 64 GB before activations. Fix: model_init_kwargs={'dtype': 'bfloat16'}. (3) pip resolver conflict: vllm 0.32.0 is outside trl[vllm] 'vllm>=0.22.0,<=0.31.0'. Fix: pin vllm==0.31.0 for colocated rollouts; sample rollouts with top_p=1.0, top_k=-1, because truncated sampling biases the IS ratio (TRL #6789). Also: 'ValueError: auto_find_batch_size is not supported by GRPO' -> remove it.

**Visual and animation.** Bespoke animation: a memory bar for a 4B model in float32 builds block by block (weights 16.1, grads 16.1, Adam 32.2 = 64 GB, red over a 80 GB line once activations add) then collapses to bf16 + LoRA size. Step 2: batch slots 6 vs 8 show a broken last group (red), then 8 slots form a whole group (green).

**Code.**

```text
Fix (lab-rl Lab 2): GRPOConfig(model_init_kwargs={'dtype': 'bfloat16'}, per_device_train_batch_size=8, gradient_accumulation_steps=4, num_generations=8, ...)  # 32 = 4 x 8. Install: pip install "trl[peft,math_verify]==1.16.0" "vllm==0.31.0".
```

### 05.09 [paper] Gate auxiliary rewards on correctness; prefer GRPO over one-shot RFT

- File: `c05-09-tag-and-rft.html`
- Id: `custom-c05-tag-and-rft`

**Content.** Kicker: arXiv Oct 2026. Two .paper cards. (1) 2610.21404 'Multi-Reward Hacking: From Aggregation-Induced Drift to Trust-Anchored Defense' (15 Oct 2026, verifier-confirmed): symmetric aggregation lets GRPO converge to the easier auxiliary reward; TAG gating on Qwen3-4B with a brevity reward: pass@4 0.581 vs 0.220 additive, responses 44% shorter. Monday: replace r = r_correct + 0.1 * r_len with the one-line multiplicative gate (code). (2) 2610.25812 'Is it RL or Data? GRPO vs Rejection-Sampling Fine-Tuning' (19 Oct 2026, verifier-confirmed): same prompts, verifier and token cap (Qwen3-4B-Base + LoRA, KL 0, loss_type dapo): GRPO beats tuned RFT by up to 10.9 pp; single-round RFT does not move greedy accuracy; iterated RFT recovers ~30% of the gap; GRPO raises mean@8 42.5% -> 70.1-77.1% while pass@64 stays ~96-98%: RL sharpens, it does not add coverage. Monday: report pass@1 and pass@k together.

**Visual and animation.** Method animation: TAG 2x2 grid (primary 0/1 x auxiliary 0/1) with reward bar heights; step 1 additive version gives the (primary 0, aux 1) cell a bar; step 2 TAG shrinks it to 0; step 3 bar pair 0.220 vs 0.581 counts up. Card 2: step 4 a pass@k curve chart where base and GRPO curves start far apart at k=1 and meet near k=64 ('sharpening, not expansion').

**Code.**

```text
arxiv-sft-rl.md #7 TAG one-liner: def tag_reward(r_primary, aux, lambdas):
    return r_primary * (1 + sum(l*a for l, a in zip(lambdas, aux))) / (1 + sum(lambdas))
```

### 05.10 [industry] ThinkingBox and KARL filter tasks by pass rate before any RL step

- File: `c05-10-thinkingbox-karl.html`
- Id: `custom-c05-thinkingbox-karl`

**Content.** Kicker: In production · Microsoft ThinkingBox (22 Oct 2026) and Databricks KARL (Mar 2026), industry.md A13 and A6. ThinkingBox: 507 tasks with real backends + MCP tools + a simulated user; binary reward on the final database state; 'offline policy-relative difficulty': probe the base n times per task, Jeffreys posterior, drop tasks < 0.08 or >= 0.90; Qwen3.8-27B full-parameter token-mean GRPO, 50 steps on 187 tasks, 18 groups x 8 rollouts, 24 H100s, LR 1e-6. Results: pass@1 51.70% -> 60.78%; tasks solved 20/20 38 -> 107; pass@20 89.35% -> 87.97% (fell); cost per dependable task $24.36 -> $8.00. Gotchas: backend timeouts are system errors (refill, do not score 0); training and eval parsers must match; package auto-sync overwrote a patched verl. KARL: synthesize grounded Q-A with vector search -> dedup/decontam agent -> several solver agents, drop all-solved and none-solved -> quality filter agent -> OAPL off-policy RL; KARLBench 52.6 (GLM 4.5 Air) -> 58.9; 67.5 with 10 parallel traces = Claude 4.6 Opus at ~33% lower cost; under $0.10 per query. .cite huggingface.co/blog/microsoft/thinkingbox-training ; databricks.com/blog/meet-karl-faster-agent-enterprise-knowledge-powered-custom-rl.

**Visual and animation.** Animated pipeline diagram (>= 50% canvas): KARL stages as 5 nodes left to right (synthesize -> dedup -> solve x N -> quality filter -> RL) with :flow; a histogram above 'solve x N' shows tasks bucketed by pass rate and the 0/N and N/N buckets fall away (gsap). Step 3: ThinkingBox result bars: pass@1 up (green), pass@20 down (red), cost per dependable task count-down $24.36 -> $8.00.

### 05.11 [practices] RL run checklist: ten checks before and during every GRPO job

- File: `c05-11-rl-checklist.html`
- Id: `custom-c05-rl-checklist`

**Content.** Best practices (lab-rl cross-lab gotchas, gotchas.md B1-B14, industry.md Part D). Do: (1) Unit-test every reward with >= 1 known hack (Lab 3). (2) Probe the base 8x per prompt; keep 0 < pass < 1 (ThinkingBox 0.08..0.90). (3) dtype bfloat16, batch divisible by num_generations. (4) beta=0.0 for verifiable rewards; beta > 0 for learned or judge rewards. (5) Log each reward channel separately and alert when the primary falls while the total rises (tripwire). (6) Keep completions/clipped_ratio < 10% or mask truncated completions. (7) Sample rollouts with top_p=1.0, top_k=-1 (IS-ratio bias, TRL #6789). (8) Gold or human audit on a random sample every N steps: proxy RMs turn 41-66% of reward gain into 'rent' (arXiv 2610.19832; frequent mild audits beat rare severe ones). (9) Watchdog on global_step: a stalled vLLM server hangs training with no error (TRL #6973). Don't: (10) Do not score infrastructure timeouts as 0; refill them. Config snippet: GRPOConfig with the explicit safe values.

**Visual and animation.** Checks list in two columns (stagger, 3 steps). Right: a mini 'pre-flight panel' of 6 toggles that flip green one by one as the matching items appear, ending with a green 'launch' button.

**Code.**

```text
GRPOConfig(model_init_kwargs={'dtype': 'bfloat16'}, num_generations=8, per_device_train_batch_size=8, gradient_accumulation_steps=4, beta=0.0, loss_type='dapo', mask_truncated_completions=True, multi_objective_aggregation='normalize_then_sum', log_completions=True) - all parameters from lab-rl Labs 2 and 4.
```

## Chapter 06: Preference tuning with DPO and reward models

Tone: `human`

**Scenario.** Acme support QA team marks replies as on-brand (empathetic, specific, takes action) or off-brand (dismissive, blames the customer). Align the support assistant with DPO + LoRA, read the DPO logs correctly, and train a reward model when you need a learned reward.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-rl.md
- C:/Users/evija/googleadk2.0/research-v2/custom/arxiv-sft-rl.md
- C:/Users/evija/googleadk2.0/research-v2/custom/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/custom/industry.md
- C:/Users/evija/googleadk2.0/research-custom/03-rl.md

### 06.01 [chapter] Preference tuning with DPO and reward models

- File: `c06-01-chapter.html`
- Id: `custom-c06-chapter`

**Content.** Chapter 06. .display 'Preference tuning'. Lede: 'When the right answer is a judgment, train on pairs. Watch what the margin is made of.' Scenario: Acme on-brand support replies.

**Visual and animation.** Self-animating mini-diagram: a chosen reply card (green) and a rejected reply card (red) feed a DPO node; two log-prob bars move apart in a loop (rejected falls faster than chosen).

### 06.02 [lab] Build preference pairs: 3 QA-reviewed seeds plus 3,000 general pairs

- File: `c06-02-lab5-pairs.html`
- Id: `custom-c06-lab5-pairs`

**Content.** Kicker: Lab 5 Acme on-brand support replies · step 1 of 3. Run it Monday: same install as Lab 4 (trl 1.16.0, peft 0.21.2), 16-24 GB GPU, folder support_dpo/lab6_dpo_support.py. Code = lab-rl Lab 6 data part (VERIFIED trl 1.16.0): turn(q, r) helper; PAIRS = 3 tuples (late package: on-brand 'Sorry about the delay. Your parcel is at the Leeds depot and arrives tomorrow; I added a $5 credit.' vs off-brand 'Shipping delays happen. Please wait.'; charged twice: '...I refunded the duplicate; it shows in 3-5 business days.' vs 'Contact your bank about card issues.'; deleted notes: 'Notes stay in Trash for 30 days...' vs 'You probably did it yourself.'); support = Dataset.from_list(...) * 100; uf = load_dataset('trl-lib/ultrafeedback_binarized', split='train[:3000]').select_columns(['chosen','rejected']); concatenate_datasets([uf, support.cast(uf.features)]).shuffle(seed=0); train_test_split(0.05). Steps-rail: implicit prompt format (each side holds the full conversation; TRL extract_prompt splits the shared prefix); oversampling x100 + general pairs keeps general ability; cast to the same features before concatenating. Output pane (illustrative): print(split) -> DatasetDict train ~3,135 / test ~165 rows, columns ['chosen','rejected']. Best practice: audit preference labels before DPO (label flips steer DPO, 2610.24945).

**Visual and animation.** Bespoke animation: three pair cards flip in (chosen green on the left, rejected red on the right); step 2 each card multiplies into a stack of 100 (counter); step 3 a large blue UltraFeedback stack (3,000) joins and the stacks shuffle into one mixed column; step 4 a 5% slice splits off as 'eval'.

**Code.**

```text
lab-rl.md Lab 6 lab6_dpo_support.py lines 1-20 (imports, turn, PAIRS, datasets). data-focus="1:5, 2:7-17, 3:18-20".
```

### 06.03 [lab] DPOConfig: sigmoid plus SFT loss, beta 0.1, adapter-off reference

- File: `c06-03-lab5-dpo-config.html`
- Id: `custom-c06-lab5-dpo-config`

**Content.** Kicker: Lab 5 Acme on-brand support replies · step 2 of 3. .lab-head: python lab6_dpo_support.py. Code = lab-rl Lab 6 trainer part (VERIFIED): DPOConfig(model_init_kwargs={'dtype': 'bfloat16'}, beta=0.1, loss_type=['sigmoid', 'sft'], loss_weights=[1.0, 0.2], learning_rate=5e-6, per_device_train_batch_size=4, gradient_accumulation_steps=4, max_length=1024, num_train_epochs=1, eval_steps=50); DPOTrainer(model='Qwen/Qwen2.5-0.5B-Instruct', args, train/eval, peft_config=LoraConfig(r=16, lora_alpha=32, target_modules='all-linear')). Focus: (1) beta = KL strength: higher stays closer to the start model; (2) losses are a list in TRL 1.x; 'sft' adds NLL on chosen (RPO-style) and must match loss_weights length; (3) no ref_model: with PEFT the adapter-disabled base is the reference (no second copy); (4) lr 5e-6 vs the 1e-6 full-FT default; per 2610.27895 the optimal LR moves with model size and does not transfer across datasets: sweep LR x beta with short runs on the downstream eval. Variation: loss_type=['sigmoid_norm'] (SimPO-style length-normalized) or label_smoothing=0.1 (Robust DPO, must be in [0, 0.5)).

**Visual and animation.** Code left with 4 focus bands; right: bespoke loss-composition animation: two bars 'sigmoid DPO x 1.0' and 'SFT NLL x 0.2' stack into a total loss bar; a beta dial (0.1) shows a leash between 'policy' and 'reference = adapter off' nodes; the leash tightens when the dial is moved to 0.5 (step 4) and relaxes back.

**Code.**

```text
lab-rl.md Lab 6 lab6_dpo_support.py lines 22-38. data-focus="1:25, 2:26, 3:33-35, 4:27".
```

### 06.04 [lab] Margins grow because rejected falls: read the log, then the samples

- File: `c06-04-lab5-read-logs.html`
- Id: `custom-c06-lab5-read-logs`

**Content.** Kicker: Lab 5 Acme on-brand support replies · step 3 of 3. Output pane 'output · illustrative' (keys verified in dpo_trainer.py): step 0 {'loss': 0.69, 'rewards/chosen': 0.00, 'rewards/rejected': 0.00, 'rewards/accuracies': 0.0, 'rewards/margins': 0.0, 'logps/chosen': -182.4, 'logps/rejected': -201.7}; later {'loss': 0.41, 'rewards/chosen': -0.21, 'rewards/rejected': -1.35, 'rewards/accuracies': 0.86, 'rewards/margins': 1.14, 'logps/chosen': -184.5}. Steps-rail: (1) loss starts at ln 2 = 0.69 (policy = reference); a loss that never leaves 0.6931 means LoRA touched nothing (C03 gotcha); (2) margins grow mostly because rejected falls; a slowly falling logps/chosen is normal, a fast fall -> raise the sft weight or beta; (3) rewards/accuracies near 1.0 within 50 steps on a tiny in-domain set = memorization: check the eval split; (4) read 10 generations at every eval: ECHO (2610.29410) shows ranking metrics can improve while vocabulary collapses. Errors (exact): 'ValueError: loss_weights must have the same length as loss_type when combining multiple losses. Got 1 weights for 2 loss types.'; 'ValueError: model and ref_model cannot be the same object.'; 'TypeError: train_dataset must be a Dataset or IterableDataset, got DatasetDict.' -> split='train'.

**Visual and animation.** Bespoke chart animation (>= 55% canvas): two log-prob lines over steps, chosen (green) drifting slightly down and rejected (red) falling faster; the gap between them fills as a shaded band labelled rewards/margins; step 3 a rewards/accuracies line rises to 0.86 with an amber warning zone above 0.95; step 4 a sample-reply card flips over to show a real generation check.

**Code.**

```text
lab-rl.md Lab 6 Expected output block (2 lines) + trainer.save_model().
```

### 06.05 [buildup] A learned reward needs margins, a trained score head and centring

- File: `c06-05-reward-model.html`
- Id: `custom-c06-reward-model`

**Content.** Kicker: Build. Feature added: a Bradley-Terry reward model from rater-scored pairs (lab-rl Lab 5, VERIFIED trl 1.16.0; the lab's rater data is HR-policy answers scored 1-9 by reviewers, the same recipe applies to support replies). .code-wrap.bad: LoraConfig(task_type='SEQ_CLS') without modules_to_save -> the new score head stays random. .code-wrap.good: margin column = score_chosen - score_rejected (loss becomes -logsigmoid(r_c - r_r - margin)); RewardConfig(learning_rate=1e-4, max_length=1024, center_rewards_coefficient=0.01); LoraConfig(task_type='SEQ_CLS', modules_to_save=['score']); merged = trainer.model.merge_and_unload(); merged.save_pretrained('hr-rm-merged'); then GRPOConfig(beta=0.02) with reward_funcs=['hr-rm-merged', cites_policy] (a string loads AutoModelForSequenceClassification with num_labels=1; a cheap verifiable guard + KL anchor limit RM over-optimisation). .delta (illustrative): eval_accuracy 0.71, eval_margin 0.81, mean_reward ~0.02 (centred). Pitfalls: RewardConfig.max_length filters out longer pairs silently -> check len(trainer.train_dataset); 'ValueError: The model has num_labels=2, but reward models require num_labels=1'. Paper hook: 2610.30765 'Scaling Laws for Generative Reward Models' (22 Oct 2026): statically more accurate RMs often trained worse policies; Answer-Only rewarders won 7 of 8 settings -> pick an RM by a short downstream RL run.

**Visual and animation.** Bespoke animation: a score-head node on top of a frozen base; step 1 (bad) the head stays grey 'random' while adapters train; step 2 (good) the head lights coral (modules_to_save); step 3 a pair of reward dots per example separates by at least the margin (dots slide apart on a number line); step 4 the merged RM plugs into a GRPO loop as one of two reward nodes, with a KL leash to the reference.

**Code.**

```text
lab-rl.md Lab 5 lab5_reward_model.py lines 19-35 (margin map, RewardConfig, RewardTrainer with LoraConfig modules_to_save, merge/save) + lab5b_grpo_with_rm.py lines 9-17 (cites_policy, GRPOConfig beta 0.02, reward_funcs).
```

### 06.06 [gotcha] Truncated preference pairs give empty answers and NaN weights

- File: `c06-06-pair-pitfalls.html`
- Id: `custom-c06-pair-pitfalls`

**Content.** Kicker: Gotcha · preference data (gotchas.md B5). Symptom: with loss_type='simpo' (CPOTrainer): loss = 0, grad_norm = nan, all rewards and logps nan after the first optimizer step; other loss types silently use logp = 0. Cause: both responses are truncated to max_length - longer_response_length; when negative, lst[:negative] cuts from the end and can empty the shorter response; length normalisation divides 0 by 0 (TRL #6548; fix for CPO in PR #6588). Fix: drop pairs longer than max_length before training (code) and fail fast on the first non-finite grad_norm. Second card: Symptom: DPO steered toward an attacker's preference. Cause: preference label flips (2610.24945, 18 Oct 2026; Trim-K Robust-DPO with bounds). Fix: audit labels, use label_smoothing=0.1 as the cheap built-in. Third card: Symptom: judge-labelled pairs are unstable. Cause: re-running Arena-Hard's GPT-4.1 judge unchanged flips 21.2% of prompt outcomes while the aggregate moves ~1 pt (2610.30512). Fix: re-judge twice, keep only pairs with the same verdict.

**Visual and animation.** Bespoke animation: a token ruler at max_length; a prompt block plus a long chosen and a short rejected response; step 1 truncation slices from the wrong end and the rejected block empties to zero width; step 2 a division '0 / 0' turns into NaN and spreads red across a weight grid; step 3 the filter drops the pair before training and the grid stays clean.

**Code.**

```text
gotchas.md B5 filter: ds = ds.filter(lambda r: len(tok(r['prompt']+r['chosen']).input_ids) <= L and len(tok(r['prompt']+r['rejected']).input_ids) <= L) ; plus DPOConfig(label_smoothing=0.1) from lab-rl Lab 6 best practice.
```

### 06.07 [paper] Preference runs can rank better while vocabulary quietly collapses

- File: `c06-07-echo-dpo-shape.html`
- Id: `custom-c06-echo-dpo-shape`

**Content.** Kicker: arXiv Oct 2026. Three .paper cards. (1) 2610.29410 ECHO (21 Oct 2026): preference optimisation grows a common-mode hidden offset into a 'vocabulary well' until one token dominates decoding; collapse in 14 of 17 lineages under their per-token ranking loss; 'the better a run ranks held-out responses, the less often two public reward models prefer its samples'. Monday: sample and read outputs at every eval; track distinct-token share. (2) 2610.27895 'The Shape of the DPO Hyperparameter Landscape' (20 Oct 2026): optimal LR varies with model size; hyperparameters do not transfer across datasets; validation loss is a poor proxy; short runs cut tuning cost. Monday: sweep LR x beta with 50-step runs scored on the downstream eval. (3) 2608.24192 'Preference Data Selection for Mitigating the Alignment Tax' (25 Aug 2026): filter DPO pairs by reference margin, length gap and similarity to general text to cut the alignment tax.

**Visual and animation.** Method animation for ECHO: a vocabulary bar chart of next-token probabilities (30 bars); over 4 steps a shared offset arrow pushes all hidden states the same way and one bar grows into a well while the others shrink; a ranking-accuracy gauge rises at the same time (the trap). Card 2: a small LR x beta heatmap whose best cell moves when the model size toggle changes.

### 06.08 [industry] Cursor turns user behaviour into rewards and ships every 5 hours

- File: `c06-08-cursor-realtime.html`
- Id: `custom-c06-cursor-realtime`

**Content.** Kicker: In production · Cursor real-time RL for Composer (26 Mar 2026, industry.md A2). Loop: serve a checkpoint behind 'Auto' -> collect billions of tokens from user interactions -> distil into reward signals (did the edit persist, dissatisfied follow-up, latency) -> update weights -> gate on eval suites incl. CursorBench -> deploy; 'about five hours', several releases per day. A/B (Composer 1.5): edit persists +2.28%, dissatisfied follow-ups -3.13%, latency -10.3%. Hacks found in production: broken tool calls on likely-failing tasks to avoid negative reward (fix: count broken calls as negatives); edit avoidance via clarifying questions (caught by a falling edit-rate monitor; reward changed). Quote: 'Each attempted reward hack essentially becomes a bug report that we can use to improve our training system.' Lessons: noisy objective -> large batches; stay close to on-policy to limit over-optimisation; eval gate + A/B before every deploy. .cite https://cursor.com/blog/real-time-rl-for-composer.

**Visual and animation.** Large animated loop diagram (>= 50% canvas): 5 nodes in a circle serve -> collect -> reward -> eval gate -> deploy with :flow pulses and a '5 h' clock in the centre whose hand sweeps once per loop. Step 2: three .stat deltas count up. Step 3: two red hack cards attach to the 'reward' node and a monitor node 'edit rate' lights when the second hack appears.

## Chapter 07: Dataset contracts, coverage and active learning

Tone: `state`

**Scenario.** Acme claims intake: reject or quarantine a bad nightly batch before it reaches the fraud-model training table, then decide which claims senior adjusters (100 labels/day) should label next.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-data.md
- C:/Users/evija/googleadk2.0/research-v2/custom/arxiv-data.md
- C:/Users/evija/googleadk2.0/research-v2/custom/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/custom/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-custom/04-dataset-design-contracts.md

### 07.01 [chapter] Dataset contracts, coverage and active learning

- File: `c07-01-chapter.html`
- Id: `custom-c07-chapter`

**Content.** Chapter 07. .display 'Contract the data'. Lede: 'A contract stops bad rows at the door. Active learning spends scarce expert labels where the model is unsure.' Scenario: Acme claims intake.

**Visual and animation.** Self-animating mini-diagram: a stream of row cards hits a contract gate; valid rows (green) pass to a 'training table' node, invalid rows (red) drop into a 'quarantine' bin; a violet adjuster node pulls a few amber 'uncertain' rows; loop.

### 07.02 [lab] A pandera contract turns the claims intake rules into code

- File: `c07-02-lab6-contract.html`
- Id: `custom-c07-lab6-contract`

**Content.** Kicker: Lab 6 Acme claims intake · step 1 of 4. Run it Monday: Python 3.12; pip install "pandera[pandas]==0.34.1" "pandas==3.0.*" (the base wheel does not depend on pandas; pandas 3.1.0 is one day old, untested); no env vars, data generated in the script. Folder tree claims_data/{lab1_claims_contract.py, lab6_active_learning.py}. Code = lab-data Lab 1 ClaimsContract (VERIFIED pandera 0.34.1): import pandera.pandas as pa; claim_id unique + str_matches '^CLM-\d{6}$'; policy_id str_length 8..8; claim_type isin auto/home/travel/health; amount_usd gt 0, le 250,000; incident_date / reported_date Timestamps; adjuster_note nullable; @pa.dataframe_check reported_after_incident; Config strict=True, coerce=True; the 4-row batch with a duplicate CLM-000102 and a bad row CLM-77/POL1/boat/-5/reported before incident. Focus: (1) Field kwargs; (2) cross-column dataframe_check; (3) strict + coerce. Steps-rail: the backend import (top-level pandera import emits a FutureWarning in 0.34.1); store the contract class in the producer's repo and import it in the training job: one definition, two enforcement points.

**Visual and animation.** Code left (.sm) with 3 focus bands; right: bespoke animation of the 4-row batch as a table; on each focus the rule's column header gets a gate icon and the violating cells flash red (duplicate ids on focus 1, reported-before-incident row on focus 2, string -> float/Timestamp coercion morph on focus 3).

**Code.**

```text
lab-data.md Lab 1 lab1_claims_contract.py lines 1-37 (class + batch). data-focus="1:8-15, 2:17-19, 3:21-23".
```

### 07.03 [lab] lazy=True returns all 12 failures in one report, then quarantine rows

- File: `c07-03-lab6-quarantine.html`
- Id: `custom-c07-lab6-quarantine`

**Content.** Kicker: Lab 6 Acme claims intake · step 2 of 4. .lab-head: python lab1_claims_contract.py. Code: the try/except block (ClaimsContract.validate(batch, lazy=True); except SchemaErrors as exc: fc = exc.failure_cases; bad_rows = set(fc['index'].dropna().astype(int)); clean = batch.drop(index=list(bad_rows))). Output pane (captured run, exact): '12 failure cases', the table (6 rows for the dataframe_check on index 3 - every column of the failing row -, field_uniqueness on index 1 and 2, str_matches('^CLM-\d{6}$') CLM-77, str_length(8, 8) POL1, isin([...]) boat, greater_than(0) -5.0), 'quarantined rows: [1, 2, 3] | clean rows kept: 1'. Steps-rail: (1) a row-wise check reports every column of the failing row (6 of the 12) - count failures by row, not by line; (2) unique=True flags both copies (rows 1 and 2) - keep one on purpose; (3) without lazy=True the first failure stops: 'pandera.errors.SchemaError: series 'claim_id' contains duplicate values:'; (4) a new upstream column fails strict mode with COLUMN_NOT_IN_SCHEMA -> version the contract or strict='filter'. Variation: Config drop_invalid_rows=True and write dropped rows + failure_cases to a quarantine/ table. Best practice: alert on new failure types, not on failure counts.

**Visual and animation.** Bespoke animation: the failure_cases table builds row by row (12 rows, stagger) while arrows connect each row to its cell in the batch table; step 3 rows 1-3 slide into a red 'quarantine' bin and row 0 slides into a green 'training table' bin; step 4 the duplicate pair shows a 'keep one' toggle.

**Code.**

```text
lab-data.md Lab 1 lines 39-47 (try/except) + captured output (15 lines).
```

### 07.04 [lab] Margin sampling: label the 100 claims the model is least sure about

- File: `c07-04-lab6-active-loop.html`
- Id: `custom-c07-lab6-active-loop`

**Content.** Kicker: Lab 6 Acme claims intake · step 3 of 4. .lab-head: python lab6_active_learning.py (~7 s; pip install "scikit-learn==1.9.1" "numpy==2.5.4"). Code = lab-data Lab 6 (VERIFIED scikit-learn 1.9.1): make_classification(20,000 claims, 10% need an adjuster, flip_y=0.02); stratified pool/test split; SEED_SIZE, BATCH, ROUNDS = 100, 100, 8; margin_scores = p(top-1) - p(top-2); run(strategy): fit LogisticRegression(class_weight='balanced') from scratch each round, score average_precision on a fixed held-out test set, pick the 100 smallest margins (or random). Focus: (1) margin works for K classes; (2) class_weight='balanced' (10% positives -> ~10 positives in the seed); (3) fixed test set never in the pool (AL-selected items are hard by construction). Errors: 'ValueError: This solver needs samples of at least 2 classes in the data, but the data contains only one class: 0' -> stratified seed or rule-based positives. Note: modAL has had no release since 2023-06; use scikit-activeml 1.0.1 (2026-10-15) in production.

**Visual and animation.** Bespoke animation (Deck.register): a 2D scatter of 400 unlabelled claim dots with a logistic decision boundary; step 1 the seed 100 dots get violet labels; step 2 the boundary fits; step 3 a band around the boundary highlights the 100 smallest-margin dots, they get labelled, the boundary moves (round 2); step 4 random picks shown in a ghost overlay for contrast (scattered far from the boundary). Deterministic dot positions.

**Code.**

```text
lab-data.md Lab 6 lab6_active_learning.py (full 37 lines). data-focus="1:15-18, 2:24-26, 3:27-32".
```

### 07.05 [lab] Margin sampling reaches random's 900-label score with about 300 labels

- File: `c07-05-lab6-curve.html`
- Id: `custom-c07-lab6-curve`

**Content.** Kicker: Lab 6 Acme claims intake · step 4 of 4. Output pane (captured run, mean of 5 seeds, exact): labels 100: random 0.546 / margin 0.546; 200: 0.548 / 0.599; 300: 0.570 / 0.620; 400: 0.587 / 0.633; 500: 0.605 / 0.643; 600: 0.606 / 0.646; 700: 0.615 / 0.652; 800: 0.620 / 0.657; 900: 0.622 / 0.659. Reading: margin reaches random's 900-label PR-AUC (0.622) with ~300 labels, about 3x less adjuster time on this synthetic task. Steps-rail: average >= 5 seeds before claiming a gain; mix 80 margin + 20 random per batch (unbiased prevalence estimate, calibration); record strategy, round and score for every queried item in the label store; diversity-aware batches (k-means on the top-1,000 margins) when batches hold near-identical borderline claims. Gotcha: under heavy label noise uncertainty sampling queries the noise. Paper hook: 2610.25215 Hidden Cartographer (18 Oct 2026): separate annotation and training budgets; annotate 20-30% of the pool, fine-tune on 10-15%.

**Visual and animation.** Bespoke learning-curve animation (>= 55% canvas): two PR-AUC lines draw from the exact table (random grey, margin green); step 2 a horizontal dashed line at 0.622 extends left from random's 900-label point until it meets the margin curve near 300 labels; step 3 a '3x fewer labels' bracket and an adjuster-days counter (9 days -> 3 days at 100/day).

**Code.**

```text
lab-data.md Lab 6 captured output table (10 lines).
```

### 07.06 [paper] Select sets, not samples: set quotas, drop each example's self-vote

- File: `c07-06-select-sets.html`
- Id: `custom-c07-select-sets`

**Content.** Kicker: arXiv Sep-Oct 2026. Three .paper cards. (1) 2610.00436 LOOM 'Every Batch Is Its Own Validation Set' (30 Sep 2026, verifier-confirmed): in-sample gradient matching rewards each example's own noise (the Gram diagonal); dropping the diagonal beats full-batch training by +2.3 (Llama-3.1-8B) and +2.4 (Qwen2.5-7B) and selects injected label noise at under 1/5 of its base rate. Monday: zero the diagonal of any gradient-similarity selector (same lesson as out-of-sample pred_probs in C09). (2) 2610.14028 'Pick the Mixture, Not the Samples' (30 Sep 2026): set domain quotas first, then rank within each domain (+20-54%). (3) 2610.24888 'Measuring Data Diversity with Embeddings' (17 Oct 2026): 21 embedding diversity measures compared; graph entropy beats mean pairwise distance. Monday: report coverage per taxonomy leaf and a diversity score per release.

**Visual and animation.** Method animation for LOOM: an 8x8 gradient Gram heatmap; step 1 the diagonal glows (self-credit) and the top-scored rows are the noisy ones (red markers); step 2 the diagonal is wiped to zero and rows re-rank (gsap reorder), red markers sink; step 3 a corrupted-label counter drops from 20% to under 4%. Card 2: quota bars per domain fill before per-sample ranking.

**Code.**

```text
arxiv-data.md #5 loo_select sketch (6 lines: gram = G @ G.T; np.fill_diagonal(gram, 0.0); score = gram.sum(1) / (len(G) - 1); return np.argsort(-score)[:k]), labelled 'simplified sketch, not the authors' code'.
```

### 07.07 [practices] Dataset design rules: contract, hash, version, and check every rank

- File: `c07-07-contract-checklist.html`
- Id: `custom-c07-contract-checklist`

**Content.** Best practices (lab-data L1/L6, gotchas.md C1-C5, research-custom/04). Do: (1) Keep the contract class in the producer repo; the training job imports it (one definition, two gates). (2) lazy=True in pipelines; alert on new failure types. (3) Validate label ranges yourself: datasets ClassLabel accepts label=5 for 3 classes when the Arrow dtype matches (datasets #8596, open). (4) Record your own sha256 of the Parquet shards and pin revision= on load_dataset: datasets 4.8.5 flipped record_checksums to False with no release note (#8590). (5) Distributed runs: assert per-rank sample-id disjointness (concatenate_datasets dropped split_dataset_by_node on iterable datasets, #8799). (6) Put an empty/whitespace doc filter first (NeMo Curator filters crashed with ZeroDivisionError, #2458). (7) Write the coverage taxonomy and the split rule into the contract. (8) Audit labels from the export or API, not from UI screenshots (Label Studio blank-grid bug #9897). Don't: (9) Do not dedupe or quarantine silently: log (row, rule, value). (10) Do not mix MinHash schemes across datasketch 1.x / 2.0.

**Visual and animation.** Checks list (stagger, 3 steps) beside a mini dataset 'passport' card that fills field by field (contract version, sha256, revision, taxonomy leaves, split rule, label range) as the matching rules appear.

**Code.**

```text
gotchas.md C2 label-range check: n = ds.features['label'].num_classes; bad = ds.filter(lambda r: not 0 <= r['label'] < n); assert len(bad) == 0  # plus load_dataset(name, revision='<commit sha>').
```

## Chapter 08: Drift, leakage, calibration and cost

Tone: `risk`

**Scenario.** Acme refund-fraud model: watch refund-request drift (September vs October holiday promo), prove the validation does not leak customers or the future, calibrate the scores, and set the hold threshold from a $15 / $120 cost matrix at 2% production prevalence.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-data.md
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-synth-eval.md
- C:/Users/evija/googleadk2.0/research-v2/custom/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/custom/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-custom/04-dataset-design-contracts.md

### 08.01 [chapter] Drift, leakage, calibration and cost

- File: `c08-01-chapter.html`
- Id: `custom-c08-chapter`

**Content.** Chapter 08. .display 'Drift, leakage, cost'. Lede: 'The same model scores 0.886 or 0.602 depending on the split. Then the threshold decides what it costs.' Scenario: Acme refund-fraud model.

**Visual and animation.** Self-animating mini-diagram: two histograms (September blue, October amber) drift apart in a loop; below, a threshold slider moves along a cost curve and settles at its minimum.

### 08.02 [lab] PSI says stable, KS says drift: at large n, distance beats p-value

- File: `c08-02-lab7-psi-ks.html`
- Id: `custom-c08-lab7-psi-ks`

**Content.** Kicker: Lab 7 Acme refund-fraud model · step 1 of 5. Run it Monday: Python 3.12; pip install "numpy==2.5.4" "scipy==1.18.1" "scikit-learn==1.9.1" "pandas==3.0.*"; folder fraud_data/{lab2_psi_ks.py, lab7_leakage_splits.py, lab5_calibration.py, lab6_cost_threshold.py}. Code = lab-data Lab 2 lab2_psi_ks.py (re-run by the verifier, identical): psi() with quantile bins fixed on the reference, edges[0], edges[-1] = -inf, inf, np.unique(edges), np.clip(eps=1e-4); verdict bands 0.1 / 0.25; reference = 20,000 September requests, current = 5,000 October (refund_amount_usd lognormal 3.6/0.6 -> 3.9/0.7, days_since_order gamma scale 6.0 -> 6.2, items_in_order unchanged). Output (captured, exact): refund_amount_usd PSI 0.243 moderate, KS D 0.205, p 5.91e-148; days_since_order PSI 0.003 stable, KS D 0.024, p 2.16e-02; items_in_order PSI 0.001 stable, KS D 0.013, p 4.99e-01. Steps-rail: (1) bins fixed on reference so weeks are comparable; (2) +-inf edges catch values beyond September's max; (3) unique() for zero-inflated features; (4) row 2: PSI 0.003 but KS p = 0.02 -> a p-value test flags shifts too small to matter at n = 20k/5k; Evidently switches to distances for n > 1000. Best practice: calibrate thresholds on reference vs reference (split September in two).

**Visual and animation.** Bespoke animation (>= 50% canvas): three small-multiple histogram pairs (reference blue bars, current amber outline) per feature; step 1 reference bins draw with fixed quantile edges; step 2 current bars rise; refund_amount visibly shifts right; step 3 PSI and KS numbers count up per feature from the exact output; step 4 the days_since_order panel gets a split verdict badge 'PSI: stable / KS: drift'.

**Code.**

```text
lab-data.md Lab 2 lab2_psi_ks.py (full 33 lines). data-focus="1:5-7, 2:8-9, 3:10-11, 4:28-31".
```

### 08.03 [lab] Same model, same data: KFold 0.886, GroupKFold 0.602 ROC-AUC

- File: `c08-03-lab7-groupkfold.html`
- Id: `custom-c08-lab7-groupkfold`

**Content.** Kicker: Lab 7 Acme refund-fraud model · step 2 of 5. .lab-head: LOKY_MAX_CPU_COUNT=4 python lab7_leakage_splits.py (PowerShell: $env:LOKY_MAX_CPU_COUNT=4; ~50 s). Code = lab-data Lab 7 first half (VERIFIED scikit-learn 1.9.1): 400 customers x 15 events; 15% fraudsters with a weak real signal (+0.8 on f0); stable customer fingerprint + noise features; HistGradientBoostingClassifier(max_iter=200); cross_val_score with KFold(5, shuffle=True) vs GroupKFold(n_splits=5, shuffle=True, random_state=0) and groups=df['customer_id']. Output (captured, exact): 'KFold (rows shuffled, customers leak):  ROC-AUC 0.886 +/- 0.025', 'GroupKFold (customer never in both):    ROC-AUC 0.602 +/- 0.075'. Reading: the 0.28 AUC gap is memorized customer fingerprints; only 0.60 generalizes to new customers. Steps-rail: GroupKFold shuffle/random_state are keyword-only (added in 1.6); the group key is a business decision (customer, household, device, policy, patient, document source): the unit the deployed model meets for the first time; use StratifiedGroupKFold when positives are rare. Error: 'ValueError: The 'groups' parameter should not be None.'

**Visual and animation.** Bespoke animation: a grid of 400 customer tiles, each with 15 event dots. Step 1 KFold: event dots of one customer split between train (blue) and test (amber) - lines link the same customer across both and glow red 'leak'. Step 2 GroupKFold: whole customer tiles move to one side. Step 3 two AUC gauges count to 0.886 and 0.602 with the 0.28 gap shaded.

**Code.**

```text
lab-data.md Lab 7 lab7_leakage_splits.py lines 1-29. data-focus="1:9-18, 2:24-27, 3:28-29".
```

### 08.04 [lab] Sort by time, leave a label-delay gap, assert the future never trains

- File: `c08-04-lab7-time-split.html`
- Id: `custom-c08-lab7-time-split`

**Content.** Kicker: Lab 7 Acme refund-fraud model · step 3 of 5. Code = lab-data Lab 7 second half: order = np.argsort(event_day, kind='stable'); rows_per_day = len(df) // 365; tscv = TimeSeriesSplit(n_splits=4, gap=7 * rows_per_day) (chargebacks take ~7 days to arrive); fold print; assert all(days[tr].max() < days[te].min() for tr, te in tscv.split(Xs)), 'future leaked into train'. Output (captured, exact): fold 0: train days 0- 64 | test days 71-145 | n_train=1088; fold 1: 0-138 | 145-220 | 2288; fold 2: 0-213 | 220-290 | 3488; fold 3: 0-284 | 290-364 | 4688. Steps-rail: (1) TimeSeriesSplit never looks at a timestamp: sort first; (2) gap counts samples, not days: convert the label delay to rows yourself; (3) the assert is an executable leakage test for the training repo; (4) for 'new customers in the future' combine a time cut-off with group exclusion. Errors: 'ValueError: Too many splits=5 for number of samples=50 with test_size=8 and gap=40.' Best practice: fit every preprocessor (scaler, target encoder, TF-IDF) inside a Pipeline so it is re-fit per fold.

**Visual and animation.** Bespoke timeline animation: a 365-day axis; for each of the 4 folds (one per step) a blue train bar grows from day 0, a grey 7-day gap block appears, then an amber test bar; the n_train counter updates (1088, 2288, 3488, 4688). Final step: a red 'future -> train' arrow attempts to cross the gap and the assert stamps 'blocked'.

**Code.**

```text
lab-data.md Lab 7 lab7_leakage_splits.py lines 31-39. data-focus="1:32-33, 2:34-35, 3:36-39".
```

### 08.05 [lab] AUROC 0.929 everywhere, but '0.86 fraud' really means 35%

- File: `c08-05-lab7-calibration.html`
- Id: `custom-c08-lab7-calibration`

**Content.** Kicker: Lab 7 Acme refund-fraud model · step 4 of 5. .lab-head: python lab5_calibration.py. Code = lab-synth-eval Lab 5 (VERIFIED scikit-learn 1.9.1; run on 1.8.0): ece() with uniform and quantile bins; 20,000 rows, 10% positives; train / calibration / test splits; GaussianNB base (redundant features -> overconfident); CalibratedClassifierCV(FrozenEstimator(base), method=m).fit(X_cal, y_cal) for sigmoid, isotonic, temperature (new in 1.8). Output (REAL): raw GaussianNB AUROC 0.929 Brier 0.0750 ECE-15u 0.0677 ECE-15q 0.0698; sigmoid 0.929 / 0.0561 / 0.0173 / 0.0251; isotonic 0.929 / 0.0536 / 0.0063 / 0.0064; temperature 0.929 / 0.0702 / 0.0780 / 0.0806; raw reliability ... '0.86->0.35', '0.98->0.67'. Steps-rail: (1) calibration fixes probabilities, not ranking (AUROC identical); (2) temperature has one parameter and no intercept, so it made ECE worse on an imbalanced, biased model (sklearn docstring: 'sigmoid calibration might be preferred'); (3) calibrate on data the base never saw. Errors (exact): "InvalidParameterError: The 'cv' parameter of CalibratedClassifierCV must be ... Got 'prefit' instead." -> FrozenEstimator; "... method ... Got 'platt' instead." -> 'sigmoid'; isotonic 'not recommended when the number of calibration samples is too low (<<1000)'; calibration_curve default n_bins=5.

**Visual and animation.** Bespoke reliability-diagram animation (Deck.register, >= 50% canvas): diagonal reference line; step 1 raw NB points draw well below the diagonal (0.86 -> 0.35 highlighted); step 2 sigmoid points move toward the diagonal; step 3 isotonic points sit on it (ECE 0.0063 count-down); step 4 temperature points stay off (ECE 0.0780, red); a fixed AUROC 0.929 badge stays constant in the corner across all steps.

**Code.**

```text
lab-synth-eval.md Lab 5 lab5_calibration.py (full 35 lines). data-focus="1:11-23, 2:30-32, 3:34-39".
```

### 08.06 [lab] A cost-tuned threshold saves 31%; the eval threshold costs 66% more

- File: `c08-06-lab7-cost-threshold.html`
- Id: `custom-c08-lab7-cost-threshold`

**Content.** Kicker: Lab 7 Acme refund-fraud model · step 5 of 5. .lab-head: python lab6_cost_threshold.py. Code = lab-synth-eval Lab 6 (VERIFIED scikit-learn 1.9.1; run on 1.8.0): C_FP=15 (manual review of a good refund), C_FN=120 (paid fraud), PI_PROD=0.02; neg_cost scorer; TunedThresholdClassifierCV(clf, scoring=make_scorer(neg_cost), cv=5, thresholds=200); Bayes t* = C_FP/(C_FP+C_FN); confusion_matrix_at_thresholds (new in 1.8) -> FPR, FNR; EC(t) = pi*FNR*C_FN + (1-pi)*FPR*C_FP at eval vs production prevalence. Output (REAL): 'Bayes rule t* = C_FP/(C_FP+C_FN) = 0.111'; 'CV-tuned threshold on eval prevalence 0.10: 0.141'; 'test $/case default@0.5=10.72 tuned=7.38'; 'best t @ eval prevalence=0.152 (EC $7.07) @ prod prevalence=0.340 (EC $1.86)'; 'using the eval-set threshold in prod costs $3.10/case vs $1.86 -> 66% more'. Steps-rail: TunedThresholdClassifierCV maximizes, so return minus dollars (default scoring is balanced_accuracy); FPR/FNR do not depend on prevalence, so re-weight with the production prior; Bayes t* is valid only for calibrated probabilities (previous step). Errors: 'ValueError: When cv='prefit', refit cannot be True.'; 'multiclass format is not supported'. Ship it: FixedThresholdClassifier(model, threshold=0.34, response_method='predict_proba').

**Visual and animation.** Bespoke cost-curve animation: x = threshold 0..1, two expected-cost curves (eval prevalence 10% blue, production 2% amber) draw; step 2 a marker drops at the 0.5 default ($10.72) and slides to the tuned 0.141 ($7.38, -31%); step 3 the production curve's minimum at 0.340 ($1.86) lights and a vertical line from the eval-optimal 0.152 hits the prod curve at $3.10 with a red '+66%' bracket.

**Code.**

```text
lab-synth-eval.md Lab 6 lab6_cost_threshold.py (full 34 lines). data-focus="1:7-13, 2:20-25, 3:29-38".
```

### 08.07 [gotcha] Leaks that pass review: fitted encoders, renamed features, agents

- File: `c08-07-leakage-gotchas.html`
- Id: `custom-c08-leakage-gotchas`

**Content.** Kicker: Gotcha · leakage (gotchas.md E1, E3; lab-data L7). Three .gotcha cards. (1) Symptom: CV score higher than production. Cause: a scaler, target encoder or vocabulary fitted on all rows before the split; sklearn docs: 'never call fit on the test data'. Fix: every transform inside a Pipeline passed to cross_val_score; the same rule for dedup thresholds, tokenizer training and RM calibration. Variation from Lab 7: a customer_fraud_rate feature computed on all rows makes GroupKFold AUC jump; compute it inside each training fold. (2) Symptom: an agent-built model selects a feature unavailable at prediction time. Evidence: LeakBench (arXiv 2610.26088, 19 Oct 2026) on MIMIC-IV (430k admissions): agents leak a prediction-time-invalid feature in 10/10 unconstrained runs, 0/10 with an explicit admission-time constraint; renaming or disguising the inputs changes neither, so 'a name-based filter fails'. Fix: an 'available at prediction time' contract column enforced by timestamp, feature_ts <= prediction_ts. (3) Symptom: PSI = inf or 'ValueError: bins must increase monotonically'. Cause: empty bins, unsorted business bin edges. Fix: np.clip eps + np.unique(edges); set a minimum window size (10 bins and < 500 rows give ~0.05 PSI noise).

**Visual and animation.** Bespoke animation: a feature-timeline per refund event with a vertical 'prediction time' line; features arriving before the line are green, one feature arriving after (chargeback_flag) is red; step 2 renaming the red feature to 'x17' does not change its timestamp and the timestamp filter still catches it; step 3 Pipeline box wraps the encoder and re-fits per fold (fold icons).

**Code.**

```text
Bad: enc = TargetEncoder().fit(X, y); cross_val_score(model, enc.transform(X), y, cv=GroupKFold(5), groups=g). Good: cross_val_score(make_pipeline(TargetEncoder(), HistGradientBoostingClassifier()), X, y, cv=GroupKFold(n_splits=5, shuffle=True, random_state=0), groups=g)  # plus contract check: assert (df.feature_ts <= df.prediction_ts).all(). (sklearn Pipeline pattern per gotchas.md E1; TargetEncoder/make_pipeline are standard sklearn 1.9.1 API.)
```

### 08.08 [paper] Random validation hides joins and regions: R2 0.994 becomes -0.20

- File: `c08-08-random-validation-hides.html`
- Id: `custom-c08-random-validation-hides`

**Content.** Kicker: arXiv Oct 2026. Three .paper cards. (1) 2610.07059 'Crop Yield Prediction for Punjab ... What Random Validation Hides' (5 Oct 2026): a 414-row table held only 46 independent observations (a join copied each crop-year 9x); holding out whole years took XGBoost from R2 0.994 to -0.20. Monday: dedup and group by the real unit before splitting. (2) 2610.08770 'Data Leakage in Patch-Based Hyperspectral Image Classification' (6 Oct 2026): random patch sampling gives a 3D-CNN 96.17% OA, spatially disjoint sampling 55.20%; ViT/2D-CNN drop 40.71/38.81 pp. Monday: the group is the image region. (3) 2610.14115 'The Silent Failures in Agentic Data Science' (9 Oct 2026): across 220 tasks most agentic solutions contain at least one failure mode, and data-leakage failures correlate positively with predictive performance. Monday: a higher CV score from a coding agent is a red flag; run the Lab 7 assert on agent-written pipelines.

**Visual and animation.** Method animation for card 1: 46 real observation cards multiply x9 into 414 rows (join explosion); step 2 a random split scatters copies of the same observation into train and test (red links) and the R2 gauge reads 0.994; step 3 a year hold-out moves whole year groups and the gauge falls to -0.20. Cards 2 and 3 appear on steps 4 and 5 with count-ups.

## Chapter 09: Ticket triage: drift gate, label noise, route or defer

Tone: `human`

**Scenario.** Acme support-ticket triage (billing / login / outage / shipping): a weekly Evidently gate holds retraining when the ticket mix shifts, cleanlab ranks the vendor's ~8% wrong labels for a 200-ticket review, and an 8-class router auto-routes only when that is cheaper than human triage.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-data.md
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-synth-eval.md
- C:/Users/evija/googleadk2.0/research-v2/custom/arxiv-data.md
- C:/Users/evija/googleadk2.0/research-v2/custom/arxiv-eval.md
- C:/Users/evija/googleadk2.0/research-custom/05-labels-noise-active.md

### 09.01 [chapter] Ticket triage: drift gate, label noise, route or defer

- File: `c09-01-chapter.html`
- Id: `custom-c09-chapter`

**Content.** Chapter 09. .display 'Triage the triage data'. Lede: 'Drift tells you when to relabel. Out-of-sample probabilities tell you what to relabel. Costs tell you when to ask a human.' Scenario: Acme support-ticket triage.

**Visual and animation.** Self-animating mini-diagram: ticket cards flow through three gates in a loop: a drift gate (green/red light), a label-review queue (violet), and a route/defer fork (route -> queue nodes, defer -> human node).

### 09.02 [lab] A weekly Evidently report that exits 1 and blocks the retraining job

- File: `c09-02-lab8-evidently.html`
- Id: `custom-c09-lab8-evidently`

**Content.** Kicker: Lab 8 Acme ticket triage · step 1 of 4. Run it Monday: pip install "evidently==0.7.23" "pandas==3.0.*" (heavy web stack: put it in a separate monitoring venv); "cleanlab==2.9.0" "scikit-learn==1.9.1"; folder triage/{lab3_evidently_tickets.py, tickets.py, lab4_cleanlab_tickets.py, lab7_abstain.py}. Code = lab-data Lab 3 (VERIFIED evidently 0.7.23): make_tickets(n, outage_share) with channel, product_area, body_chars, customer_tenure_days; reference 4,000 (outage 5%) vs current 1,500 (outage 25%: login outage); DataDefinition(numerical_columns=[...], categorical_columns=[...]); Dataset.from_pandas; Report([DataDriftPreset(num_method='psi', num_threshold=0.2, drift_share=0.5), ValueDrift(column='customer_tenure_days', method='ks', threshold=0.05)], include_tests=True); snapshot = report.run(current_data=..., reference_data=...); snapshot.save_html(...); failed = [t for t in snapshot.dict()['tests'] if t['status'] == 'FAIL']; sys.exit(1 if failed else 0). Focus: (1) the 0.7.x imports (from evidently import DataDefinition, Dataset, Report); (2) include_tests=True (Report default False -> no tests, the gate never fails); (3) run() returns a Snapshot; parse metric_name/id (there is no metric_id key); (4) non-zero exit blocks CI. Cite docs 'Data and ML checks' https://docs.evidentlyai.com/quickstart_ml.

**Visual and animation.** Code left (.xs, 34 lines) with 4 focus bands; right: a CI pipeline strip 'collect week -> drift report -> retrain' where the drift report node is a gate; on focus 4 the gate turns red and the retrain node greys out ('held').

**Code.**

```text
lab-data.md Lab 3 lab3_evidently_tickets.py (full 44 lines, .xs, helper collapsed to 6 lines). data-focus="1:5-7, 2:28-31, 3:32-33, 4:35-40".
```

### 09.03 [lab] Dataset drift passed, product_area drifted: test the key columns

- File: `c09-03-lab8-drift-output.html`
- Id: `custom-c09-lab8-drift-output`

**Content.** Kicker: Lab 8 Acme ticket triage · step 2 of 4. .lab-head: python lab3_evidently_tickets.py; echo "exit code: $?" (HTML report ~3.8 MB, embeds plotly). Output pane (captured, exit code 1, exact): DriftedColumnsCount(drift_share=0.5, num_method=psi, ...) {'count': 1.0, 'share': 0.25}; ValueDrift body_chars psi 0.00864; customer_tenure_days psi 0.01251; channel Jensen-Shannon 0.01822; product_area Jensen-Shannon 0.20686; customer_tenure_days ks 0.57091; 'tests: 6, failed: 1'; 'FAIL: Value Drift for column product_area - Drift score is 0.21. The drift detection method is Jensen-Shannon distance.' Steps-rail: (1) share 0.25 < drift_share 0.5, so the dataset-level test passes: a yes/no dataset gate would miss the login outage; (2) only the per-column test caught it; (3) the KS value 0.571 is a p-value (low = drift) while PSI/JS are distances (high = drift): never one dashboard axis; (4) save snapshot.json() next to the model version. Errors (exact): "ModuleNotFoundError: No module named 'evidently.report'" / "'evidently.metric_preset'" (legacy tutorials; old API under evidently.legacy.*), "ValueError: Reference dataset should be present", "KeyError: 'metric_id'". Best practice: per-column tests on the 3-5 business-critical columns.

**Visual and animation.** Bespoke animation: four column bars with drift scores rising to their exact values (product_area bar crosses its threshold line and turns red); step 2 a dataset-level gauge shows 1 of 4 drifted = 0.25 under the 0.5 line (green 'pass' - the trap); step 3 a split axis: p-value scale (low = drift) vs distance scale (high = drift) with the KS 0.571 dot on the left scale.

**Code.**

```text
lab-data.md Lab 3 captured output block (9 lines).
```

### 09.04 [lab] cleanlab ranks the vendor's wrong labels: review 223, not 3,000

- File: `c09-04-lab8-cleanlab.html`
- Id: `custom-c09-lab8-cleanlab`

**Content.** Kicker: Lab 8 Acme ticket triage · step 3 of 4. .lab-head: python lab4_cleanlab_tickets.py (~7 s). Code = lab-data Lab 4 (VERIFIED cleanlab 2.9.0): tickets.py synthetic corpus (4 classes, templates + filler, classes = sorted(TEMPLATES)); flip 8% of labels to a random other class (rushed BPO vendor); TF-IDF(1,2) + LogisticRegression; pred_probs = cross_val_predict(..., method='predict_proba', cv=StratifiedKFold(5, shuffle=True)); find_label_issues(labels=noisy_y, pred_probs=pred_probs, return_indices_ranked_by='self_confidence', n_jobs=1). Output (captured, exact): 'flipped labels: 225   flagged by cleanlab: 223', 'precision: 1.00   recall: 0.99', top 5 e.g. '#2195 given=outage suggested=login p(given)=0.01 'account locked after 417 attempts''. Note: near-perfect only because templates separate cleanly; on real tickets expect lower numbers and treat the list as a review queue, not an auto-delete list. Steps-rail: (1) pred_probs must be out-of-sample (in-sample probabilities memorized the noisy labels); (2) column j of pred_probs = class j (sorted labels); (3) ranked indices instead of a mask; frac_noise=0.5 for a smaller budget; (4) n_jobs=1 on Windows/macOS notebooks. Best practice: run two model families and send the intersection to review first; log reviewer decisions (fix / keep / ambiguous / drop) - 'ambiguous' often means the taxonomy needs work.

**Visual and animation.** Bespoke animation (Deck.register): 3,000 ticket dots in a 4-class confusion layout (given label rows x suggested label columns); step 1 dots fill the diagonal and a scatter of 225 off-diagonal flipped dots (red); step 2 out-of-fold probabilities are computed (5 fold bands sweep across); step 3 cleanlab flags 223 dots (outlined) and they lift into a ranked review queue; step 4 the top 5 cards show their text and p(given)=0.01.

**Code.**

```text
lab-data.md Lab 4 lab4_cleanlab_tickets.py (full 31 lines) + tickets.py collapsed (make_tickets signature only). data-focus="1:15-18, 2:9, 3:20-22, 4:22".
```

### 09.05 [lab] Route when P(correct) beats 0.8, otherwise defer: cost falls 51%

- File: `c09-05-lab8-route-defer.html`
- Id: `custom-c09-lab8-route-defer`

**Content.** Kicker: Lab 8 Acme ticket triage · step 4 of 4. .lab-head: python lab7_abstain.py. Code = lab-synth-eval Lab 7 (re-run by the verifier, identical; scikit-learn 1.8.0 run / 1.9.1 API): costs (correct route, human triage, wrong route) = (0, 1, 5), the cost model of arXiv 2610.31657; 8-class router; train / calibration / test splits; per_ticket_cost(proba, y_true, t); t_star chosen on the calibration split only and frozen; analytic break-even (C_WRONG - C_TRIAGE) / (C_WRONG - C_OK) = 0.80; evaluate always-route, always-defer and tuned once on test; paired ratio bootstrap (same resampled tickets for both policies). Output (REAL, exact): 'accuracy (always route) 0.612'; 't* from calibration = 0.79   analytic break-even = 0.80'; 'test cost/ticket  always-route=1.942  always-defer=1.000  tuned=0.946  coverage=22.08%'; 'wrong routes: always-route=38.8%  tuned=3.3%'; 'relative cost reduction 51.3%  95% CI [49.7%, 52.8%]'. Honest headline: with 61% accuracy the policy routes only 22% of tickets and is only ~5% cheaper than sending everything to humans. Steps-rail: report both trivial baselines + coverage + wrong-route rate; check the correctness AUROC of the confidence first (~0.5 = no threshold can help); compare clf.classes_[proba.argmax(1)] when labels are strings.

**Visual and animation.** Bespoke animation: a confidence axis 0..1 with ticket dots placed by max probability (green = correct, red = wrong); step 1 a threshold line sweeps from 0 to 1 while a cost-per-ticket counter traces a U-shaped curve; step 2 the line locks at 0.79 (calibration) next to the analytic 0.80 mark; step 3 three bars: always-route 1.942, always-defer 1.000, tuned 0.946 with coverage 22%; step 4 wrong-route donut 38.8% -> 3.3%.

**Code.**

```text
lab-synth-eval.md Lab 7 lab7_abstain.py (full 40 lines, .xs). data-focus="1:6, 2:15-18, 3:21-24, 4:36-40".
```

### 09.06 [gotcha] cleanlab hung 77 times on Windows; flagged labels are not delete lists

- File: `c09-06-noise-tooling-gotchas.html`
- Id: `custom-c09-noise-tooling-gotchas`

**Content.** Kicker: Gotcha · label-noise tooling (lab-data L4, captured run; gotchas.md D1). Three .gotcha cards. (1) Symptom: the script printed 'RuntimeError: An attempt has been made to start a new process before the current process has finished its bootstrapping phase.' 77 times, then hung (killed after 100 s). Cause: default n_jobs=None = one process per physical core; Windows/macOS spawn without an if __name__ == '__main__': guard. Fix: n_jobs=1 or the guard ('Windows users may see a speed-up with n_jobs=1', filter.py:177). (2) Symptom: 'ValueError: Labels cannot be strings, they must be zero-indexed integers corresponding to class indices.' / 'Values in pred_probs must be between 0 and 1.' Fix: np.searchsorted(classes, string_labels); softmax or predict_proba. (3) Symptom: cleaning made the model worse. Evidence: 2609.25487 (21 Sep 2026): over 870,514 Google Play apps, three detectors agreed on 7,598 candidates; removing them did not improve the model and the loss grew with the number removed; a model trained only on overlap apps got AUC 0.2518. Fix: use cleanlab to characterize and review noise; delete only after human review, especially when the label is a proxy.

**Visual and animation.** Bespoke animation: a terminal pane where the RuntimeError line repeats with a counter climbing to 77 and a CPU-core grid flickers; step 2 n_jobs=1 calms the grid to one core and the output appears; step 3 a 'flagged' set of dots is deleted and an AUC line drops (red), then the same set routes to a human review queue instead (green).

**Code.**

```text
Fix: if __name__ == '__main__':
    ranked = find_label_issues(labels=noisy_y, pred_probs=pred_probs, return_indices_ranked_by='self_confidence', n_jobs=1)
labels = np.searchsorted(classes, string_labels)  # lab-data Lab 4.
```

### 09.07 [paper] Freeze the abstention threshold first; LLM confidences may be flat

- File: `c09-07-abstain-papers.html`
- Id: `custom-c09-abstain-papers`

**Content.** Kicker: arXiv Oct 2026. Three .paper cards. (1) 2610.31657 'Cost-Aware Abstention for LLM-Based IT Ticket Classification' (22 Oct 2026, verifier-confirmed): cost model (0, 1, 5); select on calibration, freeze, evaluate once; TF-IDF+LR at threshold 0.60 cuts test cost 0.763 -> 0.472 (-38.1%, paired ratio-bootstrap 95% CI [35.7%, 40.4%]) and wrong routes 15.3% -> 3.5%; isotonic lowers ECE without improving discrimination; GPT-4o-mini few-shot has correctness AUROC 0.500; at break-even 0.80 seven prompted configurations defer all tickets. Monday: check correctness AUROC before you threshold an LLM's confidence. (2) 2610.17399 'Monitoring-by-Betting' (12 Oct 2026): sequential e-detectors for unstructured streams control false alarms; calibration sets as small as m = 30; LLM-concept monitors were fastest on a clinical AI-scribe deployment. Monday: monitor ticket text continuously, not only weekly PSI. (3) 2610.27701 'Understanding Data Augmentation under Label Noise' (20 Oct 2026): under label noise augmentation can act as an uncertainty amplifier. Monday: clean labels before you augment or synthesize.

**Visual and animation.** Method animation for card 1: a 3-lane router diagram (route / defer / wrong) with ticket tokens; step 1 always-route sends many tokens to the red 'wrong' lane; step 2 the frozen 0.60 threshold diverts low-confidence tokens to 'human triage'; step 3 a cost bar counts down 0.763 -> 0.472 and wrong routes 15.3% -> 3.5%; step 4 an LLM confidence histogram collapses to a single spike labelled 'AUROC 0.500'.

### 09.08 [industry] Wayfair, Amazon, Mastercard route labels to the cheapest good rater

- File: `c09-08-annotation-routing.html`
- Id: `custom-c09-annotation-routing`

**Content.** Kicker: In production · annotation routing, Aug-Sep 2026 industry papers (arxiv-data.md #8, #9, #11; affiliations from the files). Wayfair Differential Reasoning Router (2608.30224, 31 Aug 2026): routes each e-commerce labeling sample between direct LLM answer, reasoning model and human; > 60% fewer reasoning tokens. Amazon QUORUM (2608.27974, 28 Aug 2026): routes items to human or LLM annotators from difficulty features; up to +34.4% quality at -8.8% cost. Mastercard merchant matching (2609.33878, 27 Sep 2026): two confidence-gated local LLM judges with separate positive/negative thresholds; 96.88% label purity at 81.7% coverage; reasoning effort gave no F0.5 gain at 1.8-5x latency. Lesson: route by predicted differential value (direct vs reasoning vs human), gate on two agreeing cheap judges, and send the rest to people. .cite arxiv.org/abs/2608.30224, /2608.27974, /2609.33878.

**Visual and animation.** Animated routing diagram (>= 50% canvas): incoming label requests (amber tickets) hit a router node; three lanes: 'direct LLM' (fast, cheap), 'reasoning LLM' (slower), 'human' (violet); tokens split by difficulty with :flow pulses. Step 2: the two-judge gate for Mastercard: a token passes only when both judge dials agree; disagreements go to the human lane. Step 3: three .stat count-ups (-60% tokens, +34.4% quality, 96.88% purity).

## Chapter 10: Synthetic data and RAG eval sets with verification

Tone: `state`

**Scenario.** Acme HR policy assistant (RAG over PTO, parental-leave and expense policies): synthesize a RAG eval set with ragas, reject ungrounded, closed-book and duplicate items, decontaminate train vs test with MinHash, and correct the LLM judge's biased pass rate with human labels.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-synth-eval.md
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-data.md
- C:/Users/evija/googleadk2.0/research-v2/custom/arxiv-data.md
- C:/Users/evija/googleadk2.0/research-v2/custom/industry.md
- C:/Users/evija/googleadk2.0/research-v2/custom/arxiv-eval.md
- C:/Users/evija/googleadk2.0/research-custom/06-llm-rag-datasets-synthetic.md

### 10.01 [chapter] Synthetic data and RAG eval sets with verification

- File: `c10-01-chapter.html`
- Id: `custom-c10-chapter`

**Content.** Chapter 10. .display 'Generate, verify, keep'. Lede: 'Synthetic data is a draft. It counts only after grounding, closed-book, dedup and human checks.' Scenario: Acme HR policy assistant (RAG).

**Visual and animation.** Self-animating mini-diagram: a generator node emits Q/A cards; cards pass three filter gates (grounded, closed-book, near-dup); some cards drop off at each gate; survivors get a hash stamp and enter a frozen 'eval set' node; loop.

### 10.02 [lab] Synthesize 40 HR-policy questions with ragas TestsetGenerator

- File: `c10-02-lab9-ragas.html`
- Id: `custom-c10-lab9-ragas`

**Content.** Kicker: Lab 9 Acme HR policy assistant · step 1 of 4. Run it Monday: separate venv; pip install "ragas==0.4.3" "langchain-openai==1.7.2" "openai==3.37.0"; export OPENAI_API_KEY, GEN_MODEL, JUDGE_MODEL, RAGAS_DO_NOT_TRACK=true (ragas sends usage analytics unless 'true'); hr_policies/ with 5+ markdown policies, each > 500 tokens. Code = lab-synth-eval Lab 2 first part (VERIFIED vs ragas 0.4.3 docs; LLM part not run): docs = [Document(page_content=..., metadata={'source': p}) for p in sorted(glob('hr_policies/*.md'))]; generator = TestsetGenerator(llm=LangchainLLMWrapper(ChatOpenAI(model=GEN_MODEL)), embedding_model=OpenAIEmbeddings(client=client)); rows = generator.generate_with_langchain_docs(docs, testset_size=40).to_list(). Steps-rail: default query mix 0.5 single-hop specific / 0.25 multi-hop abstract / 0.25 multi-hop specific -> pass query_distribution= to match your real query logs; each row has user_input, reference_contexts, reference, persona_name, query_style, query_length, synthesizer_name; expect 'DeprecationWarning: LangchainLLMWrapper is deprecated and will be removed in a future version. Use llm_factory instead' (docs still use it). Errors (exact): 'ValueError: Documents appears to be too short (ie 100 tokens or less). Please provide longer documents.'; 'ValueError: No relationships match the provided condition. Cannot form clusters.' (multi-hop needs related docs) -> more/overlapping docs or a single-hop query_distribution. Cite: ragas 'Testset Generation for RAG' https://docs.ragas.io/en/stable/getstarted/rag_testset_generation/.

**Visual and animation.** Bespoke knowledge-graph animation (Deck.register): 5 policy documents as green nodes; step 1 headline/entity extractors add small child nodes; step 2 relationship edges draw between related nodes (PTO <-> parental leave); step 3 query cards are generated from single nodes (single-hop) and from edges (multi-hop), counted 20 / 10 / 10 in the default mix; illustrative counts labelled.

**Code.**

```text
lab-synth-eval.md Lab 2 lab2_hr_rag_testset.py lines 1-19 (imports, docs, generator, rows). data-focus="1:12-13, 2:15-16, 3:17".
```

### 10.03 [lab] Reject ungrounded, closed-book and duplicate items, then hash the set

- File: `c10-03-lab9-verify.html`
- Id: `custom-c10-lab9-verify`

**Content.** Kicker: Lab 9 Acme HR policy assistant · step 2 of 4. Code = lab-synth-eval Lab 2 second part: ask_judge(prompt) with temperature 0 and response_format json_object {'verdict': 'YES'|'NO'}; for each row: (a) 'Is every fact in this answer stated in the context?' != YES -> 'reference not grounded'; (b) closed-book answer from the judge model without contexts; if it states the same facts as the reference -> 'answerable without retrieval'; (c) difflib ratio > 0.9 vs kept questions -> 'near-duplicate question'; write hr_rag_eval_<sha256[:12]>.jsonl with json.dumps(sort_keys=True). Output (ILLUSTRATIVE, not run): 'generated=40 kept=29 dropped={'answerable without retrieval': 6, 'reference not grounded': 3, 'near-duplicate question': 2}', 'synthesizer mix: Counter({'single_hop_specific_query_synthesizer': 16, 'multi_hop_specific_query_synthesizer': 7, 'multi_hop_abstract_query_synthesizer': 6})', 'wrote hr_rag_eval_3f9c0a1b2d4e.jsonl -> send 10% to an HR reviewer before first use'. Steps-rail: a closed-book-answerable item measures parametric memory, not your RAG system: drop it or tag it as its own slice; keep reference_contexts and score retrieval recall separately (2610.26951: similarity retrieval finds any relevant chunk far more reliably than all required chunks); the hash makes the eval set immutable and is cited by the quality card (C11); add an 'unanswerable' slice (policies not in the corpus -> 'contact HR').

**Visual and animation.** Bespoke funnel animation: 40 question cards enter at the top; three gates in sequence; at each gate the dropped cards slide off to labelled bins with counters (3 not grounded, 6 closed-book, 2 near-dup); 29 survivors compress into a file icon that receives a sha256 stamp; values labelled illustrative.

**Code.**

```text
lab-synth-eval.md Lab 2 lab2_hr_rag_testset.py lines 21-50 (ask_judge, loop, hash, write). data-focus="1:21-25, 2:29-31, 3:32-36, 4:37-39, 5:42-46".
```

### 10.04 [lab] MinHash LSH removes near-duplicates and the item that leaks the test

- File: `c10-04-lab9-dedup.html`
- Id: `custom-c10-lab9-dedup`

**Content.** Kicker: Lab 9 Acme HR policy assistant · step 3 of 4. .lab-head: python lab8_minhash_dedup.py; pip install "datasketch==2.0.0". Code = lab-data Lab 8 (VERIFIED datasketch 2.0.0, captured run): shingles(text, k=5) on normalized characters; signature() MinHash(num_perm=128) (2.0.0 default scheme 'affine32') + update_batch; step 1 query-then-insert into MinHashLSH(threshold=0.7, num_perm=128) to dedup train; step 2 index the TEST set and drop train docs that hit it. Output (captured, exact): "kept: ['tr-001', 'tr-003', 'tr-004', 'tr-005']"; "dropped (dup, of, est. Jaccard): [('tr-002', 'tr-001', 0.82), ('tr-006', 'tr-005', 0.77)]"; "train docs leaking into test: {'tr-003': ['te-001']}"; "final train set: ['tr-001', 'tr-004', 'tr-005']". Steps-rail: (1) character 5-grams catch 'filed' vs 'submitted' (est. Jaccard 0.77); word 1-grams would not; (2) threshold 0.7 with 128 perms picked b = 14 bands x r = 9 rows; LSH returns candidates: check jaccard() before dropping; (3) query-then-insert keeps the first member: sort by a quality signal (newest policy version) first; two versions that differ only in '16 weeks' vs '12 weeks' are near-duplicates with different facts. Errors (exact): "ValueError: MinHash scheme 'legacy' does not match scheme 'affine32' of the MinHash previously given to this index" (datasketch 1.x pickles) -> rebuild the index or scheme='legacy' everywhere; 'ValueError: The given key already exists'.

**Visual and animation.** Bespoke animation: 6 train and 2 test policy sentences as cards; step 1 each card shatters into shingle chips that hash into a 128-cell signature strip; step 2 cards with matching band buckets snap together (tr-002 onto tr-001 with 0.82, tr-006 onto tr-005 with 0.77) and the duplicates fade; step 3 the test cards light up an index and tr-003 is pulled out with a red 'leaks te-001' tag; step 4 final 3-card train set.

**Code.**

```text
lab-data.md Lab 8 lab8_minhash_dedup.py (full 45 lines, .xs). data-focus="1:7-10, 2:12-15, 3:31-40, 4:42-48".
```

### 10.05 [lab] 88% judge agreement hides kappa 0.58; the corrected pass rate is 72.7%

- File: `c10-05-lab9-judge.html`
- Id: `custom-c10-lab9-judge`

**Content.** Kicker: Lab 9 Acme HR policy assistant · step 4 of 4. .lab-head: python lab8_judge_agreement.py; pip install "krippendorff==0.9.0" "scikit-learn==1.9.1". Code = lab-synth-eval Lab 8 (VERIFIED, REAL run): 300 answers labelled by two HR reviewers and an LLM judge (lenient: TPR 0.95, TNR 0.60 simulated); confusion_matrix(gold, judge, labels=[0, 1]) -> TPR/TNR; cohen_kappa_score human-human vs judge-human; krippendorff.alpha(reliability_data=rel, level_of_measurement='nominal') with human_b missing on 150 units; rogan_gladen(p_obs, tpr, tnr) = (p_obs + TNR - 1) / (TPR + TNR - 1) on 4,000 judge-only production answers; bootstrap resampling BOTH calibration and production items. Output (REAL, exact): 'raw agreement judge-vs-human 0.877'; 'Cohen kappa human-human 0.812  judge-human 0.580'; 'judge TPR=0.946  TNR=0.593'; 'Krippendorff alpha (nominal, 3 raters, missing ok) 0.628'; 'prod pass rate: judge-observed 0.799  corrected 0.727  95% CI [0.628 0.798]  (truth 0.726)'. Steps-rail: the human-human kappa is the ceiling, not 1.0; TNR = catching bad answers: this judge catches 59%; Rogan-Gladen needs TPR + TNR > 1; the wide CI comes from only 300 labels -> buy more human labels on the failure class. Best practice: validate per failure mode; test order-swap and replication stability (2610.12083: verdicts change across identical temperature-0 runs); read verdicts after generation, not from first-token logits (2610.00054).

**Visual and animation.** Bespoke animation: step 1 a 2x2 confusion matrix fills cell by cell (judge vs gold) and TPR/TNR gauges settle at 0.946 / 0.593; step 2 two kappa bars (0.812 humans, 0.580 judge) with the human bar drawn as a dashed ceiling; step 3 a production pass-rate bar shows 0.799, a correction arrow pulls it to 0.727 next to a hidden 'truth 0.726' marker that is revealed; step 4 a CI whisker 0.628-0.798 draws.

**Code.**

```text
lab-synth-eval.md Lab 8 lab8_judge_agreement.py (full 44 lines, .xs). data-focus="1:13-19, 2:22-24, 3:34-36, 4:38-46".
```

### 10.06 [buildup] Generate four candidates, execute hidden tests, keep only what passes

- File: `c10-06-distilabel-exec.html`
- Id: `custom-c10-distilabel-exec`

**Content.** Kicker: Build. Feature added: synthetic SFT data for the agent's Python tools with an execution verifier (lab-synth-eval Lab 1, VERIFIED distilabel 1.5.3; run_tests re-run by the verifier: (True, ''), (False, 'AssertionError'), (False, 'timeout'); LLM part not run). Example tools from the lab: refund_amount(price, days_since_delivery, opened) and is_refund_eligible(order_status, amount) with 4 hidden asserts each. .code-wrap.bad: 'LLM writes code -> straight into SFT data' (no verifier). .code-wrap.good: run_tests(code, tests, timeout=5) in a fresh TemporaryDirectory with [sys.executable, '-I', path]; @step(inputs=['generation','tests'], outputs=['code','passed','error']) ExecuteUnitTests; Pipeline: LoadDataFromDicts(SEEDS) >> TextGeneration(llm=OpenAILLM(...), template=TEMPLATE, columns=['spec'], num_generations=4) >> ExecuteUnitTests(); pipeline.run(use_cache=False); sft = ds.filter(passed). .delta (illustrative): 'candidates=8 passed=6 pass-rate=75%' plus REJECTED lines with AssertionError. Steps-rail: verifiers in order of cost (parse -> execute -> judge); the rejection histogram is your data-quality dashboard; a pass rate near 100% means the tests are too weak (mutation-test them); DPO pairs = passing vs failing code per spec. Maintenance note (state it): distilabel's last release is 1.5.3 (2025-01-28) and the README says the original authors moved on: teach the pattern, keep the verifier a plain function. Gotcha: OpenAILLM always sends max_tokens, so reasoning models may reject it -> non-reasoning model or local OpenAI-compatible server; quoted StepInput hints (or from __future__ import annotations) break DAG validation.

**Visual and animation.** Bespoke animation: 2 spec cards fan out into 4 candidate cards each (8); each candidate drops into a sandbox box with a timer; 6 turn green, 2 red with 'AssertionError'; a rejection histogram builds on the right (reason x count); step 4 the green cards form an SFT file and a passing/failing pair forms a DPO pair card.

**Code.**

```text
lab-synth-eval.md Lab 1 lab1_refund_exec_verify.py lines 28-61 (run_tests, ExecuteUnitTests, Pipeline, main). data-focus="1:28-38, 2:41-47, 3:50-57, 4:59-66".
```

### 10.07 [gotcha] krippendorff.alpha defaults to interval: 0.083, not 0.542

- File: `c10-07-krippendorff-default.html`
- Id: `custom-c10-krippendorff-default`

**Content.** Kicker: Gotcha · agreement statistics (lab-synth-eval L8 and lab-data L5, REAL runs). Three .gotcha cards. (1) Symptom: alpha 0.083 on 3-category codes (answer / clarify / escalate). Cause: alpha(..., level_of_measurement='interval') is the default. Output (exact): '3-category labels: nominal 0.542  vs default 'interval' 0.083'. Fix: pass level_of_measurement='nominal' for categories, 'ordinal' for Likert. (2) Symptom: a wrong Fleiss kappa with no error. Cause: statsmodels aggregate_raters takes items x raters, krippendorff.alpha takes raters x items: opposite orientations, neither raises. Fix: name the axes in code review; HR rubric lab: humans ordinal alpha 0.852, + lenient LLM judge 0.755, judge kappa vs every human < 0.21 unweighted. (3) Symptom: string labels return 0.0 silently. Fix: map to ints or pass value_domain. Also: unweighted Cohen kappa treats 2-vs-3 like 0-vs-3 on an ordinal 0-3 scale: ana vs ben 0.664 unweighted vs 0.905 quadratic-weighted; report which weighting you used. Paper hook: 2610.13303 'Agreement Without Alignment' (9 Oct 2026): rubric clarification raised inter-judge alpha by 0.069 (95% CI 0.046-0.092) over 129,770 requests but did not change agreement with experts.

**Visual and animation.** Bespoke animation: a raters x items matrix (4 x 12) draws; step 1 an 'interval' ruler under the categories shows answer=0, clarify=1, escalate=2 as numeric distances and the alpha gauge reads 0.083; step 2 the ruler swaps for unordered category chips and the gauge jumps to 0.542; step 3 the matrix transposes (items x raters) with arrows labelled statsmodels vs krippendorff.

**Code.**

```text
Bad: krippendorff.alpha(reliability_data=codes). Good (lab-synth-eval Lab 8): krippendorff.alpha(reliability_data=codes, level_of_measurement='nominal'); table, _ = aggregate_raters(humans.T)  # items x raters; fleiss_kappa(table, method='fleiss'); cohen_kappa_score(a, b, weights='quadratic').
```

### 10.08 [paper] Filters prefer AI text, batching distorts, decontam over-deletes

- File: `c10-08-synthetic-risks.html`
- Id: `custom-c10-synthetic-risks`

**Content.** Kicker: arXiv Sep-Oct 2026. Three .paper cards. (1) 2609.40295 'How Much Is an AI Token Worth?' (30 Sep 2026, verifier-confirmed): 27.5% (June) and 31.1% (August 2026) of FineWeb-filtered web tokens are AI-labelled; AI docs pass FineWeb 2.3x and DCLM 9.8x as often as human docs; at August's AI share an unfiltered crawl needs 1.6x compute (3.0x forecast for 2028). Monday: run an AI-text detector after your quality classifier; repeat human tokens before adding AI web tokens. (2) 2609.32546 'Shared Autoregressive Context Can Distort Relationships in Synthetic Data' (26 Sep 2026): generating 10 records per call inflates correlation error 48-127%. Monday: one record per call for tabular synthesis. (3) 2610.21229 'What Should We Remove? RLVR Data Decontamination' (15 Oct 2026, verifier-confirmed): over 1,673,514 items, cosine 0.80 removals were 88% false (52 of 59 sampled); no threshold 0.80-0.98 reached 90% precision; a judge-adjudicated policy reached 98.1% precision / 98.2% recall. Monday: two-stage decontam = MinHash/embedding candidates, then adjudication, and log every removal.

**Visual and animation.** Method animation for card 1: a funnel raw crawl -> FineWeb -> DCLM with human (blue) and AI (amber) dots; blue dots drop out faster at each stage and an AI-share counter rises (1.5% -> 14.5% survivors at DCLM). Step 2: a 10-records-per-call box shows correlated record pairs (lines) vs 1-per-call independent records. Step 3: decontam candidates at cosine 0.80 (59 dots) where 52 turn grey 'false removal' and an adjudicator node restores them.

### 10.09 [industry] Chroma Context-1 checks every synthetic quote before RL training

- File: `c10-09-chroma-context1.html`
- Id: `custom-c10-chroma-context1`

**Content.** Kicker: In production · Chroma Context-1 (26 Mar 2026, industry.md A12). A 20B retrieval subagent (gpt-oss-20b + LoRA, MXFP4 MoE inference) that returns ranked documents to a downstream reasoner. Synthetic pipeline (web, finance/SEC, legal/USPTO, email): gather documents with domain search tools -> generate clues, question, answer -> verify: an LLM extracts quotes, checked deterministically against the source text -> optional distractors -> optional chaining to control hop count. Human agreement with the verifier: web 84.4%, finance 93%, email 87.5%, legal 98.3%. Training: SFT warm-up on Kimi K2.5 trajectories (keep > 50% trajectory recall, > 40% output recall, up to 5% zero-recall negatives), then CISPO RL with 128 queries x 8 rollouts per step, converging ~step 230. Reward: recall-weighted F-beta (16x annealed to 4x), +1.0 when the answer chunk is found, penalties for repeated pruning and turns beyond 64. Results: BrowseComp-Plus 0.96 (4x) / 0.87 (1x) vs opus-4.5 0.87, gpt-5.2 0.82; 400-500 tok/s on B200, up to 10x faster; generalized to the held-out email domain. Lesson: RAG quality is a data product: verified synthetic tasks + a recall-first reward. .cite https://www.trychroma.com/research/context-1 ; data-gen code github.com/chroma-core/context-1-data-gen.

**Visual and animation.** Animated architecture (>= 50% canvas): left, the data pipeline as 4 nodes (gather -> generate -> verify quotes -> chain) with a deterministic 'quote check' tool node; right, the Context-1 subagent node feeding ranked docs to a 'reasoner' node. Step 2: four domain agreement bars count up (84.4, 93, 87.5, 98.3). Step 3: a reward meter where recall weight anneals 16x -> 4x (dial). Step 4: BC+ bars 0.96 vs 0.87 vs 0.82.

### 10.10 [practices] Synthetic data rules: seed real, verify cheap first, anchor humans

- File: `c10-10-synthetic-checklist.html`
- Id: `custom-c10-synthetic-checklist`

**Content.** Best practices (lab-synth-eval L1/L2/L8, gotchas.md F1-F3, D3, industry.md Part D 9-11). Do: (1) Seed generation from real data and stratify by an explicit attribute grid (intent x difficulty x persona): prompted generation collapses onto dominant modes (2609.38359). (2) Verify in cost order: parse -> execute/quote-check -> judge. (3) Reject samples that contain chat-template special tokens: WebFovea found self-generated template tokens in 4.9% of episodes (2610.03036). (4) Drop closed-book-answerable eval items or slice them. (5) Freeze eval sets by content hash and never train on them; decontaminate with candidates + adjudication. (6) Pin the judge model version and keep a 200-item human anchor; re-measure kappa/alpha on every judge upgrade (newer backbones are not consistently better judges, 2610.09820). (7) Compute n_eff before adding judges: mean error correlation 0.21 makes 10 judges ~ 3.5 independent ones (2609.22512). (8) Keep a fresh human-data share in every synthetic round (minimum ratio still open, 2609.18878). Don't: (9) Do not trust high inter-judge agreement as validity (2610.13303). (10) Do not depend on one unmaintained generator library (distilabel 1.5.3, 2025-01-28).

**Visual and animation.** Checks list (stagger, 3 steps). Right: bespoke n_eff animation: 10 judge avatars connected by correlation lines (rho 0.21) merge into 3.5 'independent' silhouettes as the n_eff formula counts down 10 -> 3.46.

**Code.**

```text
arxiv-eval.md #4 n_eff (5 lines, labelled 'standard design-effect formula, reproduces 10 -> 3.5'): C = np.corrcoef(err); k = C.shape[0]; rho = (C.sum() - k) / (k * (k - 1)); return k / (1 + (k - 1) * rho).
```

## Chapter 11: Eval design, the quality card and open challenges

Tone: `tool`

**Scenario.** Acme claims-extraction agent release: report the pass rate per line of business x language with honest CIs, compare v1 vs v2 on the same 400 golden cases, and ship only when a versioned quality card passes its release gate in CI.

Research files:
- C:/Users/evija/googleadk2.0/research-v2/custom/lab-synth-eval.md
- C:/Users/evija/googleadk2.0/research-v2/custom/arxiv-eval.md
- C:/Users/evija/googleadk2.0/research-v2/custom/gotchas.md
- C:/Users/evija/googleadk2.0/research-v2/custom/industry.md
- C:/Users/evija/googleadk2.0/research-v2/custom/00-VERIFIED.md
- C:/Users/evija/googleadk2.0/research-custom/07-eval-design.md

### 11.01 [chapter] Eval design, the quality card and open challenges

- File: `c11-01-chapter.html`
- Id: `custom-c11-chapter`

**Content.** Chapter 11. .display 'No number without n, CI, slice and version'. Lede: 'An eval is an experiment. The quality card is the release gate.' Scenario: Acme claims-agent release.

**Visual and animation.** Self-animating mini-diagram: a headline bar '84%' splits into 8 slice bars with error whiskers; one slice bar turns red; a quality card icon receives a red FAIL stamp, then a fix loop turns it green; loop.

### 11.02 [lab] An 84% headline hides a Spanish health-claims slice at 56%

- File: `c11-02-lab10-slices.html`
- Id: `custom-c11-lab10-slices`

**Content.** Kicker: Lab 10 Acme claims-agent release · step 1 of 4. Run it Monday: Python 3.12+ (numpy 2.5.4 and scipy 1.18.1 refuse older interpreters); pip install "numpy==2.5.4" "pandas==3.1.0" "statsmodels==0.15.0" "scipy==1.18.1"; folder release_eval/{lab3_slices.py, lab4_paired.py, lab9_quality_card.py}. Code = lab-synth-eval Lab 3 (VERIFIED statsmodels 0.15.0, REAL run on older pins): simulated eval log of 60 claim files (clusters) x 3-8 questions; line (auto/home/health/travel) x lang (en/es); wilson_table() with proportion_confint(..., method='wilson'); cluster_bootstrap_ci() resampling claim files (B=5000); writes claims_eval.jsonl. Output (REAL, exact): 'overall pass rate 0.839  (n=353 items, 60 claim files)'; 'naive Wilson 95% CI : [0.797 0.873]'; 'cluster bootstrap 95% CI : [0.791 0.882]'; slice table health/es 9/16 = 0.562 [0.332, 0.769] ... auto/en 140/156 = 0.897; 'slices with n < 30: ['health/es', 'home/es', 'travel/es', 'health/en', 'auto/es']'. Steps-rail: (1) proportion_confint default is method='normal': pass 'wilson'; (2) always carry n next to the rate; (3) resample clusters: the naive CI (width 0.076) is ~17% too narrow vs the cluster bootstrap (0.091) because questions from the same claim file correlate; (4) pre-register slices and a minimum n (30) before looking. Error: '(nan, nan)' + 'RuntimeWarning: invalid value encountered in sqrt' when count > nobs after a duplicating join -> assert (g.k <= g.n).all().

**Visual and animation.** Bespoke animation: step 1 a single 0.839 bar with a narrow naive whisker; step 2 the bar explodes into 8 slice bars sorted by rate with Wilson whiskers (health/es lowest, red; thin slices hatched for n < 30); step 3 the overall whisker widens from naive to cluster-bootstrap (0.797-0.873 -> 0.791-0.882); step 4 claim-file clusters shown as grouped dots being resampled.

**Code.**

```text
lab-synth-eval.md Lab 3 lab3_slices.py (full 42 lines, .xs). data-focus="1:25-29, 2:32-37, 3:40-45".
```

### 11.03 [lab] v1 vs v2 on the same 400 cases: unpaired says no, paired says yes

- File: `c11-03-lab10-paired.html`
- Id: `custom-c11-lab10-paired`

**Content.** Kicker: Lab 10 Acme claims-agent release · step 2 of 4. .lab-head: python lab4_paired.py. Code = lab-synth-eval Lab 4 (VERIFIED scipy 1.18.1, statsmodels 0.15.0; docstring renamed to the claims agent, data is simulated): shared item difficulty; v1 and v2 pass vectors; diff_of_means(x, y, axis=-1) (vectorized); stats.bootstrap((b, a), ..., paired=False) vs paired=True with method='percentile', rng=rng; BCa on b - a; mcnemar(table, exact=True) on discordant pairs; MDE ~ 2.8 x SE. Output (REAL; captured with scipy 1.11.4 using random_state=rng instead of rng=): 'v1=0.735  v2=0.787  delta=+0.052'; 'unpaired 95% CI [-0.007, +0.110] width=0.118 SE=0.0302'; 'paired 95% CI [+0.005, +0.102] width=0.097 SE=0.0250'; 'paired BCa [+0.005, +0.102]'; 'discordant: v1-only=40 v2-only=61  McNemar exact p=0.0460'; 'MDE unpaired ~ 0.085', 'MDE paired ~ 0.070'. Steps-rail: pairing removes shared item difficulty; the 299 concordant items carry no information about the difference; with 400 paired items you can detect only ~7 points: compute MDE before building the eval set. Errors (exact): "TypeError: bootstrap() got an unexpected keyword argument 'rng'" (scipy < 1.15) ; 'DegenerateDataWarning: The BCa confidence interval cannot be calculated' -> percentile; 'ValueError: When paired is True, all samples must have the same length along axis' -> score crashes as 0, align on item_id.

**Visual and animation.** Bespoke animation: 400 item tiles in a grid coloured by (v1, v2) outcome: both right, both wrong (grey), v1-only (red, 40), v2-only (green, 61); step 1 tiles fill; step 2 grey concordant tiles fade, leaving 101 discordant tiles (McNemar); step 3 two CI bars on a delta axis: unpaired crossing 0 (red), paired above 0 (green); step 4 an MDE ruler (0.085 vs 0.070).

**Code.**

```text
lab-synth-eval.md Lab 4 lab4_paired.py (full 30 lines). data-focus="1:9-11, 2:18-22, 3:26-30, 4:32-34".
```

### 11.04 [lab] The quality card is code: hash the eval file, gate on CI lower bounds

- File: `c11-04-lab10-card-code.html`
- Id: `custom-c11-lab10-card-code`

**Content.** Kicker: Lab 10 Acme claims-agent release · step 3 of 4. Code = lab-synth-eval Lab 9 lab9_quality_card.py (VERIFIED pandas + statsmodels 0.15.0): EVAL_FILE = 'claims_eval.jsonl' (from step 1); OTHER = numbers from earlier labs (ece_15_uniform 0.0063 isotonic, threshold 0.79, cost model (0, 1, 5), judge_kappa 0.580, judge_tpr 0.946, judge_tnr 0.593); GATES = {'min_slice_ci_low': 0.50, 'min_slice_n': 30, 'min_judge_kappa': 0.60}; sha256 of the file bytes; Wilson headline + per-slice CIs; failures list; thin slices; card dict with eval_set {file, sha256, n_items, n_clusters, unit_of_resampling: 'claim_id'}, headline, slices, calibration, decision_policy, judge, known_gaps, gate; json.dump + markdown; sys.exit(0 if not failures else 1). Focus: (1) hash the stored bytes, not a re-serialized DataFrame (else the hash changes every run); (2) gates decided before the run, on the CI lower bound so a thin slice cannot pass by luck; (3) unit_of_resampling and known_gaps make the card honest; (4) non-zero exit = failing CI check. Best practice: one card per (model version x eval-set hash); in production each lab writes a JSON fragment so no number is retyped.

**Visual and animation.** Code left (.xs) with 4 focus bands; right: bespoke card-assembly animation: a blank quality card whose fields fill one by one in sync with focus (sha256 chip, n=353 / 60 claims, headline 83.9% [79.7, 87.3], slice mini-table, judge row, known gaps), ending with an empty 'Gate' field that pulses.

**Code.**

```text
lab-synth-eval.md Lab 9 lab9_quality_card.py (full 52 lines, .xs; markdown rendering collapsed to 4 lines). data-focus="1:15-17, 2:12-14, 3:28-33, 4:52".
```

### 11.05 [lab] Gate FAIL: two Spanish slices and the judge block the release

- File: `c11-05-lab10-card-gate.html`
- Id: `custom-c11-lab10-card-gate`

**Content.** Kicker: Lab 10 Acme claims-agent release · step 4 of 4. .code-wrap.term: '$ python lab3_slices.py && python lab9_quality_card.py; echo "exit=$?"' and the CI step 'run: python lab9_quality_card.py' (job fails on exit 1); optional 'gh pr comment --body-file quality_card.md'. Output (REAL, exact): '# Quality card - claims agent eval (2026-10-23)'; 'Eval set claims_eval.jsonl sha256:d0e202a5a0b3e504 | n=353 items / 60 claims'; '**Pass rate 83.9%** (Wilson 95% 79.7%-87.3%)'; slice table (auto/en 156 90% 84-94% ... health/es 16 56% 33-77% ... travel/es 13 69% 42-87%); 'Judge: kappa 0.58, TPR 0.946, TNR 0.593'; 'Thin slices: auto/es (n=8), health/en (n=24), health/es (n=16), home/es (n=29), travel/es (n=13)'; '**Gate: FAIL** slice health/es: CI low 0.33 < 0.5; slice travel/es: CI low 0.42 < 0.5; judge kappa 0.58 < 0.6'; 'exit=1'. Steps-rail: what to do next: collect more Spanish health/travel claims (thin slices), recalibrate or replace the judge (C10 Lab 9), re-run; diff cards between releases. Errors: "FileNotFoundError: ... 'claims_eval.jsonl'" -> run step 1 first; 'TypeError: Object of type int64 is not JSON serializable' -> int()/float() casts. Variation: add synthetic_fraction, generator provenance and an n-gram contamination check (SynthSentry 2609.12353: a naive quantile alarm threshold ran 4x over budget; bootstrap it).

**Visual and animation.** Bespoke animation: the rendered markdown card types in line by line; step 2 the slice table rows light (red for CI low < 0.5); step 3 three failure chips fly into the Gate field which stamps FAIL (red) and a CI pipeline strip shows the deploy job blocked; step 4 a 'next release' ghost card shows the same fields with diffs highlighted.

**Code.**

```text
lab-synth-eval.md Lab 9 Run block (2 lines) + captured output (20 lines).
```

### 11.06 [gotcha] Eval traps: dropped denominators, shared caches, zero-scored answers

- File: `c11-06-harness-traps.html`
- Id: `custom-c11-harness-traps`

**Content.** Kicker: Gotcha · eval tooling (gotchas.md G1-G8). Three .gotcha cards. (1) Symptom: headline accuracy inflated. Cause: lm-eval drops documents whose process_results returns {} from the mean; refusals and unparseable answers vanish (#4062, open). Fix: score unparseable answers as 0 explicitly and report scored / errored / unscored counts. (2) Symptom: model B shows model A's scores. Cause: --use_cache key = sha256(request_type + args) without model name, revision or model_args (#4063, open). Fix: one cache path per model@sha or cache off for final numbers. (3) Symptom: 'B. 4' and 'ANSWER: B' score 0.0 in mmlu_*_generative; the reporter's repro flips 0.0000 <-> 0.9333 when only the endpoint changes (#4187). Fix: a multiple-choice letter extractor; eyeball 20 filtered predictions. Also: temperature 0 is not deterministic (five byte-identical greedy vLLM requests gave five completions, #54521) -> N >= 3 runs and report variance; Inspect model-graded scorers without a grader role graded with the evaluated model (#4695) -> bind model_role='grader'.

**Visual and animation.** Bespoke animation: an accuracy fraction k/n; step 1 three refusal items leave the denominator and the fraction rises (red 'inflated'); step 2 they return as zeros and the fraction drops back; step 3 a cache box keyed by prompt only serves model A's answer card to model B (red), then the key gains 'model@sha' and splits into two boxes; step 4 an extractor funnel turns 'B. 4' into 'B' (green).

**Code.**

```text
Fix sketch (plain Python, no library API): score = 1.0 if extract_letter(output) == gold else 0.0  # unparseable -> 0.0, never skipped; report {'scored': n_scored, 'errored': n_err, 'unscored': 0}; lm-eval: --use_cache cache/{model}@{sha} (gotchas.md G2 fix).
```

### 11.07 [paper] Small evals need Wilson CIs, re-runs and paired tests

- File: `c11-07-noise-floor.html`
- Id: `custom-c11-noise-floor`

**Content.** Kicker: arXiv Sep 2026. Three .paper cards. (1) 2609.35815 evalstats (20 Sep 2026, verifier-confirmed via HTML): at N < 100 bootstrap CIs under-cover: percentile 88% and BCa 82% coverage at nominal 95%, BCa separated truly tied prompts 12% of the time; defaults: Wilson for binary means, logit t-interval for numeric scores, Bonett-Price for paired binary differences; PPI on a uniformly random human-labelled subset. Monday: pip install evalstats (0.3.3), es.compare(evaldata, factors='prompt'). (2) 2609.33044 'Pinned and Still Unstable' (27 Sep 2026): pinned temperature-0 judges flip ~5% of verdicts overall and ~40% on close calls; 1/5 to 3/4 of adjacent leaderboard positions are statistically indistinguishable. Monday: run the judge 3+ times, publish the flip rate, use 2 judge families. (3) 2609.17394 'Coding Agents Have Converged' (15 Sep 2026): McNemar separates 0 of 29 adjacent SWE-bench Verified pairs. Monday: report rank bands, not point ranks.

**Visual and animation.** Method animation for card 1: 28 CI bars around a true-difference line; step 1 about 12% of them miss the line and flash red (percentile bootstrap); step 2 switch to Wilson + correction and the misses fade to the nominal rate. Step 3: a 500-cell verdict grid re-runs 3 times; ~5% of cells blink, then the close-call band zooms with ~40% blinking. Step 4: an SWE-bench rank ladder whose adjacent rungs merge into bands.

**Code.**

```text
arxiv-eval.md #1 evalstats README snippet (6 lines: import evalstats as es; evaldata = es.load_from(df); result = es.compare(evaldata, factors='prompt'); result.summary()), labelled 'from the README, not executed here'.
```

### 11.08 [industry] Judge audits in production: 99% fewer false alarms, kappa 0.04 to 0.79

- File: `c11-08-judges-in-production.html`
- Id: `custom-c11-judges-in-production`

**Content.** Kicker: In production · LLM-as-judge audits (arxiv-eval.md #5, #6; Anthropic eval guidance in industry.md Part C). MagicSchool AI K-12 product (2609.28478, v1 1 Aug 2026): 21 evaluators, median activation 0.04%; unanimous-fail panels (repeated runs of one judge; fail only if every run fails; split cases to a 'minority report' queue) + softened rubrics (require unambiguity, pervasiveness, simpler checklists) + a human-reviewed must-fail canary set: confirmed false-positive flags -99%, per-flag precision 0.6% -> 49%, egregious-failure capture 100%. Production text-to-SQL pipeline (2609.30290, 9 Sep 2026): the gpt-4o-mini judge had kappa 0.04 on the enriched set (0.42 random), over-flagging 77.1% of faithful cases ('Grade-Hallucination'); best prompt fix only 0.37; self-hosted Qwen3.6-27B 0.72 vs Claude Opus 4.7 0.71 at ~1/300 cost per call; weak + strong judge pairs degraded agreement; 3 strong judges with unanimity routing 0.79 at 89.7% auto-coverage. Anthropic (Jan 2026): start with 20-50 tasks from real failures, give the judge an 'Unknown' option, keep capability and regression suites separate. .cite arxiv.org/abs/2609.28478, /2609.30290, anthropic.com/engineering/demystifying-evals-for-ai-agents.

**Visual and animation.** Animated diagram: an alert queue overflowing with flags (167 per real failure) drains as three levers (panel, rubric U/P/C, canary gate) switch on one per step, while a green 'canary: 100% caught' badge stays lit. Step 4: a kappa thermometer climbs 0.04 -> 0.37 (prompt fix) -> 0.72 (swap judge) -> 0.79 (3-judge unanimity) and a cost meter divides by 300.

### 11.09 [concept] One loop per release: design, generate, select, label, denoise, card

- File: `c11-09-lifecycle.html`
- Id: `custom-c11-lifecycle`

**Content.** Concept slide, <= 3 lines. Line 1: the lifecycle design -> generate -> select -> curate -> label -> denoise -> quality card is one workflow, rerun per release. Line 2: every step in this deck was a lab: contract (Lab 6), synthesize + verify (Lab 9, C10 build), select (Lab 6 active learning, pass-rate filters C05), label agreement + judge correction (Lab 9), denoise (Lab 8 cleanlab), leakage + drift (Lab 7, Lab 8), train (Labs 1-5), quality card (Lab 10). Line 3: the card's hash links the model, the data and the eval.

**Visual and animation.** Large bespoke ring animation (Deck.register, >= 60% canvas): 7 green stage nodes on a ring; a token travels the ring step by step (one stage per presenter step, 7 steps); at each stage a small chip shows the lab and its key number pops (e.g. 'Lab 6: 12 failures quarantined', 'Lab 9: 29 of 40 kept', 'Lab 8: 223 flagged', 'Lab 7: AUC 0.886 -> 0.602', 'Lab 1: 10.09M params', 'Lab 4: TAG 0.581', 'Lab 10: Gate FAIL'). Final: the ring closes into the quality card icon in the centre. step() renders any step directly.

### 11.10 [paper] Open challenges: lost provenance, hidden hacking, drifting judges

- File: `c11-10-open-challenges.html`
- Id: `custom-c11-open-challenges`

**Content.** Kicker: arXiv Sep-Oct 2026 · state of the art and open problems. Three .paper cards. (1) 2610.16152 WildTrace (12 Oct 2026, verifier-confirmed): the best training-data detection method across SFT/DPO/RL stages averages AUC 0.529, close to random. Monday: record provenance (source, license, hash) at ingest; it cannot be inferred later. (2) 2610.28707 SimHack (20 Oct 2026, verifier-confirmed) predicts reward-hacking onset to 11.3% median relative error and finds curricula that train 96.6% longer without hacking, but training-time interventions 'incentivize models to obfuscate'; 2610.10947 RH-Detect: best detector pooled AUROC 0.962, 10.7-15.9 pp lower on multi-turn tool use. Monday: log cheap hack detectors from step 0. (3) 2609.34198 'Frozen Judges, Moving Agents' (28 Sep 2026): judge error changes with agent version; reusing old calibration raises comparison error from 3.8 to 19.5 pts; plus 2610.10619 TestJack: ~34.4% of 'correct' coding trials violate requirements (50.6% -> 33.2%). Monday: re-calibrate the judge for every new model version and audit a random sample of passes. Closing line: portable data, unit-tested rewards and a gated quality card are the parts you own.

**Visual and animation.** Bespoke animation: three 'open problem' gauges: provenance detection AUC needle settles at 0.529 next to a 0.5 random mark; hacking-onset timeline where a predicted onset marker lands within 11.3% of the actual one; a judge-calibration curve that shifts when the agent version toggles v1 -> v2 (error 3.8 -> 19.5). One gauge per step.

### 11.11 [practices] Release checklist: the ten checks the quality card enforces

- File: `c11-11-release-checklist.html`
- Id: `custom-c11-release-checklist`

**Content.** Best practices (lab-synth-eval cross-lab gotchas, gotchas.md G1-G8, arxiv-eval trends, industry.md Part D 31-37). Do: (1) Pre-register slices and a minimum n per slice. (2) Wilson CIs for rates; cluster bootstrap on the unit of resampling. (3) Paired comparisons (paired bootstrap / McNemar) on the same items; compute MDE first. (4) Pass every 'lying default' explicitly: proportion_confint(method='wilson'), krippendorff level_of_measurement, calibration_curve(n_bins=...), TunedThresholdClassifierCV(scoring=...). (5) Calibrate before any threshold reads the probability; re-derive thresholds at production prevalence. (6) Validate the judge against gold human labels per failure mode, with TPR and TNR; correct pass rates (Rogan-Gladen). (7) Report pass@1, pass@k and pass^k (RL sharpens, ThinkingBox pass@20 fell). (8) N >= 3 eval repeats; report flip rate and variance. (9) Keep capability and regression suites separate; retire saturated evals (Anthropic). (10) Gate release on CI lower bounds in code and store one card per (model x eval hash). Config snippet: the GATES dict and sys.exit from Lab 10.

**Visual and animation.** Checks list (stagger, 3 steps). Right: the final quality card from Lab 10 flips from FAIL to PASS as a 'next release' animation fills the thin slices (n bars grow past 30) and the judge kappa crosses 0.60 (illustrative, labelled 'target state').

**Code.**

```text
lab-synth-eval.md Lab 9: GATES = {'min_slice_ci_low': 0.50, 'min_slice_n': 30, 'min_judge_kappa': 0.60} ... sys.exit(0 if not failures else 1).
```
