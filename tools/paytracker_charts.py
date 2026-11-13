#!/usr/bin/env python3
"""Pay tracker charts: listed pay ranges by field, as posted. Rebuilt Nov 2, 2026 after the box restore.

Parse rule: every dollar figure in a row's listed pay counts toward both the low and the high, "up to"
figures included ("Up to $125+/hr" -> 125 and 125; "$60-$180 / hr" -> 60 and 180; "Pay: $50-70/h" -> 50
and 70). A trailing "+" is kept as the stated number. Only hourly wording is parsed; per-task pay and
unmatched wording are skipped and listed on the page.

History row (pay-tracker-history.csv): listed_low = min and listed_high = max over the field and platform's
parsed rows on that date; rows whose fetch failed keep their last listed value; listing_count = rows
parsed. Change-driven: a pair gets a new row only when low, high or count differs from its latest earlier
row. Earlier dates are kept; a rerun for the same date replaces that date's rows (an existing row whose
numbers are unchanged is kept verbatim, note included, so reruns are no-ops). The column is still called
sweep_date.

Usage:
  python3 paytracker_charts.py --repo R [--append-date YYYY-MM-DD] [--history FILE]
      (optionally append R/public/pay-tracker.csv to the history as of that date, then write
       R/public/pay-tracker-history.csv and the PT:CHARTS block of R/public/pay-tracker.html)
  python3 paytracker_charts.py --svg-dir DIR --history FILE   (standalone SVGs for the data mirror)
"""
import argparse, csv, datetime as dt, html, os, re, sys
from collections import defaultdict
from urllib.parse import urlparse

D = '/workspace/kb-seo-notes/paydata'
HIST = D + '/pay-tracker-history.csv'
HIST_COLS = ['sweep_date', 'field', 'platform', 'listed_low', 'listed_high', 'listing_count', 'source_note']
COLORS = {'DataAnnotation': '#3f6fb5', 'Handshake AI': '#c0602f', 'Mercor': '#2e8a5c', 'micro1': '#8a4fb0'}
SPARE = ['#b0457a', '#5f7f1f', '#1f7f8a', '#8a6d1f']

# ---------------- data ----------------
def load_csv(p):
    if not os.path.exists(p): return []
    with open(p, newline='', encoding='utf-8') as f: return list(csv.DictReader(f))

def write_csv(p, cols, rows):
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore', lineterminator='\n')
        w.writeheader(); w.writerows(rows)

def parse(pay):
    """(low, high) for hourly wording, else None."""
    if '$' not in pay or not re.search(r'/\s*h(?:r|our)?\b|per hour', pay): return None
    n = [int(x.replace(',', '')) for x in re.findall(r'\d[\d,]*', pay[pay.index('$'):])]
    return (min(n), max(n)) if n else None

def skip_reason(pay):
    if re.search(r'/\s*task|per task', pay): return 'per-task pay, not an hourly rate'
    return 'wording not parsed as an hourly figure'

def sort_platform(p): return p.lower()

def host(u):
    h = urlparse(u).netloc.lower()
    return h[4:] if h.startswith('www.') else h

def human(d): return dt.date.fromisoformat(d).strftime('%b %-d, %Y')

def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def sweep_rows(rows, date, all_rows=False):
    """History rows for `date` from tracker rows. all_rows: include rows not rechecked that day (their
    last listed value is kept); otherwise only rows whose last_checked is `date`."""
    g = defaultdict(list); skipped = defaultdict(int)
    for r in rows:
        if not all_rows and r.get('last_checked') != date: continue
        v = parse(r['listed_pay'])
        k = (r['field'], r['platform'])
        if v is None: skipped[k] += 1; continue
        g[k].append((v, r))
    out = []
    for (field, platform), items in g.items():
        n = len(items)
        stale = sum(1 for _, r in items if r.get('last_checked') != date)
        hosts = sorted({host(r['source_url']) for _, r in items})
        note = '%d hourly %s in pay-tracker.csv rechecked %s; source: %s' % (n, 'row' if n == 1 else 'rows', date, ' '.join(hosts))
        if stale: note += '; %d of them not rechecked that day (fetch failed), last listed value kept' % stale
        sk = skipped.get((field, platform), 0)
        if sk: note += '; %d per-task or unparsed %s skipped' % (sk, 'row' if sk == 1 else 'rows')
        out.append(dict(sweep_date=date, field=field, platform=platform,
                        listed_low=str(min(v[0] for v, _ in items)), listed_high=str(max(v[1] for v, _ in items)),
                        listing_count=str(n), source_note=note))
    return out

