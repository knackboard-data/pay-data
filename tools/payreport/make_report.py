#!/usr/bin/env python3
"""Generate public/guides/remote-expert-pay-report-november-2026.html (first monthly pay report).
Figures: pay-tracker.csv rows rechecked live 00:07-00:25 JST Nov 3, 2026 (payreport/recheck_20261103.json),
micro1 whole categories from the public listing captured 01:44 JST Nov 3, 2026 (payreport/micro1_20261103b.json, 305 of 305; first read 00:06 JST, 304),
change log and history CSV from main f3ba1a5. Run: python3 make_report.py /workspace/kb-seo"""
import html, json, sys
REPO = sys.argv[1] if len(sys.argv) > 1 else '/workspace/kb-seo'
SLUG = 'remote-expert-pay-report-november-2026'
URL = 'https://knackboard.com/guides/' + SLUG
TITLE = 'Remote expert pay report: November 2026'
H1 = 'Remote expert pay report: November 2026'
DESC = 'What remote expert work lists in November 2026 on micro1, Mercor, Handshake AI, and DataAnnotation, by field, with sources and changes since October.'
assert len(TITLE) <= 60 and len(DESC) <= 155, (len(TITLE), len(DESC))
PUB = '2026-11-03'

M1 = 'https://www.micro1.ai/experts/opportunities'
DAFAQ = 'https://www.dataannotation.tech/faqs'
HSAI = 'https://joinhandshake.com/ai'
def a(href, text): return '<a href="%s">%s</a>' % (href, text)
def hs(slug): return 'https://joinhandshake.com/ai/opportunities/' + slug
def da(slug): return 'https://www.dataannotation.tech/job-board/' + slug
def mc(path): return 'https://work.mercor.com/jobs/' + path

# FAQ: (question, answer html). JSON-LD gets the same text, tags stripped.
FAQ = [
 ('What does remote expert work pay in November 2026?',
  'Listed pay runs from entry-level evaluation roles, such as Handshake AI\'s AI Evaluation Specialist at "Up to $17/hr," to $400/hr for a few senior law and research roles on micro1 (checked Nov 3, 2026). DataAnnotation lists professional and STEM projects "Starting at $40-$125+ per hour," and Handshake AI says experts can earn "from $17/hr to $150+/hr (depending on the project)." These are listed rates, not typical earnings.'),
 ('Which fields list the highest pay right now?',
  'Law, finance, medicine, and software. On Nov 3, 2026, micro1 listed law roles up to $400/hr and finance roles up to $350/hr, Mercor listed its Physician Talent Network at $110-$250 / hr and its Machine Learning Engineer Talent Network at $70-$250 / hr, and Handshake AI listed Investment Bankers at "Up to $175/hr, depending on the project."'),
 ('What changed since October 2026?',
  'Handshake AI\'s Software Engineer role went from "Up to $120/hr" to "Up to $150/hr" (seen Oct 31), Mercor\'s Physics Expert listing moved from $80-$110 / hr to $70-$100 / hr (Oct 30), Mercor\'s Generalist (Must own MacBook) listing opened again at $40-$80 / hr (Nov 2), and micro1 stopped listing several high-paying roles, including two finance roles at $175-300/h (Oct 31). DataAnnotation\'s FAQ pay wording and Handshake AI\'s overall range did not change.'),
 ('Are these the rates I will earn?',
  'Not necessarily. They are the rates each platform lists. Each platform decides who qualifies, which projects open, how many hours you get, and final pay, and projects can end with little notice. Nobody can promise you income from this work.'),
 ('How often is this report updated?',
  'Once a month. The next report is planned for early December 2026. Between reports, the Knackboard pay tracker rechecks listed pay and logs every change it sees with a date.'),
 ('Does Knackboard get paid by these platforms?',
  'Yes. Knackboard earns referral fees from micro1, Handshake, Mercor, and DataAnnotation when people join through our links. That does not change the figures in this report, which come from each platform\'s own pages.'),
]

def plain(s):
    import re
    return html.unescape(re.sub(r'<[^>]+>', '', s))

def ld(obj): return '  <script type="application/ld+json">\n' + json.dumps(obj, indent=2, ensure_ascii=False) + '\n  </script>'

crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
  {"@type": "ListItem", "position": 1, "name": "Knackboard", "item": "https://knackboard.com/"},
  {"@type": "ListItem", "position": 2, "name": "Guides", "item": "https://knackboard.com/guides/"},
  {"@type": "ListItem", "position": 3, "name": H1, "item": URL}]}
