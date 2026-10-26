# Hands-on labs: SFT with TRL + PEFT (LoRA/QLoRA), Unsloth, and Vertex AI Gemini tuning

Research date: 2026-10-23. Every import, class, parameter and default in these labs was checked against the library **source code at the release tag** on GitHub. The source files are cited inline as `repo@tag:path:line`. pip is blocked on the research machine, so **none of the code was executed here**. Every "Expected output" block is **illustrative**. The parameter counts in those blocks were computed by hand from the models' `config.json` files. Losses, timings and accuracy numbers are realistic placeholders, not measurements.

This file builds on `research-custom/02-sft.md` and `09-critic-corrections.md`. It does not repeat their theory (LoRA family, merging maths, the tool landscape). It adds runnable code, the exact errors students will hit, and papers from 2026-07-23 to 2026-10-23.

---

## 0. Pinned versions (PyPI JSON, fetched 2026-10-23)

| Package | Latest | Uploaded | Notes |
|---|---|---|---|
| `trl` | **1.16.0** | 2026-10-15 | needs Python >=3.11. Deps: `transformers>=4.56.2`, `datasets>=4.7.0`, `accelerate>=1.10.1` (`trl@v1.16.0:pyproject.toml:30-42`) |
| `peft` | **0.21.2** | 2026-10-01 | |
| `transformers` | **5.20.2** | 2026-10-19 | |
| `datasets` | **5.1.0** | 2026-10-05 | |
| `accelerate` | **1.15.0** | 2026-09-09 | |
| `bitsandbytes` | **0.50.2** | 2026-08-27 | |
| `torch` | **2.14.1** | 2026-09-30 | |
| `unsloth` | **2026.10.8** | 2026-10-23 | GitHub release tag `v0.1.910-beta` (2026-10-23). Python <3.15 |
| `google-genai` | **2.33.0** | 2026-10-23 | |
| `vllm` | 0.32.0 | 2026-10-18 | used only for serving in Lab 5 |
| `kernels` | 0.17.2 | 2026-10-02 | for `attn_implementation="kernels-community/flash-attn2"` |

One pin line for every HF lab:
```bash
pip install "trl==1.16.0" "peft==0.21.2" "transformers==5.20.2" "datasets==5.1.0" "accelerate==1.15.0" "bitsandbytes==0.50.2" "torch==2.14.1"
```

Business dataset used in Labs 2, 6, 7 and 8 (verified through the HF datasets-server API): **`bitext/Bitext-customer-support-llm-chatbot-training-dataset`**. It has 26,872 rows, license CDLA-Sharing-1.0, and columns `flags, instruction, category, intent, response`. There are 11 categories. `REFUND` has 2,992 rows across the intents `get_refund` (997), `track_refund` (998) and `check_refund_policy` (997). There are 27 intents in total. Responses contain literal placeholders such as `{{Order Number}}`.

Models used (HF API): `Qwen/Qwen3-0.6B` (apache-2.0, not gated; 28 layers, hidden 1024, tied embeddings), `Qwen/Qwen3-4B-Instruct-2507` (apache-2.0), and `unsloth/gemma-4-E2B-it` (Gemma 4 is apache-2.0, not gated).

---

## Lab 1: Look before you train. Render the chat template and the assistant-loss mask (HR policy assistant)

> **Verifier (2026-10-23):** VERIFIED against trl 1.16.0 (`get_training_chat_template` export, Qwen3 patch, Gemma 4 NOT patched) and transformers 5.20.2 (`return_assistant_tokens_mask` ValueError) source. Token counts in the output remain illustrative.

**Goal.** See exactly which tokens SFT will train on before spending GPU time. This lab runs on CPU in seconds.

**Prerequisites.** `pip install "trl==1.16.0" "transformers==5.20.2"`. No GPU and no env vars needed. `HF_TOKEN` is needed only for gated models.

```python
# lab1_inspect_mask.py  - Acme HR policy assistant: what does SFT actually train on?
from transformers import AutoTokenizer
from trl import get_training_chat_template

MODEL = "Qwen/Qwen3-0.6B"
tok = AutoTokenizer.from_pretrained(MODEL)

messages = [
    {"role": "system", "content": "You are Acme HR's policy assistant. Always cite the policy ID."},
    {"role": "user", "content": "How much paid parental leave do I get?"},
    {"role": "assistant", "content": "Full-time employees get 16 weeks of paid parental leave (HR-PL-004)."},
    {"role": "user", "content": "Can I split it into blocks?"},
    {"role": "assistant", "content": "Yes, up to 3 blocks within 12 months of the birth or adoption (HR-PL-004 s.3)."},
]

# 1) Original template vs TRL's training template (adds {% generation %} + prefix-preservation)
train_tpl = get_training_chat_template(tok)          # None => template is already training-ready
print("TRL patched the template:", train_tpl is not None)
orig = tok.apply_chat_template(messages, tokenize=False)
patched = tok.apply_chat_template(messages, tokenize=False, chat_template=train_tpl)
print("Original == patched rendering:", orig == patched)

# 2) The assistant mask that SFTConfig(assistant_only_loss=True) will turn into labels=-100
out = tok.apply_chat_template(messages, chat_template=train_tpl, tokenize=True,
                              return_dict=True, return_assistant_tokens_mask=True)
ids, mask = out["input_ids"], out["assistant_masks"]
print(f"tokens={len(ids)} trained={sum(mask)} ({sum(mask) / len(ids):.0%})")

# 3) Print contiguous spans: TRAIN = contributes to loss, mask = ignored (-100)
spans, cur, cur_m = [], [], mask[0]
for t, m in zip(ids, mask):
    if m != cur_m:
        spans.append((cur_m, tok.decode(cur)))
        cur, cur_m = [], m
    cur.append(t)
spans.append((cur_m, tok.decode(cur)))
for m, text in spans:
    print(("TRAIN >> " if m else "mask  .. ") + repr(text))

# 4) The inference prompt must reproduce what training saw (empty think block for Qwen3)
prompt = tok.apply_chat_template(messages[:2], add_generation_prompt=True,
                                 tokenize=False, enable_thinking=False)
print("Inference prompt tail:", repr(prompt[-40:]))
```

**Run.**
```bash
python lab1_inspect_mask.py
```

**Expected output (illustrative; token counts are approximate).**
```
TRL patched the template: True
Original == patched rendering: False
tokens=118 trained=46 (39%)
mask  .. "<|im_start|>system\nYou are Acme HR's policy assistant. Always cite the policy ID.<|im_end|>\n<|im_start|>user\nHow much paid parental leave do I get?<|im_end|>\n<|im_start|>assistant\n"
TRAIN >> '<think>\n\n</think>\n\nFull-time employees get 16 weeks of paid parental leave (HR-PL-004).<|im_end|>\n'
mask  .. '<|im_start|>user\nCan I split it into blocks?<|im_end|>\n<|im_start|>assistant\n'
TRAIN >> '<think>\n\n</think>\n\nYes, up to 3 blocks within 12 months of the birth or adoption (HR-PL-004 s.3).<|im_end|>\n'
Inference prompt tail: 'ion leave do I get?<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
```

**Walk-through of the key lines.**
- `get_training_chat_template(tok)`: returns a patched Jinja string for known families, or `None` if the template already has `{% generation %}` and is prefix-preserving (`trl@v1.16.0:trl/chat_template_utils.py:1076-1155`). Qwen3 maps to `qwen3_training.jinja` (same file, lines 1227-1228).
- `orig == patched` is **False**. The stock Qwen3 template drops the `<think>` block from earlier assistant turns, so history renders differently from the final turn. The TRL docstring shows the "think tags missing" case (`chat_template_utils.py:1099-1125`). The patch, documented in `trl/chat_templates/README.md`, "Removed the loop.index0 > ns.last_query_index conditional; always include thinking block".
- `return_assistant_tokens_mask=True` requires `return_dict=True` and `tokenize=True`. Otherwise you get a ValueError (`transformers@v5.20.2:src/transformers/tokenization_utils_base.py:3102-3103`).
- The TRAIN spans include `<|im_end|>\n`, because the patched template puts the end-of-turn token *inside* `{% generation %}` (`qwen3_training.jinja`, lines 51-73). Without it the model never learns to stop. TRL now warns when a template leaves the stop token out (`sft_trainer.py:946-957`).
- `enable_thinking=False` makes the inference prompt prefill `<think>\n\n</think>\n\n` (`qwen3_training.jinja`, lines 86-90). That matches what training saw.

