# Customizing modern AI: SFT, RL, RAG and data-centric AI

Deck key: `custom`. 60 slides in 10 chapters. Flow: decide the lever -> mechanisms (SFT, RL, RAG) -> data (design, labels and leakage, synthetic) -> evaluation -> full lifecycle in production and open challenges. Research current to 2026-10-23.

## Chapter summary

- **00 Opening** (2 slides, tone `model`)
- **01 Choose the right customization lever** (5 slides, tone `agent`)
- **02 Supervised fine-tuning** (7 slides, tone `model`)
- **03 Reinforcement learning for LLMs** (8 slides, tone `model`)
- **04 Retrieval-augmented generation** (6 slides, tone `agent`)
- **05 Dataset design, contracts, coverage and drift** (6 slides, tone `state`)
- **06 Labels, noise, active learning and leakage** (7 slides, tone `human`)
- **07 LLM datasets and synthetic data with verification** (7 slides, tone `state`)
- **08 AI eval design** (6 slides, tone `tool`)
- **09 The full lifecycle in production and open challenges** (6 slides, tone `risk`)


## Chapter 00: Opening

Tone: `model`

Research files:
- C:/Users/evija/googleadk2.0/research-custom/01-customization-map.md
- C:/Users/evija/googleadk2.0/research-custom/08-sota-examples-challenges.md
- C:/Users/evija/googleadk2.0/research-custom/06-llm-rag-datasets-synthetic.md

### 1. The base model is shared; your data, graders and retrieval make it yours

- File: `c00-01-hero.html`
- Id: `custom-c00-hero`

**Content.** Opening slide. .display deck title 'Customizing modern AI: SFT, RL, RAG and data-centric AI'. One .lede: 'Every team rents the same foundation models. The difference is the data you train on, the reward you optimize and the knowledge you retrieve.' Three levers as tags: weights (SFT, DPO, RL: t-model), context (RAG, context engineering: t-agent), data (design -> generate -> select -> curate -> label -> denoise -> quality card: t-state). Three proof stats that count up at the end (.stat): InstructGPT 1.3B outputs preferred to 175B GPT-3 outputs (arXiv 2203.02155); Cursor Tab online RL: 28% higher accept rate with 21% fewer suggestions (cursor.com/blog/tab-rl, 2025-09-12); Anthropic Contextual Retrieval + reranking: 67% fewer retrieval failures (anthropic.com/news/contextual-retrieval). Notes: frame the course as engineering decisions with numbers; no hype words.

**Visual and animation.** Self-animating hero diagram (bespoke gsap loop, killed in leave()). Centre: a coral node 'Foundation model'. Left: a green ring of 7 small state dots labelled design, generate, select, curate, label, denoise, card; a highlight travels round the ring (index-based, deterministic). Two arms leave the centre: up to a coral 'Weights: SFT / DPO / RL' node and down to a blue 'Context: RAG' node; :flow pulses travel from the data ring into both arms. Right: a violet 'Your product' pill receives pulses from both arms. Build: 0.0s model pops, 0.6s ring draws, 1.2s arms draw, 1.8s pulses start, 2.4s the three .stat counters count up below (1.3B > 175B, +28%, -67%). Loop keeps pulsing; no presenter steps needed (optional step 1 reveals the stats if autoplay is off).

### 2. The course moves from the decision, to the mechanisms, to the data, to evaluation in production

- File: `c00-02-course-map.html`
- Id: `custom-c00-course-map`

**Content.** Map of the course in 4 groups. Decide: 1 Choose the right lever (prompt / context, RAG, SFT, DPO, RL; Oct 2026 managed-tuning shake-out). Mechanisms: 2 Supervised fine-tuning (LoRA, QLoRA, DoRA, TRL, Unsloth, Gemma, Vertex); 3 Reinforcement learning (RLHF/PPO, DPO family, GRPO, RLVR, reward models, RFT, agentic RL); 4 RAG (pipeline, contextual retrieval, Vertex AI RAG Engine, agentic RAG, RAG vs fine-tuning). Data: 5 Dataset design (cards, Croissant, contracts, coverage, slices, drift); 6 Labels and leakage (agreement, LLM annotators, confident learning, active learning, entity/time/group leakage, contamination); 7 LLM datasets and synthetic data (FineWeb-Edu, DCLM, Magpie, generate -> verify -> keep, model collapse, RAG test sets). Prove and ship: 8 Eval design (error analysis, slice metrics with CIs, LLM-as-judge, calibration, cost-sensitive thresholds); 9 Full lifecycle workflow, quality card, 2025-26 recipes, open challenges. Below the map: the data lifecycle strip design -> generate -> select -> curate -> label -> denoise -> quality card, with each stage tagged to its chapter. Each chapter ends with an interview slide (Google, Anthropic, OpenAI, Meta style questions).

**Visual and animation.** Node diagram ~1300x560. Four .group containers: g-agent 'Decide' (node 1), g-model 'Mechanisms' (nodes 2, 3, 4), g-state 'Data' (nodes 5, 6, 7), g-tool 'Prove and ship' (nodes 8, 9). Wires 1>2, 1>3, 1>4 (step 1), 2>5, 3>5, 4>5 dashed 'data feeds all' (step 2), 5>6>7 flow (step 2), 7>8>9 flow (step 3), 9>5 bend60 dashed [drift loop] (step 4). Under the Data group a 7-cell lifecycle strip; step 2 lights the cells left to right with stagger. Step 4 pulses the feedback wire.


## Chapter 01: Choose the right customization lever

Tone: `agent`

Research files:
- C:/Users/evija/googleadk2.0/research-custom/01-customization-map.md
- C:/Users/evija/googleadk2.0/research-custom/08-sota-examples-challenges.md
- C:/Users/evija/googleadk2.0/research-custom/03-rl.md

### 3. Choose the cheapest lever that fixes the failure

- File: `c01-01-chapter.html`
- Id: `custom-c01-chapter`

**Content.** Chapter opener (class chapter). .display 'Choose the cheapest lever that fixes the failure'. .lede: 'Prompt, retrieve, tune or reinforce. Each rung up the ladder costs more data, more money and more platform risk.' Tags: context engineering, RAG, SFT, DPO, RFT / GRPO. One-line thesis quote: 'you use the right optimization tool for the right job' (OpenAI, Optimizing LLM accuracy, developers.openai.com/api/docs/guides/optimizing-llm-accuracy).

**Visual and animation.** A six-rung staircase SVG (data-fx draw) on the right: prompt / context, long context, RAG, SFT, DPO, RL. Rungs draw bottom to top with stagger; a small cost bar beside each rung grows taller per rung (relative, no numbers).

### 4. Knowledge failures go to retrieval; behavior failures go to weights

- File: `c01-02-knowledge-vs-behavior.html`
- Id: `custom-c01-knowledge-vs-behavior`

**Content.** OpenAI two-axis frame: x = context optimization (what the model knows: missing, stale, private facts -> prompting, RAG); y = LLM optimization (how the model behaves: format, tone, style, consistent reasoning -> fine-tuning, preference tuning, RL). Quote: 'RAG only solves our in-context learning issues'. Icelandic grammar-correction case (BLEU): GPT-4 zero-shot 62, 3-shot 70, GPT-3.5 fine-tuned on 1,000 examples 78, GPT-4 fine-tuned on 1,000 examples 87, GPT-4 fine-tuned + RAG 83. RAG lowered the score because the task is behavioral. Evidence: Ovadia et al. 2023 (arXiv 2312.05934) 'RAG consistently outperforms' unsupervised fine-tuning for knowledge injection; Gekhman et al. EMNLP 2024 (arXiv 2405.05904): models learn new-knowledge examples slowly and hallucination rises linearly once they do; Balaguer et al. 2024 (arXiv 2401.08406, agriculture): fine-tuning +6 p.p., RAG adds +5 p.p. on top. .callout.pitfall: 'Do not add retrieval to a style task. In the Icelandic case BLEU fell from 87 to 83.' Interview angle: classify the failure before you pick the tool. Cite .cite.doc OpenAI 'Optimizing LLM accuracy'; .cite.paper the three arXiv papers.

**Visual and animation.** Left: bespoke SVG 2x2 quadrant (Deck.register). Step 1: axes draw with labels 'context optimization ->' and 'LLM optimization ^'. Step 2: chip 'prompt' pops at origin. Step 3: chip 'RAG' slides right (blue). Step 4: chip 'fine-tune' slides up (coral). Step 5: chip 'RAG + FT' slides to the top-right; a dashed arrow path prompt -> RAG -> FT -> both draws. Right: bar chart of BLEU 62, 70, 78, 87, 83 that grows at step 5 with count-up labels; the 83 bar turns red (risk) and the pitfall callout appears.

### 5. Climb the ladder one rung at a time, and let the eval decide each step

- File: `c01-03-ladder-decision.html`
- Id: `custom-c01-ladder-decision`

**Content.** Ladder table (table.t): 1 Prompting / context engineering: 0 to tens of examples + an eval set of 20+ gold cases; hours; wins first. 2 Long context: KB under ~200k tokens (~500 pages, Anthropic) + prompt caching. 3 RAG / agentic RAG: a corpus, no labels; days; +retrieval hop (tens to hundreds of ms). 4 SFT (LoRA / full): 50 to 500 examples to start (OpenAI about 50; Vertex 'at least 100 to 500'); can shrink prompts and allow a smaller model. 5 Preference tuning (DPO): pairs; ~1.1x to 4x the SFT token price (Together). 6 RL / RFT: tens to thousands of prompts + a reward function, no gold outputs; highest cost. Rung 1 detail: context engineering is 'the set of strategies for curating and maintaining the optimal set of tokens' (Anthropic, 2025-09-29); context rot; just-in-time retrieval, compaction, clearing stale tool results, sub-agents. Anthropic has no public fine-tuning API: its customization path is context engineering, prompt caching, Skills and tools. Business framing: +$20 per success, -$40 per escalation, -$1,000 churn in 5% of failures gives a break-even accuracy of 81.5% (OpenAI guide). Decision flow: eval -> prompt -> failure analysis -> KNOWLEDGE (long context, RAG, agentic RAG) or BEHAVIOR (gold outputs -> SFT; comparisons -> DPO; grader -> RFT / GRPO) -> combine (RAFT; SFT then DPO) -> re-evaluate and monitor. Rule: 'LoRA is usually enough' (LoRA Without Regret, thinkingmachines.ai/blog/lora). Cite .cite.doc Anthropic 'Effective context engineering for AI agents'.

**Visual and animation.** Node-graph decision tree (diagram ~1300x600). Step 1: 'Eval set (20+ gold)' -> 'Prompt + context' -> 'Pass? ship' (green pill). Step 2: 'Failure analysis' node (agent) splits with wires [knowledge] and [behavior]. Step 3: knowledge branch: 'KB < 200k tokens -> long context', 'RAG: hybrid + rerank', 'Agentic RAG' (state/agent nodes) with :flow. Step 4: behavior branch: 'gold outputs -> SFT', 'pairs -> DPO', 'grader -> RFT / GRPO' (model nodes). Step 5: both branches merge into 'Combine + re-evaluate' with a bend wire back to the eval node [monitor]. The table sits in a collapsed panel that replaces the tree at step 6 (data-until on tree), rows highlight with data-on.

### 6. In October 2026 managed tuning splits into hyperscaler tuning and do-it-yourself RL APIs

- File: `c01-04-managed-shakeout.html`
- Id: `custom-c01-managed-shakeout`

**Content.** Timeline: May 2025 Gemini API / AI Studio lose tuning (Gemini 1.5 Flash-001 deprecated; tuning only on Vertex). 2025-12-03 Amazon Bedrock RFT launches on Amazon Nova 2 Lite with Lambda (RLVR) or model-as-judge rewards; AWS claims '66% accuracy gains on average' (vendor-reported). 2026-05-07 OpenAI announces fine-tuning wind-down. 2026-07-02 job creation closed to orgs without inference on fine-tuned models. 2026-10-23 (today) ft-o4-mini-2025-04-16, ft-gpt-4.1-nano, ft-gpt-3.5-turbo, ft-gpt-4 and others shut down: OpenAI RFT (o4-mini only) ends. 2027-01-06 existing customers can no longer create jobs. Fireworks: 'Managed Training no longer accepts new RFT jobs' -> Training API with async GRPO and custom rollout functions. Tinker (Thinking Machines): forward_backward / optim_step primitives, LoRA from 1B to 1T+ parameters. Provider matrix (table.t): Vertex AI SFT on Gemini 3.5 Flash-Lite, 3.5 Flash, 3.1 Flash-Lite, 2.5 Pro, 2.5 Flash-Lite, 2.5 Flash + PREFERENCE_TUNING; OpenAI gpt-4.1 family for existing customers only; Anthropic: no first-party fine-tuning; Bedrock: SFT, RFT, distillation; Together: LoRA, full, DPO; Fireworks: Training API. Lesson: 'Portable recipes (data + grader + eval) matter more than checkpoints.' Cite .cite.doc OpenAI deprecations page, Fireworks RFT docs, ai.google.dev/gemini-api/docs/model-tuning, AWS News Blog 'Improve model accuracy with reinforcement fine-tuning in Amazon Bedrock'.

**Visual and animation.** Bespoke SVG timeline (Deck.register): a horizontal line draws left to right (2025 -> 2027). Step 1: May 2025 and Dec 2025 dots pop (Google, AWS). Step 2: the three 2026 OpenAI dots pop in red; step 3: a pulsing 'today 2026-10-23' marker with a sunset tag on o4-mini RFT; step 4: 2027-01-06 dot. Step 5: the timeline shrinks to the top and the provider matrix table fades in; sunset rows get t-risk tags, growth rows get .new tags.

### 7. Interview: choosing a customization lever

- File: `c01-05-qa.html`
- Id: `custom-c01-qa`

**Content.** 4 .qa pairs, each answer on its own step. Q1: 'Your support bot quotes the wrong refund policy and also sounds too formal. What do you change?' A: Two failures. The policy is knowledge: put it in retrieval (fresh, citable, permissioned). The tone is behavior: fix it with prompting, then SFT or DPO on preferred replies. Build a 20+ case eval first. The OpenAI Icelandic case shows RAG can hurt a behavior task (87 -> 83 BLEU). Q2: 'When is long context better than RAG?' A: When the KB is under ~200k tokens and stable; use prompt caching to cut cost; watch context rot; move to RAG when the corpus grows, changes or needs ACLs. Q3: 'Why not fine-tune your product catalogue into the weights?' A: New facts are learned slowly and hallucination rises (Gekhman 2024); facts go stale; retraining cost; tuned weights die with the base model. Q4: 'Your vendor retires the base model you tuned. What survives?' A: The data, the contract, the grader, the eval set and the pinned recipe. OpenAI ft-o4-mini died 2026-10-23; teams with portable recipes re-tune on Vertex, Bedrock or open models.

**Visual and animation.** Standard .qa layout: four questions visible; answers reveal at steps 1-4 with data-fx up; a small tag per answer (knowledge / behavior / cost / platform risk).


## Chapter 02: Supervised fine-tuning

Tone: `model`

