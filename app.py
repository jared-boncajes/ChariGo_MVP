import os
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import click
from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from models import db, User


@event.listens_for(Engine, "connect")
def sqlite_foreign_keys(connection, _):
    if isinstance(connection, sqlite3.Connection):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(exist_ok=True)
    secret_path = Path(app.instance_path) / "session.key"
    if not os.environ.get("SECRET_KEY") and not secret_path.exists():
        secret_path.write_text(secrets.token_hex(32))
        secret_path.chmod(0o600)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secret_path.read_text().strip(),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///charigo.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=14 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
        UPLOAD_FOLDER=str(Path(app.instance_path) / "uploads"),
        PRIVATE_FOLDER=str(Path(app.instance_path) / "portfolios"),
        CSRF_ENABLED=True,
    )
    if test_config:
        app.config.update(test_config)
    for key in ["UPLOAD_FOLDER", "PRIVATE_FOLDER"]:
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)
    db.init_app(app)

    @app.before_request
    def load_user_and_protect_forms():
        g.user = (
            db.session.get(User, session["user_id"]) if session.get("user_id") else None
        )
        if g.user and g.user.account_status != "active":
            session.clear()
            g.user = None
            flash(
                "Your account is inactive. Contact the administrator for assistance.",
                "error",
            )
            if request.endpoint != "auth.login":
                return redirect(url_for("auth.login"))
        if request.method == "POST" and app.config["CSRF_ENABLED"]:
            supplied = request.form.get("csrf_token", "")
            expected = session.get("csrf_token", "")
            if not expected or not secrets.compare_digest(supplied, expected):
                abort(400, "Your form expired. Reload the page and try again.")
        session.setdefault("csrf_token", secrets.token_urlsafe(32))

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        if g.get("user") or request.endpoint in {"auth.login", "auth.register"}:
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.context_processor
    def template_helpers():
        from common import CATEGORIES

        def image_url(name):
            if name and name.startswith("upload:"):
                return url_for("uploaded_image", name=name[7:])
            return url_for("static", filename="images/" + (name or "logo.png"))

        return dict(
            current_user=g.user,
            csrf_token=lambda: session.get("csrf_token", ""),
            image_url=image_url,
            categories=CATEGORIES,
        )

    @app.template_filter("peso")
    def peso(cents):
        return f"₱{cents / 100:,.2f}".removesuffix(".00")

    @app.template_filter("localdate")
    def localdate(value):
        if isinstance(value, datetime):
            from datetime import timezone

            value = value.replace(tzinfo=timezone.utc).astimezone(
                ZoneInfo("Asia/Manila")
            )
        return value.strftime("%b %d, %Y")

    @app.template_filter("localtime")
    def localtime(value):
        from datetime import timezone

        value = value.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Asia/Manila"))
        return value.strftime("%b %d, %Y · %I:%M %p PHT")

    @app.route("/uploads/<name>")
    def uploaded_image(name):
        return send_from_directory(app.config["UPLOAD_FOLDER"], name)

    @app.route("/health")
    def health():
        db.session.execute(db.text("SELECT 1"))
        return {"status": "ok"}

    for code in [400, 403, 404, 409, 413]:
        app.register_error_handler(
            code, lambda error: (render_template("error.html", error=error), error.code)
        )

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        app.logger.exception("Database operation failed")
        return (
            render_template(
                "error.html",
                error=type(
                    "Message",
                    (),
                    {
                        "code": 503,
                        "description": "We could not save your changes. Please try again.",
                    },
                )(),
            ),
            503,
        )

    from routes.auth import bp as auth
    from routes.goer import bp as goer
    from routes.organization import bp as organization
    from routes.admin import bp as admin

    for bp in [auth, goer, organization, admin]:
        app.register_blueprint(bp)

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        click.echo("Database initialized.")

    @app.cli.command("seed")
    def seed_command():
        from seed import seed_database

        db.create_all()
        seed_database()
        click.echo("Demo data is ready. Existing records preserved.")

    @app.cli.command("reset-db")
    @click.confirmation_option(prompt="Delete all local data and restore the demo?")
    def reset_db():
        from seed import seed_database

        db.drop_all()
        db.create_all()
        seed_database()
        click.echo("Demo database reset.")

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
    )
