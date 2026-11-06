import { initStages } from "./stages.js";
import { initReveal } from "./reveal.js";
import { initForm } from "./form.js";

const stages = initStages();
initReveal();
initForm();

const pins = {
  hero: document.querySelector('[data-pin="hero"]'),
  wipe: document.querySelector('[data-pin="wipe"]'),
  timeline: document.querySelector('[data-pin="timeline"]'),
  map: document.querySelector('[data-pin="map"]'),
};

const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
let ticking = false;
let scrollAttached = false;

function progressFor(element) {
  if (!element) return 0;

  const rect = element.getBoundingClientRect();
  const distance = element.offsetHeight - window.innerHeight;

  if (distance <= 0) return 0;

  return Math.min(Math.max(-rect.top / distance, 0), 1);
}

function setProgress(name, value) {
  if (pins[name]) {
    pins[name].style.setProperty(`--${name}-p`, value.toFixed(4));
  }
}

function update() {
  if (motionQuery.matches) {
    ticking = false;
    return;
  }

  const hero = progressFor(pins.hero);
  const wipe = progressFor(pins.wipe);
  const timeline = progressFor(pins.timeline);
  const map = progressFor(pins.map);

  setProgress("hero", hero);
  setProgress("wipe", wipe);
  setProgress("timeline", timeline);
  setProgress("map", map);

  stages.renderTimeline(timeline);
  stages.renderMap(map);

  ticking = false;
}

function requestUpdate() {
  if (ticking) return;
  ticking = true;
  window.requestAnimationFrame(update);
}

function showFinalState() {
  for (const name of Object.keys(pins)) {
    setProgress(name, 1);
  }

  stages.renderTimeline(1);
  stages.renderMap(1);
}

function attachScroll() {
  if (scrollAttached) return;
  window.addEventListener("scroll", requestUpdate, { passive: true });
  scrollAttached = true;
  requestUpdate();
}

function detachScroll() {
  if (!scrollAttached) return;
  window.removeEventListener("scroll", requestUpdate);
  scrollAttached = false;
}

function applyMotionPreference() {
  if (motionQuery.matches) {
    detachScroll();
    showFinalState();
    return;
  }

  attachScroll();
}

window.addEventListener("resize", () => {
  stages.resize();
  if (!motionQuery.matches) requestUpdate();
});

if (typeof motionQuery.addEventListener === "function") {
  motionQuery.addEventListener("change", applyMotionPreference);
}

applyMotionPreference();