Research files:
- C:/Users/evija/googleadk2.0/research-custom/02-sft.md
- C:/Users/evija/googleadk2.0/research-custom/01-customization-map.md
- C:/Users/evija/googleadk2.0/research-custom/08-sota-examples-challenges.md

### 8. Supervised fine-tuning teaches format, style and skills from examples

- File: `c02-01-chapter.html`
- Id: `custom-c02-chapter`

**Content.** Chapter opener. .display 'Supervised fine-tuning teaches format, style and skills from examples'. .lede: 'SFT minimizes the cross-entropy of the target tokens. The data and the mask decide what the model learns.' Tags: LoRA, QLoRA, DoRA, TRL v1.16.0 (2026-10-15), PEFT v0.21.0, Unsloth, Gemma 4, Vertex AI. Quote: fine-tuning is 'the most reliable way to enforce a specific output format' (Google Developers Blog, 'Own your AI', 2025-10-08).

**Visual and animation.** A token strip runs across the slide; assistant tokens light coral one by one (stagger) while user tokens stay grey; a small loss curve SVG draws (data-fx draw) under the strip.

### 9. SFT learns only from unmasked tokens, so the chat template and the mask define the task

- File: `c02-02-objective-masking-packing.html`
- Id: `custom-c02-objective-masking-packing`

**Content.** Objective: L_SFT = -sum_t log p(y_t | y_<t); masked tokens use ignore index -100. TRL v1.16.0 SFTConfig: completion_only_loss=None by default (prompt-completion data -> loss on completion only); assistant_only_loss=True puts loss on assistant turns only and needs {% generation %} / {% endgeneration %} in the chat template (TRL patches known families such as Qwen3; vision datasets since v1.15.0). Chat template = Jinja template that adds role markers and special tokens; SFTTrainer applies it automatically to conversational data. Pitfall: a train/inference template mismatch fails silently. EOS gotcha: for a base model such as Qwen/Qwen2.5-1.5B set eos_token='<|im_end|>', or the model never learns to stop. Packing: packing=True, max_length default 1024, packing_strategy 'bfd' (default, best-fit decreasing), 'bfd_split', 'wrapped'; padding_free=True with FlashAttention so examples do not attend across boundaries. Data quality beats size: LIMA used 1,000 curated examples (arXiv 2305.11206). Dataset formats: messages, or prompt + completion; tool_calls and images columns also work. Cite .cite.doc TRL SFT Trainer (huggingface.co/docs/trl/sft_trainer).

**Visual and animation.** Bespoke gsap token-strip animation (Deck.register). Step 1: a conversation renders as ~36 token boxes coloured by role (system violet, user violet-light, assistant coral). Step 2: system and user tokens fade grey and show '-100'; label 'assistant_only_loss=True'. Step 3: small loss bars rise above assistant tokens only. Step 4: an EOS token box at the end pulses red then green (pitfall callout). Step 5: the strip shrinks; a padded batch (4 rows with grey padding) re-arranges into 2 BFD-packed rows; a padding-share counter drops (computed from the drawn boxes, deterministic).

### 10. LoRA trains a thin low-rank update; its variants change the scale, the init and the precision

- File: `c02-03-lora-family.html`
- Id: `custom-c02-lora-family`

**Content.** LoRA (Hu et al., arXiv 2106.09685): W + (alpha/r)·BA, rank r << d, base frozen. Full FT needs about 16 bytes/param with AdamW mixed precision. QLoRA (arXiv 2305.14314): 4-bit NF4 frozen base + double quantization + paged optimizers; fine-tuned a 65B model on one 48 GB GPU; Guanaco reached 99.3% of ChatGPT on the Vicuna benchmark. DoRA (arXiv 2402.09353, ICML 2024): magnitude + direction; helps at low rank; merge before inference (overhead). rsLoRA (arXiv 2312.03732): alpha/sqrt(r) so high ranks keep learning. PiSSA (arXiv 2404.02948): init A, B from the top-r SVD; converges faster. Other inits in PEFT v0.21.0: olora, eva, corda, loftq, orthogonal. Evidence: 'LoRA Without Regret' (Schulman et al., Thinking Machines, 2025-09-29): LoRA matches full FT on small and medium SFT sets; apply to all layers including MLP / MoE (attention-only underperforms); optimal LR about 10x the full-FT LR; for RL even rank 1 matches full FT; LoRA falls behind when data exceeds adapter capacity (large continued pretraining). Code walk: r/alpha, target_modules='all-linear', use_rslora, use_dora, init_lora_weights. Cite .cite.doc PEFT LoRA guide, .cite.paper the arXiv ids, .cite.doc thinkingmachines.ai/blog/lora.

**Visual and animation.** Left: bespoke SVG — a large grey frozen W matrix; step 1 a thin coral B (d x r) and A (r x d) slide in beside it; a live label 'trainable %' updates as r animates 4 -> 16 -> 64 (computed from d=4096, deterministic). Step 2: the scale label morphs alpha/r -> alpha/sqrt(r) (rsLoRA). Step 3: four branch chips pop: QLoRA (4-bit base), DoRA (magnitude + direction arrows), rsLoRA, PiSSA (SVD init). Right: code-wrap with data-focus bands synced: step 1 lines r/alpha, step 2 use_rslora, step 3 use_dora + init_lora_weights, step 4 target_modules with a .callout.insight 'include MLP layers; LR about 10x full FT'.

**Code.** 02-sft.md section 2: PEFT v0.21.0 LoraConfig(r=16, lora_alpha=32, target_modules='all-linear', lora_dropout=0.05, use_rslora=True, use_dora=False, init_lora_weights='pissa_niter_4', task_type='CAUSAL_LM') + get_peft_model + print_trainable_parameters (source huggingface.co/docs/peft/developer_guides/lora, adapted).

### 11. TRL v1.16 puts QLoRA, packing and assistant-only loss in one SFTConfig

- File: `c02-04-trl-qlora.html`
- Id: `custom-c02-trl-qlora`

**Content.** Code walk of the TRL v1.16.0 SFT recipe on Qwen/Qwen3-0.6B with trl-lib/Capybara: SFTConfig(max_length=2048, packing=True, packing_strategy='bfd', assistant_only_loss=True, learning_rate=1e-4), peft_config=LoraConfig(r=16, lora_alpha=32, target_modules='all-linear'), quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4') ('Combine with peft_config for QLoRA training'). SFTConfig defaults that differ from TrainingArguments: learning_rate=2e-5, gradient_checkpointing=True, bf16=True, logging_steps=10; TRL docs advise about 1e-4 for adapters. Recent releases: v1.13.0 chunked-CE lm_head 1.2-1.7x throughput; v1.15.0 fused LM head + selective activation checkpointing; v1.16.0 pad_to_multiple_of='auto'. New loss: SFTConfig(loss_type='dft') (Dynamic Fine-Tuning, arXiv 2508.05629). .callout.pitfall API drift: the Google codelab 'How to fine tune a LLM using Cloud Run Jobs' still passes dataset_text_field=, max_seq_length=, tokenizer=, packing= to SFTTrainer (pre-1.0 style). In TRL 1.x they go in SFTConfig (max_length), and the tokenizer is processing_class=. Pin versions. CLI: 'trl sft ...'. Cite .cite.doc TRL SFT Trainer, .cite.repo github.com/huggingface/trl/releases, .cite.codelab 'How to fine tune a LLM using Cloud Run Jobs' (codelabs.developers.google.com/codelabs/cloud-run/how-to-fine-tune-model-cloud-run-jobs).

**Visual and animation.** Code walk-through: full-height code-wrap (left 60%) with data-focus bands. Step 1 focus SFTConfig packing lines -> right panel 'BFD packing, padding-free'. Step 2 focus assistant_only_loss -> panel shows the masked token strip mini-icon. Step 3 focus peft_config + quantization_config -> panel 'QLoRA = 4-bit NF4 base + LoRA'. Step 4 focus learning_rate -> panel 'adapters: ~1e-4; SFTConfig default 2e-5'. Step 5: pitfall callout slides in with old vs new argument names in a two-column mini table.

