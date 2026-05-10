# PX4 Dataset Builder v3

Builds a multi-run supervised dynamics dataset from `px4_phase1_v13` telemetry.

The builder does not train a model. It prepares Colab-ready CSV files:

```text
x_t, u_t, prev_u_t, du_t, dt_s -> x_{t+1}, dx
```

v3 also keeps v13 auxiliary acceleration targets:

```text
aux_derived_accel_north_m_s2
aux_derived_accel_east_m_s2
aux_derived_accel_down_m_s2
aux_derived_roll_accel_rad_s2
aux_derived_pitch_accel_rad_s2
aux_derived_yaw_accel_rad_s2
```

If MAVSDK IMU columns are populated for a scenario, they are also included as
optional `aux_imu_*` columns. These are auxiliary training targets, not required
runtime MPC inputs.

The builder skips incomplete run folders that do not contain `summary.csv`.

## Run In WSL

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_dataset_builder_v3
python3 build_px4_dataset_v3.py --config config.json
```

Use only the latest 5 completed v13 runs:

```bash
python3 build_px4_dataset_v3.py --config config.json --latest-n 5
```

Outputs are written to:

```text
~/px4_datasets/processed/px4_phase1_rate_dynamics_dataset_v3_imu_aux_<timestamp>/
```

Important files:

- `all_samples.csv`
- `train.csv`
- `val.csv`
- `test.csv`
- `filter_report.csv`
- `dataset_summary.csv`
- `metadata.json`

## Quick Verification

```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path

root = Path.home() / 'px4_datasets' / 'processed'
run = sorted(root.glob('px4_phase1_rate_dynamics_dataset_v3_imu_aux_*'))[-1]
print('dataset:', run)
print(pd.read_csv(run / 'dataset_summary.csv').to_string(index=False))

df = pd.read_csv(run / 'all_samples.csv')
aux_cols = [c for c in df.columns if c.startswith('aux_')]
print('rows:', len(df))
print('aux cols:', aux_cols)
print((df[aux_cols].notna().mean()).to_string())
PY
```

## Colab Use

Upload or mount the processed folder, then read:

```python
import pandas as pd

train = pd.read_csv('/content/drive/MyDrive/.../train.csv')
val = pd.read_csv('/content/drive/MyDrive/.../val.csv')
test = pd.read_csv('/content/drive/MyDrive/.../test.csv')

feature_cols = [c for c in train.columns if c.startswith(('x_', 'u_', 'prev_u_', 'du_'))] + ['dt_s']
target_cols = [c for c in train.columns if c.startswith('dx_')]
aux_cols = [c for c in train.columns if c.startswith('aux_') and train[c].notna().mean() > 0.95]
```
