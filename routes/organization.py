from datetime import date
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from common import (
    CATEGORIES,
    commit,
    email,
    image_upload,
    money,
    owned_fundraiser,
    portfolio_upload,
    record,
    require_role,
    text,
    verified_organization,
)
from models import (
    db,
    Donation,
    Fundraiser,
    Organization,
    VolunteerApplication,
    VolunteerOpportunity,
)

bp = Blueprint("organization", __name__, url_prefix="/organization")


@bp.route("")
@require_role("charity_organization")
def dashboard():
    org = g.user.organization
    return render_template(
        "organization_dashboard.html",
        title="Organization Profile",
        org=org,
        active="profile",
    )


@bp.route("/donations")
@require_role("charity_organization")
def donations():
    """Every donation the organization has received, newest first."""
    org = g.user.organization
    campaigns = sorted(org.fundraisers, key=lambda f: f.title)
    fid = request.args.get("fundraiser", type=int)
    if fid not in {f.id for f in campaigns}:
        fid = None
    query = (
        db.select(Donation)
        .join(Fundraiser)
        .where(Fundraiser.organization_id == org.id)
        .order_by(Donation.created_at.desc(), Donation.id.desc())
    )
    if fid:
        query = query.where(Donation.fundraiser_id == fid)
    items = db.session.scalars(query).all()
    return render_template(
        "organization_donations.html",
        title="Donations Received",
        items=items,
        campaigns=campaigns,
        fundraiser_id=fid,
        total=sum(d.amount_cents for d in items),
        donors=len({d.user_id for d in items}),
        active="profile",
    )


@bp.route("/profile", methods=["GET", "POST"])
@require_role("charity_organization")
def profile():
    org = g.user.organization
    if request.method == "POST":
        try:
            values = {
                key: text(key, label, minimum, maximum)
                for key, label, minimum, maximum in [
                    ("name", "Organization name", 3, 150),
                    ("description", "About your organization", 20, 5000),
                    ("mission", "Mission", 10, 2000),
                    ("portfolio", "Portfolio", 0, 3000),
                    ("phone", "Phone", 0, 40),
                    ("location", "Location", 2, 150),
                ]
            }
            values["contact_email"] = email(request.form.get("contact_email", ""))
            logo = image_upload("logo")
            portfolio = portfolio_upload()
            for key, value in values.items():
                setattr(org, key, value)
            if logo:
                org.logo = logo
            if portfolio:
                org.portfolio_file = portfolio
            if org.verification_status == "rejected":
                org.verification_status = "pending"
                org.rejection_reason = ""
            record(
                "Organization profile updated",
                "organization",
                org.id,
                (
                    "Organization details submitted for administrator review."
                    if org.verification_status == "pending"
                    else "Organization profile updated."
                ),
            )
            commit()
            flash(
                "Organization details saved. "
                + (
                    "Your registration is pending verification."
                    if org.verification_status == "pending"
                    else ""
                ),
                "success",
            )
            return redirect(url_for("organization.dashboard"))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template(
        "organization_form.html",
        title=(
            "Organization Registration"
            if org.verification_status != "verified"
            else "Edit Organization"
        ),
        org=org,
        active="profile",
    )


@bp.route("/<int:oid>/portfolio")
@require_role("administrator", "charity_organization")
def portfolio(oid):
    org = db.get_or_404(Organization, oid)
    if g.user.role != "administrator" and org.user_id != g.user.id:
        abort(403)
    if not org.portfolio_file:
        abort(404)
    return send_from_directory(
        current_app.config["PRIVATE_FOLDER"],
        org.portfolio_file,
        as_attachment=True,
        download_name="organization-portfolio.pdf",
    )


@bp.route("/fundraisers")
@require_role("charity_organization")
def fundraisers():
    past = request.args.get("status") == "past"
    items = [
        f
        for f in g.user.organization.fundraisers
        if (f.status != "active" or f.end_date < date.today()) == past
    ]
    return render_template(
        "organization_fundraisers.html",
        title="Past Fundraisers" if past else "Current Fundraisers",
        campaigns=items,
        past=past,
        active="home",
    )


