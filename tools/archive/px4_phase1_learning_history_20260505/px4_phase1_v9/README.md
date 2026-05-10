# PX4 Phase 1 Rate-Setpoint Collection v9

Version `v9` narrows hover thrust between v8's falling `0.510` case and climbing `0.520` case.

This version adds:

- safety aborts for altitude, attitude, and body-rate limits
- wait for takeoff altitude before entering Offboard rate/thrust mode
- hover-thrust calibration scenarios
- smaller rate excitations
- safer default thrust candidates

## Architecture

```text
Future PINN-MPC layer -> PX4 rate controller setpoints -> PX4 low-level control -> Gazebo plant
```

Collected action candidates:

- `ref_roll_rate_deg_s`
- `ref_pitch_rate_deg_s`
- `ref_yaw_rate_deg_s`
- `ref_thrust`

## Run Thrust Calibration First

Run one candidate at a time:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v9
python3 collect_px4_phase1_v9.py --config scenarios.yaml --scenario T0_thrust_cal_0514
python3 collect_px4_phase1_v9.py --config scenarios.yaml --scenario T1_thrust_cal_0516
python3 collect_px4_phase1_v9.py --config scenarios.yaml --scenario T2_thrust_cal_0518
python3 collect_px4_phase1_v9.py --config scenarios.yaml --scenario T3_thrust_cal_0519
```

Pick the thrust with the smallest `analysis_altitude_drift_m` and no safety abort.

## Quick Summary Check

```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path

root = Path.home() / 'px4_datasets'
runs = sorted(root.glob('px4_phase1_standard_vtol_rate_thrust_cal_v9_*'))
rows = []
for run in runs[-10:]:
    p = run / 'summary.csv'
    if p.exists():
        df = pd.read_csv(p)
        df.insert(0, 'run', run.name)
        rows.append(df)
out = pd.concat(rows, ignore_index=True)
cols = [
    'run', 'scenario', 'rows_raw', 'rows_analysis', 'abort_reason', 'safety_ok',
    'analysis_final_altitude_m', 'analysis_altitude_drift_m',
    'analysis_altitude_rmse_m', 'analysis_ref_thrust_min', 'analysis_ref_thrust_max',
    'quality_ok_basic'
]
print(out[[c for c in cols if c in out.columns]].to_string(index=False))
PY
```

## Then Run Safe Rate Excitation

After choosing hover thrust, update `nominal_thrust` and the scenario thrust values in `scenarios.yaml`, then run:

```bash
python3 collect_px4_phase1_v9.py --config scenarios.yaml --scenario R1_pitch_rate_doublet_safe
```

Do not use v4 runaway data for training.
