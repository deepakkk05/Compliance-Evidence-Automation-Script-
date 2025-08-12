# Compliance Evidence Automation Script

## 📌 Overview
This project is a **Python-based compliance evidence collection automation tool** designed to gather system, process, and AWS cloud resource data in a structured way.  
It creates a timestamped folder containing all collected evidence, logs, and metadata, and finally compresses everything into a `.zip` file for easy storage or submission.

The tool is **config-driven**, supports **parallel execution** with progress bars, and can collect:
- **Local system evidence** (e.g., OS info, running processes, installed packages)
- **AWS cloud resource details** (e.g., S3 buckets, IAM users, security groups)

---

## 🚀 Features
- **Local Evidence Collection**
  - System information (`uname` / `systeminfo`)
  - Running processes
  - Cron jobs / Scheduled tasks
  - Installed packages
- **AWS Cloud Evidence Collection**
  - S3 bucket listing
  - Security group details
  - IAM user listing
- **Parallel Execution**
  - Uses `ThreadPoolExecutor` for faster execution
  - Progress bar support via `tqdm`
- **Metadata Logging**
  - Environment details (OS, Python version, username, hostname, timestamp)
- **Summary Report Generation**
  - Creates comprehensive summary of all collected evidence
  - Includes statistics and overview of findings
- **Automatic Archiving**
  - Compresses results into `.zip` format for portability
- **Configurable**
  - YAML-based configuration file
  - Command-line arguments for flexibility

---

## 📂 Project Structure
```
compliance_evidence/
│
├── config.yaml                # Main configuration file
├── compliance_evidence.py     # Main Python script
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

---

## 🔄 Workflow Diagram
```
┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐
│ Load Config │───▶│ Create Timestmp │───▶│ Initialize Logs  │
└─────────────┘    │ Output Directory│    │ & Metadata       │
                   └─────────────────┘    └──────────────────┘
                                                     │
┌─────────────┐    ┌─────────────────┐    ┌──────────────────┘
│ Create ZIP  │◀───│ Generate Summary│◀───│ Run Local &      │
│ Archive     │    │ Report          │    │ AWS Collectors   │
└─────────────┘    └─────────────────┘    └──────────────────┘
```

---

## ⚙️ Installation
1. **Clone the repository**
```bash
git clone https://github.com/yourusername/compliance-evidence.git
cd compliance-evidence
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Ensure AWS CLI is configured** (if AWS collectors are used)
```bash
aws configure
```

---

## 📜 Configuration (config.yaml)
Example:

```yaml
output:
  base_dir: "./evidence"

collectors:
  local:
    - uname
    - processes
    - crontab
    - packages
  aws:
    - s3
    - security_groups
    - iam_users

aws:
  profile: "default"
  region: "us-east-1"
```

---

## ▶️ Usage

### Run with default config
```bash
python compliance_evidence.py
```

### Specify output directory
```bash
python compliance_evidence.py --output ./my_evidence
```

### Run specific collectors
```bash
python compliance_evidence.py --collectors uname processes
```

### Skip AWS collectors
```bash
python compliance_evidence.py --no-aws
```

### Use specific AWS profile
```bash
python compliance_evidence.py --aws-profile myprofile
```

---

## 📊 Example Output Structure
```
2025-08-13_14-23-45_MyLaptop/
│
├── collect.log
├── env_metadata.json
├── summary_report.json          # Comprehensive summary of all evidence
├── local/
│   ├── uname.txt
│   ├── processes.txt
│   ├── crontab.txt
│   └── packages.txt
├── aws/
│   ├── s3_buckets.json
│   ├── security_groups.json
│   └── iam_users.json
└── 2025-08-13_14-23-45_MyLaptop.zip
```

---

## 🛠 Dependencies
- **Python 3.7+**
- **boto3** – AWS SDK for Python
- **PyYAML** – For reading YAML config
- **tqdm** – For progress bars
- **AWS credentials configured** (for AWS collectors)

Install them via:
```bash
pip install boto3 pyyaml tqdm
```

---

## 🧩 How It Works
1. Load configuration from `config.yaml` or CLI args.
2. Create timestamped output directory with hostname.
3. Initialize logging and save environment metadata.
4. Run local collectors in parallel (with progress bar).
5. Run AWS collectors (if not skipped).
6. Generate comprehensive summary report of all collected evidence.
7. Zip the evidence folder.
8. Display success message with output location.

---

## ⚠️ Notes
- AWS collectors require valid credentials with appropriate permissions.
- For Linux-based systems, some commands like `dpkg` or `rpm` are used depending on the package manager.
- On Windows, collectors will use PowerShell / CMD equivalents.

---

