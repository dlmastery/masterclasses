# arXiv sweep: AI evaluation methodology (2026-07-23 .. 2026-10-23)

Subtopic: benchmark design, statistical rigour (CIs, variance), LLM-as-judge reliability, slice metrics, calibration, contamination, cost-sensitive thresholds, quality/model cards.
Built for the hands-on "Customizing modern AI + data-centric AI" deck. The older file `research-custom/07-eval-design.md` already covers the classics (Miller 2411.00640, Zheng MT-Bench, G-Eval, Guo calibration, Model Cards, Chatbot Arena BT). This file adds only **new** papers from the last 3 months.

## Method and verification status
- Source: arXiv advanced search (submitted-date filter 2026-07-23..2026-10-23). The export.arxiv.org API returned HTTP 429 (shared rate limit), so I used the arxiv.org/search HTML, which shows the full abstract. Queries: abstract "LLM-as-a-judge" (1,467 hits), title "judge" (200+), title "contamination", title "leaderboard", title "calibration LLM", title "cards", title "item response theory", title "abstention", title "pass@k", title "subgroup", abstract "confidence intervals benchmark LLM".
- All numbers below come from the abstract on the arXiv search page. Where marked **[HTML]**, I also read the arXiv HTML full text, which also gave the affiliations.
- The arXiv IDs (2608.x, 2609.x, 2610.x) put every v1 inside the window.
- Not verified: anything marked [UNVERIFIED]. I ran no code (pip is blocked). I checked the `evalstats` API against its GitHub README and PyPI (version 0.3.3, Python >= 3.9).
- Odd artefact: many of the window's judge papers name a system "Jev"/"JEV" (a "decision model"). I did not verify what it is and left it out.

---

## Ranked papers (by practical impact for an engineer)

### 1. 2609.35815: How to Run Statistics over LLM Judges and Trust the Results: Calibrated Inference for Small-Sample AI Evaluation with evalstats
- **Submitted:** 2026-09-20. **Author:** Ian Arawjo (sole author per the HTML), DIRO, Université de Montréal [HTML].
- **Problem:** Teams report "prompt B beats prompt A" from N<100 items scored by an LLM judge. They use bootstrap CIs and run no correction for the judge's bias.
- **Method (diagram):**
  1. Long-format table (item, prompt/model, score, optional run).
  2. A Monte Carlo study picks the CI and p-value method for each data type and N.
  3. For judge scores, label a **uniformly random** subset with humans.
  4. Prediction-powered inference (PPI/PPI++) corrects the means, CIs and tests. The paper adds "bootstrap-adaptive power tuning" for small calibration sets.
  5. Family-wise error rate (FWER) correction across all pairs, then rank bands.
- **Key results:**
  - Bootstrap CIs were "overconfident nearly everywhere". In the paper's 8-prompt example with 28 pairwise comparisons, the percentile bootstrap covered the true difference only 88% of the time (nominal 95%). BCa covered 82% and separated truly tied prompts 12% of the time (nominal 5%).
  - Recommended defaults: **Wilson** interval for binary means, **logit-transformed t-interval** for numeric scores, **Bonett-Price** for paired binary differences, Romano-Wolf step-down for FWER [HTML].
  - Running tests on raw judge scores inflates false positives. False-positive risk on Likert data peaks at **IRR 0.80-0.90** ("almost perfect" agreement) and returns to nominal only above 0.99 [HTML].
- **Monday takeaway:** Stop using bootstrap CIs for small eval sets. Report Wilson CIs. Human-label a *random* sample (not just the borderline cases) and PPI-correct the judge scores before you claim a winner.
- **Runnable (from the README; not executed here):**
```python
# pip install evalstats   (PyPI 0.3.3, MIT)
import pandas as pd, evalstats as es
df = pd.read_csv("results.csv")          # columns: prompt, item, score  (model, run optional)
evaldata = es.load_from(df)
result = es.compare(evaldata, factors="prompt")   # method="auto", correction="auto"
result.summary()                                   # CIs, pairwise tests, rank bands

# Judge-bias correction with a random human-labelled subset (human_score NaN elsewhere)
alignment = es.judge_alignment(evaldata, llm_metric="llm_score", human_groundtruth="human_score")
result = es.compare(evaldata, factors="model", metric="llm_score",
                    alignment={"llm_score": alignment})
```
- **Gotcha (README, IMPORTANT box):** If humans label only selected items (missing-not-at-random), PPI "can stay badly miscalibrated no matter how many items you label". Simulations show this from 15 to 300 labelled items out of 400.
- **Limitations:** Validation of the multi-run CIs is deferred to future work. The recommendations target N<100.
- **Slide idea:** "Your bootstrap is lying." 28 interval bars animate in, then the ~12% that miss the true value flash red. Then switch to Wilson + Šidák and the misses fade. Final frame: the 4-line evalstats snippet.

