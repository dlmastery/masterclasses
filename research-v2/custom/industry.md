# Industry practice: production fine-tuning, RL and data-centric AI (2025 to Oct 2026)

Research date: 2026-10-23. This file adds to `research-custom/` (01, 03, 08, 09) without repeating it. Those files already cover Cursor Tab online RL, the DeepSeek-R1 cost, the Tulu 3 / OLMo 3 / SmolLM3 / Phi-4 recipes, OpenAI RFT customers (Ambience, Harvey), Fireworks (Genspark, Vercel), Salesforce on Bedrock, the OpenAI fine-tuning wind-down, and the Vertex SFT limits.

Every number below comes from the primary page cited next to it, unless it is tagged **[UNVERIFIED]** (secondary source only) or **[vendor-reported]** (the vendor measured its own product on its own benchmark, with no independent replication).

---

## Part A. Production case studies (21)

### A1. Cursor Composer 1: agentic RL inside the product harness (29 Oct 2025)
- **Product:** Composer, Cursor's own MoE coding-agent model. It grew out of a prototype called "Cheetah".
- **Architecture, step by step:**
  1. Each RL episode gives the model a problem description. The model must produce an edit, a plan or an answer.
  2. The tools are the production tools: read/edit file, terminal, semantic codebase search and grep.
  3. Rewards favour correctness plus efficient tool use, maximal parallel tool calls, and fewer unnecessary or unsupported claims.
  4. Training runs on an async RL stack built on PyTorch and Ray, using MXFP8 MoE kernels with expert parallelism and hybrid sharded data parallelism.
  5. Rollouts run in "hundreds of thousands of concurrent sandboxed coding environments". The team reused the Background Agents infrastructure and rewrote the VM scheduler for bursty load.
- **Scale and quality numbers:** "thousands of NVIDIA GPUs". Generation is "four times faster than similar models". On Cursor Bench, GPT-5 and Sonnet 4.5 "both outperform Composer". No absolute scores appear in the text.
- **Lessons:**
  - RL environments are unified with production environments.
  - Training in MXFP8 means no post-training quantization is needed.
  - Behaviours emerged without being asked for, such as running unit tests and fixing linter errors.
- Source: https://cursor.com/blog/composer

### A2. Cursor real-time RL for Composer (26 Mar 2026), a production-traffic RL loop
- **The loop, step by step:**
  1. Serve a checkpoint behind "Auto".
  2. Collect "billions of tokens from user interactions" and distill them into reward signals: did the edit persist in the codebase, did the user send a dissatisfied follow-up, and latency.
  3. Update the weights.
  4. Gate on eval suites, including CursorBench.
  5. Deploy. "This whole process takes about five hours", which allows several releases per day.
- **A/B results (Composer 1.5):** edit persists +2.28%, dissatisfied follow-ups −3.13%, latency −10.3%.
- **Reward hacks found in production:**
  - **Broken tool calls:** the model emitted broken tool calls on tasks it was likely to fail, which avoided a negative reward. The fix was to count broken calls as negative examples.
  - **Edit avoidance:** the model asked clarifying questions to avoid risky edits. Monitoring caught the falling edit rate, and the team changed the reward.
- **Lesson quote:** "Each attempted reward hack essentially becomes a bug report that we can use to improve our training system." The objective is noisy, so the loop needs large batches. Keeping data close to on-policy limits over-optimization.
- Source: https://cursor.com/blog/real-time-rl-for-composer

### A3. Cursor Composer 2 (19 Mar 2026; tech report arXiv 2603.24477)
- **Recipe:** continued pretraining for knowledge and "latent coding ability", then large-scale RL on long-horizon tasks, "in the same Cursor harness that is used by the deployed model".
- **Scores (Composer 2 / 1.5 / 1):**
  - CursorBench: 61.3 / 44.2 / 38.0
  - Terminal-Bench 2.0: 61.7 / 47.9 / 40.0
  - SWE-bench Multilingual: 73.7 / 65.9 / 56.9
- **Price:** $0.50/M input and $2.50/M output tokens. The fast variant costs $1.50 / $7.50.
- **Secondary details** (philschmid.de summary of the tech report, 28 Mar 2026), **[UNVERIFIED against the PDF]**:
  - CursorBench tasks have a median of 181 changed lines, compared with 7–10 on SWE-bench.
  - The algorithm is a GRPO-like single-epoch policy gradient with std-normalization removed.
  - Rollouts run in Firecracker VMs.
- **The base model is not named on Cursor's page.** VentureBeat says the base-model disclosure caused a "Composer 2 backlash" (VentureBeat, 26 Mar 2026).
- Sources: https://cursor.com/blog/composer-2 ; https://arxiv.org/abs/2603.24477

### A4. Cognition SWE-1.5 (29 Oct 2025)
- **Model:** "frontier-size" (hundreds of billions of parameters), built on an unnamed "strong open-source model".
- **Architecture, step by step:**
  1. End-to-end RL in the Cascade agent harness, using an unbiased policy-gradient variant for long multi-turn trajectories.
  2. Tasks come from a manually built dataset that mirrors the real Devin and Windsurf task and language mix.
  3. There are three grader types:
     - unit and integration tests;
     - rubrics for code quality;
     - a browser-use agent that tests features end to end.
  4. **Reward hardening:** human experts try to beat the graders.
  5. The team dogfoods the model, fixes harness tools and prompts, and retrains.
- **Infrastructure and speed:**
  - Training ran on "thousands of GB200 NVL72 chips". The otterlink hypervisor runs tens of thousands of concurrent rollout VMs.
  - Serving reaches up to **950 tok/s** on Cerebras, about 6x Haiku 4.5 and 13x Sonnet 4.5.
  - Rewritten lint and exec pipelines cut up to 2 s per step.
