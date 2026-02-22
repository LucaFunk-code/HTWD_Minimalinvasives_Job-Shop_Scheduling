"""
Berechne die Termintreue basierend auf der Definition:
- Termintreue = Zeitliche Abweichung vom Liefertermin
- Lateness Deviation = Tardiness + Earliness (aus Tabu-Solver Zielfunktion)

HINWEIS: Die genaue Aufteilung zwischen Tardiness und Earliness ist in den CSV-Dateien
nicht gespeichert. Die Lateness Deviation ist die Summe beider Komponenten.
"""
import pandas as pd
from pathlib import Path


def analyze_termintreue_from_csv():
    """
    Analysiere Termintreue basierend auf den vorhandenen CSV-Daten.
    Die Lateness Deviation entspricht: Tardiness + Earliness
    """
    output_dir = Path("data/output")
    
    # Finde alle Lateness-Experimente
    exp_files = sorted(output_dir.glob("tabu_improvements_exp_*.csv"))
    
    all_data = []
    
    for file in exp_files:
        df = pd.read_csv(file)
        if 'Final_Lateness_Deviation' not in df.columns:
            continue
        
        exp_id = df['Experiment_ID'].iloc[0]
        
        # Lade Config für Gewichte
        config_file = output_dir / f"tabu_config_exp_{exp_id}.csv"
        config = None
        w_t, w_e, w_dev = 1, 1, 1
        
        if config_file.exists():
            config = pd.read_csv(config_file).iloc[0]
            w_t = float(config['w_t']) if 'w_t' in config else 1
            w_e = float(config['w_e']) if 'w_e' in config else 1
            w_dev = float(config['w_dev']) if 'w_dev' in config else 1
        
        # Aggregiere pro Experiment
        for _, row in df.iterrows():
            shift = row['Shift']
            initial_ld = row['Initial_Lateness_Deviation']
            final_ld = row['Final_Lateness_Deviation']
            
            all_data.append({
                'Experiment_ID': int(exp_id),
                'Shift': shift,
                'Initial_Lateness_Dev_min': initial_ld,
                'Final_Lateness_Dev_min': final_ld,
                'Initial_Lateness_Dev_hours': initial_ld / 60,
                'Final_Lateness_Dev_hours': final_ld / 60,
                'Improvement_min': initial_ld - final_ld,
                'Improvement_pct': ((initial_ld - final_ld) / initial_ld * 100) if initial_ld > 0 else 0,
                'w_t': w_t,
                'w_e': w_e,
                'w_dev': w_dev
            })
    
    df_all = pd.DataFrame(all_data)
    
    # Speichere detaillierte Daten
    detail_file = output_dir / "termintreue_detailed.csv"
    df_all.to_csv(detail_file, index=False)
    print(f"💾 Detaillierte Termintreue gespeichert: {detail_file}")
    print(f"   {len(df_all)} Shifts von {df_all['Experiment_ID'].nunique()} Experimenten\n")
    
    # Erstelle Zusammenfassung pro Experiment
    summary = df_all.groupby('Experiment_ID').agg({
        'Initial_Lateness_Dev_min': 'mean',
        'Final_Lateness_Dev_min': 'mean',
        'Final_Lateness_Dev_hours': 'mean',
        'Improvement_min': 'mean',
        'Improvement_pct': 'mean',
        'w_t': 'first',
        'w_e': 'first',
        'w_dev': 'first',
        'Shift': 'count'
    }).round(2)
    
    summary.rename(columns={'Shift': 'Num_Shifts'}, inplace=True)
    
    # Sortiere nach bester Termintreue (niedrigste Final Lateness Deviation)
    summary_sorted = summary.sort_values('Final_Lateness_Dev_min', ascending=True)
    
    # Speichere Zusammenfassung
    summary_file = output_dir / "termintreue_summary.csv"
    summary_sorted.to_csv(summary_file)
    print(f"💾 Zusammenfassung gespeichert: {summary_file}\n")
    
    # Zeige Top 10
    print("=" * 140)
    print("TOP 10 EXPERIMENTE nach Final Lateness Deviation (beste Termintreue)")
    print("=" * 140)
    print(f"{'Rank':<6} | {'Exp ID':<7} | {'Final LD (min)':<15} | {'Final LD (h)':<15} | {'Improve %':<12} | {'w_t':<5} | {'w_e':<5} | {'w_dev':<6} | {'Shifts':<7}")
    print("-" * 140)
    
    for i, (exp_id, row) in enumerate(summary_sorted.head(10).iterrows(), 1):
        print(f"{i:<6} | {exp_id:<7} | {row['Final_Lateness_Dev_min']:<15.1f} | {row['Final_Lateness_Dev_hours']:<15.1f} | {row['Improvement_pct']:<12.2f} | {row['w_t']:<5.1f} | {row['w_e']:<5.1f} | {row['w_dev']:<6.1f} | {int(row['Num_Shifts']):<7}")
    
    print("=" * 140)
    
    # Gruppiere nach Gewichtskombination
    print("\n" + "=" * 100)
    print("TERMINTREUE nach GEWICHTSKOMBINATION")
    print("=" * 100)
    
    weight_summary = df_all.groupby(['w_t', 'w_e', 'w_dev']).agg({
        'Final_Lateness_Dev_min': ['mean', 'std', 'min', 'max', 'count']
    }).round(1)
    
    print(weight_summary)
    
    print("\n✅ Analyse abgeschlossen!")
    print("\nWICHTIG:")
    print("  • Lateness Deviation = Tardiness + Earliness")
    print("  • Niedrigere Werte = bessere Termintreue")
    print("  • Einheit: Minuten (÷ 60 = Stunden)")


if __name__ == "__main__":
    analyze_termintreue_from_csv()
