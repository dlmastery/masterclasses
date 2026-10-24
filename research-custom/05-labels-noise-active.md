# 05 - Labels, Label Noise, Active Learning, Weak Supervision and Leakage

Research notes for the deck "Customizing modern AI (SFT, RL, RAG)" and "Data-Centric AI: modern dataset design and synthesis". Current to 2026-10-23.
Lifecycle position: design -> generate -> select -> curate -> **label -> denoise** -> quality card. This file also covers **leakage/contamination**, which is the "split and evaluate honestly" gate that comes before the quality card.

> Verification note: package versions were read from PyPI JSON on 2026-10-23. Paper facts come from arXiv abstract pages. My web-search quota ran out partway through, so some items below are marked [UNVERIFIED].

---

## 0. Version table (PyPI, checked 2026-10-23)

| Package | Latest | Release date | Notes |
|---|---|---|---|
| `cleanlab` | **2.9.0** | 2026-01-13 | 2.8.0 came out 2026-01-08 and 2.7.1 on 2025-02-27 |
| `scikit-learn` | **1.9.1** | date not read [UNVERIFIED] | `cohen_kappa_score`, `GroupKFold`, `StratifiedGroupKFold`, `TimeSeriesSplit` |
| `snorkel` | **0.10.0** | 2024-02-27 | No release since then. PyPI lists CVE-2026-31222..31224 (unsafe deserialization, affects versions up to 0.10.0, no fixed version listed) |
| `argilla` | **2.8.0** | 2025-03-10 | v2 SDK (`rg.Argilla`, `rg.Settings`, `rg.Dataset`) |
| `label-studio` | **1.23.2** | date not read [UNVERIFIED] | |
| `datasketch` | **2.0.0** | date not read. 1.10.0 came out 2026-04-17 | MinHash, MinHashLSH, LSHBloom, LSH Forest, LSH Ensemble, HNSW |
| `krippendorff` | **0.9.0** | 2026-10-07 | `krippendorff.alpha(reliability_data=..., level_of_measurement=...)` |
| `statsmodels` | (stable docs) | - | `statsmodels.stats.inter_rater.fleiss_kappa(table, method='fleiss')`, `aggregate_raters` |

Slide takeaway: Snorkel OSS has had no release since February 2024 and now has open CVEs. Treat it as a teaching reference, and check it before using it in production. cleanlab is actively maintained (2.9.0).

---

## 1. Why labels matter: the numbers

