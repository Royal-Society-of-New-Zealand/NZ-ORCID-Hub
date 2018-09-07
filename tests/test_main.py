# -*- coding: utf-8 -*-
"""Tests for core functions."""

from io import BytesIO
import pprint
from unittest.mock import patch, Mock
from urllib.parse import urlparse

import pytest
from flask import request, session
from flask_login import current_user, login_user, logout_user
from peewee import fn
from werkzeug.datastructures import ImmutableMultiDict

from orcid_hub import authcontroller, login_provider, utils
from orcid_hub.models import (Affiliation, OrcidAuthorizeCall, OrcidToken, Organisation, OrgInfo,
                              OrgInvitation, Role, User, UserInvitation, UserOrg)


def test_index(client, monkeypatch):
    """Test the landing page."""
    client.application.config["EXTERNAL_SP"] = "https://some.externar.sp/SP"
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"https://some.externar.sp/SP" in resp.data
    assert b"<!DOCTYPE html>" in resp.data
    assert b"Royal Society of New Zealand" in resp.data, \
        "'Royal Society of New Zealand' should be present on the index page."
    client.application.config["EXTERNAL_SP"] = None


def get_response(request_ctx):
    """Return response within the request context.  It should be used with the request context."""
    # TODO: it can be replace with a single line: resp = ctx.app.full_dispatch_request()
    app = request_ctx.app
    # call the before funcs
    resp = app.preprocess_request()
    if resp is not None:
        response = app.make_response(resp)
    else:
        # do the main dispatch
        resp = app.dispatch_request()
        response = app.make_response(resp)

        # now do the after funcs
        response = app.process_response(response)

    return response


def test_login(request_ctx):
    """Test login function."""
    with request_ctx("/") as ctx:
        test_user = User(
            name="TEST USER", email="test@test.test.net", username="test42", confirmed=True)
        login_user(test_user, remember=True)

        resp = get_response(ctx)
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert b"TEST USER" in resp.data, "Expected to have the user name on the page"
        assert b"test@test.test.net" in resp.data, "Expected to have the user email on the page"

        logout_user()
        resp = get_response(ctx)
        assert b"test@test.test.net" not in resp.data


def test_org_switch(client):
    """Test organisation switching."""
    user = User.get(orcid=User.select(fn.COUNT(User.orcid).alias("id_count"), User.orcid).group_by(
        User.orcid).having(fn.COUNT(User.orcid) > 1).naive().first().orcid)
    resp = client.login(user, follow_redirects=True)

    assert user.email.encode() in resp.data
    assert len(user.org_links) > 1
    assert current_user == user

    for ol in user.org_links:
        assert ol.org.name.encode() in resp.data
        if ol.org.id != user.organisation.id:
            next_ol = ol

    resp = client.get(f"/select/user_org/{next_ol.id}", follow_redirects=True)
    next_user = UserOrg.get(next_ol.id).user
    assert next_user != user


@pytest.mark.parametrize("url",
                         ["/link", "/auth", "/pyinfo", "/invite/organisation", "/invite/user"])
def test_access(url, client):
    """Test access to the app for unauthorized user."""
    resp = client.get(url)
    assert resp.status_code == 302
    assert "Location" in resp.headers, pprint.pformat(resp.headers, indent=4)
    assert "next=" in resp.location
    resp = client.get(url, follow_redirects=True)
    assert resp.status_code == 200
    assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
    assert b"Please log in to access this page." in resp.data


