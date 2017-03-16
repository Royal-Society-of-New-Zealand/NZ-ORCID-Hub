import os
from flask import Flask
from config import SQLALCHEMY_DATABASE_URI, MAIL_USERNAME, MAIL_PASSWORD, TOKEN_PASSWORD_SALT, TOKEN_SECRET_KEY, MAIL_DEFAULT_SENDER, MAIL_SERVER
from flask_sqlalchemy import SQLAlchemy
from flask_login import  LoginManager
from flask_mail import Mail
# NB! Should be disabled in production
from pyinfo import info
from flask_debugtoolbar import DebugToolbarExtension
import logging
from logging.handlers import RotatingFileHandler

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
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = is_dev_env
app.config['DEBUG_TB_PROFILER_ENABLED'] = is_dev_env
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
os.environ['DEBUG'] = "1"
app.debug = True
app.config['SECRET_KEY'] = app.secret_key
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
login_manager = LoginManager()
login_manager.init_app(app)


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
# NB! Disable in production
toolbar = DebugToolbarExtension(app)

@app.route('/pyinfo')
def pyinfo():
    return render_template('pyinfo.html', **info)


db = SQLAlchemy(app)
# flake8: noqa
from authcontroller import *

if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.secret_key = os.urandom(24)
    app.run(debug=True, port=5000)
