# -*- coding: utf-8 -*-
"""Authentication views.

Collection of applicion views involved in organisation on-boarding and
user (reseaser) affiliations.
"""

import base64
import pickle
import re
import secrets
import zlib
from datetime import datetime
from os import path, remove
from tempfile import gettempdir
from urllib.parse import quote, unquote, urlencode, urlparse

import requests
from flask import (Response, abort, flash, redirect, render_template, request, session, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message
from oauthlib.oauth2 import rfc6749
from requests_oauthlib import OAuth2Session
from swagger_client.rest import ApiException
from werkzeug.urls import iri_to_uri

import orcid_client
from application import app, db, mail
from config import (APP_DESCRIPTION, APP_NAME, APP_URL, AUTHORIZATION_BASE_URL, CRED_TYPE_PREMIUM,
                    EXTERNAL_SP, MEMBER_API_FORM_BASE_URL, NEW_CREDENTIALS, NOTE_ORCID,
                    NZ_ORCIDHUB_CLIENT_ID, NZ_ORCIDHUB_CLIENT_SECRET, ORCID_API_BASE,
                    ORCID_BASE_URL, SCOPE_ACTIVITIES_UPDATE, SCOPE_AUTHENTICATE,
                    SCOPE_READ_LIMITED, TOKEN_URL)
from forms import OnboardingTokenForm, OrgConfirmationForm, SelectOrganisation
from login_provider import roles_required
from models import (Affiliation, OrcidToken, Organisation, OrgInfo, OrgInvitation, Role, User,
                    UserOrg)
from utils import append_qs, confirm_token

HEADERS = {'Accept': 'application/vnd.orcid+json', 'Content-type': 'application/vnd.orcid+json'}


def get_next_url():
    """Retrieves and sanitizes next/return URL."""
    _next = request.args.get('next')
    if _next and not ("orcidhub.org.nz" in _next or _next.startswith("/")):
        return None
    return _next


@app.route("/index")
@app.route("/login")
@app.route("/")
def login():
    """Main landing page."""
    _next = get_next_url()
    if EXTERNAL_SP:
        session["auth_secret"] = secret_token = secrets.token_urlsafe()
        _next = url_for("handle_login", _next=_next, _external=True)
        login_url = append_qs(EXTERNAL_SP, _next=_next, key=secret_token)
    else:
        login_url = url_for("handle_login", _next=_next)

    org_onboarded_info = {
        r.name: r.tuakiri_name
        for r in Organisation.select(Organisation.name, Organisation.tuakiri_name).where(
            Organisation.confirmed.__eq__(True))
    }

    return render_template(
        "index.html", login_url=login_url, org_onboarded_info=org_onboarded_info)


@app.route("/Tuakiri/SP")
def shib_sp():
    """Remote Shibboleth authenitication handler.

    All it does passes all response headers to the original calller."""
    _next = request.args.get('_next')
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
    _next = request.args.get('_next')

    # TODO: make it secret
    if EXTERNAL_SP:
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
            f"User with email address {email} (eppn: {eppn} is trying " +
            f"to login having affiliation as {unscoped_affiliation} with {shib_org_name}")

        if secondary_emails:
            app.logger.info(
                f"the user has logged in with secondary email addresses: {secondary_emails}")

    except Exception as ex:
        app.logger.error("Encountered exception: %r", ex)
        abort(500, ex)

    try:
        org = Organisation.get((Organisation.tuakiri_name == shib_org_name) | (
            Organisation.name == shib_org_name))
    except Organisation.DoesNotExist:
        org = Organisation(tuakiri_name=shib_org_name)
        # try to get the official organisation name:
        try:
            org_info = OrgInfo.get((OrgInfo.tuakiri_name == shib_org_name) | (
                OrgInfo.name == shib_org_name))
        except OrgInfo.DoesNotExist:
            org.name = shib_org_name
        else:
            org.name = org_info.name
        try:
            org.save()
        except Exception as ex:
            flash("Failed to save organisation data: %s" % str(ex))
            app.logger.error("Exception Occured: %r", str(ex))

    q = User.select().where(User.email == email)
    if eppn:
        q = q.orwhere(User.eppn == eppn)
    if secondary_emails:
        q = q.orwhere(User.email.in_(secondary_emails))
    user = q.first()
    if not user:
        user = User.create(
            email=email,
            eppn=eppn,
            name=name,
            first_name=first_name,
            last_name=last_name,
            roles=Role.RESEARCHER)
    else:
        # Add Shibboleth meta data if they are missing
        if not user.name or org is not None and user.name == org.name and name:
            user.name = name
        if not user.first_name and first_name:
            user.first_name = first_name
        if not user.last_name and last_name:
            user.last_name = last_name
        if not user.eppn and eppn:
            user.eppn = eppn

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
        flash("Failed to save user data: %s" % str(ex))

    login_user(user)
    app.logger.info("User %r from %r logged in.", user, org)

    if _next:
        return redirect(_next)
    elif user.is_superuser:
        return redirect(url_for("invite_organisation"))
    elif org and org.confirmed:
        app.logger.info("User %r organisation is onboarded", user)
        return redirect(url_for("link"))
    elif org and org.is_email_confirmed and (not org.confirmed) and user.is_tech_contact_of(org):
        app.logger.info("User %r is org admin and organisation is not onboarded", user)
        return redirect(url_for("update_org_info"))
    else:
        flash("Your organisation (%s) is not onboarded" % shib_org_name, "danger")
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
        flash("Your organisation (%s) is not onboarded" % current_user.organisation.tuakiri_name,
              "danger")
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
                return render_template(
                    "linking.html",
                    orcid_url_write=orcid_url_write,
                    orcid_url_read_limited=orcid_url_read,
                    orcid_url_authenticate=orcid_url_authenticate,
                    error=error)
        return render_template(
            "linking.html", orcid_url_write=orcid_url_write, orcid_base_url=ORCID_BASE_URL)
    except Exception as ex:
        flash("Unhandled Exception occured: %s" % str(ex))
        app.logger.error("Exception Occured: %r", str(ex))
    return redirect(url_for("profile"))


