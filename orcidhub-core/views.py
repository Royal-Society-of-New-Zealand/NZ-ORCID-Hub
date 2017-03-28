# -*- coding: utf-8 -*-

"""Application views."""

# NB! Should be disabled in production
from pyinfo import info
from flask import render_template, redirect, url_for, request, flash
from application import app, admin
from flask_admin.contrib.peewee import ModelView
from models import User, Organisation, Role, OrcidToken, User_Organisation_affiliation, PartialDate as PD
from flask_login import login_required, current_user
from forms import EmploymentForm
from config import ORCID_API_BASE, scope_activities_update, scope_read_limited
import requests
from collections import namedtuple
import time
from requests_oauthlib import OAuth2Session

@app.route('/pyinfo')
@login_required
def pyinfo():
    """Show Python and runtime environment and settings."""
    return render_template('pyinfo.html', **info)


class AppModelView(ModelView):
    """ModelView customization."""

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role(Role.SUPERUSER):
            return True

        return False

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))


admin.add_view(AppModelView(User))
admin.add_view(AppModelView(Organisation))

HEADERS = {"Authorization": "Bearer fc38a9f5-85c2-4003-9e60-2c215b90f2a1", "Accept": "application/json"}
EmpRecord = namedtuple(
    "EmpRecord",
    ["employer", "city", "state", "country", "department", "role", "start_date", "end_date"])


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


@app.route("/<int:user_id>/emp/<string:put_code>/edit", methods=["GET", "POST"])
@app.route("/<int:user_id>/emp/new", methods=["GET", "POST"])
@login_required
def employment(user_id, put_code=None):
    user = User.get(id=user_id)
    if not user.orcid:
        flash("The user does't have ORDID", "error")

    orcidToken = None

    try:
        orcidToken = OrcidToken.get(user=user, org=user.organisation, scope=scope_activities_update)
    except:
        flash("The user hasn't authorized you to Add records", "warning")
        return redirect(_url)
    client = OAuth2Session(user.organisation.orcid_client_id, token={"access_token": orcidToken.access_token})
    headers = {'Accept': 'application/vnd.orcid+json', 'Content-type': 'application/vnd.orcid+json'}

    # TODO: handle "new"...
    if put_code is not None:
        resp = client.get(ORCID_API_BASE + user.orcid + "/employment/" + put_code, headers=headers)
        _data = resp.json()

        data = EmpRecord(
            employer=_data.get("organization").get("name"),
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
    if request.method == "POST" and form.validate():
        _url = request.args.get('url') or url_for("employment_list", user_id=user_id)
        # TODO: Update ORCID
        # TODO: Redirect to the list
        # TODO: Audit trail
        # TODO: Utilise generted client code
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
                "name": form.employer.data,
                "address": {
                    "city": form.city.data,
                    "region": form.state.data,
                    "country": form.country.data
                }
            },
            "role-title": form.role.data
        }
        resp = client.post('https://api.sandbox.orcid.org/v2.0/' + user.orcid + '/employment',
                           headers=headers, json=payload)
        if (resp.status_code == 200 or resp.status_code == 201):
            affiliation = User_Organisation_affiliation.create(
                user=user,
                organisation=user.organisation,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                department_name=form.department.data,
                department_city=form.city.data,
                role_title=form.role.data,
                put_code=int(resp.headers['Location'].rsplit('/', 1)[-1]),
                path=resp.headers['Location'])
            affiliation.save()
            flash("""Employment Details has been added successfully!!""", "success")
            return redirect(_url)
        else:
            flash([resp.json(), payload])
    return render_template("employment.html", form=form)


@app.route("/<int:user_id>/emp/list")
@app.route("/<int:user_id>/emp")
@login_required
def employment_list(user_id):

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

    headers = {'Accept': 'application/vnd.orcid+json'}
    resp = client.get('https://api.sandbox.orcid.org/v2.0/' + user.orcid + '/employments', headers=headers)
    # TODO: Organisation has read token
    # TODO: Organisation has access to the employment records

    # TODO: retrieve and tranform for presentation (order, etc)
    ## resp = requests.get(ORCID_API_BASE + user.orcid + "/employments", headers=HEADERS)
    data = resp.json()
    # TODO: transform data for presentation:
    # for r in data["employment-summary"]:
    #    pass
    return render_template("employments.html", data=data, user_id=user_id)
