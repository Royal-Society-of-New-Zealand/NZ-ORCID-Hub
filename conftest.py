# -*- coding: utf-8 -*-
"""Py.test configuration and fixtures for testing.

isort:skip_file
"""

# yapf: disable
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# yapf: enable

import pytest
from peewee import SqliteDatabase
from playhouse.test_utils import test_database

import config
from application import app as _app
from authcontroller import *  # noqa: F401, F403
from views import *  # noqa: F401, F403


# flake8: noqa
config.DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///:memory:"
os.environ["DATABASE_URL"] = config.DATABASE_URL


@pytest.yield_fixture
def app():
    """Session-wide test `Flask` application."""
    # Establish an application context before running the tests.
    ctx = _app.app_context()
    ctx.push()
    _app.config['TESTING'] = True
    _app.db = _db = SqliteDatabase(":memory:")

    with test_database(_db, (Organisation, User, UserOrg, OrcidToken, UserOrgAffiliation,
                             OrgInfo)):  # noqa: F405
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
