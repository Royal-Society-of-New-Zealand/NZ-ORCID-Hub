"""Application login provider for Flask-Login."""

from functools import wraps

from flask import flash
from flask_login import current_user

from . import login_manager
from .models import User


def roles_required(*roles):  # noqa: D202
    """Docorate handler with role requiremnts."""

    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            for r in roles:
                if current_user.has_role(r):
                    return fn(*args, **kwargs)
            else:
                return login_manager.unauthorized()

        return decorated_view

    return wrapper


@login_manager.user_loader
def load_user(user_id):
    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (DB user record PK) user to retrieve
    """
    try:
        u = User.get(id=user_id)
        if u.is_locked:
            flash("Your account was locked out. Please contact your administrator.", "danger")
            return None
        return u
    except User.DoesNotExist:
        return None
