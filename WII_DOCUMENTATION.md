# Whale Intent Index (WII) - Dokumentation

## Übersicht

Der **Whale Intent Index (WII)** ergänzt den Whale Activity Index (WAI) und beantwortet die Frage: **"Was wollen die Whales?"**

- **WAI**: Wie aktiv sind Whales? (Transaktionszahl & Volumen)
- **WII**: Was sind ihre Absichten? (Exchange-Flows & Akkumulation/Verkauf)

## Datengrundlage

Der WII basiert auf Exchange-Flow-Daten aus den täglichen Metriken:

```json
{
  "exchange_inflow_btc": 514.84,      // BTC, die zu Exchanges fließen
  "exchange_outflow_btc": 262.97,     // BTC, die von Exchanges abfließen
  "exchange_netflow_btc": -251.87,    // Netflow (Outflow - Inflow)
  "exchange_flow_ratio": 0.6619,      // Outflow / Inflow
  "exchange_whale_tx_count": 3        // Anzahl Whale-Exchange-Transaktionen
}
```

## Berechnung

### Schritt 1: Netflow Ratio

Die Netflow Ratio normalisiert den Netflow auf den Bereich [-1, 1]:

```
netflow_ratio = (Outflow - Inflow) / (Outflow + Inflow)
```

**Interpretation:**
- `-1`: Nur Inflow → Maximaler Verkaufsdruck
- `0`: Ausgeglichen → Neutral
- `+1`: Nur Outflow → Maximale Akkumulation

### Schritt 2: Normalisierung auf [0, 1]

```
wii_normalized = (netflow_ratio + 1) / 2
```

- `0`: Verkaufsdruck
- `0.5`: Neutral
- `1`: Akkumulation

### Schritt 3: Historisch Adaptive Skalierung

Verwendung von Percentile Rank über ein 180-Tage-Fenster:

```
wii_percentile = PercentileRank(wii_normalized, window=180)
```

Dies skaliert die Werte relativ zur historischen Verteilung.

### Schritt 4: Skalierung auf [0, 100]

```
wii_scaled = round(wii_percentile × 100)
```

### Schritt 5: EMA-Smoothing

Exponential Moving Average (EMA) mit 7-Tage-Fenster für Stabilität:

```
wii = EMA(wii_scaled, span=7)
```

## Interpretation

### WII-Bereiche

| WII-Wert | Signal | Bedeutung |
|----------|--------|-----------|
| 0-30 | `selling_pressure` | Starker Verkaufsdruck - Whales verschieben BTC zu Exchanges |
| 30-70 | `neutral` | Ausgeglichene Aktivität - Keine klare Richtung |
| 70-100 | `accumulation` | Starke Akkumulation - Whales ziehen BTC von Exchanges ab |

### Beispiel-Szenarien

#### Hoher Verkaufsdruck (WII < 30)
```json
{
  "date": "2026-01-19",
  "wii": 25,
  "wii_signal": "selling_pressure",
  "exchange_inflow": 800.5,
  "exchange_outflow": 150.2,
  "exchange_netflow": -650.3,
  "netflow_ratio": -0.684
}
```
→ Whales verschieben deutlich mehr BTC zu Exchanges als ab → Potenzieller Verkaufsdruck

#### Hohe Akkumulation (WII > 70)
```json
{
  "date": "2026-01-20",
  "wii": 82,
  "wii_signal": "accumulation",
  "exchange_inflow": 100.0,
  "exchange_outflow": 750.0,
  "exchange_netflow": 650.0,
  "netflow_ratio": 0.765
}
```
→ Whales ziehen massiv BTC von Exchanges ab → Akkumulationsphase

#### Neutral (WII 30-70)
```json
{
  "date": "2026-01-21",
  "wii": 52,
  "wii_signal": "neutral",
  "exchange_inflow": 400.0,
  "exchange_outflow": 420.0,
  "exchange_netflow": 20.0,
  "netflow_ratio": 0.024
}
```
→ Ausgeglichene Exchange-Flows → Keine klare Richtung

## API-Endpunkte

### 1. Aktuellster WII-Wert

```http
GET /api/wii/latest
```

**Response:**
```json
{
  "date": "2026-01-19",
  "wii": 45,
  "wii_signal": "neutral",
  "exchange_inflow": 514.84,
  "exchange_outflow": 262.97,
  "exchange_netflow": -251.87,
  "netflow_ratio": -0.3238,
  "interpretation": {
    "selling_pressure": "WII < 30: Whales verkaufen (Inflow zu Exchanges)",
    "neutral": "WII 30-70: Ausgeglichene Aktivität",
    "accumulation": "WII > 70: Whales akkumulieren (Outflow von Exchanges)"
  }
}
```

### 2. WII-Historie

```http
GET /api/wii/history?start_date=2026-01-01&end_date=2026-01-19&limit=10
```

**Response:**
```json
{
  "count": 10,
  "data": [
    {
      "date": "2026-01-19",
      "wii": 45,
      "wii_signal": "neutral",
      "exchange_inflow": 514.84,
      "exchange_outflow": 262.97,
      "exchange_netflow": -251.87,
      "netflow_ratio": -0.3238
    }
  ],
  "interpretation": {
    "selling_pressure": "WII < 30: Hoher Inflow zu Exchanges → Verkaufsdruck",
    "neutral": "WII 30-70: Ausgeglichene Exchange-Aktivität",
    "accumulation": "WII > 70: Hoher Outflow von Exchanges → Akkumulation"
  }
}
```

