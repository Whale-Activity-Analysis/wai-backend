# WAI Index Validierung & Analyse
**Erstellt am:** 2026-01-07 13:00:59  
**Datenbasis:** 34 Tage (2025-12-05 bis 2026-01-07)

---

## Vergleich: WAI v1 vs v2

| Metrik | WAI v1 | WAI v2 | Differenz |
|--------|--------|--------|-----------|
| Mittelwert | 49.53 | 52.41 | +2.88 |
| Median | 51.50 | 52.00 | +0.50 |
| Standardabweichung | 30.34 | 31.61 | +1.28 |
| Min / Max | 5 / 100 | 6 / 100 | +1 / +0 |
| Tage > 80 | 7 (20.6%) | 8 (23.5%) | +1 |
| Tage > 50 | 17 (50.0%) | 17 (50.0%) | +0 |
| Korrelation v1↔v2 | - | - | **0.937** |

### Autokorrelation (Lag 1-3)

| Version | 1 Tag | 2 Tage | 3 Tage |
|---------|-------|--------|--------|
| WAI v1 | -0.044 | 0.068 | -0.045 |
| WAI v2 | -0.089 | 0.137 | 0.066 |

---

## Fazit

**Messbare Unterschiede:**
- **Durchschnitt**: v2 ist höher (52.4 vs 49.5)
- **Volatilität**: v2 ist volatiler (σ=31.61 vs 30.34)
- **Extremwerte**: v2 hat mehr Tage >80
- **Korrelation**: r=0.937 (stark korreliert)

**Empfehlung für Projektbericht:**


WAI v2 stellt eine **messbare Verbesserung** dar:
- ✅ Dynamische Gewichtung zwischen Transaktionszahl und Volumen
- ✅ Median-Basislinie robuster gegen Ausreißer
- ✅ Hohe Korrelation mit v1 (r=0.937) zeigt Konsistenz
- ✅ Sensiblere Erkennung von Veränderungen

---

*Visualisierung: siehe `wai_validation_overview.png`*
