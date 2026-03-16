# FDA RADAR v14 — Dati mercato affidabili via batch download
# FIX: usa yf.download() per tutti i ticker in UNA chiamata
# invece di 16 chiamate .info separate che vanno in timeout
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
    {"ticker":"ALDX","company":"Aldeyra Therapeutics","drug":"Reproxalap",
     "indication":"Occhio secco","pdufa":"2026-03-16","crl":2,"labeling":True,
     "nota":"3a richiesta dopo 2 bocciature. FDA sta scrivendo il foglietto. AbbVie opzione $100M."},
    {"ticker":"RCKT","company":"Rocket Pharmaceuticals","drug":"Kresladi",
     "indication":"LAD-I (fatale nei bambini)","pdufa":"2026-03-28","crl":1,"labeling":False,
     "nota":"Terapia genica. 100% sopravvivenza nel trial. 1 bocciatura precedente."},
]

STORICO = [
    {"data":"2026-03-11","ticker":"WELL","azienda":"Wellcovorin","farmaco":"Leucovorin calcium","esito":"APPROVATO","fase":"sNDA","nota":"Cerebral folate deficiency.","move":"+12%"},
    {"data":"2026-03-06","ticker":"LNTH","azienda":"Lantheus","farmaco":"PYLARIFY TruVu","esito":"APPROVATO","fase":"NDA","nota":"Imaging prostatico.","move":"+8%"},
    {"data":"2026-03-06","ticker":"BMY","azienda":"Bristol Myers Squibb","farmaco":"Sotyktu","esito":"APPROVATO","fase":"sNDA","nota":"Artrite psoriasica.","move":"+3%"},
    {"data":"2026-02-25","ticker":"ENSG","azienda":"Ensergo","farmaco":"DESMODA","esito":"APPROVATO","fase":"NDA","nota":"Diabete insipido centrale.","move":"+45%"},
    {"data":"2026-01-14","ticker":"CUTX","azienda":"Sentynl/Cyprium","farmaco":"CUTX-101","esito":"APPROVATO","fase":"NDA","nota":"Malattia di Menkes.","move":"+85%"},
    {"data":"2026-01-10","ticker":"ATRA","azienda":"Atara Bio","farmaco":"Tabelecleucel","esito":"BOCCIATO","fase":"BLA","nota":"EBV+ PTLD. CRL.","move":"-62%"},
    {"data":"2025-12-16","ticker":"ALDX","azienda":"Aldeyra","farmaco":"Reproxalap","esito":"RINVIATO","fase":"NDA","nota":"PDUFA esteso a mar.2026.","move":"+18%"},
]

PHASE_DATA = {"3":{"ok":58,"pos":"+20-60%","neg":"-50-80%"},"2":{"ok":29,"pos":"+30-80%","neg":"-40-70%"},"1":{"ok":52,"pos":"+15-40%","neg":"-20-50%"}}
ENDPOINT_IT = {"overall survival":"Sopravvivenza","progression-free survival":"Senza peggioramento","progression free survival":"Senza peggioramento","objective response rate":"% tumore ridotto","overall response rate":"% miglioramento","complete response":"% tumore scomparso","adverse events":"Effetti collaterali","safety":"Sicurezza","hba1c":"Controllo diabete","pain":"Riduzione dolore","quality of life":"Qualita vita","ocular discomfort":"Fastidio occhi","seizure frequency":"Crisi epilettiche","change in bmi":"Cambio peso"}

def ep_it(text):
    if not text: return "Non specificato"
    for k,v in ENDPOINT_IT.items():
        if k in text.lower(): return v
    return text[:50]

def fmt_cap(cap):
    if cap >= 1e9: return f"${cap/1e9:.2f}B"
    elif cap >= 1e6: return f"${cap/1e6:.0f}M"
    return "N/D"


# ==============================================
# BATCH MARKET DATA — 1 chiamata per TUTTI i ticker
# ==============================================

