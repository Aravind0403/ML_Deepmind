import math

class BlockManager:
    def __init__(self, num_blocks: int, block_size: int):
        self.num_blocks = num_blocks
        self.block_size = block_size
        self.free_blocks = list(range(num_blocks - 1, -1, -1))
        self.ref_counts = [0] * num_blocks
        self.block_tables: dict[str, list[int]] = {}
        self.seq_lens: dict[str, int] = {}

    def num_free_blocks(self) -> int:
        return len(self.free_blocks)

    def _alloc_one(self) -> int:
        if not self.free_blocks:
            raise MemoryError("Out of KV-cache physical blocks")
        bid = self.free_blocks.pop()
        self.ref_counts[bid] = 1
        return bid

    def allocate_seq(self, seq_id: str, num_tokens: int) -> list[int]:
        needed = max(1, math.ceil(num_tokens / self.block_size)) if num_tokens > 0 else 0
        if needed > len(self.free_blocks):
            raise MemoryError("Out of KV-cache physical blocks")
        blocks = [self._alloc_one() for _ in range(needed)]
        self.block_tables[seq_id] = blocks
        self.seq_lens[seq_id] = num_tokens
        return list(blocks)

    def fork_seq(self, src_seq_id: str, dst_seq_id: str) -> None:
        src_blocks = self.block_tables[src_seq_id]
        for bid in src_blocks:
            self.ref_counts[bid] += 1
        self.block_tables[dst_seq_id] = list(src_blocks)
        self.seq_lens[dst_seq_id] = self.seq_lens[src_seq_id]

    def append_token(self, seq_id: str) -> int:
        cur_len = self.seq_lens[seq_id]
        table = self.block_tables[seq_id]
        if cur_len % self.block_size == 0:
            new_bid = self._alloc_one()
            table.append(new_bid)
            self.seq_lens[seq_id] = cur_len + 1
            return new_bid
        last_bid = table[-1]
        if self.ref_counts[last_bid] > 1:
            new_bid = self._alloc_one()
            self.ref_counts[last_bid] -= 1
            table[-1] = new_bid
            self.seq_lens[seq_id] = cur_len + 1
            return new_bid
        self.seq_lens[seq_id] = cur_len + 1
        return last_bid

    def free_seq(self, seq_id: str) -> None:
        table = self.block_tables.pop(seq_id)
        self.seq_lens.pop(seq_id)
        for bid in table:
            self.ref_counts[bid] -= 1
            if self.ref_counts[bid] == 0:
                self.free_blocks.append(bid)
