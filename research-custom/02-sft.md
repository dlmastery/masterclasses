# 02 - Supervised Fine-Tuning (SFT): State of the Art, October 2026

Research date: 2026-10-23. Versions checked against live docs that day: **TRL v1.16.0** (released 15 Oct 2026), **PEFT v0.21.0**, Transformers v5.20 (the version the TRL docs link to). The web-search budget ran out partway through, so a few items rely on prior knowledge. Those are marked [UNVERIFIED].

---

## 1. Where SFT sits in the customization stack

Flow: **Prompting -> RAG -> SFT (PEFT or full) -> preference/RL (DPO, GRPO) -> distillation/merging -> deploy.**

- SFT minimizes token-level cross-entropy (NLL) on target tokens: `L_SFT(θ) = -Σ_t log p_θ(y_t | y_<t)`. Padding and masked tokens use ignore index `-100` (TRL SFT docs).
- Use it when you need **format, style, tool-calling schema, a domain dialect, or behaviour** that prompting can't enforce reliably. Use RAG for fresh or citable facts.
- Quotable (Google Developers Blog, "Own your AI", 8 Oct 2025): fine-tuning is "the most reliable way to enforce a specific output format and teach the model new knowledge". Also: "You don't have to be an AI expert or data scientist to create a specialized AI model."
- Newer loss variant: **Dynamic Fine-Tuning (DFT)**, from "On the Generalization of SFT: A Reinforcement Learning Perspective with Reward Rectification" (arXiv 2508.05629, 2025). It is available in TRL as `SFTConfig(loss_type="dft")`.

---

## 2. Full fine-tuning vs PEFT

| Method | Paper (arXiv, year) | Core idea | PEFT switch (v0.21.0) |
|---|---|---|---|
| Full FT | n/a | Update every weight. Needs about 16 bytes/param with AdamW mixed precision (rule of thumb) | n/a |
| **LoRA** | Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models" (2106.09685, 2021) | Learn W + (α/r)·BA with rank r ≪ d. Base weights stay frozen | `LoraConfig(r=..., lora_alpha=...)` |
| **QLoRA** | Dettmers et al., "QLoRA: Efficient Finetuning of Quantized LLMs" (2305.14314, 2023) | 4-bit NF4 frozen base + double quantization + paged optimizers, with LoRA on top. Fine-tuned a 65B model on a single 48 GB GPU. Guanaco reached 99.3% of ChatGPT on the Vicuna benchmark | `BitsAndBytesConfig(load_in_4bit=True)` + LoRA (`quantization_config=` in SFTTrainer) |
| **DoRA** | Liu et al., "DoRA: Weight-Decomposed Low-Rank Adaptation" (2402.09353, ICML 2024) | Split W into magnitude and direction. LoRA updates the direction, and a learnable vector holds the magnitude | `use_dora=True` |
| **rsLoRA** | Kalajdzievski, "A Rank Stabilization Scaling Factor for Fine-Tuning with LoRA" (2312.03732, 2023) | Scale by α/√r instead of α/r, so high ranks keep learning | `use_rslora=True` |
| **PiSSA** | Meng et al., "PiSSA: Principal Singular Values and Singular Vectors Adaptation of LLMs" (2404.02948, NeurIPS 2024) | Initialize A and B from the top-r SVD of W. The residual stays frozen. Converges faster than LoRA | `init_lora_weights="pissa"` or `"pissa_niter_[n]"` (fast SVD) |
| Other inits | OLoRA, EVA, CorDA, LoftQ, orthogonal, MiCA | Data- or quantization-aware initialization | `init_lora_weights="olora" / "eva" / "corda" / "loftq" / "orthogonal" / "mica"` |

