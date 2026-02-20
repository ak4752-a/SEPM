import hashlib
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..models import User

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user:
            password_hash = hashlib.sha256((user.salt + password).encode()).hexdigest()
            if password_hash == user.password_hash:
                session['user_id'] = user.id
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.', 'info')
    return redirect(url_for('auth.login'))
