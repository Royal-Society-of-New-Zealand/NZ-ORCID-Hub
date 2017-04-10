# -*- coding: utf-8 -*-

"""Authentication views.

Collection of applicion views involved in organisation on-boarding and
user (reseaser) affiliations.
"""

from requests_oauthlib import OAuth2Session
from flask import request, redirect, session, url_for, render_template, flash, abort
from werkzeug.urls import iri_to_uri
from config import authorization_base_url, EDU_PERSON_AFFILIATION_EMPLOYMENT, EDU_PERSON_AFFILIATION_EDUCATION, \
    token_url, \
    scope_read_limited, scope_activities_update, MEMBER_API_FORM_BASE_URL, EDU_PERSON_AFFILIATION_MEMBER, \
    NEW_CREDENTIALS, NOTE_ORCID, CRED_TYPE_PREMIUM, APP_NAME, APP_DESCRIPTION, APP_URL, EXTERNAL_SP
import json
from application import app, mail
from models import User, Role, Organisation, UserOrg, OrcidToken
from urllib.parse import quote, unquote, urlencode, urlparse
from flask_login import login_user, current_user
from registrationForm import OrgRegistrationForm
from flask_mail import Message
from tokenGeneration import generate_confirmation_token, confirm_token
from registrationForm import OrgConfirmationForm
from flask_login import login_required, logout_user
from login_provider import roles_required
import base64
import zlib
import pickle
import secrets
from tempfile import gettempdir
from os import path, remove
import requests


@app.route("/index")
@app.route("/login")
@app.route("/")
def login():
    """Main landing page."""
    _next = request.args.get('next')
    if EXTERNAL_SP:
        session["auth_secret"] = secret_token = secrets.token_urlsafe()
        _next = url_for("shib_login", _next=_next, _external=True)
        shib_login_url = EXTERNAL_SP
        shib_login_url += ('&' if urlparse(EXTERNAL_SP).query else '?')
        shib_login_url += urlencode(dict(_next=_next, key=secret_token))
    else:
        shib_login_url = url_for("shib_login", _next=_next)

    return render_template("index.html", ship_login_url=shib_login_url)


@app.route("/Tuakiri/SP")
def shib_sp():
    """Remote Shibboleth authenitication handler.

    All it does passes all response headers to the original calller."""
    _next = request.args.get('_next')
    _key = request.args.get("key")
    if _next:
        data = {k: v for k, v in request.headers.items() if k in
                ["Auedupersonsharedtoken", 'Sn', 'Givenname', 'Mail', 'O', 'Displayname', 'unscoped-affiliation']}
        data = base64.b64encode(zlib.compress(pickle.dumps(data)))
        _next += ('&' if urlparse(_next).query else '?') + urlencode(dict(data=data))

        resp = redirect(_next)
        with open(path.join(gettempdir(), _key), 'wb') as kf:
            kf.write(data)

        return resp
    abort(403)


@app.route("/sp/attributes/<string:key>")
def get_attributes(key):
    """Retrieve SAML attributes."""
    data = ''
    data_filename = path.join(gettempdir(), key)
    try:
        with open(data_filename, 'rb') as kf:
            data = kf.read()
        remove(data_filename)
    except Exception as ex:
        abort(403, ex)
    return data


