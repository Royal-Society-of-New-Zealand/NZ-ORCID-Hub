"""HUB API."""

from datetime import datetime
import re
from urllib.parse import unquote, urlencode

import jsonschema
import requests
import validators
import yaml
from flask import (Response, abort, current_app, jsonify, make_response, render_template, request,
                   stream_with_context, url_for)
from flask.views import MethodView
from flask_login import current_user, login_user
from flask_restful import Resource, reqparse
from flask_swagger import swagger

from . import api, app, db, models, oauth, schemas
from .login_provider import roles_required
from .models import (ORCID_ID_REGEX, AffiliationRecord, Client, FundingRecord, OrcidToken,
                     PeerReviewRecord, Role, Task, TaskType, User, UserOrg, validate_orcid_id,
                     WorkRecord)
from .utils import dump_yaml, is_valid_url, register_orcid_webhook

ORCID_API_VERSION_REGEX = re.compile(r"^v[2-3].\d+(_rc\d+)?$")


def prefers_yaml():
    """Test if the client prefers YAML."""
    best = request.accept_mimetypes.best_match(["text/yaml", "application/x-yaml"])
    return (best in [
        "text/yaml",
        "application/x-yaml",
    ] and request.accept_mimetypes[best] > request.accept_mimetypes["application/json"])


@app.route('/api/me')
@app.route("/api/v1.0/me")
@oauth.require_oauth()
def me():
    """Get the token user data."""
    user = request.oauth.user
    return jsonify(email=user.email, name=user.name)


class AppResource(Resource):
    """Common application resource."""

    decorators = [
        oauth.require_oauth(),
    ]

    def dispatch_request(self, *args, **kwargs):
        """Do some pre-handling and post-handling."""
        resp = super().dispatch_request(*args, **kwargs)
        if isinstance(resp, tuple) and len(resp) == 2:
            resp, status_code = resp
            assert isinstance(resp, Response) and isinstance(status_code, int)
            resp.status_code = status_code
            return resp
        return resp

    def httpdate(self, dt):
        """Return a string representation of a date according to RFC 1123 (HTTP/1.1).

        The supplied date must be in UTC.
        """
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
        month = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ][dt.month - 1]
        return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, dt.day, month, dt.year, dt.hour,
                                                        dt.minute, dt.second)

    @property
    def is_yaml_request(self):
        """Test if the request body content type is YAML."""
        return request.content_type in ["text/yaml", "application/x-yaml"]


def changed_path(name, value):
    """Create query string with a new parameter value."""
    link = request.path
    if request.args:
        link += '&' + urlencode(
            {k: v if k != name else value
                for k, v in request.args.items()})
    return link


class AppResourceList(AppResource):
    """Resource list resource with helpers for pagination."""

    @models.lazy_property
    def page(self):
        """Get the current queried page."""
        try:
            return int(request.args.get("page", 1))
        except:
            return 1

    @models.lazy_property
    def page_size(self):  # noqa: D402
        """Get the current query page size, default: 20."""
        try:
            return int(request.args.get("page_size", 20))
        except:
            return 20

    @models.lazy_property
    def next_link(self):
        """Get the next page link of the requested resource."""
        return changed_path("page", self.page + 1)

    @models.lazy_property
    def previous_link(self):
        """Get the previous page link of the requested resource."""
        if self.page <= 1:
            return
        return changed_path("page", self.page - 1)

    @models.lazy_property
    def first_link(self):
        """Get the first page link of the requested resource."""
        return changed_path("page", 1)

    def api_response(self, query, exclude=None, only=None):
        """Create and return API response with pagination links."""
        query = query.paginate(self.page, self.page_size)
        records = [r.to_dict(recurse=False, to_dashes=True, exclude=exclude, only=only) for r in query]
        resp = yamlfy(records) if prefers_yaml() else jsonify(records)
        resp.headers["Pagination-Page"] = self.page
        resp.headers["Pagination-Page-Size"] = self.page_size
        resp.headers["Pagination-Count"] = len(records)
        resp.headers["Link"] = f'<{request.full_path}>;rel="self"'
        if self.page != 1:
            resp.headers["Link"] += f', <{self.first_link}>;rel="first"'
        if self.previous_link:
            resp.headers["Link"] += f', <{self.previous_link}>;rel="prev"'
        if len(records) == self.page_size and self.next_link:
            resp.headers["Link"] += f', <{self.next_link}>;rel="next"'
        return resp


