"""
Führt 5 Termintreue-Experimente mit unterschiedlichen Gewichtungen aus.
20 Shifts pro Experiment, Ergebnisse in data/output_termintreue/
"""
from decimal import Decimal
from src.domain.Initializer import ExperimentInitializer
from src.Tabu_Experiment_Runner import run_experiment
from src.Logger import Logger
import time

# Logger Setup
logger = Logger(name="termintreue_experiments", log_file="termintreue_experiments.log")

# Basis-Parameter
source_name = "Fisher and Thompson 10x10"
max_bottleneck_utilization = 0.75
sim_sigma = 0.1
shift_length = 1440  # 24 Stunden
total_shift_number = 20  # Volle 20 Shifts

# Tabu-Parameter
tabu_allowed = 25
max_iters = 300
patience = 20
top_k = 20
objective = "lateness_deviation"
output_dir = "data/output_termintreue"

# 5 Gewichtungs-Konfigurationen
configurations = [
    {
        "name": "Earliness-Fokus",
        "w_t": 0.2,
        "w_e": 0.8,
        "w_dev": 0.5,
    },
    {
        "name": "Deviation + Earliness",
        "w_t": 0.3,
        "w_e": 0.7,
        "w_dev": 0.8,
    },
    {
        "name": "Balanced",
        "w_t": 0.5,
        "w_e": 0.5,
        "w_dev": 0.5,
    },
    {
        "name": "Deviation + Tardiness",
        "w_t": 0.6,
        "w_e": 0.4,
        "w_dev": 0.8,
    },
    {
        "name": "Tardiness-Fokus",
        "w_t": 0.8,
        "w_e": 0.2,
        "w_dev": 0.5,
    },
]

logger.info("=" * 100)
logger.info("TERMINTREUE-EXPERIMENTE: 5 Konfigurationen mit 20 Shifts")
logger.info("=" * 100)
logger.info(f"Quelle: {source_name}")
logger.info(f"Max Bottleneck Utilization: {max_bottleneck_utilization}")
logger.info(f"Shifts: {total_shift_number}")
logger.info(f"Output: {output_dir}/")
logger.info("=" * 100)

total_start = time.time()

for i, config in enumerate(configurations, start=1):
    logger.info(f"\n{'='*100}")
    logger.info(f"EXPERIMENT {i}/5: {config['name']}")
    logger.info(f"Gewichte: w_t={config['w_t']}, w_e={config['w_e']}, w_dev={config['w_dev']}")
    logger.info(f"{'='*100}")
    
    exp_start = time.time()
    
    try:
        # Erstelle neues Experiment in DB
        experiment_id = ExperimentInitializer.insert_experiment(
            source_name=source_name,
            max_bottleneck_utilization=Decimal(f"{max_bottleneck_utilization:.2f}"),
            absolute_lateness_ratio=config['w_t'],
            inner_tardiness_ratio=config['w_dev'],
            sim_sigma=sim_sigma,
            experiment_type=f"Termintreue_{config['name'].replace(' ', '_')}",
        )
        
        logger.info(f"✓ Experiment ID {experiment_id} erstellt")
        logger.info(f"Starte Tabu-Solver für {total_shift_number} Shifts...")
        
        # Führe Experiment aus
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
            output_dir=output_dir,
        )
        
        exp_time = time.time() - exp_start
        logger.info(f"✓ Experiment {i} abgeschlossen in {exp_time/60:.1f} Minuten")
        logger.info(f"  → CSV: {output_dir}/tabu_improvements_exp_{experiment_id}.csv")
        
    except Exception as e:
        logger.error(f"✗ Fehler bei Experiment {i}: {e}")
        import traceback
        traceback.print_exc()
        continue

total_time = time.time() - total_start

logger.info(f"\n{'='*100}")
logger.info(f"ALLE EXPERIMENTE ABGESCHLOSSEN")
logger.info(f"Gesamtzeit: {total_time/60:.1f} Minuten ({total_time/3600:.2f} Stunden)")
logger.info(f"Ergebnisse in: {output_dir}/")
logger.info(f"{'='*100}")