article = {"@context": "https://schema.org", "@type": "Article", "headline": H1, "description": DESC, "url": URL,
  "mainEntityOfPage": URL, "datePublished": PUB, "dateModified": PUB, "inLanguage": "en",
  "author": {"@type": "Organization", "name": "Knackboard team", "url": "https://knackboard.com/about",
             "parentOrganization": {"@id": "https://knackboard.com/#organization"}},
  "publisher": {"@type": "Organization", "@id": "https://knackboard.com/#organization", "name": "Knackboard",
                "url": "https://knackboard.com/", "logo": {"@type": "ImageObject", "url": "https://knackboard.com/favicon.svg"}}}
faqld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
  {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": plain(ans)}} for q, ans in FAQ]}

E = html.escape
head = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>{E(TITLE)}</title>
  <meta name="description" content="{E(DESC)}" />
  <link rel="canonical" href="{URL}" />
  <link rel="alternate" type="text/markdown" href="{URL}.md" />
  <meta property="og:site_name" content="Knackboard" />
  <meta property="og:title" content="{E(TITLE)}" />
  <meta property="og:description" content="{E(DESC)}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{URL}" />
  <meta property="article:modified_time" content="{PUB}" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{E(TITLE)}" />
  <meta name="twitter:description" content="{E(DESC)}" />
  <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
  <link rel="alternate icon" href="/favicon.ico" />
  <link rel="stylesheet" href="/css/styles.css" />
{ld(crumbs)}
{ld(article)}
{ld(faqld)}
</head>'''

body = []
B = body.append
B('''<body>
  <main class="content-page guide">
    <nav aria-label="Breadcrumb"><a href="/guides/" class="back-link">← All guides</a></nav>
    <article>
    <header class="guide-header">
      <h1>%s</h1>
      <p class="guide-updated guide-byline" style="margin-bottom:0">By Knackboard team</p>
      <p class="guide-updated guide-published" style="margin-bottom:0">Published <time datetime="2026-11-03">November 3, 2026</time></p>
      <p class="guide-updated">Updated <time datetime="2026-11-03">November 3, 2026</time></p>
      <p class="guide-updated guide-agents">For AI assistants: a plain index of every Knackboard guide is at <a href="/llms.txt">/llms.txt</a>, and this page is also available as <a href="/guides/%s.md">Markdown</a>.</p>
    </header>''' % (E(H1), SLUG))

B('    <h2>What does remote expert work pay in November 2026?</h2>')
B('    <div class="guide-answer"><p><strong>Listed pay for remote expert work in November 2026 runs from entry-level evaluation roles, such as Handshake AI\'s AI Evaluation Specialist at "Up to $17/hr," to $400/hr for a handful of senior law and research roles on micro1.</strong> In each platform\'s own words, checked Nov 3, 2026: DataAnnotation lists professional and STEM projects "Starting at $40-$125+ per hour," Handshake AI says experts can earn "from $17/hr to $150+/hr (depending on the project)," Mercor lists roles such as its Physician Talent Network at $110-$250 / hr, and micro1\'s law category lists 55 hourly roles at $25 to $400/hr.</p><ul style="margin:10px 0 0">'
  '<li><strong>Highest ceilings:</strong> law, finance, medicine, software and data, and research roles.</li>'
  '<li><strong>Biggest change since October:</strong> Handshake AI raised its Software Engineer ceiling to "Up to $150/hr," while micro1 stopped listing several of its best-paid finance and law roles.</li>'
  '<li><strong>What these numbers are:</strong> rates each platform lists, not what most people earn. Hours vary and projects end.</li></ul></div>')
B('    <p>This is Knackboard\'s first monthly pay report. It pulls together what four platforms that pay experts for remote project work list for each field this month, in their own wording, with a source link and a check date on every figure. The point is simple: get paid for what you know, and know what each platform actually lists before you spend time on an application. The figures come from our ' + a('/pay-tracker', 'pay tracker') + ', which we rechecked against every live source page on Nov 3, 2026, and from micro1\'s ' + a(M1, 'public opportunities listing') + ', read the same day.</p>')

B('    <h2>What does each platform say it pays?</h2>')
B('    <p>Each platform describes pay differently, so compare the wording, not just the numbers. "Up to" is a ceiling. A range like $60-$150 / hr is the band one listing shows. "Starting at" is DataAnnotation\'s floor for a type of project.</p>')
B('    <table class="guide-table">\n      <thead><tr><th>Platform</th><th>How it states pay (own words)</th><th>Checked</th></tr></thead>\n      <tbody>')
rows = [
 ('DataAnnotation', 'FAQ: "Starting at $25-$50 per hour" for general projects, "Starting at $40-$125+ per hour" for professional and STEM projects, "Starting at $40-$150+ per hour" for coding, and "Starting at $25-$40 per hour" for multilingual work (' + a(DAFAQ, 'DataAnnotation FAQ') + ')'),
 ('Handshake AI', 'Overall: "from $17/hr to $150+/hr (depending on the project)" (' + a(HSAI, 'Handshake AI') + '). Role pages show a ceiling, such as Investment Bankers "Up to $175/hr, depending on the project." US-based experts only.'),
 ('Mercor', 'A listed range on each role, such as Physician Talent Network $110-$250 / hr (' + a(mc('list_AAABnJzK0z1CNefOyERAAb9m/physician-talent-network'), 'listing') + ') or Generalist Expert $40-$70 / hr (' + a(mc('list_AAABoKORCF2dakrez4FCAo_G/generalist-expert'), 'listing') + ').'),
 ('micro1', 'A range on each role, shown as "Pay: $X-Y/h" on its ' + a(M1, 'opportunities listing') + ', such as Finance Specialist at $150-350/h.'),
]
for p, w in rows:
    B('        <tr><td>%s</td><td>%s</td><td>Nov 3, 2026</td></tr>' % (p, w))
B('      </tbody>\n    </table>')

B('    <h2>What does each field list this month?</h2>')
B('    <p>Here are the highest listings we found for each field, plus a few lower ones so you can see the spread. Every DataAnnotation, Handshake AI, and Mercor figure below was rechecked on its live page on Nov 3, 2026, and every micro1 figure comes from its public listing on the same day.</p>')
fields = [
 ('Law', [
  'micro1: its law category listed 55 hourly roles at $25 to $400/hr (' + a(M1, 'micro1 listing') + ').',
  'Handshake AI: Legal Professionals "Up to $150/hr, depending on the project" (' + a(hs('legal-professional-ai-trainer'), 'role page') + '), Lawyers "Up to $110/hr, depending on the project" (' + a(hs('law-expert-ai-trainer'), 'role page') + ').',
  'Mercor: Lawyer Talent Network listed at $60-$150 / hr (' + a(mc('list_AAABnJz6-RP8K0Qe1IxHK6LT/lawyer-talent-network'), 'listing') + ').',
  'DataAnnotation: Attorney "Up to $125+/hr" (' + a(da('attorney'), 'role page') + ').']),
 ('Finance and accounting', [
  'micro1: its finance category listed 15 hourly roles at $30 to $350/hr, accounting roles included (' + a(M1, 'micro1 listing') + ').',
  'Handshake AI: Investment Bankers "Up to $175/hr, depending on the project" (' + a(hs('investment-banking-expert-ai-trainer'), 'role page') + '), Corporate Finance Analyst "Up to $80/hr, depending on the project" (' + a(hs('corporate-finance-analyst'), 'role page') + ').',
  'Mercor: Finance Expert listed at $60-$180 / hr (' + a(mc('list_AAABoKOQo_tcpjmZ2_xLb7qN/finance-expert'), 'listing') + '), Accounting &amp; Audit Domain Expert at $60-$100 / hr (' + a(mc('list_AAABoBt89Pf5xMUItbxMCqGe/accounting-audit-domain-expert'), 'listing') + ').',
  'DataAnnotation: Accountant, Corporate Accountant, Public Accountant, and Tax Accountant pages each "Up to $125+/hr" (' + a(da('accountant'), 'example') + ').']),
 ('Medicine, nursing, and pharmacy', [
  'micro1: its medicine category listed 20 roles at $20 to $125/hr (physician roles $70 to $125/hr, Registered Nurse $60 to $70/hr, coding, enrollment, and Medicare counseling $20 to $70/hr), the same as on Nov 2, 2026 (' + a(M1, 'micro1 listing') + ').',
  'Mercor: Physician Talent Network listed at $110-$250 / hr, Nursing Talent Network at $60-$120 / hr (' + a(mc('list_AAABnJzRBPRcrO1IUeVFkqqc/nursing-talent-network'), 'listing') + '), and Pharma Commercial Forecasting Expert at $130-$210 / hr (' + a(mc('list_AAABn9Fr4y9bpcGSiR5KqbF3/pharma-commercial-forecasting-expert-launch-curves'), 'listing') + ').',
  'Handshake AI: Healthcare and Nursing Professionals "Up to $140/hr, depending on the project" (' + a(hs('healthcare-and-nursing-professionals-ai-trainer/'), 'role page') + '), Pharmacists "Up to $130/hr, depending on the project" (' + a(hs('pharmacy-expert-(master-s)'), 'role page') + ').',
  'DataAnnotation: Physician "Up to $125+/hr" (' + a(da('physician'), 'role page') + ').']),
 ('Software, data, and machine learning', [
  'DataAnnotation: Software Engineer and Data Scientist "Up to $150+/hr" (' + a(da('software-engineer'), 'role page') + ').',
  'Handshake AI: Software Engineer "Up to $150/hr, depending on the project" (' + a(hs('software-engineer'), 'role page') + ').',
  'Mercor: Machine Learning Engineer Talent Network listed at $70-$250 / hr (' + a(mc('list_AAABnJzIt-SOsdwOeF5Ebarf/machine-learning-engineer-talent-network'), 'listing') + '), Data Scientist Talent Network at $100-$150 / hr (' + a(mc('list_AAABn6vGkxZngsMTe7xP7rqG/data-scientist-talent-network'), 'listing') + ').',
  'micro1: its software engineering category listed 18 hourly roles at $25 to $300/hr, and its AI and machine learning category 5 roles at $14 to $120/hr (' + a(M1, 'micro1 listing') + ').']),
 ('Science and math', [
  'micro1: its sciences and research category listed 11 roles at $30 to $400/hr; the top is two computational physics research scientist roles at $100-400/h (' + a(M1, 'micro1 listing') + ').',
  'Handshake AI: Chemistry Expert "Up to $150/hr, depending on the project" (' + a(hs('chemistry-expert'), 'role page') + '), Math Expert "Up to $75/hr, depending on the project" (' + a(hs('math-ai-trainer'), 'role page') + ').',
  'Mercor: Life, Physical &amp; Social Science Expert listed at $60-$120 / hr (' + a(mc('list_AAABoKOPfaLb80VeraNJDbi1/life-physical-social-science-expert'), 'listing') + '), Physics Expert at $70-$100 / hr (' + a(mc('list_AAABoNelIXEL_UXJCpdK7qyb/high-energy-physicist-phd'), 'listing') + ').',
  'DataAnnotation: Chemist and Mathematician pages each "Up to $125+/hr" (' + a(da('chemist'), 'example') + ').']),
 ('Engineering', [
  'micro1: its applied engineering category listed 24 roles at $40 to $185/hr (' + a(M1, 'micro1 listing') + ').',
  'Mercor: Mechanical Engineering Experts listed at $100-$120 / hr (' + a(mc('list_AAABoN3On6pC5dA5aDRBErDP/mechanical-engineering-experts'), 'listing') + '), Engineering Expert at $60-$125 / hr (' + a(mc('list_AAABoKOQBVjEtnDVZPFH-Ljn/engineering-expert'), 'listing') + ').',
  'Handshake AI: PCB Tool Specialist "Up to $125/hr, depending on the project" (' + a(hs('pcb-designer-ai-trainer'), 'role page') + '), Electrical Engineering Expert "Up to $120/hr, depending on the project" (' + a(hs('electrical-engineering-expert'), 'role page') + ').',
  'DataAnnotation: Hardware Engineer "Up to $125+/hr" (' + a(da('hardware-engineer'), 'role page') + ').']),
 ('Teaching', [
  'Handshake AI: STEM Professor "Up to $150/hr, depending on the project" (' + a(hs('stem-professor'), 'role page') + '), GRE/GMAT Quantitative Instructor "Up to $100/hr, depending on the project" (' + a(hs('gre-instructor'), 'role page') + ').',
  'Mercor: Education &amp; Training Expert listed at $30-$85 / hr (' + a(mc('list_AAABoKOQxMW5nhNVUkFOdLPr/education-training-expert'), 'listing') + ').']),
 ('Languages', [
  'Mercor: Spanish Tutors listed at $60-$65 / hr (' + a(mc('list_AAABoEkE3Fx5nN65LndAloi6/spanish-tutors'), 'listing') + ').',
  'Handshake AI: Linguistics Expert "Up to $80/hr, depending on the project" (' + a(hs('linguistics-expert'), 'role page') + ').',
  'micro1: its language and audio category listed 37 roles at $8 to $70/hr; most bilingual expert roles showed $30-65/h, and transcription roles sat at the bottom (' + a(M1, 'micro1 listing') + ').',
  'DataAnnotation: Spanish Specialist "Up to $40/hr" (' + a(da('spanish-expert'), 'role page') + ').']),
 ('General work (no specific field)', [
  'Mercor: Generalist (Must own MacBook) listed at $40-$80 / hr (' + a(mc('list_AAABn5vEYCY9JpDvdTdM1Y-0/generalist-must-own-macbook'), 'listing') + '), Generalist Expert at $40-$70 / hr (' + a(mc('list_AAABoKORCF2dakrez4FCAo_G/generalist-expert'), 'listing') + ').',
  'DataAnnotation: Generalist "Up to $50/hr" (' + a(da('generalist'), 'role page') + ').',
  'Handshake AI: AI Evaluation Specialist "Up to $17/hr, depending on the project" (' + a(hs('generalist-bachelor-ai-eveluation-specialist'), 'role page') + ').',
  'micro1: its generalist category listed 20 hourly roles at $6 to $70/hr (' + a(M1, 'micro1 listing') + ').']),
]
for name, items in fields:
    B('    <h3>%s</h3>' % name)
    B('    <ul>' + ''.join('<li>%s</li>' % i for i in items) + '</ul>')

B('    <h2>What does micro1 list by category?</h2>')
B('    <p>micro1 posts pay on each role, so we count its own categories on the ' + a(M1, 'micro1 opportunities listing') + ', hourly roles only, as of Nov 3, 2026. Each range runs from the lowest to the highest rate on any listing in that category, so it shows the spread, not what most roles pay. Medicine is unchanged from Nov 2, 2026.</p>')
B('    <table class="guide-table">\n      <thead><tr><th>micro1 category</th><th>Hourly roles</th><th>Listed pay</th></tr></thead>\n      <tbody>')
cats = [('Law', 55, '$25 to $400/hr'), ('Finance (accounting included)', 15, '$30 to $350/hr'),
 ('Medicine', 20, '$20 to $125/hr (physician roles $70 to $125/hr, Registered Nurse $60 to $70/hr, coding, enrollment, and Medicare counseling $20 to $70/hr)'),
 ('Sciences and research', 11, '$30 to $400/hr'), ('Applied engineering', 24, '$40 to $185/hr'),
 ('Software engineering', 18, '$25 to $300/hr'), ('Data analysis', 6, '$25 to $350/hr'),
 ('AI and machine learning', 5, '$14 to $120/hr'), ('Business operations', 12, '$28 to $350/hr'),
 ('Language and audio', 37, '$8 to $70/hr'), ('Generalist', 20, '$6 to $70/hr')]
for c, n, p in cats:
    B('        <tr><td>%s</td><td>%d</td><td>%s</td></tr>' % (c, n, p))
B('      </tbody>\n    </table>')
B('    <p>The top of a wide range usually comes from one or two specialist roles. In business operations and data analysis, the $350/h ceiling is two consulting and two data science specialist roles at $150-350/h, while every other role in those two categories topped out at $105/h or less.</p>')

B('    <h2>What changed since October?</h2>')
B('    <p>Our pay tracker started recording history on Oct 26, 2026, so "October" here means Oct 26 to Oct 31. Every change below is in the tracker\'s ' + a('/pay-tracker', 'change log') + ' and its ' + a('/pay-tracker-history.csv', 'history file') + ', dated by the day we saw it.</p>')
B('    <ul>'
  '<li><strong>Handshake AI Software Engineer went up.</strong> It was "Up to $120/hr, depending on the project" and became "Up to $150/hr, depending on the project" on Oct 31, 2026 (' + a(hs('software-engineer'), 'role page') + ').</li>'
  '<li><strong>Three Mercor listings went down.</strong> Physics Expert moved from $80-$110 / hr to $70-$100 / hr, and two Humanities Expert listings moved from $50 / hr and $50-$63 / hr to $45-$60 / hr, all on Oct 30, 2026 (' + a(mc('list_AAABoNelIXEL_UXJCpdK7qyb/high-energy-physicist-phd'), 'Physics Expert listing') + ').</li>'
  '<li><strong>A Mercor generalist listing came back.</strong> Generalist (Must own MacBook) was closed on Oct 26, 2026 and was listed again at $40-$80 / hr on Nov 2, 2026. See ' + a('/guides/mercor-generalist-macbook', 'our page on that listing') + '.</li>'
  '<li><strong>micro1 stopped listing several high-paying roles.</strong> Investment Banking Expert and Equity Research Expert ($175-300/h each), AI Legal Fellow, Litigation and Motion Practice ($150-300/h), and Bilingual Cantonese Psychiatrist ($100-200/h) were gone on Oct 31, 2026, and CFD Engineer ($50-150/h) on Nov 1, 2026. Its finance category showed 14 roles at $40 to $350/hr on Oct 31, 2026 and 15 at $30 to $350/hr on Nov 3, 2026, because new finance roles took their place, the newest a Finance Research Expert role at $30-85/h.</li>'
  '<li><strong>The headline wording held steady.</strong> DataAnnotation\'s FAQ "Starting at" figures and Handshake AI\'s "from $17/hr to $150+/hr" range read the same on Nov 3, 2026 as on Oct 26, 2026.</li></ul>')
B('    <p>One week of history is short, so treat this as a snapshot, not a trend. Next month\'s report will compare a full month.</p>')

B('    <h2>What do these numbers leave out?</h2>')
B('    <ul>'
  '<li><strong>Listed is not earned.</strong> An "Up to" figure is a ceiling, and a range is what one listing shows. Your rate depends on the project, your assessment, and the platform\'s review.</li>'
  '<li><strong>Hours come and go.</strong> DataAnnotation workers describe dry spells in r/DataAnnotationTech threads such as "' + a('https://www.reddit.com/r/DataAnnotationTech/comments/1u21ryg/ok_theres_definitely_a_drought_but_how_long_will/', 'Ok, there&#x27;s definitely a drought, but how long will it last?') + '"</li>'
  '<li><strong>Pay disputes happen.</strong> A Handshake AI ' + a('https://www.trustpilot.com/reviews/6a17b20c55ab35337325abd8', 'Trustpilot review posted May 28, 2026') + ' says: "Two weeks in a row, I had my hours retroactively cut in half, was told to file a dispute, manually track my hours on my end, and keep working."</li>'
  '<li><strong>Projects end.</strong> Negative reviews on Mercor\'s ' + a('https://www.trustpilot.com/review/mercor.io', 'Trustpilot profile') + ' (read Oct 17, 2026) describe sudden offboarding and unstable hours.</li>'
  '<li><strong>Getting in takes time.</strong> A micro1 ' + a('https://www.trustpilot.com/reviews/6ad41476c179280ae8c2538c', 'Trustpilot review posted Oct 18, 2026') + ' says: "Over the past 30 days, I completed at least five interviews daily without securing a single role."</li>'
  '<li><strong>Where you live matters.</strong> Handshake AI says: "To participate in the Handshake AI Fellowship, you must be based in the U.S. and have a valid work authorization that can be supported by Handshake." (' + a(HSAI, 'Handshake AI') + ', checked Nov 3, 2026). Some Mercor roles also require a Mac, and a few pay per task, such as Nuclear Engineer, Fuel Cycle at $65-$75 / task (' + a(mc('list_AAABoKHaq2E5KOPWUbZEO7Wr/nuclear-engineer-fuel-cycle'), 'listing') + ').</li></ul>')

B('    <h2>Who is this report for?</h2>')
B('    <p>It is for people with real expertise who want paid remote project work they can fit around a job or studies: lawyers, doctors and nurses, pharmacists, finance and accounting people, engineers, software engineers and data scientists, scientists and PhDs, teachers, and bilingual experts. If you are choosing where to apply first, look at the field lists above, then read the platform pay guide for the one that fits. Applying to more than one platform is common, since each opens and closes projects on its own schedule.</p>')

B('    <h2>How did we build this report?</h2>')
B('    <p>We started from the 169 rows in the ' + a('/pay-tracker.csv', 'pay tracker CSV') + ' and opened every DataAnnotation, Handshake AI, and Mercor source page again on Nov 3, 2026. All 98 pages that loaded matched the tracker. Fifteen Handshake AI role pages did not load from our checker that day, so this report quotes none of them except STEM Professor, which loaded on a second try, plus Healthcare and Nursing Professionals (not a tracker row), checked separately. For micro1 we read all 305 roles on its public listing on Nov 3, 2026 and grouped them by micro1\'s own categories. We copy pay in each platform\'s own words, we never count referral bonuses as pay, and we do not compute medians or claim what a typical person earns. The tracker data is also published at ' + a('https://github.com/knackboard-data/pay-data', 'github.com/knackboard-data/pay-data') + ' under CC BY 4.0.</p>')

B('    <h2>Related guides</h2>')
B('    <ul class="guide-list"><li><a href="/guides/how-much-does-micro1-pay">How much does micro1 pay by field?</a></li><li><a href="/guides/how-much-does-mercor-pay">How much does Mercor pay?</a></li><li><a href="/guides/how-much-does-handshake-ai-pay">How much does Handshake AI pay?</a></li><li><a href="/guides/how-much-does-dataannotation-pay">How much does DataAnnotation pay?</a></li><li><a href="/pay-tracker">Expert pay tracker</a></li></ul>')
B('    <p class="guide-note">Pay figures are the rates each platform listed on the dates shown, not guaranteed earnings and not forecasts. Each platform decides who qualifies, which projects are open, and final pay. Check the current listing before applying.</p>')
B('    <div class="guide-cta"><p>Not sure which platform fits your background? Answer 3 quick questions and see your best matches, ranked, with the pay each platform lists.</p><a class="btn btn-primary" href="/">Find my match →</a></div>')

B('    <h2>FAQ</h2>')
for q, ans in FAQ:
    B('    <h3>%s</h3>' % E(q))
    B('    <p>%s</p>' % E(ans, quote=True))

B('    <h2>Sources</h2>')
B('    <p class="guide-note guide-checked"><strong>How we checked:</strong> The Knackboard team rechecked every DataAnnotation, Handshake AI, and Mercor figure on this page against its live source between 00:07 and 00:26 JST on Nov 3, 2026 (STEM Professor, Healthcare and Nursing Professionals, and AI Evaluation Specialist again at 01:44 JST), and read micro1\'s public listing at 01:44 JST the same day. Changes since October come from the pay tracker change log. Reviews are quoted word for word and linked.</p>')
srcs = [
 'Knackboard ' + a('/pay-tracker', 'pay tracker') + ', ' + a('/pay-tracker.csv', 'CSV') + ', and ' + a('/pay-tracker-history.csv', 'history CSV') + ', rechecked Nov 3, 2026',
 a(M1, 'micro1 opportunities listing') + ', all 305 roles read Nov 3, 2026',
 a(DAFAQ, 'DataAnnotation FAQ') + ' and role pages on the ' + a('https://www.dataannotation.tech/job-board', 'DataAnnotation job board') + ', checked Nov 3, 2026',
 a(HSAI, 'Handshake AI') + ' and its role pages, checked Nov 3, 2026',
 a('https://work.mercor.com/', 'Mercor job listings') + ', checked Nov 3, 2026',
 'Trustpilot and Reddit posts linked above, with the dates shown',
]
B('    <ul class="guide-sources">' + ''.join('<li>%s</li>' % s for s in srcs) + '</ul>')
B('    <p class="guide-note guide-about"><strong>What is Knackboard?</strong> Knackboard is a free 3-question quiz that matches people with expert knowledge to remote paid work on platforms like Mercor, DataAnnotation, Handshake AI, and micro1. Get paid for what you know. We earn referral fees when you join through our links, and each platform decides who qualifies and what it pays.</p>')
B('    <p class="guide-disclosure"><strong>Referral disclosure:</strong> Knackboard earns referral fees from micro1, Handshake, Mercor, and DataAnnotation when people join through our links. That never changes what you are paid or how your application is reviewed. <a href="/how-we-get-paid">How we get paid</a>.</p>')
B('''    </article>
  </main>
  <footer class="site-footer">
    <nav aria-label="Site navigation">
      <a href="/guides/">Guides</a>
      <a href="/about">About</a>
      <a href="/how-we-get-paid">How we get paid</a>
      <a href="/privacy">Privacy</a>
      <a href="/terms">Terms</a>
    </nav>
  </footer>
  <script src="/js/track.js" defer></script>
</body>
</html>''')
out = head + '\n' + '\n'.join(body) + '\n'
assert '\u2014' not in out and '\u2013' not in out
open('%s/public/guides/%s.html' % (REPO, SLUG), 'w').write(out)
print('wrote', len(out))
