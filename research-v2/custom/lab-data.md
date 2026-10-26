# Hands-on labs: data quality in code (October 2026)

Subtopic: dataset contracts (pandera), drift (PSI/KS, Evidently), label noise (cleanlab), annotator agreement (Cohen, Fleiss, Krippendorff), active learning, leakage-safe splits (GroupKFold, TimeSeriesSplit), near-duplicate dedup (datasketch MinHash LSH).

This file builds on `research-custom/04-dataset-design-contracts.md` and `05-labels-noise-active.md`. Those files cover the theory: PSI/KS/JS formulas, Landis-Koch bands, confident learning, and tool matrices. This file covers only runnable labs, gotchas found in real runs, and arXiv insights from 2026-07-23 to 2026-10-23.

---

## 0. Versions and how these labs were checked

### 0.1 Current versions (PyPI JSON, fetched 2026-10-23)

| Package | Latest | Uploaded | Requires-Python | Note |
|---|---|---|---|---|
| pandera | **0.34.1** | 2026-10-06 | >=3.10 | Install the **`pandera[pandas]`** extra. The base wheel does not depend on pandas (METADATA: `pandas>=2.1.1; extra == "pandas"`). |
| evidently | **0.7.23** | 2026-09-11 | >=3.10 | Heavy dependencies (litestar, msgspec, plotly<6, statsmodels) |
| cleanlab | **2.9.0** | 2026-01-13 | >=3.10 | |
| scikit-learn | **1.9.1** | 2026-09-10 | >=3.11 | |
| datasketch | **2.0.0** | 2026-07-05 | >=3.9 | **New default MinHash permutation scheme**, see Lab 8 |
| krippendorff | **0.9.0** | 2026-10-07 | >=3.11 | |
| statsmodels | **0.15.0** | 2026-08-27 | >=3.10 | |
| scipy | 1.18.1 | 2026-08-21 | >=3.12 | |
| numpy | 2.5.4 | 2026-10-10 | >=3.12 | |
| pandas | 3.1.0 | **2026-10-22** (yesterday) | >=3.11 | Too new for any library here to have been tested on it. Pin `pandas>=3.0,<3.1` or `2.3.*` for class. |
| scikit-activeml | 1.0.1 | 2026-10-15 | | Maintained active-learning library |
| modAL-python | 0.4.2.1 | **2023-06-01** | | Stale. Do not teach it as current. |
| small-text | 1.4.1 | 2024-08-18 | | |

Recommended class environment (Python 3.12):
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install "numpy==2.5.4" "pandas==3.0.*" "scipy==1.18.1" "scikit-learn==1.9.1" \
            "pandera[pandas]==0.34.1" "evidently==0.7.23" "cleanlab==2.9.0" \
            "datasketch==2.0.0" "krippendorff==0.9.0" "statsmodels==0.15.0"
```
No lab needs an API key or env vars. Every dataset is synthetic and generated inside the script, so the labs run offline.

### 0.2 How each lab was verified
- **Every lab below was actually run** on 2026-10-23, so the "Expected output" blocks are **captured output, not illustrations**. pip was blocked on this machine, so I downloaded the **latest PyPI wheels** of pandera 0.34.1, evidently 0.7.23, cleanlab 2.9.0, datasketch 2.0.0 and krippendorff 0.9.0, extracted them, put them on `sys.path`, and read their source.
- The base stack was **older than the pinned versions**: numpy 1.26.4, pandas 2.1.4, scikit-learn 1.8.0, scipy 1.11.4, statsmodels 0.14.6. scikit-learn 1.9.1 and statsmodels 0.15.0 signatures were checked against GitHub source at the release tags. With the newer pins, numbers can differ in the 3rd decimal place **[UNVERIFIED on numpy 2.5 / pandas 3.x]**.
- Source citations give the file path inside the released wheel and the line number in that release. The GitHub repos are unionai-oss/pandera, evidentlyai/evidently (`src/evidently/...`), cleanlab/cleanlab, ekzhu/datasketch and pln-fing-udelar/fast-krippendorff. Line numbers can drift on `main`.

---

## Lab 1: Insurance-claims intake contract with pandera

> **Verifier (2026-10-23):** VERIFIED against pandera 0.34.1 source (`pandera.pandas` exports `DataFrameModel`, `Field`, `dataframe_check`). Captured run by the original author.

**Goal.** Reject or quarantine a bad nightly batch of claims *before* it reaches the fraud-model training table. Collect **all** failures in one pass so the data owner receives one complete report.

**Adapted from.** "DataFrame Models - pandera documentation" https://pandera.readthedocs.io/en/stable/dataframe_models.html and "Lazy Validation - pandera documentation" https://pandera.readthedocs.io/en/stable/lazy_validation.html.

**Prerequisites.** `pip install "pandera[pandas]==0.34.1" "pandas==3.0.*"`. No env vars.

**Code: `lab1_claims_contract.py`**
```python
"""Lab 1 - Insurance-claims intake contract with pandera 0.34.1."""
import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaErrors
from pandera.typing import Series

class ClaimsContract(pa.DataFrameModel):
    claim_id: Series[str] = pa.Field(unique=True, str_matches=r"^CLM-\d{6}$")
    policy_id: Series[str] = pa.Field(str_length={"min_value": 8, "max_value": 8})
    claim_type: Series[str] = pa.Field(isin=["auto", "home", "travel", "health"])
    amount_usd: Series[float] = pa.Field(gt=0, le=250_000)
    incident_date: Series[pd.Timestamp] = pa.Field()
    reported_date: Series[pd.Timestamp] = pa.Field()
    adjuster_note: Series[str] = pa.Field(nullable=True)

    @pa.dataframe_check(error="reported_date must be on/after incident_date")
    def reported_after_incident(cls, df: pd.DataFrame) -> Series[bool]:
        return df["reported_date"] >= df["incident_date"]

    class Config:
        strict = True    # unknown columns fail the contract
        coerce = True    # cast "1200" -> 1200.0 and ISO strings -> Timestamp

batch = pd.DataFrame({
    "claim_id": ["CLM-000101", "CLM-000102", "CLM-000102", "CLM-77"],
    "policy_id": ["POL12345", "POL12346", "POL12346", "POL1"],
    "claim_type": ["auto", "home", "home", "boat"],
    "amount_usd": ["1200.50", "98000", "98000", "-5"],
    "incident_date": ["2026-10-01", "2026-10-03", "2026-10-03", "2026-10-09"],
    "reported_date": ["2026-10-02", "2026-10-04", "2026-10-04", "2026-10-08"],
    "adjuster_note": [None, "roof damage", "roof damage", None],
})

try:
    ClaimsContract.validate(batch, lazy=True)   # collect ALL failures, not just the first
except SchemaErrors as exc:
    fc = exc.failure_cases
    print(f"{len(fc)} failure cases")
    print(fc[["column", "check", "index", "failure_case"]].to_string(index=False))
    bad_rows = set(fc["index"].dropna().astype(int))
    clean = batch.drop(index=list(bad_rows))
    print("quarantined rows:", sorted(bad_rows), "| clean rows kept:", len(clean))
```

**Run.** `python lab1_claims_contract.py`

**Expected output (captured run)**
```
12 failure cases
       column                                        check  index        failure_case
     claim_id reported_date must be on/after incident_date      3              CLM-77
    policy_id reported_date must be on/after incident_date      3                POL1
   claim_type reported_date must be on/after incident_date      3                boat
   amount_usd reported_date must be on/after incident_date      3                -5.0
incident_date reported_date must be on/after incident_date      3 2026-10-09 00:00:00
reported_date reported_date must be on/after incident_date      3 2026-10-08 00:00:00
     claim_id                             field_uniqueness      1          CLM-000102
     claim_id                             field_uniqueness      2          CLM-000102
     claim_id                   str_matches('^CLM-\d{6}$')      3              CLM-77
    policy_id                             str_length(8, 8)      3                POL1
   claim_type   isin(['auto', 'home', 'travel', 'health'])      3                boat
   amount_usd                              greater_than(0)      3                -5.0