@st.cache_data(ttl=900)
def batch_download_prices(tickers_str):
    # yf.download scarica TUTTI i ticker in una sola richiesta HTTP
    # Molto piu veloce e affidabile di 16 chiamate .info separate
    tickers = tickers_str.split(",")
    result = {}
    try:
        # Download storico 1 mese per tutti
        df = yf.download(tickers, period="1mo", group_by="ticker", progress=False, timeout=15)
        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    t_data = df
                else:
                    t_data = df[ticker] if ticker in df.columns.get_level_values(0) else None
                if t_data is None or t_data.empty:
                    result[ticker] = _empty_stock()
                    continue
                t_data = t_data.dropna(how="all")
                if t_data.empty:
                    result[ticker] = _empty_stock()
                    continue
                last_close = float(t_data["Close"].iloc[-1])
                prev_close = float(t_data["Close"].iloc[-2]) if len(t_data) >= 2 else last_close
                change = round(((last_close - prev_close) / prev_close * 100), 2) if prev_close else 0
                last_vol = int(t_data["Volume"].iloc[-1]) if "Volume" in t_data else 0
                avg_vol = int(t_data["Volume"].mean()) if "Volume" in t_data else 1
                vol_ratio = round(last_vol / avg_vol, 2) if avg_vol > 0 else 0
                # Trend volume: ultimi 5gg vs precedenti
                vol_trend = "neutro"
                if len(t_data) >= 10 and "Volume" in t_data:
                    rv = t_data["Volume"].tail(5).mean()
                    ov = t_data["Volume"].tail(15).head(10).mean()
                    if ov > 0:
                        vc = (rv - ov) / ov
                        if vc > 0.5: vol_trend = "spike"
                        elif vc > 0.2: vol_trend = "crescente"
                        elif vc < -0.2: vol_trend = "calante"
                # Price trend
                price_trend = "neutro"
                if len(t_data) >= 5:
                    p5 = t_data["Close"].tail(5).mean()
                    pa = t_data["Close"].mean()
                    if pa > 0:
                        r = (p5 - pa) / pa
                        if r > 0.05: price_trend = "sale"
                        elif r < -0.05: price_trend = "scende"
                result[ticker] = {
                    "price": round(last_close, 2), "change": change,
                    "vol_now": last_vol, "vol_avg": avg_vol, "vol_ratio": vol_ratio,
                    "vol_trend": vol_trend, "price_trend": price_trend, "ok_price": True,
                }
            except:
                result[ticker] = _empty_stock()
    except:
        for ticker in tickers:
            result[ticker] = _empty_stock()
    return result

@st.cache_data(ttl=900)
def batch_get_info(tickers_str):
    # Prende market cap, short interest, pre/post market per ogni ticker
    # Queste richiedono .info individuale ma sono opzionali
    tickers = tickers_str.split(",")
    result = {}
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            cap = info.get("marketCap", 0) or 0
            si = info.get("shortPercentOfFloat", 0) or 0
            if si and si < 1: si *= 100
            pre_price = info.get("preMarketPrice", 0)
            pre_change = info.get("preMarketChangePercent", 0)
            post_price = info.get("postMarketPrice", 0)
            post_change = info.get("postMarketChangePercent", 0)
            result[ticker] = {
                "cap": cap, "cap_str": fmt_cap(cap), "short": round(si, 1),
                "pre_price": round(pre_price, 2) if pre_price else None,
                "pre_change": round(pre_change * 100, 2) if pre_change and abs(pre_change) < 1 else round(pre_change, 2) if pre_change else None,
                "post_price": round(post_price, 2) if post_price else None,
                "post_change": round(post_change * 100, 2) if post_change and abs(post_change) < 1 else round(post_change, 2) if post_change else None,
                "ok_info": True,
            }
        except:
            result[ticker] = {"cap": 0, "cap_str": "N/D", "short": 0,
                              "pre_price": None, "pre_change": None,
                              "post_price": None, "post_change": None, "ok_info": False}
    return result

