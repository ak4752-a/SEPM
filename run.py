import os
from aura import create_app

# Render / Gunicorn entry point
app = create_app(os.environ.get("FLASK_ENV", "production"))
