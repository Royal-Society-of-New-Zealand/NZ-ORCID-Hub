# -*- coding: utf-8 -*-
"""Tests for util functions."""

import codecs
import logging
from io import BytesIO
from itertools import groupby
import random
import string
from unittest.mock import Mock, patch

import pytest
from flask import make_response
from peewee import JOIN
from urllib.parse import quote

from orcid_hub import utils
from orcid_hub.models import (AffiliationRecord, ExternalId, File, FundingContributor,
                              FundingInvitee, FundingRecord, Log, OtherNameRecord, OrcidToken, Organisation,
                              OrgInfo, PeerReviewExternalId, PeerReviewInvitee, PeerReviewRecord, ResearcherUrlRecord,
                              Role, Task, TaskType, User, UserInvitation, UserOrg, WorkContributor,
                              WorkExternalId, WorkInvitee, WorkRecord)

from tests.utils import get_profile

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def test_unique_everseen():
    """Test unique_everseen."""
    assert list(utils.unique_everseen('AAAABBBCCDAABBB')) == list("ABCD")
    assert list(utils.unique_everseen('ABBCcAD', str.lower)) == list("ABCD")


def test_append_qs():
    """Test URL modication."""
    assert utils.append_qs(
        "https://abc.com/bar?p=foo", abc=123,
        p2="ABC") == "https://abc.com/bar?p=foo&abc=123&p2=ABC"
    assert utils.append_qs(
        "https://abc.com/bar", abc=123, p2="ABC") == "https://abc.com/bar?abc=123&p2=ABC"
    assert utils.append_qs(
        "https://abc.com/bar?p=foo", p2="A&B&C D") == "https://abc.com/bar?p=foo&p2=A%26B%26C+D"


def test_generate_confirmation_token():
    """Test to generate confirmation token."""
    token = utils.generate_confirmation_token(["testemail@example.com"], expiration=0.00001)
    data = utils.confirm_token(token)
    # Test positive testcase
    assert 'testemail@example.com' == data[0]

    token = utils.generate_confirmation_token(["testemail@example.com"], expiration=-1)
    is_valid, token = utils.confirm_token(token)
    assert not is_valid

    _salt = utils.app.config["SALT"]
    utils.app.config["SALT"] = None
    token = utils.generate_confirmation_token(["testemail123@example.com"])
    utils.app.config["SALT"] = _salt
    data = utils.confirm_token(token)
    assert 'testemail123@example.com' == data[0]


def test_track_event(client, mocker):
    """Test to track event."""
    category = "test"
    action = "test"
    label = None
    value = 0
    post = mocker.patch("requests.post", return_value=Mock(status_code=200))

    with client.login(client.data["user"]):
        resp = utils.track_event(category, action, label, value)
        assert resp.status_code == 200
    post.assert_called_once()


def test_set_server_name(app):
    """Test to set server name."""
    utils.set_server_name()
    server_name = app.config.get("SERVER_NAME")
    utils.set_server_name()
    assert server_name == app.config.get("SERVER_NAME")
    app.config["SERVER_NAME"] = "abc.orcidhub.org.nz"
    utils.set_server_name()
    assert "abc.orcidhub.org.nz" == app.config.get("SERVER_NAME")


def test_process_records(app):
    """Test process records function."""
    utils.process_records(0)


def send_mail_mock(*argvs, **kwargs):
    """Mock email invitation."""
    logger.info(f"***\nActually email invitation was mocked, so no email sent!!!!!")
    return True


def test_send_user_invitation(app, mocker):
    """Test to send user invitation."""
    send_email = mocker.patch("orcid_hub.utils.send_email")
    org = app.data["org"]
    inviter = User.create(
        email="test123@mailinator.com",
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid=None,
        confirmed=True,
        organisation=org)

    email = "test123445@mailinator.com"
    first_name = "TEST"
    last_name = "Test"
    affiliation_types = {"staff"}
    u = User.create(
        email=email,
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid=None,
        confirmed=True,
        organisation=org)
    UserOrg.create(user=u, org=org)
    task = Task.create(org=org)

    mock_smtp = mocker.patch("smtplib.SMTP").return_value
    instance = mock_smtp.return_value
    error = {email: (450, "Requested mail action not taken: mailbox unavailable")}
    instance.utils.send_user_invitation.return_value = error
    result = instance.utils.send_user_invitation(
        inviter=inviter,
        org=org,
        email=email,
        first_name=first_name,
        last_name=last_name,
        affiliation_types=affiliation_types,
        task_id=task.id)
    assert instance.utils.send_user_invitation.called  # noqa: E712
    assert (450, 'Requested mail action not taken: mailbox unavailable') == result[email]

    send_email = mocker.patch("orcid_hub.utils.send_email")
    result = utils.send_user_invitation(
        inviter=inviter.id,
        org=org.id,
        email=email,
        first_name=first_name,
        last_name=last_name,
        affiliation_types=affiliation_types,
        start_date=[1971, 1, 1],
        end_date=[2018, 5, 29],
        task_id=task.id)
    send_email.assert_called_once()
    assert result == UserInvitation.select().order_by(UserInvitation.id.desc()).first().id


