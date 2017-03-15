from requests_oauthlib import OAuth2Session
from flask import request, redirect, session, url_for, render_template, flash
from werkzeug.urls import iri_to_uri
from config import client_id, client_secret, authorization_base_url, \
    token_url, scope, redirect_uri
from model import OrcidUser
from model import UserRole
from model import Organisation
from application import app
from application import db
import json
from urllib.parse import quote
from flask_login import login_user, current_user
from loginProvider import login_required
from registrationForm import OrgRegistrationForm
from flask_mail import Message
from application import mail
from tokenGeneration import generate_confirmation_token, confirm_token
from application import login_manager
from registrationForm import OrgConfirmationForm
from os import environ

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
    orcidUser = OrcidUser.query.filter_by(email=session['email']).first()
    session["shib_O"] = tuakiri_orgName = request.headers['O']

    if tuakiri_orgName:
        app.logger.info("User logged in from '%s'", tuakiri_orgName)

    # import pdb;pdb.set_trace()

    registerOptions = {}
    if (not (orcidUser is None) and (orcidUser.confirmed)):
        login_user(orcidUser)
        if current_user.get_urole() == UserRole.ADMIN:
            registerOptions['Register Researcher'] = "/Tuakiri/register/researcher"
        elif current_user.get_urole() == UserRole.SUPERUSER:
            registerOptions['Register Organisation'] = "/Tuakiri/register/organisation"
        else:
            registerOptions['View Work'] = "/Tuakiri/redirect"

        if token:
            # This is a unique id got from Tuakiri SAML used as identity in database
            session['Auedupersonsharedtoken'] = token
            return render_template("base.html", userName=request.headers['Displayname'],
                                   organisationName=request.headers['O'], registerOptions=registerOptions)
        else:
            return render_template("base.html")
    elif (orcidUser is None):
        # Check if the organization to which user belong is onboarded, if yes onboard user automatically
        organisation = Organisation.query.filter_by(tuakiriname=tuakiri_orgName).first()
        if (organisation is not None) and (organisation.confirmed):
            orcidUser = OrcidUser(rname=session['given_names'], email=session['email'], urole=UserRole.RESEARCHER,
                                  confirmed=True, orgid=organisation.emailid, auedupersonsharedtoken=token)
            db.session.add(orcidUser)
            db.session.commit()
            login_user(orcidUser)
            registerOptions['View Work'] = "/Tuakiri/redirect"
            return render_template("base.html", userName=request.headers['Displayname'],
                                   organisationName=request.headers['O'], registerOptions=registerOptions)
        else:
            flash("Your organisation (%s) is not onboarded" % tuakiri_orgName, "danger")
    # return render_template("login.html")
    return redirect(url_for("index"))


@app.route("/Tuakiri/redirect")
@login_required(role=[UserRole.ANY])
def demo():
    """Step 1: User Authorization.
    Redirect the user/resource owner to the OAuth provider (i.e.Orcid )
    using an URL with a few key OAuth parameters.
    """
    client = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = client.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    auedupersonsharedtoken = session.get("Auedupersonsharedtoken")
    # userPresent = False
    # Check if user details are already in database
    if auedupersonsharedtoken and current_user.is_active():
        # data = Researcher.query.filter_by(auedupersonsharedtoken=auedupersonsharedtoken).first()
        data = OrcidUser.query.filter_by(email=current_user.email).first()
        if None is not data:
            # If user details are already there in database redirect to profile instead of orcid
            if (data.auth_token is not None) and (data.orcidid is not None):
                flash("Your account is already linked to ORCiD", 'warning')
                session['oauth_token'] = data.auth_token
                return redirect(url_for('.profile'))
            else:
                return redirect(
                    iri_to_uri(authorization_url) + "&family_names=" + session['family_names'] + "&given_names=" +
                    session[
                        'given_names'] + "&email=" + session['email'])


# Step 2: User authorization, this happens on the provider.
@app.route("/auth", methods=["GET"])
@login_required(role=[UserRole.ANY])
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
@login_required(role=[UserRole.ANY])
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    name = ""
    oauth_token = ""
    orcid = ""
    # auedupersonsharedtoken = session['Auedupersonsharedtoken']

    #   if auedupersonsharedtoken is not None:
    data = OrcidUser.query.filter_by(email=session['email']).first()
    if data is not None:
        # data = Researcher.query.filter_by(auedupersonsharedtoken=auedupersonsharedtoken).first()
        name = data.rname
        oauth_token = data.auth_token
        orcid = data.orcidid
        if ((oauth_token is None) or (oauth_token != session['oauth_token'])):
            orcid = session['oauth_token']['orcid']
            oauth_token = session['oauth_token']['access_token']
            data.orcidid = orcid
            data.auth_token = oauth_token
            db.session.commit()
    else:
        login_manager.unauthorized()
    client = OAuth2Session(client_id, token={'access_token': oauth_token})
    headers = {'Accept': 'application/json'}
    resp = client.get("https://api.sandbox.orcid.org/v1.2/" +
                      str(orcid) + "/orcid-works", headers=headers)
    return render_template(
        "profile.html",
        userName=name,
        orcid=orcid,
        work=json.dumps(json.loads(resp.text), sort_keys=True, indent=4, separators=(',', ': ')))


