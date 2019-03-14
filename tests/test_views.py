# -*- coding: utf-8 -*-
"""Tests for core functions."""

import datetime
import json
import logging
import os
import re
import sys
import time
from io import BytesIO
from itertools import product
from unittest.mock import MagicMock, Mock, patch
from urllib.parse import parse_qs, urlparse

import pytest
import yaml
from flask import make_response, request, session
from flask_login import login_user
from peewee import SqliteDatabase
from playhouse.test_utils import test_database
from werkzeug.datastructures import ImmutableMultiDict

from orcid_api.rest import ApiException
from orcid_hub import app, orcid_client, rq, utils, views
from orcid_hub.config import ORCID_BASE_URL
from orcid_hub.forms import FileUploadForm
from orcid_hub.models import (
    Affiliation, AffiliationRecord, Client, File, FundingRecord, GroupIdRecord, OrcidToken,
    Organisation, OrgInfo, OrgInvitation, PartialDate, PeerReviewRecord, ResearcherUrlRecord, Role,
    Task, TaskType, Token, Url, User, UserInvitation, UserOrg, UserOrgAffiliation, WorkRecord)

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

        resp = client.get("/admin/delegate/")
        assert resp.status_code == 302
        assert "next=" in resp.location and "admin" in resp.location

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

    resp = client.get("/admin/schedude/?search=TEST")
    assert resp.status_code == 200
    assert b"interval" in resp.data

    jobs = list(rq.get_scheduler().get_jobs())
    resp = client.get(f"/admin/schedude/details/?id={jobs[0].id}")
    assert resp.status_code == 200
    assert b"interval" in resp.data

    resp = client.get("/admin/schedude/details/?id=99999999")
    assert resp.status_code == 404
    assert b"404" in resp.data

    resp = client.get("/admin/delegate/")
    assert resp.status_code == 200

    resp = client.post(
        "/admin/delegate/new/", data=dict(hostname="TEST HOST NAME"), follow_redirects=True)
    assert resp.status_code == 200
    assert b"TEST HOST NAME" in resp.data


def test_pyinfo(client):
    """Test /pyinfo."""
    app.config["PYINFO_TEST_42"] = "Life, the Universe and Everything"
    client.login_root()
    resp = client.get("/pyinfo")
    assert b"PYINFO_TEST_42" in resp.data
    assert b"Life, the Universe and Everything" in resp.data
    with pytest.raises(Exception) as exinfo:
        resp = client.get("/pyinfo/expected an exception")
    assert str(exinfo.value) == "expected an exception"


def test_access(client):
    """Test access to differente resources."""
    org = client.data["org"]
    user = client.data["user"]
    tech_contact = client.data["tech_contact"]
    root = User.select().where(User.email ** "root%").first()
    admin = User.create(
        name="ADMIN USER",
        email="admin123456789@test.test.net",
        confirmed=True,
        roles=Role.ADMIN)
    UserOrg.create(user=admin, org=org, is_admin=True)

    resp = client.get("/pyinfo")
    assert resp.status_code == 302

    resp = client.get("/rq")
    assert resp.status_code == 401
    assert b"401" in resp.data

    resp = client.get("/rq?next=http://orcidhub.org.nz/next")
    assert resp.status_code == 302
    assert resp.location == "http://orcidhub.org.nz/next"

    resp = client.login(root, follow_redirects=True)
    resp = client.get("/pyinfo")
    assert resp.status_code == 200
    assert bytes(sys.version, encoding="utf-8") in resp.data
    client.logout()

    resp = client.login(user)
    resp = client.get("/pyinfo")
    assert resp.status_code == 302
    client.logout()

    resp = client.login(root, follow_redirects=True)
    resp = client.get("/rq")
    assert resp.status_code == 200
    assert b"Queues" in resp.data
    client.logout()

    resp = client.login(user)
    resp = client.get("/rq")
    assert resp.status_code == 403
    assert b"403" in resp.data

    resp = client.get("/rq?next=http://orcidhub.org.nz/next")
    assert resp.status_code == 302
    assert resp.location == "http://orcidhub.org.nz/next"
    client.logout()

    resp = client.login(admin, follow_redirects=True)
    resp = client.get("/settings/webhook")
    assert resp.status_code == 302

    resp = client.login(tech_contact, follow_redirects=True)
    resp = client.get("/settings/webhook")
    assert resp.status_code == 200


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
            MagicMock(return_value=Mock(data="""{"test": "TEST1234567890"}"""))
    ) as view_employments, request_ctx(f"/section/{user.id}/EMP/list") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_employments.assert_called_once_with("XXXX-XXXX-XXXX-0001", _preload_content=False)
    with patch.object(
            orcid_client.MemberAPIV20Api,
            "view_educations",
            MagicMock(return_value=Mock(data="""{"test": "TEST1234567890"}"""))
    ) as view_educations, request_ctx(f"/section/{user.id}/EDU/list") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_educations.assert_called_once_with("XXXX-XXXX-XXXX-0001", _preload_content=False)
    with patch.object(
            orcid_client.MemberAPIV20Api,
            "view_peer_reviews",
            MagicMock(return_value=make_fake_response('{"test": "TEST1234567890"}'))
    ) as view_peer_reviews, request_ctx(f"/section/{user.id}/PRR/list") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_peer_reviews.assert_called_once_with("XXXX-XXXX-XXXX-0001")
    with patch.object(
        orcid_client.MemberAPIV20Api,
        "view_works",
        MagicMock(return_value=make_fake_response('{"test": "TEST1234567890"}'))
    ) as view_works, request_ctx(f"/section/{user.id}/WOR/list") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_works.assert_called_once_with("XXXX-XXXX-XXXX-0001")
    with patch.object(
            orcid_client.MemberAPIV20Api,
            "view_fundings",
            MagicMock(return_value=make_fake_response('{"test": "TEST1234567890"}'))
    ) as view_fundings, request_ctx(f"/section/{user.id}/FUN/list") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_fundings.assert_called_once_with("XXXX-XXXX-XXXX-0001")


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


