import io
from datetime import date, timedelta
from PIL import Image
from models import (
    db,
    Donation,
    Fundraiser,
    Organization,
    SystemRecord,
    User,
    VolunteerApplication,
    VolunteerOpportunity,
)
from conftest import login, post


def test_seed_is_repeatable_and_hashes_passwords(app):
    from seed import seed_database

    with app.app_context():
        before = db.session.query(User).count()
        seed_database()
        assert db.session.query(User).count() == before == 7
        assert all(
            u.password_hash != "ChariGo123!"
            for u in db.session.scalars(db.select(User))
        )
        assert set(
            a.status for a in db.session.scalars(db.select(VolunteerApplication))
        ) == {"pending", "accepted", "rejected"}


def test_auth_registration_validation_and_logout(client, app):
    assert client.get("/profile").status_code == 302
    assert (
        b"Incorrect email"
        in post(
            client, "/login", {"email": "goer@example.com", "password": "wrong"}
        ).data
    )
    assert (
        b"passwords do not match"
        in post(
            client,
            "/register",
            {
                "name": "New Person",
                "email": "new@example.com",
                "role": "charity_goer",
                "password": "Password123",
                "confirm_password": "different",
            },
        ).data
    )
    data = dict(
        name="New Person",
        email="NEW@example.com",
        role="charity_goer",
        password="Password123",
        confirm_password="Password123",
    )
    assert post(client, "/register", data).status_code == 302
    assert b"already exists" in post(client, "/register", data).data
    assert (
        post(client, "/register", {**data, "role": "administrator"}).status_code == 400
    )
    assert login(client).status_code == 200
    assert post(client, "/logout").status_code == 302
    assert client.get("/profile").status_code == 302
    with app.app_context():
        assert (
            db.session.scalar(
                db.select(User).where(User.email == "new@example.com")
            ).role
            == "charity_goer"
        )


def test_csrf_is_required(client):
    client.get("/login")
    assert (
        client.post(
            "/login", data={"email": "goer@example.com", "password": "ChariGo123!"}
        ).status_code
        == 400
    )


def test_all_main_pages_render_for_each_role(client):
    for email, urls in [
        (
            "goer@example.com",
            [
                "/home",
                "/causes",
                "/fundraisers/1",
                "/organizations/1",
                "/organizations/1?tab=campaigns",
                "/organizations/1?tab=contact",
                "/fundraisers/1/donate",
                "/opportunities/1",
                "/profile",
                "/profile/edit",
                "/history/donations",
                "/history/volunteering",
            ],
        ),
        (
            "organization@example.com",
            [
                "/organization",
                "/organization/profile",
                "/organization/fundraisers",
                "/organization/fundraisers?status=past",
                "/organization/fundraisers/new",
                "/organization/fundraisers/1",
                "/organization/fundraisers/1/edit",
                "/organization/fundraisers/1/applications",
                "/organization/applications/5",
                "/organization/fundraisers/1/deactivate",
                "/organization/applications/5/accept",
            ],
        ),
        (
            "admin@example.com",
            [
                "/admin",
                "/admin/users",
                "/admin/users/1",
                "/admin/organizations",
                "/admin/organizations/3",
                "/admin/opportunities",
                "/admin/opportunities/fundraiser/1",
                "/admin/opportunities/volunteer/1",
                "/admin/records",
                "/admin/actions/user/1/deactivate",
            ],
        ),
    ]:
        login(client, email)
        for url in urls:
            assert client.get(url).status_code == 200, url
        post(client, "/logout")


def test_role_and_ownership_restrictions(client):
    login(client)
    for url in [
        "/admin",
        "/admin/users",
        "/admin/organizations",
        "/admin/opportunities",
        "/admin/records",
        "/organization",
    ]:
        assert client.get(url).status_code == 403
    post(client, "/logout")
    login(client, "iwas@example.com")
    for url in [
        "/organization/fundraisers/1",
        "/organization/fundraisers/1/edit",
        "/organization/fundraisers/1/applications",
        "/organization/applications/5",
        "/organization/applications/5/accept",
    ]:
        assert client.get(url).status_code == 403
    assert (
        post(
            client, "/organization/fundraisers/1/deactivate", {"confirm": "yes"}
        ).status_code
        == 403
    )
    assert client.get("/fundraisers/1/donate").status_code == 403


