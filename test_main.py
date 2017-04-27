# -*- coding: utf-8 -*-
"""Tests for core functions."""

import pprint

import pytest
from flask import url_for
from flask_login import current_user, login_user

import login_provider
import tokenGeneration
from models import Organisation, Role, User, UserOrg


def test_index(client):
    """Test the landing page."""
    rv = client.get("/")
    assert b"<!DOCTYPE html>" in rv.data
    # assert b"Home" in rv.data
    assert b"Royal Society of New Zealand" in rv.data, \
        "'Royal Society of New Zealand' should be present on the index page."


def get_response(request_ctx):
    """Return response within the request context.  It should be used with the request context."""
    # TODO: it can be replace with a sinble line: rv = ctx.app.full_dispatch_request()
    app = request_ctx.app
    # call the before funcs
    rv = app.preprocess_request()
    if rv is not None:
        response = app.make_response(rv)
    else:
        # do the main dispatch
        rv = app.dispatch_request()
        response = app.make_response(rv)

        # now do the after funcs
        response = app.process_response(response)

    return response


def test_login(request_ctx):
    """Test login function."""
    with request_ctx("/") as ctx:
        test_user = User(
            name="TEST USER", email="test@test.test.net", username="test42", confirmed=True)
        login_user(test_user, remember=True)

        rv = get_response(ctx)
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"TEST USER" in rv.data, "Expected to have the user name on the page"
        assert b"test@test.test.net" in rv.data, "Expected to have the user email on the page"


@pytest.mark.parametrize(
    "url", ["/link", "/auth", "/pyinfo", "/reset_db", "/invite/organisation", "/invite/user"])
def test_access(url, client):
    """Test access to the app for unauthorized user."""
    rv = client.get(url)
    assert rv.status_code == 302
    assert "Location" in rv.headers, pprint.pformat(rv.headers, indent=4)
    assert "next=" in rv.location
    rv = client.get(url, follow_redirects=True)
    assert rv.status_code == 200
    assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
    assert b"Please log in to access this page." in rv.data


def test_tuakiri_login(client):
    """
    Test logging attempt via Shibboleth.

    After getting logged in a new user entry shoulg be created.
    """
    rv = client.get(
        "/Tuakiri/login",
        headers={
            "Auedupersonsharedtoken": "ABC123",
            "Sn": "LAST NAME/SURNAME/FAMILY NAME",
            'Givenname': "FIRST NAME/GIVEN NAME",
            "Mail": "user@test.test.net",
            "O": "ORGANISATION 123",
            "Displayname": "TEST USER FROM 123"
        })

    assert rv.status_code == 302
    u = User.get(email="user@test.test.net")
    assert u.name == "TEST USER FROM 123", "Expected to have the user in the DB"
    assert u.first_name == "FIRST NAME/GIVEN NAME"
    assert u.last_name == "LAST NAME/SURNAME/FAMILY NAME"
    assert u.edu_person_shared_token == "ABC123"


def test_tuakiri_login_wo_org(client):
    """
    Test logging attempt via Shibboleth.

    If a user logs in from an organisation that isn't
    onboared, the user should be informed about that and
    redirected to the login page.
    """
    rv = client.get(
        "/Tuakiri/login",
        headers={
            "Auedupersonsharedtoken": "ABC999",
            "Sn": "LAST NAME/SURNAME/FAMILY NAME",
            'Givenname': "FIRST NAME/GIVEN NAME",
            "Mail": "user@test.test.net",
            "O": "INCOGNITO",
            "Displayname": "TEST USER FROM UNKNOWN"
        },
        follow_redirects=True)

    u = User.get(email="user@test.test.net")
    assert u.edu_person_shared_token == "ABC999"
    assert b"Your organisation (INCOGNITO) is not onboarded" in rv.data


