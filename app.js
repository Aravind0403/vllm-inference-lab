// vLLM Systems Lab - Master Client Engine (Zero CDN, 100% Offline-Ready)
// Navigation Flow: Dashboard (Starting Page) -> Curriculum -> Milestones -> References -> Interactive Sandboxes

const units = [
  {
    "id": "journey",
    "n": "00",
    "title": "The 10-Stage Request Lifecycle",
    "phase": "FOUNDATIONS",
    "time": "2 sessions",
    "desc": "Trace a prompt from browser input (e.g. Gemini/ChatGPT) through the API gateway, ZeroMQ IPC, scheduler, BlockPool, and CUDA graphs to GPU output tokens."
  },
  {
    "id": "engine",
    "n": "01",
    "title": "Engine Architecture & Multiprocess IPC",
    "phase": "SYSTEMS CORE",
    "time": "3 sessions",
    "desc": "Physical process separation, ZeroMQ ROUTER/DEALER sockets, msgspec binary serialization (<15\u00b5s), and POSIX shared memory tensor IPC."
  },
  {
    "id": "scheduler",
    "n": "02",
    "title": "Continuous Batching Scheduler Critical Path",
    "phase": "SCHEDULING",
    "time": "3 sessions",
    "desc": "The unified scheduling invariant N_comp -> N_target, dynamic chunked prefill, 3-tier queue hierarchy, and production bug case studies (Issue #40004 & PR #58947)."
  },
  {
    "id": "kvcache",
    "n": "03",
    "title": "KV Cache Allocation, BlockPool & Prefix Caching",
    "phase": "MEMORY MANAGEMENT",
    "time": "3 sessions",
    "desc": "PagedAttention virtual memory tables, 64-bit cryptographic rolling hash, dual-queue LRU eviction & ghost hits, SWA and Mamba alignment."
  },
  {
    "id": "memory",
    "n": "04",
    "title": "Memory Profiling, Budgeting & CUDA Graphs",
    "phase": "PERFORMANCE & GPU",
    "time": "3 sessions",
    "desc": "VRAM partitioning, determine_available_memory empirical forward pass, CUDA Graph discrete batch buckets B in {1,2,4,8,...}, and kernel launch bypass (<15\u00b5s)."
  },
  {
    "id": "offloading",
    "n": "05",
    "title": "KV Cache Offloading & Async Disaggregation",
    "phase": "DISTRIBUTED SYSTEMS",
    "time": "3 sessions",
    "desc": "Hierarchical HBM/CPU/NVMe storage tiers, Prefill/Decode node disaggregation, async 4-stage transfer pipeline, and PR #59504 RDMA zeroing race fix."
  }
];
const sessions = [
  {
    "id": "s0_1",
    "unit": "journey",
    "title": "From Browser Keystroke to Engine Ingress",
    "subtitle": "Trace Stages 1 through 4: Web client, API gateway, AsyncMPClient, and EngineCoreProc.",
    "objective": "Map how a user's prompt in Gemini/ChatGPT converts into token IDs and crosses the process boundary into vLLM's background engine.",
    "question": "When you hit 'Enter' on a prompt like 'Explain why the sky is blue', how does the text travel across the web stack, bypass the Python GIL, and arrive safely inside the GPU worker process?",
    "definition": "In high-throughput serving systems, network ingestion (HTTP/WebSockets/SSE) and tokenization are physically decoupled from GPU scheduling to avoid stalling Tensor Cores.",
    "derive": "Consider an incoming prompt with 14 tokens. In Python v0, tokenizing on the main thread blocked the event loop for ~15ms. In vLLM v1, the frontend AsyncMPClient serializes the request using binary msgspec (<15\u00b5s) and sends it over a ZeroMQ ROUTER socket to a DEALER socket on EngineCoreProc.",
    "equation": "<div class=\"math-eq\"><span>Latency<sub>Ingress</sub> = Serialization<sub>msgspec</sub> (&lt; 15\u00b5s) + ZMQ<sub>IPC</sub> (&lt; 20\u00b5s) &lt; 35\u00b5s</span></div>",
    "code": [
      "# vllm/v1/engine/core_client.py: Ingress path",
      "async def add_request_async(self, request: Request) -> None:",
      "    # 1. Binary serialize via msgspec",
      "    frame = self._encoder.encode(request)",
      "    # 2. Non-blocking transmit across ZeroMQ ROUTER socket",
      "    await self._zmq_router_socket.send_multipart([",
      "        self._engine_identity,",
      "        EngineCoreCommand.ADD.value,",
      "        frame",
      "    ])"
    ],
    "hint": "The ZeroMQ ROUTER socket matches client requests to the backend worker by prepending an engine identity envelope.",
    "tasks": [
      "Open vllm/v1/engine/core_client.py in your local repo and inspect add_request_async().",
      "Identify how self._encoder is instantiated and what msgspec schema it uses.",
      "Write an assertion in Python checking that msgspec encoding takes under 30 microseconds for a 100-token prompt."
    ],
    "readingTitle": "vllm/v1/engine/core_client.py \u00b7 Local Source",
    "readingUrl": "file:///Users/aravindsundaresan/Open_Source/vLLMs/vllm_src/vllm/v1/engine/core_client.py",
    "readingNote": "Inspect how AsyncMPClient and SyncMPClient diverge in how they await or block on ZeroMQ socket messages.",
    "quiz": [
      [
        "Why does AsyncMPClient use msgspec instead of standard Python pickle?",
        [
          "msgspec supports pickle protocols natively",
          "msgspec achieves binary serialization in <15\u00b5s and avoids security execution risks of pickle",
          "Python pickle cannot serialize strings"
        ],
        1,
        "msgspec provides high-performance C-based binary serialization that runs in microseconds without the security vulnerabilities of arbitrary code execution inherent in pickle."
      ],
      [
        "What socket type does the frontend AsyncMPClient use to communicate with EngineCoreProc?",
        [
          "PUB socket",
          "PAIR socket",
          "ROUTER socket"
        ],
        2,
        "The client uses a ZeroMQ ROUTER socket, while the engine process uses a DEALER socket, establishing an asynchronous, multi-channel control plane."
      ]
    ],
    "time": "90\u2013120 min",
    "tags": [
      "Read",
      "Architecture",
      "ZeroMQ IPC"
    ],
    "badge": "JOURNEY",
    "badgeClass": "journey"
  },
  {
    "id": "s0_2",
    "unit": "journey",
    "title": "From Scheduler Queue to GPU Forward Execution & Egress",
    "subtitle": "Trace Stages 5 through 10: Scheduler admission, BlockPool allocation, CUDA Graphs, and token streaming.",
    "objective": "Follow the request as it enters continuous batching, claims KV cache pages, executes on GPU Tensor Cores, and streams back to the browser.",
    "question": "Once the prompt tokens sit in self.waiting, how does the scheduler decide to run them, how are physical GPU memory blocks assigned, and how does the sampled token 'Because' reach the user's screen?",
    "definition": "The scheduler packs available prompt tokens into an execution batch subject to memory budgets, queries BlockPool for prefix cache hits, replays a pre-compiled CUDA Graph, and pushes output token IDs across ZeroMQ back to the web server.",
    "derive": "For prompt length S=14, the scheduler allocates 14 tokens in Phase 2. BlockPool hashes the tokens; if cached, it reuses existing GPU blocks in O(1). The model runner launches a forward pass, samples the first token ID, and streams it back via a ZeroMQ PUSH socket.",
    "equation": "<div class=\"math-eq\"><span>TTFT = Wait<sub>Queue</sub> + T<sub>Prefix_Hit</sub> (0ms) + Forward<sub>Prefill</sub> (&lt; 20ms) + Stream<sub>SSE</sub></span></div>",
    "code": [
      "# vllm/v1/engine/core.py: Engine background step loop",
      "def step(self):",
      "    # 1. Schedule next batch",
      "    scheduler_output = self.scheduler.schedule()",
      "    # 2. Execute GPU forward pass (FlashAttention / CUDA Graph)",
      "    model_output = self.model_runner.execute_model(scheduler_output)",
      "    # 3. Stream generated token IDs to client over ZMQ PUSH socket",
      "    self._push_token_stream(model_output)"
    ],
    "hint": "Token streaming is decoupled from the forward pass: newly sampled token IDs are immediately written to the ZMQ PUSH socket so the client can stream SSE chunks.",
    "tasks": [
      "Open vllm/v1/engine/core.py and trace the main step() loop.",
      "Verify what data structure model_output returns to the engine loop.",
      "Calculate the Time to First Token (TTFT) when a prefix cache hit occurs versus a full prefill pass."
    ],
    "readingTitle": "vllm/v1/engine/core.py \u00b7 Local Source",
    "readingUrl": "file:///Users/aravindsundaresan/Open_Source/vLLMs/vllm_src/vllm/v1/engine/core.py",
    "readingNote": "Study the step() method and notice how input queue popping and scheduler execution are interleaved.",
    "quiz": [
      [
        "What happens if our 14-token prompt matches a common system prompt previously processed?",
        [
          "The engine recomputes attention weights",
          "BlockPool detects matching 64-bit hashes and delivers an instant O(1) prefix cache hit",
          "The request is aborted and re-queued"
        ],
        1,
        "Prefix caching hashes blocks of tokens; if an identical block hash exists in GPU memory, the engine reuses the physical blocks with 0ms compute overhead."
      ],
      [
        "How does the newly sampled token ID get back to the frontend FastAPI server?",
        [
          "Via HTTP polling",
          "EngineCoreProc pushes it across a ZeroMQ PUSH socket to the client's PULL socket",
          "It is written to a shared disk file"
        ],
        1,
        "The data path uses a dedicated ZeroMQ PUSH -> PULL pipeline, ensuring immediate streaming with sub-millisecond overhead."
      ]
    ],
    "time": "90\u2013120 min",
    "tags": [
      "Read",
      "Scheduler",
      "Profiling"
    ],
    "badge": "JOURNEY",
    "badgeClass": "journey"
  },
  {
    "id": "s1_1",
    "unit": "engine",
    "title": "Hardware Roofline & Arithmetic Intensity Divergence",
    "subtitle": "Understand the physical split: Compute-bound prefill vs Memory-bandwidth bound decode.",
    "objective": "Derive arithmetic intensity and prove why single-token decoding underutilizes modern GPU Tensor Cores.",
    "question": "Why does generating one token on an 80GB NVIDIA H100 run at only ~1% compute utilization unless dozens of requests are batched together?",
    "definition": "Arithmetic intensity (I) measures FLOPs per byte of memory transferred. On NVIDIA H100 (3,350 TFLOPs FP16 vs 3.35 TB/s HBM3), the hardware ridge point is ~1,000 FLOPs/byte.",
    "derive": "In prefill (M = S_prompt), all tokens attend to each other simultaneously in matrix-matrix operations (GEMM), yielding I >> 100 FLOPs/byte. In decode (M = 1), each forward step streams every weight tensor parameter and every prior cached KV activation just to produce one token, yielding I \u2248 1 FLOP/byte.",
    "equation": "<div class=\"math-eq\"><span>Memory<sub>KV</sub>(S) = 2 &times; L &times; N<sub>kv</sub> &times; D &times; P &times; S&nbsp;&nbsp;[bytes/request]</span></div>",
    "code": [
      "# Calculate KV cache memory per token for Llama-3-70B",
      "# L=80 layers, N_kv=8 heads, D=128 head_dim, P=2 bytes (BF16)",
      "L, N_kv, D, P = 80, 8, 128, 2",
      "bytes_per_token = 2 * L * N_kv * D * P",
      "print(f'Bytes per token: {bytes_per_token:,} B ({bytes_per_token / 1024:.1f} KB)')",
      "context_len = 8192",
      "total_gb = (bytes_per_token * context_len) / (1024**3)",
      "print(f'KV Cache for {context_len} tokens: {total_gb:.2f} GB per sequence')"
    ],
    "hint": "Multiply the bytes per token by 8,192 to see how a single request consumes over 2.5GB of dedicated VRAM.",
    "tasks": [
      "Run the snippet in Python or Jupyter to verify that Llama-3-70B consumes 320 KB per token.",
      "Calculate how many concurrent 8,192-token sequences can fit in an 80GB GPU if weights take 35GB.",
      "Explain why batching 64 decode requests amortizes the cost of loading model weights across sequences."
    ],
    "readingTitle": "Splitwise: Efficient Generative LLM Serving (ISCA 2024)",
    "readingUrl": "https://arxiv.org/abs/2311.18677",
    "readingNote": "Read Section 2 on the physical divergence between prompt phase and token generation phase.",
    "quiz": [
      [
        "Why is single-token autoregressive decoding memory-bandwidth bound?",
        [
          "The GPU runs out of registers",
          "The GPU must load all model weights and KV activations from HBM for a single vector-matrix multiplication (M=1)",
          "Attention matrix size is too large to fit in cache"
        ],
        1,
        "In decoding, M=1, meaning matrix operations collapse to matrix-vector products. The GPU spends almost all its time streaming weights from HBM to registers."
      ],
      [
        "For Llama-3-70B in FP16, how much KV cache does an 8,192-token sequence consume?",
        [
          "25.6 MB",
          "256 MB",
          "2.56 GB"
        ],
        2,
        "327,680 bytes/token * 8,192 tokens = 2,684,354,560 bytes \u2248 2.56 GB."
      ]
    ],
    "time": "60\u201390 min",
    "tags": [
      "Derive",
      "Roofline",
      "Analysis"
    ],
    "badge": "ENGINE",
    "badgeClass": "engine"
  },
  {
    "id": "s1_2",
    "unit": "engine",
    "title": "The Failure of v0 & The v1 Multiprocess Paradigm",
    "subtitle": "Discover why single-process Python serving introduced 15\u201330ms scheduling bubbles and how v1 fixed it.",
    "objective": "Analyze the architectural changes between vLLM v0 and v1 and inspect EngineCoreProc process isolation.",
    "question": "What happens when Python's Global Interpreter Lock (GIL), tokenization, and web request handling share the same thread as GPU kernel launching?",
    "definition": "In vLLM v0, CPU-bound string processing and GIL contention delayed GPU scheduling loops by 15\u201330ms. vLLM v1 isolates GPU execution into an independent background process (EngineCoreProc) that never touches web sockets.",
    "derive": "In v1, the background process runs a dedicated input_thread that receives commands from the frontend over ZeroMQ. The main engine thread runs an uninterrupted while True busy loop, driving the GPU at maximum utilization.",
    "equation": "<div class=\"math-eq\"><span>Scheduling Overhead: v0 (15&ndash;30 ms GIL Jitter) &rarr; v1 (&lt; 50 &mu;s IPC Ingestion)</span></div>",
    "code": [
      "# vllm/v1/engine/core.py: Dedicated background input thread",
      "class EngineCoreProc:",
      "    def _input_loop(self) -> None:",
      "        while not self._shutdown_event.is_set():",
      "            msg = self._dealer_socket.recv_multipart()",
      "            cmd, payload = msg[0], msg[1]",
      "            if cmd == EngineCoreCommand.ADD.value:",
      "                req = self._decoder.decode(payload)",
      "                self._preprocess_add_request(req)",
      "                self._input_queue.put_nowait(req)"
    ],
    "hint": "Notice that _preprocess_add_request() executes inside the input thread so hash computations do not steal time from the main GPU step loop.",
    "tasks": [
      "Inspect vllm/v1/engine/core.py in your local repo around line 200 to find _input_loop().",
      "Verify what thread pool or threading class starts _input_loop.",
      "Trace how self._input_queue transfers requests from input_thread to the main execution loop."
    ],
    "readingTitle": "vllm/v1/engine/core.py \u00b7 Local Source",
    "readingUrl": "file:///Users/aravindsundaresan/Open_Source/vLLMs/vllm_src/vllm/v1/engine/core.py",
    "readingNote": "Observe how EngineCoreProc initializes its ZeroMQ sockets and input queues.",
    "quiz": [
      [
        "What was the primary cause of scheduling bubbles in vLLM v0?",
        [
          "CUDA kernel crashes",
          "Python GIL contention and tokenization sharing the same process/thread as the GPU loop",
          "Slow network cards"
        ],
        1,
        "CPU-intensive tokenization, JSON parsing, and garbage collection blocked the Python GIL, leaving the GPU idle between forward passes."
      ],
      [
        "What role does the input_thread play in EngineCoreProc?",
        [
          "It executes CUDA kernels",
          "It asynchronously ingests and decodes ZeroMQ messages, pre-hashes tokens, and queues them for the engine loop",
          "It communicates with the database"
        ],
        1,
        "input_thread runs independently to ensure that socket receiving and deserialization never stall the main GPU scheduling loop."
      ]
    ],
    "time": "90\u2013120 min",
    "tags": [
      "Read",
      "Benchmarks",
      "Code"
    ],
    "badge": "ENGINE",
    "badgeClass": "engine"
  },
  {
    "id": "s1_3",
    "unit": "engine",
    "title": "ZeroMQ IPC, Binary Msgpack & Shared Memory Tensors",
    "subtitle": "Inspect how vLLM v1 achieves sub-15 microsecond IPC without copying tensor buffers.",
    "objective": "Understand the three client implementations (InprocClient, SyncMPClient, AsyncMPClient) and POSIX shared memory (torch_shm).",
    "question": "How can an API process pass multi-megabyte image embeddings or prompt tensor tensors to a background GPU worker without copying gigabytes through network sockets?",
    "definition": "Small control structs are serialized using msgspec (<15\u00b5s) over ZeroMQ ROUTER/DEALER sockets. Large multimodal tensors bypass sockets entirely by writing into POSIX shared memory (/dev/shm via torch_shm), passing only lightweight memory handles.",
    "derive": "Copying a 50MB tensor across a Unix socket takes ~2ms. Passing a POSIX shared memory handle takes <5\u00b5s. vLLM uses torch_shm for multimodal inputs and msgspec for Request metadata.",
    "equation": "<div class=\"math-eq\"><span>IPC Latency: Socket Copy (2,000 &mu;s) vs POSIX Shared Memory (&lt; 5 &mu;s)</span></div>",
    "code": [
      "# vllm/v1/engine/core_client.py: Client selection",
      "# 1. InprocClient: Synchronous single-process loop (unit tests)",
      "# 2. SyncMPClient: Background process with blocking API (LLM.generate)",
      "# 3. AsyncMPClient: Asyncio non-blocking IPC (FastAPI / OpenAI server)",
      "if self.vllm_config.inproc:",
      "    return InprocClient(...)",
      "elif self.vllm_config.is_async:",
      "    return AsyncMPClient(...)",
      "else:",
      "    return SyncMPClient(...)"
    ],
    "hint": "Check core_client.py to see how AsyncMPClient uses asyncio.Queue to route responses back to individual request streams.",
    "tasks": [
      "Open vllm/v1/engine/core_client.py and compare SyncMPClient against AsyncMPClient.",
      "Find the torch_shm utility in vllm/v1/ and observe how tensor handles are constructed.",
      "Write a short script comparing the creation time of a shared memory tensor vs a deep copy."
    ],
    "readingTitle": "ZeroMQ ROUTER and DEALER Sockets Guide",
    "readingUrl": "https://zguide.zeromq.org/docs/chapter3/#The-Asynchronous-Client-Server-Pattern",
    "readingNote": "Read the asynchronous client-server pattern to understand why ROUTER/DEALER is the gold standard for multiprocess IPC.",
    "quiz": [
      [
        "When should InprocClient be used instead of AsyncMPClient?",
        [
          "In production web servers",
          "For unit tests, local CPU debugging, and simplified tracing",
          "When serving multimodal models"
        ],
        1,
        "InprocClient runs everything in a single process synchronously, which simplifies debugging and unit testing but reintroduces GIL contention."
      ],
      [
        "How does torch_shm pass multimodal tensors between the client and engine process?",
        [
          "By serializing into base64 strings",
          "By writing to POSIX shared memory and passing a pointer handle",
          "By uploading to an S3 bucket"
        ],
        1,
        "POSIX shared memory (/dev/shm) allows both processes to map the same physical RAM pages, enabling zero-copy tensor passing."
      ]
    ],
    "time": "90\u2013120 min",
    "tags": [
      "Code",
      "IPC",
      "Profiling"
    ],
    "badge": "ENGINE",
    "badgeClass": "engine"
  },
  {
    "id": "s2_1",
    "unit": "scheduler",
    "title": "The Unified Scheduling Invariant (N_comp -> N_target)",
    "subtitle": "Eliminate the artificial divide between prefill and decode passes.",
    "objective": "Master vLLM v1's unified invariant and dynamic chunked prefill co-scheduling.",
    "question": "Why did earlier engines separate execution into 'prefill batches' and 'decode batches', and how does v1 treat all requests as advancing from computed tokens to target tokens?",
    "definition": "The Unified Scheduling Invariant states that every request simply advances its computed token count toward its target length: N_computed -> N_target. Prefill is merely chunked token progression; decode is a 1-token progression.",
    "derive": "A 2,048-token prompt under a 512-token chunk limit is scheduled across 4 steps. In every step, its 512-token chunk is packed alongside active 1-token decode requests in the exact same forward pass.",
    "equation": "<div class=\"math-eq\"><span>Unified Step: &sum; Tokens<sub>i</sub> &le; max_num_batched_tokens &nbsp;&amp;&nbsp; |Requests| &le; max_num_seqs</span></div>",
    "code": [
      "# vllm/v1/core/sched/scheduler.py: Unified scheduling loop",
      "def schedule(self) -> SchedulerOutput:",
      "    budget = SchedulingBudget(self.max_num_batched_tokens, self.max_num_seqs)",
      "    # Phase 1: Schedule running requests (protect TPOT)",
      "    for req in self.running:",
      "        num_tokens = req.get_num_new_tokens()",
      "        if budget.can_schedule(num_tokens, 1):",
      "            self.kv_cache_manager.allocate(req, num_tokens)",
      "            budget.consume(num_tokens, 1)",
      "            scheduled_running.append(req)"
    ],
    "hint": "Running requests ask for 1 token (or spec decode tokens), while waiting requests ask for min(uncomputed, remaining_budget).",
    "tasks": [
      "Open vllm/v1/core/sched/scheduler.py and inspect schedule().",
      "Find SchedulingBudget and see how it tracks remaining tokens and sequence slots.",
      "Derive the maximum possible batch size if max_num_batched_tokens=8192 and all requests are decode requests."
    ],
    "readingTitle": "vllm/v1/core/sched/scheduler.py \u00b7 Local Source",
    "readingUrl": "file:///Users/aravindsundaresan/Open_Source/vLLMs/vllm_src/vllm/v1/core/sched/scheduler.py",
    "readingNote": "Study how the scheduler manages token budgets and sequence budgets simultaneously.",
    "quiz": [
      [
        "What is the Unified Scheduling Invariant in vLLM v1?",
        [
          "Prefill batches run strictly before decode batches",
          "All requests simply advance from N_computed to N_target without dedicated phase modes",
          "Decode requests run only when no prefill requests exist"
        ],
        1,
        "v1 unifies all sequences: every sequence is simply advancing computed tokens towards its target length, co-scheduling prefill chunks and decodes."
      ],
      [
        "Why are RUNNING requests evaluated before WAITING requests during schedule()?",
        [
          "To maximize prompt throughput",
          "To protect token-to-token latency (TPOT) and prevent active user streams from pausing",
          "Because running requests have larger prompts"
        ],
        1,
        "Once a sequence starts streaming to a user, pausing it creates noticeable lag. Scheduling running requests first preserves predictable TPOT."
      ]
    ],
    "time": "120 min",
    "tags": [
      "Derive",
      "Code",
      "Invariants"
    ],
    "badge": "SCHEDULER",
    "badgeClass": "scheduler"
  },
  {
    "id": "s2_2",
    "unit": "scheduler",
    "title": "Queue Priority Hierarchy & Deadlock Prevention (PR #58947)",
    "subtitle": "Discover how queue ordering guarantees system progress and prevents memory deadlocks.",
    "objective": "Understand the three internal queues (running, kv_holding_waiting, waiting) and PR #58947.",
    "question": "What happens when a running request gets paused due to memory exhaustion: if new requests jump ahead of it, why can the system completely deadlock?",
    "definition": "If preempted requests holding KV blocks are queued behind fresh requests, new requests cannot find enough free blocks to start, while the holding request is never scheduled to finish. PR #58947 established kv_holding_waiting queue priority.",
    "derive": "Priority order must strictly be: (1) running -> (2) kv_holding_waiting -> (3) waiting. Draining block-holding requests releases physical pages back to the pool, guaranteeing forward progress.",
    "equation": "<div class=\"math-eq\"><span>Scheduling Priority: running &gt; kv_holding_waiting &gt; waiting</span></div>",
    "code": [
      "# PR #58947: Rework scheduler queue priority",
      "# vllm/v1/core/sched/request_queue.py",
      "class RequestQueue:",
      "    def __init__(self):",
      "        self.running = []",
      "        self.kv_holding_waiting = collections.deque()",
      "        self.waiting = collections.deque()",
      "    # kv_holding_waiting is ALWAYS drained before waiting!"
    ],
    "hint": "Requests in kv_holding_waiting already possess allocated blocks; draining them lets them complete and return memory to the pool.",
    "tasks": [
      "Open vllm/v1/core/sched/request_queue.py and inspect how queues are organized.",
      "Find git commit 42dbe4578 in your local repo (git show 42dbe4578) to see PR #58947.",
      "Sketch a scenario where inverted priority leads to 0 tokens scheduled despite non-empty queues."
    ],
    "readingTitle": "PR #58947: Rework scheduler skipped_waiting queue",
    "readingUrl": "https://github.com/vllm-project/vllm/pull/58947",
    "readingNote": "Read the PR description and discussion on why holding blocks without executing causes head-of-line deadlock.",
    "quiz": [
      [
        "Why must kv_holding_waiting take precedence over waiting?",
        [
          "Waiting requests have higher priority",
          "Holding requests already monopolize memory blocks; executing them allows them to finish and free blocks",
          "Holding requests have shorter context"
        ],
        1,
        "Holding requests already own valuable GPU blocks. Draining them allows them to complete and return physical pages to the pool."
      ],
      [
        "What trigger causes a request to move from running to kv_holding_waiting?",
        [
          "The user disconnects",
          "Transient KV cache memory exhaustion where new blocks cannot be allocated",
          "The request finished generating EOS"
        ],
        1,
        "When physical blocks run out mid-generation, the scheduler pauses the sequence instead of immediately discarding its allocated cache."
      ]
    ],
    "time": "90 min",
    "tags": [
      "Trace",
      "Queue Order",
      "PR #58947"
    ],
    "badge": "SCHEDULER",
    "badgeClass": "scheduler"
  },
  {
    "id": "s2_3",
    "unit": "scheduler",
    "title": "Production Bug Case Study: Issue #40004 & PR #45558 / #54530",
    "subtitle": "Examine how a subtle sequence slot race caused running requests to be preempted.",
    "objective": "Deep-dive into Issue #40004, slot preemption bugs, and PR #54530 adaptive prefill thresholds.",
    "question": "How could a brand-new 16-token prompt arriving at an engine preempt an active 4,000-token decode request that was 95% complete?",
    "definition": "Issue #40004 demonstrated that without strict phase separation, waiting requests could claim sequence slots before running requests claimed their next token, triggering catastrophic preemption.",
    "derive": "PR #45558 and PR #54530 solved this by ensuring that all running requests claim allocations first, and introduced an adaptive long-prefill token threshold (PR #58459) to prevent chunk starvation.",
    "equation": "<div class=\"math-eq\"><span>Invariant: Phase 1 (Running Allocations) MUST COMPLETE before Phase 2 (Waiting Allocations)</span></div>",
    "code": [
      "# Issue #40004 resolution: Strict two-phase budget allocation",
      "# Phase 1: Running sequences MUST evaluate first",
      "for req in self.running:",
      "    if not self.kv_cache_manager.can_allocate(req, num_new_tokens):",
      "        self._preempt(req)",
      "    else:",
      "        self.kv_cache_manager.allocate(req, num_new_tokens)",
      "# Phase 2: ONLY then evaluate waiting queue",
      "while self.waiting and budget.has_remaining():",
      "    ..."
    ],
    "hint": "Check Issue #40004 comment thread to see how ping-pong preemption occurred between equal priority sequences.",
    "tasks": [
      "Search git log in your local repo for commit 6697a7dd3 (PR #58459).",
      "Explain how --long-prefill-token-threshold adapts chunk sizes when requests run solo.",
      "Write down the three hazards identified in Issue #40004: slot stealing, ping-pong preemption, and LoRA accounting leaks."
    ],
    "readingTitle": "Issue #40004: Slot Preemption Hazard Discussion",
    "readingUrl": "https://github.com/vllm-project/vllm/issues/40004",
    "readingNote": "Read the bug report and see how benchmark runs exposed unexpected throughput collapse under high load.",
    "quiz": [
      [
        "What was the root cause of Issue #40004?",
        [
          "CUDA out of memory in PyTorch",
          "Waiting requests claimed sequence slots before running requests could claim decode tokens",
          "FlashAttention kernel failure"
        ],
        1,
        "New requests claimed available concurrency slots, leaving running requests unable to schedule their single token and forcing unnecessary preemption."
      ],
      [
        "How does PR #58459 tune --long-prefill-token-threshold adaptively?",
        [
          "By rejecting long prompts",
          "By allowing larger prefill chunks when no concurrent decode requests are active, saturating the GPU",
          "By moving prompts to CPU"
        ],
        1,
        "When no active decodes exist, capping chunk sizes wastes GPU compute; adapting the threshold allows full tensor core saturation."
      ]
    ],
    "time": "90\u2013120 min",
    "tags": [
      "Case Study",
      "Issue #40004",
      "PR #45558"
    ],
    "badge": "SCHEDULER",
    "badgeClass": "scheduler"
  },
  {
    "id": "s3_1",
    "unit": "kvcache",
    "title": "PagedAttention: Virtual Memory for Transformers",
    "subtitle": "Eliminate memory fragmentation by mapping logical tokens to non-contiguous physical pages.",
    "objective": "Understand PagedAttention's virtual block tables and calculate memory fragmentation savings.",
    "question": "Why did legacy serving engines waste 60% to 80% of GPU memory, and how does PagedAttention eliminate internal and external fragmentation?",
    "definition": "Traditional engines allocated contiguous memory for max context length (e.g. 8,192 tokens), wasting space when sequences stopped early. PagedAttention allocates fixed physical blocks (e.g. 16 tokens) on demand.",
    "derive": "Requests maintain a logical block table mapping logical indices [0..15], [16..31] to arbitrary physical pages across VRAM, mirroring OS virtual memory.",
    "equation": "<div class=\"math-eq\"><span>Memory Waste: Legacy (60&ndash;80% Contiguous Waste) &rarr; PagedAttention (&lt; 4% Near-Zero Waste)</span></div>",
    "code": [
      "# vllm/v1/core/block_pool.py: Physical block allocation",
      "# Block size = 16 tokens",
      "logical_tokens = [0, 1, 2, ..., 47]  # 48 tokens = 3 blocks",
      "block_table = [4, 82, 19]  # Maps to physical pages 4, 82, 19 in VRAM",
      "print('Logical Block 0 -> Physical Page:', block_table[0])",
      "print('Logical Block 1 -> Physical Page:', block_table[1])",
      "print('Logical Block 2 -> Physical Page:', block_table[2])"
    ],
    "hint": "Only the final block of a sequence can suffer from internal fragmentation (at most block_size - 1 tokens).",
    "tasks": [
      "Open vllm/v1/core/block_pool.py and inspect BlockPool initialization.",
      "Verify how physical block sizes (16 vs 32) impact memory overhead and attention kernel efficiency.",
      "Calculate internal fragmentation percentage for a 17-token sequence using block_size=16."
    ],
    "readingTitle": "PagedAttention Research Paper (SOSP 2023)",
    "readingUrl": "https://arxiv.org/abs/2309.06180",
    "readingNote": "Read Section 3: PagedAttention algorithm and virtual block table management.",
    "quiz": [
      [
        "What is internal fragmentation in KV cache allocation?",
        [
          "Memory wasted between separate allocations in heap",
          "Memory reserved in the final block that is not occupied by valid tokens",
          "Memory used by model weights"
        ],
        1,
        "Internal fragmentation occurs only in the trailing block when the sequence length is not an exact multiple of the block size."
      ],
      [
        "How does PagedAttention access non-contiguous memory during attention?",
        [
          "By copying blocks into a contiguous buffer before attention",
          "Attention kernels take the block table array directly and look up physical page pointers per block",
          "By using CPU RAM"
        ],
        1,
        "PagedAttention CUDA kernels take the block table tensor directly, fetching K and V values from arbitrary physical pages on the fly."
      ]
    ],
    "time": "90\u2013120 min",
    "tags": [
      "Architecture",
      "PagedAttention",
      "Virtual Memory"
    ],
    "badge": "KV CACHE",
    "badgeClass": "kvcache"
  },
  {
    "id": "s3_2",
    "unit": "kvcache",
    "title": "Cryptographic 64-Bit Rolling Hash & Prefix Trees",
    "subtitle": "Discover how vLLM automatically detects shared system prompts across users in O(1) time.",
    "objective": "Derive rolling block hashes and trace prefix cache hits across independent requests.",
    "question": "When millions of users ask questions starting with the same 1,000-token system prompt, how does vLLM reuse those activations without recomputing them?",
    "definition": "Each completed block of tokens is hashed using a rolling 64-bit cryptographic hash chain. If a matching hash exists in cached_block_hash_to_block, the engine reuses the physical block instantly.",
    "derive": "H_0 = Initial_Salt; H_i = Hash(H_{i-1}, Tokens_i, ExtraKeys). ExtraKeys includes multimodal embeddings, LoRA IDs, and cache salts to avoid collisions across different models.",
    "equation": "<div class=\"math-eq\"><span>H<sub>i</sub> = Hash(H<sub>i-1</sub>, Tokens<sub>i</sub>, ExtraKeys) &nbsp;&rarr;&nbsp; cached_block_hash_to_block[H<sub>i</sub>]</span></div>",
    "code": [
      "# vllm/v1/core/kv_cache_utils.py: Rolling hash calculation",
      "def hash_block(prev_hash: int, token_ids: tuple, extra_keys: tuple) -> int:",
      "    # 64-bit rolling hash combining previous block hash with current tokens",
      "    return hash((prev_hash, token_ids, extra_keys)) & 0xFFFFFFFFFFFFFFFF"
    ],
    "hint": "Because H_i depends on H_{i-1}, block hashes form an implicit prefix tree without needing an explicit tree data structure.",
    "tasks": [
      "Open vllm/v1/core/kv_cache_utils.py and find hash_block().",
      "Trace how extra_keys ensures that two requests with different LoRA adapters do not collide.",
      "Write a short Python test verifying that altering one token in block 1 changes the hash of block 2."
    ],
    "readingTitle": "vllm/v1/core/kv_cache_utils.py \u00b7 Local Source",
    "readingUrl": "file:///Users/aravindsundaresan/Open_Source/vLLMs/vllm_src/vllm/v1/core/kv_cache_utils.py",
    "readingNote": "Inspect how multimodal features and cache salts are factored into block hash calculations.",
    "quiz": [
      [
        "Why must the hash of block i include the hash of block i-1?",
        [
          "To make the hash 128-bit",
          "To guarantee that the prefix sequence leading up to block i is identical (hash chaining)",
          "To avoid using Python hash functions"
        ],
        1,
        "Hash chaining ensures that a block is only considered a cache hit if all preceding blocks in the sequence match as well."
      ],
      [
        "What is the computational latency of a prefix cache hit?",
        [
          "Equal to standard prefill",
          "0 ms forward compute (instant physical block reuse)",
          "50 ms memory transfer"
        ],
        1,
        "The engine skips the forward attention pass for all cached prefix blocks, saving 100% of the compute for those tokens."
      ]
    ],
    "time": "60\u201390 min",
    "tags": [
      "Derive",
      "64-Bit Hash",
      "Prefix Tree"
    ],
    "badge": "KV CACHE",
    "badgeClass": "kvcache"
  },
  {
    "id": "s3_3",
    "unit": "kvcache",
    "title": "BlockPool Dual Queues: Reference Counting & LRU Ghost Hits",
    "subtitle": "Understand how blocks with ref_count == 0 remain queryable for future requests.",
    "objective": "Master BlockPool reference counting, LRU eviction queues, SWA bounded replay, and Mamba alignment (PR #60533).",
    "question": "When a request completes, why are its physical blocks NOT immediately wiped or unmapped?",
    "definition": "BlockPool maintains active blocks (ref_count > 0) and an LRU eviction queue (ref_count == 0). Blocks with ref_count == 0 remain indexed in the hash table, enabling 'ghost cache hits' for identical future queries.",
    "derive": "When memory is exhausted, blocks are popped from the head of free_block_queue and overwritten. When an identical prefix arrives, the block is resurrected: removed from free_block_queue and ref_count incremented.",
    "equation": "<div class=\"math-eq\"><span>ref_count &gt; 0: Active &nbsp;|&nbsp; ref_count == 0: LRU Eviction Queue (Queryable for Hits!)</span></div>",
    "code": [
      "# vllm/v1/core/block_pool.py: Resurrecting blocks from LRU",
      "def get_cached_block(self, block_hash: int) -> Optional[int]:",
      "    block_id = self.cached_block_hash_to_block.get(block_hash)",
      "    if block_id is not None:",
      "        if self.ref_counts[block_id] == 0:",
      "            # Resurrect block from eviction queue",
      "            self.free_block_queue.remove(block_id)",
      "        self.ref_counts[block_id] += 1",
      "        return block_id",
      "    return None"
    ],
    "hint": "Check PR #60533 in your local repo to see how hybrid Mamba state boundaries were aligned to block sizes.",
    "tasks": [
      "Open vllm/v1/core/block_pool.py and inspect free_block() and get_cached_block().",
      "Find git commit d8fa463e2 (PR #60533) and read how Mamba recurrent states interact with prefix caching.",
      "Simulate a scenario where 3 completed requests remain in the eviction queue and are reused by new queries."
    ],
    "readingTitle": "PR #60533: Fix inconsistent hybrid Mamba prefix cache boundaries",
    "readingUrl": "https://github.com/vllm-project/vllm/pull/60533",
    "readingNote": "Study how non-attention recurrent states require strict block alignment to prevent prefix state corruption.",
    "quiz": [
      [
        "What happens to a physical block when its ref_count drops to 0?",
        [
          "It is immediately overwritten with zeros",
          "It is placed into free_block_queue but remains queryable in the hash table for future hits",
          "It is freed to host CPU RAM"
        ],
        1,
        "The block enters the LRU eviction queue but stays in the hash table so subsequent requests can reuse it before it gets evicted."
      ],
      [
        "In Sliding Window Attention (SWA), what is bounded replay upon a prefix hit?",
        [
          "Recomputing the entire prompt from token 0",
          "Re-evaluating only the trailing W tokens of the window so attention state is restored",
          "Clearing the KV cache"
        ],
        1,
        "Because SWA layers only attend to the trailing W tokens, only those trailing tokens need to be present in active memory."
      ]
    ],
    "time": "90\u2013120 min",
    "tags": [
      "Code",
      "BlockPool",
      "LRU Eviction"
    ],
    "badge": "KV CACHE",
    "badgeClass": "kvcache"
  },
  {
    "id": "s4_1",
    "unit": "memory",
    "title": "VRAM Partitioning & The Profiling Equation",
    "subtitle": "Calculate exact physical KV cache capacity before launching the server.",
    "objective": "Understand GPUWorker.determine_available_memory() and derive the VRAM partitioning equation.",
    "question": "How does vLLM know exactly how many physical KV blocks can fit in VRAM without crashing into an Out-Of-Memory (OOM) error?",
    "definition": "Total VRAM is partitioned into: Model Weights + Peak Activation Workspace + CUDA Graphs + Safety Headroom. All remaining bytes are dedicated to the physical KV cache BlockPool.",
    "derive": "Rather than analytically guessing activation memory, GPUWorker executes a dummy forward pass during initialization with max_num_batched_tokens to empirically measure peak activation overhead.",
    "equation": "<div class=\"math-eq\"><span>Memory<sub>KV</sub> = (VRAM &times; util) &minus; Weights &minus; Peak<sub>Act</sub> &minus; CudaGraphs &minus; Headroom</span></div>",
    "code": [
      "# vllm/v1/worker/gpu_worker.py: Empirical profiling",
      "def determine_available_memory(self) -> int:",
      "    torch.cuda.empty_cache()",
      "    baseline = torch.cuda.memory_allocated()",
      "    # Run dummy forward pass with maximum batched token budget",
      "    dummy_input = self._create_dummy_input(self.max_num_batched_tokens)",
      "    with torch.no_grad():",
      "        self.model_runner.execute_model(dummy_input)",
      "    peak = torch.cuda.max_memory_allocated()",
      "    act_overhead = peak - baseline",
      "    usable = self.total_gpu_memory * self.gpu_memory_utilization",
      "    return usable - baseline - act_overhead"
    ],
    "hint": "Check the default gpu_memory_utilization setting (typically 0.90 or 0.95), leaving 5-10% headroom for driver memory.",
    "tasks": [
      "Open vllm/v1/worker/gpu_worker.py and locate determine_available_memory().",
      "Calculate how many 16-token blocks can fit in 30GB of available KV memory for Llama-3-8B.",
      "Explain why analytical formulas for activation memory often fail due to PyTorch allocator fragmentation."
    ],
    "readingTitle": "vllm/v1/worker/gpu_worker.py \u00b7 Local Source",
    "readingUrl": "file:///Users/aravindsundaresan/Open_Source/vLLMs/vllm_src/vllm/v1/worker/gpu_worker.py",
    "readingNote": "Inspect how determine_available_memory synchronizes CUDA devices before and after profiling.",
    "quiz": [
      [
        "Why does GPUWorker run a dummy forward pass during startup?",
        [
          "To warm up the GPU fans",
          "To empirically measure true peak activation workspace before allocating the KV cache pool",
          "To test the internet connection"
        ],
        1,
        "Empirical profiling captures the exact memory required by FlashAttention workspace, layer norms, and PyTorch tensors under maximum load."
      ],
      [
        "If available KV memory is 32 GB and each 16-token block requires 5 MB, how many blocks exist?",
        [
          "640 blocks",
          "6,553 blocks",
          "65,536 blocks"
        ],
        1,
        "32 GB = 32,768 MB. 32,768 / 5 \u2248 6,553 physical blocks."
      ]
    ],
    "time": "60\u201390 min",
    "tags": [
      "Derive",
      "VRAM Partitioning",
      "determine_available_memory"
    ],
    "badge": "MEMORY",
    "badgeClass": "memory"
  },
  {
    "id": "s4_2",
    "unit": "memory",
    "title": "The CPU Kernel Launch Bottleneck",
    "subtitle": "Discover why CPU driver overhead can waste 40% of total inference time during decoding.",
    "objective": "Quantify CPU kernel launch overhead and understand why decode passes require special optimization.",
    "question": "If generating a single token on an H100 GPU takes only 600 microseconds of GPU execution, why does standard PyTorch take over 1,000 microseconds per step?",
    "definition": "Each forward decode step launches dozens of tiny GPU kernels (layer norms, projections, attention, additions). Each CPU kernel launch incurs 3\u201310\u00b5s of driver overhead.",
    "derive": "For an 80-layer model launching 100 individual kernels: 100 * 5\u00b5s = 500\u00b5s CPU driver overhead. If GPU compute is 600\u00b5s, CPU overhead wastes almost half the step time!",
    "equation": "<div class=\"math-eq\"><span>T<sub>Total</sub> = T<sub>GPU_Compute</sub> (600 &mu;s) + &sum; T<sub>CPU_Launch</sub> (500 &mu;s) = 1,100 &mu;s</span></div>",
    "code": [
      "# Without CUDA Graphs: Repeated CPU driver kernel launches",
      "for layer in model.layers:",
      "    x = layer.input_layernorm(x)    # CPU launch: 5\u00b5s",
      "    q, k, v = layer.qkv_proj(x)      # CPU launch: 5\u00b5s",
      "    attn = layer.self_attn(q, k, v)  # CPU launch: 5\u00b5s",
      "    x = x + attn                     # CPU launch: 5\u00b5s",
      "    # 80 layers * 4 launches * 5\u00b5s = 1,600\u00b5s CPU overhead!"
    ],
    "hint": "CUDA Graphs pre-record the entire sequence of GPU launches so the CPU only has to issue a single call.",
    "tasks": [
      "Profile a standard PyTorch module in a loop using torch.cuda.Event and observe CPU launch vs GPU execution time.",
      "Verify why prefill passes do not suffer as heavily from launch overhead compared to decode passes.",
      "Read the NVIDIA CUDA Graphs programming documentation on graph capture."
    ],
    "readingTitle": "NVIDIA CUDA Graphs Programming Guide",
    "readingUrl": "https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#cuda-graphs",
    "readingNote": "Study the graph capture rules: fixed memory addresses, no CPU-GPU synchronization, and fixed stream dependencies.",
    "quiz": [
      [
        "Why is CPU launch latency a bottleneck for decode passes but less for prefill passes?",
        [
          "Decode passes use more parameters",
          "Prefill passes run for tens of milliseconds per kernel, dwarfing CPU launch overhead; decode kernels finish in microseconds",
          "Decode passes cannot use Tensor Cores"
        ],
        1,
        "In prefill, large GEMMs take milliseconds, so a 5\u00b5s launch overhead is negligible (<0.1%). In decode, tiny kernels finish in microseconds, making launch overhead significant."
      ],
      [
        "How much CPU launch latency does replaying a CUDA Graph introduce?",
        [
          "Over 500 microseconds",
          "Under 15 microseconds for the entire forward pass",
          "0 microseconds"
        ],
        1,
        "A CUDA Graph replay launches the entire pre-recorded sequence of hundreds of kernels in a single hardware driver call taking <15\u00b5s."
      ]
    ],
    "time": "60\u201390 min",
    "tags": [
      "Analysis",
      "CPU Driver Overhead",
      "Kernel Latency"
    ],
    "badge": "MEMORY",
    "badgeClass": "memory"
  },
  {
    "id": "s4_3",
    "unit": "memory",
    "title": "CUDA Graphs Architecture & Discrete Batch Buckets",
    "subtitle": "Pre-record forward execution for discrete batch sizes to eliminate CPU driver overhead.",
    "objective": "Understand CUDA graph capture buckets, padding trade-offs, and inspect cudagraph_utils.py.",
    "question": "CUDA Graphs require static tensor shapes and static memory addresses. How can vLLM use CUDA Graphs when dynamic batch sizes fluctuate between 1 and 128 requests?",
    "definition": "vLLM pre-captures discrete batch size buckets: B in {1, 2, 4, 8, 16, 24, 32, 48, 64, 96, 128}. Runtime batches are padded up to the nearest bucket, replaying the corresponding graph instantly.",
    "derive": "If 14 decode requests are active, the worker rounds up to bucket B=16, inserts 2 dummy padding slots, and replays the B=16 graph in <15\u00b5s. The tiny compute cost of 2 dummy slots is vastly smaller than saving 500\u00b5s of CPU launch overhead.",
    "equation": "<div class=\"math-eq\"><span>Runtime Batch (14) &rarr; Nearest Bucket B=16 &rarr; Replay Graph (&lt; 15 &mu;s)</span></div>",
    "code": [
      "# vllm/v1/worker/gpu/cudagraph_utils.py: Discrete buckets",
      "BATCH_SIZE_BUCKETS = [1, 2, 4, 8, 16, 24, 32, 48, 64, 96, 128]",
      "def get_graph_bucket(batch_size: int) -> int:",
      "    for bucket in BATCH_SIZE_BUCKETS:",
      "        if bucket >= batch_size:",
      "            return bucket",
      "    return -1  # Fall back to eager execution"
    ],
    "hint": "Check PR #54442 in your local repo to see how padding slots must be masked to prevent structured output sampling errors.",
    "tasks": [
      "Open vllm/v1/worker/gpu/cudagraph_utils.py and inspect CUDAGraphRunner.",
      "Find git commit 34c458d27 (PR #54442) and read how unmasked padding slots caused grammar errors.",
      "Calculate padding waste percentage when running batch size 65 with bucket 96."
    ],
    "readingTitle": "vllm/v1/worker/gpu/cudagraph_utils.py \u00b7 Local Source",
    "readingUrl": "file:///Users/aravindsundaresan/Open_Source/vLLMs/vllm_src/vllm/v1/worker/gpu/cudagraph_utils.py",
    "readingNote": "Study how input buffers and output logits are mapped into fixed virtual addresses during capture.",
    "quiz": [
      [
        "Why does vLLM use discrete buckets instead of capturing a graph for every integer from 1 to 128?",
        [
          "Capturing 128 graphs would consume gigabytes of VRAM and take minutes during startup",
          "PyTorch only supports 10 graphs",
          "Discrete buckets run faster"
        ],
        0,
        "Each captured CUDA Graph maintains its own private memory pool and execution plan. Capturing all 128 graphs would cause massive VRAM bloat."
      ],
      [
        "What did PR #54442 fix regarding padded CUDA Graph slots?",
        [
          "Kernel compilation crashes",
          "Preventing structured output grammars from sampling tokens from dummy padding rows",
          "Incorrect RoPE frequencies"
        ],
        1,
        "When padding slots to the nearest graph bucket, output logits from dummy rows must be properly sliced and masked so they never contaminate sampled tokens."
      ]
    ],
    "time": "90\u2013120 min",
    "tags": [
      "Code",
      "CUDA Graphs",
      "Batch Buckets"
    ],
    "badge": "MEMORY",
    "badgeClass": "memory"
  },
  {
    "id": "s5_1",
    "unit": "offloading",
    "title": "Hierarchical Storage Pyramid (HBM <-> CPU <-> RDMA <-> NVMe)",
    "subtitle": "Tier KV cache activations across memory layers when GPU VRAM fills up.",
    "objective": "Understand memory bandwidth pyramids and the trade-offs between swapping KV blocks vs recomputing.",
    "question": "When a long agent session with 32,000 tokens of context pauses waiting for a user reply, should its KV blocks stay in HBM, swap to CPU RAM, or be recomputed from scratch?",
    "definition": "Hierarchical tiering transfers inactive KV blocks across bandwidth tiers: GPU HBM (3,350 GB/s) -> Host CPU RAM (200-400 GB/s) -> RDMA / InfiniBand (50-100 GB/s) -> NVMe Flash (7-14 GB/s).",
    "derive": "Recomputing 32,000 tokens on Llama-3-70B takes ~1.5 seconds of dense GPU compute. Swapping 10GB of KV cache from CPU RAM over PCIe 5.0 (64 GB/s) takes ~150ms\u201410x faster than recomputing!",
    "equation": "<div class=\"math-eq\"><span>Bandwidth: HBM (3,350 GB/s) &gt; CPU RAM (300 GB/s) &gt; RDMA (100 GB/s) &gt; NVMe (10 GB/s)</span></div>",
    "code": [
      "# vllm/distributed/kv_transfer/kv_connector/v1/offloading/scheduler.py",
      "# Bandwidth comparison: PCIe 5.0 vs GPU recompute",
      "kv_bytes = 10 * (1024**3)  # 10 GB KV cache",
      "pcie_bandwidth = 64 * (1024**3)  # 64 GB/s PCIe 5.0 x16",
      "transfer_time_s = kv_bytes / pcie_bandwidth",
      "print(f'PCIe swap time: {transfer_time_s * 1000:.1f} ms')",
      "# Compare with ~1500 ms dense prompt recompute!"
    ],
    "hint": "Swapping is beneficial when prompt lengths are long; for very short prompts (<100 tokens), recomputing is faster than swapping.",
    "tasks": [
      "Open vllm/distributed/kv_transfer/kv_connector/v1/offloading/scheduler.py in your repo.",
      "Calculate the crossover prompt length where swapping over PCIe becomes faster than recomputing.",
      "Explain why NVMe storage is primarily suited for long-term agent session persistence rather than active decoding."
    ],
    "readingTitle": "vllm/distributed/kv_transfer/kv_connector/v1/offloading/scheduler.py",
    "readingUrl": "file:///Users/aravindsundaresan/Open_Source/vLLMs/vllm_src/vllm/distributed/kv_transfer/kv_connector/v1/offloading/scheduler.py",
    "readingNote": "Inspect how offloading scheduler coordinates swap-in and swap-out streams.",
    "quiz": [
      [
        "Why is swapping KV cache over PCIe 5.0 faster than recomputing for long contexts?",
        [
          "CPUs have faster tensor cores than GPUs",
          "Transferring precomputed KV bytes over 64GB/s PCIe takes ~150ms, whereas recomputing 32k tokens on 70B takes ~1500ms of GPU FLOPs",
          "PCIe has zero latency"
        ],
        1,
        "For long sequences, computing self-attention over tens of thousands of tokens takes substantial GPU time; streaming the raw activations from CPU memory is ~10x faster."
      ],
      [
        "Under what condition is recomputation preferable to swapping?",
        [
          "For massive 64k token prompts",
          "For very short prompts (e.g. <64 tokens) where transfer latency overhead exceeds compute time",
          "When the GPU has no HBM"
        ],
        1,
        "For tiny prompts, recomputing 20 tokens takes <2ms, making the driver setup and DMA transfer overhead not worth the effort."
      ]
    ],
    "time": "60\u201390 min",
    "tags": [
      "Hardware",
      "Storage Pyramid",
      "HBM vs PCIe"
    ],
    "badge": "DISAGGREGATION",
    "badgeClass": "disagg"
  },
  {
    "id": "s5_2",
    "unit": "offloading",
    "title": "Prefill / Decode Disaggregation (P/D Split Architecture)",
    "subtitle": "Separate compute-heavy prefill nodes from latency-critical decode nodes.",
    "objective": "Understand DistServe and Splitwise architectures and how vLLM streams KV activations between clusters.",
    "question": "Why does mixing prompt processing and token generation on the same GPU cause inter-token latency (TPOT) jitter, and how does P/D disaggregation fix it?",
    "definition": "Collocated serving causes decode requests to pause whenever a long prefill runs. Disaggregation dedicates high-compute nodes (optimized for throughput) to prefill and latency-optimized nodes to decode.",
    "derive": "Prefill nodes compute the prompt KV activations and stream them via high-speed RDMA (InfiniBand/RoCE) to decode nodes. Decode nodes maintain perfectly stable TPOT with zero interruption.",
    "equation": "<div class=\"math-eq\"><span>Prefill Nodes (Compute-Bound, High-TP) &rarr; RDMA &rarr; Decode Nodes (Memory-Bound, Low-TP, Stable TPOT)</span></div>",
    "code": [
      "# Architecture: Prefill / Decode Disaggregation",
      "# 1. Request arrives at Prefill Node",
      "#    - Computes initial 2,048 prompt tokens (FlashAttention)",
      "# 2. Prefill Node initiates RDMA write to Decode Node VRAM",
      "# 3. Decode Node admits request to running queue",
      "#    - Executes continuous single-token decodes (CUDA Graphs)"
    ],
    "hint": "Prefill nodes often use higher Tensor Parallelism (TP=8) to maximize FLOPs, while decode nodes use lower TP (TP=1 or TP=2) to minimize communication overhead.",
    "tasks": [
      "Read the DistServe paper abstract and Section 1 on latency SLO violations in collocated serving.",
      "Calculate how much RDMA bandwidth is needed to support 100 requests/sec with average prompt length 1,000 tokens on 70B.",
      "Compare the hardware requirements of a prefill cluster vs a decode cluster."
    ],
    "readingTitle": "DistServe: Disaggregating Prefill and Decode (OSDI 2024)",
    "readingUrl": "https://arxiv.org/abs/2401.09670",
    "readingNote": "Examine Figure 1 showing how prompt prefill bursts induce tail latency spikes in concurrent decode streams.",
    "quiz": [
      [
        "What is the primary operational benefit of Prefill/Decode disaggregation?",
        [
          "Lower hardware cost",
          "Eliminating TPOT latency spikes by preventing compute-heavy prefills from preempting active decode passes",
          "Removing the need for KV cache"
        ],
        1,
        "Disaggregating prefill and decode isolates user streaming latency from erratic prompt arrivals, guaranteeing SLA compliance."
      ],
      [
        "Why might prefill nodes use higher Tensor Parallelism (TP) than decode nodes?",
        [
          "Decode nodes don't support TP",
          "Prefill is compute-bound and benefits from distributing large GEMMs across many GPUs; decode is memory-bound and communication latency dominates",
          "Prefill uses FP8 only"
        ],
        1,
        "Large GEMMs scale well with TP. For decode (M=1), all-reduce communication latency quickly dominates, so lower TP is preferred."
      ]
    ],
    "time": "90\u2013120 min",
    "tags": [
      "Architecture",
      "P/D Split",
      "Disaggregation"
    ],
    "badge": "DISAGGREGATION",
    "badgeClass": "disagg"
  },
  {
    "id": "s5_3",
    "unit": "offloading",
    "title": "Async Transfer Pipeline & The RDMA Zeroing Race Fix (PR #59504)",
    "subtitle": "Coordinate non-blocking RDMA transfers and resolve subtle memory-corruption race conditions.",
    "objective": "Understand the 4-stage transfer state machine and PR #59504 memory zeroing race fix.",
    "question": "In GPUDirect RDMA transfers, how could a local memory-clearing security feature accidentally overwrite incoming prompt activations from a remote server?",
    "definition": "By default, BlockPool launches an asynchronous CUDA kernel to zero out allocated memory. When remote NICs write directly into GPU VRAM via GPUDirect RDMA, local zeroing can run concurrently or after the transfer, corrupting KV activations.",
    "derive": "PR #59504 resolved this race condition by explicitly flagging blocks targeted by an async KV load with skip_zeroing = True, ensuring DMA data integrity.",
    "equation": "<div class=\"math-eq\"><span>State Machine: WAITING_TO_START &rarr; IN_PROGRESS &rarr; COMPLETED_WAITING &rarr; RUNNING</span></div>",
    "code": [
      "# PR #59504: Exempt RDMA destination blocks from zeroing",
      "# vllm/distributed/kv_transfer/kv_connector/v1/offloading/scheduler.py",
      "class OffloadingScheduler:",
      "    def allocate_rdma_destination_blocks(self, req, block_ids):",
      "        # Crucial fix: DO NOT launch zeroing kernel on blocks receiving RDMA data!",
      "        self.block_pool.allocate_blocks(",
      "            block_ids,",
      "            skip_zeroing=True  # Fixes PR #59504 race condition",
      "        )"
    ],
    "hint": "Check git commit ca0df1f12 in your local repo to see PR #59504.",
    "tasks": [
      "Open vllm/distributed/kv_transfer/kv_connector/v1/offloading/scheduler.py.",
      "Find git commit ca0df1f12 (git show ca0df1f12) and inspect the exact lines modified in BlockPool and OffloadingScheduler.",
      "Trace the 4 states: WAITING_TO_START, IN_PROGRESS, COMPLETED_WAITING, and RUNNING."
    ],
    "readingTitle": "PR #59504: Exempt exactly the blocks an async KV load writes from zeroing",
    "readingUrl": "https://github.com/vllm-project/vllm/pull/59504",
    "readingNote": "Study the bug description detailing how asynchronous CUDA stream races caused NaNs and corrupted tokens in disaggregated setups.",
    "quiz": [
      [
        "What was the race condition fixed in PR #59504?",
        [
          "TCP socket disconnection",
          "Local asynchronous memory zeroing kernels executed concurrently or after GPUDirect RDMA writes, corrupting transferred KV activations",
          "CUDA graph execution failure"
        ],
        1,
        "Because GPUDirect RDMA writes bypass the local GPU stream, a concurrent or subsequent local zeroing kernel overwrote valid transferred KV cache data."
      ],
      [
        "What state does a request transition to once its RDMA KV transfer finishes?",
        [
          "WAITING_TO_START",
          "IN_PROGRESS",
          "COMPLETED_WAITING"
        ],
        2,
        "Once the network transfer completes, the request enters COMPLETED_WAITING, signaling to the scheduler that all KV blocks are present in local VRAM and ready to execute."
      ]
    ],
    "time": "90\u2013120 min",
    "tags": [
      "Bug Fix",
      "RDMA Race",
      "PR #59504"
    ],
    "badge": "DISAGGREGATION",
    "badgeClass": "disagg"
  }
];
const milestones = [
  {
    "id": "m1",
    "title": "Engine Core IPC & ZeroMQ Latency Benchmark",
    "phase": "After Paths 00\u201301",
    "requires": [
      "journey",
      "engine"
    ],
    "question": "Can you measure and prove why multiprocess ZeroMQ IPC with msgspec is faster than Python GIL threading or standard pickle?",
    "deliverables": [
      "A test script comparing serialization latency between pickle and msgspec.msgpack across 10,000 synthetic request payloads.",
      "A ZeroMQ ROUTER/DEALER round-trip latency benchmark measuring p50, p95, and p99 overhead in microseconds.",
      "An architectural note citing vllm/v1/engine/core.py and core_client.py explaining how input_thread prevents GPU bubbles."
    ]
  },
  {
    "id": "m2",
    "title": "Continuous Batching Scheduler Simulator",
    "phase": "After Path 02",
    "requires": [
      "scheduler"
    ],
    "question": "Can you implement a pure-Python simulator of vLLM v1's unified scheduler invariant and prove that running requests never get starved?",
    "deliverables": [
      "A Python discrete-event simulation tracking running, kv_holding_waiting, and waiting queues across 50 simulated requests.",
      "A test reproducing Issue #40004 where incoming prefills preempt running decodes, followed by your assertion proving PR #45558's phase separation prevents it.",
      "A graph or table showing Token-to-Token Latency (TPOT) variance under 512-token chunked prefill vs non-chunked prefill."
    ]
  },
  {
    "id": "m3",
    "title": "PagedAttention & Prefix Cache Hash Audit",
    "phase": "After Path 03",
    "requires": [
      "kvcache"
    ],
    "question": "Can you implement a 64-bit rolling hash prefix tree and verify that completed blocks deliver instant O(1) cache hits from the LRU eviction queue?",
    "deliverables": [
      "A standalone BlockPool implementation maintaining ref_counts and free_block_queue.",
      "A unit test demonstrating a completed request's blocks dropping to ref_count=0, entering the eviction queue, and being resurrected on an identical prompt.",
      "A written analysis of Sliding Window Attention (SWA) bounded replay and Mamba state alignment (PR #60533)."
    ]
  },
  {
    "id": "m4",
    "title": "CUDA Graph Batch Bucketing & VRAM Partitioning Lab",
    "phase": "After Path 04",
    "requires": [
      "memory"
    ],
    "question": "Can you calculate the exact KV cache capacity for a 70B parameter model on an 80GB H100 GPU and justify CUDA Graph padding overhead?",
    "deliverables": [
      "A mathematical notebook calculating available KV blocks given model weights, peak FlashAttention workspace, and CUDA Graph memory pools.",
      "A padding efficiency model comparing discrete bucket choices (e.g. step sizes of 8 vs powers of 2) against raw CPU kernel launch driver overhead.",
      "A code inspection report on determine_available_memory() in vllm/v1/worker/gpu_worker.py."
    ]
  },
  {
    "id": "m5",
    "title": "Prefill/Decode Disaggregation Capacity Planning",
    "phase": "After Path 05",
    "requires": [
      "offloading"
    ],
    "question": "Can you design a disaggregated serving cluster meeting an SLA of TTFT < 500ms and TPOT < 20ms using RDMA KV cache transfer?",
    "deliverables": [
      "A cluster sizing model balancing prefill nodes (high compute) and decode nodes (high bandwidth) for a specified prompt/decode workload distribution.",
      "A network bandwidth calculation specifying required InfiniBand/RoCE throughput to transfer KV blocks without pipeline bubbles.",
      "A case study analysis of PR #59504 explaining how local memory zeroing corrupted GPUDirect RDMA transfers and how it was resolved."
    ]
  }
];
const refs = [
  [
    "PagedAttention: Efficient Memory Management for LLM Serving",
    "Research Paper \u00b7 Woosuk Kwon et al. (SOSP 2023)",
    "https://arxiv.org/abs/2309.06180",
    "Foundational paper establishing non-contiguous physical block allocation and virtual memory paging for transformer KV activations."
  ],
  [
    "DistServe: Disaggregating Prefill and Decode for LLM Serving",
    "Research Paper \u00b7 Yinmin Zhong et al. (OSDI 2024)",
    "https://arxiv.org/abs/2401.09670",
    "Primary architectural reference for separating compute-heavy prompt prefill from latency-critical autoregressive decoding."
  ],
  [
    "Splitwise: Efficient Generative LLM Serving Using Phase Separation",
    "Research Paper \u00b7 Pratyush Patel et al. (ISCA 2024)",
    "https://arxiv.org/abs/2311.18677",
    "Analyzes hardware Roofline divergence between prompt prefill and token generation, establishing cluster disaggregation economics."
  ],
  [
    "FlashAttention-3: Fast and Accurate Attention with Asynchrony",
    "Research Paper \u00b7 Jay Shah et al. (2024)",
    "https://arxiv.org/abs/2407.08608",
    "Hardware-aware attention utilizing Hopper Tensor Core FP8/FP16 asynchrony and warp-specialized pipeline overlapping."
  ],
  [
    "ZeroMQ: An Introduction to Distributed Messaging",
    "Architecture Guide \u00b7 Pieter Hintjens",
    "https://zguide.zeromq.org/",
    "In-depth guide to ZeroMQ socket patterns (ROUTER/DEALER, PUSH/PULL) powering vLLM v1's multiprocess control and data plane."
  ],
  [
    "NVIDIA CUDA Graphs Programming Guide",
    "Technical Documentation \u00b7 NVIDIA",
    "https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#cuda-graphs",
    "Technical reference on defining, instantiating, and replaying CUDA graphs to bypass CPU driver kernel launch overhead."
  ],
  [
    "vLLM Local Repository (vllm_src)",
    "Local Codebase \u00b7 Branch study-vllm-v1-internals",
    "file:///Users/aravindsundaresan/Open_Source/vLLMs/vllm_src",
    "The active local source code containing v1 engine, scheduler, block pool, GPU worker, and offloading connector."
  ]
];
const courseArc = [
  {
    "title": "Request Ingress",
    "paths": "00 Lifecycle \u2192 Browser to EngineCore background process"
  },
  {
    "title": "Engine & IPC",
    "paths": "01 ZeroMQ ROUTER/DEALER \u2192 torch_shm zero-copy buffers"
  },
  {
    "title": "Continuous Batching",
    "paths": "02 Scheduler invariant N_comp \u2192 Priority queues & preemption"
  },
  {
    "title": "Memory Subsystem",
    "paths": "03 PagedAttention virtual tables \u2192 04 CUDA Graphs & Profiling"
  },
  {
    "title": "Distributed Scaling",
    "paths": "05 Storage tiers \u2192 Prefill/Decode disaggregation via RDMA"
  }
];