### 2. 2609.33044: Pinned and Still Unstable: Within-Judge Verdict Variance and the Noise Floor of LLM-as-Judge Leaderboards
- **Submitted:** 2026-09-27 (v1, per arXiv API). **First author:** Krishna Chytanya Ayyagari. Org [UNVERIFIED; HTML returned 404].
- **Problem:** Teams assume a judge pinned to a model version at temperature 0 gives reproducible verdicts.
- **Method:** The authors re-ran 4 frontier judges on "a single major enterprise cloud platform" with identical inputs on Arena-Hard, AlpacaEval 2 and MT-Bench. They defined a per-item flip rate, a stability profile (waver fraction × conditional intensity) and adjacency separability, then ran a paired hierarchical bootstrap over prompts × re-runs.
- **Key results:**
  - Per-item flip rate is ~5% on average and **~40% on close-call items**. Across judges it ranges 40× (0.13% to ~10%).
  - For the main judge the top-K ranking is stable, but **1/5 to 3/4 of adjacent leaderboard positions are statistically indistinguishable**. Finite prompt sampling drives this more than the judge does.
  - Kendall τ between the Gemini and Sonnet judges on Arena-Hard is 0.42-0.64.
  - 12 of 15 expected orderings survive every re-run of the main judge. Only 8 survive every judge.
- **Monday takeaway:** Run the judge 3+ times on the same inputs, publish the flip rate, and report results under 2 judges from different families. Treat temperature 0 as *not* deterministic on hosted endpoints.
- **Limitations:** One cloud platform. The infrastructure causes are not isolated.
- **Slide idea:** A "same input, same seed" slot machine. A grid of 500 items re-runs 3 times and the flipped cells blink. Zoom to the close-call band, where 40% blink.

### 3. 2610.30512: Behind Aggregate Scores: What Systematically Varying Arena-Hard's LLM Judge Reveals
- **Submitted:** 2026-10-21. **Author:** Louise Yorke, University College London [HTML]. NeurIPS-style workshop "JUDGe: Can We Trust the Judge?" [HTML].
- **Problem:** A stable aggregate score is read as a sign that individual verdicts are reliable. This matters when the verdicts become DPO preference labels.
- **Method:** 500 Arena-Hard v2.0 prompts with two models' answers held fixed. GPT-4.1 judges under a 2×2×2 grid (criteria × output format × task framing). Each setup is re-run unchanged at temperature 0 on a pinned version.
- **Key results:**
  - A re-run of the default setup moves the aggregate by ~1 point but **changes the win/tie/loss outcome on 21.2% of prompts**.
  - "Verdict without reasoning" changes 28.2 pp more outcomes than the rerun baseline and lowers the score by 4.09.
  - Accuracy-first criteria change 6.7 pp more outcomes while the aggregate barely moves.
- **Monday takeaway:** If your judge produces *training labels* (DPO/RM data), measure prompt-level agreement between two re-runs. Drop or re-judge the unstable pairs. Do not trust the aggregate score.
- **Limitations:** One judge (GPT-4.1) and one benchmark.
- **Slide idea:** Two identical bar charts (aggregate 1 pt apart). Click and they explode into 500 dots: 21% change colour.

### 4. 2609.22512: Agreement Overstates Evidence: Error Dependence in LLM Judge Consensus
- **Submitted:** 2026-09-18. **Authors:** Elias Hossain, Niloofar Yousefi, Ser-Nam Lim, University of Central Florida [HTML].
- **Problem:** A panel of judges is treated as independent votes.
- **Method:** Build an error-correlation matrix across 10 judges on items with trusted labels. Compute the effective ensemble size and the eigen-effective rank. Use "regime-matched filters" to pick the voting rule for the error structure.
- **Key results:**
  - Mean pairwise error correlation is **0.21**, so **10 judges ≈ 3.5 independent judges**. Frontier judges from *different providers* are even more correlated.
  - In **up to 28%** of system comparisons, ignoring the shared errors produces a "significant" difference that disappears once they are accounted for.
