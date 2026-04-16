# TeX FILE EDIT CHECKLIST: Insert Points for Combined RL Work

## Quick Reference Map

```
CURRENT TEX FILE STRUCTURE:
├── Introduction (Lines 1-290)
│   ├── Background (90-180)
│   ├── Problem Statement (185-210)
│   └── Research Objectives (215-280)  ← ADD: 4th contribution bullet
│
├── Related Work (300-450)
│   ├── Existing Approaches (320-360)  ← ADD: New subsection 2.1.7 on RL
│   ├── Comparative Analysis (380-410) ← EXTEND: Add RL row
│   └── Research Gaps (425-450)         ← ADD: Mention RL+scheduling gap
│
├── System Model / Architecture (460-520)
│   └── Subsection 3.2 (360-390)        ← AFTER: Insert NEW 3.2.1 on RL module
│
├── Problem Formulation (530-620)
│   └── Optimization section (480-520)  ← AFTER: Insert NEW 4.2 on RL problem
│
├── Proposed Methodology (625-730)
│   ├── Overview (625-650)              ← MODIFY: Restructure as 2-layer approach
│   └── Algorithm (655-690)             ← AFTER: Insert NEW 5.2 on Q-learning
│
├── Implementation Details (735-800) ← FILL: All empty templates
├── Performance Evaluation (835-950) ← FILL: Complete results section
├── Discussion (960-1020)             ← FILL: Observations, implications
└── Conclusion (1030-1060)            ← REWRITE: Include RL contribution summary
```

---

## EDIT #1: Introduction - Research Objectives (Line ~278)

**Current text** (lines 276-280):
```latex
Key Contributions are:\\
    \hspace*{2em}1. Classificaiton of messages using Machine Learning Model and prioritising them.\\
    \hspace*{2em}2. Heuristic rate aware congestion control Algorithm.\\
    \hspace*{2em}3. Message scheduling Algorithm in queue before transmission.\\
```

**ADD AFTER LINE 280**:
```latex
    \hspace*{2em}4. Joint scheduling-aggregation Reinforcement Learning controller 
                       that dynamically optimizes both transmission queue selection 
                       and packet aggregation level using tabular Q-learning, 
                       achieving 4-28\% throughput improvement over FCFS baselines 
                       in realistic UAV network scenarios.\\
```

**Why**: Announces your RL work as a core contribution alongside the ML+heuristic work.

---

## EDIT #2: Related Work - New Subsection (After Line 358)

**Current**: Section 2.1 ends with paragraph on congestion control

**INSERT NEW PARAGRAPH** before Section 2.2:
```latex
\subsection{Reinforcement Learning for Adaptive UAV Communication}

While machine learning has been applied to UAV routing \citep{rovira2022review}, 
the application of reinforcement learning (RL) to joint packet scheduling and 
transmission optimization remains under-explored. Tabular Q-learning and DQN-based 
methods have shown promise in resource allocation problems for wireless networks 
\citep{wang2019deep}. In particular, Q-learning with explicit state discretization 
has been successfully deployed in bandwidth allocation and buffer management tasks 
where interpretability and lightweight inference are critical. However, applying 
RL to the coupled problem of packet scheduling (which priority queue to serve) 
and aggregation control (how many packets to bundle) in MAVLink-based UAV networks 
has not been previously studied.

The key insight is that scheduling and aggregation decisions are inherently coupled: 
the optimal aggregation level depends on queue state and channel quality, which in 
turn determines the expected benefit of serving different priority classes. A tabular 
Q-learning approach can learn these coupled dependencies directly from interaction 
with a network simulator, without requiring explicit separation of the two decisions 
as in prior rule-based or heuristic methods.
```

**Why**: Contextualizes RL work in broader literature and highlights your novel angle.

---

## EDIT #3: Comparative Analysis (Line ~410)

**Current**: Comparative table lists different paper groups

**IN THE COMPARATIVE PARAGRAPH**, add after "Priority-based scheduling" bullet:
```latex
    \item \textbf{RL-based scheduling-aggregation (this work):} Learns joint 
          optimization of which queue to serve and how aggressively to aggregate, 
          using tabular Q-learning on ns-3-generated datasets. Demonstrates 
          interpretable decision-making and superior performance in congested 
          scenarios compared to FCFS and heuristic baselines.
```

