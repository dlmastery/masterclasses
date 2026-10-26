# Hands-on labs: preference tuning and RL with TRL, plus managed RFT (OpenAI, Vertex/Gemini)

Research date: **2026-10-23**. This file is for the hands-on part of the "Customizing modern AI (SFT, RL, RAG) and data-centric AI" deck. It builds on `research-custom/03-rl.md` and `09-critic-corrections.md`, and does not repeat the theory (GRPO math, DAPO/Dr. GRPO history, the provider timeline) that is already there.

**Verification legend**
- **[V-src]**: read in library source at the pinned tag (file path and line given).
- **[V-doc]**: read on the official docs page (URL given).
- **[RAN]**: I ran the code on this machine (Windows, Python 3.12, CPU) and the output shown is real. This applies only to the pure-Python reward/grader code. pip is blocked here, so TRL, PEFT and math-verify could not be installed.
- **Illustrative**: the output shape is real (metric names verified in source), but the numbers are not from a run.
- **[UNVERIFIED]**: not confirmed.

---

## 0. Version pins (checked on PyPI JSON on 2026-10-23)

| Package | Latest | Uploaded | Notes |
|---|---|---|---|
| `trl` | **1.16.0** | 2026-10-15 | `requires_python >=3.11`. Python 3.10 cannot install it. |
| `transformers` | 5.20.2 | 2026-10-19 | TRL needs `>=4.56.2`. |
| `peft` | 0.21.2 | 2026-10-01 | |
| `datasets` | 5.1.0 | 2026-10-05 | TRL needs `>=4.7.0`. |
| `accelerate` | 1.15.0 | 2026-09-09 | TRL needs `>=1.10.1`. |
| `math-verify` | 0.9.0 | 2026-01-10 | Pulls `latex2sympy2_extended==1.11.0`. Needed by `trl.rewards.accuracy_reward`. |
| `trackio` | 0.43.0 | 2026-10-20 | `report_to="trackio"` is a supported value in transformers 5.20.2 (`training_args.py`). |
| `vllm` | **0.32.0** | 2026-10-18 | **Gotcha:** `trl[vllm]` pins `vllm>=0.22.0,<=0.31.0` (TRL `pyproject.toml` @v1.16.0). Pin `vllm==0.31.0`. |
| `torch` | 2.14.1 | 2026-09-30 | |
| `openai` | 3.37.0 | 2026-10-22 | |
| `google-genai` | 2.33.0 | 2026-10-23 | Has `client.tunings.validate_reward` and `TuningMethod.REINFORCEMENT_TUNING`. |

Common install line for Labs 1 to 6 (Linux + one NVIDIA GPU with 24 GB or more, e.g. L4, A10G, RTX 4090, A100):

```bash
python -m venv .venv && source .venv/bin/activate        # Python 3.11 or 3.12
pip install "trl[peft,math_verify]==1.16.0" "transformers==5.20.2" "peft==0.21.2" \
            "datasets==5.1.0" "accelerate==1.15.0" "math-verify==0.9.0" "trackio==0.43.0"
# optional fast generation: pip install "vllm==0.31.0"   (NOT 0.32.0, see the pin above)
export HF_TOKEN=hf_...            # only needed for gated models / pushing to the Hub
```

Every lab uses a small, ungated model: `Qwen/Qwen2.5-0.5B-Instruct`, `Qwen/Qwen2.5-Coder-0.5B-Instruct` (both confirmed on the HF API).

### Verified TRL 1.16.0 facts used across the labs [V-src]

All paths are in `https://github.com/huggingface/trl/blob/v1.16.0/`.

| Fact | Where |
|---|---|
| `GRPOConfig.learning_rate=1e-6`, `num_generations=8`, `max_completion_length=512`, `beta=0.0` ("reference model is not loaded"), `epsilon=0.2`, `epsilon_high=None` (DAPO recommends 0.28), `scale_rewards="group"`, `loss_type="dapo"`, `mask_truncated_completions=False`, `multi_objective_aggregation="sum_then_normalize"`, `use_bias_correction_kl=True`, `log_completions=False` | `trl/trainer/grpo_config.py` L423, L480, L494, L681, L693, L705, L789, L801, L836, L777, L972, L985 |
| `loss_type` options: `grpo, dr_grpo, dapo, bnpo, cispo, sapo, luspo, vespo` | `grpo_config.py` L801-834 |
| Every TRL config: `logging_steps=10`, `gradient_checkpointing=True`, `bf16=True` unless fp16 | `trl/trainer/base_config.py` |
| A model given as a string loads in **float32** unless `model_init_kwargs={"dtype": ...}` | `grpo_trainer.py` docstring L171-174; `trl/trainer/utils.py` `create_model_from_path` (`dtype = kwargs.get("dtype", "float32")`) |
| Reward functions are called as `f(prompts=..., completions=..., completion_ids=..., **dataset_columns, trainer_state=..., log_extra=..., log_metric=...)` | `grpo_trainer.py` L1584-1628 |
| `None` from a reward function becomes NaN, so that reward is skipped for that row; if all rewards are None the advantage is forced to 0 | `grpo_trainer.py` L1630, L2756-2801 |
| A string in `reward_funcs` loads `AutoModelForSequenceClassification.from_pretrained(..., num_labels=1)` | `grpo_trainer.py` L551-560 |
| With `beta>0` and a PEFT model there is no second model; the reference is "adapter disabled" | `grpo_trainer.py` L982-990; `dpo_trainer.py` L908-914 |
| KL estimator: `exp(ref-logp) - (ref-logp) - 1` (k3), times the IS ratio when `use_bias_correction_kl` | `grpo_trainer.py` L3098-3105 |
| GRPO logged metrics: `reward`, `reward_std`, `frac_reward_zero_std`, `rewards/<func>/mean`, `rewards/<func>/std`, `completions/mean_length`, `completions/min_length`, `completions/max_length`, `completions/clipped_ratio`, `completions/mean_terminated_length`, `entropy`, `kl` (only if beta≠0), `clip_ratio/region_mean`, `clip_ratio/low_mean`, `clip_ratio/high_mean`, `num_tokens` | `grpo_trainer.py` L2293-2320, L2823-2830, L3268-3283 |
| `DPOConfig`: `beta=0.1`, `learning_rate=1e-6`, `max_length=1024`, `loss_type=["sigmoid"]` (list), `loss_weights=None`, `label_smoothing=0.0`, `disable_dropout=True`, `precompute_ref_log_probs=False` | `trl/trainer/dpo_config.py` L156, L185, L195, L227, L245, L254, L288, L297 |
| DPO logged metrics: `rewards/chosen`, `rewards/rejected`, `rewards/accuracies`, `rewards/margins`, `logps/chosen`, `logps/rejected`, `logits/chosen`, `logits/rejected`, `entropy`, `mean_token_accuracy` | `dpo_trainer.py` (`_metrics[mode][...]`) |
| `RewardConfig.learning_rate=1e-4`, `max_length=1024` (longer pairs are **filtered out**), `center_rewards_coefficient=None` (recommended 0.01) | `trl/trainer/reward_config.py` L98, L144, L160 |
| RewardTrainer loss: `-logsigmoid(r_c - r_r - margin)` if a `margin` column exists; logs `accuracy`, `margin`, `min_reward`, `mean_reward`, `max_reward` | `reward_trainer.py` L788-815 |
| RewardTrainer + LoRA: "highly recommended to set `modules_to_save=["score"]`" | `reward_trainer.py` L324-327 |
| Built-in rewards: `accuracy_reward` (reads column `solution`), `reasoning_accuracy_reward`, `get_cosine_scaled_reward`, `think_format_reward`, `get_repetition_penalty_reward`, `get_soft_overlong_punishment` | `trl/rewards/__init__.py` |

---

## Lab 1: Unit-test your verifiable rewards before you spend a GPU hour (refund agent, CPU only)

> **Verifier (2026-10-23):** VERIFIED: re-run by the verifier on CPU (Python 3.12), output identical. TRL 1.16.0 reward-kwarg contract (`log_extra`, `log_metric`, `trainer_state`, count-mismatch ValueError) confirmed in `grpo_trainer.py`.

**Goal.** Write the reward functions for a refund-decision agent, which answers `<answer>{"decision": ..., "refund_amount": ..., "reason": ...}</answer>`. Unit-test them on hand-written completions, including a deliberate hack, before training. This is the cheapest bug-finding step in all of RL.

**Scenario.** An e-commerce refund agent. Gold labels (`gold_decision`, `gold_amount`) come from the refund-policy engine of record.

**Prerequisites.** Python 3.11 or newer only. The test runs with no packages. The same functions plug into `GRPOTrainer` unchanged.

**Code** (`refund_rewards.py`) **[RAN]**

```python
# refund_rewards.py - verifiable rewards for a refund-decision agent (TRL GRPO signature)
import json
import re

ANSWER_RE = re.compile(r"<answer>\s*(\{.*?\})\s*</answer>", re.DOTALL)
DECISIONS = {"approve", "deny", "escalate"}
REQUIRED = {"decision", "refund_amount", "reason"}


def _parse(text):
    """Return the JSON dict inside <answer>...</answer>, or None."""
    m = ANSWER_RE.search(text)
    if not m:
        return None
    try:
        obj = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def format_reward(completions, **kwargs):
    """0.2 if the answer block parses and has the 3 required keys, else 0.0."""
    out = []
    for c in completions:
        obj = _parse(c[0]["content"])
        ok = obj is not None and REQUIRED <= obj.keys() and obj.get("decision") in DECISIONS
        out.append(0.2 if ok else 0.0)
    return out


def decision_reward(completions, gold_decision, gold_amount, **kwargs):
    """1.0 = right decision and amount within $0.01; 0.5 = right decision only; 0.0 otherwise.
    Returns None for rows without a gold label, so TRL skips this reward for that row."""
    out = []
    for c, gd, ga in zip(completions, gold_decision, gold_amount, strict=True):
        if gd is None:
            out.append(None)
            continue
        obj = _parse(c[0]["content"])
        if obj is None or not REQUIRED <= obj.keys() or obj.get("decision") != gd:  # schema gate
            out.append(0.0)
            continue
        try:
            amount_ok = abs(float(obj.get("refund_amount")) - float(ga)) <= 0.01
        except (TypeError, ValueError):
            amount_ok = False
        out.append(1.0 if amount_ok else 0.5)
    return out


if __name__ == "__main__":
    good = '<think>Item unopened, 12 days.</think><answer>{"decision": "approve", "refund_amount": 49.99, "reason": "within 30 days"}</answer>'
    wrong_amt = '<answer>{"decision": "approve", "refund_amount": 40, "reason": "x"}</answer>'
    hack = '<answer>{"decision": "approve"}</answer> approve deny escalate'
    broken = "Sure! I approved it."
    comps = [[{"role": "assistant", "content": t}] for t in (good, wrong_amt, hack, broken)]
    print("format  :", format_reward(comps))
    print("decision:", decision_reward(comps, gold_decision=["approve"] * 4, gold_amount=[49.99] * 4))
    print("no-label:", decision_reward(comps[:1], gold_decision=[None], gold_amount=[None]))
```

