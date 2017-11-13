"""HUB API"""

from flask import jsonify, request
from flask_oauthlib.utils import create_response, extract_params
from flask_peewee.rest import Authentication, RestAPI, RestResource
from flask_peewee.utils import slugify
from oauthlib.common import add_params_to_uri, to_unicode, urlencode
from werkzeug.exceptions import NotFound

import models
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
api.register(models.User, UserResource)
api.setup()