@app.route("/Tuakiri/register/researcher", methods=["GET"])
@login_required(role=[UserRole.SUPERUSER, UserRole.ADMIN])
def registerOrganisation():
    # For now on boarding of researcher is not supported
    return "Work in Progress!!!"


@app.route("/Tuakiri/register/organisation", methods=["GET", "POST"])
@login_required(role=[UserRole.SUPERUSER])
def registerResearcher():
    form = OrgRegistrationForm()
    if request.method == 'POST':
        if form.validate() is False:
            return 'Please fill in all fields <p><a href="/Tuakiri/register/organisation">Try Again!!!</a></p>'
        else:
            data = OrcidUser.query.filter_by(email=form.orgEmailid.data).first()
            if data is not None:
                flash("This Email address is already an Admin for one of the organisation", "warning")
                return render_template('registration.html', form=form)
                # return redirect(url_for('.profile'))
            else:
                organisation = Organisation(org_name=form.orgName.data, emailid=form.orgEmailid.data)
                db.session.add(organisation)
                db.session.commit()

                orcidUser = OrcidUser(rname=form.orgName.data, email=form.orgEmailid.data, urole=UserRole.ADMIN,
                                      orgid=organisation.emailid)
                db.session.add(orcidUser)
                db.session.commit()
                # Using app context due to issue: https://github.com/mattupstate/flask-mail/issues/63
                with app.app_context():
                    msg = Message("Welcome to OrcidhHub",
                                  recipients=[str(form.orgEmailid.data)])
                    token = generate_confirmation_token(form.orgEmailid.data)
                    msg.body = "Your organisation is just one step behind to get onboarded" \
                               " please click on following link to get onboarded " \
                               "https://"+environ.get("ENV", "dev")+".orcidhub.org.nz/Tuakiri/confirm/" + str(token)
                    mail.send(msg)
                    flash("Organisation Onboarded Successfully!!! Email Communication has been sent to Admin",
                          "success")
                return render_template('registration.html', form=form)

    elif request.method == 'GET':
        return render_template('registration.html', form=form)


@app.route("/Tuakiri/confirm/<token>", methods=["GET", "POST"])
def confirmUser(token):
    email = confirm_token(token)
    form = OrgConfirmationForm()
    # For now only GET method is implemented will need post method for organisation
    # to enter client secret and client key for orcid
    if request.method == 'POST':
        if form.validate() is False:
            return 'Please fill in all fields <p><a href="/Tuakiri/register/organisation">Try Again!!!</a></p>'

        if email is False:
            login_manager.unauthorized()
        tuakiri_token = request.headers.get("Auedupersonsharedtoken")
        tuakiri_mail = request.headers['Mail']
        tuakiri_orgName = request.headers['O']
        if email == tuakiri_mail:
            orcidUser = OrcidUser.query.filter_by(email=email).first()
            organisation = Organisation.query.filter_by(emailid=email).first()
            if (not (orcidUser is None) and (not (organisation is None))):
                # Update Organisation
                organisation.tuakiriname = tuakiri_orgName
                organisation.confirmed = True
                organisation.orcid_client_id = form.orgOricdClientId.data
                organisation.orcid_secret = form.orgOrcidClientSecret.data

                # Update Orcid User
                orcidUser.confirmed = True
                orcidUser.auedupersonsharedtoken = tuakiri_token
                db.session.commit()
                with app.app_context():
                    msg = Message("Welcome to OrcidhHub",
                                  recipients=[email])
                    msg.body = "Congratulations your emailid has been confirmed and " \
                               "organisation onboarded successfully."
                    mail.send(msg)
                    flash("Your Onboarding is Completed!!!", "success")
                return redirect(url_for("login"))
                # return render_template("login.html")
            else:
                login_manager.unauthorized()
        else:
            login_manager.unauthorized()
    elif request.method == 'GET':
        if email is False:
            login_manager.unauthorized()
        form.orgEmailid.data = email
        form.orgName.data = request.headers['O']
        return render_template('orgconfirmation.html', form=form)


@app.after_request
def remove_if_invalid(response):
    if "__invalidate__" in session:
        response.delete_cookie(app.session_cookie_name)
        session.clear()
    return response


@app.route("/logout")
def logout():
    org_name = session.get("shib_O")
    session.clear()
    session["__invalidate__"] = True
    return redirect(
        "/Shibboleth.sso/Logout?return=" +
        quote(url_for("uoa_slo" if org_name and org_name == "University of Auckland" else "index")))


@app.route("/uoa-slo")
def uoa_slo():
    flash("""You had logged in from 'The University of Auckland'.
You have to close all open browser tabs and windows in order
in order to complete the log-out.""", "warning")
    return render_template("uoa-slo.html")


@app.route("/Tuakiri/clear_db")
def clear_db():
    db.session.execute("DELETE FROM orciduser WHERE rname NOT LIKE '%Royal%'")
    db.session.execute("DELETE FROM organisation WHERE org_name NOT LIKE '%Royal%'")
    db.session.execute("DELETE FROM researcher")
    db.session.commit()
    return redirect(url_for("logout"))
