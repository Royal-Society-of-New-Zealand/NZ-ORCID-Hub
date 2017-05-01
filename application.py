import logging
import os
from logging.handlers import RotatingFileHandler

import flask_login
from flask import Flask
from flask_admin import Admin
from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail
from playhouse.db_url import connect

import config
from config import (MAIL_DEFAULT_SENDER, MAIL_PASSWORD, MAIL_SERVER, MAIL_USERNAME,
                    TOKEN_PASSWORD_SALT, TOKEN_SECRET_KEY)

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.utils import OneLogin_Saml2_Utils

app = Flask(__name__)
app.config['SAML_PATH'] = os.path.join(os.path.dirname(__file__), "SAML")

if os.path.exists("/var/log/orcidhub"):
    handler = RotatingFileHandler('/var/log/orcidhub/orcidhub.log', maxBytes=10000, backupCount=10)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

app.secret_key = ")Xq/4vc'K%wesQ$n'n;?+y@^rY\/u8!sk{?D7Y>.V`t_/y'wn>7~cZ$(Q.$n)d_j"
# NB! Disable in production
is_dev_env = (os.environ.get("ENV") in ("test", ))
app.config['TESTING'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.debug = True
app.config['SECRET_KEY'] = app.secret_key
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['DEBUG'] = "1"

db = connect(config.DATABASE_URL)

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['DEBUG_TB_PROFILER_ENABLED'] = True
app.config["DATABASE_URL"] = config.DATABASE_URL
os.environ['DEBUG'] = "1"
app.debug = True
app.config['SECRET_KEY'] = app.secret_key
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# add mail server config
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_SUPPRESS_SEND'] = False
mail = Mail()
mail.init_app(app)

# Secret key and salt for token generation
app.config['TOKEN_SECRET_KEY'] = TOKEN_SECRET_KEY
app.config['TOKEN_PASSWORD_SALT'] = TOKEN_PASSWORD_SALT

#admin = Admin(app, name="NZ ORCiD Hub", template_mode="bootstrap3", base_template="layout.html")
admin = Admin(
    app, name="NZ ORCiD Hub", template_mode="bootstrap3", base_template="admin/master.html")

login_manager = flask_login.LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app)

if __name__ == "__main__":
    # flake8: noqa
    from authcontroller import *
    from views import *

    os.environ['DEBUG'] = "1"
    # This allows us to use a plain HTTP callback
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.secret_key = os.urandom(24)
    if app.debug:
        toolbar = DebugToolbarExtension(app)
    app.run(debug=True, port=5000)
