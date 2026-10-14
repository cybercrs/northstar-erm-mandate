import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {CONTENT} from '../content.js';
import {Lesson,defaults,validate,encode,decode,capacity,workProduct,findings,evidence,consequences,briefMarkdown,parseNetwork,firstChanges} from '../engine.js';
import {shuffled} from '../random.js';
import {compress,parseJSON,base64url,from64} from '../snapshot.js';
const oracles = JSON.parse(await readFile(new URL('./oracles.json',import.meta.url)));

test('1,936 independent Python finding, consequence, product, capacity and brief outcomes', () => {
  for (const item of oracles.outcomes) {
    if (item.evidence) assert.deepEqual(evidence(item.c),item.evidence);
    else {
      assert.deepEqual(capacity(item.c),item.capacity); assert.deepEqual(workProduct(item.c),item.product);
      assert.deepEqual(findings(item.c),item.findings); assert.equal(briefMarkdown(item.c),item.brief);
    }
    assert.deepEqual(consequences(item.c),item.consequences);
  }
});
test('102 exact Python string-seeded shuffle orders including zero and maximum seeds', async () => {
  for (const item of oracles.orders) assert.deepEqual(await shuffled(item.input,item.seed,item.field),item.expected);
});
test('Python ties-to-even numeric outcomes and malformed numeric drafts', () => {
  for (const item of oracles.rounding) assert.equal(parseNetwork(item.raw),item.expected);
  for (const raw of ['', '.', '97.', '1e', 'NaN', 'Infinity', '-1', '100.1', '101', '97,7', 'a', '9'.repeat(65)]) assert.equal(parseNetwork(raw),null);
});
test('original compressed bookmarks, native round trips and legacy review restoration',async () => {
  for (const item of oracles.snapshots) {
    assert.deepEqual(await decode(item.token),item.state);
    assert.deepEqual(await decode(await encode(item.state)),item.state);
    const old = structuredClone(item.state); old.stage = 2;
    const lesson = new Lesson(old);
    assert.equal(lesson.state.stage,5); assert.equal(lesson.view,2); assert.equal(lesson.reviewing,true);
    const future = new Lesson(item.state,'999'); assert.equal(future.view,5);
  }
});
test('snapshot rejects unknown fields, duplicate keys, floats, booleans, skips, bombs and trailing data', async () => {
  for (const mutate of [s=>s.seed=true,s=>s.stage=6,s=>s.v=4,s=>s.name='student',s=>s.c.headline=true,s=>s.c.citations=[1,1],s=>s.committed=[1],s=>s.stage=5]) {
    const state=defaults(0);mutate(state);assert.throws(()=>validate(state));assert.equal(await decode(await compress(state)),null);
  }
  const state=defaults(0),text=JSON.stringify(state);
  assert.throws(()=>parseJSON(text.replace('"seed":0','"seed":0.0')));
  assert.throws(()=>parseJSON(text.slice(0,-1)+',"stage":0}'));
  assert.throws(()=>parseJSON(text+' false'));
  for(const token of ['', 'not a token', 'AAAA', 'x'.repeat(6001),oracles.snapshots[0].token+'=']) assert.equal(await decode(token),null);
  async function rawToken(text) { return base64url(new Uint8Array(await new Response(new Blob([text]).stream().pipeThrough(new CompressionStream('deflate'))).arrayBuffer())); }
  assert.equal(await decode(await rawToken(' '.repeat(100000))),null);
  assert.equal(await decode(await rawToken(text.slice(0,-1)+',"stage":0}')),null);
  assert.equal(await decode(await rawToken(text.replace('"seed":0','"seed":0.0'))),null);
  const bytes=from64(await encode(state));
  assert.equal(await decode(base64url(new Uint8Array([...bytes,0,0]))),null);
});
test('full guarded routes preserve first submission, optional revision, drafts and reset',async () => {
  for (const route of [0,1,2]) {
    const lesson = new Lesson(defaults(1234));assert.throws(()=>lesson.advance(1));lesson.arrow(1);assert.equal(lesson.view,0);
    lesson.begin();assert.throws(()=>lesson.checkRoles());
    for(let i=0;i<6;i++)lesson.choose('roles',(CONTENT.case.REQUESTS[i].category+1)%3,i);
    lesson.checkRoles();const repeated=structuredClone(lesson.state);lesson.checkRoles();assert.deepEqual(lesson.state,repeated);
    for(let i=0;i<6;i++)lesson.choose('roles',CONTENT.case.REQUESTS[i].category,i);
    assert.throws(()=>lesson.advance(1));lesson.checkRoles();lesson.advance(1);
    lesson.choose('mandate',Number(route===1));lesson.choose('tracker',route===2?2:0);lesson.choose('ownership',0);
    assert.throws(()=>lesson.advance(2));lesson.checkCommission();lesson.advance(2);lesson.advance(3);
    lesson.numeric('97.');const token=await encode(lesson.state);const restored=new Lesson(await decode(token),'4','97.');assert.equal(restored.rawDraft,'97.');assert.throws(()=>restored.submit());
    lesson.numeric('98.6');
    for(const [field,value] of Object.entries({headline:0,continuity:0,work_claim:2,communication:1,authority:1,scope:0,provider:3,citations:[0]}))lesson.choose(field,value);
    lesson.submit();const wrong=structuredClone(lesson.state),first=structuredClone(wrong.first_brief);
    for(let view=4;view>=0;view--) {
      lesson.arrow(-1);const saved=structuredClone(lesson.state);
      for(const action of [()=>lesson.reset(),()=>lesson.revise(),()=>lesson.submit(),()=>lesson.checkRoles(),()=>lesson.checkCommission(),()=>lesson.begin(),()=>lesson.advance(view),()=>lesson.choose('headline',1),()=>lesson.numeric('97.7')]) {assert.throws(action);assert.deepEqual(lesson.state,saved);}
    }
    for(let view=1;view<=5;view++)lesson.arrow(1);assert.deepEqual(lesson.state,wrong);lesson.arrow(1);assert.equal(lesson.view,5);
    lesson.revise();assert.equal(lesson.state.brief_submitted,false);assert.deepEqual(lesson.state.first_brief,first);
    lesson.numeric('97.7');lesson.choose('headline',1);lesson.choose('continuity',1);lesson.choose('work_claim',0);lesson.choose('communication',0);lesson.choose('authority',0);lesson.choose('provider',0);lesson.choose('citations',[0,1,2,3,6,7]);lesson.submit();
    assert.deepEqual(lesson.state.first_brief,first);assert.ok(firstChanges(lesson.state).includes('network_tenths'));
    const final=await encode(lesson.state);lesson.reset();assert.equal(lesson.state.first_brief,null);assert.equal((await decode(final)).stage,5);
  }
});
