"""
WII Validierung: Validiert konkrete Hypothesen

Frage: Wenn WII auf Accumulation geht (>70), folgt ein höherer BTC-Preis danach?

Analysiert:
- Accumulation Days (WII > 70): Durchschnittlicher Preis die nächsten 1-7 Tage
- Selling Pressure Days (WII < 30): Durchschnittlicher Preis die nächsten 1-7 Tage
- Grafische Darstellung mit matplotlib

Run: python analysis/wii_validation.py
"""

import asyncio
import sys
import os
import pandas as pd
import numpy as np

# Füge Parent-Verzeichnis zum Path hinzu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wai_service import WAIService

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  matplotlib nicht installiert. Nur Text-Output.")


async def analyze_wii_validation(service: WAIService):
    """
    Validiert: Ist WII Signal wirklich vorhersagbar?
    """
    print("\n" + "="*80)
    print("WII VALIDIERUNG - Folgt höherer BTC-Preis auf Accumulation?")
    print("="*80)
    
    # Daten laden
    df = await service.fetch_daily_metrics()
    df = df.sort_values('date')
    
    # WAI und WII berechnen
    df_with_wai = service.calculate_wai(df)
    df_with_wii = service.calculate_wii(df)
    
    # Merge
    df_analysis = pd.DataFrame()
    df_analysis['date'] = df['date']
    df_analysis['wai'] = df_with_wai['wai']
    df_analysis['wii'] = df_with_wii['wii']
    df_analysis['wii_signal'] = df_with_wii['wii_signal']
    df_analysis['btc_close'] = df['btc_close']
    df_analysis['btc_return_1d'] = df['btc_return_1d']
    
    # Reset Index für einfacher Zugriff
    df_analysis = df_analysis.reset_index(drop=True)
    df_analysis = df_analysis.dropna()
    
    print(f"\nDatensatz: {len(df_analysis)} Tage\n")
    
    # === ANALYSE: Accumulation ===
    print("="*80)
    print("ACCUMULATION (WII > 70)")
    print("="*80)

    accumulation_indices = df_analysis[df_analysis['wii'] > 70].index.tolist()
    
    future_returns = []
    future_returns_sell = []
    future_returns_neutral = []
    
    if len(accumulation_indices) > 0:
        print(f"Anzahl Accumulation-Tage: {len(accumulation_indices)}")
        
        # Durchschnittliche Returns nach Accumulation
        future_returns = []
        for idx in accumulation_indices:
            if idx + 7 < len(df_analysis):
                # Returns für die nächsten 7 Tage
                future_prices = df_analysis.iloc[idx+1:idx+8]['btc_close'].values
                if len(future_prices) > 0:
                    avg_future_price = np.mean(future_prices)
                    current_price = df_analysis.iloc[idx]['btc_close']
                    return_7d = (avg_future_price - current_price) / current_price
                    future_returns.append(return_7d)
        
        if future_returns:
            avg_return = np.mean(future_returns)
            win_rate = sum(1 for r in future_returns if r > 0) / len(future_returns)
            
            print(f"Ø 7-Tage Return nach Accumulation: {avg_return*100:.2f}%")
            print(f"Win Rate (Preis höher): {win_rate*100:.1f}%")
            
            if avg_return > 0:
                print("✓ Accumulation ist mit höheren Preisen korreliert!")
            else:
                print("✗ Accumulation führt NICHT zu höheren Preisen")
    
    # === ANALYSE: Selling Pressure ===
    print("\n" + "="*80)
    print("SELLING PRESSURE (WII < 30)")
    print("="*80)
    
    selling_indices = df_analysis[df_analysis['wii'] < 30].index.tolist()
    
    if len(selling_indices) > 0:
        print(f"Anzahl Selling Pressure-Tage: {len(selling_indices)}")
        
        # Durchschnittliche Returns nach Selling Pressure
        future_returns_sell = []
        for idx in selling_indices:
            if idx + 7 < len(df_analysis):
                future_prices = df_analysis.iloc[idx+1:idx+8]['btc_close'].values
                if len(future_prices) > 0:
                    avg_future_price = np.mean(future_prices)
                    current_price = df_analysis.iloc[idx]['btc_close']
                    return_7d = (avg_future_price - current_price) / current_price
                    future_returns_sell.append(return_7d)
        
        if future_returns_sell:
            avg_return = np.mean(future_returns_sell)
            win_rate = sum(1 for r in future_returns_sell if r < 0) / len(future_returns_sell)
            
            print(f"Ø 7-Tage Return nach Selling Pressure: {avg_return*100:.2f}%")
            print(f"Decline Rate (Preis fällt): {win_rate*100:.1f}%")
            
            if avg_return < 0:
                print("✓ Selling Pressure ist mit niedrigeren Preisen korreliert!")
            else:
                print("✗ Selling Pressure führt NICHT zu niedrigeren Preisen")
    
    # === NEUTRAL ===
    print("\n" + "="*80)
    print("NEUTRAL (WII 30-70)")
    print("="*80)
    
    neutral_indices = df_analysis[(df_analysis['wii'] >= 30) & (df_analysis['wii'] <= 70)].index.tolist()
    
    if len(neutral_indices) > 0:
        print(f"Anzahl Neutral-Tage: {len(neutral_indices)}")
        
        future_returns_neutral = []
        for idx in neutral_indices:
            if idx + 7 < len(df_analysis):
                future_prices = df_analysis.iloc[idx+1:idx+8]['btc_close'].values
                if len(future_prices) > 0:
                    avg_future_price = np.mean(future_prices)
                    current_price = df_analysis.iloc[idx]['btc_close']
                    return_7d = (avg_future_price - current_price) / current_price
                    future_returns_neutral.append(return_7d)
        
        if future_returns_neutral:
            avg_return = np.mean(future_returns_neutral)
            print(f"Ø 7-Tage Return (Neutral): {avg_return*100:.2f}%")
    
    # === GRAFISCHE DARSTELLUNG ===
    if MATPLOTLIB_AVAILABLE:
        print("\n" + "="*80)
        print("GRAFIKEN WERDEN ERSTELLT...")
        print("="*80)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot 1: BTC Preis mit WII Signal Färbung (HAUPTPLOT)
        colors = ['green' if wii > 70 else 'red' if wii < 30 else 'gray' 
                  for wii in df_analysis['wii']]
        ax1.scatter(range(len(df_analysis)), df_analysis['btc_close'], c=colors, alpha=0.7, s=50, edgecolors='black', linewidth=0.5)
        ax1.plot(df_analysis['btc_close'], alpha=0.2, color='black', linewidth=1)
        ax1.set_title('BTC Preis mit Whale Intent Index (WII) Signalen', fontsize=14, fontweight='bold')
        ax1.set_ylabel('BTC Preis (USD)', fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Legend mit Statistiken
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='green', edgecolor='black', label=f'Accumulation (WII>70): {len(accumulation_indices)} Tage'),
            Patch(facecolor='red', edgecolor='black', label=f'Selling (WII<30): {len(selling_indices)} Tage'),
            Patch(facecolor='gray', edgecolor='black', label=f'Neutral: {len(neutral_indices)} Tage')
        ]
        ax1.legend(handles=legend_elements, loc='best', fontsize=10)
        
        # Plot 2: Statistiken
        ax2.axis('off')
        
        stats_text = "STATISTIKEN\n" + "="*60 + "\n\n"
        
        if future_returns:
            stats_text += f"Accumulation (WII > 70):\n"
            stats_text += f"  • Anzahl Tage: {len(accumulation_indices)}\n"
            stats_text += f"  • Ø 7-Tage Return: {np.mean(future_returns)*100:.2f}%\n"
            stats_text += f"  • Win Rate (Preis höher): {sum(1 for r in future_returns if r > 0)/len(future_returns)*100:.1f}%\n\n"
        
        if future_returns_sell:
            stats_text += f"Selling Pressure (WII < 30):\n"
            stats_text += f"  • Anzahl Tage: {len(selling_indices)}\n"
            stats_text += f"  • Ø 7-Tage Return: {np.mean(future_returns_sell)*100:.2f}%\n"
            stats_text += f"  • Decline Rate (Preis fällt): {sum(1 for r in future_returns_sell if r < 0)/len(future_returns_sell)*100:.1f}%\n\n"
        
        if future_returns_neutral:
            stats_text += f"Neutral (30-70):\n"
            stats_text += f"  • Anzahl Tage: {len(neutral_indices)}\n"
            stats_text += f"  • Ø 7-Tage Return: {np.mean(future_returns_neutral)*100:.2f}%\n"
        
        ax2.text(0.05, 0.5, stats_text, fontsize=11, verticalalignment='center',
                fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8, pad=1))
        
        plt.tight_layout()
        plt.savefig('analysis/wii_validation.png', dpi=150, bbox_inches='tight')
        print(f"\n✓ Grafik gespeichert: analysis/wii_validation.png")


async def main():
    """Hauptfunktion"""
    print("\n" + "="*80)
    print("WII VALIDIERUNG")
    print("="*80)
    print("\nFrage: Folgt höherer BTC-Preis auf Whale-Accumulation (WII > 70)?")
    print("Methode: Vergleiche 7-Tage-Returns nach WII-Signalen")
    print("\n" + "="*80)
    
    service = WAIService()
    
    try:
        await analyze_wii_validation(service)
        
        print("\n" + "="*80)
        print("ANALYSE ABGESCHLOSSEN ✓")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Fehler: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
