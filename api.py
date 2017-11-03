"""HUB API"""

from flask_peewee.rest import Authentication, RestResource

import models
from application import api


class UserResource(RestResource):
    exclude = (
        'password',
        'email',
    )


api.register(models.Organisation)
api.register(models.User)
api.setup()
