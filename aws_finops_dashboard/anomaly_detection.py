"""
Machine learning based anomaly detection for AWS cost data.
This module provides functionality to identify unusual spending patterns and cost anomalies.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from boto3.session import Session
from rich.console import Console
from sklearn.ensemble import IsolationForest

from aws_finops_dashboard.cost_processor import get_detailed_cost_data
from aws_finops_dashboard.types import AnomalyResult

console = Console()
logger = logging.getLogger(__name__)


def collect_historical_cost_data(
    session: Session, days: int = 90, tag: Optional[List[str]] = None
) -> Dict[str, List[float]]:
    """
    Collect daily cost data over a specified period for anomaly detection.
    
    Args:
        session: The boto3 session to use
        days: Number of days of historical data to collect
        tag: Optional list of tags in "Key=Value" format to filter resources
        
    Returns:
        Dictionary with service names as keys and daily cost lists as values
    """
    try:
        # Get detailed daily cost data from Cost Explorer
        detailed_costs = get_detailed_cost_data(
            session=session, time_range=days, tag=tag, granularity="DAILY"
        )
        
        # Group by service
        service_costs: Dict[str, List[float]] = {}
        
        # Process the detailed cost data
        for day_data in detailed_costs:
            date = day_data.get("date", "")
            services = day_data.get("services", {})
            
            for service, amount in services.items():
                if service not in service_costs:
                    service_costs[service] = []
                service_costs[service].append(float(amount))
        
        return service_costs
    except Exception as e:
        console.log(f"[yellow]Error collecting historical cost data: {str(e)}[/]")
        return {}


def detect_service_anomalies(
    historical_data: Dict[str, List[float]], sensitivity: float = 0.05
) -> Dict[str, List[Tuple[int, float, float]]]:
    """
    Detect anomalies in service-level spending using Isolation Forest.
    
    Args:
        historical_data: Dictionary with service names as keys and daily cost lists as values
        sensitivity: Contamination parameter for Isolation Forest (0.01 to 0.5)
        
    Returns:
        Dictionary of services with detected anomalies (day index, cost, anomaly score)
    """
    anomalies: Dict[str, List[Tuple[int, float, float]]] = {}
    
    for service, costs in historical_data.items():
        if len(costs) < 14:  # Need minimum data points
            continue
            
        # Convert to DataFrame for time series processing
        df = pd.DataFrame({'cost': costs})
        
        # Add time-based features
        df['rolling_mean'] = df['cost'].rolling(window=7).mean()
        df['rolling_std'] = df['cost'].rolling(window=7).std()
        
        # Fill NaN values to handle initial window
        df = df.fillna(method='bfill')
        
        # Apply Isolation Forest
        model = IsolationForest(contamination=sensitivity, random_state=42)
        df['anomaly'] = model.fit_predict(df[['cost', 'rolling_mean', 'rolling_std']])
        
        # Get anomaly scores (lower is more anomalous)
        df['score'] = model.decision_function(df[['cost', 'rolling_mean', 'rolling_std']])
        
        # Extract anomalies (anomaly = -1 indicates outlier)
        anomaly_points = df[df['anomaly'] == -1].index.tolist()
        if anomaly_points:
            anomalies[service] = [
                (day, float(df.loc[day, 'cost']), float(df.loc[day, 'score'])) 
                for day in anomaly_points
            ]
    
    return anomalies


def calculate_deviation(amount: float, baseline: float) -> float:
    """
    Calculate how much a value deviates from the baseline.
    
    Args:
        amount: The anomalous amount
        baseline: The baseline amount (average)
        
    Returns:
        Deviation as a multiplier (e.g., 2.5x higher than normal)
    """
    if baseline <= 0:
        return 0
    return amount / baseline


def detect_anomalies(
    session: Session, 
    days: int = 90, 
    tag: Optional[List[str]] = None,
    sensitivity: float = 0.05
) -> AnomalyResult:
    """
    Detect unusual spending patterns in AWS cost data.
    
    Args:
        session: The boto3 session to use
        days: Number of days of historical data to analyze
        tag: Optional list of tags in "Key=Value" format to filter resources
        sensitivity: How sensitive the anomaly detection should be (0.01-0.5)
        
    Returns:
        AnomalyResult containing detected anomalies and summary
    """
    console.print("[bold cyan]Collecting historical cost data for anomaly detection...[/]")
    
    # Collect historical cost data
    historical_data = collect_historical_cost_data(session, days, tag)
    
    if not historical_data:
        return {
            "anomalies": {},
            "summary": {
                "total_anomalies": 0,
                "total_services_analyzed": 0,
                "services_with_anomalies": 0,
                "highest_deviation": 0.0,
            }
        }
    
    console.print("[bold cyan]Analyzing spending patterns for anomalies...[/]")
    
    # Detect anomalies
    anomalies_by_service = detect_service_anomalies(historical_data, sensitivity)
    
    # Calculate statistics for results
    total_anomalies = sum(len(anomalies) for anomalies in anomalies_by_service.values())
    services_with_anomalies = len(anomalies_by_service)
    total_services = len(historical_data)
    
    # Calculate baseline and deviation for each service
    processed_anomalies: Dict[str, List[Dict[str, Any]]] = {}
    highest_deviation = 0.0
    
    for service, anomaly_points in anomalies_by_service.items():
        service_costs = historical_data[service]
        baseline = sum(service_costs) / len(service_costs) if service_costs else 0
        
        processed_anomalies[service] = []
        
        for day_idx, amount, score in anomaly_points:
            # Calculate how many days ago this was
            days_ago = len(service_costs) - day_idx - 1
            date_str = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            
            # Calculate deviation
            deviation = calculate_deviation(amount, baseline)
            highest_deviation = max(highest_deviation, deviation)
            
            processed_anomalies[service].append({
                "date": date_str,
                "amount": amount,
                "baseline": baseline,
                "deviation": deviation,
                "score": score,
                "days_ago": days_ago
            })
    
    return {
        "anomalies": processed_anomalies,
        "summary": {
            "total_anomalies": total_anomalies,
            "total_services_analyzed": total_services,
            "services_with_anomalies": services_with_anomalies,
            "highest_deviation": highest_deviation,
        }
    } 