def fundraiser_values():
    values = {
        key: text(key, label, minimum, maximum)
        for key, label, minimum, maximum in [
            ("title", "Title", 3, 150),
            ("description", "Description", 20, 5000),
            ("impact", "Your donation will help", 10, 500),
            ("location", "Location", 2, 150),
        ]
    }
    values["category"] = request.form.get("category")
    if values["category"] not in CATEGORIES:
        raise ValueError("Choose a valid category.")
    values["goal_cents"] = money(request.form.get("goal", ""))
    try:
        values["start_date"] = date.fromisoformat(request.form.get("start_date", ""))
        values["end_date"] = date.fromisoformat(request.form.get("end_date", ""))
    except ValueError:
        raise ValueError("Enter valid campaign dates.") from None
    if values["end_date"] < values["start_date"]:
        raise ValueError("The end date must be on or after the start date.")
    return values


def opportunity_values(values, fundraiser):
    enabled = request.form.get("volunteers") == "on"
    if not enabled:
        return None
    try:
        slots = int(request.form.get("slots", ""))
        event_date = date.fromisoformat(request.form.get("event_date", ""))
    except ValueError:
        raise ValueError("Enter a valid volunteer date and number of slots.") from None
    if not 1 <= slots <= 10000:
        raise ValueError("Volunteer slots must be between 1 and 10,000.")
    if not values["start_date"] <= event_date <= values["end_date"]:
        raise ValueError("The volunteer date must fall within the campaign dates.")
    if (
        fundraiser
        and fundraiser.opportunity
        and slots < fundraiser.opportunity.accepted_count
    ):
        raise ValueError("Slots cannot be fewer than the volunteers already accepted.")
    return dict(
        title=values["title"],
        description=text("volunteer_description", "What to expect", 10, 3000),
        requirements=text("requirements", "Volunteer requirements", 5, 2000),
        slots=slots,
        event_date=event_date,
        location=values["location"],
    )


@bp.route("/fundraisers/new", methods=["GET", "POST"])
@bp.route("/fundraisers/<int:fid>/edit", methods=["GET", "POST"])
@require_role("charity_organization")
def edit_fundraiser(fid=None):
    if not verified_organization():
        return redirect(url_for("organization.dashboard"))
    f = owned_fundraiser(db.get_or_404(Fundraiser, fid)) if fid else None
    if f and (f.moderation_status != "active" or f.status == "inactive"):
        abort(
            403,
            "An inactive or moderated campaign cannot be edited. Contact the administrator.",
        )
    if request.method == "POST":
        try:
            values = fundraiser_values()
            opportunity_data = opportunity_values(values, f)
            cover = image_upload("cover_image")
            if f is None and values["end_date"] < date.today():
                raise ValueError("A new campaign must end today or later.")
            if f is None:
                f = Fundraiser(organization_id=g.user.organization.id, **values)
                db.session.add(f)
            else:
                for key, value in values.items():
                    setattr(f, key, value)
            if cover:
                f.cover_image = cover
            if opportunity_data:
                if not f.opportunity:
                    f.opportunity = VolunteerOpportunity(**opportunity_data)
                    db.session.add(f.opportunity)
                else:
                    for key, value in opportunity_data.items():
                        setattr(f.opportunity, key, value)
                    # Editing never silently reverses an administrator's moderation decision.
            elif f.opportunity:
                f.opportunity.status = "inactive"
            db.session.flush()
            record(
                "Fundraiser updated" if fid else "Fundraiser created",
                "fundraiser",
                f.id,
                f.title,
            )
            if opportunity_data:
                record(
                    (
                        "Volunteer opportunity updated"
                        if fid
                        else "Volunteer opportunity created"
                    ),
                    "opportunity",
                    f.opportunity.id,
                    f.opportunity.title,
                )
            commit()
            flash(
                (
                    "Fundraiser updated successfully."
                    if fid
                    else "Fundraiser created successfully."
                ),
                "success",
            )
            return redirect(url_for("organization.manage", fid=f.id))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template(
        "fundraiser_form.html",
        title="Edit Fundraiser" if fid else "Create Fundraiser",
        fundraiser=f,
        active="create",
    )