def test_send_work_funding_peer_review_invitation(app, mocker):
    """Test to send user invitation."""
    send_email = mocker.patch("orcid_hub.utils.send_email")
    org = app.data["org"]
    inviter = User.create(
        email="test1as237@mailinator.com",
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid=None,
        confirmed=True,
        organisation=org)

    email = "test1234456@mailinator.com"
    u = User.create(
        email=email,
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid=None,
        confirmed=True,
        organisation=org)
    UserOrg.create(user=u, org=org)
    task = Task.create(org=org, task_type=1)
    fr = FundingRecord.create(task=task, title="xyz", type="Award")
    FundingInvitee.create(funding_record=fr.id, email=email, first_name="Alice", last_name="Bob")

    server_name = app.config.get("SERVER_NAME")
    app.config["SERVER_NAME"] = "abc.orcidhub.org.nz"
    utils.send_work_funding_peer_review_invitation(
        inviter=inviter, org=org, email=email, name=u.name, task_id=task.id)
    app.config["SERVER_NAME"] = server_name
    send_email.assert_called_once()


def get_record_mock():
    """Mock profile api call."""
    return {
        'activities-summary': {
            'last-modified-date': {
                'value': 1513136293368
            },  # noqa: E127
            'educations': {
                'last-modified-date': None,
                'education-summary': [],
                'path': '/0000-0002-3879-2651/educations'
            },
            "employments": {
                "last-modified-date": {
                    "value": 1511401310144
                },
                "employment-summary": [{
                    "created-date": {
                        "value": 1511401310144
                    },
                    "last-modified-date": {
                        "value": 1511401310144
                    },
                    "source": {
                        "source-orcid": None,
                        "source-client-id": {
                            "uri": "http://sandbox.orcid.org/client/APP-5ZVH4JRQ0C27RVH5",
                            "path": "APP-5ZVH4JRQ0C27RVH5",
                            "host": "sandbox.orcid.org"
                        },
                        "source-name": {
                            "value": "The University of Auckland - MyORCiD"
                        }
                    },
                    "department-name": None,
                    "role-title": None,
                    "start-date": None,
                    "end-date": None,
                    "organization": {
                        "name": "The University of Auckland",
                        "address": {
                            "city": "Auckland",
                            "region": None,
                            "country": "NZ"
                        },
                        "disambiguated-organization": None
                    },
                    "visibility": "PUBLIC",
                    "put-code": 29272,
                    "path": "/0000-0003-1255-9023/employment/29272"
                }],
                "path":
                "/0000-0003-1255-9023/employments"
            },
            'fundings': {
                'last-modified-date': {
                    'value': 1513136293368
                },
                'group': [{
                    'last-modified-date': {
                        'value': 1513136293368
                    },
                    'external-ids': {
                        'external-id': [{
                            'external-id-type': 'grant_number',
                            'external-id-value': 'GNS1701',
                            'external-id-url': None,
                            'external-id-relationship': 'SELF'
                        }, {
                            'external-id-type': 'grant_number',
                            'external-id-value': '17-GNS-022',
                            'external-id-url': None,
                            'external-id-relationship': 'SELF'
                        }]
                    },
                    'funding-summary': [{
                        'created-date': {
                            'value': 1511935227017
                        },
                        'last-modified-date': {
                            'value': 1513136293368
                        },
                        'source': {
                            'source-orcid': None,
                            'source-client-id': {
                                'uri': 'http://sandbox.orcid.org/client/APP-5ZVH4JRQ0C27RVH5',
                                'path': 'APP-5ZVH4JRQ0C27RVH5',
                                'host': 'sandbox.orcid.org'
                            },
                            'source-name': {
                                'value': 'The University of Auckland - MyORCiD'
                            }
                        },
                        'title': {
                            'title': {
                                'value': 'Probing the crust with zirco'
                            },
                            'translated-title': {
                                'value': 'नमस्ते',
                                'language-code': 'hi'
                            }
                        },
                        'type': 'CONTRACT',
                        'start-date': None,
                        'end-date': {
                            'year': {
                                'value': '2025'
                            },
                            'month': None,
                            'day': None
                        },
                        'organization': {
                            'name': 'Royal Society Te Apārangi'
                        },
                        'put-code': 9597,
                        'path': '/0000-0002-3879-2651/funding/9597'
                    }]
                }],
                'path':
                '/0000-0002-3879-2651/fundings'
            },
            "peer-reviews": {
                "group": [
                    {
                        "external-ids": {
                            "external-id": [
                                {
                                    "external-id-type": "peer-review",
                                    "external-id-value": "issn:12131",
                                    "external-id-url": None,
                                    "external-id-relationship": None
                                }
                            ]
                        },
                        "peer-review-summary": [
                            {
                                "source": {
                                    "source-orcid": None,
                                    "source-client-id": {
                                        "uri": "http://sandbox.orcid.org/client/APP-5ZVH4JRQ0C27RVH5",
                                        "path": "APP-5ZVH4JRQ0C27RVH5",
                                        "host": "sandbox.orcid.org"
                                    },
                                    "source-name": {
                                        "value": "The University of Auckland - MyORCiD"
                                    }
                                },
                                "external-ids": {
                                    "external-id": [
                                        {
                                            "external-id-type": "source-work-id",
                                            "external-id-value": "122334",
                                            "external-id-url": {
                                                "value": "https://localsystem.org/1234"
                                            },
                                            "external-id-relationship": "SELF"
                                        }
                                    ]
                                },
                                "review-group-id": "issn:12131",
                                "convening-organization": {
                                    "name": "The University of Auckland",
                                    "address": {
                                        "city": "Auckland",
                                        "region": "Auckland",
                                        "country": "NZ"
                                    },
                                    "disambiguated-organization": None
                                },
                                "visibility": "PUBLIC",
                                "put-code": 2622,
                            }
                        ]
                    }
                ],
                "path": "/0000-0003-1255-9023/peer-reviews"
            },
            'works': {
                'group': [{
                    'external-ids': {
                        'external-id': [{
                            'external-id-type': 'grant_number',
                            'external-id-value': 'GNS1701',
                            'external-id-url': None,
                            'external-id-relationship': 'SELF'
                        }]
                    },
                    'work-summary': [{
                        'source': {
                            'source-orcid': None,
                            'source-client-id': {
                                'uri': 'http://sandbox.orcid.org/client/APP-5ZVH4JRQ0C27RVH5',
                                'path': 'APP-5ZVH4JRQ0C27RVH5',
                                'host': 'sandbox.orcid.org'
                            },
                            'source-name': {
                                'value': 'The University of Auckland - MyORCiD'
                            }
                        },
                        'title': {
                            'title': {
                                'value': 'Test titile2'
                            },
                            'translated-title': {
                                'value': 'नमस्ते',
                                'language-code': 'hi'
                            }
                        },
                        'type': 'BOOK_CHAPTER',
                        'put-code': 9597,
                        'path': '/0000-0002-3879-2651/works/9597'
                    }]
                }],
                'path':
                    '/0000-0002-3879-2651/works'
            },
            'path': '/0000-0002-3879-2651/activities'
        },
        'path': '/0000-0002-3879-2651'
    }


