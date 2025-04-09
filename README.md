# AWS FinOps Dashboard (CLI)

A terminal-based AWS cost and resource dashboard built with Python and the [Rich](https://github.com/Textualize/rich) library.  
It provides an overview of AWS spend by profile, service-level breakdowns, budget tracking, and EC2 instance summaries.

---

## Features

- Current & last month's total spend  
- Cost by AWS service (sorted by highest cost)  
- AWS Budgets info (limit, actual)  
- EC2 instance status across regions with detailed state information
- Automatic profile detection and selection
- Combine multiple profiles from the same AWS account
- Specify custom regions for EC2 instance discovery
- Improved error handling and resilience
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

> If you don't have a `requirements.txt`, here's a quick one:

```
boto3
rich
```

---

## Set Up AWS CLI Profiles

If you haven't already, configure your named profiles using the AWS CLI:

```bash
aws configure --profile 01
aws configure --profile 02
aws configure --profile 03
```

Repeat this for all the profiles you want to track in your dashboard.

---

## Command Line Usage

The dashboard now supports command line arguments, eliminating the need to modify the script directly:

```bash
python dashboard.py [options]
```

### Command Line Options

```
--profiles, -p  Specific AWS profiles to use (space-separated)
--regions, -r   AWS regions to check for EC2 instances (space-separated)
--all, -a       Use all available AWS profiles
--combine, -c   Combine profiles from the same AWS account
```

### Examples

```bash
# Use default profile
python dashboard.py

# Use specific profiles
python dashboard.py --profiles dev prod

# Use all available profiles
python dashboard.py --all

# Combine profiles from the same AWS account
python dashboard.py --all --combine

# Specify custom regions to check
python dashboard.py --regions us-east-1 eu-west-1 ap-southeast-2
```

---

## Run the script

```bash
python dashboard.py [options]
```

You'll now see a live-updating table of your AWS account cost and usage details, right in your terminal.

---

## Example Output

![alt text](<Screenshot 2025-04-06 at 12.32.09 PM.png>)

---

## Cost For Every Run

AWS charges USD 0.01 for every API call. The number of API calls made by this script depends on the regions and profiles specified:

| API Service       | Calls per AWS profile/account |
|--------------------|-------------------------------|
| Cost Explorer      | 3 `get_cost_and_usage` calls  |
| Budgets            | 1 `describe_budgets` call    |
| EC2 (describe)     | 1 call per region queried     |
| Total per profile  | Varies based on regions      |

### Example Scenarios:

1. **Single Profile, Single Region**:
   - **API Calls**: 5
     - 3 Cost Explorer calls
     - 1 Budgets call
     - 1 EC2 call for the specified region

2. **Single Profile, All Regions (31 regions)**:
   - **API Calls**: 38
     - 3 Cost Explorer calls
     - 1 Budgets call
     - 31 EC2 calls (one per region)

3. **Multiple Profiles, Single Region (e.g., 3 profiles)**:
   - **API Calls**: 15
     - 3 profiles × (3 Cost Explorer + 1 Budgets + 1 EC2 call)

4. **Combine Profiles for the Same Account, All Regions**:
   - **API Calls**: 35
     - 1 EC2 call per region (31 regions, queried once using the primary profile)
     - 3 Cost Explorer calls per profile
     - 1 Budgets call per profile
     - Total depends on the number of profiles.

### Notes:
- The number of API calls increases with the number of regions queried and profiles processed.
- To minimize API calls, specify only the regions and profiles you need using the `--regions` and `--profiles` arguments.
- AWS charges USD 0.01 per API call, so the cost for each run depends on the total number of API calls.

---

## Made by Ravi Kiran

Feel free to fork, contribute, or use it as a base for your own FinOps tooling.
