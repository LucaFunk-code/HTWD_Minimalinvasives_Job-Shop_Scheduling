"""
Analyze how each Tabu Solver parameter affects performance.
Shows optimal parameter ranges and diminishing returns.

Usage: python3 analyze_tabu_parameters.py [--all-lateness]
"""

import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline


def find_all_lateness_experiments(output_dir):
    """Find all experiments with Lateness Deviation data."""
    lateness_exps = []
    for file in sorted(output_dir.glob("tabu_improvements_exp_*.csv")):
        df = pd.read_csv(file)
        if 'Initial_Lateness_Deviation' in df.columns:
            exp_id = df['Experiment_ID'].iloc[0]
            lateness_exps.append(exp_id)
    return lateness_exps


def load_all_experiment_data(exp_ids, output_dir):
    """Load all experiment data and combine into single DataFrame."""
    all_data = []
    
    for exp_id in exp_ids:
        # Load improvements
        imp_file = output_dir / f"tabu_improvements_exp_{exp_id}.csv"
        if not imp_file.exists():
            continue
        
        df = pd.read_csv(imp_file)
        
        # Load config
        config_file = output_dir / f"tabu_config_exp_{exp_id}.csv"
        if not config_file.exists():
            continue
        
        config = pd.read_csv(config_file).iloc[0]
        
        # Calculate metrics
        data = {
            'Experiment_ID': exp_id,
            'Avg_Improvement_%': df['Improvement_Percent'].mean(),
            'Median_Improvement_%': df['Improvement_Percent'].median(),
            'Std_Improvement_%': df['Improvement_Percent'].std(),
            'Min_Improvement_%': df['Improvement_Percent'].min(),
            'Max_Improvement_%': df['Improvement_Percent'].max(),
            'Avg_Solve_Time_s': df['Solve_Time_Seconds'].mean(),
            'Total_Solve_Time_s': df['Solve_Time_Seconds'].sum(),
            'tabu_allowed': int(config['tabu_allowed']),
            'max_iters': int(config['max_iters']),
            'patience': int(config['patience']),
            'top_k': int(config['top_k']),
            'w_t': float(config['w_t']),
            'w_e': float(config['w_e']),
            'w_dev': float(config['w_dev']),
        }
        
        if 'Memory_MB' in df.columns:
            data['Peak_Memory_MB'] = df['Memory_MB'].max()
        
        all_data.append(data)
    
    return pd.DataFrame(all_data)


