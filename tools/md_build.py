#!/usr/bin/env python3
"""Knackboard Markdown build (rerunnable, idempotent). Rebuilt Nov 2, 2026 after the box restore.

Run from anywhere:  python3 /workspace/kb-seo-notes/build/md_build.py [/path/to/repo] [--check]
(default repo: /workspace/kb-seo; --check writes nothing and exits 1 if any output would change)

For every guide in public/guides/ (plus the guides index, the homepage, /about, /how-we-get-paid and
/pay-tracker) it:
  1. adds <link rel="alternate" type="text/markdown" href="...md"> after the canonical link (if missing),
  2. writes the .md twin from the page's visible article text (same figures, dates, sources,
     disclosure, quiz link; nothing that is not on the page),
and for the site:
  3. writes public/_headers: per .md file the Dualmark AEO headers (text/markdown; charset=utf-8,
     X-Markdown-Tokens = whitespace word count, X-Robots-Tag: noindex, Vary: Accept, nosniff,
     X-AEO-Version: 1.0) plus the HTML page as rel=canonical; per HTML page a Link rel="alternate"
     type="text/markdown" header (https://dualmark.dev/docs/spec/headers),
  4. regenerates the "## Guides" list of public/llms.txt (one line per guide, in guides-index order:
     H1 title, link to the .md version, meta description). Everything else in llms.txt is hand-written.
The homepage twin is /index.md and the guides index twin is /guides.md (/guides/index.md is an
identical copy for older links). Acceptance test: on a clean main checkout this is a no-op.
"""
import html, re, sys
from pathlib import Path
from bs4 import BeautifulSoup, Comment, NavigableString, Tag

args = [a for a in sys.argv[1:] if not a.startswith('--')]
CHECK = '--check' in sys.argv
REPO = Path(args[0] if args else '/workspace/kb-seo')
PUB = REPO / 'public'
SITE = 'https://knackboard.com'

# ---------------- inline ----------------
def absu(h):
    if h.startswith('/'): return SITE + h
    return h

def esc(t):
    return t.replace('_', '\\_')

def inline(n):
    if isinstance(n, Comment): return ''
    if isinstance(n, NavigableString): return esc(re.sub(r'\s+', ' ', str(n)))
    if n.name in ('script', 'style', 'svg', 'button', 'input', 'label') : return ''
    if n.name == 'br': return '  \n'
    inner = ''.join(inline(c) for c in n.children)
    if n.name in ('strong', 'b'):
        s = inner.strip()
        return ('**%s**' % s) if s else ''
    if n.name in ('em', 'i'):
        s = inner.strip()
        return ('*%s*' % s) if s else ''
    if n.name == 'a' and n.get('href'):
        return '[%s](%s)' % (inner.strip(), absu(n['href']))
    return inner

def para(n):
    return re.sub(r'[ \t]+', ' ', ''.join(inline(c) for c in n.children)).strip()

# ---------------- blocks ----------------
def table(t):
    rows = []
    for tr in t.find_all('tr'):
        rows.append([para(c).replace('|', '\\|') for c in tr.find_all(['th', 'td'])])
    if not rows: return []
    out = ['| ' + ' | '.join(rows[0]) + ' |', '|' + '|'.join('---' for _ in rows[0]) + '|']
    out += ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
    return ['\n'.join(out)]

def lst(n):
    items = []
    for i, li in enumerate(n.find_all('li', recursive=False), 1):
        mark = '%d. ' % i if n.name == 'ol' else '- '
        items.append(mark + para(li))
    return ['\n'.join(items)] if items else []

def blocks(n):
    out = []
    for c in n.children:
        if isinstance(c, Comment): continue
        if isinstance(c, NavigableString):
            if c.strip(): out.append(esc(re.sub(r'\s+', ' ', str(c)).strip()))
            continue
        out += block(c)
    return out

