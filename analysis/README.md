# Solver-übergreifende Analyse

Dieses Verzeichnis enthält **Analyse-Tools**, die für alle Solver verwendet werden können.

## 📊 Analyse-Skripte

### Weight Impact Analyse ⭐
Analysiert die Auswirkungen verschiedener Gewichtungen auf Tardiness, Earliness und Deviation:

```bash
python analysis/analyze_weight_impact.py [experiment_ids...]
```

**Beispiel:**
```bash
python analysis/analyze_weight_impact.py 101 102 103
```

**Output:**
- Tardiness, Earliness, Deviation pro Experiment
- Termintreue-Score-Berechnung
- Vergleich verschiedener Gewichtungen (w_t, w_e, w_dev)

---

### Delivery Performance
Analysiert Lieferperformance über verschiedene Experimente:

```bash
python analysis/analyze_delivery_performance.py
```

---

### Run Data
Hilfsskript für Daten-Generierung:

```bash
python analysis/run_data.py
```

---

## 💡 Für Entwickler

Diese Skripte greifen auf die **Datenbank** zu und analysieren:
- `Experiment` Tabelle
- `SimulationJobs` Tabelle  
- `ScheduleJobs` Tabelle

Sie sind **solver-agnostisch** und funktionieren mit CP, Tabu und GT.
