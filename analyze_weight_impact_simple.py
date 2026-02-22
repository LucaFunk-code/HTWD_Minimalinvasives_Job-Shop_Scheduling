"""
Simple analysis of weight impact on Lateness Deviation
Compares experiments 23-27 with different weight configurations
"""
import pandas as pd
from pathlib import Path

def analyze_weight_impact():
    """Analyze how weights affect improvement results"""
    
    output_dir = Path("data/output")
    results = []
    
    # Load data for each experiment
    for exp_id in [23, 24, 25, 26, 27]:
        # Load config
        config_file = output_dir / f"tabu_config_exp_{exp_id}.csv"
        config = pd.read_csv(config_file).iloc[0]
        
        # Load improvements
        imp_file = output_dir / f"tabu_improvements_exp_{exp_id}.csv"
        improvements = pd.read_csv(imp_file)
        
        # Calculate statistics
        avg_improvement = improvements['Improvement_Percent'].mean()
        median_improvement = improvements['Improvement_Percent'].median()
        std_improvement = improvements['Improvement_Percent'].std()
        best_improvement = improvements['Improvement_Percent'].max()
        worst_improvement = improvements['Improvement_Percent'].min()
        avg_time = improvements['Solve_Time_Seconds'].mean()
        
        avg_initial = improvements['Initial_Lateness_Deviation'].mean()
        avg_final = improvements['Final_Lateness_Deviation'].mean()
        total_improvement = improvements['Improvement'].sum()
        
        results.append({
            'Experiment_ID': exp_id,
            'w_tardiness': config['w_t'],
            'w_earliness': config['w_e'],
            'w_deviation': config['w_dev'],
            'avg_improvement_pct': avg_improvement,
            'median_improvement_pct': median_improvement,
            'std_improvement_pct': std_improvement,
            'best_improvement_pct': best_improvement,
            'worst_improvement_pct': worst_improvement,
            'avg_solve_time_sec': avg_time,
            'avg_initial_lateness_dev': avg_initial,
            'avg_final_lateness_dev': avg_final,
            'total_improvement': total_improvement
        })
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Print results
    print("=" * 100)
    print("WEIGHT IMPACT ANALYSIS - Experiments 23-27")
    print("=" * 100)
    print()
    
    print("WEIGHT CONFIGURATIONS:")
    print("-" * 100)
    print(df[['Experiment_ID', 'w_tardiness', 'w_earliness', 'w_deviation']].to_string(index=False))
    print()
    
    print("IMPROVEMENT RESULTS:")
    print("-" * 100)
    print(df[['Experiment_ID', 'avg_improvement_pct', 'median_improvement_pct', 
              'best_improvement_pct', 'worst_improvement_pct']].to_string(index=False))
    print()
    
    print("PERFORMANCE METRICS:")
    print("-" * 100)
    print(df[['Experiment_ID', 'avg_solve_time_sec', 'avg_initial_lateness_dev', 
              'avg_final_lateness_dev', 'total_improvement']].to_string(index=False))
    print()
    
    print("=" * 100)
    print("INSIGHTS:")
    print("=" * 100)
    
    # Find best performer
    best_idx = df['avg_improvement_pct'].idxmax()
    best_exp = df.loc[best_idx]
    
    print(f"\n✓ Best Average Improvement: Experiment {best_exp['Experiment_ID']}")
    print(f"  - Weights: w_t={best_exp['w_tardiness']}, w_e={best_exp['w_earliness']}, w_dev={best_exp['w_deviation']}")
    print(f"  - Average Improvement: {best_exp['avg_improvement_pct']:.2f}%")
    print(f"  - Median Improvement: {best_exp['median_improvement_pct']:.2f}%")
    
    # Find fastest
    fastest_idx = df['avg_solve_time_sec'].idxmin()
    fastest_exp = df.loc[fastest_idx]
    
    print(f"\n✓ Fastest Average Solve Time: Experiment {fastest_exp['Experiment_ID']}")
    print(f"  - Weights: w_t={fastest_exp['w_tardiness']}, w_e={fastest_exp['w_earliness']}, w_dev={fastest_exp['w_deviation']}")
    print(f"  - Average Time: {fastest_exp['avg_solve_time_sec']:.2f}s ({fastest_exp['avg_solve_time_sec']/60:.2f} min)")
    
    # Most consistent
    most_consistent_idx = df['std_improvement_pct'].idxmin()
    consistent_exp = df.loc[most_consistent_idx]
    
    print(f"\n✓ Most Consistent Results: Experiment {consistent_exp['Experiment_ID']}")
    print(f"  - Weights: w_t={consistent_exp['w_tardiness']}, w_e={consistent_exp['w_earliness']}, w_dev={consistent_exp['w_deviation']}")
    print(f"  - Std Deviation: {consistent_exp['std_improvement_pct']:.2f}%")
    
    # Correlation analysis
    print("\n" + "=" * 100)
    print("CORRELATION ANALYSIS:")
    print("=" * 100)
    
    corr_improvement = df[['w_tardiness', 'w_earliness', 'w_deviation', 'avg_improvement_pct']].corr()['avg_improvement_pct']
    print("\nCorrelation with Average Improvement %:")
    print(f"  w_tardiness:  {corr_improvement['w_tardiness']:+.4f}")
    print(f"  w_earliness:  {corr_improvement['w_earliness']:+.4f}")
    print(f"  w_deviation:  {corr_improvement['w_deviation']:+.4f}")
    
    corr_time = df[['w_tardiness', 'w_earliness', 'w_deviation', 'avg_solve_time_sec']].corr()['avg_solve_time_sec']
    print("\nCorrelation with Average Solve Time:")
    print(f"  w_tardiness:  {corr_time['w_tardiness']:+.4f}")
    print(f"  w_earliness:  {corr_time['w_earliness']:+.4f}")
    print(f"  w_deviation:  {corr_time['w_deviation']:+.4f}")
    
    print("\n" + "=" * 100)
    
    # Save to CSV
    output_file = output_dir / "weight_impact_analysis_exp_23-27.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
    print("=" * 100)

if __name__ == "__main__":
    analyze_weight_impact()