quarantined rows: [1, 2, 3] | clean rows kept: 1
```

**Walk-through of the key lines**
1. `import pandera.pandas as pa`: this is the backend-specific import. Importing pandas classes from top-level `pandera` still works, but in 0.34.1 it emits `FutureWarning: Importing pandas-specific classes and functions from the top-level pandera module will be **removed in a future version of pandera**` (seen in the run; source `pandera/_pandas_deprecated.py:144`).
2. `pa.Field(unique=True, str_matches=..., str_length={...}, isin=..., gt=0, le=...)`: all of these are keyword arguments of `Field` (`pandera/api/dataframe/model_components.py:128`, with params `ge/le/in_range/isin/str_length/str_matches/nullable/unique/coerce`).
3. `@pa.dataframe_check(error=...)`: a row-wise, cross-column rule. When it fails, pandera reports **every column of the failing row** (6 of the 12 failure cases). Remember this when you count errors. Source: `model_components.py:391`.
4. `Config.strict = True` / `coerce = True`: strict rejects unknown columns, and coerce casts strings to float or Timestamp before the checks run. The Config fields live in `pandera/api/dataframe/model_config.py`, which also has `drop_invalid_rows`, `unique` and `add_missing_columns`.
5. `validate(batch, lazy=True)` + `SchemaErrors.failure_cases`: lazy mode collects every failure into a DataFrame with columns `schema_context, column, check, check_number, failure_case, index` (`pandera/errors.py:165`).
6. `unique=True` flags **both** copies of a duplicate (rows 1 and 2), not only the second one. Quarantine logic must keep one copy on purpose.

**Common errors (exact messages from the run)**
- Without `lazy=True`, the first failure stops validation: `pandera.errors.SchemaError: series 'claim_id' contains duplicate values:` followed by the rows. Fix: pass `lazy=True` in pipelines.
- An upstream team adds a column: `SchemaErrors ... "COLUMN_NOT_IN_SCHEMA" ... "error": "column 'extra_col' not in DataFrameSchema {...}"`. Fix: version the contract. Add the column to the model, or set `strict="filter"` to drop unknown columns on purpose.
- A required column is missing: `SchemaError: column 'adjuster_note' not in dataframe. Columns in dataframe: [...]`. Fix: send the batch back to the producer, or set `add_missing_columns=True` in Config when the column is nullable.
- `pip install pandera==0.34.1` followed by `import pandera.pandas` fails with a missing-pandas error in a clean venv. Fix: install the extra, `pandera[pandas]`.

**Best practice.** Store the contract class in the **producer's** repo and run it in CI on a sample batch. The training job then imports the same class, so there is one definition and two enforcement points. Alert on *new* failure types, not on failure counts.

**Variation.** Set `drop_invalid_rows = True` in `Config` and call `validate(batch, lazy=True)`. pandera then returns only the valid rows instead of raising. Write the dropped rows to a `quarantine/` table with the `failure_cases` frame attached.

---

## Lab 2: PSI + KS drift monitor for a refund agent's request features (numpy/scipy only)

> **Verifier (2026-10-23):** VERIFIED: re-run by the verifier (numpy 1.26 / scipy 1.11); output identical to the file.

**Goal.** Compute PSI and two-sample KS by hand on three features of a refund agent's traffic, September (reference) versus October (current). Show why a p-value test and a distance threshold disagree at large n.

**Adapted from.** The PSI definition in `research-custom/04` §6.1 and `scipy.stats.ks_2samp` (SciPy reference). No library magic: this is what Evidently's `psi` and `ks` compute internally.

**Prerequisites.** `pip install "numpy==2.5.4" "scipy==1.18.1"`.

**Code: `lab2_psi_ks.py`**
```python
"""Lab 2 - PSI + KS drift monitor for a refund-agent's request features (numpy/scipy only)."""
import numpy as np
from scipy.stats import ks_2samp

