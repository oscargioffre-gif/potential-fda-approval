# FDA RADAR v15 — Compatto + Espansione al tocco + Catalizzatori completi
import streamlit as st
import yfinance as yf
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="FDA Radar", page_icon="favicon.png", layout="wide")
DATA_AGG = "2026-03-16"
CAP_MIN, CAP_MAX = 100_000_000, 2_000_000_000

# === CATALIZZATORI COMPLETI ===
# Tipo: PDUFA / PH3_DATA / PH2_DATA / BLA_FILING / PH3_ENROLL
CATALYSTS = [
    {"ticker":"ALDX","company":"Aldeyra Therapeutics","drug":"Reproxalap","what":"Occhio secco",
     "type":"PDUFA","date":"2026-03-16","phase":"NDA","crl":2,"labeling":True,
     "nota":"3a richiesta dopo 2 CRL. Bozza etichetta condivisa. AbbVie $100M.","risk":"medio-alto"},
    {"ticker":"RCKT","company":"Rocket Pharmaceuticals","drug":"Kresladi","what":"LAD-I (fatale bambini)",
     "type":"PDUFA","date":"2026-03-28","phase":"BLA","crl":1,"labeling":False,
     "nota":"Terapia genica. 100% sopravvivenza. Breakthrough+Orphan.","risk":"medio"},
    {"ticker":"OCGN","company":"Ocugen","drug":"OCU410","what":"Atrofia geografica (vista)",
     "type":"PH2_DATA","date":"2026-03-31","phase":"Phase 2","crl":0,"labeling":False,
     "nota":"Dati completi Phase 2 attesi marzo 2026. Terapia genica oculare.","risk":"alto"},
    {"ticker":"OCGN","company":"Ocugen","drug":"OCU400","what":"Retinite pigmentosa (cecita)",
     "type":"BLA_FILING","date":"2026-09-30","phase":"Phase 3","crl":0,"labeling":False,
     "nota":"Phase 3 enrollment completato mar.2026. Rolling BLA da Q3 2026. Orphan+RMAT.","risk":"alto"},
    {"ticker":"MNMD","company":"MindMed","drug":"MM120","what":"Disturbo ansia generalizzata",
     "type":"PH3_DATA","date":"2026-06-30","phase":"Phase 3","crl":0,"labeling":False,
     "nota":"3 trial Phase 3 in corso. Primo readout atteso H1 2026. $258M finanziamento.","risk":"alto"},
    {"ticker":"XENE","company":"Xenon Pharmaceuticals","drug":"Azetukalner","what":"Epilessia focale",
     "type":"PH3_DATA","date":"2026-03-31","phase":"Phase 3","crl":0,"labeling":False,
     "nota":"Phase 2b best-in-class. Phase 3 FOS readout atteso inizio 2026. Potenziale $2.6B peak sales.","risk":"medio"},
    {"ticker":"PDSB","company":"PDS Biotechnology","drug":"PDS0101","what":"Cancro testa-collo (HPV+)",
     "type":"PH3_DATA","date":"2026-09-30","phase":"Phase 3","crl":0,"labeling":False,
     "nota":"Phase 3 VERSATILE-003 readout H2 2026. Partner NCI/Merck. Cap ~$39M.","risk":"molto alto"},
    {"ticker":"IMVT","company":"Immunovant","drug":"Batoclimab","what":"Miastenia gravis",
     "type":"PH3_DATA","date":"2026-06-30","phase":"Phase 3","crl":0,"labeling":False,
     "nota":"Multiple Phase 3 in corso. Anti-FcRn. Partner Roivant.","risk":"medio"},
    {"ticker":"VRDN","company":"Viridian Therapeutics","drug":"Veligrotug","what":"Malattia occhio tiroide",
     "type":"PDUFA","date":"2026-06-30","phase":"BLA","crl":0,"labeling":False,
     "nota":"Breakthrough+Priority Review. Phase 3 THRIVE positivo. PDUFA 30 giu 2026.","risk":"basso"},
    {"ticker":"VERA","company":"Vera Therapeutics","drug":"Atacicept","what":"Nefropatia IgA (rene)",
     "type":"PDUFA","date":"2026-07-07","phase":"BLA","crl":0,"labeling":False,
     "nota":"Priority Review. Phase 3 ORIGIN: -46% proteinuria. PDUFA 7 lug 2026.","risk":"basso"},
    {"ticker":"TVTX","company":"Travere Therapeutics","drug":"Sparsentan","what":"FSGS (rene raro)",
     "type":"PDUFA","date":"2026-01-13","phase":"sNDA","crl":0,"labeling":False,
     "nota":"Prima terapia per FSGS. Approvato gen.2026.","risk":"completato"},
    {"ticker":"DAWN","company":"Day One Bio","drug":"Tovorafenib","what":"Glioma pediatrico",
     "type":"PH3_DATA","date":"2026-06-30","phase":"Phase 3","crl":0,"labeling":False,
     "nota":"Gia approvato per glioma pediatrico. Phase 3 espansione adulti.","risk":"medio"},
    {"ticker":"BEAM","company":"Beam Therapeutics","drug":"BEAM-101","what":"Anemia falciforme",
     "type":"PH2_DATA","date":"2026-06-30","phase":"Phase 1/2","crl":0,"labeling":False,
     "nota":"Base editing. Primi dati clinici attesi 2026.","risk":"molto alto"},
    {"ticker":"EDIT","company":"Editas Medicine","drug":"EDIT-101","what":"Amaurosi congenita Leber",
     "type":"PH2_DATA","date":"2026-06-30","phase":"Phase 1/2","crl":0,"labeling":False,
     "nota":"CRISPR in vivo. Dati aggiornati attesi 2026.","risk":"molto alto"},
    {"ticker":"VKTX","company":"Viking Therapeutics","drug":"VK2735","what":"Obesita (GLP-1 orale)",
     "type":"PH3_DATA","date":"2026-12-31","phase":"Phase 3","crl":0,"labeling":False,
     "nota":"GLP-1 orale per obesita. Phase 2: -8.2% peso in 28gg. Phase 3 iniziato 2025.","risk":"medio"},
]

