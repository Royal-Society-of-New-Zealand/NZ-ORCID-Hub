"""HUB API."""

from collections import defaultdict
from datetime import datetime
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
from yaml.dumper import Dumper
from yaml.representer import SafeRepresenter

from . import api, app, db, models, oauth
from .login_provider import roles_required
from .models import (ORCID_ID_REGEX, AffiliationRecord, Client, OrcidToken, PartialDate, Role,
                     Task, TaskType, User, UserOrg, validate_orcid_id)
from .schemas import affiliation_task_schema
from .utils import is_valid_url, register_orcid_webhook


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
            if isinstance(resp[0], Response) and isinstance(resp[1], int):
                resp[0].status_code = resp[1]
                return resp[0]
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
        """Test if the requst body content type is YAML."""
        return request.content_type in ["text/yaml", "application/x-yaml"]


def changed_path(name, value):
    """Create query stirng with a new paremeter value."""
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
        """Get the curretn queried page."""
        try:
            return int(request.args.get("page", 1))
        except:
            return 1

    @models.lazy_property
    def page_size(self):  # noqa: D402
        """Get the curretn query page size, default: 20."""
        try:
            return int(request.args.get("page_size", 20))
        except:
            return 20

    @models.lazy_property
    def next_link(self):
        """Get the next page link of the requsted resource."""
        return changed_path("page", self.page + 1)

    @models.lazy_property
    def previous_link(self):
        """Get the previous page link of the requsted resource."""
        if self.page <= 1:
            return
        return changed_path("page", self.page - 1)

    @models.lazy_property
    def first_link(self):
        """Get the first page link of the requsted resource."""
        return changed_path("page", 1)

    def api_response(self, query, exclude=None):
        """Create and return API response with pagination likns."""
        query = query.paginate(self.page, self.page_size)
        records = [r.to_dict(recurse=False, to_dashes=True, exclude=exclude) for r in query]
        resp = yamlfy(records) if prefers_yaml() else jsonify(records)
        resp.headers["Pagination-Page"] = self.page
        resp.headers["Pagination-Page-Size"] = self.page_size
        resp.headers["Pagination-Count"] = len(records)
        resp.headers["Link"] = f'<{request.full_path}>;rel="self"'
        if self.previous_link:
            resp.headers["Link"] += f', <{self.previous_link}>;rel="prev"'
        if len(records) == self.page_size and self.next_link:
            resp.headers["Link"] += f', <{self.next_link}>;rel="next"'
        return resp


