# -*- coding: utf-8 -*-
"""Tests for core functions."""

from flask_login import login_user
from urllib.parse import urlparse

from orcid_hub.models import OrcidToken, User
from orcid_hub.orcid_client import NestedDict
import json


def test_admin_view_access(request_ctx):
    """Test if SUPERUSER can run reports."""
    user = User.get(email="root@test0.edu")
    with request_ctx("/org_invitatin_summary") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert b"Organisation Invitation Summary" in resp.data
        assert b"root@test0.edu" in resp.data


def test_user_invitation_summary(request_ctx):
    """Test user invitation summary."""
    user = User.get(email="root@test0.edu")
    with request_ctx("/user_invitatin_summary") as ctx:
        login_user(user, remember=True)
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
        assert b"User Invitation Summary" in resp.data
        assert b"root@test0.edu" in resp.data


def test_user_summary(client):
    """Test user summary."""
    client.login_root()

    resp = client.get("/user_summary?from_date=2017-01-01&to_date=2018-02-28")
    assert resp.status_code == 200
    assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
    assert b"TEST0" in resp.data and b"TEST1" in resp.data
    assert b"root@test0.edu" in resp.data
    assert b"5 / 10 (50%)" in resp.data

    resp = client.get("/user_summary?from_date=2017-01-01&to_date=2017-12-31")
    assert resp.status_code == 200
    assert b"<!DOCTYPE html>" in resp.data, "Expected HTML content"
    assert b"TEST0" in resp.data
    assert b"root@test0.edu" in resp.data
    assert b"0 / 10 (0%)" in resp.data

    for (sort, desc) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        resp = client.get(f"/user_summary?from_date=2017-01-01&to_date=2018-12-31&sort={sort}&desc={desc}")
        assert resp.status_code == 200
        data = resp.data.decode()
        assert f"&sort={0 if sort else 1}&desc=0" in data
        assert f"&sort={sort}&desc={0 if desc else 1}" in data

    resp = client.get("/user_summary")
    assert resp.status_code == 302


def test_user_cv(client, mocker):
    """Test user CV."""
    user0 = User.get(email="root@test0.edu")
    client.login(user0)
    resp = client.get("/user_cv")
    assert resp.status_code == 302
    client.logout()

    user = User.get(email="researcher101@test1.edu")
    client.login(user, follow_redirects=True)

    resp = client.get("/user_cv")
    assert resp.status_code == 302
    url = urlparse(resp.location)
    assert url.path == '/link'

    OrcidToken.create(
        access_token="ABC12345678901",
        user=user,
        org=user.organisation,
        scopes="/scope/read-limited")

    mocker.patch("orcid_hub.reports.MemberAPI.get_record", side_effect=Exception("ERROR!!!"))
    resp = client.get("/user_cv", follow_redirects=True)
    assert resp.status_code == 200
    assert b"iframe" not in resp.data
    assert b"ERROR!!!" in resp.data

    get_record = mocker.patch(
        "orcid_hub.reports.MemberAPI.get_record",
        return_value=json.loads(
            json.dumps({
                "orcid-identifier": {
                    "uri": "http://sandbox.orcid.org/0000-0001-7027-8698",
                    "path": "0000-0001-7027-8698",
                    "host": "sandbox.orcid.org"
                },
                "preferences": {
                    "locale": "EN"
                },
                "history": {
                    "creation-method": "MEMBER_REFERRED",
                    "completion-date": None,
                    "submission-date": {
                        "value": 1505964892638
                    },
                    "last-modified-date": {
                        "value": 1505965202659
                    },
                    "claimed": True,
                    "source": None,
                    "deactivation-date": None,
                    "verified-email": False,
                    "verified-primary-email": False
                },
                "person": {
                    "last-modified-date": {
                        "value": 1505964892861
                    },
                    "name": {
                        "created-date": {
                            "value": 1505964892638
                        },
                        "last-modified-date": {
                            "value": 1505964892861
                        },
                        "given-names": {
                            "value": "Sally"
                        },
                        "family-name": {
                            "value": "Simpsond"
                        },
                        "credit-name": None,
                        "source": None,
                        "visibility": "PUBLIC",
                        "path": "0000-0001-7027-8698"
                    },
                    "other-names": {
                        "last-modified-date": None,
                        "other-name": [],
                        "path": "/0000-0001-7027-8698/other-names"
                    },
                    "biography": None,
                    "researcher-urls": {
                        "last-modified-date": None,
                        "researcher-url": [],
                        "path": "/0000-0001-7027-8698/researcher-urls"
                    },
                    "emails": {
                        "last-modified-date": {
                            "value": 1505964892861
                        },
                        "email": [{
                            "created-date": {
                                "value": 1505964892861
                            },
                            "last-modified-date": {
                                "value": 1505964892861
                            },
                            "source": {
                                "source-orcid": {
                                    "uri": "http://sandbox.orcid.org/0000-0001-7027-8698",
                                    "path": "0000-0001-7027-8698",
                                    "host": "sandbox.orcid.org"
                                },
                                "source-client-id": None,
                                "source-name": {
                                    "value": "Sally Simpson"
                                }
                            },
                            "email": "researcher101@test1.edu",
                            "path": None,
                            "visibility": "LIMITED",
                            "verified": False,
                            "primary": True,
                            "put-code": None
                        }],
                        "path":
                        "/0000-0001-7027-8698/email"
                    },
                    "addresses": {
                        "last-modified-date": None,
                        "address": [],
                        "path": "/0000-0001-7027-8698/address"
                    },
                    "keywords": {
                        "last-modified-date": None,
                        "keyword": [],
                        "path": "/0000-0001-7027-8698/keywords"
                    },
                    "external-identifiers": {
                        "last-modified-date": None,
                        "external-identifier": [],
                        "path": "/0000-0001-7027-8698/external-identifiers"
                    },
                    "path": "/0000-0001-7027-8698/person"
                },
                "activities-summary": {
                    "last-modified-date": None,
                    "educations": {
                        "last-modified-date": None,
                        "education-summary": [],
                        "path": "/0000-0001-7027-8698/educations"
                    },
                    "employments": {
                        "last-modified-date": None,
                        "employment-summary": [],
                        "path": "/0000-0001-7027-8698/employments"
                    },
                    "fundings": {
                        "last-modified-date": None,
                        "group": [],
                        "path": "/0000-0001-7027-8698/fundings"
                    },
                    "peer-reviews": {
                        "last-modified-date": None,
                        "group": [],
                        "path": "/0000-0001-7027-8698/peer-reviews"
                    },
                    "works": {
                        "last-modified-date": None,
                        "group": [],
                        "path": "/0000-0001-7027-8698/works"
                    },
                    "path": "/0000-0001-7027-8698/activities"
                },
                "path": "/0000-0001-7027-8698"
            }),
            object_pairs_hook=NestedDict))

    resp = client.get("/user_cv")
    assert resp.status_code == 200
    assert b"iframe" in resp.data
    assert user.first_name.encode() not in resp.data

    resp = client.get("/user_cv/show")
    assert resp.status_code == 200
    assert user.name.encode() in resp.data
    get_record.assert_called_once_with()

    get_record.reset_mock()
    resp = client.get("/user_cv/download")
    assert resp.status_code == 200
    assert user.name.replace(' ', '_') in resp.headers["Content-Disposition"]
    assert b"content.xml" in resp.data
    get_record.asser_not_called()
