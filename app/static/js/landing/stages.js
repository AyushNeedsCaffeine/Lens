const MINUTE_MARKS = [0, 4, 11, 26, 41, 58];
const STATUS_LABELS = [
  "SOURCE READY",
  "EXTRACTING AUDIO",
  "TRANSCRIBING",
  "STRUCTURING",
  "INDEXING",
];
const NODE_COUNT = 26;
const ROUTE_INDICES = [4, 9, 14, 19, 24, 18];
const EDGE_DISTANCE = 0.18;

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

function buildNodes() {
  const nodes = [];

  for (let index = 0; index < NODE_COUNT; index += 1) {
    const angle = index * 2.399;
    const radius = Math.sqrt(index / NODE_COUNT) * 0.42;
    nodes.push({
      x: 0.5 + Math.cos(angle) * radius,
      y: 0.5 + Math.sin(angle) * radius,
    });
  }

  return nodes;
}

function buildEdges(nodes) {
  const edges = [];

  for (let first = 0; first < nodes.length; first += 1) {
    for (let second = first + 1; second < nodes.length; second += 1) {
      const dx = nodes[first].x - nodes[second].x;
      const dy = nodes[first].y - nodes[second].y;
      if (Math.hypot(dx, dy) < EDGE_DISTANCE) {
        edges.push([first, second]);
      }
    }
  }

  return edges;
}

function interpolateMinutes(progress) {
  const scaled = clamp(progress, 0, 1) * (MINUTE_MARKS.length - 1);
  const index = Math.min(Math.floor(scaled), MINUTE_MARKS.length - 2);
  const fraction = scaled - index;
  return MINUTE_MARKS[index] + (MINUTE_MARKS[index + 1] - MINUTE_MARKS[index]) * fraction;
}

