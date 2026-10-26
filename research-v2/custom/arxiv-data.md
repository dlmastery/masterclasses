# arXiv sweep: data-centric AI for LLMs (2026-07-23 .. 2026-10-23)

Scope: data selection/filtering, synthetic data generation + verification, model collapse, deduplication, contamination, data mixtures, label noise, active learning / annotation routing, LLM-as-annotator.

## Method (how this list was built)

- The arXiv API (export.arxiv.org) returned HTTP 429 for every call (shared rate limit). So I used the arXiv advanced-search page instead. Filter: abstract field, computer science, **submitted_date 2026-07-23 .. 2026-10-23**, newest first.
- I ran 19 queries: "data selection", "synthetic data" + language model, "synthetic data" + verification, "model collapse", contamination + benchmark, decontamination, deduplication, "data mixture", "data curation", "data filtering", "quality filter", "pretraining data", "instruction tuning" + data quality, "label noise", "noisy labels", "annotator disagreement", "active learning" + language model, "LLM annotation", "LLM-as-a-judge" + annotation. That gave about 1,100 hits. I shortlisted about 50 abstracts and read the **arxiv.org/html full text** of the 23 top candidates to get numbers, affiliations and set-ups.
- Every number below comes from the abstract or the HTML full text of that paper. A line marked **[interp]** is my engineering reading, not the paper's claim. **[UNVERIFIED]** means I could not confirm it in the text.
- Dates are v1 submission dates. These IDs are all new. The older research in `research-custom/` cites none of them.
- Code blocks marked "sketch" are short illustrations I wrote of the paper's core idea, for slides. They are **not** the authors' code. I did not run them, because pip is blocked on this machine. They use only the Python standard library and numpy.

---

## Ranked list (by practical impact for an engineer)

### 1. How Much Is an AI Token Worth? Scaling Laws for Wild AI-Generated Web Text
- **arXiv:** 2609.40295 · **submitted:** 2026-09-30 · **who:** Jenna Russell (University of Maryland) with Pangram Labs (Mohit Iyyer, Max Spero, Bradley Emi et al.)
- **Problem:** Web crawls now hold a lot of unlabeled AI-written text. Nobody had measured what this text does to pretraining. This is the "wild" case, not a controlled model-collapse loop.
- **Method (diagram):**
  1. Crawl → FineWeb / DCLM filtering → Pangram AI-text detector labels each doc as AI or human.
  2. Pretrain **800 LMs** while varying the ratio of added AI tokens to human tokens.
  3. Fit scaling laws to held-out loss on human text and on AI text, separately.
  4. A new law adds a separate **benefit term and harm term**, so the value of an AI token can change sign. With no AI text, the law reduces to Chinchilla.
- **Key numbers:**
  - After FineWeb filtering, **27.5%** of June-2026 web tokens are AI-labeled. The figure is **31.1%** for August 2026.
  - AI docs pass FineWeb's pipeline **2.3× as often** as human docs (29.3% vs 12.8%). They pass DCLM's full pipeline **9.8× as often** (14.5% vs 1.5%). In other words, quality filters *prefer* AI text.
  - The new law predicts held-out human-text loss for models up to 3.6× larger, with **41% lower error** than the best existing law.
  - The authors forecast that **50.7%** of FineWeb tokens will be AI by end-2028. At August-2026's AI share, an unfiltered crawl needs **1.6× compute** to match a filtered model at 20 human tokens per parameter. In 2028 this becomes **3.0×**.
- **Monday takeaway:**
  - Run an AI-text detector as a pipeline stage *after* your quality classifier. Your quality classifier is biased toward AI text.
  - When human data runs out, **repeat human tokens before you add AI web tokens**.
  - Report validation loss on human text and on AI text as separate numbers.
- **Limitations:** The result depends on one commercial detector (Pangram) and its false-positive rate. "AI text" is not split by quality. The paper says AI text is still useful when the target *is* AI-style text.
- **Released:** WildAI, an 83B-token corpus with AI/topic/format labels, plus all 800 models and code (github.com/pangramlabs/WildAI).
- **Slide idea:** a funnel animation. Raw crawl → FineWeb → DCLM, with human (blue) and AI (orange) dots. Blue dots drop out faster at each stage, and the AI share inflates from about 1.5% to 14.5% survivors. Then a curve: "value of one AI token" starts positive and crosses zero as the human budget grows.

### 2. PUFFER: Incremental Fuzzy Deduplication for Continuously Evolving Corpora
- **arXiv:** 2608.28622 · **submitted:** 2026-07-29 · **who:** Xiao Yang, Erik Edward Aldape, Beren Millidge (Zyphra)
- **Problem:** Corpora arrive as repeated releases. Each new release must be deduplicated against itself *and* against all history, without rebuilding a RAM-resident MinHash-LSH index each time.
- **Method (diagram):**
  1. MinHash-LSH as usual (16 bands).
  2. Each LSH band is stored as **immutable, dataset-tagged, memory-mapped sorted segments**. Membership checks are exact, and RAM does not grow with corpus size.
  3. **T-fanout tiered compaction** merges segments, which trades index-write cost against query fan-out.
  4. Dataset tags allow **dataset-scoped withdrawal**, for example a license takedown. Withdrawal is constant time before compaction. After compaction, only the affected merged segment is rebuilt.
