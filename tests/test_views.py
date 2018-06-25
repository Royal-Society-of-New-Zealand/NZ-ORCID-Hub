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
from flask import request, make_response
from flask_login import login_user
from peewee import SqliteDatabase
from playhouse.test_utils import test_database
from werkzeug.datastructures import ImmutableMultiDict

from orcid_hub import app, orcid_client, rq, views
from orcid_hub.config import ORCID_BASE_URL
from orcid_hub.forms import FileUploadForm
from orcid_hub.models import UserOrgAffiliation  # noqa: E128
from orcid_hub.models import (Affiliation, AffiliationRecord, Client, File, FundingRecord,
                              OrcidToken, Organisation, OrgInfo, Role, Task, Token, Url, User,
                              UserInvitation, UserOrg, PeerReviewRecord, WorkRecord)

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
    with request_ctx("/admin/schedude/") as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 403
        assert b"403" in rv.data

    user = User.create(
        name="TEST USER",
        email="test@test.test.net",
        roles=Role.SUPERUSER,
        username="test42",
        confirmed=True)

    with request_ctx("/admin/user/") as ctx:
        login_user(user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"User" in rv.data

    with request_ctx(f"/admin/user/edit/?id={user.id}") as ctx:
        login_user(user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"TEST USER" in rv.data

    with request_ctx("/admin/schedude/") as ctx:
        login_user(user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"interval" in rv.data

    jobs = rq.get_scheduler().get_jobs()
    with request_ctx(f"/admin/schedude/details/?id={jobs[0].id}") as ctx:
        login_user(user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"interval" in rv.data


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


def test_access(request_ctx):
    """Test access to differente resources."""
    test_superuser = User.create(
        name="TEST SUPERUSER",
        email="super@test.test.net",
        username="test42",
        confirmed=True,
        roles=Role.SUPERUSER)
    test_user = User.create(
        name="TEST SUPERUSER",
        email="user123456789@test.test.net",
        username="test123456789",
        confirmed=True,
        roles=Role.RESEARCHER)

    with request_ctx("/pyinfo") as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302

    with request_ctx("/rq") as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 401
        assert b"401" in rv.data

    with request_ctx("/rq?next=http://orcidhub.org.nz/next") as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert rv.location == "http://orcidhub.org.nz/next"

    with request_ctx("/pyinfo") as ctx:
        login_user(test_superuser, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert bytes(sys.version, encoding="utf-8") in rv.data

    with request_ctx("/pyinfo") as ctx:
        login_user(test_user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302

    with request_ctx("/rq") as ctx:
        login_user(test_superuser, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"Queues" in rv.data

    with request_ctx("/rq") as ctx:
        login_user(test_user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 403
        assert b"403" in rv.data

    with request_ctx("/rq?next=http://orcidhub.org.nz/next") as ctx:
        login_user(test_user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert rv.location == "http://orcidhub.org.nz/next"


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


def test_show_record_section(request_ctx):
    """Test to show selected record."""
    admin = User.get(email="admin@test0.edu")
    user = User.get(email="researcher100@test0.edu")
    if not user.orcid:
        user.orcid = "XXXX-XXXX-XXXX-0001"
        user.save()

    OrcidToken.create(user=user, org=user.organisation, access_token="ABC123")

    with patch.object(
            orcid_client.MemberAPIV20Api,
            "view_employments",
            MagicMock(return_value=make_fake_response('{"test": "TEST1234567890"}'))
    ) as view_employments, request_ctx(f"/section/{user.id}/EMP/list") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_employments.assert_called_once_with("XXXX-XXXX-XXXX-0001")
    with patch.object(
            orcid_client.MemberAPIV20Api,
            "view_educations",
            MagicMock(return_value=make_fake_response('{"test": "TEST1234567890"}'))
    ) as view_educations, request_ctx(f"/section/{user.id}/EDU/list") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_educations.assert_called_once_with("XXXX-XXXX-XXXX-0001")


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
    short_url = Url.shorten("https://HOST/confirm/organisation/ABCD1234")
    with request_ctx("/u/" + short_url.short_id) as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == "https://HOST/confirm/organisation/ABCD1234"

    with request_ctx("/u/" + short_url.short_id + "?param=PARAM123") as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == "https://HOST/confirm/organisation/ABCD1234?param=PARAM123"

    with request_ctx("/u/DOES_NOT_EXIST") as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 404


def test_load_org(request_ctx):
    """Test load organisation."""
    root = User.get(email="root@test0.edu")
    with request_ctx("/load/org") as ctx:
        login_user(root, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"


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
    with request_ctx(
            f"/hub/api/v0.1/users/{user.id}/orgs/",
            data=json.dumps({
                "id": org.id,
                "name": org.name,
                "is_admin": True,
                "is_tech_contact": True
            }),
            method="POST",
            content_type="application/json") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 201
        assert User.get(id=user.id).roles & Role.ADMIN
        organisation = Organisation.get(name="THE ORGANISATION")
        # User becomes the technical contact of the organisation.
        assert organisation.tech_contact == user
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert UserOrg.select().where(UserOrg.user == user, UserOrg.org == org,
                                      UserOrg.is_admin).exists()
    with request_ctx(f"/hub/api/v0.1/users/{user.id}/orgs/{org.id}", method="DELETE") as ctx:
        # Delete user and organisation association
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 204
        data = json.loads(resp.data)
        user = User.get(id=user.id)
        assert data["status"] == "DELETED"
        assert user.organisation_id is None
        assert not (user.roles & Role.ADMIN)
        assert not UserOrg.select().where(UserOrg.user == user, UserOrg.org == org).exists()


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
    with request_ctx("/this/does/not/exist") as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 404
        assert b"Sorry, that page doesn't exist." in resp.data

    with request_ctx("/this/does/not/exist/?url=/something/else") as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == "/something/else"


def test_favicon(request_ctx):
    """Test favicon."""
    with request_ctx("/favicon.ico") as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert resp.mimetype == "image/vnd.microsoft.icon"


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
        assert b"Are you sure?" in rv.data
    with request_ctx(
            "/settings/email_template",
            method="POST",
            data={
                "name": "TEST APP",
                "homepage_url": "http://test.at.test",
                "description": "TEST APPLICATION 123",
                "email_template": "enable {MESSAGE} {INCLUDED_URL}",
                "save": "Save"
            }) as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        org = Organisation.get(id=org.id)
        assert org.email_template == "enable {MESSAGE} {INCLUDED_URL}"
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
    UserOrg.create(user=user, org=org, affiliations=Affiliation.EMP)
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
            }) as ctx, patch("orcid_hub.views.send_user_invitation.queue") as queue_send_user_invitation:
        login_user(admin, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"test123@test.test.net" in rv.data
        queue_send_user_invitation.assert_called_once()
    with patch("orcid_hub.orcid_client.MemberAPI") as m, patch(
        "orcid_hub.orcid_client.SourceClientId"), request_ctx(
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
            "city": "test"}) as ctx:
        login_user(admin, remember=True)
        OrcidToken.create(access_token="ACCESS123", user=user, org=org, scope="/read-limited,/activities/update",
                          expires_in='121')
        api_mock = m.return_value
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"test123@test.test.net" in rv.data
        api_mock.create_or_update_affiliation.assert_called_once()


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
                "email_template": "TEST TEMPLATE TO SAVE {MESSAGE} {INCLUDED_URL}",
                "save": "Save",
            }) as ctx:
        login_user(user)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        org.reload()
        assert org.email_template_enabled
        assert "TEST TEMPLATE TO SAVE {MESSAGE} {INCLUDED_URL}" in org.email_template

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
                            b'[{"invitees": [{"identifier":"00001", "email": "marco.232323newwjwewkppp@mailinator.com",'
                            b'"first-name": "Alice", "last-name": "Contributor 1", "ORCID-iD": null, "put-code":null}],'
                            b'"title": { "title": { "value": "1ral"}},"short-description": "Mi","type": "CONTRACT",'
                            b'"contributors": {"contributor": [{"contributor-attributes": {"contributor-role": '
                            b'"co_lead"},"credit-name": {"value": "firentini"}}]}'
                            b', "external-ids": {"external-id": [{"external-id-value": '
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


@patch("pykwalify.core.Core.validate", side_effect=validate)
@patch("pykwalify.core.Core.__init__", side_effect=core_mock)
def test_load_researcher_work(patch, patch2, request_ctx):
    """Test preload work data."""
    user = User.get(email="admin@test1.edu")
    user.roles = Role.ADMIN
    user.save()
    with request_ctx(
            "/load/researcher/work",
            method="POST",
            data={
                "file_": (
                        BytesIO(
                            b'[{"invitees": [{"identifier":"00001", "email": "marco.232323newwjwewkppp@mailinator.com",'
                            b'"first-name": "Alice", "last-name": "Contributor 1", "ORCID-iD": null, "put-code":null}],'
                            b'"title": { "title": { "value": "1ral"}}, "citation": {"citation-type": '
                            b'"FORMATTED_UNSPECIFIED", "citation-value": "This is citation value"}, "type": "BOOK_CHR",'
                            b'"contributors": {"contributor": [{"contributor-attributes": {"contributor-role": '
                            b'"AUTHOR", "contributor-sequence" : "1"},"credit-name": {"value": "firentini"}}]}'
                            b', "external-ids": {"external-id": [{"external-id-value": '
                            b'"GNS170661","external-id-type": "grant_number"}]}}]'),
                        "logo.json",),
                "email": user.email
            }) as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302
        # Work file successfully loaded.
        assert "task_id" in rv.location
        assert "work" in rv.location


@patch("pykwalify.core.Core.validate", side_effect=validate)
@patch("pykwalify.core.Core.__init__", side_effect=core_mock)
def test_load_researcher_peer_review(patch, patch2, request_ctx):
    """Test preload peer review data."""
    user = User.get(email="admin@test1.edu")
    user.roles = Role.ADMIN
    user.save()
    with request_ctx(
            "/load/researcher/peer_review",
            method="POST",
            data={
                "file_": (
                        BytesIO(
                            b'[{"invitees": [{"identifier": "00001", "email": "contriuto7384P@mailinator.com", '
                            b'"first-name": "Alice", "last-name": "Contributor 1", "ORCID-iD": null, "put-code": null}]'
                            b', "reviewer-role": "REVIEWER", "review-identifiers": { "external-id": [{ '
                            b'"external-id-type": "source-work-id", "external-id-value": "1212221", "external-id-url": '
                            b'{"value": "https://localsystem.org/1234"}, "external-id-relationship": "SELF"}]}, '
                            b'"review-type": "REVIEW", "review-group-id": "issn:90122", "subject-container-name": { '
                            b'"value": "Journal title"}, "subject-type": "JOURNAL_ARTICLE", "subject-name": { '
                            b'"title": {"value": "Name of the paper reviewed"}},"subject-url": { '
                            b'"value": "https://subject-alt-url.com"}, "convening-organization": { "name": '
                            b'"The University of Auckland", "address": { "city": "Auckland", "region": "Auckland",'
                            b' "country": "NZ" } }}]'),
                        "logo.json",),
                "email": user.email
            }) as ctx:
        login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302
        # peer-review file successfully loaded.
        assert "task_id" in rv.location
        assert "peer" in rv.location


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


def test_edit_record(request_ctx):
    """Test create a new or edit an existing profile section record."""
    admin = User.get(email="admin@test0.edu")
    user = User.get(email="researcher100@test0.edu")
    admin.organisation.orcid_client_id = "ABC123"
    admin.organisation.save()
    if not user.orcid:
        user.orcid = "XXXX-XXXX-XXXX-0001"
        user.save()
    fake_response = make_response
    fake_response.status = 201
    fake_response.headers = {'Location': '12344/xyz/12399'}
    OrcidToken.create(user=user, org=user.organisation, access_token="ABC123", scope="/read-limited,/activities/update")
    with patch.object(
            orcid_client.MemberAPIV20Api,
            "view_employment",
            MagicMock(return_value=make_fake_response('{"test": "TEST1234567890"}'))
    ) as view_employment, request_ctx(f"/section/{user.id}/EMP/1212/edit") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_employment.assert_called_once_with("XXXX-XXXX-XXXX-0001", 1212)
    with patch.object(
            orcid_client.MemberAPIV20Api,
            "view_education",
            MagicMock(return_value=make_fake_response('{"test": "TEST1234567890"}'))
    ) as view_education, request_ctx(f"/section/{user.id}/EDU/1234/edit") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_education.assert_called_once_with("XXXX-XXXX-XXXX-0001", 1234)
    with patch.object(
            orcid_client.MemberAPIV20Api, "create_education",
            MagicMock(return_value=fake_response)), request_ctx(
                f"/section/{user.id}/EDU/new",
                method="POST",
                data={
                    "city": "Auckland",
                    "country": "NZ",
                    "org_name": "TEST",
                }) as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == f"/section/{user.id}/EDU/list"
        affiliation_record = UserOrgAffiliation.get(user=user)
        # checking if the UserOrgAffiliation record is updated with put_code supplied from fake response
        assert 12399 == affiliation_record.put_code


def test_delete_employment(request_ctx, app):
    """Test delete an employment record."""
    admin = User.get(email="admin@test0.edu")
    user = User.get(email="researcher100@test0.edu")

    with request_ctx(f"/section/{user.id}/EMP/1212/delete", method="POST") as ctx:
        login_user(user)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location.startswith("/?next=")

    with request_ctx(f"/section/99999999/EMP/1212/delete", method="POST") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == "/admin/viewmembers/"

    with request_ctx(f"/section/{user.id}/EMP/1212/delete", method="POST") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == f"/section/{user.id}/EMP/list"

    admin.organisation.orcid_client_id = "ABC123"
    admin.organisation.save()

    with request_ctx(f"/section/{user.id}/EMP/1212/delete", method="POST") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == f"/section/{user.id}/EMP/list"

    if not user.orcid:
        user.orcid = "XXXX-XXXX-XXXX-0001"
        user.save()

    token = OrcidToken.create(
        user=user, org=user.organisation, access_token="ABC123", scope="/read-limited")

    with request_ctx(f"/section/{user.id}/EMP/1212/delete", method="POST") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == f"/section/{user.id}/EMP/list"

    token.scope = "/read-limited,/activities/update"
    token.save()

    with patch.object(
            orcid_client.MemberAPIV20Api,
            "delete_employment",
            MagicMock(
                return_value='{"test": "TEST1234567890"}')) as delete_employment, request_ctx(
                    f"/section/{user.id}/EMP/12345/delete", method="POST") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        delete_employment.assert_called_once_with("XXXX-XXXX-XXXX-0001", 12345)

    with patch.object(
            orcid_client.MemberAPIV20Api,
            "delete_education",
            MagicMock(return_value='{"test": "TEST1234567890"}')) as delete_education, request_ctx(
                f"/section/{user.id}/EDU/54321/delete", method="POST") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        delete_education.assert_called_once_with("XXXX-XXXX-XXXX-0001", 54321)


def test_viewmembers(request_ctx):
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

    with request_ctx("/admin/viewmembers/?flt1_0=2018-05-01+to+2018-05-31&flt2_1=2018-05-01+to+2018-05-31") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"researcher100@test0.edu" not in resp.data

    with request_ctx(f"/admin/viewmembers/edit/?id={non_admin.id}") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert non_admin.email.encode() in resp.data
        assert non_admin.name.encode() in resp.data

    with request_ctx(f"/admin/viewmembers/edit/?id=9999999999") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 404

    user2 = User.get(email="researcher100@test1.edu")
    with request_ctx(f"/admin/viewmembers/edit/?id={user2.id}") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 403


def test_viewmembers_delete(request_ctx):
    """Test affilated researcher deletion via the view."""
    admin0 = User.get(email="admin@test0.edu")
    admin1 = User.get(email="admin@test1.edu")
    researcher0 = User.get(email="researcher100@test0.edu")
    researcher1 = User.get(email="researcher100@test1.edu")

    with request_ctx(
            "/admin/viewmembers/delete/",
            method="POST",
            data={
                "id": str(researcher1.id),
                "url": "/admin/viewmembers/",
            }) as ctx:  # noqa: F405
        login_user(admin0)
        resp = ctx.app.full_dispatch_request()
    assert resp.status_code == 403

    with request_ctx(
            "/admin/viewmembers/delete/",
            method="POST",
            data={
                "id": str(researcher0.id),
                "url": "/admin/viewmembers/",
            }) as ctx, patch(
                "orcid_hub.views.AppModelView.on_model_delete",
                create=True,
                side_effect=Exception("FAILURED")), patch(
                    "orcid_hub.views.AppModelView.handle_view_exception",
                    create=True,
                    return_value=False):  # noqa: F405
        login_user(admin0)
        resp = ctx.app.full_dispatch_request()
    assert resp.status_code == 302
    assert resp.location == "/admin/viewmembers/"
    assert User.select().where(User.id == researcher0.id).count() == 1

    with request_ctx(
            "/admin/viewmembers/delete/",
            method="POST",
            data={
                "id": str(researcher0.id),
                "url": "/admin/viewmembers/",
            }) as ctx:  # noqa: F405
        login_user(admin0)
        resp = ctx.app.full_dispatch_request()
    assert resp.status_code == 302
    with pytest.raises(User.DoesNotExist):
        User.get(id=researcher0.id)

    UserOrg.create(org=admin0.organisation, user=researcher1)
    OrcidToken.create(org=admin0.organisation, user=researcher1, access_token="ABC123")
    with request_ctx(
            "/admin/viewmembers/delete/",
            method="POST",
            data={
                "id": str(researcher1.id),
                "url": "/admin/viewmembers/",
            }) as ctx, patch("orcid_hub.views.requests.post") as mockpost:  # noqa: F405
        org = researcher1.organisation
        mockpost.return_value = MagicMock(status_code=400)
        login_user(admin1)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert User.select().where(User.id == researcher1.id).count() == 1
        assert UserOrg.select().where(UserOrg.user == researcher1).count() == 2
        assert OrcidToken.select().where(OrcidToken.org == org, OrcidToken.user == researcher1).count() == 1

        mockpost.side_effect = Exception("FAILURE")
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert User.select().where(User.id == researcher1.id).count() == 1
        assert UserOrg.select().where(UserOrg.user == researcher1).count() == 2
        assert OrcidToken.select().where(OrcidToken.org == org, OrcidToken.user == researcher1).count() == 1

        mockpost.reset_mock(side_effect=True)
        mockpost.return_value = MagicMock(status_code=200)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert User.select().where(User.id == researcher1.id).count() == 1
        assert UserOrg.select().where(UserOrg.user == researcher1).count() == 1
        args, kwargs = mockpost.call_args
        assert args[0] == ctx.app.config["ORCID_BASE_URL"] + "oauth/revoke"
        data = kwargs["data"]
        assert data["client_id"] == "ABC123"
        assert data["client_secret"] == "SECRET-12345"
        assert data["token"].startswith("TOKEN-1")
        assert OrcidToken.select().where(OrcidToken.org == org, OrcidToken.user == researcher1).count() == 0


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
        disambiguation_source="Test")

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

    task3 = Task.create(
        id=3,
        org=org,
        completed_at="12/12/12",
        filename="xyz.txt",
        created_by=user,
        updated_by=user,
        task_type=3)

    PeerReviewRecord.create(
        id=1,
        task=task3,
        review_group_id=1212,
        is_active=True,
        visibility="Test_visibity")

    work_task = Task.create(
        id=4,
        org=org,
        completed_at="12/12/12",
        filename="xyz.txt",
        created_by=user,
        updated_by=user,
        task_type=2)

    WorkRecord.create(
        id=1,
        task=work_task,
        title=1212,
        is_active=True,
        citation_type="Test_citation_type",
        citation_value="Test_visibity")

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
    with request_ctx("/reset_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/peer_review_record_reset_for_batch')])
        request.form = ImmutableMultiDict([('task_id', task3.id)])
        rv = ctxx.app.full_dispatch_request()
        t2 = Task.get(id=3)
        pr = PeerReviewRecord.get(id=1)
        assert "The record was reset" in pr.status
        assert t2.completed_at is None
        assert rv.status_code == 302
        assert rv.location.startswith("http://localhost/peer_review_record_reset_for_batch")
    with request_ctx("/reset_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/work_record_reset_for_batch')])
        request.form = ImmutableMultiDict([('task_id', work_task.id)])
        rv = ctxx.app.full_dispatch_request()
        t = Task.get(id=4)
        pr = WorkRecord.get(id=1)
        assert "The record was reset" in pr.status
        assert t.completed_at is None
        assert rv.status_code == 302
        assert rv.location.startswith("http://localhost/work_record_reset_for_batch")


def test_issue_470198698(request_ctx):
    """Test regression https://sentry.io/royal-society-of-new-zealand/nz-orcid-hub/issues/470198698/."""
    from bs4 import BeautifulSoup

    admin = User.get(email="admin@test0.edu")
    org = admin.organisation

    task = Task.create(org=org, filename="TEST000.csv", user=admin)
    AffiliationRecord.insert_many(
        dict(
            task=task,
            orcid=f"XXXX-XXXX-XXXX-{i:04d}" if i % 2 else None,
            first_name=f"FN #{i}",
            last_name=f"LF #{i}",
            email=f"test{i}") for i in range(10)).execute()

    with request_ctx(f"/admin/affiliationrecord/?task_id={task.id}") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        soup = BeautifulSoup(resp.data, "html.parser")

    orcid_col_idx = next(i for i, h in enumerate(soup.thead.find_all("th"))
                         if "col-orcid" in h["class"]) - 2

    with request_ctx(f"/admin/affiliationrecord/?sort={orcid_col_idx}&task_id={task.id}") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
    soup = BeautifulSoup(resp.data, "html.parser")
    orcid_column = soup.find(class_="table-responsive").find_all(class_="col-orcid")
    assert orcid_column[-1].text.strip() == "XXXX-XXXX-XXXX-0009"

    with request_ctx("/admin/affiliationrecord/") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
    assert resp.status_code == 302

    with request_ctx(f"/admin/affiliationrecord/?task_id=99999999") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
    assert resp.status_code == 404
