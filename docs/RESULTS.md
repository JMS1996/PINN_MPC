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
v6_alpha_snc_multi_maneuver_integral_terminal_OptPID100_MPPI_fast_v31_fix3
```

Current working MPC notebook:

```text
notebooks/current/MPC/PINN_MPC_v6_alpha_snc_multi_maneuver_integral_terminal_OptPID100_MPPI_fast_v31_fix3.ipynb
```

## Notes

Keep source notebooks in GitHub. Keep large outputs and checkpoints in
`MyDrive/Colab Result` or model checkpoint folders on Google Drive.

## Latest S&C Result Summary

The latest fast multi-maneuver screen compares a 100-trial Optuna PID baseline
against integral-terminal PINN-MPPI on three pitch-axis S&C references and
signed disturbances. PID gives better pitch reference RMSE, while MPPI gives
better altitude preservation and lower final altitude error.

