# -*- coding: utf-8 -*-
"""Tests for core functions."""

import copy
import json

import pytest
from flask import url_for
from flask_login import login_user

from orcid_hub.apis import yamlfy
from orcid_hub.models import Client, OrcidToken, Organisation, Role, Task, TaskType, Token, User, UserOrg

from unittest.mock import patch, MagicMock


@pytest.fixture
def app_req_ctx(request_ctx):
    """Create the fixture for the reques with a test organisation and a test tech.contatct."""
    org = Organisation.create(
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        orcid_client_id="APP-12345678",
        orcid_secret="CLIENT-SECRET",
        confirmed=True,
        city="CITY",
        country="COUNTRY")

    admin = User.create(
        email="app123@test0.edu",
        name="TEST USER WITH AN APP",
        roles=Role.TECHNICAL,
        orcid="1001-0001-0001-0001",
        confirmed=True,
        organisation=org)

    UserOrg.create(user=admin, org=org, is_admin=True)
    org.tech_contact = admin
    org.save()

    client = Client.create(
        name="TEST_CLIENT",
        user=admin,
        org=org,
        client_id="CLIENT_ID",
        client_secret="CLIENT_SECRET",
        is_confidential="public",
        grant_type="client_credentials",
        response_type="XYZ")

    Token.create(client=client, user=admin, access_token="TEST", token_type="Bearer")

    user = User.create(
        email="researcher@test0.edu",
        eppn="eppn@test0.edu",
        name="TEST REASEARCHER",
        orcid="0000-0000-0000-00X3",
        confirmed=True,
        organisation=org)

    OrcidToken.create(user=user, org=org, access_token="ORCID-TEST-ACCESS-TOKEN")

    User.create(
        email="researcher2@test0.edu",
        eppn="eppn2@test0.edu",
        name="TEST REASEARCHER W/O ORCID ACCESS TOKEN",
        orcid="0000-0000-0000-11X2",
        confirmed=True,
        organisation=org)

    org2 = Organisation.create(
        name="THE ORGANISATION #2",
        tuakiri_name="THE ORGANISATION #2",
        confirmed=True,
        city="CITY")
    User.create(
        email="researcher@org2.edu",
        eppn="eppn123@org2.edu",
        name="TEST REASEARCHER #2",
        orcid="9999-9999-9999-9999",
        confirmed=True,
        organisation=org2)

    return request_ctx


