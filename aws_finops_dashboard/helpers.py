import csv  # Added csv
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# Conditional import for tomllib
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # Use tomli and alias it as tomllib
    except ImportError:
        tomllib = None  # type: ignore

import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter, A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    ListFlowable,
    ListItem,
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from rich.console import Console

from aws_finops_dashboard.types import ProfileData

console = Console()


styles = getSampleStyleSheet()

# Custom style for the footer
audit_footer_style = ParagraphStyle(
    name="AuditFooter",
    parent=styles["Normal"],
    fontSize=8,
    textColor=colors.grey,
    alignment=1,
    leading=10,
)


def export_audit_report_to_pdf(
    audit_data_list: List[Dict[str, str]],
    file_name: str = "audit_report",
    path: Optional[str] = None,
) -> Optional[str]:
    """
    Export the audit report to a PDF file.

    :param audit_data_list: List of dictionaries, each representing a profile/account's audit data.
    :param file_name: The base name of the output PDF file.
    :param path: Optional directory where the PDF file will be saved.
    :return: Full path of the generated PDF file or None on error.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{file_name}_{timestamp}.pdf"

        if path:
            os.makedirs(path, exist_ok=True)
            output_filename = os.path.join(path, base_filename)
        else:
            output_filename = base_filename

        doc = SimpleDocTemplate(output_filename, pagesize=landscape(letter))
        styles = getSampleStyleSheet()
        elements: List[Flowable] = []

        headers = [
            "Profile",
            "Account ID",
            "Untagged Resources",
            "Stopped EC2 Instances",
            "Unused Volumes",
            "Unused EIPs",
            "Budget Alerts",
        ]
        table_data = [headers]

        for row in audit_data_list:
            table_data.append(
                [
                    row.get("profile", ""),
                    row.get("account_id", ""),
                    row.get("untagged_resources", ""),
                    row.get("stopped_instances", ""),
                    row.get("unused_volumes", ""),
                    row.get("unused_eips", ""),
                    row.get("budget_alerts", ""),
                ]
            )

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.black),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ]
            )
        )

        elements.append(
            Paragraph("AWS FinOps Dashboard (Audit Report)", styles["Title"])
        )
        elements.append(Spacer(1, 12))
        elements.append(table)
        elements.append(Spacer(1, 4))
        elements.append(
            Paragraph(
                "Note: This table lists untagged EC2, RDS, Lambda, ELBv2 only.",
                audit_footer_style,
            )
        )
        elements.append(Spacer(1, 2))
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer_text = f"This audit report is generated using AWS FinOps Dashboard (CLI) \u00a9 2025 on {current_time_str}"
        elements.append(Paragraph(footer_text, audit_footer_style))

        doc.build(elements)
        return output_filename
    except Exception as e:
        console.print(f"[bold red]Error exporting audit report to PDF: {str(e)}[/]")
        return None


def clean_rich_tags(text: str) -> str:
    """
    Clean the rich text before writing the data to a pdf.

    :param text: The rich text to clean.
    :return: Cleaned text.
    """
    return re.sub(r"\[/?[a-zA-Z0-9#_]*\]", "", text)


def export_audit_report_to_csv(
    audit_data_list: List[Dict[str, str]],
    file_name: str = "audit_report",
    path: Optional[str] = None,
) -> Optional[str]:
    """Export the audit report to a CSV file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{file_name}_{timestamp}.csv"
        output_filename = base_filename
        if path:
            os.makedirs(path, exist_ok=True)
            output_filename = os.path.join(path, base_filename)

        headers = [
            "Profile",
            "Account ID",
            "Untagged Resources",
            "Stopped EC2 Instances",
            "Unused Volumes",
            "Unused EIPs",
            "Budget Alerts",
        ]
        # Corresponding keys in the audit_data_list dictionaries
        data_keys = [
            "profile",
            "account_id",
            "untagged_resources",
            "stopped_instances",
            "unused_volumes",
            "unused_eips",
            "budget_alerts",
        ]

        with open(output_filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            for item in audit_data_list:
                writer.writerow([item.get(key, "") for key in data_keys])
        return output_filename
    except Exception as e:
        console.print(f"[bold red]Error exporting audit report to CSV: {str(e)}[/]")
        return None

def export_audit_report_to_json(
        raw_audit_data: List[Dict[str, Any]],
        file_name: str = "audit_report",
        path: Optional[str] = None) -> Optional[str]:
    """Export the audit report to a JSON file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{file_name}_{timestamp}.json"
        output_filename = base_filename
        if path:
            os.makedirs(path, exist_ok=True)
            output_filename = os.path.join(path, base_filename)

        with open(output_filename, "w", encoding="utf-8") as jsonfile:
            json.dump(raw_audit_data, jsonfile, indent=4) # Use the structured list
        return output_filename
    except Exception as e:
        console.print(f"[bold red]Error exporting audit report to JSON: {str(e)}[/]")
        return None
    
def export_trend_data_to_json(
    data: Dict[str, Any],
    filename: str,
    output_dir: Optional[str] = None,
    currency: str = "USD"
) -> Optional[str]:
    """Export trend data to a JSON file."""
    try:
        if not output_dir:
            output_dir = os.getcwd()
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(
            output_dir, f"{filename}_trend_report.json"
        )

        # Convert any costs to the target currency
        export_data = {
            "currency": currency,
            "profile": data["profile"],
            "monthly_costs": []
        }
        
        # Convert costs to the target currency
        for month, cost in data["monthly_costs"]:
            converted_cost = convert_currency(cost, "USD", currency)
            export_data["monthly_costs"].append({
                "month": month,
                "cost": converted_cost,
                "formatted_cost": format_currency(converted_cost, currency)
            })

        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return file_path
    except Exception as e:
        console.print(f"[bold red]Error exporting trend data to JSON: {e}[/]")
        return None

def export_cost_dashboard_to_csv(
    export_data: List[Dict[str, Any]],
    file_name: str = "cost_report",
    path: Optional[str] = None,
) -> Optional[str]:
    """Export the cost dashboard data to a CSV file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{file_name}_{timestamp}.csv"
        output_filename = base_filename
        if path:
            os.makedirs(path, exist_ok=True)
            output_filename = os.path.join(path, base_filename)

        headers = [
            "Profile",
            "Account ID",
            "Last Month Cost",
            "Current Month Cost",
            "Percentage Change",
            "Budget Status",
            "EC2 Running",
            "EC2 Stopped",
        ]

        with open(output_filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            for item in export_data:
                if item["success"]:
                    writer.writerow([
                        item.get("profile", ""),
                        item.get("account_id", ""),
                        item.get("last_month", 0),
                        item.get("current_month", 0),
                        f"{item.get('percent_change_in_total_cost', 0):.2f}%",
                        "; ".join(item.get("budget_info", [])),
                        item.get("ec2_summary", {}).get("running", 0),
                        item.get("ec2_summary", {}).get("stopped", 0),
                    ])
                else:
                    writer.writerow([
                        item.get("profile", ""),
                        "",
                        "Error",
                        "Error",
                        "",
                        "",
                        "",
                        "",
                    ])
        return output_filename
    except Exception as e:
        console.print(f"[bold red]Error exporting cost dashboard to CSV: {str(e)}[/]")
        return None

def export_cost_dashboard_to_json(
    export_data: List[Dict[str, Any]],
    file_name: str = "cost_report",
    path: Optional[str] = None,
) -> Optional[str]:
    """Export the cost dashboard data to a JSON file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{file_name}_{timestamp}.json"
        output_filename = base_filename
        if path:
            os.makedirs(path, exist_ok=True)
            output_filename = os.path.join(path, base_filename)

        # Create a deep copy to avoid modifying the original data
        json_data = []
        for profile_data in export_data:
            # Make a copy of the data without rich formatting
            clean_data = {}
            for key, value in profile_data.items():
                if isinstance(value, str):
                    clean_data[key] = clean_rich_tags(value)
                elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                    clean_data[key] = [clean_rich_tags(item) for item in value]
                elif isinstance(value, dict):
                    clean_dict = {}
                    for k, v in value.items():
                        if isinstance(v, str):
                            clean_dict[k] = clean_rich_tags(v)
                        else:
                            clean_dict[k] = v
                    clean_data[key] = clean_dict
                else:
                    clean_data[key] = value
            json_data.append(clean_data)

        with open(output_filename, "w", encoding="utf-8") as jsonfile:
            json.dump(json_data, jsonfile, indent=4)
        return output_filename
    except Exception as e:
        console.print(f"[bold red]Error exporting cost dashboard to JSON: {str(e)}[/]")
        return None

def export_cost_dashboard_to_pdf(
    data: List[ProfileData],
    filename: str,
    output_dir: Optional[str] = None,
    previous_period_dates: str = "N/A",
    current_period_dates: str = "N/A",
    currency: str = "USD",
    enhanced: bool = False,
) -> Optional[str]:
    """Export dashboard data to a PDF file with enhanced visualizations if requested."""
    if enhanced:
        return _export_enhanced_pdf(
            data, filename, output_dir, previous_period_dates, current_period_dates, currency
        )
    else:
        return _export_standard_pdf(
            data, filename, output_dir, previous_period_dates, current_period_dates, currency
        )
        
def _export_standard_pdf(
    data: List[ProfileData],
    filename: str,
    output_dir: Optional[str] = None,
    previous_period_dates: str = "N/A",
    current_period_dates: str = "N/A",
    currency: str = "USD",
) -> Optional[str]:
    """Export dashboard data to a standard PDF file."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        console.print(
            "[bold red]ReportLab library is required for PDF export. "
            "Please install it using: pip install reportlab[/]"
        )
        return None

    try:
        if not output_dir:
            output_dir = os.getcwd()
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, f"{filename}.pdf")

        # Set up the document
        doc = SimpleDocTemplate(
            file_path, pagesize=landscape(letter), rightMargin=30, leftMargin=30
        )

        styles = getSampleStyleSheet()
        elements = []

        # Create the table headers
        table_headers = [
            "Profile",
            "Account ID",
            f"Previous Period\n({currency})",
            f"Current Period\n({currency})",
            "Services",
            "Budgets",
            "EC2 Instances",
        ]

        table_data = [table_headers]

        # Get currency symbol for formatting
        currency_symbol = get_currency_symbol(currency)

        for row in data:
            # Convert costs to the target currency
            current_month_value = convert_currency(row['current_month'], "USD", currency)
            last_month_value = convert_currency(row['last_month'], "USD", currency)
            
            # Format service costs
            services_data = []
            for service, cost in row["service_costs"]:
                converted_cost = convert_currency(cost, "USD", currency)
                formatted_cost = format_currency(converted_cost, currency)
                services_data.append(f"{service}: {formatted_cost}")
            
            services_text = "\n".join(services_data) if services_data else "No costs"
            
            # Format budget info
            budgets_data = []
            for budget_item in row["budget_info"]:
                if " limit: $" in budget_item:
                    budget_name, limit_str = budget_item.split(" limit: $")
                    limit_value = float(limit_str)
                    converted_limit = convert_currency(limit_value, "USD", currency)
                    formatted_limit = format_currency(converted_limit, currency)
                    budgets_data.append(f"{budget_name} limit: {formatted_limit}")
                elif " actual: $" in budget_item:
                    budget_name, actual_str = budget_item.split(" actual: $")
                    actual_value = float(actual_str)
                    converted_actual = convert_currency(actual_value, "USD", currency)
                    formatted_actual = format_currency(converted_actual, currency)
                    budgets_data.append(f"{budget_name} actual: {formatted_actual}")
                elif " forecast: $" in budget_item:
                    budget_name, forecast_str = budget_item.split(" forecast: $")
                    forecast_value = float(forecast_str)
                    converted_forecast = convert_currency(forecast_value, "USD", currency)
                    formatted_forecast = format_currency(converted_forecast, currency)
                    budgets_data.append(f"{budget_name} forecast: {formatted_forecast}")
                else:
                    budgets_data.append(budget_item)
                    
            budgets_text = "\n".join(budgets_data) if budgets_data else "No budgets"
            
            # Format EC2 instance summary
            ec2_data_summary = "\n".join(
                [
                    f"{state.capitalize()}: {count}"
                    for state, count in row["ec2_summary"].items()
                    if count > 0
                ]
            )

            table_data.append(
                [
                    row["profile"],
                    row["account_id"],
                    format_currency(last_month_value, currency),
                    format_currency(current_month_value, currency),
                    services_text or "No costs",
                    budgets_text or "No budgets",
                    ec2_data_summary or "No instances",
                ]
            )

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.black),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ]
            )
        )

        elements.append(
            Paragraph(f"AWS FinOps Dashboard ({currency})", styles["Title"])
        )
        elements.append(Spacer(1, 12))
        elements.append(table)
        elements.append(Spacer(1, 4))
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(
            Paragraph(
                f"Report generated on: {current_time_str}", styles["Normal"]
            )
        )

        # Build the document
        doc.build(elements)
        return file_path
    except Exception as e:
        console.print(f"[bold red]Error exporting dashboard to PDF: {e}[/]")
        import traceback
        console.print(traceback.format_exc())
        return None
        
