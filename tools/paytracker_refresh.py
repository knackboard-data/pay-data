#!/usr/bin/env python3
"""Knackboard pay tracker refresh. Rebuilt Nov 2, 2026 after the box restore (header, fetch_row, render_table and
the output tail recovered verbatim from earlier transcripts; the recheck loop rewritten to reproduce the data on main).
Rechecks every source in /workspace/kb-seo-notes/paydata/sources.json live, updates last_checked only for
rows it actually rechecked, appends to changelog.csv only when a listed figure really changed, and regenerates:
  paydata/state.json                 last known value per row (the memory between runs)
  paydata/paydata-<date>.csv         internal table (adds pay_type, key_requirements, verified_today)
  paydata/pay-tracker.csv            public CSV (same columns as the page table)
  <repo>/public/pay-tracker.csv      when --repo is given
  <repo>/public/pay-tracker.html     table, change log, dates, and Dataset JSON-LD between PT markers
  paydata/pay-tracker-history.csv    chart history, change-driven (paytracker_charts.append_sweep)
  <repo>/public/pay-tracker-history.csv and the inline SVG charts + tables (paytracker_charts.py)
  pay-data-repo/                     CSVs, charts/*.svg and README for the public data repo, when the folder exists
                                     (paydata_repo_build.py; never committed or pushed from here)
Usage: python3 paytracker_refresh.py [--repo /workspace/kb-seo] [--date YYYY-MM-DD] [--no-fetch]
                                     [--paydata DIR] [--mirror DIR]
  --no-fetch   recheck nothing: every row keeps its last value and date (regenerates outputs from state.json;
               on an up-to-date main this must be a no-op diff, which is the rebuild's acceptance test)
  --paydata / --mirror  point at copies for testing, so the real paydata and mirror are untouched
Rules: micro1 pay comes only from the public listing https://www.micro1.ai/experts/opportunities.
Referral bonuses are never pay. No em dashes anywhere in output (platform titles are normalized).
"""
import argparse, csv, datetime as dt, html, io, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pt_fetch as F
import paytracker_charts as PC
D = '/workspace/kb-seo-notes/paydata'
PAY_DATA_REPO = '/workspace/kb-seo-notes/pay-data-repo'
PUBLIC_COLS = ['platform', 'field', 'role_or_listing', 'listed_pay', 'source_url', 'last_checked']
INTERNAL_COLS = PUBLIC_COLS + ['pay_type', 'key_requirements', 'verified_today']
CL_COLS = ['date_observed', 'platform', 'field', 'role_or_listing', 'old_pay', 'new_pay', 'source_url', 'evidence', 'public']
MICRO1_URL = 'https://www.micro1.ai/experts/opportunities'

def clean(s):
    return re.sub(r'\s+', ' ', (s or '').replace('\u2014', '-').replace('\u2013', '-')).strip()

def pay_type(p):
    if p.startswith('Up to'): return 'up to'
    if p.startswith('Starting at'): return 'starting at'
    if re.search(r'/\s*task', p): return 'per task'
    if re.search(r'\$[\d,]+\+?\s*(?:-|to)\s*\$?[\d,]+', p): return 'hourly range'
    return 'hourly'

def fetch_row(src, feed):
    k = src['kind']
    if k == 'micro1':
        x = feed.get(src['job_id']) if feed is not None else None
        if feed is None: raise RuntimeError('micro1 feed not captured')
        if x is None: return None  # no longer listed
        if not x.get('ideal_hourly_rate'): raise RuntimeError('not an hourly listing')
        return clean(x['job_name']), F.micro1_wording(x['ideal_hourly_rate'])
    if k == 'da_faq':
        st, fin, s = F.get(src['url']); t = F.text_of(s)
        m = re.search(re.escape(src['track']) + r':\s*(Starting at \$[\d,]+-\$[\d,]+\+? per hour)', t)
        if not m: raise RuntimeError('track not found on FAQ')
        return src['title'], m.group(1)
    if k == 'hs_faq':
        st, fin, s = F.get(src['url'])
        m = re.search(r'earn from (\$\d+/hr to \$\d+\+?/hr \(depending on the project\))', s)
        if not m: raise RuntimeError('FAQ range not found')
        return src['title'], 'From ' + m.group(1)
    got = F.FETCHERS[src['platform']](src['url'])
    if got is None: return None
    title, pay = got
    return clean(title), clean(pay)

def load_csv(p):
    return list(csv.DictReader(open(p, encoding='utf-8'))) if os.path.exists(p) else []

def sort_key(r):
    return (r['field'].lower(), r['platform'].lower(), r['role_or_listing'].lower())

