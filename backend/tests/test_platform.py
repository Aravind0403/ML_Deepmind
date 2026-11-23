"""End-to-end backend tests covering sandboxing, all 5 pillars, strict Stage 1-4 gating, and Readiness veto gates."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from backend.evaluators.runners import evaluate_code_problem, evaluate_math_drills
from backend.evaluators.sandbox import run_sandboxed_script
from backend.main import app

client = TestClient(app)


def test_sandbox_kills_infinite_loop_and_blocks_unsafe_imports():
    # Infinite loop must time out cleanly without crashing FastAPI
    res = run_sandboxed_script(
        "while True:\n    pass\n",
        "import sys; sys.path.insert(0, '.'); import user_solution\n",
        timeout_sec=1,
    )
    assert not res.ok
    assert res.timed_out

    # Dangerous import blocked statically by AST guard
    res2 = run_sandboxed_script("import os\nos.system('echo hi')\n", "import user_solution\n", timeout_sec=2)
    assert not res2.ok
    assert res2.violation and "os" in res2.violation

    # Problem-specific banned operator (@) blocked statically
    res3 = evaluate_code_problem("def tiled_gemm(A, B, tile_size=16): return A @ B\n", "def test_x(u): pass", ban_matmul_op=True)
    assert not res3["passed"]
    assert "banned" in (res3.get("stderr") or "").lower()


def test_sympy_symbolic_equivalence():
    drills = [{"id": "d1", "mode": "symbolic", "symbols": ["p"], "expected": "p * (1 - p)"}]
    # Algebraically equivalent expanded form must pass!
    out = evaluate_math_drills(drills, {"d1": "p - p**2"})
    assert out["passed"]
    out_bad = evaluate_math_drills(drills, {"d1": "p + 1"})
    assert not out_bad["passed"]


def test_overview_and_syllabus_endpoints():
    ov = client.get("/api/overview")
    assert ov.status_code == 200
    data = ov.json()
    assert len(data["tracks"]) == 5
    assert len(data["pipelines"]) >= 3

    syl = client.get("/api/syllabus?daily_budget_min=45")
    assert syl.status_code == 200
    assert len(syl.json()["daily_timebox"]["items"]) >= 1


def test_strict_4_stage_gating_and_readiness_unlock():
    # Create a dedicated temporary target role so test is isolated
    t_resp = client.post(
        "/api/targets",
        json={
            "company": "TestLab",
            "role_title": "Inference Staff",
            "seniority": "Staff",
            "target_date": "2026-12-30",
            "jd_markdown": "Requires KV-cache sizing, Roofline arithmetic intensity, PagedAttention, and quantization.",
        },
    )
    assert t_resp.status_code == 200
    tid = t_resp.json()["id"]

    try:
        # Readiness MUST be locked initially
        r_locked = client.get(f"/api/readiness/{tid}").json()
        assert r_locked["unlocked"] is False

        # Start Interview Studio session
        s_resp = client.post("/api/studio/sessions", json={"target_id": tid})
        assert s_resp.status_code == 200
        sess = s_resp.json()
        sid = sess["id"]

        # Attempting Stage 2 while Stage 1 is incomplete MUST fail with 403
        s2_blocked = client.post(
            f"/api/studio/sessions/{sid}/stage2",
            json={
                "coding_code": "pass",
                "coding_duration_sec": 100,
                "system_design_answer": "test",
                "constraint_shift_answer": "test",
                "deep_knowledge_answer": "test",
            },
        )
        assert s2_blocked.status_code == 403

        # Pass every Stage 1 item using its verified reference solution
        req_ids = sess["plan"]["stage1"]["track_1a_overlap_ids"] + sess["plan"]["stage1"]["track_1b_gap_ids"]
        for iid in req_ids:
            item_full = client.get(f"/api/items/{iid}").json()
            if item_full["kind"] == "math":
                math_ans = {d["id"]: str(d["expected"]) for d in item_full["drills"]}
                r1 = client.post(f"/api/studio/sessions/{sid}/stage1/{iid}", json={"math_answers": math_ans})
            else:
                r1 = client.post(f"/api/studio/sessions/{sid}/stage1/{iid}", json={"code": item_full["reference_code"]})
            assert r1.status_code == 200
            assert r1.json()["evaluation"]["passed"] is True

        # Stage 2 should now be unlocked; Stage 3 still locked
        s3_blocked = client.post(f"/api/studio/sessions/{sid}/stage3", json={"answers": {}})
        assert s3_blocked.status_code == 403

        # Pass Stage 2
        s2_cid = sess["plan"]["stage2"]["coding_item_id"]
        s2_item = client.get(f"/api/items/{s2_cid}").json()
        strong_sd = (
            "Architecture uses paged KV-cache with 16-token blocks, continuous batching, and chunked prefill on 8x H100 (80GB HBM, 3.35 TB/s bandwidth). "
            "Trade-off vs static batching: reduces HBM fragmentation from 65% to <8% and improves throughput 3x while guarding p99 latency and TTFT. "
            "Arithmetic intensity for decode is memory-bandwidth bound (~2 FLOP/byte vs 295 FLOP/byte ridge point). Under 10x context + 40% less HBM, "
            "KV-cache overflows first, so we combine FP8 KV quantization (2x savings), GQA, and prefix eviction watermark to protect latency."
        )
        strong_dk = (
            "Quantization (INT8/FP8) reduces memory bandwidth overhead during decode, however per-tensor scaling regresses accuracy when activation outliers appear. "
            "Roofline profiling shows speculative decoding regresses latency at large batch sizes when draft verification becomes compute-bound instead of memory-bound; "
            "edge cases in rejection sampling must preserve exact target distribution verified via TV distance <= 0.02."
        )
        s2_ok = client.post(
            f"/api/studio/sessions/{sid}/stage2",
            json={
                "coding_code": s2_item["reference_code"],
                "coding_duration_sec": 300,
                "system_design_answer": strong_sd,
                "constraint_shift_answer": "Under 40% HBM cut we enable FP8 KV quantization, chunked prefill (512 tokens), and preemption watermarks to keep p99 latency under 120ms.",
                "deep_knowledge_answer": strong_dk,
            },
        )
        assert s2_ok.status_code == 200
        assert s2_ok.json()["stage2"]["passed"] is True

        # Pass Stage 3
        s3_ans = {
            q["id"]: (
                "We chose 16-token paged blocks after profiling block size 4 vs 64; block size 64 wasted 32% tail HBM on 100-token chats whereas block size 4 inflated metadata lookup latency by 18%. "
                "Our biggest scaling bottleneck was head-of-line preemption thrashing and OOM at p99 latency under 10x bursts, fixed via 512-token chunked prefill and a 10% free-block watermark."
            )
            for q in sess["plan"]["stage3"]["questions"]
        }
        s3_ok = client.post(f"/api/studio/sessions/{sid}/stage3", json={"answers": s3_ans})
        assert s3_ok.status_code == 200
        assert s3_ok.json()["stage3"]["passed"] is True

        # Pass Stage 4
        s4_ans = {
            q["id"]: (
                "I authored a quantitative RFC comparing FP8 KV quantization vs chunked prefill, aligned 3 teams (Modeling, Infra, Safety) around an objective <=0.3% eval regression metric and 15% fleet cost risk cap, "
                "and owned the root cause post-mortem by adding PSI monitoring and deterministic CI canary tests to prevent silent drift across the org with 95% faster detection impact."
            )
            for q in sess["plan"]["stage4"]["questions"]
        }
        s4_ok = client.post(f"/api/studio/sessions/{sid}/stage4", json={"answers": s4_ans})
        assert s4_ok.status_code == 200
        assert s4_ok.json()["stage4"]["passed"] is True

        # Pillar 4: Prep Recap works cleanly
        recap = client.get(f"/api/recap/{sid}").json()
        assert len(recap["heatmap"]) == 6
        assert "conceptual_gap" in recap["failure_taxonomy"]

        # Pillar 5: Readiness Score is now UNLOCKED with Hiring Committee Memo!
        r_unlocked = client.get(f"/api/readiness/{tid}").json()
        assert r_unlocked["unlocked"] is True
        assert r_unlocked["effective_score"] > 70.0
        assert "Hiring Committee Debrief" in r_unlocked["hc_memo_markdown"]
    finally:
        client.delete(f"/api/targets/{tid}")


def test_phase2_flashcards_notes_stuck_flag_and_crm_burnout():
    # 1. Frontier flashcards seeded (115+ topics) + authoring + FSRS review
    fc = client.get("/api/flashcards").json()
    assert fc["total"] >= 115
    first_id = fc["cards"][0]["id"]
    up = client.put(f"/api/flashcards/{first_id}", json={"user_back_markdown": "My own first-principles summary."})
    assert up.status_code == 200 and up.json()["authored"] is True
    rev = client.post(f"/api/flashcards/{first_id}/review", json={"rating": "good"})
    assert rev.status_code == 200 and rev.json()["stability_days"] > 2.0

    # 2. Predict-Before-Running (Expected / Observed / Why) notes persistence
    n_put = client.put(
        "/api/items/causal-multihead-attention/notes",
        json={"expected_text": "Output shape (B,T,D)", "observed_text": "Matched!", "why_text": "Reshaped heads properly"},
    )
    assert n_put.status_code == 200
    n_get = client.get("/api/items/causal-multihead-attention/notes").json()
    assert n_get["expected_text"] == "Output shape (B,T,D)"

    # 3. 15-Min Stuck Cutoff FSRS Flag
    st = client.post("/api/syllabus/flag-stuck/vllm-prefill-starvation-bug")
    assert st.status_code == 200 and st.json()["fsrs"]["studio_boost"] == 3.0

    # 4. CRM + Burnout Spacing Guardrail (>3 interviews in 7 days triggers warning)
    targets = client.get("/api/targets").json()["targets"]
    tid = targets[0]["id"]
    c_put = client.put(
        f"/api/crm/{tid}",
        json={
            "app_stage": "Tech Loop",
            "referral_contact": "Ex-colleague on Inference team",
            "cold_email_draft": "Excited about your KV-cache serving work...",
            "interview_dates": ["2026-12-01", "2026-12-02", "2026-12-04", "2026-12-05"],
            "offer": {"base": 250000, "equity_annual": 200000, "equity_type": "RSU"},
        },
    )
    assert c_put.status_code == 200
    crm = client.get("/api/crm").json()
    assert crm["burnout_guardrail"]["burnout_warning"] is True
    assert crm["burnout_guardrail"]["peak_interviews_in_7_days"] >= 4
    # Reset interview dates back cleanly
    client.put(f"/api/crm/{tid}", json={"app_stage": "Researching", "interview_dates": [], "offer": {}})

