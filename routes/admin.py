from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from common import commit, record, require_role, text
from models import (
    db,
    Fundraiser,
    Organization,
    SystemRecord,
    User,
    VolunteerOpportunity,
)

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
@require_role("administrator")
def administrator_only():
    # The decorator checks the live account and role before any admin route runs.
    return None


@bp.route("")
def dashboard():
    users = db.session.scalars(db.select(User)).all()
    orgs = db.session.scalars(db.select(Organization)).all()
    campaigns = db.session.scalars(db.select(Fundraiser)).all()
    opportunities = db.session.scalars(db.select(VolunteerOpportunity)).all()
    stats = [
        ("Users", len(users), "admin.users"),
        ("Charity Goers", sum(u.role == "charity_goer" for u in users), "admin.users"),
        ("Organizations", len(orgs), "admin.organizations"),
        (
            "Pending verification",
            sum(o.verification_status == "pending" for o in orgs),
            "admin.organizations",
        ),
        (
            "Active fundraisers",
            sum(f.accepting for f in campaigns),
            "admin.opportunities",
        ),
        (
            "Volunteer opportunities",
            sum(o.available for o in opportunities),
            "admin.opportunities",
        ),
    ]
    records = db.session.scalars(
        db.select(SystemRecord).order_by(SystemRecord.created_at.desc()).limit(5)
    ).all()
    return render_template(
        "admin_dashboard.html",
        title="Administrator Dashboard",
        stats=stats,
        records=records,
        active="admin",
    )


@bp.route("/users")
def users():
    q = request.args.get("q", "").strip()[:150].casefold()
    role = request.args.get("role", "")
    status = request.args.get("status", "")
    items = [
        u
        for u in db.session.scalars(
            db.select(User).order_by(User.created_at.desc())
        ).all()
        if (not q or q in (u.name + " " + u.email).casefold())
        and (not role or u.role == role)
        and (not status or u.account_status == status)
    ]
    return render_template(
        "admin_list.html",
        title="User Accounts",
        kind="users",
        items=items,
        active="admin",
    )


@bp.route("/users/<int:uid>")
def user_detail(uid):
    user = db.get_or_404(User, uid)
    return render_template(
        "admin_detail.html",
        title="User Details",
        kind="user",
        item=user,
        active="admin",
    )


@bp.route("/organizations")
def organizations():
    q = request.args.get("q", "").strip()[:150].casefold()
    status = request.args.get("status", "")
    items = [
        o
        for o in db.session.scalars(
            db.select(Organization).order_by(Organization.created_at.desc())
        ).all()
        if (not q or q in (o.name + " " + o.description).casefold())
        and (not status or o.verification_status == status)
    ]
    return render_template(
        "admin_list.html",
        title="Charity Organizations",
        kind="organizations",
        items=items,
        active="admin",
    )


@bp.route("/organizations/<int:oid>")
def organization_detail(oid):
    org = db.get_or_404(Organization, oid)
    return render_template(
        "admin_detail.html",
        title="Organization Review",
        kind="organization",
        item=org,
        active="admin",
    )


@bp.route("/opportunities")
def opportunities():
    q = request.args.get("q", "").strip()[:150].casefold()
    status = request.args.get("status", "")
    kind = request.args.get("type", "")
    items = []
    for item_type, model in [
        ("fundraiser", Fundraiser),
        ("volunteer", VolunteerOpportunity),
    ]:
        if kind and item_type != kind:
            continue
        for item in db.session.scalars(db.select(model)).all():
            f = item if item_type == "fundraiser" else item.fundraiser
            current_status = (
                item.moderation_status if item_type == "fundraiser" else item.status
            )
            if (
                not q
                or q
                in (
                    item.title + " " + f.organization.name + " " + item.description
                ).casefold()
            ) and (not status or current_status == status):
                items.append(
                    dict(
                        type=item_type,
                        item=item,
                        status=current_status,
                        organization=f.organization,
                    )
                )
    return render_template(
        "admin_list.html",
        title="Opportunity Monitoring",
        kind="opportunities",
        items=items,
        active="admin",
    )


