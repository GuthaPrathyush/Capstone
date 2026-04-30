# Backend Runbook

This folder contains two independent services:

- [qlearning_backend](qlearning_backend/) — serves the trained Q-table as a policy API
- [sim_pinger_backend](sim_pinger_backend/) — replays the dataset, keeps volatile queue state, and pings the policy API each tick

## Prerequisites

- Python 3.12 or newer
- The trained model file at [qlearning_backend/models/q_table_combined.npz](qlearning_backend/models/q_table_combined.npz)

If you want to use the versioned model created in this workspace, copy:

```bash
cp /home/gutha-prathyush/Documents/Capstone/combined_rl/out_1.0/q_table_combined.npz \
   /home/gutha-prathyush/Documents/Capstone/backend/qlearning_backend/models/q_table_combined.npz
```

## 1) Start the policy backend

From the workspace root:

```bash
cd /home/gutha-prathyush/Documents/Capstone/backend/qlearning_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

### Policy backend endpoints

- `GET /health`
- `POST /reload`
- `POST /predict`

Quick health check:

```bash
curl -s http://127.0.0.1:8001/health
```

## 2) Start the simulation backend

Open a second terminal:

```bash
cd /home/gutha-prathyush/Documents/Capstone/backend/sim_pinger_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8002 --reload
```

### Simulation backend endpoints

- `GET /health`
- `POST /load`
- `POST /step`
- `POST /run`

Quick health check:

```bash
curl -s http://127.0.0.1:8002/health
```

## 3) Load a dataset into the simulator

Use one of the ns-3 CSVs already present in the repository. Example:

```bash
curl -X POST "http://127.0.0.1:8002/load" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_path": "/home/gutha-prathyush/Documents/Capstone/datasets/candidates/ns3/pub9_realtest/pub9_rt_baseline_balanced_50k.csv",
    "policy_url": "http://127.0.0.1:8001/predict",
    "queue_cap_pkts": 60,
    "tick_ms": 10
  }'
```

If you want a different scenario, replace `dataset_path` with one of these common files:

- `datasets/candidates/ns3/pub9_realtest/pub9_rt_baseline_balanced_50k.csv`
- `datasets/candidates/ns3/pub9_realtest/pub9_rt_energy_constrained_50k.csv`
- `datasets/candidates/ns3/pub9_realtest/pub9_rt_high_congestion_bursty_50k.csv`

## 4) Run the simulation

One tick:

```bash
curl -X POST "http://127.0.0.1:8002/step"
```

Multiple ticks:

```bash
curl -X POST "http://127.0.0.1:8002/run?steps=100"
```

## Recommended execution order

1. Start the policy backend on port `8001`
2. Start the simulation backend on port `8002`
3. Call `/load` on the simulation backend
4. Call `/step` or `/run`

## Notes

- The policy backend is independent of the simulator.
- The simulator owns the volatile queue state.
- The CSV acts as the replay trace that drives each tick.
- `run` simply loops over `step` internally.

## Closed-Loop Approach (Developed in This Project)

The backend is intentionally split into two services to implement a closed-loop
control flow between observed network state and scheduling action.

### Components

- `qlearning_backend` hosts the trained policy (`/predict`) and returns an action
  for the current state snapshot.
- `sim_pinger_backend` is the environment runner that:
  - reads one CSV row per tick,
  - builds the current queue/channel state,
  - pings the policy endpoint,
  - applies the returned action to update queue dynamics,
  - emits metrics for that step.

### Closed-loop cycle per tick

1. Simulator reads replay state from dataset row `t`.
2. Simulator sends state payload to policy server (`POST /predict`).
3. Policy server returns action (queue choice + aggregation decision).
4. Simulator applies action using transmission model and updates queue state.
5. Simulator advances to row `t+1` with updated internal state.

This loop is executed once in `/step` and repeated `N` times in `/run?steps=N`.

### Why this matters

- Keeps model serving and environment simulation decoupled.
- Mirrors deployment-style inference where policy and runtime are separate.
- Makes it easy to swap model versions (`/reload`) without changing simulator code.
- Enables reproducible, scenario-wise benchmarking with fixed replay traces.
