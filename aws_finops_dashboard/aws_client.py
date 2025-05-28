from collections import defaultdict
from typing import Dict, List, Optional, Any

import boto3
from boto3.session import Session
from botocore.exceptions import ClientError
import botocore.exceptions
from rich.console import Console
import os
import configparser

from aws_finops_dashboard.types import BudgetInfo, EC2Summary, RegionName

console = Console()


def get_aws_profiles() -> List[str]:
    """Get all available AWS profiles from AWS config and credentials files."""
    profiles = []
    
    # Check for AWS credentials file
    credentials_path = os.path.expanduser("~/.aws/credentials")
    if os.path.exists(credentials_path):
        config = configparser.ConfigParser()
        config.read(credentials_path)
        # Add all sections except 'default' as 'profile_name'
        profiles.extend([section for section in config.sections() if section != 'default'])
        # Add 'default' if it exists
        if 'default' in config:
            profiles.append('default')
    
    # Check for AWS config file for additional profiles
    config_path = os.path.expanduser("~/.aws/config")
    if os.path.exists(config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        # AWS config uses 'profile profile_name' for non-default profiles
        profiles.extend([
            section.replace('profile ', '') 
            for section in config.sections() 
            if section.startswith('profile ') and section.replace('profile ', '') not in profiles
        ])
        # Add 'default' if it exists and not already added
        if 'default' in config.sections() and 'default' not in profiles:
            profiles.append('default')
    
    return sorted(profiles)


def get_aws_profiles_with_details() -> List[Dict[str, Any]]:
    """Get all available AWS profiles with account info and status."""
    profiles = get_aws_profiles()
    profiles_with_details = []
    
    for profile_name in profiles:
        try:
            # Create a session for this profile
            session = boto3.Session(profile_name=profile_name)
            sts_client = session.client('sts')
            
            # Get account info
            caller_identity = sts_client.get_caller_identity()
            account_id = caller_identity['Account']
            username = caller_identity['Arn'].split('/')[-1]
            
            # Get regions where this profile has access
            ec2_client = session.client('ec2', region_name='us-east-1')
            regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
            
            profiles_with_details.append({
                "name": profile_name,
                "account_id": account_id,
                "username": username,
                "status": "active",
                "regions": regions
            })
        except botocore.exceptions.ClientError as e:
            # Handle specific errors
            if 'AccessDenied' in str(e):
                profiles_with_details.append({
                    "name": profile_name,
                    "status": "access_denied",
                    "error": "Access denied. Check permissions."
                })
            elif 'ExpiredToken' in str(e):
                profiles_with_details.append({
                    "name": profile_name,
                    "status": "expired",
                    "error": "Credentials expired. Please refresh."
                })
            else:
                profiles_with_details.append({
                    "name": profile_name,
                    "status": "error",
                    "error": str(e)
                })
        except Exception as e:
            # Handle general errors
            profiles_with_details.append({
                "name": profile_name,
                "status": "error",
                "error": str(e)
            })
    
    return profiles_with_details


def validate_aws_profile(profile_name: str) -> Dict[str, Any]:
    """Validate an AWS profile and return its details."""
    try:
        # Create a session for this profile
        session = boto3.Session(profile_name=profile_name)
        sts_client = session.client('sts')
        
        # Get account info
        caller_identity = sts_client.get_caller_identity()
        account_id = caller_identity['Account']
        username = caller_identity['Arn'].split('/')[-1]
        
        return {
            "name": profile_name,
            "account_id": account_id,
            "username": username,
            "status": "active",
            "is_valid": True
        }
    except Exception as e:
        return {
            "name": profile_name,
            "status": "error",
            "error": str(e),
            "is_valid": False
        }


def get_account_details(profile_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about an AWS account."""
    try:
        session = boto3.Session(profile_name=profile_name)
        sts_client = session.client('sts')
        account_id = sts_client.get_caller_identity()['Account']
        
        # Get account aliases if available
        iam_client = session.client('iam')
        aliases = iam_client.list_account_aliases()
        account_alias = aliases['AccountAliases'][0] if aliases['AccountAliases'] else None
        
        # Get account metadata
        organizations_client = None
        try:
            organizations_client = session.client('organizations')
            account = organizations_client.describe_account(AccountId=account_id)
            account_details = account['Account']
        except Exception:
            # If organizations access isn't available, just use basic info
            account_details = {
                'Id': account_id,
                'Name': account_alias or f"Account {account_id}"
            }
        
        # Get available regions
        ec2_client = session.client('ec2', region_name='us-east-1')
        regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
        
        return {
            "account_id": account_id,
            "account_name": account_details.get('Name', account_alias or f"Account {account_id}"),
            "email": account_details.get('Email'),
            "alias": account_alias,
            "regions": regions,
            "profile_name": profile_name
        }
    except Exception as e:
        print(f"Error getting account details for profile {profile_name}: {str(e)}")
        return None


def get_account_id(session: Session) -> Optional[str]:
    """Get the AWS account ID for a session."""
    try:
        account_id = session.client("sts").get_caller_identity().get("Account")
        return str(account_id) if account_id is not None else None
    except Exception as e:
        console.log(f"[yellow]Warning: Could not get account ID: {str(e)}[/]")
        return None


def get_all_regions(session: Session) -> List[RegionName]:
    """
    Get all available AWS regions.
    Using us-east-1 as a default region to get the list of all regions.

    If the call fails, it will return a hardcoded list of common regions.
    """
    try:
        ec2_client = session.client("ec2", region_name="us-east-1")
        regions = [
            region["RegionName"] for region in ec2_client.describe_regions()["Regions"]
        ]
        return regions
    except Exception as e:
        console.log(f"[yellow]Warning: Could not get all regions: {str(e)}[/]")
        return [
            "us-east-1",
            "us-east-2",
            "us-west-1",
            "us-west-2",
            "ap-southeast-1",
            "ap-south-1",
            "eu-west-1",
            "eu-west-2",
            "eu-central-1",
        ]


def get_accessible_regions(session: Session) -> List[RegionName]:
    """Get regions that are accessible with the current credentials."""
    all_regions = get_all_regions(session)
    accessible_regions = []

    for region in all_regions:
        try:
            ec2_client = session.client("ec2", region_name=region)
            ec2_client.describe_instances(MaxResults=5)
            accessible_regions.append(region)
        except Exception:
            console.log(
                f"[yellow]Region {region} is not accessible with the current credentials[/]"
            )

    if not accessible_regions:
        console.log("[yellow]No accessible regions found. Using default regions.[/]")
        return ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]

    return accessible_regions


def ec2_summary(
    session: Session, regions: Optional[List[RegionName]] = None
) -> EC2Summary:
    """Get EC2 instance summary across specified regions or all regions."""
    if regions is None:
        regions = [
            "us-east-1",
            "us-east-2",
            "us-west-1",
            "us-west-2",
            "ap-southeast-1",
            "ap-south-1",
            "eu-central-1",
            "eu-west-1",
            "eu-west-2",
        ]

    instance_summary: EC2Summary = defaultdict(int)

    for region in regions:
        try:
            ec2_regional = session.client("ec2", region_name=region)
            instances = ec2_regional.describe_instances()
            for reservation in instances["Reservations"]:
                for instance in reservation["Instances"]:
                    state = instance["State"]["Name"]
                    instance_summary[state] += 1
        except Exception as e:
            console.log(
                f"[yellow]Warning: Could not access EC2 in region {region}: {str(e)}[/]"
            )

    if "running" not in instance_summary:
        instance_summary["running"] = 0
    if "stopped" not in instance_summary:
        instance_summary["stopped"] = 0

    return instance_summary


def get_stopped_instances(
    session: Session, regions: List[RegionName]
) -> Dict[RegionName, List[str]]:
    """Get stopped EC2 instances per region."""
    stopped = {}
    for region in regions:
        try:
            ec2 = session.client("ec2", region_name=region)
            response = ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
            )
            ids = [
                inst["InstanceId"]
                for res in response["Reservations"]
                for inst in res["Instances"]
            ]
            if ids:
                stopped[region] = ids
        except Exception as e:
            console.log(
                f"[yellow]Warning: Could not fetch stopped instances in {region}: {str(e)}[/]"
            )
    return stopped


def get_unused_volumes(
    session: Session, regions: List[RegionName]
) -> Dict[RegionName, List[str]]:
    """Get unattached EBS volumes per region."""
    unused = {}
    for region in regions:
        try:
            ec2 = session.client("ec2", region_name=region)
            response = ec2.describe_volumes(
                Filters=[{"Name": "status", "Values": ["available"]}]
            )
            vols = [vol["VolumeId"] for vol in response["Volumes"]]
            if vols:
                unused[region] = vols
        except Exception as e:
            console.log(
                f"[yellow]Warning: Could not fetch unused volumes in {region}: {str(e)}[/]"
            )
    return unused


def get_unused_eips(
    session: Session, regions: List[RegionName]
) -> Dict[RegionName, List[str]]:
    """Get unused Elastic IPs per region."""
    eips = {}
    for region in regions:
        try:
            ec2 = session.client("ec2", region_name=region)
            response = ec2.describe_addresses()
            free = [
                addr["PublicIp"]
                for addr in response["Addresses"]
                if not addr.get("AssociationId")
            ]
            if free:
                eips[region] = free
        except Exception as e:
            console.log(
                f"[yellow]Warning: Could not fetch EIPs in {region}: {str(e)}[/]"
            )
    return eips


def get_untagged_resources(
    session: Session, regions: List[str]
) -> Dict[str, Dict[str, List[str]]]:
    result: Dict[str, Dict[str, List[str]]] = {
        "EC2": {},
        "RDS": {},
        "Lambda": {},
        "ELBv2": {},
    }

    for region in regions:
        # EC2
        try:
            ec2 = session.client("ec2", region_name=region)
            response = ec2.describe_instances()
            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    if not instance.get("Tags"):
                        result["EC2"].setdefault(region, []).append(
                            instance["InstanceId"]
                        )
        except Exception as e:
            console.log(
                f"[yellow]Warning: Could not fetch EC2 instances in {region}: {str(e)}[/]"
            )

        # RDS
        try:
            rds = session.client("rds", region_name=region)
            response = rds.describe_db_instances()
            for db_instance in response["DBInstances"]:
                arn = db_instance["DBInstanceArn"]
                tags = rds.list_tags_for_resource(ResourceName=arn).get("TagList", [])
                if not tags:
                    result["RDS"].setdefault(region, []).append(
                        db_instance["DBInstanceIdentifier"]
                    )
        except Exception as e:
            console.log(
                f"[yellow]Warning: Could not fetch RDS instances in {region}: {str(e)}[/]"
            )

        # Lambda
        try:
            lambda_client = session.client("lambda", region_name=region)
            response = lambda_client.list_functions()
            for function in response["Functions"]:
                arn = function["FunctionArn"]
                tags = lambda_client.list_tags(Resource=arn).get("Tags", {})
                if not tags:
                    result["Lambda"].setdefault(region, []).append(
                        function["FunctionName"]
                    )
        except Exception as e:
            console.log(
                f"[yellow]Warning: Could not fetch Lambda functions in {region}: {str(e)}[/]"
            )

        # ELBv2
        try:
            elbv2 = session.client("elbv2", region_name=region)
            lbs = elbv2.describe_load_balancers().get("LoadBalancers", [])

            if lbs:
                arn_to_name = {
                    lb["LoadBalancerArn"]: lb["LoadBalancerName"] for lb in lbs
                }
                arns = list(arn_to_name.keys())

                tags_response = elbv2.describe_tags(ResourceArns=arns)
                for desc in tags_response["TagDescriptions"]:
                    arn = desc["ResourceArn"]
                    if not desc.get("Tags"):
                        lb_name = arn_to_name.get(arn, arn)
                        result["ELBv2"].setdefault(region, []).append(lb_name)
        except Exception as e:
            console.log(
                f"[yellow]Warning: Could not fetch ELBv2 load balancers in {region}: {str(e)}[/]"
            )

    return result


def get_budgets(session: Session) -> List[BudgetInfo]:
    account_id = get_account_id(session)
    budgets = session.client("budgets", region_name="us-east-1")

    budgets_data: List[BudgetInfo] = []
    try:
        response = budgets.describe_budgets(AccountId=account_id)
        for budget in response["Budgets"]:
            budgets_data.append(
                {
                    "name": budget["BudgetName"],
                    "limit": float(budget["BudgetLimit"]["Amount"]),
                    "actual": float(budget["CalculatedSpend"]["ActualSpend"]["Amount"]),
                    "forecast": float(
                        budget["CalculatedSpend"]
                        .get("ForecastedSpend", {})
                        .get("Amount", 0.0)
                    )
                    or None,
                }
            )
    except Exception as e:
        pass

    return budgets_data
