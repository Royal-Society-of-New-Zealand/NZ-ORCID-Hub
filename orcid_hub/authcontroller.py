# -*- coding: utf-8 -*-
"""Authentication views.

Collection of applicion views involved in organisation on-boarding and
user (reseaser) affiliations.
"""

import base64
import json
import pickle
import re
import secrets
import traceback
import zlib
from datetime import datetime
from os import path, remove
from tempfile import gettempdir
from time import time
from urllib.parse import quote, unquote, urlparse

import requests
from flask import (abort, current_app, flash, g, redirect, render_template, request, session,
                   url_for)
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message
from oauthlib.oauth2 import rfc6749
from requests_oauthlib import OAuth2Session
from swagger_client.rest import ApiException
from werkzeug.urls import iri_to_uri

from . import app, db, mail, orcid_client, sentry
# TODO: need to read form app.config[...]
from .config import (APP_DESCRIPTION, APP_NAME, APP_URL, AUTHORIZATION_BASE_URL, CRED_TYPE_PREMIUM,
                     ENV, EXTERNAL_SP, MEMBER_API_FORM_BASE_URL, NOTE_ORCID, ORCID_API_BASE,
                     ORCID_BASE_URL, ORCID_CLIENT_ID, ORCID_CLIENT_SECRET, SCOPE_ACTIVITIES_UPDATE,
                     SCOPE_AUTHENTICATE, SCOPE_READ_LIMITED, TOKEN_URL)
from .forms import OrgConfirmationForm
from .login_provider import roles_required
from .models import (Affiliation, OrcidAuthorizeCall, OrcidToken, Organisation, OrgInfo,
                     OrgInvitation, Role, Url, User, UserInvitation, UserOrg)
from .utils import append_qs, confirm_token

HEADERS = {'Accept': 'application/vnd.orcid+json', 'Content-type': 'application/vnd.orcid+json'}


@app.context_processor
def utility_processor():  # noqa: D202
    """Define funcions callable form Jinja2 using application context."""

    def onboarded_organisations():
        return list(
            Organisation.select(Organisation.name, Organisation.tuakiri_name).where(
                Organisation.confirmed.__eq__(True)))

    def orcid_login_url():
        return url_for("orcid_login", next=get_next_url())

    def tuakiri_login_url():
        _next = get_next_url()
        if EXTERNAL_SP:
            session["auth_secret"] = secret_token = secrets.token_urlsafe()
            _next = url_for("handle_login", _next=_next, _external=True)
            login_url = append_qs(EXTERNAL_SP, _next=_next, key=secret_token)
        else:
            login_url = url_for("handle_login", _next=_next)
        return login_url

    return dict(
        orcid_login_url=orcid_login_url,
        tuakiri_login_url=tuakiri_login_url,
        onboarded_organisations=onboarded_organisations,
    )


def get_next_url():
    """Retrieve and sanitize next/return URL."""
    _next = request.args.get("next") or request.args.get("_next")

    if _next and ("orcidhub.org.nz" in _next or _next.startswith("/") or "127.0" in _next
                  or "c9users.io" in _next):
        return _next
    return None


@app.route("/index.html")
@app.route("/index")
@app.route("/login")
@app.route("/")
def login():
    """Show main landing page with login buttons."""
    return render_template("index.html")


@app.route("/about.html")
@app.route("/about")
def about():
    """Show about page with login buttons."""
    return render_template("about.html")


@app.route("/faq.html")
@app.route("/faq")
def faq():
    """Show FAQ page with login buttons."""
    return render_template("faq.html")


