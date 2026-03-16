"""
FDA RADAR v11 — Ottimizzato per Streamlit Cloud Free
Scansione progressiva, risultati mostrati man mano
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="FDA Radar", page_icon="favicon.png", layout="wide")

DATA_AGG = "2026-03-16"
CAP_MIN, CAP_MAX = 200_000_000, 2_000_000_000

WATCHLIST = [
    ("ALDX","Aldeyra Therapeutics"),
    ("RCKT","Rocket Pharmaceuticals"),
    ("OCGN","Ocugen"),
    ("MNMD","MindMed"),
    ("PDSB","PDS Biotechnology"),
    ("XENE","Xenon Pharmaceuticals"),
    ("BEAM","Beam Therapeutics"),
    ("EDIT","Editas Medicine"),
    ("VERV","Verve Therapeutics"),
    ("IMVT","Immunovant"),
    ("DAWN","Day One Biopharmaceuticals"),
    ("TVTX","Travere Therapeutics"),
    ("VKTX","Viking Therapeutics"),
    ("VRDN","Viridian Therapeutics"),
    ("VERA","Vera Therapeutics"),
    ("PLRX","Pliant Therapeutics"),
]

PDUFA_LIST = [
    {"ticker":"ALDX","drug":"Reproxalap","pdufa":"2026-03-16","crl":2,"labeling":True,
     "nota":"3a richiesta dopo 2 bocciature. FDA sta scrivendo il foglietto."},
    {"ticker":"RCKT","drug":"Kresladi","pdufa":"2026-03-28","crl":1,"labeling":False,
     "nota":"Terapia genica. 100% sopravvivenza. 1 bocciatura precedente."},
]

PHASE_DATA = {
    "3":{"ok":58,"pos":"+20-60%","neg":"-50-80%","label":"Phase 3"},
    "2":{"ok":29,"pos":"+30-80%","neg":"-40-70%","label":"Phase 2"},
    "1":{"ok":52,"pos":"+15-40%","neg":"-20-50%","label":"Phase 1"},
}

ENDPOINT_IT = {
    "overall survival":"Sopravvivenza","progression-free survival":"Senza peggioramento",
    "progression free survival":"Senza peggioramento",
    "objective response rate":"% tumore ridotto","overall response rate":"% miglioramento",
    "complete response":"% tumore scomparso","adverse events":"Effetti collaterali",
    "safety":"Sicurezza","hba1c":"Controllo diabete","pain":"Riduzione dolore",
    "quality of life":"Qualita vita","ocular discomfort":"Fastidio occhi",
    "seizure frequency":"Crisi epilettiche","change in bmi":"Cambio peso",
}

def ep_it(text):
    if not text: return "Non specificato"
    for k,v in ENDPOINT_IT.items():
        if k in text.lower(): return v
    return text[:50]


def get_stock(ticker):
    """Singola chiamata yfinance con gestione errori."""
    try:
        info = yf.Ticker(ticker).fast_info
        price = float(info.get("lastPrice",0) or 0)
        prev = float(info.get("previousClose",price) or price)
        cap = int(info.get("marketCap",0) or 0)
        change = round(((price-prev)/prev*100),2) if prev else 0
        return {"price":round(price,2),"change":change,"cap":cap,
                "cap_str":f"${cap/1e9:.2f}B" if cap>=1e9 else f"${cap/1e6:.0f}M" if cap>=1e6 else "N/D",
                "ok":cap>0}
    except:
        pass
    # Fallback: chiamata completa
    try:
        t = yf.Ticker(ticker)
        info = t.info
        price = info.get("currentPrice") or info.get("regularMarketPrice",0)
        prev = info.get("previousClose",price)
        cap = info.get("marketCap",0)
        change = round(((price-prev)/prev*100),2) if prev else 0
        vol_now = info.get("volume",0) or 0
        vol_avg = info.get("averageVolume",0) or 1
        vol_ratio = round(vol_now/vol_avg,2) if vol_avg else 0
        si = info.get("shortPercentOfFloat",0) or 0
        if si and si < 1: si *= 100
        return {"price":round(price,2),"change":change,"cap":cap,
                "cap_str":f"${cap/1e9:.2f}B" if cap>=1e9 else f"${cap/1e6:.0f}M" if cap>=1e6 else "N/D",
                "vol_ratio":vol_ratio,"short":round(si,1),"ok":cap>0}
    except:
        return {"price":0,"change":0,"cap":0,"cap_str":"N/D","vol_ratio":0,"short":0,"ok":False}


def get_trials(company):
    try:
        r = requests.get("https://clinicaltrials.gov/api/v2/studies", params={
            "query.spons":company,
            "filter.overallStatus":"RECRUITING|ACTIVE_NOT_RECRUITING|ENROLLING_BY_INVITATION|NOT_YET_RECRUITING",
            "pageSize":8,
            "fields":"NCTId,BriefTitle,Phase,Condition,EnrollmentInfo,DesignInfo,PrimaryOutcome,PrimaryCompletionDate",
        }, timeout=8)
        if r.status_code!=200: return []
        out=[]
        for s in r.json().get("studies",[]):
            p=s.get("protocolSection",{})
            ident=p.get("identificationModule",{})
            stat=p.get("statusModule",{})
            des=p.get("designModule",{})
            cond=p.get("conditionsModule",{})
            outc=p.get("outcomesModule",{})
            phases=des.get("phases",[]) if des else []
            ei=des.get("enrollmentInfo",{}) if des else {}
            di=des.get("designInfo",{}) if des else {}
            mi=di.get("maskingInfo",{}) if di else {}
            po=outc.get("primaryOutcomes",[]) if outc else []
            pcd=stat.get("primaryCompletionDateStruct",{}) if stat else {}
            out.append({
                "nct":ident.get("nctId",""),
                "title":ident.get("briefTitle",""),
                "phase":", ".join(phases) if phases else "N/A",
                "conditions":", ".join(cond.get("conditions",[])[:2]) if cond else "N/D",
                "enrollment":ei.get("count",0) if ei else 0,
                "mask":mi.get("masking","") if mi else "",
                "is_rand":"RANDOMIZED" in (di.get("allocation","").upper()) if di else False,
                "endpoint":po[0].get("measure","") if po else "",
                "completion":pcd.get("date","") if pcd else "",
            })
        return out
    except:
        return []


def calc_window(completion_str, phase_str):
    try:
        if len(completion_str)==7:
            cd=datetime.strptime(completion_str+"-28","%Y-%m-%d")
        elif len(completion_str)>=10:
            cd=datetime.strptime(completion_str[:10],"%Y-%m-%d")
        else: return None
    except: return None
    ws=cd+timedelta(weeks=2); we=cd+timedelta(weeks=8)
    p=phase_str.upper().replace(" ","")
    if "PHASE3" in p: pkey="3"
    elif "PHASE2" in p: pkey="2"
    elif "PHASE1" in p: pkey="1"
    else: return None
    rup={"3":45,"2":30,"1":15}[pkey]
    rs=ws-timedelta(days=rup); now=datetime.now()
    if now<rs: status="PRESTO"
    elif now<ws: status="RUNUP"
    elif now<=we: status="APERTA"
    else: status="SCADUTA"
    return {"ws":ws,"we":we,"status":status,"pkey":pkey,"pd":PHASE_DATA[pkey]}


def compute_alert(stk, window, pdufa_match):
    signals=[]; alert=0
    if pdufa_match:
        try:
            g=(datetime.strptime(pdufa_match["pdufa"],"%Y-%m-%d")-datetime.now()).days
        except: g=-1
        if 0<=g<=3: signals.append(f"⏰ VERDETTO FDA TRA {g}g"); alert+=4
        elif 0<=g<=14: signals.append(f"📅 Verdetto FDA tra {g}g"); alert+=3
        if pdufa_match.get("labeling"): signals.append("🏷️ FDA scrive il foglietto"); alert+=2
    if window:
        if window["status"]=="APERTA": signals.append("🔴 FINESTRA APERTA"); alert+=4
        elif window["status"]=="RUNUP": signals.append("🟡 Zona pre-risultati"); alert+=2
    vr = stk.get("vol_ratio",0)
    if vr>=3: signals.append(f"🔥 VOLUME {vr}x media"); alert+=3
    elif vr>=2: signals.append(f"📈 Volume {vr}x"); alert+=2
    elif vr>=1.5: signals.append(f"📊 Volume {vr}x"); alert+=1
    si = stk.get("short",0)
    if si>=20: signals.append(f"🐻 Short {si}% — squeeze possibile"); alert+=2
    elif si>=10: signals.append(f"🐻 Short {si}%"); alert+=1
    return signals, min(alert,10)


# ═══════════════════════════════
# APP
# ═══════════════════════════════

st.title("📡 FDA Radar")
st.caption("Anticipa QUANDO il titolo si muovera. Rileva SE qualcuno si sta posizionando.")

with st.expander("Come leggere i segnali"):
    st.write("""
