from flask import Blueprint, render_template, session
from ..extensions import db
from ..models import Contract, Milestone, Payment
from .auth import login_required
from ..utils.money import format_amount

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    user_id = session['user_id']

    contracts = Contract.query.filter_by(user_id=user_id).order_by(Contract.created_at.desc()).all()

    # Compute totals grouped by currency
    currency_totals = {}  # currency -> {received, pending, overdue}

    contract_breakdown = []
    for c in contracts:
        cur = c.currency or 'INR'
        if cur not in currency_totals:
            currency_totals[cur] = {'received': 0.0, 'pending': 0.0, 'overdue': 0.0}
        c_received = 0.0
        c_pending = 0.0
        c_overdue = 0.0
        for m in c.milestones:
            if m.payment:
                c_received += m.payment.amount_received
                currency_totals[cur]['received'] += m.payment.amount_received
            elif m.invoice_eligible:
                c_pending += m.payment_amount
                currency_totals[cur]['pending'] += m.payment_amount
                if m.is_overdue:
                    c_overdue += m.payment_amount
                    currency_totals[cur]['overdue'] += m.payment_amount
        contract_breakdown.append({
            'contract': c,
            'received': c_received,
            'pending': c_pending,
            'overdue': c_overdue,
            'currency': cur,
        })

    # Build formatted currency summary list
    currency_summary = []
    for cur, totals in sorted(currency_totals.items()):
        currency_summary.append({
            'currency': cur,
            'received': format_amount(totals['received'], cur),
            'pending': format_amount(totals['pending'], cur),
            'overdue': format_amount(totals['overdue'], cur),
        })

    return render_template('dashboard/index.html',
        currency_summary=currency_summary,
        contract_breakdown=contract_breakdown,
    )
