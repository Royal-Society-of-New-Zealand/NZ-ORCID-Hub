# -*- coding: utf-8 -*-

"""Application views."""

# NB! Should be disabled in production
from pyinfo import info
from flask import render_template, redirect, url_for, request, flash
from application import app, admin
from flask_admin.contrib.peewee import ModelView
from models import User, Organisation, Role, PartialDate as PD
from flask_login import login_required, current_user
from forms import EmploymentForm
from config import ORCID_API_BASE
import requests
from collections import namedtuple

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
    u = User.get(id=user_id)
    if not u.orcid:
        flash("The user does't have ORDID", "error")

    # TODO: handle "new"...
    resp = requests.get(ORCID_API_BASE + u.orcid + "/employment/" + put_code, headers=HEADERS)
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

    form = EmploymentForm(request.form, obj=data)
    if request.method == "POST" and form.validate():
        # TODO: Update ORCID
        # TODO: Redirect to the list
        # TODO: Audit trail
        pass
    return render_template("employment.html", form=form)


@app.route("/<int:user_id>/emp/list")
@app.route("/<int:user_id>/emp")
@login_required
def employment_list(user_id):

    u = User.get(id=user_id)
    if not u.orcid:
        flash("The user does't have ORDID", "error")

    # TODO: Organisation has read token
    # TODO: Organisation has access to the employment records

    # TODO: retrieve and tranform for presentation (order, etc)
    resp = requests.get(ORCID_API_BASE + u.orcid + "/employments", headers=HEADERS)
    data = resp.json()
    # TODO: transform data for presentation:
    # for r in data["employment-summary"]:
    #    pass
    return render_template("employments.html", data=data, user_id=user_id)
