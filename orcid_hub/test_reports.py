# -*- coding: utf-8 -*-
"""Tests for core functions."""

from datetime import datetime

from flask_login import login_user

from .models import Organisation, Role, User, UserOrg


def test_admin_view_access(request_ctx):
    """Test if SUPERUSER can run reports."""
    with request_ctx("/user_summary?from_date=2017-07-05&to_date=2017-08-30") as ctx:
        org = Organisation.create(name="TEST ORGANISATION", confirmed=True)
        test_user = User.create(
            created_at=datetime(2017, 8, 29, 17, 32, 31, 148548),
            name="TEST USER",
            email="test@test.test.net",
            roles=Role.SUPERUSER,
            username="test42",
            confirmed=True)
        UserOrg.create(user=test_user, org=org)
        u2 = User.create(
            created_at=datetime(2017, 8, 29, 17, 32, 31, 148548),
            name="TEST USER #2",
            email="test2@test.test.net",
            roles=Role.SUPERUSER,
            username="test42",
            orcid="123-456-789",
            confirmed=True)
        UserOrg.create(user=u2, org=org)

        login_user(test_user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"TEST ORGANISATION" in rv.data
        assert b"1 / 2" in rv.data
        assert b"(50%)" in rv.data
        assert b"TEST USER" in rv.data
