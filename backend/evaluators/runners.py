"""Evaluators for Coding Problems, Projects, Intuition Puzzles, Labs, and SymPy Math Drills."""
from __future__ import annotations

import json
import math
from typing import Any

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from backend.evaluators.sandbox import run_sandboxed_script

RESULT_MARKER = "__DML_JSON_RESULT__"


def evaluate_code_problem(
    user_code: str,
    tests_code: str,
    banned_apis: list[str] | None = None,
    ban_matmul_op: bool = False,
    timeout_sec: int = 5,
) -> dict[str, Any]:
    """Run pytest-style test_* functions in tests_code against user_solution inside strict sandbox."""
    harness = f"""
import json, sys, traceback
sys.path.insert(0, ".")
import user_solution

{tests_code}

results = []
passed = 0
failed = 0
for name, obj in list(globals().items()):
    if name.startswith("test_") and callable(obj):
        try:
            obj(user_solution)
            results.append({{"name": name, "passed": True, "error": None}})
            passed += 1
        except Exception as e:
            tb = traceback.format_exc(limit=3)
            results.append({{"name": name, "passed": False, "error": f"{{type(e).__name__}}: {{e}}", "traceback": tb}})
            failed += 1

payload = {{"passed_count": passed, "failed_count": failed, "total": passed + failed, "tests": results}}
print("{RESULT_MARKER}" + json.dumps(payload))
sys.exit(0 if failed == 0 and passed > 0 else 1)
"""
    res = run_sandboxed_script(
        user_code=user_code,
        harness_code=harness,
        timeout_sec=timeout_sec,
        banned_apis=banned_apis or [],
        ban_matmul_op=ban_matmul_op,
    )
    return _parse_harness_output(res)


def evaluate_puzzle(
    user_code: str,
    tests_code: str,
    timeout_sec: int = 5,
) -> dict[str, Any]:
    """Run adversarial property counterexamples against user's first defined function."""
    harness = f"""
import inspect, json, sys, traceback
sys.path.insert(0, ".")
import user_solution

{tests_code}

fns = [obj for name, obj in inspect.getmembers(user_solution, inspect.isfunction) if obj.__module__ == "user_solution"]
if not fns:
    payload = {{"passed": False, "counterexamples": [{{"property": "Function Missing", "input": "-", "your_output": "-", "why_broken": "Define a Python function in the editor."}}]}}
    print("{RESULT_MARKER}" + json.dumps(payload))
    sys.exit(1)

try:
    failures = run_counterexamples(fns[0])
    payload = {{"passed": len(failures) == 0, "counterexamples": failures}}
    print("{RESULT_MARKER}" + json.dumps(payload))
    sys.exit(0 if len(failures) == 0 else 1)
except Exception as e:
    payload = {{"passed": False, "counterexamples": [{{"property": "Runtime Exception", "input": "-", "your_output": type(e).__name__, "why_broken": str(e)}}]}}
    print("{RESULT_MARKER}" + json.dumps(payload))
    sys.exit(1)
"""
    res = run_sandboxed_script(user_code=user_code, harness_code=harness, timeout_sec=timeout_sec)
    parsed = _parse_harness_output(res)
    if "counterexamples" not in parsed:
        parsed["counterexamples"] = [
            {
                "property": "Execution Error",
                "input": "-",
                "your_output": "Error",
                "why_broken": parsed.get("stderr") or "Code failed to execute.",
            }
        ]
    return parsed


def evaluate_lab(
    user_code: str,
    tests_code: str,
    timeout_sec: int = 12,
) -> dict[str, Any]:
    """Run real-dataset / simulation metric lab harness inside strict sandbox."""
    harness = f"""
import json, sys, traceback
sys.path.insert(0, ".")
import user_solution

{tests_code}

try:
    out = evaluate_lab(user_solution)
    print("{RESULT_MARKER}" + json.dumps(out))
    sys.exit(0 if out.get("passed") else 1)
except Exception as e:
    out = {{"passed": False, "metric": None, "details": f"{{type(e).__name__}}: {{e}}"}}
    print("{RESULT_MARKER}" + json.dumps(out))
    sys.exit(1)
"""
    res = run_sandboxed_script(
        user_code=user_code,
        harness_code=harness,
        timeout_sec=timeout_sec,
        max_mem_mb=768,
    )
    return _parse_harness_output(res)


