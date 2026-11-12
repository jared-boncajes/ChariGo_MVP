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
        b"password is not correct"
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
        b"deactivated"
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
    # Posting without confirming (for example with JavaScript off) changes nothing
    # and shows the confirmation page instead.
    unconfirmed = post(client, "/admin/actions/user/1/deactivate", {})
    assert unconfirmed.status_code == 200 and b"Confirm deactivate" in unconfirmed.data
    with app.app_context():
        assert db.session.get(User, 1).account_status == "active"


def flat(response):
    """Page text with template whitespace collapsed."""
    return " ".join(response.get_data(as_text=True).split())


def test_history_filters_export_and_withdrawal(client, app):
    login(client)
    page = client.get("/history/donations")
    assert page.status_code == 200
    assert "Showing 3 of 3 donations" in flat(page)
    assert b"Download CSV" in page.data
    assert client.get("/history").status_code == 302

    narrowed = client.get("/history/donations?q=iwas+gutom")
    assert "Showing 1 of 3 donations" in flat(narrowed)
    assert b"Clear filters" in narrowed.data
    nothing = client.get("/history/donations?q=no-such-charity")
    assert b"Nothing matches these filters" in nothing.data
    assert client.get("/history/donations?period=30&sort=highest").status_code == 200
    # Unknown filter values fall back to the defaults instead of failing.
    assert client.get("/history/donations?period=x&sort=y").status_code == 200

    export = client.get("/history/donations.csv?q=iwas+gutom")
    assert export.mimetype == "text/csv"
    assert "attachment" in export.headers["Content-Disposition"]
    rows = export.get_data(as_text=True).strip().splitlines()
    assert len(rows) == 2 and "Iwas Gutom Society" in rows[1]

    volunteering = client.get("/history/volunteering?status=accepted")
    assert "Showing 2 of 4 applications" in flat(volunteering)
    assert client.get("/history/volunteering.csv").mimetype == "text/csv"

    with app.app_context():
        mine = db.session.scalar(
            db.select(User).where(User.email == "goer@example.com")
        )
        pending = next(a for a in mine.applications if a.status == "pending")
        decided = next(a for a in mine.applications if a.status == "accepted")
        other = db.session.scalar(
            db.select(VolunteerApplication).where(
                VolunteerApplication.user_id != mine.id
            )
        )
        pending_id, decided_id, other_id = pending.id, decided.id, other.id
    assert post(client, f"/applications/{other_id}/withdraw").status_code == 403
    assert post(client, f"/applications/{decided_id}/withdraw").status_code == 409
    done = post(client, f"/applications/{pending_id}/withdraw", follow_redirects=True)
    assert b"was withdrawn" in done.data
    with app.app_context():
        assert db.session.get(VolunteerApplication, pending_id) is None


def test_organization_sees_only_its_own_donations(client):
    login(client, "organization@example.com")
    page = client.get("/organization/donations")
    assert page.status_code == 200
    assert b"Total received" in page.data
    assert b"Dinner for the Unhoused" not in page.data
    assert client.get("/organization/donations?fundraiser=999").status_code == 200
    client.get("/")
    post(client, "/logout")
    login(client)
    assert client.get("/organization/donations").status_code == 403


def test_static_files_are_cacheable_and_pages_are_compressed(client):
    home = client.get("/home", headers={"Accept-Encoding": "gzip"})
    assert home.headers.get("Content-Encoding") == "gzip"
    assert b"opt/children.webp" in __import__("gzip").decompress(home.data)
    asset = client.get("/static/css/style.css")
    assert "max-age=31536000" in asset.headers["Cache-Control"]


def test_login_messages_and_demo_account_repair(client, app):
    assert b"Home" in post(
        client,
        "/login",
        {"email": " Goer@Example.com ", "password": "ChariGo123! "},
        follow_redirects=True,
    ).data
    client.get("/")
    post(client, "/logout")
    wrong = post(client, "/login", {"email": "nobody@nowhere.com", "password": "x"})
    assert b"No account uses that email address" in wrong.data
    with app.app_context():
        goer = db.session.scalar(db.select(User).where(User.email == "goer@example.com"))
        goer.account_status = "inactive"
        goer.password_hash = "changed"
        db.session.commit()
    broken = post(client, "/login", {"email": "goer@example.com", "password": "ChariGo123!"})
    assert b"restore-demo" in broken.data
    result = app.test_cli_runner().invoke(args=["restore-demo"])
    assert "Demo accounts are ready" in result.output
    assert login(client).status_code == 200
    assert client.get("/profile").status_code == 200


