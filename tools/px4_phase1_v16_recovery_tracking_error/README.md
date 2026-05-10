# PX4 Phase 1 v16 Recovery Tracking-Error Collection

This collector reuses the v15 yaw-relative PX4/Gazebo closed-loop workflow, but the scenarios are focused on recovery data.

The point of this dataset is to expose the learned dynamics model to states where:

```text
current state != PX4 setpoint
```

and PX4's internal closed-loop controller brings the vehicle back toward the commanded setpoint.

This approximates disturbance recovery without injecting external forces into Gazebo. The vehicle is first displaced with an offboard position setpoint, then the setpoint is returned to the nominal hover target.

## Run

Inside WSL:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v16_recovery_tracking_error
python3 collect_px4_phase1_v16.py --config scenarios.yaml
```

For repeated runs:

```bash
for i in $(seq 1 5); do
  echo "===== v16 recovery collection run $i / 5 ====="
  python3 collect_px4_phase1_v16.py --config scenarios.yaml
done
```

Outputs are written under:

```text
~/px4_datasets/px4_phase1_standard_vtol_recovery_tracking_error_dataset_v16_<timestamp>/
```

## Next

Build the tracking-error training dataset:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_dataset_builder_v9_tracking_error
python3 build_px4_dataset_v9.py --config config.json --latest-n 5
```

Then train:

```text
notebooks/current/PINN/PX4_Phase1_ClosedLoop_Dynamics_PINN_Training_v18_tracking_error.ipynb
```