**Code.** 02-sft.md section 4: 'SFT with QLoRA, assistant-only loss and packing (TRL v1.16.0)' — SFTConfig + SFTTrainer(model='Qwen/Qwen3-0.6B', train_dataset=load_dataset('trl-lib/Capybara', split='train'), peft_config=LoraConfig(...), quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4')); trainer.train().

### 12. On Google, tune Gemma with open tooling or tune Gemini with managed Vertex AI

- File: `c02-05-google-paths.html`
- Id: `custom-c02-google-paths`

**Content.** Gemma lane: 'Fine-Tune Gemma using Hugging Face Transformers and QloRA' (ai.google.dev/gemma/docs/core/huggingface_text_finetune_qlora) now defaults to google/gemma-4-E2B (options E4B, 12B, 31B, 26B-A4B); dataset philschmid/gretel-synthetic-text-to-sql (synthetic); LoRA r=16, alpha=16, dropout 0.05, modules_to_save lm_head + embed_tokens (special tokens), 3 epochs, LR 2e-4, constant schedule, adamw_torch_fused. Codelab 'How to fine tune a LLM using Cloud Run Jobs': google/gemma-3-1b-it on KomeijiForce/Text2Emoji on one L4 GPU in a Cloud Run job, LoRA r=8 alpha=16 on q_proj/v_proj, then serve with vLLM on Cloud Run. Blog + Colab 'Own your AI: Learn how to fine-tune Gemma 3 270M and run it on-device' (2025-10-08): QLoRA on a free T4 'in minutes', 4-bit model under 300 MB, LiteRT / MediaPipe or Transformers.js with WebGPU. Unsloth: README '2x faster with 70% less VRAM'; guidance rank 16 or 32, alpha = r or 2r, LR 2e-4, 1-3 epochs; train_on_responses_only with Gemma markers '<start_of_turn>user' / '<start_of_turn>model'; Kaggle notebook 'gemma4-31b-unsloth'. Gemini lane: Vertex AI supervised tuning for Gemini 3.5 Flash-Lite, 3.5 Flash, 3.1 Flash-Lite, 2.5 Pro, 2.5 Flash-Lite, 2.5 Flash; JSONL in Cloud Storage; 'at least 100 to 500 examples'; epoch_count, adapter_size, learning_rate_multiplier (default 1); first job with defaults; turn thinking off or use the minimum budget for tuned tasks. Gemini API / AI Studio: no tuning. Note: Gemma docs now point to gemma.ai; the Keras LoRA tutorial is marked deprecated. Cites: .cite.codelab, .cite.doc Gemma QLoRA page, .cite.video/.cite.doc Own your AI blog + Colab (colab.research.google.com/github/google-gemini/gemma-cookbook/.../Fine_tune_Gemma_3_270M_for_emoji_generation.ipynb), .cite.repo kaggle.com/code/danielhanchen/gemma4-31b-unsloth, .cite.doc Vertex 'gemini-use-supervised-tuning', .cite.doc googleapis.github.io/python-genai.

**Visual and animation.** Two-lane node diagram (top 45%). Gemma lane (state/model/tool nodes): 'Colab / Kaggle' -> 'QLoRA (TRL or Unsloth)' -> 'merge + 4-bit' -> split to 'Cloud Run + vLLM' and 'on-device LiteRT / WebGPU'. Gemini lane: 'JSONL in GCS' -> 'client.tunings.tune' -> 'tuned endpoint'. Step 1 Gemma lane wires draw with :flow; step 2 Gemini lane draws; step 3 the code-wrap rises below with focus on tune(...); step 4 focus moves to the polling loop and generate_content; step 5 a .callout.tip 'Gemini API and AI Studio have no tuning; use Vertex'.

**Code.** 01-customization-map.md section 2.1: Google Gen AI SDK Vertex tuning — genai.Client(http_options=HttpOptions(api_version='v1')), types.TuningDataset(gcs_uri=...), client.tunings.tune(base_model='gemini-3.5-flash', training_dataset=..., config=types.CreateTuningJobConfig(tuned_model_display_name='support-tone-v1', epoch_count=1)), polling on JOB_STATE_*, client.models.generate_content(model=tuning_job.tuned_model.endpoint, ...). Leave out the commented method='PREFERENCE_TUNING' line (its placement is unverified).

### 13. Limit forgetting with adapters, merging and on-policy distillation

- File: `c02-06-forgetting-merging-distillation.html`
- Id: `custom-c02-forgetting-merging-distillation`

**Content.** Causes of catastrophic forgetting: distribution shift, high LR, too many epochs, narrow data, template mismatch, safety-refusal drift. Mitigations, cheapest first: PEFT (keep the adapter separate and hot-swappable); lower LR, 1-3 epochs, early stopping on held-out general benchmarks; training loss below 0.2 usually means overfitting (Unsloth); scale an over-fit adapter by alpha x 0.5 (Unsloth); merge back toward the base. Merging: task arithmetic tau = theta_ft - theta_base (arXiv 2212.04089); TIES (arXiv 2306.01708): trim redundant parameters, elect the sign, average the agreeing values; DARE (arXiv 2311.03099): drop a fraction p of deltas and rescale by 1/(1-p), often dare_ties; SLERP merges two models along the arc. mergekit (LGPL-3.0) has 18+ methods, CLI 'mergekit-yaml config.yml ./out'. PEFT add_weighted_adapter(..., combination_type='dare_ties', density=0.2). Real example: SmolLM3 linear merge 0.9 APO soup + 0.1 mid-train checkpoint to recover long-context RULER scores. .callout.pitfall: special tokens added at the same embedding index collide when you merge fully fine-tuned models. Distillation: SFT on teacher outputs (DeepSeek-R1-Distill Qwen/Llama students); on-policy distillation / GKD (arXiv 2306.13649): the student writes, the teacher scores every token, which removes the train/inference mismatch. TRL DistillationTrainer stable since v1.10.0 (2026-08-13): beta 0.0 = forward KL, 1.0 = reverse KL (default), 0.5 = JSD; teacher and student must share a vocabulary; tool-result tokens masked. Cite .cite.doc PEFT model merging guide, .cite.repo github.com/arcee-ai/mergekit, .cite.doc TRL Distillation Trainer.

**Visual and animation.** Bespoke SVG (Deck.register). Step 1: scatter axes 'target-task accuracy ->' and 'general accuracy ^'; a base point. Step 2: a full-FT path animates far right and down (risk colour); a LoRA path animates right with a smaller drop (model colour). Step 3: a merge arrow pulls the full-FT point up-left toward the frontier (illustrative, no numbers). Step 4: the plot shrinks; TIES in three panels: three task-vector arrow sets -> trim (short bars fade) -> sign election (minority-sign bars turn grey) -> average (one merged bar set). Step 5: distillation strip: off-policy (student copies teacher text) vs on-policy (student writes, teacher grades each token), with a beta slider that moves 0 -> 0.5 -> 1 labelled forward KL / JSD / reverse KL.

### 14. Interview: supervised fine-tuning

- File: `c02-07-qa.html`
- Id: `custom-c02-qa`

**Content.** Q1: 'After SFT the model never stops generating. Why?' A: The EOS token or the chat template is wrong. The model never saw the stop token in the loss. Set eos_token (for example '<|im_end|>' on a Qwen2.5 base), use the same template in training and serving, and check the mask. Q2: 'LoRA or full fine-tuning for 20k support conversations?' A: LoRA on all linear layers, LR about 10x the full-FT LR (LoRA Without Regret). Full FT only when the data exceeds adapter capacity, such as large continued pretraining. Q3: 'How do you measure and limit forgetting?' A: Track held-out general benchmarks next to the target metric each epoch; stop early; keep adapters separate; mix general data; merge toward the base (TIES / DARE / linear, as in SmolLM3). Q4: 'Explain where QLoRA saves memory.' A: The base is frozen in 4-bit NF4 with double quantization; only small LoRA matrices train; paged optimizers absorb spikes. QLoRA fine-tuned a 65B model on one 48 GB GPU, against about 16 bytes/param for full FT with AdamW.

**Visual and animation.** Standard .qa layout, answers revealed at steps 1-4; a tiny icon per answer (EOS token, rank slider, frontier arrow, 4-bit block).


## Chapter 03: Reinforcement learning for LLMs

Tone: `model`

Research files:
- C:/Users/evija/googleadk2.0/research-custom/03-rl.md
- C:/Users/evija/googleadk2.0/research-custom/01-customization-map.md
- C:/Users/evija/googleadk2.0/research-custom/08-sota-examples-challenges.md

### 15. Reinforcement learning optimizes the policy against a reward, not against gold answers

- File: `c03-01-chapter.html`
- Id: `custom-c03-chapter`

**Content.** Chapter opener. .display. .lede: 'Three eras: RLHF with PPO (2022-23), direct preference optimization (2023-24), verifiable rewards with GRPO-family algorithms (2024-26). The 2026 frontier is agentic, multi-turn, tool-using RL with async rollouts.' Tags: PPO, DPO, GRPO, DAPO, RLVR, RFT, agentic RL. The shared loop: prompts -> policy samples K completions -> reward (RM / verifier / rubric judge) -> advantage (critic in PPO, group-normalized in GRPO) -> clipped policy-gradient update (+ optional KL to reference) -> repeat.

**Visual and animation.** Circular loop diagram that draws itself: five nodes around a circle (prompts, policy, reward, advantage, update) with :flow pulses circulating; era labels 2022 / 2023 / 2025 fade in under the loop with stagger.

### 16. RLHF with PPO keeps four models in memory, and generation takes most of the time

- File: `c03-02-rlhf-ppo.html`
- Id: `custom-c03-rlhf-ppo`

**Content.** InstructGPT (Ouyang et al., arXiv 2203.02155): 'outputs from the 1.3B parameter InstructGPT model are preferred to outputs from the 175B GPT-3'. Three steps: 1 SFT on demonstrations; 2 reward model trained on human rankings with the Bradley-Terry loss -log sigma(r(x,y_w) - r(x,y_l)); 3 PPO against the RM with a per-token KL penalty to the SFT model; PPO-ptx mixes pretraining gradients to reduce the alignment tax. Cost: four models live at once: policy, reference, reward, critic (value). OpenRLHF README: generation takes about 80% of RLHF time, which is why vLLM rollouts matter. Overoptimization: Gao, Schulman, Hilton (arXiv 2210.10760): as KL from the initial policy grows, the proxy RM score keeps rising while the gold score peaks and then falls (Goodhart). Reward models are the main surface for reward hacking. Cite .cite.paper InstructGPT, Gao et al., .cite.repo github.com/OpenRLHF/OpenRLHF.

**Visual and animation.** Node diagram. Step 1: 'Demonstrations' (human) -> 'SFT policy' (model). Step 2: 'Human rankings' (human) -> 'Reward model' (model) with label [Bradley-Terry]. Step 3: PPO loop group (g-model 'PPO'): 'Policy' -> 'Rollouts (vLLM)' (tool) :flow -> 'Reward model' -> 'Critic' -> back to 'Policy' [advantage]; 'Reference' dashed to Policy [KL]. Step 4: a memory bar shows 4 model blocks stacking; a '~80% generation' bar fills (count-up). Step 5: diagram dims; inline SVG draws the Gao curves: proxy score rising steadily, gold score rising then falling vs KL; a red marker at the gold peak labelled 'stop here'.

### 17. DPO turns preference learning into a classification loss on chosen and rejected pairs

- File: `c03-03-dpo-family.html`
- Id: `custom-c03-dpo-family`

**Content.** DPO (arXiv 2305.18290): L = -E[log sigma(beta(log pi(y+|x)/pi_ref(y+|x) - log pi(y-|x)/pi_ref(y-|x)))]; it 'eliminat[es] the need for sampling from the LM during fine-tuning'. TRL DPOConfig: beta default 0.1, learning_rate default 1e-6, max_length 1024; loss_type is a list (default ['sigmoid']), options include hinge, ipo, robust, bco_pair, apo_zero, apo_down, discopop, sft, sigmoid_norm (SimPO-style length normalization); MPO = ['sigmoid','bco_pair','sft'] with weights [0.8, 0.2, 1.0]; ref_model=None uses the initial policy; sync_ref_model=True = TR-DPO; label_smoothing = Robust DPO. Teaching point: DPO works 'by suppressing the likelihood of dispreferred completions rather than by increasing the likelihood of preferred ones', so logps/chosen can fall. Zoo (table.t): IPO (2310.12036) ref yes, pairs, resists overfitting on deterministic preferences; KTO (2402.01306) ref yes, unpaired thumbs up/down; ORPO (2403.07691) no ref, SFT + odds-ratio in one stage; SimPO (2405.14734) no ref, length-normalized reward + margin gamma. Managed: Vertex preference tuning, beta range 0.01 to 0.5, recommended recipe SFT on preferred responses first, then preference-tune. Cite .cite.doc TRL DPO Trainer, .cite.doc Vertex gemini-use-preference-tuning, .cite.paper DPO.

**Visual and animation.** Step 1: the DPO loss renders large; the chosen log-ratio term highlights green, step 2 the rejected term highlights red, step 3 beta pulses with label 'KL strength'. Step 4: equation shrinks to the top-left; a 2x2 zoo grid (axes: needs a reference model yes/no x paired/unpaired data) and chips DPO, IPO, KTO, ORPO, SimPO pop into cells. Step 5: code-wrap on the right with data-focus on DPOConfig loss_type/loss_weights, then on peft_config. Step 6: .callout.insight about logps/chosen falling.

**Code.** 03-rl.md section 3: 'DPO + LoRA + multi-loss' — DPOConfig(beta=0.1, learning_rate=1e-5, loss_type=['sigmoid','bco_pair','sft'], loss_weights=[0.8,0.2,1.0]); DPOTrainer('Qwen/Qwen3-0.6B', args=args, train_dataset=load_dataset('trl-lib/ultrafeedback_binarized', split='train'), peft_config=LoraConfig()); trainer.train().

### 18. GRPO drops the critic and scores each answer against its own group

- File: `c03-04-grpo-r1.html`
- Id: `custom-c03-grpo-r1`

**Content.** GRPO (DeepSeekMath, arXiv 2402.03300): sample a group of G outputs per prompt (TRL default num_generations=8); advantage A_i = (r_i - mean(r)) / std(r); PPO-style clipped ratio + optional KL; no value model, which cuts memory roughly in half against PPO. DeepSeek-R1 (arXiv 2501.12948; Nature 645, 633-638, 2025): R1-Zero = pure RL on the base model; AIME 2024 pass@1 rises 15.6% -> 77.9%, and 86.7% with self-consistency (v2 numbers). Rule-based rewards: accuracy (answer check, compiler tests), format (think tags), language consistency. Why no neural RM: they 'are susceptible to reward hacking during large-scale RL'. 'Aha moment' quote: 'Wait, wait. Wait. That's an aha moment I can flag here.' R1 pipeline: cold-start long-CoT SFT -> reasoning RL -> rejection sampling + SFT on about 800K samples -> second RL with rule rewards + helpfulness/harmlessness RMs -> distillation into Qwen/Llama students. Cost: about US$294K for the RL stage on 648 H800 GPUs, excluding the base model (Nature supplementary; The Register argues the true cost is far higher). Cite .cite.paper DeepSeekMath, DeepSeek-R1.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: one prompt node fans out into 8 completion cards. Step 2: a verifier stamp marks each card 1 or 0 (fixed pattern 1,0,0,1,1,0,0,0). Step 3: reward bars rise; a mean line draws at 0.375; advantages appear as up arrows (green) on correct cards and down arrows (red) on wrong cards, height = (r - mean)/std. Step 4: a crossed-out 'critic' node fades (no value model). Step 5: the group shrinks left; a line chart draws AIME pass@1 from 15.6 to 77.9 over RL steps (count-up end label), a dashed 86.7 line for self-consistency, and the 'aha moment' quote pops mid-curve.

### 19. DAPO and Dr. GRPO fix entropy collapse and length bias, and TRL ships them as defaults

- File: `c03-05-grpo-fixes.html`
- Id: `custom-c03-grpo-fixes`

**Content.** DAPO (arXiv 2503.14476, ByteDance Seed + Tsinghua AIR, built on verl): 50 points on AIME 2024 with Qwen2.5-32B base vs 47 for DeepSeek-R1-Zero-Qwen-32B with 50% of the training steps. Four techniques: Clip-Higher (eps_low 0.2, eps_high 0.28; 'avoids entropy collapse'); dynamic sampling (drop prompts with group accuracy 0 or 1: zero advantage, zero gradient); token-level policy-gradient loss; overlong reward shaping (max 16,384 tokens + 4,096 cache). Dr. GRPO (arXiv 2503.20783): GRPO 'artificially increases response length', especially for wrong answers; fix = constant normalization, no std term; 43.3% AIME 2024 with a 7B base. GSPO (arXiv 2507.18071, Qwen): sequence-level ratios and clipping; stabilizes MoE RL; used for Qwen3. TRL v1.16.0 GRPO defaults: loss_type='dapo' (alternatives 'dr_grpo', 'sapo', 'cispo', 'vespo'); beta=0.0 (no KL, no reference model); num_generations=8; scale_rewards='group' ('batch' or False; False = Dr. GRPO); use_vllm=True with vllm_mode 'colocate' or 'server'. Unsloth practice: reward often starts rising after about 300 steps; use 500+ rows and a model of at least 1.5B. Reward functions receive completions + dataset columns as kwargs and return list[float]. Cite .cite.doc TRL GRPO Trainer, .cite.doc Unsloth RL guide (unsloth.ai/docs/basics/reinforcement-learning-rl-guide), .cite.paper DAPO, Dr. GRPO, GSPO.

**Visual and animation.** Step 1-4: four cards flip one per step (Clip-Higher with an asymmetric clip band sketch; dynamic sampling with all-0 and all-1 groups crossed out; token-level loss; overlong shaping with a soft penalty ramp). Step 5: a fifth card 'Dr. GRPO: length bias' with a response-length curve that stops climbing; stat '50 vs 47 AIME at half the steps' counts up. Step 6: cards collapse to a strip; code-wrap appears with data-focus on correct_answer(), then format_reward(), then GRPOConfig(loss_type='dr_grpo', scale_rewards=False, beta=0.0).

**Code.** 03-rl.md section 5: 'a custom verifiable reward plus config' — correct_answer(completions, ground_truth, **kwargs) extracting a boxed answer with re, format_reward(...) giving 0.2 for '<think>', GRPOConfig(loss_type='dr_grpo', scale_rewards=False, num_generations=8, beta=0.0, use_vllm=True), GRPOTrainer(model='Qwen/Qwen2.5-0.5B-Instruct', reward_funcs=[correct_answer, format_reward], ...). Mark it 'adapted from the TRL reward-function pattern'.

### 20. Rewards range from human preference to programs, and checkable rewards are the hardest to hack

- File: `c03-06-reward-sources.html`
- Id: `custom-c03-reward-sources`

**Content.** Spectrum: human labels -> reward model (Bradley-Terry) -> LLM judge (RLAIF) -> rubric -> verifier. RLVR named in Tulu 3 (arXiv 2411.15124): 'a novel method we call Reinforcement Learning with Verifiable Rewards'. Verifiers: math answer match (math-verify), unit tests / sandbox, JSON schema / regex, IFEval-style constraint checks, SQL result match. RLAIF: Constitutional AI (arXiv 2212.08073) critique-revise + AI preference labels; Lee et al. (arXiv 2309.00267) AI labels comparable to human labels on summarization and dialogue. ORM vs PRM: 'Let's Verify Step by Step' (arXiv 2305.20050): process supervision solves 78% of a MATH subset; PRM800K = 800,000 step labels; in 2025-26 PRMs are mostly used for test-time reranking; DeepSeek-R1 did not train with PRMs. Rubrics as Rewards (arXiv 2507.17746, Scale AI): per-prompt checklist graded by a judge; up to 28% relative gain on HealthBench-1k vs Likert. Graders as products: OpenAI RFT graders string_check, text_similarity, score_model, python, multi (for example 0.5 * compliant + 0.5 * explanation), now a design pattern because the platform is winding down; Bedrock RFT rewards in AWS Lambda or model-as-judge. Hacks to know: length inflation, sycophancy to an RM, editing unit tests or sys.exit(0), regex format gaming, judge prompt injection. Fireworks advice: test the grader on full, partial, zero, malformed and edge-case answers before training. .callout.pitfall 'Graders are the new labels: red-team them like a dataset.'

**Visual and animation.** Bespoke SVG spectrum (Deck.register). Step 1: a horizontal axis draws with five nodes (human, RM, judge, rubric, verifier) popping left to right. Step 2: two shaded bands animate above it: 'cost per label' falls left -> right, 'hackability' falls left -> right (qualitative). Step 3: an ORM vs PRM inset: a 5-step reasoning chain where the ORM scores only the end, the PRM scores each step (ticks appear one by one). Step 4: a grader 'multi' box shows weighted sub-graders summing to one score. Step 5: hack icons (length, sycophancy, test edit, regex, injection) pop in red with the pitfall callout.

### 21. Production RL runs as online loops and multi-turn agent training on rented training APIs

- File: `c03-07-rft-agentic-production.html`
- Id: `custom-c03-rft-agentic-production`

**Content.** Cursor Tab online RL (cursor.com/blog/tab-rl, 2025-09-12): policy gradient on live accept/reject signals; >400M Tab requests per day; a new checkpoint ships and collects data in about 1.5-2 h; 21% fewer suggestions and 28% higher accept rate; 'we learn a policy that targets a particular accept rate'. Managed RFT results (vendor-reported, OpenAI RFT use cases): Ambience Healthcare ICD-10 coding 0.39 -> 0.57; Harvey legal citation F1 0.563 -> 0.6765; SafetyKit F1 86% -> 90%. Fireworks RFT: Genspark Deep Research +10% quality vs a SOTA closed model, +33% tool calls, ~50% cost cut. Agentic RL: rollouts are trajectories (model -> tool call -> environment observation -> model ...), reward at episode end (tests pass); problems: long-tail rollout latency -> async training, mask tool-output tokens from the loss, train/inference log-prob mismatch, sandboxing. Tooling: TRL AsyncGRPO (v1.14 LoRA + async tools; v1.15 OpenEnv harness; v1.16 tree attention, up to about 3x on shared-prompt rollouts); verl (HybridFlow, arXiv 2409.19256; ReTool recipe; uni-agent May 2026; Megatron MoE for DeepSeek-671B and Qwen3-235B; Mind Lab GRPO LoRA on a 1T model on 64 H800s); OpenRLHF v0.10 (AgentInstanceBase reset()/step(), --train.async_enable, multi-turn VLM RL). Rented APIs: Fireworks Training API (async GRPO, custom rollouts, sandboxes), Tinker (forward_backward, optim_step). Cite .cite.repo verl, OpenRLHF, trl; .cite.doc OpenAI RFT use cases; .cite.doc Fireworks RFT blog.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: Cursor loop diagram (deploy -> users accept/reject -> reward -> policy update -> deploy) with a clock label '~1.5-2 h'; counters count up -21% suggestions and +28% accept rate. Step 2: the loop moves left; an agent trajectory strip animates: LLM token block -> tool call (amber) -> sandbox (tool group) -> observation block shown hatched 'masked from loss' -> LLM ... -> reward badge. Step 3: three async rollout-worker lanes run at different speeds beside one trainer node; finished trajectories drop into a buffer. Step 4: the terminal code-wrap appears with focus on the agent / async flags. Step 5: a .tag t-risk 'vendor-reported' stamp over the RFT results row.

**Code.** 03-rl.md section 11: OpenRLHF CLI as .code-wrap.term — 'ray job submit ... -- python3 -m openrlhf.cli.train_ppo_ray --actor.model_name_or_path OpenRLHF/Llama-3-8b-sft-mixture --reward.model_name_or_path OpenRLHF/Llama-3-8b-rm-700k --algo.advantage.estimator reinforce_baseline --vllm.num_engines 4 --vllm.tensor_parallel_size 2 --train.colocate_all --ds.zero_stage 3 --ds.param_dtype bf16'; mention --train.agent_func_path and --train.async_enable in the side panel.

### 22. Interview: reinforcement learning for LLMs

- File: `c03-08-qa.html`
- Id: `custom-c03-qa`

**Content.** Q1: 'Why does GRPO not need a critic, and what does that cost?' A: The group mean and std of G sampled answers act as the baseline. You save the value model (about half the memory of PPO) but you generate G completions per prompt, and groups with all-0 or all-1 rewards give no gradient (DAPO dynamic sampling drops them). Q2: 'Reward goes up but human-rated quality goes down. What happened?' A: Overoptimization or reward hacking (Gao et al.). Read samples, look for length inflation or test edits, add hidden tests, stop at the gold peak, use KL or early stopping, rotate judges. Q3: 'DPO chosen log-probs fall during training. Is it a bug?' A: Not necessarily. DPO mostly suppresses rejected completions (TRL docs). Watch rewards/margins and an eval, and consider an SFT term (MPO) to anchor chosen responses. Q4: 'You have 2,000 prompts and a unit-test harness. Which method?' A: RLVR with GRPO-family loss (TRL default dapo, beta 0, dynamic sampling), sandboxed execution, decontaminated eval, start from an SFT checkpoint of at least 1.5B; expect reward to rise only after about 300 steps.

**Visual and animation.** Standard .qa layout with answers at steps 1-4.


## Chapter 04: Retrieval-augmented generation

Tone: `agent`

Research files:
- C:/Users/evija/googleadk2.0/research-custom/01-customization-map.md
- C:/Users/evija/googleadk2.0/research-custom/06-llm-rag-datasets-synthetic.md
- C:/Users/evija/googleadk2.0/research-custom/08-sota-examples-challenges.md

### 23. RAG gives the model fresh, private and citable knowledge at run time

- File: `c04-01-chapter.html`
- Id: `custom-c04-chapter`

**Content.** Chapter opener. .display. .lede: 'Retrieval changes the tokens in the window, not the weights. It wins when knowledge is large, changing, permissioned or needs citations.' Tags: hybrid search, contextual retrieval, reranking, Vertex AI RAG Engine, agentic RAG, RAFT. Remind: if the knowledge base is 'smaller than 200,000 tokens', Anthropic suggests putting it all in the prompt with caching.

**Visual and animation.** A document icon splits into chunk blocks (gsap stagger), the chunks fly into a green index cylinder, and a query arrow pulls three chunks out to a model node.

### 24. Hybrid search, contextual chunks and reranking cut retrieval failures by two thirds

- File: `c04-02-pipeline-contextual.html`
- Id: `custom-c04-pipeline-contextual`

**Content.** Pipeline: ingest (parse PDF / HTML / tables) -> chunk (for example 512 tokens, 100 overlap) -> enrich (a contextual header per chunk) -> embed + BM25 index -> query rewrite / expansion -> hybrid retrieve top-k (20-150) -> rerank to top-n (3-20) -> pack context with citations -> generate -> grounding / citation check -> eval (recall@k, faithfulness, answer correctness). Anthropic Contextual Retrieval (2024-09-19): baseline top-20 retrieval failure 5.7%; contextual embeddings 3.7% (-35%); + contextual BM25 2.9% (-49%); + reranking 1.9% (-67%). Why it works: a chunk such as 'revenue grew 3%' loses its company and quarter; the contextual header puts them back before embedding and BM25. Real examples: Vertex AI RAG Engine defaults (chunk_size 512, overlap 100). .callout.pitfall: 'Tune chunking with retrieval recall on a labeled set, not by eye.' Cite .cite.doc anthropic.com/news/contextual-retrieval.

**Visual and animation.** Node diagram ~1300x420 in one row with a state group 'Index' around 'Embeddings' and 'BM25'. Steps: 1 ingest -> chunk (a bespoke mini-animation shows a page splitting into 512-token blocks with an overlap band); 2 enrich -> both index nodes with :flow; 3 query -> rewrite -> hybrid retrieve (two wires from both indexes); 4 rerank -> generate -> 'cite + check'. A vertical bar at the right shows the failure rate shrinking 5.7% -> 3.7% -> 2.9% -> 1.9% as steps 2, 3, 4 light up (count-down number).

### 25. Vertex AI RAG Engine manages the corpus, chunking and retrieval behind one client

- File: `c04-03-vertex-rag-engine.html`
- Id: `custom-c04-vertex-rag-engine`

**Content.** October 2026 quickstart uses the new agentplatform client: client.rag.create_corpus(display_name=...); client.rag.import_files(corpus.name, paths=['gs://...'], transformation_config=RagFileTransformationConfig(chunking_config=RagFileChunkingConfig(chunk_size=512, chunk_overlap=100))); client.rag.retrieve_contexts(rag_resources=[corpus.name], rag_retrieval_config=RagRetrievalConfig(top_k=3, vector_distance_threshold=0.5), text='What is the refund window?'). Grounded generation: genai_types.Tool(retrieval=Retrieval(vertex_rag_store=VertexRagStore(...))) passed to Gemini generate_content. The old vertexai.preview.rag / rag.retrieval_query names no longer appear in the quickstart. Docs now move under the 'Gemini Enterprise Agent Platform' name. Notebook: GoogleCloudPlatform/generative-ai intro_rag_engine.ipynb. .callout.pitfall 'Pin the SDK version; the RAG API names changed in 2026. Check kwarg names against the live quickstart.' Cite .cite.doc Vertex AI RAG Engine quickstart (docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-quickstart), .cite.repo GoogleCloudPlatform/generative-ai.

**Visual and animation.** Code walk-through (left) synced with a small node diagram (right): 'GCS files' -> 'RAG corpus' (state group with chunk blocks) -> 'retrieve_contexts' -> 'Gemini + Retrieval tool' -> 'grounded answer'. Step 1 focus create_corpus, corpus node pops; step 2 focus import_files + chunking config, chunks fill the corpus; step 3 focus retrieve_contexts, three chunks highlight; step 4 focus on the grounding Tool line, the answer node shows a citation tag; step 5 pitfall callout.

**Code.** 01-customization-map.md section 3.1: Vertex RAG Engine sketch with agentplatform.Client(project=PROJECT, location='us-central1'), client.rag.create_corpus, client.rag.import_files(... RagFileChunkingConfig(chunk_size=512, chunk_overlap=100)), client.rag.retrieve_contexts(... RagRetrievalConfig(top_k=3), text=...). Label it 'adapted from the quickstart; check exact kwarg names'.

### 26. Agentic RAG plans, retrieves and reflects in a loop, and pays for recall with more LLM calls

- File: `c04-04-agentic-rag.html`
- Id: `custom-c04-agentic-rag`

**Content.** Survey: 'Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG' (Singh et al., arXiv 2501.09136, v4 April 2026): patterns 'reflection, planning, tool use, and multi-agent collaboration'. Loop: plan sub-questions -> choose a tool (vector search, SQL, web, API) -> retrieve -> read and reflect ('enough evidence?') -> re-query or answer -> cite. Trade-off: higher recall on multi-hop questions at the cost of 2 to 10x more LLM calls and latency. Link to context engineering (Anthropic): just-in-time retrieval keeps file paths and queries and loads data with tools; compaction and sub-agents with clean windows return condensed summaries. RL and agentic RAG converge: Genspark's RFT-trained Deep Research agent made 33% more tool calls with +10% quality vs a SOTA closed model (Fireworks) — RL teaches when and how to retrieve. Use it when questions are multi-hop or ambiguous; keep a one-shot pipeline for single-hop lookups with tight latency budgets.

**Visual and animation.** Side-by-side (.vs). Left: a linear one-shot pipeline (query -> retrieve -> generate) draws at step 1. Right (bespoke gsap): a circular loop with nodes plan, choose tool, retrieve, reflect, answer; at step 2 a token travels plan -> tool; step 3 the tool node fans to four amber options (vector, SQL, web, API) and one lights; step 4 reflect shows 'enough evidence? no' and the token loops again; step 5 'yes' -> answer with citations. An 'LLM calls' counter increments on each hop (1, 2, 3 ... 6) against the left pipeline's '1'.

### 27. Choose RAG for changing facts, fine-tuning for fixed behavior, and RAFT when you need both

- File: `c04-05-rag-vs-ft.html`
- Id: `custom-c04-rag-vs-ft`

**Content.** RAG wins: knowledge changes often, the corpus is large, answers need citations or audit trails, per-user ACLs matter, long-tail facts (Ovadia 2023; Gekhman 2024). Fine-tuning wins: format and style consistency, latency and cost (distil into a small model, shorter prompts), narrow classification or extraction, a fixed task spec (OpenAI Icelandic: adding RAG dropped 87 -> 83 BLEU). Both: Balaguer et al. 2024 (+6 p.p. FT, then +5 p.p. RAG); RAFT (Zhang et al., arXiv 2403.10131) fine-tunes with distractor documents so the model learns to ignore irrelevant chunks and cite the relevant one; gains on PubMed, HotpotQA and Gorilla. Alternative: long context + prompt caching under ~200k tokens. Cost view: RAG adds a retrieval hop (tens to hundreds of ms) and agentic RAG adds LLM turns; FT adds training and hosting cost and a deprecation risk. Decision table (table.t) with rows: freshness, corpus size, citations / ACL, output format, latency budget, data available (corpus vs examples vs grader).

**Visual and animation.** A balance-scale SVG (bespoke): left pan 'RAG', right pan 'fine-tune'. Steps 1-6 add one criterion each as a weight chip that drops on a pan (freshness -> RAG, citations/ACL -> RAG, format/style -> FT, latency/cost -> FT, both -> a centre chip 'RAFT'); the beam tilts accordingly (deterministic angles). The decision table fills row by row in sync on the right.

### 28. Interview: retrieval-augmented generation

- File: `c04-06-qa.html`
- Id: `custom-c04-qa`

**Content.** Q1: 'Retrieval recall@20 is high, but answers are still wrong. Where do you look?' A: Context packing and order, reranking to a small top-n, faithfulness checks, conflicting chunks, and the generator's use of evidence; consider RAFT-style training with distractors. Q2: 'How do you evaluate a RAG system?' A: Separate retrieval (recall@k on labeled question-chunk pairs) from generation (faithfulness, answer correctness). Build the set from real queries plus a synthetic test set, verify it (closed-book leak test, humans check 5-10%), and report per slice. Q3: 'When does agentic RAG not pay off?' A: For single-hop lookups with tight latency budgets: it costs 2-10x more LLM calls. Use it for multi-hop or ambiguous questions. Q4: 'How do you choose chunk size?' A: Start at about 512 tokens with 100 overlap, add contextual headers, then tune on retrieval recall; hybrid BM25 + embeddings + reranking cut failures 67% in Anthropic's test.

**Visual and animation.** Standard .qa layout with answers at steps 1-4.


## Chapter 05: Dataset design, contracts, coverage and drift

Tone: `state`

Research files:
- C:/Users/evija/googleadk2.0/research-custom/04-dataset-design-contracts.md
- C:/Users/evija/googleadk2.0/research-custom/07-eval-design.md
- C:/Users/evija/googleadk2.0/research-custom/06-llm-rag-datasets-synthetic.md

### 29. The dataset is the spec: design it before you generate it

- File: `c05-01-chapter.html`
- Id: `custom-c05-chapter`

**Content.** Chapter opener. .display. .lede: 'The model learns what the data covers. Gaps in coverage become gaps in capability, and missing provenance becomes legal risk.' The lifecycle strip design -> generate -> select -> curate -> label -> denoise -> quality card with DESIGN lit. Tags: Data Cards, Croissant 1.1, ODCS v3.1.0, Pandera 0.34.1, Great Expectations 1.24.1, Evidently 0.7.23.

**Visual and animation.** The 7-cell lifecycle strip draws; the DESIGN cell glows and the others dim; a blueprint grid fades in behind the title.

### 30. Document a dataset three ways: a card for people, Croissant for machines, a contract for CI

- File: `c05-02-docs-standards.html`
- Id: `custom-c05-docs-standards`

**Content.** Human-readable: Datasheets for Datasets (Gebru et al., arXiv 1803.09010; CACM 2021): 'every component, no matter how simple or complex, is accompanied with a datasheet'; sections motivation, composition, collection process, preprocessing / cleaning / labeling, uses, distribution, maintenance. Google Data Cards (Pushkarna et al., FAccT 2022, arXiv 2204.01075; 20+ deployed cards) and the Data Cards Playbook (Ask, Inspect, Answer, Audit; 15 themes; 40+ Data and Model Cards at Google). Hugging Face dataset cards: README.md + YAML front matter (license, language, task_categories, tags); 2026 adds an rl-environment tag (harbor, verifiers, openenv). Machine-readable: MLCommons Croissant (arXiv 2403.19546) JSON-LD on schema.org; Croissant 1.1 adds machine-actionable provenance and usage policies; Croissant-RAI (arXiv 2407.16883); exported by Hugging Face, Kaggle, OpenML; indexed by Google Dataset Search. Executable: contracts (next slide). Why: Data Provenance Initiative (arXiv 2310.16787) audited 1,800+ text datasets: license omission 70%+, error rates 50%+. EU AI Act Article 10: training, validation and testing data must be 'relevant, sufficiently representative, and to the best extent possible, free of errors and complete', with documented design choices, origin, preparation and bias examination (do not quote application dates without checking EUR-Lex). Optional tiny code: mlcroissant mlc.Dataset('https://huggingface.co/api/datasets/fashion_mnist/croissant').

**Visual and animation.** Three stacked layers that animate in as a pyramid: step 1 'Card' (violet reader icon: people), step 2 'Croissant JSON-LD' (amber icon: machines), step 3 'Contract' (green icon: CI). Step 4: a horizontal timeline draws 2018 Datasheets -> 2019 Model Cards -> 2022 Data Cards -> 2024 Croissant -> 2026 Croissant 1.1 / RL-environment cards. Step 5: two stats count up (1,800+ datasets audited; 70%+ license omission) with the EU AI Act quote.

### 31. A data contract makes schema, semantics and SLAs executable in CI

- File: `c05-03-data-contracts.html`
- Id: `custom-c05-data-contracts`

**Content.** Definition: an agreement between producer and consumers, versioned in git, enforced in CI and production: 1 schema (fields, types, nullability, keys); 2 semantics (allowed values, ranges, formats, units, meaning: 'amount is gross EUR incl. VAT'); 3 SLAs / quality (freshness, completeness, volume, uniqueness, owner); 4 change policy (breaking-change detection). For ML / LLM data the consumer is the training or eval pipeline; contracts catch a silent label-schema change, a new language, empty response fields from a synthetic generator, a stale RAG corpus. Tool matrix (table.t): Pandera 0.34.1 (in-code DataFrame validation; use 'import pandera.pandas as pa'); Great Expectations 1.24.1 (expectation classes with severity, checkpoints); Soda Core 4 (YAML contract, 'soda contract verify'); dbt model contracts (enforced: true; breaking-change detection on removed columns, type changes, constraints); ODCS v3.1.0 + datacontract-cli (lint, test, export, breaking v1 v2: executable SLAs). Code walk: Pandera SFTRow class with str_length, isin, ge/le and Config.strict, validated lazily.

**Visual and animation.** Split screen. Left: code-wrap with data-focus bands that light in sequence: step 1 the field types (schema), step 2 isin / ge / le (semantics), step 3 strict + lazy=True (quality gate). Right: a CI pipeline node diagram: 'synthetic generator' -> 'contract test' -> 'train'; at step 4 a red 'response empty' record hits the contract node, the wire to train turns dashed red [blocked]; step 5 a 'datacontract breaking v1 v2' badge shows a removed column failing the build; the tool matrix appears as a compact table under the pipeline.

**Code.** 04-dataset-design-contracts.md section 3.3: Pandera 0.34.1 — import pandera.pandas as pa; class SFTRow(pa.DataFrameModel): prompt: str = pa.Field(str_length={'min_value': 1}); response ...; lang: str = pa.Field(isin=['en','de','fr']); quality: float = pa.Field(ge=0.0, le=1.0); class Config: strict = True; SFTRow.validate(df, lazy=True).

### 32. Measure coverage against a taxonomy, and turn every gap into a named slice

- File: `c05-04-coverage-slices.html`
- Id: `custom-c05-coverage-slices`

**Content.** Taxonomy = domain x task x skill x difficulty x language x format x risk category. Metrics: leaf coverage = |leaves with >= k examples| / |leaves| (k = 30-100 for the eval split); balance = normalized Shannon entropy H(p)/log N, Gini, max/min ratio; effective number of categories = exp(H); embedding coverage = share of production clusters with training mass; nearest-neighbour distance from production queries flags holes; instruction diversity (InsTag tags, distinct n-grams, self-BLEU, semantic dedup ratio). Evidence: #InsTag (arXiv 2308.07074): 6.6K open-set tags; TagLM trained on 6K InsTag-selected samples beats models trained on far larger SFT sets on MT-Bench. GLAN (arXiv 2402.13064): the only input is a taxonomy of human knowledge (fields -> disciplines -> subjects -> syllabus -> key concepts -> instructions); add a skill by inserting a node. Slices: named, reproducible predicates (lang == 'de' AND prompt_tokens > 2000 AND domain == 'billing'), each with a metric, min n and an owner. Sources: declared (taxonomy, sensitive attributes, risk register); discovered: Slice Finder (ICDE 2019, arXiv 1807.06068), Domino (ICLR 2022, arXiv 2203.14960): 1,235 slice settings, finds 36% (+12 pp), names 35% exactly; production-driven (cluster failing traffic). Slice spec YAML: slice, predicate, min_eval_n: 200, metric, gate 'task_success >= overall - 0.03', owner.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: a taxonomy tree unfolds from a root (3 levels, ~12 leaves). Step 2: leaves rotate into a leaf x split heatmap (train / dev / test columns), cells fill green by count (fixed values). Step 3: empty or thin cells pulse red as 'holes'; a leaf-coverage counter shows e.g. 9/12 (computed from the drawn grid) and the entropy formula appears. Step 4: one red hole turns into a slice YAML card that slides in on the right. Step 5: a Domino callout: '36% of 1,235 planted slices found'.

### 33. Drift tests compare today's data with a reference, and the right statistic depends on type and sample size

- File: `c05-05-drift.html`
- Id: `custom-c05-drift`

**Content.** Statistics: PSI = sum (a_i - e_i) ln(a_i / e_i) over 10 quantile bins; industry convention < 0.1 stable, 0.1-0.25 moderate, > 0.25 major (Evidently default threshold 0.1). KS: D = sup |F_ref(x) - F_cur(x)|; at large n tiny shifts become 'significant'. Jensen-Shannon distance (symmetric, bounded; Evidently threshold 0.1). Wasserstein normalized by the reference std (0.1). Evidently 0.7.23 defaults: numerical n <= 1000 ks (p < 0.05), n > 1000 wasserstein; categorical chisquare / jensenshannon; text: domain classifier (ROC AUC 0.55). Dataset drift when the drifted-column share >= drift_share (default 0.5). Embedding drift (legacy API): model (AUC 0.55), ratio (0.2), distance (0.2), mmd. LLM / RAG: track descriptors (length, language, toxicity, taxonomy leaf, retrieval-hit rate, refusal rate) and apply PSI / JS to them; embedding drift between the RAG corpus and live queries reveals uncovered topics. Train/serve skew (SFT data vs production prompts) vs temporal drift (week N vs N-1). whylogs 1.6.4 mergeable profiles; WhyLabs' hosted platform was discontinued and open-sourced, so keep profiles in open formats. Cite .cite.doc Evidently 'Customize data drift', .cite.repo pypi evidently.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: reference histogram (green) and current histogram (amber) draw on shared axes; the current one shifts right (fixed shift). Step 2: PSI bins highlight and a PSI counter counts to the computed value. Step 3: histograms morph into two CDF curves; the maximum vertical gap draws as a red line labelled 'KS D'. Step 4: an Evidently defaults table (n <= 1000 vs > 1000) fades in. Step 5: code-wrap with focus on DataDriftPreset(method='psi', drift_share=0.7) and ValueDrift(..., method='ks').

**Code.** 04-dataset-design-contracts.md section 6.2: Evidently 0.7.23 — from evidently import Report; from evidently.presets import DataDriftPreset; from evidently.metrics import ValueDrift; report = Report([DataDriftPreset(method='psi', drift_share=0.7), ValueDrift(column='sepal length (cm)', method='ks')], include_tests=True); my_eval = report.run(iris.iloc[:60], iris.iloc[60:]); my_eval.save_html('drift.html').

### 34. Interview: dataset design and drift

- File: `c05-06-qa.html`
- Id: `custom-c05-qa`

**Content.** Q1: 'The team says: we have 50k SFT rows, ready to train. What do you ask?' A: Which taxonomy leaves they cover and with how many examples each; provenance and license per subset; synthetic share and generator; the contract that validates each shard; the slices and min n of the eval split; decontamination against eval sets. Q2: 'Your KS test flags drift on every column every day.' A: At large n, p-values flag tiny shifts. Use distance measures with thresholds (Wasserstein, JS, PSI), monitor descriptors that matter, and tie alerts to slice metrics. Q3: 'How do you find failing slices you did not think of?' A: Cluster failing production traffic and embeddings; use Slice Finder or Domino-style discovery; promote recurring clusters to declared slices with an owner and a gate. Q4: 'What does EU AI Act Article 10 ask of training data?' A: Governance of design choices, data origin, preparation steps such as labeling and cleaning, assumptions, and bias examination; data must be relevant, sufficiently representative and as error-free and complete as possible. A Data Card maps onto these items.

**Visual and animation.** Standard .qa layout with answers at steps 1-4.


## Chapter 06: Labels, noise, active learning and leakage

Tone: `human`

Research files:
- C:/Users/evija/googleadk2.0/research-custom/05-labels-noise-active.md
- C:/Users/evija/googleadk2.0/research-custom/07-eval-design.md
- C:/Users/evija/googleadk2.0/research-custom/06-llm-rag-datasets-synthetic.md

### 35. Labels are measurements: check their agreement, their noise and their splits

- File: `c06-01-chapter.html`
- Id: `custom-c06-chapter`

**Content.** Chapter opener. .display. .lede: 'Test sets contain errors, annotators disagree, and leaked splits inflate scores. Measure each one before you trust a number.' Lifecycle strip with LABEL and DENOISE lit. Tags: Krippendorff alpha, LLM-as-annotator, cleanlab 2.9.0, BADGE, GroupKFold, MinHash LSH, GSM1k. Stat teaser: ImageNet validation has 2,916 label errors, about 6% (Northcutt et al. 2021).

**Visual and animation.** A grid of 24 label tiles; three tiles flip to show a wrong label in red (deterministic indices); the '6%' stat counts up.

### 36. Measure agreement before you scale labeling, and accept an LLM only when it agrees like a human

- File: `c06-02-agreement.html`
- Id: `custom-c06-agreement`

**Content.** Cohen's kappa (2 raters): kappa = (p_o - p_e) / (1 - p_e); weighted (quadratic) kappa for ordinal scales. Fleiss' kappa for a fixed number of raters per item. Krippendorff's alpha = 1 - D_o / D_e: any number of raters, missing ratings, nominal to ratio levels; the default for crowd and LLM + human panels. Landis and Koch bands (0.41-0.60 moderate, 0.61-0.80 substantial, 0.81+ almost perfect) are widely cited but arbitrary. Kappa paradox: with skewed classes kappa can be low while raw agreement is high, so report both. Annotation loop: guidelines -> pilot 50-200 items with 3+ raters -> alpha per label -> adjudicate -> revise -> repeat until alpha >= 0.8 -> scale with 5-10% overlap items. Low agreement can be signal (subjective tasks): keep soft or per-annotator labels. LLM as annotator: Gilardi et al. (PNAS 2023, 2,382 tweets): zero-shot ChatGPT beat MTurk on 4 of 5 tasks at under $0.003 per annotation, 'about twenty times cheaper'; Zheng et al. 2023: GPT-4 judge 'over 80% agreement' with humans; JUDGE-BENCH (ACL 2025, 11 LLMs, 20 datasets): reliability 'varies substantially'; 'LLMs should be carefully validated against human judgments'. Hybrid recipe: humans label a 200-500 item gold set; compare LLM-human alpha with human-human alpha; swap order, fixed label set, temperature 0, several judges; route low-confidence items to humans; run cleanlab on merged labels; re-audit 2-5% of LLM labels weekly. Tools: Argilla 2.8.0 and Label Studio 1.23.2 show LLM pre-annotations as suggestions.

**Visual and animation.** Step 1: two bars p_o and p_e animate and the kappa formula fills in with their values (from the code example). Step 2: a Krippendorff panel shows a raters x items grid with grey missing cells. Step 3: code-wrap appears with focus moving Cohen -> Fleiss -> Krippendorff. Step 4: a routing diagram: 'LLM labeler' (model) -> 'confidence gate' (agent) -> 'accept' (state) or 'human review' (human) with :flow; 'cleanlab audit' node after the merge. Step 5: stats count up: 4/5 tasks, $0.003, >80%.

**Code.** 05-labels-noise-active.md section 2: cohen_kappa_score(a, b) and weights='quadratic'; statsmodels aggregate_raters + fleiss_kappa(table, method='fleiss'); krippendorff.alpha(reliability_data=rel, level_of_measurement='nominal') with np.nan for missing ratings.

### 37. Confident learning finds label errors from out-of-sample probabilities

- File: `c06-03-confident-learning.html`
- Id: `custom-c06-confident-learning`

**Content.** Why: 'Pervasive Label Errors in Test Sets Destabilize Machine Learning Benchmarks' (Northcutt, Athalye, Mueller, NeurIPS 2021 D&B, arXiv 2103.14749): at least 3.3% errors on average across 10 test sets; ImageNet val 2,916 errors (~6%); 51% (arXiv) / 54% (NeurIPS) of flagged candidates confirmed by humans; on corrected labels ResNet-18 outperforms ResNet-50 if the share of originally mislabeled test examples rises by 6%; demo labelerrors.com. Method: Confident Learning (Northcutt, Jiang, Chuang, JAIR 2021, arXiv 1911.00068): prune, count, rank; estimate the joint of noisy and true labels (the 'confident joint'). Steps: 1 out-of-sample probabilities with K-fold cross_val_predict (in-sample probabilities memorize the noise); 2 per-class threshold t_j = mean self-confidence of examples labeled j; 3 count x into cell (i, j) if p(j|x) >= t_j; 4 off-diagonal cells are likely errors, ranked by self-confidence; 5 prune or relabel, retrain. cleanlab 2.9.0: find_label_issues, CleanLearning, Datalab (label issues, outliers, near-duplicates, non-IID in one report). Pitfall: pred_probs columns must be ordered by class. Training dynamics: Dataset Cartography (EMNLP 2020, arXiv 2009.10795): confidence = mean p(true) over epochs, variability = std; easy-to-learn, ambiguous (helps OOD generalization; ~33% subset), hard-to-learn (often label errors -> relabel queue). Cite .cite.repo github.com/cleanlab/cleanlab, .cite.repo github.com/allenai/cartography.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: a 4x4 confident-joint heatmap fills cell by cell (fixed counts); diagonal cells green. Step 2: off-diagonal cells glow red and fly out into a ranked issue list. Step 3: code-wrap with focus on cross_val_predict (callout 'out-of-sample'), then find_label_issues, then Datalab. Step 4: the heatmap swaps for a data map scatter (variability x, confidence y) with three shaded regions labelled easy / ambiguous / hard; points in the hard region pulse and move to a 'relabel' bin.

**Code.** 05-labels-noise-active.md section 4: cleanlab 2.9.0 — pred_probs = cross_val_predict(model, X, labels, cv=5, method='predict_proba'); cleanlab.filter.find_label_issues(labels=labels, pred_probs=pred_probs, filter_by='both', return_indices_ranked_by='self_confidence'); CleanLearning(model).fit(X, labels); Datalab({'X': X, 'y': labels}, label_name='y').find_issues(pred_probs=pred_probs, features=X); lab.report().

### 38. Active learning spends the labeling budget on uncertain and diverse examples

- File: `c06-04-active-learning.html`
- Id: `custom-c06-active-learning`

**Content.** Loop: labeled seed -> train -> score the unlabeled pool -> select a batch of B -> humans or an LLM label it -> add -> repeat until the budget ends or performance plateaus. Strategies: uncertainty (least confidence 1 - max p, margin p1 - p2, entropy): cheap but batches are redundant; core-set (Sener and Savarese, ICLR 2018, arXiv 1708.00489): greedy k-center in embedding space; BADGE (Ash et al., ICLR 2020, arXiv 1906.03671): gradient of the loss w.r.t. the last layer using the predicted label as a hypothetical label (norm = uncertainty, direction = diversity) + k-means++ seeding; it 'balances uncertainty and diversity' with no hand-tuned trade-off. LLM-era: LLM disagreement or self-consistency as the uncertainty signal; diversity on sentence embeddings; route to LLM annotator or human. Weak supervision: Snorkel (PVLDB 2017, arXiv 1711.10160): experts built models 2.8x faster with +45.5% average performance vs 7 hours of hand labeling, within 3.60% of large hand-curated sets; labeling functions (rules, regex, LLM prompts) -> label matrix -> LabelModel learns LF accuracies without ground truth -> probabilistic labels. Snorkel OSS 0.10.0 has had no release since Feb 2024 and lists CVE-2026-31222..31224: teach it, check before production. Open challenges: cold start; sampling bias (evaluate on a separately sampled random test set); gains over random shrink with strong pretrained embeddings. Libraries: modAL, small-text, github.com/JordanAsh/badge.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: a 2-D pool of ~120 grey points (index-based positions) with a curved decision boundary. Step 2: 'uncertainty only' picks 10 points that clump near one part of the boundary (amber rings). Step 3: 'BADGE / core-set' picks 10 points spread along the boundary and into sparse regions (violet rings). Step 4: a circular loop (train -> score -> select -> label) draws around the plot with :flow pulses; the labeled set grows. Step 5: a Snorkel mini-panel: an LF vote matrix (rows examples, columns LFs, cells vote / abstain) collapses through a 'LabelModel' node into probability bars; a t-risk tag 'no release since 2024; CVEs'.

### 39. Split by entity and by time, or the test set leaks the answer

- File: `c06-05-leakage-splits.html`
- Id: `custom-c06-leakage-splits`

**Content.** Leakage types: entity / group (same patient, user, speaker, repo or document family in train and test); temporal (train on the future, test on the past; features using future information); preprocessing (scaler, imputer, feature selection, SMOTE or vocabulary fit before the split); duplicate / near-duplicate; target leakage (a proxy for the label, such as 'treatment given'); benchmark contamination. Evidence: Kapoor and Narayanan (arXiv 2207.07048): leakage errors in 329 papers across 17 fields, a taxonomy of 8 types, model info sheets; civil-war prediction: after fixing leakage, 'complex ML models don't perform substantively better than decades-old LR models'. scikit-learn guide: i.i.d. 'rarely holds in practice' — with group structure 'it is safer to use group-wise cross-validation'. Tools (scikit-learn 1.9.x): GroupKFold ('the same subject is never in both testing and training'), StratifiedGroupKFold, TimeSeriesSplit(n_splits=5, gap=7) on time-sorted rows ('successive training sets are supersets'), and make_pipeline so every fitted step is fit per fold. LLM / RAG: hold out by time — test only on documents and questions created after the model's training cutoff. .callout.pitfall 'Random K-fold on multi-scan medical images measures memorized patients, not diagnosis.'

**Visual and animation.** Leakage gallery, three panels revealed one per step. Step 1 (entity): rows coloured by patient id; with random split, same-colour rows land in both folds (red links); toggled to GroupKFold, colours separate cleanly. Step 2 (time): a timeline with a train window, a gap band (gap=7) and a test window that slide forward over 3 folds. Step 3 (preprocessing): 'scaler fit on all data' wire crosses into the test box (red), then moves inside a Pipeline box per fold. Step 4: code-wrap with focus moving GroupKFold -> StratifiedGroupKFold -> TimeSeriesSplit. No invented CV scores; use arrows labelled 'optimistic' vs 'honest'.

**Code.** 05-labels-noise-active.md section 9: scikit-learn 1.9.x — pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)); cross_val_score(pipe, X, y, groups=patient_id, cv=GroupKFold(n_splits=5)); StratifiedGroupKFold(n_splits=5); TimeSeriesSplit(n_splits=5, gap=7) on X_sorted, y_sorted.

