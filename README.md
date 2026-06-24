# Personal Bitacora

Personal Bitacora is a Django web app for publishing project documentation. Public visitors are read-only. In future modules, only the authenticated owner will be able to create, edit, archive, or manage content.

## Module Status

Module 2: Projects is implemented. It contains the Django project scaffold, environment-based settings, minimal public routes, Django auth login/logout routes, owner-only dashboard access, project create/edit/archive flows, public project list/detail pages, templates, tests, and local development documentation.

No tree node, document, work-session, tag, search, upload, registration, or deployment features are implemented yet.

## Local Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

For an initial local boot without PostgreSQL, omit `DATABASE_URL` from `.env` and Django will use a local SQLite database through `config.settings.local`.

Run migrations:

```bash
python manage.py migrate
```

Run the development server:

```bash
python manage.py runserver
```

Run tests:

```bash
python manage.py test
```

Run Django's system check:

```bash
python manage.py check
```

## Local Owner Setup

Run migrations:

```bash
.venv/bin/python manage.py migrate
```

Create the owner account as a superuser:

```bash
.venv/bin/python manage.py createsuperuser
```

Start the server:

```bash
.venv/bin/python manage.py runserver
```

Log in at `/accounts/login/`, then access `/dashboard/`.

## Projects

After pulling Module 2, run migrations:

```bash
.venv/bin/python manage.py migrate
```

Create or log in as the owner superuser, then open `/dashboard/projects/` to create a project.

Projects marked `PUBLIC` appear on `/projects/` and can be viewed at `/p/<slug>/` as long as they are not archived. Projects marked `PRIVATE` are visible only in the owner dashboard.

Archived projects are hidden from public project pages but remain visible to the owner. Projects are archived by status; they are not deleted.

## Local PostgreSQL

Start the local PostgreSQL service:

```bash
docker compose up -d db
```

Use this database URL:

```text
postgres://bitacora:bitacora@localhost:5432/bitacora
```

Stop the service:

```bash
docker compose down
```

Docker is optional for tests. The local settings can fall back to SQLite when `DATABASE_URL` is not set.