**Run**

```bash
python refund_rewards.py
```

**Expected output** **[RAN]**, exact output on this machine:

```
format  : [0.2, 0.2, 0.0, 0.0]
decision: [1.0, 0.5, 0.0, 0.0]
no-label: [None]
```

**The bug this test caught [RAN].** The first draft did not have the `not REQUIRED <= obj.keys()` gate. The hack completion `{"decision": "approve"}` followed by `approve deny escalate` then scored **0.5** on `decision_reward` (`decision: [1.0, 0.5, 0.5, 0.0]`), even though it scored 0.0 on `format_reward`. That is auxiliary/partial credit with no real answer. GRPO would amplify it: within a group, a 0.5 that costs zero tokens beats a 0.0. Rule: **gate partial credit on schema validity.**

**TRL built-ins, same test style [RAN].** I loaded the two dependency-free modules from the v1.16.0 source tree.

```python
from trl.rewards import think_format_reward, get_soft_overlong_punishment
think_format_reward([[{"content": "<think>\nok\n</think>\nanswer"}], [{"content": "answer <think>x</think>"}]])
# -> [1.0, 0.0]   (the regex demands the completion START with <think>)
p = get_soft_overlong_punishment(max_completion_len=512, soft_punish_cache=128)
p([[0]*300, [0]*448, [0]*480, [0]*512, [0]*600])
# -> [0.0, -0.5, -0.75, -1.0, -1.0]   (linear ramp from 384 to 512 tokens, DAPO Eq. 13)
```

**Walk-through**
1. `def format_reward(completions, **kwargs)`: the TRL reward contract. Each `completions` item is a list with one message dict (conversational) and the text is in `c[0]["content"]` (verified in `trl/rewards/format_rewards.py`). `**kwargs` is required because TRL always passes `prompts`, `completion_ids`, `trainer_state`, `log_extra`, `log_metric` and every extra dataset column.
2. `decision_reward(completions, gold_decision, gold_amount, **kwargs)`: named parameters receive the **dataset columns with the same names**, repeated once per generation (`grpo_trainer.py` L1584-1585).
3. `out.append(None)`: TRL turns `None` into NaN and excludes that reward for the row. Use it for multi-task datasets where only some rows have a gold label (L1630; docstring L190-196).
4. `zip(..., strict=True)`: a silent length mismatch would mis-align rewards and completions. TRL also raises if you return the wrong count (L1631-1636).
5. `1.0 / 0.5 / 0.0` graded credit gives GRPO a variance signal even when no sample in the group is fully right. That fights the "zero-std group" problem (Lab 2).

**Common errors**
- `TypeError: decision_reward() missing 1 required positional argument: 'gold_amount'`. Cause: the dataset has no `gold_amount` column, or the trainer dropped it. Fix: add the column. Keep `remove_unused_columns=False`, which is the GRPO default (`grpo_config.py` L473).
- `ValueError: The reward function 'decision_reward' returned 3 rewards, but 4 were expected (one per prompt-completion pair).` Cause: you skipped a row with `continue` and appended nothing. Fix: always append (0.0 or None) (`grpo_trainer.py` L1631-1636).
- `TypeError: string indices must be integers`. Cause: the dataset is in **standard** (plain-text) format, so each completion is a `str`, not `[{"content": ...}]`. Fix: index `c` directly, or switch the dataset to conversational `prompt` messages.

**Best practice.** Keep a `tests/test_rewards.py` with at least one **known hack** per reward ("right key, no answer", "keyword stuffing", "empty JSON", "answer in the wrong tag") and run it in CI. 2026 papers show that the *structure* of verifier errors matters more than their rate: learnable false positives cause plateaus or collapse (arXiv 2610.17824).

**Variation.** Add `log_extra("parsed_decision", [...])` inside `decision_reward`. In the trainer, that column appears in the completions table next to each sample (`grpo_trainer.py` L1553-1563).

---

## Lab 2: GRPO with a math verifier: insurance-claim payout calculator

> **Verifier (2026-10-23):** VERIFIED against trl 1.16.0 source (`GRPOConfig` defaults, `accuracy_reward`, `get_soft_overlong_punishment`, divisibility errors, `trl[vllm]` pin `<=0.31.0`). FIXED by verifier: `SYSTEM` is now a raw string (the `\b` in `\boxed` was a backspace character). Still UNVERIFIED: `trackio show` CLI name.

**Goal.** RL-train a 0.5B model to compute claim payouts (deductible, then coinsurance share, then policy limit). Use `trl.rewards.accuracy_reward` (math-verify) plus a DAPO soft length penalty, with LoRA, and log reward and length.

**Scenario.** A claims back-office. The procedural generator gives **exact** gold answers and a controllable difficulty mix. Prompts with a mix of difficulties matter in low-data RLVR (see the 2610.25812 notes below).

**Prerequisites.** The install line in §0 and one 24 GB GPU. Optional: `HF_TOKEN`; `trackio` gives a local dashboard.

**Code**: `claims_data.py` (shared with Lab 4) and `lab2_grpo_claims.py`

```python
# claims_data.py - procedural insurance-claim payout problems with exact gold answers
import random
from datasets import Dataset

SYSTEM = r"You are a claims adjuster. Think briefly, then give the payout as \boxed{number}."  # raw string: "\b" is a backspace otherwise

def make_claim(rng):
    damage = rng.randrange(500, 20000, 50)
    deductible = rng.choice([250, 500, 1000])
    share = rng.choice([70, 80, 90, 100])            # % insurer pays after the deductible
    limit = rng.choice([5000, 10000, 15000])
    payout = min(max(damage - deductible, 0) * share / 100, limit)
    q = (f"Damage ${damage}. Deductible ${deductible}. Insurer pays {share}% after the "
         f"deductible, capped at ${limit}. What is the payout in dollars?")
    return {"prompt": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": q}],
            "solution": f"{payout:g}"}               # accuracy_reward reads `solution`

def claims_dataset(n, seed):
    rng = random.Random(seed)
    return Dataset.from_list([make_claim(rng) for _ in range(n)])
```

```python
# lab2_grpo_claims.py - GRPO + LoRA on insurance-claim payouts (TRL 1.16.0)
from peft import LoraConfig
from trl import GRPOConfig, GRPOTrainer
from trl.rewards import accuracy_reward, get_soft_overlong_punishment
from claims_data import claims_dataset

train = claims_dataset(2000, seed=7)
heldout = claims_dataset(64, seed=99)          # different seed = disjoint-ish eval prompts

args = GRPOConfig(
    output_dir="qwen-claims-grpo",
    model_init_kwargs={"dtype": "bfloat16"},   # TRL default is float32 for string model ids
    learning_rate=1e-5,                        # LoRA: ~10x the 1e-6 full-FT GRPO default
    per_device_train_batch_size=8,
    gradient_accumulation_steps=4,             # 32 completions per step = 4 prompts x 8
    num_generations=8,
    max_completion_length=256,
    loss_type="dapo", beta=0.0,                # the TRL defaults, written out on purpose
    mask_truncated_completions=True,           # DAPO: do not learn from cut-off answers
    reward_weights=[1.0, 0.5],
    max_steps=300, logging_steps=5, save_steps=100,
    eval_strategy="steps", eval_steps=50, per_device_eval_batch_size=8,
    log_completions=True, num_completions_to_print=2,
    report_to="trackio",
)
trainer = GRPOTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    reward_funcs=[accuracy_reward,
                  get_soft_overlong_punishment(max_completion_len=256, soft_punish_cache=64)],
    args=args,
    train_dataset=train,
    eval_dataset=heldout,
    peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear", task_type="CAUSAL_LM"),
)
trainer.train()
trainer.save_model()
```

The generator itself was run **[RAN]**. Sample rows with `seed=7`:

```
Damage $8750. Deductible $250. Insurer pays 100% after the deductible, capped at $15000. ... -> 8500
Damage $1700. Deductible $250. Insurer pays 70% after the deductible, capped at $10000. ... -> 1015
Damage $15400. Deductible $250. Insurer pays 80% after the deductible, capped at $5000. ... -> 5000
Damage $2700. Deductible $500. Insurer pays 100% after the deductible, capped at $5000. ... -> 2200
```

**Run**

```bash
python lab2_grpo_claims.py              # single GPU
# multi-GPU: accelerate launch --num_processes 2 lab2_grpo_claims.py
trackio show                            # local dashboard [CLI name UNVERIFIED; else open the URL trackio prints]
```

**Expected output (illustrative).** The metric keys are verified in `grpo_trainer.py`. The numbers are not from a run.

```
{'loss': 0.0123, 'grad_norm': 0.41, 'learning_rate': 9.8e-06, 'num_tokens': 61440.0,
 'completions/mean_length': 141.2, 'completions/clipped_ratio': 0.06,
 'rewards/accuracy_reward/mean': 0.31, 'rewards/soft_overlong_punishment_reward/mean': -0.04,
 'reward': 0.29, 'reward_std': 0.38, 'frac_reward_zero_std': 0.25, 'entropy': 0.62,
 'clip_ratio/region_mean': 0.0, 'epoch': 0.08}
...
{'rewards/accuracy_reward/mean': 0.66, 'completions/mean_length': 118.5, 'frac_reward_zero_std': 0.47, ...}
```

How to read the curves:
- `rewards/accuracy_reward/mean` should rise.
- `frac_reward_zero_std` is the share of groups whose 8 samples all scored the same, which gives **zero advantage and no gradient**. Rising toward 1.0 means the data became too easy (or stayed too hard). Re-mix the difficulty.
- `completions/clipped_ratio` rising means answers hit the 256-token cap. Raise the cap or strengthen the length penalty.

**Walk-through**
1. `model_init_kwargs={"dtype": "bfloat16"}`: without it, TRL loads string model ids in **float32**, which is about 2x the memory, slower, and a common OOM cause on 24 GB cards (`grpo_trainer.py` L171-174).
2. `per_device_train_batch_size=8, gradient_accumulation_steps=4, num_generations=8`: TRL sets `generation_batch_size = per_device × processes × steps_per_generation` (= grad-accum by default). It must divide by `num_generations` (`grpo_config.py` L1096-1135). Here that is 32 completions = 4 prompts × 8.
3. `accuracy_reward` parses the gold `solution` with math-verify. It only accepts **LaTeX-anchored** answers from the model (`try_extract_without_anchor=False`, boxed first), so the system prompt asks for `\boxed{}` (`trl/rewards/accuracy_rewards.py` L85-96). If the gold cannot be parsed it returns `None`, so the row is skipped and not scored 0.
4. `get_soft_overlong_punishment(256, 64)`: 0 up to 192 tokens, then a linear ramp to −1 at 256. It needs `completion_ids` and is picklable for AsyncGRPO (`other_rewards.py` L83-138).
5. `mask_truncated_completions=True`: truncated samples are excluded from the loss, per the DAPO recommendation (`grpo_config.py` L836-842).
6. `loss_type="dapo", beta=0.0`: the TRL 1.16 defaults, written out so students see them. There is no reference model and no KL. Lab 4 adds KL.

