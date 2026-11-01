# ChariGo — Complete Flask Minimum Viable Product Development Specification

Transform the following ChariGo Figma design into a **complete, functional, responsive Minimum Viable Product using Flask**:

**Figma Reference:**
https://www.figma.com/design/0BwLZRjE0ir7x0JYysSEiT/CHARIGO_High-Fidelity?node-id=0-1&t=2JVtqqEKHv9nQAxW-1

The objective is to turn the existing ChariGo Figma prototype into a **fully working web application** while preserving the original ChariGo design language, branding, assets, interface patterns, and user experience as closely as possible.

The application must support three primary roles:

- Charity Goer
- Charity Organization
- System Administrator

The application should primarily use:

- Python
- Flask
- HTML5
- CSS3
- Vanilla JavaScript
- Jinja2
- SQLite
- Flask-SQLAlchemy

Use HTML, CSS, and Vanilla JavaScript for as much of the frontend as reasonably possible.

Do NOT use:

- React
- Vue
- Angular
- Svelte
- Tailwind
- Generic admin dashboard templates
- Unnecessary frontend frameworks

unless specifically requested.

---

# NON-NEGOTIABLE DELIVERY REQUIREMENTS

The final output must be a **complete runnable MVP**.

Do NOT provide only:

- Scaffolding
- Wireframes
- Static mockups
- Example pages
- Placeholder routes
- Empty templates
- TODO functionality
- Dead buttons
- Fake forms
- Fake database updates
- Navigation that leads nowhere

Every major visible action must work.

Do not use:

```text
TODO: Implement later
```

for any functionality that belongs to the MVP.

If something is intentionally outside the MVP scope, document it clearly in the README.

---

# FIGMA IS THE MAIN DESIGN REFERENCE

The supplied Figma file is the main visual reference for the entire application.

Preserve as closely as possible:

- Colors
- Typography
- Logo
- Photos
- Icons
- Illustrations
- Cards
- Buttons
- Navigation
- Forms
- Input fields
- Border radii
- Shadows
- Spacing
- Headers
- Bottom navigation
- Visual hierarchy
- Profile layouts
- Fundraiser layouts
- Organization layouts
- Status indicators
- Modal styles
- General proportions
- Overall ChariGo visual identity

Use the **exact original photos, logos, icons, illustrations, and visual assets from the Figma file whenever available**.

Do not substitute an existing Figma asset with:

- Random stock images
- Similar photos
- Emojis
- Generic icons
- Unrelated icons
- Different charity logos
- Completely different illustrations

If the exact asset exists in Figma, use it.

---

# DESIGN IMPROVEMENTS ARE ALLOWED — BUT ASK FIRST

You may recommend improvements when doing so significantly improves:

- Usability
- Accessibility
- Responsiveness
- Navigation
- Error prevention
- Readability
- Interaction clarity
- User feedback
- Mobile usability
- Desktop usability
- Human-Computer Interaction

However, do not silently make major visual or structural changes.

Before a substantial design modification, provide:

```text
Suggested Design Improvement

Current Figma:
[Describe current behavior.]

Potential UX Issue:
[Describe the problem.]

Recommended Change:
[Describe proposed improvement.]

Reason:
[Explain the relevant HCI principle.]

Would you like me to apply this change?
```

Minor responsive adjustments may be made without approval if they preserve the original design intent.

Do not stop all development while waiting for a design decision.

Continue implementing unaffected functionality.

---

# BEFORE CODING — COMPLETE FIGMA AUDIT REQUIRED

Before writing the main application, inspect the entire Figma file.

Do not start by implementing only the first screen.

Create a complete screen and workflow inventory.

For every relevant frame identify:

```text
Figma Frame
→ Screen/Page Name
→ User Role
→ Flask Route
→ Main Actions
→ Database Models Used
→ Navigation Destination
→ Existing/Missing State
→ Additional UI Required
```

Example:

```text
Frame: Browse Causes

Role:
Charity Goer

Route:
/causes

Actions:
- Search causes
- Open fundraiser
- Filter causes

Models:
- Organization
- Fundraiser

Navigation:
- Fundraiser Details
- History
- Profile

Missing States:
- Empty result
- No search results
```

Also identify:

- User roles
- Navigation structure
- Core workflows
- Reusable UI components
- Missing screens
- Missing tabs
- Missing confirmation dialogs
- Missing success states
- Missing error states
- Missing empty states
- Database requirements

Every meaningful Figma frame should be reviewed.

---

# DO NOT IGNORE SECONDARY FIGMA FRAMES

Review and implement appropriate:

