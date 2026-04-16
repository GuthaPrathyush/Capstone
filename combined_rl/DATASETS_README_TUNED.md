# Datasets README (Latest Tuned Combined RL Model)

This document lists all datasets used for the **latest tuned combined RL model** (`out_tuned_g0`) and explains how they were prepared.

## 1. Model Version Covered
- Model output directory: `combined_rl/out_tuned_g0/`
- Main Q-table: `combined_rl/out_tuned_g0/q_table_combined.npz`
- Training style: tabular Q-learning (tuned reward/state, `gamma=0`)

---

## 2. Raw ns-3 Scenario Datasets (pub9)
All base datasets are under:
- `datasets/candidates/ns3/`

Key scenario files used in this stage:
- `pub9_baseline_balanced_50k.csv`
- `pub9_energy_constrained_50k.csv`
- `pub9_high_congestion_bursty_50k.csv`
- `pub9_mixed_medium_stress_50k.csv`
- `pub9_weak_link_high_loss_50k.csv`

Each file has:
- ~50,000 data rows (+ header)
- 22 columns (queue, deadline, link quality, energy, AoI, aggregation-related fields)

The current tabular Q-learning model uses only a compact subset of these fields for state construction:
- queue length / pressure,
- urgent queue mix,
- deadline pressure,
- channel quality.

The remaining fields still matter through reward shaping and evaluation reporting.

---

## 3. Final Training Dataset (Used by Tuned Model)
**Training file**:
- `datasets/candidates/ns3/pub9_train_realistic_200k.csv`

This file was created by concatenating + shuffling 4 scenario datasets:
1. `pub9_baseline_balanced_50k.csv`
2. `pub9_energy_constrained_50k.csv`
3. `pub9_high_congestion_bursty_50k.csv`
4. `pub9_mixed_medium_stress_50k.csv`

Total size:
- 200,000 rows
- 22 columns

Why this mix:
- emphasizes realistic/learnable communication regimes,
- still includes stress behavior (mixed medium stress),
- avoids training only on impossible-link conditions.

---

## 4. Unseen Evaluation Datasets (Realistic Seeds)
Generated separately (new seeds) for fair evaluation:

Folder:
- `datasets/candidates/ns3/pub9_realtest/`

Files:
- `pub9_rt_baseline_balanced_50k.csv` (seed 3000)
- `pub9_rt_energy_constrained_50k.csv` (seed 3001)
- `pub9_rt_high_congestion_bursty_50k.csv` (seed 3002)

Purpose:
- out-of-sample testing against FCFS/baselines,
- same scenario families but unseen random realizations.

---

## 5. Stress-Test Dataset
Used to check behavior in severe link conditions:
- `datasets/candidates/ns3/pub9_weak_link_high_loss_50k.csv`

Purpose:
- robustness evaluation under harsh channel conditions,
- expected low delivery for all policies.

---

## 6. Derived Comparison Datasets (Generated Metrics)
These are post-processing outputs used for reporting/plots.

Directory:
- `combined_rl/out_tuned_g0/`

Important files:
- `benchmark_fcfs_vs_combined_g0_quick.csv`
- `benchmark_hybrid_quick.csv`
- `comparison_graph_ready_per_scenario.csv`
- `comparison_graph_ready_focus_highcong_energy.csv`
- `comparison_graph_ready_all.csv`
- `graph_data_highcong_fcfs_vs_proposed.csv`
- `graph_data_all_fcfs_vs_proposed.csv`

These are **not raw simulation data**; they are computed summaries/benchmarks.

---

## 7. Reproducibility Commands (Dataset Pipeline)
Run from workspace root: `/home/gutha-prathyush/Documents/Capstone`

### 7.1 Build training dataset
```bash
/home/gutha-prathyush/Documents/Capstone/combined_rl/.venv_combined/bin/python - <<'PY'
import pandas as pd
paths=[
 'datasets/candidates/ns3/pub9_baseline_balanced_50k.csv',
 'datasets/candidates/ns3/pub9_energy_constrained_50k.csv',
 'datasets/candidates/ns3/pub9_high_congestion_bursty_50k.csv',
 'datasets/candidates/ns3/pub9_mixed_medium_stress_50k.csv'
]
out='datasets/candidates/ns3/pub9_train_realistic_200k.csv'
df=pd.concat([pd.read_csv(p,low_memory=False) for p in paths],ignore_index=True)
df=df.sample(frac=1.0,random_state=42).reset_index(drop=True)
df.to_csv(out,index=False)
print('saved',out,df.shape)
PY
```

### 7.2 Generate unseen realtest datasets (ns-3)
```bash
NS3BIN=/home/gutha-prathyush/Documents/NS-3/ns3/build/scratch/ns3-dev-uav_rl_dataset_pub9-optimized
mkdir -p datasets/candidates/ns3/pub9_realtest
$NS3BIN --scenario=baseline_balanced --rows=50000 --seed=3000 --out=datasets/candidates/ns3/pub9_realtest/pub9_rt_baseline_balanced_50k.csv
$NS3BIN --scenario=energy_constrained --rows=50000 --seed=3001 --out=datasets/candidates/ns3/pub9_realtest/pub9_rt_energy_constrained_50k.csv
$NS3BIN --scenario=high_congestion_bursty --rows=50000 --seed=3002 --out=datasets/candidates/ns3/pub9_realtest/pub9_rt_high_congestion_bursty_50k.csv
```

---

## 8. Metric Unit Note
Some outputs are reported as `*_per_step` (step = 10 ms). For cross-project comparisons, convert if needed:
- per-second value = per-step value / 0.01

Example:
- `0.50 packets/step` -> `50 packets/sec`

For paper tables, keep the unit definition explicit and compare only metrics computed with the same step/window convention.

---

## 9. Recommended Citation Text (Dataset Section)
"We train on a 200k-row ns-3 composite dataset built from balanced, energy-constrained, high-congestion, and mixed-stress scenarios, and evaluate on unseen-seed realistic scenarios plus a weak-link stress set to assess both utility and robustness."
