#!/usr/bin/env python3
"""Pay tracker page fetchers (GET only). Rebuilt Nov 2, 2026 after the box restore.
Each platform fetcher takes a public role URL and returns (title, listed_pay) in the platform's own wording,
or None when the role is no longer listed (HTTP 404/410, or a Mercor closed-listing page with no listing shown).
Any other problem raises, and paytracker_refresh.py keeps the last listed value (a failed fetch is not a change).
  DataAnnotation  https://www.dataannotation.tech/job-board/<slug>   h1 + rail "Hourly rate up to $125+ / hour" -> "Up to $125+/hr"
  Handshake AI    https://joinhandshake.com/ai/opportunities/<slug>  h1 + chips "Up to $125/hr", "Depending on the project"
                                                                     -> "Up to $125/hr, depending on the project"
  Mercor          https://work.mercor.com/jobs/<list_id>/<slug>      h1[data-test=listing-description-title] + rate h3 "$60-$120 / hr"
  micro1          only the public listing https://www.micro1.ai/experts/opportunities, via micro1_capture.py
                  (its job/portal feed); ideal_hourly_rate {min, max} -> "Pay: $min-max/h" or "Pay: $v/h"
"""
import json, re, subprocess, time, urllib.error, urllib.parse, urllib.request
from bs4 import BeautifulSoup

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

class Gone(Exception):
    pass

_host_fail = {}  # host -> consecutive network failures; after 4 in a row the host is skipped for this run (rows carried over)

def get(url, tries=3):
    """GET a public page. Returns (status, final_url, text). 404/410 raise Gone."""
    host = urllib.parse.urlsplit(url).netloc
    if _host_fail.get(host, 0) >= 4: raise RuntimeError('fetch skipped: %s unreachable this run' % host)
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml', 'Accept-Language': 'en-US,en;q=0.9'})
            with urllib.request.urlopen(req, timeout=20) as r:
                out = r.status, r.geturl(), r.read().decode('utf-8', 'replace')
            _host_fail[host] = 0
            return out
        except urllib.error.HTTPError as e:
            if e.code in (404, 410): raise Gone('HTTP %d' % e.code)
            last = e
        except Exception as e:
            last = e
        time.sleep(3 * (i + 1))
    _host_fail[host] = _host_fail.get(host, 0) + 1
    raise RuntimeError('fetch failed: %s' % last)

def text_of(s):
    soup = BeautifulSoup(s, 'html.parser')
    for t in soup(['script', 'style', 'noscript']): t.decompose()
    return re.sub(r'\s+', ' ', soup.get_text(' ')).strip()

def _h1(s, **attrs):
    h = BeautifulSoup(s, 'html.parser').find('h1', attrs=attrs or None)
    if not h: raise RuntimeError('no h1')
    return re.sub(r'\s+', ' ', h.get_text(' ')).strip()

def micro1_wording(rate):
    if isinstance(rate, str): rate = json.loads(rate.replace("'", '"'))
    lo, hi = int(rate['min']), int(rate['max'])
    return 'Pay: $%d/h' % lo if lo == hi else 'Pay: $%d-%d/h' % (lo, hi)

def dataannotation(url):
    try: st, fin, s = get(url)
    except Gone: return None
    if '/job-board/' not in fin: return None  # redirected to the board: role removed
    t = text_of(s)
    m = re.search(r'Hourly rate up to\s*\$([\d,]+\+?)\s*/\s*hour', t)
    if not m: raise RuntimeError('DataAnnotation rate not found')
    return _h1(s), 'Up to $%s/hr' % m.group(1)

def handshake(url):
    try: st, fin, s = get(url)
    except Gone: return None
    t = text_of(s)
    m = re.search(r'(Up to \$[\d,]+\+?/hr)\s*,?\s*(Depending on the project)?', t)
    if not m: raise RuntimeError('Handshake rate not found')
    return _h1(s), m.group(1) + (', depending on the project' if m.group(2) else '')

def mercor(url):
    try: st, fin, s = get(url)
    except Gone: return None
    soup = BeautifulSoup(s, 'html.parser')
    # A closed listing either shows only the "<title> is no longer accepting applications" banner (gone), or
    # Mercor shows a replacement listing on the same URL, which is tracked as displayed (as on Oct 30, 2026).
    # So the row is gone only when no listing rate is shown.
    pay = None
    for h3 in soup.find_all('h3'):
        x = re.sub(r'\s+', ' ', h3.get_text(' ')).strip()
        if re.fullmatch(r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?\s*/\s*[a-z]+', x): pay = x; break
    if not pay:
        if 'is no longer accepting applications' in text_of(s): return None
        raise RuntimeError('Mercor rate not found')
    return _h1(s, **{'data-test': 'listing-description-title'}), pay

def micro1_feed(out_json):
    """Render https://www.micro1.ai/experts/opportunities and save the public job/portal feed."""
    subprocess.run(['/workspace/.pw/bin/python', '/workspace/kb-seo-notes/build/micro1_capture.py', out_json], check=True, timeout=600)
    return json.load(open(out_json))

FETCHERS = {'Handshake AI': handshake, 'DataAnnotation': dataannotation, 'Mercor': mercor}

if __name__ == '__main__':
    import sys
    for u in sys.argv[1:]:
        k = 'DataAnnotation' if 'dataannotation' in u else 'Mercor' if 'mercor' in u else 'Handshake AI'
        print(u, FETCHERS[k](u))
