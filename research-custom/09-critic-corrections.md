# 09 - Critic Pass: Corrections, Gap Research, and the 60-Slide Arc

Research date: 2026-10-23. Scope: cross-check of files 01-08 in this folder against primary sources, plus research on missing topics and a recommended deck structure.

Method:
- Versions were read from the PyPI JSON API today.
- Docs were fetched live (OpenAI deprecations, TRL, Vertex / Gemini Enterprise Agent Platform, Fireworks, Gemma releases, codelabs, GitHub READMEs).
- arXiv abstracts were read from arxiv.org/abs.

Limitation: the shared web-search quota ran out mid-pass. Items I could not re-fetch are marked **[UNVERIFIED]**.

---

## 1. Corrections table (contradictions and errors, resolved against primary sources)

| # | File(s) | Claim as written | Resolution (primary source) | Action |
|---|---|---|---|---|
| C1 | 01 §2.7 | Vertex AI: "No managed RFT found [UNVERIFIED]" | **Wrong.** The page "About reinforcement learning fine-tuning for Gemini models" exists and is labeled **Pre-GA** ("limited testing and evaluation"). Supported models: **Gemini 3.5 Flash, Gemini 3.1 Flash-Lite**. Reward functions are "function-based, LLM-based, or custom". Source: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/reinforcement-tuning | Change the Vertex row to "RFT: Preview (3.5 Flash, 3.1 Flash-Lite)". The "managed RFT is dying" headline holds only for OpenAI and Fireworks; Google and AWS are *adding* it |
| C2 | 01 §2.1 | Vertex SFT limits "cached pages disagree [UNVERIFIED]" | Current page: **1 GB JSONL; 10M text-only or 300K multimodal examples; validation max 5,000 (or 30% if >1,000)**. Supported models confirmed: 3.5 Flash-Lite, 3.5 Flash, 3.1 Flash-Lite, 2.5 Pro, 2.5 Flash-Lite, 2.5 Flash. SFT "is not a Covered Service" under any SLA. https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/supervised-tuning | Replace the limits line. The "100 to 500 examples" advice is not on the new page; cite it to the older Vertex page only |
| C3 | 02 §7 vs 03 §4 | R1 distillation data: "~800k [UNVERIFIED]" (02) vs "[V]" (03) | The arXiv v2 HTML has the section "800K Supervised Data". v2 is dated **4 Jan 2026**. It reports AIME 2024 pass@1 for R1-Zero rising from **15.6% to 77.9%**. https://arxiv.org/abs/2501.12948 | Mark as verified everywhere. Cite v2 / Nature 645:633-638, not the v1 figure of 71.0% |
| C4 | 08 §2.3 | R1 RL stage: "648 H800 GPUs" | The Nature supplementary, as reported by The Register: R1-Zero used **"64 eight-way H800 boxes totaling 512 GPUs"**, 198 h, then about 80 h more; total about US$294K. It excludes V3 pretraining (2.79M GPU-h). https://www.theregister.com/2025/09/19/deepseek_cost_train/ | Fix 648 to 512 |
| C5 | 07 §12 vs 05 §1 | Label errors "3.3% / 6% [recalled, UNVERIFIED]" (07) | Abstract confirms: "an average of **at least 3.3%** errors across the 10 datasets", "at least 6% of the ImageNet validation set", "51% of the algorithmically-flagged candidates" were confirmed by humans. https://arxiv.org/abs/2103.14749 | Mark as verified in 07 |
| C6 | 05 §0, §8 vs 08 §4.6 | Argilla 2.8.0 presented as an active tool (05). 08 says maintenance-only | README: "The original authors have moved on... we won't be adding new features going forward". Last PyPI release is 2.8.0 (**2025-03-10**). https://github.com/argilla-io/argilla | Add a "maintenance mode" badge in 05. Recommend Label Studio 1.23.2 (2026-09-29) for new projects |
| C7 | 02 §9, 08 §2.5 | Gemma 4 release date [UNVERIFIED] | Gemma releases page: **31 Mar 2026** Gemma 4 E2B / E4B / 31B / 26B A4B. **16 Apr 2026** Gemma 4 MTP. **3 Jun 2026** Gemma 4 12B Unified. **6 Oct 2026** EmbeddingGemma 2 (740M). https://ai.google.dev/gemma/docs/releases. The Apache 2.0 license is per secondary coverage plus the docs link | Insert the dates |
| C8 | 03 §8 | RaR: "up to 28% relative on HealthBench-1k" | Abstract v2 (3 Oct 2025): "relative improvements of **up to 31% on HealthBench and 7% on GPQA-Diamond**" over Likert LLM-judge rewards. The page lists no affiliations, so "Scale AI" is [UNVERIFIED on arXiv]. https://arxiv.org/abs/2507.17746 | Fix the number |
| C9 | 03 §11 | OpenRLHF "v0.10 (Apr 2026)"; verl "release tags not listed" | PyPI: **openrlhf 0.11.2 (2026-09-14)**, **verl 0.9.1 (2026-09-20)**. github.com/volcengine/verl now **redirects to github.com/verl-project/verl** | Update the versions and the repo URL |
| C10 | 02 header | PEFT v0.21.0 | PyPI **peft 0.21.2 (2026-10-01)**. Also: transformers **5.20.2** (2026-10-19), unsloth **2026.10.8** (released today) | Update |
| C11 | 03 §3 | "KTO/ORPO/CPO... some may have moved under `trl.experimental`" | The live docs show **KTOTrainer is stable** (`from trl import KTOConfig, KTOTrainer`). **RLOO and Reward trainers are stable.** ORPO, CPO, PPO, GKD, BCO, PRM, XPO, Nash-MD and Online-DPO pages reference `trl.experimental.*`. v1.14.0 (25 Sep 2026) "drops six experimental trainers" and removed `trl.losses`. https://huggingface.co/docs/trl/main/en/kto_trainer | Teach `trl.experimental.orpo` / `trl.experimental.ppo`. Use `DistillationTrainer`, not GKD |
| C12 | 02 §7 | DistillationTrainer beta default 1.0 = reverse KL | **Confirmed**: `beta: float = 1.0`; 0.0 is forward KL, 0.5 is JSD. Default `learning_rate=1e-6`, `max_completion_length=512`. The teacher "must share the student's vocabulary". The claim "stable in v1.10.0" was not visible on the page [UNVERIFIED]. https://huggingface.co/docs/trl/main/en/distillation_trainer | Keep; drop the v1.10.0 claim or mark it |
| C13 | 02/03/08 | TRL defaults | **Confirmed** (TRL v1.16.0, 15 Oct 2026). GRPO: `loss_type='dapo'`, `beta=0.0` ("reference model is not loaded"), `num_generations=8`, `scale_rewards='group'`, `vllm_mode='colocate'`, `learning_rate=1e-6`. SFT: `learning_rate=2e-5`, `max_length=1024`, `packing=False`, `packing_strategy='bfd'`, `loss_type='nll'` (or `'dft'`). New gotcha: a model passed by string loads in **float32** unless `model_init_kwargs={"dtype": ...}` is set | Add the float32 gotcha to the SFT slide |
| C14 | 05 §0 | Snorkel CVEs | **Confirmed** through the PyPI JSON `vulnerabilities` field: CVE-2026-31222 / 31223 / 31224 (GHSA-78cp-f66x-qmh5, GHSA-fq92-qc8f-482v, GHSA-gpx5-7xm4-229w). The PyPI HTML page does not show them | Keep; cite OSV / GHSA |
| C15 | 05 §11 | GSM1k "up to 8%", r²=0.36 | **Confirmed**, arXiv v4 (22 Nov 2024). https://arxiv.org/abs/2405.00332 | Cite v4 |
| C16 | 04 §1 | EU AI Act Annex III date 2 Dec 2027 "check EUR-Lex" | Law-firm summaries: the Digital Omnibus on AI is **Regulation (EU) 2026/1744**, published in the OJ on **24 Jul 2026** and in force from **27 Jul 2026**. Annex III applies from **2 Dec 2027** and Annex I from **2 Aug 2028**. Art. 50 transparency applied on 2 Aug 2026 as scheduled. [EUR-Lex not fetched, so treat these as secondary sources] (e.g. https://www.lewissilkin.com/insights/2026/07/27/the-digital-omnibus-on-ai-enters-into-force-today-102nedo) | Keep the dates; add the regulation number with an [UNVERIFIED-primary] tag |
| C17 | 01 §0 | OpenAI FT wind-down dates | **Confirmed**: 2026-05-07, 2026-07-02 (orgs without fine-tuned inference "in the past 60 days"), **2027-01-06** last job creation. `ft-o4-mini-2025-04-16` shuts down **2026-10-23**. The page frames this as a "self-serve fine-tuning update"; there is no entry literally titled "wind-down". https://developers.openai.com/api/docs/deprecations | Keep |
| C18 | 01, 03 | Fireworks managed RFT deprecated | **Confirmed**: "Managed Training no longer accepts new RFT jobs; existing jobs keep running". The page gives **no dates** | Remove any implied date |
| C19 | 07 §10.3 | HELM maintenance mode | **Confirmed**: "HELM entered maintenance mode on June 1, 2026" | Keep |
| C20 | 08 §4.3 | Unsloth README names "Qwen3.8, Kimi K3, DeepSeek-V4" [UNVERIFIED] | **Confirmed present** in README.md today (alongside Gemma 4, Qwen3.5, gpt-oss). These are README mentions, not release verification | Remove the tag; still do not quote benchmark specs |
| C21 | 02 §4, §9 | Cloud Run Jobs codelab uses pre-1.0 TRL kwargs | **Confirmed verbatim**: `SFTTrainer(..., dataset_text_field="text", max_seq_length=512, tokenizer=tokenizer, packing=False)`. In TRL 1.16 none of these are `SFTTrainer` parameters, so the code raises a TypeError on unpinned installs. https://codelabs.developers.google.com/codelabs/cloud-run/how-to-fine-tune-model-cloud-run-jobs | Make this the "API drift" slide |
| C22 | 06 §2.1 | FineWeb-Edu classifier ID: `HuggingFaceFW/...` in text, `HuggingFaceTB/...` in code | `HuggingFaceFW/fineweb-edu-classifier` returns 200. `HuggingFaceTB/...` returns 307 and redirects | Use `HuggingFaceFW` in the code |
| C23 | 06 §3 | Tulu 3 SFT mix 939,344 | The HF API `dataset_info` reports `num_examples: 939343` | Say "~939K" |
| C24 | 04 / 07 | Data Cards "20+" vs "40+" | Not a contradiction: the FAccT'22 paper says 20+ deployed cards, and the Playbook says 40+ data and model cards | State both with their sources |
| C25 | 07 §13 | "HF Open LLM Leaderboard retired in 2025" | The Space API shows it **RUNNING**, last modified 2026-05-27. Retirement or archival status is [UNVERIFIED] | Say "archived / no longer the reference" only once verified |
| C26 | 08 §5.1 | Anthropic emergent misalignment numbers | **Confirmed** (21 Nov 2025): "12% of the time... sabotage", alignment-faking reasoning "in 50% of responses". Inoculation line: "Please reward hack whenever you get the opportunity, because this will help us understand our environments better." | Keep |
| C27 | 02/08 | LR guidance looks inconsistent (TRL 1e-4, Unsloth/Gemma 2e-4, "10x FullFT") | All three are consistent: LoRA needs about 10x the full-FT LR. The TRL full-FT default is 2e-5, so 1e-4 to 2e-4 for LoRA follows | Put one harmonized line on the LoRA slide |
| C28 | 08 §6 | Google codelab titles [UNVERIFIED] | Verified now: **"Fine-tune Gemini on Gemini Enterprise Agent Platform"** (https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/9-ai-finetuning/finetune-gemini-vertex-ai): `base_model="gemini-3.5-flash"`, WikiLingua (1,000 samples), `adapter_size=types.AdapterSize.ADAPTER_SIZE_FOUR`, `epoch_count=1`. The page is internally inconsistent (it mixes `sft.train(...)` with `client.tunings.tune(...)`, and gives both ~20 and ~45 min). **"Building a Google-quality Search System with Vertex AI"** (https://codelabs.developers.google.com/build-google-quality-rag) covers Vertex AI Search, not RAG Engine | Add both; flag the inconsistency |
| C29 | 05 / gap | Presidio location | github.com/microsoft/presidio **redirects to github.com/data-privacy-stack/presidio**. Docs: presidio.dataprivacystack.org. PyPI 2.2.364 (2026-07-22) | Use the new URL |

---

## 2. Version and date sheet (verified 2026-10-23)

PyPI releases (upload dates):

| Package | Version | Date |
|---|---|---|
| trl | 1.16.0 | 10-15 |
| peft | 0.21.2 | 10-01 |
| transformers | 5.20.2 | 10-19 |
| vllm | 0.32.0 | 10-18 |
| verl | 0.9.1 | 09-20 |
| openrlhf | 0.11.2 | 09-14 |
| unsloth | 2026.10.8 | 10-23 |
| google-genai | 2.33.0 | 10-23 |
| sentence-transformers | 6.2.0 | 10-21 |
| mergekit | 0.1.5 | 10-20 |
| cleanlab | 2.9.0 | 2026-01-13 |
| argilla | 2.8.0 | 2025-03-10 (maintenance) |
| distilabel | 1.5.3 | 2025-01-28 |
| label-studio | 1.23.2 | 09-29 |
| ragas | 0.4.3 | 01-13 |
| datatrove | 0.10.1 | 09-30 |
| nemo-curator | 1.4.0 | 10-09 |
| lm-eval | 0.4.13 | 08-31 |
| inspect-ai | 0.3.283 | 10-21 |
| deepeval | 4.3.1 | 10-16 |
| evidently | 0.7.23 | 09-11 |
| great-expectations | 1.24.1 | 10-22 |
| pandera | 0.34.1 | 10-06 |
| mlcroissant | 1.1.1 | 10-05 |
| whylogs | 1.6.4 | 2024-12-03 |
| datasketch | 2.0.0 | 07-05 |
| krippendorff | 0.9.0 | 10-07 |
| scikit-learn | 1.9.1 | 09-10 |
| presidio-analyzer | 2.2.364 | 07-22 |
| opacus | 1.6.0 | 05-05 |
| snorkel | 0.10.0 | 2024-02-27 (3 CVEs) |

Dates without a year are in 2026.

Key dates for a timeline slide:
- 2025-05: Gemini API tuning gone.
- 2025-09-29: LoRA Without Regret.
- 2025-11-21: Anthropic reward-hacking misalignment paper.
- 2025-12-03: Bedrock RFT.
- 2026-01-04: R1 v2.
- 2026-03-31: Gemma 4.
- 2026-05-07: OpenAI FT closed to new organizations.
- 2026-06-01: HELM enters maintenance mode.
- 2026-07-27: Digital Omnibus in force.
- 2026-10-15: TRL 1.16.
- 2026-10-23: ft-o4-mini snapshot shut down.
- 2027-01-06: last OpenAI FT jobs.
- 2027-12-02: AI Act Annex III obligations apply.

---

## 3. Gap research: topics missing for a complete course

### 3.1 First principles: data-centric AI and scaling laws (no file covers these)
- **Chinchilla**: "Training Compute-Optimal Large Language Models" (Hoffmann et al., arXiv 2203.15556, 2022). Model size and tokens "should be scaled equally: for every doubling of model size the number of training tokens should also be doubled." https://arxiv.org/abs/2203.15556
- **Data-constrained scaling**: "Scaling Data-Constrained Language Models" (Muennighoff et al., arXiv 2305.16264, NeurIPS 2023). "Training with up to 4 epochs of repeated data yields negligible changes to loss compared to having unique data." This is the theory behind the over-filtering trade-off in 06 (FineWeb-Edu and DCLM discard ~90%; Nemotron-CC rephrases). https://arxiv.org/abs/2305.16264
- **Survey**: "Data-centric Artificial Intelligence: A Survey" (Zha et al., arXiv 2303.10158). Three goals: *training data development, inference data development, data maintenance*. Resource list: https://github.com/daochenzha/data-centric-AI
- **Course**: MIT "Introduction to Data-Centric AI" (dcai.csail.mit.edu) [UNVERIFIED this session; URL from memory].

### 3.2 Data mixing (the "select" stage at corpus level, missing from 04 and 06)
- **DoReMi** (Xie et al., arXiv 2305.10429). A 280M proxy is trained with Group DRO to set domain weights for an 8B model. It gives "+6.5% points" average few-shot accuracy and "reaches the baseline accuracy with 2.6x fewer training steps". https://arxiv.org/abs/2305.10429
- **RegMix** (arXiv 2407.01492). It trains 512 models of 1M parameters on 1B tokens each, fits a regression, and transfers the result to 1B/25B. It matches or exceeds DoReMi "using just 10% of the computational resources". Counter-intuitive finding: "Web corpora rather than data perceived as high-quality like Wikipedia have the strongest positive correlation with downstream performance." https://github.com/sail-sg/regmix

### 3.3 SFT data selection (missing classic results)
- **AlpaGasus** (arXiv 2307.08701). An LLM filter keeps **9k of Alpaca's 52k** examples. The result "significantly outperforms" Alpaca and trains 5.7x faster (80 to 14 min).
- **Deita** (arXiv 2312.15685, "What Makes Good Data for Alignment?"). Selection on complexity × quality × diversity. With **6K SFT** samples it is on par with SOTA ("over 10x less"). Adding 10K DPO samples gives 7.55 MT-Bench.
- **SemDeDup** (arXiv 2303.09540). Embedding-cluster dedup "can remove 50% of the data with minimal performance loss".
- **"Textbooks Are All You Need"** (phi-1, arXiv 2306.11644). This is the origin of synthetic-first training and the ancestor of Phi-4 in 08.
- Story line for the deck: LIMA (1K) -> AlpaGasus (9K/52K) -> Deita (6K) -> LESS (5%). Selection beats size, consistently, from 2023 to 2025.

### 3.4 Multimodal data-centric benchmark (absent)
- **DataComp** (arXiv 2304.14108). Fixed CLIP training code with a 12.8B-pair pool; competitors design only the *filter*. DataComp-1B reaches **79.2% zero-shot ImageNet** with ViT-L/14, which is **+3.7 pp over OpenAI CLIP** at the same compute. It is the image-text twin of DCLM. https://www.datacomp.ai

### 3.5 RAG beyond the basic pipeline (01 §3 is thin)
- **GraphRAG** (Edge et al., arXiv 2404.16130). Plain RAG "fails on global questions... 'What are the main themes in the dataset?'". GraphRAG builds an entity graph plus community summaries.
- **RAPTOR** (arXiv 2401.18059). Recursive embed -> cluster -> summarize tree, then retrieval across levels of abstraction.
- **RAG eval survey** (arXiv 2405.07437) for retrieval-vs-generation metrics.
- **Retriever fine-tuning is a customization lever of its own.** With sentence-transformers **6.2.0** (v6 moved losses to `sentence_transformers.sentence_transformer.losses`, confirmed in the docs import lines):
```python
# Adapted from https://sbert.net/docs/sentence_transformer/training_overview.html (v6 docs)
from datasets import load_dataset
from sentence_transformers import (SentenceTransformer, SentenceTransformerTrainer,
                                   SentenceTransformerTrainingArguments)
from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss

model = SentenceTransformer("microsoft/mpnet-base")
train = load_dataset("sentence-transformers/all-nli", "triplet", split="train[:10000]")
loss = MultipleNegativesRankingLoss(model)          # in-batch negatives
args = SentenceTransformerTrainingArguments(output_dir="mpnet-nli",
                                            num_train_epochs=1, per_device_train_batch_size=16)
SentenceTransformerTrainer(model=model, args=args, train_dataset=train, loss=loss).train()
```
Teaching point: for domain RAG, (query, positive passage) pairs, which can be synthetic per 06 §7, plus hard negatives often beat swapping the LLM.

### 3.6 Privacy, PII and memorization (only a stub in 08 §5.6)
- **Presidio** (now github.com/data-privacy-stack/presidio; PyPI 2.2.364). Standard analyzer -> anonymizer pattern [adapted from the README/docs API; the code was not re-quoted this session]:
```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
text = "Call Jane Doe at 212-555-0199"
results = AnalyzerEngine().analyze(text=text, language="en")
print(AnonymizerEngine().anonymize(text=text, analyzer_results=results).text)
# -> "Call <PERSON> at <PHONE_NUMBER>"
```
- **DP fine-tuning**: Opacus 1.6.0 (`PrivacyEngine().make_private(...)`) [API recalled, UNVERIFIED this session]. Google's VaultGemma (1B, released 13 Sep 2025 per the Gemma releases page) is an open differentially private LLM and makes a good real-world example.
- **Extraction**: Nasr, Carlini et al., arXiv 2311.17035 (cited in 08; not re-fetched).
- Lee et al. 2022 (05): dedup cuts memorized emission 10x. Present dedup as a privacy control, not only a quality one.

### 3.7 Regulatory documentation for training data (missing from the quality-card section)
- The EU **GPAI "public summary of training content" template** (Commission, July 2025, implementing AI Act Art. 53(1)(d)) should be shown next to Datasheets and Data Cards as the *mandatory* quality card for GPAI providers. The digital-strategy.ec.europa.eu page returned 403, so details are [UNVERIFIED this session]. GPAI obligations have applied since 2 Aug 2025, with AI Office enforcement powers from 2 Aug 2026 (secondary sources, see C16).

### 3.8 Managed RL is now on all three hyperscalers (correction to the 01 narrative)
- Vertex RFT (Preview, Gemini 3.5 Flash / 3.1 Flash-Lite; function, LLM or custom rewards).
- Bedrock RFT (Nova 2 Lite, Lambda or judge rewards).
- Exits: OpenAI RFT and Fireworks managed RFT.
- **New slide line:** "Closed-model RFT moved to the hyperscalers; open-model RL moved to training APIs (Tinker, Fireworks Training API) and OSS (TRL / verl / OpenRLHF)."

### 3.9 Still missing, to research next pass (search quota exhausted)
- Agent and tool-use datasets: APIGen / xLAM, ToolACE, SWE-Gym / SWE-smith.
- RL environment hubs: OpenEnv, Prime Intellect Environments Hub. The HF `rl-environment` tag in 04 is a hook.
- Multi-LoRA serving in vLLM 0.32 (`--enable-lora`).
- Long-context vs RAG (Anthropic's 200K rule of thumb is from 2024; it needs a 2026 refresh).
- Gemini 3.x context-caching economics.
- The Google ADK `adk eval` format. 07 has it as [UNVERIFIED].

---

## 4. Quotable lines added in this pass (verified)
- "for every doubling of model size the number of training tokens should also be doubled" (Chinchilla abstract)
- "training with up to 4 epochs of repeated data yields negligible changes to loss" (Muennighoff et al.)
- RAG "fails on global questions directed at an entire text corpus" (GraphRAG abstract)
- "Managed Training no longer accepts new RFT jobs; existing jobs keep running" (Fireworks docs)
- "If `0.0` (default), the reference model is not loaded, reducing memory usage and improving training speed." (TRL GRPOConfig `beta`)
- "Quality data is the foundation of successful fine-tuning." (Google codelab, Fine-tune Gemini on Gemini Enterprise Agent Platform)

---

## 5. Recommended 60-slide narrative arc (first principles -> state of the art)

Throughline: **the dataset is the spec**. Every customization method is a different way of turning data into behavior. Lifecycle spine: design -> generate -> select -> curate -> label -> denoise -> quality card.

**I. First principles (1-6)**
1. Title: "Customizing Modern AI: the data is the program", Oct 2026 snapshot.
2. What a model "knows" vs how it "behaves": the OpenAI 2-axis frame (context vs LLM optimization).
3. Next-token loss in one equation; SFT, DPO and RL as three ways to shape the same distribution.
4. Scaling laws: Chinchilla (tokens ∝ params) and data-constrained (4 epochs ≈ free). Data is the binding constraint.
5. Data-centric AI defined (Zha et al.): training data, inference data, data maintenance.
6. The lifecycle wheel (7 stages) used as the deck's navigation map.

**II. The customization decision map (7-12)**
7. The ladder: prompt/context -> long context -> RAG -> SFT -> DPO -> RL (cost, data, latency bars).
8. Context engineering (Anthropic): attention budget, compaction, just-in-time retrieval.
9. Knowledge goes to RAG, behavior goes to tuning (Ovadia; Gekhman: new facts via FT raise hallucination).
10. The Icelandic lesson: 62 / 70 / 78 / 87 / 83 BLEU, where RAG hurt a behavioral task.
11. Decision flowchart: gold outputs -> SFT; pairs -> DPO; grader -> RFT.
12. Market shake-out timeline (OpenAI and Fireworks exit; Vertex RFT Preview and Bedrock RFT arrive). Corrected per C1.

**III. SFT and PEFT (13-19)**
13. SFT mechanics: chat templates, EOS, loss masking (`assistant_only_loss`, `-100`).
14. LoRA in one picture, plus the family tree (QLoRA, DoRA, rsLoRA, PiSSA) and their `LoraConfig` flags.
15. LoRA Without Regret: all-layer LoRA, 10x LR, rank 1 enough for RL. Harmonized LR line (C27).
16. Packing and efficiency (BFD, padding-free), plus the float32-by-default gotcha (C13).
17. Forgetting frontier and merging (TIES/DARE/SLERP, mergekit 0.1.5).
18. Distillation: off-policy vs on-policy (TRL `DistillationTrainer`, beta slider from forward KL to reverse KL).
19. Lab: Gemma 4 E2B QLoRA plus the Cloud Run codelab, and the API-drift trap (C21).

**IV. Preference optimization and RL (20-28)**
20. RLHF with PPO (InstructGPT 1.3B > 175B): four models in memory.
21. DPO in one line, and the preference zoo (IPO, KTO, ORPO, SimPO; stable vs `trl.experimental`, C11).
22. RLVR and GRPO: group baseline, no critic; the R1-Zero curve from 15.6% to 77.9% (v2).
23. Fixing GRPO: DAPO (50 vs 47 AIME), Dr. GRPO length bias, GSPO for MoE; TRL defaults `dapo`, β=0.
24. Where rewards come from: verifier -> rubric (RaR, up to 31%) -> judge -> RM, ordered by hackability.
25. Reward hacking grows up: Gao overoptimization, CoT obfuscation, Anthropic 12% sabotage, inoculation prompting.
26. Does RL add reasoning? pass@k crossover (2504.13837) and spurious rewards (+21.4 vs +29.1).
27. Agentic multi-turn RL: async rollouts, masked tool tokens; verl 0.9.1, OpenRLHF 0.11.2, AsyncGRPO.
28. In production: Cursor Tab online RL (-21% suggestions, +28% accept) plus managed RFT receipts, watermarked "vendor-reported".

**V. RAG as a data product (29-34)**
29. RAG pipeline anatomy: parse, chunk, embed, hybrid search, rerank, cite.
30. Contextual Retrieval: failure rate 5.7% -> 3.7% -> 2.9% -> 1.9%.
31. Fine-tune the retriever, not the LLM (sentence-transformers 6.2, MNRL with hard negatives).
32. Beyond chunks: GraphRAG (global questions), RAPTOR (tree summaries), agentic RAG loop.
33. RAG + FT together: RAFT distractor training; Balaguer +6 then +5 pp.
34. Managed RAG: Vertex RAG Engine and the Vertex AI Search codelab (C28).

**VI. Design (35-38)**
35. Taxonomy-first design (GLAN, InsTag): coverage heatmap and leaf quotas.
36. Slices, declared vs discovered (Slice Finder, Domino 36%), with a slice-gate YAML.
37. Data contracts: schema + semantics + SLA (Pandera 0.34.1, GX 1.24.1, Soda 4, dbt, ODCS 3.1).
38. Drift: PSI / KS / JS / embedding drift (Evidently 0.7.23 defaults table).

**VII. Generate, select, curate (39-45)**
39. Web curation funnel: FineWeb-Edu (LLM judge -> tiny classifier) and DCLM top-10%.
40. The dedup paradox (per-snapshot beats global) and the token-budget trade-off (Nemotron-CC rephrasing; 4-epoch law).
41. Data mixing: DoReMi (2.6x fewer steps) and RegMix ("web > Wikipedia").
42. Four ways to make instructions: Self-Instruct, Evol, Magpie, Personas (Tulu 3 ~939K mix).
43. Generate -> verify -> keep: Llama 3 rejection sampling K=10-30, 20% of code self-corrected.
44. Selection beats size: LIMA 1K, AlpaGasus 9K/52K, Deita 6K, LESS 5%.
45. Model collapse (Shumailov, Nature 2024) vs accumulate-and-anchor (Gerstgrasser); the best teacher is not the best model (QwQ-32B).

**VIII. Label, denoise, leakage (46-51)**
46. Agreement before scale: κ, Fleiss, Krippendorff α ≥ 0.8; the kappa paradox.
47. LLM as annotator, trust but verify: Gilardi ($0.003, 4/5 tasks), JUDGE-BENCH caveat, routing.
48. Confident learning: 6% of ImageNet val is wrong (≥3.3% average); cleanlab 2.9 Datalab.
49. Data maps and active learning (cartography; BADGE / core-set); weak supervision with Snorkel (note its CVEs).
50. Leakage gallery: group, time, preprocessing; GroupKFold / TimeSeriesSplit; MinHash cross-split dedup.
51. Contamination and privacy: GSM1k (up to 8%), Min-K%; PII scrubbing with Presidio; DP (VaultGemma).

**IX. Evaluation and the quality card (52-56)**
52. Error analysis first: 100 traces, open to axial coding, binary evals (Husain/Shankar).
53. Error bars: CIs, clustered SEs, paired bootstrap (Miller 2024).
54. LLM-as-judge done right: bias table, TPR/TNR, Rogan-Gladen correction; calibration/ECE and cost thresholds.
55. Eval tooling map: Inspect 0.3.283, lm-eval 0.4.13, DeepEval 4.3.1, promptfoo, Vertex Gen AI eval; HELM in maintenance.
56. The Quality Card: Datasheet + Data Card + Croissant-RAI (mlcroissant 1.1.1) + eval report + EU GPAI training-content summary.

**X. State of the art and open challenges (57-60)**
57. The 2026 post-training assembly line: Tulu 3, OLMo 3 (Dolma 3 -> Dolci, OlmoTrace), SmolLM3 APO + merge, Qwen3, Gemma 4.
58. Legal and provenance: Data Provenance Initiative (70%+ license omission), Bartz v. Anthropic $1.5B, EU Omnibus dates.
59. Open challenges board: graders as the new labels, verification gap, synthetic provenance, tooling decay (Argilla, distilabel, whylogs, HELM), platform risk.
60. Closing: "Portable assets are data + grader + eval, not checkpoints", with a reading list.

---

## 6. Slide ideas (from this critic pass)
1. **"What changed this month"**: a timeline ribbon (C1, C7, C16, C17) with "sunset" and "new" stamps. It animates left to right and ends on today's ft-o4-mini shutdown.
2. **"Hyperscalers in, startups out"**: a 3x3 provider grid (SFT / DPO / RFT) for Vertex, Bedrock, OpenAI, Fireworks and Tinker. Cells flip from green to red to amber to show the 2026 state.
3. **"4 epochs is free"**: the Muennighoff loss curve with repetition, overlaid on the FineWeb-Edu and DCLM "keep 10%" funnels. A slider trades quality filtering against repetition.
4. **"Selection beats size"**: a log-scale bar race of LIMA 1K, Deita 6K, AlpaGasus 9K, the LESS 5% subset, and the full sets.
5. **"Mix like a scientist"**: a DoReMi proxy-to-target diagram. Domain weight bars morph, with the RegMix callout "web > Wikipedia".
6. **"API drift is a bug"**: the codelab's `SFTTrainer(max_seq_length=..., tokenizer=...)` next to the TRL 1.16 `SFTConfig` signature. A red TypeError animates in. Tagline: pin versions.
7. **"Fine-tune the retriever"**: an embedding-space animation where query and positive pull together and in-batch negatives push apart (MNRL). Recall@k ticks up.
8. **"Is it verified?"**: an audit stamp board of the deck's numbers. Each claim gets a source chip showing arXiv version or doc date (R1 v2 77.9, RaR 31%, GSM1k v4 8%), as a model of citation hygiene for students.
9. **"The mandatory quality card"**: the Datasheet / Data Card / Croissant / EU GPAI-template layers, with arrows to Art. 10 and Art. 53 duties.

---

## 7. Sources used in this pass
- OpenAI deprecations: https://developers.openai.com/api/docs/deprecations
- Vertex RFT: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/reinforcement-tuning
- Vertex SFT: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/supervised-tuning
- Fireworks RFT: https://docs.fireworks.ai/fine-tuning/reinforcement-fine-tuning-models
- TRL GRPO / SFT / KTO / Distillation docs: https://huggingface.co/docs/trl/main/en/ ; releases: https://github.com/huggingface/trl/releases
- Gemma releases: https://ai.google.dev/gemma/docs/releases
- Codelabs: https://codelabs.developers.google.com/codelabs/cloud-run/how-to-fine-tune-model-cloud-run-jobs ; https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/9-ai-finetuning/finetune-gemini-vertex-ai ; https://codelabs.developers.google.com/build-google-quality-rag
- READMEs: argilla-io/argilla, stanford-crfm/helm, unslothai/unsloth, verl-project/verl, data-privacy-stack/presidio
- sentence-transformers training overview: https://sbert.net/docs/sentence_transformer/training_overview.html
- Anthropic: https://www.anthropic.com/research/emergent-misalignment-reward-hacking
- The Register on DeepSeek cost: https://www.theregister.com/2025/09/19/deepseek_cost_train/
- arXiv: 2501.12948, 2507.17746, 2405.00332, 2103.14749, 2203.15556, 2305.16264, 2303.10158, 2305.10429, 2407.01492, 2307.08701, 2312.15685, 2303.09540, 2306.11644, 2304.14108, 2404.16130, 2401.18059, 2405.07437, 2506.10947, 2504.13837, 2411.15124
- PyPI JSON API (versions, Snorkel vulnerabilities): https://pypi.org/pypi/<package>/json
