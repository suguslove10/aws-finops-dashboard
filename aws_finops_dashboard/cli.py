import argparse
import os
import sys
from typing import Any, Dict, List, Optional

from packaging import version
from rich.console import Console
import boto3

from aws_finops_dashboard.helpers import load_config_file
from aws_finops_dashboard.dashboard_runner import run_dashboard
from aws_finops_dashboard.ri_optimizer import RIOptimizer
from aws_finops_dashboard.aws_client import get_aws_profiles
from aws_finops_dashboard.resource_analyzer import UnusedResourceAnalyzer, analyze_unused_resources
from aws_finops_dashboard.resource_analyzer_export import export_unused_resources

console = Console()


def welcome_banner():
    """Display a welcome banner."""
    print(
        """
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
"""
    )
    import pkg_resources

    try:
        version_str = pkg_resources.get_distribution("aws-finops-dashboard").version
        print(f"AWS FinOps Dashboard CLI (v{version_str})")
        print()
    except pkg_resources.DistributionNotFound:
        print("AWS FinOps Dashboard CLI (development version)")
        print()


def check_latest_version():
    """Check for the latest version of the package."""
    try:
        import requests

        current_version = version.parse(
            pkg_resources.get_distribution("aws-finops-dashboard").version
        )
        response = requests.get(
            "https://pypi.org/pypi/aws-finops-dashboard/json", timeout=1
        )
        latest_version = version.parse(response.json()["info"]["version"])

        if latest_version > current_version:
            console.print(
                f"[yellow]A new version of AWS FinOps Dashboard is available: {latest_version} (current: {current_version})[/]"
            )
            console.print(
                "[yellow]Run 'pip install --upgrade aws-finops-dashboard' to update.[/]"
            )
            print()
    except Exception:
        # Silently ignore any errors when checking for updates
        pass


def main() -> int:
    """Command-line interface entry point."""
    welcome_banner()
    check_latest_version()

    # Create the parser instance to be accessible for get_default
    parser = argparse.ArgumentParser(description="AWS FinOps Dashboard CLI")

    # Add all arguments
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
        default=2.0,
        help="Sensitivity for anomaly detection (default: 2.0)",
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
    # Add the new RI optimizer arguments
    parser.add_argument(
        "--ri-optimizer",
        action="store_true",
        help="Generate Reserved Instance and Savings Plan recommendations",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=30,
        help="Number of days to analyze for RI recommendations (default: 30)",
    )
    
    # Add unused resource analyzer arguments
    parser.add_argument(
        "--resource-analyzer",
        action="store_true",
        help="Find and report on unused AWS resources",
    )
    parser.add_argument(
        "--resource-types",
        nargs="+",
        choices=["ec2", "ebs", "eip", "all"],
        default=["all"],
        help="Resource types to analyze (default: all)",
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

    # Handle RI optimizer command specifically
    if args.ri_optimizer:
        run_ri_optimizer(args)
        return 0
        
    # Handle resource analyzer command
    if args.resource_analyzer:
        run_resource_analyzer(args)
        return 0

    result = run_dashboard(args)
    return 0 if result == 0 else 1


def run_ri_optimizer(args):
    """Run the RI optimizer with the given arguments."""
    # Get AWS session based on arguments
    profiles = []

    if args.profiles:
        profiles = args.profiles
    elif args.all:
        profiles = get_aws_profiles()
    else:
        default_profile = "default"
        if default_profile in get_aws_profiles():
            profiles = [default_profile]
        else:
            profiles = get_aws_profiles()

    if not profiles:
        console.print("[bold red]No AWS profiles found. Please configure AWS CLI first.[/]")
        sys.exit(1)
    
    console.print("[bold cyan]===== AWS Reserved Instance & Savings Plan Optimizer =====[/]\n")
    console.print("[bright_blue]Analyzing usage patterns to generate cost-saving recommendations...[/]\n")

    for profile in profiles:
        console.print(f"[bold bright_magenta]Analyzing profile: {profile}[/]")
        session = boto3.Session(profile_name=profile)
        
        # Create and run the optimizer
        optimizer = RIOptimizer(session, args.lookback_days)
        optimizer.display_recommendations()
        
        # Force PDF generation if requested
        if args.report_name and 'pdf' in args.report_type:
            console.print(f"\n[bright_cyan]Exporting PDF report for {profile}...[/]")
            
            from aws_finops_dashboard.dashboard_runner import _export_ri_recommendations_to_pdf
            
            try:
                # Get recommendations
                ri_recommendations = optimizer.get_ri_recommendations()
                sp_recommendations = optimizer.get_savings_plan_recommendations()
                
                # Get account ID
                account_id = session.client('sts').get_caller_identity().get('Account', 'Unknown')
                
                # Force export to PDF
                _export_ri_recommendations_to_pdf(
                    profile,
                    account_id,
                    ri_recommendations,
                    sp_recommendations,
                    args.report_name,
                    args.dir
                )
                console.print(f"[bright_green]PDF report generated successfully![/]")
            except Exception as e:
                console.print(f"[bold red]Error generating PDF: {str(e)}[/]")
                import traceback
                console.print(traceback.format_exc())
        
    console.print("\n[bright_green]Analysis complete![/]")
    console.print("[yellow]Note: These recommendations are based on historical usage patterns. Review carefully before purchasing.[/]")


def run_resource_analyzer(args):
    """Run the unused resource analyzer with the given arguments."""
    # Get AWS session based on arguments
    profiles = []

    if args.profiles:
        profiles = args.profiles
    elif args.all:
        profiles = get_aws_profiles()
    else:
        default_profile = "default"
        if default_profile in get_aws_profiles():
            profiles = [default_profile]
        else:
            profiles = get_aws_profiles()

    if not profiles:
        console.print("[bold red]No AWS profiles found. Please configure AWS CLI first.[/]")
        sys.exit(1)
    
    console.print("[bold cyan]===== AWS Unused Resource Analyzer =====[/]\n")
    console.print("[bright_blue]Analyzing resources to find unused or underutilized items...[/]\n")

    for profile in profiles:
        try:
            console.print(f"[cyan]Analyzing profile: [bold]{profile}[/bold][/]")
            
            # Create AWS session
            session = boto3.Session(profile_name=profile)
            
            # Create and run the analyzer
            analyzer = UnusedResourceAnalyzer(session, args.lookback_days or 14)
            
            # Display results on console
            analyzer.display_unused_resources(args.regions)
            
            # Export results if report type and name are specified
            if args.report_type and args.report_name:
                report_data = analyzer.get_all_unused_resources(args.regions)
                
                for report_type in args.report_type:
                    output_file = export_unused_resources(
                        report_data,
                        output_format=report_type,
                        output_dir=args.dir,
                        report_name=f"{args.report_name}_unused_resources_{profile}"
                    )
                    console.print(f"[green]Report exported to: [bold]{output_file}[/bold][/]")
                
        except Exception as e:
            console.print(f"[bold red]Error analyzing profile {profile}: {str(e)}[/]")
            import traceback
            console.print(traceback.format_exc())
            
    console.print("\n[bold green]Resource analysis complete![/]")


if __name__ == "__main__":
    sys.exit(main())
