# PX4 Dataset Builder v4

Builds a filtered multi-run supervised dynamics dataset from `px4_phase1_v13`
telemetry.

Compared with v3, this version adds:

- one-step outlier filtering for state deltas
- auxiliary acceleration outlier filtering
- partial holdout for `N11_mixed_sequence` instead of making it entirely unseen

The runtime model contract remains:

```text
x_t, u_t, prev_u_t, du_t, dt_s -> x_{t+1}
```

The processed CSV also includes auxiliary targets:

```text
aux_derived_accel_north_m_s2
aux_derived_accel_east_m_s2
aux_derived_accel_down_m_s2
aux_derived_roll_accel_rad_s2
aux_derived_pitch_accel_rad_s2
aux_derived_yaw_accel_rad_s2
```

## Run In WSL

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_dataset_builder_v4
python3 build_px4_dataset_v4.py --config config.json --latest-n 5
```

Outputs are written to:

```text
~/px4_datasets/processed/px4_phase1_rate_dynamics_dataset_v4_filtered_imu_aux_<timestamp>/
```

## Quick Verification

```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path

root = Path.home() / 'px4_datasets' / 'processed'
run = sorted(root.glob('px4_phase1_rate_dynamics_dataset_v4_filtered_imu_aux_*'))[-1]
print('dataset:', run)
print(pd.read_csv(run / 'dataset_summary.csv').to_string(index=False))

df = pd.read_csv(run / 'all_samples.csv')
print('rows:', len(df))
print('dx altitude abs max:', df['dx_relative_altitude_m'].abs().max())
print('N11 split:')
print(df[df['scenario'].eq('N11_mixed_sequence')]['split'].value_counts().to_string())
PY
```
