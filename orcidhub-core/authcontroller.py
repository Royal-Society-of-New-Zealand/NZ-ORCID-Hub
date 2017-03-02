from requests_oauthlib import OAuth2Session
from flask import request, redirect, session, url_for, render_template
from werkzeug.urls import iri_to_uri
from config import client_id, client_secret, authorization_base_url, \
    token_url, scope, redirect_uri
from models import Researcher
from application import app
import json
from peewee import DoesNotExist


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/Tuakiri/login")
def login():
    # print(request.headers)
    token = request.headers.get("Auedupersonsharedtoken")
    if token:
        # This is a unique id got from Tuakiri SAML used as identity in database
        session['Auedupersonsharedtoken'] = token
        return render_template("login.html", userName=request.headers['Displayname'],
                               organisationName=request.headers['O'])
    else:
        return render_template("login.html")


@app.route("/Tuakiri/redirect")
def demo():
    """Step 1: User Authorization.
    Redirect the user/resource owner to the OAuth provider (i.e.Orcid )
    using an URL with a few key OAuth parameters.
    """
    client = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = client.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    edu_person_shared_token = session.get("Auedupersonsharedtoken")
    # Check if user details are already in database
    if edu_person_shared_token:
        try:
            Researcher.get(Researcher.edu_person_shared_token == edu_person_shared_token)
            # If user details are already there in database redirect to profile instead of orcid
            return redirect(url_for('.profile'))
        except DoesNotExist:
            pass
    return redirect(iri_to_uri(authorization_url))


# Step 2: User authorization, this happens on the provider.
@app.route("/orcidhub/test", methods=["GET"])
def callback():
    """ Step 3: Retrieving an access token.
    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """
    client = OAuth2Session(client_id)
    token = client.fetch_token(token_url, client_secret=client_secret,
                               authorization_response=request.url)
    # #print(token)
    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_token'] = token

    return redirect(url_for('.profile'))


@app.route("/Tuakiri/profile", methods=["GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """

    edu_person_shared_token = session.get('Auedupersonsharedtoken')
    oauth_token = session["oauth_token"]
    orcid = oauth_token["orcid"]
    name = oauth_token["name"]

    Researcher.get_or_create(
        rname=name,
        orcid=orcid,
        auth_token=oauth_token["access_token"],
        edu_person_shared_token=edu_person_shared_token)

    client = OAuth2Session(client_id, token=oauth_token)

    headers = {'Accept': 'application/json'}
    resp = client.get("https://api.sandbox.orcid.org/v1.2/" +
                      str(orcid) + "/orcid-works", headers=headers)
    return render_template(
        "login.html",
        userName=name,
        work=json.dumps(json.loads(resp.text), sort_keys=True, indent=4, separators=(',', ': ')))
