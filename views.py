# -*- coding: utf-8 -*-
"""Application views."""

import os
from collections import namedtuple

from flask import (flash, redirect, render_template, request, send_from_directory, url_for)
from flask_admin.contrib.peewee import ModelView
from flask_admin.form import SecureForm
from flask_login import current_user, login_required

import orcid_client
from application import admin, app
from config import ORCID_BASE_URL, SCOPE_ACTIVITIES_UPDATE
from forms import BitmapMultipleValueField, OrgInfoForm, RecordForm
from login_provider import roles_required
from models import PartialDate as PD, db
from models import (OrcidApiCall, OrcidToken, Organisation, OrgInfo, Role, User,
                    UserOrgAffiliation)
# NB! Should be disabled in production
from pyinfo import info
from swagger_client.rest import ApiException

HEADERS = {'Accept': 'application/vnd.orcid+json', 'Content-type': 'application/vnd.orcid+json'}


@app.route("/favicon.ico")
def favicon():
    """Support for the 'favicon' legacy: faveicon location in the root directory."""
    return send_from_directory(
        os.path.join(app.root_path, "static", "images"), "favicon.ico", mimetype="image/vnd.microsoft.icon")


@app.route('/pyinfo')
@login_required
def pyinfo():
    """Show Python and runtime environment and settings."""
    return render_template('pyinfo.html', **info)


@app.route('/about')
def about():
    """Show 'about' page."""
    return render_template("about.html")


class AppModelView(ModelView):
    """ModelView customization."""

    form_base_class = SecureForm

    def is_accessible(self):
        """Verify if the view is accessible for the current user."""
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role(Role.SUPERUSER):
            return True

        return False

    def inaccessible_callback(self, name, **kwargs):
        """Handle access denial. Redirect to login page if user doesn't have access."""
        return redirect(url_for('login', next=request.url))


class UserAdmin(AppModelView):
    """User model view."""
    roles = {1: "Superuser", 2: "Administrator", 4: "Researcher", 8: "Technical Contact"}

    column_exclude_list = ("password", "username", "first_name", "last_name",
                           "edu_person_shared_token", )
    column_formatters = dict(
        roles=lambda v, c, m, p: ", ".join(n for r, n in v.roles.items() if r & m.roles),
        orcid=lambda v, c, m, p: m.orcid.replace('-', '\u2011') if m.orcid else '')
    column_filters = ("name", )
    form_overrides = dict(roles=BitmapMultipleValueField)
    form_args = dict(roles=dict(choices=roles.items()))

    form_ajax_refs = {"organisation": {"fields": (Organisation.name, "name")}}
    can_export = True


class OrganisationAdmin(AppModelView):
    """Organisation model view."""
    column_exclude_list = ("orcid_client_id", "orcid_secret", )
    column_filters = ("name", )


class OrgInfoAdmin(AppModelView):
    """OrgInfo model view."""

    can_export = True
    column_filters = ("name", )


class OrcidTokenAdmin(AppModelView):
    """ORCID token model view."""

    can_export = True
    can_create = False


class OrcidApiCallAmin(AppModelView):
    """ORCID API calls."""

    can_export = True
    can_edit = False
    can_delete = False
    can_create = False
    column_filters = ("url", )


admin.add_view(UserAdmin(User))
admin.add_view(OrganisationAdmin(Organisation))
admin.add_view(OrcidTokenAdmin(OrcidToken))
admin.add_view(OrgInfoAdmin(OrgInfo))
admin.add_view(OrcidApiCallAmin(OrcidApiCall))

SectionRecord = namedtuple("SectionRecord", [
    "name", "city", "state", "country", "department", "role", "start_date", "end_date"
])
SectionRecord.__new__.__defaults__ = (None, ) * len(SectionRecord._fields)


@app.template_filter('year_range')
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


@app.template_filter('orcid')
def user_orcid_id_url(user):
    """Render user ORCID Id URL."""
    return ORCID_BASE_URL + user.orcid if user.orcid else ''


