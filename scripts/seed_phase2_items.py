#!/usr/bin/env python3
"""Materializes the 3 Authentic ML Debugging Arena items (inspired by Silvia Sapora + vLLM Issue #40004)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DBG = ROOT / "content" / "items" / "debugging"


def write_files(base: Path, files: dict[str, str]):
    base.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (base / name).write_text(content.lstrip("\n"), encoding="utf-8")


def main():
    # 1. Silent Broadcasting + Gradient Accumulation Reset Bug (Classic Real-World ML Bug)
    write_files(
        DBG / "silent-broadcast-and-loss-bug",
        {
            "meta.yaml": """
id: silent-broadcast-and-loss-bug
kind: debugging
unit_id: linear-algebra-gemm
title: "Bug Hunt #1: Silent (N,1)-(N,) Broadcast & Unreset Gradient Accumulation"
difficulty: medium
xp: 50
estimated_minutes: 15
tags: ["debugging", "backprop", "broadcasting", "training-loop"]
order: 3
""",
            "prompt.md": """
# Authentic ML Debugging Arena — Bug Hunt #1

The linear regression SGD training loop below runs without raising any exceptions — **yet the loss diverges or converges to the wrong weights!**

There are **two classic real-world ML bugs** hidden in `train_linear_sgd(X, y, lr=0.05, steps=300)`:
1. A silent NumPy broadcasting bug where `(N, 1) - (N,)` produces an `(N, N)` pairwise difference matrix instead of `(N,)` residuals.
2. A gradient accumulator bug where `grad_w` and `grad_b` are accumulated across steps without resetting (`+=` instead of fresh per-step gradient), causing momentum explosion.

**Fix both bugs** so `train_linear_sgd` returns `(w, b, final_mse)` with `final_mse < 1e-4` and `w` recovering the ground-truth weights cleanly.
""",
            "theory.md": """
## Why Silent Broadcasting Bugs Kill Real ML Runs

In NumPy/PyTorch, subtracting `(N, 1)` from `(N,)` silently broadcasts to `(N, N)` — `loss.mean()` still returns a scalar float so nothing crashes, while gradients are completely corrupted! Always assert explicit shapes (`assert pred.shape == y.shape`).
""",
            "starter.py": """
import numpy as np

def train_linear_sgd(X: np.ndarray, y: np.ndarray, lr: float = 0.05, steps: int = 300):
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)  # shape (N,)
    N, D = X.shape
    w = np.zeros((D, 1), dtype=np.float64)
    b = 0.0
    grad_w = np.zeros_like(w)
    grad_b = 0.0

    for _ in range(steps):
        pred = X @ w + b            # BUG 1: shape (N, 1) while y is (N,) -> err is (N, N)!
        err = pred - y
        grad_w += (2.0 / N) * (X.T @ err.mean(axis=1, keepdims=True))  # BUG 2: never zeroed!
        grad_b += (2.0 / N) * float(np.sum(err)) / N
        w -= lr * grad_w
        b -= lr * grad_b

    final_pred = (X @ w).reshape(-1) + b
    final_mse = float(np.mean((final_pred - y) ** 2))
    return w.reshape(-1), float(b), final_mse
""",
            "reference.py": """
import numpy as np

def train_linear_sgd(X: np.ndarray, y: np.ndarray, lr: float = 0.05, steps: int = 300):
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64).reshape(-1)
    N, D = X.shape
    w = np.zeros(D, dtype=np.float64)
    b = 0.0

    for _ in range(steps):
        pred = X @ w + b
        err = pred - y  # shape (N,)
        grad_w = (2.0 / N) * (X.T @ err)
        grad_b = (2.0 / N) * float(np.sum(err))
        w -= lr * grad_w
        b -= lr * grad_b

    final_pred = X @ w + b
    final_mse = float(np.mean((final_pred - y) ** 2))
    return w, float(b), final_mse
""",
            "tests.py": """
import numpy as np

def test_recovers_exact_weights_and_low_mse(user_mod):
    rng = np.random.default_rng(12)
    X = rng.standard_normal((120, 4))
    true_w = np.array([2.5, -1.3, 0.7, 4.0])
    true_b = -0.8
    y = X @ true_w + true_b
    w, b, mse = user_mod.train_linear_sgd(X, y, lr=0.05, steps=350)
    assert w.shape == (4,)
    assert np.isfinite(mse) and mse < 1e-4
    np.testing.assert_allclose(w, true_w, atol=1e-2)
    np.testing.assert_allclose(b, true_b, atol=1e-2)
""",
        },
    )

    # 2. Inverted Causal Mask Sign + fp16 Softmax Overflow -> NaN
    write_files(
        DBG / "causal-mask-sign-and-fp16-nan",
        {
            "meta.yaml": """
