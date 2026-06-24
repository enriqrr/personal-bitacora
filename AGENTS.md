# AGENTS.md

## Project

This is a personal Bitácora web app built with Django.

It allows public visitors to read public project documentation, but only the owner can create, edit, archive, or manage content.

## Architecture

- Django monolith.
- PostgreSQL database.
- Server-rendered Django templates.
- HTMX only where useful.
- Tailwind CSS for styling.
- No React in V1.
- No public registration.
- Public users can only read public content.
- Only the authenticated owner can mutate content.

## File responsibilities

- models.py: persistent data.
- services.py: mutations and business rules.
- selectors.py: read/query logic.
- permissions.py: ownership and visibility rules.
- forms.py: input validation.
- views.py: thin HTTP orchestration.
- templates/: presentation only.
- tests/: automated tests.

## Rules

- Do not implement large features without a module contract.
- Do not implement future modules early.
- Do not put business logic in views.
- Do not add public signup.
- Do not expose private content through public routes.
- Do not commit secrets.
- Do not change unrelated files unless necessary.

## Testing

Every module must include tests for:
- models;
- services;
- permissions;
- views;
- edge cases.

A module is not complete if tests are missing.