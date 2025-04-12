# AWS FinOps Dashboard (CLI) v2.1.1

[![PyPI version](https://img.shields.io/pypi/v/aws-finops-dashboard.svg)](https://pypi.org/project/aws-finops-dashboard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/ravikiranvm/aws-finops-dashboard.svg)](https://github.com/ravikiranvm/aws-finops-dashboard/stargazers)

A terminal-based AWS cost and resource dashboard built with Python and the [Rich](https://github.com/Textualize/rich) library.
It provides an overview of AWS spend by profile, service-level breakdowns, budget tracking, EC2 instance summaries, and allows exporting data to CSV.

---

## Features

- Current & last month's total spend
- Cost by AWS service (sorted by highest cost)
- AWS Budgets info (limit, actual)
- EC2 instance status across specified/accessible regions with detailed state information
- Automatic profile detection and selection
- Combine multiple profiles from the same AWS account using `--combine`
- Specify custom regions for EC2 instance discovery using `--regions`
- **Export dashboard data to a timestamped CSV file using `--export-csv`**
  - CSV includes multi-line cells for detailed breakdowns (best viewed in spreadsheet software)
  - Specify output directory using `--dir`
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
  - `ec2:DescribeRegions`
  - `sts:GetCallerIdentity`

---

## Installation

### Install using pipx (Recommended)
```bash
pipx install aws-finops-dashboard
```

If you don’t have `pipx`, install it with:

```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

---

## Set Up AWS CLI Profiles

If you haven't already, configure your named profiles using the AWS CLI:

```bash
aws configure --profile profile1-name
aws configure --profile profile2-name
# ... etc ...
```

Repeat this for all the profiles you want the dashboard to potentially access.

---

## Command Line Usage

Run the script using `aws-finops` followed by options:

```bash
aws-finops [options]
```

### Command Line Options

| Flag | Description |
|---|---|
| --profiles, -p | Specific AWS profiles to use (space-separated). If omitted, uses 'default' profile if available, otherwise all profiles. |
| --regions, -r | Specific AWS regions to check for EC2 instances (space-separated). If omitted, attempts to check all accessible regions. |
| --all, -a | Use all available AWS profiles found in your config. |
| --combine, -c | Combine profiles from the same AWS account into single rows. |
| --export-csv, -e | Export the dashboard data to a CSV file. Provide a base filename (timestamp will be added automatically). |
| --dir, -d | Directory to save the CSV file (default: current directory). Requires --export-csv to be set. |


### Examples

```bash
# Use default profile, show output in terminal only
aws-finops

# Use specific profiles 'dev' and 'prod'
aws-finops --profiles dev prod

# Use all available profiles
aws-finops --all

# Combine profiles from the same AWS account
aws-finops --all --combine

# Specify custom regions to check for EC2 instances
aws-finops --regions us-east-1 eu-west-1 ap-southeast-2

# Export data for all profiles to 'aws_dashboard_data_YYYYMMDD_HHMM.csv' in the current directory
aws-finops --all --export-csv aws_dashboard_data

# Export combined data for 'dev' and 'prod' profiles to 'report_YYYYMMDD_HHMM.csv' in 'output_reports' directory
aws-finops --profiles dev prod --combine --export-csv report --dir output_reports
```

You'll see a live-updating table of your AWS account cost and usage details in the terminal. If `--export-csv` is used, a CSV file will also be generated upon completion.

---

## Example Terminal Output

![Dashboard Screenshot](dashboard_image.png)

---

## CSV Output Format

When using `--export-csv`, a CSV file is generated with the following columns:

- `CLI Profile`
- `AWS Account ID`
- `Last Month Cost`
- `Current Month Cost`
- `Cost By Service` (Each service and its cost appears on a new line within the cell)
- `Budget Status` (Each budget's limit and actual spend appears on a new line within the cell)
- `EC2 Instances` (Each instance state and its count appears on a new line within the cell)

**Note:** Due to the multi-line formatting in some cells, it's best viewed in spreadsheet software (like Excel, Google Sheets, LibreOffice Calc) rather than plain text editors.

---

## Cost For Every Run

This script makes API calls to AWS, primarily to Cost Explorer, Budgets, EC2, and STS. AWS may charge for some API calls (e.g., `$0.01` per 1,000 `GetCostAndUsage` requests beyond the free tier, check current pricing).

The number of API calls depends heavily on the options used:

-   **Cost Explorer & Budgets:** Typically 3 `ce:GetCostAndUsage` and 1 `budgets:DescribeBudgets` call per profile processed.
-   **STS:** 1 `sts:GetCallerIdentity` call per profile processed (used for account ID).
-   **EC2:**
    -   1 `ec2:DescribeRegions` call initially (per session).
    -   If `--regions` is **not** specified, the script attempts to check accessibility by calling `ec2:DescribeInstances` in *multiple regions*, potentially increasing API calls significantly.
    -   If `--regions` **is** specified, 1 `ec2:DescribeInstances` call is made *per specified region* (per profile, unless `--combine` is used, where it's called once per region for the primary profile).

**To minimize API calls and potential costs:**

-   Use the `--profiles` argument to specify only the profiles you need.
-   Use the `--regions` argument to limit EC2 checks to only relevant regions. This significantly reduces `ec2:DescribeInstances` calls compared to automatic region discovery.

The exact cost per run is usually negligible but depends on the scale of your usage and AWS pricing.

---

## Made by Ravi Kiran

Open to contributions! Feel free to fork and contribute.

```bash
# If you haven't already cloned it
git clone https://github.com/ravikiranvm/aws-finops-dashboard
cd aws-finops-dashboard
pip install -r requirements.txt
python dashboard.py --help
```

---

## Acknowledgments

Special thanks to [cschnidr](https://github.com/cschnidr) for their valuable contributions to significantly improve this project!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.