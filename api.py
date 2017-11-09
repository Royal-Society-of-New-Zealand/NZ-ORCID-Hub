"""HUB API"""

from flask_peewee.rest import Authentication, RestResource
from flask import request, jsonify

import models
from application import oauth, app
from flask_oauthlib.utils import extract_params, create_response
from oauthlib.common import to_unicode, add_params_to_uri, urlencode
from flask_peewee.rest import RestAPI


class AppRestAuthentication(Authentication):
    """Use Flask-OAuthlib authentication and application authentication."""
    # TODO: add user role requierentes.

    def authorize(self):
        if request.method in self.protected_methods:
            return False

        # snippet taken for Flask-OAuthlib decorator require_oauth(...)
        for func in oauth._before_request_funcs:
            func()

        if hasattr(request, "oauth") and request.oauth:
            return True

        valid, req = oauth.verify_request(())
        print("****", valid, req)

        for func in oauth._after_request_funcs:
            valid, req = func(valid, req)

        if not valid:
            return False
        request.oauth = req

        return True

default_auth = AppRestAuthentication()
api = RestAPI(app, prefix="/api/v0.1", default_auth=default_auth, name="ORCID Hub Data")

class UserResource(RestResource):
    exclude = (
        "password",
        "email",
    )

api.register(models.Organisation)
api.register(models.User, UserResource)
api.setup()