- **Key numbers:**
  - Cumulative maintenance cost is O(N log N log_T K), versus Θ(KN) for snapshot rebuilds.
  - 1B documents ingested in about **1.75 h** in a single process, at **128 bytes/doc**. A classic resident MinHash-LSH table needs about **6.5 KB/doc** and went over a 900 GiB RAM cap.
  - **11× faster than LSHBloom** and **35× faster than Milvus-LSH** (ten-hour comparison, 1B-doc cap).
  - Deployed on more than 30B documents. Open source: github.com/Zyphra/puffer.
- **Monday takeaway:**
  - Treat dedup as an **append-only index with provenance**, not as a batch job.
  - Tag every shard with its source dataset, so a takedown or license problem becomes a delete, not a re-crawl.
- **Limitations:** Fuzzy dedup only (MinHash). No semantic or embedding dedup. The paper reports systems numbers, not downstream model-quality numbers.
- **Slide idea:** a timeline of releases R1..R5 dropping into an LSM-tree-like stack of segments, which merge in tiers. Then a "withdraw dataset R3" button removes only R3-tagged segments.

### 3. BenchChecker: Assessing the Credibility of Bug-Fixing Benchmarks for LLMs
- **arXiv:** 2610.19447 · **submitted:** 2026-10-14 · **who:** Di Wu (George Mason University), with Palo Alto Networks
- **Problem:** Program-repair benchmarks such as SWE-bench leak into training data through public repository snapshots. Reported scores are inflated.
- **Method (diagram):** Two-stage forensics. It needs only text outputs plus public git history.
  1. **Repository presence test:** prompt the model with code prefixes from the repo and check whether it continues them verbatim. This infers whether the repo was in training data.
  2. **Patch presence test:** the fix patch may persist in later snapshots. Check this with similarity alignment plus test-suite verification.
- **Key numbers:**
  - AUC about **0.9** across six benchmarks. Validated on StarCoder-15B, StarCoder2-15B and CodeGen2-16B, whose training data (The Stack v2) is known.
  - On SWE-bench Verified and Multi-SWE-bench, removing contaminated items cuts most models' resolution rates by **more than 20% relative** on medium-difficulty tasks.
- **Monday takeaway:** Before you trust a code-agent eval, flag items whose fix commit predates the model's cutoff and still exists in the repo HEAD. Report scores on both the full set and the "clean" set.
- **Limitations:** Validated on open models with known training data. For closed models the method gives inference only. Code repair only.
- **Slide idea:** two bars per model, "reported" vs "decontaminated". Animate the clean bar shrinking by 20%+, with a git-graph showing the patch surviving into the snapshot.

### 4. Adversarial Benchmarks and BenchDoor Attacks
- **arXiv:** 2610.27533 · **submitted:** 2026-10-20 · **who:** Yixin Wu (HKUST Guangzhou), with University of Washington (Tadayoshi Kohno) and others
- **Problem:** Teams adopt any dataset that raises a benchmark score. An attacker can exploit this to ship a backdoor.
- **Method (diagram):** Five scenarios. Either the attacker poisons the benchmark's own train/test data, or ships an "improves-benchmark-X" training set. The poisoned data must (a) raise the benchmark score and (b) implant a trigger. The paper tests whether the trigger survives **synthetic rewriting** and **similarity-based decontamination**.
- **Key numbers:**
  - Benchmark gains were positive in **all 30** configurations.
  - Held-out attack success rate was **82.33–100%** at **2–10%** poisoning rates.
  - After synthetic regeneration *and* similarity-based decontamination, attack success rate was still **≥90.33%**. Tested on Qwen and Gemma models, with MCQ, classification and open QA.
- **Monday takeaway:**
  - "It raised MMLU" is not provenance.
  - Decontamination protects your *eval*. It does not protect your *model*.
  - Add trigger or backdoor scans and source review for third-party "benchmark-boosting" data.
- **Limitations:** Small and medium open models. Defenses are only explored for detectability.
- **Slide idea:** a "Trojan dataset" card. Benchmark score goes up (green), then a hidden trigger lights the model red. A decontam filter animates over it and fails to catch it.

### 5. Every Batch Is Its Own Validation Set: Leave-One-Out Gradient Matching (LOOM)
- **arXiv:** 2610.00436 · **submitted:** 2026-09-30 · **who:** Hongyu Chen (Sichuan University) with UESTC
- **Problem:** Online batch-selection methods that match the batch gradient rarely beat training on the full batch. The authors explain why and fix it.
- **Method (diagram):**
  1. In-sample gradient matching counts each example in its own target. The diagonal of the gradient Gram matrix rewards each example's *own noise*. So the objective prefers the noisiest examples, and its optimum is the full batch.
  2. **Remove the diagonal.** The other candidates in the batch are an independent sample. The objective becomes an unbiased estimate of update error against the population gradient.
  3. The optimum then weights examples by their **gradient SNR**. If SNR varies enough across examples, half a batch gives a lower-error update than the whole batch.
  4. The Gram matrix is computed in the **Adam-preconditioner metric**, during the normal backward pass. Greedy weighted subset selection has a (1−e^{−γ}) guarantee. No held-out data is needed.
- **Key numbers:**
  - Beats full-batch training by **+2.3** points (Llama-3.1-8B) and **+2.4** (Qwen2.5-7B).
  - Beats every in-sample gradient matcher by **+2.4**, and validation-guided GREATS and OPUS by **+1.6–2.0**.
  - Tested on 4 tasks (MMLU auxiliary-train → MMLU test, ScienceQA, ...) and 7 backbones from 1.5B to 8B.
  - With 20% of responses corrupted, LOOM picks injected label noise at **under 1/5 of its base rate**.
