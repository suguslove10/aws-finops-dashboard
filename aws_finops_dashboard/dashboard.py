import boto3
import argparse
import sys
import os, csv
from datetime import date, timedelta, datetime
from rich.console import Console
from rich.table import Table, Column
from rich.panel import Panel
from rich import box
from rich.live import Live
from collections import defaultdict

console = Console()

def get_aws_profiles():
    """Get all configured AWS profiles from the AWS CLI configuration."""
    try:
        session = boto3.Session()
        return session.available_profiles
    except Exception as e:
        console.print(f"[bold red]Error getting AWS profiles: {str(e)}[/]")
        return []

def get_account_id(session):
    """Get the AWS account ID for a session."""
    try:
        return session.client('sts').get_caller_identity().get('Account')
    except Exception as e:
        console.log(f"[yellow]Warning: Could not get account ID: {str(e)}[/]")
        return None

def get_cost_data(session):
    ce = session.client('ce')
    budgets = session.client('budgets', region_name='us-east-1')
    today = date.today()
    start_of_month = today.replace(day=1).isoformat()
    last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1).isoformat()
    last_month_end = today.replace(day=1) - timedelta(days=1)
    
    account_id = get_account_id(session)

    # current month cost
    try:
        this_month = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start_of_month,
            'End': today.isoformat()
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        )
    except Exception as e:
        this_month = {'ResultsByTime': [{'Total': {'UnblendedCost': {'Amount': 0}}}]}

    # last month cost 
    try:
        last_month = ce.get_cost_and_usage(
            TimePeriod={
                'Start': last_month_start,
                'End': last_month_end.isoformat()
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
        )
    except Exception as e:
        last_month = {'ResultsByTime': [{'Total': {'UnblendedCost': {'Amount': 0}}}]}

    try:
        current_month_cost_by_service = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_of_month,
                'End': today.isoformat()
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
    except Exception as e:
        current_month_cost_by_service = {'ResultsByTime': [{'Groups': []}]}

    budgets_data = []
    try:
        response = budgets.describe_budgets(AccountId=account_id)
        for budget in response['Budgets']:
            budgets_data.append({
                'name': budget['BudgetName'],
                'limit': float(budget['BudgetLimit']['Amount']),
                'actual': float(budget['CalculatedSpend']['ActualSpend']['Amount']),
                'forecast': float(budget['CalculatedSpend'].get('ForecastedSpend', {}).get('Amount', 0.0)) or None
            })
    except Exception as e:
        pass

    return{
        "account_id": account_id,
        "current_month": float(this_month['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']),
        "last_month": float(last_month['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']),
        "current_month_cost_by_service": current_month_cost_by_service.get('ResultsByTime', [{}])[0].get('Groups', []),
        "budgets": budgets_data
    }

def get_all_regions(session):
    """Get all available AWS regions."""
    try:
        ec2_client = session.client('ec2', region_name='us-east-1')
        regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
        return regions
    except Exception as e:
        console.log(f"[yellow]Warning: Could not get all regions: {str(e)}[/]")
        # Return default regions if we can't get the full list
        return ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-southeast-1', 'ap-south-1', 
                'eu-west-1', 'eu-west-2', 'eu-central-1']

def get_accessible_regions(session):
    """Get regions that are accessible with the current credentials."""
    all_regions = get_all_regions(session)
    accessible_regions = []
    
    for region in all_regions:
        try:
            # Try to create a client for this region
            ec2_client = session.client('ec2', region_name=region)
            # Make a simple API call to test access
            ec2_client.describe_instances(MaxResults=5)
            accessible_regions.append(region)
        except Exception:
            # If we get an error, this region is not accessible
            console.log(f"[yellow]Region {region} is not accessible with the current credentials[/]")
            
    if not accessible_regions:
        # If no regions are accessible, return a default set
        console.log("[yellow]No accessible regions found. Using default regions.[/]")
        return ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2']
    
    return accessible_regions

