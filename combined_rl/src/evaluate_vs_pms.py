"""Evaluate RL vs paper-style baseline on throughput and packet-loss ratio."""

from __future__ import annotations

import argparse
import os
from typing import Dict, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .env import CombinedActions, CombinedRewardWeights, transmission_model
from .train_qlearning import state_key


def load_q_table(path: str) -> Dict[Tuple[int, ...], np.ndarray]:
    z = np.load(path)
    keys = z["keys"]
    values = z["values"]
    q: Dict[Tuple[int, ...], np.ndarray] = {}
    for i in range(keys.shape[0]):
        q[tuple(int(x) for x in keys[i])] = values[i].astype(np.float32)
    return q


def policy_q(q_table: Dict[Tuple[int, ...], np.ndarray], s: Tuple[int, ...]) -> int:
    """RL policy: argmax Q(s,a)."""
    if s not in q_table:
        return CombinedActions.encode(CombinedActions.HOLD, 1)
    return int(np.argmax(q_table[s]))


def _apply_safe_aggregation_guard(action: int, row: pd.Series, step_ms: int) -> int:
    """Clamp aggregation size under weak channel conditions.

    This is a deployment-style safety layer: keep the RL scheduling choice, but
    reduce agg_k when loss risk is high so the policy does not over-attempt
    bytes that are unlikely to be delivered.
    """
    schedule_choice, agg_k = CombinedActions.decode(action)
    if schedule_choice == CombinedActions.HOLD:
        return action

    loss = float(np.clip(row.get("packet_loss_rate", 0.0), 0.0, 1.0))
    stability = float(np.clip(row.get("link_stability", 0.0), 0.0, 1.0))
    packet_size = float(max(1.0, row.get("packet_size", 1.0)))
    goodput_kbps = float(max(0.0, row.get("goodput_kbps", 0.0)))

    # Capacity-aware cap: avoid choosing aggregation sizes that consistently
    # exceed what the channel can deliver in this step.
    step_s = max(1e-6, float(step_ms) / 1000.0)
    cap_bytes = goodput_kbps * 1000.0 / 8.0 * step_s
    cap_k = int(np.floor(cap_bytes / packet_size)) if packet_size > 0 else CombinedActions.AGG_K_MAX
    cap_k = int(np.clip(cap_k, 1, CombinedActions.AGG_K_MAX))

    max_k = CombinedActions.AGG_K_MAX
    if loss >= 0.25 or stability <= 0.65:
        max_k = 1
    elif loss >= 0.15 or stability <= 0.75:
        max_k = 2
    elif loss >= 0.08 or stability <= 0.85:
        max_k = 3

    return CombinedActions.encode(schedule_choice, min(agg_k, max_k, cap_k))


def _clip01(x: float) -> float:
    return float(np.clip(x, 0.0, 1.0))


def _paper_priority_score(
    *,
    queue_idx: int,
    row: pd.Series,
) -> float:
    """Approximate the paper's priority assignment with snapshot-level features.

    The paper assigns priority from message content, message size, and dynamic
    context factors. Our dataset only exposes row-level aggregates, so we map
    those ideas to the available signals:
    - priority column: content/importance hint
    - packet_size: smaller packets are cheaper to push through the channel
    - min_deadline: tighter deadline => higher urgency
    - packet_loss_rate + link_stability: channel context
    """
    packet_size = float(row.get("packet_size", 0.0))
    min_deadline = float(row.get("min_deadline", 0.0))
    packet_loss_rate = _clip01(float(row.get("packet_loss_rate", 0.0)))
    link_stability = _clip01(float(row.get("link_stability", 0.0)))

    # Content hint from the dataset, treated as a coarse priority indicator.
    content_hint = int(row.get("priority", queue_idx))
    content_score = 1.0 if content_hint == queue_idx else 0.0

    # Paper-style dynamic factors.
    urgency_score = 1.0 / (1.0 + max(0.0, min_deadline))
    channel_score = 0.5 * (1.0 - packet_loss_rate) + 0.5 * link_stability
    size_score = 1.0 - _clip01(packet_size / 1500.0)

    # Base class ordering: higher queue index is more urgent in our project.
    class_bias = {0: 0.25, 1: 0.55, 2: 0.85}.get(queue_idx, 0.25)

    return (
        class_bias
        + 0.35 * content_score
        + 0.20 * urgency_score
        + 0.15 * channel_score
        + 0.05 * size_score
    )


def policy_paper_baseline(r0: pd.Series) -> int:
    """Paper-style PMS baseline: priority-driven scheduling with no aggregation.

    The scheduler chooses the highest-scoring non-empty queue and uses agg_k=1
    to keep the baseline focused on prioritization rather than aggregation.
    """
    q = [int(r0.get("q_p0_pkts", 0)), int(r0.get("q_p1_pkts", 0)), int(r0.get("q_p2_pkts", 0))]
    if sum(q) <= 0:
        return CombinedActions.encode(CombinedActions.HOLD, 1)

    scores: list[float] = []
    for idx in range(3):
        if q[idx] <= 0:
            scores.append(float("-inf"))
        else:
            scores.append(_paper_priority_score(queue_idx=idx, row=r0))

    best_idx = int(np.argmax(scores))
    return CombinedActions.encode(best_idx, 1)


def _policy_name_to_action(policy_name: str, row: pd.Series, q_table=None, step_ms: int = 10) -> int:
    if policy_name == "q":
        if q_table is None:
            raise ValueError("Q-table is required for RL policy")
        raw_action = policy_q(q_table, state_key(row))
        return _apply_safe_aggregation_guard(raw_action, row, step_ms)
    if policy_name == "paper":
        return policy_paper_baseline(row)
    raise ValueError(f"Unknown policy: {policy_name}")


