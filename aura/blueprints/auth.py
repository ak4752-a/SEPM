import hashlib
import hmac
import os
import re
import secrets
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..extensions import db
from ..models import User

auth_bp = Blueprint('auth', __name__)

_PBKDF2_ITERATIONS = 260000
_USERNAME_RE = re.compile(r'^[A-Za-z0-9_.-]{3,80}$')


def _hash_password(password, salt, iterations):
    """Hash password using PBKDF2-HMAC-SHA256 (iterations>1) or plain SHA-256 (iterations==1)."""
    if iterations > 1:
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations).hex()
    return hashlib.sha256((salt + password).encode()).hexdigest()


def _verify_password(password, user):
    """Constant-time password verification."""
    expected = _hash_password(password, user.salt, user.password_iterations)
    return hmac.compare_digest(expected, user.password_hash)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        errors = []
        if not username:
            errors.append('Username is required.')
        elif not _USERNAME_RE.match(username):
            errors.append('Username must be 3–80 characters (letters, digits, _, ., -).')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if not errors and User.query.filter_by(username=username).first():
            errors.append('Username already taken.')
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html', username=username)
        salt = secrets.token_hex(16)
        password_hash = _hash_password(password, salt, _PBKDF2_ITERATIONS)
        user = User(username=username, password_hash=password_hash, salt=salt,
                    password_iterations=_PBKDF2_ITERATIONS)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', username='')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and _verify_password(password, user):
            session['user_id'] = user.id
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard.index'))
        flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    flash('Logged out.', 'info')
    return redirect(url_for('auth.login'))
