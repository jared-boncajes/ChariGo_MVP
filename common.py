import functools
import re
import secrets
from datetime import timedelta, timezone
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path

from flask import abort, current_app, flash, g, redirect, request, url_for
from PIL import Image, UnidentifiedImageError
from models import db, SystemRecord

# Philippine time is UTC+8 all year (no daylight saving), so a fixed offset is
# exact and avoids needing a time-zone database, which Windows does not ship.
MANILA = timezone(timedelta(hours=8), "PHT")

CATEGORIES = {
    "Children": "children",
    "Hunger & Poverty": "hunger",
    "Education": "education",
    "Health": "health",
    "Animal Welfare": "animals",
    "Environment": "environment",
}
PAYMENT_METHODS = ["GCash", "Maya", "Credit / Debit Card", "PayPal", "Others"]


def require_role(*roles):
    def decorate(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            if not g.user:
                return redirect(url_for("auth.login", next=request.path))
            if roles and g.user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorate


def text(name, label, minimum=1, maximum=500):
    value = request.form.get(name, "").strip()
    if not minimum <= len(value) <= maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum} characters.")
    return value


def email(value):
    value = value.strip().lower()
    if len(value) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise ValueError("Enter a valid email address.")
    return value


def money(value):
    try:
        amount = Decimal(value)
        if (
            not amount.is_finite()
            or amount < 1
            or amount > 10_000_000
            or amount != amount.quantize(Decimal(".01"))
        ):
            raise ValueError()
        return int(amount * 100)
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(
            "Enter an amount from ₱1 to ₱10,000,000, with at most two decimal places."
        ) from None


def record(action, target_type, target_id, description):
    db.session.add(
        SystemRecord(
            actor_user_id=g.user.id if g.user else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            description=description[:1000],
        )
    )


def commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def image_upload(field):
    upload = request.files.get(field)
    if not upload or not upload.filename:
        return None
    suffix = Path(upload.filename).suffix.lower()
    data = upload.read(3 * 1024 * 1024 + 1)
    if suffix not in {".jpg", ".jpeg", ".png"} or len(data) > 3 * 1024 * 1024:
        raise ValueError("Choose a JPG or PNG image no larger than 3 MB.")
    try:
        with Image.open(BytesIO(data)) as im:
            if im.format not in {"PNG", "JPEG"} or im.width * im.height > 25_000_000:
                raise ValueError("Choose a valid JPG or PNG image under 25 megapixels.")
            im.load()
            im = im.convert("RGB")
            im.thumbnail((1800, 1800))
            name = secrets.token_hex(20) + ".jpg"
            im.save(
                Path(current_app.config["UPLOAD_FOLDER"]) / name, "JPEG", quality=90
            )
            return "upload:" + name
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValueError(
            "This image could not be read. Choose a valid JPG or PNG."
        ) from None


def portfolio_upload():
    upload = request.files.get("portfolio_file")
    if not upload or not upload.filename:
        return None
    data = upload.read(10 * 1024 * 1024 + 1)
    if (
        Path(upload.filename).suffix.lower() != ".pdf"
        or not data.startswith(b"%PDF-")
        or len(data) > 10 * 1024 * 1024
    ):
        raise ValueError("Choose a PDF portfolio no larger than 10 MB.")
    name = secrets.token_hex(20) + ".pdf"
    (Path(current_app.config["PRIVATE_FOLDER"]) / name).write_bytes(data)
    return name


def owned_fundraiser(fundraiser):
    if fundraiser.organization.user_id != g.user.id:
        abort(403)
    return fundraiser


def verified_organization():
    org = g.user.organization
    if not org or not org.public:
        flash("Your organization must be verified before managing campaigns.", "error")
        return False
    return True
