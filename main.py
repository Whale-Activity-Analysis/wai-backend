"""
WAI Backend API - FastAPI Application
Berechnet und liefert den Whale Activity Index (WAI)
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
import os
from datetime import datetime

from wai_service import WAIService
from config import config

# FastAPI App initialisieren
app = FastAPI(
    title="WAI Backend API",
    description="Whale Activity Index (WAI) v0.1 - Analysiert Whale-Transaktionen auf der Blockchain",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware hinzufügen (für Frontend-Integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WAI Service Instanz
wai_service = WAIService()


@app.get("/")
async def root():
    """Root Endpoint mit API-Informationen"""
    return {
        "name": "WAI Backend API",
        "version": "0.1.0",
        "description": "Whale Activity Index (WAI) & Whale Intent Index (WII) - Combined Service",
        "endpoints": {
            "docs": "/docs",
            "latest": "/api/wai/latest (inkl. WII)",
            "history": "/api/wai/history (inkl. WII)",
            "statistics": "/api/wai/statistics (inkl. WII)",
            "health": "/health"
        },
        "note": "Für wissenschaftliche Analysen siehe /analysis Ordner (Python-Skripte)"
    }


@app.get("/health")
async def health_check():
    """Health Check Endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "wai-backend"
    }


@app.get("/api/wai/latest")
async def get_latest_wai():
    """
    Gibt den aktuellsten WAI & WII-Wert zurück.
    
    Returns:
        Dictionary mit WAI, WII, Exchange-Flows und BTC-Daten
    """
    try:
        result = await wai_service.get_latest_wai()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Daten: {str(e)}")


