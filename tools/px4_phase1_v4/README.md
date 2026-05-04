# PX4 Phase 1 Rate-Setpoint Collection v4

This version matches the intended control architecture:

```text
Future PINN-MPC layer -> PX4 rate controller setpoints -> PX4 low-level control -> Gazebo plant
```

Version `v4` collects nominal hover-regime data using MAVSDK Offboard attitude-rate/thrust commands.

## What Is Collected

Telemetry:

- local/global position
- velocity NED
- attitude Euler
- body angular rates
- battery/status

Reference inputs:

- `ref_roll_rate_deg_s`
- `ref_pitch_rate_deg_s`
- `ref_yaw_rate_deg_s`
- `ref_thrust`
- `ref_label`
- `ref_phase`

These references are the first candidate action inputs for nominal dynamics learning.

## Install Requirements

Inside WSL Ubuntu:

```bash
python3 -m pip install --user -r /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v4/requirements.txt
```

## Run One Scenario First

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v4
python3 collect_px4_phase1_v4.py --config scenarios.yaml --scenario R1_pitch_rate_doublet_small
```

## Run All Rate-Setpoint Scenarios

```bash
python3 collect_px4_phase1_v4.py --config scenarios.yaml
```

## Scenarios

- `R0_rate_hover_hold`
- `R1_pitch_rate_doublet_small`
- `R2_roll_rate_doublet_small`
- `R3_yaw_rate_step_small`
- `R4_thrust_step_small`
- `R5_combined_smooth_sequence`

All scenarios are nominal. Disturbance injection belongs in a later version.

## Important URL Fix

MAVSDK rejects `udpin://:14540`. Use:

```text
udpin://0.0.0.0:14540
```

This is already set in `scenarios.yaml`.

## Output

Outputs are written to:

```text
~/px4_datasets/px4_phase1_standard_vtol_rate_setpoint_v4_<timestamp>/
```

Each scenario folder contains:

```text
telemetry_raw.csv
telemetry_analysis.csv
metadata.json
px4_stdout.log
quicklook.png
```

The run folder also contains `run_metadata.json` and `summary.csv`.
