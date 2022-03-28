# -*- coding: utf-8 -*-  # noqa
"""Quequeing."""

import logging
from time import sleep, time

import rq_dashboard
from flask import abort
from flask_login import current_user
from flask_rq2 import RQ

from . import app, models

REDIS_URL = app.config["REDIS_URL"] = app.config.get("RQ_REDIS_URL")
__redis_available = bool(REDIS_URL)
# or (app.config.get("RQ_CONNECTION_CLASS") != "fakeredis.FakeStrictRedis") or not (app.config.get("RQ_ASYNC"))

if __redis_available:
    try:
        from rq import Queue as _Queue
        import redis

        with redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1) as r:
            r.ping()

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

        # app.config.from_object(rq_dashboard.default_settings)
    except:
        __redis_available = False

if not __redis_available:
    app.config.RQ_CONNECTION_CLASS = app.config[
        "RQ_CONNECTION_CLASS"
    ] = "fakeredis.FakeStrictRedis"
    app.config.RQ_ASYNC = app.config["RQ_ASYNC"] = False

    if "RQ_QUEUE_CLASS" in app.config:
        del app.config["RQ_QUEUE_CLASS"]
    if "REDIS_URL" in app.config:
        del app.config["REDIS_URL"]
    if "RQ_REDIS_URL" in app.config:
        del app.config["RQ_REDIS_URL"]

rq = RQ(app)


@rq_dashboard.blueprint.before_request
def restrict_rq(*args, **kwargs):
    """Restrict access to RQ-Dashboard."""
    if not current_user.is_authenticated:
        abort(401)
    if not current_user.has_role(models.Role.SUPERUSER):
        abort(403)


app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")
logging.getLogger("rq.worker").addHandler(logging.StreamHandler())
