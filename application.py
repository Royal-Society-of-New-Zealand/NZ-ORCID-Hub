import logging
import os
from logging.handlers import RotatingFileHandler

import flask_login
from flask import Flask
from flask_admin import Admin
from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail
from playhouse import db_url

from config import *  # noqa: F401, F403

app = Flask(__name__)

if os.path.exists("/var/log/orcidhub"):
    handler = RotatingFileHandler('/var/log/orcidhub/orcidhub.log', maxBytes=10000, backupCount=10)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

app.secret_key = ")Xq/4vc'K%wRe&sQ$n'n;?+y@^rY\/u8!sk{?D7Y>.V`t_/y'wn>7~cZ$(Q.$n)d_j"
# NB! Disable in production
app.debug = is_dev_env = (os.environ.get("ENV") in ("dev0", ))

app.config.from_object(__name__)
app.config['TESTING'] = True
app.config['SECRET_KEY'] = app.secret_key
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

db = db_url.connect(DATABASE_URL, autorollback=True, connect_timeout=3)
## backup_db = db_url.connect(BACKUP_DATABASE_URL, autorollback=True, connect_timeout=3)

if app.debug:
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
    app.config['DEBUG_TB_PROFILER_ENABLED'] = True
    os.environ['DEBUG'] = "1"

# add mail server config
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_SUPPRESS_SEND'] = False
mail = Mail()
mail.init_app(app)

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
