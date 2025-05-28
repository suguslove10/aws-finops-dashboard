import argparse
import sys
from typing import Any, Dict, Optional

import requests
from packaging import version
from rich.console import Console

from aws_finops_dashboard.helpers import load_config_file

console = Console()

__version__ = "2.3.0"


def welcome_banner() -> None:
    banner = rf"""
[bold red]
  /$$$$$$  /$$      /$$  /$$$$$$        /$$$$$$$$ /$$            /$$$$$$                     
 /$$__  $$| $$  /$ | $$ /$$__  $$      | $$_____/|__/           /$$__  $$                    
| $$  \ $$| $$ /$$$| $$| $$  \__/      | $$       /$$ /$$$$$$$ | $$  \ $$  /$$$$$$   /$$$$$$$
| $$$$$$$$| $$/$$ $$ $$|  $$$$$$       | $$$$$   | $$| $$__  $$| $$  | $$ /$$__  $$ /$$_____/
| $$__  $$| $$$$_  $$$$ \____  $$      | $$__/   | $$| $$  \ $$| $$  | $$| $$  \ $$|  $$$$$$ 
| $$  | $$| $$$/ \  $$$ /$$  \ $$      | $$      | $$| $$  | $$| $$  | $$| $$  | $$ \____  $$
| $$  | $$| $$/   \  $$|  $$$$$$/      | $$      | $$| $$  | $$|  $$$$$$/| $$$$$$$/ /$$$$$$$/
|__/  |__/|__/     \__/ \______/       |__/      |__/|__/  |__/ \______/ | $$____/ |_______/ 
                                                                         | $$                
                                                                         | $$                
                                                                         |__/                
[/]
[bold bright_blue]AWS FinOps Dashboard CLI (v{__version__})[/]                                                                         
"""
    console.print(banner)


def check_latest_version() -> None:
    """Check for the latest version of the AWS FinOps Dashboard (CLI)."""
    try:
        response = requests.get(
            "https://pypi.org/pypi/aws-finops-dashboard/json", timeout=3
        )
        latest = response.json()["info"]["version"]
        if version.parse(latest) > version.parse(__version__):
            console.print(
                f"[bold red]A new version of AWS FinOps Dashboard is available: {latest}[/]"
            )
            console.print(
                "[bold bright_yellow]Please update using:\npipx upgrade aws-finops-dashboard\nor\npip install --upgrade aws-finops-dashboard\n[/]"
            )
    except Exception:
        pass


def main() -> int:
    """Command-line interface entry point."""
    welcome_banner()
    check_latest_version()
    from aws_finops_dashboard.main import run_dashboard

    # Create the parser instance to be accessible for get_default
    parser = argparse.ArgumentParser(description="AWS FinOps Dashboard CLI")

    parser.add_argument(
        "--config-file",
        "-C",
        help="Path to a TOML, YAML, or JSON configuration file.",
        type=str,
    )
    parser.add_argument(
        "--profiles",
        "-p",
        nargs="+",
        help="Specific AWS profiles to use (space-separated)",
        type=str,
    )
    parser.add_argument(
        "--regions",
        "-r",
        nargs="+",
        help="AWS regions to check for EC2 instances (space-separated)",
        type=str,
    )
    parser.add_argument(
        "--all", "-a", action="store_true", help="Use all available AWS profiles"
    )
    parser.add_argument(
        "--combine",
        "-c",
        action="store_true",
        help="Combine profiles from the same AWS account",
    )
    parser.add_argument(
        "--report-name",
        "-n",
        help="Specify the base name for the report file (without extension)",
        default=None,
        type=str,
    )
    parser.add_argument(
        "--report-type",
        "-y",
        nargs="+",
        choices=["csv", "json", "pdf"],
        help="Specify one or more report types: csv and/or json and/or pdf (space-separated)",
        type=str,
        default=["csv"],
    )
    parser.add_argument(
        "--dir",
        "-d",
        help="Directory to save the report files (default: current directory)",
        type=str,
    )
    parser.add_argument(
        "--time-range",
        "-t",
        help="Time range for cost data in days (default: current month). Examples: 7, 30, 90",
        type=int,
    )
    parser.add_argument(
        "--tag",
        "-g",
        nargs="+",
        help="Cost allocation tag to filter resources, e.g., --tag Team=DevOps",
        type=str,
    )
    parser.add_argument(
        "--trend",
        action="store_true",
        help="Display a trend report as bars for the past 6 months time range",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Display an audit report with cost anomalies, stopped EC2 instances, unused EBS columes, budget alerts, and more",
    )
    parser.add_argument(
        "--detect-anomalies",
        action="store_true",
        help="Detect unusual spending patterns using machine learning",
    )
    parser.add_argument(
        "--anomaly-sensitivity",
        type=float,
        default=0.05,
        help="Sensitivity for anomaly detection (0.01-0.1, lower values are more sensitive)",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Generate AI-powered cost optimization recommendations",
    )
    parser.add_argument(
        "--cpu-threshold",
        type=float,
        default=40.0,
        help="CPU utilization threshold for EC2 right-sizing recommendations (percent)",
    )
    parser.add_argument(
        "--skip-ri-analysis",
        action="store_true",
        help="Skip Reserved Instance analysis when generating optimization recommendations",
    )
    parser.add_argument(
        "--skip-savings-plans",
        action="store_true",
        help="Skip Savings Plans analysis when generating optimization recommendations",
    )
    parser.add_argument(
        "--currency",
        "-u",
        choices=["USD", "INR", "EUR", "GBP", "JPY", "AUD", "CAD", "CNY"],
        help="Currency to display costs in (default: USD)",
        type=str,
        default="USD",
    )
    parser.add_argument(
        "--enhanced-pdf",
        action="store_true",
        help="Generate enhanced PDF reports with visualizations and executive summary",
    )

    args = parser.parse_args()

    config_data: Optional[Dict[str, Any]] = None
    if args.config_file:
        config_data = load_config_file(args.config_file)
        if config_data is None:
            return 1  # Exit if config file loading failed

    # Override args with config_data if present and arg is not set via CLI
    if config_data:
        for key, value in config_data.items():
            if hasattr(args, key) and getattr(args, key) == parser.get_default(key):
                setattr(args, key, value)

    result = run_dashboard(args)
    return 0 if result == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
