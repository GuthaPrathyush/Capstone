# Comparison Status: Referenced Q-Learning Model

What is done:
- Created `out_diff_state/` as a parallel output directory.
- Copied your latest trained model to `out_diff_state/q_table_combined.npz`.
- Generated honest comparison CSVs and graphs for your model vs FCFS:
  - `out_diff_state/graph_data_all_scenarios_honest.csv`
  - `out_diff_state/graph_data_baseline_balanced_honest.csv`
  - `out_diff_state/graph_data_energy_constrained_honest.csv`
  - `out_diff_state/graph_data_high_congestion_honest.csv`
  - `out_diff_state/graph_data_weak_link_stress_honest.csv`
  - `out_diff_state/graphs_honest/*.png`

Why direct comparison with the referenced/friends Q-learning model is currently blocked:
- Available friend checkpoints exist (`Harshi/scheduling_rl/out/q_table.npz`, `Pratt/aggregation_gnn/out/q_table_agg.npz`), but they are trained on different MDPs/action spaces.
- Those projects currently do not provide evaluation scripts that output the same metrics and scenario format used by `combined_rl`.
- A Q-table from one MDP cannot be directly loaded into another environment and interpreted correctly.

Exactly what is needed to make cross-model comparison possible:
1. A runnable evaluator for the referenced model that can run on the same 4 test scenarios and output:
   - delivered throughput per step
   - lost packets/bytes per step
   - average reward
2. Or a precomputed CSV from your friends with those exact metrics for the same scenarios.
3. Confirmation of scenario files used by the referenced model (must match or be mapped to the same test sets).

Once provided, we can generate direct side-by-side graphs: `Our Combined Q-Learning` vs `Referenced Q-Learning` vs `FCFS`.
