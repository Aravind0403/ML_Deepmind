## Decode-First Phase Separation + Chunked Prefill

Scheduling running decodes first guarantees bounded TPOT latency even during bursty long-prompt arrivals, while chunked prefill packs leftover GPU compute capacity without head-of-line blocking.
