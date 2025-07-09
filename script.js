/* ============================================================
   1. Navbar toggle (mobile)
   2. Live update of km‑driven slider
   3. Cascading Brand → Model → Year dropdowns
        3‑a.  Fetch brand‑model map at load
        3‑b.  Populate models when a brand is chosen
        3‑c.  Fetch & populate years when a model is chosen
   4. POST /predict to get the estimated price
   (2025 • Yatharth)
   ============================================================ */

/* ---------- 1. Navbar toggle ---------- */
document.getElementById('navToggle').addEventListener('click', () =>
  document.querySelector('.nav-links').classList.toggle('show')
);

/* ---------- 2. Live km‑slider display ---------- */
const kmsRange = document.getElementById('kms');   // <input type="range">
const kmsVal   = document.getElementById('kmsVal'); // <span> showing value

kmsVal.textContent = kmsRange.value;               // initialise on load
kmsRange.addEventListener('input', () =>
  (kmsVal.textContent = kmsRange.value)
);

/* ---------- 3. Cascading Brand → Model → Year ---------- */
const brandSel = document.getElementById('brand');
const modelSel = document.getElementById('model');
const yearSel  = document.getElementById('year');

let brandMap = {}; // { "Maruti": ["Swift", "Baleno", …], … }

/* 3‑a. Fetch brand→models map once */
fetch('/brand_models')
  .then(r => r.json())
  .then(data => {
    brandMap = data;
    Object.keys(brandMap)
      .sort()
      .forEach(brand => brandSel.add(new Option(brand, brand)));
  });

/* 3‑b. When brand changes → populate models */
brandSel.addEventListener('change', () => {
  /* Reset model + year dropdowns */
  modelSel.innerHTML =
    '<option value="" disabled selected>Select model</option>';
  modelSel.disabled = true;

  yearSel.innerHTML =
    '<option value="" disabled selected>Select year</option>';
  yearSel.disabled = true;

  /* Fill model options for chosen brand */
  const models = brandMap[brandSel.value] || [];
  models.sort().forEach(m => modelSel.add(new Option(m, m)));
  modelSel.disabled = !models.length;
});

/* 3‑c. When model changes → fetch valid years */
modelSel.addEventListener('change', () => {
  /* Reset year dropdown */
  yearSel.innerHTML =
    '<option value="" disabled selected>Select year</option>';
  yearSel.disabled = true;

  const b = brandSel.value;
  const m = modelSel.value;
  if (!b || !m) return;

  fetch(`/years/${encodeURIComponent(b)}/${encodeURIComponent(m)}`)
    .then(r => r.json())
    .then(years => {
      years
        .sort((a, b) => b - a)          // newest first
        .forEach(y => yearSel.add(new Option(y, y)));
      yearSel.disabled = !years.length;
    });
});

/* ---------- 4. Price prediction ---------- */
const form       = document.getElementById('predictForm');
const resultBox  = document.getElementById('result');
const predictBtn = document.getElementById('predictBtn');

form.addEventListener('submit', async e => {
  e.preventDefault();

  predictBtn.disabled = true;
  resultBox.textContent = 'Predicting…';

  /* Collect form data */
  const payload = {
    brand       : brandSel.value,
    model       : modelSel.value,
    year        : +yearSel.value,
    km_driven   : +kmsRange.value,
    fuel        : document.getElementById('fuel').value,
    seller_type : document.getElementById('seller').value,
    transmission: document.getElementById('transmission').value,
    owner       : document.getElementById('owner').value
  };

  try {
    const res  = await fetch('/predict', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || res.status);

    /* Format INR price (no decimals) */
    const price = new Intl.NumberFormat('en-IN', {
      style                : 'currency',
      currency             : 'INR',
      maximumFractionDigits: 0
    }).format(data.prediction);

    resultBox.textContent = `Estimated Price: ${price}`;
  } catch (err) {
    console.error(err);
    resultBox.textContent = 'Error… please try again.';
  } finally {
    predictBtn.disabled = false;
  }
});
