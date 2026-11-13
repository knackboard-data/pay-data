#!/usr/bin/env python3
"""Sync the public data mirror (github.com/knackboard-data/pay-data). Rebuilt Nov 2, 2026 after the box restore.

Writes into the mirror clone (default /workspace/kb-seo-notes/pay-data-repo):
  pay-tracker.csv, pay-tracker-history.csv  copied from paydata/ (same bytes as public/ on the site)
  changelog.csv                              public rows of paydata/changelog.csv, file order, first 7 columns
                                             (evidence and the public flag are internal and never published)
  charts/<field>.svg                         standalone charts (paytracker_charts.write_svgs); stale SVGs removed
  README.md                                  regenerated from the data
It never commits or pushes; the caller reviews `git -C <mirror> diff` and pushes separately.

Usage: python3 paydata_repo_build.py [MIRROR_DIR] [--src PAYDATA_DIR]
"""
import argparse, csv, datetime as dt, io, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paytracker_charts as PC

D = '/workspace/kb-seo-notes/paydata'
PAY_DATA_REPO = '/workspace/kb-seo-notes/pay-data-repo'
CL_PUBLIC_COLS = ['date_observed', 'platform', 'field', 'role_or_listing', 'old_pay', 'new_pay', 'source_url']

def long_date(d): return dt.date.fromisoformat(d).strftime('%B %-d, %Y')

def and_list(xs): return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ', and ' + xs[-1]

def hist_line(hist):
    ds = sorted({r['sweep_date'] for r in hist})
    if len(ds) == 1:
        return 'The history starts %s, so there is one point for now. A new point is added on the day a listed figure changes.' % long_date(ds[0])
    return 'The history starts %s and has %d dated points so far, one for each day a listed figure changed.' % (long_date(ds[0]), len(ds))

TAIL = '''## Column dictionary

### pay-tracker.csv

| Column | Meaning |
|---|---|
| `platform` | Platform that posted the listing |
| `field` | Field grouping used by Knackboard |
| `role_or_listing` | Role or listing title as posted (long dashes replaced with hyphens) |
| `listed_pay` | Listed pay in the platform's own wording |
| `source_url` | Public page the figure was copied from |
| `last_checked` | Date (YYYY-MM-DD) the row was last rechecked against its source |

### pay-tracker-history.csv

| Column | Meaning |
|---|---|
| `sweep_date` | Date (YYYY-MM-DD) the change was seen |
| `field` | Field grouping |
| `platform` | Platform |
| `listed_low` | Lowest listed hourly figure, US dollars, across that platform's parsed rows in the field that day |
| `listed_high` | Highest listed hourly figure, US dollars, across the same rows |
| `listing_count` | Number of rows parsed for that sweep date, field, and platform |
| `source_note` | Which rows and source sites the figures come from, and any rows skipped |

### changelog.csv

| Column | Meaning |
|---|---|
| `date_observed` | Date (YYYY-MM-DD) we noticed the change |
| `platform`, `field`, `role_or_listing` | Which listing changed |
| `old_pay`, `new_pay` | Listed pay before and after, as posted ("No longer listed" when a role left the source) |
| `source_url` | Public page for the listing |

## Sources

- DataAnnotation: role pages on https://www.dataannotation.tech/job-board and the FAQ at https://www.dataannotation.tech/faqs
- Handshake AI: role pages under https://joinhandshake.com/ai/opportunities/ and the FAQ at https://joinhandshake.com/ai/
- Mercor: job listings on https://work.mercor.com/
- micro1: only the public listing at https://www.micro1.ai/experts/opportunities

Referral bonuses are never counted as pay.

## Disclosure

Knackboard earns referral fees from these platforms. The figures here come from each platform's own pages and are not affected by those fees.

## License

The data (the CSV files and charts) is licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Please credit "Knackboard pay tracker, https://knackboard.com/pay-tracker".
'''

