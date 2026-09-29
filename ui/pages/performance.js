import {escape,details,intro,validateBenchmark} from "../lib/view.js";
let lastBenchmark=null;
const ms=value=>Number.isFinite(value)?`${value.toFixed(2)} ms`:"Not measured";

export function performancePage(status) {
  const hardware=status?.hardware, identity=hardware?.processor?.values;
  return intro("OBSERVE. MEASURE. VERIFY.","Snapdragon Performance Lab","Measure the local CPU baseline. NPU comparisons require verified hardware evidence.")+
    `<div class="grid compare"><section class="card"><h2>System & runtime</h2>${details([
      ["Operating system",`${status?.system??"Unavailable"} ${hardware?.os_version??""}`],
      ["Native / process architecture",`${hardware?.native_architecture?.value??"Unknown"} / ${hardware?.process_architecture??"Unknown"}`],
      ["Processor",identity?.ProcessorNameString??status?.processor??"Unavailable"],
      ["Snapdragon",status?.snapdragon??"Unverified"],["ONNX Runtime",status?.runtime_version??"Unavailable"],
      ["Available providers",status?.provider?.available?.join(", ")||"None reported"],
      ["QNN EP",status?.qnn_ep_available?"Available; execution requires verification":"Unavailable"],
      ["NPU","QNN/NPU not verified on this device"]])}</section>
    <section class="card"><h2>Run a measured baseline</h2><p class="muted small">YOLOX-Nano FP32 · CPU only · bundled NASA image. A fresh session is followed by warmups and measured runs. No QNN comparison is generated.</p>
    <div class="form-grid"><label>Measured samples<input id="benchmark-samples" type="number" min="3" max="30" step="1" value="10"></label><label>Warmup runs<input id="benchmark-warmups" type="number" min="1" max="5" step="1" value="2"></label></div>
    <div class="actions"><button id="run-benchmark" class="primary" ${status?"":"disabled"}>Run CPU benchmark</button><button id="export" ${status?"":"disabled"}>Export environment JSON</button></div>
    <p id="benchmark-progress" class="page-footer small" role="status" aria-live="polite">No run started in this view.</p><p id="benchmark-error" class="error" role="alert"></p>
    <p class="muted small">Runs save metadata and timings to benchmarks/results/. No input image or detections are saved. Leaving the page does not cancel native inference.</p></section></div>
    <section class="card page-footer" id="benchmark-result" aria-label="Benchmark results"><h2>Measured results</h2><p class="muted">Run the benchmark to collect evidence. Memory and video FPS are not measured.</p></section>`;
}

