# 06 - LLM + RAG Datasets and Synthetic Data with Verification

Research date: 2026-10-23. Sources are primary (arXiv abstract/HTML, GitHub, official docs, HF dataset/model cards, PyPI). Items not confirmed against a primary source are marked [UNVERIFIED].

**Library versions checked on PyPI (2026-10-23):** `datatrove` 0.10.1 (2026-09-30), `nemo-curator` 1.4.0 (2026-10-09; the GitHub README "Updates" section uses calendar names such as NeMo Curator 26.04), `ragas` 0.4.3 (2026-01-13), `distilabel` 1.5.3 (2025-01-28; no PyPI release since then, so treat it as low-activity), `datasketch` 2.0.0 (2026-07-05).

---

## 1. The big picture: the data lifecycle for LLMs

Word diagram (one row of the deck lifecycle):

```
DESIGN  -> what capability, which target distribution, which eval set (held out, decontaminated)
GENERATE -> crawl (Common Crawl/PDFs) or synthesize (Self-Instruct, Evol, Magpie, Personas, distillation)
SELECT  -> heuristics -> model-based quality classifier -> targeted selection (DSIR, LESS)
CURATE  -> dedup (exact, MinHash/LSH, semantic), mixing, decontamination
LABEL   -> LLM judges, reward models, AI feedback (UltraFeedback, CAI)
DENOISE -> verification: execution, unit tests, answer match, rejection sampling, constitutional filters
CARD    -> dataset card: sources, filters + removal rates, license, contamination checks, known biases
```

The main trend from 2023 to 2026: most of the gains now come from **model-based filtering plus verified synthetic data**, not from more raw tokens. FineWeb-Edu and DCLM both throw away about 90% of web data. Nemotron-CC rephrases data to win back token count. Reasoning datasets such as OpenThoughts are 100% teacher-distilled.

---

## 2. Pretraining data curation

### 2.1 FineWeb and FineWeb-Edu (Hugging Face, 2024)
- Paper: **"The FineWeb Datasets: Decanting the Web for the Finest Text Data at Scale"**, Penedo, Kydlíček, Ben Allal, Lozhkov, Mitchell, Raffel, Von Werra, Wolf. arXiv:2406.17557 (v1 2024-06-25). https://arxiv.org/abs/2406.17557
- **FineWeb: 15T tokens from 96 Common Crawl snapshots. FineWeb-Edu: 1.3T tokens.** The dataset card now lists snapshots CC-MAIN-2013-20 through CC-MAIN-2025-26, plus 10BT/100BT/350BT samples, under the ODC-BY license. https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu
- **Edu classifier recipe (paper HTML):**
  - Llama-3-70B-Instruct scored **460k pages** from CC-MAIN-2024-10 on a 0-5 scale (410k train / 50k validation).
  - A linear regression head was trained on **Snowflake-arctic-embed-m** for 20 epochs at lr 3e-4.
  - The keep threshold is **score >= 3, which gives F1 82%**.
  - Classifying all 15T tokens took **6,000 H100 GPU-hours**.
- **Results:**
  - FineWeb-Edu reaches **33.6% MMLU at 38B tokens**. Matrix needs about 300B tokens to reach the same score, so FineWeb-Edu gets there with **almost 10x fewer tokens**.
  - In the 350B-token ablation, MMLU rose from 33% to 37% and ARC from 46% to 57%.
- **Dedup lesson (counter-intuitive, good for a slide):**
  - MinHash used 5-grams and **112 hashes = 14 buckets x 8**, targeting documents that are at least about 75% similar.
  - Deduplicating **per snapshot** left 20T tokens and matched RefinedWeb.
  - Deduplicating **globally** left about 4T tokens and performed *worse*. Over-deduplication keeps the low-quality tail.
- **Heuristics:**
  - The C4 filters were kept except the terminal-punctuation rule, which alone removes about 30% of tokens.
  - Three custom filters were added: punctuation-ending lines <= 0.12, duplicated-line characters >= 0.1, and short-line fraction >= 0.67. Together they remove about 22% of tokens for about +1% aggregate score.