PEFT doc facts (huggingface.co/docs/peft/developer_guides/lora, v0.21.0):
- DoRA: "decomposes the updates of the weights into two parts, magnitude and direction... can improve the performance of LoRA especially at low ranks." It supports only Linear and Conv2D layers and has "a bigger overhead than pure LoRA, so it is recommended to merge weights for inference."
- rsLoRA "uses `lora_alpha/math.sqrt(r)` as the scaling factor, instead of `lora_alpha/r`."
- LoftQ: pass `loftq_config=LoftQConfig(loftq_bits=4, loftq_iter=1)` together with `init_lora_weights="loftq"`, and do not pass an already-quantized model.

### Key 2025 evidence: "LoRA Without Regret" (Thinking Machines, John Schulman et al., 29 Sep 2025)
URL: https://thinkingmachines.ai/blog/lora/
- On small-to-medium instruction-tuning and reasoning datasets, "LoRA performs the same as full fine-tuning."
- Apply LoRA to **all** weight matrices, especially MLP and MoE layers. Attention-only LoRA underperforms even when the parameter count is matched.
- The best LoRA learning rate is about **10x** the best full-FT learning rate: "the optimal learning rate for FullFT is lower by a factor of 10 than for high-rank LoRAs."
- For RL, even **rank 1** works: "LoRA fully matches the learning performance of FullFT when running policy gradient algorithms."
- LoRA falls behind full FT when the dataset exceeds the adapter's capacity, for example in large continued pretraining.

### Forgetting evidence
- Biderman et al., "LoRA Learns Less and Forgets Less" (arXiv 2405.09673, TMLR 2024). On code and math, full FT beats LoRA on the target domain. LoRA preserves more source-domain ability and acts as a regularizer. [Paper details from prior knowledge, UNVERIFIED this session]

Code: LoRA config with modern options (PEFT v0.21.0 API)
```python
# Source: https://huggingface.co/docs/peft/developer_guides/lora (adapted)
from peft import LoraConfig, get_peft_model

config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules="all-linear",      # LoRA Without Regret: include MLP layers
    lora_dropout=0.05,
    use_rslora=True,                  # alpha/sqrt(r) scaling
    use_dora=False,                   # True -> DoRA (merge before inference)
    init_lora_weights="pissa_niter_4",# PiSSA init via fast SVD
    task_type="CAUSAL_LM",
)
model = get_peft_model(base_model, config)
model.print_trainable_parameters()
```
(`target_modules="all-linear"` is a documented PEFT shortcut. It was not re-checked on the v0.21 page [UNVERIFIED].)

---

## 3. Instruction tuning and chat templates

- **LIMA**, Zhou et al., "LIMA: Less Is More for Alignment" (arXiv 2305.11206, 2023). 1,000 curated examples were enough for strong instruction following (the "superficial alignment hypothesis"). This links data quality to the Data-Centric AI deck. [prior knowledge]
- **Chat template** = the Jinja template in the tokenizer that turns `messages` into role markers and special tokens. If training and inference templates differ, quality drops without any error.
- TRL handles templates: given a conversational dataset, `SFTTrainer` "will automatically apply the chat template". `SFTConfig(chat_template_path="HuggingFaceTB/SmolLM3-3B")` copies another model's template onto a base model.
- EOS gotcha (TRL docs): for base models whose template already exists, such as `Qwen/Qwen2.5-1.5B`, set `eos_token="<|im_end|>"`. Otherwise the model never learns to stop.
- Gemma turn markers (Unsloth docs): `<start_of_turn>user\n` ... `<start_of_turn>model\n`.

TRL dataset formats (verbatim from the TRL SFT docs):
```python
# Conversational language modeling
{"messages": [{"role": "user", "content": "What color is the sky?"},
              {"role": "assistant", "content": "It is blue."}]}
# Conversational prompt-completion
{"prompt": [{"role": "user", "content": "What color is the sky?"}],
 "completion": [{"role": "assistant", "content": "It is blue."}]}
```
SFTTrainer also accepts **tool-calling** data (`tool_calls`, `tool`-role messages, a `tools` column of JSON schemas) and **VLM** data (an `image` or `images` column).

