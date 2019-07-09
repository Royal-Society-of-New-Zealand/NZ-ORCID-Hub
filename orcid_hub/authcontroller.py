# -*- coding: utf-8 -*-
"""Authentication views.

Collection of applicion views involved in organisation on-boarding and
user (reseaser) affiliations.
"""

import base64
import json
import re
import secrets
import zlib
from datetime import datetime, timedelta
from os import path, remove
from tempfile import gettempdir
from time import time
from urllib.parse import parse_qs, quote, unquote, urlparse

import requests
import validators
from flask import (Response, abort, current_app, flash, redirect,
                   render_template, request, session, stream_with_context,
                   url_for)
from flask_login import current_user, login_required, login_user, logout_user
from itsdangerous import Signer
from oauthlib.oauth2 import rfc6749
from requests_oauthlib import OAuth2Session
from werkzeug.urls import iri_to_uri
from werkzeug.utils import secure_filename

from orcid_api.rest import ApiException

from . import app, cache, db, orcid_client
from . import orcid_client as scopes
# TODO: need to read form app.config[...]
from .config import (APP_DESCRIPTION, APP_NAME, APP_URL, AUTHORIZATION_BASE_URL, CRED_TYPE_PREMIUM,
                     MEMBER_API_FORM_BASE_URL, NOTE_ORCID, ORCID_API_BASE, ORCID_BASE_URL,
                     TOKEN_URL)
from .forms import OrgConfirmationForm, TestDataForm
from .login_provider import roles_required
from .models import (Affiliation, OrcidAuthorizeCall, OrcidToken, Organisation, OrgInfo,
                     OrgInvitation, Role, Task, TaskType, Url, User, UserInvitation, UserOrg,
                     audit_models, validate_orcid_id)
from .utils import (append_qs, get_next_url, enqueue_user_records, notify_about_update,
                    read_uploaded_file, register_orcid_webhook)

HEADERS = {'Accept': 'application/vnd.orcid+json', 'Content-type': 'application/vnd.orcid+json'}
ENV = app.config.get("ENV")


@app.context_processor
def utility_processor():  # noqa: D202
    """Define funcions callable form Jinja2 using application context."""

    def has_audit_logs():
        return bool(audit_models)

    def onboarded_organisations():
        rv = cache.get("onboarded_organisations")
        if not rv:
            rv = list(
                Organisation.select(Organisation.name, Organisation.tuakiri_name).where(
                    Organisation.confirmed.__eq__(True)))
            cache.set("onboarded_organisations", rv, timeout=3600)
        return rv

    def orcid_login_url():
        return url_for("orcid_login", next=get_next_url())

    def tuakiri_login_url():
        _next = get_next_url()
        external_sp = app.config.get("EXTERNAL_SP")
        if external_sp:
            session["auth_secret"] = secret_token = secrets.token_urlsafe()
            _next = url_for("sso-login", _next=_next, _external=True)
            login_url = append_qs(external_sp, _next=_next, key=secret_token)
        else:
            login_url = url_for("handle_login", _next=_next)
        return login_url

    def current_task():
        try:
            task_id = request.args.get("task_id")
            if task_id:
                task_id = int(task_id)
            else:
                url = request.args.get("url")
                if not url:
                    return False
                qs = parse_qs(urlparse(url).query)
                task_id = qs.get("task_id", [None])[0]
                if task_id:
                    task_id = int(task_id)
        except:
            return None
        return Task.get(task_id)

    def current_record():
        task = current_task()
        if not task:
            return None
        try:
            record_id = request.args.get("record_id")
            if record_id:
                record_id = int(record_id)
            else:
                url = request.args.get("url")
                if not url:
                    return None
                qs = parse_qs(urlparse(url).query)
                record_id = qs.get("record_id", [None])[0]
                if record_id:
                    record_id = int(record_id)
        except:
            return None
        return task.records.model_class.get(record_id)

    return dict(
        orcid_login_url=orcid_login_url,
        tuakiri_login_url=tuakiri_login_url,
        onboarded_organisations=onboarded_organisations,
        current_task=current_task,
        current_record=current_record,
        has_audit_logs=has_audit_logs,
    )


@app.route("/index.html")
@app.route("/index")
@app.route("/login")
@app.route("/")
def index():
    """Show main landing page with login buttons."""
    return render_template("index.html")


