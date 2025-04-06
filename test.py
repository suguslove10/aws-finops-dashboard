import boto3
from datetime import date, timedelta
from rich.console import Console
from rich.table import Table, Column
from rich.panel import Panel
from rich import box
from rich.live import Live
from time import sleep

profiles = ['05', '02', '03', '04']

console = Console()

def get_cost_data(session):
    ce = session.client('ce')
    budgets = session.client('budgets', region_name='us-east-1')
    today = date.today()
    start_of_month = today.replace(day=1).isoformat()
    last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1).isoformat()
    last_month_end = today.replace(day=1) - timedelta(days=1)

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
    last_month = ce.get_cost_and_usage(
        TimePeriod={
            'Start': last_month_start,
            'End': last_month_end.isoformat()
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
    )

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

    budgets_data = []
    try:
        response = budgets.describe_budgets(AccountId=session.client('sts').get_caller_identity().get('Account'))
        for budget in response['Budgets']:
            budgets_data.append({
                'name': budget['BudgetName'],
                'limit': float(budget['BudgetLimit']['Amount']),
                'actual': float(budget['CalculatedSpend']['ActualSpend']['Amount']),
                'forecast': float(budget['CalculatedSpend'].get('ForecastedSpend', {}).get('Amount', 0.0)) or None
            })
    except Exception as e:
        budgets_data.append({'error': str(e)})

    return{
        "current_month": float(this_month['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']),
        "last_month": float(last_month['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']),
        "current_month_cost_by_service": current_month_cost_by_service['ResultsByTime'][0]['Groups'],
        "budgets": budgets_data
    }

def ec2_summary(session):
    ec2 = session.client('ec2')
    regions = ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-southeast-1', 'ap-south-1']
    instance_summary = {'running': 0, 'stopped': 0}

    for region in regions:
        ec2_regional = session.client('ec2', region_name=region)
        instances = ec2_regional.describe_instances()
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                state = instance['State']['Name']
                if state in instance_summary:
                    instance_summary[state] += 1
    return instance_summary

table = Table("AWS Account Profile", 
              Column("Last Month Due", justify="right"), 
              Column("Current Month Cost", justify="right"), 
              Column("Cost By Service"), 
              Column("Budget Status"),
              Column("EC2 Instance Summary", justify="center"),
                title="AWS FinOps Dashboard", caption="Made by raviki", box=box.ASCII_DOUBLE_HEAD, show_lines=True, style="bright_cyan")

with Live(table, console=console, refresh_per_second=1):
    for profile in profiles:
        console.log(f"[cyan]Processing profile: {profile}[/]")

        session = boto3.Session(profile_name=profile)
        cost_data = get_cost_data(session)

        table.add_row(
            f"[bright_magenta]{profile}[/]",
            f"[bright_red]${cost_data['last_month']:.2f}[/]",
            f"[bright_green]${cost_data['current_month']:.2f}[/]",
            f"[bright_green]{'\n'.join([f'{group['Keys'][0]}: ${float(group['Metrics']['UnblendedCost']['Amount']):.2f}' for group in cost_data['current_month_cost_by_service']])}[/]",
            f"[bright_yellow]{'\n'.join([f"{budget['name']} limit: ${budget['limit']}\n{budget['name']} actual: ${budget['actual']:.2f}" 
                                for budget in cost_data['budgets']])}[/]",
            f"[bright_red]Running: {ec2_summary(session)['running']}\nStopped: {ec2_summary(session)['stopped']}[/]"
        )
        console.log(f"[bright_cyan]Processing profile: {profile} completed[/]")


        