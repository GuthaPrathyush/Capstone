# Monthly Progress Report - Combined RL (Scheduling + Aggregation)

## Project Scope (This Month)
This month focused on building and improving a **combined RL controller** for UAV communication that jointly handles:

- scheduling (which queue/class to serve), and
- aggregation (how many packets to combine before transmission).

The target benchmark was FCFS/FIFO-style transmission behavior.

---

## 1. Technical Work Completed

### 1.1 Model Development
- Implemented and stabilized a **tabular Q-learning** based combined decision model.
- Finalized unified action encoding for scheduling + aggregation.
- Integrated queue, deadline, link-quality, energy, and AoI signals into the decision process.

### 1.2 Reward and State Tuning
- Performed iterative reward tuning for better trade-off across:
  - delivery/goodput,
  - packet loss,
  - queue handling,
  - AoI,
  - energy impact.
- Improved state bucketing to better capture queue composition and link stability behavior.
- Final tuned training configuration established (`gamma=0` variant for current offline setup).

### 1.3 Dataset Preparation (ns-3)
- Generated/organized pub9 scenario-based ns-3 datasets.
- Built tuned training dataset:
  - `pub9_train_realistic_200k.csv` (200k rows, 22 columns).
- Prepared unseen realistic evaluation sets (new seeds):
  - baseline balanced,
  - energy constrained,
  - high congestion bursty.
- Included additional stress-case evaluation set (weak link/high loss).

### 1.4 Benchmarking and Evaluation
- Completed FCFS vs Proposed benchmark runs across realistic and stress conditions.
- Produced per-scenario and aggregate comparison tables.
- Verified clear improvements of proposed approach on key utility metrics.

### 1.5 Visualization and Reporting
- Built graph generation pipeline for FCFS vs Proposed comparisons.
- Generated publication-style figures for throughput and packet-loss comparisons.
- Generated graph-ready CSV outputs for direct plotting/presentation.

---

## 2. Key Experimental Outcomes

### 2.1 Realistic/High-Congestion Performance
- Demonstrated measurable improvement over FCFS baseline.
- In high-congestion conditions (representative case):
  - throughput improvement: ~6.8%
  - packet-loss reduction: ~49%

### 2.2 Aggregate Comparison
- Across evaluated scenarios, proposed method showed improved overall utility and reduced loss behavior relative to FCFS-style baseline handling.

---

## 3. Deliverables Produced

### 3.1 Code (Core)
- `combined_rl/src/env.py` (tuned reward/action behavior)
- `combined_rl/src/train_qlearning.py` (training pipeline)
- `combined_rl/src/evaluate.py` (evaluation + baseline comparison)
- `combined_rl/src/plot_fcfs_vs_proposed.py` (figure generation)

### 3.2 Model Outputs
- `combined_rl/out_tuned_g0/q_table_combined.npz`

### 3.3 Dataset and Benchmark Artifacts
- `datasets/candidates/ns3/pub9_train_realistic_200k.csv`
- `datasets/candidates/ns3/pub9_realtest/*`
- `combined_rl/out_tuned_g0/*.csv` (benchmark/graph-ready summaries)
- `combined_rl/out_tuned_g0/graphs/*.png`

### 3.4 Documentation
- `combined_rl/README.md` (portable train/validate/test commands)
- `combined_rl/DATASETS_README_TUNED.md`
- `combined_rl/COMBINED_RL_TECHNIQUE_RATIONALE.md`
- `combined_rl/EXECUTIVE_SUMMARY_COMBINED_RL.md`
- `combined_rl/PAPER_SECTION_METHOD_RESULTS_DISCUSSION.md`
- `combined_rl/CONTRIBUTIONS.md`

---

## 4. Collaboration Progress
Work distribution and ownership were documented clearly with near-equal contribution split:

- **Prathyush**: Aggregation-focused development and analysis
- **Harshitha**: Scheduling-focused development and analysis

Integration, benchmarking, and documentation were completed jointly.

---

## 5. Current Project Status
The combined RL module has moved from prototype stage to a reproducible, benchmarked, and documented implementation suitable for mentor review and publication drafting.

---

## 6. Next Month Plan (Execution-Focused)
1. Expand multi-seed statistical reporting (mean +- variation/CI).
2. Finalize paper-ready result tables and figure captions.
3. Package reproducibility script set for one-command experiment reruns.
4. Continue end-to-end integration with the broader project pipeline.
