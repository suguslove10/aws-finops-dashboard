import argparse
import sys


def parse_args():
    """Parse command line arguments for the AWS FinOps Dashboard."""
    parser = argparse.ArgumentParser(description="AWS FinOps Dashboard CLI")
    parser.add_argument(
        "--profiles",
        "-p",
        nargs="+",
        help="Specific AWS profiles to use (space-separated)",
    )
    parser.add_argument(
        "--regions",
        "-r",
        nargs="+",
        help="AWS regions to check for EC2 instances (space-separated)",
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
    )
    parser.add_argument(
        "--report-type",
        "-y",
        nargs="+",
        choices=["csv", "json"],
        help="Specify one or more report types: csv and/or json (space-separated)",
        default=["csv"],
    )
    parser.add_argument(
        "--dir",
        "-d",
        help="Directory to save the report files (default: current directory)",
    )
    parser.add_argument(
        "--time-range",
        "-t",
        help="Time range for cost data in days (default: current month). Examples: 7, 30, 90",
        type=int,
    )

    return parser.parse_args()


def main():
    """Command-line interface entry point."""
    from aws_finops_dashboard.main import run_dashboard

    args = parse_args()
    return run_dashboard(args)


if __name__ == "__main__":
    sys.exit(main())