def test_tuakiri_login(client):
    """
    Test logging attempt via Shibboleth.

    After getting logged in a new user entry shoulg be created.
    """
    resp = client.get(
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

    assert resp.status_code == 302
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

    resp = client.get(
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

    assert resp.status_code == 302
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
    resp = client.get(
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
           b"see your Technical Contact for a timeline" in resp.data


def test_tuakiri_login_with_org(client):
    """
    Test logging attempt via Shibboleth.

    If a user logs in from an organisation that isn't
    onboared, the user should be informed about that and
    redirected to the login page.
    """
    org = Organisation(tuakiri_name="THE ORGANISATION", confirmed=True)
    org.save()

    resp = client.get(
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
    assert b"Your organisation (THE ORGANISATION) is not onboarded" not in resp.data
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
    resp = client.get(
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
    assert resp.status_code == 200
    assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"


def test_confirmation_token(app):
    """Test generate_confirmation_token and confirm_token."""
    app.config['SECRET_KEY'] = "SECRET"
    token = utils.generate_confirmation_token("TEST@ORGANISATION.COM")
    assert utils.confirm_token(token) == "TEST@ORGANISATION.COM"

    app.config['SECRET_KEY'] = "COMPROMISED SECRET"
    with pytest.raises(Exception) as ex_info:
        utils.confirm_token(token)
    # Got exception
    assert "does not match" in ex_info.value.message


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
        resp = login_provider.roles_required(Role.RESEARCHER)(lambda: "SUCCESS")()
        assert resp == "SUCCESS"

        resp = login_provider.roles_required(Role.SUPERUSER)(lambda: "SUCCESS")()
        assert resp != "SUCCESS"
        assert resp.status_code == 302
        assert resp.location.startswith("/")


def test_onboard_org(request_ctx):
    """Test to organisation onboarding."""
    org = Organisation.create(
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
    u = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)
    second_user = User.create(
        email="test1234@test.test.net",
        name="TEST USER",
        roles=Role.ADMIN,
        orcid="1243",
        confirmed=True,
        organisation=org)
    org_info = OrgInfo.create(
        name="THE ORGANISATION", tuakiri_name="THE ORGANISATION")
    org.tech_contact = u
    org_info.save()
    org.save()

    OrgInvitation.get_or_create(email=u.email, org=org, token="sdsddsd")
    UserOrg.create(user=u, org=org, is_admin=True)

    with request_ctx("/confirm/organisation") as ctx:
        login_user(u)
        u.save()
        assert u.is_tech_contact_of(org)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert b"Take me to ORCID to obtain my Client ID and Client Secret" in resp.data,\
            "Expected Button on the confirmation page"
    with request_ctx("/confirm/organisation") as ctxx:
        second_user.save()
        login_user(second_user)
        resp = ctxx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location.startswith("/admin/viewmembers/")
    with request_ctx(
            "/confirm/organisation",
            method="POST",
            data={
                "orcid_client_id": "APP-FDFN3F52J3M4L34S",
                "orcid_secret": "4916c2d7-085e-487e-94d0-32450a9cfe6c",
                "country": "NZ",
                "city": "Auckland",
                "disambiguated_id": "xyz",
                "disambiguation_source": "xyz",
                "name": "THE ORGANISATION"
            }) as cttxx:
        login_user(u)
        u.save()
        with patch("orcid_hub.authcontroller.requests") as requests:
            requests.post.return_value = Mock(data=b'XXXX', status_code=200)
            resp = cttxx.app.full_dispatch_request()
            assert resp.status_code == 302
            assert resp.location.startswith("/link")


@patch("orcid_hub.utils.send_email")
def test_invite_tech_contact(send_email, client):
    """Test on-boarding of an org."""
    pass

    client.login_root()
    email = "tech.contact@a.new.org"
    client.post(
        "/invite/organisation",
        data={
            "org_name": "A NEW ORGANISATION",
            "org_email": email,
            "tech_contact": "y",
        })
    u = User.get(email=email)
    oi = OrgInvitation.get(invitee=u)

    assert not u.confirmed
    assert oi.org.name == "A NEW ORGANISATION"
    assert oi.org.tech_contact is None
    send_email.assert_called_once()
    client.logout()

    # Test invited user login:
    client.login(u, **{"Sn": "Surname", "Givenname": "Givenname", "Displayname": "Test User"})
    u = User.get(email=email)
    assert u.confirmed
    assert u.organisation.tech_contact == u


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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert "Shibboleth.sso" in resp.location
        assert "uoa-slo" in resp.location


def test_orcid_login(client):
    """Test login from orcid."""
    org = Organisation.create(
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
    u = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)

    UserOrg.create(user=u, org=org, is_admin=True)

    # with SALT
    client.application.config["SALT"] = "TEST-SALT"
    token = utils.generate_confirmation_token(email=u.email, org=org.name)
    resp = client.get("/orcid/login/" + token.decode("utf-8"))
    assert resp.status_code == 200
    orcid_authorize = OrcidAuthorizeCall.get(method="GET")
    assert "&email=test123%40test.test.net" in orcid_authorize.url

    expired_token = utils.generate_confirmation_token(expiration=-1, email=u.email, org=org.name)
    resp = client.get("/orcid/login/" + expired_token.decode("utf-8"))
    # putting sleep for token expiry.
    assert resp.status_code == 302
    url = urlparse(resp.location)
    assert url.path == '/'

    # w/o SALT:
    client.application.config["SALT"] = None
    token = utils.generate_confirmation_token(email=u.email, org=org.name)
    resp = client.get("/orcid/login/" + token.decode("utf-8"))
    assert resp.status_code == 200
    orcid_authorize = OrcidAuthorizeCall.get(method="GET")
    assert "&email=test123%40test.test.net" in orcid_authorize.url

    expired_token = utils.generate_confirmation_token(expiration=-1, email=u.email, org=org.name)
    resp = client.get("/orcid/login/" + expired_token.decode("utf-8"))
    # putting sleep for token expiry.
    assert resp.status_code == 302
    url = urlparse(resp.location)
    assert url.path == '/'


def fetch_token_mock(self,
                     token_url=None,
                     code=None,
                     authorization_response=None,
                     body='',
                     auth=None,
                     username=None,
                     password=None,
                     method='POST',
                     timeout=None,
                     headers=None,
                     verify=True,
                     proxies=None,
                     **kwargs):
    """Mock token fetching api call."""
    token = {
        'orcid': '123',
        'name': 'ros',
        'access_token': 'xyz',
        'refresh_token': 'xyz',
        'scope': '/activities/update',
        'expires_in': '12121'
    }
    return token


def get_record_mock(self, orcid=None, **kwargs):
    """Mock record api call."""
    request.data = '{"noemail": "sstest123@test.test.net"}'
    return request


@patch("orcid_hub.OAuth2Session.fetch_token", side_effect=fetch_token_mock)
@patch("orcid_hub.orcid_client.MemberAPIV20Api.view_emails", side_effect=get_record_mock)
def test_orcid_login_callback_admin_flow(patch, patch2, request_ctx):
    """Test login from orcid callback function for Organisation Technical contact."""
    org = Organisation.create(
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
    u = User.create(
        email="test123@test.test.net",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=False,
        organisation=org)
    UserOrg.create(user=u, org=org, is_admin=True)
    token = utils.generate_confirmation_token(email=u.email, org=org.name)

    with request_ctx() as resp:
        request.args = {"invitation_token": token, "state": "xyz"}
        session['oauth_state'] = "xyz"
        resp = authcontroller.orcid_login_callback(request)
        assert resp.status_code == 302
        assert resp.location.startswith("/")
    with request_ctx() as respx:
        request.args = {"invitation_token": token, "state": "xyzabc"}
        session['oauth_state'] = "xyz"
        respx = authcontroller.orcid_login_callback(request)
        assert respx.status_code == 302
        assert respx.location.startswith("/")
    with request_ctx() as resp:
        request.args = {"invitation_token": token, "state": "xyz", "error": "access_denied"}
        session['oauth_state'] = "xyz"
        resp = authcontroller.orcid_login_callback(request)
        assert resp.status_code == 302
        assert resp.location.startswith("/")
    with request_ctx() as ct:
        token = utils.generate_confirmation_token(email=u.email, org=None)
        request.args = {"invitation_token": token, "state": "xyz"}
        session['oauth_state'] = "xyz"
        ctxx = authcontroller.orcid_login_callback(request)
        assert ctxx.status_code == 302
        assert ctxx.location.startswith("/")
    with request_ctx() as ctxxx:
        request.args = {"invitation_token": token, "state": "xyzabc"}
        session['oauth_state'] = "xyz"
        ctxxx = authcontroller.orcid_login_callback(request)
        assert ctxxx.status_code == 302
        assert ctxxx.location.startswith("/")
    with request_ctx() as cttxx:
        request.args = {"invitation_token": token, "state": "xyz", "error": "access_denied"}
        session['oauth_state'] = "xyz"
        cttxx = authcontroller.orcid_login_callback(request)
        assert cttxx.status_code == 302
        assert cttxx.location.startswith("/")
    with request_ctx() as ct:
        token = utils.generate_confirmation_token(email=u.email, org=None)
        request.args = {"invitation_token": token, "state": "xyz"}
        session['oauth_state'] = "xyz"
        ct = authcontroller.orcid_login_callback(request)
        assert ct.status_code == 302
        assert ct.location.startswith("/")
    with request_ctx():
        request.args = {"invitation_token": None, "state": "xyz"}
        session['oauth_state'] = "xyz"
        ct = authcontroller.orcid_login_callback(request)
        assert ct.status_code == 302
        assert ct.location.startswith("/")
    with request_ctx():
        # Test case for catching general exception: invitation token here is integer, so an exception will be thrown.
        request.args = {"invitation_token": 123, "state": "xyz"}
        session['oauth_state'] = "xyz"
        ct = authcontroller.orcid_login_callback(request)
        assert ct.status_code == 302
        assert ct.location.startswith("/")
    with request_ctx():
        # User login via orcid, where organisation is not confirmed.
        u.orcid = "123"
        u.save()
        request.args = {"invitation_token": None, "state": "xyz"}
        session['oauth_state'] = "xyz"
        resp = authcontroller.orcid_login_callback(request)
        assert resp.status_code == 302
        assert resp.location.startswith("/about")
    with request_ctx():
        # User login via orcid, where organisation is confirmed, so showing viewmembers page.
        org.tech_contact = u
        org.confirmed = True
        org.save()
        request.args = {"invitation_token": None, "state": "xyz"}
        session['oauth_state'] = "xyz"
        resp = authcontroller.orcid_login_callback(request)
        assert resp.status_code == 302
        assert resp.location.startswith("/admin/viewmembers/")
    with request_ctx():
        # User login via orcid, where organisation is not confirmed and user is tech, so showing confirm org page.
        org.confirmed = False
        org.save()
        request.args = {"invitation_token": None, "state": "xyz"}
        session['oauth_state'] = "xyz"
        resp = authcontroller.orcid_login_callback(request)
        assert resp.status_code == 302
        assert resp.location.startswith("/confirm/organisation")


def affiliation_mock(
        self=None,
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
@patch(
    "orcid_hub.orcid_client.MemberAPI.create_or_update_affiliation", side_effect=affiliation_mock)
def test_orcid_login_callback_researcher_flow(patch, patch2, request_ctx):
    """Test login from orcid callback function for researcher and display profile."""
    org = Organisation.create(
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
    u = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=u, org=org, is_admin=False)
    token = utils.generate_confirmation_token(email=u.email, org=org.name)
    UserInvitation.create(email=u.email, token=token, affiliations=Affiliation.EMP)
    OrcidToken.create(user=u, org=org, scope='/read-limited,/activities/update')
    with request_ctx():
        request.args = {"invitation_token": token, "state": "xyz"}
        session['oauth_state'] = "xyz"
        resp = authcontroller.orcid_login_callback(request)
        assert resp.status_code == 302
        # display profile
        assert resp.location.startswith("/profile")


def test_select_user_org(request_ctx):
    """Test organisation switch of current user."""
    org = Organisation.create(
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

    org2 = Organisation.create(
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

    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)
    org.save()
    org2.save()
    user.save()
    UserOrg.create(user=user, org=org, is_admin=True)
    user_org2 = UserOrg.create(user=user, org=org2, is_admin=True)
    with request_ctx(f"/select/user_org/{user_org2.id}") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert user.organisation_id != org.id
        # Current users organisation has been changes from 1 to 2
        assert user.organisation_id == org2.id


def test_shib_sp(request_ctx):
    """Test shibboleth SP."""
    with request_ctx("/Tuakiri/SP") as ctxx:
        request.args = {'key': '123', 'url': '/profile'}
        resp = ctxx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location.startswith("/profile")


def test_get_attributes(request_ctx):
    """Test shibboleth SP."""
    key = "xyz"
    with request_ctx("/sp/attributes/" + key) as ctxx:
        resp = ctxx.app.full_dispatch_request()
        # No such file name 'xyz'
        assert resp.status_code == 403


def test_link(request_ctx):
    """Test orcid profile linking."""
    org = Organisation.create(
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

    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    with request_ctx("/link") as ctx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('error', 'access_denied')])
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"


@pytest.mark.parametrize("url", ["/faq", "/about"])
def test_faq_and_about(client, url):
    """Test faq and about page path traversal security issue."""
    resp = client.get(url + "?malicious_code")
    assert resp.status_code == 403
    resp = client.get(url)
    assert resp.status_code == 200


def test_orcid_callback(request_ctx):
    """Test orcid researcher deny flow."""
    org = Organisation.create(
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

    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)

    with request_ctx("/auth") as ctx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('error', 'access_denied'), ('login', '2')])
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location.startswith("/link")


def test_login0(client):
    """Test login from orcid."""
    from orcid_hub import current_user
    resp = client.get("/login0")
    assert resp.status_code == 401

    u = User.select().where(User.orcid.is_null(False)).first()
    email = u.email
    import itsdangerous
    signature = itsdangerous.Signer(client.application.secret_key).get_signature(email).decode()
    auth = email + ':' + signature

    resp = client.get(f"/login0/{auth}")
    assert resp.status_code == 302
    assert current_user.email == email

    resp = client.get("/login0", headers={"Authorization": auth})
    assert resp.status_code == 302
    assert current_user.email == email

    from base64 import b64encode
    resp = client.get("/login0", headers={"Authorization": b64encode(auth.encode()).decode()})
    assert resp.status_code == 302
    assert current_user.email == email


def test_load_test_data(app):
    """Test load test data generation."""
    client = app.test_client()
    client.login_root()

    resp = client.get("/test-data")
    assert resp.status_code == 200
    assert b"Load Test Data Generation" in resp.data

    resp = client.post("/test-data?user_count=123")
    assert resp.data.count(b'\n') == 123

    resp = client.post("/test-data")
    assert resp.data.count(b'\n') == 400

    import itsdangerous
    signature = itsdangerous.Signer(
        client.application.secret_key).get_signature("abc123@gmail.com")
    resp = client.post(
        "/test-data",
        data={
            "file_": (
                BytesIO(
                    b"""nks98991100099999981,paw01,ros1,abc123@gmail.com,The University of Auckland,Rosha1
nks011,paw01,ros1,2orcid100110009001@gmail.com,The University of Auckland,Rosha1,abc456@auckland.ac.nz,faculty
"""),
                "DATA.csv",
            ),
        })
    assert resp.status_code == 200
    assert signature in resp.data
    assert "DATA_SIGNED.csv" in resp.headers["Content-Disposition"]

    resp = client.post(
        "/test-data",
        data={
            "file_": (
                BytesIO(
                    "abc123@gmail.com\tUniversity\nanother@gmail.com\tThe University of Auckland".
                    encode("utf-16")),
                "DATA_WITH_TABS.csv",
            ),
        })
    assert resp.status_code == 200
    assert signature in resp.data
    assert resp.data.count(b'\n') == 2
    assert "DATA_WITH_TABS_SIGNED.csv" in resp.headers["Content-Disposition"]

    resp = client.post(
        "/test-data",
        data={
            "file_": (
                BytesIO(b"email\tname\nabc123@gmail.com\tUniversity\nanother@gmail.com\tThe University of Auckland"),
                "DATA_WITH_TABS_AND_HEADERS.csv",
            ),
        })
    assert resp.status_code == 200
    assert signature in resp.data
    assert resp.data.count(b'\n') == 2

    assert "DATA_WITH_TABS_AND_HEADERS_SIGNED.csv" in resp.headers["Content-Disposition"]

    client.logout()
