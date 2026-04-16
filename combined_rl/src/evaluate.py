from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from .env import CombinedActions, CombinedRewardWeights, transmission_model
from .train_qlearning import state_key


def load_q_table(path: str) -> Dict[Tuple[int, ...], np.ndarray]:
    z = np.load(path)
    keys = z["keys"]
    values = z["values"]
    Q: Dict[Tuple[int, ...], np.ndarray] = {}
    for i in range(keys.shape[0]):
        Q[tuple(int(x) for x in keys[i])] = values[i].astype(np.float32)
    return Q


def policy_q(Q: Dict[Tuple[int, ...], np.ndarray], s: Tuple[int, ...]) -> int:
    if s not in Q:
        return CombinedActions.encode(CombinedActions.HOLD, 1)
    return int(np.argmax(Q[s]))


def policy_baseline(name: str, r0: pd.Series) -> int:
    # Simple baselines for comparison
    if name == "hold":
        return CombinedActions.encode(CombinedActions.HOLD, 1)
    if name == "serve_p2_noagg":
        return CombinedActions.encode(CombinedActions.SERVE_P2, 1)
    if name == "serve_p2_agg5":
        return CombinedActions.encode(CombinedActions.SERVE_P2, 5)
    if name == "serve_best_nonempty":
        q = [int(r0.get("q_p0_pkts", 0)), int(r0.get("q_p1_pkts", 0)), int(r0.get("q_p2_pkts", 0))]
        if q[2] > 0:
            return CombinedActions.encode(CombinedActions.SERVE_P2, 3)
        if q[1] > 0:
            return CombinedActions.encode(CombinedActions.SERVE_P1, 2)
        if q[0] > 0:
            return CombinedActions.encode(CombinedActions.SERVE_P0, 1)
        return CombinedActions.encode(CombinedActions.HOLD, 1)
    raise ValueError(f"Unknown baseline: {name}")


def run_eval(df: pd.DataFrame, policy_name: str, Q=None, step_ms: int = 10, steps: int = 8000) -> dict:
    w = CombinedRewardWeights()
    total_r = 0.0
    total_delivered = 0.0
    total_attempted = 0.0
    holds = 0

    for i in range(min(steps, len(df) - 2)):
        r0 = df.iloc[i]
        if policy_name == "q":
            a = policy_q(Q, state_key(r0))
        else:
            a = policy_baseline(policy_name, r0)

        r, info = transmission_model(
            step_ms=step_ms,
            q_p0=int(r0.get("q_p0_pkts", 0)),
            q_p1=int(r0.get("q_p1_pkts", 0)),
            q_p2=int(r0.get("q_p2_pkts", 0)),
            packet_size=float(r0.get("packet_size", 0.0)),
            min_deadline=float(r0.get("min_deadline", 0.0)),
            mean_deadline=float(r0.get("mean_deadline", 0.0)),
            goodput_kbps=float(r0.get("goodput_kbps", 0.0)),
            packet_loss_rate=float(r0.get("packet_loss_rate", 0.0)),
            link_stability=float(r0.get("link_stability", 0.0)),
            aoi_ms=float(r0.get("aoi_ms", 0.0)),
            energy_level=float(r0.get("energy_level", 0.0)),
            action=int(a),
            w=w,
        )
        total_r += float(r)
        total_delivered += float(info["delivered_bytes"])
        total_attempted += float(info["attempted_bytes"])
        if info["schedule_choice"] == CombinedActions.HOLD:
            holds += 1

    return {
        "policy": policy_name,
        "steps": int(min(steps, len(df) - 2)),
        "avg_reward": float(total_r / max(1, steps)),
        "delivered_bytes_total": float(total_delivered),
        "attempted_bytes_total": float(total_attempted),
        "delivery_ratio": float(total_delivered / max(1.0, total_attempted)),
        "hold_frac": float(holds / max(1, steps)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--q_table", required=True)
    ap.add_argument("--step_ms", type=int, default=10)
    ap.add_argument("--steps", type=int, default=8000)
    args = ap.parse_args()

    df = pd.read_csv(args.data, low_memory=False)
    Q = load_q_table(args.q_table)

    results = []
    results.append(run_eval(df, "q", Q=Q, step_ms=args.step_ms, steps=args.steps))
    for b in ["hold", "serve_p2_noagg", "serve_p2_agg5", "serve_best_nonempty"]:
        results.append(run_eval(df, b, Q=None, step_ms=args.step_ms, steps=args.steps))

    out = pd.DataFrame(results)
    pd.set_option("display.max_columns", 200)
    print(out)


if __name__ == "__main__":
    main()

