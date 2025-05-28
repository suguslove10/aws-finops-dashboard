"""AWS FinOps Dashboard package."""

__version__ = "2.4.0"  # Update version to reflect the new feature

from aws_finops_dashboard.dashboard_runner import run_dashboard
from aws_finops_dashboard.ri_optimizer import (
    RIOptimizer, 
    get_ri_and_sp_recommendations,
    display_optimization_summary
)
from aws_finops_dashboard.resource_analyzer import (
    UnusedResourceAnalyzer,
    analyze_unused_resources
)
from aws_finops_dashboard.resource_analyzer_export import export_unused_resources

__all__ = [
    "run_dashboard", 
    "RIOptimizer", 
    "get_ri_and_sp_recommendations",
    "display_optimization_summary",
    "UnusedResourceAnalyzer",
    "analyze_unused_resources",
    "export_unused_resources"
]
