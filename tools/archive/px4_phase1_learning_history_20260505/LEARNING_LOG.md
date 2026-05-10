# PX4 Phase 1 Learning Log

Date: 2026-05-05

This archive preserves the iteration history that led from a raw PX4/Gazebo telemetry collector to the current nominal rate-setpoint dataset collector.

## Why This Archive Exists

The earlier C172/JSBSim path showed that trim and initial-condition sensitivity can dominate the controller comparison. PX4/Gazebo was introduced to provide a more stable autopilot-centered simulation environment for the broader mission-planning research goal.

The current active collector is:

```text
tools/px4_phase1_v12/
```

Everything in this archive is retained as experimental traceability.

## Version Notes

- `px4_data_collection/`
  - First MAVSDK + PX4 Gazebo headless telemetry collector.
  - Confirmed CSV logging and MAVSDK connection.

- `px4_phase1_v1/`
  - Restarted PX4 work as version `v1`.
  - Added fresh-process-per-scenario data collection.

- `px4_phase1_v2/`
  - Added stale PX4/Gazebo process cleanup to fix `PX4 server already running for instance 0`.

- `px4_phase1_v3/`
  - Tried Offboard position/yaw setpoint maneuvers.
  - Useful for pipeline validation, but too high-level for the intended PINN-MPC architecture.

- `px4_phase1_v4/`
  - Switched to Offboard attitude-rate/thrust setpoints.
  - Matched the intended future structure:
    `PINN-MPC -> PX4 rate controller setpoint`.
  - Found that `thrust=0.62` caused runaway climb.

- `px4_phase1_v5/`
  - Added safety aborts and low thrust calibration candidates.
  - Failed because safety started before takeoff altitude was reached.

- `px4_phase1_v6/`
  - Waited for takeoff altitude before entering Offboard.
  - Found `0.32-0.44` thrust was too low.

- `px4_phase1_v7/`
  - Searched `0.46-0.60` thrust.
  - Found hover thrust lies between `0.50` and `0.54`.

- `px4_phase1_v8/`
  - Narrowed search to `0.510-0.530`.
  - Found `0.520` still climbed while `0.510` descended.

- `px4_phase1_v9/`
  - Narrowed search to `0.514-0.519`.
  - Found `0.519` close but slightly descending.

- `px4_phase1_v10/`
  - Final local calibration around `0.5192`.
  - Selected `HOVER_THRUST=0.5192`.

- `px4_phase1_v11/`
  - Collected a first full nominal rate/thrust excitation dataset.
  - All scenarios were technically valid, but altitude drift accumulated because Offboard started before a sufficiently stable hover state.

## Current Decision

Use `px4_phase1_v12` as the active collector.

Main v12 changes:

- wait for takeoff altitude
- wait for hover-ready state:
  - near 25 m altitude
  - small vertical velocity
  - sustained for a short interval
- keep `HOVER_THRUST=0.5192`
- keep nominal data free of external disturbances

## Data Policy

Do not commit PX4 logs, CSV datasets, model checkpoints, or generated plots unless explicitly needed for a publication artifact. The repository should track only:

- collection code
- scenario definitions
- training/evaluation code
- summary documentation
- small curated tables if needed
