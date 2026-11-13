# livecheck.py <sha> <base>: cache-busted byte check of every served file changed base..sha, plus changed X-Markdown-Tokens headers
import subprocess,sys,time,urllib.request,urllib.error,re,datetime
S,base=sys.argv[1],sys.argv[2]; R='/workspace/kb-seo'; B='https://knackboard.com'
g=lambda *a: subprocess.check_output(['git','-C',R,*a])
pairs=[]
for f in g('diff','--name-only',base,S,'--','public').decode().split():
    p=f[7:]
    if p in ('_headers','_redirects'): continue
    pairs.append(('/'+p[:-10] if p.endswith('index.html') else '/'+p[:-5] if p.endswith('.html') else '/'+p, p))
def toks(ref):
    d={};cur=None
    for line in g('show',ref+':public/_headers').decode().split('\n'):
        if line and not line.startswith(' '): cur=line.strip()
        m=re.match(r'\s+X-Markdown-Tokens: (\d+)',line)
        if m: d[cur]=m.group(1)
    return d
new,old=toks(S),toks(base); hp=[k for k in new if old.get(k)!=new[k]]
# redirect rules added base..S in public/_redirects: expect the status and Location
rd=[l[1:].split() for l in g('diff','-U0',base,S,'--','public/_redirects').decode().split('\n') if l.startswith('+') and not l.startswith('+++') and l[1:].strip() and not l[1:].startswith('#')]
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**k): return None
nr=urllib.request.build_opener(NoRedir)
def rget(u):
    try:
        r=nr.open(urllib.request.Request(u,headers={'User-Agent':'kb-livecheck','Cache-Control':'no-cache','Accept':'*/*'}),timeout=20); return r.status,r.headers.get('Location')
    except urllib.error.HTTPError as e: return e.code,e.headers.get('Location')
def get(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'kb-livecheck','Cache-Control':'no-cache','Accept':'*/*'}),timeout=20) as r: return r.status,r.read(),r.headers
for t in range(1,21):
    cb=str(time.time_ns()); out=[]; ok=True
    for u,p in pairs:
        try: st,body,_=get(f'{B}{u}?cb={cb}')
        except Exception as e: st,body=str(e),b''
        good= st==200 and body==g('show',f'{S}:public/{p}'); ok&=good; out.append(('PASS' if good else 'FAIL')+f' {u} ({st})')
    for h in hp:
        try: v=get(f'{B}{h}?cb={cb}')[2].get('X-Markdown-Tokens')
        except Exception as e: v=str(e)
        good= v==new[h]; ok&=good; out.append(('PASS' if good else 'FAIL')+f' header {h} X-Markdown-Tokens={v} (want {new[h]})')
    for r in rd:
        src,dst,code=r[0],r[1],r[2] if len(r)>2 else '302'
        try: st,loc=rget(f'{B}{src}?cb={cb}')
        except Exception as e: st,loc=str(e),None
        good= str(st)==code and loc is not None and loc.split('?')[0].replace(B,'')==dst; ok&=good; out.append(('PASS' if good else 'FAIL')+f' redirect {src} -> {loc} ({st}, want {code} {dst})')
    print(f'attempt {t} {datetime.datetime.now():%H:%M:%S} JST ALL={int(ok)} ({len(pairs)} files, {len(hp)} headers, {len(rd)} redirects)',flush=True)
    if ok: print('\n'.join(out)); sys.exit(0)
    print('\n'.join(o for o in out if o.startswith('FAIL')),flush=True); time.sleep(30)
sys.exit(1)
