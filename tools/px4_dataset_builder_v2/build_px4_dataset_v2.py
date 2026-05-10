#!/usr/bin/env python3
"""
PX4 Phase 1 dataset builder, v2.

Input:
    One or more px4_phase1_v12 run directories containing summary.csv and
    per-scenario telemetry_analysis.csv files.

Output:
    Multi-run Colab-ready one-step dynamics CSVs:
        x_t, u_t, prev_u_t, du_t, dt_s -> x_next, dx

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
    "ref_roll_rate_rad_s",
    "ref_pitch_rate_rad_s",
    "ref_yaw_rate_rad_s",
    "ref_thrust",
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

    matches = sorted(expand_path(p) for p in glob.glob(os.path.expanduser(pattern)))
    if not matches:
        raise FileNotFoundError(f"No source runs matched: {pattern}")
    if max_runs is not None and max_runs > 0:
        matches = matches[-max_runs:]
    return matches


def make_output_dir(config: dict[str, Any], output_root: str | None) -> Path:
    root = expand_path(output_root or config.get("output_root", "~/px4_datasets/processed"))
    stamp = time.strftime("%Y%m%d_%H%M%S")
    name = config.get("dataset_name", "px4_phase1_rate_dynamics_dataset_v2_multirun")
    out = root / f"{name}_{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    return out


def scenario_dirs(run_dir: Path) -> list[Path]:
    return sorted([p for p in run_dir.iterdir() if p.is_dir() and (p / "telemetry_analysis.csv").exists()])


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
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


def build_samples_for_scenario(
    run_dir: Path,
    scenario_dir: Path,
    summary_row: dict[str, Any],
    state_cols: list[str],
    action_cols: list[str],
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
        out[f"dx_{col}"] = out[f"x_next_{col}"] - out[f"x_{col}"]

    for col in action_cols:
        values = pd.to_numeric(current[col], errors="coerce").to_numpy()
        prev_values = pd.to_numeric(df[col].shift(1).iloc[idx], errors="coerce").to_numpy()
        prev_values = np.where(np.isfinite(prev_values), prev_values, values)
        out[f"u_{col}"] = values
        out[f"prev_u_{col}"] = prev_values
        out[f"du_{col}"] = values - prev_values

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
    }
    return out, report


def deterministic_row_split(df: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    split_cfg = config.get("split", {})
    seed = int(split_cfg.get("seed", 7))
    val_scenarios = set(split_cfg.get("val_scenarios", []) or [])
    test_scenarios = set(split_cfg.get("test_scenarios", []) or [])

    out = df.copy()
    out["split"] = "train"
    out.loc[out["scenario"].isin(val_scenarios), "split"] = "val"
    out.loc[out["scenario"].isin(test_scenarios), "split"] = "test"

    remaining_mask = ~out["scenario"].isin(val_scenarios | test_scenarios)
    remaining_idx = out.index[remaining_mask].to_numpy()
    if len(remaining_idx):
        rng = np.random.default_rng(seed)
        shuffled = remaining_idx.copy()
        rng.shuffle(shuffled)
        train_frac = float(split_cfg.get("train_fraction", 0.70))
        val_frac = float(split_cfg.get("val_fraction", 0.15))
        n = len(shuffled)
        n_train = int(round(n * train_frac))
        n_val = int(round(n * val_frac))
        val_idx = shuffled[n_train : n_train + n_val]
        test_idx = shuffled[n_train + n_val :]
        out.loc[val_idx, "split"] = "val"
        out.loc[test_idx, "split"] = "test"
    return out


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--run-dir", action="append", default=None, help="Specific px4_phase1_v12 run directory. Can be repeated.")
    parser.add_argument("--latest-n", type=int, default=None, help="Use only the latest N runs matching source_run_glob.")
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args()

    config_path = expand_path(args.config)
    config = load_config(config_path)
    max_runs = args.latest_n if args.latest_n is not None else config.get("max_runs", None)
    run_dirs = [expand_path(p) for p in args.run_dir] if args.run_dir else runs_from_glob(config["source_run_glob"], max_runs=max_runs)
    for run_dir in run_dirs:
        if not (run_dir / "summary.csv").exists():
            raise FileNotFoundError(f"summary.csv not found in run directory: {run_dir}")

    output_dir = make_output_dir(config, args.output_root)

    state_cols = list(config.get("columns", {}).get("state", DEFAULT_STATE_COLS))
    action_cols = list(config.get("columns", {}).get("action", DEFAULT_ACTION_COLS))
    filters = dict(config.get("filters", {}))

    sample_parts: list[pd.DataFrame] = []
    reports: list[dict[str, Any]] = []
    summaries: list[pd.DataFrame] = []
    for run_dir in run_dirs:
        summary = pd.read_csv(run_dir / "summary.csv")
        summary["source_run"] = run_dir.name
        summaries.append(summary)
        summary_by_scenario = {str(row["scenario"]): row.to_dict() for _, row in summary.iterrows()}
        print(f"[run] {run_dir.name} scenarios={len(scenario_dirs(run_dir))}")
        for sdir in scenario_dirs(run_dir):
            scenario_name = sdir.name
            summary_row = summary_by_scenario.get(scenario_name, {"scenario": scenario_name, "source_run": run_dir.name})
            samples, report = build_samples_for_scenario(run_dir, sdir, summary_row, state_cols, action_cols, filters)
            sample_parts.append(samples)
            reports.append(report)
            print(
                f"  [scenario] {report['scenario']} raw={report['raw_rows']} "
                f"kept={report.get('kept_rows_after_filter', 0)} samples={report['sample_rows']}"
            )

    all_samples = pd.concat([p for p in sample_parts if len(p)], ignore_index=True) if sample_parts else pd.DataFrame()
    if all_samples.empty:
        raise RuntimeError("No samples survived filtering. Relax filters or inspect filter_report.csv.")

    all_samples = deterministic_row_split(all_samples, config)
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
            "builder_version": "v2",
            "source_run_dirs": [str(p) for p in run_dirs],
            "output_dir": str(output_dir),
            "config_path": str(config_path),
            "state_cols": state_cols,
            "action_cols": action_cols,
            "feature_prefixes": ["x_", "u_", "prev_u_", "du_"],
            "target_prefix": "dx_",
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
