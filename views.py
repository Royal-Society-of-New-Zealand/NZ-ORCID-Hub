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
from werkzeug import secure_filename

import orcid_client
import utils
from application import admin, app
from config import ORCID_BASE_URL, SCOPE_ACTIVITIES_UPDATE, SCOPE_READ_LIMITED
from forms import (BitmapMultipleValueField, FileUploadForm, OrgRegistrationForm, PartialDateField,
                   RecordForm, UserInvitationForm)
from login_provider import roles_required
from models import PartialDate as PD
from models import AffiliationRecord  # noqa: F401
from models import (Affiliation, CharField, OrcidApiCall, OrcidToken, Organisation, OrgInfo,
                    OrgInvitation, Role, Task, TextField, Url, User, UserInvitation, UserOrg,
                    UserOrgAffiliation, db)
# NB! Should be disabled in production
from pyinfo import info
from swagger_client.rest import ApiException
from utils import generate_confirmation_token, send_user_initation

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


@app.route("/u/<short_id>")
def short_url(short_id):
    try:
        u = Url.get(short_id=short_id)
        if request.args:
            return redirect(utils.append_qs(u.url, **request.args))
        return redirect(u.url)
    except Url.DoesNotExist:
        abort(404)


class AppModelView(ModelView):
    """ModelView customization."""

    roles_required = Role.SUPERUSER
    export_types = [
        "csv",
        "xls",
        "tsv",
        "yaml",
        "json",
        "xlsx",
        "ods",
        "html",
    ]
    form_base_class = SecureForm
    column_type_formatters = dict(typefmt.BASE_FORMATTERS)
    column_type_formatters.update({
        datetime:
        lambda view, value: Markup(value.strftime("%Y‑%m‑%d&nbsp;%H:%M")),
    })
    column_exclude_list = ("created_at", "updated_at", "created_by", "updated_by", )
    form_overrides = dict(start_date=PartialDateField, end_date=PartialDateField)

    def __init__(self, model=None, *args, **kwargs):
        """Picks the model based on the ModelView class name assuming it is ModelClass + "Admin"."""
        if model is None:
            if hasattr(self, "model"):
                model = self.model
            else:
                model_class_name = self.__class__.__name__.replace("Admin", '')
                model = globals().get(model_class_name)
            if model is None:
                raise Exception(f"Model class {model_class_name} doesn't exit.")
        super().__init__(model, *args, **kwargs)

    def get_pk_value(self, model):
        """Fix for composite keys."""
        if self.model._meta.composite_key:
            return tuple([
                model._data[field_name] for field_name in self.model._meta.primary_key.field_names
            ])
        return super().get_pk_value(model)

    def get_one(self, id):
        """Fix for composite keys."""
        if self.model._meta.composite_key:
            return self.model.get(**dict(zip(self.model._meta.primary_key.field_names, id)))
        return super().get_one(id)

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

        if current_user.has_role(self.roles_required):
            return True

        return False

    def inaccessible_callback(self, name, **kwargs):
        """Handle access denial. Redirect to login page if user doesn"t have access."""
        return redirect(url_for("login", next=request.url))

    def get_query(self):
        """Add URL query to the data select for foreign key and select data
        that user has access to."""
        query = super().get_query()

        if current_user and not current_user.has_role(Role.SUPERUSER) and current_user.has_role(
                Role.ADMIN):
            # Show only rows realted to the organisation the user is admin for.
            # Skip this part for SUPERUSER.
            db_columns = [c.db_column for c in self.model._meta.fields.values()]
            if "org_id" in db_columns or "organisation_id" in db_columns:
                admin_for_org_ids = [o.id for o in current_user.admin_for.select(Organisation.id)]
                if "org_id" in db_columns:
                    query.where(self.model.org_id << admin_for_org_ids)
                else:
                    query.where(self.model.organisation_id << admin_for_org_ids)

        if request.args and any(a.endswith("_id") for a in request.args):
            for f in self.model._meta.fields.values():
                if f.db_column.endswith("_id") and f.db_column in request.args:
                    query = query.where(f == int(request.args[f.db_column]))
        return query

    def _get_list_extra_args(self):
        """Workaournd for https://github.com/flask-admin/flask-admin/issues/1512."""
        view_args = super()._get_list_extra_args()
        extra_args = {
            k: v
            for k, v in request.args.items()
            if k not in ('page', 'page_size', 'sort', 'desc',
                         'search', ) and not k.startswith('flt')
        }
        view_args.extra_args = extra_args
        return view_args


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

    def update_model(self, form, model):
        """Added prevalidation of the form."""
        if form.roles.data != model.roles:
            if bool(form.roles.data & Role.ADMIN) != UserOrg.select().where(
                (UserOrg.user_id == model.id) & UserOrg.is_admin).exists():  # noqa: E125
                if form.roles.data & Role.ADMIN:
                    flash(f"Cannot add ADMIN role to {model} "
                          "since there is no organisation the user is an administrator for.",
                          "danger")
                else:
                    flash(f"Cannot revoke ADMIN role from {model} "
                          "since there is an organisation the user is an administrator for.",
                          "danger")
                form.roles.data = model.roles
                return False
            if bool(form.roles.data & Role.TECHNICAL) != Organisation.select().where(
                    Organisation.tech_contact_id == model.id).exists():
                if model.has_role(Role.TECHNICAL):
                    flash(f"Cannot revoke TECHNICAL role from {model} "
                          "since there is an organisation the user is the technical contact for.",
                          "danger")
                else:
                    flash(f"Cannot add TECHNICAL role to {model} "
                          "since there is no organisation the user is the technical contact for.",
                          "danger")
                form.roles.data = model.roles
                return False

        return super().update_model(form, model)


