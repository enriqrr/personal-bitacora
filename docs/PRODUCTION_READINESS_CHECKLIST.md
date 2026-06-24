# Production Readiness Checklist

Use this checklist before pointing a real domain at the MVP.

## Required Environment

- Set `DJANGO_SETTINGS_MODULE=config.settings.production`.
- Set a strong unique `SECRET_KEY`.
- Set `DATABASE_URL` to a managed PostgreSQL database.
- Set `ALLOWED_HOSTS` to the deployed domain names.
- Set `CSRF_TRUSTED_ORIGINS` to the deployed HTTPS origins.
- Set `SECURE_SSL_REDIRECT=True` when TLS is available.
- Set `SESSION_COOKIE_SECURE=True`.
- Set `CSRF_COOKIE_SECURE=True`.
- Set `SECURE_HSTS_SECONDS=31536000` after HTTPS is stable.
- Configure `SECURE_PROXY_SSL_HEADER_NAME` and `SECURE_PROXY_SSL_HEADER_VALUE` if the host terminates TLS at a proxy.

## Release Commands

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py check
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py createsuperuser
```

Run the production deploy check with production-like environment variables:

```bash
DJANGO_SETTINGS_MODULE=config.settings.production \
SECRET_KEY=<strong-random-secret> \
DATABASE_URL=postgres://... \
ALLOWED_HOSTS=example.com \
CSRF_TRUSTED_ORIGINS=https://example.com \
.venv/bin/python manage.py check --deploy
```

## Owner Account

- Create exactly the owner account needed for the MVP.
- Use a strong password stored in a password manager.
- Do not add public registration.
- Review superuser access regularly.
- Consider adding 2FA or passkeys in a future hardening module.

## Data And Backups

- Use PostgreSQL in production.
- Enable automated database backups with point-in-time recovery if the provider supports it.
- Test restoring a backup before relying on the system.
- Back up before running major migrations.
- Keep uploaded media out of scope until a future upload module defines storage rules.

## Static Files

- Run `collectstatic` during each deploy.
- Serve collected static files through WhiteNoise or the hosting provider's static file mechanism.
- Do not commit `staticfiles/`.
- Confirm the admin CSS loads after deployment.

## Security Checks

- Confirm `DEBUG=False`.
- Confirm `/accounts/signup/` returns 404.
- Confirm anonymous users are redirected from `/dashboard/`.
- Confirm non-owner authenticated users receive 403 on owner routes.
- Confirm public pages do not expose private, draft, needs-review, archived, or private-descendant content.
- Confirm public search does not reveal private titles, snippets, tag names, or IDs.
- Confirm Markdown scripts and JavaScript attributes are sanitized.

## Operations

- Configure application logs through the hosting provider.
- Configure uptime monitoring for `/health/`.
- Add error monitoring before broader use.
- Decide how migrations are run during deploys.
- Document rollback steps for code and database changes.

## Future Hardening

- CI/CD pipeline.
- Provider-specific deployment configuration.
- Monitoring and alerting.
- Rate limiting.
- 2FA or passkeys for owner login.
- Content Security Policy.
- Automated backup verification.
- Security headers beyond the current Django defaults.
- Dedicated media/object storage when uploads are implemented.
