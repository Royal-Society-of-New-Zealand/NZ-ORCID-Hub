# -*- coding: utf-8 -*-
"""Py.test configuration and fixtures for testing.

isort:skip_file
"""

# yapf: disable
import os
import sys
import logging
from datetime import datetime
from flask_login import logout_user
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# flake8: noqa
from orcid_hub import config
DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or "sqlite:///:memory:"
config.DATABASE_URL = DATABASE_URL
config.RQ_CONNECTION_CLASS = "fakeredis.FakeStrictRedis"
os.environ["DATABASE_URL"] = DATABASE_URL
# Patch it before is gets patched by 'orcid_client'
# import orcid_api
# from unittest.mock import MagicMock
# RESTClientObject = orcid_api.api_client.RESTClientObject = MagicMock(orcid_api.api_client.RESTClientObject)
# yapf: enable

from flask.testing import FlaskClient
from flask import _request_ctx_stack

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

ORCIDS = [
    "1009-2009-3009-00X3", "1017-2017-3017-00X3", "1025-2025-3025-00X3", "1033-2033-3033-00X3",
    "1041-2041-3041-00X3", "1068-2068-3068-00X3", "1076-2076-3076-00X3", "1084-2084-3084-00X3",
    "1092-2092-3092-00X3", "1105-2105-3105-00X3", "1113-2113-3113-00X3", "1121-2121-3121-00X3",
    "1148-2148-3148-00X3", "1156-2156-3156-00X3", "1164-2164-3164-00X3", "1172-2172-3172-00X3",
    "1180-2180-3180-00X3", "1199-2199-3199-00X3", "1201-2201-3201-00X3", "1228-2228-3228-00X3",
    "1236-2236-3236-00X3", "1244-2244-3244-00X3", "1252-2252-3252-00X3", "1260-2260-3260-00X3",
    "1279-2279-3279-00X3", "1287-2287-3287-00X3", "1295-2295-3295-00X3", "1308-2308-3308-00X3",
    "1316-2316-3316-00X3", "1324-2324-3324-00X3", "1332-2332-3332-00X3", "1340-2340-3340-00X3",
    "1359-2359-3359-00X3", "1367-2367-3367-00X3", "1375-2375-3375-00X3", "1383-2383-3383-00X3",
    "1391-2391-3391-00X3", "1404-2404-3404-00X3", "1412-2412-3412-00X3", "1420-2420-3420-00X3",
    "1439-2439-3439-00X3", "1447-2447-3447-00X3", "1455-2455-3455-00X3", "1463-2463-3463-00X3",
    "1471-2471-3471-00X3", "1498-2498-3498-00X3", "1500-2500-3500-00X3", "1519-2519-3519-00X3",
    "1527-2527-3527-00X3", "1535-2535-3535-00X3", "1543-2543-3543-00X3", "1551-2551-3551-00X3",
    "1578-2578-3578-00X3", "1586-2586-3586-00X3", "1594-2594-3594-00X3", "1607-2607-3607-00X3",
    "1615-2615-3615-00X3", "1623-2623-3623-00X3", "1631-2631-3631-00X3", "1658-2658-3658-00X3",
    "1666-2666-3666-00X3", "1674-2674-3674-00X3", "1682-2682-3682-00X3", "1690-2690-3690-00X3",
    "1703-2703-3703-00X3", "1711-2711-3711-00X3", "1738-2738-3738-00X3", "1746-2746-3746-00X3",
    "1754-2754-3754-00X3", "1762-2762-3762-00X3", "1770-2770-3770-00X3", "1789-2789-3789-00X3",
    "1797-2797-3797-00X3", "1818-2818-3818-00X3", "1826-2826-3826-00X3", "1834-2834-3834-00X3",
    "1842-2842-3842-00X3", "1850-2850-3850-00X3", "1869-2869-3869-00X3", "1877-2877-3877-00X3",
    "1885-2885-3885-00X3", "1893-2893-3893-00X3", "1906-2906-3906-00X3", "1914-2914-3914-00X3",
    "1922-2922-3922-00X3", "1930-2930-3930-00X3", "1949-2949-3949-00X3", "1957-2957-3957-00X3",
    "1965-2965-3965-00X3", "1973-2973-3973-00X3"
]


class HubClient(FlaskClient):
    """Extension of the default Flask test client."""

    resp_no = 0
    def login(self, user, affiliations=None, follow_redirects=False, **kwargs):
        """Log in with the given user."""
        org = user.organisation or user.organisations.first()
        if affiliations is None:
            uo = user.userorg_set.where(UserOrg.org == org).first()
            if uo and uo.affiliations:
                affiliations = ';'.join([
                    "staff" if a == Affiliation.EMP else "student" for a in Affiliation
                    if a & uo.affiliations
                ])
        headers = {
            k: v
            for k, v in [
                ("Auedupersonsharedtoken", "edu-person-shared-token"),
                ("Sn", user.last_name or "SURNAME"),
                ("Givenname", user.first_name or "GIVENNAME"),
                ("Mail", user.email),
                ("O", org.tuakiri_name or org.name),
                ("Displayname", user.name or "FULL NAME"),
                ("Unscoped-Affiliation", affiliations),
                ("Eppn", user.eppn or user.email),
            ] if v is not None
        }
        headers.update(kwargs)
        return self.get("/Tuakiri/login", headers=headers, follow_redirects=follow_redirects)

    def open(self, *args, **kwargs):
        """Save the last response."""
        self.resp = super().open(*args, **kwargs)
        if hasattr(self.resp, "data"):
            self.save_resp()
            self.resp_no += 1
        return self.resp

    def save_resp(self):
        """Save the response into 'output.html' file."""
        ext = "html"
        content_type = self.resp.headers.get("Content-Type")
        if content_type:
            if "json" in content_type:
                ext = "json"
            elif "yaml" in content_type:
                ext = "yaml"
            elif "csv" in content_type:
                ext = "csv"
        with open(f"output{self.resp_no:02d}.{ext}", "wb") as output:
            output.write(self.resp.data)

    def logout(self, follow_redirects=True):
        """Perform log-out."""
        resp = self.get("/logout", follow_redirects=follow_redirects)
        _request_ctx_stack.pop()
        self.cookie_jar.clear()
        return resp

    def login_root(self):
        """Log in with the first found Hub admin user."""
        root = User.select().where(User.roles.bin_and(Role.SUPERUSER)).first()
        return self.login(root)

    def get_access_token(self, client_id=None, client_secret=None):
        """Retrieve client credential access token for Hub API."""
        if client_id is None:
            client_id = "CLIENT_ID"
        if client_secret is None:
            client_secret = "CLIENT_SECRET"
        resp = self.post(
            "/oauth/token",
            content_type="application/x-www-form-urlencoded",
            data=f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}")
        data = json.loads(resp.data)
        return data["access_token"]


