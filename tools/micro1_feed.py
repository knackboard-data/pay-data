#!/usr/bin/env python3
"""Capture micro1's public expert opportunities feed (no browser).

Same data the public page https://www.micro1.ai/experts/opportunities loads:
  POST https://prod-api.micro1.ai/api/v1/job/portal?page={n}&limit=50&keyword=
  body {"action":"get_all_jobs","filters":{"type":["EXPERT"]}}
Pages until every record in `total` is saved. Refuses a partial capture (a partial
feed would make dozens of roles look "no longer listed").

Usage: micro1_feed.py OUT.json
Output: JSON list of job records (job_id, job_name, domain_slug, ideal_hourly_rate, apply_url, ...).
"""
import json, sys, time, urllib.request

API = 'https://prod-api.micro1.ai/api/v1/job/portal?page=%d&limit=50&keyword='
BODY = json.dumps({'action': 'get_all_jobs', 'filters': {'type': ['EXPERT']}}).encode()
HDRS = {'Content-Type': 'application/json', 'Origin': 'https://www.micro1.ai',
        'Referer': 'https://www.micro1.ai/experts/opportunities', 'User-Agent': 'Mozilla/5.0 (knackboard pay tracker)'}

def page(n):
    for attempt in range(3):
        try:
            req = urllib.request.Request(API % n, data=BODY, headers=HDRS, method='POST')
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 2: raise
            time.sleep(3)

def capture():
    recs, total, n = {}, None, 1
    while True:
        d = page(n)
        total = d.get('total') if total is None else total
        rows = d.get('data') or []
        for x in rows: recs[x['job_id']] = x
        if not rows or len(recs) >= (total or 0) or n > 50: break
        n += 1
    if not total or len(recs) < total:
        raise SystemExit('partial micro1 capture: %d records of %s' % (len(recs), total))
    return list(recs.values()), total

if __name__ == '__main__':
    out = sys.argv[1]
    recs, total = capture()
    json.dump(recs, open(out, 'w'), indent=1)
    print('micro1 feed: %d of %d records at %s -> %s' % (len(recs), total, time.strftime('%Y-%m-%d %H:%M %Z'), out))
