from src.domain.Query import ExperimentAnalysisQuery
import pandas as pd
from datetime import datetime

# Get schedule data
df_schedules = ExperimentAnalysisQuery.get_schedule_jobs_operations_dataframe()

# Calculate makespan per shift (final makespan after tabu optimization)
makespan_df = (
    df_schedules.groupby(["Experiment_ID", "Shift"])["End"].max().reset_index()
)
makespan_df.rename(columns={"End": "Final_Makespan"}, inplace=True)

# Add initial makespan column (will be populated from logs)
# For now, we'll add a placeholder - you'll need to capture this from the solver
makespan_df["Initial_Makespan"] = None

# Calculate shift metrics
shift_metrics = (
    df_schedules.groupby(["Experiment_ID", "Shift"])
    .agg(
        {
            "End": "max",
            "Start": "min",
            "Job": "nunique",
            "Operation": "count",
        }
    )
    .reset_index()
)

shift_metrics.rename(
    columns={
        "End": "Final_Makespan",
        "Start": "First_Start",
        "Job": "Num_Jobs",
        "Operation": "Num_Operations",
    },
    inplace=True,
)

print("Shift Metrics:")
print(shift_metrics)

# Save to file
output_file = f"data/output/shift_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
shift_metrics.to_csv(output_file, index=False)
print(f"\nMetrics saved to: {output_file}")