from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel


class SimConfig(BaseModel):
    dataset_path: str
    policy_url: str = "http://127.0.0.1:8001/predict"
    queue_cap_pkts: int = 60
    tick_ms: int = 10


@dataclass
class SimState:
    q_p0: int
    q_p1: int
    q_p2: int
    row_idx: int = 0


app = FastAPI(title="Simulation Pinger Backend", version="1.0.0")

_store: dict[str, Any] = {
    "df": None,
    "config": None,
    "state": None,
}


def _apply_action(state: SimState, schedule_choice: int, agg_k: int, arr_p0: int, arr_p1: int, arr_p2: int, cap: int) -> dict[str, Any]:
    q = [max(0, state.q_p0), max(0, state.q_p1), max(0, state.q_p2)]

    served = 0
    if 0 <= schedule_choice <= 2:
        served = min(q[schedule_choice], max(1, agg_k))
        q[schedule_choice] -= served

    q[0] += max(0, arr_p0)
    q[1] += max(0, arr_p1)
    q[2] += max(0, arr_p2)

    dropped = 0
    total = sum(q)
    overflow = max(0, total - max(0, cap))
    if overflow > 0:
        # Drop from low priority first.
        for idx in (0, 1, 2):
            if overflow <= 0:
                break
            take = min(q[idx], overflow)
            q[idx] -= take
            overflow -= take
            dropped += take

    state.q_p0, state.q_p1, state.q_p2 = q
    return {
        "served_pkts": served,
        "dropped_overflow_pkts": dropped,
        "q_after": {"q_p0": q[0], "q_p1": q[1], "q_p2": q[2]},
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "loaded": _store["df"] is not None,
        "rows": int(len(_store["df"])) if _store["df"] is not None else 0,
    }


@app.post("/load")
def load_sim(cfg: SimConfig) -> dict[str, Any]:
    if not os.path.exists(cfg.dataset_path):
        raise HTTPException(status_code=404, detail=f"Dataset not found: {cfg.dataset_path}")

    df = pd.read_csv(cfg.dataset_path, low_memory=False)
    required = ["q_p0_pkts", "q_p1_pkts", "q_p2_pkts", "min_deadline", "packet_loss_rate", "link_stability"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Dataset missing columns: {missing}")

    s = SimState(
        q_p0=int(max(0, df.iloc[0].get("q_p0_pkts", 0))),
        q_p1=int(max(0, df.iloc[0].get("q_p1_pkts", 0))),
        q_p2=int(max(0, df.iloc[0].get("q_p2_pkts", 0))),
        row_idx=0,
    )

    _store["df"] = df
    _store["config"] = cfg
    _store["state"] = s
    return {
        "ok": True,
        "rows": int(len(df)),
        "initial_state": {"q_p0": s.q_p0, "q_p1": s.q_p1, "q_p2": s.q_p2},
    }


@app.post("/step")
def step_once() -> dict[str, Any]:
    df: pd.DataFrame | None = _store["df"]
    cfg: SimConfig | None = _store["config"]
    state: SimState | None = _store["state"]

    if df is None or cfg is None or state is None:
        raise HTTPException(status_code=400, detail="Call /load first")

    if state.row_idx >= len(df) - 1:
        return {"done": True, "row_idx": state.row_idx}

    row = df.iloc[state.row_idx]
    next_row = df.iloc[state.row_idx + 1]

    payload = {
        "q_p0": int(state.q_p0),
        "q_p1": int(state.q_p1),
        "q_p2": int(state.q_p2),
        "min_deadline": float(row.get("min_deadline", 0.0)),
        "packet_loss_rate": float(row.get("packet_loss_rate", 0.0)),
        "link_stability": float(row.get("link_stability", 0.0)),
    }

    with httpx.Client(timeout=5.0) as client:
        r = client.post(cfg.policy_url, json=payload)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Policy backend error: {r.status_code} {r.text}")

    policy = r.json()

    # Approximate arrivals from row-to-row queue deltas in dataset.
    arr_p0 = int(max(0.0, float(next_row.get("q_p0_pkts", 0.0)) - float(row.get("q_p0_pkts", 0.0))))
    arr_p1 = int(max(0.0, float(next_row.get("q_p1_pkts", 0.0)) - float(row.get("q_p1_pkts", 0.0))))
    arr_p2 = int(max(0.0, float(next_row.get("q_p2_pkts", 0.0)) - float(row.get("q_p2_pkts", 0.0))))

    apply_info = _apply_action(
        state,
        schedule_choice=int(policy["schedule_choice"]),
        agg_k=int(policy["agg_k"]),
        arr_p0=arr_p0,
        arr_p1=arr_p1,
        arr_p2=arr_p2,
        cap=int(cfg.queue_cap_pkts),
    )

    out = {
        "done": False,
        "row_idx": state.row_idx,
        "tick_ms": cfg.tick_ms,
        "input_state": payload,
        "policy": policy,
        "arrivals": {"p0": arr_p0, "p1": arr_p1, "p2": arr_p2},
        **apply_info,
    }

    state.row_idx += 1
    return out


@app.post("/run")
def run_steps(steps: int = 50) -> dict[str, Any]:
    steps = max(1, min(steps, 5000))
    records: list[dict[str, Any]] = []
    for _ in range(steps):
        tick = step_once()
        records.append(tick)
        if tick.get("done"):
            break

    last = records[-1] if records else {"done": True}

    summary = {
        "ok": True,
        "steps_requested": steps,
        "steps_executed": len(records),
        "done": bool(last.get("done", False)),
        "last_row_idx": int(last.get("row_idx", -1)),
        "last_queue": last.get("q_after", {}),
        "last_policy": last.get("policy", {}),
    }

    payload = {
        "ok": True,
        "steps_requested": steps,
        "steps_executed": len(records),
        "summary": summary,
        "last": last,
        "records": records,
    }

    return Response(
        content=json.dumps(payload, indent=2, ensure_ascii=False),
        media_type="application/json",
    )
