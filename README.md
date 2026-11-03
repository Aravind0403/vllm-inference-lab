# vLLM v1 Systems Lab & Interactive Courseware

An interactive systems engineering laboratory and courseware platform for **vLLM v1**, **PagedAttention**, and **modern LLM inference architectures**.

Inspired by:
- `infra.bea.ai` (Dual-phase Roofline models, interactive calculators, latency breakdowns, and `nano-vllm`).
- Practice-first personal LMS design (structured curriculum, code predict-and-test, self-grading quizzes, and milestone lab rubrics).
- Local vLLM v1 codebase at `/Users/aravindsundaresan/Open_Source/vLLMs/vllm_src`.

---

## Quick Start (Run Locally)

### Option 1: Open Directly in Browser
```bash
open file:///Users/aravindsundaresan/Documents/ChatGPT/vllm-inference-systems-lab/index.html
```

### Option 2: Serve Locally (Recommended)
```bash
python3 -m http.server 8085 --directory /Users/aravindsundaresan/Documents/ChatGPT/vllm-inference-systems-lab/
# Open: http://localhost:8085
```

### Option 3: Run the nano-vllm Micro-Engine in Terminal
```bash
python3 /Users/aravindsundaresan/Documents/ChatGPT/vllm-inference-systems-lab/nano_vllm.py
```

---

## Interactive Systems Sandboxes

1. **Arithmetic Intensity & Roofline Explorer**:
   - Hardware selector: NVIDIA H100 SXM, A100 SXM, L40S, B200.
   - Interactive sliders for Batch Size ($B$) and Sequence Length ($S$).
   - Dynamic SVG Roofline plot rendering the exact operational point ($I = \text{FLOPs} / \text{Byte}$) and identifying whether your setup is Compute-Bound or Memory-Bandwidth Bound.
2. **KV Cache & VRAM Budgeting Sizer**:
   - Model profiles: Llama-3-70B, Llama-3-8B, Mistral-7B, DeepSeek-V3.
   - Formats: FP16 (2B), FP8 (1B - doubles concurrency!), INT4 (0.5B).
   - Real-time VRAM breakdown: Weights, Peak Activation Workspace, CUDA Graphs, and Available KV Cache.
   - Calculates exact max concurrent streams and 16-token PagedAttention physical blocks.
3. **Serving Architecture Timeline Comparison**:
   - Visual timeline stepping through:
     1. Naive Static Batching (bubbles when sequences finish early).
     2. Continuous Batching (v0 / Orca: dynamic slots, but prefill stalls decodes).
     3. Chunked Prefill (v1 / Sarathi-Serve: 512-token chunks co-scheduled with decodes).
     4. Prefill / Decode Disaggregation (dedicated nodes streaming over RDMA).
4. **In-Browser nano-vLLM Stepper**:
   - Interactive visual stepper of the 16-block memory pool and request queues.
   - Watch physical blocks allocate, prefix hashes match (0ms hit!), and completed blocks return to LRU.

---

## Course Curriculum & Labs

- **6 Learning Paths**: From the 10-Stage Request Lifecycle to ZeroMQ IPC, Continuous Batching, BlockPool, CUDA Graphs, and RDMA Disaggregation.
- **17 Interactive Lessons**: Questions, derivations, code inspections, and self-check quizzes.
- **5 Systems Milestones**: Hands-on lab deliverables evaluated across the 4-pillar mastery standard (*Explain, Derive, Implement, Critique*).
- **Curated Reference Shelf**: Direct links to foundational research papers (PagedAttention, DistServe, Splitwise, FlashAttention-3).
