#!/bin/bash
# Führe mehrere Tabu-Experimente parallel aus
# Usage: ./run_parallel_tabu_experiments.sh

# Anzahl paralleler Jobs (du hast 32 Kerne, also kannst du z.B. 5-10 parallel laufen lassen)
PARALLEL_JOBS=5

echo "Starting parallel Tabu experiments with ${PARALLEL_JOBS} jobs in parallel"

# Beispiel: Verschiedene Parameter-Kombinationen
# Format: tabu_allowed,max_iters,patience,top_k
export PARAMS_FILE=$(mktemp)
cat > $PARAMS_FILE << EOF
25,800,40,60
50,800,40,60
80,800,20,20
100,1000,30,40
120,1200,25,50
EOF

# Funktion für ein einzelnes Experiment
run_single_experiment() {
    local params=$1
    IFS=',' read -r tabu_allowed max_iters patience top_k <<< "$params"
    
    echo "Starting experiment: tabu_allowed=${tabu_allowed}, max_iters=${max_iters}, patience=${patience}, top_k=${top_k}"
    
    python3 -c "
import sys
sys.path.insert(0, '$(pwd)')
from src.Tabu_Experiment_Runner import run_experiment
from src.Logger import Logger
from src.domain.Initializer import ExperimentInitializer
from decimal import Decimal

experiment_id = ExperimentInitializer.insert_experiment(
    source_name='Fisher and Thompson 10x10',
    absolute_lateness_ratio=0.5,
    inner_tardiness_ratio=0.5,
    max_bottleneck_utilization=Decimal('0.75'),
    sim_sigma=0.1,
    experiment_type='Tabu_Parallel',
)

logger = Logger('tabu_parallel', f'tabu_exp_{experiment_id}_ta${tabu_allowed}.log')
run_experiment(
    experiment_id=experiment_id,
    shift_length=60*24,
    total_shift_number=20,
    logger=logger,
    tabu_allowed=${tabu_allowed},
    max_iters=${max_iters},
    patience=${patience},
    top_k=${top_k},
    objective='lateness_deviation'
)
print(f'Experiment {experiment_id} completed')
"
}

export -f run_single_experiment

# Starte parallel mit GNU parallel
if command -v parallel &> /dev/null; then
    cat $PARAMS_FILE | parallel -j $PARALLEL_JOBS run_single_experiment {}
else
    echo "GNU parallel not installed. Installing..."
    # Alternativ: Manuelle Schleife
    while IFS= read -r params; do
        run_single_experiment "$params" &
        # Limitiere Anzahl Background-Prozesse
        while [ $(jobs -r | wc -l) -ge $PARALLEL_JOBS ]; do
            sleep 1
        done
    done < $PARAMS_FILE
    wait
fi

rm $PARAMS_FILE
echo "All parallel experiments completed!"
