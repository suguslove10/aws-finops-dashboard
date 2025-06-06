import argparse
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
import os
import json

import boto3
from rich import box
from rich.console import Console
from rich.progress import track
from rich.status import Status
from rich.table import Column, Table

from aws_finops_dashboard.aws_client import (
    get_accessible_regions,
    get_account_id,
    get_aws_profiles,
    get_budgets,
    get_stopped_instances,
    get_untagged_resources,
    get_unused_eips,
    get_unused_volumes,
)
from aws_finops_dashboard.cost_processor import (
    export_to_csv,
    export_to_json,
    get_cost_data,
    get_trend,
)
from aws_finops_dashboard.helpers import (
    clean_rich_tags,
    export_audit_report_to_pdf,
    export_cost_dashboard_to_pdf,
    export_audit_report_to_csv,
    export_audit_report_to_json,
    export_trend_data_to_json,
    convert_currency,
    format_currency,
)
from aws_finops_dashboard.profile_processor import (
    process_combined_profiles,
    process_single_profile,
)
from aws_finops_dashboard.types import ProfileData
from aws_finops_dashboard.visualisations import create_trend_bars
from aws_finops_dashboard.anomaly_detection import detect_anomalies
from aws_finops_dashboard.optimization_recommendations import generate_optimization_recommendations

console = Console()


def _initialize_profiles(
    args: argparse.Namespace,
) -> Tuple[List[str], Optional[List[str]], Optional[int], str]:
    """Initialize AWS profiles based on arguments."""
    available_profiles = get_aws_profiles()
    if not available_profiles:
        console.log(
            "[bold red]No AWS profiles found. Please configure AWS CLI first.[/]"
        )
        raise SystemExit(1)

    profiles_to_use = []
    if args.profiles:
        for profile in args.profiles:
            if profile in available_profiles:
                profiles_to_use.append(profile)
            else:
                console.log(
                    f"[yellow]Warning: Profile '{profile}' not found in AWS configuration[/]"
                )
        if not profiles_to_use:
            console.log(
                "[bold red]None of the specified profiles were found in AWS configuration.[/]"
            )
            raise SystemExit(1)
    elif args.all:
        profiles_to_use = available_profiles
    else:
        if "default" in available_profiles:
            profiles_to_use = ["default"]
        else:
            profiles_to_use = available_profiles
            console.log(
                "[yellow]No default profile found. Using all available profiles.[/]"
            )

    return profiles_to_use, args.regions, args.time_range, args.currency


