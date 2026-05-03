# Results

Large experiment outputs are stored outside this repository.

## External Storage

- Storage: Google Drive
- Root folder: `MyDrive/Colab Result`
- Contents: experiment outputs, logs, checkpoints, and generated figures
- Repository policy: do not commit large generated files to GitHub

## Folder Policy

Generated outputs should use this structure:

```text
MyDrive/Colab Result/
  PINN_MPC/
    <experiment_name>/
      archive/
        <YYYYMMDD_HHMMSS>/
          RUN_MANIFEST.json
          metrics/logs/figures/config files
      latest/
      LATEST_RUN.json
```

Each notebook run should save into a new timestamped `archive` folder so old
results are preserved. `LATEST_RUN.json` points to the newest run for quick
lookup.

Current experiment name:

```text
v7_alpha_throttle_snc_D5_2input_MPPI_PID_v38_settle_trim_start
```

Current working MPC notebook:

```text
notebooks/current/MPC/PINN_MPC_v7_alpha_throttle_snc_D5_2input_MPPI_PID_v38_settle_trim_start.ipynb
```

## Notes

Keep source notebooks in GitHub. Keep large outputs and checkpoints in
`MyDrive/Colab Result` or model checkpoint folders on Google Drive.

## Latest S&C Result Summary

The latest v38 settle-trim-start notebook uses the v7 alpha-throttle PINN and upgrades MPPI from
elevator-only to two-input `[elevator, throttle]` control. The fixed
`D5_smooth_doublet` disturbance sweep remains the comparison setup, but throttle
now gives the predictive controller an explicit energy-management channel. v34
also cleans up checkpoint discovery for both `/content/drive/MyDrive` and
`/content/drive` Drive layouts.

