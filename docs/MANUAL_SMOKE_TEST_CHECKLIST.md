# Manual Smoke Test Checklist

Use this checklist after deployment or before declaring the MVP ready. Test in two browsers or profiles: one logged in as the owner and one anonymous.

## Public Basics

- Open `/` and confirm the homepage loads.
- Open `/health/` and confirm it returns `ok`.
- Open `/projects/` and confirm only public, non-archived projects appear.
- Open a public project at `/p/<slug>/` and confirm project details load.
- Open a private or archived project URL and confirm it returns 404.
- Open `/accounts/signup/` and confirm it returns 404.

## Authentication

- Open `/accounts/login/` and log in as the owner.
- Confirm `/dashboard/` loads for the owner.
- Log out and confirm dashboard routes redirect anonymous users to login.
- Log in as a non-owner staffless user if available and confirm dashboard routes return 403.

## Projects

- As owner, create a project from `/dashboard/projects/new/`.
- Edit its name, slug, description, status, and visibility.
- Confirm public projects appear publicly and private projects do not.
- Archive a project and confirm it is hidden publicly but still visible to the owner.

## Nodes

- Create a root node under a project.
- Create a child node under that root.
- Edit node metadata.
- Move a node to a valid parent.
- Confirm private nodes do not appear publicly.
- Confirm a public child under a private parent does not appear publicly.
- Archive a node and confirm it is hidden publicly but still visible to the owner.

## Documents

- Create a document under a node.
- Edit the title, slug, type, status, visibility, and Markdown body.
- Confirm `ACTIVE` and `RESOLVED` public documents inside effective-public nodes are visible publicly.
- Confirm `DRAFT`, `NEEDS_REVIEW`, `ARCHIVED`, and `PRIVATE` documents are hidden publicly.
- Add Markdown containing a heading, fenced code block, table, script tag, and event handler attribute.
- Confirm the heading, code block, and table render, while scripts and event handlers do not execute or appear as trusted HTML.
- Archive a document and confirm it is hidden publicly but still visible to the owner.

## Work Sessions

- Create a work session for a project.
- Reference nodes and documents from the same project.
- Confirm cross-project references are rejected.
- Edit the session fields and references.
- Confirm public sessions appear on `/p/<project_slug>/sessions/`.
- Confirm private and archived sessions are hidden publicly.
- Confirm public session detail hides private node and document references.
- Archive a session and confirm it remains visible to the owner.

## Tags

- Create public and private tags from `/dashboard/tags/`.
- Edit a tag.
- Assign tags to a document from the document tag management page.
- Confirm owner document detail shows private, public, and archived assigned tags.
- Confirm public document detail shows only public, non-archived assigned tags.
- Archive a tag and confirm it is hidden publicly but still visible to the owner.

## Search

- Open `/search/` anonymously with an empty query and confirm the empty state.
- Search for public project, node, document, and session terms and confirm they appear.
- Search for private, draft, needs-review, archived, and private-descendant terms and confirm they do not appear.
- Confirm public snippets do not reveal private document or session text.
- Open `/dashboard/search/` as owner.
- Search for private and archived owner content and confirm it appears.
- Confirm owner search does not show another owner user's content.

## Admin

- Open `/admin/` as the owner superuser.
- Confirm projects, nodes, documents, sessions, references, tags, and document tags are registered.
- Confirm list filters and search boxes work for the main models.

## Deployment Smoke

- Run migrations in the deployed environment.
- Run `collectstatic`.
- Confirm static files load on public and owner pages.
- Confirm `DEBUG=False` in production.
- Confirm the deployed domain is present in `ALLOWED_HOSTS`.
- Confirm HTTPS pages work and insecure HTTP redirects if enabled.
