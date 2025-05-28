"""
Unused Resource Analyzer Module.

This module analyzes AWS resources to identify unused or underutilized
resources that may be candidates for termination or downsizing.
"""

import datetime
from typing import Dict, List, Any, Optional, Set
import boto3
from rich.console import Console
from rich.table import Table

console = Console()

class UnusedResourceAnalyzer:
    """Analyzer for identifying unused AWS resources."""
    
    def __init__(self, session: boto3.Session, lookback_period: int = 14):
        """
        Initialize the analyzer.
        
        Args:
            session: Boto3 session to use for API calls
            lookback_period: Number of days to look back for usage analysis
        """
        self.session = session
        self.lookback_period = lookback_period
        self.account_id = self._get_account_id()
        
    def _get_account_id(self) -> str:
        """Get the AWS account ID."""
        try:
            return self.session.client('sts').get_caller_identity().get('Account')
        except Exception:
            return "Unknown"
    
    def analyze_ec2_instances(self, regions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Analyze EC2 instances to identify unused or underutilized instances.
        
        Args:
            regions: List of regions to analyze, or None for all accessible regions
            
        Returns:
            List of unused EC2 instances with metadata
        """
        if not regions:
            try:
                regions = [region['RegionName'] for region in 
                          self.session.client('ec2').describe_regions()['Regions']]
            except Exception as e:
                console.print(f"[red]Error retrieving regions: {str(e)}[/]")
                regions = ['us-east-1']  # Default to US East 1
        
        unused_instances = []
        
        for region in regions:
            try:
                ec2 = self.session.resource('ec2', region_name=region)
                cloudwatch = self.session.client('cloudwatch', region_name=region)
                
                # Get all instances
                instances = list(ec2.instances.all())
                
                for instance in instances:
                    # Skip terminated instances
                    if instance.state['Name'] == 'terminated':
                        continue
                    
                    # Check if instance is stopped
                    if instance.state['Name'] == 'stopped':
                        # Calculate how long the instance has been stopped
                        try:
                            status_transitions = instance.state_transition_reason
                            # Extract the date if it's in the format "User initiated (YYYY-MM-DD HH:MM:SS UTC)"
                            if '(' in status_transitions and ')' in status_transitions:
                                date_str = status_transitions.split('(')[1].split(')')[0]
                                stopped_date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S %Z')
                                days_stopped = (datetime.datetime.now() - stopped_date).days
                            else:
                                days_stopped = self.lookback_period  # Default if we can't determine
                        except Exception:
                            days_stopped = self.lookback_period  # Default if we can't determine
                        
                        # Create the unused resource entry
                        instance_name = "Unnamed"
                        for tag in instance.tags or []:
                            if tag['Key'] == 'Name':
                                instance_name = tag['Value']
                                break
                        
                        unused_instances.append({
                            'resource_id': instance.id,
                            'resource_type': 'EC2 Instance',
                            'name': instance_name,
                            'region': region,
                            'state': 'stopped',
                            'days_unused': days_stopped,
                            'estimated_monthly_cost': self._estimate_ec2_monthly_cost(instance.instance_type, region),
                            'last_used': stopped_date.strftime('%Y-%m-%d') if 'stopped_date' in locals() else 'Unknown',
                            'recommendation': f"Consider terminating if not needed; stopped for {days_stopped} days"
                        })
                        continue
                    
                    # For running instances, check CloudWatch metrics to determine if they're underutilized
                    if instance.state['Name'] == 'running':
                        # Get CPU utilization for the past lookback_period days
                        end_time = datetime.datetime.now()
                        start_time = end_time - datetime.timedelta(days=self.lookback_period)
                        
                        response = cloudwatch.get_metric_statistics(
                            Namespace='AWS/EC2',
                            MetricName='CPUUtilization',
                            Dimensions=[{'Name': 'InstanceId', 'Value': instance.id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=86400,  # 1 day in seconds
                            Statistics=['Average']
                        )
                        
                        # Calculate average CPU utilization
                        if response['Datapoints']:
                            avg_cpu = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
                            
                            # If CPU utilization is consistently below 5%, flag as unused
                            if avg_cpu < 5.0:
                                instance_name = "Unnamed"
                                for tag in instance.tags or []:
                                    if tag['Key'] == 'Name':
                                        instance_name = tag['Value']
                                        break
                                
                                unused_instances.append({
                                    'resource_id': instance.id,
                                    'resource_type': 'EC2 Instance',
                                    'name': instance_name,
                                    'region': region,
                                    'state': 'underutilized',
                                    'days_unused': self.lookback_period,
                                    'estimated_monthly_cost': self._estimate_ec2_monthly_cost(instance.instance_type, region),
                                    'last_used': 'Currently running',
                                    'utilization': f"{avg_cpu:.1f}% CPU",
                                    'recommendation': f"Consider downsizing; avg CPU: {avg_cpu:.1f}%"
                                })
            except Exception as e:
                console.print(f"[yellow]Error analyzing EC2 instances in {region}: {str(e)}[/]")
                
        return unused_instances
    
    def analyze_ebs_volumes(self, regions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Analyze EBS volumes to identify unused volumes.
        
        Args:
            regions: List of regions to analyze, or None for all accessible regions
            
        Returns:
            List of unused EBS volumes with metadata
        """
        if not regions:
            try:
                regions = [region['RegionName'] for region in 
                          self.session.client('ec2').describe_regions()['Regions']]
            except Exception as e:
                console.print(f"[red]Error retrieving regions: {str(e)}[/]")
                regions = ['us-east-1']  # Default to US East 1
        
        unused_volumes = []
        
        for region in regions:
            try:
                ec2 = self.session.resource('ec2', region_name=region)
                
                # Get all volumes
                volumes = list(ec2.volumes.all())
                
                for volume in volumes:
                    # Check if volume is available (not attached)
                    if volume.state == 'available':
                        # Calculate creation date
                        create_time = volume.create_time
                        days_available = (datetime.datetime.now(datetime.timezone.utc) - create_time).days
                        
                        # Create the unused resource entry
                        volume_name = "Unnamed"
                        for tag in volume.tags or []:
                            if tag['Key'] == 'Name':
                                volume_name = tag['Value']
                                break
                        
                        unused_volumes.append({
                            'resource_id': volume.id,
                            'resource_type': 'EBS Volume',
                            'name': volume_name,
                            'region': region,
                            'state': 'available',
                            'days_unused': days_available,
                            'size': f"{volume.size} GB",
                            'volume_type': volume.volume_type,
                            'estimated_monthly_cost': self._estimate_ebs_monthly_cost(volume.size, volume.volume_type, region),
                            'last_used': 'Never attached' if not volume.attachments else 'Previously attached',
                            'recommendation': f"Consider deleting if not needed; unattached for {days_available} days"
                        })
            except Exception as e:
                console.print(f"[yellow]Error analyzing EBS volumes in {region}: {str(e)}[/]")
                
        return unused_volumes
    
    def analyze_elastic_ips(self, regions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Analyze Elastic IPs to identify unused IPs.
        
        Args:
            regions: List of regions to analyze, or None for all accessible regions
            
        Returns:
            List of unused Elastic IPs with metadata
        """
        if not regions:
            try:
                regions = [region['RegionName'] for region in 
                          self.session.client('ec2').describe_regions()['Regions']]
            except Exception as e:
                console.print(f"[red]Error retrieving regions: {str(e)}[/]")
                regions = ['us-east-1']  # Default to US East 1
        
        unused_eips = []
        
        for region in regions:
            try:
                ec2_client = self.session.client('ec2', region_name=region)
                
                # Get all Elastic IPs
                response = ec2_client.describe_addresses()
                
                for address in response.get('Addresses', []):
                    # Check if EIP is not associated with an instance
                    if 'AssociationId' not in address:
                        unused_eips.append({
                            'resource_id': address.get('AllocationId', address.get('PublicIp', 'Unknown')),
                            'resource_type': 'Elastic IP',
                            'public_ip': address.get('PublicIp', 'Unknown'),
                            'region': region,
                            'state': 'unassociated',
                            'days_unused': 'Unknown',  # AWS doesn't provide allocation time for EIPs
                            'estimated_monthly_cost': 3.6,  # $0.005 per hour for unattached EIP = ~$3.6/month
                            'recommendation': "Consider releasing if not needed; unassociated"
                        })
            except Exception as e:
                console.print(f"[yellow]Error analyzing Elastic IPs in {region}: {str(e)}[/]")
                
        return unused_eips
    
    def _estimate_ec2_monthly_cost(self, instance_type: str, region: str) -> float:
        """Estimate monthly cost for an EC2 instance."""
        # This is a simplified pricing model
        base_prices = {
            't2.micro': 0.0116,
            't2.small': 0.023,
            't2.medium': 0.0464,
            't2.large': 0.0928,
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            'm5.large': 0.096,
            'm5.xlarge': 0.192,
            'm5.2xlarge': 0.384,
            'c5.large': 0.085,
            'c5.xlarge': 0.17,
            'r5.large': 0.126,
            'r5.xlarge': 0.252
        }
        
        # Regional price adjustments
        region_multipliers = {
            'us-east-1': 1.0,
            'us-east-2': 1.0,
            'us-west-1': 1.1,
            'us-west-2': 1.0,
            'eu-west-1': 1.05,
            'eu-central-1': 1.15,
            'ap-northeast-1': 1.15,
            'ap-southeast-1': 1.1,
            'ap-southeast-2': 1.15,
            'ap-south-1': 1.1,
        }
        
        hourly_rate = base_prices.get(instance_type, 0.1) * region_multipliers.get(region, 1.0)
        return hourly_rate * 24 * 30  # Approximate month as 30 days
    
    def _estimate_ebs_monthly_cost(self, size_gb: int, volume_type: str, region: str) -> float:
        """Estimate monthly cost for an EBS volume."""
        # Base prices per GB-month
        base_prices = {
            'gp2': 0.10,
            'gp3': 0.08,
            'io1': 0.125,
            'io2': 0.125,
            'st1': 0.045,
            'sc1': 0.025,
            'standard': 0.05
        }
        
        # Regional price adjustments
        region_multipliers = {
            'us-east-1': 1.0,
            'us-east-2': 1.0,
            'us-west-1': 1.1,
            'us-west-2': 1.0,
            'eu-west-1': 1.05,
            'eu-central-1': 1.15,
            'ap-northeast-1': 1.15,
            'ap-southeast-1': 1.1,
            'ap-southeast-2': 1.15,
            'ap-south-1': 1.1,
        }
        
        gb_month_rate = base_prices.get(volume_type, 0.1) * region_multipliers.get(region, 1.0)
        return gb_month_rate * size_gb
    
    def get_all_unused_resources(self, regions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get all unused resources across different types.
        
        Args:
            regions: List of regions to analyze, or None for all accessible regions
            
        Returns:
            Dictionary with lists of unused resources by type
        """
        console.print("[cyan]Analyzing EC2 instances...[/]")
        ec2_instances = self.analyze_ec2_instances(regions)
        
        console.print("[cyan]Analyzing EBS volumes...[/]")
        ebs_volumes = self.analyze_ebs_volumes(regions)
        
        console.print("[cyan]Analyzing Elastic IPs...[/]")
        elastic_ips = self.analyze_elastic_ips(regions)
        
        # Calculate total estimated savings
        total_monthly_savings = (
            sum(instance['estimated_monthly_cost'] for instance in ec2_instances) +
            sum(volume['estimated_monthly_cost'] for volume in ebs_volumes) +
            sum(eip['estimated_monthly_cost'] for eip in elastic_ips)
        )
        
        return {
            'ec2_instances': ec2_instances,
            'ebs_volumes': ebs_volumes,
            'elastic_ips': elastic_ips,
            'total_resources': len(ec2_instances) + len(ebs_volumes) + len(elastic_ips),
            'estimated_monthly_savings': total_monthly_savings,
            'estimated_annual_savings': total_monthly_savings * 12,
            'account_id': self.account_id,
            'regions_analyzed': regions
        }
    
    def display_unused_resources(self, regions: Optional[List[str]] = None) -> None:
        """
        Display a report of unused resources.
        
        Args:
            regions: List of regions to analyze, or None for all accessible regions
        """
        results = self.get_all_unused_resources(regions)
        
        # Display EC2 instances
        if results['ec2_instances']:
            table = Table(
                title=f"Unused or Underutilized EC2 Instances",
                box=None,
                show_header=True,
                header_style="bold"
            )
            
            table.add_column("Instance ID")
            table.add_column("Name")
            table.add_column("Region")
            table.add_column("State")
            table.add_column("Utilization/Days Unused")
            table.add_column("Monthly Cost ($)")
            table.add_column("Recommendation")
            
            for instance in results['ec2_instances']:
                table.add_row(
                    instance['resource_id'],
                    instance['name'],
                    instance['region'],
                    instance['state'],
                    instance.get('utilization', f"{instance['days_unused']} days"),
                    f"${instance['estimated_monthly_cost']:.2f}",
                    instance['recommendation']
                )
            
            console.print(table)
        else:
            console.print("[green]No unused or underutilized EC2 instances found.[/]")
        
        # Display EBS volumes
        if results['ebs_volumes']:
            table = Table(
                title=f"Unused EBS Volumes",
                box=None,
                show_header=True,
                header_style="bold"
            )
            
            table.add_column("Volume ID")
            table.add_column("Name")
            table.add_column("Region")
            table.add_column("Size")
            table.add_column("Type")
            table.add_column("Days Unused")
            table.add_column("Monthly Cost ($)")
            table.add_column("Recommendation")
            
            for volume in results['ebs_volumes']:
                table.add_row(
                    volume['resource_id'],
                    volume['name'],
                    volume['region'],
                    volume['size'],
                    volume['volume_type'],
                    str(volume['days_unused']),
                    f"${volume['estimated_monthly_cost']:.2f}",
                    volume['recommendation']
                )
            
            console.print(table)
        else:
            console.print("[green]No unused EBS volumes found.[/]")
        
        # Display Elastic IPs
        if results['elastic_ips']:
            table = Table(
                title=f"Unused Elastic IPs",
                box=None,
                show_header=True,
                header_style="bold"
            )
            
            table.add_column("Allocation ID")
            table.add_column("Public IP")
            table.add_column("Region")
            table.add_column("Monthly Cost ($)")
            table.add_column("Recommendation")
            
            for eip in results['elastic_ips']:
                table.add_row(
                    eip['resource_id'],
                    eip['public_ip'],
                    eip['region'],
                    f"${eip['estimated_monthly_cost']:.2f}",
                    eip['recommendation']
                )
            
            console.print(table)
        else:
            console.print("[green]No unused Elastic IPs found.[/]")
        
        # Display summary
        console.print(f"\n[bold cyan]Summary:[/]")
        console.print(f"Total unused resources: {results['total_resources']}")
        console.print(f"Estimated monthly savings: [bold green]${results['estimated_monthly_savings']:.2f}[/]")
        console.print(f"Estimated annual savings: [bold green]${results['estimated_annual_savings']:.2f}[/]")

def analyze_unused_resources(session: boto3.Session, regions: Optional[List[str]] = None, 
                             lookback_days: int = 14) -> Dict[str, Any]:
    """
    Analyze unused AWS resources for potential cost savings.
    
    Args:
        session: Boto3 session to use for API calls
        regions: List of regions to analyze, or None for all accessible regions
        lookback_days: Number of days to look back for usage analysis
        
    Returns:
        Dictionary with lists of unused resources by type
    """
    analyzer = UnusedResourceAnalyzer(session, lookback_days)
    return analyzer.get_all_unused_resources(regions)


def display_unused_resources_summary(session: boto3.Session, regions: Optional[List[str]] = None,
                                     lookback_days: int = 14) -> None:
    """
    Display a summary of unused AWS resources.
    
    Args:
        session: Boto3 session to use for API calls
        regions: List of regions to analyze, or None for all accessible regions
        lookback_days: Number of days to look back for usage analysis
    """
    analyzer = UnusedResourceAnalyzer(session, lookback_days)
    analyzer.display_unused_resources(regions) 