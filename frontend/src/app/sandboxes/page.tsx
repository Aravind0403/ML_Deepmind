"use client";

import { useMemo, useState } from "react";
import { Cpu, HardDrive, Play, Plus, RotateCcw, BookMarked, ExternalLink, Layers } from "lucide-react";

const GPU_SPECS: Record<string, { name: string; fp16Tflops: number; bwTbs: number; vramGb: number }> = {
  h100: { name: "NVIDIA H100 SXM (Hopper)", fp16Tflops: 989, bwTbs: 3.35, vramGb: 80 },
  a100: { name: "NVIDIA A100 SXM (Ampere)", fp16Tflops: 312, bwTbs: 2.04, vramGb: 80 },
  l40s: { name: "NVIDIA L40S (Ada Lovelace)", fp16Tflops: 362, bwTbs: 0.864, vramGb: 48 },
  b200: { name: "NVIDIA B200 (Blackwell)", fp16Tflops: 2250, bwTbs: 8.0, vramGb: 192 },
};

const MODEL_PROFILES: Record<
  string,
  { name: string; paramsB: number; layers: number; kvHeads: number; headDim: number }
> = {
  llama3_8b: { name: "Llama-3-8B", paramsB: 8.0, layers: 32, kvHeads: 8, headDim: 128 },
  llama3_70b: { name: "Llama-3-70B", paramsB: 70.6, layers: 80, kvHeads: 8, headDim: 128 },
  mistral_7b: { name: "Mistral-7B", paramsB: 7.2, layers: 32, kvHeads: 8, headDim: 128 },
  deepseek_v3: { name: "DeepSeek-V3 (MoE 671B / MLA)", paramsB: 671.0, layers: 61, kvHeads: 4, headDim: 144 },
};

const LIFECYCLE_STAGES = [
  { n: 1, title: "Client Stream Request", detail: "HTTP/SSE prompt arrives at OpenAI-compatible API gateway with sampling params & max_tokens." },
  { n: 2, title: "Tokenization & Prefix Hash", detail: "BPE tokenizer converts prompt into token IDs; 64-bit rolling hashes computed per 16-token block." },
  { n: 3, title: "ZeroMQ ROUTER/DEALER IPC", detail: "Frontend API process sends binary msgspec payload (<15µs) to decoupled EngineCore process (no Python GIL stall)." },
  { n: 4, title: "Continuous Batching Scheduler", detail: "Enforces Decode-First invariant (N_comp → N_target): guarantees running decodes never starve behind incoming prefills." },
  { n: 5, title: "BlockPool & Radix Prefix Lookup", detail: "Checks prefix cache hash table; hits reuse physical KV blocks (zero compute!) and increment ref_count." },
  { n: 6, title: "Chunked Prefill Packing", detail: "Splits long prompts into fixed token chunks (e.g. 512) to pack leftover compute budget alongside decode tokens." },
  { n: 7, title: "CUDA Graph Bucket Dispatch", detail: "Pads active decode batch to discrete CUDA Graph bucket B ∈ {1,2,4,8,16,...} to bypass CPU kernel launch latency." },
  { n: 8, title: "PagedAttention / FlashAttention Kernel", detail: "GPU streams non-contiguous KV pages into SRAM via block_tables using online softmax rescaling." },
  { n: 9, title: "Logit Sampling / Speculative Verify", detail: "Applies top-p/temperature or exact speculative rejection sampling (residual distribution preserves target law)." },
  { n: 10, title: "Detokenize & Block Eviction", detail: "Streams token back via ZeroMQ; on EOS immediately decrements ref_counts and returns freed pages to LRU pool." },
];

