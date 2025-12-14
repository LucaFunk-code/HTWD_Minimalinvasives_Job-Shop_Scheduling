# Tabu Solver - Zielfunktionen

Der Tabu Solver unterstützt jetzt zwei verschiedene Zielfunktionen:

## 1. Makespan (Standard)

**Ziel:** Minimiere die Gesamtfertigstellungszeit (Cmax)

```python
solver = TabuSolver(
    jobs_collection=jobs,
    logger=logger,
    objective="makespan"  # Standard
)
```

**Verwendung:**
```bash
python3 run_single_tabu_ft10.py
```

---

## 2. Termintreue (Lateness Deviation)

**Zielfunktion:**
```
Z = w_t * ΣTj + w_e * ΣEj + w_dev * ΣDev_i
```

Wobei:
- **Tj = max{0, Cj - dj}** - Tardiness (Verspätung) von Job j
- **Ej = max{0, dj - Cj}** - Earliness (Verfrühung) von Job j  
- **Dev_i = |start_i - original_start_i|** - Startzeit-Abweichung von Operation i

**Gewichte:**
- **w_t** = `absolute_lateness_ratio` (Gewicht für Tardiness)
- **w_e** = `1.0 - absolute_lateness_ratio` (Gewicht für Earliness)
- **w_dev** = `inner_tardiness_ratio` (Gewicht für Deviation)

### Verwendung:

```python
solver = TabuSolver(
    jobs_collection=jobs,
    logger=logger,
    objective="lateness_deviation",
    w_t=0.5,    # Tardiness weight
    w_e=0.5,    # Earliness weight
    w_dev=0.3   # Deviation weight
)
```

**Experimentskript:**
```bash
python3 run_single_tabu_lateness.py
```

### Konfiguration in `run_single_tabu_lateness.py`:

```python
ABSOLUTE_LATENESS_RATIO = 0.5  # w_t (Tardiness weight)
INNER_TARDINESS_RATIO = 0.3    # w_dev (Deviation weight)
# w_e wird automatisch berechnet: 1.0 - ABSOLUTE_LATENESS_RATIO

OBJECTIVE = "lateness_deviation"
```

---

## Vergleich der Zielfunktionen

| Aspekt | Makespan | Lateness Deviation |
|--------|----------|-------------------|
| **Ziel** | Minimiere Gesamtzeit | Minimiere Termintreue-Verletzungen |
| **Berücksichtigt** | Nur Fertigstellungszeit | Due Dates, Earliness, Tardiness, Plan-Stabilität |
| **Use Case** | Maximale Effizienz | Termintreue & Planstabilität |
| **Voraussetzungen** | Keine | Jobs benötigen `due_date`, Optional: `original_start` |

---

## Output

Beide Zielfunktionen erzeugen dieselbe CSV-Struktur:

```csv
Experiment_ID,Shift,Num_Operations,Initial_Objective,Final_Objective,Improvement,Improvement_Percent,Solve_Time_Seconds
42,1,245,5432.50,4891.20,541.30,9.96,12.45
```

**Hinweis:** Bei `objective="makespan"` ist `Initial_Objective` = Makespan, bei `objective="lateness_deviation"` ist es die gewichtete Summe der Zielfunktionskomponenten.

---

## Beispiel: Vollständiger Workflow

### 1. Makespan-Optimierung:
```bash
# Experiment durchführen
python3 run_single_tabu_ft10.py

# Ergebnisse analysieren
python3 analyze_tabu_improvements.py
```

### 2. Termintreue-Optimierung:
```bash
# Experiment durchführen
python3 run_single_tabu_lateness.py

# Ergebnisse analysieren  
python3 analyze_tabu_improvements.py
```

---

## Implementierungsdetails

### Berechnung in `_decode_sequence()`:

```python
def _calculate_lateness_objective(self, scheduled: List[OperationPlan]) -> float:
    # 1. Job completion times
    job_end = {op.job_idx: max(end) for op in scheduled}
    
    # 2. Tardiness
    tardiness = sum(max(0, job_end[j] - due_date[j]) for j in job_end)
    
    # 3. Earliness
    earliness = sum(max(0, due_date[j] - job_end[j]) for j in job_end)
    
    # 4. Deviation
    deviation = sum(abs(op.start - original_start[op]) for op in scheduled)
    
    # 5. Weighted objective
    return w_t * tardiness + w_e * earliness + w_dev * deviation
```

---

## Tipps zur Gewichtswahl

1. **Nur Verspätung minimieren:**
   - `w_t = 1.0, w_e = 0.0, w_dev = 0.0`

2. **Termintreue (Verspätung + Verfrühung):**
   - `w_t = 0.5, w_e = 0.5, w_dev = 0.0`

3. **Termintreue + Planstabilität:**
   - `w_t = 0.4, w_e = 0.4, w_dev = 0.2`

4. **Starke Planstabilität:**
   - `w_t = 0.3, w_e = 0.3, w_dev = 0.4`

**Hinweis:** Die Summe `w_t + w_e + w_dev` muss nicht 1.0 sein, aber gleiche Größenordnungen erleichtern die Interpretation.