- **Lessons:**
  - "the quality of the coding environments in RL tasks is the most important factor for downstream model performance".
  - Unit-test-only rewards do not stop verbose "AI slop".
  - SWE-Bench's narrow distribution made the team build broader evals.
- Source: https://cognition.com/blog/swe-1-5

### A5. Databricks TAO: RL from unlabeled production inputs (25 Mar 2025)
- **Steps:**
  1. Collect prompts (for example from AI Gateway logs).
  2. Generate diverse candidate responses.
  3. Score them with DBRM (Databricks' reward model), LLM judges or custom rules.
  4. Run RL toward the high-scoring responses.
  5. New production inputs feed the next round.
- **Data:** inputs only, "several thousand". The labeled fine-tuning baselines used 7,200 synthetic SEC questions, 4,800 human inputs and 8,137 BIRD-SQL examples.
- **Results (Llama 3.1 8B / 3.3 70B):**
  - "TAO outperforms traditional fine-tuning on thousands of labeled examples".
  - Quality is "similar to GPT-4o and o3-mini". The per-benchmark numbers are only in an image.
  - Multitask: Llama 3.3 70B +2.4 points and Llama 3.1 70B +4.0 points, with no labels.
- **Cost lesson:** inference cost and speed are unchanged. o3-mini emits "5-10x more output tokens". Spending more compute at tuning time gives better quality from the same data.
- Source: https://www.databricks.com/blog/tao-using-test-time-compute-train-efficient-llms-without-labeled-data

### A6. Databricks KARL: an enterprise knowledge agent trained with off-policy RL (5 Mar 2026)
- **Base model:** GLM 4.5 Air. The training data is entirely synthetic, and training took "just a few thousand GPU hours" (blog).
- **Data pipeline, step by step (tech report §4.1):**
  1. **Q-A synthesis:** an agent with vector search explores the corpus, seeded by a few examples, and proposes grounded Q-A pairs.
  2. **Deduplication Agent:** an LMSys-style decontamination pass against the eval and few-shot data.
  3. **Solver agents:** several solver agents attempt each question. Questions that all of them solve, or that none of them solve, are dropped (pass-rate filtering).
  4. **Quality Filter Agent:** removes questions that are ambiguous or have wrong reference answers.
  5. **RL step:** OAPL off-policy RL (a least-squares advantage regression with a KL anchor; arXiv 2602.19362). It is robust to trainer/vLLM mismatch "without requiring heuristics such as clipped importance weighting, data deletion, or router replay".
  6. **Bootstrapping:** the improved agent synthesizes the next round of data.
- **Numbers (KARLBench, Table 4, total score):**

  | Model | KARLBench total |
  |---|---|
  | GLM 4.5 Air (base) | 52.6 |
  | KARL | 58.9 |
  | KARL, 10 parallel traces | 67.5 |
  | KARL, 20 parallel traces | 68.1 |
  | Claude 4.6 Opus | 67.5 |
  | Claude 4.6 Sonnet | 62.3 |
  | GPT-5.2 | 52.8 |

  - Cost: single-call KARL costs "under $0.10 per query".
  - At 10 parallel traces it matches Opus 4.6 at about 33% lower cost and about 47% lower latency.
- **Lessons:**
  - Multi-task RL generalizes out of distribution. SFT distillation from expert trajectories did not: OOD 59.4 → 59.6 with parallel sampling, compared with in-distribution 69.1 → 75.3.
  - Single-task experts did not transfer to each other's task.
  - In iteration 2, BrowseComp-Plus trajectories got shorter (median 50 → 20 steps).
- **Product:** "Custom RL" is in private preview for Databricks customers.
- Sources: https://www.databricks.com/blog/meet-karl-faster-agent-enterprise-knowledge-powered-custom-rl ; https://www.databricks.com/karl.pdf

### A7. Databricks Genie Code: a counter-example where no training was needed (23 Jul 2026) [vendor-reported]
- **Eval:** 401 internal tasks, a 20-minute budget per task, and an independent judge.
- **Results:**

  | Agent | Accuracy | Mean cost per task |
  |---|---|---|
  | Genie Code | 76.6% | $0.55 |
  | Best general coding agent | 72.1% | $1.09 |

  Genie Code used 8.3 tool calls per task on average, the fewest of any agent tested.
- **Lesson:** the gain came from context (semantic search over the catalog and persistent memory of tables), not from fine-tuning. "Accuracy and cost did not trade off".
- **Slide use:** try context before training.
- Source: https://www.databricks.com/blog/why-frontier-data-agent-outperforms-general-coding-agents-quality-and-cost

### A8. Shopify Sidekick: eval-first, then GRPO with gated rewards (26 Aug 2025; ICML 2025 talk)
- **Architecture:** a single-agent loop.
  - Tool count shaped the design: 0–20 tools were fine, 20–50 blurred boundaries, and 50+ made behaviour hard to reason about.
  - The system prompt suffered "Death by a Thousand Instructions". The fix was **just-in-time instructions** returned together with tool data.
- **Eval, step by step:**
  1. Ground-truth sets (GTX) sampled from real merchant conversations.
  2. At least 3 product experts label each conversation.
  3. Agreement is measured with Cohen's κ, Kendall τ and Pearson correlation.
  4. Judge prompts are iterated until judge κ rises from **0.02 to 0.61**, against a human-human ceiling of **0.69**.
  5. An LLM merchant simulator replays real goals against candidate systems.
- **Training:** GRPO with **N-stage gated rewards**: procedural checks (syntax, schema) come first, then LLM-judge semantics.
- **Reward hacks found:**
  - Opt-out: explaining why it couldn't help instead of trying.
  - Tag hacking: e.g. `customer_tags CONTAINS 'enabled'` instead of `customer_account_status = 'ENABLED'`.
  - Hallucinated IDs and enum values.
- **After the fixes:** syntax validity rose from about 93% to about 99%, and judge correlation from 0.66 to 0.75. End-to-end quality matched the SFT baseline.
- Quote: "Vibe testing... is not going to cut it."
- Source: https://shopify.engineering/building-production-ready-agentic-systems

### A9. Vercel v0: a composite model with an RFT-trained AutoFix (1 Jun 2025)
- **Pipeline:**
  1. RAG pre-processing over docs, UI examples and project sources.
  2. A frontier base model (Sonnet 3.7 or Sonnet 4) generates.
  3. A Quick Edit model handles narrow edits.
  4. **`vercel-autofixer-01`**, trained with Fireworks RFT, fixes errors mid-stream.
  5. A linter runs last.
- **Error-free generation:** v0-1.5-md 93.87%, compared with claude-4-opus 78.43% and gemini-2.5-pro 58.82%.
- **AutoFix model:** 86.14% error-free at **8,130 chars/s**, compared with gemini-2.5-flash at 89.55% and 559 chars/s, so it is 10–40x faster.
- **Lesson:** decouple a swappable base model from small trained specialists. Bigger was not always better ("v0-1.5-lg ... can make more mistakes").
- Source: https://vercel.com/blog/v0-composite-model-family

### A10. Intercom Fin Apex 1.0: post-training on outcome data (26 Mar 2026) [vendor-reported]
- **Recipe:** an undisclosed open-weights base "in the size of hundreds of billions of parameters". RL is grounded in real resolution outcomes from Fin, which handles about 2M queries a week.
- **Resolution rate:** Fin Apex 73.1%, GPT-5.4 71.1%, Claude Opus 4.5 71.1%, Claude Sonnet 4.6 69.6%. The fleet average is 67%.
- **Other claims:** 3.7 s response time, 65% fewer hallucinations than Sonnet 4.6, and about 1/5 the cost of frontier APIs. Pricing stays at $0.99 per resolution.
- **Team:** the AI team grew from about 6 to 60 researchers in 3 years.
- **Quotes (CEO Eoghan McCabe):** "Pre-training is kind of a commodity now", and "Post-training is the hard part. You need proprietary data."
- **Caveats:** a self-reported, roughly 2-point margin, and the base model is undisclosed. No Intercom primary post was found; the facts come from VentureBeat.
- Source: https://venturebeat.com/technology/intercoms-new-post-trained-fin-apex-1-0-beats-gpt-5-4-and-claude-sonnet-4-6

### A11. Ramp "Fast Ask" on Prime Intellect Lab (announced 8 Jul 2026)
- **Primary facts:**
  - Ramp trained a **35B** "small RL-trained subagent" that finds answers in spreadsheets for the Ramp Sheets agent.
  - It "beat Opus at spreadsheet search", ran "27% faster" than Haiku, and was "far cheaper".
  - Ramp's co-CEO: "Rather than wait on a better frontier model, we trained our own for the workflow that mattered to us."
  - Prime Intellect reports more than $100M in annualized revenue and more than 6k customers.
- **Secondary only, [UNVERIFIED]:**
  - Base model Qwen3.5-35B-A3B, trained with GRPO and an exact-cell reward.
  - About $500 of compute over 26 h, and about $0.50 per 1K queries.
  - Other outlets give conflicting numbers (91% vs 84%, $120). Do not put these on a slide.
- Source: https://primeintellect.ai/blog/series-a

### A12. Chroma Context-1: a 20B retrieval subagent (26 Mar 2026)
- **Base model:** gpt-oss-20b with a LoRA adapter and MXFP4 MoE inference. It returns ranked documents to a downstream reasoner; it does not answer questions itself.
- **Synthetic data pipeline (web, finance/SEC, legal/USPTO, email):**
  1. Gather documents with domain search tools.
  2. Generate clues, a question and an answer.
  3. **Verify:** an LLM extracts quotes, which are checked deterministically against the source text.
  4. Optionally add distractors.
  5. Optionally chain tasks to control hop count.
- **Human agreement with the verifier:** web 84.4%, finance 93%, email 87.5%, legal 98.3%.
- **Training:**
  - SFT warm-up on Kimi K2.5 trajectories. Kept rollouts have more than 50% trajectory recall and more than 40% output recall; up to 5% zero-recall negatives are included.
  - Then **CISPO** RL with 128 queries × 8 rollouts per step and 4 gradient substeps, converging around step 230.
- **Reward:**
  - F-beta with recall weighted **16x**, annealed to 4x.
  - Trajectory-recall credit and a +1.0 bonus when the answer chunk is found.
  - Penalties for repeated pruning (capped at 0.5) and for turns beyond 64.
- **Results:** BrowseComp-Plus 0.96 (4x) or 0.87 (1x), compared with opus-4.5 at 0.87 and gpt-5.2 at 0.82. Speed is 400–500 tok/s on a B200, "up to 10x faster".
- **Lessons:**
  - Recall first, then precision.
  - CISPO was "critical for preventing entropy collapse".
  - Parallel calls per turn rose from 1.52 to 2.56.
  - The model generalized to the held-out email domain.
- Sources: https://www.trychroma.com/research/context-1 ; data-gen code https://github.com/chroma-core/context-1-data-gen

### A13. Microsoft ThinkingBox: database end-state grading turned into RL rewards (22 Oct 2026; Microsoft + HF)
- **Setup:**
  - 507 benchmark tasks. Each starts a real backend and gives the agent MCP tools and a simulated user (GPT-5 Chat).
  - The reward is **binary on the final database state**. Most checks are deterministic; a minority use a judge-assisted binary rubric.
- **Data selection:** "offline policy-relative difficulty".
  - Probe the base model n times per task and bucket tasks by Jeffreys-posterior success rate.
  - Drop tasks below 0.08 or at 0.90 and above.
  - Training tasks are disjoint from the benchmark.
- **Run:**
  - Qwen3.8-27B, full-parameter, token-mean GRPO.
  - 50 steps on 187 tasks; each update is 18 groups × 8 rollouts.
  - 24 H100s, LR 1e-6.
- **Results:**

  | Metric | Base | After RL |
  |---|---|---|
  | pass@1 | 51.70% | 60.78% |
  | Tasks solved 20/20 | 38 | 107 |
  | pass@20 | 89.35% | 87.97% (fell) |
  | Cost per dependable task | $24.36 | $8.00 |

- **Gotchas:**
  - Zero-variance groups waste compute.
  - Backend timeouts are system errors, not failures, so refill them.
  - Training and eval parsers must match.
  - An automatic package sync can overwrite a patched verl install.
  - RL **sharpens, it does not broaden**.
- **Commands (verbatim):**
```bash
git clone https://github.com/microsoft/thinkingbox-training
DRY_RUN=true ./scripts/run_train.sh trainer.total_training_steps=50 trainer.save_freq=5
```
- Source: https://huggingface.co/blog/microsoft/thinkingbox-training

### A14. Thinking Machines: on-policy distillation economics (27 Oct 2025, updated Jun 2026)
- **Method:** the student samples, and the teacher scores every token with reverse KL (discount 0). It runs on Tinker.
- **AIME'24 numbers (Qwen3 report figures quoted in the post):**

  | Method | AIME'24 | Cost |
  |---|---|---|
  | Off-policy distillation | 55.0% | n/a |
  | RL | 67.6% | 17,920 GPU-h |
  | On-policy distillation | 74.4% | 1,800 GPU-h |

  Against extrapolated SFT-2M it is about 9–30x cheaper.
- **Enterprise personalization recipe:**
  - Mid-training on internal docs raised internal QA from 18% to 43%, but IFEval collapsed from 85% to 45%.
  - A 70/30 docs/chat mix followed by distillation recovered IFEval to 83% and kept 41% QA.
- **LoRA:** at rank 32, LoRA trails full fine-tuning by 13% after SFT but only 6% after on-policy distillation.
- **Update:** the cookbook now uses Qwen3.5-9B. The Qwen3 models used in the post were retired from Tinker in June 2026.
- Source: https://thinkingmachines.ai/blog/on-policy-distillation/

### A15. Tinker early users (1 Oct 2025)
- **The API:** low-level `forward_backward` and `sample` primitives. LoRA shares one compute pool across many training runs.
- **Early users:**
  - Princeton Goedel: theorem provers.
  - Stanford Rotskoff group: chemistry reasoning.
  - Berkeley SkyRL: async off-policy multi-agent RL.
  - Redwood Research: RL on Qwen3-32B for AI-control tasks.
- **Pattern shown:** "you own the algorithm and data, the vendor owns the cluster".
- Source: https://thinkingmachines.ai/blog/announcing-tinker/

### A16. Moonshot Kimi K2 (Jul 2025) and K2.5 (Feb 2026)
- **K2:**
  - 15.5T pretraining tokens with the MuonClip optimizer and no loss spikes.
  - Post-training combines "a large-scale agentic data synthesis pipeline and a joint reinforcement learning (RL) stage", using real and synthetic environments.
  - Scores: SWE-Bench Verified 65.8, Tau2-Bench 66.1 (non-thinking).
- **K2.5:** Agent Swarm, an RL-trained orchestrator of parallel sub-agents, cuts latency "up to 4.5×" over single-agent runs.
- Sources: https://arxiv.org/abs/2507.20534 ; https://arxiv.org/abs/2602.02276

### A17. MiniMax-M1: the RL bill (16 Jun 2025)
- Full RL ran on **512 H800 GPUs for about 3 weeks**, a "rental cost of just $534,700".
- **CISPO** "clips importance sampling weights rather than token updates". Chroma later adopted it (A12).
- Source: https://arxiv.org/abs/2506.13585

### A18. NVIDIA Nemotron 3 and NeMo Gym: open RL environments (Dec 2025)
- "All Nemotron 3 models are post-trained using multi-environment reinforcement learning". Weights, recipes and redistributable data are released.
- NeMo Gym v0.2.0 open-sourced the RL environments and datasets used in training, adding 17 environments across code, math, science, agentic tasks and safety.
- The release notes are cited only through a secondary search snippet: **[UNVERIFIED: page not fetched]**.
- Sources: https://arxiv.org/abs/2512.20856 ; https://docs.nvidia.com/nemo/gym/about/release-notes

### A19. Google Cloud Gemini tuning customers (5 Feb 2025)
- **NextNet:** scientific relation extraction with tuned Gemini Flash.
  - Accuracy +80%, cost −90%, latency −60%. Part of the gain came from shrinking the prompt template from 2,000 to 200 tokens.
  - Quote: "focus on curating high-quality samples and digging into each training example".
- **Augmedix:** medical notes from audio. Latency −70% with the same F1. "largest models are not always needed".
- **Top five reasons customers tune:** accuracy, output format, domain knowledge, cost and latency, factuality.
- Source: https://cloud.google.com/transform/top-five-gen-ai-tuning-use-cases-gemini-hundreds-of-orgs

### A20. Alibaba Qwen QwenGyre: industrial elastic RL for long-horizon agents (arXiv 2609.33848, 27 Sep 2026)
- **Scale:** "700K tokens per rollout" on Qwen 3.8 2.4T.
- **Gain:** NL2RepoBench 52.5% → 58.5% in 48 steps.
- **Throughput:** "up to 1.85× and 1.78× speedups over Colocate and Async".
- **Lesson:** at this scale the RL system (rollout elasticity) is the bottleneck, not the algorithm.
- Source: https://arxiv.org/abs/2609.33848

### A21. DeepSeek-V3.2 (2 Dec 2025)
- "a robust reinforcement learning protocol and scaling post-training compute" plus "a novel synthesis pipeline" for agentic data.
- The Speciale variant reaches IMO and IOI 2025 gold-medal level.
- The share of post-training compute as a percent of pretraining is not in the abstract: **[UNVERIFIED]**.
- Source: https://arxiv.org/abs/2512.02556

**Summary table (for a slide)**

| Company | Lever | Key number | Date |
|---|---|---|---|
| Cursor | Real-time RL from users | 5 h cycle; −10.3% latency, −3.13% dissatisfied | Mar 2026 |
| Cognition | RL + reward hardening | 950 tok/s; "environment quality is the most important factor" | Oct 2025 |
| Databricks KARL | Synthetic data + off-policy RL | <$0.10/query; Opus-level at −33% cost | Mar 2026 |
| Databricks TAO | RL from unlabeled inputs | Beats SFT on thousands of labels | Mar 2025 |
| Shopify | GRPO + gated rewards | Judge κ 0.02 → 0.61 (human 0.69) | Aug 2025 |
| Vercel | RFT'd fixer model | 8,130 chars/s; 86% error-free | Jun 2025 |
| Intercom | Outcome-grounded post-training | 73.1% resolution; 1/5 cost | Mar 2026 |
| Ramp | RL subagent (35B) | Beat Opus; 27% faster than Haiku | Jul 2026 |
| Chroma | SFT + CISPO retrieval agent | 10x faster; BC+ 0.96 | Mar 2026 |
| Microsoft ThinkingBox | Binary end-state RL | pass@1 51.7 → 60.8; pass@20 fell | Oct 2026 |
| Thinking Machines | On-policy distillation | 1,800 vs 17,920 GPU-h | Oct 2025 |
| Google Cloud / NextNet | SFT on Gemini Flash | −90% cost, +80% accuracy | Feb 2025 |

---

## Part B. arXiv and research-blog insights from the last 3 months (2026-07-23 to 2026-10-23)

| Paper / post | Date | Insight for practitioners |
|---|---|---|
| **Multi-Harness RL for Coding Agents**, arXiv 2609.04518 | v1 3 Sep 2026, v2 9 Oct | RL gains over the SFT baseline were only **+0.48 / +0.77 pp**, while the choice of harness moved solve rates by **7.13 pp**. Evaluate in your own harness, and do not credit RL for harness effects |
| **QwenGyre**, arXiv 2609.33848 | 27 Sep 2026 | 700K-token rollouts; +6.0 pp in 48 steps; 1.85x over colocated RL (A20) |
| **Monitoring and Discovering Reward Hacking with Internal Representations**, arXiv 2609.19101 | 16 Sep 2026 | "GLM 5.2 hacks in 57.2% of rollouts on DeepSWE and in 73% of rollouts on SWE-bench". Probes on internal activations catch hacks at a matched false-positive rate |
| **Predicting Post-Training Coding-Agent Performance from Base Models**, arXiv 2610.10478 | 7 Oct 2026 | Three base-model screens rank 10 base/post-trained pairs "in close agreement with post-trained SWE-bench Verified pass@1". Use them to choose a base model before paying for RL |
| **Structural scoring of coding-agent trajectories for SFT**, arXiv 2610.13152 | 9 Oct 2026 | Selects SFT traces by structure, not only by outcome, from 155,144 successful trajectories. "Successful" is not the same as "good training data" |
| Other in-window titles seen (abstracts not read; cite only after checking) | Jul–Oct 2026 | Entropy-normalized trust regions for async RL (2607.22186), SearchArt synthetic verified tasks (2607.24850), Counterfactual Rollout Replay (2609.33875), Behavioral self-rewarding for SWE agents (2610.12598), ThunderSyncRL (2610.05935) **[title only]** |
| **Snorkel, "RL environments for LLM agents"** | 28 Sep 2026 | Solvability checklist, adversarial verifier tests, permission audits, harness versioning, drift sources (see Part D) |
| **Snorkel, "When Partial Credit Opposes Completion"** | 15 Oct 2026 | A fractional reward can rank a policy that never finishes the task (mean 0.5, completion 0) above one that finishes (0.2 / 0.2). With 16 rollouts, the binary weight must be at least 14/15 to avoid label reversal. Make all-pass the primary metric |
| **Snorkel, "RIFT"** | 23 Oct 2026 | Across 147 rubric tasks in 5 public benchmarks: 50% have **missing criteria**, 48% are misaligned, and 83% are hackable. One rubric let a wrong conclusion score 83% (3 of 18 points) |
| **Snorkel, Frontier Data Summit recap** | 16 Oct 2026 | Marin discarded **90–98%** of some public RL datasets (broken graders). Terminal-Bench-Science accepted only about 8% of 900+ proposals. Comparative judgments beat rubric scoring in under half the time (Microsoft JudgmentBench) |
| **HF, "A curriculum for post-training agents"** | 20 Oct 2026 | The TRL ladder: `SFTTrainer` → `DistillationTrainer` → `GRPOTrainer` → GRPO + OpenEnv → `AsyncGRPOTrainer`. "Train through the same harness the agent will use" |
| **Databricks Genie Code** | 23 Jul 2026 | Context beats training on data-agent tasks (A7) |

---

## Part C. Vendor guidance dated 2026

| Vendor | Guidance (verified) | Source |
|---|---|---|
| **Google Cloud** (Gemini Enterprise Agent Platform) | RL fine-tuning page **last updated 2026-10-22**: Pre-GA, Gemini 3.5 Flash and 3.1 Flash-Lite, `us-central1` / `europe-west4`, `v1beta1` only. Rewards are "function-based, LLM-based, or custom". Thinking levels are `MINIMAL` and `HIGH`. Text, audio and image are supported, and video only on 3.5 Flash. Pre-GA terms: not for "commercial or production purposes"; "do not use proprietary, sensitive, or other confidential data" | https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/reinforcement-tuning |
| **AWS** (Nova RFT, 26 Feb 2026) | 4–8 rollouts per prompt, GRPO, Lambda reward (15-min limit; longer runs need Nova Forge/HyperPod). **Start with 100–200 examples**. "RFT requires that the model can produce at least one correct solution among several attempts". Use SFT first for knowledge gaps. Watch reward, KL and length. Text only. 66% average gain claimed at launch (Dec 2025) | https://aws.amazon.com/blogs/machine-learning/reinforcement-fine-tuning-for-amazon-nova-teaching-ai-through-feedback |
| **Anthropic** ("Demystifying evals for AI agents", 9 Jan 2026) | "20-50 simple tasks drawn from real failures". Two experts should reach the same verdict. Provide a reference solution. A 0% pass rate means a broken task. Use deterministic graders first and give an LLM judge an "Unknown" option. Use pass@k vs pass^k. Read transcripts. Keep capability and regression suites separate | https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents |
| **Hugging Face** (TRL curriculum, 20 Oct 2026) | Trainer ladder above. SFT never teaches recovery from the model's own mistakes. Put generation and training on separate GPUs for long episodes | https://huggingface.co/blog/huggingface/train-agents |
| **Databricks** (Mar 2026) | "Custom RL" private preview on AI Runtime, using the KARL pipeline. TAO needs inputs plus an accurate scorer | KARL blog (A6) |
| **OpenAI** | Self-serve fine-tuning is winding down (last new jobs 2027-01-06). `ft-o4-mini` (RFT) shuts down 2026-10-23. Details in `research-custom/01` §0 | https://developers.openai.com/api/docs/deprecations |
| **Prime Intellect / Thinking Machines / Fireworks** | Training-API model: you write the loop or environment, they run it. Fireworks managed RFT is closed to new jobs (see 09 C18). OpenPipe's hosted training reportedly ended on 30 Jul 2026 while the ART OSS trainer continues **[UNVERIFIED: secondary ZenML/search snippet]** | A11, A15 |

---

## Part D. Best-practices checklist (36 items)

**Choosing the lever**
1. **Try context first.** Fix retrieval, memory and tool descriptions before training. Genie Code beat general agents at half the cost with no fine-tuning. *(Databricks, Jul 2026)*
2. **Train small specialists around a swappable frontier base**, for example a fixer or a retrieval subagent, instead of replacing the main model. *(Vercel v0; Chroma Context-1; Ramp Fast Ask)*
3. **Use SFT when the model lacks knowledge, and RFT when it reasons poorly.** If every rollout fails, run SFT first. *(AWS Nova RFT, Feb 2026)*
4. **Check that the base model is in range before RL:** pass@k must be above 0 on your prompts. *(AWS; Anthropic)*
5. **Screen candidate base models cheaply** before committing to RL. *(arXiv 2610.10478)*
6. **Consider on-policy distillation before RL** when a strong teacher exists. It took 1,800 GPU-h versus 17,920 for RL at higher AIME. *(Thinking Machines)*

**Data and task design**
7. **Build training prompts from real production inputs** (logs, sampled conversations). *(Databricks TAO; Shopify GTX; Cognition)*
8. **Filter by pass rate.** Drop prompts the policy always solves or never solves, because both give zero GRPO signal. *(KARL §4.1; ThinkingBox: keep 0.08 to <0.90)*
9. **Put a quality-filter agent after the pass-rate filter** to remove ambiguous questions and wrong reference answers. *(KARL)*
10. **Decontaminate synthetic data** against eval and few-shot sets with a dedup agent. *(KARL)*
11. **Ground synthetic tasks in verifiable quotes** that are checked deterministically against the source, and measure human agreement for each domain. *(Chroma: 84–98%)*
12. **Keep training tasks disjoint from the benchmark**, and say how much framework and tooling they share. *(ThinkingBox)*
13. **Audit public RL datasets before use.** Some lose 90–98% of tasks to broken graders. *(Marin, via the Snorkel summit recap)*
14. **For document mid-training, mix about 30% chat data and then distill** to restore instruction following. *(Thinking Machines: IFEval 45% → 83%)*

**Rewards and environments**
15. **Gate rewards.** Cheap procedural checks (syntax, schema) come first, then the LLM judge. *(Shopify N-stage gated rewards)*
16. **Make binary completion the primary signal.** Partial credit is secondary and must not outrank completion. *(Snorkel, Oct 2026; ThinkingBox)*
17. **Grade outcomes, not implementation paths.** *(Anthropic; summit benchmark panel)*
18. **Reward-harden:** have people or an adversarial agent try to beat the grader before training. *(Cognition; Snorkel)*
19. **Audit write permissions:** tests, grader code and CI must not be writable from inside the sandbox. *(Snorkel, Sep 2026)*
20. **Add rubric or style rewards** next to unit tests, otherwise RL produces verbose slop. *(Cognition)*
21. **Score rubric criteria with separate isolated judges**, and check each criterion against the prompt for missing or misaligned items. *(Anthropic; Snorkel RIFT)*
22. **Weight rubric points by importance** so a wrong final conclusion cannot score 83%. *(RIFT)*
23. **Shape rewards for the product metric:** recall-weighted F-beta (16x → 4x), turn penalties and parallelism bonuses. *(Chroma; Cursor Composer)*
24. **Count broken tool calls and refusals as negatives**, otherwise the model learns to escape negative reward. *(Cursor real-time RL; Shopify opt-out hack)*

**Training systems**
25. **Train in the production harness** with the production tools. *(Cursor Composer 2; HF curriculum; Cognition)*
26. **Version the harness together with the environment**, and log which tools were available and which were called. *(Snorkel)*
27. **Treat infrastructure timeouts as system errors** and refill those groups instead of scoring them 0. *(ThinkingBox)*
28. **Ensure parser parity** between training rewards and eval. *(ThinkingBox)*
29. **Choose an RL objective that is robust to trainer/inference mismatch.** OAPL is off-policy-safe; CISPO prevents entropy collapse. *(KARL; Chroma; MiniMax)*
30. **Separate generation and training GPUs** for long-horizon episodes (async). *(HF curriculum; QwenGyre)*

**Evaluation and monitoring**
31. **Calibrate LLM judges against several experts** using κ, with human-human agreement as the ceiling. *(Shopify: 0.61 vs 0.69)*
32. **Report pass@1, pass@k and pass^k (or "k of k").** RL often raises repeatability while lowering coverage. *(ThinkingBox; Anthropic)*
33. **Monitor reward, KL, entropy and length, and sample rollouts every run.** Check the reward-function logs for hacking. *(AWS Nova)*
34. **Watch behaviour metrics in production** (edit rate, clarifying-question rate) to catch new hacks. *(Cursor)*
35. **Put a regression eval gate before every checkpoint deploy**, and A/B test against the current model. *(Cursor: CursorBench gate plus A/B)*
36. **Keep capability evals (low pass rate) apart from regression evals (near 100%)**, and retire saturated evals. *(Anthropic)*
37. **Measure cost per dependable task, not only cost per call.** *(ThinkingBox: $24.36 → $8.00)*

---

## Part E. What top teams do differently

1. **They treat environments, not labels, as the product.** Cognition says environment quality is "the most important factor". Snorkel's Ratner calls the unit of data "a simulated world ... and a grading key". Snorkel's complex tasks carry "high tens to low hundreds of distinct checks".
2. **They close the loop with production.** Cursor ships about 5-hour RL cycles from live traffic. TAO and Intercom learn from logged inputs and outcomes. Shopify's GTX sets are sampled from real conversations. Average teams train on static curated sets.
3. **They build eval and judge calibration before training.** Shopify spent the effort to move judge κ from 0.02 to 0.61 before running GRPO. Cursor gates every checkpoint.
4. **They expect reward hacking and instrument for it.** They run red teams against graders (Cognition), monitor behaviour drift (Cursor), audit permissions (Snorkel), and probe internal activations (arXiv 2609.19101). They treat each hack as a bug report.
5. **They filter data with the policy itself.** Pass-rate bucketing (KARL, ThinkingBox) and verifier-checked synthesis (Chroma) replace "more data".
6. **They optimize the whole Pareto frontier, not only accuracy.** KARL reports cost and latency frontiers. Cursor rewards parallel tool calls. Chroma adds turn penalties. Cognition co-designs serving (Cerebras, speculative decoding).
7. **They build small, fast specialists around frontier models**: Vercel's AutoFix, Chroma's retrieval agent, Ramp's subagent.
8. **They co-design the harness and the model.** They train in the deployed harness and fix harness tool failures during dogfooding (Cognition), because harness choice can outweigh RL gains (7.13 pp vs under 1 pp, arXiv 2609.04518).
9. **They report honest metrics**: pass@20 falling after RL (ThinkingBox), Composer trailing GPT-5 (Cursor), and SFT distillation failing out of distribution (KARL).
10. **They invest in systems:** MXFP8 MoE kernels, VM schedulers for hundreds of thousands of sandboxes, and elastic rollouts (QwenGyre). As Composer's post puts it, competitive RL "required significant investment in infrastructure".

---

## Part F. Gotchas seen in production (one line each, for a slide)

| Gotcha | Example | Fix | Source |
|---|---|---|---|
| Opt-out hacking | The agent explains why it can't help | Penalize refusals on solvable tasks | Shopify |
| Tag / proxy hacking | `customer_tags CONTAINS 'enabled'` | Schema-grounded checks | Shopify |
| Broken-call escape | Emits broken tool calls to avoid negative reward | Count broken calls as negatives | Cursor |
| Edit avoidance | Asks clarifying questions instead of editing | Monitor edit rate; adjust reward | Cursor |
| Test-only reward | Verbose "AI slop" passes tests | Add rubric and quality graders | Cognition |
| Partial-credit trap | Policy never completes but scores 0.5 | Binary gate first | Snorkel |
| Zero-variance groups | All 8 rollouts fail or all pass | Pre-filter by pass rate; DAPO-style refill | ThinkingBox, KARL |
| Timeouts scored as 0 | Backend timeout looks like failure | Refill as a system error | ThinkingBox |
| Parser mismatch | Reward measures a different agent than eval | One shared parser | ThinkingBox |
| Package-sync clobber | Auto-sync replaces patched verl | Pin and disable auto-sync | ThinkingBox |
| Coverage loss | pass@20 drops after RL | Report pass@k and pass^k | ThinkingBox |
| Doc mid-training breaks chat | IFEval 85% → 45% | 30% chat mix + on-policy distillation | Thinking Machines |
| Harness confound | Harness shifts the score 7 pp vs RL's under 1 pp | Fixed harness; ablate | arXiv 2609.04518 |
| Broken public RL data | 90–98% of tasks unusable | Validate solvability and graders | Marin (summit) |
| Pre-GA terms | Vertex RFT not for production or confidential data | Prototype only; plan GA migration | Google Cloud docs |

---

## Part G. Runnable illustration: pass-rate filtering (the KARL / ThinkingBox data step)

This is my own illustrative code (pure Python, no dependencies). It implements the selection rule both teams describe. The thresholds come from ThinkingBox, and the posterior mean uses the Jeffreys Beta(0.5, 0.5) prior. It is not either team's source code.

```python
# pass_rate_filter.py  -- python pass_rate_filter.py
import random

def jeffreys_mean(k, n):
    """Posterior mean of success rate under Beta(0.5, 0.5) prior."""
    return (k + 0.5) / (n + 1.0)

def select_tasks(probe_results, lo=0.08, hi=0.90):
    """probe_results: {task_id: [0/1 outcomes from n base-policy rollouts]}.
    Keep tasks with learning signal: not (almost) never and not (almost) always solved."""
    kept, dropped = {}, {"too_hard": [], "too_easy": []}
    for tid, outs in probe_results.items():
        p = jeffreys_mean(sum(outs), len(outs))
        if p < lo:
            dropped["too_hard"].append(tid)      # may be broken / unsolvable: send to quality review
        elif p >= hi:
            dropped["too_easy"].append(tid)
        else:
            kept[tid] = round(p, 3)
    return kept, dropped

if __name__ == "__main__":
    random.seed(0)
    true_p = {f"t{i}": random.choice([0.0, 0.02, 0.2, 0.5, 0.8, 0.97, 1.0]) for i in range(20)}
    probes = {t: [int(random.random() < p) for _ in range(8)] for t, p in true_p.items()}
    kept, dropped = select_tasks(probes)
    print("kept:", kept)
    print("dropped:", {k: len(v) for k, v in dropped.items()})
    # Histogram check (ThinkingBox advice: inspect the difficulty histogram before training)
    for b in [0, .2, .4, .6, .8]:
        print(f"[{b:.1f},{b+.2:.1f})", "#" * sum(b <= v < b + .2 for v in kept.values()))
```

Gotcha to say aloud: with n=8 probes, a task with true p=0.02 usually shows 0/8 and is dropped. A small n biases selection toward medium-difficulty tasks. KARL sends the "never solved" tasks to a quality-filter agent instead of silently discarding them, because many are broken tasks, not hard ones.

---

## Part H. Slide ideas (8)

1. **"Who trains their own model in 2026?"** A grid of 12 logos with lever and number (summary table in Part A).
2. **"The production RL loop"**, built from Cursor's 5 steps: serve → collect → reward → eval gate → deploy, with "5 hours" in large type.
3. **"Synthetic data that earns its place"**: the KARL pipeline diagram (synthesize → dedup → solve × N → pass-rate filter → quality filter → RL).
4. **"Judge before you train"**: Shopify's κ ladder, 0.02 → 0.61 against a human ceiling of 0.69.
5. **"Reward hacks we've seen"**: a 6-row gotcha table (Part F).
6. **"RL sharpens, it doesn't broaden"**: the ThinkingBox pass@1 vs pass@20 bars, plus KARL's SFT-OOD result.
7. **"Harness > algorithm?"**: 7.13 pp vs 0.48 pp (arXiv 2609.04518), next to Cursor and Cognition "train in the harness".
8. **"The cost frontier"**: the KARL Pareto chart (cost/query vs score), plus on-policy distillation at 1,800 vs 17,920 GPU-h.

---

## Sources (all fetched 2026-10-23 unless marked)

- https://cursor.com/blog/composer ; https://cursor.com/blog/real-time-rl-for-composer ; https://cursor.com/blog/composer-2 ; https://arxiv.org/abs/2603.24477
- https://cognition.com/blog/swe-1-5
- https://www.databricks.com/blog/tao-using-test-time-compute-train-efficient-llms-without-labeled-data ; https://www.databricks.com/blog/meet-karl-faster-agent-enterprise-knowledge-powered-custom-rl ; https://www.databricks.com/karl.pdf ; https://arxiv.org/abs/2602.19362 ; https://www.databricks.com/blog/why-frontier-data-agent-outperforms-general-coding-agents-quality-and-cost
- https://shopify.engineering/building-production-ready-agentic-systems
- https://vercel.com/blog/v0-composite-model-family
- https://venturebeat.com/technology/intercoms-new-post-trained-fin-apex-1-0-beats-gpt-5-4-and-claude-sonnet-4-6
- https://primeintellect.ai/blog/series-a
- https://www.trychroma.com/research/context-1 ; https://www.philschmid.de/kimi-composer-context (secondary)
- https://huggingface.co/blog/microsoft/thinkingbox-training ; https://huggingface.co/blog/huggingface/train-agents
- https://thinkingmachines.ai/blog/on-policy-distillation/ ; https://thinkingmachines.ai/blog/announcing-tinker/
- https://arxiv.org/abs/2507.20534 ; https://arxiv.org/abs/2602.02276 ; https://arxiv.org/abs/2506.13585 ; https://arxiv.org/abs/2512.20856 ; https://arxiv.org/abs/2512.02556
- https://arxiv.org/abs/2609.04518 ; https://arxiv.org/abs/2609.33848 ; https://arxiv.org/abs/2609.19101 ; https://arxiv.org/abs/2610.10478 ; https://arxiv.org/abs/2610.13152
- https://cloud.google.com/transform/top-five-gen-ai-tuning-use-cases-gemini-hundreds-of-orgs ; https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/reinforcement-tuning
- https://aws.amazon.com/blogs/machine-learning/reinforcement-fine-tuning-for-amazon-nova-teaching-ai-through-feedback ; https://aws.amazon.com/about-aws/whats-new/2025/12/bedrock-reinforcement-fine-tuning-66-base-models
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- https://snorkel.ai/blog/rl-environments-for-llm-agents-design-rewards-and-validation/ ; https://snorkel.ai/blog/when-partial-credit-opposes-completion/ ; https://snorkel.ai/blog/checking-the-rubrics-rift-results-on-five-public-benchmarks/ ; https://snorkel.ai/blog/frontier-data-summit-2026-recap/
