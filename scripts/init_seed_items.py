#!/usr/bin/env python3
"""Materializes the 18 deep starter items into content/items/ and starter templates into private/."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
ITEMS = ROOT / "content" / "items"
PRIVATE = ROOT / "private"


def write_files(base: Path, files: dict[str, str]):
    base.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        p = base / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content.lstrip("\n"), encoding="utf-8")


def seed_items():
    # ------------------------------------------------------------------
    # TRACK 1: MATH & FUNDAMENTALS (4 items: puzzle, math, problem, lab)
    # ------------------------------------------------------------------
    write_files(
        ITEMS / "puzzles" / "outlier-proof-estimator",
        {
            "meta.yaml": """
id: outlier-proof-estimator
kind: puzzle
unit_id: math-stats-foundations
title: "The Billionaire Walks Into a Cafe (Outlier-Proof Estimator)"
difficulty: easy
xp: 25
estimated_minutes: 10
tags: ["statistics", "estimators", "robustness", "intuition"]
order: 1
""",
            "prompt.md": """
# Invent a Typical-Value Estimator

You are given a list of numbers `xs` representing incomes of people in a cafe.
Write **any** Python function `typical_value(xs: list[float]) -> float` that returns one representative number for the group.

No formula is given. Your function will be attacked by adversarial counterexamples using your own outputs:
1. **Constant consensus**: If everyone earns `$c`, you must return `c`.
2. **Shift equivariance**: If everyone gets a `+$10` raise, your estimate must rise by `$10`.
3. **Scale equivariance**: If incomes double, your estimate must double.
4. **Billionaire attack (Breakdown Point)**: If 1 out of 9 people becomes a billionaire (`1e9`), your estimate must NOT jump by more than 20%.
""",
            "starter.py": """
def typical_value(xs: list[float]) -> float:
    # Start with any guess — see what breaks!
    return sum(xs) / len(xs)
""",
            "reference.py": """