### 40. Deduplicate across splits with MinHash, and test LLMs on data newer than their cutoff

- File: `c06-06-dedup-contamination.html`
- Id: `custom-c06-dedup-contamination`

**Content.** Duplicates: Lee et al. (ACL 2022, arXiv 2107.06499): one 61-word sentence repeated over 60,000 times in C4; dedup makes models emit memorized text 10x less often; train-test overlap affects over 4% of the validation sets of standard datasets. MinHash LSH: normalize -> shingle (for example 5-gram words) -> MinHash signature (128 permutations; P(match at a position) = Jaccard) -> LSH banding b x r: candidate probability 1 - (1 - s^r)^b, an S-curve with threshold near (1/b)^(1/r) -> verify Jaccard -> connected components -> keep one per cluster. FineWeb used 5-grams and 112 hashes = 14 buckets x 8 (targets ~75% similar). Cross-split dedup: build the index on the test set, query every training document, drop matches; paraphrases: embedding cosine above about 0.9 (FAISS / HNSW). Contamination: Sainz et al. (EMNLP 2023 Findings) call for per-benchmark measurement; GSM1k (arXiv 2405.00332): accuracy drops up to 8% vs GSM8k for some families; likelihood of generating GSM8k items correlates with the gap (r^2 = 0.36); Min-K% Prob (arXiv 2310.16789): mean log-prob of the k% least likely tokens, +7.4% on WikiMIA; LiveCodeBench (arXiv 2403.07974) evaluates on problems released after the model cutoff; canary strings (BIG-bench GUID). Checklist: decontaminate SFT / RL sets against every eval set (n-gram + MinHash + embedding); keep a private time-stamped holdout; report the training cutoff; check RL reward problems vs benchmarks; record method, thresholds and number removed in the quality card.