def block(c):
    name, cls = c.name, c.get('class', [])
    if name in ('nav', 'script', 'style', 'svg', 'caption', 'form', 'input', 'label', 'template', 'noscript'): return []
    if c.get('aria-hidden') == 'true' or c.get('hidden') is not None: return []
    if name == 'header':
        h1 = c.find('h1')
        lines = [para(p) for p in c.find_all('p')]
        return ['# ' + para(h1)] + (['  \n'.join(lines)] if lines else [])
    if name in ('h1', 'h2', 'h3', 'h4'):
        return ['#' * int(name[1]) + ' ' + para(c)]
    if name == 'button' or c.get('hidden') is not None: return []
    if name == 'p':
        s = para(c); return [s] if s else []
    if name in ('ul', 'ol'): return lst(c)
    if name == 'table': return table(c)
    if name == 'a' and 'back-link' in cls: return []
    if name == 'a':
        s = para(c); return ['[%s](%s)' % (s, absu(c['href']))] if s else []
    return blocks(c)

# ---------------- homepage ----------------
def quiz_link(a):
    # in-page quiz anchors (#quiz-panel) point at the homepage in the twin; the arrow is decoration
    return '[%s](%s/)' % (para(a).replace(' →', '').strip(), SITE)

def render_home(soup):
    main = soup.find('main')
    out = ['# ' + para(main.find('h1'))]
    agents = soup.find(class_='footer-agents')
    if agents: out.append(para(agents))
    for sec in main.find_all('section', recursive=False):
        cls = sec.get('class', [])
        if 'homepage-hero' in cls:
            for c in sec.find_all(['h2', 'p'], recursive=False):
                out += block(c)
        elif 'panel' in cls:
            # the quiz: each question as a heading with its hint; result screens are app UI, skipped
            for sc in sec.find_all('div', class_='screen'):
                qh = sc.find(class_='question-head')
                if not qh: continue
                label = qh.find(class_='step-label')
                out.append('## %s: %s' % (para(label), para(qh.find('h2'))))
                out += [para(p) for p in qh.find_all('p') if p is not label and para(p)]
                chips = sc.find_all('button', class_='super-chip')
                if chips: out.append('\n'.join('- ' + para(b) for b in chips))
        elif 'roles-strip' in cls:
            out.append('## ' + para(sec.find('h2')))
            seen, items = set(), []
            for rc in sec.find_all(class_='role-card'):  # the scroller repeats cards to loop
                k = tuple(para(rc.find(class_=x)) for x in ('role-title', 'role-platform', 'role-pay'))
                if k in seen: continue
                seen.add(k); items.append('- %s, %s: %s' % k)
            out.append('\n'.join(items))
            out.append(para(sec.find(class_='roles-note')))
            out.append(quiz_link(sec.find('a', class_='quiz-link')))
        elif 'how-it-works' in cls:
            out.append('## ' + para(sec.find('h2')))
            for sc in sec.find_all(class_='step-card'):
                out.append('### %s. %s' % (para(sc.find(class_='step-number')), para(sc.find('h3'))))
                out += [para(p) for p in sc.find_all('p')]
            out.append(quiz_link(sec.find('a', class_='quiz-link')))
        elif 'faq-section' in cls:
            out.append('## ' + para(sec.find('h2')))
            for d in sec.find_all('details'):
                out.append('### ' + para(d.find('summary')))
                out += [para(p) for p in d.find_all('p')]
            out.append(quiz_link(sec.find('a', class_='quiz-link')))
        else:
            out += blocks(sec)
    return '\n\n'.join(b for b in out if b.strip()) + '\n'

def render(path):
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    if path == PUB / 'index.html': return render_home(soup)
    root = soup.find('article') or soup.find('main') or soup.find(class_='content-page')
    return '\n\n'.join(b for b in blocks(root) if b.strip()) + '\n'

