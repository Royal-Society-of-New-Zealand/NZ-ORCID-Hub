from requests_oauthlib import OAuth2Session
from flask import request, redirect, session, url_for, render_template
from werkzeug.urls import iri_to_uri
from config import client_id, client_secret, authorization_base_url,\
    token_url, scope, redirect_uri
from model import Researcher
from application import app
from application import db


@app.route("/index")
def index():
    print(session)
    print(request.headers)
    return render_template("index.html")


@app.route("/redirect")
def demo():
    """Step 1: User Authorization.
    Redirect the user/resource owner to the OAuth provider (i.e.Orcid )
    using an URL with a few key OAuth parameters.
    """
    client = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = client.authorization_url(authorization_base_url)
    session['oauth_state'] = state
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
    print(token)
    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_token'] = token

    return redirect(url_for('.profile'))


@app.route("/profile", methods=["GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    orcid = session['oauth_token']['orcid']
    name = session['oauth_token']['name']
    print(orcid)

    researcher = Researcher(rname=session['oauth_token']['name'],
                            orcidid=session['oauth_token']['orcid'],
                            auth_token=session['oauth_token']['access_token'])
    db.session.add(researcher)
    db.session.commit()
    client = OAuth2Session(client_id, token=session['oauth_token'])
    headers = {'Accept': 'application/json'}
    resp = client.get("https://api.sandbox.orcid.org/v1.2/" + str(orcid)
                      + "/orcid-works", headers=headers)
    return render_template("login.html", userName=name, work=resp.text)