**Common errors**
- `ValueError: generation_batch_size (6) must be divisible by num_generations (8).` Cause: e.g. `per_device_train_batch_size=6`, grad-accum 1. Fix: make per-device × GPUs × grad-accum a multiple of 8 (`grpo_config.py` L1131-1135).
- `ImportError: Please install the math_verify package to use accuracy_reward`. Fix: `pip install "math-verify==0.9.0"` or `trl[math_verify]` (`accuracy_rewards.py` L65).
- `ValueError: auto_find_batch_size is not supported by GRPO ...`. Fix: remove `auto_find_batch_size=True` and lower `per_device_train_batch_size` (L1089-1094).
- **Windows/slow rewards (gotcha).** math-verify uses `signal.alarm` on Unix but "on Windows systems, uses a multiprocessing-based approach ... This will incur a huge performance penalty" (`Math-Verify/src/math_verify/utils.py`, main branch). TRL also disables the timeouts off the main thread (`accuracy_rewards.py` L73-82). Run RL labs on Linux, WSL2 or Colab.

**Best practice.** Before RL, **measure the base model's pass rate per prompt** (8 samples each) and drop or downsample prompts at 0/8 and 8/8. They only add zero-std groups. "Where Groups Split" (arXiv 2610.25325, 18 Oct 2026) shows a short probe run predicts which prompts will *stay* informative better than the base pass rate does.

**Variation.** Set `use_vllm=True, vllm_mode="colocate", vllm_gpu_memory_utilization=0.3` (the defaults; `grpo_config.py` L587-660) with `pip install vllm==0.31.0`. Then compare tokens/sec, and check that `sampling/importance_sampling_ratio/mean` stays close to 1 (the vLLM-vs-trainer mismatch is corrected by `vllm_importance_sampling_mode="sequence_mask"`, which is the default).

---

## Lab 3: GRPO with a code-execution reward: support-ticket router

> **Verifier (2026-10-23):** VERIFIED: `code_reward.py` self-test re-run by the verifier, output identical (`[1.0, 0.25, 0.0, 0.0]`). TRL 1.16.0 GRPO API confirmed. Still UNVERIFIED: model id `Qwen2.5-Coder-1.5B-Instruct`.

**Goal.** Train a coder model to write `route_ticket(subject, body) -> str` for a helpdesk. The reward is the fraction of **hidden** unit tests passed, run in a subprocess with a timeout.

**Scenario.** Support-ticket triage into `billing / outage / account / other`. The prompt shows 3 labelled tickets; the 9 test tickets are never shown. That avoids test leakage into the prompt, which would make the reward memorizable.

**Prerequisites.** §0 install. The sandbox here is **a teaching sandbox only**: `subprocess` with `-I` isolated mode, a temp dir and a 5 s timeout. It is not a security boundary. Use a container, gVisor, Firecracker, or a remote sandbox for untrusted code at scale.

**Code**: `code_reward.py` **[RAN]** and `lab3_grpo_code.py`

```python
# code_reward.py - unit-test reward for generated Python (TRL GRPO reward signature)
import os
import re
import subprocess
import sys
import tempfile

CODE_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)
HARNESS = """
import json, sys
{code}
tests = json.loads(sys.argv[1])
passed = 0
for t in tests:
    try:
        passed += route_ticket(t["subject"], t["body"]) == t["queue"]
    except Exception:
        pass
print(passed / len(tests))
"""

def unit_test_reward(completions, tests, log_metric=None, **kwargs):
    rewards, timeouts = [], 0
    for c, t in zip(completions, tests, strict=True):
        m = CODE_RE.search(c[0]["content"])
        if not m:
            rewards.append(0.0)
            continue
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "cand.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write(HARNESS.format(code=m.group(1)))
            try:
                r = subprocess.run([sys.executable, "-I", path, t], cwd=d, capture_output=True,
                                   text=True, timeout=5)
                rewards.append(float(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else 0.0)
            except subprocess.TimeoutExpired:
                timeouts += 1
                rewards.append(0.0)
            except (ValueError, IndexError):
                rewards.append(0.0)
    if log_metric is not None:
        log_metric("code/timeout_rate", timeouts / len(completions))
    return rewards

if __name__ == "__main__":
    import json
    tests = json.dumps([
        {"subject": "Charged twice", "body": "my card was billed two times", "queue": "billing"},
        {"subject": "Site down", "body": "502 error since 9am", "queue": "outage"},
        {"subject": "Reset password", "body": "cannot log in", "queue": "account"},
        {"subject": "Hello", "body": "do you ship to Peru?", "queue": "other"},
    ])
    good = """```python
def route_ticket(subject, body):
    t = (subject + " " + body).lower()
    if any(k in t for k in ("charge", "bill", "refund", "invoice")): return "billing"
    if any(k in t for k in ("down", "502", "outage", "error")): return "outage"
    if any(k in t for k in ("password", "log in", "login", "account")): return "account"
    return "other"
```"""
    lazy = "```python\ndef route_ticket(subject, body):\n    return 'billing'\n```"
    loop = "```python\nwhile True: pass\n```"
    comps = [[{"role": "assistant", "content": x}] for x in (good, lazy, loop, "no code")]
    print(unit_test_reward(comps, [tests] * 4, log_metric=lambda k, v: print("metric", k, v)))
```

```python
# lab3_grpo_code.py - GRPO with a unit-test reward: write a support-ticket router
import json
import random
from datasets import Dataset
from peft import LoraConfig
from trl import GRPOConfig, GRPOTrainer
from code_reward import unit_test_reward

TICKETS = [  # (subject, body, queue) - in production: a labelled sample of real tickets
    ("Charged twice", "my card was billed two times", "billing"),
    ("Refund status", "where is my refund for order 1182", "billing"),
    ("Invoice wrong", "VAT number missing on invoice", "billing"),
    ("Site down", "502 error since 9am", "outage"),
    ("App not loading", "spinner forever on login page, all users", "outage"),
    ("API timeouts", "every request times out in eu-west", "outage"),
    ("Reset password", "cannot log in after reset", "account"),
    ("Change email", "please update the email on my account", "account"),
    ("2FA lost", "new phone, lost authenticator", "account"),
    ("Hello", "do you ship to Peru?", "other"),
    ("Partnership", "we would like to resell your product", "other"),
    ("Feedback", "love the new dashboard", "other"),
]
PROMPT = ("Write a Python function `route_ticket(subject: str, body: str) -> str` that returns one of "
          "'billing', 'outage', 'account', 'other'. Examples:\n{shots}\nReturn only a ```python code block.")

def make_row(rng):
    rows = rng.sample(TICKETS, len(TICKETS))
    shots, hidden = rows[:3], rows[3:]                # hidden tests never appear in the prompt
    shot_txt = "\n".join(f"- {s!r}, {b!r} -> {q!r}" for s, b, q in shots)
    tests = [{"subject": s, "body": b, "queue": q} for s, b, q in hidden]
    return {"prompt": [{"role": "user", "content": PROMPT.format(shots=shot_txt)}],
            "tests": json.dumps(tests)}

rng = random.Random(0)
train = Dataset.from_list([make_row(rng) for _ in range(400)])

args = GRPOConfig(
    output_dir="qwen-ticket-router-grpo",
    model_init_kwargs={"dtype": "bfloat16"},
    learning_rate=1e-5, per_device_train_batch_size=8, gradient_accumulation_steps=2,
    num_generations=8, max_completion_length=384, temperature=1.0,
    max_steps=200, logging_steps=5, report_to="trackio",
    log_completions=True, num_completions_to_print=1,
)
trainer = GRPOTrainer(
    model="Qwen/Qwen2.5-Coder-0.5B-Instruct",
    reward_funcs=unit_test_reward,
    args=args, train_dataset=train,
    peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear", task_type="CAUSAL_LM"),
)
trainer.train()
```

**Run**

```bash
python code_reward.py          # reward self-test, CPU, ~6 s (one sample hits the 5 s timeout on purpose)
python lab3_grpo_code.py       # GPU training
```

**Expected output, self-test** **[RAN]**:

```
metric code/timeout_rate 0.25
[1.0, 0.25, 0.0, 0.0]
```

Read it this way:
- The keyword router passes 4/4 tests.
- The **lazy constant** `return 'billing'` still earns **0.25**. That is the class prior, and it is a classic partial-credit attractor. Balance the queues in the hidden tests, or subtract the constant-baseline score.
- The infinite loop is killed by the timeout and scores 0.
- "No code" scores 0.

On a real row from `make_row` (seed 0), a 4-keyword-list solution scored `[1.0]` on the 9 hidden tests **[RAN]**.

**Training log (illustrative):**

```
{'rewards/unit_test_reward/mean': 0.41, 'code/timeout_rate': 0.02, 'completions/mean_length': 162.0, 'frac_reward_zero_std': 0.31, ...}
```

**Walk-through**
1. `unit_test_reward(completions, tests, log_metric=None, **kwargs)`: `tests` is a dataset column (JSON string). `log_metric` is injected by GRPO (`grpo_trainer.py` L1594). Your custom scalars are averaged per logging step and printed next to `kl` and `entropy` (L1565-1576, L2850-2855).
2. `subprocess.run([sys.executable, "-I", path, t], cwd=d, timeout=5)`: separate process, isolated mode (no user site, no CWD on `sys.path`), throwaway directory, and a hard wall-clock limit. Timeouts score 0 and are counted.
3. `CODE_RE = r"```python\n(.*?)```"`: extract only the fenced block. Anything outside it is ignored, so chatter around the code is never executed.
4. `shots, hidden = rows[:3], rows[3:]`: the **hidden tests differ from the in-prompt examples** on every row.
5. `temperature=1.0` (the GRPO default; `grpo_config.py` L532) keeps group diversity. With low temperature, all 8 samples are the same program, giving zero std and no gradient.

**Common errors**
- Training hangs or the rollout step takes minutes. Cause: no `timeout=` (a `while True` sample blocks the reward call), or too many concurrent subprocesses. Fix: always set a timeout, and make the reward `async def` so TRL runs the async reward funcs with `asyncio.gather` (`grpo_trainer.py` L1621, L1640-1660).
- `IndexError: list index out of range` inside the reward. Cause: the candidate printed nothing (crashed before `print`). The code here catches it (`except (ValueError, IndexError)`). Never let a reward raise mid-training.
- `frac_reward_zero_std` near 1.0 from step 0. Cause: the tasks are too hard for a 0.5B model (all 0) or too easy (all 1). Fix: change the mix of tickets per row, or start from `Qwen2.5-Coder-1.5B-Instruct` [model id not checked this session; UNVERIFIED].

**Best practice.** Reward hacking in coding RL is often **detectable but hard to prevent**. SimHack (arXiv 2610.28707, Google, 20 Oct 2026) predicts *when* hacking becomes dominant from a few small reference runs. They report a median-onset relative error of 11.3% and found curricula that "train for 96.6% longer without hacking". The practical habit: log a cheap hack detector (e.g. `code/hardcoded_return_rate`, `code/timeout_rate`) via `log_metric` from step 0.

**Variation.** Add a side-effect check, in the spirit of "Finding Side-Effect Loopholes in Verifiable Rewards" (arXiv 2610.09142). There, verifiers that "check only the requested change" passed runs with unrequested writes, and "one count assertion per template rejected all six duplicates". The analogue here: assert that `route_ticket` does not mutate globals or write files.

---

## Lab 4: KL control, multi-reward aggregation and length logging (claims calculator, two runs)

> **Verifier (2026-10-23):** VERIFIED against trl 1.16.0 (`multi_objective_aggregation="normalize_then_sum"`, reward-weights error) and transformers 5.20.2 (`should_training_stop`). FIXED by verifier: `BOX_RE` was `r"\boxed..."`, which matches word-boundary + `oxed` and never matched real model output; now `r"\\boxed..."`, and the self-test uses raw strings. Re-run: output unchanged.

**Goal.** Run the same RL job with `beta=0.0` and with `beta=0.04`. Add a brevity reward **gated on correctness**, use `normalize_then_sum` aggregation, and add a callback that stops training if total reward rises while the primary reward falls.

**Why gate.** "Multi-Reward Hacking" (arXiv 2610.21404, 15 Oct 2026) proves that symmetric aggregation lets GRPO converge to auxiliary-favouring behaviour when the auxiliary reward is easier to get. On Qwen3-4B with a brevity reward, their gated method (TAG) gets **0.581 pass@4 vs 0.220 for additive aggregation**, "while shortening responses by 44%". The gating below is a minimal TAG-style version (anchor = correctness), not their full algorithm.

**Prerequisites.** Lab 2 files (`claims_data.py`) and the §0 install.

**Code**: `lab4_rewards.py` **[RAN]** and `lab4_kl_length.py`

```python
# lab4_rewards.py - correctness-anchored brevity reward with a warm-up (multi-reward hacking guard)
import re

