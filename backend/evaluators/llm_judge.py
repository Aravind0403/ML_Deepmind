"""Provider-agnostic Staff Bar-Raiser LLM Judge (Anthropic/OpenAI/Gemini + offline rubric fallback)."""
from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

BAR_RAISER_SYSTEM_PROMPT = """You are a calibrated Staff/Principal ML Engineering & Research Bar-Raiser interviewer.
CRITICAL CALIBRATION RULE (ANTI-SYCOPHANCY):
- Do NOT flatter the candidate or inflate scores.
- A vague or textbook-level answer without quantitative numbers, memory/FLOP math, failure modes, or concrete trade-offs MUST score <= 65%.
- Only award >= 85% when the candidate demonstrates Staff-level depth: explicit trade-offs, hardware/scaling bottlenecks, edge cases, and concrete systems/research precision.
- Classify any shortcomings into the 5-bucket Failure Taxonomy:
  ["conceptual_gap", "implementation_friction", "complexity_bottleneck_blindness", "communication_structuring", "time_pressure_collapse"].
Respond ONLY with strict valid JSON matching the requested schema."""


def _detect_provider() -> tuple[str, str]:
    pref = os.environ.get("LLM_PROVIDER", "auto").strip().lower()
    keys = {
        "anthropic": os.environ.get("ANTHROPIC_API_KEY", "").strip(),
        "openai": os.environ.get("OPENAI_API_KEY", "").strip(),
        "gemini": os.environ.get("GEMINI_API_KEY", "").strip(),
    }
    if pref == "offline":
        return "offline", ""
    if pref in keys and keys[pref]:
        return pref, keys[pref]
    for p in ("anthropic", "openai", "gemini"):
        if keys[p]:
            return p, keys[p]
    return "offline", ""


def _call_llm_json(prompt: str) -> dict[str, Any] | None:
    provider, api_key = _detect_provider()
    if provider == "offline" or not api_key:
        return None
    try:
        with httpx.Client(timeout=25.0) as client:
            if provider == "anthropic":
                resp = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-3-5-sonnet-latest",
                        "max_tokens": 1200,
                        "system": BAR_RAISER_SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                resp.raise_for_status()
                text = resp.json()["content"][0]["text"]
            elif provider == "openai":
                resp = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": BAR_RAISER_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt},
                        ],
                    },
                )
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"]
            else:  # gemini
                resp = client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "system_instruction": {"parts": [{"text": BAR_RAISER_SYSTEM_PROMPT}]},
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"responseMimeType": "application/json"},
                    },
                )
                resp.raise_for_status()
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]

        # Extract JSON block safely
        m = re.search(r"\{.*\}", text, flags=re.S)
        return json.loads(m.group(0)) if m else json.loads(text)
    except Exception:
        return None