@app.get("/api/wai/history")
async def get_wai_history(
    start_date: Optional[str] = Query(None, description="Startdatum (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Enddatum (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Max. Anzahl Ergebnisse (1-1000)")
):
    """
    Gibt WAI & WII Historie für einen Zeitraum zurück.
    
    Query Parameters:
        - start_date: Startdatum im Format YYYY-MM-DD
        - end_date: Enddatum im Format YYYY-MM-DD
        - limit: Maximale Anzahl der Ergebnisse (neueste zuerst)
    
    Returns:
        Liste mit Berechnungen inkl.:
        - `wai` (v2): Whale Activity Index [0-100]
        - `wii`: Whale Intent Index [0-100]
        - `wii_signal`: selling_pressure | neutral | accumulation
        - `tx_count`: Whale-Transaktionen
        - `volume`: Whale-Volumen (BTC)
        - `exchange_inflow/outflow/netflow`: Exchange-Flows (BTC)
        - `btc_close`: BTC-Schlusskurs (USD)
        - `btc_return_1d`: Tägliche BTC-Rendite
    """
    try:
        # Datumsvalidierung
        if start_date:
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Ungültiges Startdatum. Format: YYYY-MM-DD")
        
        if end_date:
            try:
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Ungültiges Enddatum. Format: YYYY-MM-DD")
        
        result = await wai_service.get_wai_data(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "count": len(result),
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Historie: {str(e)}")


@app.get("/api/wai/statistics")
async def get_statistics(
    start_date: Optional[str] = Query(None, description="Startdatum (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Enddatum (YYYY-MM-DD)")
):
    """
    Gibt statistische Auswertungen über einen WAI-Zeitraum zurück
    
    Query Parameters:
        - start_date (optional): Startdatum im Format YYYY-MM-DD
        - end_date (optional): Enddatum im Format YYYY-MM-DD
    
    Returns:
        Dictionary mit Statistiken (Mittelwert, Median, Min, Max, etc.)
    """
    try:
        # Datumsvalidierung
        if start_date:
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Ungültiges Startdatum. Format: YYYY-MM-DD")
        
        if end_date:
            try:
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Ungültiges Enddatum. Format: YYYY-MM-DD")
        
        result = await wai_service.get_wai_statistics(
            start_date=start_date,
            end_date=end_date
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Berechnen der Statistiken: {str(e)}")


@app.get("/api/wai/formula")
async def get_formula_info():
    """
    Gibt Informationen über die WAI-Berechnungsformel zurück
    
    Returns:
        Dictionary mit Formelbeschreibung und Parametern
    """
    baseline_type = config.USE_ROBUST_BASELINE.upper()
    
    baseline_formulas = {
        "SMA": "T̂_d / SMA_30(T), V̂_d / SMA_30(V) - Standard Simple Moving Average",
        "EWMA": "T̂_d / EWMA_30(T), V̂_d / EWMA_30(V) - Exponentially Weighted (robust gegen Ausreißer)",
        "MEDIAN": "T̂_d / Median_30(T), V̂_d / Median_30(V) - Rolling Median (robust gegen Extremwerte)"
    }
    
    return {
        "version": "0.1",
        "description": "Whale Activity Index - Adaptive Skalierung mit robuster Baseline",
        "formula": {
            "normalization": {
                "baseline_type": baseline_type,
                "T_normalized": baseline_formulas.get(baseline_type, baseline_formulas["SMA"]),
                "V_normalized": "Analog zu Transaction Count",
                "description": f"Normalisierung durch {baseline_type} Basislinie (180-Tage Percentile-Fenster)"
            },
            "wai_calculation": {
                "formula": "WAI_raw = 0.5 · T̂_d + 0.5 · V̂_d",
                "weights": {
                    "transaction_count": 0.5,
                    "volume": 0.5
                },
                "description": "Gleichgewichtete Kombination von normalisierten Transaktionen und Volumen"
            },
            "percentile_scaling": {
                "formula": "WAI_percentile = PercentileRank(WAI_raw, window=180 Tage)",
                "range": "[0, 1]",
                "description": "Historisch adaptive Skalierung basierend auf 180-Tage-Fenster"
            },
            "final_output": {
                "formula": "WAI_index = round(WAI_percentile × 100)",
                "range": "[0, 100]",
                "description": "Gerundeter Indexwert ohne harte Grenzen"
            }
        },
        "parameters": {
            "SMA_window": config.SMA_WINDOW,
            "baseline_method": config.USE_ROBUST_BASELINE,
            "ewma_span": config.EWMA_SPAN,
            "percentile_window": 180,
            "data_source": config.DATA_URL
        },
        "interpretation": {
            "very_low": "0-25: Sehr niedrige Whale-Aktivität",
            "low": "25-50: Unterdurchschnittliche Whale-Aktivität",
            "normal": "50-75: Normale Whale-Aktivität",
            "high": "75-100: Überdurchschnittliche bis sehr hohe Whale-Aktivität"
        }
    }


@app.get("/api/wai/comparison")
async def get_wai_comparison():
    """
    Vergleicht den alten WAI-Index (linear, 50/50) mit dem neuen WAI-Index v2 (percentile, dynamisch).
    
    Analyse umfasst:
    - Statistische Vergleiche (Mean, Median, Std, Min, Max)
    - Häufigkeit von Index = 100
    - Histogramm-Verteilung (5er-Buckets)
    - Sensitivität in Hochaktivitätsphasen (> 75)
    - Dynamische Gewichts-Analyse
    - Key Findings
    
    Returns:
        JSON-Summary mit detaillierten Vergleichsmetriken
    """
    try:
        result = await wai_service.calculate_wai_comparison()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Vergleich: {str(e)}")


@app.get("/api/wai/validation")
async def get_validation_stats():
    """
    Gibt WII Validierungsstatistiken mit Marketing Message zurück.
    
    Die Validierungslogik lädt sich die Daten und analysiert sie mit der
    Methode aus analysis/wii_validation.py.
    
    Returns:
        Dictionary mit Marketing Message und Statistiken
    """
    try:        
        # Importiere Validierungsfunktionen aus wii_validation.py
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analysis'))
        from wii_validation import calculate_wii_returns, generate_marketing_message, load_wai_history
        
        # Lade Daten lokal
        df = load_wai_history()
        df = df.reset_index(drop=True)
        df = df.dropna(subset=['wii', 'btc_close'])
        
        if len(df) < 2:
            raise HTTPException(status_code=400, detail="Nicht genug Daten für Validierung")
        
        # Berechne Stats
        stats = calculate_wii_returns(df, [3, 7, 14])
        
        # Generiere Marketing Message
        marketing_msg = generate_marketing_message(stats)
        
        # Füge Message zu Stats hinzu
        stats['marketing_message'] = marketing_msg
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Validierungsanalyse: {str(e)}")


# Hauptfunktion zum Starten des Servers
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG  # Auto-Reload bei Dateiänderungen (nur für Development)
    )
