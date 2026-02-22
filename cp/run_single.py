# src/solvers/Tabu_Solver.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Iterable, Callable, Dict, Optional
from collections import deque
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
    Einfache Tabu-Suche auf Makespan für Job-Shop-Instanzen.

    - Liest Jobs aus LiveJobCollection
    - ignoriert Due Dates etc., Ziel ist nur Cmax-Minimierung
    - liefert einen LiveJobCollection-Schedule zurück
    """

    def __init__(
        self,
        jobs_collection: LiveJobCollection,
        logger: Logger,
        rng: Optional[random.Random] = None,
    ) -> None:
        self.logger = logger
        self.jobs_collection = jobs_collection
        self.rng = rng or random.Random()

        # interne Repräsentation: Jobs [(machine_idx, duration), ...]
        self.jobs: List[List[Tuple[int, int]]] = []
        self.machine_name_to_idx: Dict[str, int] = {}
        self.machine_idx_to_name: List[str] = []
        self.operation_lookup: Dict[Tuple[int, int], JobOperation] = {}

        self._build_internal_problem()

    # ------------------------------------------------------------------
    # Problemaufbau
    # ------------------------------------------------------------------
    def _build_internal_problem(self) -> None:
        """
        Mappt die LiveJobCollection auf (job,op)->(machine_idx,duration)
        und merkt sich den Link zurück zur JobOperation.
        """

        # sicherstellen, dass die Reihenfolge stabil ist
        try:
            self.jobs_collection.sort_jobs_by_id()
        except AttributeError:
            # falls es die Methode in deiner Version nicht gibt, ignorieren
            pass
        try:
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
            for op_idx, op in enumerate(job.operations):
                m_name = op.machine_name
                if m_name not in self.machine_name_to_idx:
                    self.machine_name_to_idx[m_name] = machine_counter
                    self.machine_idx_to_name.append(m_name)
                    machine_counter += 1
                m_idx = self.machine_name_to_idx[m_name]

                # Dauer: wir nehmen die "normale" Dauer
                duration = int(getattr(op, "duration", 0))
                if duration <= 0 and hasattr(op, "sim_duration"):
                    duration = int(op.sim_duration)

                job_ops.append((m_idx, duration))
                self.operation_lookup[(job_idx, op_idx)] = op
            self.jobs.append(job_ops)

        if not self.jobs:
            raise ValueError("TabuSolver: jobs_collection enthält keine Operationen.")

        self.num_jobs = len(self.jobs)
        self.ops_per_job = len(self.jobs[0])
        self.num_machines = len(self.machine_name_to_idx)

        self.logger.info(
            f"TabuSolver: {self.num_jobs} Jobs, {self.ops_per_job} Ops/Job, "
            f"{self.num_machines} Maschinen"
        )

    # ------------------------------------------------------------------
    # Hilfsfunktionen (Tabu-Algorithmus)
    # ------------------------------------------------------------------
    def _decode_sequence(self, sequence: List[int]) -> Tuple[int, List[OperationPlan]]:
        """
        Dekodiert eine Job-Sequenz in einen Schedule (Cmax + Operationen).
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

        makespan = max(op.end for op in scheduled)
        return makespan, scheduled

    def _generate_random_start_sequence(self) -> List[int]:
        seq = [j for j in range(self.num_jobs) for _ in range(self.ops_per_job)]
        self.rng.shuffle(seq)
        return seq

    def _neighbors_insertion(
        self, sequence: List[int]
    ) -> Iterable[Tuple[List[int], Tuple[int, int]]]:
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
    ) -> LiveJobCollection:
        """
        Führt Tabu-Suche aus und gibt einen neuen LiveJobCollection-Schedule zurück.
        """
        start_sequence = self._generate_random_start_sequence()
        start_cmax, _ = self._decode_sequence(start_sequence)
        self.logger.info(f"TabuSolver: Start-Cmax = {start_cmax}")

        best_sequence, best_makespan, _ = self._tabu_search(
            start_seq=start_sequence,
            neigh_func=self._neighbors_insertion,
            tabu_allowed=tabu_allowed,
            max_iters=max_iters,
            patience=patience,
            top_k=top_k,
        )

        self.logger.info(f"TabuSolver: Beste gefundene Lösung Cmax = {best_makespan}")

        # finaler Schedule
        final_cmax, scheduled_ops = self._decode_sequence(best_sequence)
        assert final_cmax == best_makespan

        schedule_job_collection = LiveJobCollection()
        for op_plan in scheduled_ops:
            orm_op = self.operation_lookup[(op_plan.job_idx, op_plan.op_idx)]
            schedule_job_collection.add_operation_instance(
                op=orm_op,
                new_start=int(op_plan.start),
                new_end=int(op_plan.end),
            )

        return schedule_job_collection

    # ------------------------------------------------------------------
    # Tabu-Suche (interner Algorithmus)
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
        current_makespan, _ = self._decode_sequence(current_sequence)

        best_sequence = list(current_sequence)
        best_makespan = current_makespan

        snapshots = [("Start", list(current_sequence), current_makespan)]
        tabu_list = deque(maxlen=tabu_allowed)
        iterations_without_improvement = 0

        self.logger.info(
            f"TabuSolver: Startsequenz Cmax = {current_makespan}, "
            f"TabuAllowed={tabu_allowed}, MaxIters={max_iters}"
        )

        for iteration in range(1, max_iters + 1):
            raw_candidates = []
            for cand_seq, move in neigh_func(current_sequence):
                cand_makespan, _ = self._decode_sequence(cand_seq)
                is_tabu = move in tabu_list
                raw_candidates.append((cand_makespan, cand_seq, move, is_tabu))

            raw_candidates.sort(key=self._sort_key)

            chosen_tuple = None

            # Aspiration: Verbesserung oder besser als globale beste Lösung
            for cm, cs, mv, is_tabu in raw_candidates:
                if is_tabu and cm >= best_makespan:
                    continue
                if cm < current_makespan:
                    chosen_tuple = (cm, cs, mv)
                    break

            # Diversifikation
            if chosen_tuple is None:
                iterations_without_improvement += 1
                admissible = [
                    (cm, cs, mv)
                    for (cm, cs, mv, is_tabu) in raw_candidates
                    if (not is_tabu) or (cm < best_makespan)
                ]
                if not admissible:
                    admissible = [(cm, cs, mv) for (cm, cs, mv, _) in raw_candidates]

                limited = admissible[: max(1, min(top_k, len(admissible)))]
                chosen_tuple = self.rng.choice(limited)

                if iterations_without_improvement >= patience:
                    # springe zur besten gefundenen Nachbarlösung
                    best_overall = raw_candidates[0]
                    chosen_tuple = (best_overall[0], best_overall[1], best_overall[2])
                    tabu_list.clear()
                    iterations_without_improvement = 0
            else:
                iterations_without_improvement = 0

            chosen_makespan, chosen_sequence, chosen_move = chosen_tuple
            current_sequence = list(chosen_sequence)
            current_makespan = chosen_makespan
            snapshots.append((f"Iter {iteration:03d}", list(current_sequence), current_makespan))

            tabu_list.append(chosen_move)
            tabu_list.append((chosen_move[1], chosen_move[0]))

            if current_makespan < best_makespan:
                best_makespan = current_makespan
                best_sequence = list(current_sequence)

            if iteration % 20 == 0:
                self.logger.info(
                    f"TabuSolver Iter {iteration:03d}: "
                    f"Cmax={current_makespan}, Best={best_makespan}, "
                    f"TabuSize={len(tabu_list)}"
                )

        return best_sequence, best_makespan, snapshots
