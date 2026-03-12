"""
╔══════════════════════════════════════════════════════════════╗
║          🧬 POTENTIAL FDA APPROVAL v2.0 🧬                   ║
║         App gratuita per cacciatori di catalizzatori         ║
║                                                              ║
║  Come usarla:                                                ║
║  1. pip install streamlit yfinance plotly pandas             ║
║  2. streamlit run potential_fda_approval.py                  ║
║                                                              ║
║  Oppure: carica su GitHub + Streamlit Cloud (gratis)         ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURAZIONE PAGINA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="🧬 Potential FDA Approval",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS PERSONALIZZATO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 50%, #0d0d2b 100%);
    }

    .biotech-card {
        background: linear-gradient(145deg, #1e1e3f, #2a2a5c);
        border: 1px solid #3a3a7c;
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .biotech-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(100, 100, 255, 0.15);
    }

    .badge-green {
        background: linear-gradient(135deg, #00c853, #00e676);
        color: #000;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8em;
        display: inline-block;
    }
    .badge-yellow {
        background: linear-gradient(135deg, #ffc107, #ffea00);
        color: #000;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8em;
        display: inline-block;
    }
    .badge-red {
        background: linear-gradient(135deg, #ff1744, #ff5252);
        color: #fff;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8em;
        display: inline-block;
    }
    .badge-blue {
        background: linear-gradient(135deg, #2979ff, #448aff);
        color: #fff;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8em;
        display: inline-block;
    }

    .neon-title {
        font-size: 2.8em;
        font-weight: 800;
        background: linear-gradient(90deg, #00e5ff, #7c4dff, #ff4081);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0;
    }
    .neon-subtitle {
        font-size: 1.1em;
        color: #8888cc;
        text-align: center;
        margin-top: 4px;
    }

    .glossario-box {
        background: rgba(30, 30, 80, 0.6);
        border-left: 4px solid #7c4dff;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 8px 0;
        font-size: 0.92em;
    }
    .glossario-box strong {
        color: #b388ff;
    }

    [data-testid="stMetric"] {
        background: rgba(30, 30, 80, 0.5);
        border: 1px solid #3a3a7c;
        border-radius: 12px;
        padding: 16px;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #12122e, #1a1a40);
    }
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOSSARIO "DA BAR" — Terminologia per principianti
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GLOSSARIO = {
    "PDUFA Date": {
        "da_bar": "📅 Giorno del Verdetto",
        "spiegazione": "È il giorno in cui la FDA (l'ente americano dei farmaci) "
                       "dice SÌ o NO a un nuovo farmaco. Come aspettare il voto "
                       "della giuria in tribunale."
    },
    "AdComm": {
        "da_bar": "👨‍⚖️ La Giuria degli Esperti",
        "spiegazione": "Un comitato di medici e scienziati che vota se il farmaco "
                       "funziona davvero. Se votano >90% sì, è quasi fatta."
    },
    "Market Cap": {
        "da_bar": "💰 Quanto vale l'azienda",
        "spiegazione": "Il prezzo di un'azione moltiplicato per tutte le azioni "
                       "che esistono. Come dire: 'Questa pizzeria vale 500mila euro'."
    },
    "Cash Runway": {
        "da_bar": "⛽ Benzina nel serbatoio",
        "spiegazione": "Quanti mesi l'azienda può sopravvivere coi soldi che ha "
                       "in banca, senza guadagnare nulla. Più mesi = più tranquilli."
    },
    "Short Interest": {
        "da_bar": "🐻 Quanti scommettono CONTRO",
        "spiegazione": "Percentuale di gente che scommette che il titolo scenderà. "
                       "Se sono tanti e il farmaco viene approvato, il titolo ESPLODE "
                       "verso l'alto (short squeeze)."
    },
    "Phase 3": {
        "da_bar": "🏁 L'ultimo esame",
        "spiegazione": "Il farmaco ha superato i test su pochi pazienti (Phase 1-2) "
                       "e ora viene testato su migliaia di persone. Se passa, si va alla FDA."
    },
    "Labeling Discussion": {
        "da_bar": "🏷️ Scelta dell'etichetta",
        "spiegazione": "Quando la FDA discute COME scrivere il foglietto illustrativo. "
                       "È un segnale POSITIVO: vuol dire che stanno già pensando a "
                       "come venderlo, non SE venderlo."
    },
    "NDA/BLA": {
        "da_bar": "📝 La domanda ufficiale",
        "spiegazione": "È la richiesta formale che l'azienda invia alla FDA per "
                       "far approvare il farmaco. NDA = farmaco chimico, BLA = farmaco biologico."
    },
    "Priority Review": {
        "da_bar": "🚀 Corsia preferenziale",
        "spiegazione": "La FDA lo esamina più velocemente (6 mesi anziché 10) "
                       "perché il farmaco cura qualcosa di grave o senza alternative."
    },
    "Breakthrough Therapy": {
        "da_bar": "⚡ Farmaco rivoluzionario",
        "spiegazione": "La FDA riconosce che il farmaco è molto meglio di tutto "
                       "ciò che esiste. Riceve aiuto extra per arrivare al mercato prima."
    },
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE CATALIZZATORI BIOTECH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚠️ ISTRUZIONI PER AGGIORNARE:
# Chiedi all'IA il Super-Prompt e sostituisci questa lista
# con i dati aggiornati del mese corrente.
#
# Ogni dizionario nella lista rappresenta un catalizzatore biotech.
# I dati sotto sono ESEMPI ILLUSTRATIVI per mostrare la struttura
# dell'app. Prima di qualsiasi decisione, verifica sempre le date
# e i voti sui siti ufficiali della FDA (fda.gov).
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

data = [
    {
        "ticker": "ALDX",
        "azienda": "Aldeyra Therapeutics",
        "farmaco": "Reproxalap",
        "indicazione": "Malattia dell'occhio secco (Dry Eye Disease)",
        "pdufa_date": "2026-03-16",
        "adcomm_voto": None,
        "adcomm_data": None,
        "tipo_review": "Standard Review",
        "designazioni": ["Fast Track"],
        "labeling_discussion": True,
        "fase": "NDA",
        "note": "3ª richiesta NDA. La FDA ha condiviso bozza etichetta a dic. 2025 (segnale positivo). "
               "Il field trial NON ha raggiunto l'endpoint primario ma la FDA lo considera 'supportivo'. "
               "AbbVie ha opzione di licenza da $100M in caso di approvazione.",
        "rischio": "medio",
    },
    {
        "ticker": "RYTM",
        "azienda": "Rhythm Pharmaceuticals",
        "farmaco": "Setmelanotide (Imcivree)",
        "indicazione": "Obesità ipotalamica acquisita",
        "pdufa_date": "2026-03-20",
        "adcomm_voto": None,
        "adcomm_data": None,
        "tipo_review": "Priority Review",
        "designazioni": ["Orphan Drug"],
        "labeling_discussion": False,
        "fase": "sNDA",
        "note": "Espansione di indicazione — Imcivree è già approvato per BBS e POMC. "
               "Trial Phase 3 TRANSCEND: riduzione BMI -18.8% vs placebo (p<0.0001). "
               "Azienda già commerciale con ricavi $57M Q4 2025. Dati molto solidi.",
        "rischio": "basso",
    },
    {
        "ticker": "RCKT",
        "azienda": "Rocket Pharmaceuticals",
        "farmaco": "Kresladi (marnetegragene autotemcel)",
        "indicazione": "Deficit di adesione leucocitaria grave (LAD-I) — terapia genica",
        "pdufa_date": "2026-03-28",
        "adcomm_voto": None,
        "adcomm_data": None,
        "tipo_review": "Standard Review",
        "designazioni": ["Orphan Drug", "Breakthrough Therapy"],
        "labeling_discussion": False,
        "fase": "BLA",
        "note": "Ri-sottomissione BLA dopo primo rifiuto. Trial Phase 1/2: 100% sopravvivenza "
               "a 1+ anno, tutti gli endpoint primari e secondari raggiunti. "
               "Malattia ultra-rara, quasi sempre fatale nell'infanzia senza trapianto.",
        "rischio": "medio",
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNZIONI CORE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_data(ttl=300)
def get_stock_data(ticker: str) -> dict:
    """Scarica dati finanziari da Yahoo Finance via yfinance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="3mo")

        market_cap = info.get("marketCap", 0)
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        prev_close = info.get("previousClose", price)
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0

        total_cash = info.get("totalCash", 0)
        operating_cf = info.get("operatingCashflow", 0)
        if operating_cf and operating_cf < 0:
            cash_runway_months = round(total_cash / abs(operating_cf) * 12, 1)
        else:
            cash_runway_months = None

        short_pct = info.get("shortPercentOfFloat", 0)
        if short_pct and short_pct < 1:
            short_pct = short_pct * 100

        return {
            "prezzo": round(price, 2),
            "variazione": round(change_pct, 2),
            "market_cap": market_cap,
            "market_cap_str": format_market_cap(market_cap),
            "cash": total_cash,
            "cash_str": format_market_cap(total_cash),
            "cash_runway_mesi": cash_runway_months,
            "short_interest": round(short_pct, 1) if short_pct else 0,
            "storico": hist,
            "nome": info.get("shortName", ticker),
            "volume": info.get("averageVolume", 0),
            "errore": None,
        }
    except Exception as e:
        return {
            "prezzo": 0,
            "variazione": 0,
            "market_cap": 0,
            "market_cap_str": "N/D",
            "cash": 0,
            "cash_str": "N/D",
            "cash_runway_mesi": None,
            "short_interest": 0,
            "storico": pd.DataFrame(),
            "nome": ticker,
            "volume": 0,
            "errore": str(e),
        }