- **Monday takeaway:** If you do online selection in SFT, zero the diagonal of your gradient-similarity matrix. This also works as a free label-noise filter.
- **Limitations:** Needs per-example gradients, at least in a projected or low-dimensional form. The gain depends on how much SNR varies across the batch. Code release [UNVERIFIED].
- **Sketch (simplified: last-layer gradients, no Adam metric, top-k instead of weighted greedy):**
```python
import numpy as np
def loo_select(G, k):
    """G: (n, d) per-example gradients for one candidate batch. Returns k indices."""
    gram = G @ G.T
    np.fill_diagonal(gram, 0.0)              # the whole trick: drop self-credit
    score = gram.sum(1) / (len(G) - 1)       # alignment with the *other* examples
    return np.argsort(-score)[:k]
# With the diagonal kept (in-sample), noisy examples with large ||g_i||^2 win. With it dropped, they lose.
```
- **Slide idea:** animate the Gram-matrix heatmap. The diagonal glows (noise), gets wiped to zero, and the selected rows re-rank. Then a corrupted-label counter drops from 20% to under 4%.

### 6. VerifierBench: Benchmarking the Generation of Executable Verifiers for LLM Agents
- **arXiv:** 2610.28679 · **submitted:** 2026-10-19 · **who:** Jianing Yin (University of Pennsylvania), with UC Berkeley (Dawn Song), UIUC, NYU, Rochester
- **Problem:** Synthetic agent data is filtered with LLM-written executable verifiers. How good are those verifiers?
- **Method (diagram):** 222 tasks from 6 agent benchmarks (tool-call, state-based, code). For each task, the agent writes a verifier from the instruction and the environment. The verifier is run against **4,993 hidden test cases**, which include *alternative valid solutions* and *attacks*. A six-check audit (Verifier4Verifier, "V4V") screens the source verifiers and test suites.
- **Key numbers:**
  - Normalized balanced accuracy across 19 models ranges from **10.6 to 62.1**.
  - Best is GPT-6-astra at 62.1 (TPR 67.4, TNR 94.6). Then Claude Opus 4.8 at 54.0 and Kimi K3 at 53.4.
  - Verifiers reject invalid solutions much better than they accept valid ones.
  - Most false rejections come from verifiers that accept **no** tested solution at all.
- **Monday takeaway:**
  - Every LLM-written verifier used to filter synthetic data needs a **positive control**: it must pass at least one known-correct solution, and ideally several *differently shaped* correct ones.
  - Otherwise your filter silently deletes valid diversity.
  - Self-testing does not help, because the agent writes test solutions that share the verifier's wrong assumptions.
- **Limitations:** Agent and code domains only. The hidden test sets are themselves curated.
- **Slide idea:** a 2×2 confusion grid (valid/invalid × accept/reject). Most mass sits in "valid → reject". Then a "positive control" gate animates in front of the verifier.

### 7. FROST: Online Synthetic Data Filtering via Real-Anchored Utility
- **arXiv:** 2609.29988 · **submitted:** 2026-09-24 · **who:** Yanran Wu (Purdue; work done at Meta), with Meta
- **Problem:** Synthetic data helps or hurts depending on what the learner needs *now*. Static fidelity and diversity filters ignore this.
- **Method (diagram):**
  1. Estimate each synthetic sample's utility from **gradient alignment with real training data**.
  2. Calibrate batch utility against an EMA of recent history. This decides **when** to filter.
  3. Only in "out-of-band" batches, drop samples with an **IQR rule**. This decides **what** to drop.
  4. No external verifier and no held-out set.
- **Key numbers:**
  - Filters about **20–30%** of synthetic data and improves real-task performance. Tested on image classification (3 generators) and text-to-SQL LLM fine-tuning.
  - In Meta's production **ads re-ranking**, it turns a **0.211% NE regression** (from the full noisy synthetic pool) into a **0.096% NE improvement** over real-only training. Prior work treats 0.02% as significant.
- **Monday takeaway:** If synthetic data makes things worse, do not throw it all away. Gate it online, using gradients from real data as the anchor.
- **Limitations:** Needs real data in every step. Utility is a first-order gradient approximation.
- **Slide idea:** a stream of batches on a conveyor belt with an EMA band. Batches inside the band pass untouched. Out-of-band batches open, and their IQR outliers fall off. A final NE gauge swings from red to green.

### 8. The Differential Reasoning Router (DRR): Cost-Aware LLM Annotation in E-commerce
- **arXiv:** 2608.30224 · **submitted:** 2026-08-31 · **who:** Cheng Lyu et al. (Wayfair)
- **Problem:** LLM annotation of product attributes starts cold: few labels exist, and the value of reasoning models is unknown. Using the reasoning model by default is expensive.
- **Method (diagram):** A small MLP over cached embeddings predicts, **per sample and per business rule**:
  - p(direct model correct)
  - p(reasoning model correct)
  - p(both fail), the "ambiguity" head
  
  Routing: easy items go to the direct model. Reasoning is used only when its expected gain is positive. Likely double-failures and rule disagreements go to **humans**. The human labels then feed prompt work, SFT, calibration and rule refinement.