@bp.route("/fundraisers/<int:fid>")
@require_role("charity_organization")
def manage(fid):
    f = owned_fundraiser(db.get_or_404(Fundraiser, fid))
    return render_template(
        "fundraiser.html",
        title="Manage Fundraiser",
        fundraiser=f,
        manage=True,
        active="home",
    )


@bp.route("/fundraisers/<int:fid>/<action>", methods=["GET", "POST"])
@require_role("charity_organization")
def campaign_action(fid, action):
    if action not in ["deactivate", "complete"]:
        abort(404)
    f = owned_fundraiser(db.get_or_404(Fundraiser, fid))
    if not verified_organization():
        return redirect(url_for("organization.dashboard"))
    if f.status == "inactive" and action == "complete":
        abort(
            409,
            "A deactivated fundraiser cannot be reopened by changing its completion status.",
        )
    if request.method == "POST":
        if request.form.get("confirm") != "yes":
            abort(400, "Please confirm this action.")
        f.status = "inactive" if action == "deactivate" else "completed"
        record(
            "Fundraiser " + action,
            "fundraiser",
            f.id,
            "Campaign closed; donations and applications preserved.",
        )
        commit()
        flash(
            "Fundraiser "
            + ("deactivated." if action == "deactivate" else "marked as completed."),
            "success",
        )
        return redirect(url_for("organization.fundraisers", status="past"))
    return render_template(
        "confirm.html",
        title=("Deactivate" if action == "deactivate" else "Complete") + " Fundraiser?",
        target=f.title,
        explanation="This campaign will stop accepting donations and volunteers. All historical records are preserved.",
        cancel_url=url_for("organization.manage", fid=f.id),
        button="Confirm",
        active="home",
    )


@bp.route("/fundraisers/<int:fid>/applications")
@require_role("charity_organization")
def applications(fid):
    f = owned_fundraiser(db.get_or_404(Fundraiser, fid))
    status = request.args.get("status", "")
    items = [
        a
        for a in (f.opportunity.applications if f.opportunity else [])
        if not status or a.status == status
    ]
    return render_template(
        "applications.html",
        title="Volunteer Requests",
        fundraiser=f,
        applications=items,
        status=status,
        active="home",
    )


@bp.route("/applications/<int:aid>")
@require_role("charity_organization")
def applicant(aid):
    application = db.get_or_404(VolunteerApplication, aid)
    owned_fundraiser(application.opportunity.fundraiser)
    return render_template(
        "applicant.html",
        title="Volunteer Applicant Profile",
        application=application,
        applicant=application.user,
        active="home",
    )


@bp.route("/applications/<int:aid>/<decision>", methods=["GET", "POST"])
@require_role("charity_organization")
def decide(aid, decision):
    if decision not in ["accept", "reject"]:
        abort(404)
    application = db.get_or_404(VolunteerApplication, aid)
    op = application.opportunity
    owned_fundraiser(op.fundraiser)
    if not verified_organization():
        return redirect(url_for("organization.dashboard"))
    if request.method == "POST":
        if request.form.get("confirm") != "yes":
            abort(400, "Please confirm this decision.")
        # BEGIN IMMEDIATE serializes capacity decisions in SQLite, including competing reviews.
        db.session.rollback()
        db.session.execute(db.text("BEGIN IMMEDIATE"))
        application = db.session.get(VolunteerApplication, aid)
        op = application.opportunity
        if application.status != "pending":
            abort(409, "This application has already been reviewed.")
        if decision == "accept" and (not op.available or op.accepted_count >= op.slots):
            abort(
                409, "This opportunity is closed or has no volunteer slots remaining."
            )
        application.status = "accepted" if decision == "accept" else "rejected"
        record(
            "Volunteer " + application.status,
            "application",
            aid,
            f"Application for {op.title} was {application.status}.",
        )
        commit()
        flash("Volunteer " + application.status + ".", "success")
        return redirect(url_for("organization.applicant", aid=aid))
    return render_template(
        "confirm.html",
        title=("Accept" if decision == "accept" else "Reject") + " Volunteer?",
        target=application.user.name,
        explanation="The applicant will see this decision in their volunteer history.",
        cancel_url=url_for("organization.applicant", aid=aid),
        button="Confirm decision",
        active="home",
    )