@app.route("/orcid/auth/<path:url>", methods=["GET"])
@app.route("/auth/<path:url>", methods=["GET"])
def orcid_callback_proxy(url):
    url = unquote(url)
    return redirect(url + '?' + urlencode(request.args))


def is_emp_or_edu_record_present(access_token, affiliation_type, user):
    orcid_client.configuration.access_token = access_token
    # create an instance of the API class
    api_instance = orcid_client.MemberAPIV20Api()
    try:
        api_response = None
        affiliation_type_key = ""
        # Fetch all entries
        if affiliation_type == Affiliation.EMP:
            api_response = api_instance.view_employments(user.orcid)
            affiliation_type_key = "employment_summary"

        elif affiliation_type == Affiliation.EDU:
            api_response = api_instance.view_educations(user.orcid)
            affiliation_type_key = "education_summary"

        if api_response:
            data = api_response.to_dict()
            for r in data.get(affiliation_type_key, []):
                if r["organization"]["name"] == user.organisation.name and user.organisation.name in \
                        r["source"]["source_name"]["value"]:
                    app.logger.info("For %r there is %r present on ORCID profile", user,
                                    affiliation_type_key)
                    return True

    except ApiException as apiex:
        app.logger.error(
            "For %r while checking for employment and education records, Encountered Exception: %r",
            user, apiex)
        return False
    except Exception as e:
        app.logger.error("Failed to retrive employment and education entries: %r.", str(e))
        return False
    return False