STORICO = [
    {"data":"2026-03-11","ticker":"WELL","esito":"OK","farmaco":"Leucovorin","move":"+12%","nota":"Cerebral folate deficiency"},
    {"data":"2026-03-06","ticker":"LNTH","esito":"OK","farmaco":"PYLARIFY TruVu","move":"+8%","nota":"Imaging prostatico"},
    {"data":"2026-03-06","ticker":"BMY","esito":"OK","farmaco":"Sotyktu","move":"+3%","nota":"Artrite psoriasica"},
    {"data":"2026-02-25","ticker":"ENSG","esito":"OK","farmaco":"DESMODA","move":"+45%","nota":"Diabete insipido"},
    {"data":"2026-01-14","ticker":"CUTX","esito":"OK","farmaco":"CUTX-101","move":"+85%","nota":"Malattia Menkes"},
    {"data":"2026-01-10","ticker":"ATRA","esito":"NO","farmaco":"Tabelecleucel","move":"-62%","nota":"EBV+ PTLD CRL"},
    {"data":"2025-12-16","ticker":"ALDX","esito":"RINV","farmaco":"Reproxalap","move":"+18%","nota":"PDUFA esteso"},
]

PHASE_DATA = {"3":{"ok":58,"pos":"+20-60%","neg":"-50-80%"},"2":{"ok":29,"pos":"+30-80%","neg":"-40-70%"},"1":{"ok":52,"pos":"+15-40%","neg":"-20-50%"}}
ENDPOINT_IT = {"overall survival":"Sopravvivenza","progression-free survival":"Senza peggioramento","progression free survival":"Senza peggioramento","objective response rate":"% tumore ridotto","overall response rate":"% miglioramento","adverse events":"Effetti collaterali","safety":"Sicurezza","ocular discomfort":"Fastidio occhi","seizure frequency":"Crisi epilettiche","change in bmi":"Cambio peso"}

