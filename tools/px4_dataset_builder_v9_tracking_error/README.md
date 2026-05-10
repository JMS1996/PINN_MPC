# PX4 Dataset Builder v9 Tracking Error

This builder converts v16 recovery runs into a Colab-ready one-step dynamics dataset.

v9 keeps the v8 position-state columns:

- `local_north_m`
- `local_east_m`
- `relative_altitude_m`
- velocity, attitude, and body-rate states

and adds explicit tracking-error input features:

- `e_ref_north_m = ref_north_m - local_north_m`
- `e_ref_east_m = ref_east_m - local_east_m`
- `e_ref_alt_m = -ref_down_m - relative_altitude_m`
- `e_ref_yaw_deg = wrap(ref_yaw_deg - yaw_deg)`
- `e_ref_vn_m_s = ref_north_m_s - vel_north_m_s`
- `e_ref_ve_m_s = ref_east_m_s - vel_east_m_s`
- `e_ref_vd_m_s = ref_down_m_s - vel_down_m_s`

These are model inputs, not targets. They make recovery regimes explicit when the vehicle has been displaced from the current PX4 setpoint.

## Build

Inside WSL:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_dataset_builder_v9_tracking_error
python3 build_px4_dataset_v9.py --config config.json --latest-n 5
```

Output:

```text
~/px4_datasets/processed/px4_phase1_recovery_tracking_error_dataset_v9_<timestamp>/
```

Then train:

```text
notebooks/current/PINN/PX4_Phase1_ClosedLoop_Dynamics_PINN_Training_v18_tracking_error.ipynb
```