def test_back_button_cannot_return_to_guest_pages_when_signed_in(client):
    for path in ["/", "/login", "/register", "/register/role"]:
        page = client.get(path)
        assert page.headers["Cache-Control"] == "no-store", path
        assert b'data-signed-in="0"' in page.data
    signed_in = login(client)
    assert b'data-signed-in="1"' in signed_in.data
    assert client.get_cookie("cg_signed_in").value == "1"
    for path in ["/", "/login", "/register", "/register/role"]:
        reply = client.get(path)
        assert reply.status_code == 302, path
        assert reply.headers["Location"].endswith("/home")
    client.get("/")
    post(client, "/logout")
    assert client.get_cookie("cg_signed_in") is None
    assert client.get("/login").status_code == 200


def test_navigation_and_profile_entry_points(client):
    login(client)
    home = client.get("/home").get_data(as_text=True)
    assert "Browse by category" not in home
    assert "Categories" in client.get("/causes").get_data(as_text=True)
    nav = home.split('aria-label="Main navigation"')[1].split("</nav>")[0]
    assert "Profile" not in nav and "Explore" in nav
    assert 'class="account-chip"' in home and 'href="/profile"' in home
    post(client, "/logout")

    login(client, "organization@example.com")
    page = client.get("/organization")
    text = page.get_data(as_text=True)
    nav = text.split('aria-label="Organization navigation"')[1].split("</nav>")[0]
    assert "Profile" not in nav and "Create" in nav
    assert 'class="account-chip"' in text and 'href="/organization"' in text
    # No My Account page for organizations: /profile leads to the organization profile.
    assert client.get("/profile").headers["Location"].endswith("/organization")
    for removed in ["Current Fundraisers", "Past Fundraisers", "Create Fundraiser", "My Account"]:
        assert removed not in text, removed
    for present in ["Donations Received", "Edit Organization", "Edit Profile", "Log out"]:
        assert present in text, present
    lists = client.get("/organization/fundraisers").get_data(as_text=True)
    assert 'class="back"' not in lists and "Create Fundraiser" not in lists
    past = client.get("/organization/fundraisers?status=past").get_data(as_text=True)
    assert 'class="back"' not in past and "Create Fundraiser" not in past
    edit = client.get("/profile/edit").get_data(as_text=True)
    assert 'href="/organization"' in edit


def test_review_buttons_use_standard_wording(client):
    login(client)
    post(client, "/fundraisers/1/donate", {"amount": "250", "method": "GCash"})
    review = client.get("/donation/review").get_data(as_text=True)
    assert "Edit / Cancel" not in review
    assert ">Cancel</a>" in review and "Confirm Donation" in review


def test_past_campaigns_are_viewable_but_not_donatable(client, app):
    login(client)
    page = client.get("/organizations/1?tab=campaigns").get_data(as_text=True)
    assert "Past campaigns" in page and "Community Feeding Drive" in page
    with app.app_context():
        past = db.session.scalar(
            db.select(Fundraiser).where(Fundraiser.title == "Community Feeding Drive")
        )
        past_id = past.id
    detail = client.get(f"/fundraisers/{past_id}").get_data(as_text=True)
    assert "This campaign has ended" in detail
    assert "/donate" not in detail and "Volunteer</a>" not in detail
    assert client.get(f"/fundraisers/{past_id}/donate").status_code == 409


def test_donating_from_an_organization_page_offers_its_active_campaigns(client, app):
    login(client)
    assert 'href="/organizations/1/donate"' in client.get("/organizations/1").get_data(as_text=True)
    chooser = client.get("/organizations/1/donate").get_data(as_text=True)
    assert "Choose a campaign" in chooser
    assert "Community Feeding Drive" not in chooser  # only current campaigns
    for title in ["Bawat Batang Pinoy Malusog", "Learning Kits, Brighter Futures"]:
        assert title in chooser
    assert 'href="/fundraisers/1/donate"' in chooser
    with app.app_context():
        for f in db.session.scalars(
            db.select(Fundraiser).where(
                Fundraiser.organization_id == 1, Fundraiser.id != 1
            )
        ):
            f.status = "inactive"
        db.session.commit()
    # With only one campaign left there is nothing to choose: go straight to it.
    assert client.get("/organizations/1/donate").headers["Location"].endswith("/fundraisers/1/donate")


