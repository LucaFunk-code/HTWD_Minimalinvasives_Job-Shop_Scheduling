"""
Übersichtliche Darstellung der Lateness Deviation Rankings.
Sortiert nach bester Termintreue (niedrigste Lateness Deviation).
"""
import pandas as pd
import numpy as np
from pathlib import Path


def load_all_experiments():
    """Lade alle Experiment-Ergebnisse."""
    output_dir = Path("data/output")
    
    experiments = []
    
    # Suche nach allen tabu_improvements Dateien
    for file in sorted(output_dir.glob("tabu_improvements_exp_*.csv")):
        try:
            df = pd.read_csv(file)
            if 'Final_Lateness_Deviation' in df.columns:
                exp_id = df['Experiment_ID'].iloc[0]
                
                # Lade Config
                config_file = output_dir / f"tabu_config_exp_{exp_id}.csv"
                config = None
                if config_file.exists():
                    config = pd.read_csv(config_file).iloc[0]
                
                # Berechne Metriken (pro Shift normalisiert für Vergleichbarkeit)
                num_shifts = len(df)
                exp_data = {
                    'Exp_ID': int(exp_id),
                    'Solver': 'tb',
                    'Initial_Lateness_Dev_Total': df['Initial_Lateness_Deviation'].sum(),
                    'Final_Lateness_Dev_Total': df['Final_Lateness_Deviation'].sum(),
                    'Initial_Lateness_Dev': df['Initial_Lateness_Deviation'].mean(),  # Pro Shift
                    'Final_Lateness_Dev': df['Final_Lateness_Deviation'].mean(),  # Pro Shift
                    'Final_Lateness_Dev_Median': df['Final_Lateness_Deviation'].median(),  # Median pro Shift
                    'Final_Lateness_Dev_Std': df['Final_Lateness_Deviation'].std(),  # Stabilität
                    'Final_Lateness_Dev_Min': df['Final_Lateness_Deviation'].min(),
                    'Final_Lateness_Dev_Max': df['Final_Lateness_Deviation'].max(),
                    'Tardiness': 0,  # Nicht separat gespeichert
                    'Earliness': 0,  # Nicht separat gespeichert
                    'Makespan': 0,   # Nicht separat gespeichert
                    'Improvement': df['Improvement'].sum(),
                    'Improvement_%': df['Improvement_Percent'].mean(),
                    'Num_Shifts': num_shifts,
                    'Runtime_s': df['Solve_Time_Seconds'].sum(),
                    'Avg_Runtime_s': df['Solve_Time_Seconds'].mean(),
                    'Mem_MB': df['Memory_MB'].mean() if 'Memory_MB' in df.columns else 0,
                    'Peak_Mem_MB': df['Memory_MB'].max() if 'Memory_MB' in df.columns else 0,
                }
                
                # Füge Config-Parameter hinzu
                if config is not None:
                    exp_data.update({
                        'Objective': 'lateness_deviation',
                        'w_t': float(config['w_t']) if 'w_t' in config else 1,
                        'w_e': float(config['w_e']) if 'w_e' in config else 1,
                        'w_dev': float(config['w_dev']) if 'w_dev' in config else 1,
                        'SA_Iter': int(config['max_iters']) if 'max_iters' in config else 0,
                        'Temp': f"{config['temperature_start']:.1f}/{config['temperature_end']:.1f}" if 'temperature_start' in config else "?",
                    })
                
                experiments.append(exp_data)
        except Exception as e:
            print(f"Fehler beim Laden von {file.name}: {e}")
            continue
    
    return pd.DataFrame(experiments)


