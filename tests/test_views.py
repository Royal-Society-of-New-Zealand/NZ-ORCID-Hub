# -*- coding: utf-8 -*-
"""Tests for core functions."""

import datetime
import json
import logging
import re
import sys
import time
from itertools import product
from unittest.mock import MagicMock, patch
from io import BytesIO
from urllib.parse import urlparse

import pytest
from flask import request, make_response
from flask_login import login_user
from peewee import SqliteDatabase
from playhouse.test_utils import test_database
from werkzeug.datastructures import ImmutableMultiDict

from orcid_hub import app, orcid_client, rq, views
from orcid_hub.config import ORCID_BASE_URL
from orcid_hub.forms import FileUploadForm
from orcid_hub.models import (Affiliation, AffiliationRecord, Client, File, FundingRecord,
                              GroupIdRecord, OrcidToken, Organisation, OrgInfo, OrgInvitation, PartialDate,
                              Role, Task, Token, Url, User, UserOrgAffiliation, UserInvitation,
                              UserOrg, PeerReviewRecord, WorkRecord)

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


def test_superuser_view_access(client):
    """Test if SUPERUSER can access Flask-Admin"."""
    resp = client.get("/admin/schedude/")
    assert resp.status_code == 403
    assert b"403" in resp.data

    resp = client.get("/admin/user/")
    assert resp.status_code == 302
    assert "next=" in resp.location and "admin" in resp.location

    users = User.select().where(User.email << ["admin@test0.edu", "researcher100@test0.edu"])[:]
    for u in users:
        client.login(u)
        resp = client.get("/admin/user/")
        assert resp.status_code == 302
        assert "next=" in resp.location and "admin" in resp.location

        resp = client.get("/admin/organisation/")
        assert resp.status_code == 302
        assert "next=" in resp.location and "admin" in resp.location

        resp = client.get("/admin/orcidtoken/")
        assert resp.status_code == 302
        assert "next=" in resp.location and "admin" in resp.location

        resp = client.get("/admin/orginfo/")
        assert resp.status_code == 302
        assert "next=" in resp.location and "admin" in resp.location

        resp = client.get("/admin/userorg/")
        assert resp.status_code == 302
        assert "next=" in resp.location and "admin" in resp.location

        resp = client.get("/admin/schedude/")
        assert resp.status_code == 403
        assert b"403" in resp.data

        client.logout()

    client.login_root()

    resp = client.get("/admin/user/")
    assert resp.status_code == 200
    assert b"User" in resp.data

    resp = client.get("/admin/user/?search=TEST+ORG+%23+1")
    assert resp.status_code == 200
    assert b"root@test0.edu" in resp.data

    resp = client.get("/admin/organisation/")
    assert resp.status_code == 200

    org = Organisation.select().limit(1).first()
    resp = client.get(f"/admin/organisation/edit/?id={org.id}")
    assert resp.status_code == 200

    # Change the technical contact:
    admin = org.tech_contact
    new_admin = User.select().where(User.id != org.tech_contact_id, User.email ** "admin%").first()
    data = {k: v for k, v in org.to_dict(recurse=False).items() if not isinstance(v, dict) and 'at' not in k}
    data["tech_contact"] = new_admin.id
    resp = client.post(f"/admin/organisation/edit/?id={org.id}", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert admin.email.encode() not in resp.data
    assert Organisation.get(org.id).tech_contact != admin

    # Change the technical contact to a non-admin:
    user = User.get(email="researcher100@test0.edu")
    data["tech_contact"] = user.id
    resp = client.post(f"/admin/organisation/edit/?id={org.id}", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert user.email.encode() in resp.data
    assert Organisation.get(org.id).tech_contact == user
    assert User.get(user.id).roles & Role.TECHNICAL

    resp = client.get("/admin/organisation/edit/?id=999999")
    assert resp.status_code == 404
    assert b"404" in resp.data
    assert b"The record with given ID: 999999 doesn't exist or it was deleted." in resp.data

    resp = client.get("/admin/orcidtoken/")
    assert resp.status_code == 200

    resp = client.get("/admin/orginfo/")
    assert resp.status_code == 200

    resp = client.get("/admin/userorg/")
    assert resp.status_code == 200

    for u in users:
        resp = client.get(f"/admin/user/edit/?id={u.id}")
        assert resp.status_code == 200
        assert u.name.encode() in resp.data
        resp = client.post(
            f"/admin/user/edit/?id={u.id}&url=%2Fadmin%2Fuser%2F",
            data=dict(
                name=u.name + "_NEW",
                first_name=u.first_name,
                last_name=u.last_name,
                email="NEW_" + u.email,
                eppn='',
                orcid="0000-0000-XXXX-XXXX",
                confirmed="y",
                webhook_enabled="y",
            ))
        user = User.get(u.id)
        assert user.orcid == "0000-0000-XXXX-XXXX"
        assert user.email == "NEW_" + u.email
        assert user.name == u.name + "_NEW"

    resp = client.get("/admin/schedude/")
    assert resp.status_code == 200
    assert b"interval" in resp.data

    jobs = rq.get_scheduler().get_jobs()
    resp = client.get(f"/admin/schedude/details/?id={jobs[0].id}")
    assert resp.status_code == 200
    assert b"interval" in resp.data


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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302

    with request_ctx("/rq") as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 401
        assert b"401" in resp.data

    with request_ctx("/rq?next=http://orcidhub.org.nz/next") as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == "http://orcidhub.org.nz/next"

    with request_ctx("/pyinfo") as ctx:
        login_user(test_superuser, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert bytes(sys.version, encoding="utf-8") in resp.data

    with request_ctx("/pyinfo") as ctx:
        login_user(test_user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302

    with request_ctx("/rq") as ctx:
        login_user(test_superuser, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"Queues" in resp.data

    with request_ctx("/rq") as ctx:
        login_user(test_user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 403
        assert b"403" in resp.data

    with request_ctx("/rq?next=http://orcidhub.org.nz/next") as ctx:
        login_user(test_user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == "http://orcidhub.org.nz/next"


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
        resp = client.get("/status")
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data["status"] == "Connection successful."
        assert data["db-timestamp"] == "2042-01-01T00:00:00"

    with patch("orcid_hub.views.db") as db:  # , request_ctx("/status") as ctx:
        db.execute_sql.side_effect = Exception("FAILURE")
        resp = client.get("/status")
        data = json.loads(resp.data)
        assert resp.status_code == 503
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
        resp = ctx.app.full_dispatch_request()
        c = Client.get(name="TEST APP")
        assert c.homepage_url == "http://test.at.test"
        assert c.description == "TEST APPLICATION 123"
        assert c.user == user
        assert c.org == org
        assert c.client_id
        assert c.client_secret
        assert resp.status_code == 302

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
    elif "dict" in kwargs:
        mm.to_dict.return_value = kwargs["dict"]
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


def test_load_org(client):
    """Test load organisation."""
    resp = client.get("/load/org", follow_redirects=True)
    assert b"Please log in to access this page." in resp.data

    client.login_root()
    with pytest.raises(AssertionError):
        resp = client.post(
            "/load/org",
            follow_redirects=True,
            data={
                "save":
                "Upload",
                "file_": (
                    BytesIO(b"Name\nAgResearch Ltd\nAqualinc Research Ltd\n"),
                    "incorrect-raw-org-data.csv",
                ),
            })

    resp = client.post(
        "/load/org",
        follow_redirects=True,
        data={
            "save":
            "Upload",
            "file_": (
                BytesIO(b"""Name,Disambiguated Id,Disambiguation Source
AgResearch Ltd,3713,RINGGOLD
Aqualinc Research Ltd,9429035717133,NZBN
Ara Institute of Canterbury,6006,Education Organisation Number
Auckland District Health Board,1387,RINGGOLD
Auckland University of Technology,1410,RINGGOLD
Bay of Plenty District Health Board,7854,RINGGOLD
Capital and Coast District Health Board,8458,RINGGOLD
Cawthron Institute,5732,RINGGOLD
CRL Energy Ltd,9429038654381,NZBN
Health Research Council,http://dx.doi.org/10.13039/501100001505,FUNDREF
Hutt Valley District Health Board,161292,RINGGOLD
Institute of Environmental Science and Research,8480,RINGGOLD
Institute of Geological & Nuclear Sciences Ltd,5180,RINGGOLD
"""),
                "raw-org-data.csv",
            ),
        })
    assert resp.status_code == 200
    assert OrgInfo.select().count() == 13
    assert b"CRL Energy Ltd" in resp.data

    resp = client.post(
        "/load/org",
        follow_redirects=True,
        data={
            "save":
            "Upload",
            "file_": (
                BytesIO(
                    b"Name,Disambiguated Id,Disambiguation Source\n"
                    b"CRL Energy Ltd,8888,NZBN\nLandcare Research,2243,RINGGOLD"
                ),
                "raw-org-data.csv",
            ),
        })
    assert OrgInfo.select().count() == 14, "A new entry should be added."
    assert b"8888" not in resp.data, "Etry should be updated."
    assert b"Landcare Research" in resp.data

    resp = client.post(
        "/admin/orginfo/action/",
        follow_redirects=True,
        data=dict(
            url="/admin/orginfo/",
            action="delete",
            rowid=OrgInfo.select().limit(1).first().id,
        ))
    assert OrgInfo.select().count() == 13

    resp = client.post(
        "/admin/orginfo/action/",
        follow_redirects=True,
        data=dict(
            url="/admin/orginfo/",
            action="delete",
            rowid=[r.id for r in OrgInfo.select()],
        ))
    assert OrgInfo.select().count() == 0

    resp = client.post(
        "/load/org",
        follow_redirects=True,
        data={
            "save":
            "Upload",
            "file_": (
                BytesIO(
                    b"Name,Disambiguated Id,Disambiguation Source,Email\n"
                    b"ORG #1,,,test@org1.net\n"
                    b"ORG #2,,,test@org2.net\n"
                    b"ORG #3,,,test@org3.net\n"
                ),
                "raw-org-data.csv",
            ),
        })
    assert OrgInfo.select().count() == 3

    with patch("orcid_hub.views.utils") as utils:
        client.post(
            "/admin/orginfo/action/",
            follow_redirects=True,
            data=dict(
                url="/admin/orginfo/",
                action="invite",
                rowid=[r.id for r in OrgInfo.select()],
            ))
        utils.send_email.assert_called()
        assert OrgInvitation.select().count() == 3


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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
    with request_ctx(f"/hub/api/v0.1/users/{user.id}/orgs/{org.id}") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
    with request_ctx("/hub/api/v0.1/users/1234/orgs/") as ctx:
        # failure test case, user not found
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 404


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
        resp = views.shorturl(url)
        assert "http://" in resp


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
        resp = ctxx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location.startswith("http://localhost/affiliation_record_activate_for_batch")
    with request_ctx("/activate_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/funding_record_activate_for_batch')])
        request.form = ImmutableMultiDict([('task_id', task2.id)])
        resp = ctxx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location.startswith("http://localhost/funding_record_activate_for_batch")


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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
    with request_ctx("/logo/token_123") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location.endswith("images/banner-small.png")


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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"Are you sure?" in resp.data
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"


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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert org.name.encode() in resp.data
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert b"test123@test.test.net" in resp.data
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert b"test123@test.test.net" in resp.data
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"&lt;!DOCTYPE html&gt;" in resp.data
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
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


def test_affiliation_tasks(client):
    """Test affilaffiliation task upload."""
    org = Organisation.get(name="TEST0")
    user = User.get(email="admin@test0.edu")

    client.login(user)
    resp = client.post(
        "/load/researcher",
        data={
            "save":
            "Upload",
            "file_": (
                BytesIO(b"""First Name,Last Name,Email
Roshan,Pawar,researcher.010@mailinator.com
"""),
                "affiliations.csv",
            ),
        })
    assert resp.status_code == 200
    assert b"Failed to load affiliation record file: Wrong number of fields." in resp.data

    resp = client.post(
        "/load/researcher",
        data={
            "save":
            "Upload",
            "file_": (
                BytesIO(b"""First Name,Last Name,Email,Affiliation Type
Roshan,Pawar,researcher.010@mailinator.com,Student
Roshan,Pawar,researcher.010@mailinator.com,Staff
Rad,Cirskis,researcher.990@mailinator.com,Staff
Rad,Cirskis,researcher.990@mailinator.com,Student
"""),
                "affiliations.csv",
            ),
        })
    assert resp.status_code == 302
    task_id = int(re.search(r"\/admin\/affiliationrecord/\?task_id=(\d+)", resp.location)[1])
    assert task_id
    task = Task.get(task_id)
    assert task.org == org
    records = list(task.affiliation_records)
    assert len(records) == 4
    assert AffiliationRecord.select().where(AffiliationRecord.task_id == task_id).count() == 4

    url = resp.location
    session_cookie, _ = resp.headers["Set-Cookie"].split(';', 1)
    _, session = session_cookie.split('=', 1)

    # client.set_cookie("", "session", session)
    resp = client.get(url)
    assert b"researcher.010@mailinator.com" in resp.data

    # List all tasks with a filter (select 'affiliation' task):
    resp = client.get("/admin/task/?flt1_1=0")
    assert b"affiliations.csv" in resp.data

    # Activate a single record:
    id = records[0].id
    resp = client.post(
        "/admin/affiliationrecord/action/",
        follow_redirects=True,
        data={
            "url": f"/admin/affiliationrecord/?task_id={task_id}",
            "action": "activate",
            "rowid": id,
        })
    assert AffiliationRecord.select().where(AffiliationRecord.task_id == task_id,
                                            AffiliationRecord.is_active).count() == 1

    # Activate all:
    resp = client.post("/activate_all", follow_redirects=True, data=dict(task_id=task_id))
    assert AffiliationRecord.select().where(AffiliationRecord.task_id == task_id,
                                            AffiliationRecord.is_active).count() == 4

    # Reste a single record
    AffiliationRecord.update(processed_at=datetime.datetime(2018, 1, 1)).execute()
    resp = client.post(
        "/admin/affiliationrecord/action/",
        follow_redirects=True,
        data={
            "url": f"/admin/affiliationrecord/?task_id={task_id}",
            "action": "reset",
            "rowid": id,
        })
    assert AffiliationRecord.select().where(AffiliationRecord.task_id == task_id,
                                            AffiliationRecord.processed_at.is_null()).count() == 1

    # Reset all:
    resp = client.post("/reset_all", follow_redirects=True, data=dict(task_id=task_id))
    assert AffiliationRecord.select().where(AffiliationRecord.task_id == task_id,
                                            AffiliationRecord.processed_at.is_null()).count() == 4

    # Exporting:
    for export_type in ["csv", "xls", "tsv", "yaml", "json", "xlsx", "ods", "html"]:
        resp = client.get(f"/admin/affiliationrecord/export/{export_type}/?task_id={task_id}")
        ct = resp.headers["Content-Type"]
        assert (export_type in ct or (export_type == "xls" and "application/vnd.ms-excel" == ct)
                or (export_type == "tsv" and "text/tab-separated-values" in ct)
                or (export_type == "yaml" and "application/octet-stream" in ct)
                or (export_type == "xlsx"
                    and "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" == ct)
                or
                (export_type == "ods" and "application/vnd.oasis.opendocument.spreadsheet" == ct))
        assert re.match(f"attachment;filename=affiliations_20.*\\.{export_type}",
                        resp.headers["Content-Disposition"])
        if export_type not in ["xlsx", "ods"]:
            assert b"researcher.010@mailinator.com" in resp.data

    # Delete records:
    resp = client.post(
        "/admin/affiliationrecord/action/",
        follow_redirects=True,
        data={
            "url": f"/admin/affiliationrecord/?task_id={task_id}",
            "action": "delete",
            "rowid": id,
        })
    assert AffiliationRecord.select().where(AffiliationRecord.task_id == task_id).count() == 3

    # Delete more records:
    resp = client.post(
        "/admin/affiliationrecord/action/",
        follow_redirects=True,
        data={
            "url": f"/admin/affiliationrecord/?task_id={task_id}",
            "action": "delete",
            "rowid": [ar.id for ar in records[1:-1]],
        })
    assert AffiliationRecord.select().where(AffiliationRecord.task_id == task_id).count() == 1

    resp = client.post(
        "/admin/task/delete/", data=dict(id=task_id, url="/admin/task/"), follow_redirects=True)
    assert b"affiliations.csv" not in resp.data
    assert Task.select().count() == 0
    assert AffiliationRecord.select().where(AffiliationRecord.task_id == task_id).count() == 0


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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert b"test123@test.test.net" in resp.data
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert b"test123@test.test.net" in resp.data
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        # Funding file successfully loaded.
        assert "task_id" in resp.location
        assert "funding" in resp.location


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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        # Work file successfully loaded.
        assert "task_id" in resp.location
        assert "work" in resp.location


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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        # peer-review file successfully loaded.
        assert "task_id" in resp.location
        assert "peer" in resp.location


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
        resp = ctxx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert user.email.encode() in resp.data


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
            orcid_client.MemberAPIV20Api,
            "view_funding",
            MagicMock(return_value=make_fake_response('{"test":123}', dict={"external_ids": {"external_id": [
            {"external_id_type": "test", "external_id_value": "test", "external_id_url": {"value": "test"},
             "external_id_relationship": "SELF"}]}}))
    ) as view_funding, request_ctx(f"/section/{user.id}/FUN/1234/edit") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_funding.assert_called_once_with("XXXX-XXXX-XXXX-0001", 1234)
    with patch.object(
        orcid_client.MemberAPIV20Api,
        "view_peer_review",
        MagicMock(return_value=make_fake_response('{"test":123}', dict={"review_identifiers": {"external-id": [
            {"external-id-type": "test", "external-id-value": "test", "external-id-url": {"value": "test"},
             "external-id-relationship": "SELF"}]}}))
    ) as view_peer_review, request_ctx(f"/section/{user.id}/PRR/1234/edit") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_peer_review.assert_called_once_with("XXXX-XXXX-XXXX-0001", 1234)
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
    with patch.object(
            orcid_client.MemberAPIV20Api, "create_funding",
            MagicMock(return_value=fake_response)), request_ctx(
                f"/section/{user.id}/FUN/new",
                method="POST",
                data={
                    "city": "Auckland",
                    "country": "NZ",
                    "org_name": "TEST",
                    "funding_title": "TEST",
                    "funding_type": "AWARD",
                    "translated_title_language": "hi",
                    "total_funding_amount_currency": "NZD",
                    "grant_url": "https://test.com",
                    "grant_number": "TEST123",
                    "grant_relationship": "SELF"
                }) as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == f"/section/{user.id}/FUN/list"
    with patch.object(
            orcid_client.MemberAPIV20Api, "create_peer_review",
            MagicMock(return_value=fake_response)), request_ctx(
                f"/section/{user.id}/PRR/new",
                method="POST",
                data={
                    "city": "Auckland",
                    "country": "NZ",
                    "org_name": "TEST",
                    "reviewer_role": "REVIEWER",
                    "review_type": "REVIEW",
                    "review_completion_date": PartialDate.create("2003-07-14"),
                    "review_group_id": "Test",
                    "subject_external_identifier_relationship": "PART_OF",
                    "subject_type": "OTHER",
                    "subject_translated_title_language_code": "en",
                    "grant_type": "https://test.com",
                    "grant_url": "https://test.com",
                    "grant_number": "TEST123",
                    "grant_relationship": "SELF"
                }) as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == f"/section/{user.id}/PRR/list"


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
    with patch.object(
        orcid_client.MemberAPIV20Api,
        "delete_funding",
            MagicMock(return_value='{"test": "TEST1234567890"}')) as delete_funding, request_ctx(
                f"/section/{user.id}/FUN/54321/delete", method="POST") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        delete_funding.assert_called_once_with("XXXX-XXXX-XXXX-0001", 54321)
    with patch.object(
        orcid_client.MemberAPIV20Api,
        "delete_peer_review",
            MagicMock(return_value='{"test": "TEST1234567890"}')) as delete_peer_review, request_ctx(
                f"/section/{user.id}/PRR/54321/delete", method="POST") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        delete_peer_review.assert_called_once_with("XXXX-XXXX-XXXX-0001", 54321)


def test_viewmembers(client):
    """Test affilated researcher view."""
    resp = client.get("/admin/viewmembers")
    assert resp.status_code == 302

    non_admin = User.get(email="researcher100@test0.edu")
    client.login(non_admin)
    resp = client.get("/admin/viewmembers")
    assert resp.status_code == 302
    client.logout()

    admin = User.get(email="admin@test0.edu")
    client.login(admin)
    resp = client.get("/admin/viewmembers")
    assert resp.status_code == 200
    assert b"researcher100@test0.edu" in resp.data

    resp = client.get("/admin/viewmembers/?flt1_0=2018-05-01+to+2018-05-31&flt2_1=2018-05-01+to+2018-05-31")
    assert resp.status_code == 200
    assert b"researcher100@test0.edu" not in resp.data

    resp = client.get(f"/admin/viewmembers/edit/?id={non_admin.id}")
    assert resp.status_code == 200
    assert non_admin.email.encode() in resp.data
    assert non_admin.name.encode() in resp.data

    resp = client.post(
        f"/admin/viewmembers/edit/?id={non_admin.id}&url=%2Fadmin%2Fviewmembers%2F",
        data={
            "name": non_admin.name,
            "email": "NEW_EMAIL@test0.edu",
            "eppn": non_admin.eppn,
            "orcid": non_admin.orcid,
        },
        follow_redirects=True)
    assert b"NEW_EMAIL@test0.edu" in resp.data
    assert User.get(non_admin.id).email == "NEW_EMAIL@test0.edu"

    resp = client.get(f"/admin/viewmembers/edit/?id=9999999999")
    assert resp.status_code == 404

    user2 = User.get(email="researcher100@test1.edu")
    resp = client.get(f"/admin/viewmembers/edit/?id={user2.id}")
    assert resp.status_code == 403

    client.logout()
    client.login_root()
    resp = client.get("/admin/viewmembers")


@patch("orcid_hub.views.requests.post")
def test_viewmembers_delete(mockpost, client):
    """Test affilated researcher deletion via the view."""
    admin0 = User.get(email="admin@test0.edu")
    admin1 = User.get(email="admin@test1.edu")
    researcher0 = User.get(email="researcher100@test0.edu")
    researcher1 = User.get(email="researcher100@test1.edu")

    # admin0 cannot deleted researcher1:
    client.login(admin0)
    resp = client.post(
        "/admin/viewmembers/delete/",
        data={
            "id": str(researcher1.id),
            "url": "/admin/viewmembers/",
        })
    assert resp.status_code == 403

    with patch(
            "orcid_hub.views.AppModelView.on_model_delete",
            create=True,
            side_effect=Exception("FAILURED")), patch(
                "orcid_hub.views.AppModelView.handle_view_exception",
                create=True,
                return_value=False):  # noqa: F405
        resp = client.post(
            "/admin/viewmembers/delete/",
            data={
                "id": str(researcher0.id),
                "url": "/admin/viewmembers/",
            })
    assert resp.status_code == 302
    assert urlparse(resp.location).path == "/admin/viewmembers/"
    assert User.select().where(User.id == researcher0.id).count() == 1

    mockpost.return_value = MagicMock(status_code=200)
    resp = client.post(
        "/admin/viewmembers/delete/",
        method="POST",
        follow_redirects=True,
        data={
            "id": str(researcher0.id),
            "url": "/admin/viewmembers/",
        })
    assert resp.status_code == 200
    with pytest.raises(User.DoesNotExist):
        User.get(id=researcher0.id)

    client.logout()
    UserOrg.create(org=admin0.organisation, user=researcher1)
    OrcidToken.create(org=admin0.organisation, user=researcher1, access_token="ABC123")
    client.login(admin1)
    payload = {
        "id": str(researcher1.id),
        "url": "/admin/viewmembers/",
    }
    org = researcher1.organisation
    mockpost.return_value = MagicMock(status_code=400)

    resp = client.post("/admin/viewmembers/delete/", data=payload)
    assert resp.status_code == 302
    assert User.select().where(User.id == researcher1.id).count() == 1
    assert UserOrg.select().where(UserOrg.user == researcher1).count() == 2
    assert OrcidToken.select().where(OrcidToken.org == org,
                                     OrcidToken.user == researcher1).count() == 1

    mockpost.side_effect = Exception("FAILURE")
    resp = client.post("/admin/viewmembers/delete/", data=payload)
    assert resp.status_code == 302
    assert User.select().where(User.id == researcher1.id).count() == 1
    assert UserOrg.select().where(UserOrg.user == researcher1).count() == 2
    assert OrcidToken.select().where(OrcidToken.org == org,
                                     OrcidToken.user == researcher1).count() == 1

    mockpost.reset_mock(side_effect=True)
    mockpost.return_value = MagicMock(status_code=200)
    resp = client.post("/admin/viewmembers/delete/", data=payload)
    assert resp.status_code == 302
    assert User.select().where(User.id == researcher1.id).count() == 1
    assert UserOrg.select().where(UserOrg.user == researcher1).count() == 1
    args, kwargs = mockpost.call_args
    assert args[0] == client.application.config["ORCID_BASE_URL"] + "oauth/revoke"
    data = kwargs["data"]
    assert data["client_id"] == "ABC123"
    assert data["client_secret"] == "SECRET-12345"
    assert data["token"].startswith("TOKEN-1")
    assert OrcidToken.select().where(OrcidToken.org == org,
                                     OrcidToken.user == researcher1).count() == 0


def test_action_insert_update_group_id(client):
    """Test update or insert of group id."""
    admin = User.get(email="admin@test0.edu")
    org = admin.organisation
    org.orcid_client_id = "ABC123"
    org.save()

    gr = GroupIdRecord.create(
        name="xyz",
        group_id="issn:test",
        description="TEST",
        type="journal",
        organisation=org,
    )

    fake_response = make_response
    fake_response.status = 201
    fake_response.headers = {'Location': '12344/xyz/12399'}

    OrcidToken.create(org=org, access_token="ABC123", scope="/group-id-record/update")

    client.login(admin)

    with patch.object(
            orcid_client.MemberAPIV20Api,
            "create_group_id_record",
            MagicMock(return_value=fake_response)):

        resp = client.post(
            "/admin/groupidrecord/action/",
            data={
                "rowid": str(gr.id),
                "action": "Insert/Update Record",
                "url": "/admin/groupidrecord/"
            })
        assert resp.status_code == 302
        assert urlparse(resp.location).path == "/admin/groupidrecord/"
        group_id_record = GroupIdRecord.get(id=gr.id)
        # checking if the GroupID Record is updated with put_code supplied from fake response
        assert 12399 == group_id_record.put_code


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
        resp = ctxx.app.full_dispatch_request()
        t = Task.get(id=1)
        ar = AffiliationRecord.get(id=1)
        assert "The record was reset" in ar.status
        assert t.completed_at is None
        assert resp.status_code == 302
        assert resp.location.startswith("http://localhost/affiliation_record_reset_for_batch")
    with request_ctx("/reset_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/funding_record_reset_for_batch')])
        request.form = ImmutableMultiDict([('task_id', task2.id)])
        resp = ctxx.app.full_dispatch_request()
        t2 = Task.get(id=2)
        fr = FundingRecord.get(id=1)
        assert "The record was reset" in fr.status
        assert t2.completed_at is None
        assert resp.status_code == 302
        assert resp.location.startswith("http://localhost/funding_record_reset_for_batch")
    with request_ctx("/reset_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/peer_review_record_reset_for_batch')])
        request.form = ImmutableMultiDict([('task_id', task3.id)])
        resp = ctxx.app.full_dispatch_request()
        t2 = Task.get(id=3)
        pr = PeerReviewRecord.get(id=1)
        assert "The record was reset" in pr.status
        assert t2.completed_at is None
        assert resp.status_code == 302
        assert resp.location.startswith("http://localhost/peer_review_record_reset_for_batch")
    with request_ctx("/reset_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/work_record_reset_for_batch')])
        request.form = ImmutableMultiDict([('task_id', work_task.id)])
        resp = ctxx.app.full_dispatch_request()
        t = Task.get(id=4)
        pr = WorkRecord.get(id=1)
        assert "The record was reset" in pr.status
        assert t.completed_at is None
        assert resp.status_code == 302
        assert resp.location.startswith("http://localhost/work_record_reset_for_batch")


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
