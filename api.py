"""HUB API"""

from flask import jsonify, request
from flask.views import MethodView
from flask_oauthlib.utils import create_response, extract_params
from flask_peewee.rest import Authentication, RestAPI, RestResource
from flask_peewee.utils import slugify
from oauthlib.common import add_params_to_uri, to_unicode, urlencode
from werkzeug.exceptions import NotFound

import models
from models import (EMAIL_REGEX, ORCID_ID_REGEX, User, UserOrg)
from application import api, app, oauth


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
    decorators = [oauth.require_oauth(), ]

    def get(self, identifier=None):
        if identifier is None:
            return jsonify({"error": "Need at least one parameter: email or ORCID ID."}), 400
        try:
            if EMAIL_REGEX.match(identifier):
                user = User.get(email=identifier)
            elif ORCID_ID_REGEX.match(identifier):
                try:
                    models.validate_orcid_id(identifier)
                except Exception as ex:
                    return jsonify({"error": f"Incorrect identifier value '{identifier}': {ex}"}), 400
                user = User.get(orcid=identifier)
            else:
                return jsonify({"error": f"Incorrect identifier value: {identifier}."}), 400
        except User.DoesNotExist:
            return jsonify({"error": f"User with specified identifier '{identifier}' not found."}), 404
        if not UserOrg.select().where(UserOrg.org == request.oauth.client.org, UserOrg.user == user).exists():
            return jsonify({"error": "Access Denied"}), 403
        return jsonify({
            "found": True,
            "resut": {
                "orcid": user.orcid,
                "email": user.email,
                "eppn": user.eppn
        }}), 200

app.add_url_rule("/api/v0.1/users/<identifier>",
        view_func=UserAPI.as_view("users"),
        methods=["GET", ])