---

## 4. Loss masking and packing (TRL v1.16.0 `SFTConfig`)

**Loss masking**
- `completion_only_loss=None` (default). With prompt-completion data, loss is computed on the completion only. With language-modeling data, loss covers the full sequence.
- `assistant_only_loss=True`: loss only on assistant turns. The chat template must contain `{% generation %}` / `{% endgeneration %}`. TRL "automatically patches the template" for known families such as Qwen3. Since v1.15.0 this also works for vision datasets (needs `transformers>=5.18.0`).
- Pre-tokenized data: if a `labels` column with `-100` exists, it is used as is. Otherwise TRL builds labels from `assistant_masks` / `completion_mask`.
- The older `DataCollatorForCompletionOnlyLM` approach was superseded by these flags [removal version UNVERIFIED].

**Packing** (fewer padding tokens, higher throughput)
- `packing=True`. `max_length` (default 1024) sets the packed sequence length.
- `packing_strategy`: `"bfd"` (default, best-fit decreasing, truncates overflow), `"bfd_split"` (splits overflow sequences), `"wrapped"` (aggressive, cuts mid-sequence).
- `padding_free=True` flattens the batch with no padding (FlashAttention 2/3). It switches on automatically with `bfd` packing, so examples don't attend across boundaries.
- Packing combined with context parallelism raises an error (since v1.11.0).

**Other recent SFT changes in TRL**
- v1.15.0 (8 Oct 2026): fused LM head (no full logits tensor), selective activation checkpointing.
- v1.13.0 (10 Sep 2026): chunked-CE lm_head on tensor cores, about 1.2-1.7x throughput; guide for sequences longer than 1M tokens.
- v1.16.0 (15 Oct 2026): `pad_to_multiple_of="auto"` (128 on AWS Trainium/Neuron).
- SFTConfig defaults that differ from TrainingArguments: `learning_rate=2e-5`, `gradient_checkpointing=True`, `bf16=True`, `logging_steps=10`. The TRL docs advise about 1e-4 when training adapters.

Code: SFT with QLoRA, assistant-only loss and packing (TRL v1.16.0)
```python
# Source: https://huggingface.co/docs/trl/sft_trainer (v1.16.0), combined
import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

args = SFTConfig(
    output_dir="qwen3-sft",
    max_length=2048,
    packing=True, packing_strategy="bfd",   # padding-free BFD packing
    assistant_only_loss=True,                # mask user/system tokens
    learning_rate=1e-4,                      # adapters -> higher LR
    model_init_kwargs={"dtype": torch.bfloat16},
)
trainer = SFTTrainer(
    model="Qwen/Qwen3-0.6B",
    args=args,
    train_dataset=load_dataset("trl-lib/Capybara", split="train"),
    peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear"),
    quantization_config=BitsAndBytesConfig(load_in_4bit=True,
                                           bnb_4bit_quant_type="nf4"),  # QLoRA
)
trainer.train()
```
(The `quantization_config` argument on SFTTrainer is documented in v1.16.0: "Combine with `peft_config` for QLoRA training.")

Teaching point, API drift: the Google codelab "How to fine tune a LLM using Cloud Run Jobs" still passes `dataset_text_field=`, `max_seq_length=`, `tokenizer=`, and `packing=` directly to `SFTTrainer(...)`. That is the pre-1.0 TRL style. In TRL 1.x, these go in `SFTConfig` (`max_length`, `dataset_text_field`, `packing`), and the tokenizer is `processing_class=`. Pin your versions.

---

## 5. Catastrophic forgetting: causes and mitigations

Causes: distribution shift, a high learning rate, too many epochs, narrow data, mismatched chat templates, and drift in the safety/refusal distribution.

