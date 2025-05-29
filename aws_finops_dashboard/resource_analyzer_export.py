"""
Export module for Unused Resource Analyzer.

This module provides functionality to export unused resource reports
in various formats including CSV, JSON, and PDF.
"""

import json
import csv
import os
from typing import Dict, Any, List, Optional
import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from aws_finops_dashboard.helpers import convert_currency, format_currency, get_currency_symbol


def export_to_json(data: Dict[str, Any], output_file: str) -> str:
    """
    Export unused resource data to JSON format.
    
    Args:
        data: Dictionary of unused resource data
        output_file: Destination file path
        
    Returns:
        Path to the exported file
    """
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return output_file


def export_to_csv(data: Dict[str, Any], output_file: str) -> str:
    """
    Export unused resource data to CSV format.
    
    Args:
        data: Dictionary of unused resource data
        output_file: Destination file path
        
    Returns:
        Path to the exported file
    """
    # Create a list to hold all resource entries
    all_resources = []
    
    # Add EC2 instances
    for instance in data.get('ec2_instances', []):
        resource = {
            'Resource Type': 'EC2 Instance',
            'Resource ID': instance['resource_id'],
            'Name': instance.get('name', 'Unnamed'),
            'Region': instance['region'],
            'State': instance['state'],
            'Utilization/Days Unused': instance.get('utilization', f"{instance['days_unused']} days"),
            'Monthly Cost ($)': f"${instance['estimated_monthly_cost']:.2f}",
            'Recommendation': instance['recommendation']
        }
        all_resources.append(resource)
    
    # Add EBS volumes
    for volume in data.get('ebs_volumes', []):
        resource = {
            'Resource Type': 'EBS Volume',
            'Resource ID': volume['resource_id'],
            'Name': volume.get('name', 'Unnamed'),
            'Region': volume['region'],
            'Size': volume['size'],
            'Volume Type': volume['volume_type'],
            'Days Unused': volume['days_unused'],
            'Monthly Cost ($)': f"${volume['estimated_monthly_cost']:.2f}",
            'Recommendation': volume['recommendation']
        }
        all_resources.append(resource)
    
    # Add Elastic IPs
    for eip in data.get('elastic_ips', []):
        resource = {
            'Resource Type': 'Elastic IP',
            'Resource ID': eip['resource_id'],
            'Public IP': eip['public_ip'],
            'Region': eip['region'],
            'Monthly Cost ($)': f"${eip['estimated_monthly_cost']:.2f}",
            'Recommendation': eip['recommendation']
        }
        all_resources.append(resource)
    
    # Get all unique fields
    fields = set()
    for resource in all_resources:
        fields.update(resource.keys())
    
    fields = sorted(list(fields))
    
    # Write CSV file
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for resource in all_resources:
            writer.writerow(resource)
    
    return output_file


