"""
POTENTIAL FDA APPROVAL v4.0
Cacciatore di catalizzatori FDA — Small & Mid Cap
CORREZIONI INGEGNERE SCETTICO: tutte e 11
pip install streamlit yfinance plotly pandas
streamlit run potential_fda_approval.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

st.set_page_config(
    page_title="Potential FDA Approval",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# [FIX 4] Data aggiornamento catalizzatori — cambiala ogni volta che aggiorni data=[]
DATA_ULTIMO_AGGIORNAMENTO = "2026-03-15"

# CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 50%, #0d0d2b 100%);
    }
    .biotech-card {
        background: linear-gradient(145deg, #1e1e3f, #2a2a5c);
        border: 1px solid #3a3a7c; border-radius: 16px;
        padding: 24px; margin: 12px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .biotech-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(100,100,255,0.15);
    }
    .badge-green {
        background: linear-gradient(135deg, #00c853, #00e676);
        color: #000; padding: 4px 14px; border-radius: 20px;
        font-weight: 700; font-size: 0.8em; display: inline-block;
    }
    .badge-yellow {
        background: linear-gradient(135deg, #ffc107, #ffea00);
        color: #000; padding: 4px 14px; border-radius: 20px;
        font-weight: 700; font-size: 0.8em; display: inline-block;
    }
    .badge-red {
        background: linear-gradient(135deg, #ff1744, #ff5252);
        color: #fff; padding: 4px 14px; border-radius: 20px;
        font-weight: 700; font-size: 0.8em; display: inline-block;
    }
    .badge-blue {
        background: linear-gradient(135deg, #2979ff, #448aff);
        color: #fff; padding: 4px 14px; border-radius: 20px;
        font-weight: 700; font-size: 0.8em; display: inline-block;
    }
    .badge-gray {
        background: linear-gradient(135deg, #616161, #9e9e9e);
        color: #fff; padding: 4px 14px; border-radius: 20px;
        font-weight: 700; font-size: 0.8em; display: inline-block;
    }
    .neon-title {
        font-size: 2.8em; font-weight: 800;
        background: linear-gradient(90deg, #00e5ff, #7c4dff, #ff4081);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 0;
    }
    .neon-subtitle {
        font-size: 1.1em; color: #8888cc;
        text-align: center; margin-top: 4px;
    }
    .glossario-box {
        background: rgba(30,30,80,0.6);
        border-left: 4px solid #7c4dff;
        border-radius: 8px; padding: 16px 20px;
        margin: 8px 0; font-size: 0.92em;
    }
    .glossario-box strong { color: #b388ff; }
    .alert-box-green {
        background: linear-gradient(135deg, #1b5e20, #2e7d32);
        border: 2px solid #00e676; border-radius: 12px;
        padding: 16px; margin: 8px 0; color: #c8e6c9;
    }
    .alert-box-orange {
        background: linear-gradient(135deg, #e65100, #f57c00);
        border: 2px solid #ffab40; border-radius: 12px;
        padding: 16px; margin: 8px 0; color: #fff3e0;
    }
    .alert-box-red {
        background: linear-gradient(135deg, #b71c1c, #c62828);
        border: 2px solid #ff5252; border-radius: 12px;
        padding: 16px; margin: 8px 0; color: #ffcdd2;
    }
    .indice-disclaimer {
        background: rgba(255,255,255,0.05);
        border: 1px dashed #7c4dff; border-radius: 8px;
        padding: 10px 14px; margin: 4px 0;
        font-size: 0.82em; color: #aaaacc;
    }
    .cap-info {
        background: rgba(41,121,255,0.15);
        border: 1px solid #2979ff; border-radius: 10px;
        padding: 12px 16px; margin: 8px 0;
    }
    [data-testid="stMetric"] {
        background: rgba(30,30,80,0.5);
        border: 1px solid #3a3a7c;
        border-radius: 12px; padding: 16px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #12122e, #1a1a40);
    }
</style>
""", unsafe_allow_html=True)


