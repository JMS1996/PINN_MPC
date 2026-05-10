# PX4 Dataset Builder v5 Closed Loop

Builds a supervised one-step dynamics dataset from
`px4_phase1_v14_closed_loop` telemetry.

This version changes the model contract from the older open-loop rate/thrust
form to the closed-loop upper-controller form:

```text
x_t, setpoint_t, prev_setpoint_t, dsetpoint_t, dt_s -> x_{t+1}
```

The action/setpoint columns are:

```text
ref_north_m
ref_east_m
ref_down_m
ref_north_m_s
ref_east_m_s
ref_down_m_s
ref_yaw_deg
```

This matches the intended Phase 1 controller hierarchy:

```text
future PINN-MPC layer -> PX4 position/velocity/yaw offboard setpoint -> PX4 cascaded controllers -> Gazebo plant
```

## Run In WSL

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_dataset_builder_v5_closed_loop
python3 build_px4_dataset_v5.py --config config.json --latest-n 1
```

Use the latest five v14 collection runs when available:

```bash
python3 build_px4_dataset_v5.py --config config.json --latest-n 5
```

Outputs are written to:

```text
~/px4_datasets/processed/px4_phase1_closed_loop_dynamics_dataset_v5_<timestamp>/
```

## Quick Verification

```bash
python3 - <<'PY'
import pandas as pd
from pathlib import Path

root = Path.home() / 'px4_datasets' / 'processed'
run = sorted(root.glob('px4_phase1_closed_loop_dynamics_dataset_v5_*'))[-1]
print('dataset:', run)
print(pd.read_csv(run / 'dataset_summary.csv').to_string(index=False))

df = pd.read_csv(run / 'all_samples.csv')
print('rows:', len(df))
print('split counts:')
print(df['split'].value_counts().to_string())
print('action columns:')
print([c for c in df.columns if c.startswith('u_ref_')])
print('dx altitude abs max:', df['dx_relative_altitude_m'].abs().max())
print('C09 split:')
print(df[df['scenario'].eq('C09_mixed_position_sequence')]['split'].value_counts().to_string())
PY
```
