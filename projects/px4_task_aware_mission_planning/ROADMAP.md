# Roadmap

## Milestone 1: Task Data Collection

Create PX4 SITL task scripts for:

- hover hold
- position steps
- altitude steps
- yaw steps
- box missions
- mixed waypoint missions

The data split must be trajectory-based, not random row-based.

## Milestone 2: Task-State Dataset

Build a dataset with:

- current task-state
- current target
- previous target
- target error
- delta target
- next delta task-state

Primary task-state:

```text
north, east, altitude, vn, ve, vd, yaw
```

Roll/pitch remain diagnostics.

## Milestone 3: Surrogate Training

Train a compact closed-loop task surrogate and evaluate:

- 1-step prediction
- 5-second rollout
- full-task rollout
- ETA error
- final error

## Milestone 4: Rollout Evaluation

Compare:

```text
nominal distance/speed ETA
vs
PINN rollout ETA
vs
PX4 SITL ETA
```

## Milestone 5: Mission Planning Cost

Define:

```text
J = w_eta ETA + w_err tracking_error + w_energy energy + w_risk risk
```

Use this cost for task ordering and later multi-UAV assignment.