- Profile screens
- History pages
- Organization screens
- Management screens
- Forms
- Modals
- Popups
- Alternate states
- Navigation states
- Volunteer interfaces
- Donation interfaces
- Fundraiser interfaces

If a frame is intentionally outside MVP scope, document why.

---

# CORE USER ROLES

The MVP must support:

## Charity Goer

A normal user who can:

- Browse causes
- View fundraisers
- Donate
- Apply as a volunteer
- View donation history
- View volunteer history
- Manage their profile

## Charity Organization

An organization user who can:

- Register an organization
- Manage organization profile
- Create fundraisers
- Manage fundraisers
- Edit fundraisers
- View current fundraisers
- View past fundraisers
- View volunteer requests
- Review applicants
- Accept volunteers
- Reject volunteers

## System Administrator

The administrator must be able to:

- Log In
- Manage User Accounts
- Manage Charity Organizations
- Verify / Approve Organizations
- Monitor Posted Opportunities
- Remove / Inactivate Invalid Content
- View System Records

These administrator features are REQUIRED.

---

# COMPLETE END-TO-END WORKFLOWS

Do not implement disconnected pages.

Primary workflows must work from beginning to end.

---

# CHARITY GOER WORKFLOW

```text
Register
↓
Login
↓
Charity Goer Home
↓
Browse Causes/Fundraisers
↓
View Fundraiser
↓
Donate OR Volunteer
↓
Review Action
↓
Confirm
↓
Success Feedback
↓
History Updated
```

The workflow should persist appropriate data.

---

# CHARITY ORGANIZATION WORKFLOW

```text
Register / Login
↓
Organization Registration/Profile
↓
Organization Dashboard
↓
Create Fundraiser
↓
View Current Fundraisers
↓
Manage Fundraiser
↓
View Volunteer Requests
↓
View Applicant
↓
Accept OR Reject
↓
Updated Application Status
```

---

# SYSTEM ADMINISTRATOR WORKFLOW

```text
Administrator Login
↓
Admin Dashboard
↓
Manage Users / Organizations / Opportunities
↓
Review Selected Record
↓
Perform Administrative Action
↓
Confirmation
↓
Database Updated
↓
System Record Created
↓
Updated Status Displayed
```

---

# HUMAN-COMPUTER INTERACTION REQUIREMENTS

Follow proper Human-Computer Interaction principles throughout ChariGo.

Apply principles comparable to Nielsen's usability heuristics.

---

# VISIBILITY OF SYSTEM STATUS

Users should always understand what is happening.

Include:

- Loading indicators
- Processing states
- Success messages
- Error messages
- Active navigation indicators
- Current status indicators
- Confirmation feedback

Example:

```text
Processing donation...
```

then:

```text
Donation submitted successfully.
```

---

# MATCH BETWEEN SYSTEM AND REAL WORLD

Use clear human-readable wording.

Use:

```text
Your volunteer application has been submitted.
```

instead of:

```text
Application record successfully instantiated.
```

---

# USER CONTROL AND FREEDOM

Allow users to:

- Go back
- Cancel
- Close dialogs
- Review actions
- Edit information
- Cancel destructive operations
- Return to previous pages

Do not trap users inside a workflow.

---

# CONSISTENCY

Keep similar UI elements consistent.

Examples:

- Primary buttons
- Secondary buttons
- Danger actions
- Cards
- Navigation
- Forms
- Status badges
- Alerts

---

# ERROR PREVENTION

Prevent avoidable mistakes.

Require confirmation for:

- Delete fundraiser
- Deactivate account
- Reject organization
- Remove opportunity
- Confirm donation
- Other irreversible actions

Validate required data.

Prevent duplicate submissions.

---

# RECOGNITION RATHER THAN RECALL

Display important information at the point where it is needed.

For donation confirmation show:

- Organization
- Fundraiser
- Amount
- Payment method
- Total

Do not require users to remember values from previous screens.

---

# ACCESSIBILITY

Use:

- Proper labels
- Semantic HTML
- Alt text
- Visible focus states
- Keyboard-friendly controls
- Readable text
- Appropriate heading hierarchy
- Suitable touch targets
- Sufficient contrast where possible

Preserve the ChariGo design while making reasonable accessibility improvements.

---

# RESPONSIVE DESIGN IS REQUIRED

The application must work properly on:

- Small phones
- Large phones
- Tablets
- Laptops
- Desktop monitors

Do not simply stretch the mobile Figma design.

Adapt intelligently while maintaining ChariGo's identity.

---

# MOBILE

Mobile should remain closest to the original Figma design.

Preserve:

- Portrait orientation
- Bottom navigation where present
- Single-column content
- Mobile cards
- Mobile headers
- Touch-friendly buttons

---

# TABLET

On tablets:

