# PX4 Task-Aware Mission Planning Reboot Plan

## Core Research Question

Can a learned PX4 closed-loop dynamics surrogate predict mission-level cost more accurately than nominal distance/speed planning?

The planned contribution is:

```text
Task command sequence
-> PX4 closed-loop response surrogate
-> ETA / tracking error / risk / energy prediction
-> dynamics-aware mission cost
```

This phase is focused on multicopter closed-loop mode only. Fixed-wing and VTOL transition are deferred.

## Why We Are Rebooting

The previous path tested several low-level and mid-level ideas:

- C172 JSBSim PINN-MPC
- PX4 rate-setpoint dynamics modeling
- PX4 closed-loop PINN modeling
- recovery-oriented PINN-MPC tuning

The important lesson is that low-level PINN-MPC is not the cleanest first contribution for the final mission-planning goal. The strongest and most direct path is to use the learned PX4 closed-loop model as a task-level rollout simulator.

## Phase 1: Closed-Loop Task Surrogate

Scope:

```text
PX4 Standard VTOL in multicopter mode
PX4 internal controller remains active
surrogate predicts closed-loop task response
```

Recommended state:

```text
north, east, altitude,
vn, ve, vd,
yaw
```

Roll and pitch should be logged as diagnostics, but not treated as primary mission-planning states in the first task-level model.

Recommended input:

```text
current task-state
current target/setpoint
previous target/setpoint
target error
delta target
dt
```

Recommended output:

```text
delta task-state
```

## Phase 2: Task-Aware Rollout Simulator

Input:

```text
task sequence = [(x, y, z, yaw, hold_time), ...]
```

Output:

```text
predicted ETA
final error
RMSE
max deviation
energy proxy
risk score
mission cost
```

Baseline comparison:

```text
nominal ETA = distance / nominal speed
PINN ETA = learned surrogate rollout ETA
PX4 ETA = SITL ground truth ETA
```

## Phase 3: Validation Against PX4 SITL

Run identical task scripts in PX4 SITL and compare:

- ETA error
- final position error
- altitude error
- yaw error
- maximum deviation
- failure or safety margin

The first publication-quality figure should compare nominal ETA error against PINN rollout ETA error.

## Phase 4: Dynamics-Aware Mission Planning

Start with:

```text
single UAV
multiple tasks
```

Then extend to:

```text
3-5 UAVs
5-10 tasks
```

Compare:

```text
distance-based assignment
vs
PINN rollout cost-based assignment
```

## Phase 5: Robustness

External disturbances should first be represented as uncertainty in task execution cost rather than directly as a mandatory PINN input.

Recommended robust bid:

```text
bid = mean(cost) + lambda * std(cost)
```

This aligns better with mission allocation than trying to make the first surrogate explicitly model all disturbances.

## Deferred Work

Not in the immediate phase:

- fixed-wing mode
- VTOL transition
- heterogeneous fleet
- Transformer models
- embedded deployment
- real aircraft digital twin

These become meaningful after multicopter closed-loop mission-cost prediction is validated.