@app.route("/Tuakiri/SP")
def shib_sp():
    """Remote Shibboleth authenitication handler.

    All it does passes all response headers to the original calller.
    """
    _next = get_next_url()
    _key = request.args.get("key")
    if _next:
        data = {k: v for k, v in request.headers.items()}
        data = base64.b64encode(zlib.compress(pickle.dumps(data)))

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
def handle_login():
    """Shibboleth and Rapid Connect authenitcation handler.

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
    _next = get_next_url()

    # TODO: make it secret
    if EXTERNAL_SP:
        if "auth_secret" not in session:
            return redirect(url_for("login"))
        sp_url = urlparse(EXTERNAL_SP)
        attr_url = sp_url.scheme + "://" + sp_url.netloc + "/sp/attributes/" + session.get(
            "auth_secret")
        data = requests.get(attr_url, verify=False).text
        data = pickle.loads(zlib.decompress(base64.b64decode(data)))
    else:
        data = request.headers

    try:
        last_name = data['Sn'].encode("latin-1").decode("utf-8")
        first_name = data['Givenname'].encode("latin-1").decode("utf-8")
        email, *secondary_emails = re.split("[,; \t]",
                                            data['Mail'].encode("latin-1").decode("utf-8").lower())
        session["shib_O"] = shib_org_name = data['O'].encode("latin-1").decode("utf-8")
        name = data.get('Displayname').encode("latin-1").decode("utf-8")
        eppn = data.get('Eppn').encode("latin-1").decode("utf-8")
        unscoped_affiliation = set(a.strip()
                                   for a in data.get("Unscoped-Affiliation", '').encode("latin-1")
                                   .decode("utf-8").replace(',', ';').split(';'))
        app.logger.info(
            f"User with email address {email} (eppn: {eppn} is trying "
            f"to login having affiliation as {unscoped_affiliation} with {shib_org_name}")
        if secondary_emails:
            app.logger.info(
                f"the user has logged in with secondary email addresses: {secondary_emails}")

    except Exception as ex:
        app.logger.exception("Failed to login via TUAKIRI.")
        abort(500, ex)

    try:
        org = Organisation.get((Organisation.tuakiri_name == shib_org_name)
                               | (Organisation.name == shib_org_name))
    except Organisation.DoesNotExist:
        org = Organisation(tuakiri_name=shib_org_name)
        # try to get the official organisation name:
        try:
            org_info = OrgInfo.get((OrgInfo.tuakiri_name == shib_org_name)
                                   | (OrgInfo.name == shib_org_name))
        except OrgInfo.DoesNotExist:
            org.name = shib_org_name
        else:
            org.name = org_info.name
        try:
            org.save()
        except Exception as ex:
            flash(f"Failed to save organisation data: {ex}")
            app.logger.exception(f"Failed to save organisation data: {ex}")

    q = User.select().where(User.email == email)
    if eppn:
        q = q.orwhere(User.eppn == eppn)
    if secondary_emails:
        q = q.orwhere(User.email.in_(secondary_emails))
    user = q.first()

    if user:
        # Add Shibboleth meta data if they are missing
        if not user.name or org is not None and user.name == org.name and name:
            user.name = name
        if not user.first_name and first_name:
            user.first_name = first_name
        if not user.last_name and last_name:
            user.last_name = last_name
        if not user.eppn and eppn:
            user.eppn = eppn
    else:

        if ENV != "dev" and not (unscoped_affiliation & {"faculty", "staff", "student"}):
            msg = f"Access Denied! Your account (email: {email}, eppn: {eppn}) is not affiliated with '{shib_org_name}'"
            app.logger.error(msg)
            flash(msg, "danger")
            return redirect(url_for("login"))

        user = User.create(
            email=email,
            eppn=eppn,
            name=name,
            first_name=first_name,
            last_name=last_name,
            roles=Role.RESEARCHER)

    # TODO: need to find out a simple way of tracking
    # the organization user is logged in from:
    if org != user.organisation:
        user.organisation = org

    edu_person_affiliation = Affiliation.NONE
    if unscoped_affiliation:
        if unscoped_affiliation & {"faculty", "staff"}:
            edu_person_affiliation |= Affiliation.EMP
        if unscoped_affiliation & {"student"}:
            edu_person_affiliation |= Affiliation.EDU
    else:
        app.logger.warning(f"The value of 'Unscoped-Affiliation' was not supplied for {user}")

    if org:
        user_org, _ = UserOrg.get_or_create(user=user, org=org)
        user_org.affiliations = edu_person_affiliation
        user_org.save()

    if not user.confirmed:
        user.confirmed = True

    try:
        user.save()
    except Exception as ex:
        flash(f"Failed to save user data: {ex}")
        app.logger.exception(f"Failed to save user {user} data.")

    login_user(user)
    app.logger.info("User %r from %r logged in.", user, org)

    if _next:
        return redirect(_next)
    elif user.is_superuser:
        return redirect(url_for("invite_organisation"))
    elif org and org.confirmed:
        app.logger.info("User %r organisation is onboarded", user)
        return redirect(url_for("link"))
    elif org and (not org.confirmed) and user.is_tech_contact_of(org):
        app.logger.info("User %r is org admin and organisation is not onboarded", user)
        return redirect(url_for("onboard_org"))
    else:
        flash(f"Your organisation ({shib_org_name}) is not yet using the Hub, "
              f"see your Technical Contact for a timeline", "warning")
        app.logger.info("User %r organisation is not onboarded", user)

    return redirect(url_for("login"))


@app.route("/link")
@login_required
def link():
    """Link the user's account with ORCID (i.e. affiliates user with his/her org on ORCID)."""
    # TODO: handle organisation that are not on-boarded
    redirect_uri = url_for("orcid_callback", _external=True)
    if EXTERNAL_SP:
        sp_url = urlparse(EXTERNAL_SP)
        redirect_uri = sp_url.scheme + "://" + sp_url.netloc + "/auth/" + quote(redirect_uri)

    if current_user.organisation and not current_user.organisation.confirmed:
        flash(f"Your organisation ({current_user.organisation.name}) is not yet using the Hub,"
              f" see your Technical Contact for a timeline", "warning")
        return redirect(url_for("login"))

    client_write = OAuth2Session(
        current_user.organisation.orcid_client_id,
        scope=SCOPE_ACTIVITIES_UPDATE + SCOPE_READ_LIMITED,
        redirect_uri=redirect_uri)
    authorization_url_write, state = client_write.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state

    orcid_url_write = append_qs(
        iri_to_uri(authorization_url_write),
        family_names=current_user.last_name,
        given_names=current_user.first_name,
        email=current_user.email)

    # Check if user details are already in database
    # TODO: re-affiliation after revoking access?
    # TODO: affiliation with multiple orgs should lookup UserOrg

    try:
        OrcidToken.get(user_id=current_user.id, org=current_user.organisation)
        app.logger.info("We have the %r ORCID token ", current_user)
    except OrcidToken.DoesNotExist:
        app.logger.info(
            "User %r orcid token does not exist in database, So showing the user orcid permission button",
            current_user)
        if "error" in request.args:
            error = request.args["error"]
            if error == "access_denied":
                app.logger.info(
                    "User %r has denied permissions to %r in the flow and will try to give permissions again",
                    current_user.id, current_user.organisation)
                client_write.scope = SCOPE_READ_LIMITED
                authorization_url_read, state = client_write.authorization_url(
                    AUTHORIZATION_BASE_URL, state)
                orcid_url_read = append_qs(
                    iri_to_uri(authorization_url_read),
                    family_names=current_user.last_name,
                    given_names=current_user.first_name,
                    email=current_user.email)
                client_write.scope = SCOPE_AUTHENTICATE
                authorization_url_authenticate, state = client_write.authorization_url(
                    AUTHORIZATION_BASE_URL, state)
                orcid_url_authenticate = append_qs(
                    iri_to_uri(authorization_url_authenticate),
                    family_names=current_user.last_name,
                    given_names=current_user.first_name,
                    email=current_user.email)
                oac, orcid_authorize_call_found = OrcidAuthorizeCall.get_or_create(
                    user_id=current_user.id, method="GET", url=orcid_url_write, state=state)
                oac.url = "Access_Denied Flow " + orcid_url_write + orcid_url_read + orcid_url_authenticate
                oac.save()
                return render_template(
                    "linking.html",
                    orcid_url_write=orcid_url_write,
                    orcid_url_read_limited=orcid_url_read,
                    orcid_url_authenticate=orcid_url_authenticate,
                    error=error)
        oac = OrcidAuthorizeCall.create(
            user_id=current_user.id, method="GET", url=orcid_url_write, state=state)
        oac.save()
        return render_template(
            "linking.html", orcid_url_write=orcid_url_write, orcid_base_url=ORCID_BASE_URL)
    except Exception as ex:
        flash(f"Unhandled Exception occured: {ex}")
        app.logger.exception("Failed to initiate or link user account with ORCID.")
    return redirect(url_for("profile"))