**Common errors.**
1. `ValueError: The chat template is not training-compatible (missing prefix-preservation or `{% generation %}` markers) and patching is not supported for this template. Please manually modify the chat template for training.` (`chat_template_utils.py:1249-1252`). You get this on any family TRL does not patch. **Gemma 4 is not in the patch list**: zero `gemma4` matches in lines 1080-1252, even though `gemma4*.jinja` files exist for response parsing. Fix: use a prompt-completion dataset (Lab 3), use Unsloth's `train_on_responses_only` (Lab 6), or add `{% generation %}`/`{% endgeneration %}` to the template yourself.
2. `ValueError: `return_assistant_tokens_mask=True` requires `return_dict=True` and `tokenize=True``. Fix: pass both.
3. A mask that is all zeros when you call `apply_chat_template(..., return_assistant_tokens_mask=True)` **without** `chat_template=train_tpl`. Transformers logs a warning only. In the trainer this becomes `RuntimeError: You're using `assistant_only_loss=True`, but at least one example has no assistant tokens...` (`sft_trainer.py:1387-1393`).

**Best practice.** Make this script a CI check on your dataset. Fail the build if any row has `sum(mask)==0`, or if the trained span does not end with the EOS token.

**Variation.** Add a `tools` column and an assistant `tool_calls` turn, such as `lookup_policy(policy_id="HR-PL-004")`. Confirm that the `<tool_call>` JSON is inside the TRAIN span (`qwen3_training.jinja`, lines 53-70) and that the `tool` turn is masked.

---

## Lab 2: LoRA SFT with TRL on a real refund-support dataset (assistant-only loss + BFD packing)

> **Verifier (2026-10-23):** VERIFIED against trl 1.16.0 (`SFTConfig` fields, `packing_strategy` bfd, float32 default, padding-free rule), peft 0.21.2 (qwen3 default `q_proj,v_proj`), transformers 5.20.2 (`warmup_steps: float`, no `warmup_ratio`) source. Trainable count 10,092,544 recomputed from config.json. Losses illustrative.

**Goal.** Train a refund assistant for an online store. Use `Qwen3-0.6B` + LoRA on the 2,992 Bitext `REFUND` rows, with masking and packing set correctly.

**Prerequisites.** One GPU with at least 12 GB (T4, L4 or A10G). The pin line from section 0, plus optionally `pip install "kernels==0.17.2"` for FlashAttention kernels on Ampere or newer. Set `export HF_TOKEN=...` (optional).

