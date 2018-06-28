# -*- coding: utf-8 -*-  # noqa
"""
    ORCID-Hub
    ~~~~~~~~~

    The New Zealand ORCID Hub allows all Consortium members to productively engage with ORCID
    regardless of technical resources. The technology partner, with oversight from
    the IT Advisory Group, lead agency and ORCID, will develop and maintain the Hub.

    :copyright: (c) 2017, 2018 Royal Society of New Zealand.
    :license: MIT, see LICENSE for more details.
"""

import logging
import os
import pkg_resources
import sys
from datetime import date, datetime

import click
from flask.json import JSONEncoder as _JSONEncoder
from flask_login import current_user, LoginManager
from flask import Flask, request
from flask_oauthlib.provider import OAuth2Provider
from flask_peewee.rest import Authentication, RestAPI
from flask_restful import Api
from peewee import PostgresqlDatabase
from playhouse import db_url
from playhouse.shortcuts import RetryOperationalError
# disable Sentry if there is no SENTRY_DSN:
from raven.contrib.flask import Sentry

from . import config
from .failover import PgDbWithFailover
from flask_admin import Admin
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


dist = pkg_resources.get_distribution(__name__)
__version__ = dist.version


# http://docs.peewee-orm.com/en/latest/peewee/database.html#automatic-reconnect
class ReconnectablePostgresqlDatabase(RetryOperationalError, PostgresqlDatabase):
    """Support for reconnecting closed DB connectios."""

    pass


app = Flask(__name__, instance_relative_config=True)
app.config.from_object(config)
if not app.config.from_pyfile("settings.cfg", silent=True) and app.debug:
    print("*** WARNING: Failed to laod local application configuration from 'instance/settins.cfg'")
app.url_map.strict_slashes = False
oauth = OAuth2Provider(app)
api = Api(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    headers_enabled=True,
    default_limits=[
        "40 per second",  # burst: 40/sec
        "1440 per minute",  # allowed max: 24/sec
    ])
DATABASE_URL = app.config.get("DATABASE_URL")

# TODO: implement connection factory
db_url.register_database(PgDbWithFailover, "pg+failover", "postgres+failover")
db_url.PostgresqlDatabase = ReconnectablePostgresqlDatabase
if DATABASE_URL.startswith("sqlite"):
    db = db_url.connect(DATABASE_URL, autorollback=True)
else:
    db = db_url.connect(DATABASE_URL, autorollback=True, connect_timeout=3)


class JSONEncoder(_JSONEncoder):
    """date and datetime encoding into ISO format for JSON payload."""

    def default(self, o):
        """Provide default endocing for date and datetime."""
        if isinstance(o, datetime):
            return o.isoformat(timespec="seconds")
        elif isinstance(o, date):
            return o.isoformat()
        return super().default(o)


app.json_encoder = JSONEncoder


class UserAuthentication(Authentication):
    """Use Flask-OAuthlib authentication and application authentication."""

    def authorize(self):  # noqa: D102
        return current_user.is_authenticated


class AppAuthentication(Authentication):
    """Use Flask-OAuthlib authentication and application authentication."""

    def __init__(self, roles_required=None, app_auth=True, protected_methods=None):
        """Initialize the Authenticator for accessing DB via REST API usig OAuth2."""
        super().__init__(protected_methods=protected_methods)
        self.roles_required = roles_required
        self.app_auth = app_auth

    def authorize(self):  # noqa: D102

        if self.app_auth:
            # Eithe user application authentication or Access Token
            if current_user and current_user.is_authenticated:
                if not self.roles_required or current_user.has_role(self.roles_required):
                    return True
                return False

        if not super().authorize():
            return False

        if hasattr(request, "oauth") and request.oauth:
            return True

        valid, req = oauth.verify_request(())

        # verify if the token owner has any of the roles:
        # if self.roles_required and not current_user.has_role(self.roles_required):
        #     return False

        if not valid:
            return False

        request.oauth = req
        return True


class DataRestAPI(RestAPI):
    """Customized ORM model CRUD API."""

    def configure_routes(self):  # noqa: D102
        for url, callback in self.get_urls():
            self.blueprint.route(url)(callback)

        for provider in self._registry.values():
            api_name = provider.get_api_name()
            for url, callback in provider.get_urls():
                full_url = '/%s%s' % (api_name, url)
                self.blueprint.add_url_rule(
                    full_url,
                    '%s_%s' % (api_name, callback.__name__),
                    self.auth_wrapper(callback, provider),
                    methods=provider.allowed_methods,
                    strict_slashes=False,
                )


default_auth = AppAuthentication(app_auth=True)
data_api = DataRestAPI(app, prefix="/data/api/v0.1", default_auth=default_auth, name="data_api")

admin = Admin(
    app, name="NZ ORCiD Hub", template_mode="bootstrap3", base_template="admin/master.html")

# https://sentry.io/orcid-hub/nz-orcid-hub-dev/getting-started/python-flask/
SENTRY_DSN = app.config.get("SENTRY_DSN")
if SENTRY_DSN:
    sentry = Sentry(
        app, dsn=SENTRY_DSN, logging=True, level=logging.DEBUG if app.debug else logging.WARNING)

