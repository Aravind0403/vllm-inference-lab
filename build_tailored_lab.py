import json
import sys

sys.path.append('/Users/aravindsundaresan/Documents/ChatGPT/vLLM_LMS')
import generate_app
import build_full_lms

units = generate_app.units
courseArc = generate_app.courseArc
milestones = generate_app.milestones
refs = generate_app.refs
sessions = build_full_lms.sessions

session_meta = {
    "s0_1": {"time": "90–120 min", "tags": ["Read", "Architecture", "ZeroMQ IPC"], "badge": "JOURNEY", "badgeClass": "journey"},
    "s0_2": {"time": "90–120 min", "tags": ["Read", "Scheduler", "Profiling"], "badge": "JOURNEY", "badgeClass": "journey"},
    "s1_1": {"time": "60–90 min", "tags": ["Derive", "Roofline", "Analysis"], "badge": "ENGINE", "badgeClass": "engine"},
    "s1_2": {"time": "90–120 min", "tags": ["Read", "Benchmarks", "Code"], "badge": "ENGINE", "badgeClass": "engine"},
    "s1_3": {"time": "90–120 min", "tags": ["Code", "IPC", "Profiling"], "badge": "ENGINE", "badgeClass": "engine"},
    "s2_1": {"time": "120 min", "tags": ["Derive", "Code", "Invariants"], "badge": "SCHEDULER", "badgeClass": "scheduler"},
    "s2_2": {"time": "90 min", "tags": ["Trace", "Queue Order", "PR #58947"], "badge": "SCHEDULER", "badgeClass": "scheduler"},
    "s2_3": {"time": "90–120 min", "tags": ["Case Study", "Issue #40004", "PR #45558"], "badge": "SCHEDULER", "badgeClass": "scheduler"},
    "s3_1": {"time": "90–120 min", "tags": ["Architecture", "PagedAttention", "Virtual Memory"], "badge": "KV CACHE", "badgeClass": "kvcache"},
    "s3_2": {"time": "60–90 min", "tags": ["Derive", "64-Bit Hash", "Prefix Tree"], "badge": "KV CACHE", "badgeClass": "kvcache"},
    "s3_3": {"time": "90–120 min", "tags": ["Code", "BlockPool", "LRU Eviction"], "badge": "KV CACHE", "badgeClass": "kvcache"},
    "s4_1": {"time": "60–90 min", "tags": ["Derive", "VRAM Partitioning", "determine_available_memory"], "badge": "MEMORY", "badgeClass": "memory"},
    "s4_2": {"time": "60–90 min", "tags": ["Analysis", "CPU Driver Overhead", "Kernel Latency"], "badge": "MEMORY", "badgeClass": "memory"},
    "s4_3": {"time": "90–120 min", "tags": ["Code", "CUDA Graphs", "Batch Buckets"], "badge": "MEMORY", "badgeClass": "memory"},
    "s5_1": {"time": "60–90 min", "tags": ["Hardware", "Storage Pyramid", "HBM vs PCIe"], "badge": "DISAGGREGATION", "badgeClass": "disagg"},
    "s5_2": {"time": "90–120 min", "tags": ["Architecture", "P/D Split", "Disaggregation"], "badge": "DISAGGREGATION", "badgeClass": "disagg"},
    "s5_3": {"time": "90–120 min", "tags": ["Bug Fix", "RDMA Race", "PR #59504"], "badge": "DISAGGREGATION", "badgeClass": "disagg"}
}

for s in sessions:
    meta = session_meta.get(s["id"], {
        "time": "90 min",
        "tags": ["Read", "Architecture", "Code"],
        "badge": s["unit"].upper(),
        "badgeClass": "journey"
    })
    s["time"] = meta["time"]
    s["tags"] = meta["tags"]
    s["badge"] = meta["badge"]
    s["badgeClass"] = meta["badgeClass"]

print(f"Loaded and verified {len(sessions)} sessions.")

