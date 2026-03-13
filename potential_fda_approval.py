"""
╔══════════════════════════════════════════════════════════════╗
║          🧬 POTENTIAL FDA APPROVAL v3.0 🧬                   ║
║    Cacciatore di catalizzatori FDA — Small & Mid Cap         ║
║                                                              ║
║  PARAMETRI RISPETTATI:                                       ║
║  1. Target: Small/Mid-Cap 200M-2B USD, PDUFA ≤30 giorni     ║
║  2. Dati: yfinance + lista hardcoded (no scraping)           ║
║  3. Filtro: AdComm >90% + flag Labeling Discussion           ║
║  4. Terminologia "da bar" per principianti                   ║
║  5. Streamlit con st.metric e st.balloons                    ║
║  6. Costo zero: tutte librerie open-source                   ║
║  7. Auto-aggiornamento prezzi in tempo reale                 ║
║                                                              ║
║  COME USARE:                                                 ║
║  pip install streamlit yfinance plotly pandas                 ║
║  streamlit run potential_fda_approval.py                      ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

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
# CSS
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
        background: rgba(30, 30, 80, 0.6);
        border-left: 4px solid #7c4dff;
        border-radius: 8px; padding: 16px 20px;
        margin: 8px 0; font-size: 0.92em;
    }
    .glossario-box strong { color: #b388ff; }
    .alert-labeling {
        background: linear-gradient(135deg, #1b5e20, #2e7d32);
        border: 2px solid #00e676; border-radius: 12px;
        padding: 16px; margin: 8px 0; color: #c8e6c9;
    }
    .alert-adcomm {
        background: linear-gradient(135deg, #e65100, #f57c00);
        border: 2px solid #ffab40; border-radius: 12px;
        padding: 16px; margin: 8px 0; color: #fff3e0;
    }
    .cap-filter-info {
        background: rgba(41, 121, 255, 0.15);
        border: 1px solid #2979ff; border-radius: 10px;
        padding: 12px 16px; margin: 8px 0;
    }
    [data-testid="stMetric"] {
        background: rgba(30, 30, 80, 0.5);
        border: 1px solid #3a3a7c;
        border-radius: 12px; padding: 16px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #12122e, #1a1a40);
    }
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOSSARIO "DA BAR" — Parametro 4 del prompt
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GLOSSARIO = {
    "PDUFA Date": {
        "da_bar": "📅 Giorno del Verdetto",
        "spiegazione": "Il giorno in cui la FDA dice SÌ o NO al farmaco. "
                       "Come aspettare il verdetto della giuria in tribunale."
    },
    "AdComm": {
        "da_bar": "👨‍⚖️ La Giuria degli Esperti",
        "spiegazione": "Un comitato di medici e scienziati vota se il farmaco funziona. "
                       "Se votano >90% sì = quasi fatta. "
                       "⚠️ NOTA: la FDA non convoca AdComm dal luglio 2025. "
                       "Il prossimo è previsto per il 30 aprile 2026."
    },
    "Market Cap": {
        "da_bar": "💰 Quanto vale il negozio",
        "spiegazione": "Prezzo di un'azione × tutte le azioni che esistono. "
                       "Noi cerchiamo i 'negozietti' (200M-2B$): abbastanza grandi "
                       "da non fallire domani, abbastanza piccoli da esplodere."
    },
    "Cash Runway": {
        "da_bar": "⛽ Benzina nel serbatoio",
        "spiegazione": "Quanti mesi l'azienda sopravvive coi soldi in banca, "
                       "senza guadagnare nulla. Più mesi = più tranquilli."
    },
    "Short Interest": {
        "da_bar": "🐻 Chi scommette CONTRO",
        "spiegazione": "% di gente che scommette che il titolo scenderà. "
                       "Se sono tanti e il farmaco viene approvato → BOOM verso l'alto "
                       "(si chiama 'short squeeze')."
    },
    "Labeling Discussion": {
        "da_bar": "🏷️ Stanno scrivendo il foglietto!",
        "spiegazione": "La FDA discute COME scrivere il foglietto illustrativo. "
                       "Segnale MOLTO POSITIVO: stanno pensando a COME venderlo, "
                       "non SE venderlo. È come se il notaio preparasse già il contratto."
    },
    "Priority Review": {
        "da_bar": "🚀 Corsia preferenziale",
        "spiegazione": "La FDA lo esamina in 6 mesi anziché 10 "
                       "perché il farmaco cura qualcosa di grave o senza alternative."
    },
    "Breakthrough Therapy": {
        "da_bar": "⚡ Farmaco rivoluzionario",
        "spiegazione": "La FDA riconosce che è molto meglio di tutto ciò che esiste. "
                       "Riceve aiuto extra per arrivare prima al mercato."
    },
    "Orphan Drug": {
        "da_bar": "🦄 Farmaco per malattia rara",
        "spiegazione": "Cura una malattia che colpisce poche persone. "
                       "L'azienda riceve vantaggi fiscali e 7 anni di esclusiva di mercato."
    },
    "NDA / BLA / sNDA": {
        "da_bar": "📝 La domanda ufficiale",
        "spiegazione": "NDA = domanda per farmaco chimico. BLA = per farmaco biologico. "
                       "sNDA = 'Espansione': il farmaco esiste già ma chiede un uso nuovo."
    },
    "Complete Response Letter (CRL)": {
        "da_bar": "❌ Bocciato (con appunti)",
        "spiegazione": "La FDA dice NO, ma spiega cosa manca. L'azienda può "
                       "correggere e riprovare. Non è la fine, ma è una brutta notizia."
    },
    "Accelerated Approval": {
        "da_bar": "⏩ Approvazione anticipata",
        "spiegazione": "La FDA approva in base a risultati 'promettenti' (biomarker) "
                       "prima di avere la prova definitiva. L'azienda deve poi "
                       "confermare con uno studio più grande."
    },
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATABASE CATALIZZATORI — Parametro 2 (hardcoded, no scraping)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚠️ AGGIORNAMENTO MENSILE:
# 1. Chiedi all'IA il Super-Prompt
# 2. Sostituisci questa lista `data = [...]`
# 3. Commit su GitHub → Streamlit si aggiorna da solo
#
# FONTI: fda.gov, comunicati stampa aziendali, SEC filings
# ULTIMO AGGIORNAMENTO: 12 marzo 2026
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

data = [
    {
        "ticker": "ALDX",
        "azienda": "Aldeyra Therapeutics",
        "farmaco": "Reproxalap (collirio)",
        "indicazione": "Malattia dell'occhio secco (Dry Eye Disease)",
        "pdufa_date": "2026-03-16",
        "adcomm_voto": None,  # Nessun AdComm convocato
        "adcomm_data": None,
        "tipo_review": "Standard Review",
        "designazioni": ["Fast Track"],
        "labeling_discussion": True,  # ← SEGNALE FORTE: FDA ha condiviso bozza etichetta dic. 2025
        "fase": "NDA (3ª sottomissione)",
        "note": "La FDA ha condiviso una bozza di etichetta a dicembre 2025 — segnale positivo forte. "
               "Però è la 3ª richiesta dopo 2 rifiuti (CRL). Il field trial NON ha raggiunto "
               "l'endpoint primario ma la FDA lo considera 'supportivo'. "
               "AbbVie ha opzione di licenza da $100M in caso di approvazione. "
               "Verifica su: ir.aldeyra.com",
        "rischio": "medio",
    },
    {
        "ticker": "RYTM",
        "azienda": "Rhythm Pharmaceuticals",
        "farmaco": "Setmelanotide (Imcivree)",
        "indicazione": "Obesità ipotalamica acquisita (espansione indicazione)",
        "pdufa_date": "2026-03-20",
        "adcomm_voto": None,  # Nessun AdComm convocato
        "adcomm_data": None,
        "tipo_review": "Priority Review",
        "designazioni": ["Orphan Drug"],
        "labeling_discussion": False,
        "fase": "sNDA (espansione)",
        "note": "Imcivree è GIÀ APPROVATO per BBS/POMC — questa è un'espansione. "
               "Trial Phase 3 TRANSCEND: -18.8% BMI vs placebo (p<0.0001), 142 pazienti. "
               "Azienda già commerciale: ricavi $57M nel Q4 2025. "
               "Dati tra i più solidi del mese. Verifica su: ir.rhythmtx.com",
        "rischio": "basso",
    },
    {
        "ticker": "RCKT",
        "azienda": "Rocket Pharmaceuticals",
        "farmaco": "Kresladi (marnetegragene autotemcel)",
        "indicazione": "Deficit adesione leucocitaria grave (LAD-I) — terapia genica",
        "pdufa_date": "2026-03-28",
        "adcomm_voto": None,
        "adcomm_data": None,
        "tipo_review": "Standard Review",
        "designazioni": ["Orphan Drug", "Breakthrough Therapy"],
        "labeling_discussion": False,
        "fase": "BLA (ri-sottomissione)",
        "note": "Ri-sottomissione BLA dopo primo rifiuto. Trial Phase 1/2: 100% sopravvivenza "
               "a 1+ anno, tutti endpoint primari e secondari raggiunti. "
               "LAD-I è ultra-rara e quasi sempre fatale nell'infanzia senza trapianto. "
               "Verifica su: ir.rocketpharma.com",
        "rischio": "medio",
    },
    {
        "ticker": "DNLI",
        "azienda": "Denali Therapeutics",
        "farmaco": "Tividenofusp alfa (DNL310)",
        "indicazione": "Sindrome di Hunter (MPS II) — terapia enzimatica innovativa",
        "pdufa_date": "2026-04-05",
        "adcomm_voto": None,
        "adcomm_data": None,
        "tipo_review": "Priority Review",
        "designazioni": ["Orphan Drug", "Breakthrough Therapy"],
        "labeling_discussion": False,
        "fase": "BLA (accelerated approval)",
        "note": "Dati Phase 1/2 pubblicati su New England Journal of Medicine (gen. 2026). "
               "Riduzione biomarker CSF -91% a 24 settimane. $966M in cassa. "
               "Accordo con Royalty Pharma da $275M legato a vendite future. "
               "NB: Market cap ~$2.7B, leggermente sopra il target 200M-2B. "
               "Verifica su: investors.denalitherapeutics.com",
        "rischio": "medio",
    },
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FUNZIONI CORE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@st.cache_data(ttl=300)  # Cache 5 min — Parametro 7: auto-aggiornamento
def get_stock_data(ticker: str) -> dict:
    """Scarica dati finanziari via yfinance (Parametro 2: gratuito, no scraping)."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="3mo")

        market_cap = info.get("marketCap", 0)
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        prev_close = info.get("previousClose", price)
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0

        # Cash Runway ("Benzina nel serbatoio")
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
            "market_cap_str": format_cap(market_cap),
            "cash": total_cash,
            "cash_str": format_cap(total_cash),
            "cash_runway_mesi": cash_runway_months,
            "short_interest": round(short_pct, 1) if short_pct else 0,
            "storico": hist,
            "nome": info.get("shortName", ticker),
            "volume_medio": info.get("averageVolume", 0),
            "errore": None,
        }
    except Exception as e:
        return {
            "prezzo": 0, "variazione": 0, "market_cap": 0,
            "market_cap_str": "N/D", "cash": 0, "cash_str": "N/D",
            "cash_runway_mesi": None, "short_interest": 0,
            "storico": pd.DataFrame(), "nome": ticker,
            "volume_medio": 0, "errore": str(e),
        }


