import csv
import io
import secrets
from datetime import date, datetime, timedelta, timezone

from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import IntegrityError
from common import (
    CATEGORIES,
    MANILA,
    PAYMENT_METHODS,
    commit,
    email,
    image_upload,
    money,
    record,
    require_role,
    text,
)
from models import (
    db,
    Donation,
    Fundraiser,
    Organization,
    SavedCharity,
    User,
    VolunteerApplication,
    VolunteerOpportunity,
)

bp = Blueprint("goer", __name__)


def accessible_fundraiser(fid):
    f = db.get_or_404(Fundraiser, fid)
    privileged = g.user and (
        g.user.role == "administrator" or f.organization.user_id == g.user.id
    )
    if not f.public and not privileged:
        abort(404)
    return f


@bp.route("/")
def welcome():
    if g.user:
        from routes.auth import home_for

        return redirect(url_for(home_for(g.user)))
    return render_template("welcome.html", title="Welcome to ChariGo")


@bp.route("/home")
def home():
    campaigns = [
        f
        for f in db.session.scalars(db.select(Fundraiser).order_by(Fundraiser.id)).all()
        if f.accepting
    ]
    return render_template(
        "home.html",
        title="Home",
        active="home",
        campaigns=campaigns,
        organizations=[
            o for o in db.session.scalars(db.select(Organization)).all() if o.public
        ],
    )


@bp.route("/causes")
def causes():
    q = request.args.get("q", "").strip()[:150]
    category = request.args.get("category", "")
    organization_id = request.args.get("organization", type=int)
    campaigns = [
        f
        for f in db.session.scalars(
            db.select(Fundraiser).order_by(Fundraiser.created_at.desc())
        ).all()
        if f.accepting
        and (
            not q
            or q.casefold()
            in (
                f.title
                + " "
                + f.description
                + " "
                + f.organization.name
                + " "
                + f.location
            ).casefold()
        )
        and (not category or f.category == category)
        and (not organization_id or f.organization_id == organization_id)
        and (
            not request.args.get("volunteer")
            or (f.opportunity and f.opportunity.available)
        )
    ]
    orgs = [o for o in db.session.scalars(db.select(Organization)).all() if o.public]
    return render_template(
        "causes.html",
        title="Explore Charities",
        active="explore",
        campaigns=campaigns,
        q=q,
        selected_category=category,
        organizations=orgs,
        organization_id=organization_id,
    )


@bp.route("/fundraisers/<int:fid>")
def fundraiser(fid):
    f = accessible_fundraiser(fid)
    return render_template(
        "fundraiser.html", title=f.title, fundraiser=f, active="explore"
    )


@bp.route("/organizations/<int:oid>")
def organization(oid):
    org = db.get_or_404(Organization, oid)
    if not org.public and not (
        g.user and (g.user.role == "administrator" or org.user_id == g.user.id)
    ):
        abort(404)
    campaigns = [f for f in org.fundraisers if f.accepting]
    saved = g.user and db.session.scalar(
        db.select(SavedCharity).where(
            SavedCharity.user_id == g.user.id, SavedCharity.organization_id == oid
        )
    )
    tab = request.args.get("tab", "about")
    if tab not in ["about", "campaigns", "contact"]:
        tab = "about"
    return render_template(
        "organization_public.html",
        title=org.name,
        org=org,
        campaigns=campaigns,
        saved=saved,
        tab=tab,
        active="explore",
    )


@bp.post("/organizations/<int:oid>/save")
@require_role("charity_goer")
def save_organization(oid):
    org = db.get_or_404(Organization, oid)
    if not org.public:
        abort(404)
    saved = db.session.scalar(
        db.select(SavedCharity).where(
            SavedCharity.user_id == g.user.id, SavedCharity.organization_id == oid
        )
    )
    if saved:
        db.session.delete(saved)
    else:
        db.session.add(SavedCharity(user_id=g.user.id, organization_id=oid))
    try:
        commit()
    except IntegrityError:
        db.session.rollback()
    flash("Your saved charities have been updated.", "success")
    return redirect(url_for("goer.organization", oid=oid))


