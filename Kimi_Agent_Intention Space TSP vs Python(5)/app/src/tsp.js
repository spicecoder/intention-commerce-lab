const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));

// Exact small-instance TSP for distributed attendance.
const domains = [
  { name: 'Identity', x: 340, y: 62 },
  { name: 'Orders', x: 550, y: 138 },
  { name: 'Payments', x: 560, y: 320 },
  { name: 'Inventory', x: 340, y: 388 },
  { name: 'Audit', x: 116, y: 320 },
  { name: 'Support', x: 100, y: 138 }
];
const baseMatrix = [
  [0, 8, 12, 15, 10, 7],
  [8, 0, 6, 10, 14, 9],
  [12, 6, 0, 7, 9, 13],
  [15, 10, 7, 0, 8, 11],
  [10, 14, 9, 8, 0, 6],
  [7, 9, 13, 11, 6, 0]
];
const profiles = {
  balanced: { label: 'BALANCED RESOURCES', pressure: [1, 1, 1, 1, 1, 1] },
  energy: { label: 'ENERGY PRESSURE', pressure: [1, 3, 8, 6, 2, 4] },
  latency: { label: 'LATENCY PRESSURE', pressure: [6, 2, 5, 3, 1, 7] }
};

// Each domain participation has a local DN contract and a unique situated address.
// A Colosseum mapping creates the receiving context; it does not silently reuse a Pulse across Spaces.
const participations = [
  { space: 'IDENTITY', dn: 'DN-00', action: 'resolve_participant', inputPulse: 'P00', input: 'participant.request', outputPulse: 'P01', output: 'participant.context' },
  { space: 'ORDERS', dn: 'DN-05', action: 'emit_order_transition', inputPulse: 'P51', input: 'order.context', outputPulse: 'P56', output: 'order.transition' },
  { space: 'PAYMENTS', dn: 'DN-04', action: 'validate_authority', inputPulse: 'P38', input: 'authority.request', outputPulse: 'P42', output: 'authority.checked' },
  { space: 'INVENTORY', dn: 'DN-03', action: 'observe_stock', inputPulse: 'P27', input: 'stock.query', outputPulse: 'P31', output: 'stock.observed' },
  { space: 'AUDIT', dn: 'DN-02', action: 'validate_record', inputPulse: 'P19', input: 'record.context', outputPulse: 'P23', output: 'record.checked' },
  { space: 'SUPPORT', dn: 'DN-01', action: 'observe_case', inputPulse: 'P09', input: 'case.request', outputPulse: 'P17', output: 'case.observed' }
];
const returnParticipation = {
  space: 'IDENTITY', dn: 'DN-00', action: 'close_cycle', inputPulse: 'P60', input: 'cycle.summary', outputPulse: 'P64', output: 'cycle.provenance'
};
let activeProfile = 'balanced';
let activeMatrix = baseMatrix;
let activeRoute = [];
let routeAnimation = 0;

function matrixFor(profile) {
  if (profile === 'balanced') return baseMatrix.map(row => [...row]);
  const pressure = profiles[profile].pressure;
  const factor = profile === 'energy' ? 1.25 : 1.5;
  const baseFactor = profile === 'energy' ? 0.8 : 0.7;
  return baseMatrix.map((row, i) => row.map((value, j) =>
    i === j ? 0 : Math.round(value * baseFactor + (pressure[i] + pressure[j]) * factor)
  ));
}

function solveTSP(matrix) {
  const n = matrix.length;
  const dp = new Map();
  const key = (mask, j) => `${mask}:${j}`;
  dp.set(key(1, 0), { cost: 0, previous: null });

  for (let mask = 1; mask < (1 << n); mask += 1) {
    if (!(mask & 1)) continue;
    for (let j = 1; j < n; j += 1) {
      if (!(mask & (1 << j))) continue;
      const previousMask = mask ^ (1 << j);
      let best = { cost: Infinity, previous: null };
      for (let i = 0; i < n; i += 1) {
        if (!(previousMask & (1 << i))) continue;
        const prior = dp.get(key(previousMask, i));
        if (!prior) continue;
        const cost = prior.cost + matrix[i][j];
        if (cost < best.cost) best = { cost, previous: i };
      }
      dp.set(key(mask, j), best);
    }
  }

  const full = (1 << n) - 1;
  let best = { cost: Infinity, last: null };
  for (let j = 1; j < n; j += 1) {
    const cost = dp.get(key(full, j)).cost + matrix[j][0];
    if (cost < best.cost) best = { cost, last: j };
  }

  const reversed = [];
  let mask = full;
  let current = best.last;
  while (current !== 0) {
    reversed.push(current);
    const previous = dp.get(key(mask, current)).previous;
    mask ^= 1 << current;
    current = previous;
  }
  return { cost: best.cost, route: [0, ...reversed.reverse(), 0] };
}

const edgeHost = document.getElementById('route-edges');
const nodeHost = document.getElementById('route-nodes');
for (let i = 0; i < domains.length; i += 1) {
  for (let j = i + 1; j < domains.length; j += 1) {
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', domains[i].x); line.setAttribute('y1', domains[i].y);
    line.setAttribute('x2', domains[j].x); line.setAttribute('y2', domains[j].y);
    edgeHost.append(line);
  }
}
domains.forEach((domain, index) => {
  const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  group.setAttribute('class', 'route-node');
  group.setAttribute('transform', `translate(${domain.x} ${domain.y})`);
  group.dataset.index = String(index);
  const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
  title.textContent = `${domain.name} domain`;
  const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  circle.setAttribute('r', '30');
  const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  label.setAttribute('y', '-46'); label.textContent = domain.name.toUpperCase();
  const resource = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  resource.setAttribute('class', 'resource'); resource.setAttribute('y', '53');
  group.append(title, circle, label, resource);
  nodeHost.append(group);
});