def typical_value(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return 0.5 * (s[mid - 1] + s[mid])
""",
            "tests.py": """
import math

def run_counterexamples(fn):
    failures = []
    # 1. Constant consensus
    v = fn([42.0, 42.0, 42.0, 42.0, 42.0])
    if not math.isclose(v, 42.0, rel_tol=1e-6, abs_tol=1e-6):
        failures.append({
            "property": "Constant Consensus",
            "input": "[42, 42, 42, 42, 42]",
            "your_output": repr(v),
            "why_broken": f"Everyone has 42, yet your estimator returned {v}."
        })
    # 2. Shift equivariance
    base = [10.0, 20.0, 30.0, 40.0, 50.0]
    shifted = [x + 15.0 for x in base]
    v1, v2 = fn(base), fn(shifted)
    if not math.isclose(v2 - v1, 15.0, rel_tol=1e-5, abs_tol=1e-5):
        failures.append({
            "property": "Shift Equivariance",
            "input": "base=[10..50] vs base+15",
            "your_output": f"{v1} -> {v2} (delta={v2-v1:.3f})",
            "why_broken": "Adding +15 to every person should shift the typical value by exactly +15."
        })
    # 3. Scale equivariance
    doubled = [x * 2.0 for x in base]
    v3 = fn(doubled)
    if not math.isclose(v3, 2.0 * v1, rel_tol=1e-5, abs_tol=1e-5):
        failures.append({
            "property": "Scale Equivariance",
            "input": "2 * [10, 20, 30, 40, 50]",
            "your_output": f"{v1} -> {v3}",
            "why_broken": "Doubling every number should double your estimate."
        })
    # 4. Billionaire attack
    cafe = [50.0, 52.0, 55.0, 58.0, 60.0, 62.0, 65.0, 68.0, 70.0]
    with_billionaire = [50.0, 52.0, 55.0, 58.0, 60.0, 62.0, 65.0, 68.0, 1_000_000_000.0]
    c1, c2 = fn(cafe), fn(with_billionaire)
    if abs(c2 - c1) > 0.2 * abs(c1):
        failures.append({
            "property": "Billionaire Attack (Outlier Robustness)",
            "input": "[50, 52, 55, 58, 60, 62, 65, 68, 1e9]",
            "your_output": f"normal={c1:.2f} -> with_billionaire={c2:.2f}",
            "why_broken": f"One billionaire warped your 'typical person' estimate from {c1:.2f} to {c2:.2f}! Try ranking/order statistics."
        })
    return failures
""",
        },
    )

    write_files(
        ITEMS / "math" / "softmax-and-attention-scaling",
        {
            "meta.yaml": """
id: softmax-and-attention-scaling
kind: math
unit_id: math-stats-foundations
title: "Softmax Shift-Invariance & 1/sqrt(d_k) Variance Scaling"
difficulty: medium
xp: 35
estimated_minutes: 15
tags: ["calculus", "softmax", "attention", "variance", "sympy"]
order: 2
""",
            "worked_example.md": """
# Worked Example: Why Scaled Dot-Product Attention Divides by $\\sqrt{d_k}$

Suppose query $q \\in \\mathbb{R}^{d_k}$ and key $k \\in \\mathbb{R}^{d_k}$ have i.i.d. entries with mean $0$ and variance $1$:
$$\\mathbb{E}[q_i] = 0, \\quad \\mathrm{Var}(q_i) = 1, \\quad \\mathbb{E}[k_i] = 0, \\quad \\mathrm{Var}(k_i) = 1$$

Because $q_i$ and $k_i$ are independent:
$$\\mathrm{Var}(q_i k_i) = \\mathbb{E}[q_i^2]\\mathbb{E}[k_i^2] - (\\mathbb{E}[q_i]\\mathbb{E}[k_i])^2 = 1 \\cdot 1 - 0 = 1$$

Summing $d_k$ independent terms gives:
$$\\mathrm{Var}(q^\\top k) = \\sum_{i=1}^{d_k} \\mathrm{Var}(q_i k_i) = d_k$$

Scaling by $\\frac{1}{\\sqrt{d_k}}$ restores unit variance:
$$\\mathrm{Var}\\left(\\frac{q^\\top k}{\\sqrt{d_k}}\\right) = \\frac{1}{d_k} \\cdot d_k = 1$$

Without this scaling, large $d_k$ pushes logits into the saturated tails of softmax where gradients vanish.
""",
            "drills.yaml": """
drills:
  - id: drill-1
    prompt: "If q_i, k_i ~ N(0, sigma^2) independently for i=1..d, what is Var(q^T k) in terms of d and sigma? (Use variables `d` and `sigma`, e.g. `d*sigma**4`)"
    mode: symbolic
    symbols: ["d", "sigma"]
    expected: "d * sigma**4"
    hint: "Var(q_i * k_i) = E[q_i^2]E[k_i^2] = sigma^2 * sigma^2 = sigma^4, summed d times."
  - id: drill-2
    prompt: "What is the diagonal entry d(softmax(z)_i)/dz_i in terms of p = softmax(z)_i? (Use variable `p`)"
    mode: symbolic
    symbols: ["p"]
    expected: "p * (1 - p)"
    hint: "Apply the quotient rule to exp(z_i) / sum_j exp(z_j)."
  - id: drill-3
    prompt: "For d_k = 64 with unit-variance q and k, by what factor must you divide q^T k so the logit standard deviation equals 1? (Enter a number)"
    mode: numeric
    expected: 8.0
    tol: 1e-6
    hint: "sqrt(64) = 8."
""",
        },
    )

    write_files(
        ITEMS / "problems" / "matrix-vector-and-tiled-gemm",
        {
            "meta.yaml": """
id: matrix-vector-and-tiled-gemm
kind: problem
unit_id: linear-algebra-gemm
title: "Blocked (Tiled) Matrix Multiplication (GEMM)"
difficulty: medium
xp: 40
estimated_minutes: 20
tags: ["linear-algebra", "gemm", "tiling", "cache-locality", "numpy"]
banned_apis: ["matmul", "dot", "einsum", "tensordot"]
ban_matmul_op: true
order: 1
""",
            "prompt.md": """
# Blocked (Tiled) Matrix Multiplication (GEMM)

Implement `tiled_gemm(A: np.ndarray, B: np.ndarray, tile_size: int = 16) -> np.ndarray` that computes $C = A B$ for 2D float matrices $A \\in \\mathbb{R}^{M \\times K}$ and $B \\in \\mathbb{R}^{K \\times N}$ using **explicit 3-level tiling** over `(i0, j0, k0)` with block size `tile_size`.

### Constraints
- Do **not** call `np.matmul`, `np.dot`, `np.einsum`, `np.tensordot`, or use the `@` operator (checked statically by AST guard!).
- Handle arbitrary matrix dimensions $M, K, N$ that are **not** multiples of `tile_size`.
- Raise `ValueError` if `A.shape[1] != B.shape[0]`.
""",
            "theory.md": """
## Why Tiling Matters for ML Infra & GPU Kernels

Naive matrix multiply streams $B$ out of L1/SRAM repeatedly for every row of $A$, giving poor **arithmetic intensity**.
Blocking into $T \\times T$ tiles keeps three small sub-blocks ($A_{ik}, B_{kj}, C_{ij}$) hot in fast cache/SRAM, increasing data reuse by a factor of $\\mathcal{O}(T)$ — the exact same principle behind FlashAttention and CUTLASS shared-memory GEMM.
""",
            "starter.py": """
import numpy as np

def tiled_gemm(A: np.ndarray, B: np.ndarray, tile_size: int = 16) -> np.ndarray:
    # Implement tiled matrix multiplication without using @, np.matmul, np.dot, or np.einsum
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def tiled_gemm(A: np.ndarray, B: np.ndarray, tile_size: int = 16) -> np.ndarray:
    A = np.asarray(A, dtype=np.float64)
    B = np.asarray(B, dtype=np.float64)
    if A.ndim != 2 or B.ndim != 2 or A.shape[1] != B.shape[0]:
        raise ValueError("Incompatible shapes for matrix multiplication")
    M, K = A.shape
    _, N = B.shape
    C = np.zeros((M, N), dtype=np.float64)
    for i0 in range(0, M, tile_size):
        i1 = min(i0 + tile_size, M)
        for k0 in range(0, K, tile_size):
            k1 = min(k0 + tile_size, K)
            for j0 in range(0, N, tile_size):
                j1 = min(j0 + tile_size, N)
                # Accumulate tile product explicitly
                for i in range(i0, i1):
                    for k in range(k0, k1):
                        aik = A[i, k]
                        C[i, j0:j1] += aik * B[k, j0:j1]
    return C
""",
            "tests.py": """
import numpy as np
import pytest

def test_square_exact_tile(user_mod):
    rng = np.random.default_rng(0)
    A = rng.standard_normal((16, 16))
    B = rng.standard_normal((16, 16))
    out = user_mod.tiled_gemm(A, B, tile_size=8)
    np.testing.assert_allclose(out, A @ B, rtol=1e-5, atol=1e-6)

def test_non_multiple_rectangular(user_mod):
    rng = np.random.default_rng(42)
    A = rng.standard_normal((19, 13))
    B = rng.standard_normal((13, 23))
    out = user_mod.tiled_gemm(A, B, tile_size=4)
    np.testing.assert_allclose(out, A @ B, rtol=1e-5, atol=1e-6)

def test_shape_mismatch_raises(user_mod):
    A = np.ones((4, 5))
    B = np.ones((6, 3))
    with pytest.raises(ValueError):
        user_mod.tiled_gemm(A, B, tile_size=2)
""",
        },
    )

    write_files(
        ITEMS / "labs" / "regularized-regression-lab",
        {
            "meta.yaml": """
id: regularized-regression-lab
kind: lab
unit_id: math-stats-foundations
title: "Lab: Collinear Ridge Regression & Cross-Validated Lambda Selection"
difficulty: medium
xp: 60
estimated_minutes: 25
tags: ["classical-ml", "regularization", "ridge", "linear-algebra", "lab"]
metric_name: "val_rmse"
metric_goal: "<= 0.85"
order: 3
""",
            "prompt.md": """
# Real-Dataset Lab: Surviving Extreme Multicollinearity

You are given a strongly collinear regression dataset `(X_train, y_train, X_val)` (40 correlated features, 200 training samples, heavy feature collinearity where unregularized OLS explodes with validation RMSE > 4.0).

Implement `fit_predict(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray) -> np.ndarray`:
- Standardize features cleanly (using **training statistics only** — no data leakage!).
- Select an L2 penalty $\\lambda$ (via closed-form Ridge + K-fold CV or GCV) and solve the regularized normal equations / SVD cleanly.
- **Target Metric:** Validation `RMSE <= 0.85` on the hidden held-out test set.
""",
            "starter.py": """
import numpy as np

def fit_predict(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray) -> np.ndarray:
    # Naive OLS blows up under collinearity — replace with standardized Ridge + CV
    w, *_ = np.linalg.lstsq(X_train, y_train, rcond=None)
    return X_val @ w
""",
            "reference.py": """
import numpy as np

def fit_predict(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray) -> np.ndarray:
    mu = X_train.mean(axis=0, keepdims=True)
    sd = X_train.std(axis=0, keepdims=True) + 1e-8
    Xtr = (X_train - mu) / sd
    Xva = (X_val - mu) / sd
    y_mean = y_train.mean()
    ytr = y_train - y_mean

    n, d = Xtr.shape
    folds = 5
    idx = np.arange(n)
    best_lam, best_mse = 1.0, float("inf")
    for lam in np.logspace(-3, 3, 25):
        mses = []
        for f in range(folds):
            va_mask = (idx % folds) == f
            tr_mask = ~va_mask
            Xf, yf = Xtr[tr_mask], ytr[tr_mask]
            w = np.linalg.solve(Xf.T @ Xf + lam * np.eye(d), Xf.T @ yf)
            pred = Xtr[va_mask] @ w
            mses.append(np.mean((pred - ytr[va_mask]) ** 2))
        m = float(np.mean(mses))
        if m < best_mse:
            best_mse, best_lam = m, float(lam)

    w_final = np.linalg.solve(Xtr.T @ Xtr + best_lam * np.eye(d), Xtr.T @ ytr)
    return Xva @ w_final + y_mean
""",
            "tests.py": """
import numpy as np

def evaluate_lab(user_mod):
    rng = np.random.default_rng(123)
    n_train, n_val, d = 120, 120, 40
    # Create low-rank strongly collinear design matrix
    Z_tr = rng.standard_normal((n_train, 5))
    Z_va = rng.standard_normal((n_val, 5))
    mix = rng.standard_normal((5, d))
    X_tr = Z_tr @ mix + 1e-3 * rng.standard_normal((n_train, d))
    X_va = Z_va @ mix + 1e-3 * rng.standard_normal((n_val, d))
    true_w = rng.standard_normal(5) * 1.5
    y_tr = Z_tr @ true_w + 0.6 * rng.standard_normal(n_train) + 3.0
    y_va = Z_va @ true_w + 0.6 * rng.standard_normal(n_val) + 3.0

    preds = np.asarray(user_mod.fit_predict(X_tr, y_tr, X_va), dtype=np.float64)
    if preds.shape != y_va.shape:
        return {"passed": False, "metric": 999.0, "details": f"Expected shape {y_va.shape}, got {preds.shape}"}
    rmse = float(np.sqrt(np.mean((preds - y_va) ** 2)))
    passed = rmse <= 0.85
    return {
        "passed": passed,
        "metric": round(rmse, 4),
        "threshold": 0.85,
        "details": f"Validation RMSE = {rmse:.4f} (target <= 0.85)"
    }
""",
        },
    )

    # ------------------------------------------------------------------
    # TRACK 2: LLMs & ADVANCED NETS (4 items)
    # ------------------------------------------------------------------
    write_files(
        ITEMS / "problems" / "causal-multihead-attention",
        {
            "meta.yaml": """
id: causal-multihead-attention
kind: problem
unit_id: transformer-attention
title: "Causal Multi-Head Self-Attention from Scratch"
difficulty: medium
xp: 50
estimated_minutes: 25
tags: ["transformers", "attention", "causal-mask", "llm"]
order: 1
""",
            "prompt.md": """
# Causal Multi-Head Self-Attention from Scratch

Implement `causal_mha(X, W_q, W_k, W_v, W_o, num_heads)` in pure NumPy:
- `X`: shape `(B, T, D)`
- `W_q, W_k, W_v, W_o`: shape `(D, D)`
- Split `D` into `num_heads` heads of dimension `d_h = D // num_heads`.
- Compute scaled dot-product attention with a **strict causal mask** (position `t` may only attend to `<= t`), using numerically stable softmax.
- Recombine heads and project with `W_o`, returning shape `(B, T, D)`.
""",
            "theory.md": """
## Causal Multi-Head Attention

For each head $h$, with $Q_h, K_h, V_h \\in \\mathbb{R}^{B \\times T \\times d_h}$:
$$\\mathrm{Attn}(Q_h, K_h, V_h) = \\mathrm{softmax}\\!\\left(\\frac{Q_h K_h^\\top}{\\sqrt{d_h}} + M\\right) V_h$$
where $M_{ij} = 0$ if $j \\le i$ else $-\\infty$. Subtract `max` before `exp` for numerical stability.
""",
            "starter.py": """
import numpy as np

def causal_mha(
    X: np.ndarray,
    W_q: np.ndarray,
    W_k: np.ndarray,
    W_v: np.ndarray,
    W_o: np.ndarray,
    num_heads: int,
) -> np.ndarray:
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def causal_mha(
    X: np.ndarray,
    W_q: np.ndarray,
    W_k: np.ndarray,
    W_v: np.ndarray,
    W_o: np.ndarray,
    num_heads: int,
) -> np.ndarray:
    B, T, D = X.shape
    d_h = D // num_heads
    Q = (X @ W_q).reshape(B, T, num_heads, d_h).transpose(0, 2, 1, 3)
    K = (X @ W_k).reshape(B, T, num_heads, d_h).transpose(0, 2, 1, 3)
    V = (X @ W_v).reshape(B, T, num_heads, d_h).transpose(0, 2, 1, 3)

    scores = (Q @ K.transpose(0, 1, 3, 2)) / np.sqrt(d_h)
    mask = np.triu(np.ones((T, T), dtype=bool), k=1)
    scores = np.where(mask, -1e9, scores)
    scores = scores - np.max(scores, axis=-1, keepdims=True)
    weights = np.exp(scores)
    weights = weights / np.sum(weights, axis=-1, keepdims=True)

    ctx = (weights @ V).transpose(0, 2, 1, 3).reshape(B, T, D)
    return ctx @ W_o
""",
            "tests.py": """
import numpy as np

def test_causality_no_future_leak(user_mod):
    rng = np.random.default_rng(7)
    B, T, D, H = 2, 6, 8, 2
    X = rng.standard_normal((B, T, D))
    Wq, Wk, Wv, Wo = [rng.standard_normal((D, D)) * 0.2 for _ in range(4)]
    out1 = user_mod.causal_mha(X, Wq, Wk, Wv, Wo, H)
    X2 = X.copy()
    X2[:, -1, :] += 50.0  # Perturb last token heavily
    out2 = user_mod.causal_mha(X2, Wq, Wk, Wv, Wo, H)
    assert out1.shape == (B, T, D)
    np.testing.assert_allclose(out1[:, :-1, :], out2[:, :-1, :], atol=1e-6)

def test_matches_reference_values(user_mod):
    rng = np.random.default_rng(11)
    B, T, D, H = 1, 4, 4, 2
    X = rng.standard_normal((B, T, D))
    Wq = np.eye(D); Wk = np.eye(D); Wv = np.eye(D); Wo = np.eye(D)
    out = user_mod.causal_mha(X, Wq, Wk, Wv, Wo, H)
    # First token can only attend to itself -> output at t=0 equals X[:,0,:]
    np.testing.assert_allclose(out[:, 0, :], X[:, 0, :], atol=1e-6)
""",
        },
    )

    write_files(
        ITEMS / "problems" / "rope-positional-encoding",
        {
            "meta.yaml": """
id: rope-positional-encoding
kind: problem
unit_id: transformer-attention
title: "Rotary Position Embeddings (RoPE)"
difficulty: medium
xp: 45
estimated_minutes: 20
tags: ["rope", "positional-encoding", "transformers", "llm"]
order: 2
""",
            "prompt.md": """
# Rotary Position Embeddings (RoPE)

Implement `apply_rope(x: np.ndarray, base: float = 10000.0) -> np.ndarray` for input `x` of shape `(B, T, D)` (where `D` is even).
For each adjacent pair `(2i, 2i+1)` and sequence position `m in [0, T-1]`:
- Frequency: $\\theta_i = \\text{base}^{-2i / D}$
- Angle: $\\phi_{m,i} = m \\cdot \\theta_i$
- Apply 2D rotation:
  - $x'_{2i} = x_{2i}\\cos\\phi - x_{2i+1}\\sin\\phi$
  - $x'_{2i+1} = x_{2i}\\sin\\phi + x_{2i+1}\\cos\\phi$
""",
            "theory.md": """
## Relative Position Property of RoPE

Because 2D rotation matrices satisfy $R(m\\theta)^\\top R(n\\theta) = R((n-m)\\theta)$, the dot product between rotated queries and keys depends **only on relative distance $(n-m)$** while preserving vector norms $\\|R(m\\theta)x\\|_2 = \\|x\\|_2$.
""",
            "starter.py": """
import numpy as np

def apply_rope(x: np.ndarray, base: float = 10000.0) -> np.ndarray:
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def apply_rope(x: np.ndarray, base: float = 10000.0) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    B, T, D = x.shape
    half = D // 2
    freqs = base ** (-2.0 * np.arange(half) / D)
    pos = np.arange(T)[:, None]
    angles = pos * freqs[None, :]  # (T, half)
    cos_a = np.cos(angles)[None, :, :]
    sin_a = np.sin(angles)[None, :, :]
    x_even = x[..., 0::2]
    x_odd = x[..., 1::2]
    out = np.empty_like(x)
    out[..., 0::2] = x_even * cos_a - x_odd * sin_a
    out[..., 1::2] = x_even * sin_a + x_odd * cos_a
    return out
""",
            "tests.py": """
import numpy as np

def test_norm_preservation(user_mod):
    rng = np.random.default_rng(3)
    x = rng.standard_normal((2, 10, 16))
    y = user_mod.apply_rope(x)
    np.testing.assert_allclose(np.linalg.norm(y, axis=-1), np.linalg.norm(x, axis=-1), atol=1e-6)

def test_relative_dot_product_invariance(user_mod):
    rng = np.random.default_rng(5)
    q = rng.standard_normal((1, 1, 8))
    k = rng.standard_normal((1, 1, 8))
    Q = np.repeat(q, 10, axis=1)
    K = np.repeat(k, 10, axis=1)
    Qr = user_mod.apply_rope(Q)
    Kr = user_mod.apply_rope(K)
    # Dot(m=2, n=5) must equal Dot(m=4, n=7) since relative offset is 3
    d1 = float(np.dot(Qr[0, 2], Kr[0, 5]))
    d2 = float(np.dot(Qr[0, 4], Kr[0, 7]))
    np.testing.assert_allclose(d1, d2, atol=1e-6)
""",
        },
    )

    write_files(
        ITEMS / "problems" / "gcn-message-passing",
        {
            "meta.yaml": """
id: gcn-message-passing
kind: problem
unit_id: gnn-continual
title: "Graph Convolutional Network (GCN) Layer"
difficulty: easy
xp: 35
estimated_minutes: 15
tags: ["gnn", "graph-neural-networks", "message-passing"]
order: 1
""",
            "prompt.md": """
# Kipf & Welling Graph Convolutional Layer

Implement `gcn_layer(A: np.ndarray, X: np.ndarray, W: np.ndarray) -> np.ndarray`:
1. Add self-loops: $\\tilde{A} = A + I_N$.
2. Compute symmetric degree normalization: $\\hat{A} = \\tilde{D}^{-1/2} \\tilde{A} \\tilde{D}^{-1/2}$ where $\\tilde{D}_{ii} = \\sum_j \\tilde{A}_{ij}$.
3. Propagate and apply ReLU: $H = \\mathrm{ReLU}(\\hat{A} X W)$.
""",
            "theory.md": """
## Symmetric Normalization in GCN

Using $\\tilde{D}^{-1/2} \\tilde{A} \\tilde{D}^{-1/2}$ prevents high-degree hub nodes from exploding feature scales during multi-hop message passing.
""",
            "starter.py": """
import numpy as np

def gcn_layer(A: np.ndarray, X: np.ndarray, W: np.ndarray) -> np.ndarray:
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def gcn_layer(A: np.ndarray, X: np.ndarray, W: np.ndarray) -> np.ndarray:
    A = np.asarray(A, dtype=np.float64)
    X = np.asarray(X, dtype=np.float64)
    W = np.asarray(W, dtype=np.float64)
    N = A.shape[0]
    A_tilde = A + np.eye(N)
    deg = A_tilde.sum(axis=1)
    d_inv_sqrt = np.where(deg > 0, deg ** -0.5, 0.0)
    A_hat = (d_inv_sqrt[:, None] * A_tilde) * d_inv_sqrt[None, :]
    return np.maximum(0.0, A_hat @ X @ W)
""",
            "tests.py": """
import numpy as np

def test_gcn_simple_chain(user_mod):
    A = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)
    X = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    W = np.eye(2)
    out = user_mod.gcn_layer(A, X, W)
    assert out.shape == (3, 2)
    assert np.all(out >= 0.0)
    # Node 0 has deg_tilde=2, node 1 has deg_tilde=3 -> entry (0,0) = 1/2
    np.testing.assert_allclose(out[0, 0], 0.5, atol=1e-6)
    np.testing.assert_allclose(out[0, 1], 1.0 / np.sqrt(6.0), atol=1e-6)