@bp.route("/opportunities/<kind>/<int:oid>")
def opportunity_detail(kind, oid):
    if kind not in ["fundraiser", "volunteer"]:
        abort(404)
    item = db.get_or_404(
        Fundraiser if kind == "fundraiser" else VolunteerOpportunity, oid
    )
    return render_template(
        "admin_detail.html",
        title="Opportunity Details",
        kind=kind,
        item=item,
        active="admin",
    )


@bp.route("/records")
def records():
    q = request.args.get("q", "").strip()[:150].casefold()
    items = [
        r
        for r in db.session.scalars(
            db.select(SystemRecord).order_by(
                SystemRecord.created_at.desc(), SystemRecord.id.desc()
            )
        ).all()
        if not q
        or q
        in (
            r.action
            + " "
            + r.description
            + " "
            + r.target_type
            + " "
            + (r.actor.name if r.actor else "System")
        ).casefold()
    ]
    return render_template(
        "admin_records.html", title="System Records", records=items, active="admin"
    )


@bp.route("/actions/<kind>/<int:oid>/<action>", methods=["GET", "POST"])
def action(kind, oid, action):
    models = {
        "user": User,
        "organization": Organization,
        "fundraiser": Fundraiser,
        "volunteer": VolunteerOpportunity,
    }
    allowed = {
        "user": ["deactivate", "reactivate"],
        "organization": ["approve", "reject", "deactivate", "reactivate"],
        "fundraiser": ["deactivate", "reactivate", "remove"],
        "volunteer": ["deactivate", "reactivate", "remove"],
    }
    if kind not in models or action not in allowed[kind]:
        abort(404)
    item = db.get_or_404(models[kind], oid)
    if kind == "user" and item.id == g.user.id:
        abort(403, "You cannot deactivate your own administrator account.")
    detail_endpoint = {
        "user": "admin.user_detail",
        "organization": "admin.organization_detail",
        "fundraiser": "admin.opportunity_detail",
        "volunteer": "admin.opportunity_detail",
    }[kind]
    kwargs = {"uid": oid} if kind == "user" else {"oid": oid}
    if kind in ["fundraiser", "volunteer"]:
        kwargs["kind"] = kind
    cancel_url = url_for(detail_endpoint, **kwargs)
    if request.method == "POST" and request.form.get("confirm") == "yes":
        try:
            reason = text("reason", "Reason", 0, 750)
            if kind == "user":
                item.account_status = "active" if action == "reactivate" else "inactive"
            elif kind == "organization":
                if action in ["approve", "reactivate"] and (
                    not item.description or not item.mission or not item.location
                ):
                    raise ValueError(
                        "The organization must complete its about, mission and location fields before verification."
                    )
                item.verification_status = {
                    "approve": "verified",
                    "reactivate": "verified",
                    "reject": "rejected",
                    "deactivate": "inactive",
                }[action]
                item.rejection_reason = reason if action == "reject" else ""
            else:
                status = {
                    "reactivate": "active",
                    "deactivate": "inactive",
                    "remove": "removed",
                }[action]
                if kind == "fundraiser":
                    item.moderation_status = status
                else:
                    item.status = status
            record(
                action.title() + " " + kind,
                kind,
                oid,
                f'{action.title()} {getattr(item, "name", getattr(item, "title", "record"))}. '
                + reason,
            )
            commit()
            flash("Administrative action saved successfully.", "success")
            return redirect(cancel_url)
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "error")
    return render_template(
        "confirm.html",
        title=action.title() + " " + kind.title() + "?",
        target=getattr(item, "name", getattr(item, "title", "Record")),
        explanation="This change updates access or public visibility. The record and its history will be preserved, and this action will be audited.",
        cancel_url=cancel_url,
        button="Confirm " + action,
        danger=action in {"deactivate", "remove", "reject"},
        final_label="Yes, " + action,
        ask_reason=True,
        active="admin",
    )
