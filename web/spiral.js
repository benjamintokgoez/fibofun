/**
 * spiral.js — Interactive Fibonacci golden spiral
 *
 * Loads web/data.json (spiral geometry) and web/fibonacci-facts.json,
 * renders an SVG spiral with clickable squares, and supports a
 * "Story Points Mode" side-panel skin.
 */

'use strict';

// ── Story-points definitions ──────────────────────────────────────────────

/** @type {Record<number, {label:string, heading:string, story:string, note?:string}>} */
const STORY_POINTS = {
  0: {
    label: '0',
    heading: 'No effort',
    story: 'N/A — zero is the origin of the sequence, not a plannable unit of work.',
    note: 'Planning poker typically starts at 1.',
  },
  1: {
    label: '1',
    heading: 'Trivial change (config tweak, one-line fix)',
    story: '"As a developer, I want to update the footer copyright year."',
    note: 'F(1) = F(2) = 1. Both index 1 and 2 map to this size.',
  },
  2: {
    label: '2',
    heading: 'Small, well-understood task (CSS, copy update)',
    story: '"As a designer, I want to change the primary button colour in the settings page."',
  },
  3: {
    label: '3',
    heading: 'Standard small task (simple CRUD endpoint)',
    story: '"As a developer, I want to add a GET /health endpoint that returns service status."',
  },
  5: {
    label: '5',
    heading: 'Medium task with some unknowns (new component + API)',
    story: '"As a user, I want to upload a custom profile avatar via the dashboard."',
  },
  8: {
    label: '8',
    heading: 'Complex feature, may need a spike (new auth flow)',
    story: '"As a user, I want to log in with my Google account via OAuth2."',
  },
  13: {
    label: '13',
    heading: 'Large — likely should be split (3rd-party integration)',
    story: '"As a customer, I want to pay via Stripe at checkout."',
  },
  21: {
    label: '21',
    heading: 'Too big to commit — MUST be split before the sprint',
    story: '"As an admin, I want a real-time analytics dashboard with charts and filters."',
  },
  34: {
    label: '34+',
    heading: 'Epic territory',
    story: 'Migrate the monolith to microservices. Break this into individual stories first.',
  },
  55: {
    label: '55+',
    heading: 'Initiative territory',
    story: 'Launch mobile app v1 for iOS and Android (requires multiple epics).',
  },
  89: {
    label: '89+',
    heading: 'Initiative territory',
    story: 'Internationalise the platform for 10 new locales (translation, RTL, legal).',
  },
  144: {
    label: '144+',
    heading: 'Project territory',
    story: 'Rebuild the platform from scratch on a new architecture (multi-year).',
  },
};

/**
 * Return the story-points entry whose key is the largest value ≤ fib value.
 * @param {number} value
 */
function getSpEntry(value) {
  const keys = [144, 89, 55, 34, 21, 13, 8, 5, 3, 2, 1, 0];
  for (const k of keys) {
    if (value >= k) return STORY_POINTS[k];
  }
  return STORY_POINTS[1];
}

// ── Category colours (matching fibonacci-facts.json categories) ───────────

const CATEGORY_COLORS = {
  'history':          '#f59e0b',
  'mathematics':      '#8b5cf6',
  'computer-science': '#3b82f6',
  'science':          '#10b981',
  'culture':          '#ec4899',
  'sci-fi':           '#06b6d4',
  'art':              '#f97316',
};

/** Colours for story-points size bands */
const SP_COLORS = {
  0:   '#374151',
  1:   '#16a34a',
  2:   '#22d3ee',
  3:   '#84cc16',
  5:   '#eab308',
  8:   '#f97316',
  13:  '#ef4444',
  21:  '#dc2626',
  34:  '#9333ea',
  55:  '#7c3aed',
  89:  '#6d28d9',
  144: '#4c1d95',
};

function getSpColor(value) {
  const keys = [144, 89, 55, 34, 21, 13, 8, 5, 3, 2, 1, 0];
  for (const k of keys) {
    if (value >= k) return SP_COLORS[k];
  }
  return SP_COLORS[1];
}

// ── State ─────────────────────────────────────────────────────────────────

let spiralData   = null;
let factsData    = null;
let storyPointsMode = false;
let selectedIdx  = null;

// ── DOM references ────────────────────────────────────────────────────────

