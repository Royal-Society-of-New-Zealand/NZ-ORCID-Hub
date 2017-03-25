# -*- coding: utf-8 -*-

"""Application views."""

# NB! Should be disabled in production
from pyinfo import info
from flask import render_template, redirect, url_for, request, flash
from application import app, admin
from flask_admin.contrib.peewee import ModelView
from models import User, Organisation, Role
from flask_login import login_required, current_user
from forms import EmploymentForm
import json
from config import ORCID_API_BASE

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

@app.route("/emp/<int:user_id>/<string:put_code>")
@app.route("/emp/<int:user_id>")
@login_required
def employment(user_id, put_code=None):
    form = EmploymentForm(request.form)
    if request.method == "POST" and form.validate():
        # TODO: Update ORCID
        # TODO: Redirect to the list
        pass
    return render_template("employment.html", form=form)


@app.route("/emp/<int:user_id>/list")
@login_required
def employment_list(user_id):

    u = User.get(id=user_id)
    if not u.orcid:
        flash("The user does't have ORDID", "error")

    # TODO: Organisation has read token
    # TODO: Organisation has access to the employment records

    # TODO: retrieve and tranform for presentation (order, etc)
    ###resp = requests.get(ORCID_API_BASE + u.orcid + "/employments", headers=HEADERS)
    ####data = resp.json()
    data == json.loads("""
{
  "last-modified-date": {
    "value": 1490330451228
  },
  "employment-summary": [
    {
      "created-date": {
        "value": 1490330451228
      },
      "last-modified-date": {
        "value": 1490330451228
      },
      "source": {
        "source-orcid": {
          "uri": "http://sandbox.orcid.org/0000-0002-1506-212X",
          "path": "0000-0002-1506-212X",
          "host": "sandbox.orcid.org"
        },
        "source-client-id": null,
        "source-name": {
          "value": "Radomirs Ciskis"
        }
      },
      "department-name": null,
      "role-title": null,
      "start-date": {
        "year": {
          "value": "2005"
        },
        "month": null,
        "day": null
      },
      "end-date": {
        "year": {
          "value": "2010"
        },
        "month": null,
        "day": null
      },
      "organization": {
        "name": "Test Education Ltd",
        "address": {
          "city": "Glasgow",
          "region": "Glasgow",
          "country": "GB"
        },
        "disambiguated-organization": {
          "disambiguated-organization-identifier": "368505",
          "disambiguation-source": "RINGGOLD"
        }
      },
      "visibility": "PUBLIC",
      "put-code": 26093,
      "path": "/0000-0002-1506-212X/employment/26093"
    },
    {
      "created-date": {
        "value": 1490330415438
      },
      "last-modified-date": {
        "value": 1490330415438
      },
      "source": {
        "source-orcid": {
          "uri": "http://sandbox.orcid.org/0000-0002-1506-212X",
          "path": "0000-0002-1506-212X",
          "host": "sandbox.orcid.org"
        },
        "source-client-id": null,
        "source-name": {
          "value": "Radomirs Ciskis"
        }
      },
      "department-name": null,
      "role-title": null,
      "start-date": {
        "year": {
          "value": "2004"
        },
        "month": null,
        "day": null
      },
      "end-date": null,
      "organization": {
        "name": "TEST 2",
        "address": {
          "city": "Riga",
          "region": null,
          "country": "LV"
        },
        "disambiguated-organization": null
      },
      "visibility": "PUBLIC",
      "put-code": 26092,
      "path": "/0000-0002-1506-212X/employment/26092"
    },
    {
      "created-date": {
        "value": 1488268354701
      },
      "last-modified-date": {
        "value": 1490330420719
      },
      "source": {
        "source-orcid": {
          "uri": "http://sandbox.orcid.org/0000-0002-1506-212X",
          "path": "0000-0002-1506-212X",
          "host": "sandbox.orcid.org"
        },
        "source-client-id": null,
        "source-name": {
          "value": "Radomirs Ciskis"
        }
      },
      "department-name": null,
      "role-title": null,
      "start-date": {
        "year": {
          "value": "2017"
        },
        "month": null,
        "day": null
      },
      "end-date": null,
      "organization": {
        "name": "the University of Auckland",
        "address": {
          "city": "Auckland",
          "region": null,
          "country": "NZ"
        },
        "disambiguated-organization": null
      },
      "visibility": "PUBLIC",
      "put-code": 25501,
      "path": "/0000-0002-1506-212X/employment/25501"
    }
  ],
  "path": "/0000-0002-1506-212X/employments"
}
""")
    # TODO: transform data for presentation:
    #for r in data["employment-summary"]:
    #    pass
    return render_template("employments.html", data=data)
