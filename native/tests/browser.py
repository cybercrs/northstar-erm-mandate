"""Walk through the native student app at its complete /js/ project path."""
from __future__ import annotations
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import threading
import time
import traceback
from urllib.parse import parse_qs,urlsplit,urlencode

from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from northstar.board_progress import decode,SnapshotError,encode,defaults
from northstar.board_case import REQUESTS,CATEGORIES,MANDATES,TRACKER_CHOICES,OWNERSHIP_CHOICES,BRIEF_OPTIONS,WORK_CLAIMS,RECORDS
from northstar.board_logic import request_order,work_product

CHECKS=('Five fresh-context cold initializations and native request audit','All three complete routes with wrong answers and repeats','All reached pages strictly read-only and unchanged progress','Numeric drafts, rounding, old/native bookmarks and revision','Independent tabs/contexts and reset','Invalid progress, numeric drafts and future-view rejection','Keyboard, touch targets, desktop and narrow layouts','Final branding and exact Python snapshot validation')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist',type=Path,default=ROOT/'native/dist')
    parser.add_argument('--results',type=Path,default=ROOT/'native/review')
    parser.add_argument('--chromium',default='/usr/bin/chromium')
    args=parser.parse_args();args.results.mkdir(parents=True,exist_ok=True)
    fixture=tempfile.TemporaryDirectory(prefix='northstar-native-site-',dir='/tmp')
    site=Path(fixture.name);path=site/'northstar-erm-mandate/js';shutil.copytree(args.dist,path)
    requests=[]
    class Handler(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            requests.append(self.path)
            if self.path=='/favicon.ico':self.send_response(204);self.end_headers()
            else:super().do_GET()
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(site)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    origin=f'http://127.0.0.1:{server.server_port}';url=origin+'/northstar-erm-mandate/js/'
    results={'checks':[{'name':name,'status':'not-run'} for name in CHECKS], 'errors':[],'console_errors':[],'external_requests':[],'measurement_conditions':'Five fresh Chromium contexts, cache disabled via CDP, local loopback HTTP in saved Accounting Teaching Apps cloud environment; wall clock from navigation to ready+saved URL. No hosted-network, school-device or capacity measurement.'}
    active=0;bookmarks=[];variants=[]
    def passed(index):results['checks'][index]['status']='passed';print('PASSED:',CHECKS[index],flush=True)
    def state(page,view=None,predicate=lambda s:True):
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            query=parse_qs(urlsplit(page.url).query)
            try:saved=decode(query.get('progress',[''])[0])
            except SnapshotError:saved=None
            idle=page.locator('html').get_attribute('data-busy')=='false'
            if saved is not None and idle and (view is None or query.get('view')==[str(view)]) and predicate(saved):
                expect(page.get_by_text(f'Page {int(query["view"][0])+1} of 6',exact=True)).to_be_visible();return saved
            page.wait_for_timeout(20)
        raise AssertionError('Expected restorable native state: '+page.url)
    def loaded(page):expect(page.locator('html')).to_have_attribute('data-ready','true',timeout=15000);state(page)
    def click(page,label):page.get_by_role('button',name=label,exact=True).click()
    def disabled(page,label):expect(page.get_by_role('button',name=label,exact=True,include_hidden=True)).to_be_disabled()
    def radio(page,field,value,options=None):
        options=options or BRIEF_OPTIONS[field]
        page.get_by_role('radio',name=options[value],exact=True).check();state(page,predicate=lambda s:s['c'][field]==value)
    def readonly(page):
        expect(page.get_by_text('Review only. Return to your current page to continue the activity.',exact=True)).to_be_visible()
        assert page.locator('#lesson input,#lesson select').count()==0
        for label in ('Check the role map','Review the commission plan','Submit briefing for feedback','Revise briefing (optional)','Start a new case','Open the CAE inbox'):
            assert page.locator('#lesson').get_by_role('button',name=label,exact=True).count()==0,label
        disabled(page,'Start over')
    def layout(page,name):
        boxes=[page.get_by_role('button',name=label,exact=True).bounding_box() for label in ('Back','Forward')]
        assert all(box and box['width']==44 and box['height']==44 for box in boxes),boxes
        assert abs(boxes[0]['y']-boxes[1]['y'])<1
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        results.setdefault('navigation_layout',{})[name]=boxes
    def save_variant(page,name):
        text=page.locator('body').inner_text();title=page.title()
        assert title=='Northstar Cold Chain | The ERM Mandate'
        import re
        assert not re.search(r'\b(?:pilot|preview|prototype)\b|\btest (?:app|version|site)\b',text,re.I),(name,text)
        variants.append({'name':name,'title':title,'body_sha256':__import__('hashlib').sha256(text.encode()).hexdigest()})
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=args.chromium if Path(args.chromium).exists() else None,headless=True,proxy={'server':'http://127.0.0.1:9','bypass':'127.0.0.1,localhost'})
        context=browser.new_context(viewport={'width':1280,'height':900})
        def watch(page):
            page.on('pageerror',lambda error:results['errors'].append(str(error)))
            page.on('console',lambda message:results['console_errors'].append(message.text) if message.type=='error' else None)
            page.on('request',lambda request:results['external_requests'].append(request.url) if request.url.startswith('http') and not request.url.startswith(origin) else None)
            return page
        page=watch(context.new_page())
        try:
            cold=[]
            for i in range(5):
                cold_context=browser.new_context(viewport={'width':1280,'height':900});cold_page=watch(cold_context.new_page())
                session=cold_context.new_cdp_session(cold_page);session.send('Network.enable');session.send('Network.setCacheDisabled',{'cacheDisabled':True})
                started=time.perf_counter();cold_page.goto(url);loaded(cold_page);cold.append(round((time.perf_counter()-started)*1000,2));cold_context.close()
            results['cold_initialization_ms']={'samples':cold,'median':statistics.median(cold),'min':min(cold),'max':max(cold)}
            page.goto(url);loaded(page);layout(page,'desktop');page.screenshot(path=str(args.results/'assignment-desktop.png'),full_page=True);passed(0)
            active=1
            for route in (0,1,2):
                if route:page.goto(url);loaded(page)
                save_variant(page,f'assignment-route-{route}');disabled(page,'Back');disabled(page,'Forward')
                click(page,'Open the CAE inbox');saved=state(page,1);disabled(page,'Commission the advisory work')
                assert '97.7' not in page.locator('#lesson').inner_text()
                for id_ in request_order(saved['seed']):page.locator(f'#role-{id_}').select_option(str((REQUESTS[id_]['category']+1)%3));state(page,predicate=lambda s:s['c']['roles'][id_]==(REQUESTS[id_]['category']+1)%3)
                click(page,'Check the role map');wrong=state(page,1,predicate=lambda s:s['roles_checked']);expect(page.get_by_text('Incorrect',exact=True)).to_have_count(6)
                click(page,'Check the role map');assert state(page,1)==wrong;save_variant(page,f'wrong-inbox-{route}')
                for id_,request in enumerate(REQUESTS):page.locator(f'#role-{id_}').select_option(str(request['category']));state(page,predicate=lambda s:s['c']['roles'][id_]==request['category'])
                disabled(page,'Commission the advisory work');click(page,'Check the role map');state(page,1,predicate=lambda s:s['roles_checked'])
                click(page,'Commission the advisory work');state(page,2);disabled(page,'Forward')
                mandate=int(route==1);tracker=2 if route==2 else (1 if route==1 else 0)
                radio(page,'mandate',mandate,{i:f"{v['name']} — {v['hours']} hours" for i,v in MANDATES.items()});radio(page,'tracker',tracker,TRACKER_CHOICES);radio(page,'ownership',0,OWNERSHIP_CHOICES)
                draft=state(page,2);disabled(page,'Open the board packet');assert '97.7' not in page.locator('#lesson').inner_text()
                assert 'Manager-validated workshop summary' not in page.locator('#lesson').inner_text();save_variant(page,f'commission-draft-{route}')
                order=page.locator('fieldset label.option').all_text_contents();click(page,'Back');assert state(page,1)==draft;readonly(page)
                click(page,'Forward');assert state(page,2)==draft;page.reload();loaded(page);assert state(page,2)==draft;expect(page.locator('fieldset label.option')).to_have_text(order)
                click(page,'Review the commission plan');checked=state(page,2,predicate=lambda s:s['commission_checked']);click(page,'Review the commission plan');assert state(page,2)==checked
                if route==2:expect(page.get_by_text('50',exact=True)).to_be_visible()
                save_variant(page,f'commission-reviewed-{route}');click(page,'Open the board packet');state(page,3)
                for id_ in range(8):
                    record=page.locator(f'details[data-record="{id_}"]');record.locator('summary').click();expect(record.locator('.detail-body')).to_be_visible()
                    if id_==2:expect(record.get_by_text('97.7% for the complete network',exact=False)).to_be_visible()
                save_variant(page,f'packet-{route}');page.screenshot(path=str(args.results/f'packet-route-{route}.png'),full_page=True)
                click(page,'Prepare the board briefing');state(page,4);disabled(page,'Submit briefing for feedback')
                page.get_by_text('Open case notebook',exact=True).click();expect(page.get_by_text('Case notebook',exact=True)).to_be_visible()
                number=page.locator('#network-result');number.fill('97.');draft=state(page,4,predicate=lambda s:s['c']['network_tenths']==-1)
                bookmark=page.url;page.reload();loaded(page);assert state(page,4)==draft;expect(page.locator('#network-result')).to_have_value('97.')
                number=page.locator('#network-result');number.fill('97.75');state(page,predicate=lambda s:s['c']['network_tenths']==978);number.fill('98.6');state(page,predicate=lambda s:s['c']['network_tenths']==986)
                for field,value in dict(headline=0,continuity=0,work_claim=2,communication=1,authority=1,scope=0,provider=3).items():radio(page,field,value,WORK_CLAIMS[route] if field=='work_claim' else None)
                page.locator('#citation-0').check();draft=state(page,4,predicate=lambda s:s['c']['citations']==[0])
                click(page,'Back');assert state(page,3)==draft;readonly(page);review_bookmark=page.url;page.reload();loaded(page);assert state(page,3)==draft
                click(page,'Forward');assert state(page,4)==draft;expect(page.locator('#network-result')).to_have_value('98.6')
                save_variant(page,f'brief-draft-{route}');click(page,'Submit briefing for feedback');wrong=state(page,5);assert wrong['first_brief']['network_tenths']==986
                assert page.get_by_text('Incorrect',exact=True).count()>=5;save_variant(page,f'wrong-feedback-{route}')
                for target in range(4,-1,-1):click(page,'Back');assert state(page,target)==wrong;readonly(page);save_variant(page,f'review-{route}-{target}')
                for target in range(1,6):click(page,'Forward');assert state(page,target)==wrong
                disabled(page,'Forward');click(page,'Revise briefing (optional)');revision=state(page,4);assert not revision['brief_submitted'] and revision['first_brief']==wrong['first_brief']
                page.reload();loaded(page);assert state(page,4)==revision;page.locator('#network-result').fill('97.7');state(page,predicate=lambda s:s['c']['network_tenths']==977)
                for field,value in dict(headline=1,continuity=1,work_claim=0,communication=0,authority=0,scope=0,provider=0).items():radio(page,field,value,WORK_CLAIMS[route] if field=='work_claim' else None)
                for id_ in (1,2,3,6,7):page.locator(f'#citation-{id_}').check();state(page,predicate=lambda s:id_ in s['c']['citations'])
                click(page,'Submit briefing for feedback');final=state(page,5);assert final['first_brief']==wrong['first_brief'];save_variant(page,f'corrected-feedback-{route}')
                expect(page.get_by_text('Changes since your first submission:',exact=False)).to_be_visible()
                page.screenshot(path=str(args.results/f'feedback-route-{route}.png'),full_page=True);bookmarks.append({'state':final,'url':page.url});
            passed(1);passed(2);passed(3)
            active=4;last=bookmarks[-1];fresh=watch(context.new_page());fresh.goto(url);loaded(fresh);new=state(fresh,0);assert new['c']['roles']==[-1]*6 and new['seed']!=last['state']['seed'];fresh.close()
            other_context=browser.new_context();other=watch(other_context.new_page());other.goto(last['url']);loaded(other);assert state(other,5)==last['state'];other_context.close()
            click(page,'Start a new case');reset=state(page,0);assert reset['seed']!=last['state']['seed'];assert reset['first_brief'] is None;page.reload();loaded(page);assert state(page,0)==reset;passed(4)
            active=5
            for query in ('progress=invalid!&view=999','progress=a&progress=b&view=5',urlencode({'progress':encode(defaults(4)),'view':'5'})):
                page.goto(url+'?'+query);loaded(page);assert state(page,0)['c']['roles']==[-1]*6;disabled(page,'Forward')
            click(page,'Open the CAE inbox');first=state(page,1);page.goto(page.url.replace('view=1','view=999'));loaded(page);assert state(page,1)==first;disabled(page,'Forward');passed(5)
            active=6
            page.set_viewport_size({'width':390,'height':844});layout(page,'narrow');save_variant(page,'narrow-inbox');page.screenshot(path=str(args.results/'inbox-narrow.png'),full_page=True)
            page.get_by_role('button',name='Back',exact=True).focus();assert page.get_by_role('button',name='Back',exact=True).evaluate('e=>e.matches(":focus-visible")');assert page.get_by_role('button',name='Back',exact=True).evaluate('e=>getComputedStyle(e).outlineWidth')=='2px'
            page.keyboard.press('Enter');state(page,0);readonly(page);page.get_by_role('button',name='Forward',exact=True).focus();page.keyboard.press('Enter');assert state(page,1)==first
            page.goto(last['url']);loaded(page);state(page,5);layout(page,'narrow-feedback');page.screenshot(path=str(args.results/'feedback-narrow.png'),full_page=True)
            click(page,'Back');state(page,4);readonly(page);page.get_by_role('button',name='Back',exact=True).focus();page.keyboard.press('Tab');expect(page.get_by_role('button',name='Forward',exact=True)).to_be_focused()
            page.keyboard.press('Enter');assert state(page,5)==last['state'];passed(6)
            active=7
            oracles=json.loads((ROOT/'native/tests/oracles.json').read_text())
            from copy import deepcopy
            from itertools import product
            source_state=oracles['snapshots'][0]['state']
            for owner,scope,provider in product(range(3),range(2),range(4)):
                submitted=deepcopy(source_state);submitted['c'].update(ownership=owner,scope=scope,provider=provider)
                submitted['first_brief']={field:deepcopy(submitted['c'][field]) for field in submitted['first_brief']}
                page.goto(url+'?'+urlencode({'progress':encode(submitted),'view':5}));loaded(page);assert state(page,5)==submitted
                save_variant(page,f'ownership-provider-{owner}-{scope}-{provider}')
                if provider==0 and ((owner==1 and scope==0) or (owner==2 and scope==1)):
                    expect(page.get_by_text('Self-review unresolved',exact=False)).to_be_visible()
            for item in oracles['snapshots']:
                page.goto(url+'?'+urlencode({'progress':item['token'],'view':item['view']})+'#case');loaded(page);assert state(page,2)==item['state'];readonly(page);assert urlsplit(page.url).fragment=='case'
                expect(page.get_by_role('button',name='Revise briefing (optional)',exact=True)).to_have_count(0)
                save_variant(page,'old-bookmark-route-'+str(item['state']['c']['tracker']))
            assert not results['errors'],results['errors'];assert not results['console_errors'],results['console_errors'];assert not results['external_requests'],results['external_requests']
            assert all(not any(fragment in path for fragment in ('.wasm','.whl','pyodide','stlite','_stcore','node_modules')) for path in requests),requests
            assert all(decode(parse_qs(urlsplit(item['url']).query)['progress'][0])==item['state'] for item in bookmarks)
            results['audited_variants']=variants;results['native_bookmark_states']=[item['state'] for item in bookmarks];passed(7)
        except Exception:
            results['checks'][active].update(status='failed',error=traceback.format_exc());results['body_on_failure']=page.locator('body').inner_text();page.screenshot(path=str(args.results/'failure.png'),full_page=True)
        browser.close()
    server.shutdown();fixture.cleanup();results['static_requests']=sorted(set(requests))
    manifest=json.loads((args.dist/'manifest.json').read_text());results['application_bytes']=manifest['application_bytes'];results['served_files_bytes']=sum(p.stat().st_size for p in args.dist.iterdir() if p.is_file())
    (args.results/'browser-results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({k:v for k,v in results.items() if k not in ('body_on_failure','audited_variants','static_requests','native_bookmark_states')},indent=2),flush=True)
    return 1 if any(check['status']!='passed' for check in results['checks']) else 0


if __name__=='__main__':raise SystemExit(main())