- Follow-ups:
  - **FineWeb2**, "FineWeb2: One Pipeline to Scale Them All -- Adapting Pre-Training Data Processing to Every Language", arXiv:2506.20920 (2025-06-26). It covers more than 1000 languages: 20 TB, about 5B documents. https://arxiv.org/abs/2506.20920
  - **FinePDFs** (Sept 2025): about 3T tokens from 475M PDF documents, extracted with Docling plus RolmOCR. FinePDFs-Edu has 350B+ tokens. The language count is given as "1000+" in the HF blog and 1,733 in press coverage [UNVERIFIED exact]. https://huggingfacefw-finepdfsblog.hf.space/

Code: scoring a page with the FineWeb-Edu classifier (verbatim from the model card, https://huggingface.co/HuggingFaceFW/fineweb-edu-classifier):
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("HuggingFaceTB/fineweb-edu-classifier")
model = AutoModelForSequenceClassification.from_pretrained("HuggingFaceTB/fineweb-edu-classifier")

text = "This is a test sentence."
inputs = tokenizer(text, return_tensors="pt", padding="longest", truncation=True)
outputs = model(**inputs)
logits = outputs.logits.squeeze(-1).float().detach().numpy()
score = logits.item()
result = {"text": text, "score": score,
          "int_score": int(round(max(0, min(score, 5))))}
```
The card says the classifier is biased toward primary and grade-school content and may "overfit to academic-looking content". It recommends `int_score >= 3`.

### 2.2 DataTrove: the pipeline library behind FineWeb
- Repo: https://github.com/huggingface/datatrove (PyPI 0.10.1).
- The official script `examples/fineweb.py` runs `WarcReader -> URLFilter -> Trafilatura -> LanguageFilter -> GopherRepetitionFilter -> GopherQualityFilter -> C4QualityFilter(filter_no_terminal_punct=False) -> FineWebQualityFilter -> JsonlWriter`. It then runs a 4-stage MinHash (`MinhashDedupSignature -> MinhashDedupBuckets -> MinhashDedupCluster -> MinhashDedupFilter`).

Code (adapted from https://github.com/huggingface/datatrove/blob/main/examples/fineweb.py):
```python
from datatrove.executor import LocalPipelineExecutor
from datatrove.pipeline.readers import JsonlReader
from datatrove.pipeline.filters import (GopherRepetitionFilter, GopherQualityFilter,
                                        C4QualityFilter, FineWebQualityFilter, LanguageFilter)
from datatrove.pipeline.writers import JsonlWriter
from datatrove.pipeline.dedup.minhash import MinhashConfig
from datatrove.utils.hashing import HashConfig

pipeline = [
    JsonlReader("data/raw/"),
    LanguageFilter(),
    GopherRepetitionFilter(exclusion_writer=JsonlWriter("removed/gopher_rep")),
    GopherQualityFilter(exclusion_writer=JsonlWriter("removed/gopher_qual")),
    C4QualityFilter(filter_no_terminal_punct=False),
    FineWebQualityFilter(),
    JsonlWriter("data/filtered/"),
]
LocalPipelineExecutor(pipeline=pipeline, tasks=10, workers=5, logging_dir="logs/").run()

minhash_config = MinhashConfig(hash_config=HashConfig(hash_fc="sha1", precision=64),
                               num_buckets=14, hashes_per_bucket=8, n_grams=5)
```
Teaching point: every filter has an `exclusion_writer`. Keeping the removed documents makes each filter auditable, and the per-filter removal rates belong on the quality card.

### 2.3 DCLM: DataComp-LM (2024)
- **"DataComp-LM: In search of the next generation of training sets for language models"**, arXiv:2406.11794 (v1 2024-06-17, v4 2025-04-21). https://arxiv.org/abs/2406.11794
- DCLM-Pool is **about 240T GPT-NeoX tokens** (200B documents, 370 TB gzip) from Common Crawl before 2023, re-extracted with resiliparse.
- Winning filter: a **fastText classifier** trained on **OpenHermes 2.5 plus top r/ExplainLikeImFive posts** as positives and RefinedWeb-reproduction documents as negatives (about 400k documents). It keeps the **top 10%**.
- Filter comparison at 1B-1x, Core score:

  | Filter | Core |
  |---|---|
  | fastText (OH-2.5 + ELI5) | 30.2 |
  | Top-k logits | 29.2 |
  | Perplexity | 29.0 |
  | AskLLM | 28.6 |
  | RefinedWeb | 27.5 |
  | SemDedup | 27.1 |
  | PageRank top-20% | 26.1 |

- DCLM-Baseline is **3.8T tokens**, deduplicated with a Bloom-filter near-dup method (BFF).
- **DCLM-Baseline 7B: 64% MMLU (5-shot) after 2.6T tokens.**
  - That is 6.6 points above MAP-Neo with 40% less compute.
  - It is comparable to Llama 3 8B (66%) with **6.6x less compute**.
- Quotable: *"model-based filtering is key to assembling a high-quality training set."* (abstract)

### 2.4 Dolma (AI2, 2024)
- **"Dolma: an Open Corpus of Three Trillion Tokens for Language Model Pretraining Research"**, arXiv:2402.00159, ACL 2024. https://arxiv.org/abs/2402.00159
- 3T English tokens from web, scientific papers, code, public-domain books, social media and encyclopedic sources.
- The toolkit is open: https://github.com/allenai/dolma. Dolma was the training corpus for OLMo.

### 2.5 Nemotron-CC and NeMo Curator (NVIDIA)
- **"Nemotron-CC: Transforming Common Crawl into a Refined Long-Horizon Pretraining Dataset"**, arXiv:2412.02595 (ACL 2025). https://arxiv.org/abs/2412.02595
- 6.3T tokens, built with classifier ensembling, synthetic rephrasing and fewer heuristic filters.
- Critique of prior work: FineWeb-Edu and DCLM "remove ~90% of data", which hurts long training horizons.
- Results:
  - An 8B model trained for 15T tokens (7.2T of them from Nemotron-CC) **beats Llama 3.1 8B by +5 MMLU** and +3.1 ARC-C.
  - The full 6.3T set matches DCLM on MMLU with **about 4x more unique real tokens**.
  - Its high-quality subset gives +5.6 MMLU over DCLM at a 1T-token horizon.
- **NeMo Curator**: https://github.com/NVIDIA-NeMo/Curator (PyPI `nemo-curator` 1.4.0).
  - It uses a Ray-based pipeline architecture for all modalities (text, image, video, audio). XennaExecutor is the production default.
  - It provides GPU fuzzy and semantic dedup, quality classifiers, and in-pipeline SDG through an OpenAI-compatible server.
  - Benchmark (RedPajama-v2 subset, 3x H100 nodes): fuzzy dedup took **10.7 h on a CPU alternative vs 0.65 h with Curator (about 16x)**, and cost fell from $315 to $190.
  - Python API: the README gives no inline code; see `tutorials/text` [UNVERIFIED exact class names for 1.4.0].

---

## 3. Instruction / post-training data

| Method | Paper (exact title, venue) | Core idea | Numbers |
|---|---|---|---|
| Self-Instruct | "Self-Instruct: Aligning Language Models with Self-Generated Instructions", ACL 2023, arXiv:2212.10560 | Bootstrap from seed tasks. An LLM writes new instructions, inputs and outputs. Drop near-duplicates. | +33% absolute on Super-NaturalInstructions over vanilla GPT-3 (abstract). 175 seed tasks to about 52K instructions; ROUGE-L < 0.7 novelty filter [from paper body, not re-checked today] |
| Evol-Instruct | "WizardLM: Empowering large pre-trained language models to follow complex instructions", ICLR 2024, arXiv:2304.12244 | Rewrite instructions "step by step into more complex instructions" (in-depth and in-breadth evolution) | >90% of ChatGPT capacity on 17/29 skills (GPT-4 eval) |
| Magpie | "Magpie: Alignment Data Synthesis from Scratch by Prompting Aligned LLMs with Nothing", arXiv:2406.08464 | Feed only the chat template's left side up to the user slot, so the aligned model *writes the user query itself* | 4M generated, 300K selected. Llama-3-8B-Base + Magpie SFT is comparable to official Llama-3-8B-Instruct (about 10M data points, SFT + RLHF) on some tasks |
| Persona Hub | "Scaling Synthetic Data Creation with 1,000,000,000 Personas", arXiv:2406.20094 (Tencent AI Lab) | Persona x prompt = diverse data at scale | 1B personas. Released 200K personas, later 370M "elite personas" (2025-02-18), plus 50K math, 50K logic, 50K instructions, 10K knowledge texts, 10K NPCs, 5K tools (https://github.com/tencent-ailab/persona-hub) |
| Tulu 3 | "Tulu 3: Pushing Frontiers in Open Language Model Post-Training", arXiv:2411.15124 (AI2) | SFT, then DPO, then **RLVR** (RL with Verifiable Rewards), with "substantial decontamination" | SFT mix is **939,344** samples (https://huggingface.co/datasets/allenai/tulu-3-sft-mixture), including persona-generated MATH 149,960, GSM 49,980, Python 34,999, Algebra 20,000, IF 29,980 |
| OpenThoughts | "OpenThoughts: Data Recipes for Reasoning Models", arXiv:2506.04178 | 1,000+ controlled ablations of each pipeline step | OpenThoughts3-1.2M. **OpenThinker3-7B** (on Qwen2.5-7B-Instruct): AIME25 53%, LiveCodeBench 51%, GPQA-D 54%, which is +15.3/+17.2/+20.5 over DeepSeek-R1-Distill-Qwen-7B |

**OpenThoughts findings (quotable, arXiv HTML v2):**
- "Sampling multiple answers per question from a teacher model is an effective technique to increase the size of a data source by at least 16x."
- "Selecting questions from a small number (top 1 or 2) of high-quality sources leads to better downstream performance."
- "Filtering questions by LLM labeled difficulty or LLM response length yields better results than" fastText or embedding filters.
- On verification: "We experimented with numerous verification and answer filtering methods, and none gave significant performance improvements." This is a surprising open-challenge slide: for SFT distillation from a strong teacher, verification did not pay off. It does pay off for RL (RLVR) and for code.
- "QwQ-32B is a stronger teacher than DeepSeek-R1", even though R1 scores higher on benchmarks. **The best model is not always the best teacher.**

Code: Magpie with distilabel (verbatim, https://distilabel.argilla.io/latest/components-gallery/tasks/magpiegenerator/):
```python
from distilabel.models import TransformersLLM
from distilabel.steps.tasks import MagpieGenerator

generator = MagpieGenerator(
    llm=TransformersLLM(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        magpie_pre_query_template="llama3",
        generation_kwargs={"temperature": 1.0, "max_new_tokens": 256},
        device="mps",
    ),
    only_instruction=True,
    num_rows=5,
)
generator.load()
result = next(generator.process())
```

Code: distilabel quickstart (verbatim, https://distilabel.argilla.io/latest/sections/getting_started/quickstart/; `pip install distilabel[hf-inference-endpoints] --upgrade`):
```python
from datasets import load_dataset
from distilabel.models import InferenceEndpointsLLM
from distilabel.pipeline import Pipeline
from distilabel.steps.tasks import TextGeneration

with Pipeline() as pipeline:
    TextGeneration(llm=InferenceEndpointsLLM(
        model_id="meta-llama/Meta-Llama-3.1-8B-Instruct",
        generation_kwargs={"temperature": 0.7, "max_new_tokens": 512}))

if __name__ == "__main__":
    dataset = load_dataset("distilabel-internal-testing/instructions", split="test")
    distiset = pipeline.run(dataset=dataset)
    distiset.push_to_hub(repo_id="distilabel-example")
```
distilabel's component gallery includes UltraFeedback, EvolInstruct, EvolComplexity, EvolQuality, Magpie, MagpieGenerator, SelfInstruct, GenStruct, PrometheusEval, CLAIR, PairRM, APIGenGenerator and ArgillaLabeller. Pitch line from the docs: *"the framework for synthetic data and AI feedback for engineers who need fast, reliable and scalable pipelines."*

---

## 4. Data selection

- **Heuristics** (Gopher, C4, FineWeb filters) are cheap and transparent but have a low ceiling.
- **Quality classifiers**: the FineWeb-Edu regressor, the DCLM fastText classifier, and the Nemotron-CC ensemble. The pattern is to *have an LLM annotate about 0.5M documents, distill the labels into a tiny classifier, and run it over trillions of tokens*.
- **DSIR**: "Data Selection for Language Models via Importance Resampling", Xie, Santurkar, Ma, Liang, NeurIPS 2023, arXiv:2302.03169.
  - It computes importance weights on **hashed n-gram features**, then resamples.
  - It selects 100M documents from the Pile in about 4.5 h.
  - Its "KL reduction" metric correlates r=0.82 with downstream accuracy.
  - It gives +2-2.5% GLUE over random and heuristic selection.
- **LESS**: "LESS: Selecting Influential Data for Targeted Instruction Tuning", Xia, Malladi, Gururangan, Arora, Chen, ICML 2024, arXiv:2402.04333.
  - It builds a reusable datastore of low-dimensional (projected) gradient features compatible with Adam.
  - It selects the examples most similar to a few-shot target set.
  - **Training on the LESS-selected 5% often beats training on the full dataset**, and selection transfers from small to large models.
- **Dedup**:
  - Exact (hash) dedup is the baseline.
  - Fuzzy dedup uses MinHash-LSH (`datasketch` 2.0.0, DataTrove, NeMo Curator GPU).
  - Semantic dedup clusters embeddings (SemDedup, NeMo Curator). Llama 3 SFT used RoBERTa clusters with a greedy cosine threshold, sorted by quality x difficulty.
- **Decontamination**: n-gram overlap against evaluation sets. Tulu 3 decontaminated public datasets "substantially".

---

## 5. Synthetic generation with verification ("generate -> verify -> keep")

Word diagram (animate as a funnel):
```
prompt pool (seed / persona / Magpie)
  -> sample K candidates per prompt (K = 10-30 in Llama 3)
  -> VERIFIERS in order of cost:
       1. format/parse/lint (static)
       2. execution + unit tests (code), exact-match / symbolic check (math)
       3. reward model score / LLM-as-judge rubric
       4. constitutional / safety critique-and-revise
  -> keep best-of-K (rejection sampling) or pairs (chosen/rejected -> DPO)
  -> dedup + decontaminate -> dataset card
```

- **Llama 3** ("The Llama 3 Herd of Models", arXiv:2407.21783):
  - Rejection sampling draws **K "typically between 10 and 30"** outputs per prompt, and the reward model picks the best.
  - There are **over 2.7M synthetic code examples** in SFT. About **1M coding dialogues used execution feedback**: parser and linter, model-written unit tests run in a container, and error-guided self-repair. Only dialogs that pass all checks were kept.
  - Quote: *"about 20% of solutions were initially incorrect but self-corrected."*
  - SFT quality filter: RM top-quartile **or** a Llama-judge maximum score, plus Instag difficulty tagging and semantic dedup.
- **LLM-as-judge**: "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", NeurIPS 2023 D&B, arXiv:2306.05685.
  - GPT-4 judges reach **"over 80% agreement"** with humans, about the same as human-human agreement.
  - Known biases: position, verbosity, self-enhancement, and limited reasoning. Mitigate by swapping answer order, using rubrics and reference answers, and using a judge from a different model family.
- **RLVR (Tulu 3)**: the reward is 1 only if the answer is *verifiably* correct (math answer match, instruction constraint check). This is verification moved from data filtering into the RL reward.
- **Constitutional AI**: "Constitutional AI: Harmlessness from AI Feedback", arXiv:2212.08073 (2022-12-15).
  - SL phase: the model critiques and revises its own outputs, then is finetuned on the revisions.
  - RL phase: AI preferences train a preference model, which provides the reward (**RLAIF**).
  - It is also used as a constitutional *filter* on synthetic data.

Code: unit-test rejection sampling (illustrative pattern written for the deck, *not* from an official repo; it uses only the Python standard library):
```python
import subprocess, tempfile, textwrap

def passes_tests(solution: str, tests: str, timeout=5) -> bool:
    prog = solution + "\n\n" + textwrap.dedent(tests)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(prog)
    try:
        r = subprocess.run(["python", "-I", f.name], capture_output=True, timeout=timeout)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return False

def rejection_sample(prompt, tests, generate, k=16):
    cands = [generate(prompt, temperature=0.8) for _ in range(k)]
    good = [c for c in cands if passes_tests(c, tests)]
    return good  # keep all passing (SFT) or pair passing/failing (DPO)
```
In production, run this in a real sandbox (container, no network). Llama 3 used containers.

---

## 6. Model collapse: the risk of recursive synthetic data

- **"The Curse of Recursion: Training on Generated Data Makes Models Forget"**, Shumailov, Shumaylov, Zhao, Gal, Papernot, Anderson, arXiv:2305.17493 (2023-05-27). https://arxiv.org/abs/2305.17493
  - Quote: training on model output causes *"irreversible defects in the resulting models, where tails of the original content distribution disappear."*
  - The Nature version is "AI models collapse when trained on recursively generated data", Nature 631 (July 2024), https://www.nature.com/articles/s41586-024-07566-y [bibliographic details from memory; page paywalled at fetch time].
- **"Is Model Collapse Inevitable? Breaking the Curse of Recursion by Accumulating Real and Synthetic Data"**, Gerstgrasser, Schaeffer et al., arXiv:2404.01413.
  - Quote: *"accumulating the successive generations of synthetic data alongside the original real data avoids model collapse"*, with test error provably bounded.
  - The failure mode is *replacing* real data, not *adding* synthetic data.
- Practical mitigations:
  - Always keep a real-data anchor.
  - Track provenance (a `source=synthetic` flag).
  - Add diversity controls (personas, Magpie, temperature).
  - Dedup synthetic outputs against each other.
  - Measure output diversity (distinct-n, embedding spread) on the quality card.
  - Ground in verifiers rather than self-judgment.

---

## 7. Synthetic RAG evaluation sets (RAGAS)

- Docs: "Testset Generation for RAG", https://docs.ragas.io/en/stable/getstarted/rag_testset_generation/ (ragas 0.4.3).
- Method: documents become nodes in a **`KnowledgeGraph`**.
  - `default_transforms` and `apply_transforms` add summaries, entities, embeddings and relationships. The docs example grows from 10 nodes to **48 nodes / 605 relationships**.
  - The graph then yields *scenarios*, and the scenarios yield queries.
- Default query distribution:
  - `SingleHopSpecificQuerySynthesizer`: 0.5
  - `MultiHopAbstractQuerySynthesizer`: 0.25
  - `MultiHopSpecificQuerySynthesizer`: 0.25

Code (condensed from the RAGAS docs):
```python
import openai
from langchain_community.document_loaders import DirectoryLoader
from langchain_openai import ChatOpenAI
from ragas.embeddings import OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.testset import TestsetGenerator

docs = DirectoryLoader("Sample_Docs_Markdown/", glob="**/*.md").load()
llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))
embeddings = OpenAIEmbeddings(client=openai.OpenAI())

