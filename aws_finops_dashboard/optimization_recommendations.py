"""
AI-powered cost optimization recommendations for AWS resources.
This module provides recommendations for cost savings based on usage patterns.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set

import boto3
from boto3.session import Session
from rich.console import Console
from rich.status import Status

from aws_finops_dashboard.types import (
    OptimizationRecommendation,
    EC2Recommendation,
    RIRecommendation,
    SavingsPlansRecommendation,
    ResourceRecommendation,
)

console = Console()
logger = logging.getLogger(__name__)

# EC2 instance type families for right-sizing comparisons
INSTANCE_FAMILIES = {
    "t2": ["t2.nano", "t2.micro", "t2.small", "t2.medium", "t2.large", "t2.xlarge", "t2.2xlarge"],
    "t3": ["t3.nano", "t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge", "t3.2xlarge"],
    "m5": ["m5.large", "m5.xlarge", "m5.2xlarge", "m5.4xlarge", "m5.8xlarge", "m5.12xlarge", "m5.16xlarge", "m5.24xlarge"],
    "c5": ["c5.large", "c5.xlarge", "c5.2xlarge", "c5.4xlarge", "c5.9xlarge", "c5.12xlarge", "c5.18xlarge", "c5.24xlarge"],
    "r5": ["r5.large", "r5.xlarge", "r5.2xlarge", "r5.4xlarge", "r5.8xlarge", "r5.12xlarge", "r5.16xlarge", "r5.24xlarge"],
}

# Instance pricing for savings estimation (simplified for example)
INSTANCE_PRICING = {
    # t2 family
    "t2.nano": 0.0058, "t2.micro": 0.0116, "t2.small": 0.023, "t2.medium": 0.0464, 
    "t2.large": 0.0928, "t2.xlarge": 0.1856, "t2.2xlarge": 0.3712,
    # t3 family
    "t3.nano": 0.0052, "t3.micro": 0.0104, "t3.small": 0.0208, "t3.medium": 0.0416, 
    "t3.large": 0.0832, "t3.xlarge": 0.1664, "t3.2xlarge": 0.3328,
    # m5 family (examples)
    "m5.large": 0.096, "m5.xlarge": 0.192, "m5.2xlarge": 0.384,
    # c5 family (examples)
    "c5.large": 0.085, "c5.xlarge": 0.17, "c5.2xlarge": 0.34,
    # r5 family (examples)
    "r5.large": 0.126, "r5.xlarge": 0.252, "r5.2xlarge": 0.504,
}


def get_instance_pricing(instance_type: str) -> float:
    """Get hourly on-demand pricing for an EC2 instance type."""
    return INSTANCE_PRICING.get(instance_type, 0.0)


def get_smaller_instance(instance_type: str) -> Optional[str]:
    """
    Get a smaller instance type in the same family.
    
    Args:
        instance_type: Current instance type
        
    Returns:
        Smaller instance type or None if already smallest
    """
    # Extract family and size
    parts = instance_type.split(".")
    if len(parts) != 2:
        return None
    
    family = parts[0]
    
    if family not in INSTANCE_FAMILIES:
        return None
    
    instances = INSTANCE_FAMILIES[family]
    try:
        current_index = instances.index(instance_type)
        if current_index > 0:
            return instances[current_index - 1]
    except ValueError:
        pass
    
    return None


def analyze_ec2_right_sizing(
    session: Session, 
    days: int = 14,
    cpu_threshold: float = 40.0,
    regions: Optional[List[str]] = None
) -> List[EC2Recommendation]:
    """
    Analyze EC2 instances for right-sizing opportunities.
    
    Args:
        session: The boto3 session to use
        days: Number of days of historical data to analyze
        cpu_threshold: CPU utilization threshold below which an instance is considered underutilized
        regions: List of regions to analyze or None for all accessible regions
        
    Returns:
        List of EC2 right-sizing recommendations
    """
    recommendations: List[EC2Recommendation] = []
    
    # Get regions if not specified
    if regions is None:
        try:
            ec2_client = session.client("ec2", region_name="us-east-1")
            regions = [region["RegionName"] for region in ec2_client.describe_regions()["Regions"]]
        except Exception as e:
            console.log(f"[yellow]Warning: Could not get regions: {str(e)}[/]")
            regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
    
    for region in regions:
        try:
            ec2 = session.client("ec2", region_name=region)
            cloudwatch = session.client("cloudwatch", region_name=region)
            
            # Get all running instances
            response = ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
            )
            
            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance["InstanceId"]
                    instance_type = instance["InstanceType"]
                    
                    # Skip if no smaller instance type available
                    smaller_type = get_smaller_instance(instance_type)
                    if not smaller_type:
                        continue
                    
                    # Get CPU utilization metrics for the past days
                    end_time = datetime.now()
                    start_time = end_time - timedelta(days=days)
                    
                    try:
                        metric = cloudwatch.get_metric_statistics(
                            Namespace="AWS/EC2",
                            MetricName="CPUUtilization",
                            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=3600,  # 1 hour
                            Statistics=["Average", "Maximum"]
                        )
                        
                        datapoints = metric.get("Datapoints", [])
                        
                        if not datapoints:
                            continue
                        
                        # Calculate average and maximum CPU utilization
                        avg_cpu = sum(dp["Average"] for dp in datapoints) / len(datapoints)
                        max_cpu = max(dp["Maximum"] for dp in datapoints) if datapoints else 0
                        
                        # If CPU utilization is consistently low, recommend downsizing
                        if avg_cpu < cpu_threshold and max_cpu < 80.0:
                            current_cost = get_instance_pricing(instance_type) * 24 * 30  # Monthly cost
                            recommended_cost = get_instance_pricing(smaller_type) * 24 * 30
                            savings = current_cost - recommended_cost
                            
                            # Get instance name from tags
                            instance_name = ""
                            for tag in instance.get("Tags", []):
                                if tag["Key"] == "Name":
                                    instance_name = tag["Value"]
                                    break
                            
                            recommendations.append({
                                "resource_id": instance_id,
                                "resource_name": instance_name,
                                "region": region,
                                "current_type": instance_type,
                                "recommended_type": smaller_type,
                                "reason": f"Low CPU utilization (avg: {avg_cpu:.1f}%, max: {max_cpu:.1f}%)",
                                "savings": savings,
                                "metrics": {
                                    "avg_cpu": avg_cpu,
                                    "max_cpu": max_cpu,
                                    "datapoints": len(datapoints)
                                }
                            })
                    except Exception as e:
                        logger.warning(f"Error getting metrics for instance {instance_id}: {str(e)}")
        except Exception as e:
            console.log(f"[yellow]Warning: Error analyzing EC2 instances in {region}: {str(e)}[/]")
    
    # Sort recommendations by potential savings
    recommendations.sort(key=lambda x: x["savings"], reverse=True)
    return recommendations


def analyze_unused_resources(
    session: Session,
    regions: Optional[List[str]] = None
) -> List[ResourceRecommendation]:
    """
    Analyze for unused resources across the account.
    
    Args:
        session: The boto3 session to use
        regions: List of regions to analyze or None for all accessible regions
        
    Returns:
        List of resource recommendations
    """
    recommendations: List[ResourceRecommendation] = []
    
    # Get regions if not specified
    if regions is None:
        try:
            ec2_client = session.client("ec2", region_name="us-east-1")
            regions = [region["RegionName"] for region in ec2_client.describe_regions()["Regions"]]
        except Exception as e:
            console.log(f"[yellow]Warning: Could not get regions: {str(e)}[/]")
            regions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2"]
    
    for region in regions:
        try:
            ec2 = session.client("ec2", region_name=region)
            
            # Check for unused EBS volumes
            volumes_response = ec2.describe_volumes(
                Filters=[{"Name": "status", "Values": ["available"]}]
            )
            
            for volume in volumes_response.get("Volumes", []):
                volume_id = volume["VolumeId"]
                volume_size = volume["Size"]
                volume_type = volume["VolumeType"]
                
                # Estimate monthly cost
                monthly_cost = 0.0
                if volume_type == "gp2":
                    monthly_cost = volume_size * 0.10  # $0.10 per GB-month for gp2
                elif volume_type == "gp3":
                    monthly_cost = volume_size * 0.08  # $0.08 per GB-month for gp3
                elif volume_type == "io1":
                    monthly_cost = volume_size * 0.125  # Simplified for example
                
                recommendations.append({
                    "resource_id": volume_id,
                    "resource_name": "",
                    "resource_type": "EBS Volume",
                    "region": region,
                    "recommendation": "Delete unused EBS volume",
                    "reason": f"Volume has been detached for an extended period. Size: {volume_size} GB, Type: {volume_type}",
                    "savings": monthly_cost
                })
            
            # Check for unused Elastic IPs
            eips_response = ec2.describe_addresses()
            
            for eip in eips_response.get("Addresses", []):
                if "AssociationId" not in eip:
                    eip_id = eip.get("AllocationId", "")
                    public_ip = eip.get("PublicIp", "")
                    
                    # Unattached EIPs cost approximately $0.005 per hour = $3.6 per month
                    monthly_cost = 3.6
                    
                    recommendations.append({
                        "resource_id": eip_id,
                        "resource_name": public_ip,
                        "resource_type": "Elastic IP",
                        "region": region,
                        "recommendation": "Release unused Elastic IP",
                        "reason": "Elastic IP is not associated with any instance",
                        "savings": monthly_cost
                    })
            
            # Check for stopped EC2 instances
            instances_response = ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
            )
            
            for reservation in instances_response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instance_id = instance["InstanceId"]
                    instance_type = instance["InstanceType"]
                    
                    # Get instance name from tags
                    instance_name = ""
                    for tag in instance.get("Tags", []):
                        if tag["Key"] == "Name":
                            instance_name = tag["Value"]
                            break
                    
                    # Calculate cost of attached EBS volumes
                    volumes_cost = 0.0
                    for device in instance.get("BlockDeviceMappings", []):
                        if "Ebs" in device:
                            volume_id = device["Ebs"].get("VolumeId")
                            if volume_id:
                                try:
                                    vol = ec2.describe_volumes(VolumeIds=[volume_id])["Volumes"][0]
                                    vol_size = vol["Size"]
                                    vol_type = vol["VolumeType"]
                                    
                                    # Simplified cost calculation
                                    if vol_type == "gp2":
                                        volumes_cost += vol_size * 0.10
                                    elif vol_type == "gp3":
                                        volumes_cost += vol_size * 0.08
                                    elif vol_type == "io1":
                                        volumes_cost += vol_size * 0.125
                                except Exception:
                                    pass
                    
                    if volumes_cost > 0:
                        recommendations.append({
                            "resource_id": instance_id,
                            "resource_name": instance_name,
                            "resource_type": "EC2 Instance",
                            "region": region,
                            "recommendation": "Terminate stopped EC2 instance or delete unused EBS volumes",
                            "reason": f"Instance has been stopped for an extended period, but you are still paying for attached EBS volumes",
                            "savings": volumes_cost
                        })
        
        except Exception as e:
            console.log(f"[yellow]Warning: Error analyzing unused resources in {region}: {str(e)}[/]")
    
    # Sort recommendations by potential savings
    recommendations.sort(key=lambda x: x["savings"], reverse=True)
    return recommendations


def analyze_ri_opportunities(
    session: Session,
) -> List[RIRecommendation]:
    """
    Analyze Reserved Instance opportunities based on steady usage patterns.
    
    Args:
        session: The boto3 session to use
        
    Returns:
        List of RI recommendations
    """
    recommendations: List[RIRecommendation] = []
    
    try:
        # Use AWS Cost Explorer API to get RI recommendations
        ce = session.client("ce")
        
        response = ce.get_reservation_purchase_recommendation(
            Service="Amazon Elastic Compute Cloud - Compute",
            TermInYears="ONE_YEAR",
            LookbackPeriodInDays="SIXTY_DAYS",
            PaymentOption="NO_UPFRONT"
        )
        
        for recommendation in response.get("Recommendations", []):
            for detail in recommendation.get("RecommendationDetails", []):
                instance_type = detail.get("InstanceDetails", {}).get("EC2InstanceDetails", {}).get("InstanceType", "")
                if not instance_type:
                    continue
                
                estimated_savings = float(detail.get("EstimatedMonthlySavings", "0"))
                upfront_cost = float(detail.get("UpfrontCost", "0"))
                
                if estimated_savings > 0:
                    recommendations.append({
                        "instance_type": instance_type,
                        "recommended_count": int(detail.get("RecommendedNumberOfInstancesToPurchase", "0")),
                        "current_generation": True,  # Assuming all recommendations are for current gen
                        "payment_option": "No Upfront",
                        "term": "1 year",
                        "monthly_savings": estimated_savings,
                        "upfront_cost": upfront_cost,
                        "break_even_months": upfront_cost / estimated_savings if estimated_savings > 0 else 0
                    })
    except Exception as e:
        logger.warning(f"Error getting RI recommendations: {str(e)}")
        # If AWS API doesn't work, we could implement a custom analysis here
    
    # Sort recommendations by monthly savings
    recommendations.sort(key=lambda x: x["monthly_savings"], reverse=True)
    return recommendations


def analyze_savings_plans_opportunities(
    session: Session,
) -> List[SavingsPlansRecommendation]:
    """
    Analyze Savings Plans opportunities.
    
    Args:
        session: The boto3 session to use
        
    Returns:
        List of Savings Plans recommendations
    """
    recommendations: List[SavingsPlansRecommendation] = []
    
    try:
        # Use AWS Cost Explorer API to get Savings Plans recommendations
        ce = session.client("ce")
        
        response = ce.get_savings_plans_purchase_recommendation(
            SavingsPlansType="COMPUTE_SP",
            TermInYears="ONE_YEAR",
            LookbackPeriodInDays="SIXTY_DAYS",
            PaymentOption="NO_UPFRONT"
        )
        
        for recommendation in response.get("SavingsPlansPurchaseRecommendation", {}).get("SavingsPlansPurchaseRecommendationDetails", []):
            hourly_commitment = float(recommendation.get("HourlyCommitment", "0"))
            estimated_savings = float(recommendation.get("EstimatedMonthlySavings", "0"))
            
            if estimated_savings > 0:
                recommendations.append({
                    "plan_type": "Compute Savings Plan",
                    "hourly_commitment": hourly_commitment,
                    "payment_option": "No Upfront",
                    "term": "1 year",
                    "monthly_savings": estimated_savings,
                    "estimated_utilization": float(recommendation.get("EstimatedSavingsPercentage", "0"))
                })
    except Exception as e:
        logger.warning(f"Error getting Savings Plans recommendations: {str(e)}")
    
    # Sort recommendations by monthly savings
    recommendations.sort(key=lambda x: x["monthly_savings"], reverse=True)
    return recommendations


def generate_optimization_recommendations(
    session: Session,
    analyze_ec2: bool = True,
    analyze_resources: bool = True,
    analyze_reservations: bool = True,
    analyze_savings_plans: bool = True,
    regions: Optional[List[str]] = None,
    cpu_threshold: float = 40.0
) -> OptimizationRecommendation:
    """
    Generate comprehensive cost optimization recommendations.
    
    Args:
        session: The boto3 session to use
        analyze_ec2: Whether to analyze EC2 instances for right-sizing
        analyze_resources: Whether to analyze unused resources
        analyze_reservations: Whether to analyze RI opportunities
        analyze_savings_plans: Whether to analyze Savings Plans opportunities
        regions: List of regions to analyze or None for all accessible regions
        cpu_threshold: CPU utilization threshold for EC2 right-sizing
        
    Returns:
        OptimizationRecommendation containing all recommendations and summary
    """
    result: OptimizationRecommendation = {
        "ec2_recommendations": [],
        "resource_recommendations": [],
        "ri_recommendations": [],
        "savings_plans_recommendations": [],
        "summary": {
            "total_potential_savings": 0.0,
            "ec2_savings": 0.0,
            "resource_savings": 0.0,
            "ri_savings": 0.0,
            "savings_plans_savings": 0.0
        }
    }
    
    # Analyze EC2 instances for right-sizing
    if analyze_ec2:
        console.print("[bold green]Analyzing EC2 instances for right-sizing...[/]")
        result["ec2_recommendations"] = analyze_ec2_right_sizing(
            session, regions=regions, cpu_threshold=cpu_threshold
        )
        result["summary"]["ec2_savings"] = sum(rec["savings"] for rec in result["ec2_recommendations"])
    
    # Analyze unused resources
    if analyze_resources:
        console.print("[bold green]Analyzing unused resources...[/]")
        result["resource_recommendations"] = analyze_unused_resources(
            session, regions=regions
        )
        result["summary"]["resource_savings"] = sum(rec["savings"] for rec in result["resource_recommendations"])
    
    # Analyze RI opportunities
    if analyze_reservations:
        console.print("[bold green]Analyzing Reserved Instance opportunities...[/]")
        result["ri_recommendations"] = analyze_ri_opportunities(session)
        result["summary"]["ri_savings"] = sum(rec["monthly_savings"] for rec in result["ri_recommendations"])
    
    # Analyze Savings Plans opportunities
    if analyze_savings_plans:
        console.print("[bold green]Analyzing Savings Plans opportunities...[/]")
        result["savings_plans_recommendations"] = analyze_savings_plans_opportunities(session)
        result["summary"]["savings_plans_savings"] = sum(rec["monthly_savings"] for rec in result["savings_plans_recommendations"])
    
    # Calculate total potential savings
    result["summary"]["total_potential_savings"] = (
        result["summary"]["ec2_savings"] +
        result["summary"]["resource_savings"] +
        result["summary"]["ri_savings"] +
        result["summary"]["savings_plans_savings"]
    )
    
    return result 