- Use available width appropriately
- Maintain readable line lengths
- Avoid oversized content
- Preserve the same design language

---

# LAPTOP AND DESKTOP

Larger screens may use:

- Wider content containers
- Centered page layouts
- Multi-column cards
- More efficient management lists
- Desktop-friendly navigation if approved

Do NOT transform ChariGo into an unrelated dashboard design.

---

# CSS RESPONSIVENESS

Use:

- Flexbox
- CSS Grid
- Media queries
- Relative sizing
- `max-width`
- `min-width`
- `clamp()`
- `min()`
- `max()`

Avoid excessive hard-coded absolute positioning.

Example:

```css
.container {
    width: min(100% - 2rem, 1200px);
    margin-inline: auto;
}
```

---

# MISSING SCREENS MAY BE CREATED

If an important workflow lacks a dedicated Figma frame, create the missing screen.

Examples:

- Confirmation dialogs
- Success messages
- Error states
- Empty states
- Missing tabs
- Missing navigation pages
- Payment confirmation
- Delete confirmation
- Administrator screens

Any new screen must look like it naturally belongs in ChariGo.

Match:

- Fonts
- Colors
- Buttons
- Cards
- Icons
- Spacing
- Border radius
- Shadows
- Forms
- Navigation
- General proportions

---

# FLASK PROJECT STRUCTURE

Use an organized beginner-friendly Flask structure.

Recommended:

```text
charigo/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── seed.py
│
├── templates/
│   ├── base.html
│   │
│   ├── components/
│   │   ├── navbar.html
│   │   ├── bottom_nav.html
│   │   ├── fundraiser_card.html
│   │   ├── modal.html
│   │   ├── status_badge.html
│   │   └── flash_messages.html
│   │
│   ├── auth/
│   ├── goer/
│   ├── organization/
│   └── admin/
│
├── static/
│   ├── css/
│   │   ├── style.css
│   │   ├── components.css
│   │   └── responsive.css
│   │
│   ├── js/
│   │   ├── main.js
│   │   ├── forms.js
│   │   └── modals.js
│   │
│   ├── images/
│   ├── icons/
│   ├── logos/
│   └── uploads/
│
├── models/
├── routes/
└── instance/
```

A different structure may be used if it is cleaner.

Do not overengineer the project.

---

# JINJA2

Use reusable templates.

Example:

```jinja2
{% extends "base.html" %}
```

Create reusable components for:

- Navigation
- Headers
- Cards
- Alerts
- Modals
- Forms
- Status badges

Avoid unnecessary duplication.

---

# DATABASE

Use:

**SQLite + Flask-SQLAlchemy**

The database should be easy to:

- Initialize
- Seed
- Reset
- Run locally

---

# FINALIZE THE DATABASE SCHEMA EARLY

After completing the Figma audit:

1. Identify required entities.
2. Identify relationships.
3. Identify fields.
4. Identify role permissions.
5. Identify statuses.
6. Confirm that all workflows can be supported.

Avoid repeatedly changing the schema midway through development.

---

# RECOMMENDED USER MODEL

Possible fields:

```text
id
first_name
last_name
email
password_hash
role
profile_image
account_status
created_at
updated_at
```

Roles:

```text
charity_goer
charity_organization
administrator
```

Possible account statuses:

```text
active
inactive
suspended
```

---

# ORGANIZATION MODEL

Possible fields:

```text
id
user_id
organization_name
logo
description
mission
portfolio
registration_date
verification_status
rejection_reason
created_at
updated_at
```

Possible statuses:

```text
pending
verified
rejected
inactive
```

---

# FUNDRAISER MODEL

Possible fields:

```text
id
organization_id
title
description
cover_image
goal_amount
amount_raised
start_date
end_date
status
category
location
created_at
updated_at
```

Possible statuses:

```text
active
completed
inactive
removed
```

---

# DONATION MODEL

Possible fields:

```text
id
user_id
fundraiser_id
amount
payment_method
status
created_at
```

---

# VOLUNTEER OPPORTUNITY MODEL

Possible fields:

```text
id
fundraiser_id
title
description
slots
requirements
date
location
status
created_at
updated_at
```

---

# VOLUNTEER APPLICATION MODEL

Possible fields:

```text
id
user_id
opportunity_id
message
status
created_at
updated_at
```

Statuses:

```text
pending
accepted
rejected
```

---

# SYSTEM RECORD MODEL

Implement a simple system/audit record model.

Possible structure:

```text
SystemRecord

id
actor_user_id
action
target_type
target_id
description
created_at
```

Do not store:

- Passwords
- Payment credentials
- Other unnecessary sensitive information

---

# DATABASE RELATIONSHIPS

Examples:

```text
User
1 → many Donations

User
1 → many VolunteerApplications

Organization
1 → many Fundraisers

Fundraiser
1 → many Donations

Fundraiser
1 → many VolunteerOpportunities

VolunteerOpportunity
1 → many VolunteerApplications
```

---

# AUTHENTICATION

Implement:

- Registration
- Login
- Logout
- Password hashing
- Session-based authentication
- Protected routes

Never store plain-text passwords.

Use Werkzeug or another trusted Flask-compatible hashing method.

---

# ROLE-BASED AUTHORIZATION

Authorization must happen on the server.

Do not rely only on hiding buttons.

Ensure that users cannot manually access unauthorized URLs.

Example administrator protection:

```python
if current_user.role != "administrator":
    abort(403)
```

or use an equivalent reusable decorator.

---

# CHARITY GOER FEATURES

Implement:

- Home
- Browse causes
- Search
- Filter where useful
- View fundraiser
- Donate
- Volunteer
- Donation history
- Volunteer history
- Profile management

---

# DONATION WORKFLOW

Use a simulated payment workflow unless real payment integration is specifically requested.

```text
View Fundraiser
↓
Choose Donation Amount
↓
Choose Mock Payment Method
↓
Review Donation
↓
Confirm
↓
Donation Saved
↓
Fundraiser Amount Updated
↓
History Updated
↓
Success Message
```

Do not collect real card credentials.

Clearly identify simulated payment where appropriate.

---

# FUNDRAISER PROGRESS

Calculate dynamically:

```text
amount_raised / goal_amount × 100
```

Protect against zero goals.

Example:

```text
₱35,000 raised of ₱50,000 goal
```

---

# VOLUNTEER WORKFLOW

```text
View Fundraiser
↓
View Volunteer Opportunity
↓
Submit Application
↓
Status = Pending
↓
Organization Reviews Application
↓
Accept OR Reject
↓
Status Updated
↓
User History Updated
```

Prevent duplicate applications where appropriate.

---

# CHARITY ORGANIZATION FEATURES

Implement:

- Organization registration
- Organization profile
- Dashboard
- Create fundraiser
- View current fundraisers
- Manage fundraiser
- Edit fundraiser
- Delete/deactivate fundraiser
- View past fundraisers
- Volunteer request list
- Applicant profile
- Accept volunteer
- Reject volunteer

Organizations must not modify another organization's data.

---

# SYSTEM ADMINISTRATOR MODULE — REQUIRED

The System Administrator functionality is mandatory.

The administrator must be able to:

```text
✓ Log In
✓ Manage User Accounts
✓ Manage Charity Organizations
✓ Verify / Approve Organizations
✓ Monitor Posted Opportunities
✓ Remove / Inactivate Invalid Content
✓ View System Records
```

These use cases must be implemented as actual Flask functionality backed by the database.

---

# ADMINISTRATOR UI MUST FOLLOW FIGMA

Dedicated admin frames may not currently exist in the Figma file.

That does NOT permit a completely unrelated design.

The Administrator UI must extend ChariGo's existing visual language.

Use:

- Same colors
- Same typography
- Same card style
- Same button styling
- Same rounded shapes
- Same icons or matching icon language
- Same shadows
- Same spacing
- Same input styling
- Same status styles

Do NOT introduce:

- Generic Bootstrap admin templates
- Generic dashboard themes
- Random sidebars
- Completely different typography
- Unrelated color systems

The admin interface should look like it was originally designed as part of ChariGo.

---

# ADMINISTRATOR LOGIN

System Administrators should not register through the public user registration process.

Create the administrator through:

- Seed data
- Initialization
- Controlled setup

Include a demo administrator account.

Use hashed passwords.

Unauthorized users must not be able to access:

```text
/admin
/admin/users
/admin/organizations
/admin/opportunities
/admin/records
```

---

# ADMINISTRATOR DASHBOARD

Create a dashboard providing quick access to administration.

Possible summary cards:

- Total users
- Total Charity Goers
- Total organizations
- Pending organizations
- Active fundraisers
- Active volunteer opportunities
- Inactive content
- Recent administrative activity

Do not overcrowd the dashboard.

Use strong visual hierarchy.

---

# ADMIN — MANAGE USER ACCOUNTS

Create a User Management page.

Administrator should be able to:

- View users
- Search users
- Filter by role
- Filter by status
- View user details
- View role
- View account status
- Deactivate account
- Reactivate account

Possible statuses:

```text
Active
Inactive
Suspended
```

Prefer deactivation over destructive deletion.

---

# USER MANAGEMENT INFORMATION

Possible fields:

```text
Name
Email
Role
Account Status
Registration Date
Actions
```