def print_performance_ranking_detailed(df):
    """Zeige detailliertes Ranking mit Stabilität."""
    df_sorted = df.sort_values('Final_Lateness_Dev_Median', ascending=True).reset_index(drop=True)
    df_sorted['Rank'] = range(1, len(df_sorted) + 1)
    
    print("\n" + "=" * 180)
    print("PERFORMANCE RANKING - Sortiert nach MEDIAN Lateness Deviation (robuster gegen Ausreißer)")
    print("=" * 180)
    
    # Header
    print(f"{'Rank':<6} | {'Exp ID':<7} | {'Solver':<7} | {'Median LD':<11} | {'Mean LD':<11} | {'Std Dev':<11} | {'Min LD':<11} | {'Max LD':<11} | {'Shifts':<7} | {'Improve %':<10} | {'Runtime (s)':<12}")
    print("-" * 180)
    
    # Data
    for _, row in df_sorted.iterrows():
        # Variationskoeffizient als Stabilitätsindikator
        cv = (row['Final_Lateness_Dev_Std'] / row['Final_Lateness_Dev']) * 100 if row['Final_Lateness_Dev'] > 0 else 0
        print(f"{int(row['Rank']):<6} | {int(row['Exp_ID']):<7} | {row['Solver']:<7} | {row['Final_Lateness_Dev_Median']:<11.1f} | {row['Final_Lateness_Dev']:<11.1f} | {row['Final_Lateness_Dev_Std']:<11.1f} | {row['Final_Lateness_Dev_Min']:<11.1f} | {row['Final_Lateness_Dev_Max']:<11.1f} | {int(row['Num_Shifts']):<7} | {row['Improvement_%']:<10.2f} | {row['Runtime_s']:<12.1f}")
    
    print("=" * 180)
    print("\nHinweis:")
    print("  • Median LD: Robuster Mittelwert (unempfindlich gegen Ausreißer)")
    print("  • Std Dev: Standardabweichung (niedrig = stabil, hoch = instabil)")
    print("  • Min/Max LD: Beste und schlechteste Shift-Ergebnisse")
    print()


def print_performance_ranking(df):
    """Zeige Performance Ranking nach Lateness Deviation (Standard-Ansicht)."""
    df_sorted = df.sort_values('Final_Lateness_Dev', ascending=True).reset_index(drop=True)
    df_sorted['Rank'] = range(1, len(df_sorted) + 1)
    
    print("\n" + "=" * 180)
    print("PERFORMANCE RANKING (Sortiert nach MEAN Lateness Deviation)")
    print("=" * 180)
    
    # Header
    print(f"{'Rank':<6} | {'Exp ID':<7} | {'Solver':<7} | {'Lateness Dev':<13} | {'Tardiness':<11} | {'Earliness':<11} | {'Makespan':<10} | {'Runtime (s)':<12} | {'Mem (MB)':<9} | {'Peak Mem (MB)':<14} | {'Shifts':<7} | {'Improve %':<10}")
    print("-" * 180)
    
    # Data
    for _, row in df_sorted.iterrows():
        print(f"{int(row['Rank']):<6} | {int(row['Exp_ID']):<7} | {row['Solver']:<7} | {row['Final_Lateness_Dev']:<13.1f} | {row['Tardiness']:<11.0f} | {row['Earliness']:<11.0f} | {row['Makespan']:<10.0f} | {row['Runtime_s']:<12.1f} | {row['Mem_MB']:<9.1f} | {row['Peak_Mem_MB']:<14.1f} | {int(row['Num_Shifts']):<7} | {row['Improvement_%']:<10.4f}")
    
    print("=" * 180)
    print("\nHinweis: Lateness Deviation = Durchschnittswert pro Shift (Mean, kann durch Ausreißer beeinflusst sein)")


def print_experiment_parameters(df):
    """Zeige Experiment-Parameter sortiert nach Lateness Deviation."""
    df_sorted = df.sort_values('Final_Lateness_Dev', ascending=True).reset_index(drop=True)
    
    print("\n" + "=" * 150)
    print("EXPERIMENT PARAMETERS")
    print("=" * 150)
    
    # Header
    print(f"{'Exp ID':<7} | {'Solver':<7} | {'Objective':<20} | {'w_t':<5} | {'w_e':<5} | {'w_dev':<6} | {'SA Iter':<10} | {'Final LD':<12} | {'Improve %':<10} | {'Runtime (s)':<12}")
    print("-" * 150)
    
    # Data
    for _, row in df_sorted.iterrows():
        print(f"{int(row['Exp_ID']):<7} | {row['Solver']:<7} | {row.get('Objective', 'lateness_deviation'):<20} | {row.get('w_t', 1):<5.1f} | {row.get('w_e', 1):<5.1f} | {row.get('w_dev', 1):<6.1f} | {row.get('SA_Iter', 0):<10.0f} | {row['Final_Lateness_Dev']:<12.1f} | {row['Improvement_%']:<10.2f} | {row['Runtime_s']:<12.1f}")
    
    print("=" * 150)


