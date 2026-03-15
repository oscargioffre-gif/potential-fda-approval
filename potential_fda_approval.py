"""
POTENTIAL FDA APPROVAL v9 — RADAR
Un obiettivo: anticipare QUANDO il titolo si muovera
e capire SE qualcuno si sta gia posizionando.

pip install streamlit yfinance pandas requests
streamlit run potential_fda_approval.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="FDA Radar", page_icon="📡", layout="wide")

st.markdown("""<style>
.stApp{background:#020617}
[data-testid="stMetric"]{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:12px}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════
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
     "nota":"Terapia genica. 100% sopravvivenza nel trial. 1 bocciatura precedente."},
]

# Tasso successo storico e movimenti medi
PHASE_DATA = {
    "3": {"ok":58,"pos":"+20-60%","neg":"-50-80%","run":45,"label":"Phase 3"},
    "2": {"ok":29,"pos":"+30-80%","neg":"-40-70%","run":30,"label":"Phase 2"},
    "1": {"ok":52,"pos":"+15-40%","neg":"-20-50%","run":15,"label":"Phase 1"},
}

ENDPOINT_IT = {
    "overall survival":"Sopravvivenza","progression-free survival":"Tempo senza peggioramento",
    "progression free survival":"Tempo senza peggioramento",
    "objective response rate":"% tumore ridotto","overall response rate":"% miglioramento",
    "complete response":"% tumore scomparso","adverse events":"Effetti collaterali",
    "safety":"Sicurezza","hba1c":"Controllo diabete","pain":"Riduzione dolore",
    "quality of life":"Qualita vita","ocular discomfort":"Fastidio occhi",
    "seizure frequency":"Crisi epilettiche","tumor size":"Dimensione tumore",
    "change in bmi":"Cambio peso","biomarker":"Marcatore biologico",
    "pharmacokinetics":"Farmacocinetica","maximum tolerated dose":"Dose max tollerata",
}

def ep_it(text):
    if not text: return "Non specificato"
    for k,v in ENDPOINT_IT.items():
        if k in text.lower(): return v
    return text[:50]


# ══════════════════════════════════════════════════
# YFINANCE — prezzi + volume + short interest
# ══════════════════════════════════════════════════

@st.cache_data(ttl=600)
def scan_stock(ticker):
    try:
        s = yf.Ticker(ticker)
        info = s.info
        hist = s.history(period="3mo")

        price = info.get("currentPrice") or info.get("regularMarketPrice",0)
        prev = info.get("previousClose", price)
        cap = info.get("marketCap",0)
        change = round(((price-prev)/prev*100),2) if prev else 0

        # Volume analysis — il segnale chiave
        vol_now = info.get("volume",0) or 0
        vol_avg = info.get("averageVolume",0) or 1
        vol_ratio = round(vol_now / vol_avg, 2) if vol_avg else 0

        # Short interest
        si = info.get("shortPercentOfFloat",0) or 0
        if si < 1: si *= 100

        # Trend volume 5 giorni vs media
        vol_trend = "neutro"
        if len(hist) >= 10:
            recent_vol = hist["Volume"].tail(5).mean()
            older_vol = hist["Volume"].tail(20).head(15).mean()
            if older_vol > 0:
                vol_change = (recent_vol - older_vol) / older_vol
                if vol_change > 0.5: vol_trend = "spike"
                elif vol_change > 0.2: vol_trend = "crescente"
                elif vol_change < -0.2: vol_trend = "calante"

        # Price trend
        price_trend = "neutro"
        if len(hist) >= 10:
            p5 = hist["Close"].tail(5).mean()
            p20 = hist["Close"].tail(20).mean()
            if p20 > 0:
                pt = (p5 - p20) / p20
                if pt > 0.05: price_trend = "sale"
                elif pt < -0.05: price_trend = "scende"

        return {
            "price":round(price,2),"change":change,"cap":cap,
            "cap_str": f"${cap/1e9:.2f}B" if cap>=1e9 else f"${cap/1e6:.0f}M" if cap>=1e6 else "N/D",
            "vol_now":vol_now,"vol_avg":vol_avg,"vol_ratio":vol_ratio,
            "vol_trend":vol_trend,"price_trend":price_trend,
            "short":round(si,1),"ok":cap>0,
            "name":info.get("shortName",ticker),
        }
    except:
        return {"price":0,"change":0,"cap":0,"cap_str":"N/D","vol_now":0,"vol_avg":0,
                "vol_ratio":0,"vol_trend":"errore","price_trend":"errore","short":0,"ok":False,"name":ticker}