let currentView = 'dashboard';
let activeLessonId = null;
let activeLessonTab = 'learn';

// State Persistence (Local-first in browser)
const storageKey = 'vllm-lab-master-v1';
let state = {
  done: [],
  notes: {},
  scores: {},
  milestones: [],
  milestoneChecks: {},
  milestoneNotes: {},
  completedAt: {}
};

function loadState() {
  try {
    const saved = localStorage.getItem(storageKey);
    if (saved) state = Object.assign(state, JSON.parse(saved));
  } catch (e) {
    console.error('Failed to load local state', e);
  }
}

function saveState() {
  try {
    localStorage.setItem(storageKey, JSON.stringify(state));
  } catch (e) {
    console.error('Failed to save state to localStorage', e);
  }
}

function toast(msg) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('visible');
  setTimeout(() => el.classList.remove('visible'), 2400);
}

// =============================================================
// TAB 1: DASHBOARD (HOME PAGE & PROGRESS TRACKER)
// =============================================================
function renderDashboard() {
  const doneCount = state.done.filter(id => sessions.some(s => s.id === id)).length;
  const percent = Math.round((doneCount / sessions.length) * 100);
  const completedM = state.milestones.length;
  const nextSession = sessions.find(s => !state.done.includes(s.id)) || sessions[0];

  return `
    <!-- Hero Banner -->
    <section class="dashboard-hero">
      <div class="hero-tag">⚡ vLLM v1 Systems Lab &middot; Architecture Courseware</div>
      <h1>Core Engine &amp; Continuous Batching Scheduler</h1>
      <p>A graduate-level systems study: Trace request lifecycles from browser keystroke through ZeroMQ IPC, unified scheduler invariants, PagedAttention block tables, CUDA Graphs, and RDMA disaggregation.</p>
      
      <div class="hero-stats-row">
        <button class="hero-cta" id="dash-continue-btn">
          ${doneCount === 0 ? 'Start Courseware' : doneCount < sessions.length ? 'Continue Learning' : 'Review Architecture'} &rarr;
        </button>
        <div class="hero-meta-items">
          <span><b>6</b> Paths</span>
          <span><b>17</b> In-Depth Sessions</span>
          <span><b>5</b> Portfolio Labs</span>
          <span><b>5</b> Interactive Sandboxes</span>
        </div>
      </div>
    </section>

    <!-- Metrics Tracker Grid -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-icon blue">✓</div>
        <div class="metric-body">
          <strong>${doneCount} / ${sessions.length}</strong>
          <small>Sessions Completed</small>
          <div class="progress-bar-track">
            <div class="progress-bar-fill" style="width: ${percent}%"></div>
          </div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon emerald">↗</div>
        <div class="metric-body">
          <strong>${percent}%</strong>
          <small>Course Mastery Completion</small>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon purple">⚙</div>
        <div class="metric-body">
          <strong>${completedM} / ${milestones.length}</strong>
          <small>Milestone Labs Cleared</small>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon indigo">⚡</div>
        <div class="metric-body">
          <strong style="font-size:17px;color:#0284c7">study-vllm-v1</strong>
          <small>Active Codebase Branch</small>
        </div>
      </div>
    </div>

    <!-- Subsystem Paths Section -->
    <div class="section-head">
      <div>
        <h2>Learning Paths &middot; 6 Systems Subsystems</h2>
        <p>From the hardware Roofline divergence down to RDMA zeroing bypass.</p>
      </div>
      <button class="section-head-link" id="dash-view-curriculum-btn">View Full 17 Sessions &rarr;</button>
    </div>

    <div class="paths-grid">
      ${units.map(u => {
        const uSessions = sessions.filter(s => s.unit === u.id);
        const count = uSessions.filter(s => state.done.includes(s.id)).length;
        const isComplete = count === uSessions.length && uSessions.length > 0;
        return `
          <article class="path-card" data-dash-path="${u.id}">
            <div class="path-card-top">
              <span class="path-tag">PATH ${u.n} &middot; ${u.phase}</span>
              <span class="time-pill" style="${isComplete ? 'background:#ecfdf5;color:#059669;font-weight:700' : count > 0 ? 'background:#f0f9ff;color:#0284c7;font-weight:700' : ''}">
                ${isComplete ? '✓ Completed' : count > 0 ? `${count}/${uSessions.length} in progress` : 'Not started'}
              </span>
            </div>
            <h4>${u.title}</h4>
            <p>${u.desc}</p>
            <div class="path-card-bottom">
              <span>${uSessions.length} sessions</span>
              <strong>Open Path &rarr;</strong>
            </div>
          </article>
        `;
      }).join('')}
    </div>

    <!-- Execution Pipeline Arc -->
    <div class="section-head">
      <div>
        <h2>Architecture Execution Pipeline</h2>
        <p>The 5 sequential stages of request execution in vLLM v1.</p>
      </div>
    </div>

    <div class="architecture-arc">
      ${courseArc.map((a, i) => `
        <div class="arc-node">
          <div class="arc-node-num">0${i+1}</div>
          <strong>${a.title}</strong>
          <small>${a.paths}</small>
        </div>
      `).join('')}
    </div>

    <!-- Quick Action Launchers -->
    <div class="two-col-grid" style="margin-top:12px;">
      <article class="path-card" id="dash-goto-sandboxes" style="border-color:#bae6fd;background:linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%);">
        <div class="path-card-top">
          <span class="path-tag" style="color:#0284c7">INTERACTIVE SANDBOXES &middot; TAB 5</span>
          <span class="time-pill" style="background:#e0f2fe;color:#0369a1">5 Live Tools</span>
        </div>
        <h4>Hardware Rooflines, VRAM Sizers &amp; nano-vLLM</h4>
        <p>Test arithmetic intensity across H100/A100, calculate physical blocks for 70B models, simulate continuous batching timelines, and explore prefix trees.</p>
        <div class="path-card-bottom">
          <span>Interactive Calculators</span>
          <strong>Launch Sandboxes &rarr;</strong>
        </div>
      </article>

      <article class="path-card" id="dash-goto-milestones" style="border-color:#ede9fe;background:linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%);">
        <div class="path-card-top">
          <span class="path-tag" style="color:#7c3aed">PORTFOLIO LABS &middot; 5 MILESTONES</span>
          <span class="time-pill" style="background:#ede9fe;color:#6d28d9">${completedM} / ${milestones.length} Cleared</span>
        </div>
        <h4>Systems Milestone Deliverables</h4>
        <p>Demonstrate your mastery across the 4 pillars: Explain from memory, Derive equations, Implement with code assertions, and Critique failure modes.</p>
        <div class="path-card-bottom">
          <span>4-Pillar Mastery Standard</span>
          <strong style="color:#7c3aed">Open Milestone Labs &rarr;</strong>
        </div>
      </article>
    </div>
  `;
}