const attendancePath = document.getElementById('attendance-path');
const attendanceFollower = document.getElementById('attendance-follower');
attendanceFollower.setAttribute('cx', '0');
attendanceFollower.setAttribute('cy', '0');
const routeLog = document.getElementById('route-log');
const runButton = document.getElementById('run-route');

function updateRoute() {
  cancelAnimationFrame(routeAnimation);
  runButton.disabled = false;
  runButton.firstElementChild.textContent = 'Run attendance cycle';
  activeMatrix = matrixFor(activeProfile);
  const result = solveTSP(activeMatrix);
  activeRoute = result.route;
  document.getElementById('route-cost').textContent = String(result.cost);
  document.getElementById('route-mode-label').textContent = profiles[activeProfile].label;
  const points = activeRoute.map(index => domains[index]);
  attendancePath.setAttribute('d', points.map((point, index) =>
    `${index === 0 ? 'M' : 'L'}${point.x} ${point.y}`).join(' '));
  const length = attendancePath.getTotalLength();
  attendancePath.style.strokeDasharray = String(length);
  attendancePath.style.strokeDashoffset = '0';
  attendanceFollower.style.opacity = '0';

  routeLog.replaceChildren();
  activeRoute.slice(1).forEach((domainIndex, step) => {
    const from = activeRoute[step];
    const isReturn = step === activeRoute.length - 2;
    const participation = isReturn ? returnParticipation : participations[domainIndex];
    const item = document.createElement('li');

    const name = document.createElement('span');
    name.className = 'route-domain';
    name.textContent = isReturn ? `Return to ${domains[domainIndex].name}` : domains[domainIndex].name;
    const cost = document.createElement('span');
    cost.className = 'route-leg';
    cost.textContent = `+${activeMatrix[from][domainIndex]}`;

    const activation = document.createElement('div');
    activation.className = 'route-activation';
    const action = document.createElement('b');
    action.textContent = `${participation.dn} / ${participation.action}`;
    const pulses = document.createElement('span');
    pulses.textContent = `IN ${participation.inputPulse} ${participation.input} → OUT ${participation.outputPulse} ${participation.output} / Y`;
    const address = document.createElement('code');
    address.textContent = `U01/C04/IS-${participation.space}/SIT-22/${participation.dn}/α${String(step + 1).padStart(2, '0')}`;
    activation.append(action, pulses, address);

    const handoff = document.createElement('div');
    handoff.className = 'route-handoff';
    if (!isReturn) {
      const nextIndex = activeRoute[step + 1];
      const nextParticipation = step + 1 === activeRoute.length - 2 ? returnParticipation : participations[nextIndex];
      handoff.textContent = `C–MAP ${String(step + 1).padStart(2, '0')} · ${participation.outputPulse} ${participation.output} → ${nextParticipation.inputPulse} ${nextParticipation.input}`;
    } else {
      handoff.textContent = `RETURN RESOLUTION · ${participation.outputPulse} ${participation.output} → attendance DN / Y`;
    }

    item.append(name, cost, activation, handoff);
    routeLog.append(item);
  });

  [...nodeHost.children].forEach((node, index) => {
    node.classList.remove('active');
    node.querySelector('.resource').textContent = `${participations[index].dn} / weight ${profiles[activeProfile].pressure[index]}`;
  });
}

document.querySelectorAll('[data-preset]').forEach(button => {
  button.addEventListener('click', () => {
    activeProfile = button.dataset.preset;
    document.querySelectorAll('[data-preset]').forEach(item => {
      const active = item === button;
      item.classList.toggle('active', active);
      item.setAttribute('aria-pressed', String(active));
    });
    updateRoute();
  });
});

runButton.addEventListener('click', () => {
  cancelAnimationFrame(routeAnimation);
  const length = attendancePath.getTotalLength();
  const items = [...routeLog.children];
  const nodes = [...nodeHost.children];
  items.forEach(item => item.classList.remove('active'));
  nodes.forEach(node => node.classList.remove('active'));

  if (reducedMotion) {
    items.forEach(item => item.classList.add('active'));
    nodes.forEach(node => node.classList.add('active'));
    return;
  }

  runButton.disabled = true;
  runButton.firstElementChild.textContent = 'Attending domains…';
  attendanceFollower.style.opacity = '1';
  const start = performance.now();
  const duration = 2400;

  function frame(now) {
    const progress = clamp((now - start) / duration);
    const point = attendancePath.getPointAtLength(length * progress);
    attendanceFollower.style.transform = `translate(${point.x}px, ${point.y}px)`;
    attendancePath.style.strokeDashoffset = String(length * (1 - progress));
    const step = Math.min(activeRoute.length - 1, Math.floor(progress * (activeRoute.length - 1)));
    nodes.forEach((node, index) => node.classList.toggle('active', activeRoute.slice(0, step + 1).includes(index)));
    items.forEach((item, index) => item.classList.toggle('active', index < step));
    if (progress < 1) {
      routeAnimation = requestAnimationFrame(frame);
    } else {
      attendanceFollower.style.opacity = '0';
      items.forEach(item => item.classList.add('active'));
      nodes.forEach(node => node.classList.add('active'));
      runButton.disabled = false;
      runButton.firstElementChild.textContent = 'Run attendance cycle';
    }
  }
  attendancePath.style.strokeDashoffset = String(length);
  routeAnimation = requestAnimationFrame(frame);
});
updateRoute();
