# -*- coding: utf-8 -*-
"""Tests for core functions."""

import copy
import json
import yaml
from datetime import datetime

import pytest
from flask import url_for
from flask_login import login_user

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


def test_get_oauth_access_token(request_ctx):
    """Test the acquisition of OAuth access token."""
    with request_ctx(
            "/oauth/token",
            method="POST",
            data=dict(
                grant_type="client_credentials",
                client_id="CLIENT_ID",
                client_secret="CLIENT_SECRET")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        client = Client.get(client_id="CLIENT_ID")
        token = Token.get(client=client)
        assert data["access_token"] == token.access_token
        assert data["expires_in"] == ctx.app.config["OAUTH2_PROVIDER_TOKEN_EXPIRES_IN"]
        assert data["token_type"] == token.token_type
        # prevously created access token should be removed
        assert not Token.select().where(Token.access_token == "TEST").exists()

    with request_ctx(
            "/oauth/token",
            method="POST",
            data=dict(
                grant_type="client_credentials",
                client_id="NOT-EXISTING-CLIENT_ID",
                client_secret="CLIENT_SECRET")) as ctx:
        # login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 401
        data = json.loads(rv.data)
        assert data["error"] == "invalid_client"

    with request_ctx(
            "/oauth/token",
            method="POST",
            data=dict(
                grant_type="client_credentials",
                client_id="CLIENT_ID",
                client_secret="INCORRECT")) as ctx:
        # login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 401
        data = json.loads(rv.data)
        assert data["error"] == "invalid_client"

    with request_ctx(
            "/oauth/token",
            method="POST",
            data=dict(
                grant_type="INCORRECT",
                client_id="NOT-EXISTING-CLIENT_ID",
                client_secret="CLIENT_SECRET")) as ctx:
        # login_user(user, remember=True)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert data["error"] == "unsupported_grant_type"


# def test_revoke_access_token(request_ctx):
#     """Test the acquisition of OAuth access token."""
#     with request_ctx(
#             "/oauth/token",
#             method="POST",
#             data=dict(
#                 grant_type="client_credentials",
#                 client_id="CLIENT_ID",
#                 client_secret="CLIENT_SECRET")) as ctx:
#         rv = ctx.app.full_dispatch_request()
#         assert rv.status_code == 200
#         data = json.loads(rv.data)
#         client = Client.get(client_id="CLIENT_ID")
#         token = Token.get(client=client)
#         assert data["access_token"] == token.access_token

#     with request_ctx(
#             "/oauth/token",
#             method="POST",
#             data=dict(
#                 grant_type="client_credentials",
#                 client_id="CLIENT_ID",
#                 client_secret="CLIENT_SECRET")) as ctx:
#         rv = ctx.app.full_dispatch_request()
#         assert rv.status_code == 200
#         data = json.loads(rv.data)


def test_me(request_ctx):
    """Test the echo endpoint."""
    user = User.get(email="app123@test0.edu")
    token = Token.get(user=user)
    with request_ctx("/api/me", headers=dict(authorization=f"Bearer {token.access_token}")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data["email"] == user.email
        assert data["name"] == user.name

    # Test invalid token:
    with request_ctx("/api/me", headers=dict(authorization="Bearer INVALID")) as ctx:
        user = User.get(email="app123@test0.edu")
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 401

    # Test expired token:
    token.expires = datetime(1971, 1, 1)
    token.save()
    with request_ctx("/api/me", headers=dict(authorization=f"Bearer {token.access_token}")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 401


@pytest.mark.parametrize("resource", [
    "users",
    "tokens",
])
@pytest.mark.parametrize("version", [
    "v1.0",
])
def test_user_and_token_api(request_ctx, resource, version):
    """Test the echo endpoint."""
    user = User.get(email="researcher@test0.edu")
    org2_user = User.get(email="researcher@org2.edu")
    with request_ctx(
            f"/api/{version}/{resource}/ABC123", headers=dict(authorization="Bearer TEST")) as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "error" in data
        assert "incorrect identifier" in data["error"].lower()
    with request_ctx(
            f"/api/{version}/{resource}/0000-0000-0000-0000",
            headers=dict(authorization="Bearer TEST")) as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "error" in data
        assert "incorrect identifier" in data["error"].lower()
    with request_ctx(
            f"/api/{version}/{resource}/abc123@some.org",
            headers=dict(authorization="Bearer TEST")) as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert "error" in data
        assert "not found" in data["error"].lower()
    with request_ctx(
            f"/api/{version}/{resource}/0000-0000-0000-0001",
            headers=dict(authorization="Bearer TEST")) as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert "error" in data
        assert "not found" in data["error"].lower()
    for identifier in [
            user.email,
            user.orcid,
    ]:
        with request_ctx(
                f"/api/{version}/{resource}/{identifier}",
                headers=dict(authorization="Bearer TEST")) as ctx:
            resp = ctx.app.full_dispatch_request()
            data = json.loads(resp.data)
            assert resp.status_code == 200
            data = json.loads(resp.data)
            if resource == "users":
                assert data["email"] == user.email
                assert data["eppn"] == user.eppn
                assert data["orcid"] == user.orcid
            else:
                token = OrcidToken.get(user_id=user.id)
                assert data["access_token"] == token.access_token
    if resource == "users":  # test user listing
        with request_ctx(
                f"/api/{version}/{resource}",
                headers=dict(authorization="Bearer TEST")) as ctx:
            resp = ctx.app.full_dispatch_request()
            data = json.loads(resp.data)
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert len(data) == 11
        with request_ctx(
                f"/api/{version}/{resource}?page=INVALID&page_size=INVALID",
                headers=dict(authorization="Bearer TEST")) as ctx:
            resp = ctx.app.full_dispatch_request()
            data = json.loads(resp.data)
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert len(data) == 11
        with request_ctx(
                f"/api/{version}/{resource}?page=2&page_size=3",
                headers=dict(authorization="Bearer TEST")) as ctx:
            resp = ctx.app.full_dispatch_request()
            data = json.loads(resp.data)
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert len(data) == 3
        with request_ctx(
                f"/api/{version}/{resource}?page_size=3",
                headers=dict(authorization="Bearer TEST")) as ctx:
            resp = ctx.app.full_dispatch_request()
            data = json.loads(resp.data)
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert len(data) == 3
        with request_ctx(
                f"/api/{version}/{resource}?page=42",
                headers=dict(authorization="Bearer TEST")) as ctx:
            resp = ctx.app.full_dispatch_request()
            data = json.loads(resp.data)
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert len(data) == 0
        with request_ctx(
                f"/api/{version}/{resource}?from_date=ABCD",
                headers=dict(authorization="Bearer TEST")) as ctx:
            resp = ctx.app.full_dispatch_request()
            data = json.loads(resp.data)
            assert resp.status_code == 422
        with request_ctx(
                f"/api/{version}/{resource}?from_date=2018-01-01",
                headers=dict(authorization="Bearer TEST")) as ctx:
            resp = ctx.app.full_dispatch_request()
            data = json.loads(resp.data)
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert len(data) == 4
        with request_ctx(
                f"/api/{version}/{resource}?to_date=2018-01-01",
                headers=dict(authorization="Bearer TEST")) as ctx:
            resp = ctx.app.full_dispatch_request()
            data = json.loads(resp.data)
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert len(data) == 7
        with request_ctx(
                f"/api/{version}/{resource}?from_date=2017-12-20&to_date=2017-12-21",
                headers=dict(authorization="Bearer TEST")) as ctx:
            resp = ctx.app.full_dispatch_request()
            data = json.loads(resp.data)
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert len(data) == 2

    if resource == "tokens":
        user2 = User.get(email="researcher2@test0.edu")
        for identifier in [
                user2.email,
                user2.orcid,
        ]:
            with request_ctx(
                    f"/api/{version}/tokens/{identifier}",
                    headers=dict(authorization="Bearer TEST")) as ctx:
                resp = ctx.app.full_dispatch_request()
                assert resp.status_code == 404
                data = json.loads(resp.data)
                assert "error" in data

    with request_ctx(
            f"/api/{version}/{resource}/{org2_user.email}",
            headers=dict(authorization="Bearer TEST")) as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 404
        data = json.loads(resp.data)
        assert "error" in data


@pytest.mark.parametrize("url", [
    "/spec",
    "/spec.json",
    "/spec.yml",
])
def test_spec(client, url):
    """Test API specs."""
    rv = client.get(url)
    assert rv.status_code == 200


def test_yaml_spec(client):
    """Test API specs (the default entry point with yaml content type)."""
    rv = client.get("/spec", headers={"Accept": "text/yaml"})
    assert rv.status_code == 200


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


def test_api_docs(request_ctx):
    """Test API docs."""
    data = request_ctx.data
    tech_contact = data["tech_contact"]
    super_user = data["super_user"]
    with request_ctx("/api-docs") as ctx:
        spec_url = url_for("spec", _external=True)
        data_api_spec_url = url_for("Swagger.model_resources", _external=True)
        login_user(tech_contact)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert spec_url.encode("utf-8") in rv.data
        assert data_api_spec_url.encode("utf-8") not in rv.data

    with request_ctx("/api-docs") as ctx:
        login_user(super_user)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert spec_url.encode("utf-8") in rv.data
        assert data_api_spec_url.encode("utf-8") in rv.data


def test_db_api(request_ctx):
    """Test DB API."""
    with request_ctx(
            "/data/api/v0.1/organisations/", headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert "objects" in data
        assert len(data["objects"]) == 5

    with request_ctx("/data/api/v0.1/tasks/", headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert "objects" in data
        assert len(data["objects"]) == 0

    org = Organisation.get(id=1)
    with request_ctx(
            f"/data/api/v0.1/organisations/{org.id}",
            headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data["name"] == org.name
        assert data["tuakiri_name"] == org.tuakiri_name

    org = Organisation.get(id=2)
    with request_ctx(
            f"/data/api/v0.1/organisations/{org.id}",
            headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data["name"] == org.name
        assert data["tuakiri_name"] == org.tuakiri_name


def test_affiliation_api(client):
    """Test affiliation API in various formats."""
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
    assert len(data["records"]) == 3
    # should get a new set of records

    del(data["records"][2])
    resp = client.post(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(data))
    new_data = json.loads(resp.data)
    assert len(new_data["records"]) == 2

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
    data = json.loads(resp.data)
    assert resp.status_code == 422
    assert data["error"] == "Validation error."

    resp = client.get(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    data = json.loads(resp.data)
    incorrect_data = copy.deepcopy(data)
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
    data = json.loads(resp.data)
    assert resp.status_code == 422
    assert data["error"] == "Validation error."

    resp = client.get(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    data = json.loads(resp.data)
    new_data = copy.deepcopy(data)
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
    assert len(data["records"]) == 3

    resp = client.get(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    data = json.loads(resp.data)
    new_data = copy.deepcopy(data)
    for i, r in enumerate(new_data["records"]):
        new_data["records"][i] = {"id": r["id"], "is-active": True}
    resp = client.patch(
        f"/api/v1.0/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(new_data))
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert len(data["records"]) == 3
    assert all(r["is-active"] for r in data["records"])
    assert all(r["city"] == "TEST000" for r in data["records"])

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
        assert resp.get_json() == {"error": "Unhandled except occured.", "exception": "ERROR"}

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
    data = json.loads(resp.data)
    assert data["filename"] == "TEST42.yml"
    assert data["task-type"] == "AFFILIATION"
    assert len(data["records"]) == 3
    task_id = data["id"]
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
    data = resp.get_json()
    assert resp.status_code == 400
    assert data["error"] == "Unhandled except occured."
    assert "Instance matching query does not exist" in data["exception"]

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
        data = resp.get_json()
        assert resp.status_code == 400
        assert data == {"error": "Unhandled except occured.", "exception": "ERROR"}

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
    data = resp.get_json()
    assert data["error"] == "Validation error."
    assert "INCORRECT" in data["message"]

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
    data = resp.get_json()
    assert data["error"] == "Ivalid request format. Only JSON, CSV, or TSV are acceptable."
    assert "something fishy is going here..." in data["message"]


def test_proxy_get_profile(request_ctx):
    """Test the echo endpoint."""
    user = User.get(email="app123@test0.edu")
    token = Token.get(user=user)
    orcid_id = "0000-0000-0000-00X3"

    with request_ctx(
            f"/orcid/api/v2.23/{orcid_id}", headers=dict(
                authorization=f"Bearer {token.access_token}")) as ctx, patch(
                        "orcid_hub.apis.requests.Session.send") as mocksend:
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 200
        args, kwargs = mocksend.call_args
        assert kwargs["stream"]
        assert args[0].url == f"https://api.sandbox.orcid.org/v2.23/{orcid_id}"
        assert args[0].headers["Authorization"] == "Bearer ORCID-TEST-ACCESS-TOKEN"

        data = json.loads(resp.data)
        assert data == {"data": "TEST"}

    with request_ctx(
            f"/orcid/api/v2.23/{orcid_id}/SOMETHING-MORE", headers=dict(
                authorization=f"Bearer {token.access_token}"), method="POST",
            data=b"""{"data": "REQUEST"}""") as ctx, patch(
                        "orcid_hub.apis.requests.Session.send") as mocksend:
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
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 201
        args, kwargs = mocksend.call_args
        assert kwargs["stream"]
        assert args[0].url == f"https://api.sandbox.orcid.org/v2.23/{orcid_id}/SOMETHING-MORE"
        assert args[0].headers["Authorization"] == "Bearer ORCID-TEST-ACCESS-TOKEN"

        data = json.loads(resp.data)
        assert data == {"data": "TEST"}

    # malformatted ORCID ID:
    with request_ctx(
            "/orcid/api/v2.23/NOT-ORCID-ID/PATH",
            headers=dict(authorization=f"Bearer {token.access_token}")) as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 415

    # wrong version number:
    with request_ctx(
            f"/orcid/api/v1.23_ERROR/{orcid_id}/PATH", headers=dict(
                authorization=f"Bearer {token.access_token}")) as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 404
        assert resp.get_json() == {
            "error": "Resource not found",
            "message": "Incorrect version: v1.23_ERROR"
        }

    # no ORCID access token
    with request_ctx(
            "/orcid/api/v2.23/0000-0000-0000-11X2/PATH", headers=dict(
                authorization=f"Bearer {token.access_token}")) as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 403
