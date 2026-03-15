"""
POTENTIAL FDA APPROVAL v7.0 — Con Lettore Protocolli
Livello 1: yfinance (prezzi + market cap) — AUTO
Livello 2: ClinicalTrials.gov API v2 (fasi + protocolli) — AUTO
Livello 3: PDUFA dates + news (hardcoded) — MANUALE

NOVITA v7: Traduzione automatica protocolli clinici in italiano
- Endpoint primario tradotto
- Design dello studio spiegato
- Solidita del trial valutata
- Numero pazienti contestualizzato

pip install streamlit yfinance pandas requests
streamlit run potential_fda_approval.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Potential FDA Approval", page_icon="🧬", layout="wide")

DATA_AGG = "2026-03-15"
CAP_MIN = 200_000_000
CAP_MAX = 2_000_000_000

st.markdown("""<style>
.stApp {background: #020617}
[data-testid="stMetric"] {background:#1e293b;border:1px solid #334155;border-radius:12px;padding:12px}
[data-testid="stSidebar"] {background:#0f172a}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# TRADUTTORE PROTOCOLLI — il cuore della v7
# ══════════════════════════════════════════════════

# Dizionario endpoint -> italiano semplice
ENDPOINT_DICT = {
    "overall survival": ("Sopravvivenza totale", "Quanto tempo in piu vivono i pazienti rispetto a chi non prende il farmaco"),
    "progression-free survival": ("Sopravvivenza senza peggioramento", "Quanto tempo passa prima che la malattia peggiori"),
    "progression free survival": ("Sopravvivenza senza peggioramento", "Quanto tempo passa prima che la malattia peggiori"),
    "objective response rate": ("Tasso di risposta", "Percentuale di pazienti in cui il tumore si riduce"),
    "complete response": ("Risposta completa", "Percentuale di pazienti in cui il tumore scompare del tutto"),
    "overall response rate": ("Tasso di risposta totale", "Quanti pazienti mostrano un miglioramento misurabile"),
    "change in bmi": ("Cambio nel peso corporeo (BMI)", "Quanto peso perdono i pazienti"),
    "adverse events": ("Effetti collaterali", "Quanti e quali problemi causa il farmaco"),
    "safety": ("Sicurezza", "Il farmaco e sicuro? Che effetti negativi ha?"),
    "hba1c": ("Emoglobina glicata (HbA1c)", "Misura del controllo del diabete negli ultimi 3 mesi"),
    "pain": ("Dolore", "Quanto si riduce il dolore dei pazienti"),
    "quality of life": ("Qualita della vita", "I pazienti si sentono meglio nel quotidiano?"),
    "event-free survival": ("Sopravvivenza senza eventi", "Quanto tempo prima che succeda qualcosa di brutto (ricaduta, morte, ecc)"),
    "disease-free survival": ("Sopravvivenza senza malattia", "Il paziente resta senza segni della malattia"),
    "duration of response": ("Durata della risposta", "Per quanto tempo il miglioramento dura"),
    "time to progression": ("Tempo al peggioramento", "Quanto passa prima che la malattia riparta"),
    "ocular discomfort": ("Fastidio oculare", "Quanto si riduce il fastidio agli occhi"),
    "best corrected visual acuity": ("Vista corretta", "Quanto migliora la vista con le lenti"),
    "intraocular pressure": ("Pressione dell'occhio", "La pressione dentro l'occhio si normalizza?"),
    "seizure frequency": ("Frequenza crisi epilettiche", "Quante crisi in meno ha il paziente"),
    "tumor size": ("Dimensione del tumore", "Il tumore si rimpicciolisce?"),
    "biomarker": ("Marcatore biologico", "Un valore nel sangue/liquido che indica se il farmaco agisce"),
    "pharmacokinetics": ("Come il corpo gestisce il farmaco", "Quanto velocemente entra ed esce dal corpo"),
    "dose limiting toxicity": ("Tossicita da dose", "Qual e la dose massima prima che diventi pericoloso"),
    "maximum tolerated dose": ("Dose massima tollerata", "Quanta medicina si puo dare senza troppi effetti negativi"),
}

DESIGN_DICT = {
    "RANDOMIZED": ("Randomizzato", "I pazienti sono assegnati a caso al farmaco o al placebo — metodo piu affidabile"),
    "NON_RANDOMIZED": ("Non randomizzato", "I medici decidono chi prende cosa — meno affidabile"),
    "SINGLE_GROUP": ("Gruppo singolo", "Tutti prendono il farmaco, nessun confronto diretto"),
    "PARALLEL": ("Gruppi paralleli", "Un gruppo prende il farmaco, l'altro il placebo, confronto diretto"),
    "CROSSOVER": ("Crossover", "I pazienti provano sia il farmaco che il placebo in momenti diversi"),
    "SEQUENTIAL": ("Sequenziale", "I pazienti vengono arruolati a ondate successive"),
}

MASKING_DICT = {
    "NONE": ("Aperto", "Tutti sanno chi prende cosa — meno affidabile ma necessario per certi farmaci"),
    "SINGLE": ("Cieco singolo", "Il paziente non sa se prende il farmaco vero — abbastanza affidabile"),
    "DOUBLE": ("Doppio cieco", "Ne il paziente ne il medico sanno chi prende cosa — il metodo piu affidabile"),
    "TRIPLE": ("Triplo cieco", "Nemmeno chi analizza i dati sa chi ha preso cosa — massima affidabilita"),
    "QUADRUPLE": ("Quadruplo cieco", "Nessuno sa nulla fino alla fine — blindatura totale"),
}

STATUS_DICT = {
    "RECRUITING": ("Sta cercando pazienti", "🟢"),
    "ACTIVE_NOT_RECRUITING": ("In corso, pazienti gia dentro", "🟡"),
    "ENROLLING_BY_INVITATION": ("Solo su invito", "🔵"),
    "NOT_YET_RECRUITING": ("Non ancora iniziato", "⚪"),
    "COMPLETED": ("Completato", "✅"),
    "TERMINATED": ("Interrotto", "🔴"),
    "SUSPENDED": ("Sospeso", "🟠"),
    "WITHDRAWN": ("Ritirato", "⛔"),
}

def translate_endpoint(text):
    if not text:
        return "Non specificato", "L'endpoint primario non e indicato nel registro"
    low = text.lower()
    for key, (name, desc) in ENDPOINT_DICT.items():
        if key in low:
            return name, desc
    return text[:80], "Endpoint tecnico — consulta il protocollo completo per dettagli"

def translate_design(design_info):
    alloc = design_info.get("allocation", "").upper()
    interv = design_info.get("interventionModel", "").upper()
    mask = design_info.get("maskingInfo", {})
    mask_type = mask.get("masking", "NONE").upper() if mask else "NONE"

    alloc_it = DESIGN_DICT.get(alloc, ("N/D", ""))[0] if alloc else "N/D"
    interv_name, interv_desc = DESIGN_DICT.get(interv, (interv or "N/D", ""))
    mask_name, mask_desc = MASKING_DICT.get(mask_type, ("N/D", ""))

    return alloc_it, interv_name, interv_desc, mask_name, mask_desc

def rate_solidity(enrollment, phase, mask_type, is_randomized):
    score = 0
    reasons = []
    if enrollment and enrollment >= 500:
        score += 3; reasons.append(f"{enrollment} pazienti (campione grande)")
    elif enrollment and enrollment >= 100:
        score += 2; reasons.append(f"{enrollment} pazienti (campione medio)")
    elif enrollment and enrollment > 0:
        score += 1; reasons.append(f"{enrollment} pazienti (campione piccolo)")
    else:
        reasons.append("Numero pazienti non indicato")

    if "3" in str(phase):
        score += 2; reasons.append("Phase 3 (studio avanzato)")
    elif "2" in str(phase):
        score += 1; reasons.append("Phase 2 (studio intermedio)")

    if mask_type and "DOUBLE" in mask_type.upper():
        score += 2; reasons.append("Doppio cieco (metodo affidabile)")
    elif mask_type and "SINGLE" in mask_type.upper():
        score += 1; reasons.append("Cieco singolo")
    else:
        reasons.append("Studio aperto (meno controllato)")

    if is_randomized:
        score += 1; reasons.append("Randomizzato (assegnazione casuale)")

    if score >= 7: label = "ALTA"
    elif score >= 4: label = "MEDIA"
    else: label = "BASSA"

    return label, score, reasons


# ══════════════════════════════════════════════════
# LIVELLO 1: YFINANCE
# ══════════════════════════════════════════════════

@st.cache_data(ttl=600)
def get_stock(ticker):
    try:
        s = yf.Ticker(ticker)
        i = s.info
        p = i.get("currentPrice") or i.get("regularMarketPrice", 0)
        pc = i.get("previousClose", p)
        mc = i.get("marketCap", 0)
        ch = round(((p - pc) / pc * 100), 2) if pc else 0
        return {"price": round(p,2), "change": ch, "cap": mc, "cap_str": _fmt(mc), "name": i.get("shortName", ticker), "ok": mc > 0}
    except:
        return {"price": 0, "change": 0, "cap": 0, "cap_str": "N/D", "name": ticker, "ok": False}

def _fmt(v):
    if v >= 1e9: return f"${v/1e9:.2f}B"
    elif v >= 1e6: return f"${v/1e6:.0f}M"
    elif v > 0: return f"${v:,.0f}"
    return "N/D"


# ══════════════════════════════════════════════════
# LIVELLO 2: CLINICALTRIALS.GOV API v2 (DETTAGLIATO)
# ══════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def get_trials_detailed(company_name):
    try:
        url = "https://clinicaltrials.gov/api/v2/studies"
        params = {
            "query.spons": company_name,
            "filter.overallStatus": "RECRUITING|ACTIVE_NOT_RECRUITING|ENROLLING_BY_INVITATION|NOT_YET_RECRUITING",
            "pageSize": 20,
            "fields": "NCTId,BriefTitle,Phase,OverallStatus,Condition,EnrollmentInfo,"
                      "DesignInfo,PrimaryOutcome,StartDate,PrimaryCompletionDate,"
                      "WhyStopped,ArmGroup,InterventionName",
        }
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return []
        studies = r.json().get("studies", [])
        results = []
        for s in studies:
            proto = s.get("protocolSection", {})
            ident = proto.get("identificationModule", {})
            status_mod = proto.get("statusModule", {})
            design_mod = proto.get("designModule", {})
            cond_mod = proto.get("conditionsModule", {})
            outcomes_mod = proto.get("outcomesModule", {})

            # Phase
            phases = design_mod.get("phases", [])
            phase_str = ", ".join(phases) if phases else "N/A"

            # Conditions
            conditions = cond_mod.get("conditions", [])

            # Enrollment
            enroll_info = design_mod.get("enrollmentInfo", {})
            enrollment = enroll_info.get("count", 0) if enroll_info else 0

            # Design
            design_info = design_mod.get("designInfo", {})
            allocation = design_info.get("allocation", "")
            mask_info = design_info.get("maskingInfo", {})
            mask_type = mask_info.get("masking", "") if mask_info else ""

            # Primary outcomes
            primary_outcomes = outcomes_mod.get("primaryOutcomes", []) if outcomes_mod else []
            primary_endpoint_text = primary_outcomes[0].get("measure", "") if primary_outcomes else ""

            # Completion date
            pcd = status_mod.get("primaryCompletionDateStruct", {})
            pcd_str = pcd.get("date", "N/A") if pcd else "N/A"

            results.append({
                "nct": ident.get("nctId", ""),
                "title": ident.get("briefTitle", "N/A"),
                "phase": phase_str,
                "status": status_mod.get("overallStatus", "N/A"),
                "conditions": conditions,
                "enrollment": enrollment,
                "allocation": allocation,
                "mask_type": mask_type,
                "design_info": design_info,
                "primary_endpoint": primary_endpoint_text,
                "completion": pcd_str,
            })
        return results
    except:
        return []


# ══════════════════════════════════════════════════
# LIVELLO 3: PDUFA HARDCODED
# ══════════════════════════════════════════════════

PDUFA_CATALYSTS = [
    {
        "ticker": "ALDX", "company": "Aldeyra Therapeutics",
        "drug": "Reproxalap", "indication": "Occhio secco",
        "pdufa": "2026-03-16", "phase": "NDA", "review": "Standard",
        "crl": 2, "labeling": True, "tags": ["Fast Track"],
        "summary": "3a sottomissione dopo 2 bocciature. FDA ha condiviso bozza etichetta dic.2025. AbbVie: opzione $100M.",
        "pro": ["Bozza etichetta FDA","Nessun problema sicurezza","AbbVie $100M","Phase 3: P=0.002"],
        "contra": ["2 CRL precedenti","Field trial mancato","FDA ha cambiato richieste"],
        "sources": ["ir.aldeyra.com","Fierce Biotech 16/12/25"],
    },
    {
        "ticker": "RCKT", "company": "Rocket Pharmaceuticals",
        "drug": "Kresladi", "indication": "LAD-I (fatale nei bambini)",
        "pdufa": "2026-03-28", "phase": "BLA", "review": "Standard",
        "crl": 1, "labeling": False, "tags": ["Orphan Drug","Breakthrough Therapy"],
        "summary": "Terapia genica, 100% sopravvivenza nel trial. Ri-sottomissione dopo 1 CRL.",
        "pro": ["100% sopravvivenza","Tutti endpoint raggiunti","Breakthrough+Orphan"],
        "contra": ["1 CRL precedente","Produzione complessa","Mercato ultra-piccolo"],
        "sources": ["ir.rocketpharma.com","CGTLive 14/10/25"],
    },
]

BIOTECH_WATCHLIST = [
    ("ALDX","Aldeyra Therapeutics"),("RCKT","Rocket Pharmaceuticals"),
    ("OCGN","Ocugen"),("MNMD","MindMed"),("PDSB","PDS Biotechnology"),
    ("XENE","Xenon Pharmaceuticals"),("TARS","Tarsus Pharmaceuticals"),
    ("ALEC","Alector"),("BEAM","Beam Therapeutics"),("EDIT","Editas Medicine"),
    ("NTLA","Intellia Therapeutics"),("VERV","Verve Therapeutics"),
    ("IMVT","Immunovant"),("KYMR","Kymera Therapeutics"),
    ("DAWN","Day One Biopharmaceuticals"),("CRNX","Crinetics Pharmaceuticals"),
    ("TVTX","Travere Therapeutics"),("FOLD","Amicus Therapeutics"),
    ("RLAY","Relay Therapeutics"),("KRYS","Krystal Biotech"),
    ("PCVX","Vaxcyte"),("ACLX","Arcellx"),("IDYA","IDEAYA Biosciences"),
    ("RVMD","Revolution Medicines"),("PTGX","Protagonist Therapeutics"),
    ("APLS","Apellis Pharmaceuticals"),("VKTX","Viking Therapeutics"),
    ("CORT","Corcept Therapeutics"),("NUVL","Nuvalent"),
    ("VRDN","Viridian Therapeutics"),("VERA","Vera Therapeutics"),
    ("PLRX","Pliant Therapeutics"),("ASND","Ascendis Pharma"),
]

def giorni(pdufa):
    try: return (datetime.strptime(pdufa, "%Y-%m-%d") - datetime.now()).days
    except: return -999

def indice(item):
    s = 50
    if item.get("labeling"): s += 15
    if item.get("review") == "Priority Review": s += 5
    for t in item.get("tags", []):
        if "Breakthrough" in t: s += 5
        if "Fast" in t: s += 3
        if "Orphan" in t: s += 2
    if "sNDA" in item.get("phase", ""): s += 5
    s -= item.get("crl", 0) * 12
    return max(0, min(s, 99))


# ══════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════

st.markdown(
    '<p style="font-size:2em;font-weight:900;text-align:center;'
    'background:linear-gradient(90deg,#60a5fa,#a78bfa,#f472b6);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0">'
    'Potential FDA Approval</p>', unsafe_allow_html=True)
st.caption("Small/Mid Cap 200M-2B | yfinance + ClinicalTrials.gov API + PDUFA hardcoded")

try:
    obs = (datetime.now() - datetime.strptime(DATA_AGG, "%Y-%m-%d")).days
except: obs = 999
if obs > 14: st.error(f"Dati PDUFA vecchi di {obs} giorni! Aggiorna!")
elif obs > 7: st.warning(f"Dati PDUFA di {obs} giorni fa.")

st.markdown("---")

# ══════════════════════════════════════════════════
# SEZ.1: VERDETTI FDA
# ══════════════════════════════════════════════════

st.markdown("## 1. Verdetti FDA imminenti")
st.caption("Sezione manuale — aggiorna chiedendo all'IA")

active = [c for c in PDUFA_CATALYSTS if 0 <= giorni(c["pdufa"]) <= 30]
active.sort(key=lambda x: giorni(x["pdufa"]))

if not active:
    st.info("Nessun verdetto entro 30 giorni. Aggiorna la lista PDUFA.")

for cat in active:
    g = giorni(cat["pdufa"])
    stk = get_stock(cat["ticker"])
    idx = indice(cat)
    ic = "#22c55e" if idx>=75 else "#f59e0b" if idx>=55 else "#3b82f6" if idx>=35 else "#ef4444"
    pill_bg = "#dc2626" if g<=3 else "#f59e0b" if g<=7 else "#3b82f6"

    st.markdown(f"""<div style="background:linear-gradient(135deg,#0f172a,#1e293b);
    border:1px solid {'#ef4444' if g<=3 else '#334155'};border-radius:14px;padding:16px;margin:8px 0">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:6px;margin-bottom:8px">
    <div><span style="font-size:18px;font-weight:800;color:#f8fafc">{cat['ticker']}</span>
    <span style="font-size:12px;color:#94a3b8;margin-left:6px">{cat['company']}</span>
    <div style="font-size:12px;color:#cbd5e1;margin-top:2px">{cat['drug']} — {cat['indication']}</div></div>
    <span style="background:{pill_bg};color:white;padding:3px 12px;border-radius:16px;font-weight:800;font-size:12px">{'OGGI' if g<=0 else f'{g}g'}</span>
    </div>
    <div style="background:#0f172a;border-radius:8px;padding:8px 12px;font-size:12px;color:#e2e8f0;line-height:1.5;margin-bottom:8px">{cat['summary']}</div>
    <div style="margin-bottom:8px">{"".join(f'<span style="background:#1d4ed8;color:#e2e8f0;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600;margin-right:4px">{t}</span>' for t in cat["tags"])}
    {f'<span style="background:#991b1b;color:#fca5a5;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600">{cat["crl"]} CRL</span>' if cat["crl"]>0 else ""}
    {'<span style="background:#166534;color:#bbf7d0;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600;margin-left:4px">Etichetta in corso</span>' if cat["labeling"] else ""}</div>
    <div style="display:flex;justify-content:space-between;font-size:10px;color:#94a3b8"><span>Indice Fiducia</span><span style="color:{ic};font-weight:700">{idx}/99</span></div>
    <div style="background:#1e293b;border-radius:4px;height:6px;overflow:hidden"><div style="width:{idx/99*100}%;height:100%;background:{ic};border-radius:4px"></div></div>
    <div style="font-size:9px;color:#475569;margin-top:2px">Non e una probabilita. Serve per confrontare.</div>
    </div>""", unsafe_allow_html=True)

    if stk["ok"]:
        p1,p2,p3 = st.columns(3)
        p1.metric("Prezzo", f"${stk['price']}", f"{stk['change']:+.2f}%", delta_color="normal" if stk["change"]>=0 else "inverse")
        p2.metric("Market Cap", stk["cap_str"])
        p3.metric("Verdetto", cat["pdufa"])

    with st.expander(f"Segnali + Fonti — {cat['ticker']}"):
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("**✅ Positivi**")
            for p in cat["pro"]: st.caption(f"• {p}")
        with c2:
            st.markdown("**⚠️ Rischi**")
            for c in cat["contra"]: st.caption(f"• {c}")
        st.markdown("**📰 Fonti**")
        for s in cat["sources"]: st.caption(f"→ {s}")

st.markdown("---")

# ══════════════════════════════════════════════════
# SEZ.2-4: TRIAL PER FASE CON PROTOCOLLI TRADOTTI
# ══════════════════════════════════════════════════

st.markdown("## 2. Trial clinici attivi con protocolli tradotti")
st.caption("Automatico da ClinicalTrials.gov | Filtro market cap 200M-2B | Cache 1 ora")

with st.spinner("Scansione aziende e trial..."):
    in_range = []
    for ticker, company in BIOTECH_WATCHLIST:
        stk = get_stock(ticker)
        if stk["ok"] and CAP_MIN <= stk["cap"] <= CAP_MAX:
            in_range.append((ticker, company, stk))

st.caption(f"{len(in_range)} aziende nel range su {len(BIOTECH_WATCHLIST)} scansionate")

# Collect and group
all_by_phase = {"3": [], "2": [], "1": [], "other": []}
for ticker, company, stk in in_range:
    trials = get_trials_detailed(company)
    for t in trials:
        p = t["phase"].upper().replace(" ","")
        entry = {**t, "ticker": ticker, "company": company, "stk": stk}
        if "PHASE3" in p: all_by_phase["3"].append(entry)
        elif "PHASE2" in p: all_by_phase["2"].append(entry)
        elif "PHASE1" in p: all_by_phase["1"].append(entry)
        else: all_by_phase["other"].append(entry)

section_info = [
    ("3", "🏁 Phase 3 — Ultimo esame", "Migliaia di pazienti. Se passa si va alla FDA. Il piu importante."),
    ("2", "🔬 Phase 2 — Test intermedio", "Il farmaco funziona? A che dose? Centinaia di pazienti."),
    ("1", "🧪 Phase 1 — Primi test", "Sicurezza su pochi volontari. Rischio alto, potenziale alto."),
]

for key, title, desc in section_info:
    trials = all_by_phase[key]
    if not trials:
        continue

    st.markdown(f"### {title}")
    st.caption(desc)

    by_company = {}
    for t in trials:
        k = t["ticker"]
        if k not in by_company:
            by_company[k] = {"company": t["company"], "stk": t["stk"], "trials": []}
        by_company[k]["trials"].append(t)

    for ticker, info in by_company.items():
        stk = info["stk"]
        n = len(info["trials"])
        with st.expander(f"**{ticker}** — {info['company']} | {stk['cap_str']} | ${stk['price']} ({stk['change']:+.1f}%) | {n} trial"):
            for t in info["trials"]:
                # Translate endpoint
                ep_name, ep_desc = translate_endpoint(t["primary_endpoint"])

                # Translate design
                alloc_it, interv_name, interv_desc, mask_name, mask_desc = translate_design(t.get("design_info", {}))

                # Rate solidity
                is_rand = "RANDOMIZED" in t.get("allocation","").upper()
                sol_label, sol_score, sol_reasons = rate_solidity(
                    t["enrollment"], t["phase"], t.get("mask_type",""), is_rand)
                sol_color = "#22c55e" if sol_label=="ALTA" else "#f59e0b" if sol_label=="MEDIA" else "#ef4444"

                # Status
                st_info = STATUS_DICT.get(t["status"], (t["status"], "⚪"))
                conditions_str = ", ".join(t["conditions"][:3]) if t["conditions"] else "N/D"

                # CARD
                st.markdown(f"""<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:14px;margin:6px 0">
                <div style="font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:6px">{t['title']}</div>
                <div style="font-size:11px;color:#94a3b8;margin-bottom:8px">{st_info[1]} {st_info[0]} | Malattia: {conditions_str} | Pazienti: {t['enrollment'] or 'N/D'} | Fine prevista: {t['completion']}</div>
                <div style="background:#1e293b;border-radius:8px;padding:10px;margin-bottom:6px">
                    <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">Endpoint primario — La domanda chiave</div>
                    <div style="font-size:13px;font-weight:700;color:#a5b4fc">{ep_name}</div>
                    <div style="font-size:11px;color:#cbd5e1">{ep_desc}</div>
                </div>
                <div style="background:#1e293b;border-radius:8px;padding:10px;margin-bottom:6px">
                    <div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">Design dello studio</div>
                    <div style="font-size:12px;color:#cbd5e1">
                        Assegnazione: <strong style="color:#e2e8f0">{alloc_it}</strong> |
                        Modello: <strong style="color:#e2e8f0">{interv_name}</strong> |
                        Blindatura: <strong style="color:#e2e8f0">{mask_name}</strong>
                    </div>
                    <div style="font-size:11px;color:#94a3b8;margin-top:2px">{mask_desc}</div>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                        <span style="font-size:10px;color:#64748b">SOLIDITA TRIAL: </span>
                        <span style="background:{sol_color}22;color:{sol_color};padding:2px 8px;border-radius:8px;font-size:11px;font-weight:700">{sol_label} ({sol_score}/8)</span>
                    </div>
                    <a href="https://clinicaltrials.gov/study/{t['nct']}" style="color:#60a5fa;font-size:11px">{t['nct']}</a>
                </div>
                <div style="font-size:10px;color:#475569;margin-top:4px">{"  |  ".join(sol_reasons)}</div>
                </div>""", unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════
# SEZ.5: TABELLA
# ══════════════════════════════════════════════════

st.markdown("## 3. Tutte le aziende nel range")
if in_range:
    rows = []
    for ticker, company, stk in in_range:
        trials = get_trials_detailed(company)
        phases = set()
        for t in trials:
            p = t["phase"].upper()
            if "3" in p: phases.add("Ph3")
            if "2" in p: phases.add("Ph2")
            if "1" in p: phases.add("Ph1")
        pm = next((c for c in PDUFA_CATALYSTS if c["ticker"]==ticker), None)
        rows.append({
            "Ticker": ticker, "Azienda": company, "Cap": stk["cap_str"],
            "Prezzo": f"${stk['price']}", "Var%": f"{stk['change']:+.1f}%",
            "Fasi": " ".join(sorted(phases)) or "—",
            "Trial": len(trials), "PDUFA": pm["pdufa"] if pm else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("---")

# Glossario + limiti
with st.expander("📖 Dizionario 'da bar'"):
    for t,b,d in [("PDUFA","Verdetto","FDA dice SI/NO"),("Phase 1","Primi test","Sicurezza su pochi"),
        ("Phase 2","Test intermedio","Funziona? A che dose?"),("Phase 3","Ultimo esame","Migliaia di pazienti"),
        ("NDA/BLA","Domanda ufficiale","Azienda chiede approvazione"),("CRL","Bocciato con appunti","NO ma spiega cosa correggere"),
        ("Endpoint","La domanda chiave","Cosa deve dimostrare il trial"),
        ("Doppio cieco","Nessuno sa chi prende cosa","Metodo piu affidabile"),
        ("Randomizzato","Assegnazione casuale","Evita trucchi nella selezione pazienti"),
        ("Solidita","Quanto e affidabile il trial","Piu pazienti + doppio cieco + randomizzato = piu solido")]:
        st.caption(f"**{b}** ({t}) — {d}")

with st.expander("Come funziona + limiti onesti"):
    st.markdown("""
| Livello | Fonte | Auto? | Affidabilita |
|---------|-------|-------|-------------|
| Prezzi | yfinance | Si (10min) | Buona, non ufficiale |
| Trial + protocolli | ClinicalTrials.gov API v2 | Si (1h) | Eccellente (gov USA) |
| PDUFA + notizie | Hardcoded | No (settimanale) | Buona se aggiornata |

**Limiti:** yfinance puo fallire su ~10% small cap | ClinicalTrials.gov cerca per nome (non ticker) |
Date PDUFA invecchiano | Traduzione endpoint copre i ~30 piu comuni, il resto mostra l'originale |
Solidita trial e meccanica (non clinica) | L'app NON predice successi
""")

st.caption(f"v7.0 | PDUFA: {DATA_AGG} | App educativa — non e consulenza finanziaria")
