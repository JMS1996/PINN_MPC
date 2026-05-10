# PX4 Phase 1 Closed-Loop Dataset v14

`v14` changes the data collection layer from open-loop attitude-rate/thrust
commands to PX4 closed-loop position and velocity offboard setpoints.

The reason is important: v12/v13 showed that fixed open-loop thrust hover can
drift downward even when the telemetry and kinematics are internally
consistent. For the first useful MPC model, we want the learned plant to include
the behavior that the future upper-level controller will actually see:

```text
future PINN-MPC layer -> PX4 position/velocity setpoint -> PX4 cascaded controllers -> Gazebo plant
```

## What This Collects

- Position-NED hold and step responses around 25 m relative altitude.
- Small north/east/yaw position steps.
- Small north/east/vertical velocity doublets.
- IMU acceleration and finite-difference acceleration diagnostics inherited
  from v13.

This is still multicopter-hover mode for `gz_standard_vtol`; it is not fixed
wing transition data yet.

## Run One Scenario First

Inside WSL Ubuntu:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v14_closed_loop
python3 collect_px4_phase1_v14.py --config scenarios.yaml --scenario C00_position_hold_25m
```

## Run All Scenarios

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v14_closed_loop
python3 collect_px4_phase1_v14.py --config scenarios.yaml
```

For more data, repeat all scenarios:

```bash
for i in $(seq 1 5); do
  echo "===== v14 closed-loop collection run $i / 5 ====="
  python3 collect_px4_phase1_v14.py --config scenarios.yaml
done
```

## Verify Latest Run

```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path

root = Path.home() / 'px4_datasets'
runs = sorted(root.glob('px4_phase1_standard_vtol_closed_loop_dataset_v14_*'))
if not runs:
    raise SystemExit('No v14 runs found.')

run = runs[-1]
summary = pd.read_csv(run / 'summary.csv')
cols = [
    'scenario', 'rows_analysis', 'abort_reason', 'safety_ok', 'quality_ok_basic',
    'analysis_final_altitude_m', 'analysis_altitude_drift_m', 'analysis_altitude_rmse_m',
    'analysis_horizontal_speed_mean_m_s', 'analysis_vertical_speed_mean_m_s',
    'analysis_ref_altitude_min_m', 'analysis_ref_altitude_max_m',
    'analysis_ref_north_range_m', 'analysis_ref_east_range_m',
    'analysis_ref_north_velocity_rms_m_s', 'analysis_ref_east_velocity_rms_m_s',
    'analysis_ref_down_velocity_rms_m_s',
]
print('run:', run)
print(summary[[c for c in cols if c in summary.columns]].to_string(index=False))

print('\nfailed/aborted:')
failed = summary[(summary['safety_ok'] != True) | (summary['quality_ok_basic'] != True)]
print(failed[['scenario', 'abort_reason', 'safety_ok', 'quality_ok_basic']].to_string(index=False))

sample = pd.read_csv(summary.iloc[0]['analysis_csv'])
extra_cols = [c for c in sample.columns if c.startswith('ref_') or c.startswith('imu_') or c.startswith('derived_')]
print('\nextra/ref column availability:')
print(sample[extra_cols].notna().mean().sort_values().to_string())
PY
```

## Expected Reading

The first success criterion is that `C00_position_hold_25m` has much lower
altitude drift than the old open-loop `N00_hover_hold_0p5192` data. If this is
true, v14 is the better dataset family for the first upper-level MPC/PINN model.
