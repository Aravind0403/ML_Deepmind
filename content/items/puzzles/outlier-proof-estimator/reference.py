def typical_value(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return float(s[mid])
    return 0.5 * (s[mid - 1] + s[mid])