const REFERENCES = [
  {
    title: "PagedAttention: Efficient Memory Management for LLM Serving (vLLM)",
    meta: "Woosuk Kwon et al. · SOSP 2023",
    url: "https://arxiv.org/abs/2309.06180",
    note: "Non-contiguous physical KV blocks, virtual block tables, Copy-on-Write prefix sharing.",
  },
  {
    title: "The JAX Scaling Book (How to Scale Your Model)",
    meta: "Google DeepMind · Austin, Douglas, Frostig, Levskaya, Chen",
    url: "https://jax-ml.github.io/scaling-book/",
    note: "Essential Staff bible on Roofline FLOP/byte math, TP/FSDP/PP collectives, and KV-cache sizing.",
  },
  {
    title: "DistServe: Disaggregating Prefill and Decode for LLM Serving",
    meta: "Yinmin Zhong et al. · OSDI 2024",
    url: "https://arxiv.org/abs/2401.09670",
    note: "Separating compute-bound prompt prefill nodes from memory-bound decode nodes to hit TTFT + TPOT SLAs.",
  },
  {
    title: "Splitwise: Efficient Generative LLM Serving Using Phase Separation",
    meta: "Pratyush Patel et al. · ISCA 2024",
    url: "https://arxiv.org/abs/2311.18677",
    note: "Hardware Roofline divergence between prefill and decode and heterogeneous GPU cluster economics.",
  },
  {
    title: "FlashAttention-3: Fast and Accurate Attention with Asynchrony",
    meta: "Jay Shah et al. · 2024",
    url: "https://arxiv.org/abs/2407.08608",
    note: "Hopper WGMMA, TMA warp specialization, and FP8 incoherent processing for IO-aware attention.",
  },
  {
    title: "The RLHF Book",
    meta: "Nathan Lambert · Open Online Book",
    url: "https://rlhfbook.com/",
    note: "Reward modeling, PPO, DPO, GRPO, and preference alignment mechanics.",
  },
];

interface NanoReq {
  id: string;
  prefix: string;
  tokens: number;
  maxTokens: number;
  blocks: number[];
  done: boolean;
}

const TOTAL_BLOCKS = 24;
const BLOCK_SIZE = 16;

