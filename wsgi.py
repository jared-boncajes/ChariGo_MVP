"""Production entry point: `gunicorn wsgi:app` (see README, "Deploy online")."""

from app import create_app

app = create_app()
