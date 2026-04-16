from __future__ import annotations

import argparse
import os

import matplotlib.pyplot as plt
import pandas as pd


def _pick_metric_cols(df: pd.DataFrame) -> tuple[str, str]:
    # Support both older and newer export names.
    if "throughput_pkts_per_step" in df.columns:
        throughput_col = "throughput_pkts_per_step"
    elif "throughput" in df.columns:
        throughput_col = "throughput"
    else:
        raise ValueError("Could not find throughput column in CSV")

    if "lost_pkts_per_step" in df.columns:
        loss_col = "lost_pkts_per_step"
    elif "packet_loss" in df.columns:
        loss_col = "packet_loss"
    else:
        raise ValueError("Could not find packet-loss column in CSV")

    return throughput_col, loss_col


def _extract_values(df: pd.DataFrame, throughput_col: str, loss_col: str) -> tuple[float, float, float, float]:
    fcfs = df[df["policy"].str.lower() == "fcfs"]
    proposed = df[df["policy"].str.lower() == "proposed"]
    if fcfs.empty or proposed.empty:
        raise ValueError("CSV must contain both 'FCFS' and 'Proposed' rows in 'policy' column")

    fcfs_t = float(fcfs.iloc[0][throughput_col])
    proposed_t = float(proposed.iloc[0][throughput_col])
    fcfs_l = float(fcfs.iloc[0][loss_col])
    proposed_l = float(proposed.iloc[0][loss_col])
    return fcfs_t, proposed_t, fcfs_l, proposed_l


def _draw_single(
    title: str,
    y_label: str,
    values: list[float],
    out_path: str,
    colors: list[str],
) -> None:
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    labels = ["FIFO", "Proposed"]
    bars = ax.bar(labels, values, color=colors, width=0.55, edgecolor="#333333", linewidth=1.2)

    # Add value labels on bars with better positioning
    for bar, v in zip(bars, values):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + (0.015 * max(values) if max(values) > 0 else 0.015),
            f"{v:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
            color="#000000",
            weight="normal",
            family="sans-serif",
        )

    ax.set_title(title, fontsize=13, color="#000000", pad=12, weight="bold", family="sans-serif")
    ax.set_ylabel(y_label, fontsize=11, color="#333333", family="sans-serif")
    ax.set_xlabel("Policy", fontsize=11, color="#333333", family="sans-serif")
    ax.tick_params(axis="x", colors="#333333", labelsize=10)
    ax.tick_params(axis="y", colors="#333333", labelsize=10)
    ax.grid(axis="y", color="#cccccc", linestyle="-", linewidth=0.7, alpha=0.3)

    # Remove top and right spines for cleaner look
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#333333")
    ax.spines["bottom"].set_color("#333333")

    plt.tight_layout()
    plt.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight", dpi=300)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description="Plot FCFS vs Proposed comparison charts")
    ap.add_argument("--csv", required=True, help="Input CSV with policy + metric columns")
    ap.add_argument("--out_dir", required=True, help="Output directory for PNG graphs")
    ap.add_argument("--tag", default="comparison", help="Tag prefix for generated image names")
    ap.add_argument("--title_suffix", default="", help="Optional text appended to chart titles")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    df = pd.read_csv(args.csv)

    throughput_col, loss_col = _pick_metric_cols(df)
    fcfs_t, proposed_t, fcfs_l, proposed_l = _extract_values(df, throughput_col, loss_col)

    suffix = f" ({args.title_suffix})" if args.title_suffix else ""

    out_t = os.path.join(args.out_dir, f"{args.tag}_throughput.png")
    out_l = os.path.join(args.out_dir, f"{args.tag}_packet_loss.png")

    # Research paper grade colors: muted gray and professional blue
    colors_baseline = "#7a8fa3"  # Professional gray for FIFO baseline
    colors_proposed = "#2b5f99"  # Professional blue for proposed method

    _draw_single(
        title=f"Throughput Comparison{suffix}",
        y_label="Throughput (packets/step)",
        values=[fcfs_t, proposed_t],
        out_path=out_t,
        colors=[colors_baseline, colors_proposed],
    )

    _draw_single(
        title=f"Packet Loss Comparison{suffix}",
        y_label="Packet Loss (packets/step)",
        values=[fcfs_l, proposed_l],
        out_path=out_l,
        colors=[colors_baseline, colors_proposed],
    )

    print("Generated graphs:")
    print(out_t)
    print(out_l)


if __name__ == "__main__":
    main()