def _run_audit_report(profiles_to_use: List[str], args: argparse.Namespace) -> None:
    """Generate and export an audit report."""
    console.print("[bold bright_cyan]Preparing your audit report...[/]")
    table = Table(
        Column("Profile", justify="center"),
        Column("Account ID", justify="center"),
        Column("Untagged Resources"),
        Column("Stopped EC2 Instances"),
        Column("Unused Volumes"),
        Column("Unused EIPs"),
        Column("Budget Alerts"),
        title="AWS FinOps Audit Report",
        show_lines=True,
        box=box.ASCII_DOUBLE_HEAD,
        style="bright_cyan",
    )

    audit_data = []
    raw_audit_data = []
    nl = "\n"
    comma_nl = ",\n"

    for profile in profiles_to_use:
        session = boto3.Session(profile_name=profile)
        account_id = get_account_id(session) or "Unknown"
        regions = args.regions or get_accessible_regions(session)

        try:
            untagged = get_untagged_resources(session, regions)
            anomalies = []
            for service, region_map in untagged.items():
                if region_map:
                    service_block = f"[bright_yellow]{service}[/]:\n"
                    for region, ids in region_map.items():
                        if ids:
                            ids_block = "\n".join(
                                f"[orange1]{res_id}[/]" for res_id in ids
                            )
                            service_block += f"\n{region}:\n{ids_block}\n"
                    anomalies.append(service_block)
            if not any(region_map for region_map in untagged.values()):
                anomalies = ["None"]
        except Exception as e:
            anomalies = [f"Error: {str(e)}"]

        stopped = get_stopped_instances(session, regions)
        stopped_list = [
            f"{r}:\n[gold1]{nl.join(ids)}[/]" for r, ids in stopped.items()
        ] or ["None"]

        unused_vols = get_unused_volumes(session, regions)
        vols_list = [
            f"{r}:\n[dark_orange]{nl.join(ids)}[/]" for r, ids in unused_vols.items()
        ] or ["None"]

        unused_eips = get_unused_eips(session, regions)
        eips_list = [
            f"{r}:\n{comma_nl.join(ids)}" for r, ids in unused_eips.items()
        ] or ["None"]

        budget_data = get_budgets(session)
        alerts = []
        for b in budget_data:
            if b["actual"] > b["limit"]:
                alerts.append(
                    f"[red1]{b['name']}[/]: ${b['actual']:.2f} > ${b['limit']:.2f}"
                )
        if not alerts:
            alerts = ["No budgets exceeded"]

        audit_data.append(
            {
                "profile": profile,
                "account_id": account_id,
                "untagged_resources": clean_rich_tags("\n".join(anomalies)),
                "stopped_instances": clean_rich_tags("\n".join(stopped_list)),
                "unused_volumes": clean_rich_tags("\n".join(vols_list)),
                "unused_eips": clean_rich_tags("\n".join(eips_list)),
                "budget_alerts": clean_rich_tags("\n".join(alerts)),
            }
        )

        # Data for JSON which includes raw audit data
        raw_audit_data.append(
            {
                "profile": profile,
                "account_id": account_id,
                "untagged_resources": untagged,
                "stopped_instances": stopped,
                "unused_volumes": unused_vols,
                "unused_eips": unused_eips,
                "budget_alerts": budget_data,
            }
        )

        table.add_row(
            f"[dark_magenta]{profile}[/]",
            account_id,
            "\n".join(anomalies),
            "\n".join(stopped_list),
            "\n".join(vols_list),
            "\n".join(eips_list),
            "\n".join(alerts),
        )
    console.print(table)
    console.print(
        "[bold bright_cyan]Note: The dashboard only lists untagged EC2, RDS, Lambda, ELBv2.\n[/]"
    )

    if args.report_name:  # Ensure report_name is provided for any export
        if args.report_type:
            for report_type in args.report_type:
                if report_type == "csv":
                    csv_path = export_audit_report_to_csv(
                        audit_data, args.report_name, args.dir
                    )
                    if csv_path:
                        console.print(
                            f"[bright_green]Successfully exported to CSV format: {csv_path}[/]"
                        )
                elif report_type == "json":
                    json_path = export_audit_report_to_json(
                        raw_audit_data, args.report_name, args.dir
                    )
                    if json_path:
                        console.print(
                            f"[bright_green]Successfully exported to JSON format: {json_path}[/]"
                        )
                elif report_type == "pdf":
                    pdf_path = export_audit_report_to_pdf(
                        audit_data, args.report_name, args.dir
                    )
                    if pdf_path:
                        console.print(
                            f"[bright_green]Successfully exported to PDF format: {pdf_path}[/]"
                        )
                

def _run_trend_analysis(profiles_to_use: List[str], args: argparse.Namespace) -> None:
    """Run cost trend analysis for the past 6 months."""
    console.print(
        "[bright_blue]===== AWS Cost Trend Analysis =====[/]\n"
        "[bright_blue]Running cost trend analysis for the past 6 months...[/]\n"
    )

    try:
        for profile in profiles_to_use:
            console.print(f"[bright_cyan]Processing profile: {profile}[/]")
            session = boto3.Session(profile_name=profile)
            if not session:
                console.print(f"[bold red]Error creating session for profile {profile}[/]")
                continue

            # Get cost data with fetch_trend=True to get the past 6 months
            cost_data = get_cost_data(session, tag=args.tag, fetch_trend=True)
            
            # Check if monthly_trend_data key exists and has data
            if "monthly_trend_data" in cost_data and cost_data["monthly_trend_data"]:
                create_trend_bars(cost_data["monthly_trend_data"], args.currency)
            else:
                console.print("[yellow]No trend data available for this profile[/]")
                
            # Export trend data if a report name is specified
            if args.report_name and "json" in args.report_type:
                trend_data = {
                    "profile": profile,
                    "monthly_costs": cost_data.get("monthly_trend_data", []),
                }
                export_trend_data_to_json(
                    trend_data, args.report_name, args.dir, args.currency
                )

    except Exception as e:
        console.print(f"[bold red]Error in trend analysis: {str(e)}[/]")
        import traceback
        console.print(traceback.format_exc())


