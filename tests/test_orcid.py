# -*- coding: utf-8 -*-
"""Tests related to ORCID affilation."""

import json
import time
from unittest.mock import DEFAULT, MagicMock, Mock, call, patch

import pytest
import requests_oauthlib
from flask import session, url_for
from flask_login import login_user

from orcid_hub.models import Affiliation, OrcidApiCall, OrcidToken, Organisation, User, UserOrg  # noqa:E404
from orcid_hub.orcid_client import ApiException, MemberAPI, api_client, configuration  # noqa:E404

fake_time = time.time()


def test_member_api(app, mocker):
    """Test MemberAPI extension and wrapper of ORCID API."""
    mocker.patch.multiple("orcid_hub.app.logger", error=DEFAULT, exception=DEFAULT, info=DEFAULT)
    org = Organisation.create(name="THE ORGANISATION", confirmed=True, orcid_client_id="CLIENT000")
    user = User.create(
        orcid="1001-0001-0001-0001",
        name="TEST USER 123",
        email="test123@test.test.net",
        organisation=org,
        confirmed=True)
    UserOrg.create(user=user, org=org, affiliation=Affiliation.EDU)

    MemberAPI(user=user)
    assert configuration.access_token is None or configuration.access_token == ''

    MemberAPI(user=user, org=org)
    assert configuration.access_token is None or configuration.access_token == ''

    MemberAPI(user=user, org=org, access_token="ACCESS000")
    assert configuration.access_token == 'ACCESS000'

    OrcidToken.create(
        access_token="ACCESS123", user=user, org=org, scope="/read-limited,/activities/update", expires_in='121')
    api = MemberAPI(user=user, org=org)
    assert configuration.access_token == "ACCESS123"

    with patch.object(
            api_client.ApiClient, "call_api", side_effect=ApiException(
                reason="FAILURE", status=401)) as call_api:
        with patch.object(OrcidToken, "delete") as delete:
            api.get_record()
            app.logger.error.assert_called_with("ApiException Occured: (401)\nReason: FAILURE\n")
            call_api.assert_called_once()
            delete.assert_called_once()

    with patch.object(
            api_client.ApiClient,
            "call_api",
            side_effect=ApiException(reason="FAILURE 999", status=999)) as call_api:
        api.get_record()
        app.logger.error.assert_called_with("ApiException Occured: (999)\nReason: FAILURE 999\n")

    with patch.object(
            api_client.ApiClient, "call_api", side_effect=ApiException(
                reason="FAILURE", status=401)) as call_api:
        with patch.object(OrcidToken, "get", side_effect=Exception("FAILURE")) as get:
            api.get_record()
            app.logger.exception.assert_called_with(
                "Exception occured while retriving ORCID Token")
            call_api.assert_called_once()
            get.assert_called_once()

    with patch.object(
            api_client.ApiClient,
            "call_api",
            return_value=(
                Mock(data=b"""{"mock": "data"}"""),
                200,
                [],
            )) as call_api:
        api.get_record()
        call_api.assert_called_with(
            f"/v2.0/{user.orcid}",
            "GET",
            _preload_content=False,
            auth_settings=["orcid_auth"],
            header_params={"Accept": "application/json"},
            response_type=None)

    # Test API call auditing:
    with patch.object(
            api_client.RESTClientObject.__base__,
            "request",
            return_value=Mock(data=b"""{"mock": "data"}""", status_code=200)) as request_mock:

        api.get_record()

        request_mock.assert_called_once_with(
            _preload_content=False,
            _request_timeout=None,
            body=None,
            headers={
                "Accept": "application/json",
                "User-Agent": "Swagger-Codegen/1.0.0/python",
                "Authorization": "Bearer ACCESS123"
            },
            method="GET",
            post_params=None,
            query_params=None,
            url="https://api.sandbox.orcid.org/v2.0/1001-0001-0001-0001")
        api_call = OrcidApiCall.select().first()
        assert api_call.response == '{"mock": "data"}'
        assert api_call.url == "https://api.sandbox.orcid.org/v2.0/1001-0001-0001-0001"

        with patch.object(OrcidApiCall, "create", side_effect=Exception("FAILURE")) as create:
            api.get_record()
            create.assert_called_once()

    with patch.object(
            api_client.RESTClientObject.__base__,
            "request",
            return_value=Mock(data=None, status_code=200)) as request_mock:
        # api.get_record()
        OrcidApiCall.delete().execute()
        api.view_person("1234-XXXX-XXXX-XXXX")
        api_call = OrcidApiCall.select().first()
        assert api_call.response is None
        assert api_call.url == "https://api.sandbox.orcid.org/v2.0/1234-XXXX-XXXX-XXXX/person"


