from __future__ import annotations

from decimal import Decimal

from src.Logger import Logger
from src.domain.Collection import LiveJobCollection
from src.domain.Query import JobQuery, ExperimentQuery, MachineInstanceQuery
from src.domain.orm_models import Experiment
from src.simulation.LognormalFactorGenerator import LognormalFactorGenerator
from src.simulation.ProductionSimulation import ProductionSimulation
from src.solvers.Tabu_Solver import TabuSolver


def run_experiment(
    experiment_id: int,
    shift_length: int,
    total_shift_number: int,
    logger: Logger,
    tabu_allowed: int = 25,
    max_iters: int = 800,
    patience: int = 40,
    top_k: int = 60,
) -> None:
    """
    Führt ein Tabu-Experiment mit Shift-Logik aus (analog zum CP-Solver):

    - Lädt alle Jobs für die gegebene Quelle und max_bottleneck_utilization
    - Verarbeitet die Jobs shift-weise
    - Simuliert nach jedem Shift
    - Speichert Schedule und Simulation in der DB
    """

    experiment = ExperimentQuery.get_experiment(experiment_id)

    source_name = experiment.routing_source.name
    max_bottleneck_utilization = experiment.max_bottleneck_utilization

    logger.info(
        f"Tabu-Experiment {experiment_id} gestartet "
        f"(Quelle='{source_name}', "
        f"max_util={max_bottleneck_utilization}, "
        f"shifts={total_shift_number})"
    )

    # Preparation  ----------------------------------------------------------------------------------
    simulation = ProductionSimulation(verbose=False)

    # Jobs Collection
    jobs = JobQuery.get_by_source_name_max_util_and_lt_arrival(
        source_name=source_name,
        max_bottleneck_utilization=Decimal(f"{max_bottleneck_utilization}"),
        arrival_limit=60 * 24 * total_shift_number
    )
    jobs_collection = LiveJobCollection(jobs)

    # Machines with transition times
    machines_instances = MachineInstanceQuery.get_by_source_name_and_max_bottleneck_utilization(
        source_name=source_name,
        max_bottleneck_utilization=Decimal(f"{max_bottleneck_utilization}"),
    )

    # Add transition times to operations
    for machine_instance in machines_instances:
        for job in jobs_collection.values():
            for operation in job.operations:
                if operation.machine_name == machine_instance.name:
                    operation.transition_time = machine_instance.transition_time

    # Add simulation durations to operations
    factor_gen = LognormalFactorGenerator(
        sigma=experiment.sim_sigma,
        seed=42
    )
    jobs_collection.sort_jobs_by_id()
    jobs_collection.sort_operations()
    for job in jobs_collection.values():
        for operation in job.operations:
            sim_duration_float = operation.duration * factor_gen.sample()
            operation.sim_duration = int(sim_duration_float)

    # Collections (empty)
    schedule_jobs_collection = LiveJobCollection()  # pseudo previous schedule
    active_job_ops_collection = LiveJobCollection()
    waiting_job_ops_collection = LiveJobCollection()

    # Shifts ----------------------------------------------------------------------------------------
    for shift_number in range(1, total_shift_number + 1):
        shift_start = shift_number * shift_length
        shift_end = (shift_number + 1) * shift_length
        logger.info(f"Experiment {experiment_id} shift {shift_number}: {shift_start} to {shift_end}")

        new_jobs_collection = jobs_collection.get_subset_by_earliest_start(earliest_start=shift_start)
        current_jobs_collection = new_jobs_collection + waiting_job_ops_collection

        # Scheduling mit Tabu-Solver --------------------------------------------------------------
        solver = TabuSolver(
            jobs_collection=current_jobs_collection,
            logger=logger
        )

        schedule_jobs_collection = solver.solve(
            tabu_allowed=tabu_allowed,
            max_iters=max_iters,
            patience=patience,
            top_k=top_k,
        )

        ExperimentQuery.save_schedule_jobs(
            experiment_id=experiment_id,
            shift_number=shift_number,
            live_jobs=schedule_jobs_collection.values(),
        )

        # Simulation --------------------------------------------------------------
        simulation.run(
            schedule_collection=schedule_jobs_collection,
            start_time=shift_start,
            end_time=shift_end
        )

        active_job_ops_collection = simulation.get_active_operation_collection()
        waiting_job_ops_collection = simulation.get_waiting_operation_collection()

    # Save entire Simulation -------------------------------------------------------
    entire_simulation_jobs = simulation.get_entire_finished_operation_collection()
    ExperimentQuery.save_simulation_jobs(
        experiment_id=experiment_id,
        live_jobs=entire_simulation_jobs.values(),
    )
    logger.info(f"Experiment {experiment_id} finished")
