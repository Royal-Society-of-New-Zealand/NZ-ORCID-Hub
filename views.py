# -*- coding: utf-8 -*-
"""Application views."""

from collections import namedtuple

from flask import flash, redirect, render_template, request, url_for
from flask_admin.contrib.peewee import ModelView
from flask_login import current_user, login_required

import swagger_client
from application import admin, app
from config import SCOPE_ACTIVITIES_UPDATE
from forms import BitmapMultipleValueField, EmploymentForm
from login_provider import roles_required
from models import PartialDate as PD
from models import (OrcidToken, Organisation, Role, User, User_Organisation_affiliation)
# NB! Should be disabled in production
from pyinfo import info
from swagger_client.rest import ApiException
from requests_oauthlib import OAuth2Session
import json

HEADERS = {'Accept': 'application/vnd.orcid+json', 'Content-type': 'application/vnd.orcid+json'}


@app.route('/pyinfo')
@login_required
def pyinfo():
    """Show Python and runtime environment and settings."""
    return render_template('pyinfo.html', **info)


class AppModelView(ModelView):
    """ModelView customization."""

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
                           "edu_person_shared_token",)
    column_formatters = dict(
        roles=lambda v, c, m, p: ", ".join(n for r, n in v.roles.items() if r & m.roles),
        orcid=lambda v, c, m, p: m.orcid.replace('-', '\u2011') if m.orcid else '')
    form_overrides = dict(roles=BitmapMultipleValueField)
    form_args = dict(roles=dict(choices=roles.items()))

    jax_refs = {"organisation": {"fields": (Organisation.name, "name")}}


class OrganisationAdmin(AppModelView):
    """Organisation model view."""
    column_exclude_list = ("orcid_client_id", "orcid_secret", "tuakiri_name",)


admin.add_view(UserAdmin(User))
admin.add_view(OrganisationAdmin(Organisation))

EmpRecord = namedtuple("EmpRecord", [
    "name", "city", "state", "country", "department", "role", "start_date", "end_date"
])


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

    orcidToken = None

    try:
        orcidToken = OrcidToken.get(
            user=user, org=user.organisation, scope=SCOPE_ACTIVITIES_UPDATE)
    except:
        flash("The user hasn't authorized you to Add records", "warning")
        return redirect(_url)

    swagger_client.configuration.access_token = orcidToken.access_token
    api_instance = swagger_client.MemberAPIV20Api()

    try:
        # Delete an Employment
        api_instance.delete_employment(user.orcid, put_code)
        flash("Employment record successfully deleted.", "success")
    except ApiException as e:
        flash("Failed to delete the entry: %s" % e.body, "danger")
    return redirect(_url)


