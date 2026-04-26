import streamlit as st
import requests
import pandas as pd
import re
from datetime import datetime, timezone
import time
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import inch

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Reddit Social Listener | LeadPulls",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Brand Styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root { --navy:#00233F; --orange:#FF5F00; }
    .stApp { background:#f0f2f5; }
    header[data-testid="stHeader"] { display:none; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background:#00233F !important;
        border-right: 3px solid #FF5F00;
    }
    section[data-testid="stSidebar"] * { color:#fff !important; }
    section[data-testid="stSidebar"] .stSlider label { color:#aec6d8 !important; font-size:12px; }

    /* ── Top bar ── */
    .topbar {
        background: linear-gradient(135deg, #00233F 0%, #003a65 100%);
        padding:18px 28px; border-radius:12px; margin-bottom:20px;
        display:flex; align-items:center; justify-content:space-between;
        box-shadow: 0 4px 15px rgba(0,35,63,0.3);
    }
    .topbar-left { display:flex; align-items:center; gap:14px; }
    .topbar-logo { font-size:22px; font-weight:900; letter-spacing:-0.5px; color:#fff; }
    .topbar-logo span { color:#FF5F00; }
    .topbar-tag {
        background:rgba(255,95,0,0.2); border:1px solid rgba(255,95,0,0.4);
        color:#FF5F00; font-size:11px; font-weight:700; padding:3px 10px;
        border-radius:20px; text-transform:uppercase; letter-spacing:1px;
    }
    .topbar-meta { font-size:12px; color:#aec6d8; }
    .topbar-meta b { color:#fff; }

    /* ── Config card ── */
    .config-card {
        background:#fff; border-radius:14px; padding:28px 32px;
        box-shadow:0 2px 12px rgba(0,0,0,0.06); margin-bottom:20px;
        border-top: 4px solid #FF5F00;
    }
    .step-label {
        font-size:11px; font-weight:800; color:#FF5F00;
        text-transform:uppercase; letter-spacing:1.5px; margin-bottom:6px;
    }
    .step-title {
        font-size:18px; font-weight:800; color:#00233F; margin-bottom:16px;
    }

    /* ── Industry selector ── */
    .stSelectbox > div > div {
        border: 2px solid #e0e0e0 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        color: #00233F !important;
    }
    .stSelectbox > div > div:focus-within {
        border-color: #FF5F00 !important;
    }

    /* ── Signal cards ── */
    .signal-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin:4px 0 20px; }
    .signal-card {
        background:#f8f9fa; border:2px solid #e8e8e8;
        border-radius:12px; padding:14px 16px;
        transition: all 0.2s;
    }
    .signal-card:hover { border-color:#FF5F00; background:#fff8f5; }
    .signal-card-header { display:flex; align-items:center; gap:10px; margin-bottom:4px; }
    .signal-icon { font-size:20px; }
    .signal-name { font-size:14px; font-weight:700; color:#00233F; }
    .signal-desc { font-size:12px; color:#777; line-height:1.4; padding-left:30px; }

    /* ── Keyword input ── */
    .stTextArea textarea {
        border: 2px solid #e0e0e0 !important;
        border-radius: 10px !important;
        font-size: 14px !important;
    }
    .stTextArea textarea:focus {
        border-color: #FF5F00 !important;
        box-shadow: 0 0 0 3px rgba(255,95,0,0.1) !important;
    }

    /* ── Run button ── */
    .stButton > button {
        background: linear-gradient(135deg, #FF5F00, #e05400) !important;
        color: #fff !important; border: none !important;
        border-radius: 10px !important; font-weight: 800 !important;
        font-size: 16px !important; padding: 14px 32px !important;
        width: 100% !important; letter-spacing: 0.3px !important;
        box-shadow: 0 4px 12px rgba(255,95,0,0.35) !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(255,95,0,0.45) !important;
    }

    /* ── Download buttons ── */
    .stDownloadButton > button {
        background:#00233F !important; color:#fff !important;
        border:none !important; border-radius:8px !important;
        font-weight:600 !important; font-size:13px !important;
    }

    /* ── Email gate ── */
    .email-gate {
        background: linear-gradient(135deg, #00233F, #003a65);
        border-radius:16px; padding:52px 40px; text-align:center;
        max-width:480px; margin:80px auto;
        box-shadow: 0 20px 60px rgba(0,35,63,0.3);
        border-top: 4px solid #FF5F00;
    }
    .email-gate h2 { color:#fff; font-size:26px; font-weight:900; margin-bottom:8px; }
    .email-gate p  { color:#aec6d8; font-size:14px; margin-bottom:28px; line-height:1.6; }
    .gate-perks { text-align:left; margin-bottom:24px; }
    .gate-perk  { color:#fff; font-size:13px; margin-bottom:8px; }
    .gate-perk span { color:#FF5F00; font-weight:700; margin-right:8px; }

    /* ── Stat boxes ── */
    .stats-row { display:flex; gap:12px; margin-bottom:20px; }
    .stat-box {
        background:#fff; border-radius:12px; padding:16px 20px;
        flex:1; border-bottom:3px solid #FF5F00;
        box-shadow:0 2px 8px rgba(0,0,0,0.06);
        text-align:center;
    }
    .stat-number { font-size:30px; font-weight:900; color:#00233F; line-height:1; }
    .stat-label  { font-size:11px; color:#888; text-transform:uppercase; letter-spacing:0.5px; margin-top:4px; }

    /* ── Result cards ── */
    .rcard {
        background:#fff; border-radius:12px;
        border:1px solid #eee; border-left: 4px solid #FF5F00;
        padding:20px 22px; margin-bottom:14px;
        box-shadow:0 2px 8px rgba(0,0,0,0.04);
    }
    .rcard.handled { border-left-color:#ccc; opacity:0.55; }
    .rcard-top { display:flex; align-items:center; gap:8px; margin-bottom:10px; flex-wrap:wrap; }
    .badge-sub  { background:#00233F; color:#fff; border-radius:20px; padding:3px 12px; font-size:11px; font-weight:700; }
    .badge-sig  { border-radius:20px; padding:3px 12px; font-size:11px; font-weight:600; }
    .badge-intent     { background:#e8f5e9; color:#2e7d32; }
    .badge-pain       { background:#fdecea; color:#c62828; }
    .badge-competitor { background:#fff3e0; color:#e65100; }
    .badge-trend      { background:#e8eaf6; color:#283593; }
    .badge-boolean    { background:#f3e5f5; color:#6a1b9a; }
    .badge-hot { background:#FF5F00; color:#fff; border-radius:20px; padding:3px 12px; font-size:11px; font-weight:700; margin-left:auto; }
    .rcard-title { font-size:16px; font-weight:700; color:#00233F; margin-bottom:6px; line-height:1.4; }
    .rcard-title a { color:#00233F; text-decoration:none; }
    .rcard-title a:hover { color:#FF5F00; text-decoration:underline; }
    .rcard-snippet { font-size:13px; color:#555; line-height:1.6; margin-bottom:10px; }
    .rcard-tags { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; }
    .rcard-tag { background:#f0f4f8; color:#00233F; border-radius:20px; padding:2px 10px; font-size:11px; font-weight:600; }
    .rcard-footer { font-size:12px; color:#999; }
    .rcard-footer b { color:#555; }

    div[data-testid="stExpander"] { border:1px solid #e8e8e8; border-radius:10px; }
    .stCheckbox label { font-size:14px !important; font-weight:600 !important; color:#00233F !important; }
</style>
""", unsafe_allow_html=True)

# ─── Industry Templates ───────────────────────────────────────────────────────
# ─── Industry Templates ───────────────────────────────────────────────────────
TEMPLATES = {
    "MSPs / IT Firms": {
        "subreddits": ["msp","sysadmin","ITCareerQuestions","smallbusiness","cybersecurity","techsupport","businessowners","mspownersclub"],
        "intent":     ["recommend an MSP","looking for MSP","need IT support","managed IT","new IT provider","IT company","switch IT","outsourced IT","co-managed IT","vCISO","who handles your IT","IT support company","looking for a managed","need a new IT","IT recommendations","best MSP","find an MSP","IT vendor","managed services","IT firm"],
        "pain":       ["IT keeps going","sick of our IT","IT never responds","got hacked","ransomware","MSP dropped","IT support is","downtime","IT tickets","current IT is","IT guy quit","no IT","IT headache","cybersecurity incident","data breach","IT issues","IT problems","bad MSP","fired our MSP","IT disaster","slow IT","IT outage","phishing","service desk"],
        "competitors":["ConnectWise","Datto","SentinelOne","CrowdStrike","Kaseya","NinjaRMM","Huntress","Acronis","Webroot","Sophos","Auvik","Pax8","Syncro","Atera","Halo PSA","BrightGauge","IT Glue","Veeam","Barracuda","Cisco Meraki"],
        "trends":     ["cyber insurance","zero trust","cloud migration","Microsoft 365","M365","SIEM","SOC 2","HIPAA","backup strategy","EDR","endpoint detection","AI in IT","automation","patch management","dark web monitoring","MFA","multi-factor","MDR","XDR","CMMC","compliance"],
        "negatives":  ["job posting","internship","certification study","homework","looking for work","job hunt","studying for"],
    },
    "Med Spas": {
        "subreddits": ["SkincareAddiction","PlasticSurgery","beauty","AskWomenOver30","AskWomen","30PlusSkinCare","weddingplanning"],
        "intent":     ["looking for a med spa","recommend a place for","best med spa in","where to get botox","where to get filler","anyone tried","first time getting","thinking about trying","worth it"],
        "pain":       ["botched","uneven filler","overfilled","bad results","bruising won't go away","not happy with","terrible experience","ripped off","overcharged","lumpy","migration"],
        "competitors":["Juvederm","Restylane","Sculptra","Dysport","Xeomin","CoolSculpting","Morpheus8","Hydrafacial","Ultherapy","Semaglutide"],
        "trends":     ["natural look filler","preventative botox","weight loss injections","GLP-1","skin tightening","PRF treatment","microneedling","lip flip vs filler"],
        "negatives":  ["nursing","school project","medical school","clinical trial","research paper"],
    },
    "Law Firms": {
        "subreddits": ["legaladvice","PersonalFinance","Insurance","Divorce","landlordtenant","smallbusiness","employment"],
        "intent":     ["need a lawyer","looking for an attorney","recommend a law firm","should I get a lawyer","free consultation","worth hiring a lawyer","can I sue"],
        "pain":       ["my lawyer isn't responding","fired my attorney","got lowballed","insurance denied my claim","settlement too low","wrongful termination","landlord won't return deposit","injured at work"],
        "competitors":["LegalZoom","Rocket Lawyer","Avvo","Martindale","FindLaw"],
        "trends":     ["statute of limitations","personal injury settlement","workers comp denied","divorce mediation","custody battle","slip and fall","medical malpractice"],
        "negatives":  ["law school","bar exam","paralegal student","fictional","hypothetical","for a story","writing a book"],
    },
    "Home Services": {
        "subreddits": ["HomeImprovement","DIY","Plumbing","HVAC","Roofing","Landscaping","Renovation","FirstTimeHomeBuyer","homeowners"],
        "intent":     ["recommend a contractor","looking for a plumber","need an HVAC company","anyone know a good roofer","getting quotes for","how much should I pay for","thinking of hiring","getting bids"],
        "pain":       ["contractor ghosted me","bad contractor","scammed by","took my deposit","won't come back to fix","overcharged me","AC not working","pipe burst","roof is leaking","flooded basement"],
        "competitors":["HomeAdvisor","Angi","Thumbtack","Yelp","Houzz","TaskRabbit","Porch"],
        "trends":     ["heat pump vs AC","tankless water heater","spray foam insulation","solar panels","EV charger installation","smart thermostat","foundation crack"],
        "negatives":  ["doing it myself","DIY only","no contractors","apartment"],
    },
    "Real Estate": {
        "subreddits": ["realestate","FirstTimeHomeBuyer","RealEstateInvesting","Mortgages","RealEstateAgent","landlord","airbnb"],
        "intent":     ["looking for a realtor","recommend a real estate agent","thinking of buying","first time buyer","need a mortgage broker","selling my house","relocating need help"],
        "pain":       ["my realtor is useless","agent never calls back","lost another bidding war","deal fell through","commission too high","Zillow was wrong"],
        "competitors":["Zillow","Redfin","Realtor.com","Opendoor","Offerpad","eXp Realty","Compass","Keller Williams"],
        "trends":     ["interest rates","rent vs buy","house hacking","short term rental","1031 exchange","DSCR loan"],
        "negatives":  ["real estate school","getting my license","study guide","exam prep"],
    },
    "Financial Services / Accounting": {
        "subreddits": ["personalfinance","financialplanning","investing","tax","smallbusiness","Accounting","Bookkeeping"],
        "intent":     ["looking for a financial advisor","need a good accountant","recommend a CPA","need help with taxes","fiduciary advisor","need tax help for my business"],
        "pain":       ["IRS notice","got audited","CPA messed up my taxes","my accountant never responds","missed deductions","financial advisor lost money","bookkeeper made errors"],
        "competitors":["TurboTax","H&R Block","QuickBooks","Bench","Pilot","Betterment","Edward Jones"],
        "trends":     ["backdoor Roth","tax loss harvesting","S-corp election","estate planning","fractional CFO","cryptocurrency taxes"],
        "negatives":  ["finance degree","CFA exam","accounting homework","textbook","college"],
    },
    "Insurance": {
        "subreddits": ["Insurance","HealthInsurance","personalfinance","smallbusiness","legaladvice","CarInsurance","LifeInsurance"],
        "intent":     ["looking for insurance","recommend an insurance broker","need business insurance","shopping for coverage","switching insurance providers"],
        "pain":       ["claim denied","insurance won't pay","premium went up","dropped by my insurer","adjuster lowballed me","fighting with my insurance","policy lapsed"],
        "competitors":["State Farm","Geico","Progressive","Allstate","Nationwide","USAA","Hiscox","Next Insurance","Lemonade"],
        "trends":     ["cyber liability insurance","umbrella policy","ACA marketplace","group health benefits","workers comp rates","professional liability"],
        "negatives":  ["insurance exam","licensing","study material","actuarial"],
    },
    "Dental / Healthcare": {
        "subreddits": ["Dentistry","askdentists","HealthInsurance","Invisalign","braces","cosmeticdentistry","DentalHygiene"],
        "intent":     ["looking for a dentist","recommend a good dentist","best cosmetic dentist","where to get invisalign","dental implants worth it","accepting new patients"],
        "pain":       ["dentist recommended unnecessary work","overcharged for dental","crown fell off","bad dental experience","insurance didn't cover","billing error from dentist"],
        "competitors":["Aspen Dental","Smile Direct Club","Byte","Candid","Invisalign","Heartland Dental"],
        "trends":     ["all on 4 implants","dental tourism","dental savings plan","same day crowns","dental membership plan"],
        "negatives":  ["dental school","dental student","NBDE exam"],
    },
    "Fitness / Gyms / Personal Training": {
        "subreddits": ["fitness","xxfitness","bodybuilding","personaltraining","loseit","crossfit","yoga","running"],
        "intent":     ["looking for a personal trainer","recommend a gym","online coaching worth it","need a nutrition coach","best gym in","thinking of joining","weight loss coach"],
        "pain":       ["trainer ghosted me","wasted money on gym","no results after months","trainer had no plan","gym is always packed","cancelled my membership"],
        "competitors":["Planet Fitness","Equinox","CrossFit","Orange Theory","F45","Peloton","MyFitnessPal","Noom"],
        "trends":     ["zone 2 cardio","creatine benefits","hybrid athlete","body recomposition","rucking","VO2 max training"],
        "negatives":  ["steroid source","gear","PED","buy online"],
    },
    "Automotive / Dealerships": {
        "subreddits": ["cars","askcarsales","whatcarshouldIbuy","AutoDetailing","mechanics","electricvehicles","AutoRepair"],
        "intent":     ["looking to buy a car","should I buy or lease","recommend a dealer","thinking of trading in","first time car buyer","fleet vehicles for business"],
        "pain":       ["dealer ripped me off","hidden fees","bait and switch","car broke down after purchase","dealer won't honor warranty","trade-in lowballed"],
        "competitors":["CarMax","Carvana","Vroom","TrueCar","Cars.com","AutoTrader","Tesla","Carfax"],
        "trends":     ["EV vs hybrid","best truck for business","fleet management","auto loan rates","extended warranty worth it"],
        "negatives":  ["video game","RC car","toy","model kit"],
    },
    "Recruiting / Staffing / HR": {
        "subreddits": ["recruiting","humanresources","AskHR","smallbusiness","Entrepreneur","sales"],
        "intent":     ["looking for a recruiter","need to hire fast","staffing agency recommendations","outsourcing HR","fractional HR","talent acquisition help"],
        "pain":       ["can't find good candidates","bad hire cost us","recruiter sent unqualified people","high turnover","staffing agency overcharged","payroll errors"],
        "competitors":["LinkedIn Recruiter","Indeed","ZipRecruiter","Monster","Glassdoor","Rippling","Gusto","ADP","BambooHR","Workday"],
        "trends":     ["remote hiring","skills based hiring","AI in recruiting","onboarding automation","retention strategies","fractional employees"],
        "negatives":  ["looking for a job","my resume","interview tips for me","job seeker"],
    },
    "E-Commerce / Retail": {
        "subreddits": ["ecommerce","dropship","FulfillmentByAmazon","shopify","smallbusiness","Entrepreneur","AmazonSeller","Etsy"],
        "intent":     ["looking for an agency","need help with my store","ecommerce consultant","looking for 3PL","Shopify developer","need email marketing","scaling my store"],
        "pain":       ["ROAS tanked","Facebook ads stopped working","Amazon suspended","Shopify fees too high","agency wasted my budget","ad account banned"],
        "competitors":["Shopify","WooCommerce","BigCommerce","Amazon","Etsy","ClickFunnels","Klaviyo","Mailchimp","Triple Whale"],
        "trends":     ["TikTok shop","influencer marketing","UGC content","subscription box","DTC brand","SMS marketing","retention marketing"],
        "negatives":  ["I want to buy","where can I purchase","coupon code","discount"],
    },
    "Marketing / Advertising Agencies": {
        "subreddits": ["digital_marketing","PPC","SEO","marketing","smallbusiness","Entrepreneur","socialmedia","freelance"],
        "intent":     ["looking for a marketing agency","need SEO help","PPC agency recommendations","social media management","need someone to run ads","lead generation agency"],
        "pain":       ["agency didn't deliver","wasted ad spend","no reporting from agency","SEO company took money","leads are garbage","agency went dark","no ROI from marketing"],
        "competitors":["HubSpot","Semrush","Ahrefs","Hootsuite","Sprout Social","Meta Ads","Google Ads","ActiveCampaign","GoHighLevel"],
        "trends":     ["AI content","SGE impact on SEO","zero click searches","performance max","demand gen","LinkedIn ads","video SEO"],
        "negatives":  ["marketing class","homework","school project","marketing major"],
    },
    "SaaS / Tech Startups": {
        "subreddits": ["SaaS","startups","Entrepreneur","indiehackers","smallbusiness","ProductManagement","webdev","sales"],
        "intent":     ["looking for a tool that","alternative to","recommend a SaaS","switching from","need software for","best tool for","CRM recommendations","automation platform"],
        "pain":       ["software too expensive","pricing went up","feature missing","buggy product","support is terrible","contract auto-renewed","integration doesn't work","churning because of"],
        "competitors":["Salesforce","HubSpot","Monday.com","Asana","Notion","Slack","Zapier","Intercom","Zendesk","Pipedrive"],
        "trends":     ["AI feature","usage based pricing","product led growth","churn reduction","customer success","annual vs monthly","open source alternative"],
        "negatives":  ["pirate","crack","free download","nulled","torrent"],
    },
}

SIGNAL_BADGE = {
    "🟢 Buying Intent":      "badge-intent",
    "🔴 Pain / Frustration": "badge-pain",
    "🟠 Competitor Mention": "badge-competitor",
    "🔵 Trend / Research":   "badge-trend",
    "🔍 Boolean Match":      "badge-boolean",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────
def time_ago(ts):
    diff = time.time() - ts
    if diff < 3600:   return f"{int(diff/60)}m ago"
    if diff < 86400:  return f"{int(diff/3600)}h ago"
    return f"{int(diff/86400)}d ago"

def is_hot(ts):
    return (time.time() - ts) < 10800   # < 3 hours

def parse_boolean(query):
    def match(text):
        text_lower = text.lower()
        try:
            expr = re.sub(r'\bAND\b', ' and ', query)
            expr = re.sub(r'\bOR\b',  ' or ',  expr)
            expr = re.sub(r'\bNOT\b', ' not ', expr)
            def t2e(m):
                term = m.group(1) if m.group(1) else m.group(2)
                return f'("{term.lower()}" in text_lower)'
            expr = re.sub(r'"([^"]+)"|(\b[A-Za-z0-9_\-]+\b)', t2e, expr)
            return bool(eval(expr))
        except Exception:
            return False
    return match

def matches_signals(text, template, custom_brands, custom_services, active_signals):
    text_lower = text.lower()
    neg_words = [w.lower() for w in template.get("negatives", [])]
    if any(n in text_lower for n in neg_words):
        return None, []
    triggered = []
    signal_map = {
        "Buying Intent":       ("intent",      "🟢 Buying Intent"),
        "Pain / Frustration":  ("pain",        "🔴 Pain / Frustration"),
        "Competitor Mentions": ("competitors", "🟠 Competitor Mention"),
        "Trend / Research":    ("trends",      "🔵 Trend / Research"),
    }
    for sig_name, (key, label) in signal_map.items():
        if sig_name not in active_signals: continue
        for phrase in template.get(key, []):
            p = phrase.lower()
            words = p.split()
            # Exact substring match OR all individual words present (for multi-word phrases)
            if p in text_lower or (len(words) > 1 and all(w in text_lower for w in words)):
                triggered.append((label, phrase)); break
    for term in custom_brands + custom_services:
        if term.strip() and term.strip().lower() in text_lower:
            triggered.append(("🟠 Competitor Mention", term.strip()))
    if not triggered: return None, []
    return triggered[0][0], list({t[1] for t in triggered})

HEADERS = {"User-Agent": "Mozilla/5.0 LeadPullsScrubber/1.0 (by LeadPulls)"}

def fetch_subreddit(sub, limit=100):
    """Fetch posts from a subreddit using Reddit's public JSON API — no key needed."""
    posts = []
    url = f"https://www.reddit.com/r/{sub}/new.json?limit={min(limit,100)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return posts
        for child in r.json()["data"]["children"]:
            d = child["data"]
            posts.append(d)
        # If we need more than 100, paginate with 'after'
        if limit > 100:
            after = r.json()["data"].get("after")
            if after:
                url2 = f"https://www.reddit.com/r/{sub}/new.json?limit=100&after={after}"
                r2 = requests.get(url2, headers=HEADERS, timeout=10)
                if r2.status_code == 200:
                    for child in r2.json()["data"]["children"]:
                        posts.append(child["data"])
        time.sleep(0.5)   # polite rate limiting
    except Exception:
        pass
    return posts

def scrape_reddit(subreddits, template, custom_brands, custom_services, active_signals, limit=100):
    results = []
    for sub in subreddits:
        for d in fetch_subreddit(sub, limit):
            combined = f"{d.get('title','')} {d.get('selftext','')}"
            signal, terms = matches_signals(combined, template, custom_brands, custom_services, active_signals)
            if signal:
                ts = d.get("created_utc", 0)
                results.append({
                    "signal":    signal,
                    "subreddit": f"r/{sub}",
                    "title":     d.get("title",""),
                    "snippet":   d.get("selftext","")[:220].replace("\n"," "),
                    "matched":   terms,
                    "upvotes":   d.get("score", 0),
                    "comments":  d.get("num_comments", 0),
                    "posted":    datetime.utcfromtimestamp(ts).strftime("%b %d, %Y"),
                    "ts":        ts,
                    "url":       f"https://reddit.com{d.get('permalink','')}",
                    "author":    d.get("author","[deleted]"),
                    "hot":       is_hot(ts),
                })
    return results

def run_boolean_scrape(subreddits, boolean_query, limit=100):
    matcher = parse_boolean(boolean_query)
    results = []
    for sub in subreddits:
        for d in fetch_subreddit(sub, limit):
            combined = f"{d.get('title','')} {d.get('selftext','')}"
            if matcher(combined):
                ts = d.get("created_utc", 0)
                results.append({
                    "signal":    "🔍 Boolean Match",
                    "subreddit": f"r/{sub}",
                    "title":     d.get("title",""),
                    "snippet":   d.get("selftext","")[:220].replace("\n"," "),
                    "matched":   [boolean_query[:50]],
                    "upvotes":   d.get("score", 0),
                    "comments":  d.get("num_comments", 0),
                    "posted":    datetime.utcfromtimestamp(ts).strftime("%b %d, %Y"),
                    "ts":        ts,
                    "url":       f"https://reddit.com{d.get('permalink','')}",
                    "author":    d.get("author","[deleted]"),
                    "hot":       is_hot(ts),
                })
    return results


# ─── PDF Generator ────────────────────────────────────────────────────────────
def generate_pdf(results, industry=""):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.6*inch, rightMargin=0.6*inch,
                            topMargin=0.6*inch, bottomMargin=0.6*inch)
    styles = getSampleStyleSheet()
    navy   = colors.HexColor("#00233F")
    orange = colors.HexColor("#FF5F00")
    story  = []

    # Title
    title_style = ParagraphStyle("title", fontSize=18, fontName="Helvetica-Bold",
                                 textColor=navy, spaceAfter=4)
    sub_style   = ParagraphStyle("sub",   fontSize=10, textColor=colors.HexColor("#888888"), spaceAfter=16)
    story.append(Paragraph("LeadPulls · Reddit Social Listener", title_style))
    story.append(Paragraph(f"{industry}  ·  {len(results)} results  ·  Run {datetime.now().strftime('%b %d, %Y %I:%M %p')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=orange, spaceAfter=14))

    card_title  = ParagraphStyle("ct", fontSize=12, fontName="Helvetica-Bold", textColor=navy, spaceAfter=3)
    card_meta   = ParagraphStyle("cm", fontSize=9,  textColor=colors.HexColor("#666666"), spaceAfter=4)
    card_snip   = ParagraphStyle("cs", fontSize=10, textColor=colors.HexColor("#444444"), leading=14, spaceAfter=4)
    card_match  = ParagraphStyle("ck", fontSize=9,  textColor=orange, spaceAfter=0)
    card_url    = ParagraphStyle("cu", fontSize=9,  textColor=colors.HexColor("#0066cc"), spaceAfter=0)

    for i, r in enumerate(results):
        story.append(Paragraph(r["title"], card_title))
        story.append(Paragraph(
            f"{r['signal']}  ·  {r['subreddit']}  ·  u/{r['author']}  ·  {r['posted']}  ·  ▲{r['upvotes']}  ·  💬{r['comments']}{'  🔥 HOT' if r.get('hot') else ''}",
            card_meta
        ))
        if r["snippet"]:
            story.append(Paragraph(r["snippet"] + "…", card_snip))
        story.append(Paragraph("Matched: " + ", ".join(r["matched"]), card_match))
        story.append(Paragraph(r["url"], card_url))
        story.append(Spacer(1, 8))
        if i < len(results)-1:
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e0e0e0"), spaceAfter=10))

    doc.build(story)
    buf.seek(0)
    return buf


# ─── Session State ─────────────────────────────────────────────────────────────
for k, v in [("email_ok", False), ("results", []), ("ran", False),
             ("handled", set()), ("last_run", None), ("industry_ran", "")]:
    if k not in st.session_state:
        st.session_state[k] = v


# ─── Email Gate ────────────────────────────────────────────────────────────────
if not st.session_state.email_ok:
    st.markdown("""
    <div class="email-gate">
        <div style="font-size:40px;margin-bottom:12px;">🔍</div>
        <h2>Reddit Social Listener</h2>
        <p>Free access — enter your details below and start listening to your market in minutes.</p>
    </div>
    """, unsafe_allow_html=True)
    ca, cb, cc = st.columns([1,2,1])
    with cb:
        name  = st.text_input("", placeholder="Your first name",    label_visibility="collapsed")
        email = st.text_input("", placeholder="you@company.com",    label_visibility="collapsed")
        if st.button("Get Free Access →"):
            if "@" in email and len(name.strip()) > 0:
                st.session_state.email_ok    = True
                st.session_state.user_email  = email
                st.session_state.user_name   = name
                st.rerun()
            else:
                st.error("Enter a valid email and your name.")
    st.stop()


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0 10px;">
        <div style="font-size:22px;font-weight:900;color:#fff;">Lead<span style="color:#FF5F00;">Pulls</span></div>
        <div style="font-size:11px;color:#aec6d8;margin-top:4px;">Reddit Social Listener</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div style="font-size:12px;color:#aec6d8;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Scan Depth</div>', unsafe_allow_html=True)
    post_limit = st.slider("Posts per subreddit", 25, 200, 100, 25)
    st.markdown("---")
    st.markdown('<div style="font-size:11px;color:#aec6d8;text-align:center;line-height:1.6;">Built by <b style="color:#FF5F00;">LeadPulls</b><br>leadpulls.com</div>', unsafe_allow_html=True)


# ─── Top Bar ──────────────────────────────────────────────────────────────────
last_run_str = st.session_state.last_run.strftime("%A, %b %d at %I:%M %p") if st.session_state.last_run else "Not run yet"
st.markdown(f"""
<div class="topbar">
    <div class="topbar-left">
        <div class="topbar-logo">Lead<span>Pulls</span></div>
        <div class="topbar-tag">Reddit Social Listener</div>
    </div>
    <div class="topbar-meta">Last run: <b>{last_run_str}</b></div>
</div>
""", unsafe_allow_html=True)


# ─── Config Panel ─────────────────────────────────────────────────────────────
st.markdown('<div class="config-card">', unsafe_allow_html=True)

# Step 1 — Industry
st.markdown('<div class="step-label">Step 1</div>', unsafe_allow_html=True)
st.markdown('<div class="step-title">What industry are you listening to?</div>', unsafe_allow_html=True)
industry = st.selectbox("", list(TEMPLATES.keys()), label_visibility="collapsed")
template = TEMPLATES[industry]

st.markdown("<br>", unsafe_allow_html=True)

# Step 2 — Signal types
st.markdown('<div class="step-label">Step 2</div>', unsafe_allow_html=True)
st.markdown('<div class="step-title">What signals do you want to capture?</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="signal-card">
        <div class="signal-card-header">
            <span class="signal-icon">🎯</span>
            <span class="signal-name">Buying Intent</span>
        </div>
        <div class="signal-desc">People actively searching for a service, asking for recommendations, or ready to switch providers.</div>
    </div>
    """, unsafe_allow_html=True)
    sig_intent = st.checkbox("Include Buying Intent", value=True)

    st.markdown("""
    <div class="signal-card">
        <div class="signal-card-header">
            <span class="signal-icon">😤</span>
            <span class="signal-name">Pain & Frustration</span>
        </div>
        <div class="signal-desc">Complaints about current providers — unhappy customers who are likely to switch.</div>
    </div>
    """, unsafe_allow_html=True)
    sig_pain = st.checkbox("Include Pain & Frustration", value=True)

with col2:
    st.markdown("""
    <div class="signal-card">
        <div class="signal-card-header">
            <span class="signal-icon">🥊</span>
            <span class="signal-name">Competitor Mentions</span>
        </div>
        <div class="signal-desc">When specific brands or tools are called out — great for spotting unhappy competitor customers.</div>
    </div>
    """, unsafe_allow_html=True)
    sig_competitor = st.checkbox("Include Competitor Mentions", value=True)

    st.markdown("""
    <div class="signal-card">
        <div class="signal-card-header">
            <span class="signal-icon">📈</span>
            <span class="signal-name">Market Trends</span>
        </div>
        <div class="signal-desc">What the industry is actively talking about — useful for content, positioning, and staying ahead.</div>
    </div>
    """, unsafe_allow_html=True)
    sig_trend = st.checkbox("Include Market Trends", value=True)

active_signals = []
if sig_intent:     active_signals.append("Buying Intent")
if sig_pain:       active_signals.append("Pain / Frustration")
if sig_competitor: active_signals.append("Competitor Mentions")
if sig_trend:      active_signals.append("Trend / Research")

st.markdown("<br>", unsafe_allow_html=True)

# Step 3 — Keywords
st.markdown('<div class="step-label">Step 3 — Optional</div>', unsafe_allow_html=True)
st.markdown('<div class="step-title">Any specific keywords to track?</div>', unsafe_allow_html=True)
st.caption("Add brands, competitors, services, or products you want to monitor. Leave blank to use industry defaults only.")
keyword_input = st.text_area("", height=80,
    placeholder="e.g. Datto, SentinelOne, managed IT, endpoint security, your brand name...",
    label_visibility="collapsed")
custom_keywords = [k.strip() for k in re.split(r"[,\n]", keyword_input) if k.strip()]

st.markdown("<br>", unsafe_allow_html=True)

with st.expander("📋 See which subreddits will be scanned"):
    st.markdown("  ·  ".join([f"r/{s}" for s in template["subreddits"]]))

st.markdown('</div>', unsafe_allow_html=True)

run_btn = st.button("🔍  Run Scrub")
if run_btn:
    if not active_signals:
        st.warning("Please select at least one signal type above.")
    else:
        with st.spinner(f"Scanning {len(template['subreddits'])} subreddits for {industry} signals..."):
            try:
                st.session_state.results     = scrape_reddit(template["subreddits"], template, custom_keywords, [], active_signals, post_limit)
                st.session_state.ran         = True
                st.session_state.last_run    = datetime.now()
                st.session_state.handled     = set()
                st.session_state.industry_ran= industry
            except Exception as e:
                st.error(f"Scrape error: {e}")


# ─── Results Dashboard ────────────────────────────────────────────────────────
if st.session_state.ran:
    results  = st.session_state.results
    handled  = st.session_state.handled
    industry = st.session_state.industry_ran

    st.markdown("---")

    if not results:
        st.info("No matches found. Try adjusting signal types, adding more terms, or increasing posts per subreddit.")
    else:
        # ── Stats row ──
        hot_count      = sum(1 for r in results if r["hot"])
        handled_count  = len(handled)
        new_count      = len(results)

        st.markdown(f"""
        <div class="stats-row">
            <div class="stat-box"><div class="stat-number">{new_count}</div><div class="stat-label">New This Run</div></div>
            <div class="stat-box"><div class="stat-number">{sum(1 for r in results if "Intent" in r["signal"])}</div><div class="stat-label">Buying Intent</div></div>
            <div class="stat-box"><div class="stat-number">{hot_count} 🔥</div><div class="stat-label">Hot (&lt;3 h)</div></div>
            <div class="stat-box"><div class="stat-number">{handled_count}</div><div class="stat-label">Handled</div></div>
        </div>
        """, unsafe_allow_html=True)

        # ── Filters ──
        fc1, fc2, fc3, fc4 = st.columns([2,2,2,2])
        with fc1:
            sig_options = list(set(r["signal"] for r in results))
            filter_sig  = st.multiselect("Signal", sig_options, default=sig_options, label_visibility="collapsed")
        with fc2:
            show_hot     = st.checkbox("🔥 Hot only", value=False)
        with fc3:
            show_handled = st.checkbox("Show handled", value=False)
        with fc4:
            sort_by = st.selectbox("Sort", ["Newest","Upvotes","Comments"], label_visibility="collapsed")

        search = st.text_input("", placeholder="🔍  Search posts...", label_visibility="collapsed")

        # ── Apply filters ──
        filtered = [r for r in results if r["signal"] in filter_sig]
        if show_hot:
            filtered = [r for r in filtered if r["hot"]]
        if not show_handled:
            filtered = [r for r in filtered if r["url"] not in handled]
        if search:
            s = search.lower()
            filtered = [r for r in filtered if s in r["title"].lower() or s in r["snippet"].lower()]
        if sort_by == "Upvotes":
            filtered = sorted(filtered, key=lambda x: x["upvotes"], reverse=True)
        elif sort_by == "Comments":
            filtered = sorted(filtered, key=lambda x: x["comments"], reverse=True)
        else:
            filtered = sorted(filtered, key=lambda x: x["ts"], reverse=True)

        # ── Download buttons ──
        dl1, dl2, _ = st.columns([1,1,2])
        df  = pd.DataFrame([{k: v for k, v in r.items() if k != "ts"} for r in filtered])
        csv = df.to_csv(index=False).encode("utf-8")
        with dl1:
            st.download_button("⬇️ Download CSV", data=csv,
                file_name=f"reddit_scrub_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv")
        with dl2:
            pdf_buf = generate_pdf(filtered, industry)
            st.download_button("⬇️ Download PDF", data=pdf_buf,
                file_name=f"reddit_scrub_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf")

        st.markdown(f"**{len(filtered)} results**", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Result cards ──
        for r in filtered:
            badge_cls = SIGNAL_BADGE.get(r["signal"], "badge-boolean")
            tags_html = "".join([f'<span class="rcard-tag">{t}</span>' for t in r["matched"]])
            hot_html  = '<span class="badge-hot">🔥 HOT</span>' if r["hot"] else ""
            is_done   = r["url"] in handled

            st.markdown(f"""
            <div class="rcard" style="opacity:{'0.5' if is_done else '1'};">
                <div class="rcard-top">
                    <span class="badge-sub">{r['subreddit']}</span>
                    <span class="badge-sig {badge_cls}">{r['signal']}</span>
                    {hot_html}
                </div>
                <div class="rcard-title"><a href="{r['url']}" target="_blank">{r['title']}</a></div>
                {"<div class='rcard-snippet'>" + r['snippet'] + "...</div>" if r['snippet'] else ""}
                <div class="rcard-tags">{tags_html}</div>
                <div class="rcard-footer">
                    <b>u/{r['author']}</b> · {time_ago(r['ts'])} · ▲ {r['upvotes']} · 💬 {r['comments']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            hcol, jcol, _ = st.columns([1, 1, 4])
            with hcol:
                label = "Undo Handled" if is_done else "Mark Handled"
                if st.button(label, key=f"h_{r['url']}"):
                    if r["url"] in handled:
                        st.session_state.handled.discard(r["url"])
                    else:
                        st.session_state.handled.add(r["url"])
                    st.rerun()
            with jcol:
                st.link_button("Jump In →", r["url"])
