"""
WII Validierung: Validiert konkrete Hypothesen

Frage: Wenn WII auf Accumulation geht (>70), folgt ein höherer BTC-Preis danach?

Analysiert:
- Accumulation Days (WII > 70): Durchschnittlicher Preis die nächsten 1-7 Tage
- Selling Pressure Days (WII < 30): Durchschnittlicher Preis die nächsten 1-7 Tage
- Grafische Darstellung mit matplotlib

Run: python analysis/wii_validation.py
"""

import sys
import os
import pandas as pd
import numpy as np
import json
from typing import Dict

# Füge Parent-Verzeichnis zum Path hinzu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  matplotlib nicht installiert. Nur Text-Output.")


def load_wai_history():
    """Lädt die lokalen WAI-History-Daten"""
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'wai_history.json')
    
    with open(data_path, 'r') as f:
        json_data = json.load(f)
    
    df = pd.DataFrame(json_data['data'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    return df


def calculate_wii_returns(df: pd.DataFrame, lookback_days: list) -> Dict:
    """
    Berechnet Return-Statistiken für WII Signale.
    Diese Methode enthält die Validierungslogik.
    
    Args:
        df: DataFrame mit 'wii' und 'btc_close'
        lookback_days: Liste von Tagen [3, 7, 10]
    
    Returns:
        Dict mit Statistiken pro Signal-Typ und Zeithorizont
    """
    def calculate_returns(indices, days):
        """Berechnet Returns, nutzt verfügbare Tage wenn < days Tage verfügbar"""
        returns = []
        for idx in indices:
            end_idx = min(idx + days, len(df) - 1)
            if end_idx > idx:
                future_prices = df.iloc[idx+1:end_idx+1]['btc_close'].values
                if len(future_prices) > 0:
                    avg_future_price = np.mean(future_prices)
                    current_price = df.iloc[idx]['btc_close']
                    return_val = (avg_future_price - current_price) / current_price
                    returns.append(return_val)
        return returns
    
    # Signale identifizieren
    accumulation_indices = df[df['wii'] > 70].index.tolist()
    selling_indices = df[df['wii'] < 30].index.tolist()
    neutral_indices = df[(df['wii'] >= 30) & (df['wii'] <= 70)].index.tolist()
    
    result = {
        'data_points': len(df),
        'date_range': {
            'start': df.iloc[-1]['date'].strftime('%Y-%m-%d'),
            'end': df.iloc[0]['date'].strftime('%Y-%m-%d')
        },
        'accumulation': {
            'count': len(accumulation_indices),
            'signal': 'WII > 70 (Whales Kaufen)',
            'returns': {}
        },
        'selling_pressure': {
            'count': len(selling_indices),
            'signal': 'WII < 30 (Whales Verkaufen)',
            'returns': {}
        },
        'neutral': {
            'count': len(neutral_indices),
            'signal': 'WII 30-70 (Neutral)',
            'returns': {}
        }
    }
    
    # Berechne Stats für jeden Zeithorizont
    for days in lookback_days:
        # Accumulation
        acc_returns = calculate_returns(accumulation_indices, days)
        if acc_returns:
            avg = np.mean(acc_returns)
            win_rate = sum(1 for r in acc_returns if r > 0) / len(acc_returns)
            result['accumulation']['returns'][f'{days}d'] = {
                'avg_return_pct': round(avg * 100, 2),
                'win_rate_pct': round(win_rate * 100, 1),
                'sample_size': len(acc_returns)
            }
        
        # Selling Pressure
        sell_returns = calculate_returns(selling_indices, days)
        if sell_returns:
            avg = np.mean(sell_returns)
            decline_rate = sum(1 for r in sell_returns if r < 0) / len(sell_returns)
            result['selling_pressure']['returns'][f'{days}d'] = {
                'avg_return_pct': round(avg * 100, 2),
                'decline_rate_pct': round(decline_rate * 100, 1),
                'sample_size': len(sell_returns)
            }
        
        # Neutral
        neut_returns = calculate_returns(neutral_indices, days)
        if neut_returns:
            avg = np.mean(neut_returns)
            result['neutral']['returns'][f'{days}d'] = {
                'avg_return_pct': round(avg * 100, 2),
                'sample_size': len(neut_returns)
            }
    
    return result


def generate_marketing_message(stats: Dict) -> str:
    """
    Generiert Marketing-Text basierend auf echten Accuracies.
    Berechnet Durchschnitt über alle Lookback-Perioden pro Signal-Typ.
    """
    messages = []
    
    # ACCUMULATION: Durchschnittliche Win Rate über 3d, 7d, 14d
    acc_stats = stats['accumulation']['returns']
    if acc_stats:
        win_rates = []
        for day_key in ['3d', '7d', '14d']:
            if day_key in acc_stats:
                win_rates.append(acc_stats[day_key].get('win_rate_pct', 0))
        if win_rates:
            avg_win_rate = sum(win_rates) / len(win_rates)
            if avg_win_rate > 40:  # Nur zeigen wenn signifikant
                messages.append(f"WII Accumulation: {avg_win_rate:.0f}% Hitrate")
    
    # SELLING_PRESSURE: Durchschnittliche Decline Rate über 3d, 7d, 14d
    sell_stats = stats['selling_pressure']['returns']
    if sell_stats:
        decline_rates = []
        for day_key in ['3d', '7d', '14d']:
            if day_key in sell_stats:
                decline_rates.append(sell_stats[day_key].get('decline_rate_pct', 0))
        if decline_rates:
            avg_decline_rate = sum(decline_rates) / len(decline_rates)
            if avg_decline_rate > 50:  # Nur zeigen wenn signifikant
                messages.append(f"WII Selling: {avg_decline_rate:.0f}% Accuracy")
    
    # GESAMT-ACCURACY: Kombination aller Signale
    total_signals = (stats['accumulation']['count'] + 
                     stats['selling_pressure']['count'])
    if total_signals > 0:
        all_accuracies = []
        for key in ['accumulation', 'selling_pressure']:
            for day_key in ['3d', '7d', '14d']:
                if day_key in stats[key]['returns']:
                    if key == 'accumulation':
                        all_accuracies.append(stats[key]['returns'][day_key].get('win_rate_pct', 0))
                    else:
                        all_accuracies.append(stats[key]['returns'][day_key].get('decline_rate_pct', 0))
        if all_accuracies:
            overall_accuracy = sum(all_accuracies) / len(all_accuracies)
            if messages:
                messages.append(f"Overall: {overall_accuracy:.0f}%")
    
    return " | ".join(messages) if messages else "WII Daten werden analysiert..."

def analyze_wii_validation():
    """
    Validiert: Ist WII Signal wirklich vorhersagbar?
    Nutzt interne calculate_wii_returns() Methode für Validierungslogik.
    Speichert Stats als JSON für API-Caching.
    """
    # ===== KONFIGURATION =====
    LOOKBACK_DAYS = [3, 7, 14]
    # =========================
    
    print("\n" + "="*80)
    print("WII VALIDIERUNG - Folgt höherer BTC-Preis auf Accumulation?")
    print("="*80)
    
    # Daten laden und vorbereiten
    df_analysis = load_wai_history()
    df_analysis = df_analysis.reset_index(drop=True)
    df_analysis = df_analysis.dropna(subset=['wii', 'btc_close'])
    
    print(f"\nDatensatz: {len(df_analysis)} Tage")
    print(f"Zeitraum: {df_analysis['date'].min().date()} bis {df_analysis['date'].max().date()}\n")
    
    # Berechne Validierungsstatistiken mit interner Methode
    stats = calculate_wii_returns(df_analysis, LOOKBACK_DAYS)
    
    # === ANALYSE: Accumulation ===
    print("="*80)
    print("ACCUMULATION (WII > 70)")
    print("="*80)
    acc_stats = stats['accumulation']
    print(f"Anzahl Accumulation-Tage: {acc_stats['count']}")
    for days in LOOKBACK_DAYS:
        day_key = f'{days}d'
        if day_key in acc_stats['returns']:
            data = acc_stats['returns'][day_key]
            print(f"  {days:2d}-Tage: Ø {data['avg_return_pct']:.2f}% | Win Rate: {data['win_rate_pct']:.1f}%")
    
    # === ANALYSE: Selling Pressure ===
    print("\n" + "="*80)
    print("SELLING PRESSURE (WII < 30)")
    print("="*80)
    sell_stats = stats['selling_pressure']
    print(f"Anzahl Selling Pressure-Tage: {sell_stats['count']}")
    for days in LOOKBACK_DAYS:
        day_key = f'{days}d'
        if day_key in sell_stats['returns']:
            data = sell_stats['returns'][day_key]
            print(f"  {days:2d}-Tage: Ø {data['avg_return_pct']:.2f}% | Decline Rate: {data['decline_rate_pct']:.1f}%")
    
    # === NEUTRAL ===
    print("\n" + "="*80)
    print("NEUTRAL (WII 30-70)")
    print("="*80)
    neut_stats = stats['neutral']
    print(f"Anzahl Neutral-Tage: {neut_stats['count']}")
    for days in LOOKBACK_DAYS:
        day_key = f'{days}d'
        if day_key in neut_stats['returns']:
            data = neut_stats['returns'][day_key]
            print(f"  {days:2d}-Tage: Ø {data['avg_return_pct']:.2f}%")
    
    # === MARKETING MESSAGE ===
    print("\n" + "="*80)
    print("MARKETING MESSAGE")
    print("="*80)
    marketing_msg = generate_marketing_message(stats)
    print(f"{marketing_msg}\n")
    
    # === STATS ALS JSON SPEICHERN (für API-Caching) ===
    stats_with_msg = stats.copy()
    stats_with_msg['marketing_message'] = marketing_msg
    
    stats_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'wii_validation_stats.json')
    with open(stats_file, 'w') as f:
        json.dump(stats_with_msg, f, indent=2, default=str)
    print(f"✓ Stats gespeichert: data/wii_validation_stats.json\n")
    
    # === GRAFISCHE DARSTELLUNG ===
    if MATPLOTLIB_AVAILABLE:
        print("\n" + "="*80)
        print("GRAFIKEN WERDEN ERSTELLT...")
        print("="*80)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # Plot 1: BTC Preis mit WII Signal Färbung
        colors = ['green' if wii > 70 else 'red' if wii < 30 else 'gray' 
                  for wii in df_analysis['wii']]
        ax1.scatter(range(len(df_analysis)), df_analysis['btc_close'], c=colors, alpha=0.7, s=50, edgecolors='black', linewidth=0.5)
        ax1.plot(df_analysis['btc_close'], alpha=0.2, color='black', linewidth=1)
        ax1.set_title('BTC Preis mit Whale Intent Index (WII) Signalen', fontsize=14, fontweight='bold')
        ax1.set_ylabel('BTC Preis (USD)', fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='green', edgecolor='black', label=f"Accumulation (WII>70): {acc_stats['count']} Tage"),
            Patch(facecolor='red', edgecolor='black', label=f"Selling (WII<30): {sell_stats['count']} Tage"),
            Patch(facecolor='gray', edgecolor='black', label=f"Neutral: {neut_stats['count']} Tage")
        ]
        ax1.legend(handles=legend_elements, loc='best', fontsize=10)
        
        # Plot 2: Statistiken aus der stats-Struktur
        ax2.axis('off')
        
        stats_text = "STATISTIKEN\n" + "="*60 + "\n\n"
        
        # Accumulation Stats aus neuer Struktur
        if acc_stats['returns']:
            stats_text += f"Accumulation (WII > 70):\n"
            stats_text += f"  • Anzahl Tage: {acc_stats['count']}\n"
            for days in LOOKBACK_DAYS:
                day_key = f'{days}d'
                if day_key in acc_stats['returns']:
                    data = acc_stats['returns'][day_key]
                    stats_text += f"  • {days:2d}-Tage: Ø {data['avg_return_pct']:.2f}% | Win: {data['win_rate_pct']:.1f}%\n"
            stats_text += "\n"
        
        # Selling Stats
        if sell_stats['returns']:
            stats_text += f"Selling Pressure (WII < 30):\n"
            stats_text += f"  • Anzahl Tage: {sell_stats['count']}\n"
            for days in LOOKBACK_DAYS:
                day_key = f'{days}d'
                if day_key in sell_stats['returns']:
                    data = sell_stats['returns'][day_key]
                    stats_text += f"  • {days:2d}-Tage: Ø {data['avg_return_pct']:.2f}% | Decline: {data['decline_rate_pct']:.1f}%\n"
            stats_text += "\n"
        
        # Neutral Stats
        if neut_stats['returns']:
            stats_text += f"Neutral (WII 30-70):\n"
            stats_text += f"  • Anzahl Tage: {neut_stats['count']}\n"
            for days in LOOKBACK_DAYS:
                day_key = f'{days}d'
                if day_key in neut_stats['returns']:
                    data = neut_stats['returns'][day_key]
                    stats_text += f"  • {days:2d}-Tage: Ø {data['avg_return_pct']:.2f}%\n"
        
        ax2.text(0.05, 0.5, stats_text, fontsize=10, verticalalignment='center',
                fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8, pad=1))
        
        plt.tight_layout()
        plt.savefig('analysis/wii_validation.png', dpi=150, bbox_inches='tight')
        print(f"\n✓ Grafik gespeichert: analysis/wii_validation.png")


def main():
    """Hauptfunktion"""
    print("\n" + "="*80)
    print("WII VALIDIERUNG")
    print("="*80)
    print("\nFrage: Folgt höherer BTC-Preis auf Whale-Accumulation (WII > 70)?")
    print("Methode: Vergleiche 7-Tage-Returns nach WII-Signalen")
    print("\n" + "="*80)
    
    try:
        analyze_wii_validation()
        
        print("\n" + "="*80)
        print("ANALYSE ABGESCHLOSSEN ✓")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Fehler: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
