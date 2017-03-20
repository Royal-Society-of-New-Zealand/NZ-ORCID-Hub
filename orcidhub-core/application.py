import os
from flask import Flask
from peewee import PostgresqlDatabase
import config
from config import SQLALCHEMY_DATABASE_URI, MAIL_USERNAME, MAIL_PASSWORD, TOKEN_PASSWORD_SALT, \
    TOKEN_SECRET_KEY, MAIL_DEFAULT_SENDER, MAIL_SERVER
from flask_mail import Mail
import flask_login
import logging
from logging.handlers import RotatingFileHandler
from flask_admin import Admin

app = Flask(__name__)

if os.path.exists("/var/log/orcidhub"):
    handler = RotatingFileHandler(
        '/var/log/orcidhub/orcidhub.log',
        maxBytes=10000, backupCount=10)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

app.secret_key = ")Xq/4vc'K%wesQ$n'n;?+y@^rY\/u8!sk{?D7Y>.V`t_/y'wn>7~cZ$(Q.$n)d_j"
# NB! Disable in production
is_dev_env = (os.environ.get("ENV") in ("test",))
app.config['TESTING'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.debug = True
app.config['SECRET_KEY'] = app.secret_key
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['DEBUG'] = "1"

db = PostgresqlDatabase(
    config.DB_NAME,
    user=config.DB_USERNAME,
    password=config.DB_PASSWORD,
    host=config.DB_HOSTNAME)

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['DEBUG_TB_PROFILER_ENABLED'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
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

admin = Admin(app, name="NZ ORCiD Hub", template_mode="bootstrap3")

login_manager = flask_login.LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app)

if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    # flake8: noqa
    from authcontroller import *

    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.secret_key = os.urandom(24)
    if app.debug:
        toolbar = DebugToolbarExtension(app)
    app.run(debug=True, port=5000)