BOX_RE = re.compile(r"\\boxed\{([^{}]*)\}")   # literal backslash; r"\boxed" would mean word-boundary + "oxed"

def _is_correct(text, gold):
    m = BOX_RE.findall(text)
    try:
        return bool(m) and abs(float(m[-1].replace(",", "").replace("$", "")) - float(gold)) < 0.01
    except ValueError:
        return False

def gated_brevity_reward(completions, completion_ids, solution, trainer_state=None,
                         log_metric=None, target_tokens=120, warmup_steps=50, **kwargs):
    """Brevity credit ONLY for correct answers (anchor = correctness), ramped in after warm-up."""
    step = trainer_state.global_step if trainer_state is not None else warmup_steps
    ramp = min(1.0, step / warmup_steps)
    out, gated = [], 0
    for c, ids, gold in zip(completions, completion_ids, solution, strict=True):
        if not _is_correct(c[0]["content"], gold):
            out.append(0.0)          # wrong + short earns nothing (no auxiliary-only credit)
            gated += 1
            continue
        out.append(ramp * max(0.0, 1.0 - len(ids) / (2 * target_tokens)))
    if log_metric is not None:
        log_metric("brevity/gated_frac", gated / len(out))
        log_metric("brevity/ramp", ramp)
    return out

if __name__ == "__main__":
    class S: global_step = 25
    comps = [[{"content": r"...so \boxed{8500}"}], [{"content": r"\boxed{1}"}], [{"content": r"long... \boxed{8500}"}]]
    ids = [[0] * 40, [0] * 5, [0] * 200]
    print(gated_brevity_reward(comps, ids, ["8500"] * 3, trainer_state=S(), log_metric=lambda k, v: print(k, v)))
```

```python
# lab4_kl_length.py - KL control + anchored brevity reward + a reward-hacking tripwire
import sys
from peft import LoraConfig
from transformers import TrainerCallback
from trl import GRPOConfig, GRPOTrainer
from trl.rewards import accuracy_reward
from claims_data import claims_dataset
from lab4_rewards import gated_brevity_reward

BETA = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0       # run once with 0.0, once with 0.04

class HackTripwire(TrainerCallback):
    """Stop if total reward rises while the primary (accuracy) reward falls."""
    def __init__(self, patience=3):
        self.best_acc, self.bad, self.patience = -1.0, 0, patience
    def on_log(self, args, state, control, logs=None, **kwargs):
        acc = (logs or {}).get("rewards/accuracy_reward/mean")
        if acc is None:
            return
        if acc > self.best_acc:
            self.best_acc, self.bad = acc, 0
        elif acc < self.best_acc - 0.05:
            self.bad += 1
            print(f"[tripwire] step {state.global_step}: accuracy {acc:.3f} < best {self.best_acc:.3f}")
            control.should_training_stop = self.bad >= self.patience

args = GRPOConfig(
    output_dir=f"claims-kl{BETA}",
    model_init_kwargs={"dtype": "bfloat16"},
    learning_rate=1e-5, per_device_train_batch_size=8, gradient_accumulation_steps=4,
    num_generations=8, max_completion_length=384,
    beta=BETA,                  # > 0 adds KL to the start model and logs `kl` (LoRA: adapter-off = reference)
    reward_weights=[1.0, 0.3],
    multi_objective_aggregation="normalize_then_sum",   # GDPO-style per-reward normalisation
    max_steps=300, logging_steps=5, report_to="trackio", run_name=f"kl{BETA}",
)
trainer = GRPOTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    reward_funcs=[accuracy_reward, gated_brevity_reward],
    args=args, train_dataset=claims_dataset(3000, seed=11),
    peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear", task_type="CAUSAL_LM"),
    callbacks=[HackTripwire()],
)
trainer.train()
```

**Run**

```bash
python lab4_rewards.py                 # CPU self-test
python lab4_kl_length.py 0.0           # run A: no KL (TRL default)
python lab4_kl_length.py 0.04          # run B: KL-anchored
trackio show                           # overlay runs kl0.0 and kl0.04 [CLI UNVERIFIED]
```

**Expected output, self-test [RAN]:**

```
brevity/gated_frac 0.3333333333333333
brevity/ramp 0.5
[0.4166666666666667, 0.0, 0.08333333333333331]
```

The short correct answer earns brevity credit, the short **wrong** `\boxed{1}` earns nothing, and the long correct answer earns little. All values are halved because step 25 sits at 50% of the warm-up.

**Training logs (illustrative). What to compare between runs A and B:**

```
run kl0.0  step 300: rewards/accuracy_reward/mean 0.71  completions/mean_length 96   entropy 0.31
run kl0.04 step 300: rewards/accuracy_reward/mean 0.68  completions/mean_length 121  entropy 0.47  kl 0.012
```

Expected direction, not a guarantee:
- With KL, the policy stays closer to the base model: higher entropy and slower length collapse.
- Without KL, gains come faster on a verifiable task.
- `kl` only appears when `beta != 0` (`grpo_trainer.py` L3267-3268).

**Walk-through**
1. `beta=BETA`: with a LoRA model, TRL does not load a second model. The reference is the same weights with the adapter disabled (`grpo_trainer.py` L982-990), so KL is almost free in memory.
2. `multi_objective_aggregation="normalize_then_sum"`: each reward is z-scored within its group *before* weighting. A low-variance auxiliary reward then cannot be drowned out, and cannot dominate just because of its scale (`grpo_config.py` L777-788; implementation L2789-2799, citing GDPO).
3. `trainer_state.global_step`: GRPO passes the `TrainerState` to every reward function (L1588), so curricula and warm-ups need no custom trainer.
4. `HackTripwire.on_log(..., logs=...)`: GRPO merges its averaged `_metrics` into `logs` before `Trainer.log` (`grpo_trainer.py` L3304-3320). `rewards/accuracy_reward/mean` is therefore visible to callbacks. Setting `control.should_training_stop = True` is the standard transformers stop signal (`trainer_callback.py`).
5. `reward_weights=[1.0, 0.3]`: must have the same length as `reward_funcs` (`grpo_trainer.py` L568-574).

**Common errors**
- `ValueError: Number of reward weights (3) must match number of reward functions (2)` (L571).
- A dataset column with the same name as a reward keyword parameter (e.g. a `target_tokens` column) **silently overrides the default** with a list, because every dataset column is passed as a kwarg (L1584-1585). That fails later with something like `TypeError: unsupported operand type(s) for *: 'int' and 'list'`. Fix: rename the column or the parameter.
- OOM when `beta>0` **without** LoRA. Cause: full fine-tuning plus `beta>0` loads a full reference model (L992-1003). Fix: use LoRA, set `beta=0`, or use DeepSpeed ZeRO-3.

**Best practice.** For **verifiable** rewards, start with `beta=0.0` (the TRL default, and the DAPO/Dr. GRPO consensus). For **learned or judge** rewards (Lab 5b), keep `beta>0`. The 2026 survey "Checking the Checkers" (arXiv 2610.17824) notes that under KL regularization or a fixed budget, random verifier errors "also lower final accuracy". So KL is not free when your verifier is noisy either. Measure.

**Variation.** Theory note for the slide: "On the Impossibility of Unbiased and Length-Invariant Policy Optimization" (arXiv 2607.23364, 25 Jul 2026) proves that no length weighting is both gradient-unbiased and length-invariant. GRPO (`loss_type="grpo"`) and Dr. GRPO (`"dr_grpo"`) sit at opposite ends. Run `loss_type="grpo"` vs `"dr_grpo"` vs `"dapo"` and plot `completions/mean_length` for wrong answers.

---

## Lab 5: Train a reward model (HR-policy assistant), then use it as a GRPO reward

> **Verifier (2026-10-23):** VERIFIED against trl 1.16.0 source (`RewardConfig` defaults, `margin` support, `num_labels=1` check, `modules_to_save=["score"]` advice, string reward model loading). Still UNVERIFIED: exact `OSError` text, `datasets` cast error text.

**Goal.** Train a Bradley-Terry reward model with `RewardTrainer` on preference pairs, using per-pair **margins** and reward centering. Merge it and plug it into `GRPOTrainer` as `reward_funcs="hr-rm-merged"`, guarded by a cheap verifiable reward and a KL anchor.

**Scenario.** An internal HR-policy assistant. HR reviewers rated answer pairs on a 1-9 scale, and the score gap becomes `margin`. UltraFeedback (`score_chosen - score_rejected`) supplies general preference signal. Its columns are verified on the HF API: `chosen, rejected, score_chosen, score_rejected`.

**Prerequisites.** §0 install and about 24 GB GPU. Downloads `trl-lib/ultrafeedback_binarized` (5,000 rows).

**Code**: `lab5_reward_model.py`

```python
# lab5_reward_model.py - train a Bradley-Terry reward model for HR-policy answers (TRL 1.16.0)
from datasets import Dataset, concatenate_datasets, load_dataset
from peft import LoraConfig
from trl import RewardConfig, RewardTrainer

