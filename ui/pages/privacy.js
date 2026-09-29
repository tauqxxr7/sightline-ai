import {validateHeader, validateDimensions} from "../lib/files.js";
import {regionBounds, dragBounds, transformPixels} from "../lib/privacy.js";

export function privacyPage() {
  return `<div class="page-intro"><p class="eyebrow">PRIVACY SHIELD</p><h1>Choose what stays private.</h1><p class="muted">Select regions and review the exported image before sharing.</p></div>
  <div class="notice">Manual regions only. Automatic face, text, email, phone and QR detection are unavailable. Blur and pixelation can leave information recognizable; use solid fill to replace selected pixels.</div>
  <section class="card"><label for="privacy-file">Choose a PNG or JPEG</label><input class="file-input" id="privacy-file" type="file" accept="image/png,image/jpeg"><button id="privacy-sample">Use public-domain sample</button><p class="small muted">Up to 10 MB and 6 MP. All transformations happen in this browser. No network required for this operation after the page loads.</p></section>
  <p id="privacy-error" class="error" role="alert"></p><p id="privacy-status" role="status" aria-live="polite">Choose an image to begin.</p>
  <div class="grid compare"><section class="card"><h2>Original · select a region</h2><p class="small muted">Drag on the image, or enter pixel coordinates below.</p><canvas id="privacy-original" class="image-canvas selection-canvas" hidden role="img" aria-label="Original image; use coordinate fields to select regions with the keyboard"></canvas></section>
  <section class="card"><h2>Redacted preview</h2><p class="small muted">The exported PNG contains this preview, without selection outlines.</p><canvas id="privacy-output" class="image-canvas" hidden role="img" aria-label="Redacted preview"></canvas></section></div>
  <section class="card page-footer"><h2>Region controls</h2><fieldset id="region-controls" disabled><legend class="sr-only">Manual redaction</legend><div class="form-grid">
  ${[["x","Left (px)",0],["y","Top (px)",0],["width","Width (px)",100],["height","Height (px)",100]].map(([key,label,value])=>`<label>${label}<input id="region-${key}" type="number" min="${key==='x'||key==='y'?0:1}" step="1" value="${value}"></label>`).join("")}
  <label>Effect<select id="region-mode"><option value="solid">Solid</option><option value="pixelate">Pixelate</option><option value="blur">Blur</option></select></label></div>
  <div class="actions"><button id="add-region" class="primary">Add region</button><button id="undo-region">Undo last region</button><button id="clear-regions">Clear all regions</button><button id="clear-private-image">Clear image</button></div></fieldset>
  <h3 class="page-footer">Selected regions</h3><ol id="region-list" class="object-list"></ol><p id="region-count" class="small muted">0 manual regions. Automatic detection not run.</p>
  <button id="export-private" class="primary" disabled>Export redacted PNG</button><p class="small muted page-footer">Processing: this device · No server upload · PNG export omits original file metadata. Review the entire image; unselected content remains visible.</p></section>`;
}