""",
        },
    )

    write_files(
        ITEMS / "problems" / "ewc-continual-penalty",
        {
            "meta.yaml": """
id: ewc-continual-penalty
kind: problem
unit_id: gnn-continual
title: "Elastic Weight Consolidation (EWC) Penalty & Gradient"
difficulty: medium
xp: 40
estimated_minutes: 15
tags: ["continual-learning", "ewc", "catastrophic-forgetting", "fisher"]
order: 2
""",
            "prompt.md": """
# Elastic Weight Consolidation (EWC)

To mitigate catastrophic forgetting when training on Task B after Task A, EWC adds a quadratic anchor weighted by Task A's diagonal Fisher Information $F$:
$$L_{\\text{EWC}}(\\theta) = \\frac{\\lambda}{2} \\sum_i F_i (\\theta_i - \\theta^*_{A,i})^2$$

Implement `ewc_penalty_and_grad(theta, theta_star, fisher, lam)` returning `(penalty: float, grad: np.ndarray)` where `grad` is $\\nabla_\\theta L_{\\text{EWC}}(\\theta)$.
""",
            "theory.md": """
## Laplace Approximation View of EWC

EWC approximates the posterior over parameters given Task A data as a diagonal Gaussian centered at $\\theta^*_A$ with precision given by the diagonal Fisher matrix $F$, penalizing drift most strongly along high-curvature directions.
""",
            "starter.py": """
import numpy as np

def ewc_penalty_and_grad(
    theta: np.ndarray,
    theta_star: np.ndarray,
    fisher: np.ndarray,
    lam: float,
) -> tuple[float, np.ndarray]:
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def ewc_penalty_and_grad(
    theta: np.ndarray,
    theta_star: np.ndarray,
    fisher: np.ndarray,
    lam: float,
) -> tuple[float, np.ndarray]:
    diff = np.asarray(theta, dtype=np.float64) - np.asarray(theta_star, dtype=np.float64)
    F = np.asarray(fisher, dtype=np.float64)
    penalty = 0.5 * lam * float(np.sum(F * (diff ** 2)))
    grad = lam * F * diff
    return penalty, grad
""",
            "tests.py": """
import numpy as np

def test_ewc_values_and_finite_diff(user_mod):
    theta = np.array([1.2, -0.5, 2.0])
    star = np.array([1.0, 0.0, 1.5])
    F = np.array([10.0, 2.0, 0.5])
    lam = 4.0
    pen, grad = user_mod.ewc_penalty_and_grad(theta, star, F, lam)
    expected_pen = 0.5 * 4.0 * (10.0 * 0.04 + 2.0 * 0.25 + 0.5 * 0.25)
    np.testing.assert_allclose(pen, expected_pen, atol=1e-6)
    # Finite difference check
    eps = 1e-6
    for i in range(len(theta)):
        t_plus = theta.copy(); t_plus[i] += eps
        t_minus = theta.copy(); t_minus[i] -= eps
        p_plus, _ = user_mod.ewc_penalty_and_grad(t_plus, star, F, lam)
        p_minus, _ = user_mod.ewc_penalty_and_grad(t_minus, star, F, lam)
        np.testing.assert_allclose(grad[i], (p_plus - p_minus) / (2 * eps), atol=1e-5)
""",
        },
    )

    # ------------------------------------------------------------------
    # TRACK 3: POST-TRAINING & OPTIMIZATION (3 items)
    # ------------------------------------------------------------------
    write_files(
        ITEMS / "problems" / "int8-symmetric-quantization",
        {
            "meta.yaml": """
id: int8-symmetric-quantization
kind: problem
unit_id: quantization-compression
title: "Per-Channel Symmetric INT8 Quantization & Dequantization"
difficulty: easy
xp: 35
estimated_minutes: 15
tags: ["quantization", "int8", "ptq", "per-channel"]
order: 1
""",
            "prompt.md": """
# Per-Channel Symmetric INT8 Quantization

Implement `quantize_per_channel_int8(W: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]` for a 2D weight matrix `W` of shape `(C_out, C_in)`:
- For each output channel `c`, compute scale $s_c = \\max(|W_c|) / 127.0$ (if a channel is all zeros, set $s_c = 1.0$ to avoid division by zero).
- Quantize: $Q_c = \\mathrm{clip}(\\mathrm{round}(W_c / s_c), -127, 127)$ as `np.int8`.
- Dequantize: $\\hat{W}_c = Q_c \\cdot s_c$ as `np.float32`.
- Return `(Q, scales, W_dequant)` where `scales` has shape `(C_out, 1)`.
""",
            "theory.md": """
## Per-Channel vs Per-Tensor Quantization

A single outlier weight in one output channel ruins the dynamic range of an entire tensor under per-tensor scaling. Per-channel scales isolate outliers to their own row with negligible storage overhead (`1 float` per row).
""",
            "starter.py": """
import numpy as np

