"""Application views."""

import csv
import itertools
import json
import math
import mimetypes
import os
import secrets
import traceback
from datetime import datetime
from io import BytesIO

import requests
import tablib
import yaml
from flask import (Response, abort, flash, jsonify, redirect, render_template, request, send_file,
                   send_from_directory, stream_with_context, url_for)
from flask_admin._compat import csv_encode
from flask_admin.actions import action
from flask_admin.babel import gettext
from flask_admin.base import expose
from flask_admin.contrib.peewee import ModelView, filters
from flask_admin.contrib.peewee.form import CustomModelConverter
from flask_admin.contrib.peewee.view import save_inline
from flask_admin.form import SecureForm, rules
from flask_admin.helpers import get_redirect_target
from flask_admin.model import BaseModelView, typefmt
from flask_login import current_user, login_required
from flask_rq2.job import FlaskJob
from jinja2 import Markup
from orcid_api.rest import ApiException
from playhouse.shortcuts import model_to_dict
from peewee import SQL
from werkzeug.utils import secure_filename
from wtforms.fields import BooleanField
from urllib.parse import parse_qs, urlparse
from wtforms import validators

from . import SENTRY_DSN, admin, app, cache, limiter, models, orcid_client, rq, utils
from .apis import yamlfy
from .forms import (AddressForm, ApplicationFrom, BitmapMultipleValueField, CredentialForm, EmailTemplateForm,
                    ExternalIdentifierForm, FileUploadForm, FundingForm, GroupIdForm, LogoForm, OrgRegistrationForm,
                    OtherNameKeywordForm, PartialDateField, PeerReviewForm, ProfileSyncForm,
                    RecordForm, ResearcherUrlForm, UserInvitationForm, WebhookForm, WorkForm,
                    validate_orcid_id_field)
from .login_provider import roles_required
from .models import (JOIN, Affiliation, AffiliationRecord, AffiliationExternalId, CharField, Client, Delegate,
                     ExternalId, FixedCharField, File, FundingContributor, FundingInvitee, FundingRecord,
                     Grant, GroupIdRecord, ModelException, NestedDict, OtherIdRecord, OrcidApiCall, OrcidToken,
                     Organisation, OrgInfo, OrgInvitation, PartialDate, PropertyRecord,
                     PeerReviewExternalId, PeerReviewInvitee, PeerReviewRecord,
                     Role, Task, TaskType, TextField, Token, Url, User, UserInvitation, UserOrg,
                     UserOrgAffiliation, WorkContributor, WorkExternalId, WorkInvitee, WorkRecord,
                     db, get_val)
# NB! Should be disabled in production
from .pyinfo import info
from .utils import get_next_url, read_uploaded_file, send_user_invitation

HEADERS = {"Accept": "application/vnd.orcid+json", "Content-type": "application/vnd.orcid+json"}
ORCID_BASE_URL = app.config["ORCID_BASE_URL"]


@app.errorhandler(401)
def unauthorized(e):
    """Handle Unauthorized (401)."""
    _next = get_next_url()
    if _next:
        flash(
            "You have not been authenticated, or do not have the necessary permissions to access this page",
            "danger")
        return redirect(_next)
    return render_template("401.html"), 401


@app.errorhandler(403)
def forbidden(e):
    """Handle Forbidden (403)."""
    _next = get_next_url()
    if _next:
        flash("Page Not Found", "danger")
        flash(
            "You might not have the necessary permissions to access this page.",
            "danger")
        return redirect(_next)
    return render_template("403.html"), 403


@app.errorhandler(404)
def page_not_found(e):
    """Handle nonexistin pages."""
    _next = get_next_url()
    if _next:
        flash("Page Not Found", "danger")
        return redirect(_next)
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle internal error."""
    trace = traceback.format_exc()
    if SENTRY_DSN:
        from sentry_sdk import last_event_id
        return render_template(
            "500.html",
            trace=trace,
            error_message=str(error),
            sentry_event_id=last_event_id())
    else:
        return render_template("500.html", trace=trace, error_message=str(error))


@app.route("/favicon.ico")
def favicon():
    """Support for the "favicon" legacy: favicon location in the root directory."""
    return send_from_directory(
        os.path.join(app.root_path, "static", "images"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon")


@app.route("/status")
@limiter.limit("30/minute")
def status():
    """Check the application health status attempting to connect to the DB.

    NB! This entry point should be protected and accessible
    only form the application monitoring servers.
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


@app.route("/pyinfo/<message>")
@app.route("/pyinfo")
@roles_required(Role.SUPERUSER)
def pyinfo(message=None):
    """Show Python and runtime environment and settings or test exception handling."""
    if message:
        raise Exception(message)
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


def orcid_link_formatter(view, context, model, name):
    """Format ORCID ID for ModelViews."""
    if not model.orcid:
        return ""
    return Markup(f'<a href="{ORCID_BASE_URL}{model.orcid}" target="_blank">{model.orcid}</a>')


class AppCustomModelConverter(CustomModelConverter):
    """Customized field mapping to revove the extra validator.
    This is a workaround for https://github.com/coleifer/wtf-peewee/issues/48.
    TODO: remove it as soon as the issue gets resoved.
    """

    def convert(self, model, field, field_args):
        """Remove the 'Required' validator if the model field is optional."""
        fi = super().convert(model, field, field_args)
        if field.null and field.choices:
            for v in fi.field.kwargs.get("validators", []):
                if isinstance(v, validators.Required):
                    fi.field.kwargs["validators"].remove(v)
                    break

        return fi


class AppModelView(ModelView):
    """ModelView customization."""

    roles = {1: "Superuser", 2: "Administrator", 4: "Researcher", 8: "Technical Contact"}
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
    form_args = dict(
            roles=dict(choices=roles.items()),
            email=dict(validators=[validators.email()]),
            orcid=dict(validators=[validate_orcid_id_field]))

    if app.config["ENV"] not in ["dev", "test", "dev0", ] and not app.debug:
        form_base_class = SecureForm

    column_formatters = dict(
        roles=lambda v, c, m, p: ", ".join(n for r, n in v.roles.items() if r & m.roles),
        orcid=orcid_link_formatter)
    column_default_sort = "id"
    column_labels = dict(org="Organisation", orcid="ORCID iD")
    column_type_formatters = dict(typefmt.BASE_FORMATTERS)
    column_type_formatters.update({datetime: lambda view, value: isodate(value)})
    column_type_formatters_export = dict(typefmt.EXPORT_FORMATTERS)
    column_type_formatters_export.update({PartialDate: lambda view, value: str(value)})
    column_formatters_export = dict(orcid=lambda v, c, m, p: m.orcid)
    column_exclude_list = (
        "updated_at",
        "updated_by",
    )
    form_overrides = dict(start_date=PartialDateField, end_date=PartialDateField)
    form_widget_args = {c: {"readonly": True} for c in column_exclude_list}
    form_excluded_columns = ["created_at", "updated_at", "created_by", "updated_by"]
    model_form_converter = AppCustomModelConverter

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

    # TODO: remove when it gets merged into the upstream repo (it's a workaround to make
    # joins LEFT OUTER)
    def _handle_join(self, query, field, joins):
        if field.model_class != self.model:
            model_name = field.model_class.__name__

            if model_name not in joins:
                query = query.join(field.model_class, "LEFT OUTER")
                joins.add(model_name)

        return query

    def get_one(self, rec_id):
        """Handle missing data."""
        try:
            return super().get_one(rec_id)
        except self.model.DoesNotExist:
            flash(f"The record with given ID: {rec_id} doesn't exist or it has been deleted.", "danger")
            abort(404)

    def init_search(self):
        """Include linked columns in the search if they are defined with 'liked_table.column'."""
        if self.column_searchable_list:
            for p in self.column_searchable_list:

                if isinstance(p, str):
                    if "." in p:
                        m, p = p.split('.')
                        m = getattr(self.model, m).rel_model
                        p = getattr(m, p)
                    else:
                        p = getattr(self.model, p)

                # Check type
                if not isinstance(p, (
                        CharField,
                        TextField,
                )):
                    raise Exception(
                        f'Can only search on text columns. Failed to setup search for "{p}"')

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
            # Show only rows related to the current organisation the user is admin for.
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
        """Workaround for https://github.com/flask-admin/flask-admin/issues/1512."""
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


class AuditLogModelView(AppModelView):
    """Audit Log model view."""

    can_edit = False
    can_delete = False
    can_create = False
    can_view_details = False

    def __init__(self, model, *args, **kwargs):
        """Set up the search list."""
        self.column_searchable_list = [
            f for f in model._meta.fields.values() if isinstance(f, (CharField, FixedCharField, TextField))
        ]
        self.column_filters = [
            filters.DateBetweenFilter(column=model.ts, name="Time-stamp"),
            filters.FilterEqual(
                column=model.op,
                options=[("U", "Updated"), ("D", "Deleted")],
                name="Operation"),
        ]

        super().__init__(model, *args, **kwargs)


class UserAdmin(AppModelView):
    """User model view."""

    roles = {1: "Superuser", 2: "Administrator", 4: "Researcher", 8: "Technical Contact"}
    edit_template = "admin/user_edit.html"

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
    form_ajax_refs = {
        "organisation": {
            "fields": (Organisation.name, "name")
        },
    }
    can_export = True


class OrganisationAdmin(AppModelView):
    """Organisation model view."""

    column_formatters = {
        "logo":
        lambda v, c, m, p: Markup(
            '<img style="max-height: 100px; max-width: 100px;" src="'
            f"""{url_for('logo_image', token=m.logo.token)}" alt="the logo of {m.name}">""") if m.logo else ''
    }
    column_exclude_list = (
        "orcid_client_id",
        "orcid_secret",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "email_template",
        "email_template_enabled",
    )
    form_excluded_columns = AppModelView.form_excluded_columns[:]
    form_excluded_columns.append("logo")
    column_searchable_list = (
        "name",
        "tuakiri_name",
        "city",
    )
    form_ajax_refs = {
        "tech_contact": {
            "fields": (User.name, User.email),
            "page_size": 5
        },
    }
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
                        Organisation.tech_contact_id == model.tech_contact_id,
                        Organisation.id != model.id).exists():
                app.logger.info(r"Revoked TECHNICAL from {model.tech_contact}")
                model.tech_contact.roles &= ~Role.TECHNICAL
                model.tech_contact.save()

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
    form_rules = [
        rules.FieldSet(["name", "tuakiri_name"], "Naming"),
        rules.FieldSet(["title", "first_name", "last_name", "role", "email", "phone", "is_public"],
                       "Technical Contact"),
        rules.FieldSet(["country", "city"], "Address"),
        rules.FieldSet(["disambiguated_id", "disambiguation_source"], "Disambiguation Data"),
    ]

    @action("invite", "Register Organisation",
            "Are you sure you want to register selected organisations?")
    def action_invite(self, ids):
        """Batch registration of organisations."""
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


class UserInvitationAdmin(AppModelView):
    """User Invitations."""

    can_export = True
    can_edit = False
    can_delete = False
    can_create = False
    column_searchable_list = (
        "email",
        "organisation",
        "department",
        "first_name",
        "last_name",
        "token",
        "inviter.name",
    )


