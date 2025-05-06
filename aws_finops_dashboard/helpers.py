from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os
from datetime import datetime
from typing import List, Dict, Optional
import re

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

    elements.append(Paragraph("AWS FinOps Audit Report", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(table)
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("Note: This table lists untagged EC2, RDS, Lambda, ELBv2 only.", audit_footer_style))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(f"This audit report is generated using AWS FinOps Dashboard (CLI) \u00A9 2025 on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}", audit_footer_style))

    doc.build(elements)
    return output_filename


def clean_rich_tags(text: str) -> str:
    """
    Clean the rich text before writing the data to a pdf.

    :param text: The rich text to clean.
    :return: Cleaned text.
    """
    return re.sub(r"\[/?[a-zA-Z0-9#_]*\]", "", text)
