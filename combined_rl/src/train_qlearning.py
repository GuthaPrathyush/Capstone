from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

from .env import CombinedActions, CombinedRewardWeights, transmission_model


@dataclass
class TrainConfig:
    data_path: str
    out_dir: str
    episodes: int
    alpha: float
    gamma: float
    eps: float
    max_steps: int
    step_ms: int


def _load(path: str) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def _bucket(x: float, edges: List[float]) -> int:
    for i, e in enumerate(edges):
        if x <= e:
            return i
    return len(edges)


def state_key(r: pd.Series) -> Tuple[int, ...]:
    """
    Compact state for tabular Q-learning (buckets).
    Focuses on the most important signals for aggregation decisions:
    queue pressure, priority mix, deadline urgency, and channel quality.
    """
    q_len = float(r.get("queue_length", 0.0))
    q_p2 = float(r.get("q_p2_pkts", 0.0))
    q_p1 = float(r.get("q_p1_pkts", 0.0))
    urgent_frac = ((q_p1 + q_p2) / max(1.0, q_len))

    min_deadline = float(r.get("min_deadline", 0.0))
    loss = float(r.get("packet_loss_rate", 0.0))
    stability = float(r.get("link_stability", 0.0))

    # Deadline urgency: smaller deadlines should map to a larger bucket signal.
    deadline_pressure = 1.0 / (1.0 + max(0.0, min_deadline))

    # Combine loss and stability into a single channel-quality view.
    channel_quality = 0.5 * (1.0 - float(np.clip(loss, 0.0, 1.0))) + 0.5 * float(np.clip(stability, 0.0, 1.0))

    return (
        _bucket(q_len, [0, 2, 5, 10, 20, 40]),
        _bucket(urgent_frac, [0.0, 0.05, 0.15, 0.35, 0.6, 0.85, 1.0]),
        _bucket(deadline_pressure, [0.0, 0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0]),
        _bucket(channel_quality, [0.0, 0.25, 0.45, 0.6, 0.75, 0.9, 1.0]),
    )


def train(cfg: TrainConfig) -> str:
    os.makedirs(cfg.out_dir, exist_ok=True)
    rng = np.random.default_rng(7)
    df = _load(cfg.data_path)

    required = {
        "queue_length",
        "q_p0_pkts",
        "q_p1_pkts",
        "q_p2_pkts",
        "packet_size",
        "min_deadline",
        "packet_loss_rate",
        "link_stability",
    }
    missing = sorted([c for c in required if c not in df.columns])
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")

    Q: Dict[Tuple[int, ...], np.ndarray] = {}
    w = CombinedRewardWeights()

    n_actions = CombinedActions.n()

    for ep in range(cfg.episodes):
        # choose a start point, ensure we have room for max_steps
        start = int(rng.integers(0, max(1, len(df) - (cfg.max_steps + 2))))
        total_r = 0.0

        for t in tqdm(range(cfg.max_steps), desc=f"episode {ep+1}/{cfg.episodes}", leave=False):
            idx = start + t
            r0 = df.iloc[idx]
            s = state_key(r0)
            if s not in Q:
                Q[s] = np.zeros((n_actions,), dtype=np.float32)

            # epsilon-greedy
            if rng.random() < cfg.eps:
                a = int(rng.integers(0, n_actions))
            else:
                a = int(np.argmax(Q[s]))

            # Reward proxy based on current row
            r, _info = transmission_model(
                step_ms=cfg.step_ms,
                q_p0=int(r0.get("q_p0_pkts", 0)),
                q_p1=int(r0.get("q_p1_pkts", 0)),
                q_p2=int(r0.get("q_p2_pkts", 0)),
                packet_size=float(r0.get("packet_size", 0.0)),
                min_deadline=float(r0.get("min_deadline", 0.0)),
                mean_deadline=float(r0.get("mean_deadline", r0.get("min_deadline", 0.0))),
                goodput_kbps=float(r0.get("goodput_kbps", 0.0)),
                packet_loss_rate=float(r0.get("packet_loss_rate", 0.0)),
                link_stability=float(r0.get("link_stability", 0.0)),
                aoi_ms=float(r0.get("aoi_ms", 0.0)),
                energy_level=float(r0.get("energy_level", 0.0)),
                action=a,
                w=w,
            )
            total_r += float(r)

            # Next state
            r1 = df.iloc[idx + 1]
            sp = state_key(r1)
            if sp not in Q:
                Q[sp] = np.zeros((n_actions,), dtype=np.float32)

            td_target = float(r) + cfg.gamma * float(Q[sp].max())
            Q[s][a] = (1.0 - cfg.alpha) * Q[s][a] + cfg.alpha * td_target

        if (ep + 1) % max(1, cfg.episodes // 5) == 0:
            print(f"episode {ep+1}/{cfg.episodes} avg_reward_per_step={total_r / max(1, cfg.max_steps):.4f}")

    out = os.path.join(cfg.out_dir, "q_table_combined.npz")
    keys = np.array(list(Q.keys()), dtype=np.int32)
    vals = np.stack([Q[k] for k in Q.keys()], axis=0).astype(np.float32)
    np.savez_compressed(out, keys=keys, values=vals)
    print(f"Saved Q-table to {out}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--episodes", type=int, default=40)
    ap.add_argument("--alpha", type=float, default=0.25)
    ap.add_argument("--gamma", type=float, default=0.95)
    ap.add_argument("--eps", type=float, default=0.2)
    ap.add_argument("--max_steps", type=int, default=4000)
    ap.add_argument("--step_ms", type=int, default=10)
    args = ap.parse_args()

    cfg = TrainConfig(
        data_path=args.data,
        out_dir=args.out_dir,
        episodes=args.episodes,
        alpha=args.alpha,
        gamma=args.gamma,
        eps=args.eps,
        max_steps=args.max_steps,
        step_ms=args.step_ms,
    )
    train(cfg)


if __name__ == "__main__":
    main()

