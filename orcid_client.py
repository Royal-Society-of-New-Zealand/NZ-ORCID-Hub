# -*- coding: utf-8 -*-
"""Swagger generated client 'monkey-patch' for logging API requests

isort:skip_file
"""

from config import ORCID_API_BASE
from flask_login import current_user
from models import OrcidApiCall
from swagger_client import configuration, rest, api_client, models
from time import time
from urllib.parse import urlparse

url = urlparse(ORCID_API_BASE)
configuration.host = url.scheme + "://" + url.hostname


class OrcidApiClient(api_client.ApiClient):

    def call_api(self, resource_path, method,
                 path_params=None, query_params=None, header_params=None,
                 body=None, post_params=None, files=None,
                 response_type=None, auth_settings=None, callback=None,
                 _return_http_data_only=None, collection_formats=None, _preload_content=True,
                 _request_timeout=None):
        # Add here pre-processing...
        res = super().call_api(resource_path, method,
                 path_params=path_params, query_params=query_params, header_params=header_params,
                 body=body, post_params=post_params, files=files,
                 response_type=response_type, auth_settings=auth_settings, callback=callback,
                 _return_http_data_only=_return_http_data_only, collection_formats=collection_formats, _preload_content=_preload_content,
                 _request_timeout=_request_timeout)
        # Add here post-processing...
        return res


class OrcidRESTClientObject(rest.RESTClientObject):
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

        request_time = time()
        put_code = body.get("put-code") if body else None
        try:
            oac = OrcidApiCall.create(
                user_id=current_user.id,
                method=method,
                url=url,
                query_params=query_params,
                body=body,
                put_code=put_code)
        except Exception as ex:
            # TODO: log the failure
            pass
        res = super().request(
            method=method,
            url=url,
            query_params=query_params,
            headers=headers,
            body=body,
            post_params=post_params,
            _preload_content=_preload_content,
            _request_timeout=_request_timeout,
            **kwargs)
        print("*** STATUS:", res.status)
        if res and oac:
            oac.status = res.status
            oac.response_time_ms = round((time() - request_time) * 1000)
            if res.data:
                oac.response = res.data
            oac.save()

        return res


# yapf: disable
from swagger_client import *  # noqa: F401, F403, F405
api_client.RESTClientObject = OrcidRESTClientObject  # noqa: F405
apis.member_apiv20_api.ApiClient = OrcidApiClient  # noqa: F405
