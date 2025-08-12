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

def load_config(path="config.yaml"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file '{path}' not found.", file=sys.stderr)
        sys.exit(1)

def create_output_dir(base_dir):
    """Create timestamped output directory."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    hostname = socket.gethostname()
    folder_name = f"{timestamp}_{hostname}"
    output_path = Path(base_dir) / folder_name
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

def init_logger(log_path):
    """Initialize logger that writes to a file."""
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logging.info("Logger initialized.")

def save_env_metadata(output_path):
    """Save environment metadata to env_metadata.json."""
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

    # NEW — Create output folder
    output_path = create_output_dir(base_output)

    # NEW — Initialize logging
    init_logger(output_path / "collect.log")
    logging.info("Script started.")
    logging.info(f"Output directory: {output_path}")

    # NEW — Save environment metadata
    save_env_metadata(output_path)

    print(f"✅ Output directory created: {output_path}")
    print(f"   - collect.log")
    print(f"   - env_metadata.json")

if __name__ == "__main__":
    main()
