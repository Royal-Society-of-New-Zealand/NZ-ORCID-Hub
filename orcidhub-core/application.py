import os
from flask import Flask, render_template
# NB! Should be disabled in production
from pyinfo import info
from peewee import PostgresqlDatabase
import config

app = Flask(__name__)

app.secret_key = os.urandom(24)
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)

app.secret_key = ")Xq/4vc'K%wesQ$n'n;?+y@^rY\/u8!sk{?D7Y>.V`t_/y'wn>7~cZ$(Q.$n)d_j"
# NB! Disable in production
app.config['TESTING'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
os.environ['DEBUG'] = "1"
app.debug = True
app.config['SECRET_KEY'] = app.secret_key
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# NB! Disable in production
toolbar = DebugToolbarExtension(app)

@app.route('/pyinfo')
def pyinfo():
    return render_template('pyinfo.html', **info)

db = PostgresqlDatabase(
    config.DB_NAME,
    user=config.DB_USERNAME,
    password=config.DB_PASSWORD,
    host=config.DB_HOSTNAME
)

# TODO: connection should be managed explicitely
@app.before_request
def before_request():
    db.connect()

@app.after_request
def after_request(response):
    db.close()
    return response

# flake8: noqa
from authcontroller import *

if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.secret_key = os.urandom(24)
    app.run(debug=True, port=5000)