def test_application_registration(client):
    """Test application registration."""
    org = app.data["org"]
    user = User.create(
        email="test123456@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123-456-789-098",
        organisation_id=1,
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    org.update(tech_contact=user).execute()

    resp = client.login(user, follow_redirects=True)
    resp = client.post(
        "/settings/applications",
        follow_redirects=True,
        data={
            "homepage_url": "http://test.at.test",
            "description": "TEST APPLICATION 123",
            "register": "Register",
        })
    with pytest.raises(Client.DoesNotExist):
        Client.get(name="TEST APP")
    assert resp.status_code == 200

    resp = client.post(
        "/settings/applications",
        data={
            "name": "TEST APP",
            "homepage_url": "http://test.at.test",
            "description": "TEST APPLICATION 123",
            "register": "Register",
        })
    c = Client.get(name="TEST APP")
    assert c.homepage_url == "http://test.at.test"
    assert c.description == "TEST APPLICATION 123"
    assert c.user == user
    assert c.org == org
    assert c.client_id
    assert c.client_secret
    assert resp.status_code == 302

    resp = client.get(f"/settings/applications/{c.id}")
    assert resp.status_code == 302
    assert urlparse(resp.location).path == f"/settings/credentials/{c.id}"

    resp = client.get("/settings/credentials")
    assert resp.status_code == 200

    resp = client.get(f"/settings/credentials/{c.id}")
    assert resp.status_code == 200

    resp = client.get("/settings/credentials/99999999999999")
    assert resp.status_code == 302
    assert urlparse(resp.location).path == "/settings/applications"

    Token.create(client=c, token_type="TEST", access_token="TEST000")
    resp = client.post(
        f"/settings/credentials/{c.id}", data={
            "revoke": "Revoke",
            "name": c.name,
        })
    assert resp.status_code == 200
    assert Token.select().where(Token.client == c).count() == 0

    old_client = c
    resp = client.post(
        f"/settings/credentials/{c.id}", data={
            "reset": "Reset",
            "name": c.name,
        })
    c = Client.get(name="TEST APP")
    assert resp.status_code == 200
    assert c.client_id != old_client.client_id
    assert c.client_secret != old_client.client_secret

    old_client = c
    resp = client.post(
        f"/settings/credentials/{c.id}",
        follow_redirects=True,
        data={
            "update_app": "Update",
            "name": "NEW APP NAME",
            "homepage_url": "http://test.test0.edu",
            "description": "DESCRIPTION",
            "callback_urls": "http://test0.edu/callback",
        })
    c = Client.get(c.id)
    assert resp.status_code == 200
    assert c.name == "NEW APP NAME"

    old_client = c
    resp = client.post(
        f"/settings/credentials/{c.id}", data={
            "delete": "Delete",
            "name": "NEW APP NAME",
        })
    assert resp.status_code == 302
    assert urlparse(resp.location).path == "/settings/applications"
    assert not Client.select().where(Client.id == c.id).exists()


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

    with patch("orcid_hub.views.utils.send_email") as send_email:
        client.post(
            "/admin/orginfo/action/",
            follow_redirects=True,
            data=dict(
                url="/admin/orginfo/",
                action="invite",
                rowid=[r.id for r in OrgInfo.select()],
            ))
        send_email.assert_called()
        assert OrgInvitation.select().count() == 3
        oi = OrgInvitation.select().first()
        assert oi.sent_at == oi.created_at


def test_user_orgs_org(client):
    """Test add an organisation to the user."""
    org = client.data["org"]
    root = User.create(
        email="root1234567890@test.test.net",
        name="TEST USER",
        roles=Role.SUPERUSER,
        orcid="123-456-789-098",
        confirmed=True,
        organisation=org)
    user = User.create(
        email="user1234567890@test.test.net",
        name="TEST USER",
        roles=Role.SUPERUSER,
        orcid="123-456-789-098",
        confirmed=True,
        organisation=org)
    resp = client.login(root, follow_redirects=True)

    resp = client.post(
            f"/hub/api/v0.1/users/{user.id}/orgs/",
            data=json.dumps({
                "id": org.id,
                "name": org.name,
                "is_admin": True,
                "is_tech_contact": True
            }),
            content_type="application/json")
    assert resp.status_code == 201
    assert User.get(id=user.id).roles & Role.ADMIN
    organisation = Organisation.get(name="THE ORGANISATION")
    # User becomes the technical contact of the organisation.
    assert organisation.tech_contact == user

    resp = client.post(
            f"/hub/api/v0.1/users/{user.id}/orgs/",
            data=json.dumps({
                "id": org.id,
                "name": org.name,
                "is_admin": True,
                "is_tech_contact": True
            }),
            content_type="application/json")
    assert resp.status_code == 200
    assert UserOrg.select().where(
            UserOrg.user == user, UserOrg.org == org,
            UserOrg.is_admin).exists()

    # Delete user and organisation association
    resp = client.delete(f"/hub/api/v0.1/users/{user.id}/orgs/{org.id}", method="DELETE")
    assert resp.status_code == 204
    user = User.get(user.id)
    assert user.organisation_id is None
    assert not (user.roles & Role.ADMIN)
    assert not UserOrg.select().where(UserOrg.user == user, UserOrg.org == org).exists()


def test_user_orgs(client, mocker):
    """Test add an organisation to the user."""
    org = client.data["org"]
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.SUPERUSER,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    resp = client.login(user)

    resp = client.get(f"/hub/api/v0.1/users/{user.id}/orgs/")
    assert resp.status_code == 200

    resp = client.get(f"/hub/api/v0.1/users/{user.id}/orgs/{org.id}")
    assert resp.status_code == 200

    resp = client.get("/hub/api/v0.1/users/1234/orgs/")
    assert resp.status_code == 404
    assert "Not Found" in json.loads(resp.data)["error"]

    resp = client.get(f"/hub/api/v0.1/users/{user.id}/orgs/999999999")
    assert resp.status_code == 404
    assert "Not Found" in json.loads(resp.data)["error"]

    resp = client.get("/hub/api/v0.1/users/1234/orgs/")
    assert resp.status_code == 404


def test_api_credentials(client):
    """Test manage API credentials.."""
    org = Organisation.get(name="THE ORGANISATION")
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)
    c = Client.create(
        name="Test_client",
        user=user,
        org=org,
        client_id="requestd_client_id",
        client_secret="XYZ123",
        is_confidential="public",
        grant_type="client_credentials",
        response_type="xyz")

    client.login(user)
    resp = client.post(
        "/settings/applications",
        follow_redirects=True,
        data={
            "name": "TEST APP",
            "homepage_url": "http://test.at.test",
            "description": "TEST APPLICATION 123",
            "register": "Register",
        })
    assert b"You aready have registered application" in resp.data
    assert b"test123@test.test.net" in resp.data

    resp = client.post(f"settings/credentials/{c.id}", data={"name": "TEST APP", "delete": "Delete"})
    assert resp.status_code == 302
    assert "application" in resp.location
    assert not Client.select().where(Client.id == c.id).exists()


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
    org = request_ctx.data["org"]
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
    org = request_ctx.data["org"]
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
        task_type=TaskType.AFFILIATION)
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
    org = request_ctx.data["org"]
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
    org = request_ctx.data["org"]
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


def test_researcher_invitation(client, mocker):
    """Test full researcher invitation flow."""
    mocker.patch(
        "orcid_hub.views.send_user_invitation.queue",
        lambda *args, **kwargs: (views.send_user_invitation(*args, **kwargs) and Mock()))
    send_email = mocker.patch("orcid_hub.utils.send_email")
    admin = User.get(email="admin@test1.edu")
    # org = admin.organisation
    resp = client.login(admin)
    resp = client.post(
            "/invite/user",
            data={
                "name": "TEST APP",
                "is_employee": "false",
                "email_address": "test123abc@test.test.net",
                "resend": "enable",
                "is_student": "true",
                "first_name": "test",
                "last_name": "test",
                "city": "test"
            })
    assert resp.status_code == 200
    assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
    assert b"test123abc@test.test.net" in resp.data
    send_email.assert_called_once()
    _, kwargs = send_email.call_args
    invitation_url = urlparse(kwargs["invitation_url"]).path
    client.logout()
    client.cookie_jar.clear()

    # Attempt to login via ORCID with the invitation token
    resp = client.get(invitation_url)
    auth_url = re.search(r"window.location='([^']*)'", resp.data.decode()).group(1)
    qs = parse_qs(urlparse(auth_url).query)
    redirect_uri = qs["redirect_uri"][0]
    oauth_state = qs["state"][0]
    callback_url = redirect_uri + "&state=" + oauth_state
    assert session["oauth_state"] == oauth_state
    mocker.patch(
        "orcid_hub.authcontroller.OAuth2Session.fetch_token",
        return_value={
            "orcid": "0123-1234-5678-0123",
            "name": "TESTER TESTERON",
            "access_token": "xyz",
            "refresh_token": "xyz",
            "scope": "/activities/update",
            "expires_in": "12121"
        })
    resp = client.get(callback_url, follow_redirects=True)
    user = User.get(email="test123abc@test.test.net")
    assert user.orcid == "0123-1234-5678-0123"


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

    resp = client.login(user, follow_redirects=True)
    assert b"log in" not in resp.data
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
    resp = client.get("/admin/task/?flt1_1=4")
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
        # Missing ID:
        resp = client.get(f"/admin/affiliationrecord/export/{export_type}", follow_redirects=True)
        assert b"Cannot invoke the task view without task ID" in resp.data

        # Non-existing task:
        resp = client.get(f"/admin/affiliationrecord/export/{export_type}/?task_id=9999999")
        assert b"The task deesn't exist." in resp.data

        # Incorrect task ID:
        resp = client.get(
            f"/admin/affiliationrecord/export/{export_type}/?task_id=ERROR-9999999",
            follow_redirects=True)
        assert b"invalid" in resp.data

        resp = client.get(f"/admin/affiliationrecord/export/{export_type}/?task_id={task_id}")
        ct = resp.headers["Content-Type"]
        assert (export_type in ct or (export_type == "xls" and "application/vnd.ms-excel" == ct)
                or (export_type == "tsv" and "text/tab-separated-values" in ct)
                or (export_type == "yaml" and "application/octet-stream" in ct)
                or (export_type == "xlsx"
                    and "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" == ct)
                or (export_type == "ods" and "application/vnd.oasis.opendocument.spreadsheet" == ct))
        assert re.match(f"attachment;filename=affiliations_20.*\\.{export_type}",
                        resp.headers["Content-Disposition"])
        if export_type not in ["xlsx", "ods"]:
            assert b"researcher.010@mailinator.com" in resp.data

    # Retrieve a copy of the task and attempt to reupload it:
    for export_type in ["yaml", "json"]:
        task_count = Task.select().count()
        resp = client.get(f"/admin/affiliationrecord/export/{export_type}/?task_id={task_id}")
        if export_type == "json":
            data = json.loads(resp.data)
        else:
            data = yaml.load(resp.data)
        del(data["id"])

        def default(o):
            if isinstance(o, datetime.datetime):
                return o.isoformat(timespec="seconds")
            elif isinstance(o, datetime.date):
                return o.isoformat()

        import_type = "json" if export_type == "yaml" else "yaml"
        resp = client.post(
            "/load/researcher",
            data={
                "save":
                "Upload",
                "file_": (
                    BytesIO((json.dumps(data, default=default)
                             if import_type == "json" else utils.dump_yaml(data)).encode()),
                    f"affiliations_004456.{import_type}",
                ),
            })
        assert resp.status_code == 302
        assert Task.select().count() == task_count + 1
        assert Task.select().order_by(Task.id.desc()).first().records.count() == 4

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
    assert Task.select().count() == 2
    assert AffiliationRecord.select().where(AffiliationRecord.task_id == task_id).count() == 0