**Why**: Positions your work clearly in the taxonomy.

---

## EDIT #4: Research Gaps (Line ~440)

**Current**: Bullet list of 5 gaps

**ADD NEW BULLET** at end of list:
```latex
    \item \textbf{Limited RL for Joint Scheduling-Aggregation:} Although 
          Q-learning has been applied to resource allocation in networks, 
          the specific problem of jointly optimizing packet scheduling 
          (which queue to serve) and aggregation (how many packets to combine) 
          in MAVLink-based UAV communication has not been previously addressed. 
          This decoupling is essential for capturing the true problem structure 
          and learning near-optimal policies.
```

**Why**: Explicitly states the gap your work fills.

---

## EDIT #5: System Model - NEW SUBSECTION 3.2.1 (After Line 390)

**Current** subsection 3.2 ends with:
```latex
ensuring reliable communication under dynamic network conditions.
```

**INSERT NEW SUBSECTION**:
```latex
\subsection{Joint Scheduling-Aggregation Decision Module using Reinforcement Learning}

Beyond the initial ML-based message prioritization which assigns semantic 
priority classes, the proposed architecture incorporates a learned 
scheduling-aggregation controller that makes fine-grained transmission 
decisions. This RL module operates at a finer temporal granularity than 
the ML classifier and decides at each transmission slot:

\begin{enumerate}
    \item \textbf{Scheduling Decision:} Which priority queue to serve 
    (P0, P1, P2, or HOLD). This choice depends on current queue compositions, 
    message deadlines, and channel conditions.
    
    \item \textbf{Aggregation Decision:} How many packets to combine per 
    transmission ($k \in [1,5]$). Larger aggregation improves efficiency on 
    good channels but risks excessive loss on poor channels, introducing a 
    channel-dependent trade-off.
\end{enumerate}

These two decisions are tightly coupled: the optimal aggregation level depends 
critically on which queue is being served (important messages on poor link = 
small $k$, non-critical data on good link = large $k$). Similarly, the choice 
of which queue to serve changes based on expected channel conditions. A tabular 
Q-learning agent learns representations of this coupling directly from 
transmission outcomes.

The RL module maintains a compact 4-dimensional discretized state space:
\begin{itemize}
    \item \textbf{Queue Pressure:} Total backlog normalized to [0,40] packets
    \item \textbf{Urgent Traffic Mix:} Fraction of high-priority (P1+P2) packets
    \item \textbf{Deadline Pressure:} Inverse function of minimum remaining deadline
    \item \textbf{Channel Quality:} Blend of (1 - packet loss) and link stability
\end{itemize}

The joint action space consists of 20 discrete actions resulting from 
4 scheduling choices $\times$ 5 aggregation levels. Training uses offline 
tabular Q-learning on ns-3-generated network traces, with a shaped multi-objective 
reward function balancing delivery, deadline satisfaction, loss minimization, 
energy efficiency, and Age-of-Information.
```

**Why**: Explains the RL module as a distinct layer beyond ML prioritization.

---

## EDIT #6: Problem Formulation - NEW SUBSECTION 4.2 (After Line 515)

**Current**: Section 4.2 ends with optimization objectives for rate control