@app.route("/orcid/auth/<path:url>")
@app.route("/auth/<path:url>")
def orcid_callback_proxy(url):
    """Redirect to the original invokator."""
    url = unquote(url)
    return redirect(append_qs(url, **request.args))


# Step 2: User authorization, this happens on the provider.
@app.route("/auth", methods=["GET"])
def orcid_callback():
    """Retrieve an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.


    Call back gets called when:
    - User authenticatest via ORCID (uses AUTHENTICATION key);
    - User authorises an orgainisation (uses org. key);
    - User completes registration (uses org. key);
    - Administrator completes reginstration (uses org. key);
    - Technical contact completes organisation registration/on-boarding (uses AUTHENTICATION key);
    """
    login = request.args.get("login")
    # invitation_token = request.args.get("invitation_token")

    if login != "1":
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
    else:
        return orcid_login_callback(request)

    if "error" in request.args:
        error = request.args["error"]
        error_description = request.args.get("error_description")
        if error == "access_denied":
            flash("You have denied {current_user.organisation.name} access to your ORCID record."
                  " Please choose from one of the four options below.", "warning")
        else:
            flash(
                f"Error occured while attempting to authorize '{current_user.organisation.name}': {error_description}",
                "danger")
        return redirect(url_for("link", error=error))

    client = OAuth2Session(current_user.organisation.orcid_client_id)

    try:
        state = request.args['state']
        if state != session.get('oauth_state'):
            flash("Retry giving permissions, or if the issue persist "
                  "please contact orcid@royalsociety.org.nz for support", "danger")
            app.logger.error(
                f"For {current_user} session state was {session.get('oauth_state', 'empty')}, "
                f"whereas state returned from ORCID is {state}")
            return redirect(url_for("login"))

        oac, orcid_authorize_call_found = OrcidAuthorizeCall.get_or_create(state=state)
        request_time = time()

        token = client.fetch_token(
            TOKEN_URL,
            client_secret=current_user.organisation.orcid_secret,
            authorization_response=request.url)
        response_time = time()
        oac.token = token
        oac.response_time_ms = round((response_time - request_time) * 1000)
        oac.save()

    except rfc6749.errors.MissingCodeError:
        flash("%s cannot be invoked directly..." % request.url, "danger")
        return redirect(url_for("login"))
    except rfc6749.errors.MissingTokenError:
        flash("Missing token.", "danger")
        return redirect(url_for("login"))
    except Exception as ex:
        flash(f"Something went wrong contact orcidhub support for issue: {ex}")
        app.logger.exception(f"For {current_user} encountered exception")
        return redirect(url_for("login"))

    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_token'] = token
    orcid = token['orcid']
    name = token["name"]

    user = current_user
    user.orcid = orcid
    if not user.name and name:
        user.name = name

    scope = ''
    if len(token["scope"]) >= 1 and token["scope"][0] is not None:
        scope = token["scope"][0]
    else:
        flash("Scope missing, contact orcidhub support", "danger")
        app.logger.error("For %r encountered exception: Scope missing", current_user)
        return redirect(url_for("login"))
    if len(token["scope"]) >= 2 and token["scope"][1] is not None:
        scope = scope + "," + token["scope"][1]

    orcid_token, orcid_token_found = OrcidToken.get_or_create(
        user_id=user.id, org=user.organisation, scope=scope)
    orcid_token.access_token = token["access_token"]
    orcid_token.refresh_token = token["refresh_token"]
    with db.atomic():
        try:
            orcid_token.save()
            user.save()
        except Exception as ex:
            db.rollback()
            flash(f"Failed to save data: {ex}")
            app.logger.exception("Failed to save ORCID token.")

    app.logger.info("User %r authorized %r to have %r access to the profile "
                    "and now trying to update employment or education record", user,
                    user.organisation, scope)
    if scope == SCOPE_READ_LIMITED[0] + "," + SCOPE_ACTIVITIES_UPDATE[0] and orcid_token_found:
        api = orcid_client.MemberAPI(user=user, access_token=orcid_token.access_token)

        for a in Affiliation:

            if not a & user.affiliations:
                continue

            try:
                api.create_or_update_affiliation(initial=True, affiliation=a)
            except ApiException as ex:
                flash(f"Failed to update the entry: {ex.body}", "danger")
            except Exception as ex:
                app.logger.exception(f"For {user} encountered exception")

        if not user.affiliations:
            flash(
                f"The ORCID Hub was not able to automatically write an affiliation with "
                f"{user.organisation}, as the nature of the affiliation with your "
                f"organisation does not appear to include either Employment or Education.\n "
                f"Please contact your Organisation Administrator(s) if you believe this is an error.",
                "warning")

    session['Should_not_logout_from_ORCID'] = True
    return redirect(url_for("profile"))


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """Fetch a protected resource using an OAuth 2 token."""
    user = current_user
    app.logger.info(f"For {user} trying to display profile by getting ORCID token")
    try:
        orcid_token = OrcidToken.get(user_id=user.id, org=user.organisation)
    except OrcidToken.DoesNotExist:
        app.logger.info(f"For {user} we dont have ocrditoken so redirecting back to link page")
        return redirect(url_for("link"))

    except Exception as ex:
        # TODO: need to handle this
        app.logger.exception("Failed to retrieve ORCID token form DB.")
        flash("Unhandled Exception occured: %s" % ex, "danger")
        return redirect(url_for("login"))
    else:
        client = OAuth2Session(
            user.organisation.orcid_client_id, token={
                "access_token": orcid_token.access_token
            })
        base_url = ORCID_API_BASE + user.orcid
        # TODO: utilize asyncio/aiohttp to run it concurrently
        resp_person = client.get(base_url + "/person", headers=HEADERS)
        app.logger.info("For %r logging response code %r, While fetching profile info", user,
                        resp_person.status_code)
        if resp_person.status_code == 401:
            orcid_token.delete_instance()
            app.logger.info("%r has removed his organisation from trusted list", user)
            return redirect(url_for("link"))
        else:
            users = User.select().where(User.orcid == user.orcid)
            users_orcid = OrcidToken.select().where(OrcidToken.user.in_(users))
            app.logger.info("For %r everything is fine, So displaying profile page", user)
            return render_template(
                "profile.html", user=user, users_orcid=users_orcid, profile_url=ORCID_BASE_URL)


