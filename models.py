from datetime import date, datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint

db = SQLAlchemy()


def now():
    return datetime.now(timezone.utc)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    account_status = db.Column(db.String(20), nullable=False, default="active")
    image = db.Column(db.String(100))
    phone = db.Column(db.String(40), default="")
    location = db.Column(db.String(150), default="")
    availability = db.Column(db.String(150), default="")
    skills = db.Column(db.Text, default="")
    experience = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    organization = db.relationship(
        "Organization", back_populates="owner", uselist=False
    )
    donations = db.relationship("Donation", back_populates="user")
    applications = db.relationship("VolunteerApplication", back_populates="user")
    saved_charities = db.relationship("SavedCharity", back_populates="user")

    @property
    def initials(self):
        return "".join(s[0] for s in self.name.split()[:2]).upper()


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False
    )
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    mission = db.Column(db.Text, default="")
    portfolio = db.Column(db.Text, default="")
    portfolio_file = db.Column(db.String(100))
    logo = db.Column(db.String(100))
    banner = db.Column(db.String(100), default="angat-buhay.jpg")
    contact_email = db.Column(db.String(254), default="")
    phone = db.Column(db.String(40), default="")
    location = db.Column(db.String(150), default="")
    verification_status = db.Column(db.String(20), nullable=False, default="pending")
    rejection_reason = db.Column(db.String(1000), default="")
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    owner = db.relationship("User", back_populates="organization")
    fundraisers = db.relationship("Fundraiser", back_populates="organization")

    @property
    def initials(self):
        return "".join(s[0] for s in self.name.split()[:2]).upper()

    @property
    def public(self):
        return (
            self.verification_status == "verified"
            and self.owner.account_status == "active"
        )


class Fundraiser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organization.id"), nullable=False
    )
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    impact = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    cover_image = db.Column(db.String(100), default="children.png", nullable=False)
    goal_cents = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    moderation_status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    organization = db.relationship("Organization", back_populates="fundraisers")
    donations = db.relationship("Donation", back_populates="fundraiser")
    opportunity = db.relationship(
        "VolunteerOpportunity", back_populates="fundraiser", uselist=False
    )
    __table_args__ = (
        CheckConstraint("goal_cents > 0"),
        CheckConstraint("end_date >= start_date"),
    )

    @property
    def raised_cents(self):
        return sum(d.amount_cents for d in self.donations)

    @property
    def progress(self):
        return (
            min(100, round(self.raised_cents / self.goal_cents * 100))
            if self.goal_cents
            else 0
        )

    @property
    def public(self):
        return (
            self.organization.public
            and self.moderation_status == "active"
            and self.status != "inactive"
        )

    @property
    def accepting(self):
        return (
            self.public
            and self.status == "active"
            and self.start_date <= date.today() <= self.end_date
        )

    @property
    def display_status(self):
        if self.moderation_status != "active":
            return self.moderation_status
        if self.status == "active" and self.end_date < date.today():
            return "completed"
        if self.status == "active" and self.start_date > date.today():
            return "upcoming"
        return self.status


class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    fundraiser_id = db.Column(
        db.Integer, db.ForeignKey("fundraiser.id"), nullable=False
    )
    amount_cents = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.String(40), nullable=False)
    anonymous = db.Column(db.Boolean, default=False, nullable=False)
    submission_token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    user = db.relationship("User", back_populates="donations")
    fundraiser = db.relationship("Fundraiser", back_populates="donations")
    __table_args__ = (CheckConstraint("amount_cents > 0"),)

    @property
    def reference(self):
        return f"CG-{self.created_at:%Y%m%d}-{self.id:06d}"


class VolunteerOpportunity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fundraiser_id = db.Column(
        db.Integer, db.ForeignKey("fundraiser.id"), unique=True, nullable=False
    )
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    slots = db.Column(db.Integer, nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False)
    fundraiser = db.relationship("Fundraiser", back_populates="opportunity")
    applications = db.relationship("VolunteerApplication", back_populates="opportunity")
    __table_args__ = (CheckConstraint("slots > 0"),)

    @property
    def accepted_count(self):
        return sum(a.status == "accepted" for a in self.applications)

    @property
    def available(self):
        return (
            self.status == "active"
            and self.fundraiser.accepting
            and self.event_date >= date.today()
        )


class VolunteerApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    opportunity_id = db.Column(
        db.Integer, db.ForeignKey("volunteer_opportunity.id"), nullable=False
    )
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now, nullable=False)
    user = db.relationship("User", back_populates="applications")
    opportunity = db.relationship("VolunteerOpportunity", back_populates="applications")
    __table_args__ = (UniqueConstraint("user_id", "opportunity_id"),)


class SavedCharity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    organization_id = db.Column(
        db.Integer, db.ForeignKey("organization.id"), nullable=False
    )
    user = db.relationship("User", back_populates="saved_charities")
    organization = db.relationship("Organization")
    __table_args__ = (UniqueConstraint("user_id", "organization_id"),)


class SystemRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(40), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    actor = db.relationship("User")
