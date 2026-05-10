# PX4 Task-Aware Mission Planning

This is the rebooted active project workspace.

## Objective

Build a mission-level planner evaluation framework that accounts for PX4 closed-loop dynamics:

```text
task sequence
-> learned PX4 closed-loop rollout
-> ETA / tracking error / risk / energy proxy
-> dynamics-aware mission cost
```

## Current Scope

- Vehicle: PX4 Standard VTOL in multicopter mode
- Controller: PX4 internal closed-loop controller
- Learned model: task-state surrogate
- Planning level: mission/task cost prediction

Fixed-wing and transition modes are intentionally deferred.

## Workflow

```text
data_collection/
-> dataset_builder/
-> surrogate_training/
-> rollout_evaluation/
-> mission_planning/
```

Each folder contains a short README describing its responsibility.

## First Deliverables

1. Task-level PX4 SITL data collection scripts
2. Trajectory/task-based dataset builder
3. Task-state PINN surrogate training notebook
4. Task-aware rollout evaluator
5. Nominal ETA vs PINN rollout ETA validation
