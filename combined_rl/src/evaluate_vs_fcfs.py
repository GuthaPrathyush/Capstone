"""
Comprehensive evaluation: Combined RL vs FCFS baseline.
Shows aggregation + scheduling improvements.
"""

from __future__ import annotations

import argparse
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
    """RL policy: argmax Q(s,a)"""
    if s not in Q:
        return CombinedActions.encode(CombinedActions.HOLD, 1)
    return int(np.argmax(Q[s]))


def policy_fcfs(r0: pd.Series) -> int:
    """FCFS: transmit from highest priority queue available, no aggregation (agg_k=1)"""
    q = [int(r0.get("q_p0_pkts", 0)), int(r0.get("q_p1_pkts", 0)), int(r0.get("q_p2_pkts", 0))]
    # FCFS: check priority 2 first, then 1, then 0
    if q[2] > 0:
        return CombinedActions.encode(CombinedActions.SERVE_P2, 1)
    if q[1] > 0:
        return CombinedActions.encode(CombinedActions.SERVE_P1, 1)
    if q[0] > 0:
        return CombinedActions.encode(CombinedActions.SERVE_P0, 1)
    return CombinedActions.encode(CombinedActions.HOLD, 1)


def run_eval(
    df: pd.DataFrame,
    policy_name: str,
    Q=None,
    step_ms: int = 10,
    steps: int = 8000,
) -> dict:
    """
    Run evaluation and track:
    - Total reward
    - Delivery metrics (bytes, ratio)
    - Energy efficiency (work per joule)
    - Aggregation benefit (messages sent vs attempted)
    - Deadline compliance (priority bias)
    """
    w = CombinedRewardWeights()
    total_r = 0.0
    total_delivered = 0.0
    total_attempted = 0.0
    total_energy = 0.0
    holds = 0
    transmissions = 0
    aggregated_decisions = 0
    messages_sent_count = 0
    messages_potential = 0
    deadline_bonuses = 0.0

    for i in range(min(steps, len(df) - 2)):
        r0 = df.iloc[i]
        
        if policy_name == "q":
            a = policy_q(Q, state_key(r0))
        elif policy_name == "fcfs":
            a = policy_fcfs(r0)
        else:
            raise ValueError(f"Unknown policy: {policy_name}")

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
        total_energy += float(info["energy_cost"])
        
        if info["schedule_choice"] == CombinedActions.HOLD:
            holds += 1
        else:
            transmissions += 1
            # Measure aggregation: agg_k > 1 means we tried to aggregate multiple packets
            if info["agg_k"] > 1:
                aggregated_decisions += 1
        
        messages_sent_count += max(0.0, info["send_pkts"])
        messages_potential += float(r0.get("q_p0_pkts", 0)) + float(r0.get("q_p1_pkts", 0)) + float(r0.get("q_p2_pkts", 0))
        deadline_bonuses += float(info["deadline_bonus"])

    avg_steps = min(steps, len(df) - 2)
    
    # Compute aggregation ratio: (potential messages - actual sent) / potential
    aggregation_ratio = 0.0
    if messages_potential > 0:
        aggregation_ratio = (messages_potential - messages_sent_count) / messages_potential

    # Energy efficiency: delivered bytes per unit energy
    energy_efficiency = 0.0
    if total_energy > 0:
        energy_efficiency = total_delivered / total_energy

    return {
        "policy": policy_name,
        "steps": int(avg_steps),
        
        # Core metrics
        "avg_reward": float(total_r / max(1, avg_steps)),
        "total_reward": float(total_r),
        
        # Delivery metrics
        "delivered_bytes_total": float(total_delivered),
        "attempted_bytes_total": float(total_attempted),
        "delivery_ratio": float(total_delivered / max(1.0, total_attempted)),
        
        # Action distribution
        "hold_frac": float(holds / max(1, avg_steps)),
        "transmit_frac": float(transmissions / max(1, avg_steps)),
        "agg_decisions_frac": float(aggregated_decisions / max(1, transmissions)) if transmissions > 0 else 0.0,
        
        # Aggregation benefits
        "messages_sent": float(messages_sent_count),
        "messages_potential": float(messages_potential),
        "aggregation_ratio": float(aggregation_ratio),
        
        # Energy & deadline
        "total_energy_cost": float(total_energy),
        "energy_efficiency": float(energy_efficiency),
        "deadline_bonus_avg": float(deadline_bonuses / max(1, avg_steps)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="CSV dataset path")
    ap.add_argument("--q_table", required=True, help="Q-table (npz) path")
    ap.add_argument("--step_ms", type=int, default=10)
    ap.add_argument("--steps", type=int, default=8000)
    args = ap.parse_args()

    df = pd.read_csv(args.data, low_memory=False)
    Q = load_q_table(args.q_table)

    print("\n" + "=" * 120)
    print(f"EVALUATION: Combined RL vs FCFS Baseline")
    print(f"Dataset: {args.data.split('/')[-1]} | Steps: {args.steps}")
    print("=" * 120)

    # Evaluate both policies
    results = []
    print("\nEvaluating RL policy...")
    results.append(run_eval(df, "q", Q=Q, step_ms=args.step_ms, steps=args.steps))
    
    print("Evaluating FCFS baseline...")
    results.append(run_eval(df, "fcfs", Q=None, step_ms=args.step_ms, steps=args.steps))

    out_df = pd.DataFrame(results)
    
    # Pretty print
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 20)
    print("\n" + out_df.to_string(index=False))
    
    # Compute improvements
    rl_row = results[0]
    fcfs_row = results[1]
    
    print("\n" + "=" * 120)
    print("IMPROVEMENT: Combined RL vs FCFS")
    print("=" * 120)
    
    improvements = {
        "Metric": [
            "Avg Reward",
            "Delivery Ratio",
            "Message Aggregation Ratio",
            "Energy Efficiency (bytes/J)",
            "Deadline Compliance (bonus)",
            "Hold Fraction (conservative)",
        ],
        "RL Value": [
            f"{rl_row['avg_reward']:.4f}",
            f"{rl_row['delivery_ratio']:.4f}",
            f"{rl_row['aggregation_ratio']:.4f}",
            f"{rl_row['energy_efficiency']:.4f}",
            f"{rl_row['deadline_bonus_avg']:.4f}",
            f"{rl_row['hold_frac']:.4f}",
        ],
        "FCFS Value": [
            f"{fcfs_row['avg_reward']:.4f}",
            f"{fcfs_row['delivery_ratio']:.4f}",
            f"{fcfs_row['aggregation_ratio']:.4f}",
            f"{fcfs_row['energy_efficiency']:.4f}",
            f"{fcfs_row['deadline_bonus_avg']:.4f}",
            f"{fcfs_row['hold_frac']:.4f}",
        ],
        "Improvement": [
            f"{((rl_row['avg_reward'] - fcfs_row['avg_reward']) / max(abs(fcfs_row['avg_reward']), 1e-6) * 100):.1f}%",
            f"{((rl_row['delivery_ratio'] - fcfs_row['delivery_ratio']) * 100):.1f}pp",
            f"{((rl_row['aggregation_ratio'] - fcfs_row['aggregation_ratio']) * 100):.1f}pp",
            f"{((rl_row['energy_efficiency'] - fcfs_row['energy_efficiency']) / max(fcfs_row['energy_efficiency'], 1e-6) * 100):.1f}%",
            f"{((rl_row['deadline_bonus_avg'] - fcfs_row['deadline_bonus_avg']) / max(fcfs_row['deadline_bonus_avg'], 1e-6) * 100):.1f}%",
            f"{((rl_row['hold_frac'] - fcfs_row['hold_frac']) * 100):.1f}pp",
        ]
    }
    
    imp_df = pd.DataFrame(improvements)
    print("\n" + imp_df.to_string(index=False))
    print("\n" + "=" * 120)


if __name__ == "__main__":
    main()