- **Key numbers:** In a production workflow, DRR matches the accuracy of the strongest confidence-based router and saves **>60% of reasoning tokens**. The paper also says this is "roughly one-fifth higher" savings than that router.
- **Monday takeaway:** Do not use "reasoning model as fallback". Learn *differential* success probabilities, and send the both-fail cases to humans. Those cases are also your best new training labels.
- **Limitations:** One company and one workflow. The internal dataset is not released [UNVERIFIED].
- **Slide idea:** a three-lane highway (Direct / Reasoning / Human) with items routed by a small predictor, and a token-cost meter.

### 9. QUORUM: Quality-Optimized Routing Using Multiple Annotators
- **arXiv:** 2608.27974 · **submitted:** 2026-08-28 · **who:** Antonio Purificato (Amazon / Sapienza), with Amazon and Inria
- **Problem:** Send each item to a human or an LLM under a fixed budget, without relying on LLM self-confidence.
- **Method (diagram):** Linguistic and embedding features estimate instance difficulty and per-annotator quality. A budget-aware router assigns human or LLM. It can request **multiple annotations** per item and combines them with agreement-based rewards. Two regimes: a fixed human budget ("auditor style") and a dollar budget with different annotator costs. Claude Sonnet 4.5 and Nova Pro were among the LLM annotators.
- **Key numbers:** Up to **+34.4% annotation quality** and **−8.8% cost** versus competing routers. With a budget of 200 human labels, it beats all other routers. The standalone LLM baseline was **60.4%** accuracy. Code: github.com/amazon-science/QUORUM.
- **Monday takeaway:** Route on cheap, observable difficulty features, not on LLM verbalized confidence. Buy a second label only where predicted disagreement is high.
- **Limitations:** Gains vary by task. Features are hand-designed.
- **Slide idea:** a budget bar draining as items flow either to a human icon or an LLM icon. Disputed items fork into two annotators and merge back.

### 10. LLM Judge Validation Under Sparse Overlap: From Inference to Design
- **arXiv:** 2609.31857 · **submitted:** 2026-09-25 (v1, per arXiv API) · **who:** Junxuan Li (Adobe), with Adobe Research
- **Problem:** Teams validate an LLM judge with few human co-labels. How much overlap is enough?
- **Method (diagram):**
  - Define the overlap rate ρ = the fraction of items labeled by both raters in a pair, averaged over pairs.
  - Prove that sparsity, not the choice of agreement coefficient, is the first-order cause of wrong deploy decisions.
  - Planning recipe: m* = ⌈z²_{1−α/2} · σ² / δ²⌉ co-labeled items.
  - A zero-cost **stratified allocation** of the overlap items.
- **Key numbers:**
  - At **5% overlap**, wrong-decision rate is **25%**, and the chance of picking the wrong best judge among 10 is **65%**.
  - **ρ ≥ 0.25** is enough for non-borderline judges. Borderline judges stay hard.
  - Stratified allocation **halves false-rejection rates** versus random sampling, when the strata are informative.
  - Validated on 10 LLM judges.
- **Monday takeaway:** Budget for at least 25% double-labeled items when you validate a judge. Stratify which items get double labels, for example by length, topic or predicted difficulty.
- **Limitations:** Theory uses a CLT approximation. Borderline judges cannot be resolved cheaply.
- **Slide idea:** a slider for overlap from 5% to 25%. A "wrong-judge picked" probability gauge falls from 65%. Then show the formula m*.

### 11. Curating Merchant-Matching Training Data with Two Confidence-Gated Local LLM Judges
- **arXiv:** 2609.33878 · **submitted:** 2026-09 (v2 2026-10-04) · **who:** Donghao Huang (Mastercard R&D), with Singapore Management University
- **Problem:** Pseudo-labels for entity matching. Two errors must be told apart: "the teacher abstained" vs "no entity exists". A false no-match label contaminates the negatives.
- **Method (diagram):** Two local LLM judges (Muse Glimmer 30B and Gemma 4 31B). A label is kept only when the judges **agree**. There are **separate thresholds** for positive selections and for abstentions/negatives. The ordered thresholds make the positive and negative sets disjoint.
- **Key numbers:**
  - At thresholds (0.86, 0.80): **81.7% coverage** (1,633/2,000) at **96.88% purity**. Positive purity is 99.47%, negative purity 93.38%. This is more than 2 pp better than either judge alone.
  - A symmetric threshold of 0.86 adds 40 wrong no-match labels.
  - Higher reasoning effort gave **no clear F0.5 gain** and **1.8–5.0× latency**.
- **Monday takeaway:** Threshold and audit positive and negative pseudo-labels **separately**, because negatives are where errors hide. Two cheap agreeing judges beat one judge with more reasoning effort.
- **Limitations:** Measures label purity only. Downstream student utility is not shown, as the authors state.
- **Sketch:**
```python
def gate(j1, j2, t_pos=0.86, t_neg=0.80):
    """j = (label, conf); label is an entity id or None (= no match)."""
    (l1, c1), (l2, c2) = j1, j2
    if l1 != l2:
        return "REVIEW"
    if l1 is not None:
        return l1 if min(c1, c2) >= t_pos else "REVIEW"
    return "NO_MATCH" if min(c1, c2) >= t_neg else "REVIEW"
```
- **Slide idea:** two judge avatars vote. Matching votes go to a purity meter, which splits into "positives 99.5%" and "negatives 93.4%" to show the asymmetry.

