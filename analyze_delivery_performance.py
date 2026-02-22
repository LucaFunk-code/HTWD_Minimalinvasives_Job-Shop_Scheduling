"""
Analyze delivery performance metrics (Tardiness, Earliness, Lateness) from experiments.
Provides factual production KPIs instead of meta-metrics like "improvement %".
"""
import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from pathlib import Path
from src.domain.orm_models import Experiment, SimulationJob
from src.domain.orm_setup import SessionLocal

def calculate_job_metrics(sim_job):
    """Calculate tardiness, earliness, and lateness for a single job."""
    if not sim_job.operations:
        return None
    
    # Get completion time (end of last operation)
    completion_time = max(op.end for op in sim_job.operations)
    due_date = sim_job.due_date
    
    # Calculate lateness (positive = tardy, negative = early)
    lateness = completion_time - due_date
    
    return {
        'tardiness': max(0, lateness),  # max(0, C_j - d_j)
        'earliness': max(0, -lateness),  # max(0, d_j - C_j)
        'lateness': abs(lateness),       # |C_j - d_j|
        'completion_time': completion_time,
        'due_date': due_date,
        'is_tardy': lateness > 0,
        'is_early': lateness < 0,
        'is_on_time': lateness == 0,
    }


def analyze_experiment(exp_id):
    """Analyze delivery performance for a single experiment."""
    with SessionLocal() as session:
        try:
            experiment = session.query(Experiment).filter(Experiment.id == exp_id).first()
            
            if not experiment:
                return None
            
            sim_jobs = experiment.simulation_jobs
            if not sim_jobs:
                return None
            
            # Calculate metrics for each job
            job_metrics = []
            for sim_job in sim_jobs:
                metrics = calculate_job_metrics(sim_job)
                if metrics:
                    job_metrics.append(metrics)
            
            if not job_metrics:
                return None
            
            df_jobs = pd.DataFrame(job_metrics)
            
            # Extract weights
            w_t = float(experiment.absolute_lateness_ratio)
            w_e = 1.0 - w_t
            w_dev = float(experiment.inner_tardiness_ratio)
            
            return {
                'experiment_id': exp_id,
                'w_t': w_t,
                'w_e': w_e,
                'w_dev': w_dev,
                'mean_tardiness': df_jobs['tardiness'].mean(),
                'mean_earliness': df_jobs['earliness'].mean(),
                'mean_lateness': df_jobs['lateness'].mean(),
                'on_time_rate': df_jobs['is_on_time'].mean() * 100,
                'num_jobs': len(df_jobs),
            }
        except Exception as e:
            print(f"Error {exp_id}: {e}")
            return None


def main():
    print("\n" + "=" * 120)
    print("DELIVERY PERFORMANCE ANALYSIS - Factual Production KPIs")
    print("=" * 120)
    
    exp_ids = [23, 24, 25, 26, 27] + list(range(38, 48))
    
    results = []
    for exp_id in exp_ids:
        print(f"Analyzing Exp {exp_id}...", end=" ")
        result = analyze_experiment(exp_id)
        if result:
            results.append(result)
            print("✓")
        else:
            print("✗")
    
    df = pd.DataFrame(results)
    
    if df.empty:
        print("No data!")
        return
    
    # Print results
    print("\n" + "=" * 120)
    print("RESULTS")
    print("=" * 120)
    print(f"\n{'ID':<6} {'w_t':<6} {'w_e':<6} {'w_dev':<6} {'Tardiness':<12} {'Earliness':<12} {'Lateness':<12} {'On-Time%':<10}")
    print("-" * 120)
    
    for _, row in df.sort_values('experiment_id').iterrows():
        print(f"{row['experiment_id']:<6.0f} {row['w_t']:<6.2f} {row['w_e']:<6.2f} {row['w_dev']:<6.2f} "
              f"{row['mean_tardiness']:<12.1f} {row['mean_earliness']:<12.1f} {row['mean_lateness']:<12.1f} "
              f"{row['on_time_rate']:<10.1f}")
    
    # Correlations
    print("\n" + "=" * 120)
    print("CORRELATIONS (how weights affect metrics)")
    print("=" * 120)
    
    corr_wt_tard = df[['w_t', 'mean_tardiness']].corr().iloc[0, 1]
    corr_wt_earl = df[['w_t', 'mean_earliness']].corr().iloc[0, 1]
    corr_wdev_late = df[['w_dev', 'mean_lateness']].corr().iloc[0, 1]
    
    print(f"\nw_t → Tardiness:    {corr_wt_tard:>7.3f}  ({'↓ Better' if corr_wt_tard < 0 else '↑ Worse'})")
    print(f"w_t → Earliness:    {corr_wt_earl:>7.3f}  ({'↓ Better' if corr_wt_earl < 0 else '↑ Worse'})")
    print(f"w_dev → Lateness:   {corr_wdev_late:>7.3f}  ({'↓ Better' if corr_wdev_late < 0 else '↑ Worse'})")
    
    # Best configs
    print("\n" + "=" * 120)
    print("BEST CONFIGURATIONS")
    print("=" * 120)
    
    best_tard = df.loc[df['mean_tardiness'].idxmin()]
    best_earl = df.loc[df['mean_earliness'].idxmin()]
    best_late = df.loc[df['mean_lateness'].idxmin()]
    
    print(f"\nLowest Tardiness:  Exp {best_tard['experiment_id']:.0f} (w_t={best_tard['w_t']:.2f}, w_dev={best_tard['w_dev']:.2f}) → {best_tard['mean_tardiness']:.1f} min")
    print(f"Lowest Earliness:  Exp {best_earl['experiment_id']:.0f} (w_t={best_earl['w_t']:.2f}, w_dev={best_earl['w_dev']:.2f}) → {best_earl['mean_earliness']:.1f} min")
    print(f"Lowest Lateness:   Exp {best_late['experiment_id']:.0f} (w_t={best_late['w_t']:.2f}, w_dev={best_late['w_dev']:.2f}) → {best_late['mean_lateness']:.1f} min")
    
    # Save
    output = Path("data/output/delivery_performance_analysis.csv")
    df.to_csv(output, index=False)
    print(f"\n💾 Saved: {output}")
    
    print("\n" + "=" * 120)
    print("✅ COMPLETE - All metrics are factual production KPIs!")
    print("=" * 120)


if __name__ == "__main__":
    main()