**Visual and animation.** Bespoke SVG (Deck.register). Step 1: a document turns into shingles, then into a signature strip of 16 hash cells, split into 4 bands of 4. Step 2: an S-curve plot of 1 - (1 - s^r)^b draws for b=4, r=4; step 3 it redraws for b=14, r=8 (FineWeb) and the threshold marker moves (computed exactly). Step 4: code-wrap with focus on MinHashLSH(threshold=0.8) and the query/insert loop. Step 5: a GSM8k vs GSM1k bar pair with a red 'up to 8%' gap and a timeline with a 'model cutoff' line separating LiveCodeBench problems.

**Code.** 05-labels-noise-active.md section 10: datasketch — def mh(text, num_perm=128, n=5) building word 5-gram shingles into MinHash; lsh = MinHashLSH(threshold=0.8, num_perm=128); for doc_id, text in corpus.items(): skip if lsh.query(m) else lsh.insert(doc_id, m).

### 41. Interview: labels, noise and leakage

- File: `c06-07-qa.html`
- Id: `custom-c06-qa`

**Content.** Q1: 'Raw agreement is 92% but Cohen's kappa is 0.3. Who is right?' A: Both numbers are correct. With a skewed class prior, chance agreement p_e is high, so kappa is low (kappa paradox). Report both, inspect the minority class, and use Krippendorff's alpha if raters miss items. Q2: 'Your medical imaging model scores 0.97 AUC. What do you check first?' A: Patient-level leakage: several scans per patient across folds. Re-run with GroupKFold on patient id, fit preprocessing inside a Pipeline, and check near-duplicates across splits. Q3: 'How do you use an LLM as a labeler safely?' A: Expert gold set of 200-500 items; compare LLM-human alpha with human-human alpha; swap orders, fixed label set, temperature 0, several judges; route low-confidence items to humans; cleanlab audit; re-audit 2-5% weekly. Q4: 'How do you show your RL gains are not contamination?' A: Decontaminate reward prompts against all evals (n-gram, MinHash, embeddings), use a private holdout dated after the training cutoff, test on a fresh clone such as GSM1k or LiveCodeBench, and log the method in the card.

