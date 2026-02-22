# GitHub-Ready Cleanup Plan

## 📋 Übersicht

Dieses Dokument beschreibt den Plan, um das Projekt für zukünftige Entwickler aufzuräumen.

---

## 1️⃣ Test-Skripte (Aktuell: 3 und behalten!)

### ✅ BEHALTEN (alle 3 sind sinnvoll):

**test_scripts/00_routings_&_machines.py**
- Testet: Routing- und Machine-Queries aus der Datenbank
- Grund: Wichtig für Datenbankzugriff-Verifikation

**test_scripts/01_jobs_machine_instances.py**
- Testet: Job- und Machine-Instance-Queries
- Grund: Grundlegende Domain-Objekt-Tests

**test_scripts/02_sim_duration.py**
- Testet: Simulation Duration Berechnung
- Grund: Kritisch für Job-Shop Scheduling

✅ **Empfehlung:** Alle 3 Tests behalten - sind bereits minimal und sinnvoll!

---

## 2️⃣ Tabu Search Dateien (zu kommentieren/dokumentieren)

### 📂 Kern-Implementation (mit Docstrings versehen):

**src/solvers/Tabu_Solver.py** ⭐ HAUPTDATEI
- Status: Braucht ausführliche Dokumentation
- Aufgabe: Alle Methoden kommentieren + Klassen-Docstring verbessern

**src/Tabu_Experiment_Runner.py** ⭐ RUNNER
- Status: Braucht Dokumentation
- Aufgabe: Hauptfunktion + Parameter erklären

### 📂 Experiment-Skripte (Kurze Header-Kommentare):

**Root-Level Tabu-Skripte:**
1. `run_single_tabu_ft10.py` - Einzelexperiment Makespan
2. `run_single_tabu_lateness.py` - Einzelexperiment Termintreue
3. `run_parallel_tabu_experiments.py` - Parallele Experimente
4. `run_parallel_tabu_experiments.sh` - Bash-Wrapper

**Analyse-Skripte:**
5. `analyze_tabu_improvements.py` - Verbesserungs-Analyse
6. `analyze_tabu_parameters.py` - Parameter-Analyse
7. `compare_tabu_lateness.py` - Lateness-Vergleich
8. `plot_tabu_makespan.py` - Makespan-Visualisierung
9. `plot_tabu_lateness.py` - Lateness-Visualisierung

### 📂 Dokumentation (erweitern):

10. `TABU_IMPROVEMENTS_README.md` - Verbesserungs-Tracking
11. `TABU_OBJECTIVES_README.md` - Zielfunktionen

---

## 3️⃣ Weitere Cleanup-Aufgaben

### 🗑️ Potentiell zu entfernen (nach Rücksprache):

**Experimentelle/Einmalige Skripte:**
- `run_test_lateness_experiment.py` - Test-Script?
- `list_experiments.py` - Hilfsskript
- `show_lateness_ranking.py` - Analyse-Hilfsskript

**Alte Analyse-Skripte:**
- `analyze_weight_impact_simple.py` (redundant zu `analyze_weight_impact.py`?)
- `evaluate_results.py` (generisch, unklar)
- `generate_ergebnisuebersicht.py` (Projektseminar-spezifisch?)
- `generate_projektdokument.py` (Projektseminar-spezifisch?)

### 📝 README.md erweitern:

Neue Sektion hinzufügen:
- **Tabu Search Usage** mit Beispielen
- **Available Solvers** Übersicht
- **Running Experiments** Quick-Start

---

## 4️⃣ Dokumentations-Strategie

### A) Tabu_Solver.py - Detaillierte Kommentare

