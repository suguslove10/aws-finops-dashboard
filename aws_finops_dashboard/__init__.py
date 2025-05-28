"""AWS FinOps Dashboard package."""

__version__ = "2.3.1"  # Update version to reflect the new feature

from aws_finops_dashboard.dashboard_runner import run_dashboard
from aws_finops_dashboard.ri_optimizer import (
    RIOptimizer, 
    get_ri_and_sp_recommendations,
    display_optimization_summary
)

__all__ = [
    "run_dashboard", 
    "RIOptimizer", 
    "get_ri_and_sp_recommendations",
    "display_optimization_summary"
]
