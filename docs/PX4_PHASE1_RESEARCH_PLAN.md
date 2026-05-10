# PX4 Phase 1 Research Plan

Date: 2026-05-05

## Long-Term Goal

Build a mission-planning framework that assigns tasks and predicts mission time while accounting for the capability and robustness of the low-level controller.

The planner should not assume ideal low-level tracking. Instead, it should use learned or measured low-level capability models:

- expected tracking error
- recovery time after disturbances
- energy or thrust margin
- speed/altitude loss
- failure or constraint violation probability
- uncertainty under wind/gust/model mismatch

## Research Hypothesis

A nominal learned dynamics model combined with MPC can improve the predictability and robustness of low-level maneuver execution. This low-level capability can then be summarized and used by an upper-level mission planner.

Important modeling choice:

```text
Nominal PINN dynamics should not take unknown disturbance as an input.
```

Disturbances are evaluation axes, not nominal training inputs. Measurable context such as estimated wind can be added later as a context-conditioned model, but the first model should be nominal.

## Phase 1 Objective

Create a reproducible PX4/Gazebo benchmark for local hover-regime rate/thrust dynamics.

Target control hierarchy:

```text
future PINN-MPC layer
  -> roll/pitch/yaw rate setpoints + thrust setpoint
  -> PX4 rate controller / low-level allocation
  -> Gazebo plant
```

The first dataset should support learning:

```text
x_t, u_t -> x_{t+1}
```

where:

- `x_t`: local position, velocity, attitude, body rates, altitude, battery/status if useful
- `u_t`: roll-rate setpoint, pitch-rate setpoint, yaw-rate setpoint, thrust setpoint

## Phase 1A: Simulation and Data Collection

Status:

- WSL2 + PX4 Gazebo headless runs successfully.
- MAVSDK telemetry collection works.
- Fresh-process-per-scenario collection works.
- Rate/thrust Offboard command path works.
- Hover thrust was calibrated near `0.5192`.
- v11 showed altitude drift due to insufficient hover settling before Offboard.
- v12 adds a stricter hover-ready gate.

Active collector:

```text
tools/px4_phase1_v12/
```

Immediate acceptance criteria for v12:

- all nominal scenarios collect without safety abort
- `quality_ok_basic=True`
- altitude drift is much smaller than v11
- commanded rate axes produce nonzero measured body-rate response
- telemetry contains reference columns:
  - `ref_roll_rate_deg_s`
  - `ref_pitch_rate_deg_s`
  - `ref_yaw_rate_deg_s`
  - `ref_thrust`

## Phase 1B: Dataset Builder

After v12 data is accepted, build a dataset processor that:

1. Loads all `telemetry_analysis.csv` files.
2. Filters unsafe or low-quality scenarios.
3. Constructs aligned one-step samples:

```text
[state_t, action_t] -> delta_state_t
```

4. Splits by scenario, not just random rows:
   - train: most nominal excitations
   - validation: held-out scenario instances
   - test: held-out maneuver type or repeated seeds

Initial state candidates:

- local position N/E/D or relative altitude
- local velocity N/E/D
- roll, pitch, yaw
- body rates p/q/r
- optional battery voltage if it affects thrust response

Initial action candidates:

- roll-rate setpoint
- pitch-rate setpoint
- yaw-rate setpoint
- thrust setpoint
- previous action and delta action if actuator/setpoint lag matters

## Phase 1C: Nominal Dynamics Model

Train a nominal neural/PINN-style dynamics model:

```text
f_theta(x_t, u_t) -> delta_x_t
```

Evaluation:

- one-step RMSE
- multi-step rollout RMSE
- scenario-level rollout stability
- axis-specific response quality for roll/pitch/yaw/thrust maneuvers

Do not train with disturbance labels in this phase.

## Phase 1D: Controller Evaluation

Use the learned model inside an MPC or MPPI reference-correction layer.

Compare:

- PX4 baseline behavior under nominal and disturbed scenarios
- PINN-MPC rate/thrust setpoint layer under the same scenarios

Metrics:

- tracking RMSE
- max tracking error
- recovery time
- final error
- altitude/speed loss
- thrust/control effort
- constraint violations
- scenario success/failure

## Phase 1E: Disturbance Evaluation

Only after the nominal model/controller works:

- add wind/gust or equivalent external disturbances
- keep disturbance out of the nominal model input
- evaluate robustness by severity/family:
  - none
  - weak gust
  - sinusoidal gust
  - mixed gust
  - stronger gust

Expected research output:

```text
low-level capability envelope under disturbance
```

Examples:

- recovery time versus gust severity
- tracking error bound versus maneuver type
- mission-time uncertainty induced by low-level control limits

## Phase 2: Capability Model for Mission Planning

Convert low-level evaluation results into planner-level abstractions:

- segment execution time distribution
- expected recovery delay
- risk/failure probability
- energy or thrust margin
- feasible maneuver envelope

These become edge costs or constraints in the mission planner:

```text
edge_cost = expected_time + risk_weight * risk + energy_weight * energy
```

## Phase 3: Mission Planning and Task Allocation

Use capability-aware costs for:

- route planning
- task allocation across heterogeneous vehicles
- robust scheduling under external disturbances
- uncertainty-aware mission-time prediction

Final framework target:

```text
mission planner
  -> low-level capability-aware task allocation
  -> PINN-MPC/PX4 execution layer
  -> measured outcome feedback
```

## Versioning Rule

Every new experiment code version must increment the version number. Do not overwrite old experiment versions.

Old versions should be archived with a short learning log when they are no longer active.