def format_cap(value: float) -> str:
    if value >= 1e9:
        return f"${value / 1e9:.2f}B"
    elif value >= 1e6:
        return f"${value / 1e6:.1f}M"
    elif value > 0:
        return f"${value:,.0f}"
    return "N/D"


def giorni_al_verdetto(pdufa_str: str) -> int:
    """Quanti giorni mancano al 'Giorno del Verdetto'."""
    try:
        return (datetime.strptime(pdufa_str, "%Y-%m-%d") - datetime.now()).days
    except (ValueError, TypeError):
        return -999


def semaforo(rischio: str) -> str:
    r = rischio.lower()
    if r == "basso":
        return "🟢 BASSO"
    elif r == "medio":
        return "🟡 MEDIO"
    elif r in ("medio-alto", "alto"):
        return "🔴 ALTO"
    return "⚪ N/D"


def punteggio(item: dict) -> int:
    """Score approvazione 0-99. Parametro 3: premia AdComm >90% e Labeling."""
    s = 50  # Base

    # --- ADCOMM (Parametro 3: filtra >90%) ---
    voto = item.get("adcomm_voto")
    if voto is not None:
        if voto >= 90:
            s += 25  # Unanime = bonus massimo
        elif voto >= 75:
            s += 15
        elif voto >= 60:
            s += 5
        else:
            s -= 10

    # --- LABELING DISCUSSION (Parametro 3: segnala) ---
    if item.get("labeling_discussion"):
        s += 15  # Segnale molto forte

    # --- TIPO REVIEW ---
    if item.get("tipo_review") == "Priority Review":
        s += 5

    # --- DESIGNAZIONI SPECIALI ---
    desig = item.get("designazioni", [])
    if "Breakthrough Therapy" in desig:
        s += 5
    if "Fast Track" in desig:
        s += 3
    if "Orphan Drug" in desig:
        s += 2

    # --- FARMACO GIÀ APPROVATO (espansione) ---
    fase = item.get("fase", "")
    if "sNDA" in fase or "espansione" in fase.lower():
        s += 5  # Meno rischio se il farmaco esiste già

    return min(s, 99)