def readme(live, hist):
    plats = sorted({r['platform'] for r in live}, key=str.lower)
    o = ['# Remote expert pay data (listed rates)', '',
         "Listed hourly pay for remote expert roles on %s, by field, in each platform's own wording, with the source page and "
         'the date each row was last checked. Maintained by Knackboard. The same data is published at '
         'https://knackboard.com/pay-tracker.' % and_list(plats), '',
         '**Listed rates as posted, not typical earnings or guaranteed income.** Each platform decides who qualifies, which '
         'projects are open, how many hours are offered, and final pay. Follow the source link for the current listing.', '',
         'Last checked: %s. %s' % (long_date(max(r['last_checked'] for r in live)), hist_line(hist)), '',
         '## Files', '',
         '- `pay-tracker.csv`: one row per listing, as posted.',
         '- `pay-tracker-history.csv`: one row per date, field, and platform, added only on the day the listed figures for that '
         'pair changed (earlier dates kept), used for the charts.',
         '- `changelog.csv`: listed figures we saw change, dated by the day we noticed, plus rows added to the tracker '
         '(old_pay "Not tracked").',
         '- `charts/*.svg`: one chart per field, generated from `pay-tracker-history.csv`.', '',
         '## Charts: listed pay ranges, as posted', '',
         'Each chart shows, for each platform in alphabetical order, the lowest and highest hourly figure it listed in that field '
         'on each date shown, and how many listings were counted. A platform appears on a later date only when its figures in '
         'that field changed that day. Platforms are not ranked.', '']
    for field, rows in PC.fields_of(hist).items():
        o += ['### ' + field, '', '![%s: listed pay ranges, as posted](charts/%s.svg)' % (field, PC.slug(field)), '',
              '| Sweep date | Platform | Listed low ($/hr) | Listed high ($/hr) | Listings |', '|---|---|---|---|---|']
        o += ['| %s | %s | %s | %s | %s |' % (r['sweep_date'], r['platform'], r['listed_low'], r['listed_high'], r['listing_count']) for r in rows]
        o.append('')
    o += ['## How listed pay becomes numbers', '',
          'Every dollar figure in a listing counts toward both its low and its high, "up to" figures included. "Up to $125+/hr" '
          'counts as 125 for both, and "$60-$180 / hr" counts as 60 and 180. A trailing "+" is kept as the stated number. Only '
          'hourly wording is charted. For one sweep date, field, and platform, `listed_low` is the lowest figure and `listed_high` '
          'the highest figure across the rows listed that day (a row whose recheck failed keeps its last listed value).', '']
    sk = PC.skipped_rows(live)
    if sk:
        o += ['Rows left out of the charts (still in `pay-tracker.csv`):', '']
        o += ['- %s, %s, %s: "%s" (%s)' % (r['platform'], r['field'], r['role_or_listing'], r['listed_pay'], PC.skip_reason(r['listed_pay'])) for r in sk]
        o.append('')
    return '\n'.join(o) + '\n' + TAIL

def write_if_changed(p, s, changed):
    old = open(p, encoding='utf-8').read() if os.path.exists(p) else None
    if old != s:
        with open(p, 'w', encoding='utf-8') as f: f.write(s)
        changed.append(os.path.basename(p))

def build(repo=PAY_DATA_REPO, src=D):
    changed = []
    for name in ('pay-tracker.csv', 'pay-tracker-history.csv'):
        s = open(os.path.join(src, name), encoding='utf-8').read()
        write_if_changed(os.path.join(repo, name), s, changed)
    cl = [r for r in PC.load_csv(os.path.join(src, 'changelog.csv')) if (r.get('public') or 'yes') == 'yes']
    b = io.StringIO(); w = csv.DictWriter(b, CL_PUBLIC_COLS, extrasaction='ignore', lineterminator='\n'); w.writeheader(); w.writerows(cl)
    write_if_changed(os.path.join(repo, 'changelog.csv'), b.getvalue(), changed)
    live = PC.load_csv(os.path.join(src, 'pay-tracker.csv'))
    hist = PC.load_csv(os.path.join(src, 'pay-tracker-history.csv'))
    charts = os.path.join(repo, 'charts'); os.makedirs(charts, exist_ok=True)
    want = {PC.slug(f) + '.svg' for f in PC.fields_of(hist)}
    for f in os.listdir(charts):
        if f.endswith('.svg') and f not in want: os.remove(os.path.join(charts, f)); changed.append('charts/' + f + ' (removed)')
    for field, rows in PC.fields_of(hist).items():
        write_if_changed(os.path.join(charts, PC.slug(field) + '.svg'), PC.svg(field, rows, standalone=True) + '\n', changed)
    write_if_changed(os.path.join(repo, 'README.md'), readme(live, hist), changed)
    print('pay-data mirror: %s' % (', '.join(changed) if changed else 'no changes'))
    return changed

if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('repo', nargs='?', default=PAY_DATA_REPO); a.add_argument('--src', default=D)
    a = a.parse_args(); build(a.repo, a.src)