def _export_enhanced_pdf(
    data: List[ProfileData],
    filename: str,
    output_dir: Optional[str] = None,
    previous_period_dates: str = "N/A",
    current_period_dates: str = "N/A",
    currency: str = "USD",
) -> Optional[str]:
    """Export dashboard data to a PDF file with enhanced visualizations."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import landscape, letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
            PageBreak,
            Image,
            ListFlowable,
            ListItem,
        )
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.graphics.charts.legends import Legend
        from reportlab.lib.units import inch
    except ImportError:
        console.print(
            "[bold red]ReportLab library is required for PDF export. "
            "Please install it using: pip install reportlab[/]"
        )
        return None

    try:
        if not output_dir:
            output_dir = os.getcwd()
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, f"{filename}.pdf")

        # Set up the document with landscape A4 for better table fit
        doc = SimpleDocTemplate(
            file_path, 
            pagesize=landscape(A4), 
            rightMargin=36, 
            leftMargin=36, 
            topMargin=36, 
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        # Modify existing styles or create new ones with unique names
        title_style = ParagraphStyle(
            name='EnhancedTitle', 
            fontName='Helvetica-Bold',
            fontSize=18, 
            spaceAfter=12,
            alignment=1  # 1 = center alignment
        )
        
        heading2_style = ParagraphStyle(
            name='EnhancedHeading2', 
            fontName='Helvetica-Bold',
            fontSize=14, 
            spaceAfter=8,
            spaceBefore=12
        )
        
        small_text_style = ParagraphStyle(
            name='EnhancedSmallText', 
            fontName='Helvetica',
            fontSize=8
        )
        
        exec_summary_style = ParagraphStyle(
            name='EnhancedExecutiveSummary', 
            fontName='Helvetica-Bold',
            fontSize=12,
            spaceAfter=10,
            spaceBefore=10
        )

        elements = []

        # Add title and date
        elements.append(Paragraph(f"AWS FinOps Dashboard ({currency})", title_style))
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"Report generated on: {current_time_str}", small_text_style))
        elements.append(Spacer(1, 20))
        
        # Add executive summary
        total_current_spend = 0
        total_previous_spend = 0
        total_accounts = len(data)
        
        for profile_data in data:
            if profile_data["success"]:
                current_spend = convert_currency(profile_data["current_month"], "USD", currency)
                previous_spend = convert_currency(profile_data["last_month"], "USD", currency)
                total_current_spend += current_spend
                total_previous_spend += previous_spend
        
        percentage_change = 0
        if total_previous_spend > 0:
            percentage_change = ((total_current_spend - total_previous_spend) / total_previous_spend) * 100
        
        change_text = "no change"
        if percentage_change > 0:
            change_text = f"increased by {percentage_change:.2f}%"
        elif percentage_change < 0:
            change_text = f"decreased by {abs(percentage_change):.2f}%"
            
        formatted_current = format_currency(total_current_spend, currency)
        formatted_previous = format_currency(total_previous_spend, currency)
        
        elements.append(Paragraph("Executive Summary", heading2_style))
        summary_style = ParagraphStyle(
            name='EnhancedSummary', 
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            spaceAfter=6
        )
        
        elements.append(Paragraph(
            f"This report summarizes AWS costs across {total_accounts} account{'s' if total_accounts > 1 else ''}. "
            f"The total spend for the current period ({current_period_dates}) is {formatted_current} ({currency}), which has {change_text} "
            f"compared to the previous period ({previous_period_dates}) spend of {formatted_previous} ({currency}).",
            summary_style
        ))
        
        # Add recommendations based on data
        elements.append(Paragraph("Key Observations & Recommendations:", heading2_style))
        
        recommendations = []
        
        # Check for cost increases
        if percentage_change > 10:
            recommendations.append("⚠️ Significant cost increase detected. Review services with the highest growth.")
        
        # Check for stopped instances
        stopped_instances = 0
        for profile_data in data:
            if profile_data["success"] and "stopped" in profile_data["ec2_summary"]:
                stopped_instances += profile_data["ec2_summary"]["stopped"]
        
        if stopped_instances > 0:
            recommendations.append(f"💡 You have {stopped_instances} stopped EC2 instance{'s' if stopped_instances > 1 else ''}. Consider terminating if not needed to save on EBS costs.")
            
        # Always add some general recommendations
        if not recommendations:
            recommendations.append("💡 Consider implementing AWS Cost Allocation Tags to better track spending by project or department.")
            recommendations.append("💡 Review Reserved Instance and Savings Plans coverage to optimize long-term costs.")
            recommendations.append("💡 Utilize S3 Lifecycle policies to move infrequently accessed data to cheaper storage tiers.")
        
        recommendation_items = []
        for rec in recommendations:
            recommendation_items.append(ListItem(Paragraph(rec, styles["Normal"])))
        
        elements.append(ListFlowable(recommendation_items, bulletType='bullet'))
        elements.append(Spacer(1, 20))
        
        # Add service cost distribution chart (pie chart)
        elements.append(Paragraph("Cost Distribution by Service", heading2_style))
        
        # Aggregate all services across profiles
        all_services = {}
        for profile_data in data:
            if profile_data["success"]:
                for service, cost in profile_data["service_costs"]:
                    converted_cost = convert_currency(cost, "USD", currency)
                    if service in all_services:
                        all_services[service] += converted_cost
                    else:
                        all_services[service] = converted_cost
        
        # Sort services by cost and take top 10
        top_services = sorted(all_services.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Create pie chart
        if top_services:
            drawing = Drawing(500, 300)  # Increase drawing size
            pie = Pie()
            pie.x = 125                 # Adjust position
            pie.y = 75                  # Increase height position
            pie.width = 130             # Slightly smaller
            pie.height = 130            # Slightly smaller
            
            # Only include top 7 services in pie chart to avoid overcrowding
            num_services_to_show = min(7, len(top_services))
            top_n_services = top_services[:num_services_to_show]
            
            # If there are more services, combine the rest into "Other"
            if len(top_services) > num_services_to_show:
                other_total = sum(cost for _, cost in top_services[num_services_to_show:])
                pie_data = [cost for _, cost in top_n_services] + [other_total]
                top_n_services_with_other = top_n_services + [("Other Services", other_total)]
            else:
                pie_data = [cost for _, cost in top_n_services]
                top_n_services_with_other = top_n_services
                
            pie.data = pie_data
            
            # Don't show labels on the pie itself
            pie.labels = None
            pie.slices.strokeWidth = 0.5
            
            # Add different colors for pie slices
            pie_colors = [colors.red, colors.green, colors.blue, colors.yellow, colors.cyan, 
                    colors.magenta, colors.pink, colors.lavender, colors.orange, colors.purple]
                    
            for i in range(len(pie_data)):
                pie.slices[i].fillColor = pie_colors[i % len(pie_colors)]
            
            drawing.add(pie)
            
            # Add legend with better positioning and formatting
            legend = Legend()
            legend.alignment = 'right'
            legend.x = 275              # Position further right
            legend.y = 130              # Adjust vertical position
            legend.columnMaximum = 4    # Maximum 4 items per column for better spacing
            legend.dxTextSpace = 5      # Less space between color box and text
            legend.dx = 10              # Space between columns
            legend.dy = 12              # Space between rows
            legend.fontName = 'Helvetica'
            legend.fontSize = 7         # Smaller font size
            
            # Truncate long service names more aggressively
            colorNamePairs = []
            for i, (service, cost) in enumerate(top_n_services_with_other):
                if i == len(top_n_services_with_other) - 1 and service == "Other Services":
                    # Highlight "Other" differently
                    service_name = "Other Services"
                else:
                    # Very short names for services to fit in legend
                    service_name = service
                    if len(service_name) > 18:
                        # Try to extract meaningful parts of AWS service names
                        if "Amazon" in service_name:
                            service_name = service_name.replace("Amazon ", "")
                        if "Elastic" in service_name and len(service_name) > 15:
                            service_name = service_name.replace("Elastic ", "E.")
                        if "Compute Cloud" in service_name:
                            service_name = service_name.replace("Compute Cloud", "EC2")
                        if len(service_name) > 18:
                            service_name = service_name[:16] + "..."
                
                # Add percentage to each service
                percentage = (cost / sum(pie_data)) * 100
                if percentage >= 1:  # Only show percentage if it's at least 1%
                    service_name = f"{service_name} ({percentage:.1f}%)"
                
                colorNamePairs.append((pie_colors[i % len(pie_colors)], service_name))
                
            legend.colorNamePairs = colorNamePairs
            drawing.add(legend)
            
            elements.append(drawing)
            elements.append(Spacer(1, 20))  # Add more space after the chart
        
        # Add text that summarizes the overall spending
        elements.append(Spacer(1, 10))
        currency_note = ""
        if currency != "USD":
            currency_note = f" (Currency: {currency})"
        spend_summary = Paragraph(
            f"Total current period spend: {format_currency(total_current_spend, currency)}{currency_note}", 
            summary_style
        )
        elements.append(spend_summary)
        elements.append(Spacer(1, 20))
        
        # Add month-to-month comparison bar chart if we have previous period data
        if total_previous_spend > 0:
            elements.append(Paragraph("Period Cost Comparison", heading2_style))
            
            drawing = Drawing(450, 250)  # Increase drawing size
            bc = VerticalBarChart()
            bc.x = 75
            bc.y = 50
            bc.height = 150             # Increase chart height
            bc.width = 300              # Adjust chart width
            
            # Format data with more reasonable precision
            bc.data = [[total_previous_spend, total_current_spend]]
            bc.bars[0].fillColor = colors.steelblue
            
            # More sensible Y-axis configuration
            max_value = max(total_previous_spend, total_current_spend)
            
            # Configure existing valueAxis with simpler label formatting
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = max_value * 1.1
            bc.valueAxis.valueStep = max_value / 5
            
            # Helper function to format axis labels
            def y_axis_formatter(value):
                if value >= 1000000:
                    return f"{value/1000000:.1f}M"
                elif value >= 1000:
                    return f"{value/1000:.0f}K"
                return f"{value:.0f}"
            
            # Apply label formatter
            bc.valueAxis.labelTextFormat = y_axis_formatter
            
            # Adjust spacing and positioning
            bc.categoryAxis.labels.boxAnchor = 'n'
            bc.categoryAxis.labels.dx = 0
            bc.categoryAxis.labels.dy = -5
            bc.categoryAxis.labels.angle = 0
            bc.categoryAxis.categoryNames = ['Previous Period', 'Current Period']
            
            drawing.add(bc)
            elements.append(drawing)
            elements.append(Spacer(1, 30))  # Add more space after the chart
        
        # Add page break before detailed table
        elements.append(PageBreak())
        
        # Create the table headers for the detailed data
        elements.append(Paragraph("Detailed Cost Data", heading2_style))
        
        # Use simplified headers that are guaranteed to work
        table_headers = [
            "Profile",
            "Account ID",
            f"Previous Period\n({currency})",
            f"Current Period\n({currency})",
            "Top Services",
            "Budget",
            "EC2 Instances",
        ]

        table_data = [table_headers]

        for row in data:
            if not row["success"]:
                # Skip failed profiles
                continue
                
            # Convert costs to the target currency
            current_month_value = convert_currency(row['current_month'], "USD", currency)
            last_month_value = convert_currency(row['last_month'], "USD", currency)
            
            # Format service costs - limit to top 6 services to prevent overflow
            services_data = []
            for service, cost in row["service_costs"][:6]:  # Limit to top 6 services
                converted_cost = convert_currency(cost, "USD", currency)
                formatted_cost = format_currency(converted_cost, currency)
                # Truncate long service names
                if len(service) > 25:
                    service = service[:25] + "..."
                services_data.append(f"{service}: {formatted_cost}")
            
            if len(row["service_costs"]) > 6:
                services_data.append("...")
                
            services_text = "\n".join(services_data) if services_data else "No costs"
            
            # Format budget info - show only most important items
            # Get actual and limit from the budget
            budget_limit = None
            budget_actual = None
            
            for budget_item in row["budget_info"]:
                if " limit: $" in budget_item:
                    _, limit_str = budget_item.split(" limit: $")
                    budget_limit = float(limit_str)
                elif " actual: $" in budget_item:
                    _, actual_str = budget_item.split(" actual: $")
                    budget_actual = float(actual_str)
            
            # Create a simplified budget display
            budget_data = []
            if budget_limit is not None:
                converted_limit = convert_currency(budget_limit, "USD", currency)
                budget_data.append(f"Limit: {format_currency(converted_limit, currency)}")
            
            if budget_actual is not None:
                converted_actual = convert_currency(budget_actual, "USD", currency)
                budget_data.append(f"Actual: {format_currency(converted_actual, currency)}")
                
                # Add a percentage of limit indicator
                if budget_limit is not None and budget_limit > 0:
                    percentage = (budget_actual / budget_limit) * 100
                    status = "OK" if percentage <= 100 else "OVER"
                    budget_data.append(f"{status} ({percentage:.1f}%)")
            
            budgets_text = "\n".join(budget_data) if budget_data else "No budget"
            
            # Format EC2 instance summary more clearly
            ec2_data = []
            for state, count in row["ec2_summary"].items():
                if count > 0:
                    # Simplified format without emojis
                    ec2_data.append(f"{state.capitalize()}: {count}")
            
            ec2_data_summary = "\n".join(ec2_data) if ec2_data else "No instances"

            table_data.append(
                [
                    row["profile"],
                    row["account_id"],
                    format_currency(last_month_value, currency),
                    format_currency(current_month_value, currency),
                    services_text,
                    budgets_text,
                    ec2_data_summary,
                ]
            )

        # Define column widths that work better in landscape mode
        col_widths = [70, 85, 70, 70, 200, 120, 85]
        table = Table(table_data, repeatRows=1, colWidths=col_widths)
        
        # Add more distinctive styling
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.steelblue),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, 0), 8),  # Header font size
                    ("FONTSIZE", (0, 1), (-1, -1), 7),  # Data font size (smaller)
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("WORDWRAP", (0, 0), (-1, -1), True),  # Enable word wrapping
                    # Add alternating row colors for better readability
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                    # Add some padding
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Add footer
        elements.append(Paragraph(
            f"Report generated with AWS FinOps Dashboard on {current_time_str}",
            small_text_style
        ))

        # Build the document
        doc.build(elements)
        return file_path
    except Exception as e:
        console.print(f"[bold red]Error exporting dashboard to PDF: {e}[/]")
        import traceback
        console.print(traceback.format_exc())
        return None


def load_config_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load configuration from TOML, YAML, or JSON file."""
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    try:
        with open(file_path, "rb" if file_extension == ".toml" else "r") as f:
            if file_extension == ".toml":
                if tomllib is None:
                    console.print(
                        f"[bold red]Error: TOML library (tomli) not installed for Python < 3.11. Please install it.[/]"
                    )
                    return None
                loaded_data = tomllib.load(f)
                if isinstance(loaded_data, dict):
                    return loaded_data
                console.print(
                    f"[bold red]Error: TOML file {file_path} did not load as a dictionary.[/]"
                )
                return None
            elif file_extension in [".yaml", ".yml"]:
                loaded_data = yaml.safe_load(f)
                if isinstance(loaded_data, dict):
                    return loaded_data
                console.print(
                    f"[bold red]Error: YAML file {file_path} did not load as a dictionary.[/]"
                )
                return None
            elif file_extension == ".json":
                loaded_data = json.load(f)
                if isinstance(loaded_data, dict):
                    return loaded_data
                console.print(
                    f"[bold red]Error: JSON file {file_path} did not load as a dictionary.[/]"
                )
                return None
            else:
                console.print(
                    f"[bold red]Error: Unsupported configuration file format: {file_extension}[/]"
                )
                return None
    except FileNotFoundError:
        console.print(f"[bold red]Error: Configuration file not found: {file_path}[/]")
        return None
    except tomllib.TOMLDecodeError as e:
        console.print(f"[bold red]Error decoding TOML file {file_path}: {e}[/]")
        return None
    except yaml.YAMLError as e:
        console.print(f"[bold red]Error decoding YAML file {file_path}: {e}[/]")
        return None
    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error decoding JSON file {file_path}: {e}[/]")
        return None
    except Exception as e:
        console.print(f"[bold red]Error loading configuration file {file_path}: {e}[/]")
        return None

