# ChariGo

ChariGo connects **Charity Goers**, verified **charity organizations** and **administrators**: browse causes, make (simulated) donations, apply to volunteer, and follow everything in a searchable history. It is a Flask + SQLite app with server-rendered pages and no frontend framework, so it runs anywhere Python does.

The interface follows the [ChariGo Figma prototype](https://www.figma.com/proto/0BwLZRjE0ir7x0JYysSEiT?node-id=0-1) (Inter, pink `#F77492` / `#FEB5C6`, green `#03541C`, the clover logo and the original photos and icons) and adapts to the screen: a bottom tab bar on phones, a top navigation bar and multi-column layouts on tablets and PCs.

## Quick start (local Flask)

Requires Python 3.10 or newer.

```bash
python -m venv .venv
```

Activate it — macOS / Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Then install and run:

```bash
python -m pip install -r requirements.txt
```

```bash
python app.py
```

Open <http://127.0.0.1:5000>. The first start creates the database in `instance/charigo.db` and loads the demo data automatically; later starts keep your data.

`flask --app app run --debug` also works if you prefer the Flask CLI with auto-reload.

### Try it on your phone (same Wi-Fi)

```bash
HOST=0.0.0.0 python app.py
```

Then open `http://<your-computer's-IP>:5000` on the phone. On Windows PowerShell use `$env:HOST="0.0.0.0"; python app.py`.

## Demo accounts

All demo accounts use the password **ChariGo123!** The log-in page has one-tap buttons that fill these in.

| Role | Email | What to try |
|---|---|---|
| Charity Goer | goer@example.com | Donate, apply to volunteer, view history |
| Organization | organization@example.com | Manage fundraisers, review applicants, see donations received |
| Administrator | admin@example.com | Approve organizations, moderate content, audit log |
| Organization | iwas@example.com | A second verified organization |
| Organization | pending@example.com | Waiting for administrator approval |
| Charity Goer | juan@example.com, ana@example.com | Volunteer applicants |

### If logging in fails

The log-in page says what is wrong: unknown email, wrong password, deactivated account, or a demo account that is missing or was changed.

- **A demo account stopped working** (for example you deactivated it as the administrator, or the `instance/` folder holds a database from an older copy of the project): stop the app and run the command below. It resets the demo passwords and reactivates the demo accounts; everything else is kept.

```bash
flask --app app restore-demo
```

- **Start completely fresh:** `flask --app app reset-db` erases all data and reloads the demo (it asks first). Deleting the `instance/` folder and starting the app does the same.
- Passwords are case-sensitive: `ChariGo123!` has a capital C and G and ends with an exclamation mark.

## Using the app

**Charity Goer**

1. *Sign up* → choose **Charity Goer** → create an account (or use the demo account).
2. **Home** shows your impact, categories and featured fundraisers. **Explore** searches and filters by category, organization and volunteer need — filters apply as soon as you change them.
3. Open a fundraiser → **Donate** → pick an amount and a mock payment method → review → confirm. You get a receipt with a reference number. No money moves; payments are simulated.
4. On a fundraiser with a volunteer opportunity → **Volunteer** → write a short message → review → submit.
5. **Profile → Donation history / Volunteer history** (see below).

**History**

- *Donations*: totals, number of donations and charities supported; search by charity, fundraiser or reference number; filter by period; sort newest / oldest / highest; entries grouped by month; **View receipt** and **Donate again** on each entry.
- *Volunteering*: every application with its live status (pending, accepted, rejected), a plain-language explanation of what the status means, the event date, and your message. Filter by status and period. A pending application can be **withdrawn** (with confirmation).
- **Download CSV** exports exactly what is currently shown.
- The profile page shows your three most recent activities; the home page links straight to history.
- Organizations get **Profile → Donations Received**: every donation to their fundraisers, filterable by fundraiser, with anonymous donors kept anonymous.

**Organization**: sign up as an organization → complete the organization profile → wait for administrator approval → create fundraisers (optionally with a volunteer opportunity) → review applicants and accept or decline → mark campaigns completed or deactivate them. History is always preserved.

**Administrator**: review and approve/reject organizations, deactivate or reactivate users and listings, and search the system records (audit log). Administrators cannot be created through public sign-up.

## Deploy online

The repository is ready for a Python host. `wsgi.py` exposes the app, `Procfile` and `render.yaml` hold the start command (`gunicorn wsgi:app`), and the app creates and seeds its own database on first start.

**Render (free tier)**

1. Push this repository to GitHub.
2. In Render: **New + → Blueprint**, connect the repository, and apply. `render.yaml` sets the build and start commands, generates `SECRET_KEY`, and turns on secure cookies.
3. Open the `https://<name>.onrender.com` URL Render gives you.

**Any other host** (Railway, Fly.io, PythonAnywhere, a VPS): install `requirements.txt`, run the `Procfile` command, and set the variables below. On PythonAnywhere, point the WSGI file at `wsgi.py`'s `app`.

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Signs sessions. **Set a long random value online.** | random key saved in `instance/` |
| `COOKIE_SECURE` | `1` when served over HTTPS | off |
| `TRUST_PROXY` | `1` behind a hosting platform's HTTPS proxy | off |
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:///charigo.db` in `instance/` |
| `SEED_DEMO` | `0` to start with an empty database (no demo accounts) | `1` |
| `AUTO_SETUP` | `0` to skip automatic table creation | `1` |
| `HOST`, `PORT` | Address for `python app.py` | `127.0.0.1`, `5000` |

Things to know before sharing a public link:

- The demo accounts have a published password. Fine for a class demo; for anything else set `SEED_DEMO=0` and register real accounts.
- Free hosts usually have a temporary disk: the SQLite database and uploaded images reset on each redeploy or restart. Attach a persistent disk (and point `DATABASE_URL` at it) to keep data.
- Use one worker process with SQLite, as the provided start command does.

## HCI design principles applied

| Principle | Where it shows |
|---|---|
| Visibility of system status | Loading bar on every navigation, buttons switch to "Saving…" while a form submits, status badges on every fundraiser and application, live result counts on filtered lists, progress bars from real donation totals |
| Match with the real world | Peso amounts, Philippine time, plain status notes ("The organization is reviewing your application") instead of codes |
| User control and freedom | Back button on every inner page, review step before donating or applying, Edit / Cancel on reviews, withdraw a pending application, Clear filters, dismissible messages |
| Consistency and standards | One set of tokens and components (buttons, cards, badges, tabs, stat tiles) across all three roles; navigation always in the same place for the device |
| Error prevention | Confirmation dialogs for withdraw, log out and every destructive admin/organization action; amount presets; duplicate-submission protection; file size checked before upload |
| Recognition rather than recall | Icons with text labels, category tiles, demo-account buttons, receipts and references listed in history, "Donate again" |
| Flexibility and efficiency | Filters auto-apply, search from the home page, CSV export, impact tiles link to history |
| Aesthetic and minimalist design | Figma palette with generous spacing, one primary action per screen, secondary detail tucked behind disclosure |
| Help users recover from errors | Field-level validation messages, friendly error pages with a way back, empty states that say what to do next |
| Accessibility | Keyboard focus rings, skip link, labelled forms, large touch targets, dark text on the pink surfaces for contrast, reduced-motion support |

Responsive behaviour: mobile-first CSS with breakpoints at 640px (two-column grids) and 900px (top navigation, three-column grids, sticky donate panel). Checked from 320px to 1440px wide with no horizontal scrolling.

## What makes it run smoothly

- Photos are served as WebP copies (under 1 MB in total instead of 3 MB); originals stay in `static/images/`. The Figma photos are only 300-512 px wide, so small ones are enlarged with light sharpening, stray watermarks are cropped, and the Angat Buhay banner is a brand-colour composite so its photo is not stretched across a wide screen. To use sharper photos, drop a higher-resolution file into `static/images/` under the same name and run `python scripts/optimize_images.py`.
- After signing in, the browser's Back button no longer returns to the log-in or sign-up pages; they are available again once you log out.
- Static files are versioned and cached for a year; pages are gzip-compressed.
- Cross-page transitions use the browser's View Transitions where supported, and respect "reduce motion".
- No external requests: fonts, icons and scripts are all served locally.

## Tests

```bash
python -m pip install -r requirements-dev.txt
```

```bash
python -m pytest -q
```

22 tests cover sign-up and log-in, role and ownership restrictions, CSRF, the donation and volunteer flows, history filters / CSV export / withdrawal, organization and administrator workflows, uploads, caching and compression. Each test uses its own temporary database.

## Project structure

```text
app.py                 App factory, configuration, security headers, caching, CLI
wsgi.py                Entry point for production servers (gunicorn wsgi:app)
models.py              SQLAlchemy models
common.py              Authorization, validation, uploads, audit helpers
seed.py                Demo data
routes/                auth, goer (browse / donate / history), organization, admin
templates/             Jinja pages and shared components
static/css/style.css   Design tokens, components, responsive layout
static/js/main.js      Progressive enhancement (works without JavaScript)
static/images|icons|fonts  Original Figma assets, WebP copies in images/opt
tests/                 Workflow and security tests
docs/                  Figma audit, frame inventory, specification
Procfile, render.yaml  Deployment configuration
```

Useful commands: `flask --app app:create_app seed` (load demo data into an empty database) and `flask --app app:create_app reset-db` (erase everything and restore the demo; asks first).

## Scope and limits

- Payments are simulated: no card details are requested and no money moves.
- Email/password log-in only; no social sign-in, email notifications or password recovery.
- SQLite and demo data suit a class project or demo. A production launch would need a managed database, migrations, backups, rate limiting and account recovery.
- Security already in place: hashed passwords, CSRF tokens on every form, server-side role and ownership checks, a strict Content Security Policy, validated and re-encoded image uploads, private portfolio PDFs.

See [docs/FIGMA_AUDIT.md](docs/FIGMA_AUDIT.md) for how each Figma frame maps to a page.