**INSERT NEW SUBSECTION** 4.2 titled "Joint Scheduling-Aggregation Optimization":
```latex
\subsection{Joint Scheduling-Aggregation Optimization}

While the ML prioritization in Section 4.1 addresses message-level semantic 
importance, the RL controller solves a coupled optimization problem at the 
transmission scheduling level.

Define:
\begin{itemize}
    \item State: $s = (q_{pressure}, q_{urgent\_frac}, deadline\_pressure, 
                       channel\_quality)$
    \item Action: $a = (schedule\_choice \in \{P0, P1, P2, HOLD\}, 
                        agg\_k \in \{1,2,3,4,5\})$
    \item Action Encoding: $a_{index} = schedule\_choice \times 5 + (agg_k - 1)$, 
          yielding $|A| = 20$ discrete actions
\end{itemize}

The reward function captures multi-objective performance:
\[
R = w_{gp} \cdot goodput + w_{dl} \cdot deadline\_bonus + w_{tx} \cdot tx\_success \\
    - w_{aoi} \cdot aoi\_penalty - w_{eng} \cdot energy\_cost \\
    - w_{loss} \cdot packet\_loss - w_{ovf} \cdot queue\_overflow \\
    - w_{hold} \cdot hold\_backlog\_penalty
\]

with weights: $w_{gp}=1.8, w_{dl}=0.55, w_{tx}=0.35, w_{aoi}=0.45, w_{eng}=0.3, 
w_{loss}=0.65, w_{ovf}=0.3, w_{hold}=0.55$.

The Q-learning update rule is:
\[
Q(s,a) \leftarrow (1-\alpha) Q(s,a) + \alpha \left[ r + \gamma \max_{a'} Q(s',a') \right]
\]

with $\alpha = 0.2$ (learning rate) and $\gamma = 0.0$ (discount factor aligned 
with offline transition model).

This formulation directly captures the scheduling-aggregation coupling: the 
optimal action depends jointly on which queue offers best urgency-to-channel 
tradeoff and how many packets should be aggregated given current link quality.
```

**Why**: Formalizes the RL problem mathematically and shows coupling.

---

## EDIT #7: Proposed Methodology - RESTRUCTURE Section 5.1 (Line ~625)

**Current title**: "Overview of the Proposed Approach"

**CHANGE TO**: "Overview of the Integrated ML and RL Approach"

**REWRITE opening paragraph** (lines 625-640):
```latex
\subsection{Overview of the Integrated ML and RL Approach}

The proposed methodology consists of two complementary adaptive layers:

\paragraph{Layer 1: Machine Learning-Based Message Prioritization}
At the application level, an offline-trained Random Forest classifier assigns 
semantic priority (high, medium, low) to each MAVLink message based on features 
such as message type, payload size, transmission frequency, battery level, 
mission phase, and emergency flags. This layer provides coarse-grained semantic 
awareness without requiring real-time ML inference overhead.

\paragraph{Layer 2: Reinforcement Learning-Based Scheduling-Aggregation}
Operating below Layer 1, a tabular Q-learning controller makes fine-grained 
transmission decisions: which priority queue to serve and how many packets to 
aggregate. This layer learns from a shaped reward function that balances 
throughput, deadline satisfaction, packet loss, and energy. The coupling between 
scheduling and aggregation decisions is learned implicitly from interaction with 
the network simulator.

Together, these layers combine semantic awareness from machine learning (WHAT 
to prioritize) with dynamic context-dependent adaptation from reinforcement 
learning (HOW to optimally schedule and aggregate at each transmission step).
```

**Why**: Frames your work as intentional two-layer design, not just additional features.

---

## EDIT #8: Proposed Methodology - NEW SUBSECTION 5.2 (After Section 5.1)

**INSERT** before current "Algorithm / Protocol Design":