def create_or_update_fund_mock(self=None, orcid=None, **kwargs):
    """Mock funding api call."""
    v = make_response
    v.status = 201
    v.headers = {'Location': '12344/xyz/12399'}
    return v


def create_or_update_aff_mock(affiliation=None, task_by_user=None, *args, **kwargs):
    """Mock affiliation api call."""
    v = make_response
    v.status = 201
    v.headers = {'Location': '12344/xyz/12399'}
    return v


def test_create_or_update_funding(app, mocker):
    """Test create or update funding."""
    mocker.patch("orcid_hub.utils.send_email", send_mail_mock)
    mocker.patch(
        "orcid_api.MemberAPIV20Api.create_funding", create_or_update_fund_mock)
    mocker.patch("orcid_hub.orcid_client.MemberAPI.get_record", return_value=get_profile())

    org = app.data["org"]
    u = User.create(
        email="test1234456@mailinator.com",
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid="123",
        confirmed=True,
        organisation=org)

    UserOrg.create(user=u, org=org)

    t = Task.create(org=org, filename="xyz.json", created_by=u, updated_by=u, task_type=1)

    fr = FundingRecord.create(
        task=t,
        title="Test titile",
        translated_title="Test title",
        translated_title_language_code="Test",
        type="GRANT",
        organization_defined_type="Test org",
        short_description="Test desc",
        amount="1000",
        currency="USD",
        org_name="Test_orgname",
        city="Test city",
        region="Test",
        country="Test",
        disambiguated_org_identifier="Test_dis",
        disambiguation_source="Test_source",
        is_active=True)

    FundingInvitee.create(
        funding_record=fr,
        first_name="Test",
        email="test1234456@mailinator.com",
        visibility="PUBLIC",
        orcid="123")

    ExternalId.create(
        funding_record=fr, type="Test_type", value="Test_value", url="Test", relationship="SELF")

    FundingContributor.create(
        funding_record=fr, orcid="1213", role="LEAD", name="Contributor", email="contributor@mailinator.com")

    UserInvitation.create(
        invitee=u,
        inviter=u,
        org=org,
        task=t,
        email="test1234456@mailinator.com",
        token="xyztoken")

    OrcidToken.create(
        user=u, org=org, scope="/read-limited,/activities/update", access_token="Test_token")

    utils.process_funding_records()
    funding_invitees = FundingInvitee.get(orcid=12344)
    assert 12399 == funding_invitees.put_code
    assert "12344" == funding_invitees.orcid


