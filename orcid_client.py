# -*- coding: utf-8 -*-
"""Swagger generated client 'monkey-patch' for logging API requests

isort:skip_file
"""

from flask_login import current_user
from models import OrcidApiCall
from swagger_client import rest


class HubRESTClientObject(rest.RESTClientObject):
    def request(self,
                method,
                url,
                query_params=None,
                headers=None,
                body=None,
                post_params=None,
                _preload_content=True,
                _request_timeout=None,
                **kwargs):

        OrcidApiCall.create(
            user_id=current_user.id, method=method, url=url, query_params=query_params, body=body)
        print(url)
        super().request(method, url, query_params, headers, body, post_params, _preload_contente,
                        _request_timeout, **kwargs)


# yapf: disable
from swagger_client import *  # noqa: F401, F403
api_client.RESTClientObject = HubRESTClientObject
