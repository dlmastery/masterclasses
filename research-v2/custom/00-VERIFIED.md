# 00-VERIFIED: verification pass over `research-v2/custom` (2026-10-23)

Scope: all 9 files in this folder (`lab-sft.md`, `lab-rl.md`, `lab-data.md`, `lab-synth-eval.md`, `arxiv-sft-rl.md`, `arxiv-data.md`, `arxiv-eval.md`, `gotchas.md`, `industry.md`).

How I checked:
- **Library versions.** PyPI JSON, fetched this session. All 27 pinned versions in the labs match the latest PyPI release. Examples: trl 1.16.0, peft 0.21.2, transformers 5.20.2, google-genai 2.33.0, openai 3.37.0, vllm 0.32.0, unsloth 2026.10.8, pandera 0.34.1, evidently 0.7.23, cleanlab 2.9.0, scikit-learn 1.9.1, datasketch 2.0.0, krippendorff 0.9.0, statsmodels 0.15.0, scipy 1.18.1, distilabel 1.5.3, ragas 0.4.3, evalstats 0.3.3.
- **Code.** I read the library source at the release tag through `raw.githubusercontent.com/<org>/<repo>/<tag>/...`. The exception is Unsloth: no release tag resolved, so I read `main` (PyPI 2026.10.8 is from today). I compiled every Python code block. I re-ran the CPU-only labs this machine can run: RL Labs 1, 3 and 4 (reward self-tests), Data Lab 2, Synth/Eval Lab 7 and the Synth Lab 1 `run_tests`. All outputs matched the files byte for byte.
- **arXiv.** One batched arXiv API call (`id_list=` with all 190 IDs found in the folder). All 190 IDs exist. 180 have a v1 date inside 2026-07-23..2026-10-23. 9 are older background references and are labelled as such. 1 was cited as in-window but is not, so I removed it.
- **Numbers.** I spot-checked 18 headline numbers against the arXiv abstract, and against the arXiv HTML full text where the abstract lacked them. Two more came from HF config and the dataset API. All 20 confirmed.

---

## 1. Corrections table (all applied in place)

| # | File | Location | Was | Now / action | Evidence |
|---|---|---|---|---|---|
| 1 | lab-rl.md | Lab 4 `lab4_rewards.py` | `BOX_RE = re.compile(r"\boxed\{...\}")` | `re.compile(r"\\boxed\{...\}")` | In a raw regex, `\b` is a word boundary, so the pattern needs "oxed" right after a boundary. It **never matches a real `\boxed{8500}`** in model output. Verifier test: old pattern on real text `[]`, fixed `['8500']`. The brevity reward was always 0. |
| 2 | lab-rl.md | Lab 4 self-test strings | `"...so \boxed{8500}"` (non-raw) | `r"...so \boxed{8500}"` | In a non-raw string, `\b` is a backspace (`\x08`). The old test only passed because of that bug. After the fix, the re-run output is unchanged: `[0.4166..., 0.0, 0.0833...]`. |
| 3 | lab-rl.md | Lab 2 `claims_data.py` `SYSTEM` | `"... give the payout as \boxed{number}."` | raw string `r"..."` | The prompt actually held `'\x08oxed{number}'` (verified with `repr`). The model was told to answer in a garbled format, and `accuracy_reward` needs `\boxed`. |
| 4 | industry.md | Part B, "other in-window titles" | CompactionRL (2607.05378) | removed | arXiv API v1 date is 2026-07-06, outside the window. |
| 5 | arxiv-sft-rl.md | #19 2610.23946 | "submitted 19 Oct 2026 (v2 20 Oct)" | v1 8 Oct 2026 | arXiv API `published` |
| 6 | arxiv-sft-rl.md | #5 2610.21179 | 14 Oct | 15 Oct | arXiv API |
| 7 | arxiv-sft-rl.md | #6 2610.19525 | 13 Oct | 14 Oct | arXiv API |
| 8 | arxiv-sft-rl.md | #12 2610.21337 | "v1 Oct 2026" | v1 15 Oct 2026 | arXiv API |
| 9 | arxiv-sft-rl.md | #15 2609.25618 | 21 Sep | 22 Sep | arXiv API |
| 10 | arxiv-sft-rl.md | #20 2610.25651 | 18 Oct | 19 Oct | arXiv API |
| 11 | arxiv-sft-rl.md | hon. 2610.14448 / 2610.22887 / 2610.15778 / 2610.11132 | 9 / 19 / 14 / 7 Oct | 10 / 16 / 11 / 8 Oct | arXiv API |
| 12 | arxiv-data.md | #3 2610.19447, #4 2610.27533, #10 2609.31857 | 10-13 / 10-19 / 09-28 | 10-14 / 10-20 / 09-25 | arXiv API |
| 13 | arxiv-eval.md | #2 2609.33044, #13 2609.31857, hon. 2610.21128 | 09-30 / 09-28 (v2) / 10-14 | 09-27 / 09-25 (v1) / 10-15 | arXiv API |
| 14 | arxiv-eval.md | #6 2609.28478 | "2026-09-30 (v2)" | v1 2026-08-01 (v2 09-30) | arXiv API. Still inside the window. |
| 15 | all lab files | under every `## Lab N:` heading | none | added a `> **Verifier (2026-10-23):**` stamp line | 33 labs stamped |

**Not errors, but worth knowing:**
- **lab-sft Lab 1 is correct.** In `get_training_chat_template`, TRL 1.16.0 patches `gemma` and `gemma3` but **not Gemma 4**, even though `gemma4*.jinja` files exist. It does patch `qwen3` and `qwen3_instruct_2507`.
- **lab-synth Lab 2 follows the ragas 0.4.3 docs exactly** (`OpenAIEmbeddings(client=...)`). But `ragas.embeddings.OpenAIEmbeddings` subclasses `BaseRagasEmbedding`, while `TestsetGenerator.embedding_model` is typed `BaseRagasEmbeddings`. Runtime compatibility is [UNVERIFIED].
- **vLLM `--lora-modules` parser.** It is in `vllm/entrypoints/common/cli_args.py` on `main`, but that path 404s at tag `v0.32.0`. The flag itself is long-standing. The file path at the tag is [UNVERIFIED]; the GitHub API was rate-limited.
- **Window edge.** 2607.21351 and 2607.21861 have v1 = 2026-07-23, the first day of the window. They are kept.

---

## 2. Verified labs (file, lab, versions)