def _get_display_table_period_info(
    profiles_to_use: List[str], time_range: Optional[int]
) -> Tuple[str, str, str, str]:
    """Get period information for the display table."""
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
            previous_period_dates = f"{sample_cost_data['previous_period_start']} to {sample_cost_data['previous_period_end']}"
            current_period_dates = f"{sample_cost_data['current_period_start']} to {sample_cost_data['current_period_end']}"
            return (
                previous_period_name,
                current_period_name,
                previous_period_dates,
                current_period_dates,
            )
        except Exception:
            pass  # Fall through to default values
    return "Last Month Due", "Current Month Cost", "N/A", "N/A"


def create_display_table(
    previous_period_dates: str,
    current_period_dates: str,
    previous_period_name: str = "Last Month Due",
    current_period_name: str = "Current Month Cost",
) -> Table:
    """Create and configure the display table with dynamic column names."""
    return Table(
        Column("AWS Account Profile", justify="center", vertical="middle"),
        Column(
            f"{previous_period_name}\n({previous_period_dates})",
            justify="center",
            vertical="middle",
        ),
        Column(
            f"{current_period_name}\n({current_period_dates})",
            justify="center",
            vertical="middle",
        ),
        Column("Cost By Service", vertical="middle"),
        Column("Budget Status", vertical="middle"),
        Column("EC2 Instance Summary", justify="center", vertical="middle"),
        title="AWS FinOps Dashboard",
        caption="AWS FinOps Dashboard CLI",
        box=box.ASCII_DOUBLE_HEAD,
        show_lines=True,
        style="bright_cyan",
    )


