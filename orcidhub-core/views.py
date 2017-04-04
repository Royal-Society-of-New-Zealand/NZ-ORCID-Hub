# -*- coding: utf-8 -*-

"""Application views."""

# NB! Should be disabled in production
from pyinfo import info
from flask import render_template, redirect, url_for, request, flash
from application import app, admin
from flask_admin.contrib.peewee import ModelView
from models import User, Organisation, Role, OrcidToken, User_Organisation_affiliation, PartialDate as PD
from flask_login import login_required, current_user
from login_provider import roles_required
from forms import EmploymentForm, BitmapMultipleValueField
from config import ORCID_API_BASE, scope_activities_update, scope_read_limited
from collections import namedtuple
import time
from requests_oauthlib import OAuth2Session

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
    column_exclude_list = ("password", "username",)
    column_formatters = dict(roles=lambda v, c, m, p: Role(m.roles).name)
    form_overrides = dict(roles=BitmapMultipleValueField)
    form_args = dict(
        roles=dict(
            choices=[
                (1, "Superuser"),
                (2, "Administratro"),
                (4, "Researcher"),
                (8, "Technical Contact"),
            ])
    )

    jax_refs = {
        "organisation": {
            "fields": (Organisation.name, "name")
        }
    }


admin.add_view(UserAdmin(User))
admin.add_view(AppModelView(Organisation))

EmpRecord = namedtuple(
    "EmpRecord",
    ["name", "city", "state", "country", "department", "role", "start_date", "end_date"])


@app.template_filter('emp_years')
def emp_years(entry):
    """Show an interval of employment in years."""
    val = ""
    if entry.get("start-date") is None or entry["start-date"]["year"]["value"] is None:
        val = "unknown"
    else:
        val = entry["start-date"]["year"]["value"]

    val += "-"

    if entry.get("end-date") is None or entry["end-date"]["year"]["value"] is None:
        val += "present"
    else:
        val += entry["end-date"]["year"]["value"]
    return val


@app.route("/<int:user_id>/emp/<int:put_code>/delete", methods=["POST"])
@roles_required(Role.ADMIN)
def delete_employment(user_id, put_code=None):
    """Delete an employment record."""
    _url = request.args.get('url') or request.referrer or url_for("employment_list", user_id=user_id)
    if put_code is None and "put_code" in request.form:
        put_code = request.form.get("put_code")
    user = User.get(id=user_id)
    if not user.orcid:
        flash("The user does't have ORDID", "error")
        return redirect(_url)

    orcidToken = None

    try:
        orcidToken = OrcidToken.get(user=user, org=user.organisation, scope=scope_activities_update)
    except:
        flash("The user hasn't authorized you to Add records", "warning")
        return redirect(_url)
    client = OAuth2Session(user.organisation.orcid_client_id, token={"access_token": orcidToken.access_token})
    url = ORCID_API_BASE + user.orcid + "/employment/%d" % put_code
    resp = client.delete(url, headers=HEADERS)
    if resp.status_code == 204:
        flash("Employment record successfully deleted.", "success")
    else:
        message = resp.json().get("user-message") or resp.state
        flash("Failed to delete the entry: %s" % message, "danger")
    return redirect(_url)


