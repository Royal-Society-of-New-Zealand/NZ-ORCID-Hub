# -*- coding: utf-8 -*-
"""Application views."""

import json
import os
from collections import namedtuple
from datetime import datetime
from urllib.parse import urlparse

from flask import (abort, flash, redirect, render_template, request, send_from_directory, url_for)
from flask_admin.actions import action
from flask_admin.contrib.peewee import ModelView
from flask_admin.form import SecureForm
from flask_admin.model import typefmt
from flask_login import current_user, login_required
from jinja2 import Markup

import orcid_client
import utils
from application import admin, app
from config import ORCID_BASE_URL, SCOPE_ACTIVITIES_UPDATE, SCOPE_READ_LIMITED
from forms import (BitmapMultipleValueField, FileUploadForm, OrgRegistrationForm, RecordForm,
                   UserInvitationForm)
from login_provider import roles_required
from models import PartialDate as PD
from models import (CharField, OrcidApiCall, OrcidToken, Organisation, OrgInfo, OrgInvitation,
                    Role, TextField, User, UserOrg, UserOrgAffiliation, db)
# NB! Should be disabled in production
from pyinfo import info
from swagger_client.rest import ApiException
from utils import generate_confirmation_token

HEADERS = {"Accept": "application/vnd.orcid+json", "Content-type": "application/vnd.orcid+json"}