def hist_key(r): return (r['sweep_date'], r['field'].lower(), sort_platform(r['platform']))
def _vals(r): return (int(r['listed_low']), int(r['listed_high']), int(r['listing_count']))

def append_sweep(path, rows, date):
    """Add `date` rows to the history file for pairs whose figures changed (change-driven)."""
    hist = load_csv(path)
    old_today = {(r['field'], r['platform']): r for r in hist if r['sweep_date'] == date}
    earlier = [r for r in hist if r['sweep_date'] < date]
    later = [r for r in hist if r['sweep_date'] > date]
    latest = {}
    for r in sorted(earlier, key=hist_key): latest[(r['field'], r['platform'])] = r
    full = sweep_rows(rows, date, all_rows=True)
    new = []
    for r in full:
        k = (r['field'], r['platform'])
        if k in latest and _vals(latest[k]) == _vals(r): continue
        o = old_today.get(k)
        new.append(o if o is not None and _vals(o) == _vals(r) else r)
    hist = sorted(earlier + new + later, key=hist_key)
    write_csv(path, HIST_COLS, hist)
    return hist

def fields_of(hist):
    f = defaultdict(list)
    for r in hist: f[r['field']].append(r)
    return {k: sorted(v, key=hist_key) for k, v in sorted(f.items(), key=lambda kv: kv[0].lower())}

def skipped_rows(live):
    return [r for r in sorted(live, key=lambda r: (r['field'].lower(), r['platform'].lower(), r['role_or_listing'].lower()))
            if parse(r['listed_pay']) is None]

# ---------------- svg ----------------
def f1(x): return '%.1f' % x
def fx(x): return '%.1f' % round(x)   # text anchors sit on whole pixels