id: causal-mask-sign-and-fp16-nan
kind: debugging
unit_id: transformer-attention
title: "Bug Hunt #2: Inverted Causal Mask + FP16 Softmax NaN Overflow"
difficulty: hard
xp: 60
estimated_minutes: 20
tags: ["debugging", "attention", "fp16", "numerical-stability", "causal-mask"]
order: 3
""",
            "prompt.md": """
# Authentic ML Debugging Arena — Bug Hunt #2

A mixed-precision (`float16`) attention kernel returns **`NaN`** on large logits AND leaks future tokens!

Inspect `stable_causal_attention_fp16(Q, K, V)` (`Q, K, V` are `np.float16` of shape `(T, D)`):
1. **Bug 1 (Mask Direction):** `np.tril(..., k=-1)` masks the *past* instead of the *future* (`np.triu(..., k=1)`).
2. **Bug 2 (FP16 Overflow):** Computing `np.exp(scores)` directly in `float16` overflows to `inf` whenever a logit exceeds ~11.0 (`exp(12) > 65504`), turning `inf / inf` into `NaN`!
3. **Bug 3 (Missing Scale):** Forgets to divide by $\\sqrt{D}$.

**Fix all three bugs** by upcasting softmax accumulation to `float32`, subtracting row max before `exp`, applying the upper-triangular causal mask (`-1e9` in `float32`), and casting the final output cleanly back to `float16`.
""",
            "theory.md": """
## Mixed-Precision Softmax Rule

`float16` max finite value is `65504`, so `exp(x)` overflows for `x > 11.09`. Production kernels (PyTorch SDPA, FlashAttention, Triton) ALWAYS accumulate softmax in `float32` even when `Q, K, V` are `fp16` or `bf16`.
""",
            "starter.py": """
import numpy as np

def stable_causal_attention_fp16(Q: np.ndarray, K: np.ndarray, V: np.ndarray) -> np.ndarray:
    T, D = Q.shape
    scores = Q @ K.T                                  # BUG: no 1/sqrt(D), stays fp16
    mask = np.tril(np.ones((T, T), dtype=bool), k=-1) # BUG: masks past instead of future!
    scores = np.where(mask, np.float16(-1e4), scores)
    exp_s = np.exp(scores)                            # BUG: overflows fp16 -> inf -> NaN!
    weights = exp_s / np.sum(exp_s, axis=-1, keepdims=True)
    return (weights @ V).astype(np.float16)
""",
            "reference.py": """
import numpy as np

def stable_causal_attention_fp16(Q: np.ndarray, K: np.ndarray, V: np.ndarray) -> np.ndarray:
    Q32 = np.asarray(Q, dtype=np.float32)
    K32 = np.asarray(K, dtype=np.float32)
    V32 = np.asarray(V, dtype=np.float32)
    T, D = Q32.shape
    scores = (Q32 @ K32.T) / np.sqrt(float(D))
    mask = np.triu(np.ones((T, T), dtype=bool), k=1)
    scores = np.where(mask, -1e9, scores)
    scores = scores - np.max(scores, axis=-1, keepdims=True)
    exp_s = np.exp(scores)
    weights = exp_s / np.sum(exp_s, axis=-1, keepdims=True)
    return (weights @ V32).astype(np.float16)
""",
            "tests.py": """
import numpy as np

def test_no_nan_on_large_fp16_logits(user_mod):
    rng = np.random.default_rng(55)
    Q = (rng.standard_normal((8, 16)) * 6.0).astype(np.float16)
    K = (rng.standard_normal((8, 16)) * 6.0).astype(np.float16)
    V = rng.standard_normal((8, 16)).astype(np.float16)
    out = user_mod.stable_causal_attention_fp16(Q, K, V)
    assert out.dtype == np.float16
    assert np.all(np.isfinite(out)), "Output contains NaN or Inf!"

def test_strict_causality(user_mod):
    rng = np.random.default_rng(88)
    Q = rng.standard_normal((6, 8)).astype(np.float16)
    K = rng.standard_normal((6, 8)).astype(np.float16)
    V = rng.standard_normal((6, 8)).astype(np.float16)
    out1 = user_mod.stable_causal_attention_fp16(Q, K, V)
    K2 = K.copy(); V2 = V.copy()
    K2[-1] += np.float16(20.0); V2[-1] += np.float16(20.0)
    out2 = user_mod.stable_causal_attention_fp16(Q, K2, V2)
    np.testing.assert_allclose(out1[:-1].astype(np.float32), out2[:-1].astype(np.float32), atol=1e-3)
""",
        },
    )

    # 3. vLLM Issue #40004 Prefill-Starves-Decode Scheduler Bug
    write_files(
        DBG / "vllm-prefill-starvation-bug",
        {
            "meta.yaml": """
