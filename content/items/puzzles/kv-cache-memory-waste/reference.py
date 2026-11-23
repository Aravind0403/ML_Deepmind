import math

def allocated_slots(seq_lens: list[int], max_len: int) -> int:
    block_size = 16
    return sum(max(1, math.ceil(L / block_size)) * block_size for L in seq_lens)