class OrganisationAdmin(AppModelView):
    """Organisation model view."""
    column_exclude_list = ("orcid_client_id", "orcid_secret", "created_at")
    column_searchable_list = ("name", "tuakiri_name", "city", )

    def update_model(self, form, model):
        """Handle change of the technical contact."""
        # Technical contact changed:
        if form.tech_contact.data.id != model.tech_contact_id:
            # Revoke the TECHNICAL role if thre is no org the user is tech.contact for.
            if model.tech_contact and model.tech_contact.has_role(
                    Role.TECHNICAL) and not Organisation.select().where(
                        Organisation.tech_contact_id == model.tech_contact_id).exists():
                app.logger.info(r"Revoked TECHNICAL from {model.tech_contact}")
                model.tech_contact.roles &= ~Role.TECHNICAL
                super(User, model.tech_contact).save()

        return super().update_model(form, model)


class OrgInfoAdmin(AppModelView):
    """OrgInfo model view."""

    can_export = True
    column_searchable_list = ("name", "tuakiri_name", "city", "first_name", "last_name", "email", )

    @action("invite", "Register Organisation",
            "Are you sure you want to register selected organisations?")
    def action_invite(self, ids):
        """Batch registraion of organisatons."""
        count = 0
        for oi in OrgInfo.select().where(OrgInfo.id.in_(ids)):
            try:
                register_org(
                    email=oi.name,
                    tech_contact=True,
                    via_orcid=(False if oi.tuakiri_name else True),
                    first_name=oi.first_name,
                    last_name=oi.last_name,
                    city=oi.city,
                    country=oi.country,
                    course_or_role=oi.role,
                    disambiguation_org_id=oi.disambiguation_org_id,
                    disambiguation_org_source=oi.disambiguation_source)
                count += 1
            except Exception as ex:
                flash("Failed to send an invitation to %s: %s" % (oi.email, ex))
                app.logger.exception()

        flash("%d invitations were sent successfully." % count)


class OrcidTokenAdmin(AppModelView):
    """ORCID token model view."""

    column_labels = dict(org="Organisation")
    column_searchable_list = ("user.name", "user.email", "org.name", )
    can_export = True
    can_create = False


class OrcidApiCallAmin(AppModelView):
    """ORCID API calls."""

    can_export = True
    can_edit = False
    can_delete = False
    can_create = False
    column_searchable_list = ("url", "body", "response", "user.name", )


class UserOrgAmin(AppModelView):
    """User Organisations."""

    column_searchable_list = ("user.email", "org.name", )


class TaskAdmin(AppModelView):
    roles_required = Role.SUPERUSER | Role.ADMIN
    list_template = "view_tasks.html"
    can_edit = False
    can_create = False
    can_delete = True


class AffiliationRecordAdmin(AppModelView):
    roles_required = Role.SUPERUSER | Role.ADMIN
    list_template = "affiliation_record_list.html"
    column_exclude_list = ("task", "organisation", )
    column_searchable_list = ("first_name", "last_name", "identifier", "role", "department",
                              "state", )
    can_edit = True
    can_create = False
    can_delete = False
    can_view_details = True

    @action("activate", "Activate for processing",
            "Are you sure you want to activate the selected records for batch processing?")
    def action_activate(self, ids):
        """Batch registraion of users."""
        count = 0
        try:
            with db.atomic():
                for ar in self.model.select().where(self.model.id.in_(ids)):
                    if not ar.is_active:
                        ar.is_active = True
                        ar.save()
                        count += 1
        except Exception as ex:
            flash(f"Failed to activate the selected records: {ex}")
            app.logger.exception()

        flash(f"{count} records were activated for batch processing.")


