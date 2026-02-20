from flask import Flask
from .extensions import db
from config import config_map
from .cli import register_cli

def create_app(config_name='default'):
    app = Flask(__name__)
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

    return app
