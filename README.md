# AWS FinOps Dashboard

[![PyPI version](https://img.shields.io/pypi/v/aws-finops-dashboard.svg)](https://pypi.org/project/aws-finops-dashboard/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The AWS FinOps Dashboard is a comprehensive open-source tool for AWS cost management and optimization. It provides detailed cost analysis, resource usage monitoring, anomaly detection, and optimization recommendations across multiple AWS accounts.

## Features

- **Multi-Account Cost Analysis**: View costs across multiple AWS accounts and regions
- **Cost Breakdowns**: By service, region, tag, and time period
- **Resource Management**: Identify idle, underutilized, and untagged resources
- **AI/ML Capabilities**: 
  - Machine learning-based anomaly detection
  - AI-powered cost optimization recommendations
- **Reserved Instance Optimizer**: Get data-driven recommendations for RI purchases and Savings Plans
- **Multi-Currency Support**: View costs in USD, EUR, INR, GBP, JPY, AUD, CAD, or CNY
- **Flexible Export Options**: Generate reports in CSV, JSON, or PDF formats
- **Two Interfaces**: Command-line interface (CLI) and web-based user interface (UI)

![AWS FinOps Dashboard](aws-finops-dashboard-v2.2.3.png)

## Project Structure

```
aws-finops-dashboard/
├── aws_finops_dashboard/     # Python backend package
│   ├── __init__.py           # Package initialization
│   ├── cli.py                # Command-line interface
│   ├── api.py                # REST API for web UI
│   ├── web_ui.py             # Web server interface
│   ├── dashboard_runner.py   # Core dashboard functionality
│   ├── aws_client.py         # AWS API client
│   ├── helpers.py            # Utility functions
│   ├── anomaly_detection.py  # ML-based anomaly detection
│   ├── cost_processor.py     # Cost data processing
│   ├── optimization_recommendations.py  # AI cost recommendations
│   ├── ri_optimizer.py       # Reserved Instance optimization
│   └── ...                   # Other modules
│
├── frontend/                 # React/Next.js frontend
│   └── aws-finops-ui/        # Web UI code
│
├── start.sh                  # Startup script for web UI (Unix/Mac)
└── start.bat                 # Startup script for web UI (Windows)
```

## Prerequisites

- **Python 3.8+**: The dashboard requires Python 3.8 or newer
- **Node.js 18+** (only for web UI): Required if you want to use the web interface
- **AWS CLI configured**: The tool uses your AWS CLI profiles for authentication
- **AWS IAM permissions**:
  ```
  ce:GetCostAndUsage
  budgets:ViewBudget
  ec2:DescribeInstances
  ec2:DescribeRegions
  sts:GetCallerIdentity
  ec2:DescribeInstances
  ec2:DescribeVolumes
  ec2:DescribeAddresses
  rds:DescribeDBInstances
  rds:ListTagsForResource
  lambda:ListFunctions
  lambda:ListTags
  elbv2:DescribeLoadBalancers
  elbv2:DescribeTags
  ```

## Installation

### Option 1: Install CLI Only (Recommended for most users)

```bash
# Using pipx (recommended for isolated installation)
pipx install aws-finops-dashboard

# If you don't have pipx
python -m pip install --user pipx
python -m pipx ensurepath

# OR using regular pip
pip install aws-finops-dashboard
```

### Option 2: Full Installation (CLI + Web UI)

```bash
# Clone the repository
git clone https://github.com/ravikiranvm/aws-finops-dashboard.git
cd aws-finops-dashboard

# Install Python dependencies
pip install -e .

# Install frontend dependencies
cd frontend/aws-finops-ui
npm install
cd ../..
```

## AWS CLI Profile Setup

Configure your AWS profiles with the required permissions:

```bash
# Configure AWS profiles
aws configure --profile dev-account
aws configure --profile prod-account

# Verify your profiles
aws configure list-profiles
```

## Usage

### Command Line Interface (CLI)

The tool can be run directly from the command line with various options:

```bash
# Basic usage - shows current month's costs for default profile
aws-finops

# Use specific AWS profiles
aws-finops --profiles dev-account prod-account

# Use all available profiles
aws-finops --all

# Combine profiles from the same AWS account
aws-finops --all --combine

# Analyze specific regions
aws-finops --regions us-east-1 eu-west-1 ap-south-1

# View cost data for last 30 days
aws-finops --time-range 30

# Filter by cost allocation tags
aws-finops --tag Team=DevOps Environment=Production

# Export data to CSV
aws-finops --all --report-name aws_costs --report-type csv

# Generate PDF report
aws-finops --all --report-name aws_costs --report-type pdf

# View cost trend analysis (last 6 months)
aws-finops --all --trend

# Run FinOps audit report
aws-finops --all --audit

# Detect spending anomalies using machine learning
aws-finops --all --detect-anomalies

# Get AI-powered cost optimization recommendations
aws-finops --all --optimize

# Get Reserved Instance recommendations
aws-finops --all --ri-optimizer

# Display costs in a different currency
aws-finops --all --currency INR
```

### Web UI

The web interface provides an interactive dashboard experience:

```bash
# Start the web UI (from the repository root)
# On macOS/Linux:
./start.sh

# On Windows:
start.bat
```

This will:
1. Start the backend API server
2. Launch the Next.js frontend
3. Open your browser to the dashboard (typically http://localhost:3000)

Through the web UI, you can:
- Select AWS profiles and regions
- View cost dashboards and analysis
- Generate reports
- Run optimization and anomaly detection
- Download reports in various formats

## Configuration Files

For repeatable operations, you can use configuration files in TOML, YAML, or JSON format:

### Example `config.toml`:

```toml
profiles = ["dev-account", "prod-account"]
regions = ["us-east-1", "eu-west-2"]
combine = true
report_name = "monthly_finops_summary"
report_type = ["csv", "pdf"]
dir = "./reports"
time_range = 30
tag = ["CostCenter=Engineering", "Project=Phoenix"]
```

Then run:

```bash
aws-finops --config-file config.toml
```

## Currency Support

The dashboard supports multiple currencies for cost display:

```bash
# Display costs in Indian Rupees
aws-finops --all --currency INR

# Other supported currencies: USD (default), EUR, GBP, JPY, AUD, CAD, CNY
```

## Cost For Every Run

Running this tool incurs minimal AWS costs through API calls (typically a few cents), primarily from Cost Explorer API requests.

## Troubleshooting

### Common Issues:

1. **"No profiles found"**: Ensure AWS CLI is configured with valid profiles
   ```bash
   aws configure list-profiles
   ```

2. **"Access denied"**: Check IAM permissions for your profile
   ```bash
   aws sts get-caller-identity --profile your-profile
   ```

3. **Web UI not starting**: Check that Node.js is installed and frontend dependencies are installed
   ```bash
   node --version
   cd frontend/aws-finops-ui && npm install
   ```

4. **Empty cost data**: Cost Explorer API may not have data for new accounts or may take up to 24 hours to reflect recent costs

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.