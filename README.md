# WAI Backend

Whale Activity Index (WAI) v0.1 - Backend Service

## Beschreibung

Dieses Backend berechnet den **Whale Activity Index (WAI)**, der die Aktivität von großen Krypto-Transaktionen ("Whales") analysiert und in einem normalisierten Index darstellt.

### Formel

**Normalisierung:**
- T̂_d = T_d / SMA_30(T)
- V̂_d = V_d / SMA_30(V)

**WAI-Berechnung:**
```
WAI_d = 0.5 · T̂_d + 0.5 · V̂_d
```

- **T_d**: Anzahl Whale-Transaktionen am Tag
- **V_d**: Summe des Whale-Volumens am Tag
- **SMA_30**: 30-Tage gleitender Durchschnitt
- **Wertebereich**: [0, 3]

## Installation

### 1. Virtual Environment erstellen

```bash
python -m venv venv
```

### 2. Virtual Environment aktivieren

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

## Server starten

```bash
python main.py
```

Der Server läuft dann auf: `http://localhost:8000`

## API Endpoints

### 📊 Swagger Dokumentation
- **GET** `/docs` - Interaktive API-Dokumentation

### 🔍 Health Check
- **GET** `/health` - Server Status

### 📈 WAI Endpoints

#### Aktuellster WAI-Wert
```
GET /api/wai/latest
```

#### WAI-Historie
```
GET /api/wai/history?start_date=2024-01-01&end_date=2024-12-31&limit=100
```

Parameter:
- `start_date` (optional): Startdatum (YYYY-MM-DD)
- `end_date` (optional): Enddatum (YYYY-MM-DD)
- `limit` (optional): Max. Anzahl Ergebnisse (1-1000)

#### Statistiken
```
GET /api/wai/statistics
```

#### Formel-Informationen
```
GET /api/wai/formula
```

## Datenquelle

Die täglichen Metriken werden von folgendem Repository abgerufen:
```
https://raw.githubusercontent.com/Whale-Activity-Analysis/wai-collector/refs/heads/main/data/daily_metrics.json
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
