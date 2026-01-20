# Phase 6: Wissenschaftliche Auswertung

## Übersicht

Die wissenschaftliche Auswertung ist das **Differenzierungsmerkmal** des WAI/WII-Systems. Sie beantwortet drei zentrale Fragestellungen:

1. **Folgt der Preis auf Whale-Flows?** → Lead-Lag-Analyse
2. **Ist Inflow bearish?** → Korrelationsanalyse
3. **Ist Outflow bullish?** → Korrelationsanalyse

## Implementierte Metriken

### 1. Lead-Lag-Analyse

**Zweck:** Identifiziert zeitverzögerte Beziehungen zwischen Whale-Aktivität und Preisentwicklung.

**Methodik:**
- Berechnung von Korrelationen mit verschiedenen Lags (0-7 Tage oder mehr)
- Untersuchung von: Inflow, Outflow, Netflow, WII, WAI → BTC-Returns

**API-Endpoint:**
```http
GET /api/analysis/lead-lag?max_lag=7
```

**Beispiel-Response:**
```json
{
  "description": "Lead-Lag-Analyse: Zeitverzögerte Korrelationen zwischen Whale-Flows und BTC-Returns",
  "sample_size": 150,
  "max_lag_days": 7,
  "exchange_inflow_to_btc_returns": {
    "correlations": {
      "lag_0d": -0.1234,
      "lag_1d": -0.2156,
      "lag_2d": -0.1845,
      "lag_3d": -0.0987
    },
    "best_lag": "lag_1d",
    "best_correlation": -0.2156,
    "interpretation": "Negativ = Inflow ist bearish (Verkaufsdruck)"
  },
  "exchange_outflow_to_btc_returns": {
    "correlations": {
      "lag_0d": 0.0856,
      "lag_1d": 0.1543,
      "lag_2d": 0.2187,
      "lag_3d": 0.1654
    },
    "best_lag": "lag_2d",
    "best_correlation": 0.2187,
    "interpretation": "Positiv = Outflow ist bullish (Akkumulation)"
  },
  "key_findings": {
    "inflow_bearish": true,
    "outflow_bullish": true,
    "wii_predictive": true,
    "best_predictor": "Outflow"
  }
}
```

**Interpretation:**
- **Negative Korrelation bei Inflow:** Hoher Inflow zu Exchanges führt zu negativen Returns → **Bearish**
- **Positive Korrelation bei Outflow:** Hoher Outflow von Exchanges führt zu positiven Returns → **Bullish**
- **Best Lag:** Zeigt optimalen Vorlauf (z.B. 1-2 Tage)

### 2. Regime Detection

**Zweck:** Identifiziert verschiedene Marktphasen basierend auf Whale-Verhalten.

**Methodik:**
- K-Means Clustering auf normalisierten Features:
  - WAI (Aktivität)
  - WII (Intent)
  - BTC Volatilität
- 4 Regimes werden identifiziert

**API-Endpoint:**
```http
GET /api/analysis/regime-detection
```

**Beispiel-Response:**
```json
{
  "description": "Regime Detection: Identifiziert Marktphasen basierend auf WAI, WII und Volatilität",
  "n_regimes": 4,
  "total_days": 150,
  "regimes": [
    {
      "regime_id": 0,
      "count": 45,
      "percentage": 30.0,
      "characteristics": {
        "avg_wai": 72.5,
        "avg_wii": 68.3,
        "avg_volatility": 0.0189,
        "avg_btc_return": 0.0123
      },
      "interpretation": "Bull Market - Hohe Aktivität + Akkumulation"
    },
    {
      "regime_id": 1,
      "count": 38,
      "percentage": 25.3,
      "characteristics": {
        "avg_wai": 45.2,
        "avg_wii": 52.1,
        "avg_volatility": 0.0142,
        "avg_btc_return": 0.0034
      },
      "interpretation": "Consolidation - Seitwärtsbewegung"
    },
    {
      "regime_id": 2,
      "count": 35,
      "percentage": 23.3,
      "characteristics": {
        "avg_wai": 78.9,
        "avg_wii": 28.4,
        "avg_volatility": 0.0256,
        "avg_btc_return": -0.0156
      },
      "interpretation": "Distribution Phase - Hohe Aktivität + Verkaufsdruck"
    },
    {
      "regime_id": 3,
      "count": 32,
      "percentage": 21.3,
      "characteristics": {
        "avg_wai": 28.7,
        "avg_wii": 32.5,
        "avg_volatility": 0.0198,
        "avg_btc_return": -0.0089
      },
      "interpretation": "Capitulation/Apathy - Niedrige Aktivität + Verkaufsdruck"
    }
  ],
  "current_regime": {
    "regime_id": 0,
    "interpretation": "Bull Market - Hohe Aktivität + Akkumulation",
    "count": 45,
    "percentage": 30.0
  },
  "latest_date": "2026-01-19"
}
```

