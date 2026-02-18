# WAI Backend - Whale Activity & Intent Index

Wissenschaftliche On-Chain-Analyse für Bitcoin Whale-Aktivität

## Übersicht

Das WAI Backend ist ein hochentwickeltes Analyse-System, das zwei komplementäre Indizes berechnet:

- **WAI (Whale Activity Index):** Misst die Aktivität von Bitcoin-Whales
- **WII (Whale Intent Index):** Analysiert die Absichten durch Exchange-Flows

**Differenzierungsmerkmal:** Wissenschaftliche Auswertung mit Lead-Lag-Analyse, Regime Detection und Conditional Volatility.

## Features

✅ **Whale Activity Index (WAI v2)**
- Volatilitätsabhängige dynamische Gewichtung
- Historisch adaptive Skalierung (180-Tage Percentile)
- EMA-Smoothing für Stabilität

✅ **Whale Intent Index (WII)**
- Exchange-Flow-Analyse (Inflow/Outflow)
- Akkumulations- vs. Distributions-Signale
- Leading Indicator (1-3 Tage voraus)

✅ **Wissenschaftliche Analysen**
- Lead-Lag-Korrelationen
- Regime Detection (K-Means Clustering)
- Conditional Volatility
- Kombinierte Auswertungen

## Schnellstart

### Installation

```bash
# Virtual Environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Dependencies
pip install -r requirements.txt

# Server starten
python main.py
```

Server läuft auf: http://localhost:8000

### API-Dokumentation

Interaktive Docs: http://localhost:8000/docs

## API-Endpunkte

### WAI & WII (kombiniert)

```bash
# Aktuellster WAI & WII-Wert
GET /api/wai/latest

# WAI & WII Historie (alle Daten inklusive)
GET /api/wai/history?start_date=2026-01-01&limit=30

# Statistiken (WAI & WII)
GET /api/wai/statistics
```

**Response enthält beide Indizes:**
```json
{
  "date": "2026-01-19",
  "wai": 67,
  "wii": 45,
  "wii_signal": "neutral",
  "tx_count": 10,
  "volume": 3320.58,
  "exchange_inflow": 514.84,
  "exchange_outflow": 262.97,
  "exchange_netflow": -251.87
}
```

### Wissenschaftliche Analysen

```bash
# Lead-Lag-Analyse, Regime Detection, Conditional Volatility
python analysis/wii_analysis.py
```

Das Skript analysiert:
- **Lead-Lag:** Folgt Preis auf Whale-Flows?
- **Regime Detection:** Marktphasen (Bull/Distribution/Stealth/Capitulation)
- **Conditional Volatility:** Flow-abhängige Volatilität

Ergebnisse optional als JSON speicherbar.

### WAI-Extras (Erweiterte Signale)

```bash
# Whale Momentum - Beschleunigung der Aktivität
GET /api/wai/momentum

# Confidence Score - Signalqualität
GET /api/wai/confidence

# Historical Backtest - WII-Signal Performance
GET /api/wai/backtest?signal=wii_accumulation&horizon=7
```

#### Whale Momentum

Misst die **Beschleunigung** der Whale-Aktivität:

```
Momentum = WAI_heute - WAI_7d_durchschnitt
```

**Response:**
```json
{
  "date": "2026-02-18",
  "whale_momentum": 12.5,
  "momentum_signal": "acceleration",
  "wai": 67.0,
  "wai_7d_avg": 54.5,
  "interpretation": "Whale-Aktivität nimmt zu - Momentum positiv"
}
```

**Signale:**
- `strong_acceleration` (>20): Starke Beschleunigung
- `acceleration` (10-20): Beschleunigung
- `neutral` (-10 bis +10): Stabil
- `deceleration` (-20 bis -10): Verlangsamung
- `strong_deceleration` (<-20): Starke Verlangsamung

#### Confidence Score

Bewertet die **Verlässlichkeit** des aktuellen Signals:

```
Confidence = (TX_Count × 0.4 + Exchange_Activity × 0.3 + Stability × 0.3) × 100
```

**Response:**
```json
{
  "date": "2026-02-18",
  "confidence_score": 72.5,
  "confidence_level": "high",
  "components": {
    "tx_count_score": 0.75,
    "exchange_activity_score": 0.68,
    "stability_score": 0.74
  },
  "interpretation": "Hohe Confidence - Signal ist verlässlich"
}
```

**Levels:**
- `very_high` (>80): Sehr verlässlich
- `high` (60-80): Verlässlich
- `moderate` (40-60): Mit Vorsicht
- `low` (<40): Schwaches Signal

#### Historical Backtest

Testet **WII-Signale** auf historische Performance:

**Verfügbare Signale:**
- `wii_accumulation`: WII > 70 (Bullish)
- `wii_strong_accumulation`: WII > 85 (Sehr Bullish)
- `wii_selling`: WII < 30 (Bearish)
- `wii_strong_selling`: WII < 15 (Sehr Bearish)

**Parameter:**
- `signal`: WII-Signal Typ (siehe oben)
- `horizon`: Forward-Return Horizont (1-30 Tage, default: 3)

