#!/usr/bin/env python3
"""
Test script for AWS Unused Resource Analyzer.

This script demonstrates how to use the resource analyzer functionality
to find and report on unused AWS resources.
"""

import boto3
import os
import argparse
from rich.console import Console

from aws_finops_dashboard.resource_analyzer import UnusedResourceAnalyzer
from aws_finops_dashboard.resource_analyzer_export import export_unused_resources

console = Console()


def main():
    """Run the test script."""
    parser = argparse.ArgumentParser(description="Test AWS Unused Resource Analyzer")
    parser.add_argument(
        "--profile", "-p", help="AWS profile to use", default="default", type=str
    )
    parser.add_argument(
        "--regions",
        "-r",
        nargs="+",
        help="AWS regions to check (space-separated)",
        type=str,
    )
    parser.add_argument(
        "--lookback-days",
        "-l",
        help="Number of days to look back for usage analysis",
        type=int,
        default=14,
    )
    parser.add_argument(
        "--output-format",
        "-o",
        choices=["json", "csv", "pdf"],
        help="Output format for report",
        type=str,
        default="pdf",
    )
    parser.add_argument(
        "--output-dir",
        "-d",
        help="Directory to save the output file",
        type=str,
        default=os.getcwd(),
    )

    args = parser.parse_args()

    try:
        # Create AWS session
        session = boto3.Session(profile_name=args.profile)
        
        # Create and run the analyzer
        console.print("[cyan]Creating resource analyzer...[/]")
        analyzer = UnusedResourceAnalyzer(session, args.lookback_days)
        
        # Display results on console
        console.print("[cyan]Analyzing resources...[/]")
        analyzer.display_unused_resources(args.regions)
        
        # Export results to file
        console.print(f"[cyan]Exporting results to {args.output_format.upper()}...[/]")
        report_data = analyzer.get_all_unused_resources(args.regions)
        output_file = export_unused_resources(
            report_data,
            output_format=args.output_format,
            output_dir=args.output_dir,
            report_name=f"test_unused_resources_{args.profile}"
        )
        console.print(f"[green]Report exported to: [bold]{output_file}[/bold][/]")
        
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/]")
        import traceback
        console.print(traceback.format_exc())
        return 1
        
    return 0


if __name__ == "__main__":
    exit(main()) 