@app.route("/orcid/request_credentials")
@roles_required(Role.TECHNICAL)
def request_orcid_credentials():
    """Redirect to the ORCID for the technical conact of the organisation.

    Additionally the time stamp gets saved when the handler gets invoked.
    """
    client_secret_url = append_qs(
        iri_to_uri(MEMBER_API_FORM_BASE_URL),
        new_existing=('Existing_Update'
                      if current_user.organisation.confirmed else 'New_Credentials'),
        note=NOTE_ORCID + " " + current_user.organisation.name,
        contact_email=current_user.email,
        contact_name=current_user.name,
        org_name=current_user.organisation.name,
        cred_type=CRED_TYPE_PREMIUM,
        app_name=APP_NAME + " for " + current_user.organisation.name,
        app_description=APP_DESCRIPTION + current_user.organisation.name + "and its researchers",
        app_url=APP_URL,
        redirect_uri_1=url_for("orcid_callback", _external=True))

    current_user.organisation.api_credentials_requested_at = datetime.now()
    current_user.organisation.save()

    return redirect(client_secret_url)


@app.route("/confirm/organisation", methods=["GET", "POST"])
@roles_required(Role.ADMIN, Role.TECHNICAL)
def onboard_org():
    """Confirm and finalize registration.

    TODO: expand the spect as soon as the reqirements get sorted out.
    """
    user = User.get(id=current_user.id)
    email = user.email
    organisation = user.organisation

    if not current_user.is_tech_contact_of():
        flash(f"You are not the technical contact of {organisation}", "danger")
        return redirect(url_for('viewmembers.index_view'))

    form = OrgConfirmationForm(obj=organisation)
    form.email.data = email

    if not organisation.confirmed:
        try:
            OrgInvitation.get(email=email, org=organisation)
        except OrgInvitation.DoesNotExist:
            flash(
                "This invitation to onboard the organisation wasn't sent to your email address...",
                "danger")
            return redirect(url_for("login"))

        if request.method == "GET":
            flash("""If you currently don't know Client id and Client Secret,
            Please request these from ORCID by clicking on link 'Take me to ORCID to obtain Client iD and Client Secret'
            and come back to this form once you have them.""", "info")

            try:
                oi = OrgInfo.get((OrgInfo.email == email)
                                 | (OrgInfo.tuakiri_name == user.organisation.name)
                                 | (OrgInfo.name == user.organisation.name))
                form.city.data = organisation.city = oi.city
                form.disambiguated_id.data = organisation.disambiguated_id = oi.disambiguated_id
                form.disambiguation_source.data = organisation.disambiguation_source = oi.disambiguation_source
                organisation.save()
            except OrgInfo.DoesNotExist:
                pass
            except Organisation.DoesNotExist:
                app.logger.exception("Failed to save organisation data")

    else:
        form.name.render_kw = {'readonly': True}
        form.email.render_kw = {'readonly': True}

    if form.validate_on_submit():

        headers = {'Accept': 'application/json'}
        data = [
            ('client_id', form.orcid_client_id.data),
            ('client_secret', form.orcid_secret.data),
            ('scope', '/read-public'),
            ('grant_type', 'client_credentials'),
        ]

        response = requests.post(TOKEN_URL, headers=headers, data=data)
        if response.status_code == 401:
            flash("Something is wrong! The Client id and Client Secret are not valid!\n"
                  "Please recheck and contact Hub support if this error continues", "danger")
        else:

            if not organisation.confirmed:
                organisation.confirmed = True
                with app.app_context():
                    # TODO: shouldn't it be also 'nicified' (turned into HTML)
                    msg = Message("Welcome to the NZ ORCID Hub - Success", recipients=[email])
                    msg.body = ("Congratulations! Your identity has been confirmed and "
                                "your organisation onboarded successfully.\n"
                                "Any researcher from your organisation can now use the Hub")
                    mail.send(msg)
                    app.logger.info("For %r Onboarding is Completed!", user)
                    flash("Your Onboarding is Completed!", "success")
            else:
                flash("Organisation information updated successfully!", "success")

            form.populate_obj(organisation)
            organisation.api_credentials_entered_at = datetime.now()
            try:
                organisation.save()
            except Exception as ex:
                app.logger.exception("Failed to save organisation data")
                flash(f"Failed to save organisation data: {ex}")

            try:
                # Get the most recent invitation:
                oi = (OrgInvitation.select().where(OrgInvitation.email == email,
                                                   OrgInvitation.org == organisation).order_by(
                                                       OrgInvitation.id.desc()).first())
                if oi:
                    if not oi.confirmed_at:
                        oi.confirmed_at = datetime.now()
                        oi.save()
                    # Delete the "stale" invitations:
                    OrgInvitation.delete().where(OrgInvitation.id != oi.id,
                                                 OrgInvitation.org == organisation).execute()
            except OrgInvitation.DoesNotExist:
                pass

            return redirect(url_for("link"))

    return render_template('orgconfirmation.html', form=form, organisation=organisation)


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
        app.logger.exception("Failed to log out.")

    session.clear()
    session["__invalidate__"] = True

    if org_name:
        if EXTERNAL_SP:
            sp_url = urlparse(EXTERNAL_SP)
            sso_url_base = sp_url.scheme + "://" + sp_url.netloc
        else:
            sso_url_base = ''
        return redirect(sso_url_base + "/Shibboleth.sso/Logout?return=" + quote(
            url_for(
                "uoa_slo" if org_name and org_name == "University of Auckland" else "login",
                _external=True)))
    return redirect(url_for("login", logout=True))


