# Hands-on labs: retrieval quality (hybrid, RRF, rerankers, query transforms, contextual retrieval, parent-child, recall@k/MRR)

Research date: 2026-10-23. Scope: 9 runnable labs for the "retrieval quality" chapter of the 100-slide RAG deck.
The older research in `research-rag/02-advanced-retrieval.md` covers the theory (RRF paper, HyDE, step-back, Contextual Retrieval numbers). This file does not repeat it. It holds code, commands, outputs, errors and the new (Jul–Oct 2026) arXiv evidence.

**Honesty rules for this file**
- pip downloads are blocked on the research machine, so **only Lab 1's floor run (stdlib only) was executed**; all 10 code files were extracted and syntax-checked with `ast.parse`. Every other "Expected output" block is **illustrative**: it shows the shape and the plausible direction of the numbers, not measured values.
- Every import path, class, parameter and default was checked against the library source on GitHub at the tag that matches the PyPI version below. The file and line are cited in each lab.
- Items that could not be checked are marked **[UNVERIFIED]**.

---

## 0. Version table (PyPI JSON, read 2026-10-23)

| Package | Latest | Uploaded | Python | Used in |
|---|---|---|---|---|
| `bm25s` | **0.3.15** | 2026-10-22 | >=3.8 | L2, L3, L5, L7, L8 |
| `PyStemmer` | 3.1.0 | 2026-05-22 | – | L2 |
| `sentence-transformers` | **6.2.0** | 2026-10-21 | >=3.10 | L3–L9 |
| `qdrant-client` | **1.20.0** | 2026-10-22 | >=3.10 | L4 |
| `cohere` | **7.3.0** | 2026-10-21 | >=3.10,<4 | L6 |
| `voyageai` | 0.5.0 | 2026-07-10 | >=3.9,<3.15 | L6 |
| `google-genai` | **2.33.0** | 2026-10-23 | >=3.10 | L7 |
| `anthropic` | **2.3.0** | 2026-10-23 | >=3.10 | L8 |
| `langchain-classic` | 1.0.8 | 2026-06-10 | >=3.10 | L9 |
| `langchain-core` | 1.7.0 | 2026-10-22 | >=3.10 | L9 |
| `langchain-text-splitters` | 1.1.3 | 2026-10-02 | >=3.10 | L9 |
| `ranx` | 0.3.21 | 2025-08-07 | >=3.8 | L1 (optional) |
| `numpy` | 2.5.4 | 2026-10-10 | **>=3.12** | all |

Use **Python 3.12** for all labs. numpy 2.5.x needs 3.12+. On 3.10/3.11 pip silently picks an older numpy, which is fine but differs from the table.

**Dependency trap found while checking (worth a slide):** `langchain-huggingface` 1.2.3 declares `sentence-transformers<6.0.0,>=5.2.0` in its `[full]` extra (PyPI `requires_dist`). If you install it next to `sentence-transformers==6.2.0`, pip either downgrades sentence-transformers to 5.x or refuses with `ResolutionImpossible`. Lab 9 avoids the problem with a 6-line `Embeddings` adapter.

---

## 0.1 Shared scenario and labelled set: `kb.py`

**Scenario: "Northwind Outfitters" customer-support assistant.** An outdoor-gear retailer. Support agents ask questions about refunds, warranty, payment error codes and shipping. All labs use the same 18 chunks and 15 labelled queries, so the numbers can be compared across labs on one slide.

The chunks are written the way a naive splitter leaves them. Some are ambiguous on purpose (c07 "The window starts on the purchase date" does not name the product). The queries mix paraphrases (dense wins), exact error codes (BM25 wins), and one multi-part question (decomposition wins).

```python
# kb.py  -- shared corpus + labelled queries (qrels) for all labs
DOCS = {
    "D1": "Returns & Refunds Policy (US), v2026-09",
    "D2": "Warranty Policy: Tents and Backpacks",
    "D3": "Payments Troubleshooting Runbook for Support Agents",
    "D4": "Shipping & Delivery FAQ",
}
CHUNKS = [
    ("c01", "D1", "Northwind Outfitters accepts returns of unworn items within 30 days of delivery. Items must have original tags attached."),
    ("c02", "D1", "Refunds are issued to the original payment method within 5-7 business days after the warehouse scans the return."),
    ("c03", "D1", "Final-sale items, gift cards and personalised (monogrammed) products cannot be returned."),
    ("c04", "D1", "Members of the Trailhead loyalty programme get an extended window of 60 days."),
    ("c05", "D1", "If the parcel arrives damaged, report it within 48 hours with photos; we then ship a replacement at no cost."),
    ("c06", "D2", "All tents carry a 2-year limited warranty against manufacturing defects."),
    ("c07", "D2", "The window starts on the purchase date, not the delivery date. Proof of purchase is required."),
    ("c08", "D2", "Damage from misuse, UV degradation and normal wear is excluded."),
    ("c09", "D2", "Backpacks are covered for 5 years, including zips and buckles."),
    ("c10", "D2", "Claims are filed at northwind.example/warranty; an agent responds within 3 business days."),
    ("c11", "D3", "Error E-4012 means the card issuer declined the payment. Ask the customer to contact their bank or use another card."),
    ("c12", "D3", "Error E-4019 indicates a 3-D Secure authentication timeout; the customer should retry within 10 minutes."),
    ("c13", "D3", "Error P-220 appears when a gift card balance is lower than the order total; split the payment across two methods."),
    ("c14", "D3", "Never ask customers to read out the full card number or CVV over chat."),
    ("c15", "D4", "Standard shipping takes 3-5 business days inside the continental US and is free above $75."),
    ("c16", "D4", "Express shipping (1-2 business days) costs $14.95 and must be ordered before 1 pm Eastern."),
    ("c17", "D4", "We do not ship to PO boxes for orders containing stoves or fuel canisters."),
    ("c18", "D4", "International orders may incur import duties, which are paid by the recipient."),
]
QUERIES = {  # query_id: (text, set of relevant chunk ids)
    "q01": ("how long do I have to send back a jacket I haven't worn?", {"c01"}),
    "q02": ("customer sees E-4012 at checkout", {"c11"}),
    "q03": ("when will my money come back after a return?", {"c02"}),
    "q04": ("can I return a monogrammed backpack?", {"c03"}),
    "q05": ("my tent pole snapped after 18 months, is that covered?", {"c06"}),
    "q06": ("does the tent warranty start at delivery or at purchase?", {"c07"}),
    "q07": ("box came crushed, what do I do", {"c05"}),
    "q08": ("3DS timed out while paying", {"c12"}),
    "q09": ("gift card doesn't cover the whole order", {"c13"}),
    "q10": ("what is the free shipping threshold?", {"c15"}),
    "q11": ("loyalty member: how long is the return window and when is the refund paid?", {"c04", "c02"}),
    "q12": ("can you ship a camping stove to my PO box?", {"c17"}),
    "q13": ("who pays customs fees on orders to Canada?", {"c18"}),
    "q14": ("zipper broke on my pack after 3 years", {"c09"}),
    "q15": ("P-220", {"c13"}),
}
IDS = [c[0] for c in CHUNKS]
TEXT = {c[0]: c[2] for c in CHUNKS}
DOC_OF = {c[0]: c[1] for c in CHUNKS}
def doc_text(doc_id: str) -> str:
    return DOCS[doc_id] + "\n\n" + "\n".join(t for _, d, t in CHUNKS if d == doc_id)
```

**Teaching note.** 15 queries are enough to *show* the method on a slide. They are far too few to *decide* anything. One query flip changes recall@5 by 6.7 points. For real decisions use 100–300 labelled queries from real support tickets (see Lab 1 best practice and the 2026 annotation-sensitivity paper in §10).

---

## Lab 1. Measure first: recall@k, hit@k, MRR and nDCG on a labelled set

> **VERIFIED against stdlib only (executed by the lab author); ranx snippet not checked source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Build the 25-line evaluation harness that every later lab calls. You cannot claim that hybrid or reranking "helps" until you can print one table.

**Prerequisites.**
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install "numpy==2.5.4" "ranx==0.3.21"              # ranx is optional, for the cross-check only
```
No env vars.

**Code: `evalkit.py`**
```python
# evalkit.py -- retrieval metrics on a labelled set (no dependencies)
import math
from kb import QUERIES

def recall_at_k(ranked: list[str], gold: set[str], k: int) -> float:
    return len(set(ranked[:k]) & gold) / len(gold)

def hit_at_k(ranked: list[str], gold: set[str], k: int) -> float:
    return 1.0 if set(ranked[:k]) & gold else 0.0

def mrr(ranked: list[str], gold: set[str], k: int = 10) -> float:
    for rank, doc_id in enumerate(ranked[:k], start=1):
        if doc_id in gold:
            return 1.0 / rank
    return 0.0

def ndcg_at_k(ranked: list[str], gold: set[str], k: int) -> float:
    dcg = sum(1.0 / math.log2(r + 1) for r, d in enumerate(ranked[:k], start=1) if d in gold)
    ideal = sum(1.0 / math.log2(r + 1) for r in range(1, min(len(gold), k) + 1))
    return dcg / ideal

def evaluate(name: str, search, ks=(1, 3, 5)) -> dict:
    """search(query_text) -> ranked list of chunk ids, best first."""
    rows = {f"R@{k}": 0.0 for k in ks} | {"MRR@10": 0.0, "nDCG@5": 0.0}
    misses = []
    for qid, (text, gold) in QUERIES.items():
        ranked = search(text)
        for k in ks:
            rows[f"R@{k}"] += recall_at_k(ranked, gold, k)
        rows["MRR@10"] += mrr(ranked, gold)
        rows["nDCG@5"] += ndcg_at_k(ranked, gold, 5)
        if not hit_at_k(ranked, gold, 5):
            misses.append(qid)
    n = len(QUERIES)
    rows = {m: round(v / n, 3) for m, v in rows.items()}
    print(f"{name:<22}", "  ".join(f"{m}={v:.3f}" for m, v in rows.items()), "| miss@5:", misses)
    return rows

if __name__ == "__main__":
    from kb import IDS
    evaluate("corpus-order (floor)", lambda q: IDS)   # a 'retriever' that ignores the query