function formatClock(minutes) {
  const totalSeconds = Math.round(minutes * 60);
  const mm = Math.floor(totalSeconds / 60);
  const ss = totalSeconds % 60;
  return `${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
}

export function initStages() {
  const timelineStage = document.querySelector('[data-pin="timeline"]');
  const rows = Array.from(document.querySelectorAll("[data-tl-row]"));
  const clock = document.querySelector("#tl-clock");
  const chunks = document.querySelector("#tl-chunks");
  const status = document.querySelector("#tl-status");

  const mapStage = document.querySelector('[data-pin="map"]');
  const canvas = document.querySelector("#route-map");
  const canvasWrap = canvas ? canvas.parentElement : null;
  const routeHead = document.querySelector("#route-head");
  const captionStart = document.querySelector("#map-caption-start");
  const captionEnd = document.querySelector("#map-caption-end");

  const nodes = buildNodes();
  const edges = buildEdges(nodes);
  const route = ROUTE_INDICES.map((index) => nodes[index]);
  const routeSegments = [];
  let routeLength = 0;

  for (let index = 0; index < route.length - 1; index += 1) {
    const start = route[index];
    const end = route[index + 1];
    const length = Math.hypot(end.x - start.x, end.y - start.y);
    routeSegments.push({ start, end, length });
    routeLength += length;
  }

  const context = canvas ? canvas.getContext("2d") : null;
  let viewWidth = 0;
  let viewHeight = 0;
  let lastTimelineProgress = 0;
  let lastMapProgress = 0;

  function renderTimeline(progress) {
    lastTimelineProgress = progress;
    if (!timelineStage) return;

    const minutes = interpolateMinutes(progress);
    const litCount = Math.min(5, Math.max(1, Math.floor(progress * 5) + 1));
    const chunkCount = Math.min(6, Math.ceil(minutes / 10));

    if (clock) clock.textContent = formatClock(minutes);
    if (chunks) chunks.textContent = String(chunkCount);
    if (status) {
      status.textContent = progress >= 0.999 ? "READY" : STATUS_LABELS[litCount - 1];
    }

    rows.forEach((row, index) => {
      row.style.setProperty("--on", index < litCount ? "1" : "0");
    });
  }

  function resizeCanvas() {
    if (!canvas || !canvasWrap || !context) return;

    const rect = canvasWrap.getBoundingClientRect();
    const dpr = clamp(window.devicePixelRatio || 1, 1, 2);

    viewWidth = rect.width;
    viewHeight = rect.height;

    canvas.width = Math.max(1, Math.round(viewWidth * dpr));
    canvas.height = Math.max(1, Math.round(viewHeight * dpr));
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function placeRouteHead(progress) {
    if (!routeHead || !viewWidth || !viewHeight) return;

    const targetLength = routeLength * clamp(progress, 0, 1);
    let travelled = 0;
    let head = route[0];

    for (const segment of routeSegments) {
      if (travelled + segment.length >= targetLength) {
        const fraction = segment.length === 0 ? 0 : (targetLength - travelled) / segment.length;
        head = {
          x: segment.start.x + (segment.end.x - segment.start.x) * fraction,
          y: segment.start.y + (segment.end.y - segment.start.y) * fraction,
        };
        break;
      }

      travelled += segment.length;
      head = segment.end;
    }

    routeHead.style.left = `${head.x * viewWidth}px`;
    routeHead.style.top = `${head.y * viewHeight}px`;
  }

  function placeCaptions() {
    if (!viewWidth || !viewHeight) return;

    const first = route[0];
    const last = route[route.length - 1];

    if (captionStart) {
      captionStart.style.left = `${first.x * viewWidth}px`;
      captionStart.style.top = `${first.y * viewHeight}px`;
    }

    if (captionEnd) {
      captionEnd.style.left = `${last.x * viewWidth}px`;
      captionEnd.style.top = `${last.y * viewHeight}px`;
    }
  }

  function drawMap(progress) {
    lastMapProgress = progress;
    if (!canvas || !context || !viewWidth || !viewHeight) return;

    context.clearRect(0, 0, viewWidth, viewHeight);

    context.strokeStyle = "rgba(14, 26, 58, .16)";
    context.lineWidth = 1;
    context.beginPath();
    for (const [first, second] of edges) {
      context.moveTo(nodes[first].x * viewWidth, nodes[first].y * viewHeight);
      context.lineTo(nodes[second].x * viewWidth, nodes[second].y * viewHeight);
    }
    context.stroke();

    context.fillStyle = "rgba(14, 26, 58, .55)";
    for (const node of nodes) {
      context.beginPath();
      context.arc(node.x * viewWidth, node.y * viewHeight, 1.7, 0, Math.PI * 2);
      context.fill();
    }

    const targetLength = routeLength * clamp(progress, 0, 1);
    let travelled = 0;

    context.strokeStyle = "#F26A1B";
    context.lineWidth = 2.6;
    context.lineCap = "round";
    context.lineJoin = "round";
    context.beginPath();
    context.moveTo(route[0].x * viewWidth, route[0].y * viewHeight);

    for (const segment of routeSegments) {
      if (travelled + segment.length <= targetLength) {
        context.lineTo(segment.end.x * viewWidth, segment.end.y * viewHeight);
        travelled += segment.length;
        continue;
      }

      const fraction = segment.length === 0 ? 0 : (targetLength - travelled) / segment.length;
      context.lineTo(
        (segment.start.x + (segment.end.x - segment.start.x) * fraction) * viewWidth,
        (segment.start.y + (segment.end.y - segment.start.y) * fraction) * viewHeight
      );
      break;
    }

    context.stroke();
    placeRouteHead(progress);
    placeCaptions();
  }

  function renderMap(progress) {
    drawMap(progress);
  }

  function resize() {
    resizeCanvas();
    renderTimeline(lastTimelineProgress);
    drawMap(lastMapProgress);
  }

  resizeCanvas();
  renderTimeline(0);
  drawMap(0);

  return {
    renderTimeline,
    renderMap,
    resize,
    hasMap: Boolean(canvas && mapStage),
  };
}
