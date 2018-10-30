"""HUB Data API."""

from flask import jsonify, request
from flask_peewee.rest import RestResource
from flask_peewee.utils import slugify
from flask_peewee_swagger.swagger import Swagger
from werkzeug.exceptions import NotFound

from . import data_api, models


def plural(word):
    """Convert a reguralr noun to its regular plural form."""
    if word.endswith("fe"):
        # wolf -> wolves
        return word[:-2] + "ves"
    elif word.endswith('f'):
        # knife -> knives
        return word[:-1] + "ves"
    elif word.endswith('o'):
        # potato -> potatoes
        return word + "es"
    elif word.endswith("us"):
        # cactus -> cacti
        return word[:-2] + 'i'
    elif word.endswith("ion"):
        # criterion -> criteria
        return word + 's'
    elif word.endswith("on"):
        # criterion -> criteria
        return word[:-2] + 'a'
    elif word.endswith('y'):
        # community -> communities
        return word[:-1] + "ies"
    elif word[-1] in "sx" or word[-2:] in ["sh", "ch"]:
        return word + "es"
    elif word.endswith("an"):
        return word[:-2] + "en"
    else:
        return word + 's'


class DataResource(RestResource):
    """Application REST Resource."""

    allowed_methods = ["GET", "PATCH", "POST", "PUT", "DELETE"]

    def get_api_name(self):
        """Pluralize the name based on the model."""
        return slugify(plural(self.model.__name__))

    def response_forbidden(self):  # pragma: no cover
        """Handle denied access. Return both status code and an error message."""
        return jsonify({"error": 'Forbidden'}), 403

    def response_bad_method(self):  # pragma: no cover
        """Handle ivalid method ivokation. Return both status code and an error message."""
        return jsonify({"error": f'Unsupported method "{request.method}"'}), 405

    def response_bad_request(self):  # pragma: no cover
        """Handle 'bad request'. Return both status code and an error message."""
        return jsonify({"error": 'Bad request'}), 400

    def api_detail(self, pk, method=None):
        """Handle 'data not found'. Return both status code and an error message."""
        try:
            return super().api_detail(pk, method)
        except NotFound:  # pragma: no cover
            return jsonify({"error": 'Not found'}), 404

    def check_get(self, obj=None):
        """Pre-authorizing a GET request."""
        return True

    def check_post(self, obj=None):  # pragma: no cover
        """Pre-authorizing a POST request."""
        return True

    def check_put(self, obj):  # pragma: no cover
        """Pre-authorizing a PUT request."""
        return True

    def check_delete(self, obj):  # pragma: no cover
        """Pre-authorizing a DELETE request."""
        return True


class UserResource(DataResource):
    """User resource."""

    exclude = (
        "password",
        "email",
    )


data_api.register(models.Organisation, DataResource)
data_api.register(models.Task, DataResource)
data_api.register(models.User, UserResource)
data_api.setup()


common_spec = {
    "security": [{
        "application": ["read", "write"]
    }],
    "securityDefinitions": {
        "application": {
            "flow": "application",
            "scopes": {
                "read": "allows reading resources",
                "write": "allows modifying resources"
            },
            "tokenUrl": "/oauth/token",
            "type": "oauth2"
        }
    },
}

data_api_swagger = Swagger(data_api, swagger_version="2.0", extras=common_spec)
data_api_swagger.setup()
