# -*- coding: utf-8 -*-
"""Tests for core functions."""

import datetime
import json
import logging
import os
import sys
import time
from itertools import product
from unittest.mock import MagicMock, patch
from io import BytesIO

import pytest
from flask import request
from flask_login import login_user
from peewee import SqliteDatabase
from playhouse.test_utils import test_database
from werkzeug.datastructures import ImmutableMultiDict

from orcid_hub import app, orcid_client, views
from orcid_hub.config import ORCID_BASE_URL
from orcid_hub.forms import FileUploadForm
from orcid_hub.models import UserOrgAffiliation  # noqa: E128
from orcid_hub.models import (AffiliationRecord, Client, File, FundingRecord, OrcidToken, Organisation,
                              OrgInfo, Role, Task, Token, Url, User, UserInvitation, UserOrg)

fake_time = time.time()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


@pytest.fixture
def test_db():
    """Test to check db."""
    _db = SqliteDatabase(":memory:")
    with test_database(
            _db, (
                Organisation,
                User,
                UserOrg,
                OrcidToken,
                UserOrgAffiliation,
                Task,
                AffiliationRecord,
            ),
            fail_silently=True) as _test_db:
        yield _test_db

    return


@pytest.fixture
def test_models(test_db):
    """Test to check models."""
    Organisation.insert_many((dict(
        name="Organisation #%d" % i,
        tuakiri_name="Organisation #%d" % i,
        orcid_client_id="client-%d" % i,
        orcid_secret="secret-%d" % i,
        confirmed=(i % 2 == 0)) for i in range(10))).execute()

    User.insert_many((dict(
        name="Test User #%d" % i,
        first_name="Test_%d" % i,
        last_name="User_%d" % i,
        email="user%d@org%d.org.nz" % (i, i * 4 % 10),
        confirmed=(i % 3 != 0),
        roles=Role.SUPERUSER if i % 42 == 0 else Role.ADMIN if i % 13 == 0 else Role.RESEARCHER)
                      for i in range(60))).execute()

    UserOrg.insert_many((dict(is_admin=((u + o) % 23 == 0), user=u, org=o)
                         for (u, o) in product(range(2, 60, 4), range(2, 10)))).execute()

    UserOrg.insert_many((dict(is_admin=True, user=43, org=o) for o in range(1, 11))).execute()

    OrcidToken.insert_many((dict(
        user=User.get(id=1),
        org=Organisation.get(id=1),
        scope="/read-limited",
        access_token="Test_%d" % i) for i in range(60))).execute()

    UserOrgAffiliation.insert_many((dict(
        user=User.get(id=1),
        organisation=Organisation.get(id=1),
        department_name="Test_%d" % i,
        department_city="Test_%d" % i,
        role_title="Test_%d" % i,
        path="Test_%d" % i,
        put_code="%d" % i) for i in range(30))).execute()

    yield test_db