def test_create_or_update_work(app, mocker):
    """Test create or update work."""
    mocker.patch("orcid_hub.utils.send_email", send_mail_mock)
    mocker.patch("orcid_api.MemberAPIV20Api.create_work", create_or_update_fund_mock)
    mocker.patch("orcid_hub.orcid_client.MemberAPI.get_record", return_value=get_profile())

    org = app.data["org"]
    u = User.create(
        email="test1234456@mailinator.com",
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid="12344",
        confirmed=True,
        organisation=org)

    UserOrg.create(user=u, org=org)

    t = Task.create(org=org, filename="xyz.json", created_by=u, updated_by=u, task_type=2)

    wr = WorkRecord.create(
        task=t,
        title="Test titile",
        sub_title="Test titile",
        translated_title="Test title",
        translated_title_language_code="Test",
        journal_title="Test titile",
        short_description="Test desc",
        citation_type="Test",
        citation_value="Test",
        type="BOOK_CHAPTER",
        url="Test org",
        language_code="en",
        country="Test",
        org_name="Test_orgname",
        city="Test city",
        region="Test",
        is_active=True)

    WorkInvitee.create(
        work_record=wr,
        first_name="Test",
        email="test1234456@mailinator.com",
        orcid="12344",
        visibility="PUBLIC")

    WorkExternalId.create(
        work_record=wr, type="Test_type", value="Test_value", url="Test", relationship="SELF")

    WorkContributor.create(
        work_record=wr, contributor_sequence="1", orcid="1213", role="LEAD", name="xyz", email="xyz@mailiantor.com")

    UserInvitation.create(
        invitee=u,
        inviter=u,
        org=org,
        task=t,
        email="test1234456@mailinator.com",
        token="xyztoken")

    OrcidToken.create(
        user=u, org=org, scope="/read-limited,/activities/update", access_token="Test_token")

    utils.process_work_records()
    work_invitees = WorkInvitee.get(orcid=12344)
    assert 12399 == work_invitees.put_code
    assert "12344" == work_invitees.orcid


def test_create_or_update_peer_review(app, mocker):
    """Test create or update peer review."""
    mocker.patch("orcid_hub.utils.send_email", send_mail_mock)
    mocker.patch("orcid_api.MemberAPIV20Api.create_peer_review", create_or_update_fund_mock)
    mocker.patch("orcid_hub.orcid_client.MemberAPI.get_record", return_value=get_profile())
    org = app.data["org"]
    u = User.create(
        email="test1234456@mailinator.com",
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid="12344",
        confirmed=True,
        organisation=org)

    UserOrg.create(user=u, org=org)

    t = Task.create(id=12, org=org, filename="xyz.json", created_by=u, updated_by=u, task_type=3)
    pr = PeerReviewRecord.create(
        task=t,
        review_group_id="issn:12131",
        reviewer_role="reviewer",
        review_url="xyz",
        review_type="REVIEW",
        subject_external_id_type="doi",
        subject_external_id_value="1212",
        subject_external_id_url="url/SELF",
        subject_external_id_relationship="SELF",
        subject_container_name="Journal title",
        subject_type="JOURNAL_ARTICLE",
        subject_name_title="name",
        subject_name_subtitle="subtitle",
        subject_name_translated_title_lang_code="en",
        subject_name_translated_title="sdsd",
        subject_url="url",
        convening_org_name="THE ORGANISATION",
        convening_org_city="auckland",
        convening_org_region="auckland",
        convening_org_country="nz",
        convening_org_disambiguated_identifier="123",
        convening_org_disambiguation_source="1212",
        is_active=True)

    PeerReviewInvitee.create(
        peer_review_record=pr,
        first_name="Test",
        email="test1234456@mailinator.com",
        orcid="12344",
        visibility="PUBLIC")

    PeerReviewExternalId.create(
        peer_review_record=pr, type="Test_type", value="122334_different", url="Test", relationship="SELF")

    UserInvitation.create(
        invitee=u,
        inviter=u,
        org=org,
        task=t,
        email="test1234456@mailinator.com",
        token="xyztoken")

    OrcidToken.create(
        user=u, org=org, scope="/read-limited,/activities/update", access_token="Test_token")

    utils.process_peer_review_records()
    peer_review_invitees = PeerReviewInvitee.get(orcid=12344)
    assert 12399 == peer_review_invitees.put_code
    assert "12344" == peer_review_invitees.orcid


