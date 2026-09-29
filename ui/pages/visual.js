import {readClipboardImage, clipboardFile} from "../lib/clipboard.js";
import {validateHeader, validateDimensions} from "../lib/files.js";
import {validateResult, drawDetections, objectSummary} from "../lib/results.js";

let bitmap = null;
let selectedFile = null;
let generation = 0;
let request = null;
let stopClipboard = () => {};

export function disposeVisual() {
  stopClipboard(); stopClipboard = () => {};
  generation++;
  request?.abort();
  request = null;
  bitmap?.close();
  bitmap = null;
  selectedFile = null;
}

export function visualPage(screen = false) {
  return `<div class="page-intro"><p class="eyebrow">${screen ? "SCREEN LENS" : "VISUAL ASSIST"}</p>
    <h1>${screen ? "Bring your screen into focus." : "See what is in the picture."}</h1><p class="muted">Local object detection with explicit provider evidence.</p></div>
    <div class="notice">Images are sent only to SightLine's local process at 127.0.0.1. No external inference service is used. QNN/NPU not verified on this device.</div>
    <div class="grid split"><section><div class="drop" id="drop">
      <h2>${screen ? "Import a screenshot" : "Choose a visual"}</h2>
      <p class="muted small">PNG or JPEG · up to 10 MB · 24 MP · 16000 pixels per side</p>
      <label for="file" class="sr-only">Choose a PNG or JPEG image</label>
      <input class="file-input" id="file" type="file" accept="image/png,image/jpeg">
      ${screen ? '<button id="read-clipboard">Import clipboard image</button><p class="small muted">Or press Ctrl+V to paste an image. Clipboard is read only on your action. Screen capture and OCR are unavailable.</p>' : ""}
      <button id="sample">Use public-domain sample</button>
      <canvas id="analysis-canvas" hidden role="img" aria-label="Selected image; detected objects are listed alongside it"></canvas>
      <label class="settings-row"><input id="show-overlay" type="checkbox" checked> Show detection overlays</label>
      <p id="file-meta" class="mono muted"></p>
      <label for="provider-mode">Execution policy</label>
      <select id="provider-mode"><option value="cpu">CPU baseline</option><option value="qnn">Prefer QNN; allow CPU fallback</option><option value="qnn-strict">Strict QNN; fail without verification</option></select>
      <div class="actions"><button id="analyze" class="primary" disabled>Analyze locally</button>
      <button id="clear" hidden>Clear image</button></div>
    </div><p id="file-error" class="error small" role="alert"></p>
    <p id="analysis-progress" class="muted small" role="status" aria-live="polite"></p>
    <p class="small muted">Sample: NASA astronaut photograph, public domain via scikit-image. Detection is not identity recognition.</p>
    </section><section class="card" id="result-panel" aria-label="Analysis results">
      <span class="badge" id="result-state">READY WHEN YOU ARE</span>
      <h2 class="page-footer">Objects & confidence</h2><p class="muted small" id="result-summary">Choose an image, then run local analysis.</p>
      <h3>Visual inventory</h3><p id="visual-inventory" class="muted small">No analysis yet.</p>
      <ol id="objects" class="object-list"></ol>
      <h3 class="page-footer">Text & privacy findings</h3><p class="muted small">OCR and automatic sensitive-region detection are unavailable. Object boxes are not privacy findings. Use Privacy Shield to select regions manually.</p>
      <h3 class="page-footer">Inference details</h3><dl id="inference-details" class="details"></dl>
      <button id="export-result" class="page-footer" hidden>Export result JSON</button>
      <p class="small muted page-footer">Scores are model confidence, not calibrated probabilities. OCR and scene captioning are unavailable. Manual redaction is available in Privacy Shield.</p>
    </section></div>`;
}