function attachDashboardListeners() {
  const nextSession = sessions.find(s => !state.done.includes(s.id)) || sessions[0];
  document.getElementById('dash-continue-btn').onclick = () => {
    activeLessonId = nextSession.id;
    activeLessonTab = 'learn';
    renderView('curriculum');
  };
  document.getElementById('dash-view-curriculum-btn').onclick = () => renderView('curriculum');
  document.getElementById('dash-goto-sandboxes').onclick = () => renderView('sandboxes');
  document.getElementById('dash-goto-milestones').onclick = () => renderView('milestones');

  document.querySelectorAll('[data-dash-path]').forEach(card => {
    card.onclick = () => {
      const pathId = card.dataset.dashPath;
      const firstInPath = sessions.find(s => s.unit === pathId) || sessions[0];
      activeLessonId = firstInPath.id;
      activeLessonTab = 'learn';
      renderView('curriculum');
    };
  });
}

// =============================================================
// TAB 2: COURSE CURRICULUM (THE 2-COLUMN HIGH-CLARITY CARD GRID)
// =============================================================
function renderCurriculum() {
  if (activeLessonId) {
    const s = sessions.find(x => x.id === activeLessonId) || sessions[0];
    const u = units.find(x => x.id === s.unit) || units[0];
    const isDone = state.done.includes(s.id);
    const unitSessions = sessions.filter(x => x.unit === u.id);
    const unitDone = unitSessions.filter(x => state.done.includes(x.id)).length;

    return `
      <!-- Breadcrumb Bar -->
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
        <button class="action-btn secondary" id="btn-back-curriculum">
          &larr; Back to Curriculum Grid
        </button>
        <button class="action-btn ${isDone ? 'secondary' : 'emerald'}" id="btn-toggle-session-done">
          ${isDone ? '✓ Completed (Click to undo)' : 'Mark Session Complete'}
        </button>
      </div>

      <!-- Banner -->
      <section class="dashboard-hero" style="padding:28px 34px;margin-bottom:24px;">
        <div class="hero-tag">PATH ${u.n} &middot; ${s.badge} &middot; ${s.time}</div>
        <h2>${s.title}</h2>
        <p style="margin-bottom:0">${s.subtitle}</p>
      </section>

      <!-- 2-Column Split: Content vs Sidebar -->
      <div class="lesson-layout">
        <section class="lesson-main">
          <!-- Lesson Sub-tabs -->
          <div class="lesson-tabs">
            <button class="lesson-tab-btn ${activeLessonTab === 'learn' ? 'active' : ''}" data-ltab="learn">Learn &amp; Inspect</button>
            <button class="lesson-tab-btn ${activeLessonTab === 'practice' ? 'active' : ''}" data-ltab="practice">Hands-On Practice</button>
            <button class="lesson-tab-btn ${activeLessonTab === 'quiz' ? 'active' : ''}" data-ltab="quiz">Knowledge Check</button>
            <button class="lesson-tab-btn ${activeLessonTab === 'notes' ? 'active' : ''}" data-ltab="notes">My Notes</button>
          </div>

          <div id="lesson-tab-body">
            ${renderLessonTabContent(s, activeLessonTab)}
          </div>
        </section>

        <!-- Sidebar -->
        <aside class="lesson-aside">
          <div class="aside-card">
            <h4>Session Outcome</h4>
            <p>${s.objective}</p>
            <div style="padding-top:12px;margin-top:12px;border-top:1px solid var(--border);display:flex;justify-content:space-between;font-size:12px;color:var(--ink-muted);">
              <span>Path Progress</span>
              <strong style="color:var(--ink)">${unitDone} / ${unitSessions.length}</strong>
            </div>
          </div>

          <div class="aside-card">
            <h4>Target Code &amp; Reading</h4>
            <a href="${s.readingUrl}" target="_blank" rel="noreferrer" class="section-head-link" style="font-size:12px;margin-bottom:6px;display:block">
              ${s.readingTitle} &rarr;
            </a>
            <p>${s.readingNote}</p>
          </div>

          <div class="aside-card">
            <h4>Systems Learning Loop</h4>
            <ol style="margin-top:8px;padding-left:18px;font-size:12px;color:var(--ink-secondary);line-height:1.65">
              <li>Hardware Roofline &amp; Flops</li>
              <li>Local Code Invariants</li>
              <li>Predict &amp; Check</li>
              <li>Retrieval Self-Check</li>
            </ol>
          </div>
        </aside>
      </div>
    `;
  }

  // 2-Column High-Clarity Card Grid
  return `
    <!-- Curriculum Hero -->
    <section class="dashboard-hero">
      <div class="hero-tag">CURRICULUM SYLLABUS</div>
      <h2>6 Learning Paths &middot; 17 In-Depth Systems Sessions</h2>
      <p>Trace vLLM v1 line-by-line across every critical subsystem: process boundaries, continuous batching scheduler loops, memory pools, and distributed connectors.</p>
    </section>

    <!-- 2-Column Session Grid -->
    <div class="curriculum-grid">
      ${sessions.map((s, idx) => {
        const isDone = state.done.includes(s.id);
        return `
          <article class="session-card" data-session-open="${s.id}">
            <div>
              <div class="session-card-header">
                <span class="subsystem-badge ${s.badgeClass}">
                  Session ${String(idx+1).padStart(2, '0')} &middot; ${s.badge}
                </span>
                ${isDone ? `
                  <span class="status-pill-done">✓ Done</span>
                ` : `
                  <span class="time-pill">${s.time}</span>
                `}
              </div>
              <h3 class="session-card-title">${s.title}</h3>
              <p class="session-card-desc">${s.subtitle}</p>
            </div>
            
            <div class="session-card-footer">
              <div class="session-tags-row">
                ${s.tags.map((t, tidx) => `<span>${t}</span>${tidx < s.tags.length - 1 ? '<span>&middot;</span>' : ''}`).join('')}
              </div>
              <span class="session-card-cta">
                Open session <span>&rarr;</span>
              </span>
            </div>
          </article>
        `;
      }).join('')}
    </div>
  `;
}

