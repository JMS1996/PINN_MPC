# PX4 Dataset Builder v2

Builds a multi-run supervised dynamics dataset from `px4_phase1_v12` telemetry.

The builder does not train a model. It prepares Colab-ready CSV files:

```text
x_t, u_t, prev_u_t, du_t, dt -> x_{t+1}, dx
```

## Why Row Filtering

Long open-loop thrust hover drifts because Offboard rate/thrust setpoints bypass
PX4 altitude hold. That drift is still useful dynamics data, but low-altitude or
large-attitude samples should not define the first local hover model.

Default filter:

- `10 m <= relative_altitude_m <= 35 m`
- `abs(roll_deg) <= 25`
- `abs(pitch_deg) <= 25`
- body-rate magnitude below `120 deg/s`
- sample interval near `0.05 s`
- `quality_ok_basic == True`

## Run In WSL

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_dataset_builder_v2
python3 build_px4_dataset_v2.py --config config.json
```

Use only the latest 6 runs:

```bash
python3 build_px4_dataset_v2.py --config config.json --latest-n 6
```

Use specific runs:

```bash
python3 build_px4_dataset_v2.py \
  --config config.json \
  --run-dir ~/px4_datasets/px4_phase1_standard_vtol_nominal_rate_dataset_v12_20260505_081854 \
  --run-dir ~/px4_datasets/px4_phase1_standard_vtol_nominal_rate_dataset_v12_20260506_181845
```

Outputs are written to:

```text
~/px4_datasets/processed/px4_phase1_rate_dynamics_dataset_v2_multirun_<timestamp>/
```

Important files:

- `all_samples.csv`
- `train.csv`
- `val.csv`
- `test.csv`
- `filter_report.csv`
- `dataset_summary.csv`
- `metadata.json`

## Colab Use

Upload or mount the processed folder, then read:

```python
import pandas as pd

train = pd.read_csv('/content/drive/MyDrive/.../train.csv')
val = pd.read_csv('/content/drive/MyDrive/.../val.csv')
test = pd.read_csv('/content/drive/MyDrive/.../test.csv')

feature_cols = [c for c in train.columns if c.startswith(('x_', 'u_', 'prev_u_', 'du_'))] + ['dt_s']
target_cols = [c for c in train.columns if c.startswith('dx_')]
```