def test_is_emp_or_edu_record_present(app, mocker):
    """Test 'is_emp_or_edu_record_present' method."""
    mocker.patch.multiple("orcid_hub.app.logger", error=DEFAULT, exception=DEFAULT, info=DEFAULT)
    org = Organisation.create(name="THE ORGANISATION", confirmed=True, orcid_client_id="CLIENT000")
    user = User.create(
        orcid="1001-0001-0001-0001",
        name="TEST USER 123",
        email="test123@test.test.net",
        organisation=org,
        confirmed=True)
    UserOrg.create(user=user, org=org, affiliation=Affiliation.EDU)

    api = MemberAPI(user=user, org=org)

    test_responses = [
        None,
        """{"mock": "data"}""",
        """{
            "employment-summary": [{"source": {"source-client-id": {"path": "CLIENT000"}}, "put-code": 123}],
            "education-summary": [{"source": {"source-client-id": {"path": "CLIENT000"}}, "put-code": 456}]
        }""",
        """{"employment-summary": [], "education-summary": []}"""
    ]

    for data in test_responses:
        with patch.object(
                api_client.ApiClient,
                "call_api",
                return_value=Mock(data=data)) as call_api:
            api.is_emp_or_edu_record_present(Affiliation.EDU)
            call_api.assert_called_with(
                "/v2.0/{orcid}/educations",
                "GET", {"orcid": "1001-0001-0001-0001"}, {}, {"Accept": "application/json"},
                _preload_content=False,
                _request_timeout=None,
                _return_http_data_only=True,
                auth_settings=["orcid_auth"],
                body=None,
                callback=None,
                collection_formats={},
                files={},
                post_params=[],
                response_type="Educations")
            api.is_emp_or_edu_record_present(Affiliation.EMP)
            call_api.assert_called_with(
                "/v2.0/{orcid}/employments",
                "GET", {"orcid": "1001-0001-0001-0001"}, {}, {"Accept": "application/json"},
                _preload_content=False,
                _request_timeout=None,
                _return_http_data_only=True,
                auth_settings=["orcid_auth"],
                body=None,
                callback=None,
                collection_formats={},
                files={},
                post_params=[],
                response_type="Employments")

    with patch.object(
            api_client.ApiClient, "call_api", side_effect=ApiException(
                reason="FAILURE", status=401)) as call_api:
        api.is_emp_or_edu_record_present(Affiliation.EDU)
        app.logger.error.assert_called_with(
            "For TEST USER 123 (test123@test.test.net) while checking for employment "
            "and education records, Encountered Exception: (401)\nReason: FAILURE\n")

    with patch.object(
            api_client.ApiClient, "call_api", side_effect=Exception("EXCEPTION")) as call_api:
        api.is_emp_or_edu_record_present(Affiliation.EDU)
        app.logger.exception.assert_called_with(
            "Failed to verify presence of employment or education record.")


@patch.object(requests_oauthlib.OAuth2Session, "authorization_url",
              lambda self, base_url: ("URL_123", None))
