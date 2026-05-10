# PX4 Gazebo VTOL Data Collection v51

This folder is the first PX4/Gazebo data collection scaffold for the mission-planning research path.

It separates **simulation data collection** from **PINN training**:

1. Run PX4 Gazebo SITL in WSL2 Ubuntu.
2. Connect with MAVSDK.
3. Save telemetry CSV and scenario metadata.
4. Train/evaluate PINN-MPC later from the saved dataset.

## Files

- `collect_px4_gazebo_vtol_v51.py`: headless PX4 Gazebo telemetry collector.
- `scenarios_v51.yaml`: minimal nominal takeoff/hold scenarios.
- `requirements_v51.txt`: Python package requirements for the collector.

## One-Time WSL/PX4 Setup

From Ubuntu inside WSL:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project
bash scripts/setup_px4_wsl_step2_ubuntu.sh
```

Then install the collector dependencies:

```bash
python3 -m pip install --user -r /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_data_collection/requirements_v51.txt
```

## Run Collection

From Ubuntu inside WSL:

```bash
cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_data_collection
python3 collect_px4_gazebo_vtol_v51.py --config scenarios_v51.yaml
```

The script launches:

```bash
HEADLESS=1 make px4_sitl gz_standard_vtol
```

inside `~/src/PX4-Autopilot`, then saves CSV files under:

```text
~/px4_datasets/<run_name>_<timestamp>/
```

## If PX4 Is Already Running

Use:

```bash
python3 collect_px4_gazebo_vtol_v51.py --config scenarios_v51.yaml --no-launch
```

## First Success Criteria

Do not worry about PINN yet. The first pass is successful if:

- PX4 launches headless.
- MAVSDK prints `vehicle connected`.
- One telemetry CSV is saved.
- `summary.csv` has non-empty row counts.

After that, add controlled maneuvers and disturbance cases in a new version.
