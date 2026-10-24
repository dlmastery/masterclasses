# 04 - Dataset Design: Datasheets, Data Cards, Data Contracts, Coverage, Slices, Quality and Drift

Research date: 2026-10-23. Part of the deck "Customizing modern AI - SFT, RL, RAG" / "Data-Centric AI - modern dataset design and synthesis".
Lifecycle position: **DESIGN** (this file) -> generate -> select -> curate -> label -> denoise -> **quality card** (documentation closes the loop).

Verification legend: versions and APIs below were checked against PyPI, official docs, GitHub or arXiv on 2026-10-23 unless marked **[UNVERIFIED]** (recalled, not re-checked in this session). The web-search budget ran out partway through, so a few secondary facts are recalled and marked as such.

---

## 1. Why dataset design is a first-class engineering artifact

- In modern customization (SFT, preference/RL, RAG corpora), **the dataset is the spec**. The model learns what the data covers. Gaps in coverage become gaps in capability, and undocumented provenance becomes legal risk.
- There are three complementary artifacts, each for a different reader:
  1. **Human-readable documentation** (Datasheets, Data Cards, HF dataset cards) explains why the data exists, what is in it, and how it may be used.
  2. **Machine-readable metadata** (MLCommons Croissant + Croissant-RAI) makes datasets discoverable and loadable, and lets tools audit them.
  3. **Executable contracts** (Great Expectations, Pandera, Soda, dbt model contracts, ODCS / datacontract-cli) state schema, semantics and SLAs that CI checks on every batch.
- Plus **measurement**: coverage against a taxonomy, slice definitions, and drift monitoring (PSI / KS / JS / embedding drift) with Evidently or whylogs.

Regulatory driver: **EU AI Act, Article 10 (Data and data governance)**. Training, validation and testing datasets for high-risk systems "shall be subject to data governance and management practices". Para. 2 covers "the relevant design choices", "data collection processes and the origin of data", "relevant data-preparation processing operations, such as annotation, labelling, cleaning", "the formulation of assumptions, in particular with respect to the information that the data are supposed to measure", and "examination in view of possible biases". Para. 3 says datasets shall be "relevant, sufficiently representative, and to the best extent possible, free of errors and complete". Source: https://artificialintelligenceact.eu/article/10/. That site gives the application dates as **2 Dec 2027 (Annex III)** and **2 Aug 2028 (Annex I)**, which reflects the postponement under the Digital Omnibus. Before quoting the dates on a slide, check them against EUR-Lex.

Provenance problem in numbers: **"The Data Provenance Initiative: A Large Scale Audit of Dataset Licensing & Attribution in AI"** (Longpre, Mahari, Chen et al., arXiv:2310.16787, Oct 2023) audited **1,800+ text datasets** and found **license omission of 70%+ and error rates of 50%+** on popular hosting sites. https://arxiv.org/abs/2310.16787

---

## 2. Documentation standards

### 2.1 Datasheets for Datasets (2018 -> CACM 2021)
- **Title:** "Datasheets for Datasets". **Authors:** Timnit Gebru, Jamie Morgenstern, Briana Vecchione, Jennifer Wortman Vaughan, Hanna Wallach, Hal Daumé III, Kate Crawford. arXiv:1803.09010, v1 23 Mar 2018. Published in *Communications of the ACM*, Dec 2021. https://arxiv.org/abs/1803.09010
- The analogy comes from electronics, where "every component, no matter how simple or complex, is accompanied with a datasheet".
- Question sections, from the paper's structure: **Motivation; Composition; Collection Process; Preprocessing/Cleaning/Labeling; Uses; Distribution; Maintenance**. The abstract confirms motivation, composition, collection process and recommended uses. The 7-section list is the standard reading of the paper; check it against the PDF.
- Related lineage, recalled: Data Statements for NLP (Bender & Friedman, TACL 2018); Dataset Nutrition Label (Holland et al., arXiv:1805.03677, 2018); Model Cards (Mitchell et al., arXiv:1810.03993, FAT* 2019). **[UNVERIFIED in this session]**

### 2.2 Google Data Cards and the Data Cards Playbook
- **Paper:** "Data Cards: Purposeful and Transparent Dataset Documentation for Responsible AI". Mahima Pushkarna, Andrew Zaldivar, Oddur Kjartansson (Google Research). **ACM FAccT 2022**, DOI 10.1145/3531146.3533231, arXiv:2204.01075. https://arxiv.org/abs/2204.01075
  - The cards use a row-and-column thematic structure for indexing. The paper reports lessons from deploying **20+ Data Cards**.