```

**Run.**
```bash
python evalkit.py
```

**Expected output (this one was executed: stdlib only, Python 3.12, 2026-10-23).**
```
corpus-order (floor)   R@1=0.067  R@3=0.233  R@5=0.333  MRR@10=0.197  nDCG@5=0.211 | miss@5: ['q02', 'q05', 'q06', 'q08', 'q09', 'q10', 'q12', 'q13', 'q14', 'q15']
```
The "floor" run is a sanity check. Any real retriever must beat it. If a retriever scores near the floor, the bug is usually in ID mapping, not in the model.

**Walk-through of key lines.**
- `len(set(ranked[:k]) & gold) / len(gold)`: recall@k is the fraction of the *gold* chunks found in the top k. For q11 (2 gold chunks) finding one of them gives 0.5, not 1.
- `hit_at_k`: "did at least one gold chunk appear". This is what Anthropic's Contextual Retrieval post reports as "1 − failure rate @20". Do not mix it up with recall when a query has several gold chunks.
- `return 1.0 / rank` at the first relevant hit: MRR only rewards the *first* relevant item. It tells you how far the LLM must "read down" the context.
- `ideal = ... min(len(gold), k)`: nDCG divides by the best possible ordering, so multi-gold queries are not penalised for having more answers.
- `evaluate(name, search)`: the harness takes any `search(text) -> list[id]` callable. BM25, hybrid, reranker and Qdrant all plug into the same function, so the numbers are comparable.

**Common errors.**
1. `ZeroDivisionError: division by zero` in `recall_at_k`. A query has an empty gold set (`set()`). Fix: drop unlabelled queries, or assert `all(gold for _, gold in QUERIES.values())` at load time.
2. All metrics are 0.000 for a real retriever. The retriever returns integer positions (`[3, 0, 7]`) while the qrels hold string IDs (`"c04"`). Fix: map positions back with `[IDS[i] for i in positions]`. bm25s and `CrossEncoder.rank` both return positions (Labs 2 and 5).
3. ranx cross-check gives a different MRR. ranx `mrr` uses the whole run by default, while this harness cuts at 10. Fix: compare against `"mrr@10"`. ranx metric names are documented in its README (`evaluate(qrels, run, ["map@5", "mrr"])`, https://github.com/AmenRa/ranx README "Evaluate").
4. ranx import fails on a fresh Python 3.12/3.13 env with a numba build error. ranx 0.3.21 (Aug 2025) depends on `numba>=0.54.1`. Whether numba wheels exist for your exact Python and numpy pair is **[UNVERIFIED]**. Fix: keep ranx in a separate env, or trust the 25-line harness.

**Optional cross-check with ranx (source: ranx README, "Create Qrels and Run" / "Evaluate").**
```python
from ranx import Qrels, Run, evaluate
qrels = Qrels({qid: {d: 1 for d in gold} for qid, (_, gold) in QUERIES.items()})
run = Run({qid: {d: 1.0 / (r + 1) for r, d in enumerate(search(text)[:10])} for qid, (text, _) in QUERIES.items()})
print(evaluate(qrels, run, ["recall@5", "mrr@10", "ndcg@5"]))
```

**Best practice.** Build the labelled set from **real queries** (support tickets, search logs) and label at the **evidence-span** level: mark every chunk that contains the answer, including overlapping chunks. The Oct 2026 breast-lesion RAG study (arXiv 2610.31606) found that curating the ground truth raised accepted chunk targets from 36 to 51 "without changing retrieval rankings". Incomplete labels make a good retriever look bad.

**Variation.** Add `evaluate(..., ks=(1, 3, 5, 10, 20))` and a per-query CSV dump, then sort by "lost queries" between two systems. The "Fusion Tax" paper (arXiv 2610.30612) shows that aggregate wins can hide per-query losses on 13–48% of queries. Report "queries that got worse" next to the mean.

---

## Lab 2. Lexical baseline: BM25 with `bm25s` (and the error-code trap)

> **VERIFIED against bm25s 0.3.15 wheel (FIXED: k capped at corpus size) source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Build a fast BM25 index over the support KB and measure it. Show that BM25 nails exact error codes (q02, q15) and misses paraphrases (q01, q07).

**Prerequisites.**
```bash
pip install "bm25s==0.3.15" "PyStemmer==3.1.0" "numpy==2.5.4"
```

**Source checked.** `bm25s/__init__.py` (main, 0.3.15): `class BM25.__init__(k1=1.5, b=0.75, delta=0.5, method="lucene", ...)` (lines 143–157); `retrieve(query_tokens, corpus=None, k=10, ..., return_as="tuple", show_progress=True, ...)` (line 676); `bm25s/tokenization.py` `tokenize(texts, lower=True, token_pattern=r"(?u)\b\w\w+\b", stopwords="english", stemmer=None, return_ids=True, show_progress=True, ...)` (line 569). Adapted from the bm25s README quickstart (https://github.com/xhluca/bm25s, "Quickstart").

**Code: `lab2_bm25.py`**
```python
# lab2_bm25.py -- BM25 baseline for the Northwind support KB
import re
import bm25s
import Stemmer
from kb import IDS, TEXT
from evalkit import evaluate

stemmer = Stemmer.Stemmer("english")
# Keep codes like "E-4012" / "P-220" as ONE token: the default pattern \b\w\w+\b drops the 1-letter "E".
CODE = re.compile(r"\b([A-Z])-(\d{2,5})\b", re.IGNORECASE)   # also catches "e-4012"
def normalise(text: str) -> str:
    return CODE.sub(r"\1\2", text)                    # "E-4012" -> "E4012"

corpus_tokens = bm25s.tokenize([normalise(TEXT[i]) for i in IDS], stopwords="en",
                               stemmer=stemmer, show_progress=False)
retriever = bm25s.BM25(k1=1.2, b=0.75)                # Lucene defaults would be k1=1.5 in bm25s
retriever.index(corpus_tokens, show_progress=False)

def bm25_search(query: str, k: int = 10) -> list[str]:
    q_tokens = bm25s.tokenize(normalise(query), stopwords="en", stemmer=stemmer, show_progress=False)
    k = min(k, len(IDS))                               # bm25s raises ValueError if k > corpus size (Lab 3 asks for 20 of 18)
    docs, scores = retriever.retrieve(q_tokens, corpus=IDS, k=k, show_progress=False)
    return [d for d, s in zip(docs[0], scores[0]) if s > 0]   # drop zero-score padding

if __name__ == "__main__":
    print(bm25_search("customer sees E-4012 at checkout")[:3])
    evaluate("BM25 (bm25s)", bm25_search)
    retriever.save("northwind_bm25", corpus=IDS)      # reload: bm25s.BM25.load("northwind_bm25", load_corpus=True)
```

**Run.**
```bash
python lab2_bm25.py
```

**Expected output (illustrative).**
```
['c11', 'c12', 'c13']
BM25 (bm25s)           R@1=0.600  R@3=0.733  R@5=0.767  MRR@10=0.680  nDCG@5=0.690 | miss@5: ['q01', 'q07', 'q13']
```
Read it as: BM25 wins q02/q15 (codes) and q04 (monogrammed), and loses "send back a jacket I haven't worn" (no shared words with "returns of unworn items" after stemming, except "unworn" ≠ "worn"), "box came crushed" (vs "parcel arrives damaged") and "customs fees" (vs "import duties").

**Walk-through.**
- `CODE.sub(r"\1\2", text)`: the bm25s default `token_pattern` is `(?u)\b\w\w+\b` (tokenization.py line 572). It needs 2+ word characters, so in "E-4012" the "E" is dropped and "4012" stays. Then "E-4012" and "X-4012" look the same. Gluing the code into "E4012" keeps it as one token. This is the single most common BM25 bug in support/IT corpora.
- `stopwords="en"`: accepted alias of `"english"` (tokenization.py line 528, `_infer_stopwords`).
- `stemmer=stemmer` on **both** corpus and query: the stemmer must be applied the same way on both sides, or "returns" and "return" never match.
- `retriever.retrieve(q_tokens, corpus=IDS, k=k)`: passing `corpus=IDS` makes bm25s return your string IDs instead of positions (docstring of `retrieve`). Results are arrays shaped `(n_queries, k)`, so take row `[0]`.
- `if s > 0`: bm25s always returns k rows. With an 18-chunk corpus, many tail rows have score 0. If you keep them, the evaluator counts random tail hits as "found".

**Common errors.**
1. `ValueError: k of 20 is larger than the number of available scores, which is 18 (corpus size should be larger than top-k). Please set with a smaller k or increase the size of corpus.` (exact text, `__init__.py` `retrieve`). Fix: `k=min(k, len(IDS))`.
2. Every query returns the same 10 IDs with score 0.0. The corpus was stemmed and the query was not (or the other way round). Fix: pass the same `stemmer=` and `stopwords=` to both `tokenize` calls.
3. `ValueError: `return_as` must be either 'tuple' or 'documents'` (exact). Fix: use one of the two values. `return_as="documents"` returns only the docs array.
4. `ImportError` / `Numba is not installed. Please install numba with `pip install numba` to use the numba backend.` You set `backend="numba"` without numba. Fix: keep the default `backend="numpy"` for small corpora, or `pip install numba`.

**Best practice.** Normalise the domain identifiers (error codes, SKUs, policy numbers, ticket IDs) **before** tokenising, on the corpus and on the query, with one shared function. Keep a unit test such as `assert "e4012" in bm25s.tokenize(normalise("E-4012"), return_ids=False)[0]`.

**Variation.** Try `method="bm25+"` or `method="bm25l"` (bm25s supports `lucene`, `robertson`, `atire`, `bm25l`, `bm25+` per its README "Variants"), and `stopwords="en_plus"`. Measure each with `evaluate`. Expect differences under 2 points on this tiny set. Do not over-read them.

---

## Lab 3. Dense retrieval + hybrid with Reciprocal Rank Fusion (from scratch)

> **VERIFIED against sentence-transformers 6.2.0 wheel source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Add a dense retriever (BGE-small) and fuse it with BM25 using RRF. Print BM25 vs dense vs hybrid on one table.

**Prerequisites.**
```bash
pip install "sentence-transformers==6.2.0" "bm25s==0.3.15" "PyStemmer==3.1.0"
# first run downloads BAAI/bge-small-en-v1.5 (~130 MB) from Hugging Face; set HF_TOKEN only if your network requires it
```

**Source checked.** sentence-transformers v6.2.0, `sentence_transformers/sentence_transformer/model.py`: `encode_query(inputs, prompt_name=None, prompt=None, batch_size=32, ..., normalize_embeddings=False, ...)` (line 331), `encode_document(...)` (line 494), `similarity(embeddings1, embeddings2) -> Tensor` (line 1056). The docstring says: if the model has no predefined prompts, `encode`, `encode_query` and `encode_document` "will return identical embeddings". BGE v1.5 query instruction `Represent this sentence for searching relevant passages: ` is from the model card (https://huggingface.co/BAAI/bge-small-en-v1.5, model table). `config_sentence_transformers.json` of that model has **no** `prompts` key (checked), so you must pass `prompt=` yourself.

**Code: `lab3_hybrid.py`**
```python
# lab3_hybrid.py -- dense (BGE) + BM25, fused with Reciprocal Rank Fusion
from sentence_transformers import SentenceTransformer
from kb import IDS, TEXT
from evalkit import evaluate
from lab2_bm25 import bm25_search