class TaskResource(AppResource):
    """Common task related resource."""

    available_task_types = [t.name for t in TaskType]

    def dispatch_request(self, *args, **kwargs):
        """Do some pre-handling..."""
        parser = reqparse.RequestParser()
        parser.add_argument(
            "type", type=str, required=False,
            help="Task type: " + ", ".join(self.available_task_types))
        parser.add_argument("filename", type=str, help="Filename of the task.")
        # TODO: fix Flask-Restful
        try:
            parsed_args = parser.parse_args()
            task_type = parsed_args.get("type")
            if task_type:
                task_type = task_type.upper()
            filename = parsed_args.get("filename")
        # TODO: fix Flask-Restful
        # TODO: Remove when the fix gets merged in
        except ValueError:
            filename, task_type = request.args.get("filename"), None
        self.filename = filename
        if task_type and any(task_type == t.name for t in TaskType):
            self.task_type = TaskType[task_type]
        else:
            self.task_type = None
        return super().dispatch_request(*args, **kwargs)

    def jsonify_task(self, task):
        """Create JSON response with the task payload."""
        if isinstance(task, int):
            login_user(request.oauth.user)
            try:
                task = Task.get(id=task)
            except Task.DoesNotExist:
                return jsonify({"error": "The task doesn't exist."}), 404
            if task.created_by != current_user:
                return jsonify({"error": "Access denied."}), 403
        if request.method != "HEAD":
            if task.task_type in [
                    TaskType.AFFILIATION, TaskType.FUNDING, TaskType.PEER_REVIEW, TaskType.WORK
            ]:
                resp = jsonify(task.to_export_dict())
            else:
                raise Exception(f"Suppor for {task} has not yet been implemented.")
        else:
            resp = Response()
        resp.headers["Last-Modified"] = self.httpdate(task.updated_at or task.created_at)
        return resp

    def delete_task(self, task_id):
        """Delete the task."""
        login_user(request.oauth.user)
        try:
            task = Task.get(id=task_id)
        except Task.DoesNotExist:
            return jsonify({"error": "The task doesn't exist."}), 404
        except Exception as ex:
            app.logger.exception(f"Failed to find the task with ID: {task_id}")
            return jsonify({"error": "Unhandled exception occurred.", "exception": str(ex)}), 400

        if task.created_by != current_user:
            abort(403)
        task.delete_instance()
        return {"message": "The task was successfully deleted."}

    def handle_affiliation_task(self, task_id=None):
        """Handle PUT, POST, or PATCH request. Request body expected to be encoded in JSON."""
        login_user(request.oauth.user)

        if self.is_yaml_request:
            try:
                data = yaml.load(request.data)
            except Exception as ex:
                return jsonify({
                    "error": "Invalid request format. Only JSON, CSV, or TSV are acceptable.",
                    "message": str(ex)
                }), 415
        else:
            data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid request format. Only JSON, CSV, or TSV are acceptable."}), 415
        try:
            if request.method != "PATCH":
                jsonschema.validate(data, schemas.affiliation_task)
        except jsonschema.exceptions.ValidationError as ex:
            return jsonify({"error": "Validation error.", "message": ex.message}), 422
        except Exception as ex:
            return jsonify({"error": "Unhandled exception occurred.", "exception": ex}), 400
        if "records" not in data:
            return jsonify({"error": "Validation error.", "message": "Missing affiliation records."}), 422

        filename = (data.get("filename") or self.filename or datetime.utcnow().isoformat(timespec="seconds"))
        if task_id:
            try:
                task = Task.get(id=task_id)
            except Task.DoesNotExist:
                return jsonify({"error": "The task doesn't exist."}), 404
            if task.created_by != current_user:
                return jsonify({"error": "Access denied."}), 403
        try:
            task = AffiliationRecord.load(
                data,
                filename=filename,
                task_id=task_id,
                skip_schema_validation=True,
                override=(request.method == "POST"))
        except Exception as ex:
            db.rollback()
            app.logger.exception("Failed to handle affiliation API request.")
            return jsonify({"error": "Unhandled exception occurred.", "exception": str(ex)}), 400

        return self.jsonify_task(task)

    def handle_task(self, task_id=None):
        """Handle PUT, POST, or PATCH request. Request body expected to be encoded in JSON."""
        try:
            login_user(request.oauth.user)
            if task_id:
                try:
                    task = Task.get(id=task_id)
                    if not self.filename:
                        self.filename = task.filename
                except Task.DoesNotExist:
                    return jsonify({"error": "The task doesn't exist."}), 404
                if task.created_by != current_user:
                    return jsonify({"error": "Access denied."}), 403
            else:
                task = None
            task = self.load_from_json(task=task)
        except Exception as ex:
            app.logger.exception("Failed to handle funding API request.")
            return jsonify({"error": "Unhandled exception occurred.", "exception": str(ex)}), 400

        return self.jsonify_task(task)

    def head(self, task_id):
        """Handle HEAD request.

        ---
        summary: "Return task update time-stamp."
        description: "Return record processing task update time-stamp."
        parameters:
          - name: "task_id"
            in: "path"
            description: "Task ID."
            required: true
            type: "integer"
        produces:
          - "application/json"
        responses:
          200:
            description: "Successful operation"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.jsonify_task(task_id)


class TaskList(TaskResource, AppResourceList):
    """Task list services."""

    def get(self, *args, **kwargs):
        """
        Retrieve the list of all submitted task.

        ---
        tags:
          - "tasks"
        summary: "Retrieve the list of all submitted task."
        description: "Retrieve the list of all submitted task."
        produces:
          - "application/json"
          - "text/yaml"
        definitions:
        - schema:
            id: Task
            properties:
              id:
                type: integer
                format: int64
              filename:
                type: string
              task-type:
                type: string
                enum:
                - AFFILIATION
                - FUNDING
                - PEER_REVIEW
                - WORK
              created-at:
                type: string
                format: date-time
              expires-at:
                type: string
                format: date-time
              completed-at:
                type: string
                format: date-time
        parameters:
          - name: "type"
            in: "query"
            required: false
            description: "The task type: AFFILIATION, FUNDING, etc."
            type: "string"
            enum:
              - AFFILIATION
              - FUNDING
              - PEER_REVIEW
              - WORK
          - in: query
            name: page
            description: The number of the page of retrieved data starting counting from 1
            type: integer
            minimum: 0
            default: 1
          - in: query
            name: page_size
            description: The size of the data page
            type: integer
            minimum: 0
            default: 20
        responses:
          200:
            description: "successful operation"
            schema:
              type: array
              items:
                $ref: "#/definitions/Task"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        login_user(request.oauth.user)
        query = Task.select().where(Task.org_id == current_user.organisation_id)
        task_type = request.args.get("type")
        if task_type:
            query = query.where(Task.task_type == TaskType[task_type.upper()].value)
        return self.api_response(query, exclude=[Task.created_by, Task.updated_by, Task.org])