- **Test sets contain errors.** Northcutt, Athalye and Mueller, *"Pervasive Label Errors in Test Sets Destabilize Machine Learning Benchmarks"* (NeurIPS 2021 Datasets & Benchmarks; arXiv:2103.14749, https://arxiv.org/abs/2103.14749):
  - Errors average **3.3% across 10 test sets** spanning vision, text and audio. The arXiv version says "at least 3.3%".
  - The ImageNet validation set has **2,916 label errors, about 6%**.
  - Of the candidates flagged by confident learning, **51% (arXiv) / 54% (NeurIPS)** were confirmed as errors by human reviewers.
  - On corrected ImageNet labels, **ResNet-18 outperforms ResNet-50** if the share of originally mislabeled test examples rises by just 6%.
  - Quotable: errors can "destabilize ML benchmarks". Model rankings can flip.
  - Demo site: https://labelerrors.com
- **Leakage drives a reproducibility crisis.** Kapoor and Narayanan, *"Leakage and the Reproducibility Crisis in ML-based Science"* (2022; arXiv:2207.07048, https://arxiv.org/abs/2207.07048):
  - Leakage errors were found in **329 papers across 17 fields**.
  - The paper gives a taxonomy of **8 types of leakage**.
  - It proposes **model info sheets** for reporting ML-based claims.
  - In a civil-war prediction case study, the claims that complex ML beat logistic regression failed to reproduce once leakage was fixed: "complex ML models don't perform substantively better than decades-old LR models."
- **Duplicates inflate scores and memorization.** Lee et al., *"Deduplicating Training Data Makes Language Models Better"* (ACL 2022; arXiv:2107.06499, https://arxiv.org/abs/2107.06499):
  - One 61-word sentence was repeated **over 60,000 times in C4**.
  - Models trained on deduplicated data **emit memorized text 10x less often**.
  - Train-test overlap affects **over 4% of the validation sets** of standard datasets.
  - Over 1% of unprompted LM output is copied verbatim from training data.

---

## 2. Inter-annotator agreement (IAA)

### Definitions (in words, for a formula slide)
- **Cohen's kappa** (2 raters, nominal): κ = (p_o − p_e) / (1 − p_e), where p_o is observed agreement and p_e is chance agreement from each rater's marginal distribution. **Weighted kappa** (linear or quadratic) suits ordinal scales such as 1-5 ratings.
- **Fleiss' kappa** (fixed number of raters per item, raters may differ across items; nominal). Input is an items × categories count table.
- **Krippendorff's alpha**: α = 1 − D_o / D_e, the ratio of observed to expected disagreement.
  - Handles **any number of raters, missing ratings**, and nominal, ordinal, interval or ratio levels.
  - This makes it the right default for crowd and LLM-plus-human panels, where not everyone labels everything.
  - Krippendorff's rule of thumb: α ≥ 0.800 is reliable, and 0.667 ≤ α < 0.800 is acceptable only for tentative conclusions. Source: Krippendorff, *Content Analysis*. I did not fetch it in this session [UNVERIFIED wording].
- **Landis & Koch (1977) kappa bands**: 0.41–0.60 moderate, 0.61–0.80 substantial, 0.81–1.00 almost perfect. Widely cited, but arbitrary.
- **Kappa paradox**: with highly skewed class priors, kappa can be low even when raw agreement is high. Report raw agreement **and** a chance-corrected statistic.

### Code: all three metrics
```python
# sklearn 1.9.x, statsmodels, krippendorff 0.9.0
import numpy as np
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa
import krippendorff

a = [0, 1, 1, 2, 0, 2, 1]
b = [0, 1, 2, 2, 0, 2, 0]
print("Cohen k:", cohen_kappa_score(a, b))                       # nominal
print("Quadratic-weighted k:", cohen_kappa_score(a, b, weights="quadratic"))  # ordinal

ratings = np.array([[0, 0, 1], [1, 1, 1], [2, 2, 1], [0, 0, 0]])  # items x raters
table, _ = aggregate_raters(ratings)                              # items x categories counts
print("Fleiss k:", fleiss_kappa(table, method="fleiss"))

# Krippendorff: raters x items, np.nan = missing rating
rel = np.array([[0, 1, 2, np.nan], [0, 1, 2, 0], [1, 1, np.nan, 0]])
print("Krippendorff a:", krippendorff.alpha(reliability_data=rel, level_of_measurement="nominal"))
```
Sources:
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html
- https://www.statsmodels.org/stable/generated/statsmodels.stats.inter_rater.fleiss_kappa.html
- https://pypi.org/project/krippendorff/

### Practice: the annotation loop
1. Write guidelines.
2. Run a pilot of about 50–200 items with 3+ raters.
3. Compute α or κ per label.
4. Run an adjudication meeting.
5. Revise the guidelines.
6. Repeat until α ≥ 0.8.
7. Then scale up, keeping 5–10% overlap items so drift can be monitored.

Low agreement is often *signal*, not noise: it can mean the task is genuinely subjective (toxicity, helpfulness). In that case, consider keeping soft labels or per-annotator labels (the "perspectivist" view) instead of forcing a majority vote.

---

## 3. LLM-as-annotator and LLM-as-judge: agreement with humans

- **Gilardi, Alizadeh and Kubli**, *"ChatGPT Outperforms Crowd-Workers for Text-Annotation Tasks"*, PNAS 120(30), 2023 (arXiv:2303.15056, https://arxiv.org/abs/2303.15056):
  - Data: 2,382 tweets.
  - Zero-shot ChatGPT beat MTurk crowd-workers on **4 of 5 tasks**.
  - Its intercoder agreement exceeded both crowd-workers and trained annotators on all tasks.
  - Cost was **under $0.003 per annotation, "about twenty times cheaper than MTurk."**
- **Zheng et al.**, *"Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"* (NeurIPS 2023 D&B; arXiv:2306.05685, https://arxiv.org/abs/2306.05685):
  - GPT-4 reaches **"over 80% agreement"** with human preferences, "the same level of agreement between humans".
  - Documented biases: **position, verbosity, self-enhancement**, plus limited reasoning.
- **Bavaresco et al.**, *"LLMs instead of Human Judges? A Large Scale Empirical Study across 20 NLP Evaluation Tasks"* (JUDGE-BENCH, ACL 2025; arXiv:2406.18403, https://arxiv.org/abs/2406.18403):
  - 11 LLMs were tested on 20 human-annotated datasets.
  - Reliability "varies substantially" by model, property and annotator expertise.
  - Quote: "LLMs should be carefully validated against human judgments before being used as evaluators."

**Recipe for a hybrid LLM + human labeling pipeline (step flow for a slide):**
1. Humans label a **gold set** of about 200–500 items with high IAA.
2. The LLM labels the same gold set. Compute **κ or α between LLM and humans**, and compare it with human–human α. Accept the LLM if LLM–human α is close to human–human α.
3. Mitigate known biases: swap answer order and average, constrain the output to a fixed label set, use a temperature of 0, and use several judges or several prompts with a majority vote.
4. Send low-confidence or disagreeing items to humans. This is active learning plus routing.
5. Run cleanlab on the merged labels to find the remaining errors. Re-audit 2–5% of the LLM labels each week to catch drift.

Real-world: Argilla and Label Studio both support **LLM pre-annotation as "suggestions"** that humans accept or correct. Scale AI, Surge and Snorkel Flow sell expert-plus-LLM labeling for RLHF and SFT data [vendor claims, UNVERIFIED specifics].

---

## 4. Confident learning and cleanlab (denoise)

**Paper:** Northcutt, Jiang and Chuang, *"Confident Learning: Estimating Uncertainty in Dataset Labels"*, JAIR 2021 (arXiv:1911.00068, https://arxiv.org/abs/1911.00068).
- Principles: **prune, count, rank**.
- It estimates the **joint distribution of noisy (given) and true labels**, Q(ỹ, y*), under a class-conditional noise assumption. The paper calls the counted matrix the "confident joint".
- Claims: it is provably consistent, it outperformed 7 noisy-label methods on CIFAR, and it found about 645 ImageNet "missile" images labeled as the parent class "projectile".

**Algorithm in words (diagram):**
1. Get **out-of-sample** predicted probabilities for every example with K-fold `cross_val_predict`. In-sample probabilities memorize the noise.
2. Compute a per-class threshold t_j = the model's average self-confidence on examples labeled j.
3. Example x labeled i counts toward cell (i, j) if p̂(j|x) ≥ t_j, using the argmax over the classes that pass their threshold.
4. Off-diagonal cells are likely label errors. Rank them by self-confidence or normalized margin.
5. Prune or relabel them, then retrain.

**Code (cleanlab 2.9.0, adapted from https://docs.cleanlab.ai/stable/tutorials/indepth_overview.html):**
```python
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
import cleanlab
from cleanlab.classification import CleanLearning
from cleanlab import Datalab

model = LogisticRegression(max_iter=1000)
# 1) out-of-sample probabilities (critical!)
pred_probs = cross_val_predict(model, X, labels, cv=5, method="predict_proba")

# 2) ranked indices of likely label errors
issues = cleanlab.filter.find_label_issues(
    labels=labels, pred_probs=pred_probs,
    filter_by="both", return_indices_ranked_by="self_confidence")

# 3) one-liner wrapper: finds issues then trains on cleaned data
cl = CleanLearning(model).fit(X, labels)
print(cl.get_label_issues().head())

# 4) Datalab audit: label errors + outliers + (near-)duplicates + non-IID in one report
lab = Datalab({"X": X, "y": labels}, label_name="y")
lab.find_issues(pred_probs=pred_probs, features=X)
lab.report()
```
Note: `pred_probs` columns must be ordered lexicographically by class name (cleanlab docs).

Datalab is the bridge to the quality card. A single audit covers label issues, outliers, near-duplicates and non-IID drift. The full list of issue types is in the Datalab docs [verify the list for 2.9.0].

---

## 5. Dataset cartography (training dynamics)

Swayamdipta et al., *"Dataset Cartography: Mapping and Diagnosing Datasets with Training Dynamics"* (EMNLP 2020; arXiv:2009.10795, https://arxiv.org/abs/2009.10795).
- For each example, record p(y_true | x) at the end of every epoch.
  - **Confidence** = the mean over epochs.
  - **Variability** = the standard deviation over epochs.
  - Correctness = the fraction of epochs where the prediction is right.
- The map has three regions:
  - **Easy-to-learn**: high confidence, low variability. This is the most populous region and helps optimization.
  - **Ambiguous**: high variability. These examples contribute most to out-of-distribution generalization.
  - **Hard-to-learn**: low confidence, low variability. These often correspond to labeling errors.
- Use it to send hard-to-learn examples to relabeling, and to train on the ambiguous subset (about 33% of examples) for robustness.

```python
# Minimal cartography logger (illustrative, my own code; Swayamdipta et al. 2020 definitions)
import numpy as np
probs_per_epoch = []                      # list of arrays, shape [n_examples]
for epoch in range(E):
    train_one_epoch(model)
    p = model.predict_proba(X_train)[np.arange(len(y)), y]   # p(true label)
    probs_per_epoch.append(p)
P = np.stack(probs_per_epoch)             # [E, n]
confidence, variability = P.mean(0), P.std(0)
hard_to_learn = np.where((confidence < 0.2) & (variability < 0.1))[0]  # relabel queue
ambiguous     = np.argsort(-variability)[: len(y) // 3]                # top-33% ambiguous
```
Official code: https://github.com/allenai/cartography

Modern LLM-era relatives (for one slide): loss- or perplexity-based data selection, "learnability" scores, and influence functions. AUM (Area Under the Margin, Pleiss et al., NeurIPS 2020) is another training-dynamics mislabel detector [UNVERIFIED in this session].

---

## 6. Active learning: label the right examples

**Loop (animation):** a small labeled seed → train → score the unlabeled pool → select a batch of size B → humans or an LLM label it → add it to the training set → repeat until the budget runs out or performance plateaus.

Query strategies:
- **Uncertainty**: least confidence (1 − max p), margin (p1 − p2), or entropy. It is cheap, but batches end up redundant because similar points get picked together.
- **Diversity / core-set**: Sener and Savarese, *"Active Learning for Convolutional Neural Networks: A Core-Set Approach"*, ICLR 2018 (arXiv:1708.00489, https://arxiv.org/abs/1708.00489). The paper treats active learning as core-set selection, "choosing set of points such that a model learned over the selected subset is competitive for the remaining data points". In practice this means greedy **k-center** in embedding space. The k-center detail comes from the paper body; the abstract does not name it.
- **BADGE**: Ash et al., *"Deep Batch Active Learning by Diverse, Uncertain Gradient Lower Bounds"*, ICLR 2020 (arXiv:1906.03671, https://arxiv.org/abs/1906.03671).
  - It embeds each unlabeled point as the **gradient of the loss with respect to the last layer, using the model's own predicted label as a hypothetical label**. The gradient norm reflects uncertainty, and the gradient direction reflects diversity.
  - It then runs **k-means++ seeding** on these embeddings.
  - It "balances uncertainty and diversity" with no hand-tuned trade-off.
- LLM-era twists:
  - Use LLM disagreement or self-consistency as the uncertainty signal.
  - Run diversity selection on sentence embeddings.
  - Combine active learning with the LLM-annotator routing described in Section 3.

```python
# Margin uncertainty + k-center diversity (illustrative; numpy/sklearn only)
import numpy as np
P = clf.predict_proba(X_pool)
s = np.sort(P, axis=1); margin = s[:, -1] - s[:, -2]
cand = np.argsort(margin)[:10 * B]                     # top uncertain candidates

def k_center(emb, labeled_emb, B):                     # greedy core-set (Sener & Savarese 2018)
    d = np.min(((emb[:, None] - labeled_emb[None]) ** 2).sum(-1), axis=1)
    picked = []
    for _ in range(B):
        i = int(np.argmax(d)); picked.append(i)
        d = np.minimum(d, ((emb - emb[i]) ** 2).sum(-1))
    return picked

batch = cand[k_center(E_pool[cand], E_labeled, B)]
```
```python
# BADGE gradient embedding for softmax + linear head (illustrative)
# g_x = (p - onehot(argmax p)) ⊗ h(x)  -> then k-means++ seeding
from sklearn.cluster import kmeans_plusplus
yhat = P.argmax(1); G = P.copy(); G[np.arange(len(P)), yhat] -= 1
emb = (G[:, :, None] * H_pool[:, None, :]).reshape(len(P), -1)   # H_pool = penultimate features
_, idx = kmeans_plusplus(emb, n_clusters=B, random_state=0)
```
Libraries:
- modAL: https://github.com/modAL-python/modAL
- small-text: https://github.com/webis-de/small-text
- Baidu's DeepAL repo, which reimplements BADGE [UNVERIFIED versions]

The official BADGE code is https://github.com/JordanAsh/badge.

Open challenges:
- Cold start, since active learning is weak with tiny seeds.
- Sampling bias: the labeled set is no longer IID, so evaluate on a **separately sampled random test set**.
- Results often fail to beat random sampling once strong pretrained embeddings are used.

---

## 7. Weak supervision (Snorkel)

Ratner et al., *"Snorkel: Rapid Training Data Creation with Weak Supervision"*, PVLDB 11(3), 2017 (arXiv:1711.10160, https://arxiv.org/abs/1711.10160):
- Subject-matter experts built models **2.8x faster** than with hand labeling, with **+45.5%** average predictive performance compared with 7 hours of hand labeling.
- Snorkel came within **3.60%** of the performance of large hand-curated training sets.

**Flow (diagram):**
1. Write many noisy **labeling functions (LFs)**: keyword rules, regexes, heuristics, distant supervision, LLM prompts. Each LF returns a label or ABSTAIN.
2. Build the label matrix L (n × m).
3. A **LabelModel** learns each LF's accuracy and correlations **without ground truth**, from agreements and disagreements.
4. It outputs probabilistic labels.
5. Train an end discriminative model on those labels, which generalizes beyond the LFs.

```python
# snorkel 0.10.0 - adapted from the official spam tutorial
# https://github.com/snorkel-team/snorkel-tutorials/blob/master/spam/01_spam_tutorial.py
from snorkel.labeling import labeling_function, PandasLFApplier, LFAnalysis, filter_unlabeled_dataframe
from snorkel.labeling.model import LabelModel
ABSTAIN, HAM, SPAM = -1, 0, 1

@labeling_function()
def lf_check_out(x):
    return SPAM if "check out" in x.text.lower() else ABSTAIN

@labeling_function()
def lf_short(x):
    return HAM if len(x.text.split()) < 5 else ABSTAIN

lfs = [lf_check_out, lf_short]
L_train = PandasLFApplier(lfs=lfs).apply(df=df_train)
print(LFAnalysis(L=L_train, lfs=lfs).lf_summary())        # coverage, overlaps, conflicts

label_model = LabelModel(cardinality=2, verbose=True)
label_model.fit(L_train=L_train, n_epochs=500, log_freq=100, seed=123)
probs_train = label_model.predict_proba(L=L_train)
df_f, probs_f = filter_unlabeled_dataframe(X=df_train, y=probs_train, L=L_train)
```

Real-world:
- Snorkel AI's commercial **Snorkel Flow**.
- Google's *Snorkel DryBell* (SIGMOD 2019) used weak supervision at industrial scale [UNVERIFIED in this session].
- 2025–26 trend: **LLM prompts as labeling functions**, where an LLM's zero-shot label is one noisy LF among many and the label model calibrates it.

---

## 8. Annotation tools

| Tool | What it is | LLM-era features |
|---|---|---|
| **Label Studio** (HumanSignal), OSS 1.23.2 | Multi-modal labeling (text, image, audio, video, time series) configured with XML templates. The ML backend connects pre-labeling and active-learning models | LLM pre-annotation through the ML backend. Enterprise adds "Prompts" for LLM labeling and evaluation [UNVERIFIED feature naming] |
| **Argilla**, 2.8.0 (Hugging Face; Argilla joined HF in 2024 [UNVERIFIED date]) | Python-first feedback and annotation for LLM data: SFT, preference/DPO and RAG relevance. Deploys as an HF Space | Records carry model `suggestions`. Datasets can be pushed to and pulled from the HF Hub. Pairs with `distilabel` for synthetic data plus AI feedback |
| Others | Prodigy (Explosion, active learning built in), CVAT (vision), Labelbox, Scale | - |

```python
# argilla 2.x SDK - adapted from https://docs.argilla.io/latest/how_to_guides/dataset/
import argilla as rg
client = rg.Argilla(api_url="<api_url>", api_key="<api_key>")
settings = rg.Settings(
    guidelines="Label the sentiment. Use 'unsure' if ambiguous.",
    fields=[rg.TextField(name="text")],
    questions=[rg.LabelQuestion(name="label", labels=["positive", "negative", "unsure"])],
)
dataset = rg.Dataset(name="sentiment_v1", settings=settings, client=client)
dataset.create()
dataset.records.log([rg.Record(fields={"text": "Great battery life."})])
```

---

## 9. Leakage: entity, group and time

**Types (taxonomy slide):**
- **Entity or group leakage.** The same patient, user, speaker, product, repository or document family appears in both train and test, so the model memorizes identity. Example: multiple scans per patient in medical imaging.
- **Temporal leakage.** Training on the future and testing on the past, or features computed with future information (a "next 30 days" aggregate computed at an inference time where it would not exist).
- **Preprocessing leakage.** Fitting the scaler, imputer, feature selection, SMOTE or tokenizer vocabulary on the full data before splitting. Fix: put every fitted step inside a `Pipeline` that is cross-validated.
- **Duplicate or near-duplicate leakage.** The same or a paraphrased item lands in both splits.
- **Target leakage.** A feature that is a proxy for the label, such as "treatment given" when predicting the diagnosis.
- **Benchmark contamination.** The LLM's pretraining corpus contains the test set (Section 11).

sklearn doc quote: "While i.i.d. data is a common assumption in machine learning theory, it rarely holds in practice... if we know that the generative process has a group structure (samples collected from different subjects, experiments, measurement devices), it is safer to use group-wise cross-validation." (https://scikit-learn.org/stable/modules/cross_validation.html)

```python
# scikit-learn 1.9.x - group-aware and time-aware splits
from sklearn.model_selection import GroupKFold, StratifiedGroupKFold, TimeSeriesSplit, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))  # scaler fit per fold
# Entity leakage: no patient_id in both train and test
print(cross_val_score(pipe, X, y, groups=patient_id, cv=GroupKFold(n_splits=5)))
# Imbalanced classes + groups
print(cross_val_score(pipe, X, y, groups=patient_id, cv=StratifiedGroupKFold(n_splits=5)))
# Temporal: train on past, test on future, with a gap to avoid boundary bleed
tscv = TimeSeriesSplit(n_splits=5, gap=7)   # rows must be sorted by time
print(cross_val_score(pipe, X_sorted, y_sorted, cv=tscv))
```
Behavior notes from the docs:
- `GroupKFold`: "the same subject is never in both testing and training". With `shuffle=True` it balances the number of distinct groups per fold.
- `TimeSeriesSplit`: "successive training sets are supersets of those that come before them".

For LLM and RAG evaluation sets, use **time-based holdouts**: test only on documents and questions created after the model's training cutoff.

---

## 10. Near-duplicate deduplication (MinHash / LSH)

**Flow (diagram):**
1. Normalize the text (lowercase, strip whitespace and punctuation).
2. Shingle it into word or character n-grams (for example, 5-gram word shingles).
3. MinHash each document's shingle set into a signature, for example 128 permutations. The probability that two signatures agree at a position equals the Jaccard similarity.
4. LSH banding splits the signature into b bands of r rows. Two documents become candidates if any band matches. The match probability is 1 − (1 − s^r)^b, an S-curve with its threshold near (1/b)^(1/r).
5. Verify each candidate pair's Jaccard similarity.
6. Build a graph of duplicate pairs, find its connected components, and keep one document per cluster.

At web scale this is the standard recipe in LLM pretraining pipelines (C4/Lee et al., RefinedWeb, FineWeb via `datatrove` [UNVERIFIED parameters]). Exact-substring dedup with suffix arrays (Lee et al. 2022) is the complement.

```python
# datasketch - verbatim pattern from https://ekzhu.com/datasketch/lsh.html (adapted)
from datasketch import MinHash, MinHashLSH

def mh(text, num_perm=128, n=5):
    toks = text.lower().split()
    m = MinHash(num_perm=num_perm)
    for sh in {" ".join(toks[i:i + n]) for i in range(max(1, len(toks) - n + 1))}:
        m.update(sh.encode("utf8"))
    return m

lsh = MinHashLSH(threshold=0.8, num_perm=128)
keep = []
for doc_id, text in corpus.items():
    m = mh(text)
    if lsh.query(m):          # near-duplicate of something already kept
        continue
    lsh.insert(doc_id, m); keep.append(doc_id)
```
**Cross-split dedup**: build the index on the **test set**, then query every training document against it and drop the matches. This is the cheapest leakage fix there is. For paraphrase-level duplicates, use embedding similarity (cosine above about 0.9, with a FAISS or HNSW index). cleanlab Datalab also flags near-duplicates from features.

---

## 11. Benchmark contamination in LLMs

- **Sainz et al.**, *"NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark"* (EMNLP 2023 Findings; arXiv:2310.18018, https://arxiv.org/abs/2310.18018). Contamination inflates scores and may lead to "incorrect scientific conclusions" being published. The authors call for per-benchmark contamination measurement and for flagging papers whose conclusions are compromised.
- **GSM1k**: Zhang et al., *"A Careful Examination of Large Language Model Performance on Grade School Arithmetic"* (NeurIPS 2024 D&B; arXiv:2405.00332, https://arxiv.org/abs/2405.00332).
  - GSM1k is a fresh, matched-difficulty clone of GSM8k.
  - Accuracy drops by **up to 8%** on it, and several model families show systematic overfitting.
  - A model's likelihood of generating GSM8k examples correlates with its gap (Spearman **r² = 0.36**).
  - Many frontier models show minimal overfitting.
- **Detection: Min-K% Prob.** Shi et al., *"Detecting Pretraining Data from Large Language Models"* (arXiv:2310.16789, https://arxiv.org/abs/2310.16789; published at ICLR 2024 [venue UNVERIFIED on the page]).
  - Intuition: an unseen text is "likely to contain a few outlier words with low probabilities under the LLM".
  - Score = the average log-probability of the k% lowest-probability tokens.
  - It needs no reference model and achieved **+7.4% on WikiMIA** over prior methods.
- **Prevention: dynamic, time-stamped benchmarks.** LiveCodeBench (Jain et al., arXiv:2403.07974, https://arxiv.org/abs/2403.07974) continuously collects new problems from LeetCode, AtCoder and Codeforces (400 problems from May 2023 to May 2024 at the time of the paper). It evaluates each model on problems released after its cutoff. LiveBench and private held-out sets (for example, Scale SEAL) follow the same idea [UNVERIFIED details].
- Other signals: n-gram overlap audits (the GPT-3/GPT-4 reports used 13-gram and 50-character overlap [UNVERIFIED exact numbers]), **canary strings** (BIG-bench embeds a GUID so corpus builders can filter it out), and performance on reworded or perturbed versions.

```python
# Min-K% Prob sketch with Hugging Face transformers (illustrative)
import torch
def min_k_prob(text, model, tok, k=0.2):
    ids = tok(text, return_tensors="pt").input_ids
    with torch.no_grad():
        logits = model(ids).logits[0, :-1]
    lp = torch.log_softmax(logits, -1).gather(1, ids[0, 1:, None]).squeeze(1)
    n = max(1, int(k * lp.numel()))
    return lp.topk(n, largest=False).values.mean().item()   # higher => more likely seen in training
```

**Contamination checklist for an SFT/RL/RAG project:**
1. Decontaminate the SFT and RL training sets against **every** eval set using n-gram plus MinHash plus embedding matching.
2. Keep a private, time-stamped holdout.
3. Report the model's training cutoff next to each eval result.
4. For RL with verifiable rewards, check that the reward problems do not overlap the benchmark problems.
5. Record all of this in the dataset or quality card under "decontamination: method, thresholds, # removed".

---

## 12. Open challenges (Oct 2026)
1. **LLM-label feedback loops**: models trained on LLM labels inherit and amplify that LLM's biases, and the agreement metrics themselves get gamed.
2. **Subjective tasks**: should we aggregate (majority, Dawid–Skene) or keep the disagreement (soft labels, pluralistic alignment)?
3. **Label noise at preference and RLHF scale**: inter-annotator agreement on pairwise preferences is often only 60–75% [UNVERIFIED range]. Confident learning for preference pairs and reward models is still immature.
4. **Contamination is unknowable for closed models**: membership-inference methods (Min-K%) are noisy, and later work disputes how reliable they are [UNVERIFIED].
5. **Active learning with foundation models**: gains over random sampling shrink once representations are strong, and selection costs compute.
6. **Weak-supervision tooling sustainability**: Snorkel OSS is stagnant and has CVEs. LLM-as-LF tooling is fragmented.
7. **Group definitions are domain knowledge**: no algorithm can tell you that two images come from the same patient if the metadata is missing.

---

## 13. Slide ideas (8)
1. **"6% of ImageNet val is wrong"**: a grid of real label errors from labelerrors.com that flip on hover, plus a bar chart of error rates for the 10 datasets. Animation: the ResNet-18 vs ResNet-50 ranking swaps as the noise slider moves.
2. **"Agreement before scale"**: an animated κ formula (p_o vs p_e bars), a Landis–Koch color band, and a Krippendorff α panel with missing cells shown as grey. Callout: the kappa paradox with skewed classes.
3. **"LLM as annotator: trust but verify"**: a three-column comparison (MTurk, trained annotators, ChatGPT) with Gilardi's numbers (4/5 tasks, $0.003), then the JUDGE-BENCH caveat. A routing diagram sends low-confidence items to humans.
4. **"Confident learning in 4 steps"**: a confusion-style heatmap of the confident joint that fills cell by cell. Off-diagonal cells glow and become a ranked issue list. Code snippet on the side.
5. **"Data maps"**: a scatter of confidence vs variability with three colored regions. Clicking the hard-to-learn region shows mislabeled examples.
6. **"Active learning loop"**: a circular animation (train → score → select → label). Side-by-side 2-D pool showing uncertainty-only (clumped picks) vs BADGE/core-set (spread picks).
7. **"Snorkel: many weak voters → one label"**: an LF matrix (rows = examples, columns = LFs, cells colored by vote or abstain) collapses into probabilistic labels through the LabelModel.
8. **"Leakage gallery"**: three panels (patient appears in both splits → GroupKFold; future features → TimeSeriesSplit with gap; scaler fit on all data → Pipeline). Each shows the "before/after" CV score drop.
9. **"MinHash LSH in one picture"**: shingles → signatures → bands → buckets, with an interactive S-curve plot of 1 − (1 − s^r)^b as b and r change.
10. **"Is your benchmark in the training set?"**: GSM8k vs GSM1k bars per model family (up to −8%), the Min-K% token-probability strip, and a LiveCodeBench timeline with the model cutoff line.

---

## 14. Source list
- Northcutt et al. 2021, Pervasive Label Errors: https://arxiv.org/abs/2103.14749 · https://labelerrors.com
- Northcutt et al. 2021, Confident Learning (JAIR): https://arxiv.org/abs/1911.00068
- cleanlab docs (2.9.0): https://docs.cleanlab.ai/stable/tutorials/indepth_overview.html · https://github.com/cleanlab/cleanlab
- Swayamdipta et al. 2020, Dataset Cartography: https://arxiv.org/abs/2009.10795 · https://github.com/allenai/cartography
- Gilardi et al. 2023 (PNAS): https://arxiv.org/abs/2303.15056
- Zheng et al. 2023, MT-Bench / LLM-as-a-Judge: https://arxiv.org/abs/2306.05685
- Bavaresco et al. 2024/2025, JUDGE-BENCH: https://arxiv.org/abs/2406.18403
- Ash et al. 2020, BADGE: https://arxiv.org/abs/1906.03671 · https://github.com/JordanAsh/badge
- Sener & Savarese 2018, Core-Set: https://arxiv.org/abs/1708.00489
- Ratner et al. 2017, Snorkel: https://arxiv.org/abs/1711.10160 · https://github.com/snorkel-team/snorkel-tutorials
- Argilla docs: https://docs.argilla.io/latest/ · Label Studio: https://labelstud.io
- scikit-learn cross-validation guide: https://scikit-learn.org/stable/modules/cross_validation.html
- statsmodels fleiss_kappa: https://www.statsmodels.org/stable/generated/statsmodels.stats.inter_rater.fleiss_kappa.html
- krippendorff (PyPI): https://pypi.org/project/krippendorff/
- datasketch LSH: https://ekzhu.com/datasketch/lsh.html
- Lee et al. 2022, Deduplicating Training Data: https://arxiv.org/abs/2107.06499
- Kapoor & Narayanan 2022, Leakage: https://arxiv.org/abs/2207.07048
- Sainz et al. 2023, NLP Evaluation in trouble: https://arxiv.org/abs/2310.18018
- Zhang et al. 2024, GSM1k: https://arxiv.org/abs/2405.00332
- Shi et al. 2023, Min-K% Prob: https://arxiv.org/abs/2310.16789
- Jain et al. 2024, LiveCodeBench: https://arxiv.org/abs/2403.07974
