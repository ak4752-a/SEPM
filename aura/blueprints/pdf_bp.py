import io
from datetime import date
from flask import Blueprint, session, make_response, request, abort
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from ..models import Milestone, Contract
from ..utils.money import format_amount
from .auth import login_required

pdf_bp = Blueprint('pdf', __name__)

VALID_MODES = ('normal', 'upcoming', 'overdue', 'penalty')


@pdf_bp.route('/milestones/<int:milestone_id>/pdf')
@login_required
def generate_pdf(milestone_id):
    mode = request.args.get('mode', 'normal').lower()
    if mode not in VALID_MODES:
        abort(400, 'Invalid PDF mode.')
    # 'upcoming' is an alias for 'normal'
    if mode == 'upcoming':
        mode = 'normal'

    milestone = Milestone.query.join(Contract).filter(
        Milestone.id == milestone_id,
        Contract.user_id == session['user_id']
    ).first_or_404()
    contract = milestone.contract
    currency = contract.currency or 'INR'

    today = date.today()
    due_date = milestone.due_date
    due_date_str = due_date.isoformat() if due_date else 'N/A'
    delivery_str = milestone.actual_delivery_date.isoformat() if milestone.actual_delivery_date else 'N/A'

    days_overdue = 0
    is_overdue = False
    if due_date and today > due_date and not milestone.payment:
        is_overdue = True
        days_overdue = (today - due_date).days

    # Penalty calculation
    penalty_amount = 0.0
    penalty_units = 0
    not_overdue_note = ''
    if mode == 'penalty':
        if is_overdue and milestone.penalty_enabled:
            if milestone.penalty_unit == 'month':
                penalty_units = -(-days_overdue // 30)
            else:
                penalty_units = days_overdue
            penalty_amount = round(
                milestone.payment_amount * (milestone.penalty_rate_percent / 100) * penalty_units, 2
            )
        elif not is_overdue:
            not_overdue_note = f'Not overdue as of {today.isoformat()}. Penalty = 0.'

    total_payable = milestone.payment_amount + penalty_amount

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, spaceAfter=20)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=12, spaceAfter=6)
    body_style = styles['Normal']

    # Choose title based on mode
    if mode == 'normal':
        doc_title = 'Payment Reminder Notice'
    elif mode == 'overdue':
        doc_title = 'Overdue Payment Reminder'
    else:  # penalty
        doc_title = 'Overdue Payment Reminder with Penalty'

    story = []
    story.append(Paragraph(doc_title, title_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f'<b>Client:</b> {contract.client_name}', body_style))
    story.append(Paragraph(f'<b>Contract:</b> {contract.contract_name}', body_style))
    story.append(Paragraph(f'<b>Milestone:</b> {milestone.name}', body_style))
    story.append(Paragraph(f'<b>Actual Delivery Date:</b> {delivery_str}', body_style))
    story.append(Paragraph(f'<b>Due Date:</b> {due_date_str}', body_style))
    story.append(Spacer(1, 0.2 * inch))

    amount_str = format_amount(milestone.payment_amount, currency)
    story.append(Paragraph(f'<b>Amount Due:</b> {amount_str}', body_style))

    status_label = 'Paid' if milestone.payment else ('Overdue' if is_overdue else 'Pending')
    story.append(Paragraph(f'<b>Status:</b> {status_label}', body_style))

    if mode in ('overdue', 'penalty') and is_overdue:
        story.append(Paragraph(f'<b>Days Overdue:</b> {days_overdue}', body_style))

    if mode == 'penalty':
        if not_overdue_note:
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(f'<i>{not_overdue_note}</i>', body_style))
        else:
            unit_label = 'month(s)' if milestone.penalty_unit == 'month' else 'day(s)'
            story.append(Paragraph(f'<b>Penalty Rate:</b> {milestone.penalty_rate_percent}% per {milestone.penalty_unit}', body_style))
            story.append(Paragraph(f'<b>Penalty Units:</b> {penalty_units} {unit_label}', body_style))
            story.append(Paragraph(f'<b>Penalty Amount:</b> {format_amount(penalty_amount, currency)}', body_style))
            story.append(Paragraph(f'<b>Total Payable:</b> {format_amount(total_payable, currency)}', body_style))

    story.append(Spacer(1, 0.3 * inch))

    reminder_text = (
        f'This is a formal payment reminder for the above-referenced milestone. '
        f'According to the terms of the contract, payment of <b>{amount_str}</b> '
        f'was due on <b>{due_date_str}</b>. '
    )
    if days_overdue > 0:
        reminder_text += (
            f'This payment is now <b>{days_overdue} days overdue</b>. '
            f'Please arrange payment at your earliest convenience to avoid further delays.'
        )
    else:
        reminder_text += 'Please ensure payment is made by the due date.'
    story.append(Paragraph(reminder_text, body_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(f'Generated on: {today.isoformat()}', body_style))

    doc.build(story)
    buffer.seek(0)

    mode_suffix = f'_{mode}' if mode != 'normal' else ''
    filename = f'payment_reminder_{milestone_id}{mode_suffix}.pdf'
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
