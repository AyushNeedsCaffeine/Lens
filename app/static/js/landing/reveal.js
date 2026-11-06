const WORD_STAGGER = 36;
const ITEM_STAGGER = 45;

function splitWords(element) {
  if (element.dataset.split === "done") return;

  let wordIndex = 0;

  const walk = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      const text = node.textContent;
      if (!text.trim()) return;

      const fragment = document.createDocumentFragment();
      const parts = text.split(/(\s+)/);

      for (const part of parts) {
        if (!part) continue;

        if (/^\s+$/.test(part)) {
          fragment.appendChild(document.createTextNode(part));
          continue;
        }

        const word = document.createElement("span");
        word.className = "word";
        word.style.setProperty("--d", `${wordIndex * WORD_STAGGER}ms`);
        word.textContent = part;
        fragment.appendChild(word);
        wordIndex += 1;
      }

      node.parentNode.replaceChild(fragment, node);
      return;
    }

    if (node.nodeType !== Node.ELEMENT_NODE) return;
    if (node.dataset.noSplit !== undefined) return;

    for (const child of Array.from(node.childNodes)) {
      walk(child);
    }
  };

  for (const child of Array.from(element.childNodes)) {
    walk(child);
  }

  element.dataset.split = "done";
}

function assignItemDelays(elements) {
  const counters = new Map();

  for (const element of elements) {
    const group = element.closest("section, header, footer") || document.body;
    const index = counters.get(group) || 0;
    const delay = Math.min(index * ITEM_STAGGER, 720);

    if (!element.style.getPropertyValue("--d")) {
      element.style.setProperty("--d", `${delay}ms`);
    }

    counters.set(group, index + 1);
  }
}

export function initReveal() {
  const splitTargets = Array.from(document.querySelectorAll("[data-split]"));
  const revealTargets = Array.from(document.querySelectorAll("[data-reveal]"));

  splitTargets.forEach(splitWords);
  assignItemDelays(revealTargets);

  if (!("IntersectionObserver" in window)) {
    splitTargets.forEach((element) => element.classList.add("is-in"));
    revealTargets.forEach((element) => element.classList.add("is-in"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add("is-in");
        observer.unobserve(entry.target);
      }
    },
    { threshold: 0.12 }
  );

  splitTargets.forEach((element) => observer.observe(element));
  revealTargets.forEach((element) => observer.observe(element));
}
