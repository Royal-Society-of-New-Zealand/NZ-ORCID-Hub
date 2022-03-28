# -*- coding: utf-8 -*-
"""Tests for webhooks functions."""

import datetime
import json
import logging
from types import SimpleNamespace as SimpleObject
from unittest.mock import MagicMock, Mock, call, patch
from urllib.parse import urlparse

import pytest
from flask_login import login_user

from orcid_hub import utils
from orcid_hub.models import Client, OrcidToken, Organisation, Token, User, UserOrg

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
            "orcid": None,
        }
        mockpost.return_value = mockresp

        OrcidToken.create(
            org=org, access_token="access_token", refresh_token="refresh_token", scopes="/webhook"
        )
        token = utils.get_client_credentials_token(org, "/webhook")
        assert (
            OrcidToken.select()
            .where(OrcidToken.org == org, OrcidToken.scopes == "/webhook")
            .count()
            == 1
        )
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
        data=dict(
            grant_type="client_credentials",
            client_id=client.client_id,
            client_secret=client.client_secret,
            scope="/webhook",
        ),
    )

    assert resp.status_code == 200
    data = json.loads(resp.data)
    client = Client.get(client_id="CLIENT_ID")
    token = Token.select().where(Token.user == user, Token._scopes == "/webhook").first()
    assert data["access_token"] == token.access_token
    assert data["expires_in"] == test_client.application.config["OAUTH2_PROVIDER_TOKEN_EXPIRES_IN"]
    assert data["token_type"] == token.token_type
    # prevously created access token should be removed

    resp = test_client.put(
        "/api/v1/INCORRECT/webhook/http%3A%2F%2FCALL-BACK",
        headers=dict(authorization=f"Bearer {token.access_token}"),
    )
    assert resp.status_code == 415
    assert json.loads(resp.data)["error"] == "Missing or invalid ORCID iD."

    resp = test_client.put(
        "/api/v1/0000-0001-8228-7153/webhook/http%3A%2F%2FCALL-BACK",
        headers=dict(authorization=f"Bearer {token.access_token}"),
    )
    assert resp.status_code == 404
    assert json.loads(resp.data)["error"] == "Invalid ORCID iD."

    resp = test_client.put(
        f"/api/v1/{orcid_id}/webhook/INCORRECT-WEBHOOK-URL",
        headers=dict(authorization=f"Bearer {token.access_token}"),
    )
    assert resp.status_code == 415
    assert json.loads(resp.data) == {
        "error": "Invalid call-back URL",
        "message": "Invalid call-back URL: INCORRECT-WEBHOOK-URL",
    }

    with patch("orcid_hub.utils.requests.post") as mockpost, patch(
        "orcid_hub.utils.requests.put"
    ) as mockput:
        # Access toke request resp:
        mockresp = MagicMock(status_code=201)
        mockresp.json.return_value = {
            "access_token": "ACCESS-TOKEN-123",
            "token_type": "bearer",
            "refresh_token": "REFRESH-TOKEN-123",
            "expires_in": 99999,
            "scope": "/webhook",
            "orcid": None,
        }
        mockpost.return_value = mockresp
        # Webhook registration response:
        mockresp = MagicMock(status_code=201, data=b"")
        mockresp.headers = {
            "Server": "TEST123",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        mockput.return_value = mockresp
        resp = test_client.put(
            f"/api/v1/{orcid_id}/webhook/http%3A%2F%2FCALL-BACK",
            headers=dict(authorization=f"Bearer {token.access_token}"),
        )

        assert resp.status_code == 201
        args, kwargs = mockpost.call_args
        assert args[0] == "https://sandbox.orcid.org/oauth/token"
        assert kwargs["data"] == {
            "client_id": "APP-12345678",
            "client_secret": "CLIENT-SECRET",
            "scope": "/webhook",
            "grant_type": "client_credentials",
        }
        assert kwargs["headers"] == {"Accept": "application/json"}

        args, kwargs = mockput.call_args
        assert (
            args[0]
            == "https://api.sandbox.orcid.org/0000-0000-0000-00X3/webhook/http%3A%2F%2FCALL-BACK"
        )
        assert kwargs["headers"] == {
            "Accept": "application/json",
            "Authorization": "Bearer ACCESS-TOKEN-123",
            "Content-Length": "0",
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
        mockresp = MagicMock(status_code=204, data=b"")
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
            headers=dict(authorization=f"Bearer {token.access_token}"),
        )
        assert resp.status_code == 204
        assert urlparse(resp.location).path == f"/api/v1/{orcid_id}/webhook/http://TEST-LOCATION"

        args, kwargs = mockput.call_args
        assert (
            args[0]
            == "https://api.sandbox.orcid.org/0000-0000-0000-00X3/webhook/http%3A%2F%2FCALL-BACK"
        )
        assert kwargs["headers"] == {
            "Accept": "application/json",
            "Authorization": "Bearer ACCESS-TOKEN-123",
            "Content-Length": "0",
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
        utils.requests,
        "post",
        lambda *args, **kwargs: SimpleObject(
            status_code=201,
            json=lambda: dict(
                access_token="ABC123", refresh_token="REFRESS_ME", expires_in=123456789
            ),
        ),
    )
    mocker.patch.object(
        utils.requests, "put", lambda *args, **kwargs: SimpleObject(status_code=201, text="")
    )
    mocker.patch.object(
        utils.requests, "delete", lambda *args, **kwargs: SimpleObject(status_code=204, text="")
    )

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
        "/settings/webhook", data=dict(webhook_url="https://ORG.org/HANDLE", webhook_enabled="y")
    )
    assert Organisation.get(org.id).webhook_enabled
    assert resp.status_code == 200

    resp = client.post(f"/services/{user.id}/updated")
    send_email.assert_not_called()
    assert resp.status_code == 204

    assert not Organisation.get(org.id).email_notifications_enabled
    resp = client.post(
        "/settings/webhook",
        data=dict(
            webhook_url="https://ORG.org/HANDLE",
            webhook_enabled="y",
            email_notifications_enabled="y",
        ),
    )
    assert Organisation.get(org.id).email_notifications_enabled
    assert resp.status_code == 200

    resp = client.post(f"/services/{user.id}/updated")
    send_email.assert_called()
    assert resp.status_code == 204

    post = mocker.patch.object(utils.requests, "post", return_value=Mock(status_code=204))
    for u in User.select().where(
        User.organisation == user.organisation, User.orcid.is_null(False)
    ):
        post.reset_mock()
        send_email.reset_mock()
        resp = client.post(f"/services/{u.id}/updated")
        send_email.assert_called()
        post.assert_called()
        assert resp.status_code == 204

    # Enable only email notification:
    resp = client.post(
        "/settings/webhook", data=dict(webhook_enabled="", email_notifications_enabled="")
    )
    assert resp.status_code == 200
    assert not Organisation.get(org.id).email_notifications_enabled
    resp = client.post(
        "/settings/webhook",
        data=dict(webhook_url="", webhook_enabled="", email_notifications_enabled="y"),
    )
    assert Organisation.get(org.id).email_notifications_enabled
    assert resp.status_code == 200

    post.reset_mock()
    send_email.reset_mock()
    resp = client.post(f"/services/{user.id}/updated")
    send_email.assert_called()
    post.assert_not_called()
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


