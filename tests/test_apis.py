# -*- coding: utf-8 -*-
"""Tests for core functions."""

import copy
import json
import yaml
from datetime import datetime
from io import BytesIO
import os

import pytest

from orcid_hub.apis import yamlfy
from orcid_hub.data_apis import plural
from orcid_hub.models import (AffiliationRecord, Client, OrcidToken, Organisation, Task, TaskType,
                              Token, User)

from unittest.mock import patch, MagicMock


def test_plural():
    """Test noun pluralization."""
    assert plural("wolf") == "wolves"
    assert plural("knife") == "knives"
    assert plural("potato") == "potatoes"
    assert plural("cactus") == "cacti"
    # assert plural("criterion") == "criteria"
    assert plural("organisation") == "organisations"
    assert plural("community") == "communities"
    assert plural("six") == "sixes"
    assert plural("carrot") == "carrots"


def test_get_oauth_access_token(client):
    """Test the acquisition of OAuth access token."""
    resp = client.post(
            "/oauth/token",
            data=dict(
                grant_type="client_credentials",
                client_id="CLIENT_ID",
                client_secret="CLIENT_SECRET"))
    assert resp.status_code == 200
    c = Client.get(client_id="CLIENT_ID")
    token = Token.get(client=c)
    assert resp.json["access_token"] == token.access_token
    assert resp.json["expires_in"] == client.application.config["OAUTH2_PROVIDER_TOKEN_EXPIRES_IN"]
    assert resp.json["token_type"] == token.token_type
    # prevously created access token should be removed
    assert not Token.select().where(Token.access_token == "TEST").exists()

    resp = client.post(
            "/oauth/token",
            data=dict(
                grant_type="client_credentials",
                client_id="NOT-EXISTING-CLIENT_ID",
                client_secret="CLIENT_SECRET"))
    # login_user(user, remember=True)
    assert resp.status_code == 401
    assert resp.json["error"] == "invalid_client"

    resp = client.post(
            "/oauth/token",
            data=dict(
                grant_type="client_credentials",
                client_id="CLIENT_ID",
                client_secret="INCORRECT"))
    # login_user(user, remember=True)
    assert resp.status_code == 401
    assert resp.json["error"] == "invalid_client"

    resp = client.post(
            "/oauth/token",
            data=dict(
                grant_type="INCORRECT",
                client_id="NOT-EXISTING-CLIENT_ID",
                client_secret="CLIENT_SECRET"))
    # login_user(user, remember=True)
    assert resp.status_code == 400
    assert resp.json["error"] == "unsupported_grant_type"


# def test_revoke_access_token(client):
#     """Test the acquisition of OAuth access token."""
#     resp = client.get(
#             "/oauth/token",
#             method="POST",
#             data=dict(
#                 grant_type="client_credentials",
#                 client_id="CLIENT_ID",
#                 client_secret="CLIENT_SECRET"))
#         resp = ctx.app.full_dispatch_request()
#         assert resp.status_code == 200
#         data = json.loads(resp.data)
#         client = Client.get(client_id="CLIENT_ID")
#         token = Token.get(client=client)
#         assert data["access_token"] == token.access_token

#     resp = client.get(
#             "/oauth/token",
#             data=dict(
#                 grant_type="client_credentials",
#                 client_id="CLIENT_ID",
#                 client_secret="CLIENT_SECRET"))
#         resp = ctx.app.full_dispatch_request()
#         assert resp.status_code == 200
#         data = json.loads(resp.data)


def test_me(client):
    """Test the echo endpoint."""
    user = User.get(email="app123@test0.edu")
    token = Token.get(user=user)
    resp = client.get("/api/me", headers=dict(authorization=f"Bearer {token.access_token}"))
    assert resp.status_code == 200
    assert resp.json["email"] == user.email
    assert resp.json["name"] == user.name

    # Test invalid token:
    resp = client.get("/api/me", headers=dict(authorization="Bearer INVALID"))
    assert resp.status_code == 401

    # Test expired token:
    token.expires = datetime(1971, 1, 1)
    token.save()
    resp = client.get("/api/me", headers=dict(authorization=f"Bearer {token.access_token}"))
    assert resp.status_code == 401


