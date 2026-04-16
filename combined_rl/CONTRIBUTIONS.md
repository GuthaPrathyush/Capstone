# Contributions

This project was developed as a near-equal collaboration between **Prathyush** and **Harshitha**, with clear technical ownership by module.

## Author Roles

- **Prathyush**: Aggregation-focused contributions
- **Harshitha**: Scheduling-focused contributions

---

## Contribution Split (Near-Equal)

- **Prathyush (Aggregation Track): ~50%**
- **Harshitha (Scheduling Track): ~50%**

The overall architecture, evaluation planning, and final integration were performed jointly.

---

## Prathyush Contributions (Aggregation)

1. Defined the aggregation decision structure within the combined action space (`agg_k` control).
2. Designed and refined packet-combination strategy from `k=1..5` as part of joint RL actions.
3. Led aggregation-oriented reward tuning (trade-off between transmission efficiency and reliability).
4. Analyzed how aggregation intensity behaves across realistic vs high-congestion scenarios.
5. Helped produce FCFS vs proposed comparisons focused on loss-efficiency gains.
6. Contributed aggregation interpretation for paper narrative and results discussions.

---

## Harshitha Contributions (Scheduling)

1. Defined scheduling decision structure (`serve_p0`, `serve_p1`, `serve_p2`, `hold`).
2. Led queue-priority and deadline-aware scheduling logic used in the RL proxy model.
3. Contributed scheduling-oriented state feature design (queue composition, urgency signals).
4. Led baseline comparisons against FCFS/FIFO and heuristic schedulers.
5. Analyzed scheduling behavior under varied link quality and congestion conditions.
6. Contributed scheduling-focused result interpretation and manuscript framing.

---

## Joint Contributions

1. Co-designed the combined scheduling+aggregation RL framework.
2. Co-developed ns-3 based scenario generation and dataset usage strategy.
3. Jointly performed training/evaluation experiments and benchmark validation.
4. Jointly prepared final figures, metric tables, and publication-ready documentation.
5. Jointly reviewed limitations, future scope, and reproducibility details.

---

## Notes on Authorship Intent

The contribution mapping is intentionally balanced and reflects module ownership:

- **Aggregation module leadership**: Prathyush
- **Scheduling module leadership**: Harshitha
- **System integration and publication preparation**: shared

This division supports equal intellectual contribution while maintaining distinct technical responsibility areas.