# ══════════════════════════════════════════════════
# CLINICALTRIALS.GOV — trial + completion date
# ══════════════════════════════════════════════════

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
        out = []
        for s in r.json().get("studies",[]):
            p = s.get("protocolSection",{})
            ident = p.get("identificationModule",{})
            stat = p.get("statusModule",{})
            des = p.get("designModule",{})
            cond = p.get("conditionsModule",{})
            outc = p.get("outcomesModule",{})
            phases = des.get("phases",[]) if des else []
            ei = des.get("enrollmentInfo",{}) if des else {}
            di = des.get("designInfo",{}) if des else {}
            mi = di.get("maskingInfo",{}) if di else {}
            po = outc.get("primaryOutcomes",[]) if outc else []
            pcd = stat.get("primaryCompletionDateStruct",{}) if stat else {}
            out.append({
                "nct":ident.get("nctId",""),"title":ident.get("briefTitle",""),
                "phase":", ".join(phases) if phases else "N/A",
                "conditions":", ".join(cond.get("conditions",[])[:2]) if cond else "N/D",
                "enrollment":ei.get("count",0) if ei else 0,
                "mask":mi.get("masking","") if mi else "",
                "is_rand":"RANDOMIZED" in (di.get("allocation","").upper()),
                "endpoint":po[0].get("measure","") if po else "",
                "completion":pcd.get("date","") if pcd else "",
            })
        return out
    except: return []


# ══════════════════════════════════════════════════
# FINESTRA CATALIZZATORE
# ══════════════════════════════════════════════════

def calc_window(completion_str, phase_str):
    try:
        if len(completion_str)==7:
            cd = datetime.strptime(completion_str+"-28","%Y-%m-%d")
        elif len(completion_str)>=10:
            cd = datetime.strptime(completion_str[:10],"%Y-%m-%d")
        else: return None
    except: return None

    now = datetime.now()
    ws = cd + timedelta(weeks=2)
    we = cd + timedelta(weeks=8)

    p = phase_str.upper().replace(" ","")
    if "PHASE3" in p: pkey="3"; rup=45
    elif "PHASE2" in p: pkey="2"; rup=30
    elif "PHASE1" in p: pkey="1"; rup=15
    else: return None

    rs = ws - timedelta(days=rup)
    pd_info = PHASE_DATA[pkey]

    if now < rs: status,color = "PRESTO","#475569"
    elif now < ws: status,color = "RUNUP","#f59e0b"
    elif now <= we: status,color = "APERTA","#dc2626"
    else: status,color = "SCADUTA","#64748b"

    return {"ws":ws,"we":we,"rs":rs,"status":status,"color":color,"pkey":pkey,"pd":pd_info,"cd":cd}


# ══════════════════════════════════════════════════
# SEGNALE COMBINATO
# ══════════════════════════════════════════════════