@app.route("/uoa-slo")
def uoa_slo():
    """Show the logout info for UoA users."""
    flash("""You had logged in from 'The University of Auckland'.
You have to close all open browser tabs and windows in order
in order to complete the log-out.""", "warning")
    return render_template("uoa-slo.html")


@app.errorhandler(500)
def internal_error(error):
    """Handle internal error."""
    trace = traceback.format_exc()
    return render_template(
        "http500.html",
        trace=trace,
        error_message=str(error),
        event_id=g.sentry_event_id,
        public_dsn=sentry.client.get_public_dsn("https"))


@app.route("/orcid/login/")
@app.route("/orcid/login/<invitation_token>")
def orcid_login(invitation_token=None):
    """Authenticate a user vi ORCID.

    If an invitain token is presented, perform affiliation of the user or on-boarding
    of the onboarding of the organisation, if the user is the technical conatact of
    the organisation. For technical contacts the email should be made available for
    READ LIMITED scope.
    """
    _next = get_next_url()
    redirect_uri = url_for("orcid_callback", _next=_next, _external=True)

    try:
        orcid_scope = SCOPE_AUTHENTICATE[:]

        client_id = ORCID_CLIENT_ID
        if invitation_token:
            data = confirm_token(invitation_token)
            if isinstance(data, str):
                email, org_name = data.split(';')
            else:
                email, org_name = data.get("email"), data.get("org")
            user = User.get(email=email)
            if not org_name:
                org_name = user.organisation.name
            try:
                org = Organisation.get(name=org_name)
                user_org = UserOrg.get(user=user, org=org)

                if org.orcid_client_id and not user_org.is_admin:
                    client_id = org.orcid_client_id
                    orcid_scope = SCOPE_ACTIVITIES_UPDATE + SCOPE_READ_LIMITED
                else:
                    orcid_scope += SCOPE_READ_LIMITED

                redirect_uri = append_qs(redirect_uri, invitation_token=invitation_token)
            except Organisation.DoesNotExist:
                flash("Organisation '{org_name}' doesn't exist in the Hub!", "danger")
                app.logger.error(
                    f"User '{user}' attempted to affiliate with non-existing organisation {org_name}"
                )
                return redirect(url_for("login"))

        if EXTERNAL_SP:
            sp_url = urlparse(EXTERNAL_SP)
            u = Url.shorten(redirect_uri)
            redirect_uri = url_for("short_url", short_id=u.short_id, _external=True)
            redirect_uri = sp_url.scheme + "://" + sp_url.netloc + "/auth/" + quote(redirect_uri)
        # if the invitation token is missing perform only authentication (in the call back handler)
        redirect_uri = append_qs(redirect_uri, login="1")

        client_write = OAuth2Session(client_id, scope=orcid_scope, redirect_uri=redirect_uri)

        authorization_url, state = client_write.authorization_url(AUTHORIZATION_BASE_URL)
        # if the inviation token is preset use it as OAuth state
        session['oauth_state'] = state

        orcid_authenticate_url = iri_to_uri(authorization_url)
        if invitation_token:
            orcid_authenticate_url = append_qs(orcid_authenticate_url, email=email)
            # For funding record, we dont have first name and Last Name
            if user.last_name and user.first_name:
                orcid_authenticate_url = append_qs(
                    orcid_authenticate_url,
                    family_names=user.last_name,
                    given_names=user.first_name)

        oac = OrcidAuthorizeCall.create(
            user_id=None, method="GET", url=orcid_authenticate_url, state=state)
        oac.save()

        return redirect(orcid_authenticate_url)

    except Exception as ex:
        flash("Something went wrong. Please contact orcid@royalsociety.org.nz for support!",
              "danger")
        app.logger.exception("Failed to login via ORCID.")
        return redirect(url_for("login"))


