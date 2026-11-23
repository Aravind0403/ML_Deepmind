"""Author-Your-Own Active Recall Flashcards Engine pre-indexed with Silvia Sapora's 115+ Frontier-Lab Checklist."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
import sqlite3
from typing import Any

from backend.engines.fsrs import compute_retrievability

FRONTIER_TOPIC_CHECKLIST: dict[str, list[str]] = {
    "Reinforcement Learning": [
        "Q-Learning / TD Learning",
        "Bellman Equations",
        "PPO (Proximal Policy Optimization)",
        "GRPO (Group Relative Policy Optimization)",
        "GAE (Generalized Advantage Estimation)",
        "Variance Reduction in RL",
        "DPO (Direct Preference Optimization)",
        "Policy Gradient Theorem",
        "On-Policy vs Off-Policy",
        "Exploration vs Exploitation Dilemma",
        "Credit Assignment Problem",
        "MuZero",
        "World Models / Dreamer",
        "AlphaGo (MCTS + Value/Policy)",
        "Soft Actor-Critic (SAC)",
        "Model-Based vs Model-Free RL",
        "Markov Property & MDP",
        "Monte Carlo vs Temporal Difference",
        "Actor-Critic Methods",
        "SARSA",
        "Importance Sampling",
        "Curriculum Learning",
    ],
    "LLMs": [
        "FlashAttention (Online Softmax & IO-Awareness)",
        "LoRA & QLoRA",
        "TransformerXL (Segment Recurrence)",
        "Griffin (Gated Linear Recurrences + Local Attention)",
        "Perceiver (Cross-Attention Latent Bottleneck)",
        "Chinchilla & Kaplan Scaling Laws",
        "Mixture of Experts (MoE & Load Balancing)",
        "Attention Scaling Factor (1/sqrt(d_k))",
        "RoPE (Rotary Position Embeddings)",
        "Sinusoidal Positional Embeddings",
        "Relative Positional Embeddings (ALiBi / T5)",
        "LLM vs RNN vs S4 / Mamba",
        "Tokenization (BPE / Unigram / WordPiece)",
        "Pretraining Dynamics & Data Mixtures",
        "Supervised Fine-Tuning (SFT)",
        "RLHF & Reward Hacking",
        "Decoding Techniques (Top-k, Top-p, Beam, Speculative)",
        "Causal Attention vs Bidirectional Attention",
        "Cross-Attention",
        "PagedAttention & KV-Cache Prefix Sharing",
    ],
    "Generative Modelling": [
        "GANs (Minimax Objective & Mode Collapse)",
        "VAEs & VAE ELBO Derivation",
        "Score Function & Score Matching",
        "Diffusion Forward Process (q(x_t|x_0))",
        "Diffusion Reverse Process (DDPM vs DDIM)",
        "Diffusion Forward / Reverse SDE",
        "Flow Matching ODE & Optimal Transport Paths",
        "Classifier-Free Guidance (CFG)",
    ],
    "Applied ML": [
        "Tensor Parallelism (TP — Megatron Column/Row Split)",
        "FSDP / ZeRO Stages 1, 2, 3",
        "Distributed Data Parallel (DDP & All-Reduce)",
        "Pipeline Parallelism (GPipe / 1F1B Bubbles)",
        "Collective Communication Primitives (AllReduce, AllGather, ReduceScatter)",
        "Mixed Precision Training (BF16 vs FP16 Loss Scaling)",
        "Gradient Checkpointing (Activation Recomputation)",
        "Gradient Accumulation",
        "GPU Profiling (nsys, ncu, Roofline & Kernel Launch Overhead)",
        "Gradient Clipping (Norm vs Value)",
        "Numerical Precision Tricks (LogSumExp, FP32 Softmax)",
        "Exploding & Vanishing Gradients",
        "Floating Point Representation (FP32, BF16, FP16, FP8 E4M3/E5M2)",
        "JIT Compiling (torch.compile / Inductor / XLA)",
        "JAX vs PyTorch Execution Models (Functional vs Eager)",
    ],
    "General ML": [
        "Curse of Dimensionality",
        "S4 (Structured State Space Sequence Models)",
        "CNNs & Receptive Fields",
        "RNNs / LSTMs & Gating",
        "Autoencoders & Bottleneck Regularization",
        "Gumbel-Softmax Reparameterization",
        "MLE vs MAP Estimation",
        "Newton's Method & Second-Order Optimization",
        "Linear Regression & Normal Equations",
        "Activation Functions (ReLU, GELU, SwiGLU)",
        "Loss Functions (MSE, Cross-Entropy, Huber, Focal)",
        "No Free Lunch Theorem",
        "BatchNorm vs LayerNorm vs RMSNorm",
        "Variance and Covariance",
        "Adam vs AdamW vs Adagrad",
        "Bias-Variance Tradeoff",
        "Backpropagation & Reverse-Mode Autodiff",
        "Regularization Methods (L1, L2, Dropout, Weight Decay)",
        "Unsupervised vs Supervised Learning",
        "Clustering Algorithms (k-Means, GMM, DBSCAN)",
        "K-Nearest Neighbours",
        "SVMs & Kernel Trick",
        "Boosting (XGBoost / Gradient Boosting)",
        "Bagging & Random Forests",
        "Decision Trees (Gini vs Entropy Split)",
        "Bayes Theorem",
        "Precision / Recall / F1 / AUC-ROC / PR-AUC",
        "KL Divergence (Forward vs Reverse KL)",
        "Jensen-Shannon Divergence",
        "Weight Initialization (Xavier / He / Residual Scaling)",
        "Gradient Descent / SGD / Momentum",
        "Overfitting vs Underfitting",
        "Cross-Validation & Data Leakage",
        "Data Whitening & Standardization",
        "Convex Functions & Global Optima",
        "Early Stopping",
        "Domain Adaptation & Distribution Shift",
        "Dimensionality Reduction (PCA, t-SNE, UMAP)",
        "Transfer Learning",
        "Few-Shot vs Zero-Shot Learning",
        "Expectation & Linearity of Expectation",
        "Shannon Entropy & Cross-Entropy",
        "PDF vs PMF",
        "Confidence Intervals & Bootstrap",
    ],
    "Linear Algebra": [
        "Positive Semi-Definite (PSD) Matrices",
        "Jacobian Matrix",
        "Eigenvectors & Eigenvalues",
        "Hessian Matrix & Curvature",
        "Matrix Inverse & Moore-Penrose Pseudoinverse",
        "Dot Product & Cosine Similarity",
        "Null Space & Column/Image Space (Rank-Nullity)",
        "Orthogonality & Orthonormal Projections",
        "Linear Independence",
        "Singular Matrices & Conditioning",
        "Rank & Span",
        "Determinant (Geometric Volume Meaning)",
        "Singular Value Decomposition (SVD)",
    ],
}


def _slug(cat: str, topic: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", f"{cat}-{topic}".lower()).strip("-")
    return s[:64]


def seed_frontier_flashcards(conn: sqlite3.Connection) -> int:
    """Seed blank author-your-own cards for all 115+ checklist topics (never overwrites user-authored backs)."""
    inserted = 0
    for cat, topics in FRONTIER_TOPIC_CHECKLIST.items():
        for topic in topics:
            cid = _slug(cat, topic)
            front = f"Explain '{topic}' from first principles: core equation/mechanism, failure mode/edge case, and when it matters in production or research."
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO flashcards (id, category, topic, front_prompt, user_back_markdown, authored)
                VALUES (?, ?, ?, ?, '', 0)
                """,
                (cid, cat, topic, front),
            )
            if cur.rowcount > 0:
                inserted += 1
    conn.commit()
    return inserted