def test_donation_review_commit_receipt_history_and_replay(client, app):
    login(client)
    with app.app_context():
        f = db.session.get(Fundraiser, 1)
        before = f.raised_cents
        count = db.session.query(Donation).count()
    assert post(
        client,
        "/fundraisers/1/donate",
        {"amount": "250.75", "method": "GCash", "anonymous": "on"},
    ).location.endswith("/donation/review")
    review = client.get("/donation/review")
    assert b"250.75" in review.data and b"simulated" in review.data
    with client.session_transaction() as session:
        nonce = session["donation_review"]["token"]
    response = post(client, "/donation/review", {"review_token": nonce})
    assert "/donations/" in response.location
    assert b"Thank You!" in client.get(response.location).data
    post(client, "/donation/review", {"review_token": nonce})
    assert b"250.75" in client.get("/history/donations").data
    with app.app_context():
        assert db.session.query(Donation).count() == count + 1
        assert db.session.get(Fundraiser, 1).raised_cents == before + 25075
        donation = db.session.scalar(
            db.select(Donation).where(Donation.submission_token == nonce)
        )
        assert donation.anonymous
    post(client, "/logout")
    login(client, "juan@example.com")
    assert client.get(response.location).status_code == 403


def test_invalid_donations_never_write(client, app):
    login(client)
    for amount in ["0", "-1", "NaN", "Infinity", "1.001", "10000001", "abc", ""]:
        response = post(
            client, "/fundraisers/1/donate", {"amount": amount, "method": "GCash"}
        )
        assert response.status_code == 200 and b"Enter an amount" in response.data
    assert (
        b"Choose a payment method"
        in post(
            client, "/fundraisers/1/donate", {"amount": "250", "method": "Invalid"}
        ).data
    )
    assert client.get("/fundraisers/7/donate").status_code == 409


def test_volunteer_application_review_duplicate_and_decision(client, app):
    login(client)
    assert post(
        client, "/opportunities/1", {"message": "I can help prepare nutritious meals."}
    ).location.endswith("/volunteer/review")
    assert b"Review Application" in client.get("/volunteer/review").data
    with client.session_transaction() as session:
        nonce = session["volunteer_review"]["token"]
    response = post(client, "/volunteer/review", {"review_token": nonce})
    assert b"Thank You!" in client.get(response.location).data
    with app.app_context():
        a = db.session.scalar(
            db.select(VolunteerApplication).where(
                VolunteerApplication.user_id == 1,
                VolunteerApplication.opportunity_id == 1,
            )
        )
        aid = a.id
        assert a.status == "pending"
    assert (
        post(
            client, "/opportunities/1", {"message": "Trying to apply twice."}
        ).status_code
        == 302
    )
    post(client, "/logout")
    login(client, "organization@example.com")
    assert b"I can help" in client.get(f"/organization/applications/{aid}").data
    assert (
        post(
            client, f"/organization/applications/{aid}/accept", {"confirm": "yes"}
        ).status_code
        == 302
    )
    assert (
        post(
            client, f"/organization/applications/{aid}/accept", {"confirm": "yes"}
        ).status_code
        == 409
    )
    post(client, "/logout")
    login(client)
    assert b"Accepted" in client.get("/history/volunteering").data
    with app.app_context():
        assert db.session.get(VolunteerApplication, aid).status == "accepted"
        assert (
            db.session.query(VolunteerApplication)
            .filter_by(user_id=1, opportunity_id=1)
            .count()
            == 1
        )


def test_reject_and_capacity(client, app):
    login(client, "organization@example.com")
    with app.app_context():
        op = db.session.get(VolunteerOpportunity, 1)
        op.slots = 1
        db.session.commit()
    assert (
        post(
            client, "/organization/applications/5/accept", {"confirm": "yes"}
        ).status_code
        == 302
    )
    assert (
        post(
            client, "/organization/applications/6/accept", {"confirm": "yes"}
        ).status_code
        == 409
    )
    assert (
        post(
            client, "/organization/applications/6/reject", {"confirm": "yes"}
        ).status_code
        == 302
    )
    with app.app_context():
        assert db.session.get(VolunteerOpportunity, 1).accepted_count == 1
        assert db.session.get(VolunteerApplication, 6).status == "rejected"


def campaign_data(**extra):
    return dict(
        title="Community Food Drive",
        description="A community fundraiser to prepare and distribute meals.",
        impact="Provide nutritious meals for families in our community.",
        category="Children",
        location="Pasig City",
        goal="100000.50",
        start_date=date.today().isoformat(),
        end_date=(date.today() + timedelta(days=30)).isoformat(),
        volunteers="on",
        slots="10",
        event_date=(date.today() + timedelta(days=7)).isoformat(),
        volunteer_description="Prepare and distribute meals with our team.",
        requirements="Attend the volunteer orientation.",
        **extra,
    )


