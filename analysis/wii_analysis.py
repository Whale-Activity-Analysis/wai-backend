"""
WII (Whale Intent Index) - Wissenschaftliche Analyse

Dieses Skript führt umfassende statistische Analysen des Whale Intent Index durch:
1. Lead-Lag-Analyse: Folgt der Preis auf Whale-Flows?
2. Regime Detection: Identifikation von Marktphasen
3. Conditional Volatility: Flow-abhängige Volatilität

Run: python analysis/wii_analysis.py
"""

import asyncio
import sys
import os

# Füge Parent-Verzeichnis zum Path hinzu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wai_service import WAIService
import json


async def run_lead_lag_analysis(service: WAIService, max_lag: int = 7):
    """
    Lead-Lag-Analyse: Zeitverzögerte Korrelationen zwischen Whale-Flows und BTC-Returns
    
    Beantwortet:
    - Ist Inflow bearish?
    - Ist Outflow bullish?
    - Folgt Preis auf Whale-Flow?
    """
    print("\n" + "="*80)
    print("LEAD-LAG-ANALYSE")
    print("="*80)
    
    result = await service.calculate_lead_lag_analysis(max_lag=max_lag)
    
    print(f"\nSample Size: {result['sample_size']} Tage")
    print(f"Max Lag: {result['max_lag_days']} Tage")
    
    # Exchange Inflow
    print("\n--- Exchange Inflow → BTC Returns ---")
    print(f"Beste Korrelation: {result['exchange_inflow_to_btc_returns']['best_lag']} "
          f"= {result['exchange_inflow_to_btc_returns']['best_correlation']}")
    print(f"Interpretation: {result['exchange_inflow_to_btc_returns']['interpretation']}")
    
    # Exchange Outflow
    print("\n--- Exchange Outflow → BTC Returns ---")
    print(f"Beste Korrelation: {result['exchange_outflow_to_btc_returns']['best_lag']} "
          f"= {result['exchange_outflow_to_btc_returns']['best_correlation']}")
    print(f"Interpretation: {result['exchange_outflow_to_btc_returns']['interpretation']}")
    
    # Netflow
    print("\n--- Netflow → BTC Returns ---")
    print(f"Beste Korrelation: {result['netflow_to_btc_returns']['best_lag']} "
          f"= {result['netflow_to_btc_returns']['best_correlation']}")
    
    # WII
    print("\n--- WII → BTC Returns ---")
    print(f"Beste Korrelation: {result['wii_to_btc_returns']['best_lag']} "
          f"= {result['wii_to_btc_returns']['best_correlation']}")
    
    # WAI
    print("\n--- WAI → BTC Returns ---")
    print(f"Beste Korrelation: {result['wai_to_btc_returns']['best_lag']} "
          f"= {result['wai_to_btc_returns']['best_correlation']}")
    
    # Key Findings
    print("\n--- KEY FINDINGS ---")
    findings = result['key_findings']
    print(f"✓ Inflow ist bearish: {findings['inflow_bearish']}")
    print(f"✓ Outflow ist bullish: {findings['outflow_bullish']}")
    print(f"✓ WII ist prädiktiv: {findings['wii_predictive']}")
    print(f"✓ Bester Prädiktor: {findings['best_predictor']}")
    
    return result


async def run_regime_detection(service: WAIService):
    """
    Regime Detection: Identifiziert Marktphasen via K-Means Clustering
    
    Klassifiziert in:
    - Bull Market
    - Distribution Phase
    - Stealth Accumulation
    - Capitulation
    """
    print("\n" + "="*80)
    print("REGIME DETECTION")
    print("="*80)
    
    result = await service.calculate_regime_detection()
    
    print(f"\nAnzahl Regimes: {result['n_regimes']}")
    print(f"Total Tage: {result['total_days']}")
    print(f"Letztes Datum: {result['latest_date']}")
    
    print("\n--- IDENTIFIZIERTE REGIMES ---")
    for regime in result['regimes']:
        print(f"\nRegime {regime['regime_id']}: {regime['interpretation']}")
        print(f"  Anzahl Tage: {regime['count']} ({regime['percentage']}%)")
        print(f"  Ø WAI: {regime['characteristics']['avg_wai']}")
        print(f"  Ø WII: {regime['characteristics']['avg_wii']}")
        print(f"  Ø Volatilität: {regime['characteristics']['avg_volatility']}")
        print(f"  Ø BTC Return: {regime['characteristics']['avg_btc_return']}")
    
    print("\n--- AKTUELLES REGIME ---")
    current = result['current_regime']
    print(f"Regime {current['regime_id']}: {current['interpretation']}")
    print(f"Häufigkeit: {current['count']} Tage ({current['percentage']}%)")
    
    return result