class TaskResource(AppResource):
    """Common task ralated reource."""

    available_task_types = [t.name for t in TaskType]

    def dispatch_request(self, *args, **kwargs):
        """Do some pre-handling..."""
        parser = reqparse.RequestParser()
        parser.add_argument(
            "type", type=str, help="Task type: " + ", ".join(self.available_task_types))
        parser.add_argument(
            "filename", type=str, help="Filename of the task.")
        parsed_args = parser.parse_args()
        task_type = parsed_args.get("type")
        self.filename = parsed_args.get("filename")
        self.task_type = None if task_type is None else TaskType[task_type]
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
            task_dict = task.to_dict(
                recurse=False,
                to_dashes=True,
                exclude=[Task.created_by, Task.updated_by, Task.org, Task.task_type])
            task_dict["task-type"] = TaskType(task.task_type).name
            if TaskType(task.task_type) == TaskType.AFFILIATION:
                # import pdb; pdb.set_trace()
                records = task.affiliation_records
            else:
                records = task.funding_records
            task_dict["records"] = [
                r.to_dict(to_dashes=True, recurse=False, exclude=[AffiliationRecord.task])
                for r in records
            ]
            resp = jsonify(task_dict)
        else:
            resp = jsonify({"updated-at": task.updated_at})
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
            return jsonify({"error": "Unhandled except occured.", "exception": ex}), 400

        if task.created_by != current_user:
            abort(403)
        task.delete_instance()
        return {"message": "The task was successfully deletd."}

    def handle_affiliation_task(self, task_id=None):
        """Handle PUT, POST, or PATCH request. Request body expected to be encoded in JSON."""
        login_user(request.oauth.user)

        if self.is_yaml_request:
            try:
                data = yaml.load(request.data)
            except Exception as ex:
                return jsonify({
                    "error": "Ivalid request format. Only JSON, CSV, or TSV are acceptable.",
                    "message": str(ex)
                }), 415
        else:
            data = request.get_json()

        if not data:
            return jsonify({"error": "Ivalid request format. Only JSON, CSV, or TSV are acceptable."}), 415
        try:
            if request.method != "PATCH":
                jsonschema.validate(data, affiliation_task_schema)
        except jsonschema.exceptions.ValidationError as ex:
            return jsonify({"error": "Validation error.", "message": ex.message}), 422
        except Exception as ex:
            return jsonify({"error": "Unhandled except occured.", "exception": ex}), 400
        if "records" not in data:
            return jsonify({"error": "Validation error.", "message": "Missing affiliation records."}), 422

        with db.atomic():
            try:
                filename = (data.get("filename") or self.filename or datetime.utcnow().isoformat(timespec="seconds"))
                if task_id:
                    try:
                        task = Task.get(id=task_id)
                    except Task.DoesNotExist:
                        return jsonify({"error": "The task doesn't exist."}), 404
                    if task.created_by != current_user:
                        return jsonify({"error": "Access denied."}), 403
                else:
                    task = Task.create(filename=filename, user=current_user, org=current_user.organisation)

                if request.method == "POST" and task_id:
                    AffiliationRecord.delete().where(AffiliationRecord.task_id == task_id).execute()

                record_fields = AffiliationRecord._meta.fields.keys()
                for row in data["records"]:
                    if "id" in row and request.method in ["PUT", "PATCH"]:
                        rec = AffiliationRecord.get(id=row["id"])
                    else:
                        rec = AffiliationRecord(task=task)

                    # import pdb; pdb.set_trace()
                    for k, v in row.items():
                        if k == "id":
                            continue
                        k = k.replace('-', '_')
                        if k in record_fields and rec._data.get(k) != v:
                            rec._data[k] = PartialDate.create(v) if k.endswith("date") else v
                            rec._dirty.add(k)
                    if rec.is_dirty():
                        rec.save()

            except Exception as ex:
                db.rollback()
                app.logger.exception("Failed to hadle affiliation API request.")
                return jsonify({"error": "Unhandled except occured.", "exception": str(ex)}), 400

        return self.jsonify_task(task)


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
            in: "path"
            description: "The task type: AFFILIATION, FUNDING."
            required: false
            type: "string"
          - in: query
            name: page
            description: The number of the page of retrievd data starting counting from 1
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
            type: array
            items:
              type: object
              $ref: "#/definitions/Task"
          403:
            description: "Access Denied"
        """
        login_user(request.oauth.user)
        return self.api_response(
            Task.select().where(Task.org_id == current_user.organisation_id),
            exclude=[Task.created_by, Task.updated_by, Task.org])


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
                  type: object
                  $ref: "#/definitions/AffiliationTaskRecord"
        - schema:
            id: AffiliationTaskRecord
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
                required: true
              first-name:
                type: string
                required: true
              last-name:
                type: string
                required: true
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
                required: true
              start-date:
                type: string
                required: false
              end-date:
                type: string
                required: false
              processed-at:
                type: string
                format: date-time
                required: false
              status:
                type: string
                required: false
              orcid:
                type: string
                format: "^[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}$"
                description: "User ORCID ID"
                required: false
        produces:
        - application/json
        parameters:
        - name: "filename"
          in: "path"
          description: "The batch process filename."
          required: false
          type: "string"
        - name: body
          in: body
          description: "Affiliation task."
          required: true
          schema:
            $ref: "#/definitions/AffiliationTask"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/AffiliationTask"
          403:
            description: "Access Denied"
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
            in: "path"
            description: "Affiliation task ID."
            required: true
            type: "integer"
        responses:
          200:
            description: "successful operation"
            schema:
              $ref: "#/definitions/AffiliationTask"
          403:
            description: "Access Denied"
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
          403:
            description: "Access Denied"
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
          403:
            description: "Access Denied"
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
          403:
            description: "Access Denied"
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
          403:
            description: "Access Denied"
        """
        return self.delete_task(task_id)

    def head(self, task_id):
        """Handle HEAD request.

        ---
        tags:
          - "affiliations"
        summary: "Return task update time-stamp."
        description: "Return task update time-stamp."
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
          403:
            description: "Access Denied"
        """
        return self.jsonify_task(task_id)