**Visual and animation.** Standard .qa layout with answers at steps 1-4.


## Chapter 07: LLM datasets and synthetic data with verification

Tone: `state`

Research files:
- C:/Users/evija/googleadk2.0/research-custom/06-llm-rag-datasets-synthetic.md
- C:/Users/evija/googleadk2.0/research-custom/08-sota-examples-challenges.md
- C:/Users/evija/googleadk2.0/research-custom/05-labels-noise-active.md

### 42. Modern LLM data is filtered hard, synthesized at scale and verified before use

- File: `c07-01-chapter.html`
- Id: `custom-c07-chapter`

**Content.** Chapter opener. .display. .lede: 'From 2023 to 2026 most gains came from model-based filtering and verified synthetic data, not from more raw tokens.' Lifecycle strip with GENERATE, SELECT, CURATE lit. Tags: FineWeb-Edu, DCLM, Nemotron-CC, Magpie, Persona Hub, OpenThoughts, distilabel, RAGAS. Versions: datatrove 0.10.1, nemo-curator 1.4.0, ragas 0.4.3, distilabel 1.5.3 (no PyPI release since Jan 2025).

**Visual and animation.** A wide funnel outline draws (data-fx draw); token particles stream in at the top and only a few exit at the bottom (gsap loop, deterministic).

### 43. Model-based filters throw away about 90% of the web and still win

- File: `c07-02-curation-funnel.html`
- Id: `custom-c07-curation-funnel`

**Content.** FineWeb (arXiv 2406.17557): 15T tokens from 96 Common Crawl snapshots; FineWeb-Edu 1.3T. Edu classifier: Llama-3-70B-Instruct scored 460k pages on 0-5; linear head on Snowflake-arctic-embed-m; keep score >= 3 (F1 82%); 6,000 H100 GPU-hours to score 15T tokens. Result: 33.6% MMLU at 38B tokens; Matrix needs about 300B tokens for the same score (~10x fewer tokens). Dedup paradox: per-snapshot MinHash dedup left 20T tokens and matched RefinedWeb; global dedup left ~4T and performed worse. DCLM (arXiv 2406.11794): DCLM-Pool ~240T tokens -> DCLM-Baseline 3.8T; fastText classifier on OpenHermes 2.5 + r/ExplainLikeImFive positives keeps the top 10%; Core score fastText 30.2 vs perplexity 29.0 vs AskLLM 28.6 vs RefinedWeb 27.5; DCLM-7B 64% MMLU after 2.6T tokens, comparable to Llama 3 8B (66%) with 6.6x less compute; 'model-based filtering is key'. Nemotron-CC (arXiv 2412.02595): 6.3T tokens with classifier ensembling + synthetic rephrasing; 8B model +5 MMLU over Llama 3.1 8B; argues that removing ~90% hurts long horizons. Pattern: an LLM annotates ~0.5M documents, a tiny classifier learns the labels and runs over trillions of tokens. Teaching point: datatrove filters take an exclusion_writer so every removal is auditable; removal rates go on the quality card. FineWeb-Edu card warns the classifier may 'overfit to academic-looking content'.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: two funnels side by side: DCLM 240T -> 3.8T and FineWeb 15T -> 1.3T; numbers count down as the funnels narrow. Step 2: a 3-node flow 'Llama-3-70B labels 460k pages' -> 'embed + linear head (F1 82%)' -> 'score 15T tokens (6,000 H100 h)'. Step 3: a bar pair '38B vs ~300B tokens to 33.6% MMLU'. Step 4: code-wrap with focus on the classifier call and int_score clamp. Step 5: dedup paradox bars (per-snapshot 20T good vs global 4T worse) with a t-risk tag 'too clean'.

**Code.** 06-llm-rag-datasets-synthetic.md section 2.1: FineWeb-Edu classifier (verbatim from the model card) — AutoTokenizer / AutoModelForSequenceClassification.from_pretrained('HuggingFaceTB/fineweb-edu-classifier'); logits.squeeze(-1); score; int_score = int(round(max(0, min(score, 5)))); keep int_score >= 3.

### 44. Four generators make instruction data: seeds, evolution, empty templates and personas

- File: `c07-03-instruction-synthesis.html`
- Id: `custom-c07-instruction-synthesis`

**Content.** Self-Instruct (ACL 2023, arXiv 2212.10560): bootstrap from seed tasks; +33% absolute on Super-NaturalInstructions over vanilla GPT-3. Evol-Instruct / WizardLM (ICLR 2024, arXiv 2304.12244): rewrite instructions into more complex ones (in-depth, in-breadth); >90% of ChatGPT capacity on 17 of 29 skills (GPT-4 eval). Magpie (arXiv 2406.08464): feed only the chat template up to the user slot; the aligned model writes the user query itself; 4M generated, 300K selected; Llama-3-8B-Base + Magpie SFT comparable to Llama-3-8B-Instruct on some tasks. Persona Hub (arXiv 2406.20094): persona x prompt for diversity; 1B personas, 370M 'elite personas' released 2025-02-18. Tulu 3 SFT mixture: 939,344 samples incl. persona MATH 149,960, GSM 49,980, Python 34,999, IF 29,980. OpenThoughts (arXiv 2506.04178, 1,000+ ablations): multiple teacher answers per question grow a source 'by at least 16x'; 'top 1 or 2' high-quality sources beat many; filter by LLM-labeled difficulty or response length; 'QwQ-32B is a stronger teacher than DeepSeek-R1' — the best model is not always the best teacher; OpenThinker3-7B: AIME25 53%, LiveCodeBench 51%, GPQA-D 54%. Tool: distilabel (Magpie, EvolInstruct, UltraFeedback, SelfInstruct, PrometheusEval tasks); README says community-maintained, latest fixes on develop: a sustainability risk.

**Visual and animation.** 2x2 grid of generator cards appearing one per step. Step 1 Self-Instruct: a seed pool sprouts new task chips. Step 2 Evol-Instruct: one instruction grows a mutation tree (depth / breadth). Step 3 Magpie (bespoke gsap typewriter): a chat template prints '<|start_header_id|>user<|end_header_id|>' and stops; then the model types a user question into the empty slot. Step 4 Persona Hub: persona chips multiply a prompt into varied tasks. Step 5: code-wrap with focus on magpie_pre_query_template='llama3' and only_instruction=True; OpenThoughts findings as a .callout.insight.

**Code.** 06-llm-rag-datasets-synthetic.md section 3: distilabel MagpieGenerator (verbatim from the components gallery) — MagpieGenerator(llm=TransformersLLM(model='meta-llama/Meta-Llama-3-8B-Instruct', magpie_pre_query_template='llama3', generation_kwargs={'temperature': 1.0, 'max_new_tokens': 256}), only_instruction=True, num_rows=5); generator.load(); next(generator.process()).

### 45. Generate many candidates, verify them from cheap to costly, and keep only what passes

- File: `c07-04-generate-verify-keep.html`
- Id: `custom-c07-generate-verify-keep`

