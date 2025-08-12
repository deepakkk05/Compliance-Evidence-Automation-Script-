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

#Add ZIP helper function
import shutil

def zip_evidence(output_path):
    """Compress the entire output folder into a .zip archive."""
    try:
        zip_file = shutil.make_archive(str(output_path), 'zip', str(output_path))
        logging.info(f"Evidence successfully zipped: {zip_file}")
        return zip_file
    except Exception as e:
        logging.error(f"Failed to create ZIP archive: {e}")
        return None


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

import boto3
from botocore.exceptions import NoCredentialsError, ClientError

# ----------------- AWS COLLECTORS -----------------
def aws_client(service, profile, region):
    """Create a boto3 client with optional profile."""
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        return session.client(service)
    except Exception as e:
        logging.error(f"Failed to create AWS client for {service}: {e}")
        return None

def collect_s3_buckets(output_path, profile, region):
    client = aws_client("s3", profile, region)
    if not client:
        return
    try:
        response = client.list_buckets()
        with open(output_path / "s3_buckets.json", "w", encoding="utf-8") as f:
            json.dump(response.get("Buckets", []), f, indent=2, default=str)
        logging.info("AWS S3 buckets collected.")
    except (NoCredentialsError, ClientError) as e:
        logging.error(f"Error collecting S3 buckets: {e}")

def collect_security_groups(output_path, profile, region):
    client = aws_client("ec2", profile, region)
    if not client:
        return
    try:
        response = client.describe_security_groups()
        with open(output_path / "security_groups.json", "w", encoding="utf-8") as f:
            json.dump(response.get("SecurityGroups", []), f, indent=2, default=str)
        logging.info("AWS security groups collected.")
    except (NoCredentialsError, ClientError) as e:
        logging.error(f"Error collecting security groups: {e}")

def collect_iam_users(output_path, profile, region):
    client = aws_client("iam", profile, region)
    if not client:
        return
    try:
        response = client.list_users()
        with open(output_path / "iam_users.json", "w", encoding="utf-8") as f:
            json.dump(response.get("Users", []), f, indent=2, default=str)
        logging.info("AWS IAM users collected.")
    except (NoCredentialsError, ClientError) as e:
        logging.error(f"Error collecting IAM users: {e}")
# ---------------------------------------------------


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

    # -------- Local collectors with error handling --------
    local_collectors = args.collectors or config["collectors"].get("local", [])
    for collector in local_collectors:
        try:
            if collector == "uname":
                collect_uname(local_path)
            elif collector == "processes":
                collect_processes(local_path)
            elif collector == "crontab":
                collect_crontab(local_path)
            elif collector == "packages":
                collect_packages(local_path)
        except Exception as e:
            logging.error(f"Collector {collector} failed: {e}")

    # -------- AWS collectors with error handling --------
    if not args.no_aws:
        aws_collectors = config["collectors"].get("aws", [])
        profile = args.aws_profile or config["aws"]["profile"]
        region = config["aws"]["region"]

        aws_path = output_path / "aws"
        aws_path.mkdir(exist_ok=True)

        for aws_collector in aws_collectors:
            try:
                if aws_collector == "s3":
                    collect_s3_buckets(aws_path, profile, region)
                elif aws_collector == "security_groups":
                    collect_security_groups(aws_path, profile, region)
                elif aws_collector == "iam_users":
                    collect_iam_users(aws_path, profile, region)
            except Exception as e:
                logging.error(f"AWS collector {aws_collector} failed: {e}")

    # -------- ZIP everything --------
    zip_evidence(output_path)

    print(f"✅ Evidence collected in: {output_path}")

if __name__ == "__main__":
    main()
