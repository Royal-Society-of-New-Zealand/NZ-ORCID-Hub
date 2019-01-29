# -*- coding: utf-8 -*-  # noqa
"""Quequeing."""

from time import sleep, time

from flask import abort

from . import app, models
from flask_login import current_user

REDIS_URL = app.config["REDIS_URL"] = app.config.get("RQ_REDIS_URL")
__redis_available = bool(REDIS_URL)

if __redis_available:
    try:
        from flask_rq2 import RQ
        import rq_dashboard
        from rq import Queue as _Queue

        class ThrottledQueue(_Queue):
            """Queue with throttled deque."""

            # Default rate limit per sec (20 messages/sec)
            # NB! the rate should be greater than 1.0
            DEFAULT_RATE = 20.0
            rate = DEFAULT_RATE
            _allowance = rate
            _last_check = time()

            @classmethod
            def dequeue_any(cls, *args, **kwargs):
                """Dequeue the messages with throttling."""
                current = time()
                time_passed = current - cls._last_check
                cls._last_check = time()
                cls._allowance += time_passed * cls.rate
                if cls._allowance > cls.rate:
                    cls._allowance = cls.rate
                if cls._allowance < 1.0:
                    # wait...
                    sleep(1.0 - (cls._allowance / cls.rate))
                    cls._allowance = cls.rate
                return _Queue.dequeue_any(*args, **kwargs)
    except:
        __redis_available = False

if not __redis_available:
    from functools import wraps

    class RQ:  # noqa: F811
        """Fake RQ."""

        def __init__(self, *args, **kwargs):
            """Create a fake wrapper."""
            pass

        def job(*args, **kwargs):  # noqa: D202
            """Docorate a function to emulate queueing into a queue."""

            def wrapper(fn):
                @wraps(fn)
                def decorated_view(*args, **kwargs):
                    return fn(*args, **kwargs)

                return decorated_view

            return wrapper

# app.config.from_object(rq_dashboard.default_settings)
rq = RQ(app)


if __redis_available:
    @rq_dashboard.blueprint.before_request
    def restrict_rq(*args, **kwargs):
        """Restrict access to RQ-Dashboard."""
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.has_role(models.Role.SUPERUSER):
            abort(403)

    app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")
else:
    app.config["REDIS_URL"] = None
