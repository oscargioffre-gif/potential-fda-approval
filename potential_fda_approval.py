"""
FDA RADAR v12 — Volumi ripristinati + Storico + ALDX fix
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
    ("ALDX","Aldeyra Therapeutics"),("RCKT","Rocket Pharmaceuticals"),
    ("OCGN","Ocugen"),("MNMD","MindMed"),("PDSB","PDS Biotechnology"),
    ("XENE","Xenon Pharmaceuticals"),("BEAM","Beam Therapeutics"),
    ("EDIT","Editas Medicine"),("VERV","Verve Therapeutics"),
    ("IMVT","Immunovant"),("DAWN","Day One Biopharmaceuticals"),
    ("TVTX","Travere Therapeutics"),("VKTX","Viking Therapeutics"),
    ("VRDN","Viridian Therapeutics"),("VERA","Vera Therapeutics"),
    ("PLRX","Pliant Therapeutics"),
]

PDUFA_LIST = [
    {"ticker":"ALDX","drug":"Reproxalap","pdufa":"2026-03-16","crl":2,"labeling":True,
     "nota":"3a richiesta dopo 2 bocciature. FDA sta scrivendo il foglietto. AbbVie opzione $100M."},
    {"ticker":"RCKT","drug":"Kresladi","pdufa":"2026-03-28","crl":1,"labeling":False,
     "nota":"Terapia genica. 100% sopravvivenza nel trial. 1 bocciatura precedente."},
]

# ═══════════════════════════════
# STORICO APPROVAZIONI/BOCCIATURE
# ═══════════════════════════════
STORICO = [
    {"data":"2026-03-11","ticker":"WELL","azienda":"Wellcovorin","farmaco":"Leucovorin calcium",
     "esito":"APPROVATO","fase":"sNDA","nota":"Cerebral folate deficiency. Prima terapia approvata.","move":"+12%"},
    {"data":"2026-03-06","ticker":"LNTH","azienda":"Lantheus","farmaco":"PYLARIFY TruVu",
     "esito":"APPROVATO","fase":"NDA","nota":"Nuova formulazione imaging prostatico.","move":"+8%"},
    {"data":"2026-03-06","ticker":"BMY","azienda":"Bristol Myers Squibb","farmaco":"Sotyktu",
     "esito":"APPROVATO","fase":"sNDA","nota":"Espansione a artrite psoriasica.","move":"+3%"},
    {"data":"2026-02-25","ticker":"ENSG","azienda":"Ensergo (ex-Santhera)","farmaco":"DESMODA (ET-600)",
     "esito":"APPROVATO","fase":"NDA","nota":"Diabete insipido centrale.","move":"+45%"},
    {"data":"2026-02-08","ticker":"RGNX","azienda":"REGENXBIO","farmaco":"RGX-121",
     "esito":"IN ATTESA","fase":"BLA","nota":"Sindrome di Hunter. Decisione attesa.","move":"N/D"},
    {"data":"2026-01-14","ticker":"CUTX","azienda":"Sentynl/Cyprium","farmaco":"CUTX-101",
     "esito":"APPROVATO","fase":"NDA","nota":"Malattia di Menkes. Prima terapia.","move":"+85%"},
    {"data":"2026-01-10","ticker":"ATRA","azienda":"Atara Biotherapeutics","farmaco":"Tabelecleucel",
     "esito":"BOCCIATO","fase":"BLA","nota":"EBV+ PTLD. Complete Response Letter.","move":"-62%"},
    {"data":"2025-12-16","ticker":"ALDX","azienda":"Aldeyra","farmaco":"Reproxalap",
     "esito":"RINVIATO","fase":"NDA","nota":"PDUFA esteso da dic.2025 a mar.2026.","move":"+18%"},
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


# ═══════════════════════════════
# YFINANCE — volumi ripristinati
# ═══════════════════════════════

@st.cache_data(ttl=900)
def get_stock_full(ticker):
    """Usa .info per tutti i dati inclusi volumi e short."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="1mo")

        price = info.get("currentPrice") or info.get("regularMarketPrice",0)
        prev = info.get("previousClose", price)
        cap = info.get("marketCap",0)
        change = round(((price-prev)/prev*100),2) if prev else 0

        # VOLUMI — il dato chiave
        vol_now = info.get("volume",0) or 0
        vol_avg = info.get("averageVolume",0) or 1
        vol_ratio = round(vol_now / vol_avg, 2) if vol_avg else 0

        # Pre/post market
        pre_price = info.get("preMarketPrice", 0)
        pre_change = info.get("preMarketChangePercent", 0)
        post_price = info.get("postMarketPrice", 0)
        post_change = info.get("postMarketChangePercent", 0)

        # Short interest
        si = info.get("shortPercentOfFloat",0) or 0
        if si and si < 1: si *= 100

        # Volume trend (5gg vs 15gg precedenti)
        vol_trend = "neutro"
        if len(hist) >= 10:
            rv = hist["Volume"].tail(5).mean()
            ov = hist["Volume"].tail(15).head(10).mean()
            if ov > 0:
                vc = (rv - ov) / ov
                if vc > 0.5: vol_trend = "spike"
                elif vc > 0.2: vol_trend = "crescente"
                elif vc < -0.2: vol_trend = "calante"

        # Price trend
        price_trend = "neutro"
        if len(hist) >= 5:
            p5 = hist["Close"].tail(5).mean()
            p_all = hist["Close"].mean()
            if p_all > 0:
                pt = (p5 - p_all) / p_all
                if pt > 0.05: price_trend = "sale"
                elif pt < -0.05: price_trend = "scende"

        return {
            "price":round(price,2), "change":change, "cap":cap,
            "cap_str":f"${cap/1e9:.2f}B" if cap>=1e9 else f"${cap/1e6:.0f}M" if cap>=1e6 else "N/D",
            "vol_now":vol_now, "vol_avg":vol_avg, "vol_ratio":vol_ratio, "vol_trend":vol_trend,
            "pre_price":round(pre_price,2) if pre_price else None,
            "pre_change":round(pre_change*100,2) if pre_change and abs(pre_change)<1 else round(pre_change,2) if pre_change else None,
            "post_price":round(post_price,2) if post_price else None,
            "post_change":round(post_change*100,2) if post_change and abs(post_change)<1 else round(post_change,2) if post_change else None,
            "short":round(si,1), "price_trend":price_trend, "ok":cap>0,
            "name":info.get("shortName",ticker),
        }
    except:
        return {
            "price":0,"change":0,"cap":0,"cap_str":"N/D",
            "vol_now":0,"vol_avg":0,"vol_ratio":0,"vol_trend":"errore",
            "pre_price":None,"pre_change":None,"post_price":None,"post_change":None,
            "short":0,"price_trend":"errore","ok":False,"name":ticker,
        }