def u(t): return {"role": "user", "content": t}
def a(t): return {"role": "assistant", "content": t}

HR = [  # (question, preferred answer, rejected answer, rater score gap 1-9)
    ("How many vacation days do new hires get?",
     "New hires accrue 1.67 days per month (20 days/year). See HR Policy 4.2.", "Probably around 20.", 6),
    ("Can I carry over unused PTO?",
     "Yes, up to 5 days into Q1 of the next year (Policy 4.5); the rest expires.", "Yes, all of it carries over.", 8),
    ("Is remote work allowed from another country?",
     "Up to 30 days/year with manager and Legal approval (Policy 7.1). Longer stays need a tax review.",
     "Sure, work from anywhere!", 8),
]
hr = Dataset.from_list([{"chosen": [u(q), a(c)], "rejected": [u(q), a(r)], "margin": float(m)}
                        for q, c, r, m in HR] * 50)          # oversample the in-domain pairs

uf = load_dataset("trl-lib/ultrafeedback_binarized", split="train[:5000]")
uf = uf.map(lambda x: {"margin": float(x["score_chosen"] - x["score_rejected"])})
uf = uf.select_columns(["chosen", "rejected", "margin"])
train = concatenate_datasets([uf, hr.cast(uf.features)]).shuffle(seed=0)
split = train.train_test_split(test_size=0.05, seed=0)

args = RewardConfig(
    output_dir="hr-reward-model",
    model_init_kwargs={"dtype": "bfloat16"},
    per_device_train_batch_size=8, num_train_epochs=1, learning_rate=1e-4,   # 1e-4 = RewardConfig default
    max_length=1024, center_rewards_coefficient=0.01,
    eval_strategy="steps", eval_steps=100, logging_steps=10, report_to="trackio",
)
trainer = RewardTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct", args=args,
    train_dataset=split["train"], eval_dataset=split["test"],
    peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear",
                           task_type="SEQ_CLS", modules_to_save=["score"]),
)
trainer.train()
print(trainer.evaluate())
merged = trainer.model.merge_and_unload()          # GRPO loads RMs by path, so ship a plain model
merged.save_pretrained("hr-rm-merged")
trainer.processing_class.save_pretrained("hr-rm-merged")
```

**Code**: `lab5b_grpo_with_rm.py`

```python
# lab5b_grpo_with_rm.py - use the merged HR reward model as a GRPO reward (plus a cheap guard)
from datasets import Dataset
from peft import LoraConfig
from trl import GRPOConfig, GRPOTrainer

QUESTIONS = ["How many vacation days do new hires get?", "Can I carry over unused PTO?",
             "Is remote work allowed from another country?", "How do I report harassment?"]
train = Dataset.from_list([{"prompt": [{"role": "user", "content": q}]} for q in QUESTIONS] * 100)

def cites_policy(completions, **kwargs):           # verifiable guard against RM over-optimisation
    return [0.5 if "Policy" in c[0]["content"] else 0.0 for c in completions]

args = GRPOConfig(output_dir="hr-assistant-grpo", model_init_kwargs={"dtype": "bfloat16"},
                  learning_rate=1e-5, num_generations=8, max_completion_length=256,
                  beta=0.02,                        # learned RM -> keep a KL anchor (unlike RLVR)
                  reward_weights=[1.0, 1.0], max_steps=150, logging_steps=5, report_to="trackio")
trainer = GRPOTrainer(model="Qwen/Qwen2.5-0.5B-Instruct",
                      reward_funcs=["hr-rm-merged", cites_policy],   # str -> AutoModelForSequenceClassification
                      args=args, train_dataset=train,
                      peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear",
                                             task_type="CAUSAL_LM"))
trainer.train()
```

**Run**

```bash
python lab5_reward_model.py
python lab5b_grpo_with_rm.py
```

**Expected output (illustrative; keys verified in `reward_trainer.py` L802-815):**

```
{'loss': 0.58, 'accuracy': 0.69, 'margin': 0.74, 'min_reward': -3.1, 'mean_reward': 0.02, 'max_reward': 3.4, ...}
{'eval_loss': 0.55, 'eval_accuracy': 0.71, 'eval_margin': 0.81, ...}
```

`mean_reward` stays near 0 because of `center_rewards_coefficient=0.01`. Without it, RM scores drift. Then a GRPO `reward_weights` choice made at one scale silently changes meaning.

**Walk-through**
1. `"margin": float(x["score_chosen"] - x["score_rejected"])`: when the column exists, the loss becomes `-logsigmoid(r_c - r_r - margin)` (`reward_trainer.py` L789-792). Strongly preferred pairs must be separated by more. Note that the margin is in **raw score units**. Rescale it if your gaps are large (e.g. divide by the max gap) [scaling advice is mine, not from the TRL docs].
2. `hr.cast(uf.features)`: `concatenate_datasets` needs identical features. Casting the in-code rows to UltraFeedback's schema avoids a feature mismatch. The exact error text varies by `datasets` version [UNVERIFIED].
3. `task_type="SEQ_CLS", modules_to_save=["score"]`: the reward head is new and randomly initialised. Without `modules_to_save`, LoRA trains only adapters and the score head stays random (`reward_trainer.py` L324-327).
4. `merge_and_unload()` + `save_pretrained`: GRPO loads string reward models with `AutoModelForSequenceClassification.from_pretrained(path, num_labels=1)` (`grpo_trainer.py` L551-560), so give it a plain merged checkpoint plus tokenizer.
5. `reward_funcs=["hr-rm-merged", cites_policy]` and `beta=0.02`: mixing a model and a function is allowed (docstring L198-199). The verifiable guard and the KL anchor limit RM over-optimisation.

**Common errors**
- `ValueError: The model has num_labels=2, but reward models require num_labels=1 ...` Cause: you passed a pre-built classifier. Fix: pass the model id as a string (TRL sets `num_labels=1`), or build with `num_labels=1` (`reward_trainer.py` L413-419).
- The training set silently shrinks. Cause: `RewardConfig.max_length=1024` **filters out** pairs where either side is longer (`reward_config.py` L144-149). Fix: check `len(trainer.train_dataset)` and raise `max_length` for long HR answers.
- In 5b: `OSError: hr-rm-merged does not appear to have a file named config.json`. Cause: you saved only the LoRA adapter. Fix: merge first, as in the code [exact message text UNVERIFIED].

**Best practice.** **Do not select a reward model by static accuracy alone.** "Scaling Laws for Generative Reward Models" (arXiv 2610.30765, 22 Oct 2026) found that judges with higher static gold-label accuracy often trained **worse** policies: Answer-Only rewarders won "in seven of eight matched settings", and intermediate checkpoints could beat later, more accurate ones. Evaluate each RM candidate by a short downstream RL run and judge on a held-out eval.

**Variation.** Add Dynalize-style evolving penalties (arXiv 2610.26496, 19-20 Oct 2026). Every N steps, have an LLM read a sample of rollouts and write a regex or judge penalty for behaviours the RM over-rewards, such as boilerplate disclaimers. Append it as a third reward function, and use `trainer_state.global_step` to switch it on.

---

## Lab 6: DPO + LoRA for on-brand support replies

> **Verifier (2026-10-23):** VERIFIED against trl 1.16.0 source (`DPOConfig` defaults, `loss_type` list incl. `sft` and `sigmoid_norm`, `loss_weights` length ValueError, `ref_model` same-object error).

**Goal.** Align a support assistant's tone with preference pairs (on-brand vs off-brand replies) using `DPOTrainer`. Combine the sigmoid DPO loss with an SFT term, and read the DPO metrics correctly.

**Scenario.** A customer-support QA team marks replies as on-brand (empathetic, specific, takes action) or off-brand (dismissive, blames the customer). Three seed pairs here are oversampled ×100 and mixed with 3,000 UltraFeedback pairs to keep general ability.

**Prerequisites.** §0 install and about 16-24 GB GPU.

**Code**: `lab6_dpo_support.py`

```python
# lab6_dpo_support.py - DPO + LoRA for support-reply tone (TRL 1.16.0)
from datasets import Dataset, concatenate_datasets, load_dataset
from peft import LoraConfig
from trl import DPOConfig, DPOTrainer

def turn(q, r): return [{"role": "user", "content": q}, {"role": "assistant", "content": r}]

PAIRS = [  # (customer message, on-brand reply, off-brand reply) - from QA-reviewed tickets
    ("My package is 5 days late.",
     "Sorry about the delay. Your parcel is at the Leeds depot and arrives tomorrow; I added a $5 credit.",
     "Shipping delays happen. Please wait."),
    ("I was charged twice!",
     "You're right, I see two charges of $49.99. I refunded the duplicate; it shows in 3-5 business days.",
     "Contact your bank about card issues."),
    ("Your app deleted my notes.",
     "I'm sorry. Notes stay in Trash for 30 days: Settings > Trash > Restore. Want me to restore them now?",
     "We don't delete user data. You probably did it yourself."),
]
support = Dataset.from_list([{"chosen": turn(q, c), "rejected": turn(q, r)} for q, c, r in PAIRS] * 100)
uf = load_dataset("trl-lib/ultrafeedback_binarized", split="train[:3000]").select_columns(["chosen", "rejected"])
train = concatenate_datasets([uf, support.cast(uf.features)]).shuffle(seed=0)
split = train.train_test_split(test_size=0.05, seed=0)