Adapted from: TRL docs, "SFT Trainer" (https://huggingface.co/docs/trl/sft_trainer), sections "Train on assistant messages only" and "Packing", and TRL `trl/scripts/sft.py`, "LoRA" usage block (`trl@v1.16.0:trl/scripts/sft.py:42-61`).

```python
# lab2_sft_lora_refund.py  - Refund assistant: Qwen3-0.6B + LoRA, assistant-only loss, BFD packing
import torch
from datasets import load_dataset
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

SYSTEM = ("You are the refunds assistant for an online store. Follow the refund policy, "
          "keep placeholders like {{Order Number}} unchanged, and never promise an amount.")

raw = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset", split="train")
raw = raw.filter(lambda r: r["category"] == "REFUND")          # 2,992 rows, 3 intents

def to_messages(r):
    return {"messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": r["instruction"]},
                         {"role": "assistant", "content": r["response"]}]}

ds = raw.map(to_messages, remove_columns=raw.column_names).train_test_split(test_size=0.05, seed=42)

args = SFTConfig(
    output_dir="qwen3-0.6b-refund-lora",
    model_init_kwargs={"dtype": torch.bfloat16},  # string model ids otherwise load in float32
    assistant_only_loss=True,                     # loss on assistant turns only (TRL patches Qwen3)
    max_length=1024,
    packing=True, packing_strategy="bfd",         # BFD packing => padding-free batches
    learning_rate=2e-4,                           # ~10x the full-FT default (2e-5)
    num_train_epochs=2,
    per_device_train_batch_size=8,
    gradient_accumulation_steps=2,
    lr_scheduler_type="cosine",
    warmup_steps=0.03,                            # float in [0,1) = ratio (transformers v5)
    eval_strategy="steps", eval_steps=50, save_steps=50,
    load_best_model_at_end=True, metric_for_best_model="eval_loss",
    logging_steps=10, report_to="none", seed=42,
)
peft_config = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                         target_modules="all-linear", task_type="CAUSAL_LM")

trainer = SFTTrainer(model="Qwen/Qwen3-0.6B", args=args,
                     train_dataset=ds["train"], eval_dataset=ds["test"], peft_config=peft_config)
trainer.model.print_trainable_parameters()
trainer.train()
trainer.save_model("qwen3-0.6b-refund-lora/final")   # adapter only (~40 MB), not the base
print(trainer.evaluate())
```

**Run.**
```bash
python lab2_sft_lora_refund.py
# multi-GPU: accelerate launch --num_processes 2 lab2_sft_lora_refund.py
```

**Expected output (illustrative).** The parameter count is exact arithmetic: r·(in+out) per module, 7 modules, 28 layers, lm_head excluded by `all-linear`, tied embeddings.
```
trainable params: 10,092,544 || all params: 606,142,464 || trainable%: 1.6650
{'loss': 1.912, 'grad_norm': 1.21, 'learning_rate': 0.000199, 'entropy': 1.64, 'num_tokens': 81920.0, 'mean_token_accuracy': 0.611, 'epoch': 0.09}
...
{'eval_loss': 0.583, 'eval_entropy': 0.71, 'eval_mean_token_accuracy': 0.842, 'epoch': 1.0}
...
{'train_runtime': 610.2, 'train_loss': 0.71, 'epoch': 2.0}
{'eval_loss': 0.561, 'eval_mean_token_accuracy': 0.848, ...}
```
`entropy`, `mean_token_accuracy` and `num_tokens` are the extra metrics TRL logs (`sft_trainer.py`, `_metrics[mode][...]` keys).

**Walk-through of the key lines.**
- `model_init_kwargs={"dtype": torch.bfloat16}`: if `dtype` is not set, a string model id "defaults to `float32`. This differs from `from_pretrained`, where (since Transformers v5) the dtype is inferred" (`sft_trainer.py:544-546`). That doubles memory without any warning.
- `assistant_only_loss=True`: `sft_trainer.py:933-943` raises if the data is not conversational, then swaps in the training template. Labels are built in `build_labels`: a token is kept only if `all(masks)`, otherwise it becomes -100 (`sft_trainer.py:1407-1430`).
- `packing=True, packing_strategy="bfd"`: this switches on padding-free mode automatically, `self.padding_free = args.padding_free or (args.packing and args.packing_strategy in {"bfd","bfd_split"})` (`sft_trainer.py:913-916`). The TRL memory docs say packing is "available only for SFT training and setups that use FlashAttention (or its variants)" (`docs/source/reducing_memory_usage.md:66`). On Ampere or newer, add `"attn_implementation": "kernels-community/flash-attn2"` to `model_init_kwargs` (the pattern from the same doc, line 151).
- `learning_rate=2e-4`: the SFTConfig default is `2e-5` (`trl@v1.16.0:trl/trainer/sft_config.py:140-143`), which is tuned for full FT. Adapters need about 10x more ("LoRA Without Regret"; harmonized in critic note C27).
- `target_modules="all-linear"`: if you leave it out, PEFT falls back to the per-architecture default, which for `qwen3` is **only** `["q_proj","v_proj"]` (`peft@v0.21.2:src/peft/utils/constants.py:104`). That gives 2,293,760 trainable params (0.38%) instead of 10.1M, and attention-only LoRA underperforms.
- `trainer.save_model(...)` writes `adapter_model.safetensors` + `adapter_config.json`. Lab 5 merges them.

**Common errors.**
1. `TypeError: SFTTrainer.__init__() got an unexpected keyword argument 'tokenizer'`. You copied a pre-1.0 tutorial, such as the Cloud Run Jobs codelab (critic note C21). Fix: `processing_class=tok` (`sft_trainer.py:638`).
2. `TypeError: SFTConfig.__init__() got an unexpected keyword argument 'max_seq_length'`. Fix: `max_length=`. The string `max_seq_length` appears nowhere in `sft_config.py` v1.16.0.
3. `TypeError: SFTConfig.__init__() got an unexpected keyword argument 'warmup_ratio'`. `warmup_ratio` no longer exists in `transformers@v5.20.2:training_args.py`. `warmup_steps` is now a `float` that accepts "a float in [0, 1) (ratio of total steps)" (lines 792-797).
4. `ValueError: --load_best_model_at_end requires the saving steps to be a multiple of the evaluation steps...` (`training_args.py:1712-1725`). Fix: make `save_steps` a multiple of `eval_steps`.

**Best practice.** Hold out by **intent**, not only at random, so you can measure generalisation to unseen phrasings. Keep `eval_packing` at its default, which is the same as `packing` (`sft_config.py:255-258`). Then eval loss is computed on the same token layout as training.

**Variation.** Set `loss_type="dft"` for Dynamic Fine-Tuning (choices `nll|dft`, `sft_config.py:283-289`) and compare eval loss with Lab 4's task metrics. Another variation: `use_rslora=True` with `r=64` (`peft@v0.21.2:src/peft/tuners/lora/config.py:661`).

---

## Lab 3: QLoRA on a 4B model for insurance-claim JSON extraction (prompt-completion format)

> **Verifier (2026-10-23):** VERIFIED against trl 1.16.0 (`SFTTrainer(quantization_config=, peft_config=)`, formatting-func error) and transformers 5.20.2 (`BitsAndBytesConfig` fp4 default) source. Trainable count 33,030,144 recomputed. Still UNVERIFIED: exact T4 bf16 error text.

**Goal.** Fine-tune `Qwen3-4B-Instruct-2507` in 4-bit NF4 to turn adjuster notes into a strict JSON record. Use the prompt-completion format, which masks the prompt **without depending on template patching**.

**Prerequisites.** One GPU with 16-24 GB (T4 16 GB works with `per_device_train_batch_size=2`). Same pins. Data: `claims_train.jsonl` / `claims_val.jsonl` from your claims system. **The example rows below are made up for the lab, not real data**:
```json
{"prompt":[{"role":"system","content":"Extract the claim as JSON with keys loss_type, severity, needs_adjuster, policy_section."},{"role":"user","content":"Insured reports burst pipe in upstairs bathroom 03/10, ceiling collapsed in kitchen, family staying with relatives."}],"completion":[{"role":"assistant","content":"{\"loss_type\": \"water\", \"severity\": \"high\", \"needs_adjuster\": true, \"policy_section\": \"Coverage A - Dwelling\"}"}]}
```

Adapted from: Google AI for Developers, "Fine-Tune Gemma using Hugging Face Transformers and QloRA" (https://ai.google.dev/gemma/docs/core/huggingface_text_finetune_qlora), using a Qwen model and the TRL 1.16 `quantization_config=` argument.

```python
# lab3_qlora_claims.py  - Insurance claims triage: QLoRA (NF4) on Qwen3-4B-Instruct-2507
import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

ds = load_dataset("json", data_files={"train": "claims_train.jsonl", "test": "claims_val.jsonl"})

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",              # default is "fp4" - always set nf4 for QLoRA
    bnb_4bit_use_double_quant=True,         # quantize the quantization constants too
    bnb_4bit_compute_dtype=torch.bfloat16,  # use torch.float16 on T4 (no bf16)
)
args = SFTConfig(
    output_dir="qwen3-4b-claims-qlora",
    model_init_kwargs={"dtype": torch.bfloat16},
    # completion_only_loss=None (default) => loss on the completion only for prompt/completion data
    max_length=1024,
    learning_rate=1e-4,
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    optim="paged_adamw_8bit",               # QLoRA paged optimizer
    eval_strategy="epoch", save_strategy="epoch",
    logging_steps=10, report_to="none",
)
trainer = SFTTrainer(
    model="Qwen/Qwen3-4B-Instruct-2507",
    args=args,
    train_dataset=ds["train"], eval_dataset=ds["test"],
    quantization_config=bnb,                # TRL 1.16: "Combine with peft_config for QLoRA"
    peft_config=LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                           target_modules="all-linear", task_type="CAUSAL_LM"),
)
trainer.model.print_trainable_parameters()
trainer.train()
trainer.save_model("qwen3-4b-claims-qlora/final")
```

**Run.**
```bash
python lab3_qlora_claims.py
nvidia-smi --query-gpu=memory.used --format=csv -l 5    # in a 2nd terminal: watch VRAM
```

**Expected output (illustrative).** Trainable count = r·(in+out) over q/k/v/o/gate/up/down × 36 layers, from `config.json`.
```
trainable params: 33,030,144 || all params: ~4.06B || trainable%: ~0.8
{'loss': 0.902, 'mean_token_accuracy': 0.79, 'epoch': 0.1}
{'eval_loss': 0.142, 'eval_mean_token_accuracy': 0.957, 'epoch': 1.0}
...
```

**Walk-through of the key lines.**
- `bnb_4bit_quant_type="nf4"`: the `BitsAndBytesConfig.__init__` default is `bnb_4bit_quant_type="fp4"` and `bnb_4bit_use_double_quant=False` (`transformers@v5.20.2:src/transformers/utils/quantization_config.py:440-452`). By contrast, the TRL CLI's `ModelConfig` defaults to `nf4` (`trl/trainer/model_config.py:160`). So the same "QLoRA" can quietly differ between script and CLI.
- `quantization_config=bnb` on the trainer: TRL injects it into `model_init_kwargs` (`sft_trainer.py:684-690`). If you also put it in `model_init_kwargs` you get a ValueError. If you pass an already-loaded model, it is ignored with a warning (`:704-707`).
- No `device_map`: the bnb quantizer sets `{"": torch.cuda.current_device()}` when none is given (`transformers@v5.20.2:src/transformers/quantizers/quantizer_bnb_4bit.py:102-116`).
- Prompt-completion data: `completion_only_loss=None` resolves to True when both `prompt` and `completion` columns exist (`sft_trainer.py:959-963`). This works for **any** chat template, including Gemma 4, because no `{% generation %}` tag is needed.
- TRL casts the trainable adapter params to bf16 for quantized models (`sft_trainer.py:900-911`). You do not call `prepare_model_for_kbit_training` yourself.

**Common errors.**
1. `ValueError: You set `quantization_config` both as a trainer argument and in `args.model_init_kwargs`.` (`sft_trainer.py:685-688`). Fix: keep it in one place only.
2. `ValueError: A formatting function was provided while `completion_only_loss=True`, which is incompatible.` (`sft_trainer.py:1020-1025`). Fix: drop `formatting_func` for prompt-completion data.
3. On T4: `bf16` errors such as `Your setup doesn't support bf16/gpu.` (raised by transformers TrainingArguments; exact wording [UNVERIFIED]). SFTConfig defaults `bf16=True` (`sft_config.py:131-133`). Fix: `bf16=False, fp16=True`, plus `bnb_4bit_compute_dtype=torch.float16` and `model_init_kwargs={"dtype": torch.float16}`.

**Best practice.** Put **schema validity** in the eval set, not only loss. A JSON task can reach `eval_loss` 0.14 and still emit trailing prose. Lab 4 measures that.

**Variation.** Swap the base for `google/gemma-4-E2B-it` (apache-2.0). Prompt-completion avoids the "not training-compatible" ValueError that `assistant_only_loss=True` raises for Gemma 4 (Lab 1, error 1).

---

## Lab 4: Evaluate before vs after on the business task (same weights, adapter on/off)

> **Verifier (2026-10-23):** VERIFIED against peft 0.21.2 (`disable_adapter`, target-modules error) source. Output numbers illustrative.

**Goal.** Measure the claims adapter against its base model on held-out notes: JSON validity and field accuracy. Use **one** model object and switch the adapter off for the "before" run, so the comparison is apples to apples.

**Prerequisites.** Lab 3 adapter in `qwen3-4b-claims-qlora/final`, and `claims_test.jsonl` (never seen in training or checkpoint selection). Same pins.

```python
# lab4_eval_before_after.py  - Claims triage: base vs tuned on the same quantized weights
import json, torch
from datasets import load_dataset
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

BASE, ADAPTER = "Qwen/Qwen3-4B-Instruct-2507", "qwen3-4b-claims-qlora/final"
FIELDS = ["loss_type", "severity", "needs_adjuster"]
tok = AutoTokenizer.from_pretrained(BASE)
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16)
base = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16, quantization_config=bnb)
model = PeftModel.from_pretrained(base, ADAPTER).eval()
test = load_dataset("json", data_files="claims_test.jsonl", split="train")

def generate(prompt_msgs):
    enc = tok.apply_chat_template(prompt_msgs, add_generation_prompt=True,
                                  return_tensors="pt", return_dict=True).to(model.device)
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=96, do_sample=False)
    return tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)

def score():
    valid, hits = 0, dict.fromkeys(FIELDS, 0)
    for ex in test:
        gold = json.loads(ex["completion"][0]["content"])
        try:
            pred = json.loads(generate(ex["prompt"]))
        except json.JSONDecodeError:
            continue
        if not isinstance(pred, dict):
            continue
        valid += 1
        for f in FIELDS:
            hits[f] += pred.get(f) == gold[f]
    n = len(test)
    return {"json_valid": valid / n, **{f"acc_{f}": hits[f] / n for f in FIELDS}}

with model.disable_adapter():          # BEFORE: same weights, LoRA switched off
    before = score()
after = score()                        # AFTER: adapter active
for k in before:
    print(f"{k:20s} base={before[k]:.3f} tuned={after[k]:.3f} delta={after[k] - before[k]:+.3f}")
```

**Run.**
```bash
python lab4_eval_before_after.py | tee eval_report.txt
```

**Expected output (illustrative, n=200).**
```
json_valid           base=0.615 tuned=0.995 delta=+0.380
acc_loss_type        base=0.540 tuned=0.930 delta=+0.390
acc_severity         base=0.385 tuned=0.840 delta=+0.455
acc_needs_adjuster   base=0.470 tuned=0.905 delta=+0.435
```

**Walk-through of the key lines.**
- `model.disable_adapter()` is a `@contextmanager` on `PeftModel`: "Use this to run inference on the base model" (`peft@v0.21.2:src/peft/peft_model.py:1022-1030`). The quantization noise is the same in both arms, so the delta isolates the adapter.
- `apply_chat_template(..., add_generation_prompt=True, return_dict=True, return_tensors="pt")` builds the same prompt prefix the trainer used for the `prompt` part.
- `do_sample=False`: greedy decoding makes the metric reproducible. Qwen's `generation_config.json` ships `do_sample: true, temperature 0.6`, so you must override it.
- `out[0, enc["input_ids"].shape[1]:]` decodes only the new tokens. Decoding the full sequence would put the prompt into `json.loads`.

**Common errors.**
1. `json.decoder.JSONDecodeError: Extra data: line 1 column 98` on the *base* model. That is expected, not a bug: the base model adds prose. It is caught and counted as invalid.
2. `ValueError: Target modules {...} not found in the base model. Please check the target modules and try again.` (`peft@v0.21.2:src/peft/tuners/tuners_utils.py:1063-1068`). Cause: the adapter was trained on a different base. Fix: load the base named in `adapter_config.json["base_model_name_or_path"]`.
3. Very slow eval: one sample at a time on a 4-bit model. Fix: batch with `tok.padding_side="left"`, or serve with vLLM `--enable-lora` (Lab 5) and call the OpenAI-compatible API.

**Best practice.** Pick the checkpoint with a **generation-based** metric, not `eval_loss`. Chang et al. (arXiv 2609.36569, 29 Sep 2026) report that generation-based selection beats matched NLL (validation-loss) selection by 0.71-0.85 pp across 60 SFT trajectories. Its gain over simply keeping the final checkpoint remained "unresolved". Also run a general-capability regression (for example lm-eval on MMLU/IFEval) on both arms. Forgetting is the main SFT cost (see section 9).

**Variation.** Add a **slice table**: score by `loss_type` and by note length bucket. Feed the slices into the deck's "slice metrics" chapter.

---

## Lab 5: Merge the LoRA adapter, verify it numerically, and serve it

> **Verifier (2026-10-23):** VERIFIED against peft 0.21.2 (`merge_and_unload(progressbar, safe_merge, adapter_names)`, NaN and 4-bit warnings, `add_weighted_adapter` default svd) and vllm 0.32.0 (`--enable-lora`, `--max-lora-rank`, default rank 16) source. Still UNVERIFIED: file location of `--lora-modules` parser at the v0.32.0 tag (found only on main).

**Goal.** Produce a standalone bf16 model for the refund assistant (Lab 2), prove the merge did not change behaviour, and serve it either merged or as a hot-swappable adapter.

**Prerequisites.** `qwen3-0.6b-refund-lora/final` from Lab 2. Same pins. For serving: `pip install "vllm==0.32.0"` on Linux + CUDA.

```python
# lab5_merge_and_verify.py  - Merge refund LoRA into Qwen3-0.6B and check logits match
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE, ADAPTER, OUT = "Qwen/Qwen3-0.6B", "qwen3-0.6b-refund-lora/final", "qwen3-0.6b-refund-merged"
tok = AutoTokenizer.from_pretrained(BASE)
# Merge into full-precision weights. Never into a 4-bit base (rounding error, see below).
base = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.bfloat16)
peft_model = PeftModel.from_pretrained(base, ADAPTER).eval()

msgs = [{"role": "user", "content": "I returned order {{Order Number}} two weeks ago, where is my money?"}]
enc = tok.apply_chat_template(msgs, add_generation_prompt=True, enable_thinking=False,
                              return_tensors="pt", return_dict=True)
with torch.no_grad():
    ref_logits = peft_model(**enc).logits.float()

merged = peft_model.merge_and_unload(safe_merge=True, progressbar=True)  # NOT in-place: use return value
with torch.no_grad():
    new_logits = merged(**enc).logits.float()

diff = (ref_logits - new_logits).abs().max().item()
same_argmax = torch.equal(ref_logits.argmax(-1), new_logits.argmax(-1))
print(f"max |logit diff| = {diff:.4f}  same greedy tokens: {same_argmax}")
assert same_argmax, "merge changed greedy predictions - investigate before shipping"

merged.save_pretrained(OUT)
tok.save_pretrained(OUT)
out = merged.generate(**enc, max_new_tokens=60, do_sample=False)
print(tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True))
```

**Run.**
```bash
python lab5_merge_and_verify.py
# Option A - serve the merged model
vllm serve ./qwen3-0.6b-refund-merged --served-model-name refund-agent
# Option B - serve base + adapter (hot-swappable, many adapters per base)
vllm serve Qwen/Qwen3-0.6B --enable-lora --lora-modules refund=./qwen3-0.6b-refund-lora/final --max-lora-rank 16
curl localhost:8000/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"refund","messages":[{"role":"user","content":"Track my refund for order {{Order Number}}"}]}'
```

**Expected output (illustrative).**
```
Unloading and merging model: 100%|████████| 198/198
max |logit diff| = 0.0625  same greedy tokens: True
I understand you're waiting on the refund for order {{Order Number}}. Refunds are processed ...
```

**Walk-through of the key lines.**
- `merge_and_unload(progressbar=False, safe_merge=False, adapter_names=None)` is the full signature. The docstring says "this is not an in-place operation!" and tells you to assign the result (`peft@v0.21.2:src/peft/tuners/tuners_utils.py:742-760`).
- `safe_merge=True` merges into a copy and checks for NaNs. On failure it raises `NaNs detected in the merged weights. The adapter default seems to be broken` (`peft@v0.21.2:src/peft/tuners/lora/layer.py:986`).
- The base is loaded in **bf16**, not 4-bit. Merging into bnb layers warns `Merge lora module to 4-bit linear may get different generations due to rounding errors.` (`peft@v0.21.2:src/peft/tuners/lora/bnb.py:377-378`). For a QLoRA adapter (Lab 3), reload the base in bf16 and merge there.
- The argmax check rather than exact equality: bf16 re-rounding of W+BA·α/r gives small logit deltas. The *decision* (the greedy token) is the right invariant for a deployment gate.
- vLLM flags: `--enable-lora` and `--max-lora-rank` are in `vllm@v0.32.0:vllm/engine/arg_utils.py:1573-1578`. `LoRAConfig.max_lora_rank` defaults to 16 and `max_loras` to 1 (`vllm/config/lora.py:33-35`). `--lora-modules name=path` is parsed by `LoRAParserAction` (`vllm@main:vllm/entrypoints/common/cli_args.py:37-68`; v0.32.0 file path [UNVERIFIED]).

**Common errors.**
1. `AttributeError: 'Qwen3ForCausalLM' object has no attribute 'merge_and_unload'`. You called it on the base model, or called it a second time after already reassigning. Fix: call it on the `PeftModel`.
2. vLLM: an adapter rank above `--max-lora-rank` fails at load. The exact message varies by version [UNVERIFIED]. Fix: set `--max-lora-rank` to at least your `r`.
3. Garbage `<think>` text at inference: the prompt was built without `enable_thinking=False`, so it does not match training (Lab 1). Fix: always prefill the empty think block for adapters trained with the patched Qwen3 template.

**Best practice.** Ship **adapters**, not merged copies, when you have several tenants or tasks. One base plus N adapters in vLLM costs about one base model of VRAM. Merge only for the edge or GGUF path, or when you need DoRA without its runtime overhead.

**Variation.** Combine two adapters, refunds and shipping, with `add_weighted_adapter(adapters, weights, adapter_name, combination_type="ties", density=0.5)`. The default `combination_type` is `"svd"`, and `linear`/`ties`/`dare_*` need equal ranks (`peft@v0.21.2:src/peft/tuners/lora/model.py:786-810, 748-753`).

---

## Lab 6: Unsloth fast path on Gemma 4 E2B for support-ticket triage

> **Verifier (2026-10-23):** VERIFIED against unsloth main / unsloth-zoo main as of 2026-10-23 (PyPI 2026.10.8): `FastModel`, `get_chat_template("gemma-4")` with `<|turn>`/`<turn|>`, `train_on_responses_only` signature and both ValueErrors, `merged_4bit_forced` message. `unsloth/gemma-4-E2B-it` is apache-2.0, not gated (HF API). Source read on main, not on a release tag.

**Goal.** Fine-tune Gemma 4 E2B to classify tickets into `{category, intent}` JSON on a free Colab T4. Mask the user turns with `train_on_responses_only`, which works for Gemma 4, where TRL's `assistant_only_loss` does not. Export to GGUF.

**Prerequisites.** `pip install "unsloth==2026.10.8"`. That pulls compatible `unsloth_zoo`, `trl`, `peft` and `bitsandbytes`; Unsloth pins its own transformers range, so do not force the section-0 transformers pin. GPU with at least 8 GB.

Adapted from the official Unsloth notebook **`Gemma4_(E2B)-Text.ipynb`** (https://github.com/unslothai/notebooks/blob/main/nb/Gemma4_(E2B)-Text.ipynb). The cells for `FastModel.from_pretrained`, `get_peft_model(finetune_*...)`, `get_chat_template("gemma-4")`, `train_on_responses_only(trainer)` and `save_pretrained_gguf(quantization_method="Q8_0")` are verbatim from it. The dataset and labels here are new.

```python
# lab6_unsloth_gemma4_triage.py  - Support-ticket triage with Unsloth + Gemma 4 E2B
from unsloth import FastModel            # import unsloth FIRST so it can patch transformers/trl
from unsloth.chat_templates import get_chat_template, train_on_responses_only
import json
from datasets import load_dataset
from trl import SFTConfig, SFTTrainer

model, tokenizer = FastModel.from_pretrained(
    model_name="unsloth/gemma-4-E2B-it", max_seq_length=1024,
    load_in_4bit=True, full_finetuning=False)
model = FastModel.get_peft_model(
    model, finetune_vision_layers=False, finetune_language_layers=True,
    finetune_attention_modules=True, finetune_mlp_modules=True,
    r=16, lora_alpha=16, lora_dropout=0, bias="none", random_state=3407)
tokenizer = get_chat_template(tokenizer, chat_template="gemma-4")

SYSTEM = "Classify the customer ticket. Reply with JSON only: {\"category\": ..., \"intent\": ...}."
raw = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset", split="train")
raw = raw.shuffle(seed=3407).select(range(6000))

def to_text(r):
    label = json.dumps({"category": r["category"], "intent": r["intent"]})
    convo = [{"role": "system", "content": SYSTEM},
             {"role": "user", "content": r["instruction"]},
             {"role": "assistant", "content": label}]
    return {"text": tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False)}

ds = raw.map(to_text, remove_columns=raw.column_names)
trainer = SFTTrainer(
    model=model, processing_class=tokenizer, train_dataset=ds,
    args=SFTConfig(dataset_text_field="text", per_device_train_batch_size=2,
                   gradient_accumulation_steps=4, warmup_steps=5, max_steps=200,
                   learning_rate=2e-4, optim="adamw_8bit", weight_decay=0.001,
                   lr_scheduler_type="linear", logging_steps=10, seed=3407, report_to="none"))
trainer = train_on_responses_only(trainer)          # auto-detects <|turn>user / <|turn>model markers
trainer.train()

model.save_pretrained("gemma4-triage-lora"); tokenizer.save_pretrained("gemma4-triage-lora")
model.save_pretrained_gguf("gemma4-triage-gguf", tokenizer, quantization_method="Q8_0")
```

**Run.**
```bash
python lab6_unsloth_gemma4_triage.py
# then, with llama.cpp / Ollama: point it at the .gguf in gemma4-triage-gguf/
```

**Expected output (illustrative; the banner format is real, copied from the notebook's saved output; the numbers are for this run).**
```
==((====))==  Unsloth - 2x faster free finetuning | Num GPUs used = 1
   \\   /|    Num examples = 6,000 | Num Epochs = 1 | Total steps = 200
O^O/ \_/ \    Batch size per device = 2 | Gradient accumulation steps = 4
\        /    Data Parallel GPUs = 1 | Total batch size (2 x 4 x 1) = 8
 "-____-"     Trainable parameters = ~25M of 5,135,846,944 (~0.5% trained)
Step 10  loss 1.48 ... Step 200 loss 0.06
```
(The official notebook run with `r=8` printed `Trainable parameters = 12,668,928 of 5,135,846,944 (0.25% trained)`. With `r=16` the count roughly doubles.)

**Walk-through of the key lines.**
- `from unsloth import FastModel` must be the first ML import. Unsloth patches trl/transformers at import time. That is also why the notebook can pass `tokenizer=` to `SFTTrainer`, which plain TRL 1.16 rejects (Lab 2, error 1). Using `processing_class=` works in both.
- `FastModel` (`unsloth@main:unsloth/models/loader.py:2133`) is the multimodal loader that Gemma 4 needs. `FastLanguageModel.from_pretrained` defaults are `load_in_4bit=True`, `max_seq_length=2048`, `use_gradient_checkpointing="unsloth"`, `random_state=3407` (`loader.py:1225-1258`).
- `get_chat_template(tokenizer, chat_template="gemma-4")`: Gemma 4 uses `<|turn>role\n ... <turn|>\n`, with EOS `<turn|>` (`unsloth@main:unsloth/chat_templates.py:917, 1126, 1234, 1245-1250`). The older Gemma 3 `<start_of_turn>` markers from 2025 tutorials are **wrong for Gemma 4**.
- `train_on_responses_only(trainer)` with no markers auto-detects `instruction_part`/`response_part` from the template. The signature has `instruction_part=None, response_part=None, force_match=True, ..., last_response_only=False, mask_out_tokens=None` (`unsloth-zoo@main:unsloth_zoo/dataset_utils.py`, `train_on_responses_only`).
- `save_pretrained_gguf(..., quantization_method="Q8_0")`: the notebook comment says "For now only Q8_0, BF16, F16 supported" for Gemma 4. `q4_k_m` ("Recommended") is described in `unsloth/save.py:153-154` for other models.

**Common errors.**
1. `ValueError: Unsloth: Could not auto-detect chat template structure - pass instruction_part and response_part.` (`unsloth_zoo/dataset_utils.py:307`). Fix: pass `instruction_part="<|turn>user\n", response_part="<|turn>model\n"`.
2. `ValueError: Unsloth: Give both instruction_part and response_part, or neither to auto-detect!` (`dataset_utils.py:826`). Fix: pass both or neither.
3. `RuntimeError: Unsloth: Merging into 4bit will cause your model to lose accuracy if you plan to merge to GGUF ... change `save_method` to `merged_4bit_forced`.` (`unsloth/save.py:1360-1366`). Fix: use `save_pretrained_merged(dir, tokenizer, save_method="merged_16bit")`.

**Best practice.** Decode one masked example before training, as the notebook does: `tokenizer.decode([tokenizer.pad_token_id if x == -100 else x for x in trainer.train_dataset[100]["labels"]])`. Only the JSON label should remain visible.

**Variation.** Use `last_response_only=True` for multi-turn transcripts where only the final agent reply is gold. Use `mask_out_tokens=["</think>"]` for reasoning traces (`dataset_utils.py` docstring).

---

## Lab 7: Managed SFT on Vertex AI (Gemini Enterprise Agent Platform) with the Google Gen AI SDK

> **Verifier (2026-10-23):** VERIFIED against google-genai 2.33.0 source (`tunings.tune` keyword-only signature, `CreateTuningJobConfig` fields, `AdapterSize`, `JobState`, `ThinkingLevel.MINIMAL`, `GOOGLE_GENAI_USE_ENTERPRISE`). Still UNVERIFIED: `gcloud ai tuning-jobs` CLI group; Vertex doc limits not re-fetched by the verifier.

**Goal.** Tune `gemini-3.5-flash` on the same refund data, without GPUs, and call the tuned endpoint. Compare with the open-weights path from Labs 2-5.

**Prerequisites.**
```bash
pip install "google-genai==2.33.0" "datasets==5.1.0"
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=my-project
export GOOGLE_CLOUD_LOCATION=us          # Gemini 3+: 'us' or 'eu' multi-region only; us-central1 for 2.5 and earlier
export GOOGLE_GENAI_USE_ENTERPRISE=True  # new name; GOOGLE_GENAI_USE_VERTEXAI is the legacy flag
export TUNING_BUCKET=gs://my-project-tuning
```
Adapted from: "Use supervised fine-tuning" (Python tab), https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/supervised-tuning/use, and the codelab **"Fine-tune Gemini on Gemini Enterprise Agent Platform"**, https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/9-ai-finetuning/finetune-gemini-vertex-ai (it uses `ADAPTER_SIZE_FOUR`, `epoch_count=1`).

```python
# lab7_vertex_gemini_sft.py  - Refund assistant on gemini-3.5-flash (managed SFT)
import json, os, subprocess, time
from datasets import load_dataset
from google import genai
from google.genai import types

BUCKET = os.environ["TUNING_BUCKET"]
SYSTEM = "You are the refunds assistant for an online store. Keep placeholders like {{Order Number}} unchanged."
rows = (load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset", split="train")
        .filter(lambda r: r["category"] == "REFUND").shuffle(seed=7))

def to_gemini(r):   # one JSONL line in the Gemini SFT format (systemInstruction + contents/parts)
    return {"systemInstruction": {"parts": [{"text": SYSTEM}]},
            "contents": [{"role": "user", "parts": [{"text": r["instruction"]}]},
                         {"role": "model", "parts": [{"text": r["response"]}]}]}

for name, sl in [("refund_train.jsonl", range(0, 2600)), ("refund_val.jsonl", range(2600, 2900))]:
    with open(name, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(to_gemini(rows[i])) + "\n" for i in sl)
    subprocess.run(["gcloud", "storage", "cp", name, f"{BUCKET}/{name}"], check=True)

client = genai.Client(http_options=types.HttpOptions(api_version="v1beta1"))
job = client.tunings.tune(
    base_model="gemini-3.5-flash",
    training_dataset=types.TuningDataset(gcs_uri=f"{BUCKET}/refund_train.jsonl"),
    config=types.CreateTuningJobConfig(
        tuned_model_display_name="refund-agent-v1",
        validation_dataset=types.TuningValidationDataset(gcs_uri=f"{BUCKET}/refund_val.jsonl"),
        epoch_count=3,
        adapter_size=types.AdapterSize.ADAPTER_SIZE_FOUR,
        learning_rate_multiplier=1.0,
        labels={"team": "support", "use_case": "refunds"},
    ),
)
while not job.has_ended:                      # property: state in JOB_STATES_ENDED
    print(job.state); time.sleep(60)
    job = client.tunings.get(name=job.name)
print(job.state, job.tuned_model.endpoint)

resp = client.models.generate_content(
    model=job.tuned_model.endpoint,
    contents="I was charged twice for order {{Order Number}}, refund one of them",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL)))
print(resp.text)
```

**Run.**
```bash
python lab7_vertex_gemini_sft.py
gcloud ai tuning-jobs list --region=us    # alternative status check; CLI group name [UNVERIFIED]
```

**Expected output (illustrative). The resource-name shapes are copied from the docs' "Example response".**
```
JobState.JOB_STATE_PENDING
JobState.JOB_STATE_RUNNING
...
JobState.JOB_STATE_SUCCEEDED projects/123456789012/locations/us/endpoints/123456789012345
I'm sorry you were charged twice for order {{Order Number}}. I can help you request a refund for the duplicate charge...
```

**Walk-through of the key lines.**
- `client.tunings.tune(*, base_model, training_dataset, config=None)` (`python-genai@v2.33.0:google/genai/tunings.py:3166-3172`). A base model starting with `projects/` is treated as a **pre-tuned model** for continued tuning (`:3174-3186`).
- `CreateTuningJobConfig` fields used here: `tuned_model_display_name` (up to 128 characters), `validation_dataset: TuningValidationDataset`, `epoch_count`, `learning_rate_multiplier` ("1P models only. Mutually exclusive with learning_rate"), `adapter_size`, `labels` (`google/genai/types.py:16157-16220`). `AdapterSize` values run from `ADAPTER_SIZE_ONE` to `ADAPTER_SIZE_THIRTY_TWO` (`types.py:787-802`). The docs table allows only **1, 2, 4, 8, 16** for Gemini 3.5 Flash.
- `job.has_ended` / `has_succeeded` are `@property`s on `TuningJob` (`types.py:15794-15802`). States include `JOB_STATE_PENDING/RUNNING/SUCCEEDED/FAILED/CANCELLED` (`types.py:852-872`).
- `GOOGLE_GENAI_USE_ENTERPRISE` takes precedence over `GOOGLE_GENAI_USE_VERTEXAI` if both are set ("The value of GOOGLE_GENAI_USE_ENTERPRISE will be used", `_api_client.py:871-890`). `us`/`eu` are recognised multi-regions (`_api_client.py:152`).
- `ThinkingLevel.MINIMAL`: the docs say, "For models that support thinking, set ... the thinking level to MINIMAL (for Gemini 3 and higher)... the model learns from the training data and omits the thinking process."

**Common errors.**
1. Job ends `JOB_STATE_FAILED` with a dataset error because the region is wrong. Gemini 3.5 Flash tuning and serving are "us and eu multi-region endpoints only" (SFT overview limits table). Fix: `GOOGLE_CLOUD_LOCATION=us`.
2. Validation set too large: the limit is "5000 examples or 30% of the number of training examples if there are more than 1000 validation examples" (limits table). Fix: cap validation at 5,000.
3. `pydantic.ValidationError` when you pass a raw string to `training_dataset=`. Fix: `types.TuningDataset(gcs_uri=...)` or the dict `{"gcs_uri": ...}` (`TuningDatasetOrDict`).
4. A quota error on the second concurrent job. The quota is "a global quota... at least one tuning job" per project by default. Fix: request "Global concurrent tuning jobs" quota.

**Best practice.** Inspect `job.tuning_data_stats.supervised_tuning_data_stats` after the job. It has `total_billable_token_count`, `total_truncated_example_count`, `truncated_example_indices` and `dropped_example_reasons` (`types.py:14732-14790`). Cost = training tokens × epochs (SFT overview, "Pricing"), so truncation and drops are both a cost leak and a quality leak.

**Variation.** Add `evaluation_config=types.EvaluationConfig(metrics=[...], output_config=...)` to get Gen AI eval during tuning. The SDK raises `ValueError('Evaluation config must have at least one metric and an output config.')` if either is missing (`tunings.py:3188-3200`). Another variation: pass `method=types.TuningMethod.PREFERENCE_TUNING` with `beta` for DPO-style tuning (field docs in `types.py:16163-16165, 16219-16221`).

**Open-weights vs managed, in one line for the slide:** Labs 2-5 give you weights, masking control and multi-LoRA serving. Lab 7 gives you no GPUs and an SLA-less managed service: SFT "is not a Covered Service and is excluded from the SLO of any Service Level Agreement" (SFT overview). Dataset limits are 131,072 tokens per example, 1 GB JSONL, and 10M text examples.

---

## Lab 8: Hyperparameter sweep from the TRL CLI (rank × learning rate), config-as-code

> **Verifier (2026-10-23):** VERIFIED against trl 1.16.0 source (`ModelConfig.dtype`, `lora_r=16`, `lora_alpha=32`, `lora_dropout=0.05`, list-to-string collapse, `ScriptArguments.dataset_*` fields, `scripts/sft.py` error) and peft 0.21.2 (`r=8`, `lora_alpha=8`, `lora_dropout=0.0`).

**Goal.** Run a small, reproducible sweep for the refund adapter and pick a configuration with the Lab 4 metric. All hyperparameters live in YAML that you can review in a PR.

**Prerequisites.** Same pins. Lab 2's converted dataset saved as `refund_msgs/train.jsonl` and `refund_msgs/test.jsonl`. Example: `ds["train"].to_json("refund_msgs/train.jsonl")`, and the same for test. `load_dataset("refund_msgs")` infers the `train`/`test` splits from the file names.

```yaml
# refund_sft.yaml  - consumed by `trl sft --config`
model_name_or_path: Qwen/Qwen3-0.6B
dtype: bfloat16
dataset_name: refund_msgs
dataset_train_split: train
dataset_test_split: test
assistant_only_loss: true
packing: true
max_length: 1024
use_peft: true
lora_target_modules: all-linear    # a 1-element list is collapsed to the string "all-linear"
lora_dropout: 0.05
num_train_epochs: 2
per_device_train_batch_size: 8
gradient_accumulation_steps: 2
lr_scheduler_type: cosine
warmup_steps: 0.03
eval_strategy: steps
eval_steps: 50
logging_steps: 10
report_to: none
```
```bash
# sweep.sh - 3 ranks x 3 learning rates, alpha = 2r (CLI default ratio is 32/16)
for r in 8 16 64; do
  for lr in 1e-4 2e-4 5e-4; do
    trl sft --config refund_sft.yaml --lora_r $r --lora_alpha $((2*r)) \
      --learning_rate $lr --output_dir runs/r${r}_lr${lr}
  done
done
grep -h '"eval_loss"' runs/*/checkpoint-*/trainer_state.json | head   # quick look; select with Lab 4, not loss
```

**Expected output (illustrative), a summary table you would build from Lab 4 scores.**
```
run           eval_loss  intent_exact  placeholder_kept
r8_lr1e-4     0.601      0.912         0.97
r16_lr2e-4    0.561      0.934         0.99
r64_lr5e-4    0.548      0.921         0.93   <- lowest loss, NOT the best task score
```

**Walk-through of the key lines.**
- `trl sft` is a registered CLI command (`trl@v1.16.0:trl/cli/commands/__init__.py`, `TrainingCommand("sft")`; entry point `trl = "trl.cli:main"` in `pyproject.toml:48-49`). `--config` is parsed by `parse_args_and_config` (`trl/scripts/utils.py:321-323`). CLI flags override YAML.
- `use_peft`, `lora_r` (default **16**), `lora_alpha` (default **32**), `lora_dropout` (0.05) and `lora_target_modules` (default `None`) are `ModelConfig` fields (`trl/trainer/model_config.py:103-122`). Note that these differ from `peft.LoraConfig` defaults: `r=8`, `lora_alpha=8`, `lora_dropout=0.0` (`peft/tuners/lora/config.py:632-653`). "LoRA r=16" in a CLI run and in a script are not the same adapter unless you set alpha explicitly.
- `lora_target_modules: all-linear`: `ModelConfig.__post_init__` turns a 1-element list into a string (`model_config.py:177`). Without it you get the `q_proj, v_proj` default (Lab 2).
- The `dataset_name` / split fields feed `load_dataset(script_args.dataset_name, ...)` and `dataset[script_args.dataset_train_split]` (`trl/scripts/sft.py:95-106`).

**Common errors.**
1. `ValueError: Either `datasets` or `dataset_name` must be provided.` (`sft.py:100`). Fix: set `dataset_name`.
2. `ValueError: You can't use 8 bit and 4 bit precision at the same time` (`model_config.py:174-175`), when both `load_in_4bit` and `load_in_8bit` are true.
3. `ValueError: When packing is enabled, `max_length` can't be `None`.` (`sft_trainer.py:1468`).

**Best practice.** Sweep the learning rate first; it matters more than rank. Keep alpha/r fixed, or use `use_rslora: true` when you sweep rank, so the effective step size does not change with r.

**Variation.** Add `--loss_type dft` as a 4th axis. Or wrap the loop in a job array on Cloud Run Jobs / GKE (the codelab pattern) with one adapter per task.

---

## 9. Recent arXiv evidence (2026-07-23 .. 2026-10-23) and how it changes the labs

All IDs and abstracts were fetched from arxiv.org/abs on 2026-10-23. The dates are `citation_date` (first version).

| Paper (arXiv ID, date) | Finding (from abstract) | Lab hook |
|---|---|---|
| **Post-Training Science for Supervised Fine-Tuning**, O'Neill, Jayasekara, Partridge et al. (2609.01244, 2026-09-01) | One-lever-at-a-time sweeps on Qwen3 and Llama, dense and MoE up to 235B, **four real customer SFT datasets**, LoRA and full FT. Asks how the optimal LR/batch move with scale, what LoRA rank/alpha set, "whether validation loss ... faithfully ranks downstream quality", and "how many epochs to train before general instruction-following erodes". | Lab 8: sweep LR first and validate with the task metric. Exact numeric recommendations not extracted [UNVERIFIED beyond abstract] |
| **From Checkpoint Variation to Selection Gains in SFT**, Chang, Zhang, Wu (2609.36569, 2026-09-29) | Across 60 math SFT trajectories, generation-based checkpoint selection beats matched NLL selection by **0.71 and 0.85 pp**. Going from 32 to about 305 validation examples adds about 0.3 pp. The gain over keeping the final checkpoint stayed "unresolved". | Lab 4 best practice: select with generated accuracy; at least 300 validation items |
| **SFT-as-Context Mitigates Forgetting in SFT** (2610.11132, 2026-10-08) | Training-free: the *parent* model answers using the SFT model's response as context. Within 2.2 pp of SFT on AIME24/LiveCodeBench and within 2.2 pp of the parent on general capability, across 19 pairs and 11 benchmarks. A small open SFT model's output can improve a strong closed LLM. | Lab 5 extension: route "domain + general" queries through base(prompt + adapter draft) |
| **Stick to What You Know: Knowledge-Aligned SFT** (2608.30987, 2026-08-31) | SFT targets that need knowledge the base lacks drive hallucination. "Recall Rewrite" keeps only claims the base can consistently recall. This reduced factual hallucination on WildHalu/Biography with Qwen3 4B and OLMo 3 7B. | Lab 3: do not teach new facts (policy numbers) via SFT; put them in RAG |
| **When Does SFT Reduce Instruction Sensitivity?** (2608.26661, 2026-08-27) | Before SFT, sensitivity drops sharply with Qwen3 scale. At 1.7B and 4B, task SFT cuts sensitivity across paraphrased instructions by about **54-71%**; at 8B the effect is not significant. Free-generation and forced-choice eval can disagree. | Lab 4: evaluate with several paraphrased system prompts; report the std |
| **AQLoRA: A Zero-Search Recipe for Fast Quantized LoRA** (2608.23816, 2026-08-24) | QLoRA "saves memory but not time". Keeping the highest-NF4-error layers in fp16 trains 11.3±2.3% faster (speed setting, −0.1 to −1.5 acc) or 4.8% faster at QLoRA accuracy. The selection matches Unsloth's hand-curated dynamic-4bit list. | Lab 3 vs Lab 6: explains why `unsloth-bnb-4bit` checkpoints exist |
| **Self-Distillation for SFT (Gold-Conditioned Distillation)** (2610.25497, 2026-10-18) | Teacher = same model with the gold answer in context; student is trained by forward KL to the teacher's token distribution. Better new-task accuracy than SFT and less general-benchmark loss on Qwen and Llama. | Variation of Lab 2: replace one-hot NLL targets |
| **Learn the Directions, Normalize the Gains: LoRA-Norm** (2610.02067, 2026-10-01) | "Adaptation imbalance": a few singular directions dominate a LoRA update. Post-hoc spectral rebalancing with no data and no inference cost improves specialization **and** retention. | Lab 5: a post-merge knob next to "scale alpha by 0.5" |
| **Null-Basis LoRA for post-RL models** (2609.25618, 2026-09-22) | SFT on reasoning (post-RL) models "can severely overwrite" reasoning. NB-LoRA constrains updates to the null space of reasoning activations and matches LoRA on the task while reasoning stays near pre-FT levels. | Warning slide: SFT-ing a thinking model like Qwen3 can erase reasoning |
| **PACT: NVFP4 LoRA on Consumer GPUs** (2610.25048, 2026-10-18) | Native NVFP4 GEMMs for the frozen projections plus NVFP4-saved activations. Lower memory and faster LoRA on a 16 GB RTX 5080. | Hardware outlook: 4-bit *compute*, not just 4-bit storage |
| **LoRA's Second Descent** (2610.04507, 2026-10-03) | Under label noise, risk is lowest at **rank 1**, then an "interpolation cliff" appears as rank grows. Rank-one LoRA beat dense FT on 3 of 4 vision backbones. | Data-centric link: with noisy labels, lower r acts as a regulariser |
| **Fine-grained LoRA landscape / LoRA-RIP** (2610.06542, 2026-10-05) | The right rank depends on the data-induced conditioning, not only the model. Enables data selection under a fixed rank budget. | Lab 8: rank is a data property |

---

## 10. Industry-practice checklist (each item traceable to a source above)

1. **Pin the stack and pass `dtype`.** TRL loads string models in float32 by default (`sft_trainer.py:544-546`). The TRL 0.x to 1.x renames (`tokenizer` to `processing_class`, `max_seq_length` to `max_length`) and the transformers v5 removal of `warmup_ratio` break unpinned tutorials.
2. **Mask, and prove it.** Lab 1 runs as CI. For non-patched families (Gemma 4), use the prompt-completion format or Unsloth `train_on_responses_only`.
3. **Target all linear layers.** The PEFT default for Qwen3/Llama/Gemma3 is `q_proj, v_proj` only (`constants.py:85-104`).
4. **LoRA LR about 1e-4 to 2e-4.** Set alpha explicitly, because TRL CLI (16/32), PEFT (8/8) and Unsloth (16/16) defaults all differ.
5. **QLoRA = `nf4` explicitly** (the transformers default is `fp4`). Merge into a **bf16** base.
6. **Select checkpoints on the task metric** (2609.36569). Gate deploys on before/after deltas with the same weights (`disable_adapter`).
7. **Do not use SFT to inject facts** (2608.30987); use RAG. Use SFT for format, policy tone and labels.
8. **Thinking models.** Train and serve with the same think-block convention (Lab 1/5). On Vertex, serve tuned Gemini with `thinking_level=MINIMAL`. Expect reasoning erosion when SFT-ing post-RL models (2609.25618).
9. **Serve adapters with multi-LoRA** (`vllm serve --enable-lora --lora-modules`). Merge only for GGUF or edge.
10. **Managed tuning.** Check region (`us`/`eu` for Gemini 3.x), the 5,000-example validation cap, truncation stats, and the fact that SFT has no SLA.

## Sources (primary)

- TRL v1.16.0 source: https://github.com/huggingface/trl/tree/v1.16.0 (`trl/trainer/sft_config.py`, `trl/trainer/sft_trainer.py`, `trl/chat_template_utils.py`, `trl/chat_templates/README.md`, `trl/chat_templates/qwen3_training.jinja`, `trl/trainer/model_config.py`, `trl/scripts/sft.py`, `trl/cli/`, `docs/source/reducing_memory_usage.md`, `docs/source/sft_trainer.md`)
- PEFT v0.21.2 source: https://github.com/huggingface/peft/tree/v0.21.2 (`tuners/lora/config.py`, `tuners/tuners_utils.py`, `tuners/lora/model.py`, `tuners/lora/bnb.py`, `tuners/lora/layer.py`, `peft_model.py`, `utils/constants.py`)
- Transformers v5.20.2: `utils/quantization_config.py`, `tokenization_utils_base.py`, `training_args.py`, `quantizers/quantizer_bnb_4bit.py`
- Unsloth (main @ release v0.1.910-beta / PyPI 2026.10.8): `unsloth/models/loader.py`, `unsloth/models/llama.py`, `unsloth/chat_templates.py`, `unsloth/save.py`, `unsloth/models/mapper.py`. unsloth-zoo `unsloth_zoo/dataset_utils.py`. Notebook `nb/Gemma4_(E2B)-Text.ipynb` in github.com/unslothai/notebooks
- google-genai v2.33.0: https://github.com/googleapis/python-genai/tree/v2.33.0 (`google/genai/tunings.py`, `types.py`, `_api_client.py`)
- Vertex docs: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/supervised-tuning ; `/use` ; `/prepare-data`
- vLLM v0.32.0: `vllm/engine/arg_utils.py`, `vllm/config/lora.py`; main: `vllm/entrypoints/common/cli_args.py`
- Dataset: https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset
- arXiv: 2609.01244, 2609.36569, 2610.11132, 2608.30987, 2608.26661, 2608.23816, 2610.25497, 2610.02067, 2609.25618, 2610.25048, 2610.04507, 2610.06542
