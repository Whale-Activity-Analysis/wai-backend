# WAI Backend

Whale Activity Index (WAI) v2 - Backend Service

## Beschreibung

Dieses Backend berechnet den **Whale Activity Index (WAI v2)**, der die Aktivität von großen Bitcoin-Transaktionen ("Whales") analysiert. Der Index verwendet **volatilitätsabhängige Gewichtung** und **historisch adaptive Skalierung** für eine robuste Signalqualität.

### Methodik (WAI v2)

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

### Option 1: Lokal mit Python

```bash
python main.py
```

### Option 2: Mit Docker (Empfohlen)

```bash
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
