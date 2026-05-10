#!/usr/bin/env python3
"""
PX4 Phase 1 dataset builder, v8 yaw-relative position-state block split.

Input:
    One or more px4_phase1_v15 run directories containing summary.csv and
    per-scenario telemetry_analysis.csv files.

Output:
    Multi-run Colab-ready one-step dynamics CSVs:
        x_t, u_t, prev_u_t, du_t, dt_s -> x_next, dx
    plus auxiliary acceleration targets:
        aux_derived_accel_*, aux_derived_*_accel_rad_s2

v8 keeps the v15 yaw-relative action contract and v7 contiguous time-block
splitting, then adds scenario-local north/east position states by integrating
telemetry velocity. This lets the learned model and MPC optimize position
directly instead of relying on an external velocity integrator.

This script intentionally does not train a model.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_STATE_COLS = [
    "local_north_m",
    "local_east_m",
    "relative_altitude_m",
    "vel_north_m_s",
    "vel_east_m_s",
    "vel_down_m_s",
    "roll_deg",
    "pitch_deg",
    "yaw_deg",
    "roll_rate_rad_s",
    "pitch_rate_rad_s",
    "yaw_rate_rad_s",
]

DEFAULT_ACTION_COLS = [
    "ref_north_m",
    "ref_east_m",
    "ref_down_m",
    "ref_north_m_s",
    "ref_east_m_s",
    "ref_down_m_s",
    "ref_yaw_deg",
    "ref_yaw_offset_deg",
]

DEFAULT_AUX_TARGET_COLS = [
    "derived_accel_north_m_s2",
    "derived_accel_east_m_s2",
    "derived_accel_down_m_s2",
    "derived_roll_accel_rad_s2",
    "derived_pitch_accel_rad_s2",
    "derived_yaw_accel_rad_s2",
]

DEFAULT_OPTIONAL_AUX_TARGET_COLS = [
    "imu_accel_forward_m_s2",
    "imu_accel_right_m_s2",
    "imu_accel_down_m_s2",
    "imu_angular_rate_forward_rad_s",
    "imu_angular_rate_right_rad_s",
    "imu_angular_rate_down_rad_s",
]

REF_RATE_DEG_COLS = {
    "ref_roll_rate_rad_s": "ref_roll_rate_deg_s",
    "ref_pitch_rate_rad_s": "ref_pitch_rate_deg_s",
    "ref_yaw_rate_rad_s": "ref_yaw_rate_deg_s",
}


def expand_path(path: str | Path) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(path)))).resolve()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        if path.suffix.lower() == ".json":
            return json.load(f)
        try:
            import yaml
        except ImportError as exc:
            raise ImportError(
                "YAML config requires PyYAML. Use config.json or install pyyaml."
            ) from exc
        return yaml.safe_load(f)


def runs_from_glob(pattern: str, max_runs: int | None = None) -> list[Path]:
    import glob

    all_matches = sorted(expand_path(p) for p in glob.glob(os.path.expanduser(pattern)))
    matches = [p for p in all_matches if (p / "summary.csv").exists()]
    skipped = [p for p in all_matches if not (p / "summary.csv").exists()]
    for p in skipped:
        print(f"[skip] missing summary.csv: {p}")
    if not matches:
        raise FileNotFoundError(f"No source runs matched: {pattern}")
    if max_runs is not None and max_runs > 0:
        matches = matches[-max_runs:]
    return matches


def make_output_dir(config: dict[str, Any], output_root: str | None) -> Path:
    root = expand_path(output_root or config.get("output_root", "~/px4_datasets/processed"))
    stamp = time.strftime("%Y%m%d_%H%M%S")
    name = config.get("dataset_name", "px4_phase1_closed_loop_yawrel_position_state_dataset_v8")
    out = root / f"{name}_{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    return out


def scenario_dirs(run_dir: Path) -> list[Path]:
    return sorted([p for p in run_dir.iterdir() if p.is_dir() and (p / "telemetry_analysis.csv").exists()])


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if (
        ("local_north_m" not in out.columns or "local_east_m" not in out.columns)
        and {"time_s", "vel_north_m_s", "vel_east_m_s"}.issubset(out.columns)
    ):
        t = pd.to_numeric(out["time_s"], errors="coerce").to_numpy(dtype=float)
        vn = (
            pd.to_numeric(out["vel_north_m_s"], errors="coerce")
            .interpolate(limit_direction="both")
            .bfill()
            .ffill()
            .to_numpy(dtype=float)
        )
        ve = (
            pd.to_numeric(out["vel_east_m_s"], errors="coerce")
            .interpolate(limit_direction="both")
            .bfill()
            .ffill()
            .to_numpy(dtype=float)
        )
        dt = np.diff(t, prepend=t[0] if len(t) else 0.0)
        dt = np.where(np.isfinite(dt), dt, 0.0)
        dt = np.clip(dt, 0.0, 0.2)
        north_step = np.zeros_like(vn, dtype=float)
        east_step = np.zeros_like(ve, dtype=float)
        if len(t) > 1:
            north_step[1:] = 0.5 * (vn[:-1] + vn[1:]) * dt[1:]
            east_step[1:] = 0.5 * (ve[:-1] + ve[1:]) * dt[1:]
        if "local_north_m" not in out.columns:
            out["local_north_m"] = np.cumsum(north_step)
            out["local_north_m"] -= float(out["local_north_m"].iloc[0]) if len(out) else 0.0
        if "local_east_m" not in out.columns:
            out["local_east_m"] = np.cumsum(east_step)
            out["local_east_m"] -= float(out["local_east_m"].iloc[0]) if len(out) else 0.0
    for rad_col, deg_col in REF_RATE_DEG_COLS.items():
        if rad_col not in out.columns and deg_col in out.columns:
            out[rad_col] = np.deg2rad(pd.to_numeric(out[deg_col], errors="coerce"))
    for col in ["roll_rate_rad_s", "pitch_rate_rad_s", "yaw_rate_rad_s"]:
        deg_col = col.replace("_rad_s", "_deg_s")
        if deg_col not in out.columns and col in out.columns:
            out[deg_col] = np.rad2deg(pd.to_numeric(out[col], errors="coerce"))
    return out


def finite_mask(df: pd.DataFrame, cols: list[str]) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for col in cols:
        if col not in df.columns:
            return pd.Series(False, index=df.index)
        mask &= np.isfinite(pd.to_numeric(df[col], errors="coerce"))
    return mask


def usable_aux_columns(df: pd.DataFrame, requested: list[str], min_notna_fraction: float) -> list[str]:
    cols = []
    for col in requested:
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        if float(values.notna().mean()) >= min_notna_fraction:
            cols.append(col)
    return cols


def build_samples_for_scenario(
    run_dir: Path,
    scenario_dir: Path,
    summary_row: dict[str, Any],
    state_cols: list[str],
    action_cols: list[str],
    aux_target_cols: list[str],
    filters: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    df = pd.read_csv(scenario_dir / "telemetry_analysis.csv")
    df = add_derived_columns(df)
    scenario = scenario_dir.name
    if "scenario" in df.columns and len(df):
        scenario = str(df["scenario"].iloc[0])

    required = ["time_s", *state_cols, *action_cols]
    raw_rows = len(df)
    missing = [c for c in required if c not in df.columns]

    if missing or raw_rows < 2:
        report = {
            "scenario": scenario,
            "source_run": run_dir.name,
            "raw_rows": raw_rows,
            "sample_rows": 0,
            "kept_rows_after_filter": 0,
            "missing_columns": ",".join(missing),
            "quality_ok_basic": bool(summary_row.get("quality_ok_basic", False)),
            "safety_ok": bool(summary_row.get("safety_ok", False)),
        }
        return pd.DataFrame(), report

    df = df.sort_values("time_s").reset_index(drop=True)
    times = pd.to_numeric(df["time_s"], errors="coerce")
    dt = times.shift(-1) - times

    row_mask = finite_mask(df, required)
    require_aux = bool(filters.get("require_aux_targets", True))
    if require_aux and aux_target_cols:
        row_mask &= finite_mask(df, aux_target_cols)
    row_mask &= pd.to_numeric(df["relative_altitude_m"], errors="coerce").between(
        float(filters.get("min_relative_altitude_m", 10.0)),
        float(filters.get("max_relative_altitude_m", 35.0)),
    )
    row_mask &= pd.to_numeric(df["roll_deg"], errors="coerce").abs() <= float(filters.get("max_abs_roll_deg", 25.0))
    row_mask &= pd.to_numeric(df["pitch_deg"], errors="coerce").abs() <= float(filters.get("max_abs_pitch_deg", 25.0))
    max_rate = float(filters.get("max_abs_body_rate_deg_s", 120.0))
    for col in ["roll_rate_deg_s", "pitch_rate_deg_s", "yaw_rate_deg_s"]:
        if col in df.columns:
            row_mask &= pd.to_numeric(df[col], errors="coerce").abs() <= max_rate

    if bool(filters.get("require_quality_ok_basic", True)) and not bool(summary_row.get("quality_ok_basic", False)):
        row_mask &= False

    pair_mask = row_mask & row_mask.shift(-1, fill_value=False)
    pair_mask &= dt.between(float(filters.get("min_dt_s", 0.025)), float(filters.get("max_dt_s", 0.075)))
    pair_mask.iloc[-1] = False

    # Remove finite-difference outliers that otherwise dominate direct delta and
    # acceleration supervision. Thresholds are wider than normal hover motion but
    # reject glitches such as multi-meter altitude jumps in a single 20 Hz sample.
    dx_limits = dict(filters.get("dx_limits", {}))
    for col, limit in dx_limits.items():
        if col not in df.columns:
            continue
        delta = pd.to_numeric(df[col].shift(-1), errors="coerce") - pd.to_numeric(df[col], errors="coerce")
        pair_mask &= delta.abs() <= float(limit)

    aux_abs_limits = dict(filters.get("aux_abs_limits", {}))
    for col, limit in aux_abs_limits.items():
        if col not in df.columns:
            continue
        pair_mask &= pd.to_numeric(df[col], errors="coerce").abs() <= float(limit)

    idx = np.flatnonzero(pair_mask.to_numpy())
    if len(idx) == 0:
        report = {
            "scenario": scenario,
            "source_run": run_dir.name,
            "raw_rows": raw_rows,
            "kept_rows_after_filter": int(row_mask.sum()),
            "sample_rows": 0,
            "missing_columns": "",
            "quality_ok_basic": bool(summary_row.get("quality_ok_basic", False)),
            "safety_ok": bool(summary_row.get("safety_ok", False)),
        }
        return pd.DataFrame(), report

    current = df.iloc[idx].reset_index(drop=True)
    nxt = df.iloc[idx + 1].reset_index(drop=True)
    out = pd.DataFrame(
        {
            "source_run": summary_row.get("source_run", ""),
            "scenario": scenario,
            "ref_label": current.get("ref_label", pd.Series([""] * len(current))).astype(str),
            "sample_index": idx,
            "time_s": current["time_s"].to_numpy(),
            "dt_s": dt.iloc[idx].to_numpy(),
            "scenario_safety_ok": bool(summary_row.get("safety_ok", False)),
            "scenario_quality_ok_basic": bool(summary_row.get("quality_ok_basic", False)),
        }
    )

    for col in state_cols:
        out[f"x_{col}"] = pd.to_numeric(current[col], errors="coerce").to_numpy()
        out[f"x_next_{col}"] = pd.to_numeric(nxt[col], errors="coerce").to_numpy()
        delta = out[f"x_next_{col}"] - out[f"x_{col}"]
        if col == "yaw_deg":
            delta = ((delta + 180.0) % 360.0) - 180.0
        out[f"dx_{col}"] = delta

    for col in action_cols:
        values = pd.to_numeric(current[col], errors="coerce").to_numpy()
        prev_values = pd.to_numeric(df[col].shift(1).iloc[idx], errors="coerce").to_numpy()
        prev_values = np.where(np.isfinite(prev_values), prev_values, values)
        out[f"u_{col}"] = values
        out[f"prev_u_{col}"] = prev_values
        out[f"du_{col}"] = values - prev_values

    for col in aux_target_cols:
        out[f"aux_{col}"] = pd.to_numeric(current[col], errors="coerce").to_numpy()

    report = {
        "scenario": scenario,
        "source_run": run_dir.name,
        "raw_rows": raw_rows,
        "kept_rows_after_filter": int(row_mask.sum()),
        "sample_rows": int(len(out)),
        "missing_columns": "",
        "quality_ok_basic": bool(summary_row.get("quality_ok_basic", False)),
        "safety_ok": bool(summary_row.get("safety_ok", False)),
        "min_altitude_kept_m": float(current["relative_altitude_m"].min()),
        "max_altitude_kept_m": float(current["relative_altitude_m"].max()),
        "aux_target_cols": ",".join(aux_target_cols),
    }
    return out, report


def contiguous_blocks_for_group(g: pd.DataFrame, block_size: int) -> list[np.ndarray]:
    g = g.sort_values("sample_index")
    idx_values = g.index.to_numpy()
    sample_values = g["sample_index"].to_numpy()
    blocks: list[np.ndarray] = []
    start = 0
    while start < len(g):
        end = start + 1
        while end < len(g) and sample_values[end] == sample_values[end - 1] + 1:
            end += 1
        run_idx = idx_values[start:end]
        for k in range(0, len(run_idx), block_size):
            block = run_idx[k : k + block_size]
            if len(block):
                blocks.append(block)
        start = end
    return blocks


def deterministic_block_split(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    split_cfg = config.get("split", {})
    seed = int(split_cfg.get("seed", 7))
    val_scenarios = set(split_cfg.get("val_scenarios", []) or [])
    test_scenarios = set(split_cfg.get("test_scenarios", []) or [])
    train_frac = float(split_cfg.get("train_fraction", 0.70))
    val_frac = float(split_cfg.get("val_fraction", 0.15))
    hard_test_fraction = float(split_cfg.get("hard_scenario_test_fraction", 1.0))
    block_size = int(split_cfg.get("block_size_samples", 160))

    out = df.copy()
    out["split"] = "train"
    out["block_id"] = ""
    rng = np.random.default_rng(seed)

    block_rows: list[dict[str, Any]] = []
    group_cols = ["source_run", "scenario"]
    for (source_run, scenario), g in out.groupby(group_cols, sort=True):
        blocks = contiguous_blocks_for_group(g, block_size)
        for local_id, block_idx in enumerate(blocks):
            block_id = f"{source_run}|{scenario}|{local_id:04d}"
            out.loc[block_idx, "block_id"] = block_id
            block_rows.append({
                "block_id": block_id,
                "source_run": source_run,
                "scenario": scenario,
                "indices": block_idx,
                "n": len(block_idx),
            })

    if not block_rows:
        raise RuntimeError("No contiguous blocks were available for splitting.")

    block_df = pd.DataFrame(block_rows)
    block_df["split"] = "train"

    if val_scenarios:
        block_df.loc[block_df["scenario"].isin(val_scenarios), "split"] = "val"

    for scenario in sorted(test_scenarios):
        mask = block_df["scenario"].eq(scenario)
        candidate_idx = block_df.index[mask].to_numpy()
        if not len(candidate_idx):
            continue
        shuffled = candidate_idx.copy()
        rng.shuffle(shuffled)
        n_test = max(1, int(round(len(shuffled) * hard_test_fraction)))
        block_df.loc[shuffled[:n_test], "split"] = "test"

    remaining_idx = block_df.index[block_df["split"].eq("train")].to_numpy()
    if len(remaining_idx):
        shuffled = remaining_idx.copy()
        rng.shuffle(shuffled)
        n = len(shuffled)
        n_train = int(round(n * train_frac))
        n_val = int(round(n * val_frac))
        block_df.loc[shuffled[n_train : n_train + n_val], "split"] = "val"
        block_df.loc[shuffled[n_train + n_val :], "split"] = "test"

    for _, row in block_df.iterrows():
        out.loc[row["indices"], "split"] = row["split"]

    return out


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--run-dir", action="append", default=None, help="Specific px4_phase1_v15 run directory. Can be repeated.")
    parser.add_argument("--latest-n", type=int, default=None, help="Use only the latest N runs matching source_run_glob.")
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()

    config_path = expand_path(args.config)
    config = load_config(config_path)
    max_runs = args.latest_n if args.latest_n is not None else config.get("max_runs", None)
    run_dirs = [expand_path(p) for p in args.run_dir] if args.run_dir else runs_from_glob(config["source_run_glob"], max_runs=max_runs)
    run_dirs_with_summary = []
    for run_dir in run_dirs:
        if (run_dir / "summary.csv").exists():
            run_dirs_with_summary.append(run_dir)
        else:
            print(f"[skip] missing summary.csv: {run_dir}")
    run_dirs = run_dirs_with_summary
    if not run_dirs:
        raise FileNotFoundError("No run directories with summary.csv were found.")

    output_dir = make_output_dir(config, args.output_root)

    state_cols = list(config.get("columns", {}).get("state", DEFAULT_STATE_COLS))
    action_cols = list(config.get("columns", {}).get("action", DEFAULT_ACTION_COLS))
    requested_aux_target_cols = list(config.get("columns", {}).get("aux_target", DEFAULT_AUX_TARGET_COLS))
    requested_optional_aux_target_cols = list(
        config.get("columns", {}).get("optional_aux_target", DEFAULT_OPTIONAL_AUX_TARGET_COLS)
    )
    filters = dict(config.get("filters", {}))
    min_aux_notna_fraction = float(filters.get("min_aux_notna_fraction", 0.95))

    sample_parts: list[pd.DataFrame] = []
    reports: list[dict[str, Any]] = []
    summaries: list[pd.DataFrame] = []
    for run_dir in run_dirs:
        summary = pd.read_csv(run_dir / "summary.csv")
        summary["source_run"] = run_dir.name
        summaries.append(summary)
        scenario_aux_cols: dict[str, list[str]] = {}
        summary_by_scenario = {str(row["scenario"]): row.to_dict() for _, row in summary.iterrows()}
        print(f"[run] {run_dir.name} scenarios={len(scenario_dirs(run_dir))}")
        for sdir in scenario_dirs(run_dir):
            scenario_name = sdir.name
            summary_row = summary_by_scenario.get(scenario_name, {"scenario": scenario_name, "source_run": run_dir.name})
            preview = add_derived_columns(pd.read_csv(sdir / "telemetry_analysis.csv", nrows=1000))
            aux_cols = usable_aux_columns(preview, requested_aux_target_cols, min_aux_notna_fraction)
            optional_aux_cols = usable_aux_columns(preview, requested_optional_aux_target_cols, min_aux_notna_fraction)
            scenario_aux_cols[scenario_name] = aux_cols + optional_aux_cols
            samples, report = build_samples_for_scenario(
                run_dir,
                sdir,
                summary_row,
                state_cols,
                action_cols,
                scenario_aux_cols[scenario_name],
                filters,
            )
            sample_parts.append(samples)
            reports.append(report)
            print(
                f"  [scenario] {report['scenario']} raw={report['raw_rows']} "
                f"kept={report.get('kept_rows_after_filter', 0)} samples={report['sample_rows']} "
                f"aux={len(scenario_aux_cols[scenario_name])}"
            )

    all_samples = pd.concat([p for p in sample_parts if len(p)], ignore_index=True) if sample_parts else pd.DataFrame()
    if all_samples.empty:
        raise RuntimeError("No samples survived filtering. Relax filters or inspect filter_report.csv.")

    all_samples = deterministic_block_split(all_samples, config)
    filter_report = pd.DataFrame(reports).sort_values("scenario").reset_index(drop=True)
    dataset_summary = (
        all_samples.groupby(["split", "scenario"])
        .size()
        .to_frame("samples")
        .reset_index()
        .sort_values(["split", "scenario"])
    )

    all_samples.to_csv(output_dir / "all_samples.csv", index=False)
    for split in ["train", "val", "test"]:
        all_samples[all_samples["split"].eq(split)].to_csv(output_dir / f"{split}.csv", index=False)
    filter_report.to_csv(output_dir / "filter_report.csv", index=False)
    dataset_summary.to_csv(output_dir / "dataset_summary.csv", index=False)
    source_summary = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
    source_summary.to_csv(output_dir / "source_summary.csv", index=False)
    write_json(
        output_dir / "metadata.json",
        {
            "builder_version": "v8_position_state_block_split",
            "source_run_dirs": [str(p) for p in run_dirs],
            "output_dir": str(output_dir),
            "config_path": str(config_path),
            "state_cols": state_cols,
            "action_cols": action_cols,
            "feature_prefixes": ["x_", "u_", "prev_u_", "du_"],
            "target_prefix": "dx_",
            "aux_target_prefix": "aux_",
            "requested_aux_target_cols": requested_aux_target_cols,
            "requested_optional_aux_target_cols": requested_optional_aux_target_cols,
            "filters": filters,
            "split": config.get("split", {}),
            "total_samples": int(len(all_samples)),
            "split_counts": all_samples["split"].value_counts().to_dict(),
            "run_count": int(len(run_dirs)),
        },
    )

    print("\n[done] dataset_dir=", output_dir)
    print("[done] run_count=", len(run_dirs))
    print("[done] total_samples=", len(all_samples))
    print("[done] split counts:")
    print(all_samples["split"].value_counts().to_string())
    print("\n[done] scenario samples:")
    print(dataset_summary.to_string(index=False))


if __name__ == "__main__":
    main()