@app.route("/Tuakiri/login")
def shib_login():
    """Shibboleth authenitcation handler.

    The (Apache) location should requier authentication using Shibboleth, e.g.,

    <Location /Tuakiri>
        AuthType shibboleth
        ShibRequireSession On
        require valid-user
        ShibUseHeaders On
    </Location>


    Flow:
        * recieve redicected request from SSO with authentication data in HTTP headers
        * process headeers
        * if the organisation isn't on-boarded, reject further access and redirect to the main loging page;
        * if the user isn't registered add the user with data received from Shibboleth
        * if the request has returning destination (next), redirect the user to it;
        * else choose the next view based on the role of the user:
            ** for a researcher, affiliation;
            ** for super user, the on-boarding of an organisation;
            ** for organisation administrator or technical contact, the completion of the on-boarding.
    """
    _next = request.args.get('_next')
    data = request.args.get('data')
    # TODO: make it secret
    if EXTERNAL_SP:
        sp_url = urlparse(EXTERNAL_SP)
        attr_url = sp_url.scheme + "://" + sp_url.netloc + "/sp/attributes/" + session.get("auth_secret")
        data = requests.get(attr_url, verify=False).text
        data = pickle.loads(zlib.decompress(base64.b64decode(data)))
        token = data.get("Auedupersonsharedtoken")
        last_name = data['Sn']
        first_name = data['Givenname']
        email = data['Mail']
        session["shib_O"] = shib_org_name = data['O']
        name = data.get('Displayname')
        eduPersonAffiliation = data.get('Unscoped-Affiliation')
    else:
        token = request.headers.get("Auedupersonsharedtoken")
        last_name = request.headers['Sn']
        first_name = request.headers['Givenname']
        email = request.headers['Mail']
        session["shib_O"] = shib_org_name = request.headers['O']
        name = request.headers.get('Displayname')
        eduPersonAffiliation = request.headers.get('Unscoped-Affiliation')

    if eduPersonAffiliation:
        if any(epa in eduPersonAffiliation for epa in EDU_PERSON_AFFILIATION_EMPLOYMENT):
            eduPersonAffiliation = "employment"
        elif any(epa in eduPersonAffiliation for epa in EDU_PERSON_AFFILIATION_EDUCATION):
            eduPersonAffiliation = "education"
        elif any(epa in eduPersonAffiliation for epa in EDU_PERSON_AFFILIATION_MEMBER):
            eduPersonAffiliation == "member"
    else:
        flash(
            "The value of eduPersonAffiliation was not supplied from your identity provider,"
            " So we are not able to determine the nature of affiliation you have with your organisation",
            "danger")

    try:
        # TODO: need a separate field for org name comimg from Tuakiri
        org = Organisation.get(name=shib_org_name)
    except Organisation.DoesNotExist:
        org = None
        # flash("Your organisation (%s) is not onboarded properly, Contact Orcid Hub Admin" % shib_org_name, "danger")
        # return render_template("index.html", _next=_next)

    try:
        user = User.get(User.email == email)

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
        if eduPersonAffiliation:
            user.edu_person_affiliation = eduPersonAffiliation
            # TODO: keep login auditing (last_loggedin_at... etc)

    except User.DoesNotExist:
        user = User.create(
            email=email,
            name=name,
            first_name=first_name,
            last_name=last_name,
            confirmed=True,
            roles=Role.RESEARCHER,
            edu_person_shared_token=token,
            edu_person_affiliation=eduPersonAffiliation)

    if org is not None and org not in user.organisations:
        UserOrg.create(user=user, org=org)

        # TODO: need to find out a simple way of tracking
        # the organization user is logged in from:
    if org != user.organisation:
        user.organisation = org

    user.save()

    login_user(user)

    if _next:
        return redirect(_next)
    elif user.is_superuser:
        return redirect(url_for("invite_organisation"))
    elif org and org.confirmed:
        return redirect(url_for("link"))
    else:
        flash("Your organisation (%s) is not onboarded" %
              shib_org_name, "danger")

    return redirect(url_for("login"))