def test_invite_organisation(client, mocker):
    """Test invite an organisation to register."""
    html = mocker.patch(
        "emails.html", return_value=Mock(send=lambda *args, **kwargs: Mock(success=False)))
    org = Organisation.get(name="TEST0")
    user = User.create(
        email="test123_test_invite_organisation@test.test.net",
        name="TEST USER",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)

    client.login_root()
    resp = client.post(
            "/invite/organisation",
            data={
                "org_name": "THE ORGANISATION ABC1",
                "org_email": user.email,
                "tech_contact": "True",
                "via_orcid": "True",
                "first_name": "XYZ",
                "last_name": "XYZ",
                "city": "XYZ"
            })
    html.assert_called_once()
    _, kwargs = html.call_args
    assert "Technical Contact" in kwargs["html"]
    assert "Organisation Administrator" not in kwargs["html"]

    resp = client.post(
            "/invite/organisation",
            data={
                "org_name": "THE ORGANISATION ABC2",
                "org_email": user.email,
                "first_name": "xyz",
                "last_name": "xyz",
                "city": "xyz"
            })
    _, kwargs = html.call_args
    assert "Organisation Administrator" in kwargs["html"]
    assert "Technical Contact" not in kwargs["html"]

    send_email = mocker.patch("orcid_hub.utils.send_email")
    org = Organisation.create(name="ORG NAME", confirmed=True)
    resp = client.post(
        "/invite/organisation",
        data={
            "org_name": org.name,
            "org_email": user.email,
            "tech_contact": "True",
            "via_orcid": "True",
            "first_name": "xyz",
            "last_name": "xyz",
            "city": "xyz"
        })
    assert resp.status_code == 200
    assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
    assert user.email.encode() in resp.data
    send_email.assert_called_once()

    org.tech_contact = user
    org.save()

    resp = client.post(
        "/invite/organisation",
        data={
            "org_name": org.name,
            "org_email": "test1234@test0.edu",
            "tech_contact": "True",
            "via_orcid": "True",
            "first_name": "xyz",
            "last_name": "xyz",
            "city": "xyz"
        })
    assert resp.status_code == 200
    assert b"Warning" in resp.data

    send_email.reset_mock()
    resp = client.post(
            "/invite/organisation",
            method="POST",
            data={
                "org_name": "THE ORGANISATION",
                "org_email": user.email,
                "tech_contact": "True",
                "via_orcid": "True",
                "first_name": "xyz",
                "last_name": "xyz",
                "city": "xyz"
            })
    assert resp.status_code == 200
    assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
    assert user.email.encode() in resp.data
    send_email.assert_called_once()
    _, args = send_email.call_args
    invitation = args.get("invitation")
    invitation_url = urlparse(invitation.url).path
    assert invitation_url.endswith(invitation.token)
    client.logout()

    # Attempt to login via ORCID with the invitation token
    resp = client.get(invitation_url)
    auth_url = re.search(r"window.location='([^']*)'", resp.data.decode()).group(1)
    qs = parse_qs(urlparse(auth_url).query)
    redirect_uri = qs["redirect_uri"][0]
    oauth_state = qs["state"][0]
    callback_url = redirect_uri + "&state=" + oauth_state
    assert session["oauth_state"] == oauth_state
    mocker.patch(
        "orcid_hub.authcontroller.OAuth2Session.fetch_token",
        return_value={
            "orcid": "3210-4321-8765-3210",
            "name": "ADMIN ADMINISTRATOR",
            "access_token": "xyz",
            "refresh_token": "xyz",
            "scope": "/activities/update",
            "expires_in": "12121"
        })

    mocker.patch.object(
            orcid_client.MemberAPIV20Api,
            "view_emails",
            side_effect=Exception("ERROR"))
    resp = client.get(callback_url, follow_redirects=True)
    assert b"ERROR" in resp.data

    mocker.patch.object(
            orcid_client.MemberAPIV20Api,
            "view_emails",
            side_effect=ApiException(status=401, http_resp=Mock(data=b'{"user-message": "USER ERROR MESSAGE"}')))
    resp = client.get(callback_url, follow_redirects=True)
    assert b"USER ERROR MESSAGE" in resp.data

    mocker.patch.object(
            orcid_client.MemberAPIV20Api,
            "view_emails",
            return_value=Mock(data="""{"email": [{"email": "some_ones_else@test.edu"}]}"""))
    resp = client.get(callback_url, follow_redirects=True)
    assert b"cannot verify your email address" in resp.data
    assert user.orcid is None

    mocker.patch.object(
        orcid_client.MemberAPIV20Api,
        "view_emails",
        return_value=Mock(data=json.dumps(dict(email=[dict(email=user.email)]))))
    resp = client.get(callback_url)
    user = User.get(user.id)
    assert user.orcid == "3210-4321-8765-3210"
    assert "viewmembers" in resp.location

    # New non-onboarded organisation
    email = "new_org_via_orcid@new.edu"
    client.login_root()
    send_email.reset_mock()
    resp = client.post(
            "/invite/organisation",
            data={
                "org_name": "NEW ORGANISATION (via ORCID)",
                "org_email": email,
                "tech_contact": "True",
                "via_orcid": "True",
                "first_name": "BRAND",
                "last_name": "NEW",
                "city": "Some City"
            })
    assert resp.status_code == 200
    assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
    assert email.encode() in resp.data
    send_email.assert_called_once()
    _, args = send_email.call_args
    invitation = args.get("invitation")
    invitation_url = urlparse(invitation.url).path
    assert invitation_url.endswith(invitation.token)
    client.logout()

    resp = client.get(invitation_url)
    auth_url = re.search(r"window.location='([^']*)'", resp.data.decode()).group(1)
    qs = parse_qs(urlparse(auth_url).query)
    redirect_uri = qs["redirect_uri"][0]
    oauth_state = qs["state"][0]
    callback_url = redirect_uri + "&state=" + oauth_state
    assert session["oauth_state"] == oauth_state
    mocker.patch(
        "orcid_hub.authcontroller.OAuth2Session.fetch_token",
        return_value={
            "orcid": "3210-4321-8765-8888",
            "name": "ADMIN ADMINISTRATOR",
            "access_token": "xyz",
            "refresh_token": "xyz",
            "scope": "/activities/update",
            "expires_in": "12121"
        })
    mocker.patch.object(
        orcid_client.MemberAPIV20Api,
        "view_emails",
        return_value=Mock(data=json.dumps(dict(email=[dict(email=email)]))))
    resp = client.get(callback_url)
    user = User.get(email=email)
    assert user.orcid == "3210-4321-8765-8888"
    assert "confirm/organisation" in resp.location


def core_mock(
        self=None,
        source_file=None,
        schema_files=None,
        source_data=None,
        schema_data=None,
        extensions=None,
        strict_rule_validation=False,
        fix_ruby_style_regex=False,
        allow_assertions=False,
):
    """Mock validation api call."""
    return None


def validate(self=None, raise_exception=True):
    """Mock validation api call."""
    return False


