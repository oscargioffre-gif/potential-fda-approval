"""
FDA RADAR v10 — Niente HTML annidato. Solo componenti Streamlit nativi.
pip install streamlit yfinance pandas requests
streamlit run potential_fda_approval.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="FDA Radar", page_icon="📡", layout="wide")

DATA_AGG = "2026-03-15"
CAP_MIN, CAP_MAX = 200_000_000, 2_000_000_000

WATCHLIST = [
    ("ALDX","Aldeyra Therapeutics"),("RCKT","Rocket Pharmaceuticals"),
    ("OCGN","Ocugen"),("MNMD","MindMed"),("PDSB","PDS Biotechnology"),
    ("XENE","Xenon Pharmaceuticals"),("ALEC","Alector"),
    ("BEAM","Beam Therapeutics"),("EDIT","Editas Medicine"),
    ("NTLA","Intellia Therapeutics"),("VERV","Verve Therapeutics"),
    ("IMVT","Immunovant"),("KYMR","Kymera Therapeutics"),
    ("DAWN","Day One Biopharmaceuticals"),("TVTX","Travere Therapeutics"),
    ("FOLD","Amicus Therapeutics"),("RLAY","Relay Therapeutics"),
    ("KRYS","Krystal Biotech"),("PCVX","Vaxcyte"),("ACLX","Arcellx"),
    ("IDYA","IDEAYA Biosciences"),("PTGX","Protagonist Therapeutics"),
    ("APLS","Apellis Pharmaceuticals"),("VKTX","Viking Therapeutics"),
    ("CORT","Corcept Therapeutics"),("VRDN","Viridian Therapeutics"),
    ("VERA","Vera Therapeutics"),("PLRX","Pliant Therapeutics"),
]

PDUFA_LIST = [
    {"ticker":"ALDX","drug":"Reproxalap","pdufa":"2026-03-16","crl":2,"labeling":True,
     "nota":"3a richiesta dopo 2 bocciature. FDA sta scrivendo il foglietto."},
    {"ticker":"RCKT","drug":"Kresladi","pdufa":"2026-03-28","crl":1,"labeling":False,
     "nota":"Terapia genica. 100% sopravvivenza. 1 bocciatura precedente."},
]

PHASE_DATA = {
    "3":{"ok":58,"pos":"+20-60%","neg":"-50-80%","run":45,"label":"Phase 3"},
    "2":{"ok":29,"pos":"+30-80%","neg":"-40-70%","run":30,"label":"Phase 2"},
    "1":{"ok":52,"pos":"+15-40%","neg":"-20-50%","run":15,"label":"Phase 1"},
}

ENDPOINT_IT = {
    "overall survival":"Sopravvivenza","progression-free survival":"Senza peggioramento",
    "progression free survival":"Senza peggioramento",
    "objective response rate":"% tumore ridotto","overall response rate":"% miglioramento",
    "complete response":"% tumore scomparso","adverse events":"Effetti collaterali",
    "safety":"Sicurezza","hba1c":"Controllo diabete","pain":"Riduzione dolore",
    "quality of life":"Qualita vita","ocular discomfort":"Fastidio occhi",
    "seizure frequency":"Crisi epilettiche","tumor size":"Dimensione tumore",
    "change in bmi":"Cambio peso","biomarker":"Marcatore biologico",
}

def ep_it(text):
    if not text: return "Non specificato"
    for k,v in ENDPOINT_IT.items():
        if k in text.lower(): return v
    return text[:50]


# ══════════════ YFINANCE ══════════════

@st.cache_data(ttl=600)
def scan_stock(ticker):
    try:
        s = yf.Ticker(ticker)
        info = s.info
        hist = s.history(period="3mo")
        price = info.get("currentPrice") or info.get("regularMarketPrice",0)
        prev = info.get("previousClose",price)
        cap = info.get("marketCap",0)
        change = round(((price-prev)/prev*100),2) if prev else 0
        vol_now = info.get("volume",0) or 0
        vol_avg = info.get("averageVolume",0) or 1
        vol_ratio = round(vol_now/vol_avg,2) if vol_avg else 0
        si = info.get("shortPercentOfFloat",0) or 0
        if si < 1: si *= 100
        vol_trend = "neutro"
        if len(hist)>=10:
            rv = hist["Volume"].tail(5).mean()
            ov = hist["Volume"].tail(20).head(15).mean()
            if ov>0:
                vc = (rv-ov)/ov
                if vc>0.5: vol_trend="spike"
                elif vc>0.2: vol_trend="crescente"
                elif vc<-0.2: vol_trend="calante"
        price_trend = "neutro"
        if len(hist)>=10:
            p5 = hist["Close"].tail(5).mean()
            p20 = hist["Close"].tail(20).mean()
            if p20>0:
                pt = (p5-p20)/p20
                if pt>0.05: price_trend="sale"
                elif pt<-0.05: price_trend="scende"
        return {"price":round(price,2),"change":change,"cap":cap,
                "cap_str":f"${cap/1e9:.2f}B" if cap>=1e9 else f"${cap/1e6:.0f}M" if cap>=1e6 else "N/D",
                "vol_ratio":vol_ratio,"vol_trend":vol_trend,"price_trend":price_trend,
                "short":round(si,1),"ok":cap>0,"name":info.get("shortName",ticker)}
    except:
        return {"price":0,"change":0,"cap":0,"cap_str":"N/D","vol_ratio":0,
                "vol_trend":"errore","price_trend":"errore","short":0,"ok":False,"name":ticker}


# ══════════════ CLINICALTRIALS.GOV ══════════════

@st.cache_data(ttl=3600)
def scan_trials(company):
    try:
        r = requests.get("https://clinicaltrials.gov/api/v2/studies", params={
            "query.spons":company,
            "filter.overallStatus":"RECRUITING|ACTIVE_NOT_RECRUITING|ENROLLING_BY_INVITATION|NOT_YET_RECRUITING",
            "pageSize":15,
            "fields":"NCTId,BriefTitle,Phase,OverallStatus,Condition,EnrollmentInfo,DesignInfo,PrimaryOutcome,PrimaryCompletionDate",
        }, timeout=15)
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
                "nct":ident.get("nctId",""),"title":ident.get("briefTitle",""),
                "phase":", ".join(phases) if phases else "N/A",
                "conditions":", ".join(cond.get("conditions",[])[:2]) if cond else "N/D",
                "enrollment":ei.get("count",0) if ei else 0,
                "mask":mi.get("masking","") if mi else "",
                "is_rand":"RANDOMIZED" in (di.get("allocation","").upper()) if di else False,
                "endpoint":po[0].get("measure","") if po else "",
                "completion":pcd.get("date","") if pcd else "",
            })
        return out
    except: return []


# ══════════════ FINESTRA CATALIZZATORE ══════════════

def calc_window(completion_str, phase_str):
    try:
        if len(completion_str)==7:
            cd=datetime.strptime(completion_str+"-28","%Y-%m-%d")
        elif len(completion_str)>=10:
            cd=datetime.strptime(completion_str[:10],"%Y-%m-%d")
        else: return None
    except: return None
    now=datetime.now()
    ws=cd+timedelta(weeks=2); we=cd+timedelta(weeks=8)
    p=phase_str.upper().replace(" ","")
    if "PHASE3" in p: pkey="3";rup=45
    elif "PHASE2" in p: pkey="2";rup=30
    elif "PHASE1" in p: pkey="1";rup=15
    else: return None
    rs=ws-timedelta(days=rup)
    if now<rs: status="PRESTO"
    elif now<ws: status="RUNUP"
    elif now<=we: status="APERTA"
    else: status="SCADUTA"
    return {"ws":ws,"we":we,"rs":rs,"status":status,"pkey":pkey,"pd":PHASE_DATA[pkey],"cd":cd}


# ══════════════ SEGNALE COMBINATO ══════════════

def compute_signal(stk, window, pdufa_match):
    signals=[]; alert=0
    if pdufa_match:
        g=(datetime.strptime(pdufa_match["pdufa"],"%Y-%m-%d")-datetime.now()).days
        if 0<=g<=3: signals.append(f"⏰ VERDETTO FDA TRA {g} GIORNI"); alert+=4
        elif 0<=g<=14: signals.append(f"📅 Verdetto FDA tra {g} giorni"); alert+=3
        if pdufa_match.get("labeling"): signals.append("🏷️ FDA sta scrivendo il foglietto"); alert+=2
    if window:
        if window["status"]=="APERTA": signals.append("🔴 FINESTRA APERTA — risultati possono uscire ora"); alert+=4
        elif window["status"]=="RUNUP": signals.append("🟡 Zona pre-risultati — mercato si posiziona"); alert+=2
    if stk["vol_ratio"]>=3: signals.append(f"🔥 VOLUME {stk['vol_ratio']}x — qualcuno si posiziona pesante"); alert+=3
    elif stk["vol_ratio"]>=2: signals.append(f"📈 Volume {stk['vol_ratio']}x la media"); alert+=2
    elif stk["vol_ratio"]>=1.5: signals.append(f"📊 Volume {stk['vol_ratio']}x"); alert+=1
    if stk["vol_trend"]=="spike": signals.append("⚡ Spike volume ultimi 5 giorni"); alert+=2
    elif stk["vol_trend"]=="crescente": signals.append("↗️ Volume in crescita"); alert+=1
    if stk["price_trend"]=="sale": signals.append("🟢 Prezzo in salita (5gg > 20gg)")
    elif stk["price_trend"]=="scende": signals.append("🔻 Prezzo in discesa (5gg < 20gg)")
    if stk["short"]>=20: signals.append(f"🐻 Short {stk['short']}% — possibile squeeze se notizia positiva"); alert+=2
    elif stk["short"]>=10: signals.append(f"🐻 Short {stk['short']}%"); alert+=1
    return signals, min(alert,10)


# ══════════════════════════════════════════════════
# APP — solo componenti Streamlit nativi
# ══════════════════════════════════════════════════

st.title("📡 FDA Radar")
st.caption("Anticipa QUANDO il titolo si muovera. Rileva SE qualcuno si sta posizionando.")

with st.expander("Come leggere i segnali (30 secondi)"):
    st.write("""