### 12. VulValidate: Auditing Function-Level Vulnerability Labels with Executable Evidence
- **arXiv:** 2610.05103 · **submitted:** 2026-10-04 · **who:** Leizhen Zhang, Sheng Chen (University of Louisiana at Lafayette)
- **Problem:** Vulnerability datasets mark a function "vulnerable" just because a security patch touched it. This is systematic label noise.
- **Method (diagram):** LLM agents rebuild the vulnerable and fixed revisions, choose dynamic-analysis tools, refine triggering inputs, and compare runtime behavior on both sides. The result decides function-level attribution. Evidence is packaged in Docker for cold replay.
- **Key numbers:**
  - Audited all **35,849** "vulnerable" labels in BigVul, PrimeVul and DiverseVul.
  - Results: **57.2% confirmed**, **19.0% corrected**, 22.3% undecided, 1.5% unmeasurable.
  - Expert blind review agreed with 90–92% of confirmations and 92.6–99.0% of corrections.
  - Corrected labels **lower F1 for all 5 detectors**, so earlier scores were inflated. Retraining on corrected labels improves 4 of 5 detectors.
- **Monday takeaway:** If labels come from a heuristic like "touched by fix commit", audit them with *executable* evidence. Expect about 1 in 5 to be wrong.
- **Limitations:** Security domain. 22% stay undecided.
- **Slide idea:** a stacked bar of 35,849 labels splitting into confirmed/corrected/undecided. The F1 of 5 detectors drops when re-scored.

### 13. Pick the Mixture, Not the Samples: Combinatorial Data Selection for LLMs
- **arXiv:** 2610.14028 · **submitted:** 2026-09-30 · **who:** Luyang Zhang (CMU), with UC Santa Cruz
- **Problem:** Sample-level attribution scores assume utilities add up. In real instruction pools, domains complement each other, while samples inside a domain are redundant.
- **Method (diagram):**
  - The framework separates **attribution** (how to score samples) from **selection** (which subset to pick), and models pairwise interactions.
  - **Mixture-then-Select:** stage 1 decides the per-domain quota. Stage 2 ranks within each domain by any attribution score.
  - The gap to the optimal subset is linear in selection size and does not depend on pool size.
- **Key numbers:** Beats strong baselines by **20–54%**. Pool: 50K samples from 13 public sources in 8 skill domains (math, code, QA, dialog, reasoning, NLP, complex-instruction, creative), plus a 200K pool. The result holds across attribution methods.
- **Monday takeaway:** Set domain quotas first, then rank inside each domain. Never take a global top-k by influence score.
- **Limitations:** Domain labels must exist. Interactions are modeled pairwise.
- **Slide idea:** a global top-k picks 80% math (bar chart). Mixture-then-Select first carves quotas (pie), then fills each slice.

### 14. Lev: Scalable Data Diversification for LM Pretraining via Leverage Score Sampling
- **arXiv:** 2609.32484 · **submitted:** 2026-09-26 · **who:** Zailin Ma (Peking University), with Wizard Intelligence Learning Lab and Tsinghua
- **Problem:** Quality filters prefer text that looks like the reference corpus, for example educational or QA-style text. This causes a **diversity collapse**.
- **Method (diagram):** Embed the documents. Iteratively pick the samples with the highest **leverage score**, which means the most expansion of determinantal volume. Leverage scores avoid recomputing the covariance matrix.
- **Key numbers:**
  - Up to **72× faster** than the DiSF diversification baseline, with **+9.2% Vendi score**.
  - On CommonCrawl, up to **+1.31%** accuracy across 7 tasks.
  - On StarCoderData, **−3.08% bits-per-byte** versus DiSF.
  - **Cross-domain collapse:** CC filtered with DCLM-fastText keeps too little code, so code performance drops.
- **Monday takeaway:** After your quality classifier, run a diversity pass, and check per-domain retention (code, math, non-English). A quality filter alone quietly deletes domains.
- **Limitations:** Depends on the embedding model. Gains are modest in absolute terms.
- **Slide idea:** a 2-D embedding scatter. The quality filter keeps one dense cluster. Leverage sampling then adds points at the edges until the hull expands.

### 15. AFCS: Atomic-Fact-Conditioned Synthesis for Factual Knowledge Pretraining
- **arXiv:** 2610.20086 · **submitted:** 2026-10-14 · **who:** Yunhao Wang et al. (Tencent Hunyuan)
- **Problem:** Rephrasing pipelines (WRAP, Nemotron-CC) rewrite whole passages and silently drop secondary entities, list and table entries, and dates.
- **Method (diagram):** Document tree → structure-aware **atomic fact extraction** → **source-grounded verification** of each fact → local context expansion → **one generation per fact**, in several formats (QA, prose, ...).
- **Key numbers:**
  - Continued pretraining on FineWiki, 20B tokens.
  - At **32B**: SimpleQA **9.11** vs WRAP 7.10 and Nemotron-CC 6.82. PopQA **37.22** vs 32.46 and 33.01.
  - At **7B**: +2.00 SimpleQA and +6.74 PopQA over base.
  - A 100B-token mid-training run gives **+1.09** on a 12-task average.
- **Monday takeaway:** For knowledge injection, make the **fact** the unit of synthesis and verify each fact against the source. Measure source-fact coverage of the synthetic corpus as a data-quality KPI.
- **Limitations:** Absolute SimpleQA scores stay low (single digits). Extraction cost is high.
- **Slide idea:** a source doc explodes into atomic fact chips. Each chip gets a green "verified" tick, then spawns 3 formatted samples. Compare with WRAP, which loses the table rows.