- **Volume/media 3x+** = qualcuno si posiziona pesante
- **Volume/media 2x** = attivita sopra la norma
- **Short alto + notizia positiva** = possibile squeeze
- **Finestra APERTA** = risultati trial possono uscire ora
- **RUNUP** = zona pre-risultati, mercato si muove in anticipo

Volume alto NON dice se comprano o vendono.
Volume + prezzo sale = comprano. Volume + prezzo scende = vendono.
""")

st.subheader("Movimenti storici per fase")
c1,c2,c3 = st.columns(3)
c1.metric("Phase 1","52% successo","ok +15-40% | ko -20-50%")
c2.metric("Phase 2","29% successo","ok +30-80% | ko -40-70%")
c3.metric("Phase 3","58% successo","ok +20-60% | ko -50-80%")
st.divider()

# ═══════════════════════════════
# SCANSIONE PROGRESSIVA
# ═══════════════════════════════

st.subheader("Scansione in corso...")

results_hot = []
results_silent = []
status_text = st.empty()
results_container = st.container()

for i, (ticker, company) in enumerate(WATCHLIST):
    status_text.caption(f"Scansione {i+1}/{len(WATCHLIST)}: {ticker} ({company})...")

    stk = get_stock(ticker)

    if not stk["ok"]:
        continue
    if not (CAP_MIN <= stk["cap"] <= CAP_MAX):
        continue

    trials = get_trials(company)
    pdufa_match = next((p for p in PDUFA_LIST if p["ticker"]==ticker), None)

    best_w = None
    for t in trials:
        w = calc_window(t["completion"], t["phase"])
        if w and w["status"] in ("APERTA","RUNUP"):
            if best_w is None or w["status"]=="APERTA":
                best_w = w

    signals, alert = compute_alert(stk, best_w, pdufa_match)

    item = {"ticker":ticker,"company":company,"stk":stk,"trials":trials,
            "pdufa":pdufa_match,"signals":signals,"alert":alert}

    if alert > 0:
        results_hot.append(item)
    else:
        results_silent.append(item)

status_text.empty()

# ═══════════════════════════════
# RISULTATI
# ═══════════════════════════════

results_hot.sort(key=lambda x: -x["alert"])

st.subheader(f"📡 {len(results_hot)} titoli con segnali attivi")

if not results_hot:
    st.info("Nessun titolo con segnali attivi al momento. I mercati sono calmi o la scansione non ha trovato anomalie.")

for item in results_hot:
    stk = item["stk"]
    alert = item["alert"]

    if alert>=7: badge = "🔴 ALTO"
    elif alert>=4: badge = "🟡 MEDIO"
    else: badge = "🔵 BASSO"

    st.markdown(f"### {item['ticker']} — {item['company']}")
    st.caption(f"Allerta: {badge} ({alert}/10)")

    m1,m2,m3 = st.columns(3)
    m1.metric("Prezzo", f"${stk['price']}", f"{stk['change']:+.1f}%",
              delta_color="normal" if stk["change"]>=0 else "inverse")
    m2.metric("Market Cap", stk["cap_str"])
    vr = stk.get("vol_ratio",0)
    m3.metric("Vol/Media", f"{vr}x" if vr else "N/D")

    for sig in item["signals"]:
        st.write(sig)

    if item["pdufa"]:
        pm = item["pdufa"]
        try:
            g = (datetime.strptime(pm["pdufa"],"%Y-%m-%d")-datetime.now()).days
            if g >= 0:
                st.info(f"📅 **VERDETTO FDA: {pm['pdufa']}** ({g}g) — {pm['drug']}. {pm['nota']}")
        except: pass

    with st.expander(f"Trial ({len(item['trials'])}) — {item['ticker']}"):
        if not item["trials"]:
            st.write("Nessun trial trovato su ClinicalTrials.gov.")
        for t in item["trials"]:
            w = calc_window(t["completion"], t["phase"])
            ep = ep_it(t["endpoint"])
            ph = t["phase"].upper().replace(" ","")
            pkey = "3" if "PHASE3" in ph else "2" if "PHASE2" in ph else "1" if "PHASE1" in ph else None
            pd_info = PHASE_DATA.get(pkey,{})

            sol=0
            if t["enrollment"] and t["enrollment"]>=500: sol+=3
            elif t["enrollment"] and t["enrollment"]>=100: sol+=2
            elif t["enrollment"]: sol+=1
            if pkey=="3": sol+=2
            elif pkey=="2": sol+=1
            if "DOUBLE" in (t.get("mask","").upper()): sol+=2
            elif "SINGLE" in (t.get("mask","").upper()): sol+=1
            if t.get("is_rand"): sol+=1
            sol_lbl = "ALTA" if sol>=7 else "MEDIA" if sol>=4 else "BASSA"

            st.write(f"**{t['title'][:90]}**")
            st.caption(f"{t['phase']} | {t['conditions']} | {t['enrollment'] or '?'} paz. | Solidita: **{sol_lbl}**")
            st.caption(f"Endpoint: **{ep}**")
            if pd_info:
                st.caption(f"Successo: **{pd_info['ok']}%** | ok: **{pd_info['pos']}** | ko: **{pd_info['neg']}**")
            if w:
                if w["status"]=="APERTA":
                    st.error(f"FINESTRA APERTA — {w['ws'].strftime('%d/%m')} - {w['we'].strftime('%d/%m/%Y')}")
                elif w["status"]=="RUNUP":
                    st.warning(f"RUNUP — {w['ws'].strftime('%d/%m')} - {w['we'].strftime('%d/%m/%Y')}")
                elif w["status"]=="PRESTO":
                    st.caption(f"Finestra: {w['ws'].strftime('%d/%m')} - {w['we'].strftime('%d/%m/%Y')}")
            st.caption(f"[{t['nct']}](https://clinicaltrials.gov/study/{t['nct']})")
            st.divider()

    st.divider()

# Silenziosi
if results_silent:
    with st.expander(f"Titoli senza segnali ({len(results_silent)})"):
        for item in results_silent:
            st.caption(f"**{item['ticker']}** — {item['company']} | {item['stk']['cap_str']} | ${item['stk']['price']} | {len(item['trials'])} trial")

st.divider()
st.caption(f"v11 | PDUFA: {DATA_AGG} | App educativa — non e consulenza finanziaria")
