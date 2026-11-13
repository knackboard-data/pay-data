#!/usr/bin/env python3
"""add_micro1_row.py PAYDATA FEED.json JOB_ID FIELD DATE "captured note": add one micro1 role from a full public-feed
capture as a tracked row (sources.json, state.json, changelog.csv), the way Nov 2 rows were added. Idempotent."""
import csv, json, sys
sys.path.insert(0, '/workspace/kb-seo-notes/build'); import pt_fetch as F
D, feedp, jid, field, date, note = sys.argv[1:7]
feed = {x['job_id']: x for x in json.load(open(feedp))}; x = feed[jid]
title = ' '.join(x['job_name'].split()); pay = F.micro1_wording(x['ideal_hourly_rate'])
sid = 'micro1:' + jid; URL = 'https://www.micro1.ai/experts/opportunities'
src = json.load(open(D + '/sources.json'))
if not any(s['id'] == sid for s in src):
    src.append(dict(platform='micro1', kind='micro1', id=sid, job_id=jid, url=URL, title=title, field=field, key_requirements=''))
    open(D + '/sources.json', 'w').write(json.dumps(src, indent=1, ensure_ascii=False) + '\n')
st = json.load(open(D + '/state.json'))
if sid not in st:
    st[sid] = dict(platform='micro1', field=field, role_or_listing=title, listed_pay=pay, source_url=URL, last_checked=date,
                   key_requirements='', status='rechecked')
    json.dump(st, open(D + '/state.json', 'w'), indent=1, ensure_ascii=False)
    r = x['ideal_hourly_rate']
    ev = 'Row added %s from the micro1 public feed (%s; job_id %s, domain_slug %s, ideal_hourly_rate %s-%s, posted %s)' % (
        note.split(';')[0], note.split(';', 1)[1].strip(), jid[:8], x['domain_slug'], r['min'], r['max'], x['date_posted'][:10])
    with open(D + '/changelog.csv', 'a', newline='', encoding='utf-8') as f:
        csv.writer(f, lineterminator='\n').writerow([date, 'micro1', field, title, 'Not tracked', pay, URL, ev, 'yes'])
print(title, pay)