def test_create_or_update_researcher_url(app, mocker):
    """Test create or update researcher url."""
    mocker.patch("orcid_hub.utils.send_email", send_mail_mock)
    mocker.patch("orcid_api.MemberAPIV20Api.create_researcher_url", create_or_update_fund_mock)
    mocker.patch("orcid_hub.orcid_client.MemberAPI.get_record", return_value=get_profile())
    org = app.data["org"]
    u = User.create(
        email="test1234456@mailinator.com",
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid="12344",
        confirmed=True,
        organisation=org)

    UserOrg.create(user=u, org=org)

    t = Task.create(id=12, org=org, filename="xyz.json", created_by=u, updated_by=u, task_type=5)

    ResearcherUrlRecord.create(
        task=t,
        is_active=True,
        status="email sent",
        first_name="Test",
        last_name="Test",
        email="test1234456@mailinator.com",
        visibility="PUBLIC",
        url_name="url name",
        url_value="https://www.xyz.com",
        display_index=0)

    UserInvitation.create(
        invitee=u,
        inviter=u,
        org=org,
        task=t,
        email="test1234456@mailinator.com",
        token="xyztoken")

    OrcidToken.create(
        user=u, org=org, scope="/read-limited,/person/update", access_token="Test_token")

    utils.process_researcher_url_records()
    researcher_url_record = ResearcherUrlRecord.get(email="test1234456@mailinator.com")
    assert 12399 == researcher_url_record.put_code
    assert "12344" == researcher_url_record.orcid


def test_create_or_update_other_name(app, mocker):
    """Test create or update researcher other name."""
    mocker.patch("orcid_hub.utils.send_email", send_mail_mock)
    mocker.patch("orcid_api.MemberAPIV20Api.create_other_name", create_or_update_fund_mock)
    mocker.patch("orcid_hub.orcid_client.MemberAPI.get_record", return_value=get_profile())
    org = app.data["org"]
    u = User.create(
        email="test1234456@mailinator.com",
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid="12344",
        confirmed=True,
        organisation=org)

    UserOrg.create(user=u, org=org)

    t = Task.create(id=12, org=org, filename="xyz.json", created_by=u, updated_by=u, task_type=5)

    OtherNameRecord.create(
        task=t,
        is_active=True,
        status="email sent",
        first_name="Test",
        last_name="Test",
        email="test1234456@mailinator.com",
        visibility="PUBLIC",
        content="dummy name",
        display_index=0)

    UserInvitation.create(
        invitee=u,
        inviter=u,
        org=org,
        task=t,
        email="test1234456@mailinator.com",
        token="xyztoken")

    OrcidToken.create(
        user=u, org=org, scope="/read-limited,/person/update", access_token="Test_token")

    utils.process_other_name_records()
    other_name_record = OtherNameRecord.get(email="test1234456@mailinator.com")
    assert 12399 == other_name_record.put_code
    assert "12344" == other_name_record.orcid


@patch(
    "orcid_api.MemberAPIV20Api.update_employment",
    return_value=Mock(status=201, headers={'Location': '12344/XYZ/12399'}))
@patch(
    "orcid_api.MemberAPIV20Api.create_employment",
    return_value=Mock(status=201, headers={'Location': '12344/XYZ/12399'}))
