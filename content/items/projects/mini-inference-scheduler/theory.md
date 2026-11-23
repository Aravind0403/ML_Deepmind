## Why Continuous (Iteration-Level) Batching 10x's Throughput

Static batching forces short sequences to sit idle until the longest sequence finishes (GPU bubble). Iteration-level scheduling (Orca / vLLM) frees finished KV blocks on the exact step an EOS occurs and immediately slots waiting prefills into the active batch.
