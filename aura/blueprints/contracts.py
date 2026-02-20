from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..extensions import db
from ..models import Contract
from .auth import login_required

contracts_bp = Blueprint('contracts', __name__)

@contracts_bp.route('/contracts')
@login_required
def list_contracts():
    user_id = session['user_id']
    contracts = Contract.query.filter_by(user_id=user_id).order_by(Contract.created_at.desc()).all()
    return render_template('contracts/list.html', contracts=contracts)

@contracts_bp.route('/contracts/new', methods=['GET', 'POST'])
@login_required
def new_contract():
    if request.method == 'POST':
        client_name = request.form.get('client_name', '').strip()
        contract_name = request.form.get('contract_name', '').strip()
        start_date_str = request.form.get('start_date', '')
        total_value_str = request.form.get('total_value', '')
        payment_term_days_str = request.form.get('payment_term_days', '30')
        errors = []
        if not client_name:
            errors.append('Client name is required.')
        if not contract_name:
            errors.append('Contract name is required.')
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            errors.append('Invalid start date.')
            start_date = None
        try:
            total_value = float(total_value_str)
            if total_value <= 0:
                errors.append('Total value must be positive.')
        except ValueError:
            errors.append('Total value must be a number.')
            total_value = None
        try:
            payment_term_days = int(payment_term_days_str)
            if payment_term_days <= 0:
                errors.append('Payment term must be a positive integer.')
        except ValueError:
            errors.append('Payment term must be an integer.')
            payment_term_days = 30
        if errors:
            for e in errors:
                flash(e, 'danger')
        else:
            contract = Contract(
                user_id=session['user_id'],
                client_name=client_name,
                contract_name=contract_name,
                start_date=start_date,
                total_value=total_value,
                payment_term_days=payment_term_days,
            )
            db.session.add(contract)
            db.session.commit()
            flash('Contract created.', 'success')
            return redirect(url_for('contracts.list_contracts'))
    return render_template('contracts/form.html', contract=None)

@contracts_bp.route('/contracts/<int:contract_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contract(contract_id):
    contract = Contract.query.filter_by(id=contract_id, user_id=session['user_id']).first_or_404()
    if request.method == 'POST':
        client_name = request.form.get('client_name', '').strip()
        contract_name = request.form.get('contract_name', '').strip()
        start_date_str = request.form.get('start_date', '')
        total_value_str = request.form.get('total_value', '')
        payment_term_days_str = request.form.get('payment_term_days', '30')
        errors = []
        if not client_name:
            errors.append('Client name is required.')
        if not contract_name:
            errors.append('Contract name is required.')
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            errors.append('Invalid start date.')
            start_date = None
        try:
            total_value = float(total_value_str)
            if total_value <= 0:
                errors.append('Total value must be positive.')
        except ValueError:
            errors.append('Total value must be a number.')
            total_value = None
        try:
            payment_term_days = int(payment_term_days_str)
            if payment_term_days <= 0:
                errors.append('Payment term must be a positive integer.')
        except ValueError:
            errors.append('Payment term must be an integer.')
            payment_term_days = 30
        if errors:
            for e in errors:
                flash(e, 'danger')
        else:
            contract.client_name = client_name
            contract.contract_name = contract_name
            contract.start_date = start_date
            contract.total_value = total_value
            contract.payment_term_days = payment_term_days
            db.session.commit()
            flash('Contract updated.', 'success')
            return redirect(url_for('contracts.view_contract', contract_id=contract.id))
    return render_template('contracts/form.html', contract=contract)

@contracts_bp.route('/contracts/<int:contract_id>/delete', methods=['POST'])
@login_required
def delete_contract(contract_id):
    contract = Contract.query.filter_by(id=contract_id, user_id=session['user_id']).first_or_404()
    db.session.delete(contract)
    db.session.commit()
    flash('Contract deleted.', 'info')
    return redirect(url_for('contracts.list_contracts'))

@contracts_bp.route('/contracts/<int:contract_id>')
@login_required
def view_contract(contract_id):
    contract = Contract.query.filter_by(id=contract_id, user_id=session['user_id']).first_or_404()
    return render_template('contracts/detail.html', contract=contract, today=date.today())
