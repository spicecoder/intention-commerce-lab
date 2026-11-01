const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const clamp = value => Math.min(1, Math.max(0, value));

// One visible Signal path, with a separate returning resolution path.
const heroPath = document.getElementById('hero-path');
const heroFollower = document.getElementById('hero-follower');
if (heroPath && heroFollower) {
  const length = heroPath.getTotalLength();
  const place = progress => {
    const point = heroPath.getPointAtLength(length * progress);
    heroFollower.style.transform = `translate(${point.x}px, ${point.y}px)`;
  };
  heroFollower.setAttribute('cx', '0');
  heroFollower.setAttribute('cy', '0');
  place(0);
  if (!reducedMotion) {
    const started = performance.now();
    const animate = now => {
      place(((now - started) / 5200) % 1);
      requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }
}

// The failure guard preserves business resolution independently of transport.
const scenarios = {
  timeout: {
    code: 'U', title: 'Outcome remains unresolved',
    copy: 'The request timed out. The payment may already have happened, so an automatic retry could duplicate the effect.',
    rule: 'Block retry. Request an independent observation of payment state.', effect: 'Payment state'
  },
  conflict: {
    code: 'N', title: 'Authority conflicts with the request',
    copy: 'The agent can propose a refund, but its situated authority does not permit this amount in the governing Intention Space.',
    rule: 'Block the effect. Preserve the conflict and route it to an authorized participant.', effect: 'Authority scope'
  },
  resolved: {
    code: 'Y', title: 'Effect observed in context',
    copy: 'The designated DN emitted its output Signal and an independent observation confirms the intended payment state.',
    rule: 'Carry the returning resolution Pulse into the next Signal exchange.', effect: 'Payment observed'
  }
};
const scenarioTabs = [...document.querySelectorAll('[data-scenario]')];
function selectScenario(tab, focus = false) {
  const data = scenarios[tab.dataset.scenario];
  scenarioTabs.forEach(item => {
    const selected = item === tab;
    item.setAttribute('aria-selected', String(selected));
    item.tabIndex = selected ? 0 : -1;
  });
  document.getElementById('scenario-panel').setAttribute('aria-labelledby', tab.id);
  document.getElementById('resolution-code').textContent = data.code;
  document.getElementById('resolution-title').textContent = data.title;
  document.getElementById('resolution-copy').textContent = data.copy;
  document.getElementById('guard-rule-copy').textContent = data.rule;
  document.getElementById('scenario-effect').textContent = data.effect;
  if (focus) tab.focus();
}
scenarioTabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectScenario(tab));
  tab.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    let next = index;
    if (event.key === 'ArrowRight') next = (index + 1) % scenarioTabs.length;
    if (event.key === 'ArrowLeft') next = (index - 1 + scenarioTabs.length) % scenarioTabs.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = scenarioTabs.length - 1;
    selectScenario(scenarioTabs[next], true);
  });
});

// Cooperation hierarchy: scroll only accents content that is already readable.
const modelLevels = document.querySelector('.model-levels');
const modelLine = document.getElementById('model-line-active');
const modelDot = document.getElementById('model-line-dot');
const progressHost = document.querySelector('.model-progress');
if (modelLevels && modelLine && modelDot && progressHost) {
  for (let i = 0; i < 12; i += 1) progressHost.append(document.createElement('i'));
  const bars = [...progressHost.children];
  const length = modelLine.getTotalLength();
  modelLine.style.strokeDasharray = String(length);
  let queued = false;
  const update = () => {
    const rect = modelLevels.getBoundingClientRect();
    const progress = reducedMotion ? 1 : clamp((window.innerHeight * .62 - rect.top) / rect.height);
    modelLine.style.strokeDashoffset = String(length * (1 - progress));
    modelDot.setAttribute('transform', `translate(0 ${1000 * progress})`);
    bars.forEach((bar, index) => bar.classList.toggle('active', progress * 12 > index));
    queued = false;
  };
  window.addEventListener('scroll', () => {
    if (!queued) { queued = true; requestAnimationFrame(update); }
  }, { passive: true });
  window.addEventListener('resize', update);
  update();
}
