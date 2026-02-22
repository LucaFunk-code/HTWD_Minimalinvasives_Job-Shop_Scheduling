"""
Compare multiple Tabu Solver Lateness experiments to find best parameter settings.
Usage: python3 compare_tabu_lateness.py [exp_id1] [exp_id2] ...
       python3 compare_tabu_lateness.py 16 17 18 19 20 21 22
       python3 compare_tabu_lateness.py --all-lateness
"""

import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

# Get project root (two levels up from this script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def find_all_lateness_experiments(output_dir):
    """Find all experiments with Lateness Deviation data."""
    lateness_exps = []
    for file in sorted(output_dir.glob("tabu_improvements_exp_*.csv")):
        df = pd.read_csv(file)
        if 'Initial_Lateness_Deviation' in df.columns:
            exp_id = df['Experiment_ID'].iloc[0]
            lateness_exps.append(exp_id)
    return lateness_exps


def load_experiment_data(exp_id, output_dir):
    """Load improvement and config data for one experiment."""
    # Load improvements
    imp_file = output_dir / f"tabu_improvements_exp_{exp_id}.csv"
    if not imp_file.exists():
        return None
    
    df = pd.read_csv(imp_file)
    
    # Load config
    config_file = output_dir / f"tabu_config_exp_{exp_id}.csv"
    config = None
    if config_file.exists():
        config = pd.read_csv(config_file).iloc[0]
    
    # Calculate summary metrics
    summary = {
        'Experiment_ID': exp_id,
        'Avg_Improvement_%': df['Improvement_Percent'].mean(),
        'Median_Improvement_%': df['Improvement_Percent'].median(),
        'Std_Improvement_%': df['Improvement_Percent'].std(),
        'Total_Solve_Time_s': df['Solve_Time_Seconds'].sum(),
        'Avg_Solve_Time_s': df['Solve_Time_Seconds'].mean(),
        'Total_Shifts': len(df),
        'Avg_Initial_Lateness': df['Initial_Lateness_Deviation'].mean(),
        'Avg_Final_Lateness': df['Final_Lateness_Deviation'].mean(),
        'Total_Reduction': df['Improvement'].sum(),
    }
    
    if 'Memory_MB' in df.columns:
        summary['Peak_Memory_MB'] = df['Memory_MB'].max()
    
    if config is not None:
        summary.update({
            'tabu_allowed': int(config['tabu_allowed']),
            'max_iters': int(config['max_iters']),
            'patience': int(config['patience']),
            'top_k': int(config['top_k']),
            'w_t': float(config['w_t']),
            'w_e': float(config['w_e']),
            'w_dev': float(config['w_dev']),
        })
    
    return summary


