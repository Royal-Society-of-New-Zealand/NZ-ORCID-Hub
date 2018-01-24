# -*- coding: utf-8 -*-
"""Tests for core functions."""

import datetime
import json
import os
import sys
import time
from itertools import product
from unittest.mock import MagicMock, patch

import pytest
from flask import request
from flask_login import login_user
from peewee import SqliteDatabase
from playhouse.test_utils import test_database

from orcid_hub import orcid_client, views
from orcid_hub.config import ORCID_BASE_URL
from orcid_hub.forms import FileUploadForm
from orcid_hub.models import UserOrgAffiliation  # noqa: E128
from orcid_hub.models import (AffiliationRecord, Client, File, Grant, OrcidToken, Organisation,
                              OrgInfo, Role, Task, Token, Url, User, UserOrg)

fake_time = time.time()


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


def test_admin_view_access(request_ctx):
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
    with request_ctx(
            "/settings/applications",
            method="POST",
            data={
                "name": "TEST APP",
                "homepage_url": "http://test.at.test",
                "description": "TEST APPLICATION 123",
                "register": "Register",
            }) as ctx, test_database(
                app.db, (Client, Grant, Token), fail_silently=True):  # noqa: F405

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
    test_user = User.get(id=123)
    test_user.save()
    org.save()
    with request_ctx("/load/org") as ctxx:
        login_user(test_user, remember=True)
        rv = ctxx.app.full_dispatch_request()
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
    with request_ctx():
        login_user(user, remember=True)
        request._cached_json = {
            "id": 1,
            "name": "THE ORGANISATION",
            "is_admin": True,
            "is_tech_contact": True
        }
        resp = views.user_orgs_org(user_id=123)
        assert resp[1] == 200
        assert Role.ADMIN in user.roles
        organisation = Organisation.get(id=1)
        # User becomes the technical contact of the organisation.
        assert organisation.tech_contact == user


def test_user_orgs(request_ctx):
    """Test add an organisation to the user."""
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
    user_id = str(user.id)
    org_id = str(org.id)
    with request_ctx("/hub/api/v0.1/users/" + user_id + "/orgs/") as ctxx:
        login_user(user, remember=True)
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 200
    with request_ctx("/hub/api/v0.1/users/" + user_id + "/orgs/" + org_id) as ctxxx:
        login_user(user, remember=True)
        rv = ctxxx.app.full_dispatch_request()
        assert rv.status_code == 200
    with request_ctx("/hub/api/v0.1/users/" + "1234" + "/orgs/") as ctxx:
        # failure test case, user not found
        login_user(user, remember=True)
        rv = ctxx.app.full_dispatch_request()
        assert rv.status_code == 404


def test_api_credentials(request_ctx):
    """Test manage API credentials.."""
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
    user = User.get(id=123)
    org.save()
    user.save()
    UserOrg.get_or_create(id=122, user=user, org=org, is_admin=True)
    user_org = UserOrg.get(id=122)
    user_org.save()
    Client.get_or_create(
        id=1234,
        name="Test_client",
        user=user,
        org=org,
        client_id="requestd_client_id",
        client_secret="xyz",
        is_confidential="public",
        grant_type="client_credentials",
        response_type="xyz")
    client_info = Client.get(id=1234)
    client_info.save()
    with request_ctx():
        login_user(user, remember=True)
        resp = views.api_credentials()
        assert "requestd_client_id" in resp


def test_page_not_found(request_ctx):
    """Test handle nonexistin pages."""
    with request_ctx():
        resp = views.page_not_found("abc")
        assert 404 == resp[1]
        assert "Sorry, that page doesn't exist." in resp[0]


def test_action_invite(request_ctx):
    """Test handle nonexistin pages."""
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
    user = User.get(id=123)
    org.save()
    user.save()
    UserOrg.get_or_create(id=122, user=user, org=org, is_admin=True)
    user_org = UserOrg.get(id=122)
    user_org.save()
    OrgInfo.get_or_create(
        id=1234,
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
    org_info = OrgInfo.get(id=1234)
    org_info.save()
    with request_ctx():
        login_user(user, remember=True)
        views.OrgInfoAdmin.action_invite(OrgInfo, ids=[1234])
        # New organisation is created from OrgInfo and user is added with Admin role
        org2 = Organisation.get(id=2)
        assert "Test_client" == org2.name
        assert Role.ADMIN in user.roles


def test_email_template(app, request_ctx):
    """Test email maintenance."""
    org = Organisation.create(
        name="TEST0",
        tuakiri_name="TEST")
    user = User.create(
        email="admin@test.edu",
        name="TEST",
        first_name="FIRST_NAME",
        last_name="LAST_NAME",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    org.tech_contact = user
    org.save()

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
            cc_email=("TEST", "admin@test.edu"),
            logo=None,
            org_name="TEST0",
            recipient=("TEST", "admin@test.edu"),
            reply_to=("TEST", "admin@test.edu"),
            sender=("TEST", "admin@test.edu"),
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
            cc_email=("TEST", "admin@test.edu"),
            logo=f"http://{ctx.request.host}/logo/TOKEN000",
            org_name="TEST0",
            recipient=("TEST", "admin@test.edu"),
            reply_to=("TEST", "admin@test.edu"),
            sender=("TEST", "admin@test.edu"),
            subject="TEST EMAIL")
