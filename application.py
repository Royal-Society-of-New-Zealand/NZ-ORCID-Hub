import logging
import os
from logging.handlers import RotatingFileHandler

import flask_login
from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail
from flask_peewee.rest import Authentication, RestAPI
from peewee import PostgresqlDatabase
from playhouse import db_url
from playhouse.shortcuts import RetryOperationalError
from raven.contrib.flask import Sentry

from config import *  # noqa: F401, F403
from failover import PgDbWithFailover
from flask_admin import Admin


# http://docs.peewee-orm.com/en/latest/peewee/database.html#automatic-reconnect
class ReconnectablePostgresqlDatabase(RetryOperationalError, PostgresqlDatabase):
    pass


app = Flask(__name__)
app.config.from_object(__name__)

# TODO: implment connection factory
db_url.register_database(PgDbWithFailover, "pg+failover", "postgres+failover")
db_url.PostgresqlDatabase = ReconnectablePostgresqlDatabase
if DATABASE_URL.startswith("sqlite"):
    db = db_url.connect(DATABASE_URL, autorollback=True)
else:
    db = db_url.connect(DATABASE_URL, autorollback=True, connect_timeout=3)


class UserAuthentication(Authentication):
    def authorize(self):
        return flask_login.current_user.is_authenticated


api = RestAPI(
    app, prefix="/api/v0.1", name="ORCID HUB Data API", default_auth=UserAuthentication())

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

if __name__ == "__main__":
    # flake8: noqa
    from authcontroller import *
    from views import *
    from reports import *
    1/0

    os.environ['DEBUG'] = "1"
    # This allows us to use a plain HTTP callback
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    if app.debug:
        toolbar = DebugToolbarExtension(app)
    app.run(debug=True, port=5000)