function renderLessonTabContent(s, tab) {
  if (tab === 'learn') {
    return `
      <div class="lead-question-box">${s.question}</div>

      <div class="callout-box">
        <strong>Core Systems Invariant:</strong>
        <p>${s.definition}</p>
      </div>

      <h3 style="font-size:16px;margin:22px 0 8px;">Hardware First Principles &amp; Derivations</h3>
      <p style="color:var(--ink-secondary);font-size:13.5px">${s.derive}</p>
      
      <div class="math-eq-card">${s.equation}</div>

      <h3 style="font-size:16px;margin:22px 0 8px;">Codebase Inspection</h3>
      <div class="code-box-card">
        <div class="code-box-header">
          <span>vLLM Source &middot; Python / C++</span>
          <span>study-vllm-v1-internals</span>
        </div>
        <pre>${s.code.join('\n').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>
      </div>

      <div class="predict-panel">
        <label>Predict Before Inspecting: What invariants must hold here, and what fails if memory is exhausted?</label>
        <textarea class="predict-textarea" id="predict-box" placeholder="Write your predictions and expected shapes before running..."></textarea>
        <div>
          <button class="hint-toggle-btn" id="btn-toggle-hint">Reveal Architectural Hint &rarr;</button>
          <div class="hint-box-content" id="hint-box">${s.hint}</div>
        </div>
      </div>

      <h3 style="font-size:16px;margin:22px 0 8px;">Independent Systems Tasks</h3>
      <ol style="margin:0;padding-left:20px;color:var(--ink-secondary);font-size:13px;line-height:1.65">
        ${s.tasks.map(t => `<li style="margin-bottom:6px">${t}</li>`).join('')}
      </ol>
    `;
  }

  if (tab === 'practice') {
    return `
      <h3 style="font-size:16px;margin-bottom:8px;">Hands-On Practice &amp; Repo Tracing</h3>
      <p style="color:var(--ink-muted);font-size:13px;margin-bottom:14px;">
        Open your local repository clone at <code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:12px;">/Users/aravindsundaresan/Open_Source/vLLMs/vllm_src</code> and inspect the relevant modules:
      </p>
      <ol style="padding-left:20px;color:var(--ink-secondary);font-size:13px;line-height:1.65;margin-bottom:20px;">
        ${s.tasks.map(t => `<li style="margin-bottom:6px">${t}</li>`).join('')}
      </ol>
      <div style="padding-top:16px;border-top:1px solid var(--border);">
        <h4 style="font-size:13px;text-transform:uppercase;color:var(--ink);letter-spacing:0.04em;margin-bottom:6px">Systems Reflection &amp; Bug Analysis</h4>
        <textarea class="predict-textarea" style="height:120px" id="practice-note-box" placeholder="Document what you verified in code, benchmark timings, or failure edge cases..."></textarea>
        <small style="color:var(--ink-dim)">Notes save automatically in this browser.</small>
      </div>
    `;
  }

  if (tab === 'quiz') {
    return `
      <h3 style="font-size:16px;margin-bottom:6px;">Knowledge Retrieval Check</h3>
      <p style="color:var(--ink-muted);font-size:13px;margin-bottom:16px;">Answer from memory to evaluate your conceptual mastery of invariants.</p>
      
      <form id="quiz-form">
        ${s.quiz.map((q, i) => `
          <div class="quiz-question-card">
            <p>${i + 1}. ${q[0]}</p>
            ${q[1].map((opt, j) => `
              <label class="quiz-choice-item">
                <input type="radio" name="q${i}" value="${j}">
                <span>${opt}</span>
              </label>
            `).join('')}
          </div>
        `).join('')}
        <button class="action-btn primary" type="submit" style="margin-top:10px">Check Answers</button>
      </form>
      <div id="quiz-result" class="quiz-feedback-box"></div>
    `;
  }

  if (tab === 'notes') {
    return `
      <h3 style="font-size:16px;margin-bottom:6px;">Personal Systems Notes</h3>
      <p style="color:var(--ink-muted);font-size:13px;margin-bottom:14px;">Synthesize the core invariants in your own words. Persistent across browser sessions.</p>
      <textarea class="predict-textarea" style="height:180px" id="session-note-box" placeholder="Write key takeaways, memory equations, or questions for further study..."></textarea>
      <small style="color:var(--ink-dim)">Saved automatically in this browser.</small>
    `;
  }
}