Mitigations, cheapest first:
1. **PEFT** (LoRA "forgets less"). Keep the adapter separate and hot-swappable.
2. **Lower LR, 1-3 epochs, early stopping on held-out general benchmarks** (Unsloth guide). Training loss below 0.2 usually means overfitting.
3. **Replay/mixing**: blend 5-20% general instruction data into the domain set [heuristic range, UNVERIFIED].
4. **Scale the adapter down**: Unsloth suggests multiplying alpha by 0.5 to soften an over-fit adapter.
5. **Merge back toward the base** (WiSE-FT-style interpolation, SLERP, TIES; see §6).
6. **On-policy distillation or RL afterwards**. These train on the model's own samples, which tends to shift the distribution less than SFT on off-policy text [claim, UNVERIFIED].

Diagram in words: plot target-task accuracy against general-benchmark accuracy over training steps. Full FT moves right fast but drops a lot. LoRA moves right more slowly and drops less. Merging pulls the point back up and to the left.

---

## 6. Model merging (TIES, DARE, SLERP)

- **Task arithmetic**: Ilharco et al., "Editing Models with Task Arithmetic" (arXiv 2212.04089, ICLR 2023). Task vector τ = θ_ft − θ_base. Vectors can be added or negated.
- **TIES-Merging**: Yadav et al., "TIES-Merging: Resolving Interference When Merging Models" (arXiv 2306.01708, NeurIPS 2023). Three steps (PEFT docs): "redundant parameters are trimmed, then conflicting signs are resolved into an aggregated vector, and finally the parameters whose signs are the same as the aggregate sign are averaged."
- **DARE**: Yu et al., "Language Models are Super Mario: Absorbing Abilities from Homologous Models as a Free Lunch" (arXiv 2311.03099, ICML 2024). Randomly drop a fraction p of delta parameters and rescale the rest by 1/(1−p). It is usually combined with TIES (`dare_ties`).
- **SLERP**: spherical linear interpolation (Shoemake 1985, applied to weights). It merges exactly two models along the arc, which preserves the norm and geometry better than a straight linear average.
- Tool: **mergekit** (github.com/arcee-ai/mergekit, LGPL-3.0). Methods include `linear, slerp, nuslerp, multislerp, karcher, task_arithmetic, ties, dare_linear, dare_ties, della, della_linear, breadcrumbs, breadcrumbs_ties, sce, model_stock, nearswap, arcee_fusion, passthrough`. CLI: `mergekit-yaml config.yml ./out [--cuda] [--lazy-unpickle] [--allow-crimes]`.
- Real-world example: merges dominated the 2024 Open LLM Leaderboard. Arcee and Sakana AI's "Evolutionary Optimization of Model Merging Recipes" (arXiv 2403.13187, 2024) are further examples [Sakana detail from prior knowledge].

