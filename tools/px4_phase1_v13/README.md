# PX4 Phase 1 Nominal Rate Dataset v13 IMU Auxiliary

`v13` keeps the v12 nominal multicopter-hover rate/thrust scenarios, but adds
extra telemetry columns for the next dynamics-model iteration.

Control hierarchy is unchanged:

```text
future PINN-MPC layer -> PX4 rate-controller setpoints -> PX4 low-level control -> Gazebo plant
```

## Difference From v12

Additional logged columns when MAVSDK exposes IMU telemetry:

- `imu_accel_forward_m_s2`
- `imu_accel_right_m_s2`
- `imu_accel_down_m_s2`
- `imu_angular_rate_forward_rad_s`
- `imu_angular_rate_right_rad_s`
- `imu_angular_rate_down_rad_s`

Additional derived columns from finite differences:

- `derived_accel_north_m_s2`
- `derived_accel_east_m_s2`
- `derived_accel_down_m_s2`
- `derived_roll_accel_rad_s2`
- `derived_pitch_accel_rad_s2`
- `derived_yaw_accel_rad_s2`

These are intended for auxiliary training targets and diagnostics. They do not
mean the later MPC runtime input must include every field.

## Run All Scenarios

Inside WSL Ubuntu:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v13
python3 collect_px4_phase1_v13.py --config scenarios.yaml
```

Run one scenario first:

```bash
python3 collect_px4_phase1_v13.py --config scenarios.yaml --scenario N06_yaw_rate_doublet_20dps
```

## Verify Latest Run

```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path

root = Path.home() / 'px4_datasets'
runs = sorted(root.glob('px4_phase1_standard_vtol_nominal_rate_dataset_v13_imu_aux_*'))
run = runs[-1]
summary = pd.read_csv(run / 'summary.csv')
cols = [
    'scenario', 'rows_analysis', 'abort_reason', 'safety_ok', 'quality_ok_basic',
    'analysis_altitude_drift_m', 'analysis_altitude_rmse_m',
    'analysis_roll_rate_rms_deg_s', 'analysis_pitch_rate_rms_deg_s', 'analysis_yaw_rate_rms_deg_s',
    'analysis_imu_accel_down_rms_m_s2', 'analysis_derived_accel_down_rms_m_s2',
    'analysis_derived_yaw_accel_rms_rad_s2',
]
print('run:', run)
print(summary[[c for c in cols if c in summary.columns]].to_string(index=False))

sample = pd.read_csv(summary.iloc[0]['analysis_csv'])
check_cols = [c for c in sample.columns if c.startswith('imu_') or c.startswith('derived_')]
print('\nextra columns:', check_cols)
print(sample[check_cols].notna().mean().sort_values().to_string())
PY
```