@bp.route("/fundraisers/<int:fid>/donate", methods=["GET", "POST"])
@require_role("charity_goer")
def donate(fid):
    f = accessible_fundraiser(fid)
    if not f.accepting:
        abort(409, "This fundraiser is not accepting donations.")
    if request.method == "POST":
        try:
            amount = money(request.form.get("amount", ""))
            method = request.form.get("method")
            if method not in PAYMENT_METHODS:
                raise ValueError("Choose a payment method.")
            session["donation_review"] = dict(
                fid=fid,
                amount=amount,
                method=method,
                anonymous=request.form.get("anonymous") == "on",
                token=secrets.token_urlsafe(24),
            )
            return redirect(url_for("goer.donation_review"))
        except ValueError as error:
            flash(str(error), "error")
    return render_template(
        "donate.html",
        title="Make a Donation",
        fundraiser=f,
        methods=PAYMENT_METHODS,
        active="explore",
    )


@bp.route("/donation/review", methods=["GET", "POST"])
@require_role("charity_goer")
def donation_review():
    pending = session.get("donation_review")
    if not pending:
        flash("Choose a donation amount to continue.", "error")
        return redirect(url_for("goer.causes"))
    f = accessible_fundraiser(pending["fid"])
    if not f.accepting:
        abort(409, "This fundraiser is no longer accepting donations.")
    if request.method == "POST":
        if request.form.get("review_token") != pending["token"]:
            abort(400, "This review has expired. Please start your donation again.")
        existing = db.session.scalar(
            db.select(Donation).where(Donation.submission_token == pending["token"])
        )
        if existing:
            return redirect(url_for("goer.receipt", did=existing.id))
        donation = Donation(
            user_id=g.user.id,
            fundraiser_id=f.id,
            amount_cents=pending["amount"],
            payment_method=pending["method"],
            anonymous=pending["anonymous"],
            submission_token=pending["token"],
        )
        db.session.add(donation)
        try:
            db.session.flush()
            record(
                "Simulated donation",
                "donation",
                donation.id,
                "A simulated donation was recorded.",
            )
            commit()
        except IntegrityError:
            db.session.rollback()
            donation = db.session.scalar(
                db.select(Donation).where(Donation.submission_token == pending["token"])
            )
            if not donation:
                abort(409, "Your donation could not be saved. Please try again.")
        session.pop("donation_review", None)
        return redirect(url_for("goer.receipt", did=donation.id))
    return render_template(
        "review.html",
        title="Review Donation",
        kind="donation",
        pending=pending,
        fundraiser=f,
        active="explore",
    )


@bp.route("/donations/<int:did>")
@require_role("charity_goer")
def receipt(did):
    donation = db.get_or_404(Donation, did)
    if donation.user_id != g.user.id:
        abort(403)
    return render_template(
        "success.html",
        title="Donation confirmed",
        kind="donation",
        donation=donation,
        active="profile",
    )


@bp.route("/opportunities/<int:oid>", methods=["GET", "POST"])
@require_role("charity_goer")
def opportunity(oid):
    op = db.get_or_404(VolunteerOpportunity, oid)
    accessible_fundraiser(op.fundraiser_id)
    if op.status != "active":
        abort(404)
    existing = db.session.scalar(
        db.select(VolunteerApplication).where(
            VolunteerApplication.user_id == g.user.id,
            VolunteerApplication.opportunity_id == oid,
        )
    )
    if request.method == "POST":
        if existing:
            flash(
                "You have already applied. Your current status is shown in volunteer history.",
                "error",
            )
            return redirect(url_for("goer.volunteer_history"))
        if not op.available or op.accepted_count >= op.slots:
            abort(409, "This volunteer opportunity is closed or full.")
        try:
            message = text("message", "Application message", 10, 2000)
            session["volunteer_review"] = dict(
                oid=oid, message=message, token=secrets.token_urlsafe(24)
            )
            return redirect(url_for("goer.volunteer_review"))
        except ValueError as error:
            flash(str(error), "error")
    return render_template(
        "opportunity.html",
        title=op.title,
        opportunity=op,
        existing=existing,
        active="explore",
    )