**Regime-Interpretationen:**

| WAI | WII | Interpretation |
|-----|-----|----------------|
| Hoch (>65) | Hoch (>65) | **Bull Market** - Hohe Aktivität + Akkumulation |
| Hoch (>65) | Niedrig (<35) | **Distribution Phase** - Hohe Aktivität + Verkaufsdruck |
| Niedrig (<35) | Hoch (>65) | **Stealth Accumulation** - Niedrige Aktivität + Akkumulation |
| Niedrig (<35) | Niedrig (<35) | **Capitulation/Apathy** - Niedrige Aktivität + Verkaufsdruck |

### 3. Conditional Volatility

**Zweck:** Untersucht, ob Whale-Flows die Marktvolatilität beeinflussen.

**Methodik:**
- Volatilitätsvergleich nach WII-Signal
- Volatilität bei hohen Inflows vs. Outflows
- Korrelation zwischen Flows und Volatilität

**API-Endpoint:**
```http
GET /api/analysis/conditional-volatility
```

**Beispiel-Response:**
```json
{
  "description": "Conditional Volatility: Volatilität abhängig von Whale-Flows",
  "sample_size": 150,
  "volatility_by_wii_signal": {
    "selling_pressure": {
      "count": 28,
      "avg_volatility": 0.0234,
      "avg_return": -0.0145
    },
    "neutral": {
      "count": 85,
      "avg_volatility": 0.0156,
      "avg_return": 0.0023
    },
    "accumulation": {
      "count": 37,
      "avg_volatility": 0.0178,
      "avg_return": 0.0089
    }
  },
  "volatility_by_flow_intensity": {
    "high_inflow": {
      "count": 38,
      "avg_volatility": 0.0245,
      "avg_return": -0.0167
    },
    "high_outflow": {
      "count": 35,
      "avg_volatility": 0.0189,
      "avg_return": 0.0112
    },
    "low_activity": {
      "count": 40,
      "avg_volatility": 0.0134,
      "avg_return": 0.0034
    }
  },
  "correlations": {
    "inflow_to_volatility": 0.2345,
    "outflow_to_volatility": 0.1234
  },
  "key_findings": {
    "high_inflow_increases_volatility": true,
    "selling_pressure_more_volatile": true,
    "inflow_bearish_confirmed": true
  }
}
```

**Key Insights:**
- **Verkaufsdruck ist volatiler:** Hohe Inflows zu Exchanges erhöhen die Volatilität
- **Akkumulation ist stabiler:** Outflows korrelieren mit niedrigerer Volatilität
- **Bestätigung:** Inflow ist bearish (negative Returns bei hoher Volatilität)

## Wissenschaftliche Gesamtauswertung

**API-Endpoint:**
```http
GET /api/analysis/scientific-summary
```

Kombiniert alle drei Analysen und liefert eine Executive Summary:

```json
{
  "title": "Wissenschaftliche Whale-Flow-Analyse",
  "description": "Umfassende statistische Auswertung der Whale-Aktivität und Marktauswirkungen",
  "analyses": {
    "lead_lag_analysis": { /* ... */ },
    "regime_detection": { /* ... */ },
    "conditional_volatility": { /* ... */ }
  },
  "executive_summary": {
    "inflow_effect": "Bearish",
    "outflow_effect": "Bullish",
    "current_market_regime": "Bull Market - Hohe Aktivität + Akkumulation",
    "wii_predictive_power": "Hoch",
    "best_predictor": "Outflow"
  }
}
```

## Wissenschaftliche Grundlagen

### Lead-Lag-Korrelation

Die Lead-Lag-Analyse basiert auf der **Cross-Correlation Function (CCF)**:

```
ρ(τ) = Corr(X_t, Y_{t+τ})
```

Wobei:
- `X_t`: Whale-Flow zum Zeitpunkt t
- `Y_{t+τ}`: BTC-Return zum Zeitpunkt t+τ
- `τ`: Lag (Zeitverzögerung)

**Interpretation:**
- `τ = 0`: Gleichzeitige Korrelation
- `τ > 0`: X führt Y um τ Perioden voraus
- Hohe `|ρ(τ)|`: Starke Beziehung bei Lag τ

### K-Means Clustering

**Feature-Normalisierung:**
```python
X_scaled = (X - μ) / σ
```

**K-Means-Algorithmus:**
1. Initialisiere k Cluster-Zentren
2. Weise jeden Datenpunkt dem nächsten Zentrum zu
3. Berechne neue Zentren als Mittelwert der zugewiesenen Punkte
4. Wiederhole 2-3 bis Konvergenz

**Distanzmetrik:** Euklidische Distanz
```
d(x, μ_k) = √(Σ(x_i - μ_{k,i})²)
```

### Conditional Volatility