@patch("pykwalify.core.Core.validate", side_effect=validate)
@patch("pykwalify.core.Core.__init__", side_effect=core_mock)
def test_load_researcher_funding(patch, patch2, request_ctx):
    """Test preload organisation data."""
    org = request_ctx.data["org"]
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
                            b'"GNS170661","external-id-type": "grant_number", "external-id-relationship": "SELF"}]}}]'),
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
                            b'"GNS170661","external-id-type": "grant_number", "external-id-relationship": "SELF"}]}}]'),
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
    org = request_ctx.data["org"]
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
        orcid_client.MemberAPIV20Api,
        "view_work",
        MagicMock(return_value=make_fake_response('{"test":123}', dict={"external_ids": {"external-id": [
            {"external-id-type": "test", "external-id-value": "test", "external-id-url": {"value": "test"},
             "external-id-relationship": "SELF"}]}}))
    ) as view_work, request_ctx(f"/section/{user.id}/WOR/1234/edit") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert admin.email.encode() in resp.data
        assert admin.name.encode() in resp.data
        view_work.assert_called_once_with("XXXX-XXXX-XXXX-0001", 1234)
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
                    "grant_type": "https://test.com",
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
                    "review_url": "test",
                    "subject_external_identifier_type": "test",
                    "subject_external_identifier_value": "test",
                    "subject_container_name": "test",
                    "subject_title": "test",
                    "subject_subtitle": "test",
                    "subject_translated_title": "test",
                    "subject_url": "test",
                    "subject_external_identifier_url": "test",
                    "grant_number": "TEST123",
                    "grant_relationship": "SELF"
                }) as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == f"/section/{user.id}/PRR/list"
    with patch.object(
            orcid_client.MemberAPIV20Api, "create_work",
            MagicMock(return_value=fake_response)), request_ctx(
                f"/section/{user.id}/WOR/new",
                method="POST",
                data={
                    "translated_title": "Auckland",
                    "country": "NZ",
                    "subtitle": "TEST",
                    "title": "test",
                    "work_type": "MANUAL",
                    "publication_date": PartialDate.create("2003-07-14"),
                    "translated_title_language_code": "en",
                    "journal_title": "test",
                    "short_description": "OTHER",
                    "citation_type": "FORMATTED_UNSPECIFIED",
                    "citation": "test",
                    "grant_number": "TEST123",
                    "grant_relationship": "SELF",
                    "grant_type": "https://test.com",
                    "grant_url": "https://test.com",
                    "url": "test",
                    "language_code": "en"
                }) as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        assert resp.location == f"/section/{user.id}/WOR/list"


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
    with patch.object(
        orcid_client.MemberAPIV20Api,
        "delete_work",
            MagicMock(return_value='{"test": "TEST1234567890"}')) as delete_work, request_ctx(
                f"/section/{user.id}/WOR/54321/delete", method="POST") as ctx:
        login_user(admin)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 302
        delete_work.assert_called_once_with("XXXX-XXXX-XXXX-0001", 54321)


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

    resp = client.get("/admin/viewmembers?sort=1")
    assert resp.status_code == 200
    assert b"researcher100@test0.edu" in resp.data

    resp = client.get("/admin/viewmembers?sort=1&desc=1")
    assert resp.status_code == 200
    assert b"researcher100@test0.edu" in resp.data

    resp = client.get("/admin/viewmembers?sort=0")
    assert resp.status_code == 200
    assert b"researcher100@test0.edu" in resp.data

    resp = client.get("/admin/viewmembers?sort=0&desc=1")
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
    resp = client.login(admin0, follow_redirects=True)
    assert b"log in" not in resp.data

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
    fake_response.data = '{"group_id": "new_group_id"}'
    fake_response.headers = {'Location': '12344/xyz/12399'}

    OrcidToken.create(org=org, access_token="ABC123", scope="/group-id-record/update")
    OrcidToken.create(org=org, access_token="ABC123112", scope="/group-id-record/read")

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
    # Save selected groupid record into existing group id record list.
    with patch.object(orcid_client.MemberAPIV20Api, "view_group_id_records",
                      MagicMock(return_value=fake_response)):
        client.login(admin)
        resp = client.post(
            "/search/group_id_record/list",
            data={
                "group_id": "test",
                "name": "test",
                "description": "TEST",
                "type": "TEST"
            })
        assert resp.status_code == 302
        assert urlparse(resp.location).path == "/admin/groupidrecord/"
    # Search the group id record from ORCID
    with patch.object(orcid_client.MemberAPIV20Api, "view_group_id_records",
                      MagicMock(return_value=fake_response)):
        client.login(admin)
        resp = client.post(
            "/search/group_id_record/list",
            data={
                "group_id": "test",
                "group_id_name": "test",
                "description": "TEST",
                "search": True,
                "type": "TEST"
            })
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"


