# -*- coding: utf-8 -*-
"""Tests for core functions."""

from flask_login import login_user

from orcid_hub.models import User


def test_admin_view_access(request_ctx):
    """Test if SUPERUSER can run reports."""
    user = User.get(email="root@test0.edu")
    with request_ctx("/org_invitatin_summary") as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"Organisation Invitation Summary" in rv.data
        assert b"root@test0.edu" in rv.data


def test_user_invitation_summary(request_ctx):
    """Test user invitation summary."""
    user = User.get(email="root@test0.edu")
    with request_ctx("/user_invitatin_summary") as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"User Invitation Summary" in rv.data
        assert b"root@test0.edu" in rv.data


def test_user_summary(request_ctx):
    """Test user summary."""
    user = User.get(email="root@test0.edu")
    with request_ctx("/user_summary?from_date=2017-01-01&to_date=2018-02-28") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert b"TEST0" in resp.data
        assert b"root@test0.edu" in resp.data
        assert b"4 / 9 (44%)" in resp.data
    with request_ctx("/user_summary?from_date=2017-01-01&to_date=2017-12-31") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert b"TEST0" in resp.data
        assert b"root@test0.edu" in resp.data
        assert b"0 / 9 (0%)" in resp.data
    for (sort, desc) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        with request_ctx(
                f"/user_summary?from_date=2017-01-01&to_date=2018-12-31&sort={sort}&desc={desc}"
        ) as ctx:
            login_user(user, remember=True)
            resp = ctx.app.full_dispatch_request()
            assert resp.status_code == 200
            data = resp.data.decode()
            assert f"&sort={0 if sort else 1}&desc=0" in data
            assert f"&sort={sort}&desc={0 if desc else 1}" in data
    with request_ctx("/user_summary") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
