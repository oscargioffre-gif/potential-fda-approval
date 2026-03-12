# 🧬 Potential FDA Approval v2.0

**App gratuita per cacciatori di catalizzatori FDA — Small & Mid Cap Biotech**

---

## 🚀 Come Mettere Online (tutto dal browser, zero terminale)

### Passo 1 — Crea un repository su GitHub

1. Vai su [github.com/new](https://github.com/new) (crea un account gratis se non ce l'hai)
2. Nome del repo: `potential-fda-approval`
3. Spunta "Add a README file"
4. Clicca **Create repository**

### Passo 2 — Carica i file

1. Nella pagina del repo clicca **Add file** → **Upload files**
2. Trascina dentro `potential_fda_approval.py` e `requirements.txt`
3. Clicca **Commit changes**

### Passo 3 — Collega Streamlit Cloud

1. Vai su [share.streamlit.io](https://share.streamlit.io)
2. Accedi con il tuo account GitHub
3. Clicca **New app**
4. Seleziona il repo `potential-fda-approval`
5. Nel campo "Main file path" scrivi: `potential_fda_approval.py`
6. Clicca **Deploy**

In 2 minuti l'app è online con un link tipo:
`tuonome-potential-fda-approval.streamlit.app`

---

## 📋 Come Aggiornare i Dati Ogni Mese

1. **Chiedi all'IA** il Super-Prompt per ottenere i catalizzatori aggiornati
2. **Su GitHub**: clicca su `potential_fda_approval.py` → icona matita ✏️
3. **Sostituisci** la sezione `data = [...]` con i nuovi dati
4. **Clicca** "Commit changes" — Streamlit si aggiorna da solo!

Struttura di ogni catalizzatore:

```python
{
    "ticker": "ABCD",              # Simbolo di borsa
    "azienda": "Nome Azienda",
    "farmaco": "NomeFarmaco",
    "indicazione": "Per cosa serve",
    "pdufa_date": "2026-04-15",    # Data del Verdetto FDA
    "adcomm_voto": 95,             # % voti favorevoli (o None)
    "adcomm_data": "2026-02-20",   # Data del voto (o None)
    "tipo_review": "Priority Review",  # oppure "Standard Review"
    "designazioni": ["Breakthrough Therapy", "Fast Track"],
    "labeling_discussion": True,   # True = segnale positivo
    "fase": "NDA",                 # NDA o BLA
    "note": "Eventuali note",
    "rischio": "basso",            # basso / medio / medio-alto / alto
}
```

---

## ⚠️ Disclaimer

Questa app è solo a scopo **educativo e informativo**.
Non costituisce consulenza finanziaria. Verifica sempre i dati
su [fda.gov](https://www.fda.gov) prima di qualsiasi decisione.
