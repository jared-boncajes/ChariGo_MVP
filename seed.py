from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from models import (
    db,
    Donation,
    Fundraiser,
    Organization,
    SavedCharity,
    SystemRecord,
    User,
    VolunteerApplication,
    VolunteerOpportunity,
)

DEMO_PASSWORD = "ChariGo123!"


def seed_database():
    # Seeding is idempotent and never overwrites existing application data.
    if db.session.scalar(db.select(User.id).limit(1)):
        return

    def user(name, email, role):
        u = User(
            name=name,
            email=email,
            role=role,
            password_hash=generate_password_hash(DEMO_PASSWORD),
            location="Quezon City",
            phone="+63 917 123 4567",
            availability="Weekends",
            skills="Meal preparation and food distribution\nPacking and logistics support\nEvent registration and coordination",
            experience="2 years of community volunteer work",
        )
        db.session.add(u)
        return u

    goer = user("Maria Santos", "goer@example.com", "charity_goer")
    juan = user("Juan Dela Cruz", "juan@example.com", "charity_goer")
    ana = user("Ana Reyes", "ana@example.com", "charity_goer")
    owner = user("Angat Buhay Team", "organization@example.com", "charity_organization")
    owner2 = user("Iwas Gutom Team", "iwas@example.com", "charity_organization")
    owner3 = user("Community Care Team", "pending@example.com", "charity_organization")
    admin = user("ChariGo Administrator", "admin@example.com", "administrator")
    org = Organization(
        owner=owner,
        name="Angat Buhay Foundation",
        description="Angat Buhay works with communities to create lasting opportunities through education, health, livelihood, and disaster response initiatives.",
        mission="Build resilient communities by connecting people with programs and resources that create meaningful, measurable impact.",
        portfolio="Community-led education, feeding programs, health missions and disaster response across the Philippines.",
        contact_email="organization@example.com",
        phone="+63 917 123 4567",
        location="Quezon City",
        verification_status="verified",
        banner="angat-buhay.jpg",
    )
    org2 = Organization(
        owner=owner2,
        name="Iwas Gutom Society",
        description="A community kitchen bringing warm meals and meaningful support to unhoused neighbors around Manila.",
        mission="Make nutritious meals accessible to everyone through community kitchens and volunteer service.",
        portfolio="Weekly community meal preparation and distribution.",
        contact_email="iwas@example.com",
        location="Manila",
        verification_status="verified",
        banner="iwas-gutom.png",
    )
    org3 = Organization(
        owner=owner3,
        name="Community Care Collective",
        description="A newly registered community organization preparing learning kits for children in underserved neighborhoods.",
        mission="Connect local volunteers with children who need educational support.",
        portfolio="Pilot learning kit drive and weekend reading circles.",
        contact_email="pending@example.com",
        location="Pasig City",
        verification_status="pending",
        banner="education.png",
    )
    db.session.add_all([org, org2, org3])
    today = date.today()
    entries = [
        (
            org,
            "Bawat Batang Pinoy Malusog",
            "Children",
            "children.png",
            30000,
            18500,
            "Quezon City",
        ),
        (
            org2,
            "Dinner for the Unhoused",
            "Hunger & Poverty",
            "iwas-gutom.png",
            50000,
            22000,
            "Manila",
        ),
        (
            org,
            "Learning Kits, Brighter Futures",
            "Education",
            "education.png",
            40000,
            12500,
            "Pasig City",
        ),
        (
            org,
            "Grow a Greener Community",
            "Environment",
            "environment.png",
            25000,
            6000,
            "Quezon City",
        ),
        (
            org2,
            "Care for Our Furry Friends",
            "Animal Welfare",
            "animals.png",
            20000,
            7000,
            "Manila",
        ),
        (
            org,
            "Health for Every Family",
            "Health",
            "health.png",
            60000,
            15000,
            "Quezon City",
        ),
    ]
    campaigns = []
    for index, (
        organization,
        title,
        category,
        image,
        goal,
        raised,
        location,
    ) in enumerate(entries):
        impact = (
            "Provide nutritious meals and community support for Filipino children facing hunger and food insecurity."
            if index == 0
            else {
                "Hunger & Poverty": "Prepare nutritious meals for unhoused neighbors in Manila.",
                "Education": "Provide learning kits and reading support to children.",
                "Environment": "Plant trees and restore shared green spaces.",
                "Animal Welfare": "Provide food and essential care to rescued animals.",
                "Health": "Bring basic health support to underserved families.",
            }[category]
        )
        f = Fundraiser(
            organization=organization,
            title=title,
            description=(
                "This fundraiser supports community-based feeding activities and family-centered assistance. Donations help cover meals, supplies, logistics, and partner-led outreach so more children can receive consistent support."
                if index == 0
                else impact
                + " Join our volunteers and local partners to make a practical, lasting difference."
            ),
            impact=impact,
            category=category,
            location=location,
            cover_image=image,
            goal_cents=goal * 100,
            start_date=today - timedelta(days=15),
            end_date=today + timedelta(days=45),
        )
        f.opportunity = VolunteerOpportunity(
            title=title,
            description="Help with preparation, packing, registration and community distribution alongside our experienced team.",
            requirements="Be 18 or older. Wear comfortable clothes, bring drinking water and attend the orientation.",
            slots=20,
            event_date=today + timedelta(days=14 + index),
            location=location,
        )
        db.session.add(f)
        db.session.add(
            Donation(
                user=juan,
                fundraiser=f,
                amount_cents=raised * 100,
                payment_method="GCash",
                submission_token=f"demo-community-{index}",
            )
        )
        campaigns.append(f)
    past = Fundraiser(
        organization=org,
        title="Community Feeding Drive",
        description="Together we prepared and distributed nutritious meals for families in Pasig City.",
        impact="Nutritious meals and community support.",
        category="Hunger & Poverty",
        location="Pasig City",
        cover_image="community.png",
        goal_cents=3000000,
        start_date=today - timedelta(days=60),
        end_date=today - timedelta(days=20),
        status="completed",
    )
    past.opportunity = VolunteerOpportunity(
        title=past.title,
        description="Meal preparation and distribution.",
        requirements="Attend orientation.",
        slots=30,
        event_date=today - timedelta(days=20),
        location="Pasig City",
    )
    db.session.add(past)
    db.session.add(
        Donation(
            user=juan,
            fundraiser=past,
            amount_cents=3125000,
            payment_method="Maya",
            submission_token="demo-past",
        )
    )
    for i in range(3):
        db.session.add(
            Donation(
                user=goer,
                fundraiser=campaigns[i],
                amount_cents=50000,
                payment_method="GCash",
                submission_token=f"demo-maria-{i}",
            )
        )
    db.session.add_all(
        [
            VolunteerApplication(
                user=goer,
                opportunity=campaigns[1].opportunity,
                message="I would like to help with meal preparation and distribution.",
                status="pending",
            ),
            VolunteerApplication(
                user=goer,
                opportunity=campaigns[2].opportunity,
                message="I can prepare reading kits and help with event registration.",
                status="accepted",
            ),
            VolunteerApplication(
                user=goer,
                opportunity=campaigns[3].opportunity,
                message="I can join the planting activity and help with logistics.",
                status="rejected",
            ),
            VolunteerApplication(
                user=goer,
                opportunity=past.opportunity,
                message="I helped with the community feeding drive.",
                status="accepted",
            ),
            VolunteerApplication(
                user=juan,
                opportunity=campaigns[0].opportunity,
                message="I would like to help with cooking and packing meals.",
                status="pending",
            ),
            VolunteerApplication(
                user=ana,
                opportunity=campaigns[0].opportunity,
                message="I can help with registration and food distribution.",
                status="pending",
            ),
            SavedCharity(user=goer, organization=org),
        ]
    )
    db.session.flush()
    for action, target, oid, description in [
        (
            "Demo initialized",
            "system",
            0,
            "Demo accounts and simulated records initialized.",
        ),
        ("Approve organization", "organization", org.id, "Demo foundation verified."),
        (
            "Approve organization",
            "organization",
            org2.id,
            "Demo community kitchen verified.",
        ),
        (
            "Organization registration",
            "organization",
            org3.id,
            "Registration awaiting administrator review.",
        ),
    ]:
        db.session.add(
            SystemRecord(
                actor_user_id=admin.id,
                action=action,
                target_type=target,
                target_id=oid,
                description=description,
            )
        )
    db.session.commit()


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        seed_database()
    print("Demo data is ready.")