def test_get_oauth_access_token(app_req_ctx):
    """Test the acquisition of OAuth access token."""
    with app_req_ctx(
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

    with app_req_ctx(
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

    with app_req_ctx(
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

    with app_req_ctx(
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


# def test_revoke_access_token(app_req_ctx):
#     """Test the acquisition of OAuth access token."""
#     with app_req_ctx(
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

#     with app_req_ctx(
#             "/oauth/token",
#             method="POST",
#             data=dict(
#                 grant_type="client_credentials",
#                 client_id="CLIENT_ID",
#                 client_secret="CLIENT_SECRET")) as ctx:
#         rv = ctx.app.full_dispatch_request()
#         assert rv.status_code == 200
#         data = json.loads(rv.data)


def test_me(app_req_ctx):
    """Test the echo endpoint."""
    user = User.get(email="app123@test0.edu")
    token = Token.get(user=user)
    with app_req_ctx("/api/me", headers=dict(authorization=f"Bearer {token.access_token}")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data["email"] == user.email
        assert data["name"] == user.name

    # Test invalid token:
    with app_req_ctx("/api/me", headers=dict(authorization="Bearer INVALID")) as ctx:
        user = User.get(email="app123@test0.edu")
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 401

    # Test expired token:
    from datetime import datetime
    token.expires = datetime(1971, 1, 1)
    token.save()
    with app_req_ctx("/api/me", headers=dict(authorization=f"Bearer {token.access_token}")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 401


@pytest.mark.parametrize("resource", [
    "users",
    "tokens",
])
@pytest.mark.parametrize("version", [
    "v0.1",
])
def test_user_and_token_api(app_req_ctx, resource, version):
    """Test the echo endpoint."""
    user = User.get(email="researcher@test0.edu")
    org2_user = User.get(email="researcher@org2.edu")
    with app_req_ctx(
            f"/api/{version}/{resource}/ABC123", headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert "error" in data
        assert "incorrect identifier" in data["error"].lower()
    with app_req_ctx(
            f"/api/{version}/{resource}/0000-0000-0000-0000",
            headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert "error" in data
        assert "incorrect identifier" in data["error"].lower()
    with app_req_ctx(
            f"/api/{version}/{resource}/abc123@some.org",
            headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 404
        data = json.loads(rv.data)
        assert "error" in data
        assert "not found" in data["error"].lower()
    with app_req_ctx(
            f"/api/{version}/{resource}/0000-0000-0000-0001",
            headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 404
        data = json.loads(rv.data)
        assert "error" in data
        assert "not found" in data["error"].lower()
    for identifier in [
            user.email,
            user.orcid,
    ]:
        with app_req_ctx(
                f"/api/{version}/{resource}/{identifier}",
                headers=dict(authorization="Bearer TEST")) as ctx:
            rv = ctx.app.full_dispatch_request()
            data = json.loads(rv.data)
            assert rv.status_code == 200
            data = json.loads(rv.data)
            assert data["found"]
            if resource == "users":
                result = data["result"]
                assert result["email"] == user.email
                assert result["eppn"] == user.eppn
                assert result["orcid"] == user.orcid
            else:
                token = OrcidToken.get(user_id=user.id)
                assert data["token"]["access_token"] == token.access_token

    if resource == "tokens":
        user2 = User.get(email="researcher2@test0.edu")
        for identifier in [
                user2.email,
                user2.orcid,
        ]:
            with app_req_ctx(
                    f"/api/{version}/tokens/{identifier}",
                    headers=dict(authorization="Bearer TEST")) as ctx:
                rv = ctx.app.full_dispatch_request()
                assert rv.status_code == 404
                data = json.loads(rv.data)
                assert "error" in data

    with app_req_ctx(
            f"/api/{version}/{resource}/{org2_user.email}",
            headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 403
        data = json.loads(rv.data)
        assert "error" in data
        assert "Access Denied" in data["error"]


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


def test_api_docs(app_req_ctx):
    """Test API docs."""
    tech_contact = User.get(email="app123@test0.edu")
    with app_req_ctx("/api-docs/?url=http://SPECIFICATION") as ctx:
        login_user(tech_contact)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"http://SPECIFICATION" in rv.data
    with app_req_ctx("/api-docs") as ctx:
        login_user(tech_contact)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert url_for("spec", _external=True).encode("utf-8") in rv.data
    super_user = User.create(email="super_user@test0.edu", roles=Role.SUPERUSER, confirmed=True)
    with app_req_ctx("/db-api-docs/?url=http://SPECIFICATION") as ctx:
        login_user(super_user)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"http://SPECIFICATION" in rv.data
    with app_req_ctx("/db-api-docs") as ctx:
        login_user(super_user)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert url_for("Swagger.model_resources", _external=True).encode("utf-8") in rv.data


def test_db_api(app_req_ctx):
    """Test DB API."""
    with app_req_ctx(
            "/data/api/v0.1/organisations/", headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert "objects" in data
        assert len(data["objects"]) == 4

    with app_req_ctx("/data/api/v0.1/tasks/", headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert "objects" in data
        assert len(data["objects"]) == 0

    org = Organisation.get(id=1)
    with app_req_ctx(
            f"/data/api/v0.1/organisations/{org.id}",
            headers=dict(authorization="Bearer TEST")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data["name"] == org.name
        assert data["tuakiri_name"] == org.tuakiri_name

    org = Organisation.get(id=2)
    with app_req_ctx(
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
        "/api/v0.1/affiliations/?filename=TEST42.csv",
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

    resp = client.get("/api/v0.1/tasks", headers=dict(authorization=f"Bearer {access_token}"))
    tasks = json.loads(resp.data)
    assert tasks[0]["id"] == task_id

    task_copy = copy.deepcopy(data)
    del(task_copy["id"])
    task_copy["filename"] = "TASK-COPY.csv"
    resp = client.post(
        "/api/v0.1/affiliations/",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(task_copy))
    assert Task.select().count() == 2

    for r in data["records"]:
        del(r["id"])
        r["city"] = "TEST000"
    resp = client.post(
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(data))
    data = json.loads(resp.data)
    assert len(data["records"]) == 3
    # should get a new set of records

    del(data["records"][2])
    resp = client.post(
        f"/api/v0.1/affiliations/{task_id}",
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
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(incorrect_data))
    data = json.loads(resp.data)
    assert resp.status_code == 422
    assert data["error"] == "Validation error."

    resp = client.get(
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    data = json.loads(resp.data)
    incorrect_data = copy.deepcopy(data)
    incorrect_data["records"].insert(0, {
        "email": "test1234@test.edu",
        "first-name": "TEST000 FN",
        "last-name": "TEST000 LN",
    })
    resp = client.post(
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(incorrect_data))
    data = json.loads(resp.data)
    assert resp.status_code == 422
    assert data["error"] == "Validation error."

    resp = client.get(
        f"/api/v0.1/affiliations/{task_id}",
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
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(new_data))
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert len(data["records"]) == 3

    resp = client.put(
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(data))
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert len(data["records"]) == 3

    resp = client.get(
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    data = json.loads(resp.data)
    new_data = copy.deepcopy(data)
    for i, r in enumerate(new_data["records"]):
        new_data["records"][i] = {"id": r["id"], "is-active": True}
    resp = client.patch(
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(new_data))
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert len(data["records"]) == 3
    assert all(r["is-active"] for r in data["records"])
    assert all(r["city"] == "TEST000" for r in data["records"])

    resp = client.head(
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert "Last-Modified" in resp.headers

    resp = client.head(
        "/api/v0.1/affiliations/999999999",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 404

    resp = client.get(
        "/api/v0.1/affiliations/999999999",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 404

    resp = client.patch(
        "/api/v0.1/affiliations/999999999",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(new_data))
    assert resp.status_code == 404

    resp = client.delete(
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert Task.select().count() == 1

    resp = client.delete(
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 404

    other_user = User.get(email="admin@test1.edu")
    other_task = Task.create(
        created_by=other_user,
        org=other_user.organisation,
        filename="OTHER.csv",
        task_type=TaskType.AFFILIATION)

    resp = client.head(
        f"/api/v0.1/affiliations/{other_task.id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 403

    resp = client.get(
        f"/api/v0.1/affiliations/{other_task.id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 403

    resp = client.patch(
        f"/api/v0.1/affiliations/{other_task.id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=json.dumps(new_data))
    assert resp.status_code == 403

    resp = client.delete(
        f"/api/v0.1/affiliations/{other_task.id}",
        headers=dict(authorization=f"Bearer {access_token}"))
    assert resp.status_code == 403

    resp = client.patch(
        f"/api/v0.1/affiliations/{task_id}",
        headers=dict(authorization=f"Bearer {access_token}"),
        content_type="application/json",
        data=b'')
    assert resp.status_code == 400

    resp = client.post(
        "/api/v0.1/affiliations/?filename=TEST42.csv",
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
    assert task.affiliationrecord_set.count() == 3


def test_proxy_get_profile(app_req_ctx):
    """Test the echo endpoint."""
    user = User.get(email="app123@test0.edu")
    token = Token.get(user=user)
    orcid_id = "0000-0000-0000-00X3"

    with app_req_ctx(
            f"/orcid/api/v1.23/{orcid_id}", headers=dict(
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
        assert args[0].url == f"https://api.sandbox.orcid.org/v1.23/{orcid_id}"
        assert args[0].headers["Authorization"] == "Bearer ORCID-TEST-ACCESS-TOKEN"

        data = json.loads(resp.data)
        assert data == {"data": "TEST"}

    with app_req_ctx(
            f"/orcid/api/v1.23/{orcid_id}", headers=dict(
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
                "Expires": "0",
        }
        mocksend.return_value = mockresp
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 201
        args, kwargs = mocksend.call_args
        assert kwargs["stream"]
        assert args[0].url == f"https://api.sandbox.orcid.org/v1.23/{orcid_id}"
        assert args[0].headers["Authorization"] == "Bearer ORCID-TEST-ACCESS-TOKEN"

        data = json.loads(resp.data)
        assert data == {"data": "TEST"}

    # malformatted ORCID ID:
    with app_req_ctx(
            "/orcid/api/v1.23/NOT-ORCID-ID/PATH", headers=dict(
                authorization=f"Bearer {token.access_token}")) as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 415

    # no ORCID access token
    with app_req_ctx(
            "/orcid/api/v1.23/0000-0000-0000-11X2/PATH", headers=dict(
                authorization=f"Bearer {token.access_token}")) as ctx:
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 403


def test_webhook_registration(app_req_ctx):
    """Test webhook registration."""
    user = User.get(email="app123@test0.edu")
    org = user.organisation
    orcid_id = "0000-0000-0000-00X3"
    client = Client.get(org=org)
    with app_req_ctx(
            "/oauth/token",
            method="POST",
            data=dict(
                grant_type="client_credentials",
                client_id=client.client_id,
                client_secret=client.client_secret,
                scope="/webhook")) as ctx:
        login_user(user)
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        token = Token.get(user=user, _scopes="/webhook")
        client = Client.get(client_id="CLIENT_ID")
        token = Token.get(client=client)
        assert data["access_token"] == token.access_token
        assert data["expires_in"] == ctx.app.config["OAUTH2_PROVIDER_TOKEN_EXPIRES_IN"]
        assert data["token_type"] == token.token_type
        # prevously created access token should be removed

    with app_req_ctx(
            f"/api/v0.1/{orcid_id}/webhook/http%3A%2F%2FCALL-BACK",
            method="PUT", headers=dict(
                authorization=f"Bearer {token.access_token}")) as ctx, patch(
                            "orcid_hub.utils.requests.post") as mockpost, patch(
                            "orcid_hub.utils.requests.put") as mockput:
        # Access toke request resp:
        mockresp = MagicMock(status_code=201)
        mockresp.json.return_value = {
            "access_token": "ACCESS-TOKEN-123",
            "token_type": "bearer",
            "refresh_token": "REFRESH-TOKEN-123",
            "expires_in": 99999,
            "scope": "/webhook",
            "orcid": None
        }
        mockpost.return_value = mockresp
        # Webhook registration response:
        mockresp = MagicMock(status_code=201, data=b'')
        # mockresp.raw.stream = lambda *args, **kwargs: iter([b"""{"data": "TEST"}"""])
        mockresp.raw.headers = {
                "Server": "TEST123",
                "Connection": "keep-alive",
                "Location": "LOCATION",
                "Pragma": "no-cache",
                "Expires": "0",
        }
        mockput.return_value = mockresp
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 201
        args, kwargs = mockpost.call_args
        assert args[0] == "https://sandbox.orcid.org/oauth/token"
        assert kwargs["data"] == {
            "client_id": "APP-12345678",
            "client_secret": "CLIENT-SECRET",
            "scope": "/webhook",
            "grant_type": "client_credentials"
        }
        assert kwargs["headers"] == {"Accept": "application/json"}

        args, kwargs = mockput.call_args
        assert args[0] == "https://api.sandbox.orcid.org/0000-0000-0000-00X3/webhook/http%3A%2F%2FCALL-BACK"
        assert kwargs["headers"] == {
            "Accept": "application/json",
            "Authorization": "Bearer ACCESS-TOKEN-123",
            "Content-Length": "0"
        }

        q = OrcidToken.select().where(OrcidToken.org == org, OrcidToken.scope == "/webhook")
        assert q.count() == 1
        orcid_token = q.first()
        assert orcid_token.access_token == "ACCESS-TOKEN-123"
        assert orcid_token.refresh_token == "REFRESH-TOKEN-123"
        assert orcid_token.expires_in == 99999
        assert orcid_token.scope == "/webhook"

    with app_req_ctx(
            f"/api/v0.1/{orcid_id}/webhook/http%3A%2F%2FCALL-BACK",
            method="DELETE", headers=dict(
                authorization=f"Bearer {token.access_token}")) as ctx, patch(
                            "orcid_hub.utils.requests.delete") as mockdelete:
        # Webhook deletion response:
        mockresp = MagicMock(status_code=204, data=b'')
        # mockresp.raw.stream = lambda *args, **kwargs: iter([b"""{"data": "TEST"}"""])
        mockresp.raw.headers = {
                "Server": "TEST123",
                "Connection": "keep-alive",
                "Location": "LOCATION",
                "Pragma": "no-cache",
                "Expires": "0",
        }
        mockdelete.return_value = mockresp
        resp = ctx.app.full_dispatch_request()
        assert resp.status_code == 204

        args, kwargs = mockput.call_args
        assert args[0] == "https://api.sandbox.orcid.org/0000-0000-0000-00X3/webhook/http%3A%2F%2FCALL-BACK"
        assert kwargs["headers"] == {
            "Accept": "application/json",
            "Authorization": "Bearer ACCESS-TOKEN-123",
            "Content-Length": "0"
        }

        q = OrcidToken.select().where(OrcidToken.org == org, OrcidToken.scope == "/webhook")
        assert q.count() == 1
        token = q.first()
        assert token.access_token == "ACCESS-TOKEN-123"
        assert token.refresh_token == "REFRESH-TOKEN-123"
        assert token.expires_in == 99999
        assert token.scope == "/webhook"