Code: merging LoRA adapters with TIES/DARE in PEFT (verbatim, PEFT v0.21.0 model_merging guide)
```python
from peft import PeftConfig, PeftModel
from transformers import AutoModelForCausalLM

config = PeftConfig.from_pretrained("smangrul/tinyllama_lora_norobots")
model = AutoModelForCausalLM.from_pretrained(config.base_model_name_or_path,
                                             load_in_4bit=True, device_map="auto").eval()
model = PeftModel.from_pretrained(model, "smangrul/tinyllama_lora_norobots", adapter_name="norobots")
_ = model.load_adapter("smangrul/tinyllama_lora_sql", adapter_name="sql")
_ = model.load_adapter("smangrul/tinyllama_lora_adcopy", adapter_name="adcopy")

adapters, weights = ["norobots", "adcopy", "sql"], [2.0, 0.3, 0.7]
model.add_weighted_adapter(adapters, weights, "merge",
                           combination_type="dare_ties", density=0.2)
model.set_adapter("merge")
```
(The doc's full snippet also resizes embeddings to 32005 for added special tokens. Warn students that **special tokens added at the same embedding index collide** when merging fully fine-tuned models.)

---

## 7. Distillation

- Classic KD: Hinton et al., "Distilling the Knowledge in a Neural Network" (arXiv 1503.02531, 2015).
- **Sequence-level / "SFT on teacher outputs"**: the dominant 2025-26 pattern. DeepSeek-R1 (arXiv 2501.12948, Jan 2025) released Qwen- and Llama-based "R1-Distill" models trained by SFT on about 800k R1-generated samples [count from prior knowledge, UNVERIFIED]. This connects to the "generate -> select" part of the dataset lifecycle.
- "Distilling Step-by-Step!" (Hsieh et al., arXiv 2305.02301, ACL Findings 2023): rationales as extra supervision.
- **On-policy distillation / GKD**: Agarwal et al., "On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes" (arXiv 2306.13649, ICLR 2024). The student generates, and the teacher scores every token. This fixes the train/inference mismatch.
- **TRL `DistillationTrainer`** became stable in TRL v1.10.0 (13 Aug 2026). It uses on-policy generation (optional vLLM colocate or server mode) and a chunked generalized JSD loss. `beta` selects the divergence: 0.0 = forward KL, 1.0 = reverse KL (default), 0.5 = JSD. Teacher and student **must share a vocabulary**. It supports tool-using agent trajectories, with tool-result tokens masked. `AsyncDistillationTrainer` scores against a teacher served over HTTP.

Code (verbatim, https://huggingface.co/docs/trl/main/en/distillation_trainer)
```python
from datasets import load_dataset
from trl import DistillationTrainer
from peft import LoraConfig

dataset = load_dataset("trl-lib/ultrafeedback-prompt", split="train")  # prompt-only
trainer = DistillationTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    teacher_model="Qwen/Qwen2.5-1.5B-Instruct",
    train_dataset=dataset,
    peft_config=LoraConfig(),
)
trainer.train()
```
CLI: `trl distillation --model_name_or_path ... --teacher_model_name_or_path ... --dataset_name trl-lib/ultrafeedback-prompt --use_peft --lora_r 64 --lora_alpha 16`

---

## 8. Tooling landscape (status as of Oct 2026)

| Tool | Status / version | Signature feature | Entry point |
|---|---|---|---|
| **HF TRL** | v1.16.0 (15 Oct 2026) | SFT, DPO, GRPO and Distillation trainers. Packing (BFD), assistant-only loss, DFT loss, VLM, tool-calling | `from trl import SFTTrainer, SFTConfig`; CLI `trl sft ...` |
| **HF PEFT** | v0.21.0 | LoRA, DoRA, rsLoRA, PiSSA, EVA, CorDA, LoftQ, merging (`add_weighted_adapter`) | `from peft import LoraConfig, get_peft_model` |
| **Unsloth** | Active. Gemma 4 support, "Unsloth Studio" web UI (`unsloth studio`) | Custom Triton kernels. README claim: "2× faster with 70% less VRAM with no accuracy loss" | `from unsloth import FastLanguageModel` |
| **Axolotl** | Active (latest updates 2026/10). Python ≥3.12, PyTorch ≥2.13 | One YAML for full/LoRA/QLoRA/QAT/DPO/GRPO; multipacking, sequence parallelism, NVFP4 LoRA, MoE expert parallelism, GGUF export | `axolotl fetch examples` -> `axolotl train examples/llama-3/lora-1b.yml` |
| **LLaMA-Factory** | Active. Paper: "LlamaFactory: Unified Efficient Fine-Tuning of 100+ Language Models" (ACL 2024 System Demos) | Web UI plus CLI. Full, Freeze, LoRA, QLoRA, OFT, QOFT; DoRA, PiSSA, rsLoRA, LoRA+, GaLore, APOLLO, Muon; Megatron-core backend | `llamafactory-cli train examples/train_lora/qwen3_lora_sft.yaml`, `llamafactory-cli webui`, `llamafactory-cli export ...` |
| **torchtune** | **No longer actively maintained.** README says development "wound down in 2025" (see github.com/meta-pytorch/torchtune/issues/2883). Last named release v0.4.0 | PyTorch-native recipes | Historical. Do not recommend for new projects |
| **Keras / KerasHub** | Gemma LoRA tutorial still online, but the page now says it is deprecated and points to gemma.ai | `backbone.enable_lora(rank=4)`; runs on JAX, TF or PyTorch backends | `keras_hub.models.Gemma3CausalLM.from_preset("gemma3_instruct_1b")` |
| **mergekit** | LGPL-3.0 | 18+ merge methods | `mergekit-yaml` |

Code: Unsloth LoRA (arguments verbatim from https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide)
```python
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/gemma-3-1b-it",   # example id [UNVERIFIED exact repo]
    max_seq_length=2048, load_in_4bit=True)   # 4-bit -> QLoRA
model = FastLanguageModel.get_peft_model(
    model, r=16,
    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
    lora_alpha=16, lora_dropout=0, bias="none",
    use_gradient_checkpointing="unsloth", random_state=3407,
    use_rslora=False, loftq_config=None)
# after building a TRL SFTTrainer:
from unsloth.chat_templates import train_on_responses_only
trainer = train_on_responses_only(trainer,
    instruction_part="<start_of_turn>user\n", response_part="<start_of_turn>model\n")
```
Unsloth guidance: rank 16 or 32, `lora_alpha = r` or `2*r`, LR 2e-4, 1-3 epochs.

Code: KerasHub Gemma LoRA (from https://ai.google.dev/gemma/docs/core/lora_tuning)
```python
import keras, keras_hub
gemma_lm = keras_hub.models.Gemma3CausalLM.from_preset("gemma3_instruct_1b")
gemma_lm.backbone.enable_lora(rank=4)          # freezes base, adds LoRA
gemma_lm.preprocessor.sequence_length = 256
optimizer = keras.optimizers.AdamW(learning_rate=5e-5, weight_decay=0.01)
optimizer.exclude_from_weight_decay(var_names=["bias", "scale"])
gemma_lm.compile(
    loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    optimizer=optimizer,
    weighted_metrics=[keras.metrics.SparseCategoricalAccuracy()],
)
gemma_lm.fit(data, epochs=1, batch_size=1)
```
(`enable_lora`, `compile` and `fit` were confirmed on the page. The sequence_length, AdamW values and exclude lines follow the tutorial's known structure but were not re-quoted [UNVERIFIED exact values].)

---

## 9. Google codelabs, Gemma docs and Kaggle/Colab notebooks (exact titles + URLs)

1. **Codelab: "How to fine tune a LLM using Cloud Run Jobs"**. https://codelabs.developers.google.com/codelabs/cloud-run/how-to-fine-tune-model-cloud-run-jobs. Fine-tunes `google/gemma-3-1b-it` on `KomeijiForce/Text2Emoji` on a single **L4 GPU** in a Cloud Run job, then serves the result with vLLM on Cloud Run. LoRA: `r=8, lora_alpha=16, lora_dropout=0.1, target_modules=["q_proj","v_proj"]`. An earlier revision used gemma-2b with text-to-SQL. Job command (verbatim excerpt): `gcloud run jobs create $JOB_NAME --region $REGION --image ... --set-secrets HF_TOKEN=$SECRET_ID:latest --cpu 8.0 --memory 32Gi --gpu 1 --add-volume name=finetuned_model,type=cloud-storage,bucket=$BUCKET_NAME ...`
2. **"Fine-tune Gemma in Keras using LoRA"** (Google AI for Developers). https://ai.google.dev/gemma/docs/core/lora_tuning. Colab: https://colab.research.google.com/github/google-gemma/cookbook/blob/main/docs/core/lora_tuning.ipynb. Kaggle: https://kaggle.com/kernels/welcome?src=https://github.com/google-gemma/cookbook/blob/main/docs/core/lora_tuning.ipynb. The page is now marked deprecated and points to gemma.ai.
3. **"Fine-Tune Gemma using Hugging Face Transformers and QloRA"**. https://ai.google.dev/gemma/docs/core/huggingface_text_finetune_qlora. Now defaults to **`google/gemma-4-E2B`**, with E4B, 12B, 31B and 26B-A4B as options. Installs `transformers>=5.10.1`, `peft>=0.19.0`, unpinned `trl`. LoRA r=16, α=16, dropout 0.05. Saves `lm_head`/`embed_tokens` because special tokens are trained. SFTConfig uses max_length 512, 3 epochs, LR 2e-4, constant schedule, `adamw_torch_fused`.
4. **"Fine-tuning Gemma using JAX and Flax"**. https://ai.google.dev/gemma/docs/jax_finetune (English-French on MTNT; free Colab hardware isn't enough).
5. **Blog + Colab: "Own your AI: Learn how to fine-tune Gemma 3 270M and run it on-device"** (Google Developers Blog, 8 Oct 2025, Ballantyne/Mayes/Quan). https://developers.googleblog.com/en/own-your-ai-fine-tune-gemma-3-270m-for-on-device/. Colab: https://colab.research.google.com/github/google-gemini/gemma-cookbook/blob/main/Demos/Emoji-Gemma-on-Web/resources/Fine_tune_Gemma_3_270M_for_emoji_generation.ipynb. Pipeline: QLoRA on a free T4 "in minutes", then 4-bit quantization (under 300 MB), then LiteRT/MediaPipe LLM Inference API or ONNX/Transformers.js with WebGPU in the browser.
6. **Kaggle (Unsloth): Gemma 4 31B fine-tuning notebook**. https://www.kaggle.com/code/danielhanchen/gemma4-31b-unsloth (linked from https://unsloth.ai/docs/get-started/unsloth-notebooks; contents not opened [UNVERIFIED runtime]).
7. GKE tutorial "Fine-tune Gemma open models using multiple GPUs on GKE". https://docs.cloud.google.com/kubernetes-engine/docs/tutorials/finetune-gemma-gpu [English title inferred from a Japanese result, UNVERIFIED].
- No official Google-authored Gemma fine-tuning notebook on kaggle.com/code turned up in search. The official notebooks open into Kaggle through the "kernels/welcome?src=" GitHub links above.
- Gemma 4 release date and full lineup: [UNVERIFIED this session]. The model IDs above come from the official QLoRA page.

---

## 10. Real-world examples

- **Google / Gemma ecosystem**: Gemma 3 270M emoji translator running fully on-device in the browser (blog above). Cloud Run Jobs L4 fine-tuning followed by vLLM serving (codelab).
- **DeepSeek-R1-Distill** (Jan 2025): reasoning moved into small dense models through SFT on teacher traces.
- **Thinking Machines "Tinker"** (2025): managed LoRA fine-tuning API, from the same team as "LoRA Without Regret" [product details UNVERIFIED].
- **Multi-LoRA serving**: vLLM and LoRAX serve many adapters on one base model, so per-customer adapters cost close to nothing [UNVERIFIED specifics].
- **Hugging Face SmolLM3**: its chat template is the reference TRL uses for `{% generation %}` masking.
- **Arcee / Sakana**: commercial and research use of model merging (mergekit; evolutionary merging).

---

## 11. Open challenges (Oct 2026)

1. **Forgetting vs specialization** is still measured ad hoc. There is no standard "general-capability regression card" for adapters.
2. **Chat-template fragility**: template mismatches, missing EOS, and `{% generation %}` tags absent from many model templates.
3. **The LoRA capacity ceiling** on large or knowledge-heavy data. When should you switch to full FT?
4. **Merging theory**: why sign conflicts matter, and how to merge models with different tokenizers or architectures.
5. **SFT vs RL roles**: does SFT memorize while RL generalizes? This motivates DFT, on-policy distillation, and SFT-then-GRPO pipelines.
6. **Data quality is the bottleneck** (LIMA). This feeds directly into the Data-Centric lifecycle: design -> generate -> select -> curate -> label -> denoise -> quality card.
7. **Licensing and provenance** of distilled data (teacher terms of service) and of merged weights.
8. **API churn**: TRL 0.x to 1.x renamed arguments. Codelabs lag behind, so reproducibility needs pinned versions.

---

## 12. Slide ideas (8)

1. **"The Customization Ladder"**. A staircase: Prompt -> RAG -> LoRA -> Full FT -> RL -> Distill/Merge, with cost and control growing at each step. Animation: a ball climbs while a "$/control" meter fills.
2. **"LoRA in one picture"**. A frozen W (grey) with skinny B·A matrices (colored). Animation: r shrinks and expands while the trainable-parameter percentage updates live. Add rsLoRA's α/√r label as an overlay.
3. **"The LoRA family tree"**. LoRA branching to QLoRA (4-bit base), DoRA (magnitude/direction vectors), rsLoRA (scaling), PiSSA (SVD init). Each branch shows its one-line `LoraConfig` flag.
4. **"Where does the loss go?"**. A token strip with system/user tokens greyed (-100) and assistant tokens highlighted. Toggle between `completion_only_loss` and `assistant_only_loss`.
5. **"Packing: Tetris for tokens"**. Padded batch vs BFD-packed batch. Animation: sequences fall into bins and the padding percentage drops. Mention padding-free attention.
6. **"Forgetting frontier"**. Scatter of target accuracy vs general accuracy for full FT, LoRA and merged models (the "LoRA Learns Less and Forgets Less" framing). Animation: the merge arrow pulls a point back.
7. **"Merging: TIES in 3 steps"**. Three task vectors as colored arrows, then trim, elect sign, and average the agreeing parts. A SLERP arc next to a linear chord as a side panel.
8. **"Distillation: off-policy vs on-policy"**. Left: the student copies teacher text. Right: the student writes and the teacher grades each token (GKD). Show `beta` as a slider from forward KL to reverse KL.
9. **"Tool map 2026"**. A 2x2 of code-first vs config/UI against single-GPU vs multi-node: TRL/PEFT, Unsloth, Axolotl, LLaMA-Factory, KerasHub, with torchtune greyed out as "unmaintained".
10. **"Gemma, from Colab to phone"**. Pipeline: 270M QLoRA on a free T4, then 4-bit, then LiteRT/MediaPipe, then the browser. Use a live demo GIF of the emoji translator.

---

## Sources
- TRL SFT Trainer docs (v1.16.0): https://huggingface.co/docs/trl/sft_trainer
- TRL releases: https://github.com/huggingface/trl/releases
- TRL Distillation Trainer: https://huggingface.co/docs/trl/main/en/distillation_trainer
- PEFT LoRA guide (v0.21.0): https://huggingface.co/docs/peft/developer_guides/lora
- PEFT model merging: https://huggingface.co/docs/peft/developer_guides/model_merging
- LoRA Without Regret: https://thinkingmachines.ai/blog/lora/
- Unsloth: https://github.com/unslothai/unsloth ; https://unsloth.ai/docs/get-started/fine-tuning-llms-guide/lora-hyperparameters-guide ; https://unsloth.ai/docs/get-started/unsloth-notebooks
- Axolotl: https://github.com/axolotl-ai-cloud/axolotl
- LLaMA-Factory: https://github.com/hiyouga/LlamaFactory
- torchtune: https://github.com/pytorch/torchtune
- mergekit: https://github.com/arcee-ai/mergekit
- Google: codelab, ai.google.dev pages and blog URLs listed in §9
- Papers: arXiv 2106.09685, 2305.14314, 2402.09353, 2312.03732, 2404.02948, 2405.09673, 2305.11206, 2212.04089, 2306.01708, 2311.03099, 2403.13187, 1503.02531, 2305.02301, 2306.13649, 2501.12948, 2508.05629
