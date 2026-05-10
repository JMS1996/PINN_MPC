# PX4 Phase 1 Nominal Rate Dataset v12

`v12` is the current active collector for nominal dynamics data.

It keeps the intended control hierarchy:

```text
future PINN-MPC layer -> PX4 rate-controller setpoints -> PX4 low-level control -> Gazebo plant
```

## Key Fix From v11

`v11` collected all scenarios successfully, but altitude drift accumulated because Offboard fixed-thrust mode started before the vehicle had fully settled near hover.

`v12` adds a stricter Offboard start gate:

- takeoff reaches at least `22 m`
- vehicle is near `25 m`
- `abs(vertical speed) < 0.25 m/s`
- condition is sustained for `2 s`

This makes the collected nominal dynamics closer to the intended local hover regime.

## Run All Nominal Scenarios

Inside WSL Ubuntu:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v12
python3 collect_px4_phase1_v12.py --config scenarios.yaml
```

Run one scenario:

```bash
python3 collect_px4_phase1_v12.py --config scenarios.yaml --scenario N01_pitch_rate_doublet_5dps
```

## Quick Summary

```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path

root = Path.home() / 'px4_datasets'
runs = sorted(root.glob('px4_phase1_standard_vtol_nominal_rate_dataset_v12_*'))
run = runs[-1]
summary = pd.read_csv(run / 'summary.csv')
cols = [
    'scenario', 'rows_raw', 'abort_reason', 'safety_ok',
    'analysis_final_altitude_m', 'analysis_altitude_drift_m',
    'analysis_altitude_rmse_m',
    'analysis_roll_rate_rms_deg_s',
    'analysis_pitch_rate_rms_deg_s',
    'analysis_yaw_rate_rms_deg_s',
    'analysis_ref_roll_rate_rms_deg_s',
    'analysis_ref_pitch_rate_rms_deg_s',
    'analysis_ref_yaw_rate_rms_deg_s',
    'analysis_ref_thrust_min', 'analysis_ref_thrust_max',
    'quality_ok_basic'
]
print('run:', run)
print(summary[[c for c in cols if c in summary.columns]].to_string(index=False))
PY
```

## Training Use

Use `telemetry_analysis.csv` first. Exclude scenarios with:

- `safety_ok=False`
- large altitude drift
- missing reference columns
- very small actual rate response for the commanded axis

Disturbance cases should not be mixed into the first nominal dynamics model. They belong to evaluation and robust-controller testing.