def orcid_login_callback(request):
    """Handle call-back for user authenitcation via ORCID."""
    _next = get_next_url()

    state = request.args.get("state")
    invitation_token = request.args.get("invitation_token")

    if not state or state != session.get("oauth_state"):
        flash("Something went wrong, Please retry giving permissions or if issue persist then, "
              "Please contact orcid@royalsociety.org.nz for support", "danger")
        return redirect(url_for("login"))

    error = request.args.get("error")
    if error == "access_denied":
        flash(
            "You have just denied access to the Hub knowing your ORCID iD; to log in please try again and authorise",
            "warning")
        return redirect(url_for("login"))

    try:
        orcid_client_id = ORCID_CLIENT_ID
        orcid_client_secret = ORCID_CLIENT_SECRET
        email = org_name = None

        if invitation_token:
            data = confirm_token(invitation_token)
            if isinstance(data, str):
                email, org_name = data.split(';')
            else:
                email, org_name = data.get("email"), data.get("org")
            user = User.get(email=email)

            if not org_name:
                org_name = user.organisation.name
            try:
                org = Organisation.get(name=org_name)
                user_org = UserOrg.get(user=user, org=org)
            except Organisation.DoesNotExist:
                flash("Organisation '{org_name}' doesn't exist in the Hub!", "danger")
                app.logger.error(
                    f"User '{user}' attempted to affiliate with an organisation that's not known: {org_name}"
                )
                return redirect(url_for("login"))
            if org.orcid_client_id and org.orcid_secret and not user_org.is_admin:
                orcid_client_id = org.orcid_client_id
                orcid_client_secret = org.orcid_secret

        client = OAuth2Session(orcid_client_id)
        oac, orcid_authorize_call_found = OrcidAuthorizeCall.get_or_create(state=state)
        request_time = time()

        token = client.fetch_token(
            TOKEN_URL, client_secret=orcid_client_secret, authorization_response=request.url)
        response_time = time()
        oac.token = token
        oac.response_time_ms = round((response_time - request_time) * 1000)
        oac.save()

        orcid_id = token['orcid']
        if not orcid_id:
            app.logger.error(f"Missing ORCID iD: {token}")
            abort(401, "Missing ORCID iD.")
        try:
            user = User.get(orcid=orcid_id)

        except User.DoesNotExist:
            if email is None:
                flash(
                    f"The account with ORCID iD {orcid_id} is not known in the Hub. "
                    f"Try again when you've linked your ORCID iD with an organistion through either "
                    f"a Tuakiri-mediated log in, or from an organisation's email invitation",
                    "warning")
                return redirect(url_for("login"))
            user = User.get(email=email)

        if not user.orcid:
            user.orcid = orcid_id
        if not user.name and token['name']:
            user.name = token['name']
        if not user.confirmed:
            user.confirmed = True
        login_user(user)
        oac.user_id = current_user.id
        oac.save()

        # User is a technical conatct. We should verify email address
        try:
            org = Organisation.get(name=org_name) if org_name else user.organisation
            user_org = UserOrg.get(user=user, org=org)
        except Organisation.DoesNotExist:
            flash("Organisation '{org_name}' doesn't exist in the Hub!", "danger")
            app.logger.error(
                f"User '{user}' attempted to affiliate with an organisation that's not known: {org_name}"
            )
            return redirect(url_for("login"))

        session['Should_not_logout_from_ORCID'] = True
        if user_org.is_admin and invitation_token:
            access_token = token.get("access_token")
            if not access_token:
                app.logger.error(f"Missing access token: {token}")
                abort(401, "Missing ORCID API access token.")

            orcid_client.configuration.access_token = access_token
            api_instance = orcid_client.MemberAPIV20Api()
            try:
                # NB! need to add _preload_content=False to get raw response
                api_response = api_instance.view_emails(user.orcid, _preload_content=False)
            except ApiException as ex:
                message = json.loads(ex.body.replace("''", "\"")).get('user-messsage')
                if ex.status == 401:
                    flash("User has revoked the permissions to update his/her records", "warning")
                else:
                    flash(
                        "Exception when calling MemberAPIV20Api->view_employments: %s\n" % message,
                        "danger")
                    flash(f"The Hub cannot verify your email address from your ORCID record. "
                          f"Please, change the access level for your organisation email address "
                          f"'{email}' to 'trusted parties'.", "danger")
                    return redirect(url_for("login"))
            data = json.loads(api_response.data)
            if data and data.get("email") and any(
                    e.get("email") == email for e in data.get("email")):
                user.save()
                if not org.confirmed and user.is_tech_contact_of(org):
                    return redirect(_next or url_for("onboard_org"))
                elif not org.confirmed and not user.is_tech_contact_of(org):
                    flash(
                        f"Your '{org}' has not be onboarded. Please, try again once your technical contact"
                        f" onboards your organisation on ORCIDHUB", "warning")
                    return redirect(url_for("about"))
                elif org.confirmed:
                    return redirect(url_for('viewmembers.index_view'))
            else:
                logout_user()
                flash(f"The Hub cannot verify your email address from your ORCID record. "
                      f"Please, change the access level for your "
                      f"organisation email address '{email}' to 'trusted parties'.", "danger")
                return redirect(url_for("login"))

        elif not user_org.is_admin and invitation_token:
            scope = ",".join(token.get("scope", []))
            if not scope:
                flash("Scope missing, contact orcidhub support", "danger")
                app.logger.error("For %r encountered exception: Scope missing", user)
                return redirect(url_for("login"))

            orcid_token, orcid_token_found = OrcidToken.get_or_create(
                user_id=user.id, org=user.organisation, scope=scope)
            orcid_token.access_token = token["access_token"]
            orcid_token.refresh_token = token["refresh_token"]
            with db.atomic():
                try:
                    user.save()
                    orcid_token.save()
                except Exception as ex:
                    db.rollback()
                    flash(f"Failed to save data: {ex}")
                    app.logger.exception("Failed to save token.")

            try:
                ui = UserInvitation.get(token=invitation_token)
                if ui.affiliations & (Affiliation.EMP | Affiliation.EDU):
                    api = orcid_client.MemberAPI(org, user)
                    params = {k: v for k, v in ui._data.items() if v != ""}
                    for a in Affiliation:
                        if a & ui.affiliations:
                            params["affiliation"] = a
                            params["initial"] = True
                            api.create_or_update_affiliation(**params)
                ui.confirmed_at = datetime.now()
                ui.save()

            except UserInvitation.DoesNotExist:
                pass
            except Exception as ex:
                flash(f"Something went wrong: {ex}", "danger")
                app.logger.exception("Failed to create affiliation record")

        if _next:
            return redirect(_next)
        else:
            try:
                OrcidToken.get(user=user, org=org)
            except OrcidToken.DoesNotExist:
                if user.is_tech_contact_of(org) and not org.confirmed:
                    return redirect(url_for("onboard_org"))
                elif not user.is_tech_contact_of(org) and user_org.is_admin and not org.confirmed:
                    flash(
                        f"Your '{org}' has not be onboarded."
                        f"Please, try again once your technical contact onboard's your organisation on ORCIDHUB",
                        "warning")
                    return redirect(url_for("about"))
                elif org.confirmed and user_org.is_admin:
                    return redirect(url_for('viewmembers.index_view'))
                else:
                    return redirect(url_for("link"))
        return redirect(url_for("profile"))

    except User.DoesNotExist:
        flash("You are not known in the Hub...", "danger")
        return redirect(url_for("login"))
    except UserOrg.DoesNotExist:
        flash("You are not known in the Hub...", "danger")
        return redirect(url_for("login"))
    except rfc6749.errors.MissingCodeError:
        flash("%s cannot be invoked directly..." % request.url, "danger")
        return redirect(url_for("login"))
    except rfc6749.errors.MissingTokenError:
        flash("Missing token.", "danger")
        return redirect(url_for("login"))
    except Exception as ex:
        flash(f"Something went wrong contact orcid@royalsociety.org.nz support for issue: {ex}",
              "danger")
        app.logger.exception("Unhandled excetion occrured while handling ORCID call-back.")
        return redirect(url_for("login"))


@app.route("/select/user_org/<int:user_org_id>")
@login_required
def select_user_org(user_org_id):
    """Change the current organisation of the current user."""
    user_org_id = int(user_org_id)
    _next = get_next_url() or request.referrer or url_for("login")
    try:
        uo = UserOrg.get(id=user_org_id)
        if (uo.user.orcid == current_user.orcid or uo.user.email == current_user.email
                or uo.user.eppn == current_user.eppn):
            current_user.organisation_id = uo.org_id
            current_user.save()
        else:
            flash("You cannot switch your user to this organisation", "danger")
    except UserOrg.DoesNotExist:
        flash("Your are not related to this organisation.", "danger")
    return redirect(_next)
