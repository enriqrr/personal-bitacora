"""Ownership and visibility rules for Bitacora."""

from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url


def is_owner(user):
    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and user.is_superuser
    )


def owner_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = resolve_url(settings.LOGIN_URL)
            return redirect_to_login(request.get_full_path(), login_url)
        if not is_owner(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped_view