### 16. CRDS: Compute-Responsive Data Selection for Reasoning Post-Training
- **arXiv:** 2610.20057 · **submitted:** 2026-10-14 · **who:** Liang He (UT Austin), with AMD, Warwick, Surrey
- **Problem:** Which problems should you SFT on, if the goal is better use of test-time compute?
- **Method (diagram):** Run each problem at a low budget and at a high budget. Bucket it as solved-at-low, unresolved, or **compute-responsive** (fails at low, succeeds with more reasoning). Train on the compute-responsive set. Build it carefully: truncation, repeated errors and similar effects are confounds.
- **Key numbers:** On Qwen3-8B, SFT on compute-responsive examples recovers **45.3%** of held-out low-compute failures, versus 40.6% for already-solved examples. Overall accuracy reaches **51.8%**. The method beats non-CR training at every budget from 512 to 4,096 tokens. The result also holds for Llama-3.1-8B and under on-policy distillation.
- **Monday takeaway:** Pick training items by their **response to compute**, not by difficulty or pass rate. Compute-responsive sets are model-specific, so rebuild them per model.
- **Limitations:** Needs two passes of inference over the pool. Math and reasoning only.
- **Slide idea:** three bins (solved / responsive / hopeless) filling as a budget slider rises. Only the middle bin goes to training.

### 17. Effective Synthetic Data Curation Requires Group-Level Signals
- **arXiv:** 2610.00779 · **submitted:** 2026-09-30 · **who:** Cathy Jiao, Chenyan Xiong (CMU LTI)
- **Problem:** Synthetic data is homogeneous. Per-sample influence scores are almost identical, so they cannot rank it.
- **Method (diagram):** Compare the individual-level proxy oracle with a **group oracle**, which measures the utility of a set trained jointly (groups of 128 to 5,120 samples). This is done in pre-training and post-training. Then the paper tests which common curation methods include group signals. Last, a cheap diagnostic: **within-group gradient diversity** tells you where group scoring is worth its compute.
- **Key numbers:** Groups with near-identical individual scores have widely spread group scores. Among widely used curation methods, only the ones with group-level signals beat baseline, and the gains are mostly in generative capability. Exact deltas are in Table 1 of the paper [not extracted].
- **Monday takeaway:** Score synthetic data by **batches or clusters** (for example, one generator prompt template = one group), not by single samples. Spend group-level compute where within-group gradient diversity is low.
- **Limitations:** Group oracles are expensive. The diagnostic is a heuristic.
- **Slide idea:** 10 groups with flat individual scores (a flat bar row). Flip to group scores and the bars spread out.

### 18. No Model Required: Text Entropy-Rate Filtering Mitigates Iterative Fine-Tuning Collapse
- **arXiv:** 2610.01493 · **submitted:** 2026-10-01 · **who:** Lewis Mitchell (Adelaide University)
- **Problem:** Collapse filters usually need model log-probs, an oracle, or fresh human data.
- **Method (diagram):** Compute the non-parametric **Kontoyiannis entropy-rate estimator** h_k from raw text, using match-length statistics. Each generation produces 80 documents, and 40 are kept for the next QLoRA generation. Compare random selection, log-prob entropy selection, and h_k selection.
- **Key numbers:**
  - Six-generation QLoRA chain on Llama-3.1-8B.
  - Log-prob filtering gave **no significant** diversity benefit (p > 0.23).
  - h_k filtering gave **+42% unique trigrams**, **+30% vocabulary** and **−19% repetition** (all p < 0.001).
  - As a proxy for entropy: β = 0.924, R² = 0.746. As a collapse detector: ρ = +0.454.
- **Monday takeaway:** You can add a zero-model, CPU-only diversity filter or monitor to a synthetic-data loop.
- **Limitations:** Very small scale (1,520 docs), a single lineage, and diversity metrics only (no task accuracy).
- **Sketch (simplified Kontoyiannis-style estimator over word tokens, O(n²), for a demo):**
```python
import math
def entropy_rate(tokens):
    """Kontoyiannis-style: H ≈ n·log2(n) / Σ Λ_i, where Λ_i is the length of the shortest
    sequence starting at i that does not appear starting at any earlier position."""
    n, total = len(tokens), 0
    for i in range(n):
        L = 1
        while i + L <= n and any(tokens[j:j+L] == tokens[i:i+L] for j in range(i)):
            L += 1
        total += L
    return n * math.log2(max(n, 2)) / total
# Keep the top half of generated docs by entropy_rate(doc.split()). Repetitive docs score low.
```
- **Slide idea:** six generations as stacked text panels. The repeated phrases get highlighted and grow in the unfiltered chain but stay sparse in the h_k chain.

### 19. RAG Collapse: LLM Responses Collapse When Retrieved Documents Are Self-Authored
- **arXiv:** 2608.22118 · **submitted:** 2026-08-22 · **who:** Gregory Druck, Ethan Smith (Graphite Growth)
- **Problem:** Collapse without any training: the model retrieves web pages that it (or another model) wrote earlier.
- **Method (diagram):** Three simulation types (replace-all, replace-one, search). Over rounds, the model's answers become the reference documents. The paper measures response similarity (paraphrase rate, entity-ranking Kendall's tau). 1,528 simulations, 3 model families, 1,019 prompts, more than 1M API calls.
- **Key numbers:**
  - **79.6%** of simulations collapse (1,216/1,528).
  - In one experiment, the paraphrase share among response pairs rose from 22% to **89%**.
  - **A single self-authored reference** can trigger collapse, because the LLM over-cites its own content. This holds even when reference quality is controlled.
