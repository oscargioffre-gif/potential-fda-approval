import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(page_title="Potential FDA Approval", page_icon="🧬", layout="wide")

DATA_AGG = "2026-03-15"

st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #020617, #0f172a, #020617)}
[data-testid="stMetric"] {background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 14px}
[data-testid="stSidebar"] {background: #0f172a}
.card {background: linear-gradient(135deg, #0f172a, #1e293b); border: 1px solid #334155; border-radius: 16px; padding: 20px; margin: 10px 0}
.card-urgent {background: linear-gradient(135deg, #1e1b2e, #2d1a1a); border: 1px solid #ef444466}
.pill-red {background: #dc2626; color: white; padding: 4px 14px; border-radius: 20px; font-weight: 800; font-size: 13px; display: inline-block}
.pill-orange {background: #f59e0b; color: black; padding: 4px 14px; border-radius: 20px; font-weight: 800; font-size: 13px; display: inline-block}
.pill-blue {background: #3b82f6; color: white; padding: 4px 14px; border-radius: 20px; font-weight: 800; font-size: 13px; display: inline-block}
.tag {background: #334155; color: #e2e8f0; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; display: inline-block; margin: 2px 4px 2px 0}
.tag-green {background: #166534}
.tag-red {background: #991b1b}
.tag-blue {background: #1d4ed8}
.pro {background: #0f2918; border-radius: 10px; padding: 12px; font-size: 12px; color: #a7f3d0}
.contra {background: #1c0f0f; border-radius: 10px; padding: 12px; font-size: 12px; color: #fecaca}
.news-item {background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 8px 12px; margin: 4px 0; font-size: 12px}
.title {font-size: 2.2em; font-weight: 900; background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center}
.subtitle {font-size: 1em; color: #64748b; text-align: center}
.labeling-alert {background: linear-gradient(90deg, #166534, #15803d); border-radius: 8px; padding: 8px 12px; font-size: 12px; color: #bbf7d0; font-weight: 600; margin: 8px 0}
.disclaimer-box {background: rgba(255,255,255,0.03); border: 1px dashed #334155; border-radius: 8px; padding: 10px; font-size: 11px; color: #64748b; margin: 8px 0}
</style>
""", unsafe_allow_html=True)

# Data
data = [
    {
        "ticker": "ALDX", "azienda": "Aldeyra Therapeutics",
        "farmaco": "Reproxalap (collirio)", "cosa": "Malattia dell'occhio secco",
        "pdufa": "2026-03-16", "review": "Standard", "crl": 2,
        "tags": ["Fast Track"], "labeling": True, "rischio": "medio-alto",
        "indice": 44,
        "chiave": "La FDA sta gia scrivendo il foglietto illustrativo (segnale positivo). Ma e la 3a richiesta dopo 2 bocciature.",
        "pro": [
            "FDA ha condiviso bozza etichetta (dic. 2025)",
            "Nessun problema di sicurezza o produzione",
            "AbbVie pronta a pagare $100M se approvato",
            "Phase 3 chamber trial: endpoint raggiunto (P=0.002)",
        ],
        "contro": [
            "2 bocciature precedenti (CRL nov.2023, apr.2025)",
            "Field trial ha MANCATO l'endpoint primario",
            "FDA ha cambiato idea sul field trial: prima escluso, poi richiesto",
        ],
        "news": [
            ("Fierce Biotech", "16 dic. 2025", "Il CEO ha spiegato che la FDA ha cambiato idea sul field trial: prima aveva detto di non includerlo, poi lo ha richiesto."),
            ("Ophthalmology Times", "12 mar. 2026", "Le 2 precedenti bocciature citavano problemi di efficacia, non di sicurezza. Nessun nuovo problema nel meeting di dicembre."),
            ("Seeking Alpha", "30 dic. 2025", "Valutazione ($259M) bassa rispetto al mercato DED, ma rischio 3o rifiuto resta concreto."),
        ],
    },
    {
        "ticker": "RYTM", "azienda": "Rhythm Pharmaceuticals",
        "farmaco": "Setmelanotide (Imcivree)", "cosa": "Obesita ipotalamica acquisita (espansione)",
        "pdufa": "2026-03-20", "review": "Priority Review", "crl": 0,
        "tags": ["Orphan Drug", "Farmaco gia approvato"], "labeling": False, "rischio": "basso",
        "indice": 62,
        "chiave": "Imcivree e GIA venduto. Questa e un'espansione a nuovi pazienti. Dati clinici tra i piu solidi del mese.",
        "pro": [
            "Farmaco GIA APPROVATO e in commercio ($57M ricavi Q4 2025)",
            "Phase 3 TRANSCEND: -18.8% BMI vs placebo (p<0.0001, N=142)",
            "Priority Review (corsia preferenziale)",
            "Zero bocciature precedenti",
            "Dati giapponesi confermano risultati (mar. 2026)",
        ],
        "contro": [
            "PDUFA esteso da dic.2025 a mar.2026 (analisi extra richieste)",
            "Obesita ipotalamica: mercato piu piccolo",
        ],
        "news": [
            ("Globe Newswire", "1 mar. 2026", "Nuovi dati: 12 pazienti giapponesi confermano riduzione BMI -16.4% e miglioramento fame."),
            ("Rhythm IR", "26 feb. 2026", "Ricavi 2025 a $197M (+42% YoY). Azienda in crescita solida."),
            ("FDA", "7 nov. 2025", "PDUFA esteso dopo richiesta analisi di sensibilita. Nessun problema di sicurezza."),
        ],
    },
    {
        "ticker": "RCKT", "azienda": "Rocket Pharmaceuticals",
        "farmaco": "Kresladi (terapia genica)", "cosa": "LAD-I (malattia rara, fatale nei bambini)",
        "pdufa": "2026-03-28", "review": "Standard", "crl": 1,
        "tags": ["Orphan Drug", "Breakthrough Therapy"], "labeling": False, "rischio": "medio",
        "indice": 52,
        "chiave": "Terapia genica per malattia che uccide i bambini. 100% sopravvivenza nel trial. Ri-sottomissione dopo 1 rifiuto.",
        "pro": [
            "100% sopravvivenza a 1+ anno nel trial Phase 1/2",
            "Tutti endpoint primari e secondari raggiunti",
            "Breakthrough Therapy + Orphan Drug",
            "Malattia senza alternative (unmet need altissimo)",
        ],
        "contro": [
            "1 bocciatura precedente (CRL)",
            "Terapia genica: produzione complessa",
            "Mercato ultra-piccolo (malattia ultra-rara)",
        ],
        "news": [
            ("CGTLive", "14 ott. 2025", "FDA ha accettato ri-sottomissione BLA. Trial: riduzione infezioni + miglioramento lesioni cutanee."),
            ("Rocket IR", "14 ott. 2025", "LAD-I e fatale nell'infanzia senza trapianto. Kresladi potrebbe essere l'unica alternativa."),
            ("BioMed Nexus", "gen. 2026", "Il primo CRL non era legato a efficacia/sicurezza. Ri-sottomissione ha affrontato le carenze."),
        ],
    },
]


def giorni(pdufa):
    try:
        return (datetime.strptime(pdufa, "%Y-%m-%d") - datetime.now()).days
    except:
        return -999

def fmt(v):
    if v >= 1e9: return f"${v/1e9:.2f}B"
    elif v >= 1e6: return f"${v/1e6:.1f}M"
    elif v > 0: return f"${v:,.0f}"
    return "N/D"

@st.cache_data(ttl=300)
def get_price(ticker):
    try:
        s = yf.Ticker(ticker)
        i = s.info
        p = i.get("currentPrice") or i.get("regularMarketPrice", 0)
        pc = i.get("previousClose", p)
        mc = i.get("marketCap", 0)
        ch = ((p - pc) / pc * 100) if pc else 0
        return {"prezzo": round(p, 2), "var": round(ch, 2), "cap": mc, "cap_str": fmt(mc), "ok": True}
    except:
        return {"prezzo": 0, "var": 0, "cap": 0, "cap_str": "N/D", "ok": False}


# Header
st.markdown('<p class="title">Potential FDA Approval</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Small & Mid Cap Biotech — Solo range 200M-2B USD</p>', unsafe_allow_html=True)
st.markdown(f'<p style="text-align:center;font-size:11px;color:#475569">Aggiornato: {DATA_AGG} | Fonti: comunicati aziendali, SEC filings, Fierce Biotech, CGTLive</p>', unsafe_allow_html=True)
st.markdown("---")

# Stale data check
try:
    obs = (datetime.now() - datetime.strptime(DATA_AGG, "%Y-%m-%d")).days
except:
    obs = 999
if obs > 14:
    st.error(f"I dati dei catalizzatori hanno {obs} giorni. Aggiorna la lista!")
elif obs > 7:
    st.warning(f"Dati di {obs} giorni fa. Le date PDUFA possono cambiare.")

# Summary
c1, c2, c3 = st.columns(3)
c1.metric("Catalizzatori", len(data))
c2.metric("Con Labeling", sum(1 for d in data if d["labeling"]))
urg = sum(1 for d in data if 0 <= giorni(d["pdufa"]) <= 7)
c3.metric("Entro 7 giorni", urg)

# AdComm notice
st.markdown(
    '<div style="background:#1c1917;border:1px solid #78350f;border-radius:10px;'
    'padding:10px 14px;margin:12px 0;font-size:12px;color:#fbbf24;line-height:1.5">'
    'La FDA non convoca la Giuria Esperti (AdComm) da luglio 2025. '
    'Nessuno di questi catalizzatori ha un voto. '
    'Prossimo: 30 aprile 2026 (AstraZeneca).</div>',
    unsafe_allow_html=True,
)

# Index disclaimer
st.markdown(
    '<div class="disclaimer-box">'
    '<strong>Indice di Fiducia</strong> — punteggio 0-99 per CONFRONTARE i catalizzatori. '
    '<strong>Non e una probabilita.</strong> '
    'Pesi: AdComm unanime +25 | Labeling +15 | Priority Review +5 | '
    'Breakthrough +5 | Fast Track +3 | Orphan +2 | Farmaco esistente +5 | '
    '<span style="color:#f87171">Ogni bocciatura (CRL) -12</span></div>',
    unsafe_allow_html=True,
)

st.markdown("---")

# Sort by PDUFA
sorted_data = sorted(data, key=lambda d: giorni(d["pdufa"]))

# Cards
for item in sorted_data:
    g = giorni(item["pdufa"])
    if g < 0:
        continue

    stock = get_price(item["ticker"])
    idx = item["indice"]
    urgent = g <= 3

    # Pill
    if g <= 1:
        pill = f'<span class="pill-red">{"OGGI" if g <= 0 else "DOMANI"}</span>'
    elif g <= 7:
        pill = f'<span class="pill-orange">{g} GIORNI</span>'
    else:
        pill = f'<span class="pill-blue">{g} GIORNI</span>'

    # Card class
    card_cls = "card-urgent" if urgent else "card"

    # Tags HTML
    tags_html = ""
    for t in item["tags"]:
        cls = "tag-blue" if "Priority" in t or "Breakthrough" in t else "tag-green" if "Fast" in t or "Orphan" in t or "approvato" in t.lower() else "tag"
        tags_html += f'<span class="tag {cls}">{t}</span> '
    if item["crl"] > 0:
        tags_html += f'<span class="tag tag-red">{"" if item["crl"]==1 else ""} {item["crl"]} bocciatur{"a" if item["crl"]==1 else "e"}</span> '
    if item["labeling"]:
        tags_html += '<span class="tag tag-green">Etichetta in corso</span>'

    # Risk emoji
    re = {"basso": "🟢", "medio": "🟡", "medio-alto": "🔴", "alto": "🔴"}
    tags_html += f' <span class="tag">Rischio {re.get(item["rischio"], "")} {item["rischio"]}</span>'

    # Index bar color
    ic = "#22c55e" if idx >= 75 else "#f59e0b" if idx >= 55 else "#3b82f6" if idx >= 35 else "#ef4444"
    pct = idx / 99 * 100

    st.markdown(f"""
    <div class="{card_cls}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:10px">
            <div>
                <span style="font-size:20px;font-weight:800;color:#f8fafc">{item["ticker"]}</span>
                <span style="font-size:13px;color:#94a3b8;margin-left:8px">{item["azienda"]}</span>
                <div style="font-size:13px;color:#cbd5e1;margin-top:2px">{item["farmaco"]} — {item["cosa"]}</div>
            </div>
            {pill}
        </div>
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:10px 14px;font-size:13px;color:#e2e8f0;line-height:1.5;margin-bottom:10px">
            {item["chiave"]}
        </div>
        <div style="margin-bottom:10px">{tags_html}</div>
        <div style="display:flex;justify-content:space-between;font-size:11px;color:#94a3b8;margin-bottom:3px">
            <span>Indice di Fiducia</span>
            <span style="color:{ic};font-weight:700">{idx}/99</span>
        </div>
        <div style="background:#1e293b;border-radius:6px;height:8px;overflow:hidden;margin-bottom:4px">
            <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,{ic}88,{ic});border-radius:6px"></div>
        </div>
        <div style="font-size:10px;color:#475569">Non e una probabilita. Serve per confrontare.</div>
    </div>
    """, unsafe_allow_html=True)

    # Labeling alert
    if item["labeling"]:
        st.markdown(
            '<div class="labeling-alert">'
            'LABELING IN CORSO — La FDA sta scrivendo il foglietto. '
            'Stanno pensando a COME venderlo, non SE.</div>',
            unsafe_allow_html=True,
        )

    # Price metrics
    if stock["ok"]:
        p1, p2, p3 = st.columns(3)
        dc = "normal" if stock["var"] >= 0 else "inverse"
        p1.metric("Prezzo", f"${stock['prezzo']}", f"{stock['var']:+.2f}%", delta_color=dc)
        p2.metric("Market Cap", stock["cap_str"])
        p3.metric("PDUFA", item["pdufa"])
    else:
        st.warning(f"Prezzi non disponibili per {item['ticker']}. Yahoo Finance non risponde.")

    # Expandable details
    with st.expander(f"Segnali + Notizie — {item['ticker']}"):
        col_pro, col_con = st.columns(2)
        with col_pro:
            st.markdown("**✅ SEGNALI POSITIVI**")
            for p in item["pro"]:
                st.markdown(f"<span style='font-size:12px;color:#a7f3d0'>• {p}</span>", unsafe_allow_html=True)
        with col_con:
            st.markdown("**⚠️ RISCHI**")
            for c in item["contro"]:
                st.markdown(f"<span style='font-size:12px;color:#fecaca'>• {c}</span>", unsafe_allow_html=True)

        st.markdown("**📰 DALLE FONTI UFFICIALI**")
        for src, date, txt in item["news"]:
            st.markdown(
                f'<div class="news-item">'
                f'<span style="color:#60a5fa;font-weight:700">{src}</span>'
                f'<span style="color:#475569;margin-left:6px">{date}</span>'
                f'<div style="color:#cbd5e1;margin-top:2px">{txt}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")


# Glossary
with st.expander("Dizionario 'da bar' — capire tutto in 30 secondi"):
    terms = [
        ("PDUFA", "Giorno del Verdetto", "Quando la FDA dice SI o NO"),
        ("Labeling", "Scrivono il foglietto!", "Se la FDA discute l'etichetta, pensano a COME venderlo"),
        ("CRL", "Bocciato con appunti", "La FDA dice NO ma spiega cosa correggere"),
        ("Priority Review", "Corsia preferenziale", "Esame in 6 mesi anziche 10"),
        ("Orphan Drug", "Malattia rara", "7 anni di esclusiva + vantaggi fiscali"),
        ("Breakthrough", "Rivoluzionario", "Molto meglio di tutto cio che esiste"),
    ]
    for term, bar, desc in terms:
        st.markdown(
            f'<div style="background:#0f172a;border-left:3px solid #6366f1;'
            f'border-radius:0 8px 8px 0;padding:8px 12px;margin:4px 0;font-size:12px">'
            f'<span style="color:#a5b4fc;font-weight:700">{bar}</span>'
            f' <span style="color:#475569">({term})</span>'
            f' — <span style="color:#94a3b8">{desc}</span></div>',
            unsafe_allow_html=True,
        )


# Footer
st.markdown("---")
st.markdown(
    f'<div style="text-align:center;color:#475569;font-size:11px;padding:10px 0;line-height:1.6">'
    f'Potential FDA Approval v5.0<br>'
    f'Fonti: comunicati aziendali, SEC filings, Fierce Biotech, CGTLive, Ophthalmology Times<br>'
    f'App educativa — non e consulenza finanziaria. Verifica su fda.gov.</div>',
    unsafe_allow_html=True,
)
