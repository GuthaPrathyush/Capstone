# Paper Draft Section: Method, Results, and Discussion

## 1. Method

### 1.1 Problem Formulation
We study UAV communication control as a joint decision problem where the transmitter must choose:

1. scheduling action (which priority queue to serve), and
2. aggregation action (how many packets to combine before transmission).

Unlike FCFS/FIFO baselines, which transmit in arrival order, our method adapts decisions to observed queue and link conditions.

### 1.2 State Representation
Each decision step is represented by a compact communication state built from ns-3 traces, including:

- queue pressure,
- urgent traffic mix,
- deadline pressure,
- channel quality (derived from packet loss and link stability).

Continuous features are discretized into buckets to support tabular Q-learning.

AoI, energy, and delivery quality remain part of the reward shaping rather than the tabular state in the current tuned model.

### 1.3 Action Space
A unified action index encodes:

- scheduling choice: `{serve_p0, serve_p1, serve_p2, hold}`,
- aggregation level: `k in {1,2,3,4,5}`.

This yields a compact joint action space while preserving the coupling between scheduling and aggregation.

### 1.4 Reward Design
We define a multi-objective shaped reward:

- positive terms: delivery/goodput and deadline-sensitive service,
- penalty terms: packet loss, queue overflow, AoI growth, and energy expenditure.

This reward reflects mission-relevant communication quality rather than throughput-only optimization.

### 1.5 Training and Tuning Strategy
The model is trained using tabular Q-learning on ns-3 generated datasets spanning balanced, congested, and constrained link conditions. During development we observed a degenerate HOLD policy in severe scenarios and introduced the following corrections:

- stronger penalties for backlog under HOLD,
- a compact state design centered on queue pressure, urgent traffic mix, deadline pressure, and channel quality,
- transition-aligned discounting (`gamma=0`) for offline action-independent next-state structure,
- unseen-seed scenario evaluation to verify robustness.

---

## 2. Experimental Setup

### 2.1 Environment and Data
All experiments use ns-3-generated UAV communication datasets with scenario control and deterministic seeds for reproducibility. We evaluate on both realistic and stress conditions, including:

- baseline/balanced links,
- energy-constrained conditions,
- high-congestion bursty traffic,
- weak-link stress.

### 2.2 Baselines
We compare against representative non-learning baselines:

- FCFS/FIFO proxy,
- serve-best-nonempty heuristic,
- hold-only policy.

### 2.3 Metrics
Reported metrics include:

- average reward (multi-objective utility),
- throughput (packets per step),
- packet loss (packets lost per step),
- delivery ratio,
- hold fraction.

---

## 3. Results

### 3.1 Primary Observation
The tuned combined policy outperforms FCFS in overall utility across realistic and congested scenarios, with strong packet-loss reduction in high-congestion settings.

Representative comparison (high-congestion focused):

- throughput gain vs FCFS: approximately +6.8%,
- packet-loss reduction vs FCFS: approximately -49.0%,
- utility gain (avg reward): improved relative to FCFS and heuristic baselines.

Across all evaluated scenarios (including stress), the proposed policy maintains better aggregate utility and lower mean packet loss than FCFS.

### 3.2 Stress-Condition Behavior
In extreme weak-link scenarios, all strategies exhibit near-zero effective delivery. Under such conditions, differences in utility arise primarily from conservative resource-aware behavior rather than throughput improvement.

---

## 4. Discussion

### 4.1 Why Combined Decisions Help
Scheduling and aggregation are tightly coupled in UAV links:

- aggressive aggregation may increase efficiency in stable links,
- the same action may worsen loss in unstable links,
- queue urgency and channel quality must be considered jointly.

The learned policy captures this coupling better than fixed-order FCFS logic. The compact state is deliberate: it keeps tabular Q-learning tractable while still carrying the key aggregation signals.

### 4.2 Practical Significance
The proposed controller provides a deployable decision core for UAV edge communication where reliability and freshness are as important as raw throughput.

### 4.3 Interpretation Caution
Absolute metric magnitudes can vary across implementations if temporal normalization differs (per-step vs per-window). Therefore, comparative claims should emphasize:

- matched-unit evaluation,
- relative improvement (%) over baselines,
- scenario-consistent reporting.

---

## 5. Limitations

1. Current implementation is dataset-driven proxy RL rather than fully closed-loop ns-3-in-the-loop learning.
2. Tabular representation can face scalability limits in larger state spaces.
3. Extremely adverse link states remain difficult for all evaluated policies.

---

## 6. Future Work

1. Closed-loop RL where actions directly influence next-state ns-3 transitions.
2. Multi-seed confidence interval reporting for final manuscript statistics.
3. Deeper function approximation (DQN/graph-aware variants) if state complexity increases.
4. Integration with full pipeline components (prioritization and rate adaptation) in an end-to-end communication stack.

---

## 7. Suggested Manuscript Claim
A concise, defensible contribution statement:

"We propose a joint scheduling-aggregation RL controller for UAV communication that improves FCFS-style handling in realistic ns-3 scenarios, yielding better multi-objective utility and substantially lower packet loss under congestion."