- **Monday takeaway:**
  - Tag provenance in your RAG index: AI-written vs human, and which model.
  - Down-weight or cap self-authored sources.
  - Monitor answer diversity across users for the same query.
- **Limitations:** A simulation study, from a small company. Real search engines mix sources.
- **Slide idea:** a loop of answer → published page → retrieved → answer. Each loop the answer card variants merge into one card.

### 20. Shared Autoregressive Context Can Distort Relationships in Synthetic Data
- **arXiv:** 2609.32546 · **submitted:** 2026-09-26 · **who:** Thomas S. Robinson (London School of Economics)
- **Problem:** Engineers generate N synthetic records per API call to save cost. Earlier records then become context for later ones.
- **Method (diagram):** A matched experiment on 2,000 European Social Survey profiles: 1 vs 10 respondents per request, with everything else fixed. Causal check: re-pair the preceding values while keeping the marginals fixed. Mitigation tested: hide the preceding answers.
- **Key numbers:**
  - 10-per-request **raises the error in within-country correlations by 48–58%** (Qwen3.8-27B) and **114–127%** (Llama-3.3-70B), across 3 seeds.
  - The distortion mostly comes from exaggerated relationship strength.
  - Hiding history lowers correlation error but worsens the marginals.
- **Monday takeaway:**
  - Request batching is part of your data-generating process.
  - Generate one record per call, or randomize and hide prior records.
  - Validate synthetic data on the *analysis it will feed* (correlations, regressions), not only on marginals.
- **Limitations:** Survey and tabular domain. Two models.
- **Slide idea:** one prompt spawning 10 respondents. Arrows from earlier answers bend later ones, and a correlation matrix heatmap saturates.

---

## Also notable (short entries, all in window, abstract-level only)

| arXiv | Title (short) | One-line takeaway |
|---|---|---|
| 2609.19754 | AutoData: Agentic Search for Pre-training Data Selection (Weco AI / U. Amsterdam) | An AIDE-style agent searches over *selection programs* on a 125M GPT-2 proxy overnight. It beats DCLM classifier, perplexity filter, RegMix and default ClimbMix. Best val-bpb from 125M to 897M without re-tuning. |
| 2610.14238 | Agentic Data Engineering for LLMs (UNC, Alibaba, PKU) | Agents iterating on selection, reward and curriculum strategies gave up to +13.34% AIME25 pass@32 and +5.85% on 4 held-out benchmarks. Later in-loop gains did **not** always generalize, so hold out evals the agent never sees. |
| 2610.13321 | Host-Aware Web Crawling for LLM Pretraining Data (Common Crawl Foundation) | About half of quality-score variance is *between hosts*. Sample a few pages per host, then go deep on the good hosts. This gives up to 7.8× more high-quality pages per fetch than uniform breadth. Harmonic centrality is a weak signal. |
| 2607.24717 | DataOrchestra (Zhen Huang, ..., Pengfei Liu; affiliation [UNVERIFIED]) | A per-chunk orchestrator decides drop, keep or clean, then picks edit or rewrite tools. Stable gains over single processing methods across 11 benchmarks at 0.5B–7B, with less processing compute. Numbers not extracted. |
| 2609.12353 | SynthSentry | A corpus-level synthetic-contamination score from lexical-diversity collapse, n-gram tail truncation and perplexity variance. A naive quantile threshold ran 4× over the false-positive budget, so it needs covariance shrinkage plus a bootstrap threshold. Small-scale. |
| 2608.04268 | Fairness Collapse | With recursive synthetic training on Bias in Bios, **bias rises before LM metrics show collapse**. Add fairness probes to collapse monitoring. |
| 2608.30619 | Covert Targeted Bias Injection via Benign Synthetic Data | A misaligned teacher's filtered, benign-looking synthetic data passes targeted bias to students. The paper suggests log-linearity-based scoring as a screen. |
| 2609.20027 | Can Data Attribution Filter Out Subliminal Learning? Not Reliably (Weckbecker et al.; affiliation [UNVERIFIED]) | EK-FAC token-level filtering removes part of the effect. GradCos variants help little. Do not rely on attribution as a safety filter. |
| 2610.04978 | What Will Post-Training Fix? | Independent RL runs agree on which problems improve (noise ceiling about 0.9). A priori signals (pass rate etc.) explain only 0.30/0.24 of the explainable variance. An existing checkpoint's per-problem gains predict a new run better. |
| 2609.00494 | Human-Anchored Factuality Evaluation with Strategic Annotation (Yu Wang et al.; affiliation [UNVERIFIED]) | Choose human-labeled items by judge *failure modes* (incomplete evidence, temporal mismatch, ...), not only by low confidence. +40.3% / +27.1% effective sample size. |
| 2610.18588 | Decomposing and Predicting Annotation Disagreement | 20 binary LLM-answered questions plus a classifier predict contested items. +10.5 ROC-AUC over direct prompting. 8 questions are enough (within 1.5 AUC). |
| 2608.24192 | BALIGN: Preference Data Selection for the Alignment Tax (Minsu Kim et al.; affiliation [UNVERIFIED]) | Filter DPO pairs by reference log-prob margin, chosen/rejected length gap, and TF-IDF similarity to general corpora. This keeps base capabilities. |
| 2610.24888 | EmbDivBench: Measuring Data Diversity with Embeddings | 21 measures compared. The common Mean Pairwise Distance is beaten. **Graph Entropy** is the best overall choice. |
| 2609.00062 | RePro: Proof-Verified Benchmark Rewriting | Rewrites GSM8K/MATH with Lean-verified answers (100% validity). Several models drop, which suggests memorization. |
| 2609.27510 | Uncheatable Eval | Compression rate on freshly published text as a contamination-resistant base-model eval. 80 models, 14 categories. Correlates with MMLU. |
| 2609.21888 | ETD: Pretraining-Data Detection, Free-Energy View | Loss relative to predictive entropy (an "inclined boundary"). Up to +3.5% AUROC and +5.1% TPR@5%FPR over membership-inference baselines. |
| 2609.18878 / 2610.15617 | Fisher-Rao collapse bounds / Screening collapse | Theory: the minimum human-data ratio under the Fisher-Rao metric differs from earlier Euclidean bounds. Recursive pseudo-labels also corrupt *feature screening* before model fitting. Accumulating data helps, a fixed real fraction does not fully help. |
| 2610.16876 | CLIVO: Differentiable Cluster-Based Instruction Mixing | 100K of an 8M VLM instruction pool (1.25%) reaches 97.2% of the full-data score. +1.16 to +1.55 over the best selection baseline. |
| 2608.29144 | ATOM: Error Tolerance in Synthetic Data | Models tolerate *operand* errors (wrong numbers) but collapse on *operator* errors (wrong operation). Filter on operators. +3.1% over LIMA. |
| 2609.02015 | Output Format Confounds Data Quality | A skill can give +40 pts in the training format and be nearly invisible in other formats. Evaluate data quality across output formats. |

