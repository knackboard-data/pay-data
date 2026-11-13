import csv,sys,re,json,time
sys.path.insert(0,'/workspace/kb-seo-notes/build')
import pt_fetch as F
rows=list(csv.DictReader(open('/workspace/kb-seo/public/pay-tracker.csv')))
out=[]
faq_da=None;faq_hs=None
for r in rows:
    if r['platform']=='micro1': continue
    u=r['source_url']
    try:
        if 'dataannotation.tech/faqs' in u:
            if faq_da is None: faq_da=F.text_of(F.get(u)[2])
            track=r['role_or_listing'].replace('FAQ: ','')
            m=re.search(re.escape(track)+r':\s*(Starting at \$[\d,]+-\$[\d,]+\+? per hour)',faq_da)
            got=m.group(1) if m else 'NOTFOUND'
        elif u.rstrip('/').endswith('joinhandshake.com/ai'):
            s=F.get(u)[2]; m=re.search(r'earn from (\$\d+/hr to \$\d+\+?/hr \(depending on the project\))',s)
            got='From '+m.group(1) if m else 'NOTFOUND'
        else:
            g=F.FETCHERS[r['platform']](u); got=g[1] if g else 'GONE'
    except Exception as e: got='ERR '+str(e)[:80]
    st='OK' if got==r['listed_pay'] else 'DIFF'
    out.append(dict(r,live=got,status=st,at=time.strftime('%Y-%m-%d %H:%M JST')))
    print(st,r['platform'],'|',r['role_or_listing'],'|',r['listed_pay'],'|',got,flush=True)
json.dump(out,open('/workspace/kb-seo-notes/build/payreport/recheck_20261103.json','w'),indent=1)
