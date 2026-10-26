# custom-interview: outline (v2)

Deck: **Interview drills: Customizing modern AI: SFT, RL, RAG and data-centric AI**.
Rules: `engine/AUTHORING.md` section 9 (9.6 defines this deck). 29 slides, 5 chapters plus 1 opening slide.
Sources: `research-v2/custom/00-VERIFIED.md` (overrides all), `gotchas.md`, `industry.md`, `arxiv-*.md`, the `lab-*.md` files. Best v1 questions are reused from `archive/v1/custom/slides/*-qa.html`.

## Shared conventions

- Files `slides/cNN-MM-slug.html`, ids `custom-interview-cNN-slug`.
- **QA slide**: kicker `Interview · <area>`. `.qa` x 3. Each `.q` shows at entry; each `.a` is its own `data-step` (1, 2, 3). Each answer: 2-4 short STE sentences, then a tag strip (`.tags`) with the "number to know". Answers name a mechanism, a number and a check. ≤ 45 words of prose per answer. A right-hand strip or a small bespoke SVG shows the key number for the current step (only one caption per step: `data-step="k" data-until="k+1"`).
- **Whiteboard slide**: kicker `<span class="pill">Whiteboard</span> System design`. Step 0: the prompt card (`.panel.k-<tone>`) with requirements and constraints. Steps 1-4: an animated reference architecture (`.diagram`, ≥ 40% of canvas, ≤ 7 labelled wires, labels ≤ 16 chars, ≥ 80 px between nodes) builds left to right; a `.steps-rail` caption per step names what the interviewer wants to hear. Last step: "what fails" gotcha card. Every whiteboard has a `Deck.register` hook that moves a token / pulse along the built path.
- **Debug slide**: kicker `<span class="pill">Debug this</span> <area>`. Step 0: the buggy `.code-wrap.bad` (12-28 lines, complete imports) plus an `.code-wrap.out` pane with the wrong output. Answer steps use `data-focus` to highlight the bug lines (one focus per step), with a `.gotcha` card (Symptom / Cause / Fix) per step and the fixed line(s) in a `.code-wrap.good` on the last step, plus a `.delta`. Output panes say `output · captured run` or `output · illustrative` exactly as the research says.
- Tones: c00/c01 `agent`, c02 `model`, c03 `tool`, c04 `state`, c05 `human`; debug slides `risk`.
- Pins shown on debug slides: trl 1.16.0, peft 0.21.2, transformers 5.20.2, vllm 0.32.0, scikit-learn 1.9.1, scipy 1.18.1, statsmodels 0.15.0.

## Slide list

| # | File | Type | Title |
|---|---|---|---|
| 1 | c00-01-opening.html | opening | Customizing models: the questions interviewers ask in 2026 |
| 2 | c01-01-chapter.html | chapter | Pick the lever before you train |
| 3 | c01-02-knowledge-behavior.html | qa | Knowledge goes to retrieval, behavior goes to training |
| 4 | c01-03-rag-pressure.html | qa | When RAG answers are wrong, test retrieval on its own first |
| 5 | c01-04-training-lever.html | qa | The base model's pass rate picks SFT, RFT or distillation |
| 6 | c01-05-whiteboard-claims.html | whiteboard | Design a claims assistant: cited policy, brand tone, monthly change |
| 7 | c01-06-debug-probe.html | debug | A 48-token cap makes RFT look impossible |
| 8 | c02-01-chapter.html | chapter | Supervised fine-tuning and adapters |
| 9 | c02-02-sft-mechanics.html | qa | Most SFT failures are template, mask or target bugs |
| 10 | c02-03-peft-numbers.html | qa | Know the adapter numbers: params, bytes and forgetting |
| 11 | c02-04-whiteboard-multilora.html | whiteboard | Design per-tenant fine-tuning for 200 enterprise customers |
| 12 | c02-05-debug-lora.html | debug | Three silent defaults turn this LoRA run into a no-op |
| 13 | c03-01-chapter.html | chapter | Reinforcement learning and rewards |
| 14 | c03-02-grpo-mechanics.html | qa | GRPO learns only from groups that disagree |
| 15 | c03-03-reward-hacking.html | qa | Every reward is an attack surface: gate it, hide it, audit it |
| 16 | c03-04-whiteboard-rl-loop.html | whiteboard | Design an RL loop that learns from live product traffic |
| 17 | c03-05-debug-boxed.html | debug | One missing backslash zeroed every brevity reward |
| 18 | c04-01-chapter.html | chapter | Data-centric AI: labels, leakage and synthesis |
| 19 | c04-02-labels-agreement.html | qa | Agreement numbers lie unless you fix the chance and the scale |
| 20 | c04-03-dataset-drift.html | qa | Ask about coverage and provenance, not the row count |
| 21 | c04-04-contamination-synthetic.html | qa | Record provenance at ingest: you cannot detect it later |
| 22 | c04-05-whiteboard-synth-pipeline.html | whiteboard | Design a synthetic QA pipeline that is safe to train on |
| 23 | c04-06-debug-leakage.html | debug | KFold scored 0.886 because customers sat in both folds |
| 24 | c05-01-chapter.html | chapter | Evaluation you can ship on |
| 25 | c05-02-eval-statistics.html | qa | A delta without n, a CI and pairing is not a result |
| 26 | c05-03-llm-judges.html | qa | Treat the LLM judge as an instrument you calibrate |
| 27 | c05-04-thresholds-cost.html | qa | Pick thresholds from costs at production prevalence |
| 28 | c05-05-whiteboard-release-gate.html | whiteboard | Design the eval and release gate for an LLM-judged assistant |
| 29 | c05-06-debug-paired.html | debug | An unpaired bootstrap hid a real 5-point gain |