class ViewMembersAdmin(AppModelView):
    roles_required = Role.SUPERUSER | Role.ADMIN
    list_template = "viewMembers.html"
    column_list = ("email", "orcid")
    column_searchable_list = ("email", "orcid")
    column_export_list = ("email", "eppn", "orcid")
    model = User
    can_edit = False
    can_create = False
    can_delete = False
    can_view_details = False
    can_export = True

    def get_query(self):
        return current_user.organisation.users


admin.add_view(UserAdmin(User))
admin.add_view(OrganisationAdmin(Organisation))
admin.add_view(OrcidTokenAdmin(OrcidToken))
admin.add_view(OrgInfoAdmin(OrgInfo))
admin.add_view(OrcidApiCallAmin(OrcidApiCall))
admin.add_view(TaskAdmin(Task))
admin.add_view(AffiliationRecordAdmin())
admin.add_view(AppModelView(UserInvitation))
admin.add_view(ViewMembersAdmin(name="viewmembers", endpoint="viewmembers"))

admin.add_view(UserOrgAmin(UserOrg))

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


@app.template_filter("isodate")
def isodate(d, sep=' '):
    """Render date into format YYYY-mm-dd HH:MM."""
    return d.strftime("%Y‑%m‑%d" + sep + "%H:%M") if d and isinstance(d, (datetime, )) else d


@app.template_filter("shorturl")
def shorturl(url):
    """Create and render short url"""
    u = Url.shorten(url)
    return url_for("short_url", short_id=u.short_id, _external=True)


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
        return redirect(url_for('viewmembers.index_view'))
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
            app.logger.exception(f"For {user} exception encountered")
        except Exception as ex:
            abort(500, ex)

    return render_template("profile_entry.html", section_type=section_type, form=form, _url=_url)


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

    _url = request.args.get("url") or request.referrer or url_for("viewmembers.index_view")

    section_type = section_type.upper()[:3]  # normalize the section type
    try:
        user = User.get(id=user_id, organisation_id=current_user.organisation_id)
    except:
        flash("ORCID HUB doent have data related to this researcher", "warning")
        return redirect(_url)

    if not user.orcid:
        flash("The user hasn't yet linked their ORCID record", "danger")
        return redirect(_url)

    orcid_token = None
    try:
        orcid_token = OrcidToken.get(user=user, org=current_user.organisation)
    except:
        flash("User didn't give permissions to update his/her records", "warning")
        return redirect(_url)

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
        if ex.status == 401:
            flash("User has revoked the permissions to update his/her records", "warning")
        else:
            flash("Exception when calling MemberAPIV20Api->view_employments: %s\n" % message,
                  "danger")
        return redirect(_url)
    except Exception as ex:
        abort(500, ex)

    # TODO: Organisation has read token
    # TODO: Organisation has access to the employment records
    # TODO: retrieve and tranform for presentation (order, etc)
    try:
        data = api_response.to_dict()
    except Exception as ex:
        flash("User didn't give permissions to update his/her records", "warning")
        flash("Unhandled exception occured while retrieving ORCID data: %s" % ex, "danger")
        app.logger.exception(f"For {user} encountered exception")
        return redirect(_url)
    # TODO: transform data for presentation:
    if section_type == "EMP":
        return render_template(
            "employments.html",
            url=_url,
            data=data,
            user_id=user_id,
            org_client_id=user.organisation.orcid_client_id)
    elif section_type == "EDU":
        return render_template(
            "educations.html",
            url=_url,
            data=data,
            user_id=user_id,
            org_client_id=user.organisation.orcid_client_id)


def read_uploaded_file(form):
    """Read up the whole content and deconde it and return the whole content."""
    raw = request.files[form.file_.name].read()
    for encoding in "utf-8", "utf-8-sig", "utf-16":
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


@app.route("/load/org", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER)
def load_org():
    """Preload organisation data."""

    form = FileUploadForm()
    if form.validate_on_submit():
        row_count = OrgInfo.load_from_csv(read_uploaded_file(form))

        flash("Successfully loaded %d rows." % row_count, "success")
        return redirect(url_for("orginfo.index_view"))

    return render_template("fileUpload.html", form=form, form_title="Organisation")


