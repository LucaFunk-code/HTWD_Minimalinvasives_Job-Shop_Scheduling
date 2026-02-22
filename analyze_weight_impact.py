"""
Analyze the impact of different weight configurations on delivery performance.
Usage: python3 analyze_weight_impact.py [experiment_ids...]

Example:
    python3 analyze_weight_impact.py 101 102 103 104 105
    
Or analyze all experiments of a specific type:
    python3 analyze_weight_impact.py --type Tabu_Weight
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
import pandas as pd
from decimal import Decimal

# Project root in path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def analyze_experiments(experiment_ids: list[int]) -> pd.DataFrame:
    """
    Analysiert die Ergebnisse mehrerer Experimente.
    
    Args:
        experiment_ids: Liste der Experiment-IDs
        
    Returns:
        DataFrame mit allen relevanten Metriken
    """
    from src.domain.Query import ExperimentQuery
    from src.domain.orm_models import Experiment
    
    results = []
    
    for exp_id in experiment_ids:
        try:
            experiment = ExperimentQuery.get_experiment(exp_id)
            
            if experiment is None:
                print(f"Warning: Experiment {exp_id} not found in database")
                continue
            
            # Extrahiere Gewichte
            w_t = float(experiment.absolute_lateness_ratio)
            w_e = 1.0 - w_t
            w_dev = float(experiment.inner_tardiness_ratio)
            
            # Sammle Metriken aus den SimulationJobs
            simulation_jobs = experiment.simulation_jobs
            
            if not simulation_jobs:
                print(f"Warning: Experiment {exp_id} has no simulation results")
                continue
            
            # Berechne Durchschnittswerte aus allen Simulations-Jobs
            total_tardiness = sum(float(sj.tardiness or 0) for sj in simulation_jobs)
            total_earliness = sum(float(sj.earliness or 0) for sj in simulation_jobs)
            total_lateness = sum(abs(float(sj.lateness or 0)) for sj in simulation_jobs)
            num_jobs = len(simulation_jobs)
            
            # Durchschnitt pro Job
            avg_tardiness = total_tardiness / num_jobs if num_jobs > 0 else 0
            avg_earliness = total_earliness / num_jobs if num_jobs > 0 else 0
            avg_deviation = total_lateness / num_jobs if num_jobs > 0 else 0  # Absolute Abweichung
            
            # Makespan aus ScheduleJobs (letzter Endzeitpunkt)
            schedule_jobs = experiment.schedule_jobs
            avg_makespan = 0
            if schedule_jobs:
                max_end_time = max((float(sj.end_time or 0) for sj in schedule_jobs), default=0)
                avg_makespan = max_end_time
            
            # Berechne Termintreue-Score (wie in der Zielfunktion)
            # Score = w_t * tardiness + w_e * earliness + w_dev * deviation
            termintreue_score = w_t * avg_tardiness + w_e * avg_earliness + w_dev * avg_deviation
            
            results.append({
                "experiment_id": exp_id,
                "experiment_type": experiment.experiment_type,
                "w_t (Tardiness)": w_t,
                "w_e (Earliness)": w_e,
                "w_dev (Deviation)": w_dev,
                "avg_tardiness": avg_tardiness,
                "avg_earliness": avg_earliness,
                "avg_deviation": avg_deviation,
                "avg_makespan": avg_makespan,
                "termintreue_score": termintreue_score,
                "num_jobs": num_jobs,
                "utilization": float(experiment.max_bottleneck_utilization),
                "sim_sigma": experiment.sim_sigma,
            })
            
        except Exception as e:
            print(f"Error analyzing experiment {exp_id}: {e}")
            continue
    
    if not results:
        print("No valid results found!")
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    return df


def print_analysis(df: pd.DataFrame):
    """
    Druckt eine übersichtliche Analyse der Ergebnisse.
    """
    if df.empty:
        print("No data to analyze!")
        return
    
    print("\n" + "=" * 120)
    print("GEWICHTSANALYSE - AUSWIRKUNG AUF TERMINTREUE")
    print("=" * 120)
    
    # Sortiere nach Experiment-Typ
    df_sorted = df.sort_values("experiment_type")
    
    print("\nÜBERSICHT:")
    print("-" * 120)
    for _, row in df_sorted.iterrows():
        print(f"\n📊 Experiment {row['experiment_id']} - {row['experiment_type']}")
        print(f"   Gewichte: w_t={row['w_t (Tardiness)']:.2f}, "
              f"w_e={row['w_e (Earliness)']:.2f}, "
              f"w_dev={row['w_dev (Deviation)']:.2f}")
        print(f"   Ergebnisse:")
        print(f"     • Durchschn. Verspätung (Tardiness): {row['avg_tardiness']:.2f} Minuten")
        print(f"     • Durchschn. Frühlieferung (Earliness): {row['avg_earliness']:.2f} Minuten")
        print(f"     • Durchschn. Abweichung (Deviation): {row['avg_deviation']:.2f} Minuten")
        print(f"     • Durchschn. Makespan: {row['avg_makespan']:.2f} Minuten")
        print(f"     • Termintreue-Score: {row['termintreue_score']:.4f}")
    
    print("\n" + "=" * 120)
    print("VERGLEICHSTABELLE")
    print("=" * 120)
    
    # Erstelle Vergleichstabelle
    compare_df = df[["experiment_id", "experiment_type", "w_t (Tardiness)", 
                     "w_e (Earliness)", "w_dev (Deviation)", 
                     "avg_tardiness", "avg_earliness", "avg_deviation", 
                     "termintreue_score"]].copy()
    
    print(compare_df.to_string(index=False))
    
    print("\n" + "=" * 120)
    print("RANKING")
    print("=" * 120)
    
    # Rankings
    print("\n🏆 Beste Experimente nach verschiedenen Kriterien:\n")
    
    print("1. NIEDRIGSTE VERSPÄTUNG (Tardiness):")
    best_tardiness = df.nsmallest(3, "avg_tardiness")
    for i, (_, row) in enumerate(best_tardiness.iterrows(), 1):
        print(f"   {i}. Exp {row['experiment_id']} ({row['experiment_type']}): "
              f"{row['avg_tardiness']:.2f} min (w_t={row['w_t (Tardiness)']:.2f})")
    
    print("\n2. NIEDRIGSTE FRÜHLIEFERUNG (Earliness):")
    best_earliness = df.nsmallest(3, "avg_earliness")
    for i, (_, row) in enumerate(best_earliness.iterrows(), 1):
        print(f"   {i}. Exp {row['experiment_id']} ({row['experiment_type']}): "
              f"{row['avg_earliness']:.2f} min (w_e={row['w_e (Earliness)']:.2f})")
    
    print("\n3. NIEDRIGSTE ABWEICHUNG (Deviation):")
    best_deviation = df.nsmallest(3, "avg_deviation")
    for i, (_, row) in enumerate(best_deviation.iterrows(), 1):
        print(f"   {i}. Exp {row['experiment_id']} ({row['experiment_type']}): "
              f"{row['avg_deviation']:.2f} min (w_dev={row['w_dev (Deviation)']:.2f})")
    
    print("\n4. BESTER TERMINTREUE-SCORE (niedriger = besser):")
    best_score = df.nsmallest(3, "termintreue_score")
    for i, (_, row) in enumerate(best_score.iterrows(), 1):
        print(f"   {i}. Exp {row['experiment_id']} ({row['experiment_type']}): "
              f"Score={row['termintreue_score']:.4f}")
    
    print("\n" + "=" * 120)
    print("ERKENNTNISSE")
    print("=" * 120)
    
    # Korrelationsanalyse
    print("\n📈 Korrelation zwischen Gewichten und Ergebnissen:\n")
    
    corr_tardiness = df[["w_t (Tardiness)", "avg_tardiness"]].corr().iloc[0, 1]
    corr_earliness = df[["w_e (Earliness)", "avg_earliness"]].corr().iloc[0, 1]
    corr_deviation = df[["w_dev (Deviation)", "avg_deviation"]].corr().iloc[0, 1]
    
    print(f"   • w_t vs. Tardiness: {corr_tardiness:.3f}")
    print(f"     → {'Höheres w_t reduziert Verspätungen' if corr_tardiness < 0 else 'Überraschend: Höheres w_t erhöht Verspätungen'}")
    
    print(f"   • w_e vs. Earliness: {corr_earliness:.3f}")
    print(f"     → {'Höheres w_e reduziert Frühlieferungen' if corr_earliness < 0 else 'Überraschend: Höheres w_e erhöht Frühlieferungen'}")
    
    print(f"   • w_dev vs. Deviation: {corr_deviation:.3f}")
    print(f"     → {'Höheres w_dev reduziert Abweichungen' if corr_deviation < 0 else 'Überraschend: Höheres w_dev erhöht Abweichungen'}")
    
    print("\n" + "=" * 120)


def save_results(df: pd.DataFrame, output_file: str = None):
    """
    Speichert die Ergebnisse in eine CSV-Datei.
    """
    if df.empty:
        return
    
    if output_file is None:
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "weight_analysis_results.csv"
    
    df.to_csv(output_file, index=False)
    print(f"\n💾 Ergebnisse gespeichert in: {output_file}")


def main():
    """
    Hauptfunktion für die Analyse.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze weight impact on delivery performance"
    )
    parser.add_argument(
        "experiment_ids",
        nargs="*",
        type=int,
        help="List of experiment IDs to analyze"
    )
    parser.add_argument(
        "--type",
        type=str,
        help="Analyze all experiments of a specific type (e.g., 'Tabu_Weight')"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output CSV file path (default: data/output/weight_analysis_results.csv)"
    )
    
    args = parser.parse_args()
    
    # Bestimme welche Experimente analysiert werden sollen
    experiment_ids = []
    
    if args.type:
        # Lade alle Experimente dieses Typs aus der DB
        from src.domain.Query import ExperimentQuery
        from src.domain.orm_models import Experiment
        from src.domain.orm_models import get_session
        
        session = get_session()
        experiments = session.query(Experiment).filter(
            Experiment.experiment_type.like(f"%{args.type}%")
        ).all()
        
        experiment_ids = [exp.id for exp in experiments]
        print(f"Found {len(experiment_ids)} experiments of type '{args.type}'")
        
    elif args.experiment_ids:
        experiment_ids = args.experiment_ids
    else:
        print("Error: Please provide experiment IDs or use --type to filter by experiment type")
        print("\nExamples:")
        print("  python3 analyze_weight_impact.py 101 102 103 104 105")
        print("  python3 analyze_weight_impact.py --type Tabu_Weight")
        sys.exit(1)
    
    if not experiment_ids:
        print("No experiments to analyze!")
        sys.exit(1)
    
    print(f"\nAnalyzing {len(experiment_ids)} experiments: {experiment_ids}\n")
    
    # Analysiere die Experimente
    df = analyze_experiments(experiment_ids)
    
    if df.empty:
        print("No valid data found!")
        sys.exit(1)
    
    # Zeige Analyse
    print_analysis(df)
    
    # Speichere Ergebnisse
    save_results(df, args.output)


if __name__ == "__main__":
    main()