args = DPOConfig(
    output_dir="support-dpo",
    model_init_kwargs={"dtype": "bfloat16"},
    beta=0.1,                                  # KL strength: higher = stay closer to the SFT model
    loss_type=["sigmoid", "sft"], loss_weights=[1.0, 0.2],   # DPO + NLL on chosen (RPO-style)
    learning_rate=5e-6,                        # LoRA; full FT default is 1e-6
    per_device_train_batch_size=4, gradient_accumulation_steps=4,
    max_length=1024, num_train_epochs=1,
    eval_strategy="steps", eval_steps=50, logging_steps=10, report_to="trackio",
)
trainer = DPOTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",        # ref_model=None -> frozen copy of the start model
    args=args, train_dataset=split["train"], eval_dataset=split["test"],
    peft_config=LoraConfig(r=16, lora_alpha=32, target_modules="all-linear", task_type="CAUSAL_LM"),
)
trainer.train()
trainer.save_model()
```

**Run**

```bash
python lab6_dpo_support.py
```

**Expected output (illustrative; keys verified in `dpo_trainer.py`):**

```
{'loss': 0.69, 'rewards/chosen': 0.00, 'rewards/rejected': 0.00, 'rewards/accuracies': 0.0, 'rewards/margins': 0.0, 'logps/chosen': -182.4, 'logps/rejected': -201.7, ...}
{'loss': 0.41, 'rewards/chosen': -0.21, 'rewards/rejected': -1.35, 'rewards/accuracies': 0.86, 'rewards/margins': 1.14, 'logps/chosen': -184.5, ...}
```

How to read it:
- The margin grows mostly because **rejected** falls. Per the TRL docs, DPO in practice works "by suppressing the likelihood of dispreferred completions" (see 03-rl.md). A slowly falling `logps/chosen` is normal.
- A fast fall is a warning: raise the `sft` weight or `beta`.
- `rewards/accuracies` near 1.0 within 50 steps on a tiny in-domain set means memorization. Check the eval split.

**Walk-through**
1. `{"chosen": turn(q, c), "rejected": turn(q, r)}`: the **implicit prompt** format. Each side holds the full conversation. TRL maps `extract_prompt` to split off the shared prefix (`dpo_trainer.py` L1054). An explicit `prompt` column also works (docstring L222).
2. `beta=0.1`: the DPO KL strength (`dpo_config.py` L297-303). Higher means smaller deviation from the reference. For `loss_type="ipo"` it is τ instead.
3. `loss_type=["sigmoid", "sft"], loss_weights=[1.0, 0.2]`: losses are a **list** in TRL 1.x. The two lists must have the same length (`dpo_config.py` L245-262, L360-364).
4. No `ref_model`: with PEFT, TRL uses the adapter-disabled base as the reference, so there is no second copy in memory (L908-914).
5. `learning_rate=5e-6`: the DPO default is `1e-6` for full fine-tuning (L156). LoRA usually needs several times more. Per "The Shape of the DPO Hyperparameter Landscape" (arXiv 2610.27895, 20 Oct 2026), the optimal LR "varies with model size", hyperparameters "are not transferable across training datasets", and validation loss is "a poor proxy" for downstream quality. Sweep LR × β with short runs, scored on your downstream eval.

**Common errors**
- `ValueError: loss_weights must have the same length as loss_type when combining multiple losses. Got 1 weights for 2 loss types.` (`dpo_config.py` L360-364)
- `ValueError: model and ref_model cannot be the same object. In most cases you should omit ref_model ...` (`dpo_trainer.py` L590-594). Fix: omit `ref_model`.
- `TypeError: train_dataset must be a Dataset or IterableDataset, got DatasetDict.` Cause: you passed `load_dataset(...)` without `split=`. Fix: `split="train"` (`dpo_trainer.py` L552-554).

**Best practice.** Audit preference labels before DPO. Under adversarial or noisy label flips, DPO can be steered toward an attacker's target (arXiv 2610.24945, 18 Oct 2026, proposes Trim-K Robust-DPO). The cheap built-in option is `label_smoothing=0.1` (Robust DPO; must be in [0, 0.5); `dpo_config.py` L288-295). Also watch generations for **vocabulary collapse**. ECHO (arXiv 2610.29410, 21 Oct 2026) shows that preference optimisation can improve every ranking metric while a hidden shared offset grows until one token dominates decoding. They also found that "the better a run ranks held-out responses, the less often two public reward models prefer its samples". Sample and read outputs at every eval.

**Variation.** Swap `loss_type=["sigmoid_norm"]` (SimPO-style length-normalised) and compare the mean reply length. Or set `precompute_ref_log_probs=True` for full fine-tuning without keeping a reference model in memory (`dpo_config.py` L227-233).

---

## Lab 7: OpenAI graders and reinforcement fine-tuning (refund agent), the portable part

> **Verifier (2026-10-23):** VERIFIED against openai 3.37.0 source (`fine_tuning.alpha.graders.run(grader, model_sample, item)` / `validate(grader)`, `ReinforcementMethodParam`, hyperparameter names, `GraderRunResponse.metadata.errors.*`, `string_check` operations). Local `grade()` part re-runnable. API job creation not testable (o4-mini retired 2026-10-23).

**Status first [V-doc].** https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning:
- "OpenAI is winding down the fine-tuning platform."
- "Eligible existing customers can create training jobs until January 6, 2027, unless the base model shuts down earlier."
- RFT is "currently only for o4-mini". `o4-mini-2025-04-16` and its fine-tunes shut down on **October 23, 2026, today**.
- The graders guide adds: "OpenAI is deprecating graders as part of the evals and fine-tuning workflows" (no date; https://developers.openai.com/api/docs/guides/graders).

**Teach this lab as "graders are reward functions"**: the design transfers to TRL (Lab 1) and Vertex (Lab 8). Treat the job-creation part as reference. Expect it to fail for most orgs from today.

**Goal.** Build a `multi` grader from a `python` grader (decision + amount) and a `string_check` grader (cites policy id). Unit-test the Python grader locally, then `validate` and `run` it server-side.

**Prerequisites**

```bash
pip install "openai==3.37.0"
export OPENAI_API_KEY=sk-...
```

**Code**: `lab7_openai_graders.py`. Signatures were verified in openai 3.37.0 installed locally (`inspect.signature`) and in source.

```python
# lab7_openai_graders.py - refund-policy graders: test locally, validate + run on OpenAI, (optionally) RFT
import json
import os
from openai import OpenAI

GRADE_SRC = r'''
import json, re
def grade(sample, item) -> float:
    m = re.search(r"\{.*\}", sample["output_text"], re.DOTALL)
    if not m:
        return 0.0
    try:
        out = json.loads(m.group(0))
    except Exception:
        return 0.0
    if out.get("decision") != item["gold_decision"]:
        return 0.0
    try:
        ok = abs(float(out.get("refund_amount", -1)) - float(item["gold_amount"])) <= 0.01
    except (TypeError, ValueError):
        ok = False
    return 1.0 if ok else 0.5
'''
policy = {"type": "python", "name": "policy", "source": GRADE_SRC}
tag = {"type": "string_check", "name": "tag", "operation": "ilike",
       "input": "{{sample.output_text}}", "reference": "{{item.policy_id}}"}   # must cite the policy id
grader = {"type": "multi", "name": "refund_grader", "graders": {"policy": policy, "tag": tag},
          "calculate_output": "0.8 * policy + 0.2 * tag"}

item = {"gold_decision": "approve", "gold_amount": "49.99", "policy_id": "RP-30"}
sample = '{"decision": "approve", "refund_amount": 49.99, "reason": "Unopened, day 12 of 30 (RP-30)"}'

ns = {}
exec(GRADE_SRC, ns)                                    # 1) free local unit test first
print("local policy score:", ns["grade"]({"output_text": sample}, item))

client = OpenAI()                                      # 2) server-side checks (needs OPENAI_API_KEY)
print(client.fine_tuning.alpha.graders.validate(grader=grader))
run = client.fine_tuning.alpha.graders.run(grader=grader, model_sample=sample, item=item)
print("reward:", run.reward, "sub:", run.sub_rewards, "errors:", run.metadata.errors)

if os.getenv("LAUNCH_RFT") == "1":                     # 3) only for still-eligible orgs, see notes
    train_id = client.files.create(file=open("refunds_train.jsonl", "rb"), purpose="fine-tune").id
    val_id = client.files.create(file=open("refunds_val.jsonl", "rb"), purpose="fine-tune").id
    job = client.fine_tuning.jobs.create(
        model="o4-mini-2025-04-16", training_file=train_id, validation_file=val_id,
        method={"type": "reinforcement", "reinforcement": {
            "grader": grader, "hyperparameters": {"reasoning_effort": "medium", "n_epochs": 2}}},
        suffix="refund-rft")
    print(job.id, job.status)