@app.route("/about.html")
@app.route("/about")
def about():
    """Show about page with login buttons."""
    if request.args:
        abort(403)
    return render_template("about.html")


@app.route("/faq.html")
@app.route("/faq")
def faq():
    """Show FAQ page with login buttons."""
    if request.args:
        abort(403)
    return render_template("faq.html")


@app.route("/sso/sp")
@app.route("/Tuakiri/SP")
def shib_sp():
    """Remote Shibboleth authenitication handler.

    All it does passes all response headers to the original calller.
    """
    _next = get_next_url()
    _key = request.args.get("key")
    if _next:
        data = {k: v for k, v in request.headers.items()}
        data = zlib.compress(json.dumps(data).encode())

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
        with open(data_filename, "rb") as kf:
            data = kf.read()
        remove(data_filename)
    except Exception as ex:
        abort(403, ex)
    return data, 200, {"Content-Type": "application/octet-stream"}


@app.route("/sso/login", endpoint="sso-login")
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
    external_sp = app.config.get("EXTERNAL_SP")
    if external_sp:
        if "auth_secret" not in session:
            return redirect(url_for("index"))
        sp_url = urlparse(external_sp)
        attr_url = sp_url.scheme + "://" + sp_url.netloc + "/sp/attributes/" + session.get(
            "auth_secret")
        resp = requests.get(attr_url)
        data = json.loads(zlib.decompress(resp.content))
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

        orcid = data.get("Orcid-Id")
        if orcid:
            orcid = orcid.split('/')[-1]
            try:
                validate_orcid_id(orcid)
            except ValueError:
                app.logger.exception(f"Invalid OCID iD value recieved via 'Orcid-Id': {orcid}")
                orcid = None

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
            app.logger.exception("Failed to save organisation data")
            abort(500, ex)

    q = User.select().where(User.email == email)
    if eppn:
        q = q.orwhere(User.eppn == eppn)
    if secondary_emails:
        q = q.orwhere(User.email.in_(secondary_emails))
    user = q.first()

    if user:
        # Add Shibboleth meta data if they are missing
        if name and user.name != name:
            user.name = name
        if not user.first_name and first_name:
            user.first_name = first_name
        if not user.last_name and last_name:
            user.last_name = last_name
        if not user.eppn and eppn:
            user.eppn = eppn
        if not user.orcid:
            user.orcid = orcid
    else:

        if not (unscoped_affiliation & {"faculty", "staff", "student"}):
            msg = f"You cannot automatically have your association with '{shib_org_name}' recognised as your " \
                  f"relationship according to your identity provider is '{unscoped_affiliation}' and not one " \
                  f"eligible: 'staff', 'faculty' or 'student'. If this is incorrect please contact your organisation."
            app.logger.warning(msg)
            flash(msg, "warning")

        user = User.create(
            email=email,
            eppn=eppn,
            name=name,
            first_name=first_name,
            last_name=last_name,
            orcid=orcid,
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

    return redirect(url_for("index"))


def login0(auth=None):
    """Handle secure login for performance and stress testing.

    Signature is the signature of email value with the application key.
    """
    if not auth:
        auth = request.headers.get("Authorization")
        if not auth:
            resp = Response()
            resp.headers["WWW-Authenticate"] = 'Basic realm="Access to the load-testing login"'
            resp.status_code = 401
            return resp
        if ':' not in auth:
            auth = base64.b64decode(auth).decode()

    email, signature = auth.split(':')
    s = Signer(app.secret_key)
    if s.validate(email + '.' + signature):
        try:
            u = User.get(email=email)
            login_user(u)
            return redirect(get_next_url() or url_for("index"))
        except User.DoesNotExist:
            return handle_login()
    abort(403)


@roles_required(Role.SUPERUSER)
def test_data():
    """Generate the test data for the stress/performance tests."""
    form = TestDataForm(optional=True)

    if form.validate_on_submit():
        data = read_uploaded_file(form)
        if form.file_.data:
            filename, _ = path.splitext(secure_filename(form.file_.data.filename))
        else:
            filename = "test-data"

        @stream_with_context
        def content(data=None):
            s = Signer(app.secret_key)
            if data:
                sep = '\t' if '\t' in data else ','
                for line_no, line in enumerate(data.splitlines()):
                    values = [v.strip() for v in line.split(sep)]
                    for v in values:
                        if '@' in v:
                            try:
                                validators.email(v)
                                email = v
                                break
                            except validators.ValidationFailure:
                                pass
                    else:
                        if line_no == 0:
                            continue
                        flash("Missing email address in the file", "danger")
                        abort(400)
                    yield s.get_signature(email).decode() + sep + sep.join(values)
                    yield '\n'
            else:
                use_known_orgs = bool(
                    request.args.get("use-known-orgs") or form.use_known_orgs.data)
                org_count = int(
                    request.args.get("orgs") or request.args.get("org_count")
                    or request.args.get("org-count") or form.org_count.data or 100)
                user_count = int(
                    request.args.get("users") or request.args.get("user_count")
                    or request.args.get("user-count") or form.user_count.data or 400)

                import faker
                f = faker.Faker()
                if use_known_orgs:
                    orgs = [
                        f'"{o.name}"' for o in Organisation.select().where(Organisation.confirmed)
                        .limit(org_count)
                    ]
                    org_count = len(orgs)
                else:
                    orgs = [f'"{f.company()}"' for _ in range(org_count)]

                for n in range(user_count):
                    email = f.email()
                    yield ','.join([
                        s.get_signature(email).decode(),
                        email,
                        f.user_name(),
                        f.password(),
                        orgs[n % org_count],
                        f.first_name(),
                        f.last_name(),
                        [
                            "staff",
                            "student",
                        ][n % 2],
                    ])
                    yield '\n'

        resp = Response(content(data), mimetype="text/csv")
        resp.headers["Content-Disposition"] = f"attachment; filename={filename}_SIGNED.csv"
        return resp

    return render_template("form.html", form=form, title="Load Test Data Generation")


if app.config.get("LOAD_TEST"):
    app.add_url_rule("/test-data", "test_data", test_data, methods=["GET", "POST"])
    app.add_url_rule("/login0/<string:auth>", "login0", login0)
    app.add_url_rule("/login0", "login0", login0)


@app.route("/link")
@login_required
def link():
    """Link the user's account with ORCID (i.e. affiliates user with his/her org on ORCID)."""
    # TODO: handle organisation that are not on-boarded
    redirect_uri = url_for("orcid_callback", _external=True)
    external_sp = app.config.get("EXTERNAL_SP")
    if external_sp:
        sp_url = urlparse(external_sp)
        redirect_uri = sp_url.scheme + "://" + sp_url.netloc + "/auth/" + quote(redirect_uri)

    if current_user.organisation and not current_user.organisation.confirmed:
        flash(f"Your organisation ({current_user.organisation.name}) is not yet using the Hub,"
              f" see your Technical Contact for a timeline", "warning")
        return redirect(url_for("index"))

    client_write = OAuth2Session(
        current_user.organisation.orcid_client_id,
        scope=[scopes.ACTIVITIES_UPDATE, scopes.READ_LIMITED],
        redirect_uri=redirect_uri)
    authorization_url_write, state = client_write.authorization_url(
        AUTHORIZATION_BASE_URL, state=session.get("oauth_state"))
    session["oauth_state"] = state

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
                client_write.scope = [scopes.READ_LIMITED]
                authorization_url_read, state = client_write.authorization_url(
                    AUTHORIZATION_BASE_URL, state)
                orcid_url_read = append_qs(
                    iri_to_uri(authorization_url_read),
                    family_names=current_user.last_name,
                    given_names=current_user.first_name,
                    email=current_user.email)
                client_write.scope = [scopes.PERSON_UPDATE, scopes.READ_LIMITED]
                authorization_url_person_update, state = client_write.authorization_url(
                    AUTHORIZATION_BASE_URL, state)
                orcid_url_person_update = append_qs(
                    iri_to_uri(authorization_url_person_update),
                    family_names=current_user.last_name,
                    given_names=current_user.first_name,
                    email=current_user.email)
                client_write.scope = [scopes.AUTHENTICATE]
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
                    orcid_url_person_update=orcid_url_person_update,
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
    - User authorises an organisation (uses org. key);
    - User completes registration (uses org. key);
    - Administrator completes registration (uses org. key);
    - Technical contact completes organisation registration/on-boarding (uses AUTHENTICATION key);
    """
    login = request.args.get("login")
    if login != "1":
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
    else:
        return orcid_login_callback(request)

    if "error" in request.args:
        error = request.args["error"]
        error_description = request.args.get("error_description")
        if error == "access_denied":
            flash(f"You have denied {current_user.organisation.name} access to your ORCID record."
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
            flash("Retry giving permissions, or if the issue persists "
                  "please contact orcid@royalsociety.org.nz for support", "danger")
            app.logger.error(
                f"For {current_user} session state was {session.get('oauth_state', 'empty')}, "
                f"whereas state returned from ORCID is {state}")
            return redirect(url_for("index"))

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
        return redirect(url_for("index"))
    except rfc6749.errors.MissingTokenError:
        flash("Missing token.", "danger")
        return redirect(url_for("index"))
    except Exception as ex:
        flash(f"Something went wrong contact orcidhub support for issue: {ex}")
        app.logger.exception(f"For {current_user} encountered exception")
        return redirect(url_for("index"))

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

    scope_list = ','.join(token.get("scope", []))
    if not scope_list:
        flash("Scope missing, contact orcidhub support", "danger")
        app.logger.error(f"For {current_user} encountered exception: Scope missing")
        return redirect(url_for("index"))

    orcid_token, orcid_token_found = OrcidToken.get_or_create(
        user_id=user.id, org=user.organisation, scopes=scope_list)
    orcid_token.access_token = token["access_token"]
    orcid_token.refresh_token = token["refresh_token"]
    orcid_token.expires_in = token["expires_in"]
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
                    user.organisation, scope_list)

    if scopes.ACTIVITIES_UPDATE in scope_list and orcid_token_found:
        api = orcid_client.MemberAPIV3(user=user, access_token=orcid_token.access_token)

        for a in Affiliation:

            if not a & user.affiliations:
                continue

            try:
                api.create_or_update_affiliation(initial=True, affiliation=a)
            except ApiException as ex:
                flash(f"Failed to update the entry: {ex.body}", "danger")
            except Exception:
                app.logger.exception(f"For {user} encountered exception")

        if not user.affiliations:
            flash(
                f"The ORCID Hub was not able to automatically write an affiliation with "
                f"{user.organisation}, as the nature of the affiliation with your "
                f"organisation does not appear to include either Employment or Education.\n "
                f"Please contact your Organisation Administrator(s) if you believe this is an error.",
                "warning")

    notify_about_update(user, event_type="UPDATED" if orcid_token_found else "CREATED")
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
        return redirect(url_for("index"))
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
        app_description=APP_DESCRIPTION + " " + current_user.organisation.name + " and its researchers.",
        app_url=APP_URL,
        redirect_uri_1=url_for("orcid_callback", _external=True))

    current_user.organisation.api_credentials_requested_at = datetime.utcnow()
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
            return redirect(url_for("index"))

        if request.method == "GET":
            flash("""If you currently don't know Client ID and Client Secret,
            Please request these from ORCID by clicking on link 'Take me to ORCID to obtain Client ID and Client Secret'
            and come back to this form once you have them.""", "info")

            try:
                oi = OrgInfo.get((OrgInfo.email == email)
                                 | (OrgInfo.tuakiri_name == user.organisation.name)
                                 | (OrgInfo.name == user.organisation.name))

                if organisation.city:
                    form.city.data = oi.city = organisation.city
                else:
                    form.city.data = organisation.city = oi.city

                if organisation.disambiguated_id:
                    form.disambiguated_id.data = oi.disambiguated_id = organisation.disambiguated_id
                else:
                    form.disambiguated_id.data = organisation.disambiguated_id = oi.disambiguated_id

                if organisation.disambiguation_source:
                    form.disambiguation_source.data = oi.disambiguation_source = organisation.disambiguation_source
                else:
                    form.disambiguation_source.data = organisation.disambiguation_source = oi.disambiguation_source
                oi.save()
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
            flash("Something is wrong! The Client ID and Client Secret are not valid!\n"
                  "Please recheck and contact Hub support if this error continues", "danger")
        else:

            if not organisation.confirmed:
                organisation.confirmed = True
                app.logger.info("For %r Onboarding is Completed!", user)
                flash("Your Onboarding is Completed!", "success")
            else:
                flash("Organisation information updated successfully!", "success")

            form.populate_obj(organisation)
            organisation.disambiguated_id = organisation.disambiguated_id.strip()
            organisation.disambiguation_source = organisation.disambiguation_source.strip()
            organisation.api_credentials_entered_at = datetime.utcnow()
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
                        oi.confirmed_at = datetime.utcnow()
                        oi.save()
                    # Delete the "stale" invitations:
                    OrgInvitation.delete().where(OrgInvitation.id != oi.id,
                                                 OrgInvitation.org == organisation).execute()

                org_info = OrgInfo.get((OrgInfo.tuakiri_name == organisation.name)
                                       | (OrgInfo.name == organisation.name))
                if organisation.city:
                    org_info.city = organisation.city

                if organisation.disambiguated_id:
                    org_info.disambiguated_id = organisation.disambiguated_id

                if organisation.disambiguation_source:
                    org_info.disambiguation_source = organisation.disambiguation_source

                org_info.save()
            except OrgInvitation.DoesNotExist:
                pass
            except OrgInfo.DoesNotExist:
                pass

            return redirect(url_for("link"))

    return render_template('orgconfirmation.html', form=form, organisation=organisation)


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
    except Exception:
        app.logger.exception("Failed to log out.")
    session.clear()

    if org_name:
        external_sp = app.config.get("EXTERNAL_SP")
        if external_sp:
            sp_url = urlparse(external_sp)
            sso_url_base = sp_url.scheme + "://" + sp_url.netloc
        else:
            sso_url_base = ''
        return redirect(sso_url_base + "/Shibboleth.sso/Logout?return=" + quote(
            url_for(
                "uoa_slo" if org_name and org_name == "University of Auckland" else "index",
                _external=True)))

    session.clear()
    resp = redirect(url_for("index", logout=True))
    resp.delete_cookie(app.session_cookie_name)
    return resp


@app.route("/uoa-slo")
def uoa_slo():
    """Show the logout info for UoA users."""
    flash("""You had logged in from 'The University of Auckland'.
You have to close all open browser tabs and windows in order
in order to complete the log-out.""", "warning")
    return render_template("uoa-slo.html")


@app.route("/orcid/login/")
@app.route("/orcid/login/<invitation_token>")
def orcid_login(invitation_token=None):
    """Authenticate a user via ORCID.

    If an invitation token is presented, perform affiliation of the user or on-boarding
    of the organisation, if the user is the technical conatact of
    the organisation. For technical contacts the email should be made available for
    READ LIMITED scope.
    """
    _next = get_next_url()
    redirect_uri = url_for("orcid_callback", _next=_next, _external=True)

    try:
        orcid_scopes = [scopes.AUTHENTICATE]

        client_id = app.config.get("ORCID_CLIENT_ID")
        if invitation_token:
            invitation = UserInvitation.select().where(
                UserInvitation.token == invitation_token).first() or OrgInvitation.select().where(
                    OrgInvitation.token == invitation_token).first()
            if not invitation:
                app.logger.warning(f"Failed to login via ORCID using token {invitation_token}")
                flash(f"Failed to login via ORCID using token {invitation_token}", "danger")
                return redirect(url_for("index"))
            user, org = invitation.invitee, invitation.org
            if not user:
                user = User.get(email=invitation.email)

            is_scope_person_update = hasattr(
                invitation, "is_person_update_invite") and invitation.is_person_update_invite

            if hasattr(invitation, "task_id") and invitation.task_id:
                is_scope_person_update = Task.select().where(
                    Task.id == invitation.task_id, Task.task_type == TaskType.PROPERTY).exists() or Task.select().where(
                    Task.id == invitation.task_id, Task.task_type == TaskType.OTHER_ID).exists()

            if is_scope_person_update and OrcidToken.select().where(
                    OrcidToken.user == user, OrcidToken.org == org,
                    OrcidToken.scopes.contains(scopes.PERSON_UPDATE)).exists():
                flash(
                    "You have already given permission with scope '/person/update' which allows organisation to write, "
                    "update and delete items in the other-names, keywords, countries, researcher-urls, websites, "
                    "and personal external identifiers sections of the record. Now you can simply login on orcidhub",
                    "warning")
                return redirect(url_for("index"))
            elif not is_scope_person_update and not isinstance(
                    invitation, OrgInvitation) and OrcidToken.select().where(
                        OrcidToken.user == user, OrcidToken.org == org,
                        OrcidToken.scopes.contains(scopes.ACTIVITIES_UPDATE)).exists():
                flash("You have already given permission, you can simply login on orcidhub",
                      "warning")
                return redirect(url_for("index"))

            try:
                user_org = UserOrg.get(user=user, org=org)

                if invitation.created_at < datetime.utcnow() - timedelta(weeks=4) and not user_org.is_admin:
                    flash(
                        "It's been more than 4 weeks since your invitation was sent and it has expired. "
                        "Please contact the sender to issue a new one", "danger")
                    app.logger.warning(
                        f"Failed to login via ORCID, as {user.email} from {org.name} organisation, "
                        "was trying old invitation token")
                    return redirect(url_for("index"))
                elif invitation.created_at < datetime.utcnow() - timedelta(weeks=2) and user_org.is_admin:
                    flash(
                        "It's been more than 2 weeks since your invitation was sent and it has expired. "
                        "Please contact the sender to issue a new one", "danger")
                    app.logger.warning(
                        f"Failed to login via ORCID, as {user.email} from {org.name} organisation, "
                        "was trying old invitation token")
                    return redirect(url_for("index"))

                if org.orcid_client_id and not isinstance(invitation, OrgInvitation):
                    client_id = org.orcid_client_id
                    if is_scope_person_update:
                        orcid_scopes = [scopes.PERSON_UPDATE]
                    else:
                        orcid_scopes = [scopes.ACTIVITIES_UPDATE]
                orcid_scopes.append(scopes.READ_LIMITED)

                redirect_uri = append_qs(redirect_uri, invitation_token=invitation_token)
            except Organisation.DoesNotExist:
                flash("Organisation '{org.name}' doesn't exist in the Hub!", "danger")
                app.logger.error(
                    f"User '{user}' attempted to affiliate with non-existing organisation {org.name}"
                )
                return redirect(url_for("index"))

        external_sp = app.config.get("EXTERNAL_SP")
        if external_sp and not client_id:
            sp_url = urlparse(external_sp)
            u = Url.shorten(redirect_uri)
            redirect_uri = url_for("short_url", short_id=u.short_id, _external=True)
            redirect_uri = sp_url.scheme + "://" + sp_url.netloc + "/auth/" + quote(redirect_uri)
        # if the invitation token is missing perform only authentication (in the call back handler)
        redirect_uri = append_qs(redirect_uri, login="1")

        client_write = OAuth2Session(client_id, scope=orcid_scopes, redirect_uri=redirect_uri)

        authorization_url, state = client_write.authorization_url(
            AUTHORIZATION_BASE_URL, state=session.get("oauth_state"))
        # if the inviation token is preset use it as OAuth state
        session["oauth_state"] = state
        # ORCID authorization URL:
        orcid_auth_url = iri_to_uri(authorization_url)
        if invitation_token:
            orcid_auth_url = append_qs(orcid_auth_url, email=user.email)
            # For funding record, we dont have first name and Last Name
            if user.last_name and user.first_name:
                orcid_auth_url = append_qs(
                    orcid_auth_url,
                    family_names=user.last_name,
                    given_names=user.first_name)

        OrcidAuthorizeCall.create(url=orcid_auth_url, state=state)

        return render_template("orcidLogoutAndCallback.html", callback_url=orcid_auth_url)

    except Exception as ex:
        flash("Something went wrong. Please contact orcid@royalsociety.org.nz for support!",
              "danger")
        app.logger.exception(f"Failed to login via ORCID: {ex}")
        return redirect(url_for("index"))


def orcid_login_callback(request):
    """Handle call-back for user authentication via ORCID."""
    _next = get_next_url()
    state = request.args.get("state")
    invitation_token = request.args.get("invitation_token")

    if not state or state != session.get("oauth_state"):
        flash("Something went wrong, Please retry giving permissions or if issue persists then, "
              "Please contact orcid@royalsociety.org.nz for support", "danger")
        return redirect(url_for("index"))

    error = request.args.get("error")
    if error == "access_denied":
        flash(
            "You have just denied access to the Hub knowing your ORCID iD; to log in please try again and authorise",
            "warning")
        return redirect(url_for("index"))

    try:
        orcid_client_id = app.config["ORCID_CLIENT_ID"]
        orcid_client_secret = app.config["ORCID_CLIENT_SECRET"]
        org = email = None

        if invitation_token:
            invitation = UserInvitation.select().where(
                UserInvitation.token == invitation_token).first() or OrgInvitation.select().where(
                    OrgInvitation.token == invitation_token).first()
            if not invitation:
                app.logger.warning(f"Failed to login via ORCID using token {invitation_token}")
                flash(f"Failed to login via ORCID using token {invitation_token}", "danger")
                return redirect(url_for("index"))
            user, org, email = invitation.invitee, invitation.org, invitation.email
            if not user:
                user = User.get(email=email)
            if not org:
                org = user.organisation

            try:
                UserOrg.get(user=user, org=org)
            except Organisation.DoesNotExist:
                flash("The linkage with the organisation '{org.name}' doesn't exist in the Hub!", "danger")
                app.logger.error(
                    f"User '{user}' attempted to affiliate with an organisation that's not known: {org.name}"
                )
                return redirect(url_for("index"))
            if org.orcid_client_id and org.orcid_secret and not isinstance(invitation, OrgInvitation):
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

        orcid_id = token.get("orcid")
        if not orcid_id:
            app.logger.error(f"Missing ORCID iD: {token}")
            abort(401, "Missing ORCID iD.")
        try:
            # If there is an invitation token then check user based on email; else based on orcid
            if not invitation_token:
                user = User.get(orcid=orcid_id)
                org = user.organisation
            else:
                # One ORCID iD cannot be associated with two different email address of same organisation.
                users = User.select().where(User.orcid == orcid_id, User.email != email)
                if UserOrg.select().where(
                        UserOrg.user.in_(users), UserOrg.org == org).exists():
                    flash(
                        f"This {orcid_id} is already associated with other email address of same organisation: {org}. "
                        "Please use other ORCID iD to login. If you need help then "
                        "kindly contact orcid@royalsociety.org.nz support for issue", "danger")
                    logout_user()
                    return redirect(url_for("index"))

        except User.DoesNotExist:
            if not email:
                flash(
                    f"The account with ORCID iD {orcid_id} is not known in the Hub. "
                    "Try again when you've linked your ORCID iD with an organisation through either "
                    "a Tuakiri-mediated log in, or from an organisation's email invitation",
                    "warning")
                return redirect(url_for("index"))

        if not user.orcid and orcid_id:
            user.orcid = orcid_id
            if org:
                user.organisation = org
            if user.organisation.webhook_enabled:
                register_orcid_webhook.queue(user)
        elif user.orcid != orcid_id and email:
            flash(f"This {email} is already associated with {user.orcid} and you are trying to login with {orcid_id}. "
                  "Please use correct ORCID iD to login. If you need help then "
                  "kindly contact orcid@royalsociety.org.nz support for issue", "danger")
            logout_user()
            return redirect(url_for("index"))
        if not user.name and token.get("name"):
            user.name = token["name"]
        if not user.confirmed:
            user.confirmed = True

        login_user(user)
        oac.user_id = current_user.id
        oac.save()

        try:
            user_org = UserOrg.get(user=user, org=org)
        except UserOrg.DoesNotExist:
            flash("You are not linked to the organisation '{org.name}'!", "danger")
            app.logger.error(
                f"User '{user}' attempted to affiliate with an organisation that's not known: {org.name}"
            )
            return redirect(url_for("index"))

        session['Should_not_logout_from_ORCID'] = True
        if invitation_token:
            if isinstance(invitation, OrgInvitation):
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
                    message = json.loads(ex.body.decode()).get('user-message')
                    if ex.status == 401:
                        flash(f"Got ORCID API Exception: {message}", "danger")
                    else:
                        flash(f"Exception when calling MemberAPI: {message}", "danger")
                        flash(
                            f"The Hub cannot verify your email address from your ORCID record. "
                            f"Please, change the visibility level for your organisation email address "
                            f"'{email}' to 'trusted parties' and, if the error persists, that you have"
                            f"verified this email in your record.", "danger")
                    logout_user()
                    return redirect(url_for("index"))
                data = json.loads(api_response.data)
                if data and data.get("email") and any(
                        e.get("email").lower() == email for e in data.get("email")):
                    if invitation.tech_contact and org.tech_contact != user:
                        org.tech_contact = user
                        org.save()
                    user.save()
                    if not (org.confirmed and org.orcid_client_id) and user.is_tech_contact_of(org):
                        return redirect(_next or url_for("onboard_org"))
                    elif not org.confirmed and not user.is_tech_contact_of(org):
                        flash(
                            f"Your '{org}' has yet not been onboard. Please, try again once your technical contact"
                            f" onboards your organisation on ORCIDHUB", "warning")
                        return redirect(url_for("about"))
                    elif org.confirmed:
                        return redirect(_next or url_for('viewmembers.index_view'))
                else:
                    logout_user()
                    flash(
                        f"The Hub cannot verify your email address from your ORCID record. "
                        f"Please, change the visibility level for your organisation email address "
                        f"'{email}' to 'trusted parties' and also remember to verify the email address "
                        "under ORCID account settings.", "danger")
                    return redirect(url_for("index"))

            else:
                scope_list = ','.join(token.get("scope", []))
                if not scope_list:
                    flash("Scope missing, contact orcidhub support", "danger")
                    app.logger.error("For %r encountered exception: Scope missing", user)
                    return redirect(url_for("index"))

                orcid_token, orcid_token_found = OrcidToken.get_or_create(
                    user_id=user.id, org=org, scopes=scope_list)
                orcid_token.access_token = token["access_token"]
                orcid_token.refresh_token = token["refresh_token"]
                orcid_token.expires_in = token["expires_in"]
                with db.atomic():
                    try:
                        user.organisation = org
                        user.save()
                        orcid_token.save()
                    except Exception as ex:
                        db.rollback()
                        flash(f"Failed to save data: {ex}")
                        app.logger.exception("Failed to save token.")

                try:
                    if invitation.affiliations & (Affiliation.EMP | Affiliation.EDU):
                        api = orcid_client.MemberAPIV3(org, user)
                        params = {k: v for k, v in invitation._data.items() if v != ""}
                        for a in Affiliation:
                            if a & invitation.affiliations:
                                params["affiliation"] = a
                                params["initial"] = True
                                api.create_or_update_affiliation(**params)
                    invitation.confirmed_at = datetime.utcnow()
                    invitation.save()

                except UserInvitation.DoesNotExist:
                    pass
                except Exception as ex:
                    flash(f"Something went wrong: {ex}", "danger")
                    app.logger.exception("Failed to create affiliation record")

        if not OrcidToken.select().where(OrcidToken.user == user, OrcidToken.org == org).exists():
            if user.is_tech_contact_of(org) and not org.confirmed:
                return redirect(url_for("onboard_org"))
            elif not user.is_tech_contact_of(org) and user_org.is_admin and not org.confirmed:
                flash(
                    f"Your '{org}' has not be onboarded."
                    f"Please, try again once your technical contact onboards your organisation on ORCIDHUB",
                    "warning")
                return redirect(url_for("about"))
            elif org.confirmed and user_org.is_admin:
                return redirect(url_for('viewmembers.index_view'))
            else:
                return redirect(url_for("link"))
        # Loging by invitation
        if invitation_token:
            notify_about_update(user, event_type="CREATED")
            enqueue_user_records(user)
        return redirect(url_for("profile"))

    except User.DoesNotExist:
        flash("You are not known in the Hub...", "danger")
        return redirect(url_for("index"))
    except UserOrg.DoesNotExist:
        flash("Your organisation is not known or the organisation data are missing...", "danger")
        return redirect(url_for("index"))
    except rfc6749.errors.MissingCodeError:
        flash(f"{request.url} cannot be invoked directly...", "danger")
        return redirect(url_for("index"))
    except rfc6749.errors.MissingTokenError:
        flash("Missing token.", "danger")
        return redirect(url_for("index"))
    except Exception as ex:
        flash(f"Something went wrong contact orcid@royalsociety.org.nz support for issue: {ex}",
              "danger")
        app.logger.exception("Unhandled excetion occrured while handling ORCID call-back.")
        return redirect(url_for("index"))


@app.route("/select/user_org/<int:user_org_id>")
@login_required
def select_user_org(user_org_id):
    """Change the current organisation of the current user."""
    user_org_id = int(user_org_id)
    _next = get_next_url() or request.referrer or url_for("index")
    try:
        uo = UserOrg.get(id=user_org_id)
        if (uo.user.orcid == current_user.orcid or uo.user.email == current_user.email
                or uo.user.eppn == current_user.eppn):
            if uo.user_id != current_user.id:
                login_user(uo.user)
            if current_user.organisation_id != uo.org_id:
                current_user.organisation_id = uo.org_id
                current_user.save()
        else:
            flash("You cannot switch your user to this organisation", "danger")
    except UserOrg.DoesNotExist:
        flash("Your are not related to this organisation.", "danger")
    return redirect(_next)