def format_market_cap(value: float) -> str:
    """Formatta numeri grandi in modo leggibile."""
    if value >= 1e9:
        return f"${value / 1e9:.2f}B"
    elif value >= 1e6:
        return f"${value / 1e6:.1f}M"
    elif value > 0:
        return f"${value:,.0f}"
    return "N/D"


def giorni_al_pdufa(pdufa_str: str) -> int:
    """Calcola giorni mancanti al PDUFA."""
    try:
        pdufa = datetime.strptime(pdufa_str, "%Y-%m-%d")
        return (pdufa - datetime.now()).days
    except (ValueError, TypeError):
        return -999


def semaforo_rischio(item: dict) -> str:
    """Genera il semaforo di rischio con emoji."""
    r = item.get("rischio", "medio").lower()
    if r == "basso":
        return "🟢 BASSO"
    elif r == "medio":
        return "🟡 MEDIO"
    elif r in ("medio-alto", "alto"):
        return "🔴 ALTO"
    return "⚪ N/D"


def punteggio_approvazione(item: dict) -> int:
    """Calcola un punteggio di probabilità di approvazione (0-100)."""
    score = 50

    voto = item.get("adcomm_voto")
    if voto:
        if voto >= 90:
            score += 25
        elif voto >= 75:
            score += 15
        elif voto >= 60:
            score += 5
        else:
            score -= 10

    if item.get("labeling_discussion"):
        score += 15

    if item.get("tipo_review") == "Priority Review":
        score += 5

    desig = item.get("designazioni", [])
    if "Breakthrough Therapy" in desig:
        score += 5
    if "Fast Track" in desig:
        score += 3
    if "Orphan Drug" in desig:
        score += 2

    return min(score, 99)


