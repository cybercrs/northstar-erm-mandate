"""Export unchanged lesson content and independent Python validation oracles."""
from __future__ import annotations
from dataclasses import asdict
from itertools import product
import hashlib
import json
from pathlib import Path
import random
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from northstar import board_case as case, board_logic as logic, board_progress as progress
HERE = Path(__file__).resolve().parent


def cbase(**overrides):
    c = progress.defaults(0)['c']
    c.update(dict(roles=[r['category'] for r in case.REQUESTS],mandate=0,tracker=0,ownership=0,
                  network_tenths=977,headline=1,continuity=1,work_claim=0,communication=0,authority=0,
                  scope=0,provider=0,citations=[0,1,2,3,6,7]))
    c.update(overrides)
    return c


def find(title, **overrides):
    return next(asdict(x) | {'verdict':x.verdict} for x in logic.findings(cbase(**overrides)) if x.title==title)


class State(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


class Container:
    def __init__(self, recorder, children):self.recorder,self.children=recorder,children
    def __enter__(self):self.recorder.stack.append(self.children);return self
    def __exit__(self,*args):self.recorder.stack.pop()
    def button(self,*args,**kwargs):return self.recorder.button(*args,**kwargs)


class Recorder:
    def __init__(self):self.stack=[[]];self.session_state=State(ns={'seed':0,'stage':5,'c':cbase(),'roles_checked':True,'commission_checked':True,'brief_submitted':True})
    def node(self,kind,**data):
        node={'kind':kind,**data};self.stack[-1].append(node);return node
    def __getattr__(self,kind):
        if kind in ('header','subheader','caption','info','warning'):return lambda text:self.node(kind,text=text)
        raise AttributeError(kind)
    def markdown(self,text,unsafe_allow_html=False):
        text=text.replace(r'\$', '$')
        if '__BRIEF__' in text:self.node('brief');return
        if '__ROLE_FEEDBACK__' in text:self.node('role_feedback');return
        if '__CHANGES__' in text or '  CHANGES  ' in text:self.node('changes');return
        for prefix,field in (('**Commissioned service:**','mandate'),('**Tracker decision:**','tracker'),('**Ownership agreement:**','ownership'),('**Agreement on responsibility:**','ownership')):
            if text.startswith(prefix):self.node('saved_choice',prefix=prefix,field=field);return
        self.node('html' if unsafe_allow_html else 'markdown',text=text)
    def columns(self,count):
        n=count if isinstance(count,int) else len(count)
        children=[[] for _ in range(n)];self.node('columns',children=children)
        return [Container(self,x) for x in children]
    def radio(self,label,options,**kwargs):
        field=kwargs['args'][0]
        self.node('choice',field=field,label=label,options={str(i):kwargs['format_func'](i).replace(r'\$', '$') for i in options},help=kwargs.get('help'))
    def selectbox(self,label,options,**kwargs):
        self.node('role',index=kwargs['args'][2],label=label)
    def number_input(self,label,**kwargs):self.node('number',label=label,field=kwargs['args'][0])
    def multiselect(self,label,options,**kwargs):self.node('citations',label=label,help=kwargs.get('help'))
    def button(self,label,**kwargs):
        callback=kwargs.get('on_click');name=callback.__name__ if callback else ''
        if label=='Back':return False
        self.node('action',label=label,action=name,args=list(kwargs.get('args',())),primary=kwargs.get('type')=='primary')
        return False
    def divider(self):self.node('divider')
    def popover(self,label,**kwargs):
        if label=='Open case notebook':
            children=[];self.node('details',label=label,children=children);return Container(self,children)
        id_=next((i for i,r in case.RECORDS.items() if r['title']==label),7)
        self.node('record',id=id_,notebook=False);return Container(self,[])
    def expander(self,label,**kwargs):
        if label=='View your submitted briefing':
            children=[];self.node('details',label=label,children=children);return Container(self,children)
        id_=next((i for i,r in case.RECORDS.items() if r['title']==label),7)
        self.node('record',id=id_,notebook=True);return Container(self,[])


def screens():
    app=runpy.run_path(str(ROOT/'board_app.py'));g=app['main'].__globals__;rec=Recorder();g['st']=rec
    g['brief_markdown']=lambda c:'__BRIEF__'
    g['role_review']=lambda c,seed:[{'selected':0,'expected':0,'reason':'__ROLE_FEEDBACK__'}]
    g['commission_review']=lambda c:[None];g['findings']=lambda c:[None]
    g['show_finding']=lambda x:rec.node('findings' if rec.session_state.ns['stage']==5 else 'commission_feedback')
    g['metric_grid']=lambda x:rec.node('capacity')
    g['briefing_consequences']=lambda c:[('__CONSEQUENCES__','')]
    original_card=g['card']
    g['card']=lambda title,body,eyebrow='':rec.node('consequences') if title=='__CONSEQUENCES__' else original_card(title,body,eyebrow)
    g['first_brief_changes']=lambda state:['__CHANGES__']
    result=[]
    for i,name in enumerate(('assignment','inbox','commission','board_packet','board_brief','board_feedback')):
        rec.stack=[[]];rec.session_state.ns['stage']=i;app[name]();result.append(rec.stack[0])
    return result


def consequence_bank():
    def result(index,**c):return logic.briefing_consequences(cbase(**c))[index][1]
    delivery={}
    for mode,continuity in product(range(3),range(2)):
        c={'network_tenths':986 if mode==0 else 977,'communication':2 if mode==1 else 0,'continuity':continuity}
        delivery[f'{mode}:{continuity}']=result(0,**c)
    mandate={}
    for route,bad_claim,bad_owner in product(range(3),range(2),range(2)):
        mandate[f'{route}:{bad_claim}:{bad_owner}']=result(1,mandate=1 if route==1 else 0,tracker=2 if route==2 else 0,work_claim=bad_claim,ownership=bad_owner)
    governance={f'{communication}:{authority}':result(2,communication=communication,authority=authority) for communication,authority in product(range(3),repeat=2)}
    assurance={}
    for scope,provider,owns in product(range(2),range(4),range(2)):
        assurance[f'{scope}:{provider}:{owns}']=result(3,scope=scope,provider=provider,ownership=(scope+1) if owns else 0)
    base=result(3)
    routing=result(3,citations=[0,1,2,3,4,6,7])[len(base):]
    tracker=result(3,citations=[0,1,2,3,5,6,7])[len(base):]
    other=result(3,scope=1,citations=[0,1,2,3,4,6,7]);other_base=result(3,scope=1)
    return {'delivery':delivery,'mandate':mandate,'governance':governance,'assurance':assurance,'routing':routing,'tracker':tracker,'extra':other[len(other_base):],
            'titles':[x[0] for x in logic.briefing_consequences(cbase())]}


def export():
    data={name:getattr(case,name) for name in ('STAGES','CATEGORIES','REQUESTS','MANDATES','TRACKER_CHOICES','OWNERSHIP_CHOICES','RECORDS','WORK_CLAIMS','BRIEF_OPTIONS','BRIEF_FIELDS')}
    bank={
        'number':{str(correct):find('Complete-network figure',network_tenths=977 if correct else 986) for correct in (0,1)},
        'delivery':{f'{correct}:{headline}':find('Delivery reporting',network_tenths=977 if correct else 986,headline=headline) for correct,headline in product((0,1),range(3))},
        'continuity':{str(i):find('Continuity evidence',continuity=i) for i in range(3)},
        'work':{f'{route}:{claim}':find('Advisory work product',mandate=int(route==1),tracker=2 if route==2 else 0,work_claim=claim) for route,claim in product(range(3),repeat=2)},
        'communication':{str(i):find('Mandate and confidence',communication=i) for i in range(3)},
        'accountability':{f'{owner}:{authority}':find('Management accountability',ownership=owner,authority=authority) for owner,authority in product(range(3),repeat=2)},
        'scope':{str(i):find('Future assurance subject',scope=i) for i in range(2)},
        'provider':{f'{owner}:{scope}:{provider}':find('Future independent view',ownership=owner,scope=scope,provider=provider) for owner,scope,provider in product(range(3),range(2),range(4))},
        'tracker':find('Mandate and capacity',tracker=2),
    }
    commissions={f'{m}:{t}:{o}':[asdict(x)|{'verdict':x.verdict} for x in logic.commission_review(cbase(mandate=m,tracker=t,ownership=o))] for m,t,o in product(range(2),range(3),range(3))}
    content={'case':data,'screens':screens(),'feedback':bank,'commission':commissions,'consequences':consequence_bank(),
             'products':{str(route):logic.work_product(cbase(mandate=int(route==1),tracker=2 if route==2 else 0)) for route in range(3)}}
    (HERE/'content.js').write_text('/* Generated from the unchanged Northstar Python lesson. */\nexport const CONTENT = '+json.dumps(content,ensure_ascii=False,separators=(',',':'))+';\n')
    random_source=random.Random(731)
    outcomes=[]
    for _ in range(400):
        c=cbase(mandate=random_source.randrange(2),tracker=random_source.randrange(3),ownership=random_source.randrange(3),
                network_tenths=random_source.choice([0,977,986,1000,random_source.randrange(1001)]),
                citations=sorted(random_source.sample(range(8),random_source.randrange(1,9))))
        for field,options in case.BRIEF_OPTIONS.items():c[field]=random_source.choice(list(options))
        c['work_claim']=random_source.randrange(3)
        outcomes.append({'c':c,'capacity':logic.capacity(c),'product':logic.work_product(c),'findings':[asdict(x)|{'verdict':x.verdict} for x in logic.findings(c)],'consequences':logic.briefing_consequences(c),'brief':logic.brief_markdown(c)})
    for scope,route,mask in product(range(2),range(3),range(256)):
        c=cbase(scope=scope,mandate=int(route==1),tracker=2 if route==2 else 0,citations=[i for i in range(8) if mask&(1<<i)])
        outcomes.append({'c':c,'evidence':next(asdict(x)|{'verdict':x.verdict} for x in logic.findings(c) if x.title=='Evidence selection'),'consequences':logic.briefing_consequences(c)})
    order=[]
    fields={'inbox':list(range(6)),**{f'role:{i}':list(case.CATEGORIES) for i in range(6)},'mandate':list(case.MANDATES),'tracker':list(case.TRACKER_CHOICES),'ownership':list(case.OWNERSHIP_CHOICES),**{f:list(v) for f,v in case.BRIEF_OPTIONS.items()},'work_claim':[0,1,2]}
    for seed in (0,1,1234,2147483647,125489,987654321):
        for field,values in fields.items():
            shuffled=values[:];random.Random(f'{seed}:{field}').shuffle(shuffled);order.append({'seed':seed,'field':field,'input':values,'expected':shuffled})
    snapshots=[]
    for route in range(3):
        s=progress.defaults(1234);s=progress.navigate(s,1)
        for index,request in enumerate(case.REQUESTS):s=progress.edit_choice(s,'roles',request['category'],index)
        s=progress.check_roles(s);s=progress.commit(s,1)
        for field,value in [('mandate',int(route==1)),('tracker',2 if route==2 else 0),('ownership',0)]:s=progress.edit_choice(s,field,value)
        s=progress.check_commission(s);s=progress.commit(s,2);s=progress.commit(s,3)
        for field,value in cbase().items():
            if field not in ('roles','mandate','tracker','ownership'):s=progress.edit_choice(s,field,value)
        s=progress.submit_brief(s)
        snapshots.append({'state':s,'token':progress.encode(s),'view':2})
    (HERE/'tests/oracles.json').write_text(json.dumps({'outcomes':outcomes,'orders':order,'snapshots':snapshots,'rounding':[{'raw':str(v),'expected':round(v*10)} for v in (0,100,97.7,97.75,97.85,98.25,0.05,0.15,99.95)]},ensure_ascii=False,separators=(',',':'))+'\n')
    manifest={'source_files':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('board_app.py','northstar/board_case.py','northstar/board_logic.py','northstar/board_progress.py')},'screen_count':6,'finding_oracles':len(outcomes),'shuffle_oracles':len(order),'downloads_in_original':0,'app_owned_assets_in_original':0}
    (HERE/'tests/content-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':export()