@app.route("/<int:user_id>/emp/<int:put_code>/edit", methods=["GET", "POST"])
@app.route("/<int:user_id>/emp/new", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def employment(user_id, put_code=None):
    """Create a new or edit an existing employment record."""
    _url = request.args.get('url') or url_for("employment_list", user_id=user_id)
    user = User.get(id=user_id)
    if not user.orcid:
        flash("The user does't have ORDID", "error")
        return redirect(_url)

    orcidToken = None

    try:
        orcidToken = OrcidToken.get(user=user, org=user.organisation, scope=scope_activities_update)
    except:
        flash("The user hasn't authorized you to Add records", "warning")
        return redirect(_url)
    client = OAuth2Session(user.organisation.orcid_client_id, token={"access_token": orcidToken.access_token})

    # TODO: handle "new"...
    if put_code is not None:
        resp = client.get(ORCID_API_BASE + user.orcid + "/employment/%d" % put_code, headers=HEADERS)
        _data = resp.json()

        data = EmpRecord(
            name=_data.get("organization").get("name"),
            city=_data.get("organization").get("address").get("city", ""),
            state=_data.get("organization").get("address").get("region", ""),
            country=_data.get("organization").get("address").get("country", ""),
            department=_data.get("department-name", ""),
            role=_data.get("role-title", ""),
            start_date=PD.create(_data.get("start-date")),
            end_date=PD.create(_data.get("end-date")))
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
        payload = {
            "department-name": form.department.data,
            "start-date": form.start_date.data.as_orcid_dict(),
            "end-date": form.end_date.data.as_orcid_dict(),
            "last-modified-date": {
                "value": int(time.time())
            },
            "created-date": {
                "value": int(time.time())
            },
            "visibility": "PUBLIC",
            "source": {
                "source-orcid": None,
                "source-name": {
                    "value": current_user.organisation.name,
                },
                "source-client-id": {
                    "path": current_user.organisation.orcid_client_id,
                    "host": "sandbox.orcid.org",
                    "uri": "http://sandbox.orcid.org/client/" + user.organisation.orcid_client_id,
                }
            },
            "path": "",
            "organization": {
                "disambiguated-organization": None,
                "name": form.name.data,
                "address": {
                    "city": form.city.data,
                    "region": form.state.data,
                    "country": form.country.data
                }
            },
            "role-title": form.role.data
        }
        if put_code:
            payload["put-code"] = put_code

        if current_user.organisation.name != form.name.data:
            payload["organization"]["disambiguated-organization"] = {
                "disambiguated-organization-identifier": current_user.organisation.name,
                "disambiguation-source": current_user.organisation.name
            }

        url = ORCID_API_BASE + user.orcid + "/employment"
        if put_code:
            url += "/%d" % put_code
        if put_code:
            resp = client.put(url, headers=HEADERS, json=payload)
        else:
            resp = client.post(url, headers=HEADERS, json=payload)
        if (resp.status_code == 200 or resp.status_code == 201):
            affiliation, _ = User_Organisation_affiliation.get_or_create(
                user=user, organisation=user.organisation, put_code=put_code)
            form.populate_obj(affiliation)
            if put_code:
                affiliation.put_code = put_code
            else:
                affiliation.path = resp.headers['Location']
                affiliation.put_code = int(resp.headers['Location'].rsplit('/', 1)[-1])
            affiliation.save()
            if put_code:
                flash("Employment Details has been updated successfully!", "success")
            else:
                flash("Employment Details has been added successfully!", "success")
            return redirect(_url)
        else:
            message = resp.json().get("user-message") or resp.state
            flash(
                "Failed to update the entry: %s. You don't have required permission to edit the record." %
                message, "danger")

    return render_template("employment.html", form=form, _url=_url)


@app.route("/<int:user_id>/emp/list")
@app.route("/<int:user_id>/emp")
@login_required
def employment_list(user_id):
    """Show all user employment list."""
    user = User.get(id=user_id)
    if not user.orcid:
        flash("The user does't have ORDID", "error")

    orcidToken = None
    try:
        orcidToken = OrcidToken.get(user=user, org=user.organisation, scope=scope_read_limited)
    except:
        flash("User didnt gave permission to update his/her records", "warning")
        return redirect(url_for("viewmembers"))

    client = OAuth2Session(user.organisation.orcid_client_id, token={"access_token": orcidToken.access_token})

    resp = client.get('https://api.sandbox.orcid.org/v2.0/' + user.orcid + '/employments', headers=HEADERS)
    # TODO: Organisation has read token
    # TODO: Organisation has access to the employment records
    # TODO: retrieve and tranform for presentation (order, etc)
    data = resp.json()
    # TODO: transform data for presentation:
    return render_template("employments.html", data=data, user_id=user_id)
