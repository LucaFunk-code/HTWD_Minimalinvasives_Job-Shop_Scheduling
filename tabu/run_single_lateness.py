"""
Run a single Tabu experiment with lateness deviation objective function.
Just run:
    python3 run_single_tabu_lateness.py
"""

from __future__ import annotations
import os
import sys
from decimal import Decimal

# Project root in path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    print("Starting Tabu experiment with lateness deviation objective…")

    # ---- Configuration ----
    SOURCE_NAME = "Fisher and Thompson 10x10"
    MAX_BOTTLENECK_UTILIZATION = 0.75
    ABSOLUTE_LATENESS_RATIO = 0.5  # w_t weight for tardiness
    INNER_TARDINESS_RATIO = 0.5    # w_dev weight for deviation
    SIM_SIGMA = 0.1
    SHIFT_LENGTH = 60 * 24      
    TOTAL_SHIFT_NUMBER = 20      
    
    # Tabu Search parameters
    TABU_ALLOWED = 25
    MAX_ITERS = 300
    PATIENCE = 20
    TOP_K = 20
    
    # Objective function: "makespan" or "lateness_deviation"
    OBJECTIVE = "lateness_deviation"

    try:
        from src.Tabu_Experiment_Runner import run_experiment
        from src.Logger import Logger
        from src.domain.Initializer import ExperimentInitializer
    except Exception as e:
        print("Failed to import required modules:", e)
        raise

    # Create experiment
    print(f"Creating experiment: {SOURCE_NAME}, util={MAX_BOTTLENECK_UTILIZATION}, sigma={SIM_SIGMA}")
    print(f"Objective: {OBJECTIVE}")
    print(f"Weights: w_t={ABSOLUTE_LATENESS_RATIO}, w_e={1.0-ABSOLUTE_LATENESS_RATIO}, w_dev={INNER_TARDINESS_RATIO}")
    
    experiment_id = ExperimentInitializer.insert_experiment(
        source_name=SOURCE_NAME,
        absolute_lateness_ratio=ABSOLUTE_LATENESS_RATIO,
        inner_tardiness_ratio=INNER_TARDINESS_RATIO,
        max_bottleneck_utilization=Decimal(f"{MAX_BOTTLENECK_UTILIZATION:.2f}"),
        sim_sigma=SIM_SIGMA,
        experiment_type="Tabu_Lateness",
    )
    
    if experiment_id is None:
        print("Failed to create experiment!")
        return
    
    print(f"Experiment created with ID: {experiment_id}")

    # Logger
    logger = Logger("tabu_lateness", f"tabu_lateness_experiment_{experiment_id}.log")

    # Run the Tabu Experiment with lateness objective
    run_experiment(
        experiment_id=experiment_id,
        shift_length=SHIFT_LENGTH,
        total_shift_number=TOTAL_SHIFT_NUMBER,
        logger=logger,
        tabu_allowed=TABU_ALLOWED,
        max_iters=MAX_ITERS,
        patience=PATIENCE,
        top_k=TOP_K,
        objective=OBJECTIVE,
    )

    print(f"✓ Tabu experiment with {OBJECTIVE} objective finished.")
    print(f"✓ Results saved to: data/output/tabu_improvements_exp_{experiment_id}.csv")


if __name__ == "__main__":
    main()