@pytest.fixture(autouse=True)
def no_mailing(mocker):
    """Mock HTML message for all tests."""
    yield mocker.patch("emails.html")


@pytest.fixture
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
        (File, Organisation, User, UserOrg, OrcidToken, UserOrgAffiliation, OrgInfo, Task, Log,
         AffiliationRecord, FundingRecord, FundingContributor, FundingInvitee, GroupIdRecord,
         OrcidAuthorizeCall, OrcidApiCall, Url, UserInvitation, OrgInvitation, ExternalId, Client,
         Grant, Token, WorkRecord, WorkContributor, WorkExternalId, WorkInvitee, PeerReviewRecord,
         PeerReviewInvitee, PeerReviewExternalId, ResearcherUrlRecord, OtherNameRecord, KeywordRecord),
            fail_silently=True):  # noqa: F405
        _app.db = _db
        _app.config["DATABASE_URL"] = DATABASE_URL
        _app.config["EXTERNAL_SP"] = None
        _app.config["SENTRY_DSN"] = None
        _app.config["WTF_CSRF_ENABLED"] = False
        _app.config["DEBUG_TB_ENABLED"] = False
        _app.config["LOAD_TEST"] = True
        #_app.config["SERVER_NAME"] = "ORCIDHUB"
        _app.sentry = None
        _app.config["RQ_CONNECTION_CLASS"] = "fakeredis.FakeStrictRedis"
        _app.extensions["rq2"].init_app(_app)

        # Add some data:
        for org_no in range(2):
            org = Organisation.create(name=f"TEST{org_no}", tuakiri_name=f"TEST ORG #{org_no}")
            User.create(
                created_at=datetime(2017, 11, 16),
                email=f"researcher_across_orgs@test{org_no}.edu",
                name="TEST USER ACROSS ORGS",
                first_name="FIRST_NAME",
                last_name="LAST_NAME",
                roles=Role.RESEARCHER,
                orcid="1981-2981-3981-00X3",
                confirmed=True,
                organisation=org)
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
                    orcid=ORCIDS[org_no * 10 + i - 100] if (org_no * 10 + i) % 2 else None,
                    confirmed=True,
                    organisation=org,
                    created_at=datetime(2017, 12, i % 31 + 1)) for i in range(100, 107)).execute()
            OrcidToken.insert_many(
                dict(
                    access_token=f"TOKEN-{org_no}-{u.id}",
                    scope="/read-limited,/activities/update",
                    org=org,
                    user=u,
                    expires_in=0,
                    created_at=datetime(2018, 1, 1)) for u in User.select(User.id)
                if u.id % 2 == 0).execute()
            if org_no == 0:
                Client.create(
                    org=org,
                    user=user,
                    client_id=org.name + "-ID",
                    client_secret=org.name + "-SECRET")

        UserOrg.insert_from(
            query=User.select(User.id, User.organisation_id, User.created_at, SQL('0')).where(
                User.email.contains("researcher")),
            fields=[UserOrg.user_id, UserOrg.org_id, UserOrg.created_at,
                    UserOrg.affiliations]).execute()

        _app.test_client_class = HubClient
        org = Organisation.create(
            name="THE ORGANISATION",
            tuakiri_name="THE ORGANISATION",
            orcid_client_id="APP-12345678",
            orcid_secret="CLIENT-SECRET",
            confirmed=True,
            city="CITY",
            country="NZ")

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
        OrcidToken.create(user=user,
                          org=org,
                          scope="/read-limited,/activities/update",
                          access_token="ORCID-TEST-ACCESS-TOKEN")
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

        _app.data = locals()
        yield _app

    ctx.pop()
    return


@pytest.fixture
def client(app):
    """A Flask test client. An instance of :class:`flask.testing.TestClient` by default."""
    with app.test_client() as client:
        client.data = app.data
        yield client
    if "EXTERNAL_SP" in app.config:
        del(app.config["EXTERNAL_SP"])
    client.logout()


@pytest.fixture
def request_ctx(app):
    """Request context creator."""
    def make_ctx(*args, **kwargs):
        return app.test_request_context(*args, **kwargs)

    make_ctx.data = app.data
    return make_ctx


@pytest.fixture
def app_req_ctx(request_ctx):
    """Create the fixture for the request with a test organisation and a test tech.contatct."""
    app_req_ctx.data = request_ctx.data
    return request_ctx
