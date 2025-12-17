"""
WAI Backend API - FastAPI Application
Berechnet und liefert den Whale Activity Index (WAI)
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
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
    allow_origins=["*"],  # In Production: spezifische Origins angeben
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
        "description": "Whale Activity Index Calculation Service",
        "endpoints": {
            "docs": "/docs",
            "latest": "/api/wai/latest",
            "history": "/api/wai/history",
            "statistics": "/api/wai/statistics",
            "health": "/health"
        }
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
    Gibt den aktuellsten WAI-Wert zurück
    
    Returns:
        Dictionary mit dem neuesten WAI-Wert und allen Metriken
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
    Gibt WAI-Historie für einen Zeitraum zurück
    
    Query Parameters:
        - start_date: Startdatum im Format YYYY-MM-DD
        - end_date: Enddatum im Format YYYY-MM-DD
        - limit: Maximale Anzahl der Ergebnisse (neueste zuerst)
    
    Returns:
        Liste mit WAI-Berechnungen
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
    return {
        "version": "0.1",
        "description": "Whale Activity Index - Minimale Version",
        "formula": {
            "normalization": {
                "T_normalized": "T_d / SMA_30(T)",
                "V_normalized": "V_d / SMA_30(V)",
                "description": "Normalisierung durch 30-Tage gleitenden Durchschnitt"
            },
            "wai_calculation": {
                "formula": "WAI_d = (0.5 · T̂_d + 0.5 · V̂_d) × 100",
                "weights": {
                    "transaction_count": 0.5,
                    "volume": 0.5
                },
                "description": "Gleichgewichtete Kombination von normalisierten Transaktionen und Volumen, skaliert auf 0-100"
            },
            "constraints": {
                "range": "[0, 100]",
                "description": "WAI-Wert wird auf den Bereich 0 bis 100 begrenzt"
            }
        },
        "parameters": {
            "SMA_window": 30,
            "data_source": "https://raw.githubusercontent.com/Whale-Activity-Analysis/wai-collector/refs/heads/main/data/daily_metrics.json"
        },
        "interpretation": {
            "very_low": "0-25: Sehr niedrige Whale-Aktivität",
            "low": "25-50: Unterdurchschnittliche Whale-Aktivität",
            "normal": "50-75: Normale Whale-Aktivität",
            "high": "75-100: Überdurchschnittliche bis sehr hohe Whale-Aktivität"
        }
    }


# Hauptfunktion zum Starten des Servers
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG  # Auto-Reload bei Dateiänderungen (nur für Development)
    )