const svg        = document.getElementById('spiral-svg');
const sidePanel  = document.getElementById('side-panel');
const panelInner = document.getElementById('panel-inner');
const spToggle   = document.getElementById('sp-toggle');
const panelClose = document.getElementById('panel-close');
const overlay    = document.getElementById('overlay');
const overlayMsg = document.getElementById('overlay-msg');

// ── Helpers ───────────────────────────────────────────────────────────────

const NS = 'http://www.w3.org/2000/svg';

function svgEl(tag, attrs = {}) {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
}

/**
 * Build the SVG path string for a 90° clockwise arc.
 * @param {{arc_cx:number, arc_cy:number, arc_r:number, arc_start_angle:number}} sq
 */
function arcPath(sq) {
  const { arc_cx: cx, arc_cy: cy, arc_r: r, arc_start_angle: startDeg } = sq;
  const a0 = (startDeg * Math.PI) / 180;
  const a1 = a0 + Math.PI / 2;
  const x1 = cx + r * Math.cos(a0);
  const y1 = cy + r * Math.sin(a0);
  const x2 = cx + r * Math.cos(a1);
  const y2 = cy + r * Math.sin(a1);
  // sweep-flag=1 → clockwise in SVG coordinates (y-down)
  return `M ${fmt(x1)} ${fmt(y1)} A ${fmt(r)} ${fmt(r)} 0 0 1 ${fmt(x2)} ${fmt(y2)}`;
}

function fmt(n) { return Math.round(n * 1e6) / 1e6; }

function computeViewBox(squares, pad = 8) {
  const allX = squares.flatMap(s => [s.x, s.x + s.side]);
  const allY = squares.flatMap(s => [s.y, s.y + s.side]);
  const minX = Math.min(...allX) - pad;
  const minY = Math.min(...allY) - pad;
  const w    = Math.max(...allX) - Math.min(...allX) + 2 * pad;
  const h    = Math.max(...allY) - Math.min(...allY) + 2 * pad;
  return `${fmt(minX)} ${fmt(minY)} ${fmt(w)} ${fmt(h)}`;
}

function getFact(fibIndex) {
  return factsData?.entries?.find(e => e.index === fibIndex) ?? null;
}

function squareFill(sq) {
  if (storyPointsMode) return getSpColor(sq.value);
  const fact = getFact(sq.fib_index);
  return CATEGORY_COLORS[fact?.category] ?? '#6b7280';
}

// ── Rendering ─────────────────────────────────────────────────────────────

function render() {
  const squares = spiralData.squares;

  svg.setAttribute('viewBox', computeViewBox(squares));
  svg.innerHTML = '';

  // ── Arcs (drawn below squares so they sit under the borders) ──
  const arcGroup = svgEl('g', { class: 'arcs' });

  // Arc stroke width scales with the overall geometry
  const maxSide = Math.max(...squares.map(s => s.side));
  const arcW    = Math.max(0.3, maxSide * 0.005);

  squares.forEach(sq => {
    const path = svgEl('path', {
      d:     arcPath(sq),
      class: 'spiral-arc',
      'stroke-width': arcW,
    });
    arcGroup.appendChild(path);
  });
  svg.appendChild(arcGroup);

  // ── Squares ────────────────────────────────────────────────────
  squares.forEach((sq, i) => {
    const g = svgEl('g');

    const rect = svgEl('rect', {
      x:       sq.x,
      y:       sq.y,
      width:   sq.side,
      height:  sq.side,
      class:   'spiral-square',
      tabindex: 0,
      role:    'button',
      'aria-label': `F(${sq.fib_index}) = ${sq.value}`,
    });
    rect.style.fill = squareFill(sq);
    if (i === selectedIdx) rect.classList.add('selected');

    rect.addEventListener('click', () => handleSquareClick(i));
    rect.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleSquareClick(i);
      }
    });

    g.appendChild(rect);

    // Label: show the Fibonacci value for squares large enough to read
    const minSideForLabel = maxSide * 0.035;
    if (sq.side >= minSideForLabel) {
      const fontSize = sq.side * 0.22;
      const text = svgEl('text', {
        x:                  sq.x + sq.side / 2,
        y:                  sq.y + sq.side / 2,
        class:              'square-label',
        'text-anchor':      'middle',
        'dominant-baseline':'middle',
        'font-size':        fontSize,
      });
      text.textContent = sq.value;
      g.appendChild(text);
    }

    svg.appendChild(g);
  });
}