class OrgInvitationAdmin(AppModelView):
    """User Invitations."""

    can_export = True
    can_edit = False
    can_delete = False
    can_create = False
    column_searchable_list = (
        "email",
        "org.name",
        "token",
        "inviter.name",
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
    can_edit = False
    can_create = False
    can_delete = True
    column_searchable_list = [
        "filename", "created_by.email", "created_by.name", "created_by.first_name",
        "created_by.last_name", "org.name"
    ]
    column_list = [
        "task_type", "filename", "created_at", "org", "completed_at", "created_by", "expires_at",
        "expiry_email_sent_at", "completed_count"
    ]
    # form_excluded_columns = [
    #     "is_deleted", "completed_at", "expires_at", "expiry_email_sent_at", "organisation"
    # ]

    column_filters = (
        filters.DateBetweenFilter(column=Task.created_at, name="Uploaded Date"),
        filters.FilterEqual(column=Task.task_type, options=models.TaskType.options(), name="Task Type"),
    )
    column_formatters = dict(
        task_type=lambda v, c, m, p: m.task_type.name.replace('_', ' ').title(),
        completed_count=lambda v, c, m, p: (
            '' if not m.record_count else f"{m.completed_count} / {m.record_count} ({m.completed_percent:.1f}%)"),
    )


class RecordModelView(AppModelView):
    """Task record model view."""

    roles_required = Role.SUPERUSER | Role.ADMIN
    column_exclude_list = (
        "task",
        "organisation",
    )
    form_excluded_columns = [
        "task",
        "organisation",
        "processed_at",
        "status",
    ]
    column_export_exclude_list = (
        "task",
        "is_active",
    )
    can_edit = True
    can_create = False
    can_delete = True
    can_view_details = True
    can_export = True

    form_widget_args = {"external_id": {"readonly": True}, "task": {"readonly": True}}

    def render(self, template, **kwargs):
        """Pass the task to the render function as an added argument."""
        if template == self.list_template and "task" not in kwargs:
            task_id = request.args.get("task_id")
            if task_id:
                try:
                    kwargs["task"] = Task.get(id=task_id)
                except Task.DoesNotExist:
                    flash(f"The task with ID: {task_id} doesn't exist.", "danger")
                    abort(404)
            else:
                return redirect(request.args.get("url") or url_for("task.index_view"))
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
            task_id = self.current_task_id
            if not task_id:
                _id = request.args.get("id")
                if not _id:
                    flash("Cannot invoke the task view without task ID", "danger")
                    flash("Missing or incorrect task ID value", "danger")
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

        except ValueError as ex:
            flash(str(ex), "danger")
            return False

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

    @models.lazy_property
    def record_processing_func(self):
        """Record processing function."""
        return getattr(utils, f"process_{self.model.underscore_name()}s")

    def enqueue_record(self, record_id):
        """Enqueue the specified record or all active and not yet processed ones."""
        self.record_processing_func.queue(record_id=record_id)

    @action("activate", "Activate for processing",
            """Are you sure you want to activate the selected records for batch processing?
            By clicking "OK" you are affirming that the selected records to be written are,
            to the best of your knowledge, correct!""")
    def action_activate(self, ids):
        """Batch registraion of users."""
        try:
            status = "The record was activated at " + datetime.now().isoformat(timespec="seconds")
            count = self.model.update(is_active=True, status=status).where(
                self.model.is_active == False,  # noqa: E712
                self.model.id.in_(ids)).execute()
            if self.model == AffiliationRecord:
                records = self.model.select().where(self.model.id.in_(ids)).order_by(
                    self.model.email, self.model.orcid)
                for _, chunk in itertools.groupby(records, lambda r: (r.email, r.orcid, )):
                    self.enqueue_record([r.id for r in chunk])
            else:
                for record_id in ids:
                    self.enqueue_record(record_id)

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
        task_id = None
        with db.atomic():
            try:
                if request.method == "POST" and request.form.get("rowid"):
                    # get the first ROWID:
                    rowid = int(request.form.get("rowid"))
                    task_id = self.model.get(id=rowid).task_id
                else:
                    task_id = request.form.get('task_id')
                task = Task.get(id=task_id)

                count = self.model.update(
                    processed_at=None, status=status).where(self.model.is_active,
                                                            self.model.id.in_(ids)).execute()

                if hasattr(self.model, "invitees"):
                    im = self.model.invitees.rel_model
                    count = im.update(
                        processed_at=None, status=status).where(im.record.in_(ids)).execute()
                    emails = im.select(im.email).where(im.record_id.in_(ids))
                else:
                    emails = self.model.select(self.model.email).where(self.model.id.in_(ids))
                # Delete the userInvitation token for selected reset items.
                UserInvitation.delete().where(UserInvitation.email.in_(emails)).execute()

                for record_id in ids:
                    self.enqueue_record(record_id)

            except Exception as ex:
                db.rollback()
                flash(f"Failed to activate the selected records: {ex}")
                app.logger.exception("Failed to activate the selected records")

            else:
                task.expires_at = None
                task.expiry_email_sent_at = None
                task.completed_at = None
                task.save()
                flash(
                    f"{count} {task.task_type.name} records were reset and/or updated for batch processing."
                )

    def create_form(self):
        """Prefill form with organisation default values."""
        form = super().create_form()
        if request.method == "GET":
            org = current_user.organisation
            if hasattr(form, "org_name"):
                form.org_name.data = org.name
            if hasattr(form, "city"):
                form.city.data = org.city
            if hasattr(form, "state"):
                form.state.data = org.state
            if hasattr(form, "country"):
                form.country.data = org.country
            if hasattr(form, "disambiguated_id"):
                form.disambiguated_id.data = org.disambiguated_id
            if hasattr(form, "disambiguation_source"):
                form.disambiguation_source.data = org.disambiguation_source
        return form

    @property
    def current_task_id(self):
        """Get task_id form the query pameter task_id or url."""
        try:
            task_id = request.args.get("task_id")
            if task_id:
                return int(task_id)
            url = request.args.get("url")
            if not url:
                flash("Missing return URL.", "danger")
                return False
            qs = parse_qs(urlparse(url).query)
            task_id = qs.get("task_id", [None])[0]
            if task_id:
                return int(task_id)
        except:
            return None

    def create_model(self, form):
        """Link model to the current task."""
        task_id = self.current_task_id
        if not task_id:
            flash("Missing task ID.", "danger")
            return False

        try:
            model = self.model(task_id=task_id)
            form.populate_obj(model)
            self._on_model_change(form, model, True)
            model.save()

            # For peewee have to save inline forms after model was saved
            save_inline(form, model)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(f"Failed to create record: {ex}", "danger")
                app.log.exception("Failed to create record.")

            return False
        else:
            self.after_model_change(form, model, True)
        if model.is_active:
            self.enqueue_record(model.id)

        return model

    def update_model(self, form, model):
        """Handle change of the record. Enqueue the record if got activated."""
        is_active = model.is_active
        update_resp = super().update_model(form, model)
        if update_resp and not is_active and model.is_active:
            self.enqueue_record(model.id)
        return update_resp


class RecordChildAdmin(AppModelView):
    """Batch processing record child model common bits."""

    roles_required = Role.SUPERUSER | Role.ADMIN
    list_template = "record_child_list.html"

    can_edit = True
    can_create = True
    can_delete = True
    can_view_details = True

    column_exclude_list = ["record"]
    form_excluded_columns = ["record", "record", "status", "processed_at"]
    column_details_exclude_list = ["record"]

    def is_accessible(self):
        """Verify if the view is accessible for the current user."""
        if not super().is_accessible():
            flash("Access denied! You cannot access this record.", "danger")
            return False

        return True

    @property
    def current_record_id(self):
        """Get record_id form the query pameter record_id or url."""
        try:
            record_id = request.args.get("record_id")
            if record_id:
                return int(record_id)
            url = request.args.get("url")
            if not url:
                flash("Missing return URL.", "danger")
                return None
            qs = parse_qs(urlparse(url).query)
            record_id = qs.get("record_id", [None])[0]
            if record_id:
                return int(record_id)
        except:
            return None

    def create_model(self, form):
        """Link model to the current record."""
        record_id = self.current_record_id
        if not record_id:
            flash("Missing record ID.", "danger")
            return False

        try:
            model = self.model()
            form.populate_obj(model)
            model.record_id = record_id
            self._on_model_change(form, model, True)
            model.save()

            # For peewee have to save inline forms after model was saved
            save_inline(form, model)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(f"Failed to create record: {ex}", "danger")
                app.log.exception("Failed to create record.")

            return False
        else:
            self.after_model_change(form, model, True)

        return model


class ExternalIdAdmin(RecordChildAdmin):
    """Combine ExternalId model view."""

    can_edit = True
    can_create = True
    can_delete = True
    can_view_details = True

    form_widget_args = {"external_id": {"readonly": True}}

    def is_accessible(self):
        """Verify if the external id's view is accessible for the current user."""
        if not super().is_accessible():
            flash("Access denied! You cannot access this task.", "danger")
            return False

        return True


class InviteeAdmin(RecordChildAdmin):
    """Combine Invitees record model view."""

    @action("reset", "Reset for processing",
            "Are you sure you want to reset the selected records for batch processing?")
    def action_reset(self, ids):
        """Batch reset of users."""
        with db.atomic():
            try:
                status = " The record was reset at " + datetime.utcnow().isoformat(timespec="seconds")
                count = self.model.update(
                    processed_at=None, status=status).where(self.model.id.in_(ids)).execute()
                record_id = self.model.select().where(
                    self.model.id.in_(ids))[0].record_id
                rec_class = self.model.record.rel_model
                rec_class.update(
                    processed_at=None, status=status).where(
                    rec_class.is_active, rec_class.id == record_id).execute()
                getattr(utils, f"process_{rec_class.underscore_name()}s").queue(record_id)
            except Exception as ex:
                db.rollback()
                flash(f"Failed to activate the selected records: {ex}")
                app.logger.exception("Failed to activate the selected records")
            else:
                flash(f"{count} invitee records were reset for batch processing.")


class CompositeRecordModelView(RecordModelView):
    """Common view for Funding, Work and Peer review model."""

    column_export_exclude_list = (
        "task",
        "is_active",
        "status",
        "processed_at",
        "created_at",
        "updated_at",
    )

    export_types = [
        "tsv",
        "yaml",
        "json",
        "csv",
    ]

    def _export_tablib(self, export_type, return_url):
        """Override export functionality to integrate funding/work/peer review invitees with external ids."""
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
        if self.model == PeerReviewRecord:
            self._export_columns = [(v, v.replace('_', '-')) for v in
                                    ['invitees', 'review_group_id', 'review_url', 'reviewer_role', 'review_type',
                                     'review_completion_date', 'subject_external_identifier', 'subject_container_name',
                                     'subject_type', 'subject_name', 'subject_url', 'convening_organization',
                                     'review_identifiers']]
        elif self.model == FundingRecord:
            self._export_columns = [(v, v.replace('_', '-')) for v in
                                    ['invitees', 'title', 'type', 'organization_defined_type', 'short_description',
                                     'amount', 'start_date', 'end_date', 'organization', 'contributors',
                                     'external_ids']]
        elif self.model == WorkRecord:
            self._export_columns = [(v, v.replace('_', '-')) for v in
                                    ['invitees', 'title', 'journal_title', 'short_description', 'citation', 'type',
                                     'publication_date', 'url', 'language_code', 'country', 'contributors',
                                     'external_ids']]
        ds = tablib.Dataset(headers=[c[1] for c in self._export_columns])

        count, data = self._export_data()

        for row in data:
            vals = self.expected_format(row)
            ds.append(vals)

        try:
            try:
                ds.yaml = yaml.safe_dump(json.loads(ds.json.replace("]\\", "]").replace("\\n", " ")))
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

    def expected_format(self, row):
        """Get expected export format for funding/work/peer_review records."""
        vals = []
        for c in self._export_columns:
            if c[0] == "invitees":
                invitee_list = []

                for f in row.invitees:
                    invitees_rec = {}
                    invitees_rec['identifier'] = self.get_export_value(f, 'identifier')
                    invitees_rec['email'] = self.get_export_value(f, 'email')
                    invitees_rec['first-name'] = self.get_export_value(f, 'first_name')
                    invitees_rec['last-name'] = self.get_export_value(f, 'last_name')
                    invitees_rec['ORCID-iD'] = self.get_export_value(f, 'orcid')
                    invitees_rec['put-code'] = int(self.get_export_value(f, 'put_code')) if \
                        self.get_export_value(f, 'put_code') else None
                    invitees_rec['visibility'] = self.get_export_value(f, 'visibility')
                    invitee_list.append(invitees_rec)
                vals.append(invitee_list)
            elif c[0] in ['review_completion_date', 'start_date', 'end_date', 'publication_date']:
                vals.append(PartialDate.create(self.get_export_value(row, c[0])).as_orcid_dict()
                            if self.get_export_value(row, c[0]) else None)
            elif c[0] == "subject_external_identifier":
                subject_dict = {}
                subject_dict['external-id-type'] = self.get_export_value(row, 'subject_external_id_type')
                subject_dict['external-id-value'] = self.get_export_value(row, 'subject_external_id_value')
                subject_dict['external-id-url'] = dict(value=self.get_export_value(row, 'subject_external_id_url'))
                subject_dict['external-id-relationship'] = self.get_export_value(row,
                                                                                 'subject_external_id_relationship')
                vals.append(subject_dict)
            elif c[0] == "subject_name":
                subject_name_dict = dict()
                translated_title = dict()
                subject_name_dict['title'] = dict(value=self.get_export_value(row, 'subject_name_title'))
                subject_name_dict['subtitle'] = dict(value=self.get_export_value(row, 'subject_name_subtitle'))
                translated_title['language-code'] = self.get_export_value(row,
                                                                          'subject_name_translated_title_lang_code')
                translated_title['value'] = csv_encode(self.get_export_value(row, 'subject_name_translated_title'))
                subject_name_dict['translated-title'] = translated_title
                vals.append(subject_name_dict)
            elif c[0] in ["convening_organization", "organization"]:
                convening_org_dict = dict()
                disambiguated_dict = dict()
                convening_org_dict['name'] = self.get_export_value(row, 'convening_org_name') or self.get_export_value(
                    row, 'org_name')
                convening_org_dict['address'] = dict(
                    city=self.get_export_value(row, 'convening_org_city') or self.get_export_value(row, 'city'),
                    region=self.get_export_value(row, 'convening_org_region') or self.get_export_value(row, 'region'),
                    country=self.get_export_value(row, 'convening_org_country') or self.get_export_value(row,
                                                                                                         'country'))
                disambiguated_dict['disambiguated-organization-identifier'] = \
                    self.get_export_value(row, 'convening_org_disambiguated_identifier') or \
                    self.get_export_value(row, 'disambiguated_id')
                disambiguated_dict['disambiguation-source'] = self.get_export_value(
                    row, 'convening_org_disambiguation_source') or self.get_export_value(row, 'disambiguation_source')
                convening_org_dict['disambiguated-organization'] = disambiguated_dict
                vals.append(convening_org_dict)
            elif c[0] in ["review_identifiers", "external_ids"]:
                external_ids_list = []
                external_dict = {}
                external_ids_data = row.external_ids
                for f in external_ids_data:
                    external_id_dict = {}
                    external_id_dict['external-id-type'] = self.get_export_value(f, 'type')
                    external_id_dict['external-id-value'] = self.get_export_value(f, 'value')
                    external_id_dict['external-id-relationship'] = self.get_export_value(f, 'relationship')
                    external_id_dict['external-id-url'] = dict(value=self.get_export_value(f, 'url'))
                    external_ids_list.append(external_id_dict)
                external_dict['external-id'] = external_ids_list
                vals.append(external_dict)
            elif c[0] == "title":
                title_dict = dict()
                translated_title = dict()
                title_dict['title'] = dict(value=self.get_export_value(row, 'title'))
                if self.model == WorkRecord:
                    title_dict['subtitle'] = dict(value=self.get_export_value(row, 'subtitle'))
                translated_title['language-code'] = self.get_export_value(row, 'translated_title_language_code')
                translated_title['value'] = csv_encode(self.get_export_value(row, 'translated_title'))
                title_dict['translated-title'] = translated_title
                vals.append(title_dict)
            elif c[0] == "amount":
                amount_dict = dict()
                amount_dict['currency-code'] = self.get_export_value(row, 'currency')
                amount_dict['value'] = csv_encode(self.get_export_value(row, 'amount'))
                vals.append(amount_dict)
            elif c[0] == "citation":
                citation_dict = dict()
                citation_dict['citation-type'] = self.get_export_value(row, 'citation_type')
                citation_dict['citation-value'] = csv_encode(self.get_export_value(row, 'citation_value'))
                vals.append(citation_dict)
            elif c[0] == "contributors":
                contributors_list = []
                contributors_dict = {}
                contributors_data = row.contributors
                for f in contributors_data:
                    contributor_dict = {}
                    contributor_dict['contributor-attributes'] = {'contributor-role': self.get_export_value(f, 'role')}
                    if self.model == WorkRecord:
                        contributor_dict['contributor-attributes'].update(
                            {'contributor-sequence': self.get_export_value(f, 'contributor_sequence')})
                    contributor_dict['contributor-email'] = dict(value=self.get_export_value(f, 'email'))
                    contributor_dict['credit-name'] = dict(value=self.get_export_value(f, 'name'))
                    contributor_dict['contributor-orcid'] = dict(path=self.get_export_value(f, 'orcid'))
                    contributors_list.append(contributor_dict)
                contributors_dict['contributor'] = contributors_list
                vals.append(contributors_dict)
            else:
                requires_nested_value = ['review_url', 'subject_container_name', 'subject_url', 'journal_title', 'url',
                                         'organization_defined_type', 'country']
                if c[0] in requires_nested_value:
                    vals.append(dict(value=self.get_export_value(row, c[0])))
                else:
                    vals.append(csv_encode(self.get_export_value(row, c[0])))
        return vals

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

        # Grab parameters from URL
        view_args = self._get_list_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(view_args.sort)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get count and data
        count, query = self.get_record_list(
            0,
            sort_column,
            view_args.sort_desc,
            view_args.search,
            view_args.filters,
            page_size=self.export_max_rows,
            execute=False)

        # https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
        class Echo(object):
            """An object that implements just the write method of the file-like interface."""

            def write(self, value):
                """Write the value by returning it, instead of storing in a buffer."""
                return value

        writer = csv.writer(Echo(), delimiter=delimiter)

        def generate():
            # Append the column titles at the beginning
            titles = [csv_encode(c[1]) for c in self._export_columns]
            yield writer.writerow(titles)

            for row in query:
                vals = [csv_encode(self.get_export_value(row, c[0]))
                        for c in self._export_columns]
                yield writer.writerow(vals)

        filename = self.get_export_name(export_type=export_type)

        disposition = 'attachment;filename=%s' % (secure_filename(filename), )

        return Response(
            stream_with_context(generate()),
            headers={'Content-Disposition': disposition},
            mimetype='text/' + export_type)


class FundingRecordAdmin(CompositeRecordModelView):
    """Funding record model view."""

    column_exclude_list = ("task", "translated_title_language_code", "short_description", "disambiguation_source")
    can_create = True
    column_searchable_list = ("title",)
    list_template = "funding_record_list.html"
    column_export_list = (
        "funding_id",
        "identifier",
        "put_code",
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
        "disambiguated_id",
        "disambiguation_source",
        "visibility",
        "orcid",
        "email",
        "first_name",
        "last_name",
        "external_id_type",
        "external_id_url",
        "external_id_relationship",
        "status",)

    def get_record_list(self, page, sort_column, sort_desc, search, filters, execute=True, page_size=None):
        """Return records and realated to the record data."""
        count, query = self.get_list(
            0,
            sort_column,
            sort_desc,
            search,
            filters,
            page_size=page_size,
            execute=False)

        ext_ids = [r.id for r in
                   ExternalId.select(models.fn.min(ExternalId.id).alias("id")).join(FundingRecord).where(
                       FundingRecord.task == self.current_task_id).group_by(FundingRecord.id).naive()]

        return count, query.select(
            self.model,
            FundingInvitee.email,
            FundingInvitee.orcid,
            FundingInvitee.identifier,
            FundingInvitee.first_name,
            FundingInvitee.last_name,
            FundingInvitee.put_code,
            FundingInvitee.visibility,
            ExternalId.type.alias("external_id_type"),
            ExternalId.value.alias("funding_id"),
            ExternalId.url.alias("external_id_url"),
            ExternalId.relationship.alias("external_id_relationship"),
        ).join(
            ExternalId,
            JOIN.LEFT_OUTER,
            on=(ExternalId.record_id == self.model.id)).where(ExternalId.id << ext_ids).join(
            FundingInvitee,
            JOIN.LEFT_OUTER,
            on=(FundingInvitee.record_id == self.model.id)).naive()


class WorkRecordAdmin(CompositeRecordModelView):
    """Work record model view."""

    column_exclude_list = ("task", "translated_title_language_code", "short_description", "citation_value")
    can_create = True
    column_searchable_list = ("title",)
    list_template = "work_record_list.html"
    form_overrides = dict(publication_date=PartialDateField)

    column_export_list = [
        "work_id",
        "put_code",
        "title",
        "subtitle",
        "translated_title",
        "translated_title_language_code",
        "journal_title",
        "short_description",
        "citation_type",
        "citation_value",
        "type",
        "publication_date",
        "publication_media_type",
        "url",
        "language_code",
        "country",
        "visibility",
        "orcid",
        "email",
        "identifier",
        "first_name",
        "last_name",
        "external_id_type",
        "external_id_url",
        "external_id_relationship",
        "status",
    ]

    def get_record_list(self, page, sort_column, sort_desc, search, filters, execute=True, page_size=None):
        """Return records and realated to the record data."""
        count, query = self.get_list(
            0,
            sort_column,
            sort_desc,
            search,
            filters,
            page_size=page_size,
            execute=False)

        ext_ids = [r.id for r in
                   WorkExternalId.select(models.fn.min(WorkExternalId.id).alias("id")).join(WorkRecord).where(
                       WorkRecord.task == self.current_task_id).group_by(WorkRecord.id).naive()]

        return count, query.select(
            self.model,
            WorkInvitee.email,
            WorkInvitee.orcid,
            WorkInvitee.identifier,
            WorkInvitee.first_name,
            WorkInvitee.last_name,
            WorkInvitee.put_code,
            WorkInvitee.visibility,
            WorkExternalId.type.alias("external_id_type"),
            WorkExternalId.value.alias("work_id"),
            WorkExternalId.url.alias("external_id_url"),
            WorkExternalId.relationship.alias("external_id_relationship"),
        ).join(
            WorkExternalId,
            JOIN.LEFT_OUTER,
            on=(WorkExternalId.record_id == self.model.id)).where(WorkExternalId.id << ext_ids).join(
            WorkInvitee,
            JOIN.LEFT_OUTER,
            on=(WorkInvitee.record_id == self.model.id)).naive()


class PeerReviewRecordAdmin(CompositeRecordModelView):
    """Peer Review record model view."""

    column_exclude_list = (
        "task", "subject_external_id_type", "external_id_type", "convening_org_disambiguation_source")
    can_create = True
    column_searchable_list = ("review_group_id", )
    list_template = "peer_review_record_list.html"
    form_overrides = dict(review_completion_date=PartialDateField)

    form_rules = [
        rules.FieldSet([
            "review_group_id", "reviewer_role", "review_url", "review_type",
            "review_completion_date"
        ], "Review Group"),
        rules.FieldSet([
            "subject_external_id_type", "subject_external_id_value", "subject_external_id_url",
            "subject_external_id_relationship", "subject_container_name", "subject_type",
            "subject_name_title", "subject_name_subtitle",
            "subject_name_translated_title_lang_code", "subject_name_translated_title",
            "subject_url"
        ], "Subject"),
        rules.FieldSet([
            "convening_org_name", "convening_org_city", "convening_org_region",
            "convening_org_country", "convening_org_disambiguated_identifier",
            "convening_org_disambiguation_source"
        ], "Convening Organisation"),
        "is_active",
    ]

    column_export_list = [
        "review_group_id",
        "reviewer_role",
        "review_url",
        "review_type",
        "review_completion_date",
        "subject_external_id_type",
        "subject_external_id_value",
        "subject_external_id_url",
        "subject_external_id_relationship",
        "subject_container_name",
        "subject_type",
        "subject_name_title",
        "subject_name_subtitle",
        "subject_name_translated_title_lang_code",
        "subject_name_translated_title",
        "subject_url",
        "convening_org_name",
        "convening_org_city",
        "convening_org_region",
        "convening_org_country",
        "convening_org_disambiguated_identifier",
        "convening_org_disambiguation_source",
        "email",
        "orcid",
        "identifier",
        "first_name",
        "last_name",
        "put_code",
        "visibility",
        "external_id_type",
        "peer_review_id",
        "external_id_url",
        "external_id_relationship",
    ]

    def get_record_list(self,
                        page,
                        sort_column,
                        sort_desc,
                        search,
                        filters,
                        execute=True,
                        page_size=None):
        """Return records and realated to the record data."""
        count, query = self.get_list(
            0, sort_column, sort_desc, search, filters, page_size=page_size, execute=False)

        ext_ids = [r.id for r in
                   PeerReviewExternalId.select(models.fn.min(PeerReviewExternalId.id).alias("id")).join(
                       PeerReviewRecord).where(
                       PeerReviewRecord.task == self.current_task_id).group_by(PeerReviewRecord.id).naive()]

        return count, query.select(
            self.model,
            PeerReviewInvitee.email,
            PeerReviewInvitee.orcid,
            PeerReviewInvitee.identifier,
            PeerReviewInvitee.first_name,
            PeerReviewInvitee.last_name,
            PeerReviewInvitee.put_code,
            PeerReviewInvitee.visibility,
            PeerReviewExternalId.type.alias("external_id_type"),
            PeerReviewExternalId.value.alias("peer_review_id"),
            PeerReviewExternalId.url.alias("external_id_url"),
            PeerReviewExternalId.relationship.alias("external_id_relationship"),
        ).join(
            PeerReviewExternalId,
            JOIN.LEFT_OUTER,
            on=(PeerReviewExternalId.record_id == self.model.id)).where(PeerReviewExternalId.id << ext_ids).join(
                PeerReviewInvitee,
                JOIN.LEFT_OUTER,
                on=(PeerReviewInvitee.record_id == self.model.id)).naive()


class AffiliationRecordAdmin(RecordModelView):
    """Affiliation record model view."""

    can_create = True
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
    form_widget_args = {"task": {"readonly": True}}

    def validate_form(self, form):
        """Validate the input."""
        if request.method == "POST" and hasattr(form, "orcid") and hasattr(
                form, "email") and hasattr(form, "put_code"):
            if not (form.orcid.data or form.email.data or form.put_code.data):
                flash(
                    "Either <b>email</b>, <b>ORCID iD</b>, or <b>put-code</b> should be provided.",
                    "danger")
                return False
        return super().validate_form(form)

    @expose("/export/<export_type>/")
    def export(self, export_type):
        """Check the export type whether it is csv, tsv or other format."""
        if export_type not in ["json", "yaml", "yml"]:
            return super().export(export_type)
        return_url = get_redirect_target() or self.get_url(".index_view")

        task_id = self.current_task_id
        if not task_id:
            flash("Missing task ID.", "danger")
            return redirect(return_url)

        if not self.can_export or (export_type not in self.export_types):
            flash("Permission denied.", "danger")
            return redirect(return_url)

        data = Task.get(int(task_id)).to_dict()
        if export_type == "json":
            resp = jsonify(data)
        else:
            resp = yamlfy(data)

        resp.headers[
            "Content-Disposition"] = f"attachment;filename={secure_filename(self.get_export_name(export_type))}"
        return resp


class ProfilePropertyRecordAdmin(AffiliationRecordAdmin):
    """Researcher Url, Other Name, and Keyword record model view."""

    def __init__(self, model_class, *args, **kwargs):
        """Set up model specific attributes."""
        self.column_searchable_list = [
            f for f in ["content", "name", "value", "first_name", "last_name", "email"]
            if f in model_class._meta.fields
        ]
        super().__init__(model_class, *args, **kwargs)


class ViewMembersAdmin(AppModelView):
    """Organisation member model (User beloging to the current org.admin oganisation) view."""

    roles_required = Role.SUPERUSER | Role.ADMIN
    list_template = "viewMembers.html"
    edit_template = "admin/member_edit.html"
    form_columns = ["name", "orcid", "email", "eppn"]
    form_widget_args = {c: {"readonly": True} for c in form_columns if c != "email"}
    column_list = ["email", "orcid", "created_at", "updated_at", "orcid_updated_at"]
    column_formatters_export = dict(orcid=lambda v, c, m, p: m.orcid)
    column_exclude_list = None
    column_searchable_list = ["email", "orcid", "name", "first_name", "last_name"]
    column_export_list = ("email", "eppn", "orcid")
    model = User
    can_edit = True
    can_create = False
    can_delete = True
    can_view_details = False
    can_export = True
    column_filters = (
        filters.DateBetweenFilter(column=User.created_at, name="Registration Date"),
        filters.DateBetweenFilter(column=User.updated_at, name="Update Date"),
        filters.DateBetweenFilter(column=User.orcid_updated_at, name="ORCID Update Date"),
    )
    column_labels = {"created_at": "Registered At"}

    def get_query(self):
        """Get quiery for the user belonging to the organistation of the current user."""
        return current_user.organisation.users

    def _order_by(self, query, joins, order):
        """Add ID for determenistic order of rows if sorting is by NULLable field."""
        query, joins = super()._order_by(query, joins, order)
        # add ID only if all fields are NULLable (exlcude ones given by str):
        if all(not isinstance(f, str) and f.null for (f, _) in order):
            clauses = query._order_by
            clauses.append(self.model.id.desc() if order[0][1] else self.model.id)
            query = query.order_by(*clauses)
        return query, joins

    def get_one(self, rec_id):
        """Limit access only to the userers belonging to the current organisation."""
        try:
            user = User.get(id=rec_id)
            if not user.organisations.where(UserOrg.org == current_user.organisation).exists():
                flash("Access Denied!", "danger")
                abort(403)
            return user
        except User.DoesNotExist:
            flash(f"The user with given ID: {rec_id} doesn't exist or it was deleted.", "danger")
            abort(404)

    def delete_model(self, model):
        """Delete a row and revoke all access tokens issues for the organisation."""
        org = current_user.organisation
        token_revoke_url = app.config["ORCID_BASE_URL"] + "oauth/revoke"

        if UserOrg.select().where((UserOrg.user_id == model.id) & (UserOrg.org_id == org.id)
                                  & UserOrg.is_admin).exists():
            flash(
                f"Failed to delete record for {model}, As User appears to be one of the admins. "
                f"Please contact orcid@royalsociety.org.nz for support", "danger")
            return False

        for token in OrcidToken.select().where(OrcidToken.org == org, OrcidToken.user == model):
            try:
                resp = requests.post(token_revoke_url,
                                     headers={"Accepts": "application/json"},
                                     data=dict(client_id=org.orcid_client_id,
                                               client_secret=org.orcid_secret,
                                               token=token.access_token))

                if resp.status_code != 200:
                    flash("Failed to revoke token {token.access_token}: {ex}", "danger")
                    return False

                token.delete_instance(recursive=True)

            except Exception as ex:
                flash(f"Failed to revoke token {token.access_token}: {ex}", "danger")
                app.logger.exception('Failed to delete record.')
                return False

        user_org = UserOrg.select().where(UserOrg.user == model, UserOrg.org == org).first()
        try:
            self.on_model_delete(model)
            if model.organisations.count() < 2:
                model.delete_instance(recursive=True)
            else:
                if model.organisation == user_org.org:
                    model.organisation = model.organisations.first()
                    model.save()
                user_org.delete_instance(recursive=True)

        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to delete record. %(error)s', error=str(ex)), 'danger')
                app.logger.exception('Failed to delete record.')

            return False
        else:
            self.after_model_delete(model)
        return True

    @action("delete", "Delete", "Are you sure you want to delete selected records?")
    def action_delete(self, ids):
        """Delete a record for selected entries."""
        try:
            model_pk = getattr(self.model, self._primary_key)
            count = 0

            query = self.model.select().where(model_pk << ids)

            for m in query:
                if self.delete_model(m):
                    count += 1
            if count:
                flash(
                    gettext(
                        'Record was successfully deleted.%(count)s records were successfully deleted.',
                        count=count), 'success')
        except Exception as ex:
            flash(gettext('Failed to delete records. %(error)s', error=str(ex)), 'danger')

    @action(
        "export_affiliations", "Export Affiliation Records",
        "Are you sure you want to retrieve and export selected records affiliation entries from ORCID?"
    )
    def action_export_affiliations(self, ids):
        """Export all user profile section list (either 'Education' or 'Employment')."""
        tokens = OrcidToken.select(User, OrcidToken).join(
            User, on=(OrcidToken.user_id == User.id)).where(
                OrcidToken.user_id << ids,
                OrcidToken.scopes.contains(orcid_client.READ_LIMITED))
        if not current_user.is_superuser:
            tokens = tokens.where(OrcidToken.org_id == current_user.organisation.id)

        records = []
        for t in tokens:

            try:
                api = orcid_client.MemberAPIV3(user=t.user, access_token=t.access_token)
                profile = api.get_record()
                if not profile:
                    continue
            except ApiException as ex:
                if ex.status == 401:
                    flash(f"User {t.user} has revoked the permissions to update his/her records",
                          "warning")
                else:
                    flash(
                        "Exception when calling ORCID API: \n"
                        + json.loads(ex.body.replace("''", "\"")).get('user-messsage'), "danger")
            except Exception as ex:
                abort(500, ex)

            records = itertools.chain(
                *[[(t.user, s.get(f"{rt}-summary")) for ag in
                   profile.get("activities-summary", f"{rt}s", "affiliation-group", default=[])
                   for s in ag.get("summaries")] for rt in ["employment", "education", "distinction", "membership",
                                                            "service", "qualification", "invited-position"]])

        # https://docs.djangoproject.com/en/1.8/howto/outputting-csv/
        class Echo(object):
            """An object that implements just the write method of the file-like interface."""

            def write(self, value):
                """Write the value by returning it, instead of storing in a buffer."""
                return '' if value is None or value == "None" else value

        writer = csv.writer(Echo(), delimiter=",")

        def generate():
            titles = [
                csv_encode(c) for c in [
                    "Put Code", "First Name", "Last Name", "Email", "ORCID iD", "Affiliation Type",
                    "Role", "Department", "Start Date", "End Date", "City", "State", "Country",
                    "Disambiguated Id", "Disambiguation Source"
                ]
            ]
            yield writer.writerow(titles)

            for row in records:
                u, r = row

                _, orcid, affiliation_type, put_code = r.get("path").split("/")
                yield writer.writerow(
                    csv_encode(v or '') for v in [
                        r.get("put-code"), u.first_name, u.last_name, u.email, orcid,
                        affiliation_type,
                        r.get("role-title"),
                        r.get("department-name"),
                        PartialDate.create(r.get("start-date")),
                        PartialDate.create(r.get("end-date")),
                        r.get("organization", "address", "city"),
                        r.get("organization", "address", "region"),
                        r.get("organization", "address", "country"),
                        r.get("disambiguated-organization",
                              "disambiguated-organization-identifier"),
                        r.get("disambiguated-organization", "disambiguation-source")
                    ])

        return Response(stream_with_context(generate()),
                        headers={"Content-Disposition": "attachment;filename=affiliations.csv"},
                        mimetype="text/csv")


class GroupIdRecordAdmin(AppModelView):
    """GroupIdRecord model view."""

    roles_required = Role.SUPERUSER | Role.ADMIN
    list_template = "viewGroupIdRecords.html"
    can_edit = True
    can_create = True
    can_delete = True

    form_widget_args = {"organisation": {"disabled": True}}
    column_searchable_list = (
        "name",
        "group_id",
    )
    form_excluded_columns = (
        "processed_at",
        "status",
    )

    def create_form(self, obj=None):
        """Preselect the organisation field with Admin's organisation."""
        form = super().create_form()
        form.organisation.data = current_user.organisation
        return form

    @action("Insert/Update Record", "Insert or Update record",
            "Are you sure you want add or update group id record?")
    def action_insert_update(self, ids):
        """Insert/Update GroupID records."""
        count = 0
        with db.atomic():
            for gid in self.model.select().where(self.model.id.in_(ids)):
                try:
                    org = gid.organisation
                    orcid_token = None
                    gid.status = None
                    try:
                        orcid_token = OrcidToken.get(org=org, scopes='/group-id-record/update')
                    except OrcidToken.DoesNotExist:
                        orcid_token = utils.get_client_credentials_token(org=org, scope="/group-id-record/update")
                    except Exception as ex:
                        flash("Something went wrong in ORCID call, "
                              "please contact orcid@royalsociety.org.nz for support", "warning")
                        app.logger.exception(f'Exception occured {ex}')

                    orcid_client.configuration.access_token = orcid_token.access_token
                    api = orcid_client.MemberAPI(org=org, access_token=orcid_token.access_token)

                    put_code, created = api.create_or_update_record_id_group(put_code=gid.put_code,
                                                                             org=org, group_name=gid.name,
                                                                             group_id=gid.group_id,
                                                                             description=gid.description, type=gid.type)

                    if created:
                        gid.add_status_line(f"The group id record was created.")
                    else:
                        gid.add_status_line(f"The group id record was updated.")

                    gid.put_code = put_code
                    count += 1
                except ApiException as ex:
                    if ex.status == 404:
                        gid.put_code = None
                    elif ex.status == 401:
                        orcid_token.delete_instance()
                    flash("Something went wrong in ORCID call, Please try again by making by making necessary changes, "
                          "In case you understand the 'user-message' present in the status field or else "
                          "please contact orcid@royalsociety.org.nz for support", "warning")
                    app.logger.exception(f'Exception occured {ex}')
                    gid.add_status_line(f"ApiException: {ex}")
                except Exception as ex:
                    flash("Something went wrong in ORCID call, "
                          "Please contact orcid@royalsociety.org.nz for support", "warning")
                    app.logger.exception(f'Exception occured {ex}')
                    gid.add_status_line(f"Exception: {ex}")
                finally:
                    gid.processed_at = datetime.utcnow()
                    gid.save()
        flash("%d Record was processed." % count)


admin.add_view(UserAdmin(User))
admin.add_view(OrganisationAdmin(Organisation))
admin.add_view(OrcidTokenAdmin(OrcidToken))
admin.add_view(OrgInfoAdmin(OrgInfo))
admin.add_view(OrcidApiCallAmin(OrcidApiCall))
admin.add_view(UserInvitationAdmin())
admin.add_view(OrgInvitationAdmin())

admin.add_view(TaskAdmin(Task))
admin.add_view(AffiliationRecordAdmin())
admin.add_view(RecordChildAdmin(AffiliationExternalId))
admin.add_view(FundingRecordAdmin())
admin.add_view(RecordChildAdmin(FundingContributor))
admin.add_view(InviteeAdmin(FundingInvitee))
admin.add_view(RecordChildAdmin(ExternalId))
admin.add_view(RecordChildAdmin(WorkContributor))
admin.add_view(RecordChildAdmin(WorkExternalId))
admin.add_view(InviteeAdmin(WorkInvitee))
admin.add_view(WorkRecordAdmin())
admin.add_view(PeerReviewRecordAdmin())
admin.add_view(InviteeAdmin(PeerReviewInvitee))
admin.add_view(RecordChildAdmin(PeerReviewExternalId))
admin.add_view(ProfilePropertyRecordAdmin(PropertyRecord))
admin.add_view(ProfilePropertyRecordAdmin(OtherIdRecord))
admin.add_view(ViewMembersAdmin(name="viewmembers", endpoint="viewmembers"))

admin.add_view(UserOrgAmin(UserOrg))
admin.add_view(AppModelView(Client))
admin.add_view(AppModelView(Grant))
admin.add_view(AppModelView(Token))
admin.add_view(AppModelView(Delegate))
admin.add_view(GroupIdRecordAdmin(GroupIdRecord))

for name, model in models.audit_models.items():
    admin.add_view(AuditLogModelView(model, endpoint=name + "_log"))


@app.template_filter("year_range")
def year_range(entry):
    """Show an interval of employment in years."""
    val = ""

    start_date = entry.get("start_date") or entry.get("start-date")
    if start_date and start_date["year"]["value"]:
        val = start_date["year"]["value"]
    else:
        val = "unknown"
    val += "-"

    end_date = entry.get("end_date") or entry.get("end-date")
    if end_date and end_date["year"]["value"]:
        val += end_date["year"]["value"]
    else:
        val += "present"
    return val


@app.template_filter("orcid")
def user_orcid_id_url(user):
    """Render user ORCID Id URL."""
    return ORCID_BASE_URL + user.orcid if user.orcid else ""


@app.template_filter("isodate")
def isodate(d, sep="&nbsp;", no_time=False):
    """Render date into format YYYY-mm-dd HH:MM."""
    if d:
        if isinstance(d, datetime):
            ts_format = '' if no_time else f"[{sep}]HH:mm"
            return Markup(
                f"""<time datetime="{d.isoformat(timespec='minutes')}" """
                f"""data-toggle="tooltip" title="{d.isoformat(timespec='minutes', sep=' ')} UTC" """
                f"""data-format="YYYY[&#8209;]MM[&#8209;]DD{ts_format}" />""")
        if isinstance(d, str):
            return Markup(f"""<time datetime="{d}" />""")
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
    task_id = request.form.get("task_id")
    task = Task.get(task_id)
    try:
        count = utils.activate_all_records(task)
    except Exception as ex:
        flash(f"Failed to activate the selected records: {ex}")
    else:
        flash(f"{count} records were activated for batch processing.")
    return redirect(_url)


@app.route("/reset_all", methods=["POST"])
@roles_required(Role.SUPERUSER, Role.ADMIN, Role.TECHNICAL)
def reset_all():
    """Batch reset of batch records."""
    _url = request.args.get("url") or request.referrer
    task_id = request.form.get("task_id")
    task = Task.get(task_id)
    try:
        count = utils.reset_all_records(task)
    except Exception as ex:
        flash(f"Failed to reset the selected records: {ex}")
    else:
        flash(f"{count} {task.task_type.name} records were reset for batch processing.", "info")
    return redirect(_url)


@app.route("/section/<int:user_id>/<string:section_type>/<int:put_code>/delete", methods=["POST"])
@roles_required(Role.ADMIN)
def delete_record(user_id, section_type, put_code):
    """Delete an employment, education, peer review, works or funding record."""
    _url = request.referrer or request.args.get("url") or url_for(
        "section", user_id=user_id, section_type=section_type)
    try:
        user = User.get(id=user_id, organisation_id=current_user.organisation_id)
    except Exception:
        flash("ORCID HUB doesn't have data related to this researcher", "warning")
        return redirect(url_for('viewmembers.index_view'))
    if not user.orcid:
        flash("The user hasn't yet linked their ORCID record", "danger")
        return redirect(_url)

    orcid_token = None
    if section_type in ["RUR", "ONR", "KWR", "ADR", "EXR"]:
        orcid_token = OrcidToken.select(OrcidToken.access_token).where(OrcidToken.user_id == user.id,
                                                                       OrcidToken.org_id == user.organisation_id,
                                                                       OrcidToken.scopes.contains(
                                                                           orcid_client.PERSON_UPDATE)).first()
        if not orcid_token:
            flash("The user hasn't given 'PERSON/UPDATE' permission to delete this record", "warning")
            return redirect(_url)
    else:
        orcid_token = OrcidToken.select(OrcidToken.access_token).where(OrcidToken.user_id == user.id,
                                                                       OrcidToken.org_id == user.organisation_id,
                                                                       OrcidToken.scopes.contains(
                                                                           orcid_client.ACTIVITIES_UPDATE)).first()
        if not orcid_token:
            flash("The user hasn't given 'ACTIVITIES/UPDATE' permission to delete this record", "warning")
            return redirect(_url)

    # Gradually mirgating to v3.x
    if section_type in ["EDU", "EMP", "DST", "MEM", "SER", "QUA", "POS"]:
        api = orcid_client.MemberAPIV3(user=user, access_token=orcid_token.access_token)
    else:
        api = orcid_client.MemberAPI(user=user, access_token=orcid_token.access_token)

    try:
        api.delete_section(section_type, put_code)
        app.logger.info(f"For {user.orcid} '{section_type}' record was deleted by {current_user}")
        flash("The record was successfully deleted.", "success")
    except ApiException as e:
        flash(
            "Failed to delete the entry: " + json.loads(e.body.replace(
                "''", "\"")).get('user-messsage'), "danger")
    except Exception as ex:
        app.logger.error("For %r encountered exception: %r", user, ex)
        abort(500, ex)
    return redirect(_url)


@app.route("/section/<int:user_id>/<string:section_type>/<int:put_code>/edit", methods=["GET", "POST"])
@app.route("/section/<int:user_id>/<string:section_type>/new", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def edit_record(user_id, section_type, put_code=None):
    """Create a new or edit an existing profile section record."""
    section_type = section_type.upper()[:3]
    _url = (request.args.get("url")
            or url_for("section", user_id=user_id, section_type=section_type))

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
    is_person_update = section_type in ["RUR", "ONR", "KWR", "ADR", "EXR"]
    orcid_token = OrcidToken.select(OrcidToken.access_token).where(
        OrcidToken.user_id == user.id, OrcidToken.org_id == org.id,
        OrcidToken.scopes.contains(orcid_client.PERSON_UPDATE if is_person_update else orcid_client
                                   .ACTIVITIES_UPDATE)).first()
    if not orcid_token:
        flash(
            f"""The user hasn't given '{"PERSON/UPDATE" if is_person_update else "ACTIVITIES/UPDATE"}' """
            "permission to you to Add/Update these records", "warning")
        return redirect(_url)

    # Gradually mirgating to v3.x
    if section_type in ["EDU", "EMP", "DST", "MEM", "SER", "QUA", "POS"]:
        api = orcid_client.MemberAPIV3(user=user, access_token=orcid_token.access_token)
    else:
        api = orcid_client.MemberAPI(user=user, access_token=orcid_token.access_token)

    if section_type == "FUN":
        form = FundingForm(form_type=section_type)
    elif section_type == "PRR":
        form = PeerReviewForm(form_type=section_type)
    elif section_type == "WOR":
        form = WorkForm(form_type=section_type)
    elif section_type == "RUR":
        form = ResearcherUrlForm(form_type=section_type)
    elif section_type == "ADR":
        form = AddressForm(form_type=section_type)
    elif section_type == "EXR":
        form = ExternalIdentifierForm(form_type=section_type)
    elif section_type in ["ONR", "KWR"]:
        form = OtherNameKeywordForm(form_type=section_type)
    else:
        form = RecordForm(form_type=section_type)

    grant_data_list = []
    if request.method == "GET":
        data = {}
        if put_code:
            try:
                # Fetch an Employment
                if section_type == "EMP":
                    api_response = api.view_employmentv3(user.orcid, put_code, _preload_content=False)
                elif section_type == "EDU":
                    api_response = api.view_educationv3(user.orcid, put_code, _preload_content=False)
                elif section_type == "DST":
                    api_response = api.view_distinctionv3(user.orcid, put_code, _preload_content=False)
                elif section_type == "MEM":
                    api_response = api.view_membershipv3(user.orcid, put_code, _preload_content=False)
                elif section_type == "SER":
                    api_response = api.view_servicev3(user.orcid, put_code, _preload_content=False)
                elif section_type == "QUA":
                    api_response = api.view_qualificationv3(user.orcid, put_code, _preload_content=False)
                elif section_type == "POS":
                    api_response = api.view_invited_positionv3(user.orcid, put_code, _preload_content=False)
                elif section_type == "FUN":
                    api_response = api.view_funding(user.orcid, put_code, _preload_content=False)
                elif section_type == "WOR":
                    api_response = api.view_work(user.orcid, put_code)
                elif section_type == "PRR":
                    api_response = api.view_peer_review(user.orcid, put_code)
                elif section_type == "RUR":
                    api_response = api.view_researcher_url(user.orcid, put_code, _preload_content=False)
                elif section_type == "ONR":
                    api_response = api.view_other_name(user.orcid, put_code, _preload_content=False)
                elif section_type == "ADR":
                    api_response = api.view_address(user.orcid, put_code, _preload_content=False)
                elif section_type == "EXR":
                    api_response = api.view_external_identifier(user.orcid, put_code, _preload_content=False)
                elif section_type == "KWR":
                    api_response = api.view_keyword(user.orcid, put_code, _preload_content=False)

                if section_type in ["WOR", "PRR"]:
                    _data = api_response.to_dict()
                else:
                    _data = json.loads(api_response.data, object_pairs_hook=NestedDict)

                if section_type == "PRR" or section_type == "WOR":

                    if section_type == "PRR":
                        external_ids_list = get_val(_data, "review_identifiers", "external-id")
                    else:
                        external_ids_list = get_val(_data, "external_ids", "external-id")

                    for extid in external_ids_list:
                        external_id_value = extid['external-id-value'] if extid['external-id-value'] else ''
                        external_id_url = get_val(extid['external-id-url'], "value") if get_val(
                            extid['external-id-url'], "value") else ''
                        external_id_relationship = extid['external-id-relationship'] if extid[
                            'external-id-relationship'] else ''
                        external_id_type = extid['external-id-type'] if extid[
                            'external-id-type'] else ''

                        grant_data_list.append(dict(grant_number=external_id_value, grant_url=external_id_url,
                                                    grant_relationship=external_id_relationship,
                                                    grant_type=external_id_type))

                    if section_type == "WOR":
                        data = dict(work_type=get_val(_data, "type"),
                                    title=get_val(_data, "title", "title", "value"),
                                    subtitle=get_val(_data, "title", "subtitle", "value"),
                                    translated_title=get_val(_data, "title", "translated-title", "value"),
                                    translated_title_language_code=get_val(_data, "title", "translated-title",
                                                                           "language-code"),
                                    journal_title=get_val(_data, "journal_title", "value"),
                                    short_description=get_val(_data, "short_description"),
                                    citation_type=get_val(_data, "citation", "citation_type"),
                                    citation=get_val(_data, "citation", "citation_value"),
                                    url=get_val(_data, "url", "value"),
                                    language_code=get_val(_data, "language_code"),
                                    # Removing key 'media-type' from the publication_date dict.
                                    publication_date=PartialDate.create(
                                        {date_key: _data.get("publication_date")[date_key] for date_key in
                                         ('day', 'month', 'year')}) if _data.get("publication_date") else None,
                                    country=get_val(_data, "country", "value"))
                    else:
                        data = dict(
                            org_name=get_val(_data, "convening_organization", "name"),
                            disambiguated_id=get_val(
                                _data, "convening_organization", "disambiguated-organization",
                                "disambiguated-organization-identifier"),
                            disambiguation_source=get_val(
                                _data, "convening_organization", "disambiguated-organization",
                                "disambiguation-source"),
                            city=get_val(_data, "convening_organization", "address", "city"),
                            state=get_val(_data, "convening_organization", "address", "region"),
                            country=get_val(_data, "convening_organization", "address", "country"),
                            reviewer_role=_data.get("reviewer_role", ""),
                            review_url=get_val(_data, "review_url", "value"),
                            review_type=_data.get("review_type", ""),
                            review_group_id=_data.get("review_group_id", ""),
                            subject_external_identifier_type=get_val(_data, "subject_external_identifier",
                                                                     "external-id-type"),
                            subject_external_identifier_value=get_val(_data, "subject_external_identifier",
                                                                      "external-id-value"),
                            subject_external_identifier_url=get_val(_data, "subject_external_identifier",
                                                                    "external-id-url",
                                                                    "value"),
                            subject_external_identifier_relationship=get_val(_data, "subject_external_identifier",
                                                                             "external-id-relationship"),
                            subject_container_name=get_val(_data, "subject_container_name", "value"),
                            subject_type=_data.get("subject_type", ""),
                            subject_title=get_val(_data, "subject_name", "title", "value"),
                            subject_subtitle=get_val(_data, "subject_name", "subtitle"),
                            subject_translated_title=get_val(_data, "subject_name", "translated-title", "value"),
                            subject_translated_title_language_code=get_val(_data, "subject_name", "translated-title",
                                                                           "language-code"),
                            subject_url=get_val(_data, "subject_url", "value"),
                            review_completion_date=PartialDate.create(_data.get("review_completion_date")))
                elif section_type in ["RUR", "ONR", "KWR", "ADR", "EXR"]:
                    data = dict(visibility=_data.get("visibility"), display_index=_data.get("display-index"))
                    if section_type == "RUR":
                        data.update(dict(name=_data.get("url-name"), value=_data.get("url", "value")))
                    elif section_type == "ADR":
                        data.update(dict(country=_data.get("country", "value")))
                    elif section_type == "EXR":
                        data.update(dict(type=_data.get("external-id-type"), value=_data.get("external-id-value"),
                                         url=_data.get("external-id-url", "value"),
                                         relationship=_data.get("external-id-relationship")))
                    else:
                        data.update(dict(content=_data.get("content")))
                else:
                    data = dict(
                        org_name=_data.get("organization", "name"),
                        disambiguated_id=_data.get("organization", "disambiguated-organization",
                                                   "disambiguated-organization-identifier"),
                        disambiguation_source=_data.get("organization", "disambiguated-organization",
                                                        "disambiguation-source"),
                        city=_data.get("organization", "address", "city"),
                        state=_data.get("organization", "address", "region"),
                        country=_data.get("organization", "address", "country"),
                        department=_data.get("department-name"),
                        role=_data.get("role-title"),
                        start_date=PartialDate.create(_data.get("start-date")),
                        end_date=PartialDate.create(_data.get("end-date")))

                    external_ids_list = _data.get("external-ids", "external-id", default=[])

                    for extid in external_ids_list:
                        external_id_value = extid.get('external-id-value') if extid.get('external-id-value') else ''
                        external_id_url = extid.get('external-id-url', 'value') if extid.get(
                            'external-id-url', 'value') else ''
                        external_id_relationship = extid.get('external-id-relationship').upper() if extid.get(
                            'external-id-relationship') else ''
                        external_id_type = extid.get('external-id-type') if extid.get('external-id-type') else ''

                        grant_data_list.append(dict(grant_number=external_id_value, grant_url=external_id_url,
                                                    grant_relationship=external_id_relationship,
                                                    grant_type=external_id_type))
                    if section_type == "FUN":
                        data.update(dict(funding_title=_data.get("title", "title", "value"),
                                         funding_translated_title=_data.get("title", "translated-title", "value"),
                                         translated_title_language=_data.get("title", "translated-title",
                                                                             "language-code"),
                                         funding_type=_data.get("type"),
                                         funding_subtype=_data.get("organization-defined-type", "value"),
                                         funding_description=_data.get("short-description"),
                                         total_funding_amount=_data.get("amount", "value"),
                                         total_funding_amount_currency=_data.get("amount", "currency-code")))
                    else:
                        data.update(dict(url=_data.get("url", "value"), visibility=_data.get(
                            "visibility", default='').upper(), display_index=_data.get("display-index")))

            except ApiException as e:
                message = json.loads(e.body.replace("''", "\"")).get('user-messsage')
                app.logger.error(f"Exception when calling ORCID API: {message}")
            except Exception as ex:
                app.logger.exception(
                    "Unhandler error occured while creating or editing a profile record.")
                abort(500, ex)
        else:
            data = dict(
                org_name=org.name,
                disambiguated_id=org.disambiguated_id,
                disambiguation_source=org.disambiguation_source,
                city=org.city,
                country=org.country)

        form.process(data=data)

    if form.validate_on_submit():
        try:
            if section_type == "RUR":
                put_code, orcid, created, visibility = api.create_or_update_researcher_url(
                    put_code=put_code,
                    **{f.name: f.data
                       for f in form})
            elif section_type == "ONR":
                put_code, orcid, created, visibility = api.create_or_update_other_name(
                    put_code=put_code,
                    **{f.name: f.data
                       for f in form})
            elif section_type == "ADR":
                put_code, orcid, created, visibility = api.create_or_update_address(
                    put_code=put_code,
                    **{f.name: f.data
                       for f in form})
            elif section_type == "EXR":
                put_code, orcid, created, visibility = api.create_or_update_person_external_id(
                    put_code=put_code,
                    **{f.name: f.data
                       for f in form})
            elif section_type == "KWR":
                put_code, orcid, created, visibility = api.create_or_update_keyword(
                    put_code=put_code,
                    **{f.name: f.data
                       for f in form})
            else:
                grant_type = request.form.getlist('grant_type')
                grant_number = request.form.getlist('grant_number')
                grant_url = request.form.getlist('grant_url')
                grant_relationship = request.form.getlist('grant_relationship')

                # Skip entries with no grant number:
                grant_data_list = [{
                    'grant_number': gn,
                    'grant_type': gt,
                    'grant_url': gu,
                    'grant_relationship': gr
                } for gn, gt, gu, gr in zip(grant_number, grant_type, grant_url,
                                            grant_relationship) if gn]

                if section_type == "FUN":
                    put_code, orcid, created = api.create_or_update_individual_funding(
                        put_code=put_code,
                        grant_data_list=grant_data_list,
                        **{f.name: f.data
                           for f in form})
                elif section_type == "WOR":
                    put_code, orcid, created = api.create_or_update_individual_work(
                        put_code=put_code,
                        grant_data_list=grant_data_list,
                        **{f.name: f.data
                           for f in form})
                elif section_type == "PRR":
                    put_code, orcid, created = api.create_or_update_individual_peer_review(
                        put_code=put_code,
                        grant_data_list=grant_data_list,
                        **{f.name: f.data
                           for f in form})
                else:
                    put_code, orcid, created, visibility = api.create_or_update_affiliation(
                        put_code=put_code,
                        affiliation=Affiliation[section_type],
                        grant_data_list=grant_data_list,
                        **{f.name: f.data
                           for f in form})

                    affiliation, _ = UserOrgAffiliation.get_or_create(
                        user=user,
                        organisation=org,
                        put_code=put_code)

                    affiliation.department_name = form.department.data
                    affiliation.department_city = form.city.data
                    affiliation.role_title = form.role.data
                    form.populate_obj(affiliation)
                    affiliation.save()
            if put_code and created:
                flash("Record details has been added successfully!", "success")
            else:
                flash("Record details has been updated successfully!", "success")
            return redirect(_url)

        except ApiException as e:
            body = json.loads(e.body)
            message = body.get("user-message")
            dev_message = body.get("developer-message")
            more_info = body.get("more-info")
            flash(f"Failed to update the entry: {message}; {dev_message}", "danger")
            if more_info:
                flash(f'You can find more information at <a href="{more_info}">{more_info}</a>', "info")

            app.logger.exception(f"For {user} exception encountered; {dev_message}")
        except Exception as ex:
            app.logger.exception(
                "Unhandler error occured while creating or editing a profile record.")
            abort(500, ex)
    if not grant_data_list:
        grant_data_list.append(dict(grant_number='', grant_url='',
                                    grant_relationship='',
                                    grant_type=''))
    return render_template("profile_entry.html", section_type=section_type, form=form, _url=_url,
                           grant_data_list=grant_data_list)


@app.route("/section/<int:user_id>/<string:section_type>/list", methods=["GET", "POST"])
@login_required
def section(user_id, section_type="EMP"):
    """Show all user profile section list (either 'Education' or 'Employment')."""
    _url = request.args.get("url") or request.referrer or url_for("viewmembers.index_view")

    section_type = section_type.upper()[:3]  # normalize the section type
    if section_type not in ["EDU", "EMP", "FUN", "PRR", "WOR", "RUR", "ONR", "KWR", "ADR", "EXR", "DST", "MEM", "SER",
                            "QUA", "POS"]:
        flash("Incorrect user profile section", "danger")
        return redirect(_url)

    try:
        user = User.get(id=user_id, organisation_id=current_user.organisation_id)
    except Exception:
        flash("ORCID HUB doent have data related to this researcher", "warning")
        return redirect(_url)

    if not user.orcid:
        flash("The user hasn't yet linked their ORCID record", "danger")
        return redirect(_url)

    orcid_token = None
    if request.method == "POST" and section_type in ["RUR", "ONR", "KWR", "ADR", "EXR"]:
        try:
            orcid_token = OrcidToken.select(OrcidToken.access_token).where(
                OrcidToken.user_id == user.id, OrcidToken.org_id == user.organisation_id,
                OrcidToken.scopes.contains(orcid_client.PERSON_UPDATE)).first()
            if orcid_token:
                flash(
                    "There is no need to send an invite as you already have the token with 'PERSON/UPDATE' permission",
                    "success")
            else:
                app.logger.info(f"Ready to send an ivitation to '{user.email}'.")
                token = utils.new_invitation_token()

                invitation_url = url_for("orcid_login", invitation_token=token, _external=True)

                ui = UserInvitation.create(
                    is_person_update_invite=True,
                    invitee_id=user.id,
                    inviter_id=current_user.id,
                    org=current_user.organisation,
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    organisation=current_user.organisation,
                    disambiguated_id=current_user.organisation.disambiguated_id,
                    disambiguation_source=current_user.organisation.disambiguation_source,
                    affiliations=0,
                    token=token)

                utils.send_email(
                    "email/property_invitation.html",
                    invitation=ui,
                    invitation_url=invitation_url,
                    recipient=(current_user.organisation.name, user.email),
                    reply_to=(current_user.name, current_user.email),
                    cc_email=(current_user.name, current_user.email))
                flash("Invitation requesting 'PERSON/UPDATE' as been sent.", "success")
        except Exception as ex:
            flash(f"Exception occured while sending mails {ex}", "danger")
            app.logger.exception(f"For {user} encountered exception")
            return redirect(_url)
    try:
        if not orcid_token:
            orcid_token = OrcidToken.get(user=user, org=current_user.organisation)
    except Exception:
        flash("User didn't give permissions to update his/her records", "warning")
        return redirect(_url)

    # Gradually mirgating to v3.x
    if section_type in ["EDU", "EMP", "DST", "MEM", "SER", "QUA", "POS"]:
        api = orcid_client.MemberAPIV3(user=user, org=current_user.organisation, access_token=orcid_token.access_token)
    else:
        api = orcid_client.MemberAPI(user=user, org=current_user.organisation, access_token=orcid_token.access_token)
    try:
        api_response = api.get_section(section_type)
    except ApiException as ex:
        if ex.status == 401:
            flash("User has revoked the permissions to update his/her records", "warning")
        else:
            flash(
                "Exception when calling ORCID API: \n" + json.loads(ex.body.replace(
                    "''", "\"")).get('user-messsage'), "danger")
        return redirect(_url)
    except Exception as ex:
        abort(500, ex)

    # TODO: Organisation has read token
    # TODO: Organisation has access to the employment records
    # TODO: retrieve and tranform for presentation (order, etc)
    try:
        data = json.loads(api_response.data, object_pairs_hook=NestedDict)
    except Exception as ex:
        flash("User didn't give permissions to update his/her records", "warning")
        flash("Unhandled exception occured while retrieving ORCID data: %s" % ex, "danger")
        app.logger.exception(f"For {user} encountered exception")
        return redirect(_url)

    if section_type in ["FUN", "PRR", "WOR"]:
        records = (fs for g in data.get("group", default=[]) for fs in g.get({
            "FUN": "funding-summary",
            "WOR": "work-summary",
            "PRR": "peer-review-summary",
        }[section_type]))
    elif section_type in ["EDU", "EMP", "DST", "MEM", "SER", "QUA", "POS"]:
        records = (ss.get({"EDU": "education-summary",
                           "EMP": "employment-summary",
                           "DST": "distinction-summary",
                           "MEM": "membership-summary",
                           "SER": "service-summary",
                           "QUA": "qualification-summary",
                           "POS": "invited-position-summary"}[section_type]) for ag in
                   data.get("affiliation-group", default=[]) for ss in ag.get("summaries", default=[]))
    else:
        records = data.get({
            "RUR": "researcher-url",
            "KWR": "keyword",
            "ADR": "address",
            "ONR": "other-name",
            "EXR": "external-identifier",
        }[section_type])

    return render_template(
        "section.html",
        user=user,
        url=_url,
        Affiliation=Affiliation,
        records=records,
        section_type=section_type,
        org_client_id=user.organisation.orcid_client_id)


@app.route("/search/group_id_record/list", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def search_group_id_record():
    """Search groupID record."""
    _url = url_for("groupidrecord.index_view")
    form = GroupIdForm()
    records = []

    if request.method == "GET":
        data = dict(
            page_size="100",
            page="1")

        form.process(data=data)

    if request.method == "POST" and not form.search.data:
        group_id = request.form.get('group_id')
        name = request.form.get('name')
        description = request.form.get('description')
        id_type = request.form.get('type')
        put_code = request.form.get('put_code')

        with db.atomic():
            try:
                gir, created = GroupIdRecord.get_or_create(organisation=current_user.organisation,
                                                           group_id=group_id, name=name, description=description,
                                                           type=id_type)
                gir.put_code = put_code

                if created:
                    gir.add_status_line(f"Successfully added {group_id} from ORCID.")
                    flash(f"Successfully added {group_id}.", "success")
                else:
                    flash(f"The GroupID Record {group_id} is already existing in your list.", "success")
                gir.save()

            except Exception as ex:
                db.rollback()
                flash(f"Failed to save GroupID Record: {ex}", "warning")
                app.logger.exception(f"Failed to save GroupID Record: {ex}")

        return redirect(_url)
    elif form.validate_on_submit():
        try:
            group_id_name = form.group_id_name.data
            page_size = form.page_size.data
            page = form.page.data

            orcid_token = None
            org = current_user.organisation
            try:
                orcid_token = OrcidToken.get(org=org, scope='/group-id-record/read')
            except OrcidToken.DoesNotExist:
                orcid_token = utils.get_client_credentials_token(org=org, scope="/group-id-record/read")
            except Exception as ex:
                flash("Something went wrong in ORCID call, "
                      "please contact orcid@royalsociety.org.nz for support", "warning")
                app.logger.exception(f'Exception occured {ex}')

            orcid_client.configuration.access_token = orcid_token.access_token
            api = orcid_client.MemberAPI(org=org, access_token=orcid_token.access_token)

            api_response = api.view_group_id_records(page_size=page_size, page=page, name=group_id_name,
                                                     _preload_content=False)
            if api_response:
                data = json.loads(api_response.data)
                # Currently the api only gives correct response for one entry otherwise it throws 500 exception.
                records.append(data)
        except ApiException as ex:
            if ex.status == 401:
                orcid_token.delete_instance()
                flash(f"Old token was expired. Please search again so that next time we will fetch latest token",
                      "warning")
            elif ex.status == 500:
                flash(f"ORCID API Exception: {ex}", "warning")
            else:
                flash(f"Something went wrong in ORCID call, Please try again by making necessary changes, "
                      f"In case you understand this message: {ex} or"
                      f" else please contact orcid@royalsociety.org.nz for support", "warning")
                app.logger.warning(f'Exception occured {ex}')

        except Exception as ex:
            app.logger.exception(f'Exception occured {ex}')
            abort(500, ex)

    return render_template("groupid_record_entries.html", form=form, _url=_url, records=records)


@app.route("/load/org", methods=["GET", "POST"])
@roles_required(Role.SUPERUSER)
def load_org():
    """Preload organisation data."""
    form = FileUploadForm()
    if form.validate_on_submit():
        row_count = OrgInfo.load_from_csv(read_uploaded_file(form))

        flash("Successfully loaded %d rows." % row_count, "success")
        return redirect(url_for("orginfo.index_view"))

    return render_template("fileUpload.html", form=form, title="Organisation")


@app.route("/load/researcher", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_researcher_affiliations():
    """Preload organisation data."""
    form = FileUploadForm(extensions=["csv", "tsv", "json", "yaml", "yml"])
    if form.validate_on_submit():
        try:
            filename = secure_filename(form.file_.data.filename)
            content_type = form.file_.data.content_type
            content = read_uploaded_file(form)
            if content_type in ["text/tab-separated-values", "text/csv"] or (
                    filename and filename.lower().endswith(('.csv', '.tsv'))):
                task = Task.load_from_csv(content, filename=filename)
            else:
                task = AffiliationRecord.load(content, filename=filename)
            flash(f"Successfully loaded {task.record_count} rows.")
            return redirect(url_for("affiliationrecord.index_view", task_id=task.id))
        except (
                ValueError,
                ModelException,
        ) as ex:
            flash(f"Failed to load affiliation record file: {ex}", "danger")
            app.logger.exception("Failed to load affiliation records.")

    return render_template("fileUpload.html", form=form, title="Researcher Info Upload")


@app.route("/load/researcher/funding", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_researcher_funding():
    """Preload organisation data."""
    form = FileUploadForm(extensions=["json", "yaml", "csv", "tsv"])
    if form.validate_on_submit():
        filename = secure_filename(form.file_.data.filename)
        content_type = form.file_.data.content_type
        try:
            if content_type in ["text/tab-separated-values", "text/csv"] or (
                    filename and filename.lower().endswith(('.csv', '.tsv'))):
                task = FundingRecord.load_from_csv(
                    read_uploaded_file(form), filename=filename)
            else:
                task = FundingRecord.load_from_json(read_uploaded_file(form), filename=filename)
            flash(f"Successfully loaded {task.record_count} rows.")
            return redirect(url_for("fundingrecord.index_view", task_id=task.id))
        except Exception as ex:
            flash(f"Failed to load funding record file: {ex.args}", "danger")
            app.logger.exception("Failed to load funding records.")

    return render_template("fileUpload.html", form=form, title="Funding Info Upload")


@app.route("/load/researcher/work", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_researcher_work():
    """Preload researcher's work data."""
    form = FileUploadForm(extensions=["json", "yaml", "csv", "tsv"])
    if form.validate_on_submit():
        filename = secure_filename(form.file_.data.filename)
        content_type = form.file_.data.content_type
        try:
            if content_type in ["text/tab-separated-values", "text/csv"] or (
                    filename and filename.lower().endswith(('.csv', '.tsv'))):
                task = WorkRecord.load_from_csv(
                    read_uploaded_file(form), filename=filename)
            else:
                task = WorkRecord.load_from_json(read_uploaded_file(form), filename=filename)
            flash(f"Successfully loaded {task.record_count} rows.")
            return redirect(url_for("workrecord.index_view", task_id=task.id))
        except Exception as ex:
            flash(f"Failed to load work record file: {ex.args}", "danger")
            app.logger.exception("Failed to load work records.")

    return render_template("fileUpload.html", form=form, title="Work Info Upload")


@app.route("/load/researcher/peer_review", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_researcher_peer_review():
    """Preload researcher's peer review data."""
    form = FileUploadForm(extensions=["json", "yaml", "csv", "tsv"])
    if form.validate_on_submit():
        filename = secure_filename(form.file_.data.filename)
        content_type = form.file_.data.content_type
        try:
            if content_type in ["text/tab-separated-values", "text/csv"] or (
                    filename and filename.lower().endswith(('.csv', '.tsv'))):
                task = PeerReviewRecord.load_from_csv(
                    read_uploaded_file(form), filename=filename)
            else:
                task = PeerReviewRecord.load_from_json(read_uploaded_file(form), filename=filename)
            flash(f"Successfully loaded {task.record_count} rows.")
            return redirect(url_for("peerreviewrecord.index_view", task_id=task.id))
        except Exception as ex:
            flash(f"Failed to load peer review record file: {ex.args}", "danger")
            app.logger.exception("Failed to load peer review records.")

    return render_template("fileUpload.html", form=form, title="Peer Review Info Upload")


@app.route("/load/researcher/properties/<string:property_type>", methods=["GET", "POST"])
@app.route("/load/researcher/properties", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_properties(property_type=None):
    """Preload researcher's property data."""
    form = FileUploadForm(extensions=["json", "yaml", "csv", "tsv"])
    if form.validate_on_submit():
        filename = secure_filename(form.file_.data.filename)
        content_type = form.file_.data.content_type
        try:
            if content_type in ["text/tab-separated-values", "text/csv"] or (
                    filename and filename.lower().endswith(('.csv', '.tsv'))):
                task = PropertyRecord.load_from_csv(read_uploaded_file(form),
                                                    filename=filename,
                                                    file_property_type=property_type)
            else:
                task = PropertyRecord.load_from_json(read_uploaded_file(form),
                                                     filename=filename,
                                                     file_property_type=property_type)
            flash(f"Successfully loaded {task.record_count} rows.")
            return redirect(url_for("propertyrecord.index_view", task_id=task.id))
        except Exception as ex:
            flash(f"Failed to load researcher property record file: {ex}", "danger")
            app.logger.exception("Failed to load researcher property records.")

    return render_template(
        "fileUpload.html",
        form=form,
        title=f"Researcher {property_type.title() if property_type else 'Property'} Upload")


@app.route("/load/researcher/urls", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_researcher_urls():
    """Preload researcher's property data."""
    return load_properties(property_type="URL")


@app.route("/load/other/names", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_other_names():
    """Preload Other Name data."""
    return load_properties(property_type="NAME")


@app.route("/load/keyword", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_keyword():
    """Preload Keywords data."""
    return load_properties(property_type="KEYWORD")


@app.route("/load/country", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_country():
    """Preload Country data."""
    return load_properties(property_type="COUNTRY")


@app.route("/load/other/ids", methods=["GET", "POST"])
@roles_required(Role.ADMIN)
def load_other_ids():
    """Preload researcher's Other IDs data."""
    form = FileUploadForm(extensions=["json", "yaml", "csv", "tsv"])
    if form.validate_on_submit():
        filename = secure_filename(form.file_.data.filename)
        content_type = form.file_.data.content_type
        try:
            if content_type in ["text/tab-separated-values", "text/csv"] or (
                    filename and filename.lower().endswith(('.csv', '.tsv'))):
                task = OtherIdRecord.load_from_csv(
                    read_uploaded_file(form), filename=filename)
            else:
                task = OtherIdRecord.load_from_json(read_uploaded_file(form), filename=filename)
            flash(f"Successfully loaded {task.record_count} rows.")
            return redirect(url_for("otheridrecord.index_view", task_id=task.id))
        except Exception as ex:
            flash(f"Failed to load Other IDs record file: {ex}", "danger")
            app.logger.exception("Failed to load  Other IDs records.")

    return render_template("fileUpload.html", form=form, title="Other IDs Info Upload")


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
        except Exception:
            app.logger.exception("Failed to save organisation data")
            raise

        try:
            user = User.get(email=email)
            user.organisation = org
        except User.DoesNotExist:
            user = User.create(
                email=email,
                organisation=org)

        user.roles |= Role.ADMIN
        if tech_contact:
            user.roles |= Role.TECHNICAL

        if via_orcid:
            if not user.orcid and orcid_id:
                user.orcid = orcid_id
            if not user.first_name and first_name:
                user.first_name = first_name
            if not user.last_name and last_name:
                user.last_name = last_name

        try:
            user.save()
        except Exception:
            app.logger.exception("Failed to save user data")
            raise

        try:
            user_org = UserOrg.get(user=user, org=org)
            user_org.is_admin = True
            try:
                user_org.save()
            except Exception:
                app.logger.exception(
                    "Failed to assign the user as an administrator to the organisation")
                raise
        except UserOrg.DoesNotExist:
            user_org = UserOrg.create(user=user, org=org, is_admin=True)

        app.logger.info(f"Ready to send an ivitation to '{org_name} <{email}>'.")
        token = utils.new_invitation_token()
        # TODO: for via_orcid constact direct link to ORCID with callback like to HUB
        if via_orcid:
            invitation_url = url_for("orcid_login", invitation_token=token, _external=True)
        else:
            invitation_url = url_for("index", _external=True)

        oi = OrgInvitation.create(
            inviter_id=current_user.id,
            invitee_id=user.id,
            email=user.email,
            org=org,
            token=token,
            tech_contact=tech_contact,
            url=invitation_url)

        utils.send_email(
            "email/org_invitation.html",
            invitation=oi,
            recipient=(org_name, email),
            reply_to=(current_user.name, current_user.email),
            cc_email=(current_user.name, current_user.email))

        org.is_email_sent = True
        if tech_contact:
            org.tech_contact = user
        try:
            org.save()
        except Exception:
            app.logger.exception("Failed to save organisation data")
            raise


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
                        # If the current tech contact is technical contact of more than one organisation,
                        # then dont update the Roles in User table.
                        check_tech_contact_count = Organisation.select().where(
                            Organisation.tech_contact == org.tech_contact).count()
                        if check_tech_contact_count == 1:
                            org.tech_contact.roles &= ~Role.TECHNICAL
                            org.tech_contact.save()
                        flash(f"The current tech.contact {org.tech_contact.name} "
                              f"({org.tech_contact.email}) will be revoked.", "warning")
                except Organisation.DoesNotExist:
                    pass
                except User.DoesNotExist:
                    pass

            register_org(**params)
            org = Organisation.get(name=org_name)
            user = User.get(email=email)
            if org.confirmed:
                if user.is_tech_contact_of(org):
                    flash("New Technical contact has been Invited Successfully! "
                          "An email has been sent to the Technical contact", "success")
                    app.logger.info(
                        f"For Organisation '{org_name}', "
                        f"New Technical Contact '{email}' has been invited successfully.")
                else:
                    flash("New Organisation Admin has been Invited Successfully! "
                          "An email has been sent to the Organisation Admin", "success")
                    app.logger.info(
                        f"For Organisation '{org_name}', "
                        f"New Organisation Admin '{email}' has been invited successfully.")
            else:
                flash("Organisation Invited Successfully! "
                      "An email has been sent to the organisation contact", "success")
                app.logger.info(f"Organisation '{org_name}' successfully invited. "
                                f"Invitation sent to '{email}'.")
        except Exception as ex:
            app.logger.exception(f"Failed to send registration invitation with {params}.")
            flash(f"Failed to send registration invitation: {ex}.", "danger")

    org_info = cache.get("org_info")
    if not org_info:
        org_info = {
            r.name: r.to_dict(only=[
                OrgInfo.email, OrgInfo.first_name, OrgInfo.last_name, OrgInfo.country,
                OrgInfo.city, OrgInfo.disambiguated_id, OrgInfo.disambiguation_source
            ])
            for r in OrgInfo.select(OrgInfo.name, OrgInfo.email, OrgInfo.first_name,
                                    OrgInfo.last_name, OrgInfo.country, OrgInfo.city,
                                    OrgInfo.disambiguated_id, OrgInfo.disambiguation_source)
            | Organisation.select(
                Organisation.name,
                SQL('NULL').alias("email"),
                SQL('NULL').alias("first_name"),
                SQL('NULL').alias("last_name"), Organisation.country, Organisation.city,
                Organisation.disambiguated_id, Organisation.disambiguation_source).join(
                    OrgInfo, JOIN.LEFT_OUTER, on=(
                        OrgInfo.name == Organisation.name)).where(OrgInfo.name.is_null())
        }
        cache.set("org_info", org_info, timeout=60)

    return render_template("registration.html", form=form, org_info=org_info)


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
        invited_user = None
        if form.is_student.data:
            affiliations = Affiliation.EDU
        if form.is_employee.data:
            affiliations |= Affiliation.EMP

        invited_user = User.select().where(User.email == email).first()
        if (invited_user and OrcidToken.select().where(
            (OrcidToken.user_id == invited_user.id) & (OrcidToken.org_id == org.id)
                & (OrcidToken.scopes.contains("/activities/update"))).exists()):
            try:
                if affiliations & (Affiliation.EMP | Affiliation.EDU):
                    api = orcid_client.MemberAPIV3(org, invited_user)
                    params = {f.name: f.data for f in form if f.data != ""}
                    for a in Affiliation:
                        if a & affiliations:
                            params["affiliation"] = a
                            params["initial"] = False
                            api.create_or_update_affiliation(**params)
                    flash(
                        f"The ORCID Hub was able to automatically write an affiliation with "
                        f"{invited_user.organisation}, as the nature of the affiliation with {invited_user} "
                        f"organisation does appear to include either Employment or Education.\n ",
                        "success")
                else:
                    flash(
                        f"The ORCID Hub was not able to automatically write an affiliation with "
                        f"{invited_user.organisation}, as the nature of the affiliation with {invited_user} "
                        f"organisation does not appear to include either Employment or Education.\n "
                        f"Please select 'staff' or 'student' checkbox present on this page.", "warning")
            except Exception as ex:
                flash(f"Something went wrong: {ex}", "danger")
                app.logger.exception("Failed to create affiliation record")
        else:
            try:
                ui = UserInvitation.get(org=org, email=email)
                flash(
                    f"An invitation to affiliate with {org} had been already sent to {email} earlier "
                    f"at {isodate(ui.sent_at)}.", "warning" if resend else "danger")
                if not form.resend.data:
                    break
            except UserInvitation.DoesNotExist:
                pass

            inviter = current_user._get_current_object()
            job = send_user_invitation.queue(
                inviter.id,
                org.id,
                email=email,
                affiliations=affiliations,
                **{f.name: f.data
                   for f in form},
                cc_email=(current_user.name, current_user.email))
            flash(
                f"An invitation to {email} was {'resent' if resend else 'sent'} successfully (task id: {job.id}).",
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
            if any(x in form.email_template.data for x in ['{MESSAGE}', '{INCLUDED_URL}']):
                org.email_template = form.email_template.data
                org.email_template_enabled = form.email_template_enabled.data
                org.save()
                flash("Saved organisation email template'", "info")
            else:
                flash("Are you sure? Without a {MESSAGE} or {INCLUDED_URL} "
                      "your users will be unable to respond to your invitations.", "danger")

    return render_template("email_template.html", BASE_URL=url_for("index", _external=True)[:-1], form=form)


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
        if client and client.user_id != current_user.id:
            flash("Access denied!", "danger")
            return redirect(url_for("application"))
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
            with db.atomic():
                Token.delete().where(Token.client == client).execute()
                client.delete_instance(recursive=True)
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

    Receives:
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
        UserOrg.delete().where(
                (UserOrg.user_id == user_id) & (UserOrg.org_id == org_id)).execute()
        user = User.get(id=user_id)
        if (user.roles & Role.ADMIN) and not user.admin_for.exists():
            user.roles &= ~Role.ADMIN
            user.save()
            app.logger.info(f"Revoked ADMIN role from user {user}")
        if user.organisation_id == org_id:
            user.organisation_id = None
            user.save()
        return jsonify({
            "user-org": data,
            "status": "DELETED",
        }), 204
    else:
        org = Organisation.get(org_id)
        uo, created = UserOrg.get_or_create(user_id=user_id, org_id=org_id)
        if "is_admin" in data:
            uo.is_admin = data["is_admin"]
            uo.save()
        if "is_tech_contact" in data:
            user = User.get(id=user_id)
            if data["is_tech_contact"]:
                # Updating old Technical Contact's Role info.
                if org.tech_contact and org.tech_contact != user:
                    org.tech_contact.roles &= ~Role.TECHNICAL
                    org.tech_contact.save()
                # Assigning new tech contact to organisation.
                org.tech_contact = user
            elif org.tech_contact == user:
                org.tech_contact_id = None
            org.save()
        return jsonify({
            "org": model_to_dict(org, recurse=False),
            "user_org": model_to_dict(uo, recurse=False),
            "status": ("CREATED" if created else "UPDATED"),
        }), (201 if created else 200)


@app.route("/services/<int:user_id>/updated", methods=["POST"])
def update_webhook(user_id):
    """Handle webook calls."""
    try:
        updated_at = datetime.utcnow()
        user = User.get(user_id)
        user.orcid_updated_at = updated_at
        user.save()
        utils.notify_about_update(user)

    except Exception:
        app.logger.exception(f"Invalid user_id: {user_id}")

    return '', 204


@app.route(
    "/settings/webhook", methods=[
        "GET",
        "POST",
    ])
@roles_required(Role.TECHNICAL, Role.SUPERUSER)
def org_webhook():
    """Manage organisation invitation email template."""
    org = current_user.organisation
    form = WebhookForm(obj=org)

    if form.validate_on_submit():
        old_webhook_url = org.webhook_url
        if old_webhook_url and old_webhook_url != form.webhook_url.data:
            for u in org.users.where(User.webhook_enabled):
                utils.register_orcid_webhook.queue(u, delete=True)
        form.populate_obj(org)
        org.save()
        if form.webhook_enabled.data:
            job = utils.enable_org_webhook.queue(org)
            flash(f"Webhook activation was initiated (task id: {job.id})", "info")
        else:
            utils.disable_org_webhook.queue(org)
            flash(f"Webhook was disabled.", "info")

    return render_template("form.html", form=form, title="Organisation Webhook")


@app.route("/sync_profiles/<int:task_id>", methods=["GET", "POST"])
@app.route(
    "/sync_profiles", methods=[
        "GET",
        "POST",
    ])
@roles_required(Role.TECHNICAL, Role.SUPERUSER)
def sync_profiles(task_id=None):
    """Start research profile synchronization."""
    if not current_user.is_tech_contact_of() and not current_user.is_superuser:
        flash(
            f"Access Denied! You must be the technical conatact of '{current_user.organisation}'",
            "danger")
        abort(403)
    if not task_id:
        task_id = request.args.get("task_id")
    if task_id:
        task = Task.get(task_id)
        org = task.org
    else:
        org = current_user.organisation
        task = Task.select().where(Task.task_type == TaskType.SYNC, Task.org == org).order_by(
            Task.created_at.desc()).limit(1).first()

    form = ProfileSyncForm()

    if form.is_submitted():
        if form.close.data:
            _next = get_next_url() or url_for("task.index_view")
            return redirect(_next)
        if task and not form.restart.data:
            flash(f"There is already an active profile synchronization task", "warning")
        else:
            Task.delete().where(Task.org == org, Task.task_type == TaskType.SYNC).execute()
            task = Task.create(org=org, task_type=TaskType.SYNC)
            job = utils.sync_profile.queue(task_id=task.id)
            flash(f"Profile synchronization task was initiated (job id: {job.id})", "info")
            return redirect(url_for("sync_profiles"))

    page_size = 10
    page = int(request.args.get("page", 1))
    page_count = math.ceil(task.log_entries.count() / page_size) if task else 0
    return render_template(
        "profile_sync.html",
        form=form,
        title="Profile Synchronization",
        task=task,
        page=page,
        page_size=page_size,
        page_count=page_count)


@app.route("/remove/orcid/linkage", methods=["POST"])
@login_required
def remove_linkage():
    """Delete an ORCID Token and ORCiD iD."""
    _url = request.args.get("url") or request.referrer or url_for("link")
    org = current_user.organisation
    token_revoke_url = app.config["ORCID_BASE_URL"] + "oauth/revoke"

    if UserOrg.select().where(
                (UserOrg.user_id == current_user.id) & (UserOrg.org_id == org.id) & UserOrg.is_admin).exists():
        flash(f"Failed to remove linkage for {current_user}, as this user appears to be one of the admins for {org}. "
              f"Please contact orcid@royalsociety.org.nz for support", "danger")
        return redirect(_url)

    for token in OrcidToken.select().where(OrcidToken.org_id == org.id, OrcidToken.user_id == current_user.id):
        try:
            resp = requests.post(
                token_revoke_url,
                headers={"Accepts": "application/json"},
                data=dict(
                    client_id=org.orcid_client_id,
                    client_secret=org.orcid_secret,
                    token=token.access_token))

            if resp.status_code != 200:
                flash("Failed to revoke token {token.access_token}: {ex}", "danger")
                return redirect(_url)

            token.delete_instance()

        except Exception as ex:
            flash(f"Failed to revoke token {token.access_token}: {ex}", "danger")
            app.logger.exception('Failed to delete record.')
            return redirect(_url)
    # Check if the User is Admin for other organisation or has given permissions to other organisations.
    if UserOrg.select().where(
            (UserOrg.user_id == current_user.id) & UserOrg.is_admin).exists() or OrcidToken.select().where(
            OrcidToken.user_id == current_user.id).exists():
        flash(
            f"We have removed the Access token related to {org}, However we did not remove the stored ORCiD ID as "
            f"{current_user} is either an admin of other organisation or has given permission to other organisation.",
            "warning")
    else:
        current_user.orcid = None
        current_user.save()
        flash(
            f"We have removed the Access token and storied ORCiD ID for {current_user}. "
            f"If you logout now without giving permissions, you may not be able to login again. "
            f"Please press the below button to give permissions to {org}",
            "success")
    return redirect(_url)


class ScheduerView(BaseModelView):
    """Simle Flask-RQ2 scheduled task viewer."""

    can_edit = False
    can_delete = False
    can_create = False
    can_view_details = True
    column_type_formatters = {datetime: lambda view, value: isodate(value)}

    def __init__(self,
                 name=None,
                 category=None,
                 endpoint=None,
                 url=None,
                 static_folder=None,
                 menu_class_name=None,
                 menu_icon_type=None,
                 menu_icon_value=None):
        """Initialize the view."""
        self._search_fields = []

        model = FlaskJob
        super().__init__(
            model,
            name,
            category,
            endpoint,
            url,
            static_folder,
            menu_class_name=menu_class_name,
            menu_icon_type=menu_icon_type,
            menu_icon_value=menu_icon_value)

        self._primary_key = self.scaffold_pk()

    def scaffold_pk(self):  # noqa: D102
        return "id"

    def get_pk_value(self, model):  # noqa: D102
        return model.id

    def scaffold_list_columns(self):
        """Scaffold list columns."""
        return [
            "description", "created_at", "origin", "enqueued_at", "timeout", "result_ttl",
            "status", "meta"
        ]

    def scaffold_sortable_columns(self):  # noqa: D102
        return self.scaffold_list_columns()

    def init_search(self):  # noqa: D102
        if self.column_searchable_list:
            for p in self.column_searchable_list:
                if isinstance(p, str):
                    p = getattr(self.model, p)

                # Check type
                if not isinstance(p, (CharField, TextField)):
                    raise Exception(
                        f'Can only search on text columns. Failed to setup search for "{p}"')

                self._search_fields.append(p)

        return bool(self._search_fields)

    def scaffold_filters(self, name):  # noqa: D102
        return None

    def is_valid_filter(self, filter_object):  # noqa: D102
        return isinstance(filter_object, filters.BasePeeweeFilter)

    def scaffold_form(self):  # noqa: D102
        from wtforms import Form
        return Form()

    def scaffold_inline_form_models(self, form_class):  # noqa: D102
        converter = self.model_form_converter(self)
        inline_converter = self.inline_model_form_converter(self)

        for m in self.inline_models:
            form_class = inline_converter.contribute(converter,
                                                     self.model,
                                                     form_class,
                                                     m)

        return form_class

    def get_query(self):  # noqa: D102
        return rq.get_scheduler().get_jobs()

    def get_list(self, page, sort_column, sort_desc, search, filters, execute=True,
                 page_size=None):
        """Return records from the database.

        :param page:
            Page number
        :param sort_column:
            Sort column name
        :param sort_desc:
            Descending or ascending sort
        :param search:
            Search query
        :param filters:
            List of filter tuples
        :param execute:
            Execute query immediately? Default is `True`
        :param page_size:
            Number of results. Defaults to ModelView's page_size. Can be
            overriden to change the page_size limit. Removing the page_size
            limit requires setting page_size to 0 or False.
        """
        jobs = list(self.get_query())

        # Get count
        count = len(jobs)

        # TODO: sort

        return count, jobs

    def get_one(self, job_id):
        """Get a single job."""
        try:
            scheduler = rq.get_scheduler()
            return scheduler.job_class.fetch(job_id, connection=scheduler.connection)
        except Exception as ex:
            flash(f"The jeb with given ID: {job_id} doesn't exist or it was deleted: {ex}.",
                  "danger")
            abort(404)

    def is_accessible(self):
        """Verify if the view is accessible for the current user."""
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role(Role.SUPERUSER):
            return True

        return False


admin.add_view(ScheduerView(name="schedude", endpoint="schedude"))
