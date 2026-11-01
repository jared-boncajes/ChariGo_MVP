# ChariGo

A runnable Flask MVP that connects Charity Goers, verified charity organizations and system administrators. Built from the supplied ChariGo Figma archive with its original photos, clover logo, vector icons, Inter typography and pink/green visual system. No frontend framework, CDN, payment provider or external service is required at runtime.

## Run locally

Requires Python 3.12 (tested), or a compatible Python 3.10+ installation with pip.

```bash
python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows Command Prompt
.venv\Scripts\activate.bat
```

From the project directory:

```bash
python -m pip install -r requirements.lock
flask --app app:create_app init-db
flask --app app:create_app seed
python app.py
```

Open the local server shown in the terminal (default port 5000). The cloud onboarding UI does not provide a public web preview; the app has been validated with local HTTP requests and Chromium. `HOST` and `PORT` can change the listening address. Debug mode is off by default.

The database is created in `instance/charigo.db`. The seed command is safe to repeat: it preserves existing data. To intentionally delete all local records and restore the demo, run `flask --app app:create_app reset-db` and answer its confirmation prompt. Back up `instance/` before resetting; it also contains uploaded files and the local session key.

`requirements.lock` pins the exact installed runtime and test dependencies. `requirements.txt` contains the direct application dependencies; `requirements-dev.txt` adds pytest when refreshing dependencies intentionally. Browser checks additionally need Playwright and Chromium; they are not application dependencies.

## Demo accounts

All demo accounts use **ChariGo123!**. Passwords are stored as Werkzeug scrypt hashes.

| Role | Email | Use |
|---|---|---|
| Charity Goer | goer@example.com | Maria Santos; donation and volunteer histories, saved charity |
| Organization | organization@example.com | Verified Angat Buhay Foundation; campaign and applicant management |
| System Administrator | admin@example.com | User/organization/content moderation and system records |
| Organization | iwas@example.com | A second verified organization, useful for demonstrating ownership restrictions |
| Organization | pending@example.com | Pending registration for administrator approval/rejection |
| Charity Goer | juan@example.com | Volunteer applicant with pending request |
| Charity Goer | ana@example.com | A second pending applicant |

These are local demonstration accounts. Do not expose a seeded demo database publicly with these passwords.

## Working workflows

- **Charity Goer:** select role → register → log in → browse/search by category, organization, location or volunteer availability → open fundraiser → select a simulated one-time donation → review amount/method/total → confirm → persistent receipt and updated progress/history. Volunteer applications also have a review step, pending state, duplicate protection and live acceptance/rejection in history. Edit personal information, photo, skills and availability. Save/unsave charities.
- **Organization:** register → complete official organization details and optional portfolio → pending verification → administrator approval → create fundraiser with optional volunteer opportunity → view current/past campaigns → edit campaign and volunteer details → review applicants and their profiles → confirm accept/reject. Completion or deactivation closes a campaign while preserving donations and applications.
- **Administrator:** log in with seeded admin account → search/filter users, organizations or opportunities → review a record → confirm an action → see changed access/visibility and a new audit record. Supports user deactivation/reactivation; organization approval, rejection, deactivation and reactivation; independent fundraiser and volunteer opportunity moderation; searchable system records. An administrator cannot deactivate their own account. Public registration cannot create administrators.

Verified organization features are server-enforced. A pending, rejected or inactive organization can update its profile but cannot create/edit campaigns or review applicants. Rejected organizations resubmit by updating their profile. Inactive organizations need administrator reactivation. Existing user sessions are invalidated on their next request after account deactivation. Inactive organization accounts hide their campaigns from public listings.

## Data and security

SQLite and Flask-SQLAlchemy provide eight small models: User, Organization, Fundraiser, Donation, VolunteerOpportunity, VolunteerApplication, SavedCharity and SystemRecord. Money is stored as integer centavos. Raised amounts and progress derive from the actual donation rows; no separate total can drift out of sync. Volunteer applications have a database uniqueness constraint, donation confirmations have unique submission tokens, and volunteer acceptance uses a serialized SQLite transaction to enforce available slots.

All writes use POST and CSRF tokens, passwords are hashed, and server-side role and ownership checks protect every private route. Sessions use HttpOnly and SameSite=Lax cookies. The browser receives a restrictive Content Security Policy, frame protection and MIME sniffing protection. Authenticated responses are not cached. Users see recoverable messages for validation, permission, missing records, file size and database errors.

Images accept only real decoded PNG/JPEG files up to 3 MB and 25 megapixels, are resized/re-encoded to JPEG with random filenames, and live under `instance/uploads/`. Portfolio uploads accept PDF files up to 10 MB (signature and extension checked), live outside public static files and are served as downloads only to their owning organization and administrators. A full multipart request is limited to 14 MB. Portfolio text is also supported. PDFs are not malware-scanned; handle untrusted documents appropriately before production use.

