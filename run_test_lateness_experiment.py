"""
Test-Skript für ein einzelnes Lateness-Experiment mit erweiterten Metriken.
Speichert Tardiness, Earliness und Deviation separat.
"""
from src.Logger import Logger
from src.Tabu_Experiment_Runner import run_experiment

# Setup Logger (log_file=None für nur Console-Ausgabe)
logger = Logger(name="test_experiment", log_file="test_lateness_exp.log")

# Neuer Output-Ordner für erweiterte Termintreue-Metriken
output_dir = "data/output_termintreue"

# Test-Experiment: Verwende bestehendes Experiment 17 (bestes aus Ranking)
experiment_id = 17  # Existierendes Experiment mit w_t=0.5, w_e=0.5, w_dev=0.5
shift_length = 1440  # 24 Stunden
total_shift_number = 2  # Nur 2 Shifts für schnellen Test

logger.info("=" * 80)
logger.info("TEST: Lateness-Experiment mit separaten Metriken")
logger.info("=" * 80)
logger.info(f"Experiment ID: {experiment_id}")
logger.info(f"Shifts: {total_shift_number}")
logger.info(f"Gewichte: w_t=0.5, w_e=0.5, w_dev=0.5 (aus Experiment-Config)")
logger.info("=" * 80)

try:
    run_experiment(
        experiment_id=experiment_id,
        shift_length=shift_length,
        total_shift_number=total_shift_number,
        logger=logger,
        tabu_allowed=25,
        max_iters=300,
        patience=40,
        top_k=60,
        objective="lateness_deviation",
        output_dir=output_dir,
    )
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ TEST ERFOLGREICH ABGESCHLOSSEN!")
    logger.info("=" * 80)
    logger.info("Prüfe die Ausgabe-Dateien:")
    logger.info(f"  - {output_dir}/tabu_improvements_exp_17.csv")
    logger.info(f"  - {output_dir}/tabu_config_exp_17.csv")
    logger.info("\nDie CSV sollte jetzt folgende Spalten enthalten:")
    logger.info("  • Initial/Final_Lateness_Deviation (gewichtet)")
    logger.info("  • Initial/Final_Tardiness")
    logger.info("  • Initial/Final_Earliness")
    logger.info("  • Initial/Final_Deviation")
    logger.info("  • Initial/Final_Termintreue (ungewichtet: T+E)")
    
except Exception as e:
    logger.error(f"❌ FEHLER: {e}")
    import traceback
    traceback.print_exc()
