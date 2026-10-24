# 01 - The Customization Decision Map (as of 2026-10-23)

Prompting / context engineering vs RAG vs SFT vs preference tuning (DPO) vs RL (RFT). Covers cost, data needs and latency, when each one wins, managed tuning services, RAG in brief, and company examples.

> Research date: 2026-10-23. Every item was fetched from a primary source unless it is marked [UNVERIFIED]. The web-search budget ran out partway through, so some company numbers come from memory and carry that tag.

---

## 0. Headline for October 2026: the managed-tuning market is shifting

- **OpenAI is shutting down self-serve fine-tuning.** The deprecations page (https://developers.openai.com/api/docs/deprecations) gives these dates:
  - **2026-05-07**: developers notified. "Creating fine-tuning jobs or training is not available to organizations that have not previously run fine-tuning."
  - **2026-07-02**: job creation closed to organizations "that have not run inference" on fine-tuned models.
  - **2027-01-06**: "Active existing customers will no longer be able to create new fine-tuning jobs on this date."
  - **2026-10-23 (today)**: `ft-o4-mini-2025-04-16`, `ft-gpt-4.1-nano-2025-04-14`, `ft-gpt-3.5-turbo`, `ft-gpt-4`, `ft-babbage-002` and `ft-davinci-002` snapshots shut down. RFT ran on o4-mini, so **OpenAI RFT effectively ends today**.
  - "Inference on fine-tuned models will be disabled only when the underlying base model is deprecated."
- **Fireworks managed RFT is deprecated.** "Managed Training no longer accepts new RFT jobs". New RL work moves to the **Training API**: "Async GRPO with a custom rollout function", "Multi-turn harnesses, tools, sandboxes, and token ancestry" (https://docs.fireworks.ai/fine-tuning/reinforcement-fine-tuning-models).
- **Gemini API / AI Studio has no fine-tuning.** Since Gemini 1.5 Flash-001 was deprecated in May 2025, "we no longer have a model available which supports fine-tuning in the Gemini API or AI Studio". Tuning is available only on Google Cloud (Vertex AI / "Gemini Enterprise Agent Platform"; the docs navigation now uses that name) (https://ai.google.dev/gemini-api/docs/model-tuning).
- **Growth is coming from hyperscalers and low-level training APIs.** Amazon Bedrock RFT launched 2025-12-03. Vertex supports SFT and preference tuning on Gemini 2.5 / 3.1 / 3.5. Tinker (Thinking Machines) and the Fireworks Training API expose `forward_backward` and `optim_step` style primitives in place of "upload JSONL, press go".

**Slide line:** "Black-box managed fine-tuning is converging into two things: hyperscaler tuning of their own models (Vertex, Bedrock), and do-it-yourself RL loops on rented training APIs (Tinker, Fireworks Training API)."

---

## 1. The decision map

### 1.1 The two-axis frame (OpenAI, "Optimizing LLM accuracy")
Source: https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy
- **Context optimization** (x-axis) addresses *what the model knows*: missing, stale or proprietary knowledge. Tools: prompting, RAG.
- **LLM optimization** (y-axis) addresses *how the model behaves*: format, tone, style, consistent reasoning. Tools: fine-tuning, preference tuning, RL.
- Quotes:
  - "RAG only solves our in-context learning issues"
  - "Quality of training data is more important than quantity when fine-tuning"
  - "you use the right optimization tool for the right job"
- Numbers: build an eval set of **20+** ground-truth questions before going further. Start fine-tuning with about **50** examples.
- Icelandic grammar-correction case (BLEU): GPT-4 zero-shot **62**, 3-shot **70**, GPT-3.5 fine-tuned on 1,000 examples **78**, GPT-4 fine-tuned on 1,000 examples **87**, GPT-4 fine-tuned + RAG **83**. RAG lowered the score because the task was behavioral, not knowledge-based.
- Business break-even example: +$20 per success, -$40 per escalation, -$1,000 churn in 5% of failures. Break-even accuracy is **81.5%**.

### 1.2 Ladder of interventions (cheapest first)

| Rung | What changes | Data needed | Upfront cost | Inference latency/cost | Wins when |
|---|---|---|---|---|---|
| 1. Prompting / context engineering | Tokens in the window | 0 to tens of examples (few-shot), an eval set of 20+ | Hours | Longer prompts mean more tokens; prompt caching offsets this | Always try first; the task fits the model's priors |
| 2. Long-context "stuff it all in" | Whole KB in prompt | KB under ~200k tokens (~500 pages) per Anthropic | Very low | High per call unless cached | Small, stable corpora |
| 3. RAG / agentic RAG | Retrieved evidence at runtime | A corpus, no labels; eval Q/A pairs | Days (index + chunking + eval) | +retrieval hop (tens to hundreds of ms); agentic RAG adds multiple LLM turns | Fresh, large, proprietary, citable, permissioned knowledge |
| 4. SFT (LoRA / full) | Weights: format, style, skill, distillation | 50 to 500 to start (OpenAI ≥50; Vertex "100 to 500"), up to tens of thousands | Training tokens × epochs, plus hosting | Can *shrink* prompts and allow a smaller model | Consistent format/tone, narrow tasks, distilling a big model into a small one |
| 5. Preference tuning (DPO) | Weights: relative quality | Pairs (chosen, rejected) | ~1.1x to 4x SFT token price (Together) | Same as SFT | Style, safety and helpfulness judgments that are hard to write as one "gold" answer |
| 6. RL / RFT (GRPO, RLVR, RLAIF) | Weights: policy optimized against a grader | Tens to thousands of *prompts* + a reward function; no gold outputs needed | Highest: rollouts + training | Same as SFT; often lets a small model match a large one | Verifiable tasks (code, math, extraction, tool use, agents) where graders exist |

**Rules of thumb (sourced):**
1. **Knowledge goes to RAG, behavior goes to tuning.** Ovadia et al. 2023: "RAG consistently outperforms" unsupervised fine-tuning for knowledge injection, both for seen and for new facts.
2. **Fine-tuning on new facts raises hallucination.** Gekhman et al. (EMNLP 2024): models learn new-knowledge examples slowly, and hallucination rises linearly once they do. "Fine-tuning mainly teaches them to use that knowledge more effectively."
3. **The two combine.** Balaguer et al. (Microsoft, 2024, agriculture): fine-tuning gave **+6 p.p.** accuracy, and RAG added a cumulative **+5 p.p.** on top.
4. **Teach the model to use retrieval.** RAFT (Zhang et al. 2024) fine-tunes with distractor documents so the model learns to ignore irrelevant chunks and cite the relevant one. Gains reported on PubMed, HotpotQA and Gorilla.
5. **LoRA is usually enough.** "LoRA Without Regret" (Schulman et al., Thinking Machines, 2025-09-29): LoRA matches full fine-tuning on small and medium SFT sets. For RL it matches FullFT **even at rank 1**, because policy gradients carry about "one bit per episode". The optimal LR is about **10x** the FullFT LR. Apply LoRA to all layers, including MLP/MoE.

### 1.3 Decision flow (diagram in words)
```
START: define task + build eval (20+ gold cases, business metric)
  -> Prompt / context-engineer (instructions, few-shot, tools, caching)
       pass eval? -> SHIP
  -> Failure analysis: is the failure KNOWLEDGE or BEHAVIOR?
       KNOWLEDGE (missing/stale/private facts, needs citations, ACLs)
          -> KB < ~200k tokens? -> long context + prompt caching
          -> else RAG -> hybrid search + rerank + contextual chunks
          -> multi-hop / ambiguous? -> agentic RAG (plan, retrieve, reflect)
       BEHAVIOR (format, tone, policy, latency/cost of big model)
          -> have gold outputs? -> SFT (LoRA), or distill teacher -> student
          -> have only comparisons? -> DPO / preference tuning
          -> have a grader/verifier but no gold? -> RFT / GRPO
  -> Combine: RAG + SFT (RAFT) ; SFT -> DPO (Vertex recommends SFT first)
  -> Re-evaluate; monitor drift; re-tune when base model is deprecated
```

### 1.4 Context engineering (rung 1, the 2025-26 framing)
Anthropic, "Effective context engineering for AI agents" (2025-09-29): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Definition: "the set of strategies for curating and maintaining the optimal set of tokens (information) during LLM inference."
- **Context rot**: recall drops as the window fills. Context is a finite "attention budget".
- Techniques: **just-in-time retrieval** (keep file paths and queries, load with tools), **compaction** (summarize history and continue in a fresh window), **clearing stale tool results**, **sub-agents** with clean windows that return condensed summaries.

---

## 2. Managed tuning services (verified October 2026)

### 2.1 Google Vertex AI (docs moving under "Gemini Enterprise Agent Platform")
**Supervised fine-tuning** (https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-supervised-tuning)
- Supported models: **Gemini 3.5 Flash-Lite, Gemini 3.5 Flash, Gemini 3.1 Flash-Lite, Gemini 2.5 Pro, Gemini 2.5 Flash-Lite, Gemini 2.5 Flash.**
- Data: JSONL in Cloud Storage. "For best results, provide at least 100 to 500 examples." Separate pages cover text, document, image, audio, video and function calling.
- Hyperparameters: `epoch_count`, `adapter_size`, `learning_rate_multiplier` (default 1). Google recommends running the first job with defaults.
- Thinking models: turn thinking off, or set the minimum budget, for tuned tasks.
- `evaluation_config` (auto-eval) is in Preview, us-central1 only. The console tunes only 2.5 models. The SDK sample uses location `us`.

**Preference tuning (DPO)** (https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-preference-tuning, overview: .../gemini-preference-tuning)
- Prompt + preferred + dispreferred responses. `method="PREFERENCE_TUNING"`.
- **`beta` recommended range 0.01 to 0.5.** Lower values make more aggressive updates. 0 means no learning.
- Recommended recipe: **SFT on the preferred responses first, then preference-tune from that checkpoint.**
- Metrics: `/preference_optimization_train_loss`, `/eval_total_loss`.
- Announcement: preference tuning for Gemini 2.5 Flash and Flash-Lite (https://discuss.google.dev/t/preference-tuning-now-available-for-gemini-2-5-flash-models-on-vertex-ai/287524). The SDK sample now uses `gemini-3.5-flash`.
- Limits: cached pages disagree (1 GB / 10M examples / adapter sizes 1, 2, 4, 8, 16 vs 10 GB / 1M). [UNVERIFIED, check the live page]

Code: Vertex SFT and preference tuning with the Google Gen AI SDK (`pip install google-genai`). Adapted from the SDK docs (https://googleapis.github.io/python-genai/) and the Vertex pages above.
```python
import time
from google import genai
from google.genai import types
from google.genai.types import HttpOptions

client = genai.Client(http_options=HttpOptions(api_version="v1"))  # Vertex env vars set

training_dataset = types.TuningDataset(
    gcs_uri="gs://your-gcs-bucket/your-tuning-data.jsonl",
)
tuning_job = client.tunings.tune(
    base_model="gemini-3.5-flash",
    training_dataset=training_dataset,
    config=types.CreateTuningJobConfig(
        tuned_model_display_name="support-tone-v1",
        epoch_count=1,
        # method="PREFERENCE_TUNING",  # for DPO-style tuning (per Vertex docs)
    ),
)
done = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED"}
while tuning_job.state not in done:
    time.sleep(60)
    tuning_job = client.tunings.get(name=tuning_job.name)

resp = client.models.generate_content(
    model=tuning_job.tuned_model.endpoint, contents="why is the sky blue?")
```
Note: the exact placement of `method` (top-level kwarg vs config field) is shown on the Vertex page only in fragments. [UNVERIFIED placement]

### 2.2 OpenAI fine-tuning + RFT (shutting down; see §0)
Source: https://developers.openai.com/api/docs/guides/fine-tuning
- "OpenAI is winding down the fine-tuning platform." "The platform is no longer accessible to new users."
- Last supported matrix:
  - **SFT**: gpt-4.1 / 4.1-mini / 4.1-nano (2025-04-14)
  - **Vision FT**: gpt-4o-2024-08-06
  - **DPO**: gpt-4.1 family
  - **RFT**: `o4-mini-2025-04-16` only ("o-series reasoning models only")
- **RFT** (https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning): graders `string_check`, `text_similarity`, `score_model` (LLM judge, 0 to 1), `python`, `multi` (combined via `calculate_output`). Hyperparameter `reasoning_effort`. Limits: **50,000 train / 1,000 test** examples. Billed by training time ([UNVERIFIED] historically about $100/hour of training).
- **DPO** (https://developers.openai.com/api/docs/guides/direct-preference-optimization): JSONL fields `input`, `preferred_output`, `non_preferred_output`. `beta` takes values in 0 to 2 or `auto`. Higher values are more conservative.

Code (adapted from the OpenAI DPO/RFT guides):
```python
from openai import OpenAI
client = OpenAI()

f = client.files.create(file=open("prefs.jsonl", "rb"), purpose="fine-tune")
job = client.fine_tuning.jobs.create(
    training_file=f.id,
    model="gpt-4.1-mini-2025-04-14",
    method={"type": "dpo", "dpo": {"hyperparameters": {"beta": 0.1}}},
)
# RFT variant (o4-mini, now retired):
# method={"type": "reinforcement",
#         "reinforcement": {"grader": {"type": "string_check", "name": "exact",
#                                      "input": "{{sample.output_text}}",
#                                      "reference": "{{item.label}}", "operation": "eq"},
#                           "hyperparameters": {"reasoning_effort": "medium"}}}
```
RFT customer results (https://developers.openai.com/api/docs/guides/rft-use-cases):
- **Ambience Healthcare**: ICD-10 coding 0.39 to 0.57, "trailing humans to leading them by 12 points".
- **Harvey**: legal citation extraction F1 0.563 to 0.6765 (+20%).
- **ChipStack**: about +12 p.p.
- **Milo**: 0.86 to 0.91 (hardest cases 0.46 to 0.71).
- **Accordance** (tax): +38.89%.
- **SafetyKit**: F1 86% to 90%.
- **Thomson Reuters**: beat o1 and o3-mini baselines (chart only).

### 2.3 Anthropic / Amazon Bedrock
- **Anthropic's first-party API offers no public fine-tuning.** Claude fine-tuning was only ever offered as **Claude 3 Haiku on Bedrock** (GA Nov 2024, us-west-2; https://www.anthropic.com/news/fine-tune-claude-3-haiku-ga). Claude 3 Haiku reportedly reached end of life on Bedrock in September 2026 [UNVERIFIED exact date]. Anthropic's customization story is now context engineering, prompt caching, Skills and tools, not weights.
- **Bedrock customization methods** (https://docs.aws.amazon.com/bedrock/latest/userguide/custom-models.html):
  - Supervised fine-tuning, reinforcement fine-tuning, distillation (teacher to student; Bedrock synthesizes teacher responses), and continued pre-training on some models.
  - Billing: "number of tokens in training data corpus × number of epochs" plus monthly model storage.
- **Bedrock RFT** (2025-12-03, https://aws.amazon.com/blogs/aws/improve-model-accuracy-with-reinforcement-fine-tuning-in-amazon-bedrock):
  - Launch model: **Amazon Nova 2 Lite**, with more promised.
  - Rewards: Python in **AWS Lambda** (RLVR), or **model-as-judge** (RLAIF). 7 reward templates.
  - Data: Bedrock **invocation logs**, JSONL, or S3, in OpenAI Chat Completions format.
  - Claim: "**66% accuracy gains on average** over base models" (https://aws.amazon.com/about-aws/whats-new/2025/12/bedrock-reinforcement-fine-tuning-66-base-models). Salesforce cites up to **73%**. Both are vendor-reported numbers.

### 2.4 Together AI
- Methods: LoRA (default `lora=True`), full fine-tuning (`lora=False`), preference tuning (DPO), from-checkpoint continuation (https://docs.together.ai/docs/fine-tuning-quickstart).
- Billing: tokens = n_epochs × train tokens + n_evals × val tokens (https://support.together.ai/articles/7922061943-fine-tuning-pricing).
- Pricing (third-party trackers):
  - Older size-band rates, SFT-LoRA: $0.48 / $1.50 / $2.90 per 1M tokens (≤16B / 17-69B / 70-100B).
  - Reported 2026-09-20 move to per-model pricing, e.g. Llama 3.3 70B at $2.03 SFT / $5.08 DPO (LoRA). [UNVERIFIED, third-party capture]
```python
from together import Together
client = Together()
train_file = client.files.upload(file="coqa_train.jsonl", purpose="fine-tune", check=True)
job = client.fine_tuning.create(
    training_file=train_file.id,
    model="Qwen/Qwen3.5-9B",
    lora=True, n_epochs=3, learning_rate=1e-5,
    n_checkpoints=1, warmup_ratio=0, train_on_inputs="auto",
    suffix="qwen35_9b_demo",
)
```

### 2.5 Fireworks AI
- RFT blog (2025-11-10, https://fireworks.ai/blog/fireworks-rft): RFT on open models (DeepSeek V3, Kimi K2). Evaluators score 0 to 1 (rule-based, tests, LLM-judge, hybrid). Launch via `firectl rftj create` or `eval-protocol create rft`.
  - **Genspark** Deep Research agent: "+10% better quality vs a SOTA closed model", "+33% more tool calls", "~50% cost reduction".
  - **Vercel v0**: "33% improvement over closed-source models", "40X faster", 93 to 94% error-free generation (the page gives both figures).
- **Now:** managed RFT is deprecated in favor of the **Training API** (custom async GRPO loops, multi-turn harnesses, sandboxes). The docs reference a "Price vs Tinker" comparison and warn: do not "assume a free tier".

### 2.6 Tinker (Thinking Machines), the "training API" pattern
- https://tinker-docs.thinkingmachines.ai/ — install `uv pip install tinker tinker-cookbook`. "28+" models, LoRA "from 1B to 1T+ parameters", dense and MoE, text and vision.
- Primitives (cheatsheet sections): forward-backward, optimizer step, sample, save/load weights.
- Sketch [UNVERIFIED exact signatures]:
```python
import tinker
svc = tinker.ServiceClient()
tc = svc.create_lora_training_client(base_model="Qwen/Qwen3-8B", rank=32)
for batch in data:
    tc.forward_backward(batch, loss_fn="cross_entropy")   # or importance-sampling for RL
    tc.optim_step(tinker.AdamParams(learning_rate=1e-4))
```

### 2.7 Comparison table for a slide

| Provider | SFT | DPO/pref | RL/RFT | Notes (Oct 2026) |
|---|---|---|---|---|
| Vertex AI (Gemini) | Yes: 2.5 / 3.1 / 3.5 Flash(-Lite), 2.5 Pro | Yes (`PREFERENCE_TUNING`) | No managed RFT found [UNVERIFIED] | Gemini API / AI Studio: no tuning |
| OpenAI | gpt-4.1 family (existing customers) | gpt-4.1 family | o4-mini, retired 2026-10-23 | No new jobs after 2027-01-06 |
| Anthropic | Only Claude 3 Haiku via Bedrock (legacy) | No | No | Customization = context engineering |
| Amazon Bedrock | Nova, Llama, etc. | [UNVERIFIED] | Nova 2 Lite (Lambda/judge rewards) | Distillation built-in |
| Together | LoRA + full, many OSS models | Yes | [UNVERIFIED] | Per-token pricing |
| Fireworks | Yes | Yes | Managed RFT deprecated; Training API | RL as code |
| Tinker | Primitive-level | DIY | DIY (RL cookbook) | LoRA only |

---

## 3. RAG in brief (for this deck)

### 3.1 Classic pipeline (diagram in words)
`Ingest (parse PDF/HTML/tables) -> chunk (e.g. 512 tokens, 100 overlap) -> enrich (contextual header per chunk) -> embed + BM25 index -> [query] -> rewrite/expand -> hybrid retrieve top-k (e.g. 20-150) -> rerank to top-n (e.g. 3-20) -> pack context with citations -> generate -> grounding/citation check -> eval (recall@k, faithfulness, answer correctness)`

- **Anthropic Contextual Retrieval** (2024-09-19, https://www.anthropic.com/news/contextual-retrieval). Baseline top-20 retrieval failure rate is 5.7%.
  - Contextual embeddings: -35% (3.7%)
  - Plus contextual BM25: **-49%** (2.9%)
  - Plus reranking: **-67%** (1.9%)
  - Also: if the KB is "smaller than 200,000 tokens", skip RAG and put it all in the prompt.
- **Vertex AI RAG Engine** quickstart (https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-quickstart).
  - The October 2026 sample uses the new `agentplatform` client: `client.rag.create_corpus`, `client.rag.import_files` with `RagFileTransformationConfig(RagFileChunkingConfig(chunk_size=512, chunk_overlap=100))`, and `client.rag.retrieve_contexts` with `RagRetrievalConfig(top_k=3, vector_distance_threshold=0.5)`.
  - Grounded generation goes through `genai_types.Tool(retrieval=Retrieval(vertex_rag_store=VertexRagStore(...)))`.
  - Notebook: GoogleCloudPlatform/generative-ai `intro_rag_engine.ipynb`.
  - The older `vertexai.preview.rag` / `rag.retrieval_query` API names are no longer in the quickstart.

Sketch adapted from the quickstart [UNVERIFIED exact kwarg names]:
```python
import agentplatform
from agentplatform import types
from google import genai
from google.genai import types as genai_types

client = agentplatform.Client(project=PROJECT, location="us-central1")
corpus = client.rag.create_corpus(display_name="policies")
client.rag.import_files(corpus.name, paths=["gs://bucket/policies/"],
    transformation_config=types.RagFileTransformationConfig(
        chunking_config=types.RagFileChunkingConfig(chunk_size=512, chunk_overlap=100)))
ctx = client.rag.retrieve_contexts(rag_resources=[corpus.name],
    rag_retrieval_config=types.RagRetrievalConfig(top_k=3), text="What is the refund window?")
```

### 3.2 Agentic RAG
- Survey: "Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG" (Singh et al., arXiv 2501.09136, Jan 2025, v4 April 2026). Patterns: "reflection, planning, tool use, and multi-agent collaboration."
- Loop: `plan sub-questions -> choose tool (vector search / SQL / web / API) -> retrieve -> read & reflect ("enough evidence?") -> re-query or answer -> cite`.
- Trade-off: higher recall on multi-hop questions, at the cost of 2 to 10x more LLM calls and latency. This connects to just-in-time context engineering (agents grep and open files instead of relying only on pre-chunked vectors).
- Genspark's RFT-trained Deep Research agent (+33% tool calls) shows **RL and agentic RAG converging**: RL teaches *when and how to retrieve*.

### 3.3 When RAG beats fine-tuning (and the reverse)
- **RAG wins** when knowledge changes often, the corpus is large, answers need citations or audit trails, per-user ACLs matter, or the domain is long-tail factual (Ovadia 2023; Gekhman 2024).
- **FT wins** for format and style consistency, latency and cost (distilling into a small model, shorter prompts), narrow classification or extraction, or a fixed task spec. In OpenAI's Icelandic example, adding RAG *hurt* (87 to 83).
- **Both**: Balaguer 2024 (+6 then +5 p.p.); RAFT (train with retrieved distractors).

---

## 4. Real-world examples

| Company | Technique | Result | Source |
|---|---|---|---|
| Cursor (Tab) | **Online RL** from accept/reject; new checkpoints every 1.5 to 2 h | **21% fewer suggestions, 28% higher accept rate**, 400M+ req/day | https://cursor.com/blog/tab-rl (2025-09-12) |
| Ambience Healthcare | OpenAI RFT | ICD-10 0.39 to 0.57 | OpenAI RFT use cases |
| Harvey | OpenAI RFT (+ earlier custom case-law model) | F1 +20% | same; custom-model details [UNVERIFIED, openai.com/index/harvey returned 403] |
| Genspark | Fireworks RFT on open model | +10% quality vs closed SOTA, ~50% cost cut | Fireworks blog |
| Vercel v0 | Fireworks RFT | +33% vs closed models, 40x faster | Fireworks blog |
| Salesforce | Bedrock RFT | up to 73% accuracy gain (AWS benchmark) | AWS What's New |
| Morgan Stanley | RAG over research library (GPT-4) | ~98% advisor-team adoption [UNVERIFIED, page 403] | https://openai.com/index/morgan-stanley/ |
| Microsoft agriculture study | RAG + FT | +6 p.p. FT, +5 p.p. RAG | arXiv 2401.08406 |

Quotable lines:
- "Quality of training data is more important than quantity when fine-tuning" (OpenAI).
- "RAG consistently outperforms" unsupervised fine-tuning for knowledge (Ovadia et al.).
- "Optimal LR is 10 times higher for LoRA" (Thinking Machines).
- "Managed Training no longer accepts new RFT jobs" (Fireworks docs).
- Context engineering is "the set of strategies for curating and maintaining the optimal set of tokens" (Anthropic).

---

## 5. Open challenges
1. **Platform risk.** Tuned weights are tied to base-model deprecation; the OpenAI ft-o4-mini snapshot dies today. Portable recipes (data + grader + eval) matter more than checkpoints.
2. **Graders are the new labels.** RFT quality is bounded by the reward function. Reward hacking and judge bias need red-team tests (Fireworks recommends testing full, partial, zero, malformed and edge cases).
3. **Knowledge via FT increases hallucination** (Gekhman). Keep facts in retrieval.
4. **Evaluating agentic RAG**: cost and latency budgets, multi-hop attribution, and retrieval-recall vs answer-faithfulness trade-offs.
5. **Vendor-reported gains** (66%, 73%, 40x) are not independently replicated. Teach students to demand task-matched evals.
6. **On-policy data loops** (Cursor) need deployment infrastructure, privacy controls and fast rollback.

---

## 6. Slide ideas (8)
1. **"The Ladder of Customization"**: a vertical staircase (prompt, context, RAG, SFT, DPO, RL) with cost, data and latency bars that grow per step; each step animates in.
2. **"Knowledge vs Behavior"**: the OpenAI 2x2 (context optimization on x, LLM optimization on y). Techniques fly into quadrants; the arrow path runs prompt, then RAG, then FT, then RAG+FT.
3. **"The Icelandic Lesson"**: a bar chart of 62 / 70 / 78 / 87 / 83 BLEU. Highlight the drop when RAG is added to a behavioral task.
4. **"Decision Flowchart"**: the §1.3 flow as an interactive tree. Click knowledge or behavior, then gold outputs / pairs / grader.
5. **"October 2026: The Managed-Tuning Shake-out"**: a timeline (Gemini API tuning gone May 2025, Bedrock RFT Dec 2025, OpenAI wind-down May 2026, ft-o4-mini retired 2026-10-23, Fireworks managed RFT deprecated, OpenAI last jobs 2027-01-06).
6. **"Provider Matrix"**: the §2.7 table with check, cross and sunset icons.
7. **"RAG Pipeline + Contextual Retrieval"**: an animated pipeline. The failure-rate bar shrinks 5.7%, 3.7%, 2.9%, 1.9% as each stage lights up.
8. **"Agentic RAG Loop"**: a circular plan, retrieve, reflect, answer loop, compared side by side with a one-shot linear RAG pipeline.
9. **"RL in Production: Cursor Tab"**: a loop diagram (deploy, collect accept/reject, policy gradient, redeploy every ~2 h) with -21% / +28% counters.
10. **"Receipts"**: a grid of RFT company wins (Ambience, Harvey, Genspark, Vercel, SafetyKit) with a "vendor-reported" watermark, setting up the open-challenges slide.

---

## 7. Source list
- OpenAI, Optimizing LLM accuracy: https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy
- OpenAI, Fine-tuning guide: https://developers.openai.com/api/docs/guides/fine-tuning
- OpenAI, Reinforcement fine-tuning: https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning
- OpenAI, RFT use cases: https://developers.openai.com/api/docs/guides/rft-use-cases
- OpenAI, Direct preference optimization: https://developers.openai.com/api/docs/guides/direct-preference-optimization
- OpenAI, Deprecations: https://developers.openai.com/api/docs/deprecations
- Vertex AI, Supervised tuning: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-supervised-tuning
- Vertex AI, Preference tuning: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-preference-tuning
- Vertex AI RAG Engine quickstart: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-quickstart
- Gemini API model tuning (deprecated): https://ai.google.dev/gemini-api/docs/model-tuning
- Google Gen AI Python SDK: https://googleapis.github.io/python-genai/
- Amazon Bedrock custom models: https://docs.aws.amazon.com/bedrock/latest/userguide/custom-models.html
- AWS News Blog, "Improve model accuracy with reinforcement fine-tuning in Amazon Bedrock": https://aws.amazon.com/blogs/aws/improve-model-accuracy-with-reinforcement-fine-tuning-in-amazon-bedrock
- Anthropic, Fine-tune Claude 3 Haiku GA: https://www.anthropic.com/news/fine-tune-claude-3-haiku-ga
- Anthropic, Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval
- Anthropic, Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Together, Fine-tuning quickstart: https://docs.together.ai/docs/fine-tuning-quickstart
- Fireworks, RFT blog: https://fireworks.ai/blog/fireworks-rft ; docs: https://docs.fireworks.ai/fine-tuning/how-rft-works.md
- Tinker docs: https://tinker-docs.thinkingmachines.ai/
- Thinking Machines, "LoRA Without Regret": https://thinkingmachines.ai/blog/lora/
- Cursor, "Improving Cursor Tab with online RL": https://cursor.com/blog/tab-rl
- Ovadia et al., "Fine-Tuning or Retrieval? Comparing Knowledge Injection in LLMs", arXiv 2312.05934
- Balaguer et al., "RAG vs Fine-tuning: Pipelines, Tradeoffs, and a Case Study on Agriculture", arXiv 2401.08406
- Gekhman et al., "Does Fine-Tuning LLMs on New Knowledge Encourage Hallucinations?", arXiv 2405.05904 (EMNLP 2024)
- Zhang et al., "RAFT: Adapting Language Model to Domain Specific RAG", arXiv 2403.10131
- Singh et al., "Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG", arXiv 2501.09136
