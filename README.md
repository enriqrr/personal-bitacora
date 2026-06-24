# Personal Bitacora

Personal Bitacora is a Django web app for publishing project documentation. Public visitors are read-only. In future modules, only the authenticated owner will be able to create, edit, archive, or manage content.

## Module Status

Module 0: Repository Foundation is implemented. It contains the Django project scaffold, environment-based settings, minimal public routes, placeholder owner dashboard, templates, tests, and local development documentation.

No project, document, work-session, tag, search, upload, registration, or deployment features are implemented yet.

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