export function mountVisual(onResult, getMode = () => document.querySelector("#provider-mode").value, onSettled = () => {}) {
  const canvas = document.querySelector("#analysis-canvas");
  const context = canvas.getContext("2d");
  const error = document.querySelector("#file-error");
  const progress = document.querySelector("#analysis-progress");
  const analyze = document.querySelector("#analyze");
  const clear = document.querySelector("#clear");
  let latestResult = null;

  function resetResults() {
    latestResult = null;
    document.querySelector("#visual-inventory").textContent = "No analysis yet.";
    canvas.setAttribute("aria-label", "Selected image; no completed analysis");
    document.querySelector("#objects").replaceChildren();
    document.querySelector("#inference-details").replaceChildren();
    document.querySelector("#export-result").hidden = true;
    document.querySelector("#result-state").textContent = "NOT ANALYZED";
    document.querySelector("#result-summary").textContent = "No analysis for this image yet.";
    document.querySelector("#result-panel").removeAttribute("aria-busy");
  }

  function paintImage() {
    context.fillStyle = "white";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.drawImage(bitmap, 0, 0);
  }

  async function choose(file) {
    generation++; request?.abort(); request = null; bitmap?.close(); bitmap = null; selectedFile = null;
    const id = generation;
    canvas.hidden = true;
    canvas.width = canvas.height = 1;
    error.textContent = progress.textContent = "";
    document.querySelector("#file-meta").textContent = "";
    analyze.disabled = true;
    analyze.textContent = "Analyze locally";
    clear.hidden = true;
    resetResults();
    if (!file) return;
    let decoded;
    try {
      validateHeader(new Uint8Array(await file.slice(0, 16).arrayBuffer()), file.size, file.type, file.name);
      decoded = await createImageBitmap(file);
      validateDimensions(decoded.width, decoded.height);
      if (id !== generation) return;
      bitmap = decoded;
      decoded = null;
      selectedFile = file;
      canvas.width = bitmap.width;
      canvas.height = bitmap.height;
      paintImage();
      canvas.hidden = false;
      document.querySelector("#file-meta").textContent = `${bitmap.width} × ${bitmap.height} pixels · Ready`;
      analyze.disabled = false;
      clear.hidden = false;
      progress.textContent = "Image ready for local analysis.";
    } catch (problem) {
      if (id === generation) error.textContent = problem instanceof Error ? problem.message : "Image could not be loaded.";
    } finally { decoded?.close(); }
  }

  if (document.querySelector("#read-clipboard")) {
    const lifetime = new AbortController();
    stopClipboard = () => lifetime.abort();
    document.querySelector("#read-clipboard").addEventListener("click", async () => {
      const id = generation;
      try {
        const file = await readClipboardImage(navigator.clipboard);
        if (id === generation && !lifetime.signal.aborted) await choose(file);
      } catch (problem) { if (id === generation && !lifetime.signal.aborted) error.textContent = problem.message; }
    }, {signal:lifetime.signal});
    document.addEventListener("paste", event => {
      const image = [...(event.clipboardData?.files ?? [])].find(file => file.type.startsWith("image/"));
      if (!image) { error.textContent = "No image found in the paste. Copy an image or import a screenshot file."; return; }
      event.preventDefault();
      try { choose(clipboardFile(image)); } catch (problem) { error.textContent = problem.message; }
    }, {signal:lifetime.signal});
  }
  document.querySelector("#show-overlay").addEventListener("change", event => {
    if (!bitmap) return;
    paintImage();
    if (latestResult && event.target.checked) drawDetections(context, latestResult.detections);
  });
  document.querySelector("#file").addEventListener("change", event => choose(event.target.files[0]));
  const drop = document.querySelector("#drop");
  drop.addEventListener("dragover", event => { event.preventDefault(); drop.classList.add("dragging"); });
  drop.addEventListener("dragleave", () => drop.classList.remove("dragging"));
  drop.addEventListener("drop", event => {
    event.preventDefault(); drop.classList.remove("dragging"); choose(event.dataTransfer.files[0]);
  });
  clear.addEventListener("click", () => {
    choose(null); document.querySelector("#file").value = ""; document.querySelector("#file").focus();
  });
  document.querySelector("#sample").addEventListener("click", async () => {
    const id = generation;
    try {
      const response = await fetch("/samples/astronaut.png", {signal: AbortSignal.timeout(10000)});
      if (!response.ok) throw new Error("Sample could not be loaded.");
      const blob = await response.blob();
      if (id === generation) await choose(new File([blob], "astronaut.png", {type:"image/png"}));
    } catch { if (id === generation) error.textContent = "Sample could not be loaded. Choose a local image."; }
  });

  analyze.addEventListener("click", async () => {
    if (!selectedFile || !bitmap) return;
    const id = generation;
    resetResults(); paintImage();
    error.textContent = "";
    progress.textContent = "Running local inference… Provider verification may initialize a model.";
    analyze.disabled = true;
    analyze.textContent = "Analyzing…";
    document.querySelector("#result-panel").setAttribute("aria-busy", "true");
    request = new AbortController();
    const controller = request;
    const timeout = setTimeout(() => controller.abort(), 60000);
    try {
      const response = await fetch("/api/analyze", {
        method:"POST", headers:{"Content-Type":selectedFile.type, "X-SightLine-Request":"1", "X-SightLine-Provider":getMode()},
        body:selectedFile, signal:request.signal,
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error?.message ?? "Local analysis failed.");
      if (id !== generation) return;
      latestResult = validateResult(body, canvas.width, canvas.height);
      if (document.querySelector("#show-overlay").checked) drawDetections(context, latestResult.detections);
      document.querySelector("#visual-inventory").textContent = objectSummary(latestResult.detections);
      const count = latestResult.detections.length;
      document.querySelector("#result-state").textContent = `${latestResult.runtime.backend} ANALYSIS COMPLETE`;
      const summary = count ? `${count} object${count === 1 ? "" : "s"} above the 30% confidence threshold.` : "No objects above the 30% confidence threshold. This does not mean the image contains no objects.";
      document.querySelector("#result-summary").textContent = summary;
      canvas.setAttribute("aria-label", `Analyzed image. ${summary} See the object list for details.`);
      for (const detection of latestResult.detections) {
        const row = document.createElement("li");
        const title = document.createElement("strong");
        title.textContent = `${detection.label} · ${(detection.confidence * 100).toFixed(1)}%`;
        const bounds = document.createElement("span");
        bounds.className = "mono muted small";
        bounds.textContent = `Box: ${detection.box.map(value => value.toFixed(1)).join(", ")} px`;
        row.append(title, bounds); document.querySelector("#objects").append(row);
      }
      const timings = latestResult.timings_ms;
      const items = [["Model", `${latestResult.model.name} · ${latestResult.model.version} · ${latestResult.model.precision}`],
        ["Requested / active provider", `${latestResult.runtime.requested} / ${latestResult.runtime.active}`],
        ["Available providers", latestResult.runtime.available.join(", ")],
        ["Backend / fallback", `${latestResult.runtime.backend} / ${latestResult.runtime.fallback}`],
        ["Fallback reason", latestResult.runtime.fallback_message ?? "None"],
        ["Initialization (this request)", timings.initialization === null ? "Session reused" : `${timings.initialization.toFixed(2)} ms`],
        ["Preprocessing", `${timings.preprocessing.toFixed(2)} ms`],
        ["Inference", `${timings.inference.toFixed(2)} ms`],
        ["Postprocessing", `${timings.postprocessing.toFixed(2)} ms`],
        ["Total local pipeline", `${timings.total_pipeline.toFixed(2)} ms`],
        ["Run", `${latestResult.run_kind} · single observation, not a benchmark`],
        ["Network", latestResult.network], ["NPU", latestResult.runtime.npu]];
      for (const [label, value] of items) {
        const row = document.createElement("div"), term = document.createElement("dt"), description = document.createElement("dd");
        term.textContent = label; description.textContent = value; row.append(term, description);
        document.querySelector("#inference-details").append(row);
      }
      document.querySelector("#export-result").hidden = false;
      progress.textContent = `Analysis complete. ${summary}${latestResult.runtime.fallback === "cpu" ? " QNN unavailable or unverified; CPU fallback used." : ""}`;
      onResult(latestResult);
    } catch (problem) {
      if (id !== generation) return;
      resetResults();
      error.textContent = problem.name === "AbortError" ? "Analysis timed out. The local process may still be finishing; retry shortly." : problem.message;
      progress.textContent = "Analysis did not complete.";
    } finally {
      clearTimeout(timeout);
      if (id === generation) {
        request = null; analyze.disabled = !selectedFile; analyze.textContent = "Analyze locally";
        document.querySelector("#result-panel").removeAttribute("aria-busy");
        onSettled();
      }
    }
  });
  document.querySelector("#provider-mode").addEventListener("change", () => {
    generation++;
    request?.abort(); request = null;
    resetResults();
    if (bitmap) paintImage();
    analyze.disabled = !selectedFile; analyze.textContent = "Analyze locally";
    error.textContent = "";
    progress.textContent = "Policy changed. Run analysis to verify actual execution.";
  });
  document.querySelector("#export-result").addEventListener("click", () => {
    if (!latestResult) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(latestResult,null,2)], {type:"application/json"}));
    const link = document.createElement("a"); link.href = url; link.download = "sightline-analysis.json"; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}