# ═══════════════════════════════
# CLINICALTRIALS.GOV
# ═══════════════════════════════

@st.cache_data(ttl=3600)
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


def calc_window(completion_str, phase_str):
    try:
        if len(completion_str)==7: cd=datetime.strptime(completion_str+"-28","%Y-%m-%d")
        elif len(completion_str)>=10: cd=datetime.strptime(completion_str[:10],"%Y-%m-%d")
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
            pdate = datetime.strptime(pdufa_match["pdufa"],"%Y-%m-%d")
            g = (pdate - datetime.now()).days
            # FIX: mostra anche il giorno stesso e fino a 2 giorni dopo (in attesa del comunicato)
            if -2 <= g <= 0:
                signals.append(f"⏰ VERDETTO FDA OGGI/IMMINENTE"); alert+=5
            elif 0 < g <= 3:
                signals.append(f"⏰ VERDETTO FDA TRA {g}g"); alert+=4
            elif 3 < g <= 14:
                signals.append(f"📅 Verdetto FDA tra {g}g"); alert+=3
        except: pass
        if pdufa_match.get("labeling"): signals.append("🏷️ FDA scrive il foglietto"); alert+=2
        if pdufa_match.get("crl",0) >= 2: signals.append(f"❌ {pdufa_match['crl']} bocciature precedenti")
    if window:
        if window["status"]=="APERTA": signals.append("🔴 FINESTRA APERTA"); alert+=4
        elif window["status"]=="RUNUP": signals.append("🟡 Zona pre-risultati"); alert+=2
    if stk["vol_ratio"]>=3: signals.append(f"🔥 VOLUME {stk['vol_ratio']}x media"); alert+=3
    elif stk["vol_ratio"]>=2: signals.append(f"📈 Volume {stk['vol_ratio']}x"); alert+=2
    elif stk["vol_ratio"]>=1.5: signals.append(f"📊 Volume {stk['vol_ratio']}x"); alert+=1
    if stk["vol_trend"]=="spike": signals.append("⚡ Spike volume 5gg"); alert+=2
    elif stk["vol_trend"]=="crescente": signals.append("↗️ Volume crescente"); alert+=1
    if stk["price_trend"]=="sale": signals.append("🟢 Prezzo in salita")
    elif stk["price_trend"]=="scende": signals.append("🔻 Prezzo in discesa")
    if stk["short"]>=20: signals.append(f"🐻 Short {stk['short']}% — squeeze possibile"); alert+=2
    elif stk["short"]>=10: signals.append(f"🐻 Short {stk['short']}%"); alert+=1
    return signals, min(alert,10)