@app.route("/load/researcher", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_researcher_affiliations():
    """Preload organisation data."""

    form = FileUploadForm()
    if form.validate_on_submit():
        filename = secure_filename(form.file_.data.filename)
        task = Task.load_from_csv(read_uploaded_file(form), filename=filename)

        flash(f"Successfully loaded {task.record_count} rows.")
        return redirect(url_for("affiliationrecord.index_view", task_id=task.id))

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


def register_org(org_name,
                 email=None,
                 org_email=None,
                 tech_contact=True,
                 via_orcid=False,
                 first_name=None,
                 last_name=None,
                 orcid_id=None,
                 city=None,
                 state=None,
                 country=None,
                 course_or_role=None,
                 disambiguation_org_id=None,
                 disambiguation_org_source=None,
                 **kwargs):
    """Register research organisaion."""

    email = (email or org_email).lower()
    try:
        User.get(User.email == email)
    except User.DoesNotExist:
        pass
    finally:
        try:
            org = Organisation.get(name=org_name)
        except Organisation.DoesNotExist:
            org = Organisation(name=org_name)
            if via_orcid:
                org.state = state
                org.city = city
                org.country = country
                org.disambiguation_org_id = disambiguation_org_id
                org.disambiguation_org_source = disambiguation_org_source

        try:
            org_info = OrgInfo.get(name=org.name)
        except OrgInfo.DoesNotExist:
            pass
        else:
            org.tuakiri_name = org_info.tuakiri_name

        try:
            org.save()
        except Exception as ex:
            app.logger.exception("Failed to save organisation data")
            raise

        try:
            user = User.get(email=email)
            user.organisation = org
            user.confirmed = True
        except User.DoesNotExist:
            user = User.create(
                email=email,
                confirmed=True,  # In order to let the user in...
                organisation=org)

        user.roles |= Role.ADMIN
        if via_orcid:
            if not user.orcid and orcid_id:
                user.orcid = orcid_id
            if not user.first_name and first_name:
                user.first_name = first_name
            if not user.last_name and last_name:
                user.last_name = last_name

        try:
            user.save()
        except Exception as ex:
            app.logger.exception("Failed to save user data")
            raise

        if tech_contact:
            user.roles |= Role.TECHNICAL
            org.tech_contact = user
            try:
                user.save()
                org.save()
            except Exception as ex:
                app.logger.exception(
                    "Failed to assign the user as the technical contact to the organisation")
                raise
        try:
            user_org = UserOrg.get(user=user, org=org)
            user_org.is_admin = True
            try:
                user_org.save()
            except Exception as ex:
                app.logger.exception(
                    "Failed to assign the user as an administrator to the organisation")
                raise
        except UserOrg.DoesNotExist:
            user_org = UserOrg.create(user=user, org=org, is_admin=True)

        app.logger.info(f"Ready to send an ivitation to '{org_name} <{email}>'.")
        token = generate_confirmation_token(email=email, org_name=org_name)
        # TODO: for via_orcid constact direct link to ORCID with callback like to HUB
        if via_orcid:
            short_id = Url.shorten(
                url_for(
                    "orcid_login",
                    invitation_token=token,
                    _next=url_for("onboard_org", invitation_token=token))).short_id
        else:
            short_id = Url.shorten(url_for("onboard_org", invitation_token=token)).short_id

        utils.send_email(
            "email/org_invitation.html",
            recipient=(org_name, email),
            reply_to=(current_user.name, current_user.email),
            cc_email=(current_user.name, current_user.email),
            invitation_url=url_for("short_url", short_id=short_id, _external=True),
            org_name=org_name,
            user=user)

        org.is_email_sent = True
        try:
            org.save()
        except Exception as ex:
            app.logger.exception("Failed to save organisation data")
            raise

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
    if form.validate_on_submit():
        try:
            register_org(**{f.name: f.data for f in form})
            flash("Organisation Invited Successfully! "
                  "An email has been sent to the organisation contact", "success")
            app.logger.info("Organisation '%s' successfully invited. Invitation sent to '%s'." %
                            (form.org_name.data, form.org_email.data))
        except Exception as ex:
            app.logger.exception()
            flash(str(ex), "danger")

    return render_template(
        "registration.html", form=form, org_info={r.name: r.to_dict()
                                                  for r in OrgInfo.select()})


@app.route("/invite/user", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER, Role.ADMIN)
def invite_user():
    """Invite a researcher to join the hub."""
    form = UserInvitationForm()
    org = current_user.organisation
    if request.method == "GET":
        form.organisation.data = org.name
        form.disambiguation_org_id.data = org.disambiguation_org_id
        form.disambiguation_org_source.data = org.disambiguation_org_source
        form.city.data = org.city
        form.state.data = org.state
        form.country.data = org.country

    if form.validate_on_submit():
        affiliations = 0
        if form.is_student.data:
            affiliations = Affiliation.EDU
        if form.is_employee.data:
            affiliations |= Affiliation.EMP
        send_user_initation(
            current_user,
            org,
            email=form.email_address.data,
            affiliations=affiliations,
            **{f.name: f.data
               for f in form})
    return render_template("user_invitation.html", form=form)
