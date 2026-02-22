"""
Run a single Tabu experiment with shift logic (like CP solver).
Just run:
    python run_single_tabu_ft10.py
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
    print("Starting Tabu experiment with shift logic…")

    # ---- Configuration (NO CLI PARAMS) ----
    SOURCE_NAME = "Fisher and Thompson 10x10"
    MAX_BOTTLENECK_UTILIZATION = 0.75
    ABSOLUTE_LATENESS_RATIO = 0.5
    INNER_TARDINESS_RATIO = 0.5
    SIM_SIGMA = 0.1
    SHIFT_LENGTH = 60 * 24      
    TOTAL_SHIFT_NUMBER = 2    
    TABU_ALLOWED = 100
    MAX_ITERS = 20
    PATIENCE = 10
    TOP_K = 10

    # Set TABU environment variables (optional but consistent)
    os.environ["TABU_SAMPLE_SIZE"] = "none"
    os.environ["TABU_MAX_ITERS"] = str(MAX_ITERS)
    os.environ["TABU_PATIENCE"] = str(PATIENCE)
    os.environ["TABU_TOP_K"] = str(TOP_K)
    os.environ["TABU_RESTARTS"] = "1"
    os.environ["TABU_RNG_SEED"] = "123"

    try:
        from src.Tabu_Experiment_Runner import run_experiment
        from src.Logger import Logger
        from src.domain.Initializer import ExperimentInitializer
    except Exception as e:
        print("Failed to import required modules:", e)
        raise

    # Create experiment dynamically (like CP runner)
    print(f"Creating experiment: {SOURCE_NAME}, util={MAX_BOTTLENECK_UTILIZATION}, sigma={SIM_SIGMA}")
    experiment_id = ExperimentInitializer.insert_experiment(
        source_name=SOURCE_NAME,
        absolute_lateness_ratio=ABSOLUTE_LATENESS_RATIO,
        inner_tardiness_ratio=INNER_TARDINESS_RATIO,
        max_bottleneck_utilization=Decimal(f"{MAX_BOTTLENECK_UTILIZATION:.2f}"),
        sim_sigma=SIM_SIGMA,
        experiment_type="Tabu",
    )
    
    if experiment_id is None:
        print("Failed to create experiment!")
        return
    
    print(f"Experiment created with ID: {experiment_id}")

    # Logger
    logger = Logger("tabu_shifts", f"tabu_experiment_{experiment_id}.log")

    # Run the Tabu Experiment with shifts
    run_experiment(
        experiment_id=experiment_id,
        shift_length=SHIFT_LENGTH,
        total_shift_number=TOTAL_SHIFT_NUMBER,
        logger=logger,
        tabu_allowed=TABU_ALLOWED,
        max_iters=MAX_ITERS,
        patience=PATIENCE,
        top_k=TOP_K,
    )

    print(" Tabu experiment with shifts finished.")


if __name__ == "__main__":
    main()
