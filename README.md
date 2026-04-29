# PINN MPC

PINN-based model training and MPC experiment notebooks.

## Repository Structure

```text
PINN_MPC/
├── notebooks/
│   ├── training/
│   │   ├── PINN_model_training_auto_v5_2_warmstart_aligned.ipynb
│   │   └── PINN_model_training_auto_v6_alpha_state.ipynb
│   └── mpc/
│       ├── PINN_MPC_v5.ipynb
│       └── PINN_MPC_v6_alpha_LOAD_ONLY_PID_CEM_MPPI.ipynb
├── docs/
│   └── RESULTS.md
├── .gitignore
├── LICENSE
└── README.md
```

## Notebooks

### Training

- `notebooks/training/PINN_model_training_auto_v5_2_warmstart_aligned.ipynb`
- `notebooks/training/PINN_model_training_auto_v6_alpha_state.ipynb`

### MPC

- `notebooks/mpc/PINN_MPC_v5.ipynb`
- `notebooks/mpc/PINN_MPC_v6_alpha_LOAD_ONLY_PID_CEM_MPPI.ipynb`

## Data, Results, and Checkpoints

Large files such as datasets, trained model checkpoints, logs, and generated experiment results are not tracked in this repository.

Recommended external storage:

- Google Drive for large result folders
- Google Drive for model checkpoints
- GitHub for source notebooks, documentation, configuration, and small reproducibility notes

The `.gitignore` file excludes common local output folders such as `data/`, `outputs/`, `results/`, `runs/`, `logs/`, `checkpoints/`, and model checkpoint files.

## License

Apache License 2.0

