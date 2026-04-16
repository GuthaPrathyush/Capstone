from __future__ import annotations

import os
from typing import Any

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class PolicyRequest(BaseModel):
    q_p0: int
    q_p1: int
    q_p2: int
    min_deadline: float
    packet_loss_rate: float
    link_stability: float


class PolicyResponse(BaseModel):
    state_key: tuple[int, int, int, int]
    seen_state: bool
    action_idx: int
    schedule_choice: int
    agg_k: int


def _bucket(x: float, edges: list[float]) -> int:
    for i, e in enumerate(edges):
        if x <= e:
            return i
    return len(edges)


def _state_key(payload: PolicyRequest) -> tuple[int, int, int, int]:
    q_len = float(max(0, payload.q_p0) + max(0, payload.q_p1) + max(0, payload.q_p2))
    urgent_frac = (float(max(0, payload.q_p1) + max(0, payload.q_p2)) / max(1.0, q_len))

    min_deadline = float(max(0.0, payload.min_deadline))
    deadline_pressure = 1.0 / (1.0 + min_deadline)

    loss = float(np.clip(payload.packet_loss_rate, 0.0, 1.0))
    stability = float(np.clip(payload.link_stability, 0.0, 1.0))
    channel_quality = 0.5 * (1.0 - loss) + 0.5 * stability

    return (
        _bucket(q_len, [0, 2, 5, 10, 20, 40]),
        _bucket(urgent_frac, [0.0, 0.05, 0.15, 0.35, 0.6, 0.85, 1.0]),
        _bucket(deadline_pressure, [0.0, 0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0]),
        _bucket(channel_quality, [0.0, 0.25, 0.45, 0.6, 0.75, 0.9, 1.0]),
    )


def _decode_action(a: int) -> tuple[int, int]:
    a = int(a)
    schedule_choice = int(a // 5)
    agg_k = int(a % 5) + 1
    return schedule_choice, agg_k


class QPolicyStore:
    def __init__(self) -> None:
        self.q_table: dict[tuple[int, ...], np.ndarray] = {}

    def load(self, model_path: str) -> None:
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        z = np.load(model_path)
        keys = z["keys"]
        values = z["values"]
        q: dict[tuple[int, ...], np.ndarray] = {}
        for i in range(keys.shape[0]):
            q[tuple(int(x) for x in keys[i])] = values[i].astype(np.float32)
        self.q_table = q

    def predict(self, state: tuple[int, int, int, int]) -> tuple[bool, int]:
        if state not in self.q_table:
            # Fallback HOLD, k=1 => action idx 15
            return False, 15
        return True, int(np.argmax(self.q_table[state]))


app = FastAPI(title="Q-Learning Policy Backend", version="1.0.0")
store = QPolicyStore()


@app.on_event("startup")
def _startup() -> None:
    root = os.path.dirname(__file__)
    default_model = os.path.join(root, "models", "q_table_combined.npz")
    model_path = os.getenv("MODEL_PATH", default_model)
    try:
        store.load(model_path)
    except FileNotFoundError:
        # Service can start without model, but predict will fail clearly.
        store.q_table = {}


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "loaded_states": len(store.q_table),
    }


@app.post("/reload")
def reload_model(model_path: str | None = None) -> dict[str, Any]:
    root = os.path.dirname(__file__)
    path = model_path or os.getenv("MODEL_PATH") or os.path.join(root, "models", "q_table_combined.npz")
    store.load(path)
    return {"ok": True, "loaded_states": len(store.q_table), "model_path": path}


@app.post("/predict", response_model=PolicyResponse)
def predict(payload: PolicyRequest) -> PolicyResponse:
    if not store.q_table:
        raise HTTPException(status_code=500, detail="Q-table not loaded. Put q_table_combined.npz in models/ and call /reload.")

    state = _state_key(payload)
    seen, action_idx = store.predict(state)
    schedule_choice, agg_k = _decode_action(action_idx)

    return PolicyResponse(
        state_key=state,
        seen_state=seen,
        action_idx=action_idx,
        schedule_choice=schedule_choice,
        agg_k=agg_k,
    )