id: vllm-prefill-starvation-bug
kind: debugging
unit_id: paged-serving-speculative
title: "Bug Hunt #3: vLLM Issue #40004 — Incoming Prefills Preempting Active Decodes"
difficulty: hard
xp: 65
estimated_minutes: 20
tags: ["debugging", "vllm", "continuous-batching", "scheduler", "inference"]
order: 5
""",
            "prompt.md": """
# Authentic ML Debugging Arena — Bug Hunt #3 (Inspired by vLLM Issue #40004 / PR #45558)

In `schedule_iteration(running, waiting, token_budget)`:
- `running`: list of dicts `{"id": str, "remaining_decode": int}` (each active decode needs **1 token** of compute budget this step).
- `waiting`: list of dicts `{"id": str, "prompt_tokens": int}` (each waiting prefill needs `prompt_tokens` of compute budget, or can be **chunked** down to remaining budget if > 0!).
- `token_budget`: total compute tokens allowed in this GPU iteration.

### The Production Bug
The buggy scheduler admits `waiting` prefills **BEFORE** reserving 1 token for every active `running` decode request! When a large prompt arrives, it eats the entire `token_budget`, starving active decodes and spiking **TPOT (Time Per Output Token)**!

### Your Fix
Enforce the **vLLM V1 Decode-First Phase Separation Invariant**:
1. Reserve 1 token for every `running` request first (up to `token_budget`).
2. Spend only the **leftover budget** on `waiting` prefills (chunking a prompt if leftover budget `< prompt_tokens`, reducing its remaining `prompt_tokens` instead of dropping it, and moving it to `admitted_prefills` with `chunk_tokens`).
3. Return `{"scheduled_decodes": [...ids], "scheduled_prefills": [(id, chunk_tokens), ...], "budget_used": int}`.
""",
            "theory.md": """
## Decode-First Phase Separation + Chunked Prefill

Scheduling running decodes first guarantees bounded TPOT latency even during bursty long-prompt arrivals, while chunked prefill packs leftover GPU compute capacity without head-of-line blocking.
""",
            "starter.py": """
def schedule_iteration(running: list[dict], waiting: list[dict], token_budget: int) -> dict:
    # BUG: Schedules waiting prefills first -> starves active decodes!
    used = 0
    prefills = []
    decodes = []
    for req in waiting:
        need = req["prompt_tokens"]
        if used + need <= token_budget:
            prefills.append((req["id"], need))
            used += need
    for req in running:
        if used + 1 <= token_budget:
            decodes.append(req["id"])
            used += 1
    return {"scheduled_decodes": decodes, "scheduled_prefills": prefills, "budget_used": used}
""",
            "reference.py": """
def schedule_iteration(running: list[dict], waiting: list[dict], token_budget: int) -> dict:
    used = 0
    decodes = []
    prefills = []
    # 1. Decode-first invariant: guarantee active running requests never starve
    for req in running:
        if used + 1 <= token_budget:
            decodes.append(req["id"])
            used += 1
    # 2. Pack remaining budget with chunked prefills
    for req in waiting:
        rem = token_budget - used
        if rem <= 0:
            break
        chunk = min(req["prompt_tokens"], rem)
        if chunk > 0:
            prefills.append((req["id"], chunk))
            used += chunk
    return {"scheduled_decodes": decodes, "scheduled_prefills": prefills, "budget_used": used}
""",
            "tests.py": """
def test_decodes_never_starved_by_large_prefill(user_mod):
    running = [{"id": "d1", "remaining_decode": 10}, {"id": "d2", "remaining_decode": 5}, {"id": "d3", "remaining_decode": 8}]
    waiting = [{"id": "p_huge", "prompt_tokens": 512}]
    out = user_mod.schedule_iteration(running, waiting, token_budget=64)
    # All 3 running decodes MUST be scheduled
    assert out["scheduled_decodes"] == ["d1", "d2", "d3"]
    # Remaining 61 tokens go to chunked prefill of p_huge!
    assert out["scheduled_prefills"] == [("p_huge", 61)]
    assert out["budget_used"] == 64

def test_multiple_prefills_fit_after_decodes(user_mod):
    running = [{"id": "d1", "remaining_decode": 4}]
    waiting = [{"id": "p1", "prompt_tokens": 10}, {"id": "p2", "prompt_tokens": 20}]
    out = user_mod.schedule_iteration(running, waiting, token_budget=25)
    assert out["scheduled_decodes"] == ["d1"]
    assert out["scheduled_prefills"] == [("p1", 10), ("p2", 14)]
    assert out["budget_used"] == 25
""",
        },
    )

    print("Seeded 3 Authentic ML Debugging Arena items in content/items/debugging/.")


if __name__ == "__main__":
    main()
