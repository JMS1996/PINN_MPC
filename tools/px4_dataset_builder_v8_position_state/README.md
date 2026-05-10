# PX4 Dataset Builder v8 Position State

This builder converts PX4 Phase 1 closed-loop yaw-relative runs into a Colab-ready one-step dynamics dataset.

v8 keeps the v7 contiguous block split and adds scenario-local horizontal position states:

- `local_north_m`
- `local_east_m`

Those position states are derived from telemetry velocity with trapezoidal integration inside each scenario. This is intended for the next PINN-MPC step where the learned model predicts position directly instead of letting the MPC bolt on a separate velocity integrator.

## Build Dataset

Run this inside WSL:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_dataset_builder_v8_position_state
python3 build_px4_dataset_v8.py --config config.json --latest-n 5
```

The output is written under:

```text
~/px4_datasets/processed/px4_phase1_closed_loop_yawrel_position_state_dataset_v8_<timestamp>/
```

## Expected Source Runs

By default the builder reads:

```text
~/px4_datasets/px4_phase1_standard_vtol_closed_loop_yawrel_dataset_v15_*
```

Use `--source-glob` if the source directory pattern changes.

## Next Step

After building v8, train:

```text
notebooks/current/PINN/PX4_Phase1_ClosedLoop_Dynamics_PINN_Training_v17_position_state.ipynb
```

Then run:

```text
notebooks/current/MPC/PX4_Phase1_ClosedLoop_PINN_MPC_v2_position_state.ipynb
```
