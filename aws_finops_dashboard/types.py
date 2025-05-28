"""Type definitions for AWS FinOps Dashboard."""

from typing import Dict, List, Optional, Tuple, TypedDict, Any


class BudgetInfo(TypedDict):
    """Type for a budget entry."""

    name: str
    limit: float
    actual: float
    forecast: Optional[float]


class CostData(TypedDict):
    """Type for cost data returned from AWS Cost Explorer."""

    account_id: Optional[str]
    current_month: float
    last_month: float
    current_month_cost_by_service: List[Dict]
    budgets: List[BudgetInfo]
    current_period_name: str
    previous_period_name: str
    time_range: Optional[int]
    current_period_start: str
    current_period_end: str
    previous_period_start: str
    previous_period_end: str
    monthly_costs: Optional[List[Tuple[str, float]]]


class ProfileData(TypedDict):
    """Type for processed profile data."""

    profile: str
    account_id: str
    last_month: float
    current_month: float
    service_costs: List[Tuple[str, float]]
    service_costs_formatted: List[str]
    budget_info: List[str]
    ec2_summary: Dict[str, int]
    ec2_summary_formatted: List[str]
    success: bool
    error: Optional[str]
    current_period_name: str
    previous_period_name: str
    percent_change_in_total_cost: Optional[float]


class CLIArgs(TypedDict, total=False):
    """Type for CLI arguments."""

    profiles: Optional[List[str]]
    regions: Optional[List[str]]
    all: bool
    combine: bool
    report_name: Optional[str]
    report_type: Optional[List[str]]
    dir: Optional[str]
    time_range: Optional[int]
    currency: Optional[str]


# Anomaly Detection Types
class AnomalyDetailItem(TypedDict):
    """Type for a single anomaly detail."""
    date: str
    amount: float
    baseline: float
    deviation: float
    score: float
    days_ago: int


class AnomalySummary(TypedDict):
    """Type for anomaly detection summary."""
    total_anomalies: int
    total_services_analyzed: int
    services_with_anomalies: int
    highest_deviation: float


class AnomalyResult(TypedDict):
    """Type for anomaly detection results."""
    anomalies: Dict[str, List[AnomalyDetailItem]]
    summary: AnomalySummary


# Cost Optimization Recommendation Types
class EC2Recommendation(TypedDict):
    """Type for EC2 instance right-sizing recommendations."""
    resource_id: str
    resource_name: str
    region: str
    current_type: str
    recommended_type: str
    reason: str
    savings: float
    metrics: Dict[str, Any]


class ResourceRecommendation(TypedDict):
    """Type for unused resource recommendations."""
    resource_id: str
    resource_name: str
    resource_type: str
    region: str
    recommendation: str
    reason: str
    savings: float


class RIRecommendation(TypedDict):
    """Type for Reserved Instance recommendations."""
    instance_type: str
    recommended_count: int
    current_generation: bool
    payment_option: str
    term: str
    monthly_savings: float
    upfront_cost: float
    break_even_months: float


class SavingsPlansRecommendation(TypedDict):
    """Type for Savings Plans recommendations."""
    plan_type: str
    hourly_commitment: float
    payment_option: str
    term: str
    monthly_savings: float
    estimated_utilization: float


class OptimizationSummary(TypedDict):
    """Type for optimization recommendations summary."""
    total_potential_savings: float
    ec2_savings: float
    resource_savings: float
    ri_savings: float
    savings_plans_savings: float


class OptimizationRecommendation(TypedDict):
    """Type for comprehensive optimization recommendations."""
    ec2_recommendations: List[EC2Recommendation]
    resource_recommendations: List[ResourceRecommendation]
    ri_recommendations: List[RIRecommendation]
    savings_plans_recommendations: List[SavingsPlansRecommendation]
    summary: OptimizationSummary


RegionName = str
EC2Summary = Dict[str, int]
