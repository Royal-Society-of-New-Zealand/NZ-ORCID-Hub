# -*- coding: utf-8 -*-
"""Tests for core functions."""

import json
import sys
import time
from itertools import product
from unittest.mock import MagicMock, patch

import pytest
from flask_login import login_user
from peewee import SqliteDatabase
from playhouse.test_utils import test_database

from . import orcid_client, views
from .config import ORCID_BASE_URL
from .models import UserOrgAffiliation  # noqa: E128
from .models import (AffiliationRecord, OrcidToken, Organisation, Role, Task, User, UserOrg)

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
    org = Organisation.get_or_create(
        id=1,
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=True,
        orcid_client_id="CLIENT ID",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="SOURCE")
    org = Organisation.get(id=1)
    u = User.get_or_create(
        id=123,
        email="test123@test.test.net",
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid=123,
        organisation_id=1,
        confirmed=True,
        organisation=org)
    u = User.get(id=123)

    OrcidToken.get_or_create(user=u, org=org, access_token="ABC123")

    with request_ctx("/"):
        login_user(u)
        rv = views.show_record_section(user_id=123)
        assert u.email in rv


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
