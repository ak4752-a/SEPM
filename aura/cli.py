import click
import hashlib
import os
import secrets
from flask.cli import AppGroup
from .extensions import db
from .models import User

aura_cli = AppGroup('aura')

_PBKDF2_ITERATIONS = 260000


def _hash_password(password, salt, iterations):
    if iterations > 1:
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations).hex()
    return hashlib.sha256((salt + password).encode()).hexdigest()


@aura_cli.command('init-user')
@click.argument('username')
@click.password_option()
def init_user(username, password):
    """Create an application user (multi-user environment)."""
    from flask import current_app
    with current_app.app_context():
        if User.query.filter_by(username=username).first():
            click.echo(f'User "{username}" already exists.')
            return
        salt = secrets.token_hex(16)
        password_hash = _hash_password(password, salt, _PBKDF2_ITERATIONS)
        user = User(username=username, password_hash=password_hash, salt=salt,
                    password_iterations=_PBKDF2_ITERATIONS)
        db.session.add(user)
        db.session.commit()
        click.echo(f'User "{username}" created successfully.')

def register_cli(app):
    app.cli.add_command(aura_cli)
