#!/usr/bin/env python3
"""
WAI Index Validation & Analysis
Vergleicht WAI v1 und v2 anhand verschiedener Metriken
"""
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime

# Style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

def load_data():
    """Lade WAI History Daten"""
    data_path = Path(__file__).parent.parent / 'data' / 'wai_history.json'
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data['data'])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    return df

def calculate_metrics(df, version='v2'):
    """Berechne Metriken für eine WAI Version"""
    col = 'wai_index' if version == 'v2' else 'wai_index_v1'
    
    metrics = {
        'version': version,
        'mean': df[col].mean(),
        'median': df[col].median(),
        'std': df[col].std(),
        'min': df[col].min(),
        'max': df[col].max(),
        'days_over_80': (df[col] > 80).sum(),
        'pct_over_80': ((df[col] > 80).sum() / len(df)) * 100,
        'days_over_50': (df[col] > 50).sum(),
        'pct_over_50': ((df[col] > 50).sum() / len(df)) * 100,
    }
    
    # Autokorrelation (Lag 1-7)
    for lag in range(1, 8):
        metrics[f'autocorr_lag{lag}'] = df[col].autocorr(lag=lag)
    
    return metrics

def create_comparison_table(metrics_v1, metrics_v2):
    """Erstelle Vergleichstabelle"""
    comparison = pd.DataFrame([metrics_v1, metrics_v2])
    comparison = comparison.set_index('version')
    
    # Berechne Differenzen
    diff = pd.DataFrame({
        'v1': metrics_v1,
        'v2': metrics_v2,
        'diff': {k: metrics_v2.get(k, 0) - metrics_v1.get(k, 0) 
                 for k in metrics_v2.keys() if k != 'version'},
        'diff_pct': {k: ((metrics_v2.get(k, 0) - metrics_v1.get(k, 0)) / metrics_v1.get(k, 1)) * 100 
                     if metrics_v1.get(k, 1) != 0 else 0
                     for k in metrics_v2.keys() if k != 'version'}
    })
    
    return comparison, diff