generator = TestsetGenerator(llm=llm, embedding_model=embeddings)
dataset = generator.generate_with_langchain_docs(docs, testset_size=10)
dataset.to_pandas()   # user_input, reference_contexts, reference, synthesizer_name
```
Verification for synthetic RAG evaluation sets:
1. Check that the reference answer is supported by `reference_contexts` (judge faithfulness).
2. Remove questions answerable without retrieval (closed-book leak test).
3. Have humans spot-check about 5-10%.
4. Rebalance single-hop vs multi-hop to match real query logs.
5. Version the evaluation set and never train on it.

---

## 8. Real-world examples

- **Hugging Face**: FineWeb, FineWeb-Edu, FineWeb2 and FinePDFs. Built with DataTrove and used for the SmolLM family [SmolLM link not re-checked today].
- **Apple / Toyota Research / UW et al.**: DCLM. The DCLM-7B baseline is open [author affiliations UNVERIFIED in detail].
- **NVIDIA**: Nemotron-CC and NeMo Curator (16x GPU fuzzy dedup). Synthetic rephrasing is used for Nemotron pretraining.
- **Meta**: Llama 3 used rejection sampling, execution-verified code SFT and RM/Llama-judge filtering.
- **AI2**: Dolma, then OLMo. Tulu 3 used persona SFT plus RLVR, with fully open data.
- **Tencent AI Lab**: Persona Hub (1B personas). Tulu 3 used its personas for 285K SFT examples (sum of the persona subsets).
- **Anthropic**: Constitutional AI / RLAIF.
- **Bespoke Labs / Stanford / UW / Berkeley et al. (OpenThoughts consortium)**: OpenThoughts3 and OpenThinker3 [consortium membership UNVERIFIED in detail].
- **Argilla (Hugging Face)**: distilabel (AI feedback, UltraFeedback-style pipelines).

## 9. Open challenges (Oct 2026)

1. **Verification gap.** Verifiers exist for math and code but not for open-ended writing, long-horizon agents or RAG faithfulness at scale. LLM judges carry known biases.
2. **Verification does not always help SFT** (OpenThoughts), yet it is essential for RL. When should verification budget be spent?
3. **Over-filtering vs token budget.** Discarding about 90% (FineWeb-Edu, DCLM) runs out of unique tokens on 15T+ horizons. Nemotron-CC answers with rephrasing. What is the optimal trade-off between repetition, rephrasing and quality?
4. **Classifier monoculture.** Every lab filters for "educational-looking" text, which risks a narrow style and lost tails. This is collapse by curation rather than by recursion.
5. **Contamination.** Synthetic data from teachers trained on benchmarks leaks the test set indirectly. N-gram decontamination misses paraphrases.
6. **Teacher selection.** The best benchmark model is not the best teacher (QwQ-32B > DeepSeek-R1 as a teacher).
7. **Licensing and provenance.** Terms of service for distilling from closed models, PII in Common Crawl and PDFs, and the opt-out movement.
8. **Multilingual.** FineWeb2 covers 1000+ languages, but quality classifiers and judges are weak outside English.

## 10. Dataset quality card: what to report

Report the following:
- Sources with snapshot dates.
- Every filter with its removal rate (FineWeb style).
- Dedup level (per-snapshot vs global) and thresholds.
- Classifier: annotator model, number of labels, F1, and threshold.
- Synthetic share and the generator/teacher model(s).
- Verifier types and pass rates (for example, the Llama 3 note that 20% of code was self-corrected).
- Decontamination method and the benchmarks checked.
- Diversity metrics.
- License (for example ODC-BY).
- Known biases (the FineWeb-Edu card's "grade-school bias").

---

## Slide ideas (8)

1. **"90% of the web is thrown away"**: an animated funnel from 240T (DCLM-Pool) to 3.8T (DCLM-Baseline), with the FineWeb 15T to FineWeb-Edu 1.3T funnel beside it. Each filter stage fades out with its removal % (C4 terminal punctuation alone would remove 30%).
2. **"Distill an LLM judge into a tiny classifier"**: a 3-step flow. Llama-3-70B labels 460k pages, an arctic-embed + linear head reaches F1 82%, and 6,000 GPU-hours score 15T tokens. Then a chart: MMLU 33.6% at 38B tokens vs 300B for Matrix (10x).
3. **"Dedup paradox"**: two bars. Per-snapshot dedup gives 20T tokens and good results; global dedup gives 4T and worse results. A "too clean" warning icon. Short MinHash explainer (5-grams, 14x8 bands).
4. **"Four ways to make instructions"**: a 2x2 grid (Self-Instruct seeds, Evol-Instruct mutation tree, Magpie empty-template trick, Persona Hub persona x prompt). Animate the Magpie template being cut at the user slot.
5. **"Generate -> Verify -> Keep"**: a funnel animation through the verifier cascade (lint, unit tests, RM/judge, constitution) with the Llama 3 numbers: K=10-30, 2.7M code examples, 20% self-corrected.
6. **"Did verification help?"**: a contrast slide. OpenThoughts SFT shows "none gave significant improvements"; Tulu 3 RLVR and Llama 3 code show verification is essential. Open question for the audience.
7. **"Model collapse"**: a distribution plot whose tails shrink over generations (replace) vs a stable distribution (accumulate, Gerstgrasser 2024). Overlay the quotes.
8. **"Synthetic RAG evaluation sets in 10 lines"**: a knowledge-graph animation (10 nodes become 48 nodes and 605 edges), then a pie of the 50/25/25 synthesizer mix, then the RAGAS code.
9. **"Selection beats size"**: LESS's 5% beating 100%, and DSIR's hashed n-gram importance weights (diagram of the source vs target n-gram histograms).
10. **"The Dataset Quality Card"**: a template card filled in for FineWeb-Edu, as the closing artifact of the lifecycle.