**Response:**
```json
{
  "signal_type": "wii_accumulation",
  "signal_direction": "bullish (Long)",
  "horizon_days": 7,
  "total_signals": 45,
  "performance": {
    "win_rate": 62.22,
    "avg_return": 2.34,
    "median_return": 1.98,
    "max_drawdown": -8.45,
    "sharpe_ratio": 1.42
  },
  "prediction_stats": {
    "correct_predictions": 28,
    "incorrect_predictions": 17,
    "avg_return_when_correct": 4.12,
    "avg_return_when_incorrect": -2.45,
    "profit_factor": 2.35,
    "win_condition": "Preis stieg (positiv)"
  },
  "interpretation": {
    "signal_direction": "bullish (Long)",
    "win_rate_assessment": "Sehr gut - Signal zeigt starke Vorhersagekraft",
    "return_assessment": "Gut - Positive durchschnittliche Returns",
    "sharpe_assessment": "Gut - Solides Risk/Reward-Verhältnis",
    "overall_assessment": "✅ Bullish Signal zeigt starke historische Performance",
    "recommendation": "Signal zeigt robuste Vorhersagekraft"
  }
}
```

**Wichtig:** 
- Bei **bullish** Signalen: Positive Returns = Win
- Bei **bearish** Signalen: **Negative Returns = Win** (Short Position simuliert)

## Dokumentation

### Methodologie

- **[WII_DOCUMENTATION.md](WII_DOCUMENTATION.md)** - Whale Intent Index Details
- **[SCIENTIFIC_ANALYSIS.md](SCIENTIFIC_ANALYSIS.md)** - Phase 6: Wissenschaftliche Auswertung
- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)** - Technische Dokumentation

### Analysen

- **[analysis/whale_intent_index.md](analysis/whale_intent_index.md)** - WII Methodologie & Validierung
- **[analysis/wai_vs_wii_comparison.md](analysis/wai_vs_wii_comparison.md)** - WAI vs. WII Vergleich
- **[analysis/wai_comparison_evaluation.md](analysis/wai_comparison_evaluation.md)** - WAI v1 vs. v2

## WAI Methodik (v2)

Der WAI v2 verbessert die ursprüngliche Methodik durch dynamische Anpassung an Marktbedingungen:

**1. Adaptive Normalisierung**
```
Normalisierte_Transaktionen = Tagestransaktionen / Median_50(Transaktionen)
Normalisiertes_Volumen = Tagesvolumen / Median_50(Volumen)
```

Die Basislinie verwendet einen 50-Tage rollierenden Median für maximale Robustheit gegen Ausreißer.

**2. Volatilitätsabhängige Gewichtung**

Anstatt fixer 50/50-Gewichte werden die Komponenten dynamisch gewichtet:

```
Volatilitäts_Perzentil = PercentileRank(std(Normalisiertes_Volumen), window=50)
Gewicht_Volumen = Volatilitäts_Perzentil
Gewicht_Transaktionen = 1 - Volatilitäts_Perzentil

WAI_roh = Gewicht_Transaktionen × Normalisierte_Transaktionen + Gewicht_Volumen × Normalisiertes_Volumen
```

**Logik:** 
- Hohe Volumen-Volatilität → Transaktionsanzahl wird stärker gewichtet
- Stabile Volumen-Daten → Volumen wird stärker gewichtet

**3. Historisch adaptive Skalierung**

```
WAI_Perzentil = PercentileRank(WAI_roh, window=180)
WAI_Index = round(WAI_Perzentil × 100)
```

- **Wertebereich**: [0, 100]
- Zeigt die relative Position im 180-Tage-Fenster
- WAI = 50 bedeutet Median-Aktivität
- WAI > 80 bedeutet außergewöhnlich hohe Aktivität

**4. EMA-Smoothing**

Nach der Skalierung wird der Index durch exponentielle Glättung über 7 Tage beruhigt:

```
WAI_final = EMA_7(WAI_scaled)
```

Reduziert tägliche Volatilität bei Erhalt der Trends.

## WII Methodik

Der **Whale Intent Index** analysiert Exchange-Flows:

```
1. Netflow Ratio = (Outflow - Inflow) / (Outflow + Inflow)
2. Normalisierung: [-1, 1] → [0, 1]
3. Percentile: WII = PercentileRank₁₈₀(normalized) × 100
4. Smoothing: EMA₇(WII)
```

**Interpretation:**
- WII < 30: Selling Pressure (Inflow zu Exchanges)
- WII 30-70: Neutral
- WII > 70: Accumulation (Outflow von Exchanges)

## Wissenschaftliche Analysen

### Lead-Lag-Analyse

Beantwortet: **"Folgt der Preis auf Whale-Flows?"**

- Zeitverzögerte Korrelationen (0-7+ Tage)
- Identifiziert: Ist Inflow bearish? Ist Outflow bullish?

### Regime Detection

K-Means Clustering identifiziert 4 Marktphasen:
1. Bull Market (WAI↑ + WII↑)
2. Distribution (WAI↑ + WII↓)
3. Stealth Accumulation (WAI↓ + WII↑)
4. Capitulation (WAI↓ + WII↓)