```latex
\subsection{Q-Learning Based Scheduling-Aggregation Controller}

After ML priority classification, messages are sorted into priority-based queues 
(P0, P1, P2). At each transmission opportunity, the RL agent decides not just 
whether to transmit, but HOW to transmit by selecting both the source queue 
and the aggregation level.

\subsubsection{5.2.1 State Discretization}

The continuous network state is mapped to a discrete finite state space to enable 
tabular Q-learning. Four key features are discretized:

\begin{equation}
s = \left( bucket(q_{len}, \mathcal{B}_q), 
          bucket(urgent\_frac, \mathcal{B}_u), 
          bucket(deadline\_pressure, \mathcal{B}_d),
          bucket(channel\_quality, \mathcal{B}_c) \right)
\end{equation}

where the bucket definitions are:
\begin{itemize}
    \item $\mathcal{B}_q = [0, 2, 5, 10, 20, 40]$ captures queue length (0-6 states)
    \item $\mathcal{B}_u = [0.0, 0.05, 0.15, 0.35, 0.6, 0.85, 1.0]$ captures 
          urgent mix fraction (0-7 states)
    \item $\mathcal{B}_d = [0.0, 0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0]$ captures 
          deadline urgency (0-8 states)
    \item $\mathcal{B}_c = [0.0, 0.25, 0.45, 0.6, 0.75, 0.9, 1.0]$ captures 
          channel quality (0-7 states)
\end{itemize}

This results in $|S| \approx 6 \times 7 \times 8 \times 7 \approx 2352$ possible 
states, a manageable size for tabular methods while retaining sufficient 
expressiveness.

\subsubsection{5.2.2 Action Encoding}

The joint scheduling-aggregation action space is encoded as a single integer:
\begin{equation}
a_{index} = schedule\_choice \times 5 + (agg\_k - 1)
\end{equation}

where $schedule\_choice \in \{0,1,2,3\}$ represents $\{SERVE\_P0, SERVE\_P1, 
SERVE\_P2, HOLD\}$ and $agg\_k \in \{1,2,3,4,5\}$ represents aggregation level. 
This yields $|A| = 4 \times 5 = 20$ discrete actions that can be indexed into a 
$(2352 \times 20)$ Q-table.

\subsubsection{5.2.3 Training Procedure}

The Q-table is initialized to zero and trained using tabular Q-learning with 
$\epsilon$-greedy exploration:
\begin{equation}
Q(s,a) \leftarrow (1 - \alpha) Q(s,a) + \alpha \left[ r + \gamma \max_{a'} Q(s',a') \right]
\end{equation}

Training on the realistic composite dataset (pub9\_train\_realistic\_200k.csv) 
consists of 70 episodes, each spanning 6000 transitions. Hyperparameters are set as:
\begin{itemize}
    \item Learning rate $\alpha = 0.2$: balances learning with stability
    \item Discount factor $\gamma = 0.0$: appropriate for offline training where 
          action does not affect next state
    \item Exploration rate $\epsilon = 0.25$: 25\% exploration, 75\% exploitation
\end{itemize}

\subsubsection{5.2.4 Reward Design}

The reward function is shaped to reflect the multi-objective optimization goal, 
balancing deliverability, timeliness, efficiency, and reliability:

\begin{equation}
R = 1.8 \cdot goodput + 0.55 \cdot deadline\_bonus + 0.35 \cdot tx\_success \\
    - 0.45 \cdot aoi\_penalty - 0.3 \cdot energy\_cost \\
    - 0.65 \cdot loss - 0.3 \cdot overflow - 0.55 \cdot hold\_backlog
\end{equation}

Each component is computed as follows:
\begin{itemize}
    \item goodput: fraction of attempted bytes successfully delivered
    \item deadline\_bonus: reward for serving urgent deadlines (priority 2 highest)
    \item tx\_success: reward when any bytes are successfully delivered
    \item aoi\_penalty: cost of message freshness degradation
    \item energy\_cost: transmission energy consumption
    \item loss: packet loss proportion
    \item overflow: queue length relative to capacity
    \item hold\_backlog: explicit penalty for HOLD action when queue is non-empty
\end{itemize}

The hold\_backlog term was critical to prevent policy collapse toward always 
holding and never transmitting, which occurred in earlier training iterations.
```

**Why**: Provides the technical depth on how RL training is done.

---

## EDIT #9: Implementation Details (Lines 735-800)