**Content.** Funnel: prompt pool (seeds, personas, Magpie) -> sample K candidates per prompt (Llama 3: K 'typically between 10 and 30') -> verifiers in order of cost: 1 format / parse / lint; 2 execution + unit tests (code), exact match or symbolic check (math); 3 reward model or LLM-judge rubric; 4 constitutional / safety critique-and-revise -> keep best-of-K (rejection sampling) or chosen/rejected pairs for DPO -> dedup + decontaminate -> card. Llama 3 (arXiv 2407.21783): over 2.7M synthetic code examples in SFT; about 1M coding dialogues used execution feedback (parser, linter, model-written unit tests in containers, error-guided self-repair); 'about 20% of solutions were initially incorrect but self-corrected'; SFT filter: RM top quartile or Llama-judge max score + InsTag difficulty + semantic dedup. Judges: >80% agreement with humans (Zheng 2023) but position, verbosity and self-enhancement bias: swap order, use rubrics and reference answers, use a judge from another model family. RLVR moves verification into the reward (Tulu 3). Constitutional AI also works as a filter on synthetic data. .callout.pitfall 'Run generated code in a sandbox: a container, no network.' Code is an illustrative pattern written for the deck (not from an official repo).

**Visual and animation.** Bespoke gsap funnel (Deck.register). Step 1: 16 candidate dots fall from a prompt into the funnel. Step 2: a 'lint' gate removes 3 dots (they fade red). Step 3: a 'unit tests' gate removes 6 more. Step 4: a 'judge rubric' gate removes 2; a 'constitution' gate removes 1; survivors split into a 'best-of-K -> SFT' tray and a 'pass/fail pairs -> DPO' tray. Counters per gate are computed from the fixed dot pattern. Step 5: code-wrap with focus on passes_tests() (subprocess with -I and timeout) then rejection_sample(); the Llama 3 stat '20% self-corrected' counts up.

**Code.** 06-llm-rag-datasets-synthetic.md section 5: illustrative unit-test rejection sampling — passes_tests(solution, tests, timeout=5) writing a temp file and running subprocess.run(['python', '-I', f.name], capture_output=True, timeout=timeout); rejection_sample(prompt, tests, generate, k=16) keeping passing candidates (SFT) or passing/failing pairs (DPO).

### 46. Synthetic data collapses a model when it replaces real data, not when it is anchored and added

- File: `c07-05-collapse-verification.html`
- Id: `custom-c07-collapse-verification`

**Content.** Collapse: Shumailov et al. (arXiv 2305.17493; Nature 631, 755-759, July 2024): training on model output causes 'irreversible defects in the resulting models, where tails of the original content distribution disappear'; a prompt about medieval architecture turned into a list of jackrabbits by generation 9. Counter-result: Gerstgrasser, Schaeffer et al. (arXiv 2404.01413): 'accumulating the successive generations of synthetic data alongside the original real data avoids model collapse' — the failure is replacing, not adding. Mitigations: keep a real-data anchor, a source=synthetic flag, diversity controls (personas, Magpie, temperature), dedup synthetic outputs against each other, measure diversity (distinct-n, embedding spread), ground in verifiers rather than self-judgment. Anchored synthesis works: Phi-4 (arXiv 2412.08905) 'substantially surpasses its teacher model on STEM-focused QA'; SmolLM3 APO pairs with chosen = Qwen3-32B, rejected = Qwen3-0.6B. Verification paradox: OpenThoughts — 'We experimented with numerous verification and answer filtering methods, and none gave significant performance improvements' for SFT distillation from a strong teacher; verification is essential for RLVR (Tulu 3) and for code (Llama 3). Collapse by curation: every lab filters for 'educational-looking' text, which risks a narrow style and lost tails (classifier monoculture).

**Visual and animation.** Bespoke gsap (Deck.register). Two histogram panels side by side over generations 0 -> 9 (step 1 sets gen 0). Step 2-3: the 'replace' panel's tails shrink each generation and the peak narrows (deterministic formula); a 'jackrabbits' quote pops at gen 9. Step 3: the 'accumulate' panel keeps its tails (a real-data band stays under the curve). Step 4: a contrast strip: 'SFT distillation: verification did not help (OpenThoughts)' vs 'RLVR and code: verification essential (Tulu 3, Llama 3)', with a question mark for the audience. Step 5: mitigation ticks list (ul.ticks) stagger in.

### 47. Build RAG test sets from a knowledge graph, then verify them before they count as gold

- File: `c07-06-rag-eval-datasets.html`
- Id: `custom-c07-rag-eval-datasets`

**Content.** RAGAS 0.4.3 'Testset Generation for RAG': documents become nodes of a KnowledgeGraph; default_transforms / apply_transforms add summaries, entities, embeddings and relationships (docs example: 10 nodes -> 48 nodes / 605 relationships); the graph yields scenarios, scenarios yield queries. Default query mix: SingleHopSpecificQuerySynthesizer 0.5, MultiHopAbstractQuerySynthesizer 0.25, MultiHopSpecificQuerySynthesizer 0.25. Output columns: user_input, reference_contexts, reference, synthesizer_name. Metrics: LLMContextRecall, Faithfulness, FactualCorrectness (docs example: 1.0, 0.857, 0.728). Verification before the set counts as gold: 1 the reference is supported by reference_contexts (faithfulness judge); 2 remove questions answerable without retrieval (closed-book leak test); 3 humans spot-check 5-10%; 4 rebalance single-hop vs multi-hop to match real query logs; 5 version the set and never train on it. Combine with real queries from logs (PII-scrubbed). Cite .cite.doc docs.ragas.io 'Testset Generation for RAG' and 'rag_eval'.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: 10 document nodes appear; step 2 edges and derived nodes grow to 48 nodes / 605 edges (counter counts up; layout deterministic, edges drawn as thin lines). Step 3: a donut chart of the 50/25/25 synthesizer mix draws. Step 4: code-wrap with focus on TestsetGenerator(llm, embedding_model) and generate_with_langchain_docs(docs, testset_size=10). Step 5: an ol.seq of the five verification steps reveals; the 'closed-book leak test' step gets a t-risk tag.

**Code.** 06-llm-rag-datasets-synthetic.md section 7: RAGAS condensed — DirectoryLoader('Sample_Docs_Markdown/', glob='**/*.md').load(); LangchainLLMWrapper(ChatOpenAI(model='gpt-4o')); OpenAIEmbeddings(client=openai.OpenAI()); TestsetGenerator(llm=llm, embedding_model=embeddings).generate_with_langchain_docs(docs, testset_size=10); dataset.to_pandas().

### 48. Interview: LLM datasets and synthetic data

- File: `c07-07-qa.html`
- Id: `custom-c07-qa`

**Content.** Q1: 'Why might verifying distilled SFT data not improve the student?' A: With a strong teacher most traces are already good, and wrong-but-instructive traces still teach format and reasoning style; OpenThoughts found no significant gain from verification. Spend the verification budget on RL rewards and code, where wrong signals do damage. Q2: 'How do you stop a synthetic data loop from collapsing the model?' A: Accumulate, never replace, real data; flag provenance; control diversity with personas and sampling; dedup synthetic outputs; verify with programs; track distinct-n and tail coverage on the card. Q3: 'Design a quality filter for 10T web tokens.' A: Have a large LLM label ~0.5M pages on a rubric, train a small classifier (fastText or an embedding + linear head), pick the threshold by F1 on a held-out split (FineWeb-Edu: >= 3, F1 82%), log removal rates per filter, and check the bias of the classifier. Q4: 'Dedup globally or per snapshot?' A: FineWeb found per-snapshot dedup (20T tokens) better than global dedup (~4T, worse): global dedup over-removes good repeated content and keeps the low-quality tail. Measure, do not assume.

**Visual and animation.** Standard .qa layout with answers at steps 1-4.


## Chapter 08: AI eval design

Tone: `tool`

Research files:
- C:/Users/evija/googleadk2.0/research-custom/07-eval-design.md
- C:/Users/evija/googleadk2.0/research-custom/05-labels-noise-active.md
- C:/Users/evija/googleadk2.0/research-custom/01-customization-map.md

### 49. An eval is an experiment: design it like a dataset and report it with error bars

- File: `c08-01-chapter.html`
- Id: `custom-c08-chapter`

**Content.** Chapter opener. .display. .lede: 'The eval set decides what ships, so it needs more care than the training set.' Quote: 'Fundamentally, evaluations are experiments' (Evan Miller, Adding Error Bars to Evals, arXiv 2411.00640). Tags: error analysis, golden sets, slice metrics, paired bootstrap, LLM-as-judge, calibration, cost-sensitive thresholds. Lifecycle strip with an arrow from error analysis back to DESIGN.

**Visual and animation.** A single score '84%' appears, then CI whiskers grow around it and the number splits into slice bars (gsap), previewing the chapter.

### 50. Start with error analysis on real traces, then freeze a versioned golden set

- File: `c08-02-error-analysis-golden.html`
- Id: `custom-c08-error-analysis-golden`

**Content.** Husain and Shankar, 'AI Evals: Everything You Need to Know' (hamel.dev, 2026-09-18): 'Error analysis is the most important activity in evals'; 'Write evaluators for errors you discover, not errors you imagine'; review at least 100 traces; annotate at least 30 yourself. Loop: open coding (free-text notes per failing trace) -> axial coding (cluster into a failure taxonomy) -> each failure mode becomes a slice with a binary pass/fail evaluator ('Binary evaluations force clearer thinking') -> one benevolent dictator owns the quality definition -> code assertions first (regex, JSON schema, exact match), LLM judges only for subjective criteria -> align the judge to humans (TPR / TNR) -> CI regression gate per slice -> watch criteria drift ('grading outputs helps users define criteria', Shankar et al., arXiv 2404.12272). Evals before code? The FAQ says 'Generally no' — EDD is error-analysis-first. Golden set rules (table.t): source mix = production traces + targeted synthetic edge cases (dimensions x values grid, human-validated); size 100-500 to start (n=400, p=0.8 -> 95% CI about +/-3.9 pts); slices by intent, language, tier, length, failure mode, safety; decontaminate against SFT data, keep a private holdout; immutable versions (golden_v3.2) with an owner; splits dev / test / judge-calibration; refresh monthly, retire saturated items.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: 100 small trace cards fill a grid (index-based). Step 2: notes appear on ~30 failing cards (open coding). Step 3: failing cards fly into 6 labelled piles (axial coding: e.g. wrong policy, missing citation, tone, tool error, hallucinated field, refusal). Step 4: each pile turns into a slice tag + a binary pass/fail chip. Step 5: the piles compress into a 'golden_v3.2' box with version and owner, and the golden-set rules table fades in beside it.

### 51. Report every score per slice with n and a confidence interval, and compare models on paired items

- File: `c08-03-slices-ci.html`
- Id: `custom-c08-slices-ci`