def list_flashcards(conn: sqlite3.Connection, category: str | None = None, only_authored: bool = False) -> dict[str, Any]:
    seed_frontier_flashcards(conn)
    sql = "SELECT * FROM flashcards WHERE 1=1"
    params: list[Any] = []
    if category and category != "All":
        sql += " AND category = ?"
        params.append(category)
    if only_authored:
        sql += " AND authored = 1"
    sql += " ORDER BY category, topic"

    rows = conn.execute(sql, params).fetchall()
    cards = []
    authored_count = 0
    due_count = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for r in rows:
        is_auth = bool(r["authored"])
        if is_auth:
            authored_count += 1
        ret = compute_retrievability(r["last_review_at"], r["stability"]) if r["last_review_at"] else 0.0
        is_due = is_auth and (not r["due_at"] or r["due_at"] <= now_iso)
        if is_due:
            due_count += 1
        cards.append(
            {
                "id": r["id"],
                "category": r["category"],
                "topic": r["topic"],
                "front_prompt": r["front_prompt"],
                "user_back_markdown": r["user_back_markdown"],
                "authored": is_auth,
                "stability_days": r["stability"],
                "difficulty": r["difficulty"],
                "reps": r["reps"],
                "lapses": r["lapses"],
                "retrievability_pct": round(ret * 100.0, 1),
                "is_due": is_due,
                "due_at": r["due_at"],
            }
        )

    return {
        "total": len(cards),
        "authored": authored_count,
        "due": due_count,
        "categories": list(FRONTIER_TOPIC_CHECKLIST.keys()),
        "cards": cards,
    }


def review_flashcard(conn: sqlite3.Connection, card_id: str, rating: str) -> dict[str, Any]:
    """Apply FSRS stability/difficulty update for rating in ('again', 'hard', 'good', 'easy')."""
    row = conn.execute("SELECT * FROM flashcards WHERE id = ?", (card_id,)).fetchone()
    if not row:
        raise ValueError(f"Flashcard '{card_id}' not found")

    now = datetime.now(timezone.utc)
    stability = float(row["stability"])
    difficulty = float(row["difficulty"])
    reps = int(row["reps"])
    lapses = int(row["lapses"])

    r = compute_retrievability(row["last_review_at"], stability) if row["last_review_at"] else 0.5
    rating = rating.lower()
    if rating == "again":
        lapses += 1
        stability = max(0.5, stability * 0.4)
        difficulty = min(10.0, difficulty + 1.0)
    elif rating == "hard":
        reps += 1
        stability = max(1.0, stability * 1.2)
        difficulty = min(10.0, difficulty + 0.3)
    elif rating == "easy":
        reps += 1
        stability = min(180.0, stability * (2.2 + 0.4 * (1.0 - r)))
        difficulty = max(1.0, difficulty - 0.6)
    else:  # good
        reps += 1
        stability = min(180.0, stability * (1.6 + 0.4 * (1.0 - r)))
        difficulty = max(1.0, difficulty - 0.15)

    due_at = (now + timedelta(days=stability)).isoformat()
    conn.execute(
        """
        UPDATE flashcards
        SET stability = ?, difficulty = ?, reps = ?, lapses = ?, last_review_at = ?, due_at = ?
        WHERE id = ?
        """,
        (round(stability, 2), round(difficulty, 2), reps, lapses, now.isoformat(), due_at, card_id),
    )
    conn.commit()
    return {
        "id": card_id,
        "rating": rating,
        "stability_days": round(stability, 2),
        "difficulty": round(difficulty, 2),
        "due_at": due_at,
    }
