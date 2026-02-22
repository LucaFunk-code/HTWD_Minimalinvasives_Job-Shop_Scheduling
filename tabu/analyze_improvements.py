"""
Analyze Tabu Solver improvements from saved CSV files.
Reads improvement data and calculates statistics for a single experiment.
"""
from pathlib import Path
import pandas as pd
import sys
import os

# Get project root (two levels up from this script)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def analyze_improvements(experiment_id=None):
    """Analyze tabu improvement file for a single experiment."""
    
    output_dir = PROJECT_ROOT / "data" / "output"
    
    if experiment_id is None:
        # Find the latest experiment file
        improvement_files = sorted(output_dir.glob("tabu_improvements_exp_*.csv"))
        
        if not improvement_files:
            print("No improvement files found in data/output/")
            print("Run a tabu experiment first to generate improvement data.")
            return
        
        # Take the most recent file
        file_path = improvement_files[-1]
        print(f"No experiment ID specified. Using latest file: {file_path.name}")
    else:
        file_path = output_dir / f"tabu_improvements_exp_{experiment_id}.csv"
        
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            print(f"\nAvailable files:")
            for f in sorted(output_dir.glob("tabu_improvements_exp_*.csv")):
                print(f"  - {f.name}")
            return
    
    # Load data
    df = pd.read_csv(file_path)
    experiment_id = df['Experiment_ID'].iloc[0]
    
    # Try to load configuration
    config_file = output_dir / f"tabu_config_exp_{experiment_id}.csv"
    config = None
    if config_file.exists():
        config = pd.read_csv(config_file).iloc[0]
    
    print("=" * 80)
    print(f"TABU SOLVER ANALYSIS - EXPERIMENT {experiment_id}")
    print("=" * 80)
    print()
    
    # Display configuration if available
    if config is not None:
        print("CONFIGURATION:")
        print("-" * 80)
        print(f"Source Name:                 {config['source_name']}")
        print(f"Max Bottleneck Utilization:  {config['max_bottleneck_utilization']}")
        print(f"Absolute Lateness Ratio:     {config['absolute_lateness_ratio']}")
        print(f"Inner Tardiness Ratio:       {config['inner_tardiness_ratio']}")
        print(f"Sim Sigma:                   {config['sim_sigma']}")
        print(f"Shift Length:                {config['shift_length']}")
        print(f"Total Shift Number:          {config['total_shift_number']}")
        print()
        print("TABU SEARCH SETTINGS:")
        print(f"  TABU_ALLOWED:              {int(config['tabu_allowed'])}")
        print(f"  MAX_ITERS:                 {int(config['max_iters'])}")
        print(f"  PATIENCE:                  {int(config['patience'])}")
        print(f"  TOP_K:                     {int(config['top_k'])}")
        print()
    
    # Display all shift data
    print("SHIFT-BY-SHIFT RESULTS:")
    print("-" * 80)
    print(df.to_string(index=False))
    print()
    
    # Determine objective type from columns
    if 'Initial_Makespan' in df.columns:
        objective_type = "Makespan"
        initial_col = 'Initial_Makespan'
        final_col = 'Final_Makespan'
    elif 'Initial_Lateness_Deviation' in df.columns:
        objective_type = "Lateness_Deviation"
        initial_col = 'Initial_Lateness_Deviation'
        final_col = 'Final_Lateness_Deviation'
    else:
        # Fallback for old format
        objective_type = "Objective"
        initial_col = 'Initial_Objective'
        final_col = 'Final_Objective'
    
    # Statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Objective Type: {objective_type}")
    print(f"Total Shifts: {len(df)}")
    print()
    
    # Improvement statistics
    print("Improvement Statistics:")
    print(f"  Average Improvement: {df['Improvement_Percent'].mean():.2f}%")
    print(f"  Median Improvement:  {df['Improvement_Percent'].median():.2f}%")
    print(f"  Std Deviation:       {df['Improvement_Percent'].std():.2f}%")
    print(f"  Best Improvement:    {df['Improvement_Percent'].max():.2f}% (Shift {df.loc[df['Improvement_Percent'].idxmax(), 'Shift']})")
    print(f"  Worst Improvement:   {df['Improvement_Percent'].min():.2f}% (Shift {df.loc[df['Improvement_Percent'].idxmin(), 'Shift']})")
    print()
    
    # Time statistics
    if 'Solve_Time_Seconds' in df.columns:
        total_solve_time = df['Solve_Time_Seconds'].sum()
        avg_solve_time = df['Solve_Time_Seconds'].mean()
        print("Time Statistics:")
        print(f"  Total Solve Time:    {total_solve_time:.2f}s ({total_solve_time/60:.2f} minutes)")
        print(f"  Average per Shift:   {avg_solve_time:.2f}s")
        print(f"  Fastest Shift:       {df['Solve_Time_Seconds'].min():.2f}s (Shift {df.loc[df['Solve_Time_Seconds'].idxmin(), 'Shift']})")
        print(f"  Slowest Shift:       {df['Solve_Time_Seconds'].max():.2f}s (Shift {df.loc[df['Solve_Time_Seconds'].idxmax(), 'Shift']})")
        print()
    
    # Memory statistics
    if 'Memory_MB' in df.columns:
        peak_memory = df['Memory_MB'].max()
        avg_memory = df['Memory_MB'].mean()
        total_memory_used = df['Memory_Used_MB'].sum() if 'Memory_Used_MB' in df.columns else 0
        print("Memory Statistics:")
        print(f"  Peak Memory:         {peak_memory:.2f}MB (Shift {df.loc[df['Memory_MB'].idxmax(), 'Shift']})")
        print(f"  Average Memory:      {avg_memory:.2f}MB")
        if 'Memory_Used_MB' in df.columns:
            print(f"  Total Memory Used:   {total_memory_used:.2f}MB")
        print()
    
    # Operations statistics
    if 'Num_Operations' in df.columns:
        total_ops = df['Num_Operations'].sum()
        avg_ops = df['Num_Operations'].mean()
        print("Operations Statistics:")
        print(f"  Total Operations:    {total_ops}")
        print(f"  Average per Shift:   {avg_ops:.2f}")
        print(f"  Min Operations:      {df['Num_Operations'].min()} (Shift {df.loc[df['Num_Operations'].idxmin(), 'Shift']})")
        print(f"  Max Operations:      {df['Num_Operations'].max()} (Shift {df.loc[df['Num_Operations'].idxmax(), 'Shift']})")
        print()
    
    # Objective value statistics
    print(f"{objective_type} Statistics:")
    print(f"  Avg Initial {objective_type}: {df[initial_col].mean():.2f}")
    print(f"  Avg Final {objective_type}:   {df[final_col].mean():.2f}")
    print(f"  Total Improvement:            {df['Improvement'].sum():.2f}")
    
    print()
    print("=" * 80)
    print(f"Data loaded from: {file_path}")
    print("=" * 80)


if __name__ == "__main__":
    # Check if experiment ID was provided as command line argument
    if len(sys.argv) > 1:
        try:
            exp_id = int(sys.argv[1])
            analyze_improvements(exp_id)
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid experiment ID")
            print("Usage: python3 analyze_tabu_improvements.py [experiment_id]")
    else:
        # Use latest experiment if no ID provided
        analyze_improvements()