def write_csv(path, cols, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore', lineterminator='\n'); w.writeheader(); w.writerows(rows)

def human(d):
    return dt.date.fromisoformat(d).strftime('%b %-d, %Y')

def render_table(rows):
    out = ['<table class="guide-table pay-tracker-table">',
           '      <caption>Listed pay by field and platform. Each row links to its source and shows the date we last checked it.</caption>',
           '      <thead><tr><th scope="col">Field</th><th scope="col">Platform</th><th scope="col">Role or listing</th><th scope="col">Listed pay</th><th scope="col">Last checked</th></tr></thead>',
           '      <tbody>']
    e = html.escape
    for r in rows:
        out.append('        <tr><td>%s</td><td>%s</td><td><a href="%s" rel="nofollow">%s</a></td><td>%s</td><td><time datetime="%s">%s</time></td></tr>' % (
            e(r['field']), e(r['platform']), e(r['source_url']), e(r['role_or_listing']), e(r['listed_pay']), r['last_checked'], human(r['last_checked'])))
    out += ['      </tbody>', '    </table>']
    return '\n'.join(out)

def strip_pay(p):
    return re.sub(r'^Pay: ', '', p)

def change_text(c, pub):
    old, new = c['old_pay'], c['new_pay']
    if old == 'Not tracked': return 'added to the tracker, listed at %s' % strip_pay(new)
    if new == 'No longer listed': return '%s, no longer listed' % strip_pay(old)
    if old == 'No longer listed':
        gone = [g['date_observed'] for g in pub if g['new_pay'] == 'No longer listed' and g['source_url'] == c['source_url']
                and g['role_or_listing'] == c['role_or_listing'] and g['date_observed'] < c['date_observed']]
        return 'listed again at %s' % strip_pay(new) + (' (no longer listed on %s)' % human(max(gone)) if gone else '')
    return 'was %s, now %s' % (strip_pay(old), strip_pay(new))

def render_changelog(entries):
    """Newest date first; within a date by platform, then role, descending (recovered rule; ties keep file order)."""
    e = html.escape
    pub = [c for c in entries if (c.get('public') or 'yes') == 'yes']
    if not pub: return '<p>No listed figure has changed since we started tracking.</p>'
    order = sorted(pub, key=lambda c: (c['date_observed'], c['platform'], c['role_or_listing']), reverse=True)
    li = ['<ul class="pay-tracker-changes">']
    for c in order:
        li.append('      <li><time datetime="%s">%s</time>: %s %s: %s, <a href="%s" rel="nofollow">source</a></li>' % (
            c['date_observed'], human(c['date_observed']), e(c['platform']), e(c['role_or_listing']), e(change_text(c, pub)), e(c['source_url'])))
    li.append('    </ul>')
    return '\n'.join(li)

def replace_block(s, name, inner):
    """Replace the content of the single element carrying data-pt="NAME" (div or span; no nesting of the same tag)."""
    m = re.search(r'(<(div|span)\b[^>]*\bdata-pt="%s"[^>]*>)' % name, s)
    if not m: raise SystemExit('data-pt="%s" block not found' % name)
    tag, start = m.group(2), m.end()
    depth, pos = 1, start
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % tag, s[start:]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            end = start + t.start(); break
    else: raise SystemExit('data-pt="%s" block not closed' % name)
    return s[:start] + inner + s[end:]

def today_jst():
    return (dt.datetime.utcnow() + dt.timedelta(hours=9)).date().isoformat()

def main():
    global D
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo'); ap.add_argument('--date'); ap.add_argument('--no-fetch', action='store_true')
    ap.add_argument('--paydata', default=D); ap.add_argument('--mirror', default=PAY_DATA_REPO)
    a = ap.parse_args()
    D = a.paydata
    SOURCES, STATE, CHANGELOG, HIST = D + '/sources.json', D + '/state.json', D + '/changelog.csv', D + '/pay-tracker-history.csv'
    today = a.date or today_jst()
    sources = json.load(open(SOURCES, encoding='utf-8'))
    state = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
    report = dict(rechecked=0, carried=0, changed=0, gone=0, failed=[])
    feed = None
    if not a.no_fetch and any(s['kind'] == 'micro1' for s in sources):
        out = D + '/micro1_public_feed_%s-%sjst.json' % (today, (dt.datetime.utcnow() + dt.timedelta(hours=9)).strftime('%H%M'))
        try: feed = {x['job_id']: x for x in F.micro1_feed(out)}
        except Exception as ex: report['failed'].append('micro1 feed: %s' % ex)  # every micro1 row is carried over
    changes = []
    def log(src, prev, old, new, title):
        ev = 'paytracker_refresh.py live check %s' % today + (' (previous check %s)' % prev['last_checked'] if prev else '')
        changes.append(dict(date_observed=today, platform=src['platform'], field=src['field'], role_or_listing=title,
                            old_pay=old, new_pay=new, source_url=src['url'], evidence=ev, public='yes'))
    for src in sources:
        prev = state.get(src['id'])
        if a.no_fetch:
            report['carried'] += 1; continue
        try:
            got = fetch_row(src, feed)
        except Exception as ex:
            report['failed'].append('%s: %s' % (src['id'], ex)); report['carried'] += 1; continue
        if got is None:
            if prev and prev['status'] != 'no longer listed':
                log(src, prev, prev['listed_pay'], 'No longer listed', prev['role_or_listing'])
                prev['status'] = 'no longer listed'; report['gone'] += 1
            continue
        title, pay = got
        if '\u2014' in title + pay: raise SystemExit('em dash in fetched text: %s' % src['id'])
        if prev is None: log(src, None, 'Not tracked', pay, title)
        elif prev['status'] == 'no longer listed': log(src, prev, 'No longer listed', pay, title)
        elif prev['listed_pay'] != pay: log(src, prev, prev['listed_pay'], pay, title)
        if prev is not None and prev['status'] == 'rechecked' and prev['listed_pay'] != pay: report['changed'] += 1
        state[src['id']] = dict(platform=src['platform'], field=src['field'], role_or_listing=title, listed_pay=pay,
                                source_url=src['url'], last_checked=today, key_requirements=src.get('key_requirements', ''),
                                status='rechecked')
        report['rechecked'] += 1
    live = sorted([v for v in state.values() if v['status'] == 'rechecked'], key=sort_key)
    if True:  # --no-fetch writes every output too: all rows carried over, so a no-op on up-to-date data
        with open(STATE, 'w', encoding='utf-8') as f: json.dump(state, f, indent=1, ensure_ascii=False)
        if changes:
            new_file = not os.path.exists(CHANGELOG)
            with open(CHANGELOG, 'a', newline='', encoding='utf-8') as f:
                w = csv.DictWriter(f, fieldnames=CL_COLS, lineterminator='\n')
                if new_file: w.writeheader()
                w.writerows(changes)
        internal = [dict(r, pay_type=pay_type(r['listed_pay']), verified_today='yes' if r['last_checked'] == today else 'no') for r in live]
        write_csv(D + '/paydata-%s.csv' % today, INTERNAL_COLS, internal)
        write_csv(D + '/pay-tracker.csv', PUBLIC_COLS, live)
        swept = PC.append_sweep(HIST, live, today)
    hist = PC.load_csv(HIST)
    if os.path.isdir(a.mirror):  # local pay-data repo folder (never pushed from here)
        import paydata_repo_build
        paydata_repo_build.build(a.mirror, D)
    if a.repo:
        write_csv(a.repo + '/public/pay-tracker.csv', PUBLIC_COLS, live)
        p = a.repo + '/public/pay-tracker.html'
        s = open(p, encoding='utf-8').read()
        newest = max(r['last_checked'] for r in live)
        s = replace_block(s, 'TABLE', '\n    ' + render_table(live) + '\n    ')
        s = replace_block(s, 'CHANGES', '\n    ' + render_changelog(load_csv(CHANGELOG)) + '\n    ')
        s = replace_block(s, 'COUNT', str(len(live)))
        s = replace_block(s, 'UPDATED', '<time datetime="%s">%s</time>' % (newest, dt.date.fromisoformat(newest).strftime('%B %-d, %Y')))
        s = re.sub(r'("dateModified": ")[\d-]+(")', r'\g<1>%s\2' % newest, s)
        s = re.sub(r'(<meta property="article:modified_time" content=")[\d-]+(")', r'\g<1>%s\2' % newest, s)
        if '\u2014' in s: raise SystemExit('em dash in page output')
        open(p, 'w', encoding='utf-8').write(s)
        PC.write_csv(a.repo + '/public/pay-tracker-history.csv', PC.HIST_COLS, hist)
        PC.write_page(p, hist, PC.skipped_rows(live))  # inline SVG charts + tables between PT:CHARTS markers
        import subprocess  # keep the Markdown twin, llms.txt and _headers in step (md_build.py is idempotent)
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'md_build.py'), a.repo], check=True)
    print(json.dumps(dict(rows=len(live), history_rows_today=len(swept), rechecked=report['rechecked'], carried_over=report['carried'], changed=report['changed'], gone=report['gone'], failed=report['failed']), indent=1, ensure_ascii=False))

if __name__ == '__main__':
    main()
