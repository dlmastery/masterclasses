# Hands-on labs: build a RAG index end to end (parse, chunk, embed, index, filter)

Research date: **2026-10-23**. Audience: a hands-on lecture deck. The user asked for code, not theory.
These labs extend `research-rag/01-foundations.md`, which covers the theory for Docling, the Chroma chunking study, and HNSW/IVF. That theory is not repeated here.

**How this was verified.** pip/PyPI downloads are blocked on the research machine, so **none of the code below was executed**. Every import path, class, parameter and default was checked against the library **source on GitHub** (the main branch was sparse-cloned on 2026-10-23) and against the PyPI JSON metadata. Citations give `file:line` from those clones. "Expected output" blocks are **illustrative**: realistic in shape, but the numbers are not measured.

---

## 0. Version pins (PyPI JSON, checked 2026-10-23)

| Package | Latest | Uploaded | Requires-Python | Notes |
|---|---|---|---|---|
| `docling` | **2.142.1** | 2026-10-23 | >=3.10,<4 | Now a **meta-package**: `docling` = `docling-slim[standard]==2.142.1` (PyPI requires_dist). |
| `docling-core` | 2.104.0 | 2026-10-22 | >=3.10 | Holds `HybridChunker` and tokenizers. |
| `unstructured` | **0.27.34** | 2026-10-22 | >=3.11,**<3.14** | Main branch is `0.27.35-dev`. |
| `langchain-text-splitters` | **1.1.3** | 2026-10-02 | >=3.10 | |
| `langchain-core` | 1.7.0 | 2026-10-22 | >=3.10 | |
| `google-genai` | **2.33.0** | 2026-10-23 | >=3.10 | `google/genai/version.py` |
| `sentence-transformers` | **6.2.0** | 2026-10-21 | >=3.10 | Needs `transformers>=5.0.0,<6`. |
| `transformers` | 5.20.2 | 2026-10-19 | | |
| `torch` | 2.14.1 | 2026-09-30 | | |
| `faiss-cpu` | **1.15.1** | 2026-09-16 | >=3.10 | Wheels for cp310 to cp314. |
| `pgvector` (Python) | **0.5.1** | 2026-10-09 | >=3.10 | Postgres extension: **0.8.7** (2026-10-01, `CHANGELOG.md`). 0.9.0 is unreleased and drops PG 13/14. |
| `psycopg` / `psycopg-binary` | 3.3.6 | 2026-09-18 | >=3.10 | |
| `chromadb` | **1.5.9** | 2026-05-05 | >=3.9 | No PyPI release since May 2026. APIs below were checked at tag `1.5.9` and on main. |
| `numpy` | 2.5.4 | 2026-10-10 | **>=3.12** | |
| `tiktoken` | 0.14.0 | 2026-08-17 | | |

**Use Python 3.12 or 3.13 for every lab.** `unstructured` refuses 3.14, and numpy 2.5 refuses 3.11 or older, though pip silently falls back to an older numpy there.

```bash
python3.12 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install "docling==2.142.1" "unstructured[chunking-tokens]==0.27.34" \
  "langchain-text-splitters==1.1.3" "google-genai==2.33.0" "sentence-transformers==6.2.0" \
  "faiss-cpu==1.15.1" "pgvector==0.5.1" "psycopg[binary]==3.3.6" "chromadb==1.5.9" pandas
```

Running scenario for all labs: **"Northwind Mutual"**, a fictional insurer. It has a claims-policy PDF, an HR handbook, a refund/cancellation policy, and a support-ticket knowledge base.

---

## Lab 1: Parse a claims-policy PDF with Docling and chunk it for your embedding model

> **VERIFIED against docling-slim 2.142.1 + docling-core 2.104.0 wheels source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Convert a PDF into a `DoclingDocument` with tables and reading order. Then create token-bounded chunks that keep headings and page provenance, so every answer can cite "page 7, §3.2 Exclusions".

**Prerequisites.**
- `pip install "docling==2.142.1"`. The `standard` extra already includes PDF parsing, local layout/table models, RapidOCR, and `docling-core[chunking]` (docling `pyproject.toml` lines 288-291 and 316-317).
- No env vars. The first run downloads layout and TableFormer models from Hugging Face. On air-gapped machines, pre-fetch them with `docling-tools models download` (`docling/cli/models.py:126`, registered under `docling-tools models` in `docling/cli/tools.py:34`).