def plot_parameter_analysis(df, output_dir):
    """Create 4 parameter analysis plots showing optimal ranges."""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Tabu Solver Parameter Analysis - Optimal Ranges & Diminishing Returns', 
                 fontsize=16, fontweight='bold')
    
    # Color map for better visualization
    color_main = '#2e7d32'
    color_trend = '#ff6b6b'
    
    # 1. MAX_ITERS Analysis
    ax1 = axes[0, 0]
    param = 'max_iters'
    if param in df.columns and len(df[param].unique()) > 1:
        # Group by parameter and calculate mean/std
        grouped = df.groupby(param).agg({
            'Avg_Improvement_%': ['mean', 'std', 'count'],
            'Avg_Solve_Time_s': 'mean'
        }).reset_index()
        
        x = grouped[param].values
        y_mean = grouped[('Avg_Improvement_%', 'mean')].values
        y_std = grouped[('Avg_Improvement_%', 'std')].values
        
        # Main plot with error bars
        ax1.errorbar(x, y_mean, yerr=y_std, fmt='o', markersize=10, 
                    capsize=5, capthick=2, color=color_main, 
                    label='Actual Performance', linewidth=2)
        
        # Smooth trend line if enough points
        if len(x) >= 3:
            x_smooth = np.linspace(x.min(), x.max(), 300)
            spl = make_interp_spline(x, y_mean, k=min(3, len(x)-1))
            y_smooth = spl(x_smooth)
            ax1.plot(x_smooth, y_smooth, '--', color=color_trend, 
                    linewidth=2, alpha=0.7, label='Trend')
        
        # Mark best point
        best_idx = y_mean.argmax()
        ax1.scatter(x[best_idx], y_mean[best_idx], s=300, 
                   color='gold', marker='*', edgecolors='black', 
                   linewidths=2, zorder=5, label=f'Best: {int(x[best_idx])}')
        
        ax1.set_xlabel('Max Iterations', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Avg Improvement (%)', fontsize=12, fontweight='bold')
        ax1.set_title(f'Iterations vs Performance\nOptimal: {int(x[best_idx])} iterations ({y_mean[best_idx]:.2f}%)', 
                     fontsize=11, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best')
        
        # Add annotation
        ax1.text(0.05, 0.95, f'Range tested: {int(x.min())}-{int(x.max())}', 
                transform=ax1.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 2. TABU_ALLOWED Analysis
    ax2 = axes[0, 1]
    param = 'tabu_allowed'
    if param in df.columns and len(df[param].unique()) > 1:
        grouped = df.groupby(param).agg({
            'Avg_Improvement_%': ['mean', 'std', 'count'],
            'Avg_Solve_Time_s': 'mean'
        }).reset_index()
        
        x = grouped[param].values
        y_mean = grouped[('Avg_Improvement_%', 'mean')].values
        y_std = grouped[('Avg_Improvement_%', 'std')].values
        
        ax2.errorbar(x, y_mean, yerr=y_std, fmt='o', markersize=10, 
                    capsize=5, capthick=2, color=color_main, 
                    label='Actual Performance', linewidth=2)
        
        if len(x) >= 3:
            x_smooth = np.linspace(x.min(), x.max(), 300)
            spl = make_interp_spline(x, y_mean, k=min(3, len(x)-1))
            y_smooth = spl(x_smooth)
            ax2.plot(x_smooth, y_smooth, '--', color=color_trend, 
                    linewidth=2, alpha=0.7, label='Trend')
        
        best_idx = y_mean.argmax()
        ax2.scatter(x[best_idx], y_mean[best_idx], s=300, 
                   color='gold', marker='*', edgecolors='black', 
                   linewidths=2, zorder=5, label=f'Best: {int(x[best_idx])}')
        
        ax2.set_xlabel('Tabu List Size', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Avg Improvement (%)', fontsize=12, fontweight='bold')
        ax2.set_title(f'Tabu List Size vs Performance\nOptimal: {int(x[best_idx])} moves ({y_mean[best_idx]:.2f}%)', 
                     fontsize=11, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='best')
        
        ax2.text(0.05, 0.95, f'Range tested: {int(x.min())}-{int(x.max())}', 
                transform=ax2.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 3. PATIENCE Analysis
    ax3 = axes[1, 0]
    param = 'patience'
    if param in df.columns and len(df[param].unique()) > 1:
        grouped = df.groupby(param).agg({
            'Avg_Improvement_%': ['mean', 'std', 'count'],
            'Avg_Solve_Time_s': 'mean'
        }).reset_index()
        
        x = grouped[param].values
        y_mean = grouped[('Avg_Improvement_%', 'mean')].values
        y_std = grouped[('Avg_Improvement_%', 'std')].values
        
        ax3.errorbar(x, y_mean, yerr=y_std, fmt='o', markersize=10, 
                    capsize=5, capthick=2, color=color_main, 
                    label='Actual Performance', linewidth=2)
        
        if len(x) >= 3:
            x_smooth = np.linspace(x.min(), x.max(), 300)
            spl = make_interp_spline(x, y_mean, k=min(3, len(x)-1))
            y_smooth = spl(x_smooth)
            ax3.plot(x_smooth, y_smooth, '--', color=color_trend, 
                    linewidth=2, alpha=0.7, label='Trend')
        
        best_idx = y_mean.argmax()
        ax3.scatter(x[best_idx], y_mean[best_idx], s=300, 
                   color='gold', marker='*', edgecolors='black', 
                   linewidths=2, zorder=5, label=f'Best: {int(x[best_idx])}')
        
        ax3.set_xlabel('Patience (Early Stop)', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Avg Improvement (%)', fontsize=12, fontweight='bold')
        ax3.set_title(f'Patience vs Performance\nOptimal: {int(x[best_idx])} iterations ({y_mean[best_idx]:.2f}%)', 
                     fontsize=11, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc='best')
        
        ax3.text(0.05, 0.95, f'Range tested: {int(x.min())}-{int(x.max())}', 
                transform=ax3.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 4. TOP_K Analysis (or combined efficiency)
    ax4 = axes[1, 1]
    param = 'top_k'
    if param in df.columns and len(df[param].unique()) > 1:
        grouped = df.groupby(param).agg({
            'Avg_Improvement_%': ['mean', 'std', 'count'],
            'Avg_Solve_Time_s': 'mean'
        }).reset_index()
        
        x = grouped[param].values
        y_mean = grouped[('Avg_Improvement_%', 'mean')].values
        y_std = grouped[('Avg_Improvement_%', 'std')].values
        
        ax4.errorbar(x, y_mean, yerr=y_std, fmt='o', markersize=10, 
                    capsize=5, capthick=2, color=color_main, 
                    label='Actual Performance', linewidth=2)
        
        if len(x) >= 3:
            x_smooth = np.linspace(x.min(), x.max(), 300)
            spl = make_interp_spline(x, y_mean, k=min(3, len(x)-1))
            y_smooth = spl(x_smooth)
            ax4.plot(x_smooth, y_smooth, '--', color=color_trend, 
                    linewidth=2, alpha=0.7, label='Trend')
        
        best_idx = y_mean.argmax()
        ax4.scatter(x[best_idx], y_mean[best_idx], s=300, 
                   color='gold', marker='*', edgecolors='black', 
                   linewidths=2, zorder=5, label=f'Best: {int(x[best_idx])}')
        
        ax4.set_xlabel('Top K Neighbors', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Avg Improvement (%)', fontsize=12, fontweight='bold')
        ax4.set_title(f'Top K vs Performance\nOptimal: {int(x[best_idx])} neighbors ({y_mean[best_idx]:.2f}%)', 
                     fontsize=11, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.legend(loc='best')
        
        ax4.text(0.05, 0.95, f'Range tested: {int(x.min())}-{int(x.max())}', 
                transform=ax4.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    else:
        # Alternative: Efficiency plot (Improvement per second)
        df['Efficiency'] = df['Avg_Improvement_%'] / df['Avg_Solve_Time_s']
        
        # Plot efficiency for each experiment
        x = df['Experiment_ID'].values
        y = df['Efficiency'].values
        
        ax4.bar(x, y, alpha=0.7, color=color_main)
        
        best_idx = y.argmax()
        ax4.bar(x[best_idx], y[best_idx], color='gold', alpha=0.9, 
               label=f'Best: Exp {int(x[best_idx])}')
        
        ax4.set_xlabel('Experiment ID', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Efficiency (% per second)', fontsize=12, fontweight='bold')
        ax4.set_title('Overall Efficiency Comparison\n(Improvement per Second)', 
                     fontsize=11, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.legend(loc='best')
        
        best_exp = df.iloc[best_idx]
        info_text = (f"Best Config:\n"
                    f"iters={int(best_exp['max_iters'])}, "
                    f"tabu={int(best_exp['tabu_allowed'])}\n"
                    f"patience={int(best_exp['patience'])}, "
                    f"top_k={int(best_exp['top_k'])}")
        ax4.text(0.05, 0.95, info_text, 
                transform=ax4.transAxes, fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    plt.tight_layout()
    
    # Save plot
    plot_file = output_dir / "tabu_parameter_analysis.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Parameter analysis plot saved to: {plot_file}")
    
    plt.show()
    
    # Print parameter recommendations
    print("\n" + "="*80)
    print("PARAMETER RECOMMENDATIONS")
    print("="*80)
    
    for param in ['max_iters', 'tabu_allowed', 'patience', 'top_k']:
        if param in df.columns and len(df[param].unique()) > 1:
            grouped = df.groupby(param)['Avg_Improvement_%'].mean()
            best_val = grouped.idxmax()
            best_perf = grouped.max()
            
            print(f"\n{param.upper()}:")
            print(f"  Optimal value: {int(best_val)}")
            print(f"  Performance: {best_perf:.2f}%")
            print(f"  Range tested: {int(df[param].min())}-{int(df[param].max())}")
            
            # Check for diminishing returns
            sorted_grouped = grouped.sort_index()
            if len(sorted_grouped) > 1:
                improvements = sorted_grouped.diff().dropna()
                if len(improvements) > 0 and improvements.iloc[-1] < 0:
                    print(f"  ⚠ Diminishing returns detected after {int(sorted_grouped.index[-2])}")


if __name__ == "__main__":
    output_dir = Path("data/output")
    
    # Find all lateness experiments
    exp_ids = find_all_lateness_experiments(output_dir)
    
    if not exp_ids:
        print("No Lateness experiments found!")
        print("Please run some experiments first.")
        sys.exit(1)
    
    print(f"Found {len(exp_ids)} Lateness experiments: {exp_ids}")
    
    # Load all data
    df = load_all_experiment_data(exp_ids, output_dir)
    
    if df.empty:
        print("No valid experiment data found!")
        sys.exit(1)
    
    print(f"\nAnalyzing {len(df)} experiments...")
    print(f"Parameters available: {[col for col in df.columns if col in ['max_iters', 'tabu_allowed', 'patience', 'top_k']]}")
    
    # Create parameter analysis plots
    plot_parameter_analysis(df, output_dir)