**I fondi non annunciano che comprano. Ma lasciano tracce nel volume.**

- **Volume/media 3x+** = qualcuno si sta posizionando pesantemente
- **Volume/media 2x** = attivita sopra la norma
- **Spike 5gg** = ultimi 5 giorni molto sopra i precedenti 15
- **Short alto** = tanti scommettono contro. Se notizia positiva → squeeze
- **Finestra APERTA** = i risultati del trial possono uscire in qualsiasi momento
- **RUNUP** = zona pre-risultati, il mercato si muove in anticipo

**Volume alto NON dice se comprano o vendono.**
Volume + prezzo sale = comprano. Volume + prezzo scende = vendono.

**Allerta 0-10** = timing + volume + short. Piu alto = piu caldo. Non significa "compra".
""")

# Pattern storici
st.subheader("Movimenti storici per fase")
c1,c2,c3 = st.columns(3)
c1.metric("Phase 1", "52% successo", "Se ok: +15-40%")
c2.metric("Phase 2", "29% successo", "Se ok: +30-80%")
c3.metric("Phase 3", "58% successo", "Se ok: +20-60%")
st.caption("Se fallisce: Phase 1 -20-50% | Phase 2 -40-70% | Phase 3 -50-80% | PDUFA bocciato -50-90%")

st.divider()

# SCAN
with st.spinner("Scansione aziende..."):
    radar = []
    for ticker, company in WATCHLIST:
        stk = scan_stock(ticker)
        if not stk["ok"] or not (CAP_MIN<=stk["cap"]<=CAP_MAX):
            continue
        trials = scan_trials(company)
        pdufa_match = next((p for p in PDUFA_LIST if p["ticker"]==ticker), None)
        best_w = None; best_t = None
        for t in trials:
            w = calc_window(t["completion"], t["phase"])
            if w and w["status"] in ("APERTA","RUNUP"):
                if best_w is None or (w["status"]=="APERTA" and best_w["status"]!="APERTA"):
                    best_w=w; best_t=t
        signals, alert = compute_signal(stk, best_w, pdufa_match)
        if alert > 0:
            radar.append({"ticker":ticker,"company":company,"stk":stk,"trials":trials,
                          "best_w":best_w,"best_t":best_t,"pdufa":pdufa_match,
                          "signals":signals,"alert":alert})

radar.sort(key=lambda x: -x["alert"])
st.caption(f"{len(radar)} titoli con segnali attivi")

# RENDER — solo componenti nativi
for item in radar:
    stk = item["stk"]
    alert = item["alert"]

    # Emoji allerta
    if alert>=7: al_text = f"🔴 ALLERTA ALTA ({alert}/10)"
    elif alert>=4: al_text = f"🟡 ALLERTA MEDIA ({alert}/10)"
    else: al_text = f"🔵 ALLERTA BASSA ({alert}/10)"

    st.subheader(f"{item['ticker']} — {item['company']}")
    st.caption(al_text)

    # Metriche
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Prezzo", f"${stk['price']}", f"{stk['change']:+.1f}%",
              delta_color="normal" if stk["change"]>=0 else "inverse")
    m2.metric("Volume/Media", f"{stk['vol_ratio']}x",
              "ESPLOSIVO" if stk["vol_ratio"]>=3 else "Alto" if stk["vol_ratio"]>=2 else "Normale")
    m3.metric("Short %", f"{stk['short']}%",
              "Molto alto" if stk["short"]>=20 else "Elevato" if stk["short"]>=10 else "Nella norma")
    m4.metric("Market Cap", stk["cap_str"])

    # Segnali come testo
    for sig in item["signals"]:
        st.write(sig)

    # PDUFA info
    if item["pdufa"]:
        pm = item["pdufa"]
        g = (datetime.strptime(pm["pdufa"],"%Y-%m-%d")-datetime.now()).days
        if g >= 0:
            st.info(f"📅 VERDETTO FDA: **{pm['pdufa']}** ({g} giorni) — {pm['drug']}. {pm['nota']}")

    # Trial details
    with st.expander(f"Dettagli {len(item['trials'])} trial — {item['ticker']}"):
        for t in item["trials"]:
            w = calc_window(t["completion"], t["phase"])
            ep = ep_it(t["endpoint"])
            ph = t["phase"].upper().replace(" ","")
            pkey = "3" if "PHASE3" in ph else "2" if "PHASE2" in ph else "1" if "PHASE1" in ph else None
            pd_info = PHASE_DATA.get(pkey,{})

            # Solidity
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

            st.markdown(f"**{t['title'][:90]}**")
            st.caption(f"{t['phase']} | {t['conditions']} | {t['enrollment'] or '?'} pazienti | Solidita: **{sol_lbl}** ({sol}/8)")
            st.caption(f"Endpoint: **{ep}**")

            if pd_info:
                st.caption(f"Successo storico: **{pd_info['ok']}%** | Se positivo: **{pd_info['pos']}** | Se negativo: **{pd_info['neg']}**")

            if w:
                if w["status"]=="APERTA":
                    st.error(f"🔴 FINESTRA APERTA — Risultati attesi: {w['ws'].strftime('%d/%m')} → {w['we'].strftime('%d/%m/%Y')}")
                elif w["status"]=="RUNUP":
                    st.warning(f"🟡 ZONA RUNUP — Finestra risultati: {w['ws'].strftime('%d/%m')} → {w['we'].strftime('%d/%m/%Y')}")
                elif w["status"]=="PRESTO":
                    st.caption(f"⏳ Finestra risultati: {w['ws'].strftime('%d/%m')} → {w['we'].strftime('%d/%m/%Y')}")
                elif w["status"]=="SCADUTA":
                    st.caption(f"⚠️ Finestra scaduta — risultati dovrebbero essere gia usciti")

            st.caption(f"[{t['nct']}](https://clinicaltrials.gov/study/{t['nct']})")
            st.markdown("---")

    st.divider()

# Silenziosi
with st.expander("Titoli silenziosi (nessun segnale)"):
    for ticker, company in WATCHLIST:
        if not any(r["ticker"]==ticker for r in radar):
            stk = scan_stock(ticker)
            if stk["ok"] and CAP_MIN<=stk["cap"]<=CAP_MAX:
                st.caption(f"**{ticker}** — {company} | {stk['cap_str']} | ${stk['price']}")

st.divider()

# Legenda
with st.expander("Legenda + limiti"):
    st.write("""
**Volume/media** = volume oggi / media 3 mesi. 2x+ = insolito.
**Short %** = % azioni scommesse contro. Alto + notizia buona = squeeze.
**Allerta** = timing + volume + short. Non significa "compra".
**Finestra** = completion date del trial + 2-8 settimane.
**Solidita** = pazienti + doppio cieco + randomizzato. ALTA = piu affidabile.

**Limiti:** yfinance non ufficiale | Volume non distingue acquisto/vendita |
Completion date e una stima | Pattern storici sono medie, non previsioni |
~40% volume istituzionale passa per dark pool (invisibile) |
Aggiorna PDUFA settimanalmente chiedendo all'IA
""")

st.caption(f"v10 | PDUFA: {DATA_AGG} | App educativa — non e consulenza finanziaria | Verifica su fda.gov")
