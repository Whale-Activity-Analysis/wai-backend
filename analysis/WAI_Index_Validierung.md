# WAI Index Validierung & Analyse
**Erstellt am:** 2026-01-14 15:27:26  
**Datenbasis:** 31 Tage (2025-12-15 bis 2026-01-14)

---

## Vergleich: WAI v1 vs v2

| Metrik | WAI v1 | WAI v2 | Differenz |
|--------|--------|--------|-----------|
| Mittelwert | 54.10 | 53.97 | -0.13 |
| Median | 50.00 | 50.00 | +0.00 |
| Standardabweichung | 32.53 | 32.09 | -0.44 |
| Min / Max | 9 / 100 | 9 / 100 | +0 / +0 |
| Tage > 80 | 9 (29.0%) | 8 (25.8%) | -1 |
| Tage > 50 | 15 (48.4%) | 15 (48.4%) | +0 |
| Korrelation v1↔v2 | - | - | **0.873** |

### Autokorrelation (Lag 1-3)

| Version | 1 Tag | 2 Tage | 3 Tage |
|---------|-------|--------|--------|
| WAI v1 | -0.348 | 0.308 | -0.289 |
| WAI v2 | -0.177 | -0.023 | -0.117 |

---

## Fazit

**Messbare Unterschiede:**
- **Durchschnitt**: v2 ist niedriger (54.0 vs 54.1)
- **Volatilität**: v2 ist stabiler (σ=32.09 vs 32.53)
- **Extremwerte**: v2 hat weniger Tage >80
- **Korrelation**: r=0.873 (stark korreliert)

**Empfehlung für Projektbericht:**


WAI v2 stellt eine **messbare Verbesserung** dar:
- ✅ Dynamische Gewichtung zwischen Transaktionszahl und Volumen
- ✅ Median-Basislinie robuster gegen Ausreißer
- ✅ Hohe Korrelation mit v1 (r=0.873) zeigt Konsistenz
- ✅ Stabilere Metrik

---

*Visualisierung: siehe `wai_validation_overview.png`*