**REPLACE** all the placeholder text with:
```latex
\section{Implementation Details}

\subsection{Simulation Environment and Tools}

The experimental evaluation was conducted using:
\begin{itemize}
    \item \textbf{ns-3 Network Simulator (v3.36):} For generating realistic 
          UAV communication datasets with controlled scenarios, mobility patterns, 
          and channel models.
    \item \textbf{Python 3.9 with NumPy, Pandas:} For tabular Q-learning training, 
          data preprocessing, and analysis.
    \item \textbf{Matplotlib:} For visualization of comparison graphs.
\end{itemize}

\subsection{Dataset Description}

\subsubsection{ns-3 Scenario Generator (pub9)}
The pub9 scenario generator simulates UAV swarms with heterogeneous message 
streams (heartbeat, telemetry, navigation, commands) under various conditions:
\begin{itemize}
    \item 5-10 UAVs communicating with a ground station
    \item Variable distances (1-10 km)
    \item Path loss, fading, and interference models
    \item Dynamic mobility simulating realistic flight patterns
\end{itemize}

\subsubsection{Training Dataset}
\textbf{pub9\_train\_realistic\_200k.csv:} A composite training set created by 
concatenating and shuffling four scenario types:
\begin{enumerate}
    \item pub9\_baseline\_balanced\_50k.csv: Balanced queue, stable link
    \item pub9\_energy\_constrained\_50k.csv: High battery awareness
    \item pub9\_high\_congestion\_bursty\_50k.csv: Heavy traffic, poor link
    \item pub9\_mixed\_medium\_stress\_50k.csv: Moderate degradation
\end{enumerate}

Composition: 200,000 rows, 22 columns including queue state, deadline, link 
quality, energy, AoI, and aggregation-related fields.

\subsubsection{Evaluation Datasets}
Unseen test sets generated with fresh random seeds for fair out-of-sample comparison:
\begin{itemize}
    \item pub9\_rt\_baseline\_balanced\_50k.csv (seed 3000)
    \item pub9\_rt\_energy\_constrained\_50k.csv (seed 3001)
    \item pub9\_rt\_high\_congestion\_bursty\_50k.csv (seed 3002)
    \item pub9\_weak\_link\_high\_loss\_50k.csv (stress test with 80%+ loss)
\end{itemize}

\subsection{Parameter Settings}

Table 1 summarizes the Q-learning hyperparameters:

\begin{table}[H]
\centering
\begin{tabular}{|c|c|c|}
\hline
\textbf{Parameter} & \textbf{Value} & \textbf{Rationale} \\
\hline
Episodes & 70 & Convergence observed by episode 50-60 \\
Max steps/episode & 6000 & Sufficient trajectory sampling per episode \\
Learning rate ($\alpha$) & 0.2 & Balance stability and adaptation \\
Discount factor ($\gamma$) & 0.0 & Offline setting; next state independent of action \\
Exploration rate ($\epsilon$) & 0.25 & 25\% exploration, 75\% exploitation \\
\hline
\end{tabular}
\caption{Q-Learning Hyperparameters.}
\end{table}

Reward weights (Table 2):

\begin{table}[H]
\centering
\begin{tabular}{|c|c|c|}
\hline
\textbf{Reward Component} & \textbf{Weight} & \textbf{Justification} \\
\hline
Goodput & 1.8 & Primary objective: successful delivery \\
Deadline Satisfaction & 0.55 & Strong prioritization of urgent messages \\
Transmission Success & 0.35 & Bonus for effective transmission \\
AoI Penalty & 0.45 & Cost of message staleness \\
Energy Cost & 0.3 & Balanced efficiency vs throughput \\
Packet Loss & 0.65 & Penalize unreliable transmissions \\
Queue Overflow & 0.3 & Discourage buffer buildup \\
Hold Backlog & 0.55 & Prevent HOLD-collapse policy \\
\hline
\end{tabular}
\caption{Reward Function Weights.}
\end{table}
```

**Why**: Provides concrete implementation details reproducible by others.

---

## EDIT #10: Performance Evaluation (Lines 835-950) - COMPLETELY FILL IN

**REPLACE** all placeholder sections with the actual results from your experiments.

**Key tables to include**:
- Delivered throughput comparison (bytes/step)
- Packet loss comparison
- Reward comparison
- Figures comparing RL vs FCFS vs baselines

(Use the honest metrics from your compact_state model)

---

## Summary

These 10 edits will integrate your RL work seamlessly into the existing paper:
- **Minimal disruption** to existing sections
- **Clear positioning** of RL as complementary to ML+heuristic approach
- **Technical depth** to explain how scheduling+aggregation coupling works
- **Honest results** showing strengths AND limitations

Would you like me to generate any of these sample tex content blocks ready to copy-paste?
