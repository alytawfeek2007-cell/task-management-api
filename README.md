# Task Management API

A REST API for task and project management, built to demonstrate token-based authentication, resource-scoped authorization, and API design patterns not covered by my previous two portfolio projects (session-based auth in the hotel booking app, no auth at all in the data insights app).

**Live API:** https://task-management-api-fg69.onrender.com
**Source:** https://github.com/alytawfeek2007-cell/task-management-api

> Note: this is hosted on a free tier, so the app may take up to 50 seconds to "wake up" after inactivity. This is a hosting limitation, not the app itself. There's no browsable frontend — it's a pure JSON API — but you can try it yourself with the example request below.

## What it does

Users register and authenticate via JWT, then create projects and invite other users into them with one of two roles: **Owner** or **Member**. Within a project, users create tasks, assign them to members, comment on them, and attach files — with every action checked against the requester's role in that specific project, not a single global permission level.

**Auth**
- `POST /register` — create an account
- `POST /login` — obtain an access + refresh token pair
- `POST /refresh` — exchange a refresh token for a new access token

**Projects**
- `POST /projects` — create a project (creator becomes Owner)
- `GET /projects` / `GET /projects/<id>` — list or view projects you belong to
- `PUT /projects/<id>` / `DELETE /projects/<id>` — Owner only
- `POST /projects/<id>/members` — add a member (Owner only)
- `GET /projects/<id>/members` — list members
- `PUT /projects/<id>/members/<user_id>` / `DELETE /projects/<id>/members/<user_id>` — change role / remove a member (Owner only)

**Tasks** — scoped to a project, visible only to its members
- Full CRUD, plus assignment to a specific member
- `GET /projects/<id>/tasks` supports filtering by `status`, `priority`, and `assignee_id`; sorting via `?sort=-priority` (whitelisted columns, `-` prefix for descending); and pagination (`page`, `per_page`, capped server-side)

**Comments** — attached to a task
- Full CRUD; only the author can edit their own comment, but the project Owner can delete any comment (moderation without content tampering)
- Always returned newest-first

**Attachments** — files attached to a task
- Multipart upload, capped at 5 MB, stored under a UUID-prefixed filename on disk (original filename preserved for display, never exposed in the internal path)
- Download and delete; delete permitted for the uploader or the project Owner

## Try it live

```bash
curl -X POST https://task-management-api-fg69.onrender.com/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "email": "demo@example.com", "password": "DemoPass123"}'
```

## Tech stack

Python, Flask, SQLAlchemy, Flask-JWT-Extended, Flask-Bcrypt, Flask-Migrate, pytest.

## Notable design decisions

- **Authorization is scoped per project, not global.** A user can be an Owner on one project and a Member on another simultaneously — every protected route re-checks the requester's `ProjectMember` role for *that specific project* rather than relying on a single account-wide permission flag.
- **404, not 403, for non-members.** Requesting a project (or its tasks/comments) you don't belong to returns the same 404 as a project that doesn't exist at all. This prevents an attacker from distinguishing "this resource exists but you're not on it" from "this resource doesn't exist" — a 403 would leak that information. 403 is only ever returned once membership is already confirmed.
- **JWT identity is always cast to `int`.** The JWT spec requires the `sub` claim to be a string, but this app's user IDs are integers throughout — every route explicitly converts `get_jwt_identity()` back to `int` before using it in a query, rather than relying on implicit coercion.
- **Comment editing is author-only; comment deletion is author-or-Owner.** Letting an Owner edit someone else's comment would let them silently put words in another user's mouth. Letting an Owner delete an inappropriate comment is moderation, not misrepresentation — so deletion has a wider permission than editing does.
- **Attachment file paths are never returned by the API.** Responses expose the original filename for display, but the actual on-disk path is an internal server detail and is stripped from every serialized response.
- **Secrets are environment-only, with no working fallback in source.** `SECRET_KEY` and `JWT_SECRET_KEY` are read via `os.environ.get()` with no hardcoded default — the app will not start with insecure placeholder keys by accident, in development or in production.
- **Known limitation:** attachments are stored on local disk. On most hosting platforms this is not persistent across deploys/restarts — a production version of this app would move to object storage (e.g. S3-compatible storage) instead.

## Running locally

```
git clone https://github.com/alytawfeek2007-cell/task-management-api.git
cd task-management-api
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create a `.env` file with:
```
SECRET_KEY=your-generated-secret
JWT_SECRET_KEY=your-generated-secret
```

Then apply the existing migration history to create the database tables, and run the app:
```
set FLASK_APP=app:create_app     # Windows (cmd)
$env:FLASK_APP="app:create_app"  # Windows (PowerShell)
export FLASK_APP=app:create_app  # macOS/Linux

flask db upgrade
python run.py
```

The `migrations/` folder is already part of this repo — `flask db upgrade` applies it to build the tables. Do not run `flask db init` or `flask db migrate` again; they're only needed once, and have already been done.

## Deployment

Deployed on Render's free tier, with a separate Render PostgreSQL instance for production data (local development still uses SQLite — see `config.py`'s `DevelopmentConfig` vs `ProductionConfig`).

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `flask db upgrade && gunicorn run:app` — migrations are applied automatically before the server starts on every deploy, since the free tier has no separate shell access to run them manually
- **Environment variables** set on the host: `SECRET_KEY`, `JWT_SECRET_KEY`, `DATABASE_URL` (provided automatically by Render's Postgres instance), and `FLASK_CONFIG=production` (selects `ProductionConfig`, which reads `DATABASE_URL` instead of falling back to SQLite)

## Running the tests

```
python -m pytest
```

21 tests across auth, projects, tasks, comments, and attachments — covering both the "happy path" for each route and the access-control rules (non-members, non-owners, wrong-author edits) that the API is built around.