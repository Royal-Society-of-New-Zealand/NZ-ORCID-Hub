# -*- coding: utf-8 -*-
"""Tests for core functions."""

from datetime import datetime

from flask_login import login_user

from orcid_hub.models import Organisation, Role, User, UserOrg


def test_admin_view_access(request_ctx):
    """Test if SUPERUSER can run reports."""
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
    with request_ctx("/user_summary?from_date=2017-07-05&to_date=2017-08-30") as ctx:
        login_user(test_user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"TEST ORGANISATION" in rv.data
        assert b"1 / 2" in rv.data
        assert b"(50%)" in rv.data
        assert b"TEST USER" in rv.data
    with request_ctx("/user_summary") as ctx:
        login_user(test_user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert b"2017-08-29" in rv.data


def test_org_invitation_summary(request_ctx):
    """Test org invitation summary."""
    Organisation.get_or_create(
        id=1,
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=False,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="SOURCE",
        is_email_sent=True)
    org = Organisation.get(id=1)
    User.get_or_create(
        id=123,
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.SUPERUSER,
        orcid=123,
        organisation_id=1,
        confirmed=True,
        organisation=org)
    user = User.get(id=123)
    org.save()
    user.save()
    UserOrg.get_or_create(id=122, user=user, org=org, is_admin=True)
    user_org = UserOrg.get(id=122)
    user_org.save()
    with request_ctx("/org_invitatin_summary") as ctxx:
        login_user(user, remember=True)
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"Organisation Invitation Summary" in rv.data
        assert b"test123@test.test.net" in rv.data


def test_user_invitation_summary(request_ctx):
    """Test user invitation summary."""
    Organisation.get_or_create(
        id=1,
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=False,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="SOURCE",
        is_email_sent=True)
    org = Organisation.get(id=1)
    User.get_or_create(
        id=123,
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.SUPERUSER,
        orcid=123,
        organisation_id=1,
        confirmed=True,
        organisation=org)
    user = User.get(id=123)
    org.save()
    user.save()
    UserOrg.get_or_create(id=122, user=user, org=org, is_admin=True)
    user_org = UserOrg.get(id=122)
    user_org.save()
    with request_ctx("/user_invitatin_summary") as ctxx:
        login_user(user, remember=True)
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"User Invitation Summary" in rv.data
        assert b"test123@test.test.net" in rv.data
