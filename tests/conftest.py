# -*- coding: utf-8 -*-
"""Py.test configuration and fixtures for testing.

isort:skip_file
"""

# yapf: disable
import os
import sys
import logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# flake8: noqa
from orcid_hub import config
DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or "sqlite:///:memory:"
config.DATABASE_URL = DATABASE_URL
os.environ["DATABASE_URL"] = DATABASE_URL
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
        (Organisation, User, UserOrg, OrcidToken, UserOrgAffiliation, OrgInfo, Task,
         AffiliationRecord, FundingRecord, FundingContributor, OrcidAuthorizeCall, OrcidApiCall, Url,
         UserInvitation, OrgInvitation, ExternalId, Client),
            fail_silently=True):  # noqa: F405
        _app.db = _db
        _app.config["DATABASE_URL"] = DATABASE_URL
        _app.config["EXTERNAL_SP"] = None
        _app.config["SENTRY_DSN"] = None
        _app.config["WTF_CSRF_ENABLED"] = False
        _app.sentry = None

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