@patch("orcid_hub.utils.send_email")
def test_create_or_update_affiliation(send_email, update_employment, create_employment, app):
    """Test create or update affiliation."""
    org = app.data["org"]
    u = User.create(
        email="test1234456@mailinator.com",
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid="123",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=u, org=org)
    t = Task.create(org=org, filename="xyz.json", created_by=u, updated_by=u, task_type=0)
    OrcidToken.create(
        user=u, org=org, scope="/read-limited,/activities/update", access_token="Test_token")
    UserInvitation.create(
        invitee=u,
        inviter=u,
        org=org,
        task=t,
        email="test1234456@mailinator.com",
        token="xyztoken")

    u = User.create(
        email="test1234456_2@mailinator.com",
        name="TEST USER 2",
        roles=Role.RESEARCHER,
        confirmed=True,
        organisation=org)
    UserOrg.create(user=u, org=org)

    AffiliationRecord.create(
        is_active=True,
        task=t,
        external_id="Test",
        first_name="Test",
        last_name="Test",
        email="test1234456@mailinator.com",
        orcid="123112311231",
        organisation="asdasd",
        affiliation_type="staff",
        role="Test",
        department="Test",
        city="Test",
        state="Test",
        country="Test",
        disambiguated_id="Test",
        disambiguation_source="Test")
    AffiliationRecord.create(
        is_active=True,
        task=t,
        external_id="Test",
        first_name="Test",
        last_name="Test",
        email="test1234456@mailinator.com",
        orcid="123112311231",
        organisation=org.name,
        affiliation_type="staff",
        role="Test",
        department="Test",
        city="Test",
        state="Test",
        country="Test")
    AffiliationRecord.create(
        is_active=True,
        task=t,
        external_id="Test",
        first_name="Test",
        last_name="Test",
        email="test1234456@mailinator.com",
        orcid="123112311231",
        organisation="ANOTHER ORG",
        affiliation_type="staff",
        role="Test",
        department="Test",
        city="Test",
        state="Test",
        country="Test")
    AffiliationRecord.create(
        is_active=True,
        task=t,
        external_id="Test#2",
        first_name="Test2",
        last_name="Test2",
        email="test1234456_2@mailinator.com",
        organisation=org.name,
        affiliation_type="staff")

    tasks = (Task.select(
        Task, AffiliationRecord, User, UserInvitation.id.alias("invitation_id"), OrcidToken).join(
            AffiliationRecord, on=(Task.id == AffiliationRecord.task_id)).join(
                User,
                JOIN.LEFT_OUTER,
                on=((User.email == AffiliationRecord.email)
                    | (User.orcid == AffiliationRecord.orcid))).join(
                        Organisation, JOIN.LEFT_OUTER, on=(Organisation.id == Task.org_id)).join(
                            UserInvitation,
                            JOIN.LEFT_OUTER,
                            on=((UserInvitation.email == AffiliationRecord.email)
                                & (UserInvitation.task_id == Task.id))).join(
                                    OrcidToken,
                                    JOIN.LEFT_OUTER,
                                    on=((OrcidToken.user_id == User.id)
                                        & (OrcidToken.org_id == Organisation.id)
                                        & (OrcidToken.scope.contains("/activities/update")))))
    app.config["SERVER_NAME"] = "orcidhub"
    for (task_id, org_id, user), tasks_by_user in groupby(tasks, lambda t: (
            t.id,
            t.org_id,
            t.affiliation_record.user, )):
        with patch(
                "orcid_hub.orcid_client.MemberAPI.get_record",
                return_value=get_profile() if user.orcid else None) as get_record:
            utils.create_or_update_affiliations(user=user, org_id=org_id, records=tasks_by_user)
            get_record.assert_any_call()
    affiliation_record = AffiliationRecord.select().order_by(AffiliationRecord.id).limit(1).first()
    assert 12399 == affiliation_record.put_code
    assert "12344" == affiliation_record.orcid
    assert ("Employment record was updated" in affiliation_record.status
            or "Employment record was created" in affiliation_record.status)
    send_email.assert_called_once()


