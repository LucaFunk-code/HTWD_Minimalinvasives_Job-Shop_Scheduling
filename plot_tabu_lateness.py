"""
Visualize Tabu Solver results for Lateness Deviation optimization.
Usage: python3 plot_tabu_lateness.py [experiment_id]
"""

import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def plot_lateness_results(experiment_id=None):
    """Create comprehensive plots for Lateness Deviation optimization results."""
    
    output_dir = Path("data/output")
    
    # Find experiment file
    if experiment_id is None:
        improvement_files = sorted(output_dir.glob("tabu_improvements_exp_*.csv"))
        if not improvement_files:
            print("No improvement files found!")
            return
        file_path = improvement_files[-1]
        print(f"Using latest file: {file_path.name}")
    else:
        file_path = output_dir / f"tabu_improvements_exp_{experiment_id}.csv"
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return
    
    # Load data
    df = pd.read_csv(file_path)
    
    # Check if it's Lateness data
    if 'Initial_Lateness_Deviation' not in df.columns:
        print("Error: This file does not contain Lateness Deviation data!")
        print("Use plot_tabu_makespan.py for Makespan data.")
        return
    
    experiment_id = df['Experiment_ID'].iloc[0]
    
    # Load configuration if available
    config_file = output_dir / f"tabu_config_exp_{experiment_id}.csv"
    config = None
    if config_file.exists():
        config = pd.read_csv(config_file).iloc[0]
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    title = f'Tabu Solver - Lateness Deviation Optimization (Experiment {experiment_id})'
    if config is not None:
        title += f'\nWeights: w_t={config["w_t"]:.2f}, w_e={config["w_e"]:.2f}, w_dev={config["w_dev"]:.2f}'
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    # 1. Initial vs Final Lateness Deviation
    ax1 = plt.subplot(3, 3, 1)
    x = df['Shift']
    width = 0.35
    ax1.bar(x - width/2, df['Initial_Lateness_Deviation'], width, label='Initial', alpha=0.8, color='#ff7f0e')
    ax1.bar(x + width/2, df['Final_Lateness_Deviation'], width, label='Final', alpha=0.8, color='#2ca02c')
    ax1.set_xlabel('Shift')
    ax1.set_ylabel('Lateness Deviation')
    ax1.set_title('Initial vs Final Lateness Deviation per Shift')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Improvement Percentage
    ax2 = plt.subplot(3, 3, 2)
    ax2.plot(df['Shift'], df['Improvement_Percent'], marker='o', linewidth=2, 
             markersize=8, color='#1f77b4')
    ax2.axhline(y=df['Improvement_Percent'].mean(), color='r', linestyle='--', 
                label=f'Avg: {df["Improvement_Percent"].mean():.2f}%')
    ax2.set_xlabel('Shift')
    ax2.set_ylabel('Improvement (%)')
    ax2.set_title('Improvement Percentage per Shift')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Absolute Improvement
    ax3 = plt.subplot(3, 3, 3)
    colors = ['#2ca02c' if x > 0 else '#d62728' for x in df['Improvement']]
    ax3.bar(df['Shift'], df['Improvement'], color=colors, alpha=0.7)
    ax3.set_xlabel('Shift')
    ax3.set_ylabel('Improvement (absolute)')
    ax3.set_title('Absolute Lateness Reduction')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Number of Operations
    ax4 = plt.subplot(3, 3, 4)
    ax4.plot(df['Shift'], df['Num_Operations'], marker='s', linewidth=2, 
             markersize=8, color='#9467bd')
    ax4.set_xlabel('Shift')
    ax4.set_ylabel('Number of Operations')
    ax4.set_title('Operations per Shift')
    ax4.grid(True, alpha=0.3)
    
    # 5. Solve Time
    ax5 = plt.subplot(3, 3, 5)
    ax5.bar(df['Shift'], df['Solve_Time_Seconds'], alpha=0.7, color='#8c564b')
    ax5.set_xlabel('Shift')
    ax5.set_ylabel('Time (seconds)')
    ax5.set_title('Solve Time per Shift')
    ax5.grid(True, alpha=0.3, axis='y')
    
    # 6. Memory Usage
    if 'Memory_MB' in df.columns:
        ax6 = plt.subplot(3, 3, 6)
        ax6.plot(df['Shift'], df['Memory_MB'], marker='o', linewidth=2, 
                 color='#e377c2', label='Total Memory')
        if 'Memory_Used_MB' in df.columns:
            ax6_twin = ax6.twinx()
            ax6_twin.bar(df['Shift'], df['Memory_Used_MB'], alpha=0.3, 
                        color='#7f7f7f', label='Memory Used')
            ax6_twin.set_ylabel('Memory Used (MB)', color='#7f7f7f')
            ax6_twin.tick_params(axis='y', labelcolor='#7f7f7f')
        ax6.set_xlabel('Shift')
        ax6.set_ylabel('Total Memory (MB)', color='#e377c2')
        ax6.set_title('Memory Usage')
        ax6.tick_params(axis='y', labelcolor='#e377c2')
        ax6.grid(True, alpha=0.3)
        ax6.legend(loc='upper left')
    
    # 7. Lateness Reduction Trend
    ax7 = plt.subplot(3, 3, 7)
    cumulative_improvement = df['Improvement'].cumsum()
    ax7.fill_between(df['Shift'], 0, cumulative_improvement, alpha=0.3, color='#2ca02c')
    ax7.plot(df['Shift'], cumulative_improvement, marker='o', linewidth=2, 
             color='#2ca02c', markersize=8)
    ax7.set_xlabel('Shift')
    ax7.set_ylabel('Cumulative Improvement')
    ax7.set_title('Cumulative Lateness Reduction')
    ax7.grid(True, alpha=0.3)
    
    # 8. Statistics Summary (Text)
    ax8 = plt.subplot(3, 3, 8)
    ax8.axis('off')
    stats_text = f"""
    SUMMARY STATISTICS
    {'='*30}
    Total Shifts: {len(df)}
    
    Lateness Deviation:
      Avg Initial: {df['Initial_Lateness_Deviation'].mean():.2f}
      Avg Final:   {df['Final_Lateness_Deviation'].mean():.2f}
      Total Saved: {df['Improvement'].sum():.2f}
    
    Improvement:
      Average: {df['Improvement_Percent'].mean():.2f}%
      Median:  {df['Improvement_Percent'].median():.2f}%
      Best:    {df['Improvement_Percent'].max():.2f}%
      Worst:   {df['Improvement_Percent'].min():.2f}%
    
    Time:
      Total: {df['Solve_Time_Seconds'].sum():.2f}s
      Average: {df['Solve_Time_Seconds'].mean():.2f}s/shift
    
    Operations:
      Total: {df['Num_Operations'].sum()}
      Average: {df['Num_Operations'].mean():.0f}/shift
    """
    if 'Memory_MB' in df.columns:
        stats_text += f"\n    Memory:\n      Peak: {df['Memory_MB'].max():.2f}MB"
    
    if config is not None:
        stats_text += f"\n\n    Weights:\n      w_t:   {config['w_t']:.2f}\n      w_e:   {config['w_e']:.2f}\n      w_dev: {config['w_dev']:.2f}"
    
    ax8.text(0.1, 0.9, stats_text, transform=ax8.transAxes, 
             fontsize=10, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    # 9. Improvement Distribution
    ax9 = plt.subplot(3, 3, 9)
    ax9.hist(df['Improvement_Percent'], bins=min(10, len(df)), 
             alpha=0.7, color='#1f77b4', edgecolor='black')
    ax9.axvline(df['Improvement_Percent'].mean(), color='r', linestyle='--', 
                linewidth=2, label=f'Mean: {df["Improvement_Percent"].mean():.2f}%')
    ax9.set_xlabel('Improvement (%)')
    ax9.set_ylabel('Frequency')
    ax9.set_title('Improvement Distribution')
    ax9.legend()
    ax9.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Save figure
    plot_file = output_dir / f"tabu_lateness_plot_exp_{experiment_id}.png"
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Plot saved to: {plot_file}")
    
    # Show plot
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            exp_id = int(sys.argv[1])
            plot_lateness_results(exp_id)
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid experiment ID")
            print("Usage: python3 plot_tabu_lateness.py [experiment_id]")
    else:
        plot_lateness_results()