@app.route("/link")
@login_required
def link():
    """Link the user's account with ORCiD (i.e. affiliates user with his/her org on ORCID)."""
    # TODO: handle organisation that are not on-boarded
    redirect_uri = url_for("orcid_callback", _external=True)
    if EXTERNAL_SP:
        sp_url = urlparse(EXTERNAL_SP)
        redirect_uri = sp_url.scheme + "://" + sp_url.netloc + "/auth/" + quote(redirect_uri)

    client = OAuth2Session(current_user.organisation.orcid_client_id, scope=scope_read_limited,
                           redirect_uri=redirect_uri)
    authorization_url, state = client.authorization_url(authorization_base_url)
    session['oauth_state'] = state

    client_write = OAuth2Session(current_user.organisation.orcid_client_id, scope=scope_activities_update,
                                 redirect_uri=redirect_uri)
    authorization_url_write, state = client_write.authorization_url(
        authorization_base_url)

    orcid_url = iri_to_uri(authorization_url) + urlencode(dict(
        family_names=current_user.last_name, given_names=current_user.first_name, email=current_user.email))

    orcid_url_write = iri_to_uri(authorization_url_write) + urlencode(dict(
        family_names=current_user.last_name, given_names=current_user.first_name, email=current_user.email))

    # Check if user details are already in database
    # TODO: re-affiliation after revoking access?
    # TODO: affiliation with multiple orgs should lookup UserOrg

    user = User.get(email=current_user.email,
                    organisation=current_user.organisation)
    orcidTokenRead = None
    orcidTokenWrite = None
    try:
        orcidTokenRead = OrcidToken.get(
            user=user, org=user.organisation, scope=scope_read_limited)
    except:
        pass
    try:
        orcidTokenWrite = OrcidToken.get(
            user=user, org=user.organisation, scope=scope_activities_update)
    except:
        pass

    if ((orcidTokenRead is not None) and (orcidTokenWrite is not None)):
        flash("You have already given read and write permissions to '%s' and your ORCiD %s" % (
            current_user.organisation.name, current_user.orcid), "warning")
        return redirect(url_for("profile"))
    elif orcidTokenRead:
        flash("You have already given read permissions to '%s' and your ORCiD %s" % (
            current_user.organisation.name, current_user.orcid), "warning")
        return render_template("linking.html", orcid_url_write=orcid_url_write)
    elif orcidTokenWrite:
        flash("You have already given write permissions to '%s' and your ORCiD %s" % (
            current_user.organisation.name, current_user.orcid), "warning")
        return render_template("linking.html", orcid_url=orcid_url)

    return render_template("linking.html", orcid_url=orcid_url, orcid_url_write=orcid_url_write)


@app.route("/auth/<path:url>", methods=["GET"])
def orcid_callback_proxy(url):
    url = unquote(url)
    return redirect(url + '?' + urlencode(request.args))


# Step 2: User authorization, this happens on the provider.
@app.route("/auth", methods=["GET"])
@login_required
def orcid_callback():
    """Retrieve an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """
    client = OAuth2Session(current_user.organisation.orcid_client_id)
    token = client.fetch_token(token_url, client_secret=current_user.organisation.orcid_secret,
                               authorization_response=request.url)
    # #print(token)
    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_token'] = token
    app.logger.info("* TOKEN: %s", token)
    orcid = token['orcid']
    name = token["name"]

    # TODO: should be linked to the affiliated org

    user = current_user
    user.orcid = orcid
    if not user.name and name:
        user.name = name

    orciduser = User.get(email=user.email, organisation=user.organisation)

    orcidToken = OrcidToken.create(user=orciduser, org=orciduser.organisation, scope=token["scope"][0],
                                   access_token=token["access_token"], refresh_token=token["refresh_token"], )
    orcidToken.save()
    user.save()

    flash("Your account was linked to ORCiD %s" % orcid, "success")

    return redirect(url_for("profile"))


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """Fetch a protected resource using an OAuth 2 token."""

    user = User.get(email=current_user.email,
                    organisation=current_user.organisation)

    orcidTokenRead = None
    try:
        orcidTokenRead = OrcidToken.get(
            user=user, org=user.organisation, scope=scope_read_limited)
    except:
        flash("You need to link your ORCiD with your account", "warning")
        return redirect(url_for("link"))

    client = OAuth2Session(user.organisation.orcid_client_id, token={
        "access_token": orcidTokenRead.access_token})

    headers = {'Accept': 'application/vnd.orcid+json'}
    resp = client.get("https://api.sandbox.orcid.org/v2.0/" +
                      user.orcid + "/works", headers=headers)
    return render_template(
        "profile.html",
        user=user,
        data=json.loads(resp.text))


@app.route("/invite/user", methods=["GET"])
@roles_required(Role.SUPERUSER, Role.ADMIN)
def invite_user():
    """Invite a researcher to join the hub."""
    # For now on boarding of researcher is not supported
    return "Work in Progress!!!"