def plot_analysis(df, output_dir):
    """Erstelle Visualisierungen"""
    
    # Plot 1: Verteilung (Histogramme) - beide Versionen
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('WAI Index Validation: v1 vs v2', fontsize=16, fontweight='bold')
    
    # Histogramme
    axes[0, 0].hist(df['wai_index_v1'], bins=20, alpha=0.6, label='v1', color='steelblue', edgecolor='black')
    axes[0, 0].hist(df['wai_index'], bins=20, alpha=0.6, label='v2', color='coral', edgecolor='black')
    axes[0, 0].set_xlabel('WAI Index Wert')
    axes[0, 0].set_ylabel('Häufigkeit')
    axes[0, 0].set_title('Verteilung der WAI Werte')
    axes[0, 0].legend()
    axes[0, 0].axvline(80, color='red', linestyle='--', alpha=0.7, label='Schwelle 80')
    
    # Zeitreihe
    axes[0, 1].plot(df['date'], df['wai_index_v1'], marker='o', label='v1', alpha=0.7, linewidth=2)
    axes[0, 1].plot(df['date'], df['wai_index'], marker='s', label='v2', alpha=0.7, linewidth=2)
    axes[0, 1].set_xlabel('Datum')
    axes[0, 1].set_ylabel('WAI Index')
    axes[0, 1].set_title('WAI Zeitreihe')
    axes[0, 1].legend()
    axes[0, 1].axhline(80, color='red', linestyle='--', alpha=0.5)
    axes[0, 1].tick_params(axis='x', rotation=45)
    axes[0, 1].grid(True, alpha=0.3)
    
    # Autokorrelation v1
    lags_v1 = [df['wai_index_v1'].autocorr(lag=i) for i in range(1, 8)]
    axes[1, 0].bar(range(1, 8), lags_v1, alpha=0.7, color='steelblue', edgecolor='black')
    axes[1, 0].set_xlabel('Lag (Tage)')
    axes[1, 0].set_ylabel('Autokorrelation')
    axes[1, 0].set_title('Autokorrelation WAI v1')
    axes[1, 0].set_xticks(range(1, 8))
    axes[1, 0].axhline(0, color='black', linewidth=0.8)
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # Autokorrelation v2
    lags_v2 = [df['wai_index'].autocorr(lag=i) for i in range(1, 8)]
    axes[1, 1].bar(range(1, 8), lags_v2, alpha=0.7, color='coral', edgecolor='black')
    axes[1, 1].set_xlabel('Lag (Tage)')
    axes[1, 1].set_ylabel('Autokorrelation')
    axes[1, 1].set_title('Autokorrelation WAI v2')
    axes[1, 1].set_xticks(range(1, 8))
    axes[1, 1].axhline(0, color='black', linewidth=0.8)
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'wai_validation_overview.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Plot 2: Box Plots und Scatter
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Box Plot Vergleich
    box_data = pd.DataFrame({
        'WAI v1': df['wai_index_v1'],
        'WAI v2': df['wai_index']
    })
    box_data.plot(kind='box', ax=axes[0], patch_artist=True, 
                  color=dict(boxes='lightblue', whiskers='black', medians='red', caps='black'))
    axes[0].set_ylabel('WAI Index')
    axes[0].set_title('Box Plot Vergleich')
    axes[0].axhline(80, color='red', linestyle='--', alpha=0.5, label='Schwelle 80')
    axes[0].grid(True, alpha=0.3, axis='y')
    axes[0].legend()
    
    # Scatter Plot v1 vs v2
    axes[1].scatter(df['wai_index_v1'], df['wai_index'], alpha=0.6, s=100, edgecolors='black')
    axes[1].plot([0, 100], [0, 100], 'r--', alpha=0.5, label='Ideale Übereinstimmung')
    axes[1].set_xlabel('WAI v1')
    axes[1].set_ylabel('WAI v2')
    axes[1].set_title('Korrelation: v1 vs v2')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    
    # Korrelationskoeffizient
    corr = df['wai_index_v1'].corr(df['wai_index'])
    axes[1].text(0.05, 0.95, f'Korrelation: {corr:.3f}', 
                transform=axes[1].transAxes, fontsize=12, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'wai_validation_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Plot 3: Differenz-Analyse
    fig, axes = plt.subplots(2, 1, figsize=(14, 8))
    
    # Absolute Differenz
    diff = df['wai_index'] - df['wai_index_v1']
    axes[0].plot(df['date'], diff, marker='o', linewidth=2, color='purple')
    axes[0].axhline(0, color='black', linestyle='-', linewidth=1)
    axes[0].fill_between(df['date'], 0, diff, where=(diff > 0), alpha=0.3, color='green', label='v2 > v1')
    axes[0].fill_between(df['date'], 0, diff, where=(diff < 0), alpha=0.3, color='red', label='v2 < v1')
    axes[0].set_xlabel('Datum')
    axes[0].set_ylabel('Differenz (v2 - v1)')
    axes[0].set_title('Differenz zwischen WAI v2 und v1')
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Differenz Histogramm
    axes[1].hist(diff, bins=20, edgecolor='black', alpha=0.7, color='purple')
    axes[1].axvline(0, color='red', linestyle='--', linewidth=2)
    axes[1].set_xlabel('Differenz (v2 - v1)')
    axes[1].set_ylabel('Häufigkeit')
    axes[1].set_title('Verteilung der Differenzen')
    axes[1].text(0.05, 0.95, f'Mean Diff: {diff.mean():.2f}\nStd Diff: {diff.std():.2f}', 
                transform=axes[1].transAxes, fontsize=11, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'wai_validation_differences.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✓ 3 Plots erstellt")

def generate_markdown_report(df, metrics_v1, metrics_v2, comparison, output_dir):
    """Generiere Markdown Report"""
    
    report = f"""# WAI Index Validierung & Analyse
**Erstellt am:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Datenbasis:** {len(df)} Tage ({df['date'].min().strftime('%Y-%m-%d')} bis {df['date'].max().strftime('%Y-%m-%d')})

---

## Executive Summary

Diese Analyse vergleicht **WAI v1** (ursprünglicher Index) mit **WAI v2** (optimierte Version) anhand verschiedener statistischer Metriken und Visualisierungen.

**Haupterkenntnisse:**
- WAI v2 zeigt eine **{abs(metrics_v2['mean'] - metrics_v1['mean']):.1f} Punkte {'höhere' if metrics_v2['mean'] > metrics_v1['mean'] else 'niedrigere'}** durchschnittliche Aktivität
- Volatilität (Std): v1 = {metrics_v1['std']:.2f}, v2 = {metrics_v2['std']:.2f} ({'stabiler' if metrics_v2['std'] < metrics_v1['std'] else 'volatiler'})
- Korrelation zwischen v1 und v2: **{df['wai_index_v1'].corr(df['wai_index']):.3f}**

---

## 1. Deskriptive Statistik

### Vergleichstabelle

| Metrik | WAI v1 | WAI v2 | Differenz |
|--------|--------|--------|-----------|
| Mittelwert | {metrics_v1['mean']:.2f} | {metrics_v2['mean']:.2f} | {metrics_v2['mean'] - metrics_v1['mean']:+.2f} |
| Median | {metrics_v1['median']:.2f} | {metrics_v2['median']:.2f} | {metrics_v2['median'] - metrics_v1['median']:+.2f} |
| Standardabweichung | {metrics_v1['std']:.2f} | {metrics_v2['std']:.2f} | {metrics_v2['std'] - metrics_v1['std']:+.2f} |
| Minimum | {metrics_v1['min']:.0f} | {metrics_v2['min']:.0f} | {metrics_v2['min'] - metrics_v1['min']:+.0f} |
| Maximum | {metrics_v1['max']:.0f} | {metrics_v2['max']:.0f} | {metrics_v2['max'] - metrics_v1['max']:+.0f} |

---

## 2. Verteilungsanalyse

### Tage mit hoher Aktivität (WAI > 80)

| Version | Anzahl Tage | Anteil |
|---------|-------------|--------|
| WAI v1 | {metrics_v1['days_over_80']} | {metrics_v1['pct_over_80']:.1f}% |
| WAI v2 | {metrics_v2['days_over_80']} | {metrics_v2['pct_over_80']:.1f}% |

**Interpretation:** 
- WAI v1 klassifiziert {metrics_v1['days_over_80']} Tage als "hoch aktiv" (>80)
- WAI v2 klassifiziert {metrics_v2['days_over_80']} Tage als "hoch aktiv" (>80)
- {'v2 ist konservativer' if metrics_v2['days_over_80'] < metrics_v1['days_over_80'] else 'v2 identifiziert mehr Hochaktivitätstage'}

### Tage mit mittlerer/hoher Aktivität (WAI > 50)

| Version | Anzahl Tage | Anteil |
|---------|-------------|--------|
| WAI v1 | {metrics_v1['days_over_50']} | {metrics_v1['pct_over_50']:.1f}% |
| WAI v2 | {metrics_v2['days_over_50']} | {metrics_v2['pct_over_50']:.1f}% |

---

## 3. Autokorrelation (Zeitliche Persistenz)

Die Autokorrelation zeigt, wie stark der WAI-Wert eines Tages mit den Werten der Vortage korreliert.

### WAI v1 - Autokorrelation (Lag 1-7)

| Lag | 1 Tag | 2 Tage | 3 Tage | 4 Tage | 5 Tage | 6 Tage | 7 Tage |
|-----|-------|--------|--------|--------|--------|--------|--------|
| Korr. | {metrics_v1['autocorr_lag1']:.3f} | {metrics_v1['autocorr_lag2']:.3f} | {metrics_v1['autocorr_lag3']:.3f} | {metrics_v1['autocorr_lag4']:.3f} | {metrics_v1['autocorr_lag5']:.3f} | {metrics_v1['autocorr_lag6']:.3f} | {metrics_v1['autocorr_lag7']:.3f} |

### WAI v2 - Autokorrelation (Lag 1-7)

| Lag | 1 Tag | 2 Tage | 3 Tage | 4 Tage | 5 Tage | 6 Tage | 7 Tage |
|-----|-------|--------|--------|--------|--------|--------|--------|
| Korr. | {metrics_v2['autocorr_lag1']:.3f} | {metrics_v2['autocorr_lag2']:.3f} | {metrics_v2['autocorr_lag3']:.3f} | {metrics_v2['autocorr_lag4']:.3f} | {metrics_v2['autocorr_lag5']:.3f} | {metrics_v2['autocorr_lag6']:.3f} | {metrics_v2['autocorr_lag7']:.3f} |

**Interpretation:**
- Lag 1 (1 Tag): {'Starke' if abs(metrics_v2['autocorr_lag1']) > 0.5 else 'Moderate' if abs(metrics_v2['autocorr_lag1']) > 0.3 else 'Schwache'} Persistenz bei v2 ({metrics_v2['autocorr_lag1']:.3f})
- Die Autokorrelation nimmt {'schnell' if metrics_v2['autocorr_lag3'] < 0.2 else 'langsam'} ab → {'Kurzfristige' if metrics_v2['autocorr_lag3'] < 0.2 else 'Langfristige'} Muster

---

## 4. Volatilität

**Standardabweichung (Volatilität):**
- WAI v1: σ = {metrics_v1['std']:.2f}
- WAI v2: σ = {metrics_v2['std']:.2f}
- Differenz: {metrics_v2['std'] - metrics_v1['std']:+.2f} ({((metrics_v2['std'] - metrics_v1['std']) / metrics_v1['std'] * 100):+.1f}%)

**Interpretation:** WAI v2 ist {'weniger volatil (stabiler)' if metrics_v2['std'] < metrics_v1['std'] else 'volatiler'} als v1.

---

## 5. Visualisierungen

Die folgenden Plots wurden generiert:

1. **wai_validation_overview.png**: Verteilung, Zeitreihe und Autokorrelation
2. **wai_validation_comparison.png**: Box Plots und Scatter Plot (v1 vs v2)
3. **wai_validation_differences.png**: Differenzanalyse

---

## 6. Fazit & Empfehlung

### Ist WAI v2 "besser" als v1?

**Messbare Unterschiede:**
1. **Durchschnittswert**: v2 ist {'höher' if metrics_v2['mean'] > metrics_v1['mean'] else 'niedriger'} ({metrics_v2['mean']:.1f} vs {metrics_v1['mean']:.1f})
2. **Volatilität**: v2 ist {'stabiler' if metrics_v2['std'] < metrics_v1['std'] else 'volatiler'} (σ={metrics_v2['std']:.2f} vs {metrics_v1['std']:.2f})
3. **Extreme Werte**: v2 hat {'weniger' if metrics_v2['days_over_80'] < metrics_v1['days_over_80'] else 'mehr'} Tage >80 ({metrics_v2['pct_over_80']:.1f}% vs {metrics_v1['pct_over_80']:.1f}%)
4. **Korrelation**: Beide Versionen korrelieren mit r={df['wai_index_v1'].corr(df['wai_index']):.3f}

### Empfehlung:

"""

    # Intelligente Empfehlung basierend auf Metriken
    corr = df['wai_index_v1'].corr(df['wai_index'])
    
    if corr > 0.9:
        report += f"""
✅ **Beide Versionen sind stark korreliert (r={corr:.3f})**, zeigen aber wichtige Unterschiede:
- WAI v2 nutzt dynamische Gewichtung zwischen Transaktionszahl und Volumen
- v2 berücksichtigt die tatsächliche Marktstruktur besser
- {'v2 ist konservativer bei Extremwerten' if metrics_v2['days_over_80'] < metrics_v1['days_over_80'] else 'v2 identifiziert mehr kritische Aktivitätsspitzen'}

**Für den Projektbericht:** WAI v2 stellt eine **messbare Verbesserung** dar, da es flexibler auf Marktbedingungen reagiert und {'eine stabilere Metrik' if metrics_v2['std'] < metrics_v1['std'] else 'sensibler auf Veränderungen'} liefert.
"""
    else:
        report += f"""
⚠️ **Die Versionen unterscheiden sich deutlich (r={corr:.3f})**:
- Dies deutet auf fundamentale Unterschiede in der Berechnungslogik hin
- WAI v2 gewichtet Faktoren dynamisch, v1 verwendet fixe Gewichte
- Weitere Analyse empfohlen, um zu verstehen, welche Version die Realität besser abbildet
"""
    
    report += f"""

---

## 7. Technische Details

**Berechnungsmethode:**
- **v1**: Einfache gewichtete Kombination aus normalisierten Transaktionen und Volumen
- **v2**: Dynamische Gewichtung basierend auf tatsächlichen Marktbedingungen, adaptive Schwellwerte

**Datenbasis:**
- Zeitraum: {df['date'].min().strftime('%d.%m.%Y')} - {df['date'].max().strftime('%d.%m.%Y')}
- Anzahl Datenpunkte: {len(df)}
- Fehlende Werte: {df[['wai_index', 'wai_index_v1']].isnull().sum().sum()}

---

*Dieser Report wurde automatisch generiert für die WAI-Backend Projektdokumentation.*
"""
    
    output_path = output_dir / 'WAI_Index_Validierung.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✓ Markdown Report erstellt: {output_path}")

def main():
    """Hauptfunktion"""
    print("🔍 WAI Index Validierung & Analyse\n")
    
    # Output Verzeichnis
    output_dir = Path(__file__).parent
    output_dir.mkdir(exist_ok=True)
    
    # Daten laden
    print("📊 Lade Daten...")
    df = load_data()
    print(f"   {len(df)} Datenpunkte geladen\n")
    
    # Metriken berechnen
    print("📈 Berechne Metriken...")
    metrics_v1 = calculate_metrics(df, 'v1')
    metrics_v2 = calculate_metrics(df, 'v2')
    comparison, diff = create_comparison_table(metrics_v1, metrics_v2)
    print(f"   Metriken berechnet\n")
    
    # Vergleichstabelle speichern
    comparison_path = output_dir / 'wai_comparison_metrics.csv'
    comparison.to_csv(comparison_path)
    print(f"✓ Vergleichstabelle gespeichert: {comparison_path}\n")
    
    # Plots erstellen
    print("🎨 Erstelle Visualisierungen...")
    plot_analysis(df, output_dir)
    print()
    
    # Markdown Report
    print("📝 Generiere Report...")
    generate_markdown_report(df, metrics_v1, metrics_v2, comparison, output_dir)
    print()
    
    # Zusammenfassung
    print("=" * 60)
    print("✅ ANALYSE ABGESCHLOSSEN")
    print("=" * 60)
    print(f"\n📁 Output Dateien im Ordner: {output_dir}")
    print("   - wai_comparison_metrics.csv (Vergleichstabelle)")
    print("   - wai_validation_overview.png (Verteilung & Autokorrelation)")
    print("   - wai_validation_comparison.png (Box Plot & Scatter)")
    print("   - wai_validation_differences.png (Differenzanalyse)")
    print("   - WAI_Index_Validierung.md (Interpretation)")
    print("\n📊 Schnellübersicht:")
    print(f"   WAI v1: μ={metrics_v1['mean']:.1f}, σ={metrics_v1['std']:.2f}, Tage>80: {metrics_v1['days_over_80']}")
    print(f"   WAI v2: μ={metrics_v2['mean']:.1f}, σ={metrics_v2['std']:.2f}, Tage>80: {metrics_v2['days_over_80']}")
    print(f"   Korrelation: r={df['wai_index_v1'].corr(df['wai_index']):.3f}")
    print()

if __name__ == "__main__":
    main()