def axis_for(mx):
    for step in (10, 25, 50, 100, 250, 500, 1000):
        if -(-mx // step) <= 6: return step, -(-mx // step) * step
    return 1000, -(-mx // 1000) * 1000

def asof(rows):
    ds = sorted({r['sweep_date'] for r in rows})
    return ds[-1], ds[0]

def svg(field, rows, standalone=False):
    e = html.escape; sl = slug(field)
    dates = sorted({r['sweep_date'] for r in rows})
    plats = sorted({r['platform'] for r in rows}, key=sort_platform)
    spare = iter(SPARE)
    color = {p: COLORS.get(p) or next(spare) for p in plats}
    step, top = axis_for(max(int(r['listed_high']) for r in rows))
    k = 170 / top
    maxc = max(int(r['listing_count']) for r in rows)
    nd, np_ = len(dates), len(plats)
    single = nd == 1
    if single:
        sp = 304 / np_; w = 14.0; x2 = 350
    else:
        gw = np_ * 22 + 18.05; w = 9.9
        x2 = int(round(52 + (nd - 1) * gw + (np_ - 1) * 22 + w + 6))
    width = max(360, x2 + 10)
    rowsn = -(-np_ // 2)
    height = 366 + 18 * rowsn
    last, first = asof(rows)
    sub = 'As of %s' % human(last) if single else 'As of %s, history since %s' % (human(last), human(first))
    parts = []
    for d in dates:
        dr = sorted([r for r in rows if r['sweep_date'] == d], key=lambda r: sort_platform(r['platform']))
        parts.append('Sweep %s: ' % human(d) + '; '.join(
            '%s $%s to $%s per hour from %s %s' % (r['platform'], r['listed_low'], r['listed_high'], r['listing_count'],
                                                  'listing' if r['listing_count'] == '1' else 'listings') for r in dr))
    desc = ('Range chart of listed hourly pay as posted, low to high, for %s, platforms in alphabetical order, with the '
            'number of listings counted. %s.' % (field, '. '.join(parts)))
    style = ('max-width:%dpx;height:auto;color:#263b32;background:#fffdf6' % width) if standalone else 'max-width:560px;height:auto'
    o = ['<svg %sclass="pt-chart-svg" viewBox="0 0 %d %d" width="100%%" role="img" aria-labelledby="ptc-%s-title ptc-%s-desc" '
         'preserveAspectRatio="xMinYMin meet" font-family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif" font-size="12" '
         'style="%s">' % ('xmlns="http://www.w3.org/2000/svg" ' if standalone else '', width, height, sl, sl, style),
         '<title id="ptc-%s-title">%s: listed pay ranges, as posted</title>' % (sl, e(field)),
         '<desc id="ptc-%s-desc">%s</desc>' % (sl, e(desc)),
         '<text x="0" y="15" font-weight="700" font-size="13" fill="currentColor">Listed pay ranges, as posted ($/hr)</text>',
         '<text x="0" y="32" font-size="12" fill="currentColor" opacity=".8">%s</text>' % e(sub)]
    for v in range(0, top + 1, step):
        y = 220 - v * k
        o.append('<line x1="46" x2="%d" y1="%s" y2="%s" stroke="currentColor" stroke-opacity=".18"/>' % (x2, f1(y), f1(y)))
        o.append('<text x="40" y="%s" text-anchor="end" font-size="11" fill="currentColor" opacity=".8">$%d</text>' % (f1(y + 3.5), v))
    for g, d in enumerate(dates):
        by = {r['platform']: r for r in rows if r['sweep_date'] == d}
        for i, p in enumerate(plats):
            r = by.get(p)
            if r is None: continue
            x = 46 + i * sp + sp / 2 - 7 if single else 52 + g * gw + i * 22
            lo, hi, c = _vals(r)
            yh, yl = 220 - hi * k, 220 - lo * k
            y, h = yh, yl - yh
            if h < 4: y, h = (yh + yl) / 2 - 2, 4.0
            o.append('<rect x="%s" y="%s" width="%s" height="%s" rx="3" fill="%s"/>' % (f1(x), f1(y), f1(w), f1(h), color[p]))
            if single:
                lab = '$%d' % lo if lo == hi else '$%d-%d' % (lo, hi)
                o.append('<text x="%s" y="%s" text-anchor="middle" font-size="11" fill="currentColor">%s</text>' % (fx(x + w / 2), f1(y - 5), lab))
            ch = 54 * c / maxc
            o.append('<rect x="%s" y="%s" width="%s" height="%s" fill="%s" fill-opacity=".55"/>' % (f1(x), f1(326 - ch), f1(w), f1(ch), color[p]))
            o.append('<text x="%s" y="%s" text-anchor="middle" font-size="11" fill="currentColor">%d</text>' % (fx(x + w / 2), f1(326 - ch - 4), c))
        cx = 198.0 if single else 52 + g * gw + ((np_ - 1) * 22 + w) / 2
        o.append('<text x="%s" y="340" text-anchor="middle" font-size="11" fill="currentColor">%s</text>' % (fx(cx), human(d)))
    o.append('<line x1="46" x2="%d" y1="326" y2="326" stroke="currentColor" stroke-opacity=".4"/>' % x2)
    o.append('<text x="0" y="250" font-size="12" fill="currentColor" opacity=".8">Listings counted per platform</text>')
    for i, p in enumerate(plats):
        lx, ly = (i % 2) * 175, 353 + (i // 2) * 18
        o.append('<rect x="%d" y="%d" width="10" height="10" rx="2" fill="%s"/>' % (lx, ly, color[p]))
        o.append('<text x="%d" y="%d" font-size="12" fill="currentColor">%s</text>' % (lx + 15, ly + 9, e(p)))
    o.append('</svg>')
    return ''.join(o)

# ---------------- page block ----------------
def t(d, h=None): return '<time datetime="%s">%s</time>' % (d, h or human(d))

def section(field, rows):
    e = html.escape; sl = slug(field)
    last, first = asof(rows)
    label = 'As of %s.' % t(last) if last == first else 'As of %s, history since %s.' % (t(last), t(first))
    o = ['    <section class="pt-chart" id="chart-%s">' % sl,
         '      <h3>%s</h3>' % e(field),
         '      <p class="pt-chart-label">Listed pay ranges, as posted. %s</p>' % label,
         '      <div class="pt-chart-figure">%s</div>' % svg(field, rows),
         '      <div class="pt-chart-tablewrap"><table class="guide-table pt-chart-table" data-field="%s">' % e(field),
         '      <caption>%s: listed pay ranges, as posted, per sweep date (same numbers as the chart)</caption>' % e(field),
         '      <thead><tr><th scope="col">Sweep date</th><th scope="col">Platform</th><th scope="col">Listed low ($/hr)</th>'
         '<th scope="col">Listed high ($/hr)</th><th scope="col">Listings</th></tr></thead>',
         '      <tbody>']
    for r in rows:
        o.append('      <tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                 % (t(r['sweep_date']), e(r['platform']), r['listed_low'], r['listed_high'], r['listing_count']))
    o += ['      </tbody>', '      </table></div>', '    </section>']
    return o

def hist_line(hist):
    ds = sorted({r['sweep_date'] for r in hist})
    if len(ds) == 1:
        return 'The history starts %s, so there is one point for now. A new point is added on the day a listed figure changes.' % human(ds[0])
    return 'The history starts %s and has %d dated points so far, one for each day a listed figure changed.' % (human(ds[0]), len(ds))

HOW = ('    <p>How we turn wording into numbers: every dollar figure in a listing counts toward both its low and its high, '
       '&quot;up to&quot; figures included, so &quot;Up to $125+/hr&quot; counts as 125 for both and &quot;$60-$180 / hr&quot; '
       'as 60 and 180. A trailing &quot;+&quot; is kept as the stated number. Only hourly wording is charted.</p>')

def block(hist, skipped):
    o = ['    <!-- PT:CHARTS:START -->', '    <h2>Listed pay ranges by field, as posted</h2>',
         '    <p class="guide-note pt-charts-note"><strong>Listed pay ranges, as posted.</strong> %s Each chart shows, for each '
         'platform in alphabetical order, the lowest and highest hourly figure it listed in that field on each date shown, plus '
         'how many listings we counted. A platform appears on a later date only when its figures in that field changed that day. '
         'These are listed rates, not typical earnings or guaranteed income, and the charts do not rank platforms. '
         '<a href="/pay-tracker-history.csv" download>Download the chart data as a CSV file</a>.</p>' % hist_line(hist), HOW]
    for field, rows in fields_of(hist).items(): o += section(field, rows)
    if skipped:
        o.append('    <p class="guide-note pt-skipped"><strong>Rows left out of the charts:</strong> these rows are in the table '
                 'above but are not charted, because their wording is not an hourly figure we can parse honestly.</p>')
        o.append('    <ul class="pt-skipped-list">')
        for r in skipped:
            o.append('      <li>%s</li>' % html.escape('%s, %s, %s: "%s" (%s)' % (r['platform'], r['field'], r['role_or_listing'],
                                                                                    r['listed_pay'], skip_reason(r['listed_pay']))))
        o.append('    </ul>')
    o.append('    <!-- PT:CHARTS:END -->')
    return '\n'.join(o)

def write_page(page, hist, skipped):
    s = open(page, encoding='utf-8').read()
    n = re.sub(r'    <!-- PT:CHARTS:START -->.*?<!-- PT:CHARTS:END -->', lambda m: block(hist, skipped), s, count=1, flags=re.S)
    if '<!-- PT:CHARTS:START -->' not in s: raise SystemExit('no PT:CHARTS block in ' + page)
    if '\u2014' in n or '\u2013' in n: raise SystemExit('em or en dash in chart output')
    if n != s:
        with open(page, 'w', encoding='utf-8') as f: f.write(n)

def write_svgs(d, hist):
    os.makedirs(d, exist_ok=True)
    for field, rows in fields_of(hist).items():
        with open(os.path.join(d, slug(field) + '.svg'), 'w', encoding='utf-8') as f: f.write(svg(field, rows, standalone=True) + '\n')

def run_repo(repo, date=None, history=HIST):
    pub = os.path.join(repo, 'public')
    live = load_csv(os.path.join(pub, 'pay-tracker.csv'))
    if date: append_sweep(history, live, date)
    hist = load_csv(history)
    write_csv(os.path.join(pub, 'pay-tracker-history.csv'), HIST_COLS, hist)
    write_page(os.path.join(pub, 'pay-tracker.html'), hist, skipped_rows(live))
    print('history rows: %d, fields charted: %d' % (len(hist), len(fields_of(hist))))

if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--repo'); a.add_argument('--append-date'); a.add_argument('--history', default=HIST); a.add_argument('--svg-dir')
    a = a.parse_args()
    if a.svg_dir:
        write_svgs(a.svg_dir, load_csv(a.history))
    elif a.repo:
        run_repo(a.repo, a.append_date, a.history)
    else:
        sys.exit(__doc__)
