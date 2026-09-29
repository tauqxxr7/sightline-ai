import test from "node:test";
import assert from "node:assert/strict";
import {validateHeader, validateDimensions, MAX_BYTES} from "../ui/lib/files.js";
import {validateResult, drawDetections, objectSummary} from "../ui/lib/results.js";
const png = new Uint8Array([137,80,78,71,13,10,26,10]);
const jpg = new Uint8Array([255,216,255,224]);
test("matching PNG and JPEG headers accepted", () => {
  assert.equal(validateHeader(png, 100, "image/png", "sample.PNG"), "image/png");
  assert.equal(validateHeader(jpg, 100, "image/jpeg", "sample.jpeg"), "image/jpeg");
});
test("empty and oversized files rejected", () => {
  for (const size of [0, MAX_BYTES + 1]) assert.throws(() => validateHeader(png, size, "image/png", "sample.png"));
});
test("MIME, extension and content must agree", () => {
  assert.throws(() => validateHeader(png, 100, "text/html", "sample.png"));
  assert.throws(() => validateHeader(png, 100, "image/png", "sample.svg"));
  assert.throws(() => validateHeader(new Uint8Array([1,2,3]), 100, "image/png", "sample.png"));
  assert.throws(() => validateHeader(jpg, 100, "image/png", "sample.png"));
});
test("image dimensions reject invalid and excessive values", () => {
  validateDimensions(1920, 1080);
  for (const dimensions of [[0,10],[-1,10],[NaN,10],[100000,100000],[1.2,10]]) {
    assert.throws(() => validateDimensions(...dimensions));
  }
});

const result = () => ({schema_version:1, image:{width:200,height:100}, runtime:{active:"CPUExecutionProvider"}, detections:[{label:"person",class_id:0,confidence:.9,box:[10,20,80,90]}], timings_ms:{initialization:null,preprocessing:1,inference:2,postprocessing:1,total_pipeline:4}});
test("result validation rejects stale dimensions and bad coordinates", () => {
  assert.equal(validateResult(result(),200,100).detections.length,1);
  assert.throws(() => validateResult(result(),100,200));
  const bad=result(); bad.detections[0].box[0]=NaN;
  assert.throws(() => validateResult(bad,200,100));
  const invalid=result(); invalid.timings_ms.inference=-1;
  assert.throws(() => validateResult(invalid,200,100));
});
test("canvas uses original-image box geometry and labels", () => {
  const rectangles=[], labels=[];
  const ctx={canvas:{width:200},strokeRect:(...args)=>rectangles.push(args),fillRect:()=>{},measureText:()=>({width:50}),fillText:(label)=>labels.push(label)};
  drawDetections(ctx,result().detections);
  assert.deepEqual(rectangles,[[10,20,70,70]]);
  assert.match(labels[0], /1\. person 90%/);
});

test("visual inventory derives only from actual detection labels", () => {
  assert.equal(objectSummary([{label:"person"},{label:"dog"},{label:"person"}]), "person: 2 · dog: 1");
  assert.match(objectSummary([]), /Objects may still be present/);
});
test("QNN output requires explicit verified execution", () => {
  const data = result(); data.runtime.active = "QNNExecutionProvider";
  assert.throws(() => validateResult(data, 200, 100));
  data.runtime.npu_verified = true;
  assert.equal(validateResult(data, 200, 100), data);
});
