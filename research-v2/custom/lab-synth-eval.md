# Hands-on labs: synthetic data with verification + eval design in code

Deck: *Customizing modern AI (SFT, RL, RAG) and data-centric AI, October 2026*. Research date: 2026-10-23.
Subtopic: generate, verify (execution, unit tests, judge), filter (distilabel); RAG eval sets (ragas); slice metrics; bootstrap CIs; calibration (ECE); cost-sensitive thresholds from a cost matrix; LLM-judge agreement; quality card.

This file adds to `research-custom/06-llm-rag-datasets-synthetic.md` and `07-eval-design.md`. Those files have the theory and short snippets. Here you get 9 complete labs. Each lab is a named business scenario with code you can run, the commands, the output, the errors you will hit and their fixes.

---

## 0. Ground truth for this file

### 0.1 Library versions (PyPI JSON, fetched 2026-10-23)

| Package | Latest | Uploaded | Requires-Python | Used in |
|---|---|---|---|---|
| distilabel | **1.5.3** | 2025-01-28 | >=3.9 | Lab 1 |
| ragas | **0.4.3** | 2026-01-13 | >=3.9 | Lab 2 |
| openai | **3.37.0** | 2026-10-22 | >=3.10 | Labs 1, 2 |
| langchain-openai / langchain-core | 1.7.2 / 1.7.0 | 2026-10-14 / 10-22 | | Lab 2 |
| numpy | **2.5.4** | 2026-10-10 | **>=3.12** | all |
| scipy | **1.18.1** | 2026-08-21 | **>=3.12** | Lab 4 |
| scikit-learn | **1.9.1** | 2026-09-10 | >=3.11 | Labs 5-8 |
| pandas | **3.1.0** | 2026-10-22 | >=3.11 | Labs 3, 9 |
| statsmodels | **0.15.0** | 2026-08-27 | >=3.10 | Labs 3, 4, 9 |
| krippendorff | **0.9.0** | 2026-10-07 | >=3.11 | Lab 8 |
| datasets | 5.1.0 | 2026-10-05 | >=3.10 | Lab 1 (via distilabel) |

**Use Python 3.12 or later.** numpy 2.5 and scipy 1.18 need 3.12. That is the first gotcha for a room of laptops.

### 0.2 What was run, and what was not

- **Labs 3-9 were run on this machine.** Their outputs below are **real**. The machine has older versions installed: Python 3.12.3, numpy 1.26.4, scipy 1.11.4, scikit-learn 1.8.0, pandas 2.1.4, statsmodels 0.14.6. For krippendorff 0.9.0, I used the source from the v0.9.0 tag (pure numpy) because pip downloads are blocked here. With the latest pins, digits can change a little.
  - Lab 4 is the one exception. scipy 1.11 does not accept `rng=`, so I ran a copy with `random_state=rng`. See the Lab 4 errors.
  - Everything the labs use (`method="temperature"`, `FrozenEstimator`, `confusion_matrix_at_thresholds`, `TunedThresholdClassifierCV`) exists in both 1.8.0 and 1.9.1. I checked the 1.9.1 source.
- **Labs 1-2 call paid LLM APIs and were not run.** Their outputs are marked **ILLUSTRATIVE**. I checked every import, class, parameter and default against the tagged source on GitHub (citations inline). I did run the Lab 1 verifier function (`run_tests`) locally with a passing candidate, a failing one and an infinite loop. It returned `(True, '')`, `(False, 'AssertionError')` and `(False, 'timeout')`.

### 0.3 Maintenance status (state this on a slide)

- **distilabel**: the last PyPI release is 1.5.3 (2025-01-28). The README now opens with: *"The original authors have moved on to other projects. A group of community members have recently joined the GitHub project as collaborators... Check out the `develop` branch for access to the latest fixes."* The last commit on `main` is 2025-12-15. Teach the *pattern* (generate, verify, filter), and treat the library as replaceable. Lab 1 keeps the verifier in a plain function for that reason.
- **ragas 0.4.3**: `LangchainLLMWrapper` is deprecated in code (`src/ragas/llms/__init__.py`): *"LangchainLLMWrapper is deprecated and will be removed in a future version. Use llm_factory instead."* The 0.4.3 testset docs (`docs/extra/components/choose_generator_llm.md`) still use `LangchainLLMWrapper(ChatOpenAI(...))`. Lab 2 follows the docs and you will see a deprecation warning.
- **openai 3.0.0 (2026-08-12)**, breaking change: *"HTTPX2 is now the default HTTP client, and `httpx` is no longer installed automatically."* (CHANGELOG.md). distilabel 1.5.3 declares `httpx >= 0.25.2` itself, so `httpx` still gets installed. Nobody has tested distilabel 1.5.3 with openai 3.x [UNVERIFIED]. If Lab 1 fails inside the OpenAI client, pin `"openai>=2.54,<3"`.

### 0.4 arXiv insights from the last 3 months (2026-07-23 .. 2026-10-23), mapped to labs

From the arXiv API (sorted by submittedDate). Every claim below is quoted or paraphrased from the abstract only.

| Paper | Date | What it says (abstract) | Lab |
|---|---|---|---|
| **Cost-Aware Abstention for LLM-Based IT Ticket Classification**, arXiv:2610.31657 | 2026-10-22 | Cost model (c_ok, c_triage, c_wrong) = (0, 1, 5). Select the policy on calibration data, freeze it, and evaluate once on test. TF-IDF+LR at threshold 0.60 cuts test cost from 0.763 to 0.472 (-38.1%, paired ratio-bootstrap 95% CI [35.7%, 40.4%]) and wrong routes from 15.3% to 3.5%. Isotonic "lowers expected calibration error without reliably improving discrimination". GPT-4o-mini few-shot has "correctness AUROC 0.500". At break-even 0.80, "seven prompted configurations defer all tickets". | 5, 7 |
| **Three Ways Classical Test Theory Can Mislead About LLM Judges**, arXiv:2609.29709 | 2026-08-31 | KR-20 was 0.5223 on the judge's verdicts and 0.5231 on error-free gold verdicts. Reliability stats with no gold labels "cannot isolate the judge". "A statement about the judge therefore needs gold labels or a varied scorer facet." | 8 |
| **All Verdicts are Not Equal: Rethinking LLM Judge Reliability**, arXiv:2610.12083 | 2026-10-08 | Verdicts change "across identical replications at temperature zero". Position swaps "flip the majority of verdicts on challenging tasks". The most deterministic judge agrees with ground truth "only 51% of the time". Holistic rubric scoring beats pairwise win-rate. | 8 |
| **The First Token Is Not the Verdict**, arXiv:2610.00054 | 2026-09-04 | Reading a judge's verdict from first-token logits overstates position bias. Forced reads flip on 89.7% of non-committed pairs vs 47.5% after generation (paired diff +0.422, 95% CI [+0.365, +0.467]). | 8 |
| **Pair Difficulty Matters**, arXiv:2609.37577 | 2026-09-29 | Position-bias, transitivity and agreement proxies are dominated by close-rank-gap pairs. Assess judges "on rank-gap-conditional metrics". | 8 |
| **A Shared Taste for Model-Written Text**, arXiv:2610.00369 | 2026-09-30 | No detectable own-model premium (pooled +0.019, 95% interval -0.008 to 0.046). "Position bias moves single cells by up to 0.42 share points." | 8 |
| **Calibrating LLM Judges for Human and AI Conversations**, arXiv:2609.29431 | 2026-09-24 | A small anchor set and a calibration function put any judge "onto a shared, interpretable scale". | 8 |
| **SafeLLM4SE: Statistical Evaluation and Reporting**, arXiv:2609.37294 | 2026-09-29 | A single output, mean, best-of-N or pass@k "can obscure variability". Proposes CIs, effect sizes and a minimum reporting standard (PyPI package; name not checked) [UNVERIFIED package name]. | 4, 9 |
| **Speculative Evaluation of Stochastic LLMs**, arXiv:2609.28560 | 2026-09-23 | Neyman allocation of rollouts cuts the variance of the benchmark mean by 12.8%-33.6% vs uniform repetition. | 4 |
| **Beyond Pass@k**, arXiv:2608.14711 | 2026-08-11 | Many harnesses misapply pass@k (n = number of unit tests instead of independent rollouts). That inflates scores by 0.85-0.97 absolute. SWE-bench pilot: hidden-test pass rate 0.80 vs strict resolution 0.20. | 1, 4 |
| **Claim-Level Confidence Calibration**, arXiv:2608.22483 | 2026-08-23 | Decompose answers into atomic claims and calibrate each claim post-hoc. This "reduces expected calibration error" but fails on false-premise questions. | 5 |
| **Outcome-Grounded Confidence Calibration in LLM Agents**, arXiv:2610.18614 | 2026-10-13 | GRPO plus a proper scoring rule against the episode outcome: ECE "from 0.42 to below 0.12" on ALFWorld. | 5 |
| **GRADS: Graph-Regulated Agentic Data Synthesis**, arXiv:2610.21167 | 2026-10-15 | A closed loop: seed, evidence expansion, QA construction, **verification**. Seed expansion often adds evidence "only weakly coupled to the answer". | 1, 2 |
| **WinSyn: Realistic Enterprise QA Evaluation**, arXiv:2609.12171 | 2026-09-10 | Synthetic enterprise email corpora with grounded gold answers. Frontier agentic baselines stay "below 80%". | 2 |
| **The Bottleneck Is Retrieval, Not Reading**, arXiv:2610.26951 | 2026-10-18 | Similarity retrieval finds *any* relevant chunk far more reliably than *all* required chunks for multi-fact queries. Answer-only eval hides grounding failures. | 2 |
| **SynthSentry: Detecting Synthetic Data Contamination**, arXiv:2609.12353 | 2026-09-11 | A corpus-level synthetic-contamination score. A naive quantile threshold "runs four times over budget" on false positives. A bootstrap threshold fixes it. | 1, 9 |

---

## Lab 1: Refund-agent tool code. Generate K candidates, execute unit tests, keep or pair (distilabel)

> **Verifier (2026-10-23):** VERIFIED against distilabel 1.5.3 source (`distilabel.models.OpenAILLM`, `distilabel.steps.{LoadDataFromDicts, StepInput, step}`, `distilabel.steps.tasks.TextGeneration`, `distilabel.typing.StepOutput`, `max_new_tokens` -> `max_tokens`, `group_generations=False`). `run_tests` re-run by the verifier: `(True,'')`, `(False,'AssertionError')`, `(False,'timeout')`. LLM part not run (needs API key).

