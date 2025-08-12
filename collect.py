#!/usr/bin/env python3
import argparse
import yaml
import sys
from pathlib import Path
from datetime import datetime
import socket
import platform
import json
import getpass
import logging
import subprocess
import shutil
import os

def load_config(path="config.yaml"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file '{path}' not found.", file=sys.stderr)
        sys.exit(1)

def create_output_dir(base_dir):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    hostname = socket.gethostname()
    folder_name = f"{timestamp}_{hostname}"
    output_path = Path(base_dir) / folder_name
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

def init_logger(log_path):
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logging.info("Logger initialized.")

def save_env_metadata(output_path):
    metadata = {
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "os": platform.system(),
        "os_version": platform.version(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "timestamp": datetime.now().isoformat()
    }
    with open(output_path / "env_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logging.info("Environment metadata saved.")

# ----------------- LOCAL COLLECTORS -----------------
def run_command(command, output_file):
    """Run a shell command and save its output."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, encoding="utf-8"
        )
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.stdout or "")
            if result.stderr:
                f.write("\n[STDERR]\n" + result.stderr)
        logging.info(f"Collector saved: {output_file}")
    except Exception as e:
        logging.error(f"Failed to run command {command}: {e}")

def collect_uname(output_path):
    if platform.system() == "Windows":
        cmd = "systeminfo"
    else:
        cmd = "uname -a"
    run_command(cmd, output_path / "uname.txt")

def collect_processes(output_path):
    if platform.system() == "Windows":
        cmd = "tasklist"
    else:
        cmd = "ps aux"
    run_command(cmd, output_path / "processes.txt")

def collect_crontab(output_path):
    if platform.system() == "Windows":
        cmd = "schtasks /query /fo LIST /v"
    else:
        cmd = "crontab -l"
    run_command(cmd, output_path / "crontab.txt")

def collect_packages(output_path):
    if platform.system() == "Windows":
        cmd = "wmic product get name,version"
    elif shutil.which("dpkg"):
        cmd = "dpkg -l"
    elif shutil.which("rpm"):
        cmd = "rpm -qa"
    else:
        logging.warning("No package manager found.")
        return
    run_command(cmd, output_path / "packages.txt")

# -----------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Compliance Evidence Automation Script"
    )
    parser.add_argument("--output", "-o", help="Output directory (default from config)")
    parser.add_argument("--collectors", "-c", nargs="+", help="Collectors to run (default from config)")
    parser.add_argument("--aws-profile", help="AWS profile to use (default from config)")
    parser.add_argument("--no-aws", action="store_true", help="Skip AWS collectors")
    args = parser.parse_args()

    config = load_config()
    base_output = args.output or config["output"]["base_dir"]

    output_path = create_output_dir(base_output)
    local_path = output_path / "local"
    local_path.mkdir(exist_ok=True)

    init_logger(output_path / "collect.log")
    logging.info("Script started.")
    save_env_metadata(output_path)

    # Determine which local collectors to run
    local_collectors = args.collectors or config["collectors"]["local"]

    if "uname" in local_collectors:
        collect_uname(local_path)
    if "processes" in local_collectors:
        collect_processes(local_path)
    if "crontab" in local_collectors:
        collect_crontab(local_path)
    if "packages" in local_collectors:
        collect_packages(local_path)

    print(f"✅ Evidence collected in: {output_path}")

if __name__ == "__main__":
    main()
