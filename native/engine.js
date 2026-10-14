/** Northstar's original decisions, feedback, and guarded progress model. */
import {CONTENT} from './content.js';
import {assert, copy, integer, exactKeys, compress, decompress} from './snapshot.js';
export const DATA = CONTENT.case;
export const fields = ['mandate','tracker','ownership', ...DATA.BRIEF_FIELDS,'citations'];
const same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
export const workRoute = c => c.tracker === 2 ? 2 : c.mandate;
export const workProduct = c => copy(CONTENT.products[workRoute(c)]);
export function capacity(c) {
  return {advisory_hours: c.tracker === 2 ? 30 : DATA.MANDATES[c.mandate].hours, protected_hours: c.tracker === 2 ? 50 : 60,
    chosen_service_delivered:c.tracker !== 2, tracker_pending:c.tracker === 1};
}
export const commissionReview = c => copy(CONTENT.commission[`${c.mandate}:${c.tracker}:${c.ownership}`]);
export const ownsSubject = c => (c.scope === 0 && c.ownership === 1) || (c.scope === 1 && c.ownership === 2);
export function evidence(c) {
  const core = [0,1,2,3,6,7], optional = [ ...(c.scope === 0 ? [4] : []), ...([0,2].includes(workRoute(c)) ? [5] : []) ];
  const missing = core.filter(i => !c.citations.includes(i)), extra = c.citations.filter(i => !core.includes(i) && !optional.includes(i));
  const recordNames = ids => ids.map(i => DATA.RECORDS[i].title).join(', ');
  const result = {title:'Evidence selection',status:'Focused and sufficient',explanation:'',prompt:'',verdict:'Correct'};
  if (!missing.length && !extra.length) {
    const qualified = [];
    if (c.citations.includes(4)) qualified.push('The routing sample can motivate a proposed reporting or dispatch-exception scope, but its ten items do not establish shipment outcomes or a network error rate.');
    if (c.citations.includes(5)) qualified.push('The management tracker can provide context for the workshop or tracker product, but its green rating is not independent corroboration.');
    result.explanation = 'Your exhibit set is complete and focused for the topics in this briefing: the dashboard, approved benchmark, complete-network source, continuity file, management requests, and actual work product. This assesses source selection, not whether every conclusion you drew is correct. ' + (qualified.length ? qualified.join(' ') : 'You left other packet records out of the exhibit list because the submitted statements did not need them.');
  } else {
    const details = [];
    if (missing.length) details.push('Add records directly supporting your submitted statements: ' + recordNames(missing) + '.');
    if (extra.length) details.push('These exhibits are not tied to a distinct statement or proposed subject in this draft: ' + recordNames(extra) + '. An exhibit belongs in the brief only when you can name the limited claim it supports; keep other records in the notebook for later scoping.');
    result.status = missing.length && !extra.length ? 'Important source omitted' : 'Selection needs editing';
    result.verdict = missing.length && !extra.length ? 'Partly correct' : 'Incorrect'; result.explanation = details.join(' ');
  }
  return result;
}
export function findings(c) {
  const bank = CONTENT.feedback, correct = Number(c.network_tenths === 977);
  return copy([bank.number[correct],bank.delivery[`${correct}:${c.headline}`],bank.continuity[c.continuity],evidence(c),
    ...(c.tracker === 2 ? [bank.tracker] : []),bank.work[`${workRoute(c)}:${c.work_claim}`],bank.communication[c.communication],
    bank.accountability[`${c.ownership}:${c.authority}`],bank.scope[c.scope],bank.provider[`${c.ownership}:${c.scope}:${c.provider}`]]);
}
export function consequences(c) {
  const bank = CONTENT.consequences, cited = c.citations;
  const supported = c.network_tenths === 977 && c.headline === 1 && [0,1,2].every(i => cited.includes(i));
  const mode = !supported ? 0 : c.communication === 2 || c.authority === 2 ? 1 : 2;
  const qualified = Number(c.continuity === 1 && cited.includes(3));
  let assurance = bank.assurance[`${c.scope}:${c.provider}:${Number(ownsSubject(c))}`];
  if (cited.includes(4) && c.scope === 0) assurance += bank.routing;
  if (cited.includes(5) && [0,2].includes(workRoute(c))) assurance += bank.tracker;
  if ((cited.includes(4) && c.scope !== 0) || (cited.includes(5) && workRoute(c) === 1)) assurance += bank.extra;
  return [bank.delivery[`${mode}:${qualified}`],bank.mandate[`${workRoute(c)}:${Number(c.work_claim !== 0)}:${Number(c.ownership !== 0)}`],bank.governance[`${c.communication}:${c.authority}`],assurance].map((body,i) => [bank.titles[i],body]);
}
export function briefMarkdown(c) {
  const title = workProduct(c)[0], sources = c.citations.map(i => i === 7 ? title : DATA.RECORDS[i].title).join(', ') || 'None selected';
  return '### Proposed board briefing\n\n' +
    `**Work performed:** ${title}.\n\n` +
    `**Delivery:** The monthly on-time delivery figure you entered is ${(c.network_tenths / 10).toFixed(1)}%. ${DATA.BRIEF_OPTIONS.headline[c.headline]}\n\n` +
    `**Records cited:** ${sources}.\n\n` +
    `**Continuity:** ${DATA.BRIEF_OPTIONS.continuity[c.continuity]}\n\n` +
    `**Observation from our completed work:** ${DATA.WORK_CLAIMS[workRoute(c)][c.work_claim]}\n\n` +
    `**How we communicate:** ${DATA.BRIEF_OPTIONS.communication[c.communication]}\n\n` +
    `**Decisions and authority:** ${DATA.BRIEF_OPTIONS.authority[c.authority]}\n\n` +
    `**Proposed independent follow-up:** ${DATA.BRIEF_OPTIONS.scope[c.scope]} Provider: ${DATA.BRIEF_OPTIONS.provider[c.provider]}`;
}
export const firstChanges = state => state.first_brief ? fields.filter(field => !same(state.first_brief[field],state.c[field])) : [];
export function defaults(seed) {
  if (seed === undefined) seed = crypto.getRandomValues(new Uint32Array(1))[0] & 0x7fffffff;
  return {v:5,seed,stage:0,committed:[],roles_checked:false,commission_checked:false,brief_submitted:false,first_brief:null,
    c:{roles:Array(6).fill(-1),mandate:-1,tracker:-1,ownership:-1,citations:[],...Object.fromEntries(DATA.BRIEF_FIELDS.map(f => [f,-1]))}};
}
export const completeBrief = c => c.citations.length > 0 && DATA.BRIEF_FIELDS.every(f => c[f] !== -1);
export function ready(state, stage) {
  const c = state.c;
  if (stage === 1) return state.roles_checked && c.roles.every(v => integer(v,0,2));
  if (stage === 2) return state.commission_checked && integer(c.mandate,0,1) && integer(c.tracker,0,2) && integer(c.ownership,0,2);
  if (stage === 3) return true;
  if (stage === 4) return state.brief_submitted && completeBrief(c);
  return false;
}
function validateChoices(c) {
  assert(exactKeys(c,Object.keys(defaults(0).c)));
  assert(Array.isArray(c.roles) && c.roles.length === 6 && c.roles.every(v => integer(v,-1,2)));
  assert(integer(c.mandate,-1,1));
  assert(integer(c.tracker,-1,2) && integer(c.ownership,-1,2));
  for (const field of DATA.BRIEF_FIELDS) assert(integer(c[field],-1,field === 'network_tenths' ? 1000 : field === 'provider' ? 3 : field === 'scope' ? 1 : 2));
  assert(Array.isArray(c.citations) && c.citations.length <= 8 && c.citations.every((v,i) => integer(v,0,7) && (i === 0 || c.citations[i-1] < v)));
}
export function validate(state) {
  assert(exactKeys(state,Object.keys(defaults(0))) && state.v === 5);
  assert(integer(state.seed,0,2**31-1) && integer(state.stage,0,5));
  assert(['roles_checked','commission_checked','brief_submitted'].every(f => typeof state[f] === 'boolean'));
  validateChoices(state.c);
  assert(Array.isArray(state.committed) && state.committed.length <= 4 && state.committed.every((v,i) => v === i+1 && integer(v,1,4)));
  assert(state.stage <= state.committed.length+1 && state.committed.every(step => ready(state,step)));
  assert(!state.roles_checked || state.c.roles.every(v => v !== -1));
  assert(!state.commission_checked || ['mandate','tracker','ownership'].every(f => state.c[f] !== -1));
  assert(!state.brief_submitted || completeBrief(state.c));
  if (state.first_brief !== null) {
    assert(exactKeys(state.first_brief,fields));
    const candidate = {...state.c,...state.first_brief}; validateChoices(candidate); assert(completeBrief(candidate));
  }
  assert(!state.brief_submitted || state.first_brief !== null);
  assert(state.committed.includes(4) === state.brief_submitted);
  assert(state.stage !== 4 || same(state.committed,[1,2,3]) || same(state.committed,[1,2,3,4]));
  assert(state.stage !== 5 || same(state.committed,[1,2,3,4]) && state.brief_submitted);
  return copy(state);
}
export async function encode(state) { return compress(validate(state)); }
export async function decode(token) { try { return validate(await decompress(token)); } catch { return null; } }
export function pyRound(value) {
  const lower = Math.floor(value), fraction = value - lower;
  return fraction === 0.5 ? (lower % 2 === 0 ? lower : lower+1) : Math.round(value);
}
export function parseNetwork(raw) {
  if (typeof raw !== 'string' || raw.length > 64 || !/^\s*[+-]?(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?\s*$/.test(raw)) return null;
  const value = Number(raw); return Number.isFinite(value) && value >= 0 && value <= 100 ? pyRound(value*10) : null;
}
export class Lesson {
  constructor(state = defaults(), rawView, rawDraft = null) {
    const originalStage = state.stage;
    this.state = validate(state);
    if (this.state.committed.length) this.state.stage = Math.max(this.state.stage,Math.min(5,this.state.committed.length+1));
    const view = typeof rawView === 'string' && /^\d+$/.test(rawView) ? Number(rawView) : rawView === undefined ? originalStage : -1;
    this.view = integer(view,0,this.state.stage) ? view : this.state.stage;
    this.rawDraft = rawDraft === null ? this.state.c.network_tenths === -1 ? '' : (this.state.c.network_tenths/10).toFixed(1) : rawDraft;
    if (rawDraft !== null) assert((parseNetwork(rawDraft) ?? -1) === this.state.c.network_tenths, 'The numeric draft and saved choice disagree.');
  }
  get reviewing() { return this.view < this.state.stage; }
  current(stage) { assert(!this.reviewing && (stage === undefined || stage === this.state.stage), 'Earlier pages are view only.'); }
  browse(target) { assert(integer(target,0,this.state.stage),'That section is not available yet.'); this.view = target; }
  arrow(direction) { assert(direction === -1 || direction === 1); this.browse(Math.max(0,Math.min(this.state.stage,this.view+direction))); }
  choose(field,value,index) {
    const stage = field === 'roles' ? 1 : ['mandate','tracker','ownership'].includes(field) ? 2 : 4; this.current(stage);
    const state = copy(this.state); assert(field === 'roles' || fields.includes(field));
    if (field === 'roles') { assert(integer(index,0,5) && integer(value,0,2)); state.c.roles[index] = value; state.roles_checked = false; state.commission_checked = false; }
    else { state.c[field] = field === 'citations' ? [...value].sort((a,b) => a-b) : value; if (stage === 2) state.commission_checked = false; }
    state.brief_submitted = false; state.committed = state.committed.filter(step => step < stage); this.state = validate(state);
  }
  numeric(raw) { this.current(4); assert(typeof raw === 'string' && raw.length <= 64 && /^[0-9eE+\-.\s]*$/.test(raw)); this.choose('network_tenths',parseNetwork(raw) ?? -1); this.rawDraft = raw; }
  checkRoles() { this.current(1); assert(this.state.c.roles.every(v => v !== -1),'Classify every request first.'); this.state.roles_checked = true; this.state = validate(this.state); }
  checkCommission() { this.current(2); assert(['mandate','tracker','ownership'].every(f => this.state.c[f] !== -1),'Complete the commission decisions first.'); this.state.commission_checked = true; this.state = validate(this.state); }
  begin() { this.current(0); this.state.stage = this.view = 1; this.state = validate(this.state); }
  advance(stage) { this.current(stage); assert([1,2,3].includes(stage) && ready(this.state,stage),'Complete this section before continuing.'); this.state.committed = Array.from({length:stage},(_,i) => i+1); this.state.stage = this.view = stage+1; this.state = validate(this.state); }
  submit() {
    this.current(4); assert(completeBrief(this.state.c) && parseNetwork(this.rawDraft) !== null,'Complete and cite the board briefing first.');
    const state = copy(this.state); state.brief_submitted = true;
    if (state.first_brief === null) state.first_brief = Object.fromEntries(fields.map(field => [field,copy(state.c[field])]));
    state.committed = [1,2,3,4]; state.stage = 5; this.state = validate(state); this.view = 5;
  }
  revise() { this.current(5); this.state.stage = this.view = 4; this.state.committed = [1,2,3]; this.state.brief_submitted = false; this.state = validate(this.state); }
  reset() { this.current(); this.state = defaults(); this.view = 0; this.rawDraft = ''; }
}
