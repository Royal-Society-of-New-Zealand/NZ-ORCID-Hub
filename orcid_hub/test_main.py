# -*- coding: utf-8 -*-
"""Tests for core functions."""

import pprint

import pytest
from flask_login import login_user

from . import login_provider, utils
from .models import Organisation, OrgInfo, OrgInvitation, Role, User, UserOrg


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


@pytest.mark.parametrize("url",
                         ["/link", "/auth", "/pyinfo", "/invite/organisation", "/invite/user"])
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
            "Displayname": "TEST USER FROM 123",
            "Unscoped-Affiliation": "staff",
            "Eppn": "user@test.test.net"
        })

    assert rv.status_code == 302
    u = User.get(email="user@test.test.net")
    assert u.name == "TEST USER FROM 123", "Expected to have the user in the DB"
    assert u.first_name == "FIRST NAME/GIVEN NAME"
    assert u.last_name == "LAST NAME/SURNAME/FAMILY NAME"


def test_tuakiri_login_usgin_eppn(client):
    """Test logging attempt via Shibboleth using differt values to identify the user."""
    org = Organisation(tuakiri_name="ORGANISATION 123ABC")
    org.save()
    user = User.create(
        email="something_else@test.test.net", eppn="eppn123@test.test.net", roles=Role.RESEARCHER)
    user.save()

    rv = client.get(
        "/Tuakiri/login",
        headers={
            "Auedupersonsharedtoken": "ABC123",
            "Sn": "LAST NAME/SURNAME/FAMILY NAME",
            'Givenname': "FIRST NAME/GIVEN NAME",
            "Mail": "user123@test.test.net",
            "O": "ORGANISATION 123ABC",
            "Displayname": "TEST USER FROM 123",
            "Unscoped-Affiliation": "staff",
            "Eppn": "eppn123@test.test.net"
        })

    assert rv.status_code == 302
    u = User.get(eppn="eppn123@test.test.net")
    assert u.email == "something_else@test.test.net"
    assert u.name == "TEST USER FROM 123", "Expected to have the user in the DB"
    assert u.first_name == "FIRST NAME/GIVEN NAME"
    assert u.last_name == "LAST NAME/SURNAME/FAMILY NAME"


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
            "Displayname": "TEST USER FROM UNKNOWN",
            "Unscoped-Affiliation": "staff",
            "Eppn": "user@test.test.net"
        },
        follow_redirects=True)

    u = User.get(email="user@test.test.net")
    assert u is not None
    assert u.eppn == "user@test.test.net"
    assert b"Your organisation (INCOGNITO) is not yet using the Hub, " \
           b"see your Technical Contact for a timeline" in rv.data


def test_tuakiri_login_with_org(client):
    """
    Test logging attempt via Shibboleth.

    If a user logs in from an organisation that isn't
    onboared, the user should be informed about that and
    redirected to the login page.
    """
    org = Organisation(tuakiri_name="THE ORGANISATION", confirmed=True)
    org.save()

    rv = client.get(
        "/Tuakiri/login",
        headers={
            "Auedupersonsharedtoken": "ABC111",
            "Sn": "LAST NAME/SURNAME/FAMILY NAME",
            'Givenname': "FIRST NAME/GIVEN NAME",
            "Mail": "user111@test.test.net",
            "O": "THE ORGANISATION",
            "Displayname": "TEST USER FROM THE ORGANISATION",
            "Unscoped-Affiliation": "staff",
            "Eppn": "user@test.test.net"
        },
        follow_redirects=True)

    u = User.get(email="user111@test.test.net")
    assert u.organisation == org
    assert org in u.organisations
    assert b"Your organisation (THE ORGANISATION) is not onboarded" not in rv.data
    uo = UserOrg.get(user=u, org=org)
    assert not uo.is_admin


def test_tuakiri_login_by_techical_contact_organisation_not_onboarded(client):
    """Test logging attempt by technical contact when organisation is not onboarded."""
    org = Organisation(name="Org112", tuakiri_name="Org112", confirmed=False, is_email_sent=True)
    u = User(
        email="user1113@test.test.net", confirmed=True, roles=Role.TECHNICAL, organisation=org)
    org.tech_contact = u
    org.save()

    UserOrg(user=u, org=org, is_admin=True)
    rv = client.get(
        "/Tuakiri/login",
        headers={
            "Auedupersonsharedtoken": "ABC11s1",
            "Sn": "LAST NAME/SURNAME/FAMILY NAME",
            'Givenname': "FIRST NAME/GIVEN NAME",
            "Mail": "user1113@test.test.net",
            "O": "Org112",
            "Displayname": "TEST USER FROM THE Org112",
            "Unscoped-Affiliation": "student",
            "Eppn": "user11137@test.test.net"
        },
        follow_redirects=True)

    assert u.organisation == org
    assert not org.confirmed
    assert u.is_tech_contact_of(org)
    assert rv.status_code == 200
    assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"


def test_confirmation_token(app):
    """Test generate_confirmation_token and confirm_token."""
    app.config['SECRET_KEY'] = "SECRET"
    app.config['SALT'] = "SALT"
    token = utils.generate_confirmation_token("TEST@ORGANISATION.COM")
    assert utils.confirm_token(token) == "TEST@ORGANISATION.COM"

    app.config['SECRET_KEY'] = "SECRET"
    app.config['SALT'] = "COMPROMISED SALT"
    assert utils.confirm_token(token) is False

    app.config['SECRET_KEY'] = "COMPROMISED SECRET"
    app.config['SALT'] = "SALT"
    assert utils.confirm_token(token) is False

    app.config['SECRET_KEY'] = "COMPROMISED SECRET"
    app.config['SALT'] = "COMPROMISED SALT"
    assert utils.confirm_token(token) is False

    app.config['SECRET_KEY'] = "COMPROMISED"
    app.config['SALT'] = "COMPROMISED"
    assert utils.confirm_token(token, 0) is False, "Expired token shoud be rejected"


def test_login_provider_load_user(request_ctx):  # noqa: D103
    """Test to load user."""
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


def test_onboard_org(request_ctx):
    """Test to organisation onboarding."""
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
        roles=Role.TECHNICAL,
        orcid=123,
        organisation_id=1,
        confirmed=True,
        organisation=org)
    User.get_or_create(
        id=124,
        email="test1234@test.test.net",
        name="TEST USER",
        roles=Role.ADMIN,
        orcid=1243,
        organisation_id=1,
        confirmed=True,
        organisation=org)
    org_info = OrgInfo.get_or_create(
        id=121, name="THE ORGANISATION", tuakiri_name="THE ORGANISATION")
    org_info = OrgInfo.get(id=121)
    u = User.get(id=123)
    second_user = User.get(id=124)
    org.tech_contact = u
    org.tech_contact_id = u.id
    org_info.save()
    org.save()
    u.save()
    OrgInvitation.get_or_create(id=111, email=u.email, org=org, token="sdsddsd")
    org_invitation = OrgInvitation.get(id=111)
    org_invitation.save()
    UserOrg(user=u, org=org, is_admin=True)
    with request_ctx("/confirm/organisation") as ctx:
        login_user(u)
        u.save()
        assert u.is_tech_contact_of(org)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"Take me to ORCID to obtain my Client ID and Client Secret" in rv.data,\
            "Expected Button on the confirmation page"
    with request_ctx("/confirm/organisation") as ctxx:
        second_user.save()
        login_user(second_user)
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert rv.location.startswith("/admin/viewmembers/")


def test_logout(request_ctx):
    """Test to logout."""
    with request_ctx("/logout") as ctxx:
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert rv.location.startswith("/?logout=True")