| File | Lab | Status | Checked against |
|---|---|---|---|
| lab-sft.md | 1 Chat template + assistant mask (HR) | VERIFIED | trl 1.16.0, transformers 5.20.2 |
| lab-sft.md | 2 LoRA SFT, assistant-only loss + BFD packing (refunds) | VERIFIED; 10,092,544 trainable recomputed | trl 1.16.0, peft 0.21.2, transformers 5.20.2, Qwen3-0.6B config.json |
| lab-sft.md | 3 QLoRA NF4, prompt-completion (claims JSON) | VERIFIED; 33,030,144 recomputed. Unverified: T4 bf16 error text | trl 1.16.0, transformers 5.20.2 |
| lab-sft.md | 4 Before/after eval with `disable_adapter` | VERIFIED | peft 0.21.2 |
| lab-sft.md | 5 Merge + logit check + vLLM serve | VERIFIED. Unverified: `--lora-modules` file path at tag | peft 0.21.2, vllm 0.32.0 |
| lab-sft.md | 6 Unsloth Gemma 4 E2B triage + GGUF | VERIFIED on `main` (no tag) | unsloth / unsloth-zoo main (PyPI 2026.10.8) |
| lab-sft.md | 7 Vertex Gemini managed SFT | VERIFIED (SDK). Unverified: gcloud CLI group | google-genai 2.33.0 |
| lab-sft.md | 8 TRL CLI sweep (YAML) | VERIFIED | trl 1.16.0, peft 0.21.2 |
| lab-rl.md | 1 Unit-tested refund rewards | VERIFIED + re-run | trl 1.16.0 (reward contract) |
| lab-rl.md | 2 GRPO + math-verify (claims payout) | VERIFIED; **fixed** `SYSTEM` escape. Unverified: `trackio show` | trl 1.16.0 (`trl[vllm]` pins vllm <=0.31.0) |
| lab-rl.md | 3 GRPO + code-execution reward (ticket router) | VERIFIED + re-run | trl 1.16.0 |
| lab-rl.md | 4 KL on/off, gated brevity, tripwire | VERIFIED; **fixed** regex bug; re-run | trl 1.16.0, transformers 5.20.2 |
| lab-rl.md | 5 Reward model with margins, then RM as GRPO reward | VERIFIED. Unverified: 2 error texts | trl 1.16.0 |
| lab-rl.md | 6 DPO + LoRA, sigmoid+sft losses | VERIFIED | trl 1.16.0 |
| lab-rl.md | 7 OpenAI graders + RFT | VERIFIED (SDK); job path dead (o4-mini retired today) | openai 3.37.0 |
| lab-rl.md | 8 Vertex Gemini RFT + `validate_reward` | VERIFIED (SDK) | google-genai 2.33.0 |
| lab-data.md | 1 pandera claims contract | VERIFIED | pandera 0.34.1 |
| lab-data.md | 2 PSI + KS by hand | VERIFIED + re-run (identical) | numpy/scipy |
| lab-data.md | 3 Evidently drift report + CI gate | VERIFIED | evidently 0.7.23 |
| lab-data.md | 4 cleanlab `find_label_issues` | VERIFIED | cleanlab 2.9.0 |
| lab-data.md | 5 Cohen / Fleiss / Krippendorff | VERIFIED | krippendorff 0.9.0, statsmodels 0.15.0 |
| lab-data.md | 6 Margin active learning | VERIFIED (sklearn). Unverified: skactiveml variation | scikit-learn 1.9.1 |
| lab-data.md | 7 GroupKFold / TimeSeriesSplit leakage | VERIFIED | scikit-learn 1.9.1 |
| lab-data.md | 8 MinHash LSH dedup + decontam | VERIFIED | datasketch 2.0.0 |
| lab-synth-eval.md | 1 distilabel generate-execute-filter | VERIFIED (imports + `run_tests` re-run); LLM part not run | distilabel 1.5.3 |
| lab-synth-eval.md | 2 ragas RAG test set + verification | VERIFIED vs docs. Unverified: embedding type compatibility | ragas 0.4.3 |
| lab-synth-eval.md | 3 Slice metrics, Wilson + cluster bootstrap | VERIFIED | statsmodels 0.15.0 |
| lab-synth-eval.md | 4 Paired vs unpaired bootstrap, McNemar | VERIFIED | scipy 1.18.1, statsmodels 0.15.0 |
| lab-synth-eval.md | 5 ECE + sigmoid/isotonic/temperature | VERIFIED | scikit-learn 1.9.1 |
| lab-synth-eval.md | 6 Cost-matrix threshold + prevalence shift | VERIFIED | scikit-learn 1.9.1 |
| lab-synth-eval.md | 7 Route-or-defer on cost | VERIFIED + re-run (identical) | scikit-learn 1.8.0 run / 1.9.1 API |
| lab-synth-eval.md | 8 LLM-judge agreement + Rogan-Gladen | VERIFIED | krippendorff 0.9.0, scikit-learn 1.9.1 |
| lab-synth-eval.md | 9 Quality card + release gate | VERIFIED | statsmodels 0.15.0, pandas |

---

## 3. Spot-check of the most important numbers (20 checked, 20 confirmed)

| # | Claim in the files | Source checked | Result |
|---|---|---|---|
| 1 | TAG gating 0.581 vs 0.220 pass@4, 44% shorter (2610.21404) | abstract | confirmed |
| 2 | Cost-aware abstention: 0.763 to 0.472 (-38.1%, CI 35.7-40.4), wrong routes 15.3% to 3.5%, LLM AUROC 0.500 (2610.31657) | abstract | confirmed |
| 3 | GRPO beats tuned RFT by 10.9 pts; iterated RFT recovers ~30% (2610.25812) | abstract | confirmed |
| 4 | Generation-based checkpoint selection +0.71 / +0.85 pp over NLL (2609.36569) | abstract | confirmed |
| 5 | Answer-Only RMs won "seven of eight" settings (2610.30765) | abstract | confirmed |
| 6 | Rubric clarification: inter-judge alpha +0.069 (CI 0.046-0.092), 129,770 requests (2610.13303) | abstract | confirmed |
| 7 | AI share of filtered web 27.5% (Jun) / 31.1% (Aug); FineWeb 2.3x, DCLM 9.8x; 1.6x to 3.0x compute (2609.40295) | abstract + HTML | confirmed |
| 8 | Decontam at cosine 0.80: 88% false removals; adjudicated 98.1% P / 98.2% R over 1,673,514 items (2610.21229) | abstract | confirmed |
| 9 | Judge error correlation 0.21, so 10 judges ~ 3.5 (2609.22512) | abstract | confirmed |
| 10 | SimHack 11.3% median error, 96.6% longer training (2610.28707) | abstract | confirmed |
| 11 | NB-LoRA: plain LoRA drops reasoning 63.8% to 8.3% (3B), 80.1% to 9.4% (1.5B); 6.3x faster (2609.25618) | HTML | confirmed |
| 12 | Bootstrap CI coverage 88% (percentile) / 82% (BCa), 12% false separation (2609.35815) | HTML | confirmed |
| 13 | BenchDoor ASR 82.33-100%, >=90.33% after decontam, 30/30 configs (2610.27533) | abstract | confirmed |
| 14 | LOOM +2.3 / +2.4 over full batch; noise picked at under 1/5 base rate (2610.00436) | abstract | confirmed |
| 15 | Pinned judges flip ~5% overall, ~40% on close calls (2609.33044) | abstract | confirmed |
| 16 | Text-to-SQL production judge kappa 0.04; open judge 0.72; 3-judge 0.79 (2609.30290) | abstract | confirmed |
| 17 | TestJack ~34.4% of "correct" trials violate requirements (50.6% to 33.2%) (2610.10619) | abstract | confirmed |
| 18 | WildTrace detection average AUC 0.529 (2610.16152) | abstract | confirmed |
| 19 | Qwen3-0.6B LoRA r=16 all-linear = 10,092,544 params; q/v-only = 2,293,760; Qwen3-4B = 33,030,144 | HF `config.json` + arithmetic | confirmed |
| 20 | Bitext customer-support dataset = 26,872 rows | HF datasets-server `/size` | confirmed |

I did not re-fetch these (they come from vendor docs and blogs, not from code or arXiv): the Vertex/OpenAI/Bedrock limits and the industry case-study numbers (Cursor, KARL, Shopify, ThinkingBox, and others). Treat them as checked by the original agents only.

---

## 4. 25 strongest slide candidates (hands-on, code-first)