@bp.route("/volunteer/review", methods=["GET", "POST"])
@require_role("charity_goer")
def volunteer_review():
    pending = session.get("volunteer_review")
    if not pending:
        return redirect(url_for("goer.volunteer_history"))
    op = db.get_or_404(VolunteerOpportunity, pending["oid"])
    if not op.available or op.accepted_count >= op.slots:
        abort(409, "This volunteer opportunity is closed or full.")
    if request.method == "POST":
        if request.form.get("review_token") != pending["token"]:
            abort(400, "This review has expired. Please start your application again.")
        application = db.session.scalar(
            db.select(VolunteerApplication).where(
                VolunteerApplication.user_id == g.user.id,
                VolunteerApplication.opportunity_id == op.id,
            )
        )
        if application:
            return redirect(url_for("goer.application_success", aid=application.id))
        application = VolunteerApplication(
            user_id=g.user.id, opportunity_id=op.id, message=pending["message"]
        )
        db.session.add(application)
        try:
            db.session.flush()
            record(
                "Volunteer application",
                "application",
                application.id,
                "A volunteer application was submitted for review.",
            )
            commit()
        except IntegrityError:
            db.session.rollback()
            flash("You have already applied to this opportunity.", "error")
            return redirect(url_for("goer.volunteer_history"))
        session.pop("volunteer_review", None)
        return redirect(url_for("goer.application_success", aid=application.id))
    return render_template(
        "review.html",
        title="Review Application",
        kind="volunteer",
        pending=pending,
        opportunity=op,
        fundraiser=op.fundraiser,
        active="explore",
    )


@bp.route("/applications/<int:aid>/success")
@require_role("charity_goer")
def application_success(aid):
    application = db.get_or_404(VolunteerApplication, aid)
    if application.user_id != g.user.id:
        abort(403)
    return render_template(
        "success.html",
        title="Application submitted",
        kind="volunteer",
        application=application,
        active="profile",
    )


PERIODS = {"30": "Last 30 days", "90": "Last 90 days", "365": "Last 12 months"}


def local(moment):
    """Stored timestamps are UTC; people read them in Philippine time."""
    return moment.replace(tzinfo=timezone.utc).astimezone(MANILA)


def history_filters():
    q = request.args.get("q", "").strip()[:100]
    period = request.args.get("period", "")
    if period not in PERIODS:
        period = ""
    since = (
        datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=int(period))
        if period
        else None
    )
    return q, period, since


def by_month(items):
    groups = []
    for item in items:
        label = local(item.created_at).strftime("%B %Y")
        if not groups or groups[-1][0] != label:
            groups.append((label, []))
        groups[-1][1].append(item)
    return groups


