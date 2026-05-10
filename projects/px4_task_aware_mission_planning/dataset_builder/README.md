# Dataset Builder

Converts raw PX4 task logs into trajectory-aware training, validation, and test splits.

Important rule:

```text
split by run/task trajectory, not by random rows
```

This prevents leakage across rollout validation.