```

**Run**

```bash
python lab7_openai_graders.py                 # local test + validate + run
LAUNCH_RFT=1 python lab7_openai_graders.py    # only if your org is still eligible (see status)
```

**Expected output.** The local part is **[RAN]** (first line exact). The API part is illustrative; the response field names are verified in `types/fine_tuning/alpha/grader_run_response.py`.

```
local policy score: 1.0
GraderValidateResponse(grader=MultiGrader(...))
reward: 1.0 sub: {'policy': 1.0, 'tag': 1.0} errors: MetadataErrors(formula_parse_error=False, ..., python_grader_runtime_error=False, ...)
```

`0.8*1.0 + 0.2*1.0 = 1.0`, so a sample that passes both sub-graders must print **1.0**. Use that as a self-check on the formula.

Extra local tests of `grade()` **[RAN]**:
- wrong amount: 0.5
- free text "I approve it": 0.0
- `{"decision": "deny"}`: 0.0
- reasoning text before the JSON: 1.0 (the regex finds the JSON anywhere)

**Walk-through**
1. `def grade(sample, item) -> float`: the required Python-grader entry point. It takes "exactly two arguments". `sample["output_text"]` is the model output, and `item` is the JSONL row without `messages`. Exceptions or non-floats score 0 [V-doc graders guide].
2. `"graders": {"policy": ..., "tag": ...}` + `"calculate_output": "0.8 * policy + 0.2 * tag"`: the docs' multi grader uses an **object keyed by name**, and the keys are the formula variables [V-doc]. **SDK typing gotcha:** in openai 3.37.0, `MultiGraderParam.graders` is typed as a single-grader union, not a dict (`types/graders/multi_grader_param.py`). TypedDicts are not enforced at runtime, so follow the docs and ignore the type-checker warning.
3. `client.fine_tuning.alpha.graders.validate(grader=...)` and `.run(grader=, model_sample=, item=)`: `POST /fine_tuning/alpha/graders/validate|run` (`resources/fine_tuning/alpha/graders.py` L43-127). The response has `reward`, `sub_rewards` and `metadata.errors.*` flags, such as `python_grader_runtime_error` and `formula_parse_error`.
4. `method={"type": "reinforcement", "reinforcement": {"grader": ..., "hyperparameters": {...}}}`: `ReinforcementMethodParam` has only `grader` (required) and `hyperparameters`. The hyperparameters are `batch_size`, `compute_multiplier`, `eval_interval`, `eval_samples`, `learning_rate_multiplier`, `n_epochs`, `reasoning_effort` (`types/fine_tuning/reinforcement_*_param.py`). The REST guide also shows a `response_format` key under `reinforcement`. It is not in the 3.37.0 TypedDict [docs/SDK mismatch; passing it untested].
5. `{{item.policy_id}}` / `{{sample.output_text}}`: the template namespaces. `sample.output_json` is only populated when you train with a `response_format` [V-doc].

**Common errors and limits [V-doc unless marked]**
- Python grader limits: code under 256 kB, **no network**, 2-minute execution limit, 2 GB RAM, 1 GB disk, 2 CPU cores. Only preinstalled packages are available (numpy, scipy, sympy, pandas, rapidfuzz, scikit-learn, jsonschema, pydantic, ...). `import requests` therefore fails at runtime and the sample scores 0.
- `metadata.errors.formula_parse_error=True` from `run`. Cause: a variable in `calculate_output` does not match a key in `graders`. Fix: rename one so they match.
- Job creation on a retired model (`o4-mini-2025-04-16` after 2026-10-23) or by a non-eligible org is rejected [exact error text UNVERIFIED]. Fix: move the same grader logic to Lab 1 (TRL) or Lab 8 (Vertex `code_execution_reward_scorer`).
- Dataset limits: at most 50,000 training examples and at most 1,000 test examples [V-doc].

**Best practice.** OpenAI's own guidance [V-doc]:
- Produce "a smooth score, not a pass/fail stamp".
- Guard against reward hacking ("Models being trained sometimes learn to exploit weaknesses in model graders").
- Run several candidate responses through any LLM judge, using few-shot examples of great, fair and poor answers.

That is why `policy` here returns 0 / 0.5 / 1.

**Variation.** Replace `tag` with a `score_model` grader that checks the `reason` is policy-grounded. Its fields are `input` (messages), `model`, `range` (default `[0, 1]`) and `sampling_params` (`types/graders/score_model_grader_param.py`). Then compare its scores with human labels on 50 items before trusting it.

---

## Lab 8: Gemini reinforcement fine-tuning on Vertex AI (Pre-GA), with reward validation

> **Verifier (2026-10-23):** VERIFIED against google-genai 2.33.0 source (`validate_reward(parent, sample_response, example, single_reward_config)`, `SingleReinforcementTuningRewardConfig`, `ReinforcementTuningCodeExecutionRewardScorer.python_code_snippet`, `CreateTuningJobConfig.reward_config/samples_per_prompt/thinking_level/validation_dataset_uri`, `ReinforcementTuningThinkingLevel` = MINIMAL/HIGH, Vertex -> v1beta1). Vertex doc limits not re-fetched by the verifier.

**Status [V-doc]** (https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/reinforcement-tuning and subpages):
- **Pre-GA**, "solely for limited testing and evaluation, and may not be used for commercial or production purposes". The docs also say "do not use proprietary, sensitive, or other confidential data".
- Models: **Gemini 3.5 Flash** and **Gemini 3.1 Flash-Lite**, tuned in `us-central1` or `europe-west4`, served from the `us`/`eu` multi-region endpoint.
- **v1beta1 API only.**

**Goal.** Express the refund reward as a **code-execution reward** (`def evaluate(example, response) -> float`). Validate it with `validate_reward` (no training cost), then launch an RFT job with `client.tunings.tune`.

**Prerequisites**

```bash
pip install "google-genai==2.33.0"
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=my-project RFT_BUCKET=gs://acme-rft-data
```

You need the Vertex AI API enabled and the JSONL files uploaded. Dataset line schema [V-doc, tuning-dataset page]:

```json
{"systemInstruction": {"role": "system", "parts": [{"text": "You are Acme's refund agent."}]},
 "contents": [{"role": "user", "parts": [{"text": "Order A-1182, $49.99, unopened, day 12 ..."}]}],
 "references": {"gold_decision": "approve", "gold_amount": "49.99"}}
```

**Code**: `lab8_vertex_rft.py`. Class and field names were verified in `google/genai/types.py` @v2.33.0 and the method in `google/genai/tunings.py` @v2.33.0.

```python
# lab8_vertex_rft.py - Gemini reinforcement fine-tuning (Pre-GA) with a code-execution reward
import os
from google import genai
from google.genai import types

PROJECT, LOC = os.environ["GOOGLE_CLOUD_PROJECT"], "us-central1"
BUCKET = os.environ["RFT_BUCKET"]                     # e.g. gs://acme-rft-data
client = genai.Client(vertexai=True, project=PROJECT, location=LOC)   # Vertex -> api_version v1beta1

EVALUATE_SRC = r'''
import json, re
def evaluate(example, response) -> float:
    text = "".join(p.get("text", "") for p in response.get("parts", []))
    refs = example.get("references", {})
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return -1.0                                   # unparseable = clearly bad, never crash/NaN
    try:
        out = json.loads(m.group(0))
    except Exception:
        return -1.0
    if out.get("decision") != refs.get("gold_decision"):
        return -0.5
    try:
        ok = abs(float(out.get("refund_amount", -1)) - float(refs.get("gold_amount"))) <= 0.01
    except (TypeError, ValueError):
        ok = False
    return 1.0 if ok else 0.25
'''
reward = types.SingleReinforcementTuningRewardConfig(
    reward_name="refund_policy",
    code_execution_reward_scorer=types.ReinforcementTuningCodeExecutionRewardScorer(
        python_code_snippet=EVALUATE_SRC))

example = types.ReinforcementTuningExample(
    contents=[types.Content(role="user", parts=[types.Part(text=
        "Order A-1182, $49.99, unopened, returned on day 12. Policy RP-30: full refund within 30 days. "
        'Reply with JSON {"decision", "refund_amount", "reason"}.')])],
    references={"gold_decision": "approve", "gold_amount": "49.99"})
sample = types.Content(role="model", parts=[types.Part(text=
    '{"decision": "approve", "refund_amount": 49.99, "reason": "RP-30, day 12"}')])

check = client.tunings.validate_reward(parent=f"projects/{PROJECT}/locations/{LOC}",
                                       sample_response=sample, example=example,
                                       single_reward_config=reward)
print("overall_reward:", check.overall_reward, "| details:", check.reward_info_details)

if os.getenv("LAUNCH_RFT") == "1":
    job = client.tunings.tune(
        base_model="gemini-3.5-flash",
        training_dataset=types.TuningDataset(gcs_uri=f"{BUCKET}/refunds_train.jsonl"),
        config=types.CreateTuningJobConfig(
            method="REINFORCEMENT_TUNING", tuned_model_display_name="refund-agent-rft",
            reward_config=reward, validation_dataset_uri=f"{BUCKET}/refunds_val.jsonl",
            batch_size=32, samples_per_prompt=16,     # 32*16=512: divisible by 16, <= 8192
            thinking_level="MINIMAL", evaluate_interval=5, checkpoint_interval=10))
    print(job.name, job.state)