def ec2_summary(session, regions=None):
    """Get EC2 instance summary across specified regions or all regions."""
    if regions is None:
        # Include standard regions where instances are likely to exist
        regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-southeast-1', 'ap-south-1',
                  'eu-central-1', 'eu-west-1', 'eu-west-2']
    
    # Track all instance states, not just running and stopped
    instance_summary = defaultdict(int)

    for region in regions:
        try:
            ec2_regional = session.client('ec2', region_name=region)
            instances = ec2_regional.describe_instances()
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    state = instance['State']['Name']
                    instance_summary[state] += 1
        except Exception as e:
            console.log(f"[yellow]Warning: Could not access EC2 in region {region}: {str(e)}[/]")
    
    # Ensure running and stopped are always present in the summary
    if 'running' not in instance_summary:
        instance_summary['running'] = 0
    if 'stopped' not in instance_summary:
        instance_summary['stopped'] = 0
    
    return instance_summary

def export_to_csv(data, filename, output_dir=None):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{filename}_{timestamp}.csv"

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_filename = os.path.join(output_dir, base_filename)
        else:
            output_filename = base_filename 
        
        with open(output_filename, 'w', newline='') as csvfile:
            fieldnames = ['CLI Profile', 'AWS Account ID', 'Last Month Cost', 'Current Month Cost', 'Cost By Service', 'Budget Status', 'EC2 Instances']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:

                services_data = "\n".join([f"{service}: ${cost:.2f}" 
                                        for service, cost in row['service_costs']])
                
                # Format budget info from raw data
                budgets_data = "\n".join(row['budget_info']) if row['budget_info'] else "No budgets"
                
                # Format EC2 info from raw data
                ec2_data_summary = "\n".join([f"{state}: {count}" 
                                    for state, count in row['ec2_summary'].items() 
                                    if count > 0])

                writer.writerow({
                    'CLI Profile': row['profile'],
                    'AWS Account ID': row['account_id'],
                    'Last Month Cost': f"${row['last_month']:.2f}",
                    'Current Month Cost': f"${row['current_month']:.2f}",
                    'Cost By Service': services_data or "No costs",
                    'Budget Status': budgets_data or "No budgets",
                    'EC2 Instances': ec2_data_summary or "No instances"
                })
        console.print(f"[bright_green]Exported dashboard data to {os.path.abspath(output_filename)}[/]")
        return os.path.abspath(output_filename)
    except Exception as e:
        console.print(f"[bold red]Error exporting to CSV: {str(e)}[/]")
        return None