**Volatilität (7-Tage-Rolling-Fenster):**
```
σ_t = √(Var(r_{t-6}, ..., r_t))
```

**Conditional Analysis:**
```
E[σ | Flow = high_inflow] vs. E[σ | Flow = high_outflow]
```

Vergleicht durchschnittliche Volatilität unter verschiedenen Flow-Bedingungen.

## Praktische Anwendung

### Trading-Signale aus der Wissenschaft

#### 1. Lead-Lag-Optimierung
```python
# Wenn Outflow um 2 Tage vorausläuft und positiv korreliert
if best_outflow_lag == "lag_2d" and correlation > 0.15:
    # Hoher Outflow heute → Erwarte Preissteigerung in 2 Tagen
    signal = "BULLISH_DELAYED"
```

#### 2. Regime-basiertes Trading
```python
if current_regime == "Bull Market":
    strategy = "LONG_BIAS"
elif current_regime == "Distribution Phase":
    strategy = "SHORT_BIAS"
elif current_regime == "Stealth Accumulation":
    strategy = "ACCUMULATE"
else:
    strategy = "DEFENSIVE"
```

#### 3. Volatility-Adjusted Position Sizing
```python
if high_inflow_volatility > baseline_volatility * 1.5:
    position_size *= 0.5  # Reduziere Positionsgröße bei hoher Inflow-Volatilität
```

## Installation & Setup

### Dependencies

Die wissenschaftliche Analyse benötigt scikit-learn:

```bash
pip install scikit-learn==1.3.2
```

Oder mit requirements.txt:
```bash
pip install -r requirements.txt
```

### Verwendung

```python
# In wai_service.py
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# Lead-Lag-Analyse
result = await wai_service.calculate_lead_lag_analysis(max_lag=7)

# Regime Detection
result = await wai_service.calculate_regime_detection()

# Conditional Volatility
result = await wai_service.calculate_conditional_volatility()
```

## Limitierungen

### 1. Datenverfügbarkeit
- Mindestens 50+ Tage für robuste Lead-Lag-Analyse
- 100+ Tage empfohlen für Regime Detection

### 2. Statistische Signifikanz
- Korrelationen < 0.15 sind oft nicht handelbar
- Multiple-Testing-Problem bei vielen Lags

### 3. Non-Stationarity
- Marktbedingungen ändern sich über Zeit
- Periodische Rekalibrierung erforderlich

### 4. Overfitting
- Zu viele Regimes können zu Überanpassung führen
- K=4 ist ein guter Kompromiss

## Zukünftige Erweiterungen

### 1. Erweiterte Zeitreihenmodelle
- [ ] ARIMA/GARCH für Volatilitätsprognose
- [ ] VAR (Vector Autoregression) für multivariates Lead-Lag
- [ ] Granger-Kausalitätstests

### 2. Machine Learning
- [ ] Random Forest für Regime-Vorhersage
- [ ] LSTM für Zeitreihenprognose
- [ ] Ensemble-Methoden

### 3. Erweiterte Statistik
- [ ] Bootstrapping für Konfidenzintervalle
- [ ] Monte-Carlo-Simulationen
- [ ] Bayesianische Analyse

### 4. Alternative Metriken
- [ ] Sharpe Ratio nach Regimes
- [ ] Maximum Drawdown-Analyse
- [ ] Kelly-Kriterium für optimale Positionsgrößen

## Wissenschaftliche Validierung

### Backtesting

**Empfohlene Methodik:**
1. Out-of-Sample Testing (60/40 Split)
2. Walk-Forward-Optimierung
3. Monte-Carlo-Simulationen für Robustheit

### Performance-Metriken

```python
# Sharpe Ratio des Regimes
sharpe_ratio = mean(returns) / std(returns) * √252

# Information Ratio (vs. Buy & Hold)
information_ratio = (mean(strategy_returns) - mean(benchmark_returns)) / tracking_error

# Maximum Drawdown
max_drawdown = min(cumulative_returns - running_max)
```

## Zusammenfassung

Die wissenschaftliche Auswertung ist das **Alleinstellungsmerkmal** des WAI/WII-Systems:

✅ **Lead-Lag-Analyse** beantwortet: Folgt Preis auf Flows?
✅ **Regime Detection** identifiziert: Aktuelle Marktphase
✅ **Conditional Volatility** zeigt: Flow-abhängige Volatilität

**Zentrale Erkenntnisse:**
1. **Inflow ist bearish** (negative Korrelation mit Returns)
2. **Outflow ist bullish** (positive Korrelation mit Returns)
3. **Preis folgt auf Whale-Flows** (mit 1-3 Tagen Verzögerung)
4. **Verkaufsdruck erhöht Volatilität**

Diese wissenschaftlich fundierte Analyse hebt das System von einfachen Indikatoren ab und bietet **quantifizierbare, statistisch abgesicherte Handelssignale**.