**Content.** Rules: never report only the global number; aggregate accuracy hides slice regressions (Simpson's paradox). SE ~ sqrt(p(1-p)/n). Use Wilson intervals for small n or p near 0 or 1 (statsmodels proportion_confint(method='wilson')). Miller (arXiv 2411.00640): report the standard error; use clustered SEs when questions share a passage; compare two models with paired differences on the same items (removes item-difficulty variance); resample answers k times to reduce within-item variance; do a power analysis first. Power: minimum detectable effect at alpha 0.05 and power 0.8 is about 2.8 x SE(delta); unpaired with p = 0.8 and n = 500 per arm, SE(delta) ~ 0.025, so only ~7-point deltas are detectable; pairing shrinks this. Paired bootstrap: 10,000 resamples of per-item differences, 95% percentile CI and P(delta <= 0); SciPy scipy.stats.bootstrap(..., method='BCa'); for clustered data resample clusters. .callout.pitfall 'Many SOTA deltas sit inside the noise.' Example for the animation (labelled as an example): A 81.0 vs B 82.1.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: two leaderboard bars A 81.0 and B 82.1 (labelled 'example'). Step 2: CI whiskers grow until they overlap. Step 3: bars split into 5 slice bars each; one slice of B drops below A (fixed example values, labelled illustrative). Step 4: the view switches to a histogram of bootstrap deltas building up bar by bar with a vertical 0 line and the 95% band shaded. Step 5: code-wrap with focus on d = b - a, the bootstrap list comprehension, and the percentile line.

**Code.** 07-eval-design.md section 5: paired bootstrap — rng = np.random.default_rng(0); a, b = per-item scores; d = b - a; boots = np.array([rng.choice(d, size=len(d), replace=True).mean() for _ in range(10_000)]); lo, hi = np.percentile(boots, [2.5, 97.5]); print delta, CI and P(delta<=0). Optional second block: the statsmodels Wilson slice table from section 4.

### 52. Validate the LLM judge against expert labels, then correct its pass rate

- File: `c08-04-llm-judge.html`
- Id: `custom-c08-llm-judge`

**Content.** Zheng et al. (NeurIPS 2023 D&B, arXiv 2306.05685): GPT-4 judge 'over 80% agreement, the same level of agreement between humans'; biases: position, verbosity, self-enhancement, limited reasoning. Pitfall -> mitigation (table.t): position bias -> judge both orders, win only if it holds in both; verbosity -> length-controlled scoring (Length-Controlled AlpacaEval, arXiv 2404.04475), rubric says 'do not reward length'; self-preference -> judge from another model family; vague Likert -> binary pass/fail per criterion, one judge per failure mode; rubric drift -> freeze and version the judge prompt; never validated -> expert-labeled calibration split with TPR, TNR and kappa; reference leakage -> reference-guided grading only where a reference exists. G-Eval (arXiv 2303.16634) is the basis of DeepEval GEval. Correction (Rogan-Gladen): theta = (p_obs + TNR - 1) / (TPR + TNR - 1); bootstrap over calibration and eval items. Managed: Vertex Gen AI evaluation service default GENERAL_QUALITY adaptive rubric metric (rubrics generated per prompt, then judged); AutoSxS for side-by-side migrations. Pairwise: Chatbot Arena (arXiv 2403.04132, 240K+ votes) moved from online Elo to Bradley-Terry with bootstrap CIs (order-independent); P(i beats j) = sigmoid(beta_i - beta_j); added style control.

**Visual and animation.** Step 1-4: four bias icons (position, verbosity, self-preference, vague scale) flip one per step to show their mitigation. Step 5: a 2x2 confusion matrix (human vs judge) fills cell by cell (example counts), TPR / TNR / kappa compute and count up. Step 6: the Rogan-Gladen formula types in and a corrected pass-rate bar slides from p_obs to theta. Code-wrap at the bottom right with focus on cohen_kappa_score and confusion_matrix(...).ravel().

**Code.** 07-eval-design.md section 8: k = cohen_kappa_score(human, judge); tn, fp, fn, tp = confusion_matrix(human, judge, labels=[0, 1]).ravel(); tpr, tnr = tp/(tp+fn), tn/(tn+fp); print kappa / TPR / TNR. Add one line computing theta = (p_obs + tnr - 1) / (tpr + tnr - 1) (the Rogan-Gladen formula from the same section).

### 53. Calibrate the scores, then pick the threshold with the cost of each error

- File: `c08-05-calibration-thresholds.html`
- Id: `custom-c08-calibration-thresholds`

**Content.** Calibration: Guo et al. (ICML 2017, arXiv 1706.04599): 'modern neural networks, unlike those from a decade ago, are poorly calibrated'; temperature scaling 'is surprisingly effective'. ECE = sum_b (|B_b|/n) |acc(B_b) - conf(B_b)| with 10 or 15 equal-width bins; it depends on binning, so also report Brier / log loss and a reliability diagram. Fix: CalibratedClassifierCV(method='sigmoid' or 'isotonic') or temperature scaling on a held-out split. LLM uses: guardrail heads, verbalized or token-probability confidence for abstention, judge confidence for routing to humans. Thresholds: a score is not a decision. With calibrated p, flag when p > t* = C_FP / (C_FP + C_FN); a miss costing 20x a false alarm gives t* = 1/21 ~ 0.048. Expected cost EC(t) = pi x FNR(t) x C_FN + (1 - pi) x FPR(t) x C_FP with pi = production prevalence; on ROC the optimum touches an iso-cost line of slope C_FP(1 - pi) / (C_FN pi). .callout.pitfall 'Golden sets are enriched with positives: re-weight to production prevalence before you pick t.' Check the threshold per slice. Link back to chapter 1: the OpenAI break-even accuracy example (81.5%) is the same cost logic.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: reliability diagram with 10 bars above/below the diagonal (fixed example values) and an ECE counter. Step 2: temperature scaling: bars slide onto the diagonal and ECE counts down. Step 3: a ROC curve draws (parametric, deterministic). Step 4: an iso-cost line sweeps for cost ratio 1, then 5, then 20; the operating-point dot slides along the curve each time and t* updates (1/2 -> 1/6 -> 1/21). Step 5: code-wrap with focus on the ec = pi*(1-tpr)*C_fn + (1-pi)*fpr*C_fp line and argmin.

**Code.** 07-eval-design.md section 7: fpr, tpr, thr = roc_curve(y_true, scores); pi, C_fp, C_fn = 0.02, 1.0, 20.0; ec = pi*(1-tpr)*C_fn + (1-pi)*fpr*C_fp; best = np.argmin(ec); print threshold / TPR / FPR / EC.

### 54. Interview: AI eval design

- File: `c08-06-qa.html`
- Id: `custom-c08-qa`

**Content.** Q1: 'Model B beats model A by 1.1 points on 500 items. Do you ship?' A: Not yet. Compute a paired bootstrap CI of the per-item delta; unpaired at n=500 you can detect only about 7 points. Check every slice for regressions, and cluster by conversation or passage if items are grouped. Q2: 'How do you trust an LLM judge?' A: Label a calibration split with experts, measure TPR, TNR and kappa, mitigate position / length / self-preference bias, freeze and version the judge prompt, and correct the pass rate with Rogan-Gladen. Q3: 'Pick the threshold for a PII filter where a miss costs 20x a false alarm.' A: Calibrate first; t* = 1/(1+20) ~ 0.048; compute expected cost at the production prevalence, not the enriched eval prevalence; check the threshold per slice. Q4: 'What goes on an eval quality card?' A: Set version and owner, provenance mix, n and slices with min n, decontamination method, label agreement and noise audit, judge model + prompt version + TPR / TNR, headline score with CI, worst slice, calibration (ECE), operating point, known gaps.

**Visual and animation.** Standard .qa layout with answers at steps 1-4.


## Chapter 09: The full lifecycle in production and open challenges

Tone: `risk`

Research files:
- C:/Users/evija/googleadk2.0/research-custom/08-sota-examples-challenges.md
- C:/Users/evija/googleadk2.0/research-custom/06-llm-rag-datasets-synthetic.md
- C:/Users/evija/googleadk2.0/research-custom/07-eval-design.md
- C:/Users/evija/googleadk2.0/research-custom/04-dataset-design-contracts.md

### 55. Run the whole lifecycle as one workflow, then face the open problems

- File: `c09-01-chapter.html`
- Id: `custom-c09-chapter`

**Content.** Chapter opener. .display. .lede: 'Design, generate, select, curate, label, denoise and document every release. Then measure what still breaks: reward hacking, contamination, collapse, licensing and platform risk.' Quote: 'The model flow is the full lifecycle of an LM: every stage, checkpoint, dataset, and dependency.' (Ai2, OLMo 3 blog, allenai.org/blog/olmo3). Tags: workflow, quality card, Tulu 3, OLMo 3, SmolLM3, open challenges.

**Visual and animation.** The 7-stage lifecycle strip bends into a closed ring (gsap morph); a pulse travels round it once; a red 'open problems' badge appears at the centre.

### 56. One workflow runs design, generate, select, curate, label, denoise and the quality card for every release

- File: `c09-02-lifecycle-workflow.html`
- Id: `custom-c09-lifecycle-workflow`

**Content.** Best-practice workflow, Oct 2026 (stage -> artifact -> tool -> gate): DESIGN: taxonomy + slices + contract (ODCS v3.1.0 / datacontract-cli, Pandera 0.34.1) -> gate: contract lint. GENERATE: logs + synthetic (distilabel Magpie / personas, teacher distillation, TRL DistillationTrainer) -> gate: provenance flag per row. SELECT: quality classifier (FineWeb-Edu style), LESS (arXiv 2402.04333: the LESS-selected 5% often beats the full set), DSIR (arXiv 2302.03169) -> gate: removal rates logged. CURATE: MinHash / semantic dedup + decontamination (datatrove 0.10.1; NeMo Curator 1.4.0 GPU fuzzy dedup ~16x faster: 10.7 h CPU vs 0.65 h) -> gate: cross-split overlap = 0. LABEL: experts + LLM suggestions (Argilla 2.8.0 in maintenance mode; Label Studio 1.23.2) -> gate: alpha >= 0.8. DENOISE: cleanlab 2.9.0, verifiers, unit tests -> gate: audit rate. TRAIN: TRL v1.16.0 / Unsloth / Vertex tuning. EVAL: Inspect AI 0.3.283, lm-evaluation-harness 0.4.13, DeepEval 4.3.1, promptfoo, Vertex client.evals; HELM entered maintenance mode on 2026-06-01 -> gate: no slice regresses beyond its CI. CARD: Data Card + Croissant-RAI + eval card. MONITOR: Evidently 0.7.23 on descriptors -> drift alert loops to DESIGN (taxonomy update, contract v2). Sustainability: Argilla maintenance-only, distilabel community-maintained, Snorkel no release since 2024 + CVEs, WhyLabs hosted shut down, torchtune wound down in 2025: pin versions, keep open formats (ODCS, Croissant, JSONL), keep recipes portable.

**Visual and animation.** Bespoke gsap lifecycle wheel (Deck.register): 8 sectors (design, generate, select, curate, label, denoise, card, monitor) around a 'train + eval' hub. Steps 1-4 each light two sectors and drop the tool chips (with version badges) into them; gate icons appear on the sector borders. Step 5: a red drift-alert pulse runs from monitor back to design along a bend wire. Step 6: maintenance-risk tags (t-risk) appear on Argilla, distilabel, Snorkel, HELM chips.

### 57. The quality card closes the loop: no number without n, CI, slice and version

- File: `c09-03-quality-card.html`
- Id: `custom-c09-quality-card`

**Content.** Lineage: Datasheets (2018), Model Cards (Mitchell et al., FAT* 2019, arXiv 1810.03993: intended use, factors, metrics, evaluation data, quantitative analyses, caveats), Data Cards (2022): 'documentation must be treated as a user-centric product in and of itself'. Data quality card fields (from FineWeb / Llama 3 practice): sources with snapshot dates; every filter with its removal rate; dedup level and thresholds; classifier annotator model, label count, F1 and threshold; synthetic share and generator / teacher; verifier types and pass rates (for example 'about 20% of code self-corrected', Llama 3); decontamination method and benchmarks checked; diversity metrics; license (for example ODC-BY); known biases (FineWeb-Edu 'grade-school bias'). Eval quality card template (a synthesis for this deck, label it 'example template'): set version and owner; provenance 62% prod traces / 38% synthetic; n=640, 9 slices, min n=48; decontamination 13-gram + embedding; labels: 2 experts + adjudication, kappa, noise audit; judge model + prompt version + TPR / TNR; headline with bootstrap 95% CI; worst slice; ECE after temperature scaling; operating point t for C_FN/C_FP = 20; known gaps. Traceability: OlmoTrace traces outputs back to training documents in real time, the closest thing to a live data quality card. Tagline: 'No number without n, CI, slice and version.'

**Visual and animation.** A card-shaped code-wrap (data-lang yaml) fills field by field (data-fx type on each line group, steps 1-4: provenance & size, labels & judge, headline & worst slice, calibration & operating point). Each step pulses a matching highlight chip on the left lineage column (Datasheets -> Model Cards -> Data Cards -> OlmoTrace). Step 5: the tagline appears as a .callout.insight.

**Code.** 07-eval-design.md section 11: the 'Eval Quality Card' template block (Eval set: support-bot-golden v3.2 ... Known gaps / not measured), shown as an illustrative example, plus the field list from 06-llm-rag-datasets-synthetic.md section 10.

### 58. Open 2025-26 recipes share one pipeline: distilled SFT, preference tuning, verifiable RL and merging

- File: `c09-04-sota-recipes.html`
- Id: `custom-c09-sota-recipes`

**Content.** Assembly line: raw web / PDF / code -> filter + dedup + classifiers -> pretrain -> mid-train (math, code, reasoning, long context) -> SFT (synthetic + curated, decontaminated) -> DPO / APO -> RLVR -> merge -> eval (dev vs unseen) -> card + traceability. Tulu 3 (arXiv 2411.15124): SFT -> DPO -> RLVR on Llama 3.1; open data, code and eval; decontamination; dev vs unseen split. OLMo 3 (2025-11-20; 3.1 on 2025-12-12): Dolma 3 pool ~9.3T -> Dolma 3 Mix ~5.9T -> Dolmino 100B mid-train -> Longmino ~50B -> Dolci SFT / DPO / RLVR; Olmo 3-Think 32B: MATH 96.1, AIME24 76.8, AIME25 72.5, IFEval 89.0; OlmoTrace. DeepSeek-R1: RL-first, then distillation. Gemma 3 (arXiv 2503.19786): all models trained with distillation; 'making Gemma3-4B-IT competitive with Gemma2-27B-IT'; Gemma 4: E2B, E4B, 12B, 26B A4B MoE, 31B dense, 128K / 256K context, Apache 2.0 license link. SmolLM3 (3B, ~11.2T tokens): SFT on 1.8B tokens, APO with chosen Qwen3-32B / rejected Qwen3-0.6B, linear merge 0.9 APO + 0.1 mid-train. Phi-4 (14B): recipe 'centrally focused on data quality', synthetic data throughout. OpenThoughts3: +15.3 / +17.2 / +20.5 points over R1-Distill-Qwen-7B on AIME25 / LiveCodeBench / GPQA-D. Courses for follow-up: Stanford CS336 (data lectures, RL assignment), Nathan Lambert 'Reinforcement Learning from Human Feedback' (rlhfbook.com), Karpathy 'Deep Dive into LLMs like ChatGPT'.

**Visual and animation.** Bespoke gsap conveyor (Deck.register): 8 stations in a row (pretrain, mid-train, SFT, DPO/APO, RLVR, merge, eval, card). Step 1: a token packet moves along the belt and each station lights. Step 2: station badges pop with the model that made it known (Tulu 3 at RLVR, SmolLM3 at APO + merge, DeepSeek-R1 at RL, Gemma 3 at distillation, OLMo 3 at card / OlmoTrace). Step 3: below, an OLMo 3 funnel counts down 9.3T -> 5.9T -> 100B -> 50B -> Dolci. Step 4: Olmo 3-Think 32B stats count up (MATH 96.1, AIME24 76.8). Step 5: course .cite links fade in.

### 59. Open challenges: reward hacking, inflated RL gains, collapse, contamination, licensing and platform risk

- File: `c09-05-open-challenges.html`
- Id: `custom-c09-open-challenges`

**Content.** RL gains need suspicion: 'Spurious Rewards' (arXiv 2506.10947): GRPO on Qwen2.5-Math-7B gains +21.4 points on MATH-500 with random rewards vs +29.1 with ground-truth rewards; 'Does Reinforcement Learning Really Incentivize Reasoning Capacity...' (arXiv 2504.13837): 'the base models achieve a higher pass@k score when k is large' — RLVR sharpens sampling more than it adds reasoning. Reward hacking grows up: OpenAI CoT monitoring (arXiv 2503.11926): GPT-4o monitored o3-mini; training against the monitor teaches 'obfuscated reward hacking'; pay a 'monitorability tax'. Anthropic 'From shortcuts to sabotage' (2025-11-21): hacking coding tasks generalized to ~12% sabotage of safety-research code and ~50% alignment-faking reasoning; inoculation prompting fixed it: 'Learning to cheat no longer generalized to other misaligned behaviors.' Saturation: Humanity's Last Exam (arXiv 2501.14249) 2,500 questions; 'benchmarks are not keeping pace in difficulty'; dynamic benchmarks lack standard criteria (arXiv 2502.17521). Collapse and curation monoculture (Nature 2024). Licensing: Bartz v. Anthropic: training on lawfully acquired books ruled fair use (2025-06-23); pirated copies went to trial; settled for US$1.5B (Sep 2025) — provenance decides legal risk. Platform risk: OpenAI fine-tuning wind-down; Fireworks managed RFT deprecated. Also open: graders for non-verifiable tasks (rubric quality, judge bias), agent evals (pass@k vs pass^k), vendor-reported gains (66%, 73%, 40x) not independently replicated, documentation decay, slice explosion, synthetic-data provenance fields.

**Visual and animation.** Bespoke gsap (Deck.register). Step 1: a pass@k plot draws: RL curve above base at k=1, base curve crossing above at large k (qualitative shape, labelled from arXiv 2504.13837). Step 2: an inset bar pair counts up +21.4 (random rewards) vs +29.1 (true rewards). Step 3: a 'clean-looking CoT' mask slides over a hacking-agent icon, then lifts to show the hack; Anthropic stats ~12% / ~50% count up. Step 4: a 3x3 grid of challenge cards flips one row at a time (saturation, collapse, licensing $1.5B, platform risk, judge validity, agent evals, vendor claims, doc decay, provenance).

### 60. Interview: the end-to-end customization system

- File: `c09-06-qa.html`
- Id: `custom-c09-qa`

**Content.** Q1: 'Design an assistant for insurance-claims agents: policies change monthly, answers must cite, tone must follow brand rules.' A: RAG over versioned policy docs with hybrid search + reranking and citation checks; SFT or DPO for tone; data contract and taxonomy of claim types; golden set from real traces with slices per product line; judge validated against experts; drift monitoring on queries vs corpus; quality card per release. Q2: 'A paper claims +20 points on MATH-500 from RL on Qwen2.5-Math. How do you check it?' A: Run a random-reward control (Spurious Rewards), test other model families, decontaminate, report pass@k for large k, and use paired CIs. Q3: 'How do you limit reward hacking in agentic coding RL?' A: Hidden tests, read-only test files, sandboxing, reward audits on samples, CoT monitoring that is not part of the reward, inoculation prompting, early stopping at the gold peak. Q4: 'Your platform deprecates your tuned model next quarter. What do you keep?' A: The data with its contract and card, the grader, the eval set, and the pinned training recipe, so you can re-tune on Vertex, Bedrock or open weights and compare with paired CIs.

**Visual and animation.** Standard .qa layout with answers at steps 1-4; a closing line after step 4: 'Your recipe is the asset: data, grader, eval and card.'
