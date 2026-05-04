#!/usr/bin/env python3
"""
PX4 Gazebo headless telemetry collector, v51.

This script intentionally does only one job:
  1. Optionally launch PX4 SITL headless.
  2. Connect with MAVSDK.
  3. Run a small takeoff/hold scenario.
  4. Save time-aligned telemetry to CSV plus scenario metadata to JSON.

It does not train a PINN and does not claim disturbance injection yet. Keeping
collection separate from training makes the dataset reproducible.
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
    north_m_s: float | None = None
    east_m_s: float | None = None
    down_m_s: float | None = None
    roll_deg: float | None = None
    pitch_deg: float | None = None
    yaw_deg: float | None = None
    roll_rate_rad_s: float | None = None
    pitch_rate_rad_s: float | None = None
    yaw_rate_rad_s: float | None = None
    battery_voltage_v: float | None = None
    battery_remaining_percent: float | None = None
    errors: list[str] = field(default_factory=list)


def expand_path(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path))).resolve()


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


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
    )


async def stream_process_output(proc: subprocess.Popen, prefix: str = "[px4]") -> None:
    if proc.stdout is None:
        return
    while True:
        line = await asyncio.to_thread(proc.stdout.readline)
        if not line:
            break
        print(prefix, line.rstrip())


def stop_process(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    print("[cleanup] stopping PX4 process")
    if os.name == "nt":
        proc.terminate()
    else:
        proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


async def watch_connection(drone: System, state: TelemetryState) -> None:
    async for connection_state in drone.core.connection_state():
        state.connected = bool(connection_state.is_connected)
        if state.connected:
            print("[mavsdk] vehicle connected")
            return


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
        state.north_m_s = float(vel.north_m_s)
        state.east_m_s = float(vel.east_m_s)
        state.down_m_s = float(vel.down_m_s)


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


def snapshot(state: TelemetryState, scenario_name: str, t0: float) -> dict[str, Any]:
    now = time.time()
    return {
        "scenario": scenario_name,
        "wall_time_s": now,
        "time_s": now - t0,
        "connected": state.connected,
        "armed": state.armed,
        "flight_mode": state.flight_mode,
        "health_global_position_ok": state.health_global_position_ok,
        "health_home_position_ok": state.health_home_position_ok,
        "latitude_deg": state.latitude_deg,
        "longitude_deg": state.longitude_deg,
        "absolute_altitude_m": state.absolute_altitude_m,
        "relative_altitude_m": state.relative_altitude_m,
        "vel_north_m_s": state.north_m_s,
        "vel_east_m_s": state.east_m_s,
        "vel_down_m_s": state.down_m_s,
        "roll_deg": state.roll_deg,
        "pitch_deg": state.pitch_deg,
        "yaw_deg": state.yaw_deg,
        "roll_rate_rad_s": state.roll_rate_rad_s,
        "pitch_rate_rad_s": state.pitch_rate_rad_s,
        "yaw_rate_rad_s": state.yaw_rate_rad_s,
        "battery_voltage_v": state.battery_voltage_v,
        "battery_remaining_percent": state.battery_remaining_percent,
    }


async def wait_for_health(state: TelemetryState, timeout_s: float = 60.0) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        if state.health_global_position_ok and state.health_home_position_ok:
            print("[mavsdk] global/home position ready")
            return
        await asyncio.sleep(0.5)
    print("[warn] health did not report global/home position ready before timeout")


async def run_scenario(drone: System, scenario: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    scenario_name = scenario["name"]
    duration_s = float(scenario["duration_s"])
    sample_period_s = float(scenario["sample_period_s"])
    state = TelemetryState()

    watchers = [
        asyncio.create_task(watch_connection(drone, state)),
        asyncio.create_task(watch_armed(drone, state)),
        asyncio.create_task(watch_flight_mode(drone, state)),
        asyncio.create_task(watch_health(drone, state)),
        asyncio.create_task(watch_position(drone, state)),
        asyncio.create_task(watch_velocity(drone, state)),
        asyncio.create_task(watch_attitude(drone, state)),
        asyncio.create_task(watch_rates(drone, state)),
        asyncio.create_task(watch_battery(drone, state)),
    ]

    await wait_for_health(state, timeout_s=45.0)

    if scenario.get("arm", True):
        print(f"[{scenario_name}] arm")
        try:
            await drone.action.arm()
        except Exception as exc:
            print(f"[warn] arm failed: {type(exc).__name__}: {exc}")

    if scenario.get("takeoff", True):
        takeoff_altitude_m = float(scenario.get("takeoff_altitude_m", 25.0))
        print(f"[{scenario_name}] takeoff altitude={takeoff_altitude_m:.1f} m")
        try:
            await drone.action.set_takeoff_altitude(takeoff_altitude_m)
            await drone.action.takeoff()
            await asyncio.sleep(float(scenario.get("hold_after_takeoff_s", 8.0)))
        except Exception as exc:
            print(f"[warn] takeoff failed: {type(exc).__name__}: {exc}")

    if scenario.get("transition_to_fixedwing", False):
        print(f"[{scenario_name}] transition_to_fixedwing")
        try:
            await drone.action.transition_to_fixedwing()
            await asyncio.sleep(8.0)
        except Exception as exc:
            print(f"[warn] transition_to_fixedwing failed: {type(exc).__name__}: {exc}")

    print(f"[{scenario_name}] collect {duration_s:.1f}s @ {sample_period_s:.3f}s")
    rows: list[dict[str, Any]] = []
    t0 = time.time()
    next_sample = t0
    while time.time() - t0 < duration_s:
        now = time.time()
        if now >= next_sample:
            rows.append(snapshot(state, scenario_name, t0))
            next_sample += sample_period_s
        await asyncio.sleep(min(0.01, sample_period_s))

    for task in watchers:
        task.cancel()
    await asyncio.gather(*watchers, return_exceptions=True)

    df = pd.DataFrame(rows)
    csv_path = out_dir / f"{scenario_name}_telemetry.csv"
    df.to_csv(csv_path, index=False)

    summary = {
        "scenario": scenario_name,
        "rows": int(len(df)),
        "csv_path": str(csv_path),
        "duration_s": duration_s,
        "sample_period_s": sample_period_s,
        "final_relative_altitude_m": none_to_float(df["relative_altitude_m"].dropna().iloc[-1] if df["relative_altitude_m"].notna().any() else None),
        "final_pitch_deg": none_to_float(df["pitch_deg"].dropna().iloc[-1] if df["pitch_deg"].notna().any() else None),
        "mean_abs_pitch_deg": none_to_float(np.nanmean(np.abs(df["pitch_deg"].astype(float))) if len(df) else None),
    }
    return summary


def none_to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if np.isnan(value):
            return None
    except TypeError:
        pass
    return float(value)


async def main_async(args: argparse.Namespace) -> None:
    cfg = load_config(expand_path(args.config))
    defaults = cfg.get("defaults", {})
    run_stamp = time.strftime("%Y%m%d_%H%M%S")
    output_root = expand_path(str(cfg.get("output_root", "~/px4_datasets")))
    out_dir = output_root / f"{cfg.get('run_name', 'px4_run')}_{run_stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    scenarios = [deep_merge(defaults, item) for item in cfg["scenarios"]]
    if args.scenario:
        scenarios = [s for s in scenarios if s["name"] == args.scenario]
        if not scenarios:
            raise ValueError(f"Unknown scenario: {args.scenario}")

    metadata = {
        "created_at": run_stamp,
        "config_path": str(expand_path(args.config)),
        "px4_dir": cfg.get("px4_dir"),
        "vehicle": cfg.get("vehicle"),
        "connection_url": cfg.get("connection_url"),
        "scenarios": scenarios,
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    proc: subprocess.Popen | None = None
    output_task: asyncio.Task | None = None
    try:
        launch_px4_flag = bool(scenarios[0].get("launch_px4", True)) and not args.no_launch
        if launch_px4_flag:
            proc = launch_px4(
                expand_path(str(cfg["px4_dir"])),
                str(cfg.get("vehicle", "gz_standard_vtol")),
                bool(scenarios[0].get("headless", True)),
            )
            output_task = asyncio.create_task(stream_process_output(proc))
            await asyncio.sleep(float(args.launch_wait_s))

        drone = System()
        connection_url = str(cfg.get("connection_url", "udp://:14540"))
        print(f"[mavsdk] connecting to {connection_url}")
        await drone.connect(system_address=connection_url)

        summaries = []
        for scenario in scenarios:
            summaries.append(await run_scenario(drone, scenario, out_dir))

        summary_path = out_dir / "summary.csv"
        pd.DataFrame(summaries).to_csv(summary_path, index=False)
        print(f"[done] output_dir={out_dir}")
        print(f"[done] summary={summary_path}")
    finally:
        if output_task is not None:
            output_task.cancel()
            await asyncio.gather(output_task, return_exceptions=True)
        stop_process(proc)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect PX4 Gazebo VTOL telemetry to CSV.")
    parser.add_argument("--config", default="scenarios_v51.yaml", help="Scenario YAML path.")
    parser.add_argument("--scenario", default="", help="Run only one scenario by name.")
    parser.add_argument("--no-launch", action="store_true", help="Do not launch PX4; connect to an already-running SITL.")
    parser.add_argument("--launch-wait-s", type=float, default=25.0, help="Seconds to wait after launching PX4 before MAVSDK connect.")
    return parser.parse_args()


def main() -> None:
    try:
        asyncio.run(main_async(parse_args()))
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)


if __name__ == "__main__":
    main()