function attachCurriculumListeners() {
  if (activeLessonId) {
    document.getElementById('btn-back-curriculum').onclick = () => {
      activeLessonId = null;
      renderView('curriculum');
    };

    document.getElementById('btn-toggle-session-done').onclick = () => {
      if (state.done.includes(activeLessonId)) {
        state.done = state.done.filter(x => x !== activeLessonId);
        delete state.completedAt[activeLessonId];
      } else {
        state.done.push(activeLessonId);
        state.completedAt[activeLessonId] = new Date().toISOString().split('T')[0];
      }
      saveState();
      renderView('curriculum');
      toast('Session status updated.');
    };

    document.querySelectorAll('[data-ltab]').forEach(b => {
      b.onclick = () => {
        activeLessonTab = b.dataset.ltab;
        renderView('curriculum');
      };
    });

    if (activeLessonTab === 'learn') {
      const pBox = document.getElementById('predict-box');
      if (pBox) {
        pBox.value = state.notes[activeLessonId + '_predict'] || '';
        pBox.oninput = () => {
          state.notes[activeLessonId + '_predict'] = pBox.value;
          saveState();
        };
      }
      const hintBtn = document.getElementById('btn-toggle-hint');
      if (hintBtn) {
        hintBtn.onclick = () => {
          const h = document.getElementById('hint-box');
          h.classList.toggle('visible');
          hintBtn.textContent = h.classList.contains('visible') ? 'Hide Architectural Hint' : 'Reveal Architectural Hint →';
        };
      }
    }

    if (activeLessonTab === 'practice') {
      const prBox = document.getElementById('practice-note-box');
      if (prBox) {
        prBox.value = state.notes[activeLessonId + '_practice'] || '';
        prBox.oninput = () => {
          state.notes[activeLessonId + '_practice'] = prBox.value;
          saveState();
        };
      }
    }

    if (activeLessonTab === 'notes') {
      const nBox = document.getElementById('session-note-box');
      if (nBox) {
        nBox.value = state.notes[activeLessonId] || '';
        nBox.oninput = () => {
          state.notes[activeLessonId] = nBox.value;
          saveState();
        };
      }
    }

    if (activeLessonTab === 'quiz') {
      const form = document.getElementById('quiz-form');
      if (form) {
        form.onsubmit = (e) => {
          e.preventDefault();
          const s = sessions.find(x => x.id === activeLessonId);
          let score = 0;
          let feedback = [];
          s.quiz.forEach((q, i) => {
            const chosen = form.querySelector(`input[name="q${i}"]:checked`);
            if (chosen && parseInt(chosen.value) === q[2]) {
              score++;
              feedback.push(`<b style="color:#34d399">Q${i+1}: Correct!</b> &mdash; ${q[3]}`);
            } else {
              feedback.push(`<b style="color:#fbbf24">Q${i+1}: Review Invariant.</b> &mdash; ${q[3]}`);
            }
          });
          state.scores[activeLessonId] = score;
          saveState();
          const res = document.getElementById('quiz-result');
          res.style.display = 'block';
          res.innerHTML = `<strong>Your Score: ${score} / ${s.quiz.length}</strong><br><br>${feedback.join('<br><br>')}`;
          toast(`Knowledge Check: ${score}/${s.quiz.length}`);
        };
      }
    }
  } else {
    document.querySelectorAll('[data-session-open]').forEach(card => {
      card.onclick = () => {
        activeLessonId = card.dataset.sessionOpen;
        activeLessonTab = 'learn';
        renderView('curriculum');
      };
    });
  }
}

