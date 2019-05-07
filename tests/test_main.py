# -*- coding: utf-8 -*-
"""Tests for core functions."""

import base64
from datetime import timedelta
import pickle
import pprint
import zlib
from io import BytesIO
from unittest.mock import patch, Mock
from urllib.parse import urlparse

from click.testing import CliRunner
import pytest
from flask import request, session
from flask_login import current_user, login_user, logout_user
from peewee import fn
from werkzeug.datastructures import ImmutableMultiDict

from orcid_hub import authcontroller, create_hub_administrator, login_provider, utils
from orcid_hub.models import (Affiliation, OrcidAuthorizeCall, OrcidToken, Organisation, OrgInfo,
                              OrgInvitation, Role, User, UserInvitation, UserOrg)


def test_create_hub_administrator(app):
    """Test creation of the Hub administrators."""
    org = app.data["org"]
    runner = CliRunner()
    runner.invoke(create_hub_administrator, ["root000@test.ac.nz"])
    assert User.select().where(User.email == "root000@test.ac.nz").exists()
    assert Organisation.select().where(Organisation.name == "ORCID Hub").exists()
    runner.invoke(create_hub_administrator, ["root000@test.ac.nz", "-O", "NEW ORGANISATION #0"])
    assert Organisation.select().where(Organisation.name == "NEW ORGANISATION #0").exists()
    assert User.get(email="root000@test.ac.nz").organisation.name == "NEW ORGANISATION #0"

    runner.invoke(create_hub_administrator, ["root001@test.ac.nz", "-O", "NEW ORG"])
    assert Organisation.select().where(Organisation.name == "NEW ORG").exists()
    assert User.get(email="root001@test.ac.nz").organisation.name == "NEW ORG"

    org_count = Organisation.select().count()
    runner.invoke(create_hub_administrator, ["root002@test.ac.nz", "-O", org.name])
    assert Organisation.select().count() == org_count
    assert User.get(email="root002@test.ac.nz").organisation.name == org.name

    runner.invoke(create_hub_administrator, ["root010@test.ac.nz", "-I", "INTERNAL NAME 111"])
    assert User.select().where(User.email == "root010@test.ac.nz").exists()
    assert Organisation.select().where(Organisation.name == "ORCID Hub",
                                       Organisation.tuakiri_name == "INTERNAL NAME 111").exists()
    assert User.get(email="root010@test.ac.nz").organisation.tuakiri_name == "INTERNAL NAME 111"

    runner.invoke(create_hub_administrator,
                  ["root011@test.ac.nz", "-O", "NEW ORG", "-I", "INTERNAL NAME 222"])
    assert Organisation.select().where(Organisation.name == "NEW ORG",
                                       Organisation.tuakiri_name == "INTERNAL NAME 222").exists()
    assert User.get(email="root011@test.ac.nz").organisation.tuakiri_name == "INTERNAL NAME 222"

    org_count = Organisation.select().count()
    runner.invoke(create_hub_administrator, ["root012@test.ac.nz", "-O", org.name, "-I", "INTERNAL NAME 333"])
    assert Organisation.select().count() == org_count
    assert User.get(email="root012@test.ac.nz").organisation.tuakiri_name == "INTERNAL NAME 333"


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
            name="TEST USER", email="test@test.test.net", confirmed=True)
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
    user_orgs = UserOrg.select().join(User).where(User.orcid == user.orcid)
    new_org = Organisation.select().where(Organisation.id.not_in([uo.org_id for uo in user_orgs])).first()
    UserOrg.create(user=user, org=new_org, affiliations=0)

    resp = client.login(user, follow_redirects=True)
    assert user.email.encode() in resp.data
    assert len(user.org_links) > 1
    assert current_user == user

    # Nothing changes if it is the same organisation
    uo = user.userorg_set.where(UserOrg.org_id == user.organisation_id).first()
    resp = client.get(f"/select/user_org/{uo.id}", follow_redirects=True)
    assert User.get(user.id).organisation_id == user.organisation_id
    assert user.email.encode() in resp.data

    # The current org changes if it's a dirrerent org on the list
    uo = user.userorg_set.where(UserOrg.org_id != user.organisation_id).first()
    resp = client.get(f"/select/user_org/{uo.id}", follow_redirects=True)
    assert User.get(user.id).organisation_id != user.organisation_id
    assert User.get(user.id).organisation_id == uo.org_id

    for ol in user.org_links:
        assert ol.org.name.encode() in resp.data
        if UserOrg.get(ol.id).user.id != user.id:
            next_ol = ol

    # Shoud be a totally different user account:
    resp = client.get(f"/select/user_org/{next_ol.id}", follow_redirects=True)
    next_user = UserOrg.get(next_ol.id).user
    assert next_user.id != user.id