def badge_class(score: int) -> str:
    if score >= 80:
        return "badge-green"
    elif score >= 60:
        return "badge-yellow"
    elif score >= 40:
        return "badge-blue"
    return "badge-red"


def in_range_cap(market_cap: float, min_cap: float, max_cap: float) -> bool:
    """Parametro 1: filtra per Market Cap."""
    if market_cap == 0:
        return True  # Se non disponibile, mostra comunque
    return min_cap <= market_cap <= max_cap


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEADER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown('<p class="neon-title">🧬 Potential FDA Approval</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="neon-subtitle">'
    'Caccia ai catalizzatori FDA — Small &amp; Mid Cap Biotech (200M-2B USD)'
    '</p>',
    unsafe_allow_html=True,
)
st.markdown("---")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR — TUTTI I FILTRI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("## ⚙️ Filtri")

    # --- PARAMETRO 1: Market Cap 200M-2B ---
    st.markdown("### 💰 Quanto vale il negozio (Market Cap)")
    cap_min = st.number_input(
        "Minimo ($M)", min_value=0, max_value=10000, value=200, step=50
    )
    cap_max = st.number_input(
        "Massimo ($M)", min_value=0, max_value=10000, value=2000, step=100
    )
    mostra_fuori_range = st.checkbox(
        "Mostra anche titoli fuori range (con avviso)", value=True
    )

    st.markdown("---")

    # --- PARAMETRO 1: PDUFA entro 30 giorni ---
    max_giorni = st.slider(
        "📅 Verdetto entro (giorni)", min_value=7, max_value=90, value=30, step=7
    )

    # --- Rischio ---
    filtro_rischio = st.multiselect(
        "🚦 Livello di rischio",
        options=["basso", "medio", "medio-alto", "alto"],
        default=["basso", "medio", "medio-alto", "alto"],
    )

    st.markdown("---")

    # --- PARAMETRO 3: AdComm >90% ---
    st.markdown("### 👨‍⚖️ Giuria Esperti (AdComm)")
    solo_unanime = st.checkbox("Solo AdComm unanime (>90%)", value=False)
    st.markdown(
        '<div class="cap-filter-info">'
        '⚠️ <strong>Nota importante:</strong> La FDA non convoca AdComm '
        'da luglio 2025. Il prossimo è previsto per il 30 aprile 2026 '
        '(AstraZeneca/oncologia). Nessun catalizzatore attuale ha un voto recente.'
        '</div>',
        unsafe_allow_html=True,
    )

    # --- PARAMETRO 3: Labeling Discussion ---
    solo_labeling = st.checkbox("🏷️ Solo con Labeling Discussion (etichetta in corso)")

    st.markdown("---")

    # --- PARAMETRO 7: Auto-refresh ---
    st.markdown("### 🔄 Auto-Aggiornamento Prezzi")
    auto_refresh = st.checkbox("Aggiorna automaticamente")
    refresh_sec = st.selectbox("Ogni quanti secondi?", [30, 60, 120, 300], index=1)

    st.markdown("---")

    # --- PARAMETRO 4: Glossario da bar ---
    st.markdown("### 📖 Dizionario 'da bar'")
    with st.expander("📚 Clicca per capire tutto", expanded=False):
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
        "⚠️ **Disclaimer**: App solo a scopo educativo. "
        "Non è consulenza finanziaria. Verifica sempre su "
        "[fda.gov](https://www.fda.gov) prima di qualsiasi decisione."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FILTRAGGIO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

