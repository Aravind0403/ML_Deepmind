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