def ep_it(text):
    if not text: return "Non specificato"
    for k,v in ENDPOINT_IT.items():
        if k in text.lower(): return v
    return text[:50]

def fmt_n(n):
    if n >= 1e6: return f"{n/1e6:.1f}M"
    elif n >= 1e3: return f"{n/1e3:.0f}K"
    return str(int(n))

TYPE_LABELS = {"PDUFA":"Verdetto FDA","PH3_DATA":"Dati Phase 3","PH2_DATA":"Dati Phase 2","BLA_FILING":"Deposito BLA","PH3_ENROLL":"Arruolamento Phase 3"}
RISK_EMOJI = {"basso":"🟢","medio":"🟡","medio-alto":"🟠","alto":"🔴","molto alto":"🔴","completato":"✅"}

# === BATCH MARKET DATA ===
@st.cache_data(ttl=900)
def batch_prices(tickers_str):
    tickers = tickers_str.split(",")
    result = {}
    try:
        df = yf.download(tickers, period="1mo", group_by="ticker", progress=False, timeout=15)
        for t in tickers:
            try:
                td = df[t] if len(tickers) > 1 and t in df.columns.get_level_values(0) else df if len(tickers) == 1 else None
                if td is None or td.empty: result[t] = None; continue
                td = td.dropna(how="all")
                if td.empty: result[t] = None; continue
                lc = float(td["Close"].iloc[-1])
                pc = float(td["Close"].iloc[-2]) if len(td)>=2 else lc
                ch = round(((lc-pc)/pc*100),2) if pc else 0
                lv = int(td["Volume"].iloc[-1]) if "Volume" in td else 0
                av = int(td["Volume"].mean()) if "Volume" in td else 1
                vr = round(lv/av,2) if av>0 else 0
                vt = "neutro"
                if len(td)>=10 and "Volume" in td:
                    rv=td["Volume"].tail(5).mean();ov=td["Volume"].tail(15).head(10).mean()
                    if ov>0:
                        vc=(rv-ov)/ov
                        if vc>0.5: vt="spike"
                        elif vc>0.2: vt="crescente"
                result[t] = {"price":round(lc,2),"change":ch,"vol":lv,"vol_avg":av,"vol_ratio":vr,"vol_trend":vt}
            except: result[t] = None
    except:
        for t in tickers: result[t] = None
    return result

@st.cache_data(ttl=1800)
def get_info(ticker):
    try:
        info = yf.Ticker(ticker).info
        cap = info.get("marketCap",0) or 0
        si = info.get("shortPercentOfFloat",0) or 0
        if si and si<1: si*=100
        pre = info.get("preMarketPrice",0)
        prec = info.get("preMarketChangePercent",0)
        post = info.get("postMarketPrice",0)
        postc = info.get("postMarketChangePercent",0)
        return {"cap":cap,"short":round(si,1),
                "pre":round(pre,2) if pre else None,"prec":round(prec*100,2) if prec and abs(prec)<1 else round(prec,2) if prec else None,
                "post":round(post,2) if post else None,"postc":round(postc*100,2) if postc and abs(postc)<1 else round(postc,2) if postc else None}
    except: return {"cap":0,"short":0,"pre":None,"prec":None,"post":None,"postc":None}