# ---------------- pages ----------------
def pages():
    P = []
    P.append(('index.html', 'index.md', SITE + '/', '/'))
    P.append(('guides/index.html', 'guides.md', SITE + '/guides/', '/guides/'))
    for f in sorted((PUB / 'guides').glob('*.html')):
        if f.name == 'index.html': continue
        slug = f.stem
        P.append(('guides/' + f.name, 'guides/%s.md' % slug, SITE + '/guides/' + slug, '/guides/' + slug))
    for name in ('about', 'how-we-get-paid', 'pay-tracker'):
        if (PUB / (name + '.html')).exists():
            P.append((name + '.html', name + '.md', SITE + '/' + name, '/' + name))
    return P

changed = []
def write(p, s):
    p = Path(p)
    old = p.read_text(encoding='utf-8') if p.exists() else None
    if old != s:
        changed.append(str(p.relative_to(REPO)))
        if not CHECK: p.write_text(s, encoding='utf-8')

# ---------------- html: alternate link and agent line (only added when missing) ----------------
AGENTS = ('For AI assistants: a plain index of every Knackboard guide is at <a href="/llms.txt">/llms.txt</a>, '
          'and this page is also available as <a href="%s">Markdown</a>.')

def patch_html(path, md_url, canon):
    s = path.read_text(encoding='utf-8'); o = s
    alt = '  <link rel="alternate" type="text/markdown" href="%s%s" />' % (SITE, md_url)
    if 'type="text/markdown"' not in s:
        s = re.sub(r'(  <link rel="canonical" href="[^"]*" />\n)', lambda m: m.group(1) + alt + '\n', s, count=1)
    if 'guide-agents' not in s and 'footer-agents' not in s:
        if '</header>' in s.split('<main', 1)[-1]:
            s = s.replace('    </header>', '      <p class="guide-updated guide-agents">%s</p>\n    </header>' % (AGENTS % md_url), 1)
        else:
            s = s.replace('  </footer>', '    <p class="footer-agents">For AI assistants: a plain index of every Knackboard guide is at <a href="/llms.txt">/llms.txt</a>.</p>\n  </footer>', 1)
    if s != o: write(path, s)

def patch_footer_only():
    # pages without a twin (privacy, terms, 404) still get the footer line
    for f in sorted(PUB.glob('*.html')):
        if f.name in ('index.html', 'about.html', 'how-we-get-paid.html', 'pay-tracker.html'): continue
        s = f.read_text(encoding='utf-8')
        if 'guide-agents' in s or 'footer-agents' in s or '</footer>' not in s: continue
        write(f, s.replace('  </footer>', '    <p class="footer-agents">For AI assistants: a plain index of every Knackboard guide is at <a href="/llms.txt">/llms.txt</a>.</p>\n  </footer>', 1))

# ---- _headers ----
HEAD = ['# Generated by kb-seo-notes/build/md_build.py (Dualmark AEO spec 1.0 headers). Markdown twins:',
        '# text/markdown with the HTML page as canonical and noindex, so search engines index the HTML.',
        '# HTML pages with a twin: Link rel="alternate" type="text/markdown".', '']
STATIC = ['/llms.txt', '  Content-Type: text/plain; charset=utf-8', '  X-Robots-Tag: noindex', '',
          '/pay-tracker.csv', '  Content-Type: text/csv; charset=utf-8', '  Link: <https://knackboard.com/pay-tracker>; rel="describedby"', '',
          '/pay-tracker-history.csv', '  Content-Type: text/csv; charset=utf-8', '  Link: <https://knackboard.com/pay-tracker>; rel="describedby"']

def md_rule(md_path, canon, tokens):
    return ['/' + md_path, '  Content-Type: text/markdown; charset=utf-8', '  Link: <%s>; rel="canonical"' % canon,
            '  X-Markdown-Tokens: %d' % tokens, '  X-Robots-Tag: noindex', '  Vary: Accept',
            '  X-Content-Type-Options: nosniff', '  X-AEO-Version: 1.0', '']

