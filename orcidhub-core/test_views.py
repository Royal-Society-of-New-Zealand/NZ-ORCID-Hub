# -*- coding: utf-8 -*-

"""Tests for core functions."""

import sys

from flask_login import login_user

import views
from models import Role, User


def test_admin_view_access(request_ctx):
    """Test if SUPERUSER can access Flask-Admin"."""

    with request_ctx("/admin/user/") as ctx:
        test_user = User(
            name="TEST USER",
            email="test@test.test.net",
            roles=Role.SUPERUSER,
            username="test42",
            confirmed=True)
        login_user(test_user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"User" in rv.data


def test_admin_view_access_fail(client, request_ctx):
    """Test if non SUPERUSER cannot access Flask-Admin"."""

    rv = client.get("/admin/user/")
    assert rv.status_code == 302
    assert "next=" in rv.location and "admin" in rv.location

    with request_ctx("/admin/user/") as ctx:
        test_user = User(
            name="TEST USER",
            email="test@test.test.net",
            username="test42",
            confirmed=True)
        login_user(test_user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert "next=" in rv.location and "admin" in rv.location


def test_pyinfo(request_ctx):
    """Test pyinfo is workinkg."""

    with request_ctx("/pyinfo") as ctx:
        test_user = User(
            name="TEST USER",
            email="test@test.test.net",
            username="test42",
            confirmed=True)
        login_user(test_user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert bytes(sys.version, encoding="utf-8") in rv.data


def test_year_range():
    """Test Jinja2 filter."""

    assert views.year_range({"start_date": None, "end_date": None}) == "unknown-present"
    assert views.year_range({
        "start_date": {"year": {"value": "1998"}, "whatever": "..."},
        "end_date": None}) == "1998-present"
    assert views.year_range({
        "start_date": {"year": {"value": "1998"}, "whatever": "..."},
        "end_date": {"year": {"value": "2001"}, "whatever": "..."}}) == "1998-2001"