model = SentenceTransformer("BAAI/bge-small-en-v1.5")
BGE_QUERY = "Represent this sentence for searching relevant passages: "
doc_emb = model.encode_document([TEXT[i] for i in IDS], normalize_embeddings=True)

def dense_search(query: str, k: int = 10) -> list[str]:
    q_emb = model.encode_query(query, prompt=BGE_QUERY, normalize_embeddings=True)
    scores = model.similarity(q_emb, doc_emb)[0]            # cosine, shape (n_docs,)
    top = scores.argsort(descending=True)[:k].tolist()
    return [IDS[i] for i in top]

def rrf(rankings: list[list[str]], k: int = 60, weights: list[float] | None = None) -> list[str]:
    weights = weights or [1.0] * len(rankings)
    fused: dict[str, float] = {}
    for w, ranking in zip(weights, rankings):
        for rank, doc_id in enumerate(ranking, start=1):
            fused[doc_id] = fused.get(doc_id, 0.0) + w / (k + rank)
    return sorted(fused, key=fused.get, reverse=True)

def hybrid_search(query: str, depth: int = 20, k_rrf: int = 60) -> list[str]:
    return rrf([bm25_search(query, depth), dense_search(query, depth)], k=k_rrf)

if __name__ == "__main__":
    evaluate("BM25", bm25_search)
    evaluate("dense (bge-small)", dense_search)
    evaluate("hybrid RRF k=60", hybrid_search)
    evaluate("hybrid RRF k=2", lambda q: hybrid_search(q, k_rrf=2))
    evaluate("hybrid RRF dense x2", lambda q: rrf([bm25_search(q, 20), dense_search(q, 20)], weights=[1, 2]))
```

**Run.**
```bash
python lab3_hybrid.py
```

**Expected output (illustrative).**
```
BM25                   R@1=0.600  R@3=0.733  R@5=0.767  MRR@10=0.680  nDCG@5=0.690 | miss@5: ['q01', 'q07', 'q13']
dense (bge-small)      R@1=0.600  R@3=0.800  R@5=0.867  MRR@10=0.710  nDCG@5=0.740 | miss@5: ['q15']
hybrid RRF k=60        R@1=0.667  R@3=0.867  R@5=0.933  MRR@10=0.770  nDCG@5=0.800 | miss@5: []
hybrid RRF k=2         R@1=0.667  R@3=0.833  R@5=0.900  MRR@10=0.760  nDCG@5=0.780 | miss@5: ['q11']
hybrid RRF dense x2    R@1=0.667  R@3=0.867  R@5=0.933  MRR@10=0.775  nDCG@5=0.805 | miss@5: []
```
The pattern to teach (not the exact numbers): dense fixes the paraphrase misses, BM25 fixes the bare code "P-220", and the fused list covers both. Hybrid often wins on **recall@5** more than on **R@1**.

**Walk-through.**
- `model.encode_query(query, prompt=BGE_QUERY, ...)`: BGE v1.5 was trained with a query instruction. The model ships without a `prompts` config, so `encode_query` alone adds nothing. Pass `prompt=` explicitly. Documents get no prefix.
- `normalize_embeddings=True` on both sides: unit vectors make dot product equal cosine. If you later move to a vector DB with `Distance.DOT`, normalisation keeps scores the same.
- `model.similarity(q_emb, doc_emb)[0]`: returns a torch tensor of shape `[1, n_docs]` using the model's `similarity_fn_name` (cosine by default).
- `w / (k + rank)`: the Cormack et al. (SIGIR 2009) formula with an optional weight per list. Weighted RRF is the same idea as Qdrant's `Rrf(weights=[...])` (Lab 4).
- `depth=20`: each retriever contributes its top 20 to the fusion. Depth matters as much as k. A gold chunk at dense rank 25 cannot be rescued by fusion.

**Common errors.**
1. `OSError: We couldn't connect to 'https://huggingface.co' to load the files...` on an offline machine. Fix: download once with network, then set `HF_HUB_OFFLINE=1`, or pass a local folder path to `SentenceTransformer(...)`.
2. `RuntimeError: ... must be on the same device` / `Expected all tensors to be on the same device` when `doc_emb` is a CPU numpy array and `q_emb` a CUDA tensor. Fix: keep the defaults (`convert_to_numpy=True` for both), or pass `device="cpu"` to `SentenceTransformer`.
3. Dense recall is mysteriously lower than BM25. You used `model.encode(...)` for queries and forgot the BGE instruction, or used an E5/Qwen3/EmbeddingGemma model whose required prefix differs. Fix: read the model card's "query instruction" row; for models that ship `prompts` in their config, `encode_query`/`encode_document` apply them automatically.
4. `TypeError: '<' not supported between instances of 'NoneType' and 'float'` in `sorted(...)`. A retriever returned `None` for a doc. Fix: return lists of IDs only, never `None`.

**Best practice.** Decide fusion **per corpus with your labelled set**, not by default. "The Fusion Tax" (arXiv 2610.30612, 22 Oct 2026) found that even the best fusion method ranks relevant documents below the dense-only retriever on **8–21% of queries**, and that "RRF carries the higher tax wherever the dense retriever is clearly stronger and only beats dense-only where the two components are balanced". Run `evaluate` on BM25, dense and hybrid, and keep a list of the queries hybrid made worse.

**Variation.** Replace fixed weights with a query-type router: if the query contains a code pattern (`CODE.search(query)`), use `weights=[3, 1]`, else `[1, 2]`. The Thomson Reuters study (arXiv 2610.24341, 17 Oct 2026) found that "74 of 128 dynamic fusion methods tested were significantly better than standard RRF", and that the per-query optimal weight is "an interval rather than a point". So a coarse two-bucket router is a reasonable first step.

---

## Lab 4. Hybrid inside the vector DB: Qdrant 1.20 dense + native BM25 + server-side RRF

> **VERIFIED against qdrant-client 1.20.0 wheel (local mode) source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Move hybrid search into one Qdrant call: dense vectors and Qdrant's **native BM25 text query** (`models.TextQuery`) are both prefetched and fused with `RrfQuery`. Runs in local mode (`":memory:"`), no server needed.

**Prerequisites.**
```bash
pip install "qdrant-client==1.20.0" "sentence-transformers==6.2.0"
# optional server instead of local mode:  docker run -p 6333:6333 qdrant/qdrant
```

