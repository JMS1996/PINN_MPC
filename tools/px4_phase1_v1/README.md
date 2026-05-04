# PX4 Phase 1 Data Collection v1

This is the new PX4/Gazebo research line starting from version `v1`.

Purpose:

- Validate PX4 Gazebo data collection.
- Launch a fresh PX4 process for each scenario.
- Save raw telemetry, analysis-window telemetry, quality metrics, metadata, and quicklook plots.
- Keep data collection separate from PINN training and controller evaluation.

## Run

Inside WSL Ubuntu:

```bash
python3 -m pip install --user -r /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v1/requirements.txt

cd /mnt/c/Users/jangm/Documents/New\ project/drive_upload_code/PINN_MPC/tools/px4_phase1_v1
python3 collect_px4_phase1_v1.py --config scenarios.yaml
```

Run only one scenario:

```bash
python3 collect_px4_phase1_v1.py --config scenarios.yaml --scenario W0_nominal_takeoff_hold_45s
```

## Output

Outputs are written to:

```text
~/px4_datasets/px4_phase1_standard_vtol_v1_<timestamp>/
```

Each scenario has its own folder:

```text
<scenario>/
  telemetry_raw.csv
  telemetry_analysis.csv
  metadata.json
  px4_stdout.log
  quicklook.png
```

The run folder also contains:

```text
run_metadata.json
summary.csv
```

## Why Fresh Process Per Scenario?

The earlier v51 collector executed multiple scenarios in one PX4 instance. The second scenario inherited vehicle state from the first scenario, so takeoff altitude appeared to accumulate. This v1 collector starts and stops PX4 for every scenario to prevent state leakage.

## First Quality Checks

Open `summary.csv` and verify:

- `rows_raw` matches roughly `duration_s / sample_period_s`.
- `rows_analysis` is nonzero.
- `quality_ok_basic` is `True`.
- `analysis_final_altitude_m` stays near `target_altitude_m`.
- `analysis_pitch_abs_mean_deg` is small during nominal hold.

Disturbances and maneuver commands should be added in `v2` after this baseline is verified.