class AffiliationListAPI(TaskResource):
    """Affiliation list API."""

    def post(self, *args, **kwargs):
        """Upload the affiliation task.

        ---
        tags:
          - "affiliations"
        summary: "Post the affiliation list task."
        description: "Post the affiliation list task."
        consumes:
        - application/json
        - text/csv
        - text/yaml
        produces:
        - application/json
        parameters:
        - name: "filename"
          required: false
          in: "query"
          description: "The batch process filename."
          type: "string"
        - name: body
          in: body
          description: "Affiliation task."
          schema:
            $ref: "#/definitions/AffiliationTask"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/AffiliationTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        definitions:
        - schema:
            id: AffiliationTask
            properties:
              id:
                type: integer
                format: int64
              filename:
                type: string
              task-type:
                type: string
                enum:
                - AFFILIATION
                - FUNDING
              created-at:
                type: string
                format: date-time
              expires-at:
                type: string
                format: date-time
              completed-at:
                type: string
                format: date-time
              records:
                type: array
                items:
                  $ref: "#/definitions/AffiliationTaskRecord"
        - schema:
            id: AffiliationTaskRecord
            required:
              - email
              - first-name
              - last-name
              - affiliation-type
            properties:
              id:
                type: integer
                format: int64
              put-code:
                type: string
              external-id:
                type: string
              is-active:
                type: boolean
              email:
                type: string
              first-name:
                type: string
              last-name:
                type: string
              role:
                type: string
              organisation:
                type: string
              department:
                type: string
              city:
                type: string
              state:
                type: string
              country:
                type: string
              disambiguated-id:
                type: string
              disambiguated-source:
                type: string
              affiliation-type:
                type: string
                enum:
                  - student
                  - staff
              start-date:
                type: string
              end-date:
                type: string
              processed-at:
                type: string
                format: date-time
              status:
                type: string
              orcid:
                type: string
                format: "^[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}$"
                description: "User ORCID ID"
        """
        login_user(request.oauth.user)
        if request.content_type in ["text/csv", "text/tsv"]:
            task = Task.load_from_csv(request.data.decode("utf-8"), filename=self.filename)
            return self.jsonify_task(task)
        return self.handle_affiliation_task()


class AffiliationAPI(TaskResource):
    """Affiliation task services."""

    def get(self, task_id):
        """
        Retrieve the specified affiliation task.

        ---
        tags:
          - "affiliations"
        summary: "Retrieve the specified affiliation task."
        description: "Retrieve the specified affiliation task."
        produces:
          - "application/json"
        parameters:
          - name: "task_id"
            required: true
            in: "path"
            description: "Affiliation task ID."
            type: "integer"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/AffiliationTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.jsonify_task(task_id)

    def post(self, task_id):
        """Upload the task and completely override the affiliation task.

        ---
        tags:
          - "affiliations"
        summary: "Update the affiliation task."
        description: "Update the affiliation task."
        consumes:
          - application/json
          - text/yaml
        definitions:
        parameters:
          - name: "task_id"
            in: "path"
            description: "Affiliation task ID."
            required: true
            type: "integer"
          - in: body
            name: affiliationTask
            description: "Affiliation task."
            schema:
              $ref: "#/definitions/AffiliationTask"
        produces:
          - "application/json"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/AffiliationTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.handle_affiliation_task(task_id)

    def put(self, task_id):
        """Update the affiliation task.

        ---
        tags:
          - "affiliations"
        summary: "Update the affiliation task."
        description: "Update the affiliation task."
        consumes:
          - application/json
          - text/yaml
        parameters:
          - name: "task_id"
            in: "path"
            description: "Affiliation task ID."
            required: true
            type: "integer"
          - in: body
            name: affiliationTask
            description: "Affiliation task."
            schema:
              $ref: "#/definitions/AffiliationTask"
        produces:
          - "application/json"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/AffiliationTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.handle_affiliation_task(task_id)

    def patch(self, task_id):
        """Update the affiliation task.

        ---
        tags:
          - "affiliations"
        summary: "Update the affiliation task."
        description: "Update the affiliation task."
        consumes:
          - application/json
          - text/yaml
        parameters:
          - name: "task_id"
            in: "path"
            description: "Affiliation task ID."
            required: true
            type: "integer"
          - in: body
            name: affiliationTask
            description: "Affiliation task."
            schema:
              $ref: "#/definitions/AffiliationTask"
        produces:
          - "application/json"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/AffiliationTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.handle_affiliation_task(task_id)

    def delete(self, task_id):
        """Delete the specified affiliation task.

        ---
        tags:
          - "affiliations"
        summary: "Delete the specified affiliation task."
        description: "Delete the specified affiliation task."
        parameters:
          - name: "task_id"
            in: "path"
            description: "Affiliation task ID."
            required: true
            type: "integer"
        produces:
          - "application/json"
        responses:
          200:
            description: "Successful operation"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.delete_task(task_id)


api.add_resource(TaskList, "/api/v1.0/tasks")
api.add_resource(AffiliationListAPI, "/api/v1.0/affiliations")
api.add_resource(AffiliationAPI, "/api/v1.0/affiliations/<int:task_id>")


class FundListAPI(TaskResource):
    """Fund list API."""

    def load_from_json(self, task=None):
        """Load Funding records form the JSON upload."""
        return FundingRecord.load_from_json(
            request.data.decode("utf-8"), filename=self.filename, task=task)

    def post(self, *args, **kwargs):
        """Upload the fund task.

        ---
        tags:
          - "funds"
        summary: "Post the fund list task."
        description: "Post the fund list task."
        consumes:
        - application/json
        - text/csv
        - text/yaml
        produces:
        - application/json
        parameters:
        - name: "filename"
          required: false
          in: "query"
          description: "The batch process filename."
          type: "string"
        - name: body
          in: body
          description: "Fund task."
          schema:
            $ref: "#/definitions/FundTask"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/FundTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        definitions:
        - schema:
            id: FundTask
            properties:
              id:
                type: integer
                format: int64
              filename:
                type: string
              task-type:
                type: string
                enum:
                - fund
                - FUNDING
              created-at:
                type: string
                format: date-time
              expires-at:
                type: string
                format: date-time
              completed-at:
                type: string
                format: date-time
              records:
                type: array
                items:
                  $ref: "#/definitions/FundTaskRecord"
        - schema:
            id: FundTaskRecord
            type: object
        """
        login_user(request.oauth.user)
        if request.content_type in ["text/csv", "text/tsv"]:
            task = FundingRecord.load_from_csv(request.data.decode("utf-8"), filename=self.filename)
            return self.jsonify_task(task)
        return self.handle_task()


class FundAPI(FundListAPI):
    """Fund task services."""

    def get(self, task_id):
        """
        Retrieve the specified fund task.

        ---
        tags:
          - "funds"
        summary: "Retrieve the specified fund task."
        description: "Retrieve the specified fund task."
        produces:
          - "application/json"
        parameters:
          - name: "task_id"
            required: true
            in: "path"
            description: "Fund task ID."
            type: "integer"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/FundTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.jsonify_task(task_id)

    def post(self, task_id):
        """Upload the task and completely override the fund task.

        ---
        tags:
          - "funds"
        summary: "Update the fund task."
        description: "Update the fund task."
        consumes:
          - application/json
          - text/yaml
        definitions:
        parameters:
          - name: "task_id"
            in: "path"
            description: "Fund task ID."
            required: true
            type: "integer"
          - in: body
            name: fundTask
            description: "Fund task."
            schema:
              $ref: "#/definitions/FundTask"
        produces:
          - "application/json"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/FundTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.handle_task(task_id)

    def delete(self, task_id):
        """Delete the specified fund task.

        ---
        tags:
          - "funds"
        summary: "Delete the specified fund task."
        description: "Delete the specified fund task."
        parameters:
          - name: "task_id"
            in: "path"
            description: "Fund task ID."
            required: true
            type: "integer"
        produces:
          - "application/json"
        responses:
          200:
            description: "Successful operation"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.delete_task(task_id)


