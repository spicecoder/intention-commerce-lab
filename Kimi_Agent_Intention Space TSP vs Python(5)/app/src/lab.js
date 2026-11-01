const form = document.getElementById('signal-form');
const output = document.getElementById('signal-json');
const diagnosticsHost = document.getElementById('lab-diagnostics');
const fingerprintHost = document.getElementById('signal-fingerprint');
let experiment = 'none';

function values() {
  return {
    customer: document.getElementById('lab-customer').value.trim(),
    sku: document.getElementById('lab-sku').value.trim(),
    quantity: Number(document.getElementById('lab-quantity').value)
  };
}
function makeSignal() {
  const data = values();
  const pulses = [
    { name:'customer_id', tv:'Y', R:data.customer },
    { name:'sku', tv:experiment === 'invalid-tv' ? 'perhaps' : 'Y', R:data.sku },
    { name:'quantity', tv:'Y', R:data.quantity }
  ];
  if (experiment === 'duplicate') pulses.push({ name:'customer_id', tv:'Y', R:data.customer });
  return { signal:'S_CreateDraft', space:'IS_CommerceReference/v1', intention:'I_OrderDraftRequested', pulses };
}
function validate(signal) {
  const findings = [];
  const allowed = new Set(['Y','U','N']);
  const identities = new Set();
  signal.pulses.forEach(pulse => {
    const id = `${pulse.name}+${pulse.tv}`;
    if (identities.has(id)) findings.push(`DUPLICATE_PULSE: ${id} occurs more than once in the Pulse set.`);
    identities.add(id);
    if (!allowed.has(pulse.tv)) findings.push(`INVALID_TV: ${pulse.name} uses ${pulse.tv}; expected Y, U, or N.`);
  });
  const required = ['customer_id','sku','quantity'];
  required.forEach(name => { if (!signal.pulses.some(p => p.name === name)) findings.push(`MISSING_PULSE: ${name} is required.`); });
  if (!signal.pulses[0].R) findings.push('INVALID_RESPONSE: customer_id must be non-empty.');
  if (!signal.pulses[1].R) findings.push('INVALID_RESPONSE: sku must be non-empty.');
  if (!Number.isInteger(signal.pulses[2].R) || signal.pulses[2].R < 1) findings.push('INVALID_RESPONSE: quantity must be a positive integer.');
  return findings;
}
async function fingerprint(signal) {
  const semantic = JSON.stringify({ intention:signal.intention, pulses:signal.pulses.map(p => ({name:p.name,tv:p.tv})).sort((a,b) => `${a.name}+${a.tv}`.localeCompare(`${b.name}+${b.tv}`)) });
  if (!window.crypto?.subtle) return `Semantic form: ${semantic}`;
  const bytes = new TextEncoder().encode(semantic);
  const digest = await window.crypto.subtle.digest('SHA-256',bytes);
  return [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2,'0')).join('');
}
async function analyze() {
  const signal = makeSignal();
  const findings = validate(signal);
  output.textContent = JSON.stringify(signal,null,2);
  fingerprintHost.textContent = await fingerprint(signal);
  diagnosticsHost.replaceChildren();
  if (!findings.length) {
    const valid = document.createElement('p'); valid.className = 'valid'; valid.textContent = 'VALID: declared Signal form passes these structural checks.';
    const note = document.createElement('p'); note.textContent = 'Response values are excluded from the semantic fingerprint. Changing R alone does not change it.';
    diagnosticsHost.append(valid,note);
  } else {
    findings.forEach(text => { const item = document.createElement('p'); item.className = 'invalid'; item.textContent = text; diagnosticsHost.append(item); });
  }
}
function setExperiment(next) {
  experiment = next;
  document.querySelectorAll('[data-experiment]').forEach(button => button.setAttribute('aria-pressed',String(button.dataset.experiment === next)));
  analyze();
}
form.addEventListener('submit',event => { event.preventDefault(); analyze(); });
document.querySelectorAll('[data-experiment]').forEach(button => button.addEventListener('click',() => setExperiment(button.dataset.experiment)));
analyze();
