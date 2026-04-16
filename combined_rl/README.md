## Combined RL: Scheduling + Aggregation (ns-3 dataset)

This folder trains a **single RL agent** that makes **both**:
- **Scheduling** decisions (which priority class to serve, or HOLD)
- **Aggregation** decisions (how many packets to aggregate per transmission)

It is designed for your **combined idea**: RL + AoI + energy + congestion/link prediction signals.

Current training uses a **compact tabular state** with 4 main signals:
- queue pressure,
- urgent traffic mix,
- deadline pressure,
- channel quality.

Other quantities such as AoI, energy, and loss are mainly handled in the reward shaping.

### Dataset (input)

Use the ns-3 CSV you generated:

- `datasets/candidates/ns3/uav_ns3_combined_v6_50k.csv`

Expected columns (22):
- `timestamp`
- `queue_length`, `q_len_bytes`, `q_p0_pkts`, `q_p1_pkts`, `q_p2_pkts`
- `packet_size`, `priority`, `deadline`, `min_deadline`, `mean_deadline`
- `snr`, `signal_dbm`, `noise_dbm`
- `goodput_kbps`, `packet_loss_rate`, `link_stability`
- `distance_to_receiver`, `energy_level`, `aoi_ms`
- `aggregation_possible`, `num_packets_aggregated`

### Install

```bash
python3 -m venv .venv_combined
source .venv_combined/bin/activate
pip install -r requirements.txt
```

### Train (NumPy-only tabular Q-learning)

```bash
python3 -m src.train_qlearning \
  --data "../../datasets/candidates/ns3/uav_ns3_combined_v6_50k.csv" \
  --out_dir "./out" \
  --episodes 40 \
  --max_steps 4000
```

### Evaluate + baselines

```bash
python3 -m src.evaluate \
  --data "../../datasets/candidates/ns3/uav_ns3_combined_v6_50k.csv" \
  --q_table "./out/q_table_combined.npz"
```

## Tuned Workflow (Latest)

Use this section for the current tuned model (`out_tuned_g0`).

### 1) Build tuned training dataset (200k)

Run from workspace root:

```bash
cd ..
./combined_rl/.venv_combined/bin/python - <<'PY'
import pandas as pd
paths = [
    'datasets/candidates/ns3/pub9_baseline_balanced_50k.csv',
    'datasets/candidates/ns3/pub9_energy_constrained_50k.csv',
    'datasets/candidates/ns3/pub9_high_congestion_bursty_50k.csv',
    'datasets/candidates/ns3/pub9_mixed_medium_stress_50k.csv',
]
out = 'datasets/candidates/ns3/pub9_train_realistic_200k.csv'
df = pd.concat([pd.read_csv(p, low_memory=False) for p in paths], ignore_index=True)
df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
df.to_csv(out, index=False)
print('saved', out, df.shape)
PY
```

### 2) Train tuned model

```bash
cd ..
PYTHONPATH=. \
./combined_rl/.venv_combined/bin/python \
  -m combined_rl.src.train_qlearning \
  --data ./datasets/candidates/ns3/pub9_train_realistic_200k.csv \
  --out_dir ./combined_rl/out_tuned_g0 \
  --episodes 70 --alpha 0.2 --gamma 0.0 --eps 0.25 --max_steps 6000 --step_ms 10
```

State note: the current tabular policy is intentionally compact so it remains interpretable and trainable without DQN. If you expand the state much further, the tabular space grows quickly.

### 3) Validation / Testing commands

Validation-like realistic scenarios:

```bash
cd ..
PYTHONPATH=. \
./combined_rl/.venv_combined/bin/python \
  -m combined_rl.src.evaluate \
  --data ./datasets/candidates/ns3/pub9_realtest/pub9_rt_baseline_balanced_50k.csv \
  --q_table ./combined_rl/out_tuned_g0/q_table_combined.npz \
  --steps 8000

PYTHONPATH=. \
./combined_rl/.venv_combined/bin/python \
  -m combined_rl.src.evaluate \
  --data ./datasets/candidates/ns3/pub9_realtest/pub9_rt_energy_constrained_50k.csv \
  --q_table ./combined_rl/out_tuned_g0/q_table_combined.npz \
  --steps 8000
```

Stress test:

```bash
cd ..
PYTHONPATH=. \
./combined_rl/.venv_combined/bin/python \
  -m combined_rl.src.evaluate \
  --data ./datasets/candidates/ns3/pub9_weak_link_high_loss_50k.csv \
  --q_table ./combined_rl/out_tuned_g0/q_table_combined.npz \
  --steps 8000
```

For full dataset mapping and generation commands, see:

- `combined_rl/DATASETS_README_TUNED.md`

### Important note (what this is, and what it isn’t)

This is a **dataset-driven** RL prototype:
- State comes from the dataset rows.
- Actions affect the **reward** via a lightweight transmission/aggregation model.
- The dataset’s next row is used as the next state (so the environment dynamics are not fully closed-loop).

This means the current training/evaluation pipeline is best described as **offline proxy RL** rather than fully closed-loop control.

For a fully closed-loop “real RL” setup, the next step is to **run the agent inside ns-3** (agent chooses action each step; ns-3 produces next state).

