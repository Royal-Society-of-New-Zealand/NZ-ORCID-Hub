"""HUB API"""

from flask import jsonify, request
from flask_oauthlib.utils import create_response, extract_params
from flask_peewee.rest import Authentication, RestAPI, RestResource
from oauthlib.common import add_params_to_uri, to_unicode, urlencode

import models
from application import app, oauth


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
