# -*- coding: utf-8 -*-
"""Tests for core functions."""

import pprint

import pytest
from orcid_hub import authcontroller
from flask_login import login_user
from flask import request, session
from unittest.mock import patch
from werkzeug.datastructures import ImmutableMultiDict

from orcid_hub import login_provider, utils
from orcid_hub.models import Organisation, OrgInfo, OrgInvitation, Role, User, UserOrg, OrcidAuthorizeCall, \
    UserInvitation, Affiliation, OrcidToken


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
    user = User.create(
        email="test@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        confirmed=True,
        organisation=Organisation.create(
            name="THE ORGANISATION",
            tuakiri_name="THE ORGANISATION",
            confirmed=True,
            is_email_sent=True))

    with request_ctx("/logout") as ctx:
        # UoA user:
        login_user(user)
        session["shib_O"] = "University of Auckland"
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert "Shibboleth.sso" in rv.location
        assert "uoa-slo" in rv.location


def test_orcid_login(request_ctx):
    """Test login from orcid."""
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
    u = User.get(id=123)
    org.save()
    u.save()
    UserOrg.get_or_create(id=122, user=u, org=org, is_admin=True)
    user_org = UserOrg.get(id=122)
    user_org.save()
    token = utils.generate_confirmation_token(email=u.email, org=org.name)
    with request_ctx("/orcid/login/" + token) as ctxx:
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 302
        orcid_authorize = OrcidAuthorizeCall.get(method="GET")
        assert "&email=test123%40test.test.net" in orcid_authorize.url


def fetch_token_mock(self, token_url=None, code=None, authorization_response=None,
                     body='', auth=None, username=None, password=None, method='POST',
                     timeout=None, headers=None, verify=True, proxies=None, **kwargs):
    """Mock token fetching api call."""
    token = {'orcid': '12121', 'name': 'ros', 'access_token': 'xyz', 'refresh_token': 'xyz',
             'scope': '/activities/update'}
    return token


def get_record_mock(self, orcid=None, **kwargs):
    """Mock record api call."""
    request.data = '{"noemail": "sstest123@test.test.net"}'
    return request


@patch("orcid_hub.OAuth2Session.fetch_token", side_effect=fetch_token_mock)
@patch("orcid_hub.orcid_client.MemberAPIV20Api.view_emails", side_effect=get_record_mock)
def test_orcid_login_callback_admin_flow(patch, patch2, request_ctx):
    """Test login from orcid callback function for Organisation Technical contact."""
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
    u = User.get(id=123)
    org.save()
    u.save()
    UserOrg.get_or_create(id=122, user=u, org=org, is_admin=True)
    user_org = UserOrg.get(id=122)
    user_org.save()
    token = utils.generate_confirmation_token(email=u.email, org=org.name)
    with request_ctx() as ctxx:
        request.args = {"invitation_token": token, "state": "xyz"}
        session['oauth_state'] = "xyz"
        ctxx = authcontroller.orcid_login_callback(request)
        assert ctxx.status_code == 302
        assert ctxx.location.startswith("/")


def affiliation_mock(self=None,
                     affiliation=None,
                     role=None,
                     department=None,
                     org_name=None,
                     # NB! affiliation_record has 'organisation' field for organisation name
                     organisation=None,
                     city=None,
                     state=None,
                     region=None,
                     country=None,
                     disambiguated_id=None,
                     disambiguation_source=None,
                     start_date=None,
                     end_date=None,
                     put_code=None,
                     initial=False,
                     *args,
                     **kwargs):
    """Mock record api call."""
    return "xyz"