**Goal.** Build SFT data, plus DPO pairs if you want them, for the Python tools a refund agent calls (`refund_amount`, `is_refund_eligible`). The LLM writes 4 candidates per spec. Each candidate runs against hidden unit tests in a fresh subprocess. You keep only the ones that pass. This is the Llama 3 "execution feedback" pattern (see 06 §5) in about 60 lines.

**Adapted from:** distilabel "Quickstart" (https://distilabel.argilla.io/latest/sections/getting_started/quickstart/) and "Define Steps for your Pipeline" (`docs/sections/how_to_guides/basic/step/index.md`, tag 1.5.3). Both are verified at tag 1.5.3.

**Prerequisites**
```bash
python -m venv .venv-synth && . .venv-synth/bin/activate        # Windows: .venv-synth\Scripts\activate
pip install "distilabel[openai]==1.5.3" "openai==3.37.0"        # fallback if client errors: "openai>=2.54,<3"
export OPENAI_API_KEY=sk-...                                     # read by distilabel (base_clients/openai.py:27,39)
export GEN_MODEL=gpt-4.1-mini        # any NON-reasoning chat model; see error 3. Availability [UNVERIFIED]
# Local alternative (OpenAI-compatible): export OPENAI_BASE_URL=http://localhost:11434/v1  GEN_MODEL=qwen2.5-coder:7b
```

**Code: `lab1_refund_exec_verify.py`** (60 lines)
```python
"""Lab 1 - Refund agent tool code: generate K candidates -> execute unit tests -> keep / pair."""
import os
import re
import subprocess
import sys
import tempfile

from distilabel.models import OpenAILLM
from distilabel.pipeline import Pipeline
from distilabel.steps import LoadDataFromDicts, StepInput, step
from distilabel.steps.tasks import TextGeneration
from distilabel.typing import StepOutput

SEEDS = [
    {"spec": "def refund_amount(price: float, days_since_delivery: int, opened: bool) -> float:\n"
             "Full refund within 30 days if unopened; 85% (15% restocking fee) if opened; 0 after 30 days. "
             "Round to 2 decimals.",
     "tests": "assert refund_amount(100, 10, False) == 100\nassert refund_amount(100, 10, True) == 85\n"
              "assert refund_amount(100, 31, False) == 0\nassert refund_amount(19.99, 30, True) == 16.99"},
    {"spec": "def is_refund_eligible(order_status: str, amount: float) -> bool:\n"
             "Eligible only if status is 'delivered' or 'returned' (case-insensitive) and 0 < amount <= 5000.",
     "tests": "assert is_refund_eligible('Delivered', 20)\nassert not is_refund_eligible('shipped', 20)\n"
              "assert not is_refund_eligible('returned', 0)\nassert not is_refund_eligible('returned', 5000.01)"},
]
TEMPLATE = "Write only the Python function below, no tests, no prose, in one ```python block.\n{{ spec }}"


def run_tests(code: str, tests: str, timeout: int = 5) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory() as tmp:                      # fresh dir per candidate
        path = os.path.join(tmp, "candidate.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code + "\n\n" + tests + "\n")
        try:
            r = subprocess.run([sys.executable, "-I", path], cwd=tmp, capture_output=True,
                               text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return False, "timeout"
    return r.returncode == 0, r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ""


@step(inputs=["generation", "tests"], outputs=["code", "passed", "error"])
def ExecuteUnitTests(inputs: StepInput) -> StepOutput:
    for row in inputs:
        m = re.search(r"```(?:python)?\n(.*?)```", row["generation"] or "", re.S)
        row["code"] = m.group(1) if m else (row["generation"] or "")
        row["passed"], row["error"] = run_tests(row["code"], row["tests"])
    yield inputs


with Pipeline(name="refund-tools-exec-verify") as pipeline:
    seeds = LoadDataFromDicts(data=SEEDS)
    gen = TextGeneration(
        llm=OpenAILLM(model=os.getenv("GEN_MODEL", "gpt-4.1-mini"),
                      generation_kwargs={"temperature": 0.9, "max_new_tokens": 512}),
        template=TEMPLATE, columns=["spec"], num_generations=4)
    verify = ExecuteUnitTests()
    seeds >> gen >> verify

if __name__ == "__main__":
    ds = pipeline.run(use_cache=False)["default"]["train"]
    sft = ds.filter(lambda r: r["passed"])
    print(f"candidates={len(ds)}  passed={len(sft)}  pass-rate={len(sft) / len(ds):.0%}")
    for r in ds.filter(lambda r: not r["passed"]).select_columns(["spec", "error"]).to_list()[:3]:
        print("REJECTED:", r["spec"].splitlines()[0], "->", r["error"])
    sft.select_columns(["spec", "code"]).to_json("refund_tools_sft.jsonl")
```

**Run**
```bash
python lab1_refund_exec_verify.py
head -c 400 refund_tools_sft.jsonl
```

**Expected output (ILLUSTRATIVE: not run, needs an API key)**
```
... distilabel progress logs (pipeline 'refund-tools-exec-verify', 3 steps) ...
candidates=8  passed=6  pass-rate=75%
REJECTED: def refund_amount(price: float, days_since_delivery: int, opened: bool) -> float: -> AssertionError
REJECTED: def is_refund_eligible(order_status: str, amount: float) -> bool: -> AssertionError
```
(8 rows = 2 seeds x `num_generations=4`. `group_generations` defaults to `False`, which makes one row per generation: `steps/tasks/base.py` lines 460-471 at tag 1.5.3.)

**Key lines walk-through**
1. `from distilabel.steps import LoadDataFromDicts, StepInput, step`: all three are exported in `src/distilabel/steps/__init__.py` (1.5.3). `step` is defined at `steps/decorator.py:51-74`, with `step_type` one of `"normal"|"global"|"generator"`.
2. `@step(inputs=["generation", "tests"], outputs=[...])`: the DAG checks that every input column is produced upstream. `tests` comes from `LoadDataFromDicts.outputs`, which returns `list(self.data[0].keys())` (`steps/generators/data.py:86-89`). `generation` comes from `TextGeneration.format_output` (`text_generation.py:276-281`).
3. `TextGeneration(template=..., columns=["spec"])`: `template` is Jinja2. Each name in `columns` must appear in the template, or `check_column_in_template` fails (`text_generation.py:191-223`).
4. `num_generations=4`: a `Task` runtime parameter, default 1 (`steps/tasks/base.py:78-80`). Do not confuse this with pass@k: see arXiv:2608.14711. Here n = independent samples, which is the correct use.
5. `subprocess.run([sys.executable, "-I", path], cwd=tmp, timeout=...)`: `-I` (isolated mode) ignores `PYTHON*` env vars and the user site dir. A fresh `TemporaryDirectory` stops a candidate from reading or overwriting another candidate's files. The timeout catches `while True`.
6. `pipeline.run(use_cache=False)["default"]["train"]`: the `Distiset` names the single leaf `"default"` (`distiset.py:721-723`). `use_cache=False` forces new generations. Without it, the second run silently re-serves cached rows.

**Common errors**
1. `ValueError: To use `OpenAILLM` an API key must be provided via `api_key` attribute or runtime parameter, or set the environment variable `OPENAI_API_KEY`.` (`base_clients/openai.py:77-81`). **Fix:** export `OPENAI_API_KEY`. For a local server, set any non-empty string.
2. `DistilabelUserError: Step 'execute_unit_tests_0' should have a parameter with type hint `StepInput` to receive the output from the previous step: 'text_generation_0'.` (`pipeline/_dag.py:612-615`; the step-name format is [UNVERIFIED]). **Cause:** you quoted the hint (`"StepInput"`), imported it under `TYPE_CHECKING`, or added `from __future__ import annotations`, which turns every hint into a string. The step docs say the hints "should be used and not surrounded with double-quotes or imported under `typing.TYPE_CHECKING`, otherwise, the validation and/or serialization will fail". **Fix:** use a plain import and a plain annotation.
3. A 400 error from reasoning models (o-series, GPT-5.x), for example *"Unsupported parameter: 'max_tokens' ... Use 'max_completion_tokens' instead"* [exact wording UNVERIFIED]. **Cause:** `OpenAILLM` always sends `max_tokens`, `frequency_penalty`, `presence_penalty`, `top_p` and `temperature` (`models/llms/openai.py:319-331`). **Fix:** use a non-reasoning chat model, or an OpenAI-compatible local server (vLLM, Ollama) through `OPENAI_BASE_URL` (`base_clients/openai.py:32-35`).
4. `ValueError: Step 'execute_unit_tests_0' requires inputs ['generation', 'tests'], but only the inputs=[...] are available ...` (`_dag.py:438-445`). **Cause:** a typo in a column name, or a seed dict without `tests`. **Fix:** make every seed dict carry the same keys. Only the **first** dict's keys define the outputs.

**Best practice.** Run verifiers in order of cost: parse, then execute, then judge. Log *why* each candidate was rejected (the `error` column). The rejection histogram is your data-quality dashboard. A pass rate near 100% means the tests are too weak. Mutation-test them (see the variation).

**Variation / extension**
- *DPO pairs:* group `ds` by `spec` and pair a passing `code` (chosen) with a failing one (rejected). Then `FormatTextGenerationDPO` (exported in `steps/__init__.py`) or TRL's `DPOTrainer` can consume the result.
- *Stronger tests:* mutate the reference (`<=` to `<`, `0.85` to `0.8`) and require the tests to fail on every mutant before you trust them. *Judge as a 3rd verifier:* add a second `TextGeneration` with a rubric template ("Does the code handle negative price? YES/NO") on rows that passed execution only, since judges cost more than tests.
- *Production sandbox:* replace `subprocess` with a container with no network, as Llama 3 did (06 §5).

---

## Lab 2: HR policy search. Synthesize a RAG eval set with ragas, then verify it before use

> **Verifier (2026-10-23):** VERIFIED against ragas 0.4.3 source and docs (`TestsetGenerator`, `generate_with_langchain_docs`, `LangchainLLMWrapper` deprecation helper, `ragas.embeddings.OpenAIEmbeddings(client=)` exactly as in `choose_generator_llm.md`). Still UNVERIFIED: `OpenAIEmbeddings` is a `BaseRagasEmbedding` while `TestsetGenerator.embedding_model` is typed `BaseRagasEmbeddings`; runtime compatibility not tested.

**Goal.** Generate 40 question/answer/context triples from internal HR policy docs (PTO, parental leave, expenses). Then reject three kinds of rows: (a) the reference answer is not grounded in its contexts, (b) the question is answerable without retrieval (closed-book leak), (c) the question near-duplicates a kept one. Write a content-hashed, versioned JSONL file.

**Adapted from:** ragas "Testset Generation for RAG" (`docs/getstarted/rag_testset_generation.md`, tag v0.4.3; https://docs.ragas.io/en/stable/getstarted/rag_testset_generation/). The verification part is this deck's addition. It follows the checklist in 06 §7.

**Prerequisites**
```bash
python -m venv .venv-rag && . .venv-rag/bin/activate          # separate venv from Lab 1 (datasets pins differ)
pip install "ragas==0.4.3" "langchain-openai==1.7.2" "openai==3.37.0"
export OPENAI_API_KEY=sk-...  GEN_MODEL=gpt-4.1  JUDGE_MODEL=gpt-4.1-mini   # model availability [UNVERIFIED]
export RAGAS_DO_NOT_TRACK=true          # ragas sends usage analytics unless this is "true" (_analytics.py:41-49)
mkdir hr_policies   # put 5+ markdown policies here, EACH > 500 tokens (see error 1)
```
ragas 0.4.3 depends on `langchain`, `langchain-core`, `langchain-community`, `langchain_openai`, `instructor` and `datasets>=4.0.0` (pyproject.toml, tag v0.4.3). Compatibility with langchain-core 1.7 is [UNVERIFIED].

**Code: `lab2_hr_rag_testset.py`** (50 lines)
```python
"""Lab 2 - HR policy search: synthesize a RAG eval set with ragas, then VERIFY before use."""
import collections, difflib, glob, hashlib, json, os

from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from openai import OpenAI
from ragas.embeddings import OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.testset import TestsetGenerator

JUDGE = os.getenv("JUDGE_MODEL", "gpt-4.1-mini")
client = OpenAI()
docs = [Document(page_content=open(p, encoding="utf-8").read(), metadata={"source": p})
        for p in sorted(glob.glob("hr_policies/*.md"))]          # e.g. pto.md, parental_leave.md

generator = TestsetGenerator(llm=LangchainLLMWrapper(ChatOpenAI(model=os.getenv("GEN_MODEL", "gpt-4.1"))),
                             embedding_model=OpenAIEmbeddings(client=client))
rows = generator.generate_with_langchain_docs(docs, testset_size=40).to_list()


def ask_judge(prompt: str) -> str:
    out = client.chat.completions.create(model=JUDGE, temperature=0, messages=[
        {"role": "user", "content": prompt + '\nReply as JSON: {"verdict": "YES" or "NO"}'}],
        response_format={"type": "json_object"})
    return json.loads(out.choices[0].message.content)["verdict"]


kept, dropped = [], collections.Counter()
for r in rows:
    ctx = "\n---\n".join(r["reference_contexts"])
    if ask_judge(f"Context:\n{ctx}\n\nIs every fact in this answer stated in the context?\n"
                 f"Answer: {r['reference']}") != "YES":
        dropped["reference not grounded"] += 1; continue
    closed_book = client.chat.completions.create(model=JUDGE, temperature=0, messages=[
        {"role": "user", "content": r["user_input"]}]).choices[0].message.content
    if ask_judge(f"Reference: {r['reference']}\nCandidate: {closed_book}\n"
                 "Does the candidate state the same specific facts as the reference?") == "YES":
        dropped["answerable without retrieval"] += 1; continue
    if any(difflib.SequenceMatcher(None, r["user_input"].lower(), k["user_input"].lower()).ratio() > 0.9
           for k in kept):
        dropped["near-duplicate question"] += 1; continue
    kept.append(r)

blob = "\n".join(json.dumps(r, sort_keys=True) for r in kept)
version = hashlib.sha256(blob.encode()).hexdigest()[:12]
with open(f"hr_rag_eval_{version}.jsonl", "w", encoding="utf-8") as f:
    f.write(blob + "\n")
print(f"generated={len(rows)} kept={len(kept)} dropped={dict(dropped)}")
print("synthesizer mix:", collections.Counter(r["synthesizer_name"] for r in kept))
print(f"wrote hr_rag_eval_{version}.jsonl  -> send 10% to an HR reviewer before first use")
```

**Run**
```bash
python lab2_hr_rag_testset.py
```

**Expected output (ILLUSTRATIVE: not run)**
```
DeprecationWarning: LangchainLLMWrapper is deprecated and will be removed in a future version. Use llm_factory instead: ...
Applying HeadlinesExtractor: 100%|...|   (knowledge-graph transforms, then scenario + sample generation)
generated=40 kept=29 dropped={'answerable without retrieval': 6, 'reference not grounded': 3, 'near-duplicate question': 2}
synthesizer mix: Counter({'single_hop_specific_query_synthesizer': 16, 'multi_hop_specific_query_synthesizer': 7, 'multi_hop_abstract_query_synthesizer': 6})
wrote hr_rag_eval_3f9c0a1b2d4e.jsonl  -> send 10% to an HR reviewer before first use
```
The synthesizer names are verified (`name: str = "single_hop_specific_query_synthesizer"` etc. in `testset/synthesizers/single_hop/specific.py:42`, `multi_hop/abstract.py:35`, `multi_hop/specific.py:33`). The default mix is 0.5 / 0.25 / 0.25 (`default_query_distribution`, `testset/synthesizers/__init__.py:24-33`).

**Key lines walk-through**
1. `TestsetGenerator(llm=..., embedding_model=...)`: a dataclass with fields `llm`, `embedding_model`, `knowledge_graph`, `persona_list`, `llm_context` (`testset/synthesizers/generate.py:55-75`).
2. `OpenAIEmbeddings(client=client)`: `__init__(self, client, model="text-embedding-3-small", ...)` (`embeddings/openai_provider.py:21-24`). It auto-detects a sync or async client.
3. `generate_with_langchain_docs(docs, testset_size=40)`: signature at `generate.py:114-127`. Pass `query_distribution=` to rebalance toward the single-hop/multi-hop mix of your real query logs.
4. `.to_list()`: each row is `eval_sample.model_dump(exclude_none=True)` plus `synthesizer_name` (`testset_schema.py:69-77`). Keys come from `SingleTurnSample`: `user_input`, `reference_contexts`, `reference`, `persona_name`, `query_style`, `query_length` (`dataset_schema.py:54-82`).
5. The closed-book check: if a model answers correctly *without* retrieval, the item measures parametric memory, not your RAG system. Drop it, or tag it as a separate slice.
6. `hashlib.sha256(...)[:12]` in the file name: the eval set is immutable and addressable. The quality card (Lab 9) cites this hash.

**Common errors**
1. `ValueError: Documents appears to be too short (ie 100 tokens or less). Please provide longer documents.` (`testset/transforms/default.py:163-164`). `default_transforms` bins documents by token length: (0,100), (101,500), (501,inf). **Fix:** merge short FAQ entries into longer docs, or chunk them yourself and call `generate_with_chunks(...)` (`generate.py:302`), which uses `default_transforms_for_prechunked`.
2. `ValueError: No relationships match the provided condition. Cannot form clusters.` (`testset/graph.py:530`). Multi-hop synthesizers need related nodes, and with 1-2 docs there are none. **Fix:** use more and overlapping docs, or pass `query_distribution=[(SingleHopSpecificQuerySynthesizer(llm=llm), 1.0)]`.
3. `ValueError: No nodes found with the `entities` property.` (`single_hop/specific.py:135`). The extractors produced nothing, usually because the docs were filtered out by the 500-token / 100-token `filter_nodes` rules (`default.py:68-71`). **Fix:** same as error 1.
4. `DeprecationWarning: LangchainLLMWrapper is deprecated...`. This is not fatal. If you move to `llm_factory('...', client=OpenAI())` as the warning suggests, check that `TestsetGenerator` accepts the returned `InstructorBaseRagasLLM`. Its type hint is `BaseRagasLLM` [UNVERIFIED for testset generation in 0.4.3].

**Best practice.** Synthetic eval sets are a *draft*. Gate them like data: grounded, not closed-book answerable, deduplicated, then human-reviewed on a 5-10% sample. Then freeze them by hash and never train on them. arXiv:2610.26951 shows answer-only scoring hides grounding failures, so keep `reference_contexts` and score retrieval recall separately.

**Variation / extension.** Tag each kept item with `persona_name` and `query_style` (both are already in the row) and report Lab 3 slice metrics per persona. Add an "unanswerable" slice: questions about policies that are *not* in the corpus, where the right answer is "I don't know / contact HR".

---

## Lab 3: Insurance-claims extraction agent. Slice metrics with honest error bars

> **Verifier (2026-10-23):** VERIFIED against statsmodels 0.15.0 source (`proportion_confint(..., method="normal")` default).

**Goal.** Report the pass rate per (line of business x language) slice, with Wilson CIs. Show that the overall CI must be computed by **resampling claim files (clusters)**, not individual questions. Flag slices too small to act on.

**Adapted from:** the statsmodels `proportion_confint` API (https://www.statsmodels.org/stable/generated/statsmodels.stats.proportion.proportion_confint.html). Signature verified at tag v0.15.0, `statsmodels/stats/proportion.py:114-116`: `proportion_confint(count, nobs, alpha=0.05, method="normal", alternative="two-sided")`. **The default is `"normal"`, so pass `method="wilson"` explicitly.**

**Prerequisites**
```bash
pip install "numpy==2.5.4" "pandas==3.1.0" "statsmodels==0.15.0"
```

**Code: `lab3_slices.py`** (45 lines)
```python
"""Lab 3 - Insurance-claims extraction agent: slice metrics with honest error bars."""
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportion_confint

rng = np.random.default_rng(7)

# 1) Simulated eval log: 60 claim files (clusters), 3-8 questions per file.
rows = []
for claim_id in range(60):
    line = rng.choice(["auto", "home", "health", "travel"], p=[0.4, 0.3, 0.2, 0.1])
    lang = rng.choice(["en", "es"], p=[0.8, 0.2])
    base = {"auto": 0.90, "home": 0.85, "health": 0.75, "travel": 0.80}[line]
    base -= 0.12 if lang == "es" else 0.0
    claim_effect = rng.normal(0, 0.10)          # some claim files are just harder
    for q in range(rng.integers(3, 9)):
        p = np.clip(base + claim_effect, 0, 1)
        rows.append({"claim_id": claim_id, "line": line, "lang": lang,
                     "passed": int(rng.random() < p)})
df = pd.DataFrame(rows)
df.to_json("claims_eval.jsonl", orient="records", lines=True)


def wilson_table(d: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    g = d.groupby(by)["passed"].agg(k="sum", n="count")
    g["rate"] = g["k"] / g["n"]
    g["lo"], g["hi"] = proportion_confint(g["k"], g["n"], alpha=0.05, method="wilson")
    return g.sort_values("rate")


def cluster_bootstrap_ci(d: pd.DataFrame, B: int = 5000) -> np.ndarray:
    per_claim = d.groupby("claim_id")["passed"].agg(["sum", "count"]).to_numpy()
    idx = rng.integers(0, len(per_claim), size=(B, len(per_claim)))
    s = per_claim[idx]                            # shape (B, n_claims, 2)
    rates = s[..., 0].sum(axis=1) / s[..., 1].sum(axis=1)
    return np.percentile(rates, [2.5, 97.5])


k, n = df["passed"].sum(), len(df)
print(f"overall pass rate {k / n:.3f}  (n={n} items, {df.claim_id.nunique()} claim files)")
print("naive Wilson 95% CI      :", np.round(proportion_confint(k, n, method="wilson"), 3))
print("cluster bootstrap 95% CI :", np.round(cluster_bootstrap_ci(df), 3))
table = wilson_table(df, ["line", "lang"])
print(table.round(3).to_string())
print("slices with n < 30:", [f"{a}/{b}" for a, b in table.query("n < 30").index])
```

**Run:** `python lab3_slices.py`

**Output (REAL, run 2026-10-23 with numpy 1.26.4 / pandas 2.1.4 / statsmodels 0.14.6)**
```
overall pass rate 0.839  (n=353 items, 60 claim files)
naive Wilson 95% CI      : [0.797 0.873]
cluster bootstrap 95% CI : [0.791 0.882]
               k    n   rate     lo     hi
line   lang
health es      9   16  0.562  0.332  0.769
home   es     20   29  0.690  0.508  0.827
travel es      9   13  0.692  0.424  0.873
home   en     61   74  0.824  0.722  0.894
health en     20   24  0.833  0.641  0.933
auto   es      7    8  0.875  0.529  0.978
       en    140  156  0.897  0.840  0.936
travel en     30   33  0.909  0.764  0.969
slices with n < 30: ['health/es', 'home/es', 'travel/es', 'health/en', 'auto/es']
```
Read it like this: the headline 84% hides a Spanish health-claims slice at 56% [33%, 77%]. The naive CI (width 0.076) is about 17% too narrow compared with the cluster bootstrap (width 0.091), because questions from the same claim file are correlated.

**Key lines walk-through**
1. `proportion_confint(g["k"], g["n"], alpha=0.05, method="wilson")`: it is vectorized over Series and returns `(lo, hi)`. Wilson stays inside [0, 1] and behaves for small n or p near 0 or 1. The normal approximation does neither.
2. `groupby(by)["passed"].agg(k="sum", n="count")`: always carry **n** next to the rate. A rate without n is not a metric.
3. `per_claim[idx]` with `idx` of shape (B, n_claims): you resample *clusters* with replacement and recompute the ratio of sums. That is the cluster bootstrap (Miller, arXiv:2411.00640, in 07 §5).
4. `table.query("n < 30")`: an explicit list of slices that are too thin. They go on the quality card as "known gaps", not as conclusions.

**Common errors**
1. `(nan, nan)` plus `RuntimeWarning: invalid value encountered in sqrt` from `proportion_confint(12, 10, method="wilson")` (observed locally). **Cause:** count > nobs, usually from a join that duplicated rows. **Fix:** `assert (g.k <= g.n).all()` and dedup on `item_id` first.
2. A slice CI looks fine at `[0.80, 0.97]`, but that is `method="normal"` (the default) on n=8. **Fix:** always pass `method="wilson"` (or `"beta"` for Clopper-Pearson).
3. `KeyError: 'claim_id'` in `cluster_bootstrap_ci`: your log has no cluster id. **Fix:** log `conversation_id` / `document_id` / `claim_id` in every eval row from day one. You cannot rebuild it later.

**Best practice.** Pre-register the slices (line of business, language, channel, customer tier) *before* looking at results, and set a minimum n per slice (30 here). Slices invented after looking at the results are p-hacking.

**Variation / extension.** Add a Benjamini-Hochberg correction across slices when you test "slice < headline" (`statsmodels.stats.multitest.multipletests(pvals, method="fdr_bh")`; the function name is from statsmodels docs, [UNVERIFIED line]). Or replace simulated data with a real `eval_results.jsonl` from Lab 2's RAG set, using `persona_name` as the slice.

---

## Lab 4: Refund agent v1 vs v2 on the same 400 golden cases. Paired vs unpaired CIs

> **Verifier (2026-10-23):** VERIFIED against scipy 1.18.1 source (`bootstrap(..., method='BCa', rng=None)`).

**Goal.** Decide whether v2 is really better than v1. Both models answered the *same* items, so the comparison must be paired. Compare the unpaired bootstrap, the paired bootstrap, paired BCa and the exact McNemar test, plus the minimum detectable effect (MDE).

**Adapted from:** SciPy `scipy.stats.bootstrap` reference (https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html). Signature verified at tag v1.18.1, `scipy/stats/_resampling.py:300-303`: `bootstrap(data, statistic, *, n_resamples=9999, batch=None, vectorized=None, paired=False, axis=0, confidence_level=0.95, alternative='two-sided', method='BCa', bootstrap_result=None, rng=None)`. `statsmodels.stats.contingency_tables.mcnemar(table, exact=True, correction=True)` is at `contingency_tables.py:1349` (v0.15.0).

**Prerequisites:** `pip install "numpy==2.5.4" "scipy==1.18.1" "statsmodels==0.15.0"`

**Code: `lab4_paired.py`** (34 lines)
```python
"""Lab 4 - Refund agent v1 vs v2 on the SAME 400 golden cases: paired vs unpaired CIs."""
import numpy as np
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar

rng = np.random.default_rng(0)
n = 400
difficulty = rng.normal(0, 1.5, n)                     # shared item difficulty
a = (rng.random(n) < 1 / (1 + np.exp(-(1.3 - difficulty)))).astype(float)  # v1
b = (rng.random(n) < 1 / (1 + np.exp(-(1.6 - difficulty)))).astype(float)  # v2
print(f"v1={a.mean():.3f}  v2={b.mean():.3f}  delta={b.mean() - a.mean():+.3f}")


def diff_of_means(x, y, axis=-1):
    return np.mean(x, axis=axis) - np.mean(y, axis=axis)


common = dict(n_resamples=9999, confidence_level=0.95, method="percentile", rng=rng)
unpaired = stats.bootstrap((b, a), diff_of_means, paired=False, **common)
paired = stats.bootstrap((b, a), diff_of_means, paired=True, **common)
bca = stats.bootstrap((b - a,), np.mean, method="BCa", n_resamples=9999, rng=rng)
for name, r in [("unpaired", unpaired), ("paired", paired), ("paired BCa", bca)]:
    lo, hi = r.confidence_interval
    print(f"{name:11s} 95% CI [{lo:+.3f}, {hi:+.3f}]  width={hi - lo:.3f}  SE={r.standard_error:.4f}")

# McNemar uses only the discordant pairs (v1 right/v2 wrong vs v1 wrong/v2 right).
table = [[np.sum((a == 1) & (b == 1)), np.sum((a == 1) & (b == 0))],
         [np.sum((a == 0) & (b == 1)), np.sum((a == 0) & (b == 0))]]
res = mcnemar(table, exact=True)
print(f"discordant: v1-only={table[0][1]} v2-only={table[1][0]}  McNemar exact p={res.pvalue:.4f}")

# Minimum detectable effect (alpha=0.05, power=0.8) ~ 2.8 * SE(delta)
for name, r in [("unpaired", unpaired), ("paired", paired)]:
    print(f"MDE {name:8s} ~ {2.8 * r.standard_error:.3f}")
```

**Run:** `python lab4_paired.py`

**Output (REAL, run with scipy 1.11.4 using `random_state=rng` in place of `rng=rng`; statsmodels 0.14.6)**
```
v1=0.735  v2=0.787  delta=+0.052
unpaired    95% CI [-0.007, +0.110]  width=0.118  SE=0.0302
paired      95% CI [+0.005, +0.102]  width=0.097  SE=0.0250
paired BCa  95% CI [+0.005, +0.102]  width=0.097  SE=0.0251
discordant: v1-only=40 v2-only=61  McNemar exact p=0.0460
MDE unpaired ~ 0.085
MDE paired   ~ 0.070
```
The story for the slide: the same data supports two different verdicts. The unpaired CI crosses 0 ("no evidence"). The paired CI does not ("v2 better by +0.5 to +10 points"). Pairing removes the shared item-difficulty variance.

**Key lines walk-through**
1. `def diff_of_means(x, y, axis=-1)`: with an `axis` parameter, SciPy treats the statistic as vectorized (`vectorized=None` means auto-detect), which is about 100x faster.
2. `paired=True`: one index vector resamples both arrays, so item *i* of v1 stays matched to item *i* of v2 (`_resampling.py:215-228`).
3. `method="BCa"` (the default) on `b - a`: bias-corrected and accelerated. It is better than percentile for skewed statistics, but it breaks on degenerate data (error 2).
4. `mcnemar(table, exact=True)`: an exact binomial test on the 40 vs 61 discordant pairs. The 299 concordant items carry no information about the *difference*.
5. `2.8 * SE`: z(0.975) + z(0.8) ≈ 1.96 + 0.84. With 400 paired items you can only detect about a 7-point change. Do this *before* you build the eval set.

**Common errors**
1. `TypeError: bootstrap() got an unexpected keyword argument 'rng'` (observed with scipy 1.11.4). `rng` replaced `random_state` in **scipy 1.15.0**: the v1.14.1 signature ends in `random_state=None`, v1.15.0 in `rng=None`. **Fix:** upgrade to scipy>=1.15, or use `random_state=` on old SciPy.
2. `DegenerateDataWarning: The BCa confidence interval cannot be calculated. This problem is known to occur when the distribution is degenerate or the statistic is np.min.` and the CI comes back `(nan, nan)` (`_resampling.py:664-670`; observed locally). **Cause:** all differences are 0, for example two identical checkpoints or a tiny slice. **Fix:** `method="percentile"`, or report "no discordant items".
3. `ValueError: When `paired is True`, all samples must have the same length along `axis`` (`_resampling.py:219-220`; observed locally). **Cause:** v2 crashed on 3 items and those rows were dropped. **Fix:** score crashes as failures (0) instead of dropping rows, and align on `item_id`.

**Best practice.** For every A/B on a fixed eval set, report the paired delta with its CI and n. With several samples per item (temperature > 0), average within the item first, or use a cluster bootstrap. SafeLLM4SE (arXiv:2609.37294) argues the same for LLM software-engineering evals.

**Variation / extension.** Add k=5 samples per item and compare "1 sample per item" with "mean of 5" SEs. Then read arXiv:2609.28560, which spends the rollout budget unevenly (Neyman allocation) to cut variance by 12.8-33.6%.

---

## Lab 5: Refund-fraud scorer. Measure ECE, then fix calibration on a held-out split

> **Verifier (2026-10-23):** VERIFIED against scikit-learn 1.9.1 source (`method` in {'sigmoid','isotonic','temperature'}, `FrozenEstimator`).

**Goal.** Show that a model with good AUROC can still give probabilities you cannot use as risk numbers. Measure ECE (equal-width and equal-mass bins), Brier and a reliability curve. Recalibrate with sigmoid, isotonic and **temperature** scaling (new in sklearn 1.8), using a frozen model and a separate calibration split.

**Adapted from:** scikit-learn "Probability calibration" user guide and the `CalibratedClassifierCV` docstring example `CalibratedClassifierCV(FrozenEstimator(base_clf))` (`sklearn/calibration.py:287-288`, tag 1.9.1).

**Prerequisites:** `pip install "scikit-learn==1.9.1" "numpy==2.5.4"`

**Code: `lab5_calibration.py`** (44 lines)
```python
"""Lab 5 - Refund-fraud scorer: measure ECE, then fix calibration on a held-out split."""
import numpy as np
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.datasets import make_classification
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB


def ece(y, p, n_bins=15, strategy="uniform"):
    """Expected calibration error for binary P(y=1). strategy: 'uniform' or 'quantile'."""
    if strategy == "uniform":
        edges = np.linspace(0, 1, n_bins + 1)
    else:
        edges = np.quantile(p, np.linspace(0, 1, n_bins + 1))
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, n_bins - 1)
    total = 0.0
    for b in range(n_bins):
        m = idx == b
        if m.any():
            total += m.mean() * abs(y[m].mean() - p[m].mean())
    return total


X, y = make_classification(n_samples=20_000, n_features=20, n_informative=6,
                           n_redundant=10, weights=[0.9, 0.1], random_state=0)
X_tr, X_rest, y_tr, y_rest = train_test_split(X, y, test_size=0.5, stratify=y, random_state=0)
X_cal, X_te, y_cal, y_te = train_test_split(X_rest, y_rest, test_size=0.5, stratify=y_rest, random_state=0)

base = GaussianNB().fit(X_tr, y_tr)        # NB with redundant features = overconfident
models = {"raw GaussianNB": base}
for method in ["sigmoid", "isotonic", "temperature"]:
    models[method] = CalibratedClassifierCV(FrozenEstimator(base), method=method).fit(X_cal, y_cal)

print(f"{'model':15s} {'AUROC':>6s} {'Brier':>7s} {'ECE-15u':>8s} {'ECE-15q':>8s}")
for name, m in models.items():
    p = m.predict_proba(X_te)[:, 1]
    print(f"{name:15s} {roc_auc_score(y_te, p):6.3f} {brier_score_loss(y_te, p):7.4f} "
          f"{ece(y_te, p):8.4f} {ece(y_te, p, strategy='quantile'):8.4f}")

frac_pos, mean_pred = calibration_curve(y_te, base.predict_proba(X_te)[:, 1], n_bins=10)
print("raw reliability (mean_pred -> frac_pos):",
      [f"{mp:.2f}->{fp:.2f}" for mp, fp in zip(mean_pred, frac_pos)])
```

**Run:** `python lab5_calibration.py`

**Output (REAL, scikit-learn 1.8.0 / numpy 1.26.4)**
```
model            AUROC   Brier  ECE-15u  ECE-15q
raw GaussianNB   0.929  0.0750   0.0677   0.0698
sigmoid          0.929  0.0561   0.0173   0.0251
isotonic         0.929  0.0536   0.0063   0.0064
temperature      0.929  0.0702   0.0780   0.0806
raw reliability (mean_pred -> frac_pos): ['0.01->0.01', '0.15->0.09', '0.24->0.14', '0.35->0.24', '0.45->0.23', '0.55->0.22', '0.65->0.35', '0.75->0.37', '0.86->0.35', '0.98->0.67']
```
Two teaching points. **(1)** AUROC is the same in all four rows: calibration fixes the *probabilities*, not the *ranking*. arXiv:2610.31657 reports the same about isotonic on LLM ticket classifiers. **(2)** Temperature scaling made ECE *worse* here. It has one parameter and no intercept, so it cannot fix a classifier biased toward the majority class on imbalanced data. The sklearn docstring says so directly: *"For very uncalibrated classifiers on very imbalanced datasets, sigmoid calibration might be preferred because it fits an additional intercept parameter."* (`calibration.py:130-133`). When the model says "0.86 fraud", the true rate is 0.35.

**Key lines walk-through**
1. `from sklearn.frozen import FrozenEstimator`: wraps an already-fitted model so `CalibratedClassifierCV` will not refit it. With a frozen estimator, `ensemble` becomes False (`calibration.py:370`).
2. `method="temperature"`: added in 1.8 (`.. versionchanged:: 1.8  Added option 'temperature'.`, `calibration.py:139-140`). It is natively multiclass: `softmax(logits / T)`.
3. `.fit(X_cal, y_cal)`: calibrate on data the base model never saw. Calibrating on training data learns nothing.
4. `ece(..., strategy="quantile")`: equal-mass bins. With 10% positives, most equal-width bins are nearly empty. Report both, plus Brier, because ECE depends on the binning.
5. `calibration_curve(y_te, p, n_bins=10)`: signature `(y_true, y_prob, *, pos_label=None, n_bins=5, strategy="uniform")` (`calibration.py:1227-1234`). **The default is 5 bins.**

**Common errors**
1. `InvalidParameterError: The 'cv' parameter of CalibratedClassifierCV must be an int in the range [2, inf), an object implementing 'split' and 'get_n_splits', an iterable or None. Got 'prefit' instead.` (observed, sklearn 1.8.0). `cv="prefit"` was removed. **Fix:** `CalibratedClassifierCV(FrozenEstimator(model))`.
2. `InvalidParameterError: The 'method' parameter of CalibratedClassifierCV must be a str among {'temperature', 'sigmoid', 'isotonic'}. Got 'platt' instead.` **Fix:** Platt scaling is `method="sigmoid"`. On sklearn < 1.8, `'temperature'` also fails this way.
3. `ValueError: y_prob has values outside [0, 1].` (`calibration.py:1312`). **Cause:** you passed `decision_function` scores or LLM logprobs. **Fix:** pass `predict_proba[:, 1]`, or `np.exp(logprob)` for LLM token probabilities.
4. Isotonic overfits on small calibration sets. The docstring: *"Isotonic calibration is not recommended when the number of calibration samples is too low (≪1000)"* (`calibration.py:136-137`). **Fix:** use sigmoid below about 1k calibration items.

**Best practice.** Report ECE (both binnings), Brier and AUROC together, on a split that was not used for training or calibration. If a downstream threshold reads the probability (Labs 6-7), calibrate first. Otherwise the Bayes threshold formula is wrong.

**Variation / extension.** Score an **LLM judge's** verbalized or token-probability confidence the same way. Collect (confidence, was_correct) pairs from Lab 8's calibration set and run `ece()`. arXiv:2608.22483 does this per atomic claim instead of per response. arXiv:2610.18614 trains an agent's step confidence against the episode outcome (ECE 0.42 to <0.12).

---

## Lab 6: Refund-fraud hold. Choose the threshold from a cost matrix, not 0.5

> **Verifier (2026-10-23):** VERIFIED against scikit-learn 1.9.1 source (`confusion_matrix_at_thresholds` exported, `TunedThresholdClassifierCV` default `scoring="balanced_accuracy"`).

**Goal.** A false positive (holding a good customer's refund for manual review) costs $15. A false negative (paying a fraudster) costs $120. Find the threshold that minimizes expected dollars. Then show the gotcha: the eval set is enriched to 10% fraud, but production has 2%.

**Adapted from:** scikit-learn example "Post-tuning the decision threshold for cost-sensitive learning" (`examples/model_selection/plot_cost_sensitive_learning.py`, tag 1.9.1; https://scikit-learn.org/stable/auto_examples/model_selection/plot_cost_sensitive_learning.html). That example uses a gain matrix `[[0, -1], [-5, 0]]` with `make_scorer` and `TunedThresholdClassifierCV(estimator=model, scoring=..., store_cv_results=True)`.

**Prerequisites:** `pip install "scikit-learn==1.9.1" "numpy==2.5.4"`

**Code: `lab6_cost_threshold.py`** (40 lines)
```python
"""Lab 6 - Refund-fraud hold: choose the threshold from a cost matrix, not 0.5."""
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, confusion_matrix_at_thresholds, make_scorer
from sklearn.model_selection import TunedThresholdClassifierCV, train_test_split

C_FP, C_FN = 15.0, 120.0      # $ manual review of a good refund vs $ paid to a fraudster
PI_PROD = 0.02                 # fraud prevalence in production (eval set is enriched)


def neg_cost(y, y_pred):       # scorer: higher is better, so return minus dollars per case
    tn, fp, fn, tp = confusion_matrix(y, y_pred, labels=[0, 1]).ravel()
    return -(fp * C_FP + fn * C_FN) / len(y)


X, y = make_classification(n_samples=12_000, n_features=15, n_informative=5,
                           weights=[0.9, 0.1], class_sep=0.8, random_state=1)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, stratify=y, random_state=1)
clf = LogisticRegression(max_iter=1000)

tuned = TunedThresholdClassifierCV(clf, scoring=make_scorer(neg_cost), cv=5,
                                   thresholds=200, store_cv_results=True).fit(X_tr, y_tr)
default = clf.fit(X_tr, y_tr)
print(f"Bayes rule t* = C_FP/(C_FP+C_FN) = {C_FP / (C_FP + C_FN):.3f}")
print(f"CV-tuned threshold on eval prevalence {y_tr.mean():.2f}: {tuned.best_threshold_:.3f}")
print(f"test $/case  default@0.5={-neg_cost(y_te, default.predict(X_te)):.2f}  "
      f"tuned={-neg_cost(y_te, tuned.predict(X_te)):.2f}")

# Re-weight to PRODUCTION prevalence: EC(t) = pi*FNR*C_FN + (1-pi)*FPR*C_FP
p_te = default.predict_proba(X_te)[:, 1]
tns, fps, fns, tps, thr = confusion_matrix_at_thresholds(y_te, p_te)
fpr, fnr = fps / (fps[-1]), fns / (tps[-1])
ec_eval = y_te.mean() * fnr * C_FN + (1 - y_te.mean()) * fpr * C_FP
ec_prod = PI_PROD * fnr * C_FN + (1 - PI_PROD) * fpr * C_FP
i_eval, i_prod = np.argmin(ec_eval), np.argmin(ec_prod)
print(f"best t @ eval prevalence={thr[i_eval]:.3f} (EC ${ec_eval[i_eval]:.2f})  "
      f"@ prod prevalence={thr[i_prod]:.3f} (EC ${ec_prod[i_prod]:.2f})")
print(f"using the eval-set threshold in prod costs ${ec_prod[i_eval]:.2f}/case "
      f"vs ${ec_prod[i_prod]:.2f} -> {100 * (ec_prod[i_eval] / ec_prod[i_prod] - 1):.0f}% more")
```

**Run:** `python lab6_cost_threshold.py`

**Output (REAL, scikit-learn 1.8.0)**
```
Bayes rule t* = C_FP/(C_FP+C_FN) = 0.111
CV-tuned threshold on eval prevalence 0.10: 0.141
test $/case  default@0.5=10.72  tuned=7.38
best t @ eval prevalence=0.152 (EC $7.07)  @ prod prevalence=0.340 (EC $1.86)
using the eval-set threshold in prod costs $3.10/case vs $1.86 -> 66% more
```
Slide message: moving from 0.5 to the cost-tuned threshold saves 31% ($10.72 to $7.38 per case). But if you ship the threshold tuned on the *enriched* eval set into 2%-prevalence production, you pay 66% more than necessary.

**Key lines walk-through**
1. `make_scorer(neg_cost)`: `TunedThresholdClassifierCV` *maximizes* the score, so return the negative cost (the sklearn example uses a gain matrix with negative entries for the same reason).
2. `TunedThresholdClassifierCV(clf, scoring=..., cv=5, thresholds=200)`: defaults are `scoring="balanced_accuracy"`, `thresholds=100`, `cv=None` (5-fold stratified), `refit=True` (`_classification_threshold.py:682-693`). The result is in `best_threshold_`.
3. `t* = C_FP / (C_FP + C_FN)`: the Bayes-optimal threshold, valid **only if the probabilities are calibrated** and the prevalence matches. The sklearn example cites Elkan for this ("we do not need to tune the threshold, but can safely set it to ...").
4. `confusion_matrix_at_thresholds(y_te, p_te)`: new in 1.8 (`_ranking.py:934`, `.. versionadded:: 1.8`). It returns `tns, fps, fns, tps, thresholds`, with thresholds decreasing. `fps[-1]` = all negatives and `tps[-1]` = all positives, per the docstring.
5. `ec_prod = PI_PROD * fnr * C_FN + (1 - PI_PROD) * fpr * C_FP`: FPR and FNR are properties of the classifier at threshold t and do not depend on prevalence. Plug in the *production* prior to get production cost.

**Common errors**
1. `ValueError: When cv='prefit', refit cannot be True.` (`_classification_threshold.py:730`; observed). **Fix:** `TunedThresholdClassifierCV(FrozenEstimator(model), cv="prefit", refit=False)`, or use CV. The docstring warns that prefit on the training data "is subject to undesired overfitting".
2. `ValueError: multiclass format is not supported` from `confusion_matrix_at_thresholds` with 3+ classes (observed). **Fix:** binarize (one-vs-rest per class), or use the Lab 7 route/defer formulation.
3. `ImportError: cannot import name 'confusion_matrix_at_thresholds' from 'sklearn.metrics'` on sklearn < 1.8 [message format standard Python; not reproduced]. **Fix:** upgrade, or use `roc_curve` and compute FNR = 1 - TPR.

**Best practice.** Write the cost matrix down with the business owner (finance or ops), version it on the quality card, and re-derive the threshold whenever prevalence or costs change. One global threshold can also be unfair across slices, so print the per-slice FPR at the chosen t.

**Variation / extension.** Use per-transaction amounts as costs (the sklearn example's second half uses `make_scorer(business_metric).set_score_request(amount=True)` with metadata routing). Or wrap the final policy as `FixedThresholdClassifier(model, threshold=0.34, response_method="predict_proba")` (`_classification_threshold.py:208, 302-310`) so the threshold ships with the model artifact.

---

## Lab 7: IT support-ticket triage. Auto-route or defer to a human, chosen on cost

> **Verifier (2026-10-23):** VERIFIED: re-run by the verifier (scikit-learn 1.8.0); output identical to the file.

**Goal.** An 8-class ticket router either routes a ticket automatically or defers it to human triage. Costs are (correct route, human triage, wrong route) = (0, 1, 5), the illustrative cost model of arXiv:2610.31657. Select the confidence threshold on a **calibration split**, freeze it, and evaluate **once** on test. Compare it with always-route and always-defer, and give a paired ratio-bootstrap CI. This reproduces that paper's protocol on synthetic data.

**Prerequisites:** `pip install "scikit-learn==1.9.1" "numpy==2.5.4"`

**Code: `lab7_abstain.py`** (45 lines)
```python
"""Lab 7 - IT support-ticket triage: auto-route or defer to a human, chosen on cost."""
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

C_OK, C_TRIAGE, C_WRONG = 0.0, 1.0, 5.0     # cost model used in arXiv:2610.31657
rng = np.random.default_rng(3)

X, y = make_classification(n_samples=24_000, n_features=30, n_informative=12,
                           n_classes=8, n_clusters_per_class=1, class_sep=0.9, random_state=3)
X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.5, stratify=y, random_state=3)
X_cal, X_te, y_cal, y_te = train_test_split(X_tmp, y_tmp, test_size=0.5, stratify=y_tmp, random_state=3)
clf = LogisticRegression(max_iter=2000).fit(X_tr, y_tr)


def per_ticket_cost(proba, y_true, t):
    conf, pred = proba.max(axis=1), proba.argmax(axis=1)
    route = conf >= t
    return np.where(route, np.where(pred == y_true, C_OK, C_WRONG), C_TRIAGE)


# 1) Select the threshold on the CALIBRATION split only, then freeze it.
p_cal, p_te = clf.predict_proba(X_cal), clf.predict_proba(X_te)
grid = np.round(np.arange(0.0, 1.0001, 0.01), 2)
cal_cost = [per_ticket_cost(p_cal, y_cal, t).mean() for t in grid]
t_star = grid[int(np.argmin(cal_cost))]
t_break_even = (C_WRONG - C_TRIAGE) / (C_WRONG - C_OK)   # route iff P(correct) > 0.8

# 2) Evaluate frozen policies ONCE on the test split.
always_route = per_ticket_cost(p_te, y_te, 0.0)
always_defer = per_ticket_cost(p_te, y_te, 1.01)
tuned = per_ticket_cost(p_te, y_te, t_star)
coverage = (p_te.max(axis=1) >= t_star).mean()
print(f"accuracy (always route) {(p_te.argmax(1) == y_te).mean():.3f}")
print(f"t* from calibration = {t_star:.2f}   analytic break-even = {t_break_even:.2f}")
print(f"test cost/ticket  always-route={always_route.mean():.3f}  "
      f"always-defer={always_defer.mean():.3f}  tuned={tuned.mean():.3f}  coverage={coverage:.2%}")
print(f"wrong routes: always-route={(always_route == C_WRONG).mean():.1%}  tuned={(tuned == C_WRONG).mean():.1%}")

# 3) Paired ratio bootstrap of the relative cost reduction vs always-route.
idx = rng.integers(0, len(y_te), size=(5000, len(y_te)))
ratio = 1 - tuned[idx].mean(axis=1) / always_route[idx].mean(axis=1)
lo, hi = np.percentile(ratio, [2.5, 97.5])
print(f"relative cost reduction {1 - tuned.mean() / always_route.mean():.1%}  95% CI [{lo:.1%}, {hi:.1%}]")
```

**Run:** `python lab7_abstain.py`

**Output (REAL, scikit-learn 1.8.0 / numpy 1.26.4)**
```
accuracy (always route) 0.612
t* from calibration = 0.79   analytic break-even = 0.80
test cost/ticket  always-route=1.942  always-defer=1.000  tuned=0.946  coverage=22.08%
wrong routes: always-route=38.8%  tuned=3.3%
relative cost reduction 51.3%  95% CI [49.7%, 52.8%]
```
Read it like this: the data-driven t* (0.79) lands on the analytic break-even (0.80), because logistic regression is fairly well calibrated. With 61% accuracy, the policy routes only 22% of tickets and is only about 5% cheaper than "send everything to humans". That is the honest headline, and it matches the paper's finding that weak LLM configurations "defer all tickets" at the 0.80 break-even.

**Key lines walk-through**
1. `per_ticket_cost(...)`: the cost matrix *is* the metric. Each ticket costs 0, 1 or 5, so the mean is dollars (or minutes) per ticket.
2. `t_break_even = (C_WRONG - C_TRIAGE) / (C_WRONG - C_OK)`: route when the expected cost of routing, (1 - p) x 5, is below the cost of deferring, 1. That gives p > 0.8. The rule is valid only if `conf` is calibrated (Lab 5).
3. `t_star` is chosen on `p_cal` and then **frozen**. Tuning on test and reporting test is optimistic: the "select on calibration, evaluate frozen once" protocol of arXiv:2610.31657.
4. `idx = rng.integers(...)`, then `tuned[idx]` and `always_route[idx]`: the same resampled tickets for both policies give a **paired** ratio bootstrap. Policies compared on different resamples would give wider, misleading CIs.

**Common errors**
1. `ValueError: Found input variables with inconsistent numbers of samples` [standard sklearn message, not reproduced here] when `X_cal` and `y_cal` were split separately. **Fix:** always split X and y in the same `train_test_split` call.
2. t* = 0.0 or 1.0 (routes everything or nothing) without any error. **Cause:** costs entered in the wrong order, or uncalibrated LLM confidences (arXiv:2610.31657: GPT-4o-mini few-shot had "one confidence value" and correctness AUROC 0.500). **Fix:** check the correctness AUROC of `conf` first. If it is about 0.5, no threshold can help.
3. `IndexError` in `per_ticket_cost` when labels are strings ("billing", "vpn"). **Fix:** compare `clf.classes_[proba.argmax(1)]` with `y_true`, not raw argmax indices.

**Best practice.** Always report the two trivial baselines (always-route, always-defer) next to the tuned policy, plus coverage and the wrong-route rate. A cost reduction against always-route alone can be a win that a human-only process already delivers.

**Variation / extension.** Replace `LogisticRegression` with LLM verbalized confidences on a 1,000-ticket stratified subset. Add a risk-coverage curve (sweep t, plot error rate among routed tickets vs coverage). Or use per-class costs, where a wrong route to "security incident" costs 20.

---

## Lab 8: HR-policy assistant. Is the LLM judge good enough to replace human review?

> **Verifier (2026-10-23):** VERIFIED against krippendorff 0.9.0 and scikit-learn 1.9.1 source.

**Goal.** On 300 answers labelled by two HR reviewers and an LLM judge, compute raw agreement, Cohen's kappa (human-human vs judge-human), judge TPR/TNR and Krippendorff's alpha with missing ratings. Then use the judge on 4,000 unlabeled production answers and **correct** its biased pass rate (Rogan-Gladen), with a bootstrap CI over both datasets.

**Adapted from:** the krippendorff README/docstring example (`src/krippendorff/krippendorff.py:265-330`, tag v0.9.0). Signature: `alpha(reliability_data=None, value_counts=None, value_domain=None, level_of_measurement="interval", dtype=...)`. **The default is `"interval"`.** Also `sklearn.metrics.cohen_kappa_score(y1, y2, *, labels=None, weights=None, sample_weight=None, replace_undefined_by=np.nan)` (`_classification.py:889-897`, 1.9.1). The correction workflow follows hamel.dev's LLM-judge FAQ (07 §8).

**Prerequisites:** `pip install "krippendorff==0.9.0" "scikit-learn==1.9.1" "numpy==2.5.4"`

**Code: `lab8_judge_agreement.py`** (48 lines)
```python
"""Lab 8 - HR-policy assistant: is the LLM judge good enough to replace human review?"""
import krippendorff
import numpy as np
from sklearn.metrics import cohen_kappa_score, confusion_matrix

rng = np.random.default_rng(11)
N_CAL, N_PROD = 300, 4000
truth = (rng.random(N_CAL) < 0.80).astype(int)          # 1 = answer is policy-correct

def noisy(labels, tpr, tnr):
    flip = np.where(labels == 1, rng.random(len(labels)) > tpr, rng.random(len(labels)) > tnr)
    return np.where(flip, 1 - labels, labels)

human_a, human_b = noisy(truth, 0.97, 0.93), noisy(truth, 0.95, 0.90)
judge = noisy(truth, 0.95, 0.60)                          # lenient judge: misses bad answers
gold = human_a                                            # adjudicated label in real life

tn, fp, fn, tp = confusion_matrix(gold, judge, labels=[0, 1]).ravel()
tpr, tnr = tp / (tp + fn), tn / (tn + fp)
print(f"raw agreement judge-vs-human {np.mean(judge == gold):.3f}")
print(f"Cohen kappa human-human {cohen_kappa_score(human_a, human_b):.3f}  "
      f"judge-human {cohen_kappa_score(gold, judge):.3f}")
print(f"judge TPR={tpr:.3f}  TNR={tnr:.3f}   (TNR = catches bad answers)")

# Krippendorff alpha: 3 raters x 300 units, human_b only rated 150 units (missing = nan).
rel = np.vstack([human_a, np.where(np.arange(N_CAL) < 150, human_b, np.nan), judge]).astype(float)
print(f"Krippendorff alpha (nominal, 3 raters, missing ok) "
      f"{krippendorff.alpha(reliability_data=rel, level_of_measurement='nominal'):.3f}")
codes = [[0, 2, 1, 2, 0, 1], [2, 2, 1, 0, 0, 1]]   # 0=answer 1=clarify 2=escalate (categories!)
print(f"3-category labels: nominal {krippendorff.alpha(reliability_data=codes, level_of_measurement='nominal'):.3f}"
      f"  vs default 'interval' {krippendorff.alpha(reliability_data=codes):.3f}")

# Production: judge-only labels on 4000 answers whose true pass rate is 0.72.
prod_truth = (rng.random(N_PROD) < 0.72).astype(int)
prod_judge = noisy(prod_truth, 0.95, 0.60)

def rogan_gladen(p_obs, tpr, tnr):
    return np.clip((p_obs + tnr - 1) / (tpr + tnr - 1), 0, 1)

boots = []
for _ in range(2000):                                     # resample BOTH calibration and prod
    i, j = rng.integers(0, N_CAL, N_CAL), rng.integers(0, N_PROD, N_PROD)
    g, jd = gold[i], judge[i]
    b_tpr, b_tnr = jd[g == 1].mean(), 1 - jd[g == 0].mean()
    boots.append(rogan_gladen(prod_judge[j].mean(), b_tpr, b_tnr))
print(f"prod pass rate: judge-observed {prod_judge.mean():.3f}  corrected "
      f"{rogan_gladen(prod_judge.mean(), tpr, tnr):.3f}  95% CI {np.round(np.percentile(boots, [2.5, 97.5]), 3)}"
      f"  (truth {prod_truth.mean():.3f})")
```

**Run:** `python lab8_judge_agreement.py`

**Output (REAL, scikit-learn 1.8.0; krippendorff v0.9.0 source)**
```
raw agreement judge-vs-human 0.877
Cohen kappa human-human 0.812  judge-human 0.580
judge TPR=0.946  TNR=0.593   (TNR = catches bad answers)
Krippendorff alpha (nominal, 3 raters, missing ok) 0.628
3-category labels: nominal 0.542  vs default 'interval' 0.083
prod pass rate: judge-observed 0.799  corrected 0.727  95% CI [0.628 0.798]  (truth 0.726)
```
Slide message: "88% agreement" sounds good, but kappa is 0.58, against 0.81 between humans. The judge catches only 59% of bad answers. Its raw production pass rate (79.9%) overstates the truth (72.6%) by 7 points. The corrected estimate (72.7%) recovers the truth, but the CI is wide (0.63-0.80) because only 300 calibration labels exist. **Buy more human labels on the failure class.**

**Key lines walk-through**
1. `confusion_matrix(gold, judge, labels=[0, 1]).ravel()`: always pass `labels=`. Otherwise a slice with only passes returns a 1x1 matrix and `ravel()` unpacking breaks.
2. `cohen_kappa_score(human_a, human_b)` next to `cohen_kappa_score(gold, judge)`: the human-human kappa is the *ceiling*. A judge is "good enough" relative to that ceiling, not relative to 1.0.
3. `krippendorff.alpha(reliability_data=rel, level_of_measurement='nominal')`: the shape is (raters, units), and `np.nan` marks a missing rating. Only alpha handles partial overlap (human_b rated 150 of 300).
4. `rogan_gladen(p_obs, tpr, tnr) = (p_obs + TNR - 1) / (TPR + TNR - 1)`: inverts the judge's known error rates. It needs TPR + TNR > 1 (better than chance) and is clipped to [0, 1].
5. The bootstrap resamples **both** `i` (calibration items, which re-estimates TPR/TNR) and `j` (production items). Ignoring the uncertainty in TPR/TNR gives a falsely tight CI.

**Common errors**
1. `nan` plus `UserWarning: A single label was found in 'y_true' and 'y_pred'. For the confusion matrix to have the correct shape, use the 'labels' parameter to pass all known labels.` from `cohen_kappa_score([1,1,1,1],[1,1,1,1])` (observed, 1.8.0). **Cause:** a slice where everything passes. **Fix:** compute kappa on pooled data with enough negatives, or set `replace_undefined_by=` (1.9.1 signature).
2. `ValueError: There has to be more than one value in the domain.` from `krippendorff.alpha` when every rating is identical (observed). **Fix:** same as above. Alpha is undefined without variation.
3. Silent wrong answer: the default `level_of_measurement="interval"` on categorical codes gave **0.083 vs 0.542** nominal on the same data (output above). **Fix:** always pass `level_of_measurement="nominal"` for categories. Use `"ordinal"` for 1-5 Likert scales.
4. Silent wrong answer: string labels (`[["pass","fail"],["pass","pass"]]`) returned `0.0` without an error (observed). **Fix:** map labels to integers, or pass `value_domain=["fail","pass"]` explicitly.

**Best practice.** Validate a judge against **gold human labels**, per failure mode, with TPR and TNR separately. Reliability statistics with no gold labels cannot isolate the judge (arXiv:2609.29709). Also test order-swap and replication stability: arXiv:2610.12083 found verdicts flip across identical temperature-0 replications and under position swaps. Read verdicts *after* generation, not from first-token logits (arXiv:2610.00054).

**Variation / extension.** *Pairwise judge consistency:* call the judge twice per pair with the order swapped and count a win only if both orders agree. Report the swap-flip rate split by rank gap (close vs far pairs, arXiv:2609.37577). *Anchor calibration:* map each judge's 1-5 scores onto a shared scale with a small anchor set (arXiv:2609.29431).

---

## Lab 9: Build a versioned quality card and a release gate for the claims-agent eval

> **Verifier (2026-10-23):** VERIFIED (pandas + statsmodels 0.15.0 `proportion_confint`). Captured run by the original author.

**Goal.** Turn Labs 3-8 into one artifact that a reviewer can read in 60 seconds and CI can enforce: the eval set hash, n and clusters, the headline with its CI, slices with CIs, calibration, decision policy, judge validity, known gaps, and a **pass/fail gate with a non-zero exit code**.

**Adapted from:** the quality-card template in 07 §11 (Model Cards, Mitchell et al. 2019; Datasheets for Datasets, Gebru et al.; Data Cards). Its tagline: "No number without n, CI, slice and version."

**Prerequisites:** `pip install "pandas==3.1.0" "statsmodels==0.15.0"`. Run Lab 3 first; it writes `claims_eval.jsonl`.

**Code: `lab9_quality_card.py`** (53 lines)
```python
"""Lab 9 - Build a versioned quality card + release gate for the claims agent eval."""
import datetime as dt
import hashlib
import json
import sys

import pandas as pd
from statsmodels.stats.proportion import proportion_confint

EVAL_FILE = "claims_eval.jsonl"                       # written by Lab 3
OTHER = {"ece_15_uniform": 0.0063, "calibration": "isotonic on 5,000-item cal split",  # Lab 5
         "threshold": 0.79, "cost_model": "(ok, triage, wrong) = (0, 1, 5)",           # Lab 7
         "judge_kappa": 0.580, "judge_tpr": 0.946, "judge_tnr": 0.593}                  # Lab 8
GATES = {"min_slice_ci_low": 0.50, "min_slice_n": 30, "min_judge_kappa": 0.60}

raw = open(EVAL_FILE, "rb").read()
df = pd.read_json(EVAL_FILE, lines=True)
k, n = int(df.passed.sum()), len(df)
lo, hi = proportion_confint(k, n, method="wilson")
g = df.groupby(["line", "lang"])["passed"].agg(k="sum", n="count").reset_index()
g["lo"], g["hi"] = proportion_confint(g.k, g.n, method="wilson")

failures = [f"slice {r.line}/{r.lang}: CI low {r.lo:.2f} < {GATES['min_slice_ci_low']}"
            for r in g.itertuples() if r.lo < GATES["min_slice_ci_low"]]
failures += [f"judge kappa {OTHER['judge_kappa']:.2f} < {GATES['min_judge_kappa']}"] \
    if OTHER["judge_kappa"] < GATES["min_judge_kappa"] else []
thin = [f"{r.line}/{r.lang} (n={r.n})" for r in g.itertuples() if r.n < GATES["min_slice_n"]]

card = {
    "card_version": "1.0", "created": dt.date.today().isoformat(),
    "eval_set": {"file": EVAL_FILE, "sha256": hashlib.sha256(raw).hexdigest()[:16],
                 "n_items": n, "n_clusters": int(df.claim_id.nunique()), "unit_of_resampling": "claim_id"},
    "headline": {"pass_rate": round(k / n, 3), "wilson_95": [round(lo, 3), round(hi, 3)]},
    "slices": g.round(3).to_dict(orient="records"),
    "calibration": {k_: OTHER[k_] for k_ in ("ece_15_uniform", "calibration")},
    "decision_policy": {k_: OTHER[k_] for k_ in ("threshold", "cost_model")},
    "judge": {k_: OTHER[k_] for k_ in ("judge_kappa", "judge_tpr", "judge_tnr")},
    "known_gaps": {"thin_slices_n_lt_30": thin},
    "gate": {"passed": not failures, "failures": failures},
}
json.dump(card, open("quality_card.json", "w"), indent=2)
md = [f"# Quality card - claims agent eval ({card['created']})",
      f"Eval set `{EVAL_FILE}` sha256:{card['eval_set']['sha256']} | n={n} items / "
      f"{card['eval_set']['n_clusters']} claims",
      f"**Pass rate {k / n:.1%}** (Wilson 95% {lo:.1%}-{hi:.1%})", "",
      "| slice | n | pass | 95% CI |", "|---|---|---|---|"]
md += [f"| {r.line}/{r.lang} | {r.n} | {r.k / r.n:.0%} | {r.lo:.0%}-{r.hi:.0%} |" for r in g.itertuples()]
md += ["", f"Judge: kappa {OTHER['judge_kappa']}, TPR {OTHER['judge_tpr']}, TNR {OTHER['judge_tnr']}",
       f"Thin slices: {', '.join(thin) or 'none'}",
       f"**Gate: {'PASS' if not failures else 'FAIL'}** " + "; ".join(failures)]
open("quality_card.md", "w").write("\n".join(md) + "\n")
print("\n".join(md))
sys.exit(0 if not failures else 1)
```

**Run**
```bash
python lab3_slices.py && python lab9_quality_card.py; echo "exit=$?"
# In CI (GitHub Actions step):  run: python lab9_quality_card.py   -> job fails on exit 1
```

**Output (REAL, pandas 2.1.4 / statsmodels 0.14.6)**
```
# Quality card - claims agent eval (2026-10-23)
Eval set `claims_eval.jsonl` sha256:d0e202a5a0b3e504 | n=353 items / 60 claims
**Pass rate 83.9%** (Wilson 95% 79.7%-87.3%)

| slice | n | pass | 95% CI |
|---|---|---|---|
| auto/en | 156 | 90% | 84%-94% |
| auto/es | 8 | 88% | 53%-98% |
| health/en | 24 | 83% | 64%-93% |
| health/es | 16 | 56% | 33%-77% |
| home/en | 74 | 82% | 72%-89% |
| home/es | 29 | 69% | 51%-83% |
| travel/en | 33 | 91% | 76%-97% |
| travel/es | 13 | 69% | 42%-87% |

Judge: kappa 0.58, TPR 0.946, TNR 0.593
Thin slices: auto/es (n=8), health/en (n=24), health/es (n=16), home/es (n=29), travel/es (n=13)
**Gate: FAIL** slice health/es: CI low 0.33 < 0.5; slice travel/es: CI low 0.42 < 0.5; judge kappa 0.58 < 0.6
exit=1
```

**Key lines walk-through**
1. `hashlib.sha256(raw).hexdigest()[:16]`: hash the **bytes** of the eval file. Any edit to the eval set changes the card's ID, so numbers from different set versions cannot be mixed silently.
2. `"unit_of_resampling": "claim_id"`: write down which unit the CIs resample (Lab 3). A reviewer needs it to judge the CI.
3. The `GATES` dict: release criteria live in code and in the card, decided *before* the run. Gate on the **CI lower bound**, not the point estimate, so a thin slice cannot pass by luck.
4. `sys.exit(0 if not failures else 1)`: the card becomes a CI check. A failed gate blocks the merge or deploy, like a failing unit test.
5. `known_gaps`: list what the eval cannot tell you (thin slices). An honest card lists its blind spots.

**Common errors**
1. `FileNotFoundError: [Errno 2] No such file or directory: 'claims_eval.jsonl'`. **Fix:** run Lab 3 first, or point `EVAL_FILE` at your real results.
2. `TypeError: Object of type int64 is not JSON serializable` from `json.dump` [standard message; avoided in the lab via `int(...)` and `round(...)`]. **Fix:** cast numpy scalars (`int(k)`, `float(x)`), or `json.dump(..., default=float)`.
3. The hash changes on every run even though nothing changed. **Cause:** you hashed a re-serialized DataFrame (key order, float formatting) instead of the stored bytes. **Fix:** hash the file bytes as the lab does, and write eval files once with `sort_keys=True` (as Lab 2 does).

**Best practice.** One card per (model version x eval-set hash). Store it next to the model artifact, and diff cards between releases. The `OTHER` dict is hard-coded here for clarity. In production, have Labs 5-8 each write a JSON fragment and merge the fragments, so no number is ever retyped.

**Variation / extension.** Add `synthetic_fraction` and generator provenance (from Labs 1-2) and a contamination check: n-gram overlap between training data and the eval set. SynthSentry (arXiv:2609.12353) shows why the alarm threshold itself needs a bootstrap. Render the markdown card into the PR description with `gh pr comment --body-file quality_card.md`.

---

## Cross-lab gotchas (one slide)

1. **Python 3.12+**: numpy 2.5.4 and scipy 1.18.1 refuse older interpreters.
2. **scipy `rng=` vs `random_state=`**: the switch happened in 1.15.0. Old Colab images break Lab 4.
3. **sklearn `cv="prefit"` is gone** from `CalibratedClassifierCV`. Use `FrozenEstimator`. `TunedThresholdClassifierCV` still accepts `cv="prefit"`, but only with `refit=False`.
4. **Defaults that lie**: `proportion_confint(method="normal")`, `krippendorff.alpha(level_of_measurement="interval")`, `calibration_curve(n_bins=5)`, `TunedThresholdClassifierCV(scoring="balanced_accuracy")`. Pass all four explicitly.
5. **Prevalence**: thresholds and costs computed on an enriched eval set are wrong in production (Lab 6: +66% cost).
6. **Temperature scaling is not a universal fix**: on an imbalanced, biased model it made ECE worse (Lab 5).
7. **distilabel's OpenAILLM always sends `max_tokens` and sampling params**, so use non-reasoning models or a compatible local server.
8. **ragas needs documents longer than 100 tokens** and related documents for multi-hop. Set `RAGAS_DO_NOT_TRACK=true`.

## Industry practice notes (verified only where cited)

- Llama 3 execution-feedback rejection sampling (06 §5, arXiv:2407.21783) is the pattern behind Lab 1.
- "Select on calibration, freeze, evaluate once on test" plus a paired ratio bootstrap is the protocol in arXiv:2610.31657 (Lab 7).
- The binary pass/fail-per-failure-mode judge plus Rogan-Gladen correction is the hamel.dev workflow (07 §8; not re-fetched today).
- sklearn's own cost-sensitive example uses a 1:5 cost ratio and `TunedThresholdClassifierCV` (Lab 6 source).

## Sources (fetched this session, 2026-10-23)

- PyPI JSON: https://pypi.org/pypi/{distilabel,ragas,openai,numpy,scipy,scikit-learn,pandas,statsmodels,krippendorff,datasets,langchain-openai,langchain-core}/json
- distilabel 1.5.3 source: https://raw.githubusercontent.com/argilla-io/distilabel/1.5.3/src/distilabel/ (steps/__init__.py, steps/decorator.py, steps/tasks/text_generation.py, steps/tasks/base.py, steps/generators/data.py, models/llms/openai.py, models/base_clients/openai.py, pipeline/__init__.py, pipeline/_dag.py, distiset.py), docs/sections/getting_started/quickstart.md, docs/sections/how_to_guides/basic/step/index.md, pyproject.toml; README on main.
- ragas v0.4.3 source: https://raw.githubusercontent.com/explodinggradients/ragas/v0.4.3/src/ragas/ (testset/synthesizers/generate.py, testset_schema.py, synthesizers/__init__.py, single_hop/specific.py, multi_hop/*.py, testset/transforms/default.py, testset/graph.py, llms/__init__.py, embeddings/openai_provider.py, dataset_schema.py, _analytics.py), docs/getstarted/rag_testset_generation.md, docs/extra/components/choose_generator_llm.md, pyproject.toml.
- openai-python: README.md and CHANGELOG.md (3.0.0 entry), https://github.com/openai/openai-python
- scipy v1.18.1 / v1.15.0 / v1.14.1: scipy/stats/_resampling.py
- scikit-learn 1.9.1: sklearn/calibration.py, sklearn/model_selection/_classification_threshold.py, sklearn/metrics/_ranking.py, sklearn/metrics/_classification.py, sklearn/metrics/__init__.py, examples/model_selection/plot_cost_sensitive_learning.py
- statsmodels v0.15.0: statsmodels/stats/proportion.py, statsmodels/stats/contingency_tables.py
- krippendorff v0.9.0: https://github.com/pln-fing-udelar/fast-krippendorff (src/krippendorff/krippendorff.py, __init__.py)
- arXiv API (export.arxiv.org, sortBy=submittedDate) abstracts for: 2610.31657, 2609.29709, 2610.12083, 2610.00054, 2609.37577, 2610.00369, 2609.29431, 2609.37294, 2609.28560, 2608.14711, 2608.22483, 2610.18614, 2610.21167, 2609.12171, 2610.26951, 2609.12353.
