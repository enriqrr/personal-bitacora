# MVP Acceptance Audit

Module 9 is an audit and hardening checkpoint for the current MVP. It does not add new product features, domain models, or migrations.

## Scope Reviewed

- Public visitors can read only public-safe content.
- Owner-only dashboard routes require an authenticated active superuser.
- Mutations live in services and reads use selectors or search helpers where practical.
- Projects, nodes, documents, sessions, and tags preserve their data integrity rules.
- Public document Markdown is rendered server-side and sanitized before templates use `safe`.
- Public search uses visibility-safe query helpers and does not expose private, draft, needs-review, archived, or non-effective descendants.
- Deployment settings are split between local and production, with production driven by required environment variables.
- Admin registrations expose useful list, search, and filter fields without adding product behavior.
- README documentation matches the currently implemented modules.

## Current MVP Surface

- Module 0: Django foundation, homepage, health check, auth routes.
- Module 1: owner-only dashboard protection.
- Module 2: projects with public/private and archived behavior.
- Module 3: hierarchical project nodes with effective public visibility.
- Module 4: node documents with sanitized Markdown rendering.
- Module 5: work sessions with node and document references.
- Module 6: owner-scoped document tags.
- Module 7: simple database-backed public and owner search.
- Module 8: deployment hardening and production settings.
- Module 9: acceptance audit, smoke checklist, production readiness checklist, and cross-module canary tests.

## Security And Visibility Findings

- Public project routes filter out private and archived projects.
- Public node routes require the project, node, and every ancestor node to be public and non-archived.
- Public document routes require an effectively public node, public document visibility, and `ACTIVE` or `RESOLVED` status.
- Public session routes require public visibility, non-archived session state, and a public non-archived project.
- Public session detail pages filter references independently, so a public session does not leak private referenced nodes or documents.
- Public document pages show only public, non-archived tags attached to effectively public documents.
- Public search excludes private and archived content, draft and needs-review documents, private tags, and public children hidden under private ancestors.
- Owner search is owner-scoped and includes private and archived owner content.

## Architecture Findings

- Models contain persistent data rules and model-level validation for cross-object integrity.
- Services own create, update, archive, move, reference, and tag assignment mutations.
- Selectors and search helpers own query and visibility filtering.
- Views remain thin HTTP orchestration layers.
- Templates remain server-rendered and do not contain domain visibility logic.

## Data Integrity Findings

- Slug uniqueness is scoped to the intended owner, project, node, or sibling relationship.
- Document `project` must match `node.project`.
- Work-session references must belong to the same project as the session.
- Document tag ownership must match the document project owner.
- Archive flows soft-archive records instead of hard deleting them.

## Deployment Findings

- Production requires `SECRET_KEY`, `DATABASE_URL`, and `ALLOWED_HOSTS`.
- Production defaults to `DEBUG=False`.
- Production supports secure cookies, HTTPS redirect, HSTS, trusted CSRF origins, and proxy SSL header configuration through environment variables.
- Static files use WhiteNoise compressed manifest storage in production.
- Local settings can still run without PostgreSQL by falling back to SQLite.

## Known MVP Limits

- No public registration, password reset, custom user model, or multi-owner collaboration.
- No uploads, binary attachments, comments, version history, or rich text editor.
- No full-text search index, external search engine, ranking service, autocomplete, saved searches, or analytics.
- No AI summaries, calendar integration, GitHub integration, background jobs, or notification system.
- Production provider setup, DNS, TLS certificates, CI/CD, monitoring, backups, and rate limiting remain operational follow-up work.

## Audit Result

The current codebase supports the MVP shape: public-safe read-only publishing, owner-only mutation, project tree documentation, chronological sessions, document tags, simple safe search, and production-oriented settings. The main remaining work before a real launch is operational setup and manual smoke testing in the target hosting environment.