def test_organization_campaign_lifecycle(client, app):
    login(client, "organization@example.com")
    response = post(client, "/organization/fundraisers/new", campaign_data())
    assert response.status_code == 302
    with app.app_context():
        f = db.session.scalar(
            db.select(Fundraiser).where(Fundraiser.title == "Community Food Drive")
        )
        fid = f.id
        assert f.goal_cents == 10000050 and f.opportunity.slots == 10
    assert b"Community Food Drive" in client.get("/causes?q=Community+Food").data
    assert (
        post(
            client,
            f"/organization/fundraisers/{fid}/edit",
            {**campaign_data(), "title": "Updated Food Drive"},
        ).status_code
        == 302
    )
    assert b"Updated Food Drive" in client.get(f"/fundraisers/{fid}").data
    assert b"Confirm" in client.get(f"/organization/fundraisers/{fid}/deactivate").data
    with app.app_context():
        assert db.session.get(Fundraiser, fid).status == "active"
    assert (
        post(
            client, f"/organization/fundraisers/{fid}/deactivate", {"confirm": "yes"}
        ).status_code
        == 302
    )
    assert b"Updated Food Drive" not in client.get("/causes").data
    assert (
        b"Updated Food Drive"
        in client.get("/organization/fundraisers?status=past").data
    )
    with app.app_context():
        assert db.session.get(Fundraiser, fid).status == "inactive"


def test_campaign_validation_and_unverified_restrictions(client):
    login(client, "organization@example.com")
    for changed in [
        {"goal": "-100"},
        {"end_date": "2020-01-01"},
        {"slots": "0"},
        {"event_date": "2020-01-01"},
        {"category": "Imaginary"},
    ]:
        response = post(
            client, "/organization/fundraisers/new", {**campaign_data(), **changed}
        )
        assert response.status_code == 200 and b"flash error" in response.data
    post(client, "/logout")
    login(client, "pending@example.com")
    assert client.get("/organization/fundraisers/new").status_code == 302
    assert (
        post(client, "/organization/fundraisers/new", campaign_data()).status_code
        == 302
    )


def test_new_organization_registration_and_approval(client, app):
    post(
        client,
        "/register",
        dict(
            name="New Team",
            email="team@example.com",
            role="charity_organization",
            password="Password123",
            confirm_password="Password123",
        ),
    )
    post(client, "/login", dict(email="team@example.com", password="Password123"))
    data = dict(
        name="Neighborhood Helpers",
        description="We bring community members together to prepare nutritious meals.",
        mission="Provide meaningful support for our neighbors.",
        portfolio="Community kitchen project.",
        contact_email="team@example.com",
        phone="",
        location="Manila",
    )
    assert post(client, "/organization/profile", data).status_code == 302
    with app.app_context():
        org = db.session.scalar(
            db.select(Organization).where(Organization.name == "Neighborhood Helpers")
        )
        oid = org.id
        assert org.verification_status == "pending"
    post(client, "/logout")
    login(client, "admin@example.com")
    assert (
        post(
            client, f"/admin/actions/organization/{oid}/approve", {"confirm": "yes"}
        ).status_code
        == 302
    )
    with app.app_context():
        assert db.session.get(Organization, oid).verification_status == "verified"
        assert db.session.scalar(
            db.select(SystemRecord).where(
                SystemRecord.target_id == oid,
                SystemRecord.action == "Approve organization",
            )
        )


def test_admin_deactivate_and_reactivate_live_account(client, app):
    goer = app.test_client()
    login(goer)
    login(client, "admin@example.com")
    assert client.get("/admin/actions/user/1/deactivate").status_code == 200
    assert (
        post(
            client,
            "/admin/actions/user/1/deactivate",
            {"confirm": "yes", "reason": "Account review."},
        ).status_code
        == 302
    )
    assert goer.get("/profile").status_code == 302
    assert (
        b"inactive"
        in post(
            goer, "/login", {"email": "goer@example.com", "password": "ChariGo123!"}
        ).data
    )
    assert (
        post(client, "/admin/actions/user/1/reactivate", {"confirm": "yes"}).status_code
        == 302
    )
    assert login(goer).status_code == 200
    assert (
        post(client, "/admin/actions/user/7/deactivate", {"confirm": "yes"}).status_code
        == 403
    )
    with app.app_context():
        assert db.session.get(User, 1).account_status == "active"


