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
git clone https://github.com/ravikiranvm/aws-finops-dashboard.git
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

## Update the script with your profiles & regions

Open the Python script and modify the list of profiles:

```python
profiles = ['01', '02', '03']  # Add your AWS named profiles here
```

You may modify the regions list as per your need:
```python
regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-southeast-1', 'ap-south-1'] # Add your most used regions here
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

## Cost For Every Run

AWS charges USD 0.01 for every API call. Currently this script makes 10 API calls per account on every run. 

| API Service | Calls per AWS profile/account |
| --- | --- |
| Cost Explorer | 3 get_cost_and_usage calls |
| Budgets | 1 describe_budgets call |
| EC2 (describe) | 6 calls (one per region) |
| Total per profile/account | 10 API calls |

---

## Made by Ravi Kiran

Feel free to fork, contribute, or use it as a base for your own FinOps tooling.