- **Playbook:** https://sites.research.google/datacardsplaybook/ (blog: "The Data Cards Playbook: A Toolkit for Transparency in Dataset Documentation", Google Research, Nov 2022, https://research.google/blog/the-data-cards-playbook-a-toolkit-for-transparency-in-dataset-documentation/)
  - Four modules: **Ask** (co-create a template with stakeholders), **Inspect** (test the template on real datasets), **Answer** (fill the card, using patterns from **40+ Data and Model Cards deployed at Google**), **Audit** (assess a completed card and measure transparency across datasets).
  - The template covers **15 themes**, e.g. Authorship, Motivations & Intentions, Provenance, Human and Other Sensitive Attributes, Annotations & Labeling, Reflections on Data.
  - Quotable lines: "Data Cards are structured summaries of essential facts about various aspects of ML datasets"; "Co-create transparency with stakeholders from across the dataset lifecycle." The site also says it "may not reflect current approaches to Data Cards". This is an honest point for the open-challenges slide.

### 2.3 Hugging Face Dataset Cards (de facto industry format)
- A dataset card is the repo's `README.md`. The Hub renders it, and a **YAML front-matter** block drives search and filters. Docs: https://huggingface.co/docs/hub/datasets-cards; spec: https://github.com/huggingface/hub-docs/blob/main/datasetcard.md
- Key fields: `language`, `pretty_name`, `tags`, `license`, `task_categories` (plus size categories and `configs`). The Hub turns linked arXiv IDs into `arxiv:<id>` tags.
- New in 2026 docs: an `rl-environment` tag plus framework tags (`harbor`, `verifiers`, `openenv`, `nemo-gym`, `agentenv`). This shows that "datasets" now include **RL environments**, which is directly relevant to the RL part of the deck.