def test_access(client):
    """Test access to the app for unauthorized user."""
    for url in ["/link", "/auth", "/pyinfo", "/invite/organisation", "/invite/user"]:
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
    data = {
        "Auedupersonsharedtoken": "ABC123",
        "Sn": "LAST NAME/SURNAME/FAMILY NAME",
        'Givenname': "FIRST NAME/GIVEN NAME",
        "Mail": "user@test.test.net",
        "O": "ORGANISATION 123",
        "Displayname": "TEST USER FROM 123",
        "Unscoped-Affiliation": "staff",
        "Eppn": "user@test.test.net"
    }

    resp = client.get("/sso/login", headers=data)

    assert resp.status_code == 302
    u = User.get(email="user@test.test.net")
    assert u.name == "TEST USER FROM 123", "Expected to have the user in the DB"
    assert u.first_name == "FIRST NAME/GIVEN NAME"
    assert u.last_name == "LAST NAME/SURNAME/FAMILY NAME"


def test_sso_loging_with_external_sp(client, mocker):
    """Test with EXTERNAL_SP."""
    data = {
        "Auedupersonsharedtoken": "ABC123",
        "Sn": "LAST NAME/SURNAME/FAMILY NAME",
        'Givenname': "FIRST NAME/GIVEN NAME",
        "Mail": "test_external_sp@test.ac.nz;secondory@test.edu",
        "O": client.data["org"].name,
        "Displayname": "TEST USER #42",
        "Unscoped-Affiliation": "staff",
        "Eppn": "user@test.test.net"
    }

    client.application.config["EXTERNAL_SP"] = "https://exernal.ac.nz/SP"
    resp = client.get("/index")
    assert b"https://exernal.ac.nz/SP" in resp.data
    get = mocker.patch(
        "requests.get",
        return_value=Mock(text=base64.b64encode(zlib.compress(pickle.dumps(data)))))

    resp = client.get("/sso/login", follow_redirects=True)
    get.assert_called_once()
    assert b"TEST USER #42" in resp.data
    assert b"test_external_sp@test.ac.nz" in resp.data
    u = User.get(email="test_external_sp@test.ac.nz")
    assert u.name == "TEST USER #42"


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
    org = client.data.get("org")
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


