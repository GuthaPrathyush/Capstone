# Combined RL Technique Rationale

## 1. Purpose of This Document
This document explains, in clear technical language, why we chose a combined RL approach for UAV message handling, how we built and improved it, what results we obtained, and where this work can go next.

The target reader is someone with engineering background who may not be deeply familiar with machine learning or UAV communication protocols.

---

## 2. Problem Context
UAV swarms continuously exchange mission data, telemetry, status, and control packets. In practical deployments, communication links are unstable due to mobility, interference, and congestion. If packet handling is poor, we see:

- delayed critical messages,
- stale data at the receiver,
- wasted battery from unnecessary retransmissions,
- high packet drops during congestion.

A common baseline in communication systems is FIFO/FCFS (First-In-First-Out / First-Come-First-Served), where packets are transmitted in arrival order with little context awareness.

This is simple but often suboptimal in UAV networks because FIFO does not directly account for:

- urgency/deadline,
- changing link quality,
- energy constraints,
- aggregation opportunities,
- data freshness (AoI).

---

## 3. Research Direction and Why This Technique
The larger research direction (from the project planning stage) includes four communication dimensions:

1. message scheduling,
2. message prioritization,
3. message rate control,
4. message aggregation.

This model addresses the scheduling + aggregation core as a combined decision block. The key reason is that in practice these two decisions are coupled:

- deciding *which* queue to serve and
- deciding *how much* to aggregate

should not be separated blindly, because one affects delay, loss, and energy behavior of the other.

### Why RL instead of fixed rules?
Rule-based methods (for example, always serve highest priority or always aggregate to k=5) are predictable but rigid. In UAV links, conditions change quickly. RL provides adaptive behavior by learning from state-dependent reward feedback.

### Why tabular Q-learning (initially)?
Given time pressure and the need for reproducibility, tabular Q-learning was selected as a fast and interpretable starting point:

- low implementation overhead,
- easy debugging,
- clear action-value interpretation,
- no heavy deep learning dependency for the first publication cycle.

---

## 4. System Model (What the Agent Sees and Does)

### 4.1 State Inputs
The model uses communication and queue indicators derived from ns-3 traces, including:

- queue length / queue pressure,
- urgent traffic mix,
- deadline urgency,
- channel quality from loss + link stability.

Continuous values are bucketed to make a finite tabular state space.

AoI, energy, and delivery quality are still used in the reward, but they are not part of the compact tabular state in the current tuned version.

### 4.2 Combined Action Space
A single action encodes two decisions:

- scheduling choice: serve P0 / P1 / P2 / HOLD,
- aggregation level: aggregate k packets, where k in [1..5].

So one action jointly controls packet selection and bundling intensity.

### 4.3 Reward Objective
Reward was designed to reflect real communication trade-offs:

- positive terms: successful delivery/goodput, deadline-sensitive service,
- negative terms: AoI growth, energy spending, loss, queue overflow.

This gives a multi-objective optimization target, closer to mission reality than throughput-only tuning.

---

## 5. Data and Experimental Environment

### 5.1 Why ns-3 Data
Public UAV datasets often lack the exact combined features needed for this decision process (queue-state + link-state + temporal behavior at required granularity). Therefore, ns-3 simulation was used to generate controlled and reproducible scenarios.

### 5.2 Scenario Design
Multiple scenarios were generated to represent different channel/traffic conditions (balanced, congestion-heavy, energy-constrained, weak-link, mobility-unstable, etc.).

This allowed:

- realistic stress testing,
- controlled train/validation/test separation,
- reproducible experiments via scenario names and random seeds.

---

## 6. How We Arrived at the Current Model
This section is important for transparency.

### 6.1 Initial Outcome
Early versions showed policy collapse toward HOLD behavior in severe scenarios. This happened because:

- many scenarios had near-zero feasible delivery,
- the reward structure made conservative non-transmission too safe,
- offline transition dynamics (next state from dataset row) limited action influence on future state.

