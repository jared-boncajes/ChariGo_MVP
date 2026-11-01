from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import IntegrityError
from common import commit, email, record, require_role, text
from models import db, Organization, User

bp = Blueprint("auth", __name__)


def home_for(user):
    return {
        "charity_goer": "goer.home",
        "charity_organization": "organization.dashboard",
        "administrator": "admin.dashboard",
    }[user.role]


@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for(home_for(g.user)))
    if request.method == "POST":
        user = db.session.scalar(
            db.select(User).where(
                User.email == request.form.get("email", "").strip().lower()
            )
        )
        if (
            user
            and check_password_hash(
                user.password_hash, request.form.get("password", "")
            )
            and user.account_status == "active"
        ):
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for(home_for(user)))
        flash("Incorrect email or password, or this account is inactive.", "error")
    return render_template("auth.html", mode="login", title="Log in")


@bp.route("/register/role")
def choose_role():
    return render_template("role.html", title="Choose your role")


@bp.route("/register", methods=["GET", "POST"])
def register():
    role = request.values.get("role", "charity_goer")
    if role not in ["charity_goer", "charity_organization"]:
        abort(400, "Choose Charity Goer or Organization.")
    if g.user:
        return redirect(url_for(home_for(g.user)))
    if request.method == "POST":
        try:
            name = text("name", "Full name", 2, 100)
            address = email(request.form.get("email", ""))
            password = request.form.get("password", "")
            if not 8 <= len(password) <= 128:
                raise ValueError("Use a password between 8 and 128 characters.")
            if password != request.form.get("confirm_password"):
                raise ValueError("Your passwords do not match.")
            if db.session.scalar(db.select(User).where(User.email == address)):
                raise ValueError(
                    "An account with this email already exists. Please log in."
                )
            user = User(
                name=name,
                email=address,
                role=role,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.flush()
            record(
                "User registration",
                "user",
                user.id,
                f'{name} joined as {role.replace("_", " ")}.',
            )
            if role == "charity_organization":
                org = Organization(
                    owner=user, name=name + " Organization", contact_email=address
                )
                db.session.add(org)
                db.session.flush()
                record(
                    "Organization registration",
                    "organization",
                    org.id,
                    "Organization created; awaiting completed profile and verification.",
                )
            commit()
            flash("Account created successfully. Please log in to continue.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("An account with this email already exists. Please log in.", "error")
    return render_template(
        "auth.html", mode="register", role=role, title="Create account"
    )


@bp.post("/logout")
@require_role()
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
