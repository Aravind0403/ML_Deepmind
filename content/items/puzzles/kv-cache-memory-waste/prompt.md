# Invent a Low-Waste KV-Cache Allocator

An inference engine serves concurrent requests with varying actual lengths `seq_lens: list[int]`, each with a worst-case maximum length `max_len: int`.

Write `allocated_slots(seq_lens: list[int], max_len: int) -> int` returning the **total KV-cache token slots allocated** by your memory scheme.
Your scheme must satisfy two competing realities:
1. **No Overflow:** You must allocate at least `sum(seq_lens)` slots (you can't store more tokens than slots).
2. **Page-Aligned Efficiency:** Real GPU kernels cannot allocate 1 token at a time (huge pointer overhead), so your allocator must reserve in fixed-size chunks (blocks of size 16 or 32) — **yet** when 64 requests have short actual lengths (30–200 tokens) under `max_len=4096`, your waste ratio `(allocated - used) / allocated` must stay **below 20%** (naive contiguous pre-allocation wastes > 95%!).
3. **Single-Token Boundary:** Even a 1-token sequence must allocate at least 1 block (≥ 16 slots), proving you aren't cheating with block_size=1.
