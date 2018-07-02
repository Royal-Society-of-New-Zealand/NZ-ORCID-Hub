# -*- coding: utf-8 -*-
"""Tests for webhooks functions."""

import logging
import json
from types import SimpleNamespace as SimpleObject

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
            org=org, access_token="access_token", refresh_token="refresh_token", scope="/webhook")
        token = utils.get_client_credentials_token(org, "/webhook")
        assert OrcidToken.select().where(OrcidToken.org == org, OrcidToken.scope == "/webhook").count() == 1
        assert token.access_token == "ACCESS-TOKEN-123"
        assert token.refresh_token == "REFRESH-TOKEN-123"
        assert token.expires_in == 99999
        assert token.scope == "/webhook"


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
            f"/api/v1.0/{orcid_id}/webhook/http%3A%2F%2FCALL-BACK",
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
            f"/api/v1.0/{orcid_id}/webhook/http%3A%2F%2FCALL-BACK",
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


def test_org_webhook(app_req_ctx, monkeypatch):
    """Test Organisation webhooks."""
    monkeypatch.setattr(
        utils.requests, "post",
        lambda *args, **kwargs: SimpleObject(
            status_code=201,
            json=lambda: dict(access_token="ABC123", refresh_token="REFRESS_ME", expires_in=123456789)))
    monkeypatch.setattr(utils.requests, "put", lambda *args, **kwargs: SimpleObject(status_code=201))
    monkeypatch.setattr(utils.requests, "delete", lambda *args, **kwargs: SimpleObject(status_code=204))

    org = app_req_ctx.data["org"]
    admin = org.tech_contact
    user = app_req_ctx.data["user"]

    monkeypatch.setattr(utils.register_orcid_webhook, "queue", utils.register_orcid_webhook)
    monkeypatch.setattr(utils.invoke_webhook_handler, "queue", utils.invoke_webhook_handler)

    utils.enable_org_webhook(org)
    assert org.webhook_enabled
    assert org.users.where(User.orcid.is_null(False), User.webhook_enabled).count() > 0

    utils.disable_org_webhook(org)
    assert not org.webhook_enabled
    assert org.users.where(User.orcid.is_null(False), User.webhook_enabled).count() == 0

    with app_req_ctx(
            f"/services/{user.id}/updated",
            method="POST") as ctx, patch.object(utils, "send_email") as send_email:
        send_email.assert_not_called()

    with app_req_ctx(
            "/settings/webhook", method="POST",
            data=dict(
                webhook_url="https://ORG.org/HANDLE",
                webhook_enabled='y')) as ctx:

        login_user(admin)
        assert not Organisation.get(org.id).webhook_enabled
        resp = ctx.app.full_dispatch_request()
        assert Organisation.get(org.id).webhook_enabled
        assert resp.status_code == 200

        with app_req_ctx(
                f"/services/{user.id}/updated",
                method="POST") as ctx, patch.object(utils, "send_email") as send_email:
            resp = ctx.app.full_dispatch_request()
            send_email.assert_not_called()
            assert resp.status_code == 204

    with app_req_ctx(
            "/settings/webhook", method="POST",
            data=dict(
                webhook_url="https://ORG.org/HANDLE",
                webhook_enabled='y',
                email_notifications_enabled='y')) as ctx:

        login_user(admin)
        assert not Organisation.get(org.id).email_notifications_enabled
        resp = ctx.app.full_dispatch_request()
        assert Organisation.get(org.id).email_notifications_enabled
        assert resp.status_code == 200

        with app_req_ctx(
                f"/services/{user.id}/updated",
                method="POST") as ctx, patch.object(utils, "send_email") as send_email:
            resp = ctx.app.full_dispatch_request()
            send_email.assert_called()
            assert resp.status_code == 204

        monkeypatch.setattr(utils.requests, "post", lambda *args, **kwargs: SimpleObject(status_code=404))
        with app_req_ctx(
                f"/services/{user.id}/updated",
                method="POST") as ctx, patch.object(utils, "send_email") as send_email:
            resp = ctx.app.full_dispatch_request()
            send_email.assert_called()
            assert resp.status_code == 204

        # Test update summary:
        monkeypatch.setattr(utils.send_orcid_update_summary, "queue", utils.send_orcid_update_summary)

        with patch.object(utils, "send_email") as send_email:
            utils.send_orcid_update_summary()
            send_email.assert_not_called()

            utils.send_orcid_update_summary(org.id)
            send_email.assert_not_called()

            utils.send_orcid_update_summary(9999999)
            send_email.assert_not_called()

        with patch.object(utils, "send_email") as send_email:
            user.orcid_updated_at = utils.date.today().replace(day=1) - utils.timedelta(days=1)
            user.save()
            utils.send_orcid_update_summary()
            send_email.assert_called()

        with patch("emails.html") as mock_msg:
            org.notification_email = "notifications@org.edu"
            org.save()
            utils.send_orcid_update_summary()
            mock_msg.return_value.mail_to.append.assert_called_with((
                "notifications@org.edu",
                "notifications@org.edu",
            ))
