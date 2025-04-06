# AWS FinOps Dashboard (CLI)

A terminal-based AWS cost and resource dashboard built with Python and the [Rich](https://github.com/Textualize/rich) library.  
It provides an overview of AWS spend by profile, service-level breakdowns, budget tracking, and EC2 instance summaries.

---

## Features

- Current & last month's total spend  
- Cost by AWS service  
- AWS Budgets info (limit, actual)  
- EC2 instance status (running/stopped) across regions  
- Beautifully styled terminal UI

---

## Prerequisites

- Python 3.8 or later
- AWS CLI configured with named profiles
- AWS credentials with permissions for:
  - `ce:GetCostAndUsage`
  - `budgets:DescribeBudgets`
  - `ec2:DescribeInstances`
  - `sts:GetCallerIdentity`

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/yourusernameravikiranvm/aws-finops-dashboard.git
cd aws-finops-dashboard
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> If you don’t have a `requirements.txt`, here’s a quick one:

```
boto3
rich
```

---

## Set Up AWS CLI Profiles

If you haven’t already, configure your named profiles using the AWS CLI:

```bash
aws configure --profile 01
aws configure --profile 02
aws configure --profile 03
```

Repeat this for all the profiles you want to track in your dashboard.

---

## Update the script with your profiles

Open the Python script and modify the list of profiles:

```python
profiles = ['01', '02', '03']  # Add your AWS named profiles here
```

---

## Run the script

```bash
python dashboard.py
```

You’ll now see a live-updating table of your AWS account cost and usage details, right in your terminal.

---

## Example Output

![alt text](<Screenshot 2025-04-06 at 12.32.09 PM.png>)

---

## Made by Ravi Kiran

Feel free to fork, contribute, or use it as a base for your own FinOps tooling.