def quantize_per_channel_int8(W: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def quantize_per_channel_int8(W: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    W = np.asarray(W, dtype=np.float32)
    max_abs = np.max(np.abs(W), axis=1, keepdims=True)
    scales = np.where(max_abs > 0, max_abs / 127.0, 1.0).astype(np.float32)
    q = np.clip(np.round(W / scales), -127, 127).astype(np.int8)
    w_deq = (q.astype(np.float32) * scales).astype(np.float32)
    return q, scales, w_deq
""",
            "tests.py": """
import numpy as np

def test_outlier_isolation_and_zero_row(user_mod):
    W = np.array([
        [0.01, -0.02, 0.03, 0.04],
        [100.0, -50.0, 25.0, 0.0],
        [0.0, 0.0, 0.0, 0.0],
    ], dtype=np.float32)
    q, scales, w_deq = user_mod.quantize_per_channel_int8(W)
    assert q.dtype == np.int8
    assert scales.shape == (3, 1)
    # Row 0 should retain high precision despite row 1's 100.0 outlier
    np.testing.assert_allclose(w_deq[0], W[0], atol=5e-4)
    np.testing.assert_allclose(w_deq[1], W[1], atol=1.0)
    np.testing.assert_allclose(w_deq[2], np.zeros(4), atol=1e-7)
""",
        },
    )

    write_files(
        ITEMS / "problems" / "grpo-group-advantage",
        {
            "meta.yaml": """
id: grpo-group-advantage
kind: problem
unit_id: rl-post-training
title: "DeepSeek-R1 GRPO Group-Relative Advantage & Clipped Objective"
difficulty: medium
xp: 50
estimated_minutes: 20
tags: ["grpo", "rlhf", "post-training", "rl", "deepseek"]
order: 1
""",
            "prompt.md": """
# Group Relative Policy Optimization (GRPO)

Given a group of $G$ rollouts for one prompt:
- `rewards`: shape `(G,)`
- `logp_new`: shape `(G,)` (sum or mean token log-probs under current policy $\\pi_\\theta$)
- `logp_old`: shape `(G,)` (log-probs under behavior policy $\\pi_{\\text{old}}$)
- `logp_ref`: shape `(G,)` (log-probs under reference policy $\\pi_{\\text{ref}}$)
- `eps`: clip parameter (default `0.2`), `beta`: KL weight (default `0.04`)

Implement `grpo_loss(rewards, logp_new, logp_old, logp_ref, eps=0.2, beta=0.04) -> float`:
1. Group-normalized advantage: $A_i = \\frac{r_i - \\mathrm{mean}(r)}{\\mathrm{std}(r) + 10^{-8}}$.
2. Importance ratio: $\\rho_i = \\exp(\\log\\pi_\\theta - \\log\\pi_{\\text{old}})$.
3. Clipped surrogate: $s_i = \\min(\\rho_i A_i, \\mathrm{clip}(\\rho_i, 1-\\epsilon, 1+\\epsilon) A_i)$.
4. Unbiased Schulman KL estimator: $\\mathrm{KL}_i = \\exp(\\log\\pi_{\\text{ref}} - \\log\\pi_\\theta) - (\\log\\pi_{\\text{ref}} - \\log\\pi_\\theta) - 1$.
5. Return scalar loss to **minimize**: $-\\frac{1}{G}\\sum_i (s_i - \\beta \\cdot \\mathrm{KL}_i)$.
""",
            "theory.md": """
## Why GRPO Scales Reasoning RL

By normalizing rewards within a group of $G$ rollouts sampled for the *same* prompt, GRPO removes the learned critic network (cutting ~50% of training memory in PPO) while using the non-negative $k_3$ KL estimator $\\exp(\\Delta) - \\Delta - 1 \\ge 0$.
""",
            "starter.py": """
import numpy as np

def grpo_loss(
    rewards: np.ndarray,
    logp_new: np.ndarray,
    logp_old: np.ndarray,
    logp_ref: np.ndarray,
    eps: float = 0.2,
    beta: float = 0.04,
) -> float:
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def grpo_loss(
    rewards: np.ndarray,
    logp_new: np.ndarray,
    logp_old: np.ndarray,
    logp_ref: np.ndarray,
    eps: float = 0.2,
    beta: float = 0.04,
) -> float:
    r = np.asarray(rewards, dtype=np.float64)
    ln = np.asarray(logp_new, dtype=np.float64)
    lo = np.asarray(logp_old, dtype=np.float64)
    lr = np.asarray(logp_ref, dtype=np.float64)

    adv = (r - np.mean(r)) / (np.std(r) + 1e-8)
    ratio = np.exp(ln - lo)
    clipped = np.clip(ratio, 1.0 - eps, 1.0 + eps)
    surr = np.minimum(ratio * adv, clipped * adv)
    delta = lr - ln
    kl = np.exp(delta) - delta - 1.0
    return float(-np.mean(surr - beta * kl))
""",
            "tests.py": """
import numpy as np

def test_grpo_on_policy_zero_kl(user_mod):
    r = np.array([1.0, 0.0, 1.0, 0.0])
    lp = np.array([-2.0, -3.0, -2.5, -1.5])
    # On-policy (logp_new == logp_old == logp_ref): ratio=1, kl=0, mean(adv)=0 -> loss=0
    loss = user_mod.grpo_loss(r, lp, lp, lp)
    np.testing.assert_allclose(loss, 0.0, atol=1e-6)

def test_grpo_rewards_increasing_good_rollout(user_mod):
    r = np.array([1.0, 0.0, 0.0, 0.0])
    lo = np.array([-2.0, -2.0, -2.0, -2.0])
    ln_better = np.array([-1.85, -2.0, -2.0, -2.0])
    loss_better = user_mod.grpo_loss(r, ln_better, lo, lo, beta=0.01)
    assert loss_better < 0.0
""",
        },
    )

    write_files(
        ITEMS / "problems" / "dpo-preference-loss",
        {
            "meta.yaml": """
id: dpo-preference-loss
kind: problem
unit_id: rl-post-training
title: "Direct Preference Optimization (DPO) Loss & Implicit Reward Margin"
difficulty: medium
xp: 45
estimated_minutes: 15
tags: ["dpo", "rlhf", "post-training", "alignment"]
order: 2
""",
            "prompt.md": """
# Direct Preference Optimization (DPO)

Given batch arrays of shape `(B,)`:
- `pi_chosen`, `pi_rejected`: policy log-probabilities $\\log\\pi_\\theta(y_w|x), \\log\\pi_\\theta(y_l|x)$
- `ref_chosen`, `ref_rejected`: reference log-probabilities $\\log\\pi_{\\text{ref}}(y_w|x), \\log\\pi_{\\text{ref}}(y_l|x)$
- `beta`: temperature parameter (default `0.1`)

Implement `dpo_loss(pi_chosen, pi_rejected, ref_chosen, ref_rejected, beta=0.1) -> tuple[float, float]`:
- Implicit reward margin: $h_i = \\beta [(\\log\\pi_\\theta(y_w) - \\log\\pi_{\\text{ref}}(y_w)) - (\\log\\pi_\\theta(y_l) - \\log\\pi_{\\text{ref}}(y_l))]$.
- Loss: $\\mathcal{L}_{\\text{DPO}} = -\\mathrm{mean}(\\log\\sigma(h_i)) = \\mathrm{mean}(\\log(1 + e^{-h_i}))$ (use numerically stable `logaddexp`).
- Return `(loss: float, mean_margin: float)`.
""",
            "theory.md": """
## Closed-Form Optimal Policy in DPO

DPO reparameterizes the Bradley-Terry preference model directly in terms of the KL-regularized optimal policy, replacing explicit reward modeling and online RL sampling with a simple binary cross-entropy over log-probability ratios.
""",
            "starter.py": """
import numpy as np

def dpo_loss(
    pi_chosen: np.ndarray,
    pi_rejected: np.ndarray,
    ref_chosen: np.ndarray,
    ref_rejected: np.ndarray,
    beta: float = 0.1,
) -> tuple[float, float]:
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def dpo_loss(
    pi_chosen: np.ndarray,
    pi_rejected: np.ndarray,
    ref_chosen: np.ndarray,
    ref_rejected: np.ndarray,
    beta: float = 0.1,
) -> tuple[float, float]:
    h = beta * ((np.asarray(pi_chosen) - np.asarray(ref_chosen)) - (np.asarray(pi_rejected) - np.asarray(ref_rejected)))
    loss = float(np.mean(np.logaddexp(0.0, -h)))
    return loss, float(np.mean(h))
""",
            "tests.py": """
import numpy as np

def test_dpo_zero_margin_is_log2(user_mod):
    a = np.array([-1.0, -2.0])
    loss, margin = user_mod.dpo_loss(a, a, a, a, beta=0.1)
    np.testing.assert_allclose(loss, np.log(2.0), atol=1e-6)
    np.testing.assert_allclose(margin, 0.0, atol=1e-6)

def test_dpo_numerical_stability_extreme_margin(user_mod):
    loss, margin = user_mod.dpo_loss(np.array([-1000.0]), np.array([0.0]), np.array([0.0]), np.array([0.0]), beta=1.0)
    assert np.isfinite(loss)
    np.testing.assert_allclose(loss, 1000.0, atol=1e-4)
""",
        },
    )

    # ------------------------------------------------------------------
    # TRACK 4: SYSTEMS & INFERENCE (CORE) (5 items: puzzle, math, problem, lab, project)
    # ------------------------------------------------------------------
    write_files(
        ITEMS / "puzzles" / "kv-cache-memory-waste",
        {
            "meta.yaml": """
id: kv-cache-memory-waste
kind: puzzle
unit_id: roofline-kv-memory
title: "Ragged Sequence Fragmentation (Why PagedAttention Exists)"
difficulty: medium
xp: 35
estimated_minutes: 15
tags: ["kv-cache", "paged-attention", "inference", "fragmentation", "intuition"]
order: 1
""",
            "prompt.md": """
# Invent a Low-Waste KV-Cache Allocator

An inference engine serves concurrent requests with varying actual lengths `seq_lens: list[int]`, each with a worst-case maximum length `max_len: int`.

Write `allocated_slots(seq_lens: list[int], max_len: int) -> int` returning the **total KV-cache token slots allocated** by your memory scheme.
Your scheme must satisfy two competing realities:
1. **No Overflow:** You must allocate at least `sum(seq_lens)` slots (you can't store more tokens than slots).
2. **Page-Aligned Efficiency:** Real GPU kernels cannot allocate 1 token at a time (huge pointer overhead), so your allocator must reserve in fixed-size chunks (blocks of size 16 or 32) — **yet** when 64 requests have short actual lengths (30–200 tokens) under `max_len=4096`, your waste ratio `(allocated - used) / allocated` must stay **below 20%** (naive contiguous pre-allocation wastes > 95%!).
3. **Single-Token Boundary:** Even a 1-token sequence must allocate at least 1 block (≥ 16 slots), proving you aren't cheating with block_size=1.
""",
            "starter.py": """
def allocated_slots(seq_lens: list[int], max_len: int) -> int:
    # Naive contiguous pre-allocation reserves max_len for every request!
    return len(seq_lens) * max_len
""",
            "reference.py": """
import math

def allocated_slots(seq_lens: list[int], max_len: int) -> int:
    block_size = 16
    return sum(max(1, math.ceil(L / block_size)) * block_size for L in seq_lens)
""",
            "tests.py": """
def run_counterexamples(fn):
    failures = []
    # 1. No overflow
    lens = [17, 33, 64, 129]
    alloc = fn(lens, 4096)
    used = sum(lens)
    if alloc < used:
        failures.append({
            "property": "No KV-Cache Overflow",
            "input": f"seq_lens={lens}, max_len=4096",
            "your_output": f"allocated={alloc} < used={used}",
            "why_broken": "Allocated fewer token slots than actual tokens in flight."
        })
    # 2. Block alignment check (prevent trivial block_size=1)
    one_tok = fn([1], 4096)
    if one_tok < 16 or one_tok % 16 != 0:
        failures.append({
            "property": "Hardware Block Alignment (>=16)",
            "input": "seq_lens=[1], max_len=4096",
            "your_output": f"allocated={one_tok}",
            "why_broken": "GPU paged KV blocks must be aligned to at least 16-token pages (got non-page-aligned allocation)."
        })
    # 3. Ragged batch waste attack
    ragged = [45, 110, 80, 150, 62, 195, 90, 120] * 8
    used_r = sum(ragged)
    alloc_r = fn(ragged, 4096)
    waste = (alloc_r - used_r) / max(1, alloc_r)
    if waste >= 0.20:
        failures.append({
            "property": "Ragged Batch Fragmentation (<20% waste)",
            "input": "64 requests of len 45..195 with max_len=4096",
            "your_output": f"used={used_r}, allocated={alloc_r}, waste={waste*100:.1f}%",
            "why_broken": f"You wasted {waste*100:.1f}% of HBM! Paged block allocation caps waste to <1 block per sequence."
        })
    return failures
""",
        },
    )

    write_files(
        ITEMS / "math" / "roofline-and-kv-cache-math",
        {
            "meta.yaml": """
id: roofline-and-kv-cache-math
kind: math
unit_id: roofline-kv-memory
title: "KV-Cache Sizing & GPU Roofline Arithmetic Intensity"
difficulty: medium
xp: 40
estimated_minutes: 15
tags: ["roofline", "kv-cache", "hbm", "arithmetic-intensity", "inference"]
order: 2
""",
            "worked_example.md": """
# Worked Example: Sizing KV-Cache & Roofline Ridge Point

For a Transformer with $L$ layers, $H_{kv}$ KV heads (GQA), head dimension $d_h$, precision $b$ bytes/element, sequence length $S$, and batch size $B$:
$$\\text{KV Bytes} = 2 \\cdot L \\cdot H_{kv} \\cdot d_h \\cdot b \\cdot S \\cdot B$$
*(The factor of $2$ accounts for both Keys and Values.)*

On an accelerator with peak compute $F_{\\text{peak}}$ (FLOP/s) and HBM bandwidth $BW$ (bytes/s), the **Roofline Ridge Point** is:
$$I_{\\text{ridge}} = \\frac{F_{\\text{peak}}}{BW} \\quad [\\text{FLOP/byte}]$$
An operation with arithmetic intensity $I < I_{\\text{ridge}}$ is **memory-bandwidth bound**; $I > I_{\\text{ridge}}$ is **compute bound**.
""",
            "drills.yaml": """
drills:
  - id: kv-formula
    prompt: "Write the symbolic formula for total KV-cache bytes for 1 token across L layers, H_kv heads, head dim d_h, and b bytes per element. (Use variables `L`, `H_kv`, `d_h`, `b`)"
    mode: symbolic
    symbols: ["L", "H_kv", "d_h", "b"]
    expected: "2 * L * H_kv * d_h * b"
    hint: "Keys and Values each store L * H_kv * d_h * b bytes per token."
  - id: ridge-point
    prompt: "An H100 SXM delivers 989 TFLOP/s (BF16) and 3.35 TB/s HBM3 bandwidth. What is its Roofline ridge point in FLOP/byte? (Round to 1 decimal place)"
    mode: numeric
    expected: 295.2
    tol: 0.5
    hint: "989 / 3.35 ≈ 295.2 FLOP/byte."
  - id: kv-bytes-concrete
    prompt: "A model has L=32 layers, H_kv=8 GQA heads, d_h=128, FP16 (2 bytes). How many MiB (divide bytes by 1024^2) does a single 8192-token sequence's KV-cache consume?"
    mode: numeric
    expected: 1024.0
    tol: 0.5
    hint: "2 * 32 * 8 * 128 * 2 * 8192 / (1024*1024) = 1024 MiB (1 GiB)."
""",
        },
    )

    write_files(
        ITEMS / "problems" / "paged-kv-cache-allocator",
        {
            "meta.yaml": """
id: paged-kv-cache-allocator
kind: problem
unit_id: paged-serving-speculative
title: "PagedAttention Physical Block Allocator with Copy-on-Write Fork"
difficulty: hard
xp: 65
estimated_minutes: 30
tags: ["paged-attention", "vllm", "kv-cache", "ml-infra", "systems"]
order: 1
""",
            "prompt.md": """
# PagedAttention Block Allocator with Copy-on-Write (CoW)

Implement class `BlockManager(num_blocks: int, block_size: int)`:
- `allocate_seq(seq_id: str, num_tokens: int) -> list[int]`: Allocates the minimum number of physical blocks (`ceil(num_tokens / block_size)`) from the free pool. Raises `MemoryError` if insufficient free blocks.
- `fork_seq(src_seq_id: str, dst_seq_id: str) -> None`: **Zero-copy prefix sharing!** `dst_seq_id` shares `src_seq_id`'s physical block IDs and increments each block's reference count (`ref_count`).
- `append_token(seq_id: str) -> int`: Appends 1 token to `seq_id`.
  - If the last logical block is **full** (`len % block_size == 0`), allocate a new physical block.
  - If the last logical block is **not full** AND its `ref_count > 1`, perform **Copy-on-Write**: decrement old block's `ref_count`, allocate a fresh physical block, replace the last block entry for `seq_id`, and return the new physical block ID!
  - Otherwise return the current last physical block ID.
- `free_seq(seq_id: str) -> None`: Decrements `ref_count` on every block held by `seq_id`, returning blocks whose `ref_count == 0` back to the free pool.
- `num_free_blocks() -> int`: Returns number of currently free physical blocks.
""",
            "theory.md": """
## Why Copy-on-Write Matters in Beam Search & Prefix Caching

In vLLM, shared system prompts and parallel beam search branches point their logical block tables to the **same physical KV blocks** (`ref_count > 1`). Only when a branch mutates a partially filled tail block does CoW allocate a private copy — saving up to 55% of KV HBM during parallel sampling.
""",
            "starter.py": """
import math

class BlockManager:
    def __init__(self, num_blocks: int, block_size: int):
        raise NotImplementedError

    def num_free_blocks(self) -> int:
        raise NotImplementedError

    def allocate_seq(self, seq_id: str, num_tokens: int) -> list[int]:
        raise NotImplementedError

    def fork_seq(self, src_seq_id: str, dst_seq_id: str) -> None:
        raise NotImplementedError

    def append_token(self, seq_id: str) -> int:
        raise NotImplementedError

    def free_seq(self, seq_id: str) -> None:
        raise NotImplementedError
""",
            "reference.py": """
import math

class BlockManager:
    def __init__(self, num_blocks: int, block_size: int):
        self.num_blocks = num_blocks
        self.block_size = block_size
        self.free_blocks = list(range(num_blocks - 1, -1, -1))
        self.ref_counts = [0] * num_blocks
        self.block_tables: dict[str, list[int]] = {}
        self.seq_lens: dict[str, int] = {}

    def num_free_blocks(self) -> int:
        return len(self.free_blocks)

    def _alloc_one(self) -> int:
        if not self.free_blocks:
            raise MemoryError("Out of KV-cache physical blocks")
        bid = self.free_blocks.pop()
        self.ref_counts[bid] = 1
        return bid

    def allocate_seq(self, seq_id: str, num_tokens: int) -> list[int]:
        needed = max(1, math.ceil(num_tokens / self.block_size)) if num_tokens > 0 else 0
        if needed > len(self.free_blocks):
            raise MemoryError("Out of KV-cache physical blocks")
        blocks = [self._alloc_one() for _ in range(needed)]
        self.block_tables[seq_id] = blocks
        self.seq_lens[seq_id] = num_tokens
        return list(blocks)

    def fork_seq(self, src_seq_id: str, dst_seq_id: str) -> None:
        src_blocks = self.block_tables[src_seq_id]
        for bid in src_blocks:
            self.ref_counts[bid] += 1
        self.block_tables[dst_seq_id] = list(src_blocks)
        self.seq_lens[dst_seq_id] = self.seq_lens[src_seq_id]

    def append_token(self, seq_id: str) -> int:
        cur_len = self.seq_lens[seq_id]
        table = self.block_tables[seq_id]
        if cur_len % self.block_size == 0:
            new_bid = self._alloc_one()
            table.append(new_bid)
            self.seq_lens[seq_id] = cur_len + 1
            return new_bid
        last_bid = table[-1]
        if self.ref_counts[last_bid] > 1:
            new_bid = self._alloc_one()
            self.ref_counts[last_bid] -= 1
            table[-1] = new_bid
            self.seq_lens[seq_id] = cur_len + 1
            return new_bid
        self.seq_lens[seq_id] = cur_len + 1
        return last_bid

    def free_seq(self, seq_id: str) -> None:
        table = self.block_tables.pop(seq_id)
        self.seq_lens.pop(seq_id)
        for bid in table:
            self.ref_counts[bid] -= 1
            if self.ref_counts[bid] == 0:
                self.free_blocks.append(bid)
""",
            "tests.py": """
import pytest

def test_cow_fork_and_free(user_mod):
    bm = user_mod.BlockManager(num_blocks=6, block_size=4)
    b_src = bm.allocate_seq("s1", 6)  # uses 2 blocks (2nd block half full)
    assert len(b_src) == 2
    assert bm.num_free_blocks() == 4

    bm.fork_seq("s1", "s2")  # zero new blocks!
    assert bm.num_free_blocks() == 4

    # Appending to s2 triggers Copy-on-Write on the shared partial block
    cow_bid = bm.append_token("s2")
    assert cow_bid != b_src[-1]
    assert bm.num_free_blocks() == 3

    # Freeing s1 releases only blocks whose ref_count hits 0 (s2 still holds b_src[0])
    bm.free_seq("s1")
    assert bm.num_free_blocks() == 4

    bm.free_seq("s2")
    assert bm.num_free_blocks() == 6

def test_oom_raises(user_mod):
    bm = user_mod.BlockManager(num_blocks=2, block_size=4)
    with pytest.raises(MemoryError):
        bm.allocate_seq("big", 12)
""",
        },
    )

    write_files(
        ITEMS / "labs" / "speculative-decoding-lab",
        {
            "meta.yaml": """
id: speculative-decoding-lab
kind: lab
unit_id: paged-serving-speculative
title: "Lab: Exact Speculative Decoding Rejection Sampler"
difficulty: hard
xp: 75
estimated_minutes: 30
tags: ["speculative-decoding", "inference", "sampling", "lab"]
metric_name: "tv_distance"
metric_goal: "<= 0.02"
order: 2
""",
            "prompt.md": """
# Lab: Distribution-Preserving Speculative Decoding

Implement `speculative_step(p_target: np.ndarray, q_draft: np.ndarray, draft_token: int, rng: np.random.Generator) -> int`:
- `p_target` and `q_draft` are 1D probability distributions over vocabulary size `V`.
- `draft_token` was already sampled from `q_draft`.
- Accept `draft_token` with probability $\\min\\left(1, \\frac{p(x)}{q(x)}\\right)$.
- If rejected, sample a replacement token from the **normalized residual distribution**:
  $$p_{\\text{res}}(x) = \\frac{\\max(0, p(x) - q(x))}{\\sum_j \\max(0, p(j) - q(j))}$$

### Lab Evaluation Gate
The harness runs 40,000 Monte Carlo trials across skewed draft/target distributions and verifies Total Variation Distance `TV(empirical, p_target) <= 0.02`.
""",
            "starter.py": """
import numpy as np

def speculative_step(
    p_target: np.ndarray,
    q_draft: np.ndarray,
    draft_token: int,
    rng: np.random.Generator,
) -> int:
    # Naive bug: always accepts draft token (distorts distribution!)
    return draft_token
""",
            "reference.py": """
import numpy as np

def speculative_step(
    p_target: np.ndarray,
    q_draft: np.ndarray,
    draft_token: int,
    rng: np.random.Generator,
) -> int:
    p = np.asarray(p_target, dtype=np.float64)
    q = np.asarray(q_draft, dtype=np.float64)
    accept_prob = min(1.0, float(p[draft_token]) / max(float(q[draft_token]), 1e-12))
    if rng.random() < accept_prob:
        return int(draft_token)
    residual = np.maximum(0.0, p - q)
    total = float(residual.sum())
    if total <= 1e-12:
        return int(rng.choice(len(p), p=p))
    residual /= total
    return int(rng.choice(len(p), p=residual))
""",
            "tests.py": """
import numpy as np

def evaluate_lab(user_mod):
    rng = np.random.default_rng(2026)
    p = np.array([0.45, 0.25, 0.15, 0.10, 0.05], dtype=np.float64)
    q = np.array([0.15, 0.45, 0.25, 0.05, 0.10], dtype=np.float64)
    V = len(p)
    counts = np.zeros(V, dtype=np.float64)
    trials = 25000
    draft_tokens = rng.choice(V, size=trials, p=q)
    for dt in draft_tokens:
        tok = user_mod.speculative_step(p, q, int(dt), rng)
        counts[int(tok)] += 1
    emp = counts / trials
    tv = 0.5 * float(np.sum(np.abs(emp - p)))
    passed = tv <= 0.02
    return {
        "passed": passed,
        "metric": round(tv, 5),
        "threshold": 0.02,
        "details": f"Total Variation Distance = {tv:.5f} (target <= 0.02; exact target match preserved)"
    }
""",
        },
    )

    write_files(
        ITEMS / "projects" / "mini-inference-scheduler",
        {
            "meta.yaml": """
id: mini-inference-scheduler
kind: project
unit_id: paged-serving-speculative
title: "Project: Continuous Batching & KV-Budget Inference Scheduler"
difficulty: hard
xp: 100
estimated_minutes: 45
tags: ["continuous-batching", "scheduler", "vllm", "inference", "project", "ml-infra"]
order: 3
milestones:
  - id: m1
    title: "Milestone 1: Request Admission & KV Budget Check"
  - id: m2
    title: "Milestone 2: Iteration-Level Decode + Completion Eviction"
  - id: m3
    title: "Milestone 3: Preemption Under Memory Pressure"
""",
            "prompt.md": """
# Capstone Project: Mini Continuous-Batching LLM Scheduler

Build a working iteration-level inference scheduler `ContinuousBatchScheduler(max_kv_tokens: int, max_batch_size: int)`:
- `add_request(req_id: str, prompt_len: int, max_new_tokens: int) -> None`: Adds a waiting request to FIFO queue.
- `step() -> dict`: Executes **one engine iteration**:
  1. **Running Decode:** Each currently running request generates 1 token (increasing its `kv_used` by 1 and `generated` by 1). If total KV across running requests exceeds `max_kv_tokens`, **preempt** the most recently admitted running request back to the front of the waiting queue (freeing its KV and resetting `generated = 0`) until KV fits!
  2. **Admit Waiting Requests:** While `len(running) < max_batch_size` and waiting queue is non-empty, admit the next request if `total_kv + req.prompt_len <= max_kv_tokens` (Prefill consumes `prompt_len` KV tokens immediately).
  3. **Evict Finished:** Any running request with `generated >= max_new_tokens` is moved to `finished` and its KV is freed.
  4. Return `{"running": [...ids], "finished_this_step": [...ids], "kv_used": int, "waiting": int}`.
""",
            "theory.md": """
## Why Continuous (Iteration-Level) Batching 10x's Throughput

Static batching forces short sequences to sit idle until the longest sequence finishes (GPU bubble). Iteration-level scheduling (Orca / vLLM) frees finished KV blocks on the exact step an EOS occurs and immediately slots waiting prefills into the active batch.
""",
            "starter.py": """
from collections import deque

class ContinuousBatchScheduler:
    def __init__(self, max_kv_tokens: int, max_batch_size: int):
        raise NotImplementedError

    def add_request(self, req_id: str, prompt_len: int, max_new_tokens: int) -> None:
        raise NotImplementedError

    def step(self) -> dict:
        raise NotImplementedError
""",
            "reference.py": """
from collections import deque

class ContinuousBatchScheduler:
    def __init__(self, max_kv_tokens: int, max_batch_size: int):
        self.max_kv_tokens = max_kv_tokens
        self.max_batch_size = max_batch_size
        self.waiting = deque()
        self.running: list[dict] = []

    def add_request(self, req_id: str, prompt_len: int, max_new_tokens: int) -> None:
        self.waiting.append({
            "id": req_id,
            "prompt_len": prompt_len,
            "max_new_tokens": max_new_tokens,
            "generated": 0,
            "kv": 0,
        })

    def _kv_used(self) -> int:
        return sum(r["kv"] for r in self.running)

    def step(self) -> dict:
        # 1. Decode step for currently running requests
        for r in self.running:
            r["generated"] += 1
            r["kv"] += 1

        # Preempt newest running requests if KV budget exceeded
        while self._kv_used() > self.max_kv_tokens and self.running:
            victim = self.running.pop()
            victim["generated"] = 0
            victim["kv"] = 0
            self.waiting.appendleft(victim)

        # 2. Evict completed requests before admitting new ones (or after decode)
        finished_now = []
        still_running = []
        for r in self.running:
            if r["generated"] >= r["max_new_tokens"]:
                finished_now.append(r["id"])
            else:
                still_running.append(r)
        self.running = still_running

        # 3. Admit waiting requests (prefill)
        while self.waiting and len(self.running) < self.max_batch_size:
            nxt = self.waiting[0]
            if self._kv_used() + nxt["prompt_len"] <= self.max_kv_tokens:
                self.waiting.popleft()
                nxt["kv"] = nxt["prompt_len"]
                nxt["generated"] = 0
                self.running.append(nxt)
            else:
                break

        return {
            "running": [r["id"] for r in self.running],
            "finished_this_step": finished_now,
            "kv_used": self._kv_used(),
            "waiting": len(self.waiting),
        }
""",
            "tests.py": """
def test_milestone_1_admission_and_budget(user_mod):
    s = user_mod.ContinuousBatchScheduler(max_kv_tokens=20, max_batch_size=2)
    s.add_request("r1", prompt_len=12, max_new_tokens=2)
    s.add_request("r2", prompt_len=10, max_new_tokens=2)
    st = s.step()
    assert st["running"] == ["r1"]
    assert st["kv_used"] == 12
    assert st["waiting"] == 1

def test_milestone_2_eviction_and_continuous_refill(user_mod):
    s = user_mod.ContinuousBatchScheduler(max_kv_tokens=20, max_batch_size=2)
    s.add_request("r1", prompt_len=12, max_new_tokens=2)
    s.add_request("r2", prompt_len=10, max_new_tokens=1)
    s.step()  # admit r1 (kv=12)
    st2 = s.step()  # r1 gen=1, kv=13
    assert st2["running"] == ["r1"]
    st3 = s.step()  # r1 gen=2 -> finished & evicted, r2 admitted!
    assert "r1" in st3["finished_this_step"]
    assert "r2" in st3["running"]

def test_milestone_3_preemption_under_pressure(user_mod):
    s = user_mod.ContinuousBatchScheduler(max_kv_tokens=10, max_batch_size=2)
    s.add_request("r1", prompt_len=5, max_new_tokens=3)
    s.add_request("r2", prompt_len=5, max_new_tokens=3)
    st1 = s.step()  # both admitted, kv=10
    assert st1["kv_used"] == 10
    st2 = s.step()  # decode would need 12 > 10 -> r2 preempted!
    assert st2["kv_used"] <= 10
    assert st2["running"] == ["r1"]
    assert st2["waiting"] == 1
""",
        },
    )

    # ------------------------------------------------------------------
    # TRACK 5: OPERATIONS & GOVERNANCE (2 items)
    # ------------------------------------------------------------------
    write_files(
        ITEMS / "problems" / "linear-probe-and-ablation",
        {
            "meta.yaml": """
id: linear-probe-and-ablation
kind: problem
unit_id: mlops-safety-interp
title: "Directional Concept Erasure (Amnesic Probing / Orthogonal Ablation)"
difficulty: medium
xp: 45
estimated_minutes: 20
tags: ["ai-safety", "interpretability", "probes", "ablation", "governance"]
order: 1
""",
            "prompt.md": """
# Causal Concept Erasure (Orthogonal Projection Ablation)

Given hidden activations `H` of shape `(N, D)` and a learned linear concept direction `v` of shape `(D,)`:

Implement `erase_concept_direction(H: np.ndarray, v: np.ndarray) -> np.ndarray`:
1. Normalize $u = v / \\|v\\|_2$.
2. Project every row of `H` onto the orthogonal complement of $u$:
   $$H_{\\text{erased}} = H - (H u) u^\\top$$
3. Return `H_erased` of shape `(N, D)`. If $\\|v\\|_2 == 0$, raise `ValueError`.
""",
            "theory.md": """
## Amnesic Probing & Refusal Ablation

Projecting activations onto $I - u u^\\top$ removes all linear information along direction $u$ (making any probe aligned with $u$ drop to chance) while minimally perturbing orthogonal features.
""",
            "starter.py": """
import numpy as np

def erase_concept_direction(H: np.ndarray, v: np.ndarray) -> np.ndarray:
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def erase_concept_direction(H: np.ndarray, v: np.ndarray) -> np.ndarray:
    H = np.asarray(H, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    norm = float(np.linalg.norm(v))
    if norm == 0.0:
        raise ValueError("Concept direction vector cannot be zero")
    u = v / norm
    proj = np.outer(H @ u, u)
    return H - proj
""",
            "tests.py": """
import numpy as np
import pytest

def test_erasure_orthogonality_and_idempotence(user_mod):
    rng = np.random.default_rng(99)
    H = rng.standard_normal((20, 8))
    v = rng.standard_normal(8)
    He = user_mod.erase_concept_direction(H, v)
    # Projection onto v must be zero
    np.testing.assert_allclose(He @ v, np.zeros(20), atol=1e-6)
    # Idempotence: erasing twice equals erasing once
    He2 = user_mod.erase_concept_direction(He, v)
    np.testing.assert_allclose(He2, He, atol=1e-6)

def test_zero_vector_raises(user_mod):
    with pytest.raises(ValueError):
        user_mod.erase_concept_direction(np.ones((4, 3)), np.zeros(3))
""",
        },
    )

    write_files(
        ITEMS / "problems" / "psi-feature-drift-detector",
        {
            "meta.yaml": """
id: psi-feature-drift-detector
kind: problem
unit_id: mlops-safety-interp
title: "MLOps Production Feature Drift Monitor (Population Stability Index)"
difficulty: easy
xp: 35
estimated_minutes: 15
tags: ["mlops", "drift", "psi", "monitoring"]
order: 2
""",
            "prompt.md": """
# Population Stability Index (PSI) for Production Drift

Implement `compute_psi(expected: np.ndarray, actual: np.ndarray, num_bins: int = 10, eps: float = 1e-6) -> tuple[float, str]`:
1. Compute quantile bin edges from `expected` (from `0` to `100` percentiles, with `-inf` and `+inf` outer edges so out-of-range production values are captured).
2. Compute bin proportions $e_i, a_i$ for `expected` and `actual`, clamping any zero proportion to `eps`.
3. Compute $\\mathrm{PSI} = \\sum_i (a_i - e_i) \\ln(a_i / e_i)$.
4. Return `(psi, status)` where `status` is `"ok"` if `psi < 0.1`, `"moderate_drift"` if `0.1 <= psi < 0.25`, else `"severe_drift"`.
""",
            "theory.md": """
## Monitoring Data Drift in MLOps

PSI is the symmetric KL divergence (Jeffreys divergence) between binned training (`expected`) and production (`actual`) distributions. Industry thresholds: `< 0.1` stable, `0.1–0.25` investigate, `>= 0.25` trigger retraining alert.
""",
            "starter.py": """
import numpy as np

def compute_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_bins: int = 10,
    eps: float = 1e-6,
) -> tuple[float, str]:
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def compute_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_bins: int = 10,
    eps: float = 1e-6,
) -> tuple[float, str]:
    exp = np.asarray(expected, dtype=np.float64)
    act = np.asarray(actual, dtype=np.float64)
    quantiles = np.linspace(0, 100, num_bins + 1)
    edges = np.percentile(exp, quantiles)
    edges[0] = -np.inf
    edges[-1] = np.inf
    edges = np.unique(edges)

    e_counts, _ = np.histogram(exp, bins=edges)
    a_counts, _ = np.histogram(act, bins=edges)
    e_pct = np.clip(e_counts / max(len(exp), 1), eps, None)
    a_pct = np.clip(a_counts / max(len(act), 1), eps, None)

    psi = float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))
    if psi < 0.1:
        status = "ok"
    elif psi < 0.25:
        status = "moderate_drift"
    else:
        status = "severe_drift"
    return psi, status