def compute_signal(stk, window, pdufa_match):
    """Combina timing + volume + short per dare un segnale di attenzione."""
    signals = []
    alert_level = 0  # 0-10

    # TIMING
    if pdufa_match:
        g = (datetime.strptime(pdufa_match["pdufa"],"%Y-%m-%d")-datetime.now()).days
        if 0 <= g <= 3:
            signals.append(("⏰","VERDETTO IMMINENTE",f"FDA decide tra {g} giorni"))
            alert_level += 4
        elif 0 <= g <= 14:
            signals.append(("📅","Verdetto vicino",f"FDA decide tra {g} giorni"))
            alert_level += 3
    if window:
        if window["status"]=="APERTA":
            signals.append(("🔴","FINESTRA APERTA","I risultati possono uscire ora"))
            alert_level += 4
        elif window["status"]=="RUNUP":
            signals.append(("🟡","Zona pre-risultati","Il mercato potrebbe gia muoversi"))
            alert_level += 2

    # VOLUME — il proxy per i fondi
    if stk["vol_ratio"] >= 3:
        signals.append(("🔥","VOLUME ESPLOSIVO",f"{stk['vol_ratio']}x la media — qualcuno si sta posizionando pesantemente"))
        alert_level += 3
    elif stk["vol_ratio"] >= 2:
        signals.append(("📈","Volume alto",f"{stk['vol_ratio']}x la media — attivita sopra la norma"))
        alert_level += 2
    elif stk["vol_ratio"] >= 1.5:
        signals.append(("📊","Volume moderato",f"{stk['vol_ratio']}x la media"))
        alert_level += 1

    if stk["vol_trend"]=="spike":
        signals.append(("⚡","Trend volume in spike","Ultimi 5gg molto sopra i precedenti 15"))
        alert_level += 2
    elif stk["vol_trend"]=="crescente":
        signals.append(("↗️","Volume in crescita","Trend ultimi 5gg sopra la media"))
        alert_level += 1

    # PREZZO
    if stk["price_trend"]=="sale":
        signals.append(("🟢","Prezzo in salita","Media 5gg sopra media 20gg"))
    elif stk["price_trend"]=="scende":
        signals.append(("🔴","Prezzo in discesa","Media 5gg sotto media 20gg"))

    # SHORT INTEREST
    if stk["short"] >= 20:
        signals.append(("🐻","Short molto alto",f"{stk['short']}% — se arriva notizia positiva, possibile short squeeze"))
        alert_level += 2
    elif stk["short"] >= 10:
        signals.append(("🐻","Short elevato",f"{stk['short']}% — pressione ribassista significativa"))
        alert_level += 1

    # LABELING (dal PDUFA)
    if pdufa_match and pdufa_match.get("labeling"):
        signals.append(("🏷️","FDA scrive il foglietto","Segnale positivo — pensano a COME venderlo"))
        alert_level += 2

    return signals, min(alert_level, 10)


# ══════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════

st.markdown('<p style="font-size:2.2em;font-weight:900;text-align:center;background:linear-gradient(90deg,#60a5fa,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0">📡 FDA Radar</p>', unsafe_allow_html=True)
st.caption("Un obiettivo: anticipare QUANDO il titolo si muovera e capire SE qualcuno si sta gia posizionando")

# Quick reference
with st.expander("Come leggere i segnali (30 secondi)"):
    st.markdown("""
**I fondi non annunciano che comprano. Ma lasciano tracce nel volume.**

Se un titolo fa normalmente 500K azioni/giorno e improvvisamente ne fa 2 milioni,
qualcuno si sta posizionando. Se questo succede vicino a un catalizzatore, e un segnale forte.

**Livello di allerta (0-10):** combina timing del catalizzatore + volume anomalo + short interest.
Piu e alto, piu il titolo e "caldo". Non significa che salira — significa che si muovera.

| Segnale | Significato |
|---------|-----------|
| 🔴 FINESTRA APERTA | I risultati del trial possono uscire ora |
| 🟡 RUNUP | Il mercato si posiziona prima dei risultati |
| 🔥 VOLUME ESPLOSIVO | 3x+ la media — qualcuno sa o scommette forte |
| 📈 Volume alto | 2x la media — attivita insolita |
| 🐻 Short alto | Tanti scommettono contro — se va bene, squeeze |
| 🏷️ FDA scrive foglietto | Segnale positivo forte per approvazione |

**⚠️ Nessun segnale garantisce la direzione. Servono per capire QUANDO prestare attenzione, non COSA comprare.**
""")

st.markdown("---")

# SCAN
with st.spinner("Scansione 28 aziende..."):
    radar_items = []
    for ticker, company in WATCHLIST:
        stk = scan_stock(ticker)
        if not stk["ok"] or not (CAP_MIN <= stk["cap"] <= CAP_MAX):
            continue

        trials = scan_trials(company)
        pdufa_match = next((p for p in PDUFA_LIST if p["ticker"]==ticker), None)

        # Best window across trials
        best_window = None
        best_trial = None
        for t in trials:
            w = calc_window(t["completion"], t["phase"])
            if w and w["status"] in ("APERTA","RUNUP"):
                if best_window is None or (w["status"]=="APERTA" and best_window["status"]!="APERTA"):
                    best_window = w
                    best_trial = t

        signals, alert = compute_signal(stk, best_window, pdufa_match)

        radar_items.append({
            "ticker":ticker,"company":company,"stk":stk,
            "trials":trials,"best_window":best_window,"best_trial":best_trial,
            "pdufa":pdufa_match,"signals":signals,"alert":alert,
        })