def test_superuser_view_access(request_ctx):
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
            name="TEST USER", email="test@test.test.net", username="test42", confirmed=True)
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
            confirmed=True,
            roles=Role.SUPERUSER)
        login_user(test_user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert bytes(sys.version, encoding="utf-8") in rv.data


def test_year_range():
    """Test Jinja2 filter."""
    assert views.year_range({"start_date": None, "end_date": None}) == "unknown-present"
    assert views.year_range({
        "start_date": {
            "year": {
                "value": "1998"
            },
            "whatever": "..."
        },
        "end_date": None
    }) == "1998-present"
    assert views.year_range({
        "start_date": {
            "year": {
                "value": "1998"
            },
            "whatever": "..."
        },
        "end_date": {
            "year": {
                "value": "2001"
            },
            "whatever": "..."
        }
    }) == "1998-2001"


def test_user_orcid_id_url():
    """Test to get orcid url."""
    u = User(
        email="test123@test.test.net",
        name="TEST USER",
        username="test123",
        roles=Role.RESEARCHER,
        orcid="123",
        confirmed=True)
    assert (views.user_orcid_id_url(u) == ORCID_BASE_URL + "123")
    u.orcid = None
    assert (views.user_orcid_id_url(u) == "")


@patch.object(orcid_client.MemberAPIV20Api, "view_employments",
              lambda self, *args, **kwargs: make_fake_response('{"test": "TEST1234567890"}'))
@patch.object(orcid_client.MemberAPIV20Api, "view_educations",
              lambda self, *args, **kwargs: make_fake_response('{"test": "TEST1234567890"}'))
def test_show_record_section(request_ctx, test_db):
    """Test to show selected record."""
    org = Organisation.create(
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="SOURCE")
    u = User.create(
        orcid="12123",
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.RESEARCHER,
        confirmed=True,
        organisation=org)

    OrcidToken.create(user=u, org=org, access_token="ABC123")

    with request_ctx("/"):
        login_user(u)
        rv = views.show_record_section(user_id=u.id)
        assert u.email in rv
        assert u.name in rv
    with request_ctx("/"):
        login_user(u)
        rv = views.show_record_section(user_id=u.id, section_type="EDU")
        assert u.email in rv
        assert u.name in rv


def test_status(client):
    """Test status is workinkg both when DB is accessible or not."""
    with patch("orcid_hub.views.db") as db:  # , request_ctx("/status") as ctx:
        result = MagicMock()
        result.fetchone.return_value = (datetime.datetime(2042, 1, 1, 0, 0), )
        db.execute_sql.return_value = result
        rv = client.get("/status")
        data = json.loads(rv.data)
        assert rv.status_code == 200
        assert data["status"] == "Connection successful."
        assert data["db-timestamp"] == "2042-01-01T00:00:00"

    with patch("orcid_hub.views.db") as db:  # , request_ctx("/status") as ctx:
        db.execute_sql.side_effect = Exception("FAILURE")
        rv = client.get("/status")
        data = json.loads(rv.data)
        assert rv.status_code == 503
        assert data["status"] == "Error"
        assert "FAILURE" in data["message"]


def test_application_registration(app, request_ctx):
    """Test application registration."""
    org = Organisation.create(
        can_use_api=True,
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="SOURCE")
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        organisation_id=1,
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    org.update(tech_contact=user).execute()

    with request_ctx(
            "/settings/applications",
            method="POST",
            data={
                "homepage_url": "http://test.at.test",
                "description": "TEST APPLICATION 123",
                "register": "Register",
            }) as ctx:  # noqa: F405
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        with pytest.raises(Client.DoesNotExist):
            Client.get(name="TEST APP")
        assert resp.status_code == 200

    with request_ctx(
            "/settings/applications",
            method="POST",
            data={
                "name": "TEST APP",
                "homepage_url": "http://test.at.test",
                "description": "TEST APPLICATION 123",
                "register": "Register",
            }) as ctx:  # noqa: F405
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        c = Client.get(name="TEST APP")
        assert c.homepage_url == "http://test.at.test"
        assert c.description == "TEST APPLICATION 123"
        assert c.user == user
        assert c.org == org
        assert c.client_id
        assert c.client_secret
        assert rv.status_code == 302

    client = Client.get(name="TEST APP")
    with request_ctx(f"/settings/applications/{client.id}") as ctx:

        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == f"/settings/credentials/{client.id}"

    with request_ctx("/settings/credentials") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200

    with request_ctx(f"/settings/credentials/{client.id}") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200

    with request_ctx("/settings/credentials/99999999999999") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == "/settings/applications"

    with request_ctx(
            f"/settings/credentials/{client.id}", method="POST", data={
                "revoke": "Revoke",
                "name": client.name,
            }) as ctx:
        login_user(user, remember=True)
        Token.create(client=client, token_type="TEST", access_token="TEST000")
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert Token.select().where(Token.client == client).count() == 0

    with request_ctx(
            f"/settings/credentials/{client.id}", method="POST", data={
                "reset": "Reset",
                "name": client.name,
            }) as ctx:
        login_user(user, remember=True)
        old_client = client
        resp = ctx.app.full_dispatch_request()
        client = Client.get(name="TEST APP")
        assert resp.status_code == 200
        assert client.client_id != old_client.client_id
        assert client.client_secret != old_client.client_secret

    with request_ctx(
            f"/settings/credentials/{client.id}", method="POST", data={
                "update_app": "Update",
                "name": "NEW APP NAME",
                "homepage_url": "http://test.test0.edu",
                "description": "DESCRIPTION",
                "callback_urls": "http://test0.edu/callback",
            }) as ctx:
        login_user(user, remember=True)
        old_client = client
        resp = ctx.app.full_dispatch_request()
        client = Client.get(id=client.id)
        assert resp.status_code == 200
        assert client.name == "NEW APP NAME"

    with request_ctx(
            f"/settings/credentials/{client.id}", method="POST", data={
                "delete": "Delete",
                "name": "NEW APP NAME",
            }) as ctx:
        login_user(user, remember=True)
        old_client = client
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == "/settings/applications"
        assert not Client.select().where(Client.id == client.id).exists()


def make_fake_response(text, *args, **kwargs):
    """Mock out the response object returned by requests_oauthlib.OAuth2Session.get(...)."""
    mm = MagicMock(name="response")
    mm.text = text
    if "json" in kwargs:
        mm.json.return_value = kwargs["json"]
    else:
        mm.json.return_value = json.loads(text)
    if "status_code" in kwargs:
        mm.status_code = kwargs["status_code"]
    return mm


def test_short_url(request_ctx):
    """Test short url."""
    short_url = Url.shorten("https://dev.orcidhub.org.nz/confirm/organisation/xsdsdsfdds")
    with request_ctx("/u/" + short_url.short_id) as ctxx:
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert rv.location.startswith("https://dev.orcidhub.org.nz")


def test_load_org(request_ctx):
    """Test load organisation."""
    root = User.get(email="root@test0.edu")
    with request_ctx("/load/org") as ctx:
        login_user(root, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"


def test_read_uploaded_file(request_ctx):
    """Test Uploading File."""
    with request_ctx() as ctxx:
        form = FileUploadForm()
        form.file_.name = "conftest.py"
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'conftest.py'),
                  'rb') as f:
            request.files = {'conftest.py': f}
            ctxx = views.read_uploaded_file(form)
        assert "@pytest.fixture" in ctxx


