# Constraint Programming (CP) Solver

Dieses Verzeichnis enthält Skripte für den **CP-Solver** (Google OR-Tools).

##  Experimente ausführen

### Einzelnes Experiment
```bash
python cp/run_single.py
# oder mit Shell-Wrapper
bash cp/run_single.sh
```

### Batch-Experimente
```bash
python cp/run_experiments.py
# oder
bash cp/run_experiments.sh
```

### Termintreue-Experimente
Spezielle Experimente für Termintreue-Optimierung:
```bash
python cp/run_termintreue.py
```

### HPC-Cluster (Romeo)
```bash
bash cp/run_experiments_romeo.sh
```

---

##  Weitere Informationen

**Kern-Implementation:**
- `src/solvers/CP_Solver.py` - CP-Solver mit OR-Tools
- `src/CP_Experiment_Runner.py` - Experiment-Runner

**Zielfunktionen:**
- Makespan-Minimierung
- Termintreue (Tardiness + Earliness + Deviation)
- Flowtime-Optimierung