For local development a random session signing key is generated once in the ignored `instance/session.key` with restricted file permissions. Set a securely generated **SECRET_KEY** environment variable for deployments. Optional **DATABASE_URL** overrides the default SQLite connection. Set **COOKIE_SECURE=1** behind HTTPS. Never commit secrets or upload files to Git. Displayed audit times use Asia/Manila; stored timestamps use UTC.

## Structure

```text
app.py                 App factory, configuration, CSRF, security headers, CLI
models.py              SQLAlchemy models and shared derived state
common.py              Authorization, validation, uploads, audit helpers
seed.py                Repeatable demonstration data
routes/
  auth.py              Registration, login and logout
  goer.py              Browse, donations, volunteering, histories, profiles
  organization.py      Organization, campaign and applicant management
  admin.py             Review, moderation, account management and audit log
templates/             Jinja pages and reusable component macros
static/
  css/style.css        Figma tokens, responsive styles and component states
  js/main.js           Native form validation, dialogs and processing feedback
  images/              Original extracted Figma assets
  icons/               Original Figma vector exports
  fonts/               Locally served Inter, with its font license
tests/                 Isolated database workflow and authorization tests
docs/                  Figma audit, frame inventory, assets and specification
instance/              Ignored local database, uploads and session key
```

## Design audit and scope

See [docs/FIGMA_AUDIT.md](docs/FIGMA_AUDIT.md) for all 25 application-frame mappings, component states, schema, missing UI and design decisions. [docs/figma-inventory.json](docs/figma-inventory.json) records every top-level frame/component with its original Figma ID and text. The administrator screens extend the same cards, buttons, forms and colors; no unrelated dashboard template or sidebar is introduced. Mobile bottom navigation remains present; wider layouts use centered content and grids.

[docs/ASSETS.md](docs/ASSETS.md) lists the original image hashes and exported vector sources. Images remain the exact supplied bytes. Inter is served locally under its included OFL license. Use of the supplied charity names, photos and branding is for this prototype; no organizational endorsement is claimed.

MVP limits:

- Payments are **simulated**, one-time and stored locally. No funds are transferred and no real card details are requested. Monthly/recurring payments and live gateways are not exposed.
- Email/password login is implemented. Phone-number login, Google/Facebook OAuth, automated email notifications and email password recovery need external providers and are not exposed as inactive buttons. In-app status and histories supply updates.
- Organization portfolios support text and PDF; DOC/DOCX uploads are intentionally excluded. No sensitive identity document is requested.
- One editable volunteer opportunity per fundraiser keeps organization management straightforward. Accepted applications for past events represent participation history; there is no separate attendance/certification workflow.
- Campaign and admin removals use preserved records and soft status changes. Organizations cannot reactivate moderator-disabled content. Administrator reactivation does not override an owner's completed/deactivated campaign or an inactive organization.
- SQLite, a development server and demo accounts are intended for a student presentation/local MVP. Production operation would require a production server, TLS, migrations, backups, rate limiting, secure account recovery, stronger document scanning and deployment-specific hardening.

## Validation

```bash
python -m pytest -q
```

Tests create an isolated temporary SQLite database for each case. They do not mutate your demo database. Coverage includes authentication, registration, inactive accounts, role/ownership restrictions, CSRF, donation validation/review/idempotency/receipts, volunteer applications and capacity, organization approval, campaign edits/deactivation, moderation visibility, audit records, image validation, private portfolios, saved charities and empty states.

Browser validation uses the running Flask server, native form submissions, logout confirmation, original asset loading and responsive checks at 320, 375, 390, 430, 768, 1024, 1366 and 1920 pixels. The final evidence and limitations are recorded in [docs/VALIDATION.md](docs/VALIDATION.md).

For the managed Linux environment, `bash scripts/setup.sh` performs the same repeatable installation and seeding steps. Each cloud task is already isolated; use this checkout directly rather than creating a Git worktree.

To repeat browser checks, install Playwright separately and use a disposable seeded database. For example, in one terminal on macOS/Linux:

```bash
export DATABASE_URL="sqlite:////tmp/charigo-browser-check.db"
flask --app app:create_app init-db
flask --app app:create_app seed
PORT=5010 python app.py
```

In another terminal:

```bash
# Playwright and a Chromium browser must be available in this Python environment.
CHARIGO_BASE_URL=http://127.0.0.1:5010 CHROMIUM_BINARY=/usr/bin/chromium python tests/browser_check.py
```

The optional browser script exercises 25 pages at eight widths, login for all roles, amount selection, donation confirmation/receipt and logout cancel/confirm. It writes screenshots and JSON results under ignored `artifacts/`, and creates a simulated donation in the database served at the supplied URL. Use a separate database rather than your presentation data. The script assumes the documented demo accounts and seed records are present.
