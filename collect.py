#!/usr/bin/env python3
import argparse
import yaml
import sys
from pathlib import Path

def load_config(path="config.yaml"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file '{path}' not found.", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Compliance Evidence Automation Script"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory (default from config)",
        default=None
    )
    parser.add_argument(
        "--collectors", "-c",
        nargs="+",
        help="Collectors to run (default from config)"
    )
    parser.add_argument(
        "--aws-profile",
        help="AWS profile to use (default from config)"
    )
    parser.add_argument(
        "--no-aws",
        action="store_true",
        help="Skip AWS collectors"
    )

    args = parser.parse_args()

    config = load_config()

    print("✅ Script started")
    print(f"Output dir: {args.output or config['output']['base_dir']}")
    print(f"Collectors: {args.collectors or config['collectors']}")
    print(f"AWS Profile: {args.aws_profile or config['aws']['profile']}")
    print(f"Skip AWS: {args.no_aws}")

if __name__ == "__main__":
    main()
