# -*- coding: utf-8 -*-
"""Application views."""

import copy
import csv
import json
import mimetypes
import os
import secrets
from collections import namedtuple
from datetime import datetime
from io import BytesIO

import tablib
import yaml
from flask import (Response, abort, flash, jsonify, redirect, render_template, request, send_file, send_from_directory,
                   stream_with_context, url_for)
from flask_admin._compat import csv_encode
from flask_admin.actions import action
from flask_admin.babel import gettext
from flask_admin.base import expose
from flask_admin.contrib.peewee import ModelView
from flask_admin.form import SecureForm
from flask_admin.helpers import get_redirect_target
from flask_admin.model import typefmt
from flask_login import current_user, login_required
from jinja2 import Markup
from playhouse.shortcuts import model_to_dict
from werkzeug.utils import secure_filename
from wtforms.fields import BooleanField

from orcid_api.rest import ApiException

from . import admin, app, limiter, models, orcid_client, utils
from .config import ORCID_BASE_URL, SCOPE_ACTIVITIES_UPDATE, SCOPE_READ_LIMITED
from .forms import (ApplicationFrom, BitmapMultipleValueField, CredentialForm, EmailTemplateForm,
                    FileUploadForm, JsonOrYamlFileUploadForm, LogoForm, OrgRegistrationForm,
                    PartialDateField, RecordForm, UserInvitationForm)
from .login_provider import roles_required
from .models import (Affiliation, AffiliationRecord, CharField, Client, File, FundingContributor,
                     FundingRecord, Grant, ModelException, OrcidApiCall, OrcidToken, Organisation,
                     OrgInfo, OrgInvitation, PartialDate, Role, Task, TextField, Token, Url, User,
                     UserInvitation, UserOrg, UserOrgAffiliation, db)
# NB! Should be disabled in production
from .pyinfo import info
from .utils import generate_confirmation_token, get_next_url, send_user_invitation

HEADERS = {"Accept": "application/vnd.orcid+json", "Content-type": "application/vnd.orcid+json"}


@app.errorhandler(404)
def page_not_found(e):
    """Handle nonexistin pages."""
    _next = get_next_url()
    if _next:
        flash("Page Not Found", "danger")
        return redirect(_next)
    return render_template("404.html"), 404


