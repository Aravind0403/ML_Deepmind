# PagedAttention Block Allocator with Copy-on-Write (CoW)

Implement class `BlockManager(num_blocks: int, block_size: int)`:
- `allocate_seq(seq_id: str, num_tokens: int) -> list[int]`: Allocates the minimum number of physical blocks (`ceil(num_tokens / block_size)`) from the free pool. Raises `MemoryError` if insufficient free blocks.
- `fork_seq(src_seq_id: str, dst_seq_id: str) -> None`: **Zero-copy prefix sharing!** `dst_seq_id` shares `src_seq_id`'s physical block IDs and increments each block's reference count (`ref_count`).
- `append_token(seq_id: str) -> int`: Appends 1 token to `seq_id`.
  - If the last logical block is **full** (`len % block_size == 0`), allocate a new physical block.
  - If the last logical block is **not full** AND its `ref_count > 1`, perform **Copy-on-Write**: decrement old block's `ref_count`, allocate a fresh physical block, replace the last block entry for `seq_id`, and return the new physical block ID!
  - Otherwise return the current last physical block ID.
- `free_seq(seq_id: str) -> None`: Decrements `ref_count` on every block held by `seq_id`, returning blocks whose `ref_count == 0` back to the free pool.
- `num_free_blocks() -> int`: Returns number of currently free physical blocks.
