from .base import *  # noqa: F403

DEBUG = env("DEBUG", default=True)  # noqa: F405
ALLOWED_HOSTS = env("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])  # noqa: F405
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405
MIDDLEWARE = [  # noqa: F405
    middleware
    for middleware in MIDDLEWARE  # noqa: F405
    if middleware != "whitenoise.middleware.WhiteNoiseMiddleware"
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