@app.route("/<int:user_id>/emp/<int:put_code>/edit", methods=["GET", "POST"])
@app.route("/<int:user_id>/emp/new", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def employment(user_id, put_code=None):
    """Create a new or edit an existing employment record."""
    _url = request.args.get('url') or url_for("employment_list", user_id=user_id)

    try:
        user = User.get(id=user_id, organisation_id=current_user.organisation_id)
    except:
        flash("ORCID HUB doent have data related to this researcher", "warning")
        return redirect(url_for("viewmembers"))

    if not user.orcid:
        flash("The user hasn't yet linked their ORCID record", "danger")
        return redirect(_url)

    orcidToken = None

    try:
        orcidToken = OrcidToken.get(
            user=user, org=user.organisation, scope=SCOPE_ACTIVITIES_UPDATE)
    except:
        flash("The user hasn't authorized you to Add records", "warning")
        return redirect(_url)
    swagger_client.configuration.access_token = orcidToken.access_token
    api_instance = swagger_client.MemberAPIV20Api()

    # TODO: handle "new"...
    if put_code is not None:
        try:
            # Fetch an Employment
            api_response = api_instance.view_employment(user.orcid, put_code)
            _data = api_response.to_dict()
            data = EmpRecord(
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
        data = None

    form = EmploymentForm(request.form, obj=data)
    # TODO: prefill the form from the organisation data
    if not form.name.data:
        form.name.data = current_user.organisation.name
    if not form.country.data or form.country.data == "None":
        form.country.data = current_user.organisation.country

    if request.method == "POST" and form.validate():
        # TODO: Audit trail
        # TODO: Utilise generted client code
        # TODO: If it's guarantee that the record will be editited solely by a sigle token we can
        # cache the record in the local DB

        employment = swagger_client.Employment(
            start_date=form.start_date.data.as_orcid_dict(),
            end_date=form.end_date.data.as_orcid_dict(),
            path="",
            department_name=form.department.data,
            role_title=form.role.data)

        source_clientid = swagger_client.SourceClientId(
            host='sandbox.orcid.org',
            path=current_user.organisation.orcid_client_id,
            uri="http://sandbox.orcid.org/client/" + user.organisation.orcid_client_id)
        employment.source = swagger_client.Source(
            source_orcid=None,
            source_client_id=source_clientid,
            source_name=current_user.organisation.name)

        organisation_address = swagger_client.OrganizationAddress(
            city=form.city.data, region=form.state.data, country=form.country.data)

        employment.organization = swagger_client.Organization(
            name=form.name.data, address=organisation_address, disambiguated_organization=None)

        if current_user.organisation.name != form.name.data:
            swagger_client.DisambiguatedOrganization(
                disambiguated_organization_identifier=current_user.organisation.name,
                disambiguation_source=current_user.organisation.name)
        try:
            if put_code:
                # TODO: We can uncomment the below swagger employment update call,
                # Once the bug fix (in update employment functionality) related to put code is done from ORCID side
                # api_instance.update_employment(user.orcid, put_code, body=employment)
                try:
                    client = OAuth2Session(user.organisation.orcid_client_id, token={
                        "access_token": swagger_client.configuration.access_token})

                    headers = {'Accept': 'application/vnd.orcid+json', 'Content-type': 'application/vnd.orcid+json'}
                    data = employment.to_dict()
                    data['put-code'] = int(put_code)
                    temp = json.dumps(data).replace('_', '-')
                    data = json.loads(temp)
                    resp = client.put(
                        url="https://api.sandbox.orcid.org/v2.0/" + user.orcid + "/employment/" + str(put_code),
                        json=data, headers=headers)
                    print(resp)
                except:
                    pass
            else:
                api_response = api_instance.create_employment(user.orcid, body=employment)

            affiliation, _ = User_Organisation_affiliation.get_or_create(
                user=user,
                organisation=user.organisation,
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
            if put_code:
                flash("Employment Details has been u" "pdated successfully!", "success")
            else:
                flash("Employment Details has been added successfully!", "success")
            return redirect(_url)
        except ApiException as e:
            # message = resp.json().get("user-message") or resp.state
            flash("Failed to update the entry: %s." % e.body, "danger")

    return render_template("employment.html", form=form, _url=_url)


@app.route("/<int:user_id>/emp/list")
@app.route("/<int:user_id>/emp")
@login_required
def employment_list(user_id):
    """Show all user employment list."""
    try:
        user = User.get(id=user_id, organisation_id=current_user.organisation_id)
    except:
        flash("ORCID HUB doent have data related to this researcher", "warning")
        return redirect(url_for("viewmembers"))

    if not user.orcid:
        flash("The user hasn't yet linked their ORCID record", "danger")
        return redirect(url_for("viewmembers"))

    orcidToken = None
    try:
        orcidToken = OrcidToken.get(
            user=user, org=user.organisation, scope=SCOPE_ACTIVITIES_UPDATE)
    except:
        flash("User didnt gave permission to update his/her records", "warning")
        return redirect(url_for("viewmembers"))

    swagger_client.configuration.access_token = orcidToken.access_token
    # create an instance of the API class
    api_instance = swagger_client.MemberAPIV20Api()
    try:
        # Fetch all employments
        api_response = api_instance.view_employments(user.orcid)
        print(api_response)
    except ApiException as e:
        print("Exception when calling MemberAPIV20Api->view_employments: %s\n" % e.body)

    # TODO: Organisation has read token
    # TODO: Organisation has access to the employment records
    # TODO: retrieve and tranform for presentation (order, etc)
    try:
        data = api_response.to_dict()
    except:
        flash("User didn't gave permission to update his/her records", "warning")
        return redirect(url_for("viewmembers"))
    # TODO: transform data for presentation:
    return render_template("employments.html", data=data, user_id=user_id)