def test_send_email(app):
    """Test emailing."""
    server_name = app.config.get("SERVER_NAME")
    app.config["SERVER_NAME"] = "abc.orcidhub.org.nz"
    with app.app_context():

        with patch("emails.message.Message") as msg_cls, patch("flask.current_app.jinja_env"):
            msg = msg_cls.return_value = Mock()
            app.config["SERVER_NAME"] = "abc.orcidhub.org.nz"
            utils.send_email(
                "template.html", (
                    "TEST USER",
                    "test123@test0.edu",
                ), subject="TEST")

            msg_cls.assert_called_once()
            msg.send.assert_called_once()

            msg.reset_mock()
            dkip_key_path = app.config["DKIP_KEY_PATH"]
            app.config["DKIP_KEY_PATH"] = __file__
            utils.send_email(
                "template", (
                    "TEST USER",
                    "test123@test0.edu",
                ), base="BASE", subject="TEST")
            msg.dkim.assert_called_once()
            msg.send.assert_called_once()

            msg.reset_mock()
            app.config["DKIP_KEY_PATH"] = "NON-EXISTING FILE..."
            utils.send_email(
                "template", (
                    "TEST USER",
                    "test123@test0.edu",
                ), base="BASE", subject="TEST")
            msg.dkim.assert_not_called()
            msg.send.assert_called_once()
            app.config["DKIP_KEY_PATH"] = dkip_key_path

            # User organisation's logo
            msg.reset_mock()
            logo_file = File.create(
                filename="LOGO.png",
                data=b"000000000000000000000",
                mimetype="image/png",
                token="TOKEN000")
            org = Organisation.create(
                name="THE ORGANISATION:test_send_email",
                tuakiri_name="THE ORGANISATION:test_send_email",
                confirmed=True,
                orcid_client_id="APP-5ZVH4JRQ0C27RVH5",
                orcid_secret="Client Secret",
                city="CITY",
                logo=logo_file,
                country="COUNTRY",
                disambiguation_org_id="ID",
                disambiguation_org_source="SOURCE")
            utils.send_email(
                "template", (
                    "TEST USER",
                    "test123@test0.edu",
                ),
                base="BASE {LOGO}",
                subject="TEST WITH BASE AND LOGO",
                org=org)
            msg.send.assert_called_once()
            _, kwargs = msg_cls.call_args
            assert kwargs["subject"] == "TEST WITH BASE AND LOGO"
            assert kwargs["mail_from"] == (
                "NZ ORCID HUB",
                "no-reply@orcidhub.org.nz",
            )
            expected_html = f"BASE http://{app.config['SERVER_NAME'].lower()}/logo/TOKEN000"
            assert kwargs["html"] == expected_html
            assert kwargs["text"] == expected_html + "\n\n"

            # Using organisation template
            msg.reset_mock()
            org.email_template = "TEMPLATE {LOGO}"
            org.email_template_enabled = True
            org.save()
            utils.send_email(
                "template", (
                    "TEST USER",
                    "test123@test0.edu",
                ),
                sender=(
                    None,
                    None,
                ),
                subject="TEST WITH ORG BASE AND LOGO",
                org=org)
            msg.send.assert_called_once()
            _, kwargs = msg_cls.call_args
            assert kwargs["subject"] == "TEST WITH ORG BASE AND LOGO"
            assert kwargs["mail_from"] == (
                "NZ ORCID HUB",
                "no-reply@orcidhub.org.nz",
            )
            expected_html = f"TEMPLATE http://{app.config['SERVER_NAME'].lower()}/logo/TOKEN000"
            assert kwargs["html"] == expected_html
            assert kwargs["text"] == expected_html + "\n\n"

        # temlates w/o extension and missing template file
        # login_user(super_user)
        from jinja2.exceptions import TemplateNotFound

        with pytest.raises(TemplateNotFound):
            utils.send_email(
                "missing_template.html", (
                    "TEST USER",
                    "test123@test0.edu",
                ),
                logo="LOGO",
                subject="TEST")
    app.config["SERVER_NAME"] = server_name


def test_is_valid_url():
    """Test URL validation for call-back URLs."""
    assert utils.is_valid_url("http://www.orcidhub.org.nz/some_path")
    assert utils.is_valid_url("http://www.orcidhub.org.nz")
    assert not utils.is_valid_url("www.orcidhub.org.nz/some_path")
    assert not utils.is_valid_url(12345)


