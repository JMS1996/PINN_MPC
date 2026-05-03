# PINN-MPC Research Progress

## Current Working Notebook

- MPC: `notebooks/current/MPC/PINN_MPC_v6_alpha_snc_smooth_pitch_doublet_two_case_simplePID_MPPI_fast_v22.ipynb`
- PINN training: `notebooks/current/PINN/PINN_model_training_auto_v6_alpha_state.ipynb`

## Summary

The project moved from altitude-climb tracking toward pitch-axis stability and control maneuver tracking. Altitude climb tests exposed trim, energy, speed-unit, and sustained-climb feasibility issues that made the controller comparison difficult to interpret. The current direction is to first validate nominal pitch-axis maneuver tracking, then add disturbances once the nominal case is stable.

## Key Findings

- The JSBSim initial speed command uses knots, while the PINN state velocity uses ft/s. The notebooks now separate `INIT_SPEED_KTS` and `INIT_SPEED_FPS`.
- Linear altitude guidance exposed that elevator-only control with fixed throttle is not a clean way to evaluate early PINN-MPC behavior.
- Sustained climb authority checks showed that short open-loop pull-up behavior can look feasible while long-duration climb tracking fails.
- Smooth pitch doublet tracking is a better near-term S&C test because it focuses on pitch, pitch-rate, alpha, speed, and altitude-hold behavior without requiring a large energy climb.
- PID is tuned with JSBSim rollout through Optuna. MPPI intentionally remains PINN-prediction based, which is the intended research comparison.
- The smooth pitch doublet nominal case improved MPPI tracking compared with the step doublet, but MPPI remains computationally expensive.
- v20 strengthens altitude-hold cost and reduces MPPI horizon/sample count to explore the pitch-tracking versus compute-time trade-off.

## Notebook Evolution

- v4-v6: Load-only PINN-MPC baseline and altitude guidance debugging.
- v7-v9: Linear altitude guidance and checkpoint/path fixes.
- v10-v12: Longer tracking runs, guidance plotting, and plant authority diagnostics.
- v13-v14: Speed-unit correction and guard checks.
- v15-v16: Feasible climb-rate and speed-aware altitude tests.
- v17-v18: Pitch-axis S&C doublet and multi-disturbance experiments.
- v19: Nominal smooth pitch doublet with longer MPPI horizon and faster update.
- v20: Nominal smooth pitch doublet with stronger altitude-hold cost and reduced MPPI compute load.
- v21: Two-case smooth pitch doublet comparison using nominal and one representative sine-step elevator disturbance.
- v22: Fast two-case comparison using simple PID, no Optuna, shorter simulation, shorter MPPI horizon, and one representative disturbance.

## Archive

Older MPC notebooks from the current folder were moved to:

`notebooks/archive/2026-05-03/MPC/`

The latest MPC notebook remains in:

`notebooks/current/MPC/`

## Next Recommended Step

Run v22 and compare nominal versus the representative disturbance case:

- Compare pitch RMSE, peak pitch error, altitude loss, and speed loss for PID and MPPI.
- Use v22 first for quick iteration without Colab disconnects.
- If the disturbed case separates PID and MPPI clearly, keep this as the first robustness experiment.
- If v22 is stable, increase horizon/sample count or re-enable Optuna only after the quick case is understood.
