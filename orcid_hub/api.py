"""HUB API."""

import yaml
from flask import current_app, jsonify, request, url_for
from flask.views import MethodView
from flask_peewee.rest import RestResource
from flask_peewee.utils import slugify
from flask_swagger import swagger
from werkzeug.exceptions import NotFound

from . import api, app, models, oauth
from .models import EMAIL_REGEX, ORCID_ID_REGEX, OrcidToken, User, UserOrg


class AppRestResource(RestResource):
    """Application REST Resource."""

    def get_api_name(self):
        """Pluralize the name based on the model."""
        return slugify(self.model.__name__ + 's')

    def response_forbidden(self):
        """Handle denied access. Return both status code and an error message."""
        return jsonify({"error": 'Forbidden'}), 403

    def response_bad_method(self):
        """Handle ivalid method ivokation. Return both status code and an error message."""
        return jsonify({"error": f'Unsupported method "{request.method}"'}), 405

    def response_bad_request(self):
        """Handle 'bad request'. Return both status code and an error message."""
        return jsonify({"error": 'Bad request'}), 400

    def api_detail(self, pk, method=None):
        """Handle 'data not found'. Return both status code and an error message."""
        try:
            return super().api_detail(pk, method)
        except NotFound:
            return jsonify({"error": 'Not found'}), 404


class UserResource(AppRestResource):
    """User resource."""

    exclude = (
        "password",
        "email",
    )


api.register(models.Organisation, AppRestResource)
api.register(models.Task, AppRestResource)
# api.register(models.User, UserResource)
api.setup()


@app.route('/api/me')
@app.route("/api/v0.1/me")
@oauth.require_oauth()
def me():
    """Get the token user data."""
    user = request.oauth.user
    return jsonify(email=user.email, name=user.name)


class UserAPI(MethodView):
    """User data service."""

    decorators = [
        oauth.require_oauth(),
    ]

    def get(self, identifier=None):
        """
        Verify if a user with given email address or ORCID ID exists.

        ---
        tags:
          - "user"
        summary: "Get user by user email or ORCID ID"
        description: ""
        produces:
          - "application/json"
        parameters:
          - name: "identifier"
            in: "path"
            description: "The name that needs to be fetched. Use user1 for testing. "
            required: true
            type: "string"
        responses:
          200:
            description: "successful operation"
            schema:
              id: UserApiResponse
              properties:
                found:
                  type: "boolean"
                result:
                  type: "object"
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
          403:
            description: "Access Denied"
          404:
            description: "User not found"
        """
        if identifier is None:
            return jsonify({"error": "Need at least one parameter: email, eppn or ORCID ID."}), 400

        identifier = identifier.strip()
        if EMAIL_REGEX.match(identifier):
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
        if user is None:
            return jsonify({
                "error": f"User with specified identifier '{identifier}' not found."
            }), 404

        if not UserOrg.select().where(UserOrg.org == request.oauth.client.org,
                                      UserOrg.user == user).exists():
            return jsonify({"error": "Access Denied"}), 403
        return jsonify({
            "found": True,
            "result": {
                "orcid": user.orcid,
                "email": user.email,
                "eppn": user.eppn
            }
        }), 200


app.add_url_rule(
    "/api/v0.1/users/<identifier>", view_func=UserAPI.as_view("users"), methods=[
        "GET",
    ])


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
                found:
                  type: "boolean"
                token:
                  type: "object"
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
        if identifier is None:
            return jsonify({"error": "Need at least one parameter: email or ORCID ID."}), 400

        identifier = identifier.strip()
        if EMAIL_REGEX.match(identifier):
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
        if user is None:
            return jsonify({
                "error": f"User with specified identifier '{identifier}' not found."
            }), 404

        org = request.oauth.client.org
        if not UserOrg.select().where(UserOrg.org == org, UserOrg.user == user).exists():
            return jsonify({"error": "Access Denied"}), 403

        try:
            token = OrcidToken.get(user=user, org=org)
        except OrcidToken.DoesNotExist:
            return jsonify({
                "error":
                f"Token for the users {user} ({identifier}) affiliated with {org} not found."
            }), 404

        return jsonify({
            "found": True,
            "token": {
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "issue_time": token.issue_time.isoformat(),
                "expires_in": token.expires_in
            }
        }), 200


app.add_url_rule(
    "/api/v0.1/tokens/<identifier>", view_func=TokenAPI.as_view("tokens"), methods=[
        "GET",
    ])


def get_spec(app):
    """Build API swagger scecifiction."""
    swag = swagger(app)
    swag["info"]["version"] = "0.1"
    swag["info"]["title"] = "ORCID HUB API"
    # swag["basePath"] = "/api/v0.1"
    swag["host"] = request.host  # "dev.orcidhub.org.nz"
    swag["consumes"] = [
        "application/json",
    ]
    swag["produces"] = [
        "application/json",
    ]
    swag["schemes"] = [
        "https",
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


def yamlfy(*args, **kwargs):
    """Create respose in YAML just like jsonify does it for JSON."""
    if args and kwargs:
        raise TypeError('yamlfy() behavior undefined when passed both args and kwargs')
    elif len(args) == 1:  # single args are passed directly to dumps()
        data = args[0]
    else:
        data = args or kwargs

    return current_app.response_class((yaml.dump(data), '\n'), mimetype="text/yaml")
