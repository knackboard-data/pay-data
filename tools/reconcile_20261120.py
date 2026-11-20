# Reconcile paydata state/sources/changelog/history with main (PR #65 hand-added rows) before the Nov 20 refresh. Usage: reconcile_20261120.py PAYDATA REPO
import csv,json,re,sys,html
D,R=sys.argv[1:3]
main=list(csv.DictReader(open(R+'/public/pay-tracker.csv')))
st=json.load(open(D+'/state.json')); src=json.load(open(D+'/sources.json'))
ids={s['id'] for s in src}
feed={x['job_id']:x for x in json.load(open('/tmp/feed-2026-11-20.json'))}
M1={'Cardiac Electrophysiologist':'7a2d57b4','Cardiac Imaging Specialist':'e456304b','General Cardiologist':'1504ee4d','Heart Failure & Transplant Cardiologist':'fddfeff8','Hematologist':'4bf88f49','Hematology/Oncology Physician':'172b81f5','Interventional Cardiologist':'2605f5d4','Medical Oncologist':'868d0dba','Pediatric Hematology/Oncology Physician':'51a68d9c','Preventive Cardiologist':'61506be4'}
have={(v['platform'],v['source_url'],v['role_or_listing']) for v in st.values() if v['status']=='rechecked'}
for r in main:
    k=(r['platform'],r['source_url'],r['role_or_listing'])
    if k in have: continue
    p=r['platform']
    if p=='micro1':
        jid=[j for j in feed if j.startswith(M1[r['role_or_listing']])][0]; sid='micro1:'+jid
        s=dict(platform=p,kind='micro1',id=sid,job_id=jid,url=r['source_url'],title=r['role_or_listing'],field=r['field'],key_requirements='')
    else:
        slug=r['source_url'].rstrip('/').split('/')[-1]
        kind={'Mercor':'mercor','DataAnnotation':'dataannotation','Handshake AI':'handshake'}[p]
        sid=kind+':'+slug
        s=dict(platform=p,url=r['source_url'],title=r['role_or_listing'],field=r['field'],kind=kind,id=sid,key_requirements='')
    if sid not in ids: src.append(s); ids.add(sid)
    st[sid]=dict(platform=p,field=r['field'],role_or_listing=r['role_or_listing'],listed_pay=r['listed_pay'],source_url=r['source_url'],last_checked=r['last_checked'],key_requirements='',status='rechecked')
# rows main dropped (no longer listed, already in main changelog)
mk={(r['platform'],r['source_url'],r['role_or_listing']) for r in main}
for k,v in st.items():
    if v['status']=='rechecked' and (v['platform'],v['source_url'],v['role_or_listing']) not in mk: v['status']='no longer listed'; print('gone',v['role_or_listing'])
# carry last_checked/pay from main for shared rows
mm={(r['platform'],r['source_url'],r['role_or_listing']):r for r in main}
for v in st.values():
    r=mm.get((v['platform'],v['source_url'],v['role_or_listing']))
    if r and v['status']=='rechecked': v['listed_pay']=r['listed_pay']; v['last_checked']=r['last_checked']
json.dump(st,open(D+'/state.json','w'),indent=1,ensure_ascii=False); open(D+'/sources.json','w').write(json.dumps(src,indent=1,ensure_ascii=False)+'\n')
# changelog rows from main html
h=open(R+'/public/pay-tracker.html').read()
cl=list(csv.DictReader(open(D+'/changelog.csv'))); seen={(c['date_observed'],c['platform'],c['role_or_listing'],c['source_url']) for c in cl}
add=[]
for d,body,url in re.findall(r'<li><time datetime="(2026-11-1\d)">[^<]*</time>: (.*?), <a href="([^"]*)" rel="nofollow">source</a></li>',h):
    body=html.unescape(body); url=html.unescape(url)
    m=re.match(r'(micro1|Mercor|DataAnnotation|Handshake AI) (.*?): (added to the tracker, listed at (.*)|(.*), no longer listed)$',body)
    plat,role=m.group(1),m.group(2)
    if m.group(4): old,new='Not tracked',m.group(4)
    else: old,new=m.group(5),'No longer listed'
    if plat=='micro1':
        if old!='Not tracked' and not old.startswith('Pay:'): old='Pay: '+old
        if new!='No longer listed' and not new.startswith('Pay:'): new='Pay: '+new
    field=next((r['field'] for r in main if r['role_or_listing']==role and r['platform']==plat),'')
    if not field:
        field={'Consulting Specialist':'General','Finance Specialist':'Accounting and Finance','Brand & Creative Strategy Expert':'General','Physics Expert (PhD / Postdoc)':'Science and Research'}.get(role,'')
    if (d,plat,role,url) in seen: continue
    add.append(dict(date_observed=d,platform=plat,field=field,role_or_listing=role,old_pay=old,new_pay=new,source_url=url,evidence='Reconstructed Nov 20, 2026 from the live pay-tracker change log (PR #65, Nov 12 pass)',public='yes'))
print(len(add),'changelog rows added')
cols=['date_observed','platform','field','role_or_listing','old_pay','new_pay','source_url','evidence','public']
with open(D+'/changelog.csv','a',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n'); w.writerows(add)
import shutil; shutil.copy(R+'/public/pay-tracker-history.csv',D+'/pay-tracker-history.csv')
