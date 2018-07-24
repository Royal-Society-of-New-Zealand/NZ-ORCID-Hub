# -*- coding: utf-8 -*-
"""Py.test configuration and fixtures for testing.

isort:skip_file
"""

# yapf: disable
import os
import sys
import logging
from datetime import datetime
from peewee import SqliteDatabase
from itertools import product

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

from flask.testing import FlaskClient

import pytest
from playhouse import db_url

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
    "1965-2965-3965-00X3", "1973-2973-3973-00X3", "1981-2981-3981-00X3"
]


class HubClient(FlaskClient):
    """Extension of the default Flask test client."""
    def login(self, user, affiliations=None):
        """Log in with the given user."""
        org = user.organisation
        if affiliations is None:
            uo = user.userorg_set.where(models.UserOrg.org == org).first()
            if uo and uo.affiliations:
                affiliations = ';'.join([
                    "staff" if a == Affiliation.EMP else "student" for a in Affiliation
                    if a & uo.affiliations
                ])

        return self.get(
            "/Tuakiri/login",
            headers={
                "Auedupersonsharedtoken": "edu-person-shared-token",
                "Sn": user.last_name,
                'Givenname': user.first_name,
                "Mail": user.email,
                "O": org.tuakiri_name or org.name,
                "Displayname": user.name,
                "Unscoped-Affiliation": affiliations,
                "Eppn": user.eppn,
            })


@pytest.fixture
def test_db():
    """Peewee Test DB context.

    Example:

    def test_NAME(test_db):
        u = models.User(email="test@test.org", name="TESTER TESTERON")
        u.save()
        asser modls.User.count() == 1
    """
    _db = SqliteDatabase(":memory:")
    with _db.bind_ctx(MODELS):  # noqa: F405
        _app.db = _db
        _app.config["DATABASE_URL"] = "sqlite:///:memory:"
        _app.config["EXTERNAL_SP"] = None
        _app.config["SENTRY_DSN"] = None
        _app.config["WTF_CSRF_ENABLED"] = False
        _app.config["DEBUG_TB_ENABLED"] = False
        _app.config["SERVER_NAME"] = "ORCIDHUB"
        _app.sentry = None
        _db.create_tables(MODELS)

        yield _db

    return