def test_reset_all(request_ctx):
    """Test reset batch process."""
    org = request_ctx.data["org"]
    user = User.create(
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.TECHNICAL,
        orcid=123,
        confirmed=True,
        organisation=org)
    UserOrg.create(user=user, org=org, is_admin=True)

    task1 = Task.create(
        org=org,
        completed_at="12/12/12",
        filename="xyz.txt",
        created_by=user,
        updated_by=user,
        task_type=TaskType.AFFILIATION)

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
        org=org,
        completed_at="12/12/12",
        filename="xyz.txt",
        created_by=user,
        updated_by=user,
        task_type=3)

    PeerReviewRecord.create(
        task=task3,
        review_group_id=1212,
        is_active=True,
        visibility="Test_visibity")

    work_task = Task.create(
        org=org,
        completed_at="12/12/12",
        filename="xyz.txt",
        created_by=user,
        updated_by=user,
        task_type=2)

    WorkRecord.create(
        task=work_task,
        title=1212,
        is_active=True,
        citation_type="Test_citation_type",
        citation_value="Test_visibity")

    researcher_url_task = Task.create(id=12, org=org, filename="xyz.json", created_by=user, updated_by=user,
                                      task_type=5, completed_at="12/12/12")

    ResearcherUrlRecord.create(
        task=researcher_url_task,
        is_active=True,
        status="email sent",
        first_name="Test",
        last_name="Test",
        email="test1234456@mailinator.com",
        visibility="PUBLIC",
        url_name="url name",
        url_value="https://www.xyz.com",
        display_index=0)

    with request_ctx("/reset_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/researcher_url_record_reset_for_batch')])
        request.form = ImmutableMultiDict([('task_id', researcher_url_task.id)])
        resp = ctxx.app.full_dispatch_request()
        t = Task.get(id=researcher_url_task.id)
        rec = t.records.first()
        assert "The record was reset" in rec.status
        assert t.completed_at is None
        assert resp.status_code == 302
        assert resp.location.startswith("http://localhost/researcher_url_record_reset_for_batch")
    with request_ctx("/reset_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/affiliation_record_reset_for_batch')])
        request.form = ImmutableMultiDict([('task_id', task1.id)])
        resp = ctxx.app.full_dispatch_request()
        t = Task.get(id=task1.id)
        rec = t.records.first()
        assert "The record was reset" in rec.status
        assert t.completed_at is None
        assert resp.status_code == 302
        assert resp.location.startswith("http://localhost/affiliation_record_reset_for_batch")
    with request_ctx("/reset_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/funding_record_reset_for_batch')])
        request.form = ImmutableMultiDict([('task_id', task2.id)])
        resp = ctxx.app.full_dispatch_request()
        t = Task.get(id=task2.id)
        rec = t.records.first()
        assert "The record was reset" in rec.status
        assert t.completed_at is None
        assert resp.status_code == 302
        assert resp.location.startswith("http://localhost/funding_record_reset_for_batch")
    with request_ctx("/reset_all", method="POST") as ctxx:
        login_user(user, remember=True)
        request.args = ImmutableMultiDict([('url', 'http://localhost/peer_review_record_reset_for_batch')])
        request.form = ImmutableMultiDict([('task_id', task3.id)])
        resp = ctxx.app.full_dispatch_request()
        t = Task.get(id=task3.id)
        rec = PeerReviewRecord.get(id=1)
        assert "The record was reset" in rec.status
        assert t.completed_at is None
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


def test_sync_profiles(client, mocker):
    """Test organisation switching."""
    def sync_profile_mock(*args, **kwargs):
        utils.sync_profile(*args, **kwargs, delay=0)
        return Mock(id="test-test-test-test")
    mocker.patch("orcid_hub.utils.sync_profile.queue", sync_profile_mock)

    user = User.get(email="admin@test1.edu")
    resp = client.login(user, follow_redirects=True)

    resp = client.get("/sync_profiles")

    resp = client.post("/sync_profiles", data={"start": "Start"}, follow_redirects=True)
    assert Task.select(Task.task_type == TaskType.SYNC).count() == 1

    task = Task.get(task_type=TaskType.SYNC, org=user.organisation)
    resp = client.get(f"/sync_profiles/{task.id}")
    assert resp.status_code == 200

    resp = client.get(f"/sync_profiles/?task_id={task.id}")
    assert resp.status_code == 200

    resp = client.post("/sync_profiles", data={"start": "Start"}, follow_redirects=True)
    assert b"already" in resp.data

    resp = client.post("/sync_profiles", data={"restart": "Restart"}, follow_redirects=True)
    assert Task.select(Task.task_type == TaskType.SYNC).count() == 1

    resp = client.post("/sync_profiles", data={"close": "Close"})
    assert resp.status_code == 302
    assert urlparse(resp.location).path == "/admin/task/"

    client.logout()
    user = User.get(email="researcher100@test0.edu")
    client.login(user)
    resp = client.get("/sync_profiles")
    assert resp.status_code == 302

    client.logout()
    user.roles += Role.TECHNICAL
    user.save()
    client.login(user)
    resp = client.get("/sync_profiles")
    assert resp.status_code == 403

    client.logout()
    client.login_root()
    resp = client.get("/sync_profiles")
    assert resp.status_code == 200


def test_load_researcher_url_csv(client):
    """Test preload researcher url data."""
    user = client.data["admin"]
    client.login(user, follow_redirects=True)
    resp = client.post(
        "/load/researcher/urls",
        data={
            "file_": (BytesIO("""Url Name,Url Value,Display Index,Email,First Name,Last Name,ORCID iD,Put Code,Visibility,Processed At,Status
xyzurl,https://test.com,0,xyz@mailinator.com,sdksdsd,sds1,0000-0001-6817-9711,43959,PUBLIC,,
xyzurlinfo,https://test123.com,10,xyz1@mailinator.com,sdksasadsd,sds1,,,PUBLIC,,""".encode()), "researcher_urls.csv",),
        }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"https://test.com" in resp.data
    assert b"researcher_urls.csv" in resp.data
    assert Task.select().where(Task.task_type == TaskType.RESEARCHER_URL).count() == 1
    task = Task.select().where(Task.task_type == TaskType.RESEARCHER_URL).first()
    assert task.researcher_url_records.count() == 2


def test_load_other_names_csv(client):
    """Test preload other names data."""
    user = client.data["admin"]
    client.login(user, follow_redirects=True)
    resp = client.post(
        "/load/other/names",
        data={
            "file_": (BytesIO("""Content,Display Index,Email,First Name,Last Name,ORCID iD,Put Code,Visibility,Processed At,Status
dummy 1220,0,rad42@mailinator.com,sdsd,sds1,,,PUBLIC,,
dummy 10,0,raosti12dckerpr13233jsdpos8jj2@mailinator.com,sdsd,sds1,0000-0002-0146-7409,16878,PUBLIC,,""".encode()),
                      "other_names.csv",), }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"dummy 1220" in resp.data
    assert b"other_names.csv" in resp.data
    assert Task.select().where(Task.task_type == TaskType.OTHER_NAME).count() == 1
    task = Task.select().where(Task.task_type == TaskType.OTHER_NAME).first()
    assert task.other_name_records.count() == 2


def test_load_peer_review_csv(client):
    """Test preload peer review data."""
    user = client.data["admin"]
    client.login(user, follow_redirects=True)
    resp = client.post(
        "/load/researcher/peer_review",
        data={
            "file_": (
                BytesIO(
                    """Review Group Id,Reviewer Role,Review Url,Review Type,Review Completion Date,Subject External Id Type,Subject External Id Value,Subject External Id Url,Subject External Id Relationship,Subject Container Name,Subject Type,Subject Name Title,Subject Name Subtitle,Subject Name Translated Title Lang Code,Subject Name Translated Title,Subject Url,Convening Org Name,Convening Org City,Convening Org Region,Convening Org Country,Convening Org Disambiguated Identifier,Convening Org Disambiguation Source,Email,ORCID iD,Identifier,First Name,Last Name,Put Code,Visibility,External Id Type,Peer Review Id,External Id Url,External Id Relationship
issn:1213199811,REVIEWER,https://alt-url.com,REVIEW,2012-08-01,doi,10.1087/20120404,https://doi.org/10.1087/20120404,SELF,Journal title,JOURNAL_ARTICLE,Name of the paper reviewed,Subtitle of the paper reviewed,en,Translated title,https://subject-alt-url.com,The University of Auckland,Auckland,Auckland,NZ,385488,RINGGOLD,rad4wwww299ssspppw99pos@mailinator.com,,00001,sdsd,sds1,,PUBLIC,grant_number,GNS1706900961,https://www.grant-url.com2,PART_OF
issn:1213199811,REVIEWER,https://alt-url.com,REVIEW,2012-08-01,doi,10.1087/20120404,https://doi.org/10.1087/20120404,SELF,Journal title,JOURNAL_ARTICLE,Name of the paper reviewed,Subtitle of the paper reviewed,en,Translated title,https://subject-alt-url.com,The University of Auckland,Auckland,Auckland,NZ,385488,RINGGOLD,radsdsd22@mailinator.com,,00032,sdsssd,ffww,,PUBLIC,grant_number,GNS1706900961,https://www.grant-url.com2,PART_OF
issn:1213199811,REVIEWER,https://alt-url.com,REVIEW,2012-08-01,doi,10.1087/20120404,https://doi.org/10.1087/20120404,SELF,Journal title,JOURNAL_ARTICLE,Name of the paper reviewed,Subtitle of the paper reviewed,en,Translated title,https://subject-alt-url.com,The University of Auckland,Auckland,Auckland,NZ,385488,RINGGOLD,rad4wwww299ssspppw99pos@mailinator.com,,00001,sdsd,sds1,,PUBLIC,source-work-id,232xxx22fff,https://localsystem.org/1234,SELF
issn:1213199811,REVIEWER,https://alt-url.com,REVIEW,2012-08-01,doi,10.1087/20120404,https://doi.org/10.1087/20120404,SELF,Journal title,JOURNAL_ARTICLE,Name of the paper reviewed,Subtitle of the paper reviewed,en,Translated title,https://subject-alt-url.com,The University of Auckland,Auckland,Auckland,NZ,385488,RINGGOLD,radsdsd22@mailinator.com,,00032,sdsssd,ffww,,PUBLIC,source-work-id,232xxx22fff,https://localsystem.org/1234,SELF""".encode()  # noqa: E501
                ),  # noqa: E501
                "peer_review.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"issn:1213199811" in resp.data
    assert b"peer_review.csv" in resp.data
    assert Task.select().where(Task.task_type == TaskType.PEER_REVIEW).count() == 1
    task = Task.select().where(Task.task_type == TaskType.PEER_REVIEW).first()
    prr = task.peer_review_records.where(PeerReviewRecord.review_group_id == "issn:1213199811").first()
    assert prr.external_ids.count() == 2
    assert prr.peer_review_invitee.count() == 2


def test_load_funding_csv(client):
    """Test preload organisation data."""
    user = client.data["admin"]
    client.login(user, follow_redirects=True)
    resp = client.post(
        "/load/researcher/funding",
        data={
            "file_": (
                BytesIO(
                    """title,translated title,language,type,org type,short description,amount,currency,start,end,org name,city,region,country,disambiguated organisation identifier,disambiguation source,orcid id,name,role,email,external identifier type,external identifier value,external identifier url,external identifier relationship

THIS IS A TITLE, नमस्ते,hi,  CONTRACT,MY TYPE,Minerals unde.,300000,NZD,,2025,Royal Society Te Apārangi,Wellington,,New Zealand,210126,RINGGOLD,1914-2914-3914-00X3, GivenName Surname, LEAD, test123@org1.edu,grant_number,GNS1706900961,https://www.grant-url2.com,PART_OF
THIS IS A TITLE, नमस्ते,hi,  CONTRACT,MY TYPE,Minerals unde.,300000,NZD,,2025,Royal Society Te Apārangi,Wellington,,New Zealand,210126,RINGGOLD,1885-2885-3885-00X3, GivenName Surname #2, LEAD, test123_2@org1.edu,grant_number,GNS1706900961,https://www.grant-url2.com,PART_OF
THIS IS A TITLE, नमस्ते,hi,  CONTRACT,MY TYPE,Minerals unde.,300000,NZD,,2025,Royal Society Te Apārangi,Wellington,,New Zealand,210126,RINGGOLD,1914-2914-3914-00X3, GivenName Surname, LEAD, test123@org1.edu,type2,GNS9999999999,https://www.grant-url2.com,PART_OF
THIS IS A TITLE, नमस्ते,hi,  CONTRACT,MY TYPE,Minerals unde.,300000,NZD,,2025,Royal Society Te Apārangi,Wellington,,New Zealand,210126,RINGGOLD,1885-2885-3885-00X3, GivenName Surname #2, LEAD, test123_2@org1.edu,type2,GNS9999999999,https://www.grant-url2.com,PART_OF
THIS IS A TITLE #2, नमस्ते #2,hi,  CONTRACT,MY TYPE,Minerals unde.,900000,USD,,2025,,,,,210126,RINGGOLD,1914-2914-3914-00X3, GivenName Surname, LEAD, test123@org1.edu,,,,""".encode()  # noqa: E501
                ),  # noqa: E501
                "fundings.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"THIS IS A TITLE" in resp.data
    assert b"THIS IS A TITLE #2" in resp.data
    assert b"fundings.csv" in resp.data
    assert Task.select().where(Task.task_type == TaskType.FUNDING).count() == 1
    task = Task.select().where(Task.task_type == TaskType.FUNDING).first()
    assert task.funding_records.count() == 2
    fr = task.funding_records.where(FundingRecord.title == "THIS IS A TITLE").first()
    assert fr.contributors.count() == 0
    assert fr.external_ids.count() == 2

    resp = client.get(f"/admin/fundingrecord/export/tsv/?task_id={task.id}")
    assert resp.headers["Content-Type"] == "text/tsv; charset=utf-8"
    assert len(resp.data.splitlines()) == 6

    resp = client.post(
        "/load/researcher/funding",
        data={"file_": (BytesIO(resp.data), "funding000.tsv")},
        follow_redirects=True)
    assert Task.select().where(Task.task_type == TaskType.FUNDING).count() == 2
    task = Task.select().where(Task.filename == "funding000.tsv",
                               Task.task_type == TaskType.FUNDING).first()
    assert task.funding_records.count() == 2
    fr = task.funding_records.where(FundingRecord.title == 'THIS IS A TITLE').first()
    assert fr.contributors.count() == 0
    assert fr.external_ids.count() == 2

    resp = client.get(f"/admin/fundingrecord/export/csv/?task_id={task.id}")
    assert resp.headers["Content-Type"] == "text/csv; charset=utf-8"
    assert len(resp.data.splitlines()) == 6

    resp = client.post(
        "/load/researcher/funding",
        data={"file_": (BytesIO(resp.data), "funding001.csv")},
        follow_redirects=True)
    assert Task.select().where(Task.task_type == TaskType.FUNDING).count() == 3
    task = Task.select().where(Task.filename == "funding001.csv",
                               Task.task_type == TaskType.FUNDING).first()
    assert task.funding_records.count() == 2
    fr = task.funding_records.where(FundingRecord.title == 'THIS IS A TITLE').first()
    assert fr.contributors.count() == 0
    assert fr.external_ids.count() == 2
    assert fr.invitees.count() == 2

    export_resp = client.get(f"/admin/fundingrecord/export/json/?task_id={task.id}")
    assert export_resp.status_code == 200
    assert b'"type": "CONTRACT"' in export_resp.data
    assert b'"title": {"title": {"value": "THIS IS A TITLE"}' in export_resp.data
    assert b'"title": {"title": {"value": "THIS IS A TITLE #2"}' in export_resp.data

    resp = client.post(
        "/load/researcher/funding",
        data={
            "file_": (
                BytesIO(
                    """title	translated title	language	type	org type	short description	amount	aurrency	start	end	org name	city	region	country	disambiguated organisation identifier	disambiguation source	orcid id	name	role	email	external identifier type	external identifier value	external identifier url	external identifier relationship
THIS IS A TITLE #3	 नमस्ते	hi	CONTRACT	MY TYPE	Minerals unde.	300000	NZD		2025	Royal Society Te Apārangi	Wellington		New Zealand	210126	RINGGOLD	1914-2914-3914-00X3	 GivenName Surname	 LEAD	 test123@org1.edu	grant_number	GNS1706900961	https://www.grant-url2.com	PART_OF
THIS IS A TITLE #4	 नमस्ते #2	hi	CONTRACT	MY TYPE	Minerals unde.	900000	USD		2025					210126	RINGGOLD	1914-2914-3914-00X3	 GivenName Surname	 LEAD	 test123@org1.edu				""".encode()  # noqa: E501
                ),  # noqa: E501
                "fundings.tsv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"THIS IS A TITLE #3" in resp.data
    assert b"THIS IS A TITLE #4" in resp.data
    assert b"fundings.tsv" in resp.data

    assert Task.select().where(Task.task_type == TaskType.FUNDING).count() == 4
    task = Task.select().where(Task.task_type == TaskType.FUNDING).order_by(Task.id.desc()).first()
    assert task.funding_records.count() == 2

    resp = client.post(
        "/admin/task/delete/",
        data={
            "id": task.id,
            "url": "/admin/task/"
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert not Task.select().where(Task.id == task.id).exists()

    resp = client.post(
        "/load/researcher/funding",
        data={
            "file_": (
                BytesIO(
                    """title,translated title,language,type,org type,short description,amount,aurrency,start,end,org name,city,region,country,disambiguated organisation identifier,disambiguation source,orcid id,name,role,email,external identifier type,external identifier value,external identifier url,external identifier relationship
THIS IS A TITLE, नमस्ते,hi,,MY TYPE,Minerals unde.,300000,NZD.,,2025,Royal Society Te Apārangi,Wellington,,New Zealand,210126,RINGGOLD,1914-2914-3914-00X3, GivenName Surname, LEAD, test123@org1.edu,grant_number,GNS1706900961,https://www.grant-url2.com,PART_OF

""".encode()  # noqa: E501
                ),  # noqa: E501
                "error.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Failed to load funding record file" in resp.data
    assert b"type is mandatory" in resp.data

    resp = client.post(
        "/load/researcher/funding",
        data={"file_": (BytesIO(b"title\nVAL"), "error.csv")},
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Failed to load funding record file" in resp.data
    assert b"Expected CSV or TSV format file." in resp.data

    resp = client.post(
        "/load/researcher/funding",
        data={"file_": (BytesIO(b"header1,header2,header2\n1,2,3"), "error.csv")},
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Failed to load funding record file" in resp.data
    assert b"Failed to map fields based on the header of the file" in resp.data

    resp = client.post(
        "/load/researcher/funding",
        data={
            "file_": (
                BytesIO(
                    """title,translated title,language,type,org type,short description,amount,aurrency,start,end,org name,city,region,country,disambiguated organisation identifier,disambiguation source,orcid id,name,role,email,external identifier type,external identifier value,external identifier url,external identifier relationship
THIS IS A TITLE #2, नमस्ते #2,hi, CONTRACT,MY TYPE,Minerals unde.,900000,USD.,,**ERROR**,,,,,210126,RINGGOLD,1914-2914-3914-00X3, GivenName Surname, LEAD, test123@org1.edu,,,,""".encode()  # noqa: E501
                ),  # noqa: E501
                "fundings.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Failed to load funding record file" in resp.data
    assert b"Wrong partial date value '**ERROR**'" in resp.data

    resp = client.post(
        "/load/researcher/funding",
        data={
            "file_": (
                BytesIO(
                    """title,translated title,language,type,org type,short description,amount,aurrency,start,end,org name,city,region,country,disambiguated organisation identifier,disambiguation source,orcid id,name,role,email,external identifier type,external identifier value,external identifier url,external identifier relationship

THIS IS A TITLE, नमस्ते,hi,  CONTRACT,MY TYPE,Minerals unde.,300000,NZD.,,2025,Royal Society Te Apārangi,Wellington,,New Zealand,210126,RINGGOLD,1914-2914-3914-00X3, GivenName Surname, LEAD,**ERROR**,grant_number,GNS1706900961,https://www.grant-url2.com,PART_OF """.encode()  # noqa: E501
                ),  # noqa: E501
                "fundings.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Failed to load funding record file" in resp.data
    assert b"Invalid email address '**error**'" in resp.data

    resp = client.post(
        "/load/researcher/funding",
        data={
            "file_": (
                BytesIO(
                    """title,translated title,language,type,org type,short description,amount,aurrency,start,end,org name,city,region,country,disambiguated organisation identifier,disambiguation source,orcid id,name,role,email,external identifier type,external identifier value,external identifier url,external identifier relationship

THIS IS A TITLE, नमस्ते,hi,  CONTRACT,MY TYPE,Minerals unde.,300000,NZD.,,2025,Royal Society Te Apārangi,Wellington,,New Zealand,210126,RINGGOLD,ERRO-R914-3914-00X3, GivenName Surname, LEAD,user1234@test123.edu,grant_number,GNS1706900961,https://www.grant-url2.com,PART_OF """.encode()  # noqa: E501
                ),  # noqa: E501
                "fundings.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Failed to load funding record file" in resp.data
    assert b"Invalid ORCID iD ERRO-R" in resp.data

    # without "excluded"
    resp = client.post(
        "/load/researcher/funding",
        data={
            "file_": (
                BytesIO(
                    """Put Code,Title,Translated Title,Translated Title Language Code,Type,Organization Defined Type,Short Description,Amount,Currency,Start Date,End Date,Org Name,City,Region,Country,Disambiguated Org Identifier,Disambiguation Source,Visibility,ORCID iD,Email,First Name,Last Name,Name,Role,External Id Type,External Id Value,External Id Url,External Id Relationship,Identifier
,This is the project title,,,CONTRACT,Fast-Start,This is the project abstract,300000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,0000-0002-9207-4933,,,,Associate Professor A Contributor 1,lead,grant_number,XXX1701,,SELF,
,This is the project title,,,CONTRACT,Fast-Start,This is the project abstract,300000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,,,,Dr B Contributor 2,co_lead,grant_number,XXX1701,,SELF,
,This is the project title,,,CONTRACT,Fast-Start,This is the project abstract,300000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,,,,Dr E Contributor 3,,grant_number,XXX1701,,SELF,
,This is another project title,,,CONTRACT,Standard,This is another project abstract,800000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,contributor4@mailinator.com,,,Associate Professor F Contributor 4,lead,grant_number,XXX1702,,SELF,9999
,This is another project title,,,CONTRACT,Standard,This is another project abstract,800000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,contributor5@mailinator.com,John,Doe,,co_lead,grant_number,XXX1702,,SELF,8888 """.encode()  # noqa: E501
                ),  # noqa: E501
                "fundings042.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"This is the project title" in resp.data
    assert b"This is another project title" in resp.data
    assert b"fundings042.csv" in resp.data
    assert Task.select().where(Task.task_type == TaskType.FUNDING).count() == 4
    task = Task.select().where(Task.filename == "fundings042.csv").first()
    assert task.funding_records.count() == 2
    fr = task.funding_records.where(FundingRecord.title == "This is another project title").first()
    assert fr.contributors.count() == 0
    assert fr.external_ids.count() == 1
    assert fr.invitees.count() == 2

    resp = client.get(f"/admin/fundingrecord/export/tsv/?task_id={task.id}")
    assert resp.headers["Content-Type"] == "text/tsv; charset=utf-8"
    assert len(resp.data.splitlines()) == 4

    resp = client.post(
        "/load/researcher/funding",
        data={
            "file_": (
                BytesIO(b"""Funding Id,Identifier,Put Code,Title,Translated Title,Translated Title Language Code,Type,Organization Defined Type,Short Description,Amount,Currency,Start Date,End Date,Org Name,City,Region,Country,Disambiguated Org Identifier,Disambiguation Source,Visibility,ORCID iD,Email,First Name,Last Name,Name,Role,Excluded,External Id Type,External Id Url,External Id Relationship
XXX1701,00002,,This is the project title,,,CONTRACT,Fast-Start,This is the project abstract,300000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,contributor2@mailinator.com,Bob,Contributor 2,,,Y,grant_number,,SELF
XXX1701,00003,,This is the project title,,,CONTRACT,Fast-Start,This is the project abstract,300000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,contributor3@mailinator.com,Eve,Contributor 3,,,Y,grant_number,,SELF
XXX1702,00004,,This is another project title,,,CONTRACT,Standard,This is another project abstract,800000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,contributor4@mailinator.com,Felix,Contributor 4,,,Y,grant_number,,SELF"""  # noqa: E501
                ),  # noqa: E501
                "fundings_ex.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"the project title" in resp.data
    assert b"fundings_ex.csv" in resp.data
    assert Task.select().where(Task.task_type == TaskType.FUNDING).count() == 5
    task = Task.select().where(Task.task_type == TaskType.FUNDING).order_by(Task.id.desc()).first()
    assert task.funding_records.count() == 2
    for r in task.funding_records:
        assert r.invitees.count() == 0


def test_researcher_work(client):
    """Test preload work data."""
    user = client.data["admin"]
    client.login(user, follow_redirects=True)
    resp = client.post(
        "/load/researcher/work",
        data={
            "file_": (
                BytesIO(
                    b'[{"invitees": [{"identifier":"00001", "email": "marco.232323newwjwewkppp@mailinator.com",'
                    b'"first-name": "Alice", "last-name": "Contributor 1", "ORCID-iD": null, "put-code":null}],'
                    b'"title": { "title": { "value": "WORK TITLE #1"}}, "citation": {"citation-type": '
                    b'"FORMATTED_UNSPECIFIED", "citation-value": "This is citation value"}, "type": "BOOK_CHR",'
                    b'"contributors": {"contributor": [{"contributor-attributes": {"contributor-role": '
                    b'"AUTHOR", "contributor-sequence" : "1"},"credit-name": {"value": "firentini"}}]}'
                    b', "external-ids": {"external-id": [{"external-id-value": '
                    b'"GNS170661","external-id-type": "grant_number", "external-id-relationship": "SELF"}]}}]'),
                "work001.json",
            ),
            "email":
            user.email
        },
        follow_redirects=True)
    assert resp.status_code == 200
    # Work file successfully loaded.
    assert b"WORK TITLE #1" in resp.data
    assert b"BOOK_CHR" in resp.data
    task = Task.get(filename="work001.json")
    assert task.records.count() == 1
    rec = task.records.first()
    assert rec.external_ids.count() == 1
    assert rec.contributors.count() == 1
    assert rec.invitees.count() == 1

    resp = client.get(f"/admin/workrecord/export/csv/?task_id={task.id}")
    assert resp.headers["Content-Type"] == "text/csv; charset=utf-8"
    assert len(resp.data.splitlines()) == 3

    resp = client.get(f"/admin/workrecord/export/csv/?task_id={task.id}")
    assert resp.headers["Content-Type"] == "text/csv; charset=utf-8"
    assert len(resp.data.splitlines()) == 3

    resp = client.post(
        "/load/researcher/work",
        data={
            "file_": (
                BytesIO("""[{
    "invitees": [
      {
        "identifier": "00001", "email": "contributor1@mailinator.com",
        "first-name": "Alice", "last-name": "Contributor 1",
        "ORCID-iD": "0000-0002-9207-4933", "put-code": null, "visibility": null
      },
      {
        "identifier": "00002", "email": "contributor2@mailinator.com",
        "first-name": "Bob", "last-name": "Contributor 2", "ORCID-iD": null,
        "put-code": null, "visibility": null
      }
    ],
    "path": null,
    "title": {
      "title": {"value": "This is a title"},
      "subtitle": null,
      "translated-title": {"value": "हिंदी","language-code": "hi"}
    },
    "journal-title": {"value": "This is a journal title"},
    "short-description": "xyz this is short description",
    "citation": {"citation-type": "FORMATTED_UNSPECIFIED", "citation-value": "This is citation value"},
    "type": "BOOK_CHAPTER",
    "publication-date": {
      "year": {"value": "2001"},
      "month": {"value": "1"},
      "day": {"value": "12"},
      "media-type": null
    },
    "external-ids": {
      "external-id": [{
          "external-id-type": "bibcode",
          "external-id-value": "sdsds",
          "external-id-url": {"value": "http://url.edu/abs/ghjghghj"},
          "external-id-relationship": "SELF"
        }
      ]
    },
    "url": null,
    "contributors": {
      "contributor": [
        {"contributor-attributes": {"contributor-sequence": "FIRST", "contributor-role": "AUTHOR"},
          "credit-name": {"value": "Associate Professor Alice"},
          "contributor-orcid": {
            "uri": "https://sandbox.orcid.org/0000-0002-9207-4933",
            "path": "0000-0002-9207-4933",
            "host": "sandbox.orcid.org"
          }
        },
        {"contributor-attributes": {"contributor-sequence": "ADDITIONAL", "contributor-role": "AUTHOR"},
          "credit-name": {"value": "Dr Bob"}
        }
      ]
    },
    "language-code": "en",
    "country": {"value": "NZ"}
  }
]""".encode()),
                "work002.json",
            ),
            "email": user.email
        },
        follow_redirects=True)
    assert resp.status_code == 200
    # Work file successfully loaded.
    assert b"FORMATTED_UNSPECIFIED" in resp.data
    task = Task.get(filename="work002.json")
    assert task.records.count() == 1
    rec = task.records.first()
    assert rec.external_ids.count() == 1
    assert rec.contributors.count() == 2
    assert rec.invitees.count() == 2

    resp = client.get(f"/admin/workrecord/export/csv/?task_id={task.id}")
    assert resp.headers["Content-Type"] == "text/csv; charset=utf-8"
    assert len(resp.data.splitlines()) == 5

    resp = client.post(
        "/load/researcher/work",
        data={"file_": (BytesIO(resp.data), "work003.csv")},
        follow_redirects=True)
    assert Task.select().where(Task.task_type == TaskType.WORK).count() == 3
    task = Task.select().where(Task.filename == "work003.csv",
                               Task.task_type == TaskType.WORK).first()
    assert task.records.count() == 1
    rec = task.records.first()
    assert rec.external_ids.count() == 1
    assert rec.contributors.count() == 2
    assert rec.invitees.count() == 2

    resp = client.post(
        "/load/researcher/work",
        data={"file_": (BytesIO(b"title\nVAL"), "error.csv")},
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Failed to load work record file" in resp.data
    assert b"Expected CSV or TSV format file." in resp.data

    resp = client.post(
        "/load/researcher/work",
        data={"file_": (BytesIO(b"header1,header2,header2\n1,2,3"), "error.csv")},
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Failed to load work record file" in resp.data
    assert b"Failed to map fields based on the header of the file" in resp.data

    export_resp = client.get(f"/admin/workrecord/export/json/?task_id={task.id}")
    assert export_resp.status_code == 200
    assert b"BOOK_CHAPTER" in export_resp.data
    assert b'journal-title": {"value": "This is a journal title"}' in export_resp.data

    resp = client.post(
        "/load/researcher/work",
        data={
            "file_": (
                BytesIO(
                    """Work Id,Put Code,Title,Sub Title,Translated Title,Translated Title Language Code,Journal Title,Short Description,Citation Type,Citation Value,Type,Publication Date,Publication Media Type,Url,Language Code,Country,Visibility,ORCID iD,Email,First Name,Last Name,Name,Role,Excluded,External Id Type,External Id Url,External Id Relationship
sdsds,,This is a title,,,hi,This is a journal title,xyz this is short description,FORMATTED_UNSPECIFIED,This is citation value,BOOK_CHAPTER,**ERROR**,,,en,NZ,,0000-0002-9207-4933,contributor1@mailinator.com,Alice,Contributor 1,,,,bibcode,http://url.edu/abs/ghjghghj,SELF
sdsds,,This is a title,,,hi,This is a journal title,xyz this is short description,FORMATTED_UNSPECIFIED,This is citation value,BOOK_CHAPTER,2001-01-12,,,en,NZ,,0000-0002-9207-4933,,,,Associate Professor Alice,AUTHOR,Y,bibcode,http://url.edu/abs/ghjghghj,SELF""".encode()  # noqa: E501
                ),  # noqa: E501
                "work.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Failed to load work record file" in resp.data
    assert b"Wrong partial date value '**ERROR**'" in resp.data

    resp = client.post(
        "/load/researcher/work",
        data={
            "file_": (
                BytesIO(
                    """Work Id,Put Code,Title,Sub Title,Translated Title,Translated Title Language Code,Journal Title,Short Description,Citation Type,Citation Value,Type,Publication Date,Publication Media Type,Url,Language Code,Country,Visibility,ORCID iD,Email,First Name,Last Name,Name,Role,Excluded,External Id Type,External Id Url,External Id Relationship
sdsds,,This is a title,,,hi,This is a journal title,xyz this is short description,FORMATTED_UNSPECIFIED,This is citation value,BOOK_CHAPTER,,,,en,NZ,,0000-0002-9207-4933,**ERROR**,Alice,Contributor 1,,,,bibcode,http://url.edu/abs/ghjghghj,SELF
sdsds,,This is a title,,,hi,This is a journal title,xyz this is short description,FORMATTED_UNSPECIFIED,This is citation value,BOOK_CHAPTER,2001-01-12,,,en,NZ,,0000-0002-9207-4933,,,,Associate Professor Alice,AUTHOR,Y,bibcode,http://url.edu/abs/ghjghghj,SELF""".encode()  # noqa: E501
                ),  # noqa: E501
                "work.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Failed to load work record file" in resp.data
    assert b"Invalid email address '**error**'" in resp.data

    resp = client.post(
        "/load/researcher/work",
        data={
            "file_": (
                BytesIO(
                    """Work Id,Put Code,Title,Sub Title,Translated Title,Translated Title Language Code,Journal Title,Short Description,Citation Type,Citation Value,Type,Publication Date,Publication Media Type,Url,Language Code,Country,Visibility,ORCID iD,Email,First Name,Last Name,Name,Role,Excluded,External Id Type,External Id Url,External Id Relationship
sdsds,,This is a title,,,hi,This is a journal title,xyz this is short description,FORMATTED_UNSPECIFIED,This is citation value,BOOK_CHAPTER,,,,en,NZ,,**ERROR**,alice@test.edu,Alice,Contributor 1,,,,bibcode,http://url.edu/abs/ghjghghj,SELF
sdsds,,This is a title,,,hi,This is a journal title,xyz this is short description,FORMATTED_UNSPECIFIED,This is citation value,BOOK_CHAPTER,2001-01-12,,,en,NZ,,0000-0002-9207-4933,,,,Associate Professor Alice,AUTHOR,Y,bibcode,http://url.edu/abs/ghjghghj,SELF""".encode()  # noqa: E501
                ),  # noqa: E501
                "work.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"Failed to load work record file" in resp.data
    assert b"Invalid ORCID iD **ERROR**" in resp.data

    # Conten and extension mismatch:
    Task.delete().execute()
    resp = client.post(
        "/load/researcher/work",
        data={
            "file_": (open(os.path.join(os.path.dirname(__file__), "data", "example_works.json"), "rb"),
                      "works042.csv"),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert Task.select().count() == 0
    assert b"Failed to load work record file" in resp.data


def test_peer_reviews(client):
    """Test peer review data management."""
    user = client.data["admin"]
    client.login(user, follow_redirects=True)
    resp = client.post(
        "/load/researcher/peer_review",
        data={
            "file_": (
                BytesIO(b"""[{
  "invitees": [
  {
    "identifier":"00001",
    "email": "contributor1@mailinator.com",
    "first-name": "Alice", "last-name": "Contributor 1",
    "ORCID-iD": "0000-0002-9207-4933"},
  {
    "identifier":"00002",
    "email": "contributor2@mailinator.com",
    "first-name": "Bob", "last-name": "Contributor 2"}],
  "reviewer-role": "REVIEWER",
  "review-identifiers": {
    "external-id": [{
      "external-id-type": "source-work-id",
      "external-id-value": "1212221",
      "external-id-url": {
        "value": "https://localsystem.org/1234"
      },
      "external-id-relationship": "SELF"
    }]
  },
  "review-url": {
    "value": "https://alt-url.com"
  },
  "review-type": "REVIEW",
  "review-completion-date": {
    "year": {
      "value": "2012"
    },
    "month": {
      "value": "08"
    },
    "day": {
      "value": "01"
    }
  },
  "review-group-id": "issn:12131",
  "subject-external-identifier": {
    "external-id-type": "doi",
    "external-id-value": "10.1087/20120404",
    "external-id-url": {
      "value": "https://doi.org/10.1087/20120404"
    },
    "external-id-relationship": "SELF"
  },
  "subject-container-name": {
    "value": "Journal title"
  },
  "subject-type": "JOURNAL_ARTICLE",
  "subject-name": {
    "title": {
      "value": "Name of the paper reviewed"
    },
    "subtitle": {
      "value": "Subtitle of the paper reviewed"
    },
    "translated-title": {
      "language-code": "en",
      "value": "Translated title"
    }
  },
  "subject-url": {
    "value": "https://subject-alt-url.com"
  },
  "convening-organization": {
    "name": "The University of Auckland",
    "address": {
      "city": "Auckland",
      "region": "Auckland",
      "country": "NZ"
    },
    "disambiguated-organization": {
      "disambiguated-organization-identifier": "385488",
      "disambiguation-source": "RINGGOLD"
    }
  }
}]"""),
                "peer_reviews_001.json",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"https://doi.org/10.1087/20120404" in resp.data
    task = Task.get(filename="peer_reviews_001.json")
    assert task.records.count() == 1
    rec = task.records.first()
    assert rec.external_ids.count() == 1

    resp = client.get(f"/admin/peerreviewrecord/export/json/?task_id={task.id}")
    assert resp.status_code == 200
    assert b'"review-type": "REVIEW"' in resp.data
    assert b'"invitees": [' in resp.data
    assert b'"review-group-id": "issn:12131"' in resp.data


def test_other_names(client):
    """Test researcher other name data management."""
    user = client.data["admin"]
    client.login(user, follow_redirects=True)
    resp = client.post(
        "/load/other/names",
        data={
            "file_": (
                BytesIO(b"""{
  "created-at": "2019-02-15T04:39:23",
  "filename": "othernames_sample_latest.json",
  "records": [
    {
      "content": "dummy 1220",
      "display-index": 0,
      "email": "rad42@mailinator.com",
      "first-name": "sdsd",
      "last-name": "sds1",
      "orcid": null,
      "processed-at": null,
      "put-code": null,
      "status": "The record was reset at 2019-02-20T08:31:49",
      "visibility": "PUBLIC"
    },
    {
      "content": "dummy 10",
      "display-index": 0,
      "email": "xyzz@mailinator.com",
      "first-name": "sdsd",
      "last-name": "sds1",
      "orcid": "0000-0002-0146-7409",
      "processed-at": null,
      "put-code": 16878,
      "status": "The record was reset at 2019-02-20T08:31:49",
      "visibility": "PUBLIC"
    }
  ],
  "task-type": "OTHER_NAME",
  "updated-at": "2019-02-19T19:31:49"}"""),
                "othernames_sample_latest.json",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"dummy 1220" in resp.data
    task = Task.get(filename="othernames_sample_latest.json")
    assert task.records.count() == 2

    resp = client.get(f"/admin/othernamerecord/export/json/?task_id={task.id}")
    assert resp.status_code == 200
    assert b'xyzz@mailinator.com' in resp.data
    assert b'dummy 1220' in resp.data
    assert b'dummy 10' in resp.data


def test_researcher_url(client):
    """Test researcher url data management."""
    user = client.data["admin"]
    client.login(user, follow_redirects=True)
    resp = client.post(
        "/load/researcher/urls",
        data={
            "file_": (
                BytesIO(b"""{
  "records": [
    {
      "display-index": 0, "email": "xyzzz@mailinator.com", "first-name": "sdksdsd", "last-name": "sds1",
      "orcid": "0000-0001-6817-9711", "put-code": 43959, "url-name": "xyzurl",
      "url-value": "https://fdhfdasa112j.com", "visibility": "PUBLIC"
    },
    {
      "display-index": 10, "email": "dsjdh11222@mailinator.com", "first-name": "sdksasadsd",
      "last-name": "sds1", "put-code": null, "orcid": null, "url-name": "xyzurl",
      "url-value": "https://fdhfdasa112j.com", "visibility": "PUBLIC"
    }]}"""),
                "researcher_url_001.json",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert b"https://fdhfdasa112j.com" in resp.data
    task = Task.get(filename="researcher_url_001.json")
    assert task.records.count() == 2

    resp = client.get(f"/admin/researcherurlrecord/export/json/?task_id={task.id}")
    assert resp.status_code == 200
    assert b'xyzzz@mailinator.com' in resp.data
    assert b'https://fdhfdasa112j.com' in resp.data