# Step 2: User authorization, this happens on the provider.
@app.route("/auth", methods=["GET"])
@login_required
def orcid_callback():
    """Retrieve an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """
    if "error" in request.args:
        error = request.args["error"]
        error_description = request.args.get("error_description")
        if error == "access_denied":
            flash("You have denied the Hub access to your ORCID record."
                  " At a minimum, the Hub needs to know your ORCID iD to be useful.", "danger")
        else:
            flash("Error occured while attempting to authorize '%s': %s" %
                  (current_user.organisation.name, error_description), "danger")
        return redirect(url_for("link") + '?' + 'error=' + error)

    client = OAuth2Session(current_user.organisation.orcid_client_id)

    try:
        state = request.args['state']
        if state != session.get('oauth_state'):
            flash(
                "Retry giving permissions or if issue persist then, Please contact ORCIDHUB for support",
                "danger")
            app.logger.error(
                "For %r session state was %r, whereas state returned from ORCID is %r",
                current_user, session.get('oauth_state', 'empty'), state)
            return redirect(url_for("login"))

        token = client.fetch_token(
            TOKEN_URL,
            client_secret=current_user.organisation.orcid_secret,
            authorization_response=request.url)
    except rfc6749.errors.MissingCodeError:
        flash("%s cannot be invoked directly..." % request.url, "danger")
        return redirect(url_for("login"))
    except rfc6749.errors.MissingTokenError:
        flash("Missing token.", "danger")
        return redirect(url_for("login"))
    except Exception as ex:
        flash("Something went wrong contact orcidhub support for issue: %s" % str(ex))
        app.logger.error("For %r encountered exception: %r", current_user, ex)
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
            flash("Failed to save data: %s" % str(ex))
            app.logger.error("Exception Occured: %r", str(ex))

    app.logger.info("User %r authorized %r to have %r access to the profile "
                    "and now trying to update employment or education record", user,
                    user.organisation, scope)
    if scope == SCOPE_READ_LIMITED[0] + "," + SCOPE_ACTIVITIES_UPDATE[0] and orcid_token_found:
        orcid_client.configuration.access_token = orcid_token.access_token
        api_instance = orcid_client.MemberAPIV20Api()

        url = urlparse(ORCID_BASE_URL)
        source_clientid = orcid_client.SourceClientId(
            host=url.hostname,
            path=user.organisation.orcid_client_id,
            uri="http://" + url.hostname + "/client/" + user.organisation.orcid_client_id)

        organisation_address = orcid_client.OrganizationAddress(
            city=user.organisation.city, country=user.organisation.country)

        disambiguated_organization_details = orcid_client.DisambiguatedOrganization(
            disambiguated_organization_identifier=user.organisation.disambiguated_id,
            disambiguation_source=user.organisation.disambiguation_source)

        # TODO: need to check if the entry doesn't exist already:
        for a in Affiliation:

            if not a & user.affiliations:
                continue

            if a == Affiliation.EMP:
                rec = orcid_client.Employment()
            elif a == Affiliation.EDU:
                rec = orcid_client.Education()
            else:
                continue

            rec.source = orcid_client.Source(
                source_orcid=None,
                source_client_id=source_clientid,
                source_name=user.organisation.name)

            rec.organization = orcid_client.Organization(
                name=user.organisation.name,
                address=organisation_address,
                disambiguated_organization=disambiguated_organization_details)

            if (not is_emp_or_edu_record_present(orcid_token.access_token, a, user)):
                try:
                    if a == Affiliation.EMP:

                        api_instance.create_employment(user.orcid, body=rec)
                        flash(
                            "Your ORCID employment record was updated with an affiliation entry from '%s'"
                            % user.organisation, "success")
                        app.logger.info("For %r the ORCID employment record was updated from %r",
                                        user, user.organisation)
                    elif a == Affiliation.EDU:
                        api_instance.create_education(user.orcid, body=rec)
                        flash(
                            "Your ORCID education record was updated with an affiliation entry from '%s'"
                            % user.organisation, "success")
                        app.logger.info("For %r the ORCID education record was updated from %r",
                                        user, user.organisation)
                    else:
                        continue
                    # TODO: Save the put-code in db table

                except ApiException as e:
                    flash("Failed to update the entry: %s." % e.body, "danger")
                except Exception as ex:
                    app.logger.error("For %r encountered exception: %r", user, ex)

        if not user.affiliations:
            flash(
                "The ORCID Hub was not able to automatically write an affiliation with "
                f"{user.organisation}, as the nature of the affiliation with your "
                "organisation does not appear to include either Employment or Education.\n"
                "Please contact your Organisation Administrator(s) if you believe this is an error "
                "and try again.", "warning")

    session['Should_not_logout_from_ORCID'] = True
    return redirect(url_for("profile"))


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """Fetch a protected resource using an OAuth 2 token."""
    user = current_user
    app.logger.info("For %r trying to display profile by getting ORCID token", user)
    try:
        orcid_token = OrcidToken.get(user_id=user.id, org=user.organisation)
    except OrcidToken.DoesNotExist:
        app.logger.info("For %r we dont have ocrditoken so redirecting back to link page", user)
        return redirect(url_for("link"))

    except Exception as ex:
        # TODO: need to handle this
        flash("Unhandled Exception occured: %s" % ex, "danger")
        return redirect(url_for("login"))
    else:
        client = OAuth2Session(
            user.organisation.orcid_client_id, token={"access_token": orcid_token.access_token})
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