```python
class TabuSolver:
    """
    Tabu Search Solver für Job-Shop Scheduling Problem (JSP).
    
    Implementiert eine Tabu-Suche zur Optimierung von Job-Shop Schedules mit zwei
    unterstützten Zielfunktionen:
    
    1. Makespan-Minimierung: Minimiert die Gesamtfertigstellungszeit Cmax
    2. Termintreue-Optimierung: Minimiert gewichtete Summe aus Tardiness, 
       Earliness und Startzeit-Deviation
    
    Algorithmus:
    -----------
    1. Generiere zufällige Initiallösung (Job-Sequenz)
    2. Iteriere max_iters Mal:
       - Generiere Nachbar-Lösungen durch Swap-Operationen
       - Wähle besten nicht-tabu Nachbarn (auch bei Verschlechterung)
       - Speichere Swap in Tabu-Liste (verhindert Zyklen)
       - Aktualisiere beste gefundene Lösung
    3. Gebe beste Lösung zurück
    
    Parameters:
    -----------
    jobs_collection : LiveJobCollection
        Collection von Jobs mit Operationen aus der Datenbank
    logger : Logger
        Logger-Instanz für Ausgaben
    rng : Optional[random.Random]
        Random Number Generator für Reproduzierbarkeit
    objective : Literal["makespan", "lateness_deviation"]
        Zielfunktion ("makespan" oder "lateness_deviation")
    w_t : float
        Gewicht für Tardiness (nur bei lateness_deviation)
    w_e : float
        Gewicht für Earliness (nur bei lateness_deviation)
    w_dev : float
        Gewicht für Deviation (nur bei lateness_deviation)
    
    Examples:
    ---------
    >>> # Makespan-Minimierung
    >>> solver = TabuSolver(jobs, logger, objective="makespan")
    >>> schedule, initial, final = solver.solve(max_iters=1000)
    
    >>> # Termintreue-Optimierung
    >>> solver = TabuSolver(
    ...     jobs, logger, 
    ...     objective="lateness_deviation",
    ...     w_t=0.5, w_e=0.5, w_dev=0.3
    ... )
    >>> schedule, initial, final = solver.solve(max_iters=1000)
    """
```

### B) Experiment-Skripte - Header-Kommentare

```python
"""
Tabu Search Experiment Runner - Makespan Optimization

Führt Tabu Search Experimente auf dem FT10 Benchmark aus und optimiert
für minimale Makespan (Gesamtfertigstellungszeit).

Usage:
    python run_single_tabu_ft10.py

Output:
    - Datenbank-Eintrag mit Experiment-ID
    - CSV: data/output/tabu_improvements_exp_<ID>.csv
    - Console: Verbesserungen pro Schicht

Configuration:
    MAX_ITERATIONS = 1000  # Tabu Search Iterationen
    TABU_ALLOWED = 25      # Tabu-Listen-Länge
"""
```

### C) Analyse-Skripte - Header-Kommentare

```python
"""
Tabu Search Improvement Analysis

Analysiert die Verbesserungen (initial vs. final objective) über alle
Tabu Search Experimente hinweg.

Usage:
    python analyze_tabu_improvements.py

Input:
    - data/output/tabu_improvements_exp_*.csv

Output:
    - data/output/tabu_improvements_summary.csv - Kombinierte Daten
    - data/output/tabu_improvements_stats.csv - Aggregierte Statistiken
    - Console: Statistiken pro Experiment
"""
```

---

## 5️⃣ Implementierungs-Reihenfolge

### Phase 1: Kern-Dokumentation (Priorität: HOCH)
1. ✅ `src/solvers/Tabu_Solver.py` - Klassen- und Methoden-Docstrings
2. ✅ `src/Tabu_Experiment_Runner.py` - Funktions-Docstrings

### Phase 2: Skript-Header (Priorität: MITTEL)
3. ✅ Alle run_*tabu*.py - Header-Kommentare
4. ✅ Alle analyze_tabu*.py - Header-Kommentare
5. ✅ Alle plot_tabu*.py - Header-Kommentare

### Phase 3: README erweitern (Priorität: MITTEL)
6. ✅ Tabu Search Sektion in README.md
7. ✅ Quick-Start Beispiele

### Phase 4: Cleanup (Priorität: NIEDRIG)
8. ⚠️ Entfernen unnötiger Skripte (nach Rücksprache)
9. ✅ .gitignore erweitern (Ausgabedateien)

---

## 6️⃣ Fragen zur Klärung

### 🤔 Skripte entfernen?

**Bitte entscheiden:**

1. `run_test_lateness_experiment.py` - Noch benötigt?
2. `analyze_weight_impact_simple.py` - Redundant?
3. `generate_ergebnisuebersicht.py` - Projektseminar-spezifisch?
4. `generate_projektdokument.py` - Projektseminar-spezifisch?
5. `list_experiments.py` - Debugging-Tool behalten?
6. `show_lateness_ranking.py` - Hilfreich für neue Entwickler?

### 🤔 Sonstige Fragen:

- Sollen die `run_cp_experiments*.sh` Skripte auch dokumentiert werden?
- Notebooks in `notebooks/` - Cleanup erforderlich?
- Projektseminar-Ordner behalten oder archivieren?

---

## 7️⃣ Nächste Schritte

1. **Reviewe diesen Plan** - Bestätige, welche Dateien entfernt werden sollen
2. **Phase 1 starten** - Kern-Dokumentation (Tabu_Solver.py)
3. **Phase 2-3** - Skript-Header + README
4. **Phase 4** - Cleanup + .gitignore

**Bereit zum Start?** 🚀