def print_top_experiments(df, n=10):
    """Zeige die besten N Experimente."""
    df_sorted = df.sort_values('Final_Lateness_Dev', ascending=True).head(n)
    
    print(f"\n" + "=" * 150)
    print(f"TOP {n} EXPERIMENTE (Niedrigste Lateness Deviation)")
    print("=" * 150)
    
    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        print(f"\n#{i} - Experiment {int(row['Exp_ID'])}")
        print(f"    Initial Lateness Dev: {row['Initial_Lateness_Dev']:.1f}")
        print(f"    Final Lateness Dev:   {row['Final_Lateness_Dev']:.1f}")
        print(f"    Verbesserung:         {row['Improvement']:.1f} ({row['Improvement_%']:.2f}%)")
        print(f"    Anzahl Shifts:        {int(row['Num_Shifts'])}")
        print(f"    Runtime:              {row['Runtime_s']:.1f} s (Ø {row['Avg_Runtime_s']:.1f} s/Shift)")
        print(f"    Peak Memory:          {row['Peak_Mem_MB']:.1f} MB")
        if 'w_t' in row:
            print(f"    Gewichte:             w_t={row['w_t']:.1f}, w_e={row['w_e']:.1f}, w_dev={row['w_dev']:.1f}")
        if 'SA_Iter' in row:
            print(f"    SA Iterationen:       {row['SA_Iter']:.0f}")


def analyze_weight_impact(df):
    """Analysiere den Einfluss der Gewichte."""
    if 'w_t' not in df.columns or 'w_dev' not in df.columns:
        return
    
    print(f"\n" + "=" * 150)
    print("GEWICHTUNGS-ANALYSE")
    print("=" * 150)
    
    # Gruppiere nach Gewichten
    grouped = df.groupby(['w_t', 'w_e', 'w_dev']).agg({
        'Initial_Lateness_Dev': ['mean'],
        'Final_Lateness_Dev': ['mean', 'min', 'max', 'count'],
        'Improvement_%': ['mean', 'std'],
    }).round(1)
    
    print("\nLateness Deviation nach Gewichtskombination:")
    print(grouped)
    
    # Beste Gewichtskombination
    best_weight = df.loc[df['Final_Lateness_Dev'].idxmin()]
    print(f"\n✅ BESTE GEWICHTSKOMBINATION:")
    print(f"   Experiment {int(best_weight['Exp_ID'])}: w_t={best_weight['w_t']:.1f}, w_e={best_weight['w_e']:.1f}, w_dev={best_weight['w_dev']:.1f}")
    print(f"   Initial Lateness Dev:  {best_weight['Initial_Lateness_Dev']:.1f}")
    print(f"   Final Lateness Dev:    {best_weight['Final_Lateness_Dev']:.1f}")
    print(f"   Verbesserung:          {best_weight['Improvement_%']:.2f}%")
    
    # Schlechteste Gewichtskombination
    worst_weight = df.loc[df['Final_Lateness_Dev'].idxmax()]
    print(f"\n❌ SCHLECHTESTE GEWICHTSKOMBINATION:")
    print(f"   Experiment {int(worst_weight['Exp_ID'])}: w_t={worst_weight['w_t']:.1f}, w_e={worst_weight['w_e']:.1f}, w_dev={worst_weight['w_dev']:.1f}")
    print(f"   Initial Lateness Dev:  {worst_weight['Initial_Lateness_Dev']:.1f}")
    print(f"   Final Lateness Dev:    {worst_weight['Final_Lateness_Dev']:.1f}")
    print(f"   Verbesserung:          {worst_weight['Improvement_%']:.2f}%")
    
    # Differenz
    diff = worst_weight['Final_Lateness_Dev'] - best_weight['Final_Lateness_Dev']
    print(f"\n📊 DIFFERENZ: {diff:.1f} (Faktor {worst_weight['Final_Lateness_Dev']/best_weight['Final_Lateness_Dev']:.1f}x)")


def main():
    """Hauptfunktion."""
    print("\n🔍 Lade Experiment-Daten...")
    df = load_all_experiments()
    
    if df.empty:
        print("❌ Keine Experimente gefunden!")
        return
    
    print(f"✅ {len(df)} Experimente geladen.\n")
    
    # Zeige verschiedene Ansichten
    print_performance_ranking_detailed(df)  # Neu: Mit Stabilität (sortiert nach Median)
    print_performance_ranking(df)  # Original (sortiert nach Mean)
    print_experiment_parameters(df)
    print_top_experiments(df, n=10)
    analyze_weight_impact(df)
    
    # Speichere sortierte Ergebnisse
    output_file = Path("data/output/lateness_ranking_overview.csv")
    df_sorted = df.sort_values('Final_Lateness_Dev', ascending=True)
    df_sorted.to_csv(output_file, index=False)
    print(f"\n💾 Ergebnisse gespeichert in: {output_file}")


if __name__ == "__main__":
    main()
