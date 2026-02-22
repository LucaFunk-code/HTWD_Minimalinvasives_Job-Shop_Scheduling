# Tabu Search Solver

Dieses Verzeichnis enthält alle Skripte für den **Tabu Search Solver**.

---

## 🚀 Erstes Setup (Für neue Entwickler)

### 1️⃣ Python Dependencies installieren

```bash
# Virtuelle Umgebung erstellen (empfohlen)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# oder: venv\Scripts\activate  # Windows

# Pakete installieren
pip install pandas matplotlib simpy pulp ortools editdistance scipy sqlalchemy colorama scikit-learn python-dotenv seaborn tomli
```

### 2️⃣ Datenbank initialisieren

Die Datenbank muss **einmalig** mit Beispieldaten (Fisher & Thompson 10x10) initialisiert werden:

```bash
# Von der Projekt-Root aus:
python 00_Problem_Generation/all.py
```

**Was passiert:**
1. `00_data_preprocessing.py` - Liest CSV-Daten aus `data/basic/`
2. `01_insert_data_source.py` - Erstellt Datenbank-Schema und fügt Data Source ein
3. `02_insert_jobs_based_on_max_utilization.py` - Generiert Jobs basierend auf Auslastung
4. `03_update_jobs_due_dates_and_insert_corresponding_machines.py` - Berechnet Due Dates

**Output:**
- `experiments.db` - SQLite-Datenbank mit allen Jobs und Maschinen

### 3️⃣ Erstes Experiment ausführen

```bash
# Makespan-Optimierung
python tabu/run_single_ft10.py

# Ergebnisse analysieren
python tabu/analyze_improvements.py
```

✅ **Fertig!** Du solltest jetzt Experiment-Ergebnisse in `data/output/` sehen.

---

## 🚀 Experimente ausführen

### Makespan-Optimierung
Minimiert die Gesamtfertigstellungszeit (Cmax):
```bash
python tabu/run_single_ft10.py
```

### Termintreue-Optimierung
Minimiert Tardiness, Earliness und Deviation:
```bash
python tabu/run_single_lateness.py
```

### Parallele Experimente
Führt mehrere Experimente parallel aus:
```bash
python tabu/run_parallel.py
# oder
bash tabu/run_parallel.sh
```

---

##  Analyse & Auswertung

### Verbesserungen analysieren ⭐
Zeigt Initial vs. Final Makespan mit Zeiten:
```bash
python tabu/analyze_improvements.py [experiment_id]
```
**Output:**
- `data/output/tabu_improvements_summary.csv`
- Statistiken pro Schicht

### Parameter-Analyse
Analysiert Tabu-Search-Parameter (Tabu-Länge, Iterationen):
```bash
python tabu/analyze_parameters.py
```

### Lateness-Vergleich
Vergleicht verschiedene Lateness-Experimente:
```bash
python tabu/compare_lateness.py [exp_id1] [exp_id2] ...
```

---

##  Visualisierung

### Makespan-Plot
```bash
python tabu/plot_makespan.py [experiment_id]
```

### Lateness-Plot
```bash
python tabu/plot_lateness.py [experiment_id]
```

---

##  Konfiguration

Alle Experimente verwenden diese Parameter (anpassbar in den Skripten):

- **TABU_ALLOWED**: Tabu-Listen-Länge (default: 100)
- **MAX_ITERS**: Maximale Iterationen (default: 20)
- **PATIENCE**: Early-Stopping Geduld (default: 10)
- **TOP_K**: Top-K Nachbarn evaluieren (default: 10)

---
##  Weitere Dokumentation

- [TABU_OBJECTIVES_README.md](../TABU_OBJECTIVES_README.md) - Zielfunktionen erklärt
- [TABU_IMPROVEMENTS_README.md](../TABU_IMPROVEMENTS_README.md) - Improvement Tracking

---

##  Für Entwickler

**Kern-Implementation:**
- `src/solvers/Tabu_Solver.py` - Tabu Search Algorithmus
- `src/Tabu_Experiment_Runner.py` - Experiment-Runner mit Shift-Logik

**Wichtige Funktionen:**
- Zwei Zielfunktionen: Makespan und Lateness-Deviation
- Shift-basierte Experimente (wie CP-Solver)
- Improvement-Tracking (Initial → Final)

---

## 🔧 Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'pandas'`
**Lösung:** Dependencies installieren (siehe Setup Schritt 1)

### Problem: `No improvement files found in data/output/`
**Lösung:** Erst ein Experiment ausführen:
```bash
python tabu/run_single_ft10.py
```

### Problem: Datenbank-Fehler beim Experiment-Start
**Lösung:** Datenbank initialisieren (siehe Setup Schritt 2):
```bash
python 00_Problem_Generation/all.py
```

### Problem: Skripte finden `data/output/` nicht
**Lösung:** Immer von der **Projekt-Root** aus ausführen:
```bash
# Von Root aus:
python tabu/run_single_ft10.py
# NICHT von tabu/ Verzeichnis aus
```

### Problem: `experiments.db` ist leer oder fehlt
**Lösung:** Datenbank neu initialisieren:
```bash
rm experiments.db  # Alte DB löschen
python 00_Problem_Generation/all.py  # Neu generieren
```