def test_admin_moderation_preserves_history_and_audits(client, app):
    login(client, "admin@example.com")
    for kind in ["fundraiser", "volunteer"]:
        assert (
            post(
                client,
                f"/admin/actions/{kind}/1/deactivate",
                {"confirm": "yes", "reason": "Please review the listing."},
            ).status_code
            == 302
        )
    guest = app.test_client()
    assert b"Bawat Batang Pinoy Malusog" not in guest.get("/causes").data
    assert guest.get("/fundraisers/1").status_code == 404
    user = app.test_client()
    login(user)
    assert user.get("/opportunities/1").status_code == 404
    assert (
        post(
            client, "/admin/actions/fundraiser/1/reactivate", {"confirm": "yes"}
        ).status_code
        == 302
    )
    assert guest.get("/fundraisers/1").status_code == 200
    with app.app_context():
        assert db.session.get(Fundraiser, 1).donations
        assert (
            db.session.query(SystemRecord)
            .filter(SystemRecord.action.like("Deactivate%"))
            .count()
            == 2
        )
    assert b"Please review the listing" in client.get("/admin/records?q=listing").data


def test_organization_admin_statuses_and_public_visibility(client):
    login(client, "admin@example.com")
    for action in ["reject", "approve", "deactivate", "reactivate"]:
        assert (
            post(
                client,
                f"/admin/actions/organization/3/{action}",
                {"confirm": "yes", "reason": "Registration reviewed."},
            ).status_code
            == 302
        )
    assert (
        post(
            client, "/admin/actions/organization/1/deactivate", {"confirm": "yes"}
        ).status_code
        == 302
    )
    guest = client.application.test_client()
    assert guest.get("/organizations/1").status_code == 404
    assert guest.get("/fundraisers/1").status_code == 404
    assert (
        post(
            client, "/admin/actions/organization/1/reactivate", {"confirm": "yes"}
        ).status_code
        == 302
    )
    assert guest.get("/fundraisers/1").status_code == 200


def test_search_filters_and_empty_states(client):
    assert b"No causes match" in client.get("/causes?q=nevermatchthis").data
    assert b"Bawat Batang Pinoy Malusog" in client.get("/causes?category=Children").data
    assert (
        b"Dinner for the Unhoused" not in client.get("/causes?category=Children").data
    )
    login(client, "admin@example.com")
    assert b"No matching records" in client.get("/admin/users?q=nevermatchthis").data
    assert (
        b"Community Care Collective"
        in client.get("/admin/organizations?status=pending").data
    )
    assert b"Fundraiser" in client.get("/admin/opportunities?type=volunteer").data


def test_upload_validation_profile_save_and_private_portfolio(client, app):
    login(client)
    data = dict(
        name="Maria Updated",
        email="goer@example.com",
        phone="",
        location="Pasig",
        availability="Weekends",
        skills="Cooking",
        experience="Community kitchen",
    )
    assert (
        b"valid JPG or PNG"
        in post(
            client,
            "/profile/edit",
            {**data, "image": (io.BytesIO(b"not an image"), "bad.png")},
        ).data
    )
    im = Image.new("RGB", (20, 20), "pink")
    buf = io.BytesIO()
    im.save(buf, "PNG")
    buf.seek(0)
    assert (
        post(
            client, "/profile/edit", {**data, "image": (buf, "../../avatar.png")}
        ).status_code
        == 302
    )
    assert b"Maria Updated" in client.get("/profile").data
    with app.app_context():
        image = db.session.get(User, 1).image
        assert image.startswith("upload:") and ".." not in image
    assert client.get("/uploads/" + image[7:]).status_code == 200
    post(client, "/logout")
    login(client, "organization@example.com")
    orgdata = dict(
        name="Angat Buhay Foundation",
        description="We connect communities with meaningful volunteer programs.",
        mission="Create lasting opportunities for everyone.",
        portfolio="",
        contact_email="organization@example.com",
        phone="",
        location="Manila",
    )
    assert (
        b"PDF portfolio"
        in post(
            client,
            "/organization/profile",
            {**orgdata, "portfolio_file": (io.BytesIO(b"not pdf"), "bad.pdf")},
        ).data
    )
    assert (
        post(
            client,
            "/organization/profile",
            {**orgdata, "portfolio_file": (io.BytesIO(b"%PDF-1.7\n%%EOF"), "safe.pdf")},
        ).status_code
        == 302
    )
    assert client.get("/organization/1/portfolio").status_code == 200
    post(client, "/logout")
    login(client, "iwas@example.com")
    assert client.get("/organization/1/portfolio").status_code == 403


def test_save_charity_and_confirmations(client, app):
    login(client)
    assert post(client, "/organizations/2/save").status_code == 302
    assert b"Iwas Gutom Society" in client.get("/profile").data
    post(client, "/organizations/2/save")
    post(client, "/logout")
    login(client, "admin@example.com")
    assert post(client, "/admin/actions/user/1/deactivate", {}).status_code == 400
    with app.app_context():
        assert db.session.get(User, 1).account_status == "active"
