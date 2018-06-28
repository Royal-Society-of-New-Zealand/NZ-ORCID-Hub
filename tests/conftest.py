# -*- coding: utf-8 -*-
"""Py.test configuration and fixtures for testing.

isort:skip_file
"""

# yapf: disable
import os
import sys
import logging
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# flake8: noqa
from orcid_hub import config
DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or "sqlite:///:memory:"
config.DATABASE_URL = DATABASE_URL
os.environ["DATABASE_URL"] = DATABASE_URL
# Patch it before is gets patched by 'orcid_client'
# import orcid_api
# from unittest.mock import MagicMock
# RESTClientObject = orcid_api.api_client.RESTClientObject = MagicMock(orcid_api.api_client.RESTClientObject)
# yapf: enable


import pytest
from playhouse import db_url
from playhouse.test_utils import test_database

from orcid_hub import app as _app
_app.config["DATABASE_URL"] = DATABASE_URL
from orcid_hub.models import *  # noqa: F401, F403
from orcid_hub.authcontroller import *  # noqa: F401, F403
from orcid_hub.views import *  # noqa: F401, F403
from orcid_hub.reports import *  # noqa: F401, F403

db = _app.db = _db = db_url.connect(DATABASE_URL, autorollback=True)


@pytest.yield_fixture
def app():
    """Session-wide test `Flask` application."""
    # Establish an application context before running the tests.
    ctx = _app.app_context()
    ctx.push()
    _app.config['TESTING'] = True
    logger = logging.getLogger("peewee")
    if logger:
        logger.setLevel(logging.INFO)

    with test_database(
            _db,
        (File, Organisation, User, UserOrg, OrcidToken, UserOrgAffiliation, OrgInfo, Task,
         AffiliationRecord, FundingRecord, FundingContributor, FundingInvitees, OrcidAuthorizeCall, OrcidApiCall,
         Url, UserInvitation, OrgInvitation, ExternalId, Client, Grant, Token, WorkRecord, WorkContributor,
         WorkExternalId, WorkInvitees, PeerReviewRecord, PeerReviewInvitee, PeerReviewExternalId), fail_silently=True):  # noqa: F405
        _app.db = _db
        _app.config["DATABASE_URL"] = DATABASE_URL
        _app.config["EXTERNAL_SP"] = None
        _app.config["SENTRY_DSN"] = None
        _app.config["WTF_CSRF_ENABLED"] = False
        _app.config["DEBUG_TB_ENABLED"] = False
        #_app.config["SERVER_NAME"] = "ORCIDHUB"
        _app.sentry = None

        # Add some data:
        for org_no in range(2):
            org = Organisation.create(
                name=f"TEST{org_no}",
                tuakiri_name=f"TEST ORG #{org_no}")
            if org_no == 1:
                org.orcid_client_id = "ABC123"
                org.orcid_secret = "SECRET-12345"
                org.save()

            # An org.admin
            user = User.create(
                created_at=datetime(2017, 11, 28),
                email=f"admin@test{org_no}.edu",
                name=f"TEST ORG #{org_no} ADMIN",
                first_name="FIRST_NAME",
                last_name="LAST_NAME",
                can_use_api=(org_no == 0),
                confirmed=True,
                organisation=org)
            UserOrg.create(user=user, org=org, is_admin=True)
            org.tech_contact = user
            org.save()
            # Hub admin:
            User.create(
                created_at=datetime(2017, 11, 27),
                email=f"root@test{org_no}.edu",
                name="TEST HUB ADMIN",
                first_name="FIRST_NAME",
                last_name="LAST_NAME",
                roles=Role.SUPERUSER,
                confirmed=True,
                organisation=org)
            User.insert_many(
                dict(
                    email=f"researcher{i}@test{org_no}.edu",
                    name=f"TEST RESEARCHER #{i} OF {org_no} ",
                    first_name=f"FIRST_NAME #{i}",
                    last_name=f"LAST_NAME #{i}",
                    confirmed=True,
                    organisation=org,
                    created_at=datetime(2017, 12, i % 31 + 1)) for i in range(100, 107)).execute()
            OrcidToken.insert_many(
                dict(
                    access_token=f"TOKEN-{org_no}-{u.id}",
                    org=org,
                    user=u,
                    expires_in=0,
                    created_at=datetime(2018, 1, 1)) for u in User.select(User.id)
                if u.id % 2 == 0).execute()
            if org_no == 0:
                Client.create(org=org, user=user, client_id=org.name + "-ID", client_secret=org.name + "-SECRET")
        UserOrg.insert_from(
            query=User.select(User.id, User.organisation_id, User.created_at).where(
                User.email.contains("researcher")),
            fields=[UserOrg.user_id, UserOrg.org_id, UserOrg.created_at]).execute()

        yield _app

    ctx.pop()
    return


@pytest.fixture
def client(app):
    """A Flask test client. An instance of :class:`flask.testing.TestClient` by default."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def request_ctx(app):
    """Request context creator."""
    def make_ctx(*args, **kwargs):
        return app.test_request_context(*args, **kwargs)

    return make_ctx


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
    tech_contact = admin

    UserOrg.create(user=admin, org=org, is_admin=True)
    org.tech_contact = admin
    org.save()
    request_ctx.org = org

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
    UserOrg.create(user=user, org=org)

    User.insert_many(
        dict(
            email=f"researcher{i}@test0.edu",
            name=f"TEST RESEARCHER #{i}",
            first_name=f"FIRST_NAME #{i}",
            last_name=f"LAST_NAME #{i}",
            confirmed=True,
            organisation=org,
            created_at=datetime(2017, 12, i % 31 + 1),
            updated_at=datetime(2017, 12, i % 31 + 1)) for i in range(200, 207)).execute()

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

    super_user = User.create(
        email="super_user@test0.edu", organisation=org, roles=Role.SUPERUSER, confirmed=True)

    request_ctx.data = locals()

    return request_ctx