# ═══════════════════════════════
# APP
# ═══════════════════════════════

st.title("📡 FDA Radar")
st.caption("Volumi + Catalizzatori + Storico approvazioni")

try:
    obs=(datetime.now()-datetime.strptime(DATA_AGG,"%Y-%m-%d")).days
except: obs=999
if obs>14: st.error(f"Dati PDUFA vecchi di {obs} giorni!")
elif obs>7: st.warning(f"Dati PDUFA di {obs} giorni fa.")

with st.expander("Come leggere i segnali"):
    st.write("""
**VOLUMI** — la traccia dei fondi:
- **Volume/media 3x+** = qualcuno si posiziona pesante
- **Volume/media 2x** = attivita sopra la norma
- **Pre-market / After-hours** = movimenti fuori orario, spesso su notizie
- Volume + prezzo sale = comprano. Volume + prezzo scende = vendono.

**CATALIZZATORI:**
- **Finestra APERTA** = risultati trial possono uscire ora
- **RUNUP** = zona pre-risultati, mercato anticipa
- **Short alto** = tanti scommettono contro. Se notizia positiva = squeeze
""")

st.subheader("Movimenti storici per fase")
c1,c2,c3 = st.columns(3)
c1.metric("Phase 1","52% successo","ok +15-40% | ko -20-50%")
c2.metric("Phase 2","29% successo","ok +30-80% | ko -40-70%")
c3.metric("Phase 3","58% successo","ok +20-60% | ko -50-80%")
st.divider()


# ═══════════════════════════════
# SCANSIONE
# ═══════════════════════════════

status_text = st.empty()
radar_hot = []
radar_silent = []

for i, (ticker, company) in enumerate(WATCHLIST):
    status_text.caption(f"Scansione {i+1}/{len(WATCHLIST)}: {ticker}...")
    stk = get_stock_full(ticker)
    if not stk["ok"]: continue
    if not (CAP_MIN <= stk["cap"] <= CAP_MAX): continue

    trials = get_trials(company)
    pdufa_match = next((p for p in PDUFA_LIST if p["ticker"]==ticker), None)

    best_w = None
    for t in trials:
        w = calc_window(t["completion"], t["phase"])
        if w and w["status"] in ("APERTA","RUNUP"):
            if best_w is None or w["status"]=="APERTA": best_w=w

    signals, alert = compute_alert(stk, best_w, pdufa_match)
    item = {"ticker":ticker,"company":company,"stk":stk,"trials":trials,
            "pdufa":pdufa_match,"signals":signals,"alert":alert}

    if alert > 0: radar_hot.append(item)
    else: radar_silent.append(item)

status_text.empty()
radar_hot.sort(key=lambda x: -x["alert"])

st.subheader(f"📡 {len(radar_hot)} titoli con segnali attivi")

if not radar_hot:
    st.info("Nessun segnale attivo al momento.")