| # | Slide | Source (file / lab) | Why it lands |
|---|---|---|---|
| 1 | "What does SFT actually train on?" Print the TRAIN/mask spans of a Qwen3 chat (`get_training_chat_template` + `return_assistant_tokens_mask`) | lab-sft L1 | CPU-only, 30 lines, makes masking visible; doubles as a CI check |
| 2 | LoRA SFT in 25 lines: `SFTConfig(assistant_only_loss, packing_strategy="bfd")` + `LoraConfig(target_modules="all-linear")`; 10.1M vs 2.3M params gotcha | lab-sft L2 | Real dataset (Bitext REFUND, 2,992 rows); exact param arithmetic |
| 3 | QLoRA: `nf4` is not the default (`fp4` is) | lab-sft L3 | One-line silent-default gotcha, verified in source |
| 4 | Same weights, adapter on/off: `with model.disable_adapter():` before/after table | lab-sft L4 | Honest A/B pattern; pairs with 2609.36569 (select on generation, not loss) |
| 5 | Merge + assert same greedy tokens, then `vllm serve --enable-lora --lora-modules` | lab-sft L5 | Deployment gate students can copy |
| 6 | Defaults differ: TRL CLI 16/32/0.05 vs PEFT 8/8/0.0 vs Unsloth 16/16 | lab-sft L8 | Table slide; explains "my r=16 is not your r=16" |
| 7 | Unit-test your reward before the GPU: the "schema-less 0.5" hack caught by a test | lab-rl L1 | Runnable, real output, memorable bug |
| 8 | GRPO + `accuracy_reward` + soft overlong penalty; read `frac_reward_zero_std` and `clipped_ratio` | lab-rl L2 | Metric-reading slide using verified TRL metric names |
| 9 | Code-execution reward in a subprocess; the lazy `return 'billing'` earns 0.25 | lab-rl L3 | Partial-credit attractor shown with real numbers |
| 10 | Gate auxiliary rewards on correctness (TAG 0.581 vs 0.220) + a `\boxed` regex bug the verifier found | lab-rl L4 + 2610.21404 | Code + paper + a real bug; great "gotcha" moment |
| 11 | Reward model with margins and `modules_to_save=["score"]`; do not pick RMs by static accuracy (2610.30765) | lab-rl L5 | Code + counter-intuitive finding |
| 12 | DPO with `loss_type=["sigmoid","sft"]`; why `rewards/margins` rise while `logps/chosen` fall; ECHO collapse | lab-rl L6 + 2610.29410 | Teaches reading DPO logs |
| 13 | Vertex RFT: `validate_reward` as CI for a reward function | lab-rl L8 | Managed-service hands-on; ties to Lab 1 |
| 14 | pandera contract with `lazy=True`: one report, 12 failure cases, quarantine rows | lab-data L1 | Captured run; data-contract chapter anchor |
| 15 | PSI vs KS at large n: "stable" PSI 0.003 but KS p=0.02 | lab-data L2 | Re-run by verifier; crisp p-value vs distance lesson |
| 16 | Evidently CI gate: dataset drift "passes" while `product_area` drifted | lab-data L3 | Shows why per-column tests matter |
| 17 | cleanlab on out-of-sample `pred_probs`; Windows `n_jobs` hang | lab-data L4 + 2609.25487 | Flagged != delete, with code |
| 18 | Krippendorff default is `interval`: 0.083 vs 0.542 nominal on the same data | lab-synth L8 / lab-data L5 | One-line silent-default gotcha |
| 19 | KFold 0.886 vs GroupKFold 0.602 on the same model | lab-data L7 | Leakage made visible; 2610.07059 (R² 0.994 to -0.20) as the paper echo |
| 20 | MinHash dedup + decontaminate train against test; datasketch 2.0 scheme change | lab-data L8 + 2610.21229 | Code + "88% false removals at cosine 0.80" |
| 21 | Execute-to-verify synthetic code with distilabel; rejection histogram as dashboard | lab-synth L1 | Generate-verify-filter in 60 lines |
| 22 | Slice table with Wilson CIs + cluster bootstrap: the 56% Spanish-health slice under an 84% headline | lab-synth L3 | Real output; slice-metrics chapter |
| 23 | Paired vs unpaired bootstrap: same data, opposite verdicts; McNemar on discordant pairs | lab-synth L4 + 2609.17394 | Statistics students will reuse |
| 24 | Cost-matrix thresholds: 0.5 to tuned saves 31%; enriched-eval threshold costs 66% more in prod; route/defer at 0.80 break-even | lab-synth L6-L7 + 2610.31657 | Re-run by verifier; business framing |
| 25 | Quality card as a CI gate (`sys.exit(1)` on CI-low < 0.5 or judge kappa < 0.6) | lab-synth L9 | Closes the data lifecycle; one artifact per model x eval hash |

---

## 5. Remaining [UNVERIFIED] items (carried forward, not fixed)

- Exact error-message wording that the original authors marked [UNVERIFIED]: the T4 bf16 error, the vLLM rank-overflow error, the OpenAI retired-model error, the Vertex batch-shape error, the RM `OSError`, and the `datasets` cast error.
- `trackio show` CLI name; `gcloud ai tuning-jobs` group; `Qwen2.5-Coder-1.5B-Instruct` model id; skactiveml API; ragas embedding type compatibility; the vLLM `--lora-modules` file path at v0.32.0.
- Vendor-doc claims (Vertex/OpenAI/Bedrock limits) and industry blog numbers. I did not re-fetch these.
- Paper affiliations marked [UNVERIFIED] in the arxiv-*.md files, and full-text numbers that I did not spot-check above.
- Takeaways for 6 "title only" papers (2607.22186, 2607.24850, 2609.33875, 2610.05935, 2610.12598, and the window-edge items). The IDs and titles are confirmed; the content was not read.

---

## 6. Confirmed arXiv papers in the window (180; title and v1 date from the arXiv API)

Cited-in key: SFT = lab-sft, RL = lab-rl, DATA = lab-data, SYN = lab-synth-eval, AX-RL / AX-DATA / AX-EVAL = arxiv-*.md, GOT = gotchas, IND = industry. Each takeaway is a one-line summary of the claim the research files make. I checked the numbers in section 3; the rest come from the cited file.

