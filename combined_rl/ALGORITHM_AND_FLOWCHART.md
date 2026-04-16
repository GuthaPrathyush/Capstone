# Algorithm and Flowchart: Joint Scheduling & Aggregation RL

This document details the core logic, algorithmic flow, and system architecture of the Combined Reinforcement Learning approach for UAV message management. It is designed to be easily understood, explaining every core concept used in the project.

---

## 1. Core Concepts Explained

Before diving into the flow, here is a brief explanation of the key terms and algorithms we are using.

### What is a Markov Decision Process (MDP)?
An MDP is a mathematical framework used to describe an environment in Reinforcement Learning. It assumes that the future depends *only* on the current state, not the history of how we got there. It consists of:
*   **State (S):** What the agent observes right now (e.g., queue length, SNR).
*   **Action (A):** What the agent can do right now (e.g., send 3 packets of high priority).
*   **Reward (R):** The immediate feedback the agent gets after taking an action (e.g., +10 for delivering a packet, -5 for wasting energy).
*   **Transition:** How the environment changes after the action is taken.

### What is Q-Learning?
Q-Learning is a specific Reinforcement Learning algorithm. The goal of Q-learning is to learn a "Quality" value (the Q-value) for every possible Action in every possible State. 
*   A high Q-value means: "Taking this action in this state will likely lead to a high total reward in the long run."
*   The agent learns these values through trial and error using the **Bellman Equation** (updating its guesses based on the actual rewards it receives).

### What is "Tabular" Q-Learning?
In *Tabular* Q-learning, we literally create a giant lookup table (a spreadsheet). 
*   The **Rows** are every possible State.
*   The **Columns** are every possible Action.
*   The **Cells** contain the Q-values.
Because continuous numbers (like an SNR of 12.345 dB) would create infinite rows, we use **Bucketing (Discretization)**. We group continuous numbers into chunks (e.g., SNR bucket 1: 0-10 dB, bucket 2: 10-20 dB).

### What is Epsilon-Greedy?
This is how the agent decides what to do during training. 
*   **Epsilon ($\epsilon$)** is a small probability (like 20%).
*   20% of the time, the agent does something completely **Random** (Exploration) to discover new strategies.
*   80% of the time, the agent is **Greedy** (Exploitation)—it looks at its Q-table and picks the action with the highest known Q-value.

---

## 2. System Architecture Flowchart

This shows how the different parts of our system talk to each other.

[ UAV Generates Packets ] 
       |
       v
[ Message Queue ]  <---- (Holds packets, tracks priorities and deadlines)
       |
       v
[ RL Agent ] <---- (Observes Queue State, Link Quality from ns-3, and Energy)
       |
       v
[ Agent Consults Q-Table ] ---> (Decides: Which priority to send? How many to aggregate?)
       |
       v
[ Execute Transmission ] ---> (Sends aggregated packet via ns-3 simulated Wi-Fi)
       |
       v
[ Receiver / GCS ] ---> (Packet arrives or drops based on SNR/Congestion)
       |
       v
[ Calculate Reward ] ---> (Agent gets + points for delivery, - points for drops/AoI/Energy)
       |
       v
[ Update Q-Table ] ---> (Agent learns and gets smarter for the next step)

---

## 3. The Algorithm Breakdown

### 3.1. State Space (What the agent sees)
To use Tabular Q-learning, we compress the ns-3 dataset into 8 specific "buckets":
1.  **Queue Length:** How many packets are waiting? (Buckets: 0, 2, 5, 10, 20, 40+)
2.  **Priority 2 Fraction:** What % of the queue is critical data?
3.  **Min Deadline:** How close is the most urgent packet to expiring?
4.  **SNR:** Signal-to-Noise ratio of the wireless link.
5.  **Goodput:** Current available network capacity.
6.  **Loss Rate:** Are packets currently dropping?
7.  **Energy Level:** How much battery is left?
8.  **AoI (Age of Information):** How stale is the data at the receiver?

### 3.2. Action Space (What the agent can do)
The agent makes a **Combined Action**. It picks one number from 0 to 19, which decodes into two decisions:
*   **Schedule Choice:** Serve Priority 0, Priority 1, Priority 2, or HOLD (do nothing).
*   **Aggregation Choice:** Combine 1, 2, 3, 4, or 5 packets together.

### 3.3. Reward Function (How the agent is graded)
After the action, we calculate the reward:
*   **+ Goodput:** Bytes successfully delivered.
*   **+ Deadline Bonus:** Extra points for saving a packet right before it expires.
*   **- AoI Penalty:** Heavy penalty if the receiver hasn't heard from the UAV in a long time.
*   **- Energy Penalty:** Small penalty for transmitting, larger penalty for transmitting massive aggregated packets.
*   **- Loss Penalty:** Penalty if the packet was dropped due to bad SNR.

---

## 4. Step-by-Step Execution Flowchart (Inside the Code)

This is exactly what happens line-by-line inside our `train_qlearning.py` script for every single timestep.

Step 1: Read current row from ns-3 dataset (e.g., Row 100).
   |
   v
Step 2: Discretize the row's data into the 8 State Buckets (This is State $S_t$).
   |
   v
Step 3: Roll a virtual dice (Epsilon-Greedy).
        -> If < 20%: Pick a random action from 0-19.
        -> If > 20%: Look up State $S_t$ in Q-table, pick the action with the highest score.
   |
   v
Step 4: Decode the action. (e.g., Action 14 = "Serve Priority 2, Aggregate 5 packets").
   |
   v
Step 5: Run the Transmission Proxy Model. 
        -> Did the action exceed the current Goodput? (If yes, partial loss).
        -> Did the action fail due to current Packet Loss Rate?
        -> Calculate how much energy was spent.
        -> Update the simulated Age of Information (AoI).
   |
   v
Step 6: Calculate the Total Reward ($R_t$) using the math formula.
   |
   v
Step 7: Read the *next* row from the ns-3 dataset (Row 101). Discretize it to get Next State ($S_{t+1}$).
   |
   v
Step 8: Apply the Bellman Equation.
        -> Look at the highest possible score in Next State ($S_{t+1}$).
        -> Update the Q-table cell for ($S_t$, Action) using the Reward ($R_t$) + Future potential.
   |
   v
Step 9: Move to the next timestep. Repeat.

---

## 5. Why This Solves the UAV Problem

1.  **Adapting to Bad Links:** If the SNR drops, the agent learns that trying to send 5 aggregated packets ($k=5$) results in a massive Loss Penalty. The Q-table updates, and next time SNR is low, it will choose to send 1 packet ($k=1$) or HOLD.
2.  **Balancing Battery vs. Freshness:** If the queue is empty, normally a drone does nothing. But if the AoI is getting dangerously high, the AoI Penalty grows huge. The agent learns it is worth taking a small Energy Penalty to send a tiny "heartbeat" packet just to reset the AoI.
3.  **Rescuing Critical Data:** Because the state includes `min_deadline`, the agent knows when a packet is about to expire. It learns to ignore standard FIFO (First-In-First-Out) rules and immediately schedule Priority 2 traffic to get the Deadline Bonus.