Adapted from the official examples `docs/examples/hybrid_chunking.ipynb` ("Hybrid chunking") and `docs/examples/custom_convert.py` (https://github.com/docling-project/docling/tree/main/docs/examples).

```python
# lab1_docling_claims.py
import json
import sys
from pathlib import Path

from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer

# Your claims policy PDF; falls back to the public Docling tech report so the lab always runs.
SOURCE = sys.argv[1] if len(sys.argv) > 1 else "https://arxiv.org/pdf/2408.09869"
EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"   # chunk with the SAME tokenizer you embed with
MAX_TOKENS = 512

opts = PdfPipelineOptions()
opts.do_ocr = False                      # born-digital PDF: skip OCR (default is True)
opts.do_table_structure = True           # default True; shown for clarity
opts.table_structure_options.mode = TableFormerMode.ACCURATE
converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
)

result = converter.convert(SOURCE, max_num_pages=60)
doc = result.document
print(f"status={result.status.value} pages={len(doc.pages)} tables={len(doc.tables)}")
out = Path("out"); out.mkdir(exist_ok=True)
(out / "claims_policy.md").write_text(doc.export_to_markdown(), encoding="utf-8")

tokenizer = HuggingFaceTokenizer(
    tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID), max_tokens=MAX_TOKENS
)
chunker = HybridChunker(tokenizer=tokenizer, merge_peers=True, repeat_table_header=True)

n = 0
with open(out / "claims_chunks.jsonl", "w", encoding="utf-8") as f:
    for i, chunk in enumerate(chunker.chunk(dl_doc=doc)):
        embed_text = chunker.contextualize(chunk=chunk)        # headings + text
        pages = sorted({p.page_no for item in chunk.meta.doc_items for p in item.prov})
        rec = {
            "chunk_id": f"{doc.origin.filename}#{i}",
            "text": embed_text,
            "raw_text": chunk.text,
            "headings": chunk.meta.headings or [],
            "pages": pages,
            "labels": sorted({item.label.value for item in chunk.meta.doc_items}),
            "tokens": tokenizer.count_tokens(embed_text),
        }
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n += 1
print(f"wrote {n} chunks -> out/claims_chunks.jsonl")
```

**Run.**
```bash
python lab1_docling_claims.py ./data/northwind_claims_policy.pdf
head -c 600 out/claims_chunks.jsonl
```

**Expected output (illustrative).**
```
status=success pages=9 tables=5
wrote 41 chunks -> out/claims_chunks.jsonl
{"chunk_id": "2408.09869v5.pdf#0", "text": "Docling Technical Report\nVersion 1.0 ...", "headings": ["Docling Technical Report"], "pages": [1], "labels": ["page_header", "text"], "tokens": 187}
```

**Key lines.**
1. `PdfPipelineOptions()` with `do_ocr = False`. The default is `do_ocr=True` (`docling/datamodel/pipeline_options.py:2127-2136`). On born-digital PDFs OCR wastes minutes and can add noise. Keep it on for scans.
2. `table_structure_options.mode = TableFormerMode.ACCURATE`. The enum is at `pipeline_options.py:125-139`. ACCURATE is already the default (`:175`). FAST trades table quality for speed.
3. `converter.convert(SOURCE, max_num_pages=60)`. The signature also has `raises_on_error=True`, `max_file_size` and `page_range` (`docling/document_converter.py:632-639`). Set limits so a 2,000-page upload cannot block a worker.
4. `HuggingFaceTokenizer(tokenizer=AutoTokenizer.from_pretrained(...), max_tokens=512)`. Without it, `HybridChunker` falls back to the `sentence-transformers/all-MiniLM-L6-v2` tokenizer (`docling_core/transforms/chunker/tokenizer/huggingface.py:91-93`). Chunk limits are then measured in the wrong tokens for your embedder.
5. `HybridChunker(..., merge_peers=True, repeat_table_header=True)`. Both are defaults (`hybrid_chunker.py:73-76`). `repeat_table_header` re-emits the table header row when a table is split. Without it, a rate table chunk with no column names is useless.
6. `chunker.contextualize(chunk=chunk)`. This returns the heading path plus the text. **Embed this, not `chunk.text`.** Store `raw_text` separately for display. `chunk.meta.doc_items[*].prov[*].page_no` gives page provenance (`DocItem.prov: list[ProvenanceItem]`, `docling_core/types/doc/items/node.py:119-124`; `ProvenanceItem.page_no`, `types/doc/common/reference.py:205-213`).

**Common errors.**
- `docling.exceptions.ConversionError: Conversion failed because the provided file has no recognizable format or it wasn't in the list of allowed formats.` (`document_converter.py:793-796`). The cause is a wrong extension or MIME type, or an `allowed_formats=[...]` list that excludes the type. Fix: check the file, or add the `InputFormat`.
- `ConversionError: Conversion failed for: <file> with status: failure. Errors: ...` (`:785-788`). Encrypted PDFs land here, and the original `PdfiumError` is chained in `__cause__` (`:781-784`). Fix: decrypt upstream, or call `convert(..., raises_on_error=False)` and route `result.status != SUCCESS` to a dead-letter queue.
- A scanned PDF converts but every chunk is nearly empty. Cause: `do_ocr=False` on an image-only PDF. Fix: set `do_ocr=True`. The default `OcrAutoOptions` picks an installed engine (`pipeline_options.py:315-322`). Alternatively, send hard pages to the VLM pipeline.
- `DeprecationWarning: Deprecated initialization parameter types for HybridChunker.` (`hybrid_chunker.py:94-99`). Cause: passing `tokenizer="model-name"` or `max_tokens=` directly (legacy style). Fix: wrap it in `HuggingFaceTokenizer(...)` as shown above.

**Best practice.** Write `DoclingDocument` JSON (`doc.save_as_json(...)`) to object storage **before** chunking. Re-chunking is then cheap, and re-parsing (the expensive GPU/CPU step) never repeats.

**Variation.** Swap in `TableStructureV2Options` (TableFormer V2, `pipeline_options.py:178`) and compare chunks for a premium-rate table. Or run `docling --pipeline vlm --vlm-model granite_docling <pdf>` on the 5% of pages where the layout parser fails.

---

## Lab 2: Partition and chunk an HR handbook with Unstructured `chunk_by_title`

> **VERIFIED against unstructured 0.27.34 wheel source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Turn an HTML HR handbook into typed elements (Title, NarrativeText, ListItem, Table). Then group them into section-aligned chunks, using both a character budget and a **token budget**.

**Prerequisites.** `pip install "unstructured[chunking-tokens]==0.27.34"`. The `chunking-tokens` extra pulls `tiktoken` (`pyproject.toml` optional-dependencies). HTML needs no other extras. Python 3.11 to 3.13 only. No env vars.

Adapted from the Unstructured chunking docs (https://docs.unstructured.io/open-source/core-functionality/chunking) and `unstructured/chunking/title.py`.

```python
# lab2_unstructured_hr.py
from collections import Counter

from unstructured.chunking.title import chunk_by_title
from unstructured.partition.html import partition_html

HR_HTML = """
<h1>Northwind Mutual Employee Handbook</h1>
<h2>1. Leave policies</h2>
<p>Full-time employees accrue 1.67 days of paid time off (PTO) per month, up to 20 days per year.</p>
<p>Unused PTO up to 5 days carries over to the next calendar year.</p>
<h3>1.1 Parental leave</h3>
<p>Birth and adoptive parents receive 16 weeks of fully paid parental leave.</p>
<ul><li>Leave can start up to 2 weeks before the expected date.</li>
<li>Leave must be taken within 12 months of the birth or placement.</li></ul>
<h2>2. Expenses</h2>
<table><tr><th>Category</th><th>Daily limit (USD)</th></tr>
<tr><td>Meals</td><td>75</td></tr><tr><td>Hotel</td><td>250</td></tr></table>
<p>Receipts are required for any single expense above 25 USD.</p>
"""

elements = partition_html(text=HR_HTML)
print("element types:", dict(Counter(e.category for e in elements)))

# Character budget: hard max 800, soft max 600, merge tiny sections below 150 chars.
by_chars = chunk_by_title(
    elements, max_characters=800, new_after_n_chars=600, combine_text_under_n_chars=150
)
# Token budget (tiktoken encoding name) - max_characters and max_tokens are mutually exclusive.
by_tokens = chunk_by_title(elements, max_tokens=120, tokenizer="cl100k_base")

for name, chunks in [("chars", by_chars), ("tokens", by_tokens)]:
    print(f"\n== {name}: {len(chunks)} chunks")
    for c in chunks:
        origs = c.metadata.orig_elements or []
        print(f"[{c.category}] {len(c.text):>4} chars from {len(origs)} elements | {c.text[:70]!r}")
        if c.metadata.text_as_html:
            print("   table html kept:", c.metadata.text_as_html[:60], "...")
```

**Run.**
```bash
python lab2_unstructured_hr.py
```

**Expected output (illustrative).**
```
element types: {'Title': 4, 'NarrativeText': 5, 'ListItem': 2, 'Table': 1}

== chars: 4 chunks
[CompositeElement]  141 chars from 3 elements | 'Northwind Mutual Employee Handbook\n\n1. Leave policies\n\nFull-time empl'
[CompositeElement]  213 chars from 4 elements | '1.1 Parental leave\n\nBirth and adoptive parents receive 16 weeks of fu'
[Table]              40 chars from 1 elements | 'Category Daily limit (USD) Meals 75 Hotel 250'
   table html kept: <table><tr><th>Category</th><th>Daily limit (USD)</th></tr> ...
[CompositeElement]   72 chars from 2 elements | '2. Expenses\n\nReceipts are required for any single expense above 25 US'
```

**Key lines.**
1. `partition_html(text=HR_HTML)`. `partition_html` takes `filename`, `file`, `text` or `url` (`unstructured/partition/html/partition.py:30-36`). For mixed folders use `unstructured.partition.auto.partition(filename=...)`.
2. `chunk_by_title(..., max_characters=800, new_after_n_chars=600, combine_text_under_n_chars=150)`. This is the signature at `chunking/title.py:23-39`. Defaults: `max_characters=500` (`CHUNK_MAX_CHARS_DEFAULT`, `chunking/base.py:36`). `new_after_n_chars` defaults to `max_characters`, and `combine_text_under_n_chars` also defaults to `max_characters` (`title.py:242`). `multipage_sections=True` (`base.py:45`).
3. `max_tokens=120, tokenizer="cl100k_base"`. Token-budget chunking resolves the name through `tiktoken.encoding_for_model` / `get_encoding` (`base.py:66-84`).
4. `c.metadata.orig_elements`. With the default `include_orig_elements=True` (`base.py:252-253`), each chunk keeps its source elements. This is lineage for citations, but it inflates memory (see Gotcha).
5. Tables are **isolated** into their own chunk by default (`isolate_table`, see `base.py:281,434`), and `metadata.text_as_html` keeps the structure. Index the HTML or a Markdown rendering for table chunks, not only the flattened text.

**Common errors.**
- `ValueError: 'max_tokens' and 'max_characters' are mutually exclusive; specify one or the other, not both` (`base.py:389-392`).
- `ValueError: 'tokenizer' is required when using 'max_tokens'` (`base.py:399-400`). Since 0.27.x, an empty string `""` also raises this. Before that, it silently counted characters (CHANGELOG line 321).
- `ValueError: 'combine_text_under_n_chars' argument must not exceed `max_characters` value, got 600 > 500` (`title.py:268-272`). Cause: setting `combine_text_under_n_chars=600` while leaving `max_characters` at the default of 500. Fix: raise `max_characters` too.
- `ValueError: 'overlap' argument must be less than `max_characters`, got 500 >= 500` (`base.py:449-453`).

**Best practice.** Set `new_after_n_chars` to about 75% of `max_characters`, as above. Sections then close at a natural boundary instead of being cut mid-sentence at the hard max.

**Variation.** Use `iter_chunks_by_title()` (CHANGELOG line 317) to stream chunks from a 5,000-page handbook without holding every chunk in memory. Pass `include_orig_elements=False` when images are present, because `image_base64` payloads get copied into every chunk.

---

## Lab 3: Header-aware, token-sized chunking of a refund policy with `langchain-text-splitters`

> **VERIFIED against langchain-text-splitters 1.1.3 wheel source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Compare a **naive** fixed-size split with a **structure-first** split (Markdown headers, then token-sized recursive splitting) on a refund/cancellation policy. Count how often the naive splitter cuts a policy rule away from its heading.

**Prerequisites.** `pip install "langchain-text-splitters==1.1.3" "transformers==5.20.2"`. No env vars.

Adapted from the LangChain splitter docs (https://docs.langchain.com/oss/python/integrations/splitters) and the source `libs/text-splitters/langchain_text_splitters/{base,character,markdown}.py`.

```python
# lab3_splitters_refund.py
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

REFUND_MD = """# Northwind Mutual Refund and Cancellation Policy
## 1. Free-look period
You may cancel any new policy within 30 days of the start date for a full refund of premiums paid.
No claim must have been filed during the free-look period.
## 2. Cancellation after 30 days
### 2.1 Annual policies
Refunds are pro-rata minus a 25 USD administration fee.
### 2.2 Monthly policies
Cancellation takes effect at the end of the current billing month. No partial refunds are issued.
## 3. Claims-related exceptions
If a claim was paid in the current policy year, the premium for that year is non-refundable.
"""
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-Embedding-0.6B")
ntok = lambda s: len(tok.tokenize(s))

# A) naive: fixed character windows over the whole file
naive = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=0).split_text(REFUND_MD)

# B) structure first: split on headers, keep header text, then size by TOKENS
headers = [("#", "h1"), ("##", "h2"), ("###", "h3")]
sections = MarkdownHeaderTextSplitter(headers_to_split_on=headers, strip_headers=False).split_text(REFUND_MD)
sizer = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
    tok, chunk_size=64, chunk_overlap=8, add_start_index=True
)
structured = sizer.split_documents(sections)

orphans = sum(1 for c in naive if not c.lstrip().startswith("#"))
print(f"naive: {len(naive)} chunks, {orphans} start without a heading")
for c in naive:
    print("  N |", c.replace("\n", " ")[:90])
print(f"structured: {len(structured)} chunks")
for d in structured:
    path = " > ".join(d.metadata[k] for k in ("h1", "h2", "h3") if k in d.metadata)
    print(f"  S | {ntok(d.page_content):>3} tok | start={d.metadata['start_index']:>3} | {path}")
```

**Run.**
```bash
python lab3_splitters_refund.py
```

**Expected output (illustrative).**
```
naive: 5 chunks, 3 start without a heading
  N | # Northwind Mutual Refund and Cancellation Policy ## 1. Free-look period You may cancel
  N | No claim must have been filed during the free-look period. ## 2. Cancellation after 30
  ...
structured: 5 chunks
  S |  45 tok | start=  0 | Northwind Mutual Refund and Cancellation Policy > 1. Free-look period
  S |  22 tok | start=  0 | Northwind Mutual Refund and Cancellation Policy > 2. Cancellation after 30 days > 2.1 Annual policies
  S |  31 tok | start=  0 | ... > 2.2 Monthly policies
  S |  30 tok | start=  0 | ... > 3. Claims-related exceptions
```

**Key lines.**
1. `RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=0)`. The base defaults are `chunk_size=4000`, `chunk_overlap=200`, `length_function=len` (`base.py:62-70`), and the default separators are `["\n\n", "\n", " ", ""]` (`character.py:107`). **`chunk_size` counts characters unless you change `length_function`.**
2. `MarkdownHeaderTextSplitter(headers_to_split_on=..., strip_headers=False)`. The signature is `(headers_to_split_on, return_each_line=False, strip_headers=True)` (`markdown.py:26-31`). Its `split_text` returns `list[Document]` with header metadata (`markdown.py:134`), not `list[str]`. Keep the header text in the chunk (`strip_headers=False`) so the embedding sees it.
3. `from_huggingface_tokenizer(tok, chunk_size=64, ...)`. A classmethod on `TextSplitter` (`base.py:212-233`). It sets `length_function = len(tokenizer.tokenize(text))`, so `chunk_size` now means **tokens of your embedding model**.
4. `add_start_index=True`. This writes `metadata["start_index"]` (`base.py:139-143`). Gotcha: after `split_documents(sections)`, the offset is relative to the **section**, not the original file. Store the section anchor too if you need character highlights in the UI.
5. `split_documents(sections)`. It copies each section's metadata (`h1`/`h2`/`h3`) onto every sub-chunk (`base.py:146-...`). That metadata becomes your filter and citation fields.

**Common errors.**
- `ValueError: Got a larger chunk overlap (300) than chunk size (256), should be smaller.` (`base.py:94-99`).
- `ValueError: Could not import transformers python package. Please install it with `pip install transformers`.` (`base.py:45-55`). This is raised by `from_huggingface_tokenizer`.
- Warning `Created a chunk of size 1203, which is longer than the specified 1000` (logged at `base.py:183-186`). Cause: one paragraph has no separator to split on (a long table row or minified text). Fix: add separators such as `"|"` or `". "`, or pre-clean the text.
- `ValueError: Tokenizer received was not an instance of PreTrainedTokenizerBase` (`base.py:226-228`). Cause: passing a `tokenizers.Tokenizer` or a model name string. Fix: pass `AutoTokenizer.from_pretrained(...)`.

**Best practice.** Measure chunk size in the **embedding model's tokens**, and keep the chunk well under its window. A Qwen3-Embedding chunk can be 32k tokens, but retrieval precision drops long before that. Start at 256 to 512 tokens, then tune on your own eval set.

**Variation.** Use `RecursiveCharacterTextSplitter.from_language(Language.PYTHON, ...)` (`character.py:165`) for a code-search corpus. Or use `SentenceTransformersTokenTextSplitter(model_name=..., tokens_per_chunk=...)` (`sentence_transformers.py:16-20`, default `chunk_overlap=50`).

**Insight from new arXiv work (2026-07-23 .. 10-23).**
- *Does Document Structure Help Dense Retrieval?* (arXiv **2610.10170**, 7 Oct 2026). A placebo-controlled ablation on 200 Wikipedia articles and 1,585 QASPER papers. Structure-aligned chunks with **real heading paths** beat contextualized fixed windows (+0.022 and +0.012 cov-nDCG@10) and beat a **shuffled-heading placebo** (+0.010 and +0.016). So the gain comes from content, not from extra tokens. Naive two-stage hierarchical retrieval *hurt* (-0.033 and -0.015). The effects are small but significant.
- *StrucChunk* (arXiv **2610.26313**, 19 Oct 2026). On legal corpora, clause-boundary-aware chunking plus BM25+BGE-M3 RRF raised Recall@5 from 0.557 to 0.804 on Indian CrPC. Chunking explains 88% of that gain. Boundary precision was 100% vs **7.7% for recursive splitting**.

---

## Lab 4: Embed a support-ticket KB with Gemini (`gemini-embedding-001` and `gemini-embedding-2`)

> **VERIFIED against google-genai 2.33.0 wheel source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Embed resolved support tickets for a **ticket-triage** bot. Use asymmetric document/query embeddings, Matryoshka truncation to 768 dims, correct normalization, batching and retry.

**Prerequisites.** `pip install "google-genai==2.33.0" numpy`. Env: `export GEMINI_API_KEY=...`. The client reads `GOOGLE_API_KEY` or `GEMINI_API_KEY`, and if both are set it warns and uses `GOOGLE_API_KEY` (`google/genai/_api_client.py:162-172`).

Adapted from the Gemini API guide "Embeddings" (https://ai.google.dev/gemini-api/docs/embeddings): samples 4 (similarity), 5 (dimensionality), 6 (normalize) and 9 (separate embeddings).

```python
# lab4_gemini_tickets.py
import time

import numpy as np
from google import genai
from google.genai import errors, types

client = genai.Client()                       # GEMINI_API_KEY / GOOGLE_API_KEY
MODEL, DIM, BATCH = "gemini-embedding-001", 768, 100

TICKETS = [
    ("TKT-1042", "Login loop after Okta SSO", "Clear the stale session cookie; re-sync the SAML clock skew."),
    ("TKT-1077", "Claim PDF upload fails", "Files over 20 MB are rejected; compress or split the PDF."),
    ("TKT-1103", "Refund not received", "Refunds post 5-7 business days after approval to the original card."),
    ("TKT-1150", "Duplicate premium charge", "Void the second authorization in Billing > Transactions."),
]

def embed(texts: list[str], task_type: str) -> np.ndarray:
    vecs = []
    for i in range(0, len(texts), BATCH):
        cfg = types.EmbedContentConfig(task_type=task_type, output_dimensionality=DIM)
        for attempt in range(5):
            try:
                resp = client.models.embed_content(model=MODEL, contents=texts[i:i + BATCH], config=cfg)
                break
            except errors.APIError as err:
                if err.code in (429, 500, 503) and attempt < 4:
                    time.sleep(2 ** attempt)
                    continue
                raise
        vecs.extend(emb.values for emb in resp.embeddings)
    v = np.asarray(vecs, dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)   # REQUIRED for 001 below 3072 dims

docs = [f"{title}\n{body}" for _, title, body in TICKETS]
D = embed(docs, "RETRIEVAL_DOCUMENT")
q = embed(["customer says money from cancelled policy never arrived"], "RETRIEVAL_QUERY")
scores = (D @ q.T).ravel()
for idx in np.argsort(-scores):
    print(f"{scores[idx]:.3f}  {TICKETS[idx][0]}  {TICKETS[idx][1]}")
np.save("tickets_768.npy", D)
print("shape:", D.shape, "norm[0]:", round(float(np.linalg.norm(D[0])), 4))
```

**Run.**
```bash
export GEMINI_API_KEY="..."      # PowerShell: $env:GEMINI_API_KEY="..."
python lab4_gemini_tickets.py
```

**Expected output (illustrative).**
```
0.742  TKT-1103  Refund not received
0.611  TKT-1150  Duplicate premium charge
0.503  TKT-1077  Claim PDF upload fails
0.455  TKT-1042  Login loop after Okta SSO
shape: (4, 768) norm[0]: 1.0
```

**Key lines.**
1. `client.models.embed_content(model=..., contents=..., config=...)`. All arguments are keyword-only (`google/genai/models.py:6063-6069`).
2. `types.EmbedContentConfig(task_type=..., output_dimensionality=DIM)`. Fields: `task_type`, `title`, `output_dimensionality`, plus Vertex-only `mime_type`, `auto_truncate` and `document_ocr` (`types.py:9128-9172`). `title` applies to the whole request, so put per-ticket titles into the text, as done here.
3. `"RETRIEVAL_DOCUMENT"` for the index and `"RETRIEVAL_QUERY"` for the question. These are asymmetric task types, `gemini-embedding-001` only (Embeddings guide).
4. `v / np.linalg.norm(...)`. The guide says the 3072-dim output is normalized but truncated `gemini-embedding-001` outputs are **not**: "divide each vector by its norm yourself". Without this step, dot product is not cosine, and the FAISS/pgvector inner-product indexes in Labs 6-7 rank incorrectly.
5. `errors.APIError` with `.code`. `APIError` declares `code: int` (`errors.py:56-58`), and `ClientError` subclasses it (`:308`). Retry only on 429/5xx.

**Same thing with `gemini-embedding-2`** (multimodal, 8,192-token input). This model has **no `task_type`**. Use text prefixes instead, and wrap **each** input in its own `Content`. Passing a plain list of strings returns **one aggregated embedding** (Embeddings guide). The SDK also converts contents with `t.t_contents` only for this model on the Gemini API (`models.py:6105-6107`).
```python
def prep_doc(title, body): return f"title: {title} | text: {body}"
def prep_query(q):        return f"task: search result | query: {q}"
resp = client.models.embed_content(
    model="gemini-embedding-2",
    contents=[types.Content(parts=[types.Part.from_text(text=prep_doc(t, b))]) for _, t, b in TICKETS],
    config=types.EmbedContentConfig(output_dimensionality=768),   # 2 auto-normalizes truncated dims
)
assert len(resp.embeddings) == len(TICKETS)
```

**Common errors.**
- `ValueError: No API key was provided. Please pass a valid API key. Learn how to create an API key at https://ai.google.dev/gemini-api/docs/api-key.` (`_api_client.py:1048-1053`). Fix: export `GEMINI_API_KEY`, or use `genai.Client(vertexai=True, project=..., location=...)`.
- You get `len(resp.embeddings) == 1` for 100 inputs on `gemini-embedding-2`. This is the aggregation behaviour described above. Fix: wrap each input in `types.Content`.
- `google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED ...`. The exact message text depends on the quota tier [UNVERIFIED wording]. Fix: back off as shown, or use `client.batches.create_embeddings(...)` (experimental; it warns that it "is experimental and may change", `batches.py:2318-2349`). The guide states batch costs 50% of the default price.
- Mixing models: vectors from `gemini-embedding-001` and `gemini-embedding-2` are **not compatible**, so re-embed everything (research-rag/05). Store `embedding_model` and `dim` on every row (Labs 7-9).

**Best practice.** Pin `MODEL` and `DIM` in config and write them into index metadata. Refuse to query an index whose recorded model differs from the query embedder.

**Variation.** `BATCH = 100` is a conservative choice. The official guide does **not** state a per-request item cap for text [UNVERIFIED limit]. Measure throughput at 50, 100 and 250 items on your quota.

---

## Lab 5: Local embeddings with sentence-transformers v6 (Qwen3-Embedding-0.6B, MRL truncation, int8)

> **VERIFIED against sentence-transformers 6.2.0 wheel source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Embed the claims chunks from Lab 1 **on-prem** (no data leaves the VPC). Use the model's own query/document prompts, truncate 1024 dims to 256 (Matryoshka), and test int8 quantization.

**Prerequisites.** `pip install "sentence-transformers==6.2.0" "torch==2.14.1"`. No env vars. `Qwen/Qwen3-Embedding-0.6B` is **not gated** (HF API `gated: False`). Its `config_sentence_transformers.json` defines `prompts.query = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:"`, `prompts.document = ""`, and `similarity_fn_name: cosine`. Hidden size is 1024. Note: `google/embeddinggemma-300m` is **gated** (`gated: manual`) and needs an HF token plus license acceptance.

Adapted from the sentence-transformers docs "Semantic Search" and the example `examples/sentence_transformer/applications/embedding-quantization/semantic_search_recommended.py` (https://github.com/huggingface/sentence-transformers).

```python
# lab5_st_claims.py
import json

import numpy as np
from sentence_transformers import SentenceTransformer, quantize_embeddings

chunks = [json.loads(line) for line in open("out/claims_chunks.jsonl", encoding="utf-8")]
texts = [c["text"] for c in chunks]

model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", device="cpu", truncate_dim=256)
print("prompts:", list(model.prompts), "| dim:", model.get_embedding_dimension(),
      "| max_seq_length:", model.max_seq_length)
model.max_seq_length = 1024          # cap memory; chunks are <=512 tokens anyway

doc_emb = model.encode_document(texts, batch_size=16, normalize_embeddings=True,
                                show_progress_bar=True)
queries = ["Is water damage from a burst pipe covered?", "How long do I have to report a claim?"]
q_emb = model.encode_query(queries, normalize_embeddings=True)

scores = model.similarity(q_emb, doc_emb)            # cosine (from model config)
for qi, q in enumerate(queries):
    top = np.argsort(-scores[qi].numpy())[:3]
    print(f"\nQ: {q}")
    for j in top:
        print(f"  {scores[qi, j]:.3f} p{chunks[j]['pages']} {chunks[j]['headings'][-1:]} ")

int8_docs = quantize_embeddings(doc_emb, precision="int8", calibration_embeddings=doc_emb)
print("\nfloat32 bytes:", doc_emb.nbytes, "| int8 bytes:", int8_docs.nbytes)
np.save("out/claims_qwen256.npy", doc_emb.astype(np.float32))
```

**Run.**
```bash
python lab1_docling_claims.py ./data/northwind_claims_policy.pdf   # produces the chunks
python lab5_st_claims.py
```

**Expected output (illustrative).**
```
prompts: ['query', 'document'] | dim: 256 | max_seq_length: 32768
Batches: 100%|██████████| 3/3
Q: Is water damage from a burst pipe covered?
  0.712 p[4] ['3.2 Exclusions']
  0.655 p[3] ['3.1 Covered perils']
...
float32 bytes: 41984 | int8 bytes: 10496
```

**Key lines.**
1. `SentenceTransformer(..., truncate_dim=256)`. This is a constructor argument (`sentence_transformer/model.py:175-179`). `get_embedding_dimension()` reports the truncated size (`:1151-1175`).
2. `encode_document(...)`. If no prompt is given, it picks the first prompt named `"document"`, `"passage"` or `"corpus"` (`model.py:518-536`). `encode_query` does the same with `"query"`. **Using plain `encode()` for queries silently drops the instruction prompt** and costs recall.
3. `normalize_embeddings=True`. In `encode`, truncation (`model.py:~967`) happens *before* normalization (`~992`), so truncated vectors come out unit-length.
4. `model.similarity(q_emb, doc_emb)`. It uses `similarity_fn_name`, which defaults to cosine if unset (`model.py:1030-1037`).
5. `quantize_embeddings(..., precision="int8", calibration_embeddings=...)`. Signature at `util/quantization.py:469-474`, exported at the package top level (`__init__.py:43`). It cuts storage 4x. Calibrate on a representative sample, not on the query set.

**Common errors.**
- `FutureWarning: The `get_sentence_embedding_dimension` method has been renamed to `get_embedding_dimension`.` (`model.py:1177-1182`). This is v6 behaviour, and old tutorials still use the old name.
- Old import paths such as `from sentence_transformers.quantization import ...` and `from sentence_transformers.models import Dense` now go through a deprecation shim (`util/deprecated_import.py:18,74-79`). Fix: import from the top level or `sentence_transformers.util.quantization`.
- `OSError: You are trying to access a gated repo.` when loading `google/embeddinggemma-300m` without `HF_TOKEN` [message wording from huggingface_hub, UNVERIFIED]. Fix: accept the license on the Hub and `export HF_TOKEN=...`.
- CPU out of memory on long chunks. The model's `max_seq_length` comes from its 32,768-position config. Fix: set `model.max_seq_length` as shown and keep `batch_size` small.

**Best practice.** Embed with the **same tokenizer budget you chunked with** (Lab 1 used this model's tokenizer at 512). Then no chunk is silently truncated at embed time.

**Variation.** Try `precision="binary"` plus rescoring with float32 (the recommended pattern in the quantization example). Compare top-10 overlap against float32.

**Insight from new arXiv work.**
- *Geometric Structure Predicts Per-Example Neighborhood Loss Under PCA Truncation* (arXiv **2610.17742**, 13 Oct 2026). Average retrieval quality under truncation hides **large per-example variation**. Some queries lose most of their neighbors, so test truncation on your hard queries, not only on the mean.
- *MRVQ* (arXiv **2610.03651**, 2 Oct 2026). One residual-quantized index serves every (prefix-dimension, bit-rate) pair at 17.8x to 22.0x less RAM than separate QINCo2 indices. Per-rate QINCo2 is still 0.026 to 0.107 nDCG@10 better on FiQA, so this is a memory operating point, not a quality win.

---

## Lab 6: FAISS index lab: Flat vs HNSW vs IVF, recall/latency sweep, ID mapping, metadata filter

> **VERIFIED against faiss-cpu 1.15.1 wheel (Python wrappers) + faiss v1.15.1 headers on GitHub source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Measure recall@10 and latency against exact search for HNSW (`efSearch` sweep) and IVF (`nprobe` sweep) on 100k unit vectors. Then do a **tenant-filtered** search with stable external IDs, and persist the index.

**Prerequisites.** `pip install "faiss-cpu==1.15.1" numpy`. No env vars.

Adapted from the FAISS wiki "Faiss indexes" and "Getting started" (https://github.com/facebookresearch/faiss/wiki) and `tutorial/python/`.

```python
# lab6_faiss_bench.py
import time

import faiss
import numpy as np

rng = np.random.default_rng(7)
N, D, NQ, K = 100_000, 256, 500, 10
centers = rng.standard_normal((1_000, D)).astype(np.float32)          # clustered, like real embeddings
xb = centers[rng.integers(0, 1_000, N)] + 0.3 * rng.standard_normal((N, D)).astype(np.float32)
xq = xb[rng.choice(N, NQ, replace=False)] + 0.1 * rng.standard_normal((NQ, D)).astype(np.float32)
faiss.normalize_L2(xb); faiss.normalize_L2(xq)                         # cosine == inner product

flat = faiss.IndexFlatIP(D); flat.add(xb)
_, gt = flat.search(xq, K)
recall = lambda I: np.mean([len(set(I[i]) & set(gt[i])) / K for i in range(NQ)])

def bench(index, params, label):
    t = time.perf_counter(); _, I = index.search(xq, K, params=params)
    print(f"{label:<22} recall@10={recall(I):.3f}  {1e3 * (time.perf_counter() - t) / NQ:.3f} ms/q")

hnsw = faiss.IndexHNSWFlat(D, 32, faiss.METRIC_INNER_PRODUCT)          # M=32
hnsw.hnsw.efConstruction = 80
t = time.perf_counter(); hnsw.add(xb); print(f"HNSW build {time.perf_counter() - t:.1f}s")
for ef in (16, 64, 128, 256):
    bench(hnsw, faiss.SearchParametersHNSW(efSearch=ef), f"HNSW efSearch={ef}")

nlist = 1024                                                           # ~4*sqrt(N)
ivf = faiss.IndexIVFFlat(faiss.IndexFlatIP(D), D, nlist, faiss.METRIC_INNER_PRODUCT)
ivf.train(xb[rng.choice(N, 60_000, replace=False)]); ivf.add(xb)
for p in (1, 8, 32, 64):
    bench(ivf, faiss.SearchParametersIVF(nprobe=p), f"IVF nprobe={p}")

# Stable external IDs + tenant filter (e.g. only Northwind's 'claims' tenant = 3)
ids = np.arange(10_000_000, 10_000_000 + N, dtype=np.int64)            # your chunk primary keys
tenant = rng.integers(0, 10, N)
idx = faiss.IndexIDMap(faiss.IndexHNSWFlat(D, 32, faiss.METRIC_INNER_PRODUCT))
idx.add_with_ids(xb, ids)
sel = faiss.IDSelectorBatch(ids[tenant == 3])
Dist, I = idx.search(xq[:1], K, params=faiss.SearchParametersHNSW(sel=sel, efSearch=256))
print("filtered ids:", I[0][:5], "all tenant 3:", bool(np.all(tenant[I[0] - 10_000_000] == 3)))
faiss.write_index(idx, "claims_hnsw.faiss"); print("saved", faiss.read_index("claims_hnsw.faiss").ntotal)
```

**Run.**
```bash
python lab6_faiss_bench.py
```

**Expected output (illustrative; the shape of the trade-off is what matters).**
```
HNSW build 38.2s
HNSW efSearch=16       recall@10=0.781  0.041 ms/q
HNSW efSearch=64       recall@10=0.952  0.098 ms/q
HNSW efSearch=128      recall@10=0.984  0.171 ms/q
HNSW efSearch=256      recall@10=0.996  0.320 ms/q
IVF nprobe=1           recall@10=0.412  0.020 ms/q
IVF nprobe=8           recall@10=0.861  0.105 ms/q
IVF nprobe=32          recall@10=0.973  0.390 ms/q
IVF nprobe=64          recall@10=0.991  0.760 ms/q
filtered ids: [10041233 10088120 10002317 10063390 10017741] all tenant 3: True
saved 100000
```

**Key lines.**
1. `faiss.normalize_L2(...)` plus `METRIC_INNER_PRODUCT`. FAISS has no "cosine" metric, so normalize first (`extra_wrappers.py:147`). The default metric of `IndexHNSWFlat(int d, int M, MetricType metric = METRIC_L2)` is **L2** (`faiss/IndexHNSW.h:175`).
2. `hnsw.hnsw.efConstruction = 80`. The defaults are `efConstruction = 40` and `efSearch = 16` (`faiss/impl/HNSW.h:141,144`). efSearch=16 is low for RAG. Expect to raise it to 64-256.
3. `faiss.SearchParametersHNSW(efSearch=ef)` / `SearchParametersIVF(nprobe=p)`. These are per-query parameters, set through kwargs in the Python wrapper (`class_wrappers.py:1472-1485`). The search signature is `search(x, k, *, params=None, ...)` (`class_wrappers.py:426-440`). Per-query params are thread-safe. Mutating `index.hnsw.efSearch` globally is not. The `nprobe` default is **1** (`faiss/IndexIVF.h:97`).
4. `ivf.train(...)` on 60k points. FAISS warns below `min_points_per_centroid = 39` per list (`Clustering.h:44`) and subsamples above `max_points_per_centroid = 256` (`:46`). For nlist=1024, that means about 40k to 262k training points.
5. `IndexIDMap(...)` plus `add_with_ids`. HNSW alone cannot take your IDs. `IndexIDMap` translates an `IDSelector` from external IDs to internal ones (`faiss/IndexIDMap.cpp:179-194`). The Python `IDSelectorBatch(array)` constructor casts to int64 (`class_wrappers.py:1511-1523`).
6. `faiss.write_index` / `read_index`. Persist after build, because the HNSW build is the slow part (seconds per 100k vectors on CPU).

**Common errors.**
- `RuntimeError: Error in virtual void faiss::Index::add_with_ids(...): add_with_ids not implemented for this type of index` (message from `faiss/Index.cpp:56`). Fix: wrap the index in `faiss.IndexIDMap` (or `IndexIDMap2` if you need `reconstruct`).
- `RuntimeError: Error in ... IndexIVF::search ...: IVF index is not trained` (`faiss/IndexIVF.cpp:442`). Adding before training fails the `is_trained` assertion (`:366`). Fix: call `train()` first.
- Stderr `WARNING clustering 5000 points to 1024 centroids: please provide at least 39936 training points` (`faiss/Clustering.cpp:179-186`). Recall will be poor. Fix: use more training data or a smaller `nlist`.
- `AssertionError` in `replacement_add` (`assert d == self.d`, `class_wrappers.py:309`). Cause: a dimension mismatch, for example 768-dim Gemini vectors added to a 256-dim index. FAISS also silently casts float64 to float32 (`ascontiguousarray(x, dtype=float32)`), which hides an upstream dtype bug.

**Best practice.** Always build an exact `IndexFlatIP` on a 1-5k query sample and report **recall@k vs exact** next to latency. Tune `efSearch`/`nprobe` to a recall target (for example 0.95) and write the chosen value into config.

**Variation.** Replace the strings: `faiss.index_factory(D, "IVF1024,PQ32", faiss.METRIC_INNER_PRODUCT)` (IVF-PQ, 32 bytes per vector) or `"HNSW32,SQ8"`. Compare memory using the bytes-per-vector formulas in research-rag/01 §6.

**Insight from new arXiv work.**
- *A Power Law in Logarithm's Clothing* (arXiv **2609.02143**, 2 Sep 2026). At fixed recall, graph-search cost grows as **N^c (0<c<1)** while N is small relative to intrinsic dimensionality. It only later slows toward poly-log. Re-tune `efSearch` when the corpus grows 10x, and don't assume "log N".
- *Closed Forms and Synthetic Twins* (arXiv **2609.00364**, 31 Aug 2026). ANN recall can be predicted from label-free embedding statistics, within 0.03 of measured recall on a million-document corpus. One encoder recovered only 14% of its exact top-10 through a raw FDE index. Lesson: benchmark the **encoder + index pair**, not the encoder alone.
- *MERIT* (arXiv **2607.29173**, 31 Jul 2026). In-place HNSW/Vamana deletion at about the cost of one insert, 3.02x to 18.87x faster than prior methods. This matters for "right to be forgotten" deletes in production RAG.

---

## Lab 7: pgvector on Postgres 18: claims chunks with metadata, HNSW params, filtered search that still returns k rows

> **VERIFIED against pgvector-python 0.5.1 wheel + pgvector v0.8.7 README/CHANGELOG source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Store claim-policy chunks with tenant, product and effective-date columns. Bulk-load with binary COPY, build HNSW with explicit `m`/`ef_construction`, and run a **filtered** top-k that does not come back short. Then check index use with `EXPLAIN`.

**Prerequisites.**
```bash
docker run -d --name pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=rag -p 5432:5432 pgvector/pgvector:pg18-trixie
pip install "pgvector==0.5.1" "psycopg[binary]==3.3.6" numpy
export PG_DSN="postgresql://postgres:postgres@localhost:5432/rag"
```
The image tag comes from the pgvector README "Docker" section (`docker pull pgvector/pgvector:pg18-trixie`).

Adapted from pgvector-python `README.md` (Psycopg 3) and `examples/loading/example.py` (https://github.com/pgvector/pgvector-python), plus pgvector `README.md` (HNSW, Filtering, Iterative Index Scans).

```python
# lab7_pgvector_claims.py
import datetime as dt
import os

import numpy as np
import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector

conn = psycopg.connect(os.environ["PG_DSN"], autocommit=True)
conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
register_vector(conn)                                   # after CREATE EXTENSION
conn.execute("DROP TABLE IF EXISTS claim_chunks")
conn.execute("""CREATE TABLE claim_chunks (
    id bigserial PRIMARY KEY, tenant_id int NOT NULL, product text NOT NULL,
    effective_date date NOT NULL, content text NOT NULL,
    embedding_model text NOT NULL, embedding vector(256) NOT NULL)""")

rng = np.random.default_rng(1)
N, products = 50_000, ["auto", "home", "travel", "pet"]
emb = rng.standard_normal((N, 256)).astype(np.float32)
emb /= np.linalg.norm(emb, axis=1, keepdims=True)
with conn.cursor() as cur, cur.copy(
    "COPY claim_chunks (tenant_id, product, effective_date, content, embedding_model, embedding)"
    " FROM STDIN WITH (FORMAT BINARY)") as copy:
    copy.set_types(["int4", "text", "date", "text", "text", "vector"])
    for i in range(N):
        copy.write_row([i % 20, products[i % 4], dt.date(2024 + i % 3, 1, 1),
                        f"chunk {i} of policy wording", "qwen3-emb-0.6b@256", Vector(emb[i])])

conn.execute("SET maintenance_work_mem = '1GB'")          # build after load
conn.execute("CREATE INDEX claim_hnsw ON claim_chunks USING hnsw (embedding vector_cosine_ops)"
             " WITH (m = 16, ef_construction = 64)")
conn.execute("CREATE INDEX ON claim_chunks (tenant_id, product)")
conn.execute("ANALYZE claim_chunks")

SQL = """SELECT id, product, effective_date, embedding <=> %s AS dist FROM claim_chunks
         WHERE tenant_id = %s AND product = %s AND effective_date >= %s
         ORDER BY embedding <=> %s LIMIT 10"""
q = Vector(emb[123])
with conn.transaction():
    conn.execute("SET LOCAL hnsw.ef_search = 100")
    conn.execute("SET LOCAL hnsw.iterative_scan = relaxed_order")   # pgvector >= 0.8.0
    rows = conn.execute(SQL, (q, 3, "home", dt.date(2025, 1, 1), q)).fetchall()
    plan = conn.execute("EXPLAIN " + SQL, (q, 3, "home", dt.date(2025, 1, 1), q)).fetchall()
print(len(rows), "rows; first:", rows[0][:3])
print("\n".join(r[0] for r in plan[:4]))
```

**Run.**
```bash
python lab7_pgvector_claims.py
```

**Expected output (illustrative).** The filter matches about 1/20 × 1/4 × 2/3 ≈ 0.8% of rows, so without iterative scan HNSW would return around 0 rows.
```
10 rows; first: (123, 'home', datetime.date(2026, 1, 1))
Limit  (cost=... rows=10 width=...)
  ->  Index Scan using claim_hnsw on claim_chunks  (cost=...)
        Order By: (embedding <=> '[...]'::vector)
        Filter: ((tenant_id = 3) AND (product = 'home'::text) AND (effective_date >= '2025-01-01'::date))
```
The planner may choose the B-tree on `(tenant_id, product)` plus an exact sort instead. For selective filters, that is correct and gives exact results (pgvector README, "Filtering").

**Key lines.**
1. `register_vector(conn)`. It fetches the `vector`, `bit`, `halfvec` and `sparsevec` type OIDs (`pgvector/psycopg/register.py`), so it **must run after** `CREATE EXTENSION`.
2. `cur.copy(... FORMAT BINARY)` plus `copy.set_types([..., "vector"])`. This is the fastest bulk-load path (`examples/loading/example.py`). Create indexes **after** loading.
3. `USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)`. Both values are the defaults (README "Index Options": m 16, ef_construction 64). The operator class must match the query operator: `<=>` goes with `vector_cosine_ops`, `<#>` with `vector_ip_ops`, `<->` with `vector_l2_ops`.
4. `SET LOCAL hnsw.ef_search = 100`. The default is **40** (README "Query Options"). `SET LOCAL` scopes it to the transaction, which is safe with connection pools.
5. `SET LOCAL hnsw.iterative_scan = relaxed_order`. pgvector filters **after** the index scan: "If a condition matches 10% of rows, with HNSW and the default hnsw.ef_search of 40, only 4 rows will match on average" (README "Filtering"). Iterative scans (0.8.0+) keep scanning up to `hnsw.max_scan_tuples` (default 20,000).
6. `ORDER BY embedding <=> %s LIMIT 10`. The index is used only for `ORDER BY <distance operator> ASC LIMIT n`. `ORDER BY 1 - (embedding <=> q) DESC` does **not** use the index (README "Troubleshooting").

**Common errors.**
- `ERROR: column cannot have more than 2000 dimensions for hnsw index` (`src/hnswbuild.c:707`). Cause: indexing 3072-dim `gemini-embedding-001` vectors. Fix: use `output_dimensionality=1536` or 768, or `halfvec` (up to 4,000 dims), or an expression index `USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops)` (README "Half-Precision Indexing"; limits in "HNSW": vector 2,000, halfvec 4,000, bit 64,000).
- `ERROR: expected 256 dimensions, not 768` (`src/vector.c:88`). Cause: embedder and column disagree. Fix: one table (or partition) per `embedding_model`.
- `ERROR: ef_construction must be greater than or equal to 2 * m` (`src/hnswbuild.c:712`).
- `NOTICE: hnsw graph no longer fits into maintenance_work_mem after N tuples` / `DETAIL: Building will take significantly more time.` (`hnswbuild.c:536-538`). Fix: raise `maintenance_work_mem` for the build session. Do not set it so high that the server runs out of memory.
- `psycopg.ProgrammingError: vector type not found in the database` (`pgvector/psycopg/vector.py:50`). Cause: `register_vector` was called before `CREATE EXTENSION`, or in the wrong database.

**Best practice.** For **multi-tenant** RAG, the pgvector README recommends `PARTITION BY LIST(tenant_id)` or separate tables ("Multitenancy"), because one shared ANN index lets other tenants' vectors hurt your recall. Few distinct filter values: use **partial indexes** (`... WHERE (product = 'home')`).

**Variation.** For IVFFlat: `CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)`. The README suggests `rows/1000` lists up to 1M rows and `sqrt(rows)` above that, with `SET ivfflat.probes = sqrt(lists)` (default 1). Building it on an empty table raises `NOTICE: ivfflat index created with little data` / `DETAIL: This will cause low recall.` (`src/ivfbuild.c:463-465`).

**Insight from new arXiv work.**
- *Recall-Bounded Staleness for Filtered Multi-Tenant ANN Graph Indexes* (arXiv **2610.15130**, 10 Oct 2026). Per-tenant recall loss splits into (a) **staleness** from updates not yet merged and (b) **filtered navigability**, which depends on local predicate density. Bigger merge batches made staleness loss *worse* super-linearly: terminal recall@10 fell from 99.44% to 99.01% at 20x merge size. This supports small frequent index maintenance plus tenant isolation.
- *Simple and Fast Algorithm for Graph-based Filtered ANN Search* (arXiv **2607.24173**, 27 Jul 2026), and *RaG-Tree* (arXiv **2608.01255**, R-tree + HNSW for multi-attribute **range** filters). Filtered ANN is still an active research area. Post-filtering (pgvector's default) is the simple baseline these papers improve on.

---

## Lab 8: Chroma 1.5.9: HR-policy collection with explicit HNSW config and rich metadata filters

> **VERIFIED against chromadb 1.5.9 sdist + sentence-transformers 6.2.0 source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Store the HR chunks from Lab 2 with your **own** embeddings (Qwen3 from Lab 5). Set cosine space and HNSW parameters explicitly. Query with `$and` / `$gte` / `$in`, the list-membership operator `$contains`, and a full-text `where_document` filter.

**Prerequisites.** `pip install "chromadb==1.5.9" "sentence-transformers==6.2.0"`. No env vars. Data persists in `./chroma_hr`.

Adapted from the Chroma docs "Getting Started", "Configure collections" and "Metadata filtering" (https://docs.trychroma.com) and `chromadb/api/collection_configuration.py`.

```python
# lab8_chroma_hr.py
import chromadb
from sentence_transformers import SentenceTransformer

POLICIES = [
    ("hr-001", "Parental leave: 16 weeks fully paid for birth and adoptive parents.",
     {"doc_type": "policy", "section": "1.1", "effective_year": 2026, "regions": ["US", "CA"]}),
    ("hr-002", "Parental leave (EU): 20 weeks paid; statutory pay is topped up to 100%.",
     {"doc_type": "policy", "section": "1.1", "effective_year": 2026, "regions": ["DE", "FR"]}),
    ("hr-003", "Expenses: meals 75 USD/day, hotel 250 USD/night; receipts above 25 USD.",
     {"doc_type": "policy", "section": "2", "effective_year": 2025, "regions": ["US"]}),
    ("hr-004", "FAQ: Can I split my parental leave into two blocks? Yes, with manager approval.",
     {"doc_type": "faq", "section": "1.1", "effective_year": 2024, "regions": ["US", "CA"]}),
]
model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", truncate_dim=256)

client = chromadb.PersistentClient(path="./chroma_hr")
col = client.get_or_create_collection(
    name="hr_policies",
    embedding_function=None,                        # we supply vectors ourselves
    configuration={"hnsw": {"space": "cosine", "ef_construction": 200,
                            "max_neighbors": 32, "ef_search": 100}},
    metadata={"embedding_model": "Qwen3-Embedding-0.6B@256"},
)
ids, docs, metas = zip(*POLICIES)
col.upsert(ids=list(ids), documents=list(docs), metadatas=list(metas),
           embeddings=model.encode_document(list(docs), normalize_embeddings=True))

q = model.encode_query(["How long is paid parental leave in Canada?"], normalize_embeddings=True)
res = col.query(
    query_embeddings=q, n_results=3,
    where={"$and": [{"doc_type": {"$in": ["policy", "faq"]}},
                    {"effective_year": {"$gte": 2025}},
                    {"regions": {"$contains": "CA"}}]},
    where_document={"$contains": "parental"},
    include=["documents", "metadatas", "distances"],
)
for i, d, m, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
    print(f"{dist:.3f} {i} {m['regions']} {d[:60]}")
print("count:", col.count(), "| config:", col.configuration["hnsw"])
```

**Run.**
```bash
python lab8_chroma_hr.py
python lab8_chroma_hr.py   # second run: upsert is idempotent, count stays 4
```

**Expected output (illustrative).**
```
0.214 hr-001 ['US', 'CA'] Parental leave: 16 weeks fully paid for birth and adoptive pa
count: 4 | config: {'space': 'cosine', 'ef_construction': 200, 'ef_search': 100, 'max_neighbors': 32, ...}
```
(`hr-002` is excluded by region, `hr-003` by `where_document`, and `hr-004` by `effective_year`.)

**Key lines.**
1. `configuration={"hnsw": {...}}`. The keys allowed by `CreateHNSWConfiguration` are `space`, `ef_construction`, `max_neighbors`, `ef_search`, `num_threads`, `batch_size`, `sync_threshold` and `resize_factor` (`collection_configuration.py:184-192`). Defaults: `ef_construction=100`, `max_neighbors=16`, `ef_search=100` (`:444-455`). `Space = Literal["cosine","l2","ip"]` (`api/types.py:807`).
2. `embedding_function=None`. The **space default** is `ef.default_space() if ef else "l2"` (`collection_configuration.py:448-449`). The built-in default embedding function picks `cosine` (`onnx_mini_lm_l6_v2.py:328-329`), but with `embedding_function=None` you silently get **L2** unless you set `space`, as done here.
3. `get_or_create_collection(name, schema, configuration, metadata, embedding_function, data_loader)` (`chromadb/api/__init__.py:650-660`). The configuration is applied only on **create**. Changing it on a later call does not rebuild an existing collection.
4. `col.upsert(...)`. Use it instead of `add` so re-runs are idempotent. `add` with existing IDs raises `DuplicateIDError` only for duplicates *within one batch* (`api/types.py:1034-1046`).
5. `{"regions": {"$contains": "CA"}}`. List-valued metadata (`MetadataListValue = List[str|int|float|bool]`, `base_types.py:119-121`) with the `$contains` / `$not_contains` operators (`base_types.py:140`). This is verified present at tag `1.5.9`. Logical `$and`/`$or` and `$in`/`$nin` are at `base_types.py:130,139`.

**Common errors.**
- `ValueError: Expected metadata value to be a str, int, float, bool, SparseVector, list, or None, got {...} which is a dict` (`api/types.py:1100`). Cause: nested dicts in metadata. Fix: flatten them (`"claim.type"` → `"claim_type"`).
- `ValueError: Expected where to have exactly one operator, got {...}` (`api/types.py:1194`). Cause: `where={"doc_type": "policy", "effective_year": {"$gte": 2025}}` with two keys at the top level. Fix: wrap them in `{"$and": [...]}`.
- `chromadb.errors.DuplicateIDError: Expected IDs to be unique, found duplicates of: hr-001` (`api/types.py:1034`).
- A dimension mismatch, such as adding 768-dim vectors to a collection created with 256, raises an `InvalidArgumentError` stating the expected and received dimension [exact wording UNVERIFIED; it is raised from Chroma's Rust core]. Fix: one collection per embedding model and dimension, recorded in `metadata`.

**Best practice.** Put **ACL and tenant fields in metadata on every chunk**, such as `regions`, `tenant_id` and `acl_groups`, and apply them as a `where` filter **server-side** on every query. Never filter in the LLM prompt.

**Variation.** Switch to `chromadb.HttpClient(host=..., port=8000)` (`__init__.py:262-268`) against a `chroma run` server, or to `CloudClient(...)`, without changing the query code. Try `"spann"` configuration (`search_nprobe`, `write_nprobe`, `collection_configuration.py:33-42`) for Chroma's distributed/cloud index.

---

## Lab 9: Incremental, idempotent ingestion: Docling → HybridChunker → Gemini → Chroma with content-hash IDs

> **VERIFIED against docling-core 2.104.0, google-genai 2.33.0, chromadb 1.5.9 source (verifier pass, 2026-10-23).** Imports, class/function names and parameters re-checked in the released package; code still not executed.

**Goal.** Re-ingest an **edited** claims policy without re-embedding unchanged chunks. Delete chunks that disappeared. This is the "day-2" problem that static chunking benchmarks ignore.

**Prerequisites.** Labs 1, 4 and 8 installed. `export GEMINI_API_KEY=...`.

```python
# lab9_incremental_ingest.py
import hashlib
import sys

import chromadb
import numpy as np
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from google import genai
from google.genai import types

SOURCE, MODEL, DIM = sys.argv[1], "gemini-embedding-001", 768
gclient = genai.Client()
col = chromadb.PersistentClient(path="./chroma_claims").get_or_create_collection(
    name=f"claims_{MODEL.replace('-', '_')}_{DIM}", embedding_function=None,
    configuration={"hnsw": {"space": "cosine"}}, metadata={"embedding_model": MODEL, "dim": DIM})

doc = DocumentConverter().convert(SOURCE).document
chunker = HybridChunker(tokenizer=HuggingFaceTokenizer.from_pretrained(
    model_name="sentence-transformers/all-MiniLM-L6-v2", max_tokens=400))   # [see Gotcha]
fresh = {}
for ch in chunker.chunk(dl_doc=doc):
    text = chunker.contextualize(chunk=ch)
    cid = hashlib.sha256(f"{MODEL}|{DIM}|{text}".encode()).hexdigest()[:32]  # content-addressed
    pages = sorted({p.page_no for it in ch.meta.doc_items for p in it.prov})
    fresh[cid] = (text, {"source": doc.origin.filename, "first_page": pages[0] if pages else -1,
                         "heading": (ch.meta.headings or [""])[-1]})

existing = set(col.get(where={"source": doc.origin.filename}, include=[])["ids"])
to_add = [cid for cid in fresh if cid not in existing]
to_delete = sorted(existing - fresh.keys())

for i in range(0, len(to_add), 100):
    batch = to_add[i:i + 100]
    resp = gclient.models.embed_content(
        model=MODEL, contents=[fresh[c][0] for c in batch],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=DIM))
    v = np.asarray([e.values for e in resp.embeddings], dtype=np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    col.upsert(ids=batch, embeddings=v, documents=[fresh[c][0] for c in batch],
               metadatas=[fresh[c][1] for c in batch])
if to_delete:
    col.delete(ids=to_delete)
print(f"chunks={len(fresh)} reused={len(fresh) - len(to_add)} embedded={len(to_add)} "
      f"deleted={len(to_delete)} total_in_index={col.count()}")
```

**Run.**
```bash
python lab9_incremental_ingest.py data/claims_policy_v1.pdf
# edit one section of the policy, export as v2 with the same file name, then:
python lab9_incremental_ingest.py data/claims_policy_v1.pdf
```

**Expected output (illustrative).**
```
chunks=41 reused=0 embedded=41 deleted=0 total_in_index=41
chunks=42 reused=37 embedded=5 deleted=4 total_in_index=42
```

**Key lines.**
1. `cid = sha256(f"{MODEL}|{DIM}|{text}")`. A content-addressed ID: an unchanged chunk keeps the same ID, so it is never re-embedded. A model or dimension change automatically produces new IDs.
2. Collection name `claims_<model>_<dim>`. This makes cross-model mixing impossible (see Lab 4 and Lab 8 errors).
3. `col.get(where={"source": ...}, include=[])`. This returns IDs only (`Collection.get(ids, where, limit, offset, where_document, include)`, `api/models/Collection.py:149-154`).
4. `to_delete = existing - fresh`. Without this, stale, superseded policy wording stays retrievable. That is a correctness bug, and in regulated domains a compliance bug.
5. `HuggingFaceTokenizer.from_pretrained(model_name=..., max_tokens=400)` (`docling_core/.../tokenizer/huggingface.py:70-75`). **Gotcha:** Gemini does not publish a local HF tokenizer. A proxy tokenizer with a safety margin (400 « 2,048-token limit for 001) is a pragmatic choice [proxy choice is this lab's assumption, not an official recommendation].

**Common errors.**
- Re-running after changing `DIM` "works" but doubles the index. That is why `DIM` is in the ID and the collection name.
- `IndexError` on `pages[0]` for chunks with no provenance (for example, generated headings). This is guarded by `-1` above.
- Gemini `429` during a big first ingest. Add the retry loop from Lab 4.

**Best practice.** Record `embedded`, `reused` and `deleted` per run as pipeline metrics. A sudden "reused=0" on a small edit means boundary drift (next bullet), or that someone changed chunking parameters.

**Insight from new arXiv work.**
- *Chunk Recomputation under Real Document Revisions* (arXiv **2610.31019**, 22 Oct 2026). This paper is the direct motivation for this lab. On 120 pairs of adjacent Wikipedia revisions (Chinese and English), with byte-identical reuse and a frozen encoder: **fixed-size chunking recomputed 57-68%** of the new version's embedding workload, recursive chunking 38-56%, and content-defined chunking 43-54%. Evidence recall differed by **under 2 points**. **Boundary drift** is one cause. Takeaway: report update cost next to retrieval quality, and prefer structure-aligned chunkers for documents that change often.
- *RAGit* (arXiv **2610.24659**, 17 Oct 2026). An open-source workbench (https://github.com/OmarElbachyr/ragit) that treats parser × chunker × index as **experimental variables** and maps chunks back to page-level rankings for evaluation. Use it, or copy its design, to A/B Lab 1 against Lab 2 on your own documents.
- *The Bottleneck Is Retrieval, Not Reading* (arXiv **2610.26951**, 18 Oct 2026). Similarity retrieval surfaces *any* relevant chunk far more reliably than *all* required chunks for multi-fact queries. Chunking also **destroys document meta-information** needed for identity-bearing queries ("which policy version says..."). This is why Labs 1, 8 and 9 put `source`, `heading` and `pages` into every chunk's metadata.

---

## Cross-cutting gotchas for the deck (each verified above)

1. **Chunk with the embedder's tokenizer.** Docling defaults to the MiniLM tokenizer, and LangChain defaults to *characters*. Either one can silently exceed your embedder's window. (Labs 1, 3)
2. **Normalize when you truncate `gemini-embedding-001`.** `gemini-embedding-2` normalizes automatically. FAISS and pgvector inner-product ranking assumes unit vectors. (Labs 4, 6)
3. **`gemini-embedding-2` with a plain list of strings returns one aggregated vector.** Wrap each input in `types.Content`. (Lab 4)
4. **Default ANN search breadth is small.** FAISS `efSearch=16`, FAISS IVF `nprobe=1`, pgvector `hnsw.ef_search=40`, Chroma `ef_search=100`. Tune it against exact search. (Labs 6-8)
5. **Post-filtering starves top-k.** pgvector needs `hnsw.iterative_scan`. In FAISS, use `IDSelector` inside the search, not a Python filter afterwards. (Labs 6, 7)
6. **Default metrics are L2.** FAISS HNSW defaults to L2, and Chroma with `embedding_function=None` defaults to L2. Set cosine/IP explicitly. (Labs 6, 8)
7. **pgvector's HNSW/IVFFlat dimension limit is 2,000 for `vector`.** 3072-dim Gemini vectors need `halfvec` or a smaller `output_dimensionality`. (Lab 7)
8. **Docling `do_ocr=True` is the default.** It is slow on born-digital PDFs, but turning it off breaks scans. Route by document type. (Lab 1)
9. **Packaging changes in 2026.** `docling` is now a meta-package over `docling-slim[standard]`. sentence-transformers v6 renamed `get_sentence_embedding_dimension` and moved its modules. Unstructured requires Python <3.14. (§0, Labs 1, 5)

## Not verified / open items
- No code was executed (pip blocked). All outputs are illustrative.
- The exact Gemini 429 message text and the per-request item cap for text `embed_content` are [UNVERIFIED].
- The exact Chroma dimension-mismatch error text (raised in Rust) is [UNVERIFIED].
- The HF gated-repo `OSError` wording is [UNVERIFIED].
- Line numbers refer to main-branch clones of 2026-10-23 and may drift by a few lines from the PyPI release builds. For Chroma, the list-metadata and HNSW defaults were re-checked at tag `1.5.9`.
