import test from "node:test";
import assert from "node:assert/strict";
import {regionBounds,dragBounds,transformPixels} from "../ui/lib/privacy.js";

test("manual regions reject empty, fractional, invalid and out-of-image coordinates",()=>{
  assert.deepEqual(regionBounds(1,2,3,4,10,10),{x:1,y:2,width:3,height:4});
  for(const args of [[-1,0,1,1],[0,0,0,1],[0,0,11,1],[0.5,0,1,1],[NaN,0,1,1]])
    assert.throws(()=>regionBounds(...args,10,10));
});
test("drag regions support reverse drags and clamp to the image",()=>{
  assert.deepEqual(dragBounds({x:9,y:8},{x:-2,y:2},10,10),{x:0,y:2,width:9,height:6});
  assert.throws(()=>dragBounds({x:2,y:2},{x:2,y:2},10,10));
});
test("solid fill replaces every crop channel, including alpha, without mutating source",()=>{
  const source=new Uint8ClampedArray([255,30,60,0,1,2,3,90]);
  assert.deepEqual([...transformPixels(source,2,1,"solid")],[0,0,0,255,0,0,0,255]);
  assert.equal(source[0],255);assert.equal(source[3],0);
});
test("pixelation averages the crop and handles partial blocks",()=>{
  const source=new Uint8ClampedArray(17*4);
  for(let x=0;x<17;x++){source[x*4]=x*10;source[x*4+3]=255;}
  const output=transformPixels(source,17,1,"pixelate");
  assert.equal(output[0],75);assert.equal(output[15*4],75);assert.equal(output[16*4],160);
});
test("blur changes spatial detail and preserves uniform colors including tiny regions",()=>{
  const source=new Uint8ClampedArray(32*4);source[16*4]=255;
  const out=transformPixels(source,32,1,"blur");
  assert.ok(out[16*4]<255);assert.ok(out[15*4]>0);assert.equal(out[3],255);
  assert.deepEqual([...transformPixels(new Uint8ClampedArray([20,40,60,255]),1,1,"blur")],[20,40,60,255]);
});
test("unknown transformations and malformed crop buffers are rejected",()=>{
  assert.throws(()=>transformPixels(new Uint8ClampedArray(4),1,1,"none"));
  assert.throws(()=>transformPixels(new Uint8ClampedArray(4),2,2,"solid"));
});