@pytest.fixture
def test_models(test_db):

    Organisation.insert_many((dict(
        name="Organisation #%d" % i,
        tuakiri_name="Organisation #%d" % i,
        orcid_client_id="client-%d" % i,
        orcid_secret="secret-%d" % i,
        confirmed=(i % 2 == 0)) for i in range(10))).execute()

    User.insert_many((dict(
        name="Test User #%d" % i,
        first_name="Test_%d" % i,
        last_name="User_%d" % i,
        email="user%d@org%d.org.nz" % (i, i * 4 % 10),
        confirmed=(i % 3 != 0),
        roles=Role.SUPERUSER if i % 42 == 0 else Role.ADMIN if i % 13 == 0 else Role.RESEARCHER)
                      for i in range(60))).execute()

    User.insert_many((dict(
        name="Test User with ORCID ID 'ABC-123' #%d" % i,
        orcid="ABC-123",
        first_name="Test_%d" % i,
        last_name="User_%d" % i,
        email="user_the_same_id_%d@org%d.org.nz" % (i, i),
        confirmed=True,
        roles=Role.RESEARCHER) for i in range(3))).execute()

    UserOrg.insert_many((dict(is_admin=((u + o) % 23 == 0), user=u, org=o)
                         for (u, o) in product(range(2, 60, 4), range(2, 10)))).execute()

    UserOrg.insert_many((dict(is_admin=True, user=43, org=o) for o in range(1, 11))).execute()

    OrcidToken.insert_many((dict(
        user=User.get(id=1),
        org=Organisation.get(id=1),
        scope="/read-limited",
        access_token="Test_%d" % i) for i in range(60))).execute()

    UserOrgAffiliation.insert_many((dict(
        user=User.get(id=1),
        organisation=Organisation.get(id=1),
        department_name="Test_%d" % i,
        department_city="Test_%d" % i,
        role_title="Test_%d" % i,
        path="Test_%d" % i,
        put_code="%d" % i) for i in range(30))).execute()

    Task.insert_many((dict(
        org=Organisation.get(id=1),
        created_by=User.get(id=1),
        updated_by=User.get(id=1),
        filename="Test_%d" % i,
        task_type=0) for i in range(30))).execute()

    AffiliationRecord.insert_many((dict(
        is_active=False,
        task=Task.get(id=1),
        put_code=90,
        external_id="Test_%d" % i,
        status="Test_%d" % i,
        first_name="Test_%d" % i,
        last_name="Test_%d" % i,
        email="Test_%d" % i,
        orcid="123112311231%d" % i,
        organisation="Test_%d" % i,
        affiliation_type="Test_%d" % i,
        role="Test_%d" % i,
        department="Test_%d" % i,
        city="Test_%d" % i,
        state="Test_%d" % i,
        country="Test_%d" % i,
        disambiguated_id="Test_%d" % i,
        disambiguation_source="Test_%d" % i) for i in range(10))).execute()

    FundingRecord.insert_many((dict(
        task=Task.get(id=1),
        title="Test_%d" % i,
        translated_title="Test_%d" % i,
        translated_title_language_code="Test_%d" % i,
        type="Test_%d" % i,
        organization_defined_type="Test_%d" % i,
        short_description="Test_%d" % i,
        amount="Test_%d" % i,
        currency="Test_%d" % i,
        org_name="Test_%d" % i,
        city="Test_%d" % i,
        region="Test_%d" % i,
        country="Test_%d" % i,
        disambiguated_org_identifier="Test_%d" % i,
        disambiguation_source="Test_%d" % i,
        is_active=False,
        status="Test_%d" % i) for i in range(10))).execute()

    FundingContributor.insert_many((dict(
        funding_record=FundingRecord.get(id=1),
        orcid="123112311231%d" % i,
        name="Test_%d" % i,
        role="Test_%d" % i) for i in range(10))).execute()

    FundingInvitees.insert_many((dict(
        funding_record=FundingRecord.get(id=1),
        orcid="123112311231%d" % i,
        first_name="Test_%d" % i,
        last_name="Test_%d" % i,
        put_code=i,
        status="Test_%d" % i,
        identifier="%d" % i,
        visibility="Test_%d" % i,
        email="Test_%d" % i) for i in range(10))).execute()

    ExternalId.insert_many((dict(
        funding_record=FundingRecord.get(id=1),
        type="Test_%d" % i,
        value="Test_%d" % i,
        url="Test_%d" % i,
        relationship="Test_%d" % i) for i in range(10))).execute()

    PeerReviewRecord.insert_many((dict(
        task=Task.get(id=1),
        review_group_id="issn:1212_%d" % i,
        reviewer_role="reviewer_%d" % i,
        review_url="xyz_%d" % i,
        review_type="REVIEW_%d" % i,
        subject_external_id_type="doi_%d" % i,
        subject_external_id_value="1212_%d" % i,
        subject_external_id_url="url/SELF_%d" % i,
        subject_external_id_relationship="SELF_%d" % i,
        subject_container_name="Journal title_%d" % i,
        subject_type="JOURNAL_ARTICLE_%d" % i,
        subject_name_title="name_%d" % i,
        subject_name_subtitle="subtitle_%d" % i,
        subject_name_translated_title_lang_code="en",
        subject_name_translated_title="sdsd_%d" % i,
        subject_url="url_%d" % i,
        convening_org_name="THE ORGANISATION_%d" % i,
        convening_org_city="auckland_%d" % i,
        convening_org_region="auckland_%d" % i,
        convening_org_country="nz_%d" % i,
        convening_org_disambiguated_identifier="123_%d" % i,
        convening_org_disambiguation_source="1212_%d" % i,
        is_active=False) for i in range(10))).execute()

    PeerReviewExternalId.insert_many((dict(
        peer_review_record=PeerReviewRecord.get(id=1),
        type="Test1_%d" % i,
        value="Test1_%d" % i,
        url="Test1_%d" % i,
        relationship="Test1_%d" % i) for i in range(10))).execute()

    PeerReviewInvitee.insert_many((dict(
        peer_review_record=PeerReviewRecord.get(id=1),
        orcid="1231123112311%d" % i,
        first_name="Test1_%d" % i,
        last_name="Test1_%d" % i,
        put_code=i,
        status="Test1_%d" % i,
        identifier="1%d" % i,
        visibility = "PUBLIC",
        email="Test1_%d" % i) for i in range(10))).execute()

    WorkRecord.insert_many((dict(
        task=Task.get(id=1),
        title="Test_%d" % i,
        sub_title="Test_%d" % i,
        translated_title="Test_%d" % i,
        translated_title_language_code="Test_%d" % i,
        journal_title="Test_%d" % i,
        short_description="Test_%d" % i,
        citation_type="Test_%d" % i,
        citation_value="Test_%d" % i,
        type="Test_%d" % i,
        url="Test_%d" % i,
        language_code="Test_%d" % i,
        country="Test_%d" % i,
        is_active=False,
        status="Test_%d" % i) for i in range(10))).execute()

    WorkContributor.insert_many((dict(
        work_record=WorkRecord.get(id=1),
        orcid="123112311231%d" % i,
        name="Test_%d" % i,
        contributor_sequence="%d" % i,
        role="Test_%d" % i) for i in range(10))).execute()

    WorkExternalId.insert_many((dict(
        work_record=WorkRecord.get(id=1),
        type="Test_%d" % i,
        value="Test_%d" % i,
        url="Test_%d" % i,
        relationship="Test_%d" % i) for i in range(10))).execute()

    WorkInvitees.insert_many((dict(
        work_record=WorkRecord.get(id=1),
        orcid="123112311231%d" % i,
        first_name="Test_%d" % i,
        last_name="Test_%d" % i,
        put_code=i,
        status="Test_%d" % i,
        identifier="%d" % i,
        visibility="Test_%d" % i,
        email="Test_%d" % i) for i in range(10))).execute()

    yield test_db


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

    with _db.bind_ctx(MODELS):  # noqa: F405
        _app.db = _db
        _app.config["DATABASE_URL"] = DATABASE_URL
        _app.config["EXTERNAL_SP"] = None
        _app.config["SENTRY_DSN"] = None
        _app.config["WTF_CSRF_ENABLED"] = False
        _app.config["DEBUG_TB_ENABLED"] = False
        #_app.config["SERVER_NAME"] = "ORCIDHUB"
        _app.sentry = None
        _db.create_tables(MODELS)

        # Add some data:
        for org_no in range(2):
            org = Organisation.create(name=f"TEST{org_no}", tuakiri_name=f"TEST ORG #{org_no}")
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
            query=User.select(User.id, User.organisation_id, User.created_at).where(
                User.email.contains("researcher")),
            fields=[UserOrg.user_id, UserOrg.org_id, UserOrg.created_at]).execute()

        _app.test_client_class = HubClient
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
