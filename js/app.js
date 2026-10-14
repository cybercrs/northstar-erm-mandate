import {CONTENT} from './content.js';
import {DATA,Lesson,decode,encode,defaults,ready,completeBrief,parseNetwork,workRoute,workProduct,capacity,commissionReview,findings,consequences,briefMarkdown,firstChanges} from './engine.js';
import {shuffled} from './random.js';
import {readDraft,draftToken} from './snapshot.js';
const root=document.querySelector('#app');
let lesson,notice='',orders={},ordersSeed=-1,queue=Promise.resolve();
const escape = value => String(value).replace(/[&<>"']/g,character=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
function markdown(text) {
  return text.split('\n\n').map(paragraph => paragraph.startsWith('### ') ? `<h3>${escape(paragraph.slice(4))}</h3>` : `<p>${escape(paragraph).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\n/g,'<br>')}</p>`).join('');
}
const saved = (label,value) => `<div class="saved"><strong>${escape(label)}</strong><span>${escape(value ?? 'No selection')}</span></div>`;
const finding = item => `<div class="result"><h3>${escape(item.title)}</h3><div class="status"><span class="verdict ${item.verdict==='Correct'?'correct':item.verdict==='Partly correct'?'partial':'incorrect'}">${escape(item.verdict)}</span>${escape(item.status)}</div><p>${escape(item.explanation)}</p></div>`;
async function prepareOrders() {
  if(ordersSeed===lesson.state.seed)return;
  const definitions = {inbox:[0,1,2,3,4,5],mandate:[0,1],tracker:[0,1,2],ownership:[0,1,2],work_claim:[0,1,2],...Object.fromEntries(Object.entries(DATA.BRIEF_OPTIONS).map(([f,options])=>[f,Object.keys(options).map(Number)])),...Object.fromEntries(DATA.REQUESTS.map((_,i)=>[`role:${i}`,[0,1,2]]))};
  const entries=await Promise.all(Object.entries(definitions).map(async([field,input])=>[field,await shuffled(input,lesson.state.seed,field)]));
  orders=Object.fromEntries(entries);ordersSeed=lesson.state.seed;
}
function roleCards() {
  const c=lesson.state.c;
  return `<div class="columns inbox">${orders.inbox.map((id,position)=>`<div class="request" data-request="${id}"><div class="case-card"><h3>Request ${position+1}</h3><p>${escape(DATA.REQUESTS[id].text)}</p></div>${lesson.reviewing?saved(`Service category for request ${position+1}`,DATA.CATEGORIES[c.roles[id]]):`<label class="field-label" for="role-${id}">Service category for request ${position+1}</label><select id="role-${id}" data-role="${id}"><option value="" disabled ${c.roles[id]===-1?'selected':''}>Choose a category</option>${orders[`role:${id}`].map(value=>`<option value="${value}" ${c.roles[id]===value?'selected':''}>${escape(DATA.CATEGORIES[value])}</option>`).join('')}</select>`}</div>`).join('')}</div>`;
}
function record(node) {
  const c=lesson.state.c,item=DATA.RECORDS[node.id],product=workProduct(c),title=node.id===7?product[0]:item.title,body=node.id===7?product[1]:item.body;
  return `<details class="record" data-record="${node.id}"><summary>${escape(title)}</summary><div class="detail-body">${node.notebook?'':`<p class="caption">${escape(item.type)}</p>`}${markdown((node.notebook?'':'**Why this record is here:** ')+item.context)}${markdown((node.notebook?'':'**Record:** ')+body)}</div></details>`;
}
function optionField(node) {
  const c=lesson.state.c,options=node.field==='work_claim'?DATA.WORK_CLAIMS[workRoute(c)]:node.options;
  if(lesson.reviewing)return saved(node.label,options[c[node.field]]);
  return `<fieldset data-field="${node.field}"><legend>${escape(node.label)}</legend>${node.help?`<p class="help">${escape(node.help)}</p>`:''}${orders[node.field].map(value=>`<label class="option"><input id="${node.field}-${value}" type="radio" name="${node.field}" value="${value}" data-choice="${node.field}" ${c[node.field]===value?'checked':''}><span>${escape(options[value])}</span></label>`).join('')}</fieldset>`;
}
function action(node) {
  if(lesson.reviewing)return '';
  const c=lesson.state.c;
  const disabled=node.action==='check_inbox'?c.roles.some(value=>value===-1):node.action==='check_plan'?['mandate','tracker','ownership'].some(f=>c[f]===-1):node.action==='advance'?!ready(lesson.state,node.args[0]):node.action==='send_brief'?!completeBrief(c)||parseNetwork(lesson.rawDraft)===null:false;
  return `<button class="action ${node.primary?'primary':''}" id="action-${node.action}-${node.args[0]??0}" data-action="${node.action}" data-target="${node.args[0]??''}" ${disabled?'disabled':''}>${escape(node.label)}</button>`;
}
function renderNodes(nodes) {
  let inboxShown=false,gated=false;
  return nodes.map(node=>{
    if(lesson.view===1&&node.kind==='action'&&node.action==='check_inbox')gated=true;
    else if(lesson.view===2&&node.kind==='action'&&node.action==='check_plan')gated=true;
    else if(node.kind==='divider')gated=false;
    if(gated&&node.kind!=='action'&&! (lesson.view===1?lesson.state.roles_checked:lesson.state.commission_checked))return '';
    const c=lesson.state.c;
    if(node.kind==='header')return `<h2 id="lesson-heading" tabindex="-1">${escape(node.text)}</h2>`;
    if(node.kind==='subheader')return `<h3>${escape(node.text)}</h3>`;
    if(node.kind==='markdown')return markdown(node.text);
    if(node.kind==='html')return lesson.view===4&&!completeBrief(c)&&node.text.includes('class="memo"')?'':node.text;
    if(node.kind==='columns') {
      if(node.children.some(column=>column.some(child=>child.kind==='role'))) { if(inboxShown)return '';inboxShown=true;return roleCards(); }
      const columns=node.children.map(children=>renderNodes(children));return columns.every(value=>!value)?'':`<div class="columns">${columns.map(html=>`<div>${html}</div>`).join('')}</div>`;
    }
    if(node.kind==='choice')return optionField(node);
    if(node.kind==='record')return record(node);
    if(node.kind==='details')return `<details><summary>${escape(node.label)}</summary><div class="detail-body">${renderNodes(node.children)}</div></details>`;
    if(node.kind==='role_feedback')return orders.inbox.map((id,pos)=>finding({title:`Request ${pos+1}`,verdict:c.roles[id]===DATA.REQUESTS[id].category?'Correct':'Incorrect',status:`You selected ${DATA.CATEGORIES[c.roles[id]]}`,explanation:DATA.REQUESTS[id].reason})).join('');
    if(node.kind==='commission_feedback')return commissionReview(c).map(finding).join('');
    if(node.kind==='capacity') {
      const used=capacity(c);return `<div class="metric-grid">${[[used.advisory_hours,'Hours assigned to ERM work'],[used.protected_hours,'Hours left on approved access-control audit'],[used.tracker_pending?'To be requested':c.tracker===0?'Not needed now':'Not obtained','Tracker approval']].map(([value,label])=>`<div class="metric"><strong>${escape(value)}</strong><span>${escape(label)}</span></div>`).join('')}</div>`;
    }
    if(node.kind==='saved_choice') {
      const value=node.field==='mandate'?DATA.MANDATES[c.mandate].name:node.field==='tracker'?DATA.TRACKER_CHOICES[c.tracker]:DATA.OWNERSHIP_CHOICES[c.ownership];return markdown(node.prefix+' '+value);
    }
    if(node.kind==='number') {
      if(lesson.reviewing)return saved(node.label,c.network_tenths===-1?null:`${(c.network_tenths/10).toFixed(1)}%`);
      return `<fieldset><label class="field-label" for="network-result">${escape(node.label)}</label><div class="number-row"><input id="network-result" role="spinbutton" aria-valuemin="0" aria-valuemax="100" ${parseNetwork(lesson.rawDraft)===null?'':`aria-valuenow="${c.network_tenths/10}"`} inputmode="decimal" maxlength="64" autocomplete="off" value="${escape(lesson.rawDraft)}"><button data-nudge="-1" aria-label="Decrease monthly on-time delivery by 0.1">−</button><button data-nudge="1" aria-label="Increase monthly on-time delivery by 0.1">+</button></div>${lesson.rawDraft!==''&&parseNetwork(lesson.rawDraft)===null?'<p class="help" role="status">Enter a percentage from 0 to 100.</p>':''}</fieldset>`;
    }
    if(node.kind==='citations') {
      const labels=i=>i===7?workProduct(c)[0]:DATA.RECORDS[i].title;
      if(lesson.reviewing)return saved(node.label,c.citations.map(labels).join(', ')||'None selected');
      return `<fieldset data-field="citations"><legend>${escape(node.label)}</legend><p class="help">${escape(node.help)}</p>${Object.keys(DATA.RECORDS).map(Number).map(i=>`<label class="option"><input id="citation-${i}" type="checkbox" data-citation="${i}" ${c.citations.includes(i)?'checked':''}><span>${escape(labels(i))}</span></label>`).join('')}</fieldset>`;
    }
    if(node.kind==='brief')return completeBrief(c)?`<div class="brief">${markdown(briefMarkdown(c))}</div>`:'';
    if(node.kind==='findings')return findings(c).map(finding).join('');
    if(node.kind==='consequences')return consequences(c).map(([title,body])=>`<div class="case-card"><h3>${escape(title)}</h3><p>${escape(body)}</p></div>`).join('');
    if(node.kind==='changes')return firstChanges(lesson.state).length?markdown('**Changes since your first submission:** '+firstChanges(lesson.state).map(f=>f.replace(/_/g,' ')).join(', ')+'.'):'';
    if(node.kind==='action')return action(node);
    if(node.kind==='divider')return '<hr>';
    throw new Error('Unknown lesson content.');
  }).join('');
}
const arrow = (direction,label,disabled) => `<button id="${label.toLowerCase()}" class="arrow" data-arrow="${direction}" aria-label="${label}" title="${label==='Back'?'Back: review the previous reached page. Earlier pages are read-only.':'Forward: review the next reached page. Use the existing action on your current page to continue.'}" ${disabled?'disabled':''}><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" ${direction===1?'style="transform:rotate(180deg)"':''}><path d="M19 12H5m0 0 7-7m-7 7 7 7"/></svg></button>`;
async function render(scroll=false) {
  const focus=document.activeElement?.id,selection=document.activeElement?.id==='network-result'?[document.activeElement.selectionStart,document.activeElement.selectionEnd]:null;
  const opened=new Set([...root.querySelectorAll('details[open]')].map(d=>d.querySelector('summary').textContent));
  await prepareOrders();const view=lesson.view,stage=lesson.state.stage;
  root.innerHTML=`<header class="hero"><div class="kicker">ENTERPRISE RISK MANAGEMENT</div><h1>Northstar Cold Chain</h1><p>The ERM Mandate · Prepare the CAE for the board.</p></header><nav class="review-nav" aria-label="Review navigation"><small>Page ${view+1} of 6</small>${arrow(-1,'Back',view===0)}${arrow(1,'Forward',view===stage)}</nav><nav class="rail" aria-label="Lesson sections">${DATA.STAGES.map((name,i)=>`<button class="step ${i===view?'active':i<stage?'done':''}" data-browse="${i}" ${i===view?'aria-current="step"':''} ${i>stage?'disabled':''}>${escape(name)}</button>`).join('')}</nav>${notice?`<p class="notice warning" role="status">${escape(notice)}</p>`:''}${lesson.reviewing?'<p class="notice" role="status">Review only. Return to your current page to continue the activity.</p>':''}<section id="lesson">${renderNodes(CONTENT.screens[view])}</section><details class="trail"><summary>Your decision trail</summary><div class="detail-body"><p><strong>Approved delivery criterion</strong><br>At least 98% monthly on-time delivery across existing and new shipments.</p><p><strong>Available internal-audit capacity</strong><br>60 hours committed to access-control assurance; 20 available for ERM advice.</p><button class="action" data-action="reset" ${lesson.reviewing?'disabled':''}>Start over</button></div></details><div id="error" role="alert"></div>`;
  if(!scroll)for(const details of root.querySelectorAll('details'))if(opened.has(details.querySelector('summary').textContent))details.open=true;
  const target=focus?document.getElementById(focus):null;
  if(target&&!target.disabled) { target.focus({preventScroll:true});if(selection)target.setSelectionRange(...selection); }
  else if(scroll)document.getElementById('lesson-heading').focus({preventScroll:true});
  if(scroll)window.scrollTo({top:0,left:0,behavior:'instant'});
  document.documentElement.dataset.ready='true';document.documentElement.dataset.busy='false';
}
async function sync() {
  const url=new URL(location.href);url.searchParams.set('progress',await encode(lesson.state));url.searchParams.set('view',String(lesson.view));
  if(lesson.rawDraft!==''&&parseNetwork(lesson.rawDraft)!==null&&lesson.rawDraft===(lesson.state.c.network_tenths/10).toFixed(1)||lesson.rawDraft==='')url.searchParams.delete('draft');
  else url.searchParams.set('draft',draftToken(lesson.rawDraft));
  history.replaceState(null,'',url);
}
function dispatch(operation,scroll=false) {
  document.documentElement.dataset.busy='true';
  queue=queue.then(async()=>{operation();await sync();await render(scroll);}).catch(error=>{document.documentElement.dataset.busy='false';const target=document.getElementById('error');if(target)target.innerHTML=`<p class="notice error">${escape(error.message)}</p>`;else root.textContent=error.message;});
  return queue;
}
root.addEventListener('change',event=>{
  const element=event.target;
  if(element.dataset.role!==undefined)dispatch(()=>lesson.choose('roles',Number(element.value),Number(element.dataset.role)));
  else if(element.dataset.choice)dispatch(()=>lesson.choose(element.dataset.choice,Number(element.value)));
  else if(element.dataset.citation!==undefined) {const id=Number(element.dataset.citation),checked=element.checked;dispatch(()=>lesson.choose('citations',checked?[...lesson.state.c.citations,id]:lesson.state.c.citations.filter(i=>i!==id)));}
});
root.addEventListener('input',event=>{
  if(event.target.id==='network-result') {
    const raw=event.target.value;
    // The numeric control never retains arbitrary text or a stale accepted value.
    const accepted=/^[0-9eE+\-.\s]*$/.test(raw)?raw:'';
    dispatch(()=>lesson.numeric(accepted));
  }
});
root.addEventListener('keydown',event=>{if(event.target.id==='network-result'&&['ArrowUp','ArrowDown'].includes(event.key)){event.preventDefault();nudge(event.key==='ArrowUp'?1:-1);}});
function nudge(direction) {dispatch(()=>lesson.numeric((Math.min(1000,Math.max(0,(lesson.state.c.network_tenths===-1?0:lesson.state.c.network_tenths)+direction))/10).toFixed(1)));}
root.addEventListener('click',event=>{
  const button=event.target.closest('button');if(!button||button.disabled)return;
  if(button.dataset.nudge) { nudge(Number(button.dataset.nudge));return; }
  if(button.dataset.arrow)dispatch(()=>lesson.arrow(Number(button.dataset.arrow)),true);
  else if(button.dataset.browse!==undefined)dispatch(()=>lesson.browse(Number(button.dataset.browse)),true);
  else if(button.dataset.action) {
    const name=button.dataset.action,target=Number(button.dataset.target);
    const actions={go:()=>lesson.state.stage===0?lesson.begin():target===4?lesson.revise():lesson.browse(target),advance:()=>lesson.advance(target),check_inbox:()=>lesson.checkRoles(),check_plan:()=>lesson.checkCommission(),send_brief:()=>lesson.submit(),reset:()=>{lesson.reset();notice='';}};
    dispatch(actions[name],['go','advance','send_brief','reset'].includes(name));
  }
});
async function restore() {
  const query=new URL(location.href).searchParams,values=query.getAll('progress');
  const state=values.length===0?defaults():values.length===1?await decode(values[0]):null;
  notice=state?'':'This link could not restore your choices. A new case has started.';
  const rawView=query.getAll('view');const rawDraft=query.getAll('draft');
  try {lesson=new Lesson(state??defaults(),rawView.length===0?undefined:rawView.length===1?rawView[0]:null,rawDraft.length===1?readDraft(rawDraft[0]):null);}
  catch {lesson=new Lesson(state??defaults(),rawView.length===1?rawView[0]:undefined);notice='The unfinished numeric draft could not be restored. Your saved choices are available.';}
  await sync();await render();
}
window.addEventListener('popstate',()=>{queue=queue.then(restore).catch(error=>root.textContent=error.message);});
try {await restore();} catch {root.innerHTML='<p role="alert">This activity needs a current browser with JavaScript, Web Crypto, and Compression Streams enabled. Refresh after checking your browser.</p>';}
