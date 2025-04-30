import argparse
import sys
from rich.console import Console
import requests
from packaging import version
import sys

console = Console()

def welcome_banner() -> None:
    banner = r"""
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
[bold bright_blue]AWS FinOps Dashboard CLI (v2.2.4)[/]                                                                         
"""
    console.print(banner)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for the AWS FinOps Dashboard."""
    parser = argparse.ArgumentParser(description="AWS FinOps Dashboard CLI")

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
        choices=["csv", "json"],
        help="Specify one or more report types: csv and/or json (space-separated)",
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

    return parser.parse_args()

__version__ = "2.2.4"
def check_latest_version() -> None:
    """Check for the latest version of the AWS FinOps Dashboard (CLI)."""
    try:
        response = requests.get("https://pypi.org/pypi/aws-finops-dashboard/json", timeout=3)
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
        
    args = parse_args()
    result = run_dashboard(args)
    return 0 if result == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