api.add_resource(FundListAPI, "/api/v1.0/funds")
api.add_resource(FundAPI, "/api/v1.0/funds/<int:task_id>")


class WorkListAPI(TaskResource):
    """Work list API."""

    def load_from_json(self, task=None):
        """Load Working records form the JSON upload."""
        return WorkRecord.load_from_json(
            request.data.decode("utf-8"), filename=self.filename, task=task)

    def post(self, *args, **kwargs):
        """Upload the work record processing task.

        ---
        tags:
          - "works"
        summary: "Post the work list task."
        description: "Post the work record processing task."
        consumes:
        - application/json
        - text/yaml
        produces:
        - application/json
        parameters:
        - name: "filename"
          required: false
          in: "query"
          description: "The batch process filename."
          type: "string"
        - name: body
          in: body
          description: "Work task."
          schema:
            $ref: "#/definitions/WorkTask"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/WorkTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        definitions:
        - schema:
            id: WorkTask
            properties:
              id:
                type: integer
                format: int64
              filename:
                type: string
              task-type:
                type: string
                enum:
                - WORK
                - WORKING
              created-at:
                type: string
                format: date-time
              expires-at:
                type: string
                format: date-time
              completed-at:
                type: string
                format: date-time
              records:
                type: array
                items:
                  $ref: "#/definitions/WorkTaskRecord"
        - schema:
            id: WorkTaskRecord
            type: object
        """
        login_user(request.oauth.user)
        if request.content_type in ["text/csv", "text/tsv"]:
            task = WorkRecord.load_from_csv(request.data.decode("utf-8"), filename=self.filename)
            return self.jsonify_task(task)
        return self.handle_task()


class WorkAPI(WorkListAPI):
    """Work record processing task services."""

    def get(self, task_id):
        """
        Retrieve the specified work record processing task.

        ---
        tags:
          - "works"
        summary: "Retrieve the specified work task."
        description: "Retrieve the specified work record processing task."
        produces:
          - "application/json"
        parameters:
          - name: "task_id"
            required: true
            in: "path"
            description: "Work task ID."
            type: "integer"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/WorkTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.jsonify_task(task_id)

    def post(self, task_id):
        """Upload the task and completely override the work record processing task.

        ---
        tags:
          - "works"
        summary: "Update the work task."
        description: "Update the work record processing task."
        consumes:
          - application/json
          - text/yaml
        definitions:
        parameters:
          - name: "task_id"
            in: "path"
            description: "Work task ID."
            required: true
            type: "integer"
          - in: body
            name: workTask
            description: "Work task."
            schema:
              $ref: "#/definitions/WorkTask"
        produces:
          - "application/json"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/WorkTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.handle_task(task_id)

    def delete(self, task_id):
        """Delete the specified work task.

        ---
        tags:
          - "works"
        summary: "Delete the specified work task."
        description: "Delete the specified work record processing task."
        parameters:
          - name: "task_id"
            in: "path"
            description: "Work task ID."
            required: true
            type: "integer"
        produces:
          - "application/json"
        responses:
          200:
            description: "Successful operation"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.delete_task(task_id)


api.add_resource(WorkListAPI, "/api/v1.0/works")
api.add_resource(WorkAPI, "/api/v1.0/works/<int:task_id>")


class PeerReviewListAPI(TaskResource):
    """PeerReview list API."""

    def load_from_json(self, task=None):
        """Load PeerReviewing records form the JSON upload."""
        return PeerReviewRecord.load_from_json(
            request.data.decode("utf-8"), filename=self.filename, task=task)

    def post(self, *args, **kwargs):
        """Upload the peer review record processing task.

        ---
        tags:
          - "peer-reviews"
        summary: "Post the peer review list task."
        description: "Post the peer review record processing task."
        consumes:
        - application/json
        - text/yaml
        produces:
        - application/json
        parameters:
        - name: "filename"
          required: false
          in: "query"
          description: "The batch process filename."
          type: "string"
        - name: body
          in: body
          description: "PeerReview task."
          schema:
            $ref: "#/definitions/PeerReviewTask"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/PeerReviewTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        definitions:
        - schema:
            id: PeerReviewTask
            properties:
              id:
                type: integer
                format: int64
              filename:
                type: string
              task-type:
                type: string
                enum:
                - peer_review
                - peer_reviewING
              created-at:
                type: string
                format: date-time
              expires-at:
                type: string
                format: date-time
              completed-at:
                type: string
                format: date-time
              records:
                type: array
                items:
                  $ref: "#/definitions/PeerReviewTaskRecord"
        - schema:
            id: PeerReviewTaskRecord
            type: object
        """
        login_user(request.oauth.user)
        if request.content_type in ["text/csv", "text/tsv"]:
            task = PeerReviewRecord.load_from_csv(request.data.decode("utf-8"), filename=self.filename)
            return self.jsonify_task(task)
        return self.handle_task()


class PeerReviewAPI(PeerReviewListAPI):
    """PeerReview record processing task services."""

    def get(self, task_id):
        """
        Retrieve the specified peer review record processing task.

        ---
        tags:
          - "peer-reviews"
        summary: "Retrieve the specified peer review task."
        description: "Retrieve the specified peer review record processing task."
        produces:
          - "application/json"
        parameters:
          - name: "task_id"
            required: true
            in: "path"
            description: "PeerReview task ID."
            type: "integer"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/PeerReviewTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.jsonify_task(task_id)

    def post(self, task_id):
        """Upload the task and completely override the peer review record processing task.

        ---
        tags:
          - "peer-reviews"
        summary: "Update the peer review task."
        description: "Update the peer review record processing task."
        consumes:
          - application/json
          - text/yaml
        definitions:
        parameters:
          - name: "task_id"
            in: "path"
            description: "PeerReview task ID."
            required: true
            type: "integer"
          - in: body
            name: peerReviewTask
            description: "PeerReview task."
            schema:
              $ref: "#/definitions/PeerReviewTask"
        produces:
          - "application/json"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/PeerReviewTask"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.handle_task(task_id)

    def delete(self, task_id):
        """Delete the specified peer-review task.

        ---
        tags:
          - "peer-reviews"
        summary: "Delete the specified peer review task."
        description: "Delete the specified peer review record processing task."
        parameters:
          - name: "task_id"
            in: "path"
            description: "PeerReview task ID."
            required: true
            type: "integer"
        produces:
          - "application/json"
        responses:
          200:
            description: "Successful operation"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        return self.delete_task(task_id)


