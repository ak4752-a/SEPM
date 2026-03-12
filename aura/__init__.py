import logging
from flask import Flask
from .extensions import db
from config import config_map
from .cli import register_cli
import os
from sqlalchemy.exc import SQLAlchemyError

_log = logging.getLogger(__name__)


def create_app(config_name='default'):
    # IMPORTANT: enable instance folder
    app = Flask(__name__, instance_relative_config=True)

    # VERY IMPORTANT for Render + SQLite
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_object(config_map[config_name])

    # Enable Secure cookies at runtime if the HTTPS env var is set to "true".
    # This allows the config class to remain static while the setting is resolved
    # after the process env is fully populated (important for Render deployments).
    if os.environ.get('HTTPS', '').lower() == 'true':
        app.config['SESSION_COOKIE_SECURE'] = True

    db.init_app(app)

    from .blueprints.auth import auth_bp
    from .blueprints.contracts import contracts_bp
    from .blueprints.milestones import milestones_bp
    from .blueprints.dashboard import dashboard_bp
    from .blueprints.pdf_bp import pdf_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(milestones_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(pdf_bp)

    register_cli(app)

    # Register template globals
    from .utils.money import format_amount
    app.jinja_env.globals['format_amount'] = format_amount

    # Only initialise the database schema and bootstrap an admin user when
    # explicitly requested via INIT_DB=true.  This prevents crash-loops on
    # Render (and other PaaS platforms) where Postgres may be temporarily
    # unreachable at boot time: Gunicorn must bind to $PORT before the
    # platform's health-check passes, and any uncaught exception raised here
    # will kill the process before it can listen on that port.
    #
    # Usage:
    #   • First deploy / schema migration: set INIT_DB=true in Render
    #     environment, deploy once, then remove / set back to false.
    #   • Normal deploys: leave INIT_DB unset or INIT_DB=false — the app
    #     starts cleanly even if Postgres is temporarily unavailable.
    if os.environ.get('INIT_DB', '').lower() == 'true':
        with app.app_context():
            try:
                db.create_all()

                # Auto-create admin user in fresh deployments
                from .models import User
                from sqlalchemy import select

                admin_username = os.environ.get("ADMIN_USERNAME")
                admin_password = os.environ.get("ADMIN_PASSWORD")

                if admin_username and admin_password:
                    existing = db.session.execute(
                        select(User).where(User.username == admin_username)
                    ).scalar_one_or_none()

                    if not existing:
                        import secrets
                        from .blueprints.auth import _hash_password, _PBKDF2_ITERATIONS
                        salt = secrets.token_hex(16)
                        hashed = _hash_password(admin_password, salt, _PBKDF2_ITERATIONS)
                        admin = User(username=admin_username, password_hash=hashed, salt=salt,
                                     password_iterations=_PBKDF2_ITERATIONS)
                        db.session.add(admin)
                        db.session.commit()
                        _log.info("Admin user '%s' created.", admin_username)
                    else:
                        _log.info("Admin user '%s' already exists; skipping.", admin_username)

                _log.info("DB initialisation (INIT_DB=true) completed successfully.")
            except SQLAlchemyError as exc:
                _log.error(
                    "DB initialisation failed (INIT_DB=true): %s — "
                    "the app will continue to start but tables/admin may be missing.",
                    exc,
                )

    return app
