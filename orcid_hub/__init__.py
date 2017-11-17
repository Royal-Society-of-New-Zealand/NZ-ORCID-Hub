import logging
import os
import click
from logging.handlers import RotatingFileHandler

import flask_login
from flask import Flask, request
from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail
from flask_oauthlib.provider import OAuth2Provider
from flask_peewee.rest import Authentication, RestAPI
from peewee import PostgresqlDatabase
from playhouse import db_url
from playhouse.shortcuts import RetryOperationalError
from raven.contrib.flask import Sentry

from config import *  # noqa: F401, F403
from .failover import PgDbWithFailover
from flask_admin import Admin


# http://docs.peewee-orm.com/en/latest/peewee/database.html#automatic-reconnect
class ReconnectablePostgresqlDatabase(RetryOperationalError, PostgresqlDatabase):
    pass


app = Flask(__name__)
app.config.from_object(__name__)
app.url_map.strict_slashes = False
oauth = OAuth2Provider(app)

# TODO: implment connection factory
db_url.register_database(PgDbWithFailover, "pg+failover", "postgres+failover")
db_url.PostgresqlDatabase = ReconnectablePostgresqlDatabase
if DATABASE_URL.startswith("sqlite"):
    db = db_url.connect(DATABASE_URL, autorollback=True)
else:
    db = db_url.connect(DATABASE_URL, autorollback=True, connect_timeout=3)


class UserAuthentication(Authentication):
    """Use Flask-OAuthlib authentication and application authentication."""

    def authorize(self):
        return flask_login.current_user.is_authenticated


class Oauth2Authentication(Authentication):
    """Use Flask-OAuthlib authentication and application authentication."""

    # TODO: add user role requierentes.
    # TOOD: limit access to the user data ONLY!

    def authorize(self):
        if not super().authorize():
            return False

        if hasattr(request, "oauth") and request.oauth:
            return True

        valid, req = oauth.verify_request(())
        if not valid:
            return False

        request.oauth = req
        return True


class DataRestAPI(RestAPI):
    def configure_routes(self):
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


default_auth = Oauth2Authentication()
api = DataRestAPI(app, prefix="/data/api/v0.1", default_auth=default_auth, name="data_api")

mail = Mail()
mail.init_app(app)

admin = Admin(
    app, name="NZ ORCiD Hub", template_mode="bootstrap3", base_template="admin/master.html")

# https://sentry.io/orcid-hub/nz-orcid-hub-dev/getting-started/python-flask/
sentry = Sentry(app, logging=True, level=logging.WARNING)

login_manager = flask_login.LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app)

from . import models  # noqa: F401
from .api import *  # noqa: F401,F403
# from .application import app
from .authcontroller import *  # noqa: F401,F403
from .views import *  # noqa: F401,F403
from .oauth import *  # noqa: F401,F403
from .reports import *  # noqa: F401,F403
from .utils import process_affiliation_records, process_funding_records