- **Monday takeaway:** Before you add a 4th or 5th judge, compute n_eff on ~100 trusted items. If n_eff stays flat, spend the money on human labels instead.
- **Code (my illustration of the standard design-effect formula, which reproduces the paper's 10 → 3.5; the paper's exact Eq. 2 was not extracted [formula match inferred]):**
```python
import numpy as np
# err[j, i] = 1 if judge j is wrong on trusted item i
def n_eff(err):
    C = np.corrcoef(err)                      # judge x judge error correlation
    k = C.shape[0]; rho = (C.sum() - k) / (k * (k - 1))
    return k / (1 + (k - 1) * rho)            # 10 judges, rho=0.21 -> 3.46
```
- **Limitations:** Preference-pair tasks. The filters are diagnostics, not general methods.
- **Slide idea:** 10 judge avatars, with correlation lines drawn between them. The avatars merge into 3.5 "independent" silhouettes.

### 5. 2609.30290: Auditing and Repairing LLM-as-Judge Failures in a Production Text-to-SQL Pipeline
- **Submitted:** 2026-09-09. **Authors:** Haowei Liu (Santa Clara University), Hsin-Tai Wu, Yi Fang [HTML]. Code: github.com/JamesL404/synca-audit.
- **Problem:** The production gpt-4o-mini judge had never been checked against humans.
- **Method:**
  1. Two authors annotate 234 questions, oversampled from the judge's flags, plus a 200-question uniform spot-check.
  2. Build a failure taxonomy.
  3. Run a 4-variant prompt sweep.
  4. Try replacement judges.
  5. Use a "disagreement-win" diagnostic to predict whether an ensemble will help.
  6. Route by unanimity across 3 strong judges.
- **Key results:**
  - The production judge's κ = **0.04** on the enriched set and 0.42 on the random set. It over-flagged 77.1% of human-faithful cases. The main cause is "Grade-Hallucination": the judge sees values like 'E' or 'None' in the result preview and penalises SQL for including them.
  - The best prompt fix raises κ only to 0.37.
  - Qwen3.6-27B self-hosted reaches κ = 0.72 vs Claude Opus 4.7 at 0.71, at **~1/300 the cost per call**.
  - Pairing the weak judge with a strong one *degrades* agreement. Three strong judges with unanimity routing reach κ = 0.79 at 89.7% auto-coverage.
  - The audit flagged 25.5% of BIRD-financial gold SQL as candidate gold errors.
- **Monday takeaway:** Measure your production judge's κ on a random sample this week. Swap in a cheap, strong open judge. Do not ensemble a weak judge with a strong one.
- **Limitations:** n = 96 for the head-to-head (underpowered). Two-author gold.
- **Slide idea:** A "κ thermometer" rising 0.04 → 0.37 (prompt fix) → 0.72 (swap judge) → 0.79 (3-judge unanimity). A cost meter drops ÷300.

### 6. 2609.28478: When Evaluators Cry Wolf: Lessons from Production LLM-as-Judge Evaluation in Educational AI
- **Submitted:** v1 2026-08-01 (per arXiv API; v2 2026-09-30). **Authors:** Chris Rohlfs et al.; co-authors from MagicSchool AI [HTML]. The K-12 product serves millions of teachers.
- **Problem:** In a mature product, real failures are rare, so the judges' false positives swamp analyst queues.
- **Method:**
  1. **Unanimous-fail panels:** repeated runs of one judge, with "fail" only if every run fails. The first pass short-circuits the panel. Split cases go to a low-priority "minority report" queue.
  2. Choose the judge model per evaluator.
  3. Soften rubrics with three levers: **U** require unambiguity, **P** require pervasiveness, **C** simplify checklists.
  4. Run two synthetic sets per evaluator: an activation benchmark that counts flags, and a human-reviewed egregious-failure set (12-79 cases) that must still fail [HTML].
- **Key results:** Across 21 evaluators, the median activation rate is 0.04%. Confirmed false-positive flags drop **99%**. Per-flag precision rises from **0.6% to 49%**, and egregious-failure capture stays at **100%**.
- **Monday takeaway:** For monitoring judges, optimise precision under a recall floor. Keep a must-fail canary set and gate every rubric edit on it.
- **Limitations:** One company. The canary sets are small and synthetic.
- **Slide idea:** An alert queue overflowing with 167 flags for each real one. Apply U/P/C and the panel, and the queue drains to about 2 flags per real failure while a "canary set: 100% caught" badge stays green.