filtered = []
fuori_range_cap = []

for item in data:
    giorni = giorni_al_verdetto(item["pdufa_date"])

    # Filtro giorni
    if giorni < 0 or giorni > max_giorni:
        continue

    # Filtro rischio
    if item.get("rischio", "medio").lower() not in filtro_rischio:
        continue

    # Filtro AdComm unanime (Parametro 3)
    if solo_unanime:
        voto = item.get("adcomm_voto")
        if voto is None or voto < 90:
            continue

    # Filtro Labeling (Parametro 3)
    if solo_labeling and not item.get("labeling_discussion"):
        continue

    # Filtro Market Cap (Parametro 1)
    stock_data = get_stock_data(item["ticker"])
    mc = stock_data["market_cap"]
    cap_min_val = cap_min * 1e6
    cap_max_val = cap_max * 1e6

    if not in_range_cap(mc, cap_min_val, cap_max_val):
        if mostra_fuori_range:
            fuori_range_cap.append((item, stock_data))
        continue

    filtered.append((item, stock_data))

# Ordina per PDUFA più vicino
filtered.sort(key=lambda x: giorni_al_verdetto(x[0]["pdufa_date"]))
fuori_range_cap.sort(key=lambda x: giorni_al_verdetto(x[0]["pdufa_date"]))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DASHBOARD RIEPILOGO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("🧬 Catalizzatori Totali", len(data))
col_b.metric("🎯 Nel range 200M-2B", len(filtered))
col_c.metric(
    "🏷️ Con Labeling",
    sum(1 for d, _ in filtered if d.get("labeling_discussion")),
)
alta = sum(1 for d, _ in filtered if punteggio(d) >= 75)
col_d.metric("🟢 Alta Probabilità", alta)