On mobile, convert wide tables into responsive cards if necessary.

---

# USER DETAILS

Display relevant information such as:

- Name
- Email
- Profile image
- Role
- Registration date
- Account status

For Charity Goers, optionally show:

- Donation count
- Volunteer applications

For Charity Organizations, optionally show:

- Organization
- Verification status
- Fundraiser count

---

# USER DEACTIVATION CONFIRMATION

Example:

```text
Deactivate Account?

Are you sure you want to deactivate this account?

The user will no longer be able to access ChariGo until reactivated.

Cancel     Deactivate
```

After completion:

```text
User account successfully deactivated.
```

Create an audit record.

---

# ADMIN — MANAGE CHARITY ORGANIZATIONS

Administrator should be able to:

- View organizations
- Search organizations
- Filter organizations
- View profile
- Review registration information
- Approve organization
- Reject organization
- Deactivate organization
- Reactivate organization where appropriate

Possible statuses:

```text
Pending
Verified
Rejected
Inactive
```

---

# ORGANIZATION LIST INFORMATION

Possible information:

```text
Organization Name
Logo
Registration Date
Verification Status
Number of Fundraisers
Actions
```

Reuse the ChariGo organization card visual style where appropriate.

---

# VERIFY / APPROVE ORGANIZATIONS

Complete workflow:

```text
Organization Registers
↓
Status = Pending
↓
Administrator Opens Pending Organizations
↓
Reviews Organization
↓
Approve OR Reject
↓
Status Updated
↓
Audit Record Created
↓
Organization Access Updated
```

---

# ORGANIZATION REVIEW PAGE

Display relevant information such as:

- Logo
- Organization name
- Registration date
- About
- Mission
- Portfolio
- Contact information where appropriate
- Submitted verification information
- Status

Do not invent unnecessary sensitive verification requirements.

---

# APPROVE ORGANIZATION

Require confirmation.

Example:

```text
Approve Organization?

You are about to verify this organization.

Once approved, the organization may access verified organization features.

Cancel     Approve
```

Then:

```text
Organization successfully verified.
```

Update the database and system record.

---

# REJECT ORGANIZATION

Allow a rejection reason where useful.

Example:

```text
Reject Organization?

Reason:
[________________________________]

Cancel     Reject
```

Persist the status and reason appropriately.

---

# ADMIN — MONITOR POSTED OPPORTUNITIES

Administrators must be able to monitor:

- Fundraisers
- Donation campaigns
- Volunteer opportunities

Create an Opportunity Monitoring page.

Allow:

- View
- Search
- Filter
- Open details
- View organization
- View current status
- Deactivate invalid content

Possible information:

```text
Opportunity Title
Organization
Type
Date Posted
Status
Actions
```

Types:

```text
Fundraiser
Volunteer Opportunity
```

---

# OPPORTUNITY DETAILS

Display relevant information such as:

- Image
- Title
- Organization
- Description
- Category
- Location
- Dates
- Goal
- Volunteer requirements
- Current status

Reuse existing Figma fundraiser/opportunity components.

---

# ADMIN — REMOVE / INACTIVATE INVALID CONTENT

Prefer soft deletion.

Possible statuses:

```text
Active
Inactive
Removed
```

Administrators may deactivate content such as:

- Invalid fundraiser
- Misleading opportunity
- Improper volunteer listing
- Content from an invalid organization

The administrator makes the decision.

Do not automatically classify legitimate content as invalid.

---

# CONTENT DEACTIVATION CONFIRMATION

Example:

```text
Deactivate Opportunity?

This opportunity will no longer be visible to Charity Goers.

The record will remain available for system auditing.

Cancel     Deactivate
```

After confirmation:

1. Update database status.
2. Hide it from public listings.
3. Preserve the record.
4. Create system record.
5. Show feedback.

Example:

```text
Opportunity successfully deactivated.
```

---

# ADMINISTRATIVE ACTION REASONS

Where appropriate allow administrators to record a reason for:

- User deactivation
- Organization rejection
- Organization deactivation
- Opportunity removal

Keep this simple for the MVP.

---

# ADMIN — VIEW SYSTEM RECORDS

Create a System Records page.

Possible records:

- User registration
- Organization registration
- Organization approval
- Organization rejection
- Fundraiser creation
- Volunteer opportunity creation
- User deactivation
- Organization deactivation
- Opportunity deactivation
- Administrator actions

Display useful information such as:

```text
Date / Time
Action
Actor
Affected Record
Result
```

---

# AUDIT IMPORTANT ADMIN ACTIONS

System records should be created for actions such as:

```text
Approve Organization
Reject Organization
Deactivate Organization
Reactivate Organization
Deactivate User
Reactivate User
Deactivate Opportunity
Reactivate Opportunity
```

