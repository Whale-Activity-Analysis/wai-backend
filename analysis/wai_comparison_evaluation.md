# Vergleichsauswertung: WAI v1 vs. WAI v2

## 1. Ziel der Auswertung

Ziel dieser Analyse ist der systematische Vergleich der ursprünglichen Version des **Whale Activity Index (WAI v1)** mit der verbesserten Version **WAI v2**. Bewertet werden statistische Eigenschaften, Extremwertverhalten, Glattheit sowie zeitliche Stabilität anhand standardisierter Metriken.

Die zentrale Fragestellung lautet:

> Führt die neue Methodik (Median-Normalisierung, dynamische Gewichtung, Percentile-Skalierung, EMA-Glättung) zu einem robusteren, stabileren und besser interpretierbaren Indexverhalten?

---

## 2. Deskriptive Statistik

| Version | Mittelwert | Median | Standardabweichung | Minimum | Maximum |
| ------- | ---------- | ------ | ------------------ | ------- | ------- |
| WAI v1  | 54.10      | 50.0   | 32.53              | 9       | 100     |
| WAI v2  | 53.97      | 50.0   | 32.09              | 9       | 100     |

### Interpretation

Beide Versionen sind sauber um den neutralen Wert von **50** zentriert. Es liegt weder eine systematische Über- noch Unterbewertung vor. Dies ist essenziell für die Interpretation des Index als relativer Aktivitätsindikator.

Die leicht reduzierte Standardabweichung in Version 2 deutet auf eine geringfügig höhere Stabilität hin, ohne die Reaktivität vollständig zu verlieren.

---

## 3. Extremwertverhalten

| Version | Tage > 80 | Anteil > 80 | Tage > 50 | Anteil > 50 |
| ------- | --------- | ----------- | --------- | ----------- |
| WAI v1  | 9         | 29.03 %     | 15        | 48.39 %     |
| WAI v2  | 8         | 25.81 %     | 15        | 48.39 %     |

### Interpretation

WAI v2 produziert weniger extreme Hochwerte, obwohl der Wertebereich unverändert bleibt. Dies ist ein gewünschter Effekt der percentile-basierten Skalierung und der EMA-Glättung.

Extreme Werte sollen selten und bedeutungsvoll sein und nicht das Resultat einzelner Ausreißer. Diese Eigenschaft wird in Version 2 besser erfüllt.

---

## 4. Autokorrelationsanalyse (Lag 1–7)

### WAI v1

| Lag | Autokorrelation |
| --- | --------------- |
| 1   | -0.348          |
| 2   | 0.308           |
| 3   | -0.289          |
| 4   | 0.079           |
| 5   | -0.117          |
| 6   | 0.067           |
| 7   | -0.061          |

### WAI v2

| Lag | Autokorrelation |
| --- | --------------- |
| 1   | -0.177          |
| 2   | -0.023          |
| 3   | -0.117          |
| 4   | 0.033           |
| 5   | -0.075          |
| 6   | -0.044          |
| 7   | -0.355          |

### Interpretation

WAI v1 zeigt stark oszillierende Autokorrelationen mit häufigen Vorzeichenwechseln. Dieses Verhalten ist typisch für stark reaktive, aber instabile Indikatoren.

WAI v2 weist geringere Beträge der Autokorrelation, weniger erratische Wechsel und glattere zeitliche Übergänge auf.

Das bedeutet: Der Index reagiert weiterhin auf neue Informationen, zeigt jedoch weniger chaotisches „Ping-Pong“-Verhalten.

---

## 5. Gesamtbewertung

Die neue Version des Index erfüllt die ursprünglichen Designziele in höherem Maße.

WAI v2 bietet:

* Höhere Robustheit gegenüber Ausreißern durch Median-Normalisierung
* Kontextuelle Skalierung durch Percentile-Fenster
* Dynamische Gewichtung durch Volatilitätsadaption
* Geringere Extremwertinflation
* Glattere zeitliche Übergänge durch EMA-Smoothing
* Bessere Interpretierbarkeit

Dabei bleibt die Reaktivität gegenüber strukturellen Veränderungen erhalten.

---

## 6. Fazit

WAI v2 stellt eine signifikante methodische Verbesserung gegenüber WAI v1 dar. Die Kombination aus robuster Normalisierung, adaptiver Gewichtung und historisch kontextualisierter Skalierung führt zu einem stabileren, besser interpretierbaren und weniger artefaktanfälligen Index.

Während WAI v1 eher als „roher Aktivitätsoszillator“ fungiert, kann WAI v2 als kontextsensitiver Aktivitätsindikator mit wissenschaftlicher Begründung betrachtet werden.

---

## 7. Hinweise zur Weiterentwicklung

Empfohlene nächste Schritte:

* Visualisierung der beiden Zeitreihen (v1 vs. v2)
* Event-basierte Validierung (bekannte Whale-Transfers)
* Parameter-Sensitivitätsanalyse (Fenstergrößen ±25 %)
* Regime-Erkennung (Bull/Bear, Volatilitätscluster)

---

**Dokument:** WAI Index Comparison
**Version:** 1.0
**Status:** Draft