# GLOSSARIO
GLOSSARIO = {
    "PDUFA Date": {"da_bar": "Giorno del Verdetto", "spiegazione": "Il giorno in cui la FDA dice SI o NO al farmaco."},
    "AdComm": {"da_bar": "La Giuria degli Esperti", "spiegazione": "Comitato di medici/scienziati che vota se il farmaco funziona. >90% si = quasi fatta. La FDA non ne convoca dal luglio 2025."},
    "Market Cap": {"da_bar": "Quanto vale il negozio", "spiegazione": "Prezzo azione x tutte le azioni. Noi cerchiamo 200M-2B$: grandi da non fallire, piccoli da esplodere."},
    "Cash Runway": {"da_bar": "Benzina nel serbatoio", "spiegazione": "Mesi di sopravvivenza con la cassa attuale. Se l'azienda guadagna, mostriamo 'Produce benzina'."},
    "Short Interest": {"da_bar": "Chi scommette CONTRO", "spiegazione": "% che scommette sul ribasso. Se tanti e arriva approvazione: BOOM (short squeeze)."},
    "Labeling Discussion": {"da_bar": "Stanno scrivendo il foglietto!", "spiegazione": "La FDA discute il foglietto illustrativo. Segnale MOLTO positivo: pensano a COME venderlo, non SE."},
    "CRL (Complete Response Letter)": {"da_bar": "Bocciato (con appunti)", "spiegazione": "La FDA dice NO ma spiega cosa manca. Ogni bocciatura passata RIDUCE il nostro Indice di Fiducia."},
    "Priority Review": {"da_bar": "Corsia preferenziale", "spiegazione": "Esame in 6 mesi anziche 10 per malattie gravi."},
    "Breakthrough Therapy": {"da_bar": "Farmaco rivoluzionario", "spiegazione": "La FDA riconosce che e molto meglio di tutto cio che esiste."},
    "Orphan Drug": {"da_bar": "Farmaco per malattia rara", "spiegazione": "Malattia rara: vantaggi fiscali + 7 anni esclusiva."},
    "Indice di Fiducia": {"da_bar": "Il nostro termometro", "spiegazione": "NON e una probabilita reale. E un punteggio relativo (0-99) per CONFRONTARE i catalizzatori. Non significa 'X% di probabilita'."},
}


