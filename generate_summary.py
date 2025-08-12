import json
from pathlib import Path
import tarfile
import hashlib
import socket
from datetime import datetime

def count_public_s3_buckets(s3_file):
    count = 0
    try:
        buckets = json.loads(s3_file.read_text(encoding="utf-8"))
        # This is just bucket names, no ACL info in list_buckets, so count buckets as public if name contains 'public'
        # Ideally you'd check bucket ACLs or policies, but for demo we flag buckets with 'public' in name
        count = sum(1 for b in buckets if 'public' in b.get('Name', '').lower())
    except Exception:
        pass
    return count

def count_open_security_groups(sg_file):
    count = 0
    try:
        sgs = json.loads(sg_file.read_text(encoding="utf-8"))
        for sg in sgs:
            for perm in sg.get('IpPermissions', []):
                for ip_range in perm.get('IpRanges', []):
                    if ip_range.get('CidrIp') == '0.0.0.0/0':
                        count += 1
    except Exception:
        pass
    return count

def summarize_local(local_path):
    summary = {}

    # Count processes lines
    processes_file = local_path / "processes.txt"
    if processes_file.exists():
        summary["process_count"] = sum(1 for _ in processes_file.open(encoding="utf-8"))
    else:
        summary["process_count"] = 0

    # Check if crontab has entries
    crontab_file = local_path / "crontab.txt"
    if crontab_file.exists():
        content = crontab_file.read_text(encoding="utf-8").strip()
        summary["crontab_present"] = bool(content)
    else:
        summary["crontab_present"] = False

    # Count packages lines
    packages_file = local_path / "packages.txt"
    if packages_file.exists():
        summary["package_count"] = sum(1 for _ in packages_file.open(encoding="utf-8"))
    else:
        summary["package_count"] = 0

    return summary

def create_archive(output_path):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    hostname = socket.gethostname()
    archive_name = f"audit_evidence_{timestamp}_{hostname}.tar.gz"
    archive_path = output_path.parent / archive_name
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(output_path, arcname=output_path.name)
    return archive_path

def sha256_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def main(output_path):
    output_path = Path(output_path)
    local_path = output_path / "local"
    aws_path = output_path / "aws"

    # AWS high risk counts
    s3_buckets_file = aws_path / "s3_buckets.json"
    sg_file = aws_path / "security_groups.json"

    public_s3 = count_public_s3_buckets(s3_buckets_file) if s3_buckets_file.exists() else 0
    open_sgs = count_open_security_groups(sg_file) if sg_file.exists() else 0

    # Local summary
    local_summary = summarize_local(local_path)

    # Write summary.md
    summary_file = output_path / "summary.md"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"# Audit Summary Report\n\n")
        f.write(f"## AWS Findings\n")
        f.write(f"- Public S3 Buckets (with 'public' in name): {public_s3}\n")
        f.write(f"- Security Groups open to 0.0.0.0/0: {open_sgs}\n\n")
        f.write(f"## Local Findings\n")
        f.write(f"- Number of processes: {local_summary['process_count']}\n")
        f.write(f"- Cron jobs present: {'Yes' if local_summary['crontab_present'] else 'No'}\n")
        f.write(f"- Number of packages installed: {local_summary['package_count']}\n")

    # Create archive
    archive_path = create_archive(output_path)

    # Compute checksum
    checksum = sha256_checksum(archive_path)
    manifest_file = archive_path.parent / "manifest.txt"
    with open(manifest_file, "w") as mf:
        mf.write(f"{archive_path.name} SHA256: {checksum}\n")

    print(f"✅ Summary created at: {summary_file}")
    print(f"✅ Archive created at: {archive_path}")
    print(f"✅ Manifest created at: {manifest_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python generate_summary.py <path_to_output_directory>")
        sys.exit(1)
    main(sys.argv[1])
