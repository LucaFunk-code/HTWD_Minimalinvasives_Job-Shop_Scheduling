# src/solvers/Tabu_Solver.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Iterable, Callable, Dict, Optional, Literal
from collections import deque, defaultdict
import random

from src.Logger import Logger
from src.domain.Collection import LiveJobCollection
from src.domain.orm_models import JobOperation


@dataclass
class OperationPlan:
    job_idx: int
    op_idx: int
    machine_idx: int
    duration: int
    start: int = 0
    end: int = 0


class TabuSolver:
    """
    Tabu-Suche für Job-Shop-Scheduling auf einer LiveJobCollection.

    - liest Jobs + Operationen aus der DB-Collection
    - minimiert Makespan (Cmax) oder Termintreue-Zielfunktion
    - liefert einen neuen LiveJobCollection-Schedule zurück
    """

    def __init__(
        self,
        jobs_collection: LiveJobCollection,
        logger: Logger,
        rng: Optional[random.Random] = None,
        objective: Literal["makespan", "lateness_deviation"] = "makespan",
        w_t: float = 1.0,
        w_e: float = 1.0,
        w_dev: float = 0.0,
    ) -> None:
        self.logger = logger
        self.jobs_collection = jobs_collection
        self.rng = rng or random.Random()
        self.objective = objective
        self.w_t = w_t
        self.w_e = w_e
        self.w_dev = w_dev

        # interne Repräsentation: je Job eine Liste (machine_idx, duration)
        self.jobs: List[List[Tuple[int, int]]] = []
        self.machine_name_to_idx: Dict[str, int] = {}
        self.machine_idx_to_name: List[str] = []
        self.operation_lookup: Dict[Tuple[int, int], JobOperation] = {}
        
        # Due dates und original starts für Termintreue
        self.job_due_dates: Dict[int, int] = {}
        self.original_starts: Dict[Tuple[int, int], int] = {}

        self._build_internal_problem()

    # ------------------------------------------------------------------
    # Problem aus LiveJobCollection aufbauen
    # ------------------------------------------------------------------
    def _build_internal_problem(self) -> None:
        try:
            # wenn vorhanden, identische Sortierung wie beim CP-Solver
            self.jobs_collection.sort_jobs_by_id()
            self.jobs_collection.sort_operations()
        except AttributeError:
            pass

        machine_counter = 0
        self.jobs.clear()
        self.machine_name_to_idx.clear()
        self.machine_idx_to_name.clear()
        self.operation_lookup.clear()

        for job_idx, job in enumerate(self.jobs_collection.values()):
            job_ops: List[Tuple[int, int]] = []
            
            # Due date für diesen Job speichern
            if hasattr(job, 'due_date') and job.due_date is not None:
                self.job_due_dates[job_idx] = int(job.due_date)
            
            for op_idx, op in enumerate(job.operations):
                m_name = op.machine_name
                if m_name not in self.machine_name_to_idx:
                    self.machine_name_to_idx[m_name] = machine_counter
                    self.machine_idx_to_name.append(m_name)
                    machine_counter += 1
                m_idx = self.machine_name_to_idx[m_name]

                # Dauer: sim_duration, falls vorhanden, sonst duration
                duration = int(getattr(op, "sim_duration", 0) or getattr(op, "duration", 0))
                if duration <= 0:
                    raise ValueError(f"Operation {op} hat keine positive Dauer.")

                job_ops.append((m_idx, duration))
                self.operation_lookup[(job_idx, op_idx)] = op
                
                # Original start speichern falls vorhanden
                if hasattr(op, 'start') and op.start is not None:
                    self.original_starts[(job_idx, op_idx)] = int(op.start)

            if not job_ops:
                raise ValueError(f"Job {job} hat keine Operationen.")
            self.jobs.append(job_ops)

        if not self.jobs:
            raise ValueError("TabuSolver: jobs_collection enthält keine Jobs/Operationen.")

        self.num_jobs = len(self.jobs)
        self.num_machines = len(self.machine_name_to_idx)

        # Jobs dürfen unterschiedlich lang sein; Sequenzen berücksichtigen das
        self.ops_per_job_list = [len(ops) for ops in self.jobs]

        self.logger.info(
            f"TabuSolver: {self.num_jobs} Jobs, "
            f"Operationen pro Job: {self.ops_per_job_list}, "
            f"{self.num_machines} Maschinen"
        )

    # ------------------------------------------------------------------
    # Grundbausteine der Tabu-Suche
    # ------------------------------------------------------------------
    def _decode_sequence(self, sequence: List[int]) -> Tuple[float, List[OperationPlan]]:
        """
        Dekodiert eine Job-Sequenz in einen Schedule.
        Gibt Zielfunktionswert + Operationen zurück.
        
        Returns:
            Tuple[float, List[OperationPlan]]: (objective_value, scheduled_operations)
        """
        job_next_op = [0] * self.num_jobs
        job_ready = [0] * self.num_jobs
        machine_ready = [0] * self.num_machines
        scheduled: List[OperationPlan] = []

        for j in sequence:
            op_idx = job_next_op[j]
            machine_id, p = self.jobs[j][op_idx]

            start_time = max(job_ready[j], machine_ready[machine_id])
            op_plan = OperationPlan(j, op_idx, machine_id, p, start_time, start_time + p)
            scheduled.append(op_plan)

            job_next_op[j] += 1
            job_ready[j] = op_plan.end
            machine_ready[machine_id] = op_plan.end

        # Berechne Zielfunktion basierend auf Objective
        if self.objective == "makespan":
            makespan = max(op.end for op in scheduled)
            return makespan, scheduled
        else:
            return self._calculate_lateness_objective(scheduled), scheduled
    
    def _calculate_lateness_objective(self, scheduled: List[OperationPlan]) -> float:
        """
        Berechnet die Termintreue-Zielfunktion:
        Z = w_t * ΣTj + w_e * ΣEj + w_dev * ΣDev_i
        
        Tj = max{0, Cj - dj} (Tardiness of job j)
        Ej = max{0, dj - Cj} (Earliness of job j)
        Dev_i = |start_i - original_start_i| (Start deviation of operation i)
        """
        # Job completion times ermitteln
        job_end: Dict[int, int] = defaultdict(int)
        for op in scheduled:
            job_end[op.job_idx] = max(job_end[op.job_idx], op.end)
        
        # Tardiness: Tj = max{0, Cj - dj}
        tardiness = sum(
            max(0, job_end[j] - self.job_due_dates.get(j, 0))
            for j in job_end
        )
        
        # Earliness: Ej = max{0, dj - Cj}
        earliness = sum(
            max(0, self.job_due_dates.get(j, 0) - job_end[j])
            for j in job_end
        )
        
        # Deviation: Dev_i = |start_i - original_start_i|
        deviation = 0
        if self.w_dev > 0 and self.original_starts:
            for op in scheduled:
                key = (op.job_idx, op.op_idx)
                if key in self.original_starts:
                    deviation += abs(op.start - self.original_starts[key])
        
        # Gewichtete Zielfunktion
        objective = self.w_t * tardiness + self.w_e * earliness + self.w_dev * deviation
        return objective
    
    def calculate_lateness_components(self, scheduled: List[OperationPlan]) -> dict:
        """
        Berechnet die einzelnen Komponenten der Termintreue separat.
        
        Returns:
            Dictionary mit 'tardiness', 'earliness', 'deviation' und 'objective'
        """
        if not scheduled:
            return {'tardiness': 0, 'earliness': 0, 'deviation': 0, 'objective': 0}
        
        # Job completion times ermitteln
        job_end: Dict[int, int] = defaultdict(int)
        for op in scheduled:
            job_end[op.job_idx] = max(job_end[op.job_idx], op.end)
        
        # Tardiness: Tj = max{0, Cj - dj}
        tardiness = sum(
            max(0, job_end[j] - self.job_due_dates.get(j, 0))
            for j in job_end
        )
        
        # Earliness: Ej = max{0, dj - Cj}
        earliness = sum(
            max(0, self.job_due_dates.get(j, 0) - job_end[j])
            for j in job_end
        )
        
        # Deviation: Dev_i = |start_i - original_start_i|
        deviation = 0
        if self.w_dev > 0 and self.original_starts:
            for op in scheduled:
                key = (op.job_idx, op.op_idx)
                if key in self.original_starts:
                    deviation += abs(op.start - self.original_starts[key])
        
        # Gewichtete Zielfunktion
        objective = self.w_t * tardiness + self.w_e * earliness + self.w_dev * deviation
        
        return {
            'tardiness': tardiness,
            'earliness': earliness,
            'deviation': deviation,
            'objective': objective
        }

    def _generate_random_start_sequence(self) -> List[int]:
        """
        Erstellt eine Startsequenz: Job j kommt so oft vor, wie er Operationen hat.
        """
        seq: List[int] = []
        for j, ops in enumerate(self.jobs):
            seq.extend([j] * len(ops))
        self.rng.shuffle(seq)
        return seq

    def _neighbors_insertion(
        self, sequence: List[int]
    ) -> Iterable[Tuple[List[int], Tuple[int, int]]]:
        """
        Insertion-Nachbarschaft: verschiebe ein Element von i nach j.
        """
        length = len(sequence)
        for i in range(length):
            for j in range(length):
                if i == j:
                    continue
                new_seq = list(sequence)
                elem = new_seq.pop(i)
                new_seq.insert(j, elem)
                yield new_seq, (i, j)

    @staticmethod
    def _sort_key(item):
        makespan_value = item[0]
        move_tuple = item[2]
        return (makespan_value, move_tuple)

    # ------------------------------------------------------------------
    # Öffentliches Interface
    # ------------------------------------------------------------------
    def solve(
        self,
        tabu_allowed: int = 25,
        max_iters: int = 800,
        patience: int = 40,
        top_k: int = 60,
    ) -> Tuple[LiveJobCollection, float, float]:
        """
        Führt Tabu-Suche aus und gibt einen neuen LiveJobCollection-Schedule zurück.
        
        Returns:
            Tuple[LiveJobCollection, float, float]: (schedule_collection, initial_objective, final_objective)
        """
        start_sequence = self._generate_random_start_sequence()
        start_objective, start_schedule = self._decode_sequence(start_sequence)
        
        # Speichere initial schedule für spätere Analyse
        self.best_schedule_initial = start_schedule
        
        objective_name = "Makespan" if self.objective == "makespan" else "Lateness"
        self.logger.info(f"TabuSolver: Start-{objective_name} = {start_objective:.2f}")
        
        if self.objective == "lateness_deviation":
            self.logger.info(f"TabuSolver: Weights w_t={self.w_t}, w_e={self.w_e}, w_dev={self.w_dev}")

        best_sequence, best_objective, _ = self._tabu_search(
            start_seq=start_sequence,
            neigh_func=self._neighbors_insertion,
            tabu_allowed=tabu_allowed,
            max_iters=max_iters,
            patience=patience,
            top_k=top_k,
        )

        self.logger.info(f"TabuSolver: Beste gefundene Lösung {objective_name} = {best_objective:.2f}")

        # finaler Schedule bauen
        final_objective, scheduled_ops = self._decode_sequence(best_sequence)
        assert abs(final_objective - best_objective) < 0.01, f"Objective mismatch: {final_objective} != {best_objective}"

        # Speichere besten schedule für spätere Analyse
        self.best_schedule = scheduled_ops
        
        schedule_job_collection = LiveJobCollection()
        for op_plan in scheduled_ops:
            orm_op = self.operation_lookup[(op_plan.job_idx, op_plan.op_idx)]
            schedule_job_collection.add_operation_instance(
                op=orm_op,
                new_start=int(op_plan.start),
                new_end=int(op_plan.end),
            )

        return schedule_job_collection, start_objective, best_objective

    # ------------------------------------------------------------------
    # Tabu-Suche selbst
    # ------------------------------------------------------------------
    def _tabu_search(
        self,
        start_seq: List[int],
        neigh_func: Callable[[List[int]], Iterable[Tuple[List[int], Tuple[int, int]]]],
        tabu_allowed: int = 25,
        max_iters: int = 800,
        patience: int = 40,
        top_k: int = 60,
    ):
        current_sequence = list(start_seq)
        current_objective, _ = self._decode_sequence(current_sequence)

        best_sequence = list(current_sequence)
        best_objective = current_objective

        snapshots = [("Start", list(current_sequence), current_objective)]
        tabu_list = deque(maxlen=tabu_allowed)
        iterations_without_improvement = 0
        
        objective_name = "Cmax" if self.objective == "makespan" else "Objective"

        self.logger.info(
            f"TabuSolver: Startsequenz {objective_name} = {current_objective:.2f}, "
            f"TabuAllowed={tabu_allowed}, MaxIters={max_iters}"
        )

        for iteration in range(1, max_iters + 1):
            raw_candidates = []
            for cand_seq, move in neigh_func(current_sequence):
                cand_objective, _ = self._decode_sequence(cand_seq)
                is_tabu = move in tabu_list
                raw_candidates.append((cand_objective, cand_seq, move, is_tabu))

            raw_candidates.sort(key=self._sort_key)

            chosen_tuple = None

            # (1) Aspiration: Verbesserung zulassen, auch wenn tabu
            for obj, cs, mv, is_tabu in raw_candidates:
                if is_tabu and obj >= best_objective:
                    continue
                if obj < current_objective:
                    chosen_tuple = (obj, cs, mv)
                    break

            # (2) Diversifikation
            if chosen_tuple is None:
                iterations_without_improvement += 1
                admissible = [
                    (obj, cs, mv)
                    for (obj, cs, mv, is_tabu) in raw_candidates
                    if (not is_tabu) or (obj < best_objective)
                ]
                if not admissible:
                    admissible = [(obj, cs, mv) for (obj, cs, mv, _) in raw_candidates]

                limited = admissible[: max(1, min(top_k, len(admissible)))]
                chosen_tuple = self.rng.choice(limited)

                if iterations_without_improvement >= patience:
                    # springe zur besten bekannten Nachbarlösung und leere Tabu-Liste
                    best_overall = raw_candidates[0]
                    chosen_tuple = (best_overall[0], best_overall[1], best_overall[2])
                    tabu_list.clear()
                    iterations_without_improvement = 0
            else:
                iterations_without_improvement = 0

            chosen_objective, chosen_sequence, chosen_move = chosen_tuple
            current_sequence = list(chosen_sequence)
            current_objective = chosen_objective
            snapshots.append((f"Iter {iteration:03d}", list(current_sequence), current_objective))

            tabu_list.append(chosen_move)
            tabu_list.append((chosen_move[1], chosen_move[0]))

            if current_objective < best_objective:
                best_objective = current_objective
                best_sequence = list(current_sequence)

            if iteration % 20 == 0:
                self.logger.info(
                    f"TabuSolver Iter {iteration:03d}: "
                    f"{objective_name}={current_objective:.2f}, Best={best_objective:.2f}, "
                    f"TabuSize={len(tabu_list)}"
                )

        return best_sequence, best_objective, snapshots
