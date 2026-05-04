# PX4 Phase 1 Nominal Maneuver Collection v3

This is the first nominal maneuver dataset collector for the new PX4/Gazebo research line.

Version `v3` builds on the validated fresh-process collector:

- Starts a fresh PX4/Gazebo SITL process for each scenario.
- Cleans stale PX4/Gazebo processes before launch.
- Takes off to a stable hover.
- Starts MAVSDK Offboard mode.
- Sends local NED position/yaw setpoint sequences.
- Saves raw telemetry, analysis-window telemetry, quality metrics, metadata, PX4 logs, and quicklook plots.

No disturbances, PINN training, or MPC are included in this version.

## Install Requirements

Inside WSL Ubuntu:

```bash
python3 -m pip install --user -r /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v3/requirements.txt
```

## Run One Scenario First

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v3
python3 collect_px4_phase1_v3.py --config scenarios.yaml --scenario M1_altitude_step_25_35_25m
```

## Run All Nominal Maneuvers

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v3
python3 collect_px4_phase1_v3.py --config scenarios.yaml
```

## Scenarios

- `M0_hover_hold_25m`
- `M1_altitude_step_25_35_25m`
- `M2_north_step_0_20_0m`
- `M3_square_20m`
- `M4_yaw_step_0_45_0deg`

Each row includes telemetry plus current reference columns:

- `ref_phase`
- `ref_label`
- `ref_north_m`
- `ref_east_m`
- `ref_altitude_m`
- `ref_yaw_deg`

## Output

Outputs are written to:

```text
~/px4_datasets/px4_phase1_standard_vtol_nominal_maneuver_v3_<timestamp>/
```

Each scenario folder contains:

```text
telemetry_raw.csv
telemetry_analysis.csv
metadata.json
px4_stdout.log
quicklook.png
```

The run folder also contains:

```text
run_metadata.json
summary.csv
```

## Suggested First Check

After one scenario finishes:

```bash
cat ~/px4_datasets/px4_phase1_standard_vtol_nominal_maneuver_v3_*/summary.csv
```

Check:

- `quality_ok_basic=True`
- `rows_raw` matches roughly `duration_s / sample_period_s`
- `analysis_ref_altitude_rmse_m` is reasonable for altitude scenarios
- `analysis_ref_horizontal_rmse_m` is reasonable for position scenarios

If this works, collect each maneuver multiple times before training a nominal dynamics model.
