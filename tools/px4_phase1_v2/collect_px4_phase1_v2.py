#!/usr/bin/env python3
"""
PX4 Gazebo Phase 1 data collector, v2.

Scope:
- Launch a fresh PX4/Gazebo SITL process for each scenario.
- Connect through MAVSDK.
- Run a minimal takeoff/hold scenario.
- Save raw telemetry, analysis-window telemetry, quality metrics, metadata, and plots.

Non-scope:
- No PINN training.
- No MPC.
- No disturbance injection yet.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from mavsdk import System


@dataclass
class TelemetryState:
    connected: bool = False
    armed: bool | None = None
    flight_mode: str | None = None
    health_global_position_ok: bool | None = None
    health_home_position_ok: bool | None = None
    latitude_deg: float | None = None
    longitude_deg: float | None = None
    absolute_altitude_m: float | None = None
    relative_altitude_m: float | None = None
    vel_north_m_s: float | None = None
    vel_east_m_s: float | None = None
    vel_down_m_s: float | None = None
    roll_deg: float | None = None
    pitch_deg: float | None = None
    yaw_deg: float | None = None
    roll_rate_rad_s: float | None = None
    pitch_rate_rad_s: float | None = None
    yaw_rate_rad_s: float | None = None
    battery_voltage_v: float | None = None
    battery_remaining_percent: float | None = None


def expand_path(path: str | Path) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(path)))).resolve()


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def launch_px4(px4_dir: Path, vehicle: str, headless: bool) -> subprocess.Popen:
    env = os.environ.copy()
    if headless:
        env["HEADLESS"] = "1"
    cmd = ["make", "px4_sitl", vehicle]
    print(f"[launch] cwd={px4_dir}")
    print(f"[launch] {' '.join(cmd)} HEADLESS={env.get('HEADLESS', '')}")
    return subprocess.Popen(
        cmd,
        cwd=str(px4_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
    )


def cleanup_stale_px4_processes() -> None:
    """Best-effort cleanup for stale SITL processes from a previous interrupted run."""
    if os.name == "nt":
        return
    patterns = [
        "build/px4_sitl_default/bin/px4",
        "PX4_SIM_MODEL=gz_",
        "gz sim",
        "ruby.*Tools/simulation/gz",
        "MicroXRCEAgent",
    ]
    for pattern in patterns:
        subprocess.run(
            ["pkill", "-f", pattern],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    time.sleep(2.0)


async def mirror_process_output(proc: subprocess.Popen, log_path: Path) -> None:
    if proc.stdout is None:
        return
    with log_path.open("w", encoding="utf-8", errors="replace") as f:
        while True:
            line = await asyncio.to_thread(proc.stdout.readline)
            if not line:
                break
            f.write(line)
            f.flush()
            text = line.rstrip()
            if text:
                print("[px4]", text)


def stop_px4(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    print("[cleanup] stopping fresh PX4 process")
    try:
        if os.name == "nt":
            proc.terminate()
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        proc.wait(timeout=12)
    except Exception:
        proc.kill()


async def first_connection(drone: System, state: TelemetryState, timeout_s: float) -> None:
    async def wait_loop() -> None:
        async for connection_state in drone.core.connection_state():
            state.connected = bool(connection_state.is_connected)
            if state.connected:
                print("[mavsdk] vehicle connected")
                return

    await asyncio.wait_for(wait_loop(), timeout=timeout_s)


async def watch_armed(drone: System, state: TelemetryState) -> None:
    async for armed in drone.telemetry.armed():
        state.armed = bool(armed)


async def watch_flight_mode(drone: System, state: TelemetryState) -> None:
    async for mode in drone.telemetry.flight_mode():
        state.flight_mode = str(mode)


async def watch_health(drone: System, state: TelemetryState) -> None:
    async for health in drone.telemetry.health():
        state.health_global_position_ok = bool(health.is_global_position_ok)
        state.health_home_position_ok = bool(health.is_home_position_ok)


async def watch_position(drone: System, state: TelemetryState) -> None:
    async for pos in drone.telemetry.position():
        state.latitude_deg = float(pos.latitude_deg)
        state.longitude_deg = float(pos.longitude_deg)
        state.absolute_altitude_m = float(pos.absolute_altitude_m)
        state.relative_altitude_m = float(pos.relative_altitude_m)


async def watch_velocity(drone: System, state: TelemetryState) -> None:
    async for vel in drone.telemetry.velocity_ned():
        state.vel_north_m_s = float(vel.north_m_s)
        state.vel_east_m_s = float(vel.east_m_s)
        state.vel_down_m_s = float(vel.down_m_s)


async def watch_attitude(drone: System, state: TelemetryState) -> None:
    async for att in drone.telemetry.attitude_euler():
        state.roll_deg = float(att.roll_deg)
        state.pitch_deg = float(att.pitch_deg)
        state.yaw_deg = float(att.yaw_deg)


async def watch_rates(drone: System, state: TelemetryState) -> None:
    async for rates in drone.telemetry.attitude_angular_velocity_body():
        state.roll_rate_rad_s = float(rates.roll_rad_s)
        state.pitch_rate_rad_s = float(rates.pitch_rad_s)
        state.yaw_rate_rad_s = float(rates.yaw_rad_s)


async def watch_battery(drone: System, state: TelemetryState) -> None:
    async for battery in drone.telemetry.battery():
        state.battery_voltage_v = float(battery.voltage_v)
        state.battery_remaining_percent = float(battery.remaining_percent)


async def wait_for_position_health(state: TelemetryState, timeout_s: float) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        if state.health_global_position_ok and state.health_home_position_ok:
            print("[mavsdk] global/home position ready")
            return True
        await asyncio.sleep(0.25)
    print("[warn] position health timeout")
    return False


def snapshot(state: TelemetryState, scenario: str, t0: float) -> dict[str, Any]:
    row = asdict(state)
    row["scenario"] = scenario
    row["wall_time_s"] = time.time()
    row["time_s"] = row["wall_time_s"] - t0
    return row


async def collect_one_scenario(
    cfg: dict[str, Any],
    scenario: dict[str, Any],
    run_dir: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    name = scenario["name"]
    scenario_dir = run_dir / name
    scenario_dir.mkdir(parents=True, exist_ok=True)

    proc: subprocess.Popen | None = None
    px4_log_task: asyncio.Task | None = None
    if not args.no_launch:
        if args.kill_existing:
            cleanup_stale_px4_processes()
        proc = launch_px4(
            expand_path(cfg["px4_dir"]),
            str(cfg.get("vehicle", "gz_standard_vtol")),
            bool(scenario.get("headless", True)),
        )
        px4_log_task = asyncio.create_task(mirror_process_output(proc, scenario_dir / "px4_stdout.log"))
        await asyncio.sleep(float(scenario.get("launch_wait_s", 25.0)))

    state = TelemetryState()
    watchers: list[asyncio.Task] = []
    try:
        drone = System()
        connection_url = str(cfg.get("connection_url", "udp://:14540"))
        print(f"[{name}] connecting {connection_url}")
        await drone.connect(system_address=connection_url)
        await first_connection(drone, state, timeout_s=float(args.connection_timeout_s))

        watchers = [
            asyncio.create_task(watch_armed(drone, state)),
            asyncio.create_task(watch_flight_mode(drone, state)),
            asyncio.create_task(watch_health(drone, state)),
            asyncio.create_task(watch_position(drone, state)),
            asyncio.create_task(watch_velocity(drone, state)),
            asyncio.create_task(watch_attitude(drone, state)),
            asyncio.create_task(watch_rates(drone, state)),
            asyncio.create_task(watch_battery(drone, state)),
        ]

        await wait_for_position_health(state, timeout_s=float(args.health_timeout_s))

        if scenario.get("arm", True):
            print(f"[{name}] arm")
            await drone.action.arm()

        if scenario.get("takeoff", True):
            takeoff_alt_m = float(scenario.get("takeoff_altitude_m", 25.0))
            print(f"[{name}] takeoff altitude={takeoff_alt_m:.1f} m")
            await drone.action.set_takeoff_altitude(takeoff_alt_m)
            await drone.action.takeoff()
            await asyncio.sleep(float(scenario.get("hold_after_takeoff_s", 8.0)))

        if scenario.get("transition_to_fixedwing", False):
            print(f"[{name}] transition_to_fixedwing")
            await drone.action.transition_to_fixedwing()
            await asyncio.sleep(float(scenario.get("hold_after_transition_s", 8.0)))

        duration_s = float(scenario["duration_s"])
        sample_period_s = float(scenario["sample_period_s"])
        print(f"[{name}] collecting duration={duration_s:.1f}s sample={sample_period_s:.3f}s")
        rows: list[dict[str, Any]] = []
        t0 = time.time()
        next_sample = t0
        while time.time() - t0 < duration_s:
            now = time.time()
            if now >= next_sample:
                rows.append(snapshot(state, name, t0))
                next_sample += sample_period_s
            await asyncio.sleep(min(0.01, sample_period_s))

        raw_df = pd.DataFrame(rows)
        raw_path = scenario_dir / "telemetry_raw.csv"
        raw_df.to_csv(raw_path, index=False)

        analysis_df = make_analysis_window(raw_df, scenario)
        analysis_path = scenario_dir / "telemetry_analysis.csv"
        analysis_df.to_csv(analysis_path, index=False)

        metrics = compute_quality_metrics(raw_df, analysis_df, scenario)
        metrics.update({
            "scenario": name,
            "raw_csv": str(raw_path),
            "analysis_csv": str(analysis_path),
            "scenario_dir": str(scenario_dir),
        })

        plot_path = scenario_dir / "quicklook.png"
        plot_quicklook(raw_df, analysis_df, scenario, plot_path)

        scenario_metadata = {
            "scenario": scenario,
            "metrics": metrics,
            "quicklook": str(plot_path),
        }
        (scenario_dir / "metadata.json").write_text(json.dumps(scenario_metadata, indent=2), encoding="utf-8")
        return metrics
    finally:
        for task in watchers:
            task.cancel()
        if watchers:
            await asyncio.gather(*watchers, return_exceptions=True)
        if px4_log_task is not None:
            px4_log_task.cancel()
            await asyncio.gather(px4_log_task, return_exceptions=True)
        stop_px4(proc)
        if not args.no_launch:
            await asyncio.sleep(float(args.cooldown_s))


def make_analysis_window(raw_df: pd.DataFrame, scenario: dict[str, Any]) -> pd.DataFrame:
    if raw_df.empty:
        return raw_df.copy()
    start_s = float(scenario.get("analysis_start_s", 0.0) or 0.0)
    end_cfg = scenario.get("analysis_end_s", None)
    mask = raw_df["time_s"] >= start_s
    if end_cfg is not None:
        mask &= raw_df["time_s"] <= float(end_cfg)
    return raw_df.loc[mask].reset_index(drop=True)


def finite_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns or df.empty:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[col], errors="coerce").dropna()


def compute_quality_metrics(raw_df: pd.DataFrame, analysis_df: pd.DataFrame, scenario: dict[str, Any]) -> dict[str, Any]:
    time_raw = finite_series(raw_df, "time_s")
    dt = time_raw.diff().dropna()
    rel_alt = finite_series(analysis_df, "relative_altitude_m")
    pitch = finite_series(analysis_df, "pitch_deg")
    down = finite_series(analysis_df, "vel_down_m_s")
    vel_n = finite_series(analysis_df, "vel_north_m_s")
    vel_e = finite_series(analysis_df, "vel_east_m_s")
    horiz_speed = np.sqrt(vel_n.to_numpy() ** 2 + vel_e.to_numpy() ** 2) if len(vel_n) and len(vel_e) else np.array([])

    target_alt = float(scenario.get("takeoff_altitude_m", np.nan))
    alt_error = rel_alt - target_alt if len(rel_alt) else pd.Series(dtype=float)

    metrics = {
        "rows_raw": int(len(raw_df)),
        "rows_analysis": int(len(analysis_df)),
        "duration_raw_s": safe_float(time_raw.max() - time_raw.min()) if len(time_raw) else None,
        "dt_mean_s": safe_float(dt.mean()) if len(dt) else None,
        "dt_std_s": safe_float(dt.std()) if len(dt) else None,
        "nan_fraction_raw": safe_float(raw_df.isna().mean().mean()) if len(raw_df) else None,
        "target_altitude_m": target_alt,
        "analysis_altitude_mean_m": safe_float(rel_alt.mean()) if len(rel_alt) else None,
        "analysis_altitude_rmse_m": safe_float(np.sqrt(np.mean(np.square(alt_error)))) if len(alt_error) else None,
        "analysis_altitude_drift_m": safe_float(rel_alt.iloc[-1] - rel_alt.iloc[0]) if len(rel_alt) > 1 else None,
        "analysis_final_altitude_m": safe_float(rel_alt.iloc[-1]) if len(rel_alt) else None,
        "analysis_pitch_mean_deg": safe_float(pitch.mean()) if len(pitch) else None,
        "analysis_pitch_abs_mean_deg": safe_float(np.mean(np.abs(pitch))) if len(pitch) else None,
        "analysis_pitch_max_abs_deg": safe_float(np.max(np.abs(pitch))) if len(pitch) else None,
        "analysis_vertical_speed_mean_m_s": safe_float((-down).mean()) if len(down) else None,
        "analysis_horizontal_speed_mean_m_s": safe_float(np.mean(horiz_speed)) if len(horiz_speed) else None,
    }
    metrics["quality_ok_basic"] = bool(
        metrics["rows_raw"] > 0
        and metrics["rows_analysis"] > 0
        and (metrics["dt_mean_s"] is not None)
        and abs(float(metrics["dt_mean_s"]) - float(scenario["sample_period_s"])) < 0.02
    )
    return metrics


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(value):
        return None
    return value


def plot_quicklook(raw_df: pd.DataFrame, analysis_df: pd.DataFrame, scenario: dict[str, Any], path: Path) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(11, 9), sharex=True)
    target_alt = float(scenario.get("takeoff_altitude_m", np.nan))

    def plot_col(ax: plt.Axes, col: str, ylabel: str) -> None:
        if col in raw_df:
            ax.plot(raw_df["time_s"], pd.to_numeric(raw_df[col], errors="coerce"), lw=1.0, label="raw")
        if col in analysis_df and not analysis_df.empty:
            ax.plot(analysis_df["time_s"], pd.to_numeric(analysis_df[col], errors="coerce"), lw=1.8, label="analysis")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25)
        ax.legend(loc="best")

    plot_col(axes[0], "relative_altitude_m", "Rel Alt (m)")
    if np.isfinite(target_alt):
        axes[0].axhline(target_alt, color="k", ls="--", lw=0.9, label="target")

    plot_col(axes[1], "pitch_deg", "Pitch (deg)")
    plot_col(axes[2], "vel_down_m_s", "Down Vel (m/s)")
    plot_col(axes[3], "battery_voltage_v", "Battery (V)")
    axes[3].set_xlabel("Time (s)")
    fig.suptitle(scenario["name"])
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


async def main_async(args: argparse.Namespace) -> None:
    config_path = expand_path(args.config)
    cfg = load_config(config_path)
    defaults = cfg.get("defaults", {})
    scenarios = [deep_merge(defaults, item) for item in cfg["scenarios"]]
    if args.scenario:
        scenarios = [s for s in scenarios if s["name"] == args.scenario]
        if not scenarios:
            raise ValueError(f"Unknown scenario: {args.scenario}")

    run_stamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = expand_path(cfg.get("output_root", "~/px4_datasets")) / f"{cfg.get('run_name', 'px4_phase1_v1')}_{run_stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    run_metadata = {
        "collector_version": "v2",
        "created_at": run_stamp,
        "config_path": str(config_path),
        "vehicle": cfg.get("vehicle"),
        "px4_dir": cfg.get("px4_dir"),
        "connection_url": cfg.get("connection_url"),
        "fresh_process_per_scenario": not args.no_launch,
        "scenarios": scenarios,
    }
    (run_dir / "run_metadata.json").write_text(json.dumps(run_metadata, indent=2), encoding="utf-8")

    summaries = []
    for idx, scenario in enumerate(scenarios, start=1):
        print(f"=== Scenario {idx}/{len(scenarios)}: {scenario['name']} ===")
        summary = await collect_one_scenario(cfg, scenario, run_dir, args)
        summaries.append(summary)

    summary_df = pd.DataFrame(summaries)
    summary_path = run_dir / "summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print("[done] output_dir=", run_dir)
    print("[done] summary=", summary_path)
    print(summary_df)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PX4 Gazebo Phase 1 data collector v1.")
    parser.add_argument("--config", default="scenarios.yaml", help="Scenario YAML path.")
    parser.add_argument("--scenario", default="", help="Run only one scenario.")
    parser.add_argument("--no-launch", action="store_true", help="Connect to an already-running PX4 process.")
    parser.add_argument("--connection-timeout-s", type=float, default=90.0)
    parser.add_argument("--health-timeout-s", type=float, default=60.0)
    parser.add_argument("--cooldown-s", type=float, default=5.0, help="Delay after stopping PX4 before next scenario.")
    parser.add_argument(
        "--no-kill-existing",
        dest="kill_existing",
        action="store_false",
        help="Do not clean stale PX4/Gazebo processes before launching a fresh scenario.",
    )
    parser.set_defaults(kill_existing=True)
    return parser.parse_args()


def main() -> None:
    try:
        asyncio.run(main_async(parse_args()))
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)


if __name__ == "__main__":
    main()
