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
