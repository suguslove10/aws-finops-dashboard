#!/usr/bin/env python
"""
Debug script to test PDF generation.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

def test_pdf_generation():
    """Generate a simple test PDF."""
    filepath = "test_pdf_output.pdf"
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Add a title
    elements.append(Paragraph("Test PDF Document", styles["Title"]))
    elements.append(Spacer(1, 12))
    
    # Add some text
    elements.append(Paragraph("This is a test PDF to verify PDF generation is working.", styles["Normal"]))
    elements.append(Spacer(1, 12))
    
    # Add a simple table
    data = [
        ["Header 1", "Header 2", "Header 3"],
        ["Row 1, Col 1", "Row 1, Col 2", "Row 1, Col 3"],
        ["Row 2, Col 1", "Row 2, Col 2", "Row 2, Col 3"]
    ]
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    
    # Build the document
    try:
        doc.build(elements)
        print(f"Successfully created test PDF: {filepath}")
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_pdf_generation() 