// =============================================================
// TAB 3: MILESTONE LABS (PORTFOLIO PROJECTS)
// =============================================================
function renderMilestones() {
  const criteria = [
    ['explain', 'Explain from memory', 'Explain the underlying hardware trade-offs and code architecture without referencing documentation.'],
    ['derive', 'Derive the equations', 'Derive the mathematical formulas (arithmetic intensity, memory bounds, or latency breakdown) by hand.'],
    ['implement', 'Implement and verify', 'Write a script or test harness with assertions that independently verify the subsystem\'s behavior.'],
    ['critique', 'Critique failure modes', 'Identify edge cases, race conditions, memory leaks, or starvation hazards in the design.']
  ];

  return `
    <section class="dashboard-hero">
      <div class="hero-tag" style="color:#c084fc;background:rgba(192,132,252,0.14);border-color:rgba(192,132,252,0.28)">
        PORTFOLIO LABS
      </div>
      <h2>5 Systems Milestone Deliverables</h2>
      <p>Demonstrate your systems engineering mastery: Explain from memory, Derive equations, Implement with code assertions, and Critique failure modes.</p>
    </section>

    <div class="two-col-grid">
      ${milestones.map(m => {
        const isComplete = state.milestones.includes(m.id);
        const checks = state.milestoneChecks[m.id] || {};
        const ready = m.requires.every(uid =>
          sessions.filter(s => s.unit === uid).every(s => state.done.includes(s.id))
        );
        return `
          <div class="milestone-card">
            <div>
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <span class="subsystem-badge engine">
                  ${m.phase}
                </span>
                <span class="time-pill" style="${isComplete ? 'background:#ecfdf5;color:#059669;font-weight:700' : ready ? 'background:#f0f9ff;color:#0284c7;font-weight:700' : ''}">
                  ${isComplete ? '✓ Completed' : ready ? 'Ready to Start' : 'Builds on prerequisites'}
                </span>
              </div>
              <h3 style="font-size:18px;margin-bottom:6px;">${m.title}</h3>
              <p style="font-size:13px;color:var(--ink-muted);line-height:1.55;margin-bottom:16px;">${m.question}</p>
              
              <h4 style="font-size:12px;text-transform:uppercase;color:var(--ink);letter-spacing:0.04em;margin-bottom:6px;">Deliverables:</h4>
              <ul style="padding-left:18px;font-size:12.5px;color:var(--ink-secondary);line-height:1.6;margin-bottom:18px;">
                ${m.deliverables.map(d => `<li style="margin-bottom:4px;">${d}</li>`).join('')}
              </ul>
            </div>

            <div style="padding-top:14px;border-top:1px solid var(--border);">
              <h4 style="font-size:12px;text-transform:uppercase;color:var(--ink);letter-spacing:0.04em;margin-bottom:8px;">4-Pillar Mastery Standards:</h4>
              <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;">
                ${criteria.map(([k, label, desc]) => `
                  <label style="display:flex;align-items:flex-start;gap:8px;font-size:12px;color:var(--ink-secondary);cursor:pointer">
                    <input type="checkbox" data-mcheck="${m.id}" data-key="${k}" ${checks[k] ? 'checked' : ''} style="margin-top:3px;accent-color:var(--sub-engine)">
                    <span><b style="color:var(--ink)">${label}</b> &mdash; ${desc}</span>
                  </label>
                `).join('')}
              </div>

              <textarea class="predict-textarea" style="height:65px;margin-bottom:12px;" data-mnotes="${m.id}" placeholder="Save test script paths or benchmark notes...">${state.milestoneNotes[m.id] || ''}</textarea>

              <button class="action-btn ${isComplete ? 'secondary' : 'primary'}" data-mtoggle="${m.id}" style="width:100%;${!isComplete ? 'background:var(--sub-engine)' : ''}">
                ${isComplete ? '✓ Milestone Cleared (Undo)' : 'Mark Milestone Complete'}
              </button>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

function attachMilestonesListeners() {
  document.querySelectorAll('[data-mcheck]').forEach(box => {
    box.onchange = () => {
      const mId = box.dataset.mcheck;
      const key = box.dataset.key;
      state.milestoneChecks[mId] = state.milestoneChecks[mId] || {};
      state.milestoneChecks[mId][key] = box.checked;
      saveState();
      toast('Rubric saved.');
    };
  });

  document.querySelectorAll('[data-mnotes]').forEach(area => {
    area.oninput = () => {
      const mId = area.dataset.mnotes;
      state.milestoneNotes[mId] = area.value;
      saveState();
    };
  });

  document.querySelectorAll('[data-mtoggle]').forEach(btn => {
    btn.onclick = () => {
      const mId = btn.dataset.mtoggle;
      if (state.milestones.includes(mId)) {
        state.milestones = state.milestones.filter(x => x !== mId);
      } else {
        state.milestones.push(mId);
      }
      saveState();
      renderView('milestones');
      toast('Milestone status updated.');
    };
  });
}

// =============================================================
// TAB 4: ARCHITECTURAL REFERENCE SHELF
// =============================================================
function renderReferences() {
  return `
    <section class="dashboard-hero">
      <div class="hero-tag">SYSTEMS LIBRARY</div>
      <h2>Architectural Reference Shelf</h2>
      <p>Primary research papers, official documentation, and local source repositories informing vLLM v1.</p>
    </section>

    <div class="two-col-grid">
      ${refs.map((r, i) => `
        <div class="reference-card">
          <div style="margin-bottom:14px;">
            <div style="margin-bottom:10px;">
              <span class="subsystem-badge kvcache">
                ${String(i + 1).padStart(2, '0')} &middot; ${r[1]}
              </span>
            </div>
            <h3 style="font-size:17px;margin-bottom:6px;">${r[0]}</h3>
            <p style="font-size:13px;color:var(--ink-secondary);line-height:1.55;">${r[3]}</p>
          </div>
          <div style="padding-top:12px;border-top:1px solid var(--border);">
            <a href="${r[2]}" target="_blank" rel="noreferrer" class="section-head-link" style="font-size:13px">
              Open Resource &rarr;
            </a>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

// =============================================================
// TAB 5: INTERACTIVE SANDBOXES (AT THE END AS REQUESTED)
// =============================================================
const GPU_SPECS = {
  h100: { name: 'NVIDIA H100 SXM (Hopper)', tflops: 3350, bandwidth_gb: 3350, ridge: 1000 },
  a100: { name: 'NVIDIA A100 SXM (Ampere)', tflops: 312, bandwidth_gb: 2000, ridge: 156 },
  l40s: { name: 'NVIDIA L40S (Ada Lovelace)', tflops: 366, bandwidth_gb: 864, ridge: 423 },
  b200: { name: 'NVIDIA B200 (Blackwell)', tflops: 9000, bandwidth_gb: 8000, ridge: 1125 }
};

function calculateRoofline(gpuKey, mode, batchSize, seqLen) {
  const gpu = GPU_SPECS[gpuKey];
  const weightsBytes = 140 * 1e9;
  const L = 80, N_kv = 8, D = 128, P = 2;
  const kvBytesPerToken = 2 * L * N_kv * D * P;

  let flops = 0, bytes = 0;
  if (mode === 'prefill') {
    flops = 2 * 70e9 * batchSize * seqLen;
    bytes = weightsBytes + (kvBytesPerToken * batchSize * seqLen);
  } else {
    flops = 2 * 70e9 * batchSize * 1;
    bytes = weightsBytes + (kvBytesPerToken * batchSize * seqLen);
  }

  const intensity = flops / Math.max(bytes, 1);
  const isComputeBound = intensity >= gpu.ridge;
  const maxFlopsFromBandwidth = intensity * (gpu.bandwidth_gb * 1e9);
  const achievableFlops = Math.min(gpu.tflops * 1e12, maxFlopsFromBandwidth);
  const achievableTFlops = achievableFlops / 1e12;
  const saturationPct = Math.min(100, Math.round((achievableTFlops / gpu.tflops) * 100));

  return { gpu, intensity, isComputeBound, achievableTFlops, saturationPct };
}

function renderRooflineSVG(res) {
  const { gpu, intensity, isComputeBound, achievableTFlops } = res;
  const width = 540, height = 200, pad = 40;
  const mapX = (val) => pad + (Math.log10(Math.max(1, Math.min(10000, val))) / 4) * (width - 2 * pad);
  const mapY = (val) => (height - pad) - ((Math.log10(Math.max(10, Math.min(10000, val))) - 1) / 3) * (height - 2 * pad);

  const ridgeX = mapX(gpu.ridge);
  const ceilingY = mapY(gpu.tflops);
  const startX = mapX(1);
  const startY = mapY(Math.max(10, (1 * gpu.bandwidth_gb) / 1000));
  const endX = mapX(10000);

  const dotX = mapX(intensity);
  const dotY = mapY(achievableTFlops);

  return `
    <svg viewBox="0 0 ${width} ${height}">
      <defs>
        <radialGradient id="dotGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#38bdf8" stop-opacity="1"/>
          <stop offset="100%" stop-color="#38bdf8" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="#334155" stroke-width="1.5"/>
      <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="#334155" stroke-width="1.5"/>

      <polyline points="${startX},${startY} ${ridgeX},${ceilingY} ${endX},${ceilingY}"
        fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-linejoin="round"/>

      <line x1="${ridgeX}" y1="${ceilingY}" x2="${ridgeX}" y2="${height - pad}" stroke="#64748b" stroke-dasharray="3,3"/>
      <text x="${ridgeX}" y="${height - pad + 15}" fill="#94a3b8" font-size="9" text-anchor="middle">Ridge: ${gpu.ridge} FLOPs/B</text>

      <circle cx="${dotX}" cy="${dotY}" r="12" fill="url(#dotGlow)"/>
      <circle cx="${dotX}" cy="${dotY}" r="5" fill="#38bdf8" stroke="#fff" stroke-width="2"/>

      <text x="${width - pad}" y="${ceilingY - 8}" fill="#f59e0b" font-size="10" font-weight="bold" text-anchor="end">Peak: ${gpu.tflops} TFLOPs</text>
      <text x="${dotX}" y="${Math.max(20, dotY - 12)}" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">
        ${intensity.toFixed(1)} FLOPs/B (${isComputeBound ? 'Compute-Bound' : 'Memory-Bound'})
      </text>
      <text x="${width / 2}" y="${height - 8}" fill="#64748b" font-size="9" text-anchor="middle">Arithmetic Intensity [FLOPs / Byte] (Log Scale)</text>
      <text x="12" y="${height / 2}" fill="#64748b" font-size="9" text-anchor="middle" transform="rotate(-90 12,${height / 2})">Performance [TFLOPs]</text>
    </svg>
  `;
}

const MODEL_PROFILES = {
  'llama3-8b': { name: 'Llama-3-8B', layers: 32, kv_heads: 8, head_dim: 128, params_b: 8.0 },
  'llama3-70b': { name: 'Llama-3-70B', layers: 80, kv_heads: 8, head_dim: 128, params_b: 70.6 },
  'mistral-7b': { name: 'Mistral-7B', layers: 32, kv_heads: 8, head_dim: 128, params_b: 7.2 },
  'deepseek-v3': { name: 'DeepSeek-V3 (MoE)', layers: 61, kv_heads: 8, head_dim: 128, params_b: 37.0 }
};

function calculateVRAM(modelKey, precisionBytes, gpuVramGB, contextLen) {
  const m = MODEL_PROFILES[modelKey];
  const weightsGB = (m.params_b * precisionBytes);
  const peakActGB = Math.max(2.0, (m.params_b * 0.05));
  const cudaGraphsGB = 1.5;
  const headroomGB = gpuVramGB * 0.05;

  const usedNonKV = weightsGB + peakActGB + cudaGraphsGB + headroomGB;
  const availableKV_GB = Math.max(0, gpuVramGB - usedNonKV);

  const kvBytesPerToken = 2 * m.layers * m.kv_heads * m.head_dim * precisionBytes;
  const kvKBPerToken = kvBytesPerToken / 1024;
  const kvBytesPerSeq = kvBytesPerToken * contextLen;
  const kvGBPerSeq = kvBytesPerSeq / (1024 ** 3);

  const maxConcurrentStreams = Math.floor((availableKV_GB * (1024 ** 3)) / Math.max(1, kvBytesPerSeq));
  const blockSize = 16;
  const bytesPerBlock = kvBytesPerToken * blockSize;
  const totalPhysicalBlocks = Math.floor((availableKV_GB * (1024 ** 3)) / Math.max(1, bytesPerBlock));

  const pctWeights = Math.min(100, (weightsGB / gpuVramGB) * 100);
  const pctAct = Math.min(100, (peakActGB / gpuVramGB) * 100);
  const pctGraphs = Math.min(100, (cudaGraphsGB / gpuVramGB) * 100);
  const pctKV = Math.max(0, 100 - pctWeights - pctAct - pctGraphs - 5);

  return {
    weightsGB, peakActGB, cudaGraphsGB, availableKV_GB,
    kvKBPerToken, kvGBPerSeq, maxConcurrentStreams, totalPhysicalBlocks,
    pctWeights, pctAct, pctGraphs, pctKV
  };
}

// Timeline Simulator state
let timelineStep = 0;
const TIMELINE_STEPS = [
  { step: 1, desc: 'Step 1: Incoming requests arrive. Prefills start.', slots: ['P1', 'P1', 'P2', 'P2', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B'] },
  { step: 2, desc: 'Step 2: Req 1 & 2 enter decode. Req 3 arrives with 2k prompt.', slots: ['D1', 'D2', 'P3', 'P3', 'P3', 'P3', 'B', 'B', 'B', 'B', 'B', 'B'] },
  { step: 3, desc: 'Step 3: Chunked Prefill (v1): Req 3 chunk co-scheduled with D1 & D2 decodes.', slots: ['D1', 'D2', 'C3', 'C3', 'D1', 'D2', 'C3', 'C3', 'B', 'B', 'B', 'B'] },
  { step: 4, desc: 'Step 4: Disaggregated Serving: Prefills on Node A; Node B maintains flat TPOT!', slots: ['D1', 'D2', 'D3', 'D1', 'D2', 'D3', 'D1', 'D2', 'D3', 'D1', 'D2', 'D3'] }
];

// Nano-vLLM Stepper state
let nanoStepCount = 0;
let nanoBlocks = Array.from({ length: 16 }, (_, i) => ({ id: i, ref: 0, hash: null }));
let nanoRequests = [
  { id: 'Req-1', prompt: 'SysPrompt + UserA', status: 'Running', tokens: 18, blocks: [0, 1] },
  { id: 'Req-2', prompt: 'SysPrompt + UserB', status: 'Running', tokens: 18, blocks: [0, 2] },
  { id: 'Req-3', prompt: 'Long RAG Context', status: 'Waiting', tokens: 0, blocks: [] }
];

function stepNanoSim() {
  nanoStepCount++;
  nanoBlocks[0].ref = 2; // Shared system prompt block!
  nanoBlocks[0].hash = '0x8F3A';
  nanoBlocks[1].ref = 1;
  nanoBlocks[1].hash = '0x1A2B';
  nanoBlocks[2].ref = 1;
  nanoBlocks[2].hash = '0x9C8D';

  if (nanoStepCount >= 2) {
    nanoRequests[2].status = 'Running (Chunked Prefill)';
    nanoRequests[2].tokens = 16;
    nanoRequests[2].blocks = [3];
    nanoBlocks[3].ref = 1;
    nanoBlocks[3].hash = '0x44EE';
  }
  if (nanoStepCount >= 3) {
    nanoRequests[0].status = 'Finished (Blocks freed to LRU)';
    nanoBlocks[1].ref = 0; // Freed to LRU eviction queue
    nanoBlocks[0].ref = 1; // Req 2 still holds block 0
  }
}

function renderRadixTreeSVG() {
  return `
    <svg viewBox="0 0 540 180">
      <defs>
        <marker id="arrow" markerWidth="6" markerHeight="4" refX="6" refY="2" orient="auto"><polygon points="0 0, 6 2, 0 4" fill="#64748b"/></marker>
      </defs>
      <rect x="200" y="10" width="140" height="36" rx="6" fill="#1e1b4b" stroke="#818cf8" stroke-width="1.5"/>
      <text x="270" y="32" fill="#fff" font-size="10" font-weight="bold" text-anchor="middle">Root: System Prompt</text>
      
      <path d="M 240 46 L 140 90" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>
      <rect x="70" y="90" width="140" height="34" rx="6" fill="#0f291e" stroke="#10b981" stroke-width="1.5"/>
      <text x="140" y="111" fill="#fff" font-size="9" font-weight="bold" text-anchor="middle">User A: Quicksort (O(1) Hit!)</text>

      <path d="M 300 46 L 400 90" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>
      <rect x="330" y="90" width="140" height="34" rx="6" fill="#0f291e" stroke="#10b981" stroke-width="1.5"/>
      <text x="400" y="111" fill="#fff" font-size="9" font-weight="bold" text-anchor="middle">User B: Mergesort (O(1) Hit!)</text>

      <path d="M 140 124 L 140 148" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>
      <rect x="70" y="148" width="140" height="26" rx="4" fill="#111827" stroke="#38bdf8" stroke-width="1"/>
      <text x="140" y="165" fill="#38bdf8" font-size="8.5" text-anchor="middle">Turn 2: "Now optimize space"</text>
    </svg>
  `;
}

function renderSandboxes() {
  const roof = calculateRoofline('h100', 'decode', 16, 4096);
  const vram = calculateVRAM('llama3-70b', 2, 80, 8192);

  return `
    <section class="dashboard-hero">
      <div class="hero-tag">INTERACTIVE SANDBOXES &middot; TAB 5</div>
      <h2>Hardware Rooflines, VRAM Sizers &amp; nano-vLLM</h2>
      <p>Test hardware limits, model VRAM footprints, step through continuous batching timelines, and simulate PagedAttention BlockPool algorithms.</p>
    </section>

    <div class="sandboxes-grid">
      <!-- 1. Roofline Explorer -->
      <article class="sandbox-card">
        <div class="sandbox-header">
          <div>
            <h3>1. Arithmetic Intensity &amp; Roofline Explorer</h3>
            <p>Prefill compute-bound ($I &gt;&gt; 100$) vs Decode memory-bound ($I &approx; 1$)</p>
          </div>
          <span class="subsystem-badge kvcache">ROOFLINE</span>
        </div>

        <div class="sim-controls-grid">
          <div class="sim-control-item">
            <label>Hardware Architecture</label>
            <select id="rf-gpu">
              <option value="h100" selected>NVIDIA H100 SXM (3,350 TFLOPs / 3.35 TB/s)</option>
              <option value="a100">NVIDIA A100 SXM (312 TFLOPs / 2.0 TB/s)</option>
              <option value="l40s">NVIDIA L40S (366 TFLOPs / 864 GB/s)</option>
              <option value="b200">NVIDIA B200 (9,000 TFLOPs / 8.0 TB/s)</option>
            </select>
          </div>
          <div class="sim-control-item">
            <label>Inference Phase</label>
            <select id="rf-mode">
              <option value="decode" selected>Autoregressive Decode (M = 1)</option>
              <option value="prefill">Prompt Prefill (M = Sequence Length)</option>
            </select>
          </div>
        </div>

        <div class="sim-controls-grid">
          <div class="sim-control-item">
            <label>Batch Size: <span id="rf-b-val">16</span></label>
            <input type="range" id="rf-b" min="1" max="128" value="16">
          </div>
          <div class="sim-control-item">
            <label>Sequence Length: <span id="rf-s-val">4096</span></label>
            <input type="range" id="rf-s" min="128" max="16384" step="128" value="4096">
          </div>
        </div>

        <div class="dark-chart-container" id="rf-svg-container">
          ${renderRooflineSVG(roof)}
        </div>

        <div class="sim-stats-banner" id="rf-stats">
          <div class="sim-stat-box">
            <span>Operational Regime</span>
            <strong style="color:${roof.isComputeBound ? '#0284c7' : '#d97706'}">
              ${roof.isComputeBound ? 'Compute-Bound' : 'Memory-Bound'}
            </strong>
          </div>
          <div class="sim-stat-box">
            <span>Arithmetic Intensity</span>
            <strong>${roof.intensity.toFixed(1)} FLOPs/B</strong>
          </div>
          <div class="sim-stat-box">
            <span>Achievable Speed</span>
            <strong>${roof.achievableTFlops.toFixed(1)} TFLOPs</strong>
          </div>
          <div class="sim-stat-box">
            <span>Bus Saturation</span>
            <strong>${roof.saturationPct}%</strong>
          </div>
        </div>
      </article>

      <!-- 2. VRAM Allocation Sizer -->
      <article class="sandbox-card">
        <div class="sandbox-header">
          <div>
            <h3>2. KV Cache &amp; VRAM Allocation Sizer</h3>
            <p>Calculate physical blocks and concurrency bounds</p>
          </div>
          <span class="subsystem-badge scheduler">VRAM SIZER</span>
        </div>

        <div class="sim-controls-grid">
          <div class="sim-control-item">
            <label>Model Architecture</label>
            <select id="vr-model">
              <option value="llama3-70b" selected>Llama-3-70B (80L, 8KV, 70B)</option>
              <option value="llama3-8b">Llama-3-8B (32L, 8KV, 8B)</option>
              <option value="mistral-7b">Mistral-7B (32L, 8KV, 7B)</option>
              <option value="deepseek-v3">DeepSeek-V3 MoE (61L, 8KV, 37B)</option>
            </select>
          </div>
          <div class="sim-control-item">
            <label>Precision Format</label>
            <select id="vr-prec">
              <option value="2" selected>FP16 / BF16 (2 bytes)</option>
              <option value="1">FP8 Native (1 byte - 2x Capacity!)</option>
              <option value="0.5">INT4 Compressed (0.5 byte)</option>
            </select>
          </div>
        </div>

        <div class="sim-controls-grid">
          <div class="sim-control-item">
            <label>Hardware VRAM</label>
            <select id="vr-vram">
              <option value="80" selected>80 GB (NVIDIA H100 / A100)</option>
              <option value="141">141 GB (NVIDIA H200)</option>
              <option value="48">48 GB (NVIDIA L40S)</option>
              <option value="24">24 GB (RTX 4090)</option>
            </select>
          </div>
          <div class="sim-control-item">
            <label>Context Length: <span id="vr-ctx-val">8,192</span></label>
            <input type="range" id="vr-ctx" min="512" max="32768" step="512" value="8192">
          </div>
        </div>

        <div class="vram-legend-row">
          <span><span class="legend-dot" style="background:#3b82f6"></span> Weights: <b id="vr-leg-w">${vram.weightsGB.toFixed(1)}GB</b></span>
          <span><span class="legend-dot" style="background:#f59e0b"></span> Activations: <b id="vr-leg-a">${vram.peakActGB.toFixed(1)}GB</b></span>
          <span><span class="legend-dot" style="background:#ec4899"></span> CUDA Graphs: <b id="vr-leg-g">${vram.cudaGraphsGB.toFixed(1)}GB</b></span>
          <span><span class="legend-dot" style="background:#10b981"></span> Usable KV: <b id="vr-leg-k">${vram.availableKV_GB.toFixed(1)}GB</b></span>
        </div>

        <div class="vram-bar" id="vr-bar">
          <div class="vram-slice weights" style="width: ${vram.pctWeights}%"></div>
          <div class="vram-slice act" style="width: ${vram.pctAct}%"></div>
          <div class="vram-slice graphs" style="width: ${vram.pctGraphs}%"></div>
          <div class="vram-slice kv" style="width: ${vram.pctKV}%"></div>
        </div>

        <div class="sim-stats-banner" id="vr-stats">
          <div class="sim-stat-box">
            <span>KV / Token</span>
            <strong>${vram.kvKBPerToken.toFixed(1)} KB</strong>
          </div>
          <div class="sim-stat-box">
            <span>KV / Sequence</span>
            <strong>${vram.kvGBPerSeq.toFixed(2)} GB</strong>
          </div>
          <div class="sim-stat-box">
            <span>Max Concurrency</span>
            <strong style="color:#059669">${vram.maxConcurrentStreams} streams</strong>
          </div>
          <div class="sim-stat-box">
            <span>Physical Blocks (16t)</span>
            <strong>${vram.totalPhysicalBlocks.toLocaleString()}</strong>
          </div>
        </div>
      </article>

      <!-- 3. Timeline Simulator (Full Width) -->
      <article class="sandbox-card full-width">
        <div class="sandbox-header">
          <div>
            <h3>3. Serving Architecture Timeline Comparison</h3>
            <p>From static batching bubbles to continuous chunked prefill and disaggregation</p>
          </div>
          <button class="action-btn secondary" id="btn-next-step">Step Forward &rarr;</button>
        </div>

        <p style="font-size:13px;color:var(--ink-secondary);font-weight:600;margin-bottom:12px;" id="timeline-desc">
          ${TIMELINE_STEPS[timelineStep].desc}
        </p>

        <div style="background:#090d16;padding:16px;border-radius:10px;border:1px solid #1e293b;display:flex;flex-direction:column;gap:10px;">
          <div style="display:flex;align-items:center;gap:12px;">
            <span style="width:150px;font-family:var(--font-mono);font-size:11px;color:#94a3b8;font-weight:600">1. Static Batching</span>
            <div style="flex:1;display:grid;grid-template-columns:repeat(12,1fr);gap:4px;font-family:var(--font-mono);font-size:9.5px;color:#fff;text-align:center">
              <div style="background:#3b82f6;border-radius:4px;padding:3px 0">P1</div>
              <div style="background:#3b82f6;border-radius:4px;padding:3px 0">P2</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#1e293b;border-radius:4px;padding:3px 0;color:#64748b;border:1px dashed #334155">Idle</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#1e293b;border-radius:4px;padding:3px 0;color:#64748b;border:1px dashed #334155">Idle</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#1e293b;border-radius:4px;padding:3px 0;color:#64748b;border:1px dashed #334155">Idle</div>
              <div style="background:#1e293b;border-radius:4px;padding:3px 0;color:#64748b;border:1px dashed #334155">Wait</div>
              <div style="background:#1e293b;border-radius:4px;padding:3px 0;color:#64748b;border:1px dashed #334155">Wait</div>
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:12px;">
            <span style="width:150px;font-family:var(--font-mono);font-size:11px;color:#94a3b8;font-weight:600">2. Continuous (v0)</span>
            <div style="flex:1;display:grid;grid-template-columns:repeat(12,1fr);gap:4px;font-family:var(--font-mono);font-size:9.5px;color:#fff;text-align:center">
              <div style="background:#3b82f6;border-radius:4px;padding:3px 0">P1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#3b82f6;border-radius:4px;padding:3px 0">P2</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
              <div style="background:#ef4444;border-radius:4px;padding:3px 0;font-weight:bold">Stall</div>
              <div style="background:#3b82f6;border-radius:4px;padding:3px 0">P3</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:12px;">
            <span style="width:150px;font-family:var(--font-mono);font-size:11px;color:#94a3b8;font-weight:600">3. Chunked Prefill (v1)</span>
            <div style="flex:1;display:grid;grid-template-columns:repeat(12,1fr);gap:4px;font-family:var(--font-mono);font-size:9.5px;color:#fff;text-align:center">
              <div style="background:#8b5cf6;border-radius:4px;padding:3px 0">C1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
              <div style="background:#8b5cf6;border-radius:4px;padding:3px 0">C1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
              <div style="background:#8b5cf6;border-radius:4px;padding:3px 0">C2</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
              <div style="background:#8b5cf6;border-radius:4px;padding:3px 0">C3</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D3</div>
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:12px;">
            <span style="width:150px;font-family:var(--font-mono);font-size:11px;color:#94a3b8;font-weight:600">4. Disaggregated (P/D)</span>
            <div style="flex:1;display:grid;grid-template-columns:repeat(12,1fr);gap:4px;font-family:var(--font-mono);font-size:9.5px;color:#fff;text-align:center">
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D3</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D3</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D3</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D1</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D2</div>
              <div style="background:#10b981;border-radius:4px;padding:3px 0">D3</div>
            </div>
          </div>
        </div>
      </article>

      <!-- 4. Nano-vLLM Stepper -->
      <article class="sandbox-card">
        <div class="sandbox-header">
          <div>
            <h3>4. In-Browser nano-vLLM Stepper</h3>
            <p>BlockPool physical pages, reference counters, and LRU eviction</p>
          </div>
          <button class="action-btn primary" id="btn-nano-step" style="font-size:12px;padding:7px 14px;">
            Step Engine (t = ${nanoStepCount})
          </button>
        </div>

        <div style="background:#090d16;padding:14px;border-radius:10px;border:1px solid #1e293b;">
          <div style="display:grid;grid-template-columns:repeat(8,1fr);gap:6px;margin-bottom:12px;">
            ${nanoBlocks.map(b => `
              <div style="padding:6px 2px;text-align:center;border-radius:4px;border:1px solid ${b.ref > 1 ? '#a855f7' : b.ref === 1 ? '#10b981' : '#334155'};background:${b.ref > 1 ? 'rgba(168,85,247,0.15)' : b.ref === 1 ? 'rgba(16,185,129,0.15)' : '#111827'}">
                <span style="display:block;font-size:10px;font-family:var(--font-mono);font-weight:700;color:#fff">B${b.id}</span>
                <span style="display:block;font-size:8px;color:#94a3b8">${b.ref > 0 ? `ref:${b.ref}` : 'free'}</span>
              </div>
            `).join('')}
          </div>
          <div style="font-size:11.5px;color:#cbd5e1;line-height:1.6">
            <span style="font-weight:700;color:#fff;display:block;margin-bottom:2px">Queue Status:</span>
            ${nanoRequests.map(r => `<div>&bull; <b style="color:#38bdf8">${r.id}</b>: ${r.status} (Blocks: ${JSON.stringify(r.blocks)})</div>`).join('')}
          </div>
        </div>
      </article>

      <!-- 5. Radix Tree / Prefix Caching DAG -->
      <article class="sandbox-card">
        <div class="sandbox-header">
          <div>
            <h3>5. Radix Tree &amp; Prefix Caching DAG</h3>
            <p>Visualizing 64-bit rolling hash matches across independent users</p>
          </div>
          <span class="subsystem-badge engine">PREFIX CACHE</span>
        </div>

        <div class="dark-chart-container">
          ${renderRadixTreeSVG()}
          <p style="font-size:11.5px;color:#94a3b8;margin-top:10px;line-height:1.55">
            <b style="color:#34d399">Zero-Compute Reuse ($0\text{ms}$):</b> When User A and User B share the root system prompt, the root block is retained in VRAM with <code>ref_count = 2</code>. Divergent tokens allocate only new physical pages.
          </p>
        </div>
      </article>
    </div>
  `;
}

function attachSandboxesListeners() {
  const updateRoof = () => {
    const gpu = document.getElementById('rf-gpu').value;
    const mode = document.getElementById('rf-mode').value;
    const b = parseInt(document.getElementById('rf-b').value);
    const s = parseInt(document.getElementById('rf-s').value);

    document.getElementById('rf-b-val').textContent = b;
    document.getElementById('rf-s-val').textContent = s;

    const res = calculateRoofline(gpu, mode, b, s);
    document.getElementById('rf-svg-container').innerHTML = renderRooflineSVG(res);
    document.getElementById('rf-stats').innerHTML = `
      <div class="sim-stat-box">
        <span>Operational Regime</span>
        <strong style="color:${res.isComputeBound ? '#0284c7' : '#d97706'}">
          ${res.isComputeBound ? 'Compute-Bound' : 'Memory-Bound'}
        </strong>
      </div>
      <div class="sim-stat-box">
        <span>Arithmetic Intensity</span>
        <strong>${res.intensity.toFixed(1)} FLOPs/B</strong>
      </div>
      <div class="sim-stat-box">
        <span>Achievable Speed</span>
        <strong>${res.achievableTFlops.toFixed(1)} TFLOPs</strong>
      </div>
      <div class="sim-stat-box">
        <span>Bus Saturation</span>
        <strong>${res.saturationPct}%</strong>
      </div>
    `;
  };

  ['rf-gpu', 'rf-mode', 'rf-b', 'rf-s'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.oninput = updateRoof;
  });

  const updateVRAM = () => {
    const model = document.getElementById('vr-model').value;
    const prec = parseFloat(document.getElementById('vr-prec').value);
    const vramGB = parseFloat(document.getElementById('vr-vram').value);
    const ctx = parseInt(document.getElementById('vr-ctx').value);

    document.getElementById('vr-ctx-val').textContent = ctx.toLocaleString();

    const res = calculateVRAM(model, prec, vramGB, ctx);
    document.getElementById('vr-leg-w').textContent = res.weightsGB.toFixed(1) + 'GB';
    document.getElementById('vr-leg-a').textContent = res.peakActGB.toFixed(1) + 'GB';
    document.getElementById('vr-leg-g').textContent = res.cudaGraphsGB.toFixed(1) + 'GB';
    document.getElementById('vr-leg-k').textContent = res.availableKV_GB.toFixed(1) + 'GB';

    document.getElementById('vr-bar').innerHTML = `
      <div class="vram-slice weights" style="width: ${res.pctWeights}%"></div>
      <div class="vram-slice act" style="width: ${res.pctAct}%"></div>
      <div class="vram-slice graphs" style="width: ${res.pctGraphs}%"></div>
      <div class="vram-slice kv" style="width: ${res.pctKV}%"></div>
    `;

    document.getElementById('vr-stats').innerHTML = `
      <div class="sim-stat-box">
        <span>KV / Token</span>
        <strong>${res.kvKBPerToken.toFixed(1)} KB</strong>
      </div>
      <div class="sim-stat-box">
        <span>KV / Sequence</span>
        <strong>${res.kvGBPerSeq.toFixed(2)} GB</strong>
      </div>
      <div class="sim-stat-box">
        <span>Max Concurrency</span>
        <strong style="color:#059669">${res.maxConcurrentStreams} streams</strong>
      </div>
      <div class="sim-stat-box">
        <span>Physical Blocks (16t)</span>
        <strong>${res.totalPhysicalBlocks.toLocaleString()}</strong>
      </div>
    `;
  };

  ['vr-model', 'vr-prec', 'vr-vram', 'vr-ctx'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.oninput = updateVRAM;
  });

  document.getElementById('btn-next-step').onclick = () => {
    timelineStep = (timelineStep + 1) % TIMELINE_STEPS.length;
    document.getElementById('timeline-desc').textContent = TIMELINE_STEPS[timelineStep].desc;
    toast(`Timeline advanced to Step ${timelineStep + 1}`);
  };

  document.getElementById('btn-nano-step').onclick = () => {
    stepNanoSim();
    renderView('sandboxes');
    toast(`nano-vLLM stepped (t = ${nanoStepCount})`);
  };
}

// =============================================================
// MAIN ROUTER & APP INITIALIZATION
// =============================================================
function renderView(view) {
  currentView = view;
  document.querySelectorAll('.nav-tab-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.view === view);
  });

  const container = document.getElementById('view-container');
  if (view === 'dashboard') {
    container.innerHTML = renderDashboard();
    attachDashboardListeners();
  } else if (view === 'curriculum') {
    container.innerHTML = renderCurriculum();
    attachCurriculumListeners();
  } else if (view === 'milestones') {
    container.innerHTML = renderMilestones();
    attachMilestonesListeners();
  } else if (view === 'references') {
    container.innerHTML = renderReferences();
  } else if (view === 'sandboxes') {
    container.innerHTML = renderSandboxes();
    attachSandboxesListeners();
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.addEventListener('DOMContentLoaded', () => {
  loadState();
  document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    btn.onclick = () => {
      activeLessonId = null;
      renderView(btn.dataset.view);
    };
  });
  document.getElementById('brand-link').onclick = (e) => {
    e.preventDefault();
    activeLessonId = null;
    renderView('dashboard');
  };
  
  // Starting page: Dashboard!
  renderView('dashboard');
});