---

# ADMINISTRATOR NAVIGATION

Possible sections:

```text
Dashboard
Users
Organizations
Opportunities
System Records
Profile / Logout
```

Derive the exact design from ChariGo.

Do not automatically create a generic desktop sidebar.

---

# ADMINISTRATOR HCI

Apply the same HCI rules.

Especially:

## Error Prevention

Confirm before:

- Deactivating users
- Rejecting organizations
- Deactivating organizations
- Removing content

## Visibility

Clearly display:

```text
Pending
Verified
Rejected
Active
Inactive
Removed
```

## User Control

Allow cancellation before confirmation.

Where appropriate support:

```text
Deactivate → Reactivate
```

## Feedback

Examples:

```text
Organization approved successfully.
```

```text
User account deactivated.
```

```text
Opportunity removed from public listings.
```

---

# ADMINISTRATOR SEARCH AND FILTERING

Users:

```text
Role
Account Status
```

Organizations:

```text
Pending
Verified
Rejected
Inactive
```

Opportunities:

```text
Fundraiser
Volunteer Opportunity
Active
Inactive
Removed
```

---

# ADMIN EMPTY STATES

Examples:

```text
No organizations are awaiting verification.
```

```text
No inactive opportunities found.
```

```text
No system records match your search.
```

Never show a blank broken page.

---

# COMPLETE ADMINISTRATOR WORKFLOWS

## Organization Approval

```text
Organization Registration
↓
Pending Verification
↓
Admin Login
↓
Organizations
↓
Open Pending Organization
↓
Review
↓
Approve
↓
Database Updated
↓
Audit Record Created
↓
Organization = Verified
```

## Invalid Opportunity Removal

```text
Organization Posts Opportunity
↓
Opportunity Becomes Visible
↓
Admin Opens Opportunities
↓
Reviews Opportunity
↓
Deactivate
↓
Confirmation
↓
Status Updated
↓
Removed From Public Listings
↓
Audit Record Created
```

## User Management

```text
Admin Login
↓
Users
↓
Open User
↓
Deactivate
↓
Confirmation
↓
Account Status Updated
↓
User Access Restricted
↓
Audit Record Created
```

Reactivation must restore appropriate access.

---

# FORMS

Use:

- Visible labels
- Correct input types
- Helpful placeholders
- Inline validation
- Clear errors
- Logical grouping
- Appropriate mobile keyboard types

Do not use placeholder text as the only label.

---

# FRONTEND AND BACKEND VALIDATION

Validate on both:

- JavaScript
- Flask

Validate:

- Required fields
- Email format
- Password requirements
- Donation amounts
- Numeric values
- Dates
- File type
- File size where appropriate
- Text lengths

Never trust only client-side validation.

---

# FLASH / FEEDBACK MESSAGES

Examples:

```text
Fundraiser created successfully.
```

```text
Volunteer application submitted.
```

```text
Incorrect email or password.
```

```text
Organization approved successfully.
```

Style feedback using the ChariGo visual system.

---

# LOADING STATES

For submissions:

- Disable the button after click.
- Show processing state.
- Prevent duplicate submissions.

Example:

```text
Processing...
```

---

# BUTTON STATES

Support:

- Default
- Hover
- Active
- Focus
- Disabled
- Loading

Disabled controls should look disabled.

---

# TOUCH TARGETS

Where possible, provide mobile interaction areas around:

```text
44 × 44 px
```

without unnecessarily altering the visual design.

---

# NO DEAD ENDS

Primary controls must function.

Verify:

- Navigation
- Buttons
- Back actions
- Forms
- Tabs
- Cancel
- Confirm
- History pages
- Management actions

Avoid:

```html
<a href="#">
```

for real navigation unless handled by JavaScript.

---

# NO FAKE CORE FUNCTIONALITY

Do not simulate database features using only:

```javascript
alert("Success");
```

For example, when a donation succeeds:

- Create Donation record.
- Associate user.
- Associate fundraiser.
- Update amount raised.
- Update donation history.
- Update fundraiser progress.
- Show success feedback.

When an application is accepted:

- Update application status.
- Show new status to organization.
- Show new status to Charity Goer.

---

# DATA CONSISTENCY

Data should stay consistent across pages.

If an organization creates:

```text
Community Food Drive
Goal: ₱100,000
```

it should appear consistently on:

- Organization Dashboard
- Browse
- Fundraiser Details
- Manage Fundraiser
- Donation Page

Changes should propagate appropriately.

---

# IMAGE UPLOADS

Validate:

- Extensions
- MIME/type where practical
- Safe filenames
- File size
- Upload location