@patch("orcid_hub.OAuth2Session.fetch_token", side_effect=fetch_token_mock)
@patch("orcid_hub.orcid_client.MemberAPI.create_or_update_affiliation", side_effect=affiliation_mock)
def test_orcid_login_callback_researcher_flow(patch, patch2, request_ctx):
    """Test login from orcid callback function for researcher and display profile."""
    Organisation.get_or_create(
        id=1,
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=True,
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
        roles=Role.RESEARCHER,
        orcid=123,
        organisation_id=1,
        confirmed=True,
        organisation=org)
    u = User.get(id=123)
    org.save()
    u.save()
    UserOrg.get_or_create(id=122, user=u, org=org, is_admin=False)
    user_org = UserOrg.get(id=122)
    user_org.save()
    token = utils.generate_confirmation_token(email=u.email, org=org.name)
    UserInvitation.get_or_create(
        id=1233,
        email=u.email,
        token=token,
        affiliations=Affiliation.EMP)
    user_invitation = UserInvitation.get(id=1233)
    user_invitation.save()
    OrcidToken.get_or_create(
        id=19,
        user_id=u.id,
        org_id=org.id,
        scope='/read-limited,/activities/update')
    orcid_token = OrcidToken.get(id=19)
    orcid_token.save()
    with request_ctx() as ctxx:
        request.args = {"invitation_token": token, "state": "xyz"}
        session['oauth_state'] = "xyz"
        ctxx = authcontroller.orcid_login_callback(request)
        assert ctxx.status_code == 302
        # display profile
        assert ctxx.location.startswith("/profile")


def test_select_user_org(request_ctx):
    """Test organisation switch of current user."""
    Organisation.get_or_create(
        id=1,
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="SOURCE",
        is_email_sent=True)
    org = Organisation.get(id=1)

    Organisation.get_or_create(
        id=2,
        name="THE ORGANISATION2",
        tuakiri_name="THE ORGANISATION2",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="SOURCE",
        is_email_sent=True)
    org2 = Organisation.get(id=2)

    User.get_or_create(
        id=123,
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid=123,
        organisation_id=1,
        confirmed=True,
        organisation=org)
    user = User.get(id=123)
    org.save()
    org2.save()
    user.save()
    UserOrg.get_or_create(id=1224, user=user, org=org, is_admin=True)
    UserOrg.get_or_create(id=12234, user=user, org=org2, is_admin=True)
    user_org = UserOrg.get(id=1224)
    user_org2 = UserOrg.get(id=12234)
    user_org.save()
    user_org2.save()
    org_id = str(user_org2.id)
    with request_ctx("/select/user_org/" + org_id) as ctxx:
        login_user(user, remember=True)
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert user.organisation_id != 1
        # Current users organisation has been changes from 1 to 2
        assert user.organisation_id == 2


def test_shib_sp(request_ctx):
    """Test shibboleth SP."""
    with request_ctx("/Tuakiri/SP") as ctxx:
        request.args = {'key': '123', 'url': '/profile'}
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert rv.location.startswith("/profile")


def test_get_attributes(request_ctx):
    """Test shibboleth SP."""
    key = "xyz"
    with request_ctx("/sp/attributes/" + key) as ctxx:
        rv = ctxx.app.full_dispatch_request()
        # No such file name 'xyz'
        assert rv.status_code == 403


def test_link(request_ctx):
    """Test orcid profile linking."""
    Organisation.get_or_create(
        id=1,
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=True,
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
    user = User.get(id=123)
    org.save()
    user.save()
    UserOrg.get_or_create(id=1224, user=user, org=org, is_admin=True)
    user_org = UserOrg.get(id=1224)
    user_org.save()
    with request_ctx("/link") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('error', 'access_denied')])
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"


def test_orcid_callback(request_ctx):
    """Test orcid researcher deny flow."""
    Organisation.get_or_create(
        id=1,
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=True,
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
    user = User.get(id=123)
    org.save()
    user.save()
    UserOrg.get_or_create(id=1224, user=user, org=org, is_admin=True)
    user_org = UserOrg.get(id=1224)
    user_org.save()
    with request_ctx("/auth") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('error', 'access_denied'), ('login', '2')])
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert rv.location.startswith("/link")
