# -*- coding: utf-8 -*-
"""Application module gluing script.

Simple solution to overcome circular import problem:
http://charlesleifer.com/blog/structuring-flask-apps-a-how-to-for-those-coming-from-django/
"""

import os

# NB! Should be disabled in production
from flask_debugtoolbar import DebugToolbarExtension
from peewee import OperationalError

import models  # noqa: F401
from application import app, db
from authcontroller import *  # noqa: F401, F403
from views import *  # noqa: F401, F403
import initializedb


# TODO: connection should be managed explicitely
@app.before_request
def before_request():
    try:
        db.connect()
    except OperationalError:
        pass


@app.after_request
def after_request(response):
    if db is not None:
        try:
            db.close()
        except OperationalError:
            pass
    return response


@app.cli.command()
def initdb():
    """Initialize the database."""
    initializedb.initdb()


if app.debug:
    toolbar = DebugToolbarExtension(app)

if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.secret_key = os.urandom(24)
    app.run(debug=True, port=8000)