def add_profile_to_table(table: Table, profile_data: ProfileData, currency: str = "USD") -> None:
    """Add profile data to the display table."""
    if profile_data["success"]:
        percentage_change = profile_data.get("percent_change_in_total_cost")
        change_text = ""

        if percentage_change is not None:
            if percentage_change > 0:
                change_text = f"\n\n[bright_red]⬆ {percentage_change:.2f}%"
            elif percentage_change < 0:
                change_text = f"\n\n[bright_green]⬇ {abs(percentage_change):.2f}%"
            elif percentage_change == 0:
                change_text = "\n\n[bright_yellow]➡ 0.00%[/]"

        # Convert currency values
        current_month_value = convert_currency(profile_data['current_month'], "USD", currency)
        last_month_value = convert_currency(profile_data['last_month'], "USD", currency)
        
        # Format with currency symbol
        current_month_formatted = format_currency(current_month_value, currency)
        last_month_formatted = format_currency(last_month_value, currency)

        current_month_with_change = (
            f"[bold red]{current_month_formatted}[/]{change_text}"
        )

        # Convert and format service costs
        service_costs_formatted = []
        for service_cost in profile_data["service_costs_formatted"]:
            # Extract service name and cost value
            if ": $" in service_cost:
                service_name, cost_str = service_cost.split(": $")
                cost_value = float(cost_str)
                converted_cost = convert_currency(cost_value, "USD", currency)
                formatted_cost = format_currency(converted_cost, currency)
                service_costs_formatted.append(f"{service_name}: {formatted_cost}")
            else:
                service_costs_formatted.append(service_cost)
        
        # Convert and format budget info
        budget_info_formatted = []
        for budget_item in profile_data["budget_info"]:
            if " limit: $" in budget_item:
                budget_name, limit_str = budget_item.split(" limit: $")
                limit_value = float(limit_str)
                converted_limit = convert_currency(limit_value, "USD", currency)
                formatted_limit = format_currency(converted_limit, currency)
                budget_info_formatted.append(f"{budget_name} limit: {formatted_limit}")
            elif " actual: $" in budget_item:
                budget_name, actual_str = budget_item.split(" actual: $")
                actual_value = float(actual_str)
                converted_actual = convert_currency(actual_value, "USD", currency)
                formatted_actual = format_currency(converted_actual, currency)
                budget_info_formatted.append(f"{budget_name} actual: {formatted_actual}")
            elif " forecast: $" in budget_item:
                budget_name, forecast_str = budget_item.split(" forecast: $")
                forecast_value = float(forecast_str)
                converted_forecast = convert_currency(forecast_value, "USD", currency)
                formatted_forecast = format_currency(converted_forecast, currency)
                budget_info_formatted.append(f"{budget_name} forecast: {formatted_forecast}")
            else:
                budget_info_formatted.append(budget_item)

        table.add_row(
            f"[bright_magenta]Profile: {profile_data['profile']}\nAccount: {profile_data['account_id']}[/]",
            f"[bold red]{last_month_formatted}[/]",
            current_month_with_change,
            "[bright_green]"
            + "\n".join(service_costs_formatted)
            + "[/]",
            "[bright_yellow]" + "\n\n".join(budget_info_formatted) + "[/]",
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


def _generate_dashboard_data(
    profiles_to_use: List[str],
    user_regions: Optional[List[str]],
    time_range: Optional[int],
    args: argparse.Namespace,
    table: Table,
) -> List[ProfileData]:
    """Fetch, process, and prepare the main dashboard data."""
    export_data: List[ProfileData] = []
    if args.combine:
        account_profiles = defaultdict(list)
        for profile in profiles_to_use:
            try:
                session = boto3.Session(profile_name=profile)
                current_account_id = get_account_id(
                    session
                )  # Renamed to avoid conflict
                if current_account_id:
                    account_profiles[current_account_id].append(profile)
                else:
                    console.log(
                        f"[yellow]Could not determine account ID for profile {profile}[/]"
                    )
            except Exception as e:
                console.log(
                    f"[bold red]Error checking account ID for profile {profile}: {str(e)}[/]"
                )

        console.print("[bright_cyan]Fetching cost data...[/]")
        for account_id_key, profiles_list in account_profiles.items():
            # account_id_key here is known to be a string because it's a key from account_profiles
            # where None keys were filtered out when populating it.
            if len(profiles_list) > 1:
                profile_data = process_combined_profiles(
                    account_id_key, profiles_list, user_regions, time_range, args.tag
                )
            else:
                profile_data = process_single_profile(
                    profiles_list[0], user_regions, time_range, args.tag
                )
            export_data.append(profile_data)
            add_profile_to_table(table, profile_data, args.currency)
    else:
        console.print("[bright_cyan]Fetching cost data...[/]")
        for profile in profiles_to_use:
            profile_data = process_single_profile(
                profile, user_regions, time_range, args.tag
            )
            export_data.append(profile_data)
            add_profile_to_table(table, profile_data, args.currency)
    return export_data


def _export_dashboard_reports(
    export_data: List[ProfileData],
    args: argparse.Namespace,
    previous_period_dates: str,
    current_period_dates: str,
) -> None:
    """Export dashboard data to report files."""
    if not args.report_name or not args.report_type:
        return

    from aws_finops_dashboard.helpers import (
        export_cost_dashboard_to_csv,
        export_cost_dashboard_to_json,
        export_cost_dashboard_to_pdf,
    )

    if "csv" in args.report_type:
        csv_path = export_cost_dashboard_to_csv(
            export_data, args.report_name, args.dir
        )
        if csv_path:
            console.print(
                f"[bright_green]Report exported to CSV: {csv_path}[/]"
            )

    if "json" in args.report_type:
        json_path = export_cost_dashboard_to_json(
            export_data, args.report_name, args.dir
        )
        if json_path:
            console.print(
                f"[bright_green]Report exported to JSON: {json_path}[/]"
            )

    if "pdf" in args.report_type:
        pdf_path = export_cost_dashboard_to_pdf(
            export_data,
            args.report_name,
            args.dir,
            previous_period_dates,
            current_period_dates,
            args.currency,
            args.enhanced_pdf,
        )
        if pdf_path:
            console.print(
                f"[bright_green]Report exported to PDF: {pdf_path}[/]"
            )


def _run_anomaly_detection(profiles_to_use: List[str], args: argparse.Namespace) -> None:
    """Run anomaly detection on AWS cost data."""
    console.print("[bold bright_cyan]Running ML-based anomaly detection on AWS cost data...[/]")
    
    from rich import box
    from rich.table import Table
    
    console.print("[bright_cyan]Analyzing profiles for anomalies...[/]")
    for profile in profiles_to_use:
        console.print(f"[bold bright_magenta]Analyzing profile: {profile}[/]")
        
        session = boto3.Session(profile_name=profile)
        account_id = get_account_id(session) or "Unknown"
        
        # Run anomaly detection
        result = detect_anomalies(
            session=session,
            days=args.time_range or 90,
            tag=args.tag,
            sensitivity=args.anomaly_sensitivity
        )
        
        if not result["anomalies"]:
            console.print(f"[green]No significant anomalies detected for profile {profile}.[/]")
            continue
        
        # Create table to display the results
        anomaly_table = Table(
            title=f"Cost Anomalies for {profile} (Account: {account_id})",
            box=box.ASCII_DOUBLE_HEAD,
            style="bright_cyan",
            show_lines=True
        )
        
        anomaly_table.add_column("Service", style="bold magenta")
        anomaly_table.add_column("Date", style="cyan")
        anomaly_table.add_column("Amount ($)", justify="right", style="green")
        anomaly_table.add_column("Baseline ($)", justify="right", style="blue")
        anomaly_table.add_column("Deviation", justify="right", style="yellow")
        
        for service, anomalies in result["anomalies"].items():
            for anomaly in anomalies:
                anomaly_table.add_row(
                    service,
                    anomaly["date"],
                    f"{anomaly['amount']:.2f}",
                    f"{anomaly['baseline']:.2f}",
                    f"{anomaly['deviation']:.1f}x"
                )
        
        console.print(anomaly_table)
        
        # Print summary
        summary = result["summary"]
        console.print(f"[bold cyan]Summary for {profile}:[/]")
        console.print(f"• Total anomalies detected: [bold]{summary['total_anomalies']}[/]")
        console.print(f"• Services with anomalies: [bold]{summary['services_with_anomalies']}/{summary['total_services_analyzed']}[/]")
        console.print(f"• Highest cost deviation: [bold]{summary['highest_deviation']:.1f}x[/]")
        
        if args.report_name and "json" in args.report_type:
            # Export anomaly data to JSON
            output_dir = args.dir or "."
            filename = f"{args.report_name}_{profile}_anomalies.json"
            filepath = os.path.join(output_dir, filename)
            
            try:
                os.makedirs(output_dir, exist_ok=True)
                with open(filepath, "w") as f:
                    json.dump(result, f, indent=2)
                console.print(f"[green]Anomaly data exported to {filepath}[/]")
            except Exception as e:
                console.print(f"[red]Error exporting anomaly data: {str(e)}[/]")


def _run_optimization_recommendations(profiles_to_use: List[str], args: argparse.Namespace) -> None:
    """Generate cost optimization recommendations."""
    console.print("[bold bright_cyan]Generating AI-powered cost optimization recommendations...[/]")
    
    from rich import box
    from rich.table import Table
    
    console.print("[bright_cyan]Analyzing profiles for optimization opportunities...[/]")
    for profile in profiles_to_use:
        console.print(f"[bold bright_magenta]Analyzing profile: {profile}[/]")
        
        session = boto3.Session(profile_name=profile)
        account_id = get_account_id(session) or "Unknown"
        
        # Generate optimization recommendations
        result = generate_optimization_recommendations(
            session=session,
            analyze_ec2=True,
            analyze_resources=True,
            analyze_reservations=not args.skip_ri_analysis,
            analyze_savings_plans=not args.skip_savings_plans,
            regions=args.regions,
            cpu_threshold=args.cpu_threshold
        )
        
        # Check if we have any recommendations
        has_recommendations = (
            result["ec2_recommendations"] or
            result["resource_recommendations"] or
            result["ri_recommendations"] or
            result["savings_plans_recommendations"]
        )
        
        if not has_recommendations:
            console.print(f"[green]No optimization opportunities found for profile {profile}.[/]")
            continue
        
        # Display EC2 right-sizing recommendations
        if result["ec2_recommendations"]:
            ec2_table = Table(
                title=f"EC2 Right-Sizing Recommendations for {profile} (Account: {account_id})",
                box=box.ASCII_DOUBLE_HEAD,
                style="bright_cyan",
                show_lines=True
            )
            
            ec2_table.add_column("Instance ID")
            ec2_table.add_column("Name")
            ec2_table.add_column("Region")
            ec2_table.add_column("Current Type")
            ec2_table.add_column("Recommended")
            ec2_table.add_column("Avg CPU", justify="right")
            ec2_table.add_column("Monthly Savings", justify="right")
            
            for rec in result["ec2_recommendations"]:
                ec2_table.add_row(
                    rec["resource_id"],
                    rec["resource_name"] or "-",
                    rec["region"],
                    rec["current_type"],
                    f"[bold green]{rec['recommended_type']}[/]",
                    f"{rec['metrics']['avg_cpu']:.1f}%",
                    f"[bold]${rec['savings']:.2f}[/]"
                )
            
            console.print(ec2_table)
        
        # Display unused resource recommendations
        if result["resource_recommendations"]:
            resource_table = Table(
                title=f"Unused Resource Recommendations for {profile} (Account: {account_id})",
                box=box.ASCII_DOUBLE_HEAD,
                style="bright_cyan",
                show_lines=True
            )
            
            resource_table.add_column("Resource Type")
            resource_table.add_column("Resource ID")
            resource_table.add_column("Region")
            resource_table.add_column("Recommendation")
            resource_table.add_column("Monthly Savings", justify="right")
            
            for rec in result["resource_recommendations"]:
                resource_table.add_row(
                    rec["resource_type"],
                    rec["resource_id"],
                    rec["region"],
                    rec["recommendation"],
                    f"[bold]${rec['savings']:.2f}[/]"
                )
            
            console.print(resource_table)
        
        # Display Reserved Instance recommendations
        if result["ri_recommendations"]:
            ri_table = Table(
                title=f"Reserved Instance Recommendations for {profile} (Account: {account_id})",
                box=box.ASCII_DOUBLE_HEAD,
                style="bright_cyan",
                show_lines=True
            )
            
            ri_table.add_column("Instance Type")
            ri_table.add_column("Count")
            ri_table.add_column("Term")
            ri_table.add_column("Payment Option")
            ri_table.add_column("Monthly Savings", justify="right")
            
            for rec in result["ri_recommendations"]:
                ri_table.add_row(
                    rec["instance_type"],
                    str(rec["recommended_count"]),
                    rec["term"],
                    rec["payment_option"],
                    f"[bold]${rec['monthly_savings']:.2f}[/]"
                )
            
            console.print(ri_table)
        
        # Display Savings Plans recommendations
        if result["savings_plans_recommendations"]:
            sp_table = Table(
                title=f"Savings Plans Recommendations for {profile} (Account: {account_id})",
                box=box.ASCII_DOUBLE_HEAD,
                style="bright_cyan",
                show_lines=True
            )
            
            sp_table.add_column("Plan Type")
            sp_table.add_column("Hourly Commitment")
            sp_table.add_column("Term")
            sp_table.add_column("Payment Option")
            sp_table.add_column("Monthly Savings", justify="right")
            
            for rec in result["savings_plans_recommendations"]:
                sp_table.add_row(
                    rec["plan_type"],
                    f"${rec['hourly_commitment']:.2f}/hr",
                    rec["term"],
                    rec["payment_option"],
                    f"[bold]${rec['monthly_savings']:.2f}[/]"
                )
            
            console.print(sp_table)
        
        # Print summary
        summary = result["summary"]
        console.print(f"[bold cyan]Summary for {profile}:[/]")
        console.print(f"• Total potential monthly savings: [bold]${summary['total_potential_savings']:.2f}[/]")
        if summary["ec2_savings"] > 0:
            console.print(f"• EC2 right-sizing savings: [bold]${summary['ec2_savings']:.2f}[/]")
        if summary["resource_savings"] > 0:
            console.print(f"• Unused resource savings: [bold]${summary['resource_savings']:.2f}[/]")
        if summary["ri_savings"] > 0:
            console.print(f"• Reserved Instance savings: [bold]${summary['ri_savings']:.2f}[/]")
        if summary["savings_plans_savings"] > 0:
            console.print(f"• Savings Plans savings: [bold]${summary['savings_plans_savings']:.2f}[/]")
        
        if args.report_name and "json" in args.report_type:
            # Export optimization data to JSON
            output_dir = args.dir or "."
            filename = f"{args.report_name}_{profile}_optimization.json"
            filepath = os.path.join(output_dir, filename)
            
            try:
                os.makedirs(output_dir, exist_ok=True)
                with open(filepath, "w") as f:
                    json.dump(result, f, indent=2)
                console.print(f"[green]Optimization data exported to {filepath}[/]")
            except Exception as e:
                console.print(f"[red]Error exporting optimization data: {str(e)}[/]")


def _run_resource_analyzer(profiles_to_use: List[str], args: argparse.Namespace) -> None:
    """Run the unused resource analyzer feature."""
    from aws_finops_dashboard.resource_analyzer import UnusedResourceAnalyzer
    from aws_finops_dashboard.resource_analyzer_export import export_unused_resources
    
    console.print("[bold cyan]===== AWS Unused Resource Analyzer =====[/]\n")
    console.print("[bright_blue]Analyzing resources to find unused or underutilized items...[/]\n")

    for profile in profiles_to_use:
        try:
            console.print(f"[cyan]Analyzing profile: [bold]{profile}[/bold][/]")
            
            # Create AWS session
            session = boto3.Session(profile_name=profile)
            
            # Create and run the analyzer
            analyzer = UnusedResourceAnalyzer(session, args.lookback_days or 14)
            
            # Display results on console using the specified currency
            analyzer.display_unused_resources(args.regions, args.currency)
            
            # Export results if report type and name are specified
            if args.report_type and args.report_name:
                report_data = analyzer.get_all_unused_resources(args.regions)
                
                for report_type in args.report_type:
                    output_file = export_unused_resources(
                        report_data,
                        output_format=report_type,
                        output_dir=args.dir,
                        report_name=f"{args.report_name}_unused_resources_{profile}",
                        currency=args.currency  # Pass the currency parameter
                    )
                    console.print(f"[green]Report exported to: [bold]{output_file}[/bold][/]")
                
        except Exception as e:
            console.print(f"[bold red]Error analyzing profile {profile}: {str(e)}[/]")
            import traceback
            console.print(traceback.format_exc())
            
    console.print("\n[bold green]Resource analysis complete![/]")


def run_dashboard(args: argparse.Namespace) -> int:
    """Main function to run the AWS FinOps dashboard."""
    try:
        # Apply force_color if specified
        global console
        if hasattr(args, 'force_color') and args.force_color:
            console = Console(force_terminal=True, color_system="truecolor")
            
        with Status("[bright_cyan]Initialising...", spinner="aesthetic", speed=0.4):
            profiles_to_use, user_regions, time_range, currency = _initialize_profiles(args)

        if args.audit:
            _run_audit_report(profiles_to_use, args)
            return 0

        if args.trend:
            _run_trend_analysis(profiles_to_use, args)
            return 0
                
        if args.detect_anomalies:
            _run_anomaly_detection(profiles_to_use, args)
            return 0
            
        if args.optimize:
            _run_optimization_recommendations(profiles_to_use, args)
            return 0

        if args.ri_optimizer:
            _run_ri_optimizer(profiles_to_use, args)
            return 0

        if args.resource_analyzer:
            _run_resource_analyzer(profiles_to_use, args)
            return 0

        with Status(
            "[bright_cyan]Initialising dashboard...", spinner="aesthetic", speed=0.4
        ):
            (
                previous_period_name,
                current_period_name,
                previous_period_dates,
                current_period_dates,
            ) = _get_display_table_period_info(profiles_to_use, time_range)

            table = create_display_table(
                previous_period_dates,
                current_period_dates,
                previous_period_name,
                current_period_name,
            )

        export_data = _generate_dashboard_data(
            profiles_to_use, user_regions, time_range, args, table
        )
                    
        console.print(table)
                
        _export_dashboard_reports(
            export_data, args, previous_period_dates, current_period_dates
        )

        return 0
    except KeyboardInterrupt:
        console.print("[bold red]Operation cancelled by user.[/]")
        return 1
    except Exception as e:
        console.print(f"[bold red]Error running dashboard: {str(e)}[/]")
        import traceback
        console.print(traceback.format_exc())
        return 1 