### 7. 2610.31657: Cost-Aware Abstention for LLM-Based IT Ticket Classification
- **Submitted:** 2026-10-22. **Author:** Sachin Gupta, independent researcher [HTML].
- **Problem:** A wrong auto-route costs more than human triage. How do you choose a threshold, and are LLM confidences usable for it?
- **Method:** Cost model (c_ok, c_triage, c_wrong) = (0, 1, 5). Pick the threshold on a calibration split, freeze it, and evaluate once on test. Compare 4 trained classifiers with 4 LLMs (zero/few-shot). Report correctness AUROC and risk-coverage area alongside ECE.
- **Key results:**
  - TF-IDF + logistic regression with threshold 0.60 cuts expected cost from 0.763 to **0.472 (-38.1%, 95% CI [35.7, 40.4])**, and wrong routes fall from 15.3% to 3.5%.
  - The best prompted LLM reaches 0.477 accuracy vs **0.879 for fine-tuned DistilBERT**.
  - Isotonic recalibration lowers ECE without improving discrimination. GPT-4o-mini few-shot emits **one confidence value**, so its AUROC is 0.500.
  - At the break-even probability of 0.80, 7 prompted configurations defer every ticket.
- **Monday takeaway:** Write down your cost matrix. Derive the threshold. Select it on calibration data and report it on test. Never trust a low ECE without a correctness AUROC.
- **Code (my sketch of the paper's setup; the closed form is my derivation, which matches its stated 0.80 break-even):**
```python
import numpy as np
c_ok, c_triage, c_wrong = 0.0, 1.0, 5.0
p_star = (c_wrong - c_triage) / (c_wrong - c_ok)      # route iff P(correct) >= 0.80
def expected_cost(conf, correct, t):
    route = conf >= t
    return np.where(route, np.where(correct, c_ok, c_wrong), c_triage).mean()
ts = np.linspace(0, 1, 101)
t_best = ts[np.argmin([expected_cost(conf_cal, y_cal, t) for t in ts])]   # pick on CAL
test_cost = expected_cost(conf_test, y_test, t_best)                       # report once on TEST
```
- **Limitations:** Illustrative costs and one dataset. Not a new algorithm.
- **Slide idea:** A cost curve vs threshold with a sliding marker. Overlay the LLM's single-value confidence as a vertical spike: "nothing to threshold".

### 8. 2608.17994: Judge, Retrieve, or Abstain: Uncertainty-Guarded LLM Judging with Provable Risk Guarantees
- **Submitted:** 2026-08-18. **Authors:** Sher Badshah (Dalhousie U. / NYU Abu Dhabi), Ali Emami (Emory), Hassan Sajjad [HTML].
- **Problem:** A reference-free judge on factual QA can hallucinate verdicts, and nothing controls the error of the verdicts it accepts.
- **Method (a two-threshold cascade):**
  1. The judge produces a verdict and an uncertainty score.
  2. If confident under threshold τ1, accept.
  3. Otherwise, run a retrieval-augmented re-judge with web evidence and accept under threshold τ2.
  4. Otherwise, abstain and send the item to a human.
  5. τ1 and τ2 are calibrated jointly on a held-out labelled set so that the **FDR of accepted verdicts ≤ α** with high probability, using Clopper-Pearson upper bounds. The finite-sample guarantee carries over to the routing.
- **Key result:** Holds the target error rate with "substantially higher coverage than single-mode baselines" on open-domain QA. Exact coverage numbers are not in the abstract [UNVERIFIED].
- **Monday takeaway:** Put an error budget on your judge. Accept only verdicts whose calibrated upper error bound is ≤ α, escalate the rest to retrieval and then to humans.
- **Code (my illustration of the Clopper-Pearson threshold step, using scipy):**
```python
from scipy.stats import beta
def cp_upper(k, n, delta=0.05): return 1.0 if k == n else beta.ppf(1 - delta, k + 1, n - k)
def pick_threshold(conf, wrong, alpha=0.1):
    for t in sorted(set(conf)):                     # lowest t whose accepted-set UCB <= alpha
        m = conf >= t; n = m.sum(); k = wrong[m].sum()
        if n and cp_upper(k, n) <= alpha: return t
```
- **Slide idea:** A three-lane highway (accept / retrieve / human) with cars routed by a confidence gauge. An "FDR ≤ 10%" speed sign appears.

### 9. 2609.17394: Coding Agents Have Converged: Why the SWE-bench Leaderboard Can No Longer Order Its Top Entries, and What to Measure Instead
- **Submitted:** 2026-09-15. **First author:** Fengshuo Liu, Imperial College London (with PolyU, Korea U., Jinan U.) [HTML].
- **Method:** Uses only published per-instance verdicts from 254 submissions. Computes the shared-success partition, solution-set nesting, scaffold ranges, exact paired **McNemar** tests between adjacent entries with Holm correction, and an instance budget for resolution.
- **Key results:**
  - The top 2 entries each resolve 396 of 500 instances. The top 10 share 285 successes and 51 failures, so only 164 instances discriminate between them.
  - Within-model scaffold ranges reach **29.8 pp**, vs an 8.8-pt spread across the top 30.
  - McNemar separates **0 of 29** adjacent Verified pairs. The larger Test split separates 14 of 23.
- **Monday takeaway:** When you compare two agent versions, use a paired McNemar on per-item outcomes, not two accuracies. Report the model *and* the scaffold.
- **Code (statsmodels API, standard):**
```python
from statsmodels.stats.contingency_tables import mcnemar
# b = items A solved & B failed, c = B solved & A failed
print(mcnemar([[n_both, b], [c, n_neither]], exact=True).pvalue)
```
- **Slide idea:** A 500-cell grid where solved-by-all cells fade to grey and only 164 coloured cells remain. "This is your real benchmark."

### 10. 2609.28177: How Sensitive Are LLM Leaderboard Claims to Hidden Model Selection?
- **Submitted:** 2026-09-25 (v2). **Authors:** Chen Yang (Texas A&M Statistics), Jun Chen (Mayo Clinic) [HTML].
- **Method:** Uses a Gaussian margin model to compute how many privately tested variants a published margin can survive, given a lower bound on within-family correlation. Includes an item-level audit of adjacent-rank claims.
- **Key results:** On the Open LLM Leaderboard, **391 of 394 adjacent-rank claims lack statistical support**, before any selection correction. The right correlation depends on the score: 0.90 pooled item, 0.46 composite under item resampling, 0.92 under subject resampling.
- **Monday takeaway:** If you tried 20 checkpoints and report the best one, your margin must cover a best-of-20 selection effect. Log every variant you evaluated.
- **Slide idea:** A ranking table where 391 of 394 "↑" arrows turn grey.

### 11. 2610.00651: Agent Evaluation Reliability: More Tasks Won't (Always) Fix An Agent Leaderboard
- **Submitted:** 2026-09-30. **Authors:** Michael Hardy, Ruhana Azam, Anka Reuel, Mykel Kochenderfer, Sanmi Koyejo (Stanford; UIUC) [HTML].
- **Method:** A Bayesian generalizability-theory variance decomposition (model × scaffold × task) for sparse binary agent leaderboards. Applied to 22 benchmarks from HAL and Harbor Index.
- **Key results:**
  - Fixed model+scaffold systems are ranked reliably (0.935-0.994). Underlying *models* are not (0.148-0.841).
  - Infinitely many more similar tasks add at most **+0.097** reliability when scaffold coverage dominates the uncertainty.
  - Pooling diverse benchmarks lifts reliability from 0.44 to 0.75 at the same budget, at up to **83%** lower cost.
- **Monday takeaway:** Decide what your claim is ("this system" vs "this model"). If it is about the model, spend budget on more scaffolds, not more tasks.
- **Slide idea:** A variance pie (model / scaffold / task / noise). Clicking "add 1000 tasks" barely shrinks the scaffold slice.

### 12. 2609.34198: Frozen Judges, Moving Agents: Version-Dependent LLM-Judge Error and the Limits of Judge-Assisted Agent Evaluation
- **Submitted:** 2026-09-28. **First author:** Jiapeng Li. Org [UNVERIFIED; HTML 404].
- **Method:** Tests 20 version pairs on 250 SWE-bench Verified issues, plus τ-bench and 1,106 AgentRewardBench trajectories, for whether judge error is invariant across agent versions. Compares judge-only intervals with execution-based ones.
- **Key results:**
  - 8 judge-only intervals declare upgrades that execution-based intervals cannot establish, despite rank correlations of 0.71-0.79.
  - False acceptance of failed patches **rises with agent capability**.
  - Reusing the old version's calibration raises comparison error from **3.8 to 19.5 points**.
- **Monday takeaway:** Re-validate the judge on the *new* agent's outputs for every release. A calibration from v1 does not transfer to v2.
- **Slide idea:** A frozen judge (ice block) while agent versions v1→v4 run past. The red "false accept" bar grows with each version.

### 13. 2609.31857: LLM Judge Validation Under Sparse Overlap: From Inference to Design
- **Submitted:** 2026-09-25 (v1, per arXiv API). **Authors:** Junxuan Li, Arko Mukherjee, Soumyabrata Pal (Adobe / Adobe Research) [HTML].
- **Key results:** At 5% pairwise human-judge overlap, the wrong-decision rate reaches 25%, and the chance of picking the wrong best judge out of 10 is 65%. An overlap of **ρ ≥ 0.25** suffices for non-borderline judges. A zero-cost stratified allocation halves false rejections vs random sampling when the strata are informative.
- **Monday takeaway:** Plan your human-label budget so that at least 25% of items are scored by both a human and the judge. Stratify that sample.
- **Slide idea:** An overlap slider from 5% to 25%. A "wrong judge chosen" gauge falls from 65%.

### 14. 2608.05086: Item Response Theory for AI Safety
- **Submitted:** 2026-08-05. **Authors:** Joshua Fonseca Rivera, Neil Shah, David Demitri Africa, Konstantinos Voudouris. The HTML lists "Independent" and "UK AI Security Institute"; author-to-org mapping [UNVERIFIED].
- **Method:** Fits 2PL/multidimensional IRT over 8 safety benchmarks × 192 models. Selects items adaptively. Uses person-fit, ability-shift and fingerprint tests for audits.
- **Key results:**
  - 3 factors (refusal strictness, truthfulness, contextual harm) explain most of the variance.
  - About **10 adaptively chosen items** recover several benchmarks, cutting eval cost by **97-99%**.
  - The combined tests detect **94-97%** of sandbagging runs [HTML]. Fingerprints catch silent model swaps behind an API.
- **Monday takeaway:** Fit IRT on your eval history. Run a 10-30-item "tiny eval" on every commit and the full set nightly. Use fingerprints to detect a vendor model swap.
- **Slide idea:** An item characteristic curve morphs, and then 1,000 items collapse to 10 glowing ones.

### 15. 2608.24419: A Judge Should Know What Changed: Construct Validity for LLM-as-a-Judge Evaluation
- **Submitted:** 2026-08-25. **Authors:** Jianlin Chen (South China U. of Technology) et al., with the University of Macau [HTML].
- **Method:** Defines a 2-D profile: invariance S (the verdict stays the same under construct-preserving edits) and sensitivity R (the verdict changes under minimal construct-changing edits). Tests 7 judges × 4 domains with 7 intervention types and 5 register-only controls.
- **Key results:** At S ≥ 0.90, judges average S = 0.945 but **R = 0.319**. Surface-only predictors reproduce 55-67% of public labels, including **67.4% of MT-Bench human votes**.
- **Monday takeaway:** Add "must-flip" counterfactual items to your judge test suite (break the answer slightly, and the verdict must change). Do not stop at robustness tests.
- **Slide idea:** A 2×2 quadrant (robust/insensitive vs robust/sensitive). The judges' dots cluster in the "robust but blind" corner.

### 16. 2610.13303: Agreement Without Alignment: Label-Free Rubric Clarification Increases LLM-Judge Consensus but Not Agreement with Humans
- **Submitted:** 2026-10-09. **Authors:** Sangdo Han, Moonsoo Kim (CEO Business School) [HTML]. Preregistered, with 129,770 judge requests.
- **Key results:** On SummEval, rewriting the most-contested rubric clauses raises inter-judge Krippendorff's α by +0.069 (95% CI 0.046-0.092). Agreement with experts does not change (Kendall τ diff -0.007, CI -0.037 to 0.021).
- **Monday takeaway:** Judge-vs-judge agreement is not a proxy for validity. Never tune rubrics without human labels.
- **Slide idea:** Two gauges: "judges agree" rising while "humans agree" stays flat.

### 17. 2610.05094: How Much Do LLM-as-a-Judge Design Choices Matter? A Systematic Comparison of Prompt Designs, Rating Scales, and Models
- **Submitted:** 2026-10-04. **Authors:** Laurène Vaugrante, Thilo Hagendorff (AI Safety Research Group, U. Stuttgart) [HTML].
- **Key results:**
  - 10 reasoning models. Rating mean absolute deviation is 0.11 on a 1-7 scale, and binary accuracy is 96.5%.
  - The rating scale alone shifts measured bias by up to 0.93 points.
  - Leniency drops 28.9 pp with detailed prompts and up to 56.1 pp when switching models.
  - Lower reasoning effort changes neither accuracy nor leniency. **Model identity is the dominant source of variance.**
- **Monday takeaway:** Version the judge model, scale and prompt as part of the metric definition. Changing any of them is a breaking change. Use low reasoning effort to save cost.
- **Slide idea:** Three dials (prompt, scale, model). Turning the model dial swings the leniency needle the most.

### 18. 2608.07914: When Is Benchmark Contamination Detectable? Information Limits and Power-Calibrated Audits
- **Submitted:** 2026-08-08. **Authors:** Ibne Farabi Shihab, Sanjeda Akter, Anuj Sharma (Iowa State) [HTML].
- **Method:** Models contamination as the mixture (1-α)P0 + αP1. Detectability scales with **α·ρ·√m** (fraction seen × behavioural separability × items). Estimates detector efficacy from matched clean and seen controls before the audit, and uses a two-stage planner that abstains when power is too low.
- **Key results:** Calibration efficacy predicts held-out power (R² 0.83-0.98). The naive Gaussian budget fails in 9 of 9 channels. Signal ordering is verbatim > paraphrase > surface.
- **Monday takeaway:** "Our contamination check found nothing" means nothing unless you report the check's power. Plant known-seen controls and verify that the detector fires on them.
- **Slide idea:** A dial with three knobs (α, ρ, m) controlling a "detectable?" light.

### 19. 2610.05830: Measurement-First Auditing of Agentic Leaderboards: Contamination Susceptibility, Matched-Control Re-evaluation, and Scorer Validation
- **Submitted:** 2026-10-05. **First author:** Dishu Yang (Northeastern), with GWU [HTML].
- **Method:** Three contamination channels: training-time exposure, eval-time retrieval, and pipeline/scaffold leakage. Each is coded open / partial / closed / unknown, fail-closed. Adds a matched-control re-evaluation and a scorer-validation gate.
- **Key results:** Across 9 HAL configurations, **0 of 27** channel assessments were coded "closed", with incidents confirmed in 4. A +10.0-pt SWE-bench file-localisation gap had a 95% CI that included 0. The reproduction scorer failed its own validation gate.
- **Monday takeaway:** For agents, check eval-time leakage (web search finding the benchmark repo, solution files in the container), not only training data.
- **Slide idea:** Three pipes (training, retrieval, scaffold) with leak drips. Every valve is labelled "unknown".

### 20. 2609.26489: Calibration as a First-Class Criterion in LLM Evaluation
- **Submitted:** 2026-09-22. **Authors:** Mario Sanz-Guerrero, Katharina von der Wense (JGU Mainz; CU Boulder) [HTML].
- **Point:** A position paper. Most benchmarks already provide (confidence, correctness) pairs, so a calibration score can be reported now. Judges, synthetic-data filters and active learning all depend on calibrated confidence that nobody checks.
- **Monday takeaway:** Add ECE plus a reliability diagram next to accuracy on every eval dashboard. Pair it with AUROC (see #7).

### Honourable mentions (verified from the abstracts)
- **2609.24516: LLJ Cards** (Chehbouni, McGill/Mila; 2026-09-21). A reporting card for LLM-judge evaluations based on measurement theory. Use it as the template for the deck's "judge card" slide.
- **2610.04430: MERCI Cards** (Komarla; 2026-10-03). An eval/deployment card framework built on weighted multi-objective optimisation, applied to criminal-justice LLM systems.
- **2608.24807: Automatic Model Card Generation Using an LLM** (Toma; 2026-08-25). MCTidy/MCGenie on 48 HF cards: semantic similarity ~0.9, over half fully correct. Quality depends on whether a paper is available.
- **2608.15980: Whose Gold?** (Jha; 2026-08-17). Expert and crowd pools disagree on 23.6% of unanimous MultiPref items, yet the 6-model leaderboard is unchanged (τ = 1.00). A 10-model board would be displaced with p = 0.86. An LLM judge tracks the crowd pool, not the experts.
- **2609.09245: What Fixed-Rollout pass@k Evaluations Can Identify** (Singh, IIT Ropar; 2026-09-08). pass@k for k > n is not identified. With n = 16, failure at k = 1000 is ambiguous by 1.5× to over 2,600×.
- **2610.07405: What pass@k Cannot Measure** (Rath et al., Accenture/Vizuara; 2026-10-05). GRPO and RFT move diversity in opposite directions while pass@8/32 show no winner. No arm beats the base checkpoint on hard-problem coverage. Lesson: always include the base-model control.
- **2609.38914: Risk-Aware Adaptive Evaluation** (Maji, Georgia Tech; 2026-09-30). Thompson sampling weighted by impact on τ-bench airline: 50 trials find 86% of impact-weighted failures, vs 25% for uniform.
- **2608.18296: FairGlucose** (Luo; 2026-08-18). Aggregate OOD ratio ~1.0 hides subgroup ratios of 0.8-1.4. T1D error is 6 mg/dL higher than T2D across all 33 models. A clean slice-metrics example.
- **2609.34521: Population-level decision curve analysis may mislead** (Wang; 2026-09-28). Net benefit mixes subgroup utility scales. When subgroup ΔNB has opposite signs, run decision curve analysis per subgroup.
- **2609.10357: A Later Test Set Is Not a New Domain** (Naser Moghadasi; 2026-09-09). A temporal hold-out removes window memorisation but not domain familiarity: the largest gain (28% lower MASE) comes on Wikipedia pageviews, which dominate the TimesFM corpus.
- **2609.32211: Rank Confidence Sequences** (Khosravi, Huo; 2026-09-26) and **2610.10597: Certified Corruption Budgets** (Khosravi; 2026-10-06). Anytime-valid rank CIs let you peek at a leaderboard after every item. In replays on 1.8M Arena votes, a few hundred rigged votes make standard CIs certify false orderings.
- **2610.21128: When Judges Agree and Are Wrong** (Zhang; 2026-10-15). 60% of wrong answers sit in the high-consistency region (≥ 0.8), and 77.7% of those collapse to an identical wrong answer.
- **2609.11987: Harness or Model?** (Arjmandi; 2026-09-08). On a private, contamination-controlled suite, the native vs neutral harness shows no average difference (Opus 4.8: -1.25 pp, CI [-10.0, +7.5]). 22 of 81 runs cancelled at the wall-clock ceiling had already produced a passing patch.

---

## Cross-paper trends (Jul-Oct 2026)
1. **The noise floor is the story.** Pinned judges flip 5% of verdicts overall and 21-40% of close calls (#2, #3). Adjacent leaderboard ranks are mostly unresolvable: 0/29 SWE-bench pairs (#9) and 391/394 Open-LLM claims (#10). The new norm is paired tests, re-runs, and rank *bands* instead of point ranks.
2. **Judges are measurement instruments that need validation, not oracles.** Panels are correlated (10 ≈ 3.5, #4). Inter-judge consensus ≠ human agreement (#16, honourable mention 2610.21128). Construct sensitivity is low (R = 0.32, #15). Judge error drifts with agent version (#12). The fix is a random human-labelled anchor plus PPI (#1) and adequate overlap (#13).
3. **Thresholds and abstention get guarantees.** Clopper-Pearson FDR control (#8), cost-matrix thresholds frozen on a calibration split (#7) and anytime-valid sequences (2609.32211) all turn "is it good?" into "what error rate do we accept, at what cost?".
4. **Production papers optimise precision, not accuracy.** MagicSchool (#6) and the text-to-SQL audit (#5) both found false positives dominating. Both fixed it with unanimity panels and judge swaps, and both found that cheap open judges match frontier judges at a fraction of the cost.
5. **Reporting standards are converging into "cards".** LLJ Cards, MERCI Cards, automatic model cards, SafeLLM4SE (2609.37294, a statistical reporting standard on PyPI), and the Pinned paper's minimal protocol (re-runs + 2 judge families + adjacency intervals). The common fields: judge model/version, rubric hash, re-run flip rate, human-overlap κ, CI method, contamination channels.

## Gotchas list for a slide
- Temperature 0 is not deterministic on hosted endpoints (#2, #3).
- Bootstrap CIs at N<100 under-cover (#1). Use Wilson.
- Judge κ measured only on flagged items is a biased estimate (#5 reports both an enriched set and a random set). PPI needs a *random* label sample (#1).
- A weak judge plus a strong judge can be worse than the strong judge alone (#5).
- One constant LLM confidence value gives ECE without discrimination (AUROC 0.5) (#7).
- "No contamination found" without a power estimate means nothing (#18).
- A temporal hold-out ≠ a new domain (2609.10357).
- The best of N private variants needs a selection correction (#10).

## Suggested 8-slide block (animations)
1. "The noise floor": the flip grid from #2/#3.
2. "Your bootstrap lies": coverage bars from #1, then the evalstats code.
3. "10 judges = 3.5": merging avatars from #4, with the n_eff code.
4. "Audit your judge on Monday": the κ thermometer from #5.
5. "Cry wolf": the alert queue drains, from #6.
6. "Threshold from a cost matrix": the sliding cost curve from #7, then the 3-lane router from #8.
7. "Leaderboards can't order the top": 164 coloured cells and McNemar, from #9/#10/#11.
8. "Judge card": the LLJ-card fields fill in one by one (trend 5).

## Sources
All at https://arxiv.org/abs/<id>: 2609.35815, 2609.33044, 2610.30512, 2609.22512, 2609.30290, 2609.28478, 2610.31657, 2608.17994, 2609.17394, 2609.28177, 2610.00651, 2609.34198, 2609.31857, 2608.05086, 2608.24419, 2610.13303, 2610.05094, 2608.07914, 2610.05830, 2609.26489, 2609.24516, 2610.04430, 2608.24807, 2608.15980, 2609.09245, 2610.07405, 2609.38914, 2608.18296, 2609.34521, 2609.10357, 2609.32211, 2610.10597, 2610.21128, 2609.11987, 2609.37294.
evalstats: https://raw.githubusercontent.com/ianarawjo/evalstats/main/README.md ; https://pypi.org/pypi/evalstats/json (0.3.3).