api.add_resource(PeerReviewListAPI, "/api/v1.0/peer-reviews")
api.add_resource(PeerReviewAPI, "/api/v1.0/peer-reviews/<int:task_id>")


class UserListAPI(AppResourceList):
    """User list data service."""

    def get(self):
        """
        Return the list of the user belonging to the organisation.

        ---
        tags:
          - "users"
        summary: "Retrieve the list of all users."
        description: "Retrieve the list of all users."
        produces:
          - "application/json"
        parameters:
          - in: query
            name: from_date
            type: string
            minimum: 0
            description: The date starting from which user accounts were created and/or updated.
          - in: query
            name: to_date
            type: string
            minimum: 0
            description: The date until which user accounts were created and/or updated.
          - in: query
            name: page
            type: integer
            minimum: 0
            default: 1
            description: The number of the page of retrieved data starting counting from 1
          - in: query
            name: page_size
            type: integer
            minimum: 0
            default: 20
            description: The size of the data page
        responses:
          200:
            description: "successful operation"
            schema:
              id: UserListApiResponse
              type: array
              items:
                $ref: "#/definitions/HubUser"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
          422:
            description: "Unprocessable Entity"
        definitions:
        - schema:
            id: HubUser
            properties:
              orcid:
                type: "string"
                format: "^[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}$"
                description: "User ORCID ID"
              email:
                type: "string"
              eppn:
                type: "string"
              confirmed:
                type: "boolean"
              updated-at:
                type: "string"
                format: date-time
        """
        login_user(request.oauth.user)
        users = User.select().where(User.organisation == current_user.organisation)
        for a in ["from_date", "to_date"]:
            v = request.args.get(a)
            if not v:
                continue
            try:
                v = datetime.strptime(v, "%Y-%m-%d")
            except ValueError as ex:
                return jsonify({
                    "error": f"Failed to parse the date for \"{a}\": {v}",
                    "message": str(ex)
                }), 422
            if a.startswith("from"):
                users = users.where((User.created_at >= v) | (User.updated_at >= v))
            else:
                users = users.where((User.created_at <= v) & (User.updated_at <= v))
        return self.api_response(
            users,
            only=[User.email, User.eppn, User.name, User.orcid, User.confirmed, User.updated_at])


api.add_resource(UserListAPI, "/api/v1.0/users")


class UserAPI(AppResource):
    """User data service."""

    def get(self, identifier=None):
        """
        Verify if a user with given email address or ORCID ID exists.

        ---
        tags:
          - "users"
        summary: "Get user by user email or ORCID ID"
        description: ""
        produces:
          - "application/json"
        parameters:
          - name: "identifier"
            in: "path"
            description: "The unique identifier (email, ORCID iD, or eppn)"
            required: true
            type: "string"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/HubUser"
          400:
            description: "Invalid identifier supplied"
          404:
            description: "User not found"
        """
        identifier = identifier.strip()
        if validators.email(identifier):
            user = User.select().where((User.email == identifier)
                                       | (User.eppn == identifier)).first()
        elif ORCID_ID_REGEX.match(identifier):
            try:
                models.validate_orcid_id(identifier)
            except Exception as ex:
                return jsonify({"error": f"Incorrect identifier value '{identifier}': {ex}"}), 400
            user = User.select().where(User.orcid == identifier).first()
        else:
            return jsonify({"error": f"Incorrect identifier value: {identifier}."}), 400
        if user is None or (user.organisation != request.oauth.client.org
                            and not UserOrg.select().where(
                                UserOrg.org == request.oauth.client.org,
                                UserOrg.user == user,
                            ).exists()):
            return jsonify({
                "error": f"User with specified identifier '{identifier}' not found."
            }), 404

        return jsonify({
            "confirmed": user.confirmed,
            "email": user.email,
            "eppn": user.eppn,
            "orcid": user.orcid,
            "updated-at": user.updated_at,
        }), 200