**Source checked (qdrant-client tag v1.20.0).**
- `http/models/models.py`: `class TextQuery(text: TextInterface)` "Rank by BM25 over the text index of the payload field named by `using`, which must have `scoring` set" (line 3819); `TextIndexParams(..., scoring: Optional[TextScoringInterface])` "Enable ranking points by BM25 over this field; `true` for the defaults" (line 3805); `Bm25Params(k: default 1.2, b: default 0.75)` (line 176); `Rrf(k: Optional[int], weights: Optional[List[float]])` (line 2965); `RrfQuery(rrf: Rrf)` (line 2977).
- `local/local_collection.py`: local mode fuses `RrfQuery` with `ranking_constant_k=query.rrf.k, weights=query.rrf.weights` (lines ~999–1007) and supports `TextQuery` only with default tokenization (lines 1248–1262).
- `hybrid/fusion.py`: `DEFAULT_RANKING_CONSTANT_K = 2` (line 4).
- Qdrant docs "Hybrid and Multi-Stage Queries" (https://qdrant.tech/documentation/concepts/hybrid-queries/): "k is a constant (set to 2 by default)"; parameterised k "Available as of v1.16.0"; weighted RRF "Available as of v1.17.0"; prefetch `limit` must be "at least `limit + offset` of the main query", "otherwise you can get an empty result".

**Code: `lab4_qdrant.py`**
```python
# lab4_qdrant.py -- one-call hybrid search in Qdrant: dense + native BM25, fused by RRF
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from kb import CHUNKS
from evalkit import evaluate

client = QdrantClient(":memory:")                     # or QdrantClient(url="http://localhost:6333")
model = SentenceTransformer("BAAI/bge-small-en-v1.5")
BGE_QUERY = "Represent this sentence for searching relevant passages: "

client.create_collection(
    collection_name="northwind_kb",
    vectors_config={"dense": models.VectorParams(size=384, distance=models.Distance.COSINE)},
)
client.create_payload_index(                          # BM25 over the 'text' payload field
    collection_name="northwind_kb", field_name="text",
    field_schema=models.TextIndexParams(type=models.TextIndexType.TEXT, scoring=True),
)
vectors = model.encode_document([t for _, _, t in CHUNKS], normalize_embeddings=True)
client.upsert(collection_name="northwind_kb", points=[
    models.PointStruct(id=n, vector={"dense": vectors[n].tolist()},
                       payload={"chunk_id": cid, "doc_id": did, "text": text})
    for n, (cid, did, text) in enumerate(CHUNKS)
])

def qdrant_hybrid(query: str, limit: int = 10, k_rrf: int = 60) -> list[str]:
    q_vec = model.encode_query(query, prompt=BGE_QUERY, normalize_embeddings=True).tolist()
    res = client.query_points(
        collection_name="northwind_kb",
        prefetch=[
            models.Prefetch(query=models.TextQuery(text=query), using="text", limit=20),
            models.Prefetch(query=q_vec, using="dense", limit=20),
        ],
        query=models.RrfQuery(rrf=models.Rrf(k=k_rrf)),   # default k is 2, not 60
        limit=limit,
    )
    return [p.payload["chunk_id"] for p in res.points]

if __name__ == "__main__":
    print(qdrant_hybrid("3DS timed out while paying")[:3])
    evaluate("qdrant RRF k=60", qdrant_hybrid)
    evaluate("qdrant RRF default k", lambda q: qdrant_hybrid(q, k_rrf=None))
```

**Run.**
```bash
python lab4_qdrant.py
```

**Expected output (illustrative).**
```
['c12', 'c11', 'c13']
qdrant RRF k=60        R@1=0.667  R@3=0.867  R@5=0.933  MRR@10=0.765  nDCG@5=0.795 | miss@5: []
qdrant RRF default k   R@1=0.667  R@3=0.833  R@5=0.900  MRR@10=0.755  nDCG@5=0.780 | miss@5: ['q11']
```
Numbers should be close to Lab 3 but not identical. Qdrant's BM25 uses its own word tokenizer without stemming or code gluing, so q15 "P-220" can behave differently from the bm25s version.

**Walk-through.**
- `TextIndexParams(type=TEXT, scoring=True)`: `scoring=True` turns a filter-only full-text index into a BM25-ranked one ("Changing it rebuilds the index", models.py). Without it, a `TextQuery` fails (error 2 below).
- `models.Prefetch(query=models.TextQuery(text=query), using="text", ...)`: for a text query, `using` names the **payload field**, not a vector ("`using` names the payload field of a text query, not a vector", local_collection.py comment, line ~1093).
- `vector={"dense": ...}`: named vectors. The `using="dense"` in the second prefetch must match the name in `vectors_config`.
- `models.RrfQuery(rrf=models.Rrf(k=k_rrf))`: fusion runs inside Qdrant. **Qdrant's default k is 2**, the paper's is 60. With k=2, rank 1 scores 1/3 and rank 10 scores 1/12, so one list's top hit dominates. With k=60 the curve is flat and agreement between lists dominates.
- `PointStruct(id=n, ...)`: point IDs must be unsigned integers or UUIDs. Keep your business ID (`"c01"`) in the payload.

**Common errors.**
1. `ValueError: Collection northwind_kb already exists` (exact, `qdrant_local.py` line ~1002) when you rerun against a persisted path (`QdrantClient(path="./qdrant_data")`). Fix: `if not client.collection_exists("northwind_kb"): client.create_collection(...)`.
2. `ValueError: A text query needs a text index with `scoring` on `text`` (exact, local_collection.py `_text_query_params`). The payload index is missing or was created without `scoring=True`. Fix: create the index as in the code, before querying.
3. `NotImplementedError: Text queries in the local Qdrant only support text indexes with the default tokenization. Please use server Qdrant if you need other text index params.` (exact). You set `stemmer=`, `stopwords=`, `ascii_folding=True` or a non-word tokenizer in local mode (`has_default_tokenization`, `local/bm25.py` lines 15–26). Fix: use a Qdrant server for stemming/stopwords, or keep the defaults locally.
4. Empty result list even though both prefetches return points. A prefetch `limit` is smaller than the main `limit + offset`. Fix: set each prefetch `limit` ≥ final `limit + offset` (docs warning above). A point ID that is a plain string such as `"c01"` is rejected because IDs must be integers or UUIDs. The exact local-mode error text is **[UNVERIFIED]**.

**Best practice.** Pin `Rrf(k=60)` (or a k you tuned on the labelled set) explicitly in code and in the config review. Defaults differ between engines: Qdrant k=2, the paper k=60. Changing engines silently changes ranking.

**Variation.** Weighted RRF to trust lexical more for code-like queries: `models.RrfQuery(rrf=models.Rrf(k=60, weights=[3.0, 1.0]))` (v1.17.0+; "The number of weights should match the number of prefetches", models.py line 2971). Or swap fusion for DBSF: `query=models.FusionQuery(fusion=models.Fusion.DBSF)`.

---

## Lab 5. Second stage: cross-encoder reranking with `CrossEncoder.rank`

> **VERIFIED against sentence-transformers 6.2.0 wheel source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Retrieve 20 hybrid candidates, rerank them with a cross-encoder, keep the top 5. Measure MRR before and after.

**Prerequisites.**
```bash
pip install "sentence-transformers==6.2.0" "bm25s==0.3.15" "PyStemmer==3.1.0"
# downloads cross-encoder/ms-marco-MiniLM-L6-v2 (~90 MB); variation uses BAAI/bge-reranker-v2-m3 (~2.3 GB)
```

**Source checked.** sentence-transformers v6.2.0 `cross_encoder/model.py`: `CrossEncoder.__init__(model_name_or_path, *, device=None, ..., max_length=None, activation_fn=None, ...)` (line 161); `rank(query, documents, top_k=None, return_documents=False, ..., batch_size=32, ...) -> list[dict["corpus_id","score","text"]]` (line 712); `get_default_activation_fn`: uses the model config's activation, else `nn.Sigmoid()` when `num_labels == 1` (lines 358–379). The `cross-encoder/ms-marco-MiniLM-L6-v2` `config.json` sets `"sbert_ce_default_activation_function": "torch.nn.modules.linear.Identity"`, so `rank()` returns **raw logits** (model card example prints `[ 8.607138 -4.320078]`). Model card: https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2 (adapted from SBERT "Retrieve & Re-rank").

**Code: `lab5_cross_encoder.py`**
```python
# lab5_cross_encoder.py -- hybrid top-20 -> cross-encoder -> top-5
import time
from sentence_transformers import CrossEncoder
from kb import TEXT
from evalkit import evaluate
from lab3_hybrid import hybrid_search

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2", max_length=512)

def rerank_search(query: str, candidates: int = 20, keep: int = 10) -> list[str]:
    cand_ids = hybrid_search(query)[:candidates]
    hits = reranker.rank(query, [TEXT[i] for i in cand_ids], top_k=keep, batch_size=32)
    return [cand_ids[h["corpus_id"]] for h in hits]       # corpus_id = position in cand_ids

if __name__ == "__main__":
    q = "zipper broke on my pack after 3 years"
    for h in reranker.rank(q, [TEXT[i] for i in hybrid_search(q)[:5]], return_documents=True):
        print(f'{h["score"]:7.2f}  {h["text"][:60]}')
    evaluate("hybrid", hybrid_search)
    t0 = time.perf_counter()
    evaluate("hybrid + MiniLM-L6 CE", rerank_search)
    print(f"rerank latency per query: {(time.perf_counter() - t0) / 15 * 1000:.0f} ms (CPU)")
```

**Run.**
```bash
python lab5_cross_encoder.py
```

**Expected output (illustrative).**
```
   6.91  Backpacks are covered for 5 years, including zips and buckles
  -2.48  Damage from misuse, UV degradation and normal wear is excluded
  -6.10  All tents carry a 2-year limited warranty against manufactur
  -9.73  Claims are filed at northwind.example/warranty; an agent res
 -10.42  Final-sale items, gift cards and personalised (monogrammed)
hybrid                 R@1=0.667  R@3=0.867  R@5=0.933  MRR@10=0.770  nDCG@5=0.800 | miss@5: []
hybrid + MiniLM-L6 CE  R@1=0.800  R@3=0.933  R@5=0.933  MRR@10=0.860  nDCG@5=0.870 | miss@5: []
rerank latency per query: 40 ms (CPU)
```
Teaching point: reranking cannot raise recall@20 (it only reorders the 20 candidates). It moves the gold chunk **up**, so R@1 and MRR rise. The latency figure is a placeholder **[UNVERIFIED]**; measure it on your hardware.

**Walk-through.**
- `CrossEncoder(..., max_length=512)`: pairs longer than 512 tokens are truncated. MiniLM is a BERT model with `max_position_embeddings: 512` (config.json). Long parent sections get cut, which is a reason to rerank **child** chunks.
- `reranker.rank(query, docs, top_k=keep)`: returns a sorted list of dicts `{"corpus_id", "score"}`. `corpus_id` is the index into the list you passed, not your chunk ID.
- `cand_ids[h["corpus_id"]]`: map back to business IDs. Forgetting this is error 1 below.
- `h["score"]`: raw logits for this model (Identity activation). Do not threshold at 0.5. Models without a stored activation and with one output label get a sigmoid, which gives 0–1 scores.
- `candidates=20`: the rerank budget. Cost grows linearly with candidates. Anthropic's Contextual Retrieval setup retrieved 150 and kept 20 (older research file 02 §5.4).

**Common errors.**
1. All metrics drop to near the floor after reranking. You returned `h["corpus_id"]` (an int 0–19) instead of `cand_ids[h["corpus_id"]]`. Fix: map positions back to IDs.
2. `Token indices sequence length is longer than the specified maximum sequence length for this model (613 > 512)` (tokenizer warning). Fix: rerank chunks, not full documents, or set `max_length` and accept truncation; for long inputs use a long-context reranker (Lab 6 APIs accept 32K tokens per doc).
3. A score threshold `score > 0.5` drops most good results. Logits for this model range roughly −11 to +11. Fix: rank only, or pass `activation_fn=torch.nn.Sigmoid()` to `CrossEncoder(...)` to get 0–1 values, then tune the threshold on the labelled set.
4. `Activation function path '...' is not trusted, using default activation function instead.` (warning text from `_resolve_activation_fn`, model.py line 352). A model config names a non-`torch.` activation. Fix: pass `trust_remote_code=True` only for models you trust, or set `activation_fn` explicitly.

**Best practice.** Size the rerank budget to the **context window**, not to "top-1". BoundaryMORPH (arXiv 2609.27213, Sep 2026) points out that when the cross-encoder budget is smaller than the number of chunks the LLM will read, standard reranking "wastes compute verifying obvious top candidates while ignoring relevant documents further down". For agents that read 10 chunks, rerank 30–50 and keep 10.

**Variation.** Swap in the multilingual `BAAI/bge-reranker-v2-m3` (0.6B, model card https://huggingface.co/BAAI/bge-reranker-v2-m3) with the same `CrossEncoder(...)` line and compare MRR and latency. Also test the negation trap: "Preference Is Not Position" (arXiv 2610.26260) shows a pairwise-trained ranker *improved* pairwise preference (56.62% vs 52.30%) while *cutting* the preferred passage's MRR from 0.5764 to 0.3055. Measure MRR, not only "which of two is better".

---

## Lab 6. Hosted rerank APIs: Cohere Rerank v5 (with relevant spans) and Voyage rerank-3

> **VERIFIED against cohere 7.3.0 + voyageai 0.5.0 wheels; rerank-3 model name on docs.voyageai.com source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Rerank the same 20 candidates through two vendor APIs. Use Cohere's v5 `relevant_spans` to cut each chunk to its relevant sentence before it goes to the LLM.

**Prerequisites.**
```bash
pip install "cohere==7.3.0" "voyageai==0.5.0" "sentence-transformers==6.2.0" "bm25s==0.3.15" "PyStemmer==3.1.0"
export CO_API_KEY=...        # Cohere (COHERE_API_KEY is also accepted, client.py line 578)
export VOYAGE_API_KEY=...    # Voyage
```

**Source checked.**
- cohere-python tag `7.3.0`, `src/cohere/v2/client.py` line 556: `rerank(*, model, query, documents: Sequence[str], top_n=OMIT, max_tokens_per_doc=OMIT, relevant_spans: Optional[RerankRelevantSpans]=OMIT, priority=OMIT, request_options=None) -> V2RerankResponse`. Docstring: `max_tokens_per_doc` "Defaults to `4096`"; "we recommend against sending more than 1,000 documents in a single request". `types/rerank_relevant_spans.py`: `RerankRelevantSpans(mode: "enabled"|"disabled", threshold: default 0.1, max_spans)`, "only supported for Rerank v5 and newer models". `v2/types/v2rerank_response_results_item.py`: `index`, `relevance_score` ("normalized to be in the range [0, 1]"), `relevant_spans: list[RerankRelevantSpanResponse]` with `start`, `end` (Unicode codepoints, `[start, end)`), `score`. The SDK docstring example uses `model="rerank-v5.0-pro"`. `ClientV2` constructor: `client_v2.py` line 31.
- voyageai-python main (0.5.0), `voyageai/client.py` line 167: `rerank(query, documents, model, top_k=None, truncation=True) -> RerankingObject`; `object/reranking.py`: `RerankingResult(index, document, relevance_score)`. Voyage docs (https://docs.voyageai.com/docs/reranker): current models `rerank-3` and `rerank-3-lite`, 32,000-token context, max 1,000 documents, query ≤ 8,000 tokens, total ≤ 600K tokens per request.

**Code: `lab6_api_rerank.py`**
```python
# lab6_api_rerank.py -- Cohere Rerank v5 (+ relevant spans) and Voyage rerank-3 on hybrid candidates
import cohere
import voyageai
from cohere import RerankRelevantSpans
from kb import TEXT
from evalkit import evaluate
from lab3_hybrid import hybrid_search

co = cohere.ClientV2()                    # reads CO_API_KEY
vo = voyageai.Client()                    # reads VOYAGE_API_KEY

def cohere_search(query: str, candidates: int = 20) -> list[str]:
    ids = hybrid_search(query)[:candidates]
    resp = co.rerank(model="rerank-v5.0-pro", query=query, documents=[TEXT[i] for i in ids],
                     top_n=10, max_tokens_per_doc=1024)
    return [ids[r.index] for r in resp.results]

def voyage_search(query: str, candidates: int = 20) -> list[str]:
    ids = hybrid_search(query)[:candidates]
    out = vo.rerank(query, [TEXT[i] for i in ids], model="rerank-3", top_k=10)
    return [ids[r.index] for r in out.results]

def compressed_context(query: str, keep: int = 3) -> list[str]:
    """Return only the sentences Cohere marks as relevant: smaller, cleaner LLM context."""
    ids = hybrid_search(query)[:20]
    docs = [TEXT[i] for i in ids]
    resp = co.rerank(model="rerank-v5.0-pro", query=query, documents=docs, top_n=keep,
                     relevant_spans=RerankRelevantSpans(mode="enabled", threshold=0.3, max_spans=2))
    out = []
    for r in resp.results:
        spans = r.relevant_spans or []
        text = " ... ".join(docs[r.index][s.start:s.end] for s in spans) or docs[r.index]
        out.append(f"[{ids[r.index]} {r.relevance_score:.2f}] {text}")
    return out

if __name__ == "__main__":
    print("\n".join(compressed_context("loyalty member: how long is the return window and when is the refund paid?")))
    evaluate("hybrid + Cohere v5 pro", cohere_search)
    evaluate("hybrid + Voyage rr-3", voyage_search)
```

**Run.**
```bash
python lab6_api_rerank.py
```

**Expected output (illustrative).**
```
[c04 0.91] Members of the Trailhead loyalty programme get an extended window of 60 days.
[c02 0.77] Refunds are issued to the original payment method within 5-7 business days
[c01 0.42] Northwind Outfitters accepts returns of unworn items within 30 days of delivery.
hybrid + Cohere v5 pro R@1=0.800  R@3=0.967  R@5=0.967  MRR@10=0.880  nDCG@5=0.890 | miss@5: []
hybrid + Voyage rr-3   R@1=0.800  R@3=0.933  R@5=0.967  MRR@10=0.870  nDCG@5=0.880 | miss@5: []
```
Do not present one vendor as "better" from 15 queries. Vendor benchmark claims (e.g. Voyage vs Cohere percentages) are **[UNVERIFIED]** vendor claims; see older file 02 §5.2.

**Walk-through.**
- `cohere.ClientV2()`: the v2 client. `co.rerank(...)` resolves to `V2Client.rerank` (keyword-only arguments).
- `[ids[r.index] for r in resp.results]`: both APIs return the **index into the list you sent**, sorted by relevance. Map it back.
- `max_tokens_per_doc=1024`: default is 4096. Lower values cut cost and latency for short chunks; long docs are truncated silently.
- `RerankRelevantSpans(mode="enabled", threshold=0.3, max_spans=2)`: v5 returns character spans `[start, end)` per document. Slicing `docs[r.index][s.start:s.end]` gives "context compression" without a second LLM call.
- `r.relevant_spans or []`: spans are returned "only when the request enabled `relevant_spans` and the model found at least one span". Fall back to the full chunk when it is `None`.

**Common errors.**
1. `cohere.core.api_error.ApiError: ... The client must be instantiated be either passing in token or setting CO_API_KEY` (exact text in `base_client.py` line 139, typo included). Fix: `export CO_API_KEY=...`.
2. `voyageai.error.AuthenticationError: An API key is required for API-based models. Set your API key via the VOYAGE_API_KEY environment variable or pass it to the client (api_key=...).` (exact, `voyageai/_base.py` `_require_api_key`). Fix: set `VOYAGE_API_KEY`.
3. HTTP 400 when sending `relevant_spans` with `model="rerank-v3.5"` or `rerank-v4.0-*`. The type docstring says spans are "only supported for Rerank v5 and newer models". The exact server message is **[UNVERIFIED]**. Fix: use `rerank-v5.0-pro` or `rerank-v5.0-fast`.
4. HTTP 429 rate-limit errors during a batch evaluation loop (15 queries × 2 calls). Fix: cache rerank responses per `(model, query, tuple(ids))` while you iterate on the eval; use `priority=` (Cohere v2 parameter, lower = earlier) for interactive traffic.

**Best practice.** Treat the reranker score as a **ranking signal**, not a probability. Cohere's own docstring: "It is not accurate to assume a score of 0.9 means the document is 2x more relevant than a document with a score of 0.45." If you need a cut-off ("no good answer, escalate to a human"), tune it on labelled data, per model version, and re-tune after every model upgrade.

**Variation.** Measure answer impact, not only MRR. The longitudinal clinical-notes study (arXiv 2610.01324, Oct 2026) saw MedCPT cross-encoder reranking raise Hit@10 from 46.6% to 60.6% and MRR from 0.2371 to 0.3252, but judge-rated answer correctness only from 44.8% to 48.6%: "gains in retrieval do not translate proportionally into gains in answer correctness". Add a small answer-level check after reranking.

---

## Lab 7. Query transformation with Gemini: multi-query, HyDE and decomposition in one structured call

> **VERIFIED against google-genai 2.33.0 wheel source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** One Gemini call returns three rewrites (paraphrases, a hypothetical answer passage, sub-questions). Retrieve for each, fuse with RRF ("RAG-Fusion"), and compare against the plain hybrid baseline. Fix q11 (the two-part question).

**Prerequisites.**
```bash
pip install "google-genai==2.33.0" "pydantic>=2.7" "sentence-transformers==6.2.0" "bm25s==0.3.15" "PyStemmer==3.1.0"
export GEMINI_API_KEY=...     # GOOGLE_API_KEY wins if both are set (_api_client.py line 168-172)
```

**Source checked.** python-genai main (`version.py` 2.33.0), `google/genai/types.py`: `GenerateContentConfig.response_mime_type` (line 6650), `.response_schema: Optional[SchemaUnion]` "If set, a compatible response_mime_type must also be set" (line 6660), `.response_json_schema` alternative (line 6673), `.thinking_config` (line 6755); `ThinkingConfig.thinking_level` with `ThinkingLevel` values `MINIMAL|LOW|MEDIUM|HIGH` (lines 376–388, 5815); `GenerateContentResponse.parsed` "First candidate from the parsed response if response_schema is provided. Not available for streaming." (line 8801). Model ID `gemini-3.8-flash` is listed as stable on https://ai.google.dev/gemini-api/docs/models (read 2026-10-23). Pattern adapted from the Gemini API "Structured output" guide (https://ai.google.dev/gemini-api/docs/structured-output) **[page not re-read in this pass]**.

**Code: `lab7_query_transform.py`**
```python
# lab7_query_transform.py -- multi-query + HyDE + decomposition, fused with RRF
from functools import lru_cache
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from evalkit import evaluate
from lab2_bm25 import bm25_search
from lab3_hybrid import dense_search, hybrid_search, rrf

client = genai.Client()                                   # reads GEMINI_API_KEY / GOOGLE_API_KEY

class Rewrites(BaseModel):
    paraphrases: list[str] = Field(description="3 rewordings using policy vocabulary")
    hypothetical_answer: str = Field(description="2-sentence passage that would answer the question")
    sub_questions: list[str] = Field(description="1-3 self-contained sub-questions; 1 if the question is simple")

PROMPT = ("You rewrite customer-support questions for search over an outdoor retailer's policy KB "
          "(returns, refunds, warranty, payment error codes, shipping). Keep error codes exactly as written.\n"
          "Question: {q}")

@lru_cache(maxsize=1024)                                  # never pay twice for the same query
def rewrite(query: str) -> Rewrites:
    resp = client.models.generate_content(
        model="gemini-3.8-flash", contents=PROMPT.format(q=query),
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=Rewrites,
            thinking_config=types.ThinkingConfig(thinking_level="LOW")))
    return resp.parsed

def fusion_search(query: str) -> list[str]:
    rw = rewrite(query)
    lists = [hybrid_search(query)]                         # always keep the original query
    lists += [hybrid_search(p) for p in rw.paraphrases + rw.sub_questions]
    lists.append(dense_search(rw.hypothetical_answer, 20)) # HyDE: embed the fake answer, dense only
    return rrf(lists, k=60, weights=[2.0] + [1.0] * (len(lists) - 1))

if __name__ == "__main__":
    print(rewrite("loyalty member: how long is the return window and when is the refund paid?").model_dump_json(indent=1))
    evaluate("hybrid", hybrid_search)
    evaluate("RAG-Fusion (MQ+HyDE+decomp)", fusion_search)
```

**Run.**
```bash
python lab7_query_transform.py
```

**Expected output (illustrative).**
```
{
 "paraphrases": ["return period for Trailhead loyalty members", "refund processing time after a return", "extended return window loyalty programme"],
 "hypothetical_answer": "Trailhead loyalty members can return items within 60 days. Refunds reach the original payment method 5-7 business days after the return is scanned.",
 "sub_questions": ["How long is the return window for loyalty members?", "How long does a refund take after a return?"]
}
hybrid                 R@1=0.667  R@3=0.867  R@5=0.933  MRR@10=0.770  nDCG@5=0.800 | miss@5: []
RAG-Fusion (MQ+HyDE+decomp) R@1=0.667  R@3=0.933  R@5=0.967  MRR@10=0.780  nDCG@5=0.830 | miss@5: []
```
Teach the honest pattern: the multi-part q11 gains (both gold chunks enter the top 3). Single-fact queries gain little, while latency and cost grow by one LLM call plus 5–7 retrievals.

**Walk-through.**
- `response_mime_type="application/json", response_schema=Rewrites`: the schema needs the JSON MIME type (types.py docstring). Passing a Pydantic class makes `resp.parsed` a `Rewrites` instance.
- `thinking_config=types.ThinkingConfig(thinking_level="LOW")`: query rewriting is a latency-critical, easy task. Keep thinking low. (`ThinkingLevel` is a case-insensitive enum, so the string works.)
- `@lru_cache`: cache rewrites by query string. In production use a shared cache (Redis) keyed on the normalised query. Repeated FAQ-style questions are common in support traffic.
- `lists = [hybrid_search(query)]` with `weights=[2.0] + ...`: always keep the **original** query and give it more weight. The SPLADE-v3 expansion study (arXiv 2609.37911) found gains in "every setting that assigns at least 30% of the mixture weight to the original query".
- `dense_search(rw.hypothetical_answer, 20)`: HyDE goes to the **dense** side only. A hallucinated answer full of invented terms pollutes BM25.

**Common errors.**
1. `ValueError: No API key was provided. Please pass a valid API key. Learn how to create an API key at https://ai.google.dev/gemini-api/docs/api-key.` (exact, `_api_client.py` line ~1049). Fix: export `GEMINI_API_KEY`.
2. `resp.parsed` is `None`. The model output did not validate (often truncated by a too-small `max_output_tokens`, or a safety block). Fix: check `resp.candidates[0].finish_reason`, log `resp.text`, and fall back to the original query only. Never let a failed rewrite fail the search.
3. HTTP 404 `models/gemini-x is not found for API version v1beta`. Model IDs change often (the models page lists `gemini-2.0-flash` as shut down). Fix: read the ID from config, not code; check https://ai.google.dev/gemini-api/docs/models. Exact error wording **[UNVERIFIED]**.
4. The rewriter "fixes" error codes (`E-4012` → `E4012` or "error 4012"). Fix: the prompt line "Keep error codes exactly as written", plus a post-check that every `CODE.findall(query)` still appears in each rewrite.

**Best practice.** Gate query transformation with a router. Use it for multi-part, vague or very short queries. Skip it for queries that contain an exact identifier. Two 2026 results back this: Medrano et al. (arXiv 2603.02153, older file 02 §6) saw fusion gains "mostly disappear after re-ranking and context truncation"; SAFE-QE (arXiv 2610.13810, 9 Oct 2026) counted **57.5 unsupported (hallucinated) expansion terms per query for HyDE** and 27.8 for Query2doc versus 4.3 for their filtered method, and reported that on a strong learned sparse retriever "every expansion method regresses".

**Variation.** Move the work to index time with **HyPE** (Hypothetical Prompt Embeddings, arXiv 2607.29402, 31 Jul 2026): for each chunk, generate 3–5 questions it answers, embed the questions, and point them at the chunk. Retrieval becomes question-to-question matching with zero query-time LLM latency. The paper reports up to +42 points context precision and +45 points claim recall on six datasets. Reuse `Rewrites`-style structured output with a "questions this chunk answers" schema, then index with Lab 3.

---

## Lab 8. Anthropic-style Contextual Retrieval with Claude Haiku 5.5 and prompt caching

> **VERIFIED against anthropic 2.3.0 wheel (no temperature param; API version 2026-10-21) + claude-api reference (Haiku 5.5 $0.10/$0.50, 512-token cache min) source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** For each chunk, ask Claude for a 1–2 sentence context ("This chunk is from Northwind's Warranty Policy for tents and backpacks; it explains when the tent warranty period starts"). Prepend it to the chunk, rebuild **both** BM25 and dense indexes, and measure. Target: q06 (c07 "The window starts on the purchase date" never says "tent" or "warranty").

**Prerequisites.**
```bash
pip install "anthropic==2.3.0" "sentence-transformers==6.2.0" "bm25s==0.3.15" "PyStemmer==3.1.0"
export ANTHROPIC_API_KEY=...      # or `ant auth login`; the SDK also reads ANTHROPIC_AUTH_TOKEN
```

**Sources checked.**
- Official cookbook: "Enhancing RAG with Contextual Retrieval", `anthropics/claude-cookbooks`, `capabilities/contextual-embeddings/guide.ipynb` (https://github.com/anthropics/claude-cookbooks/blob/main/capabilities/contextual-embeddings/guide.ipynb). The two prompts below are **verbatim** from its `DOCUMENT_CONTEXT_PROMPT` / `CHUNK_CONTEXT_PROMPT` cell. The cookbook calls `client.messages.create(model="claude-haiku-4-5", max_tokens=1024, temperature=0.0, ...)` with `cache_control: {"type": "ephemeral"}` on the document block.
- anthropic-sdk-python main (`_version.py` 2.3.0), `resources/messages/messages.py`: `create(..., model, cache_control=omit, ..., output_config=omit, ..., thinking=omit, ...)` (lines ~127–139); the file contains **no** `temperature` parameter (grep count 0). CHANGELOG: 2.0.0 (2026-10-21) "add support for new API version 2026-10-21".
- Claude API reference (bundled `claude-api` skill, cached 2026-10-06): `claude-haiku-5-5` costs $0.10 / $0.50 per MTok (prompts ≤100K tokens); minimum cacheable prefix 512 tokens on Haiku 5.5 versus 4,096 on Haiku 4.5; on API version 2026-10-21 "a Messages request that sends `temperature`, `top_p` or `top_k` returns a 400 error on every model"; Haiku 5.5 runs adaptive thinking by default with effort default `medium`.

**Code: `lab8_contextual.py`**
```python
# lab8_contextual.py -- Contextual Retrieval: LLM-written chunk context -> contextual BM25 + contextual embeddings
import json, os
import anthropic
import bm25s, Stemmer
from sentence_transformers import SentenceTransformer
from kb import CHUNKS, IDS, doc_text
from evalkit import evaluate
from lab2_bm25 import normalise
from lab3_hybrid import rrf, BGE_QUERY

client = anthropic.Anthropic()
DOCUMENT_CONTEXT_PROMPT = "\n<document>\n{doc_content}\n</document>\n"
CHUNK_CONTEXT_PROMPT = """
Here is the chunk we want to situate within the whole document
<chunk>
{chunk_content}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.
Answer only with the succinct context and nothing else.
"""

def situate(doc: str, chunk: str) -> str:
    resp = client.messages.create(
        model="claude-haiku-5-5", max_tokens=300,
        output_config={"effort": "low"},                  # no temperature: 400 on API 2026-10-21
        messages=[{"role": "user", "content": [
            {"type": "text", "text": DOCUMENT_CONTEXT_PROMPT.format(doc_content=doc),
             "cache_control": {"type": "ephemeral"}},     # same doc for every chunk -> cache it
            {"type": "text", "text": CHUNK_CONTEXT_PROMPT.format(chunk_content=chunk)}]}])
    u = resp.usage
    print(f"  cache_write={u.cache_creation_input_tokens} cache_read={u.cache_read_input_tokens} in={u.input_tokens}")
    return next(b.text for b in resp.content if b.type == "text").strip()

CACHE = "contexts.json"
ctx = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
for cid, did, text in CHUNKS:                              # document order keeps the cache warm
    if cid not in ctx:
        ctx[cid] = situate(doc_text(did), text)
json.dump(ctx, open(CACHE, "w"), indent=1)
ctext = [f"{ctx[cid]}\n{text}" for cid, _, text in CHUNKS]  # context + original chunk

stem = Stemmer.Stemmer("english")
bm25 = bm25s.BM25(); bm25.index(bm25s.tokenize([normalise(t) for t in ctext], stemmer=stem, show_progress=False), show_progress=False)
model = SentenceTransformer("BAAI/bge-small-en-v1.5")
emb = model.encode_document(ctext, normalize_embeddings=True)

def contextual_hybrid(q: str, depth: int = 18) -> list[str]:
    d, s = bm25.retrieve(bm25s.tokenize(normalise(q), stemmer=stem, show_progress=False), corpus=IDS, k=depth, show_progress=False)
    lex = [x for x, y in zip(d[0], s[0]) if y > 0]
    sims = model.similarity(model.encode_query(q, prompt=BGE_QUERY, normalize_embeddings=True), emb)[0]
    dense = [IDS[i] for i in sims.argsort(descending=True)[:depth].tolist()]
    return rrf([lex, dense], k=60)

if __name__ == "__main__":
    print("c07 context:", ctx["c07"])
    evaluate("contextual hybrid", contextual_hybrid)
```

**Run.**
```bash
python lab8_contextual.py          # first run calls Claude 18 times and writes contexts.json
python lab3_hybrid.py              # baseline, for the side-by-side slide
```

**Expected output (illustrative).**
```
  cache_write=0 cache_read=0 in=268
  cache_write=0 cache_read=0 in=262
  ... (18 lines)
c07 context: From Northwind's Warranty Policy for tents and backpacks; explains that the tent warranty period starts on the purchase date and requires proof of purchase.
contextual hybrid      R@1=0.733  R@3=0.933  R@5=1.000  MRR@10=0.830  nDCG@5=0.860 | miss@5: []
```
Note `cache_write=0`: the toy documents are ~150–250 tokens, below Haiku 5.5's **512-token** minimum, so nothing is cached and **no error is returned**. With real policy PDFs (5–50K tokens) you should see `cache_write` > 0 on the first chunk of each document and `cache_read` > 0 on the rest.

**Walk-through.**
- `"cache_control": {"type": "ephemeral"}` on the **document** block, and the varying chunk block **after** it: caching is a prefix match. The document is identical for all chunks of one document, so chunks 2..n read it from cache. Processing chunks in document order keeps the 5-minute cache warm.
- `output_config={"effort": "low"}` and no `temperature`: the cookbook's `temperature=0.0` does not exist in SDK 2.x (`messages.py` has no `temperature` parameter), and the 2026-10-21 API rejects sampling parameters with a 400. Effort is the remaining control.
- `next(b.text for b in resp.content if b.type == "text")`: Haiku 5.5 thinks by default, so `resp.content[0]` can be a `thinking` block (with empty text when display is omitted). The cookbook's `response.content[0].text` breaks here.
- `ctext = f"{ctx[cid]}\n{text}"`: the **same** augmented text goes to BM25 and to the embedder ("Contextual BM25" + "Contextual Embeddings"). Keep the original `text` for display and citations.
- `contexts.json`: contextualisation is an **ingest-time** cost. Persist it and recompute only for changed chunks.

**Common errors.**
1. `TypeError: Messages.create() got an unexpected keyword argument 'temperature'` when you paste the cookbook cell into SDK 2.x. The `temperature` parameter is absent from `messages.py`; the exact message is standard Python wording **[UNVERIFIED by running]**. Fix: delete `temperature=0.0`; use `output_config={"effort": "low"}`.
2. `anthropic.AuthenticationError` / `TypeError: "Could not resolve authentication method. Expected one of api_key, auth_token, or credentials to be set. Or for the `Authorization` header to be explicitly omitted"` (exact string in `_client.py` line 424). Fix: `export ANTHROPIC_API_KEY=...` or run `ant auth login`.
3. `AttributeError: 'ThinkingBlock' object has no attribute 'text'` from `resp.content[0].text`. Fix: select the first block with `type == "text"` (code above).
4. Cache never hits on real documents: `cache_read_input_tokens` stays 0. Causes: (a) the document prefix is under the model minimum (512 on Haiku 5.5; **4,096 on `claude-haiku-4-5`**, the cookbook's model); (b) something before the breakpoint changes per call (a timestamp, the chunk text placed *before* the document); (c) more than 5 minutes between chunks of the same document. Fix: put the document first and unchanged, process chunks of a document back-to-back, or set `"ttl": "1h"`.

**Best practice.** Contextualise **once at ingest**, with the cheapest capable model and caching, and store the context next to the chunk with a hash of the source document. Re-run only when that hash changes. "RAG Deserves an Index" (arXiv 2608.20845, Aug 2026) makes the same argument as a systems principle ("do the expensive work once, at write time"). It found that the only baseline that matched their compiled-claims index was "a contextualized-chunk pipeline with hybrid retrieval and reranking", at about 21× the query-path tokens.

**Variation.** Add a **placebo** run to prove the gain is semantic: prepend a context written for a *different* chunk (e.g. shift `ctx` by one). The Oct 2026 ablation "Does Document Structure Help Dense Retrieval?" (arXiv 2610.10170) notes that "any text prepended to a chunk perturbs its embedding" and controls for it with shuffled heading paths; it found real structure beats the placebo (+0.010 / +0.016 cov-nDCG@10) and that structure-aligned chunks with real heading paths beat "contextualized fixed windows". Cheaper alternative to test: prepend the deterministic heading path (`"Warranty Policy: Tents and Backpacks > "`) with no LLM at all.

---

## Lab 9. Parent-child ("small-to-big") retrieval with LangChain `ParentDocumentRetriever`

> **VERIFIED against langchain-classic 1.0.8 + langchain-core 1.7.0 + langchain-text-splitters 1.1.3 wheels source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Embed small child chunks for precise matching, but return the whole parent document (policy page) to the LLM. Measure at the **parent** level: did we return the right policy document?

**Prerequisites.**
```bash
pip install "langchain-classic==1.0.8" "langchain-core==1.7.0" "langchain-text-splitters==1.1.3" "sentence-transformers==6.2.0"
# do NOT add langchain-huggingface[full]: it pins sentence-transformers<6 (see §0)
```

**Source checked.** langchain master `libs/langchain/pyproject.toml` = langchain-classic 1.0.8. `langchain_classic/retrievers/parent_document_retriever.py`: `class ParentDocumentRetriever(MultiVectorRetriever)` with fields `child_splitter: TextSplitter`, `parent_splitter: TextSplitter | None = None`, `child_metadata_fields: Sequence[str] | None = None` (lines 11–71); `add_documents(documents, ids=None, add_to_docstore=True)` (line 116). `langchain_classic/retrievers/multi_vector.py`: `id_key: str = "doc_id"`, `search_kwargs: dict = Field(default_factory=dict)` (line 57); retrieval runs `vectorstore.similarity_search(query, **self.search_kwargs)` then de-duplicates parent IDs "to maintain the order" and calls `docstore.mget(ids)` (lines ~100–113). `langchain_core/vectorstores/in_memory.py`: `InMemoryVectorStore(embedding)` (line 161). `langchain_core/stores.py`: `InMemoryStore` (line 244). Adapted from the class docstring example in `parent_document_retriever.py`.

**Code: `lab9_parent_child.py`**
```python
# lab9_parent_child.py -- embed children, return parents (policy documents)
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.stores import InMemoryStore
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from kb import DOCS, QUERIES, DOC_OF, doc_text

class STEmbeddings(Embeddings):                            # 6-line adapter, avoids langchain-huggingface pin
    def __init__(self, name: str):
        self.m = SentenceTransformer(name)
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.m.encode_document(texts, normalize_embeddings=True).tolist()
    def embed_query(self, text: str) -> list[float]:
        return self.m.encode_query(text, prompt="Represent this sentence for searching relevant passages: ",
                                   normalize_embeddings=True).tolist()

retriever = ParentDocumentRetriever(
    vectorstore=InMemoryVectorStore(STEmbeddings("BAAI/bge-small-en-v1.5")),
    docstore=InMemoryStore(),
    child_splitter=RecursiveCharacterTextSplitter(chunk_size=160, chunk_overlap=0, separators=["\n", ". "]),
    search_kwargs={"k": 12},                                # children fetched BEFORE de-dup to parents
)
parents = [Document(page_content=doc_text(d), metadata={"doc_id_biz": d}) for d in DOCS]
retriever.add_documents(parents, ids=list(DOCS))            # parent ids = D1..D4

hits = mrr_sum = 0.0
for qid, (text, gold_chunks) in QUERIES.items():
    gold_docs = {DOC_OF[c] for c in gold_chunks}
    got = [d.metadata["doc_id_biz"] for d in retriever.invoke(text)]
    hits += bool(set(got[:1]) & gold_docs)
    mrr_sum += next((1 / r for r, d in enumerate(got, 1) if d in gold_docs), 0.0)
    print(f"{qid} gold={sorted(gold_docs)} got={got}")
n = len(QUERIES)
print(f"parent-level Hit@1={hits / n:.3f}  MRR={mrr_sum / n:.3f}  (avg parents returned: see list lengths)")
```

**Run.**
```bash
python lab9_parent_child.py
```

**Expected output (illustrative).**
```
q01 gold=['D1'] got=['D1', 'D2', 'D4']
q02 gold=['D3'] got=['D3', 'D1']
...
q11 gold=['D1'] got=['D1', 'D3']
parent-level Hit@1=0.933  MRR=0.960  (avg parents returned: see list lengths)
```
Point for the slide: the LLM now gets the full policy page, so q11 gets c04 **and** c02 together, and c07 arrives with its "Warranty Policy: Tents" title. The cost: each returned parent is 5–10× more tokens than a child chunk.

**Walk-through.**
- `class STEmbeddings(Embeddings)`: LangChain only needs `embed_documents` and `embed_query`. Writing the adapter keeps sentence-transformers 6.2 and the BGE query prefix under your control.
- `child_splitter=RecursiveCharacterTextSplitter(chunk_size=160, ...)`: children are what gets embedded. With no `parent_splitter`, the parent is the whole input `Document`.
- `search_kwargs={"k": 12}`: `similarity_search` returns k **children**, and the retriever then de-duplicates them to parents (`multi_vector.py`). With the default (empty `search_kwargs`, so the vector store's default k, 4 for `similarity_search`; verified: `InMemoryVectorStore.similarity_search(self, query, k=4, ...)`, langchain-core 1.7.0 `vectorstores/in_memory.py` L404), four children from the same policy collapse into **one** parent.
- `retriever.add_documents(parents, ids=list(DOCS))`: giving explicit parent IDs lets you re-index a changed document without duplicates (`add_to_docstore=False` is only allowed when `ids` are given).
- `d.metadata["doc_id_biz"]`: the retriever stores the parent ID under `id_key="doc_id"` in the **child** metadata; the returned parent keeps its own metadata, so store your business ID there.

**Common errors.**
1. `ValueError: Got uneven list of documents and ids. If `ids` is provided, should be same length as `documents`.` (exact, `parent_document_retriever.py` lines 92–95). Fix: one ID per parent.
2. `ModuleNotFoundError: No module named 'langchain.retrievers'`. LangChain 1.x moved this class to `langchain_classic`. Fix: `from langchain_classic.retrievers import ParentDocumentRetriever` and install `langchain-classic`.
3. Only one parent comes back for every query. `search_kwargs` is empty, so a small child k is used and the children all belong to the same parent. Fix: set `search_kwargs={"k": 3 * desired_parents}`.
4. `ERROR: Cannot install langchain-huggingface ... and sentence-transformers==6.2.0 because these package versions have conflicting dependencies.` (pip `ResolutionImpossible` wording) when you add `langchain-huggingface[full]`. Fix: the adapter above, or pin `sentence-transformers<6`.

**Best practice.** Make the parent a **structural** unit (a policy section with its heading), not an arbitrary 2,000-character window, and cap the parent size so 3–5 parents fit the context budget. Evidence: the 2026 ablation (arXiv 2610.10170) found "naive two-stage hierarchical retrieval hurts (−0.033 / −0.015)", traced to first-stage section recall, while structure-aligned chunks with real headings help. A production ingestion system (arXiv 2610.07091, Oct 2026) reports a "deterministic structure-aware parent-child chunker" reaching hit@1 68.6%, hit@10 92.8% and MRR 0.77 over 25,050 generated questions.

**Variation.** Add `parent_splitter=RecursiveCharacterTextSplitter(chunk_size=600)` to make "parents" medium-sized sections instead of whole documents, then compare tokens returned per query versus parent-level Hit@1. Also try returning *child + neighbours* (sentence-window retrieval) as a middle ground.

---

## 10. New evidence from arXiv, 2026-07-23 .. 2026-10-23 (for the "insights" slides)

All IDs, dates and quotes were read from the arXiv API abstracts on 2026-10-23. Only abstracts were read, not full papers.

| arXiv ID (date) | Title (short) | Practical takeaway | Lab |
|---|---|---|---|
| 2610.30612 (22 Oct) | The Fusion Tax: When Hybrid Retrieval Hurts (Chauhan, Agarwal) | Best fusion still ranks relevant docs below dense-only on 8–21% of queries; RRF only beats dense-only when the two retrievers are balanced; a cross-encoder recovers part of the loss "only where it is itself reliable". Key the fusion decision to the measured sparse/dense balance of your corpus. | L3, L4 |
| 2610.24341 (17 Oct) | Optimal Fusion Weights Form Intervals, Not Points (Thomson Reuters; Ma et al.) | 74/128 dynamic fusion methods significantly beat standard RRF; per-query optimal weight is an interval. Code: github.com/thomsonreuters/query-based-rrf. | L3 variation |
| 2609.15143 (14 Sep) | Top-K Is Not a Budget for Hybrid Retrieval (Zhang) | Fixed per-retriever depth does not transfer; budgeted exact RRF keeps 95–97.7% nDCG@20 with 66–99.5% fewer accesses. | L3 depth |
| 2610.26260 (19 Oct) | Preference Is Not Position (NevIR) | A ranker can improve pairwise preference while cutting MRR (0.5764 → 0.3055). BGE cross-encoder: 69.77% strict preference, MRR 0.7404. Evaluate MRR and cost together. | L5 |
| 2609.27213 (23 Sep) | BoundaryMORPH: Budgeted Reranking | When CE budget < context size k, spend CE calls on the top-k boundary; +5.4 nCG@100. | L5 best practice |
| 2610.01324 (1 Oct) | Biomedical reranking over clinical notes | Hybrid + weighted RRF + MedCPT CE: Hit@10 46.6 → 60.6%, MRR 0.2371 → 0.3252, answer correctness only 44.8 → 48.6%. | L6 |
| 2610.14816 (10 Oct) | Unlocking Qwen3-0.6B for MS MARCO (Han) | Sub-1B rerankers reach strong results through data curation, hard negatives and model soups, not architecture tricks. Argument for fine-tuning a small in-house reranker. | L5 variation |
| 2610.13810 (9 Oct) | SAFE-QE: hallucinated terms in LLM query expansion | HyDE injects 57.5 unsupported terms/query, Query2doc 27.8, SAFE-QE 4.3, at equal nDCG@10; on a strong learned sparse retriever "every expansion method regresses". | L7 |
| 2609.37911 (29 Sep) | Generated Query Expansion Still Helps SPLADE-v3 | All 12 comparisons improve nDCG@10 (best +4.8/+8.9/+9.5%), provided the original query keeps ≥30% weight; shuffled-text controls also help, so the vocabulary carries the gain. | L7 weights |
| 2609.14875 (14 Sep) | EviQE: Evidence Selection for LLM Query Expansion | Pool documents from several reformulators, select evidence by LLM relevance, expand once; more rounds "can reduce effectiveness". | L7 |
| 2607.29402 (31 Jul) | HyPE: Hypothetical Prompt Embeddings | Index-time hypothetical *questions* per chunk; up to +42 pts context precision, +45 pts claim recall; no query-time latency. | L7 variation |
| 2608.20845 (21 Aug) | RAG Deserves an Index (ingest-time compilation) | Compiled claims: 85.2% correct from ~2.2k reader tokens vs 72.5% from 16.3k for the best chunk setup; only contextualised-chunk hybrid+rerank keeps pace, at ~21× query tokens. | L8 |
| 2610.10170 (7 Oct) | Does Document Structure Help Dense Retrieval? (placebo-controlled) | Real headings beat a shuffled-heading placebo and beat LLM-contextualised fixed windows; naive two-stage hierarchical retrieval hurts. Effects small (dz 0.06–0.11) but consistent. | L8, L9 |
| 2610.07091 (5 Oct) | Smart Content Ingestion for GenAI Workloads | Production extractor + structure-aware parent-child chunker: hit@1 68.6%, hit@10 92.8%, MRR 0.77 over 25,050 generated questions; principle "never mutate what you measure". | L9 |
| 2610.31019 (22 Oct) | Chunk Recomputation under Real Document Revisions | Fixed-size chunking re-embeds 57–68% of a revised article; recursive 38–56%; retrieval quality differs <2 pts. Report update cost next to quality. | L8 ingest |
| 2610.26951 (18 Oct) | The Bottleneck Is Retrieval, Not Reading | Similarity retrieval finds *any* relevant chunk far more reliably than *all* required chunks for multi-fact queries; chunking loses document meta-information. Measure recall@k (all gold), not only hit@k. | L1, L9 |
| 2610.31606 (22 Oct) | How Ground Truth Shapes Retrieval Scores | Evidence-span labelling; curation raised accepted chunk targets 36 → 51 with unchanged rankings; best: 384-token chunks, 20% overlap, hybrid + CE (R@3 = MRR@3 = 0.94 on 18 queries). | L1 |
| 2610.30755 (22 Oct) | Naive RAG Is Stronger Than We Thought | Dense retrieval + reranking over raw history ranked first in 6 of 7 memory benchmark settings vs complex agentic memory. Build the strong simple baseline first. | all |

---

## 11. Gotchas worth a slide each (all verified above)

1. **bm25s eats one-letter prefixes.** Default token pattern `\b\w\w+\b` turns "E-4012" into "4012". Normalise codes on both sides. (L2)
2. **Qdrant's RRF k defaults to 2, the paper's to 60.** Pin it. (L4)
3. **Prefetch limit < main limit + offset gives an empty result in Qdrant.** (L4)
4. **`CrossEncoder.rank` returns positions and, for ms-marco MiniLM, raw logits.** Map IDs back; do not threshold at 0.5. (L5)
5. **Cohere/Voyage return `index` into your candidate list**, and scores are not calibrated probabilities. (L6)
6. **Cookbook drift:** the Contextual Retrieval cookbook's `temperature=0.0` breaks on anthropic SDK 2.x / API 2026-10-21; its `claude-haiku-4-5` needs ≥4,096-token documents to cache; `content[0].text` breaks when thinking blocks come first. (L8)
7. **Caching below the minimum fails silently** (`cache_creation_input_tokens == 0`, no error). (L8)
8. **`langchain-huggingface[full]` pins sentence-transformers < 6.** (§0, L9)
9. **ParentDocumentRetriever de-duplicates after the child search**: small child k → one parent. (L9)
10. **Hybrid, reranking and query rewriting can each make individual queries worse** while the mean improves. Always print the per-query "got worse" list. (L1, §10)

## 12. Suggested slide sequence for this chapter (one lab per 2–3 slides)

1. "Measure first" — the 25-line harness + the floor run (L1).
2. "BM25 in 15 lines" + the E-4012 bug (L2).
3. "Hybrid = two lists + 1/(k+rank)" — the comparison table BM25 / dense / hybrid (L3).
4. "Do it in the DB" — Qdrant one-call hybrid, k=2 vs k=60 (L4).
5. "Rerank 20, keep 5" — before/after MRR + latency (L5).
6. "Rerank as a service" — Cohere v5 spans as context compression (L6).
7. "Rewrite the question — sometimes" — RAG-Fusion + the SAFE-QE hallucinated-terms number (L7).
8. "Give every chunk its missing context" — c07 before/after, cache counters (L8).
9. "Search small, read big" — parent-child, tokens vs hit@1 (L9).
10. "What 2026 papers say" — Fusion Tax, HyPE, ingest-time compilation (§10).
