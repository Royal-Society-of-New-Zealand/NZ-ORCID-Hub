from requests_oauthlib import OAuth2Session
from flask import Flask, request, redirect, session, url_for, render_template
from flask.json import jsonify
import os
from werkzeug.urls import iri_to_uri
from config import *
from flask_sqlalchemy import SQLAlchemy
#from model import Researcher
#from authcontroller import *


app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
os.environ['DEBUG'] = "1"
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

#NB! Should be disabled in production
from pyinfo import info
@app.route('/pyinfo')
def pyinfo():
    return render_template('pyinfo.html', **info)

db = SQLAlchemy(app)
from authcontroller import *
if __name__ == "__main__":
    # This allows us to use a plain HTTP callback
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.secret_key = os.urandom(24)
    app.run(debug=True,port=5000)