### Conditional Volatility

Untersucht Flow-abhängige Volatilität:
- Erhöhen hohe Inflows die Volatilität?
- Ist Verkaufsdruck volatiler als Akkumulation?

## Beispiel-Response

```json
{
  "date": "2026-01-19",
  "wai": 67,
  "wii": 45,
  "wii_signal": "neutral",
  "tx_count": 10,
  "volume": 3320.58,
  "exchange_inflow": 514.84,
  "exchange_outflow": 262.97,
  "exchange_netflow": -251.87,
  "netflow_ratio": -0.3238,
  "btc_close": 104500.23,
  "btc_return_1d": 0.0234
}
```

Alle Daten (WAI & WII) in einem Endpoint - einfach und übersichtlich!

## Technologie-Stack

- **FastAPI** - Moderne async Web-Framework
- **Pandas** - Datenanalyse
- **NumPy** - Numerische Berechnungen
- **scikit-learn** - Machine Learning (Regime Detection)
- **httpx** - Async HTTP-Client

## Deployment

### Docker

```bash
docker build -t wai-backend .
docker run -p 8000:8000 wai-backend
```

### Umgebungsvariablen

Erstelle `.env`:
```env
HOST=0.0.0.0
PORT=8000
DEBUG=False
MEDIAN_WINDOW=50
WAI_SMOOTHING_WINDOW=7
WII_SMOOTHING_WINDOW=7
```

## Projektstruktur

```
wai-backend/
├── main.py                    # FastAPI App & API-Endpoints
├── wai_service.py            # WAI/WII Berechnung
├── config.py                 # Konfiguration
├── requirements.txt          # Dependencies
├── README.md                 # Diese Datei
├── analysis/                 # Analysen & Dokumentation
│   ├── wii_analysis.py       # WII Wissenschaftliche Analyse (Skript)
│   ├── wai_index_validation.py  # WAI Validierung
│   ├── whale_intent_index.md
│   ├── wai_vs_wii_comparison.md
│   └── wai_comparison_evaluation.md
└── data/                     # Historische Daten
```

## Lizenz

MIT License

## Kontakt & Support

Bei Fragen zur Methodologie siehe Dokumentation im `/analysis` Ordner.

---

**Differenzierungsmerkmal:** Dieses System kombiniert nicht nur Indikatoren, sondern liefert wissenschaftlich validierte, quantifizierbare Erkenntnisse über Whale-Verhalten und deren Marktauswirkungen.

# Mit Docker Compose
docker-compose up -d

# Oder nur Docker
docker build -t wai-backend .
docker run -p 8000:8000 wai-backend
```

**Docker-Befehle:**
```bash
# Logs anzeigen
docker-compose logs -f

# Status prüfen
docker-compose ps

# Stoppen
docker-compose down

# Neu bauen & starten
docker-compose up -d --build
```

Der Server läuft dann auf: `http://localhost:8000`

## API Endpoints

### Swagger Dokumentation
- **GET** `/docs` - Interaktive API-Dokumentation

### Health Check
- **GET** `/health` - Server Status

### WAI Endpoints

#### Aktuellster WAI-Wert
```
GET /api/wai/latest
```

Liefert den neuesten WAI-Wert mit beiden Versionen:
- `wai_index`: WAI v2 (volatilitätsgewichtet)
- `wai_index_v1`: WAI v1 (50/50-Gewichtung)
- Alle Komponenten und Gewichte

#### WAI-Historie
```
GET /api/wai/history?start_date=2024-01-01&end_date=2024-12-31&limit=100
```

Parameter:
- `start_date` (optional): Startdatum (YYYY-MM-DD)
- `end_date` (optional): Enddatum (YYYY-MM-DD)
- `limit` (optional): Max. Anzahl Ergebnisse (1-1000)

Liefert historische Daten mit v2 und v1 zum Vergleich.

#### Statistiken
```
GET /api/wai/statistics
```

#### Formel-Informationen
```
GET /api/wai/formula
```

## Konfiguration

Umgebungsvariablen können in `.env` Datei gesetzt werden:

```bash
# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Data Source
DATA_URL=https://raw.githubusercontent.com/Whale-Activity-Analysis/wai-collector/refs/heads/main/data/daily_metrics.json

# WAI Calculation Parameters
MEDIAN_WINDOW=30
WAI_MIN=0
WAI_MAX=100
```

## Technologie-Stack

- **FastAPI**: Modernes Python Web Framework
- **Pandas**: Datenanalyse und Berechnungen
- **NumPy**: Numerische Operationen
- **HTTPX**: Asynchrone HTTP-Requests
- **Uvicorn**: ASGI Server

## Entwicklung

### Auto-Reload aktivieren

Der Server startet standardmäßig im Development-Modus mit Auto-Reload. Bei Änderungen am Code wird der Server automatisch neu gestartet.

### Tests ausführen

```bash
pytest
```

## Features
- Whale Activity Score Endpunkte
- Historische Zeitserien (aus der Datenbank)
- Auth (später)
- Endpunkte für Collector-Uploads
- Validation, Caching, Logging