def _empty_stock():
    return {"price":0,"change":0,"vol_now":0,"vol_avg":0,"vol_ratio":0,"vol_trend":"N/D","price_trend":"N/D","ok_price":False}

def merge_stock_data(price_data, info_data):
    return {
        "price": price_data.get("price", 0),
        "change": price_data.get("change", 0),
        "vol_now": price_data.get("vol_now", 0),
        "vol_avg": price_data.get("vol_avg", 0),
        "vol_ratio": price_data.get("vol_ratio", 0),
        "vol_trend": price_data.get("vol_trend", "N/D"),
        "price_trend": price_data.get("price_trend", "N/D"),
        "cap": info_data.get("cap", 0),
        "cap_str": info_data.get("cap_str", "N/D"),
        "short": info_data.get("short", 0),
        "pre_price": info_data.get("pre_price"),
        "pre_change": info_data.get("pre_change"),
        "post_price": info_data.get("post_price"),
        "post_change": info_data.get("post_change"),
        "ok": price_data.get("ok_price", False),
    }


# ==============================================
# CLINICALTRIALS.GOV
# ==============================================

@st.cache_data(ttl=3600)
def get_trials(company):
    try:
        r = requests.get("https://clinicaltrials.gov/api/v2/studies", params={
            "query.spons": company,
            "filter.overallStatus": "RECRUITING|ACTIVE_NOT_RECRUITING|ENROLLING_BY_INVITATION|NOT_YET_RECRUITING",
            "pageSize": 8,
            "fields": "NCTId,BriefTitle,Phase,Condition,EnrollmentInfo,DesignInfo,PrimaryOutcome,PrimaryCompletionDate",
        }, timeout=8)
        if r.status_code != 200: return []
        out = []
        for s in r.json().get("studies", []):
            p = s.get("protocolSection", {})
            ident = p.get("identificationModule", {})
            stat = p.get("statusModule", {})
            des = p.get("designModule", {})
            cond = p.get("conditionsModule", {})
            outc = p.get("outcomesModule", {})
            phases = des.get("phases", []) if des else []
            ei = des.get("enrollmentInfo", {}) if des else {}
            di = des.get("designInfo", {}) if des else {}
            mi = di.get("maskingInfo", {}) if di else {}
            po = outc.get("primaryOutcomes", []) if outc else []
            pcd = stat.get("primaryCompletionDateStruct", {}) if stat else {}
            out.append({
                "nct": ident.get("nctId", ""), "title": ident.get("briefTitle", ""),
                "phase": ", ".join(phases) if phases else "N/A",
                "conditions": ", ".join(cond.get("conditions", [])[:2]) if cond else "N/D",
                "enrollment": ei.get("count", 0) if ei else 0,
                "mask": mi.get("masking", "") if mi else "",
                "is_rand": "RANDOMIZED" in (di.get("allocation", "").upper()) if di else False,
                "endpoint": po[0].get("measure", "") if po else "",
                "completion": pcd.get("date", "") if pcd else "",
            })
        return out
    except:
        return []


def calc_window(cs, ps):
    try:
        if len(cs) == 7: cd = datetime.strptime(cs + "-28", "%Y-%m-%d")
        elif len(cs) >= 10: cd = datetime.strptime(cs[:10], "%Y-%m-%d")
        else: return None
    except: return None
    ws = cd + timedelta(weeks=2); we = cd + timedelta(weeks=8)
    p = ps.upper().replace(" ", "")
    if "PHASE3" in p: pkey = "3"
    elif "PHASE2" in p: pkey = "2"
    elif "PHASE1" in p: pkey = "1"
    else: return None
    rup = {"3": 45, "2": 30, "1": 15}[pkey]
    rs = ws - timedelta(days=rup); now = datetime.now()
    if now < rs: status = "PRESTO"
    elif now < ws: status = "RUNUP"
    elif now <= we: status = "APERTA"
    else: status = "SCADUTA"
    return {"ws": ws, "we": we, "status": status, "pkey": pkey, "pd": PHASE_DATA[pkey]}