def psi(reference, current, n_bins=10, eps=1e-4):
    """Population Stability Index with quantile bins fixed on the REFERENCE window."""
    edges = np.quantile(reference, np.linspace(0, 1, n_bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf          # catch out-of-range current values
    edges = np.unique(edges)                       # ties (e.g. many zeros) collapse bins
    ref_share = np.histogram(reference, edges)[0] / len(reference)
    cur_share = np.histogram(current, edges)[0] / len(current)
    ref_share, cur_share = np.clip(ref_share, eps, None), np.clip(cur_share, eps, None)
    return float(np.sum((cur_share - ref_share) * np.log(cur_share / ref_share)))

def verdict(value):
    return "stable" if value < 0.1 else ("moderate" if value < 0.25 else "MAJOR")

rng = np.random.default_rng(7)
# Reference: September refund requests. Current: October, after a holiday promo.
reference = {
    "refund_amount_usd": rng.lognormal(mean=3.6, sigma=0.6, size=20_000),
    "days_since_order":  rng.gamma(shape=2.0, scale=6.0, size=20_000),
    "items_in_order":    rng.poisson(lam=2.0, size=20_000).astype(float),
}
current = {
    "refund_amount_usd": rng.lognormal(mean=3.9, sigma=0.7, size=5_000),   # real shift
    "days_since_order":  rng.gamma(shape=2.0, scale=6.2, size=5_000),      # tiny shift
    "items_in_order":    rng.poisson(lam=2.0, size=5_000).astype(float),   # no shift
}

print(f"{'feature':<20}{'PSI':>8}  {'verdict':<9}{'KS D':>7}{'KS p':>11}")
for col in reference:
    p = psi(reference[col], current[col])
    ks = ks_2samp(reference[col], current[col])
    print(f"{col:<20}{p:>8.3f}  {verdict(p):<9}{ks.statistic:>7.3f}{ks.pvalue:>11.2e}")
```

**Run.** `python lab2_psi_ks.py`

**Expected output (captured run)**
```
feature                  PSI  verdict     KS D       KS p
refund_amount_usd      0.243  moderate   0.205  5.91e-148
days_since_order       0.003  stable     0.024   2.16e-02
items_in_order         0.001  stable     0.013   4.99e-01
```

**Walk-through**
1. `edges = np.quantile(reference, ...)`: fix the bins on the **reference** window only. If you re-bin on each new window, PSI values from different weeks cannot be compared.
2. `edges[0], edges[-1] = -np.inf, np.inf`: without this, October refunds above September's maximum fall outside all bins, and that tail shift becomes invisible.
3. `edges = np.unique(edges)`: discrete or zero-inflated features (`items_in_order`) produce duplicate quantiles. Without `unique`, empty zero-width bins appear.
4. `np.clip(..., eps, None)`: an empty bin gives `log(0)` = `-inf`. The eps value changes PSI noticeably for sparse bins, so record it in the monitor config.
5. Read row 2: `days_since_order` has **PSI 0.003 (stable)** but **KS p = 0.02**. With an alpha of 0.05, the KS test calls it "drift". At n = 20k/5k a p-value test flags shifts too small to matter. This is why Evidently switches to distance metrics for numeric columns when n > 1000 (`research-custom/04` §6.2).

**Common errors**
- `RuntimeWarning: divide by zero encountered in divide` and PSI = `inf` (checked with a share vector that contains 0). Cause: a bin with 0 current or 0 reference rows. Fix: the `np.clip` epsilon line, or merge sparse bins.
- ``ValueError: `bins` must increase monotonically, when an array`` from `np.histogram` (checked). Cause: hand-written or business-defined bin edges that are not sorted, or that repeat. Fix: `edges = np.unique(edges)`, which sorts and de-duplicates. For a constant feature, the edges collapse to ±inf only, so skip it or test it with an exact-match rule.
- PSI that is unstable from week to week on small windows: with 10 bins and < 500 rows, the sampling noise alone reaches about 0.05. Fix: set a minimum window size, or bootstrap a null PSI from two reference halves.

**Best practice.** Calibrate the thresholds on **reference vs. reference** (split September in two). The 0.1/0.25 PSI bands are a credit-risk convention, not a law (see `research-custom/04` §6.1). Whether a shift matters is a business decision: refund amount drift changes the payout, item count drift may not.

**Variation.** Compute PSI on LLM-traffic **descriptors** instead of raw features. Good descriptors are prompt length, a language-ID share, a retrieval hit-rate, and the refusal rate. For unstructured streams, see the e-detector paper in §9: its calibration sets are as small as m = 30.

---

## Lab 3: Weekly drift report and CI gate for a support-ticket triage model (Evidently)

> **Verifier (2026-10-23):** VERIFIED against evidently 0.7.23 source (`from evidently import DataDefinition, Dataset, Report`, `evidently.metrics.ValueDrift`, `DataDriftPreset(num_method, drift_share=0.5, include_tests=True)`, `Report(include_tests=False)` default).

**Goal.** Compare this week's support tickets with last month's, write an HTML report for humans, and **exit non-zero** in CI when a drift test fails, so a retraining or labeling job is held.

**Adapted from.** "Data and ML checks - Documentation" https://docs.evidentlyai.com/quickstart_ml and "Customize Data Drift - Documentation" https://docs.evidentlyai.com/metrics/customize_data_drift.

**Prerequisites.** `pip install "evidently==0.7.23" "pandas==3.0.*"`.

**Code: `lab3_evidently_tickets.py`**
```python
"""Lab 3 - Weekly drift report + CI gate for a support-ticket triage model (evidently 0.7.23)."""
import sys
import numpy as np
import pandas as pd
from evidently import DataDefinition, Dataset, Report
from evidently.metrics import ValueDrift
from evidently.presets import DataDriftPreset

rng = np.random.default_rng(42)

def make_tickets(n, outage_share):
    channel = rng.choice(["email", "chat", "phone"], size=n, p=[0.5, 0.4, 0.1])
    product = rng.choice(["billing", "login", "outage", "shipping"], size=n,
                         p=[0.35, 0.30 - outage_share / 2, outage_share, 0.35 - outage_share / 2])
    return pd.DataFrame({
        "channel": channel,
        "product_area": product,
        "body_chars": rng.lognormal(5.5, 0.5, n).round(),
        "customer_tenure_days": rng.gamma(2.0, 200.0, n).round(),
    })

reference = make_tickets(4_000, outage_share=0.05)   # last month
current = make_tickets(1_500, outage_share=0.25)     # this week: login outage

schema = DataDefinition(numerical_columns=["body_chars", "customer_tenure_days"],
                        categorical_columns=["channel", "product_area"])
ref_ds = Dataset.from_pandas(reference, data_definition=schema)
cur_ds = Dataset.from_pandas(current, data_definition=schema)

report = Report([
    DataDriftPreset(num_method="psi", num_threshold=0.2, drift_share=0.5),
    ValueDrift(column="customer_tenure_days", method="ks", threshold=0.05),  # p-value test
], include_tests=True)
snapshot = report.run(current_data=cur_ds, reference_data=ref_ds)
snapshot.save_html("ticket_drift_report.html")

result = snapshot.dict()
for m in result["metrics"]:
    print(f"{m['metric_name'][:60]:<62} {m['value']}")
failed = [t for t in result["tests"] if t["status"] == "FAIL"]
print(f"tests: {len(result['tests'])}, failed: {len(failed)}")
for t in failed:
    print("FAIL:", t["name"], "-", t["description"][:90])
sys.exit(1 if failed else 0)   # non-zero exit blocks the retraining job in CI
```

**Run.** `python lab3_evidently_tickets.py; echo "exit code: $?"`, then open `ticket_drift_report.html` (about 3.8 MB, because it embeds plotly).

**Expected output (captured run, exit code 1)**
```
DriftedColumnsCount(drift_share=0.5,num_method=psi,num_thres   {'count': 1.0, 'share': 0.25}
ValueDrift(column=body_chars,method=psi,threshold=0.2)         0.00864067267465683
ValueDrift(column=customer_tenure_days,method=psi,threshold=   0.012513760650011765
ValueDrift(column=channel,method=Jensen-Shannon distance,thr   0.0182178544907071
ValueDrift(column=product_area,method=Jensen-Shannon distanc   0.20686265028221704
ValueDrift(column=customer_tenure_days,method=ks,threshold=0   0.5709138235382716
tests: 6, failed: 1
FAIL: Value Drift for column product_area - Drift score is 0.21. The drift detection method is Jensen-Shannon distance. The drift thre
```

**Walk-through**
1. `from evidently import DataDefinition, Dataset, Report`: the 0.7.x API. `DataDefinition` takes `numerical_columns`, `categorical_columns`, `text_columns`, `timestamp` and `id_column` (`evidently/core/datasets.py:367`). `Dataset.from_pandas(data, data_definition=...)` is at `datasets.py:1243`.
2. `DataDriftPreset(num_method="psi", num_threshold=0.2, drift_share=0.5)`: the preset accepts `method, cat_method, num_method, text_method, per_column_method, threshold, cat_threshold, num_threshold, per_column_threshold, drift_share=0.5, include_tests=True` (`evidently/presets/drift.py:64-81`). Categorical columns kept the automatic choice, which was **Jensen-Shannon distance** for n > 1000, as the output shows.
3. `Report([...], include_tests=True)`: `Report.__init__` defaults to `include_tests=False` (`core/report.py`, class at line 821). Without this argument, no pass/fail tests are produced, and the CI gate never fails.
4. `report.run(current_data=..., reference_data=...)` returns a **Snapshot** (`core/report.py:904`). The `Report` object itself holds no results.
5. `snapshot.dict()` returns `{"metrics": [...], "tests": [...]}` (`core/report.py:769`). Each metric has the keys `id, metric_name, config, value`, and each test has `name, description, status ("SUCCESS"/"FAIL"), ...`. There is **no `metric_id` key** on metrics: my first draft used it and got `KeyError: 'metric_id'`.
6. **Key insight from the output:** `DriftedColumnsCount` share = 0.25, which is below `drift_share` = 0.5, so the *dataset-level* drift test passes. The business-critical column `product_area` drifted (JS 0.21) and only its column test failed. A gate that reads only "dataset drift: yes/no" would have missed a login outage.
7. The extra KS metric returned **0.571**. For `ks`, the value is a **p-value**, where low means drift. For `psi` or JS, the value is a **distance**, where high means drift. Do not put both on one dashboard axis.

**Common errors (exact messages)**
- Legacy tutorial code fails: `ModuleNotFoundError: No module named 'evidently.report'` and `ModuleNotFoundError: No module named 'evidently.metric_preset'`. Fix: use the 0.7 imports above. The old API lives under `evidently.legacy.*`.
- No reference dataset: `ValueError: Reference dataset should be present`. Fix: pass `reference_data`, because drift is always relative.
- `KeyError: 'metric_id'` when you parse `snapshot.dict()`. Fix: use `metric_name` or `id`.
- Importing evidently prints `CryptographyDeprecationWarning: TripleDES has been moved...`. This came from paramiko in my environment, not from evidently. It is harmless.

**Best practice.** Put **per-column tests on the 3-5 columns the business cares about** (here `product_area`) in addition to the preset. Do not rely on `drift_share`. Save `snapshot.json()` next to the model version so a drift alert can be traced to the data that caused it.

**Variation.** Add `text_columns=["body"]` to the `DataDefinition` with raw ticket text, so Evidently applies its text-drift method. Or set `embeddings=` with `embeddings_drift_method=` on the preset (params at `presets/drift.py:67-68`) for embedding drift on ticket vectors **[embedding path not run in this session]**.

---

## Lab 4: Find mislabeled support tickets with cleanlab `find_label_issues`

> **Verifier (2026-10-23):** VERIFIED against cleanlab 2.9.0 source (`find_label_issues` keyword-only signature, `n_jobs=None`).

**Goal.** A labeling vendor tagged 3,000 tickets (billing / login / outage / shipping), and about 8% are wrong. Rank the suspicious labels so a team lead re-reviews 200 tickets instead of 3,000.

**Adapted from.** "Text Classification with Noisy Labels - cleanlab" https://docs.cleanlab.ai/stable/tutorials/clean_learning/text.html and "The Workflows of Data-centric AI for Classification with Noisy Labels - cleanlab" https://docs.cleanlab.ai/stable/tutorials/indepth_overview.html.

**Prerequisites.** `pip install "cleanlab==2.9.0" "scikit-learn==1.9.1"`. Save this helper next to the lab:

**`tickets.py` (shared synthetic corpus)**
```python
"""Shared synthetic support-ticket corpus used by Labs 4 and 6."""
import numpy as np

TEMPLATES = {
    "billing":  ["I was charged twice for order {n}", "refund the duplicate charge on my card",
                 "my invoice {n} shows the wrong amount", "why did my subscription price go up"],
    "login":    ["cannot log in, password reset email never arrives", "2FA code rejected on login",
                 "account locked after {n} attempts", "SSO login loops back to the sign-in page"],
    "shipping": ["package {n} has not arrived yet", "tracking says delivered but nothing here",
                 "wrong address on shipment {n}", "parcel arrived damaged, box crushed"],
    "outage":   ["app shows error 503 since this morning", "dashboard will not load for whole team",
                 "API returns timeouts in region eu-west", "service down, status page says ok"],
}
FILLER = ["please help", "this is urgent", "thanks", "second time asking", "", "asap"]

def make_tickets(n, seed=0):
    rng = np.random.default_rng(seed)
    classes = sorted(TEMPLATES)                      # alphabetical = cleanlab column order
    y = rng.integers(0, len(classes), n)
    texts = [f"{rng.choice(TEMPLATES[classes[k]]).format(n=rng.integers(100, 999))} "
             f"{rng.choice(FILLER)}" for k in y]
    return texts, y, classes
```

**Code: `lab4_cleanlab_tickets.py`**
```python
"""Lab 4 - Find mislabeled support tickets with cleanlab 2.9.0 confident learning."""
import numpy as np
from cleanlab.filter import find_label_issues
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from tickets import make_tickets

texts, true_y, classes = make_tickets(3_000, seed=1)

# Simulate a rushed BPO labeling vendor: 8% of labels flipped to a random other class.
rng = np.random.default_rng(2)
noisy_y = true_y.copy()
flip = rng.random(len(true_y)) < 0.08
noisy_y[flip] = (true_y[flip] + rng.integers(1, len(classes), flip.sum())) % len(classes)

model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2),
                      LogisticRegression(max_iter=2_000))
# Out-of-sample probabilities: every row is scored by a model that never saw it.
pred_probs = cross_val_predict(model, texts, noisy_y, method="predict_proba",
                               cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=0))

ranked = find_label_issues(labels=noisy_y, pred_probs=pred_probs,
                           return_indices_ranked_by="self_confidence",
                           n_jobs=1)   # Windows/macOS + notebooks: avoid spawn hangs
truly_wrong = set(np.flatnonzero(flip))
hits = len(truly_wrong & set(ranked))
print(f"flipped labels: {len(truly_wrong)}   flagged by cleanlab: {len(ranked)}")
print(f"precision: {hits / len(ranked):.2f}   recall: {hits / len(truly_wrong):.2f}")
print("\nTop 5 for human review:")
for i in ranked[:5]:
    print(f"  #{i:<5} given={classes[noisy_y[i]]:<9} suggested={classes[pred_probs[i].argmax()]:<9}"
          f" p(given)={pred_probs[i, noisy_y[i]]:.2f}  '{texts[i][:48]}'")
```

**Run.** `python lab4_cleanlab_tickets.py` (about 7 s).

**Expected output (captured run)**
```
flipped labels: 225   flagged by cleanlab: 223
precision: 1.00   recall: 0.99

Top 5 for human review:
  #2195  given=outage    suggested=login     p(given)=0.01  'account locked after 417 attempts '
  #2859  given=outage    suggested=shipping  p(given)=0.01  'package 216 has not arrived yet '
  #408   given=billing   suggested=login     p(given)=0.01  'account locked after 324 attempts asap'
  #2060  given=shipping  suggested=login     p(given)=0.01  'account locked after 575 attempts please help'
  #1962  given=shipping  suggested=login     p(given)=0.01  'account locked after 979 attempts please help'
```
Note: precision and recall are near-perfect only because the templates separate cleanly. On real tickets, expect much lower numbers, and treat the ranked list as a **review queue, not an auto-delete list** (see the Google Play paper in §9).

**Walk-through**
1. `cross_val_predict(..., method="predict_proba", cv=StratifiedKFold(...))`: `pred_probs` **must be out-of-sample**. In-sample probabilities have memorized the noisy labels, so cleanlab finds almost nothing.
2. `classes = sorted(TEMPLATES)` with labels as ints 0..K-1: column j of `pred_probs` must be class j. sklearn orders `classes_` by sorted label value, and cleanlab assumes the same order.
3. `find_label_issues(labels, pred_probs, *, return_indices_ranked_by=None, filter_by="prune_by_noise_rate", frac_noise=1.0, ..., n_jobs=None, ...)` is at `cleanlab/filter.py:57-71`. With `return_indices_ranked_by` set, it returns **indices sorted by severity** instead of a boolean mask. The options are `self_confidence`, `normalized_margin` and `confidence_weighted_entropy`.
4. `n_jobs=1`: `n_jobs=None` means "one process per physical core" (`filter.py:260-278`). See the first common error below for what happens on Windows.
5. `frac_noise` (default 1.0): lower it, for example to 0.5, to return only the most confident half of the issues when the review budget is small.

**Common errors (exact messages)**
- **Windows/macOS, script without an `if __name__ == "__main__":` guard, default `n_jobs`:** the run printed `RuntimeError: An attempt has been made to start a new process before the current process has finished its bootstrapping phase. ... The "freeze_support()" line can be omitted if the program is not going to be frozen` 77 times and then **hung** (killed after 100 s). Fix: `n_jobs=1`, or wrap the script body in `if __name__ == "__main__":`. The cleanlab docstring also says: *"Windows users may see a speed-up with n_jobs=1"* (`filter.py:177`).
- String labels: `ValueError: Labels cannot be strings, they must be zero-indexed integers corresponding to class indices.` Fix: `labels = np.searchsorted(classes, string_labels)` or a `LabelEncoder`.
- Raw scores or logits: `ValueError: Values in pred_probs must be between 0 and 1.` Fix: apply softmax, or use `predict_proba`.
- Class missing from the probabilities: `ValueError: pred_probs must have at least 3 columns, based on the largest class index which appears in labels.` Fix: make every fold see every class (StratifiedKFold), and keep the label encoding consistent.

**Best practice.** Run cleanlab with **two different model families**, for example TF-IDF+LR and a small sentence-embedding + LR model, and send the **intersection** to human review first. Log the reviewer's decision (fix label / keep / ambiguous / drop) back into the dataset card, because "ambiguous" items often mean the taxonomy itself needs work.

**Variation.** Replace `find_label_issues` with `cleanlab.Datalab(data=df, label_name="label").find_issues(pred_probs=pred_probs, features=emb)`. That checks label, outlier, near-duplicate and non-IID issues in one report **[Datalab path not run in this session]**. Or use `cleanlab.rank.get_label_quality_scores` (`cleanlab/rank.py:33`) to get a 0-1 score per row for a review UI.

---

## Lab 5: Is the HR-policy-search relevance rubric reliable? Cohen, Fleiss, Krippendorff

> **Verifier (2026-10-23):** VERIFIED against krippendorff 0.9.0 (`alpha(..., level_of_measurement="interval")` default) and statsmodels 0.15.0 (`aggregate_raters`, `fleiss_kappa(method="fleiss")`) source.

**Goal.** Three HR analysts and one LLM judge graded 12 (query, retrieved policy passage) pairs on a 0-3 relevance scale. Decide whether the rubric is reliable enough to build a RAG eval set, and whether the LLM judge can replace one human.

**Adapted from.** The scikit-learn `cohen_kappa_score` API docs, the statsmodels `fleiss_kappa` page (https://www.statsmodels.org/stable/generated/statsmodels.stats.inter_rater.fleiss_kappa.html), and the README of https://github.com/pln-fing-udelar/fast-krippendorff.

**Prerequisites.** `pip install "krippendorff==0.9.0" "statsmodels==0.15.0" "scikit-learn==1.9.1"`.

**Code: `lab5_agreement_hr.py`**
```python
"""Lab 5 - Is the HR-policy-search relevance rubric reliable? Cohen, Fleiss, Krippendorff."""
from itertools import combinations
import numpy as np
import krippendorff
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa

# 12 (query, retrieved HR-policy passage) pairs graded 0-3:
# 0 = irrelevant, 1 = related, 2 = partially answers, 3 = fully answers.
ratings = {                       # one row per rater, one column per item
    "ana":       [3, 2, 0, 1, 3, 2, 0, 3, 1, 2, 3, 0],
    "ben":       [3, 2, 0, 2, 3, 1, 0, 3, 1, 2, 2, 0],
    "chen":      [2, 2, 1, 1, 3, 2, 0, 3, 0, 2, 3, 1],
    "llm_judge": [3, 3, 1, 2, 3, 3, 1, 3, 2, 3, 3, 1],   # lenient grader
}
raters = list(ratings)
R = np.array([ratings[r] for r in raters])                # shape (raters, items)

print("Pairwise Cohen kappa   (unweighted | quadratic-weighted)")
for a, b in combinations(raters, 2):
    k = cohen_kappa_score(ratings[a], ratings[b])
    kw = cohen_kappa_score(ratings[a], ratings[b], weights="quadratic")
    print(f"  {a:>9} vs {b:<9} {k:6.3f} | {kw:6.3f}")

humans = R[:3]
table, _ = aggregate_raters(humans.T)                     # items x categories counts
print(f"\nFleiss kappa, 3 humans (nominal):      {fleiss_kappa(table, method='fleiss'):.3f}")

print(f"Krippendorff alpha, humans, nominal:   "
      f"{krippendorff.alpha(reliability_data=humans, level_of_measurement='nominal'):.3f}")
print(f"Krippendorff alpha, humans, ordinal:   "
      f"{krippendorff.alpha(reliability_data=humans, level_of_measurement='ordinal'):.3f}")
print(f"Krippendorff alpha, humans+LLM, ord.:  "
      f"{krippendorff.alpha(reliability_data=R.astype(float), level_of_measurement='ordinal'):.3f}")

# Real projects have gaps: Chen skipped items 4-7. Alpha handles np.nan, kappa cannot.
gappy = humans.astype(float)
gappy[2, 4:8] = np.nan
print(f"Krippendorff alpha, with missing:      "
      f"{krippendorff.alpha(reliability_data=gappy, level_of_measurement='ordinal'):.3f}")
```

**Run.** `python lab5_agreement_hr.py`

**Expected output (captured run)**
```
Pairwise Cohen kappa   (unweighted | quadratic-weighted)
        ana vs ben        0.664 |  0.905
        ana vs chen       0.556 |  0.864
        ana vs llm_judge  0.077 |  0.739
        ben vs chen       0.215 |  0.747
        ben vs llm_judge  0.119 |  0.637
       chen vs llm_judge  0.208 |  0.625

Fleiss kappa, 3 humans (nominal):      0.476
Krippendorff alpha, humans, nominal:   0.491
Krippendorff alpha, humans, ordinal:   0.852
Krippendorff alpha, humans+LLM, ord.:  0.755
Krippendorff alpha, with missing:      0.828
```

**Walk-through**
1. `cohen_kappa_score(a, b, weights="quadratic")`: on an **ordinal** scale, unweighted kappa treats 2-vs-3 as just as wrong as 0-vs-3. Ana and Ben go from 0.664 to 0.905 once near-misses get partial credit. Choose the weighting to match the scale, and report which one you used.
2. `aggregate_raters(humans.T)`: statsmodels expects **items × raters**, and returns an items × categories count table for `fleiss_kappa(table, method="fleiss")` (`statsmodels/stats/inter_rater.py:84,197` at tag v0.15.0). If you pass raters × items, it builds a wrong table **silently**.
3. `krippendorff.alpha(reliability_data=..., level_of_measurement=...)` takes **raters × items**, which is the *opposite* orientation from statsmodels. Signature: `alpha(reliability_data=None, value_counts=None, value_domain=None, level_of_measurement="interval", dtype=...)` (`krippendorff/krippendorff.py:265-271`).
4. **The default level is `"interval"`**, not nominal. In a test run on toy data, the same ratings gave alpha 0.868 (interval default) versus 0.500 (nominal). Always pass the level explicitly.
5. The humans have an ordinal alpha of 0.852, which is above Krippendorff's 0.800 "reliable" bar (see `research-custom/05` §2, wording [UNVERIFIED there]). Adding the lenient LLM judge drops alpha to 0.755. Kappa against every human is < 0.21 unweighted. Conclusion: the LLM judge is **biased upward by about one grade**. Calibrate it, or use it as a 4th opinion, but do not let it replace a human.
6. `np.nan` cells: alpha uses only pairable values, so a rater who skipped items 4-7 still contributes. Cohen and Fleiss need complete data.

**Common errors (exact messages)**
- String labels with an ordinal level: `ValueError: When using strings, an ordered value_domain is required for level_of_measurement other than 'nominal'.` Fix: pass `value_domain=["irrelevant","related","partial","full"]`, or map the strings to ints.
- Almost everything missing: `ValueError: There has to be at least one unit with values assigned by at least two coders.` Fix: check the matrix orientation (raters × items) and the overlap design.
- NaN in Cohen: `ValueError: Input y_true contains NaN.` Fix: drop the items that either rater skipped, or switch to Krippendorff.
- Interval used by mistake on nominal categories: no error at all, only an inflated alpha. Fix: pass `level_of_measurement="nominal"` explicitly in code review.

**Best practice.** Run an agreement pilot of 50-100 items with **≥ 3 raters** before any large labeling job. Report alpha with a bootstrap CI over items, and put "agreement level + level of measurement + rater pool" in the dataset card. If alpha is low, fix the **rubric and examples**. The Agreement-Without-Alignment paper (§9) shows that LLM judges can be made to agree with *each other* without agreeing more with humans. Always keep a human anchor.

**Variation.** Bootstrap the CI: resample item columns 1,000 times with `rng.integers(0, n_items, n_items)`, compute alpha on each resample, and report the 2.5/97.5 percentiles. With 12 items the interval is very wide, which makes a good classroom point.

---

## Lab 6: Pool-based active learning: which insurance claims should senior adjusters label next?

> **Verifier (2026-10-23):** VERIFIED (plain scikit-learn API). skactiveml API in the variation remains UNVERIFIED.

**Goal.** Senior adjusters can label 100 claims per day as "needs adjuster" or "auto-approve". Compare **margin (uncertainty) sampling** with random sampling at an equal labeling budget.

**Adapted from.** The standard pool-based loop (Settles, *Active Learning Literature Survey*), written in plain scikit-learn so every step is visible. For production, use `scikit-activeml` 1.0.1 (released 2026-10-15, https://scikit-activeml.github.io/). `modAL` has had no release since 2023-06.

**Prerequisites.** `pip install "scikit-learn==1.9.1" "numpy==2.5.4"`.

**Code: `lab6_active_learning.py`**
```python
"""Lab 6 - Pool-based active learning: which insurance claims should senior adjusters label next?"""
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

# 20k unlabeled claims; ~10% truly need an adjuster (positive class).
X, y = make_classification(n_samples=20_000, n_features=30, n_informative=8,
                           weights=[0.9, 0.1], flip_y=0.02, class_sep=0.8, random_state=0)
X_pool, X_test, y_pool, y_test = train_test_split(X, y, test_size=0.25, stratify=y, random_state=0)

SEED_SIZE, BATCH, ROUNDS = 100, 100, 8      # adjuster time: 100 claims per day

def margin_scores(model, X_unlabeled):
    """Small gap between top-2 class probabilities = model is unsure."""
    p = np.sort(model.predict_proba(X_unlabeled), axis=1)
    return p[:, -1] - p[:, -2]

def run(strategy, seed=0):
    rng = np.random.default_rng(seed)
    labeled = rng.choice(len(X_pool), SEED_SIZE, replace=False)
    curve = []
    for _ in range(ROUNDS + 1):
        model = LogisticRegression(max_iter=1_000, class_weight="balanced")
        model.fit(X_pool[labeled], y_pool[labeled])           # y_pool = the adjuster's answers
        curve.append(average_precision_score(y_test, model.predict_proba(X_test)[:, 1]))
        unlabeled = np.setdiff1d(np.arange(len(X_pool)), labeled)
        if strategy == "margin":
            pick = unlabeled[np.argsort(margin_scores(model, X_pool[unlabeled]))[:BATCH]]
        else:
            pick = rng.choice(unlabeled, BATCH, replace=False)
        labeled = np.concatenate([labeled, pick])
    return np.array(curve)

rand = np.mean([run("random", s) for s in range(5)], axis=0)
marg = np.mean([run("margin", s) for s in range(5)], axis=0)
print(f"{'labels':>7} {'random PR-AUC':>14} {'margin PR-AUC':>14}")
for r, (a, b) in enumerate(zip(rand, marg)):
    print(f"{SEED_SIZE + r * BATCH:>7} {a:>14.3f} {b:>14.3f}")
```

**Run.** `python lab6_active_learning.py` (about 7 s).

**Expected output (captured run, mean of 5 seeds)**
```
 labels  random PR-AUC  margin PR-AUC
    100          0.546          0.546
    200          0.548          0.599
    300          0.570          0.620
    400          0.587          0.633
    500          0.605          0.643
    600          0.606          0.646
    700          0.615          0.652
    800          0.620          0.657
    900          0.622          0.659
```
Reading: margin sampling reaches random's 900-label PR-AUC (0.622) with about **300 labels**, roughly 3× less adjuster time on this synthetic task.

**Walk-through**
1. `margin_scores`: margin = p(top-1) − p(top-2). Pick the smallest margins. For binary tasks this equals picking scores closest to 0.5, but the same code also works for K classes.
2. `class_weight="balanced"`: with 10% positives and 100 seed labels you have about 10 positive examples. Without balancing, the first models predict "auto-approve" for everything, and uncertainty sampling becomes meaningless.
3. `average_precision_score` on a **fixed held-out test set** that is never in the pool: when you evaluate an AL run on the queried items, the estimate is biased, because those items are hard by construction.
4. `np.mean([...] for s in range(5))`: AL curves are noisy, so always average several seeds before you claim a gain.
5. Retraining from scratch every round (`model = LogisticRegression(...)` inside the loop) keeps the comparison fair and avoids warm-start artifacts.

**Common errors**
- `ValueError: This solver needs samples of at least 2 classes in the data, but the data contains only one class: 0` (with float labels it prints `0.0`). Cause: the random seed set has no positives (likely when prevalence is < 2%). Fix: seed with a stratified sample, or add a few known positives from rules.
- Margin sampling *underperforms* random after a few rounds. Cause: the batch holds 100 near-identical borderline claims (redundancy), or the classes are in heavy label noise (uncertainty sampling then queries the noise). Fix: use diversity-aware batching, such as k-means on the candidate top-1,000 margins, then take 1 per cluster. Alternatively, cap queries per customer or segment.
- **Sampling bias in the final dataset.** AL-selected data is not i.i.d., so a model trained only on it reports miscalibrated probabilities. Fix: keep a random 10-20% slice of every batch. This also gives you an unbiased estimate of prevalence.

**Best practice.** Mix exploration and exploitation in every batch (for example 80 margin + 20 random). Record **why** each item was queried (`strategy`, `round`, `score`) in the label store, so the dataset card can state the selection process.

**Variation.** For LLM fine-tuning data, use embeddings from the model being tuned and **hidden-state** or training-dynamics scores instead of margin. Hidden Cartographer (arXiv 2610.25215, §9) reports annotating only 20-30% of the pool and fine-tuning on 10-15% under dual budgets. Swap `LogisticRegression` for `skactiveml`'s `SklearnClassifier` + `UncertaintySampling` **[skactiveml API not verified from source in this session]**.

---

## Lab 7: Leakage-safe validation for a refund-fraud model with GroupKFold and TimeSeriesSplit

> **Verifier (2026-10-23):** VERIFIED against scikit-learn 1.9.1 source (`GroupKFold(n_splits=5, *, shuffle=False, random_state=None)`, `TimeSeriesSplit(..., gap=0)`).

**Goal.** Show the AUC inflation caused by the same customer appearing in train and test, then build a time-ordered split with a label-delay gap for a refund-fraud model.

**Adapted from.** "3.1. Cross-validation: evaluating estimator performance - scikit-learn 1.9.1 documentation" https://scikit-learn.org/stable/modules/cross_validation.html (sections "Cross-validation iterators for grouped data" and "Time Series Split").

**Prerequisites.** `pip install "scikit-learn==1.9.1" "pandas==3.0.*"`. On Windows set `LOKY_MAX_CPU_COUNT=4` to silence a joblib warning (see the errors below).

**Code: `lab7_leakage_splits.py`**
```python
"""Lab 7 - Leakage-safe validation for a refund-fraud model: GroupKFold and TimeSeriesSplit."""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, KFold, TimeSeriesSplit, cross_val_score

rng = np.random.default_rng(0)
n_customers, per_customer = 400, 15
customer = np.repeat(np.arange(n_customers), per_customer)
# Each customer has a stable "fingerprint" (device, address hash) and a fixed fraud propensity.
fraudster = rng.random(n_customers) < 0.15
profile = rng.normal(size=(n_customers, 5))
profile[fraudster, 0] += 0.8          # weak, REAL signal that generalizes to new customers
fingerprint, is_fraudster = profile[customer], fraudster[customer]
noise = rng.normal(size=(len(customer), 5))
df = pd.DataFrame(np.hstack([fingerprint + 0.3 * noise, noise[:, :2]]),
                  columns=[f"f{i}" for i in range(7)])
df["customer_id"] = customer
df["event_day"] = rng.integers(0, 365, len(df))
y = (is_fraudster & (rng.random(len(df)) < 0.8)).astype(int)

X = df.drop(columns=["customer_id", "event_day"])
model = HistGradientBoostingClassifier(max_iter=200, random_state=0)

leaky = cross_val_score(model, X, y, cv=KFold(5, shuffle=True, random_state=0), scoring="roc_auc")
safe = cross_val_score(model, X, y, groups=df["customer_id"],
                       cv=GroupKFold(n_splits=5, shuffle=True, random_state=0), scoring="roc_auc")
print(f"KFold (rows shuffled, customers leak):  ROC-AUC {leaky.mean():.3f} +/- {leaky.std():.3f}")
print(f"GroupKFold (customer never in both):    ROC-AUC {safe.mean():.3f} +/- {safe.std():.3f}")

# Time-ordered evaluation: sort by event time FIRST, then leave a 7-day gap (label delay).
order = np.argsort(df["event_day"].to_numpy(), kind="stable")
Xs, ys, days = X.iloc[order], y[order], df["event_day"].to_numpy()[order]
rows_per_day = len(df) // 365
tscv = TimeSeriesSplit(n_splits=4, gap=7 * rows_per_day)
for k, (tr, te) in enumerate(tscv.split(Xs)):
    print(f"fold {k}: train days {days[tr].min():>3}-{days[tr].max():>3} | "
          f"test days {days[te].min():>3}-{days[te].max():>3} | n_train={len(tr)}")
assert all(days[tr].max() < days[te].min() for tr, te in tscv.split(Xs)), "future leaked into train"
```

**Run.** `LOKY_MAX_CPU_COUNT=4 python lab7_leakage_splits.py` (PowerShell: `$env:LOKY_MAX_CPU_COUNT=4; python lab7_leakage_splits.py`). It took about 50 s on a laptop.

**Expected output (captured run)**
```
KFold (rows shuffled, customers leak):  ROC-AUC 0.886 +/- 0.025
GroupKFold (customer never in both):    ROC-AUC 0.602 +/- 0.075
fold 0: train days   0- 64 | test days  71-145 | n_train=1088
fold 1: train days   0-138 | test days 145-220 | n_train=2288
fold 2: train days   0-213 | test days 220-290 | n_train=3488
fold 3: train days   0-284 | test days 290-364 | n_train=4688
```
Reading: the same model and data give **0.886 vs 0.602**. The 0.28 AUC gap is pure memorization of customer fingerprints. Only 0.60 generalizes to *new* customers.

**Walk-through**
1. `GroupKFold(n_splits=5, shuffle=True, random_state=0)`: `shuffle`/`random_state` are **keyword-only** and were added in scikit-learn 1.6. The signature at the 1.9.1 tag is `def __init__(self, n_splits=5, *, shuffle=False, random_state=None)` (`sklearn/model_selection/_split.py:608`, class at line 533). Without shuffle, folds are formed by greedy group-size balancing.
2. `cross_val_score(..., groups=df["customer_id"], ...)`: the group key is a **business decision**: customer, household, device, policy, patient, or document source. Choose the unit that the deployed model will meet *for the first time*.
3. `TimeSeriesSplit(n_splits=4, gap=7 * rows_per_day)`: `gap` counts **samples, not days** (signature `n_splits=5, *, max_train_size=None, test_size=None, gap=0`, `_split.py:1239`). Convert the label delay (chargebacks take about 7 days to arrive) into rows yourself, or write a custom date-based splitter.
4. `np.argsort(..., kind="stable")` before splitting: `TimeSeriesSplit` assumes the rows are already in time order. It never looks at a timestamp.
5. `assert ... days[tr].max() < days[te].min()`: an executable leakage test. Put it in the training repo's unit tests.
6. Both leak types appear together in real systems. Use `StratifiedGroupKFold` when positives are rare, and for "new customers in the future" combine a time cut-off with group exclusion.

**Common errors (exact messages)**
- `groups` forgotten: `ValueError: The 'groups' parameter should not be None.` Fix: pass `groups=` to `cross_val_score` / `split`.
- Too few groups: `ValueError: Cannot have number of splits n_splits=5 greater than the number of groups: 3.` Fix: lower `n_splits`, or use `LeaveOneGroupOut`.
- Gap too large: `ValueError: Too many splits=5 for number of samples=50 with test_size=8 and gap=40.` Fix: reduce `n_splits` or `gap`, or set `test_size`.
- Windows: `UserWarning: Could not find the number of physical cores ... Returning the number of logical cores instead. You can silence this warning by setting LOKY_MAX_CPU_COUNT ...`. It is harmless. Set the env var.

**Best practice.** Fit every preprocessor (scaler, target encoder, TF-IDF) **inside a `Pipeline`**, so it is re-fit per fold. A target encoder fit on all rows leaks the label even when the split is correct. Write the split rule ("group = customer_id; time cut-off = event_day; gap = 7 days") into the dataset contract.

**Variation.** Add a deliberately leaky feature, for example `customer_fraud_rate` computed on all rows. Watch GroupKFold AUC jump, then fix it by computing the feature inside each training fold only.

---

## Lab 8: Near-duplicate dedup and train/test decontamination of an HR-policy QA set (datasketch MinHash LSH)

> **Verifier (2026-10-23):** VERIFIED against datasketch 2.0.0 source (`MinHash(..., scheme=None)` with `affine32`/`affine64`/`legacy`).

**Goal.** Before fine-tuning an HR-policy assistant, (1) collapse near-duplicate policy snippets in the training set, and (2) remove training items that nearly duplicate the held-out eval set.

**Adapted from.** "MinHash LSH - datasketch 2.0.0 documentation" https://ekzhu.com/datasketch/lsh.html.

**Prerequisites.** `pip install "datasketch==2.0.0"`.

**Code: `lab8_minhash_dedup.py`**
```python
"""Lab 8 - Near-duplicate dedup + train/test decontamination of an HR-policy QA set (datasketch 2.0.0)."""
import re
from datasketch import MinHash, MinHashLSH

NUM_PERM = 128

def shingles(text, k=5):
    """Character 5-grams over normalized text: robust to small edits and punctuation."""
    t = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text.lower())).strip()
    return {t[i:i + k] for i in range(max(1, len(t) - k + 1))}

def signature(text):
    m = MinHash(num_perm=NUM_PERM)          # 2.0.0 default scheme = "affine32"
    m.update_batch(s.encode("utf8") for s in shingles(text))
    return m

train = {
    "tr-001": "Employees accrue 1.5 days of paid time off per month of service.",
    "tr-002": "Employees accrue 1.5 days of paid time-off per month of service!",
    "tr-003": "Parental leave is 16 weeks at full pay for all new parents.",
    "tr-004": "Remote work requires manager approval and a signed equipment form.",
    "tr-005": "Expense reports must be filed within 30 days of the purchase date.",
    "tr-006": "Expense reports must be submitted within 30 days of the purchase date.",
}
test = {
    "te-001": "Parental leave is 16 weeks at full pay for all new parents",
    "te-002": "Badges must be worn visibly at all times inside the office.",
}

# 1) Dedup inside train: keep the first doc of each near-duplicate cluster.
lsh = MinHashLSH(threshold=0.7, num_perm=NUM_PERM)
sigs, kept, dropped = {}, [], []
for key, text in train.items():
    sigs[key] = signature(text)
    matches = lsh.query(sigs[key])
    if matches:
        dropped.append((key, matches[0], round(sigs[key].jaccard(sigs[matches[0]]), 2)))
    else:
        lsh.insert(key, sigs[key])
        kept.append(key)
print("kept:", kept)
print("dropped (dup, of, est. Jaccard):", dropped)

# 2) Decontaminate: index the TEST set, drop any train doc that hits it.
test_lsh = MinHashLSH(threshold=0.7, num_perm=NUM_PERM)
for key, text in test.items():
    test_lsh.insert(key, signature(text))
leaked = {k: test_lsh.query(sigs[k]) for k in kept if test_lsh.query(sigs[k])}
print("train docs leaking into test:", leaked)
print("final train set:", [k for k in kept if k not in leaked])
```

**Run.** `python lab8_minhash_dedup.py`

**Expected output (captured run)**
```
kept: ['tr-001', 'tr-003', 'tr-004', 'tr-005']
dropped (dup, of, est. Jaccard): [('tr-002', 'tr-001', 0.82), ('tr-006', 'tr-005', 0.77)]
train docs leaking into test: {'tr-003': ['te-001']}
final train set: ['tr-001', 'tr-004', 'tr-005']
```

**Walk-through**
1. `shingles(..., k=5)` on normalized characters: the shingle design matters more than the LSH settings. Word 1-grams make "filed" vs "submitted" look very different. Character 5-grams after stripping punctuation catch it (estimated Jaccard 0.77).
2. `MinHash(num_perm=128)`: signature `MinHash(num_perm=128, seed=1, gpu_mode="disable", hashfunc=None, hashobj=None, hashvalues=None, permutations=None, scheme=None)` (`datasketch/minhash.py:248-258`). **New in 2.0.0:** `scheme=None` means `"affine32"`. The pre-2.0 behavior is `"legacy"`. The docstring says *"MinHash pickled by earlier versions deserializes with scheme="legacy"... Any persisted LSH index must be rebuilt with sketches of a single scheme."*
3. `update_batch(...)` (`minhash.py:456`) is faster than calling `update` in a loop. `MinHash.bulk(...)` (`minhash.py:718`) builds many signatures at once.
4. `MinHashLSH(threshold=0.7, num_perm=128)`: signature `threshold=0.9, num_perm=128, weights=(0.5, 0.5), params=None, storage_config=None, prepickle=None, hashfunc=None` (`datasketch/lsh.py:147-156`). With threshold 0.7 and 128 perms it picked b = 14 bands × r = 9 rows (printed from `.b`/`.r` in the run). LSH is **approximate**: `query` returns *candidates*. Check `jaccard()` before you drop anything that matters.
5. Query-then-insert in step 1 keeps the first member of each cluster. That is order-dependent, so sort by a quality signal (newest policy version, longest, human-verified) before deduping.
6. Step 2 **indexes the test set** and queries the train set. It is cheap (the index size equals the test size) and is the standard decontamination step for fine-tuning and RAG eval sets.

**Common errors (exact messages)**
- `ValueError: The given key already exists`. Cause: the same doc ID is inserted twice. Fix: query first (as above), or use unique keys such as `f"{source}:{id}:{chunk}"`.
- `ValueError: Expecting minhash with length 128, got 256`. Cause: index and signatures were built with different `num_perm`. Fix: one constant shared by the indexing and query code.
- **New in 2.0:** `ValueError: MinHash scheme 'legacy' does not match scheme 'affine32' of the MinHash previously given to this index`, and `ValueError: Cannot compute Jaccard given MinHash with different permutation schemes`. Cause: signatures pickled with datasketch 1.x are mixed with new ones. Fix: rebuild the whole index after the upgrade, or pass `scheme="legacy"` everywhere until you can.
- `ValueError: The product of b and r in params is 30 * 5 = 150 -- it must be less than num_perm 128. Did you forget to specify num_perm?` Fix: `b * r <= num_perm`.

**Best practice.** Dedup in layers: (1) exact hash on normalized text, (2) MinHash LSH for edits, (3) embedding cosine for paraphrases (`research-custom/05` §7). Log every drop as `(dropped_id, kept_id, jaccard)` so a reviewer can audit false merges. Two policy versions that differ only in "16 weeks" vs "12 weeks" are near-duplicates **with different facts**, and you must keep the current one, not the first one.

**Variation.** For millions of documents, use `lsh.insertion_session(buffer_size=50000)` (`lsh.py:257`) or `storage_config={"type": "redis", ...}` for a shared index. For a membership-sensitive audit, read the near-duplicate-family MI paper in §9: dedup changes what "this exact record was in training" can mean.

---

## 9. arXiv insights for these labs (2026-07-23 .. 2026-10-23)

All found through the arXiv API (sorted by submittedDate). Claims below are taken from the abstracts only; I did not read the full papers.

| Lab | Paper | What it says (from the abstract) | Classroom use |
|---|---|---|---|
| 5 | **Agreement Without Alignment: Label-Free Rubric Clarification Increases LLM-Judge Consensus but Not Agreement with Humans**: Han, Kim, arXiv **2610.13303** (2026-10-09) | Rewriting the most contested rubric clauses raised inter-judge Krippendorff α by **0.069** (95% CI 0.046-0.092) on SummEval, but agreement with experts did not change (Kendall τ diff −0.007, CI −0.037 to 0.021). 5 judges from 3 providers, 129,770 judge requests. | High alpha between LLM judges ≠ validity. Lab 5 keeps humans as the anchor. |
| 5 | **Four Ledgers, Not One Score: Responsible Communication of LLM-Judge Calibration in Biomedical ML**: Chang, Zhu, **2609.15015** (2026-09-14) | Planted synthetic perturbations are not human ground truth. A naive scorer produced 0.710 and 0.218, which were "proposal-confirmation yield and submitted-ledger composition, not judge precision and recall". Only 3 targets were double-annotated. | Track the provenance of labels. Do not report IAA from 3 double-annotated items. |
| 4 | **Identifying Suspected Mislabeled Apps in Google Play Application Removal Prediction: An Empirical Comparison of Label Noise Detection Methods**: Dobles Montalvan et al., **2609.25487** (2026-09-21) | Over 870,514 apps, three detectors agreed on 7,598 candidates. **Removing flagged apps did not improve the model**, and the loss grew with the number removed. A model trained only on overlap apps got AUC 0.2518. | Flagged ≠ delete. Use cleanlab to *characterize and review* noise, especially when the label is a proxy. |
| 4 | **Adaptive Ensemble Selection for Noisy Labels on Tabular Data**: Ali, Kang, Seneviratne, **2609.32976** (2026-09-26) | A meta-model weighting confidence-, neighborhood- and distribution-based detectors is "comparable to a Confident Learning baseline on average, with dataset-dependent gains and losses". | Confident learning remains the baseline to beat. Supports Lab 4's two-model best practice. |
| 4 | **Every Batch Is Its Own Validation Set: Leave-One-Out Gradient Matching for Online Data Selection in LLM Fine-Tuning** (LOOM): Chen et al., **2610.00436** (2026-09-30) | In-sample gradient matching favors the noisiest examples. The leave-one-out fix beats full-batch training by +2.3/+2.4 points (Llama-3.1-8B, Qwen2.5-7B) and "selects injected label noise at under a fifth of its base rate". | Same lesson as `cross_val_predict` in Lab 4: scoring an example with itself rewards noise. |
| 4 | **Understanding Data Augmentation under Label Noise**: Zheng, Teng, **2610.27701** (2026-10-20) | Theory: under label noise, DA "acts as an uncertainty amplifier", decreasing stability and generalization in some regimes. | Clean labels before you augment or synthesize. |
| 6 | **Hidden Cartographer: Hidden State Guided Data Selection for Dual Budgeted Instruction Tuning**: Qin et al., **2610.25215** (2026-10-18) | Two-stage selection (hidden-state proxy for annotation, then training-dynamics pruning) across medical, legal and finance. Best average accuracy among budgeted baselines, annotating 20-30% of the pool and fine-tuning on 10-15%. | The LLM-era version of Lab 6: separate the *annotation* budget from the *training* budget. |
| 7 | **The Silent Failures in Agentic Data Science**: Li et al., **2610.14115** (2026-10-09) | Across 220 tasks, "the majority of agentic solutions contain at least one failure mode". They found a **positive correlation between data leakage failures and predictive performance**. | Higher CV score from a coding agent is a red flag. Run Lab 7's assert on agent-written pipelines. |
| 7 | **Crop Yield Prediction for Punjab, Pakistan: ... and What Random Validation Hides**: Asif et al., **2610.07059** (2026-10-05) | A 414-row table held only **46 independent observations** (a join copied each crop-year 9×). Holding out whole years took XGBoost from **R² 0.994 to −0.20**. | Joins create hidden groups. Dedup and group by the real unit before splitting. |
| 7 | **Data Leakage in Patch-Based Hyperspectral Image Classification: Quantifying the Impact of Spatial Overlap**: Alkhatib, **2610.08770** (2026-10-06) | Random patch sampling gives 3D-CNN 96.17% OA. Spatially disjoint sampling gives 55.20%. ViT/2D-CNN drop 40.71/38.81 pp. | Spatial version of GroupKFold: the group is the image region. |
| 8 | **Scores That Hold, Benchmarks That Leak: Measuring Dataset Contamination in Public Brain-Tumor MRI Classification**: Vangala et al., **2610.00421** (2026-09-30) | 28.8% of the official test split has a near-twin in train, a second corpus leaks 22.3% byte-identically, and 95.5% of traceable test images share a patient with train. Removing leaked test images left balanced accuracy **essentially unchanged**: "stable performance after deduplication does not establish benchmark integrity". | Dedup is necessary but does not prove integrity. Also check group (patient) and source shortcuts. |
| 8 | **Near-Duplicate Families Break Exact-Record Membership Inference**: Liu et al., **2609.33909** (2026-09-27) | On CC-News, a LiRA auditor labels **99.70%** of family-present exact non-members as members at 1% FPR. The effect persists after deduplication and retraining. | After MinHash dedup, "was this exact record trained on?" is still hard to answer. Audit at the family level. |
| 2/3 | **Learning to Detect Shifts in Unstructured Data Streams via Monitoring-by-Betting**: Zhou et al., **2610.17399** (2026-10-12) | Sequential e-detectors with adaptive "witness functions" control false alarms asymptotically. Calibration sets as small as **m = 30** worked. LLM-concept monitors were fastest and most interpretable on a clinical AI-scribe deployment. | The next step beyond fixed PSI/KS for LLM traffic: monitor continuously, with controlled false alarms. |

---

## 10. Cross-lab gotchas (all found in real runs)

1. **Matrix orientation flips between libraries.** statsmodels `aggregate_raters` takes items × raters. `krippendorff.alpha` takes raters × items. Neither raises an error when you get it wrong.
2. **Defaults that silently change the answer:** `krippendorff.alpha` defaults to `interval`. Evidently `Report` defaults to `include_tests=False`. `DataDriftPreset` gates on `drift_share=0.5`. datasketch 2.0 changed the MinHash scheme. cleanlab `n_jobs=None` uses multiprocessing.
3. **p-values vs. distances.** Evidently's `ValueDrift` value is a p-value for `ks` (low means drift) and a distance for `psi`/JS (high means drift).
4. **Windows multiprocessing:** cleanlab with default `n_jobs` and no `__main__` guard printed `RuntimeError ... bootstrapping phase` and hung. joblib warns about physical cores unless `LOKY_MAX_CPU_COUNT` is set.
5. **Dependency footprint:** `pandera` needs the `[pandas]` extra. `evidently` 0.7.23 pulls a web stack (litestar, msgspec, uvicorn) and needs `plotly<6`. Pin it in a separate monitoring environment if the training environment is strict.
6. **pandas 3.1.0 was released yesterday (2026-10-22).** pandera 0.34.1 has explicit `PANDAS_3_0_0_PLUS` code paths (`pandera/engines/pandas_engine.py:74`), but no library here has been tested on 3.1, so pin `pandas==3.0.*` for class **[pandas 3.x behavior with these labs UNVERIFIED]**.

## 11. Sources
- PyPI JSON: https://pypi.org/pypi/{pandera,evidently,cleanlab,scikit-learn,datasketch,krippendorff,statsmodels,scipy,numpy,pandas,scikit-activeml,modAL-python,small-text}/json (fetched 2026-10-23)
- Library source read from the released wheels (pandera 0.34.1, evidently 0.7.23, cleanlab 2.9.0, datasketch 2.0.0, krippendorff 0.9.0). scikit-learn: https://raw.githubusercontent.com/scikit-learn/scikit-learn/1.9.1/sklearn/model_selection/_split.py. statsmodels: https://raw.githubusercontent.com/statsmodels/statsmodels/v0.15.0/statsmodels/stats/inter_rater.py
- Docs: https://pandera.readthedocs.io/en/stable/dataframe_models.html · https://pandera.readthedocs.io/en/stable/lazy_validation.html · https://docs.evidentlyai.com/quickstart_ml · https://docs.evidentlyai.com/metrics/customize_data_drift · https://docs.cleanlab.ai/stable/tutorials/clean_learning/text.html · https://docs.cleanlab.ai/stable/tutorials/indepth_overview.html · https://scikit-learn.org/stable/modules/cross_validation.html · https://ekzhu.com/datasketch/lsh.html · https://github.com/pln-fing-udelar/fast-krippendorff · https://www.statsmodels.org/stable/generated/statsmodels.stats.inter_rater.fleiss_kappa.html · https://scikit-activeml.github.io/
- arXiv: 2610.13303, 2609.15015, 2609.25487, 2609.32976, 2610.00436, 2610.27701, 2610.25215, 2610.14115, 2610.07059, 2610.08770, 2610.00421, 2609.33909, 2610.17399 (https://arxiv.org/abs/<id>)
