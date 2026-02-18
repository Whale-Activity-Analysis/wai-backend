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
import json
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
            "latest": "/api/wai/latest (inkl. WII, Momentum, Confidence)",
            "history": "/api/wai/history (inkl. WII, Momentum, Confidence)",
            "statistics": "/api/wai/statistics",
            "momentum": "/api/wai/momentum (Whale Momentum Indikator)",
            "confidence": "/api/wai/confidence (Signal Confidence Score)",
            "backtest": "/api/wai/backtest (Historical Signal Backtest)",
            "validation": "/api/wai/validation (WII-Validierungsstats)"
        },
        "note": "Für wissenschaftliche Analysen siehe /analysis Ordner (Python-Skripte)"
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


@app.get("/api/wai/momentum")
async def get_whale_momentum(
    limit: Optional[int] = Query(10, ge=1, le=100, description="Max. Anzahl Ergebnisse (1-100)")
):
    """
    Gibt Whale Momentum Daten zurück - zeigt Beschleunigung/Verlangsamung der Whale-Aktivität.
    
    Whale Momentum = WAI_today - WAI_7d_avg
    
    Query Parameters:
        - limit: Maximale Anzahl der Ergebnisse (neueste zuerst, default: 10)
    
    Returns:
        - `whale_momentum`: Momentum-Wert (positiv = Beschleunigung, negativ = Verlangsamung)
        - `momentum_signal`: Klassifikation (strong_acceleration | acceleration | neutral | deceleration | strong_deceleration)
        - `wai`: Aktueller WAI-Wert
        - `wai_7d_avg`: 7-Tage-Durchschnitt des WAI
    
    Interpretation:
        - > 20: Starke Beschleunigung
        - 10-20: Beschleunigung
        - -10 bis 10: Neutral
        - -20 bis -10: Verlangsamung
        - < -20: Starke Verlangsamung
    """
    try:
        # Hole Daten mit Momentum-Berechnung
        result = await wai_service.get_wai_data(limit=limit)
        
        # Extrahiere relevante Momentum-Felder
        momentum_data = []
        for item in result:
            momentum_data.append({
                'date': item['date'],
                'wai': item['wai'],
                'wai_7d_avg': item['wai_7d_avg'],
                'whale_momentum': item['whale_momentum'],
                'momentum_signal': item['momentum_signal']
            })
        
        return {
            "count": len(momentum_data),
            "data": momentum_data,
            "interpretation": {
                "strong_acceleration": "Momentum > 20 - Stark steigende Whale-Aktivität",
                "acceleration": "Momentum 10-20 - Steigende Whale-Aktivität",
                "neutral": "Momentum -10 bis 10 - Stabile Aktivität",
                "deceleration": "Momentum -20 bis -10 - Abnehmende Aktivität",
                "strong_deceleration": "Momentum < -20 - Stark abnehmende Aktivität"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen des Momentums: {str(e)}")


@app.get("/api/wai/confidence")
async def get_confidence_score(
    limit: Optional[int] = Query(10, ge=1, le=100, description="Max. Anzahl Ergebnisse (1-100)")
):
    """
    Gibt Confidence Scores zurück - bewertet die Verlässlichkeit des WAI-Signals.
    
    Der Confidence Score kombiniert:
    - Anzahl der Whale-Transaktionen
    - Exchange-Aktivität
    - Abweichung vom historischen Median
    
    Query Parameters:
        - limit: Maximale Anzahl der Ergebnisse (neueste zuerst, default: 10)
    
    Returns:
        - `confidence_score`: Score 0-100 (höher = verlässlicher)
        - `confidence_level`: Klassifikation (very_high | high | moderate | low)
        - `wai`: Aktueller WAI-Wert
        - `tx_count`: Anzahl Whale-Transaktionen
    
    Interpretation:
        - > 80: Sehr hohe Confidence (starkes, verlässliches Signal)
        - 60-80: Hohe Confidence (verlässlich)
        - 40-60: Moderate Confidence (mit Vorsicht betrachten)
        - < 40: Niedrige Confidence (schwaches Signal)
    """
    try:
        # Hole Daten mit Confidence-Berechnung
        result = await wai_service.get_wai_data(limit=limit)
        
        # Extrahiere relevante Confidence-Felder
        confidence_data = []
        for item in result:
            confidence_data.append({
                'date': item['date'],
                'wai': item['wai'],
                'tx_count': item['tx_count'],
                'confidence_score': item['confidence_score'],
                'confidence_level': item['confidence_level']
            })
        
        return {
            "count": len(confidence_data),
            "data": confidence_data,
            "interpretation": {
                "very_high": "Score > 80 - Sehr verlässliches Signal",
                "high": "Score 60-80 - Verlässliches Signal",
                "moderate": "Score 40-60 - Mit Vorsicht betrachten",
                "low": "Score < 40 - Schwaches Signal"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen des Confidence Scores: {str(e)}")


@app.get("/api/wai/backtest")
async def backtest_signal(
    signal: str = Query(..., description="WII Signal-Typ zum Backtesten"),
    horizon: int = Query(3, ge=1, le=30, description="Forward-Return Horizont (Tage, 1-30)")
):
    """
    Führt einen historischen Backtest für WII-Signale aus.
    
    **Verfügbare WII-Signale:**
    - `wii_accumulation`: Whale Akkumulation (WII > 70) - Bullish Signal
    - `wii_strong_accumulation`: Starke Akkumulation (WII > 85) - Sehr Bullish
    - `wii_selling`: Whale Verkaufsdruck (WII < 30) - Bearish Signal
    - `wii_strong_selling`: Starker Verkaufsdruck (WII < 15) - Sehr Bearish
    
    **Wichtig:** 
    - Bei **bullish** Signalen (accumulation): Positive Returns = Win
    - Bei **bearish** Signalen (selling): Negative Returns = Win (Short Position)
    
    Query Parameters:
        - signal: WII Signal-Typ (siehe oben)
        - horizon: Forward-Return Horizont in Tagen (default: 3)
    
    Returns:
        - **win_rate**: % der korrekten Prognosen
        - **avg_return**: Durchschnittlicher Return (%)
        - **median_return**: Medianer Return (%)
        - **max_drawdown**: Maximaler Drawdown (%)
        - **sharpe_ratio**: Risk-adjusted Return
        - **profit_factor**: Total Wins / Total Losses
        - **prediction_stats**: Detaillierte Statistiken zu Correct/Incorrect
        - **interpretation**: Automatische Analyse (bearish/bullish-aware)
    
    Beispiel:
        `/api/wai/backtest?signal=wii_selling&horizon=7`
    
    Interpretation:
        - Win Rate > 55%: Signal zeigt gute Vorhersagekraft
        - Bearish Signale: Negative Avg Return = gut (Preis fällt wie vorhergesagt)
        - Bullish Signale: Positive Avg Return = gut (Preis steigt wie vorhergesagt)
        - Sharpe > 1.0: Gutes Risk/Reward-Verhältnis
    """
    try:
        result = await wai_service.backtest_signal(
            signal_type=signal,
            horizon=horizon
        )
        
        # Wenn Fehler im Result, passenden Status Code returnen
        if 'error' in result:
            if 'Unbekannter Signal-Typ' in result.get('error', ''):
                raise HTTPException(
                    status_code=400,
                    detail=result['error'] + '. Available: ' + ', '.join(result.get('available_signals', []))
                )
            else:
                raise HTTPException(status_code=400, detail=result['error'])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Backtest: {str(e)}")


@app.get("/api/wai/validation")
async def get_validation_stats():
    """
    Gibt zwischengespeicherte WII Validierungsstatistiken mit Marketing Message zurück.
    Stats werden regelmäßig via wii_validation.py aktualisiert (Teil des Collect Jobs).
    """
    try:
        # Versuche gecachte Stats zu laden
        stats_file = os.path.join(os.path.dirname(__file__), 'data', 'wii_validation_stats.json')
        
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            return stats
        else:
            # Fallback: live berechnen wenn noch keine Cache-Datei existiert
            import sys
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analysis'))
            from wii_validation import calculate_wii_returns, generate_marketing_message, load_wai_history
            
            df = load_wai_history()
            df = df.reset_index(drop=True)
            df = df.dropna(subset=['wii', 'btc_close'])
            
            if len(df) < 2:
                raise HTTPException(status_code=400, detail="Nicht genug Daten")
            
            stats = calculate_wii_returns(df, [3, 7, 14])
            stats['marketing_message'] = generate_marketing_message(stats)
            return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler: {str(e)}")


# Hauptfunktion zum Starten des Servers
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG  # Auto-Reload bei Dateiänderungen (nur für Development)
    )
