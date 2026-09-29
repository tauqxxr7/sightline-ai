import test from "node:test";
import assert from "node:assert/strict";
import {readClipboardImage,clipboardFile} from "../ui/lib/clipboard.js";

test("clipboard import selects actual image bytes and safe generated filename",async()=>{
  const bytes=new Uint8Array([137,80,78,71,13,10,26,10]);
  const file=await readClipboardImage({read:async()=>[{types:["text/html","image/png"],getType:async type=>new Blob([bytes],{type})}]});
  assert.equal(file.name,"clipboard.png");assert.equal(file.type,"image/png");
  assert.deepEqual(new Uint8Array(await file.arrayBuffer()),bytes);
});
test("clipboard unavailable, denied and text-only states give actionable errors",async()=>{
  await assert.rejects(readClipboardImage(undefined),/unavailable/);
  await assert.rejects(readClipboardImage({read:async()=>{throw new Error("private detail");}}),/denied/);
  await assert.rejects(readClipboardImage({read:async()=>[{types:["text/plain"]}]}),/no PNG or JPEG/);
});
test("unsupported clipboard images are rejected",()=>{
  assert.throws(()=>clipboardFile(new Blob(["svg"],{type:"image/svg+xml"})),/PNG or JPEG/);
});
