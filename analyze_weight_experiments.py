"""
Comprehensive analysis of weight experiments based on CSV output files.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

def load_experiment_data(exp_ids):
    """Load experiment data from CSV files."""
    data = []
    
    for exp_id in exp_ids:
        config_file = Path(f"data/output/tabu_config_exp_{exp_id}.csv")
        improvements_file = Path(f"data/output/tabu_improvements_exp_{exp_id}.csv")
        
        if not config_file.exists() or not improvements_file.exists():
            print(f"Warning: Files for experiment {exp_id} not found")
            continue
        
        # Load config
        config = pd.read_csv(config_file)
        
        # Load improvements
        improvements = pd.read_csv(improvements_file)
        
        # Calculate aggregated metrics
        avg_improvement = improvements['Improvement_Percent'].mean()
        total_solve_time = improvements['Solve_Time_Seconds'].sum()
        num_shifts = len(improvements)
        
        # Extract weights from config
        w_t = config['w_t'].iloc[0]
        w_e = config['w_e'].iloc[0]
        w_dev = config['w_dev'].iloc[0]
        
        # Get other parameters
        tabu_allowed = config['tabu_allowed'].iloc[0]
        max_iters = config['max_iters'].iloc[0]
        patience = config['patience'].iloc[0]
        
        data.append({
            'experiment_id': exp_id,
            'w_t': w_t,
            'w_e': w_e,
            'w_dev': w_dev,
            'avg_improvement_percent': avg_improvement,
            'total_solve_time_min': total_solve_time / 60,
            'num_shifts': num_shifts,
            'tabu_allowed': tabu_allowed,
            'max_iters': max_iters,
            'patience': patience,
        })
    
    return pd.DataFrame(data)


def print_analysis(df, title="EXPERIMENT ANALYSIS"):
    """Print detailed analysis of experiments."""
    print("\n" + "=" * 120)
    print(title)
    print("=" * 120)
    
    # Sort by experiment ID
    df_sorted = df.sort_values('experiment_id')
    
    # Display table
    print(f"\n{'ID':<8} {'w_t':<8} {'w_e':<8} {'w_dev':<8} {'Improvement %':<15} {'Solve Time (min)':<20} {'Shifts':<10}")
    print("-" * 120)
    
    for _, row in df_sorted.iterrows():
        print(f"{row['experiment_id']:<8} {row['w_t']:<8.2f} {row['w_e']:<8.2f} {row['w_dev']:<8.2f} "
              f"{row['avg_improvement_percent']:<15.2f} {row['total_solve_time_min']:<20.2f} {row['num_shifts']:<10.0f}")
    
    print("=" * 120)


def analyze_weight_impact(df):
    """Analyze impact of weights on performance."""
    print("\n" + "=" * 120)
    print("WEIGHT IMPACT ANALYSIS")
    print("=" * 120)
    
    # Group by weight configurations
    print("\n1. TARDINESS WEIGHT (w_t) IMPACT:")
    print("-" * 80)
    
    # Sort by w_t
    df_by_wt = df.sort_values('w_t')
    print(f"{'w_t':<10} {'w_e':<10} {'w_dev':<10} {'Avg Improvement %':<20}")
    for _, row in df_by_wt.iterrows():
        print(f"{row['w_t']:<10.2f} {row['w_e']:<10.2f} {row['w_dev']:<10.2f} {row['avg_improvement_percent']:<20.2f}")
    
    # Correlation analysis
    print("\n2. CORRELATIONS:")
    print("-" * 80)
    corr_improvement_wt = df[['w_t', 'avg_improvement_percent']].corr().iloc[0, 1]
    corr_improvement_we = df[['w_e', 'avg_improvement_percent']].corr().iloc[0, 1]
    corr_improvement_wdev = df[['w_dev', 'avg_improvement_percent']].corr().iloc[0, 1]
    
    print(f"w_t vs. Improvement:     {corr_improvement_wt:>8.3f}")
    print(f"w_e vs. Improvement:     {corr_improvement_we:>8.3f}")
    print(f"w_dev vs. Improvement:   {corr_improvement_wdev:>8.3f}")
    
    # Best configurations
    print("\n3. TOP 3 CONFIGURATIONS BY IMPROVEMENT:")
    print("-" * 80)
    top_3 = df.nlargest(3, 'avg_improvement_percent')
    for i, (_, row) in enumerate(top_3.iterrows(), 1):
        print(f"{i}. Exp {row['experiment_id']}: w_t={row['w_t']:.2f}, w_e={row['w_e']:.2f}, w_dev={row['w_dev']:.2f} "
              f"→ {row['avg_improvement_percent']:.2f}%")
    
    print("=" * 120)


def analyze_stability(df_base, df_duplicates):
    """Analyze stability by comparing base experiments with duplicates."""
    print("\n" + "=" * 120)
    print("STABILITY ANALYSIS - Comparing Base Experiments with Duplicates")
    print("=" * 120)
    
    # Match configurations
    stability_results = []
    
    for _, base_row in df_base.iterrows():
        w_t = base_row['w_t']
        w_dev = base_row['w_dev']
        
        # Find duplicates with same configuration
        duplicates = df_duplicates[
            (np.isclose(df_duplicates['w_t'], w_t, atol=0.01)) &
            (np.isclose(df_duplicates['w_dev'], w_dev, atol=0.01))
        ]
        
        if len(duplicates) > 0:
            all_improvements = [base_row['avg_improvement_percent']] + duplicates['avg_improvement_percent'].tolist()
            
            stability_results.append({
                'config': f"w_t={w_t:.2f}, w_dev={w_dev:.2f}",
                'base_id': base_row['experiment_id'],
                'duplicate_ids': duplicates['experiment_id'].tolist(),
                'mean_improvement': np.mean(all_improvements),
                'std_improvement': np.std(all_improvements),
                'min_improvement': np.min(all_improvements),
                'max_improvement': np.max(all_improvements),
                'num_runs': len(all_improvements),
            })
    
    if stability_results:
        print(f"\n{'Configuration':<30} {'Base':<8} {'Duplic.':<15} {'Mean%':<10} {'Std%':<10} {'Min%':<10} {'Max%':<10}")
        print("-" * 120)
        
        for result in stability_results:
            dup_str = str(result['duplicate_ids'])[:12]
            print(f"{result['config']:<30} {result['base_id']:<8} {dup_str:<15} "
                  f"{result['mean_improvement']:<10.2f} {result['std_improvement']:<10.2f} "
                  f"{result['min_improvement']:<10.2f} {result['max_improvement']:<10.2f}")
        
        # Overall stability assessment
        overall_std = np.mean([r['std_improvement'] for r in stability_results])
        print(f"\nOverall Stability (Avg Std Dev): {overall_std:.2f}%")
        
        if overall_std < 2.0:
            print("✓ EXCELLENT stability - Results are highly reproducible")
        elif overall_std < 5.0:
            print("✓ GOOD stability - Results are reasonably reproducible")
        else:
            print("⚠ MODERATE stability - Some variation in results")
    else:
        print("\nNo matching duplicates found for comparison.")
    
    print("=" * 120)


def create_visualizations(df_base, df_all, output_dir="data/output"):
    """Create visualization plots."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Plot 1: Weight vs. Improvement
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # w_t vs improvement
    axes[0].scatter(df_all['w_t'], df_all['avg_improvement_percent'], s=100, alpha=0.6)
    axes[0].set_xlabel('w_t (Tardiness Weight)', fontsize=12)
    axes[0].set_ylabel('Average Improvement %', fontsize=12)
    axes[0].set_title('Impact of Tardiness Weight on Performance', fontsize=14)
    axes[0].grid(True, alpha=0.3)
    
    # w_dev vs improvement
    axes[1].scatter(df_all['w_dev'], df_all['avg_improvement_percent'], s=100, alpha=0.6, color='orange')
    axes[1].set_xlabel('w_dev (Deviation Weight)', fontsize=12)
    axes[1].set_ylabel('Average Improvement %', fontsize=12)
    axes[1].set_title('Impact of Deviation Weight on Performance', fontsize=14)
    axes[1].grid(True, alpha=0.3)
    
    # Comparison of all experiments
    axes[2].bar(range(len(df_base)), df_base['avg_improvement_percent'], alpha=0.7)
    axes[2].set_xlabel('Experiment Configuration', fontsize=12)
    axes[2].set_ylabel('Average Improvement %', fontsize=12)
    axes[2].set_title('Performance Comparison (Base Experiments)', fontsize=14)
    axes[2].set_xticks(range(len(df_base)))
    axes[2].set_xticklabels([f"Exp{id}" for id in df_base['experiment_id']], rotation=45)
    axes[2].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plot_file = output_dir / "weight_impact_visualization.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"\n📊 Visualization saved: {plot_file}")
    plt.close()
    
    # Plot 2: Heatmap of weight combinations
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create pivot table
    pivot_data = df_all.pivot_table(
        values='avg_improvement_percent',
        index='w_dev',
        columns='w_t',
        aggfunc='mean'
    )
    
    sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Improvement %'})
    ax.set_title('Performance Heatmap: w_t vs w_dev', fontsize=14)
    ax.set_xlabel('w_t (Tardiness Weight)', fontsize=12)
    ax.set_ylabel('w_dev (Deviation Weight)', fontsize=12)
    
    plt.tight_layout()
    heatmap_file = output_dir / "weight_heatmap.png"
    plt.savefig(heatmap_file, dpi=300, bbox_inches='tight')
    print(f"📊 Heatmap saved: {heatmap_file}")
    plt.close()