| # | arXiv id | Title (arXiv API) | v1 date | Cited in | One-line takeaway |
|---|---|---|---|---|---|
| 1 | 2607.21351 | How Much Can a LoRA Adapter Memorize? Measuring Adapter Capacity in Bits | 2026-07-23 | AX-RL | LoRA stores 2-3.4 bits/param; at equal accuracy SFT memorizes ~3x more example-specific info than GRPO. |
| 2 | 2607.21861 | Data Quality over Capacity: Internalizing Documents into LoRA Adapters for Closed-Book QA | 2026-07-23 | AX-RL | Curating documents into canonical short answers moved closed-book LoRA QA from 57.7% to 85.7%. |
| 3 | 2607.22186 | Deconstructing Off-Policy Ratios: Entropy-Normalized Trust Regions for Asynchronous Reinforcement Learning | 2026-07-24 | IND | Title only (entropy-normalized trust regions for async RL); abstract not read. |
| 4 | 2607.23364 | On the Impossibility of Unbiased and Length-Invariant Policy Optimization with Outcome Rewards | 2026-07-25 | RL | No length weighting is both unbiased and length-invariant; GRPO and Dr. GRPO sit at opposite ends. |
| 5 | 2607.23711 | The Intruder Threshold: A Spectral Law for LoRA Fine-Tuning | 2026-07-26 | AX-RL | Predicts which LoRA layers grow forgetting-driving intruder dimensions; lowering alpha or LR is the robust fix. |
| 6 | 2607.24717 | DataOrchestra: Learning to Orchestrate Per-Example Curation of Pretraining Data | 2026-07-27 | AX-DATA | Per-chunk orchestrator picks drop/keep/clean/rewrite for pretraining data; beats single processing methods. |
| 7 | 2607.24850 | SearchArt: Training Long-Horizon Search Agent with Scalable Synthetic and Verified Task | 2026-07-25 | IND | Title only (synthetic verified tasks for long-horizon search agents); abstract not read. |
| 8 | 2608.04268 | The Fairness Collapse Phenomenon: Bias Amplification in Language Models Trained on Synthetic Data | 2026-08-04 | AX-DATA | In recursive synthetic training, bias rises before LM metrics show collapse: add fairness probes. |
| 9 | 2608.05086 | Item Response Theory for AI Safety | 2026-08-05 | AX-EVAL | IRT over 8 safety benchmarks: ~10 adaptive items recover benchmarks at 97-99% lower cost. |
| 10 | 2608.07914 | When Is Benchmark Contamination Detectable? Information Limits and Power-Calibrated Audits | 2026-08-08 | AX-EVAL | Contamination detectability scales with alpha*rho*sqrt(m); report the power of your contamination check. |
| 11 | 2608.10579 | Agentic Instruction Data Selection: Let DataMaster Interpret Your Intent | 2026-08-11 | AX-DATA | DataMaster: agentic instruction-data selection; hold out evals the agent never sees. |
| 12 | 2608.11669 | Rubric Dropout: A Simple Way to Mitigate Reward Hacking in Rubric-Based RL | 2026-08-12 | AX-RL | Rubric dropout (drop 30-50% of criteria per step, shared per GRPO group) curbs rubric reward hacking. |
| 13 | 2608.14711 | Beyond Pass@k: Measuring Reliability and Security of Agentic Code Generation | 2026-08-11 | SYN | Harnesses misuse pass@k (n = unit tests, not rollouts), inflating scores by 0.85-0.97 absolute. |
| 14 | 2608.15980 | Whose Gold? Annotator-Pool Disagreement Is Large at the Item Level, and Hidden by Small Leaderboards | 2026-08-17 | AX-EVAL | Expert and crowd gold disagree on 23.6% of 'unanimous' items; small leaderboards hide it. |
| 15 | 2608.16620 | Palmyra x6 Technical Report: An Agentic, Tool-Use Model Post-Trained via Anchored Supervised Fine-Tuning | 2026-08-17 | AX-RL | Palmyra x6: anchored SFT on 626 verified tool-use trajectories reaches BFCL Core 0.785. |
| 16 | 2608.17776 | Debate Training Reduces Reward Hacking in RLAIF | 2026-08-18 | AX-RL | Debate (trained critic, 150-word cap) slows RLAIF reward hacking of a weak judge. |
| 17 | 2608.17994 | Judge, Retrieve, or Abstain: Uncertainty-Guarded LLM Judging with Provable Risk Guarantees | 2026-08-18 | AX-EVAL | Two-threshold judge -> retrieve -> human cascade with Clopper-Pearson FDR control on accepted verdicts. |
| 18 | 2608.18296 | FairGlucose: A CGM Fairness Benchmark Reveals Subgroup Disparities Hidden in Population-Level Validation | 2026-08-18 | AX-EVAL | Aggregate OOD ratio ~1.0 hides subgroup ratios 0.8-1.4: a clean slice-metrics example. |
| 19 | 2608.22118 | RAG Collapse: LLM Responses Collapse When Retrieved Documents Are Self-Authored | 2026-08-22 | AX-DATA | RAG answers collapse when retrieved docs are self-authored (79.6% of 1,528 simulations). |
| 20 | 2608.22483 | Claim-Level Confidence Calibration for Reliable Decision Making with Large Language Models | 2026-08-23 | SYN | Calibrating per atomic claim lowers ECE but fails on false-premise questions. |
| 21 | 2608.23816 | AQLoRA: A Zero-Search Recipe for Fast Quantized LoRA Fine-Tuning | 2026-08-24 | SFT | QLoRA saves memory not time; keeping high-NF4-error layers in fp16 trains ~11% faster. |
| 22 | 2608.24192 | Preference Data Selection for Mitigating the Alignment Tax in Large Language Models | 2026-08-25 | AX-DATA | Filter DPO pairs by reference margin, length gap and similarity to general text to cut the alignment tax. |
| 23 | 2608.24419 | A Judge Should Know What Changed:Construct Validity for LLM-as-a-Judge Evaluation | 2026-08-25 | AX-EVAL | Judges are robust (S=0.945) but blind to construct-changing edits (R=0.319): add must-flip items. |
| 24 | 2608.24807 | Automatic Model Card Generation Using an LLM | 2026-08-25 | AX-EVAL | LLM-generated model cards: ~0.9 semantic similarity, over half fully correct. |
| 25 | 2608.26661 | When Does Supervised Fine-Tuning Reduce Instruction Sensitivity? | 2026-08-27 | SFT | Task SFT cuts instruction sensitivity 54-71% at 1.7B/4B, not significantly at 8B. |
| 26 | 2608.27974 | QUORUM: QUality-Optimized Routing Using Multiple annotators | 2026-08-28 | AX-DATA | QUORUM routes items to human or LLM annotators on difficulty features: up to +34.4% quality, -8.8% cost. |
| 27 | 2608.28622 | PUFFER: Incremental Fuzzy Deduplication for Continuously Evolving Corpora | 2026-07-29 | AX-DATA | PUFFER: append-only, dataset-tagged MinHash-LSH segments; 1B docs at 128 B/doc, supports takedowns. |
| 28 | 2608.29144 | Quantifying Error Tolerance in Synthetic Data: An Atomic-level Operand vs. Operator Perturbation Study | 2026-08-29 | AX-DATA | Synthetic data tolerates operand errors but collapses on operator errors: filter on operators. |
| 29 | 2608.30224 | The Differential Reasoning Router: Operationalizing Cost-Aware LLM Annotation in E-commerce | 2026-08-31 | AX-DATA | Wayfair DRR routes per sample between direct/reasoning/human; >60% fewer reasoning tokens. |
| 30 | 2608.30619 | Hidden Threat in Synthetic Data: Covert Targeted Bias Injection through Benign Text | 2026-08-31 | AX-DATA | Benign-looking filtered synthetic data can carry a teacher's targeted bias to students. |
| 31 | 2608.30987 | Stick to What You Know: A Study of Knowledge-Aligned Supervised Fine-Tuning | 2026-08-31 | SFT | Do not teach facts the base cannot recall via SFT; Recall Rewrite reduces hallucination. |
| 32 | 2609.00062 | RePro: Proof-Verified Benchmark Rewriting for Reliable Evaluation of LLM Mathematical Problem Solving | 2026-08-30 | AX-DATA | Lean-verified rewrites of GSM8K/MATH drop several models' scores, suggesting memorization. |
| 33 | 2609.00494 | Human-Anchored Factuality Evaluation with Strategic Annotation | 2026-08-31 | AX-DATA | Choose items for human labels by judge failure modes: +40.3%/+27.1% effective sample size. |
| 34 | 2609.01244 | Post-Training Science for Supervised Fine-Tuning | 2026-09-01 | AX-RL, SFT | One-lever-at-a-time SFT sweeps on 4 customer datasets up to 235B MoE; LR and validation-loss questions. |
| 35 | 2609.01572 | From Production Traffic to Post-Training: Building a Self-Hosted LLM That Covers the Corporate Request Mix | 2026-09-01 | AX-RL | T-Tech: 3 GRPO experts with per-expert hack fixes, SLERP-merged; serves 116M requests/month. |
| 36 | 2609.02015 | How Output Format Confounds Data Quality and Capability in Instruction Tuning | 2026-09-02 | AX-DATA | A data skill can show +40 pts in its training format and vanish in others: eval across formats. |
| 37 | 2609.04518 | Multi-Harness Reinforcement Learning for Coding Agents: Training Gains and Harness Dependence | 2026-09-03 | IND | Harness choice moved solve rates 7.13 pp vs +0.48/+0.77 pp from RL: evaluate in your own harness. |
| 38 | 2609.09245 | What Fixed-Rollout pass@k Evaluations Can Identify | 2026-09-08 | AX-EVAL | pass@k for k > n rollouts is not identified; n=16 leaves k=1000 ambiguous by orders of magnitude. |
| 39 | 2609.10357 | A Later Test Set Is Not a New Domain: Pretraining Familiarity Survives a Contamination-Free Hold-Out | 2026-09-09 | AX-EVAL | A later test set removes window memorization but not domain familiarity. |
| 40 | 2609.11987 | Harness or Model? Isolating the Harness Effect in Agentic Coding with a Contamination-Controlled Private Suite | 2026-09-08 | AX-EVAL | On a private contamination-controlled suite, native vs neutral harness shows no average difference. |
| 41 | 2609.12171 | WinSyn: An Automated Pipeline for Realistic Enterprise Question-Answering Evaluation | 2026-09-10 | SYN | WinSyn: synthetic enterprise email QA with grounded gold; frontier agents stay below 80%. |
| 42 | 2609.12353 | SynthSentry: Detecting Synthetic Data Contamination in Language Model Training Data | 2026-09-11 | AX-DATA, SYN | SynthSentry: corpus-level synthetic-contamination score; thresholds need a bootstrap. |
| 43 | 2609.15015 | Four Ledgers, Not One Score: Responsible Communication of LLM-Judge Calibration in Biomedical ML | 2026-09-14 | DATA | Planted perturbations are not human ground truth; judge 'precision/recall' can be ledger artefacts. |
| 44 | 2609.17394 | Coding Agents Have Converged: Why the SWE-bench Leaderboard Can No Longer Order Its Top Entries, and What to Measure Instead | 2026-09-15 | AX-EVAL | SWE-bench top entries can no longer be ordered: McNemar separates 0 of 29 adjacent Verified pairs. |
| 45 | 2609.18878 | Preventing Model Collapse: A Fisher-Rao Perspective on the Dynamics of Training with Synthetic Data | 2026-09-16 | AX-DATA, GOT | Fisher-Rao view: the minimum human-data ratio to avoid collapse differs from Euclidean bounds; still open. |
| 46 | 2609.19101 | Monitoring and Discovering Reward Hacking with Internal Representations during LLM Evaluations | 2026-09-16 | IND | Probes on internal activations catch reward hacking (GLM 5.2 hacks in 57-73% of SWE rollouts). |
| 47 | 2609.19754 | AutoData: Agentic Search for Pre-training Data Selection | 2026-09-17 | AX-DATA | An agent searching over data-selection programs on a 125M proxy beats DCLM/perplexity/RegMix filters. |
| 48 | 2609.20027 | Can Data Attribution Filter Out Subliminal Learning? Not Reliably | 2026-09-17 | AX-DATA | Data attribution (EK-FAC, GradCos) does not reliably filter subliminal learning. |
| 49 | 2609.21888 | Detecting Pretraining Data in Large Language Models from a Free-Energy Perspective | 2026-09-18 | AX-DATA | Free-energy pretraining-data detection: up to +3.5% AUROC over membership-inference baselines. |
| 50 | 2609.22512 | Agreement Overstates Evidence: Error Dependence in LLM Judge Consensus | 2026-09-18 | AX-EVAL | Judge errors correlate (mean 0.21): 10 judges ~ 3.5 independent ones; up to 28% spurious wins. |
| 51 | 2609.22978 | DeepSeek Elastic Compute (DSec): A Sandbox Infrastructure for Effective Agentic Training at Scale | 2026-09-19 | AX-RL | DeepSeek DSec sandbox platform: 380k concurrent sandboxes for agentic RL. |
| 52 | 2609.24516 | LLJ Cards: Best practices for the Use of LLMs as Judges | 2026-09-21 | AX-EVAL | LLJ Cards: a measurement-theory reporting card for LLM-as-judge evaluations. |
| 53 | 2609.25487 | Identifying Suspected Mislabeled Apps in Google Play Application Removal Prediction: An Empirical Comparison of Label Noise Detection Methods | 2026-09-21 | DATA | Removing apps flagged by 3 label-noise detectors did not improve the model: flagged != delete. |
| 54 | 2609.25618 | Reasoning-Preserving Fine-Tuning of Post-RL LLMs with Null-Basis LoRA | 2026-09-22 | AX-RL, SFT | SFT on post-RL models erases reasoning (63.8% -> 8.3%); null-basis LoRA preserves it. |
| 55 | 2609.26489 | Calibration as a First-Class Criterion in LLM Evaluation | 2026-09-22 | AX-EVAL | Position paper: report calibration (ECE + reliability) next to accuracy on every eval. |
| 56 | 2609.27510 | Uncheatable Eval: Dynamic Compression-Based Evaluation of Language Models | 2026-09-23 | AX-DATA | Compression rate on fresh text as a contamination-resistant base-model eval (80 models). |
| 57 | 2609.28177 | How Sensitive Are LLM Leaderboard Claims to Hidden Model Selection? | 2026-09-23 | AX-EVAL | 391 of 394 adjacent Open-LLM-Leaderboard claims lack statistical support before selection correction. |
| 58 | 2609.28478 | When Evaluators Cry Wolf: Lessons from Production LLM-as-Judge Evaluation in Educational AI | 2026-08-01 | AX-EVAL | MagicSchool: unanimous-fail panels + softened rubrics cut false positives 99% with 100% canary recall. |
| 59 | 2609.28560 | Speculative Evaluation of Stochastic LLMs | 2026-09-23 | SYN | Neyman allocation of rollouts cuts benchmark-mean variance 12.8-33.6% vs uniform repeats. |
| 60 | 2609.29431 | Calibrating LLM Judges for Human and AI Conversations | 2026-09-24 | SYN | A small anchor set plus a calibration map puts any judge on a shared scale. |
| 61 | 2609.29709 | Three Ways Classical Test Theory Can Mislead About LLM Judges | 2026-08-31 | SYN | Reliability stats without gold labels cannot isolate the judge (KR-20 0.522 vs 0.523 gold). |
| 62 | 2609.29988 | Let Training Guide Selection: Online Synthetic Data Filtering via Real-Anchored Utility | 2026-09-24 | AX-DATA | FROST (Meta): online filtering of synthetic data by gradient alignment with real data; fixes ads NE regression. |
| 63 | 2609.30290 | Auditing and Repairing LLM-as-Judge Failures in a Production Text-to-SQL Pipeline | 2026-09-09 | AX-EVAL | Production text-to-SQL judge had kappa 0.04; a self-hosted open judge reached 0.72 at ~1/300 cost. |
| 64 | 2609.31857 | LLM Judge Validation Under Sparse Overlap: From Inference to Design | 2026-09-25 | AX-DATA, AX-EVAL | Validating a judge needs >=25% human overlap; at 5% the wrong best judge is picked 65% of the time. |
| 65 | 2609.31896 | Auditing Quality Filters for Long-Tail Human Data Curation | 2026-09-25 | AX-DATA | Quality filters under-retain long-tail human data: audit per-domain retention. |
| 66 | 2609.32211 | Rank Confidence Sequences:Anytime-valid Leaderboards | 2026-09-26 | AX-EVAL | Anytime-valid rank confidence sequences let you peek at a leaderboard after each item. |
| 67 | 2609.32484 | Towards Scalable Data Diversification for Language Model Pretraining via Leverage Score Sampling | 2026-09-26 | AX-DATA | Leverage-score diversification after quality filtering: up to 72x faster than DiSF, +1.31% accuracy. |
| 68 | 2609.32546 | Shared Autoregressive Context Can Distort Relationships in Synthetic Data | 2026-09-26 | AX-DATA | Generating 10 records per call inflates correlation error 48-127%: one record per call. |
| 69 | 2609.32976 | Adaptive Ensemble Selection for Noisy Labels on Tabular Data | 2026-09-26 | DATA | Meta-ensembles of noisy-label detectors are only comparable to confident learning on average. |
| 70 | 2609.33044 | Pinned and Still Unstable: Within-Judge Verdict Variance and the Noise Floor of LLM-as-Judge Leaderboards | 2026-09-27 | AX-EVAL | Pinned temperature-0 judges flip ~5% of verdicts, ~40% on close calls: re-run and report flip rate. |
| 71 | 2609.33848 | QwenGyre: An Elastic Reinforcement Learning Framework for Training xLong-Horizon Agents | 2026-09-27 | IND | QwenGyre: elastic RL for 700K-token rollouts; up to 1.85x over colocated RL. |
| 72 | 2609.33875 | Counterfactual Rollout Replay: Forkable Environments as Free Process Rewards for Software Engineering Agents | 2026-09-27 | IND | Title only (forkable environments as free process rewards for SWE agents); abstract not read. |
| 73 | 2609.33878 | Curating Merchant-Matching Training Data with Two Confidence-Gated Local LLM Judges | 2026-09-27 | AX-DATA | Two agreeing local LLM judges with separate pos/neg thresholds: 96.88% label purity at 81.7% coverage. |
| 74 | 2609.33909 | Near-Duplicate Families Break Exact-Record Membership Inference | 2026-09-27 | DATA | Near-duplicate families break exact-record membership inference, even after dedup. |
| 75 | 2609.34198 | Frozen Judges, Moving Agents: Version-Dependent LLM-Judge Error and the Limits of Judge-Assisted Agent Evaluation | 2026-09-28 | AX-EVAL | Judge error changes with agent version: reusing old calibration raises comparison error 3.8 -> 19.5 pts. |
| 76 | 2609.34521 | Population-Level Decision Curve Analysis May Mislead the Evaluation of Prediction Model Usefulness under Subgroup Utility Heterogeneity | 2026-09-28 | AX-EVAL | Population-level decision curves can mislead under subgroup heterogeneity: analyse per subgroup. |
| 77 | 2609.35815 | How to Run Statistics over LLM Judges and Trust the Results: Calibrated Inference for Small-Sample AI Evaluation with evalstats | 2026-09-20 | AX-EVAL | Bootstrap CIs under-cover at N<100 (88%/82%); use Wilson etc. plus PPI on a random human sample (evalstats). |
| 78 | 2609.36569 | From Checkpoint Variation to Selection Gains in Supervised Fine-Tuning | 2026-09-29 | SFT | Generation-based checkpoint selection beats NLL selection by 0.71-0.85 pp; gain over final checkpoint unresolved. |
| 79 | 2609.37294 | SafeLLM4SE: Statistical Evaluation and Reporting for LLM-based Software Engineering Systems | 2026-09-29 | AX-EVAL, SYN | SafeLLM4SE: CIs, effect sizes and a minimum statistical reporting standard for LLM SE evals. |
| 80 | 2609.37577 | Pair Difficulty Matters: Rethinking Pairwise LLM-as-a-Judge Evaluation and Consistency | 2026-09-29 | SYN | Judge position-bias and transitivity proxies are dominated by close rank-gap pairs: condition on gap. |
| 81 | 2609.38359 | Beyond Mode Collapse: Generating Diverse Synthetic Expert Conversations via Generative Flow Networks | 2026-09-29 | GOT | Prompted synthetic conversations collapse onto dominant modes; GFlowNets improve diversity. |
| 82 | 2609.38526 | Revisiting scaling laws for reward optimization | 2026-09-29 | AX-RL | Reward-optimisation performance scales like sqrt(min(log M, K)): preference data has log returns. |
| 83 | 2609.38914 | Risk-Aware Adaptive Evaluation: Finding High-Impact Failures Under Limited Budgets | 2026-09-30 | AX-EVAL | Impact-weighted Thompson sampling finds 86% of high-impact failures in 50 trials vs 25% uniform. |
| 84 | 2609.40295 | How Much Is an AI Token Worth? Scaling Laws for Wild AI-Generated Web Text | 2026-09-30 | AX-DATA | 27.5-31.1% of filtered web tokens are AI text; FineWeb/DCLM filters prefer AI docs 2.3x/9.8x. |
| 85 | 2610.00054 | The First Token Is Not the Verdict: Hidden Costs of Reading LLM Judges Without Generating | 2026-09-04 | SYN | Reading judge verdicts from first-token logits overstates position bias (89.7% vs 47.5% flips). |
| 86 | 2610.00369 | A Shared Taste for Model-Written Text: The Generator-by-Selector Matrices of "AI-AI Bias" Show No Detectable Own-Model Premium | 2026-09-30 | SYN | No detectable own-model premium in AI-AI bias; position bias moves cells up to 0.42. |
| 87 | 2610.00421 | Scores That Hold, Benchmarks That Leak: Measuring Dataset Contamination in Public Brain-Tumor MRI Classification | 2026-09-30 | DATA | 28.8% of a brain-MRI test split has near-twins in train, yet scores barely move after dedup. |
| 88 | 2610.00436 | Every Batch Is Its Own Validation Set: Leave-One-Out Gradient Matching for Online Data Selection in LLM Fine-Tuning | 2026-09-30 | AX-DATA, DATA | LOOM: drop the diagonal of the gradient Gram matrix; +2.3/+2.4 over full-batch, rejects label noise. |
| 89 | 2610.00651 | Agent Evaluation Reliability: More Tasks Won't (Always) Fix An Agent Leaderboard | 2026-09-30 | AX-EVAL | Agent leaderboards rank systems reliably but models poorly; more tasks add at most +0.097 reliability. |
| 90 | 2610.00779 | Effective Synthetic Data Curation Requires Group-Level Signals | 2026-09-30 | AX-DATA | Synthetic data needs group-level (set) scores; per-sample influence is nearly flat. |
| 91 | 2610.01493 | No Model Required: Text Entropy Rate Filtering Mitigates Iterative Fine-Tuning Collapse | 2026-10-01 | AX-DATA | Model-free entropy-rate filtering mitigates iterative fine-tuning collapse (+42% unique trigrams). |
| 92 | 2610.02067 | Learn the Directions, Normalize the Gains: Post-Training Normalization for LoRA | 2026-10-01 | SFT | LoRA-Norm: post-hoc spectral rebalancing of LoRA directions improves specialization and retention. |
| 93 | 2610.03036 | WebFovea: When the Model Is Right but the Click Is Wrong -- Reliable Round Trips for Vision-Based Web Agents on Live Websites | 2026-10-02 | GOT | WebFovea: self-generated chat-template tokens contaminated 4.9% of episodes: reject special tokens. |
| 94 | 2610.03185 | Gains and Collapse in On-Policy Distillation:A Reinforcement Learning Perspective | 2026-10-02 | AX-RL | On-policy distillation = RL with the teacher as implicit reward; mask length-capped rollouts (+3.08 pp). |
| 95 | 2610.04430 | MERCI Cards: An LLM Evaluation and Deployment Framework for High-Stakes Domains | 2026-10-03 | AX-EVAL | MERCI Cards: eval/deployment card framework for high-stakes LLM systems. |
| 96 | 2610.04507 | LoRA's Second Descent Extends Beyond Parameter Parity | 2026-10-03 | SFT | Under label noise LoRA risk is lowest at rank 1, then an interpolation cliff appears. |
| 97 | 2610.04978 | What Will Post-Training Fix? Per-Problem Gains Are Shared Across Independent RL Runs, and Existing Checkpoints Predict Them Better Than A Priori Signals | 2026-10-04 | AX-DATA | Independent RL runs agree on which problems improve; existing checkpoints predict gains best. |
| 98 | 2610.05094 | How Much Do LLM-as-a-Judge Design Choices Matter? A Systematic Comparison of Prompt Designs, Rating Scales, and Models | 2026-10-04 | AX-EVAL | Judge model identity dominates variance; scale and prompt shift leniency; low reasoning effort is fine. |
| 99 | 2610.05103 | VulValidate: Auditing Function-Level Vulnerability Labels with Executable Evidence | 2026-10-04 | AX-DATA | Executable audit of 35,849 vulnerability labels: 57.2% confirmed, 19.0% corrected. |
| 100 | 2610.05540 | SALUS: Automated Auditing of NL-to-SQL Benchmarks through Weak Supervision of Multi-Agent Output | 2026-10-04 | GOT | SALUS estimates ~37% annotation errors on BIRD dev. |
| 101 | 2610.05830 | Measurement-First Auditing of Agentic Leaderboards: Contamination Susceptibility, Matched-Control Re-evaluation, and Scorer Validation | 2026-10-05 | AX-EVAL | Agentic leaderboards: 0 of 27 contamination channels coded closed; check eval-time leakage. |
| 102 | 2610.05935 | ThunderSyncRL: Lossless Acceleration of Agentic Reinforcement Learning | 2026-10-05 | IND | Title only (lossless acceleration of agentic RL); abstract not read. |
| 103 | 2610.06542 | A Fine-Grained Analysis of the LoRA Fine-Tuning Landscape with Implications for Data Selection | 2026-10-05 | SFT | The right LoRA rank depends on data-induced conditioning; enables data selection at fixed rank. |
| 104 | 2610.07059 | Crop Yield Prediction for Punjab, Pakistan: A Tree-Ensemble and Leaf-Health Prototype, and What Random Validation Hides | 2026-10-05 | DATA | A 414-row table held 46 independent observations; year hold-out took R^2 from 0.994 to -0.20. |
| 105 | 2610.07405 | What pass@k Cannot Measure: Evaluating Diversity and Capability Retention after Post-Training | 2026-10-05 | AX-EVAL | pass@k cannot show diversity shifts: GRPO and RFT move diversity in opposite directions. |
| 106 | 2610.08026 | The Labeling Problem in Hallucination Detection Benchmarks: An Empirical Evaluation | 2026-10-06 | GOT | Hallucination labelers apply reference faithfulness when the target is factual correctness. |
| 107 | 2610.08770 | Data Leakage in Patch-Based Hyperspectral Image Classification: Quantifying the Impact of Spatial Overlap | 2026-10-06 | DATA | Random patch sampling gives 96.17% OA, spatially disjoint 55.20%: group by region. |
| 108 | 2610.09142 | Finding Side-Effect Loopholes in Verifiable Rewards | 2026-10-06 | RL | Verifiers that check only the requested change pass unrequested side effects; add count assertions. |
| 109 | 2610.09820 | The Impact of Backbone Evolution on LLM-Based Relevance Assessments | 2026-10-07 | GOT | Newer LLM backbones are not consistently better relevance judges; pin judge versions. |
| 110 | 2610.10478 | Before They Can Solve: Predicting Post-Training Coding-Agent Performance from Base Models | 2026-10-07 | IND | Base-model screens predict post-trained SWE-bench pass@1 ranking: choose the base before RL. |
| 111 | 2610.10597 | Certified Corruption Budgets: Anytime-Valid Leaderboard Claims under Adaptive Rigging | 2026-10-06 | AX-EVAL, GOT | A few hundred rigged votes can make standard CIs certify false leaderboard orderings. |
| 112 | 2610.10619 | TestJack: Should you trust the results in coding benchmarks? Agentic Coding Benchmarks Auditing via Evaluator Evolution | 2026-10-07 | GOT | TestJack: ~34.4% of 'correct' coding trials violate requirements (resolution 50.6% -> 33.2%). |
| 113 | 2610.10947 | RH-Detect: A Unified Benchmark for Reward Hacking Detection | 2026-10-07 | GOT | RH-Detect benchmark: best reward-hacking detector AUROC 0.962, weaker on multi-turn tool use. |
| 114 | 2610.11132 | SFT-as-Context Mitigates Forgetting in Supervised Fine-Tuning | 2026-10-08 | AX-RL, SFT | Training-free SFT-as-context: parent model reads the SFT model's answer; forgetting mitigated. |
| 115 | 2610.11281 | How to post-train on a surrogate: Envelope sampling mitigates reward hacking | 2026-10-08 | AX-RL | To recalibrate a judge with few labels, label envelope samples, not base-model samples. |
| 116 | 2610.11959 | MiMo-V2.6: Scaling Reinforcement Learning Towards Self-Improvement | 2026-10-08 | AX-RL | MiMo-V2.6: industrial RL with frozen MoE router and multi-layer reward-hacking defence. |
| 117 | 2610.12083 | All Verdicts are Not Equal: Rethinking LLM Judge Reliability | 2026-10-08 | GOT, SYN | Judge verdicts change across identical temperature-0 runs; most deterministic judge 51% accurate. |
| 118 | 2610.12598 | Beyond Binary Verifiable Rewards: Behavioral Self-Rewarding for SWE Agents | 2026-10-08 | IND | Title only (behavioural self-rewarding for SWE agents); abstract not read. |
| 119 | 2610.13152 | Quality, Not Just Outcome: A Structural Scoring Framework for Selecting Coding-Agent Trajectories for Supervised Fine-Tuning | 2026-10-09 | IND | Select SFT coding trajectories by structure, not only outcome: success != good training data. |
| 120 | 2610.13303 | Agreement Without Alignment: Label-Free Rubric Clarification Increases LLM-Judge Consensus but Not Agreement with Humans | 2026-10-09 | AX-EVAL, DATA | Rubric clarification raised inter-judge alpha +0.069 but not agreement with humans. |
| 121 | 2610.13321 | Host-Aware Web Crawling for LLM Pretraining Data | 2026-10-09 | AX-DATA | About half of quality variance is between hosts: sample a few pages per host, then go deep. |
| 122 | 2610.14028 | Pick the Mixture, Not the Samples: Combinatorial Data Selection for LLMs | 2026-09-30 | AX-DATA | Mixture-then-Select: set domain quotas first, then rank within domain (+20-54%). |
| 123 | 2610.14115 | The Silent Failures in Agentic Data Science | 2026-10-09 | DATA | Agentic data-science solutions show leakage failures that correlate positively with scores. |
| 124 | 2610.14238 | Agentic Data Engineering for LLMs: System Design and a Controlled Empirical Study | 2026-10-09 | AX-DATA | Agentic data engineering gains in-loop do not always generalize: hold out evals. |
| 125 | 2610.14270 | The Thinking Leakage in Reinforcement Learning for LLMs | 2026-10-09 | AX-RL | GRPO in Qwen3 no-think mode mostly re-activates think-mode reasoning. |
| 126 | 2610.14405 | SPROUT: Scaling Agentic Reinforcement Learning for Long-Horizon Software Engineering | 2026-10-09 | AX-RL | SPROUT: branch failed SWE rollouts from verified-good snapshots; +13.9 pts over GRPO. |
| 127 | 2610.14448 | KV4-RL: Unlocking Faster Asynchronous Rollouts for RLVR with INT4 KV Cache Quantization | 2026-10-10 | AX-RL | KV4-RL: INT4 KV-cache rollouts give 1.80x rollout speedup within 0.5 pp accuracy. |
| 128 | 2610.15617 | Screening Collapse under Recursive Synthetic Data | 2026-10-11 | AX-DATA | Recursive pseudo-labels corrupt feature screening before model fitting. |
| 129 | 2610.15778 | Who Sets the Pace of Judge Hacking? Judge Capability versus the Policy-Judge Gap | 2026-10-11 | AX-RL | GRPO against a frozen judge gives at most +0.04 held-out accuracy; hacking depth tracks judge AUC. |
| 130 | 2610.15924 | Scalable Weak-to-Strong Verifier Hardening for Agent Environments | 2026-10-11 | GOT | Weak-to-strong hacker/fixer loops harden agent-environment verifiers. |
| 131 | 2610.16152 | WildTrace: Evaluating Training Data Detection in Realistic Large-Scale LLM Post-Training | 2026-10-12 | GOT | WildTrace: post-training data detection averages AUC 0.529: record provenance at ingest. |
| 132 | 2610.16352 | LoongSage: A Production-Grade, High-Efficiency Agentic RL Framework for Frontier LLMs with Validated Recipes | 2026-10-12 | AX-RL | LoongSage: production async agentic RL framework with multi-teacher OPD manager. |
| 133 | 2610.16876 | CLIVO: Differentiable Cluster-Based Instruction Mixing with Learned Validation Objectives | 2026-10-12 | AX-DATA | CLIVO: 1.25% of an 8M VLM instruction pool reaches 97.2% of full-data score. |
| 134 | 2610.17062 | Gradient Routing Localizes and Removes Unintended Behaviors in RL | 2026-10-12 | AX-RL | GRAFT: route flagged-hack gradients into a throwaway adapter instead of penalizing; then delete it. |
| 135 | 2610.17399 | Learning to Detect Shifts in Unstructured Data Streams via Monitoring-by-Betting | 2026-10-12 | DATA | Monitoring-by-betting e-detectors for unstructured streams; calibration sets as small as m=30. |
| 136 | 2610.17747 | Auditing Failure Attribution: Label Predictability and Judge Behavior | 2026-10-13 | GOT | Surface-cue predictors match or beat GPT-4.1 on failure-attribution benchmarks. |
| 137 | 2610.17824 | Checking the Checkers: A Synthesis of Verifier Noise and Robustness in RLVR | 2026-10-13 | RL | Survey of 58 RLVR verifier-noise studies: error structure matters more than rate. |
| 138 | 2610.18011 | Correcting or Continuing? What On-Policy Distillation Learns from Student Errors | 2026-10-13 | AX-RL | OPD on failure-only curricula declines in all 8 configs: supervision must land on correct prefixes. |
| 139 | 2610.18588 | Decomposing and Predicting Annotation Disagreement in Harmful Content Across Languages | 2026-10-13 | AX-DATA | 20 binary LLM-answered questions predict contested annotation items (+10.5 ROC-AUC). |
| 140 | 2610.18613 | Does self-distillation improve reasoning? | 2026-10-13 | AX-RL | Self-distillation reasoning gains mostly overfitting or thinking-mode transfer, not privileged info. |
| 141 | 2610.18614 | Can an Agent Learn to Predict Its Own Failure? Outcome-Grounded Confidence Calibration in LLM Agents | 2026-10-13 | SYN | GRPO with a proper scoring rule on episode outcome cut agent ECE from 0.42 to below 0.12. |
| 142 | 2610.18853 | Two Clocks: Why Larger Rollout Batches Learn Slower but Fail on Schedule in Reinforcement Learning with Verifiable Rewards | 2026-10-13 | AX-RL | Larger rollout batches learn slower per sample past a critical batch: start small, then switch up. |
| 143 | 2610.19447 | BenchChecker: Assessing the Credibility of Bug-Fixing Benchmarks for LLMs | 2026-10-14 | AX-DATA, GOT | BenchChecker: contamination forensics (AUC ~0.9); clean subsets cut SWE-bench scores >20% relative. |
| 144 | 2610.19525 | Diagnosing and Correcting Reward Hacking in Verifiable Instruction Following | 2026-10-14 | AX-RL, RL | CaLIF: a reference-likelihood band stops IF-RLVR from satisfying constraints while not answering. |
| 145 | 2610.19789 | More Methods, Better Agents? A Reality Check on Self-Distillation in Agentic Reinforcement Learning | 2026-10-14 | AX-RL | Re-running 10 self-distillation methods: none beats GRPO consistently in agentic RL (12k GPU-h). |
| 146 | 2610.19832 | Rent-Seeking Language Models: Reward Models Set the Prices, Frequent Audits Curb the Rent | 2026-10-14 | GOT | RL turns 41-66% of proxy-reward gain into 'rent'; frequent mild audits beat rare severe ones. |
| 147 | 2610.20057 | Beyond Correctness: Compute-Responsive Data Selection for Reasoning Model Post-Training | 2026-10-14 | AX-DATA | SFT on compute-responsive problems (fail low budget, pass high) beats other selections. |
| 148 | 2610.20086 | AFCS: Atomic-Fact-Conditioned Synthesis for Factual Knowledge Pretraining | 2026-10-14 | AX-DATA | Atomic-fact-conditioned synthesis with per-fact verification beats WRAP/Nemotron-CC on SimpleQA. |
| 149 | 2610.21128 | When Judges Agree and Are Wrong: Consistency-Accuracy Dissociation as a Blind Spot for Label-Free Evaluation | 2026-10-15 | AX-EVAL | 60% of wrong answers sit in the high-consistency region: agreement is not accuracy. |
| 150 | 2610.21167 | GRADS: Graph-Regulated Agentic Data Synthesis with Controllable Difficulty | 2026-10-15 | SYN | GRADS: graph-regulated agentic QA synthesis with an explicit verification stage. |
| 151 | 2610.21179 | Judging the Judges: Confidence and Disagreement in Rubrics as Rewards | 2026-10-15 | AX-RL, RL | RaRE: confidence-weighted judges plus drop-on-disagreement masking beat any single judge. |
| 152 | 2610.21229 | What Should We Remove? Evaluating the Reliability and Costs of RLVR Data Decontamination | 2026-10-15 | GOT | Cosine-0.80 decontamination: 88% false removals; judge-adjudicated policy hits 98.1/98.2 P/R. |
| 153 | 2610.21337 | Does On-Policy Distillation Need to Complete Every Rollout? | 2026-10-15 | AX-RL | STOPD: random block truncation with IPW gives 25-48% fewer tokens, 1.3-2.2x faster OPD. |
| 154 | 2610.21404 | Multi-Reward Hacking: From Aggregation-Induced Drift to Trust-Anchored Defense | 2026-10-15 | AX-RL, GOT, RL | Additive multi-reward GRPO drifts to the easy auxiliary; correctness-gated TAG 0.581 vs 0.220 pass@4. |
| 155 | 2610.22760 | Between Spoilers and Guesswork: Avoiding Over-Specification in Coding Benchmarks | 2026-10-16 | GOT | Ground-truth-derived hints over-specify coding benchmark tasks ('spoilers'). |
| 156 | 2610.22887 | Batched Contextual Reinforcement II: Does RLVR Need Long Rollout Windows? | 2026-10-16 | AX-RL | Packing 3 verifiable problems per completion cuts RLVR tokens per step ~80%. |
| 157 | 2610.23946 | How Data Scales in Agentic Reinforcement Learning: Laws and Synthesis Strategies | 2026-10-08 | AX-RL | Agentic RL data scaling: new environments > new tasks > more trajectories (alpha 0.41/0.26/0.11). |
| 158 | 2610.24294 | Not Every User Says It All: Training Tool-Using Agents Beyond Ideal Simulated Users | 2026-10-16 | AX-RL | Training tool agents with terse simulated users needs state-grouped credit (+4.8 over GRPO). |
| 159 | 2610.24888 | Measuring Data Diversity with Embeddings: A Taxonomy and Benchmark for Diversity Measures | 2026-10-17 | AX-DATA | 21 embedding diversity measures compared; graph entropy beats mean pairwise distance. |
| 160 | 2610.24945 | Robust Direct Preference Optimization under Preference Label-Flip Attacks | 2026-10-18 | RL | DPO is steerable by preference label flips; Trim-K Robust-DPO comes with bounds. |
| 161 | 2610.25048 | PACT: NVFP4 Data-Flow LoRA Fine-Tuning on Consumer GPUs | 2026-10-18 | SFT | PACT: native NVFP4 compute for LoRA on a 16 GB consumer GPU. |
| 162 | 2610.25215 | Hidden Cartographer: Hidden State Guided Data Selection for Dual Budgeted Instruction Tuning | 2026-10-18 | DATA | Hidden Cartographer: separate annotation and training budgets; annotate 20-30%, train on 10-15%. |
| 163 | 2610.25325 | Where Groups Split: A Probe Prior for Nonzero Within-Group Variance in RL Post-Training | 2026-10-18 | RL | A short probe run predicts which prompts keep nonzero group variance better than base pass rate. |
| 164 | 2610.25497 | Self-Distillation for Supervised Fine-Tuning | 2026-10-18 | AX-RL, SFT | Gold-conditioned self-distillation (forward KL to an EMA teacher) beats SFT on new tasks. |
| 165 | 2610.25651 | OPDArena: Understanding Learning and Forgetting in On-Policy Distillation | 2026-10-19 | AX-RL | OPD from RLVR-trained teachers forgets less; OOD JS change tracks forgetting. |
| 166 | 2610.25725 | Anatomy of Off-Policy Policy Gradient: Importance Sampling, KL Regularization, and Baselines | 2026-10-19 | RL | Off-policy PG consistency needs trajectory IS or KL with a group-mean baseline. |
| 167 | 2610.25812 | Is it RL or Data? A Controlled Comparison of GRPO and Rejection-Sampling Fine-Tuning | 2026-10-19 | AX-RL, RL | Same prompts and verifier: GRPO beats tuned rejection-sampling FT by up to 10.9 pts; iterated RFT recovers ~30%. |
| 168 | 2610.26088 | LeakBench: Auditing Reward Hacking through Prediction-Time Leakage in Clinical Modeling Agents | 2026-10-19 | GOT | LeakBench: agents leak prediction-time-invalid features 10/10 runs unless constrained; names don't help. |
| 169 | 2610.26496 | Mitigating Reward Hacking in Preference Reward Models with Evolving Penalties | 2026-10-19 | RL | Dynalize: LLM-written evolving penalties curb RM reward hacking during training. |
| 170 | 2610.26951 | The Bottleneck Is Retrieval, Not Reading: Diagnosing Evidence-Based Generation with RAG for Long Context Question Answering | 2026-10-18 | SYN | Similarity retrieval finds any relevant chunk, not all required ones: score retrieval separately. |
| 171 | 2610.27533 | Adversarial Benchmarks and BenchDoor Attacks: Exploiting Benchmark Incentives for Backdoor Attacks | 2026-10-20 | AX-DATA | BenchDoor: benchmark-boosting data can implant backdoors that survive decontamination (>=90.33% ASR). |
| 172 | 2610.27701 | Understanding Data Augmentation under Label Noise | 2026-10-20 | DATA | Under label noise, data augmentation can act as an uncertainty amplifier: clean before augmenting. |
| 173 | 2610.27895 | The Shape of the DPO Hyperparameter Landscape: What to Measure, How It Moves with Scale, and When Not to Transfer It | 2026-10-20 | RL | DPO optimal LR moves with model size, does not transfer across datasets; val loss a poor proxy. |
| 174 | 2610.28679 | VerifierBench: Benchmarking the Generation of Executable Verifiers for LLM Agents | 2026-10-19 | AX-DATA | VerifierBench: LLM-written verifiers score 10.6-62.1 balanced accuracy; mostly over-reject valid solutions. |
| 175 | 2610.28707 | SimHack: Predicting the onset of detectable reward hacking before RL training | 2026-10-20 | AX-RL, GOT, RL | SimHack predicts reward-hacking onset (11.3% median error); curricula train 96.6% longer without hacking. |
| 176 | 2610.29410 | ECHO: Emergent Common-Mode Hidden Offsets Drive Vocabulary Collapse in Preference Optimization | 2026-10-21 | AX-RL, RL | ECHO: preference optimisation grows a common-mode hidden offset into vocabulary collapse (14 of 17 lineages). |
| 177 | 2610.30512 | Behind Aggregate Scores: What Systematically Varying Arena-Hard's LLM Judge Reveals | 2026-10-21 | AX-EVAL | Re-running Arena-Hard's judge unchanged flips 21.2% of prompt outcomes while the aggregate moves ~1 pt. |
| 178 | 2610.30765 | Scaling Laws for Generative Reward Models | 2026-10-22 | AX-RL, RL | Statically more accurate generative RMs often train worse policies; Answer-Only won 7 of 8 settings. |
| 179 | 2610.31172 | Prompting Strategy Effects Depend on the Judge: A Multilingual Study of LLM-as-a-Judge Robustness | 2026-10-22 | GOT | Prompting-strategy effects on judges reverse across judges and 27 languages. |
| 180 | 2610.31657 | Cost-Aware Abstention for LLM-Based IT Ticket Classification | 2026-10-22 | AX-EVAL, SYN | Cost-aware abstention: threshold from a (0,1,5) cost model, frozen on calibration; -38.1% cost. |