st.markdown("---")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AVVISO ADCOMM — Parametro 3
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

any_adcomm = any(d.get("adcomm_voto") is not None for d in data)
if not any_adcomm:
    st.markdown(
        '<div class="alert-adcomm">'
        '👨‍⚖️ <strong>NESSUN ADCOMM RECENTE</strong> — '
        'La FDA non ha convocato advisory committee dal luglio 2025. '
        'Nessuno dei catalizzatori attuali ha un voto di "Giuria Esperti". '
        'Il filtro AdComm >90% è pronto per quando riprenderanno '
        '(prossimo previsto: 30 aprile 2026, oncologia AstraZeneca).'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEGNALAZIONE LABELING DISCUSSION — Parametro 3
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

labeling_items = [(d, s) for d, s in filtered if d.get("labeling_discussion")]
if labeling_items:
    for d, s in labeling_items:
        st.markdown(
            f'<div class="alert-labeling">'
            f'🏷️ <strong>LABELING IN CORSO — {d["azienda"]} ({d["ticker"]})</strong><br>'
            f'Il farmaco <strong>{d["farmaco"]}</strong> ha una discussione sull\'etichetta attiva. '
            f'Traduzione "da bar": la FDA sta già scrivendo il foglietto illustrativo! '
            f'Questo è un segnale MOLTO positivo — significa che pensano a COME venderlo, non SE.'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown("")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TIMELINE — Parametro 5 (grafica accattivante)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

all_display = filtered + fuori_range_cap
if all_display:
    st.markdown("### 📅 Timeline — Prossimi 'Giorni del Verdetto'")

    fig = go.Figure()
    for item, stock in all_display:
        g = giorni_al_verdetto(item["pdufa_date"])
        sc = punteggio(item)
        in_range = (item, stock) in filtered
        color = (
            "#00e676" if sc >= 75 else "#ffc107" if sc >= 60
            else "#2979ff" if sc >= 40 else "#ff5252"
        )
        if not in_range:
            color = "#666688"

        label = f"{item['azienda']}" + ("" if in_range else " ⚠️ fuori range")

        fig.add_trace(go.Bar(
            x=[g], y=[f"{label}<br>({item['farmaco']})"],
            orientation="h", marker_color=color,
            text=f"{g}g — Score {sc}%",
            textposition="outside", showlegend=False,
            hovertemplate=(
                f"<b>{item['azienda']}</b> ({item['ticker']})<br>"
                f"Farmaco: {item['farmaco']}<br>"
                f"PDUFA: {item['pdufa_date']}<br>"
                f"Giorni: {g}<br>Score: {sc}%<br>"
                f"Market Cap: {stock['market_cap_str']}<br>"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Giorni al Verdetto →",
        height=max(250, len(all_display) * 90),
        margin=dict(l=20, r=140, t=20, b=40),
        font=dict(color="#ccccee"),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCHEDE DETTAGLIO — Parametro 5 (st.metric, st.balloons)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def render_card(item, stock, in_range=True):
    giorni = giorni_al_verdetto(item["pdufa_date"])
    sc = punteggio(item)
    bc = badge_class(sc)

    # Header
    range_warning = "" if in_range else (
        ' <span class="badge-red">⚠️ FUORI RANGE CAP</span>'
    )
    st.markdown(
        f'<div class="biotech-card">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<div>'
        f'<span style="font-size:1.6em;font-weight:800;color:#e0e0ff;">'
        f'{item["azienda"]}</span>'
        f'<span style="color:#8888bb;margin-left:12px;">({item["ticker"]})</span>'
        f'{range_warning}'
        f'</div>'
        f'<span class="{bc}">Score: {sc}%</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # --- Parametro 5: st.metric per i prezzi ---
    m1, m2, m3, m4, m5 = st.columns(5)
    delta_color = "normal" if stock["variazione"] >= 0 else "inverse"
    m1.metric(
        "💵 Prezzo",
        f"${stock['prezzo']}" if stock["prezzo"] else "N/D",
        f"{stock['variazione']:+.2f}%" if stock["prezzo"] else None,
        delta_color=delta_color,
    )
    m2.metric("💰 Valore Negozio", stock["market_cap_str"])
    m3.metric("⛽ Benzina (Cash)", stock["cash_str"])
    m4.metric(
        "⏱️ Mesi di Benzina",
        f"{stock['cash_runway_mesi']}m" if stock["cash_runway_mesi"] else "N/D",
    )
    m5.metric("🐻 Contro-scommesse", f"{stock['short_interest']}%")

    # Dettagli
    d1, d2 = st.columns(2)
    with d1:
        st.markdown(f"**📅 Giorno del Verdetto:** `{item['pdufa_date']}` — **{giorni} giorni**")
        st.markdown(f"**📝 Tipo domanda:** {item['fase']}")
        st.markdown(f"**🚀 Tipo Review:** {item['tipo_review']}")
        if item.get("designazioni"):
            tags = " ".join(f'<span class="badge-blue">{d}</span>' for d in item["designazioni"])
            st.markdown(f"**⚡ Designazioni:** {tags}", unsafe_allow_html=True)

    with d2:
        # AdComm — Parametro 3
        if item.get("adcomm_voto") is not None:
            v = item["adcomm_voto"]
            emoji = "✅" if v >= 90 else "⚠️" if v >= 70 else "❌"
            st.markdown(f"**👨‍⚖️ Giuria Esperti:** {emoji} **{v}%** (data: {item.get('adcomm_data', 'N/D')})")
            if v >= 90:
                st.markdown('<span class="badge-green">UNANIME — Segnale fortissimo</span>', unsafe_allow_html=True)
        else:
            st.markdown("**👨‍⚖️ Giuria Esperti:** Nessun AdComm convocato")

        # Labeling — Parametro 3
        if item.get("labeling_discussion"):
            st.markdown(
                '**🏷️ Stanno scrivendo il foglietto:** '
                '<span class="badge-green">IN CORSO — Segnale MOLTO POSITIVO</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("**🏷️ Foglietto illustrativo:** Non ancora in discussione")

        st.markdown(f"**🚦 Semaforo Rischio:** {semaforo(item.get('rischio', 'medio'))}")

    # Note
    if item.get("note"):
        st.info(f"📌 **Note:** {item['note']}")

    # Grafico candlestick
    if not stock["storico"].empty:
        with st.expander(f"📈 Grafico 3 mesi — {item['ticker']}", expanded=False):
            fig_s = go.Figure()
            fig_s.add_trace(go.Candlestick(
                x=stock["storico"].index,
                open=stock["storico"]["Open"],
                high=stock["storico"]["High"],
                low=stock["storico"]["Low"],
                close=stock["storico"]["Close"],
                name=item["ticker"],
            ))
            try:
                pdufa_dt = datetime.strptime(item["pdufa_date"], "%Y-%m-%d")
                fig_s.add_vline(
                    x=pdufa_dt.timestamp() * 1000,
                    line_dash="dash", line_color="#ff4081",
                    annotation_text="📅 VERDETTO",
                    annotation_font_color="#ff4081",
                )
            except ValueError:
                pass
            fig_s.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=350, xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=30, b=10),
                font=dict(color="#ccccee"),
            )
            st.plotly_chart(fig_s, use_container_width=True)

    if stock.get("errore"):
        st.warning(f"⚠️ Errore dati {item['ticker']}: {stock['errore']}")

    st.markdown("---")

    # --- Parametro 5: st.balloons() per alta probabilità ---
    if sc >= 90 and giorni <= 7:
        st.balloons()


# Render cards nel range
if not filtered and not fuori_range_cap:
    st.warning("Nessun catalizzatore corrisponde ai filtri. Prova ad allargare i parametri.")
else:
    if filtered:
        st.markdown(f"### 🎯 Nel range {cap_min}M - {cap_max}M USD")
        for item, stock in filtered:
            render_card(item, stock, in_range=True)

    if fuori_range_cap:
        st.markdown(f"### ⚠️ Fuori range Market Cap (comunque interessanti)")
        for item, stock in fuori_range_cap:
            render_card(item, stock, in_range=False)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABELLA RIEPILOGATIVA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if all_display:
    st.markdown("### 📊 Tabella Riepilogativa")
    rows = []
    for item, stock in all_display:
        in_r = (item, stock) in filtered
        rows.append({
            "Ticker": item["ticker"],
            "Azienda": item["azienda"],
            "Farmaco": item["farmaco"],
            "PDUFA": item["pdufa_date"],
            "Giorni": giorni_al_verdetto(item["pdufa_date"]),
            "AdComm %": item.get("adcomm_voto") or "—",
            "Labeling": "✅" if item.get("labeling_discussion") else "❌",
            "Score %": punteggio(item),
            "Prezzo $": stock["prezzo"],
            "Var %": stock["variazione"],
            "Market Cap": stock["market_cap_str"],
            "In Range": "✅" if in_r else "⚠️",
            "Rischio": semaforo(item.get("rischio", "medio")),
        })

    df = pd.DataFrame(rows)
    st.dataframe(
        df, use_container_width=True, hide_index=True,
        column_config={
            "Score %": st.column_config.ProgressColumn(
                "Score %", min_value=0, max_value=100, format="%d%%"
            ),
            "Var %": st.column_config.NumberColumn("Var %", format="%.2f%%"),
        },
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PARAMETRO 7: AUTO-REFRESH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if auto_refresh:
    st.markdown(f"🔄 Auto-aggiornamento attivo ogni **{refresh_sec} secondi**.")
    time.sleep(refresh_sec)
    st.cache_data.clear()
    st.rerun()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FOOTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#6666aa;padding:20px;">'
    '🧬 <strong>Potential FDA Approval v3.0</strong> — '
    'Streamlit + yfinance + Plotly (tutto gratis)<br>'
    f'Dati catalizzatori aggiornati al: 12/03/2026<br>'
    f'Prezzi aggiornati alle: {datetime.now().strftime("%H:%M:%S")}<br><br>'
    '⚠️ <em>App educativa — non è consulenza finanziaria. '
    'Verifica sempre su fda.gov. Investi solo ciò che puoi perdere.</em>'
    '</div>',
    unsafe_allow_html=True,
)