def compare_experiments(exp_ids):
    """Compare multiple Lateness experiments and create visualizations."""
    
    output_dir = PROJECT_ROOT / "data" / "output"
    
    # Load all experiment data
    print(f"Loading {len(exp_ids)} experiments...")
    summaries = []
    for exp_id in exp_ids:
        summary = load_experiment_data(exp_id, output_dir)
        if summary:
            summaries.append(summary)
            print(f"  ✓ Experiment {exp_id}: {summary['Avg_Improvement_%']:.2f}% improvement")
        else:
            print(f"  ✗ Experiment {exp_id}: Not found")
    
    if not summaries:
        print("No valid experiments found!")
        return
    
    df_summary = pd.DataFrame(summaries)
    
    # Create comprehensive comparison plots
    fig = plt.figure(figsize=(18, 12))
    fig.suptitle('Tabu Solver - Lateness Deviation Parameter Comparison', 
                 fontsize=16, fontweight='bold')
    
    # 1. Overall Performance Comparison
    ax1 = plt.subplot(3, 3, 1)
    x = np.arange(len(df_summary))
    ax1.bar(x, df_summary['Avg_Improvement_%'], alpha=0.7, color='#2ca02c')
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_summary['Experiment_ID'], rotation=45)
    ax1.set_xlabel('Experiment ID')
    ax1.set_ylabel('Average Improvement (%)')
    ax1.set_title('Average Improvement by Experiment')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Highlight best
    best_idx = df_summary['Avg_Improvement_%'].idxmax()
    ax1.bar(best_idx, df_summary.loc[best_idx, 'Avg_Improvement_%'], 
            color='gold', alpha=0.9, label='Best')
    ax1.legend()
    
    # 2. Solve Time Comparison
    ax2 = plt.subplot(3, 3, 2)
    ax2.bar(x, df_summary['Avg_Solve_Time_s'], alpha=0.7, color='#8c564b')
    ax2.set_xticks(x)
    ax2.set_xticklabels(df_summary['Experiment_ID'], rotation=45)
    ax2.set_xlabel('Experiment ID')
    ax2.set_ylabel('Avg Solve Time (s)')
    ax2.set_title('Average Solve Time per Shift')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Improvement vs Time Efficiency
    ax3 = plt.subplot(3, 3, 3)
    scatter = ax3.scatter(df_summary['Avg_Solve_Time_s'], 
                         df_summary['Avg_Improvement_%'],
                         s=200, alpha=0.6, c=df_summary.index, cmap='viridis')
    for idx, row in df_summary.iterrows():
        ax3.annotate(f"Exp {int(row['Experiment_ID'])}", 
                    (row['Avg_Solve_Time_s'], row['Avg_Improvement_%']),
                    fontsize=8, ha='center')
    ax3.set_xlabel('Avg Solve Time (s)')
    ax3.set_ylabel('Avg Improvement (%)')
    ax3.set_title('Improvement vs Time Efficiency')
    ax3.grid(True, alpha=0.3)
    
    # 4. Parameter: tabu_allowed
    if 'tabu_allowed' in df_summary.columns:
        ax4 = plt.subplot(3, 3, 4)
        for ta in df_summary['tabu_allowed'].unique():
            mask = df_summary['tabu_allowed'] == ta
            ax4.scatter(df_summary[mask]['Experiment_ID'], 
                       df_summary[mask]['Avg_Improvement_%'],
                       label=f'tabu_allowed={ta}', s=100, alpha=0.7)
        ax4.set_xlabel('Experiment ID')
        ax4.set_ylabel('Avg Improvement (%)')
        ax4.set_title('Effect of tabu_allowed Parameter')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
    
    # 5. Parameter: max_iters
    if 'max_iters' in df_summary.columns:
        ax5 = plt.subplot(3, 3, 5)
        for mi in df_summary['max_iters'].unique():
            mask = df_summary['max_iters'] == mi
            ax5.scatter(df_summary[mask]['Experiment_ID'], 
                       df_summary[mask]['Avg_Improvement_%'],
                       label=f'max_iters={mi}', s=100, alpha=0.7)
        ax5.set_xlabel('Experiment ID')
        ax5.set_ylabel('Avg Improvement (%)')
        ax5.set_title('Effect of max_iters Parameter')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
    
    # 6. Parameter: patience
    if 'patience' in df_summary.columns:
        ax6 = plt.subplot(3, 3, 6)
        for p in df_summary['patience'].unique():
            mask = df_summary['patience'] == p
            ax6.scatter(df_summary[mask]['Experiment_ID'], 
                       df_summary[mask]['Avg_Improvement_%'],
                       label=f'patience={p}', s=100, alpha=0.7)
        ax6.set_xlabel('Experiment ID')
        ax6.set_ylabel('Avg Improvement (%)')
        ax6.set_title('Effect of patience Parameter')
        ax6.legend()
        ax6.grid(True, alpha=0.3)
    
    # 7. Weights Comparison
    if 'w_t' in df_summary.columns:
        ax7 = plt.subplot(3, 3, 7)
        width = 0.25
        x_pos = np.arange(len(df_summary))
        ax7.bar(x_pos - width, df_summary['w_t'], width, label='w_t (Tardiness)', alpha=0.7)
        ax7.bar(x_pos, df_summary['w_e'], width, label='w_e (Earliness)', alpha=0.7)
        ax7.bar(x_pos + width, df_summary['w_dev'], width, label='w_dev (Deviation)', alpha=0.7)
        ax7.set_xticks(x_pos)
        ax7.set_xticklabels(df_summary['Experiment_ID'], rotation=45)
        ax7.set_xlabel('Experiment ID')
        ax7.set_ylabel('Weight Value')
        ax7.set_title('Weight Configuration Comparison')
        ax7.legend()
        ax7.grid(True, alpha=0.3, axis='y')
    
    # 8. Ranking Table
    ax8 = plt.subplot(3, 3, 8)
    ax8.axis('off')
    
    # Sort by improvement
    df_ranked = df_summary.sort_values('Avg_Improvement_%', ascending=False)
    
    ranking_text = "TOP PERFORMING EXPERIMENTS\n" + "="*40 + "\n\n"
    for rank, (idx, row) in enumerate(df_ranked.head(5).iterrows(), 1):
        ranking_text += f"{rank}. Exp {int(row['Experiment_ID'])}: {row['Avg_Improvement_%']:.2f}%\n"
        if 'tabu_allowed' in row:
            ranking_text += f"   tabu={int(row['tabu_allowed'])}, iters={int(row['max_iters'])}, "
            ranking_text += f"patience={int(row['patience'])}\n"
        if 'w_t' in row:
            ranking_text += f"   w_t={row['w_t']:.2f}, w_e={row['w_e']:.2f}, w_dev={row['w_dev']:.2f}\n"
        ranking_text += f"   Time: {row['Avg_Solve_Time_s']:.2f}s/shift\n\n"
    
    ax8.text(0.05, 0.95, ranking_text, transform=ax8.transAxes, 
             fontsize=9, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    # 9. Statistics Summary
    ax9 = plt.subplot(3, 3, 9)
    ax9.axis('off')
    
    stats_text = f"""
    COMPARISON SUMMARY
    {'='*30}
    Total Experiments: {len(df_summary)}
    
    Best Improvement:
      Exp {int(df_summary.loc[best_idx, 'Experiment_ID'])}: {df_summary.loc[best_idx, 'Avg_Improvement_%']:.2f}%
    
    Fastest:
      Exp {int(df_summary.loc[df_summary['Avg_Solve_Time_s'].idxmin(), 'Experiment_ID'])}: {df_summary['Avg_Solve_Time_s'].min():.2f}s
    
    Average Across All:
      Improvement: {df_summary['Avg_Improvement_%'].mean():.2f}%
      Solve Time: {df_summary['Avg_Solve_Time_s'].mean():.2f}s
      Std Dev: {df_summary['Std_Improvement_%'].mean():.2f}%
    """
    
    if 'Peak_Memory_MB' in df_summary.columns:
        stats_text += f"\n    Peak Memory:\n      {df_summary['Peak_Memory_MB'].max():.2f}MB"
    
    ax9.text(0.1, 0.9, stats_text, transform=ax9.transAxes, 
             fontsize=10, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    
    # Save comparison plot
    plot_file = output_dir / f"tabu_lateness_comparison.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Comparison plot saved to: {plot_file}")
    
    # Save summary CSV
    csv_file = output_dir / "tabu_lateness_comparison_summary.csv"
    df_summary.to_csv(csv_file, index=False)
    print(f"✓ Summary data saved to: {csv_file}")
    
    # Show plot
    plt.show()
    
    # Print recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    best_exp = df_summary.loc[best_idx]
    print(f"\n🏆 Best Overall Performance: Experiment {int(best_exp['Experiment_ID'])}")
    print(f"   Average Improvement: {best_exp['Avg_Improvement_%']:.2f}%")
    if 'tabu_allowed' in best_exp:
        print(f"   Parameters: tabu_allowed={int(best_exp['tabu_allowed'])}, "
              f"max_iters={int(best_exp['max_iters'])}, "
              f"patience={int(best_exp['patience'])}, "
              f"top_k={int(best_exp['top_k'])}")
    if 'w_t' in best_exp:
        print(f"   Weights: w_t={best_exp['w_t']:.2f}, w_e={best_exp['w_e']:.2f}, w_dev={best_exp['w_dev']:.2f}")
    print(f"   Average Time: {best_exp['Avg_Solve_Time_s']:.2f}s per shift")


if __name__ == "__main__":
    output_dir = PROJECT_ROOT / "data" / "output"
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all-lateness":
            # Find all lateness experiments automatically
            exp_ids = find_all_lateness_experiments(output_dir)
            if not exp_ids:
                print("No Lateness experiments found!")
                sys.exit(1)
            print(f"Found {len(exp_ids)} Lateness experiments: {exp_ids}")
        else:
            # Use provided experiment IDs
            try:
                exp_ids = [int(x) for x in sys.argv[1:]]
            except ValueError:
                print("Error: Please provide valid experiment IDs")
                print("Usage: python3 compare_tabu_lateness.py 16 17 18 19 20 21 22")
                print("   or: python3 compare_tabu_lateness.py --all-lateness")
                sys.exit(1)
    else:
        # Default: find all lateness experiments
        exp_ids = find_all_lateness_experiments(output_dir)
        if not exp_ids:
            print("No Lateness experiments found!")
            print("Usage: python3 compare_tabu_lateness.py 16 17 18 19 20 21 22")
            sys.exit(1)
        print(f"Auto-detected {len(exp_ids)} Lateness experiments: {exp_ids}")
    
    compare_experiments(exp_ids)