def main():
    parser = argparse.ArgumentParser(description='AWS FinOps Dashboard CLI')
    parser.add_argument('--profiles', '-p', nargs='+', help='Specific AWS profiles to use (space-separated)')
    parser.add_argument('--regions', '-r', nargs='+', help='AWS regions to check for EC2 instances (space-separated)')
    parser.add_argument('--all', '-a', action='store_true', help='Use all available AWS profiles')
    parser.add_argument('--combine', '-c', action='store_true', help='Combine profiles from the same AWS account')

    parser.add_argument('--export-csv', '-e', help='Export the dashboard data to a CSV file(provide a filename without extension)')
    parser.add_argument('--dir', '-d', help='Directory to save the CSV file (default: current directory)')
    args = parser.parse_args()

    export_data = []

    # Get all available profiles
    available_profiles = get_aws_profiles()
    
    if not available_profiles:
        console.print("[bold red]No AWS profiles found. Please configure AWS CLI first.[/]")
        sys.exit(1)
    
    # Determine which profiles to use
    profiles_to_use = []
    if args.profiles:
        # Validate provided profiles
        for profile in args.profiles:
            if profile in available_profiles:
                profiles_to_use.append(profile)
            else:
                console.print(f"[yellow]Warning: Profile '{profile}' not found in AWS configuration[/]")
        
        if not profiles_to_use:
            console.print("[bold red]None of the specified profiles were found in AWS configuration.[/]")
            sys.exit(1)
    elif args.all:
        profiles_to_use = available_profiles
    else:
        # Default: use the default profile if it exists, otherwise use all profiles
        if 'default' in available_profiles:
            profiles_to_use = ['default']
        else:
            profiles_to_use = available_profiles
            console.print("[yellow]No default profile found. Using all available profiles.[/]")
    
    # Store user-specified regions if provided
    user_regions = args.regions
    
    # Create the table
    table = Table("AWS Account Profile", 
                Column("Last Month Due", justify="right"), 
                Column("Current Month Cost", justify="right"), 
                Column("Cost By Service"), 
                Column("Budget Status"),
                Column("EC2 Instance Summary", justify="center"),
                title="AWS FinOps Dashboard", 
                caption="AWS FinOps Dashboard CLI", 
                box=box.ASCII_DOUBLE_HEAD, 
                show_lines=True, 
                style="bright_cyan")

    # Group profiles by account ID if combine flag is set
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
                    console.log(f"[cyan]Profile {profile} belongs to account {account_id}[/]")
                else:
                    console.log(f"[yellow]Could not determine account ID for profile {profile}[/]")
            except Exception as e:
                console.log(f"[bold red]Error checking account ID for profile {profile}: {str(e)}[/]")
        
        # Process profiles by account
        with Live(table, console=console, refresh_per_second=1):
            for account_id, profiles in account_profiles.items():
                if len(profiles) > 1:
                    console.log(f"[cyan]Processing combined profiles for account {account_id}: {', '.join(profiles)}...[/]")
                    
                    # Use only the first profile for EC2 instance discovery to avoid duplicate API calls
                    primary_profile = profiles[0]
                    console.log(f"[cyan]Using {primary_profile} as primary profile for EC2 discovery & cost data[/]")

                    # Get EC2 data and cost data from the primary profile
                    primary_session = boto3.Session(profile_name=primary_profile)
                    
                    # cost data for this account
                    # since all profiles belong to the same account, we can use the first profile to get cost data
                    combined_current_month = 0
                    combined_last_month = 0
                    combined_service_costs = defaultdict(float)
                    combined_budgets = []
                    
                    try:
                        account_cost_data = get_cost_data(primary_session)
                        combined_current_month = account_cost_data['current_month']
                        combined_last_month = account_cost_data['last_month']
                        combined_service_costs = defaultdict(float)
                        for group in account_cost_data['current_month_cost_by_service']:
                            if 'Keys' in group and 'Metrics' in group:
                                service_name = group['Keys'][0]
                                cost_amount = float(group['Metrics']['UnblendedCost']['Amount'])
                                if cost_amount > 0.001:  # Only add services with non-zero costs
                                    combined_service_costs[service_name] += cost_amount
                    except Exception as e:
                        console.log(f"[bold red]Error getting cost data for account {account_id}: {str(e)}[/]")

                    # Add budgets
                    combined_budgets = account_cost_data.get('budgets', [])

                    # Determine accessible regions for the primary profile
                    if user_regions:
                        primary_regions = user_regions
                    else:
                        primary_regions = get_accessible_regions(primary_session)
                        console.log(f"[cyan]Primary profile {primary_profile} - Using regions: {', '.join(primary_regions)}[/]")
                    
                    combined_ec2 = ec2_summary(primary_session, primary_regions)
                                        
                    # Format service costs and sort by cost (highest to lowest)
                    service_costs = []
                    service_cost_data = [(service, cost) for service, cost in combined_service_costs.items() if cost > 0.001]
                    service_cost_data.sort(key=lambda x: x[1], reverse=True)
                    
                    # Format the sorted data
                    if not service_cost_data:
                        service_costs.append("No costs associated with this account")
                    else:
                        for service_name, cost_amount in service_cost_data:
                            service_costs.append(f"{service_name}: ${cost_amount:.2f}")
                        
                    # Format budget info
                    budget_info = []
                    for budget in combined_budgets:
                        budget_info.append(f"{budget['name']} limit: ${budget['limit']}")
                        budget_info.append(f"{budget['name']} actual: ${budget['actual']:.2f}")
                    
                    # Format EC2 instance summary
                    ec2_summary_text = []
                    for state, count in sorted(combined_ec2.items()):
                        if count > 0:  # Only show states with instances
                            state_color = "bright_green" if state == "running" else "bright_yellow" if state == "stopped" else "bright_cyan"
                            ec2_summary_text.append(f"[{state_color}]{state}: {count}[/]")
                    
                    if not ec2_summary_text:
                        ec2_summary_text = ["No instances found"]
                    
                    # Add the combined row
                    profile_list = ", ".join(profiles)
                    table.add_row(
                        f"[bright_magenta]Account: {account_id}\nProfiles: {profile_list}[/]",
                        f"[bright_red]${combined_last_month:.2f}[/]",
                        f"[bright_green]${combined_current_month:.2f}[/]",
                        f"[bright_green]{'\n'.join(service_costs)}[/]",
                        f"[bright_yellow]{'\n'.join(budget_info)}[/]",
                        "\n".join(ec2_summary_text)
                    )

                    # Export the data to CSV
                    export_data.append({
                        'profile': profile_list,
                        'account_id': account_id,
                        'last_month': combined_last_month,
                        'current_month': combined_current_month,
                        'service_costs': service_cost_data,
                        'budget_info': budget_info,
                        'ec2_summary': combined_ec2
                    })

                else:
                    # Process single profile normally
                    profile = profiles[0]
                    console.log(f"[cyan]Processing profile: {profile}...[/]")
                    
                    try:
                        session = boto3.Session(profile_name=profile)
                        cost_data = get_cost_data(session)
                        
                        # Determine accessible regions for this specific profile
                        if user_regions:
                            profile_regions = user_regions
                        else:
                            profile_regions = get_accessible_regions(session)
                            console.log(f"[cyan]Profile {profile} - Using regions: {', '.join(profile_regions)}[/]")
                        
                        ec2_data = ec2_summary(session, profile_regions)

                        ec2_summary_text = []
                        for state, count in sorted(ec2_data.items()):
                            if count > 0:  # Only show states with instances
                                state_color = "bright_green" if state == "running" else "bright_yellow" if state == "stopped" else "bright_cyan"
                                ec2_summary_text.append(f"[{state_color}]{state}: {count}[/]")

                        if not ec2_summary_text:
                            ec2_summary_text = ["No instances found"]
                        
                        # Format service costs and sort by cost (highest to lowest)
                        service_costs = []
                        service_cost_data = []
                        for group in cost_data['current_month_cost_by_service']:
                            if 'Keys' in group and 'Metrics' in group:
                                service_name = group['Keys'][0]
                                cost_amount = float(group['Metrics']['UnblendedCost']['Amount'])
                                if cost_amount > 0.001:  # Filter out zero-cost services
                                    service_cost_data.append((service_name, cost_amount))
                        
                        # Sort by cost (highest to lowest)
                        service_cost_data.sort(key=lambda x: x[1], reverse=True)
                        
                        # Format the sorted data
                        if not service_cost_data:
                            service_costs.append("No costs associated with this account")
                        else:
                            for service_name, cost_amount in service_cost_data:
                                service_costs.append(f"{service_name}: ${cost_amount:.2f}")
                            
                        # Format budget info
                        budget_info = []
                        for budget in cost_data['budgets']:
                            budget_info.append(f"{budget['name']} limit: ${budget['limit']}")
                            budget_info.append(f"{budget['name']} actual: ${budget['actual']:.2f}")
                        
                        table.add_row(
                            f"[bright_magenta]{profile}\nAccount: {account_id}[/]",
                            f"[bright_red]${cost_data['last_month']:.2f}[/]",
                            f"[bright_green]${cost_data['current_month']:.2f}[/]",
                            f"[bright_green]{'\n'.join(service_costs)}[/]",
                            f"[bright_yellow]{'\n'.join(budget_info)}[/]",
                            "\n".join(ec2_summary_text)
                        )
                        console.log(f"[bright_cyan]Processing profile: {profile} completed[/]")

                        # Export the data to CSV
                        export_data.append({
                            'profile': profile,
                            'account_id': account_id,
                            'last_month': cost_data['last_month'],
                            'current_month': cost_data['current_month'],
                            'service_costs': service_cost_data,
                            'budget_info': budget_info,
                            'ec2_summary': ec2_data
                        })

                    except Exception as e:
                        console.log(f"[bold red]Error processing profile {profile}: {str(e)}[/]")
                        table.add_row(
                            f"[bright_magenta]{profile}[/]",
                            "[red]Error[/]",
                            "[red]Error[/]",
                            f"[red]Failed to process profile: {str(e)}[/]",
                            "[red]N/A[/]",
                            "[red]N/A[/]"
                        )
                        export_data.append({
                            'profile': profile,
                            'account_id': 'Error',
                            'last_month': 0,
                            'current_month': 0,
                            'service_costs': [],
                            'budget_info': ['N/A'],
                            'ec2_summary': {'N/A' : 'N/A'}
                        })


    else:
        # Original behavior - process each profile individually
        with Live(table, console=console, refresh_per_second=1):
            for profile in profiles_to_use:
                console.log(f"[cyan]Processing profile: {profile}...[/]")
                
                try:
                    session = boto3.Session(profile_name=profile)
                    cost_data = get_cost_data(session)
                    
                    # Determine accessible regions for this specific profile
                    if user_regions:
                        profile_regions = user_regions
                    else:
                        profile_regions = get_accessible_regions(session)
                        console.log(f"[cyan]Profile {profile} - Using regions: {', '.join(profile_regions)}[/]")
                    
                    ec2_data = ec2_summary(session, profile_regions)
                    
                    # Format service costs and sort by cost (highest to lowest)
                    service_costs = []
                    service_cost_data = []
                    for group in cost_data['current_month_cost_by_service']:
                        if 'Keys' in group and 'Metrics' in group:
                            service_name = group['Keys'][0]
                            cost_amount = float(group['Metrics']['UnblendedCost']['Amount'])
                            if cost_amount > 0.001:  # Filter out zero-cost services
                                service_cost_data.append((service_name, cost_amount))
                    
                    # Sort by cost (highest to lowest)
                    service_cost_data.sort(key=lambda x: x[1], reverse=True)
                    
                    # Format the sorted data
                    if not service_cost_data:
                        service_costs.append("No costs associated with this profile")
                    else:
                        for service_name, cost_amount in service_cost_data:
                            service_costs.append(f"{service_name}: ${cost_amount:.2f}")
                        
                    # Format budget info
                    budget_info = []
                    for budget in cost_data['budgets']:
                        budget_info.append(f"{budget['name']} limit: ${budget['limit']}")
                        budget_info.append(f"{budget['name']} actual: ${budget['actual']:.2f}")
                    
                    account_id = cost_data.get('account_id', 'Unknown')
                    # Format EC2 instance summary
                    ec2_summary_text = []
                    for state, count in sorted(ec2_data.items()):
                        if count > 0:  # Only show states with instances
                            state_color = "bright_green" if state == "running" else "bright_yellow" if state == "stopped" else "bright_cyan"
                            ec2_summary_text.append(f"[{state_color}]{state}: {count}[/]")
                    
                    if not ec2_summary_text:
                        ec2_summary_text = ["No instances found"]
                    
                    table.add_row(
                        f"[bright_magenta]{profile}\nAccount: {account_id}[/]",
                        f"[bright_red]${cost_data['last_month']:.2f}[/]",
                        f"[bright_green]${cost_data['current_month']:.2f}[/]",
                        f"[bright_green]{'\n'.join(service_costs)}[/]",
                        f"[bright_yellow]{'\n'.join(budget_info)}[/]",
                        "\n".join(ec2_summary_text)
                    )
                    console.log(f"[bright_cyan]Processing profile: {profile} completed[/]")

                    # Export the data to CSV
                    export_data.append({
                        'profile': profile,
                        'account_id': account_id,
                        'last_month': cost_data['last_month'],
                        'current_month': cost_data['current_month'],
                        'service_costs': service_cost_data,
                        'budget_info': budget_info,
                        'ec2_summary': ec2_data
                    })

                except Exception as e:
                    console.log(f"[bold red]Error processing profile {profile}: {str(e)}[/]")
                    table.add_row(
                        f"[bright_magenta]{profile}[/]",
                        "[red]Error[/]",
                        "[red]Error[/]",
                        f"[red]Failed to process profile: {str(e)}[/]",
                        "[red]N/A[/]",
                        "[red]N/A[/]"
                    )
                    export_data.append({
                        'profile': profile,
                        'account_id': 'Error',
                        'last_month': 0,
                        'current_month': 0,
                        'service_costs': [],
                        'budget_info': ['N/A'],
                        'ec2_summary': {'N/A' : 'N/A'}
                    })
                
    # Export to CSV if requested
    if args.export_csv:
        export_to_csv(export_data, args.export_csv, args.dir)

if __name__ == "__main__":
    main()
