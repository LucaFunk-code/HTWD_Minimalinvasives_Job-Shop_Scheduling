"""
Run a single Tabu experiment on FT10 (10x10) with ZERO command line arguments.
Just run:
    python run_single_tabu_ft10.py
"""

from __future__ import annotations
import os
import sys

# Project root in path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def main():
    print("Starting Tabu FT10 experiment…")

    # ---- Configuration (NO CLI PARAMS) ----
    EXPERIMENT_ID = 1           # The experiment to write into
    OVERWRITE_SCHEDULE = True   # Delete previous schedule
    TABU_ALLOWED = 25
    MAX_ITERS = 800
    PATIENCE = 40
    TOP_K = 60
    NUM_JOBS = 10               # FT10 → always 10

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
        from src.domain.Query import ExperimentQuery
    except Exception as e:
        print("Failed to import required modules:", e)
        raise

    # Delete previous schedule (optional)
    if OVERWRITE_SCHEDULE:
        try:
            print(f"Overwriting existing schedule for experiment={EXPERIMENT_ID}, shift=1 …")
            ExperimentQuery.delete_schedule_for_experiment_shift(EXPERIMENT_ID, 1)
        except Exception as e:
            print("Warning: Could not delete previous schedule:", e)

    # Logger
    logger = Logger("tabu_ft10", f"tabu_ft10_experiment_{EXPERIMENT_ID}.log")

    # Run the FT10 Tabu Experiment
    run_experiment(
        experiment_id=EXPERIMENT_ID,
        logger=logger,
        num_jobs=NUM_JOBS,
        tabu_allowed=TABU_ALLOWED,
        max_iters=MAX_ITERS,
        patience=PATIENCE,
        top_k=TOP_K,
    )

    print("✔️ Tabu FT10 run finished.")


if __name__ == "__main__":
    main()
