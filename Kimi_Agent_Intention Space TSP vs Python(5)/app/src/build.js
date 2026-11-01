const checklistForm = document.getElementById('participation-form');
const checklistInputs = [...checklistForm.querySelectorAll('input[type="checkbox"]')];
const copyStatus = document.getElementById('copy-status');
function updateChecklist() {
  const complete = checklistInputs.filter(input => input.checked).length;
  document.getElementById('check-count').textContent = `${complete} / ${checklistInputs.length}`;
  document.getElementById('meter-fill').style.width = `${(complete / checklistInputs.length) * 100}%`;
}
checklistInputs.forEach(input => input.addEventListener('change',updateChecklist));
function checklistText() {
  const lines = ['INTENTION SPACE — PARTICIPATION CHECKLIST',''];
  checklistForm.querySelectorAll('fieldset').forEach(fieldset => {
    lines.push(fieldset.querySelector('legend').textContent.toUpperCase());
    fieldset.querySelectorAll('input[type="checkbox"]').forEach(input => lines.push(`${input.checked ? '[•]' : '[ ]'} ${input.value}`));
    lines.push('');
  });
  lines.push(`Completion: ${checklistInputs.filter(input => input.checked).length}/${checklistInputs.length}`);
  return lines.join('\n');
}
async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(text); return; }
  const textarea = document.createElement('textarea'); textarea.value = text; textarea.style.position = 'fixed'; textarea.style.opacity = '0'; document.body.append(textarea); textarea.select();
  const copied = document.execCommand('copy'); textarea.remove(); if (!copied) throw new Error('Copy unavailable');
}
document.getElementById('copy-checklist').addEventListener('click',async () => {
  try { await copyText(checklistText()); copyStatus.textContent = 'Checklist copied with its current completion state.'; }
  catch { copyStatus.textContent = 'Copy is unavailable in this browser. Use Print to save a copy.'; }
});
document.getElementById('print-checklist').addEventListener('click',() => window.print());
document.getElementById('reset-checklist').addEventListener('click',() => { checklistForm.reset(); updateChecklist(); copyStatus.textContent = 'Checklist reset.'; });
updateChecklist();