def test_user_orgs_org(request_ctx):
    """Test add an organisation to the user."""
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
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.SUPERUSER,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    with request_ctx():
        login_user(user, remember=True)
        request._cached_json = {
            "id": org.id,
            "name": org.name,
            "is_admin": True,
            "is_tech_contact": True
        }
        resp = views.user_orgs_org(user_id=user.id)
        assert resp[1] == 200
        assert Role.ADMIN in user.roles
        organisation = Organisation.get(name="THE ORGANISATION")
        # User becomes the technical contact of the organisation.
        assert organisation.tech_contact == user
    with request_ctx(method="DELETE"):
        # Delete user and organisation association
        login_user(user, remember=True)
        request._cached_json = {
            "id": org.id,
            "name": org.name,
            "is_admin": True,
            "is_tech_contact": True
        }
        resp = views.user_orgs_org(user_id=user.id)
        assert "DELETED" in resp.data.decode("utf-8")
        user = User.get(id=user.id)
        assert user.organisation_id is None


def test_user_orgs(request_ctx):
    """Test add an organisation to the user."""
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
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.SUPERUSER,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)

    with request_ctx(f"/hub/api/v0.1/users/{user.id}/orgs/") as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
    with request_ctx(f"/hub/api/v0.1/users/{user.id}/orgs/{org.id}") as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
    with request_ctx("/hub/api/v0.1/users/1234/orgs/") as ctx:
        # failure test case, user not found
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 404


def test_api_credentials(request_ctx):
    """Test manage API credentials.."""
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
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    Client.create(
        name="Test_client",
        user=user,
        org=org,
        client_id="requestd_client_id",
        client_secret="xyz",
        is_confidential="public",
        grant_type="client_credentials",
        response_type="xyz")
    with request_ctx(
            method="POST",
            data={
                "name": "TEST APP",
                "homepage_url": "http://test.at.test",
                "description": "TEST APPLICATION 123",
                "register": "Register",
                "reset": "xyz"
            }):
        login_user(user, remember=True)
        resp = views.api_credentials()
        assert "test123@test.test.net" in resp
    with request_ctx(method="POST", data={"name": "TEST APP", "delete": "xyz"}):
        login_user(user, remember=True)
        resp = views.api_credentials()
        assert resp.status_code == 302
        assert "application" in resp.location


