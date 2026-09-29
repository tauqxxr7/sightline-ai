import {performancePage, mountPerformance} from "./pages/performance.js";
import {escape, details, intro} from "./lib/view.js";
import {privacyPage, mountPrivacy} from "./pages/privacy.js";
import {visualPage, mountVisual, disposeVisual} from "./pages/visual.js";

// Original line icons: one consistent stroke grid; no external font or CDN dependency.
const paths = {
  overview: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>',
  visual: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="8" r="1.5"/><path d="m3 17 6-5 4 3 4-5 4 7"/>',
  screen: '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8m-4-4v4"/>',
  camera: '<path d="M3 7h4l2-3h6l2 3h4v13H3z"/><circle cx="12" cy="13" r="4"/>',
  privacy: '<path d="m12 2 8 4v6c0 5-8 10-8 10S4 17 4 12V6z"/><path d="m8 12 3 3 5-6"/>',
  performance: '<path d="M3 3v18h18M7 16v-5m5 5V6m5 10V9"/>',
  models: '<path d="m12 2 10 5-10 5L2 7zm-10 10 10 5 10-5M2 17l10 5 10-5"/>',
  settings: '<circle cx="12" cy="12" r="4"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4M5 5l3 3m8 8 3 3M5 19l3-3m8-8 3-3"/>'
};
const pages = {overview: "Overview", visual: "Visual Assist", screen: "Screen Lens", camera: "Camera Assist", privacy: "Privacy Shield", performance: "Performance Lab", models: "Models", settings: "Settings"};
const icon = name => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name]}</svg>`;
let status = null;
let statusError = "";
let lastResult = null;
let disposePage = () => {};
const main = document.querySelector("main");
document.querySelector(".skip").addEventListener("click", event => {
  event.preventDefault();
  main.focus();
});
const announce = text => { document.querySelector("#announcement").textContent = text; };
const pending = text => `<div class="notice">${text}</div>`;
const stat = (label, value, note) => `<div class="card"><span class="stat-label">${label}</span><strong class="stat-value">${escape(value)}</strong><span class="stat-note">${note}</span></div>`;

for (const [name, label] of Object.entries(pages)) {
  const parent = ["performance","models","settings"].includes(name) ? "#system-nav" : "#workspace-nav";
  document.querySelector(parent).insertAdjacentHTML("beforeend", `<a href="#${name}">${icon(name)}${label}</a>`);
}

function overview() {
  return `<section class="hero"><div><p class="eyebrow">YOUR PRIVATE VISUAL WORKSPACE</p><h1>More clarity.<br><span class="hero-title">Closer to you.</span></h1><p class="muted">Understand visual information on your own device. Designed for local AI on Snapdragon-powered Windows PCs.</p><div class="actions"><a class="button primary" href="#visual">${icon("visual")}Analyze Visual</a><a class="button" href="#screen">Open Screen Lens →</a></div></div><div class="chip-art" aria-hidden="true"><div><small>DESIGNED FOR</small><strong>LOCAL AI</strong><small>SNAPDRAGON / WINDOWS</small></div></div></section>
  <div class="grid stats">${stat("SNAPDRAGON", status?.snapdragon ?? "Unverified", "Hardware observation only")}${stat("NPU EXECUTION", "Unverified", "Execution evidence required")}${stat("ACTIVE PROVIDER", status?.provider?.active ?? "Not initialized", status?.provider?.active ? "Last successful execution" : "No inference run yet")}${stat("PRIVACY", "This device", "Inference over loopback only")}</div>
  <div class="section-head"><h2>Your workspace</h2><span class="muted small">Built around what you see</span></div><div class="grid workflows">
  ${[["visual","Visual Assist","Detect objects in a visual with real model output and provider evidence.","Open workspace"],["screen","Screen Lens","Import or paste a screenshot and analyze it locally.","Import screenshot"],["privacy","Privacy Shield","Select regions, compare effects and export a redacted PNG.","Redact regions"]].map(([id,title,desc,action]) => `<a class="card workflow" href="#${id}">${icon(id)}<h3>${title}</h3><p>${desc}</p><span class="link">${action} →</span></a>`).join("")}</div>
  <div class="grid bottom-grid"><section class="card"><h2>Recent analysis</h2><div class="empty">${icon("visual")}<strong>A clear starting point</strong><p>${lastResult ? `${lastResult.detections.length} objects in the last analysis. ${escape(lastResult.runtime.active)} completed.` : "No analyses yet. Try the bundled public-domain sample."}<br>Images are not saved to a history.</p></div></section><section class="card"><h2>System readiness</h2><ul class="readiness"><li>Application shell <span class="success">Ready</span></li><li>Runtime inspection <span>${status ? "Complete" : "Unavailable"}</span></li><li>Visual model <span>${status?.model?.installed ? "Installed; verified on load" : "Not installed"}</span></li><li>QNN / HTP verification <span class="warning">Pending</span></li></ul></section></div>`;
}

function models() {
  return intro("MODEL REGISTRY", "One model. A reliable foundation.", "Start with a small object detector and validate each step.") + `<section class="card"><span class="badge warning">PINNED CPU ARTIFACT</span><h2 class="page-footer">YOLOX-Nano</h2><p class="muted">${status?.model?.loaded ? "Model loaded and contract checked." : "Model verified by SHA-256 before loading."} Weights are acquired through the setup script.</p>${details([["Purpose","COCO object detection"],["Input","1 × 3 × 416 × 416"],["Precision","FP32 CPU baseline"],["QNN / HTP compatibility","Unverified; requires a separately validated export"],["Provenance","Megvii-BaseDetection/YOLOX"],["License","Apache-2.0; official YOLOX release"],["Version","0.1.1rc0"], ["Checksum",status?.model?.sha256 ?? "See models/manifest.json"]])}</section>`;
}
function settings() {
  return intro("WORKSPACE PREFERENCES", "Explicit by design.", "Execution modes are explicit.") + `<section class="card"><h2>Execution policy</h2><p>Choose CPU, QNN with CPU fallback, or strict QNN on Visual Assist. Strict QNN fails if HTP execution cannot be verified. A separate compatible model and Windows ARM64 QNN runtime are required.</p><h2>Data lifecycle</h2><p class="muted">Images go only to the local process for inference. Images and detection results are not saved automatically. Benchmarks save model, environment and timing metadata locally. JSON and redacted PNG exports are explicit.</p><button id="refresh">Refresh environment</button></section>`;
}

function render(focus = false) {
  disposePage(); disposePage = () => {};
  disposeVisual();
  const route = Object.hasOwn(pages, location.hash.slice(1)) ? location.hash.slice(1) : "overview";
  document.querySelector("#page-name").textContent = pages[route];
  document.title = `${pages[route]} — SightLine AI`;
  document.querySelectorAll("nav a").forEach(a => a.hash === `#${route}` ? a.setAttribute("aria-current","page") : a.removeAttribute("aria-current"));
  const views = {overview, visual: () => visualPage(), screen: () => visualPage(true), performance: () => performancePage(status), privacy: privacyPage, models, settings, camera: () => intro("CAMERA ASSIST", "A considered view, frame by frame.", "Camera support follows the core image workflow.") + pending("Camera sampling is not implemented. This shell does not request camera access.") + '<section class="card"><h2>Planned capture controls</h2><p class="muted">Explicit start and stop, configurable sampling, change detection and graceful camera failure handling.</p><button disabled>Start camera</button></section>'};
  main.innerHTML = (statusError ? `<div class="notice" role="alert">${escape(statusError)} <button id="retry">Retry environment check</button></div>` : "") + views[route]();
  document.querySelector("#retry")?.addEventListener("click", async () => { await refresh(); render(); });
  if (route === "visual" || route === "screen") mountVisual(result => {
    lastResult = result;
    if (status) status.provider = result.runtime;
  }, undefined, refresh);
  if (route === "performance") disposePage = mountPerformance();
  if (route === "privacy") disposePage = mountPrivacy();
  document.querySelector("#export")?.addEventListener("click", () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(status,null,2)], {type:"application/json"}));
    const a = document.createElement("a"); a.href = url; a.download = "sightline-environment.json"; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  document.querySelector("#refresh")?.addEventListener("click", refresh);
  if (focus) main.focus();
}
async function refresh() {
  try {
    const response = await fetch("/api/status", {signal: AbortSignal.timeout(5000)});
    if (!response.ok) throw new Error("Status unavailable");
    const data = await response.json();
    if (data.schema_version !== 1 || !data.provider || !Array.isArray(data.provider.available)) throw new Error("Invalid status");
    status = data;
    statusError = "";
    document.querySelector("#hardware-foot").textContent = `${status.architecture} · NPU unverified`;
  } catch {
    status = null;
    statusError = "Environment information could not be read. Confirm the local host is running.";
    document.querySelector("#hardware-foot").textContent = "Environment unavailable";
  }
  if (!["#visual", "#screen", "#privacy", "#performance"].includes(location.hash)) render();
}
window.addEventListener("hashchange", () => { render(true); });
window.addEventListener("pagehide", () => { disposeVisual(); disposePage(); });
render();
refresh().then(() => { if (location.hash === "#performance") render(); });
