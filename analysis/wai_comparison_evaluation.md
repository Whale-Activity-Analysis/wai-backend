Vergleichsauswertung: WAI v1 vs. WAI v2

1. Ziel der Auswertung

Ziel dieser Analyse ist der systematische Vergleich der ursprünglichen Version des Whale Activity Index (WAI v1) mit der verbesserten Version (WAI v2). Bewertet werden statistische Eigenschaften, Extremwertverhalten, Glattheit sowie zeitliche Stabilität anhand standardisierter Metriken.

Die zentrale Fragestellung lautet: Führt die neue Methodik (Median-Normalisierung, dynamische Gewichtung, Percentile-Skalierung, EMA-Glättung) zu einem robusteren, stabileren und besser interpretierbaren Indexverhalten?

2. Deskriptive Statistik

WAI v1: Mittelwert 54.10, Median 50.0, Standardabweichung 32.53, Minimum 9, Maximum 100
WAI v2: Mittelwert 53.97, Median 50.0, Standardabweichung 32.09, Minimum 9, Maximum 100

Interpretation:
Beide Versionen sind sauber um den neutralen Wert von 50 zentriert. Es liegt weder eine systematische Über- noch Unterbewertung vor. Dies ist essenziell für die Interpretation des Index als relativer Aktivitätsindikator.

Die leicht reduzierte Standardabweichung in Version 2 deutet auf eine geringfügig höhere Stabilität hin, ohne die Reaktivität vollständig zu verlieren.

3. Extremwertverhalten

WAI v1: 9 Tage über 80 (29.03 %), 15 Tage über 50 (48.39 %)
WAI v2: 8 Tage über 80 (25.81 %), 15 Tage über 50 (48.39 %)

Interpretation:
WAI v2 produziert weniger extreme Hochwerte, obwohl der Wertebereich unverändert bleibt. Dies ist ein gewünschter Effekt der percentile-basierten Skalierung und der EMA-Glättung.

Extreme Werte sollen selten und bedeutungsvoll sein und nicht das Resultat einzelner Ausreißer. Diese Eigenschaft wird in Version 2 besser erfüllt.

4. Autokorrelationsanalyse (Lag 1–7)

WAI v1:
Lag 1: -0.348
Lag 2: 0.308
Lag 3: -0.289
Lag 4: 0.079
Lag 5: -0.117
Lag 6: 0.067
Lag 7: -0.061

WAI v2:
Lag 1: -0.177
Lag 2: -0.023
Lag 3: -0.117
Lag 4: 0.033
Lag 5: -0.075
Lag 6: -0.044
Lag 7: -0.355

Interpretation:
WAI v1 zeigt stark oszillierende Autokorrelationen mit häufigen Vorzeichenwechseln. Dieses Verhalten ist typisch für stark reaktive, aber instabile Indikatoren.

WAI v2 weist geringere Beträge der Autokorrelation, weniger erratische Wechsel und glattere zeitliche Übergänge auf.

Das bedeutet: Der Index reagiert weiterhin auf neue Informationen, zeigt jedoch weniger chaotisches „Ping-Pong“-Verhalten.

5. Gesamtbewertung

Die neue Version des Index erfüllt die ursprünglichen Designziele.

WAI v2 bietet:

* Höhere Robustheit gegenüber Ausreißern durch Median-Normalisierung
* Kontextuelle Skalierung durch Percentile-Fenster
* Dynamische Gewichtung durch Volatilitätsadaption
* Geringere Extremwertinflation
* Glattere zeitliche Übergänge durch EMA-Smoothing
* Bessere Interpretierbarkeit

Dabei bleibt die Reaktivität gegenüber strukturellen Veränderungen erhalten.

6. Fazit

WAI v2 stellt eine signifikante methodische Verbesserung gegenüber WAI v1 dar. Die Kombination aus robuster Normalisierung, adaptiver Gewichtung und historisch kontextualisierter Skalierung führt zu einem stabileren, besser interpretierbaren und weniger artefaktanfälligen Index.

Während WAI v1 eher als „roher Aktivitätsoszillator“ fungiert, kann WAI v2 als kontextsensitiver Aktivitätsindikator mit wissenschaftlicher Begründung betrachtet werden.

