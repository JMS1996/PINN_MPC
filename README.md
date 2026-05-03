# PINN MPC

PINN-based model training and MPC experiment notebooks.

## Current Notebooks

The latest working notebooks are kept here so they are easy to find first:

- Training: `notebooks/current/PINN/PINN_model_training_auto_v6_alpha_state.ipynb`
- MPC: `notebooks/current/MPC/PINN_MPC_v6_alpha_snc_smooth_pitch_doublet_nominal_alt_hold_horizon_PID_MPPI_Optuna_v20.ipynb`

For VS Code usage, start with `docs/VSCODE_COLAB_RUN.md`.

Research status and notebook history are summarized in `docs/RESEARCH_PROGRESS.md`.

## Notebook Naming

Use the notebook naming rule in `docs/NOTEBOOK_NAMING.md` for new notebooks.

## Repository Structure

```text
PINN_MPC/
├── notebooks/
│   ├── current/
│   │   ├── training/
│   │   └── mpc/
│   └── archive/
│       ├── 2026-04-29/
│       │   ├── training/
│       │   └── mpc/
│       └── 2026-04-28/
│           ├── training/
│           └── mpc/
├── docs/
│   └── RESULTS.md
├── .gitignore
├── LICENSE
└── README.md
```

## Archive Policy

- `notebooks/current/`: latest code that should be checked first.
- `notebooks/archive/YYYY-MM-DD/`: previous training and MPC versions grouped by work date.
- Google Drive: large results, logs, datasets, and model checkpoints.

## Data, Results, and Checkpoints

Large files such as datasets, trained model checkpoints, logs, and generated experiment results are not tracked in this repository.

Recommended external storage:

- Google Drive for large result folders
- Google Drive for model checkpoints
- GitHub for source notebooks, documentation, configuration, and small reproducibility notes

The `.gitignore` file excludes common local output folders such as `data/`, `outputs/`, `results/`, `runs/`, `logs/`, `checkpoints/`, and model checkpoint files.

## License

Apache License 2.0
