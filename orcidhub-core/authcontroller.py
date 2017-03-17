from requests_oauthlib import OAuth2Session
from flask import request, redirect, session, url_for, render_template, flash
from werkzeug.urls import iri_to_uri
from config import client_id, client_secret, authorization_base_url, \
    token_url, scope, redirect_uri
import json
from peewee import DoesNotExist
from application import app, db, mail
from models import User, Role, Organisation
from urllib.parse import quote
from flask_login import login_user, current_user
from registrationForm import OrgRegistrationForm
from flask_mail import Message
from tokenGeneration import generate_confirmation_token, confirm_token
from registrationForm import OrgConfirmationForm
from flask_login import login_required
from login_provider import roles_required
from os import environ

@app.route("/")
@app.route("/login")
@app.route("/home")
@app.route("/index")
def login():
    """
    Main landing page
    """
    return render_template("index.html")


@app.route("/Tuakiri/login")
def shib_login():
    token = request.headers.get("Auedupersonsharedtoken")
    last_name = session['family_names'] = request.headers['Sn']
    first_name = session['given_names'] = request.headers['Givenname']
    email = session['email'] = request.headers['Mail']
    session["shib_O"] = shib_org_name = request.headers['O']
    name = request.headers.get('Displayname')

    try:
        org = Organisation.get(Organisation.name == shib_org_name)
    except Organisation.DoesNotExist:
        org = None

    try:
        user = User.get(User.email == session['email'])
    except User.DoesNotExist:
        user = User.create(
            email=email,
            name=name,
            first_name=first_name,
            last_name=last_name,
            confirmed=True,
            roles=Role.RESEARCHER,
            organisation=org,
            edu_person_shared_token=token)
        user.save()
    login_user(user)

    if org and org.confirmed:
        return redirect(url_for("link"))
    else:
        flash("Your organisation (%s) is not onboarded" % shib_org_name, "danger")

    return redirect(url_for("login"))


@app.route("/link")
@login_required
def link():
    """
    Links the user's account with ORCiD (i.e. affiliates user with his/her org on ORCID)

    Step 1: User Authorization.
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
            User.get(User.edu_person_shared_token == edu_person_shared_token)
            # If user details are already there in database redirect to profile instead of orcid
            return redirect(url_for('.profile'))
        except DoesNotExist:
            pass
    return redirect(
        iri_to_uri(authorization_url) +
        "&family_names=" + session['family_names'] +
        "&given_names=" + session['given_names'] +
        "&email=" + session['email'])


# Step 2: User authorization, this happens on the provider.
@app.route("/auth", methods=["GET"])
@login_required
def orcid_callback():
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
    name = token["name"]
    access_token = token["access_token"]
    user = current_user()
    if orcid:
        user.orcid = orcid
    if name:
        user.name = name
    if access_token:
        user.auth_token = access_token
    user.save()

    flash("Your account was linked to ORCiD %s" % orcid, "success")

    return redirect(url_for("profile"))


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    user = current_user()
    client = OAuth2Session(client_id, token={"oauth_token": user.access_token})

    headers = {'Accept': 'application/json'}
    resp = client.get("https://api.sandbox.orcid.org/v1.2/" +
                      user.orcid + "/orcid-works", headers=headers)
    return render_template(
        "profile.html",
        user,
        work=json.dumps(json.loads(resp.text), sort_keys=True, indent=4, separators=(',', ': ')))


@app.route("/invite/user", methods=["GET"])  # /invite/user
@roles_required(Role.SUPERUSER, Role.ADMIN)
def invite_user():
    # For now on boarding of researcher is not supported
    return "Work in Progress!!!"


@app.route("/register/organisation", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER)
def register_organisation():
    form = OrgRegistrationForm()
    if request.method == "POST":
        if form.validate() is False:
            flash("Please fill in all fields and try again.", "danger")
        else:
            data = User.query.filter_by(email=form.orgEmailid.data).first()
            if data is not None:
                flash("This Email address is already an Admin for one of the organisation", "warning")
            else:
                org = Organisation(org_name=form.orgName.data, emailid=form.orgEmailid.data)
                org.save()
                user = User(name=form.orgName.data, email=form.orgEmailid.data, roles=Role.ADMIN, organisation=org)
                user.save()
                # Note: Using app context due to issue: https://github.com/mattupstate/flask-mail/issues/63
                with app.app_context():
                    msg = Message("Welcome to OrcidhHub",
                                  recipients=[str(form.orgEmailid.data)])
                    token = generate_confirmation_token(form.orgEmailid.data)
                    # TODO: do it with templates
                    msg.body = "Your organisation is just one step behind to get onboarded" \
                               " please click on following link to get onboarded " \
                               "https://"+environ.get("ENV", "dev")+".orcidhub.org.nz" + \
                               url_for("confirm_orgganisation", token=token)
                    mail.send(msg)
                    flash(
                        "Organisation Onboarded Successfully!!! Email Communication has been sent to Admin",
                        "success")

    return render_template('registration.html', form=form)


@app.route("/confirm/organisation/<token>", methods=["GET", "POST"])
def confirm_organisation(token):
    email = confirm_token(token)
    form = OrgConfirmationForm()
    try:
        role = current_user.get_urole().name
    except:
        role = None
    # For now only GET method is implemented will need post method for organisation
    # to enter client secret and client key for orcid
    if request.method == 'POST':
        if not form.validate():
            flash('Please fill in all fields and try again!', "danger")
        else:
            if email is False:
                app.login_manager.unauthorized()
            tuakiri_token = request.headers.get("Auedupersonsharedtoken")
            tuakiri_mail = request.headers['Mail']
            shib_org_name = request.headers['O']
            if email == tuakiri_mail:
                user = User.query.filter_by(email=email).first()
                organisation = Organisation.get(emailid=email)
                if (not (user is None) and (not (organisation is None))):
                    # Update Organisation
                    organisation.tuakiri_name = shib_org_name
                    organisation.confirmed = True
                    organisation.orcid_client_id = form.orgOricdClientId.data
                    organisation.orcid_secret = form.orgOrcidClientSecret.data

                    # Update Orcid User
                    user.confirmed = True
                    user.edu_person_shared_token = tuakiri_token
                    db.session.commit()
                    with app.app_context():
                        msg = Message("Welcome to OrcidhHub", recipients=[email])
                        msg.body = "Congratulations your emailid has been confirmed and " \
                            "organisation onboarded successfully."
                        mail.send(msg)
                        flash("Your Onboarding is Completed!!!", "success")
                    return redirect(url_for("login"))
                    # return render_template("login.html")
                else:
                    app.login_manager.unauthorized()
            else:
                app.login_manager.unauthorized()
    elif request.method == 'GET':

        if email is False:
            app.login_manager.unauthorized()
        form.orgEmailid.data = email
        form.orgName.data = request.headers['O']

    return render_template('orgconfirmation.html', form=form, role=role)


@app.after_request
def remove_if_invalid(response):
    """
    Removes stale session...
    """
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
    """
    Shows the logout info for UoA users.
    """
    flash("""You had logged in from 'The University of Auckland'.
You have to close all open browser tabs and windows in order
in order to complete the log-out.""", "warning")
    return render_template("uoa-slo.html")

# NB! Disable for the production!!!
@app.route("/reset_db")
@login_required
def reset_db():
    """
    Resets the DB for testing cycle
    """
    db.session.execute("DELETE FROM user WHERE name NOT LIKE '%Royal%'")
    db.session.execute("DELETE FROM organisation WHERE name NOT LIKE '%Royal%'")
    db.session.commit()
    return redirect(url_for("logout"))
