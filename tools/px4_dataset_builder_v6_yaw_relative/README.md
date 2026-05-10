# PX4 Dataset Builder v6 Yaw Relative

Builds a supervised one-step dynamics dataset from
`px4_phase1_v15_closed_loop_yaw_relative` telemetry.

Compared with v5, this version uses v15 data where yaw commands are interpreted
as offsets from the vehicle yaw at offboard start. The processed dataset keeps
both:

```text
ref_yaw_deg
ref_yaw_offset_deg
```

The model contract remains:

```text
x_t, setpoint_t, prev_setpoint_t, dsetpoint_t, dt_s -> x_{t+1}
```

## Run In WSL

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_dataset_builder_v6_yaw_relative
python3 build_px4_dataset_v6.py --config config.json --latest-n 1
```

Use the latest five v15 collection runs when available:

```bash
python3 build_px4_dataset_v6.py --config config.json --latest-n 5
```

Outputs are written to:

```text
~/px4_datasets/processed/px4_phase1_closed_loop_yawrel_dynamics_dataset_v6_<timestamp>/
```

## Quick Verification

```bash
python3 - <<'PY'
import json
import pandas as pd
from pathlib import Path

root = Path.home() / 'px4_datasets' / 'processed'
run = sorted(root.glob('px4_phase1_closed_loop_yawrel_dynamics_dataset_v6_*'))[-1]
with open(run / 'metadata.json') as f:
    meta = json.load(f)
print('dataset:', run)
print('run_count:', meta.get('run_count'))
print(pd.read_csv(run / 'dataset_summary.csv').to_string(index=False))

df = pd.read_csv(run / 'all_samples.csv')
print('rows:', len(df))
print('action columns:')
print([c for c in df.columns if c.startswith('u_ref_')])
print('yaw offset range:', df['u_ref_yaw_offset_deg'].min(), df['u_ref_yaw_offset_deg'].max())
PY
```
