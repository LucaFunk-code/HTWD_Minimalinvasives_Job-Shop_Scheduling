"""
Run multiple Tabu experiments in parallel using Python multiprocessing.
Usage: python3 run_parallel_tabu_experiments.py
"""

from __future__ import annotations
import os
import sys
from decimal import Decimal
from multiprocessing import Pool, cpu_count
from typing import Dict, Any
import time

# Project root in path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def run_single_experiment(config: Dict[str, Any]) -> int:
    """
    Führt ein einzelnes Tabu-Experiment aus.
    
    Args:
        config: Dictionary mit allen Experiment-Parametern
        
    Returns:
        experiment_id
    """
    from src.Tabu_Experiment_Runner import run_experiment
    from src.Logger import Logger
    from src.domain.Initializer import ExperimentInitializer
    
    # Extrahiere Parameter
    source_name = config.get("source_name", "Fisher and Thompson 10x10")
    max_bottleneck_utilization = config.get("max_bottleneck_utilization", 0.75)
    absolute_lateness_ratio = config.get("absolute_lateness_ratio", 0.5)
    inner_tardiness_ratio = config.get("inner_tardiness_ratio", 0.5)
    sim_sigma = config.get("sim_sigma", 0.1)
    shift_length = config.get("shift_length", 60 * 24)
    total_shift_number = config.get("total_shift_number", 20)
    
    # Tabu-Parameter
    tabu_allowed = config.get("tabu_allowed", 25)
    max_iters = config.get("max_iters", 800)
    patience = config.get("patience", 40)
    top_k = config.get("top_k", 60)
    objective = config.get("objective", "lateness_deviation")
    
    experiment_type = config.get("experiment_type", "Tabu_Parallel")
    
    print(f"[Process {os.getpid()}] Starting experiment: tabu_allowed={tabu_allowed}, "
          f"max_iters={max_iters}, patience={patience}, top_k={top_k}")
    
    try:
        # Create experiment
        experiment_id = ExperimentInitializer.insert_experiment(
            source_name=source_name,
            absolute_lateness_ratio=absolute_lateness_ratio,
            inner_tardiness_ratio=inner_tardiness_ratio,
            max_bottleneck_utilization=Decimal(f"{max_bottleneck_utilization:.2f}"),
            sim_sigma=sim_sigma,
            experiment_type=experiment_type,
        )
        
        if experiment_id is None:
            print(f"[Process {os.getpid()}] Failed to create experiment!")
            return -1
        
        print(f"[Process {os.getpid()}] Experiment created with ID: {experiment_id}")
        
        # Logger
        logger = Logger(
            "tabu_parallel", 
            f"tabu_exp_{experiment_id}_ta{tabu_allowed}_mi{max_iters}.log"
        )
        
        # Run experiment
        start_time = time.time()
        run_experiment(
            experiment_id=experiment_id,
            shift_length=shift_length,
            total_shift_number=total_shift_number,
            logger=logger,
            tabu_allowed=tabu_allowed,
            max_iters=max_iters,
            patience=patience,
            top_k=top_k,
            objective=objective,
        )
        
        elapsed = time.time() - start_time
        print(f"[Process {os.getpid()}] Experiment {experiment_id} completed in {elapsed:.2f}s")
        
        return experiment_id
        
    except Exception as e:
        print(f"[Process {os.getpid()}] Error in experiment: {e}")
        import traceback
        traceback.print_exc()
        return -1


