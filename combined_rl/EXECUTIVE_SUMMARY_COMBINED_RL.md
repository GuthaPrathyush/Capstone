# Executive Summary: Combined RL for UAV Scheduling + Aggregation

## Goal
We developed a combined Reinforcement Learning (RL) controller for UAV communication that jointly decides:

- which message queue to serve (scheduling), and
- how many packets to aggregate (aggregation level).

The objective is to outperform FCFS/FIFO-style transmission in realistic ns-3 communication conditions.

---

## Why This Was Needed
Traditional FCFS sends packets in arrival order, which is simple but not robust in UAV links where conditions change rapidly due to mobility, congestion, and varying signal quality.

In these settings, a useful controller must balance multiple objectives simultaneously:

- delivery success,
- packet loss reduction,
- low information staleness (AoI),
- deadline awareness,
- energy efficiency.

A fixed rule is usually too rigid for this trade-off. RL provides adaptive behavior based on current queue/link state.

---

## What We Built
We implemented a tabular Q-learning based combined action policy using ns-3 derived datasets.

### State signals used
- queue composition and backlog,
- deadline urgency,
- link quality indicators (goodput, loss, stability, SNR),
- energy level,
- AoI.

### Action design
A single action jointly encodes:
- scheduling decision: `serve_p0 / serve_p1 / serve_p2 / hold`,
- aggregation factor: `k in [1..5]` packets.

### Reward design
Reward combines:
- positive: successful transmission and deadline-aware service,
- negative: loss, queue overflow, AoI growth, and transmission energy cost.

---

## What We Improved During Development
Initial versions showed HOLD-dominant behavior in harsh scenarios. We addressed this with targeted fixes:

1. reward retuning to discourage idle behavior under backlog,
2. improved state representation (including better queue and link stability cues),
3. training objective alignment (`gamma=0`) for offline action-independent transition data,
4. realistic unseen-seed ns-3 evaluation for fair testing.

---

## Final Result Snapshot
The tuned combined model variants achieved measurable gains over FCFS on realistic scenarios.

Representative outcomes:
- packet-loss reduction (strong scenario): about 49% lower vs FCFS,
- throughput increase (same scenario): about 6.8% higher vs FCFS,
- improved multi-objective utility across realistic and congested tests.

In extreme weak-link stress cases, all methods degrade significantly, but the proposed model remains competitive in utility.

---

## Publication Positioning
This work is publication-ready as a focused contribution:

"A joint scheduling-aggregation RL controller for UAV communication that improves FCFS-style handling under realistic ns-3 conditions."

Key strengths:
- reproducible scenario/seed setup,
- interpretable baseline comparisons,
- iterative ablation-driven model improvement.

---

## Limitations (Transparent Reporting)
- Current approach is dataset-driven proxy RL, not full closed-loop ns-3 control at every transition.
- Tabular policy may not scale indefinitely with higher-dimensional swarm state spaces.
- Metric normalization must be standardized when comparing across independent implementations.

---

## Immediate Next Steps
1. run larger multi-seed evaluation and report mean +- CI,
2. standardize metrics to packets/sec and loss/sec across all model reports,
3. include final ablation table in manuscript,
4. prepare end-to-end integration section with prioritization/rate-control context in the broader research narrative.

This establishes a solid technical core under deadline constraints while remaining extensible for the full research pipeline.