def test_page_not_found(request_ctx):
    """Test handle nonexistin pages."""
    with request_ctx():
        resp = views.page_not_found("abc")
        assert 404 == resp[1]
        assert "Sorry, that page doesn't exist." in resp[0]


def send_mail_mock(*argvs, **kwargs):
    """Mock email invitation."""
    app.logger.info(f"***\nActually email invitation was mocked, so no email sent!!!!!")
    return True


@patch("orcid_hub.utils.send_email", side_effect=send_mail_mock)
def test_action_invite(patch, request_ctx):
    """Test handle nonexistin pages."""
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
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    org_info = OrgInfo.create(
        name="Test_client",
        tuakiri_name="xyz",
        title="mr",
        first_name="xyz",
        last_name="xyz",
        role="lead",
        email="test123@test.test.net",
        phone="121",
        is_public=True,
        country="NZ",
        city="Auckland",
        disambiguated_id="123",
        disambiguation_source="ringgold")
    with request_ctx():
        login_user(user, remember=True)
        views.OrgInfoAdmin.action_invite(OrgInfo, ids=[org_info.id])
        # New organisation is created from OrgInfo and user is added with Admin role
        org2 = Organisation.get(name="Test_client")
        assert user.is_admin_of(org2)
        assert Role.ADMIN in user.roles


def test_shorturl(request_ctx):
    """Test short url."""
    url = "http://localhost/xsdsdsfdds"
    with request_ctx():
        rv = views.shorturl(url)
        assert "http://" in rv