def main():
    """
    Hauptfunktion: Definiere Experimente und führe sie parallel aus.
    """
    
    # =========================================================================
    # KONFIGURATION: Gewichtsanalyse für Termintreue
    # =========================================================================
    
    # Anzahl paralleler Prozesse (du hast 32 Kerne)
    NUM_PARALLEL_JOBS = 10  # Erhöht von 5 auf 10 für doppelte Geschwindigkeit
    NUM_REPETITIONS = 10     # Jede Gewichtskombination 10x wiederholen
    
    # Basis-Parameter für alle Experimente (wie in run_single_tabu_lateness.py)
    BASE_CONFIG = {
        "source_name": "Fisher and Thompson 10x10",
        "max_bottleneck_utilization": 0.75,
        "sim_sigma": 0.1,
        "shift_length": 60 * 24,
        "total_shift_number": 20,
        "tabu_allowed": 25,
        "max_iters": 300,
        "patience": 20,
        "top_k": 20,
        "objective": "lateness_deviation"
    }
    
    # Basis-Gewichtskonfigurationen
    # w_t = ABSOLUTE_LATENESS_RATIO (Tardiness-Gewicht)
    # w_e = 1.0 - w_t (Earliness-Gewicht, implizit)
    # w_dev = INNER_TARDINESS_RATIO (Deviation-Gewicht)
    weight_configs = [
        # Config 1: TARDINESS-FOKUS
        {
            "absolute_lateness_ratio": 0.8,
            "inner_tardiness_ratio": 0.5,
            "experiment_type": "Tabu_Weight_TardinessFocus"
        },
        # Config 2: EARLINESS-FOKUS
        {
            "absolute_lateness_ratio": 0.2,
            "inner_tardiness_ratio": 0.5,
            "experiment_type": "Tabu_Weight_EarlinessFocus"
        },
        # Config 3: BALANCED
        {
            "absolute_lateness_ratio": 0.5,
            "inner_tardiness_ratio": 0.5,
            "experiment_type": "Tabu_Weight_Balanced"
        },
        # Config 4: DEVIATION-FOKUS mit Tardiness-Bias
        {
            "absolute_lateness_ratio": 0.6,
            "inner_tardiness_ratio": 0.8,
            "experiment_type": "Tabu_Weight_DeviationTardiness"
        },
        # Config 5: DEVIATION-FOKUS mit Earliness-Bias
        {
            "absolute_lateness_ratio": 0.3,
            "inner_tardiness_ratio": 0.8,
            "experiment_type": "Tabu_Weight_DeviationEarliness"
        },
    ]
    
    # Erstelle alle Experimente (jede Gewichtskonfiguration NUM_REPETITIONS mal)
    experiment_configs = []
    for rep in range(1, NUM_REPETITIONS + 1):
        for config in weight_configs:
            exp_config = {
                **BASE_CONFIG,
                **config,
                "experiment_type": f"{config['experiment_type']}_Rep{rep:02d}"
            }
            experiment_configs.append(exp_config)
    
    # =========================================================================
    # AUSFÜHRUNG
    # =========================================================================
    
    print("=" * 80)
    print(f"Starting {len(experiment_configs)} Tabu experiments in parallel")
    print(f"  - {len(weight_configs)} weight configurations")
    print(f"  - {NUM_REPETITIONS} repetitions per configuration")
    print(f"  - Total: {len(experiment_configs)} experiments")
    print(f"Using {NUM_PARALLEL_JOBS} parallel processes (out of {cpu_count()} available cores)")
    print("=" * 80)
    
    start_time = time.time()
    
    # Führe Experimente parallel aus
    with Pool(processes=NUM_PARALLEL_JOBS) as pool:
        experiment_ids = pool.map(run_single_experiment, experiment_configs)
    
    elapsed_time = time.time() - start_time
    
    # Ergebnisse
    print("\n" + "=" * 80)
    print("ALL EXPERIMENTS COMPLETED!")
    print("=" * 80)
    print(f"Total time: {elapsed_time:.2f}s ({elapsed_time/60:.2f} minutes)")
    print(f"Successful experiments: {sum(1 for eid in experiment_ids if eid > 0)}")
    print(f"Failed experiments: {sum(1 for eid in experiment_ids if eid < 0)}")
    
    print("\n" + "=" * 80)
    print("EXPERIMENT RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total experiments: {len(experiment_ids)}")
    print(f"Successful: {sum(1 for eid in experiment_ids if eid > 0)}")
    print(f"Failed: {sum(1 for eid in experiment_ids if eid < 0)}")
    print()
    
    # Gruppiere nach Gewichtskonfiguration
    print("Results by weight configuration:")
    print("-" * 80)
    for i, base_config in enumerate(weight_configs, 1):
        w_t = base_config["absolute_lateness_ratio"]
        w_e = 1.0 - w_t
        w_dev = base_config["inner_tardiness_ratio"]
        config_name = base_config["experiment_type"]
        
        # Finde alle Experimente für diese Konfiguration
        start_idx = (i - 1) * NUM_REPETITIONS
        end_idx = i * NUM_REPETITIONS
        config_ids = experiment_ids[start_idx:end_idx]
        successful = sum(1 for eid in config_ids if eid > 0)
        
        print(f"\n{i}. {config_name}")
        print(f"   Weights: w_t={w_t:.1f}, w_e={w_e:.1f}, w_dev={w_dev:.1f}")
        print(f"   Results: {successful}/{NUM_REPETITIONS} successful")
        print(f"   IDs: {', '.join(str(eid) if eid > 0 else 'FAILED' for eid in config_ids)}")
    
    print("\n" + "=" * 80)
    print("\nAUSWERTUNG:")
    print("Für jeden Experiment-Typ wurden folgende Dateien erstellt:")
    print("  1. Log-Datei: logs/tabu_parallel_exp_<ID>_ta*.log")
    print("  2. Verbesserungen: data/output/tabu_improvements_exp_<ID>.csv")
    print("  3. Datenbank: Experiment-Tabelle mit allen Metriken")
    print("\nZum Auswerten der Gewichte, vergleiche die Termintreue-Metriken:")
    print("  - Tardiness (Verspätung)")
    print("  - Earliness (Frühlieferung)")
    print("  - Deviation (Abweichung vom Termin)")
    print("  - Termintreue-Score (kombiniert)")
    print("=" * 80)


if __name__ == "__main__":
    main()