Support:

- Profile image
- Organization logo
- Fundraiser cover

Use original Figma assets for seeded demo data where available.

---

# SECURITY BASICS

Implement:

- Password hashing
- Session security
- Backend validation
- Role authorization
- Ownership checks
- Safe uploads
- Error handling
- Environment variables for secrets

Do not expose production secrets.

---

# JAVASCRIPT SHOULD ENHANCE FLASK

Use JavaScript for:

- Modals
- Tabs
- Dynamic totals
- Loading states
- Client-side validation
- Search filtering
- Confirmation dialogs
- UI interaction

Critical data operations must still be processed and validated by Flask.

---

# SEMANTIC HTML

Use proper elements:

```html
<header>
<nav>
<main>
<section>
<article>
<form>
<label>
<button>
<footer>
```

Do not build everything with meaningless `<div>` elements.

---

# PRESERVE FIGMA ASSETS

Use exact Figma assets whenever available:

- ChariGo logo
- Charity images
- Organization logos
- Profile images
- Fundraiser images
- Icons
- Decorative graphics
- Illustrations

If an asset cannot be extracted:

1. Keep intended size.
2. Keep aspect ratio.
3. Keep positioning.
4. Use clearly named temporary asset.
5. Document replacement requirement.

---

# NEW COMPONENTS MUST LOOK LIKE CHARIGO

Any new interface should inherit:

- Fonts
- Colors
- Button design
- Cards
- Border radius
- Spacing
- Icons
- Shadows
- Form styles

Do not use visually unrelated browser defaults or Bootstrap-like components.

---

# DEMO DATA IS REQUIRED

Seed realistic demo content.

Include:

- Multiple Charity Goers
- Multiple organizations
- Active fundraisers
- Completed fundraisers
- Volunteer opportunities
- Pending volunteer applications
- Accepted applications
- Rejected applications
- Donations
- Pending organization verification
- Verified organizations
- Some system records

This ensures the project can immediately be demonstrated.

---

# DEMO ACCOUNTS

Provide at least one account for each implemented role.

Example:

```text
Charity Goer
Email: goer@example.com
Password: documented in README

Organization
Email: organization@example.com
Password: documented in README

System Administrator
Email: admin@example.com
Password: documented in README
```

Store passwords as hashes.

---

# BEGINNER-FRIENDLY CODE

Prefer:

- Clear route names
- Descriptive variables
- Straightforward SQLAlchemy models
- Useful comments
- Logical folder structure

Avoid unnecessary abstraction.

---

# IMPLEMENTATION ORDER

## Phase 0 — Figma Audit

- Inspect all relevant frames.
- Create screen inventory.
- Identify roles.
- Identify workflows.
- Identify missing screens.
- Identify reusable components.
- Finalize schema.

## Phase 1 — Foundation

- Flask setup
- Configuration
- Database
- Seed data
- Authentication
- Authorization
- Base templates

## Phase 2 — Charity Goer

- Home
- Browse
- Fundraiser detail
- Donate
- Volunteer
- History
- Profile

## Phase 3 — Charity Organization

- Registration
- Profile
- Dashboard
- Create fundraiser
- Manage fundraiser
- Edit fundraiser
- Volunteer requests
- Applicant details
- Past fundraisers

## Phase 4 — System Administrator

- Admin login
- Dashboard
- User management
- Organization management
- Verification
- Opportunity monitoring
- Content deactivation
- System records

## Phase 5 — Missing UX States

- Confirmations
- Success screens
- Errors
- Empty states
- Missing navigation screens

## Phase 6 — Responsive / HCI Review

- Mobile
- Tablet
- Laptop
- Desktop
- Accessibility
- Validation
- Feedback
- Error prevention

---

# README REQUIRED

Create a README containing:

- Project description
- Features
- Stack
- Folder structure
- Installation
- Virtual environment setup
- Dependencies
- Database initialization
- Seed instructions
- Running instructions
- Demo accounts
- Roles
- MVP limitations