```

**Run**

```bash
python lab8_vertex_rft.py                    # validate the reward only
LAUNCH_RFT=1 python lab8_vertex_rft.py       # create the tuning job
```

**Expected output.** The validation is illustrative; the field names are verified on `ValidateRewardResponse`.

```
overall_reward: 1.0 | details: {'refund_policy': ReinforcementTuningRewardInfo(reward=1.0, error_status=None, ...)}
projects/123/locations/us-central1/tuningJobs/456789 JobState.JOB_STATE_PENDING
```

Local `evaluate()` tests **[RAN]**:
- correct decision and amount: 1.0
- right decision, wrong amount: 0.25
- wrong decision: -0.5
- unparseable: -1.0

**Walk-through**
1. `genai.Client(vertexai=True, project=..., location=...)`: for Vertex the SDK sets `api_version = 'v1beta1'` (`_api_client.py` L1046), which RFT requires.
2. `def evaluate(example, response) -> float`: `example` is the dataset line in camelCase ProtoJSON (`references` included), and `response` is a `Content` dict (`parts[].text`). The return is **clipped to [-1, 1]** (`ReinforcementTuningCodeExecutionRewardScorer` docstring). Sandbox limits [V-doc]:
   - 100 s per call, retried; dropped if it keeps timing out
   - 1 CPU, 1 GB RAM
   - libraries: cv2, matplotlib, mpmath, numpy, pandas, seaborn, sklearn, statsmodels, sympy
3. `return -1.0` on unparseable output instead of raising: the docs say a reward should "return a low value rather than crash and return NaN". "If more than 80% of your reward invocations are errored ... the tuning job is stopped automatically."
4. `client.tunings.validate_reward(parent=, sample_response=, example=, single_reward_config=)` calls `tuningJobs:validateReinforcementTuningReward` (`tunings.py` L3027-3091). Use it in CI exactly as Lab 1 uses unit tests.
5. `CreateTuningJobConfig(method="REINFORCEMENT_TUNING", reward_config=..., samples_per_prompt=16, batch_size=32, thinking_level="MINIMAL")`:
   - `samples_per_prompt` is the GRPO "group size", default 16.
   - `batchSize × samplesPerPrompt` "must be divisible by 16 and less than or equal to 8,192" for text (1,024 multimodal).
   - The SDK enum offers `MINIMAL` and `HIGH` (`types.py` L836-848). The REST enum also lists `LOW` and `MEDIUM`, but the docs say only `MINIMAL` and `HIGH` are allowed.

**Other reward types (same `SingleReinforcementTuningRewardConfig`) [V-src discovery doc + V-doc]**
- `string_match_reward_scorer`: `string_match_expression.match_operation` takes `EXACT_MATCH`, `PARTIAL_MATCH` or `REGEX_CONTAINS`. It supports `{{references.key}}` placeholders and is paired with `parse_response_config` (`REGEX_EXTRACT`, which keeps the **last** match).
- `autorater_scorer`: a Gemini judge, with placeholders `{{prompt}}`, `{{response}}`, `{{system_instruction}}`, `{{references.key}}`. One minute per rating.
- `cloud_run_reward_scorer`: your HTTP service gets `{"example", "response", "metadata": {"step", "tuningJobId"}}` and returns `{"reward": float}`. 5-minute timeout, exponential retries. Grant `roles/run.invoker` to `service-PROJECT_NUMBER@gcp-sa-vertex-tune.iam.gserviceaccount.com`.
- `composite_reward_config.weighted_reward_configs[]`: up to 16 rewards. Total = Σ(wᵢ·rᵢ)/Σwᵢ.

**Common errors**
- The v1 API returns a job with missing RFT fields. The docs say "Using the v1 API will return a response with insufficient fields populated". Fix: keep the SDK default for Vertex (v1beta1). Do not force `HttpOptions(api_version="v1")`.
- Batch-shape rejection: e.g. `batch_size=10, samples_per_prompt=10` (100 is not divisible by 16). Fix: use products such as 32×16 = 512 [exact error text UNVERIFIED].
- Dataset rejected for size. Limits [V-doc]: 5,000 training examples at most, a 1 GB file, 32,768 input tokens and 32,768 output tokens (thinking included) per example.
- Setting `thinking_budget` on Gemini 3.5 is "a user error". Use `thinking_level` (discovery doc, `ReinforcementTuningHyperParameters.thinkingLevel`).

**Best practice.** Check the reward's difficulty before you pay for a job. The docs warn that RL "can't learn well when the reward is either too hard (rewards are almost always 0) or too straightforward (rewards are almost always 1)". Sample the base model 16× on 50 prompts, compute the score distribution with your `evaluate()` locally, and adjust. Then watch these metrics [V-doc, metrics page]:
- `/learnable_prompt_ratio`, the Vertex analogue of TRL's `1 - frac_reward_zero_std`
- `/train_generation_length` and `/train_thinking_token_length`, for length drift
- `${reward_name}/train_clipping_rewards_ratio`

**Variation.** Make it a **composite** reward: `0.7 × code_execution(policy)` plus `0.3 × autorater("does the reason cite the correct policy clause?")`. Then apply the multi-reward-hacking lesson from Lab 4: make the autorater prompt return "No" whenever the decision is wrong, so the auxiliary reward is gated on the primary one.

---

## Cross-lab gotchas (collected, all verified above unless marked)

1. **float32 by default.** TRL loads string model ids in float32. Always pass `model_init_kwargs={"dtype": "bfloat16"}`.
2. **The divisibility rule.** `per_device × GPUs × steps_per_generation` must be a multiple of `num_generations`, and `num_generations ≥ 2`. The eval batch must also be divisible.
3. **`beta=0.0` is the GRPO default.** There is no reference model and no `kl` metric. Turn it on deliberately for learned or judge rewards.
4. **vLLM pin.** `vllm==0.32.0` (latest) is outside `trl[vllm]`'s `<=0.31.0` range.
5. **math-verify on Windows** falls back to multiprocessing timeouts ("huge performance penalty").
6. **Rewards must never raise.**
   - TRL: return 0.0 or `None`.
   - Vertex: return −1. Above 80% errored invocations the job auto-stops.
   - OpenAI: an exception scores 0.
7. **Partial credit is an attractor.** A constant-class router scored 0.25 and a schema-less answer scored 0.5 in our own tests **[RAN]**. Gate partial credit on validity.
8. **Hidden tests ≠ prompt examples.** Otherwise the reward is memorizable, which is leakage.
9. **RewardTrainer filters pairs longer than `max_length`** silently. Check the dataset length after init.
10. **Managed RFT reality on 2026-10-23.**
    - OpenAI RFT is winding down; o4-mini is retired today and graders are being deprecated.
    - Vertex Gemini RFT is Pre-GA and not for production data.
    - Portable assets are the **dataset + reward code + eval**, not checkpoints.

---

## arXiv insights from the last 3 months (2026-07-23 to 2026-10-23) used in the labs

All abstracts were read on arxiv.org/abs on 2026-10-23.

| arXiv | Date | Claim used | Lab |
|---|---|---|---|
| 2610.25812 "Is it RL or Data? A Controlled Comparison of GRPO and Rejection-Sampling Fine-Tuning" | 19 Oct | With the same prompts, verifier and token cap (Qwen3-4B-Base + LoRA), GRPO beats RFT at every prompt set, by 10.9 points on held-out test with curated prompts. Iterated RFT recovers about 30% of the gap. One synthetic task, 3 seeds. | 2 (why RL, not just filter-and-SFT) |
| 2610.21404 "Multi-Reward Hacking: From Aggregation-Induced Drift to Trust-Anchored Defense" | 15 Oct | Symmetric aggregation lets GRPO converge to the auxiliary reward. TAG gating gets 0.581 vs 0.220 pass@4 (Qwen3-4B, brevity) and 44% shorter answers. | 4 |
| 2607.23364 "On the Impossibility of Unbiased and Length-Invariant Policy Optimization with Outcome Rewards" | 25 Jul | No length weighting is both unbiased and length-invariant. GRPO and Dr. GRPO are opposite ends of the f_α(L)=L^(α−1) family. | 4 |
| 2610.25325 "Where Groups Split: A Probe Prior for Nonzero Within-Group Variance" | 18 Oct | Zero-variance groups waste rollouts. A short probe run predicts future informative prompts better than the base pass rate. | 2 |
| 2610.17824 "Checking the Checkers: A Synthesis of Verifier Noise and Robustness in RLVR" | 13 Oct | A survey of 58 studies. Error *structure* matters more than rate. Learnable false positives cause plateaus or collapse. Random errors lower final accuracy under KL or a fixed budget. | 1, 4 |
| 2610.19525 "Diagnosing and Correcting Reward Hacking in Verifiable Instruction Following" (CALIF) | 14 Oct | Public RLVR checkpoints show higher constraint satisfaction but lower response quality. Fix: add a likelihood bonus under the frozen reference policy. | 1, 4 (format rewards can be gamed) |
| 2610.09142 "Finding Side-Effect Loopholes in Verifiable Rewards" | 6/16 Oct | Verifiers that check only the requested change pass runs with unrequested side effects. One count assertion per template rejected all six duplicates. | 3 |
| 2610.28707 "SimHack: Predicting the onset of detectable reward hacking before RL training" | 20 Oct | Predicts the median hacking onset to 11.3% relative error. Curricula found with it train 96.6% longer without hacking. | 3 |
| 2610.30765 "Scaling Laws for Generative Reward Models" | 22 Oct | Static judge accuracy does not determine downstream policy quality. Answer-Only rewarders won 7 of 8 settings under online DPO. | 5 |
| 2610.26496 "Mitigating Reward Hacking in Preference Reward Models with Evolving Penalties" (Dynalize) | 19-20 Oct | An LLM writes penalties for RM-rewarded bad patterns during training. This sustains longer training and better external benchmarks. | 5 |
| 2610.27895 "The Shape of the DPO Hyperparameter Landscape" | 20 Oct | The optimal LR varies with model size. Hyperparameters do not transfer across datasets. Validation loss is a poor proxy. Short runs cut tuning cost. | 6 |
| 2610.24945 "Robust Direct Preference Optimization under Preference Label-Flip Attacks" | 18 Oct | DPO is manipulable by label flips. Trim-K and Soft-Trim-K Robust-DPO come with bounds. | 6 |
| 2610.29410 "ECHO: Emergent Common-Mode Hidden Offsets Drive Vocabulary Collapse in Preference Optimization" | 21 Oct | Ranking metrics improve while a shared hidden offset grows into a "vocabulary well". Collapse seen in 14 of 17 lineages under their per-token ranking loss. | 6 |
| 2610.21179 "Judging the Judges: Confidence and Disagreement in Rubrics as Rewards" (RaRE) | 15 Oct | Judge identity alone spreads scores widely. A naive judge average does not beat the best single judge. Confidence-weighted soft-Likert plus a drop-on-disagreement mask does. | 7, 8 (autorater design) |
| 2610.25725 "Anatomy of Off-Policy Policy Gradient: Importance Sampling, KL Regularization, and Baselines" | 19 Oct | Off-policy PG consistency needs trajectory-level IS or KL with a group-mean baseline (the GRPO-like route). A constant baseline shift implements pessimism. | 4 (theory slide) |

---

## Sources

**Library source (pinned tags)**
- TRL v1.16.0:
  - `trl/trainer/grpo_config.py`, `grpo_trainer.py`, `dpo_config.py`, `dpo_trainer.py`, `reward_config.py`, `reward_trainer.py`, `base_config.py`, `utils.py`
  - `trl/rewards/*.py`, `pyproject.toml`
  - https://github.com/huggingface/trl/tree/v1.16.0
- transformers v5.20.2: `src/transformers/training_args.py` (`report_to` default `"none"`, `trackio` supported, `per_device_train_batch_size=8`) and `trainer_callback.py` (`on_log`).
- PEFT v0.21.2: `src/peft/tuners/lora/config.py` (`r=8`, `lora_alpha=8`, `target_modules` "all-linear").
- Math-Verify (main): `src/math_verify/parser.py` (`parse` defaults), `utils.py` (Windows timeout note).
- openai-python v3.37.0:
  - `src/openai/types/fine_tuning/{job_create_params,reinforcement_method_param,reinforcement_hyperparameters_param}.py`
  - `types/graders/*_param.py`
  - `resources/fine_tuning/alpha/graders.py`
  - `types/fine_tuning/alpha/grader_run_response.py`
  - Also checked with `inspect.signature` on the locally installed 3.37.0.
- python-genai v2.33.0: `google/genai/types.py` (`CreateTuningJobConfig`, `SingleReinforcementTuningRewardConfig`, `ReinforcementTuningCodeExecutionRewardScorer`, `MatchOperation`, `ResponseParseType`, `ReinforcementTuningThinkingLevel`, `ValidateRewardResponse`), `tunings.py` (`tune`, `validate_reward`), `_api_client.py` (v1beta1 for Vertex).
- Vertex discovery document `https://aiplatform.googleapis.com/$discovery/rest?version=v1beta1`: the `ReinforcementTuning*` schemas.

**Official docs**
- TRL trainer docs (official quickstarts the labs adapt): https://huggingface.co/docs/trl/main/en/grpo_trainer, https://huggingface.co/docs/trl/main/en/dpo_trainer, https://huggingface.co/docs/trl/main/en/reward_trainer
- OpenAI RFT guide: https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning
- OpenAI graders guide: https://developers.openai.com/api/docs/guides/graders
- Vertex RFT pages (all under https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tuning/reinforcement-tuning):
  - overview: the base URL
  - `/quick-start`
  - `/reinforcement-tuning-job/tuning-dataset`
  - `/reinforcement-tuning-job/reward-functions`
  - `/reinforcement-tuning-job/hyperparameters`
  - `/reinforcement-tuning-job/job-status-metrics-monitoring`

**PyPI JSON:** https://pypi.org/pypi/{trl,transformers,peft,datasets,accelerate,math-verify,trackio,vllm,torch,openai,google-genai}/json

**HF Hub API:** Qwen/Qwen2.5-0.5B-Instruct, Qwen/Qwen2.5-Coder-0.5B-Instruct, Qwen/Qwen3-0.6B, trl-lib/ultrafeedback_binarized, trl-lib/DeepMath-103K, openai/gsm8k.

**arXiv:** the IDs listed in the table above, at https://arxiv.org/abs/<id>.
