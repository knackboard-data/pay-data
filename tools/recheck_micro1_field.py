#!/usr/bin/env python3
"""recheck_micro1_field.py PAYDATA FEED.json FIELD DATE: recheck every tracked micro1 row in FIELD against a full,
saved public-feed capture using paytracker_refresh.fetch_row, and set last_checked=DATE when the wording matches.
Refuses (no write) on any mismatch or missing role, so changes still go through a real refresh run."""
import json, sys
sys.path.insert(0, '/workspace/kb-seo-notes/build'); import paytracker_refresh as R
D, feedp, field, date = sys.argv[1:5]
feed = {x['job_id']: x for x in json.load(open(feedp))}
st = json.load(open(D + '/state.json')); n = 0
for src in json.load(open(D + '/sources.json')):
    prev = st.get(src['id'])
    if src['kind'] != 'micro1' or src['field'] != field or not prev or prev['status'] != 'rechecked': continue
    got = R.fetch_row(src, feed)
    if got != (prev['role_or_listing'], prev['listed_pay']): raise SystemExit('mismatch %s: %s vs %s' % (src['id'], got, prev))
    prev['last_checked'] = date; n += 1
json.dump(st, open(D + '/state.json', 'w'), indent=1, ensure_ascii=False)
print('rechecked', n, 'micro1 rows in', field)