api.add_resource(UserAPI, "/api/v1.0/users/<identifier>")


class TokenAPI(MethodView):
    """ORCID access token service."""

    decorators = [
        oauth.require_oauth(),
    ]

    def get(self, identifier=None):
        """
        Retrieve user access token and refresh token.

        ---
        tags:
          - "token"
        summary: "Retrieves user access and refresh tokens."
        description: ""
        produces:
          - "application/json"
        parameters:
          - name: "identifier"
            in: "path"
            description: "User identifier (either email, eppn or ORCID ID)"
            required: true
            type: "string"
        responses:
          200:
            description: "successful operation"
            schema:
              id: OrcidToken
              properties:
                access_token:
                  type: "string"
                  description: "ORCID API user profile access token"
                refresh_token:
                  type: "string"
                  description: "ORCID API user profile refresh token"
                scopes:
                  type: "string"
                  description: "ORCID API user token scopes"
                issue_time:
                  type: "string"
                expires_in:
                  type: "integer"
          400:
            description: "Invalid identifier supplied"
          401:
            $ref: "#/responses/Unauthorized"
          403:
            $ref: "#/responses/AccessDenied"
          404:
            $ref: "#/responses/NotFound"
        """
        identifier = identifier.strip()
        if validators.email(identifier):
            user = User.select().where((User.email == identifier)
                                       | (User.eppn == identifier)).first()
        elif ORCID_ID_REGEX.match(identifier):
            try:
                models.validate_orcid_id(identifier)
            except Exception as ex:
                return jsonify({"error": f"Incorrect identifier value '{identifier}': {ex}"}), 400
            user = User.select().where(User.orcid == identifier).first()
        else:
            return jsonify({"error": f"Incorrect identifier value: {identifier}."}), 400

        org = request.oauth.client.org
        if user is None or (user.organisation != request.oauth.client.org
                            and not UserOrg.select().where(
                                UserOrg.org == request.oauth.client.org,
                                UserOrg.user == user,
                            ).exists()):
            return jsonify({
                "error": f"User with specified identifier '{identifier}' not found."
            }), 404

        try:
            token = OrcidToken.get(user=user, org=org)
        except OrcidToken.DoesNotExist:
            return jsonify({
                "error":
                f"Token for the users {user} ({identifier}) affiliated with {org} not found."
            }), 404

        return jsonify({
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "scopes": token.scope,
            "issue_time": token.issue_time.isoformat(),
            "expires_in": token.expires_in,
        }), 200


app.add_url_rule(
    "/api/v1.0/tokens/<identifier>", view_func=TokenAPI.as_view("tokens"), methods=[
        "GET",
    ])


