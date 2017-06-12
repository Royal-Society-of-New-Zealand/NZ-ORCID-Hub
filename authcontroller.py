# -*- coding: utf-8 -*-
"""Authentication views.

Collection of applicion views involved in organisation on-boarding and
user (reseaser) affiliations.
"""

import base64
import pickle
import secrets
import zlib
from os import path, remove
from tempfile import gettempdir
from urllib.parse import quote, unquote, urlencode, urlparse

import requests
from flask import (abort, flash, redirect, render_template, request, session, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message
from oauthlib.oauth2 import rfc6749
from requests_oauthlib import OAuth2Session
from werkzeug.urls import iri_to_uri

import swagger_client
import utils
from application import app, db, mail
from config import (APP_DESCRIPTION, APP_NAME, APP_URL, AUTHORIZATION_BASE_URL, CRED_TYPE_PREMIUM,
                    EXTERNAL_SP, MEMBER_API_FORM_BASE_URL, NEW_CREDENTIALS, NOTE_ORCID,
                    ORCID_API_BASE, ORCID_BASE_URL, SCOPE_ACTIVITIES_UPDATE, TOKEN_URL)
from forms import OnboardingTokenForm
from login_provider import roles_required
from models import (Affiliation, OrcidToken, Organisation, OrgInfo, Role, User, UserOrg)
from registrationForm import OrgConfirmationForm, OrgRegistrationForm
from swagger_client.rest import ApiException
from tokenGeneration import confirm_token, generate_confirmation_token

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
        login_url = EXTERNAL_SP
        login_url += ('&' if urlparse(EXTERNAL_SP).query else '?')
        login_url += urlencode(dict(_next=_next, key=secret_token))
    else:
        login_url = url_for("handle_login", _next=_next)

    return render_template("index.html", login_url=login_url)


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
@app.route("/auth/jwt", methods=["POST"])
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

    token = data.get("Auedupersonsharedtoken").encode("latin-1").decode("utf-8")
    last_name = data['Sn'].encode("latin-1").decode("utf-8")
    first_name = data['Givenname'].encode("latin-1").decode("utf-8")
    email = data['Mail'].encode("latin-1").decode("utf-8").lower()
    session["shib_O"] = shib_org_name = data['O'].encode("latin-1").decode("utf-8")
    name = data.get('Displayname').encode("latin-1").decode("utf-8")
    unscoped_affiliation = set(a.strip()
                               for a in data.get("Unscoped-Affiliation", '').encode("latin-1")
                               .decode("utf-8").replace(',', ';').split(';'))

    if unscoped_affiliation:
        edu_person_affiliation = Affiliation.NONE
        if unscoped_affiliation & {"faculty", "staff"}:
            edu_person_affiliation |= Affiliation.EMP
        if unscoped_affiliation & {"student", "alum"}:
            edu_person_affiliation |= Affiliation.EDU
    else:
        flash(
            "The value of 'Unscoped-Affiliation' was not supplied from your identity provider,"
            " So we are not able to determine the nature of affiliation you have with your organisation",
            "danger")

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

    try:
        user = User.get(User.email == email)

        # Add Shibboleth meta data if they are missing
        if not user.edu_person_shared_token:
            user.edu_person_shared_token = token
        if not user.name or org is not None and user.name == org.name and name:
            user.name = name
        if not user.first_name and first_name:
            user.first_name = first_name
        if not user.last_name and last_name:
            user.last_name = last_name

    except User.DoesNotExist:
        user = User.create(
            email=email,
            name=name,
            first_name=first_name,
            last_name=last_name,
            roles=Role.RESEARCHER,
            edu_person_shared_token=token)

    # TODO: need to find out a simple way of tracking
    # the organization user is logged in from:
    if org != user.organisation:
        user.organisation = org

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

    if _next:
        return redirect(_next)
    elif user.is_superuser:
        return redirect(url_for("invite_organisation"))
    elif org and org.confirmed:
        return redirect(url_for("link"))
    elif org and org.is_email_confirmed and (not org.confirmed) and user.is_tech_contact_of(org):
        return redirect(url_for("update_org_info"))
    else:
        flash("Your organisation (%s) is not onboarded" % shib_org_name, "danger")

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

    client_write = OAuth2Session(
        current_user.organisation.orcid_client_id,
        scope=SCOPE_ACTIVITIES_UPDATE,
        redirect_uri=redirect_uri)
    authorization_url_write, state = client_write.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state

    orcid_url_write = iri_to_uri(authorization_url_write) + urlencode(
        dict(
            family_names=current_user.last_name,
            given_names=current_user.first_name,
            email=current_user.email))

    # Check if user details are already in database
    # TODO: re-affiliation after revoking access?
    # TODO: affiliation with multiple orgs should lookup UserOrg

    try:
        OrcidToken.get(
            user_id=current_user.id, org=current_user.organisation, scope=SCOPE_ACTIVITIES_UPDATE)
    except OrcidToken.DoesNotExist:
        return render_template("linking.html", orcid_url_write=orcid_url_write)
    except Exception as ex:
        flash("Unhandled Exception occured: %s" % str(ex))
    return redirect(url_for("profile"))


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
    # error=access_denied&error_description=User%20denied%20access&state=bd95UVMdcleJWr9SRJIDRxUXvkpvYVfamily_names=User
    if "error" in request.args:
        error = request.args["error"]
        error_description = request.args.get("error_description")
        if error == "access_denied":
            flash("You have denied the Hub access to your ORCID record."
                  " The Hub needs at least read access to your profile to be useful.", "danger")
        else:
            flash("Error occured while attempting to authorize '%s': %s" %
                  (current_user.organisation.name, error_description), "danger")
        return redirect(url_for("link"))

    client = OAuth2Session(current_user.organisation.orcid_client_id)
    try:
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

    # At this point you can fetch protected resources but lets save
    # the token and show how this is done from a persisted token
    # in /profile.
    session['oauth_token'] = token
    orcid = token['orcid']
    name = token["name"]

    # TODO: should be linked to the affiliated org

    user = current_user
    user.orcid = orcid
    if not user.name and name:
        user.name = name

    # TODO: refactor this "user" and "orciduser" effectively are the same
    orciduser = User.get(email=user.email, organisation=user.organisation)

    orcid_token, orcid_token_found = OrcidToken.get_or_create(
        user=orciduser, org=orciduser.organisation, scope=token["scope"][0])
    orcid_token.access_token = token["access_token"]
    orcid_token.refresh_token = token["refresh_token"]
    with db.atomic():
        try:
            orcid_token.save()
            user.save()
        except Exception as ex:
            db.rollback()
            flash("Failed to save data: %s" % str(ex))

    if token["scope"] == SCOPE_ACTIVITIES_UPDATE and orcid_token_found:
        swagger_client.configuration.access_token = orcid_token.access_token
        api_instance = swagger_client.MemberAPIV20Api()

        source_clientid = swagger_client.SourceClientId(
            # TODO: this shouldn't be hardcoded
            host='sandbox.orcid.org',
            path=orciduser.organisation.orcid_client_id,
            # TODO: this shouldn't be hardcoded
            uri="http://sandbox.orcid.org/client/" + orciduser.organisation.orcid_client_id)

        organisation_address = swagger_client.OrganizationAddress(
            city=orciduser.organisation.city, country=orciduser.organisation.country)

        disambiguated_organization_details = swagger_client.DisambiguatedOrganization(
            disambiguated_organization_identifier=orciduser.organisation.disambiguation_org_id,
            disambiguation_source=orciduser.organisation.disambiguation_org_source)

        # TODO: need to check if the entry doesn't exist already:
        for a in Affiliation:

            if not a & orciduser.affiliations:
                continue

            if a == Affiliation.EMP:
                rec = swagger_client.Employment()
            elif a == Affiliation.EDU:
                rec = swagger_client.Education()
            else:
                continue

            rec.source = swagger_client.Source(
                source_orcid=None,
                source_client_id=source_clientid,
                source_name=orciduser.organisation.name)

            rec.organization = swagger_client.Organization(
                name=orciduser.organisation.name,
                address=organisation_address,
                disambiguated_organization=disambiguated_organization_details)

            try:
                if a == Affiliation.EMP:
                    api_instance.create_employment(user.orcid, body=rec)
                    flash(
                        "Your ORCID employment record was updated with an affiliation entry from '%s'"
                        % orciduser.organisation, "success")
                elif a == Affiliation.EDU:
                    api_instance.create_education(user.orcid, body=rec)
                    flash(
                        "Your ORCID education record was updated with an affiliation entry from '%s'"
                        % orciduser.organisation, "success")
                else:
                    continue
                # TODO: Save the put-code in db table

            except ApiException as e:
                flash("Failed to update the entry: %s." % e.body, "danger")

        if not orciduser.affiliations:
            flash(
                "The ORCID Hub was not able to automatically write an affiliation with %s, "
                "as the nature of the affiliation with your organisation does not appear to include either "
                "Employment or Education.\n"
                "Please contact one of your Organisaiton Administrator if you believe this is an error."
                % orciduser.organisation, "danger")

    return redirect(url_for("profile"))


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """Fetch a protected resource using an OAuth 2 token."""
    user = User.get(email=current_user.email, organisation=current_user.organisation)

    try:
        orcidTokenRead = OrcidToken.get(
            user=user, org=user.organisation, scope=SCOPE_ACTIVITIES_UPDATE)
    except OrcidToken.DoesNotExist:
        return redirect(url_for("link"))
    except:
        # TODO: need to handle this
        pass
    else:
        client = OAuth2Session(
            user.organisation.orcid_client_id, token={"access_token": orcidTokenRead.access_token})
        base_url = ORCID_API_BASE + user.orcid
        # TODO: utilize asyncio/aiohttp to run it concurrently
        resp_person = client.get(base_url + "/person", headers=HEADERS)
        if resp_person.status_code == 401:
            orcidTokenRead.delete_instance()
            return redirect(url_for("link"))
        else:
            return render_template("profile.html", user=user, profile_url=ORCID_BASE_URL)


@app.route("/invite/user", methods=["GET"])
@roles_required(Role.SUPERUSER, Role.ADMIN)
def invite_user():
    """Invite a researcher to join the hub."""
    # For now on boarding of researcher is not supported
    return "Work in Progress!"


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
            email = form.orgEmailid.data.lower()
            org_name = form.orgName.data
            tech_contact = bool(request.form.get('tech_contact'))
            try:
                User.get(User.email == form.orgEmailid.data.lower())
            except User.DoesNotExist:
                pass
            finally:
                # TODO: organisation can have mutiple admins:
                # TODO: user OrgAdmin
                try:
                    org = Organisation.get(name=org_name)
                    # TODO: fix it!
                    if tech_contact:
                        org.email = email
                except Organisation.DoesNotExist:
                    org = Organisation(name=org_name, email=email)

                try:
                    org_info = OrgInfo.get(name=org.name)
                except OrgInfo.DoesNotExist:
                    pass
                else:
                    org.tuakiri_name = org_info.tuakiri_name

                try:
                    org.save()
                except Exception as ex:
                    flash("Failed to save organisation data: %s" % str(ex))

                try:
                    user = User.get(email=email)
                    user.roles |= Role.ADMIN
                    user.organisation = org
                    user.confirmed = True
                except User.DoesNotExist:
                    user = User(
                        email=form.orgEmailid.data.lower(),
                        confirmed=True,  # In order to let the user in...
                        roles=Role.ADMIN,
                        organisation=org)
                try:
                    user.save()
                except Exception as ex:
                    flash("Failed to save user data: %s" % str(ex))

                if tech_contact:
                    org.tech_contact = user
                    try:
                        org.save()
                    except Exception as ex:
                        flash(
                            "Failed to assign the user as the technical contact to the organisation: %s"
                            % str(ex))

                user_org, _ = UserOrg.get_or_create(user=user, org=org)
                user_org.is_admin = True
                try:
                    user_org.save()
                except Exception as ex:
                    flash("Failed to assign the user as an administrator to the organisation: %s" %
                          str(ex))

                # Note: Using app context due to issue:
                # https://github.com/mattupstate/flask-mail/issues/63
                with app.app_context():
                    token = generate_confirmation_token(form.orgEmailid.data.lower())
                    utils.send_email(
                        "email/org_invitation.html",
                        recipient=(form.orgName.data, form.orgEmailid.data.lower()),
                        token=token,
                        org_name=form.orgName.data,
                        user=user)
                    flash("Organisation Onboarded Successfully! "
                          "Welcome to the NZ ORCID Hub.  A notice has been sent to the Hub Admin",
                          "success")

    return render_template(
        'registration.html',
        form=form,
        org_info={r.name: r.email
                  for r in OrgInfo.select(OrgInfo.name, OrgInfo.email)})


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
        flash("This invitation to onboard the organisation wasn't sent to your email address...",
              "danger")
        return redirect(url_for("login"))

    # TODO: refactor this: user == current_user here no need to requery DB
    user = User.get(email=current_user.email, organisation=current_user.organisation)
    if not user.is_tech_contact_of():
        try:
            user.save()
        except Exception as ex:
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
        organisation = Organisation.get(email=email)
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
                organisation.disambiguation_org_id = form.disambiguation_org_id.data
                organisation.disambiguation_org_source = form.disambiguation_org_source.data
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
                    organisation.orcid_client_id = form.orgOricdClientId.data
                    organisation.orcid_secret = form.orgOrcidClientSecret.data

                    with app.app_context():
                        msg = Message("Welcome to the NZ ORCID Hub - Success", recipients=[email])
                        msg.body = "Congratulations! Your identity has been confirmed and " \
                                   "your organisation onboarded successfully.\n" \
                                   "Any researcher from your organisation can now use the Hub"
                        mail.send(msg)
                        flash("Your Onboarding is Completed!", "success")

                    try:
                        organisation.save()
                    except Exception as ex:
                        flash("Failed to save organisation data: %s" % str(ex))
                    return redirect(url_for("link"))

    elif request.method == 'GET':
        if organisation is not None and not organisation.is_email_confirmed:
            organisation.is_email_confirmed = True
            try:
                organisation.save()
            except Exception as ex:
                flash("Failed to save organisation data: %s" % str(ex))
        elif organisation is not None and organisation.is_email_confirmed:
            flash(
                """Your email link has expired. However, you should be able to login directly!""",
                "warning")
            return redirect(url_for("login"))

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
            form.disambiguation_org_id.data = organisation.disambiguation_org_id = orgInfo.disambiguation_org_id
            form.disambiguation_org_source.data = organisation.disambiguation_org_source = orgInfo.disambiguation_source

        except OrgInfo.DoesNotExist:
            pass
        organisation.country = form.country.data

    try:
        organisation.save()
    except Exception as ex:
        flash("Failed to save organisation data: %s" % str(ex))
    redirect_uri = url_for("orcid_callback", _external=True)
    client_secret_url = iri_to_uri(MEMBER_API_FORM_BASE_URL) + "?" + urlencode(
        dict(
            new_existing=NEW_CREDENTIALS,
            note=NOTE_ORCID + " " + user.organisation.name,
            contact_email=email,
            contact_name=user.name,
            org_name=user.organisation.name,
            cred_type=CRED_TYPE_PREMIUM,
            app_name=APP_NAME + " for " + user.organisation.name,
            app_description=APP_DESCRIPTION + user.organisation.name + "and its researchers",
            app_url=APP_URL,
            redirect_uri_1=redirect_uri))
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


# NB! Disable for the production!!!
@app.route("/reset_db")
@login_required
def reset_db():
    """Reset the DB for a new testing cycle."""
    User.delete().where(~(User.name**"%nzorcidhub%" | User.name**"%root%")).execute()
    Organisation.delete().where(~(Organisation.name % "%Royal%")).execute()
    return redirect(url_for("logout"))


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
    client_secret_url = iri_to_uri(MEMBER_API_FORM_BASE_URL) + "?" + urlencode(
        dict(
            new_existing=NEW_CREDENTIALS,
            note=NOTE_ORCID + " " + user.organisation.name,
            contact_email=email,
            contact_name=user.name,
            org_name=user.organisation.name,
            cred_type=CRED_TYPE_PREMIUM,
            app_name=APP_NAME + " at " + user.organisation.name,
            app_description=APP_DESCRIPTION + " at " + user.organisation.name,
            app_url=APP_URL,
            redirect_uri_1=redirect_uri))

    try:
        organisation = Organisation.get(tech_contact_id=current_user.id)
    except Organisation.DoesNotExist:
        flash("It appears that you are not the technical contact for your organisaton.", "danger")
        return redirect(url_for("login"))
    if request.method == 'POST':
        if not form.validate():
            flash('Please fill in all fields and try again!', "danger")
        else:
            organisation = Organisation.get(email=email)
            if (not (user is None) and (not (organisation is None))):
                # Update Organisation
                organisation.country = form.country.data
                organisation.city = form.city.data
                organisation.disambiguation_org_id = form.disambiguation_org_id.data
                organisation.disambiguation_org_source = form.disambiguation_org_source.data

                headers = {'Accept': 'application/json'}
                data = [
                    ('client_id', form.orgOricdClientId.data),
                    ('client_secret', form.orgOrcidClientSecret.data),
                    ('scope', '/read-public'),
                    ('grant_type', 'client_credentials'),
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
                        flash("Failed to save organisation data: %s" % str(ex))
                    return redirect(url_for("link"))

    elif request.method == 'GET':

        form.orgName.data = user.organisation.name
        form.orgEmailid.data = user.organisation.email

        form.city.data = user.organisation.city
        form.country.data = user.organisation.country
        form.disambiguation_org_id.data = user.organisation.disambiguation_org_id
        form.disambiguation_org_source.data = user.organisation.disambiguation_org_source
        form.orgOricdClientId.data = user.organisation.orcid_client_id
        form.orgOrcidClientSecret.data = user.organisation.orcid_secret

        form.orgName.render_kw = {'readonly': True}
        form.orgEmailid.render_kw = {'readonly': True}

    try:
        organisation.save()
    except Exception as ex:
        flash("Failed to save organisation data: %s" % str(ex))
    return render_template('orgconfirmation.html', client_secret_url=client_secret_url, form=form)