```yaml
---
pretty_name: Support-Tickets-SFT-v3
license: cc-by-4.0
language: [en, de]
task_categories: [text-generation]
tags: [sft, customer-support, synthetic]
---
```
(Adapted from https://huggingface.co/docs/hub/datasets-cards)

### 2.4 MLCommons Croissant + Croissant-RAI (machine-readable)
- Repo: https://github.com/mlcommons/croissant. The spec page links **Croissant 1.1** (https://mlcommons.org/croissant/1.1); many files still declare `conformsTo: http://mlcommons.org/croissant/1.0`.
- Paper: "Croissant: A Metadata Format for ML-Ready Datasets", arXiv:2403.19546, NeurIPS 2024 Datasets & Benchmarks Track. RAI paper: arXiv:2407.16883 ("A Standardized Machine-readable Dataset Documentation Format for Responsible AI").
- Built on schema.org JSON-LD, in four layers: metadata, resources (FileObject/FileSet), structure (RecordSet/Field), and semantics.
- Adoption: **Hugging Face, Kaggle, OpenML** expose Croissant JSON-LD (export buttons, API endpoints), and Google Dataset Search indexes it.
- Croissant 1.1 (ODI announcement, https://theodi.org/news-and-events/blog/croissant-11/) adds machine-actionable provenance, interoperability with domain ontologies, structured usage policies, and better modelling of complex datasets.
- Croissant-RAI covers the data life cycle, labeling, participatory processes, AI safety, fairness and regulatory compliance. It draws explicitly on Data Cards and Datasheets.
- NeurIPS D&B requiring Croissant files for submissions: started in 2024; current-year status **[UNVERIFIED]**.

```python
# pip install mlcroissant   (Python 3.10+)
import mlcroissant as mlc

url = "https://huggingface.co/api/datasets/fashion_mnist/croissant"
ds = mlc.Dataset(url)                     # local or remote JSON-LD
print(ds.metadata.to_json()["name"])      # inspect metadata
for i, record in enumerate(ds.records(record_set="fashion_mnist")):
    print(record)
    if i > 2: break
```
(Adapted from https://github.com/mlcommons/croissant README. The HF endpoint pattern `/api/datasets/<id>/croissant` is from HF docs; the record_set name depends on the dataset.)

---

## 3. Data contracts: schema + semantics + SLAs as code

**Definition for the slide:** a data contract is an agreement between a producer and its consumers. It is versioned in git and enforced in CI and production. It specifies:
1. **Schema**: columns/fields, types, nullability, keys.
2. **Semantics**: allowed values, ranges, regex formats, referential rules, units, and meaning ("`amount` is gross EUR, incl. VAT").
3. **SLAs / quality**: freshness, completeness, volume, uniqueness, latency, plus an owner and support channel.
4. **Change policy**: breaking-change detection and versioning.

For ML/LLM datasets, the "consumer" is a training or evaluation pipeline. Contracts catch problems like a silent label-schema change, a new language appearing, empty `response` fields from a synthetic generator, or a stale RAG corpus.

### 3.1 Open Data Contract Standard (ODCS), Bitol / Linux Foundation
- ODCS v3 broadened schema support to hierarchical, streaming and unstructured data and added a Support & Communication section (https://bitol.io/odcs-version-3-transforming-data-contracts-with-enhanced-flexibility-integration-and-global-collaboration/).
- **ODCS v3.1.0** (announced ~Dec 2025) added relationships between properties, stricter JSON Schema validation, **executable SLAs**, and improved referencing, while keeping v3.0.x contracts valid (https://bitol.io/bitol-announces-odcs-v3-1-0-stronger-smarter-and-stricter/).
- ODCS v3.2 with an "AI context block" (RFC-0038, reportedly approved 2026-05-19) and Bitol "graduating" within LF AI & Data: both from secondary sources, **[UNVERIFIED]**.
- **datacontract-cli** (https://github.com/datacontract/datacontract-cli) is built on ODCS:
  - `datacontract lint odcs.yaml`
  - `datacontract test odcs.yaml` (schema and quality checks against the live source)
  - `datacontract export sql odcs.yaml` (also dbt, JSON Schema, HTML ...)
  - `datacontract breaking v1.odcs.yaml v2.odcs.yaml` (fails on breaking changes)

```python
from datacontract.data_contract import DataContract

data_contract = DataContract(data_contract_file="odcs.yaml")
run = data_contract.test()
if not run.has_passed():
    print("Data quality validation failed.")
```
(Source: datacontract-cli README; version not shown on GitHub page, check `datacontract --version` **[version UNVERIFIED]**.)

### 3.2 Great Expectations (GX Core) - v1.24.1 (PyPI, released 2026-10-22)
- Concepts in GX 1.x: Data Context -> Data Source -> Data Asset -> Batch Definition -> Batch -> Expectation / Expectation Suite -> Validation Definition -> Checkpoint (actions). Expectations are now **classes** (`gx.expectations.ExpectColumnValuesToBeBetween`) and support `severity`.

```python
import great_expectations as gx
import pandas as pd

context = gx.get_context()
df = pd.read_csv("https://raw.githubusercontent.com/great-expectations/"
                 "gx_tutorials/main/data/yellow_tripdata_sample_2019-01.csv")

data_source = context.data_sources.add_pandas("pandas")
data_asset = data_source.add_dataframe_asset(name="pd dataframe asset")
batch_def = data_asset.add_batch_definition_whole_dataframe("batch definition")
batch = batch_def.get_batch(batch_parameters={"dataframe": df})

expectation = gx.expectations.ExpectColumnValuesToBeBetween(
    column="passenger_count", min_value=1, max_value=6, severity="warning")
print(batch.validate(expectation))   # -> "success": true on the sample
```
(Source: "Try GX Core", https://docs.greatexpectations.io/docs/core/introduction/try_gx)

### 3.3 Pandera - v0.34.1 (PyPI, released 2026-10-06)
- Schemas live in code and run as DataFrame validators (pandas, polars, pyspark, ibis ...). **Use `import pandera.pandas as pa`**: the top-level `import pandera` for pandas is deprecated and emits a `FutureWarning`.

```python
import pandas as pd
import pandera.pandas as pa

class SFTRow(pa.DataFrameModel):          # class-based contract for an SFT shard
    prompt: str   = pa.Field(str_length={"min_value": 1})
    response: str = pa.Field(str_length={"min_value": 1})
    lang: str     = pa.Field(isin=["en", "de", "fr"])
    quality: float = pa.Field(ge=0.0, le=1.0)

    class Config:
        strict = True                       # no unexpected columns

SFTRow.validate(df, lazy=True)              # collect all failures at once
```
(Pattern adapted from https://pypi.org/project/pandera/ and Pandera docs. `DataFrameModel`, `Field(ge, le, isin, str_length)`, `Config.strict` and `lazy=True` are documented APIs. The column names are illustrative.)

### 3.4 Soda Core v4 data contracts
- A contract is a YAML file with a `dataset:` key (fully qualified `datasource/db/schema/table`, which must match the data-source config name), per-column `checks`, and dataset-level `checks`.

```yaml
dataset: my_datasource/my_database/public/orders
columns:
  - name: order_id
    checks:
      - missing:
      - duplicate:
  - name: email
    checks:
      - invalid:
          valid_format:
            name: Email address
            regex: '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
  - name: created_at
checks:
  - row_count:
      threshold: { must_be_greater_than: 0 }
  - freshness:
      column: created_at
      threshold: { unit: hour, must_be_less_than: 24 }
```
```bash
soda contract verify --data-source ds_config.yml --contract contract.yml
#   --set START_DATE=2024-05-01  (variables)   --publish --soda-cloud sc.yml
```
(Source: Soda docs, contract-language-reference and git-managed-data-contracts/verify-a-contract, https://docs.soda.io/. Kestra's plugin pins `soda-core==4.23.1`, which suggests 4.x is current. **Exact latest version [UNVERIFIED]**.)

### 3.5 dbt model contracts
- Source: "Model contracts | dbt Developer Hub", https://docs.getdbt.com/docs/mesh/govern/model-contracts

```yaml
models:
  - name: dim_customers
    config:
      contract:
        enforced: true
    columns:
      - name: customer_id
        data_type: int
        constraints:
          - type: not_null
      - name: customer_name
        data_type: string
```
- With `enforced: true`, every column must declare `name` + `data_type`. Supported for `table`, `view` (no constraints) and `incremental` (only with `on_schema_change: append_new_columns` or `fail`). Not supported for Python models, materialized views, ephemeral models, sources, seeds or snapshots.
- **Breaking-change detection** (state comparison) flags: removing a column, changing `data_type`, removing or modifying a constraint (v1.6+), and deleting, renaming or disabling a contracted model (v1.9+; an error for versioned models, a warning for unversioned ones).

### 3.6 Tool choice matrix (slide-ready)
| Need | Best fit |
|---|---|
| Validate pandas/polars frames inside Python training code | **Pandera** |
| Rich expectation library, data docs, checkpoints, many backends | **Great Expectations** |
| YAML contracts on warehouse tables, CI verify, cloud alerting | **Soda Core 4** |
| Contracts on SQL-transformed models, breaking-change gates | **dbt contracts** |
| Vendor-neutral spec with SLAs, ownership, lint/test/export | **ODCS + datacontract-cli** |
| Distribution drift reports and tests (tabular, text, embeddings) | **Evidently** |
| Lightweight mergeable statistical profiles at scale | **whylogs** |

---

## 4. Coverage metrics and taxonomy coverage

**Idea:** define the space the model must handle as a **taxonomy** (domain x task x skill x difficulty x language x format x risk category). Then measure what fraction of the leaves the dataset populates, and how evenly.

Metrics (definitions to put on a slide):
- **Leaf coverage** = |leaves with >= k examples| / |leaves|. Choose k per leaf by required eval confidence (e.g. k = 30-100 for the eval split).
- **Balance / evenness**: normalized Shannon entropy of the leaf distribution H(p)/log(N); Gini coefficient; max/min leaf ratio.
- **Effective number of categories** = exp(H(p)).
- **Embedding-space coverage**: cluster embeddings (k-means / HDBSCAN), then compute the fraction of clusters from the reference (production) distribution that have training mass. Nearest-neighbor distance from production queries to the training set flags **"holes"**.
- **Diversity of instructions**: tag diversity (InsTag), distinct n-grams, self-BLEU, semantic dedup ratio.

Primary examples:
- **#InsTag: Instruction Tagging for Analyzing Supervised Fine-tuning of Large Language Models**: Lu, Yuan, Yuan, Lin, Lin, Tan, Zhou, Zhou (Alibaba/Qwen), arXiv:2308.07074, Aug 2023. It produced **6.6K open-set tags** for user queries. **TagLM**, fine-tuned on **6K** InsTag-selected samples, beats open models trained on far larger SFT sets on **MT-Bench**. Lesson: *diversity and complexity measured via tags predict SFT value.* https://arxiv.org/abs/2308.07074
- **Synthetic Data (Almost) from Scratch: Generalized Instruction Tuning for Language Models (GLAN)**: Haoran Li et al. (Microsoft, 20 authors), arXiv:2402.13064, Feb 2024. Its **only input is a taxonomy of human knowledge and skills**: fields -> sub-fields -> disciplines -> subjects -> syllabus -> class sessions -> key concepts -> instructions. New skills are added by **inserting a taxonomy node**. This is the clearest example of "taxonomy-first design driving generation". https://arxiv.org/abs/2402.13064
- Industry practice, recalled: Llama 3 / Tülu 3 reports describe skill-based data mixes and per-skill evaluation. **[UNVERIFIED details]**

Design flow (diagram in words):
`Product requirements -> risk & use-case taxonomy (tree) -> per-leaf target counts & eval quotas -> generate/collect per leaf -> tag every row with leaf IDs (LLM tagger + human spot-check) -> coverage heatmap (leaf x split) -> fill holes -> freeze + document in Data Card`

---

## 5. Slice definitions

A **slice** is a named, reproducible predicate over the data, e.g. `lang == "de" AND len(prompt) > 2000 AND domain == "billing"`. Slices turn coverage into **accountable evaluation**: every slice gets a metric, a minimum sample size and an owner.

Slices come from three sources:
1. **Declared (a priori):** from the taxonomy, fairness or sensitive attributes, product surfaces, and the risk register.
2. **Discovered (a posteriori):**
   - **Slice Finder: Automated Data Slicing for Model Validation**: Chung, Kraska, Polyzotis, Tae, Whang. **ICDE 2019** (arXiv:1807.06068). Finds **interpretable, large** slices where the model underperforms, using statistical testing in an interactive framework. https://arxiv.org/abs/1807.06068
   - **Domino: Discovering Systematic Errors with Cross-Modal Embeddings**: Eyuboglu, Varma, Saab, Delbrouck, Lee-Messer, Dunnmon, Zou, Ré. **ICLR 2022 (Oral)**, arXiv:2203.14960. It uses an evaluation framework of **1,235 slice settings** and identifies **36%** of them (+12 pp over prior methods). It names slices in natural language, getting the exact name in **35%** of settings. https://arxiv.org/abs/2203.14960
3. **Production-driven:** cluster live traffic and failed or flagged conversations, then promote recurring clusters to declared slices.

Slice spec template (put this in the contract or Data Card):
```yaml
slice: de_long_billing
predicate: "lang == 'de' and prompt_tokens > 2000 and domain == 'billing'"
min_eval_n: 200
metric: [task_success, groundedness]
gate: "task_success >= overall - 0.03"
owner: support-ml@company
```
(Illustrative schema, not a specific tool's format.)

---

## 6. Quality and drift

### 6.1 Core statistics (formulas for slides)
- **PSI (Population Stability Index)**: bin the reference distribution (e.g. 10 quantile bins), then PSI = Σ_i (a_i - e_i) · ln(a_i / e_i), where e_i are reference shares and a_i are current shares. Common credit-risk rule of thumb (an industry convention, not a standard): **< 0.1 stable, 0.1-0.25 moderate shift, > 0.25 major shift**. Evidently's default PSI threshold is **0.1**.
- **KS (Kolmogorov-Smirnov, two-sample)**: D = sup_x |F_ref(x) - F_cur(x)|. Reports a p-value and works for numeric data only. On large n even tiny shifts become "significant", which is why Evidently switches to distances when n > 1000.
- **Jensen-Shannon**: JS(P‖Q) = ½ KL(P‖M) + ½ KL(Q‖M), with M = ½(P+Q). It is symmetric and bounded, and its square root is a metric (the JS *distance*). Evidently uses the JS distance with a default threshold of **0.1**.
- **Wasserstein (Earth mover's)**: Evidently normalizes it by the reference std; default threshold **0.1**.
- **Embedding drift**: domain-classifier ROC AUC, share of drifted components, distance between mean embeddings, and MMD.

### 6.2 Evidently - v0.7.23 (PyPI, released 2026-09-11)
Default method choice (https://docs.evidentlyai.com/metrics/customize_data_drift):

| Column type | n <= 1000 | n > 1000 |
|---|---|---|
| Numerical | `ks` (p < 0.05) | `wasserstein` (>= 0.1) |
| Categorical | `chisquare` (`z` if binary) | `jensenshannon` (>= 0.1) |
| Text | `perc_text_content_drift` (domain classifier, 95th pct) | `abs_text_content_drift` (ROC AUC 0.55) |

Dataset-level drift is flagged when the share of drifted columns is >= `drift_share` (default **0.5**). Other methods: `psi`, `kl_div`, `hellinger`, `anderson`, `cramer_von_mises`, `mannw`, `ed`, `es`, `t_test`, `empirical_mmd`, `fisher_exact`, `g-test`, `TVD`.

```python
import pandas as pd
from sklearn import datasets
from evidently import Report
from evidently.presets import DataDriftPreset
from evidently.metrics import ValueDrift

iris = datasets.load_iris(as_frame=True).frame
report = Report([
    DataDriftPreset(method="psi", drift_share=0.7),   # all columns via PSI
    ValueDrift(column="sepal length (cm)", method="ks"),
], include_tests=True)
my_eval = report.run(iris.iloc[:60], iris.iloc[60:])  # (current, reference)
my_eval.save_html("drift.html")                        # or my_eval.json()
```
(Adapted from https://pypi.org/project/evidently/ and the customize-data-drift docs. The `ValueDrift` import path `evidently.metrics` follows the new API **[verify on run]**.)

Embedding drift (https://docs.evidentlyai.com/metrics/customize_embedding_drift) is still documented on the **legacy** `EmbeddingsDriftMetric` API, and the new API is marked "coming soon":

| method | output | default threshold |
|---|---|---|
| `model` (default) | domain-classifier ROC AUC | 0.55 |
| `ratio` | share of drifted components (Wasserstein, 0.1) | 0.2 |
| `distance` | euclidean/cosine/cityblock/chebyshev between means | 0.2 |
| `mmd` | Maximum Mean Discrepancy | 0.015 (the docs page is inconsistent here) |

```python
from evidently.metrics.data_drift.embedding_drift_methods import model
report = Report(metrics=[
    EmbeddingsDriftMetric("small_subset",
        drift_method=model(threshold=0.55, bootstrap=None,
                           quantile_probability=0.95, pca_components=None))
])
```
(Legacy API; `Report` / `EmbeddingsDriftMetric` come from `evidently.legacy.*` in 0.7.x **[import path UNVERIFIED]**.)

### 6.3 WhyLabs / whylogs
- **whylogs** (open source) builds mergeable statistical **profiles** (counts, types, distribution sketches, cardinality) without storing raw data. This makes it privacy-friendly and suits streaming or distributed data. Latest on PyPI: **1.6.4 (2024-12-03)**, so it has seen little activity since.

```python
import whylogs as why
import pandas as pd
results = why.log(pd.read_csv("train_shard.csv"))
summary = results.view().to_pandas()     # per-column stats
```
(Source: https://pypi.org/project/whylogs/. The `view().to_pandas()` call is from the whylogs docs **[UNVERIFIED this session]**.)
- **Status:** WhyLabs' hosted platform was **discontinued**, and the platform code was released as open source (github.com/whylabs). Reports from 2025 (GeekWire, https://www.geekwire.com/2025/founders-at-seattle-startup-whylabs-join-apple-following-under-the-radar-acquisition) say **Apple** hired founders and staff and licensed the IP. Neither company has officially confirmed this. Teaching point: *managed observability vendors can vanish, so keep contracts and profiles in open formats.*

### 6.4 Drift for LLM/RAG data specifically
- Track drift on **descriptors** rather than raw text: length, language, toxicity score, topic or taxonomy leaf, retrieval-hit rate, refusal rate. Then apply PSI/JS to those descriptors (Evidently explicitly supports text descriptors plus numeric/categorical tests).
- **Embedding drift** between the RAG corpus and live queries shows when users ask about things the index does not cover. This connects back to coverage holes (section 4).
- **Train/serve skew vs. temporal drift**: compare SFT data against production prompts (skew), and production week N against week N-1 (drift).

---

## 7. End-to-end flow (diagram in words)

```
[1 Requirements + risk register]
      -> [2 Taxonomy & slices]  (coverage targets per leaf, min eval n)
      -> [3 Contract v1]  ODCS/Soda/Pandera: schema + semantics + SLAs (+owner)
      -> [4 Generate/collect]  per leaf (synthetic + human + logs)
      -> [5 CI gate]  contract test + breaking-change check (dbt / datacontract breaking)
      -> [6 Coverage & slice report]  heatmap; fill holes -> back to 4
      -> [7 Train/eval]  per-slice metrics
      -> [8 Monitor]  PSI/JS/KS on descriptors + embedding drift vs reference
      -> [9 Quality card]  Data Card / HF card + Croissant-RAI JSON-LD, versioned with the data
      -> loop: drift alert or new slice -> taxonomy update -> contract v2
```

---

## 8. Real-world examples
- **Google**: Data Cards Playbook built from **40+ Data and Model Cards deployed at Google**; FAccT'22 paper reports 20+ deployed cards. Source: Playbook site and paper.
- **Hugging Face Hub**: README dataset cards with YAML metadata are the default format for open datasets. Croissant JSON-LD is auto-served per dataset. In 2026 the Hub added **RL-environment dataset tags** (e.g. Terminal-Bench 2.0 example with `harbor`, `verifiers`).
- **Kaggle, OpenML, Google Dataset Search**: Croissant export and indexing.
- **dbt Mesh** users: model contracts plus versioning as cross-team interfaces.
- **GoCardless**: Andrew Jones popularized "data contracts" around 2021 and later wrote *Driving Data Quality with Data Contracts* (Packt, 2023). **[UNVERIFIED this session]**
- **EU AI Act Art. 10**: forces documented design choices, provenance, preparation steps, assumptions and bias examination. Data Cards and datasheets map almost one-to-one onto para. 2(a)-(f).
- **Data Provenance Initiative**: the 70%+ license omission rate shows why provenance fields in cards and contracts are not optional.

---

## 9. Open challenges (Oct 2026)
1. **Documentation decay**: cards are written once and go stale. The Playbook itself warns it "may not reflect current approaches". Cards need CI regeneration from contracts and profiles.
2. **Synthetic-data provenance**: which model, prompt, seed and filter produced each row? Neither Datasheets nor most contracts have first-class fields for generator lineage. Croissant 1.1 provenance and ODCS AI-context work are early attempts.
3. **Semantics beyond schema**: contracts check types and ranges well, but not *meaning* (e.g. "the response is grounded in the cited doc"). LLM-judge checks inside contracts are emerging but non-deterministic.
4. **Drift statistics at LLM scale**: p-value tests flag everything at large n. Distance thresholds such as PSI 0.1/0.25 are heuristics inherited from credit risk. Embedding drift depends on the embedding model and is hard to explain.
5. **Taxonomy design is subjective**: different taxonomies give different "coverage". There is no standard taxonomy for agent/tool-use skills.
6. **Slice explosion and multiple testing**: thousands of slices produce false alarms. Discovery methods like Domino find only ~36% of planted slices.
7. **Vendor risk**: WhyLabs' hosted shutdown shows why open formats (ODCS, Croissant, whylogs profiles) matter.
8. **Regulatory alignment**: mapping Art. 10 "sufficiently representative" to measurable coverage metrics is unresolved.

---

## 10. Quotable lines (with source)
- "every component, no matter how simple or complex, is accompanied with a datasheet" (Gebru et al., Datasheets for Datasets, arXiv:1803.09010)
- "Data Cards are structured summaries of essential facts about various aspects of ML datasets" (Data Cards Playbook)
- "Co-create transparency with stakeholders from across the dataset lifecycle." (Data Cards Playbook)
- Datasets must be "relevant, sufficiently representative, and to the best extent possible, free of errors and complete" (EU AI Act Art. 10(3))
- "license omission of 70%+ and error rates of 50%+" (Longpre et al., arXiv:2310.16787)

---

## 11. Slide ideas (8)
1. **"The dataset is the spec"**: three stacked layers (Doc card -> Croissant JSON-LD -> executable contract) that animate in as people / machines / CI. Visual: a pyramid with the reader icon for each layer.
2. **Datasheets -> Data Cards -> Croissant-RAI timeline (2018-2026)**: a horizontal timeline with paper thumbnails. Then a zoom on the Playbook's 4 modules (Ask/Inspect/Answer/Audit) as a cycling wheel.
3. **Anatomy of a data contract**: split screen with the Soda YAML on the left and four highlighted bands (schema / semantics / SLA / owner) that light up in sequence. On the right, a CI pipeline turning red on `datacontract breaking`.
4. **Tool matrix**: a 2x2 with axes "in-code vs. warehouse" and "validation vs. monitoring", placing Pandera, GX, Soda, dbt, ODCS, Evidently and whylogs. Animate the logos dropping into quadrants.
5. **Taxonomy coverage heatmap**: a tree (GLAN-style fields -> disciplines -> concepts) unfolds into a leaf x split heatmap, and empty cells pulse red as "holes". Show the formula for leaf coverage and normalized entropy.
6. **Slices: declared vs. discovered**: a Venn diagram, with Slice Finder (interpretable predicates) and Domino (embedding clusters plus NL names, 36% / 1,235 settings) as callouts. End on a slice-gate YAML.
7. **Drift metrics side by side**: one pair of histograms (reference vs. current) with PSI, KS (CDF gap highlighted as the max vertical distance), JS and Wasserstein all computed on it. Animate the CDF gap for KS. Add a table of Evidently defaults by n.
8. **Embedding drift for RAG**: a 2-D UMAP of the corpus vs. live queries, with query clusters outside the corpus hull lighting up. Annotate the domain-classifier AUC of 0.55 threshold.
9. **The closed loop**: the 9-step lifecycle circle from section 7, with the drift alert arrow feeding back to taxonomy and contract v2.
10. **Open challenges**: 8 cards that flip to reveal "why it's hard" (synthetic provenance, semantic checks, p-value explosion, vendor risk).

---

## 12. Source list (exact titles + URLs)
- Datasheets for Datasets: https://arxiv.org/abs/1803.09010
- Data Cards: Purposeful and Transparent Dataset Documentation for Responsible AI: https://arxiv.org/abs/2204.01075
- The Data Cards Playbook: https://sites.research.google/datacardsplaybook/
- The Data Cards Playbook: A Toolkit for Transparency in Dataset Documentation (blog): https://research.google/blog/the-data-cards-playbook-a-toolkit-for-transparency-in-dataset-documentation/
- Dataset Cards (HF Hub docs): https://huggingface.co/docs/hub/datasets-cards
- mlcommons/croissant (GitHub): https://github.com/mlcommons/croissant
- Croissant: A Metadata Format for ML-Ready Datasets: https://arxiv.org/abs/2403.19546
- A Standardized Machine-readable Dataset Documentation Format for Responsible AI: https://arxiv.org/abs/2407.16883
- Croissant 1.1 (ODI): https://theodi.org/news-and-events/blog/croissant-11/
- Try GX Core: https://docs.greatexpectations.io/docs/core/introduction/try_gx | PyPI great-expectations 1.24.1: https://pypi.org/project/great-expectations/
- pandera 0.34.1: https://pypi.org/project/pandera/
- Soda v4 docs (contracts, verify): https://docs.soda.io/
- Model contracts, dbt Developer Hub: https://docs.getdbt.com/docs/mesh/govern/model-contracts
- ODCS v3.1.0 announcement: https://bitol.io/bitol-announces-odcs-v3-1-0-stronger-smarter-and-stricter/
- datacontract-cli: https://github.com/datacontract/datacontract-cli
- Evidently 0.7.23: https://pypi.org/project/evidently/ ; Customize data drift: https://docs.evidentlyai.com/metrics/customize_data_drift ; Embedding drift: https://docs.evidentlyai.com/metrics/customize_embedding_drift
- whylogs 1.6.4: https://pypi.org/project/whylogs/ ; WhyLabs/Apple report: https://www.geekwire.com/2025/founders-at-seattle-startup-whylabs-join-apple-following-under-the-radar-acquisition
- #InsTag: https://arxiv.org/abs/2308.07074
- GLAN, Synthetic Data (Almost) from Scratch: https://arxiv.org/abs/2402.13064
- Slice Finder / Automated Data Slicing for Model Validation: https://arxiv.org/abs/1807.06068
- Domino: Discovering Systematic Errors with Cross-Modal Embeddings: https://arxiv.org/abs/2203.14960
- The Data Provenance Initiative: https://arxiv.org/abs/2310.16787
- EU AI Act Article 10: https://artificialintelligenceact.eu/article/10/