---

## Cross-paper trends (for a "what changed in 2026" slide)

1. **Quality filters are now part of the problem.** FineWeb/DCLM filters prefer AI-written text (2.3× and 9.8× pass rates, #1). They delete code and long-tail domains (#14, plus the long-tail pose audit 2609.31896). Many teams now run filters in this order: quality → AI-text detection → diversity rebalancing.
2. **Group, mixture or set beats per-sample scoring.** Mixture-then-Select (#13), group-level synthetic curation (#17), CLIVO, and LOOM's leave-one-out batch view (#5) all show that a subset's value is not additive. Practice: set quotas first, then rank inside each quota.
3. **Verification needs its own verification.** LLM-written verifiers over-reject (#6). LLM judges need ≥25% overlap to validate (#10). Two gated judges beat one strong judge (#11). Executable evidence finds 19% wrong labels (#12). Lean proofs make rewritten benchmarks valid (RePro). Pattern: positive controls + agreement + executable ground truth.
4. **Collapse moved from theory into operations.** It now shows up in wild web data (#1), RAG loops without training (#19), request batching (#20), fairness drift that appears before loss drift (2608.04268), and covert channels (2608.30619, BenchDoor #4). Defenses are provenance tags, cheap model-free monitors (#18, SynthSentry), and online real-anchored gating (#7).
5. **Cost-aware routing for annotation is now standard in industry.** Wayfair (#8), Amazon (#9), Mastercard (#11) and Meta (#7) all route by predicted *differential* value (direct vs reasoning vs human). Reasoning effort often does not pay for labeling (#11: no F0.5 gain, 1.8–5× latency).
6. **Agents are entering the data loop**, under the same caveat each time: hold-out evals the agent never sees (AutoData, ADE 2610.14238, DataMaster 2608.10579, DataOrchestra).

## Suggested 6-slide arXiv block for the deck

1. "Your quality filter loves AI text": funnel animation (#1) + Lev hull expansion (#14).
2. "Dedup as an index, not a job": PUFFER segments (#2).
3. "Your benchmark is lying, and can be weaponized": BenchChecker bars (#3) + BenchDoor trigger (#4).
4. "Select sets, not samples": LOOM diagonal wipe (#5) + Mixture-then-Select quotas (#13).
5. "Who checks the checker?": VerifierBench 2×2 (#6) + overlap slider (#10) + two-judge gate code (#11).
6. "Collapse in production": RAG loop (#19), batching heatmap (#20), entropy filter code (#18), FROST gate (#7).

## Sources (all arxiv.org/abs/<id>; full text read at arxiv.org/html/<id> for #1–#20 except where noted)
2609.40295, 2608.28622, 2610.19447, 2610.27533, 2610.00436, 2610.28679, 2609.29988, 2608.30224, 2608.27974, 2609.31857, 2609.33878, 2610.05103, 2610.14028, 2609.32484, 2610.20086, 2610.20057, 2610.00779, 2610.01493, 2608.22118, 2609.32546. Abstract only: 2609.19754 (HTML partly), 2610.14238 (HTML partly), 2610.13321 (HTML partly), 2607.24717, 2609.12353, 2608.04268, 2608.30619, 2609.20027, 2610.04978, 2609.00494, 2610.18588, 2608.24192, 2610.24888, 2609.00062, 2609.27510, 2609.21888, 2609.18878, 2610.15617, 2610.16876, 2608.29144, 2609.02015, 2608.10579.
