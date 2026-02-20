from flask import Blueprint, render_template, session
from sqlalchemy import func
from ..extensions import db
from ..models import Contract, Milestone, Payment
from .auth import login_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    user_id = session['user_id']

    # Total received: sum of payments for user's milestones
    total_received = db.session.query(func.sum(Payment.amount_received))\
        .join(Milestone, Payment.milestone_id == Milestone.id)\
        .join(Contract, Milestone.contract_id == Contract.id)\
        .filter(Contract.user_id == user_id)\
        .scalar() or 0.0

    # Total pending: invoice_eligible=True and no payment
    paid_milestone_ids = db.session.query(Payment.milestone_id)
    total_pending = db.session.query(func.sum(Milestone.payment_amount))\
        .join(Contract, Milestone.contract_id == Contract.id)\
        .filter(Contract.user_id == user_id)\
        .filter(Milestone.invoice_eligible.is_(True))\
        .filter(Milestone.id.notin_(paid_milestone_ids))\
        .scalar() or 0.0

    # Contracts with breakdown
    contracts = Contract.query.filter_by(user_id=user_id).order_by(Contract.created_at.desc()).all()

    # Compute overdue total using Python (after loading)
    total_overdue = 0.0
    contract_breakdown = []
    for c in contracts:
        c_received = 0.0
        c_pending = 0.0
        c_overdue = 0.0
        for m in c.milestones:
            if m.payment:
                c_received += m.payment.amount_received
            elif m.invoice_eligible:
                c_pending += m.payment_amount
                if m.is_overdue:
                    c_overdue += m.payment_amount
        contract_breakdown.append({
            'contract': c,
            'received': c_received,
            'pending': c_pending,
            'overdue': c_overdue,
        })
        total_overdue += c_overdue

    return render_template('dashboard/index.html',
        total_received=total_received,
        total_pending=total_pending,
        total_overdue=total_overdue,
        contract_breakdown=contract_breakdown,
    )
