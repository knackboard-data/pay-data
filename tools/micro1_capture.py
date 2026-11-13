#!/usr/bin/env python3
# Rebuilt Nov 2, 2026 verbatim from the recovered transcript (recovered/msg0538.txt). Run with /workspace/.pw/bin/python.
# Usage: micro1_capture.py OUT.json
# Capture micro1's public opportunities feed (https://www.micro1.ai/experts/opportunities,
# data from prod-api.micro1.ai/api/v1/job/portal) by rendering the public page headlessly.
import json,sys,time
from playwright.sync_api import sync_playwright
out=sys.argv[1]
recs={}
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1280,'height':1000})
    def on(r):
        if 'job/portal' in r.url:
            try:
                for x in r.json().get('data',[]): recs[x['job_id']]=x
            except Exception as e: print('err',e)
    pg.on('response',on)
    pg.goto('https://www.micro1.ai/experts/opportunities',wait_until='domcontentloaded',timeout=90000); pg.wait_for_timeout(8000)
    import re
    def found():
        m=re.findall(r'(\d+) roles? found',pg.inner_text('body'))
        return int(m[0]) if m else None
    prev=-1; stable=0
    for i in range(300):
        pg.mouse.wheel(0,30000); pg.wait_for_timeout(1200)
        n=pg.locator('a[href*="jobs.micro1.ai/post/"]').count()
        tot=found()
        if tot and len(recs)>=tot and n>=tot: break
        stable = stable+1 if n==prev else 0
        if stable>=15: break  # about 18 s with no new cards
        prev=n
    tot=found(); print('found',tot)
    print('rendered cards',n,'records',len(recs),'at',time.strftime('%Y-%m-%d %H:%M %Z'))
    b.close()
# a partial capture would look like dozens of roles "no longer listed": refuse it
if not tot or len(recs)<tot:
    raise SystemExit('partial micro1 capture: %d records of %s roles found' % (len(recs),tot))
json.dump(list(recs.values()),open(out,'w'),indent=1)