def run_eval(
    df: pd.DataFrame,
    policy_name: str,
    q_table=None,
    step_ms: int = 10,
    steps: int = 8000,
) -> dict:
    """Run evaluation and return throughput + packet-loss ratio metrics."""
    w = CombinedRewardWeights()
    total_delivered = 0.0
    total_attempted = 0.0
    total_loss_ratio_sampled = 0.0

    for i in range(min(steps, len(df) - 2)):
        r0 = df.iloc[i]
        a = _policy_name_to_action(policy_name, r0, q_table=q_table, step_ms=step_ms)

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

        _ = r
        total_delivered += float(info["delivered_bytes"])
        total_attempted += float(info["attempted_bytes"])
        total_loss_ratio_sampled += float(np.clip(r0.get("packet_loss_rate", 0.0), 0.0, 1.0))

    avg_steps = min(steps, len(df) - 2)

    step_s = max(1e-6, float(step_ms) / 1000.0)
    throughput_kbps = (total_delivered * 8.0 / 1000.0) / max(step_s * avg_steps, 1e-6)
    packet_loss_ratio = (total_attempted - total_delivered) / max(total_attempted, 1.0)
    avg_input_packet_loss_rate = total_loss_ratio_sampled / max(1, avg_steps)

    return {
        "policy": policy_name,
        "steps": int(avg_steps),
        "throughput_kbps": float(throughput_kbps),
        "packet_loss_ratio": float(packet_loss_ratio),
        "avg_input_packet_loss_rate": float(avg_input_packet_loss_rate),
        "delivered_bytes_total": float(total_delivered),
        "attempted_bytes_total": float(total_attempted),
    }


def _plot_bar_metric(
    results: list[dict],
    metric_key: str,
    title: str,
    y_label: str,
    out_path: str,
    colors: list[str],
) -> None:
    labels = ["RL", "Paper Baseline"]
    values = [float(results[0][metric_key]), float(results[1][metric_key])]

    fig, ax = plt.subplots(figsize=(7.6, 5.2), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    bars = ax.bar(labels, values, color=colors, width=0.55, edgecolor="#333333", linewidth=1.1)

    vmax = max(values) if values else 0.0
    for bar, v in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            v + (0.015 * vmax if vmax > 0 else 0.015),
            f"{v:.4f}",
            ha="center",
            va="bottom",
            fontsize=10,
            color="#000000",
        )

    ax.set_title(title, fontsize=13, color="#000000", pad=12, weight="bold", family="sans-serif")
    ax.set_ylabel(y_label, fontsize=11, color="#333333", family="sans-serif")
    ax.tick_params(axis="x", colors="#333333", labelsize=10)
    ax.tick_params(axis="y", colors="#333333", labelsize=10)
    ax.grid(axis="y", color="#cccccc", linestyle="-", linewidth=0.7, alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333333")
    ax.spines["bottom"].set_color("#333333")

    plt.tight_layout()
    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight", dpi=300)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="CSV dataset path")
    ap.add_argument("--q_table", required=True, help="Q-table (npz) path")
    ap.add_argument("--out_dir", required=True, help="Output directory for graphs and summary CSV")
    ap.add_argument("--step_ms", type=int, default=10)
    ap.add_argument("--steps", type=int, default=8000)
    ap.add_argument("--tag", default="paper_vs_rl", help="File prefix for generated outputs")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    df = pd.read_csv(args.data, low_memory=False)
    q_table = load_q_table(args.q_table)

    print("\n" + "=" * 120)
    print("EVALUATION: Throughput and Packet-Loss Ratio (RL vs Paper Baseline)")
    print(f"Dataset: {args.data.split('/')[-1]} | Steps: {args.steps}")
    print("=" * 120)

    results: list[dict] = []
    print("\nEvaluating RL policy...")
    results.append(run_eval(df, "q", q_table=q_table, step_ms=args.step_ms, steps=args.steps))

    print("Evaluating paper-style baseline...")
    results.append(run_eval(df, "paper", q_table=None, step_ms=args.step_ms, steps=args.steps))

    out_df = pd.DataFrame(results)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 30)
    print("\n" + out_df.to_string(index=False))

    rl_row = results[0]
    paper_row = results[1]

    print("\n" + "=" * 120)
    print("IMPROVEMENT: RL vs Paper Baseline")
    print("=" * 120)

    throughput_delta_pct = ((rl_row["throughput_kbps"] - paper_row["throughput_kbps"]) / max(paper_row["throughput_kbps"], 1e-6)) * 100.0
    loss_delta_pp = (rl_row["packet_loss_ratio"] - paper_row["packet_loss_ratio"]) * 100.0
    print(f"Throughput change: {throughput_delta_pct:.2f}%")
    print(f"Packet-loss-ratio change: {loss_delta_pp:.2f}pp")

    summary_csv = os.path.join(args.out_dir, f"{args.tag}_throughput_loss_summary.csv")
    out_df.to_csv(summary_csv, index=False)

    colors = ["#2b5f99", "#7a8fa3"]
    metric_specs = [
        ("throughput_kbps", "Throughput Comparison", "Throughput (kbps)", f"{args.tag}_throughput_kbps.png"),
        ("packet_loss_ratio", "Packet Loss Ratio Comparison", "Packet Loss Ratio", f"{args.tag}_packet_loss_ratio.png"),
    ]

    generated = [summary_csv]
    for metric_key, title, y_label, filename in metric_specs:
        out_path = os.path.join(args.out_dir, filename)
        _plot_bar_metric(results, metric_key, title, y_label, out_path, colors)
        generated.append(out_path)

    print("\nGenerated files:")
    for p in generated:
        print(p)
    print("\n" + "=" * 120)


if __name__ == "__main__":
    main()