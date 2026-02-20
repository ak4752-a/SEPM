from flask import Flask
from .extensions import db
from config import config_map
from .cli import register_cli
import os

def create_app(config_name='default'):
    # IMPORTANT: enable instance folder
    app = Flask(__name__, instance_relative_config=True)

    # VERY IMPORTANT for Render + SQLite
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_object(config_map[config_name])

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

    with app.app_context():
        db.create_all()

        # Auto-create admin user in fresh deployments
        from .models import User
        import hashlib
        from sqlalchemy import select

        admin_username = os.environ.get("ADMIN_USERNAME")
        admin_password = os.environ.get("ADMIN_PASSWORD")

        if admin_username and admin_password:
            existing = db.session.execute(
                select(User).where(User.username == admin_username)
            ).scalar_one_or_none()

            if not existing:
                import secrets
                salt = secrets.token_hex(16)
                hashed = hashlib.sha256((salt + admin_password).encode()).hexdigest()
                admin = User(username=admin_username, password_hash=hashed, salt=salt)
                db.session.add(admin)
                db.session.commit()

    return app
