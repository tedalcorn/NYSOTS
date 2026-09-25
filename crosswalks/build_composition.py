"""Uniform cross-year composition analysis for the SOTS corpus.

Why this exists: `section_bucket` is not comparable across years (2022-2024 use
normalized thematic buckets, 2025-2026 carry raw chapter headings), and
`overlap_theme` is a hand-assigned per-item lookup whose granularity drifts by
year (its "_general" catch-all share swings 9%-46%). Neither supports a
composition trend. This module re-classifies all rows with ONE ruleset applied
identically to every year, so residual error is at least uniform.
"""
import csv, glob, re, json
from collections import Counter, defaultdict

# Priority-ordered. First domain whose pattern matches the scored text wins ties
# by weight, not order; order only breaks exact ties.
DOMAINS = [
 ("public_safety_justice", r"\b(police|law enforcement|trooper|state police|crime|criminal|prosecut|district attorney|jail|prison|incarcerat|parole|probation|reentry|gun|firearm|shooting|violence|retail theft|subway (crime|safety)|hate crime|domestic violence|victim)\w*"),
 ("health_care", r"\b(health care|healthcare|hospital|medicaid|medicare|physician|nurse|clinic|patient|insur\w+ coverage|public health|disease|maternal|cancer|opioid|overdose|substance use|nursing home|long-?term care|telehealth|prescription|pharmac)\w*"),
 ("mental_health", r"\b(mental health|psychiatric|behavioral health|suicide|988|crisis (stabilization|response|center)|counsel\w*|therap\w+|OMH)\b"),
 ("housing_homelessness", r"\b(housing|homeless|shelter|rent|tenant|landlord|eviction|mortgage|zoning|accessory dwelling|affordable unit)\w*"),
 ("climate_energy_env", r"\b(climate|emission|renewable|solar|wind power|offshore wind|clean energy|decarboniz|electric vehicle|EV charg|greenhouse|green energy|environment|conservation|water quality|pollut|resilien|flood|heat pump|building code)\w*"),
 ("education_k12", r"\b(school|student|teacher|classroom|pre-?k|kindergarten|literacy|curriculum|school district|chronic absentee|school meal)\w*"),
 ("higher_ed_workforce", r"\b(college|university|SUNY|CUNY|apprentice|workforce|job training|credential|career pathway|community college|tuition|degree program|reskill|upskill)\w*"),
 ("child_care_family", r"\b(child care|childcare|day care|early childhood|paid family leave|foster|youth program|after-?school|parent\w*|diaper|baby)\b"),
 ("affordability_cost", r"\b(affordab\w+|cost of living|tax (credit|cut|relief|rebate)|inflation|utility bill|grocery|consumer (protection|price)|fee|rebate check|minimum wage|earned income)\w*"),
 ("economic_development", r"\b(economic development|business|manufactur|semiconductor|chip|startup|entrepreneur|innovation|tourism|downtown|main street|investment fund|jobs? (creation|growth)|industry|small business)\w*"),
 ("infrastructure_transport", r"\b(transit|MTA|subway service|rail|bus|highway|bridge|road|airport|port|broadband|infrastructure|transportation|traffic|pedestrian|bike)\w*"),
 ("agriculture_food", r"\b(farm|agricultur|food (bank|access|insecurity|system)|nutrition|SNAP|dairy|crop|hunger)\w*"),
 ("government_ops", r"\b(state agency|red tape|permit|licens\w+|customer (service|experience)|digital (service|government)|modern\w+ (the )?state|procurement|workforce of state|government (operation|efficien)|data (system|sharing|privacy)|private data|artificial intelligence|cyber)\w*"),
 ("equity_civil_rights", r"\b(equity|discriminat|civil rights|immigrant|refugee|LGBTQ|transgender|disabilit|veteran|tribal|indigenous|minority-?owned|women-?owned|language access|reproductive|abortion)\w*"),
 ("aging_seniors", r"\b(senior|aging|older adult|elder|caregiv|retirement)\w*"),
 ("parks_recreation", r"\b(state park|parks|recreation|trail|campground|swimming|pool|beach|open space|historic site)\w*"),
]
COMPILED=[(n,re.compile(p,re.I)) for n,p in DOMAINS]
NUMWORD=re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion|percent|double|triple|quadruple|first|half)\b",re.I)
DOLLAR=re.compile(r"\$\s?[\d,.]+")
NUM=re.compile(r"\b\d[\d,\.]*\b")

