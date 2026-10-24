# 07 - AI Eval Design: from golden sets to quality cards (state of play, Oct 2026)

Research date: 2026-10-23. Versions were checked on PyPI/GitHub where noted. Items marked [UNVERIFIED] could not be confirmed against a primary source in this session (the web-search budget ran out partway through, so later checks used WebFetch on known URLs only).

---

## 1. Core thesis: evals are experiments, and the eval set is a dataset product

- "Fundamentally, evaluations are experiments" - Evan Miller, *Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations*, arXiv:2411.00640 (Nov 2024, Anthropic). https://arxiv.org/abs/2411.00640
- "Error analysis is **the most important activity in evals**." - Hamel Husain & Shreya Shankar, *AI Evals: Everything You Need to Know*, hamel.dev, published 2026-09-18. https://hamel.dev/blog/posts/evals-faq/
- "Write evaluators for errors you discover, not errors you imagine." - same source.
- "documentation must be treated as a user-centric product in and of itself" - Pushkarna, Zaldivar, Kjartansson, *Data Cards: Purposeful and Transparent Dataset Documentation for Responsible AI*, arXiv:2204.01075 (FAccT 2022). https://arxiv.org/abs/2204.01075

**Data-centric framing for the deck:** an eval set goes through the same lifecycle as a training set, and it needs more care because it decides what ships.

```
DESIGN -> GENERATE -> SELECT -> CURATE -> LABEL -> DENOISE -> QUALITY CARD
  |          |          |         |         |        |           |
 task spec  prod traces dedup /  slices,  human +   label-noise  datasheet / data card
 + failure  + synthetic  decontam  coverage  judge    audit,      + model card + eval
 taxonomy   edge cases   vs train  quotas   rubric   adjudicate  report with CIs
                                                         ^
            error analysis on failing traces -------------+  (loop: new failure modes -> new slices)
```

---

## 2. Eval-driven development (EDD): the loop

Practitioner consensus in 2025-2026 (Husain/Shankar, Anthropic, OpenAI and Google docs) follows these steps:

1. **Look at the data first.** Read real traces. Husain/Shankar: "We recommend reviewing at least 100 traces. Continue past 100 while you are still learning." They also say to annotate at least 30 traces yourself before trusting an agent's suggestions.
2. **Open coding, then axial coding.** Write free-text notes per failing trace, then cluster them into a **failure taxonomy**. Each failure mode becomes a slice.
3. **Binary pass/fail per failure mode.** "Binary evaluations force clearer thinking and more consistent labeling." "Start with binary labels... Numeric labels are advanced and usually not necessary." (hamel.dev)
4. **Benevolent dictator.** One domain expert owns the quality definition: "Start with a benevolent dictator whenever feasible."
5. **Automate cheaply first.** Use code assertions (regex, JSON schema, exact match), then LLM judges only for subjective criteria.
6. **Align the judge to the humans.** Measure judge TPR/TNR against expert labels on a held-out labeled split.
7. **Put it in CI as a regression gate.** Every prompt, model or retriever change re-runs the golden set. Ship only if no slice regresses beyond its CI.
8. **Watch for criteria drift.** "users need criteria to grade outputs, but grading outputs helps users define criteria." - Shankar et al., *Who Validates the Validators? Aligning LLM-Assisted Evaluation of LLM Outputs with Human Preferences*, arXiv:2404.12272 (UIST 2024 per the authors [venue UNVERIFIED on the arXiv page]). https://arxiv.org/abs/2404.12272

Caveat for the slide: asked whether to write evals before the code, the FAQ answers "Generally no." Their EDD is error-analysis-first, not TDD-first.

---

## 3. Golden sets: design rules

