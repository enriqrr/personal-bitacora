# Personal Bitacora

Personal Bitacora is a Django web app for publishing project documentation. Public visitors are read-only. In future modules, only the authenticated owner will be able to create, edit, archive, or manage content.

## Module Status

Module 3: Project Tree Nodes is implemented. It contains the Django project scaffold, environment-based settings, minimal public routes, Django auth login/logout routes, owner-only dashboard access, project create/edit/archive flows, hierarchical project nodes, public tree/node pages, templates, tests, and local development documentation.

No document, work-session, tag, search, upload, registration, or deployment features are implemented yet.

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

After pulling Module 2 or later, run migrations:

```bash
.venv/bin/python manage.py migrate
```

Create or log in as the owner superuser, then open `/dashboard/projects/` to create a project.

Projects marked `PUBLIC` appear on `/projects/` and can be viewed at `/p/<slug>/` as long as they are not archived. Projects marked `PRIVATE` are visible only in the owner dashboard.

Archived projects are hidden from public project pages but remain visible to the owner. Projects are archived by status; they are not deleted.

## Project Tree Nodes

Project nodes are hierarchical compartments inside a project. They can represent areas, modules, features, screens, technical topics, research topics, deployment topics, testing topics, or other project structure.

After pulling Module 3, run migrations:

```bash
.venv/bin/python manage.py migrate
```

Log in as the owner, open `/dashboard/projects/`, choose a project, then use the tree links to create root nodes and child nodes. Root nodes start a tree. Child nodes are created from an existing node detail page.

Nodes marked `PUBLIC` can appear on the public project tree only when the project is also `PUBLIC`, the project is not archived, the node is not archived, and every ancestor node is also public and not archived. A public child under a private or archived parent is hidden publicly.

Archived nodes are hidden from public node pages but remain visible to the owner. Moving nodes is allowed only when it preserves tree integrity: a node cannot become its own parent, cannot move under one of its descendants, and cannot move under a node from another project.

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