app_js = f"""// vLLM Systems Lab - Master Client Engine (Zero CDN, 100% Offline-Ready)
// Navigation Flow: Dashboard (Starting Page) -> Curriculum -> Milestones -> References -> Interactive Sandboxes

const units = {json.dumps(units, indent=2)};
const sessions = {json.dumps(sessions, indent=2)};
const milestones = {json.dumps(milestones, indent=2)};
const refs = {json.dumps(refs, indent=2)};
const courseArc = {json.dumps(courseArc, indent=2)};

let currentView = 'dashboard';
let activeLessonId = null;
let activeLessonTab = 'learn';

// State Persistence (Local-first in browser)
const storageKey = 'vllm-lab-master-v1';
let state = {{
  done: [],
  notes: {{}},
  scores: {{}},
  milestones: [],
  milestoneChecks: {{}},
  milestoneNotes: {{}},
  completedAt: {{}}
}};

function loadState() {{
  try {{
    const saved = localStorage.getItem(storageKey);
    if (saved) state = Object.assign(state, JSON.parse(saved));
  }} catch (e) {{
    console.error('Failed to load local state', e);
  }}
}}

function saveState() {{
  try {{
    localStorage.setItem(storageKey, JSON.stringify(state));
  }} catch (e) {{
    console.error('Failed to save state to localStorage', e);
  }}
}}

function toast(msg) {{
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('visible');
  setTimeout(() => el.classList.remove('visible'), 2400);
}}

// =============================================================
// TAB 1: DASHBOARD (HOME PAGE & PROGRESS TRACKER)
// =============================================================
function renderDashboard() {{
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
          ${{doneCount === 0 ? 'Start Courseware' : doneCount < sessions.length ? 'Continue Learning' : 'Review Architecture'}} &rarr;
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
          <strong>${{doneCount}} / ${{sessions.length}}</strong>
          <small>Sessions Completed</small>
          <div class="progress-bar-track">
            <div class="progress-bar-fill" style="width: ${{percent}}%"></div>
          </div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon emerald">↗</div>
        <div class="metric-body">
          <strong>${{percent}}%</strong>
          <small>Course Mastery Completion</small>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon purple">⚙</div>
        <div class="metric-body">
          <strong>${{completedM}} / ${{milestones.length}}</strong>
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
      ${{units.map(u => {{
        const uSessions = sessions.filter(s => s.unit === u.id);
        const count = uSessions.filter(s => state.done.includes(s.id)).length;
        const isComplete = count === uSessions.length && uSessions.length > 0;
        return `
          <article class="path-card" data-dash-path="${{u.id}}">
            <div class="path-card-top">
              <span class="path-tag">PATH ${{u.n}} &middot; ${{u.phase}}</span>
              <span class="time-pill" style="${{isComplete ? 'background:#ecfdf5;color:#059669;font-weight:700' : count > 0 ? 'background:#f0f9ff;color:#0284c7;font-weight:700' : ''}}">
                ${{isComplete ? '✓ Completed' : count > 0 ? `${{count}}/${{uSessions.length}} in progress` : 'Not started'}}
              </span>
            </div>
            <h4>${{u.title}}</h4>
            <p>${{u.desc}}</p>
            <div class="path-card-bottom">
              <span>${{uSessions.length}} sessions</span>
              <strong>Open Path &rarr;</strong>
            </div>
          </article>
        `;
      }}).join('')}}
    </div>

    <!-- Execution Pipeline Arc -->
    <div class="section-head">
      <div>
        <h2>Architecture Execution Pipeline</h2>
        <p>The 5 sequential stages of request execution in vLLM v1.</p>
      </div>
    </div>

    <div class="architecture-arc">
      ${{courseArc.map((a, i) => `
        <div class="arc-node">
          <div class="arc-node-num">0${{i+1}}</div>
          <strong>${{a.title}}</strong>
          <small>${{a.paths}}</small>
        </div>
      `).join('')}}
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
          <span class="time-pill" style="background:#ede9fe;color:#6d28d9">${{completedM}} / ${{milestones.length}} Cleared</span>
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
}}

function attachDashboardListeners() {{
  const nextSession = sessions.find(s => !state.done.includes(s.id)) || sessions[0];
  document.getElementById('dash-continue-btn').onclick = () => {{
    activeLessonId = nextSession.id;
    activeLessonTab = 'learn';
    renderView('curriculum');
  }};
  document.getElementById('dash-view-curriculum-btn').onclick = () => renderView('curriculum');
  document.getElementById('dash-goto-sandboxes').onclick = () => renderView('sandboxes');
  document.getElementById('dash-goto-milestones').onclick = () => renderView('milestones');

  document.querySelectorAll('[data-dash-path]').forEach(card => {{
    card.onclick = () => {{
      const pathId = card.dataset.dashPath;
      const firstInPath = sessions.find(s => s.unit === pathId) || sessions[0];
      activeLessonId = firstInPath.id;
      activeLessonTab = 'learn';
      renderView('curriculum');
    }};
  }});
}}

// =============================================================
// TAB 2: COURSE CURRICULUM (THE 2-COLUMN HIGH-CLARITY CARD GRID)
// =============================================================
function renderCurriculum() {{
  if (activeLessonId) {{
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
        <button class="action-btn ${{isDone ? 'secondary' : 'emerald'}}" id="btn-toggle-session-done">
          ${{isDone ? '✓ Completed (Click to undo)' : 'Mark Session Complete'}}
        </button>
      </div>

      <!-- Banner -->
      <section class="dashboard-hero" style="padding:28px 34px;margin-bottom:24px;">
        <div class="hero-tag">PATH ${{u.n}} &middot; ${{s.badge}} &middot; ${{s.time}}</div>
        <h2>${{s.title}}</h2>
        <p style="margin-bottom:0">${{s.subtitle}}</p>
      </section>

      <!-- 2-Column Split: Content vs Sidebar -->
      <div class="lesson-layout">
        <section class="lesson-main">
          <!-- Lesson Sub-tabs -->
          <div class="lesson-tabs">
            <button class="lesson-tab-btn ${{activeLessonTab === 'learn' ? 'active' : ''}}" data-ltab="learn">Learn &amp; Inspect</button>
            <button class="lesson-tab-btn ${{activeLessonTab === 'practice' ? 'active' : ''}}" data-ltab="practice">Hands-On Practice</button>
            <button class="lesson-tab-btn ${{activeLessonTab === 'quiz' ? 'active' : ''}}" data-ltab="quiz">Knowledge Check</button>
            <button class="lesson-tab-btn ${{activeLessonTab === 'notes' ? 'active' : ''}}" data-ltab="notes">My Notes</button>
          </div>

          <div id="lesson-tab-body">
            ${{renderLessonTabContent(s, activeLessonTab)}}
          </div>
        </section>

        <!-- Sidebar -->
        <aside class="lesson-aside">
          <div class="aside-card">
            <h4>Session Outcome</h4>
            <p>${{s.objective}}</p>
            <div style="padding-top:12px;margin-top:12px;border-top:1px solid var(--border);display:flex;justify-content:space-between;font-size:12px;color:var(--ink-muted);">
              <span>Path Progress</span>
              <strong style="color:var(--ink)">${{unitDone}} / ${{unitSessions.length}}</strong>
            </div>
          </div>

          <div class="aside-card">
            <h4>Target Code &amp; Reading</h4>
            <a href="${{s.readingUrl}}" target="_blank" rel="noreferrer" class="section-head-link" style="font-size:12px;margin-bottom:6px;display:block">
              ${{s.readingTitle}} &rarr;
            </a>
            <p>${{s.readingNote}}</p>
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
  }}

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
      ${{sessions.map((s, idx) => {{
        const isDone = state.done.includes(s.id);
        return `
          <article class="session-card" data-session-open="${{s.id}}">
            <div>
              <div class="session-card-header">
                <span class="subsystem-badge ${{s.badgeClass}}">
                  Session ${{String(idx+1).padStart(2, '0')}} &middot; ${{s.badge}}
                </span>
                ${{isDone ? `
                  <span class="status-pill-done">✓ Done</span>
                ` : `
                  <span class="time-pill">${{s.time}}</span>
                `}}
              </div>
              <h3 class="session-card-title">${{s.title}}</h3>
              <p class="session-card-desc">${{s.subtitle}}</p>
            </div>
            
            <div class="session-card-footer">
              <div class="session-tags-row">
                ${{s.tags.map((t, tidx) => `<span>${{t}}</span>${{tidx < s.tags.length - 1 ? '<span>&middot;</span>' : ''}}`).join('')}}
              </div>
              <span class="session-card-cta">
                Open session <span>&rarr;</span>
              </span>
            </div>
          </article>
        `;
      }}).join('')}}
    </div>
  `;
}}

function renderLessonTabContent(s, tab) {{
  if (tab === 'learn') {{
    return `
      <div class="lead-question-box">${{s.question}}</div>

      <div class="callout-box">
        <strong>Core Systems Invariant:</strong>
        <p>${{s.definition}}</p>
      </div>

      <h3 style="font-size:16px;margin:22px 0 8px;">Hardware First Principles &amp; Derivations</h3>
      <p style="color:var(--ink-secondary);font-size:13.5px">${{s.derive}}</p>
      
      <div class="math-eq-card">${{s.equation}}</div>

      <h3 style="font-size:16px;margin:22px 0 8px;">Codebase Inspection</h3>
      <div class="code-box-card">
        <div class="code-box-header">
          <span>vLLM Source &middot; Python / C++</span>
          <span>study-vllm-v1-internals</span>
        </div>
        <pre>${{s.code.join('\\n').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}}</pre>
      </div>

      <div class="predict-panel">
        <label>Predict Before Inspecting: What invariants must hold here, and what fails if memory is exhausted?</label>
        <textarea class="predict-textarea" id="predict-box" placeholder="Write your predictions and expected shapes before running..."></textarea>
        <div>
          <button class="hint-toggle-btn" id="btn-toggle-hint">Reveal Architectural Hint &rarr;</button>
          <div class="hint-box-content" id="hint-box">${{s.hint}}</div>
        </div>
      </div>

      <h3 style="font-size:16px;margin:22px 0 8px;">Independent Systems Tasks</h3>
      <ol style="margin:0;padding-left:20px;color:var(--ink-secondary);font-size:13px;line-height:1.65">
        ${{s.tasks.map(t => `<li style="margin-bottom:6px">${{t}}</li>`).join('')}}
      </ol>
    `;
  }}

  if (tab === 'practice') {{
    return `
      <h3 style="font-size:16px;margin-bottom:8px;">Hands-On Practice &amp; Repo Tracing</h3>
      <p style="color:var(--ink-muted);font-size:13px;margin-bottom:14px;">
        Open your local repository clone at <code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:12px;">/Users/aravindsundaresan/Open_Source/vLLMs/vllm_src</code> and inspect the relevant modules:
      </p>
      <ol style="padding-left:20px;color:var(--ink-secondary);font-size:13px;line-height:1.65;margin-bottom:20px;">
        ${{s.tasks.map(t => `<li style="margin-bottom:6px">${{t}}</li>`).join('')}}
      </ol>
      <div style="padding-top:16px;border-top:1px solid var(--border);">
        <h4 style="font-size:13px;text-transform:uppercase;color:var(--ink);letter-spacing:0.04em;margin-bottom:6px">Systems Reflection &amp; Bug Analysis</h4>
        <textarea class="predict-textarea" style="height:120px" id="practice-note-box" placeholder="Document what you verified in code, benchmark timings, or failure edge cases..."></textarea>
        <small style="color:var(--ink-dim)">Notes save automatically in this browser.</small>
      </div>
    `;
  }}

  if (tab === 'quiz') {{
    return `
      <h3 style="font-size:16px;margin-bottom:6px;">Knowledge Retrieval Check</h3>
      <p style="color:var(--ink-muted);font-size:13px;margin-bottom:16px;">Answer from memory to evaluate your conceptual mastery of invariants.</p>
      
      <form id="quiz-form">
        ${{s.quiz.map((q, i) => `
          <div class="quiz-question-card">
            <p>${{i + 1}}. ${{q[0]}}</p>
            ${{q[1].map((opt, j) => `
              <label class="quiz-choice-item">
                <input type="radio" name="q${{i}}" value="${{j}}">
                <span>${{opt}}</span>
              </label>
            `).join('')}}
          </div>
        `).join('')}}
        <button class="action-btn primary" type="submit" style="margin-top:10px">Check Answers</button>
      </form>
      <div id="quiz-result" class="quiz-feedback-box"></div>
    `;
  }}

  if (tab === 'notes') {{
    return `
      <h3 style="font-size:16px;margin-bottom:6px;">Personal Systems Notes</h3>
      <p style="color:var(--ink-muted);font-size:13px;margin-bottom:14px;">Synthesize the core invariants in your own words. Persistent across browser sessions.</p>
      <textarea class="predict-textarea" style="height:180px" id="session-note-box" placeholder="Write key takeaways, memory equations, or questions for further study..."></textarea>
      <small style="color:var(--ink-dim)">Saved automatically in this browser.</small>
    `;
  }}
}}

function attachCurriculumListeners() {{
  if (activeLessonId) {{
    document.getElementById('btn-back-curriculum').onclick = () => {{
      activeLessonId = null;
      renderView('curriculum');
    }};

    document.getElementById('btn-toggle-session-done').onclick = () => {{
      if (state.done.includes(activeLessonId)) {{
        state.done = state.done.filter(x => x !== activeLessonId);
        delete state.completedAt[activeLessonId];
      }} else {{
        state.done.push(activeLessonId);
        state.completedAt[activeLessonId] = new Date().toISOString().split('T')[0];
      }}
      saveState();
      renderView('curriculum');
      toast('Session status updated.');
    }};

    document.querySelectorAll('[data-ltab]').forEach(b => {{
      b.onclick = () => {{
        activeLessonTab = b.dataset.ltab;
        renderView('curriculum');
      }};
    }});

    if (activeLessonTab === 'learn') {{
      const pBox = document.getElementById('predict-box');
      if (pBox) {{
        pBox.value = state.notes[activeLessonId + '_predict'] || '';
        pBox.oninput = () => {{
          state.notes[activeLessonId + '_predict'] = pBox.value;
          saveState();
        }};
      }}
      const hintBtn = document.getElementById('btn-toggle-hint');
      if (hintBtn) {{
        hintBtn.onclick = () => {{
          const h = document.getElementById('hint-box');
          h.classList.toggle('visible');
          hintBtn.textContent = h.classList.contains('visible') ? 'Hide Architectural Hint' : 'Reveal Architectural Hint \u2192';
        }};
      }}
    }}

    if (activeLessonTab === 'practice') {{
      const prBox = document.getElementById('practice-note-box');
      if (prBox) {{
        prBox.value = state.notes[activeLessonId + '_practice'] || '';
        prBox.oninput = () => {{
          state.notes[activeLessonId + '_practice'] = prBox.value;
          saveState();
        }};
      }}
    }}

    if (activeLessonTab === 'notes') {{
      const nBox = document.getElementById('session-note-box');
      if (nBox) {{
        nBox.value = state.notes[activeLessonId] || '';
        nBox.oninput = () => {{
          state.notes[activeLessonId] = nBox.value;
          saveState();
        }};
      }}
    }}

    if (activeLessonTab === 'quiz') {{
      const form = document.getElementById('quiz-form');
      if (form) {{
        form.onsubmit = (e) => {{
          e.preventDefault();
          const s = sessions.find(x => x.id === activeLessonId);
          let score = 0;
          let feedback = [];
          s.quiz.forEach((q, i) => {{
            const chosen = form.querySelector(`input[name="q${{i}}"]:checked`);
            if (chosen && parseInt(chosen.value) === q[2]) {{
              score++;
              feedback.push(`<b style="color:#34d399">Q${{i+1}}: Correct!</b> &mdash; ${{q[3]}}`);
            }} else {{
              feedback.push(`<b style="color:#fbbf24">Q${{i+1}}: Review Invariant.</b> &mdash; ${{q[3]}}`);
            }}
          }});
          state.scores[activeLessonId] = score;
          saveState();
          const res = document.getElementById('quiz-result');
          res.style.display = 'block';
          res.innerHTML = `<strong>Your Score: ${{score}} / ${{s.quiz.length}}</strong><br><br>${{feedback.join('<br><br>')}}`;
          toast(`Knowledge Check: ${{score}}/${{s.quiz.length}}`);
        }};
      }}
    }}
  }} else {{
    document.querySelectorAll('[data-session-open]').forEach(card => {{
      card.onclick = () => {{
        activeLessonId = card.dataset.sessionOpen;
        activeLessonTab = 'learn';
        renderView('curriculum');
      }};
    }});
  }}
}}

// =============================================================
// TAB 3: MILESTONE LABS (PORTFOLIO PROJECTS)
// =============================================================
function renderMilestones() {{
  const criteria = [
    ['explain', 'Explain from memory', 'Explain the underlying hardware trade-offs and code architecture without referencing documentation.'],
    ['derive', 'Derive the equations', 'Derive the mathematical formulas (arithmetic intensity, memory bounds, or latency breakdown) by hand.'],
    ['implement', 'Implement and verify', 'Write a script or test harness with assertions that independently verify the subsystem\\'s behavior.'],
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
      ${{milestones.map(m => {{
        const isComplete = state.milestones.includes(m.id);
        const checks = state.milestoneChecks[m.id] || {{}};
        const ready = m.requires.every(uid =>
          sessions.filter(s => s.unit === uid).every(s => state.done.includes(s.id))
        );
        return `
          <div class="milestone-card">
            <div>
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <span class="subsystem-badge engine">
                  ${{m.phase}}
                </span>
                <span class="time-pill" style="${{isComplete ? 'background:#ecfdf5;color:#059669;font-weight:700' : ready ? 'background:#f0f9ff;color:#0284c7;font-weight:700' : ''}}">
                  ${{isComplete ? '✓ Completed' : ready ? 'Ready to Start' : 'Builds on prerequisites'}}
                </span>
              </div>
              <h3 style="font-size:18px;margin-bottom:6px;">${{m.title}}</h3>
              <p style="font-size:13px;color:var(--ink-muted);line-height:1.55;margin-bottom:16px;">${{m.question}}</p>
              
              <h4 style="font-size:12px;text-transform:uppercase;color:var(--ink);letter-spacing:0.04em;margin-bottom:6px;">Deliverables:</h4>
              <ul style="padding-left:18px;font-size:12.5px;color:var(--ink-secondary);line-height:1.6;margin-bottom:18px;">
                ${{m.deliverables.map(d => `<li style="margin-bottom:4px;">${{d}}</li>`).join('')}}
              </ul>
            </div>

            <div style="padding-top:14px;border-top:1px solid var(--border);">
              <h4 style="font-size:12px;text-transform:uppercase;color:var(--ink);letter-spacing:0.04em;margin-bottom:8px;">4-Pillar Mastery Standards:</h4>
              <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px;">
                ${{criteria.map(([k, label, desc]) => `
                  <label style="display:flex;align-items:flex-start;gap:8px;font-size:12px;color:var(--ink-secondary);cursor:pointer">
                    <input type="checkbox" data-mcheck="${{m.id}}" data-key="${{k}}" ${{checks[k] ? 'checked' : ''}} style="margin-top:3px;accent-color:var(--sub-engine)">
                    <span><b style="color:var(--ink)">${{label}}</b> &mdash; ${{desc}}</span>
                  </label>
                `).join('')}}
              </div>

              <textarea class="predict-textarea" style="height:65px;margin-bottom:12px;" data-mnotes="${{m.id}}" placeholder="Save test script paths or benchmark notes...">${{state.milestoneNotes[m.id] || ''}}</textarea>

              <button class="action-btn ${{isComplete ? 'secondary' : 'primary'}}" data-mtoggle="${{m.id}}" style="width:100%;${{!isComplete ? 'background:var(--sub-engine)' : ''}}">
                ${{isComplete ? '✓ Milestone Cleared (Undo)' : 'Mark Milestone Complete'}}
              </button>
            </div>
          </div>
        `;
      }}).join('')}}
    </div>
  `;
}}

function attachMilestonesListeners() {{
  document.querySelectorAll('[data-mcheck]').forEach(box => {{
    box.onchange = () => {{
      const mId = box.dataset.mcheck;
      const key = box.dataset.key;
      state.milestoneChecks[mId] = state.milestoneChecks[mId] || {{}};
      state.milestoneChecks[mId][key] = box.checked;
      saveState();
      toast('Rubric saved.');
    }};
  }});

  document.querySelectorAll('[data-mnotes]').forEach(area => {{
    area.oninput = () => {{
      const mId = area.dataset.mnotes;
      state.milestoneNotes[mId] = area.value;
      saveState();
    }};
  }});

  document.querySelectorAll('[data-mtoggle]').forEach(btn => {{
    btn.onclick = () => {{
      const mId = btn.dataset.mtoggle;
      if (state.milestones.includes(mId)) {{
        state.milestones = state.milestones.filter(x => x !== mId);
      }} else {{
        state.milestones.push(mId);
      }}
      saveState();
      renderView('milestones');
      toast('Milestone status updated.');
    }};
  }});
}}

// =============================================================
// TAB 4: ARCHITECTURAL REFERENCE SHELF
// =============================================================
function renderReferences() {{
  return `
    <section class="dashboard-hero">
      <div class="hero-tag">SYSTEMS LIBRARY</div>
      <h2>Architectural Reference Shelf</h2>
      <p>Primary research papers, official documentation, and local source repositories informing vLLM v1.</p>
    </section>

    <div class="two-col-grid">
      ${{refs.map((r, i) => `
        <div class="reference-card">
          <div style="margin-bottom:14px;">
            <div style="margin-bottom:10px;">
              <span class="subsystem-badge kvcache">
                ${{String(i + 1).padStart(2, '0')}} &middot; ${{r[1]}}
              </span>
            </div>
            <h3 style="font-size:17px;margin-bottom:6px;">${{r[0]}}</h3>
            <p style="font-size:13px;color:var(--ink-secondary);line-height:1.55;">${{r[3]}}</p>
          </div>
          <div style="padding-top:12px;border-top:1px solid var(--border);">
            <a href="${{r[2]}}" target="_blank" rel="noreferrer" class="section-head-link" style="font-size:13px">
              Open Resource &rarr;
            </a>
          </div>
        </div>
      `).join('')}}
    </div>
  `;
}}

// =============================================================
// TAB 5: INTERACTIVE SANDBOXES (AT THE END AS REQUESTED)
// =============================================================
const GPU_SPECS = {{
  h100: {{ name: 'NVIDIA H100 SXM (Hopper)', tflops: 3350, bandwidth_gb: 3350, ridge: 1000 }},
  a100: {{ name: 'NVIDIA A100 SXM (Ampere)', tflops: 312, bandwidth_gb: 2000, ridge: 156 }},
  l40s: {{ name: 'NVIDIA L40S (Ada Lovelace)', tflops: 366, bandwidth_gb: 864, ridge: 423 }},
  b200: {{ name: 'NVIDIA B200 (Blackwell)', tflops: 9000, bandwidth_gb: 8000, ridge: 1125 }}
}};

function calculateRoofline(gpuKey, mode, batchSize, seqLen) {{
  const gpu = GPU_SPECS[gpuKey];
  const weightsBytes = 140 * 1e9;
  const L = 80, N_kv = 8, D = 128, P = 2;
  const kvBytesPerToken = 2 * L * N_kv * D * P;

  let flops = 0, bytes = 0;
  if (mode === 'prefill') {{
    flops = 2 * 70e9 * batchSize * seqLen;
    bytes = weightsBytes + (kvBytesPerToken * batchSize * seqLen);
  }} else {{
    flops = 2 * 70e9 * batchSize * 1;
    bytes = weightsBytes + (kvBytesPerToken * batchSize * seqLen);
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
    <svg viewBox="0 0 ${{width}} ${{height}}">
      <defs>
        <radialGradient id="dotGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#38bdf8" stop-opacity="1"/>
          <stop offset="100%" stop-color="#38bdf8" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <line x1="${{pad}}" y1="${{height - pad}}" x2="${{width - pad}}" y2="${{height - pad}}" stroke="#334155" stroke-width="1.5"/>
      <line x1="${{pad}}" y1="${{pad}}" x2="${{pad}}" y2="${{height - pad}}" stroke="#334155" stroke-width="1.5"/>

      <polyline points="${{startX}},${{startY}} ${{ridgeX}},${{ceilingY}} ${{endX}},${{ceilingY}}"
        fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-linejoin="round"/>

      <line x1="${{ridgeX}}" y1="${{ceilingY}}" x2="${{ridgeX}}" y2="${{height - pad}}" stroke="#64748b" stroke-dasharray="3,3"/>
      <text x="${{ridgeX}}" y="${{height - pad + 15}}" fill="#94a3b8" font-size="9" text-anchor="middle">Ridge: ${{gpu.ridge}} FLOPs/B</text>

      <circle cx="${{dotX}}" cy="${{dotY}}" r="12" fill="url(#dotGlow)"/>
      <circle cx="${{dotX}}" cy="${{dotY}}" r="5" fill="#38bdf8" stroke="#fff" stroke-width="2"/>

      <text x="${{width - pad}}" y="${{ceilingY - 8}}" fill="#f59e0b" font-size="10" font-weight="bold" text-anchor="end">Peak: ${{gpu.tflops}} TFLOPs</text>
      <text x="${{dotX}}" y="${{Math.max(20, dotY - 12)}}" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">
        ${{intensity.toFixed(1)}} FLOPs/B (${{isComputeBound ? 'Compute-Bound' : 'Memory-Bound'}})
      </text>
      <text x="${{width / 2}}" y="${{height - 8}}" fill="#64748b" font-size="9" text-anchor="middle">Arithmetic Intensity [FLOPs / Byte] (Log Scale)</text>
      <text x="12" y="${{height / 2}}" fill="#64748b" font-size="9" text-anchor="middle" transform="rotate(-90 12,${{height / 2}})">Performance [TFLOPs]</text>
    </svg>
  `;
}}

const MODEL_PROFILES = {{
  'llama3-8b': {{ name: 'Llama-3-8B', layers: 32, kv_heads: 8, head_dim: 128, params_b: 8.0 }},
  'llama3-70b': {{ name: 'Llama-3-70B', layers: 80, kv_heads: 8, head_dim: 128, params_b: 70.6 }},
  'mistral-7b': {{ name: 'Mistral-7B', layers: 32, kv_heads: 8, head_dim: 128, params_b: 7.2 }},
  'deepseek-v3': {{ name: 'DeepSeek-V3 (MoE)', layers: 61, kv_heads: 8, head_dim: 128, params_b: 37.0 }}
}};

function calculateVRAM(modelKey, precisionBytes, gpuVramGB, contextLen) {{
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

  return {{
    weightsGB, peakActGB, cudaGraphsGB, availableKV_GB,
    kvKBPerToken, kvGBPerSeq, maxConcurrentStreams, totalPhysicalBlocks,
    pctWeights, pctAct, pctGraphs, pctKV
  }};
}}

// Timeline Simulator state
let timelineStep = 0;
const TIMELINE_STEPS = [
  {{ step: 1, desc: 'Step 1: Incoming requests arrive. Prefills start.', slots: ['P1', 'P1', 'P2', 'P2', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'B'] }},
  {{ step: 2, desc: 'Step 2: Req 1 & 2 enter decode. Req 3 arrives with 2k prompt.', slots: ['D1', 'D2', 'P3', 'P3', 'P3', 'P3', 'B', 'B', 'B', 'B', 'B', 'B'] }},
  {{ step: 3, desc: 'Step 3: Chunked Prefill (v1): Req 3 chunk co-scheduled with D1 & D2 decodes.', slots: ['D1', 'D2', 'C3', 'C3', 'D1', 'D2', 'C3', 'C3', 'B', 'B', 'B', 'B'] }},
  {{ step: 4, desc: 'Step 4: Disaggregated Serving: Prefills on Node A; Node B maintains flat TPOT!', slots: ['D1', 'D2', 'D3', 'D1', 'D2', 'D3', 'D1', 'D2', 'D3', 'D1', 'D2', 'D3'] }}
];

// Nano-vLLM Stepper state
let nanoStepCount = 0;
let nanoBlocks = Array.from({{ length: 16 }}, (_, i) => ({{ id: i, ref: 0, hash: null }}));
let nanoRequests = [
  {{ id: 'Req-1', prompt: 'SysPrompt + UserA', status: 'Running', tokens: 18, blocks: [0, 1] }},
  {{ id: 'Req-2', prompt: 'SysPrompt + UserB', status: 'Running', tokens: 18, blocks: [0, 2] }},
  {{ id: 'Req-3', prompt: 'Long RAG Context', status: 'Waiting', tokens: 0, blocks: [] }}
];

function stepNanoSim() {{
  nanoStepCount++;
  nanoBlocks[0].ref = 2; // Shared system prompt block!
  nanoBlocks[0].hash = '0x8F3A';
  nanoBlocks[1].ref = 1;
  nanoBlocks[1].hash = '0x1A2B';
  nanoBlocks[2].ref = 1;
  nanoBlocks[2].hash = '0x9C8D';

  if (nanoStepCount >= 2) {{
    nanoRequests[2].status = 'Running (Chunked Prefill)';
    nanoRequests[2].tokens = 16;
    nanoRequests[2].blocks = [3];
    nanoBlocks[3].ref = 1;
    nanoBlocks[3].hash = '0x44EE';
  }}
  if (nanoStepCount >= 3) {{
    nanoRequests[0].status = 'Finished (Blocks freed to LRU)';
    nanoBlocks[1].ref = 0; // Freed to LRU eviction queue
    nanoBlocks[0].ref = 1; // Req 2 still holds block 0
  }}
}}

function renderRadixTreeSVG() {{
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
}}

function renderSandboxes() {{
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
          ${{renderRooflineSVG(roof)}}
        </div>

        <div class="sim-stats-banner" id="rf-stats">
          <div class="sim-stat-box">
            <span>Operational Regime</span>
            <strong style="color:${{roof.isComputeBound ? '#0284c7' : '#d97706'}}">
              ${{roof.isComputeBound ? 'Compute-Bound' : 'Memory-Bound'}}
            </strong>
          </div>
          <div class="sim-stat-box">
            <span>Arithmetic Intensity</span>
            <strong>${{roof.intensity.toFixed(1)}} FLOPs/B</strong>
          </div>
          <div class="sim-stat-box">
            <span>Achievable Speed</span>
            <strong>${{roof.achievableTFlops.toFixed(1)}} TFLOPs</strong>
          </div>
          <div class="sim-stat-box">
            <span>Bus Saturation</span>
            <strong>${{roof.saturationPct}}%</strong>
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

        <div class="sim-stats-banner" id="vr-stats">
          <div class="sim-stat-box">
            <span>KV / Token</span>
            <strong>${{vram.kvKBPerToken.toFixed(1)}} KB</strong>
          </div>
          <div class="sim-stat-box">
            <span>KV / Sequence</span>
            <strong>${{vram.kvGBPerSeq.toFixed(2)}} GB</strong>
          </div>
          <div class="sim-stat-box">
            <span>Max Concurrency</span>
            <strong style="color:#059669">${{vram.maxConcurrentStreams}} streams</strong>
          </div>
          <div class="sim-stat-box">
            <span>Physical Blocks (16t)</span>
            <strong>${{vram.totalPhysicalBlocks.toLocaleString()}}</strong>
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
          ${{TIMELINE_STEPS[timelineStep].desc}}
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
            Step Engine (t = ${{nanoStepCount}})
          </button>
        </div>

        <div style="background:#090d16;padding:14px;border-radius:10px;border:1px solid #1e293b;">
          <div style="display:grid;grid-template-columns:repeat(8,1fr);gap:6px;margin-bottom:12px;">
            ${{nanoBlocks.map(b => `
              <div style="padding:6px 2px;text-align:center;border-radius:4px;border:1px solid ${{b.ref > 1 ? '#a855f7' : b.ref === 1 ? '#10b981' : '#334155'}};background:${{b.ref > 1 ? 'rgba(168,85,247,0.15)' : b.ref === 1 ? 'rgba(16,185,129,0.15)' : '#111827'}}">
                <span style="display:block;font-size:10px;font-family:var(--font-mono);font-weight:700;color:#fff">B${{b.id}}</span>
                <span style="display:block;font-size:8px;color:#94a3b8">${{b.ref > 0 ? `ref:${{b.ref}}` : 'free'}}</span>
              </div>
            `).join('')}}
          </div>
          <div style="font-size:11.5px;color:#cbd5e1;line-height:1.6">
            <span style="font-weight:700;color:#fff;display:block;margin-bottom:2px">Queue Status:</span>
            ${{nanoRequests.map(r => `<div>&bull; <b style="color:#38bdf8">${{r.id}}</b>: ${{r.status}} (Blocks: ${{JSON.stringify(r.blocks)}})</div>`).join('')}}
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
          ${{renderRadixTreeSVG()}}
          <p style="font-size:11.5px;color:#94a3b8;margin-top:10px;line-height:1.55">
            <b style="color:#34d399">Zero-Compute Reuse ($0\\text{{ms}}$):</b> When User A and User B share the root system prompt, the root block is retained in VRAM with <code>ref_count = 2</code>. Divergent tokens allocate only new physical pages.
          </p>
        </div>
      </article>
    </div>
  `;
}}

function attachSandboxesListeners() {{
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
      <div class="sim-stat-box">
        <span>Operational Regime</span>
        <strong style="color:${{res.isComputeBound ? '#0284c7' : '#d97706'}}">
          ${{res.isComputeBound ? 'Compute-Bound' : 'Memory-Bound'}}
        </strong>
      </div>
      <div class="sim-stat-box">
        <span>Arithmetic Intensity</span>
        <strong>${{res.intensity.toFixed(1)}} FLOPs/B</strong>
      </div>
      <div class="sim-stat-box">
        <span>Achievable Speed</span>
        <strong>${{res.achievableTFlops.toFixed(1)}} TFLOPs</strong>
      </div>
      <div class="sim-stat-box">
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
      <div class="sim-stat-box">
        <span>KV / Token</span>
        <strong>${{res.kvKBPerToken.toFixed(1)}} KB</strong>
      </div>
      <div class="sim-stat-box">
        <span>KV / Sequence</span>
        <strong>${{res.kvGBPerSeq.toFixed(2)}} GB</strong>
      </div>
      <div class="sim-stat-box">
        <span>Max Concurrency</span>
        <strong style="color:#059669">${{res.maxConcurrentStreams}} streams</strong>
      </div>
      <div class="sim-stat-box">
        <span>Physical Blocks (16t)</span>
        <strong>${{res.totalPhysicalBlocks.toLocaleString()}}</strong>
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
    renderView('sandboxes');
    toast(`nano-vLLM stepped (t = ${{nanoStepCount}})`);
  }};
}}

// =============================================================
// MAIN ROUTER & APP INITIALIZATION
// =============================================================
function renderView(view) {{
  currentView = view;
  document.querySelectorAll('.nav-tab-btn').forEach(b => {{
    b.classList.toggle('active', b.dataset.view === view);
  }});

  const container = document.getElementById('view-container');
  if (view === 'dashboard') {{
    container.innerHTML = renderDashboard();
    attachDashboardListeners();
  }} else if (view === 'curriculum') {{
    container.innerHTML = renderCurriculum();
    attachCurriculumListeners();
  }} else if (view === 'milestones') {{
    container.innerHTML = renderMilestones();
    attachMilestonesListeners();
  }} else if (view === 'references') {{
    container.innerHTML = renderReferences();
  }} else if (view === 'sandboxes') {{
    container.innerHTML = renderSandboxes();
    attachSandboxesListeners();
  }}
  window.scrollTo({{ top: 0, behavior: 'smooth' }});
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
    renderView('dashboard');
  }};
  
  // Starting page: Dashboard!
  renderView('dashboard');
}});
"""

with open('/Users/aravindsundaresan/Documents/ChatGPT/vllm-inference-systems-lab/app.js', 'w') as f:
    f.write(app_js)

print("Generated clean app.js for pure styles.css architecture!")