@pytest.mark.parametrize("resource", [
    "users",
    "tokens",
])
@pytest.mark.parametrize("version", [
    "v1.0",
])
def test_user_and_token_api(client, resource, version):
    """Test the echo endpoint."""
    user = User.get(email="researcher@test0.edu")
    org2_user = User.get(email="researcher@org2.edu")
    resp = client.get(
            f"/api/{version}/{resource}/ABC123", headers=dict(authorization="Bearer TEST"))
    assert resp.status_code == 400
    assert "error" in resp.json
    assert "incorrect identifier" in resp.json["error"].lower()

    resp = client.get(
            f"/api/{version}/{resource}/0000-0000-0000-0000",
            headers=dict(authorization="Bearer TEST"))
    assert resp.status_code == 400
    assert "error" in resp.json
    assert "incorrect identifier" in resp.json["error"].lower()

    resp = client.get(
            f"/api/{version}/{resource}/abc123@some.org",
            headers=dict(authorization="Bearer TEST"))
    assert resp.status_code == 404
    assert "error" in resp.json
    assert "not found" in resp.json["error"].lower()

    resp = client.get(
            f"/api/{version}/{resource}/0000-0000-0000-0001",
            headers=dict(authorization="Bearer TEST"))
    assert resp.status_code == 404
    assert "error" in resp.json
    assert "not found" in resp.json["error"].lower()

    for identifier in [
            user.email,
            user.orcid,
    ]:
        resp = client.get(
                f"/api/{version}/{resource}/{identifier}",
                headers=dict(authorization="Bearer TEST"))
        assert resp.status_code == 200
        if resource == "users":
            assert resp.json["email"] == user.email
            assert resp.json["eppn"] == user.eppn
            assert resp.json["orcid"] == user.orcid
        else:
            token = OrcidToken.get(user_id=user.id)
            assert resp.json["access_token"] == token.access_token

    if resource == "users":  # test user listing
        resp = client.get(
                f"/api/{version}/{resource}",
                headers=dict(authorization="Bearer TEST"))
        assert resp.status_code == 200
        assert len(resp.json) == 11

        resp = client.get(
                f"/api/{version}/{resource}?page=INVALID&page_size=INVALID",
                headers=dict(authorization="Bearer TEST"))
        assert resp.status_code == 200
        assert len(resp.json) == 11

        resp = client.get(
                f"/api/{version}/{resource}?page=2&page_size=3",
                headers=dict(authorization="Bearer TEST"))
        assert resp.status_code == 200
        assert len(resp.json) == 3

        resp = client.get(
                f"/api/{version}/{resource}?page_size=3",
                headers=dict(authorization="Bearer TEST"))
        assert resp.status_code == 200
        assert len(resp.json) == 3

        resp = client.get(
                f"/api/{version}/{resource}?page=42",
                headers=dict(authorization="Bearer TEST"))
        assert resp.status_code == 200
        assert len(resp.json) == 0

        resp = client.get(
                f"/api/{version}/{resource}?from_date=ABCD",
                headers=dict(authorization="Bearer TEST"))
        assert resp.status_code == 422

        resp = client.get(
                f"/api/{version}/{resource}?from_date=2018-01-01",
                headers=dict(authorization="Bearer TEST"))
        assert resp.status_code == 200
        assert len(resp.json) == 4

        resp = client.get(
                f"/api/{version}/{resource}?to_date=2018-01-01",
                headers=dict(authorization="Bearer TEST"))
        assert resp.status_code == 200
        assert len(resp.json) == 7

        resp = client.get(
                f"/api/{version}/{resource}?from_date=2017-12-20&to_date=2017-12-21",
                headers=dict(authorization="Bearer TEST"))
        assert resp.status_code == 200
        assert len(resp.json) == 2

    if resource == "tokens":
        user2 = User.get(email="researcher2@test0.edu")
        for identifier in [
                user2.email,
                user2.orcid,
        ]:
            resp = client.get(
                    f"/api/{version}/tokens/{identifier}",
                    headers=dict(authorization="Bearer TEST"))
            assert resp.status_code == 404
            assert "error" in resp.json

    resp = client.get(
            f"/api/{version}/{resource}/{org2_user.email}",
            headers=dict(authorization="Bearer TEST"))
    assert resp.status_code == 404
    assert "error" in resp.json