def get_currency_symbol(currency_code: str = "USD") -> str:
    """Get the currency symbol for a given currency code."""
    currency_symbols = {
        "USD": "$",
        "INR": "₹",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "AUD": "A$",
        "CAD": "C$",
        "CNY": "¥",
    }
    return currency_symbols.get(currency_code, "$")

def convert_currency(amount: float, from_currency: str = "USD", to_currency: str = "USD") -> float:
    """
    Convert amount from one currency to another.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code (default: USD)
        to_currency: Target currency code (default: USD)
        
    Returns:
        Converted amount
    """
    if from_currency == to_currency:
        return amount
        
    # Exchange rates as of September 2023 (would ideally be fetched from an API)
    exchange_rates = {
        "USD_INR": 83.5,  # 1 USD = 83.5 INR
        "USD_EUR": 0.91,  # 1 USD = 0.91 EUR
        "USD_GBP": 0.79,  # 1 USD = 0.79 GBP
        "USD_JPY": 149.2, # 1 USD = 149.2 JPY
        "USD_AUD": 1.55,  # 1 USD = 1.55 AUD
        "USD_CAD": 1.38,  # 1 USD = 1.38 CAD
        "USD_CNY": 7.29,  # 1 USD = 7.29 CNY
    }
    
    # For simplicity, we only support conversion from USD to other currencies
    if from_currency == "USD":
        rate_key = f"USD_{to_currency}"
        if rate_key in exchange_rates:
            return amount * exchange_rates[rate_key]
    
    # If currency pair not supported, return original amount
    return amount