login_manager = LoginManager()
login_manager.login_view = "index"
login_manager.login_message_category = "info"
login_manager.init_app(app)

from .queuing import __redis_available, rq  # noqa: F401
from . import models  # noqa: F401
from .apis import *  # noqa: F401,F403
from .data_apis import *  # noqa: F401,F403
from .authcontroller import *  # noqa: F401,F403
from .views import *  # noqa: F401,F403
from .oauth import *  # noqa: F401,F403
from .reports import *  # noqa: F401,F403


from .utils import process_records  # noqa: E402
if app.testing:
    from .mocks import mocks
    app.register_blueprint(mocks)

if __redis_available:
    from . import schedule  # noqa: E402
    schedule.setup()


@app.before_first_request
def setup_app():
    """Set-up logger to log to STDOUT (eventually conainer log), set up the DB, and some other setttings."""
    app.logger.addHandler(logging.StreamHandler())
    app.logger.setLevel(logging.DEBUG if app.debug else logging.WARNING)
    models.create_tables()
    if app.config.get("SHIBBOLETH_DISABLED") is None:
        app.config["SHIBBOLETH_DISABLED"] = (
            not ("mod_wsgi.version" in os.environ and "SHIB_IDP_DOMAINNAME" in os.environ)
            and "EXTERNAL_SP" not in os.environ)


@app.after_request
def apply_x_frame(response):
    """Include X-frame header in http response to protect against clickhiJacking."""
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


@app.cli.command()
@click.option("-d", "--drop", is_flag=True, help="Drop tables before creating...")
@click.option("-f", "--force", is_flag=True, help="Enforce table creation.")
@click.option("-A", "--audit", is_flag=True, help="Create adit trail tables.")
@click.option(
    "-V",
    "--verbose",
    is_flag=True,
    help="Shows SQL statements that get sent to the server or DB.")
def initdb(create=False, drop=False, force=False, audit=True, verbose=False):
    """Initialize the database."""
    if verbose:
        logger = logging.getLogger("peewee")
        if logger:
            logger.setLevel(logging.DEBUG)
            logger.addHandler(logging.StreamHandler())

    if drop and force:
        models.drop_tables()

    try:
        models.create_tables()
    except Exception:
        app.logger.exception("Failed to create tables...")

    if audit:
        app.logger.info("Creating audit tables...")
        models.create_audit_tables()


@app.cli.command("cradmin")
@click.option("-f", "--force", is_flag=True, help="Enforce creation of the super-user.")
@click.option("-V", "--verbose", is_flag=True, help="Shows SQL statements.")
@click.option("-N", "--name", help="User full name.")
@click.option("-O", "--org-name", help="Organisation name.")
@click.option("--orcid", help="User's ORCID iD (for the users authenticated via ORCID).")
@click.option("-I", "--internal-org-name", help="Internal organisation name (e.g., used by IdPs).")
@click.argument("email", nargs=1)
def create_hub_administrator(email,
                             name=None,
                             force=False,
                             verbose=False,
                             org_name=None,
                             orcid=None,
                             internal_org_name=None):
    """Create a hub administrator, an organisation and link the user to the Organisation."""
    if verbose:
        logger = logging.getLogger("peewee")
        if logger:
            logger.setLevel(logging.DEBUG)
            logger.addHandler(logging.StreamHandler())
    if not models.User.table_exists() or not models.Organisation.table_exists():
        app.logger.error(
            "Database tables doensn't exist. Please, firts initialize the datatabase.")
        sys.exit(1)

    super_user, created = models.User.get_or_create(email=email)

    super_user.name = name or org_name or internal_org_name
    super_user.confirmed = True
    super_user.is_superuser = True
    super_user.orcid = orcid

    if org_name:
        org, _ = models.Organisation.get_or_create(name=org_name)
        if internal_org_name:
            org.tuakiri_name = internal_org_name
        org.confirmed = True
        org.save()
        models.UserOrg.get_or_create(user=super_user, org=org)

        super_user.organisation = org

    super_user.save()


@app.cli.group()
@click.option("-v", "--verbose", is_flag=True)
def load(verbose):
    """Load data from files."""
    app.verbose = verbose


@load.command()
@click.argument('input', type=click.File('r'), required=True)
def org_info(input):
    """Pre-loads organisation data."""
    row_count = models.OrgInfo.load_from_csv(input)
    click.echo(f"Loaded {row_count} records")


@app.cli.command()
@click.option("-n", default=20, help="Max number of rows to process.")
def process(n):
    """Process uploaded records."""
    process_records(n)


if os.environ.get("ENV") == "dev0":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.debug = True

if app.debug:
    try:
        from flask_debugtoolbar import DebugToolbarExtension
        toolbar = DebugToolbarExtension(app)
        # logger = logging.getLogger('peewee')
        # logger.setLevel(logging.DEBUG)
        # logger.addHandler(logging.StreamHandler())
    except ModuleNotFoundError:
        pass