@st.cache_data(ttl=3600)
def get_trials(company):
    try:
        r=requests.get("https://clinicaltrials.gov/api/v2/studies",params={"query.spons":company,"filter.overallStatus":"RECRUITING|ACTIVE_NOT_RECRUITING|ENROLLING_BY_INVITATION|NOT_YET_RECRUITING","pageSize":6,"fields":"NCTId,BriefTitle,Phase,Condition,EnrollmentInfo,DesignInfo,PrimaryOutcome,PrimaryCompletionDate"},timeout=8)
        if r.status_code!=200: return []
        out=[]
        for s in r.json().get("studies",[]):
            p=s.get("protocolSection",{});ident=p.get("identificationModule",{});des=p.get("designModule",{});cond=p.get("conditionsModule",{});outc=p.get("outcomesModule",{});pcd=p.get("statusModule",{}).get("primaryCompletionDateStruct",{})
            phases=des.get("phases",[]) if des else [];ei=des.get("enrollmentInfo",{}) if des else {};di=des.get("designInfo",{}) if des else {};mi=di.get("maskingInfo",{}) if di else {};po=outc.get("primaryOutcomes",[]) if outc else []
            out.append({"nct":ident.get("nctId",""),"title":ident.get("briefTitle",""),"phase":", ".join(phases) if phases else "N/A","conditions":", ".join(cond.get("conditions",[])[:2]) if cond else "N/D","enrollment":ei.get("count",0) if ei else 0,"mask":mi.get("masking","") if mi else "","endpoint":po[0].get("measure","") if po else "","completion":pcd.get("date","") if pcd else ""})
        return out
    except: return []

# === APP ===
st.title("FDA Radar")

with st.expander("Come funziona"):
    st.write("Volume/media 3x+ = qualcuno si posiziona. Pre/After = movimenti fuori orario.")
    st.write("Volume + prezzo sale = comprano. Volume + prezzo scende = vendono.")
    st.write("Short alto + notizia buona = possibile squeeze.")
    c1,c2,c3=st.columns(3)
    c1.metric("Phase 1","52% ok","Se ok +15-40%")
    c2.metric("Phase 2","29% ok","Se ok +30-80%")
    c3.metric("Phase 3","58% ok","Se ok +20-60%")

st.divider()

# Load batch prices
all_tickers = list(set(c["ticker"] for c in CATALYSTS if c.get("risk") != "completato"))
prices = batch_prices(",".join(all_tickers))

# Group catalysts by type
now = datetime.now()
pdufa_items = [c for c in CATALYSTS if c["type"]=="PDUFA" and c.get("risk")!="completato"]
data_items = [c for c in CATALYSTS if c["type"] in ("PH3_DATA","PH2_DATA") and c.get("risk")!="completato"]
filing_items = [c for c in CATALYSTS if c["type"] in ("BLA_FILING","PH3_ENROLL") and c.get("risk")!="completato"]

def days_to(d):
    try: return (datetime.strptime(d,"%Y-%m-%d")-now).days
    except: return 999