@pytest.mark.parametrize("url", [
    "/spec",
    "/spec.json",
    "/spec.yml",
])
def test_spec(client, url):
    """Test API specs."""
    resp = client.get(url)
    assert resp.status_code == 200


def test_yaml_spec(client):
    """Test API specs (the default entry point with yaml content type)."""
    resp = client.get("/spec", headers={"Accept": "text/yaml"})
    assert resp.status_code == 200


def test_yamlfy(app):
    """Test yamlfy function."""
    from flask import Response
    assert isinstance(yamlfy(1), Response)
    assert isinstance(yamlfy(1, 2, 3), Response)
    assert isinstance(yamlfy(key_arg=42), Response)
    with pytest.raises(TypeError):
        yamlfy(1, 2, 3, key_arg=42)
    # with app.app_context():
    resp = yamlfy(datetime(2018, 7, 10, 16, 26, 25, 86519))
    assert yaml.load(resp.data) == datetime(2018, 7, 10, 16, 26, 25)


def test_api_docs(client):
    """Test API docs."""
    data = client.data
    tech_contact = data["tech_contact"]
    super_user = data["super_user"]
    client.login(tech_contact)
    # assert resp is None
    resp = client.get("/api-docs")
    assert resp.status_code == 200
    assert b"/spec" in resp.data
    assert b"ORCID HUB Data API" not in resp.data
    client.logout()

    client.login(super_user)
    resp = client.get("/api-docs")
    assert resp.status_code == 200
    assert b"/spec" in resp.data
    assert b"ORCID HUB Data API" in resp.data


def test_db_api(client):
    """Test DB API."""
    resp = client.get("/data/api/v0.1/organisations/", headers=dict(authorization="Bearer TEST"))
    assert resp.status_code == 200
    assert "objects" in resp.json
    assert len(resp.json["objects"]) == 4

    resp = client.get("/data/api/v0.1/tasks/", headers=dict(authorization="Bearer TEST"))
    assert resp.status_code == 200
    assert "objects" in resp.json
    assert len(resp.json["objects"]) == 0

    org = Organisation.select().where(Organisation.tuakiri_name.is_null(False)).first()
    resp = client.get(
            f"/data/api/v0.1/organisations/{org.id}",
            headers=dict(authorization="Bearer TEST"))
    assert resp.status_code == 200
    assert resp.json["name"] == org.name
    assert resp.json["tuakiri_name"] == org.tuakiri_name

    org = Organisation.select().where(Organisation.tuakiri_name.is_null(False), Organisation.id != org.id).first()
    resp = client.get(
            f"/data/api/v0.1/organisations/{org.id}",
            headers=dict(authorization="Bearer TEST"))
    assert resp.status_code == 200
    assert resp.json["name"] == org.name
    assert resp.json["tuakiri_name"] == org.tuakiri_name