def render_metrics(stk):
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Prezzo", f"${stk['price']}" if stk["price"] else "N/D",
              f"{stk['change']:+.1f}%" if stk["price"] else None,
              delta_color="normal" if stk["change"] >= 0 else "inverse")
    m2.metric("Market Cap", stk["cap_str"])
    m3.metric("Vol/Media", f"{stk['vol_ratio']}x" if stk["vol_ratio"] else "N/D",
              "ESPLOSIVO" if stk["vol_ratio"] >= 3 else "Alto" if stk["vol_ratio"] >= 2 else None)
    m4.metric("Short", f"{stk['short']}%" if stk["short"] else "N/D",
              "Molto alto" if stk["short"] >= 20 else "Elevato" if stk["short"] >= 10 else None)
    v1, v2, v3 = st.columns(3)
    v1.metric("Volume oggi", f"{stk['vol_now']:,.0f}" if stk['vol_now'] else "N/D")
    v2.metric("Volume medio", f"{stk['vol_avg']:,.0f}" if stk['vol_avg'] else "N/D")
    vt = stk.get("vol_trend", "N/D")
    v3.metric("Trend 5gg", "SPIKE" if vt == "spike" else "Crescente" if vt == "crescente" else "Calante" if vt == "calante" else "Neutro")
    pm1, pm2 = st.columns(2)
    pm1.metric("Pre-Market", f"${stk['pre_price']}" if stk.get("pre_price") else "Chiuso",
               f"{stk['pre_change']:+.1f}%" if stk.get("pre_change") else None)
    pm2.metric("After-Hours", f"${stk['post_price']}" if stk.get("post_price") else "Chiuso",
               f"{stk['post_change']:+.1f}%" if stk.get("post_change") else None)


def render_trials(trials, ticker):
    with st.expander(f"Trial ({len(trials)}) — {ticker}"):
        if not trials:
            st.write("Nessun trial trovato.")
            return
        for t in trials:
            w = calc_window(t["completion"], t["phase"])
            ep = ep_it(t["endpoint"])
            ph = t["phase"].upper().replace(" ", "")
            pkey = "3" if "PHASE3" in ph else "2" if "PHASE2" in ph else "1" if "PHASE1" in ph else None
            pd_info = PHASE_DATA.get(pkey, {})
            sol = 0
            if t["enrollment"] and t["enrollment"] >= 500: sol += 3
            elif t["enrollment"] and t["enrollment"] >= 100: sol += 2
            elif t["enrollment"]: sol += 1
            if pkey == "3": sol += 2
            elif pkey == "2": sol += 1
            if "DOUBLE" in (t.get("mask", "").upper()): sol += 2
            elif "SINGLE" in (t.get("mask", "").upper()): sol += 1
            if t.get("is_rand"): sol += 1
            sol_lbl = "ALTA" if sol >= 7 else "MEDIA" if sol >= 4 else "BASSA"
            st.write(f"**{t['title'][:90]}**")
            st.caption(f"{t['phase']} | {t['conditions']} | {t['enrollment'] or '?'} paz. | Solidita: **{sol_lbl}**")
            st.caption(f"Endpoint: **{ep}**")
            if pd_info:
                st.caption(f"Successo: **{pd_info['ok']}%** | ok: **{pd_info['pos']}** | ko: **{pd_info['neg']}**")
            if w:
                if w["status"] == "APERTA":
                    st.error(f"FINESTRA APERTA - {w['ws'].strftime('%d/%m')} - {w['we'].strftime('%d/%m/%Y')}")
                elif w["status"] == "RUNUP":
                    st.warning(f"RUNUP - {w['ws'].strftime('%d/%m')} - {w['we'].strftime('%d/%m/%Y')}")
                elif w["status"] == "PRESTO":
                    st.caption(f"Finestra: {w['ws'].strftime('%d/%m')} - {w['we'].strftime('%d/%m/%Y')}")
            st.caption(f"[{t['nct']}](https://clinicaltrials.gov/study/{t['nct']})")
            st.divider()


