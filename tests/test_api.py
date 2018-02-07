# -*- coding: utf-8 -*-
"""Tests for core functions."""

import json

import pytest
from flask import url_for
from flask_login import login_user

from orcid_hub.api import yamlfy
from orcid_hub.models import Client, OrcidToken, Organisation, Role, Token, User, UserOrg


@pytest.fixture
def app_req_ctx(request_ctx):
    """Create the fixture for the reques with a test organisation and a test tech.contatct."""
    org = Organisation.create(
        name="THE ORGANISATION",
        tuakiri_name="THE ORGANISATION",
        confirmed=True,
        city="CITY",
        country="COUNTRY")

    admin = User.create(
        email="app123@test.edu",
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
        email="researcher@test.edu",
        eppn="eppn@test.edu",
        name="TEST REASEARCHER",
        orcid="0000-0000-0000-00X3",
        confirmed=True,
        organisation=org)

    OrcidToken.create(user=user, org=org, access_token="ORCID-TEST-ACCESS-TOKEN")

    User.create(
        email="researcher2@test.edu",
        eppn="eppn2@test.edu",
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
    user = User.get(email="app123@test.edu")
    token = Token.get(user=user)
    with app_req_ctx("/api/me", headers=dict(authorization=f"Bearer {token.access_token}")) as ctx:
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data["email"] == user.email
        assert data["name"] == user.name

    # Test invalid token:
    with app_req_ctx("/api/me", headers=dict(authorization="Bearer INVALID")) as ctx:
        user = User.get(email="app123@test.edu")
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
    user = User.get(email="researcher@test.edu")
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
        user2 = User.get(email="researcher2@test.edu")
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
    tech_contact = User.get(email="app123@test.edu")
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
    super_user = User.create(email="super_user@test.edu", roles=Role.SUPERUSER, confirmed=True)
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
        assert len(data["objects"]) == 2

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