def get_spec(app):
    """Build API swagger scecifiction."""
    swag = swagger(app)
    swag["info"]["version"] = "1.0"
    swag["info"]["title"] = "ORCID HUB API"
    # swag["basePath"] = "/api/v1.0"
    swag["host"] = request.host  # "dev.orcidhub.org.nz"
    swag["consumes"] = ["application/json"]
    swag["produces"] = ["application/json"]
    swag["schemes"] = [request.scheme]
    swag["securityDefinitions"] = {
        "application": {
            "type": "oauth2",
            "tokenUrl": url_for("access_token", _external=True),
            "flow": "application",
            "scopes": {
                "write": "allows modifying resources",
                "read": "allows reading resources",
            }
        }
    }
    swag["security"] = [
        {
            "application": [
                "read",
                "write",
            ]
        },
    ]
    swag["tags"] = [
        {
            "name": "affiliations",
            "description": "Affiliation data management APIs",
            "externalDocs": {
                "url": "http://docs.orcidhub.org.nz/en/latest/writing_affiliation_items.html"
            },
        },
        {
            "name": "funds",
            "description": "Fund data management APIs",
            "externalDocs": {
                "url": "http://docs.orcidhub.org.nz/en/latest/writing_funding_items.html"
            },
        },
        {
            "name": "orcid-proxy",
            "description": "ORCID API proxy",
            "externalDocs": {
                "url": "https://api.sandbox.orcid.org"
            },
        },
        {
            "name": "webhooks",
            "description": "ORCID Webhook management",
            "externalDocs": {
                "url": "https://members.orcid.org/api/tutorial/webhooks"
            },
        },
    ]
    swag["parameters"] = {
        "orcidParam": {
            "in": "path",
            "name": "orcid",
            "required": True,
            "type": "string",
            "description": "User ORCID ID.",
            "format": "^[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}$",
        },
        "versionParam": {
            "in": "path",
            "name": "version",
            "required": True,
            "description": "ORCID API version",
            "type": "string",
            "enum": [
                "v2.0",
                "v2.1",
                "v3.0_rc1",
                "v3.0_rc2s",
                "v3.0",
            ],
        },
        "pathParam": {
            "in": "path",
            "name": "path",
            "required": True,
            "type": "string",
            "description": "The rest of the ORCID API entry point URL.",
        },
    }
    # Common responses:
    swag["responses"] = {
            "AccessDenied": {
                "description": "Access Denied",
                "schema": {"$ref": "#/definitions/Error"}
            },
            "Unauthorized": {
                "description": "Unauthorized",
                "schema": {"$ref": "#/definitions/Error"}
            },
            "NotFound": {
                "description": "The specified resource was not found",
                "schema": {"$ref": "#/definitions/Error"}
            },
    }
    swag["definitions"]["Error"] = {
        "properties": {
            "error": {
                "type": "string",
                "description": "Error type/name."
            },
            "message": {
                "type": "string",
                "description": "Error details explaining message."
            },
        }
    }
    # Webhooks:
    put_responses = {
        "201": {
            "description": "A webhoook successfully set up.",
        },
        "415": {
            "description": "Invalid call-back URL or missing ORCID iD.",
            "schema": {
                "$ref": "#/definitions/Error"
            },
        },
        "404": {
            "description": "Invalid ORCID iD.",
            "schema": {
                "$ref": "#/definitions/Error"
            },
        },
    }
    delete_responses = {
        "204": {
            "description": "A webhoook successfully unregistered.",
        },
        "415": {
            "description": "Invalid call-back URL or missing ORCID iD.",
            "schema": {
                "$ref": "#/definitions/Error"
            },
        },
        "404": {
            "description": "Invalid ORCID iD.",
            "schema": {
                "$ref": "#/definitions/Error"
            },
        },
    }
    swag["paths"]["/api/v1.0/{orcid}/webhook"] = {
        "parameters": [swag["parameters"]["orcidParam"]],
        "put": {
            "tags": ["webhooks"],
            "responses": put_responses,
        },
        "delete": {
            "tags": ["webhooks"],
            "responses": delete_responses,
        }
    }
    swag["paths"]["/api/v1.0/{orcid}/webhook/{callback_url}"] = {
        "parameters": [
            swag["parameters"]["orcidParam"],
            {
                "in": "path",
                "name": "callback_url",
                "required": True,
                "type": "string",
                "description":
                "The call-back URL that will receive a POST request when an update of a ORCID profile occurs.",
            },
        ],
        "put": {
            "tags": ["webhooks"],
            "responses": put_responses,
        },
        "delete": {
            "tags": ["webhooks"],
            "responses": delete_responses,
        }
    }
    # Proxy:
    swag["paths"]["/orcid/api/{version}/{orcid}"] = {
        "parameters": [
            swag["parameters"]["versionParam"],
            swag["parameters"]["orcidParam"],
        ],
        "get": {
            "tags": ["orcid-proxy"],
            "produces": [
                "application/vnd.orcid+xml; qs=5", "application/orcid+xml; qs=3",
                "application/xml", "application/vnd.orcid+json; qs=4",
                "application/orcid+json; qs=2", "application/json"
            ],
            "responses": {
                "200": {
                    "description": "Successful operation",
                    "schema": {
                        "type": "object"
                    }
                },
                "403": {
                    "description": "The user hasn't granted acceess to the profile.",
                    "schema": {"$ref": "#/definitions/Error"}
                },
                "404": {
                    "description": "Resource not found",
                    "schema": {"$ref": "#/definitions/Error"}
                },
                "415": {
                    "description": "Missing or invalid ORCID iD.",
                    "schema": {"$ref": "#/definitions/Error"}
                },
            },
        },
    }
    swag["paths"]["/orcid/api/{version}/{orcid}/{path}"] = {
        "parameters": [
            swag["parameters"]["versionParam"],
            swag["parameters"]["orcidParam"],
            swag["parameters"]["pathParam"],
        ],
        "delete": {
            "tags": ["orcid-proxy"],
            "produces": [
                "application/vnd.orcid+xml; qs=5", "application/orcid+xml; qs=3",
                "application/xml", "application/vnd.orcid+json; qs=4",
                "application/orcid+json; qs=2", "application/json"
            ],
            "responses": {
                "204": {
                    "description": "Record deleted",
                    "schema": {
                        "type": "object"
                    }
                },
                "403": {
                    "description": "The user hasn't granted acceess to the profile.",
                    "schema": {"$ref": "#/definitions/Error"}
                },
                "404": {
                    "description": "Resource not found",
                    "schema": {"$ref": "#/definitions/Error"}
                },
                "415": {
                    "description": "Missing or invalid ORCID iD.",
                    "schema": {"$ref": "#/definitions/Error"}
                },
            },
        },
        "get": {
            "tags": ["orcid-proxy"],
            "produces": [
                "application/vnd.orcid+xml; qs=5", "application/orcid+xml; qs=3",
                "application/xml", "application/vnd.orcid+json; qs=4",
                "application/orcid+json; qs=2", "application/json"
            ],
            "responses": {
                "200": {
                    "description": "Successful operation",
                    "schema": {
                        "type": "object"
                    }
                },
                "403": {
                    "description": "The user hasn't granted acceess to the profile.",
                    "schema": {"$ref": "#/definitions/Error"}
                },
                "404": {
                    "description": "Resource not found",
                    "schema": {"$ref": "#/definitions/Error"}
                },
                "415": {
                    "description": "Missing or invalid ORCID iD.",
                    "schema": {"$ref": "#/definitions/Error"}
                },
            },
        },
        "post": {
            "tags": ["orcid-proxy"],
            "consumes": [
                "application/vnd.orcid+xml; qs=5", "application/orcid+xml; qs=3",
                "application/xml", "application/vnd.orcid+json; qs=4",
                "application/orcid+json; qs=2", "application/json"
            ],
            "produces": [
                "application/vnd.orcid+xml; qs=5", "application/orcid+xml; qs=3",
                "application/xml", "application/vnd.orcid+json; qs=4",
                "application/orcid+json; qs=2", "application/json"
            ],
            "parameters": [{
                "in": "body",
                "name": "body",
                "required": False,
                "schema": {
                    "type": "object"
                }
            }],
            "responses": {
                "200": {
                    "description": "successful operation",
                    "schema": {
                        "type": "object"
                    }
                },
                "403": {
                    "description": "The user hasn't granted acceess to the profile.",
                    "schema": {"$ref": "#/definitions/Error"}
                },
                "404": {
                    "description": "Resource not found",
                    "schema": {"$ref": "#/definitions/Error"}
                },
                "415": {
                    "description": "Missing or invalid ORCID iD.",
                    "schema": {"$ref": "#/definitions/Error"}
                },
            },
        },
        "put": {
            "tags": ["orcid-proxy"],
            "consumes": [
                "application/vnd.orcid+xml; qs=5", "application/orcid+xml; qs=3",
                "application/xml", "application/vnd.orcid+json; qs=4",
                "application/orcid+json; qs=2", "application/json"
            ],
            "parameters": [{
                "in": "body",
                "name": "body",
                "required": False,
                "schema": {
                    "type": "object"
                }
            }],
            "responses": {
                "200": {
                    "description": "successful operation",
                    "schema": {
                        "type": "object"
                    }
                },
                "403": {
                    "description": "The user hasn't granted acceess to the profile.",
                    "schema": {"$ref": "#/definitions/Error"}
                },
                "404": {
                    "description": "Resource not found",
                    "schema": {"$ref": "#/definitions/Error"}
                },
                "415": {
                    "description": "Missing or invalid ORCID iD.",
                    "schema": {"$ref": "#/definitions/Error"}
                },
            }
        }
    }
    return swag