# ==========================================
# APP
# ==========================================

st.title("FDA Radar")
st.caption("Volumi + Catalizzatori + Storico")

try:
    obs = (datetime.now() - datetime.strptime(DATA_AGG, "%Y-%m-%d")).days
except:
    obs = 999
if obs > 14: st.error(f"Dati PDUFA vecchi di {obs} giorni!")
elif obs > 7: st.warning(f"Dati PDUFA di {obs} giorni fa.")

with st.expander("Come leggere i segnali"):
    st.write("Volume/media 3x+ = qualcuno si posiziona pesante")
    st.write("Pre-market/After-hours = movimenti fuori orario")
    st.write("Volume + prezzo sale = comprano. Volume + prezzo scende = vendono.")
    st.write("Finestra APERTA = risultati trial possono uscire ora")
    st.write("Short alto + notizia positiva = possibile squeeze")

st.subheader("Movimenti storici per fase")
c1, c2, c3 = st.columns(3)
c1.metric("Phase 1", "52% successo", "ok +15-40% | ko -20-50%")
c2.metric("Phase 2", "29% successo", "ok +30-80% | ko -40-70%")
c3.metric("Phase 3", "58% successo", "ok +20-60% | ko -50-80%")
st.divider()


# ==========================================
# CARICAMENTO DATI — BATCH (1 chiamata per tutti)
# ==========================================

all_tickers = [t for t, c in WATCHLIST]
tickers_str = ",".join(all_tickers)

st.caption("Caricamento dati di mercato...")

# Step 1: Prezzi + volumi (1 sola chiamata HTTP per tutti)
prices = batch_download_prices(tickers_str)

# Step 2: Market cap + short + pre/post (chiamate individuali, ma opzionali)
infos = batch_get_info(tickers_str)

# Merge
all_stocks = {}
for ticker in all_tickers:
    p = prices.get(ticker, _empty_stock())
    i = infos.get(ticker, {"cap": 0, "cap_str": "N/D", "short": 0, "pre_price": None, "pre_change": None, "post_price": None, "post_change": None})
    all_stocks[ticker] = merge_stock_data(p, i)

st.caption(f"Dati caricati per {sum(1 for s in all_stocks.values() if s['ok'])} / {len(all_tickers)} titoli")


# ==========================================
# SEZIONE 1: VERDETTI FDA — SEMPRE VISIBILI
# ==========================================

st.subheader("Verdetti FDA imminenti")

for pm in PDUFA_LIST:
    try:
        g = (datetime.strptime(pm["pdufa"], "%Y-%m-%d").date() - datetime.now().date()).days
    except:
        g = -999
    if g < -5: continue

    if g <= 0:
        st.error(f"VERDETTO OGGI: **{pm['ticker']}** - {pm['drug']} ({pm['indication']})")
    elif g <= 3:
        st.error(f"VERDETTO TRA {g}g: **{pm['ticker']}** - {pm['drug']} ({pm['indication']})")
    elif g <= 7:
        st.warning(f"VERDETTO TRA {g}g: **{pm['ticker']}** - {pm['drug']} ({pm['indication']})")
    else:
        st.info(f"VERDETTO TRA {g}g: **{pm['ticker']}** - {pm['drug']} ({pm['indication']})")

    st.write(pm["nota"])
    if pm["crl"] > 0: st.caption(f"Bocciature precedenti: {pm['crl']}")
    if pm.get("labeling"): st.caption("FDA sta scrivendo il foglietto (segnale positivo)")

    stk = all_stocks.get(pm["ticker"])
    if stk and stk["ok"]:
        render_metrics(stk)
    elif stk and stk["price"] > 0:
        st.metric("Prezzo", f"${stk['price']}", f"{stk['change']:+.1f}%")
        st.caption("Dati parziali — market cap/volumi non disponibili")
    else:
        st.warning(f"Dati di mercato non disponibili per {pm['ticker']}")

    trials = get_trials(pm.get("company", pm["ticker"]))
    render_trials(trials, pm["ticker"])
    st.divider()