api.add_resource(TaskList, "/api/v1.0/tasks")
api.add_resource(AffiliationListAPI, "/api/v1.0/affiliations")
api.add_resource(AffiliationAPI, "/api/v1.0/affiliations/<int:task_id>")


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
            description: The number of the page of retrievd data starting counting from 1
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
                type: "object"
                properties:
                  name:
                    type: string
                  orcid:
                    type: "string"
                    description: "User ORCID ID"
                  email:
                    type: "string"
                  eppn:
                    type: "string"
          403:
            description: "Access Denied"
          422:
            description: "Unprocessable Entity"
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
        return self.api_response(users)


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
              id: UserApiResponse
              properties:
                orcid:
                  type: "string"
                  format: "^[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}$"
                  description: "User ORCID ID"
                email:
                  type: "string"
                eppn:
                  type: "string"
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
            "orcid": user.orcid,
            "email": user.email,
            "eppn": user.eppn,
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
          403:
            description: "Access Denied"
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
    swag["consumes"] = [
        "application/json",
    ]
    swag["produces"] = [
        "application/json",
    ]
    swag["schemes"] = [
        request.scheme,
    ]
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
    return swag


@app.route("/spec.json")
def json_spec():
    """Return the specification of the API."""
    swag = get_spec(app)
    return jsonify(swag)


@app.route("/spec.yml")
@app.route("/spec.yaml")
def yaml_spec():
    """Return the specification of the API."""
    swag = get_spec(app)
    return yamlfy(swag)


@app.route("/spec")
def spec():
    """Return the specification of the API."""
    swag = get_spec(app)
    best = request.accept_mimetypes.best_match(["text/yaml", "application/x-yaml"])
    if (best in (
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


class SafeRepresenterWithISODate(SafeRepresenter):
    """Customized representer for datetaime rendering in ISO format."""

    def represent_datetime(self, data):
        """Customize datetime rendering in ISO format."""
        value = data.isoformat(timespec="seconds")
        return self.represent_scalar('tag:yaml.org,2002:timestamp', value)


def yamlfy(*args, **kwargs):
    """Create respose in YAML just like jsonify does it for JSON."""
    yaml.add_representer(datetime, SafeRepresenterWithISODate.represent_datetime, Dumper=Dumper)
    yaml.add_representer(defaultdict, SafeRepresenter.represent_dict)
    if args and kwargs:
        raise TypeError('yamlfy() behavior undefined when passed both args and kwargs')
    elif len(args) == 1:  # single args are passed directly to dumps()
        data = args[0]
    else:
        data = args or kwargs

    return current_app.response_class((yaml.dump(data), '\n'), mimetype="text/yaml")


@app.route("/orcid/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
@oauth.require_oauth()
def orcid_proxy(path=None):
    """Handle proxied request..."""
    login_user(request.oauth.user)
    version, orcid, *rest = path.split('/')
    # TODO: verify the version
    # TODO: add logging ...
    try:
        validate_orcid_id(orcid)
    except Exception as ex:
        return jsonify({"error": str(ex), "message": "Missing or invalid ORCID iD."}), 415
    token = OrcidToken.select().join(User).where(
        User.orcid == orcid, OrcidToken.org == current_user.organisation).first()
    if not token:
        return jsonify({"message": "The user hasn't granted acceess to the user profile"}), 403

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
    if rest:
        url += '/' + '/'.join(rest)

    proxy_req = requests.Request(request.method, url, data=request.stream, headers=headers).prepare()
    session = requests.Session()
    # TODO: add timemout
    resp = session.send(proxy_req, stream=True)

    def generate():
        # for chunk in resp.raw.stream(decode_content=False, amt=CHUNK_SIZE):
        for chunk in resp.raw.stream(decode_content=False):
            yield chunk

    # TODO: verify if flask can create chunked responses: Transfer-Encoding: chunked
    proxy_headers = [(h, v) for h, v in resp.raw.headers.items() if h not in ["Transfer-Encoding", ]]
    # import pdb; pdb.set_trace()
    proxy_resp = Response(
        stream_with_context(generate()), headers=proxy_headers, status=resp.status_code)
    return proxy_resp


@app.route("/api/v1.0/<string:orcid>/webhook/<path:callback_url>", methods=["PUT", "DELETE"])
@oauth.require_oauth()
def register_webhook(orcid, callback_url=None):
    """Handle webhook registration for an individual user with direct client call-back."""
    login_user(request.oauth.user)

    try:
        validate_orcid_id(orcid)
    except Exception as ex:
        return jsonify({"error": str(ex), "message": "Missing or invalid ORCID iD."}), 415
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
            "error": "Invalid ORCID ID.",
            "message": f"User with given ORCID ID '{orcid}' doesn't exist."
        }), 415

    orcid_resp = register_orcid_webhook(user, callback_url, delete=request.method == "DELETE")
    resp = make_response('', orcid_resp.status_code)
    if "Location" in orcid_resp.headers:
        resp.headers["Location"] = orcid_resp.headers["Location"]

    return resp
