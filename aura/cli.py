import click
import hashlib
import os
from flask.cli import AppGroup
from .extensions import db
from .models import User

aura_cli = AppGroup('aura')

@aura_cli.command('init-user')
@click.argument('username')
@click.password_option()
def init_user(username, password):
    """Initialize the single application user."""
    from flask import current_app
    with current_app.app_context():
        if User.query.first():
            click.echo('A user already exists. Delete the database to reinitialize.')
            return
        salt = os.urandom(16).hex()
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        user = User(username=username, password_hash=password_hash, salt=salt)
        db.session.add(user)
        db.session.commit()
        click.echo(f'User "{username}" created successfully.')

def register_cli(app):
    app.cli.add_command(aura_cli)
