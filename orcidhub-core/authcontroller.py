from requests_oauthlib import OAuth2Session
from flask import request, redirect, session, url_for, render_template, flash
from werkzeug.urls import iri_to_uri
from config import client_id, client_secret, authorization_base_url, \
    token_url, scope, redirect_uri
from model import Researcher
from application import app
from application import db
import json
from urllib.parse import quote


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/Tuakiri/login")
def login():
    # print(request.headers)
    token = request.headers.get("Auedupersonsharedtoken")
    session['family_names'] = request.headers['Sn']
    session['given_names'] = request.headers['Givenname']
    session['email'] = request.headers['Mail']
    if token:
        # This is a unique id got from Tuakiri SAML used as identity in database
        session['Auedupersonsharedtoken'] = token
        return render_template("linking.html", userName=request.headers['Displayname'],
                               organisationName=request.headers['O'])
    else:
        return redirect(url_for("index"))


@app.route("/Tuakiri/redirect")
def demo():
    """Step 1: User Authorization.
    Redirect the user/resource owner to the OAuth provider (i.e.Orcid )
    using an URL with a few key OAuth parameters.
    """
    client = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = client.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    auedupersonsharedtoken = session.get("Auedupersonsharedtoken")
    userPresent = False
    # Check if user details are already in database
    if auedupersonsharedtoken:
        data = Researcher.query.filter_by(auedupersonsharedtoken=auedupersonsharedtoken).first()
        if None is not data:
            userPresent = True
    # If user details are already there in database redirect to profile instead of orcid
    if userPresent:
        flash("Your account is already linked to ORCiD", 'warning')
        return redirect(url_for('.profile'))
    else:
        return redirect(
            iri_to_uri(authorization_url) + "&family_names=" + session['family_names'] + "&given_names=" + session[
                'given_names'] + "&email=" + session['email'])


# Step 2: User authorization, this happens on the provider.
@app.route("/auth", methods=["GET"])
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
    orcid = token['orcid']
    flash("Your account was linked to ORCiD %s" % orcid)

    return redirect(url_for('profile'))


@app.route("/Tuakiri/profile", methods=["GET"])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    name = ""
    oauth_token = ""
    orcid = ""
    auedupersonsharedtoken = session['Auedupersonsharedtoken']

    if auedupersonsharedtoken is not None:
        data = Researcher.query.filter_by(auedupersonsharedtoken=auedupersonsharedtoken).first()
        if None is not data:
            name = data.rname
            oauth_token = data.auth_token
            orcid = data.orcidid
        else:
            orcid = session['oauth_token']['orcid']
            name = session['oauth_token']['name']
            researcher = Researcher(rname=session['oauth_token']['name'],
                                    orcidid=session['oauth_token']['orcid'],
                                    auth_token=session['oauth_token']['access_token'],
                                    auedupersonsharedtoken=session['Auedupersonsharedtoken'])
            oauth_token = session['oauth_token']['access_token']
            db.session.add(researcher)
            db.session.commit()
    client = OAuth2Session(client_id, token={'access_token': oauth_token})
    headers = {'Accept': 'application/json'}
    resp = client.get("https://api.sandbox.orcid.org/v1.2/" +
                      str(orcid) + "/orcid-works", headers=headers)
    return render_template(
        "profile.html",
        userName=name,
        orcid=orcid,
        work=json.dumps(json.loads(resp.text), sort_keys=True, indent=4, separators=(',', ': ')))


@app.after_request
def remove_if_invalid(response):
    if "__invalidate__" in session:
        response.delete_cookie(app.session_cookie_name)
    return response


@app.route("/logout")
def logout():
    session.clear()
    session["__invalidate__"] = True
    return redirect("/Shibboleth.sso/Logout?return=" + quote(url_for("index")))


@app.route("/Tuakiri/clear_db")
def clear_db():
    db.session.execute("DELETE FROM researcher")
    db.session.commit()
    return redirect(url_for("logout"))