## 7. Out-of-window IDs found in the folder (10)

Background references are kept because they are not presented as window claims. CompactionRL was removed from industry.md.

| arXiv id | Title | v1 date | Status |
|---|---|---|---|
| 2407.21783 | The Llama 3 Herd of Models | 2024-07-31 | kept as background, not a window claim |
| 2411.00640 | Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations | 2024-11-01 | kept as background, not a window claim |
| 2506.13585 | MiniMax-M1: Scaling Test-Time Compute Efficiently with Lightning Attention | 2025-06-16 | kept as background, not a window claim |
| 2507.20534 | Kimi K2: Open Agentic Intelligence | 2025-07-28 | kept as background, not a window claim |
| 2512.02556 | DeepSeek-V3.2: Pushing the Frontier of Open Large Language Models | 2025-12-02 | kept as background, not a window claim |
| 2512.20856 | NVIDIA Nemotron 3: Efficient and Open Intelligence | 2025-12-24 | kept as background, not a window claim |
| 2602.02276 | Kimi K2.5: Visual Agentic Intelligence | 2026-02-02 | kept as background, not a window claim |
| 2602.19362 | LLMs Can Learn to Reason Via Off-Policy RL | 2026-02-22 | kept as background, not a window claim |
| 2603.24477 | Composer 2 Technical Report | 2026-03-25 | kept as background, not a window claim |
| 2607.05378 | CompactionRL: Reinforcement Learning with Context Compaction for Long-Horizon Agents | 2026-07-06 | REMOVED (outside window, cited as in-window) |

## 8. Verifier artefacts

Scratch scripts and the raw arXiv API response (190 entries) are in the session scratchpad, folder `verifier_custom/`: `arxiv.xml`, `arxiv.json`, `scan.py`, `stamp.py`, `boxtest.py`. Library sources read are under `verifier_custom/src/`.
