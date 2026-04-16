from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CombinedRewardWeights:
    # Positive
    goodput: float = 2.2
    deadline: float = 0.55
    tx_success: float = 0.45
    agg_efficiency: float = 0.4

    # Negative
    aoi: float = 0.45
    energy: float = 0.3
    loss: float = 1.1
    overflow: float = 0.3
    hold_backlog: float = 0.55


class CombinedActions:
    """
    Action = (schedule_choice, agg_k)

    schedule_choice:
      - 0: serve priority 0
      - 1: serve priority 1
      - 2: serve priority 2
      - 3: HOLD

    agg_k:
      - 1..5

    We encode a single integer:
      a = schedule_choice * 5 + (agg_k - 1)
    """

    SERVE_P0 = 0
    SERVE_P1 = 1
    SERVE_P2 = 2
    HOLD = 3

    AGG_K_MIN = 1
    AGG_K_MAX = 5

    @staticmethod
    def n() -> int:
        return 4 * (CombinedActions.AGG_K_MAX - CombinedActions.AGG_K_MIN + 1)

    @staticmethod
    def encode(schedule_choice: int, agg_k: int) -> int:
        k = int(np.clip(agg_k, CombinedActions.AGG_K_MIN, CombinedActions.AGG_K_MAX))
        s = int(np.clip(schedule_choice, 0, 3))
        return s * 5 + (k - 1)

    @staticmethod
    def decode(a: int) -> tuple[int, int]:
        a = int(a)
        s = int(a // 5)
        k = int(a % 5) + 1
        return s, k


def transmission_model(
    *,
    step_ms: int,
    q_p0: int,
    q_p1: int,
    q_p2: int,
    packet_size: float,
    min_deadline: float,
    mean_deadline: float,
    goodput_kbps: float,
    packet_loss_rate: float,
    link_stability: float,
    aoi_ms: float,
    energy_level: float,
    action: int,
    w: CombinedRewardWeights = CombinedRewardWeights(),
) -> tuple[float, dict]:
    """
    Compute a shaped reward for a combined scheduling+aggregation action.

    Notes:
    - This uses a lightweight model on top of dataset signals.
    - It does NOT attempt to exactly reproduce ns-3; it is a training proxy.
    """
    schedule_choice, agg_k = CombinedActions.decode(action)

    q = np.array([q_p0, q_p1, q_p2], dtype=np.float32)
    queue_len = float(q.sum())

    # Capacity in bytes per step.
    step_s = max(1e-6, float(step_ms) / 1000.0)
    cap_bytes = max(0.0, float(goodput_kbps) * 1000.0 / 8.0 * step_s)

    loss = float(np.clip(packet_loss_rate, 0.0, 1.0))
    stab = float(np.clip(link_stability, 0.0, 1.0))

    # Determine how many packets we *attempt* to send from a chosen priority class.
    if schedule_choice == CombinedActions.HOLD:
        chosen_p = -1
        send_pkts = 0.0
    else:
        chosen_p = int(np.clip(schedule_choice, 0, 2))
        available = float(q[chosen_p])
        send_pkts = float(min(available, float(agg_k)))

    attempted_bytes = send_pkts * float(max(0.0, packet_size))

    # Delivered bytes limited by capacity and further reduced by loss proxy.
    delivered_bytes = min(attempted_bytes, cap_bytes) * (1.0 - loss)

    # Deadline shaping: encourage serving when deadlines are tight.
    md = float(max(0.0, min_deadline))
    mean_d = float(max(0.0, mean_deadline))
    urgency = 1.0 / (1.0 + md)  # higher when min_deadline is small
    deadline_bonus = 0.0
    if chosen_p == 2:
        deadline_bonus = 1.0 * urgency
    elif chosen_p == 1:
        deadline_bonus = 0.6 * urgency
    elif chosen_p == 0:
        deadline_bonus = 0.3 * urgency
    else:
        deadline_bonus = 0.0

    # AoI penalty: prefer actions that likely deliver an update (success depends on stability and chosen action).
    # Use dataset AoI as baseline; "successful transmit" reduces AoI proxy.
    base_aoi = float(max(0.0, aoi_ms))
    did_tx = 1.0 if send_pkts > 0 else 0.0
    # success proxy: stability * (1-loss)
    success_p = stab * (1.0 - loss)
    aoi_after = base_aoi + float(step_ms)
    if did_tx > 0:
        # if we "transmit", reduce AoI in proportion to success
        aoi_after = aoi_after * (1.0 - 0.85 * success_p)
    aoi_pen = np.clip(aoi_after / 500.0, 0.0, 10.0)  # scale to ~[0,10]

    # Energy cost: base transmit + per-byte; HOLD is cheap but not free.
    # energy_level is logged as remaining J (from energy model).
    if schedule_choice == CombinedActions.HOLD or send_pkts <= 0:
        energy_cost = 0.002
    else:
        energy_cost = 0.01 + 0.000002 * attempted_bytes + 0.002 * float(max(0, agg_k - 1))
    energy_pen = float(energy_cost)

    # Loss penalty still discourages waste, but with a softer slope to avoid over-conservative policies.
    loss_pen = ((attempted_bytes - delivered_bytes) / 2600.0) if attempted_bytes > 0 else 0.0

    # Queue penalty: discourage building queues.
    overflow_pen = queue_len / 60.0

    # Explicitly penalize HOLD when backlog exists to avoid degenerate do-nothing policies.
    hold_backlog_pen = 0.0
    if schedule_choice == CombinedActions.HOLD and queue_len > 0:
        hold_backlog_pen = min(1.0, queue_len / 20.0)

    # Small success bonus for actions that actually deliver bytes.
    tx_success_bonus = 0.0
    if delivered_bytes > 0:
        tx_success_bonus = min(1.0, delivered_bytes / max(1.0, attempted_bytes if attempted_bytes > 0 else delivered_bytes))

    # Encourage larger aggregation only when link conditions suggest it is safe and efficient.
    agg_eff_bonus = 0.0
    if schedule_choice != CombinedActions.HOLD and send_pkts > 0:
        agg_scale = float(max(0, agg_k - 1)) / float(max(1, CombinedActions.AGG_K_MAX - 1))
        agg_eff_bonus = agg_scale * stab * (1.0 - loss)

    # Positive term: normalize delivered bytes to a stable scale
    goodput_term = delivered_bytes / 2000.0

    r = (
        w.goodput * goodput_term
        + w.deadline * deadline_bonus
        + w.tx_success * tx_success_bonus
        + w.agg_efficiency * agg_eff_bonus
        - w.aoi * aoi_pen
        - w.energy * energy_pen
        - w.loss * loss_pen
        - w.overflow * overflow_pen
        - w.hold_backlog * hold_backlog_pen
    )

    info = {
        "schedule_choice": schedule_choice,
        "agg_k": agg_k,
        "chosen_p": chosen_p,
        "send_pkts": send_pkts,
        "cap_bytes": cap_bytes,
        "attempted_bytes": attempted_bytes,
        "delivered_bytes": delivered_bytes,
        "deadline_bonus": deadline_bonus,
        "aoi_after": aoi_after,
        "energy_cost": energy_cost,
        "loss": loss,
        "stability": stab,
        "hold_backlog_pen": hold_backlog_pen,
        "tx_success_bonus": tx_success_bonus,
        "agg_eff_bonus": agg_eff_bonus,
    }
    return float(r), info