def test_activate_all(request_ctx):
    """Test batch registraion of users."""
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
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid=123,
        organisation_id=1,
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)

    task1 = Task.create(
        org=org,
        completed_at="12/12/12",
        filename="xyz.txt",
        created_by=user,
        updated_by=user,
        task_type=0)
    task2 = Task.create(
        org=org,
        completed_at="12/12/12",
        filename="xyz.txt",
        created_by=user,
        updated_by=user,
        task_type=1)

    with request_ctx("/activate_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/affiliation_record_activate_for_batch')])
        request.form = ImmutableMultiDict([('task_id', task1.id)])
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert rv.location.startswith("http://localhost/affiliation_record_activate_for_batch")
    with request_ctx("/activate_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/funding_record_activate_for_batch')])
        request.form = ImmutableMultiDict([('task_id', task2.id)])
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert rv.location.startswith("http://localhost/funding_record_activate_for_batch")


def test_logo(request_ctx):
    """Test manage organisation 'logo'."""
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
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    with request_ctx("/settings/logo", method="POST") as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
    with request_ctx("/logo/token_123") as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert rv.location.endswith("images/banner-small.png")


@patch("orcid_hub.utils.send_email", side_effect=send_mail_mock)
def test_manage_email_template(patch, request_ctx):
    """Test manage organisation invitation email template."""
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
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    with request_ctx(
            "/settings/email_template",
            method="POST",
            data={
                "name": "TEST APP",
                "homepage_url": "http://test.at.test",
                "description": "TEST APPLICATION 123",
                "email_template": "enable",
                "save": "Save"
            }) as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        org = Organisation.get(id=org.id)
        assert org.email_template == "enable"
    with request_ctx(
            "/settings/email_template",
            method="POST",
            data={
                "name": "TEST APP",
                "email_template_enabled": "true",
                "email_address": "test123@test.test.net",
                "send": "Save"
            }) as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"


def send_mail_mock(*argvs, **kwargs):
    """Mock email invitation."""
    logger.info(f"***\nActually email invitation was mocked, so no email sent!!!!!")
    return True


def test_invite_user(request_ctx):
    """Test invite a researcher to join the hub."""
    org = Organisation.get(name="TEST0")
    admin = User.get(email="admin@test0.edu")
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org)
    UserInvitation.create(
        invitee=user,
        inviter=admin,
        org=org,
        email="test1234456@mailinator.com",
        token="xyztoken")
    with request_ctx("/invite/user") as ctx:
        login_user(admin, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert org.name.encode() in rv.data
    with request_ctx(
            "/invite/user",
            method="POST",
            data={
                "name": "TEST APP",
                "is_employee": "false",
                "email_address": "test123@test.test.net",
                "resend": "enable",
                "is_student": "true",
                "first_name": "test",
                "last_name": "test",
                "city": "test"
            }) as ctx, patch("orcid_hub.views.send_user_invitation") as send_user_invitation:
        login_user(admin, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"test123@test.test.net" in rv.data
        send_user_invitation.assert_called_once()


def test_email_template(app, request_ctx):
    """Test email maintenance."""
    org = Organisation.get(name="TEST0")
    user = User.get(email="admin@test0.edu")

    with request_ctx(
            "/settings/email_template",
            method="POST",
            data={
                "email_template_enabled": "y",
                "prefill": "Pre-fill",
            }) as ctx:
        login_user(user)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"&lt;!DOCTYPE html&gt;" in rv.data
        org.reload()
        assert not org.email_template_enabled

    with patch("orcid_hub.utils.send_email") as send_email, request_ctx(
            "/settings/email_template",
            method="POST",
            data={
                "email_template_enabled": "y",
                "email_template": "TEST TEMPLATE {EMAIL}",
                "send": "Send",
            }) as ctx:
        login_user(user)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        org.reload()
        assert not org.email_template_enabled
        send_email.assert_called_once_with(
            "email/test.html",
            base="TEST TEMPLATE {EMAIL}",
            cc_email=("TEST ORG #0 ADMIN", "admin@test0.edu"),
            logo=None,
            org_name="TEST0",
            recipient=("TEST ORG #0 ADMIN", "admin@test0.edu"),
            reply_to=("TEST ORG #0 ADMIN", "admin@test0.edu"),
            sender=("TEST ORG #0 ADMIN", "admin@test0.edu"),
            subject="TEST EMAIL")

    with request_ctx(
            "/settings/email_template",
            method="POST",
            data={
                "email_template_enabled": "y",
                "email_template": "TEST TEMPLATE TO SAVE",
                "save": "Save",
            }) as ctx:
        login_user(user)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        org.reload()
        assert org.email_template_enabled
        assert "TEST TEMPLATE TO SAVE" in org.email_template

    with patch("emails.message.Message") as msg_cls, request_ctx(
            "/settings/email_template",
            method="POST",
            data={
                "email_template_enabled": "y",
                "email_template": app.config["DEFAULT_EMAIL_TEMPLATE"],
                "send": "Send",
            }) as ctx:
        login_user(user)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        org.reload()
        assert org.email_template_enabled
        msg_cls.assert_called_once()
        _, kwargs = msg_cls.call_args
        assert kwargs["subject"] == "TEST EMAIL"
        assert kwargs["mail_from"] == (
            "NZ ORCID HUB",
            "no-reply@orcidhub.org.nz",
        )
        assert "<!DOCTYPE html>\n<html>\n" in kwargs["html"]
        assert "TEST0" in kwargs["text"]

    org.logo = File.create(
        filename="LOGO.png",
        data=b"000000000000000000000",
        mimetype="image/png",
        token="TOKEN000")
    org.save()
    user.reload()
    with patch("orcid_hub.utils.send_email") as send_email, request_ctx(
            "/settings/email_template",
            method="POST",
            data={
                "email_template_enabled": "y",
                "email_template": "TEST TEMPLATE {EMAIL}",
                "send": "Send",
            }) as ctx:
        login_user(user)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        org.reload()
        assert org.email_template_enabled
        send_email.assert_called_once_with(
            "email/test.html",
            base="TEST TEMPLATE {EMAIL}",
            cc_email=("TEST ORG #0 ADMIN", "admin@test0.edu"),
            logo=f"http://{ctx.request.host}/logo/TOKEN000",
            org_name="TEST0",
            recipient=("TEST ORG #0 ADMIN", "admin@test0.edu"),
            reply_to=("TEST ORG #0 ADMIN", "admin@test0.edu"),
            sender=("TEST ORG #0 ADMIN", "admin@test0.edu"),
            subject="TEST EMAIL")


def test_logo_file(request_ctx):
    """Test logo support."""
    org = Organisation.get(name="TEST0")
    user = User.get(email="admin@test0.edu")
    with request_ctx(
            "/settings/logo",
            method="POST",
            data={
                "upload": "Upload",
                "logo_file": (
                    BytesIO(b"FAKE IMAGE"),
                    "logo.png",
                ),
            }) as ctx:
        login_user(user)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        org.reload()
        assert org.logo is not None
        assert org.logo.filename == "logo.png"
    with request_ctx(
            "/settings/logo",
            method="POST",
            data={
                "reset": "Reset",
            }) as ctx:
        login_user(user)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        org.reload()
        assert org.logo is None


@patch("orcid_hub.utils.send_email", side_effect=send_mail_mock)
def test_invite_organisation(send_email, request_ctx):
    """Test invite an organisation to register."""
    org = Organisation.get(name="TEST0")
    root = User.get(email="root@test0.edu")
    user = User.create(
        email="test123@test.test.net", name="TEST USER", confirmed=True, organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    with request_ctx(
            "/invite/organisation",
            method="POST",
            data={
                "org_name": "THE ORGANISATION",
                "org_email": "test123@test.test.net",
                "tech_contact": "True",
                "via_orcid": "True",
                "first_name": "xyz",
                "last_name": "xyz",
                "city": "xyz"
            }) as ctx:
        login_user(root, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"test123@test.test.net" in rv.data
        send_email.assert_called_once()
    with request_ctx(
            "/invite/organisation",
            method="POST",
            data={
                "org_name": "ORG NAME",
                "org_email": "test123@test.test.net",
                "tech_contact": "True",
                "via_orcid": "True",
                "first_name": "xyz",
                "last_name": "xyz",
                "city": "xyz"
            }) as ctx:
        send_email.reset_mock()
        login_user(root, remember=True)
        org = Organisation.get(id=1)
        org.name = "ORG NAME"
        org.confirmed = True
        org.save()
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"test123@test.test.net" in rv.data
        send_email.assert_called_once()


def core_mock(self=None, source_file=None, schema_files=None, source_data=None, schema_data=None, extensions=None,
              strict_rule_validation=False,
              fix_ruby_style_regex=False, allow_assertions=False, ):
    """Mock validation api call."""
    return None


def validate(self=None, raise_exception=True):
    """Mock validation api call."""
    return False


@patch("pykwalify.core.Core.validate", side_effect=validate)
@patch("pykwalify.core.Core.__init__", side_effect=core_mock)
def test_load_researcher_funding(patch, patch2, request_ctx):
    """Test preload organisation data."""
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
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.ADMIN,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    with request_ctx(
            "/load/researcher/funding",
            method="POST",
            data={
                "file_": (
                        BytesIO(
                            b'[{"title": { "title": { "value": "1ral"}},"short-description": "Mi","type": "CONTRACT",'
                            b'"contributors": {"contributor": [{"contributor-attributes": {"contributor-role": '
                            b'"co_lead"},"credit-name": {"value": "firentini"},"contributor-email": {"value": '
                            b'"ma1@mailinator.com"}}]}, "external-ids": {"external-id": [{"external-id-value": '
                            b'"GNS170661","external-id-type": "grant_number"}]}}]'),
                        "logo.json",),
                "email": user.email
            }) as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302
        # Funding file successfully loaded.
        assert "task_id" in rv.location
        assert "funding" in rv.location


def test_load_researcher_affiliations(request_ctx):
    """Test preload organisation data."""
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
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.ADMIN,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    form = FileUploadForm()
    form.file_.name = "conftest.py"
    with request_ctx("/load/researcher", method="POST", data={"file_": "{'filename': 'xyz.json'}",
                                                              "email": user.email, form: form}) as ctxx:
        login_user(user, remember=True)
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert user.email.encode() in rv.data


@patch.object(orcid_client.MemberAPIV20Api, "view_employment",
              lambda self, *args, **kwargs: make_fake_response('{"test": "TEST1234567890"}'))
@patch.object(orcid_client.MemberAPIV20Api, "view_education",
              lambda self, *args, **kwargs: make_fake_response('{"test": "TEST1234567890"}'))
def test_edit_section_record(request_ctx, test_db):
    """Test create a new or edit an existing profile section record."""
    org = Organisation.create(
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="SOURCE")
    u = User.create(
        orcid="12123",
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.RESEARCHER,
        confirmed=True,
        organisation=org)

    OrcidToken.create(user=u, org=org, access_token="ABC123", scope="/read-limited,/activities/update")
    with request_ctx("/"):
        login_user(u)
        rv = views.edit_section_record(user_id=u.id, put_code="1212")
        assert u.email in rv
        assert u.name in rv
    with request_ctx("/"):
        login_user(u)
        rv = views.edit_section_record(user_id=u.id, put_code="1212", section_type="EDU")
        assert u.email in rv
        assert u.name in rv


@patch.object(orcid_client.MemberAPIV20Api, "delete_employment",
              lambda self, *args, **kwargs: make_fake_response('{"test": "TEST1234567890"}'))
def test_delete_employment(request_ctx, test_db):
    """Test delete an employment record."""
    org = Organisation.create(
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="SOURCE")
    u = User.create(
        orcid="12123",
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.ADMIN,
        confirmed=True,
        organisation=org)

    OrcidToken.create(user=u, org=org, access_token="ABC123", scope="/read-limited,/activities/update")
    with request_ctx("/"):
        login_user(u)
        rv = views.delete_employment(user_id=u.id, put_code="1212")
        assert rv.status_code == 302


def test_viewmemebers(request_ctx):
    """Test affilated researcher view."""
    non_admin = User.get(email="researcher100@test0.edu")
    with request_ctx("/admin/viewmembers") as ctx:
        login_user(non_admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302

    admin = User.get(email="admin@test0.edu")
    with request_ctx("/admin/viewmembers") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"researcher100@test0.edu" in resp.data

    with request_ctx(f"/admin/viewmembers/edit/?id={non_admin.id}") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert non_admin.email.encode() in resp.data
        assert non_admin.name.encode() in resp.data

    user2 = User.get(email="researcher100@test1.edu")
    with request_ctx(f"/admin/viewmembers/edit/?id={user2.id}") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 403


def test_reset_all(request_ctx):
    """Test reset batch process."""
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

    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid=123,
        organisation_id=1,
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)

    task1 = Task.create(
        id=1,
        org=org,
        completed_at="12/12/12",
        filename="xyz.txt",
        created_by=user,
        updated_by=user,
        task_type=0)

    AffiliationRecord.create(
        is_active=True,
        task=task1,
        external_id="Test",
        first_name="Test",
        last_name="Test",
        email="test1234456@mailinator.com",
        orcid="123112311231",
        organisation="asdasd",
        affiliation_type="staff",
        role="Test",
        department="Test",
        city="Test",
        state="Test",
        country="Test",
        disambiguated_id="Test",
        disambiguated_source="Test")

    UserInvitation.create(
        invitee=user,
        inviter=user,
        org=org,
        task=task1,
        email="test1234456@mailinator.com",
        token="xyztoken")

    task2 = Task.create(
        id=2,
        org=org,
        completed_at="12/12/12",
        filename="xyz.txt",
        created_by=user,
        updated_by=user,
        task_type=1)

    FundingRecord.create(
        task=task2,
        title="Test titile",
        translated_title="Test title",
        translated_title_language_code="Test",
        type="GRANT",
        organization_defined_type="Test org",
        short_description="Test desc",
        amount="1000",
        currency="USD",
        org_name="Test_orgname",
        city="Test city",
        region="Test",
        country="Test",
        disambiguated_org_identifier="Test_dis",
        disambiguation_source="Test_source",
        is_active=True,
        visibility="Test_visibity")

    with request_ctx("/reset_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/affiliation_record_reset_for_batch')])
        request.form = ImmutableMultiDict([('task_id', task1.id)])
        rv = ctxx.app.full_dispatch_request()
        t = Task.get(id=1)
        ar = AffiliationRecord.get(id=1)
        assert "The record was reset" in ar.status
        assert t.completed_at is None
        assert rv.status_code == 302
        assert rv.location.startswith("http://localhost/affiliation_record_reset_for_batch")
    with request_ctx("/reset_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/funding_record_reset_for_batch')])
        request.form = ImmutableMultiDict([('task_id', task2.id)])
        rv = ctxx.app.full_dispatch_request()
        t2 = Task.get(id=2)
        fr = FundingRecord.get(id=1)
        assert "The record was reset" in fr.status
        assert t2.completed_at is None
        assert rv.status_code == 302
        assert rv.location.startswith("http://localhost/funding_record_reset_for_batch")
