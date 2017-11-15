"""HUB API"""

from flask import jsonify, request
from flask.views import MethodView
from flask_oauthlib.utils import create_response, extract_params
from flask_peewee.rest import Authentication, RestAPI, RestResource
from flask_peewee.utils import slugify
from oauthlib.common import add_params_to_uri, to_unicode, urlencode
from werkzeug.exceptions import NotFound
from flask_swagger import swagger

import models
from application import api, app, oauth
from models import EMAIL_REGEX, ORCID_ID_REGEX, User, UserOrg, OrcidToken


class AppRestResource(RestResource):
    def get_api_name(self):
        return slugify(self.model.__name__ + 's')

    def response_forbidden(self):
        return jsonify({"error": 'Forbidden'}), 403

    def response_bad_method(self):
        return jsonify({"error": f'Unsupported method "{request.method}"'}), 405

    def response_bad_request(self):
        return jsonify({"error": 'Bad request'}), 400

    def api_detail(self, pk, method=None):
        try:
            return super().api_detail(pk, method)
        except NotFound:
            return jsonify({"error": 'Not found'}), 404


class UserResource(AppRestResource):
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
    user = request.oauth.user
    return jsonify(email=user.email, name=user.name)


class UserAPI(MethodView):
    decorators = [
        oauth.require_oauth(),
    ]

    def get(self, identifier=None):
        """
        Verifies if a user with given email address or ORCID ID exists.
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
            return jsonify({"error": "Need at least one parameter: email or ORCID ID."}), 400
        try:
            if EMAIL_REGEX.match(identifier):
                user = User.get(email=identifier)
            elif ORCID_ID_REGEX.match(identifier):
                try:
                    models.validate_orcid_id(identifier)
                except Exception as ex:
                    return jsonify({
                        "error": f"Incorrect identifier value '{identifier}': {ex}"
                    }), 400
                user = User.get(orcid=identifier)
            else:
                return jsonify({"error": f"Incorrect identifier value: {identifier}."}), 400
        except User.DoesNotExist:
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
    decorators = [
        oauth.require_oauth(),
    ]

    def get(self, identifier=None):
        """
        Retrieves user access token and refresh token.
        ---
        tags:
          - "token"
        summary: "Retrieves user access token and refresh token."
        description: ""
        produces:
          - "application/json"
        parameters:
          - name: "identifier"
            in: "path"
            description: "User identifier (either email or ORCID ID)"
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
                      type: "dateTime"
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
        try:
            if EMAIL_REGEX.match(identifier):
                user = User.get(email=identifier)
            elif ORCID_ID_REGEX.match(identifier):
                try:
                    models.validate_orcid_id(identifier)
                except Exception as ex:
                    return jsonify({
                        "error": f"Incorrect identifier value '{identifier}': {ex}"
                    }), 400
                user = User.get(orcid=identifier)
            else:
                return jsonify({"error": f"Incorrect identifier value: {identifier}."}), 400
        except User.DoesNotExist:
            return jsonify({
                "error": f"User with specified identifier '{identifier}' not found."
            }), 404
        org = request.oauth.client.org
        if not UserOrg.select().where(UserOrg.org == org,
                                      UserOrg.user == user).exists():
            return jsonify({"error": "Access Denied"}), 403

        try:
            token = OrcidToken.get(user=user, org=org)
        except OrcidToken.DoesNotExist:
            return jsonify({
                "error": f"Token for the users {user} ({identifier}) affiliated with {org} not found."
            }), 404

        return jsonify({
            "found": True,
            "token": {
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "issue_time": token.issue_time,
                "expires_in": token.expires_in
            }
        }), 200


app.add_url_rule(
    "/api/v0.1/tokens/<identifier>", view_func=TokenAPI.as_view("tokens"), methods=[
        "GET",
    ])

@app.route("/spec")
def spec():
    swag = swagger(app)
    swag["info"]["version"] = "0.1"
    swag["info"]["title"] = "ORCID HUB API"
    swag["basePath"] = "/api/v0.1"
    swag["host"] = "dev.orcidhub.org.nz"
    return jsonify(swag)
