# Technische Dokumentation: Whale Activity Index v2 (WAI_v2)

## 1. Motivation

### 1.1 Limitationen der Originalversion

Die erste WAI-Version basiert auf einer linearen Skalierung mit statischen Gewichten (0.5 / 0.5):

$$\text{WAI}_{\text{v1}} = \text{round}(100 \cdot (0.5 \cdot \hat{T}_d + 0.5 \cdot \hat{V}_d))$$

Diese Formulierung weist mehrere konzeptionelle Schwächen auf:

1. **Fehlende Volatilitätsadaption:** Die konstante Gewichtung ignoriert unterschiedliche Stabilitäten der Input-Metriken. Volumen-Daten können höhere Ausreißer aufweisen als Transaktionszahlen.

2. **Unkalibrierte Absolutskalierung:** Die Multiplikation mit 100 basiert auf ad-hoc-Annahmen, nicht auf historischen Perzentilanken.

3. **Fehlende Marktkontext-Sensitivity:** Der Index reagiert nicht auf absolute vs. relative Magnitude von Whale-Aktivität innerhalb längerfristiger Trends.

### 1.2 Ziel von WAI_v2

Die neue Version adressiert diese Limitationen durch:
- **Adaptive Volatilitätsgewichtung:** Dynamische Verteilung basierend auf Volumen-Volatilität
- **Percentile-basierte Skalierung:** Historisch kontextualisierte Rang-Normalisierung
- **Robuste Basislinie:** Optional EWMA/Median statt SMA zur Reduktion von Ausreißereffekten

---

## 2. Mathematische Definition WAI_v2

### 2.1 Input-Normalisierung

Gegeben sei eine Zeitserie von Whale-Metriken für Tag $d$:
- $T_d$ = Anzahl Whale-Transaktionen
- $V_d$ = Gesamtvolumen Whale-Transaktionen (BTC)

Die Normalisierung erfolgt durch eine adaptive Basislinie $B(.)$:

$$\hat{T}_d = \frac{T_d}{B_T(d)}$$

$$\hat{V}_d = \frac{V_d}{B_V(d)}$$

wobei $B(d)$ die Basislinie zum Zeitpunkt $d$ darstellt.

**Basislinie-Varianten:**
- SMA: $B_T(d) = \text{SMA}_{30}(T)$
- EWMA: $B_T(d) = \text{EWMA}_{\text{span}=30}(T)$
- Median: $B_T(d) = \text{Median}_{30}(T)$

### 2.2 Volatilitätsabhängige Gewichtung

Die Volatilität der Volumen-Normalisierung wird quantifiziert als:

$$\sigma_V(d) = \text{std}(\hat{V}_{[d-29:d]})$$

Normalisierung der Volatilität auf [0,1] via Percentile Rank innerhalb eines 30-Tage-Fensters:

$$\rho_{\sigma}(d) = \text{PercentileRank}(\sigma_V(d), \text{window}=30)$$

Die dynamischen Gewichte ergeben sich aus:

$$w_V(d) = \rho_{\sigma}(d)$$

$$w_T(d) = 1 - \rho_{\sigma}(d)$$

**Interpretation:** Höhere Volumen-Volatilität führt zu geringerem Volumen-Gewicht, da Transaktionszahlen zuverlässiger sind.

### 2.3 Gewichtete Rohindex-Berechnung

$$\text{WAI}_{\text{raw}}(d) = w_T(d) \cdot \hat{T}_d + w_V(d) \cdot \hat{V}_d$$

wobei $w_T(d) + w_V(d) = 1$ für alle $d$.

### 2.4 Historisch adaptive Skalierung

Der Rohindex wird normalisiert auf [0, 1] via 180-Tage Percentile Rank:

$$\text{WAI}_{\text{percentile}}(d) = \text{PercentileRank}(\text{WAI}_{\text{raw}}(d), \text{window}=180)$$

Diese Funktion berechnet den Rang des aktuellen Wertes $\text{WAI}_{\text{raw}}(d)$ innerhalb der letzten 180 Werte:

