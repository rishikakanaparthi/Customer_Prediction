/* predict.js — Handles form validation, API call, and result rendering */

// ── Discount toggle ─────────────────────────────────
function setDiscount(val) {
  document.getElementById('discount_used').value = val;
  document.getElementById('discNo').classList.toggle('active', val === 0);
  document.getElementById('discYes').classList.toggle('active', val === 1);
}

// ── Validation helpers ──────────────────────────────
function showError(fieldId, msg) {
  const el = document.getElementById(fieldId);
  if (el) el.textContent = msg;
  const input = document.getElementById(fieldId.replace('err-', ''));
  if (input) input.classList.add('error');
}

function clearErrors() {
  document.querySelectorAll('.field-error').forEach(e => (e.textContent = ''));
  document.querySelectorAll('.error').forEach(e => e.classList.remove('error'));
}

function validateForm(data) {
  let valid = true;

  if (!data.age || isNaN(data.age) || data.age < 18 || data.age > 100) {
    showError('err-age', 'Enter a valid age between 18 and 100.'); valid = false;
  }
  if (data.gender === '' || data.gender === null) {
    showError('err-gender', 'Please select a gender.'); valid = false;
  }
  if (data.time_spent === '' || isNaN(data.time_spent) || data.time_spent < 0) {
    showError('err-time_spent', 'Enter a valid time ≥ 0 minutes.'); valid = false;
  }
  if (data.prev_purchases === '' || isNaN(data.prev_purchases) || data.prev_purchases < 0) {
    showError('err-prev_purchases', 'Enter a number ≥ 0.'); valid = false;
  }
  if (!data.pages_visited || isNaN(data.pages_visited) || data.pages_visited < 1) {
    showError('err-pages_visited', 'Enter at least 1 page.'); valid = false;
  }
  if (data.cart_items === '' || isNaN(data.cart_items) || data.cart_items < 0) {
    showError('err-cart_items', 'Enter a number ≥ 0.'); valid = false;
  }

  return valid;
}

// ── UI state helpers ────────────────────────────────
function showPanel(id) {
  ['resultIdle', 'resultContent', 'resultError'].forEach(p => {
    document.getElementById(p).classList.add('hidden');
  });
  document.getElementById(id).classList.remove('hidden');
}

function setLoading(loading) {
  const btn     = document.getElementById('submitBtn');
  const txt     = btn.querySelector('.btn-text');
  const spinner = document.getElementById('spinner');
  btn.disabled  = loading;
  txt.classList.toggle('hidden', loading);
  spinner.classList.toggle('hidden', !loading);
}

// ── Render result ───────────────────────────────────
function renderResult(data) {
  const willBuy = data.will_buy;

  // Verdict box
  const verdict = document.getElementById('resultVerdict');
  verdict.className = `result-verdict ${willBuy ? 'buy' : 'no-buy'}`;
  verdict.innerHTML = `
    <div class="verdict-icon">${willBuy ? '🛒' : '👋'}</div>
    <div class="verdict-label">AI Prediction</div>
    <div class="verdict-text ${willBuy ? 'green' : 'red'}">${data.prediction}</div>
  `;

  // Confidence bar
  const conf = data.confidence;
  document.getElementById('confPct').textContent = `${conf}%`;
  setTimeout(() => {
    document.getElementById('confBar').style.width = `${conf}%`;
  }, 100);

  // Meta badges
  document.getElementById('resultMeta').innerHTML = `
    <span class="meta-badge">🤖 Model Accuracy: ${data.model_accuracy}%</span>
    <span class="meta-badge">🎯 Confidence: ${conf}%</span>
  `;

  // Recommendations
  const recList = document.getElementById('recList');
  recList.innerHTML = '';
  if (data.recommendations && data.recommendations.length) {
    data.recommendations.forEach(r => {
      const li = document.createElement('li');
      li.textContent = r;
      recList.appendChild(li);
    });
    document.getElementById('recommendations').style.display = '';
  } else {
    document.getElementById('recommendations').style.display = 'none';
  }

  showPanel('resultContent');
}

// ── Reset form ──────────────────────────────────────
function resetForm() {
  document.getElementById('predictForm').reset();
  setDiscount(0);
  clearErrors();
  document.getElementById('confBar').style.width = '0%';
  showPanel('resultIdle');
}

// ── Form submit ─────────────────────────────────────
document.getElementById('predictForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  clearErrors();

  const getValue = id => document.getElementById(id).value.trim();

  const payload = {
    age:            parseFloat(getValue('age')),
    gender:         getValue('gender') === '' ? null : parseInt(getValue('gender')),
    time_spent:     parseFloat(getValue('time_spent')),
    prev_purchases: parseFloat(getValue('prev_purchases')),
    pages_visited:  parseFloat(getValue('pages_visited')),
    cart_items:     parseFloat(getValue('cart_items')),
    discount_used:  parseInt(document.getElementById('discount_used').value),
  };

  if (!validateForm(payload)) return;

  setLoading(true);

  try {
    const res  = await fetch('/api/predict', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      document.getElementById('errorMsg').textContent = data.error || 'Unknown error.';
      showPanel('resultError');
      return;
    }

    renderResult(data);

  } catch (err) {
    document.getElementById('errorMsg').textContent = 'Could not reach the server. Is Flask running?';
    showPanel('resultError');
  } finally {
    setLoading(false);
  }
});
