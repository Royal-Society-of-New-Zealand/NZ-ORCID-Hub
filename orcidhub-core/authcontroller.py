from requests_oauthlib import OAuth2Session
from flask import request, redirect, session, url_for, render_template, flash
from werkzeug.urls import iri_to_uri
from config import client_id, client_secret, authorization_base_url, \
    token_url, scope, redirect_uri, MEMBER_AIP_FORM_BASE_URL_SANDBOX, \
    NEW_CREDENTIALS, NOTE_ORCID, CRED_TYPE_PREMIUM, APP_NAME, APP_DESCRIPTION, APP_URL
import json
from application import app, db, mail
from models import User, Role, Organisation, UserOrg
from urllib.parse import quote
from flask_login import login_user, current_user
from registrationForm import OrgRegistrationForm
from flask_mail import Message
from tokenGeneration import generate_confirmation_token, confirm_token
from registrationForm import OrgConfirmationForm
from flask_login import login_required, logout_user
from login_provider import roles_required
from os import environ
from urllib.parse import urlencode


@app.route("/index")
@app.route("/login")
@app.route("/")
def login():
    """
    Main landing page.
    """
    _next = request.args.get('next')
    return render_template("index.html", _next=_next)


@app.route("/Tuakiri/login")
def shib_login():

    _next = request.args.get('_next')
    token = request.headers.get("Auedupersonsharedtoken")
    last_name = request.headers['Sn']
    first_name = request.headers['Givenname']
    email = request.headers['Mail']
    session["shib_O"] = shib_org_name = request.headers['O']
    name = request.headers.get('Displayname')

    try:
        org = Organisation.get(name=shib_org_name)
    except Organisation.DoesNotExist:
        org = None

    try:
        user = User.get(User.email == email)
        if org is not None and org not in user.organisations:
            UserOrg.create(user=user, org=org)

            # TODO: need to find out a simple way of tracking
            # the organization user is logged in from:
            if org != user.organisation:
                user.organisation = org

        # Add Shibboleth meta data if they are missing
        if not user.edu_person_shared_token:
            user.edu_person_shared_token = token
        if not user.name or org is not None and user.name == org.name and name:
            user.name = name
        if not user.first_name and first_name:
            user.firts_name = first_name
        if not user.last_name and last_name:
            user.last_name = last_name
        if not user.confirmed:
            user.confirmed = True
        # TODO: keep login auditing (last_loggedin_at... etc)

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

    if _next:
        return redirect(_next)
    elif user.is_superuser:
        return redirect(url_for("invite_organisation"))
    elif org and org.confirmed:
        return redirect(url_for("link"))
    else:
        flash("Your organisation (%s) is not onboarded" % shib_org_name, "danger")

    return redirect(url_for("login"))


@app.route("/link")
@login_required
def link():
    """
    Links the user's account with ORCiD (i.e. affiliates user with his/her org on ORCID)
    """
    client = OAuth2Session(client_id, scope=scope, redirect_uri=redirect_uri)
    authorization_url, state = client.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    # Check if user details are already in database
    if current_user.orcid:
        flash("You have already affilated '%s' with your ORCiD %s" % (
            current_user.organisation.name, current_user.orcid), "warning")
        return redirect(url_for("profile"))

    orcid_url = iri_to_uri(authorization_url) + urlencode(dict(
        family_names=current_user.last_name, given_names=current_user.first_name, email=current_user.email))

    return render_template("linking.html", orcid_url=orcid_url)


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
    app.logger.info("* TOKEN: %s", token)
    orcid = token['orcid']
    name = token["name"]
    access_token = token["access_token"]
    user = current_user
    user.orcid = orcid
    if not user.name and name:
        user.name = name
    user.access_token = access_token
    user.save()

    flash("Your account was linked to ORCiD %s" % orcid, "success")

    return redirect(url_for("profile"))


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """Fetching a protected resource using an OAuth 2 token.
    """
    user = current_user
    if user.orcid is None:
        flash("You need to link your ORCiD with your account", "warning")
        return redirect(url_for("link"))

    client = OAuth2Session(client_id, token={"access_token": user.access_token})

    headers = {'Accept': 'application/json'}
    resp = client.get("https://api.sandbox.orcid.org/v1.2/" +
                      user.orcid + "/orcid-works", headers=headers)
    return render_template(
        "profile.html",
        user=user,
        data=json.loads(resp.text))


@app.route("/invite/user", methods=["GET"])  # /invite/user
@roles_required(Role.SUPERUSER, Role.ADMIN)
def invite_user():
    # For now on boarding of researcher is not supported
    return "Work in Progress!!!"


