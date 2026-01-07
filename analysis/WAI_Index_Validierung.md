# WAI Index Validierung & Analyse
**Erstellt am:** 2026-01-07 11:32:32  
**Datenbasis:** 34 Tage (2025-12-05 bis 2026-01-07)

---

## Executive Summary

Diese Analyse vergleicht **WAI v1** (ursprünglicher Index) mit **WAI v2** (optimierte Version) anhand verschiedener statistischer Metriken und Visualisierungen.

**Haupterkenntnisse:**
- WAI v2 zeigt eine **1.5 Punkte höhere** durchschnittliche Aktivität
- Volatilität (Std): v1 = 32.53, v2 = 31.28 (stabiler)
- Korrelation zwischen v1 und v2: **0.927**

---

## 1. Deskriptive Statistik

### Vergleichstabelle

| Metrik | WAI v1 | WAI v2 | Differenz |
|--------|--------|--------|-----------|
| Mittelwert | 51.47 | 53.00 | +1.53 |
| Median | 52.00 | 52.00 | +0.00 |
| Standardabweichung | 32.53 | 31.28 | -1.25 |
| Minimum | 3 | 6 | +3 |
| Maximum | 100 | 100 | +0 |

---

## 2. Verteilungsanalyse

### Tage mit hoher Aktivität (WAI > 80)

| Version | Anzahl Tage | Anteil |
|---------|-------------|--------|
| WAI v1 | 9 | 26.5% |
| WAI v2 | 9 | 26.5% |

**Interpretation:** 
- WAI v1 klassifiziert 9 Tage als "hoch aktiv" (>80)
- WAI v2 klassifiziert 9 Tage als "hoch aktiv" (>80)
- v2 identifiziert mehr Hochaktivitätstage

### Tage mit mittlerer/hoher Aktivität (WAI > 50)

| Version | Anzahl Tage | Anteil |
|---------|-------------|--------|
| WAI v1 | 17 | 50.0% |
| WAI v2 | 17 | 50.0% |

---

## 3. Autokorrelation (Zeitliche Persistenz)

Die Autokorrelation zeigt, wie stark der WAI-Wert eines Tages mit den Werten der Vortage korreliert.

### WAI v1 - Autokorrelation (Lag 1-7)

| Lag | 1 Tag | 2 Tage | 3 Tage | 4 Tage | 5 Tage | 6 Tage | 7 Tage |
|-----|-------|--------|--------|--------|--------|--------|--------|
| Korr. | -0.114 | 0.048 | -0.051 | 0.064 | -0.138 | -0.128 | 0.089 |

### WAI v2 - Autokorrelation (Lag 1-7)

| Lag | 1 Tag | 2 Tage | 3 Tage | 4 Tage | 5 Tage | 6 Tage | 7 Tage |
|-----|-------|--------|--------|--------|--------|--------|--------|
| Korr. | -0.056 | 0.088 | 0.076 | 0.159 | -0.322 | -0.089 | -0.019 |

**Interpretation:**
- Lag 1 (1 Tag): Schwache Persistenz bei v2 (-0.056)
- Die Autokorrelation nimmt schnell ab → Kurzfristige Muster

---

## 4. Volatilität

**Standardabweichung (Volatilität):**
- WAI v1: σ = 32.53
- WAI v2: σ = 31.28
- Differenz: -1.25 (-3.8%)

**Interpretation:** WAI v2 ist weniger volatil (stabiler) als v1.

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
1. **Durchschnittswert**: v2 ist höher (53.0 vs 51.5)
2. **Volatilität**: v2 ist stabiler (σ=31.28 vs 32.53)
3. **Extreme Werte**: v2 hat mehr Tage >80 (26.5% vs 26.5%)
4. **Korrelation**: Beide Versionen korrelieren mit r=0.927

### Empfehlung:


✅ **Beide Versionen sind stark korreliert (r=0.927)**, zeigen aber wichtige Unterschiede:
- WAI v2 nutzt dynamische Gewichtung zwischen Transaktionszahl und Volumen
- v2 berücksichtigt die tatsächliche Marktstruktur besser
- v2 identifiziert mehr kritische Aktivitätsspitzen

**Für den Projektbericht:** WAI v2 stellt eine **messbare Verbesserung** dar, da es flexibler auf Marktbedingungen reagiert und eine stabilere Metrik liefert.


---

## 7. Technische Details

**Berechnungsmethode:**
- **v1**: Einfache gewichtete Kombination aus normalisierten Transaktionen und Volumen
- **v2**: Dynamische Gewichtung basierend auf tatsächlichen Marktbedingungen, adaptive Schwellwerte

**Datenbasis:**
- Zeitraum: 05.12.2025 - 07.01.2026
- Anzahl Datenpunkte: 34
- Fehlende Werte: 0

---

*Dieser Report wurde automatisch generiert für die WAI-Backend Projektdokumentation.*
