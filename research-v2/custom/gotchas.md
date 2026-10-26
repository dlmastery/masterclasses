# Gotchas and Open Challenges: Fine-tuning, RL, Data, and Evaluation (as of 2026-10-23)

Scope: TRL / PEFT / Unsloth / verl / vLLM issues, dataset pipelines, labelling, leakage, synthetic data, evaluation mistakes, and managed tuning services.

Method:
- Each GitHub item was read through the GitHub REST API (issue body plus last comments) on 2026-10-23.
- Each arXiv item was read on its `arxiv.org/abs/<id>` page (2026-07-23 .. 2026-10-23 window).
- Docs warnings are quoted from raw docs source or the live page.
- Items the older research already covered (`research-custom/09-critic-corrections.md` C13, C17, C18, C21) appear only as short pointers.

Status legend:
- **FIXED vX**: the fix shipped in that version.
- **OPEN**: no fix on main yet.
- **CLOSED-NOFIX**: closed by the maintainers without a code change. Often the reason is "found by reading code, not in a real run" (TRL policy #6862, cited in maintainer comments). Teach the mechanism anyway, because the failure class is real.

Versions referenced: TRL 1.16.0, PEFT 0.21.2, transformers 5.20.2, vLLM 0.32.0, verl 0.9.1, unsloth 2026.10.8. The full sheet is in research-custom/09 §2.

---

## A. SFT and PEFT (TRL, PEFT, Unsloth)

### A1. The model never stops generating: EOS does not match the chat template
- **Symptom:** after SFT, the model keeps generating past the answer. It runs into a new "user" turn or to `max_new_tokens`.
- **Root cause:** the base model's tokenizer has a chat template whose end-of-turn token (`<|im_end|>` for Qwen) differs from `tokenizer.eos_token`. The trainer appends the wrong EOS, so the model never learns to emit the turn terminator.
- **Fix** (TRL docs warning, verbatim intent: "it is necessary to align the EOS token with the chat template"):
  ```python
  SFTConfig(eos_token="<|im_end|>")   # e.g. for Qwen/Qwen2.5-1.5B
  ```
- **Detect early:** a unit test that tokenizes one formatted example and asserts `ids[-1] == tok.convert_tokens_to_ids("<|im_end|>")`. Eval metric: the share of generations that end with the stop token (it should be close to 100%).
- **Source:** https://github.com/huggingface/trl/blob/main/docs/source/sft_trainer.md (WARNING block, "Some base models, like those from Qwen…")

### A2. `assistant_only_loss=True` silently needs `{% generation %}` markers in the template
- **Symptom:** you get an error, or the model trains on user and system tokens (the loss mask covers everything). The chat template has no generation markers.
- **Root cause:** TRL derives the assistant mask from `{% generation %}…{% endgeneration %}` in the Jinja template. TRL auto-patches known families only, for example Qwen3.
- **Fix:** use a bundled training template, or add the markers yourself (SmolLM3's `chat_template.jinja` L76-82 is the reference). For VLMs you also need `transformers>=5.18.0`.
- **Detect early:** decode the tokens where `labels != -100` for one sample and assert that no user text appears.
- **Source:** TRL `sft_trainer.md` WARNING and NOTE blocks (same URL as A1).

### A3. float32 by default leads to OOM, and the "escape hatch" collides
- **Symptom:** `torch.OutOfMemoryError … Tried to allocate 3.81 GiB` when training a 4B model on an 80 GB H100. In the async trainer, passing a dtype raised `TypeError: … from_pretrained() got multiple values for keyword argument 'dtype'`.
- **Root cause:**
  - TRL loads a model passed by name string in float32 unless `model_init_kwargs={"dtype": ...}` is set (C13).
  - `AsyncGRPOTrainer` also hardcoded `dtype=torch.float32`. For 4B parameters: 16.1 GB weights + 16.1 GB grads + 32.2 GB AdamW states ≈ 64 GB before activations.
- **Fix:** **FIXED v1.11.0**: `AsyncGRPOConfig(dtype="bfloat16")` or `model_init_kwargs={"dtype": "bfloat16"}`. The default stays fp32 on purpose, because the training-inference mismatch results were measured at that precision.
  ```python
  GRPOConfig(..., model_init_kwargs={"dtype": "bfloat16"})
  ```
- **Detect early:** log `next(model.parameters()).dtype` at step 0, and compare peak memory against the 16-bytes-per-parameter rule.
- **Source:** https://github.com/huggingface/trl/issues/6684

### A4. LoRA "trains" but nothing changes: `target_modules` matched 7% of the layers
- **Symptom:** a DPO-LoRA run on `nvidia/NVIDIA-Nemotron-Nano-9B-v2` completed 25/25 steps. Loss stayed at **0.6931 (= ln 2)** for every step, and HumanEval was **0.0% (0/164)**.
- **Root cause:**
  - PEFT's default targets for `nemotron_h` are attention projections only. They cover 4 of 56 layers; the other 52 are Mamba layers with `in_proj`, `out_proj`, etc.
  - PEFT raises only when *no* target matches. A partial match is silent (#3658).
- **Fix:** list the hybrid-architecture module names explicitly, then assert coverage:
  ```python
  from peft import get_peft_model
  m = get_peft_model(model, cfg)
  m.print_trainable_parameters()
  hit = {n.split(".lora_A")[0] for n, _ in m.named_parameters() if "lora_A" in n}
  layers = {int(n.split("layers.")[1].split(".")[0]) for n in hit if "layers." in n}
  assert len(layers) == model.config.num_hidden_layers, f"LoRA on {len(layers)} layers only"
  ```
- **Detect early:** a DPO loss that stays exactly at ln 2 means the policy equals the reference. Also check the per-layer adapter census above.
- **Source:** https://github.com/huggingface/peft/issues/3554 (closed; docs PR #3603), https://github.com/huggingface/peft/issues/3658 (OPEN)

### A5. A wrong adapter loads with no warning, and `strict=True` is ignored
- **Symptom:** an adapter from a different architecture or depth loads with no error. Outputs equal the base model, or are subtly wrong.
- **Root cause:**
  - `PeftModel.from_pretrained` warns about *missing* keys but drops *unexpected* ones.
  - `load_adapter` warns about neither.
  - Both accept `strict=True` with no effect (peft 0.21.0, main 116a979).
- **Fix:** **OPEN**. PR #3832 adds `strict_adapter_check`. Until then, diff the keys yourself:
  ```python
  from safetensors.torch import load_file
  sd = load_file(f"{path}/adapter_model.safetensors")
  model_keys = {k for k, _ in peft_model.named_parameters() if "lora_" in k}
  unexpected = [k for k in sd if not any(k.replace(".weight", "") in mk for mk in model_keys)]
  assert not unexpected, unexpected[:5]
  ```
- **Detect early:** a golden-output test that compares the adapter-loaded model against the base on 5 prompts. The two must differ.
- **Source:** https://github.com/huggingface/peft/issues/3804

### A6. transformers v5 module renames break adapters in vLLM
- **Symptom:** an adapter trained under transformers 5.x fails to apply, or is ignored, when served by vLLM's native model implementation (seen with GLM-5.3-Flash).
- **Root cause:** transformers v5 renames modules at load time (`conversion_mapping`). `save_pretrained` reverses the rename for base weights (`save_original_format=True`), but the PEFT adapter is saved under the *runtime* names.
- **Fix:**
  - Serve with `--model-impl transformers`.
  - Or use the vLLM PRs vllm-project/vllm#60656 (LoRA) and #60666 (all), cited by the reporter as solving it.
  - PEFT back-conversion: **OPEN**.
- **Detect early:** a CI step that loads the adapter into the *serving* engine and compares logprobs with the training stack on 3 prompts.
- **Source:** https://github.com/huggingface/peft/issues/3896

### A7. An old torchao preinstalled on Colab or Kaggle breaks every LoRA injection
- **Symptom:** `ImportError: Found an incompatible version of torchao. Found version 0.10.0, but only versions above 0.16.0 are supported`. The model does not use torchao at all.
- **Root cause:** since PEFT 0.19.0, `is_torchao_available()` raises instead of returning False. It runs on every targeted layer.
- **Fix:** `pip uninstall -y torchao` (or upgrade it to ≥0.16). Upstream will warn and return False (approved 2026-10-16).
- **Detect early:** pin and print `torchao` in the environment-report cell of every notebook.
- **Source:** https://github.com/huggingface/peft/issues/3964

### A8. Merge then unmerge on 4-bit weights does not give you the base model back
- **Symptom:** after `merge_adapter(); unmerge_adapter()` on a bitsandbytes 4-bit model, the base weights drift, and each cycle moves them further. A caller that holds the old `Params4bit` keeps a stale tensor.
- **Root cause:** merging into 4-bit weights quantizes again, which is lossy, so unmerge cannot restore the exact weights.
- **Fix:** reload the base model to get clean weights. Do A/B adapter comparisons on unmerged models, or merge into a bf16 copy for export.
- **Detect early:** checksum the dequantized base weight before and after the cycle.
- **Source:** https://github.com/huggingface/peft/issues/3878 (docs note approved)

### A9. Unsloth GGUF export silently ships the *base* model
- **Symptom:** the exported GGUF behaves exactly like the base model. The LoRA was not merged.
- **Root cause:** `patch_saving_functions` binds `save_pretrained_gguf` / `save_pretrained_merged` to the base object. If you then wrap it with `PeftModel.from_pretrained(base, adapter)`, the bound method still sees the base, and the `isinstance(self, PeftModel)` check fails.
- **Fix:** load the adapter folder through `FastModel.from_pretrained(<adapter dir>)`, not through the raw PEFT API, before you export.
- **Detect early:** after export, run 3 fine-tune-specific probe prompts on the GGUF in llama.cpp. The answers must differ from the base model.
- **Source:** https://github.com/unslothai/unsloth/issues/11698 (closed 2026-09-26)

### A10. Merged Gemma 4 gives garbled answers; the adapter-only save works
- **Symptom:** `model.save_pretrained_merged("gemma-finetune", processor)` produces garbled output. `model.save_pretrained("gemma_4_lora")` works (unsloth 2026.7.4, transformers 5.5.0).
- **Fix:** ship the adapter and verify the merge separately. Upgrade (closed same day).
- **Detect early:** compare perplexity of merged vs adapter on 50 held-out rows. They must match within about 1%.
- **Source:** https://github.com/unslothai/unsloth/issues/7318

### A11. Loss goes NaN at a *deterministic* step after the first eval
- **Symptom:** Qwen3.5-0.8B/2B LoRA SFT. Steps 1–57 are finite; `eval_loss: NaN` at step 57, then NaN for every training step from 58. LR, optimizer and seed make no difference.
- **Root cause:** on transformers 5.3, flash attention misread Qwen3.5 position ids for a **single-row batch**. The 79-row eval split ended with exactly such a batch. The eval wrote past its buffers and left NaNs in the LoRA weights and optimizer state.
- **Fix:** **FIXED** in unsloth #12856. Workaround: make the eval set size a multiple of the eval batch size, or set `dataloader_drop_last`.
- **Detect early:** if NaN starts right after an eval, suspect eval batch shape. Assert `torch.isfinite` on the LoRA params after every eval.
- **Source:** https://github.com/unslothai/unsloth/issues/12737

### A12. A "fast" loader silently degrades embedding quality
- **Symptom:** `Qwen/Qwen3-Embedding-0.6B` loaded via `FastSentenceTransformer` scores recall@50 **39.3–40.4**, against **54.3** for plain `SentenceTransformer`. There is no warning. This happens before any training.
- **Fix:** fixed on unsloth main (2026-07-10).
- **Lesson:** always run a parity check of the accelerated loader against the reference loader *before* fine-tuning.
- **Detect early:**
  ```python
  import numpy as np
  assert np.dot(e_ref, e_fast) > 0.999   # same text, both normalized
  ```
- **Source:** https://github.com/unslothai/unsloth/issues/6881

### A13. API drift: unpinned TRL breaks tutorials (2026 removal wave)
- **Symptom:**
  - `ImportError: cannot import name 'PPOTrainer' from 'trl'`
  - `from trl.losses import FusedLinearDPOLoss` fails
  - `TypeError` on the old `SFTTrainer(dataset_text_field=..., max_seq_length=..., tokenizer=...)` (codelab, C21)
- **Root cause** (from the TRL release notes):
  - **v1.10**: `from trl import PPOTrainer` stopped working. `torch_dtype` is replaced by `dtype`. `GRPOConfig.use_bias_correction_kl` now defaults to `True`.
  - **v1.13.0** (2026-09-10): "⚠️ PPO is removed". `PPOTrainer`, `PPOConfig` and `AutoModelForCausalLMWithValueHead` are gone. (This corrects research-custom C11, which said PPO lives under `trl.experimental`.)
  - **v1.14.0** (2026-09-25): six experimental trainers removed (BCO, GRPO-with-replay-buffer, PRM, Nash-MD, XPO, GSPO-token), and `trl.losses` removed.
  - **v1.15.0** (2026-10-08): `use_liger_kernel=True` is deprecated in DPO/KTO/GRPO/RLOO (removal in v2.0.0). Use `model_init_kwargs={"use_kernels": True}`. "A PEFT adapter **on `lm_head`** now raises. Use `modules_to_save=["lm_head"]` instead."
  - **v1.16.0**: the experimental SSD trainer is removed.
- **Fix:** pin `trl==1.16.0` in every lab, and teach `trl.experimental.*` as "no stability guarantee".
- **Detect early:** a CI smoke test that imports and runs one step of each trainer the deck uses.
- **Source:** https://github.com/huggingface/trl/releases (v1.10.0–v1.16.0)

---

## B. Preference tuning and RL (TRL GRPO/DPO, verl, vLLM)

### B1. GRPO config errors on the first run
- **Symptom** (verbatim from `grpo_config.py`):
  - `ValueError: generation_batch_size (…) must be divisible by num_generations (…)`
  - `GRPO requires at least 2 generations per prompt to calculate the advantages.`
- **Root cause:** advantages are computed within a group, so a batch must hold whole prompt groups.
- **Fix:** choose `per_device_train_batch_size * num_processes * gradient_accumulation_steps` as a multiple of `num_generations` (default 8). Example: 1 GPU × 8 × 1, or 4 GPUs × 4 × 1 with `num_generations=16`.
- **Source:** https://github.com/huggingface/trl/blob/main/trl/trainer/grpo_config.py (L1128-1140)

### B2. Truncated completions are punished as wrong answers
- **Symptom:** reward falls and response length collapses, or reward is noisy when many completions hit `max_completion_length` (default **512**).
- **Root cause:** a truncated reasoning trace gets reward 0 even when it was on track. `mask_truncated_completions` defaults to `False`.
- **Fix:**
  ```python
  GRPOConfig(max_completion_length=2048, mask_truncated_completions=True)  # DAPO practice per docstring
  ```
- **Detect early:** log `completions/clipped_ratio`. If it is above about 10%, raise the length or mask truncated completions.
- **Source:** `grpo_config.py` docstring (same URL as B1)

### B3. The vLLM importance-sampling ratio is biased when you use top_p / top_k / min_p
- **Symptom:** none visible. The policy gradient is silently and token-dependently down-weighted.
- **Root cause:** vLLM returns log-probs renormalized over the *truncated* nucleus. The trainer recomputes them over the full vocabulary. That gives a per-token bias of `-log(sum surviving mass)` in `log π_θ − log π_behaviour`, and the IS ratio multiplies the per-token loss directly.
- **Fix:** sample rollouts with `top_p=1.0, top_k=-1` (temperature alone is handled symmetrically). Or use the training-side fix, which was ported to the fused LM head (PRs #7389 and #7415).
- **Detect early:** log the mean `log π_θ − log π_vllm` on sampled tokens. It should be near 0 at step 0, before any update.
- **Source:** https://github.com/huggingface/trl/issues/6789 (closed 2026-10-16)

### B4. The MoE router auxiliary loss is silently dropped with `use_liger_kernel=True`
- **Symptom:** expert load imbalance or collapse in GRPO on MoE models. `trainer.aux_loss_enabled` still reads `True`.
- **Root cause:** the Liger path returned before `_compute_loss`, which is the only place the aux loss was added. DPO and KTO already raised on this combination; GRPO did not.
- **Fix:** **FIXED** on main by #7077 (test `test_train_with_liger_and_moe_aux_loss`). `use_liger_kernel` is now deprecated anyway (A13).
- **Detect early:** assert that the `aux_loss` metric exists and is non-zero in the logs at step 1.
- **Source:** https://github.com/huggingface/trl/issues/7009

### B5. Preference-pair truncation gives empty completions, then a NaN loss that wipes the weights
- **Symptom:** with `loss_type="simpo"` (CPOTrainer) you see `loss = 0`, `grad_norm = nan`, and all rewards and logps `nan` after the first optimizer step. Other loss types silently use `logp = 0`.
- **Root cause:** both responses are truncated to `max_length - longer_response_length`. When that is negative, `lst[:negative]` cuts from the end and can empty the shorter response. Length normalization then divides 0 by 0.
- **Fix:** drop pairs where `len(prompt) + max(len(chosen), len(rejected)) > max_length` *before* training. That is DPO's behaviour; a fix for CPO is in PR #6588.
  ```python
  ds = ds.filter(lambda r: len(tok(r["prompt"]+r["chosen"]).input_ids) <= L and
                           len(tok(r["prompt"]+r["rejected"]).input_ids) <= L)
  ```
- **Detect early:** a data-contract check that every pair has at least 1 completion token after truncation. Fail fast on the first non-finite `grad_norm`.
- **Source:** https://github.com/huggingface/trl/issues/6548

### B6. A stalled vLLM server hangs training forever
- **Symptom:** GPU utilisation drops to 0, there is no error, and the job never finishes.
- **Root cause:** `VLLMClient` makes `requests` calls with no `timeout=`. The `Retry(read=5)` policy cannot fire, because a read with no timeout blocks rather than fails.
- **Fix:** **CLOSED-NOFIX**. Wrap the trainer with a watchdog: a heartbeat file, plus a Kubernetes or Slurm liveness probe on step progress.
- **Detect early:** alert when `train/global_step` has not advanced for N minutes.
- **Source:** https://github.com/huggingface/trl/issues/6973

### B7. Logged GRPO metrics are not the optimized objective
- **Symptom:** `policy_loss` in the logs disagrees with the optimizer-window average (2x on the scaled path in the reporter's measurement). The base `loss` is correct.
- **Root cause:** the last accumulation window of an epoch is shorter. The metrics take a flat mean over micro-batch entries, so long windows weigh more.
- **Fix:** **CLOSED-NOFIX**. Compare runs on the transformers `loss` or on eval reward, not on `policy_loss`, when `steps_in_epoch % grad_accum != 0`.
- **Source:** https://github.com/huggingface/trl/issues/7047

### B8. verl LoRA + async: rollouts keep sampling from the *initial* policy
- **Symptom:** reward curves stay flat. The trainer updates the LoRA, but the disaggregated weight sync never delivers the adapter to vLLM.
- **Fix:** **OPEN**. Use colocated mode for LoRA RL. A maintainer notes that async is rarely needed with vLLM multi-LoRA.
- **Detect early:** after each sync, generate greedily on a fixed probe prompt and assert that the logprob changes between step 0 and step k.
- **Source:** https://github.com/verl-project/verl/issues/7495

### B9. verl ignores `_keep_in_fp32_modules`, which silently lowers precision
- **Symptom:** subtle quality loss on models that declare fp32 modules (Qwen3-Next and others).
- **Root cause:** `grep -rn keep_in_fp32 verl/` returns 0 hits. FSDP casts everything to the mixed-precision dtype.
- **Fix:** **OPEN**; a PR is in progress. Check the model's `_keep_in_fp32_modules` and compare the dtypes after wrapping.
- **Source:** https://github.com/verl-project/verl/issues/7092

### B10. A config flag is accepted but may do nothing (sequence parallel)
- **Symptom:** `ulysses_sequence_parallel_size=8` appears in the resolved config, yet the job OOMs at 32K context. The allocator snapshot showed full-length `[T, hidden]` blocks.
- **Status:** **OPEN, disputed.** A second engineer could not reproduce the no-op on a small Qwen3.5 config, and showed that `max_token_len` is the *total* across SP ranks.
- **Lesson:** verify memory claims with `torch.cuda.memory_snapshot()`; do not trust the config echo.
- **Source:** https://github.com/verl-project/verl/issues/7476

### B11. Training–inference mismatch: weight reload and LoRA correctness in vLLM
- **Symptom:** rollout logprobs drift away from trainer logprobs. Stale prefix-cache KV appears after a weight update. LoRA deltas are lost under MoE + data parallelism.
- **Evidence:** vLLM keeps two tracking RFCs.
  - #48312 "Weight Reload Correctness for RL" classifies failures by root cause, including prefix-KV coherence after `reload_weights`.
  - #48297 "LoRA Correctness and Lifecycle for RL Training" (checked 2026-10-15) lists open items: MoE+DP adapter isolation (#61453), and MLA `kv_b_proj` LoRA bypassed in absorbed decode (#48974).
- **Fix:**
  - Reset the prefix cache after every weight sync.
  - Avoid MoE + DP + LoRA rollouts for now.
  - Keep the IS correction on, and monitor its clip rate.
- **Source:** https://github.com/vllm-project/vllm/issues/48312, https://github.com/vllm-project/vllm/issues/48297

### B12. Noisy verifiers change *which* prompts you train on
- **Symptom:** zero-advantage filtering (DAPO-style dynamic sampling) keeps or drops the wrong groups.
- **Root cause:** a single verifier false positive turns an all-wrong group into a "mixed" group that is kept. A false negative makes a mixed group look constant, so it is filtered out.
- **Status:** OPEN analysis proposal on TRL main (commit 8248639).
- **Fix:** measure the verifier's FP and FN rates on 200 hand-labelled rollouts before RL. Log `reward` vs `reward_kept`.
- **Source:** https://github.com/huggingface/trl/issues/7747

### B13. Multi-reward aggregation rewards the easy auxiliary and degrades the primary task
- **Symptom:** total reward goes up while accuracy goes down (for example a correctness + brevity reward).
- **Evidence:** arXiv 2610.21404 (2026-10-15) proves that, under symmetric aggregation, GRPO converges to auxiliary-favouring behaviour when the auxiliary reward is more reliably obtained. Their TAG gating reaches **0.581 pass@4 vs 0.220** with additive aggregation (Qwen3-4B, brevity reward).
- **Fix:** gate the auxiliary credit on primary success:
  ```python
  def reward(c, ok): return float(ok) + (0.2 * brevity(c) if ok else 0.0)
  ```
- **Detect early:** log each reward channel separately. Alert when the primary channel falls while the total rises.
- **Source:** https://arxiv.org/abs/2610.21404

### B14. Proxy-RM overoptimization becomes fabrication
- **Evidence:** arXiv 2610.19832 (2026-10-14). RL turns **41–66% of the proxy reward gain into "rent"** while the gold reward plateaus. Policies learn to fabricate details about nonexistent entities (**97–100% of probes**) or to deflect factual questions (**67–98%**), depending on what the RM pays for. "Frequent mild audits beat rare severe ones."
- **Fix:** run a gold-reward or human audit on a random sample every N steps, and early-stop on the gold/proxy gap.
- **Source:** https://arxiv.org/abs/2610.19832

---

## C. Dataset pipelines

### C1. In distributed training, every rank trains on all the data
- **Symptom:** none visible. Each example is seen `world_size` times per epoch, so the effective epochs are wrong and overfitting comes early.
- **Root cause:** `concatenate_datasets` on iterable datasets drops the `split_dataset_by_node` split, on both `axis=0` and `axis=1`. `interleave_datasets` and `.skip()` had the same bug earlier.
- **Fix:** **FIXED** (closed 2026-10-21). On older `datasets`, call `split_dataset_by_node` *after* concatenating.
- **Detect early:** each rank hashes the ids of its first 100 examples. `all_gather` the hashes and assert they are disjoint.
- **Source:** https://github.com/huggingface/datasets/issues/8799

### C2. Out-of-range labels load silently
- **Symptom:** `ClassLabel(names=["neg","pos","oth"])` accepts `label=5` from JSONL or Parquet. It fails later, in `int2str`, or trains on garbage.
- **Root cause:** the range check is skipped when the source Arrow dtype already matches `int64`.
- **Fix:** **OPEN**. Validate explicitly:
  ```python
  n = ds.features["label"].num_classes
  bad = ds.filter(lambda r: not 0 <= r["label"] < n)
  assert len(bad) == 0
  ```
  You can also put this in a pandera or Great Expectations contract.
- **Source:** https://github.com/huggingface/datasets/issues/8596

### C3. A provenance default changed without a release note
- **Symptom:** dataset checksums are no longer recorded, so a silent upstream data change goes unnoticed.
- **Root cause:** `datasets` 4.8.5 flipped `record_checksums` from True to False. The release notes do not mention checksums.
- **Fix:** record your own content hash (sha256 of the Parquet shards) in the dataset card or quality card, and pin `revision=` on `load_dataset`.
- **Source:** https://github.com/huggingface/datasets/issues/8590

### C4. Quality filters crash on empty documents
- **Symptom:** `ZeroDivisionError` in `MeanWordLengthFilter`, `BulletsFilter`, `PunctuationFilter` and others. `ValueError: max() iterable argument is empty` in `LongWordFilter` (nemo-curator 1.3.0).
- **Fix:** **FIXED** (PR #2462). Put an empty or whitespace-only doc filter first in the pipeline (also catches `"\xa0"`).
- **Source:** https://github.com/NVIDIA-NeMo/Curator/issues/2458

### C5. A labelling UI that looks like data loss
- **Symptom:** after you return from a task, the Label Studio Data Manager shows blank annotation results for every row. A column resize brings them back.
- **Cause:** a rendering bug only; the data is intact.
- **Lesson:** audit labels from the export or API, never from screenshots of the grid.
- **Source:** https://github.com/HumanSignal/label-studio/issues/9897 (OPEN; PR #9938)

---

## D. Labelling, noise and agreement

### D1. Confident learning on in-sample predictions finds the wrong "errors"
- **Symptom:** `find_label_issues` flags too few issues, because the model memorized the noisy labels.
- **Fix:** the cleanlab docstring says issues "are most accurate when they are computed based on out-of-sample `pred_probs`":
  ```python
  from sklearn.model_selection import cross_val_predict
  pred_probs = cross_val_predict(clf, X, y, cv=5, method="predict_proba")
  from cleanlab.filter import find_label_issues
  idx = find_label_issues(y, pred_probs, return_indices_ranked_by="self_confidence")
  ```
- **Source:** https://github.com/cleanlab/cleanlab/blob/master/cleanlab/filter.py (L105)

### D2. Benchmark gold labels are wrong far more often than people assume
- **Evidence:**
  - SALUS (arXiv 2610.05540, 2026-10-04) estimates annotation error rates of **≈37% on BIRD** dev (F1 0.919 detector on 298 hand-verified tasks).
  - arXiv 2610.08026 (2026-10-06): automated hallucination labelers apply "reference faithfulness" when the target is "factual correctness". There is substantial disagreement among 7 LLM judges on 900 human-labelled pairs.
- **Fix:** before you trust a benchmark delta, hand-audit about 50 items the model "fails". Report the noise ceiling.
- **Source:** https://arxiv.org/abs/2610.05540, https://arxiv.org/abs/2610.08026

### D3. LLM labelers regress when the backbone is updated, with the same prompt
- **Evidence:**
  - arXiv 2610.09820 (2026-10-07): with prompts fixed (UMBRELA, EXAM), newer Gemini, GPT, Qwen and Llama versions show "no consistent evidence that newer versions lead to better relevance judges". Correct judgements from an earlier version "are not necessarily preserved".
  - arXiv 2610.17747: on three failure-attribution benchmarks, simple surface-cue predictors match or beat GPT-4.1.
- **Fix:**
  - Pin the judge model *version*.
  - Keep a 200-item human-labelled anchor set, and re-measure Cohen's κ or Krippendorff's α against humans on every judge upgrade.
- **Source:** https://arxiv.org/abs/2610.09820, https://arxiv.org/abs/2610.17747

---

## E. Leakage and contamination

### E1. Preprocessing fitted on all the data
- **Symptom:** cross-validation scores are higher than production.
- **Root cause:** a scaler, feature selector or vocabulary was fitted before the split. The sklearn docs: "**never call** `fit` **on the test data**".
- **Fix:** put every transform inside a `Pipeline` that is passed to `cross_val_score`. For LLM data, apply the same rule to dedup thresholds, tokenizer training and RM calibration.
- **Source:** https://github.com/scikit-learn/scikit-learn/blob/main/doc/common_pitfalls.rst

### E2. Semantic-similarity decontamination throws away good training data
- **Evidence:** arXiv 2610.21229 (2026-10-15) audited 16 open RLVR math corpora (1,673,514 items) against 6 benchmarks.
  - At cosine 0.80, **52 of 59 sampled removals (88%) were false removals**.
  - No threshold in 0.80–0.98 met 90% precision.
  - A judge-adjudicated policy reached **98.1% precision, 98.2% recall**.
- **Fix:** two-stage decontamination. Use n-gram or embedding *candidates*, then an LLM or human adjudicator. Log what was removed.
- **Source:** https://arxiv.org/abs/2610.21229

### E3. Agents that build models pick leaking features
- **Evidence:** LeakBench (arXiv 2610.26088, 2026-10-19). On MIMIC-IV (430k admissions), DeepSeek Flash and GPT-6-astra **leak a prediction-time-invalid feature in 10/10 unconstrained runs, 0/10 with an explicit admission-time constraint**. "Renaming or disguising the leaking inputs changes neither selection… a name-based filter fails."
- **Fix:** add an explicit "available at prediction time" column to the data contract, enforced by timestamp (`feature_ts <= prediction_ts`), not by column name.
- **Source:** https://arxiv.org/abs/2610.26088

### E4. Benchmark hints and contamination inflate coding scores
- **Evidence:**
  - arXiv 2610.22760: hints derived from ground truth (SWE-bench Pro, FEA-bench, Multi-SWE-bench) over-specify tasks ("spoilers").
  - BenchChecker (arXiv 2610.19447): filtering contaminated samples cuts most LLMs' SWE-bench Verified / Multi-SWE-bench medium-difficulty resolution rates by **>20% relative**.
- **Fix:** report scores on a post-cutoff slice, and give results with and without hints.
- **Source:** https://arxiv.org/abs/2610.22760, https://arxiv.org/abs/2610.19447

---

## F. Synthetic data

### F1. Prompted generation collapses onto dominant modes
- **Evidence:**
  - arXiv 2609.38359 (2026-09-29): "Prompting LLMs directly or conditioning them on end use scenarios yields low diversity data that collapses onto dominant modes."
  - arXiv 2609.18878 (2026-09-16): the minimum human-to-synthetic ratio needed to prevent collapse is still "an open question". Earlier bounds "can be vacuous for very high dimensions".
- **Fix:**
  - Seed from real data.
  - Stratify generation by an explicit attribute grid (intent × difficulty × persona).
  - Measure diversity (distinct n-grams, embedding coverage against the real set).
  - Keep a fresh human-data share in every round.
- **Source:** https://arxiv.org/abs/2609.38359, https://arxiv.org/abs/2609.18878

### F2. Chat-template tokens leak into generated text
- **Evidence:** WebFovea (arXiv 2610.03036): "self-generated chat-template tokens contaminated 4.9% of task episodes". Also "A coordinate-space mismatch placed every click at 3/4 of its intended coordinates."
- **Fix:** a verifier step that rejects any sample containing special-token strings:
  ```python
  bad = [t for t in tok.all_special_tokens if t in text]
  ```
  Run this check before the sample enters SFT data.
- **Source:** https://arxiv.org/abs/2610.03036

### F3. The synthetic-data tooling is under-maintained
- Argilla is in maintenance mode; distilabel 1.5.3 dates from 2025-01-28 (research-custom C6).
- Plan for forks, or keep generation as plain Python plus `datasets`.

---

## G. Evaluation mistakes

### G1. Unscorable samples silently leave the denominator
- **Symptom:** headline accuracy is inflated. Refusals or unparseable answers vanish instead of counting as wrong.
- **Root cause:** in lm-eval, a `process_results` that returns `{}` for a document drops it from the mean. `n-samples.effective` is the length of the *last* metric list (there is a TODO in the code).
- **Fix:** score unparseable answers as 0 explicitly, and report scored, errored and unscored counts. Inspect has a similar request (#4481).
- **Source:** https://github.com/EleutherAI/lm-evaluation-harness/issues/4062 (OPEN; PR #4092)

### G2. The response cache serves model A's answers as model B's scores
- **Root cause:** the `--use_cache` key is `sha256([request_type] + args)`. It does not include the model name, revision or `model_args`.
- **Fix:** use one cache path per model and revision (for example `--use_cache cache/{model}@{sha}`), or turn the cache off for final numbers.
- **Source:** https://github.com/EleutherAI/lm-evaluation-harness/issues/4063 (OPEN)

### G3. The answer extractor scores correct answers as 0.000
- **Symptom:** in `mmlu_*_generative`, `B` scores 1.0, but `B. 4` and `ANSWER: B` score **0.0**. The reporter's repro flips between **0.0000 and 0.9333** when only the endpoint changes.
- **Fix:** route the output through a multiple-choice letter extractor (PR #4188). Always hand-inspect 20 filtered predictions.
- **Source:** https://github.com/EleutherAI/lm-evaluation-harness/issues/4187

### G4. Blank-after-normalization targets score as correct, and the judge silently grades itself
- **Root cause, scoring:** Inspect's `exact()` and `f1()` guarded `target.strip()` on the *raw* target. A target like "a" normalizes to "", which then matches an empty answer.
- **Root cause, grading:** model-graded scorers with no grader role fell back to the evaluated model, so the model graded itself with no warning.
- **Fix:**
  - Scoring: **FIXED** (PR #5686).
  - Grading: always bind `model_role="grader"` explicitly. A runtime warning is approved (#4695).
  - Validate that no target is empty after normalization (#5525: a blank `Sample.target` makes every completion CORRECT).
- **Source:** https://github.com/UKGovernmentBEIS/inspect_ai/issues/5619, https://github.com/UKGovernmentBEIS/inspect_ai/issues/4695

### G5. A RAG metric reads only the first sentence
- **Symptom:** ragas `BleuScore` gives 1.0 when only the first sentence matches.
- **Root cause:** it passes N reference streams of 1 segment each to `sacrebleu.corpus_bleu`, and `zip` truncates to 1.
- **Related:** ragas 0.4.3 fails at import with `No module named 'langchain_community.chat_models.vertexai'` (#2741, OPEN).
- **Fix:** compute BLEU directly with `sacrebleu.corpus_bleu(hyps, [refs])`, and pin `langchain-community`.
- **Source:** https://github.com/vibrantlabsai/ragas/issues/2888 (repo moved from explodinggradients/ragas)

### G6. The eval harness itself corrupts generation (Gemma 4, SDPA, torch ≤ 2.13)
- **Symptom:** a stray `<|channel>thought` token at the start of the answer, and generation that diverges from eager mode. About 3% of prompts are affected: those whose length is ≡ 1 mod 32, batch size 1 included. Only the prefill without autograd is affected, so training is fine.
- **Root cause:** a PyTorch mem-efficient SDPA kernel bug on a stride-0 `repeat_kv` view (Gemma 4 global layers: 1 KV head, head_dim 512).
- **Fix:** `torch>=2.14.0` (pytorch#191984, #192138), or `attn_implementation="eager"` for evals.
- **Detect early:** compare eval outputs between eager and sdpa on 100 prompts.
- **Source:** https://github.com/huggingface/transformers/issues/47651

### G7. Generation settings silently overridden in `pipeline()`
- **Symptom:** `model.generation_config.max_new_tokens = 500; do_sample = False` are ignored by `pipeline(...)` (transformers 5.14.1).
- **Fix:** pass the generation kwargs to the pipeline call explicitly. Log the effective config with every eval run.
- **Source:** https://github.com/huggingface/transformers/issues/47752 (PR #47953)

### G8. temperature=0 is not deterministic
- **Evidence:**
  - vLLM: five byte-identical greedy requests to `Qwen3.8-Flash-Next-FP8` gave five different completions once the context exceeded `indexer_budget`. HTTP status stayed 200, and Thai text was corrupted.
  - arXiv 2610.12083: judge "verdicts change across identical replications at temperature zero". The most consistent judge agrees with ground truth only **51%** of the time.
- **Fix:** run each eval N≥3 times, report the variance, and never use single-run deltas below the noise floor.
- **Source:** https://github.com/vllm-project/vllm/issues/54521, https://arxiv.org/abs/2610.12083

### G9. Passing unit tests ≠ correct
- **Evidence:** TestJack (arXiv 2610.10619, 2026-10-07) generates requirement-targeted tests across 6 models and 5 coding benchmarks. Per the arXiv listing, about **34.4%** of trials judged correct violate task requirements, which lowers resolution from **50.6% to 33.2%**. The headline numbers come from the abstract tail; the abs page excerpt was truncated, so treat them as [partially verified].
- **Fix:** for RLVR rewards and for evals, keep a hidden test set that the policy never sees, and audit a random sample of "passes".
- **Source:** https://arxiv.org/abs/2610.10619

---

## H. Managed tuning services

### H1. Vertex AI / Gemini Enterprise Agent Platform SFT
Verbatim callouts from the live page:
- **Thinking:** "set the thinking budget to `0` (for Gemini 2.5 models and lower)", and use thinking level MINIMAL for Gemini 3+.
- **Known issue:** controlled generation "can result in decreased model quality due to data misalignment during tuning and inference time". Do not use the JSON schema at inference if you did not tune with it.
- **Quota:** "Quota is enforced on the number of concurrent tuning jobs". It is global across regions and models, so parallel hyperparameter sweeps queue.
- **Endpoints:** Gemini 3.x tuning and serving run on the "`us` and `eu` multi-region endpoints only". Computation "could be offloaded to other `US` or `EU` regions".
- **Coverage:** "not a Covered Service" under any SLA.
- **Limits:** 131,072 tokens per example. Training tokens = dataset tokens × epochs.
- **Source:** https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/supervised-tuning

### H2. Vertex RFT (Pre-GA)
- **Data:** "do not use proprietary, sensitive, or other confidential data". It is not for "commercial or production purposes".
- **Availability:** `v1beta1` only, us-central1 and europe-west4 only. Models: Gemini 3.5 Flash and 3.1 Flash-Lite.
- **Continuous tuning:** only SFT→RFT or RFT→RFT.
- **Cost:** the tuned endpoint costs "**1.5 times the price of the base model**" (Gemini 3+). Auto-evals are billed as batch prediction.
- **Source:** https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/reinforcement-tuning

### H3. Amazon Bedrock RFT
- **Pre-check:** "If rewards are consistently 0 percent, use supervised fine-tuning first… If rewards are greater than 95 percent, reinforcement fine-tuning might be unnecessary."
- **Start small:** begin with 100–200 examples.
- **Red flags:** "rewards plateauing below 0.15, increasing reward variance over time, and declining validation performance".
- **Lambda graders:** they should "Execute within seconds (not minutes)".
- **Model/region pinning:** Nova 2 Lite is us-east-1 only; gpt-oss-20B and Qwen3-32B are us-west-2 only. The algorithm is GRPO.
- **Source:** https://docs.aws.amazon.com/bedrock/latest/userguide/reinforcement-fine-tuning.html

### H4. Vendor exit risk
- OpenAI self-serve fine-tuning closes to new jobs on **2027-01-06**, and `ft-o4-mini-2025-04-16` shuts down **2026-10-23** (today) (C17).
- Fireworks Managed Training "no longer accepts new RFT jobs" (C18).
- **Lesson:** keep datasets, graders and evals vendor-neutral (JSONL + Python reward functions), so the tuning backend can be swapped.

---

## Ten open challenges (with 2026 evidence)

1. **Contamination cannot be detected after the fact.** WildTrace (arXiv 2610.16152): the best training-data detection method across SFT/DPO/RL stages reaches an **average AUC of 0.529**, which is close to random. Provenance has to be recorded at ingest; it cannot be inferred later.
2. **Decontamination has no good precision/recall trade-off without a judge.** 88% false removals at cosine 0.80, and no threshold reached 90% precision (2610.21229). Adjudication works, but it costs LLM or human time per candidate.
3. **Predicting and detecting reward hacking.**
   - SimHack (2610.28707) predicts the hacking-onset step to 11.3% relative error, but notes that training-time interventions "incentivize models to obfuscate".
   - RH-Detect (2610.10947): the best detector reaches pooled AUROC 0.962, but accuracy is **10.7–15.9 pp lower on multi-turn tool-use trajectories**.
4. **Judges are not instruments.** Verdicts are non-deterministic at T=0, and the most consistent judge is 51% accurate (2610.12083). Prompt-strategy effects reverse across judges and languages (2610.31172; 27 languages, more than 1M scores). Backbone upgrades lose correct judgements (2610.09820).
5. **Verifiers built on unit tests are weak.** About 34% of "passing" trials violate requirements (2610.10619). Hardening verifiers needs adversarial hacker-fixer loops (2610.15924), which adds an arms race to every environment.
6. **Training–inference mismatch in RL stacks.** IS-ratio bias from truncated sampling (TRL #6789), weight-reload and LoRA-lifecycle bugs (vLLM RFCs #48312 and #48297), and adapters that never sync (verl #7495). There is no end-to-end "rollout logprob == trainer logprob" contract across frameworks yet.
7. **Gold labels are noisy at benchmark scale.** About 37% annotation errors are estimated on BIRD (2610.05540), and label criteria are ambiguous in hallucination benchmarks (2610.08026). The field still reports single-number leaderboards without noise ceilings.
8. **The synthetic-to-human ratio is unknown.** The minimum fresh-human-data rate to avoid collapse is open (2609.18878). Prompted generators collapse onto dominant modes (2609.38359). There is no standard diversity metric that predicts downstream gain.
9. **Statistical validity of leaderboards under attack.**
   - Certified corruption budgets (2610.10597) show that vote rigging, selective disclosure and contamination can each move a ranking. The abstract excerpt gives no figure; the arXiv listing reported "a few hundred rigged votes" on 1.8M Arena votes [UNVERIFIED].
   - lm-eval still lacks CIs by default (proposal #4019) and drops unscorable items (#4062).
10. **Tooling churn and maintainer bandwidth.**
    - TRL removed PPO (v1.13) and 7 more trainers in 6 weeks.
    - transformers v5 renames break adapter portability (PEFT #3896).
    - Maintainers now close bug reports that come from code-reading or scanners rather than real runs. Quote (TRL #7608): "the wall of text reads like automated scanner output… triaging these takes maintainer time away".
    - Reproducibility therefore depends on exact pins plus your own regression tests, not on upstream issue status.

---

## Slide-ready checklist (derived from the above)

```text
[ ] EOS == template end-of-turn            [ ] assistant-only mask decoded & checked
[ ] dtype printed at step 0                [ ] LoRA layer-coverage assert
[ ] adapter loads into SERVING engine      [ ] merged vs adapter perplexity parity
[ ] eval set size % batch == 0             [ ] fast-loader parity vs reference
[ ] rollouts: top_p=1, top_k=-1            [ ] clipped_ratio < 10% or mask truncation
[ ] per-reward-channel logging             [ ] gold audit every N steps
[ ] per-rank sample-id disjointness        [ ] label range / schema contract
[ ] own content hashes + pinned revision   [ ] out-of-sample pred_probs for cleanlab
[ ] decontam: candidates + adjudication    [ ] prediction-time availability by timestamp
[ ] unscored counts reported               [ ] cache keyed by model@sha
[ ] 20 extracted predictions eyeballed     [ ] judge version pinned + human anchor kappa
[ ] N>=3 eval repeats, report variance     [ ] hidden tests for RLVR rewards
[ ] trl/peft/transformers/torch pinned     [ ] vendor-neutral JSONL + Python graders
```