def evaluate_math_drills(
    drills: list[dict[str, Any]],
    answers: dict[str, str],
) -> dict[str, Any]:
    """Deterministically grade symbolic (SymPy) and numeric math drills."""
    transforms = standard_transformations + (implicit_multiplication_application,)
    results = []
    passed_count = 0

    for drill in drills:
        did = drill["id"]
        raw = str(answers.get(did, "")).strip()
        mode = drill.get("mode", "numeric")
        if not raw:
            results.append({"id": did, "passed": False, "feedback": "No answer submitted.", "hint": drill.get("hint")})
            continue

        if mode == "numeric":
            try:
                val = float(sp.N(parse_expr(raw.replace("^", "**"), transformations=transforms)))
                exp = float(drill["expected"])
                tol = float(drill.get("tol", 1e-4))
                ok = math.isclose(val, exp, rel_tol=1e-4, abs_tol=tol)
                if ok:
                    passed_count += 1
                results.append(
                    {
                        "id": did,
                        "passed": ok,
                        "feedback": "Exact numerical match!" if ok else f"Evaluated to {val:.4g}, which is outside tolerance of expected target.",
                        "hint": None if ok else drill.get("hint"),
                    }
                )
            except Exception as exc:
                results.append({"id": did, "passed": False, "feedback": f"Could not parse number: {exc}", "hint": drill.get("hint")})
        else:
            # Symbolic equivalence via SymPy
            try:
                sym_names = drill.get("symbols", [])
                local_dict = {s: sp.Symbol(s, positive=True) for s in sym_names}
                user_expr = parse_expr(raw.replace("^", "**"), local_dict=local_dict, transformations=transforms)
                exp_expr = parse_expr(str(drill["expected"]).replace("^", "**"), local_dict=local_dict, transformations=transforms)
                diff = sp.simplify(user_expr - exp_expr)
                ok = diff == 0
                if ok:
                    passed_count += 1
                results.append(
                    {
                        "id": did,
                        "passed": ok,
                        "feedback": "Symbolically equivalent!" if ok else f"Parsed as `{user_expr}` — not algebraically equivalent to expected expression.",
                        "hint": None if ok else drill.get("hint"),
                    }
                )
            except Exception as exc:
                results.append({"id": did, "passed": False, "feedback": f"Could not parse symbolic expression: {exc}", "hint": drill.get("hint")})

    all_passed = passed_count == len(drills) and len(drills) > 0
    return {
        "passed": all_passed,
        "passed_count": passed_count,
        "total": len(drills),
        "score": round(100.0 * passed_count / max(len(drills), 1), 1),
        "results": results,
    }


def _parse_harness_output(res) -> dict[str, Any]:
    stdout = res.stdout or ""
    stderr = res.stderr or ""
    if RESULT_MARKER in stdout:
        prefix, _, rest = stdout.partition(RESULT_MARKER)
        line = rest.splitlines()[0].strip()
        try:
            data = json.loads(line)
            data["stdout"] = prefix.strip()
            data["stderr"] = stderr.strip()
            data["elapsed_ms"] = res.elapsed_ms
            data["timed_out"] = res.timed_out
            if "passed" not in data:
                data["passed"] = bool(res.ok and data.get("failed_count", 1) == 0 and data.get("passed_count", 0) > 0)
            return data
        except Exception:
            pass
    return {
        "passed": False,
        "passed_count": 0,
        "failed_count": 1,
        "total": 1,
        "tests": [],
        "stdout": stdout.strip(),
        "stderr": stderr.strip() or res.violation or "Sandbox execution failed.",
        "elapsed_ms": res.elapsed_ms,
        "timed_out": res.timed_out,
        "violation": res.violation,
    }