def test_users_api(client):
    """Test user API."""
    c = Client.get(client_id="TEST0-ID")
    resp = client.post(
        "/oauth/token",
        content_type="application/x-www-form-urlencoded",
        data=f"grant_type=client_credentials&client_id={c.client_id}&client_secret={c.client_secret}")
    data = json.loads(resp.data)
    access_token = data["access_token"]
    resp = client.get(
        "/api/v1.0/users?page=1&page_size=2000",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json")

    data = json.loads(resp.data)
    assert list(data[0].keys()) == ["confirmed", "email", "eppn", "name", "orcid", "updated-at"]
    assert not any(u["email"] == "researcher102@test1.edu" for u in data)

    resp = client.get(
        "/api/v1.0/users?page=1&page_size=2000&from_date=2000-12-01&to_date=1999-01-01",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json")
    data = json.loads(resp.data)
    assert len(data) == 0

    resp = client.get(
        "/api/v1.0/users/researcher102@test1.edu",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json")
    assert resp.status_code == 404
    data = json.loads(resp.data)

    resp = client.get(
        "/api/v1.0/users/researcher102@test0.edu",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["email"] == "researcher102@test0.edu"


def test_affiliation_api(client, mocker):
    """Test affiliation API in various formats."""
    exception = mocker.patch.object(client.application.logger, "exception")
    capture_event = mocker.patch("sentry_sdk.transport.HttpTransport.capture_event")
    resp = client.post(
        "/oauth/token",
        content_type="application/x-www-form-urlencoded",
        data=b"grant_type=client_credentials&client_id=TEST0-ID&client_secret=TEST0-SECRET")
    data = json.loads(resp.data)
    access_token = data["access_token"]
    resp = client.post(
        "/api/v1.0/affiliations/?filename=TEST42.csv",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="text/csv",
        data=b"First Name,Last Name,email,Organisation,Affiliation Type,Role,Department,Start Date,"
        b"End Date,City,State,Country,Disambiguated Id,Disambiguated Source\n"
        b"Researcher,Par,researcher.020@mailinator.com,Royal Org1,Staff,Programme Guide - "
        b"ORCID,Research Funding,2016-09,,Wellington,SATE,NZ,,\n"
        b"Roshan,Pawar,researcher.010@mailinator.com,Royal Org1,Staff,AAA,Research "
        b"Funding,2016-09,,Wellington,SATE,NZ,,\n"
        b"Roshan,Pawar,researcher.010@mailinator.com,Royal Org1,Student,BBB,Research "
        b"Funding,2016-09,,Wellington,SATE,New Zealand,,")
    data = json.loads(resp.data)
    assert data["filename"] == "TEST42.csv"
    assert data["task-type"] == "AFFILIATION"
    assert len(data["records"]) == 3
    task_id = data["id"]

    resp = client.get("/api/v1.0/tasks", headers=dict(authorization=f"Bearer {access_token}"))
    tasks = json.loads(resp.data)
    assert tasks[0]["id"] == task_id

    resp = client.get(
        "/api/v1.0/tasks?type=AFFILIATION", headers=dict(authorization=f"Bearer {access_token}"))
    tasks = json.loads(resp.data)
    assert tasks[0]["id"] == task_id

    resp = client.get(
        "/api/v1.0/tasks?type=AFFILIATION&page=1&page_size=20",
        headers=dict(authorization=f"Bearer {access_token}"))
    tasks = json.loads(resp.data)
    assert tasks[0]["id"] == task_id

    task_copy = copy.deepcopy(data)
    del(task_copy["id"])
    task_copy["filename"] = "TASK-COPY.csv"
    resp = client.post(
        "/api/v1.0/affiliations/",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(task_copy))
    assert Task.select().count() == 2

    for r in data["records"]:
        del(r["id"])
        r["city"] = "TEST000"
    resp = client.post(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(data))
    data = json.loads(resp.data)
    assert len(resp.json["records"]) == 3
    # should get a new set of records

    del(data["records"][2])
    resp = client.post(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(data))
    assert len(resp.json["records"]) == 2

    incorrect_data = copy.deepcopy(data)
    incorrect_data["records"].insert(0, {
        "first-name": "TEST000 FN",
        "last-name": "TEST000 LN",
    })
    resp = client.post(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(incorrect_data))
    assert resp.status_code == 422
    assert resp.json["error"] == "Validation error."

    resp = client.get(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    incorrect_data = copy.deepcopy(resp.json)
    incorrect_data["records"].insert(0, {
        "email": "test1234@test.edu",
        "first-name": "TEST000 FN",
        "last-name": "TEST000 LN",
    })
    resp = client.post(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(incorrect_data))
    assert resp.status_code == 422
    assert resp.json["error"] == "Validation error."

    resp = client.get(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    new_data = copy.deepcopy(resp.json)
    new_data["records"].insert(0, {
        "email": "test1234@test.edu",
        "first-name": "TEST000 FN",
        "last-name": "TEST000 LN",
        "affiliation-type": "staff",
        "city": "TEST000"
    })
    resp = client.post(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(new_data))
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert len(data["records"]) == 3

    resp = client.put(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(data))
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert len(resp.json["records"]) == 3

    resp = client.get(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    new_data = copy.deepcopy(resp.json)
    for i, r in enumerate(new_data["records"]):
        new_data["records"][i] = {"id": r["id"], "is-active": True}
    resp = client.patch(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(new_data))
    assert resp.status_code == 200
    assert len(resp.json["records"]) == 3
    assert all(r["is-active"] for r in resp.json["records"])
    assert all(r["city"] == "TEST000" for r in resp.json["records"])

    resp = client.head(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert "Last-Modified" in resp.headers

    resp = client.head(
        "/api/v1.0/affiliations/999999999",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 404

    resp = client.get(
        "/api/v1.0/affiliations/999999999",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 404

    resp = client.patch(
        "/api/v1.0/affiliations/999999999",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(new_data))
    assert resp.status_code == 404

    with patch.object(Task, "get", side_effect=Exception("ERROR")):
        resp = client.delete(
            f"/api/v1.0/affiliations/{task_id}",
            headers=dict(authorization=f"Bearer {access_token}"))
        assert resp.status_code == 400
        assert resp.json == {"error": "Unhandled exception occurred.", "exception": "ERROR"}

    resp = client.delete(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert Task.select().count() == 1

    resp = client.delete(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 404

    other_user = User.get(email="admin@test1.edu")
    other_task = Task.create(
        created_by=other_user,
        org=other_user.organisation,
        filename="OTHER.csv",
        task_type=TaskType.AFFILIATION)

    resp = client.head(
        f"/api/v1.0/affiliations/{other_task.id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 403

    resp = client.get(
        f"/api/v1.0/affiliations/{other_task.id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 403

    resp = client.patch(
        f"/api/v1.0/affiliations/{other_task.id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(new_data))
    assert resp.status_code == 403

    resp = client.delete(
        f"/api/v1.0/affiliations/{other_task.id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 403

    resp = client.patch(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=b'')
    assert resp.status_code == 400

    resp = client.post(
        "/api/v1.0/affiliations/?filename=TEST42.csv",
        headers=dict(authorization=f"Bearer {access_token}", accept="text/yaml"),
        content_type="text/yaml",
        data="""task-type: AFFILIATION
filename: TEST42.yml
records:
- affiliation-type: student
  city: Wellington
  country: NZ
  department: Research Funding
  email: researcher.010@mailinator.com
  first-name: Roshan
  last-name: Pawar
  organisation: Royal Org1
  role: BBB
  start-date: 2016-09
- affiliation-type: staff
  city: Wellington
  country: NZ
  department: Research Funding
  email: researcher.010@mailinator.com
  first-name: Roshan
  last-name: Pawar
  organisation: Royal Org1
  role: AAA
  start-date: 2016-09
- affiliation-type: staff
  city: Wellington
  country: NZ
  department: Research Funding
  email: researcher.020@mailinator.com
  first-name: Researcher
  is-active: false
  last-name: Par
  organisation: Royal Org1
  role: Programme Guide - ORCID
  start-date: 2016-09
""")
    assert resp.json["filename"] == "TEST42.yml"
    assert resp.json["task-type"] == "AFFILIATION"
    assert len(resp.json["records"]) == 3
    task_id = resp.json["id"]
    task = Task.get(id=task_id)
    assert task.affiliation_records.count() == 3

    resp = client.put(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}", accept="text/yaml"),
        content_type="text/yaml",
        data="""task-type: AFFILIATION
filename: TEST42.yml
records:
- affiliation-type: student
  id: 9999999999
  city: Wellington
  country: NZ
  department: Research Funding
  email: researcher.010@mailinator.com
  first-name: Roshan
  last-name: Pawar
  organisation: Royal Org1
  role: BBB
  start-date: 2016-09
""")
    assert resp.status_code == 400
    assert resp.json["error"] == "Unhandled exception occurred."
    assert "Instance matching query does not exist" in resp.json["exception"]

    with patch.object(AffiliationRecord, "get", side_effect=Exception("ERROR")):
        resp = client.put(
            f"/api/v1.0/affiliations/{task_id}",
            headers=dict(authorization=f"Bearer {access_token}", accept="text/yaml"),
            content_type="text/yaml",
            data="""task-type: AFFILIATION
filename: TEST42.yml
records:
- affiliation-type: student
  id: 9999999999
  city: Wellington
  country: NZ
  department: Research Funding
  email: researcher.010@mailinator.com
  first-name: Roshan
  last-name: Pawar
  organisation: Royal Org1
  role: BBB
  start-date: 2016-09
""")
        assert resp.status_code == 400
        assert resp.json == {"error": "Unhandled exception occurred.", "exception": "ERROR"}

    resp = client.post(
        f"/api/v1.0/affiliations/?filename=TEST42.csv",
        headers=dict(authorization=f"Bearer {access_token}", accept="text/yaml"),
        content_type="text/yaml",
        data="""task-type: INCORRECT
filename: TEST42.yml
records:
- affiliation-type: student
  id: 9999999999
""")
    assert resp.status_code == 422
    assert resp.json["error"] == "Validation error."
    assert "INCORRECT" in resp.json["message"]

    resp = client.post(
        "/api/v1.0/affiliations/?filename=TEST_ERROR.csv",
        headers=dict(authorization=f"Bearer {access_token}", accept="text/yaml"),
        content_type="text/yaml",
        data="""task-type: AFFILIATION
filename: TEST_ERROR.yml
records:
- affiliation-type: student
something fishy is going here...
""")
    assert resp.status_code == 415
    assert resp.json["error"] == "Invalid request format. Only JSON, CSV, or TSV are acceptable."
    assert "something fishy is going here..." in resp.json["message"]
    exception.assert_called()
    capture_event.assert_called()


def test_funding_api(client):
    """Test funding API in various formats."""
    admin = client.data.get("admin")
    resp = client.login(admin, follow_redirects=True)
    resp = client.post(
        "/load/researcher/funding",
        data={
            "file_": (
                BytesIO(
                    """Put Code,Title,Translated Title,Translated Title Language Code,Type,Organization Defined Type,Short Description,Amount,Currency,Start Date,End Date,Org Name,City,Region,Country,Disambiguated Org Identifier,Disambiguation Source,Visibility,ORCID iD,Email,First Name,Last Name,Name,Role,External Id Type,External Id Value,External Id Url,External Id Relationship,Identifier
,This is the project title,,,CONTRACT,Fast-Start,This is the project abstract,300000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,0000-0002-9207-4933,,,,Associate Professor A Contributor 1,lead,grant_number,XXX1701,,SELF,
,This is the project title,,,CONTRACT,Fast-Start,This is the project abstract,300000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,,,,Dr B Contributor 2,co_lead,grant_number,XXX1701,,SELF,
,This is the project title,,,CONTRACT,Fast-Start,This is the project abstract,300000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,,,,Dr E Contributor 3,,grant_number,XXX1701,,SELF,
,This is the project title,,,CONTRACT,Fast-Start,This is the project abstract,300000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,contributor@test.eud,FN,LN,Dr E Contributor 4,,grant_number,XXX1701,,SELF,
,This is another project title,,,CONTRACT,Standard,This is another project abstract,800000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,contributor4@mailinator.com,,,Associate Professor F Contributor 4,lead,grant_number,XXX1702,,SELF,9999
,This is another project title,,,CONTRACT,Standard,This is another project abstract,800000,NZD,2018,2021,Marsden Fund,Wellington,,NZ,http://dx.doi.org/10.13039/501100009193,FUNDREF,,,contributor5@mailinator.com,John,Doe,,co_lead,grant_number,XXX1702,,SELF,8888 """.encode()  # noqa: E501
                ),  # noqa: E501
                "fundings042.csv",
            ),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert Task.select().count() == 1

    # TODO: factor it out
    resp = client.post(
        "/oauth/token",
        content_type="application/x-www-form-urlencoded",
        data=b"grant_type=client_credentials&client_id=CLIENT_ID&client_secret=CLIENT_SECRET")
    data = json.loads(resp.data)
    access_token = data["access_token"]

    resp = client.get(
        "/api/v1.0/tasks?type=FUNDING",
        headers=dict(authorization=f"Bearer {access_token}"))
    data = json.loads(resp.data)
    task_id = int(data[0]["id"])

    resp = client.get(
        f"/api/v1.0/funds/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    data = json.loads(resp.data)
    assert len(data["records"]) == 2
    assert data["filename"] == "fundings042.csv"

    resp = client.post(
        "/api/v1.0/funds/?filename=fundings333.json",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(data))
    assert resp.status_code == 200
    assert Task.select().count() == 2

    records = data["records"]
    resp = client.post(
        "/api/v1.0/funds/?filename=fundings444.json",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(records))
    assert resp.status_code == 200
    assert Task.select().count() == 3

    resp = client.post(
        f"/api/v1.0/funds/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(records))
    assert resp.status_code == 200
    assert Task.select().count() == 3

    resp = client.head(
        f"/api/v1.0/funds/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert "Last-Modified" in resp.headers
    assert resp.status_code == 200

    resp = client.delete(
        f"/api/v1.0/funds/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 200
    assert Task.select().count() == 2

    resp = client.head(
        f"/api/v1.0/funds/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 404


def test_work_api(client):
    """Test work API in various formats."""
    admin = client.data.get("admin")
    resp = client.login(admin, follow_redirects=True)
    resp = client.post(
        "/load/researcher/work",
        data={
            "file_": (open(os.path.join(os.path.dirname(__file__), "data", "example_works.json"), "rb"),
                      "works042.json"),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert Task.select().count() == 1

    access_token = client.get_access_token()

    resp = client.get(
        "/api/v1.0/tasks?type=work",
        headers=dict(authorization=f"Bearer {access_token}"))
    data = json.loads(resp.data)
    task_id = int(data[0]["id"])

    resp = client.get(
        f"/api/v1.0/works/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    data = json.loads(resp.data)
    assert len(data["records"]) == 1
    assert data["filename"] == "works042.json"

    del(data["id"])
    resp = client.post(
        "/api/v1.0/works/?filename=works333.json",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(data))
    assert resp.status_code == 200
    assert Task.select().count() == 2

    records = data["records"]
    resp = client.post(
        "/api/v1.0/works/?filename=works444.json",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(records))
    assert resp.status_code == 200
    assert Task.select().count() == 3

    resp = client.post(
        f"/api/v1.0/works/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(records))
    assert resp.status_code == 200
    assert Task.select().count() == 3

    resp = client.head(
        f"/api/v1.0/works/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert "Last-Modified" in resp.headers
    assert resp.status_code == 200

    resp = client.delete(
        f"/api/v1.0/works/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 200
    assert Task.select().count() == 2

    resp = client.head(
        f"/api/v1.0/works/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 404


def test_peer_review_api(client):
    """Test peer review API in various formats."""
    admin = client.data.get("admin")
    resp = client.login(admin, follow_redirects=True)
    resp = client.post(
        "/load/researcher/peer_review",
        data={
            "file_": (open(
                os.path.join(os.path.dirname(__file__), "data", "example_peer_reviews.json"),
                "rb"), "peer-reviews042.json"),
        },
        follow_redirects=True)
    assert resp.status_code == 200
    assert Task.select().count() == 1

    access_token = client.get_access_token()

    resp = client.get(
        "/api/v1.0/tasks?type=PEER_REVIEW",
        headers=dict(authorization=f"Bearer {access_token}"))
    data = json.loads(resp.data)
    task_id = int(data[0]["id"])

    resp = client.get(
        f"/api/v1.0/peer-reviews/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    data = json.loads(resp.data)
    assert len(data["records"]) == 1
    assert data["filename"] == "peer-reviews042.json"

    del(data["id"])
    resp = client.post(
        "/api/v1.0/peer-reviews/?filename=peer_reviews333.json",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(data))
    assert resp.status_code == 200
    assert Task.select().count() == 2

    records = data["records"]
    resp = client.post(
        "/api/v1.0/peer-reviews/?filename=peer_reviews444.json",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(records))
    assert resp.status_code == 200
    assert Task.select().count() == 3

    resp = client.post(
        "/api/v1.0/peer-reviews",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(records))
    assert resp.status_code == 200
    assert Task.select().count() == 4

    resp = client.post(
        f"/api/v1.0/peer-reviews/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(records))
    assert resp.status_code == 200
    assert Task.select().count() == 4

    resp = client.head(
        f"/api/v1.0/peer-reviews/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert "Last-Modified" in resp.headers
    assert resp.status_code == 200

    resp = client.delete(
        f"/api/v1.0/peer-reviews/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 200
    assert Task.select().count() == 3

    resp = client.head(
        f"/api/v1.0/peer-reviews/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 404


def test_proxy_get_profile(client):
    """Test the echo endpoint."""
    user = User.get(email="app123@test0.edu")
    token = Token.get(user=user)
    orcid_id = "0000-0000-0000-00X3"

    with patch("orcid_hub.apis.requests.Session.send") as mocksend:
        mockresp = MagicMock(status_code=200)
        mockresp.raw.stream = lambda *args, **kwargs: iter([b"""{"data": "TEST"}"""])
        mockresp.raw.headers = {
            "Server": "TEST123",
            "Content-Type": "application/json;charset=UTF-8",
            "Transfer-Encoding": "chunked",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no -cache, no-store, max-age=0, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        mocksend.return_value = mockresp
        resp = client.get(
            f"/orcid/api/v2.23/{orcid_id}",
            headers=dict(authorization=f"Bearer {token.access_token}"))
        assert resp.status_code == 200
        args, kwargs = mocksend.call_args
        assert kwargs["stream"]
        assert args[0].url == f"https://api.sandbox.orcid.org/v2.23/{orcid_id}"
        assert args[0].headers["Authorization"] == "Bearer ORCID-TEST-ACCESS-TOKEN"
        assert resp.json == {"data": "TEST"}

    with patch("orcid_hub.apis.requests.Session.send") as mocksend:
        mockresp = MagicMock(status_code=201)
        mockresp.raw.stream = lambda *args, **kwargs: iter([b"""{"data": "TEST"}"""])
        mockresp.raw.headers = {
            "Server": "TEST123",
            "Content-Type": "application/json;charset=UTF-8",
            "Transfer-Encoding": "chunked",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no -cache, no-store, max-age=0, must-revalidate",
            "Pragma": "no-cache",
            "Loction": "TEST-LOCATION",
            "Expires": "0",
        }
        mocksend.return_value = mockresp
        resp = client.post(
            f"/orcid/api/v2.23/{orcid_id}/SOMETHING-MORE",
            headers=dict(authorization=f"Bearer {token.access_token}"),
            data=b"""{"data": "REQUEST"}""")
        assert resp.status_code == 201
        args, kwargs = mocksend.call_args
        assert kwargs["stream"]
        assert args[0].url == f"https://api.sandbox.orcid.org/v2.23/{orcid_id}/SOMETHING-MORE"
        assert args[0].headers["Authorization"] == "Bearer ORCID-TEST-ACCESS-TOKEN"
        assert resp.json == {"data": "TEST"}

    # malformatted ORCID ID:
    resp = client.get(
        "/orcid/api/v2.23/NOT-ORCID-ID/PATH",
        headers=dict(authorization=f"Bearer {token.access_token}"))
    assert resp.status_code == 415

    # wrong version number:
    resp = client.get(
        f"/orcid/api/v1.23_ERROR/{orcid_id}/PATH",
        headers=dict(authorization=f"Bearer {token.access_token}"))
    assert resp.status_code == 404
    assert resp.json == {
        "error": "Resource not found",
        "message": "Incorrect version: v1.23_ERROR"
    }

    # no ORCID access token
    resp = client.get(
        "/orcid/api/v2.23/0000-0000-0000-11X2/PATH",
        headers=dict(authorization=f"Bearer {token.access_token}"))
    assert resp.status_code == 403