# TODO: user can be admin for multiple org and org can have multiple admins:
# TODO: user shoud be assigned exclicitly organization
# TODO: OrgAdmin ...
# TODO: gracefully handle all exceptions (repeated infitation, user is
# already an admin for the organization etc.)
@app.route("/invite/organisation", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER)
def invite_organisation():
    """Invite an organisation to register.

    Flow:
        * Hub administrort (super user) invokes the page,
        * Fills in the form with the organisation and organisation technica contatct data (including an email address);
        * Submits the form;
        * A secure registration token gets ceated;
        * An email message with confirmation link gets created and sent off to the technical contact.
    """
    form = OrgRegistrationForm()
    if request.method == "POST":
        if not form.validate():
            flash("Please fill in all fields and try again.", "danger")
        else:
            email = form.orgEmailid.data
            org_name = form.orgName.data
            try:
                User.get(User.email == form.orgEmailid.data)
                flash(
                    "This Email address is already an Admin for one of the organisation", "warning")
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
                    user.roles = Role.ADMIN
                    user.organisation = org
                except User.DoesNotExist:
                    user = User(
                        name=form.orgName.data,
                        email=form.orgEmailid.data,
                        confirmed=True,  # In order to let the user in...
                        roles=Role.ADMIN,
                        organisation=org)
                user.save()
                # Note: Using app context due to issue:
                # https://github.com/mattupstate/flask-mail/issues/63
                with app.app_context():
                    msg = Message("Welcome to OrcidhHub",
                                  recipients=[str(form.orgEmailid.data)])
                    token = generate_confirmation_token(form.orgEmailid.data)
                    # TODO: do it with templates
                    msg.body = "Your organisation is just one step behind to get onboarded" \
                               " please click on following link to get onboarded " + \
                               url_for("confirm_organisation",
                                       token=token, _external=True)
                    mail.send(msg)
                    flash(
                        "Organisation Onboarded Successfully!!! Email Communication has been sent to Admin",
                        "success")

    return render_template('registration.html', form=form)


@app.route("/confirm/organisation/<token>", methods=["GET", "POST"])
@login_required
def confirm_organisation(token):
    """Registration confirmations.

    TODO: expand the spect as soon as the reqirements get sorted out.
    """
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

        redirect_uri = url_for("orcid_callback", _external=True)
        clientSecret_url = iri_to_uri(MEMBER_API_FORM_BASE_URL) + "?" + urlencode(dict(
            new_existing=NEW_CREDENTIALS, note=NOTE_ORCID + " " + user.organisation.name,
            contact_email=email, contact_name=user.name, org_name=user.organisation.name,
            cred_type=CRED_TYPE_PREMIUM, app_name=APP_NAME + " at " + user.organisation.name,
            app_description=APP_DESCRIPTION + " at " + user.organisation.name,
            app_url=APP_URL, redirect_uri_1=redirect_uri))

    return render_template('orgconfirmation.html', clientSecret_url=clientSecret_url, form=form)


@app.after_request
def remove_if_invalid(response):
    """Remove a stale session and session cookie."""
    if "__invalidate__" in session:
        response.delete_cookie(app.session_cookie_name)
        session.clear()
    return response


@app.route("/logout")
def logout():
    """Log out a logged user.

    Note: if the user has logged in via the University of Auckland SSO,
    show the message about the log out procedure and the linke to the instruction
    about SSO at the university.
    """
    org_name = session.get("shib_O")
    try:
        logout_user()
    except Exception as ex:
        app.logger.error("Failed to logout: %s", ex)

    session.clear()
    session["__invalidate__"] = True

    if EXTERNAL_SP:
        sp_url = urlparse(EXTERNAL_SP)
        sso_url_base = sp_url.scheme + "://" + sp_url.netloc
    else:
        sso_url_base = ''
    return redirect(
        sso_url_base + "/Shibboleth.sso/Logout?return=" +
        quote(url_for("uoa_slo" if org_name and org_name == "University of Auckland" else "login", _external=True)))


@app.route("/uoa-slo")
def uoa_slo():
    """Show the logout info for UoA users."""
    flash("""You had logged in from 'The University of Auckland'.
You have to close all open browser tabs and windows in order
in order to complete the log-out.""", "warning")
    return render_template("uoa-slo.html")


# NB! Disable for the production!!!
@app.route("/reset_db")
@login_required
def reset_db():
    """Reset the DB for a new testing cycle."""
    User.delete().where(~(User.name ** "royal" | User.name ** "%root%")).execute()
    Organisation.delete().where(~(Organisation.name % "%Royal%")).execute()
    return redirect(url_for("logout"))


@app.route("/viewmembers")
@roles_required(Role.ADMIN)
def viewmembers():
    """View the list of users (researchers)."""
    user = current_user
    users = user.organisation.users
    return render_template("viewMembers.html", orgnisationname=user.organisation.name, users=users)
