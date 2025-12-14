from __future__ import annotations

from decimal import Decimal
import csv
from pathlib import Path
import time
import psutil
import os

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
    objective: str = "makespan",
) -> None:
    """
    Führt ein Tabu-Experiment mit Shift-Logik aus (analog zum CP-Solver):

    - Lädt alle Jobs für die gegebene Quelle und max_bottleneck_utilization
    - Verarbeitet die Jobs shift-weise
    - Simuliert nach jedem Shift
    - Speichert Schedule und Simulation in der DB
    
    Args:
        objective: "makespan" oder "lateness_deviation"
    """

    experiment = ExperimentQuery.get_experiment(experiment_id)

    source_name = experiment.routing_source.name
    max_bottleneck_utilization = experiment.max_bottleneck_utilization
    
    # Weights für Termintreue-Zielfunktion
    w_t = float(experiment.absolute_lateness_ratio)
    w_e = 1.0 - w_t
    w_dev = float(experiment.inner_tardiness_ratio)
    
    # Store configuration for later use
    config_info = {
        'source_name': source_name,
        'max_bottleneck_utilization': float(max_bottleneck_utilization),
        'absolute_lateness_ratio': float(experiment.absolute_lateness_ratio),
        'inner_tardiness_ratio': float(experiment.inner_tardiness_ratio),
        'sim_sigma': float(experiment.sim_sigma),
        'shift_length': shift_length,
        'total_shift_number': total_shift_number,
        'tabu_allowed': tabu_allowed,
        'max_iters': max_iters,
        'patience': patience,
        'top_k': top_k,
        'objective': objective,
        'w_t': w_t,
        'w_e': w_e,
        'w_dev': w_dev,
    }

    logger.info(
        f"Tabu-Experiment {experiment_id} gestartet "
        f"(Quelle='{source_name}', "
        f"max_util={max_bottleneck_utilization}, "
        f"shifts={total_shift_number}, "
        f"objective='{objective}')"
    )
    
    if objective == "lateness_deviation":
        logger.info(f"Weights: w_t={w_t:.2f}, w_e={w_e:.2f}, w_dev={w_dev:.2f}")

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

    # List to track makespan improvements
    makespan_improvements = []
    
    # Track total time
    total_start_time = time.time()

    # Shifts ----------------------------------------------------------------------------------------
    for shift_number in range(1, total_shift_number + 1):
        shift_start = shift_number * shift_length
        shift_end = (shift_number + 1) * shift_length
        logger.info(f"Experiment {experiment_id} shift {shift_number}: {shift_start} to {shift_end}")

        new_jobs_collection = jobs_collection.get_subset_by_earliest_start(earliest_start=shift_start)
        current_jobs_collection = new_jobs_collection + waiting_job_ops_collection
        
        # Count operations
        num_operations = sum(len(job.operations) for job in current_jobs_collection.values())

        # Scheduling mit Tabu-Solver --------------------------------------------------------------
        shift_solve_start = time.time()
        
        # Get memory usage before solving
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        solver = TabuSolver(
            jobs_collection=current_jobs_collection,
            logger=logger,
            objective=objective,
            w_t=w_t,
            w_e=w_e,
            w_dev=w_dev,
        )

        schedule_jobs_collection, initial_objective, final_objective = solver.solve(
            tabu_allowed=tabu_allowed,
            max_iters=max_iters,
            patience=patience,
            top_k=top_k,
        )
        
        shift_solve_time = time.time() - shift_solve_start
        
        # Get memory usage after solving
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        # Calculate improvement percentage
        improvement_percent = ((initial_objective - final_objective) / initial_objective * 100) if initial_objective > 0 else 0
        
        # Spaltenbezeichnungen abhängig vom Objective
        if objective == "makespan":
            initial_col = 'Initial_Makespan'
            final_col = 'Final_Makespan'
            objective_label = "Makespan"
        else:
            initial_col = 'Initial_Lateness_Deviation'
            final_col = 'Final_Lateness_Deviation'
            objective_label = "Lateness_Deviation"
        
        makespan_improvements.append({
            'Experiment_ID': experiment_id,
            'Shift': shift_number,
            'Num_Operations': num_operations,
            initial_col: round(initial_objective, 2),
            final_col: round(final_objective, 2),
            'Improvement': round(initial_objective - final_objective, 2),
            'Improvement_Percent': round(improvement_percent, 2),
            'Solve_Time_Seconds': round(shift_solve_time, 2),
            'Memory_MB': round(memory_after, 2),
            'Memory_Used_MB': round(memory_used, 2)
        })
        
        logger.info(
            f"Shift {shift_number}: Ops={num_operations}, Initial {objective_label}={initial_objective:.2f}, "
            f"Final {objective_label}={final_objective:.2f}, Improvement={improvement_percent:.2f}%, "
            f"Time={shift_solve_time:.2f}s, Memory={memory_after:.2f}MB (used: {memory_used:+.2f}MB)"
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
    
    # Calculate total time
    total_time = time.time() - total_start_time
    
    # Save makespan improvements to CSV file
    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"tabu_improvements_exp_{experiment_id}.csv"
    
    with open(output_file, 'w', newline='') as f:
        if makespan_improvements:
            writer = csv.DictWriter(f, fieldnames=makespan_improvements[0].keys())
            writer.writeheader()
            writer.writerows(makespan_improvements)
    
    # Save configuration to separate file
    config_file = output_dir / f"tabu_config_exp_{experiment_id}.csv"
    with open(config_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=config_info.keys())
        writer.writeheader()
        writer.writerow(config_info)
    
    # Calculate and log statistics
    if makespan_improvements:
        avg_improvement = sum(m['Improvement_Percent'] for m in makespan_improvements) / len(makespan_improvements)
        total_solve_time = sum(m['Solve_Time_Seconds'] for m in makespan_improvements)
        max_memory = max(m['Memory_MB'] for m in makespan_improvements)
        total_memory_used = sum(m['Memory_Used_MB'] for m in makespan_improvements)
        
        logger.info("=" * 80)
        logger.info(f"EXPERIMENT {experiment_id} SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Configuration:")
        logger.info(f"  Source: {config_info['source_name']}")
        logger.info(f"  Max Bottleneck Utilization: {config_info['max_bottleneck_utilization']}")
        logger.info(f"  Sim Sigma: {config_info['sim_sigma']}")
        logger.info(f"  Objective: {config_info['objective']}")
        if objective == "lateness_deviation":
            logger.info(f"  Weights: w_t={config_info['w_t']:.2f}, w_e={config_info['w_e']:.2f}, w_dev={config_info['w_dev']:.2f}")
        logger.info(f"  Tabu Settings: allowed={config_info['tabu_allowed']}, "
                   f"max_iters={config_info['max_iters']}, "
                   f"patience={config_info['patience']}, top_k={config_info['top_k']}")
        logger.info(f"Results:")
        logger.info(f"  Total shifts: {len(makespan_improvements)}")
        logger.info(f"  Average improvement: {avg_improvement:.2f}%")
        logger.info(f"  Total solve time: {total_solve_time:.2f}s ({total_solve_time/60:.2f} minutes)")
        logger.info(f"  Total experiment time: {total_time:.2f}s ({total_time/60:.2f} minutes)")
        logger.info(f"  Peak memory usage: {max_memory:.2f}MB")
        logger.info(f"  Total memory used: {total_memory_used:.2f}MB")
        logger.info(f"Files saved:")
        logger.info(f"  Improvements: {output_file}")
        logger.info(f"  Configuration: {config_file}")
        logger.info("=" * 80)
    
    logger.info(f"Experiment {experiment_id} finished")
