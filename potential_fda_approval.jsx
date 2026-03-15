import { useState, useEffect } from "react";

const CATALYSTS = [
  {
    ticker: "ALDX",
    company: "Aldeyra Therapeutics",
    drug: "Reproxalap",
    what: "Collirio per occhio secco",
    pdufa: "2026-03-16",
    reviewType: "Standard",
    tags: ["Fast Track", "🏷️ Etichetta in corso"],
    labelingActive: true,
    crl: 2,
    index: 44,
    risk: "medio-alto",
    keyFact: "La FDA sta già scrivendo il foglietto illustrativo — segnale positivo. Ma è la 3ª richiesta dopo 2 bocciature.",
    proSignals: [
      "FDA ha condiviso bozza etichetta (dic. 2025)",
      "Nessun problema di sicurezza o produzione identificato",
      "AbbVie pronta a pagare $100M se approvato",
      "Phase 3 chamber trial: endpoint primario raggiunto (P=0.002)",
    ],
    contraSignals: [
      "2 bocciature precedenti (CRL nov. 2023 e apr. 2025)",
      "Field trial ha MANCATO l'endpoint primario",
      "FDA ha chiesto lo stesso trial 2 volte → incertezza interna",
    ],
    news: [
      { src: "Fierce Biotech", date: "16 dic. 2025", text: "Il CEO ha spiegato che la FDA ha cambiato idea sul field trial: prima aveva detto di non includerlo, poi lo ha richiesto." },
      { src: "Ophthalmology Times", date: "12 mar. 2026", text: "Le due precedenti bocciature citavano problemi di efficacia, non di sicurezza. Nessun nuovo problema identificato nel meeting di dicembre." },
      { src: "Seeking Alpha", date: "30 dic. 2025", text: "La valutazione attuale ($259M) sembra bassa rispetto al potenziale del mercato DED, ma il rischio di un 3° rifiuto resta concreto." },
    ],
  },
  {
    ticker: "RYTM",
    company: "Rhythm Pharmaceuticals",
    drug: "Setmelanotide (Imcivree)",
    what: "Espansione: obesità ipotalamica acquisita",
    pdufa: "2026-03-20",
    reviewType: "Priority Review",
    tags: ["Orphan Drug", "🚀 Corsia preferenziale", "Farmaco già approvato"],
    labelingActive: false,
    crl: 0,
    index: 62,
    risk: "basso",
    keyFact: "Imcivree esiste già ed è venduto. Questa è solo un'espansione a nuovi pazienti. Dati clinici eccellenti.",
    proSignals: [
      "Farmaco GIÀ APPROVATO e in commercio (ricavi $57M nel Q4 2025)",
      "Phase 3 TRANSCEND: -18.8% BMI vs placebo (p<0.0001, N=142)",
      "Priority Review (corsia preferenziale FDA)",
      "Nessuna bocciatura precedente",
      "Dati giapponesi confermano risultati (mar. 2026)",
    ],
    contraSignals: [
      "PDUFA esteso da dic. 2025 a mar. 2026 (FDA ha chiesto analisi extra)",
      "Obesità ipotalamica è un mercato più piccolo di BBS/POMC",
    ],
    news: [
      { src: "Globe Newswire", date: "1 mar. 2026", text: "Nuovi dati positivi dal trial: i 12 pazienti giapponesi confermano riduzione BMI -16.4% e miglioramento della fame." },
      { src: "Rhythm IR", date: "26 feb. 2026", text: "Ricavi 2025 a $197M (+42% anno su anno). $57M solo nell'ultimo trimestre. Azienda in crescita solida." },
      { src: "FDA", date: "7 nov. 2025", text: "La FDA ha esteso il PDUFA dopo aver richiesto analisi di sensibilità aggiuntive sui dati di efficacia. Nessun problema di sicurezza." },
    ],
  },
  {
    ticker: "RCKT",
    company: "Rocket Pharmaceuticals",
    drug: "Kresladi",
    what: "Terapia genica per LAD-I (malattia rara, fatale nei bambini)",
    pdufa: "2026-03-28",
    reviewType: "Standard",
    tags: ["Orphan Drug", "Breakthrough Therapy"],
    labelingActive: false,
    crl: 1,
    index: 52,
    risk: "medio",
    keyFact: "Terapia genica per una malattia che uccide i bambini. 100% sopravvivenza nel trial. Ma è una ri-sottomissione dopo un rifiuto.",
    proSignals: [
      "100% sopravvivenza a 1+ anno nel trial Phase 1/2",
      "Tutti gli endpoint primari e secondari raggiunti",
      "Breakthrough Therapy + Orphan Drug designation",
      "Malattia senza alternative terapeutiche (unmet need altissimo)",
    ],
    contraSignals: [
      "1 bocciatura precedente (CRL) — motivo non completamente pubblico",
      "Terapia genica: produzione complessa, rischi di CMC",
      "Mercato ultra-piccolo (malattia ultra-rara)",
    ],
    news: [
      { src: "CGTLive", date: "14 ott. 2025", text: "La FDA ha accettato la ri-sottomissione del BLA. Il trial ha mostrato riduzione delle infezioni e miglioramento delle lesioni cutanee." },
      { src: "Rocket IR", date: "14 ott. 2025", text: "LAD-I è quasi sempre fatale nell'infanzia senza trapianto di midollo. Kresladi potrebbe essere l'unica alternativa." },
      { src: "BioMed Nexus", date: "gen. 2026", text: "Il primo CRL non era legato a efficacia o sicurezza. La ri-sottomissione ha affrontato le carenze identificate dalla FDA." },
    ],
  },
];

