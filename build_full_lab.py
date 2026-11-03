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

print(f"Loaded {len(units)} units, {len(sessions)} sessions, {len(milestones)} milestones, {len(refs)} references.")

app_js = f"""// vLLM Systems Lab & Interactive Courseware
// Order: Dashboard (Home) -> Curriculum -> Milestone Labs -> Reference Shelf -> Interactive Sandboxes

const units = {json.dumps(units, indent=2)};
const sessions = {json.dumps(sessions, indent=2)};
const milestones = {json.dumps(milestones, indent=2)};
const refs = {json.dumps(refs, indent=2)};
const courseArc = {json.dumps(courseArc, indent=2)};

let currentView = 'dashboard';
let activeLessonId = null;

// Persistent state management
const storageKey = 'vllm-lab-v2';
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
    console.error('Failed to load state', e);
  }}
}}

function saveState() {{
  try {{
    localStorage.setItem(storageKey, JSON.stringify(state));
  }} catch (e) {{
    console.error('Failed to save state', e);
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
// TAB 1: DASHBOARD (STARTING PAGE & TRACKER)
// =============================================================
function renderDashboard() {{
  const doneCount = state.done.filter(id => sessions.some(s => s.id === id)).length;
  const percent = Math.round((doneCount / sessions.length) * 100);
  const completedM = state.milestones.length;
  const nextSession = sessions.find(s => !state.done.includes(s.id)) || sessions[0];

  return `
    <section class="dashboard-hero">
      <div class="hero-tag">⚡ vLLM v1 SYSTEMS LAB &middot; PRACTICE-FIRST</div>
      <h1>Core Engine &amp; Continuous Batching Scheduler</h1>
      <p>A graduate-level systems study and interactive lab: Trace request lifecycles from browser ingress through ZeroMQ IPC, unified scheduler invariants, PagedAttention block tables, CUDA Graphs, and RDMA disaggregation.</p>
      
      <div class="hero-stats-row">
        <button class="hero-cta" id="dash-continue-btn">
          ${{doneCount === 0 ? 'Start Courseware' : doneCount < sessions.length ? 'Continue Learning' : 'Review Architecture'}} &rarr;
        </button>
        <div class="hero-meta-items">
          <span><b>6</b> Paths</span>
          <span><b>17</b> In-Depth Sessions</span>
          <span><b>5</b> Portfolio Labs</span>
          <span><b>6</b> Interactive Sandboxes</span>
        </div>
      </div>
    </section>

    <!-- Metrics Tracker Grid -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-icon">✓</div>
        <div class="metric-body">
          <strong>${{doneCount}} / ${{sessions.length}}</strong>
          <small>Sessions Completed</small>
          <div class="progress-bar-track">
            <div class="progress-bar-fill" style="width: ${{percent}}%"></div>
          </div>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon">↗</div>
        <div class="metric-body">
          <strong>${{percent}}%</strong>
          <small>Course Mastery Progress</small>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon">⚙</div>
        <div class="metric-body">
          <strong>${{completedM}} / ${{milestones.length}}</strong>
          <small>Milestone Labs Cleared</small>
        </div>
      </div>

      <div class="metric-card">
        <div class="metric-icon">⚡</div>
        <div class="metric-body">
          <strong style="font-size:16px;color:#38bdf8">v1 Core</strong>
          <small>Target: study-vllm-v1-internals</small>
        </div>
      </div>
    </div>

    <!-- Learning Paths Grid -->
    <div class="section-head">
      <div>
        <h2>Learning Paths &middot; 6 Comprehensive Modules</h2>
        <p>Step-by-step architectural breakdown from hardware Rooflines down to kernel execution.</p>
      </div>
      <button class="section-head-link" id="dash-view-all-curriculum">View Full Syllabus &rarr;</button>
    </div>

    <div class="paths-grid">
      ${{units.map(u => {{
        const uSessions = sessions.filter(s => s.unit === u.id);
        const count = uSessions.filter(s => state.done.includes(s.id)).length;
        const isComplete = count === uSessions.length && uSessions.length > 0;
        return `
          <article class="path-card" data-path-id="${{u.id}}">
            <div class="path-card-top">
              <span class="path-tag">${{u.n}} &middot; ${{u.phase}}</span>
              <span class="path-status ${{isComplete ? 'completed' : ''}}">
                ${{isComplete ? 'Completed' : count > 0 ? `${{count}}/${{uSessions.length}} in progress` : 'Not started'}}
              </span>
            </div>
            <h3>${{u.title}}</h3>
            <p>${{u.desc}}</p>
            <div class="path-card-bottom">
              <span>${{uSessions.length}} authored sessions</span>
              <strong>Open Path &rarr;</strong>
            </div>
          </article>
        `;
      }}).join('')}}
    </div>

    <!-- Architecture Lifecycle Pipeline -->
    <div class="section-head">
      <div>
        <h2>How the Architecture Connects &middot; End-to-End Pipeline</h2>
        <p>The 5 foundational stages of request execution in vLLM v1.</p>
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

    <!-- Quick Access Hub to Sandboxes & Milestones -->
    <div class="section-head">
      <div>
        <h2>Interactive Exploration &amp; Systems Practice</h2>
        <p>Interactive hardware models, VRAM sizers, and hands-on portfolio milestones.</p>
      </div>
    </div>

    <div class="paths-grid" style="grid-template-columns: repeat(2, 1fr);">
      <article class="path-card" id="dash-open-sandboxes">
        <div class="path-card-top">
          <span class="path-tag">SANDBOXES &middot; 6 TOOLS</span>
          <span class="path-status" style="color:#38bdf8;border-color:rgba(56,189,248,0.3)">Live Simulators</span>
        </div>
        <h3>Hardware Rooflines, VRAM Sizers &amp; nano-vLLM</h3>
        <p>Test arithmetic intensity, calculate physical KV cache blocks for 70B models, simulate continuous batching timelines, and explore prefix trees.</p>
        <div class="path-card-bottom">
          <span>Interactive Calculators</span>
          <strong>Launch Sandboxes &rarr;</strong>
        </div>
      </article>

      <article class="path-card" id="dash-open-milestones">
        <div class="path-card-top">
          <span class="path-tag">PORTFOLIO LABS &middot; 5 MILESTONES</span>
          <span class="path-status" style="color:#a855f7;border-color:rgba(168,85,247,0.3)">Self-Assessed</span>
        </div>
        <h3>Systems Milestone Deliverables</h3>
        <p>Demonstrate your mastery across the 4 pillars: Explain from memory, Derive equations, Implement with code assertions, and Critique failure modes.</p>
        <div class="path-card-bottom">
          <span>${{completedM}} / ${{milestones.length}} Complete</span>
          <strong>Open Milestones &rarr;</strong>
        </div>
      </article>
    </div>
  `;
}}

function attachDashboardListeners() {{
  const nextSession = sessions.find(s => !state.done.includes(s.id)) || sessions[0];
  document.getElementById('dash-continue-btn').onclick = () => {{
    activeLessonId = nextSession.id;
    renderView('curriculum');
  }};
  document.getElementById('dash-view-all-curriculum').onclick = () => renderView('curriculum');
  document.getElementById('dash-open-sandboxes').onclick = () => renderView('sandboxes');
  document.getElementById('dash-open-milestones').onclick = () => renderView('milestones');

  document.querySelectorAll('[data-path-id]').forEach(card => {{
    card.onclick = () => {{
      const pathId = card.dataset.pathId;
      const firstInPath = sessions.find(s => s.unit === pathId) || sessions[0];
      activeLessonId = firstInPath.id;
      renderView('curriculum');
    }};
  }});
}}

// =============================================================
// TAB 2: COURSE CURRICULUM & IN-DEPTH SESSIONS
// =============================================================
let activeLessonTab = 'learn';

function renderCurriculum() {{
  if (activeLessonId) {{
    const s = sessions.find(x => x.id === activeLessonId) || sessions[0];
    const u = units.find(x => x.id === s.unit) || units[0];
    const isDone = state.done.includes(s.id);
    const unitSessions = sessions.filter(x => x.unit === u.id);
    const unitDone = unitSessions.filter(x => state.done.includes(x.id)).length;

    return `
      <div style="margin-bottom:18px;display:flex;justify-content:space-between;align-items:center;">
        <button class="action-btn secondary" id="btn-back-curriculum">&larr; Back to Path Overview</button>
        <button class="action-btn" id="btn-toggle-session-done" style="background:${{isDone ? '#334155' : 'var(--primary)'}};color:${{isDone ? '#fff' : '#04121e'}}">
          ${{isDone ? '✓ Completed (Click to Undo)' : 'Mark Session Complete'}}
        </button>
      </div>

      <section class="dashboard-hero" style="padding:28px 32px;margin-bottom:24px;">
        <div class="hero-tag">PATH ${{u.n}} &middot; SESSION</div>
        <h1>${{s.title}}</h1>
        <p>${{s.subtitle}}</p>
      </section>

      <div class="lesson-layout">
        <section class="lesson-main">
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

        <aside class="lesson-aside">
          <div class="aside-card">
            <h3>Session Outcome</h3>
            <p>${{s.objective}}</p>
            <div style="margin-top:12px;font-size:11px;color:var(--ink-muted);">
              Path Progress: <strong style="color:#fff">${{unitDone}} / ${{unitSessions.length}}</strong>
            </div>
          </div>

          <div class="aside-card">
            <h3>Target Local Code / Source</h3>
            <a class="section-head-link" href="${{s.readingUrl}}" target="_blank" rel="noreferrer" style="font-size:11px;display:block;margin-bottom:6px;">
              ${{s.readingTitle}} &rarr;
            </a>
            <p>${{s.readingNote}}</p>
          </div>

          <div class="aside-card">
            <h3>Systems Mastery Loop</h3>
            <ol style="margin:8px 0 0;padding-left:16px;font-size:11px;color:var(--ink-muted);line-height:1.6">
              <li>Hardware Rooflines</li>
              <li>Local Code Invariants</li>
              <li>Predict &amp; Test</li>
              <li>Knowledge Retrieval</li>
            </ol>
          </div>
        </aside>
      </div>
    `;
  }}

  // Path Catalog View
  return `
    <section class="dashboard-hero" style="padding:28px 32px;margin-bottom:24px;">
      <div class="hero-tag">CURRICULUM SYLLABUS</div>
      <h1>6 Learning Paths &middot; 17 In-Depth Systems Sessions</h1>
      <p>Trace vLLM v1 line-by-line across every critical subsystem: process boundaries, continuous batching scheduler loops, memory pools, and distributed connectors.</p>
    </section>

    <div class="course-grid">
      ${{sessions.map((s, idx) => {{
        const isDone = state.done.includes(s.id);
        return `
          <article class="course-card" data-lesson-select="${{s.id}}">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <span class="card-tag">SESSION ${{String(idx+1).padStart(2, '0')}} &middot; ${{s.unit.toUpperCase()}}</span>
              <span style="font-size:10px;padding:2px 6px;border-radius:4px;background:${{isDone ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.05)'}};color:${{isDone ? '#10b981' : '#94a3b8'}}">
                ${{isDone ? '✓ Completed' : 'Pending'}}
              </span>
            </div>
            <h4>${{s.title}}</h4>
            <p>${{s.subtitle}}</p>
          </article>
        `;
      }}).join('')}}
    </div>
  `;
}}

function renderLessonTabContent(s, tab) {{
  if (tab === 'learn') {{
    return `
      <div class="lead-question">${{s.question}}</div>

      <div class="callout-box">
        <strong>Core Systems Invariant:</strong>
        <p>${{s.definition}}</p>
      </div>

      <h3 style="color:#fff;margin:20px 0 8px;font-size:16px">Hardware First Principles &amp; Derivations</h3>
      <p style="color:var(--ink-secondary);font-size:13px">${{s.derive}}</p>
      ${{s.equation}}

      <h3 style="color:#fff;margin:20px 0 8px;font-size:16px">Local Codebase Inspection</h3>
      <div class="code-box">
        <div class="code-box-header">
          <span>vLLM Source &middot; Python / C++</span>
          <span>study-vllm-v1-internals</span>
        </div>
        <pre>${{s.code.join('\\n').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}}</pre>
      </div>

      <div class="predict-panel">
        <label>Predict Before Inspecting: What invariants must hold here, and what fails if memory is exhausted?</label>
        <textarea class="predict-textarea" id="predict-box" placeholder="Write your predictions and expected shapes before running..."></textarea>
        <button class="hint-toggle-btn" id="btn-toggle-hint">Reveal Architectural Hint &rarr;</button>
        <div class="hint-content" id="hint-box">${{s.hint}}</div>
      </div>

      <h3 style="color:#fff;margin:20px 0 8px;font-size:16px">Independent Systems Tasks</h3>
      <ol style="margin:0;padding-left:18px;color:var(--ink-secondary);font-size:13px;line-height:1.6">
        ${{s.tasks.map(t => `<li>${{t}}</li>`).join('')}}
      </ol>
    `;
  }}

  if (tab === 'practice') {{
    return `
      <h3 style="color:#fff;margin-bottom:8px">Hands-On Practice &amp; Repo Tracing</h3>
      <p style="color:var(--ink-muted);font-size:13px">Open your local repo at <code>/Users/aravindsundaresan/Open_Source/vLLMs/vllm_src</code> and execute these tasks:</p>
      <ol style="margin:14px 0 20px;padding-left:18px;color:var(--ink-secondary);font-size:13px;line-height:1.65">
        ${{s.tasks.map(t => `<li>${{t}}</li>`).join('')}}
      </ol>
      <h4 style="color:#fff;margin-bottom:8px">Systems Reflection &amp; Bug Analysis</h4>
      <textarea class="predict-textarea" style="height:120px" id="practice-note-box" placeholder="Document what you verified in code, benchmark timings, or failure edge cases..."></textarea>
      <small style="color:var(--ink-dim)">Saved automatically to local storage</small>
    `;
  }}

  if (tab === 'quiz') {{
    return `
      <h3 style="color:#fff;margin-bottom:8px">Knowledge Retrieval Check</h3>
      <p style="color:var(--ink-muted);font-size:13px;margin-bottom:16px">Answer without looking at documentation to audit your conceptual retention of invariants.</p>
      <form id="quiz-form">
        ${{s.quiz.map((q, i) => `
          <div class="quiz-question-card">
            <p>${{i + 1}}. ${{q[0]}}</p>
            ${{q[1].map((opt, j) => `
              <label class="quiz-choice">
                <input type="radio" name="q${{i}}" value="${{j}}">
                <span>${{opt}}</span>
              </label>
            `).join('')}}
          </div>
        `).join('')}}
        <button class="action-btn" type="submit">Check Answers</button>
      </form>
      <div id="quiz-result" class="quiz-feedback-box" style="display:none"></div>
    `;
  }}

  if (tab === 'notes') {{
    return `
      <h3 style="color:#fff;margin-bottom:8px">Personal Systems Notes</h3>
      <p style="color:var(--ink-muted);font-size:13px;margin-bottom:14px">Summarize the core mechanism in your own words. Persistent across browser sessions.</p>
      <textarea class="predict-textarea" style="height:180px" id="session-note-box" placeholder="Write key takeaways, memory equations, or questions for further study..."></textarea>
      <small style="color:var(--ink-dim)">Saved automatically in this browser</small>
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

    // Tab specific attachments
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
              feedback.push(`<b style="color:#10b981">Q${{i+1}}: Correct!</b> &mdash; ${{q[3]}}`);
            }} else {{
              feedback.push(`<b style="color:#f59e0b">Q${{i+1}}: Review Invariant.</b> &mdash; ${{q[3]}}`);
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
    document.querySelectorAll('[data-lesson-select]').forEach(card => {{
      card.onclick = () => {{
        activeLessonId = card.dataset.lessonSelect;
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
    <section class="dashboard-hero" style="padding:28px 32px;margin-bottom:24px;">
      <div class="hero-tag">PORTFOLIO PROJECTS</div>
      <h1>5 Systems Milestone Deliverables</h1>
      <p>Demonstrate your mastery across the 4 pillars: Explain from memory, Derive equations, Implement with code assertions, and Critique failure modes.</p>
    </section>

    <div class="sandboxes-grid">
      ${{milestones.map(m => {{
        const isComplete = state.milestones.includes(m.id);
        const checks = state.milestoneChecks[m.id] || {{}};
        const ready = m.requires.every(uid =>
          sessions.filter(s => s.unit === uid).every(s => state.done.includes(s.id))
        );
        return `
          <article class="sandbox-card">
            <div class="sandbox-header">
              <div>
                <h3>${{m.title}}</h3>
                <p>${{m.phase}}</p>
              </div>
              <span class="sandbox-badge">${{isComplete ? 'COMPLETED' : ready ? 'READY' : 'LOCKED'}}</span>
            </div>
            
            <p style="color:var(--ink-secondary);font-size:13px;margin-bottom:12px;">${{m.question}}</p>
            
            <h4 style="color:#fff;font-size:12px;margin-bottom:6px">Required Deliverables:</h4>
            <ol style="margin:0 0 16px;padding-left:18px;color:var(--ink-muted);font-size:12px;line-height:1.6">
              ${{m.deliverables.map(d => `<li>${{d}}</li>`).join('')}}
            </ol>

            <h4 style="color:#fff;font-size:12px;margin-bottom:8px">4-Pillar Mastery Standards:</h4>
            <div style="display:flex;flex-direction:column;gap:6px;margin-bottom:14px">
              ${{criteria.map(([k, label, desc]) => `
                <label style="display:flex;align-items:flex-start;gap:8px;font-size:11px;color:var(--ink-secondary);cursor:pointer">
                  <input type="checkbox" data-mcheck="${{m.id}}" data-key="${{k}}" ${{checks[k] ? 'checked' : ''}}>
                  <span><b style="color:#fff">${{label}}</b> &mdash; ${{desc}}</span>
                </label>
              `).join('')}}
            </div>

            <textarea class="predict-textarea" style="height:70px;margin-bottom:10px" data-mnotes="${{m.id}}" placeholder="Save notes or links to your local benchmark scripts...">${{state.milestoneNotes[m.id] || ''}}</textarea>

            <button class="action-btn ${{isComplete ? 'secondary' : ''}}" data-mtoggle="${{m.id}}">
              ${{isComplete ? '✓ Milestone Cleared (Undo)' : 'Mark Milestone Complete'}}
            </button>
          </article>
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
    <section class="dashboard-hero" style="padding:28px 32px;margin-bottom:24px;">
      <div class="hero-tag">SYSTEMS LIBRARY</div>
      <h1>Primary Architectural References &amp; Repositories</h1>
      <p>Official foundational research papers, architectural specifications, and active local repositories informing vLLM v1.</p>
    </section>

    <div class="sandboxes-grid">
      ${{refs.map(r => `
        <article class="sandbox-card">
          <div class="sandbox-header">
            <div>
              <h3>${{r[0]}}</h3>
              <p>${{r[1]}}</p>
            </div>
            <span class="sandbox-badge">RESOURCE</span>
          </div>
          <p style="color:var(--ink-secondary);font-size:13px;line-height:1.6;margin-bottom:18px;">${{r[3]}}</p>
          <div style="margin-top:auto">
            <a class="action-btn" href="${{r[2]}}" target="_blank" rel="noreferrer" style="font-size:11px">
              Open Resource &rarr;
            </a>
          </div>
        </article>
      `).join('')}}
    </div>
  `;
}}

// =============================================================
// TAB 5: INTERACTIVE SANDBOXES (PLACED AT THE END AS REQUESTED)
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

// Nano-vLLM Visual Stepper state
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

// New Sandbox: Radix Tree Visualizer
let radixBranchTurn = 0;
function renderRadixTreeSVG() {{
  return `
    <svg viewBox="0 0 540 180" style="max-width:100%;height:auto">
      <defs>
        <marker id="arrow" markerWidth="6" markerHeight="4" refX="6" refY="2" orient="auto"><polygon points="0 0, 6 2, 0 4" fill="#64748b"/></marker>
      </defs>
      <!-- Root: Shared System Prompt -->
      <rect x="200" y="10" width="140" height="36" rx="6" fill="#1e1b4b" stroke="#818cf8" stroke-width="1.5"/>
      <text x="270" y="32" fill="#fff" font-size="10" font-weight="bold" text-anchor="middle">Root: System Prompt</text>
      
      <!-- Branch A: User Query A -->
      <path d="M 240 46 L 140 90" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>
      <rect x="70" y="90" width="140" height="34" rx="6" fill="#0f291e" stroke="#10b981" stroke-width="1.5"/>
      <text x="140" y="111" fill="#fff" font-size="9" font-weight="bold" text-anchor="middle">User A: Quicksort (O(1) Hit!)</text>

      <!-- Branch B: User Query B -->
      <path d="M 300 46 L 400 90" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>
      <rect x="330" y="90" width="140" height="34" rx="6" fill="#0f291e" stroke="#10b981" stroke-width="1.5"/>
      <text x="400" y="111" fill="#fff" font-size="9" font-weight="bold" text-anchor="middle">User B: Mergesort (O(1) Hit!)</text>

      <!-- Sub-branch Turn 2 for User A -->
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
    <section class="dashboard-hero" style="padding:28px 32px;margin-bottom:24px;">
      <div class="hero-tag">SYSTEMS SIMULATORS &middot; TAB 5</div>
      <h1>Interactive Systems Engineering Sandboxes</h1>
      <p>Test hardware Rooflines, model VRAM footprints, step through continuous batching timelines, and simulate PagedAttention BlockPool algorithms.</p>
    </section>

    <div class="sandboxes-grid">
      <!-- 1. Roofline Explorer -->
      <article class="sandbox-card">
        <div class="sandbox-header">
          <div>
            <h3>1. Arithmetic Intensity &amp; Roofline Explorer</h3>
            <p>Prefill compute-bound ($I &gt;&gt; 100$) vs Decode memory-bound ($I &approx; 1$)</p>
          </div>
          <span class="sandbox-badge">ROOFLINE</span>
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

        <div style="background:#060912;padding:12px;border-radius:8px;border:1px solid var(--border);margin-bottom:14px" id="rf-svg-container">
          ${{renderRooflineSVG(roof)}}
        </div>

        <div class="sim-stats-banner" id="rf-stats">
          <div class="sim-stat-box">
            <span>Operational Regime</span>
            <strong class="${{roof.isComputeBound ? 'highlight' : 'warning'}}">
              ${{roof.isComputeBound ? 'Compute-Bound' : 'Memory-Bandwidth Bound'}}
            </strong>
          </div>
          <div class="sim-stat-box">
            <span>Arithmetic Intensity</span>
            <strong>${{roof.intensity.toFixed(2)}} FLOPs/B</strong>
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

      <!-- 2. VRAM & KV Cache Sizer -->
      <article class="sandbox-card">
        <div class="sandbox-header">
          <div>
            <h3>2. KV Cache &amp; VRAM Allocation Sizer</h3>
            <p>Empirical VRAM breakdown and PagedAttention capacity planning</p>
          </div>
          <span class="sandbox-badge">VRAM SIZER</span>
        </div>

        <div class="sim-controls-grid">
          <div class="sim-control-item">
            <label>Model Profile</label>
            <select id="vr-model">
              <option value="llama3-70b" selected>Llama-3-70B (80L, 8KV, 70B Params)</option>
              <option value="llama3-8b">Llama-3-8B (32L, 8KV, 8B Params)</option>
              <option value="mistral-7b">Mistral-7B (32L, 8KV, 7B Params)</option>
              <option value="deepseek-v3">DeepSeek-V3 MoE (61L, 8KV, 37B Active)</option>
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
            <label>GPU Hardware VRAM</label>
            <select id="vr-vram">
              <option value="80" selected>80 GB (NVIDIA H100 / A100)</option>
              <option value="141">141 GB (NVIDIA H200)</option>
              <option value="48">48 GB (NVIDIA L40S)</option>
              <option value="24">24 GB (RTX 4090)</option>
            </select>
          </div>
          <div class="sim-control-item">
            <label>Context Length: <span id="vr-ctx-val">8,192</span> tokens</label>
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
            <span>KV Cache / Token</span>
            <strong>${{vram.kvKBPerToken.toFixed(1)}} KB</strong>
          </div>
          <div class="sim-stat-box">
            <span>KV / Sequence</span>
            <strong>${{vram.kvGBPerSeq.toFixed(2)}} GB</strong>
          </div>
          <div class="sim-stat-box">
            <span>Max Concurrency</span>
            <strong class="highlight">${{vram.maxConcurrentStreams}} streams</strong>
          </div>
          <div class="sim-stat-box">
            <span>Physical Blocks (16t)</span>
            <strong>${{vram.totalPhysicalBlocks.toLocaleString()}} blocks</strong>
          </div>
        </div>
      </article>

      <!-- 3. Timeline Simulator -->
      <article class="sandbox-card full-width">
        <div class="sandbox-header">
          <div>
            <h3>3. Serving Architecture Timeline Comparison</h3>
            <p>From static batching bubbles to continuous chunked prefill and disaggregation</p>
          </div>
          <button class="action-btn secondary" id="btn-next-step">Step Forward &rarr;</button>
        </div>

        <p style="font-size:12px;color:var(--ink-muted);margin-bottom:12px;" id="timeline-desc">
          ${{TIMELINE_STEPS[timelineStep].desc}}
        </p>

        <div style="background:#060912;border:1px solid var(--border);border-radius:8px;padding:14px;display:flex;flex-direction:column;gap:10px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <span style="width:160px;font:600 11px var(--font-mono);color:var(--ink-muted)">1. Static Batching</span>
            <div style="flex:1;display:grid;grid-template-columns:repeat(12,1fr);gap:4px;">
              <div style="height:24px;background:#3b82f6;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">P1</div>
              <div style="height:24px;background:#3b82f6;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">P2</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#1e293b;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#64748b;border:1px dashed #334155">Idle</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#1e293b;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#64748b;border:1px dashed #334155">Idle</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#1e293b;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#64748b;border:1px dashed #334155">Idle</div>
              <div style="height:24px;background:#1e293b;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#64748b;border:1px dashed #334155">Wait</div>
              <div style="height:24px;background:#1e293b;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#64748b;border:1px dashed #334155">Wait</div>
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:10px;">
            <span style="width:160px;font:600 11px var(--font-mono);color:var(--ink-muted)">2. Continuous (v0)</span>
            <div style="flex:1;display:grid;grid-template-columns:repeat(12,1fr);gap:4px;">
              <div style="height:24px;background:#3b82f6;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">P1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#3b82f6;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">P2</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
              <div style="height:24px;background:#ef4444;border-radius:3px;display:grid;place-items:center;font-size:8px;color:#fff">P3 Stall</div>
              <div style="height:24px;background:#3b82f6;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">P3</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:10px;">
            <span style="width:160px;font:600 11px var(--font-mono);color:var(--ink-muted)">3. Chunked Prefill (v1)</span>
            <div style="flex:1;display:grid;grid-template-columns:repeat(12,1fr);gap:4px;">
              <div style="height:24px;background:#8b5cf6;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">C1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
              <div style="height:24px;background:#8b5cf6;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">C1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
              <div style="height:24px;background:#8b5cf6;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">C2</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
              <div style="height:24px;background:#8b5cf6;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">C3</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D3</div>
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:10px;">
            <span style="width:160px;font:600 11px var(--font-mono);color:var(--ink-muted)">4. Disaggregated (P/D)</span>
            <div style="flex:1;display:grid;grid-template-columns:repeat(12,1fr);gap:4px;">
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D3</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D3</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D3</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D1</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D2</div>
              <div style="height:24px;background:#10b981;border-radius:3px;display:grid;place-items:center;font-size:9px;color:#fff">D3</div>
            </div>
          </div>
        </div>
      </article>

      <!-- 4. Nano-vLLM Stepper -->
      <article class="sandbox-card">
        <div class="sandbox-header">
          <div>
            <h3>4. In-Browser nano-vLLM Stepper</h3>
            <p>Step-by-step BlockPool memory pages and reference counting</p>
          </div>
          <button class="action-btn" id="btn-nano-step" style="font-size:11px">Step Engine (t = ${{nanoStepCount}})</button>
        </div>

        <div style="background:#060912;border:1px solid var(--border);border-radius:8px;padding:12px;">
          <div style="display:grid;grid-template-columns:repeat(8,1fr);gap:6px;margin-bottom:12px">
            ${{nanoBlocks.map(b => `
              <div style="padding:6px 2px;text-align:center;border-radius:4px;border:1px solid ${{b.ref > 1 ? '#c084fc' : b.ref === 1 ? '#10b981' : '#334155'}};background:${{b.ref > 1 ? 'rgba(192,132,252,0.1)' : b.ref === 1 ? 'rgba(16,185,129,0.1)' : '#111827'}}">
                <strong style="display:block;font-size:10px;font-family:var(--font-mono);color:#fff">B${{b.id}}</strong>
                <small style="font-size:8px;color:var(--ink-muted)">${{b.ref > 0 ? `ref:${{b.ref}}` : 'free'}}</small>
              </div>
            `).join('')}}
          </div>
          <div style="font-size:11px;color:var(--ink-secondary)">
            <strong style="color:#fff">Queue Status:</strong>
            ${{nanoRequests.map(r => `<div>&bull; <b>${{r.id}}</b>: ${{r.status}} (Blocks: ${{JSON.stringify(r.blocks)}})</div>`).join('')}}
          </div>
        </div>
      </article>

      <!-- 5. Radix Tree / Prefix Caching Visualizer -->
      <article class="sandbox-card">
        <div class="sandbox-header">
          <div>
            <h3>5. Radix Tree &amp; Prefix Caching DAG</h3>
            <p>Visualizing hash-chaining and multi-user prompt block sharing</p>
          </div>
          <span class="sandbox-badge">PREFIX CACHE</span>
        </div>

        <div style="background:#060912;border:1px solid var(--border);border-radius:8px;padding:12px;">
          ${{renderRadixTreeSVG()}}
          <p style="font-size:11px;color:var(--ink-muted);margin:8px 0 0;line-height:1.5">
            <b>Zero-Compute Reuse ($0\\text{{ms}}$):</b> When User A and User B share the root system prompt, the root block is retained in VRAM with <code>ref_count = 2</code>. Only divergent tokens allocate new physical pages.
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
        <strong class="${{res.isComputeBound ? 'highlight' : 'warning'}}">
          ${{res.isComputeBound ? 'Compute-Bound' : 'Memory-Bandwidth Bound'}}
        </strong>
      </div>
      <div class="sim-stat-box">
        <span>Arithmetic Intensity</span>
        <strong>${{res.intensity.toFixed(2)}} FLOPs/B</strong>
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
        <span>KV Cache / Token</span>
        <strong>${{res.kvKBPerToken.toFixed(1)}} KB</strong>
      </div>
      <div class="sim-stat-box">
        <span>KV / Sequence</span>
        <strong>${{res.kvGBPerSeq.toFixed(2)}} GB</strong>
      </div>
      <div class="sim-stat-box">
        <span>Max Concurrency</span>
        <strong class="highlight">${{res.maxConcurrentStreams}} streams</strong>
      </div>
      <div class="sim-stat-box">
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
  
  // Always start on Dashboard!
  renderView('dashboard');
}});
"""

with open('/Users/aravindsundaresan/Documents/ChatGPT/vllm-inference-systems-lab/app.js', 'w') as f:
    f.write(app_js)

print("Generated complete app.js in /Users/aravindsundaresan/Documents/ChatGPT/vllm-inference-systems-lab/ successfully!")