export default function SandboxesPage() {
  // 1. Roofline state
  const [gpuKey, setGpuKey] = useState("h100");
  const [batchSize, setBatchSize] = useState(16);
  const [seqLen, setSeqLen] = useState(2048);
  const [bytesPerParam, setBytesPerParam] = useState(2); // 2=BF16, 1=FP8

  // 2. VRAM Sizer state
  const [modelKey, setModelKey] = useState("llama3_70b");
  const [tp, setTp] = useState(4);
  const [vramBatch, setVramBatch] = useState(32);
  const [vramCtx, setVramCtx] = useState(8192);
  const [kvBytes, setKvBytes] = useState(2);

  // 3. nano-vLLM PagedAttention & Radix Prefix-Cache Stepper state
  const [stepCount, setStepCount] = useState(0);
  const [prefixHits, setPrefixHits] = useState(0);
  const [reqs, setReqs] = useState<NanoReq[]>([
    { id: "R1", prefix: "SYS_A", tokens: 32, maxTokens: 64, blocks: [0, 1], done: false },
    { id: "R2", prefix: "SYS_A", tokens: 32, maxTokens: 80, blocks: [0, 2], done: false },
  ]);

  // 4. 10-Stage Lifecycle Stepper
  const [lifecycleIdx, setLifecycleIdx] = useState(0);

  // Roofline math
  const gpu = GPU_SPECS[gpuKey];
  const ridgePoint = gpu.fp16Tflops / gpu.bwTbs; // FLOP/byte
  const decodeAI = (2 * batchSize) / bytesPerParam; // ~2*B / b FLOP/byte for matmul weights
  const prefillAI = (2 * batchSize * seqLen) / (bytesPerParam * (batchSize * seqLen + 8192) / 8192 + bytesPerParam);
  const prefillAIClamped = Math.min(2500, Math.max(decodeAI * 8, seqLen / bytesPerParam));
  const decodePerf = Math.min(gpu.fp16Tflops, decodeAI * gpu.bwTbs);
  const prefillPerf = Math.min(gpu.fp16Tflops, prefillAIClamped * gpu.bwTbs);

  // Map log10(AI in [0.5..3000]) -> x in [50..560], log10(TFLOPS in [1..4000]) -> y in [220..25]
  const mapX = (ai: number) => 50 + ((Math.log10(Math.max(0.5, ai)) - Math.log10(0.5)) / (Math.log10(3000) - Math.log10(0.5))) * 510;
  const mapY = (tf: number) => 220 - ((Math.log10(Math.max(1, tf)) - Math.log10(1)) / (Math.log10(4000) - Math.log10(1))) * 195;

  // VRAM math
  const model = MODEL_PROFILES[modelKey];
  const vramCalc = useMemo(() => {
    const weightsPerGpu = (model.paramsB * 2) / tp; // BF16 weights sharded across TP
    const kvTotalGb =
      (2 * model.layers * model.kvHeads * model.headDim * kvBytes * vramCtx * vramBatch) /
      (1024 ** 3);
    const kvPerGpu = kvTotalGb / tp;
    const actOverhead = 3.5 + 0.06 * vramBatch;
    const totalUsed = weightsPerGpu + kvPerGpu + actOverhead;
    const capacity = gpu.vramGb;
    return {
      weightsPerGpu: Number(weightsPerGpu.toFixed(1)),
      kvPerGpu: Number(kvPerGpu.toFixed(1)),
      actOverhead: Number(actOverhead.toFixed(1)),
      totalUsed: Number(totalUsed.toFixed(1)),
      capacity,
      oom: totalUsed > capacity,
    };
  }, [model, tp, vramBatch, vramCtx, kvBytes, gpu.vramGb]);

  // nano-vLLM BlockPool calculations
  const blockRefs = useMemo(() => {
    const refs = Array(TOTAL_BLOCKS).fill(0);
    for (const r of reqs) {
      if (r.done) continue;
      for (const b of r.blocks) {
        if (b >= 0 && b < TOTAL_BLOCKS) refs[b] += 1;
      }
    }
    return refs;
  }, [reqs]);

  const usedBlockCount = blockRefs.filter((c) => c > 0).length;
  const activeTokens = reqs.filter((r) => !r.done).reduce((s, r) => s + r.tokens, 0);
  const naiveAllocated = reqs.filter((r) => !r.done).reduce((s, r) => s + r.maxTokens, 0);
  const pagedAllocated = usedBlockCount * BLOCK_SIZE;
  const fragmentationPct = pagedAllocated > 0 ? Math.max(0, ((pagedAllocated - activeTokens) / pagedAllocated) * 100) : 0;

  const findFreeBlock = (currentRefs: number[]) => currentRefs.findIndex((c) => c === 0);

  const stepNano = () => {
    setStepCount((c) => c + 1);
    setReqs((prev) => {
      const refs = Array(TOTAL_BLOCKS).fill(0);
      prev.forEach((r) => {
        if (!r.done) r.blocks.forEach((b) => (refs[b] += 1));
      });
      return prev.map((r) => {
        if (r.done) return r;
        const nextTok = r.tokens + 8;
        if (nextTok >= r.maxTokens) {
          return { ...r, tokens: r.maxTokens, done: true, blocks: [] };
        }
        const needBlocks = Math.ceil(nextTok / BLOCK_SIZE);
        const blocks = [...r.blocks];
        while (blocks.length < needBlocks) {
          const fb = findFreeBlock(refs);
          if (fb === -1) break;
          refs[fb] = 1;
          blocks.push(fb);
        }
        return { ...r, tokens: nextTok, blocks };
      });
    });
  };

  const addSharedPrefixReq = () => {
    setReqs((prev) => {
      const activeSysA = prev.find((r) => !r.done && r.prefix === "SYS_A" && r.blocks.length > 0);
      const refs = Array(TOTAL_BLOCKS).fill(0);
      prev.forEach((r) => {
        if (!r.done) r.blocks.forEach((b) => (refs[b] += 1));
      });
      const sharedBlock = activeSysA ? activeSysA.blocks[0] : findFreeBlock(refs);
      if (sharedBlock === -1) return prev;
      if (activeSysA) setPrefixHits((h) => h + 1);
      refs[sharedBlock] += 1;
      const tailBlock = findFreeBlock(refs);
      const blocks = tailBlock !== -1 ? [sharedBlock, tailBlock] : [sharedBlock];
      const nextId = `R${prev.length + 1}`;
      return [
        ...prev,
        { id: nextId, prefix: "SYS_A", tokens: 24, maxTokens: 96, blocks, done: false },
      ];
    });
  };

  const resetNano = () => {
    setStepCount(0);
    setPrefixHits(0);
    setReqs([
      { id: "R1", prefix: "SYS_A", tokens: 32, maxTokens: 64, blocks: [0, 1], done: false },
      { id: "R2", prefix: "SYS_A", tokens: 32, maxTokens: 80, blocks: [0, 2], done: false },
    ]);
  };

  return (
    <div className="space-y-8">
      <div className="border-b border-zinc-800 pb-5">
        <p className="font-mono text-xs uppercase tracking-widest text-emerald-400">
          Phase 2 · Interactive Systems & Inference Lab Suite
        </p>
        <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">
          Hardware Rooflines, VRAM Sizer & nano-vLLM Simulator
        </h1>
        <p className="mt-1 text-sm text-zinc-400">
          Interactive visualizers for Track 4 (Systems & Inference Core) and Stage 2 Whiteboard System Design warm-ups.
        </p>
      </div>

      {/* Sandbox 1 & 2 Grid: Roofline SVG Explorer + VRAM Partitioning Sizer */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* 1. Roofline SVG Explorer */}
        <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-emerald-400" />
              <h2 className="text-sm font-bold text-white">1. Arithmetic Intensity & GPU Roofline Explorer</h2>
            </div>
            <select
              value={gpuKey}
              onChange={(e) => setGpuKey(e.target.value)}
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1 font-mono text-xs text-white"
            >
              {Object.entries(GPU_SPECS).map(([k, v]) => (
                <option key={k} value={k}>
                  {v.name}
                </option>
              ))}
            </select>
          </div>

          <svg viewBox="0 0 600 255" className="w-full rounded-lg border border-zinc-800 bg-zinc-950">
            {/* Axes */}
            <line x1="50" y1="220" x2="565" y2="220" stroke="#3f3f46" strokeWidth="1" />
            <line x1="50" y1="25" x2="50" y2="220" stroke="#3f3f46" strokeWidth="1" />
            <text x="275" y="246" fill="#71717a" fontSize="10" fontFamily="monospace">
              Arithmetic Intensity (FLOP / Byte, log scale)
            </text>
            <text x="14" y="135" fill="#71717a" fontSize="10" fontFamily="monospace" transform="rotate(-90 14 135)">
              TFLOP/s
            </text>

            {/* Roofline Slope + Peak Ceiling */}
            <polyline
              fill="none"
              stroke="#34d399"
              strokeWidth="2.5"
              points={`${mapX(0.5)},${mapY(0.5 * gpu.bwTbs)} ${mapX(ridgePoint)},${mapY(gpu.fp16Tflops)} ${mapX(3000)},${mapY(gpu.fp16Tflops)}`}
            />
            {/* Ridge vertical guide */}
            <line
              x1={mapX(ridgePoint)}
              y1={mapY(gpu.fp16Tflops)}
              x2={mapX(ridgePoint)}
              y2="220"
              stroke="#3f3f46"
              strokeDasharray="4 4"
            />
            <text x={mapX(ridgePoint) + 6} y={mapY(gpu.fp16Tflops) + 14} fill="#a1a1aa" fontSize="10" fontFamily="monospace">
              Ridge: {ridgePoint.toFixed(1)} FLOP/B ({gpu.fp16Tflops} TF)
            </text>

            {/* Decode operating point */}
            <circle cx={mapX(decodeAI)} cy={mapY(decodePerf)} r="6" fill="#f59e0b" />
            <text x={mapX(decodeAI) + 8} y={mapY(decodePerf) + 4} fill="#fcd34d" fontSize="10" fontFamily="monospace">
              Decode ({decodeAI.toFixed(1)} F/B)
            </text>

            {/* Prefill operating point */}
            <circle cx={mapX(prefillAIClamped)} cy={mapY(prefillPerf)} r="6" fill="#38bdf8" />
            <text x={Math.min(430, mapX(prefillAIClamped) - 45)} y={mapY(prefillPerf) - 10} fill="#7dd3fc" fontSize="10" fontFamily="monospace">
              Prefill ({prefillAIClamped.toFixed(0)} F/B)
            </text>
          </svg>

          <div className="grid grid-cols-3 gap-3 font-mono text-xs">
            <label className="space-y-1">
              <span className="text-zinc-400">Batch: {batchSize}</span>
              <input
                type="range"
                min={1}
                max={256}
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
                className="w-full accent-amber-400"
              />
            </label>
            <label className="space-y-1">
              <span className="text-zinc-400">Seq Len: {seqLen}</span>
              <input
                type="range"
                min={128}
                max={8192}
                step={128}
                value={seqLen}
                onChange={(e) => setSeqLen(Number(e.target.value))}
                className="w-full accent-sky-400"
              />
            </label>
            <label className="space-y-1">
              <span className="text-zinc-400">Precision: {bytesPerParam === 2 ? "BF16" : "FP8/INT8"}</span>
              <select
                value={bytesPerParam}
                onChange={(e) => setBytesPerParam(Number(e.target.value))}
                className="w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-white"
              >
                <option value={2}>BF16 (2B)</option>
                <option value={1}>FP8/INT8 (1B)</option>
              </select>
            </label>
          </div>

          <p className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 font-mono text-xs text-zinc-300">
            Decode is{" "}
            <strong className={decodeAI < ridgePoint ? "text-amber-400" : "text-emerald-400"}>
              {decodeAI < ridgePoint ? "MEMORY-BANDWIDTH BOUND" : "COMPUTE BOUND"}
            </strong>{" "}
            ({decodePerf.toFixed(0)} / {gpu.fp16Tflops} TFLOP/s). Need batch ≥{" "}
            <strong>{Math.ceil((ridgePoint * bytesPerParam) / 2)}</strong> to saturate Tensor Cores!
          </p>
        </section>

        {/* 2. KV-Cache & VRAM Partitioning Sizer */}
        <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HardDrive className="h-4 w-4 text-sky-400" />
              <h2 className="text-sm font-bold text-white">2. KV-Cache & VRAM Partitioning Sizer</h2>
            </div>
            <select
              value={modelKey}
              onChange={(e) => setModelKey(e.target.value)}
              className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1 font-mono text-xs text-white"
            >
              {Object.entries(MODEL_PROFILES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3 font-mono text-xs sm:grid-cols-4">
            <label className="space-y-1">
              <span className="text-zinc-400">TP GPUs: {tp}</span>
              <select
                value={tp}
                onChange={(e) => setTp(Number(e.target.value))}
                className="w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-white"
              >
                {[1, 2, 4, 8].map((n) => (
                  <option key={n} value={n}>
                    TP={n}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1">
              <span className="text-zinc-400">Batch: {vramBatch}</span>
              <input
                type="range"
                min={1}
                max={128}
                value={vramBatch}
                onChange={(e) => setVramBatch(Number(e.target.value))}
                className="w-full accent-sky-400"
              />
            </label>
            <label className="space-y-1">
              <span className="text-zinc-400">Ctx: {vramCtx}</span>
              <input
                type="range"
                min={1024}
                max={32768}
                step={1024}
                value={vramCtx}
                onChange={(e) => setVramCtx(Number(e.target.value))}
                className="w-full accent-emerald-400"
              />
            </label>
            <label className="space-y-1">
              <span className="text-zinc-400">KV Dtype</span>
              <select
                value={kvBytes}
                onChange={(e) => setKvBytes(Number(e.target.value))}
                className="w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-white"
              >
                <option value={2}>BF16 (2B)</option>
                <option value={1}>FP8 (1B)</option>
              </select>
            </label>
          </div>

          {/* Stacked HBM Bar */}
          <div className="space-y-2">
            <div className="flex justify-between font-mono text-xs">
              <span className="text-zinc-300">
                Per-GPU HBM Usage ({gpu.name.split(" ")[1]} {vramCalc.capacity} GB)
              </span>
              <span className={vramCalc.oom ? "text-rose-400 font-bold" : "text-emerald-400 font-bold"}>
                {vramCalc.totalUsed} GB / {vramCalc.capacity} GB {vramCalc.oom ? "— OOM!" : "— FITS"}
              </span>
            </div>
            <div className="flex h-7 w-full overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950">
              <div
                style={{ width: `${Math.min(100, (vramCalc.weightsPerGpu / vramCalc.capacity) * 100)}%` }}
                className="bg-sky-500/80 flex items-center justify-center font-mono text-[10px] text-zinc-950 font-bold"
                title="Weights"
              >
                W: {vramCalc.weightsPerGpu}G
              </div>
              <div
                style={{ width: `${Math.min(100, (vramCalc.kvPerGpu / vramCalc.capacity) * 100)}%` }}
                className="bg-amber-400/85 flex items-center justify-center font-mono text-[10px] text-zinc-950 font-bold"
                title="KV Cache"
              >
                KV: {vramCalc.kvPerGpu}G
              </div>
              <div
                style={{ width: `${Math.min(100, (vramCalc.actOverhead / vramCalc.capacity) * 100)}%` }}
                className="bg-violet-500/80"
                title="Activations + CUDA Graph"
              />
            </div>
            <div className="flex flex-wrap gap-4 font-mono text-[11px] text-zinc-400">
              <span><span className="inline-block h-2 w-2 rounded-full bg-sky-500 mr-1" />Weights: {vramCalc.weightsPerGpu} GB</span>
              <span><span className="inline-block h-2 w-2 rounded-full bg-amber-400 mr-1" />KV Cache: {vramCalc.kvPerGpu} GB</span>
              <span><span className="inline-block h-2 w-2 rounded-full bg-violet-500 mr-1" />Act/CUDA Graphs: {vramCalc.actOverhead} GB</span>
            </div>
          </div>
        </section>
      </div>

      {/* Sandbox 3: nano-vLLM PagedAttention BlockPool & Radix Prefix-Cache Stepper */}
      <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-amber-400" />
            <div>
              <h2 className="text-sm font-bold text-white">
                3. In-Browser nano-vLLM PagedAttention BlockPool & Radix Prefix-Cache Stepper
              </h2>
              <p className="text-xs text-zinc-400">
                24 physical KV blocks ({BLOCK_SIZE} tokens/block). Amber blocks = shared prefix (`ref_count &gt; 1` via CoW); emerald = private blocks.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={stepNano}
              className="flex items-center gap-1 rounded-lg bg-emerald-600 px-3 py-1.5 font-mono text-xs font-semibold text-white hover:bg-emerald-500"
            >
              <Play className="h-3.5 w-3.5" /> Step (+8 tok)
            </button>
            <button
              type="button"
              onClick={addSharedPrefixReq}
              className="flex items-center gap-1 rounded-lg border border-amber-500/40 bg-amber-500/15 px-3 py-1.5 font-mono text-xs text-amber-200 hover:bg-amber-500/25"
            >
              <Plus className="h-3.5 w-3.5" /> Add Shared-Prefix Req
            </button>
            <button
              type="button"
              onClick={resetNano}
              className="flex items-center gap-1 rounded-lg border border-zinc-700 px-2.5 py-1.5 font-mono text-xs text-zinc-300 hover:bg-zinc-800"
            >
              <RotateCcw className="h-3.5 w-3.5" /> Reset
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          {/* Physical BlockPool Grid */}
          <div className="lg:col-span-2 space-y-3">
            <div className="grid grid-cols-6 gap-2 sm:grid-cols-8">
              {blockRefs.map((rc, bid) => (
                <div
                  key={bid}
                  className={`rounded-lg border p-2 text-center font-mono text-xs ${
                    rc > 1
                      ? "border-amber-400 bg-amber-500/20 text-amber-200"
                      : rc === 1
                      ? "border-emerald-500/50 bg-emerald-500/15 text-emerald-200"
                      : "border-zinc-800 bg-zinc-950 text-zinc-600"
                  }`}
                >
                  <div className="font-bold">B{bid}</div>
                  <div className="text-[10px]">ref:{rc}</div>
                </div>
              ))}
            </div>
            <div className="flex flex-wrap gap-4 font-mono text-xs text-zinc-400">
              <span>Iteration: <strong className="text-white">{stepCount}</strong></span>
              <span>Physical Used: <strong className="text-white">{usedBlockCount}/{TOTAL_BLOCKS}</strong></span>
              <span>Paged Waste: <strong className="text-emerald-400">{fragmentationPct.toFixed(1)}%</strong></span>
              <span>Naive Contiguous Need: <strong className="text-rose-400">{naiveAllocated} slots</strong></span>
              <span>Radix Prefix Hits: <strong className="text-amber-300">{prefixHits}</strong></span>
            </div>
          </div>

          {/* Active Request Block Tables */}
          <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-3 space-y-2 max-h-56 overflow-y-auto">
            <p className="font-mono text-[11px] font-bold uppercase text-zinc-400">
              Logical → Physical Block Tables
            </p>
            {reqs.map((r) => (
              <div
                key={r.id}
                className={`rounded border px-2.5 py-1.5 font-mono text-xs ${
                  r.done ? "border-zinc-900 text-zinc-600 line-through" : "border-zinc-800 text-zinc-200"
                }`}
              >
                <div className="flex justify-between">
                  <span>{r.id} ({r.prefix})</span>
                  <span>{r.tokens}/{r.maxTokens} tok</span>
                </div>
                <div className="text-[10px] text-zinc-400">
                  pages: [{r.blocks.join(", ")}]
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sandbox 4 & 5: 10-Stage Request Lifecycle + Reference Shelf */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-4">
          <h2 className="text-sm font-bold text-white">4. 10-Stage LLM Request Lifecycle Stepper</h2>
          <div className="flex flex-wrap gap-1.5">
            {LIFECYCLE_STAGES.map((st, idx) => (
              <button
                key={st.n}
                type="button"
                onClick={() => setLifecycleIdx(idx)}
                className={`rounded px-2.5 py-1 font-mono text-xs ${
                  lifecycleIdx === idx
                    ? "bg-emerald-500 text-zinc-950 font-bold"
                    : "bg-zinc-950 border border-zinc-800 text-zinc-400 hover:text-white"
                }`}
              >
                {st.n}
              </button>
            ))}
          </div>
          <div className="rounded-lg border border-emerald-500/30 bg-zinc-950 p-4 space-y-1.5">
            <p className="font-mono text-xs uppercase text-emerald-400">
              Stage {LIFECYCLE_STAGES[lifecycleIdx].n} of 10
            </p>
            <h3 className="text-base font-bold text-white">{LIFECYCLE_STAGES[lifecycleIdx].title}</h3>
            <p className="text-sm text-zinc-300">{LIFECYCLE_STAGES[lifecycleIdx].detail}</p>
          </div>
        </section>

        <section className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-3">
          <div className="flex items-center gap-2">
            <BookMarked className="h-4 w-4 text-sky-400" />
            <h2 className="text-sm font-bold text-white">5. Curated Systems & Frontier Reference Shelf</h2>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {REFERENCES.map((ref) => (
              <a
                key={ref.title}
                href={ref.url}
                target="_blank"
                rel="noreferrer"
                className="block rounded-lg border border-zinc-800 bg-zinc-950 p-3 hover:border-sky-500/50"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-xs font-semibold text-white">{ref.title}</p>
                  <ExternalLink className="h-3.5 w-3.5 text-sky-400 shrink-0" />
                </div>
                <p className="font-mono text-[10px] text-sky-300/80">{ref.meta}</p>
                <p className="mt-1 text-xs text-zinc-400">{ref.note}</p>
              </a>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