# DATABASE CATALIZZATORI
# [FIX 9] Nuovo campo crl_precedenti: penalizza bocciature passate
data = [
    {
        "ticker": "ALDX",
        "azienda": "Aldeyra Therapeutics",
        "farmaco": "Reproxalap (collirio)",
        "indicazione": "Malattia dell'occhio secco",
        "pdufa_date": "2026-03-16",
        "adcomm_voto": None,
        "adcomm_data": None,
        "tipo_review": "Standard Review",
        "designazioni": ["Fast Track"],
        "labeling_discussion": True,
        "fase": "NDA",
        "crl_precedenti": 2,
        "note": "3a sottomissione dopo 2 CRL (apr.2024, apr.2025). FDA ha condiviso bozza etichetta dic.2025 — segnale positivo. Field trial NON ha raggiunto endpoint primario ma FDA lo ritiene supportivo. AbbVie: opzione licenza $100M. Fonte: ir.aldeyra.com",
        "rischio": "medio-alto",
    },
    {
        "ticker": "RYTM",
        "azienda": "Rhythm Pharmaceuticals",
        "farmaco": "Setmelanotide (Imcivree)",
        "indicazione": "Obesita ipotalamica acquisita (espansione)",
        "pdufa_date": "2026-03-20",
        "adcomm_voto": None,
        "adcomm_data": None,
        "tipo_review": "Priority Review",
        "designazioni": ["Orphan Drug"],
        "labeling_discussion": False,
        "fase": "sNDA",
        "crl_precedenti": 0,
        "note": "Imcivree GIA APPROVATO per BBS/POMC — espansione. Phase 3 TRANSCEND: -18.8% BMI vs placebo (p<0.0001), N=142. Azienda commerciale: $57M ricavi Q4 2025. Fonte: ir.rhythmtx.com",
        "rischio": "basso",
    },
    {
        "ticker": "RCKT",
        "azienda": "Rocket Pharmaceuticals",
        "farmaco": "Kresladi (terapia genica)",
        "indicazione": "Deficit adesione leucocitaria (LAD-I)",
        "pdufa_date": "2026-03-28",
        "adcomm_voto": None,
        "adcomm_data": None,
        "tipo_review": "Standard Review",
        "designazioni": ["Orphan Drug", "Breakthrough Therapy"],
        "labeling_discussion": False,
        "fase": "BLA",
        "crl_precedenti": 1,
        "note": "Ri-sottomissione BLA dopo 1 CRL. Phase 1/2: 100% sopravvivenza a 1+ anno. LAD-I: ultra-rara, fatale nell'infanzia senza trapianto. Fonte: ir.rocketpharma.com",
        "rischio": "medio",
    },
    {
        "ticker": "DNLI",
        "azienda": "Denali Therapeutics",
        "farmaco": "Tividenofusp alfa (DNL310)",
        "indicazione": "Sindrome di Hunter (MPS II)",
        "pdufa_date": "2026-04-05",
        "adcomm_voto": None,
        "adcomm_data": None,
        "tipo_review": "Priority Review",
        "designazioni": ["Orphan Drug", "Breakthrough Therapy"],
        "labeling_discussion": False,
        "fase": "BLA (accelerated approval)",
        "crl_precedenti": 0,
        "note": "Dati su NEJM gen.2026. Biomarker CSF -91%. $966M cassa. Royalty Pharma $275M. Market cap ~$3.4B: FUORI target 200M-2B. Fonte: investors.denalitherapeutics.com",
        "rischio": "medio",
    },
]


# FUNZIONI

# [FIX 2] Cache con TTL naturale, NON svuotata ad ogni refresh. Retry integrato.
@st.cache_data(ttl=300)
def fetch_stock(ticker):
    for attempt in range(2):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            # [FIX 7] Validazione ticker
            if not info or (info.get("regularMarketPrice") is None and info.get("currentPrice") is None and info.get("shortName") is None):
                return _empty(ticker, f"Ticker '{ticker}' non trovato su Yahoo Finance")
            hist = stock.history(period="3mo")
            mc = info.get("marketCap", 0)
            price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            prev = info.get("previousClose", price)
            chg = ((price - prev) / prev * 100) if prev else 0
            cash = info.get("totalCash", 0)
            ocf = info.get("operatingCashflow", 0)
            # [FIX 6] Cash runway migliorata
            if ocf and ocf < 0:
                runway = round(cash / abs(ocf) * 12, 1)
                cstatus = "burn"
            elif ocf and ocf > 0:
                runway = None
                cstatus = "positive"
            else:
                runway = None
                cstatus = "unknown"
            si = info.get("shortPercentOfFloat", 0)
            if si and si < 1:
                si *= 100
            return {
                "prezzo": round(price, 2), "variazione": round(chg, 2),
                "market_cap": mc, "market_cap_str": _fmt(mc),
                "market_cap_ok": mc > 0,
                "cash": cash, "cash_str": _fmt(cash),
                "cash_runway_mesi": runway, "cash_status": cstatus,
                "short_interest": round(si, 1) if si else 0,
                "storico": hist, "nome": info.get("shortName", ticker),
                "errore": None, "ticker_valido": True,
            }
        except Exception as e:
            if attempt == 0:
                time.sleep(2)
                continue
            return _empty(ticker, str(e))
    return _empty(ticker, "Errore sconosciuto")

def _empty(ticker, errore=""):
    return {
        "prezzo": 0, "variazione": 0, "market_cap": 0,
        "market_cap_str": "N/D", "market_cap_ok": False,
        "cash": 0, "cash_str": "N/D",
        "cash_runway_mesi": None, "cash_status": "unknown",
        "short_interest": 0, "storico": pd.DataFrame(),
        "nome": ticker, "errore": errore, "ticker_valido": False,
    }