def judge_open_response(
    stage_label: str,
    question: str,
    answer: str,
    rubric_keywords: list[str],
    context_notes: str = "",
    time_overrun: bool = False,
    pass_threshold: float = 75.0,
) -> dict[str, Any]:
    """Grade an open-ended System Design, Deep Knowledge, Project Deep-Dive, or Behavioral response."""
    answer_clean = (answer or "").strip()
    if len(answer_clean) < 25:
        return {
            "score": 20.0,
            "passed": False,
            "provider": "deterministic-guard",
            "rubric": {
                "technical_depth": 1,
                "tradeoff_rigor": 0,
                "quantitative_precision": 0,
                "clarity_structure": 1,
            },
            "strengths": [],
            "vulnerabilities": [f"{stage_label}: Answer too brief ({len(answer_clean)} chars) to demonstrate Senior/Staff depth."],
            "failure_buckets": ["communication_structuring", "conceptual_gap"],
            "feedback": "Expand with concrete mechanisms, quantitative estimates, bottlenecks, and trade-offs.",
            "follow_up_probe": "Walk through the exact failure mode under 10x load and quantify the memory/latency bottleneck.",
        }

    # Try live LLM judge first if API key is set
    llm_prompt = f"""Evaluate this candidate response for {stage_label}.
Question: {question}
Context / Target JD / Dossier: {context_notes[:1800]}
Key expected technical/leadership anchors: {rubric_keywords}
Time overrun: {time_overrun}

Candidate Response:
{answer_clean}

Return STRICT JSON:
{{
  "score": <float 0-100>,
  "rubric": {{
    "technical_depth": <0-4>,
    "tradeoff_rigor": <0-4>,
    "quantitative_precision": <0-4>,
    "clarity_structure": <0-4>
  }},
  "strengths": [<1-3 concise bullets>],
  "vulnerabilities": [<1-3 specific, critical gaps>],
  "failure_buckets": [<subset of conceptual_gap, implementation_friction, complexity_bottleneck_blindness, communication_structuring, time_pressure_collapse>],
  "feedback": "<2-3 sentence calibrated bar-raiser critique>",
  "follow_up_probe": "<1 sharp Staff-level adversarial follow-up question>"
}}"""
    llm_out = _call_llm_json(llm_prompt)
    if llm_out and isinstance(llm_out.get("score"), (int, float)):
        score = float(max(0.0, min(100.0, llm_out["score"])))
        if time_overrun:
            score = max(0.0, score - 8.0)
            buckets = list(set(llm_out.get("failure_buckets", []) + ["time_pressure_collapse"]))
            llm_out["failure_buckets"] = buckets
        llm_out["score"] = round(score, 1)
        llm_out["passed"] = score >= pass_threshold
        llm_out["provider"] = _detect_provider()[0]
        return llm_out

    # Calibrated Offline Deterministic Rubric Fallback (so MVP works out-of-the-box with 0 API keys)
    low = answer_clean.lower()
    matched = [kw for kw in rubric_keywords if kw.lower() in low]
    missed = [kw for kw in rubric_keywords if kw.lower() not in low]
    cov_ratio = len(matched) / max(len(rubric_keywords), 1)

    has_quant = bool(re.search(r"\b\d+(\.\d+)?\s*(gb|mb|tb|ms|s|x|%|flops|tflops|bytes|tokens|k|m|b|o\()", low))
    has_tradeoff = any(w in low for w in ["trade-off", "tradeoff", "however", "vs", "versus", "alternative", "bottleneck", "instead of", "downside", "risk"])
    has_structure = ("\n" in answer_clean) or (len(answer_clean.split()) >= 55)

    tech_depth = min(4, int(round(cov_ratio * 4)))
    tradeoff_rigor = 3 if has_tradeoff else 1
    if has_tradeoff and len(matched) >= 3:
        tradeoff_rigor = 4
    quant_score = 4 if has_quant else 1
    clarity = 4 if (has_structure and len(answer_clean.split()) >= 45) else 2

    raw_score = (tech_depth * 0.40 + tradeoff_rigor * 0.25 + quant_score * 0.20 + clarity * 0.15) * 25.0
    if time_overrun:
        raw_score = max(0.0, raw_score - 10.0)
    score = round(min(96.0, raw_score), 1)

    failure_buckets: list[str] = []
    vulnerabilities: list[str] = []
    strengths: list[str] = []

    if matched:
        strengths.append(f"Anchored response on key concepts: {', '.join(matched[:4])}.")
    if has_quant:
        strengths.append("Included quantitative numbers/metrics to ground claims.")
    if has_tradeoff:
        strengths.append("Explicitly articulated architectural trade-offs and alternatives.")

    if cov_ratio < 0.5:
        failure_buckets.append("conceptual_gap")
        vulnerabilities.append(f"Missed critical expected concepts: {', '.join(missed[:4])}.")
    if not has_quant:
        failure_buckets.append("complexity_bottleneck_blindness")
        vulnerabilities.append("Lacked quantitative back-of-the-envelope numbers (latency, HBM GB, FLOP/byte, or complexity bounds).")
    if not has_tradeoff:
        failure_buckets.append("communication_structuring")
        vulnerabilities.append("Did not clearly contrast rejected alternatives or failure modes under scale.")
    if time_overrun:
        failure_buckets.append("time_pressure_collapse")
        vulnerabilities.append("Exceeded dynamic time budget during Stage execution.")

    probe_topic = missed[0] if missed else (matched[0] if matched else "scaling bottleneck")
    return {
        "score": score,
        "passed": score >= pass_threshold,
        "provider": "offline-rubric",
        "rubric": {
            "technical_depth": tech_depth,
            "tradeoff_rigor": tradeoff_rigor,
            "quantitative_precision": quant_score,
            "clarity_structure": clarity,
        },
        "strengths": strengths,
        "vulnerabilities": vulnerabilities,
        "failure_buckets": failure_buckets,
        "feedback": (
            f"Calibrated Offline Rubric ({score:.1f}%): Covered {len(matched)}/{len(rubric_keywords)} expected Staff anchors. "
            + ("Strong quantitative & trade-off rigor." if score >= pass_threshold else "To pass the Staff bar, quantify bottlenecks explicitly and address missed concepts.")
        ),
        "follow_up_probe": f"Now assume traffic spikes 10x and HBM budget is halved — how does your design handle `{probe_topic}` without violating p99 latency?",
    }
