# -*- coding: utf-8 -*-
"""Tests for webhooks functions."""

import logging
import json
from types import SimpleNamespace as SimpleObject
from urllib.parse import urlparse

from flask_login import login_user
from unittest.mock import MagicMock, patch

from orcid_hub import utils
from orcid_hub.models import Client, OrcidToken, Organisation, User, Token

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def test_get_client_credentials_token(request_ctx):
    """Test retrieval of the webhook tokens."""
    with request_ctx("/"), patch("orcid_hub.utils.requests.post") as mockpost:
        admin = User.get(email="admin@test0.edu")
        org = admin.organisation
        login_user(admin)
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

        OrcidToken.create(
            org=org, access_token="access_token", refresh_token="refresh_token", scopes="/webhook")
        token = utils.get_client_credentials_token(org, "/webhook")
        assert OrcidToken.select().where(OrcidToken.org == org, OrcidToken.scopes == "/webhook").count() == 1
        assert token.access_token == "ACCESS-TOKEN-123"
        assert token.refresh_token == "REFRESH-TOKEN-123"
        assert token.expires_in == 99999
        assert token.scopes == "/webhook"


def test_webhook_registration(client):
    """Test webhook registration."""
    test_client = client
    user = User.get(email="app123@test0.edu")
    test_client.login(user)
    org = user.organisation
    orcid_id = "0000-0000-0000-00X3"
    client = Client.get(org=org)

    resp = test_client.post(
        "/oauth/token",
        method="POST",
        data=dict(
            grant_type="client_credentials",
            client_id=client.client_id,
            client_secret=client.client_secret,
            scope="/webhook"))

    assert resp.status_code == 200
    data = json.loads(resp.data)
    token = Token.get(user=user, _scopes="/webhook")
    client = Client.get(client_id="CLIENT_ID")
    token = Token.get(client=client)
    assert data["access_token"] == token.access_token
    assert data["expires_in"] == test_client.application.config["OAUTH2_PROVIDER_TOKEN_EXPIRES_IN"]
    assert data["token_type"] == token.token_type
    # prevously created access token should be removed

    resp = test_client.put(
        "/api/v1/INCORRECT/webhook/http%3A%2F%2FCALL-BACK",
        headers=dict(authorization=f"Bearer {token.access_token}"))
    assert resp.status_code == 415
    assert json.loads(resp.data)["error"] == "Missing or invalid ORCID iD."

    resp = test_client.put(
        "/api/v1/0000-0001-8228-7153/webhook/http%3A%2F%2FCALL-BACK",
        headers=dict(authorization=f"Bearer {token.access_token}"))
    assert resp.status_code == 404
    assert json.loads(resp.data)["error"] == "Invalid ORCID iD."

    resp = test_client.put(
        f"/api/v1/{orcid_id}/webhook/INCORRECT-WEBHOOK-URL",
        headers=dict(authorization=f"Bearer {token.access_token}"))
    assert resp.status_code == 415
    assert json.loads(resp.data) == {
        "error": "Invalid call-back URL",
        "message": "Invalid call-back URL: INCORRECT-WEBHOOK-URL"
    }

    with patch("orcid_hub.utils.requests.post") as mockpost, patch(
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
        mockresp.headers = {
                "Server": "TEST123",
                "Connection": "keep-alive",
                "Pragma": "no-cache",
                "Expires": "0",
        }
        mockput.return_value = mockresp
        resp = test_client.put(
            f"/api/v1/{orcid_id}/webhook/http%3A%2F%2FCALL-BACK",
            headers=dict(authorization=f"Bearer {token.access_token}"))

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

        q = OrcidToken.select().where(OrcidToken.org == org, OrcidToken.scopes == "/webhook")
        assert q.count() == 1
        orcid_token = q.first()
        assert orcid_token.access_token == "ACCESS-TOKEN-123"
        assert orcid_token.refresh_token == "REFRESH-TOKEN-123"
        assert orcid_token.expires_in == 99999
        assert orcid_token.scopes == "/webhook"

    with patch("orcid_hub.utils.requests.delete") as mockdelete:
        # Webhook deletion response:
        mockresp = MagicMock(status_code=204, data=b'')
        mockresp.headers = {
            "Seresper": "TEST123",
            "Connection": "keep-alive",
            "Location": "TEST-LOCATION",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        mockdelete.return_value = mockresp
        resp = test_client.delete(
            f"/api/v1/{orcid_id}/webhook/http%3A%2F%2FCALL-BACK",
            headers=dict(authorization=f"Bearer {token.access_token}"))
        assert resp.status_code == 204
        assert urlparse(resp.location).path == f"/api/v1/{orcid_id}/webhook/http://TEST-LOCATION"

        args, kwargs = mockput.call_args
        assert args[
            0] == "https://api.sandbox.orcid.org/0000-0000-0000-00X3/webhook/http%3A%2F%2FCALL-BACK"
        assert kwargs["headers"] == {
            "Accept": "application/json",
            "Authorization": "Bearer ACCESS-TOKEN-123",
            "Content-Length": "0"
        }

        q = OrcidToken.select().where(OrcidToken.org == org, OrcidToken.scopes == "/webhook")
        assert q.count() == 1
        token = q.first()
        assert token.access_token == "ACCESS-TOKEN-123"
        assert token.refresh_token == "REFRESH-TOKEN-123"
        assert token.expires_in == 99999
        assert token.scopes == "/webhook"


def test_org_webhook(client, mocker):
    """Test Organisation webhooks."""
    mocker.patch.object(
        utils.requests, "post",
        lambda *args, **kwargs: SimpleObject(
            status_code=201,
            json=lambda: dict(access_token="ABC123", refresh_token="REFRESS_ME", expires_in=123456789)))
    mocker.patch.object(utils.requests, "put", lambda *args, **kwargs: SimpleObject(status_code=201))
    mocker.patch.object(utils.requests, "delete", lambda *args, **kwargs: SimpleObject(status_code=204))

    org = client.data["org"]
    admin = org.tech_contact
    user = client.data["user"]

    mocker.patch.object(utils.register_orcid_webhook, "queue", utils.register_orcid_webhook)
    mocker.patch.object(utils.invoke_webhook_handler, "queue", utils.invoke_webhook_handler)

    utils.enable_org_webhook(org)
    assert org.webhook_enabled
    assert org.users.where(User.orcid.is_null(False), User.webhook_enabled).count() > 0

    utils.disable_org_webhook(org)
    assert not org.webhook_enabled
    assert org.users.where(User.orcid.is_null(False), User.webhook_enabled).count() == 0

    resp = client.login(admin)
    resp = client.post(f"/services/{user.id}/updated")
    send_email = mocker.patch.object(utils, "send_email")
    send_email.assert_not_called()

    assert not Organisation.get(org.id).webhook_enabled
    resp = client.post(
        "/settings/webhook", data=dict(webhook_url="https://ORG.org/HANDLE", webhook_enabled='y'))
    assert Organisation.get(org.id).webhook_enabled
    assert resp.status_code == 200

    resp = client.post(f"/services/{user.id}/updated")
    send_email.assert_not_called()
    assert resp.status_code == 204

    assert not Organisation.get(org.id).email_notifications_enabled
    resp = client.post("/settings/webhook", data=dict(
                webhook_url="https://ORG.org/HANDLE",
                webhook_enabled='y',
                email_notifications_enabled='y'))
    assert Organisation.get(org.id).email_notifications_enabled
    assert resp.status_code == 200

    resp = client.post(f"/services/{user.id}/updated")
    send_email.assert_called()
    assert resp.status_code == 204

    mocker.patch.object(utils.requests, "post", lambda *args, **kwargs: SimpleObject(status_code=404))
    resp = client.post(f"/services/{user.id}/updated")
    send_email.assert_called()
    assert resp.status_code == 204

    # Test update summary:
    mocker.patch.object(utils.send_orcid_update_summary, "queue", utils.send_orcid_update_summary)

    send_email.reset_mock()
    utils.send_orcid_update_summary()
    send_email.assert_not_called()

    utils.send_orcid_update_summary(org.id)
    send_email.assert_not_called()

    utils.send_orcid_update_summary(9999999)
    send_email.assert_not_called()

    user.orcid_updated_at = utils.date.today().replace(day=1) - utils.timedelta(days=1)
    user.save()
    utils.send_orcid_update_summary()
    send_email.assert_called()

    send_email.reset_mock()
    org.notification_email = "notifications@org.edu"
    org.save()
    utils.send_orcid_update_summary()
    send_email.assert_called_once()

    resp = client.post("/settings/webhook", data=dict(save_webhook="Save"))
    assert resp.status_code == 200
    assert not Organisation.get(org.id).webhook_enabled
    assert not Organisation.get(org.id).email_notifications_enabled
