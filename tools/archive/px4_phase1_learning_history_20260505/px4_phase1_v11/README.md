# PX4 Phase 1 Nominal Rate Dataset v11

Version `v11` uses the calibrated hover thrust:

```text
HOVER_THRUST = 0.5192
```

It collects nominal attitude-rate/thrust excitation data for training a local dynamics model:

```text
state_t, [roll_rate_sp, pitch_rate_sp, yaw_rate_sp, thrust_sp] -> state_t+1
```

No disturbance injection is included in this version. Disturbances should be reserved for evaluation after a nominal model exists.

## Scenarios

- `N00_hover_hold_0p5192`
- `N01_pitch_rate_doublet_5dps`
- `N02_pitch_rate_doublet_10dps`
- `N03_roll_rate_doublet_5dps`
- `N04_roll_rate_doublet_10dps`
- `N05_yaw_rate_doublet_10dps`
- `N06_yaw_rate_doublet_20dps`
- `N07_thrust_step_pm010`
- `N08_thrust_step_pm020`
- `N09_pitch_thrust_coupled`
- `N10_roll_yaw_coupled`
- `N11_mixed_sequence`

## Run All

Inside WSL Ubuntu:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v11
python3 collect_px4_phase1_v11.py --config scenarios.yaml
```

Run one scenario:

```bash
python3 collect_px4_phase1_v11.py --config scenarios.yaml --scenario N01_pitch_rate_doublet_5dps
```

## Quick Summary

```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path

root = Path.home() / 'px4_datasets'
runs = sorted(root.glob('px4_phase1_standard_vtol_nominal_rate_dataset_v11_*'))
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

## First Pass Criteria

- `quality_ok_basic=True`
- no safety abort for most scenarios
- altitude remains inside safety bounds
- reference RMS is nonzero for the intended excitation axis
- actual body-rate RMS responds to the reference

If a scenario aborts, keep the CSV but exclude that scenario from training or reduce its excitation amplitude in the next version.