def render_compact_card(cat):
    ticker = cat["ticker"]
    pd = prices.get(ticker)
    info = get_info(ticker)
    g = days_to(cat["date"])
    risk_em = RISK_EMOJI.get(cat.get("risk","medio"),"")
    type_lbl = TYPE_LABELS.get(cat["type"],cat["type"])

    # Compact header
    price_str = f"${pd['price']}" if pd else "N/D"
    change_str = f"{pd['change']:+.1f}%" if pd else ""
    cap_str = f"${info['cap']/1e9:.2f}B" if info["cap"]>=1e9 else f"${info['cap']/1e6:.0f}M" if info["cap"]>=1e6 else "N/D"
    vol_str = f"{pd['vol_ratio']}x" if pd and pd["vol_ratio"] else ""

    # Urgency
    if g <= 0: urgency = "OGGI"
    elif g <= 3: urgency = f"{g}g"
    elif g <= 14: urgency = f"{g}g"
    elif g <= 30: urgency = f"{g}g"
    else: urgency = f"{g}g"

    if g <= 3: st.error(f"**{ticker}** {price_str} {change_str} | {cap_str} | Vol {vol_str} | {risk_em} | **{type_lbl}: {urgency}**")
    elif g <= 14: st.warning(f"**{ticker}** {price_str} {change_str} | {cap_str} | Vol {vol_str} | {risk_em} | **{type_lbl}: {urgency}**")
    else: st.info(f"**{ticker}** {price_str} {change_str} | {cap_str} | Vol {vol_str} | {risk_em} | **{type_lbl}: {urgency}**")

    # Expand on touch
    with st.expander(f"{ticker} — {cat['company']} — {cat['drug']} — {cat['what']}"):
        st.write(cat["nota"])
        if cat.get("crl",0) > 0: st.caption(f"Bocciature precedenti: {cat['crl']}")
        if cat.get("labeling"): st.caption("FDA sta scrivendo il foglietto (segnale positivo)")
        st.caption(f"Fase: {cat['phase']} | Data catalizzatore: {cat['date']} | Rischio: {cat.get('risk','N/D')}")

        # Market data
        if pd:
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Prezzo",f"${pd['price']}",f"{pd['change']:+.1f}%",delta_color="normal" if pd["change"]>=0 else "inverse")
            m2.metric("Cap",cap_str)
            m3.metric("Vol/Media",f"{pd['vol_ratio']}x","ESPLOSIVO" if pd["vol_ratio"]>=3 else "Alto" if pd["vol_ratio"]>=2 else None)
            m4.metric("Short",f"{info['short']}%" if info["short"] else "N/D","Molto alto" if info["short"]>=20 else None)

            v1,v2,v3 = st.columns(3)
            v1.metric("Vol oggi",fmt_n(pd["vol"]) if pd["vol"] else "N/D")
            v2.metric("Vol medio",fmt_n(pd["vol_avg"]) if pd["vol_avg"] else "N/D")
            v3.metric("Trend",pd.get("vol_trend","N/D").upper())

            pm1,pm2 = st.columns(2)
            pm1.metric("Pre-Market",f"${info['pre']}" if info.get("pre") else "Chiuso",f"{info['prec']:+.1f}%" if info.get("prec") else None)
            pm2.metric("After-Hours",f"${info['post']}" if info.get("post") else "Chiuso",f"{info['postc']:+.1f}%" if info.get("postc") else None)

        # Trials
        trials = get_trials(cat["company"])
        if trials:
            st.caption(f"**{len(trials)} trial attivi su ClinicalTrials.gov:**")
            for t in trials:
                ep = ep_it(t["endpoint"])
                st.caption(f"- {t['phase']} | {t['conditions']} | {t['enrollment'] or '?'} paz. | Endpoint: **{ep}** | [{t['nct']}](https://clinicaltrials.gov/study/{t['nct']})")


# === VERDETTI FDA ===
pdufa_active = [c for c in pdufa_items if days_to(c["date"]) >= -5]
pdufa_active.sort(key=lambda c: days_to(c["date"]))

if pdufa_active:
    st.subheader("Verdetti FDA")
    for cat in pdufa_active:
        render_compact_card(cat)
    st.divider()

# === DATI TRIAL ATTESI ===
data_active = [c for c in data_items if days_to(c["date"]) >= 0]
data_active.sort(key=lambda c: days_to(c["date"]))

if data_active:
    st.subheader("Dati trial attesi")
    for cat in data_active:
        render_compact_card(cat)
    st.divider()

# === DEPOSITI / ARRUOLAMENTI ===
filing_active = [c for c in filing_items if days_to(c["date"]) >= 0]
filing_active.sort(key=lambda c: days_to(c["date"]))

if filing_active:
    st.subheader("Depositi e arruolamenti")
    for cat in filing_active:
        render_compact_card(cat)
    st.divider()

# === STORICO ===
with st.expander("Storico verdetti recenti"):
    for s in STORICO:
        icon = "OK" if s["esito"]=="OK" else "NO" if s["esito"]=="NO" else "RINV"
        st.caption(f"**{s['data']}** {s['ticker']} — {s['farmaco']} — **{icon}** {s['move']} — {s['nota']}")

with st.expander("Legenda"):
    st.write("PDUFA = FDA dice SI/NO | PH3_DATA = risultati Phase 3 | PH2_DATA = risultati Phase 2")
    st.write("BLA_FILING = deposito domanda approvazione | Vol/Media = volume/media 1 mese")
    st.write("Pre-Market 4-9:30 ET | After-Hours 16-20 ET | Short = scommesse contro")

st.caption(f"v15 | {DATA_AGG} | Educativa - non consulenza finanziaria | fda.gov")
