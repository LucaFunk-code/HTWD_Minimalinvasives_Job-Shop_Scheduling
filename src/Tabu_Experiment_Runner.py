from __future__ import annotations

from decimal import Decimal

from src.Logger import Logger
from src.domain.Collection import LiveJobCollection
from src.domain.Query import JobQuery, ExperimentQuery
from src.domain.orm_models import Experiment
from src.solvers.Tabu_Solver import TabuSolver


def _prepare_ft10_jobs_collection(experiment: Experiment, num_jobs: int = 10) -> LiveJobCollection:
    """
    Erzeuge eine LiveJobCollection mit EXACT num_jobs Jobs im FT10-Stil:

    - Quelle: experiment.routing_source.name (sollte "Fisher and Thompson 10x10" sein)
    - max_bottleneck_utilization: experiment.max_bottleneck_utilization
    - sortiere alle passenden Jobs nach Arrival
    - nimm die ersten num_jobs
    - setze sim_duration = duration (keine Stochastik, klassisches FT10)
    """

    source_name = experiment.routing_source.name
    max_util = experiment.max_bottleneck_utilization

    # Alle Jobs für diese Quelle + Auslastung holen
    jobs = JobQuery.get_by_source_name_and_max_bottleneck_utilization(
        source_name=source_name,
        max_bottleneck_utilization=Decimal(f"{max_util}")
    )

    # Nach Arrival sortieren und nur die ersten num_jobs nehmen
    jobs_sorted = sorted(jobs, key=lambda j: j.arrival)
    jobs_small = jobs_sorted[:num_jobs]

    jobs_collection = LiveJobCollection(jobs_small)

    # FT10-Style: sim_duration = duration (keine zufällige Störung)
    for job in jobs_collection.values():
        for op in job.operations:
            op.sim_duration = op.duration

    return jobs_collection


def run_experiment(
    experiment_id: int,
    logger: Logger,
    num_jobs: int = 10,
    tabu_allowed: int = 25,
    max_iters: int = 800,
    patience: int = 40,
    top_k: int = 60,
) -> None:
    """
    Führt EIN Tabu-Experiment im FT10-Stil aus:

    - Lädt genau num_jobs Jobs aus der DB (Quelle FT10, passende Auslastung)
    - Optimiert den Makespan mit Tabu-Suche
    - Speichert das Ergebnis als Shift 1 in schedule_* Tabellen
    """

    experiment = ExperimentQuery.get_experiment(experiment_id)

    logger.info(
        f"Tabu-Experiment {experiment_id} gestartet "
        f"(Quelle='{experiment.routing_source.name}', "
        f"max_util={experiment.max_bottleneck_utilization}, "
        f"num_jobs={num_jobs})"
    )

    jobs_collection = _prepare_ft10_jobs_collection(experiment, num_jobs=num_jobs)

    solver = TabuSolver(jobs_collection=jobs_collection, logger=logger)
    schedule_jobs_collection = solver.solve(
        tabu_allowed=tabu_allowed,
        max_iters=max_iters,
        patience=patience,
        top_k=top_k,
    )

    # Ergebnis als Shift 1 speichern
    ExperimentQuery.save_schedule_jobs(
        experiment_id=experiment_id,
        shift_number=1,
        live_jobs=schedule_jobs_collection.values(),
    )

    logger.info(f"Tabu-Experiment {experiment_id} beendet")
