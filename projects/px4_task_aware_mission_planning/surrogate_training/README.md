# Surrogate Training

Training code and notebooks for the PX4 closed-loop task-state surrogate.

Target model:

```text
input: state, target, previous target, error, delta target, dt
output: delta task-state
```

Primary validation:

- 1-step prediction
- short rollout
- full task rollout
- ETA error