# TODO: user can be admin for multiple org and org can have multiple admins:
# TODO: user shoud be assigned exclicitly organization
# TODO: OrgAdmin ...
# TODO: gracefully handle all exceptions (repeated infitation, user is already an admin for the organization etc.)
@app.route("/invite/organisation", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER)
def invite_organisation():
    form = OrgRegistrationForm()
    if request.method == "POST":
        if not form.validate():
            flash("Please fill in all fields and try again.", "danger")
        else:
            email = form.orgEmailid.data
            org_name = form.orgName.data
            try:
                User.get(User.email == form.orgEmailid.data)
                flash("This Email address is already an Admin for one of the organisation", "warning")
            except User.DoesNotExist:
                pass
            finally:
                # TODO: organisation can have mutiple admins:
                # TODO: user OrgAdmin
                try:
                    org = Organisation.get(name=org_name)
                    # TODO: fix it!
                    org.email = email
                except Organisation.DoesNotExist:
                    org = Organisation(name=org_name, email=email)
                org.save()

                try:
                    user = User.get(email=email)
                    user.roles |= Role.ADMIN
                    user.organisation = org
                except User.DoesNotExist:
                    user = User(
                        name=form.orgName.data,
                        email=form.orgEmailid.data,
                        confirmed=True,  # In order to let the user in...
                        roles=Role.ADMIN,
                        organisation=org)
                user.save()
                # Note: Using app context due to issue: https://github.com/mattupstate/flask-mail/issues/63
                with app.app_context():
                    msg = Message("Welcome to OrcidhHub",
                                  recipients=[str(form.orgEmailid.data)])
                    token = generate_confirmation_token(form.orgEmailid.data)
                    # TODO: do it with templates
                    msg.body = "Your organisation is just one step behind to get onboarded" \
                               " please click on following link to get onboarded " \
                               "https://" + environ.get("ENV", "dev") + ".orcidhub.org.nz" + \
                               url_for("confirm_organisation", token=token)
                    mail.send(msg)
                    flash(
                        "Organisation Onboarded Successfully!!! Email Communication has been sent to Admin",
                        "success")

    return render_template('registration.html', form=form)


@app.route("/confirm/organisation/<token>", methods=["GET", "POST"])
@login_required
def confirm_organisation(token):
    clientSecret_url = None
    email = confirm_token(token)
    user = current_user

    if not email:
        app.error("token '%s'", token)
        app.login_manager.unauthorized()
    if user.email != email:
        flash("The invitation to on-board the organisation wasn't sent to your email address...", "danger")
        return redirect(url_for("login"))

    # TODO: support for mutliple orgs and admins
    # TODO: admin role asigning to an exiting user
    # TODO: support for org not participating in Tuakiri
    form = OrgConfirmationForm()

    # For now only GET method is implemented will need post method for organisation
    # to enter client secret and client key for orcid
    if request.method == 'POST':
        if not form.validate():
            flash('Please fill in all fields and try again!', "danger")
        else:
            organisation = Organisation.get(email=email)
            if (not (user is None) and (not (organisation is None))):
                # Update Organisation
                organisation.confirmed = True
                organisation.orcid_client_id = form.orgOricdClientId.data
                organisation.orcid_secret = form.orgOrcidClientSecret.data
                organisation.save()

                # Update Orcid User
                user.confirmed = True
                user.save()
                with app.app_context():
                    msg = Message("Welcome to OrcidhHub", recipients=[email])
                    msg.body = "Congratulations your emailid has been confirmed and " \
                               "organisation onboarded successfully."
                    mail.send(msg)
                    flash("Your Onboarding is Completed!!!", "success")
                return redirect(url_for("login"))

    elif request.method == 'GET':

        form.orgEmailid.data = email
        form.orgName.data = user.organisation.name

        flash("""If you currently don't know Client id and Client Secret,
        Please request those by clicking on link 'Take me to ORCiD to obtain Client iD and Client Secret'
        and come back to this same place once you have them within 15 days""", "warning")

        clientSecret_url = iri_to_uri(MEMBER_AIP_FORM_BASE_URL_SANDBOX) + "?" + urlencode(dict(
            new_existing=NEW_CREDENTIALS, note=NOTE_ORCID + " " + user.organisation.name,
            contact_email=email, contact_name=user.name, org_name=user.organisation.name,
            cred_type=CRED_TYPE_PREMIUM, app_name=APP_NAME + " at " + user.organisation.name,
            app_description=APP_DESCRIPTION + " at " + user.organisation.name,
            app_url=APP_URL, redirect_uri_1=redirect_uri))

    return render_template('orgconfirmation.html', clientSecret_url=clientSecret_url, form=form)


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
    try:
        logout_user()
    except Exception as ex:
        app.logger.error("Failed to logout: %s", ex)

    session.clear()
    session["__invalidate__"] = True
    return redirect(
        "/Shibboleth.sso/Logout?return=" +
        quote(url_for("uoa_slo" if org_name and org_name == "University of Auckland" else "login")))


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
    db.execute_sql("DELETE FROM \"user\" WHERE name !~ 'Royal' AND name != 'The Root' RETURNING id")
    db.execute_sql("DELETE FROM organisation WHERE name !~ 'Royal'")
    db.commit()
    return redirect(url_for("logout"))