def research_recommendations(df):
    """Provide recommendations for future experiments."""
    print("\n" + "=" * 120)
    print("RESEARCH RECOMMENDATIONS - Gaps & Next Steps")
    print("=" * 120)
    
    # Find tested weight combinations
    tested_wt = sorted(df['w_t'].unique())
    tested_wdev = sorted(df['w_dev'].unique())
    
    print("\n1. TESTED WEIGHT COMBINATIONS:")
    print(f"   w_t values: {[f'{v:.1f}' for v in tested_wt]}")
    print(f"   w_dev values: {[f'{v:.1f}' for v in tested_wdev]}")
    
    # Suggest gaps
    print("\n2. SUGGESTED ADDITIONAL EXPERIMENTS (to fill gaps):")
    print("-" * 80)
    
    suggestions = [
        {"w_t": 0.4, "w_dev": 0.5, "reason": "Between Balanced and Earliness-focus"},
        {"w_t": 0.6, "w_dev": 0.5, "reason": "Between Balanced and Tardiness-focus"},
        {"w_t": 0.4, "w_dev": 0.8, "reason": "Mid-range tardiness with high deviation penalty"},
        {"w_t": 0.7, "w_dev": 0.6, "reason": "High tardiness with moderate deviation"},
        {"w_t": 0.1, "w_dev": 0.5, "reason": "Extreme earliness preference"},
    ]
    
    for i, sug in enumerate(suggestions, 1):
        print(f"   {i}. w_t={sug['w_t']:.1f}, w_dev={sug['w_dev']:.1f} - {sug['reason']}")
    
    # Best performing range
    best_config = df.loc[df['avg_improvement_percent'].idxmax()]
    print(f"\n3. BEST PERFORMING CONFIGURATION SO FAR:")
    print(f"   Exp {int(best_config['experiment_id'])}: w_t={best_config['w_t']:.2f}, w_dev={best_config['w_dev']:.2f}")
    print(f"   → Improvement: {best_config['avg_improvement_percent']:.2f}%")
    print(f"   → Consider testing variations around these values")
    
    print("\n4. PARAMETER VARIATIONS TO TEST:")
    print("   - Different tabu_allowed values (currently all 25)")
    print("   - Different max_iters values (currently all 300)")
    print("   - Different patience values (currently all 20)")
    print("   - Different utilization levels (currently all 0.75)")
    
    print("=" * 120)


