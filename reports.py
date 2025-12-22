from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import database as db

def generate_report(report_type="Weekly"):
    filename = f"{report_type}_Tool_Report.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    
    # Title
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"TrackTool {report_type} Status Report", styles['Title']))
    
    # Header Row
    data = [["Tool ID", "Name", "Worker", "Status", "Due Date"]]
    
    # Fetch real data from your database
    tools = db.get_all_tools()
    for tool in tools:
        # tool structure: (id, qr_id, name, status, last_worker, expected_return)
        data.append([tool[1], tool[2], tool[4] if tool[4] else "N/A", tool[3], tool[5] if tool[5] else "N/A"])

    # Table Styling
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(t)
    doc.build(elements)
    return filename