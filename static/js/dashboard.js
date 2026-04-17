/* dashboard.js — Loads stats, draws charts, renders history table */

// ── Mini canvas chart helpers ───────────────────────

/** Draw a donut chart on a canvas element */
function drawDonut(canvasId, buyers, nonBuyers) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2;
  const r = Math.min(W, H) / 2 - 20;
  const inner = r * 0.58;

  ctx.clearRect(0, 0, W, H);

  const total = buyers + nonBuyers || 1;
  const segments = [
    { value: buyers,    color: '#1eaa6e' },
    { value: nonBuyers, color: '#e84040' },
  ];

  let startAngle = -Math.PI / 2;
  segments.forEach(seg => {
    const sweep = (seg.value / total) * 2 * Math.PI;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, startAngle, startAngle + sweep);
    ctx.closePath();
    ctx.fillStyle = seg.color;
    ctx.fill();
    startAngle += sweep;
  });

  // Inner hole (donut)
  ctx.beginPath();
  ctx.arc(cx, cy, inner, 0, 2 * Math.PI);
  ctx.fillStyle = '#ffffff';
  ctx.fill();

  // Centre label
  ctx.fillStyle = '#0e0e12';
  ctx.textAlign = 'center';
  ctx.font = 'bold 22px "DM Serif Display", serif';
  ctx.fillText(`${Math.round((buyers / total) * 100)}%`, cx, cy + 4);
  ctx.font = '11px "DM Sans", sans-serif';
  ctx.fillStyle = '#7a7a85';
  ctx.fillText('buy rate', cx, cy + 18);
}

/** Draw a horizontal bar chart showing confidence buckets */
function drawBarChart(canvasId, rows) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  // Bucket confidence scores into ranges
  const buckets = { '0–20': 0, '21–40': 0, '41–60': 0, '61–80': 0, '81–100': 0 };
  rows.forEach(r => {
    const c = r.confidence;
    if      (c <= 20)  buckets['0–20']++;
    else if (c <= 40)  buckets['21–40']++;
    else if (c <= 60)  buckets['41–60']++;
    else if (c <= 80)  buckets['61–80']++;
    else               buckets['81–100']++;
  });

  const labels = Object.keys(buckets);
  const values = Object.values(buckets);
  const maxVal = Math.max(...values, 1);

  const barH    = 28;
  const gapY    = 14;
  const labelW  = 64;
  const padLeft = labelW + 12;
  const padRight = 50;

  ctx.font = '12px "DM Sans", sans-serif';
  ctx.fillStyle = '#7a7a85';

  labels.forEach((lbl, i) => {
    const y = 20 + i * (barH + gapY);
    const barW = ((values[i] / maxVal) * (W - padLeft - padRight)) || 0;

    // Label
    ctx.textAlign = 'right';
    ctx.fillStyle = '#7a7a85';
    ctx.fillText(lbl + '%', labelW, y + barH / 2 + 4);

    // Bar background
    ctx.fillStyle = '#eceae4';
    ctx.beginPath();
    ctx.roundRect(padLeft, y, W - padLeft - padRight, barH, 4);
    ctx.fill();

    // Bar fill
    if (barW > 0) {
      ctx.fillStyle = '#e8a020';
      ctx.beginPath();
      ctx.roundRect(padLeft, y, barW, barH, 4);
      ctx.fill();
    }

    // Count label
    ctx.textAlign = 'left';
    ctx.fillStyle = '#0e0e12';
    ctx.font = 'bold 12px "DM Sans", sans-serif';
    ctx.fillText(values[i], padLeft + barW + 8, y + barH / 2 + 4);
    ctx.font = '12px "DM Sans", sans-serif';
  });
}

// ── Load stats ──────────────────────────────────────
async function loadStats() {
  try {
    const res  = await fetch('/api/stats');
    const data = await res.json();

    document.getElementById('sc-total').textContent    = data.total;
    document.getElementById('sc-buyers').textContent   = data.buyers;
    document.getElementById('sc-nonbuyers').textContent = data.non_buyers;
    document.getElementById('sc-rate').textContent     = `${data.buy_rate}%`;
    document.getElementById('sc-conf').textContent     = `${data.avg_confidence}%`;

    drawDonut('donutChart', data.buyers, data.non_buyers);
  } catch (err) {
    console.error('Stats error', err);
  }
}

// ── Load history ────────────────────────────────────
async function loadHistory() {
  const tbody = document.getElementById('historyBody');
  try {
    const res  = await fetch('/api/history');
    const rows = await res.json();

    document.getElementById('rowCount').textContent = rows.length;

    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="10" class="empty-row">No predictions yet. <a href="/predict">Make one →</a></td></tr>';
      drawBarChart('barChart', []);
      return;
    }

    tbody.innerHTML = rows.map((r, idx) => `
      <tr>
        <td>${idx + 1}</td>
        <td>${r.age}</td>
        <td>${r.gender}</td>
        <td>${parseFloat(r.time_spent).toFixed(1)}</td>
        <td>${r.prev_purchases}</td>
        <td>${r.cart_items}</td>
        <td>${r.discount_used ? '✓' : '—'}</td>
        <td>
          <span class="pill ${r.prediction === 'Will Purchase' ? 'buy' : 'no-buy'}">
            ${r.prediction}
          </span>
        </td>
        <td>${r.confidence}%</td>
        <td>${r.created_at ? r.created_at.substring(0, 16) : '—'}</td>
      </tr>
    `).join('');

    drawBarChart('barChart', rows);

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="10" class="empty-row">Error loading history.</td></tr>`;
    console.error('History error', err);
  }
}

// ── Clear history ───────────────────────────────────
async function clearHistory() {
  if (!confirm('Clear all prediction history? This cannot be undone.')) return;
  try {
    await fetch('/api/history', { method: 'DELETE' });
    loadAll();
  } catch (err) {
    alert('Failed to clear history.');
  }
}

// ── Load everything ─────────────────────────────────
function loadAll() {
  loadStats();
  loadHistory();
}

// Auto-refresh on page load
loadAll();