def _fmt(v):
    if v >= 1e9: return f"${v/1e9:.2f}B"
    elif v >= 1e6: return f"${v/1e6:.1f}M"
    elif v > 0: return f"${v:,.0f}"
    return "N/D"

def giorni_al_verdetto(pdufa):
    try: return (datetime.strptime(pdufa, "%Y-%m-%d") - datetime.now()).days
    except: return -999

def semaforo(r):
    r = r.lower()
    if r == "basso": return "🟢 BASSO"
    elif r == "medio": return "🟡 MEDIO"
    elif r in ("medio-alto", "alto"): return "🔴 ALTO"
    return "⚪ N/D"

# [FIX 1+9] Indice di Fiducia (non "Score %")
# Pesi documentati, penalizza CRL precedenti
def calcola_indice(item):
    s = 50
    v = item.get("adcomm_voto")
    if v is not None:
        if v >= 90: s += 25
        elif v >= 75: s += 15
        elif v >= 60: s += 5
        else: s -= 10
    if item.get("labeling_discussion"): s += 15
    if item.get("tipo_review") == "Priority Review": s += 5
    desig = item.get("designazioni", [])
    if "Breakthrough Therapy" in desig: s += 5
    if "Fast Track" in desig: s += 3
    if "Orphan Drug" in desig: s += 2
    fase = item.get("fase", "")
    if "sNDA" in fase: s += 5
    crl = item.get("crl_precedenti", 0)
    s -= crl * 12  # [FIX 9] -12 per ogni bocciatura
    return max(0, min(s, 99))

def badge_indice(sc):
    if sc >= 75: return "badge-green"
    elif sc >= 55: return "badge-yellow"
    elif sc >= 35: return "badge-blue"
    return "badge-red"

# [FIX 5] Classifica market cap senza bypass silenzioso
def classifica_cap(mc, ok, mn, mx):
    if not ok or mc == 0: return "dato_mancante"
    if mn <= mc <= mx: return "in_range"
    return "fuori_range"


# HEADER
st.markdown('<p class="neon-title">🧬 Potential FDA Approval</p>', unsafe_allow_html=True)
st.markdown('<p class="neon-subtitle">Catalizzatori FDA — Small &amp; Mid Cap Biotech (200M-2B USD)</p>', unsafe_allow_html=True)
st.markdown("---")

# [FIX 4] Avviso dati obsoleti
try:
    data_agg = datetime.strptime(DATA_ULTIMO_AGGIORNAMENTO, "%Y-%m-%d")
    giorni_obs = (datetime.now() - data_agg).days
except: giorni_obs = 999

if giorni_obs > 14:
    st.markdown(f'<div class="alert-box-red">🚨 <strong>DATI VECCHI DI {giorni_obs} GIORNI!</strong> La lista catalizzatori risale al {DATA_ULTIMO_AGGIORNAMENTO}. Aggiorna data=[] e DATA_ULTIMO_AGGIORNAMENTO.</div>', unsafe_allow_html=True)
elif giorni_obs > 7:
    st.markdown(f'<div class="alert-box-orange">⚠️ <strong>Dati di {giorni_obs} giorni fa</strong> — le date PDUFA possono cambiare.</div>', unsafe_allow_html=True)


