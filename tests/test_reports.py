# -*- coding: utf-8 -*-
"""Tests for core functions."""

from flask_login import login_user

from orcid_hub.models import User


def test_admin_view_access(request_ctx):
    """Test if SUPERUSER can run reports."""
    user = User.get(email="root@test.edu")
    with request_ctx("/org_invitatin_summary") as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"Organisation Invitation Summary" in rv.data
        assert b"root@test.edu" in rv.data


def test_user_invitation_summary(request_ctx):
    """Test user invitation summary."""
    user = User.get(email="root@test.edu")
    with request_ctx("/user_invitatin_summary") as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"User Invitation Summary" in rv.data
        assert b"root@test.edu" in rv.data
