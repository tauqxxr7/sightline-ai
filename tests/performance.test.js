import test from "node:test";
import assert from "node:assert/strict";
import {validateBenchmark,escape} from "../ui/lib/view.js";

test("benchmark response rejects missing, fake-kind or non-CPU results",()=>{
  for(const data of [null,{}, {report:{schema_version:1,kind:"example"}}]) assert.throws(()=>validateBenchmark(data));
});
test("shared detail escaping prevents runtime strings becoming markup",()=>{
  assert.equal(escape('<script>"&'), '&lt;script&gt;&quot;&amp;');
});
