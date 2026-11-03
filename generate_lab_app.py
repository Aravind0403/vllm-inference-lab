import json

# Load curriculum sessions and metadata from previous build
with open('/Users/aravindsundaresan/Documents/ChatGPT/vLLM_LMS/generate_app.py') as f:
    code = f.read()

# Extract units, courseArc, milestones, refs
import sys
sys.path.append('/Users/aravindsundaresan/Documents/ChatGPT/vLLM_LMS')
import generate_app
import build_full_lms

units = generate_app.units
courseArc = generate_app.courseArc
milestones = generate_app.milestones
refs = generate_app.refs
sessions = build_full_lms.sessions

print(f"Loaded {len(units)} units, {len(sessions)} sessions, {len(milestones)} milestones.")

app_js_header = f"""// vLLM Systems Lab & Interactive Courseware
// Inspired by vLLM v1, infra.bea.ai, and practice-first learning.

const units = {json.dumps(units, indent=2)};
const sessions = {json.dumps(sessions, indent=2)};
const milestones = {json.dumps(milestones, indent=2)};
const refs = {json.dumps(refs, indent=2)};

let currentView = 'simulators';
let activeLessonId = null;

// Persistent state
const storageKey = 'vllm-lab-state-v1';
let state = {{
  done: [],
  notes: {{}},
  scores: {{}},
  milestones: [],
  milestoneChecks: {{}}
}};

function loadState() {{
  try {{
    const saved = localStorage.getItem(storageKey);
    if (saved) state = Object.assign(state, JSON.parse(saved));
  }} catch (e) {{}}
}}

function saveState() {{
  try {{
    localStorage.setItem(storageKey, JSON.stringify(state));
  }} catch (e) {{}}
}}

function toast(msg) {{
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('visible');
  setTimeout(() => el.classList.remove('visible'), 2400);
}}

// -------------------------------------------------------------
// SIMULATOR 1: Roofline & Arithmetic Intensity Explorer
// -------------------------------------------------------------
const GPU_SPECS = {{
  h100: {{ name: 'NVIDIA H100 SXM (Hopper)', tflops: 3350, bandwidth_gb: 3350, ridge: 1000 }},
  a100: {{ name: 'NVIDIA A100 SXM (Ampere)', tflops: 312, bandwidth_gb: 2000, ridge: 156 }},
  l40s: {{ name: 'NVIDIA L40S (Ada Lovelace)', tflops: 366, bandwidth_gb: 864, ridge: 423 }},
  b200: {{ name: 'NVIDIA B200 (Blackwell)', tflops: 9000, bandwidth_gb: 8000, ridge: 1125 }}
}};

function calculateRoofline(gpuKey, mode, batchSize, seqLen) {{
  const gpu = GPU_SPECS[gpuKey];
  let flops = 0;
  let bytes = 0;

  // Assume 70B parameter model in FP16 (2 bytes per param = 140 GB weights)
  const weightsBytes = 140 * 1e9;
  const L = 80, N_kv = 8, D = 128, P = 2;
  const kvBytesPerToken = 2 * L * N_kv * D * P; // 327,680 B

  if (mode === 'prefill') {{
    // Prefill: M = seqLen, batch = batchSize
    // GEMMs: 2 * Params * B * S
    flops = 2 * (70e9) * batchSize * seqLen;
    // Reads weights once, writes KV cache
    bytes = weightsBytes + (kvBytesPerToken * batchSize * seqLen);
  }} else {{
    // Decode: M = 1, batch = batchSize
    // GEMVs: 2 * Params * B * 1
    flops = 2 * (70e9) * batchSize * 1;
    // Reads ALL weights + reads ALL prior KV cache for every sequence!
    const kvTotalBytes = kvBytesPerToken * batchSize * seqLen;
    bytes = weightsBytes + kvTotalBytes;
  }}

  const intensity = flops / Math.max(bytes, 1);
  const isComputeBound = intensity >= gpu.ridge;
  const maxFlopsFromBandwidth = intensity * (gpu.bandwidth_gb * 1e9);
  const achievableFlops = Math.min(gpu.tflops * 1e12, maxFlopsFromBandwidth);
  const achievableTFlops = achievableFlops / 1e12;
  const saturationPct = Math.min(100, Math.round((achievableTFlops / gpu.tflops) * 100));

  return {{ gpu, intensity, isComputeBound, achievableTFlops, saturationPct }};
}}

function renderRooflineSVG(res) {{
  const {{ gpu, intensity, isComputeBound, achievableTFlops }} = res;
  const width = 540, height = 200, pad = 40;

  // Log scale mapping
  // X: Intensity from 1 to 10,000 (log10: 0 to 4)
  // Y: TFLOPs from 10 to 10,000 (log10: 1 to 4)
  const mapX = (val) => pad + (Math.log10(Math.max(1, Math.min(10000, val))) / 4) * (width - 2 * pad);
  const mapY = (val) => (height - pad) - ((Math.log10(Math.max(10, Math.min(10000, val))) - 1) / 3) * (height - 2 * pad);

  const ridgeX = mapX(gpu.ridge);
  const ceilingY = mapY(gpu.tflops);
  const startX = mapX(1);
  const startY = mapY(Math.max(10, (1 * gpu.bandwidth_gb) / 1000));
  const endX = mapX(10000);

  // Operational dot position
  const dotX = mapX(intensity);
  const dotY = mapY(achievableTFlops);

  return `
    <svg viewBox="0 0 ${{width}} ${{height}}">
      <defs>
        <radialGradient id="dotGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#38bdf8" stop-opacity="1"/>
          <stop offset="100%" stop-color="#38bdf8" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <!-- Grid Lines -->
      <line x1="${{pad}}" y1="${{height - pad}}" x2="${{width - pad}}" y2="${{height - pad}}" stroke="#334155" stroke-width="1.5"/>
      <line x1="${{pad}}" y1="${{pad}}" x2="${{pad}}" y2="${{height - pad}}" stroke="#334155" stroke-width="1.5"/>

      <!-- Roofline path -->
      <polyline points="${{startX}},${{startY}} ${{ridgeX}},${{ceilingY}} ${{endX}},${{ceilingY}}"
        fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-linejoin="round"/>

      <!-- Ridge point marker -->
      <line x1="${{ridgeX}}" y1="${{ceilingY}}" x2="${{ridgeX}}" y2="${{height - pad}}" stroke="#64748b" stroke-dasharray="3,3"/>
      <text x="${{ridgeX}}" y="${{height - pad + 15}}" fill="#94a3b8" font-size="9" text-anchor="middle">Ridge: ${{gpu.ridge}} FLOPs/B</text>

      <!-- Operational Point Dot -->
      <circle cx="${{dotX}}" cy="${{dotY}}" r="12" fill="url(#dotGlow)"/>
      <circle cx="${{dotX}}" cy="${{dotY}}" r="5" fill="#38bdf8" stroke="#fff" stroke-width="2"/>

      <!-- Labels -->
      <text x="${{width - pad}}" y="${{ceilingY - 8}}" fill="#f59e0b" font-size="10" font-weight="bold" text-anchor="end">Peak: ${{gpu.tflops}} TFLOPs</text>
      <text x="${{dotX}}" y="${{Math.max(20, dotY - 12)}}" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">
        ${{intensity.toFixed(1)}} FLOPs/B (${{isComputeBound ? 'Compute-Bound' : 'Memory-Bound'}})
      </text>

      <text x="${{width / 2}}" y="${{height - 8}}" fill="#64748b" font-size="9" text-anchor="middle">Arithmetic Intensity [FLOPs / Byte] (Log Scale)</text>
      <text x="12" y="${{height / 2}}" fill="#64748b" font-size="9" text-anchor="middle" transform="rotate(-90 12,${{height / 2}})">Performance [TFLOPs]</text>
    </svg>
  `;
}}

// -------------------------------------------------------------
// SIMULATOR 2: KV Cache & VRAM Budgeting Sizer
// -------------------------------------------------------------
const MODEL_PROFILES = {{
  'llama3-8b': {{ name: 'Llama-3-8B', layers: 32, kv_heads: 8, head_dim: 128, params_b: 8.0 }},
  'llama3-70b': {{ name: 'Llama-3-70B', layers: 80, kv_heads: 8, head_dim: 128, params_b: 70.6 }},
  'mistral-7b': {{ name: 'Mistral-7B', layers: 32, kv_heads: 8, head_dim: 128, params_b: 7.2 }},
  'deepseek-v3': {{ name: 'DeepSeek-V3 (MoE)', layers: 61, kv_heads: 8, head_dim: 128, params_b: 37.0 }}
}};

function calculateVRAM(modelKey, precisionBytes, gpuVramGB, contextLen) {{
  const m = MODEL_PROFILES[modelKey];
  const weightsGB = (m.params_b * precisionBytes);
  const peakActGB = Math.max(2.0, (m.params_b * 0.05)); // Empirical activation workspace
  const cudaGraphsGB = 1.5; // Fixed CUDA Graph memory pool
  const headroomGB = gpuVramGB * 0.05; // 5% safety margin

  const usedNonKV = weightsGB + peakActGB + cudaGraphsGB + headroomGB;
  const availableKV_GB = Math.max(0, gpuVramGB - usedNonKV);

  // KV cache per token = 2 * L * N_kv * D * P
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

  return {{
    weightsGB, peakActGB, cudaGraphsGB, availableKV_GB,
    kvKBPerToken, kvGBPerSeq, maxConcurrentStreams, totalPhysicalBlocks,
    pctWeights, pctAct, pctGraphs, pctKV
  }};
}}

// -------------------------------------------------------------
// SIMULATOR 3: Interactive Timeline Simulator
// -------------------------------------------------------------
let timelineStep = 0;
const TIMELINE_STEPS = [
  {{ step: 1, desc: 'Incoming requests arrive at engine. Prefills start.', slots: ['P1', 'P1', 'P2', 'P2', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B'] }},
  {{ step: 2, desc: 'Req 1 & 2 complete prefill. Req 3 arrives with long prompt.', slots: ['D1', 'D2', 'P3', 'P3', 'P3', 'P3', 'B', 'B', 'B', 'B', 'B', 'B'] }},
  {{ step: 3, desc: 'Chunked Prefill active: Req 3 chunk 1 co-scheduled with D1 and D2.', slots: ['D1', 'D2', 'C3', 'C3', 'D1', 'D2', 'C3', 'C3', 'B', 'B', 'B', 'B'] }},
  {{ step: 4, desc: 'Disaggregated Serving: Prefills on Node A; Node B achieves flat, perfect TPOT!', slots: ['D1', 'D2', 'D3', 'D1', 'D2', 'D3', 'D1', 'D2', 'D3', 'D1', 'D2', 'D3'] }}
];

// -------------------------------------------------------------
// SIMULATOR 4: Nano-vLLM In-Browser Visualizer
// -------------------------------------------------------------
let nanoStepCount = 0;
let nanoBlocks = Array.from({{ length: 16 }}, (_, i) => ({{ id: i, ref: 0, hash: null }}));
let nanoRequests = [
  {{ id: 'Req-1', prompt: 'SysPrompt + UserA', status: 'Running', tokens: 18, blocks: [0, 1] }},
  {{ id: 'Req-2', prompt: 'SysPrompt + UserB', status: 'Running', tokens: 18, blocks: [0, 2] }},
  {{ id: 'Req-3', prompt: 'Long RAG Context', status: 'Waiting', tokens: 0, blocks: [] }}
];

function stepNanoSim() {{
  nanoStepCount++;
  // Simulate block allocation & hash sharing
  nanoBlocks[0].ref = 2; // Shared system prompt block!
  nanoBlocks[0].hash = '0x8F3A';
  nanoBlocks[1].ref = 1;
  nanoBlocks[1].hash = '0x1A2B';
  nanoBlocks[2].ref = 1;
  nanoBlocks[2].hash = '0x9C8D';

  if (nanoStepCount >= 2) {{
    // Req 3 admitted with chunked prefill
    nanoRequests[2].status = 'Running (Chunked Prefill)';
    nanoRequests[2].tokens = 16;
    nanoRequests[2].blocks = [3];
    nanoBlocks[3].ref = 1;
    nanoBlocks[3].hash = '0x44EE';
  }}
  if (nanoStepCount >= 3) {{
    // Req 1 finishes; block 1 freed to LRU (ref drops to 0, stays queryable!)
    nanoRequests[0].status = 'Finished (Blocks freed to LRU)';
    nanoBlocks[1].ref = 0;
    nanoBlocks[0].ref = 1; // Req 2 still holds block 0
  }}
}}

// -------------------------------------------------------------
// Main Render Views
// -------------------------------------------------------------
function renderSimulators() {{
  const roof = calculateRoofline('h100', 'decode', 16, 4096);
  const vram = calculateVRAM('llama3-70b', 2, 80, 8192);

  return `
    <section class="lab-hero">
      <span class="tag">INTERACTIVE INFERENCE SYSTEMS LAB</span>
      <h1>Hardware First Principles &amp; Scheduling Sandboxes</h1>
      <p>Inspired by <code>infra.bea.ai</code> and vLLM v1: Explore hardware Rooflines, VRAM partitioning, continuous batching timelines, and minimal engine execution step-by-step.</p>
    </section>

    <div class="sim-grid">
      <!-- Simulator 1: Roofline Explorer -->
      <article class="sim-card">
        <div class="sim-header">
          <div>
            <h3>1. Arithmetic Intensity &amp; Roofline Explorer</h3>
            <p>Compute-bound prefill ($I &gt;&gt; 100$) vs Memory-bandwidth bound decode ($I &approx; 1$)</p>
          </div>
          <span class="sim-badge">ROOFLINE</span>
        </div>

        <div class="control-row">
          <div class="control-group">
            <label>Target GPU Hardware</label>
            <select id="rf-gpu">
              <option value="h100" selected>NVIDIA H100 SXM (3,350 TFLOPs / 3.35 TB/s)</option>
              <option value="a100">NVIDIA A100 SXM (312 TFLOPs / 2.0 TB/s)</option>
              <option value="l40s">NVIDIA L40S (366 TFLOPs / 864 GB/s)</option>
              <option value="b200">NVIDIA B200 (9,000 TFLOPs / 8.0 TB/s)</option>
            </select>
          </div>
          <div class="control-group">
            <label>Inference Phase</label>
            <select id="rf-mode">
              <option value="decode" selected>Autoregressive Decode (M = 1)</option>
              <option value="prefill">Prompt Prefill (M = Sequence Length)</option>
            </select>
          </div>
        </div>

        <div class="control-row">
          <div class="control-group">
            <label>Batch Size: <span id="rf-b-val">16</span></label>
            <input type="range" id="rf-b" min="1" max="128" value="16">
          </div>
          <div class="control-group">
            <label>Sequence Length: <span id="rf-s-val">4096</span></label>
            <input type="range" id="rf-s" min="128" max="16384" step="128" value="4096">
          </div>
        </div>

        <div class="chart-box" id="rf-svg-container">
          ${{renderRooflineSVG(roof)}}
        </div>

        <div class="stat-banner" id="rf-stats">
          <div class="stat-item">
            <span>Operational Regime</span>
            <strong class="${{roof.isComputeBound ? 'highlight' : 'warning'}}">
              ${{roof.isComputeBound ? 'Compute-Bound' : 'Memory-Bandwidth Bound'}}
            </strong>
          </div>
          <div class="stat-item">
            <span>Arithmetic Intensity</span>
            <strong>${{roof.intensity.toFixed(2)}} FLOPs/B</strong>
          </div>
          <div class="stat-item">
            <span>Achievable Speed</span>
            <strong>${{roof.achievableTFlops.toFixed(1)}} TFLOPs</strong>
          </div>
          <div class="stat-item">
            <span>Bus Saturation</span>
            <strong>${{roof.saturationPct}}%</strong>
          </div>
        </div>
      </article>

      <!-- Simulator 2: KV Cache Sizer -->
      <article class="sim-card">
        <div class="sim-header">
          <div>
            <h3>2. KV Cache &amp; VRAM Budgeting Sizer</h3>
            <p>Empirical VRAM breakdown and PagedAttention capacity planning</p>
          </div>
          <span class="sim-badge">VRAM SIZER</span>
        </div>

        <div class="control-row">
          <div class="control-group">
            <label>Model Architecture</label>
            <select id="vr-model">
              <option value="llama3-70b" selected>Llama-3-70B (80L, 8KV, 70B Params)</option>
              <option value="llama3-8b">Llama-3-8B (32L, 8KV, 8B Params)</option>
              <option value="mistral-7b">Mistral-7B (32L, 8KV, 7B Params)</option>
              <option value="deepseek-v3">DeepSeek-V3 MoE (61L, 8KV, 37B Active)</option>
            </select>
          </div>
          <div class="control-group">
            <label>Precision Format</label>
            <select id="vr-prec">
              <option value="2" selected>FP16 / BF16 (2 bytes)</option>
              <option value="1">FP8 Native (1 byte - 2x Capacity!)</option>
              <option value="0.5">INT4 Compressed (0.5 byte)</option>
            </select>
          </div>
        </div>

        <div class="control-row">
          <div class="control-group">
            <label>GPU Hardware VRAM</label>
            <select id="vr-vram">
              <option value="80" selected>80 GB (NVIDIA H100 / A100)</option>
              <option value="141">141 GB (NVIDIA H200)</option>
              <option value="48">48 GB (NVIDIA L40S / A6000)</option>
              <option value="24">24 GB (RTX 4090 / 3090)</option>
            </select>
          </div>
          <div class="control-group">
            <label>Context Length: <span id="vr-ctx-val">8,192</span> tokens</label>
            <input type="range" id="vr-ctx" min="512" max="32768" step="512" value="8192">
          </div>
        </div>

        <div class="vram-legend">
          <span><span class="legend-dot" style="background:#3b82f6"></span> Weights: <b id="vr-leg-w">${{vram.weightsGB.toFixed(1)}}GB</b></span>
          <span><span class="legend-dot" style="background:#f59e0b"></span> Activations: <b id="vr-leg-a">${{vram.peakActGB.toFixed(1)}}GB</b></span>
          <span><span class="legend-dot" style="background:#ec4899"></span> CUDA Graphs: <b id="vr-leg-g">${{vram.cudaGraphsGB.toFixed(1)}}GB</b></span>
          <span><span class="legend-dot" style="background:#10b981"></span> Usable KV: <b id="vr-leg-k">${{vram.availableKV_GB.toFixed(1)}}GB</b></span>
        </div>

        <div class="vram-bar" id="vr-bar">
          <div class="vram-slice weights" style="width: ${{vram.pctWeights}}%"></div>
          <div class="vram-slice act" style="width: ${{vram.pctAct}}%"></div>
          <div class="vram-slice graphs" style="width: ${{vram.pctGraphs}}%"></div>
          <div class="vram-slice kv" style="width: ${{vram.pctKV}}%"></div>
        </div>

        <div class="stat-banner" id="vr-stats">
          <div class="stat-item">
            <span>KV Cache / Token</span>
            <strong>${{vram.kvKBPerToken.toFixed(1)}} KB</strong>
          </div>
          <div class="stat-item">
            <span>KV / Sequence</span>
            <strong>${{vram.kvGBPerSeq.toFixed(2)}} GB</strong>
          </div>
          <div class="stat-item">
            <span>Max Concurrency</span>
            <strong class="highlight">${{vram.maxConcurrentStreams}} streams</strong>
          </div>
          <div class="stat-item">
            <span>Physical Blocks (16t)</span>
            <strong>${{vram.totalPhysicalBlocks.toLocaleString()}} blocks</strong>
          </div>
        </div>
      </article>

      <!-- Simulator 3: Batching Timeline Comparison -->
      <article class="sim-card full-width">
        <div class="sim-header">
          <div>
            <h3>3. Serving Architecture Timeline Comparison</h3>
            <p>From static batching bubbles to continuous chunked prefill and disaggregation</p>
          </div>
          <div>
            <button class="action-btn secondary" id="btn-next-step">Step Forward &rarr;</button>
          </div>
        </div>

        <p style="font-size:12px;color:#94a3b8;margin:0 0 10px;" id="timeline-desc">
          ${{TIMELINE_STEPS[timelineStep].desc}}
        </p>

        <div class="timeline-track">
          <div class="track-row">
            <span class="track-label">1. Static Batching</span>
            <div class="slots-container">
              <div class="slot-block prefill">P1</div><div class="slot-block prefill">P2</div>
              <div class="slot-block decode">D1</div><div class="slot-block decode">D2</div>
              <div class="slot-block decode">D1</div><div class="slot-block bubble">Idle</div>
              <div class="slot-block decode">D1</div><div class="slot-block bubble">Idle</div>
              <div class="slot-block decode">D1</div><div class="slot-block bubble">Idle</div>
              <div class="slot-block bubble">Wait</div><div class="slot-block bubble">Wait</div>
            </div>
          </div>
          <div class="track-row">
            <span class="track-label">2. Continuous (v0)</span>
            <div class="slots-container">
              <div class="slot-block prefill">P1</div><div class="slot-block decode">D1</div>
              <div class="slot-block decode">D1</div><div class="slot-block decode">D1</div>
              <div class="slot-block prefill">P2</div><div class="slot-block decode">D2</div>
              <div class="slot-block decode">D1</div><div class="slot-block decode">D2</div>
              <div class="slot-block prefill">P3 (Stall!)</div><div class="slot-block prefill">P3</div>
              <div class="slot-block decode">D1</div><div class="slot-block decode">D2</div>
            </div>
          </div>
          <div class="track-row">
            <span class="track-label">3. Chunked Prefill (v1)</span>
            <div class="slots-container">
              <div class="slot-block chunk">C1</div><div class="slot-block decode">D2</div>
              <div class="slot-block chunk">C1</div><div class="slot-block decode">D2</div>
              <div class="slot-block chunk">C2</div><div class="slot-block decode">D1</div>
              <div class="slot-block decode">D1</div><div class="slot-block decode">D2</div>
              <div class="slot-block chunk">C3</div><div class="slot-block decode">D1</div>
              <div class="slot-block decode">D2</div><div class="slot-block decode">D3</div>
            </div>
          </div>
          <div class="track-row">
            <span class="track-label">4. Disaggregated (P/D)</span>
            <div class="slots-container">
              <div class="slot-block decode">D1</div><div class="slot-block decode">D2</div>
              <div class="slot-block decode">D3</div><div class="slot-block decode">D1</div>
              <div class="slot-block decode">D2</div><div class="slot-block decode">D3</div>
              <div class="slot-block decode">D1</div><div class="slot-block decode">D2</div>
              <div class="slot-block decode">D3</div><div class="slot-block decode">D1</div>
              <div class="slot-block decode">D2</div><div class="slot-block decode">D3</div>
            </div>
          </div>
        </div>
      </article>

      <!-- Simulator 4: Nano-vLLM Visual Stepper -->
      <article class="sim-card full-width">
        <div class="sim-header">
          <div>
            <h3>4. In-Browser nano-vLLM Stepper</h3>
            <p>Visualizing BlockPool virtual memory paging, reference counts, and prefix cache hits</p>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="action-btn" id="btn-nano-step">Step Engine (t = ${{nanoStepCount}})</button>
            <a class="action-btn secondary" href="nano_vllm.py" download style="text-decoration:none">Download nano_vllm.py</a>
          </div>
        </div>

        <div class="stepper-box">
          <p style="font-size:11px;color:#94a3b8;margin:0 0 8px;">
            Physical BlockPool Memory Pages (16 blocks total). Green: Active allocation; Purple: Cached prefix block (0ms compute hit!).
          </p>
          <div class="block-grid" id="nano-grid">
            ${{nanoBlocks.map(b => `
              <div class="block-cell ${{b.ref > 1 ? 'cached' : b.ref === 1 ? 'active' : ''}}">
                <strong>Block ${{b.id}}</strong>
                <small>${{b.ref > 0 ? `ref: ${{b.ref}}` : 'free LRU'}}</small>
                <small style="color:#a855f7">${{b.hash || ''}}</small>
              </div>
            `).join('')}}
          </div>

          <div style="margin-top:14px;font-size:12px;">
            <strong style="color:#fff">Scheduler Queues:</strong>
            <ul style="margin:6px 0;padding-left:18px;color:#94a3b8">
              ${{nanoRequests.map(r => `
                <li><b>${{r.id}}</b> &mdash; ${{r.prompt}} | Status: <span style="color:#38bdf8">${{r.status}}</span> | Physical Blocks: <code>${{JSON.stringify(r.blocks)}}</code></li>
              `).join('')}}
            </ul>
          </div>
        </div>
      </article>
    </div>
  `;
}}

function attachSimulatorListeners() {{
  const updateRoof = () => {{
    const gpu = document.getElementById('rf-gpu').value;
    const mode = document.getElementById('rf-mode').value;
    const b = parseInt(document.getElementById('rf-b').value);
    const s = parseInt(document.getElementById('rf-s').value);

    document.getElementById('rf-b-val').textContent = b;
    document.getElementById('rf-s-val').textContent = s;

    const res = calculateRoofline(gpu, mode, b, s);
    document.getElementById('rf-svg-container').innerHTML = renderRooflineSVG(res);
    document.getElementById('rf-stats').innerHTML = `
      <div class="stat-item">
        <span>Operational Regime</span>
        <strong class="${{res.isComputeBound ? 'highlight' : 'warning'}}">
          ${{res.isComputeBound ? 'Compute-Bound' : 'Memory-Bandwidth Bound'}}
        </strong>
      </div>
      <div class="stat-item">
        <span>Arithmetic Intensity</span>
        <strong>${{res.intensity.toFixed(2)}} FLOPs/B</strong>
      </div>
      <div class="stat-item">
        <span>Achievable Speed</span>
        <strong>${{res.achievableTFlops.toFixed(1)}} TFLOPs</strong>
      </div>
      <div class="stat-item">
        <span>Bus Saturation</span>
        <strong>${{res.saturationPct}}%</strong>
      </div>
    `;
  }};

  ['rf-gpu', 'rf-mode', 'rf-b', 'rf-s'].forEach(id => {{
    const el = document.getElementById(id);
    if (el) el.oninput = updateRoof;
  }});

  const updateVRAM = () => {{
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
      <div class="vram-slice weights" style="width: ${{res.pctWeights}}%"></div>
      <div class="vram-slice act" style="width: ${{res.pctAct}}%"></div>
      <div class="vram-slice graphs" style="width: ${{res.pctGraphs}}%"></div>
      <div class="vram-slice kv" style="width: ${{res.pctKV}}%"></div>
    `;

    document.getElementById('vr-stats').innerHTML = `
      <div class="stat-item">
        <span>KV Cache / Token</span>
        <strong>${{res.kvKBPerToken.toFixed(1)}} KB</strong>
      </div>
      <div class="stat-item">
        <span>KV / Sequence</span>
        <strong>${{res.kvGBPerSeq.toFixed(2)}} GB</strong>
      </div>
      <div class="stat-item">
        <span>Max Concurrency</span>
        <strong class="highlight">${{res.maxConcurrentStreams}} streams</strong>
      </div>
      <div class="stat-item">
        <span>Physical Blocks (16t)</span>
        <strong>${{res.totalPhysicalBlocks.toLocaleString()}} blocks</strong>
      </div>
    `;
  }};

  ['vr-model', 'vr-prec', 'vr-vram', 'vr-ctx'].forEach(id => {{
    const el = document.getElementById(id);
    if (el) el.oninput = updateVRAM;
  }});

  document.getElementById('btn-next-step').onclick = () => {{
    timelineStep = (timelineStep + 1) % TIMELINE_STEPS.length;
    document.getElementById('timeline-desc').textContent = TIMELINE_STEPS[timelineStep].desc;
    toast(`Timeline advanced to Step ${{timelineStep + 1}}`);
  }};

  document.getElementById('btn-nano-step').onclick = () => {{
    stepNanoSim();
    renderView('simulators');
    toast(`nano-vLLM simulated step ${{nanoStepCount}}`);
  }};
}}

// -------------------------------------------------------------
// Curriculum & Reference Renderers
// -------------------------------------------------------------
function renderCurriculum() {{
  if (activeLessonId) {{
    const s = sessions.find(x => x.id === activeLessonId) || sessions[0];
    const u = units.find(x => x.id === s.unit) || units[0];
    return `
      <div style="margin-bottom:18px;">
        <button class="action-btn secondary" id="btn-back-curriculum">&larr; Back to Curriculum</button>
      </div>
      <section class="lab-hero">
        <span class="tag">PATH ${{u.n}} &middot; SESSION</span>
        <h1>${{s.title}}</h1>
        <p>${{s.subtitle}}</p>
      </section>

      <div class="sim-card" style="margin-bottom:20px;">
        <h3 style="color:#fff">Start with a Question</h3>
        <p style="color:#94a3b8;font-size:14px">${{s.question}}</p>
        <div style="padding:12px;background:#1e293b;border-radius:8px;margin:12px 0;">
          <strong style="color:#38bdf8">Core Systems Idea:</strong>
          <p style="margin:4px 0 0;color:#cbd5e1">${{s.definition}}</p>
        </div>
        <h4 style="color:#fff;margin:14px 0 6px;">Derivation &amp; Equations</h4>
        <p style="color:#94a3b8">${{s.derive}}</p>
        ${{s.equation}}

        <h4 style="color:#fff;margin:14px 0 6px;">Code Inspection</h4>
        <div style="background:#060911;padding:14px;border-radius:8px;border:1px solid #334155;">
          <pre style="margin:0;font-family:var(--font-mono);font-size:12px;color:#cbd5e1;overflow-x:auto;">${{s.code.join('\\n')}}</pre>
        </div>

        <h4 style="color:#fff;margin:14px 0 6px;">Independent Practice Tasks</h4>
        <ol style="color:#94a3b8;font-size:13px;line-height:1.6">
          ${{s.tasks.map(t => `<li>${{t}}</li>`).join('')}}
        </ol>

        <h4 style="color:#fff;margin:14px 0 6px;">Knowledge Retrieval Check</h4>
        <form id="lesson-quiz-form">
          ${{s.quiz.map((q, i) => `
            <div style="margin:12px 0;padding:12px;background:#1e293b;border-radius:8px;">
              <p style="margin:0 0 8px;font-weight:600;color:#fff">${{i+1}}. ${{q[0]}}</p>
              ${{q[1].map((opt, j) => `
                <label style="display:block;margin:4px 0;font-size:12px;color:#cbd5e1;cursor:pointer">
                  <input type="radio" name="q${{i}}" value="${{j}}"> ${{opt}}
                </label>
              `).join('')}}
            </div>
          `).join('')}}
          <button class="action-btn" type="submit">Check Answers</button>
        </form>
        <div id="quiz-feedback" style="margin-top:12px;display:none;padding:12px;background:#060911;border-radius:8px;border:1px solid #38bdf8;font-size:12px;"></div>
      </div>
    `;
  }}

  return `
    <section class="lab-hero">
      <span class="tag">GRADUATE SYLLABUS</span>
      <h1>6 Learning Paths &middot; 17 In-Depth Systems Sessions</h1>
      <p>Follow the request lifecycle from browser keystroke to GPU execution, scheduler invariants, BlockPool algorithms, and disaggregation.</p>
    </section>

    <div class="course-grid">
      ${{sessions.map((s, idx) => `
        <article class="course-card" data-lesson-id="${{s.id}}">
          <span class="card-tag">SESSION ${{String(idx+1).padStart(2, '0')}} &middot; ${{s.unit.toUpperCase()}}</span>
          <h4>${{s.title}}</h4>
          <p>${{s.subtitle}}</p>
        </article>
      `).join('')}}
    </div>
  `;
}}

function renderMilestones() {{
  return `
    <section class="lab-hero">
      <span class="tag">PORTFOLIO LABS</span>
      <h1>5 Systems Milestone Deliverables</h1>
      <p>Demonstrate your systems engineering mastery: Explain, Derive, Implement, and Critique.</p>
    </section>

    <div class="sim-grid">
      ${{milestones.map(m => `
        <article class="sim-card">
          <div class="sim-header">
            <div>
              <h3>${{m.title}}</h3>
              <p>${{m.phase}}</p>
            </div>
            <span class="sim-badge">MILESTONE</span>
          </div>
          <p style="color:#94a3b8;font-size:13px">${{m.question}}</p>
          <h4 style="color:#fff;margin:12px 0 6px;font-size:13px">Deliverables:</h4>
          <ol style="margin:0;padding-left:18px;color:#cbd5e1;font-size:12px;line-height:1.6">
            ${{m.deliverables.map(d => `<li>${{d}}</li>`).join('')}}
          </ol>
        </article>
      `).join('')}}
    </div>
  `;
}}

function renderReferences() {{
  return `
    <section class="lab-hero">
      <span class="tag">LIBRARY &amp; PAPERS</span>
      <h1>Architectural Reference Shelf</h1>
      <p>Primary papers, guides, and source repositories powering modern LLM inference systems.</p>
    </section>

    <div class="sim-grid">
      ${{refs.map(r => `
        <article class="sim-card">
          <div class="sim-header">
            <div>
              <h3>${{r[0]}}</h3>
              <p>${{r[1]}}</p>
            </div>
            <span class="sim-badge">PAPER</span>
          </div>
          <p style="color:#94a3b8;font-size:13px">${{r[3]}}</p>
          <div style="margin-top:auto">
            <a class="action-btn" href="${{r[2]}}" target="_blank" rel="noreferrer" style="text-decoration:none">
              Open Resource &rarr;
            </a>
          </div>
        </article>
      `).join('')}}
    </div>
  `;
}}

function renderView(view) {{
  currentView = view;
  document.querySelectorAll('.nav-tab-btn').forEach(b => {{
    b.classList.toggle('active', b.dataset.view === view);
  }});

  const container = document.getElementById('view-container');
  if (view === 'simulators') {{
    container.innerHTML = renderSimulators();
    attachSimulatorListeners();
  }} else if (view === 'curriculum') {{
    container.innerHTML = renderCurriculum();
    if (activeLessonId) {{
      document.getElementById('btn-back-curriculum').onclick = () => {{
        activeLessonId = null;
        renderView('curriculum');
      }};
      const form = document.getElementById('lesson-quiz-form');
      if (form) {{
        form.onsubmit = (e) => {{
          e.preventDefault();
          const s = sessions.find(x => x.id === activeLessonId);
          let score = 0;
          let notes = [];
          s.quiz.forEach((q, i) => {{
            const checked = form.querySelector(`input[name="q${{i}}"]:checked`);
            if (checked && parseInt(checked.value) === q[2]) {{
              score++;
              notes.push(`<b>Q${{i+1}}: Correct!</b> &mdash; ${{q[3]}}`);
            }} else {{
              notes.push(`<b>Q${{i+1}}: Review needed.</b> &mdash; ${{q[3]}}`);
            }}
          }});
          const fb = document.getElementById('quiz-feedback');
          fb.style.display = 'block';
          fb.innerHTML = `<strong>Score: ${{score}} / ${{s.quiz.length}}</strong><br><br>${{notes.join('<br><br>')}}`;
          toast(`Quiz completed: ${{score}}/${{s.quiz.length}}`);
        }};
      }}
    }} else {{
      document.querySelectorAll('[data-lesson-id]').forEach(card => {{
        card.onclick = () => {{
          activeLessonId = card.dataset.lessonId;
          renderView('curriculum');
        }};
      }});
    }}
  }} else if (view === 'milestones') {{
    container.innerHTML = renderMilestones();
  }} else if (view === 'references') {{
    container.innerHTML = renderReferences();
  }}
}}

document.addEventListener('DOMContentLoaded', () => {{
  loadState();
  document.querySelectorAll('.nav-tab-btn').forEach(btn => {{
    btn.onclick = () => {{
      activeLessonId = null;
      renderView(btn.dataset.view);
    }};
  }});
  document.getElementById('brand-link').onclick = (e) => {{
    e.preventDefault();
    activeLessonId = null;
    renderView('simulators');
  }};
  renderView('simulators');
}});
"""

with open('/Users/aravindsundaresan/Documents/ChatGPT/vllm-inference-systems-lab/app.js', 'w') as f:
    f.write(app_js_header)

print("Generated /Users/aravindsundaresan/Documents/ChatGPT/vllm-inference-systems-lab/app.js successfully!")