@app.route("/favicon.ico")
def favicon():
    """Support for the "favicon" legacy: faveicon location in the root directory."""
    return send_from_directory(
        os.path.join(app.root_path, "static", "images"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon")


@app.route("/pyinfo")
@roles_required(Role.SUPERUSER)
def pyinfo():
    """Show Python and runtime environment and settings."""
    return render_template("pyinfo.html", **info)


@app.route("/about")
def about():
    """Show "about" page."""
    return render_template("about.html")


class AppModelView(ModelView):
    """ModelView customization."""

    form_base_class = SecureForm
    column_type_formatters = dict(typefmt.BASE_FORMATTERS)
    column_type_formatters.update({
        datetime:
        lambda view, value: Markup(value.strftime("%Y‑%m‑%d&nbsp;%H:%M")),
    })

    def init_search(self):
        if self.column_searchable_list:
            for p in self.column_searchable_list:
                if "." in p:
                    m, p = p.split('.')
                    m = getattr(self.model, m).rel_model
                    p = getattr(m, p)

                elif isinstance(p, str):
                    p = getattr(self.model, p)

                field_type = type(p)

                # Check type
                if (field_type != CharField and field_type != TextField):
                    raise Exception('Can only search on text columns. ' +
                                    'Failed to setup search for "%s"' % p)

                self._search_fields.append(p)

        return bool(self._search_fields)

    def is_accessible(self):
        """Verify if the view is accessible for the current user."""
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role(Role.SUPERUSER):
            return True

        return False

    def inaccessible_callback(self, name, **kwargs):
        """Handle access denial. Redirect to login page if user doesn"t have access."""
        return redirect(url_for("login", next=request.url))


class UserAdmin(AppModelView):
    """User model view."""
    roles = {1: "Superuser", 2: "Administrator", 4: "Researcher", 8: "Technical Contact"}

    column_exclude_list = ("password", "username", "first_name", "last_name", )
    column_formatters = dict(
        roles=lambda v, c, m, p: ", ".join(n for r, n in v.roles.items() if r & m.roles),
        orcid=lambda v, c, m, p: m.orcid.replace("-", "\u2011") if m.orcid else "")
    column_searchable_list = ("name", "orcid", "email", "eppn", "organisation.name", )
    form_overrides = dict(roles=BitmapMultipleValueField)
    form_args = dict(roles=dict(choices=roles.items()))

    form_ajax_refs = {"organisation": {"fields": (Organisation.name, "name")}}
    can_export = True


class OrganisationAdmin(AppModelView):
    """Organisation model view."""
    column_exclude_list = ("orcid_client_id", "orcid_secret", )
    column_searchable_list = ("name", "tuakiri_name", "city", )


class OrgInfoAdmin(AppModelView):
    """OrgInfo model view."""

    can_export = True
    column_searchable_list = ("name", "tuakiri_name", "city", "first_name", "last_name", "email", )

    @action("invite", "Register Organisation",
            "Are you sure you want to register selected organisations?")
    def action_invite(self, ids):
        """Batch registraion of organisatons."""
        count = 0
        for oi in OrgInfo.select(OrgInfo.name, OrgInfo.email).where(OrgInfo.id.in_(ids)):
            try:
                register_org(oi.name, oi.email)
                count += 1
            except Exception as ex:
                flash("Failed to send an invitation to %s: %s" % (oi.email, ex))
                app.logger.error("Exception Occured: %r", str(ex))

        flash("%d invitations were sent successfully." % count)


class OrcidTokenAdmin(AppModelView):
    """ORCID token model view."""

    column_labels = dict(org="Organisation")
    column_searchable_list = ("org.name", )
    can_export = True
    can_create = False


class OrcidApiCallAmin(AppModelView):
    """ORCID API calls."""

    can_export = True
    can_edit = False
    can_delete = False
    can_create = False
    column_searchable_list = ("url", "body", "response", "user.name", )


admin.add_view(UserAdmin(User))
admin.add_view(OrganisationAdmin(Organisation))
admin.add_view(OrcidTokenAdmin(OrcidToken))
admin.add_view(OrgInfoAdmin(OrgInfo))
admin.add_view(OrcidApiCallAmin(OrcidApiCall))

SectionRecord = namedtuple("SectionRecord", [
    "name", "city", "state", "country", "department", "role", "start_date", "end_date"
])
SectionRecord.__new__.__defaults__ = (None, ) * len(SectionRecord._fields)


@app.template_filter("year_range")
def year_range(entry):
    """Show an interval of employment in years."""
    val = ""
    if entry.get("start_date") is None or entry["start_date"]["year"]["value"] is None:
        val = "unknown"
    else:
        val = entry["start_date"]["year"]["value"]

    val += "-"

    if entry.get("end_date") is None or entry["end_date"]["year"]["value"] is None:
        val += "present"
    else:
        val += entry["end_date"]["year"]["value"]
    return val


@app.template_filter("orcid")
def user_orcid_id_url(user):
    """Render user ORCID Id URL."""
    return ORCID_BASE_URL + user.orcid if user.orcid else ""


@app.route("/<int:user_id>/emp/<int:put_code>/delete", methods=["POST"])
@roles_required(Role.ADMIN)
def delete_employment(user_id, put_code=None):
    """Delete an employment record."""
    _url = request.args.get("url") or request.referrer or url_for(
        "employment_list", user_id=user_id)
    if put_code is None and "put_code" in request.form:
        put_code = request.form.get("put_code")
    try:
        user = User.get(id=user_id, organisation_id=current_user.organisation_id)
    except:
        flash("ORCID HUB doent have data related to this researcher", "warning")
        return redirect(url_for("viewmembers"))
    if not user.orcid:
        flash("The user hasn't yet linked their ORCID record", "danger")
        return redirect(_url)

    orcid_token = None

    try:
        orcid_token = OrcidToken.get(
            user=user,
            org=user.organisation,
            scope=SCOPE_READ_LIMITED[0] + "," + SCOPE_ACTIVITIES_UPDATE[0])
    except:
        flash("The user hasn't authorized you to delete records", "warning")
        return redirect(_url)

    orcid_client.configuration.access_token = orcid_token.access_token
    api_instance = orcid_client.MemberAPIV20Api()

    try:
        # Delete an Employment
        api_instance.delete_employment(user.orcid, put_code)
        app.logger.info("For %r employment record was deleted by %r", user.orcid, current_user)
        flash("Employment record successfully deleted.", "success")
    except ApiException as e:
        message = json.loads(e.body.replace("''", "\"")).get('user-messsage')
        flash("Failed to delete the entry: %s" % message, "danger")
    except Exception as ex:
        app.logger.error("For %r encountered exception: %r", user, ex)
        abort(500, ex)
    return redirect(_url)


@app.route("/<int:user_id>/edu/<int:put_code>/edit", methods=["GET", "POST"])
@app.route("/<int:user_id>/edu/new", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def education(user_id, put_code=None):
    """Create a new or edit an existing employment record."""

    return edit_section_record(user_id, put_code, "EDU")


@app.route("/<int:user_id>/emp/<int:put_code>/edit", methods=["GET", "POST"])
@app.route("/<int:user_id>/emp/new", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def employment(user_id, put_code=None):
    """Create a new or edit an existing employment record."""

    return edit_section_record(user_id, put_code, "EMP")


def edit_section_record(user_id, put_code=None, section_type="EMP"):
    """Create a new or edit an existing profile section record."""

    section_type = section_type.upper()[:3]
    _url = (request.args.get("url") or url_for("employment_list", user_id=user_id)
            if section_type == "EMP" else url_for("edu_list", user_id=user_id))

    org = current_user.organisation
    try:
        # TODO: multiple orginisation support
        user = User.get(id=user_id, organisation=org.id)
    except User.DoesNotExist:
        flash("ORCID HUB doent have data related to this researcher", "warning")
        return redirect(_url)

    if not user.orcid:
        flash("The user hasn't yet linked their ORCID record", "danger")
        return redirect(_url)

    orcid_token = None
    try:
        orcid_token = OrcidToken.get(
            user=user, org=org, scope=SCOPE_READ_LIMITED[0] + "," + SCOPE_ACTIVITIES_UPDATE[0])
    except:
        flash("The user hasn't authorized you to Add records", "warning")
        return redirect(_url)
    orcid_client.configuration.access_token = orcid_token.access_token
    api_instance = orcid_client.MemberAPIV20Api()

    # TODO: handle "new"...
    if put_code:
        try:
            # Fetch an Employment
            if section_type == "EMP":
                api_response = api_instance.view_employment(user.orcid, put_code)
            elif section_type == "EDU":
                api_response = api_instance.view_education(user.orcid, put_code)

            _data = api_response.to_dict()
            data = SectionRecord(
                name=_data.get("organization").get("name"),
                city=_data.get("organization").get("address").get("city", ""),
                state=_data.get("organization").get("address").get("region", ""),
                country=_data.get("organization").get("address").get("country", ""),
                department=_data.get("department_name", ""),
                role=_data.get("role_title", ""),
                start_date=PD.create(_data.get("start_date")),
                end_date=PD.create(_data.get("end_date")))
        except ApiException as e:
            message = json.loads(e.body.replace("''", "\"")).get('user-messsage')
            print("Exception when calling MemberAPIV20Api->view_employment: %s\n" % message)
        except Exception as ex:
            app.logger.error("For %r encountered exception: %r", user, ex)
            abort(500, ex)
    else:
        data = SectionRecord(name=org.name, city=org.city, country=org.country)

    form = RecordForm.create_form(request.form, obj=data, form_type=section_type)
    if not form.name.data:
        form.name.data = org.name
    if not form.country.data or form.country.data == "None":
        form.country.data = org.country

    if form.validate_on_submit():
        # TODO: Audit trail
        # TODO: If it"s guarantee that the record will be editited solely by a sigle token we can
        # cache the record in the local DB

        rec = orcid_client.Employment() if section_type == "EMP" else orcid_client.Education()
        rec.start_date = form.start_date.data.as_orcid_dict()
        rec.end_date = form.end_date.data.as_orcid_dict()
        rec.path = ""
        rec.department_name = form.department.data
        rec.role_title = form.role.data

        url = urlparse(ORCID_BASE_URL)
        source_clientid = orcid_client.SourceClientId(
            host=url.hostname,
            path=org.orcid_client_id,
            uri="http://" + url.hostname + "/client/" + org.orcid_client_id)
        rec.source = orcid_client.Source(
            source_orcid=None, source_client_id=source_clientid, source_name=org.name)

        organisation_address = orcid_client.OrganizationAddress(
            city=form.city.data, region=form.state.data, country=form.country.data)

        rec.organization = orcid_client.Organization(
            name=form.name.data, address=organisation_address, disambiguated_organization=None)

        if org.name != form.name.data:
            orcid_client.DisambiguatedOrganization(
                disambiguated_organization_identifier=org.name, disambiguation_source=org.name)
        try:
            if put_code:
                rec.put_code = int(put_code)
                if section_type == "EMP":
                    api_response = api_instance.update_employment(user.orcid, put_code, body=rec)
                    app.logger.info("For %r employment record updated by %r", user.orcid,
                                    current_user)
                else:
                    api_response = api_instance.update_education(user.orcid, put_code, body=rec)
                    app.logger.info("For %r education record updated by %r", user.orcid,
                                    current_user)
            else:
                if section_type == "EMP":
                    api_response = api_instance.create_employment(user.orcid, body=rec)
                    app.logger.info("For %r employment record created by %r", user.orcid,
                                    current_user)
                else:
                    api_response = api_instance.create_education(user.orcid, body=rec)
                    app.logger.info("For %r education record created by %r", user.orcid,
                                    current_user)

                flash("Record details has been added successfully!", "success")

            affiliation, _ = UserOrgAffiliation.get_or_create(
                user=user,
                organisation=org,
                put_code=put_code,
                department_name=form.department.data,
                department_city=form.city.data,
                role_title=form.role.data)

            form.populate_obj(affiliation)
            if put_code:
                affiliation.put_code = put_code
            else:
                pass
                # affiliation.path = resp.headers["Location"]
                # affiliation.put_code = int(resp.headers["Location"].rsplit("/", 1)[-1])
            affiliation.save()
            return redirect(_url)
        except ApiException as e:
            message = json.loads(e.body.replace("''", "\"")).get('user-messsage')
            flash("Failed to update the entry: %s." % message, "danger")
            app.logger.error("For %r Exception encountered: %r", user, e)
        except Exception as ex:
            app.logger.error("For %r encountered exception: %r", user, ex)
            abort(500, ex)

    return render_template(
        "employment.html" if section_type == "EMP" else "education.html", form=form, _url=_url)


@app.route("/<int:user_id>/emp/list")
@app.route("/<int:user_id>/emp")
@login_required
def employment_list(user_id):
    return show_record_section(user_id, "EMP")


@app.route("/<int:user_id>/edu/list")
@app.route("/<int:user_id>/edu")
@login_required
def edu_list(user_id):
    return show_record_section(user_id, "EDU")


def show_record_section(user_id, section_type="EMP"):
    """Show all user profile section list."""

    section_type = section_type.upper()[:3]  # normalize the section type
    try:
        user = User.get(id=user_id, organisation_id=current_user.organisation_id)
    except:
        flash("ORCID HUB doent have data related to this researcher", "warning")
        return redirect(url_for("viewmembers"))

    if not user.orcid:
        flash("The user hasn't yet linked their ORCID record", "danger")
        return redirect(url_for("viewmembers"))

    orcid_token = None
    try:
        orcid_token = OrcidToken.get(user=user, org=current_user.organisation)
    except:
        flash("User didn't give permissions to update his/her records", "warning")
        return redirect(url_for("viewmembers"))

    orcid_client.configuration.access_token = orcid_token.access_token
    # create an instance of the API class
    api_instance = orcid_client.MemberAPIV20Api()
    try:
        # Fetch all entries
        if section_type == "EMP":
            api_response = api_instance.view_employments(user.orcid)
        elif section_type == "EDU":
            api_response = api_instance.view_educations(user.orcid)
    except ApiException as ex:
        message = json.loads(ex.body.replace("''", "\"")).get('user-messsage')
        flash("Exception when calling MemberAPIV20Api->view_employments: %s\n" % message, "danger")
        return redirect(url_for("viewmembers"))
    except Exception as ex:
        app.logger.error("For %r encountered exception: %r", user, ex)
        abort(500, ex)

    # TODO: Organisation has read token
    # TODO: Organisation has access to the employment records
    # TODO: retrieve and tranform for presentation (order, etc)
    try:
        data = api_response.to_dict()
    except Exception as ex:
        flash("User didn't give permissions to update his/her records", "warning")
        flash("Unhandled exception occured while retrieving ORCID data: %s" % ex, "danger")
        app.logger.error("For %r encountered exception: %r", user, ex)
        return redirect(url_for("viewmembers"))
    # TODO: transform data for presentation:
    if section_type == "EMP":
        return render_template(
            "employments.html",
            data=data,
            user_id=user_id,
            org_client_id=user.organisation.orcid_client_id)
    elif section_type == "EDU":
        return render_template(
            "educations.html",
            data=data,
            user_id=user_id,
            org_client_id=user.organisation.orcid_client_id)


@app.route("/load/org", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER)
def load_org():
    """Preload organisation data."""

    form = FileUploadForm()
    if form.validate_on_submit():
        data = request.files[form.org_info.name].read().decode("utf-8")
        row_count = OrgInfo.load_from_csv(data)

        flash("Successfully loaded %d rows." % row_count, "success")
        return redirect(url_for("orginfo.index_view"))

    return render_template("fileUpload.html", form=form, form_title="Organisation")


@app.route("/load/researcher", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_researcher_info():
    """Preload organisation data."""

    form = FileUploadForm()
    if form.validate_on_submit():
        data = request.files[form.org_info.name].read().decode("utf-8")
        users = User.load_from_csv(data)

        flash("Successfully loaded %d rows." % len(users), "success")
        try:
            for u in users.keys():
                user = users[u]
                with app.app_context():
                    email_and_organisation = user.email + ";" + user.organisation.name
                    token = generate_confirmation_token(email_and_organisation)
                    utils.send_email(
                        "email/researcher_invitation.html",
                        recipient=(user.organisation.name, user.email),
                        cc_email=None,
                        token=token,
                        org_name=user.organisation.name,
                        user=user)
        except Exception as ex:
            flash("Exception occured while sending mails %r" % str(ex), "danger")

        return redirect(url_for("viewmembers"))

    return render_template("fileUpload.html", form=form, form_title="Researcher")


@app.route("/orcid_api_rep", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER)
def orcid_api_rep():
    """Show ORCID API invocation report."""

    data = db.execute_sql("""
    WITH rd AS (
        SELECT date_trunc("minute", call_datetime) AS d, count(*) AS c
        FROM orcid_api_call
        GROUP BY date_trunc("minute", call_datetime))
    SELECT date_trunc("day", d) AS d, max(c) AS c
    FROM rd GROUP BY DATE_TRUNC("day", d) ORDER BY 1
    """).fetchall()

    return render_template("orcid_api_call_report.html", data=data)


def register_org(org_name, email, tech_contact=True):
    """Register research organisaion."""

    email = email.lower()
    try:
        User.get(User.email == email)
    except User.DoesNotExist:
        pass
    finally:
        try:
            org = Organisation.get(name=org_name)
        except Organisation.DoesNotExist:
            org = Organisation(name=org_name)

        try:
            org_info = OrgInfo.get(name=org.name)
        except OrgInfo.DoesNotExist:
            pass
        else:
            org.tuakiri_name = org_info.tuakiri_name

        try:
            org.save()
        except Exception as ex:
            app.logger.error("Encountered exception: %r", ex)
            raise Exception("Failed to save organisation data: %s" % str(ex), ex)

        try:
            user = User.get(email=email)
            user.roles |= Role.ADMIN
            user.organisation = org
            user.confirmed = True
        except User.DoesNotExist:
            user = User.create(
                email=email,
                confirmed=True,  # In order to let the user in...
                roles=Role.ADMIN,
                organisation=org)
        try:
            user.save()
        except Exception as ex:
            app.logger.error("Encountered exception: %r", ex)
            raise Exception("Failed to save user data: %s" % str(ex), ex)

        if tech_contact:
            user.roles |= Role.TECHNICAL
            org.tech_contact = user
            try:
                user.save()
                org.save()
            except Exception as ex:
                app.logger.error("Encountered exception: %r", ex)
                raise Exception(
                    "Failed to assign the user as the technical contact to the organisation: %s" %
                    str(ex), ex)

        user_org, _ = UserOrg.get_or_create(user=user, org=org)
        user_org.is_admin = True
        try:
            user_org.save()
        except Exception as ex:
            app.logger.error("Encountered exception: %r", ex)
            raise Exception(
                "Failed to assign the user as an administrator to the organisation: %s" % str(ex),
                ex)

        # Note: Using app context due to issue:
        # https://github.com/mattupstate/flask-mail/issues/63
        with app.app_context():
            app.logger.info(f"Ready to send an ivitation to '{org_name} <{email}>.")
            token = generate_confirmation_token(email)
            utils.send_email(
                "email/org_invitation.html",
                recipient=(org_name, email),
                reply_to=(current_user.name, current_user.email),
                cc_email=(current_user.name, current_user.email),
                token=token,
                org_name=org_name,
                user=user)

        OrgInvitation.create(
            inviter_id=current_user.id, invitee_id=user.id, email=user.email, org=org, token=token)


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
            try:
                register_org(form.orgName.data,
                             form.orgEmailid.data.lower(), request.form.get("tech_contact"))
                flash("Organisation Invited Successfully! "
                      "An email has been sent to the organisation contact", "success")
                app.logger.info(
                    "Organisation '%s' successfully invited. Invitation sent to '%s'." %
                    (form.orgName.data, form.orgEmailid.data))
            except Exception as ex:
                app.logger.error("Encountered exception: %r", ex)
                flash(str(ex), "danger")

    return render_template(
        "registration.html",
        form=form,
        org_info={r.name: r.email
                  for r in OrgInfo.select(OrgInfo.name, OrgInfo.email)})


@app.route("/invite/user", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER, Role.ADMIN)
def invite_user():
    """Invite a researcher to join the hub."""
    form = UserInvitationForm()
    if request.method == "GET":
        org = current_user.organisation
        form.organisation.data = org.name
        form.disambiguation_org_id.data = org.disambiguation_org_id
        form.disambiguation_org_source.data = org.disambiguation_org_source
        form.city.data = org.city
        form.state.data = org.state
        form.country.data = org.country

    if form.validate_on_submit():
        pass  # TODO: handle a single inviation:
        # 1. create token;
        # 2. save the invitation parametes into DB (UserInvitaiton);
        # 3. dispatch invitation email;
    return render_template("user_invitation.html", form=form)