async def run_conditional_volatility(service: WAIService):
    """
    Conditional Volatility: Volatilität abhängig von Whale-Flows
    
    Untersucht:
    - Volatilität nach WII-Signal
    - Volatilität bei hohen Inflows vs. Outflows
    - Korrelation: Flows → Volatilität
    """
    print("\n" + "="*80)
    print("CONDITIONAL VOLATILITY")
    print("="*80)
    
    result = await service.calculate_conditional_volatility()
    
    print(f"\nSample Size: {result['sample_size']} Tage")
    
    # Volatilität nach WII-Signal
    print("\n--- Volatilität nach WII-Signal ---")
    for signal, data in result['volatility_by_wii_signal'].items():
        print(f"\n{signal.upper()}:")
        print(f"  Anzahl Tage: {data['count']}")
        print(f"  Ø Volatilität: {data['avg_volatility']:.6f}")
        print(f"  Ø Return: {data['avg_return']:.6f}")
    
    # Volatilität nach Flow-Intensität
    print("\n--- Volatilität nach Flow-Intensität ---")
    for flow_type, data in result['volatility_by_flow_intensity'].items():
        print(f"\n{flow_type.upper()}:")
        print(f"  Anzahl Tage: {data['count']}")
        print(f"  Ø Volatilität: {data['avg_volatility']:.6f}")
        print(f"  Ø Return: {data['avg_return']:.6f}")
    
    # Korrelationen
    print("\n--- Korrelationen: Flows → Volatilität ---")
    print(f"Inflow → Volatilität: {result['correlations']['inflow_to_volatility']}")
    print(f"Outflow → Volatilität: {result['correlations']['outflow_to_volatility']}")
    
    # Key Findings
    print("\n--- KEY FINDINGS ---")
    findings = result['key_findings']
    print(f"✓ Hoher Inflow erhöht Volatilität: {findings['high_inflow_increases_volatility']}")
    print(f"✓ Selling Pressure ist volatiler: {findings['selling_pressure_more_volatile']}")
    print(f"✓ Inflow bearish bestätigt: {findings['inflow_bearish_confirmed']}")
    
    return result


async def main():
    """
    Hauptfunktion: Führt alle WII-Analysen aus
    """
    print("\n" + "="*80)
    print("WII (WHALE INTENT INDEX) - WISSENSCHAFTLICHE ANALYSE")
    print("="*80)
    print("\nDiese Analyse untersucht:")
    print("1. Lead-Lag-Korrelationen (Folgt Preis auf Flows?)")
    print("2. Regime Detection (Marktphasen)")
    print("3. Conditional Volatility (Flow-abhängige Volatilität)")
    print("\nDatenquelle: GitHub - daily_metrics.json")
    print("="*80)
    
    # Service initialisieren
    service = WAIService()
    
    try:
        # 1. Lead-Lag-Analyse
        lead_lag = await run_lead_lag_analysis(service, max_lag=7)
        
        # 2. Regime Detection
        regime = await run_regime_detection(service)
        
        # 3. Conditional Volatility
        cond_vol = await run_conditional_volatility(service)
        
        # Executive Summary
        print("\n" + "="*80)
        print("EXECUTIVE SUMMARY")
        print("="*80)
        
        print("\n--- Marktverhalten ---")
        print(f"Inflow-Effekt: {'Bearish ✓' if lead_lag['key_findings']['inflow_bearish'] else 'Nicht signifikant bearish'}")
        print(f"Outflow-Effekt: {'Bullish ✓' if lead_lag['key_findings']['outflow_bullish'] else 'Nicht signifikant bullish'}")
        print(f"WII Prädiktiv: {'Ja ✓' if lead_lag['key_findings']['wii_predictive'] else 'Eingeschränkt'}")
        print(f"Bester Prädiktor: {lead_lag['key_findings']['best_predictor']}")
        
        print("\n--- Aktueller Markt ---")
        print(f"Regime: {regime['current_regime']['interpretation']}")
        print(f"Häufigkeit: {regime['current_regime']['percentage']}% der Zeit")
        
        print("\n--- Volatilitäts-Verhalten ---")
        print(f"Hoher Inflow erhöht Volatilität: {'Ja ✓' if cond_vol['key_findings']['high_inflow_increases_volatility'] else 'Nein'}")
        print(f"Selling Pressure volatiler: {'Ja ✓' if cond_vol['key_findings']['selling_pressure_more_volatile'] else 'Nein'}")
        
        # Optional: Ergebnisse speichern
        print("\n" + "="*80)
        save = input("\nErgebnisse als JSON speichern? (j/n): ")
        if save.lower() == 'j':
            output = {
                'lead_lag_analysis': lead_lag,
                'regime_detection': regime,
                'conditional_volatility': cond_vol,
                'executive_summary': {
                    'inflow_effect': 'Bearish' if lead_lag['key_findings']['inflow_bearish'] else 'Nicht signifikant',
                    'outflow_effect': 'Bullish' if lead_lag['key_findings']['outflow_bullish'] else 'Nicht signifikant',
                    'current_regime': regime['current_regime']['interpretation'],
                    'wii_predictive': lead_lag['key_findings']['wii_predictive'],
                    'best_predictor': lead_lag['key_findings']['best_predictor']
                }
            }
            
            filename = 'analysis/wii_analysis_results.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Ergebnisse gespeichert in: {filename}")
        
        print("\n" + "="*80)
        print("ANALYSE ABGESCHLOSSEN")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Fehler bei der Analyse: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Asyncio Event Loop ausführen
    asyncio.run(main())