def test_sync_profile(app, mocker):
    """Test sync_profile."""
    mocker.patch(
        "orcid_api.MemberAPIV20Api.update_employment",
        return_value=Mock(status=201, headers={'Location': '12344/XYZ/54321'}))
    mocker.patch(
        "orcid_api.MemberAPIV20Api.update_education",
        return_value=Mock(status=201, headers={'Location': '12344/XYZ/12345'}))

    def sync_profile_mock(*args, **kwargs):
        utils.sync_profile(*args, **kwargs)
        return Mock(id="test-test-test-test")
    mocker.patch("orcid_hub.utils.sync_profile.queue", sync_profile_mock)

    org = Organisation.create(
        name="THE ORGANISATION:test_sync_profile",
        tuakiri_name="THE ORGANISATION:test_sync_profile",
        confirmed=True,
        orcid_client_id="APP-5ZVH4JRQ0C27RVH5",
        orcid_secret="Client Secret",
        city="CITY",
        country="COUNTRY",
        disambiguated_id="ID",
        disambiguation_source="SOURCE")
    u = User.create(
        email="test1234456@mailinator.com",
        name="TEST USER",
        roles=Role.RESEARCHER,
        orcid="12344",
        confirmed=True,
        organisation=org)
    UserOrg.create(user=u, org=org)

    utils.sync_profile(task_id=999999)

    t = Task.create(org=org, task_type=TaskType.SYNC)

    mocker.patch("orcid_hub.orcid_client.MemberAPI.get_record", lambda *args: None)
    utils.sync_profile(task_id=t.id, delay=0)

    resp = get_profile()
    mocker.patch("orcid_hub.orcid_client.MemberAPI.get_record", lambda *args: resp)
    utils.sync_profile(task_id=t.id, delay=0)

    resp["activities-summary"]["educations"]["education-summary"] = []
    mocker.patch("orcid_hub.orcid_client.MemberAPI.get_record", lambda *args: resp)
    utils.sync_profile(task_id=t.id, delay=0)

    mocker.patch(
        "orcid_hub.orcid_client.MemberAPI.update_employment", side_effect=Exception("FAILED"))
    utils.sync_profile(task_id=t.id, delay=0)

    resp["activities-summary"]["employments"]["employment-summary"][0]["source"] = None
    resp["activities-summary"]["employments"]["employment-summary"][0]["source"] = None
    mocker.patch("orcid_hub.orcid_client.MemberAPI.get_record", lambda *args: resp)
    utils.sync_profile(task_id=t.id, delay=0)

    org.disambiguated_id = None
    org.save()
    utils.sync_profile(task_id=t.id, delay=0)

    assert Log.select().count() > 0


def test_process_tasks(app, mocker):
    """Test task hanging."""
    send_email = mocker.patch("orcid_hub.utils.send_email")
    org = Organisation.select().first()
    Task.insert_many(dict(
        org=org,
        updated_at=utils.datetime.utcnow(),
        filename=tt.name,
        task_type=tt.value) for tt in TaskType).execute()
    utils.process_tasks()
    send_email.assert_not_called()

    Task.insert_many(dict(
        org=org,
        created_by=org.tech_contact,
        created_at=utils.datetime(2017, 1, 1),
        updated_at=utils.datetime(2017, 1, 1),
        filename=tt.name,
        task_type=tt.value) for tt in TaskType).execute()
    utils.process_tasks()
    send_email.assert_called()

    task_count = Task.select().count()
    utils.process_tasks()
    assert Task.select().count() == task_count // 2


def test_file_upload_with_encodings(client, mocker):
    """Test BOM handling in the uploaded file."""
    client.login_root()
    for no, (e, bom) in enumerate([
            ("utf-8", None),
            ("utf-8", codecs.BOM_UTF8),
            ("utf-16", None),
            ("utf-16", codecs.BOM_UTF16),
            ("utf-32", None),
            ("utf-32", codecs.BOM_UTF32),
    ]):
        data = f"disambiguated id,disambiguation source,name\n123,ABC,대학 #{no} WITH {e}".encode(e)
        if bom:
            data = bom + data
        resp = client.post(
            "/load/org",
            follow_redirects=True,
            data={
                "save":
                "Upload",
                "file_": (
                    BytesIO(data),
                    "raw-org-data-with-bom.csv",
                ),
            })
        assert resp.status_code == 200
        assert OrgInfo.select().count() == no + 1


def test_new_invitation_token(app):
    """Test if the tokens are realy unique."""
    random.seed(42)
    token0 = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5))
    random.seed(42)
    token = utils.new_invitation_token()
    assert token == token0
    org, user, admin = [app.data[n] for n in ["org", "user", "admin"]]

    UserInvitation.create(org=org, invitee=user, inviter=admin, token=token)
    random.seed(42)
    token2 = utils.new_invitation_token()
    assert token2 != token


def test_get_next_url(client):
    """Test 'get_next_url'."""
    client.login_root()
    client.post(
            "/admin/delegate/new/", data=dict(hostname="test.delegate.com"), follow_redirects=True)

    for url in [
            "/admin/delegate/",
            "http://test.orcidhub.org.nz/ABC",
            "http://127.0.0.1/TEST",
            "http://c9users.io/test",
            "http://delegate.com/test",
    ]:
        with client.get(f"/?_next={quote(url)}"):
            assert utils.get_next_url() == url

    for url in [
            "https://test.malicious.org.nz/ABC",
    ]:
        with client.get(f"/?_next={quote(url)}"):
            assert utils.get_next_url() is None
