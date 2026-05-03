# Notebook Naming Rule

Use stable, descriptive names so each notebook tells us the model, role, task, controller set, run mode, and revision.

## Format

```text
{model_family}_{model_version}_{task_or_guidance}_{controllers}_{mode}_{revision}.ipynb
```

## Fields

- `model_family`: `PINN_MPC`, `PINN`, `PID`, `CBBA`, or `IL`
- `model_version`: dynamics/checkpoint version, for example `v6_alpha`
- `task_or_guidance`: main experiment target, for example `altitude_guidance`, `task_guidance`, `wind_disturbance`
- `controllers`: controller group, for example `PID_RS_CEM_MPPI`, `MPPI`, `PID_MPPI`
- `mode`: `debug`, `single`, `full`, `ablation`, or `train`
- `revision`: notebook implementation revision, for example `v5`

## Current Example

```text
PINN_MPC_v6_alpha_altitude_guidance_PID_RS_CEM_MPPI_debug_v5.ipynb
```

This means:

- frozen PINN dynamics model is `v6_alpha`
- notebook role is PINN-linked MPC
- guidance target is altitude tracking
- comparison controllers are PID, Random Shooting, CEM, and MPPI
- default run mode is debug
- implementation revision is v5
