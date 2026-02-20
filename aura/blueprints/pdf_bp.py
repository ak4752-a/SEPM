import io
from datetime import date
from flask import Blueprint, session, make_response
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from ..models import Milestone, Contract
from .auth import login_required

pdf_bp = Blueprint('pdf', __name__)

@pdf_bp.route('/milestones/<int:milestone_id>/pdf')
@login_required
def generate_pdf(milestone_id):
    milestone = Milestone.query.join(Contract).filter(
        Milestone.id == milestone_id,
        Contract.user_id == session['user_id']
    ).first_or_404()
    contract = milestone.contract

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, spaceAfter=20)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=12, spaceAfter=6)
    body_style = styles['Normal']

    story = []
    story.append(Paragraph("Payment Reminder Notice", title_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"<b>Client:</b> {contract.client_name}", body_style))
    story.append(Paragraph(f"<b>Contract:</b> {contract.contract_name}", body_style))
    story.append(Paragraph(f"<b>Milestone:</b> {milestone.name}", body_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"<b>Amount Due:</b> ${milestone.payment_amount:,.2f}", body_style))
    due_date_str = milestone.due_date.isoformat() if milestone.due_date else 'N/A'
    story.append(Paragraph(f"<b>Due Date:</b> {due_date_str}", body_style))
    story.append(Paragraph(f"<b>Days Overdue:</b> {milestone.overdue_days}", body_style))
    story.append(Spacer(1, 0.3 * inch))

    reminder_text = (
        f"This is a formal payment reminder for the above-referenced milestone. "
        f"According to the terms of the contract, payment of <b>${milestone.payment_amount:,.2f}</b> "
        f"was due on <b>{due_date_str}</b>. "
    )
    if milestone.overdue_days > 0:
        reminder_text += (
            f"This payment is now <b>{milestone.overdue_days} days overdue</b>. "
            f"Please arrange payment at your earliest convenience to avoid further delays."
        )
    else:
        reminder_text += "Please ensure payment is made by the due date."
    story.append(Paragraph(reminder_text, body_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f"Generated on: {date.today().isoformat()}", body_style))

    doc.build(story)
    buffer.seek(0)

    filename = f"payment_reminder_{milestone_id}.pdf"
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
