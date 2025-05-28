#!/usr/bin/env python
"""
Debug script to test RI recommendations PDF generation.
"""

import os
from datetime import datetime
from typing import Dict, Any

from aws_finops_dashboard.dashboard_runner import _export_ri_recommendations_to_pdf
from rich.console import Console

console = Console()

def create_sample_ri_recommendations() -> Dict[str, Any]:
    """Create sample RI recommendations data for testing."""
    return {
        'recommendations': [],
        'estimated_savings': 0,
        'confidence': 'Medium',
        'analysis_period': {
            'days': 30,
            'start_date': '2023-05-01',
            'end_date': '2023-05-30'
        }
    }

def create_sample_sp_recommendations() -> Dict[str, Any]:
    """Create sample Savings Plan recommendations data for testing."""
    return {
        'recommendations': [
            {
                'plan_type': 'Compute Savings Plan',
                'hourly_commitment': 0.68,
                'monthly_commitment': 0.68 * 24 * 30,
                'term': '1 year',
                'payment_option': 'Partial Upfront',
                'estimated_monthly_savings': 122.15,
                'estimated_utilization': '90.0%',
                'confidence': 'Medium'
            }
        ],
        'estimated_total_savings': 122.15,
        'analysis_period': {
            'days': 30,
            'start_date': '2023-05-01',
            'end_date': '2023-05-30'
        }
    }

def test_ri_pdf_generation():
    """Test RI recommendations PDF generation."""
    profile = "test-profile"
    account_id = "123456789012"
    report_name = "test_ri_recommendations"
    output_dir = None  # Use current directory
    
    ri_recommendations = create_sample_ri_recommendations()
    sp_recommendations = create_sample_sp_recommendations()
    
    try:
        # Call the PDF export function directly
        _export_ri_recommendations_to_pdf(
            profile,
            account_id,
            ri_recommendations,
            sp_recommendations,
            report_name,
            output_dir
        )
        
        # Check if the file was created (approximate filename)
        timestamp = datetime.now().strftime("%Y%m%d")
        expected_filename_pattern = f"{report_name}_{profile}_ri_recommendations_{timestamp}"
        
        # Find files matching the pattern
        matching_files = [f for f in os.listdir('.') if expected_filename_pattern in f and f.endswith('.pdf')]
        
        if matching_files:
            console.print(f"[green]PDF file created successfully: {matching_files[0]}[/]")
        else:
            console.print("[red]PDF file was not found after export[/]")
            
    except Exception as e:
        console.print(f"[red]Error during PDF export: {str(e)}[/]")
        import traceback
        console.print(traceback.format_exc())
        
if __name__ == "__main__":
    test_ri_pdf_generation() 