""",
            "tests.py": """
import numpy as np

def test_no_drift_vs_severe_drift(user_mod):
    rng = np.random.default_rng(10)
    base = rng.normal(0.0, 1.0, size=2000)
    same = rng.normal(0.0, 1.0, size=2000)
    shifted = rng.normal(1.5, 1.0, size=2000)

    psi_ok, st_ok = user_mod.compute_psi(base, same)
    assert psi_ok < 0.1 and st_ok == "ok"

    psi_bad, st_bad = user_mod.compute_psi(base, shifted)
    assert psi_bad >= 0.25 and st_bad == "severe_drift"
""",
        },
    )

    # ------------------------------------------------------------------
    # EXTRA 3 DEEP ITEMS TO REACH 18 TOTAL (Systems/Inference + Math/DL + LLM)
    # ------------------------------------------------------------------
    write_files(
        ITEMS / "problems" / "flash-attention-online-softmax",
        {
            "meta.yaml": """
id: flash-attention-online-softmax
kind: problem
unit_id: roofline-kv-memory
title: "FlashAttention Online Softmax Tile Update"
difficulty: hard
xp: 65
estimated_minutes: 25
tags: ["flash-attention", "inference", "gpu-kernels", "sram", "softmax"]
order: 3
""",
            "prompt.md": """