for item in radar_hot:
    stk = item["stk"]
    alert = item["alert"]
    if alert>=7: badge="🔴 ALTO"
    elif alert>=4: badge="🟡 MEDIO"
    else: badge="🔵 BASSO"

    st.markdown(f"### {item['ticker']} — {item['company']}")
    st.caption(f"Allerta: {badge} ({alert}/10)")

    # METRICHE PRINCIPALI
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Prezzo", f"${stk['price']}", f"{stk['change']:+.1f}%",
              delta_color="normal" if stk["change"]>=0 else "inverse")
    m2.metric("Market Cap", stk["cap_str"])
    m3.metric("Vol/Media", f"{stk['vol_ratio']}x",
              "ESPLOSIVO" if stk["vol_ratio"]>=3 else "Alto" if stk["vol_ratio"]>=2 else "Normale")
    m4.metric("Short", f"{stk['short']}%",
              "Molto alto" if stk["short"]>=20 else "Elevato" if stk["short"]>=10 else "Norma")

    # VOLUMI DETTAGLIATI
    v1,v2,v3 = st.columns(3)
    v1.metric("Volume oggi", f"{stk['vol_now']:,.0f}" if stk['vol_now'] else "N/D")
    v2.metric("Volume medio", f"{stk['vol_avg']:,.0f}" if stk['vol_avg'] else "N/D")
    if stk["vol_trend"]=="spike": v3.metric("Trend 5gg","⚡ SPIKE")
    elif stk["vol_trend"]=="crescente": v3.metric("Trend 5gg","↗️ Crescente")
    elif stk["vol_trend"]=="calante": v3.metric("Trend 5gg","↘️ Calante")
    else: v3.metric("Trend 5gg","→ Neutro")

    # PRE/POST MARKET
    pm1,pm2 = st.columns(2)
    if stk["pre_price"]:
        pm1.metric("Pre-Market", f"${stk['pre_price']}", f"{stk['pre_change']:+.1f}%" if stk["pre_change"] else None)
    else:
        pm1.metric("Pre-Market", "—")
    if stk["post_price"]:
        pm2.metric("After-Hours", f"${stk['post_price']}", f"{stk['post_change']:+.1f}%" if stk["post_change"] else None)
    else:
        pm2.metric("After-Hours", "—")

    # SEGNALI
    for sig in item["signals"]:
        st.write(sig)

    # PDUFA
    if item["pdufa"]:
        pm = item["pdufa"]
        try:
            g = (datetime.strptime(pm["pdufa"],"%Y-%m-%d").date() - datetime.now().date()).days
            if g <= 0:
                st.error(f"⏰ **VERDETTO FDA OGGI: {pm['pdufa']}** — {pm['drug']}. {pm['nota']}")
            elif g <= 7:
                st.warning(f"📅 **VERDETTO FDA: {pm['pdufa']}** ({g}g) — {pm['drug']}. {pm['nota']}")
            else:
                st.info(f"📅 **VERDETTO FDA: {pm['pdufa']}** ({g}g) — {pm['drug']}. {pm['nota']}")
        except: pass

    # TRIAL
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
            if pd_info: st.caption(f"Successo: **{pd_info['ok']}%** | ok: **{pd_info['pos']}** | ko: **{pd_info['neg']}**")
            if w:
                if w["status"]=="APERTA": st.error(f"FINESTRA APERTA — {w['ws'].strftime('%d/%m')} - {w['we'].strftime('%d/%m/%Y')}")
                elif w["status"]=="RUNUP": st.warning(f"RUNUP — {w['ws'].strftime('%d/%m')} - {w['we'].strftime('%d/%m/%Y')}")
                elif w["status"]=="PRESTO": st.caption(f"Finestra: {w['ws'].strftime('%d/%m')} - {w['we'].strftime('%d/%m/%Y')}")
            st.caption(f"[{t['nct']}](https://clinicaltrials.gov/study/{t['nct']})")
            st.divider()
    st.divider()

# SILENZIOSI
if radar_silent:
    with st.expander(f"Titoli senza segnali ({len(radar_silent)})"):
        for item in radar_silent:
            st.caption(f"**{item['ticker']}** — {item['company']} | {item['stk']['cap_str']} | ${item['stk']['price']} | {len(item['trials'])} trial")

st.divider()

# ═══════════════════════════════
# SEZIONE STORICO
# ═══════════════════════════════

st.subheader("📜 Storico verdetti FDA recenti")
st.caption("Approvati, bocciati e rinviati — con movimento del titolo")

for item in STORICO:
    if item["esito"] == "APPROVATO":
        icon = "✅"
        color_text = "APPROVATO"
    elif item["esito"] == "BOCCIATO":
        icon = "❌"
        color_text = "BOCCIATO (CRL)"
    elif item["esito"] == "RINVIATO":
        icon = "⏳"
        color_text = "RINVIATO"
    else:
        icon = "⏳"
        color_text = item["esito"]

    move_text = item.get("move","N/D")
    st.write(f"{icon} **{item['data']}** — **{item['ticker']}** ({item['azienda']}) — {item['farmaco']}")
    st.caption(f"{color_text} | {item['fase']} | Movimento: **{move_text}** | {item['nota']}")
    st.divider()

# ═══════════════════════════════
# LEGENDA + FOOTER
# ═══════════════════════════════

with st.expander("Legenda + limiti"):
    st.write("""
**Volume/media** = volume oggi / media 3 mesi. 2x+ = insolito.
**Pre-market** = scambi prima apertura (4:00-9:30 ET). Spesso su notizie notturne.
**After-hours** = scambi dopo chiusura (16:00-20:00 ET). Spesso su comunicati post-chiusura.
**Short %** = % azioni scommesse contro. Alto + notizia buona = squeeze.
**Allerta** = timing + volume + short. Non significa "compra".

**Limiti:** yfinance non ufficiale | Volume non distingue acquisto/vendita |
Pre/post market disponibili solo durante le sessioni estese |
~40% volume istituzionale passa per dark pool (invisibile) |
Lo storico e hardcoded — aggiornalo chiedendo all'IA |
Aggiorna PDUFA settimanalm