@app.route("/favicon.ico")
def favicon():
    """Support for the "favicon" legacy: faveicon location in the root directory."""
    return send_from_directory(
        os.path.join(app.root_path, "static", "images"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon")


@app.route("/status")
@limiter.limit("10/minute")
def status():
    """Check the application health status attempting to connect to the DB.

    NB! This entry point should be protectd and accessible
    only form the appliction monitoring servers.
    """
    try:
        now = db.execute_sql("SELECT now();").fetchone()[0]
        return jsonify({
            "status": "Connection successful.",
            "db-timestamp": now.isoformat(),
        })
    except Exception as ex:
        return jsonify({
            "status": "Error",
            "message": str(ex),
        }), 503  # Service Unavailable


@app.route("/pyinfo")
@roles_required(Role.SUPERUSER)
def pyinfo():
    """Show Python and runtime environment and settings."""
    return render_template("pyinfo.html", **info)


@app.route("/u/<short_id>")
def short_url(short_id):
    """Redirect to the full URL."""
    try:
        u = Url.get(short_id=short_id)
        if request.args:
            return redirect(utils.append_qs(u.url, **request.args))
        return redirect(u.url)
    except Url.DoesNotExist:
        abort(404)


def read_uploaded_file(form):
    """Read up the whole content and deconde it and return the whole content."""
    raw = request.files[form.file_.name].read()
    for encoding in "utf-8", "utf-8-sig", "utf-16":
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def orcid_link_formatter(view, context, model, name):
    """Format ORCID ID for ModelViews."""
    if not model.orcid:
        return ""
    return Markup(f'<a href="{ORCID_BASE_URL}/{model.orcid}" target="_blank">{model.orcid}</a>')


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
    column_formatters = dict(
        roles=lambda v, c, m, p: ", ".join(n for r, n in v.roles.items() if r & m.roles),
        orcid=orcid_link_formatter)
    column_default_sort = "id"
    column_labels = dict(org="Organisation", orcid="ORCID iD")
    column_type_formatters = dict(typefmt.BASE_FORMATTERS)
    column_type_formatters.update({
        datetime:
        lambda view, value: Markup(f"""<time datetime="{value.isoformat(timespec='minutes')}" />"""),
        # lambda view, value: Markup(value.strftime("%Y‑%m‑%d&nbsp;%H:%M")),
    })
    column_type_formatters_export = dict(typefmt.EXPORT_FORMATTERS)
    column_type_formatters_export.update({PartialDate: lambda view, value: str(value)})
    column_formatters_export = dict(orcid=lambda v, c, m, p: m.orcid)
    column_exclude_list = (
        "updated_at",
        "updated_by",
    )
    form_overrides = dict(start_date=PartialDateField, end_date=PartialDateField)
    form_widget_args = {c: {"readonly": True} for c in column_exclude_list}

    def __init__(self, model=None, *args, **kwargs):
        """Pick the model based on the ModelView class name assuming it is ModelClass + "Admin"."""
        if model is None:
            if hasattr(self, "model"):
                model = self.model
            else:
                model_class_name = self.__class__.__name__.replace("Admin", '')
                model = globals().get(model_class_name)
            if model is None:
                if model_class_name not in dir(models):
                    raise Exception(f"Model class {model_class_name} doesn't exit.")
                model = models.__dict__.get(model_class_name)
        super().__init__(model, *args, **kwargs)

    # TODO: remove whent it gets merged into the upsteem repo (it's a workaround to make
    # joins LEFT OUTERE)
    def _handle_join(self, query, field, joins):
        if field.model_class != self.model:
            model_name = field.model_class.__name__

            if model_name not in joins:
                query = query.join(field.model_class, "LEFT OUTER")
                joins.add(model_name)

        return query

    def get_pk_value(self, model):
        """Get correct value for composite keys."""
        if self.model._meta.composite_key:
            return tuple([
                model._data[field_name] for field_name in self.model._meta.primary_key.field_names
            ])
        return super().get_pk_value(model)

    def get_one(self, id):
        """Fix for composite keys."""
        try:
            if self.model._meta.composite_key:
                return self.model.get(**dict(zip(self.model._meta.primary_key.field_names, id)))
            return super().get_one(id)
        except self.model.DoesNotExist:
            flash(f"The record with given ID: {id} doesn't exist or it was deleted.", "danger")
            abort(404)

    def init_search(self):
        """Include linked columns in the search if they are defined with 'liked_table.column'."""
        if self.column_searchable_list:
            for p in self.column_searchable_list:
                if "." in p:
                    m, p = p.split('.')
                    m = getattr(self.model, m).rel_model
                    p = getattr(m, p)

                elif isinstance(p, str):
                    p = getattr(self.model, p)

                # Check type
                if not isinstance(p, (
                        CharField,
                        TextField,
                )):
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
        return redirect(url_for("index", next=request.url))

    def get_query(self):
        """Add URL query to the data select for foreign key and select data that user has access to."""
        query = super().get_query()

        if current_user and not current_user.has_role(Role.SUPERUSER) and current_user.has_role(
                Role.ADMIN):
            # Show only rows realted to the curretn organisation the user is admin for.
            # Skip this part for SUPERUSER.
            db_columns = [c.db_column for c in self.model._meta.fields.values()]
            if "org_id" in db_columns or "organisation_id" in db_columns:
                if "org_id" in db_columns:
                    query = query.where(self.model.org_id == current_user.organisation.id)
                else:
                    query = query.where(self.model.organisation_id == current_user.organisation.id)

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
            if k not in (
                'page',
                'page_size',
                'sort',
                'desc',
                'search',
            ) and not k.startswith('flt')
        }
        view_args.extra_args = extra_args
        return view_args


class UserAdmin(AppModelView):
    """User model view."""

    edit_template = "admin/user_edit.html"
    roles = {1: "Superuser", 2: "Administrator", 4: "Researcher", 8: "Technical Contact"}

    form_extra_fields = dict(is_superuser=BooleanField("Is Superuser"))
    form_excluded_columns = (
        "roles",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    column_exclude_list = (
        "password",
        "username",
        "first_name",
        "last_name",
    )
    column_searchable_list = (
        "name",
        "orcid",
        "email",
        "eppn",
        "organisation.name",
    )
    form_overrides = dict(roles=BitmapMultipleValueField)
    form_args = dict(roles=dict(choices=roles.items()))

    form_ajax_refs = {
        "organisation": {
            "fields": (Organisation.name, "name")
        },
    }
    can_export = True

    def update_model(self, form, model):
        """Added prevalidation of the form."""
        if "roles" not in self.form_excluded_columns and form.roles.data != model.roles:
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

    column_exclude_list = (
        "orcid_client_id",
        "orcid_secret",
        "created_at",
        "logo",
    )
    column_searchable_list = (
        "name",
        "tuakiri_name",
        "city",
    )
    edit_template = "admin/organisation_edit.html"
    form_widget_args = AppModelView.form_widget_args
    form_widget_args["api_credentials_requested_at"] = {"readonly": True}
    form_widget_args["api_credentials_entered_at"] = {"readonly": True}

    def update_model(self, form, model):
        """Handle change of the technical contact."""
        # Technical contact changed:
        if form.tech_contact.data and form.tech_contact.data.id != model.tech_contact_id:
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
    column_searchable_list = (
        "name",
        "tuakiri_name",
        "city",
        "first_name",
        "last_name",
        "email",
    )

    @action("invite", "Register Organisation",
            "Are you sure you want to register selected organisations?")
    def action_invite(self, ids):
        """Batch registraion of organisatons."""
        count = 0
        for oi in OrgInfo.select().where(OrgInfo.id.in_(ids)):
            try:
                register_org(
                    org_name=oi.name,
                    email=oi.email,
                    tech_contact=True,
                    via_orcid=(False if oi.tuakiri_name else True),
                    first_name=oi.first_name,
                    last_name=oi.last_name,
                    city=oi.city,
                    country=oi.country,
                    course_or_role=oi.role,
                    disambiguated_id=oi.disambiguated_id,
                    disambiguation_source=oi.disambiguation_source)
                count += 1
            except Exception as ex:
                flash(f"Failed to send an invitation to {oi.email}: {ex}")
                app.logger.exception(f"Failed to send registration invitation to {oi.email}.")

        flash("%d invitations were sent successfully." % count)


class OrcidTokenAdmin(AppModelView):
    """ORCID token model view."""

    column_searchable_list = (
        "user.name",
        "user.email",
        "org.name",
    )
    can_export = True
    can_create = False


class OrcidApiCallAmin(AppModelView):
    """ORCID API calls."""

    can_export = True
    can_edit = False
    can_delete = False
    can_create = False
    column_searchable_list = (
        "url",
        "body",
        "response",
        "user.name",
    )


class UserOrgAmin(AppModelView):
    """User Organisations."""

    column_searchable_list = (
        "user.email",
        "org.name",
    )


class TaskAdmin(AppModelView):
    """Task model view."""

    roles_required = Role.SUPERUSER | Role.ADMIN
    list_template = "view_tasks.html"
    column_exclude_list = ("task_type", )
    can_edit = False
    can_create = False
    can_delete = True
    column_searchable_list = (
        "filename",
        "created_by.email",
        "created_by.name",
        "created_by.first_name",
        "created_by.last_name",
        "org.name",
    )


class RecordModelView(AppModelView):
    """Task record model view."""

    roles_required = Role.SUPERUSER | Role.ADMIN
    column_exclude_list = (
        "task",
        "organisation",
    )
    column_export_exclude_list = (
        "task",
        "is_active",
    )
    can_edit = True
    can_create = False
    can_delete = False
    can_view_details = True
    can_export = True

    form_widget_args = {"external_id": {"readonly": True}}

    def render(self, template, **kwargs):
        """Pass the task to the render function as an added argument."""
        if "task" not in kwargs:
            task_id = request.args.get("task_id")
            if task_id:
                try:
                    kwargs["task"] = Task.get(id=task_id)
                except Task.DoesNotExist:
                    flash(f"The task with ID: {task_id} doesn't exist.", "danger")
                    abort(404)
        return super().render(template, **kwargs)

    def is_accessible(self):
        """Verify if the task view is accessible for the current user."""
        if not super().is_accessible():
            return False

        # Added the feature for superuser to access task related to all research organiastion
        if current_user.is_superuser:
            return True

        if request.method == "POST" and request.form.get("rowid"):
            # get the first ROWID:
            rowid = int(request.form.get("rowid"))
            task_id = self.model.get(id=rowid).task_id
        else:
            task_id = request.args.get("task_id")
            if not task_id:
                _id = request.args.get("id")
                if not _id:
                    flash("Cannot invoke the task view without task ID", "danger")
                    return False
                else:
                    task_id = self.model.get(id=_id).task_id

        try:
            task = Task.get(id=task_id)
            if task.org.id != current_user.organisation.id:
                flash("Access denied! You cannot access this task.", "danger")
                return False

        except Task.DoesNotExist:
            flash("The task deesn't exist.", "danger")
            abort(404)

        return True

    def get_export_name(self, export_type='csv'):
        """Get export file name using the original imported file name.

        :return: The exported csv file name.
        """
        task_id = request.args.get("task_id")
        if task_id:
            try:
                task = Task.get(id=task_id)
                filename = os.path.splitext(task.filename)[0]
                return "%s_%s.%s" % (filename, datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S"),
                                     export_type)
            except Task.DoesNotExist:
                flash(f"The batch task doesn't exist", "danger")
                abort(404)

        return super().get_export_name(export_type=export_type)

    @action("activate", "Activate for processing",
            """Are you sure you want to activate the selected records for batch processing?

By clicking "OK" you are affirming that the affiliations or the funding records to be written are,
to the best of your knowledge, correct!""")
    def action_activate(self, ids):
        """Batch registraion of users."""
        try:
            count = self.model.update(is_active=True).where(
                self.model.is_active == False,  # noqa: E712
                self.model.id.in_(ids)).execute()
        except Exception as ex:
            flash(f"Failed to activate the selected records: {ex}")
            app.logger.exception("Failed to activate the selected records")
        else:
            flash(f"{count} records were activated for batch processing.")

    @action("reset", "Reset for processing",
            "Are you sure you want to reset the selected records for batch processing?")
    def action_reset(self, ids):
        """Reset batch task records."""
        status = "The record was reset at " + datetime.utcnow().isoformat(timespec="seconds")
        with db.atomic():
            try:
                count = self.model.update(
                    processed_at=None, status=status).where(self.model.is_active,
                                                            self.model.id.in_(ids)).execute()

                if self.model == FundingRecord:
                    count = FundingContributor.update(
                        processed_at=None, status=status).where(
                            FundingContributor.funding_record.in_(ids)).execute()
                elif self.model == AffiliationRecord:
                    # Delete the userInvitation token when reset to send the mail again.
                    task_id = None
                    if request.method == "POST" and request.form.get("rowid"):
                        # get the first ROWID:
                        rowid = int(request.form.get("rowid"))
                        task_id = self.model.get(id=rowid).task_id
                    else:
                        task_id = request.form.get('task_id')
                    user_invitation = UserInvitation.get(task_id=task_id)
                    user_invitation.delete_instance()
            except UserInvitation.DoesNotExist:
                pass
            except Exception as ex:
                db.rollback()
                flash(f"Failed to activate the selected records: {ex}")
                app.logger.exception("Failed to activate the selected records")

            else:
                if self.model == FundingRecord:
                    flash(f"{count} Funding Contributor records were reset for batch processing.")
                else:
                    flash(f"{count} Affiliation records were reset for batch processing.")


class ExternalIdAdmin(AppModelView):
    """ExternalId model view."""

    roles_required = Role.SUPERUSER | Role.ADMIN
    list_template = "funding_externalid_list.html"
    column_exclude_list = ("funding_record", )

    can_edit = True
    can_create = False
    can_delete = False
    can_view_details = True

    form_widget_args = {"external_id": {"readonly": True}}

    def is_accessible(self):
        """Verify if the external id's view is accessible for the current user."""
        if not super().is_accessible():
            flash("Access denied! You cannot access this task.", "danger")
            return False

        return True


class FundingContributorAdmin(AppModelView):
    """Funding record model view."""

    roles_required = Role.SUPERUSER | Role.ADMIN
    list_template = "funding_contributor_list.html"
    column_exclude_list = ("funding_record", )

    can_edit = True
    can_create = False
    can_delete = False
    can_view_details = True

    form_widget_args = {"external_id": {"readonly": True}}

    def is_accessible(self):
        """Verify if the funding contributor view is accessible for the current user."""
        if not super().is_accessible():
            flash("Access denied! You cannot access this task.", "danger")
            return False

        return True

    @action("reset", "Reset for processing",
            "Are you sure you want to reset the selected records for batch processing?")
    def action_reset(self, ids):
        """Batch reset of users."""
        with db.atomic():
            try:
                status = " The record was reset at " + datetime.utcnow().isoformat(timespec="seconds")
                count = self.model.update(
                    processed_at=None, status=status).where(self.model.id.in_(ids)).execute()
                funding_record_id = self.model.select().where(
                    self.model.id.in_(ids))[0].funding_record_id
                FundingRecord.update(
                    processed_at=None, status=status).where(
                        FundingRecord.is_active, FundingRecord.id == funding_record_id).execute()
            except Exception as ex:
                db.rollback()
                flash(f"Failed to activate the selected records: {ex}")
                app.logger.exception("Failed to activate the selected records")
            else:
                flash(f"{count} Funding Contributor records were reset for batch processing.")


class FundingRecordAdmin(RecordModelView):
    """Funding record model view."""

    list_template = "funding_record_list.html"
    column_searchable_list = ("title", )
    column_export_exclude_list = (
        "task",
        "is_active",
        "status",
        "processed_at",
        "created_at",
        "updated_at",
        "title",
        "translated_title",
        "translated_title_language_code",
        "type",
        "organization_defined_type",
        "short_description",
        "amount",
        "currency",
        "start_date",
        "end_date",
        "org_name",
        "city",
        "region",
        "country",
        "disambiguated_org_identifier",
        "disambiguation_source",
        "visibility",
    )
    export_types = [
        "tsv",
        "yaml",
        "json",
        "csv",
    ]
    column_export_list = (
        "funding id",
        "contributors",
    )
    column_csv_export_list = ("funding id", "email", "name", "orcid", "put_code", "role", "status")

    def _export_tablib(self, export_type, return_url):
        """Override funding export functionality to integrate funding contributors and external ids."""
        if tablib is None:
            flash(gettext('Tablib dependency not installed.'), 'error')
            return redirect(return_url)

        filename = self.get_export_name(export_type)

        disposition = 'attachment;filename=%s' % (secure_filename(filename), )

        mimetype, encoding = mimetypes.guess_type(filename)
        if not mimetype:
            mimetype = 'application/octet-stream'
        if encoding:
            mimetype = '%s; charset=%s' % (mimetype, encoding)

        ds = tablib.Dataset(headers=[c[1] for c in self._export_columns])

        count, data = self._export_data()

        for row in data:
            external_id_list, contributor_list = self.get_external_id_contributors(row)
            for external_ids in external_id_list:
                vals = []
                vals.append(external_ids['value'])
                vals.append(contributor_list)
                ds.append(vals)

        try:
            try:
                ds.yaml = yaml.safe_dump(
                    json.loads(ds.json.replace("]\\", "]").replace("\\n", " ")))
                response_data = ds.export(format=export_type)
            except AttributeError:
                response_data = getattr(ds, export_type)
        except (AttributeError, tablib.UnsupportedFormat):
            flash(gettext('Export type "%(type)s not supported.', type=export_type), 'error')
            return redirect(return_url)

        return Response(
            response_data,
            headers={'Content-Disposition': disposition},
            mimetype=mimetype,
        )

    def get_external_id_contributors(self, row):
        """Get funding contributors and external ids."""
        vals = []
        contributor_list = []
        external_id_list = []
        exclude_list = ['id', 'funding_record_id', 'processed_at']
        for c in self._export_columns:
            if c[0] == 'contributors':
                for f in row.contributors:
                    contributor_rec = {}
                    for col in f._meta.columns.keys():
                        if col not in exclude_list:
                            contributor_rec[col] = self._get_list_value(
                                None,
                                f,
                                col,
                                self.column_formatters_export,
                                self.column_type_formatters_export,
                            )
                    contributor_list.append(contributor_rec)
            elif c[0] == 'funding id':
                external_id_relation_part_of = {}
                for f in row.external_ids:
                    external_id_rec = {}
                    for col in f._meta.columns.keys():
                        if col not in exclude_list:
                            external_id_rec[col] = self._get_list_value(
                                None,
                                f,
                                col,
                                self.column_formatters_export,
                                self.column_type_formatters_export,
                            )
                    # Get the first external id from extrnal id list with 'SELF' relationship for funding export
                    if not external_id_list and external_id_rec.get(
                            'relationship') and external_id_rec.get(
                                'relationship').lower() == 'self':
                        external_id_list.append(external_id_rec)
                    elif not external_id_list and not external_id_relation_part_of and external_id_rec.get(
                            'relationship').lower() == 'part_of':
                        external_id_relation_part_of = copy.deepcopy(external_id_rec)
                # Also if there no external id with relation 'Self' take first one from 'part_of'
                if not external_id_list and external_id_relation_part_of:
                    external_id_list.append(external_id_relation_part_of)
            else:
                vals.append(self.get_export_value(row, c[0]))
        return (external_id_list, contributor_list)

    @expose('/export/<export_type>/')
    def export(self, export_type):
        """Check the export type whether it is csv, tsv or other format."""
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_export or (export_type not in self.export_types):
            flash(gettext('Permission denied.'), 'error')
            return redirect(return_url)

        if export_type == 'csv' or export_type == 'tsv':
            return self._export_csv(return_url, export_type)
        else:
            return self._export_tablib(export_type, return_url)

    def _export_csv(self, return_url, export_type):
        """Export a CSV or tsv of records as a stream."""
        delimiter = ","
        if export_type == 'tsv':
            delimiter = "\t"

        count, data = self._export_data()

        # https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
        class Echo(object):
            """An object that implements just the write method of the file-like interface."""

            def write(self, value):
                """Write the value by returning it, instead of storing in a buffer."""
                return value

        writer = csv.writer(Echo(), delimiter=delimiter)

        def generate():
            # Append the column titles at the beginning
            titles = [csv_encode(c) for c in self.column_csv_export_list]
            yield writer.writerow(titles)

            for row in data:
                external_id_list, contributor_list = self.get_external_id_contributors(row)
                for external_ids in external_id_list:
                    for cont in contributor_list:
                        vals = []
                        vals.append(external_ids['value'])
                        for col in self.column_csv_export_list[1:]:
                            vals.append(cont.get(col))
                        yield writer.writerow(vals)

        filename = self.get_export_name(export_type=export_type)

        disposition = 'attachment;filename=%s' % (secure_filename(filename), )

        return Response(
            stream_with_context(generate()),
            headers={'Content-Disposition': disposition},
            mimetype='text/' + export_type)


class AffiliationRecordAdmin(RecordModelView):
    """Affiliation record model view."""

    list_template = "affiliation_record_list.html"
    column_exclude_list = (
        "task",
        "organisation",
    )
    column_searchable_list = (
        "first_name",
        "last_name",
        "email",
        "role",
        "department",
        "state",
    )
    column_export_exclude_list = (
        "task",
        "is_active",
    )


class ViewMembersAdmin(AppModelView):
    """Organisation member model (User beloging to the current org.admin oganisation) view."""

    roles_required = Role.SUPERUSER | Role.ADMIN
    list_template = "viewMembers.html"
    column_list = ("email", "orcid")
    column_searchable_list = (
        "email",
        "orcid",
        "name",
        "first_name",
        "last_name",
    )
    column_export_list = ("email", "eppn", "orcid")
    model = User
    can_edit = False
    can_create = False
    can_delete = False
    can_view_details = False
    can_export = True

    def get_query(self):
        """Get quiery for the user belonging to the organistation of the current user."""
        return current_user.organisation.users


admin.add_view(UserAdmin(User))
admin.add_view(OrganisationAdmin(Organisation))
admin.add_view(OrcidTokenAdmin(OrcidToken))
admin.add_view(OrgInfoAdmin(OrgInfo))
admin.add_view(OrcidApiCallAmin(OrcidApiCall))
admin.add_view(TaskAdmin(Task))
admin.add_view(AffiliationRecordAdmin())
admin.add_view(FundingRecordAdmin())
admin.add_view(FundingContributorAdmin())
admin.add_view(ExternalIdAdmin())
admin.add_view(AppModelView(UserInvitation))
admin.add_view(ViewMembersAdmin(name="viewmembers", endpoint="viewmembers"))

admin.add_view(UserOrgAmin(UserOrg))
admin.add_view(AppModelView(Client))
admin.add_view(AppModelView(Grant))
admin.add_view(AppModelView(Token))

SectionRecord = namedtuple(
    "SectionRecord",
    ["org_name", "city", "state", "country", "department", "role", "start_date", "end_date"])
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
def isodate(d, sep="&nbsp;"):
    """Render date into format YYYY-mm-dd HH:MM."""
    if d and isinstance(d, datetime):
        return Markup(
            f"""<time datetime="{d.isoformat(timespec='minutes')}" """
            f"""data-format="YYYY[&#8209;]MM[&#8209;]DD[{sep}]HH:mm" />""")
    return ''


@app.template_filter("shorturl")
def shorturl(url):
    """Create and render short url."""
    u = Url.shorten(url)
    return url_for("short_url", short_id=u.short_id, _external=True)


@app.route("/activate_all", methods=["POST"])
@roles_required(Role.SUPERUSER, Role.ADMIN, Role.TECHNICAL)
def activate_all():
    """Batch registraion of users."""
    _url = request.args.get("url") or request.referrer
    task_id = request.form.get('task_id')
    task = Task.get(id=task_id)
    try:
        if task.task_type == 0:
            count = AffiliationRecord.update(is_active=True).where(
                AffiliationRecord.task_id == task_id,
                AffiliationRecord.is_active == False).execute()  # noqa: E712
        elif task.task_type == 1:
            count = FundingRecord.update(is_active=True).where(
                FundingRecord.task_id == task_id,
                FundingRecord.is_active == False).execute()  # noqa: E712
    except Exception as ex:
        flash(f"Failed to activate the selected records: {ex}")
        app.logger.exception("Failed to activate the selected records")
    else:
        flash(f"{count} records were activated for batch processing.")
    return redirect(_url)


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
    except Exception:
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
    except Exception:
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
    except Exception:
        flash("The user hasn't authorized you to Add records", "warning")
        return redirect(_url)
    orcid_client.configuration.access_token = orcid_token.access_token
    api = orcid_client.MemberAPI(user=user)

    # TODO: handle "new"...
    if put_code:
        try:
            # Fetch an Employment
            if section_type == "EMP":
                api_response = api.view_employment(user.orcid, put_code)
            elif section_type == "EDU":
                api_response = api.view_education(user.orcid, put_code)

            _data = api_response.to_dict()
            data = SectionRecord(
                org_name=_data.get("organization").get("name"),
                city=_data.get("organization").get("address").get("city", ""),
                state=_data.get("organization").get("address").get("region", ""),
                country=_data.get("organization").get("address").get("country", ""),
                department=_data.get("department_name", ""),
                role=_data.get("role_title", ""),
                start_date=PartialDate.create(_data.get("start_date")),
                end_date=PartialDate.create(_data.get("end_date")))
        except ApiException as e:
            message = json.loads(e.body.replace("''", "\"")).get('user-messsage')
            app.logger.error(f"Exception when calling MemberAPIV20Api->view_employment: {message}")
        except Exception as ex:
            app.logger.exception(
                "Unhandler error occured while creating or editing a profile record.")
            abort(500, ex)
    else:
        data = SectionRecord(org_name=org.name, city=org.city, country=org.country)

    form = RecordForm.create_form(request.form, obj=data, form_type=section_type)
    if not form.org_name.data:
        form.org_name.data = org.name
    if not form.country.data or form.country.data == "None":
        form.country.data = org.country

    if form.validate_on_submit():
        try:
            put_code, orcid, created = api.create_or_update_affiliation(
                put_code=put_code,
                affiliation=Affiliation[section_type],
                **{f.name: f.data
                   for f in form})
            if put_code and created:
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
            app.logger.exception(
                "Unhandler error occured while creating or editing a profile record.")
            abort(500, ex)

    return render_template("profile_entry.html", section_type=section_type, form=form, _url=_url)


@app.route("/<int:user_id>/emp/list")
@app.route("/<int:user_id>/emp")
@login_required
def employment_list(user_id):
    """Show the employmen list of the selected user."""
    return show_record_section(user_id, "EMP")


@app.route("/<int:user_id>/edu/list")
@app.route("/<int:user_id>/edu")
@login_required
def edu_list(user_id):
    """Show the education list of the selected user."""
    return show_record_section(user_id, "EDU")


def show_record_section(user_id, section_type="EMP"):
    """Show all user profile section list."""
    _url = request.args.get("url") or request.referrer or url_for("viewmembers.index_view")

    section_type = section_type.upper()[:3]  # normalize the section type
    try:
        user = User.get(id=user_id, organisation_id=current_user.organisation_id)
    except Exception:
        flash("ORCID HUB doent have data related to this researcher", "warning")
        return redirect(_url)

    if not user.orcid:
        flash("The user hasn't yet linked their ORCID record", "danger")
        return redirect(_url)

    orcid_token = None
    try:
        orcid_token = OrcidToken.get(user=user, org=current_user.organisation)
    except Exception:
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
        try:
            task = Task.load_from_csv(read_uploaded_file(form), filename=filename)
            flash(f"Successfully loaded {task.record_count} rows.")
            return redirect(url_for("affiliationrecord.index_view", task_id=task.id))
        except (
                ValueError,
                ModelException,
        ) as ex:
            flash(f"Failed to load affiliation record file: {ex}", "danger")
            app.logger.exception("Failed to load affiliation records.")

    return render_template("fileUpload.html", form=form, form_title="Researcher")


@app.route("/load/researcher/funding", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_researcher_funding():
    """Preload organisation data."""
    form = JsonOrYamlFileUploadForm()
    if form.validate_on_submit():
        filename = secure_filename(form.file_.data.filename)
        try:
            task = FundingRecord.load_from_json(read_uploaded_file(form), filename=filename)
            flash(f"Successfully loaded {task.record_funding_count} rows.")
            return redirect(url_for("fundingrecord.index_view", task_id=task.id))
        except Exception as ex:
            flash(f"Failed to load funding record file: {ex}", "danger")
            app.logger.exception("Failed to load funding records.")

    return render_template("fileUpload.html", form=form, form_title="Funding")


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
                 disambiguated_id=None,
                 disambiguation_source=None,
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
                org.disambiguated_id = disambiguated_id
                org.disambiguation_source = disambiguation_source

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
                url_for("orcid_login", invitation_token=token,
                        _next=url_for("onboard_org"))).short_id
            invitation_url = url_for("short_url", short_id=short_id, _external=True)
        else:
            invitation_url = url_for("index", _external=True)

        utils.send_email(
            "email/org_invitation.html",
            recipient=(org_name, email),
            reply_to=(current_user.name, current_user.email),
            cc_email=(current_user.name, current_user.email),
            invitation_url=invitation_url,
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
        params = {f.name: f.data for f in form}
        try:
            org_name = params.get("org_name")
            email = params.get("org_email").lower()

            if params.get("tech_contact"):
                try:
                    org = Organisation.get(name=org_name)
                    if org.tech_contact and org.tech_contact.email != email:
                        flash(f"The current tech.conact {org.tech_contact.name} "
                              f"({org.tech_contact.email}) will be revoked.", "warning")
                except Organisation.DoesNotExist:
                    pass

            register_org(**params)
            org = Organisation.get(name=org_name)
            user = User.get(email=email)
            if org.confirmed:
                if user.is_tech_contact_of(org):
                    flash("New Technical contact has been Invited Successfully! "
                          "An email has been sent to the Technical contact", "success")
                    app.logger.info(
                        f"For Organisation '{org_name}' , "
                        f"New Technical Contact '{email}' has been invited successfully.")
                else:
                    flash("New Organisation Admin has been Invited Successfully! "
                          "An email has been sent to the Organisation Admin", "success")
                    app.logger.info(
                        f"For Organisation '{org_name}' , "
                        f"New Organisation Admin '{email}' has been invited successfully.")
            else:
                flash("Organisation Invited Successfully! "
                      "An email has been sent to the organisation contact", "success")
                app.logger.info(f"Organisation '{org_name}' successfully invited. "
                                f"Invitation sent to '{email}'.")
        except Exception as ex:
            app.logger.exception(f"Failed to send registration invitation with {params}.")
            flash(f"Failed to send registration invitation: {ex}.", "danger")

    return render_template(
        "registration.html", form=form, org_info={r.name: r.to_dict()
                                                  for r in OrgInfo.select()})


@app.route("/user/<int:user_id>/organisations", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER)
def user_organisations(user_id):
    """Manage user organisaions."""
    user_orgs = (Organisation.select(
        Organisation.id, Organisation.name,
        (Organisation.tech_contact_id == user_id).alias("is_tech_contact"), UserOrg.is_admin).join(
            UserOrg, on=((UserOrg.org_id == Organisation.id) & (UserOrg.user_id == user_id)))
                 .naive())
    return render_template("user_organisations.html", user_orgs=user_orgs)


@app.route("/invite/user", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER, Role.ADMIN)
def invite_user():
    """Invite a researcher to join the hub."""
    form = UserInvitationForm()
    org = current_user.organisation
    if request.method == "GET":
        form.organisation.data = org.name
        form.disambiguated_id.data = org.disambiguated_id
        form.disambiguation_source.data = org.disambiguation_source
        form.city.data = org.city
        form.state.data = org.state
        form.country.data = org.country

    while form.validate_on_submit():
        resend = form.resend.data
        email = form.email_address.data.lower()
        affiliations = 0
        if form.is_student.data:
            affiliations = Affiliation.EDU
        if form.is_employee.data:
            affiliations |= Affiliation.EMP
        try:
            ui = UserInvitation.get(org=org, email=email)
            flash(
                f"An invitation to affiliate with {org} had been already sent to {email} earlier "
                f"at {isodate(ui.sent_at)}.", "warning" if resend else "danger")
            if not form.resend.data:
                break
        except UserInvitation.DoesNotExist:
            pass

        ui = send_user_invitation(
            current_user,
            org,
            email=email,
            affiliations=affiliations,
            **{f.name: f.data
               for f in form})
        flash(f"An invitation to {ui.email} was {'resent' if resend else 'sent'} successfully.",
              "success")
        break

    return render_template("user_invitation.html", form=form)


@app.route(
    "/settings/email_template", methods=[
        "GET",
        "POST",
    ])
@roles_required(Role.TECHNICAL, Role.ADMIN)
def manage_email_template():
    """Manage organisation invitation email template."""
    org = current_user.organisation
    form = EmailTemplateForm(obj=org)
    default_template = app.config.get("DEFAULT_EMAIL_TEMPLATE")

    if form.validate_on_submit():
        if form.prefill.data or form.reset.data:
            form.email_template.data = default_template
        elif form.cancel.data:
            pass
        elif form.send.data:
            logo = org.logo if form.email_template_enabled.data else None
            utils.send_email(
                "email/test.html",
                recipient=(current_user.name, current_user.email),
                reply_to=(current_user.name, current_user.email),
                cc_email=(current_user.name, current_user.email),
                sender=(current_user.name, current_user.email),
                subject="TEST EMAIL",
                org_name=org.name,
                logo=url_for("logo_image", token=logo.token, _external=True) if logo else None,
                base=form.email_template.data
                if form.email_template_enabled.data else default_template)
        elif form.save.data:
            # form.populate_obj(org)
            org.email_template = form.email_template.data
            org.email_template_enabled = form.email_template_enabled.data
            org.save()
            flash("Saved organisation email template'", "info")

    return render_template("email_template.html", form=form)


@app.route("/logo/<string:token>")
@app.route("/logo")
def logo_image(token=None):
    """Get organisation Logo image."""
    if token:
        logo = File.select().where(File.token == token).first()
        if logo:
            return send_file(
                BytesIO(logo.data), mimetype=logo.mimetype, attachment_filename=logo.filename)
    return redirect(url_for("static", filename="images/banner-small.png", _external=True))


@app.route(
    "/settings/logo", methods=[
        "GET",
        "POST",
    ])
@roles_required(Role.TECHNICAL, Role.ADMIN)
def logo():
    """Manage organisation 'logo'."""
    org = current_user.organisation
    best = request.accept_mimetypes.best_match(["text/html", "image/*"])
    if best == "image/*" and org.logo:
        return send_file(
            BytesIO(org.logo.data),
            mimetype=org.logo.mimetype,
            attachment_filename=org.logo.filename)

    form = LogoForm()
    if request.method == "POST" and form.reset.data:
        org.logo = None
        org.save()
    elif form.validate_on_submit():
        f = form.logo_file.data
        filename = secure_filename(f.filename)
        logo = File.create(data=f.read(), mimetype=f.mimetype, filename=f.filename)
        org.logo = logo
        org.save()
        flash(f"Saved organisation logo '{filename}'", "info")

    return render_template("logo.html", form=form)


@app.route(
    "/settings/applications/<int:app_id>", methods=[
        "GET",
        "POST",
    ])
@app.route(
    "/settings/applications", methods=[
        "GET",
        "POST",
    ])
@roles_required(Role.SUPERUSER, Role.TECHNICAL)
def application(app_id=None):
    """Register an application client."""
    form = ApplicationFrom()
    if app_id:
        client = Client.select().where(Client.id == app_id).first()
    else:
        client = Client.select().where(Client.user_id == current_user.id).first()
    if client:
        flash(
            f"You aready have registered application '{client.name}' and issued API credentials.",
            "info")
        return redirect(url_for("api_credentials", app_id=client.id))

    if form.validate_on_submit():
        client = Client(org_id=current_user.organisation.id)
        form.populate_obj(client)
        client.client_id = secrets.token_hex(10)
        client.client_secret = secrets.token_urlsafe(20)
        client.save()
        flash(f"Application '{client.name}' was successfully registered.", "success")
        return redirect(url_for("api_credentials", app_id=client.id))

    return render_template("application.html", form=form)


@app.route(
    "/settings/credentials/<int:app_id>", methods=[
        "GET",
        "POST",
    ])
@app.route(
    "/settings/credentials", methods=[
        "GET",
        "POST",
    ])
@roles_required(Role.SUPERUSER, Role.TECHNICAL)
def api_credentials(app_id=None):
    """Manage API credentials."""
    if app_id:
        client = Client.select().where(Client.id == app_id).first()
    else:
        client = Client.select().where(Client.user_id == current_user.id).first()
    if not client:
        return redirect(url_for("application"))
    form = CredentialForm(obj=client)
    if form.validate_on_submit():
        if form.revoke.data:
            Token.delete().where(Token.client == client).execute()
        elif form.reset.data:
            form.client_id.data = client.client_id = secrets.token_hex(10)
            form.client_secret.data = client.client_secret = secrets.token_urlsafe(20)
            client.save()
        elif form.update_app.data:
            form.populate_obj(client)
            client.save()
        elif form.delete.data:
            Token.delete().where(Token.client == client).execute()
            client.delete().execute()
            return redirect(url_for("application"))

    return render_template("api_credentials.html", form=form)


@app.route("/hub/api/v0.1/users/<int:user_id>/orgs/<int:org_id>")
@app.route("/hub/api/v0.1/users/<int:user_id>/orgs/")
@roles_required(Role.SUPERUSER, Role.ADMIN)
def user_orgs(user_id, org_id=None):
    """Retrive all linked to the user organisations."""
    try:
        u = User.get(id=user_id)
        if org_id:
            org = u.organisations.where(Organisation.id == org_id).first()
            if org:
                return jsonify(model_to_dict(org))
            return jsonify({"error": f"Not Found Organisation with ID: {org_id}"}), 404
        return jsonify({"user-orgs": list(u.organisations.dicts())})
    except User.DoesNotExist:
        return jsonify({"error": f"Not Found user with ID: {user_id}"}), 404
    except Exception as ex:
        app.logger.exception(f"Failed to retrieve user (ID: {user_id}) organisations.")
        return jsonify({
            "error": f"Failed to retrieve user (ID: {user_id}) organisations: {ex}."
        }), 500


@app.route(
    "/hub/api/v0.1/users/<int:user_id>/orgs/<int:org_id>",
    methods=[
        "DELETE",
        "PATCH",
        "POST",
        "PUT",
    ])
@app.route(
    "/hub/api/v0.1/users/<int:user_id>/orgs/", methods=[
        "DELETE",
        "PATCH",
        "POST",
        "PUT",
    ])
@roles_required(Role.SUPERUSER, Role.ADMIN)
def user_orgs_org(user_id, org_id=None):
    """Add an organisation to the user.

    Recieves:
    {"id": N, "is_admin": true/false, "is_tech_contact": true/false, ...}

    Where: id - the organisation ID.

    If the user is already linked to the organisation, the entry gets only updated.

    If another user is the tech.contact of the organisation, the existing user
    should be demoted.

    Returns: user_org entry

    """
    data = request.json
    if not org_id and not (data and data.get("id")):
        return jsonify({"error": "NOT DATA"}), 400
    if not org_id:
        org_id = data.get("id")
    if request.method == "DELETE":
        UserOrg.delete().where((UserOrg.user_id == user_id) & (UserOrg.org_id == org_id)).execute()
        user = User.get(id=user_id)
        if user.organisation_id == org_id:
            user.organisation_id = None
            user.save()
        return jsonify({
            "user-org": data,
            "status": "DELETED",
        })
    else:
        org = Organisation.get(id=org_id)
        uo, created = UserOrg.get_or_create(user_id=user_id, org_id=org_id)
        if "is_admin" in data and uo.is_admin != data["is_admin"]:
            uo.is_admin = data["is_admin"]
            uo.save()
        if "is_tech_contact" in data:
            user = User.get(id=user_id)
            if data["is_tech_contact"]:
                org.tech_contact = user
            elif org.tech_contact == user:
                org.tech_contact_id = None
            org.save()
        return jsonify({
            "org": model_to_dict(org, recurse=False),
            "user_org": model_to_dict(uo, recurse=False),
            "status": ("CREATED" if created else "UPDATED"),
        }), (201 if created else 200)
