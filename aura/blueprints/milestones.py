from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..extensions import db
from ..models import Contract, Milestone, Payment
from .auth import login_required

milestones_bp = Blueprint('milestones', __name__)


def _validate_milestone_form(form):
    """Validate and parse milestone form fields. Returns (errors, name, planned_delivery_date, payment_amount)."""
    name = form.get('name', '').strip()
    planned_delivery_date_str = form.get('planned_delivery_date', '')
    payment_amount_str = form.get('payment_amount', '')
    errors = []
    if not name:
        errors.append('Milestone name is required.')
    try:
        planned_delivery_date = date.fromisoformat(planned_delivery_date_str)
    except ValueError:
        errors.append('Invalid planned delivery date.')
        planned_delivery_date = None
    try:
        payment_amount = float(payment_amount_str)
        if payment_amount <= 0:
            errors.append('Payment amount must be positive.')
    except ValueError:
        errors.append('Payment amount must be a number.')
        payment_amount = None
    return errors, name, planned_delivery_date, payment_amount


@milestones_bp.route('/contracts/<int:contract_id>/milestones/new', methods=['GET', 'POST'])
@login_required
def new_milestone(contract_id):
    contract = Contract.query.filter_by(id=contract_id, user_id=session['user_id']).first_or_404()
    if request.method == 'POST':
        errors, name, planned_delivery_date, payment_amount = _validate_milestone_form(request.form)
        if errors:
            for e in errors:
                flash(e, 'danger')
        else:
            milestone = Milestone(
                contract_id=contract.id,
                name=name,
                planned_delivery_date=planned_delivery_date,
                payment_amount=payment_amount,
            )
            db.session.add(milestone)
            db.session.commit()
            flash('Milestone added.', 'success')
            return redirect(url_for('contracts.view_contract', contract_id=contract.id))
    return render_template('milestones/form.html', contract=contract, milestone=None)

@milestones_bp.route('/milestones/<int:milestone_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_milestone(milestone_id):
    milestone = Milestone.query.join(Contract).filter(
        Milestone.id == milestone_id,
        Contract.user_id == session['user_id']
    ).first_or_404()
    contract = milestone.contract
    if request.method == 'POST':
        errors, name, planned_delivery_date, payment_amount = _validate_milestone_form(request.form)
        if errors:
            for e in errors:
                flash(e, 'danger')
        else:
            milestone.name = name
            milestone.planned_delivery_date = planned_delivery_date
            milestone.payment_amount = payment_amount
            db.session.commit()
            flash('Milestone updated.', 'success')
            return redirect(url_for('contracts.view_contract', contract_id=contract.id))
    return render_template('milestones/form.html', contract=contract, milestone=milestone)

@milestones_bp.route('/milestones/<int:milestone_id>/deliver', methods=['POST'])
@login_required
def deliver_milestone(milestone_id):
    milestone = Milestone.query.join(Contract).filter(
        Milestone.id == milestone_id,
        Contract.user_id == session['user_id']
    ).first_or_404()
    actual_delivery_date_str = request.form.get('actual_delivery_date', '')
    try:
        actual_delivery_date = date.fromisoformat(actual_delivery_date_str)
    except ValueError:
        flash('Invalid delivery date.', 'danger')
        return redirect(url_for('contracts.view_contract', contract_id=milestone.contract_id))
    milestone.actual_delivery_date = actual_delivery_date
    milestone.invoice_eligible = True
    db.session.commit()
    flash('Delivery recorded. Milestone is now invoice eligible.', 'success')
    return redirect(url_for('contracts.view_contract', contract_id=milestone.contract_id))

@milestones_bp.route('/milestones/<int:milestone_id>/pay', methods=['POST'])
@login_required
def record_payment(milestone_id):
    milestone = Milestone.query.join(Contract).filter(
        Milestone.id == milestone_id,
        Contract.user_id == session['user_id']
    ).first_or_404()
    received_date_str = request.form.get('received_date', '')
    amount_received_str = request.form.get('amount_received', str(milestone.payment_amount))
    try:
        received_date = date.fromisoformat(received_date_str)
    except ValueError:
        flash('Invalid payment date.', 'danger')
        return redirect(url_for('contracts.view_contract', contract_id=milestone.contract_id))
    try:
        amount_received = float(amount_received_str)
    except ValueError:
        flash('Invalid payment amount.', 'danger')
        return redirect(url_for('contracts.view_contract', contract_id=milestone.contract_id))
    if milestone.payment:
        flash('Payment already recorded for this milestone.', 'warning')
        return redirect(url_for('contracts.view_contract', contract_id=milestone.contract_id))
    payment = Payment(
        milestone_id=milestone.id,
        received_date=received_date,
        amount_received=amount_received,
    )
    db.session.add(payment)
    db.session.commit()
    flash('Payment recorded.', 'success')
    return redirect(url_for('contracts.view_contract', contract_id=milestone.contract_id))

@milestones_bp.route('/milestones/<int:milestone_id>/delete', methods=['POST'])
@login_required
def delete_milestone(milestone_id):
    milestone = Milestone.query.join(Contract).filter(
        Milestone.id == milestone_id,
        Contract.user_id == session['user_id']
    ).first_or_404()
    contract_id = milestone.contract_id
    db.session.delete(milestone)
    db.session.commit()
    flash('Milestone deleted.', 'info')
    return redirect(url_for('contracts.view_contract', contract_id=contract_id))