# SIDEBAR
with st.sidebar:
    st.markdown("## Filtri")
    st.markdown("### Valore azienda")
    cap_min_in = st.number_input("Minimo ($M)", 0, 50000, 200, 50)
    cap_max_in = st.number_input("Massimo ($M)", 0, 50000, 2000, 100)
    mostra_fuori = st.checkbox("Mostra anche fuori range", value=True)
    mostra_no_cap = st.checkbox("Mostra se cap non disponibile", value=True)
    st.markdown("---")
    max_giorni = st.slider("Verdetto entro (giorni)", 7, 90, 30, 7)
    filtro_rischio = st.multiselect("Rischio", ["basso","medio","medio-alto","alto"], default=["basso","medio","medio-alto","alto"])
    st.markdown("---")

    # [FIX 8] AdComm contestuale
    st.markdown("### Giuria Esperti (AdComm)")
    ha_adcomm = any(d.get("adcomm_voto") is not None for d in data)
    if ha_adcomm:
        solo_unanime = st.checkbox("Solo AdComm unanime (>90%)")
    else:
        st.markdown('<div class="cap-info">Nessun catalizzatore ha un voto AdComm. La FDA non convoca dal luglio 2025. Prossimo: 30 aprile 2026. Il filtro si attiva quando ci saranno dati.</div>', unsafe_allow_html=True)
        solo_unanime = False

    solo_labeling = st.checkbox("Solo con Labeling Discussion")
    st.markdown("---")

    # [FIX 3] Auto-refresh
    st.markdown("### Auto-Aggiornamento")
    auto_refresh = st.checkbox("Aggiorna automaticamente")
    refresh_sec = st.selectbox("Intervallo (sec)", [60, 120, 300], index=0)
    st.markdown("---")

    st.markdown("### Dizionario 'da bar'")
    with st.expander("Clicca per capire tutto"):
        for term, info in GLOSSARIO.items():
            st.markdown(f'<div class="glossario-box"><strong>{info["da_bar"]}</strong> ({term})<br>{info["spiegazione"]}</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("⚠️ **Disclaimer**: App educativa. Non e consulenza finanziaria. Verifica su [fda.gov](https://www.fda.gov).")


# FILTRAGGIO
in_range_list = []
fuori_range_list = []
no_cap_list = []
ticker_invalidi = []
cap_min_val = cap_min_in * 1e6
cap_max_val = cap_max_in * 1e6

for item in data:
    g = giorni_al_verdetto(item["pdufa_date"])
    if g < 0 or g > max_giorni: continue
    if item.get("rischio","medio").lower() not in filtro_rischio: continue
    if solo_unanime:
        v = item.get("adcomm_voto")
        if v is None or v < 90: continue
    if solo_labeling and not item.get("labeling_discussion"): continue
    stock = fetch_stock(item["ticker"])
    if not stock["ticker_valido"]:
        ticker_invalidi.append((item["ticker"], stock["errore"]))
    cat = classifica_cap(stock["market_cap"], stock["market_cap_ok"], cap_min_val, cap_max_val)
    if cat == "in_range": in_range_list.append((item, stock))
    elif cat == "fuori_range": fuori_range_list.append((item, stock))
    else: no_cap_list.append((item, stock))

for lst in [in_range_list, fuori_range_list, no_cap_list]:
    lst.sort(key=lambda x: giorni_al_verdetto(x[0]["pdufa_date"]))

# [FIX 7] Ticker non validi
for tk, err in ticker_invalidi:
    st.error(f"🚫 **Ticker '{tk}' non riconosciuto** da Yahoo Finance. Errore: {err}")


# DASHBOARD
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🧬 Totali", len(data))
c2.metric("🎯 Nel range", len(in_range_list))
c3.metric("⚠️ Fuori range", len(fuori_range_list))
c4.metric("❓ Cap ignoto", len(no_cap_list))
c5.metric("🏷️ Labeling", sum(1 for d,_ in in_range_list if d.get("labeling_discussion")))
st.markdown("---")

# [FIX 1] Disclaimer Indice
st.markdown('<div class="indice-disclaimer">📊 <strong>Indice di Fiducia</strong> — punteggio relativo 0-99. <strong>NON e una probabilita di approvazione.</strong> Serve per confrontare i catalizzatori tra loro. Tiene conto di AdComm, labeling, review, designazioni e penalizza le bocciature (CRL). Vedi tabella pesi in fondo.</div>', unsafe_allow_html=True)
st.markdown("")

# ALERT
for d, s in in_range_list + fuori_range_list + no_cap_list:
    if d.get("labeling_discussion"):
        st.markdown(f'<div class="alert-box-green">🏷️ <strong>LABELING IN CORSO — {d["azienda"]} ({d["ticker"]})</strong><br>La FDA sta scrivendo il foglietto per <strong>{d["farmaco"]}</strong>. Stanno pensando a COME venderlo, non SE.</div>', unsafe_allow_html=True)

if not ha_adcomm:
    st.markdown('<div class="alert-box-orange">👨‍⚖️ <strong>NESSUN ADCOMM ATTIVO</strong> — la FDA non convoca dal luglio 2025. Prossimo: 30 aprile 2026 (AstraZeneca, oncologia).</div>', unsafe_allow_html=True)

# [FIX 10] Alert verdetto imminente
for d, s in in_range_list:
    g = giorni_al_verdetto(d["pdufa_date"])
    if 0 <= g <= 3:
        st.markdown(f'<div class="alert-box-red">🔔 <strong>VERDETTO IMMINENTE — {d["azienda"]} ({d["ticker"]})</strong><br>Mancano <strong>{g} giorni</strong> alla decisione FDA su {d["farmaco"]}! Data: {d["pdufa_date"]}.</div>', unsafe_allow_html=True)
st.markdown("")


# TIMELINE
all_items = (
    [(i,s,"in_range") for i,s in in_range_list]
    + ([(i,s,"fuori_range") for i,s in fuori_range_list] if mostra_fuori else [])
    + ([(i,s,"no_cap") for i,s in no_cap_list] if mostra_no_cap else [])
)

if all_items:
    st.markdown("### Timeline — Prossimi Verdetti")
    fig = go.Figure()
    for item, stock, cat in all_items:
        g = giorni_al_verdetto(item["pdufa_date"])
        idx = calcola_indice(item)
        if cat == "in_range":
            color = "#00e676" if idx>=75 else "#ffc107" if idx>=55 else "#2979ff" if idx>=35 else "#ff5252"
        elif cat == "fuori_range":
            color = "#666688"
        else:
            color = "#9e9e9e"
        suffix = " ⚠️fuori range" if cat=="fuori_range" else " ❓cap ignoto" if cat=="no_cap" else ""
        fig.add_trace(go.Bar(
            x=[g], y=[f"{item['azienda']}{suffix}<br>({item['farmaco']})"],
            orientation="h", marker_color=color,
            text=f"{g}g — Indice {idx}/99", textposition="outside",
            showlegend=False,
            hovertemplate=f"<b>{item['azienda']}</b> ({item['ticker']})<br>Farmaco: {item['farmaco']}<br>PDUFA: {item['pdufa_date']} ({g}g)<br>Indice: {idx}/99<br>Cap: {stock['market_cap_str']}<br>CRL: {item.get('crl_precedenti',0)}<extra></extra>",
        ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Giorni al Verdetto", height=max(250, len(all_items)*90),
        margin=dict(l=20,r=160,t=20,b=40), font=dict(color="#ccccee"),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")


# SCHEDE DETTAGLIO
def render_card(item, stock, cat):
    giorni = giorni_al_verdetto(item["pdufa_date"])
    idx = calcola_indice(item)
    bc = badge_indice(idx)
    crl = item.get("crl_precedenti", 0)
    cap_badge = ""
    if cat == "fuori_range": cap_badge = ' <span class="badge-red">⚠️ FUORI RANGE</span>'
    elif cat == "no_cap": cap_badge = ' <span class="badge-gray">❓ CAP IGNOTO</span>'
    crl_badge = ""
    if crl >= 2: crl_badge = f' <span class="badge-red">❌ {crl} bocciature</span>'
    elif crl == 1: crl_badge = f' <span class="badge-yellow">⚠️ 1 bocciatura</span>'
    st.markdown(f'<div class="biotech-card"><div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;"><div><span style="font-size:1.5em;font-weight:800;color:#e0e0ff;">{item["azienda"]}</span> <span style="color:#8888bb;">({item["ticker"]})</span>{cap_badge}{crl_badge}</div><span class="{bc}">Indice: {idx}/99</span></div></div>', unsafe_allow_html=True)

    m1,m2,m3,m4,m5 = st.columns(5)
    dc = "normal" if stock["variazione"]>=0 else "inverse"
    m1.metric("Prezzo", f"${stock['prezzo']}" if stock["prezzo"] else "N/D", f"{stock['variazione']:+.2f}%" if stock["prezzo"] else None, delta_color=dc)
    m2.metric("Valore", stock["market_cap_str"])
    m3.metric("Cassa", stock["cash_str"])
    if stock["cash_status"]=="burn": m4.metric("Benzina", f"{stock['cash_runway_mesi']}m")
    elif stock["cash_status"]=="positive": m4.metric("Benzina", "♻️ Produce")
    else: m4.metric("Benzina", "N/D")
    m5.metric("Contro %", f"{stock['short_interest']}%")

    if not stock["market_cap_ok"]:
        st.warning(f"⚠️ Market Cap non disponibile per {item['ticker']}. Il filtro 200M-2B NON e stato applicato.")

    d1,d2 = st.columns(2)
    with d1:
        st.markdown(f"**📅 Verdetto:** `{item['pdufa_date']}` — **{giorni} giorni**")
        st.markdown(f"**📝 Domanda:** {item['fase']}")
        st.markdown(f"**🚀 Review:** {item['tipo_review']}")
        if item.get("designazioni"):
            tags = " ".join(f'<span class="badge-blue">{d}</span>' for d in item["designazioni"])
            st.markdown(f"**Designazioni:** {tags}", unsafe_allow_html=True)
        if crl > 0:
            st.markdown(f"**❌ Bocciature (CRL):** {crl} (penalita: -{crl*12} punti)")
    with d2:
        if item.get("adcomm_voto") is not None:
            v = item["adcomm_voto"]
            em = "✅" if v>=90 else "⚠️" if v>=70 else "❌"
            st.markdown(f"**Giuria:** {em} **{v}%** ({item.get('adcomm_data','N/D')})")
            if v >= 90: st.markdown('<span class="badge-green">UNANIME</span>', unsafe_allow_html=True)
        else:
            st.markdown("**Giuria:** Nessun AdComm")
        if item.get("labeling_discussion"):
            st.markdown('**Foglietto:** <span class="badge-green">IN CORSO</span>', unsafe_allow_html=True)
        else:
            st.markdown("**Foglietto:** Non ancora")
        st.markdown(f"**Rischio:** {semaforo(item.get('rischio','medio'))}")

    if item.get("note"):
        st.info(f"📌 {item['note']}")

    if not stock["storico"].empty:
        with st.expander(f"Grafico 3 mesi — {item['ticker']}"):
            fs = go.Figure()
            fs.add_trace(go.Candlestick(x=stock["storico"].index, open=stock["storico"]["Open"], high=stock["storico"]["High"], low=stock["storico"]["Low"], close=stock["storico"]["Close"], name=item["ticker"]))
            try:
                pdt = datetime.strptime(item["pdufa_date"], "%Y-%m-%d")
                fs.add_vline(x=pdt.timestamp()*1000, line_dash="dash", line_color="#ff4081", annotation_text="VERDETTO", annotation_font_color="#ff4081")
            except: pass
            fs.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=30,b=10), font=dict(color="#ccccee"))
            st.plotly_chart(fs, use_container_width=True)

    if stock.get("errore"):
        st.warning(f"⚠️ Errore dati {item['ticker']}: {stock['errore']}")
    st.markdown("---")
    if idx >= 85 and giorni <= 5:
        st.balloons()


if not all_items:
    st.warning("Nessun catalizzatore corrisponde ai filtri.")
else:
    if in_range_list:
        st.markdown(f"### 🎯 Nel range {cap_min_in}M — {cap_max_in}M USD")
        for item, stock in in_range_list: render_card(item, stock, "in_range")
    if fuori_range_list and mostra_fuori:
        st.markdown("### ⚠️ Fuori range Market Cap")
        for item, stock in fuori_range_list: render_card(item, stock, "fuori_range")
    if no_cap_list and mostra_no_cap:
        st.markdown("### ❓ Market Cap non disponibile")
        st.markdown('<div class="cap-info">Il filtro 200M-2B <strong>NON</strong> e stato applicato a questi titoli. Verifica manualmente.</div>', unsafe_allow_html=True)
        for item, stock in no_cap_list: render_card(item, stock, "no_cap")


# TABELLA
if all_items:
    st.markdown("### Tabella Riepilogativa")
    rows = []
    for item, stock, cat in all_items:
        rows.append({
            "Ticker": item["ticker"], "Azienda": item["azienda"],
            "Farmaco": item["farmaco"], "PDUFA": item["pdufa_date"],
            "Giorni": giorni_al_verdetto(item["pdufa_date"]),
            "CRL": item.get("crl_precedenti",0),
            "AdComm": item.get("adcomm_voto") or "—",
            "Labeling": "✅" if item.get("labeling_discussion") else "❌",
            "Indice": calcola_indice(item),
            "Prezzo $": stock["prezzo"], "Var %": stock["variazione"],
            "Cap": stock["market_cap_str"],
            "Stato": "✅" if cat=="in_range" else "⚠️" if cat=="fuori_range" else "❓",
            "Rischio": semaforo(item.get("rischio","medio")),
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True,
        column_config={
            "Indice": st.column_config.ProgressColumn("Indice /99", min_value=0, max_value=99, format="%d"),
            "Var %": st.column_config.NumberColumn("Var %", format="%.2f%%"),
        })


# [FIX 1] TABELLA PESI — trasparenza totale
with st.expander("Come viene calcolato l'Indice di Fiducia (trasparenza pesi)"):
    st.markdown("""
| Fattore | Punti | Perche |
|---------|------:|--------|
| Base | 50 | Punto di partenza neutro |
| AdComm >=90% | +25 | ~95% approvati storicamente con voto unanime |
| AdComm 75-89% | +15 | Buon segnale |
| AdComm 60-74% | +5 | Misto |
| AdComm <60% | -10 | Negativo |
| Labeling discussion | +15 | FDA prepara etichetta |
| Priority Review | +5 | Malattia grave |
| Breakthrough Therapy | +5 | Meccanismo innovativo |
| Fast Track | +3 | Percorso facilitato |
| Orphan Drug | +2 | Malattia rara |
| Farmaco gia approvato (sNDA) | +5 | Meno rischio |
| **Per OGNI CRL precedente** | **-12** | **Ogni bocciatura riduce la fiducia** |

⚠️ Pesi editoriali, NON probabilita statistiche. Serve per confrontare, non per prevedere.
""")


# [FIX 3] Auto-refresh senza time.sleep — usa JavaScript per ricaricare la pagina
if auto_refresh:
    st.markdown(f"""<script>setTimeout(function(){{ window.location.reload(); }}, {refresh_sec * 1000});</script>""", unsafe_allow_html=True)
    st.caption(f"🔄 Prossimo aggiornamento tra {refresh_sec}s. I prezzi si aggiornano quando la cache scade (ogni 5 min).")


# FOOTER
st.markdown("---")
st.markdown(f'<div style="text-align:center;color:#6666aa;padding:20px;">🧬 <strong>Potential FDA Approval v4.0</strong><br>Catalizzatori: {DATA_ULTIMO_AGGIORNAMENTO} ({giorni_obs}g fa)<br>Prezzi: cache yfinance 5 min — ora: {datetime.now().strftime("%H:%M:%S")}<br><br>⚠️ <em>App educativa. yfinance e una libreria non ufficiale: i prezzi possono essere ritardati. Verifica su fonti ufficiali. Non e consulenza finanziaria.</em></div>', unsafe_allow_html=True)
