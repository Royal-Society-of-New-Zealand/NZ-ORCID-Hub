# -*- coding: utf-8 -*-
"""Tests for util functions."""

from flask_login import login_user

from . import utils
from .models import Organisation, Role, User, UserOrg


def test_append_qs():
    """Test URL modication."""
    assert utils.append_qs(
        "https://abc.com/bar?p=foo", abc=123,
        p2="ABC") == "https://abc.com/bar?p=foo&abc=123&p2=ABC"
    assert utils.append_qs(
        "https://abc.com/bar", abc=123, p2="ABC") == "https://abc.com/bar?abc=123&p2=ABC"
    assert utils.append_qs(
        "https://abc.com/bar?p=foo", p2="A&B&C D") == "https://abc.com/bar?p=foo&p2=A%26B%26C+D"


def test_generate_confirmation_token():
    """Test to generate confirmation token."""
    token = utils.generate_confirmation_token(["testemail@example.com"])
    data = utils.confirm_token(token)
    # Test positive testcase
    assert 'testemail@example.com' == data[0]
    import time
    time.sleep(2)
    assert not utils.confirm_token(token, expiration=1)


def test_track_event(request_ctx):
    """Test to track event."""
    category = "test"
    action = "test"
    label = None
    value = 0

    u = User(
        email="test123@test.test.net",
        name="TEST USER",
        username="test123",
        roles=Role.RESEARCHER,
        orcid=None,
        confirmed=True)
    u.save()

    with request_ctx("/"):
        login_user(u)
        rv = utils.track_event(category, action, label, value)
        assert rv.status_code == 200


def test_set_server_name(app):
    """Test to set server name."""
    utils.set_server_name()
    server_name = app.config.get("SERVER_NAME")
    utils.set_server_name()
    assert server_name == app.config.get("SERVER_NAME")
    app.config["SERVER_NAME"] = "abc.orcidhub.org.nz"
    utils.set_server_name()
    assert "abc.orcidhub.org.nz" == app.config.get("SERVER_NAME")


def test_send_user_invitation(request_ctx):
    """Test to send user invitation."""
    org = Organisation(
        id=1,
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguation_org_id="ID",
        disambiguation_org_source="SOURCE")

    inviter = User(
        email="test123@mailinator.com",
        name="TEST USER",
        username="test123",
        roles=Role.RESEARCHER,
        orcid=None,
        confirmed=True,
        organisation=org)

    u = User(
        email="test1234@mailinator.com",
        name="TEST USER",
        username="test123",
        roles=Role.RESEARCHER,
        orcid=None,
        confirmed=True,
        organisation=org)
    u.save()
    user_org = UserOrg(user=u, org=org)
    user_org.save()

    email = "test1234@mailinator.com"
    first_name = "TEST"
    last_name = "Test"
    affiliation_types = {"staff"}
    with request_ctx("/"):
        utils.send_user_invitation(
            inviter=inviter,
            org=org,
            email=email,
            first_name=first_name,
            last_name=last_name,
            affiliation_types=affiliation_types)