### 6.2 Diagnosis and Corrections
We made targeted corrections rather than rewriting everything:

1. **Reward retuning**:
- stronger reward for effective transmission,
- explicit penalty for HOLD under backlog,
- adjusted penalties for loss/overflow/energy balance.

2. **State enrichment**:
- kept the state compact but more meaningful for aggregation:
	- queue pressure,
	- urgent traffic mix,
	- deadline pressure,
	- channel quality.

3. **Training objective alignment**:
- switched to gamma=0 variant for offline action-independent transitions,
- this matched the proxy environment better and improved practical policy behavior.

4. **Realistic unseen testing**:
- generated fresh-seed ns-3 datasets for fair out-of-sample comparisons.

### 6.3 Final Practical Variant
A high-performing practical policy was obtained using a hybrid gate:

- use learned RL policy generally,
- apply safe heuristic in clearly good link conditions.

This improved deployment robustness and widened the FCFS performance gap in realistic scenarios.

---

## 7. Results Summary and Interpretation

### 7.1 Main Finding
On realistic and congested scenarios, the proposed combined approach outperformed FCFS in overall utility and significantly reduced packet loss in key conditions.

### 7.2 Important Interpretation Note
Absolute values in different experiments can differ in scale because of metric normalization choices (per-step vs per-window). Therefore:

- direct comparison of raw magnitudes across independent implementations can be misleading,
- relative improvements (%) under matched metric definitions are the correct comparison basis.

### 7.3 Why This Matters
In UAV communication, throughput alone is not sufficient. A useful controller must balance:

- reliable delivery,
- low packet loss,
- low staleness (AoI),
- energy-aware transmission.

The combined RL framing directly optimizes this multi-constraint behavior.

---

## 8. Why This Approach Is Publication-Relevant
This work is publication-appropriate because it provides:

- a clear problem statement (joint scheduling + aggregation),
- a reproducible simulation setup (scenario + seed controlled),
- interpretable baseline comparisons (FCFS and heuristics),
- iterative model-improvement evidence,
- practical lessons from failure modes and fixes.

A strong paper contribution can be presented as:

"A joint scheduling-aggregation RL controller for UAV communication that improves FCFS-style handling under realistic ns-3 conditions while preserving robustness under stress links."

---

## 9. Limitations (To State Clearly)
No serious paper should hide limitations. Current constraints include:

1. Dataset-driven proxy RL, not fully closed-loop ns-3 control at every transition.
2. Tabular representation may not scale to very high-dimensional fleet state spaces.
3. Some extreme weak-link scenarios produce near-zero delivery for all methods.
4. Metric normalization must be carefully standardized before cross-team result fusion.

These limitations are normal for a first strong implementation cycle and can be turned into future-work opportunities.

---

## 10. Future Scope

### 10.1 Near-Term (Next Iteration)
1. Multi-seed statistical reporting (mean +- std/CI).
2. Unified metrics in packets/sec and loss/sec across all model variants.
3. Full ablation table:
- baseline reward vs tuned reward,
- gamma variants,
- state-feature variants.

### 10.2 Mid-Term
1. Closed-loop agent-in-the-loop ns-3 execution.
2. Integrate explicit prioritization/rate-control modules with the current combined block.
3. Introduce per-packet metadata (message type, urgency class, deadline class) for richer action control.

### 10.3 Long-Term
1. Move from tabular Q-learning to DQN / graph-aware RL where needed.
2. Validate in hardware-in-the-loop / SITL / real flight logs.
3. Build an end-to-end edge intelligence pipeline that jointly handles:
- prioritization,
- rate adaptation,
- scheduling,
- aggregation,
- integrity constraints.

---

## 11. Practical Conclusion
We chose this technique because it is the most effective balance of:

- scientific relevance,
- implementation speed under deadline pressure,
- reproducibility,
- and measurable gains over FCFS-style baselines.

The current model is not the final endpoint of the broader research vision, but it is a strong and defensible technical core that can anchor a conference-quality submission and support the next pipeline expansions.