# Sort by alert level (highest first)
radar_items.sort(key=lambda x: -x["alert"])

st.caption(f"{len(radar_items)} aziende nel range 200M-2B | Ordinate per livello di allerta")

# RENDER
for item in radar_items:
    stk = item["stk"]
    alert = item["alert"]
    sigs = item["signals"]

    if alert == 0:
        continue  # Skip silent ones

    # Alert color
    if alert >= 7: ac,al = "#dc2626","ALTO"
    elif alert >= 4: ac,al = "#f59e0b","MEDIO"
    else: ac,al = "#3b82f6","BASSO"

    # Volume bar
    vr = min(stk["vol_ratio"], 5)
    vr_pct = vr / 5 * 100
    vr_col = "#dc2626" if vr>=3 else "#f59e0b" if vr>=2 else "#3b82f6" if vr>=1.5 else "#334155"

    # Main card
    st.markdown(f"""<div style="background:#0f172a;border:1px solid {ac}44;border-left:4px solid {ac};
    border-radius:0 12px 12px 0;padding:14px;margin:6px 0">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:8px">
    <div>
    <span style="font-size:18px;font-weight:900;color:#f8fafc">{item['ticker']}</span>
    <span style="font-size:12px;color:#94a3b8;margin-left:6px">{item['company']}</span>
    <span style="font-size:11px;color:#64748b;margin-left:6px">{stk['cap_str']}</span>
    </div>
    <span style="background:{ac};color:white;padding:3px 12px;border-radius:16px;font-weight:800;font-size:11px">ALLERTA {al} ({alert}/10)</span>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;margin-bottom:10px">
    <div style="text-align:center"><div style="font-size:16px;font-weight:800;color:{'#22c55e' if stk['change']>=0 else '#ef4444'}">${stk['price']}</div><div style="font-size:10px;color:#64748b">{stk['change']:+.1f}%</div></div>
    <div style="text-align:center"><div style="font-size:16px;font-weight:800;color:{vr_col}">{stk['vol_ratio']}x</div><div style="font-size:10px;color:#64748b">vol/media</div></div>
    <div style="text-align:center"><div style="font-size:16px;font-weight:800;color:{'#ef4444' if stk['short']>=15 else '#f8fafc'}">{stk['short']}%</div><div style="font-size:10px;color:#64748b">short</div></div>
    <div style="text-align:center"><div style="font-size:16px;font-weight:800;color:#f8fafc">{len(item['trials'])}</div><div style="font-size:10px;color:#64748b">trial</div></div>
    </div>

    <div style="background:#1e293b;border-radius:4px;height:6px;overflow:hidden;margin-bottom:8px">
    <div style="width:{vr_pct}%;height:100%;background:{vr_col};border-radius:4px"></div></div>

    {"".join(f'<div style="font-size:12px;color:#cbd5e1;margin:2px 0"><span style="margin-right:4px">{e}</span> <strong>{t}</strong> — <span style="color:#94a3b8">{d}</span></div>' for e,t,d in sigs)}
    </div>""", unsafe_allow_html=True)

    # Expand: trial details
    with st.expander(f"Dettagli trial + catalizzatori — {item['ticker']}"):
        # PDUFA
        if item["pdufa"]:
            pm = item["pdufa"]
            g = (datetime.strptime(pm["pdufa"],"%Y-%m-%d")-datetime.now()).days
            st.markdown(f"**📅 VERDETTO FDA: {pm['pdufa']}** ({g}g) — {pm['drug']}")
            st.caption(pm["nota"])
            if pm["crl"]>0: st.caption(f"❌ {pm['crl']} bocciature precedenti")
            if pm.get("labeling"): st.caption("🏷️ FDA sta scrivendo il foglietto illustrativo")

        # Trials
        for t in item["trials"]:
            w = calc_window(t["completion"], t["phase"])
            ep = ep_it(t["endpoint"])
            ph = t["phase"].upper().replace(" ","")
            pkey = "3" if "PHASE3" in ph else "2" if "PHASE2" in ph else "1" if "PHASE1" in ph else None
            pd_info = PHASE_DATA.get(pkey, {})

            # Solidity
            sol = 0
            if t["enrollment"] and t["enrollment"]>=500: sol+=3
            elif t["enrollment"] and t["enrollment"]>=100: sol+=2
            elif t["enrollment"]: sol+=1
            if pkey=="3": sol+=2
            elif pkey=="2": sol+=1
            if "DOUBLE" in (t.get("mask","").upper()): sol+=2
            elif "SINGLE" in (t.get("mask","").upper()): sol+=1
            if t.get("is_rand"): sol+=1
            sol_lbl = "ALTA" if sol>=7 else "MEDIA" if sol>=4 else "BASSA"
            sol_col = "#22c55e" if sol>=7 else "#f59e0b" if sol>=4 else "#ef4444"

            win_html = ""
            if w:
                win_html = f'<div style="background:{w["color"]}15;border:1px solid {w["color"]}44;border-radius:6px;padding:6px 10px;margin:4px 0;font-size:11px"><strong style="color:{w["color"]}">{w["status"]}</strong> — Risultati attesi: {w["ws"].strftime("%d/%m")} → {w["we"].strftime("%d/%m/%Y")}</div>'

            st.markdown(f"""<div style="background:#1e293b;border-radius:8px;padding:10px;margin:4px 0;font-size:12px">
            <strong style="color:#e2e8f0">{t['title'][:90]}</strong>
            <div style="color:#94a3b8;margin:4px 0">{t['phase']} | {t['conditions']} | {t['enrollment'] or '?'} pazienti | Solidita: <span style="color:{sol_col};font-weight:700">{sol_lbl}</span></div>
            <div style="color:#a5b4fc">Endpoint: <strong>{ep}</strong></div>
            {f'<div style="color:#94a3b8">Successo storico: <strong style="color:#f59e0b">{pd_info["ok"]}%</strong> | Se positivo: <strong style="color:#22c55e">{pd_info["pos"]}</strong> | Se negativo: <strong style="color:#ef4444">{pd_info["neg"]}</strong></div>' if pd_info else ''}
            {win_html}
            <a href="https://clinicaltrials.gov/study/{t['nct']}" style="color:#60a5fa;font-size:11px">{t['nct']}</a>
            </div>""", unsafe_allow_html=True)