# ==========================================
# SEZIONE 2: SCANSIONE RADAR
# ==========================================

st.subheader("Scansione radar")

pdufa_tickers = {p["ticker"] for p in PDUFA_LIST}
radar_hot = []
radar_silent = []

for ticker, company in WATCHLIST:
    if ticker in pdufa_tickers: continue
    stk = all_stocks.get(ticker)
    if not stk or not stk["ok"]: continue
    if not (CAP_MIN <= stk["cap"] <= CAP_MAX): continue

    trials = get_trials(company)
    best_w = None
    for t in trials:
        w = calc_window(t["completion"], t["phase"])
        if w and w["status"] in ("APERTA", "RUNUP"):
            if best_w is None or w["status"] == "APERTA": best_w = w

    signals = []; alert = 0
    if best_w:
        if best_w["status"] == "APERTA": signals.append("FINESTRA APERTA"); alert += 4
        elif best_w["status"] == "RUNUP": signals.append("Zona pre-risultati"); alert += 2
    if stk["vol_ratio"] >= 3: signals.append(f"VOLUME {stk['vol_ratio']}x media"); alert += 3
    elif stk["vol_ratio"] >= 2: signals.append(f"Volume {stk['vol_ratio']}x"); alert += 2
    elif stk["vol_ratio"] >= 1.5: signals.append(f"Volume {stk['vol_ratio']}x"); alert += 1
    if stk["vol_trend"] == "spike": signals.append("Spike volume 5gg"); alert += 2
    elif stk["vol_trend"] == "crescente": signals.append("Volume crescente"); alert += 1
    if stk["short"] >= 20: signals.append(f"Short {stk['short']}%"); alert += 2
    elif stk["short"] >= 10: signals.append(f"Short {stk['short']}%"); alert += 1

    item = {"ticker": ticker, "company": company, "stk": stk, "trials": trials, "signals": signals, "alert": min(alert, 10)}
    if alert > 0: radar_hot.append(item)
    else: radar_silent.append(item)

radar_hot.sort(key=lambda x: -x["alert"])

if radar_hot:
    for item in radar_hot:
        stk = item["stk"]
        badge = "ALTO" if item["alert"] >= 7 else "MEDIO" if item["alert"] >= 4 else "BASSO"
        st.markdown(f"### {item['ticker']} - {item['company']}")
        st.caption(f"Allerta: {badge} ({item['alert']}/10)")
        for sig in item["signals"]: st.write(sig)
        render_metrics(stk)
        render_trials(item["trials"], item["ticker"])
        st.divider()
else:
    st.caption("Nessun altro titolo con segnali attivi.")

if radar_silent:
    with st.expander(f"Titoli senza segnali ({len(radar_silent)})"):
        for item in radar_silent:
            st.caption(f"**{item['ticker']}** - {item['company']} | {item['stk']['cap_str']} | ${item['stk']['price']} | {len(item['trials'])} trial")

st.divider()

# ==========================================
# STORICO in expander
# ==========================================

with st.expander("Storico verdetti FDA recenti"):
    for item in STORICO:
        st.write(f"**{item['data']}** - **{item['ticker']}** ({item['azienda']}) - {item['farmaco']}")
        st.caption(f"{item['esito']} | {item['fase']} | Movimento: **{item.get('move','N/D')}** | {item['nota']}")
        st.divider()

with st.expander("Legenda + limiti"):
    st.write("Volume/media = volume oggi / media 1 mese")
    st.write("Pre-market 4:00-9:30 ET | After-hours 16:00-20:00 ET")
    st.write("Batch download: 1 chiamata per tutti i ticker (molto piu veloce)")
    st.write("Limiti: yfinance non ufficiale | Aggiorna PDUFA settimanalmente")

st.caption(f"v14 | PDUFA: {DATA_AGG} | App educativa - non e consulenza finanziaria | fda.gov")