def test_email_notification(client, mocker):
    """Test Organisation webhook email notifcations."""
    org = client.data["org"]
    user = client.data["user"]

    org.email_notifications_enabled = True
    org.save()
    resp = client.post(f"/services/{user.id}/updated")
    assert resp.status_code == 204

    org.notification_email = "notification@org.edu"
    org.save()
    resp = client.post(f"/services/{user.id}/updated")
    assert resp.status_code == 204

    send_email = mocker.patch("orcid_hub.utils.send_email")

    org.notification_email = None
    org.save()
    resp = client.post(f"/services/{user.id}/updated")
    assert resp.status_code == 204
    _, kwargs = send_email.call_args
    assert kwargs["cc_email"] is None

    org.notification_email = "notification@org.edu"
    org.save()
    resp = client.post(f"/services/{user.id}/updated")
    assert resp.status_code == 204
    _, kwargs = send_email.call_args


def test_webhook_invokation(client, mocker):
    """Test Organisation webhook invokation."""
    org = client.data["org"]
    user = client.data["user"]
    post = mocker.patch.object(utils.requests, "post", return_value=Mock(status_code=204))
    message = {
        "orcid": user.orcid,
        "url": f"https://sandbox.orcid.org/{user.orcid}",
        "type": "UPDATED",
        "updated-at": User.get(user.id).updated_at.isoformat(timespec="seconds"),
        "email": user.email,
        "eppn": user.eppn,
    }

    org.webhook_enabled = True
    org.webhook_url = "http://test.edu/"
    org.save()
    resp = client.post(f"/services/{user.id}/updated")
    assert resp.status_code == 204
    post.assert_called_with("http://test.edu/", json=message)

    org.webhook_append_orcid = True
    org.save()
    resp = client.post(f"/services/{user.id}/updated")
    assert resp.status_code == 204
    post.assert_called_with(f"http://test.edu/{user.orcid}", json=message)

    org.webhook_url = "http://test.edu"
    org.save()
    resp = client.post(f"/services/{user.id}/updated")
    assert resp.status_code == 204
    post.assert_called_with(f"http://test.edu/{user.orcid}", json=message)

    post = mocker.patch.object(utils.requests, "post", return_value=Mock(status_code=400))
    with pytest.raises(Exception):
        utils.invoke_webhook_handler(org.id, attempts=1, message=message)

    schedule = mocker.patch("orcid_hub.utils.invoke_webhook_handler.schedule")
    resp = client.post(f"/services/{user.id}/updated")
    assert resp.status_code == 204
    schedule.assert_called_with(
        datetime.timedelta(seconds=300), attempts=4, message=message, org_id=org.id
    )

    Organisation.update(webhook_apikey="ABC123").execute()
    schedule.reset_mock()
    resp = client.post(f"/services/{user.id}/updated")
    schedule.assert_called_with(
        datetime.timedelta(seconds=300), attempts=4, message=message, org_id=org.id
    )

    Organisation.update(webhook_apikey=None).execute()
    post = mocker.patch.object(utils.requests, "post", side_effect=Exception("OH! NOHHH!"))
    schedule.reset_mock()
    resp = client.post(f"/services/{user.id}/updated")
    assert resp.status_code == 204
    schedule.assert_not_called()

    with pytest.raises(Exception):
        utils.invoke_webhook_handler(org.id, attempts=1, message=message)

    # Test backward compatibility
    with pytest.raises(Exception):
        utils.invoke_webhook_handler(
            orcid=user.orcid, attempts=2, message=message, legacy_kwarg="abc123"
        )