def main():
    """Main analysis function."""
    print("\n" + "=" * 120)
    print("TABU SEARCH WEIGHT EXPERIMENTS - COMPREHENSIVE ANALYSIS")
    print("=" * 120)
    
    # 1. Load base experiments (23-27)
    print("\n📂 Loading Base Experiments (23-27)...")
    df_base = load_experiment_data([23, 24, 25, 26, 27])
    
    if df_base.empty:
        print("❌ No base experiment data found!")
        return
    
    print(f"✓ Loaded {len(df_base)} base experiments")
    
    # 2. Load duplicate experiments (38-47)
    print("\n📂 Loading Duplicate Experiments (38-47)...")
    df_duplicates = load_experiment_data(list(range(38, 48)))
    print(f"✓ Loaded {len(df_duplicates)} duplicate experiments")
    
    # Combine all
    df_all = pd.concat([df_base, df_duplicates], ignore_index=True)
    
    # Step 1: Analyze base experiments
    print_analysis(df_base, "STEP 1: BASE EXPERIMENTS (23-27)")
    
    # Step 2: Analyze weight impact
    analyze_weight_impact(df_base)
    
    # Step 3: Stability analysis
    if not df_duplicates.empty:
        analyze_stability(df_base, df_duplicates)
    
    # Step 4: Visualizations
    print("\n📊 Creating visualizations...")
    create_visualizations(df_base, df_all)
    
    # Step 5: Research recommendations
    research_recommendations(df_all)
    
    # Save summary
    summary_file = Path("data/output/weight_analysis_summary.csv")
    df_all.to_csv(summary_file, index=False)
    print(f"\n💾 Summary saved: {summary_file}")
    
    print("\n" + "=" * 120)
    print("ANALYSIS COMPLETE!")
    print("=" * 120)


if __name__ == "__main__":
    main()
