import argparse
import sys
from collections import defaultdict
from typing import Dict, List, Optional

import boto3
from rich import box
from rich.console import Console
from rich.live import Live
from rich.table import Column, Table

from aws_finops_dashboard.aws_client import (
    ec2_summary,
    get_accessible_regions,
    get_account_id,
    get_aws_profiles,
)
from aws_finops_dashboard.cost_processor import (
    export_to_csv,
    export_to_json,
    format_budget_info,
    format_ec2_summary,
    get_cost_data,
    process_service_costs,
)
from aws_finops_dashboard.types import BudgetInfo, ProfileData

console = Console()


def process_single_profile(
    profile: str,
    user_regions: Optional[List[str]] = None,
    time_range: Optional[int] = None,
) -> ProfileData:
    """Process a single AWS profile and return its data."""
    console.log(f"[cyan]Processing profile: {profile}...[/]")

    try:
        session = boto3.Session(profile_name=profile)
        cost_data = get_cost_data(session, time_range)

        if user_regions:
            profile_regions = user_regions
        else:
            profile_regions = get_accessible_regions(session)
            console.log(
                f"[cyan]Profile {profile} - Using regions: {', '.join(profile_regions)}[/]"
            )

        ec2_data = ec2_summary(session, profile_regions)
        service_costs, service_cost_data = process_service_costs(cost_data)
        budget_info = format_budget_info(cost_data["budgets"])
        account_id = cost_data.get("account_id", "Unknown") or "Unknown"
        ec2_summary_text = format_ec2_summary(ec2_data)

        console.log(f"[bright_cyan]Processing profile: {profile} completed[/]")

        return {
            "profile": profile,
            "account_id": account_id,
            "last_month": cost_data["last_month"],
            "current_month": cost_data["current_month"],
            "service_costs": service_cost_data,
            "service_costs_formatted": service_costs,
            "budget_info": budget_info,
            "ec2_summary": ec2_data,
            "ec2_summary_formatted": ec2_summary_text,
            "success": True,
            "error": None,
            "current_period_name": cost_data.get(
                "current_period_name", "Current month"
            ),
            "previous_period_name": cost_data.get("previous_period_name", "Last month"),
        }

    except Exception as e:
        console.log(f"[bold red]Error processing profile {profile}: {str(e)}[/]")
        return {
            "profile": profile,
            "account_id": "Error",
            "last_month": 0,
            "current_month": 0,
            "service_costs": [],
            "service_costs_formatted": [f"Failed to process profile: {str(e)}"],
            "budget_info": ["N/A"],
            "ec2_summary": {"N/A": 0},
            "ec2_summary_formatted": ["Error"],
            "success": False,
            "error": str(e),
            "current_period_name": "Current month",
            "previous_period_name": "Last month",
        }


def process_combined_profiles(
    account_id: str,
    profiles: List[str],
    user_regions: Optional[List[str]] = None,
    time_range: Optional[int] = None,
) -> ProfileData:
    """Process multiple profiles from the same AWS account."""
    console.log(
        f"[cyan]Processing combined profiles for account {account_id}: {', '.join(profiles)}...[/]"
    )

    primary_profile = profiles[0]
    console.log(
        f"[cyan]Using {primary_profile} as primary profile for EC2 discovery & cost data[/]"
    )

    primary_session = boto3.Session(profile_name=primary_profile)

    combined_current_month: float = 0.0
    combined_last_month: float = 0.0
    combined_service_costs: Dict[str, float] = defaultdict(float)
    combined_budgets: List[BudgetInfo] = []

    try:
        account_cost_data = get_cost_data(primary_session, time_range)
        combined_current_month = account_cost_data["current_month"]
        combined_last_month = account_cost_data["last_month"]
        combined_service_costs = defaultdict(float)
        for group in account_cost_data["current_month_cost_by_service"]:
            if "Keys" in group and "Metrics" in group:
                service_name = group["Keys"][0]
                cost_amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if cost_amount > 0.001:
                    combined_service_costs[service_name] += cost_amount
    except Exception as e:
        console.log(
            f"[bold red]Error getting cost data for account {account_id}: {str(e)}[/]"
        )

    combined_budgets = account_cost_data.get("budgets", [])

    if user_regions:
        primary_regions = user_regions
    else:
        primary_regions = get_accessible_regions(primary_session)
        console.log(
            f"[cyan]Primary profile {primary_profile} - Using regions: {', '.join(primary_regions)}[/]"
        )

    combined_ec2 = ec2_summary(primary_session, primary_regions)

    service_costs = []
    service_cost_data = [
        (service, cost)
        for service, cost in combined_service_costs.items()
        if cost > 0.001
    ]
    service_cost_data.sort(key=lambda x: x[1], reverse=True)

    if not service_cost_data:
        service_costs.append("No costs associated with this account")
    else:
        for service_name, cost_amount in service_cost_data:
            service_costs.append(f"{service_name}: ${cost_amount:.2f}")

    budget_info = format_budget_info(combined_budgets)

    ec2_summary_text = format_ec2_summary(combined_ec2)

    profile_list = ", ".join(profiles)

    return {
        "profile": profile_list,
        "account_id": account_id,
        "last_month": combined_last_month,
        "current_month": combined_current_month,
        "service_costs": service_cost_data,
        "service_costs_formatted": service_costs,
        "budget_info": budget_info,
        "ec2_summary": combined_ec2,
        "ec2_summary_formatted": ec2_summary_text,
        "success": True,
        "error": None,
        "current_period_name": account_cost_data.get(
            "current_period_name", "Current month"
        ),
        "previous_period_name": account_cost_data.get(
            "previous_period_name", "Last month"
        ),
    }


