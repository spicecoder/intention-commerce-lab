const activations = [
  { stage:'Establish customer context', host:'CRM / CUSTOMER', dn:'DN_CRMStart', intention:'I_CustomerContextRequested', input:'S_StartCustomer', output:'S_CustomerContext', pulses:['customer_id'] },
  { stage:'Assess available stock', host:'SPRING BOOT / INVENTORY', dn:'DN_InventoryRead', intention:'I_CustomerContextAvailable', input:'S_CustomerContext', output:'S_StockAssessed', pulses:['customer_id','customer_profile'] },
  { stage:'Generate recommendations', host:'CRM / CUSTOMER', dn:'DN_CRMRecommend', intention:'I_CustomerStockAssessed', input:'S_StockAssessed', output:'S_RecommendationsReady', pulses:['customer_id','customer_profile','inventory_rows'] },
  { stage:'Create order draft', host:'NODE.JS / ORDERS', dn:'DN_OrdersDraft', intention:'I_OrderDraftRequested', input:'S_CreateDraft', output:'S_DraftReady', pulses:['customer_id','sku','quantity'] },
  { stage:'Submit order', host:'NODE.JS / ORDERS', dn:'DN_OrdersSubmit', intention:'I_OrderSubmissionRequested', input:'S_SubmitOrder', output:'S_ReservationRequested', pulses:['order_id'] },
  { stage:'Reserve stock', host:'SPRING BOOT / INVENTORY', dn:'DN_InventoryReserve', intention:'I_StockReservationRequested', input:'S_ReservationRequested', output:'S_ReservationDecision', pulses:['order_id','sku','quantity'] },
  { stage:'Apply reservation decision', host:'NODE.JS / ORDERS', dn:'DN_OrdersDecide', intention:'I_StockReservationDecided', input:'S_ReservationDecision', output:'S_OrderDecision', pulses:['order_id','reservation_id','reservation_status','failure_reason'] },
  { stage:'Prepare shipment', host:'SHIPPING / FULFILLMENT', dn:'DN_ShippingPrepare', intention:'I_OrderAcceptanceDecided', input:'S_OrderDecision', output:'S_ShipmentReady', pulses:['order_id','reservation_id','order_status'] },
  { stage:'Dispatch shipment', host:'SHIPPING / FULFILLMENT', dn:'DN_ShippingDispatch', intention:'I_ShipmentDispatchRequested', input:'S_DispatchShipment', output:'S_DispatchDecision', pulses:['shipment_id'] },
  { stage:'Commit reserved stock', host:'SPRING BOOT / INVENTORY', dn:'DN_InventoryCommit', intention:'I_ShipmentDispatchDecided', input:'S_DispatchDecision', output:'S_StockCommitted', pulses:['order_id','reservation_id','shipment_id','dispatch_status'] },
  { stage:'Complete order', host:'NODE.JS / ORDERS', dn:'DN_OrdersComplete', intention:'I_ReservedStockConsumed', input:'S_StockCommitted', output:'S_OrderCompleted', pulses:['order_id','shipment_id','tracking_id'] },
  { stage:'Update customer history', host:'CRM / CUSTOMER', dn:'DN_CRMClose', intention:'I_OrderShipmentCompleted', input:'S_OrderCompleted', output:'S_CustomerHistoryUpdated', pulses:['order_id','customer_id','tracking_id'] }
];
const scenarioData = {
  success:{label:'Successful path', stop:11, resolution:'Y', title:'Customer history updated', copy:'All twelve reference activations resolve Y. This is a computed declaration trace, not a live enterprise transaction.'},
  insufficient:{label:'Insufficient stock', stop:5, resolution:'N', title:'Reservation conflict returned', copy:'DN_InventoryReserve resolves N. The reference path stops before shipment; successful transport must not turn this business N into Y.'},
  timeout:{label:'Ambiguous timeout', stop:5, resolution:'U', title:'Reservation remains unresolved', copy:'DN_InventoryReserve resolves U. Automatic advancement stops because the reservation may require independent observation or reconciliation.'}
};
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
let scenario = 'success';
let currentStep = -1;
let selectedIndex = 0;
let timer = 0;
const buttons = [];
const list = document.getElementById('commerce-stage-list');
const nextButton = document.getElementById('advance-trace');
const runButton = document.getElementById('run-trace');
const backButton = document.getElementById('back-trace');