$$\text{PercentileRank}(x, W) = \frac{\#\{w \in W : w \leq x\}}{|W|}$$

### 2.5 Finale Ausgabe

Die finale Indexskalierung auf [0, 100] erfolgt linear:

$$\text{WAI}_{\text{v2}}(d) = \text{round}(100 \cdot \text{WAI}_{\text{percentile}}(d))$$

**Resultat:** $\text{WAI}_{\text{v2}} \in [0, 100]$ als Ganzzahl.

### 2.6 Kompakte Formulierung

$$\text{WAI}_{\text{v2}}(d) = \text{round}\left(100 \cdot \text{PR}_{180}\left(w_T(d) \cdot \hat{T}_d + w_V(d) \cdot \hat{V}_d\right)\right)$$

wobei:
- $\text{PR}_{w}(x)$ = Percentile Rank mit Fenster-Größe $w$
- $w_T(d) = 1 - \text{PR}_{30}(\text{std}(\hat{V}_{[d-29:d]}))$

---

## 3. Vorteile gegenüber WAI_v1

### 3.1 Robustheit gegen Ausreißer

Durch percentile-basierte Skalierung sind extreme Werte weniger dominierend. Ein einzelner Spitzentag führt nicht automatisch zu Wert 100.

**Numerisches Beispiel:**
- v1: Spike führt zu $\text{WAI} = 100$ bei 3× Durchschnitt
- v2: Spike erhält Rang basierend auf historischen Top-25-Tagen → differenzierte Bewertung

### 3.2 Adaptive Volatilitätsgewichtung

Die Gewichte passen sich an Marktbedingungen an:
- Volatiles Volumen-Umfeld: TX stärker gewichtet
- Stabiles Volumen: Volumen vollständig genutzt

Dies reduziert False Positives bei Volumen-Noisen.

### 3.3 Historischer Kontext

Percentile-basierte Skalierung berücksichtigt die Häufigkeit von Hochaktivitätsphasen. In bullish-Perioden werden extreme Werte häufiger → relative Skalierung ist sinnvoller.

### 3.4 Transparente Gewichtsausgabe

Die API gibt dynamische Gewichte direkt aus, ermöglicht Post-hoc-Audit und externe Validierung.

### 3.5 Flexibilität in der Basislinie

Konfigurierbare Baseline (SMA/EWMA/Median) erlaubt Anpassung an spezifische Anforderungen:
- SMA: Schnelle Reaktion
- EWMA: Trend-Sensitivität
- Median: Maximum Robustheit

---

## 4. Limitationen und offene Fragen

### 4.1 Fenster-Parameter-Abhängigkeit

Die Wahl von Fenster-Größen ist nicht vollständig theoretisch begründet:

| Parameter | Wert | Begründung | Sensitivität |
|-----------|------|-----------|--------------|
| SMA_WINDOW | 30 | Konvention (~1 Monat) | Hoch |
| PERCENTILE_WINDOW | 180 | Konvention (~6 Monate) | Hoch |
| VOLATILITY_WINDOW | 30 | SMA_WINDOW | Mittel |

Eine empirische Optimierung (z.B. via Sharpe Ratio) wäre wünschenswert.

### 4.2 Zirkularität bei frühen Daten

In den ersten 180 Tagen ist das Percentile-Fenster unvollständig. Die `fillna(0)` Strategie ist pragmatisch, aber konzeptionell schwach.

**Alternative:** Adaptive Fenster-Größe für $d < 180$.

### 4.3 Keine explizite Zeitstrukturierung

Der Index behandelt alle historischen Tage gleich. Ein exponentiell abklingendes Fenster könnte jüngere Daten bevorzugen.

### 4.4 Annahme: Unabhängigkeit der Metriken

Die Gewichtungsfunktion nimmt an, dass Volumen-Volatilität unabhängig von TX-Volatilität ist. In Realität können beide korreliert sein.

$$\text{Cov}(\text{std}(\hat{T}), \text{std}(\hat{V})) \neq 0 \text{ möglich}$$

Eine multivariate Faktorisierung wäre robuster.

### 4.5 Percentile Rank: Diskontinuitäten

Bei vielen identischen Werten können Percentile Rank Stufen aufweisen. Glättung via linearer Interpolation könnte sinnvoll sein.

---

## 5. Validierungsstrategie

### 5.1 Empirische Tests

```
Test: Vergleich WAI_v1 vs. WAI_v2 auf historischen Daten
- Metriken: Volatilität, Autokorrelation, Extremwertfrequenz
- Ziel: WAI_v2 sollte glatter, aber sensibel für Regime-Wechsel sein
```

### 5.2 Backtesting gegen externe Events

```
Test: Korrelation mit bekannten Whale-Events (z.B. große Transfers)
- Ziel: WAI_v2 sollte bei echten Whale-Aktivitäten ansteigen
```

### 5.3 Sensitivitätsanalyse

```
Test: Variation der Fenster-Parameter (±25%)
- Ziel: Ergebnisse sollten robust gegen kleine Parameter-Variationen sein
```

---

## 6. Conclusion

WAI_v2 stellt eine konzeptionell verbesserte Version dar, die durch adaptive Gewichtung und percentile-basierte Skalierung robustere Signals liefert. Die Flexibilität in Baseline-Wahl und explizite Gewichtsausgabe fördern Transparenz und Validierbarkeit.

Limitationen in der Fenster-Parameterisierung und frühen Daten-Behandlung sollten in zukünftigen Iterationen adressiert werden.

---

## Literatur & Referenzen

- Welford, B. P. (1962). "Note on a method for calculating corrected sums of squares and products." Technometrics.
- Hunter, J. D. (2007). "Matplotlib: A 2D graphics environment." Computing in Science & Engineering.
- Pandas Development Team. "pandas: powerful Python data analysis toolkit."

---

**Version:** 1.0  
**Datum:** 2025-12-29  
**Autor:** WAI Backend Team  
**Status:** Draft