def create_display_table(
    previous_period_name: str = "Last Month Due",
    current_period_name: str = "Current Month Cost",
) -> Table:
    """Create and configure the display table with dynamic column names."""
    return Table(
        "AWS Account Profile",
        Column(previous_period_name, justify="right"),
        Column(current_period_name, justify="right"),
        Column("Cost By Service"),
        Column("Budget Status"),
        Column("EC2 Instance Summary", justify="center"),
        title="AWS FinOps Dashboard",
        caption="AWS FinOps Dashboard CLI",
        box=box.ASCII_DOUBLE_HEAD,
        show_lines=True,
        style="bright_cyan",
    )


def add_profile_to_table(table: Table, profile_data: ProfileData) -> None:
    """Add profile data to the display table."""
    if profile_data["success"]:
        table.add_row(
            f"[bright_magenta]{profile_data['profile']}\nAccount: {profile_data['account_id']}[/]",
            f"[bright_red]${profile_data['last_month']:.2f}[/]",
            f"[bright_green]${profile_data['current_month']:.2f}[/]",
            "[bright_green]"
            + "\n".join(profile_data["service_costs_formatted"])
            + "[/]",
            "[bright_yellow]" + "\n".join(profile_data["budget_info"]) + "[/]",
            "\n".join(profile_data["ec2_summary_formatted"]),
        )
    else:
        table.add_row(
            f"[bright_magenta]{profile_data['profile']}[/]",
            "[red]Error[/]",
            "[red]Error[/]",
            f"[red]Failed to process profile: {profile_data['error']}[/]",
            "[red]N/A[/]",
            "[red]N/A[/]",
        )


def run_dashboard(args: argparse.Namespace) -> int:
    """Main function to run the AWS FinOps dashboard."""
    export_data = []

    available_profiles = get_aws_profiles()

    if not available_profiles:
        console.print(
            "[bold red]No AWS profiles found. Please configure AWS CLI first.[/]"
        )
        return 1

    profiles_to_use = []
    if args.profiles:
        for profile in args.profiles:
            if profile in available_profiles:
                profiles_to_use.append(profile)
            else:
                console.print(
                    f"[yellow]Warning: Profile '{profile}' not found in AWS configuration[/]"
                )

        if not profiles_to_use:
            console.print(
                "[bold red]None of the specified profiles were found in AWS configuration.[/]"
            )
            return 1
    elif args.all:
        profiles_to_use = available_profiles
    else:
        if "default" in available_profiles:
            profiles_to_use = ["default"]
        else:
            profiles_to_use = available_profiles
            console.print(
                "[yellow]No default profile found. Using all available profiles.[/]"
            )

    user_regions = args.regions
    time_range = args.time_range

    if time_range:
        console.print(
            f"[cyan]Using time range of {time_range} days for cost analysis[/]"
        )

    if profiles_to_use:
        try:
            sample_session = boto3.Session(profile_name=profiles_to_use[0])
            sample_cost_data = get_cost_data(sample_session, time_range)
            previous_period_name = sample_cost_data.get(
                "previous_period_name", "Last Month Due"
            )
            current_period_name = sample_cost_data.get(
                "current_period_name", "Current Month Cost"
            )
        except Exception:
            previous_period_name = "Last Month Due"
            current_period_name = "Current Month Cost"
    else:
        previous_period_name = "Last Month Due"
        current_period_name = "Current Month Cost"

    table = create_display_table(previous_period_name, current_period_name)

    if args.combine:
        console.log("[cyan]Checking account IDs for profiles...[/]")
        account_profiles = defaultdict(list)
        profile_account_map = {}

        for profile in profiles_to_use:
            try:
                session = boto3.Session(profile_name=profile)
                account_id = get_account_id(session)
                if account_id:
                    account_profiles[account_id].append(profile)
                    profile_account_map[profile] = account_id
                    console.log(
                        f"[cyan]Profile {profile} belongs to account {account_id}[/]"
                    )
                else:
                    console.log(
                        f"[yellow]Could not determine account ID for profile {profile}[/]"
                    )
            except Exception as e:
                console.log(
                    f"[bold red]Error checking account ID for profile {profile}: {str(e)}[/]"
                )

        for account_id, profiles in account_profiles.items():
            if len(profiles) > 1:
                profile_data = process_combined_profiles(
                    account_id, profiles, user_regions, time_range
                )
                export_data.append(profile_data)
            else:
                profile_data = process_single_profile(
                    profiles[0], user_regions, time_range
                )
                export_data.append(profile_data)
    else:
        for profile in profiles_to_use:
            profile_data = process_single_profile(profile, user_regions, time_range)
            export_data.append(profile_data)

    for profile_data in export_data:
        add_profile_to_table(table, profile_data)

    with Live(table, console=console, refresh_per_second=1):
        pass

    if args.report_name and args.report_type:
        for report_type in args.report_type:
            if report_type == "csv":
                csv_path = export_to_csv(export_data, args.report_name, args.dir)
                if csv_path:
                    console.print(
                        f"[bright_green]Successfully exported to CSV format: {csv_path}[/]"
                    )
            elif report_type == "json":
                json_path = export_to_json(export_data, args.report_name, args.dir)
                if json_path:
                    console.print(
                        f"[bright_green]Successfully exported to JSON format: {json_path}[/]"
                    )

    return 0


def main() -> int:
    """Entry point for the module when run directly."""
    from aws_finops_dashboard.cli import parse_args

    args = parse_args()
    return run_dashboard(args)


if __name__ == "__main__":
    sys.exit(main())
