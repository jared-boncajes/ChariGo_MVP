# Reusable cloud environment instructions

The application and dependencies have been prepared and validated in the current machine. An attempt to save the environment's `install_script` and `start_skill` was rejected with `draft_not_editable`; persistence of these two configuration fields was **not confirmed**. A subsequent read still returned null fields. The platform reported that this can happen when the draft has already been published or publication is in progress. No network or secret requirements were changed.

If publication is still running, let it finish. To persist these instructions later, open a new setup chat from environment settings and supply this project or the ZIP handoff. Save these complete fields there. No application functionality depends on that draft operation succeeding.

## install_script

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /workspace/ChariGo_MVP
bash scripts/setup.sh
```

## start_skill

Each cloud task already runs in an isolated environment. Use the existing checkout at `/workspace/ChariGo_MVP`; do not create a Git worktree unless the user explicitly requests one.

Read README.md and any applicable agent instructions. Check Git status and preserve user edits. This is a Python 3.12 Flask/Jinja/vanilla JavaScript application with SQLite and Flask-SQLAlchemy. Dependencies and files may be retained in snapshots; live server processes are not retained.

If `.venv` or the database is missing, run `bash scripts/setup.sh` from the repository root. It installs `requirements.lock`, initializes tables and seeds an empty database without overwriting existing users. Keep the managed proxy and TLS verification enabled. Never reset the database without an explicit request. No Figma, social login or payment credentials are required.

Start `.venv/bin/python app.py` in a long-running exec session and inspect its output. Default bind is `127.0.0.1:5000`; `HOST` and `PORT` can override it. Reuse an existing healthy server rather than killing unrelated processes. Stop only processes started by the agent. Use the supported command permission path if sandbox restrictions block required local sockets; do not disable proxy/TLS settings.

Verify readiness with a local HTTP GET to `/health`, expecting status 200 and `{"status":"ok"}`. Also request `/home` and `/login`, verify expected content and asset loading. A process or open port alone is insufficient. The onboarding UI does not support public localhost preview links; report results in text.

For relevant changes run `.venv/bin/python -m pytest -q`, which uses temporary isolated databases. Optional browser validation is documented in README.md; use a disposable seeded database because it records simulated donations.

Demo accounts: `goer@example.com`, `organization@example.com`, `admin@example.com`; shared demo password `ChariGo123!`. These are presentation-only credentials. Payments are simulated. For deployment supply a secure `SECRET_KEY` and `COOKIE_SECURE=1` behind HTTPS; the local ignored key must not be copied to source control or a handoff archive. Do not deploy or publish automatically.