function resolutionAt(index) {
  if (scenario === 'success' || index < 5) return 'Y';
  if (index === 5) return scenarioData[scenario].resolution;
  return '—';
}
function selectActivation(index) {
  selectedIndex = index;
  const activation = activations[index];
  buttons.forEach((button, i) => {
    button.classList.toggle('active', i === index);
    button.setAttribute('aria-pressed', String(i === index));
    button.classList.toggle('executed', i <= currentStep);
  });
  document.getElementById('commerce-detail-step').textContent = `${String(index + 1).padStart(2,'0')} / ${activations.length}`;
  document.getElementById('commerce-detail-host').textContent = activation.host;
  document.getElementById('commerce-detail-dn').textContent = activation.dn;
  document.getElementById('commerce-detail-stage').textContent = `${activation.stage}.`;
  document.getElementById('commerce-detail-intention').textContent = activation.intention;
  document.getElementById('commerce-detail-input').textContent = activation.input;
  document.getElementById('commerce-detail-output').textContent = activation.output;
  document.getElementById('commerce-detail-resolution').textContent = resolutionAt(index);
  document.getElementById('commerce-detail-address').textContent = `U01/C04/IS_CommerceReference/SIT-ORDER-184/${activation.dn}/α${String(index + 1).padStart(2,'0')}`;
  const host = document.getElementById('commerce-detail-pulses');
  host.replaceChildren(...activation.pulses.map(name => {
    const code = document.createElement('code'); code.textContent = name; return code;
  }));
}
function terminal() { return currentStep >= scenarioData[scenario].stop; }
function updateState() {
  const data = scenarioData[scenario];
  const code = currentStep < 0 ? '—' : resolutionAt(currentStep);
  document.getElementById('trace-resolution').textContent = code;
  document.getElementById('trace-scenario').textContent = data.label;
  document.getElementById('trace-title').textContent = currentStep < 0 ? 'No activation admitted yet' : terminal() ? data.title : `${activations[currentStep].dn} emitted ${activations[currentStep].output}`;
  document.getElementById('trace-copy').textContent = currentStep < 0 ? 'Choose a scenario, then advance one transition. Selecting a stage inspects its declaration without advancing the trace.' : terminal() ? data.copy : `Reference activation ${currentStep + 1} of ${activations.length} is complete. Its declared output can become the next participation input with its resolution preserved.`;
  document.getElementById('trace-progress-fill').style.width = `${((currentStep + 1) / activations.length) * 100}%`;
  nextButton.disabled = terminal() || Boolean(timer);
  runButton.disabled = terminal() || Boolean(timer);
  backButton.disabled = currentStep < 0 || Boolean(timer);
  buttons.forEach((button, i) => {
    button.classList.toggle('executed', i <= currentStep);
    button.disabled = Boolean(timer);
  });
  document.querySelectorAll('[data-trace-scenario]').forEach(tab => { tab.disabled = Boolean(timer); });
}
function advance() {
  if (terminal()) { clearInterval(timer); timer = 0; updateState(); return; }
  currentStep += 1;
  selectActivation(currentStep);
  updateState();
  if (terminal() && timer) { clearInterval(timer); timer = 0; updateState(); }
}
function stopRunning() { if (timer) clearInterval(timer); timer = 0; updateState(); }
function resetTrace() {
  stopRunning(); currentStep = -1; selectedIndex = 0; selectActivation(0); updateState();
}
activations.forEach((activation, index) => {
  const button = document.createElement('button'); button.type = 'button'; button.className = 'commerce-stage'; button.setAttribute('aria-pressed','false');
  const number = document.createElement('span'); number.className = 'stage-number'; number.textContent = String(index + 1).padStart(2,'0');
  const name = document.createElement('span'); name.className = 'stage-name'; name.textContent = activation.stage;
  const dn = document.createElement('span'); dn.className = 'stage-dn'; dn.textContent = activation.dn;
  button.append(number,name,dn); button.addEventListener('click',() => selectActivation(index)); list.append(button); buttons.push(button);
});
const tabs = [...document.querySelectorAll('[data-trace-scenario]')];
function selectScenario(tab, focus = false) {
  stopRunning(); scenario = tab.dataset.traceScenario;
  tabs.forEach(item => { const active = item === tab; item.setAttribute('aria-selected',String(active)); item.tabIndex = active ? 0 : -1; });
  resetTrace(); if (focus) tab.focus();
}
tabs.forEach((tab,index) => {
  tab.addEventListener('click',() => selectScenario(tab));
  tab.addEventListener('keydown',event => {
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
    event.preventDefault(); let next = index;
    if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
    if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = tabs.length - 1;
    selectScenario(tabs[next],true);
  });
});
nextButton.addEventListener('click',advance);
backButton.addEventListener('click',() => { if (currentStep >= 0) { currentStep -= 1; selectActivation(Math.max(0,currentStep)); updateState(); } });
runButton.addEventListener('click',() => {
  if (terminal()) return;
  if (reducedMotion) { while (!terminal()) advance(); return; }
  timer = window.setInterval(advance,280); updateState();
});
document.getElementById('reset-trace').addEventListener('click',resetTrace);
resetTrace();