@app.route("/invite/user", methods=["GET"])
@roles_required(Role.SUPERUSER, Role.ADMIN)
def invite_user():
    """Invite a researcher to join the hub."""
    # For now on boarding of researcher is not supported
    return "Work in Progress!"


@app.route("/confirm/organisation", methods=["GET", "POST"])
@app.route("/confirm/organisation/<token>", methods=["GET", "POST"])
@login_required
def confirm_organisation(token=None):
    """Registration confirmations.

    TODO: expand the spect as soon as the reqirements get sorted out.
    """
    if token is None:
        form = OnboardingTokenForm()
        if form.validate_on_submit():
            return redirect(url_for("confirm_organisation", token=form.token.data))

        return render_template("missing_onboarding_token.html", form=form)

    client_secret_url = None
    email = confirm_token(token)
    user = current_user

    if not email:
        app.error("token '%s'", token)
        app.login_manager.unauthorized()
    if user.email != email:
        app.logger.info("The invitation was send to %r and not to the email address: %r", email,
                        user.email)
        flash("This invitation to onboard the organisation wasn't sent to your email address...",
              "danger")
        return redirect(url_for("login"))

    # TODO: refactor this: user == current_user here no need to requery DB
    user = User.get(email=current_user.email, organisation=current_user.organisation)
    if not user.is_tech_contact_of():
        try:
            user.save()
            app.logger.info("Onboarding is complete for user: %r", user)
        except Exception as ex:
            app.logger.error("Exception occured: %r", str(ex))
            flash("Failed to save user data: %s" % str(ex))
        with app.app_context():
            msg = Message("Welcome to the NZ ORCID Hub", recipients=[email])
            msg.body = "Congratulations you are confirmed as an Organisation Admin for " + str(
                user.organisation)
            mail.send(msg)
            flash(
                "Your registration is completed; however, if they've not yet done so it is the responsibility of your "
                "Technical Contact to complete onboarding by entering your organisation's ORCID API credentials.",
                "success")
        return redirect(url_for("viewmembers"))

    # TODO: support for mutliple orgs and admins
    # TODO: admin role asigning to an exiting user
    # TODO: support for org not participating in Tuakiri
    form = OrgConfirmationForm()

    # For now only GET method is implemented will need post method for organisation
    # to enter client secret and client key for orcid

    try:
        organisation = Organisation.get(name=current_user.organisation.name)
    except Organisation.DoesNotExist:
        flash('We are very sorry, your organisation invitation has been cancelled, '
              'please contact ORCID HUB Admin!', "danger")
        return redirect(url_for("login"))

    if request.method == 'POST':
        if not form.validate():
            flash('Please fill in all fields and try again!', "danger")
        else:

            if (not (user is None) and (not (organisation is None))):
                # Update Organisation
                organisation.country = form.country.data
                organisation.city = form.city.data
                organisation.disambiguated_id = form.disambiguated_id.data
                organisation.disambiguation_source = form.disambiguation_source.data
                organisation.is_email_confirmed = True

                headers = {'Accept': 'application/json'}
                data = [
                    ('client_id', form.orgOricdClientId.data),
                    ('client_secret', form.orgOrcidClientSecret.data),
                    ('scope', '/read-public'),
                    ('grant_type', 'client_credentials'),
                ]

                response = requests.post(TOKEN_URL, headers=headers, data=data)

                if response.status_code == 401:
                    flash("Something is wrong! The Client id and Client Secret are not valid!\n"
                          "Please recheck and contact Hub support if this error continues",
                          "danger")
                else:
                    organisation.confirmed = True
                    organisation.orcid_client_id = form.orgOricdClientId.data.strip()
                    organisation.orcid_secret = form.orgOrcidClientSecret.data.strip()

                    with app.app_context():
                        # TODO: shouldn't it be also 'nicified'?
                        msg = Message("Welcome to the NZ ORCID Hub - Success", recipients=[email])
                        msg.body = "Congratulations! Your identity has been confirmed and " \
                                   "your organisation onboarded successfully.\n" \
                                   "Any researcher from your organisation can now use the Hub"
                        mail.send(msg)
                        app.logger.info("For %r Onboarding is Completed!", current_user)
                        flash("Your Onboarding is Completed!", "success")

                    try:
                        organisation.save()
                    except Exception as ex:
                        app.logger.error("Exception Occured: %r", str(ex))
                        flash("Failed to save organisation data: %s" % str(ex))

                    try:
                        oi = OrgInvitation.get(token=token)
                        oi.confirmed_at = datetime.now()
                        oi.save()
                    except OrgInvitation.DoesNotExist:
                        pass
                    # Delete the "stale" invitations:
                    OrgInvitation.delete().where(OrgInvitation.org == organisation,
                                                 OrgInvitation.token != token).execute()

                    return redirect(url_for("link"))

    elif request.method == 'GET':
        if organisation is not None and not organisation.is_email_confirmed:
            organisation.is_email_confirmed = True
            try:
                organisation.save()
            except Exception as ex:
                flash("Failed to save organisation data: %s" % str(ex))
                app.logger.error("Exception Occured: %r", str(ex))
        elif organisation is not None and organisation.is_email_confirmed:
            flash(
                "We have noted that you came on orcidhub through the email link, which is now unneccessary. "
                "You should be able to login on orcidhub directly by visiting our orcidhub's website",
                "warning")

        form.orgEmailid.data = email
        form.orgName.data = user.organisation.name

        flash("""If you currently don't know Client id and Client Secret,
        Please request these from ORCID by clicking on link 'Take me to ORCID to obtain Client iD and Client Secret'
        and come back to this form once you have them.""", "warning")

        try:
            orgInfo = OrgInfo.get((OrgInfo.email == email) | (
                OrgInfo.tuakiri_name == user.organisation.name) | (
                    OrgInfo.name == user.organisation.name))
            form.city.data = organisation.city = orgInfo.city
            form.disambiguated_id.data = organisation.disambiguated_id = orgInfo.disambiguated_id
            form.disambiguation_source.data = organisation.disambiguation_source = orgInfo.disambiguation_source

        except OrgInfo.DoesNotExist:
            pass
        organisation.country = form.country.data

    try:
        organisation.save()
    except Exception as ex:
        flash("Failed to save organisation data: %s" % str(ex))
        app.logger.error("Exception Occured: %r", str(ex))
    redirect_uri = url_for("orcid_callback", _external=True)
    client_secret_url = append_qs(
        iri_to_uri(MEMBER_API_FORM_BASE_URL),
        new_existing=NEW_CREDENTIALS,
        note=NOTE_ORCID + " " + user.organisation.name,
        contact_email=email,
        contact_name=user.name,
        org_name=user.organisation.name,
        cred_type=CRED_TYPE_PREMIUM,
        app_name=APP_NAME + " for " + user.organisation.name,
        app_description=APP_DESCRIPTION + user.organisation.name + "and its researchers",
        app_url=APP_URL,
        redirect_uri_1=redirect_uri)
    return render_template('orgconfirmation.html', client_secret_url=client_secret_url, form=form)


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
    return redirect(sso_url_base + "/Shibboleth.sso/Logout?return=" + quote(
        url_for(
            "uoa_slo" if org_name and org_name == "University of Auckland" else "login",
            _external=True)))


