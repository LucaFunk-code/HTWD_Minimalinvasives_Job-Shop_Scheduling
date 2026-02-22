"""
List all Tabu experiments with their configurations.
"""
import sys
sys.path.insert(0, '.')
from src.domain.orm_models import get_session, Experiment

session = get_session()
experiments = session.query(Experiment).filter(Experiment.id >= 3).order_by(Experiment.id).all()

print('=' * 120)
print('ÜBERSICHT ALLER TABU-EXPERIMENTE')
print('=' * 120)
print(f"{'ID':<5} {'Type':<40} {'w_t':<7} {'w_e':<7} {'w_dev':<7} {'Util':<7} {'Sigma':<7} {'Schedules':<10}")
print('-' * 120)

exp_types = {}
for exp in experiments:
    w_t = float(exp.absolute_lateness_ratio)
    w_e = 1.0 - w_t
    w_dev = float(exp.inner_tardiness_ratio)
    util = float(exp.max_bottleneck_utilization)
    sigma = float(exp.sim_sigma)
    exp_type = exp.experiment_type[:40]
    num_schedules = len(exp.schedules)
    
    # Group by type
    if exp_type not in exp_types:
        exp_types[exp_type] = []
    exp_types[exp_type].append(exp.id)
    
    print(f"{exp.id:<5} {exp_type:<40} {w_t:<7.2f} {w_e:<7.2f} {w_dev:<7.2f} {util:<7.2f} {sigma:<7.2f} {num_schedules:<10}")

print('=' * 120)
print('\nGRUPPIERUNG NACH EXPERIMENT-TYP:')
print('-' * 120)
for exp_type, ids in sorted(exp_types.items()):
    print(f"{exp_type:<40} → IDs: {ids}")
print('=' * 120)