def test_onboard_org(client):
    """Test to organisation onboarding."""
    org = Organisation.create(
        name="THE ORGANISATION:test_onboard_org",
        tuakiri_name="THE ORGANISATION:test_onboard_org",
        confirmed=False,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="RINGGOLD",
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
    UserOrg.create(user=second_user, org=org, is_admin=True)
    org_info = OrgInfo.create(
        name="A NEW ORGANISATION", tuakiri_name="A NEW ORGANISATION")
    org.tech_contact = u
    org_info.save()
    org.save()

    client.login_root()
    with patch("orcid_hub.utils.send_email"):
        resp = client.post(
            "/invite/organisation",
            data=dict(org_name="A NEW ORGANISATION", org_email="test_abc_123@test.test.net"),
            follow_redirects=True)
        assert User.select().where(User.email == "test_abc_123@test.test.net").exists()
        resp = client.post(
            "/invite/organisation",
            data=dict(
                org_name="A NEW ORGANISATION",
                org_email="test12345@test.test.net",
                tech_contact='y'),
            follow_redirects=True)
        assert User.select().where(User.email == "test12345@test.test.net").exists()
    org = Organisation.get(name="A NEW ORGANISATION")
    user = User.get(email="test12345@test.test.net")
    assert user.name is None
    assert org.tech_contact == user
    client.logout()

    resp = client.login(
        user,
        **{
            "Sn": "TECHNICAL",
            "Givenname": "CONTACT",
            "Displayname": "Test User",
            "shib_O": "NEW ORGANISATION"
        },
        follow_redirects=True)
    user = User.get(email="test12345@test.test.net")
    org = user.organisation
    assert user.is_tech_contact_of(org)
    resp = client.get("/confirm/organisation")
    assert resp.status_code == 200
    org = Organisation.get(org.id)
    assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
    assert b"Take me to ORCID to obtain my Client ID and Client Secret" in resp.data

    with patch("orcid_hub.authcontroller.requests") as requests:
        requests.post.return_value = Mock(data=b'XXXX', status_code=200)
        resp = client.post(
            "/confirm/organisation",
            data={
                "orcid_client_id": "APP-1234567890ABCDEF",
                "orcid_secret": "12345678-1234-1234-1234-1234567890ab",
                "country": "NZ",
                "city": "Auckland",
                "disambiguated_id": "XYZ123",
                "disambiguation_source": "RINGGOLD",
                "name": org.name,
                "email": user.email,
            })
    assert resp.status_code == 302
    url = urlparse(resp.location).path
    assert url == "/link"
    resp = client.get(url)
    client.logout()
    org = Organisation.get(org.id)
    assert org.disambiguated_id == "XYZ123"
    assert org.disambiguation_source == "RINGGOLD"
    assert org.orcid_client_id == "APP-1234567890ABCDEF"
    assert org.orcid_secret == "12345678-1234-1234-1234-1234567890ab"

    user = User.get(email="test_abc_123@test.test.net")
    resp = client.login(
        user,
        **{
            "Sn": "NEW ORGANISATION",
            "Givenname": "ADMINISTRATOR",
            "Displayname": "Admin User",
            "shib_O": "NEW ORGANISATION"
        },
        follow_redirects=True)
    assert b"Take me to ORCID to allow A NEW ORGANISATION permission to access my ORCID record" in resp.data
    resp = client.get("/confirm/organisation")
    assert resp.status_code == 302
    assert urlparse(resp.location).path == "/admin/viewmembers/"

    resp = client.get("/admin/viewmembers/")
    assert b"test12345@test.test.net" in resp.data

    resp = client.get("/admin/viewmembers/export/csv/")
    assert resp.headers["Content-Type"] == "text/csv; charset=utf-8"
    assert b"test12345@test.test.net" in resp.data
    assert b"test_abc_123@test.test.net" in resp.data


@patch("orcid_hub.utils.send_email")
def test_invite_tech_contact(send_email, client):
    """Test on-boarding of an org."""
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
    assert oi.org.tech_contact == u
    send_email.assert_called_once()
    client.logout()

    # Test invited user login:
    client.login(u, **{"Sn": "Surname", "Givenname": "Givenname", "Displayname": "Test User"})
    u = User.get(email=email)
    assert u.confirmed
    assert u.organisation.tech_contact == u


def test_logout(client):
    """Test to logout."""
    org = Organisation.create(
        name="THE ORGANISATION:test_logout",
        tuakiri_name="University of Auckland",
        confirmed=True,
        is_email_sent=True)
    user = User.create(
        email="test@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        confirmed=True,
        organisation=org)

    client.login(user)
    resp = client.get("/logout")
    # UoA user:
    assert resp.status_code == 302
    assert "Shibboleth.sso" in resp.location
    assert "uoa-slo" in resp.location

    org.tuakiri_name = org.name
    org.save()
    client.login(user)
    resp = client.get("/logout")
    # non-UoA user:
    assert resp.status_code == 302
    assert "Shibboleth.sso" in resp.location
    assert "uoa-slo" not in resp.location


def test_orcid_login(client):
    """Test login from orcid."""
    org = Organisation.get(name="THE ORGANISATION")
    u = User.create(
        email="test123_test_orcid_login@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)
    user_org = UserOrg.create(user=u, org=org, is_admin=True)
    token = "TOKEN-1234567"
    ui = UserInvitation.create(org=org, invitee=u, email=u.email, token=token)
    resp = client.get(f"/orcid/login/{token}")
    assert resp.status_code == 200
    orcid_authorize = OrcidAuthorizeCall.get(method="GET")
    assert "&email=test123_test_orcid_login%40test.test.net" in orcid_authorize.url
    ui.created_at -= timedelta(days=100)
    ui.save()
    resp = client.get(f"/orcid/login/{token}")
    assert resp.status_code == 302
    url = urlparse(resp.location)
    assert url.path == '/'
    # Testing the expired token flow for researcher
    user_org.is_admin = False
    user_org.save()
    resp = client.get(f"/orcid/login/{token}")
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
        name="THE ORGANISATION:test_orcid_login_callback_admin_flow",
        tuakiri_name="THE ORGANISATION:test_orcid_login_callback_admin_flow",
        confirmed=False,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="RINGGOLD",
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
        request.args = {"invitation_token": None, "state": "xyz-about"}
        session['oauth_state'] = "xyz-about"
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
        name="THE ORGANISATION:test_orcid_login_callback_researcher_flow",
        tuakiri_name="THE ORGANISATION:test_orcid_login_callback_researcher_flow",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="RINGGOLD",
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
    OrcidToken.create(user=u, org=org, scope="/read-limited,/activities/update")
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
        name="THE ORGANISATION:test_select_user_org",
        tuakiri_name="THE ORGANISATION:test_select_user_org",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="RINGGOLD",
        is_email_sent=True)
    org2 = Organisation.create(
        name="THE ORGANISATION2:test_select_user_org",
        tuakiri_name="THE ORGANISATION2:test_select_user_org",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="RINGGOLD",
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


def test_shib_sp(client):
    """Test shibboleth SP."""
    resp = client.get("/Tuakiri/SP?key=123ABC&url=/profile", headers={"USER": "TEST123ABC"})
    assert resp.status_code == 302
    assert "/profile" in resp.location

    resp = client.get("/sp/attributes/123ABC")
    assert resp.status_code == 200
    data = pickle.loads(zlib.decompress(base64.b64decode(resp.data)))
    assert data["User"] == "TEST123ABC"

    resp = client.get("/Tuakiri/SP?key=123&url=https://harmfull.one/profile")
    assert resp.status_code == 403


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
        name="THE ORGANISATION:test_link",
        tuakiri_name="THE ORGANISATION:test_link",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="RINGGOLD",
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


def test_orcid_callback(client, mocker):
    """Test orcid researcher deny flow."""
    org = Organisation.create(
        name="THE ORGANISATION:test_orcid_callback",
        tuakiri_name="THE ORGANISATION:test_orcid_callback",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="RINGGOLD",
        is_email_sent=True)
    user = User.create(
        email="test123_test_orcid_callback@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)

    client.login(user)
    resp = client.get("/auth?error=access_denied&login=2")
    assert resp.status_code == 302
    assert "/link" in resp.location


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