const daysTo = (dateStr) => {
  const d = new Date(dateStr + "T00:00:00");
  const now = new Date();
  return Math.ceil((d - now) / 86400000);
};

const riskColor = { basso: "#22c55e", medio: "#f59e0b", "medio-alto": "#ef4444", alto: "#dc2626" };
const riskEmoji = { basso: "🟢", medio: "🟡", "medio-alto": "🔴", alto: "🔴" };

function CountdownPill({ days }) {
  const urgent = days <= 1;
  const close = days <= 5;
  return (
    <div style={{
      background: urgent ? "#dc2626" : close ? "#f59e0b" : "#3b82f6",
      color: "#fff",
      borderRadius: 24,
      padding: "6px 16px",
      fontSize: 13,
      fontWeight: 800,
      letterSpacing: 0.5,
      display: "inline-flex",
      alignItems: "center",
      gap: 6,
      animation: urgent ? "pulse 1.5s infinite" : "none",
    }}>
      {urgent ? "🔔" : close ? "⏰" : "📅"}
      {days <= 0 ? "OGGI" : days === 1 ? "DOMANI" : `${days} GIORNI`}
    </div>
  );
}

function IndexBar({ value }) {
  const pct = (value / 99) * 100;
  const color = value >= 75 ? "#22c55e" : value >= 55 ? "#f59e0b" : value >= 35 ? "#3b82f6" : "#ef4444";
  return (
    <div style={{ marginTop: 6 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#94a3b8", marginBottom: 3 }}>
        <span>Indice di Fiducia</span>
        <span style={{ color, fontWeight: 700 }}>{value}/99</span>
      </div>
      <div style={{ background: "#1e293b", borderRadius: 6, height: 8, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: `linear-gradient(90deg, ${color}88, ${color})`, borderRadius: 6, transition: "width 0.8s ease" }} />
      </div>
      <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>
        Non è una probabilità. Serve per confrontare.
      </div>
    </div>
  );
}

function Tag({ children, color = "#334155" }) {
  return (
    <span style={{
      background: color,
      color: "#e2e8f0",
      padding: "2px 10px",
      borderRadius: 12,
      fontSize: 11,
      fontWeight: 600,
      display: "inline-block",
      margin: "2px 4px 2px 0",
    }}>{children}</span>
  );
}

function CatalystCard({ c }) {
  const [expanded, setExpanded] = useState(false);
  const days = daysTo(c.pdufa);
  const urgent = days <= 3;

  return (
    <div style={{
      background: urgent
        ? "linear-gradient(135deg, #1e1b2e, #2d1a1a)"
        : "linear-gradient(135deg, #0f172a, #1e293b)",
      border: urgent ? "1px solid #ef444466" : "1px solid #334155",
      borderRadius: 16,
      padding: 20,
      marginBottom: 16,
      position: "relative",
      overflow: "hidden",
    }}>
      {/* Glow effect for urgent */}
      {urgent && <div style={{ position: "absolute", top: -40, right: -40, width: 120, height: 120, background: "radial-gradient(circle, #ef444422, transparent)", borderRadius: "50%" }} />}

      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
        <div>
          <div style={{ fontSize: 20, fontWeight: 800, color: "#f8fafc", letterSpacing: -0.5 }}>
            {c.ticker}
            <span style={{ fontSize: 13, fontWeight: 400, color: "#94a3b8", marginLeft: 8 }}>{c.company}</span>
          </div>
          <div style={{ fontSize: 14, color: "#cbd5e1", marginTop: 2 }}>
            💊 {c.drug} — {c.what}
          </div>
        </div>
        <CountdownPill days={days} />
      </div>

      {/* Key fact */}
      <div style={{
        background: "#0f172a",
        border: "1px solid #1e293b",
        borderRadius: 10,
        padding: "10px 14px",
        fontSize: 13,
        color: "#e2e8f0",
        lineHeight: 1.5,
        marginBottom: 12,
      }}>
        {c.keyFact}
      </div>

      {/* Tags row */}
      <div style={{ marginBottom: 12 }}>
        {c.tags.map((t, i) => (
          <Tag key={i} color={t.includes("🏷️") ? "#166534" : t.includes("🚀") ? "#1d4ed8" : "#334155"}>{t}</Tag>
        ))}
        {c.crl > 0 && <Tag color="#991b1b">❌ {c.crl} bocciatur{c.crl > 1 ? "e" : "a"}</Tag>}
        <Tag color={riskColor[c.risk] + "33"}>
          {riskEmoji[c.risk]} Rischio {c.risk}
        </Tag>
      </div>

      {/* Index bar */}
      <IndexBar value={c.index} />

      {/* Labeling alert */}
      {c.labelingActive && (
        <div style={{
          background: "linear-gradient(90deg, #166534, #15803d)",
          borderRadius: 8,
          padding: "8px 12px",
          marginTop: 12,
          fontSize: 12,
          color: "#bbf7d0",
          fontWeight: 600,
        }}>
          🏷️ LABELING IN CORSO — La FDA sta scrivendo il foglietto illustrativo.
          Stanno pensando a COME venderlo, non SE.
        </div>
      )}

      {/* Expand button */}
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          background: "none",
          border: "1px solid #334155",
          borderRadius: 8,
          color: "#94a3b8",
          padding: "8px 16px",
          fontSize: 12,
          fontWeight: 600,
          cursor: "pointer",
          marginTop: 12,
          width: "100%",
          transition: "all 0.2s",
        }}
        onMouseEnter={(e) => { e.target.style.borderColor = "#60a5fa"; e.target.style.color = "#60a5fa"; }}
        onMouseLeave={(e) => { e.target.style.borderColor = "#334155"; e.target.style.color = "#94a3b8"; }}
      >
        {expanded ? "▲ Chiudi dettagli" : "▼ Segnali + Notizie da fonti ufficiali"}
      </button>

      {/* Expanded section */}
      {expanded && (
        <div style={{ marginTop: 14 }}>
          {/* Pro/Contra */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 14 }}>
            <div style={{ background: "#0f2918", borderRadius: 10, padding: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#4ade80", marginBottom: 6 }}>✅ SEGNALI POSITIVI</div>
              {c.proSignals.map((s, i) => (
                <div key={i} style={{ fontSize: 11, color: "#a7f3d0", lineHeight: 1.5, marginBottom: 4 }}>• {s}</div>
              ))}
            </div>
            <div style={{ background: "#1c0f0f", borderRadius: 10, padding: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#f87171", marginBottom: 6 }}>⚠️ RISCHI</div>
              {c.contraSignals.map((s, i) => (
                <div key={i} style={{ fontSize: 11, color: "#fecaca", lineHeight: 1.5, marginBottom: 4 }}>• {s}</div>
              ))}
            </div>
          </div>

          {/* News */}
          <div style={{ fontSize: 12, fontWeight: 700, color: "#94a3b8", marginBottom: 6 }}>📰 DALLE FONTI UFFICIALI</div>
          {c.news.map((n, i) => (
            <div key={i} style={{
              background: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: 8,
              padding: "8px 12px",
              marginBottom: 6,
              fontSize: 11,
              lineHeight: 1.5,
            }}>
              <span style={{ color: "#60a5fa", fontWeight: 700 }}>{n.src}</span>
              <span style={{ color: "#475569", marginLeft: 6 }}>{n.date}</span>
              <div style={{ color: "#cbd5e1", marginTop: 2 }}>{n.text}</div>
            </div>
          ))}

          {/* PDUFA details */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: 8,
            marginTop: 10,
          }}>
            <div style={{ background: "#1e293b", borderRadius: 8, padding: 10, textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "#64748b" }}>PDUFA</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#f8fafc" }}>{c.pdufa}</div>
            </div>
            <div style={{ background: "#1e293b", borderRadius: 8, padding: 10, textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "#64748b" }}>REVIEW</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#f8fafc" }}>{c.reviewType}</div>
            </div>
            <div style={{ background: "#1e293b", borderRadius: 8, padding: 10, textAlign: "center" }}>
              <div style={{ fontSize: 10, color: "#64748b" }}>DOMANDA</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: "#f8fafc" }}>{c.crl > 0 ? "Ri-sottomissione" : "Prima richiesta"}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Glossary() {
  const [open, setOpen] = useState(false);
  const terms = [
    ["PDUFA", "Giorno del Verdetto", "Quando la FDA dice SÌ o NO."],
    ["Labeling", "Stanno scrivendo il foglietto!", "Se la FDA discute l'etichetta, stanno pensando a COME venderlo."],
    ["CRL", "Bocciato con appunti", "La FDA dice NO ma spiega cosa correggere."],
    ["Priority Review", "Corsia preferenziale", "Esame in 6 mesi anziché 10."],
    ["Orphan Drug", "Farmaco per malattia rara", "7 anni di esclusiva + vantaggi fiscali."],
    ["Breakthrough", "Rivoluzionario", "La FDA riconosce che è molto meglio di tutto ciò che esiste."],
    ["Indice", "Il nostro termometro", "Punteggio 0-99 per CONFRONTARE, non per prevedere."],
  ];
  return (
    <div style={{ marginTop: 16 }}>
      <button onClick={() => setOpen(!open)} style={{
        background: "none", border: "1px solid #334155", borderRadius: 10,
        color: "#94a3b8", padding: "10px 16px", fontSize: 13, fontWeight: 600,
        cursor: "pointer", width: "100%",
      }}>
        {open ? "▲" : "📖"} Dizionario "da bar" — {open ? "chiudi" : "capire tutto in 30 secondi"}
      </button>
      {open && (
        <div style={{ marginTop: 8 }}>
          {terms.map(([term, bar, desc], i) => (
            <div key={i} style={{
              background: "#0f172a", borderLeft: "3px solid #6366f1",
              borderRadius: "0 8px 8px 0", padding: "8px 12px", marginBottom: 4,
              fontSize: 12, lineHeight: 1.5,
            }}>
              <span style={{ color: "#a5b4fc", fontWeight: 700 }}>{bar}</span>
              <span style={{ color: "#475569" }}> ({term})</span>
              <span style={{ color: "#94a3b8" }}> — {desc}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const sorted = [...CATALYSTS].sort((a, b) => daysTo(a.pdufa) - daysTo(b.pdufa));
  const today = new Date().toLocaleDateString("it-IT", { day: "numeric", month: "long", year: "numeric" });

  return (
    <div style={{
      minHeight: "100vh",
      background: "#020617",
      fontFamily: "'Segoe UI', -apple-system, sans-serif",
      color: "#f8fafc",
      padding: "20px 16px",
      maxWidth: 640,
      margin: "0 auto",
    }}>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        * { box-sizing: border-box; }
      `}</style>

      {/* Header */}
      <div style={{ textAlign: "center", marginBottom: 24 }}>
        <div style={{ fontSize: 28, fontWeight: 900, letterSpacing: -1, lineHeight: 1.1 }}>
          <span style={{ background: "linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Potential FDA Approval
          </span>
        </div>
        <div style={{ fontSize: 13, color: "#64748b", marginTop: 4 }}>
          Small & Mid Cap Biotech — Solo nel range 200M-2B USD
        </div>
        <div style={{ fontSize: 11, color: "#475569", marginTop: 2 }}>
          Aggiornato: {today} · Dati notizie: comunicati aziendali + SEC filings
        </div>
      </div>

      {/* Summary strip */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr 1fr",
        gap: 8,
        marginBottom: 20,
      }}>
        <div style={{ background: "#1e293b", borderRadius: 10, padding: "10px 8px", textAlign: "center" }}>
          <div style={{ fontSize: 22, fontWeight: 800 }}>{sorted.length}</div>
          <div style={{ fontSize: 10, color: "#64748b" }}>CATALIZZATORI</div>
        </div>
        <div style={{ background: "#1e293b", borderRadius: 10, padding: "10px 8px", textAlign: "center" }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: "#22c55e" }}>
            {sorted.filter(c => c.labelingActive).length}
          </div>
          <div style={{ fontSize: 10, color: "#64748b" }}>CON LABELING</div>
        </div>
        <div style={{ background: "#1e293b", borderRadius: 10, padding: "10px 8px", textAlign: "center" }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: "#f59e0b" }}>
            {sorted.filter(c => daysTo(c.pdufa) <= 7).length}
          </div>
          <div style={{ fontSize: 10, color: "#64748b" }}>ENTRO 7 GG</div>
        </div>
      </div>

      {/* No AdComm notice */}
      <div style={{
        background: "#1c1917",
        border: "1px solid #78350f",
        borderRadius: 10,
        padding: "10px 14px",
        marginBottom: 16,
        fontSize: 11,
        color: "#fbbf24",
        lineHeight: 1.5,
      }}>
        👨‍⚖️ La FDA non convoca la Giuria Esperti (AdComm) da luglio 2025.
        Nessuno di questi catalizzatori ha un voto di esperti.
        Prossimo AdComm: 30 aprile 2026 (AstraZeneca).
      </div>

      {/* Cards */}
      {sorted.map((c) => (
        <div key={c.ticker} style={{ animation: "fadeIn 0.4s ease" }}>
          <CatalystCard c={c} />
        </div>
      ))}

      {/* Glossary */}
      <Glossary />

      {/* Index explanation */}
      <div style={{
        marginTop: 16,
        background: "#0f172a",
        border: "1px dashed #334155",
        borderRadius: 10,
        padding: 14,
        fontSize: 11,
        color: "#64748b",
        lineHeight: 1.6,
      }}>
        <strong style={{ color: "#94a3b8" }}>Come funziona l'Indice di Fiducia</strong><br />
        Base 50 · AdComm ≥90%: +25 · Labeling: +15 · Priority Review: +5 ·
        Breakthrough: +5 · Fast Track: +3 · Orphan Drug: +2 · Farmaco già approvato: +5 ·
        <strong style={{ color: "#f87171" }}> Ogni bocciatura (CRL): -12</strong><br />
        ⚠️ Non è una probabilità. Serve solo per confrontare.
      </div>

      {/* Footer */}
      <div style={{
        marginTop: 24,
        textAlign: "center",
        fontSize: 10,
        color: "#475569",
        lineHeight: 1.6,
        paddingBottom: 20,
      }}>
        🧬 Potential FDA Approval v5.0<br />
        Fonti: comunicati stampa aziendali, SEC filings, Fierce Biotech, CGTLive<br />
        ⚠️ App educativa — non è consulenza finanziaria.<br />
        Verifica sempre su fda.gov. Investi solo ciò che puoi perdere.
      </div>
    </div>
  );
}