| Property | Rule of thumb | Why |
|---|---|---|
| Source mix | Real production traces + targeted synthetic edge cases | Real traces give the actual distribution. Synthetic cases cover rare, high-cost tails. |
| Size | 100-500 to start. Size each slice for the effect you need to detect (see section 5). | SE ~ sqrt(p(1-p)/n). At n=400 and p=0.8, the 95% CI is about +/-3.9 pts. |
| Slices | Intent, language, user tier, doc type, length bucket, failure mode, safety category | Aggregate accuracy hides slice regressions (Simpson's paradox). |
| Decontamination | n-gram / embedding dedup against training and SFT data. Keep a private holdout. | Public benchmark leakage inflates scores. |
| Versioning | Immutable versions (`golden_v3.2`), changelog, owner | A score is meaningless without the set version. |
| Splits | dev (iterate) / test (report) / judge-calibration (labeled by experts) | Prevents overfitting prompts to the test set. |
| Refresh | Add new failure modes monthly. Retire saturated items. | Saturation and drift. |

Synthetic generation for evals: use a "dimensions x values" grid (persona x intent x difficulty x language), sample tuples, then have an LLM write the query and a human validate it. This approach is recommended in the hamel.dev FAQ. Synthetic items must still be human-checked before they count as gold.

---

## 4. Slice metrics

Always report the metric per slice with n and a CI, never only the global number.

```python
# Slice table with Wilson intervals (statsmodels)
import pandas as pd
from statsmodels.stats.proportion import proportion_confint

df = pd.read_json("eval_results.jsonl", lines=True)   # cols: slice, passed (0/1)
g = df.groupby("slice")["passed"].agg(["sum", "count"])
g["acc"] = g["sum"] / g["count"]
lo, hi = proportion_confint(g["sum"], g["count"], alpha=0.05, method="wilson")
g["ci_low"], g["ci_high"] = lo, hi
print(g.sort_values("acc"))
```
Source: statsmodels `proportion_confint` API (https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.proportion_confint.html).

Use Wilson rather than the normal approximation for small n or p near 0 or 1.

---

## 5. Confidence intervals, bootstrap and paired comparisons

Key points from Miller (arXiv:2411.00640). The abstract promises formulas for "measuring differences between two models" and recommendations that minimize "statistical noise"; the bullet details below follow the paper body, which the fetch did not reach [UNVERIFIED wording]:
- Report a **standard error of the mean** (CLT) with every eval score.
- When questions come in groups (several questions per passage), use **clustered standard errors**. Naive SEs can be badly too small.
- When comparing two models on the same items, use **paired differences**. This removes item-difficulty variance and gives much tighter CIs.
- Reduce within-item variance by resampling each answer k times, or by scoring from token probabilities instead of a single sample.
- Do a **power analysis** before building the set: how many items do you need to detect a 2-point delta?

```python
# Paired bootstrap: is model B really better than A on the same golden set?
import numpy as np
rng = np.random.default_rng(0)
a = np.load("scores_A.npy")   # per-item 0/1 or float, same item order
b = np.load("scores_B.npy")
d = b - a
boots = np.array([rng.choice(d, size=len(d), replace=True).mean()
                  for _ in range(10_000)])
lo, hi = np.percentile(boots, [2.5, 97.5])
print(f"delta={d.mean():+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}]  "
      f"P(delta<=0)={np.mean(boots<=0):.3f}")
```
SciPy equivalent: `scipy.stats.bootstrap((d,), np.mean, confidence_level=0.95, method="BCa")` (https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html). For clustered data, resample clusters (passages or conversations), not individual items.

Power intuition: the minimum detectable effect at alpha=0.05 and power 0.8 is about 2.8 x SE(delta). For an unpaired test with p=0.8 and n=500 per arm, SE(delta) is about 0.025, so you can only detect a delta of about 7 points. Pairing typically shrinks this a lot.

---

## 6. Calibration and ECE

- Guo, Pleiss, Sun, Weinberger, *On Calibration of Modern Neural Networks*, ICML 2017, arXiv:1706.04599. "We discover that modern neural networks, unlike those from a decade ago, are poorly calibrated." Temperature scaling, a single-parameter variant of Platt scaling, "is surprisingly effective". https://arxiv.org/abs/1706.04599
- **ECE** = sum over bins b of (|B_b| / n) x |acc(B_b) - conf(B_b)|, typically with M=10 or 15 equal-width bins. It depends on the binning, so also report Brier score / log loss and a reliability diagram.
- LLM relevance: (a) classifier heads and safety filters, (b) verbalized or token-prob confidence for abstention ("I don't know"), (c) **judge confidence**, where a calibrated judge lets you route low-confidence items to humans.

```python
import numpy as np
from sklearn.calibration import calibration_curve

def ece(y_true, p, n_bins=15):
    bins = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(p, bins) - 1, 0, n_bins - 1)
    e = 0.0
    for b in range(n_bins):
        m = idx == b
        if m.any():
            e += m.mean() * abs(y_true[m].mean() - p[m].mean())
    return e

frac_pos, mean_pred = calibration_curve(y_true, p, n_bins=10)  # reliability diagram
```
Source: scikit-learn `sklearn.calibration.calibration_curve` (https://scikit-learn.org/stable/modules/generated/sklearn.calibration.calibration_curve.html). The fix is `CalibratedClassifierCV(method="sigmoid"|"isotonic")` or temperature scaling on a held-out split.

---

## 7. Cost-sensitive thresholds: cost matrix, expected cost, ROC operating point

A score is not a decision. A guardrail, router or fraud flag needs a threshold chosen with the **costs** of each error type.

- Cost matrix C: C_FP = cost of a false alarm (blocking a good user, escalating to a human), C_FN = cost of a miss (leaked PII, harmful output shipped).
- With **calibrated** probabilities, the Bayes-optimal rule is to flag when p > t* = C_FP / (C_FP + C_FN). Example: a miss costs 20x a false alarm, so t* = 1/21 ≈ 0.048.
- Expected cost at threshold t: EC(t) = pi x FNR(t) x C_FN + (1 - pi) x FPR(t) x C_FP, where pi is the prevalence in **production** (not in the eval set).
- On the ROC curve, the optimal point is where the curve touches an iso-cost line of slope (C_FP x (1 - pi)) / (C_FN x pi).

```python
import numpy as np
from sklearn.metrics import roc_curve
fpr, tpr, thr = roc_curve(y_true, scores)
pi, C_fp, C_fn = 0.02, 1.0, 20.0              # prod prevalence, costs
ec = pi*(1-tpr)*C_fn + (1-pi)*fpr*C_fp
best = np.argmin(ec)
print(f"threshold={thr[best]:.3f} TPR={tpr[best]:.2f} FPR={fpr[best]:.3f} EC={ec[best]:.4f}")
```
Pitfall: golden sets are often enriched with positives. Re-weight to production prevalence before picking t, or EC is wrong. Show the threshold per slice too, because one global t can be unfair across slices.

---

## 8. LLM-as-judge: pitfalls, mitigations and agreement

**Foundational paper:** Zheng et al., *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*, NeurIPS 2023 Datasets & Benchmarks, arXiv:2306.05685. GPT-4 as judge reaches "over 80% agreement, the same level of agreement between humans." The paper identifies **position bias, verbosity bias, self-enhancement bias, limited reasoning ability**. https://arxiv.org/abs/2306.05685

Related primary work, cited from memory with titles and IDs [arXiv pages not re-fetched this session]:
- Wang et al., *Large Language Models are not Fair Evaluators*, arXiv:2305.17926 (2023). Shows position bias; mitigation is to swap the order and average ("balanced position calibration").
- Liu et al., *G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment*, arXiv:2303.16634 (2023). Chain-of-thought rubric plus probability-weighted scores. This is the basis of DeepEval's `GEval`.
- Dubois et al., *Length-Controlled AlpacaEval: A Simple Way to Debias Automatic Evaluators*, arXiv:2404.04475 (2024). Regression-based length debiasing.

**Pitfall to mitigation checklist**

| Pitfall | Mitigation |
|---|---|
| Position bias (pairwise) | Judge both orders; count a win only if it holds in both, otherwise tie |
| Verbosity / length bias | Length-controlled scoring; rubric says "do not reward length" |
| Self-preference | Judge from a different model family than the candidate |
| Vague Likert scales | Binary pass/fail per criterion; one judge per failure mode |
| Rubric drift and prompt overfitting | Freeze the judge prompt and version it like code |
| Judge never validated | Expert-labeled calibration split; report TPR, TNR and kappa |
| Leaking the reference | Reference-guided grading only where a reference exists; otherwise a rubric |

**Agreement metrics:** raw % agreement inflates with class imbalance, so report **Cohen's kappa** (2 raters), **Krippendorff's alpha** (many raters, missing data), and judge **TPR/TNR** against the human label.

```python
from sklearn.metrics import cohen_kappa_score, confusion_matrix
k = cohen_kappa_score(human, judge)
tn, fp, fn, tp = confusion_matrix(human, judge, labels=[0, 1]).ravel()
tpr, tnr = tp/(tp+fn), tn/(tn+fp)
print(f"kappa={k:.2f}  TPR={tpr:.2f}  TNR={tnr:.2f}")
```

**Bias-correcting the judge's pass rate:** given judge TPR/TNR from the calibration split, the corrected true pass rate is theta = (p_obs + TNR - 1) / (TPR + TNR - 1) (Rogan-Gladen estimator). Bootstrap the CI over both the calibration and the eval items. The hamel.dev FAQ describes this correction workflow.

---

## 9. Pairwise comparison, Elo and Bradley-Terry

- Chiang et al., *Chatbot Arena: An Open Platform for Evaluating LLMs by Human Preference*, arXiv:2403.04132 (Mar 2024; ICML 2024 [venue UNVERIFIED on arXiv page]). The abstract reports "over 240K votes" at writing. https://arxiv.org/abs/2403.04132 . The leaderboard (now LMArena, lmarena.ai) moved from online Elo to **Bradley-Terry MLE with bootstrap CIs**. Online Elo depends on match order, while BT is order-independent [method detail per LMSYS blog, UNVERIFIED this session].
- BT model: P(i beats j) = sigmoid(beta_i - beta_j), shown on an Elo-like scale of 400 x log10 odds + 1000.
- Known critiques for the "open challenges" slide: style and length effects (Arena added "style control"), and vote gaming and private testing (*The Leaderboard Illusion*, Singh et al., arXiv:2504.20879, 2025 [UNVERIFIED this session]).

```python
# Bradley-Terry via logistic regression on pairwise battles
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
b = pd.read_json("battles.jsonl", lines=True)      # model_a, model_b, winner in {a,b}
models = sorted(set(b.model_a) | set(b.model_b)); ix = {m:i for i,m in enumerate(models)}
X = np.zeros((len(b), len(models)))
X[np.arange(len(b)), b.model_a.map(ix)] = 1
X[np.arange(len(b)), b.model_b.map(ix)] = -1
y = (b.winner == "a").astype(int)
lr = LogisticRegression(fit_intercept=False, C=1e6).fit(X, y)
elo = 400 * lr.coef_[0] / np.log(10) + 1000
print(pd.Series(elo, index=models).sort_values(ascending=False))
```
This mirrors the approach in the LMSYS Arena analysis notebook [adapted, UNVERIFIED exact source cell]. To get CIs, bootstrap the battles 1,000 times and refit.

Enterprise variant: pairwise "SxS" (side-by-side) on your own golden set. Google Vertex has **AutoSxS** (a "Run AutoSxS pipeline" doc page exists in the Gen AI evaluation docs).

---

## 10. Eval frameworks: verified facts and snippets

### 10.1 EleutherAI lm-evaluation-harness - `lm-eval` **0.4.13** (PyPI, uploaded 2026-08-31)
Repo: https://github.com/EleutherAI/lm-evaluation-harness . It is the backend of the HF Open LLM Leaderboard (v1/v2). The CLI was refactored (2025/12) into subcommands `run`, `ls`, `validate` with `--config` YAML. The legacy `lm_eval --model ...` form still appears in the README.
```bash
pip install "lm_eval[hf]"
lm_eval --model hf --model_args pretrained=EleutherAI/gpt-j-6B \
        --tasks hellaswag --device cuda:0 --batch_size 8
lm-eval ls tasks
```
```python
import lm_eval
from lm_eval.models.huggingface import HFLM
lm = HFLM(pretrained="gpt2", batch_size=16)
results = lm_eval.simple_evaluate(model=lm, tasks=["hellaswag"], num_fewshot=0)
```
Source: docs/python-api.md in the repo.

### 10.2 Inspect AI (UK AI Security Institute) - `inspect-ai` **0.3.283** (latest on PyPI at fetch time)
Docs: https://inspect.aisi.org.uk/ . It provides Task = dataset + solver + scorer, supports agents and sandboxes, and includes the `inspect view` log viewer. It is widely used by AISI and other safety institutes for frontier evals.
```python
from inspect_ai import Task, task
from inspect_ai.dataset import FieldSpec, hf_dataset
from inspect_ai.scorer import model_graded_qa
from inspect_ai.solver import generate

@task
def simpleqa():
    return Task(
        dataset=hf_dataset("codelion/SimpleQA-Verified", split="train",
                           sample_fields=FieldSpec(input="problem", target="answer")),
        solver=generate(),
        scorer=model_graded_qa(),
    )
```
```bash
inspect eval simpleqa.py --model openai/gpt-5
inspect view
```

### 10.3 Stanford HELM - `crfm-helm` (repo shows v0.5.4)
Repo: https://github.com/stanford-crfm/helm . Paper: Liang et al., *Holistic Evaluation of Language Models*, arXiv:2211.09110 (TMLR 2023). It measures many metrics (accuracy, calibration, robustness, fairness, efficiency...) across many scenarios. Leaderboards include HELM Capabilities, HELM Safety, VHELM, MedHELM and audio. **The README notes that HELM entered maintenance mode on June 1, 2026.**
```bash
pip install crfm-helm
helm-run --run-entries mmlu:subject=philosophy,model=openai/gpt2 --suite my-suite --max-eval-instances 10
helm-summarize --suite my-suite
helm-server --suite my-suite      # http://localhost:8000/
```

### 10.4 OpenAI Evals
Repo: https://github.com/openai/evals (`pip install evals`). The README says: "You can now configure and run Evals directly in the OpenAI Dashboard." The repo is "currently not accepting evals with custom code", though YAML model-graded evals are still accepted. Registry: `evals/registry/evals/*.yaml` with Git-LFS data under `evals/registry/data`. OpenAI also exposes a hosted Evals API (`client.evals.create`, graders) [API shape UNVERIFIED this session].

### 10.5 promptfoo (CLI, YAML, red-teaming)
Docs: https://www.promptfoo.dev/docs/getting-started/ . The page's copyright reads "Promptfoo, Inc. (2026)". Reports in 2026 of an acquisition by OpenAI are [UNVERIFIED; not on the docs page].
```bash
npx promptfoo@latest init --example getting-started
npx promptfoo@latest eval
npx promptfoo@latest view
```
```yaml
prompts:
  - 'Convert the following English text to {{language}}: {{input}}'
providers: [openai:gpt-6-sol]      # as printed in current docs
defaultTest:
  assert:
    - type: llm-rubric
      value: Do not mention that you are an AI or chat assistant
tests:
  - vars: {language: French, input: Hello world}
    assert: [{type: contains, value: 'Bonjour le monde'}]
```

### 10.6 DeepEval (Confident AI) - `deepeval` **4.3.1** (PyPI)
Docs: https://deepeval.com/docs/getting-started . It is pytest-style. Note: current docs use `SingleTurnParams`, while older tutorials use `LLMTestCaseParams`.
```python
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, SingleTurnParams
from deepeval.metrics import GEval

def test_correctness():
    metric = GEval(
        name="Correctness",
        criteria="Determine if the 'actual output' is correct based on the 'expected output'.",
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT, SingleTurnParams.EXPECTED_OUTPUT],
        threshold=0.5)
    tc = LLMTestCase(input="I have a persistent cough and fever. Should I be worried?",
                     actual_output="...", expected_output="...")
    assert_test(tc, [metric])
```
```bash
deepeval test run test_example.py
```

### 10.7 Google Vertex AI / Gemini Enterprise Agent Platform - Gen AI evaluation service
Docs now live under docs.cloud.google.com/gemini-enterprise-agent-platform/ (the old cloud.google.com/vertex-ai/... URLs 301-redirect there). Two SDK tracks exist: the **GenAI Client** (`vertexai.Client`, `client.evals.*`), which is the current recommended path, and the older **evaluation module** (`vertexai.evaluation.EvalTask`). Related pages: "Details for managed rubric-based metrics", "Evaluate agents", "Evaluate a judge model", "Run AutoSxS pipeline". The default metric is `GENERAL_QUALITY`, an "adaptive rubric-based metric", where rubrics are generated per prompt and then judged.
```python
# pip install google-cloud-aiplatform[evaluation]
from vertexai import Client
client = Client(project="YOUR_PROJECT_ID", location="YOUR_LOCATION")
eval_dataset = client.evals.run_inference(model="gemini-2.5-flash", src=eval_df)
eval_dataset.show()
eval_result = client.evals.evaluate(dataset=eval_dataset)
eval_result.show()
```
Source: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-genai-sdk . Explicit metric objects such as `types.RubricMetric.GENERAL_QUALITY` and `types.PrebuiltMetric...` are [UNVERIFIED this session], as is any deprecation date for `EvalTask`. Google ADK ships `adk eval` with `.test.json`/`.evalset.json` files (tool-trajectory and response-match scores) [UNVERIFIED this session].

**Framework selection summary**

| Need | Pick |
|---|---|
| Base-model academic benchmarks, reproducible few-shot | lm-evaluation-harness |
| Agentic / safety / sandboxed evals, research-grade logs | Inspect AI |
| Broad multi-metric reference leaderboards | HELM (now maintenance mode) |
| Prompt/regression CI and red-teaming via YAML | promptfoo |
| pytest-style app tests, RAG metrics, G-Eval | DeepEval |
| Managed GCP, adaptive rubrics, agent eval, AutoSxS | Vertex Gen AI evaluation service |
| OpenAI-hosted graders and dashboard | OpenAI Evals |

---

## 11. Quality card: model cards, datasheets, data cards and eval reports

- Mitchell et al., *Model Cards for Model Reporting*, FAT* 2019, arXiv:1810.03993. "Model cards are short documents accompanying trained machine learning models". They cover intended use, performance across demographic and intersectional groups, and evaluation procedures. Canonical sections: Model Details, Intended Use, Factors, Metrics, Evaluation Data, Training Data, Quantitative Analyses, Ethical Considerations, Caveats & Recommendations [section list from paper PDF, recalled]. https://arxiv.org/abs/1810.03993
- Gebru et al., *Datasheets for Datasets*, arXiv:1803.09010 (CACM 2021). It covers motivation, composition, collection, preprocessing/labeling, uses, distribution and maintenance.
- Pushkarna et al., *Data Cards*, FAccT 2022, arXiv:2204.01075. Lessons from "over 20 Data Cards" at Google.
- Hugging Face model/dataset cards (README.md with YAML metadata, including `model-index` eval results) are the de facto industry format.

**Proposed "Eval Quality Card" template (synthesis for the deck):**
```
Eval set: support-bot-golden v3.2   Owner: <domain expert>   Date: 2026-10
Provenance: 62% prod traces (PII-scrubbed), 38% synthetic (human-validated)
Size / slices: n=640; 9 slices (min n=48); prevalence of positive class 4.1%
Decontamination: 13-gram + embedding (cos>0.92) vs SFT set -> 11 removed
Labels: 2 experts + adjudication; Cohen kappa=0.78; label-noise audit 3.1%
Judge: <model>@<version>, prompt v7; TPR=0.91 TNR=0.88 vs experts (n=200)
Headline: pass 84.2% [81.3, 86.9] (bootstrap 95%); worst slice: refunds-ES 71% [58, 81]
Calibration: ECE=0.04 (15 bins) after temperature scaling
Operating point: t=0.05 for C_FN/C_FP=20 at prod prevalence 2%
Known gaps / not measured: multi-turn > 8 turns, voice channel
```

---

## 12. Denoise: label noise in eval sets

- Northcutt, Jiang, Chuang, *Confident Learning: Estimating Uncertainty in Dataset Labels*, arXiv:1911.00068 (JAIR 2021). The `cleanlab` library implements it (`cleanlab.filter.find_label_issues`).
- Northcutt, Athalye, Mueller, *Pervasive Label Errors in Test Sets Destabilize Machine Learning Benchmarks*, arXiv:2103.14749 (NeurIPS 2021 D&B). It estimated an average of about 3.3% label errors across 10 popular test sets, with ImageNet val at about 6% [figures recalled, UNVERIFIED this session]. A quotable implication: model rankings can flip on corrected test sets.
- LLM-era example: MMLU errors motivated *Are We Done with MMLU?* (MMLU-Redux, arXiv:2406.04127) [UNVERIFIED this session], and SimpleQA was re-curated as "SimpleQA-Verified", the dataset used in the Inspect hello-world above.

The flow is: model-disagreement flags, then expert re-label, then adjudicate, then log the change in the card, then bump the version.

```python
from cleanlab.filter import find_label_issues
issues = find_label_issues(labels=y, pred_probs=oof_probs,
                           return_indices_ranked_by="self_confidence")
review_queue = df.iloc[issues[:200]]       # send to experts
```

---

## 13. Real-world examples

- **HF Open LLM Leaderboard**: ran on lm-evaluation-harness and was retired in 2025 after benchmark saturation and contamination concerns [retirement date UNVERIFIED this session].
- **UK AISI and partner institutes**: Inspect AI for pre-deployment frontier-model testing.
- **LMArena (ex-Chatbot Arena)**: pairwise human preference with BT ratings. Labs cite Arena ranks at launch.
- **Google Cloud customers**: Gen AI evaluation service with adaptive rubrics and AutoSxS for model migration (e.g. moving to a new Gemini version).
- **Anthropic**: Miller (2024) error-bars paper. It argues that leaderboards should report SEs.
- **OpenAI**: open-source Evals registry, then dashboard-hosted evals and graders.
- **Startups (Husain/Shankar case studies)**: error analysis on 100+ traces, binary judges, and a benevolent dictator.

---

## 14. Open challenges (Oct 2026)

1. **Benchmark saturation and contamination.** Static public sets have a short half-life, so private, refreshed holdouts are needed.
2. **Judge validity.** Judges share blind spots with the candidates (same pretraining). Self-preference is not fully solved.
3. **Agent evals.** Trajectory scoring, nondeterminism, environment cost and side effects. Pass@k vs pass^k reliability.
4. **Statistical hygiene is still rare.** Most reports omit CIs and clustering; many "SOTA" deltas sit inside the noise.
5. **Cost-aware evaluation.** Quality per dollar and latency tails belong in the operating point.
6. **Arena gaming and style confounds** in preference leaderboards.
7. **Tool churn.** HELM is in maintenance mode, Vertex docs were renamed to Gemini Enterprise Agent Platform, DeepEval params were renamed, and the lm-eval CLI was refactored. Pin versions in eval reports.

---

## 15. Slide ideas (8)

1. **"Evals are experiments"**: the lifecycle strip DESIGN to QUALITY CARD with an animated feedback arrow from error analysis back to DESIGN. Quote Miller.
2. **Error analysis to failure taxonomy**: animate 100 trace cards clustering into 6 labeled failure-mode piles (open coding, then axial coding), each pile becoming a slice and a binary eval.
3. **Slices beat averages**: a bar chart where the global 84% stays flat while one slice drops from 80 to 62. Reveal it by toggling "show slices".
4. **Error bars change the story**: two leaderboard bars (A 81.0, B 82.1). Animate CI whiskers growing until they overlap, then switch to the paired-bootstrap delta histogram with the 0 line.
5. **Calibration**: a reliability diagram before and after temperature scaling, with bars sliding onto the diagonal and the ECE counter dropping.
6. **Pick the threshold with money**: a ROC curve with an iso-cost line sweeping as the C_FN/C_FP slider moves, and the operating point dot sliding along the curve. Formula t* = C_FP/(C_FP+C_FN).
7. **LLM-as-judge pitfalls**: four bias icons (position, verbosity, self-preference, vague scale) flip to their mitigations, ending on the judge-vs-human confusion matrix with kappa, TPR and TNR.
8. **Pairwise to Bradley-Terry**: a battle graph of models (nodes) and votes (edges) morphs into a ranked list with bootstrap CI whiskers. Note Elo's order dependence.
9. **Framework map**: a 2x2 (research benchmark vs app testing x self-hosted vs managed) placing lm-eval, Inspect, HELM, promptfoo, DeepEval, Vertex and OpenAI Evals, with version badges.
10. **The Quality Card**: the template from section 11 filled in, with highlights pulsing on CI, kappa, ECE and operating point. Tagline: "No number without n, CI, slice and version."

---

## Sources (fetched this session unless noted)
- https://arxiv.org/abs/2411.00640 - Miller, Adding Error Bars to Evals (2024)
- https://arxiv.org/abs/2306.05685 - Zheng et al., Judging LLM-as-a-Judge (NeurIPS 2023)
- https://arxiv.org/abs/2403.04132 - Chiang et al., Chatbot Arena (2024)
- https://arxiv.org/abs/1706.04599 - Guo et al., On Calibration of Modern Neural Networks (ICML 2017)
- https://arxiv.org/abs/1810.03993 - Mitchell et al., Model Cards (FAT* 2019)
- https://arxiv.org/abs/2204.01075 - Pushkarna et al., Data Cards (FAccT 2022)
- https://arxiv.org/abs/2404.12272 - Shankar et al., Who Validates the Validators? (2024)
- https://hamel.dev/blog/posts/evals-faq/ - Husain & Shankar, AI Evals FAQ (2026-09-18)
- https://github.com/EleutherAI/lm-evaluation-harness ; https://pypi.org/project/lm-eval/ (0.4.13)
- https://inspect.aisi.org.uk/ ; https://pypi.org/project/inspect-ai/ (0.3.283)
- https://github.com/stanford-crfm/helm
- https://github.com/openai/evals
- https://www.promptfoo.dev/docs/getting-started/
- https://deepeval.com/docs/getting-started ; https://pypi.org/project/deepeval/ (4.3.1)
- https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-genai-sdk
- Not re-fetched (cited from memory): arXiv 2305.17926, 2303.16634, 2404.04475, 1803.09010, 1911.00068, 2103.14749, 2211.09110, 2406.04127, 2504.20879
