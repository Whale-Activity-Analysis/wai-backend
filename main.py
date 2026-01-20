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
        "description": "Whale Activity Index & Whale Intent Index Calculation Service",
        "endpoints": {
            "docs": "/docs",
            "latest": "/api/wai/latest",
            "history": "/api/wai/history",
            "statistics": "/api/wai/statistics",
            "wii_latest": "/api/wii/latest",
            "wii_history": "/api/wii/history",
            "analysis_lead_lag": "/api/analysis/lead-lag",
            "analysis_regime": "/api/analysis/regime-detection",
            "analysis_volatility": "/api/analysis/conditional-volatility",
            "analysis_summary": "/api/analysis/scientific-summary",
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
    Gibt den aktuellsten WAI-Wert zurück (v2) und den historischen v1-Vergleich mit BTC-Daten.
    
    Returns:
        Dictionary mit dem neuesten WAI-Wert, v1-Vergleich, BTC-Preis und Volatilität
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
    Gibt WAI-Historie für einen Zeitraum zurück (v2) plus v1-Vergleichswerte und BTC-Daten.
    
    Query Parameters:
        - start_date: Startdatum im Format YYYY-MM-DD
        - end_date: Enddatum im Format YYYY-MM-DD
        - limit: Maximale Anzahl der Ergebnisse (neueste zuerst)
    
    Returns:
        Liste mit WAI-Berechnungen inkl.:
        - `wai` (v2): Percentile + EMA-Smoothing
        - `wai_v1`: Linear 50/50 mit Percentile-Skalierung
        - `tx_count`: Whale-Transaktionen
        - `volume`: Whale-Volumen (BTC)
        - `btc_close`: BTC-Schlusskurs (USD)
        - `btc_return_1d`: Tägliche BTC-Rendite
        - `btc_volatility_7d`: 7-Tage BTC-Volatilität
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


@app.get("/api/wii/latest")
async def get_latest_wii():
    """
    Gibt den aktuellsten WII-Wert (Whale Intent Index) zurück.
    
    Der WII zeigt die Absichten der Whales basierend auf Exchange-Flows:
    - WII < 30: Starker Verkaufsdruck (Hoher Inflow zu Exchanges)
    - WII 30-70: Neutral / Ausgeglichen
    - WII > 70: Starke Akkumulation (Hoher Outflow von Exchanges)
    
    Returns:
        Dictionary mit dem neuesten WII-Wert und Exchange-Flow-Daten
    """
    try:
        result = await wai_service.get_latest_wai()
        return {
            'date': result.get('date'),
            'wii': result.get('wii'),
            'wii_signal': result.get('wii_signal'),
            'exchange_inflow': result.get('exchange_inflow'),
            'exchange_outflow': result.get('exchange_outflow'),
            'exchange_netflow': result.get('exchange_netflow'),
            'netflow_ratio': result.get('netflow_ratio'),
            'interpretation': {
                'selling_pressure': 'WII < 30: Whales verkaufen (Inflow zu Exchanges)',
                'neutral': 'WII 30-70: Ausgeglichene Aktivität',
                'accumulation': 'WII > 70: Whales akkumulieren (Outflow von Exchanges)'
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der WII-Daten: {str(e)}")


@app.get("/api/wii/history")
async def get_wii_history(
    start_date: Optional[str] = Query(None, description="Startdatum (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Enddatum (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Max. Anzahl Ergebnisse (1-1000)")
):
    """
    Gibt WII-Historie (Whale Intent Index) für einen Zeitraum zurück.
    
    Der WII analysiert Whale-Absichten basierend auf Exchange-Flows:
    - Netflow Ratio: (Outflow - Inflow) / (Outflow + Inflow)
    - WII-Skalierung: Percentile-basiert auf 180-Tage-Fenster
    
    Query Parameters:
        - start_date: Startdatum im Format YYYY-MM-DD
        - end_date: Enddatum im Format YYYY-MM-DD
        - limit: Maximale Anzahl der Ergebnisse (neueste zuerst)
    
    Returns:
        Liste mit WII-Berechnungen inkl.:
        - `wii`: Whale Intent Index [0-100]
        - `wii_signal`: selling_pressure | neutral | accumulation
        - `exchange_inflow`: BTC-Inflow zu Exchanges
        - `exchange_outflow`: BTC-Outflow von Exchanges
        - `exchange_netflow`: Netflow (Outflow - Inflow)
        - `netflow_ratio`: Normalisiertes Netflow [-1, 1]
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
        
        # Extrahiere nur WII-relevante Daten
        wii_data = []
        for item in result:
            wii_data.append({
                'date': item.get('date'),
                'wii': item.get('wii'),
                'wii_signal': item.get('wii_signal'),
                'exchange_inflow': item.get('exchange_inflow'),
                'exchange_outflow': item.get('exchange_outflow'),
                'exchange_netflow': item.get('exchange_netflow'),
                'netflow_ratio': item.get('netflow_ratio')
            })
        
        return {
            "count": len(wii_data),
            "data": wii_data,
            "interpretation": {
                "selling_pressure": "WII < 30: Hoher Inflow zu Exchanges → Verkaufsdruck",
                "neutral": "WII 30-70: Ausgeglichene Exchange-Aktivität",
                "accumulation": "WII > 70: Hoher Outflow von Exchanges → Akkumulation"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der WII-Historie: {str(e)}")


@app.get("/api/analysis/lead-lag")
async def get_lead_lag_analysis(
    max_lag: Optional[int] = Query(7, ge=1, le=30, description="Maximale Anzahl Tage für Lag-Analyse (1-30)")
):
    """
    Lead-Lag-Analyse: Folgt der BTC-Preis auf Whale-Flows?
    
    Wissenschaftliche Analyse zeitverzögerter Korrelationen zwischen:
    - Exchange Inflow/Outflow und BTC-Returns
    - WAI/WII und BTC-Returns
    
    Beantwortet Fragen:
    - Ist Inflow bearish?
    - Ist Outflow bullish?
    - Folgt Preis auf Whale-Flow?
    
    Query Parameters:
        - max_lag: Maximale Anzahl Tage für Lag-Analyse (Standard: 7)
    
    Returns:
        Detaillierte Korrelationsanalysen mit Best-Lag-Identifikation
    """
    try:
        result = await wai_service.calculate_lead_lag_analysis(max_lag=max_lag)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei Lead-Lag-Analyse: {str(e)}")


@app.get("/api/analysis/regime-detection")
async def get_regime_detection():
    """
    Regime Detection: Identifiziert verschiedene Marktphasen
    
    Verwendet K-Means Clustering auf:
    - WAI (Aktivität)
    - WII (Intent)
    - BTC Volatilität
    
    Identifiziert Regimes wie:
    - Bull Market (Hohe Aktivität + Akkumulation)
    - Distribution Phase (Hohe Aktivität + Verkaufsdruck)
    - Stealth Accumulation (Niedrige Aktivität + Akkumulation)
    - Capitulation (Niedrige Aktivität + Verkaufsdruck)
    
    Returns:
        Regime-Klassifizierung mit Charakteristiken und aktuellem Regime
    """
    try:
        result = await wai_service.calculate_regime_detection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei Regime Detection: {str(e)}")


@app.get("/api/analysis/conditional-volatility")
async def get_conditional_volatility():
    """
    Conditional Volatility: Volatilität abhängig von Whale-Flows
    
    Untersucht, ob und wie Whale-Flows die Marktvolatilität beeinflussen:
    - Volatilität nach WII-Signal (selling_pressure, neutral, accumulation)
    - Volatilität bei hohen Inflows vs. Outflows
    - Korrelation zwischen Flows und Volatilität
    
    Beantwortet:
    - Erhöhen hohe Inflows die Volatilität?
    - Ist Verkaufsdruck volatiler als Akkumulation?
    
    Returns:
        Detaillierte Volatilitätsanalysen konditioniert auf Whale-Aktivität
    """
    try:
        result = await wai_service.calculate_conditional_volatility()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei Conditional Volatility: {str(e)}")


@app.get("/api/analysis/scientific-summary")
async def get_scientific_summary():
    """
    Wissenschaftliche Gesamtauswertung: Alle Analysen kombiniert
    
    Liefert eine umfassende wissenschaftliche Analyse mit:
    1. Lead-Lag-Analyse (Preis folgt Flows?)
    2. Regime Detection (Aktuelle Marktphase)
    3. Conditional Volatility (Flow-abhängige Volatilität)
    
    Dies ist das Differenzierungsmerkmal des Systems!
    
    Returns:
        Kombinierte wissenschaftliche Auswertung mit Key Findings
    """
    try:
        # Parallele Ausführung der Analysen
        lead_lag = await wai_service.calculate_lead_lag_analysis()
        regime = await wai_service.calculate_regime_detection()
        cond_vol = await wai_service.calculate_conditional_volatility()
        
        return {
            'title': 'Wissenschaftliche Whale-Flow-Analyse',
            'description': 'Umfassende statistische Auswertung der Whale-Aktivität und Marktauswirkungen',
            'analyses': {
                'lead_lag_analysis': lead_lag,
                'regime_detection': regime,
                'conditional_volatility': cond_vol
            },
            'executive_summary': {
                'inflow_effect': 'Bearish' if lead_lag.get('key_findings', {}).get('inflow_bearish', False) else 'Nicht signifikant bearish',
                'outflow_effect': 'Bullish' if lead_lag.get('key_findings', {}).get('outflow_bullish', False) else 'Nicht signifikant bullish',
                'current_market_regime': regime.get('current_regime', {}).get('interpretation', 'Unbekannt'),
                'wii_predictive_power': 'Hoch' if lead_lag.get('key_findings', {}).get('wii_predictive', False) else 'Mittel bis Niedrig',
                'best_predictor': lead_lag.get('key_findings', {}).get('best_predictor', 'Unbekannt')
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei wissenschaftlicher Auswertung: {str(e)}")


# Hauptfunktion zum Starten des Servers
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG  # Auto-Reload bei Dateiänderungen (nur für Development)
    )