def classify(title, text):
    """Title-first: the title names the commitment. Body text only decides when
    the title is silent, because bodies cite context that drifts off-topic
    (a labor bill that mentions 'green jobs' is not a climate commitment)."""
    order=[n for n,_ in DOMAINS]
    tscore={n:len(p.findall(title or "")) for n,p in COMPILED}
    tscore={k:v for k,v in tscore.items() if v}
    if tscore:
        best=max(tscore.values())
        winners=sorted([k for k,v in tscore.items() if v==best], key=order.index)
        return winners[0], best
    bscore={n:len(p.findall(text or "")) for n,p in COMPILED}
    bscore={k:v for k,v in bscore.items() if v>=2}   # need real repetition, not a passing mention
    if not bscore: return "unclassified", 0
    best=max(bscore.values())
    winners=sorted([k for k,v in bscore.items() if v==best], key=order.index)
    return winners[0], best

def load():
    rows=[]
    for f in glob.glob("20*-*enriched-inventory.csv"):
        for r in csv.DictReader(open(f)):
            t=r.get("proposal_title","") or ""; x=r.get("commitment_text","") or ""
            d,score=classify(t,x)
            r["_domain"]=d; r["_score"]=score
            r["_words"]=len(x.split())
            blob=t+" "+x
            r["_has_dollar"]="yes" if DOLLAR.search(blob) else "no"
            r["_has_number"]="yes" if (NUM.search(blob) or NUMWORD.search(blob)) else "no"
            r["_dollar_title"]="yes" if DOLLAR.search(t) else "no"
            rows.append(r)
    return rows

if __name__=="__main__":
    rows=load()
    by=defaultdict(list)
    for r in rows: by[r["year"]].append(r)
    years=sorted(by)
    print(f"n={len(rows)}  unclassified={sum(1 for r in rows if r['_domain']=='unclassified')} "
          f"({100*sum(1 for r in rows if r['_domain']=='unclassified')//len(rows)}%)")
    print("\nunclassified by year:", {y:sum(1 for r in by[y] if r['_domain']=='unclassified') for y in years})
    doms=[n for n,_ in DOMAINS]
    print("\n=== SHARE OF ITEMS (%) ===")
    print(f"{'domain':26}"+"".join(f"{y:>8}" for y in years)+f"{'Δ22→26':>9}")
    out={}
    for d in doms:
        sh=[100*sum(1 for r in by[y] if r["_domain"]==d)/len(by[y]) for y in years]
        out[d]=sh
        print(f"{d:26}"+"".join(f"{v:>8.1f}" for v in sh)+f"{sh[-1]-sh[0]:>+9.1f}")
    print("\n=== SHARE OF WORDS (%) — emphasis proxy ===")
    print(f"{'domain':26}"+"".join(f"{y:>8}" for y in years)+f"{'Δ22→26':>9}")
    for d in doms:
        sh=[]
        for y in years:
            tot=sum(r["_words"] for r in by[y])
            sh.append(100*sum(r["_words"] for r in by[y] if r["_domain"]==d)/tot)
        print(f"{d:26}"+"".join(f"{v:>8.1f}" for v in sh)+f"{sh[-1]-sh[0]:>+9.1f}")

def write_outputs():
    rows=load(); by=defaultdict(list)
    for r in rows: by[r["year"]].append(r)
    years=sorted(by)
    with open("crosswalks/composition-by-domain.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["year","domain","n_items","pct_items","n_words","pct_words"])
        for y in years:
            tot=len(by[y]); totw=sum(r["_words"] for r in by[y])
            for d in [n for n,_ in DOMAINS]+["unclassified"]:
                sel=[r for r in by[y] if r["_domain"]==d]
                ww=sum(r["_words"] for r in sel)
                w.writerow([y,d,len(sel),round(100*len(sel)/tot,2),ww,round(100*ww/totw,2)])
    with open("crosswalks/agenda-character-by-year.csv","w",newline="") as f:
        w=csv.writer(f); w.writerow(["year","n","pct_new","pct_continuation_or_expansion",
            "pct_title_quantified","pct_text_has_dollar","pct_title_has_dollar","median_words"])
        for y in years:
            rs=by[y]; n=len(rs)
            cont=sum(1 for r in rs if r["continuity_to_prior_year"] in("continuation","expansion","follow_on"))
            new=sum(1 for r in rs if r["continuity_to_prior_year"]=="new")
            ws=sorted(r["_words"] for r in rs)
            w.writerow([y,n,round(100*new/n,1),round(100*cont/n,1),
                round(100*sum(1 for r in rs if r["quantified"]=="yes")/n,1),
                round(100*sum(1 for r in rs if r["_has_dollar"]=="yes")/n,1),
                round(100*sum(1 for r in rs if r["_dollar_title"]=="yes")/n,1),
                ws[len(ws)//2]])
    print("wrote crosswalks/composition-by-domain.csv and crosswalks/agenda-character-by-year.csv")