# FlashAttention Online Softmax Rescaling

Implement `online_softmax_attention(q: np.ndarray, K: np.ndarray, V: np.ndarray, block_size: int = 4) -> np.ndarray`:
- `q`: single query vector `(D,)`
- `K`: keys `(N, D)`
- `V`: values `(N, D)`
- Process `(K, V)` strictly in streaming blocks of size `block_size` without ever materializing the full `(N,)` attention weight vector!
- Maintain running `(m, l, acc)` where `m` is running max logit, `l` is running denominator sum, and `acc` is running unnormalized weighted value sum.
- Return the exact attention output `(D,)` matching standard scaled dot-product attention.
""",
            "theory.md": """
## Online Softmax Is the Heart of FlashAttention

When a new tile yields max $m_{\\text{new}} = \\max(m, m_{\\text{tile}})$, rescaling prior accumulators by $e^{m - m_{\\text{new}}}$ allows streaming $K, V$ tiles through GPU SRAM in $O(N)$ HBM reads instead of $O(N^2)$.
""",
            "starter.py": """
import numpy as np

def online_softmax_attention(
    q: np.ndarray, K: np.ndarray, V: np.ndarray, block_size: int = 4
) -> np.ndarray:
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def online_softmax_attention(
    q: np.ndarray, K: np.ndarray, V: np.ndarray, block_size: int = 4
) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    K = np.asarray(K, dtype=np.float64)
    V = np.asarray(V, dtype=np.float64)
    N, D = K.shape
    scale = 1.0 / np.sqrt(D)
    m = -np.inf
    l = 0.0
    acc = np.zeros(D, dtype=np.float64)
    for start in range(0, N, block_size):
        k_blk = K[start:start + block_size]
        v_blk = V[start:start + block_size]
        scores = (k_blk @ q) * scale
        m_blk = float(np.max(scores))
        m_new = max(m, m_blk)
        alpha = np.exp(m - m_new) if np.isfinite(m) else 0.0
        p_blk = np.exp(scores - m_new)
        l = l * alpha + float(np.sum(p_blk))
        acc = acc * alpha + (p_blk @ v_blk)
        m = m_new
    return acc / l
