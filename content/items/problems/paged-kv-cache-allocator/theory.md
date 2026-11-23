## Why Copy-on-Write Matters in Beam Search & Prefix Caching

In vLLM, shared system prompts and parallel beam search branches point their logical block tables to the **same physical KV blocks** (`ref_count > 1`). Only when a branch mutates a partially filled tail block does CoW allocate a private copy — saving up to 55% of KV HBM during parallel sampling.