def format_currency(amount: float, currency_code: str = "USD") -> str:
    """
    Format amount with currency symbol.
    
    Args:
        amount: Amount to format
        currency_code: Currency code (default: USD)
        
    Returns:
        Formatted amount with currency symbol
    """
    # Use currency codes for PDF rather than symbols for better compatibility
    pdf_currency_prefixes = {
        "USD": "$",      # Dollar sign
        "INR": "Rs. ",   # Use "Rs. " instead of ₹ for better PDF compatibility
        "EUR": "€",      # Euro sign
        "GBP": "£",      # Pound sign
        "JPY": "¥",      # Yen sign
        "AUD": "A$",     # Australian dollar
        "CAD": "C$",     # Canadian dollar
        "CNY": "CN¥",    # Chinese yuan
    }
    
    symbol = pdf_currency_prefixes.get(currency_code, "$")
    
    # Format with commas for thousands separator
    if currency_code == "JPY":
        # No decimal places for JPY
        return f"{symbol}{amount:,.0f}"
    elif currency_code == "INR":
        # Format Indian style with lakhs and crores
        if amount < 100000:  # Less than 1 lakh
            return f"{symbol}{amount:,.2f}"
        elif amount < 10000000:  # Less than 1 crore
            # Convert to lakhs (1 lakh = 100,000)
            lakhs = amount / 100000
            return f"{symbol}{lakhs:.2f}L"
        else:  # 1 crore or more
            # Convert to crores (1 crore = 10,000,000)
            crores = amount / 10000000
            return f"{symbol}{crores:.2f}Cr"
    else:
        # Default formatting with 2 decimal places
        return f"{symbol}{amount:,.2f}"