Mix: 1 opening, 5 chapter openers, 13 QA slides (39 Q&A pairs), 5 whiteboards, 5 debug slides. Bespoke `Deck.register` animations: opening, 5 openers, 5 whiteboards, 2 QA slides (c04-02 kappa bars, c05-03 judge flips) = 13 of 29.

## Chapter 0: Opening

**c00-01-opening** (`custom-interview-c00-opening`, tone agent). Display title, lede: "39 questions, 5 whiteboards, 5 bugs. Each answer names a mechanism, a number and a check." Bespoke animation: five chapter nodes (Lever, SFT, RL, Data, Eval) light up in sequence around a central "your system" node; a pulse travels the loop Data -> SFT/RL -> Eval -> Data. Three tags: "trade-offs", "failure modes", "numbers to know". Notes: how to use the deck (ask, pause, reveal).

## Chapter 1: Choosing the lever (context, RAG, SFT, RL)

Research: `industry.md` (A7 Genie Code, A14 Thinking Machines, Part C AWS/Anthropic), `gotchas.md` H1-H4, `00-VERIFIED.md` (2608.30987, 2610.26951, 2608.22118, 2609.12171), v1 `c01-05-qa`, `c04-06-qa`, `c09-06-qa`.

- **c01-01-chapter**: "Pick the lever before you train". Mini-diagram: a failure card splits into "knowledge" (-> retrieval/context) and "behavior" (-> prompt -> SFT -> RL) branches that draw themselves.
- **c01-02-knowledge-behavior** (qa):
  1. Q: Your support bot quotes the wrong refund policy and sounds too formal. What do you change? A: Two failures. The policy is knowledge: put it in retrieval, so it stays fresh, cited and permissioned. The tone is behavior: fix the prompt, then SFT or DPO. First build 20-50 eval tasks from real failures (Anthropic, Jan 2026).
  2. Q: Why not fine-tune the product catalogue into the weights? A: SFT on facts the base cannot recall raises hallucination (arXiv 2608.30987). Facts go stale. Doc mid-training raised internal QA 18% -> 43% but IFEval fell 85% -> 45%; a 70/30 docs/chat mix plus distillation brought IFEval back to 83% (Thinking Machines).
  3. Q: When does context beat training? A: Databricks Genie Code: 76.6% at $0.55/task vs 72.1% at $1.09 for the best general agent, with no fine-tuning; the gain came from catalog search and table memory. Fix retrieval, memory and tool descriptions first.
  Visual: right strip with three stat tiles that swap per step (20-50 tasks; IFEval 85 -> 45 -> 83; $0.55 vs $1.09).