""",
            "tests.py": """
import numpy as np

def test_matches_full_attention_exact(user_mod):
    rng = np.random.default_rng(17)
    N, D = 23, 16
    q = rng.standard_normal(D)
    K = rng.standard_normal((N, D))
    V = rng.standard_normal((N, D))
    out = user_mod.online_softmax_attention(q, K, V, block_size=5)
    scores = (K @ q) / np.sqrt(D)
    scores -= scores.max()
    w = np.exp(scores) / np.exp(scores).sum()
    expected = w @ V
    np.testing.assert_allclose(out, expected, rtol=1e-6, atol=1e-6)
""",
        },
    )

    write_files(
        ITEMS / "problems" / "ir-operator-fusion-pass",
        {
            "meta.yaml": """
id: ir-operator-fusion-pass
kind: problem
unit_id: paged-serving-speculative
title: "ML Compiler Pass: Pointwise Operator Fusion over SSA DAG"
difficulty: hard
xp: 60
estimated_minutes: 25
tags: ["compilers", "mlir", "fusion", "graph", "systems", "swe-infra"]
order: 4
""",
            "prompt.md": """
# ML Compiler Pass: Producer-Consumer Pointwise Fusion

Given an SSA computation graph as a topologically sorted list of node dicts:
```python
{"id": str, "op": str, "inputs": list[str], "kind": "compute" | "elementwise" | "io"}
```
Implement `fuse_elementwise_chains(nodes: list[dict]) -> list[list[str]]`:
- Group consecutive `elementwise` nodes into fused kernel groups (lists of node IDs) whenever:
  1. A producer `u` (`elementwise`) is consumed **exclusively** by a single consumer `v` (`elementwise`) (fan-out of `u` is 1), OR
  2. A `compute` node (e.g., `matmul`) feeds directly into a single-consumer `elementwise` epilogue (e.g., `bias_add` -> `gelu`), fusing the compute node + its linear elementwise epilogue chain!
- Never fuse two `compute` nodes together, and never fuse `io` nodes.
- Return the list of fused groups in topological order.
""",
            "theory.md": """
## Why Epilogue Fusion Eliminates HBM Round-Trips

In `torch.compile` (Inductor) and XLA, fusing `matmul -> bias_add -> gelu` keeps the intermediate tensor in GPU registers instead of writing and re-reading tens of megabytes to HBM between separate kernel launches.
""",
            "starter.py": """
def fuse_elementwise_chains(nodes: list[dict]) -> list[list[str]]:
    raise NotImplementedError
""",
            "reference.py": """
def fuse_elementwise_chains(nodes: list[dict]) -> list[list[str]]:
    consumers: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    node_map = {n["id"]: n for n in nodes}
    for n in nodes:
        for inp in n.get("inputs", []):
            if inp in consumers:
                consumers[inp].append(n["id"])

    visited = set()
    groups: list[list[str]] = []

    for n in nodes:
        nid = n["id"]
        if nid in visited:
            continue
        kind = n["kind"]
        if kind == "io":
            visited.add(nid)
            groups.append([nid])
            continue
        # Start a group from compute or elementwise
        group = [nid]
        visited.add(nid)
        cur = nid
        while len(consumers[cur]) == 1:
            nxt_id = consumers[cur][0]
            nxt = node_map[nxt_id]
            if nxt_id in visited or nxt["kind"] != "elementwise":
                break
            # Only fuse if all non-io/graph inputs of nxt are already in this group or not a second unfused compute branch
            group.append(nxt_id)
            visited.add(nxt_id)
            cur = nxt_id
        groups.append(group)
    return groups
""",
            "tests.py": """