def test_link(request_ctx):
    """Test a user affiliation initialization."""
    with request_ctx("/link") as ctx:
        org = Organisation.create(name="THE ORGANISATION", confirmed=True)
        test_user = User.create(
            name="TEST USER 123", email="test123@test.test.net", organisation=org, confirmed=True)
        login_user(test_user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert b"<!DOCTYPE html>" in rv.data, "Expected HTML content"
        assert b"TEST USER 123" in rv.data, "Expected to have the user name on the page"
        assert b"test123@test.test.net" in rv.data, "Expected to have the user email on the page"
        assert b"URL_123" in rv.data, "Expected to have ORCiD authorization link on the page"


@patch.object(requests_oauthlib.OAuth2Session, "authorization_url",
              lambda self, base_url: ("URL_123", None))
def test_link_with_unconfirmed_org(request_ctx):
    """Test a user affiliation initialization if the user Organisation isn't registered yet."""
    with request_ctx("/link") as ctx:
        org = Organisation(
            name="THE ORGANISATION", confirmed=False, orcid_client_id="Test Client id")
        org.save()
        test_user = User(
            name="TEST USER", email="test@test.test.net", confirmed=True, organisation=org)
        test_user.save()
        login_user(test_user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302


@patch.object(requests_oauthlib.OAuth2Session, "authorization_url",
              lambda self, base_url: ("URL_123", None))
def test_link_already_affiliated(request_ctx):
    """Test a user affiliation initialization if the uerer is already affilated."""
    with request_ctx("/link") as ctx:
        org = Organisation(name="THE ORGANISATION", confirmed=True, orcid_client_id="ABC123")
        org.save()
        test_user = User(
            email="test123@test.test.net",
            name="TEST USER",
            organisation=org,
            orcid="ABC123",
            confirmed=True)
        test_user.save()
        orcidtoken = OrcidToken(
            user=test_user, org=org, scope="/read-limited", access_token="ABC1234")
        orcidtoken_write = OrcidToken(
            user=test_user,
            org=org,
            scope="/read-limited,/activities/update",
            access_token="ABC234")
        orcidtoken.save()
        orcidtoken_write.save()
        login_user(test_user, remember=True)
        uo = UserOrg(user=test_user, org=org)
        uo.save()

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302, "If the user is already affiliated, the user should be redirected ..."
        assert "profile" in rv.location, "redirection to 'profile' showing the ORCID"


@pytest.mark.parametrize("name", ["TEST USER", None])
@patch.object(requests_oauthlib.OAuth2Session, "fetch_token", lambda self, *args, **kwargs: dict(
    name="NEW TEST",
    access_token="ABC123",
    orcid="ABC-123-456-789",
    scope=['/read-limited'],
    expires_in="1212",
    refresh_token="ABC1235"))
def test_link_orcid_auth_callback(name, request_ctx):
    """Test ORCID callback - the user authorized the organisation access to the ORCID profile."""
    with request_ctx("/auth?state=xyz") as ctx:
        org = Organisation(name="THE ORGANISATION", confirmed=True)
        org.save()

        test_user = User.create(
            name=name,
            email="test123@test.test.net",
            organisation=org,
            orcid="ABC123",
            confirmed=True)
        orcidtoken = OrcidToken.create(
            user=test_user,
            org=org,
            scope="/read-limited,/activities/update",
            access_token="ABC1234")
        login_user(test_user, remember=True)
        session['oauth_state'] = "xyz"
        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302, "If the user is already affiliated, the user should be redirected ..."
        assert "profile" in rv.location, "redirection to 'profile' showing the ORCID"

        u = User.get(id=test_user.id)
        orcidtoken = OrcidToken.get(user=u)
        assert u.orcid == "ABC-123-456-789"
        assert orcidtoken.access_token == "ABC1234"
        if name:
            assert u.name == name, "The user name should be changed"
        else:
            assert u.name == "NEW TEST", "the user name should be set from record coming from ORCID"


@pytest.mark.parametrize("name", ["TEST USER", None])
@patch.object(requests_oauthlib.OAuth2Session, "fetch_token", lambda self, *args, **kwargs: dict(
    name="NEW TEST",
    access_token="ABC123",
    orcid="ABC-123-456-789",
    scope=['/read-limited,/activities/update'],
    expires_in="1212",
    refresh_token="ABC1235"))
def test_link_orcid_auth_callback_with_affiliation(name, request_ctx):
    """Test ORCID callback - the user authorized the organisation access to the ORCID profile."""
    with patch("orcid_hub.orcid_client.MemberAPI") as m, patch(
            "orcid_hub.orcid_client.SourceClientId"), request_ctx("/auth?state=xyz") as ctx:
        org = Organisation.create(
            name="THE ORGANISATION",
            confirmed=True,
            orcid_client_id="CLIENT ID",
            city="CITY",
            country="COUNTRY",
            disambiguated_id="ID",
            disambiguation_source="SOURCE")

        test_user = User.create(
            name=name,
            email="test123@test.test.net",
            organisation=org,
            orcid="ABC123",
            confirmed=True)

        UserOrg.create(user=test_user, org=org, affiliations=Affiliation.EMP | Affiliation.EDU)

        login_user(test_user, remember=True)
        session['oauth_state'] = "xyz"
        api_mock = m.return_value
        ctx.app.full_dispatch_request()
        assert test_user.orcid == "ABC-123-456-789"

        orcid_token = OrcidToken.get(user=test_user, org=org)
        assert orcid_token.access_token == "ABC123"

        api_mock.create_or_update_affiliation.assert_has_calls([
            call(affiliation=Affiliation.EDU, initial=True),
            call(affiliation=Affiliation.EMP, initial=True),
        ])
        # api_mock.create_employment.assert_called_once()
        # api_mock.create_education.assert_called_once()


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


@patch.object(requests_oauthlib.OAuth2Session, "get",
              lambda self, *args, **kwargs: make_fake_response('{"test": "TEST1234567890"}'))
def test_profile(request_ctx):
    """Test an affilated user profile and ORCID data retrieval."""
    with request_ctx("/profile") as ctx:
        org = Organisation(name="THE ORGANISATION", confirmed=True)
        org.save()
        test_user = User(
            email="test123@test.test.net", organisation=org, orcid="ABC123", confirmed=True)
        test_user.save()
        orcidtoken = OrcidToken(
            user=test_user,
            org=org,
            scope="/read-limited,/activities/update",
            access_token="ABC1234")
        orcidtoken.save()
        login_user(test_user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 200
        assert b"ABC123" in rv.data


def test_profile_wo_orcid(request_ctx):
    """Test a user profile that doesn't hava an ORCID."""
    with request_ctx("/profile") as ctx:
        org = Organisation(name="THE ORGANISATION", confirmed=True)
        org.save()
        test_user = User(
            email="test123@test.test.net", organisation=org, orcid=None, confirmed=True)
        test_user.save()
        login_user(test_user, remember=True)

        rv = ctx.app.full_dispatch_request()
        assert rv.status_code == 302
        assert rv.location == url_for("link")