def build_headers(entries):
    out = list(HEAD); n = 0
    for h, m, canon, route, tokens in entries:
        out += md_rule(m, canon, tokens); n += 1
        if m == 'guides.md': out += md_rule('guides/index.md', canon, tokens); n += 1
        out += [route, '  Link: </%s>; rel="alternate"; type="text/markdown"' % m, '  Vary: Accept', '']; n += 1
    out += STATIC; n += 3
    assert n <= 100, 'Cloudflare allows 100 _headers rules, have %d' % n
    return '\n'.join(out) + '\n'

# ---- llms.txt ----
def meta(path):
    b = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    return b.h1.get_text(' ', strip=True), b.find('meta', attrs={'name': 'description'})['content']

# (label, link, page the description is read from, text after the description)
KEY = [('Quiz and homepage', 'index.md', 'index.html', ' (web page and quiz: https://knackboard.com/)'),
       ('Guides', 'guides.md', None, ''),
       ('About', 'about.md', 'about.html', ' (web page: https://knackboard.com/about)'),
       ('How we get paid', 'how-we-get-paid.md', 'how-we-get-paid.html', ' (web page: https://knackboard.com/how-we-get-paid)'),
       ('Pay tracker', 'pay-tracker.md', 'pay-tracker.html', ' (web page: https://knackboard.com/pay-tracker, data: https://knackboard.com/pay-tracker.csv,'
        ' chart history: https://knackboard.com/pay-tracker-history.csv, GitHub: https://github.com/knackboard-data/pay-data)'),
       ('Privacy', 'privacy', 'privacy.html', ''), ('Terms', 'terms', 'terms.html', '')]
GUIDES_LINE = 'every guide in one list, with a short answer to which guide fits your question (web page: https://knackboard.com/guides/)'

def guide_order():
    b = BeautifulSoup((PUB / 'guides/index.html').read_text(encoding='utf-8'), 'html.parser')
    seen = []
    for a in b.select('ul.guide-list a[href^="/guides/"]'):
        slug = a['href'].split('/guides/', 1)[1].strip('/')
        if slug and slug not in seen and (PUB / 'guides' / (slug + '.html')).exists(): seen.append(slug)
    rest = [f.stem for f in sorted((PUB / 'guides').glob('*.html')) if f.stem != 'index' and f.stem not in seen]
    return seen + rest

def build_llms():
    p = PUB / 'llms.txt'; s = p.read_text(encoding='utf-8')
    key = ['- [%s](%s/%s): %s%s' % (label, SITE, url, GUIDES_LINE if src is None else meta(PUB / src)[1], tail)
           for label, url, src, tail in KEY if src is None or (PUB / src).exists()]
    s = re.sub(r'(## Key pages\n\n)(?:- .*\n)+', lambda m: m.group(1) + '\n'.join(key) + '\n', s, count=1)
    g = []
    for slug in guide_order():
        t, d = meta(PUB / 'guides' / (slug + '.html'))
        g.append('- [%s](%s/guides/%s.md): %s' % (t, SITE, slug, d))
    s = re.sub(r'(## Guides\n\n(?:[^\n-].*\n\n)?)(?:- .*\n)+', lambda m: m.group(1) + '\n'.join(g) + '\n', s, count=1)
    write(p, s)

def main():
    entries = []
    for h, m, canon, route in pages():
        patch_html(PUB / h, '/' + m, canon)
        md = render(PUB / h)
        write(PUB / m, md)
        if m == 'guides.md': write(PUB / 'guides/index.md', md)
        entries.append((h, m, canon, route, len(md.split())))
    patch_footer_only()
    write(PUB / '_headers', build_headers(entries))
    build_llms()
    print('%d markdown pages written' % len(entries))
    if changed: print('changed:', *changed, sep='\n  ')
    if CHECK and changed: sys.exit(1)

if __name__ == '__main__':
    main()
