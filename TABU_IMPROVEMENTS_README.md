# Tabu Solver Improvement Tracking

This document explains how to track and analyze the improvements made by the Tabu Solver for job-shop scheduling.

## Overview

The Tabu Solver now tracks:
- **Initial Makespan**: The makespan of the randomly generated initial solution
- **Final Makespan**: The optimized makespan after tabu search
- **Improvement**: Absolute reduction in makespan
- **Improvement Percentage**: Percentage improvement for each shift

## Running Experiments with Improvement Tracking

### 1. Run a Tabu Experiment

Execute the tabu solver experiment:

```bash
python run_single_tabu_ft10.py
```

This will:
- Create a new experiment in the database
- Run the tabu solver for each shift
- Track initial and final makespan values
- Save improvement data to `data/output/tabu_improvements_exp_<ID>.csv`
- Display improvement percentages in the console/log

### 2. Analyze the Results

After running one or more experiments, analyze the improvements:

```bash
python analyze_tabu_improvements.py
```

This script will:
- Load all improvement CSV files from `data/output/`
- Display per-experiment statistics
- Calculate overall statistics across all experiments
- Generate summary files:
  - `tabu_improvements_summary.csv` - Combined data from all experiments
  - `tabu_improvements_stats.csv` - Aggregated statistics per experiment

## Output Files

### Individual Experiment Files
`data/output/tabu_improvements_exp_<ID>.csv`

Contains per-shift data:
```csv
Experiment_ID,Shift,Initial_Makespan,Final_Makespan,Improvement,Improvement_Percent
1,1,5432,4891,541,9.96
1,2,6234,5678,556,8.92
...
```

### Summary File
`data/output/tabu_improvements_summary.csv`

Combined data from all experiments for aggregate analysis.

### Statistics File
`data/output/tabu_improvements_stats.csv`

Per-experiment statistics including:
- Mean improvement percentage
- Standard deviation
- Min/Max improvements
- Number of shifts
- Average makespans

## Implementation Details

### Modified Files

1. **`src/solvers/Tabu_Solver.py`**
   - `solve()` method now returns: `(schedule, initial_makespan, final_makespan)`
   - Tracks the initial random solution's makespan

2. **`src/Tabu_Experiment_Runner.py`**
   - Captures initial and final makespan values
   - Calculates improvement percentages
   - Writes data to CSV files
   - Logs improvement statistics

3. **`analyze_tabu_improvements.py`** (NEW)
   - Standalone analysis script
   - Generates comprehensive statistics
   - Creates summary reports

## Example Output

```
Experiment 42:
--------------------------------------------------------------------------------
 Experiment_ID  Shift  Initial_Makespan  Final_Makespan  Improvement  Improvement_Percent
            42      1              5432            4891          541                 9.96
            42      2              6234            5678          556                 8.92
            42      3              5891            5234          657                11.15

Average Improvement: 10.01%
Best Improvement: 11.15% (Shift 3)
Worst Improvement: 8.92% (Shift 2)
```

## Configuration

You can adjust the tabu search parameters in `run_single_tabu_ft10.py`:

```python
TABU_ALLOWED = 25        # Tabu list size
MAX_ITERS = 300          # Maximum iterations
PATIENCE = 40            # Iterations without improvement before diversification
TOP_K = 60               # Number of candidates for diversification
```

Higher values generally lead to better improvements but take longer to run.

## Using with Other Scripts

If you're running tabu experiments from other scripts, the improvements will be automatically tracked as long as you:

1. Use the `run_experiment()` function from `src.Tabu_Experiment_Runner`
2. The solver's `solve()` method returns the tuple: `(schedule, initial_makespan, final_makespan)`

## Troubleshooting

### No improvement files found
- Make sure you've run at least one tabu experiment
- Check that the experiment completed successfully
- Verify the `data/output/` directory exists

### Negative improvement percentages
- This means the initial solution was better than the optimized one (rare but possible with very short runs)
- Consider increasing `MAX_ITERS` or adjusting other parameters

## Further Analysis

You can load the CSV files into pandas for custom analysis:

```python
import pandas as pd

# Load specific experiment
df = pd.read_csv('data/output/tabu_improvements_exp_42.csv')

# Load summary of all experiments
summary = pd.read_csv('data/output/tabu_improvements_summary.csv')

# Custom analysis
print(df['Improvement_Percent'].describe())
```
