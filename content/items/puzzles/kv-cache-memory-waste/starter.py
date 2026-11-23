def allocated_slots(seq_lens: list[int], max_len: int) -> int:
    # Naive contiguous pre-allocation reserves max_len for every request!
    return len(seq_lens) * max_len
