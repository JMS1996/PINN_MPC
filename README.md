# PINN MPC Research Workspace

This repository tracks the research code, notebooks, and reproducibility notes for PINN-based aircraft/vehicle dynamics modeling and mission-level planning experiments.

## Current Direction

The active research direction has been rebooted around:

```text
PX4 multicopter closed-loop response
-> task-aware PINN surrogate
-> rollout-based ETA / error / risk prediction
-> dynamics-aware mission planning cost
```

The goal is no longer to make a low-level PINN-MPC controller first. The near-term goal is to learn a reliable PX4 closed-loop task response surrogate and use it as a mission-cost predictor.

Start here:

- New project workspace: `projects/px4_task_aware_mission_planning/`
- Reboot plan: `docs/PX4_RESEARCH_REBOOT_PLAN.md`
- Phase 1 history plan: `docs/PX4_PHASE1_RESEARCH_PLAN.md`
- Latest task rollout notebook: `notebooks/current/MPC/PX4_Phase1_TaskAware_PINN_Rollout_Simulator_v1.ipynb`

## Repository Structure

```text
PINN_MPC/
├── docs/
│   ├── PX4_RESEARCH_REBOOT_PLAN.md
│   └── PX4_PHASE1_RESEARCH_PLAN.md
├── notebooks/
│   └── current/
│       ├── PINN/
│       └── MPC/
├── projects/
│   └── px4_task_aware_mission_planning/
└── tools/
    ├── archive/
    ├── px4_phase1_v16_recovery_tracking_error/
    └── px4_dataset_builder_v9_tracking_error/
```

## Historical Code

Earlier work is intentionally preserved:

- C172 / JSBSim trim and PINN-MPC experiments
- PX4 rate-setpoint data collection experiments
- PX4 closed-loop dynamics training experiments
- PINN-MPC recovery experiments

These are useful as research history, but the new active project should use the `projects/px4_task_aware_mission_planning/` workflow.

## Data, Results, and Checkpoints

Large files are not tracked in Git:

- PX4 datasets
- trained checkpoints
- Colab result folders
- generated logs and plots

Use Google Drive or local external storage for large artifacts. Git should contain source notebooks, scripts, configs, and small documentation.

## License

Apache License 2.0