def csv_download(filename, header, rows):
    def safe(value):
        # Spreadsheet programs run cells that begin with these as formulas.
        value = str(value)
        return "'" + value if value[:1] in "=+-@" else value

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows([safe(cell) for cell in row] for row in rows)
    return Response(
        "﻿" + buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def filtered_donations():
    q, period, since = history_filters()
    sort = request.args.get("sort", "newest")
    if sort not in {"newest", "oldest", "highest"}:
        sort = "newest"
    everything = db.session.scalars(
        db.select(Donation)
        .where(Donation.user_id == g.user.id)
        .order_by(Donation.created_at.desc(), Donation.id.desc())
    ).all()
    items = [
        d
        for d in everything
        if (not since or d.created_at.replace(tzinfo=None) >= since)
        and (
            not q
            or q.casefold()
            in " ".join(
                [
                    d.fundraiser.title,
                    d.fundraiser.organization.name,
                    d.reference,
                    d.payment_method,
                ]
            ).casefold()
        )
    ]
    if sort == "oldest":
        items.reverse()
    elif sort == "highest":
        items.sort(key=lambda d: d.amount_cents, reverse=True)
    return everything, items, dict(q=q, period=period, sort=sort)


def filtered_applications():
    q, period, since = history_filters()
    status = request.args.get("status", "")
    if status not in {"pending", "accepted", "rejected"}:
        status = ""
    everything = db.session.scalars(
        db.select(VolunteerApplication)
        .where(VolunteerApplication.user_id == g.user.id)
        .order_by(VolunteerApplication.created_at.desc(), VolunteerApplication.id.desc())
    ).all()
    items = [
        a
        for a in everything
        if (not status or a.status == status)
        and (not since or a.created_at.replace(tzinfo=None) >= since)
        and (
            not q
            or q.casefold()
            in " ".join(
                [
                    a.opportunity.title,
                    a.opportunity.fundraiser.organization.name,
                    a.opportunity.location,
                ]
            ).casefold()
        )
    ]
    return everything, items, dict(q=q, period=period, status=status)


@bp.route("/history")
@require_role("charity_goer")
def history():
    return redirect(url_for("goer.donation_history"))


@bp.route("/history/donations")
@require_role("charity_goer")
def donation_history():
    everything, items, filters = filtered_donations()
    return render_template(
        "history.html",
        title="Donation History",
        kind="donation",
        items=items,
        groups=by_month(items) if filters["sort"] != "highest" else [("", items)],
        everything=everything,
        filters=filters,
        filtered=bool(filters["q"] or filters["period"]),
        periods=PERIODS,
        total=sum(d.amount_cents for d in everything),
        shown_total=sum(d.amount_cents for d in items),
        charities=len({d.fundraiser.organization_id for d in everything}),
        active="profile",
    )


@bp.route("/history/donations.csv")
@require_role("charity_goer")
def donation_history_csv():
    _, items, _ = filtered_donations()
    return csv_download(
        "charigo-donations.csv",
        ["Date", "Reference", "Organization", "Fundraiser", "Amount (PHP)", "Method", "Anonymous"],
        [
            [
                local(d.created_at).strftime("%Y-%m-%d %H:%M"),
                d.reference,
                d.fundraiser.organization.name,
                d.fundraiser.title,
                f"{d.amount_cents / 100:.2f}",
                d.payment_method + " (simulated)",
                "Yes" if d.anonymous else "No",
            ]
            for d in items
        ],
    )


@bp.route("/history/volunteering")
@require_role("charity_goer")
def volunteer_history():
    everything, items, filters = filtered_applications()
    return render_template(
        "history.html",
        title="Volunteer History",
        kind="volunteer",
        items=items,
        groups=by_month(items),
        everything=everything,
        filters=filters,
        filtered=bool(filters["q"] or filters["period"] or filters["status"]),
        periods=PERIODS,
        total=sum(a.status == "accepted" for a in everything),
        pending=sum(a.status == "pending" for a in everything),
        today=date.today(),
        active="profile",
    )


@bp.route("/history/volunteering.csv")
@require_role("charity_goer")
def volunteer_history_csv():
    _, items, _ = filtered_applications()
    return csv_download(
        "charigo-volunteering.csv",
        ["Applied", "Opportunity", "Organization", "Event date", "Location", "Status"],
        [
            [
                local(a.created_at).strftime("%Y-%m-%d %H:%M"),
                a.opportunity.title,
                a.opportunity.fundraiser.organization.name,
                a.opportunity.event_date.isoformat(),
                a.opportunity.location,
                a.status.title(),
            ]
            for a in items
        ],
    )


@bp.post("/applications/<int:aid>/withdraw")
@require_role("charity_goer")
def withdraw_application(aid):
    application = db.get_or_404(VolunteerApplication, aid)
    if application.user_id != g.user.id:
        abort(403)
    if application.status != "pending":
        abort(409, "Only a pending application can be withdrawn.")
    title = application.opportunity.title
    record(
        "Application withdrawn",
        "application",
        application.id,
        "A volunteer withdrew a pending application.",
    )
    db.session.delete(application)
    commit()
    flash(f"Your application for {title} was withdrawn.", "success")
    return redirect(url_for("goer.volunteer_history"))


@bp.route("/profile")
@require_role()
def profile():
    recent = []
    if g.user.role == "charity_goer":
        recent = sorted(
            [("donation", d) for d in g.user.donations]
            + [("volunteer", a) for a in g.user.applications],
            key=lambda pair: pair[1].created_at,
            reverse=True,
        )[:3]
    return render_template(
        "profile.html", title="My Profile", active="profile", recent=recent
    )


@bp.route("/profile/edit", methods=["GET", "POST"])
@require_role()
def edit_profile():
    if request.method == "POST":
        try:
            values = {
                key: text(key, label, minimum, maximum)
                for key, label, minimum, maximum in [
                    ("name", "Full name", 2, 100),
                    ("phone", "Phone", 0, 40),
                    ("location", "Location", 0, 150),
                    ("availability", "Availability", 0, 150),
                    ("skills", "Skills", 0, 2000),
                    ("experience", "Experience", 0, 2000),
                ]
            }
            values["email"] = email(request.form.get("email", ""))
            duplicate = db.session.scalar(
                db.select(User).where(
                    User.email == values["email"], User.id != g.user.id
                )
            )
            if duplicate:
                raise ValueError("This email address is already in use.")
            avatar = image_upload("image")
            for key, value in values.items():
                setattr(g.user, key, value)
            if avatar:
                g.user.image = avatar
            record("Profile updated", "user", g.user.id, "Account profile updated.")
            commit()
            flash("Profile updated successfully.", "success")
            return redirect(url_for("goer.profile"))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
        except IntegrityError:
            db.session.rollback()
            flash("This email address is already in use.", "error")
    return render_template("profile_edit.html", title="Edit Profile", active="profile")