function refreshColors() {
  const squares = spiralData?.squares ?? [];
  svg.querySelectorAll('.spiral-square').forEach((rect, i) => {
    rect.style.fill = squareFill(squares[i]);
  });
}

// ── Side panel ────────────────────────────────────────────────────────────

function openPanel(content) {
  panelInner.innerHTML = content;
  sidePanel.classList.add('open');
}

function closePanel() {
  sidePanel.classList.remove('open');
  selectedIdx = null;
  svg.querySelectorAll('.selected').forEach(el => el.classList.remove('selected'));
}

function handleSquareClick(idx) {
  const squares = spiralData.squares;
  const sq      = squares[idx];

  // Toggle off if same square clicked again
  if (selectedIdx === idx && sidePanel.classList.contains('open')) {
    closePanel();
    return;
  }

  selectedIdx = idx;
  svg.querySelectorAll('.selected').forEach(el => el.classList.remove('selected'));
  svg.querySelectorAll('.spiral-square')[idx]?.classList.add('selected');

  if (storyPointsMode) {
    openPanel(buildSpPanel(sq));
  } else {
    const fact = getFact(sq.fib_index);
    openPanel(buildFactPanel(sq, fact));
  }
}

function buildFactPanel(sq, fact) {
  const ratio = sq.ratio_to_previous != null
    ? `≈ ${sq.ratio_to_previous.toFixed(6)}`
    : '—';
  const catColor = CATEGORY_COLORS[fact?.category] ?? '#6b7280';
  const catLabel = fact?.category ?? 'unknown';

  return `
    <div class="panel-index-badge">F(${sq.fib_index})</div>
    <div class="panel-value">${sq.value}</div>
    <div class="panel-label">Fibonacci number at index ${sq.fib_index}</div>

    <div class="panel-ratio">
      <span>F(${sq.fib_index}) / F(${sq.fib_index - 1})</span>
      <span class="ratio-num">${ratio}</span>
      <span style="color:var(--text-muted);font-size:.75rem">→ φ ≈ 1.618034</span>
    </div>

    <span class="category-badge"
          style="background:${catColor}26;color:${catColor};border:1px solid ${catColor}55">
      ${catLabel}
    </span>

    <p class="panel-fact">${escHtml(fact?.fact ?? 'No fact available.')}</p>
  `;
}

function buildSpPanel(sq) {
  const sp = getSpEntry(sq.value);
  const col = getSpColor(sq.value);

  return `
    <div class="panel-index-badge">F(${sq.fib_index}) — Story Points</div>
    <div class="sp-size" style="color:${col}">${sp.label} SP</div>
    <div class="sp-heading">${escHtml(sp.heading)}</div>

    <p class="sp-story">${escHtml(sp.story)}</p>

    ${sp.note ? `<p class="sp-note">ℹ️ ${escHtml(sp.note)}</p>` : ''}

    <div class="panel-ratio" style="margin-top:1rem">
      <span>Fibonacci value</span>
      <span class="ratio-num" style="color:${col}">${sq.value}</span>
    </div>
  `;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Event listeners ───────────────────────────────────────────────────────

spToggle.addEventListener('click', () => {
  storyPointsMode = !storyPointsMode;
  spToggle.setAttribute('aria-pressed', storyPointsMode);
  spToggle.classList.toggle('active', storyPointsMode);

  refreshColors();

  // Refresh open panel with new mode's content
  if (sidePanel.classList.contains('open') && selectedIdx !== null) {
    const sq   = spiralData.squares[selectedIdx];
    const fact = getFact(sq.fib_index);
    openPanel(storyPointsMode ? buildSpPanel(sq) : buildFactPanel(sq, fact));
  }
});

panelClose.addEventListener('click', closePanel);

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closePanel();
});

// ── Data loading ──────────────────────────────────────────────────────────

async function loadData() {
  try {
    const [spiralRes, factsRes] = await Promise.all([
      fetch('data.json'),
      fetch('fibonacci-facts.json'),
    ]);

    if (!spiralRes.ok)
      throw new Error(`data.json: HTTP ${spiralRes.status}`);
    if (!factsRes.ok)
      throw new Error(`fibonacci-facts.json: HTTP ${factsRes.status}`);

    spiralData = await spiralRes.json();
    factsData  = await factsRes.json();

    overlay.classList.add('hidden');
    render();
  } catch (err) {
    overlayMsg.textContent = `Error: ${err.message}`;
    console.error(err);
  }
}

loadData();
