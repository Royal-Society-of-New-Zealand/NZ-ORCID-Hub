from application import app, db
import models  # noqa: F401
from views import *  # noqa: F401, F403
from authcontroller import *  # noqa: F401, F403
import os
from peewee import OperationalError

# TODO: connection should be managed explicitely
@app.before_request
def before_request():
    try:
        db.connect()
    except OperationalError:
        pass


@app.after_request
def after_request(response):
    try:
        db.close()
    except OperationalError:
        pass
    return response


if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.secret_key = os.urandom(24)
    app.run(debug=True, port=5000)