def export_to_pdf(data: Dict[str, Any], output_file: str, currency: str = "USD") -> str:
    """
    Export unused resource data to PDF format.
    
    Args:
        data: Dictionary of unused resource data
        output_file: Destination file path
        currency: Currency code (default: USD)
        
    Returns:
        Path to the exported file
    """
    # Initialize PDF document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=landscape(letter),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Add title and date
    title = Paragraph(f"AWS Unused Resources Report", styles['Title'])
    elements.append(title)
    
    # Add report generation date
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_paragraph = Paragraph(f"Generated on: {date_str}", styles['Normal'])
    elements.append(date_paragraph)
    
    # Add account information
    account_id = data.get('account_id', 'Unknown')
    account_paragraph = Paragraph(f"AWS Account: {account_id}", styles['Normal'])
    elements.append(account_paragraph)
    
    # Add spacing
    elements.append(Spacer(1, 20))
    
    # Add summary section
    total_resources = data.get('total_resources', 0)
    monthly_savings = data.get('estimated_monthly_savings', 0)
    annual_savings = data.get('estimated_annual_savings', 0)
    
    # Convert amounts to selected currency
    monthly_savings = convert_currency(monthly_savings, "USD", currency)
    annual_savings = convert_currency(annual_savings, "USD", currency)
    
    # Format with appropriate currency
    monthly_savings_formatted = format_currency(monthly_savings, currency)
    annual_savings_formatted = format_currency(annual_savings, currency)
    
    summary_title = Paragraph("Summary", styles['Heading2'])
    elements.append(summary_title)
    
    summary_data = [
        ["Total Unused Resources", str(total_resources)],
        ["Estimated Monthly Savings", monthly_savings_formatted],
        ["Estimated Annual Savings", annual_savings_formatted]
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Add EC2 Instances section
    if data.get('ec2_instances'):
        ec2_title = Paragraph("Unused or Underutilized EC2 Instances", styles['Heading2'])
        elements.append(ec2_title)
        
        ec2_data = [["Instance ID", "Name", "Region", "State", "Utilization", "Monthly Cost", "Recommendation"]]
        
        for instance in data.get('ec2_instances', []):
            # Convert cost to selected currency
            cost = convert_currency(instance['estimated_monthly_cost'], "USD", currency)
            cost_formatted = format_currency(cost, currency)
            
            ec2_data.append([
                instance['resource_id'],
                instance.get('name', 'Unnamed'),
                instance['region'],
                instance['state'],
                instance.get('utilization', f"{instance['days_unused']} days"),
                cost_formatted,
                instance['recommendation']
            ])
        
        # Adjust column widths for better formatting
        ec2_table = Table(ec2_data, colWidths=[95, 70, 60, 60, 75, 75, 215])
        ec2_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('WORDWRAP', (0, 0), (-1, -1), True), # Enable word wrapping
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to top
        ]))
        
        elements.append(ec2_table)
        elements.append(Spacer(1, 20))
    
    # Add EBS Volumes section
    if data.get('ebs_volumes'):
        ebs_title = Paragraph("Unused EBS Volumes", styles['Heading2'])
        elements.append(ebs_title)
        
        ebs_data = [["Volume ID", "Name", "Region", "Size", "Type", "Days Unused", "Monthly Cost", "Recommendation"]]
        
        for volume in data.get('ebs_volumes', []):
            # Convert cost to selected currency
            cost = convert_currency(volume['estimated_monthly_cost'], "USD", currency)
            cost_formatted = format_currency(cost, currency)
            
            ebs_data.append([
                volume['resource_id'],
                volume.get('name', 'Unnamed'),
                volume['region'],
                volume['size'],
                volume['volume_type'],
                str(volume['days_unused']),
                cost_formatted,
                volume['recommendation']
            ])
        
        # Adjust column widths for better formatting
        ebs_table = Table(ebs_data, colWidths=[80, 70, 60, 45, 55, 60, 70, 210])
        ebs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('WORDWRAP', (0, 0), (-1, -1), True), # Enable word wrapping
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to top
        ]))
        
        elements.append(ebs_table)
        elements.append(Spacer(1, 20))
    
    # Add Elastic IPs section
    if data.get('elastic_ips'):
        eip_title = Paragraph("Unused Elastic IPs", styles['Heading2'])
        elements.append(eip_title)
        
        eip_data = [["Allocation ID", "Public IP", "Region", "Monthly Cost", "Recommendation"]]
        
        for eip in data.get('elastic_ips', []):
            # Convert cost to selected currency
            cost = convert_currency(eip['estimated_monthly_cost'], "USD", currency)
            cost_formatted = format_currency(cost, currency)
            
            eip_data.append([
                eip['resource_id'],
                eip['public_ip'],
                eip['region'],
                cost_formatted,
                eip['recommendation']
            ])
        
        # Adjust column widths for better formatting
        eip_table = Table(eip_data, colWidths=[120, 120, 80, 90, 240])
        eip_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('WORDWRAP', (0, 0), (-1, -1), True), # Enable word wrapping
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align content to top
        ]))
        
        elements.append(eip_table)
    
    # Build PDF
    doc.build(elements)
    
    return output_file


def export_unused_resources(data: Dict[str, Any], output_format: str = 'json', 
                            output_dir: str = None, report_name: str = None,
                            currency: str = "USD") -> str:
    """
    Export unused resource data to the specified format.
    
    Args:
        data: Dictionary of unused resource data
        output_format: Format to export (json, csv, pdf)
        output_dir: Directory to save the output file
        report_name: Name for the report file
        currency: Currency code (default: USD)
        
    Returns:
        Path to the exported file
    """
    # Set defaults
    if not output_dir:
        output_dir = os.getcwd()
    
    if not report_name:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"unused_resources_{timestamp}"
    
    # Create directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create output file path
    output_file = os.path.join(output_dir, f"{report_name}.{output_format}")
    
    # Export based on format
    if output_format.lower() == 'json':
        return export_to_json(data, output_file)
    elif output_format.lower() == 'csv':
        return export_to_csv(data, output_file)
    elif output_format.lower() == 'pdf':
        return export_to_pdf(data, output_file, currency)
    else:
        raise ValueError(f"Unsupported output format: {output_format}") 