export function mountPrivacy() {
  const lifetime=new AbortController();
  let bitmap=null, regions=[], generation=0, start=null;
  const $=id=>document.querySelector(`#${id}`);
  const original=$("privacy-original"), output=$("privacy-output");
  const source=original.getContext("2d"), target=output.getContext("2d",{willReadFrequently:true});
  const error=$("privacy-error"), status=$("privacy-status");
  const on=(id,event,fn)=>$(id).addEventListener(event,fn,{signal:lifetime.signal});
  function base(ctx) { ctx.fillStyle="white";ctx.fillRect(0,0,original.width,original.height);ctx.drawImage(bitmap,0,0); }
  function render() {
    $("export-private").disabled=true;
    if (bitmap) {
      base(source);base(target);
      for (const [index,r] of regions.entries()) {
        const pixels=target.getImageData(r.x,r.y,r.width,r.height);
        pixels.data.set(transformPixels(pixels.data,r.width,r.height,r.mode));
        target.putImageData(pixels,r.x,r.y);
        source.strokeStyle=getComputedStyle(original).getPropertyValue("--accent");
        source.lineWidth=Math.max(2,original.width/300);source.strokeRect(r.x,r.y,r.width,r.height);
        source.fillStyle="black";source.font="16px sans-serif";source.fillText(String(index+1),r.x+4,r.y+18);
      }
    }
    $("region-list").replaceChildren();
    regions.forEach((r,index)=>{
      const row=document.createElement("li"), text=document.createElement("span"), button=document.createElement("button");
      text.textContent=`${r.mode} · left ${r.x}, top ${r.y}, ${r.width} × ${r.height} px`;
      button.textContent=`Remove region ${index+1}`;
      button.addEventListener("click",()=>{regions.splice(index,1);generation++;render();$("add-region").focus();});
      row.append(text,button);$("region-list").append(row);
    });
    $("region-count").textContent=`${regions.length} manual region${regions.length===1?"":"s"}. Automatic detection not run.`;
    output.setAttribute("aria-label",`Redacted preview with ${regions.length} manual regions; see selected regions list.`);
    $("export-private").disabled=!bitmap || !regions.length;
    $("undo-region").disabled=$("clear-regions").disabled=!regions.length;
  }
  function clear() {
    generation++;bitmap?.close();bitmap=null;regions=[];start=null;
    for(const canvas of [original,output]) {canvas.hidden=true;canvas.width=canvas.height=1;}
    $("region-controls").disabled=true;$("privacy-file").value="";error.textContent="";
    status.textContent="Choose an image to begin.";render();
  }
  async function choose(file) {
    clear();if(!file)return;const id=generation;
    let decoded;
    try {
      validateHeader(new Uint8Array(await file.slice(0,16).arrayBuffer()),file.size,file.type,file.name);
      decoded=await createImageBitmap(file);validateDimensions(decoded.width,decoded.height);
      if(decoded.width*decoded.height>6000000)throw new Error("Privacy Shield supports images up to 6 megapixels.");
      if(id!==generation || lifetime.signal.aborted)return;
      bitmap=decoded;decoded=null;
      for(const canvas of [original,output]){canvas.width=bitmap.width;canvas.height=bitmap.height;canvas.hidden=false;}
      $("region-controls").disabled=false;
      $("region-width").value=Math.min(100,bitmap.width);$("region-height").value=Math.min(100,bitmap.height);
      $("region-x").value=$("region-y").value=0;
      status.textContent=`${bitmap.width} × ${bitmap.height} pixels. Select regions to redact.`;render();
    }catch(problem){if(id===generation)error.textContent=problem.message;}
    finally{decoded?.close();}
  }
  function add(bounds) {
    if(regions.length>=50)throw new Error("Up to 50 regions are supported.");
    regions.push({...bounds,mode:$("region-mode").value});generation++;render();error.textContent="";
    status.textContent=`Preview updated with ${regions.length} manual regions.`;
  }
  on("privacy-file","change",event=>choose(event.target.files[0]));
  on("privacy-sample","click",async()=>{
    const id=generation;
    try{const response=await fetch("/samples/astronaut.png",{signal:lifetime.signal});if(!response.ok)throw new Error();
      const blob=await response.blob();if(id===generation)await choose(new File([blob],"sample.png",{type:"image/png"}));
    }catch{if(!lifetime.signal.aborted)error.textContent="Sample unavailable. Choose a local image.";}
  });
  on("add-region","click",()=>{try{add(regionBounds(...["x","y","width","height"].map(k=>$("region-"+k).valueAsNumber),original.width,original.height));}catch(problem){error.textContent=problem.message;}});
  const point=event=>{const rect=original.getBoundingClientRect();return {x:(event.clientX-rect.left)*original.width/rect.width,y:(event.clientY-rect.top)*original.height/rect.height};};
  on("privacy-original","pointerdown",event=>{if(!bitmap||event.button!==0)return;start=point(event);original.setPointerCapture(event.pointerId);});
  on("privacy-original","pointerup",event=>{if(!start)return;try{add(dragBounds(start,point(event),original.width,original.height));}catch(problem){error.textContent=problem.message;}finally{start=null;}});
  on("privacy-original","pointercancel",()=>{start=null;});
  on("undo-region","click",()=>{regions.pop();generation++;render();});
  on("clear-regions","click",()=>{regions=[];generation++;render();});
  on("clear-private-image","click",clear);
  on("export-private","click",()=>{
    if(!regions.length)return;const id=generation;
    output.toBlob(blob=>{
      if(id!==generation||lifetime.signal.aborted)return;
      if(!blob){error.textContent="PNG export failed. Please try again.";return;}
      const url=URL.createObjectURL(blob), link=document.createElement("a");
      link.href=url;link.download="sightline-redacted.png";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
      status.textContent="Redacted PNG exported. Review it before sharing.";
    },"image/png");
  });
  return ()=>{lifetime.abort();clear();};
}
