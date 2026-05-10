# PX4 Phase 1 Closed-Loop Dataset v15 Yaw Relative

`v15` keeps the v14 closed-loop position/velocity offboard data collection
strategy, but fixes the yaw-reference issue.

In v14, `yaw_deg: 0` was an absolute yaw command. If the aircraft started near
90 deg, a simple hover scenario could unintentionally command a large yaw turn.
In v15, scenario yaw commands are interpreted as offsets from the vehicle yaw at
offboard start:

```text
actual yaw command = yaw_at_offboard_start + yaw_offset_deg
```

The telemetry logs both `ref_yaw_deg` and `ref_yaw_offset_deg`.

## Run One Scenario First

Inside WSL Ubuntu:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v15_closed_loop_yaw_relative
python3 collect_px4_phase1_v15.py --config scenarios.yaml --scenario C00_position_hold_25m
```

## Run All Scenarios

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v15_closed_loop_yaw_relative
python3 collect_px4_phase1_v15.py --config scenarios.yaml
```

For more data:

```bash
for i in $(seq 1 5); do
  echo "===== v15 yaw-relative collection run $i / 5 ====="
  python3 collect_px4_phase1_v15.py --config scenarios.yaml
done
```

## Verify Latest Run

```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path

root = Path.home() / 'px4_datasets'
runs = sorted(root.glob('px4_phase1_standard_vtol_closed_loop_yawrel_dataset_v15_*'))
if not runs:
    raise SystemExit('No v15 runs found.')

run = runs[-1]
summary = pd.read_csv(run / 'summary.csv')
cols = [
    'scenario', 'rows_analysis', 'abort_reason', 'safety_ok', 'quality_ok_basic',
    'analysis_final_altitude_m', 'analysis_altitude_drift_m', 'analysis_altitude_rmse_m',
    'analysis_ref_altitude_min_m', 'analysis_ref_altitude_max_m',
    'analysis_ref_north_range_m', 'analysis_ref_east_range_m',
]
print('run:', run)
print(summary[[c for c in cols if c in summary.columns]].to_string(index=False))

sample = pd.read_csv(summary.iloc[0]['analysis_csv'])
print('\nyaw reference columns:')
print(sample[['yaw_deg', 'ref_yaw_deg', 'ref_yaw_offset_deg', 'ref_yaw_base_deg']].describe().to_string())
PY
```

Expected first check: `C00_position_hold_25m` should keep
`ref_yaw_offset_deg` at zero and `ref_yaw_deg` near the initial yaw, not force
the aircraft to absolute zero yaw.