# Titoli silenziosi
silent = [i for i in radar_items if i["alert"]==0]
if silent:
    with st.expander(f"Titoli silenziosi — nessun segnale ({len(silent)})"):
        for i in silent:
            st.caption(f"**{i['ticker']}** — {i['company']} | {i['stk']['cap_str']} | ${i['stk']['price']} | {len(i['trials'])} trial | Vol: {i['stk']['vol_ratio']}x")

st.markdown("---")

# LEGENDA RAPIDA
st.markdown("""<div style="background:#0f172a;border:1px solid #334155;border-radius:10px;padding:14px;font-size:12px;color:#94a3b8;line-height:1.7">
<strong style="color:#f8fafc">Legenda rapida</strong><br>
<strong>Volume/media</strong> = volume di oggi diviso la media 3 mesi. 2x+ = qualcuno compra/vende piu del normale.<br>
<strong>Short %</strong> = % di azioni "scommesse contro". Se alto + notizia positiva = squeeze.<br>
<strong>Allerta</strong> = timing catalizzatore + volume anomalo + short. Piu alto = piu caldo. Non significa "compra".<br>
<strong>Finestra</strong> = periodo in cui i risultati del trial potrebbero uscire (completion + 2-8 settimane).<br>
<strong>Solidita trial</strong> = pazienti + doppio cieco + randomizzato. ALTA = dati piu affidabili.<br><br>
<strong style="color:#fbbf24">⚠️ I segnali volume NON distinguono se i fondi COMPRANO o VENDONO.</strong>
Volume alto significa attivita — puo essere acquisto, vendita, o hedging. Per sapere la direzione serve guardare il prezzo insieme al volume: volume alto + prezzo sale = probabilmente comprano. Volume alto + prezzo scende = probabilmente vendono.
</div>""", unsafe_allow_html=True)

st.caption(f"v9.0 | PDUFA: {DATA_AGG} | Prezzi: 10min | Trial: 1h | App educativa — non e consulenza finanziaria")
