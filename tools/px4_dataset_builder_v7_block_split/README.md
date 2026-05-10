# PX4 Dataset Builder v7 Block Split

Builds a supervised one-step dynamics dataset from v15 yaw-relative closed-loop
telemetry, but assigns train/val/test splits by contiguous time blocks instead
of random rows.

Why this matters:

```text
row-random split -> good one-step metrics, broken rollout evaluation
block split      -> contiguous validation/test windows remain available
```

The action contract remains:

```text
x_t, setpoint_t, prev_setpoint_t, dsetpoint_t, dt_s -> x_{t+1}
```

Setpoints include:

```text
ref_north_m
ref_east_m
ref_down_m
ref_north_m_s
ref_east_m_s
ref_down_m_s
ref_yaw_deg
ref_yaw_offset_deg
```

## Run In WSL

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_dataset_builder_v7_block_split
python3 build_px4_dataset_v7.py --config config.json --latest-n 5
```

Outputs are written to:

```text
~/px4_datasets/processed/px4_phase1_closed_loop_yawrel_block_dataset_v7_<timestamp>/
```

## Quick Verification

```bash
python3 - <<'PY'
import json
import pandas as pd
from pathlib import Path

root = Path.home() / 'px4_datasets' / 'processed'
run = sorted(root.glob('px4_phase1_closed_loop_yawrel_block_dataset_v7_*'))[-1]
with open(run / 'metadata.json') as f:
    meta = json.load(f)
df = pd.read_csv(run / 'all_samples.csv')
summary = pd.read_csv(run / 'dataset_summary.csv')

print('dataset:', run)
print('run_count:', meta.get('run_count'))
print(summary.to_string(index=False))
print('\nblock counts:')
print(df.groupby('split')['block_id'].nunique().to_string())
print('\nlongest contiguous windows by split:')
for split, part in df.groupby('split'):
    best = 0
    for _, g in part.sort_values(['source_run', 'scenario', 'sample_index']).groupby(['source_run', 'scenario', 'block_id']):
        best = max(best, len(g))
    print(split, best)
PY
```
