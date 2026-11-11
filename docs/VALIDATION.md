# Validation evidence

> **November 11, 2026 update.** The interface was rebuilt (responsive navigation, new stylesheet, WebP image copies, history filters / CSV export / withdrawal, donations received, deployment files). Current evidence: `python -m pytest -q` passes 21 tests; a Chromium pass over 40 pages at 320, 375, 430, 768, 1024 and 1440 pixels under `gunicorn wsgi:app` found no horizontal overflow, broken images or script errors, and completed the donation, filter, CSV and withdraw flows. The optional `tests/browser_check.py` script was removed because it targeted the old markup. The remainder of this file records the October 31 validation of the previous interface, including checks (axe-core scan, byte-identical image serving) that have not been repeated.

Validated in the current cloud machine on October 31, 2026 using Python 3.12.14, Flask 3.1.2, Flask-SQLAlchemy 3.1.1, SQLite and Chromium. This is local runtime validation; no deployment, GitHub push, fresh-task snapshot restoration or environment publication is claimed.

| Check | Outcome |
|---|---|
| `bash scripts/setup.sh` | Passed; pinned dependencies installed, tables initialized, seed safely repeated |
| `.venv/bin/python -m pytest -q` | 18 passed; no failed/skipped/expected-failure tests |
| Python compilation | Passed for application, routes, seed and test files |
| Internal navigation audit | 97 distinct per-role link destinations returned successful pages or successful authorized redirects; no broken destinations |
| Browser responsive matrix | 200 page checks: 25 pages × 8 widths; all HTTP 200, no horizontal overflow, no broken images |
| Requested widths | 320, 375, 390, 430, 768, 1024, 1366 and 1920 pixels |
| Real browser workflow | All three roles logged in/out; donation amount selection, review, confirmation, receipt and history; logout cancel/confirm |
| Browser JavaScript errors | None in the final matrix |
| Automated accessibility | axe-core WCAG 2 A/AA and 2.1 AA scan: 21 representative pages, zero reported violations in the final run |
| Asset integrity | All 12 selected original image files compared byte-for-byte with the supplied Figma ZIP; exact matches |
| Final post-format restart | `/health` returned 200 and `{"status":"ok"}`; images loaded, pages rendered, all three role login/logout smoke checks passed |

The workflow suite covers registration and duplicates, hashed passwords, invalid login, protected routes, public admin signup rejection, inactive account sessions, role and organization ownership restrictions, CSRF, invalid amounts, exact centavo accounting, persisted receipts and donation replay, unique volunteer applications, acceptance capacity and rejection, organization onboarding/approval, current and historical campaigns, create/edit/deactivation, content moderation and preserved history, audit records, image decoding/paths, private portfolios, profile editing, saved charities, search/filters and empty results. Tests use isolated temporary databases.

Initial browser checks found wrong image filename extensions and a JavaScript named-form-field collision. These were corrected and the complete browser matrix rerun successfully. The initial accessibility scan found insufficient contrast on small green copy over pink cards; using the existing dark text token for only those labels resolved the finding without changing the pink palette. No failing checks are hidden or disabled.

Visual comparison used the decoded Figma frame inventory and representative mobile/desktop screenshots for welcome, home, fundraiser, receipt, organization and administrator pages. Original tokens, photos, clover logo, category icons and navigation icons are retained; responsive sizing and new states use native HTML/CSS. Automated accessibility results do not substitute for a comprehensive human assistive-technology audit, and the implementation does not claim pixel-identical rendering of every Figma variant.

Local screenshot and browser-result files are in the ignored `artifacts/` directory. The optional repeatable browser check is `tests/browser_check.py`; it requires Playwright and Chromium and should target a disposable seeded database because it records a simulated donation. Its final assertions fail for HTTP errors, overflow, image failures or JavaScript errors.

## Environment configuration status

The app runs locally and installation/startup instructions are preserved in the source. The platform rejected the configuration draft update with `draft_not_editable`; a follow-up draft read still showed null install/start fields. These fields were **not saved**, and no publication was attempted. See `CLOUD_START.md` and `environment-config.proposed.json` for the transferable proposal. If publication has finished and the draft remains locked, open a new setup chat from environment settings to persist that proposal.

## Local presentation

Start with `python app.py` after the README setup commands. Demo emails: `goer@example.com`, `organization@example.com`, `admin@example.com`; shared demo password: `ChariGo123!`. Payments are simulated. Live payment processing, social sign-in, automated email delivery and production deployment are excluded as documented in README.md.