export function mountPerformance() {
  const controller=new AbortController();
  const panel=document.querySelector("#benchmark-result"), run=document.querySelector("#run-benchmark");
  const progress=document.querySelector("#benchmark-progress"), error=document.querySelector("#benchmark-error");
  function show(data) {
    const r=data.report, stats=r.summary_ms.inference;
    panel.innerHTML=`<div class="section-head"><h2>Measured CPU results</h2><span class="badge">${escape(r.configuration.samples)} samples</span></div>
      <p class="small muted">${escape(r.observed_at)} · ${escape(r.configuration.warmups)} warmups excluded · Fresh session, not process/OS cold</p>
      <div class="grid metric-grid">${[["Cold initialization",r.cold.timings_ms.initialization],["Warm inference median",stats.median],["Warm inference p95",stats.p95],["Warm mean",stats.mean],["Warm standard deviation",stats.stdev],["Pipeline median",r.summary_ms.total_pipeline.median]].map(([label,value])=>`<div class="metric"><span>${escape(label)}</span><strong>${ms(value)}</strong></div>`).join("")}</div>
      ${details([["Model / version / precision",`${r.model.name} / ${r.model.version} / ${r.model.precision}`],
        ["Requested / active",`${r.runtime.requested} / ${r.runtime.active}`],["Available",r.runtime.available.join(", ")],
        ["Backend / fallback",`${r.runtime.backend} / ${r.runtime.fallback}`],["NPU",r.runtime.npu],
        ["Memory",r.memory_note],["FPS",r.fps_note],["Artifacts",`benchmarks/results/${r.id}.{json,csv}`]])}
      <h3 class="page-footer">Pipeline stages · measured runs only</h3><div class="table-scroll"><table><caption>Timing statistics in milliseconds; nearest-rank p95</caption><thead><tr><th scope="col">Stage</th><th scope="col">Mean</th><th scope="col">Median</th><th scope="col">p95</th></tr></thead><tbody>${Object.entries(r.summary_ms).map(([stage,s])=>`<tr><th scope="row">${escape(stage.replaceAll("_"," "))}</th><td>${ms(s.mean)}</td><td>${ms(s.median)}</td><td>${ms(s.p95)}</td></tr>`).join("")}</tbody></table></div>
      <div class="actions"><button class="primary" id="download-benchmark-json">Export benchmark JSON</button><button id="download-benchmark-csv">Export samples CSV</button></div>
      <p class="small muted page-footer">${r.limitations.map(escape).join(" · ")}</p>`;
    for (const kind of ["json","csv"]) {
      document.querySelector(`#download-benchmark-${kind}`).addEventListener("click", async () => {
        try {
          const filename=data.artifacts[kind];
          const response=await fetch(`/api/benchmarks/${filename}`, {signal:controller.signal});
          if(!response.ok)throw new Error("Saved benchmark is unavailable. Run a new benchmark.");
          const blob=await response.blob();if(controller.signal.aborted)return;
          const url=URL.createObjectURL(blob), link=document.createElement("a");
          link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
        } catch(problem) { if(!controller.signal.aborted)error.textContent=problem.message; }
      },{signal:controller.signal});
    }
  }
  if(lastBenchmark)show(lastBenchmark);
  run.addEventListener("click",async()=>{
    const samples=document.querySelector("#benchmark-samples").valueAsNumber;
    const warmups=document.querySelector("#benchmark-warmups").valueAsNumber;
    error.textContent="";
    if(!Number.isInteger(samples)||samples<3||samples>30||!Number.isInteger(warmups)||warmups<1||warmups>5){error.textContent="Use 3–30 measured samples and 1–5 warmups.";return;}
    run.disabled=true;panel.setAttribute("aria-busy","true");
    progress.textContent="Running fresh-session initialization, warmups and measured CPU inference…";
    // Previous results must not masquerade as the new attempt.
    lastBenchmark=null;panel.innerHTML='<h2>Collecting measurements</h2><p class="muted">Results appear only after all runs and artifact saves succeed.</p>';
    const request = new AbortController();
    const abort = () => request.abort();
    controller.signal.addEventListener("abort", abort, {once:true});
    const timeout=setTimeout(()=>request.abort(),150000);
    try {
      const response=await fetch("/api/benchmark",{method:"POST",headers:{"Content-Type":"application/json","X-SightLine-Request":"1"},body:JSON.stringify({samples,warmups}),signal:request.signal});
      const data=await response.json();if(!response.ok)throw new Error(data.error?.message??"Benchmark failed.");
      if(controller.signal.aborted)return;
      lastBenchmark=validateBenchmark(data);show(lastBenchmark);progress.textContent="Benchmark complete. JSON and CSV saved locally.";
    }catch(problem){
      if(panel.isConnected && !controller.signal.aborted){error.textContent=problem.name==="AbortError"?"The response timed out. Native inference may still finish; artifacts are saved on completion.":problem.message;progress.textContent="No completed result for this attempt.";panel.innerHTML='<h2>No benchmark result</h2><p class="muted">Resolve the error, then retry.</p>';}
    }finally{clearTimeout(timeout);controller.signal.removeEventListener("abort",abort);if(panel.isConnected && !controller.signal.aborted){run.disabled=false;panel.removeAttribute("aria-busy");}}
  },{signal:controller.signal});
  return ()=>controller.abort();
}
