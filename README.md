# Personal Bitacora

Personal Bitacora is a Django web app for publishing project documentation. Public visitors are read-only. In future modules, only the authenticated owner will be able to create, edit, archive, or manage content.

## Module Status

Module 5: Work Sessions is implemented. It contains the Django project scaffold, environment-based settings, minimal public routes, Django auth login/logout routes, owner-only dashboard access, project create/edit/archive flows, hierarchical project nodes, editable node documents, chronological work-session logs, public session pages, templates, tests, and local development documentation.

No tag, search, upload, attachment, comment, registration, deployment, AI summary, calendar, or GitHub integration features are implemented yet.

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

## Node Documents

Node documents are editable Markdown notes attached to project tree nodes. They are the V1 content files for theory, specifications, pseudocode, code snippets, questions, todo lists, decisions, bug notes, deployment notes, references, and other notes.

After pulling Module 4, install dependencies and run migrations:

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
```

Log in as the owner, open a node detail page, then use `Create document` to add a document. Documents can be edited and archived from the owner document detail page.

Available document types are `THEORY`, `SPECIFICATION`, `PSEUDOCODE`, `CODE_SNIPPET`, `QUESTION`, `TODO_LIST`, `DECISION`, `BUG_NOTE`, `DEPLOYMENT_NOTE`, `REFERENCE`, and `OTHER`.

Available statuses are `DRAFT`, `ACTIVE`, `NEEDS_REVIEW`, `RESOLVED`, and `ARCHIVED`.

Documents marked `PUBLIC` are visible publicly only when their status is `ACTIVE` or `RESOLVED`, their project is public and not archived, and their node is effectively public. `DRAFT` and `NEEDS_REVIEW` documents are never public in V1, even when their visibility is set to `PUBLIC`.

Markdown is rendered server-side and sanitized with `bleach` before templates mark it safe. Raw Markdown is never trusted directly in templates.

Archived documents are hidden publicly but remain visible to the owner. Documents are archived by status; they are not deleted.

## Work Sessions

Work sessions are chronological logs for a project work block. They record the session title, start and optional end time, summary, goals, work done, decisions made, doubts opened, and next actions.

After pulling Module 5, run migrations:

```bash
.venv/bin/python manage.py migrate
```

Log in as the owner, open a project detail page, then use the work-session links to create, edit, view, and archive sessions.

Sessions belong to a single project. They can reference nodes and node documents from that same project so chronological work history can connect back to the project knowledge tree.

Sessions marked `PUBLIC` appear publicly only when they are not archived and their project is public and not archived. Private and archived sessions are hidden publicly but remain visible to the owner.

Public session detail pages show only references that are also publicly visible. Private or archived nodes, documents that are private, draft, needs-review, archived, or under non-public nodes, and references from non-effective objects are hidden from public visitors.

Session references must belong to the same project as the session. References from another project are rejected by the service layer.

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