### 3. Kombinierte WAI + WII Daten

```http
GET /api/wai/history?start_date=2026-01-01&limit=10
```

**Response (enthält beide Indizes):**
```json
{
  "count": 10,
  "data": [
    {
      "date": "2026-01-19",
      "wai": 67,
      "wai_v1": 65,
      "wii": 45,
      "wii_signal": "neutral",
      "tx_count": 10,
      "volume": 3320.58,
      "exchange_inflow": 514.84,
      "exchange_outflow": 262.97,
      "exchange_netflow": -251.87,
      "netflow_ratio": -0.3238,
      "btc_close": 104500.23,
      "btc_return_1d": 0.0234,
      "btc_volatility_7d": 0.0156
    }
  ]
}
```

### 4. Statistiken (inkl. WII)

```http
GET /api/wai/statistics?start_date=2026-01-01&end_date=2026-01-19
```

**Response:**
```json
{
  "total_days": 19,
  "date_range": {
    "start": "2026-01-01",
    "end": "2026-01-19"
  },
  "wai_stats": {
    "mean": 56.32,
    "median": 54.0,
    "min": 12.0,
    "max": 98.0,
    "std": 18.45
  },
  "wii_stats": {
    "mean": 51.24,
    "median": 50.0,
    "min": 15.0,
    "max": 87.0,
    "std": 16.78,
    "signal_distribution": {
      "selling_pressure": 4,
      "neutral": 11,
      "accumulation": 4
    }
  },
  "latest_wai": 67.0,
  "latest_wii": 45.0,
  "latest_wii_signal": "neutral",
  "latest_date": "2026-01-19"
}
```

## Kombinierte Analyse: WAI + WII

Die gleichzeitige Betrachtung beider Indizes liefert tiefe Einblicke:

| WAI | WII | Interpretation |
|-----|-----|----------------|
| Hoch | Hoch | Hohe Aktivität + Akkumulation → Starkes bullishes Signal |
| Hoch | Niedrig | Hohe Aktivität + Verkaufsdruck → Distributionsphase |
| Niedrig | Hoch | Niedrige Aktivität + Akkumulation → Stilles Akkumulieren |
| Niedrig | Niedrig | Niedrige Aktivität + Verkaufsdruck → Kapitulation/Desinteresse |

### Beispiel: Bullishes Setup
```json
{
  "date": "2026-01-20",
  "wai": 85,          // Sehr hohe Whale-Aktivität
  "wii": 78,          // Starke Akkumulation
  "wii_signal": "accumulation",
  "exchange_netflow": 450.2   // Positiver Netflow
}
```
→ Whales sind sehr aktiv UND akkumulieren → Bullish

### Beispiel: Bearishes Setup
```json
{
  "date": "2026-01-21",
  "wai": 82,          // Sehr hohe Whale-Aktivität
  "wii": 22,          // Starker Verkaufsdruck
  "wii_signal": "selling_pressure",
  "exchange_netflow": -680.5  // Negativer Netflow
}
```
→ Whales sind sehr aktiv UND verschieben zu Exchanges → Bearish

## Technische Details

### Konfiguration

In [config.py](config.py):
```python
# WII (Whale Intent Index) Calculation Parameters
WII_SMOOTHING_WINDOW = int(os.getenv("WII_SMOOTHING_WINDOW", 7))  # EMA-Glättung
WII_MIN = int(os.getenv("WII_MIN", 0))
WII_MAX = int(os.getenv("WII_MAX", 100))
```

### Service-Methode

In [wai_service.py](wai_service.py):
```python
def calculate_wii(self, df: pd.DataFrame) -> pd.DataFrame:
    """
    Berechnet den Whale Intent Index (WII)
    
    Returns:
        DataFrame mit WII-Werten und Signalen
    """
    # Implementierung siehe Code
```

## Vorteile

1. **Klare Interpretation**: Einfache Unterscheidung zwischen Akkumulation und Distribution
2. **Historisch adaptiv**: Percentile-basierte Skalierung passt sich an
3. **Robust**: Netflow Ratio ist resistent gegen einzelne Ausreißer
4. **Ergänzend**: Perfekte Ergänzung zum WAI für ganzheitliche Analyse

## Einschränkungen

1. **Fehlende Daten**: An Tagen ohne Exchange-Aktivität wird WII = 50 (neutral) gesetzt
2. **Exchange-Abdeckung**: Nur erfasste Exchanges werden berücksichtigt
3. **Latenz**: Exchange-Flows können verzögert erkannt werden
4. **OTC-Trades**: Over-the-Counter-Geschäfte werden nicht erfasst

## Zukünftige Erweiterungen

- [ ] Gewichtung nach Exchange-Größe
- [ ] Trennung nach CEX und DEX
- [ ] Kombination mit On-Chain-Metriken (UTXO-Alter, etc.)
- [ ] Machine Learning für Signalverbesserung
- [ ] Integration von Stablecoin-Flows

## Zusammenfassung

Der **WII (Whale Intent Index)** erweitert das WAI-System um eine entscheidende Dimension:

- **WAI**: Misst die Aktivität (Wie viel bewegt sich?)
- **WII**: Misst die Absicht (Wohin bewegt es sich?)

Zusammen bieten sie ein vollständiges Bild der Whale-Aktivitäten und ihrer Marktauswirkungen.