Example:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
```

Then initialize/seed database.

Then:

```bash
python app.py
```

Document the actual final commands.

---

# FINAL TESTING — AUTHENTICATION

Test:

- Registration
- Login
- Logout
- Invalid login
- Duplicate registration
- Protected routes
- Role restrictions
- Inactive accounts

---

# FINAL TESTING — CHARITY GOER

Test:

- Browse
- Search
- Filter
- View fundraiser
- Donate
- Confirm donation
- Donation stored
- History updated
- Volunteer
- Volunteer history
- Profile

---

# FINAL TESTING — CHARITY ORGANIZATION

Test:

- Registration
- Organization profile
- Create fundraiser
- Edit fundraiser
- Delete/deactivate confirmation
- Current fundraisers
- Past fundraisers
- Volunteer requests
- Applicant details
- Accept applicant
- Reject applicant

---

# FINAL TESTING — SYSTEM ADMINISTRATOR

Test:

## Authentication

- Admin login works.
- Non-admin cannot access admin routes.
- Inactive admin cannot use protected functions.

## User Management

- View users.
- Search users.
- Filter users.
- View details.
- Deactivate.
- Confirm.
- Reactivate.
- Status persists.

## Organization Management

- View organizations.
- View pending.
- Review details.
- Approve.
- Reject.
- Deactivate where appropriate.
- Status persists.

## Opportunity Monitoring

- View opportunities.
- View fundraiser details.
- View volunteer opportunity.
- Deactivate invalid content.
- Confirmation works.
- Public listing updates.
- Database record remains.

## System Records

- Records display correctly.
- Admin actions create records.
- Sensitive information is not logged.

---

# RESPONSIVE TESTING

Test around:

```text
320px
375px
390px
430px
768px
1024px
1366px
1920px
```

Verify:

- No unwanted horizontal scrolling
- No overlap
- No hidden actions
- No distorted images
- No unreadable text
- No content hidden beneath navigation
- Forms remain usable
- Cards remain readable
- Navigation remains functional

---

# FINAL VISUAL REVIEW

Compare every implemented screen against the original Figma design.

The result should feel like:

> “The original ChariGo Figma prototype has become a functioning web application.”

Not:

> “A different website loosely inspired by ChariGo.”

---

# FINAL FUNCTIONAL AUDIT

Before declaring completion, verify that there are no knowingly:

- Broken primary links
- Dead buttons
- Empty templates
- Missing routes
- Fake submissions
- TODO core features
- Unauthorized access paths
- Inconsistent records
- Missing confirmations
- Broken responsive layouts

---

# FINAL MVP REQUIRED USE CASES

The finished ChariGo MVP must support:

## CHARITY GOER

```text
✓ Register / Login
✓ Browse Causes
✓ View Fundraisers
✓ Donate
✓ Volunteer
✓ View Donation History
✓ View Volunteer History
✓ Manage Profile
```

## CHARITY ORGANIZATION

```text
✓ Register / Login
✓ Manage Organization Profile
✓ Create Fundraisers
✓ View Current Fundraisers
✓ Manage Fundraisers
✓ Edit Fundraisers
✓ View Volunteer Requests
✓ View Applicant Profiles
✓ Accept / Reject Applicants
✓ View Past Fundraisers
```

## SYSTEM ADMINISTRATOR

```text
✓ Log In
✓ Manage User Accounts
✓ Manage Charity Organizations
✓ Verify / Approve Organizations
✓ Monitor Posted Opportunities
✓ Remove / Inactivate Invalid Content
✓ View System Records
```

---

# FINAL PRIORITY ORDER

When making development decisions, prioritize:

1. **Core workflows must actually work.**
2. **The application must be immediately demonstrable.**
3. **Database state must update correctly.**
4. **Role permissions must be enforced.**
5. **User actions must be clear and safe.**
6. **Proper HCI principles must be followed.**
7. **The application must work across mobile, tablet, laptop, and desktop.**
8. **The original Figma visual identity must be preserved.**
9. **Exact original Figma assets should be used whenever available.**
10. **New screens must look native to ChariGo.**
11. **Major design changes should be proposed before implementation.**
12. **Unrelated development should continue while waiting for design approval.**
13. **Use HTML, CSS, and Vanilla JavaScript for the frontend as much as possible.**
14. **Use Flask for business logic, persistence, authentication, and authorization.**
15. **Keep the architecture understandable for students.**
16. **Do not overengineer the MVP.**

---

# MOST IMPORTANT INSTRUCTION

Do not redesign ChariGo into a different application.

Use the Figma file as the foundation for the entire system.

You are allowed to make ChariGo:

- More functional
- More responsive
- More accessible
- More consistent
- Easier to use
- Safer
- Better suited to desktop and mobile

but improvements must preserve ChariGo's identity.

When a screen is missing, create it as though it were originally designed by the same team that created the Figma prototype.

When an Administrator page is missing, derive it from the same Figma visual language instead of introducing a generic admin dashboard.

When a significant visual change is desirable, recommend it and ask before implementing it whenever possible.

Do not stop unrelated development while awaiting approval.

The final result must be a:

**complete, responsive, functional, database-backed, role-based, intuitive Flask MVP for ChariGo that works across phones, tablets, laptops, and desktops while remaining visually faithful to the original Figma design.**

The finished application must not merely look functional.

**IT MUST ACTUALLY WORK.**