def test_org_webhook_api(client, mocker):
    """Test Organisation webhooks."""
    mocker.patch.object(
        utils.requests,
        "post",
        lambda *args, **kwargs: Mock(
            status_code=201,
            json=lambda: dict(
                access_token="ABC123", refresh_token="REFRESH_ME", expires_in=123456789
            ),
        ),
    )

    mockput = mocker.patch.object(utils.requests, "put")
    mockdelete = mocker.patch.object(utils.requests, "delete")

    org = client.data["org"]
    admin = org.tech_contact

    send_email = mocker.patch("orcid_hub.utils.send_email")

    api_client = Client.get(org=org)

    resp = client.post(
        "/oauth/token",
        data=dict(
            grant_type="client_credentials",
            client_id=api_client.client_id,
            client_secret=api_client.client_secret,
            scope="/webhook",
        ),
    )

    assert resp.status_code == 200
    data = json.loads(resp.data)
    api_client = Client.get(client_id="CLIENT_ID")
    token = Token.select().where(Token.user == admin, Token._scopes == "/webhook").first()

    assert data["access_token"] == token.access_token
    assert data["expires_in"] == client.application.config["OAUTH2_PROVIDER_TOKEN_EXPIRES_IN"]
    assert data["token_type"] == token.token_type

    client.access_token = token.access_token

    resp = client.put("/api/v1/webhook/INCORRECT-WEBHOOK-URL")
    assert resp.status_code == 415
    assert json.loads(resp.data) == {
        "error": "Invalid call-back URL",
        "message": "Invalid call-back URL: INCORRECT-WEBHOOK-URL",
    }

    # Webhook registration response:
    mockresp = MagicMock(status_code=201, data=b"")
    mockresp.headers = {
        "Server": "TEST123",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    mockput.return_value = mockresp

    # Webhook deletion response:
    mockresp = MagicMock(status_code=204, data=b"")
    mockresp.headers = {
        "Seresper": "TEST123",
        "Connection": "keep-alive",
        "Location": "TEST-LOCATION",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    mockdelete.return_value = mockresp

    resp = client.put("/api/v1/webhook/http%3A%2F%2FCALL-BACK")
    assert resp.status_code == 200

    resp = client.put(
        "/api/v1/webhook/http%3A%2F%2FCALL-BACK",
        data=dict(enabled=True, url="https://CALL-BACK.edu/callback"),
    )
    assert resp.status_code == 201

    server_name = client.application.config["SERVER_NAME"]
    mockput.assert_has_calls(
        [
            call(
                "https://api.sandbox.orcid.org/1001-0001-0001-0001/webhook/"
                f"https%3A%2F%2F{server_name}%2Fservices%2F21%2Fupdated",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer ABC123",
                    "Content-Length": "0",
                },
            ),
            call(
                "https://api.sandbox.orcid.org/0000-0000-0000-00X3/webhook/"
                f"https%3A%2F%2F{server_name}%2Fservices%2F22%2Fupdated",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer ABC123",
                    "Content-Length": "0",
                },
            ),
            call(
                "https://api.sandbox.orcid.org/0000-0000-0000-11X2/webhook/"
                f"https%3A%2F%2F{server_name}%2Fservices%2F30%2Fupdated",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer ABC123",
                    "Content-Length": "0",
                },
            ),
        ]
    )

    q = OrcidToken.select().where(OrcidToken.org == org, OrcidToken.scopes == "/webhook")
    assert q.exists()
    assert q.count() == 1
    orcid_token = q.first()
    assert orcid_token.access_token == "ABC123"
    assert orcid_token.refresh_token == "REFRESH_ME"
    assert orcid_token.expires_in == 123456789
    assert orcid_token.scopes == "/webhook"

    # deactivate:

    resp = client.delete("/api/v1/webhook/http%3A%2F%2FCALL-BACK")
    assert resp.status_code == 200
    assert "job-id" in resp.json

    # activate with all options:
    mockput.reset_mock()
    resp = client.put(
        "/api/v1/webhook",
        data={
            "enabled": True,
            "append-orcid": True,
            "apikey": "APIKEY123",
            "email-notifications-enabled": True,
            "notification-email": "notify_me@org.edu",
        },
    )
    server_name = client.application.config["SERVER_NAME"]
    mockput.assert_has_calls(
        [
            call(
                "https://api.sandbox.orcid.org/1001-0001-0001-0001/webhook/"
                f"https%3A%2F%2F{server_name}%2Fservices%2F21%2Fupdated",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer ABC123",
                    "Content-Length": "0",
                },
            ),
            call(
                "https://api.sandbox.orcid.org/0000-0000-0000-00X3/webhook/"
                f"https%3A%2F%2F{server_name}%2Fservices%2F22%2Fupdated",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer ABC123",
                    "Content-Length": "0",
                },
            ),
            call(
                "https://api.sandbox.orcid.org/0000-0000-0000-11X2/webhook/"
                f"https%3A%2F%2F{server_name}%2Fservices%2F30%2Fupdated",
                headers={
                    "Accept": "application/json",
                    "Authorization": "Bearer ABC123",
                    "Content-Length": "0",
                },
            ),
        ]
    )

    # Link other org to the users
    org2 = Organisation.select().where(Organisation.id != org.id).first()
    UserOrg.insert_many([dict(user_id=u.id, org_id=org2.id) for u in org.users]).execute()
    org2.webhook_enabled = True
    org2.save()
    resp = client.delete("/api/v1/webhook")

    mockput.reset_mock()
    resp = client.put(
        "/api/v1/webhook",
        data={
            "enabled": False,
            "url": "https://CALL-BACK.edu/callback",
            "append-orcid": False,
            "email-notifications-enabled": True,
            "notification-email": "notify_me@org.edu",
        },
    )
    mockput.assert_not_called()

    # Test update summary:
    User.update(
        orcid_updated_at=datetime.date.today().replace(day=1) - datetime.timedelta(days=15)
    ).execute()
    send_email.reset_mock()
    utils.send_orcid_update_summary()
    send_email.assert_called_once()
    client.logout()
