# -*- coding: utf-8 -*-
"""Tests for core functions."""

from flask_login import login_user

from models import Organisation, Role, User, UserOrg


def __test_admin_view_access(request_ctx):
    """Test if SUPERUSER can run reports."""

    with request_ctx("/user_summary") as ctx:
        org = Organisation(name="TEST ORGANISATION", confirmed=True)
        test_user = User(
            name="TEST USER",
            email="test@test.test.net",
            roles=Role.SUPERUSER,
            username="test42",
            confirmed=True)
        UserOrg(user=test_user, org=org)
        u2 = User(
            name="TEST USER #2",
            email="test2@test.test.net",
            roles=Role.SUPERUSER,
            username="test42",
            orcid="123-456-789",
            confirmed=True)
        UserOrg(user=u2, org=org)

        login_user(test_user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"TEST USER" in rv.data
