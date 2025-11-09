#!/usr/bin/env python3
"""
Profiling script for PneumoStabSim application
Uses py-spy to profile Qt Quick 3D performance
"""

import subprocess
import time
import psutil
from pathlib import Path

from tools.headless import prepare_launch_environment


def find_pneumostab_process():
    """Find running PneumoStabSim process"""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else ""
            if "app.py" in cmdline or "PneumoStabSim" in proc.info["name"]:
                return proc.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def profile_startup():
    """Profile application startup"""
    output_file = f"profiles/startup_{int(time.time())}.svg"
    Path("profiles").mkdir(exist_ok=True)

    cmd = [
        "py-spy",
        "record",
        "-o",
        output_file,
        "--native",  # Include C/C++/Qt stacks
        "--rate",
        "100",  # 100Hz sampling
        "--duration",
        "30",  # 30 seconds max
        "--",
        "python",
        "app.py",
        "--test-mode",
    ]

    print(f"🔍 Profiling startup... Output: {output_file}")
    try:
        subprocess.run(cmd, check=True, env=prepare_launch_environment())
        print(f"✅ Startup profile saved: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Profiling failed: {e}")


def profile_running():
    """Profile already running application"""
    pid = find_pneumostab_process()
    if not pid:
        print("❌ PneumoStabSim process not found. Start the application first.")
        return

    output_file = f"profiles/runtime_{int(time.time())}.svg"
    Path("profiles").mkdir(exist_ok=True)

    cmd = [
        "py-spy",
        "record",
        "-o",
        output_file,
        "--native",
        "--rate",
        "100",
        "--duration",
        "60",  # 60 seconds
        "--pid",
        str(pid),
    ]

    print(f"🔍 Profiling PID {pid}... Output: {output_file}")
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Runtime profile saved: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Profiling failed: {e}")


def live_monitor():
    """Live performance monitoring"""
    pid = find_pneumostab_process()
    if not pid:
        print("❌ PneumoStabSim process not found. Start the application first.")
        return

    cmd = ["py-spy", "top", "--pid", str(pid)]
    print(f"📊 Live monitoring PID {pid}... Press Ctrl+C to stop")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n✅ Monitoring stopped")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Profile PneumoStabSim")
    parser.add_argument(
        "mode", choices=["startup", "runtime", "live"], help="Profiling mode"
    )

    args = parser.parse_args()

    if args.mode == "startup":
        profile_startup()
    elif args.mode == "runtime":
        profile_running()
    elif args.mode == "live":
        live_monitor()