@app.route("/uoa-slo")
def uoa_slo():
    """Show the logout info for UoA users."""
    flash("""You had logged in from 'The University of Auckland'.
You have to close all open browser tabs and windows in order
in order to complete the log-out.""", "warning")
    return render_template("uoa-slo.html")


@app.route("/viewmembers")
@roles_required(Role.ADMIN)
def viewmembers():
    """View the list of users (researchers)."""
    try:
        users = current_user.organisation.users
    except:
        flash("There are no users registered in your organisation.", "danger")
        return redirect(url_for("login"))

    return render_template(
        "viewMembers.html", orgnisationname=current_user.organisation.name, users=users)


@app.route("/updateorginfo", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def update_org_info():
    email = current_user.email
    user = User.get(email=current_user.email, organisation=current_user.organisation)
    form = OrgConfirmationForm()
    redirect_uri = url_for("orcid_callback", _external=True)
    client_secret_url = append_qs(
        iri_to_uri(MEMBER_API_FORM_BASE_URL),
        new_existing=NEW_CREDENTIALS,
        note=NOTE_ORCID + " " + user.organisation.name,
        contact_email=email,
        contact_name=user.name,
        org_name=user.organisation.name,
        cred_type=CRED_TYPE_PREMIUM,
        app_name=user.organisation.name,
        app_description=APP_DESCRIPTION + " at " + user.organisation.name,
        app_url=APP_URL,
        redirect_uri_1=redirect_uri)

    try:
        organisation = Organisation.get(tech_contact_id=current_user.id)
    except Organisation.DoesNotExist:
        flash("It appears that you are not the technical contact for your organisaton.", "danger")
        return redirect(url_for("login"))
    if request.method == "POST":
        if not form.validate():
            flash("Please fill in all fields and try again!", "danger")
        else:
            organisation = Organisation.get(tech_contact_id=current_user.id)
            if (not (user is None) and (not (organisation is None))):
                # Update Organisation
                organisation.country = form.country.data
                organisation.city = form.city.data
                organisation.disambiguated_id = form.disambiguated_id.data
                organisation.disambiguation_source = form.disambiguation_source.data

                headers = {"Accept": "application/json"}
                data = [
                    ("client_id", form.orgOricdClientId.data),
                    ("client_secret", form.orgOrcidClientSecret.data),
                    ("scope", "/read-public"),
                    ("grant_type", "client_credentials"),
                ]

                response = requests.post(TOKEN_URL, headers=headers, data=data)

                if response.status_code == 401:
                    flash("Something is wrong! The Client id and Client Secret are not valid!"
                          "\n Please recheck and contact Hub support if this error continues",
                          "danger")
                else:

                    organisation.orcid_client_id = form.orgOricdClientId.data
                    organisation.orcid_secret = form.orgOrcidClientSecret.data
                    if not organisation.confirmed:
                        organisation.confirmed = True
                        with app.app_context():
                            msg = Message(
                                "Welcome to the NZ ORCID Hub - Success", recipients=[email])
                            msg.body = "Congratulations! Your identity has been confirmed and " \
                                       "your organisation onboarded successfully.\n" \
                                       "Any researcher from your organisation can now use the Hub"
                            mail.send(msg)
                        flash("Your Onboarding is Completed!", "success")
                    else:
                        flash("Organisation information updated successfully!", "success")
                    try:
                        organisation.save()
                    except Exception as ex:
                        app.logger.error("Exception occured due to: %r", str(ex))
                        flash("Failed to save organisation data: %s" % str(ex))
                    return redirect(url_for("link"))

    elif request.method == 'GET':

        form.orgName.data = user.organisation.name
        form.orgEmailid.data = user.email

        form.city.data = user.organisation.city
        form.country.data = user.organisation.country
        form.disambiguated_id.data = user.organisation.disambiguated_id
        form.disambiguation_source.data = user.organisation.disambiguation_source
        form.orgOricdClientId.data = user.organisation.orcid_client_id
        form.orgOrcidClientSecret.data = user.organisation.orcid_secret

        form.orgName.render_kw = {'readonly': True}
        form.orgEmailid.render_kw = {'readonly': True}

    try:
        organisation.save()
    except Exception as ex:
        app.logger.error("Exception occured due to: %r", str(ex))
        flash("Failed to save organisation data: %s" % str(ex))
    return render_template('orgconfirmation.html', client_secret_url=client_secret_url, form=form)


@app.route("/exportmembers")
@roles_required(Role.ADMIN)
def exportmembers():
    """View the list of users (researchers)."""
    try:
        users = current_user.organisation.users
        return Response(
            generateRow(users),
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment; filename=ResearchersData.csv"})
    except:
        flash("There are no users registered in your organisation.", "warning")
    return redirect(url_for("viewmembers"))


def generateRow(users):
    yield "Email,Eppn,ORCID ID\n"
    for u in users:
        """ ORCID ID might be NULL, Hence adding a check """
        yield ','.join([u.email, str(u.eppn or ""), str(u.orcid or "")]) + '\n'


@app.errorhandler(500)
def internal_error(error):
    app.logger.exception("Exception 500 occured.")
    return render_template("http500.html", error_message=str(error))


@app.route("/orcid/login/", methods=["GET", "POST"])
@app.route("/orcid/login/<token>", methods=["GET", "POST"])
def orcid_login(token=None):

    try:
        extend_url = "?"

        if token is not None:
            email_and_organisation = confirm_token(token)
            email, org = email_and_organisation.split(';')
            extend_url = extend_url + "email=" + email + "&" + "orgName=" + org
            organisation = Organisation.get(name=org)
            session['email'] = email
            session['orgName'] = organisation.name

        redirect_uri = url_for("orcid_login_callback", _external=True)
        if EXTERNAL_SP:
            sp_url = urlparse(EXTERNAL_SP)
            redirect_uri = sp_url.scheme + "://" + sp_url.netloc + "/orcid/auth/" + quote(
                redirect_uri) + extend_url
        else:
            redirect_uri = redirect_uri + extend_url

        client_write = OAuth2Session(
            NZ_ORCIDHUB_CLIENT_ID,
            scope=SCOPE_AUTHENTICATE,
            redirect_uri=redirect_uri, )

        authorization_url_write, state = client_write.authorization_url(AUTHORIZATION_BASE_URL)
        session['oauth_state'] = state

        orcid_url_write = append_qs(iri_to_uri(authorization_url_write))

        return redirect(orcid_url_write)
    except Exception as ex:
        flash("Something went wrong contact orcidhub support for issue: %s" % str(ex))
        app.logger.error("Encountered exception: %r", ex)
        return redirect(url_for("login"))


@app.route("/orcid/auth", methods=["GET", "POST"])
def orcid_login_callback():
    try:
        state = request.args['state']

        if state != session.get('oauth_state'):
            flash(
                "Something went wrong, Please retry giving permissions or if issue persist then, "
                "Please contact ORCIDHUB for support", "danger")

        token = None
        orcid_id = session.get('orcid_id')
        if orcid_id is None:
            client = OAuth2Session(NZ_ORCIDHUB_CLIENT_ID)
            token = client.fetch_token(
                TOKEN_URL,
                client_secret=NZ_ORCIDHUB_CLIENT_SECRET,
                authorization_response=request.url)
            orcid_id = token['orcid']
            session['orcid_id'] = orcid_id

        email = None
        if session.get('email') and session.get('orgName'):
            email = request.args['email']
            orgName = request.args['orgName']
            user = User.get(email=email)
            organisation = Organisation.get(name=orgName)
            UserOrg.get(user=user, org=organisation)
            user.orcid = orcid_id
            user.confirmed = True
            if user.name is None and token['name']:
                user.name = token['name']
            user.save()

            login_user(user)
            return redirect(url_for("link"))
        else:
            form = SelectOrganisation()

            user_data = User.get(orcid=orcid_id)

            if request.method == 'GET':
                org_data = Organisation.select(
                    Organisation.id,
                    Organisation.name).where(Organisation.id << UserOrg.select(UserOrg.org).where(
                        UserOrg.user << User.select().where(User.orcid == orcid_id))).tuples()

                form.orgNames.choices = org_data

                if len(org_data) == 1:
                    login_user(user_data)
                    return redirect(url_for("link"))

                return render_template("selectOrganisation.html", form=form)
            elif request.method == 'POST':
                if form.orgNames.data:
                    organisation = Organisation.get(id=int(form.orgNames.data))
                    user_data = User.get(orcid=orcid_id, organisation=organisation)
                    login_user(user_data)
                    return redirect(url_for("link"))

                else:
                    flash("Please select organisation through which you want to login", "danger")
                    return render_template("selectOrganisation.html", form=form)

    except User.DoesNotExist:
        flash("You are not onboarded on ORCIDHUB...", "danger")
        return redirect(url_for("login"))
    except UserOrg.DoesNotExist:
        flash("You are not onboarded on ORCIDHUB...", "danger")
        return redirect(url_for("login"))
    except rfc6749.errors.MissingCodeError:
        flash("%s cannot be invoked directly..." % request.url, "danger")
        return redirect(url_for("login"))
    except rfc6749.errors.MissingTokenError:
        flash("Missing token.", "danger")
        return redirect(url_for("login"))
    except Exception as ex:
        flash("Something went wrong contact orcidhub support for issue: %s" % str(ex))
        app.logger.error("For %r encountered exception: %r", current_user, ex)
        return redirect(url_for("login"))
    return redirect(url_for("link"))
