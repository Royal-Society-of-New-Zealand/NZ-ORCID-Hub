# -*- coding: utf-8 -*-
"""Swagger generated client 'monkey-patch' for logging API requests

isort:skip_file
"""

from config import ORCID_API_BASE, SCOPE_READ_LIMITED, SCOPE_ACTIVITIES_UPDATE, ORCID_BASE_URL
from flask_login import current_user
from models import OrcidApiCall, Affiliation, OrcidToken
from swagger_client import (configuration, rest, api_client, apis, MemberAPIV20Api, SourceClientId,
                            Source, OrganizationAddress, DisambiguatedOrganization, Employment,
                            Education, Organization)
from time import time
from urllib.parse import urlparse
from application import app

url = urlparse(ORCID_API_BASE)
configuration.host = url.scheme + "://" + url.hostname


class OrcidApiClient(api_client.ApiClient):
    def call_api(
            self,
            resource_path,
            method,
            path_params=None,
            query_params=None,
            header_params=None,
            body=None,
            post_params=None,
            files=None,
            response_type=None,
            auth_settings=None,
            callback=None,
            _return_http_data_only=None,
            collection_formats=None,
            _preload_content=False,  # Always get back response
            _request_timeout=None):
        # Add here pre-processing...
        res = super().call_api(
            resource_path,
            method,
            path_params=path_params,
            query_params=query_params,
            header_params=header_params,
            body=body,
            post_params=post_params,
            files=files,
            response_type=response_type,
            auth_settings=auth_settings,
            callback=callback,
            _return_http_data_only=_return_http_data_only,
            collection_formats=collection_formats,
            _preload_content=_preload_content,
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
                user_id=current_user.id if current_user else None,
                method=method,
                url=url,
                query_params=query_params,
                body=body,
                put_code=put_code)
        except Exception as ex:
            app.logger.errer(ex)
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
        if res and oac:
            oac.status = res.status
            oac.response_time_ms = round((time() - request_time) * 1000)
            if res.data:
                oac.response = res.data
            oac.save()

        return res


class MemberAPI(MemberAPIV20Api):
    """ORCID Mmeber API extension."""

    def __init__(self, org, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_config(org, user)

    def set_config(self, org, user):
        """Set up clietn configuration."""
        self.org = org
        self.user = user
        self.orcid_token = None
        try:
            self.orcid_token = OrcidToken.get(
                user=user, org=org, scope=SCOPE_READ_LIMITED[0] + "," + SCOPE_ACTIVITIES_UPDATE[0])
        except Exception as ex:
            app.logger.error(f"Exception occured while retriving ORCID Token {ex}")
            return None

        configuration.access_token = self.orcid_token.access_token

        url = urlparse(ORCID_BASE_URL)
        self.source_clientid = SourceClientId(
            host=url.hostname,
            path=org.orcid_client_id,
            uri="http://" + url.hostname + "/client/" + org.orcid_client_id)

        self.source = Source(
            source_orcid=None, source_client_id=self.source_clientid, source_name=org.name)

    def create_or_update_affiliation(self,
                                     affiliation=None,
                                     role=None,
                                     department=None,
                                     org_name=None,
                                     city=None,
                                     state=None,
                                     country=None,
                                     disambiguation_org_id=None,
                                     disambiguation_source=None,
                                     start_date=None,
                                     end_date=None,
                                     put_code=None,
                                     *args,
                                     **kwargs):
        """Creates or updates affiliation record of a user.

        Returns tuple (put-code, ORCID iD, created), where created is True if a new entry
        was created, otherwise - False.
        """

        if affiliation is None:
            app.logger.warning("Missing affiliation value.")
            raise Exception("Missing affiliation value.")

        organisation_address = OrganizationAddress(
            city=city or self.org.city, country=country or self.org.country)

        disambiguated_organization_details = DisambiguatedOrganization(
            disambiguated_organization_identifier=disambiguation_org_id or
            self.org.disambiguation_org_id,
            disambiguation_source=disambiguation_source or self.org.disambiguation_org_source)

        if affiliation == Affiliation.EMP:
            rec = Employment()
        if affiliation == Affiliation.EDU:
            rec = Education()
        else:
            app.logger.info(
                f"For {self.user} not able to determine affiliaton type with {self.org}")
            raise Exception(
                f"Unsupported affiliation type '{affiliation}' for {self.user} affiliaton type with {self.org}"
            )

        rec.source = self.source
        rec.organization = Organization(
            name=org_name or self.org.name,
            address=organisation_address,
            disambiguated_organization=disambiguated_organization_details)

        if put_code:
            rec.put_code = put_code

        rec.department_name = department
        rec.role_title = role
        if start_date:
            rec.start_date = start_date.as_orcid_dict()
        if end_date:
            rec.end_date = end_date.as_orcid_dict()

        try:
            if affiliation == Affiliation.EDU:
                api_call = self.update_employment if put_code else self.create_employment
            else:
                api_call = self.update_education if put_code else self.create_education

            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            app.logger.info(
                f"For {self.user} the ORCID record was {'updated' if put_code else 'created'} from {self.org}"
            )
            created = bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                except:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid

        except:
            app.logger.exception(f"For {self.user} encountered exception")
        else:
            return (put_code, orcid, created)


# yapf: disable
from swagger_client import *  # noqa: F401, F403, F405
api_client.RESTClientObject = OrcidRESTClientObject  # noqa: F405
apis.member_apiv20_api.ApiClient = OrcidApiClient  # noqa: F405