def test_costly_actions_are_red_and_ask_again(client):
    login(client, "admin@example.com")
    risky = client.get("/admin/actions/user/2/deactivate").get_data(as_text=True)
    assert 'data-tone="danger"' in risky and 'class="button danger"' in risky
    safe = client.get("/admin/actions/organization/3/approve").get_data(as_text=True)
    assert 'data-tone="danger"' not in safe
    detail = client.get("/admin/organizations/3").get_data(as_text=True)
    assert 'class="button danger"' in detail  # Reject Organization
    post(client, "/logout")
    login(client, "organization@example.com")
    decline = client.get("/organization/applications/5/reject").get_data(as_text=True)
    assert 'data-tone="danger"' in decline
    close = client.get("/organization/fundraisers/1/deactivate").get_data(as_text=True)
    assert 'data-tone="danger"' in close
    post(client, "/logout")
    login(client)
    history = client.get("/history/volunteering?status=pending").get_data(as_text=True)
    assert "data-confirm-again=" in history and 'class="button danger small"' in history


def test_admin_filters_keep_apply_and_reset_together(client):
    login(client, "admin@example.com")
    for path in ["/admin/users", "/admin/organizations", "/admin/opportunities"]:
        page = client.get(path).get_data(as_text=True)
        assert 'class="filter-form admin-filter"' in page
        assert 'class="button secondary" href="' + path + '">Reset</a>' in page


def test_every_role_lands_on_its_home_after_login(client):
    expected = {
        "goer@example.com": "/home",
        "organization@example.com": "/organization/fundraisers",
        "admin@example.com": "/admin",
    }
    for email, home in expected.items():
        landed = login(client, email)
        assert landed.request.path == home, email
        # Signed-in visits to the welcome and log-in pages lead to the same place.
        for path in ["/", "/login"]:
            assert client.get(path).headers["Location"].endswith(home), (email, path)
        post(client, "/logout")


def test_unapproved_organization_sees_its_status_on_home(client):
    landed = login(client, "pending@example.com")
    assert landed.request.path == "/organization/fundraisers"
    page = landed.get_data(as_text=True)
    assert "Please Wait!" in page and "Complete organization registration" in page


def test_confirmations_are_popups_not_pages(client, app):
    # Fundraiser management (organization)
    login(client, "organization@example.com")
    manage = client.get("/organization/fundraisers/1").get_data(as_text=True)
    assert 'data-confirm-title="Deactivate fundraiser?"' in manage
    assert 'data-confirm-title="Mark as completed?"' in manage
    assert 'href="/organization/fundraisers/1/deactivate"' not in manage
    assert manage.count("data-confirm-again=") == 2
    # Volunteer decisions
    applicant = client.get("/organization/applications/5").get_data(as_text=True)
    assert 'data-confirm-title="Accept volunteer?"' in applicant
    assert 'data-confirm-title="Decline volunteer?"' in applicant
    assert applicant.count("data-confirm-again=") == 1  # only the decline asks twice
    # The popup submits confirm=yes: the action is applied
    done = post(client, "/organization/applications/5/accept", {"confirm": "yes"}, follow_redirects=True)
    assert b"Volunteer accepted" in done.data
    post(client, "/logout")
    # Administrator actions carry an optional reason
    login(client, "admin@example.com")
    detail = client.get("/admin/organizations/3").get_data(as_text=True)
    assert 'data-confirm-title="Approve organization?"' in detail and "data-reason=" in detail
    assert 'name="reason"' in detail and 'href="/admin/actions/' not in detail
    user = client.get("/admin/users/2").get_data(as_text=True)
    assert 'data-confirm-title="Deactivate account?"' in user and "data-confirm-again=" in user
    opp = client.get("/admin/opportunities/fundraiser/1").get_data(as_text=True)
    assert 'data-confirm-title="Remove from listings?"' in opp
    reasoned = post(
        client,
        "/admin/actions/organization/3/approve",
        {"confirm": "yes", "reason": "Documents checked."},
        follow_redirects=True,
    )
    assert b"saved successfully" in reasoned.data
    with app.app_context():
        record = db.session.scalar(
            db.select(SystemRecord).where(SystemRecord.action == "Approve organization").order_by(SystemRecord.id.desc())
        )
        assert "Documents checked." in record.description


def test_logout_and_withdraw_popups_are_red(client):
    login(client)
    profile = client.get("/profile").get_data(as_text=True)
    form = profile.split('action="/logout"')[1].split("</form>")[0]
    assert 'data-tone="danger"' in form and 'data-confirm-label="Log out"' in form
    post(client, "/logout")
    login(client, "organization@example.com")
    org = client.get("/organization").get_data(as_text=True)
    form = org.split('action="/logout"')[1].split("</form>")[0]
    assert 'data-tone="danger"' in form
    post(client, "/logout")
    login(client)
    history = client.get("/history/volunteering?status=pending").get_data(as_text=True)
    withdraw = history.split("/withdraw")[0].rsplit("<form", 1)[1]
    assert 'data-tone="danger"' in withdraw and "data-confirm-again=" in withdraw