def colore_punteggio(score: int) -> str:
    """Restituisce classe CSS per il punteggio."""
    if score >= 80:
        return "badge-green"
    elif score >= 60:
        return "badge-yellow"
    elif score >= 40:
        return "badge-blue"
    return "badge-red"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown('<p class="neon-title">🧬 Potential FDA Approval</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="neon-subtitle">Caccia ai catalizzatori FDA — '
    'Small &amp; Mid Cap Biotech</p>',
    unsafe_allow_html=True,
)
st.markdown("---")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown("## ⚙️ Filtri")

    filtro_rischio = st.multiselect(
        "🚦 Livello di rischio",
        options=["basso", "medio", "medio-alto", "alto"],
        default=["basso", "medio", "medio-alto", "alto"],
    )

    max_giorni = st.slider(
        "📅 PDUFA entro (giorni)", min_value=7, max_value=90, value=30, step=7
    )

    min_adcomm = st.slider(
        "👨‍⚖️ Voto AdComm minimo (%)", min_value=0, max_value=100, value=0, step=5
    )

    solo_labeling = st.checkbox("🏷️ Solo con Labeling Discussion")

    st.markdown("---")
    st.markdown("## 🔄 Auto-Aggiornamento")
    auto_refresh = st.checkbox("Aggiorna prezzi automaticamente")
    refresh_interval = st.selectbox(
        "Ogni quanti secondi?", options=[30, 60, 120, 300], index=1
    )

    st.markdown("---")
    st.markdown("## 📖 Glossario")
    with st.expander("📚 Clicca per il dizionario 'da bar'", expanded=False):
        for termine, info in GLOSSARIO.items():
            st.markdown(
                f'<div class="glossario-box">'
                f"<strong>{info['da_bar']}</strong> ({termine})<br>"
                f"{info['spiegazione']}"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown(
        "⚠️ **Disclaimer**: Questa app è solo a scopo educativo e informativo. "
        "Non costituisce consulenza finanziaria. Fai sempre le tue ricerche "
        "prima di investire."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILTRAGGIO DATI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

filtered = []
for item in data:
    giorni = giorni_al_pdufa(item["pdufa_date"])

    if giorni < 0 or giorni > max_giorni:
        continue
    if item.get("rischio", "medio").lower() not in filtro_rischio:
        continue

    voto = item.get("adcomm_voto")
    if voto is not None and voto < min_adcomm:
        continue
    if solo_labeling and not item.get("labeling_discussion"):
        continue

    filtered.append(item)

filtered.sort(key=lambda x: giorni_al_pdufa(x["pdufa_date"]))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DASHBOARD RIEPILOGO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("🧬 Catalizzatori Totali", len(data))
col_b.metric("🎯 Dopo i Filtri", len(filtered))
col_c.metric(
    "🏷️ Con Labeling",
    sum(1 for d in filtered if d.get("labeling_discussion")),
)
alta_prob = sum(1 for d in filtered if punteggio_approvazione(d) >= 80)
col_d.metric("🟢 Alta Probabilità", alta_prob)

st.markdown("---")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TIMELINE PDUFA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if filtered:
    st.markdown("### 📅 Timeline — Prossimi 'Giorni del Verdetto'")

    timeline_data = []
    for item in filtered:
        giorni = giorni_al_pdufa(item["pdufa_date"])
        score = punteggio_approvazione(item)
        timeline_data.append({
            "Azienda": item["azienda"],
            "Farmaco": item["farmaco"],
            "PDUFA": item["pdufa_date"],
            "Giorni": giorni,
            "Punteggio": score,
        })

    df_timeline = pd.DataFrame(timeline_data)

    fig_timeline = go.Figure()

    for _, row in df_timeline.iterrows():
        color = (
            "#00e676" if row["Punteggio"] >= 80
            else "#ffc107" if row["Punteggio"] >= 60
            else "#2979ff" if row["Punteggio"] >= 40
            else "#ff5252"
        )
        fig_timeline.add_trace(go.Bar(
            x=[row["Giorni"]],
            y=[f"{row['Azienda']}<br>({row['Farmaco']})"],
            orientation="h",
            marker_color=color,
            text=f"{row['Giorni']}g — Score {row['Punteggio']}%",
            textposition="outside",
            hovertemplate=(
                f"<b>{row['Azienda']}</b><br>"
                f"Farmaco: {row['Farmaco']}<br>"
                f"PDUFA: {row['PDUFA']}<br>"
                f"Giorni: {row['Giorni']}<br>"
                f"Punteggio: {row['Punteggio']}%<br>"
                "<extra></extra>"
            ),
            showlegend=False,
        ))

    fig_timeline.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Giorni al Verdetto →",
        height=max(200, len(filtered) * 80),
        margin=dict(l=20, r=120, t=20, b=40),
        font=dict(color="#ccccee"),
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

    st.markdown("---")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCHEDE DETTAGLIO PER OGNI CATALIZZATORE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if not filtered:
    st.warning(
        "Nessun catalizzatore corrisponde ai filtri selezionati. "
        "Prova ad allargare i parametri nella sidebar."
    )
else:
    for item in filtered:
        giorni = giorni_al_pdufa(item["pdufa_date"])
        score = punteggio_approvazione(item)
        badge_class = colore_punteggio(score)

        stock = get_stock_data(item["ticker"])

        st.markdown(
            f'<div class="biotech-card">'
            f'<div style="display:flex; justify-content:space-between; align-items:center;">'
            f'<div>'
            f'<span style="font-size:1.6em; font-weight:800; color:#e0e0ff;">'
            f'{item["azienda"]}</span>'
            f'<span style="color:#8888bb; margin-left:12px;">({item["ticker"]})</span>'
            f'</div>'
            f'<div>'
            f'<span class="{badge_class}">Score: {score}%</span>'
            f'</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4, m5 = st.columns(5)

        delta_color = "normal" if stock["variazione"] >= 0 else "inverse"
        m1.metric(
            "💵 Prezzo",
            f"${stock['prezzo']}" if stock["prezzo"] else "N/D",
            f"{stock['variazione']:+.2f}%" if stock["prezzo"] else None,
            delta_color=delta_color,
        )
        m2.metric("💰 Valore Azienda", stock["market_cap_str"])
        m3.metric("⛽ Benzina (Cash)", stock["cash_str"])
        m4.metric(
            "⏱️ Mesi di Benzina",
            f"{stock['cash_runway_mesi']} mesi"
            if stock["cash_runway_mesi"]
            else "N/D",
        )
        m5.metric("🐻 Scommesse Contro", f"{stock['short_interest']}%")

        det1, det2 = st.columns(2)

        with det1:
            st.markdown(f"**📅 Giorno del Verdetto (PDUFA):** "
                        f"`{item['pdufa_date']}` — **{giorni} giorni**")
            st.markdown(f"**📝 Tipo domanda:** {item['fase']}")
            st.markdown(f"**🚀 Tipo Review:** {item['tipo_review']}")

            if item.get("designazioni"):
                tags = " ".join(
                    f'<span class="badge-blue">{d}</span>'
                    for d in item["designazioni"]
                )
                st.markdown(f"**⚡ Designazioni speciali:** {tags}", unsafe_allow_html=True)

        with det2:
            if item.get("adcomm_voto") is not None:
                voto = item["adcomm_voto"]
                voto_emoji = "✅" if voto >= 90 else "⚠️" if voto >= 70 else "❌"
                st.markdown(
                    f"**👨‍⚖️ Giuria Esperti (AdComm):** {voto_emoji} "
                    f"**{voto}%** favorevoli (data: {item.get('adcomm_data', 'N/D')})"
                )
                if voto >= 90:
                    st.markdown(
                        '<span class="badge-green">UNANIME — Segnale molto forte</span>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown("**👨‍⚖️ Giuria Esperti (AdComm):** Nessun AdComm convocato")

            if item.get("labeling_discussion"):
                st.markdown(
                    '**🏷️ Scelta Etichetta:** '
                    '<span class="badge-green">IN CORSO — Segnale POSITIVO</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("**🏷️ Scelta Etichetta:** Non ancora in discussione")

            st.markdown(f"**🚦 Semaforo Rischio:** {semaforo_rischio(item)}")

        if item.get("note"):
            st.info(f"📌 **Note:** {item['note']}")

        if not stock["storico"].empty:
            with st.expander(f"📈 Grafico 3 mesi — {item['ticker']}", expanded=False):
                fig_stock = go.Figure()
                fig_stock.add_trace(go.Candlestick(
                    x=stock["storico"].index,
                    open=stock["storico"]["Open"],
                    high=stock["storico"]["High"],
                    low=stock["storico"]["Low"],
                    close=stock["storico"]["Close"],
                    name=item["ticker"],
                ))

                pdufa_dt = datetime.strptime(item["pdufa_date"], "%Y-%m-%d")
                fig_stock.add_vline(
                    x=pdufa_dt.timestamp() * 1000,
                    line_dash="dash",
                    line_color="#ff4081",
                    annotation_text="📅 PDUFA",
                    annotation_font_color="#ff4081",
                )

                fig_stock.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=350,
                    xaxis_rangeslider_visible=False,
                    margin=dict(l=10, r=10, t=30, b=10),
                    font=dict(color="#ccccee"),
                )
                st.plotly_chart(fig_stock, use_container_width=True)

        if stock.get("errore"):
            st.warning(
                f"⚠️ Impossibile caricare i dati di mercato per {item['ticker']}: "
                f"{stock['errore']}. Verifica che il ticker sia corretto."
            )

        st.markdown("---")

        if score >= 90 and giorni <= 7:
            st.balloons()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABELLA RIEPILOGATIVA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if filtered:
    st.markdown("### 📊 Tabella Riepilogativa")

    table_data = []
    for item in filtered:
        stock = get_stock_data(item["ticker"])
        table_data.append({
            "Ticker": item["ticker"],
            "Azienda": item["azienda"],
            "Farmaco": item["farmaco"],
            "PDUFA": item["pdufa_date"],
            "Giorni": giorni_al_pdufa(item["pdufa_date"]),
            "AdComm %": item.get("adcomm_voto", "—"),
            "Labeling": "✅" if item.get("labeling_discussion") else "❌",
            "Score %": punteggio_approvazione(item),
            "Prezzo $": stock["prezzo"],
            "Var %": stock["variazione"],
            "Market Cap": stock["market_cap_str"],
            "Rischio": semaforo_rischio(item),
        })

    df_table = pd.DataFrame(table_data)
    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score %": st.column_config.ProgressColumn(
                "Score %", min_value=0, max_value=100, format="%d%%"
            ),
            "Var %": st.column_config.NumberColumn("Var %", format="%.2f%%"),
        },
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTO-REFRESH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if auto_refresh:
    st.markdown(
        f"🔄 Auto-aggiornamento attivo: i prezzi si aggiornano "
        f"ogni **{refresh_interval} secondi**."
    )
    time.sleep(refresh_interval)
    st.cache_data.clear()
    st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#6666aa; padding:20px;">'
    '🧬 <strong>Potential FDA Approval v2.0</strong> — '
    'Creato con Streamlit + yfinance + Plotly<br>'
    'Ultimo aggiornamento dati: '
    f'{datetime.now().strftime("%d/%m/%Y %H:%M")}<br><br>'
    '⚠️ <em>Questa app non fornisce consulenza finanziaria. '
    'Investi solo ciò che puoi permetterti di perdere. '
    'Verifica sempre i dati sui siti ufficiali FDA.</em>'
    '</div>',
    unsafe_allow_html=True,
)
