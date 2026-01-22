# WAI & WII Dokumentation

## Was ist WAI?

Der **Whale Activity Index (WAI)** misst, **wie aktiv** Bitcoin-Whales sind.

- **WAI = 0-30:** Sehr niedrige Aktivität
- **WAI = 30-70:** Normale Aktivität  
- **WAI = 70-100:** Sehr hohe Aktivität

**Beispiel:** Wenn 100 große Transaktionen an einem Tag stattfinden und das viel mehr ist als im Durchschnitt, steigt WAI.

## Was ist WII?

Der **Whale Intent Index (WII)** zeigt, **was Whales vorhaben** - kaufen oder verkaufen?

Basis: Wohin fließt das Bitcoin?

- **Zu Exchanges** → Whales wollen **verkaufen** → WII niedrig (< 30)
- **Von Exchanges weg** → Whales wollen **halten/kaufen** → WII hoch (> 70)

**Beispiel:**
- Tag 1: 500 BTC zu Exchange = Verkaufsdruck
- Tag 2: 800 BTC von Exchange weg = Akkumulation

## Kombiniert: WAI + WII

Die Kombination sagt viel:

| WAI | WII | Bedeutung |
|-----|-----|-----------|
| Hoch | Hoch | **Bullish!** Viele Whales kaufen aktiv |
| Hoch | Niedrig | **Bearish!** Viele Whales verkaufen aktiv |
| Niedrig | Hoch | Whales kaufen im Verborgenen |
| Niedrig | Niedrig | Alle warten/desinteressiert |

## Wie wird WAI berechnet?

1. **Basis:** Transaktionsanzahl + Volumen der Whales
2. **Gewicht:** Dynamisch angepasst an Marktbedingungen
3. **Vergleich:** Wie viel mehr als normal?
4. **Skala:** 0-100 für einfache Interpretation
5. **Smoothing:** 7-Tage-Glättung gegen Rauschen

## Wie wird WII berechnet?

1. **Messung:** Inflow (zu Exchange) vs. Outflow (von Exchange)
2. **Ratio:** (Outflow - Inflow) / Total Flow
3. **Normalisierung:** -1 bis +1 → 0 bis 100
4. **Historischer Kontext:** Wie ist das im Vergleich zu den letzten 180 Tagen?
5. **Smoothing:** 7-Tage-Glättung

## API-Endpunkte

Alle Daten kombiniert abrufen:

```bash
# Aktuellste Daten
curl http://localhost:8000/api/wai/latest

# Historie (z.B. letzte 30 Tage)
curl http://localhost:8000/api/wai/history?limit=30

# Statistiken
curl http://localhost:8000/api/wai/statistics
```

## Beispiel-Response

```json
{
  "date": "2026-01-19",
  "wai": 67,
  "wii": 75,
  "wii_signal": "accumulation",
  "tx_count": 10,
  "volume": 3320.58,
  "exchange_inflow": 514.84,
  "exchange_outflow": 1200.00,
  "exchange_netflow": 685.16,
  "btc_close": 104500.23
}
```

**Interpretation:**
- WAI = 67: Moderat hohe Whale-Aktivität
- WII = 75: Whales akkumulieren (viel Outflow)
- BTC Close: 104.500 USD

## Trading-Ideen

### Einfache Strategie

```
Wenn WII > 70 (Accumulation):
  → Whales kaufen
  → Erwarte Preisanstieg in den nächsten Tagen
  → Überprüfe mit /analysis/wii_validation.py

Wenn WII < 30 (Selling Pressure):
  → Whales verkaufen
  → Erwarte Preisrückgang
```

### Mit WAI kombiniert

```
Wenn WAI > 65 UND WII > 70:
  → Bull Signal! Aggressive Akkumulation
  
Wenn WAI > 65 UND WII < 30:
  → Bear Signal! Distribution läuft
```

## Wo bekomme ich die Daten?

Die Daten für WAI/WII kommen von:
- **On-Chain-Daten:** Blockchain-Analyse von Exchange-Wallets
- **Quelle:** GitHub (siehe config.py)
- **Update:** Täglich

## Nächste Schritte

1. **Server starten:**
   ```bash
   python main.py
   ```

2. **Daten abrufen:**
   ```bash
   curl http://localhost:8000/api/wai/latest
   ```

3. **Analysen laufen:**
   ```bash
   python analysis/wii_validation.py
   ```

## Fragen?

- Siehe `/analysis/*.md` für Detailinformationen
- Siehe `/analysis/*.py` für Beispielanalysen

---

**Bottom Line:**
- WAI sagt: "Wie viel passiert?"
- WII sagt: "Kaufen oder verkaufen?"
- Zusammen: Vollständiges Bild der Whale-Aktivität