- **c01-03-rag-pressure** (qa):
  1. Q: Recall@20 is high but answers are still wrong. Where do you look? A: Similarity retrieval finds *any* relevant chunk, not *all* required chunks (arXiv 2610.26951). Score "all evidence retrieved" separately, then faithfulness. Check context order and rerank to a small top-n.
  2. Q: How do you build a RAG eval set fast? A: Synthesize from your corpus (ragas `TestsetGenerator`), then verify: a closed-book leak test, and humans check a sample. Even grounded synthetic enterprise QA is hard: frontier agents stay below 80% on WinSyn (2609.12171). Report per slice.
  3. Q: Your knowledge base now holds pages your own model wrote. Risk? A: RAG collapse: answers collapse when retrieved docs are self-authored, in 79.6% of 1,528 simulations (2608.22118). Tag provenance at ingest and filter or down-rank model-written docs.
  Visual: small animated retrieval diagram per step (query -> 3 chunks with only 1 of 2 required hit; then generator; then a "self-authored" loop that turns red).
- **c01-04-training-lever** (qa):
  1. Q: SFT or reinforcement fine-tuning? A: RFT needs at least one correct answer among several attempts. AWS Bedrock: rewards consistently 0% -> SFT first; above 95% -> RFT may be unnecessary. Start with 100-200 examples.
  2. Q: A strong teacher exists. RL or distillation? A: On-policy distillation reached 74.4% AIME'24 at 1,800 GPU-h; RL reached 67.6% at 17,920 GPU-h (Thinking Machines). The student samples, the teacher scores every token.
  3. Q: Your vendor retires your tuned model. What survives? A: The data with its contract, the graders, the frozen eval and the pinned recipe. `ft-o4-mini` shut down 2026-10-23; OpenAI self-serve fine-tuning closes to new jobs on 2027-01-06. Keep JSONL + Python graders vendor-neutral, re-tune, prove parity on the same eval.
  Visual: animated decision ladder (pass@k = 0 -> SFT; 0 < p < 0.95 -> RFT; teacher -> OPD) with a bar for GPU-h 1,800 vs 17,920.
- **c01-05-whiteboard-claims** (whiteboard). Prompt: "Assistant for insurance-claims agents. Policies change monthly, every answer must cite a policy clause, tone follows brand rules, 3 product lines." Reference architecture steps: (1) versioned policy store -> hybrid retriever + reranker -> generator with citation check; (2) tone via SFT/DPO adapter on approved replies; (3) golden set from real traces, one slice per product line, judge validated against adjusters; (4) monitor query-vs-corpus drift and ship a quality card per release. What fails: stale index after a policy update (fix: re-index on publish, cite version id); citation that points at the wrong clause (fix: deterministic quote check, as Chroma Context-1 checks quotes against source text).
- **c01-06-debug-probe** (debug). `probe_base.py`: probe the base model 8 times per claim before choosing RFT. Bug: `max_tokens=48` cuts the reasoning before `\boxed{}`, so every rollout fails and the script says "run SFT first". Step 1 focus: the `SamplingParams` line. Step 2 focus: the decision block that never checks `finish_reason == "length"`. Fix: `max_tokens=384` and print the truncated share. Output illustrative.

## Chapter 2: SFT and PEFT

Research: `lab-sft.md` Labs 1-5, 8; `gotchas.md` A1-A6, A8-A9, A13; `00-VERIFIED.md` rows 19, 2609.25618, 2609.36569, 2608.23816; v1 `c02-07-qa`.

- **c02-01-chapter**: "Supervised fine-tuning and adapters". Mini-diagram: a chat transcript whose user tokens grey out (mask) and assistant tokens glow (loss), then a small LoRA A x B pair attaches to a frozen block.
- **c02-02-sft-mechanics** (qa):
  1. Q: After SFT the model never stops generating. Why? A: The trained EOS is not the template's end-of-turn token (`<|im_end|>` for Qwen), so the stop token never got loss. Set `SFTConfig(eos_token="<|im_end|>")`. Test: the last token id of one formatted example equals `<|im_end|>`.
  2. Q: What does `assistant_only_loss=True` need? A: `{% generation %}` markers in the chat template. TRL 1.16.0 patches Qwen3, not Gemma 4. Check: decode the tokens where `labels != -100` and assert no user text.
  3. Q: A LoRA run finishes, but nothing changed. DPO loss stayed at 0.6931. Why? A: 0.6931 = ln 2: policy equals reference. PEFT's default targets on Nemotron-H hit 4 of 56 layers, and a partial match is silent. Assert adapter coverage per layer.