def test_tuakiri_login_with_org(client):
    """
    Test logging attempt via Shibboleth.

    If a user logs in from an organisation that isn't
    onboared, the user should be informed about that and
    redirected to the login page.
    """
    org = Organisation(name="THE ORGANISATION")
    org.save()

    rv = client.get(
        "/Tuakiri/login",
        headers={
            "Auedupersonsharedtoken": "ABC111",
            "Sn": "LAST NAME/SURNAME/FAMILY NAME",
            'Givenname': "FIRST NAME/GIVEN NAME",
            "Mail": "user111@test.test.net",
            "O": "THE ORGANISATION",
            "Displayname": "TEST USER FROM THE ORGANISATION"
        },
        follow_redirects=True)

    u = User.get(email="user111@test.test.net")
    assert u.organisation == org
    assert org in u.organisations
    assert u.edu_person_shared_token == "ABC111"
    assert b"Your organisation (INCOGNITO) is not onboarded" not in rv.data
    uo = UserOrg.get(user=u, org=org)
    assert not uo.is_admin


def test_reset_db(request_ctx):
    """Test reset_db function for 'testing' cycle reset."""
    with request_ctx("/reset_db") as ctx:
        org = Organisation(name="THE ORGANISATION")
        org.save()
        u = User(
            email="test123@test.test.net",
            name="TEST USER",
            username="test123",
            roles=Role.SUPERUSER,
            orcid=None,
            confirmed=True)
        u.save()
        root = User(
            email="root@test.test.net",
            name="The root",
            username="root",
            roles=Role.SUPERUSER,
            orcid=None,
            confirmed=True)
        root.save()
        assert User.select().count() == 2
        assert Organisation.select().count() == 1
        login_user(u, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert User.select().count() == 1
        assert Organisation.select().count() == 0
        assert rv.status_code == 302
        assert rv.location == url_for("logout")


def test_confirmation_token(app):
    """Test generate_confirmation_token and confirm_token"""
    app.config['TOKEN_SECRET_KEY'] = "SECRET"
    app.config['TOKEN_PASSWORD_SALT'] = "SALT"
    token = tokenGeneration.generate_confirmation_token("TEST@ORGANISATION.COM")
    assert tokenGeneration.confirm_token(token) == "TEST@ORGANISATION.COM"

    app.config['TOKEN_SECRET_KEY'] = "SECRET"
    app.config['TOKEN_PASSWORD_SALT'] = "COMPROMISED SALT"
    assert tokenGeneration.confirm_token(token) is False

    app.config['TOKEN_SECRET_KEY'] = "COMPROMISED SECRET"
    app.config['TOKEN_PASSWORD_SALT'] = "SALT"
    assert tokenGeneration.confirm_token(token) is False

    app.config['TOKEN_SECRET_KEY'] = "COMPROMISED SECRET"
    app.config['TOKEN_PASSWORD_SALT'] = "COMPROMISED SALT"
    assert tokenGeneration.confirm_token(token) is False

    app.config['TOKEN_SECRET_KEY'] = "COMPROMISED"
    app.config['TOKEN_PASSWORD_SALT'] = "COMPROMISED"
    assert tokenGeneration.confirm_token(token, 0) is False, "Expired token shoud be rejected"


def test_login_provider_load_user(request_ctx):

    u = User(
        email="test123@test.test.net",
        name="TEST USER",
        username="test123",
        roles=Role.RESEARCHER,
        orcid=None,
        confirmed=True)
    u.save()

    user = login_provider.load_user(u.id)
    assert user == u
    assert login_provider.load_user(9999999) is None

    with request_ctx("/"):

        login_user(u)
        rv = login_provider.roles_required(Role.RESEARCHER)(lambda: "SUCCESS")()
        assert rv == "SUCCESS"

        rv = login_provider.roles_required(Role.SUPERUSER)(lambda: "SUCCESS")()
        assert rv != "SUCCESS"
        assert rv.status_code == 302
        assert rv.location.startswith("/")