def test_matmul_epilogue_fusion(user_mod):
    graph = [
        {"id": "x", "op": "input", "inputs": [], "kind": "io"},
        {"id": "mm", "op": "matmul", "inputs": ["x"], "kind": "compute"},
        {"id": "add", "op": "bias_add", "inputs": ["mm"], "kind": "elementwise"},
        {"id": "gelu", "op": "gelu", "inputs": ["add"], "kind": "elementwise"},
        {"id": "mm2", "op": "matmul", "inputs": ["gelu"], "kind": "compute"},
    ]
    groups = user_mod.fuse_elementwise_chains(graph)
    assert groups == [["x"], ["mm", "add", "gelu"], ["mm2"]]

def test_branching_stops_fusion(user_mod):
    graph = [
        {"id": "mm", "op": "matmul", "inputs": [], "kind": "compute"},
        {"id": "r1", "op": "relu", "inputs": ["mm"], "kind": "elementwise"},
        {"id": "r2", "op": "sigmoid", "inputs": ["mm"], "kind": "elementwise"},
    ]
    groups = user_mod.fuse_elementwise_chains(graph)
    # mm has fan-out 2 -> cannot fuse exclusively into r1 or r2
    assert groups == [["mm"], ["r1"], ["r2"]]
""",
        },
    )

    write_files(
        ITEMS / "problems" / "mlp-manual-backprop",
        {
            "meta.yaml": """
id: mlp-manual-backprop
kind: problem
unit_id: linear-algebra-gemm
title: "2-Layer MLP Forward & Manual Analytical Backprop"
difficulty: medium
xp: 45
estimated_minutes: 20
tags: ["backprop", "deep-learning", "calculus", "linear-algebra"]
order: 2
""",
            "prompt.md": """
# 2-Layer MLP Forward & Manual Backpropagation

Given `X: (N, D_in)`, `W1: (D_in, H)`, `b1: (H,)`, `W2: (H, D_out)`, `b2: (D_out,)`, and target `Y: (N, D_out)`:
- Forward: `Z1 = X @ W1 + b1`, `A1 = ReLU(Z1)`, `Y_hat = A1 @ W2 + b2`
- Loss: Mean Squared Error $L = \\frac{1}{N \\cdot D_{\\text{out}}} \\sum (\\hat{Y} - Y)^2$.

Implement `mlp_forward_backward(X, W1, b1, W2, b2, Y)` returning `(loss, grads)` where `grads` is a dict with keys `"W1", "b1", "W2", "b2"`.
""",
            "theory.md": """
## Analytical Matrix Gradients

With $d\\hat{Y} = \\frac{2}{N D_{\\text{out}}} (\\hat{Y} - Y)$:
- $dW_2 = A_1^\\top d\\hat{Y}$, $db_2 = \\sum_n d\\hat{Y}_n$
- $dA_1 = d\\hat{Y} W_2^\\top$, $dZ_1 = dA_1 \\odot \\mathbb{1}[Z_1 > 0]$
- $dW_1 = X^\\top dZ_1$, $db_1 = \\sum_n dZ_{1,n}$
""",
            "starter.py": """
import numpy as np

def mlp_forward_backward(X, W1, b1, W2, b2, Y):
    raise NotImplementedError
""",
            "reference.py": """
import numpy as np

def mlp_forward_backward(X, W1, b1, W2, b2, Y):
    Z1 = X @ W1 + b1
    A1 = np.maximum(0.0, Z1)
    Y_hat = A1 @ W2 + b2
    diff = Y_hat - Y
    loss = float(np.mean(diff ** 2))

    dY = (2.0 / diff.size) * diff
    dW2 = A1.T @ dY
    db2 = np.sum(dY, axis=0)
    dA1 = dY @ W2.T
    dZ1 = dA1 * (Z1 > 0)
    dW1 = X.T @ dZ1
    db1 = np.sum(dZ1, axis=0)
    return loss, {"W1": dW1, "b1": db1, "W2": dW2, "b2": db2}
""",
            "tests.py": """
import numpy as np

def test_gradients_match_finite_diff(user_mod):
    rng = np.random.default_rng(21)
    X = rng.standard_normal((5, 4))
    W1 = rng.standard_normal((4, 6)) * 0.5
    b1 = rng.standard_normal(6) * 0.1
    W2 = rng.standard_normal((6, 3)) * 0.5
    b2 = rng.standard_normal(3) * 0.1
    Y = rng.standard_normal((5, 3))

    loss, grads = user_mod.mlp_forward_backward(X, W1, b1, W2, b2, Y)
    assert np.isfinite(loss)
    eps = 1e-6
    for name, arr in [("W1", W1), ("b1", b1), ("W2", W2), ("b2", b2)]:
        num = np.zeros_like(arr)
        it = np.nditer(arr, flags=["multi_index"])
        while not it.finished:
            idx = it.multi_index
            orig = arr[idx]
            arr[idx] = orig + eps
            lp, _ = user_mod.mlp_forward_backward(X, W1, b1, W2, b2, Y)
            arr[idx] = orig - eps
            lm, _ = user_mod.mlp_forward_backward(X, W1, b1, W2, b2, Y)
            arr[idx] = orig
            num[idx] = (lp - lm) / (2 * eps)
            it.iternext()
        np.testing.assert_allclose(grads[name], num, rtol=1e-4, atol=1e-5)
""",
        },
    )


def seed_private_templates():
    write_files(
        PRIVATE,
        {
            "cv.md": """
# Candidate CV (Edit with your real CV — stays 100% local in private/)

## Summary
Senior ML Systems & Inference Engineer focusing on high-throughput LLM serving, KV-cache memory optimization, quantized inference, and post-training pipelines.

## Core Skills
Python, PyTorch, NumPy, CUDA/Triton concepts, vLLM / PagedAttention, Continuous Batching, Speculative Decoding, INT8/FP8 Quantization, Transformers, RoPE, RLHF/DPO/GRPO, Distributed Training (FSDP/DDP), MLOps Drift Monitoring.

## Key Projects
### 1. High-Throughput Paged KV-Cache Serving Engine
- Designed an iteration-level continuous batching scheduler with Copy-on-Write prefix caching for 70B models.
- Reduced HBM KV fragmentation from 62% to <8% and improved p99 TTFT by 2.4x under bursty traffic.
- Integrated per-channel INT8 weight quantization and speculative decoding with a 7B draft model.

### 2. GRPO Reasoning Post-Training Pipeline
- Built distributed rollout + group-advantage reward normalization pipeline for code-verifiable math reasoning tasks.
- Implemented KL-regularized policy updates and automated eval contamination checks.
""",
            "star_stories.md": """
# Private STAR Story Bank (Staff-Scope Calibration)

## Story 1: Resolving Cross-Team Serving Latency vs. Accuracy Trade-Off
- **Situation:** Product team wanted 32k context enabled globally; infra HBM budget was saturated at 8k.
- **Task:** Ship 32k context within 3 weeks without increasing GPU fleet cost by >15%.
- **Action:** Authored an RFC comparing FP8 KV quantization, prefix caching, and chunked prefill; aligned Modeling and Infra teams on an automated eval gate (<=0.3% drop on needle-in-a-haystack) before rollout.
- **Result:** Shipped chunked prefill + prefix caching with 11% fleet overhead and zero regression on safety/quality evals.

## Story 2: Leading Production Outage Post-Mortem (Silent OOM / Drift)
- **Situation:** Nightly batch inference silently degraded quality after an upstream tokenizer update.
- **Task:** Restore SLA and prevent silent regressions permanently.
- **Action:** Root-caused input distribution shift via PSI monitoring, introduced deterministic canary golden tests in CI, and instituted blameless post-mortem reviews across 3 teams.
- **Result:** Cut mean-time-to-detect from 18 hours to 4 minutes.
""",
            "dossiers/paged_inference_engine.md": """
# Project War-Room Dossier: High-Throughput Paged KV-Cache Serving Engine

- **Architecture:** Decoupled Scheduler + Physical BlockManager (16-token pages) + Prefill/Decode chunked workers.
- **Key Numbers:** 8x H100 80GB (TP=8), Llama-3 70B, BF16 weights (~140GB total), ~360GB remaining for KV cache. Block size = 16 tokens.
- **Rejected Alternatives:**
  - Block size 64: wasted too much tail memory on short 100-token chat turns.
  - Block size 4: inflated block table metadata lookups and hurt FlashDecoding memory coalescing.
- **Scaling Bottlenecks Hit:**
  - Head-of-line blocking when a 32k prefill stalled active decode batches → fixed with chunked prefill (512-token chunks).
  - Preemption thrashing under burst traffic → added watermark reservation (10% free blocks) + swap/recompute policy.
""",
            "jds/openai_inference.md": """
# OpenAI — Inference Research Engineer
target_date: 2026-12-20
company: OpenAI
role_title: Inference Research Engineer
seniority: Staff

## Requirements
- Deep mastery of LLM inference architecture: KV-cache sizing, Roofline modeling, arithmetic intensity, prefill vs. decode bottlenecks.
- Hands-on implementation of Causal Multi-Head Attention, RoPE, FlashAttention online softmax, PagedAttention block allocators, and continuous batching schedulers.
- Experience with speculative decoding (exact rejection sampling), INT8/FP8 quantization, and post-training reasoning models (GRPO / RLHF).
- Ability to defend production serving trade-offs at Staff level and align cross-functional research and systems teams.
""",
            "jds/anthropic_systems.md": """
# Anthropic — ML Systems & Safety Infrastructure Engineer
target_date: 2027-01-15
company: Anthropic
role_title: ML Systems & Safety Infra Engineer
seniority: Senior/Staff

## Requirements
- Strong foundations in distributed ML systems, continuous batching, KV-cache memory management, and deterministic eval harnesses.
- Experience with AI safety & mechanistic interpretability tooling (linear probes, causal concept erasure/ablation) and production monitoring (PSI drift detection).
- Solid understanding of post-training alignment (DPO, RLHF, GRPO) and Transformer internals (causal attention, manual backprop).
- Proven track record leading ambiguous cross-team technical projects and high-reliability incident post-mortems.
""",
            "jds/google_ml_compiler.md": """
# Google — ML Compiler & Kernel Engineer
target_date: 2027-02-01
company: Google
role_title: ML Compiler & Kernel Engineer
seniority: Staff

## Requirements
- Deep expertise in linear algebra & blocked/tiled GEMM, cache locality, Roofline modeling, and GPU kernel optimization.
- Experience designing SSA graph compiler passes (pointwise operator & matmul epilogue fusion, memory planning, layout optimization).
- Strong understanding of quantization (INT8/FP8 per-channel scaling), FlashAttention online softmax tiling, and Transformer execution graphs.
- Staff-level system design, architecture defense, and technical leadership across compiler and hardware teams.
""",
        },
    )


if __name__ == "__main__":
    seed_items()
    seed_private_templates()
    # Count items
    count = sum(1 for p in ITEMS.rglob("meta.yaml"))
    print(f"Seeded {count} deep items in {ITEMS} and starter templates in {PRIVATE}")
