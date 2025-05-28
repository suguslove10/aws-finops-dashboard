"""
Reserved Instance and Savings Plan Optimization Module.

This module analyzes current usage patterns and provides recommendations
for Reserved Instance purchases and Savings Plan commitments.
"""

import datetime
from typing import Dict, List, Any, Optional, Tuple
import boto3
from rich.console import Console
from rich.table import Table, Column
from rich import box

console = Console()

class RIOptimizer:
    """Reserved Instance and Savings Plan optimizer for AWS resources."""
    
    def __init__(self, session: boto3.Session, lookback_period: int = 30):
        """
        Initialize the optimizer.
        
        Args:
            session: Boto3 session to use for API calls
            lookback_period: Number of days to look back for usage analysis
        """
        self.session = session
        self.lookback_period = lookback_period
        self.ce_client = session.client('ce')  # Cost Explorer client
        
    def analyze_usage_patterns(self) -> Dict[str, Any]:
        """
        Analyze usage patterns to identify consistent resource usage.
        
        Returns:
            Dictionary containing usage patterns by service and instance type
        """
        # Get start and end dates for the analysis period
        end_date = datetime.datetime.now().date()
        start_date = end_date - datetime.timedelta(days=self.lookback_period)
        
        # Format dates for Cost Explorer API
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        try:
            # Get EC2 usage by instance type
            ec2_usage = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date_str,
                    'End': end_date_str
                },
                Granularity='DAILY',
                Metrics=['UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'INSTANCE_TYPE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'REGION'
                    }
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Elastic Compute Cloud - Compute']
                    }
                }
            )
            
            # Get RDS usage by instance type
            rds_usage = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date_str,
                    'End': end_date_str
                },
                Granularity='DAILY',
                Metrics=['UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'INSTANCE_TYPE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'REGION'
                    }
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Relational Database Service']
                    }
                }
            )
            
            return self._process_usage_data(ec2_usage, rds_usage)
            
        except Exception as e:
            console.print(f"[bold red]Error analyzing usage patterns: {str(e)}[/]")
            return {}
    
    def _process_usage_data(self, ec2_usage: Dict[str, Any], rds_usage: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the usage data to identify consistent usage patterns.
        
        Args:
            ec2_usage: EC2 usage data from Cost Explorer
            rds_usage: RDS usage data from Cost Explorer
            
        Returns:
            Processed usage patterns
        """
        ec2_patterns = self._extract_consistent_usage(ec2_usage, 'EC2')
        rds_patterns = self._extract_consistent_usage(rds_usage, 'RDS')
        
        return {
            'EC2': ec2_patterns,
            'RDS': rds_patterns,
            'analysis_period': {
                'days': self.lookback_period,
                'start_date': (datetime.datetime.now().date() - datetime.timedelta(days=self.lookback_period)).strftime('%Y-%m-%d'),
                'end_date': datetime.datetime.now().date().strftime('%Y-%m-%d')
            }
        }
    
    def _extract_consistent_usage(self, usage_data: Dict[str, Any], service: str) -> List[Dict[str, Any]]:
        """
        Extract consistent usage patterns from the usage data.
        
        Args:
            usage_data: Usage data from Cost Explorer
            service: Service name (EC2 or RDS)
            
        Returns:
            List of consistent usage patterns
        """
        if not usage_data or 'ResultsByTime' not in usage_data:
            return []
        
        # Track instance usage over time
        instance_usage = {}
        
        for time_period in usage_data['ResultsByTime']:
            for group in time_period.get('Groups', []):
                keys = group['Keys']
                instance_type = keys[0]
                region = keys[1]
                
                usage_quantity = float(group['Metrics']['UsageQuantity']['Amount'])
                
                if usage_quantity > 0:
                    key = f"{instance_type}:{region}"
                    if key not in instance_usage:
                        instance_usage[key] = {
                            'instance_type': instance_type,
                            'region': region,
                            'service': service,
                            'days_used': 0,
                            'total_usage': 0,
                            'daily_usage': []
                        }
                    
                    instance_usage[key]['days_used'] += 1
                    instance_usage[key]['total_usage'] += usage_quantity
                    instance_usage[key]['daily_usage'].append(usage_quantity)
        
        # Identify consistent usage
        consistent_usage = []
        for key, data in instance_usage.items():
            # Calculate usage consistency
            usage_consistency = data['days_used'] / self.lookback_period
            
            if usage_consistency >= 0.7:  # At least 70% of days had usage
                avg_daily_usage = data['total_usage'] / data['days_used']
                
                # Calculate standard deviation to assess stability
                if len(data['daily_usage']) > 1:
                    mean = sum(data['daily_usage']) / len(data['daily_usage'])
                    variance = sum((x - mean) ** 2 for x in data['daily_usage']) / len(data['daily_usage'])
                    std_dev = variance ** 0.5
                    
                    # Coefficient of variation (lower is more stable)
                    cv = std_dev / mean if mean > 0 else float('inf')
                else:
                    cv = 0
                
                consistent_usage.append({
                    'instance_type': data['instance_type'],
                    'region': data['region'],
                    'service': data['service'],
                    'consistency': usage_consistency,
                    'avg_daily_usage': avg_daily_usage,
                    'stability': 'High' if cv < 0.1 else ('Medium' if cv < 0.3 else 'Low'),
                    'total_hours': int(data['total_usage']),
                    'recommendation_confidence': 'High' if (usage_consistency > 0.9 and cv < 0.1) else 
                                              ('Medium' if (usage_consistency > 0.8 and cv < 0.2) else 'Low')
                })
        
        # Sort by total hours (highest first)
        return sorted(consistent_usage, key=lambda x: x['total_hours'], reverse=True)
    
    def get_ri_recommendations(self) -> Dict[str, Any]:
        """
        Generate Reserved Instance purchase recommendations.
        
        Returns:
            Dictionary with RI purchase recommendations
        """
        usage_patterns = self.analyze_usage_patterns()
        
        if not usage_patterns:
            return {
                'recommendations': [],
                'estimated_savings': 0,
                'confidence': 'Low'
            }
        
        # Analyze EC2 patterns for RI recommendations
        ec2_recommendations = self._generate_ec2_ri_recommendations(usage_patterns['EC2'])
        
        # Analyze RDS patterns for RI recommendations
        rds_recommendations = self._generate_rds_ri_recommendations(usage_patterns['RDS'])
        
        # Combine recommendations
        all_recommendations = ec2_recommendations + rds_recommendations
        total_savings = sum(rec['monthly_savings'] for rec in all_recommendations)
        
        # Determine overall confidence based on individual recommendation confidence
        confidence_levels = [rec['confidence'] for rec in all_recommendations]
        overall_confidence = 'High' if all(c == 'High' for c in confidence_levels) else \
                            ('Medium' if any(c == 'Medium' for c in confidence_levels) else 'Low')
        
        return {
            'recommendations': all_recommendations,
            'estimated_savings': total_savings,
            'confidence': overall_confidence,
            'analysis_period': usage_patterns['analysis_period']
        }
    
    def _generate_ec2_ri_recommendations(self, ec2_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate EC2 Reserved Instance recommendations.
        
        Args:
            ec2_patterns: EC2 usage patterns
            
        Returns:
            List of EC2 RI recommendations
        """
        recommendations = []
        
        for pattern in ec2_patterns:
            if pattern['recommendation_confidence'] == 'Low':
                continue
                
            instance_type = pattern['instance_type']
            region = pattern['region']
            avg_daily_usage = pattern['avg_daily_usage']
            
            # Calculate number of instances to reserve
            # For EC2, we need to be conservative to avoid over-commitment
            # Round down to the nearest whole number
            recommended_count = int(avg_daily_usage / 24)  # Convert from hours to instance count
            
            if recommended_count < 1:
                continue
                
            # Calculate estimated savings
            # This is a simplification - in a real implementation, we would query the
            # AWS Price List API for exact pricing
            on_demand_hourly_rate = self._get_ec2_hourly_rate(instance_type, region)
            ri_hourly_rate = on_demand_hourly_rate * 0.6  # Estimate 40% savings with RIs
            hourly_savings = (on_demand_hourly_rate - ri_hourly_rate) * recommended_count
            monthly_savings = hourly_savings * 24 * 30  # Approximate month as 30 days
            
            recommendations.append({
                'service': 'EC2',
                'instance_type': instance_type,
                'region': region,
                'current_usage': pattern['total_hours'] / self.lookback_period,  # Average daily hours
                'recommended_count': recommended_count,
                'commitment_term': '1 year',  # Default to 1 year for safer recommendation
                'payment_option': 'Partial Upfront',  # Best balance of savings and flexibility
                'monthly_savings': monthly_savings,
                'confidence': pattern['recommendation_confidence'],
                'utilization_projection': f"{pattern['consistency'] * 100:.1f}%"
            })
            
        return recommendations
    
    def _generate_rds_ri_recommendations(self, rds_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate RDS Reserved Instance recommendations.
        
        Args:
            rds_patterns: RDS usage patterns
            
        Returns:
            List of RDS RI recommendations
        """
        recommendations = []
        
        for pattern in rds_patterns:
            if pattern['recommendation_confidence'] == 'Low':
                continue
                
            instance_type = pattern['instance_type']
            region = pattern['region']
            avg_daily_usage = pattern['avg_daily_usage']
            
            # Calculate number of instances to reserve
            recommended_count = int(avg_daily_usage / 24)
            
            if recommended_count < 1:
                continue
                
            # Calculate estimated savings
            on_demand_hourly_rate = self._get_rds_hourly_rate(instance_type, region)
            ri_hourly_rate = on_demand_hourly_rate * 0.55  # Estimate 45% savings with RIs
            hourly_savings = (on_demand_hourly_rate - ri_hourly_rate) * recommended_count
            monthly_savings = hourly_savings * 24 * 30
            
            recommendations.append({
                'service': 'RDS',
                'instance_type': instance_type,
                'region': region,
                'current_usage': pattern['total_hours'] / self.lookback_period,
                'recommended_count': recommended_count,
                'commitment_term': '1 year',
                'payment_option': 'Partial Upfront',
                'monthly_savings': monthly_savings,
                'confidence': pattern['recommendation_confidence'],
                'utilization_projection': f"{pattern['consistency'] * 100:.1f}%"
            })
            
        return recommendations
    
    def _get_ec2_hourly_rate(self, instance_type: str, region: str) -> float:
        """
        Get the estimated on-demand hourly rate for an EC2 instance type.
        
        In a production implementation, this would use the AWS Price List API.
        For now, we use estimated prices based on common instance types.
        
        Args:
            instance_type: EC2 instance type
            region: AWS region
            
        Returns:
            Estimated hourly rate
        """
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
            'us-east-1': 1.0,      # N. Virginia
            'us-east-2': 1.0,      # Ohio
            'us-west-1': 1.1,      # N. California
            'us-west-2': 1.0,      # Oregon
            'eu-west-1': 1.05,     # Ireland
            'eu-central-1': 1.15,  # Frankfurt
            'ap-northeast-1': 1.15,# Tokyo
            'ap-southeast-1': 1.1, # Singapore
            'ap-southeast-2': 1.15,# Sydney
            'ap-south-1': 1.1,     # Mumbai
        }
        
        base_price = base_prices.get(instance_type, 0.1)  # Default if unknown
        region_multiplier = region_multipliers.get(region, 1.0)
        
        return base_price * region_multiplier
    
    def _get_rds_hourly_rate(self, instance_type: str, region: str) -> float:
        """
        Get the estimated on-demand hourly rate for an RDS instance type.
        
        Args:
            instance_type: RDS instance type
            region: AWS region
            
        Returns:
            Estimated hourly rate
        """
        # Simplified pricing model for RDS
        base_prices = {
            'db.t2.micro': 0.017,
            'db.t2.small': 0.034,
            'db.t2.medium': 0.068,
            'db.t3.micro': 0.016,
            'db.t3.small': 0.032,
            'db.t3.medium': 0.064,
            'db.m5.large': 0.171,
            'db.m5.xlarge': 0.342,
            'db.r5.large': 0.226,
            'db.r5.xlarge': 0.452
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
        
        base_price = base_prices.get(instance_type, 0.15)  # Default if unknown
        region_multiplier = region_multipliers.get(region, 1.0)
        
        return base_price * region_multiplier
    
    def get_savings_plan_recommendations(self) -> Dict[str, Any]:
        """
        Generate Savings Plan commitment recommendations.
        
        Returns:
            Dictionary with Savings Plan recommendations
        """
        # Get start and end dates for the analysis period
        end_date = datetime.datetime.now().date()
        start_date = end_date - datetime.timedelta(days=self.lookback_period)
        
        # Format dates for Cost Explorer API
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        try:
            # Get Savings Plan recommendations from AWS
            # This uses the actual AWS recommendations API
            recommendations = self.ce_client.get_savings_plans_recommendation(
                LookbackPeriod='SIXTY_DAYS',
                TermInYears='ONE_YEAR',
                PaymentOption='PARTIAL_UPFRONT',
                SavingsPlansType='COMPUTE_SP'  # Compute Savings Plans are most flexible
            )
            
            processed_recommendations = []
            total_estimated_savings = 0
            
            for rec in recommendations.get('SavingsPlansRecommendation', {}).get('SavingsPlansPurchaseRecommendation', {}).get('SavingsPlansRecommendationDetails', []):
                hourly_commitment = float(rec.get('HourlyCommitment', '0'))
                estimated_savings = float(rec.get('EstimatedSavingsAmount', '0'))
                estimated_utilization = float(rec.get('EstimatedUtilizationPercentage', '0'))
                
                total_estimated_savings += estimated_savings
                
                processed_recommendations.append({
                    'plan_type': 'Compute Savings Plan',
                    'hourly_commitment': hourly_commitment,
                    'monthly_commitment': hourly_commitment * 24 * 30,
                    'term': '1 year',
                    'payment_option': 'Partial Upfront',
                    'estimated_monthly_savings': estimated_savings,
                    'estimated_utilization': f"{estimated_utilization:.1f}%",
                    'confidence': 'High' if estimated_utilization > 90 else 'Medium'
                })
                
            return {
                'recommendations': processed_recommendations,
                'estimated_total_savings': total_estimated_savings,
                'analysis_period': {
                    'days': 60,  # AWS uses 60 days for Savings Plans recommendations
                    'start_date': start_date_str,
                    'end_date': end_date_str
                }
            }
            
        except Exception as e:
            # Fallback to generating our own recommendations if AWS API fails
            console.print(f"[yellow]Could not retrieve AWS Savings Plans recommendations. Generating estimate based on usage patterns.[/]")
            return self._generate_estimated_savings_plans()
    
    def _generate_estimated_savings_plans(self) -> Dict[str, Any]:
        """
        Generate estimated Savings Plan recommendations based on usage patterns.
        This is a fallback if the AWS API fails.
        
        Returns:
            Dictionary with estimated Savings Plan recommendations
        """
        usage_patterns = self.analyze_usage_patterns()
        
        if not usage_patterns or ('EC2' not in usage_patterns and 'RDS' not in usage_patterns):
            return {
                'recommendations': [],
                'estimated_total_savings': 0,
                'analysis_period': {
                    'days': self.lookback_period,
                    'start_date': (datetime.datetime.now().date() - datetime.timedelta(days=self.lookback_period)).strftime('%Y-%m-%d'),
                    'end_date': datetime.datetime.now().date().strftime('%Y-%m-%d')
                }
            }
        
        # Calculate total consistent usage across services
        ec2_usage_hours = sum(pattern['total_hours'] for pattern in usage_patterns.get('EC2', []) 
                             if pattern['recommendation_confidence'] != 'Low')
        
        # Convert to average hourly usage
        avg_hourly_usage = ec2_usage_hours / (self.lookback_period * 24)
        
        # Conservative estimate: commit to 70% of consistent usage
        recommended_hourly_commitment = avg_hourly_usage * 0.7
        
        # Estimate savings (typically 20-30% with Compute Savings Plans)
        estimated_savings_percentage = 0.25
        estimated_hourly_savings = recommended_hourly_commitment * estimated_savings_percentage
        estimated_monthly_savings = estimated_hourly_savings * 24 * 30
        
        recommendation = {
            'plan_type': 'Compute Savings Plan',
            'hourly_commitment': recommended_hourly_commitment,
            'monthly_commitment': recommended_hourly_commitment * 24 * 30,
            'term': '1 year',
            'payment_option': 'Partial Upfront',
            'estimated_monthly_savings': estimated_monthly_savings,
            'estimated_utilization': '90.0%',  # Conservative estimate
            'confidence': 'Medium'  # Since this is our estimate, not AWS's
        }
        
        return {
            'recommendations': [recommendation] if recommended_hourly_commitment > 0 else [],
            'estimated_total_savings': estimated_monthly_savings,
            'analysis_period': {
                'days': self.lookback_period,
                'start_date': (datetime.datetime.now().date() - datetime.timedelta(days=self.lookback_period)).strftime('%Y-%m-%d'),
                'end_date': datetime.datetime.now().date().strftime('%Y-%m-%d')
            }
        }
    
    def display_recommendations(self) -> None:
        """Display RI and Savings Plan recommendations in a formatted table."""
        # Get recommendations
        ri_recommendations = self.get_ri_recommendations()
        sp_recommendations = self.get_savings_plan_recommendations()
        
        # Display RI recommendations
        if ri_recommendations['recommendations']:
            console.print("\n[bold cyan]Reserved Instance Recommendations[/]")
            
            table = Table(
                Column("Service"),
                Column("Instance Type"),
                Column("Region"),
                Column("Count"),
                Column("Term"),
                Column("Payment Option"),
                Column("Monthly Savings ($)"),
                Column("Confidence"),
                title="Reserved Instance Recommendations",
                box=box.SIMPLE_HEAD,
                show_header=True,
                header_style="bold"
            )
            
            for rec in ri_recommendations['recommendations']:
                table.add_row(
                    rec['service'],
                    rec['instance_type'],
                    rec['region'],
                    str(rec['recommended_count']),
                    rec['commitment_term'],
                    rec['payment_option'],
                    f"${rec['monthly_savings']:.2f}",
                    rec['confidence']
                )
            
            console.print(table)
            console.print(f"Total estimated monthly savings: [bold green]${ri_recommendations['estimated_savings']:.2f}[/]")
            console.print(f"Analysis period: {ri_recommendations['analysis_period']['days']} days")
        else:
            console.print("\n[yellow]No Reserved Instance recommendations available.[/]")
        
        # Display Savings Plan recommendations
        if sp_recommendations['recommendations']:
            console.print("\n[bold cyan]Savings Plan Recommendations[/]")
            
            table = Table(
                Column("Plan Type"),
                Column("Hourly Commitment ($)"),
                Column("Term"),
                Column("Payment Option"),
                Column("Monthly Savings ($)"),
                Column("Est. Utilization"),
                Column("Confidence"),
                title="Savings Plan Recommendations",
                box=box.SIMPLE_HEAD,
                show_header=True,
                header_style="bold"
            )
            
            for rec in sp_recommendations['recommendations']:
                table.add_row(
                    rec['plan_type'],
                    f"${rec['hourly_commitment']:.2f}",
                    rec['term'],
                    rec['payment_option'],
                    f"${rec['estimated_monthly_savings']:.2f}",
                    rec['estimated_utilization'],
                    rec['confidence']
                )
            
            console.print(table)
            console.print(f"Total estimated monthly savings: [bold green]${sp_recommendations['estimated_total_savings']:.2f}[/]")
            console.print(f"Analysis period: {sp_recommendations['analysis_period']['days']} days")
        else:
            console.print("\n[yellow]No Savings Plan recommendations available.[/]")
        
        # Display total potential savings
        total_savings = ri_recommendations['estimated_savings'] + sp_recommendations.get('estimated_total_savings', 0)
        console.print(f"\n[bold green]Total potential monthly savings: ${total_savings:.2f}[/]")
        console.print(f"[bold green]Total potential annual savings: ${total_savings * 12:.2f}[/]")


def get_ri_and_sp_recommendations(session: boto3.Session, lookback_days: int = 30) -> Dict[str, Any]:
    """
    Get Reserved Instance and Savings Plan recommendations.
    
    Args:
        session: Boto3 session to use for API calls
        lookback_days: Number of days to look back for usage analysis
        
    Returns:
        Dictionary with recommendations and savings estimates
    """
    optimizer = RIOptimizer(session, lookback_days)
    
    # Get recommendations
    ri_recommendations = optimizer.get_ri_recommendations()
    sp_recommendations = optimizer.get_savings_plan_recommendations()
    
    # Calculate total savings
    total_monthly_savings = ri_recommendations['estimated_savings'] + sp_recommendations.get('estimated_total_savings', 0)
    
    return {
        'ri_recommendations': ri_recommendations['recommendations'],
        'sp_recommendations': sp_recommendations['recommendations'],
        'total_monthly_savings': total_monthly_savings,
        'total_annual_savings': total_monthly_savings * 12,
        'analysis_period_days': ri_recommendations['analysis_period']['days'],
        'confidence': ri_recommendations['confidence']
    }


def display_optimization_summary(recommendations: Dict[str, Any]) -> None:
    """
    Display a summary of the RI and SP recommendations.
    
    Args:
        recommendations: Dictionary with recommendations from get_ri_and_sp_recommendations
    """
    console.print("\n[bold cyan]Cost Optimization Summary[/]")
    console.print(f"Analysis period: {recommendations['analysis_period_days']} days")
    console.print(f"Total potential monthly savings: [bold green]${recommendations['total_monthly_savings']:.2f}[/]")
    console.print(f"Total potential annual savings: [bold green]${recommendations['total_annual_savings']:.2f}[/]")
    
    # Summary of RI recommendations
    ri_count = len(recommendations['ri_recommendations'])
    if ri_count > 0:
        ri_savings = sum(rec['monthly_savings'] for rec in recommendations['ri_recommendations'])
        console.print(f"Reserved Instance recommendations: [bold]{ri_count}[/] ({ri_savings:.2f}$/month)")
    
    # Summary of SP recommendations
    sp_count = len(recommendations['sp_recommendations'])
    if sp_count > 0:
        sp_savings = sum(rec['estimated_monthly_savings'] for rec in recommendations['sp_recommendations'])
        console.print(f"Savings Plan recommendations: [bold]{sp_count}[/] ({sp_savings:.2f}$/month)")
    
    console.print("\nRecommendation confidence: [bold]{recommendations['confidence']}[/]") 