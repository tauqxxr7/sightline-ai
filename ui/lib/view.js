export const escape = value => String(value ?? "Not measured").replace(/[&<>"']/g, c => ({"&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"}[c]));
export const details = items => `<dl class="details">${items.map(([key,value]) => `<div><dt>${escape(key)}</dt><dd>${escape(value)}</dd></div>`).join("")}</dl>`;
export const intro = (eyebrow,title,description) => `<div class="page-intro"><p class="eyebrow">${escape(eyebrow)}</p><h1>${escape(title)}</h1><p class="muted">${escape(description)}</p></div>`;

export function validateBenchmark(data) {
  const r=data?.report;
  if(r?.schema_version!==1 || r.kind!=="measured_cpu_benchmark" ||
     r.runtime?.active!=="CPUExecutionProvider" || !/^[a-f0-9]{32}$/.test(r.id) ||
     !Array.isArray(r.runs) || r.configuration?.samples<3 || r.configuration.samples>30 ||
     r.runs.filter(row=>row.phase==="measured").length!==r.configuration.samples ||
     data.artifacts?.json!==`${r.id}.json` || data.artifacts?.csv!==`${r.id}.csv`) throw new Error("Invalid benchmark response.");
  for(const stage of ["preprocessing","inference","postprocessing","total_pipeline"]) {
    const summary=r.summary_ms?.[stage];
    if(summary?.count!==r.configuration.samples || ![summary.mean,summary.median,summary.p95,summary.stdev].every(v=>Number.isFinite(v)&&v>=0))
      throw new Error("Invalid benchmark measurements.");
  }
  return data;
}
