from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
from datetime import datetime
from typing import List, Dict, Optional
import re

from rich.console import Console
console = Console()


styles = getSampleStyleSheet()

# Custom style for the footer
audit_footer_style = ParagraphStyle(
    name="AuditFooter",
    parent=styles["Normal"],
    fontSize=8,
    textColor=colors.grey,
    alignment=1,
    leading=10
)

def export_audit_report_to_pdf(
    audit_data_list: List[Dict[str, str]],
    file_name: str = "audit_report",
    path: Optional[str] = None
) -> str:
    """
    Export the audit report to a PDF file.

    :param audit_data_list: List of dictionaries, each representing a profile/account's audit data.
    :param file_name: The base name of the output PDF file.
    :param path: Optional directory where the PDF file will be saved.
    :return: Full path of the generated PDF file.
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
        elements = []

        headers = [
            "Profile", "Account ID", "Untagged Resources",
            "Stopped EC2 Instances", "Unused Volumes",
            "Unused EIPs", "Budget Alerts"
        ]
        table_data = [headers]

        for row in audit_data_list:
            table_data.append([
                row.get("profile", ""),
                row.get("account_id", ""),
                row.get("untagged_resources", ""),
                row.get("stopped_instances", ""),
                row.get("unused_volumes", ""),
                row.get("unused_eips", ""),
                row.get("budget_alerts", ""),
            ])


        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ]))

        elements.append(Paragraph("AWS FinOps Dashboard (Audit Report)", styles["Title"]))
        elements.append(Spacer(1, 12))
        elements.append(table)
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("Note: This table lists untagged EC2, RDS, Lambda, ELBv2 only.", audit_footer_style))
        elements.append(Spacer(1, 2))
        elements.append(Paragraph(f"This audit report is generated using AWS FinOps Dashboard (CLI) \u00A9 2025 on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}", audit_footer_style))

        doc.build(elements)
        return output_filename
    except Exception as e:
        console.print(f"[bold red]Error exporting to PDF: {str(e)}[/]")
        return None


def clean_rich_tags(text: str) -> str:
    """
    Clean the rich text before writing the data to a pdf.

    :param text: The rich text to clean.
    :return: Cleaned text.
    """
    return re.sub(r"\[/?[a-zA-Z0-9#_]*\]", "", text)


def export_cost_dashboard_to_pdf(
    data: List[dict],
    filename: str,
    output_dir: Optional[str] = None,
    previous_period_dates: str = "N/A",
    current_period_dates: str = "N/A",
) -> Optional[str]:
    """Export dashboard data to a PDF file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{filename}_{timestamp}.pdf"

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_filename = os.path.join(output_dir, base_filename)
        else:
            output_filename = base_filename

        doc = SimpleDocTemplate(output_filename, pagesize=landscape(letter))
        styles = getSampleStyleSheet()
        elements = []

        previous_period_header = f"Cost for period\n({previous_period_dates})"
        current_period_header = f"Cost for period\n({current_period_dates})"

        headers = [
            "CLI Profile",
            "AWS Account ID",
            previous_period_header,
            current_period_header,
            "Cost By Service",
            "Budget Status",
            "EC2 Instances",
        ]
        table_data = [headers]

        for row in data:
            services_data = "\n".join(
                [f"{service}: ${cost:.2f}" for service, cost in row["service_costs"]]
            )
            budgets_data = (
                "\n".join(row["budget_info"]) if row["budget_info"] else "No budgets"
            )
            ec2_data_summary = "\n".join(
                [
                    f"{state}: {count}"
                    for state, count in row["ec2_summary"].items()
                    if count > 0
                ]
            )

            table_data.append([
                row["profile"],
                row["account_id"],
                f"${row['last_month']:.2f}",
                f"${row['current_month']:.2f}",
                services_data or "No costs",
                budgets_data or "No budgets",
                ec2_data_summary or "No instances",
            ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ]))

        elements.append(Paragraph("AWS FinOps Dashboard (Cost Report)", styles["Title"]))
        elements.append(Spacer(1, 12))
        elements.append(table)
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"This report is generated using AWS FinOps Dashboard (CLI) \u00A9 2025 on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}", audit_footer_style))

        doc.build(elements)
        return os.path.abspath(output_filename)
    except Exception as e:
        console.print(f"[bold red]Error exporting to PDF: {str(e)}[/]")
        return None
