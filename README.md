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
git clone https://github.com/suguslove10/aws-finops-dashboard.git
cd aws-finops-dashboard

# Install Python dependencies
pip install -e .

# Install frontend dependencies
cd frontend/aws-finops-ui
npm install
cd ../..
```

### Option 3: Docker Compose Installation

You can also run the entire application using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/suguslove10/aws-finops-dashboard.git
cd aws-finops-dashboard

# Build and start the containers
docker-compose up -d

# The application will be available at:
# - Frontend: http://localhost:3001
# - Backend API: http://localhost:5001
```

**Note:** When using Docker, you need to configure AWS credentials using one of these methods:
1. Mount your AWS credentials by ensuring `~/.aws` exists
2. Add credentials through the web UI
3. Use environment variables in the Docker Compose file

#### Docker Troubleshooting

If you encounter issues with the Docker setup:

```bash
# Remove existing containers
docker-compose down

# Rebuild containers without using cache
docker-compose build --no-cache

# Start services and view logs
docker-compose up
```

If the frontend container fails to build due to ESLint errors, this is expected and the configuration has been adjusted to ignore these during the build process.

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

## API Communication

The frontend communicates with the backend through API routes in Next.js. Here's how the data flow works:

### Command Execution
- When you interact with the frontend UI (clicking buttons, submitting forms), the frontend sends requests to `/api/run-command` route
- This route executes the AWS FinOps CLI command using child_process.exec
- The Python backend processes AWS data and generates formatted output

### Data Flow
- The frontend sends parameters (profiles, regions, currency, etc.) to the API
- The API constructs and executes the CLI command
- The CLI command returns JSON or formatted text output
- The API sends this output back to the frontend

### Report Downloads
- When downloading reports, the frontend sends a request to `/api/download-report`
- This route finds the generated report file (CSV/JSON/PDF) and serves it
- The file gets downloaded through the browser

### Debugging Notes
- If you're having issues, check the browser console and the terminal where you're running Next.js
- The output from the backend should appear in the terminal and be passed back to the frontend
- The improvements made should now be working properly - with accurate currency conversion, better error handling, and clearer display of data in the dashboard.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributors

Special thanks to all contributors who have helped improve this project!