@app.route("/spec.json")
@app.route("/spec.yml")
@app.route("/spec.yaml")
@app.route("/spec")
def spec():
    """Return the specification of the API."""
    swag = get_spec(app)
    best = request.accept_mimetypes.best_match(["text/yaml", "application/x-yaml"])
    path = request.path
    if path.endswith(".yaml") or path.endswith(".yml") or (best in (
            "text/yaml",
            "application/x-yaml",
    ) and request.accept_mimetypes[best] > request.accept_mimetypes["application/json"]):
        return yamlfy(swag)
    else:
        return jsonify(swag)


@app.route("/api-docs")
@roles_required(Role.TECHNICAL, Role.SUPERUSER)
def api_docs():
    """Show Swagger UI for the latest/current Hub API and Data API."""
    client = Client.select().where(Client.org == current_user.organisation).first()
    return render_template("swaggerui.html", client=client)


def yamlfy(*args, **kwargs):
    """Create respose in YAML just like jsonify does it for JSON."""
    if args and kwargs:
        raise TypeError('yamlfy() behavior undefined when passed both args and kwargs')
    elif len(args) == 1:  # single args are passed directly to dumps()
        data = args[0]
    else:
        data = args or kwargs

    return current_app.response_class((dump_yaml(data), '\n'), mimetype="text/yaml")


@app.route("/orcid/api/<string:version>/<string:orcid>", methods=["GET", "POST", "PUT", "DELETE"])
@app.route(
    "/orcid/api/<string:version>/<string:orcid>/<path:rest>",
    methods=["GET", "POST", "PUT", "DELETE"])
@oauth.require_oauth()
def orcid_proxy(version, orcid, rest=None):
    """Handle proxied request..."""
    login_user(request.oauth.user)
    if not ORCID_API_VERSION_REGEX.match(version):
        return jsonify({
            "error": "Resource not found",
            "message": f"Incorrect version: {version}"
        }), 404
    try:
        validate_orcid_id(orcid)
    except Exception as ex:
        return jsonify({"error": str(ex), "message": "Missing or invalid ORCID iD."}), 415
    token = OrcidToken.select().join(User).where(
        User.orcid == orcid, OrcidToken.org == current_user.organisation).first()
    if not token:
        return jsonify({"message": "The user hasn't granted access to the user profile"}), 403

    orcid_api_host_url = app.config["ORCID_API_HOST_URL"]
    # CHUNK_SIZE = 1024
    # TODO: sanitize headers
    headers = {
        h: v
        for h, v in request.headers if h in
        ["Cache-Control", "User-Agent", "Accept", "Accept-Encoding", "Connection", "Content-Type"]
    }
    headers["Authorization"] = f"Bearer {token.access_token}"
    url = f"{orcid_api_host_url}{version}/{orcid}"
    # Swagger-UI sets 'path' to 'undefined':
    if rest and rest != "undefined":
        url += '/' + rest

    proxy_req = requests.Request(
        request.method, url, data=request.stream, headers=headers).prepare()
    session = requests.Session()
    # TODO: add time-out
    resp = session.send(proxy_req, stream=True)

    def generate():
        # for chunk in resp.raw.stream(decode_content=False, amt=CHUNK_SIZE):
        for chunk in resp.raw.stream(decode_content=False):
            yield chunk

    # TODO: verify if flask can create chunked responses: Transfer-Encoding: chunked
    proxy_headers = [(h, v) for h, v in resp.raw.headers.items() if h not in [
        "Transfer-Encoding",
    ]]
    proxy_resp = Response(
        stream_with_context(generate()), headers=proxy_headers, status=resp.status_code)
    return proxy_resp


@app.route("/api/v1.0/<string:orcid>/webhook", methods=["PUT", "DELETE"])
@app.route("/api/v1.0/<string:orcid>/webhook/<path:callback_url>", methods=["PUT", "DELETE"])
@oauth.require_oauth()
def register_webhook(orcid, callback_url=None):
    """Handle webhook registration for an individual user with direct client call-back."""
    login_user(request.oauth.user)

    try:
        validate_orcid_id(orcid)
    except Exception as ex:
        return jsonify({"error": "Missing or invalid ORCID iD.", "message": str(ex)}), 415
    if callback_url == "undefined":
        callback_url = None
    if callback_url:
        callback_url = unquote(callback_url)
        if not is_valid_url(callback_url):
            return jsonify({
                "error": "Invalid call-back URL",
                "message": f"Invalid call-back URL: {callback_url}"
            }), 415

    try:
        user = User.get(orcid=orcid)
    except User.DoesNotExist:
        return jsonify({
            "error": "Invalid ORCID iD.",
            "message": f"User with given ORCID ID '{orcid}' doesn't exist."
        }), 404

    orcid_resp = register_orcid_webhook(user, callback_url, delete=request.method == "DELETE")
    resp = make_response('', orcid_resp.status_code if orcid_resp else 204)
    if orcid_resp and "Location" in orcid_resp.headers:
        resp.headers["Location"] = orcid_resp.headers["Location"]

    return resp