@app.route("/<int:user_id>/emp/<int:put_code>/delete", methods=["POST"])
@roles_required(Role.ADMIN)
def delete_employment(user_id, put_code=None):
    """Delete an employment record."""
    _url = request.args.get('url') or request.referrer or url_for(
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
            user=user, org=user.organisation, scope=SCOPE_ACTIVITIES_UPDATE)
    except:
        flash("The user hasn't authorized you to delete records", "warning")
        return redirect(_url)

    orcid_client.configuration.access_token = orcid_token.access_token
    api_instance = orcid_client.MemberAPIV20Api()

    try:
        # Delete an Employment
        api_instance.delete_employment(user.orcid, put_code)
        flash("Employment record successfully deleted.", "success")
    except ApiException as e:
        flash("Failed to delete the entry: %s" % e.body, "danger")
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
    _url = (request.args.get('url') or url_for("employment_list", user_id=user_id)
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
        orcid_token = OrcidToken.get(user=user, org=org, scope=SCOPE_ACTIVITIES_UPDATE)
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
            print("Exception when calling MemberAPIV20Api->view_employment: %s\n" % e.body)
    else:
        data = SectionRecord(name=org.name, city=org.city, country=org.country)

    form = RecordForm.create_form(request.form, obj=data, form_type=section_type)
    if not form.name.data:
        form.name.data = org.name
    if not form.country.data or form.country.data == "None":
        form.country.data = org.country

    if form.validate_on_submit():
        # TODO: Audit trail
        # TODO: If it's guarantee that the record will be editited solely by a sigle token we can
        # cache the record in the local DB

        rec = orcid_client.Employment() if section_type == "EMP" else orcid_client.Education()
        rec.start_date = form.start_date.data.as_orcid_dict()
        rec.end_date = form.end_date.data.as_orcid_dict()
        rec.path = ""
        rec.department_name = form.department.data
        rec.role_title = form.role.data

        # TODO: adjust literals to the environment
        source_clientid = orcid_client.SourceClientId(
            host='sandbox.orcid.org',
            path=org.orcid_client_id,
            uri="http://sandbox.orcid.org/client/" + org.orcid_client_id)
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
                else:
                    api_response = api_instance.update_education(user.orcid, put_code, body=rec)
            else:
                if section_type == "EMP":
                    api_response = api_instance.create_employment(user.orcid, body=rec)
                else:
                    api_response = api_instance.create_education(user.orcid, body=rec)

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
                # affiliation.path = resp.headers['Location']
                # affiliation.put_code = int(resp.headers['Location'].rsplit('/', 1)[-1])
            affiliation.save()
            return redirect(_url)
        except ApiException as e:
            # message = resp.json().get("user-message") or resp.state
            flash("Failed to update the entry: %s." % e.body, "danger")

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
        orcid_token = OrcidToken.get(
            user=user, org=current_user.organisation)
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
        flash("Exception when calling MemberAPIV20Api->view_employments: %s\n" % ex, "danger")
        return redirect(url_for("viewmembers"))

    # TODO: Organisation has read token
    # TODO: Organisation has access to the employment records
    # TODO: retrieve and tranform for presentation (order, etc)
    try:
        data = api_response.to_dict()
    except Exception as ex:
        flash("User didn't give permissions to update his/her records", "warning")
        flash("Unhandled exception occured while retrieving ORCID data: %s" % ex, "danger")
        return redirect(url_for("viewmembers"))
    # TODO: transform data for presentation:
    if section_type == "EMP":
        return render_template("employments.html", data=data, user_id=user_id)
    elif section_type == "EDU":
        return render_template("educations.html", data=data, user_id=user_id)


@app.route("/load/org", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER)
def load_org():
    """Preload organisation data."""

    form = OrgInfoForm()
    if form.validate_on_submit():
        data = request.files[form.org_info.name].read().decode("utf-8")
        row_count = OrgInfo.load_from_csv(data)

        flash("Successfully loaded %d rows." % row_count, "success")
        return redirect(url_for("orginfo.index_view"))

    return render_template("orginfo.html", form=form)


@app.route("/orcid_api_rep", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER)
def orcid_api_rep():
    """Show ORCID API invocation report."""

    data = db.execute_sql("""
    WITH rd AS (
        SELECT date_trunc('minute', call_datetime) AS d, count(*) AS c
        FROM orcid_api_call
        GROUP BY date_trunc('minute', call_datetime))
    SELECT date_trunc('day', d) AS d, max(c) AS c
    FROM rd GROUP BY DATE_TRUNC('day', d) ORDER BY 1
    """).fetchall()

    return render_template("orcid_api_call_report.html", data=data)