- **c02-03-peft-numbers** (qa):
  1. Q: LoRA r=16 on Qwen3-0.6B: how many trainable params? A: All-linear: 10,092,544 (1.665%): r x (in + out) x 7 modules x 28 layers. PEFT's qwen3 default (q/v only): 2,293,760 (0.38%). Use LR about 10x the full-FT default (2e-4 vs 2e-5).
  2. Q: Where does QLoRA save memory, and what is the silent default? A: Full FT with AdamW needs about 16 bytes/param: a 4B model is 16.1 + 16.1 + 32.2 GB, about 64 GB before activations. QLoRA freezes the base in 4-bit; but `BitsAndBytesConfig` defaults to `fp4`, so set `nf4`. QLoRA saves memory, not time (AQLoRA 2608.23816).
  3. Q: You fine-tune a post-RL reasoning model and reasoning collapses. What happened? A: Plain LoRA SFT erased it: 63.8% -> 8.3% (3B), 80.1% -> 9.4% (1.5B) (2609.25618); null-basis LoRA preserves it. Choose checkpoints on generation, not NLL (+0.71/+0.85 pp, 2609.36569).
  Visual: animated parameter bar (2.29M vs 10.09M), then a memory stack (weights/grads/Adam) for 4B.
- **c02-04-whiteboard-multilora** (whiteboard). Prompt: "200 enterprise tenants each want a tuned assistant. One GPU pool, new adapters weekly, no tenant may see another's behavior." Steps: (1) tenant data -> contract + template/mask CI check -> LoRA SFT job per tenant (adapter ~40 MB, not a model copy); (2) adapter registry with key-diff load check and golden-output test (adapter must differ from base on 5 prompts); (3) eval gate: `disable_adapter()` A/B on the same weights, plus a general regression set; (4) serving: shared base on vLLM `--enable-lora` with per-request adapter. What fails: `PeftModel.from_pretrained` drops unexpected keys and `strict=True` does nothing (PEFT #3804); transformers v5 renames break adapters in vLLM (PEFT #3896): CI loads the adapter in the serving engine and compares logprobs.
- **c02-05-debug-lora** (debug). `sft_refund.py` on Bitext REFUND (2,992 rows). Bugs: (1) `LoraConfig` without `target_modules` -> q/v only, `trainable params: 2,293,760 || all params: 598,343,680 || trainable%: 0.3833`; (2) `learning_rate=2e-5` is the full-FT default; (3) no `model_init_kwargs={"dtype": torch.bfloat16}` -> a string model id loads in float32. Fixed output: `trainable params: 10,092,544 || all params: 606,142,464 || trainable%: 1.6650` (exact arithmetic, verified).

## Chapter 3: RL, preference tuning and rewards

Research: `lab-rl.md` Labs 1, 2, 4, 6; `gotchas.md` B1-B2, B12-B14, G9; `industry.md` A2, A4, A8, A13, Part D; `00-VERIFIED.md` 2610.21404, 2610.25812, 2610.19832, 2610.10619, 2610.30765; v1 `c03-08-qa`, `c09-06-qa`.

- **c03-01-chapter**: "Reinforcement learning and rewards". Mini-diagram: one prompt fans out to 8 rollouts, rewards drop onto them, the group mean line appears, and above/below-mean rollouts turn green/red.
- **c03-02-grpo-mechanics** (qa):
  1. Q: Why does GRPO not need a critic, and what does that cost? A: The group's reward mean (and std) is the baseline. You save the value model, but you sample G completions per prompt, and all-0 or all-1 groups give zero gradient. Watch `frac_reward_zero_std`; keep prompts with base pass rate 0.08 to < 0.90 (ThinkingBox).
  2. Q: Reward is noisy and length collapses. What do you read? A: `completions/clipped_ratio`: truncated answers score 0 even when on track. `max_completion_length` defaults to 512 and `mask_truncated_completions` to False. Above ~10%, raise the length or mask. Batch must hold whole groups: `generation_batch_size must be divisible by num_generations`.
  3. Q: GRPO or rejection-sampling fine-tuning on the same prompts and verifier? A: GRPO wins by up to 10.9 points; iterated RFT recovers ~30% of the gap (2610.25812). But RL sharpens, it does not broaden: ThinkingBox pass@1 51.70% -> 60.78%, pass@20 89.35% -> 87.97%.
- **c03-03-reward-hacking** (qa):
  1. Q: Total reward rises, accuracy falls, with correctness + brevity rewards. Why? A: Additive aggregation drifts to the easier auxiliary (2610.21404). Gate the auxiliary on correctness: TAG reached 0.581 vs 0.220 pass@4. Log each reward channel; alert when primary falls while total rises.
  2. Q: DPO `logps/chosen` falls during training. Is it a bug? A: Not necessarily. DPO mostly pushes the rejected answer down, so the margin grows while both log-probs fall. Watch `rewards/margins` and an eval. Add an SFT term: `loss_type=["sigmoid", "sft"]`.
  3. Q: How do you harden rewards for an agentic coding RL run? A: Hidden tests the policy never sees: ~34.4% of "correct" trials violate requirements (50.6% -> 33.2%, TestJack). Make tests and graders read-only in the sandbox. Red-team the grader (Cognition). Count broken tool calls as negatives (Cursor). Audit often: RL turned 41-66% of proxy gain into "rent" (2610.19832).
- **c03-04-whiteboard-rl-loop** (whiteboard). Prompt: "Your coding assistant has 1M daily users. Improve it with RL from live traffic, ship several times a day, and do not ship a reward hack." Reference (Cursor real-time RL): (1) serve checkpoint -> collect interactions; (2) distill reward signals: edit persisted, dissatisfied follow-up, latency; (3) GRPO update in the production harness with sandboxed tools; (4) eval gate (regression suite + behavior monitors: edit rate, clarifying-question rate) -> deploy; about 5 h per cycle. Numbers: edit persists +2.28%, dissatisfied follow-ups -3.13%, latency -10.3% (Composer 1.5 A/B). What fails: broken tool calls to dodge negative reward; asking clarifying questions to avoid risky edits. "Each attempted reward hack ... becomes a bug report."
- **c03-05-debug-boxed** (debug). `lab4_rewards.py`, the correctness-gated brevity reward. Bug: `BOX_RE = re.compile(r"\boxed\{([^{}]*)\}")`: in a raw regex `\b` is a word boundary, so it never matches a real `\boxed{8500}`; every answer counts as wrong and brevity is always 0. Buggy output: `brevity/gated_frac 1.0`, `[0.0, 0.0, 0.0]`. Fix: `r"\\boxed\{([^{}]*)\}"`. Captured run: `brevity/gated_frac 0.3333333333333333`, `brevity/ramp 0.5`, `[0.4166666666666667, 0.0, 0.08333333333333331]`. Step 2: the same `\b` in a non-raw prompt string is a backspace (`\x08`), found in `claims_data.SYSTEM`. Lesson: a self-test with a real model-style string per reward.

## Chapter 4: Data-centric AI

Research: `lab-data.md` Labs 2, 4, 5, 7, 8; `lab-synth-eval.md` Lab 8; `gotchas.md` C3, D1-D3, E1-E3, F1; `industry.md` A6 KARL, A12 Chroma; `00-VERIFIED.md` 2610.21229, 2610.16152, 2609.32546, 2609.33878, 2609.25487, 2610.09820; v1 `c05-06-qa`, `c06-07-qa`, `c07-07-qa`.

- **c04-01-chapter**: "Data-centric AI: labels, leakage and synthesis". Mini-diagram: rows flow through contract -> dedup -> label audit -> split; a red duplicate row is caught between train and test.
- **c04-02-labels-agreement** (qa, bespoke animation):
  1. Q: Raw agreement is 92% but Cohen's kappa is 0.3. Who is right? A: Both. With a skewed prior, chance agreement p_e is high, so kappa = (p_o - p_e)/(1 - p_e) is low (the kappa paradox). Report both and the minority-class agreement.
  2. Q: Krippendorff's alpha came out 0.083 on 3 category labels. Is the rubric broken? A: Check the call. `krippendorff.alpha` defaults to `level_of_measurement="interval"`. The same data gives 0.542 as nominal. Pass the level explicitly; use ordinal for 1-5 scales.
  3. Q: How do you use an LLM as a labeler safely? A: Pin the judge version: newer backbones are not consistently better relevance judges (2610.09820). Keep a 200-item human anchor set; re-measure kappa on every upgrade. Two agreeing local judges with separate thresholds gave 96.88% label purity at 81.7% coverage (2609.33878).
  Bespoke: a bar pair (p_o vs p_e) whose gap draws kappa; then the 0.083 bar grows to 0.542 when the level flips to "nominal".
- **c04-03-dataset-drift** (qa):
  1. Q: "We have 50k SFT rows, ready to train." What do you ask? A: Coverage per taxonomy leaf, provenance and license per subset, synthetic share and generator, the contract per shard, eval slices with min n, and decontamination against the evals.
  2. Q: Your KS test flags drift on every column every day. Why? A: At large n a p-value flags tiny shifts. In the lab, `days_since_order` had PSI 0.003 (stable) but KS p = 0.02. Use distance thresholds calibrated reference vs reference, and tie each alert to a slice metric.
  3. Q: cleanlab flags 3% of support tickets as mislabeled. Delete them? A: Not blindly. Compute `pred_probs` out-of-sample (`cross_val_predict`, cv=5), or the model has memorized the noise. Removing apps flagged by 3 detectors did not improve the Google Play model (2609.25487): review, relabel, then re-measure.
- **c04-04-contamination-synthetic** (qa):
  1. Q: You decontaminate RL math data at embedding cosine 0.80. Good? A: No. At 0.80, 88% of sampled removals were false; no threshold in 0.80-0.98 reached 90% precision. Use candidates (n-gram/embedding), then a judge adjudicates: 98.1% precision, 98.2% recall (2610.21229).
  2. Q: Can you prove after training that a test set was not in the data? A: Not reliably: post-training data detection averages AUC 0.529 (WildTrace, 2610.16152). Record provenance at ingest, pin `revision=`, and store your own sha256: `datasets` 4.8.5 stopped recording checksums by default.
  3. Q: How do you stop synthetic data from collapsing? A: Seed from real data, stratify by an attribute grid, keep a fresh human share. Generate one record per call: 10 per call inflated correlation error 48-127% (2609.32546). Measure diversity against the real set.
- **c04-05-whiteboard-synth-pipeline** (whiteboard). Prompt: "Train an enterprise knowledge agent with RL. You have the document corpus, few labels, and a frozen eval set." Reference (Databricks KARL): (1) Q-A synthesis agent over vector search, seeded by a few examples; (2) dedup/decontam agent against eval and few-shot sets; (3) solver agents x N, drop questions all solve or none solve; (4) quality-filter agent removes ambiguous or wrong-reference items -> RL -> the improved agent synthesizes the next round. Numbers: KARL 58.9 vs base 52.6 on KARLBench; 67.5 with 10 parallel traces (= Claude 4.6 Opus) at ~33% lower cost. What fails: "never solved" items are often broken, not hard: send them to review; decontam by cosine alone throws away good data (88% false removals).
- **c04-06-debug-leakage** (debug). `lab7_leakage_splits.py`, refund-fraud model, 400 customers x 15 events. Bug: `cross_val_score(model, X, y, cv=KFold(5, shuffle=True, random_state=0))`: the same customer's fingerprint sits in train and test. Captured run: KFold ROC-AUC 0.886 +/- 0.025 vs GroupKFold 0.602 +/- 0.075. Step 2 focus: the fix `groups=df["customer_id"], cv=GroupKFold(n_splits=5, shuffle=True, random_state=0)`. Step 3: the executable leakage assert for the time split. `.delta` -0.284 AUC "pure memorization".

## Chapter 5: Evaluation, judges and release gates

Research: `lab-synth-eval.md` Labs 3, 4, 6, 7, 8, 9; `gotchas.md` G1, G8; `industry.md` A8 Shopify; `00-VERIFIED.md` 2609.17394, 2609.35815, 2609.33044, 2610.30512, 2609.22512, 2610.21128, 2609.30290, 2610.31657; v1 `c08-06-qa`.

- **c05-01-chapter**: "Evaluation you can ship on". Mini-diagram: two score bars with overlapping CI whiskers, then pairing lines connect item to item and the CI shrinks.
- **c05-02-eval-statistics** (qa):
  1. Q: How many items do you need to detect a 2-point change? A: Do a power analysis first: MDE is about 2.8 x SE of the delta. With 400 paired items the refund lab could detect only about 7 points (unpaired: 8.5). Pair on the same items to cut SE.
  2. Q: Two adjacent agents on the SWE-bench Verified leaderboard. Which is better? A: Usually nobody can say: McNemar separates 0 of 29 adjacent pairs (2609.17394). Report paired tests on discordant items, not rank.
  3. Q: A slice has 25 items. Which CI do you report? A: Not a plain bootstrap: at N < 100, percentile and BCa CIs covered only 88% and 82% (2609.35815). Use Wilson, and a cluster bootstrap when items share a conversation. A 56% Spanish-health slice can hide under an 84% headline.
- **c05-03-llm-judges** (qa, bespoke animation):
  1. Q: How do you trust an LLM judge? A: Calibrate against several experts with kappa, using human-human agreement as the ceiling. Shopify iterated judge prompts from kappa 0.02 to 0.61 against a 0.69 ceiling. A production text-to-SQL judge had kappa 0.04; an open judge reached 0.72 at ~1/300 cost (2609.30290).
  2. Q: Is a pinned temperature-0 judge deterministic? A: No. Pinned judges flip ~5% of verdicts, ~40% on close calls (2609.33044). Re-running Arena-Hard's judge flipped 21.2% of prompt outcomes while the aggregate moved ~1 point. Run N >= 3, report the flip rate.
  3. Q: Five judges agree. Is that strong evidence? A: Less than it looks. Judge errors correlate (mean 0.21), so 10 judges act like ~3.5 independent ones (2609.22512). 60% of wrong answers sat in the high-consistency region (2610.21128). Agreement is not accuracy.
  Bespoke: a grid of 40 verdict cells re-runs; ~5% flip overall, close-call row flips ~40% (2 of 5 cells).
- **c05-04-thresholds-cost** (qa):
  1. Q: A missed fraud costs $120, a false hold $15. Which threshold? A: With calibrated probabilities, t* = C_FP/(C_FP + C_FN) = 15/135 = 0.111. Moving from 0.5 to the cost-tuned threshold cut cost 31% ($10.72 -> $7.38 per case).
  2. Q: The eval set is enriched to 10% fraud; production has 2%. Does it matter? A: Yes. FPR and FNR do not depend on prevalence, but cost does. The eval-tuned threshold cost 66% more in production ($3.10 vs $1.86 per case). Re-derive t at production prevalence.
  3. Q: When should the model defer to a human instead of answering? A: When expected cost of acting exceeds review cost. Cost-aware abstention with a (0, 1, 5) cost model, threshold frozen on calibration data, cut cost 0.763 -> 0.472 (-38.1%) and wrong routes 15.3% -> 3.5% (2610.31657).
- **c05-05-whiteboard-release-gate** (whiteboard). Prompt: "An HR-policy assistant ships weekly. Human review cannot scale. Design the eval and the release gate." Reference: (1) golden set from real traces + human anchor set (labelled by 2+ experts); (2) judge calibrated vs anchor (kappa, TPR/TNR), version pinned, N >= 3 runs; (3) paired comparison vs current model with CIs, per-slice Wilson CIs; (4) quality card per model x eval hash -> CI gate `sys.exit(1)` if CI-low < 0.5 or judge kappa < 0.6. What fails: unscorable answers leave the denominator (lm-eval #4062): count them as 0; the eval cache keyed without the model name serves A's answers as B's (lm-eval #4063).
- **c05-06-debug-paired** (debug). `lab4_paired.py`: refund agent v1 vs v2 on the same 400 cases. Bug: `stats.bootstrap((b, a), diff_of_means, paired=False, ...)` treats matched items as independent; CI [-0.007, +0.110] crosses 0 and the script says "no evidence, keep v1". Fix: `paired=True` -> CI [+0.005, +0.102]; McNemar exact p = 0.0460 on 40 vs 61 discordant pairs. Step 2: dropping 3 crashed rows breaks pairing (`ValueError: When paired is True, all samples must have the same length along axis`): score crashes as 0 and align on item_id. Captured run (scipy 1.11.4 with `random_state=`).
