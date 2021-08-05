# -*- coding: utf-8 -*-
"""
Swagger generated client 'monkey-patch' for logging API requests.

isort:skip_file
"""

from .config import ORCID_API_BASE, ORCID_BASE_URL
from flask_login import current_user
from .models import (
    OrcidApiCall,
    Affiliation,
    AffiliationExternalId,
    OrcidToken,
    FundingContributor as FundingCont,
    Log,
    ExternalId as ExternalIdModel,
    NestedDict,
    WorkContributor as WorkCont,
    WorkExternalId,
    PeerReviewExternalId,
)
from orcid_api import configuration, rest, api_client, MemberAPIV20Api, SourceClientId, Source
import orcid_api_v3 as v3
from orcid_api.rest import ApiException
from time import time
from urllib.parse import urlparse
from . import app
import json

url = urlparse(ORCID_API_BASE)
host = url.scheme + "://" + url.hostname
configuration.host = host


# ORCID API Scopes:
ACTIVITIES_UPDATE = "/activities/update"
READ_LIMITED = "/read-limited"
AUTHENTICATE = "/authenticate"
PERSON_UPDATE = "/person/update"


class OrcidRESTClientObjectMixing:
    """REST Client with call logging."""

    def request(
        self,
        method,
        url,
        query_params=None,
        headers=None,
        body=None,
        post_params=None,
        _preload_content=True,
        _request_timeout=None,
        **kwargs,
    ):
        """Exectue REST API request and logs both request, response and the restponse time."""
        request_time = time()
        put_code = body.get("put-code") if body else None
        try:
            oac = OrcidApiCall.create(
                user_id=current_user.id if current_user else None,
                method=method,
                url=url,
                query_params=query_params,
                body=body,
                put_code=put_code,
            )
        except Exception:
            app.logger.exception("Failed to create API call log entry.")
            oac = None
        try:
            res = super().request(
                method=method,
                url=url,
                query_params=query_params,
                headers=headers,
                body=body,
                post_params=post_params,
                _preload_content=_preload_content,
                _request_timeout=_request_timeout,
                **kwargs,
            )
        except (ApiException, v3.rest.ApiException) as ex:
            if oac:
                oac.status = ex.status
                if ex.data:
                    oac.response = ex.data
        else:
            if res and oac:
                oac.status = res.status
                if res.data:
                    oac.response = res.data
        finally:
            oac.response_time_ms = round((time() - request_time) * 1000)
            oac.save()

        return res


class OrcidRESTClientObject(OrcidRESTClientObjectMixing, rest.RESTClientObject):
    """REST Client with call logging."""

    pass


class OrcidRESTClientObjectV3(OrcidRESTClientObjectMixing, v3.rest.RESTClientObject):
    """REST Client with call logging."""

    def __init__(self, *args, **kwargs):
        """Override the default host."""
        super().__init__(*args, **kwargs)
        self.host = host


class MemberAPIMixin:
    """ORCID Mmeber API extension."""

    DEFAULT_VERSION = "v2.0"
    content_type = "application/json"

    def __init__(
        self, org=None, user=None, access_token=None, version=DEFAULT_VERSION, *args, **kwargs
    ):
        """Set up the configuration with the access token given to the org. by the user."""
        super().__init__(*args, **kwargs)
        self.set_config(org, user, access_token, version)

    def get_token(self, scopes=READ_LIMITED + "," + ACTIVITIES_UPDATE):
        """Retrieve the user ORCID API access token given the the organisation."""
        return (
            OrcidToken.select()
            .where(
                OrcidToken.user_id == self.user.id,
                OrcidToken.org_id == self.org.id,
                OrcidToken.scopes.contains(scopes),
            )
            .first()
        )

    def set_config(self, org=None, user=None, access_token=None, version=None):
        """Set up clietn configuration."""
        # global configuration
        if org is None:
            org = user.organisation
        self.org = org
        self.user = user
        if version:
            self.version = version

        url = urlparse(ORCID_BASE_URL)
        self.source_clientid = SourceClientId(
            host=url.hostname,
            path=org.orcid_client_id,
            uri="https://"
            + url.hostname
            + "/client/"
            + (org.orcid_client_id if org.orcid_client_id else ""),
        )
        self.source = Source(
            source_orcid=None, source_client_id=self.source_clientid, source_name=org.name
        )

        if access_token is None and user:
            orcid_token = self.get_token()
            if not orcid_token:
                access_token = None
                app.logger.error("Failed to find an ORCID API access token.")
            else:
                access_token = orcid_token.access_token

        if access_token:
            if hasattr(self.api_client, "configuration"):
                self.api_client.configuration.access_token = access_token
            else:
                configuration.access_token = access_token

    def get_record(self):
        """Fetch record details. (The generated one is broken)."""
        resp = self.get()
        try:
            resp, code, headers = self.api_client.call_api(
                f"/{self.version}/{self.user.orcid}",
                "GET",
                header_params={"Accept": self.content_type},
                response_type=None,
                auth_settings=["orcid_auth"],
                _preload_content=False,
            )
        except (ApiException, v3.rest.ApiException) as ex:
            if ex.status == 401:
                orcid_token = self.get_token()
                if orcid_token:
                    orcid_token.delete_instance()
                else:
                    app.logger.exception("Exception occurred while retrieving ORCID Token")
                    return None
            app.logger.error(f"ApiException Occurred: {ex}")
            return None

        if code != 200:
            app.logger.error(f"Failed to retrieve ORDIC profile. Code: {code}.")
            app.logger.info(f"Headers: {headers}")
            app.logger.info(f"Body: {resp.data.decode()}")
            return None

        return json.loads(resp.data.decode(), object_pairs_hook=NestedDict)

    def get_resources(self):
        """Fetch all research resources linked to the user profile."""
        resp = self.get("research-resources")
        if resp.status != 200:
            app.logger.error(f"Failed to retrieve research resources. Code: {resp.status}.")
            app.logger.info(f"Headers: {resp.headers}")
            app.logger.info(f"Body: {resp.data.decode()}")
            return None
        return resp.json

    def is_emp_or_edu_record_present(self, affiliation_type):
        """Determine if there is already an affiliation record for the user.

        Returns:
            Either False or put-code, if there is an affiliation record.

        """
        try:
            if affiliation_type == Affiliation.EMP:
                resp = self.view_employmentsv3(self.user.orcid, _preload_content=False)
            else:
                resp = self.view_educationsv3(self.user.orcid, _preload_content=False)

            data = json.loads(resp.data)

            for record in data.get("affiliation-group"):
                r = (
                    record.get("summaries")[0].get("employment-summary")
                    if affiliation_type == Affiliation.EMP
                    else record.get("summaries")[0].get("education-summary")
                )

                if r.get("source").get("source-client-id") and self.org.orcid_client_id == r.get(
                    "source"
                ).get("source-client-id").get("path"):
                    app.logger.info(
                        f"For {self.user} there is {affiliation_type!s} "
                        "present on ORCID profile."
                    )
                    return r["put-code"]

        except (ApiException, v3.rest.ApiException) as apiex:
            app.logger.error(
                f"For {self.user} while checking for employment and education records, Encountered Exception: {apiex}"
            )
            return False
        except Exception:
            app.logger.exception("Failed to verify presence of employment or education record.")
            return False
        return False

    def create_or_update_record_id_group(
        self, org=None, group_name=None, group_id=None, description=None, type=None, put_code=None
    ):
        """Create or update group id record."""
        rec = v3.GroupIdRecord()  # noqa: F405

        rec.name = group_name
        rec.group_id = group_id
        rec.description = description
        rec.type = type
        if put_code:
            rec.put_code = put_code

        try:
            api_call = self.update_group_id_recordv3 if put_code else self.create_group_id_recordv3

            params = dict(body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)

            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    _, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                except:
                    app.logger.exception("Failed to get put-code from the response.")
                    raise Exception("Failed to get put-code from the response.")
        except (ApiException, v3.rest.ApiException) as ex:
            if ex.status == 404:
                app.logger.exception(
                    f"For {self.user} encountered exception, So updating related put_code"
                )
            raise ex
        except:
            app.logger.exception(f"For {self.user} encountered exception")
        else:
            return (put_code, created)

    def create_or_update_peer_review(self, task_by_user, *args, **kwargs):
        """Create or update peer review record of a user."""
        pr = task_by_user.record
        pi = pr.invitee
        put_code = pi.put_code
        visibility = pi.visibility

        rec = v3.PeerReviewV30()  # noqa: F405

        if pr.reviewer_role:
            rec.reviewer_role = pr.reviewer_role.replace("_", "-").lower()

        if pr.review_url:
            rec.review_url = v3.UrlV30(value=pr.review_url)  # noqa: F405

        if pr.review_type:
            rec.review_type = pr.review_type.replace("_", "-").lower()

        if pr.review_completion_date:
            rec.review_completion_date = pr.review_completion_date.as_orcid_dict()

        if pr.review_group_id:
            rec.review_group_id = pr.review_group_id

        if pr.subject_external_id_type and pr.subject_external_id_value:
            subject_external_id_relationship = "self"
            if pr.subject_external_id_relationship:
                subject_external_id_relationship = pr.subject_external_id_relationship.replace(
                    "_", "-"
                ).lower()
            subject_external_id_url = None
            if pr.subject_external_id_url:
                subject_external_id_url = v3.UrlV30(value=pr.subject_external_id_url)  # noqa: F405
            rec.subject_external_identifier = v3.ExternalIDV30(
                external_id_type=pr.subject_external_id_type,
                external_id_value=pr.subject_external_id_value,
                external_id_relationship=subject_external_id_relationship,
                external_id_url=subject_external_id_url,
            )  # noqa: F405

        if pr.subject_container_name:
            rec.subject_container_name = v3.TitleV30(value=pr.subject_container_name)  # noqa: F405

        if pr.subject_type:
            rec.subject_type = pr.subject_type.replace("_", "-").lower()

        if pr.subject_name_title:
            title = v3.TitleV30(value=pr.subject_name_title)  # noqa: F405
            subtitle = None
            if pr.subject_name_subtitle:
                subtitle = v3.SubtitleV30(value=pr.subject_name_subtitle)  # noqa: F405
            translated_title = None
            if pr.subject_name_translated_title_lang_code and pr.subject_name_translated_title:
                translated_title = v3.TranslatedTitleV30(
                    value=pr.subject_name_translated_title,  # noqa: F405
                    language_code=pr.subject_name_translated_title_lang_code,
                )
            rec.subject_name = v3.SubjectNameV30(
                title=title, subtitle=subtitle, translated_title=translated_title  # noqa: F405
            )

        if pr.subject_url:
            rec.subject_url = v3.UrlV30(value=pr.subject_url)  # noqa: F405

        organisation_address = v3.OrganizationAddressV30(
            city=pr.convening_org_city or self.org.city,
            country=pr.convening_org_country or self.org.country,
            region=pr.convening_org_region or self.org.region,
        )

        disambiguated_organization_details = v3.DisambiguatedOrganizationV30(
            disambiguated_organization_identifier=pr.convening_org_disambiguated_identifier
            or self.org.disambiguated_id,  # noqa: E501
            disambiguation_source=pr.convening_org_disambiguation_source
            or self.org.disambiguation_source,
        )

        rec.convening_organization = v3.OrganizationV30(
            name=pr.convening_org_name or self.org.name,
            address=organisation_address,
            disambiguated_organization=disambiguated_organization_details,
        )

        if put_code:
            rec.put_code = pi.put_code

        if visibility:
            rec.visibility = visibility.replace("_", "-").lower()

        external_ids = []
        if pr.id:
            external_ids = [
                v3.ExternalIDV30(  # noqa: F405
                    external_id_type=eid.type if eid.type else "grant_number",
                    external_id_value=eid.value,
                    external_id_url=v3.UrlV30(value=eid.url) if eid.url else None,
                    external_id_relationship=eid.relationship.replace("_", "-").lower()
                    if eid.relationship
                    else "self",
                )
                for eid in PeerReviewExternalId.select()
                .where(PeerReviewExternalId.record_id == pr.id)
                .order_by(PeerReviewExternalId.id)
            ]
        if external_ids:
            rec.review_identifiers = v3.ExternalIDsV30(external_id=external_ids)  # noqa: F405

        try:
            api_call = self.update_peer_reviewv3 if put_code else self.create_peer_reviewv3

            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            app.logger.info(
                f"For {self.user} the ORCID record was {'updated' if put_code else 'created'} from {self.org}"
            )
            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                    visibility = None
                except:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid
                visibility = (
                    json.loads(resp.data).get("visibility") if hasattr(resp, "data") else None
                )

        except (ApiException, v3.rest.ApiException) as ex:
            if ex.status == 404:
                pi.put_code = None
                pi.save()
                app.logger.exception(
                    f"For {self.user} encountered exception, So updating related put_code"
                )
            raise ex
        except:
            app.logger.exception(f"For {self.user} encountered exception")
        else:
            return (put_code, orcid, created, visibility)

    def create_or_update_work(self, task_by_user, *args, **kwargs):
        """Create or update work record of a user."""
        wr = task_by_user.record
        wi = wr.invitee
        put_code = wi.put_code
        visibility = wi.visibility

        rec = v3.WorkV30()  # noqa: F405

        if put_code:
            rec.put_code = put_code

        if wr.title:
            title = v3.TitleV30(value=wr.title)  # noqa: F405
            subtitle = None
            if wr.subtitle:
                subtitle = v3.SubtitleV30(value=wr.subtitle)  # noqa: F405
            translated_title = None
            if wr.translated_title and wr.translated_title_language_code:
                translated_title = v3.TranslatedTitleV30(
                    value=wr.translated_title, language_code=wr.translated_title_language_code
                )  # noqa: F405
            rec.title = v3.WorkTitleV30(
                title=title, subtitle=subtitle, translated_title=translated_title
            )  # noqa: F405

        if wr.journal_title:
            rec.journal_title = v3.TitleV30(value=wr.journal_title)  # noqa: F405

        if wr.short_description:
            rec.short_description = wr.short_description

        if wr.citation_type and wr.citation_value:
            rec.citation = v3.Citation(
                citation_type=wr.citation_type.replace("_", "-").lower(),
                citation_value=wr.citation_value,
            )  # noqa: F405

        if wr.type:
            rec.type = wr.type.replace("_", "-").lower()

        if wr.publication_date:
            rec.publication_date = wr.publication_date.as_orcid_dict()

        external_ids = []
        contributors = []

        if wr.id:
            external_ids = [
                v3.ExternalIDV30(  # noqa: F405
                    external_id_type=eid.type if eid.type else "grant_number",
                    external_id_value=eid.value,
                    external_id_url=v3.UrlV30(value=eid.url) if eid.url else None,
                    external_id_relationship=eid.relationship.replace("_", "-").lower()
                    if eid.relationship
                    else "self",
                )
                for eid in WorkExternalId.select()
                .where(WorkExternalId.record_id == wr.id)
                .order_by(WorkExternalId.id)
            ]
            url = urlparse(ORCID_BASE_URL)
            contributors = [
                v3.ContributorV30(  # noqa: F405
                    contributor_orcid=v3.ContributorOrcidV30(
                        uri="https://" + url.hostname + "/" + wid.orcid,
                        path=wid.orcid,
                        host=url.hostname,
                    )
                    if wid.orcid
                    else None,
                    credit_name=v3.CreditNameV30(value=wid.name) if wid.name else None,
                    contributor_email=v3.ContributorEmailV30(value=wid.email)
                    if wid.email
                    else None,
                    contributor_attributes=v3.ContributorAttributesV30(
                        contributor_sequence=wid.contributor_sequence.replace("_", "-").lower()
                        if wid.contributor_sequence
                        else None,
                        contributor_role=wid.role.replace("_", "-").lower() if wid.role else None,
                    ),
                )
                for wid in WorkCont.select()
                .where(WorkCont.record_id == wr.id)
                .order_by(WorkCont.contributor_sequence)
            ]

        if external_ids:
            rec.external_ids = v3.ExternalIDsV30(external_id=external_ids)  # noqa: F405

        if wr.url:
            rec.url = v3.UrlV30(value=wr.url)  # noqa: F405

        if contributors:
            rec.contributors = v3.WorkContributorsV30(contributor=contributors)  # noqa: F405

        if wr.language_code:
            rec.language_code = wr.language_code

        if wr.country:
            rec.country = v3.CountryV30(value=wr.country)  # noqa: F405

        if visibility:
            rec.visibility = visibility.replace("_", "-").lower()

        try:
            api_call = self.update_workv3 if put_code else self.create_workv3

            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            app.logger.info(
                f"For {self.user} the ORCID record was {'updated' if put_code else 'created'} from {self.org}"
            )
            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                    visibility = None
                except:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid
                visibility = (
                    json.loads(resp.data).get("visibility") if hasattr(resp, "data") else None
                )

        except (ApiException, v3.rest.ApiException) as ex:
            if ex.status == 404:
                wi.put_code = None
                wi.save()
                app.logger.exception(
                    f"For {self.user} encountered exception, So updating related put_code"
                )
            raise ex
        except:
            app.logger.exception(f"For {self.user} encountered exception")
        else:
            return (put_code, orcid, created, visibility)

    def create_or_update_funding(self, task_by_user, *args, **kwargs):
        """Create or update funding record of a user."""
        fr = task_by_user.record
        fi = fr.invitee
        put_code = fi.put_code
        visibility = fi.visibility

        rec = v3.FundingV30()  # noqa: F405

        if put_code:
            rec.put_code = put_code

        if fr.type:
            rec.type = fr.type.replace("_", "-").lower()

        if fr.organization_defined_type:
            rec.organization_defined_type = v3.OrganizationDefinedFundingSubTypeV30(
                value=fr.organization_defined_type
            )  # noqa: F405

        if fr.title:
            title = v3.TitleV30(value=fr.title)  # noqa: F405
            translated_title = None
            if fr.translated_title and fr.translated_title_language_code:
                translated_title = v3.TranslatedTitleV30(
                    value=fr.translated_title, language_code=fr.translated_title_language_code
                )  # noqa: F405
            rec.title = v3.FundingTitleV30(
                title=title, translated_title=translated_title
            )  # noqa: F405

        if fr.short_description:
            rec.short_description = fr.short_description

        if fr.amount and fr.currency:
            rec.amount = v3.AmountV30(value=fr.amount, currency_code=fr.currency)  # noqa: F405

        if fr.url:
            rec.url = v3.UrlV30(value=fr.url)

        if fr.start_date:
            rec.start_date = fr.start_date.as_orcid_dict()
        if fr.end_date:
            rec.end_date = fr.end_date.as_orcid_dict()

        organisation_address = v3.OrganizationAddressV30(
            city=fr.city or self.org.city,
            country=fr.country or self.org.country,
            region=fr.region or self.org.region,
        )

        disambiguated_organization_details = v3.DisambiguatedOrganizationV30(
            disambiguated_organization_identifier=fr.disambiguated_id or self.org.disambiguated_id,
            disambiguation_source=fr.disambiguation_source or self.org.disambiguation_source,
        )

        rec.organization = v3.OrganizationV30(
            name=fr.org_name or self.org.name,
            address=organisation_address,
            disambiguated_organization=disambiguated_organization_details,
        )

        external_ids = []
        contributors = []

        if fr.id:
            external_ids = [
                v3.ExternalIDV30(  # noqa: F405
                    external_id_type=eid.type if eid.type else "grant_number",
                    external_id_value=eid.value,
                    external_id_url=v3.UrlV30(value=eid.url) if eid.url else None,
                    external_id_relationship=eid.relationship.replace("_", "-").lower()
                    if eid.relationship
                    else "self",
                )
                for eid in ExternalIdModel.select()
                .where(ExternalIdModel.record_id == fr.id)
                .order_by(ExternalIdModel.id)
            ]
            url = urlparse(ORCID_BASE_URL)
            contributors = [
                v3.FundingContributorV30(  # noqa: F405
                    contributor_orcid=v3.ContributorOrcidV30(
                        uri="https://" + url.hostname + "/" + fid.orcid,
                        path=fid.orcid,
                        host=url.hostname,
                    )
                    if fid.orcid
                    else None,
                    credit_name=v3.CreditNameV30(value=fid.name) if fid.name else None,
                    contributor_email=v3.ContributorEmailV30(value=fid.email)
                    if fid.email
                    else None,
                    contributor_attributes=v3.FundingContributorAttributesV30(
                        contributor_role=fid.role.replace("_", "-").lower()
                    )
                    if fid.role
                    else None,
                )
                for fid in FundingCont.select()
                .where(FundingCont.record_id == fr.id)
                .order_by(FundingCont.id)
            ]
        if external_ids:
            rec.external_ids = v3.ExternalIDsV30(external_id=external_ids)  # noqa: F405

        if contributors:
            rec.contributors = v3.FundingContributorsV30(contributor=contributors)  # noqa: F405

        if visibility:
            rec.visibility = visibility.replace("_", "-").lower()

        try:
            api_call = self.update_fundingv3 if put_code else self.create_fundingv3

            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            app.logger.info(
                f"For {self.user} the ORCID record was {'updated' if put_code else 'created'} from {self.org}"
            )
            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                    visibility = None
                except:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid
                visibility = (
                    json.loads(resp.data).get("visibility") if hasattr(resp, "data") else None
                )

        except (ApiException, v3.rest.ApiException) as ex:
            if ex.status == 404:
                fi.put_code = None
                fi.save()
                app.logger.exception(
                    f"For {self.user} encountered exception, So updating related put_code"
                )
            raise ex
        except:
            app.logger.exception(f"For {self.user} encountered exception")
        else:
            return (put_code, orcid, created, visibility)

    def create_or_update_individual_funding(
        self,
        funding_title=None,
        funding_translated_title=None,
        translated_title_language=None,
        funding_type=None,
        funding_subtype=None,
        funding_description=None,
        total_funding_amount=None,
        total_funding_amount_currency=None,
        org_name=None,
        city=None,
        region=None,
        country=None,
        start_date=None,
        end_date=None,
        disambiguated_id=None,
        disambiguation_source=None,
        grant_data_list=None,
        put_code=None,
        url=None,
        visibility=None,
        *args,
        **kwargs,
    ):
        """Create or update individual funding record via UI."""
        rec = v3.FundingV30()  # noqa: F405

        if funding_title:
            title = v3.TitleV30(value=funding_title)  # noqa: F405
            translated_title = None
            if funding_translated_title and translated_title_language:
                translated_title = v3.TranslatedTitleV30(
                    value=funding_translated_title, language_code=translated_title_language
                )  # noqa: F405
            rec.title = v3.FundingTitleV30(
                title=title, translated_title=translated_title
            )  # noqa: F405

        if funding_type:
            rec.type = funding_type.replace("_", "-").lower()

        if funding_subtype:
            rec.organization_defined_type = v3.OrganizationDefinedFundingSubTypeV30(
                value=funding_subtype
            )  # noqa: F405

        if funding_description:
            rec.short_description = funding_description

        if total_funding_amount and total_funding_amount_currency:
            rec.amount = v3.AmountV30(
                value=total_funding_amount, currency_code=total_funding_amount_currency
            )  # noqa: F405
        if url:
            rec.url = v3.UrlV30(value=url)

        organisation_address = v3.OrganizationAddressV30(
            city=city or self.org.city,
            country=country or self.org.country,
            region=region or self.org.region,
        )

        disambiguated_organization_details = v3.DisambiguatedOrganizationV30(
            disambiguated_organization_identifier=disambiguated_id or self.org.disambiguated_id,
            disambiguation_source=disambiguation_source or self.org.disambiguation_source,
        )

        rec.organization = v3.OrganizationV30(
            name=org_name or self.org.name,
            address=organisation_address,
            disambiguated_organization=disambiguated_organization_details,
        )

        if put_code:
            rec.put_code = put_code

        if start_date:
            rec.start_date = start_date.as_orcid_dict()
        if end_date:
            rec.end_date = end_date.as_orcid_dict()

        external_ids = []

        if grant_data_list:
            external_ids = [
                v3.ExternalIDV30(  # noqa: F405
                    external_id_type=gdl.get("grant_type")
                    if gdl.get("grant_type")
                    else "grant_number",
                    external_id_value=gdl.get("grant_number"),
                    external_id_url=v3.UrlV30(value=gdl.get("grant_url"))
                    if gdl.get("grant_url")
                    else None,
                    external_id_relationship=gdl.get("grant_relationship")
                    .replace("_", "-")
                    .lower()
                    if gdl.get("grant_relationship")
                    else "self",
                )
                for gdl in grant_data_list
            ]

        if external_ids:
            rec.external_ids = v3.ExternalIDsV30(external_id=external_ids)  # noqa: F405

        if visibility:
            rec.visibility = visibility.replace("_", "-").lower()

        try:
            api_call = self.update_fundingv3 if put_code else self.create_fundingv3

            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            app.logger.info(
                f"For {self.user} the ORCID record was {'updated' if put_code else 'created'} from {self.org}"
            )
            created = not bool(put_code)
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

        except (ApiException, v3.rest.ApiException) as apiex:
            if apiex.status == 404:
                app.logger.exception(
                    f"For {self.user} encountered exception, So updating related put_code"
                )
            raise apiex
        except Exception as ex:
            app.logger.exception(f"For {self.user} encountered exception")
            raise ex
        else:
            return (put_code, orcid, created)

    def create_or_update_individual_peer_review(
        self,
        org_name=None,
        disambiguated_id=None,
        disambiguation_source=None,
        city=None,
        region=None,
        country=None,
        reviewer_role=None,
        review_url=None,
        review_type=None,
        review_group_id=None,
        subject_external_identifier_type=None,
        subject_external_identifier_value=None,
        subject_external_identifier_url=None,
        subject_external_identifier_relationship=None,
        subject_container_name=None,
        subject_type=None,
        subject_title=None,
        subject_subtitle=None,
        subject_translated_title=None,
        subject_translated_title_language_code=None,
        subject_url=None,
        review_completion_date=None,
        grant_data_list=None,
        put_code=None,
        visibility=None,
        *args,
        **kwargs,
    ):
        """Create or update individual peer review record via UI."""
        rec = v3.PeerReviewV30()  # noqa: F405

        if reviewer_role:
            rec.reviewer_role = reviewer_role.replace("_", "-").lower()

        if review_url:
            rec.review_url = v3.UrlV30(value=review_url)  # noqa: F405

        if review_type:
            rec.review_type = review_type.replace("_", "-").lower()

        if review_completion_date.as_orcid_dict():
            rec.review_completion_date = review_completion_date.as_orcid_dict()

        if review_group_id:
            rec.review_group_id = review_group_id

        if subject_external_identifier_type and subject_external_identifier_value:
            subject_external_id_relationship = "self"
            if subject_external_identifier_relationship:
                subject_external_id_relationship = subject_external_identifier_relationship.replace(
                    "_", "-"
                ).lower()
            subject_external_id_url = None
            if subject_external_identifier_url:
                subject_external_id_url = v3.UrlV30(
                    value=subject_external_identifier_url
                )  # noqa: F405
            rec.subject_external_identifier = v3.ExternalIDV30(
                external_id_type=subject_external_identifier_type,
                external_id_value=subject_external_identifier_value,
                external_id_relationship=subject_external_id_relationship,
                external_id_url=subject_external_id_url,
            )  # noqa: F405

        if subject_container_name:
            rec.subject_container_name = v3.TitleV30(value=subject_container_name)  # noqa: F405

        if subject_type:
            rec.subject_type = subject_type.replace("_", "-").lower()

        if subject_title:
            title = v3.TitleV30(value=subject_title)  # noqa: F405
            subtitle = None
            if subject_subtitle:
                subtitle = v3.SubtitleV30(value=subject_subtitle)  # noqa: F405
            translated_title = None
            if subject_translated_title_language_code and subject_translated_title:
                translated_title = v3.TranslatedTitleV30(
                    value=subject_translated_title,  # noqa: F405
                    language_code=subject_translated_title_language_code,
                )
            rec.subject_name = v3.SubjectNameV30(
                title=title, subtitle=subtitle, translated_title=translated_title  # noqa: F405
            )

        if subject_url:
            rec.subject_url = v3.UrlV30(value=subject_url)  # noqa: F405

        organisation_address = v3.OrganizationAddressV30(
            city=city or self.org.city,
            country=country or self.org.country,
            region=region or self.org.region,
        )

        disambiguated_organization_details = v3.DisambiguatedOrganizationV30(
            disambiguated_organization_identifier=disambiguated_id or self.org.disambiguated_id,
            disambiguation_source=disambiguation_source or self.org.disambiguation_source,
        )

        rec.convening_organization = v3.OrganizationV30(
            name=org_name or self.org.name,
            address=organisation_address,
            disambiguated_organization=disambiguated_organization_details,
        )

        if put_code:
            rec.put_code = put_code

        external_ids = []

        if grant_data_list:
            external_ids = [
                v3.ExternalIDV30(  # noqa: F405
                    external_id_type=gdl.get("grant_type") if gdl.get("grant_type") else None,
                    external_id_value=gdl.get("grant_number"),
                    external_id_url=v3.UrlV30(value=gdl.get("grant_url"))
                    if gdl.get("grant_url")
                    else None,
                    external_id_relationship=gdl.get("grant_relationship")
                    .replace("_", "-")
                    .lower()
                    if gdl.get("grant_relationship")
                    else "self",
                )
                for gdl in grant_data_list
            ]

        if external_ids:
            rec.review_identifiers = v3.ExternalIDsV30(external_id=external_ids)  # noqa: F405

        if visibility:
            rec.visibility = visibility.replace("_", "-").lower()

        try:
            api_call = self.update_peer_reviewv3 if put_code else self.create_peer_reviewv3

            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            app.logger.info(
                f"For {self.user} the ORCID record was {'updated' if put_code else 'created'} from {self.org}"
            )
            created = not bool(put_code)
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

        except (ApiException, v3.rest.ApiException) as apiex:
            if apiex.status == 404:
                app.logger.exception(
                    f"For {self.user} encountered exception, So updating related put_code"
                )
            raise apiex
        except Exception as ex:
            app.logger.exception(f"For {self.user} encountered exception")
            raise ex
        else:
            return (put_code, orcid, created)

    def create_or_update_individual_work(
        self,
        work_type=None,
        title=None,
        subtitle=None,
        translated_title=None,
        translated_title_language_code=None,
        journal_title=None,
        short_description=None,
        citation_type=None,
        citation=None,
        publication_date=None,
        url=None,
        language_code=None,
        country=None,
        grant_data_list=None,
        put_code=None,
        visibility=None,
        *args,
        **kwargs,
    ):
        """Create or update individual work record via UI."""
        rec = v3.WorkV30()  # noqa: F405

        if put_code:
            rec.put_code = put_code

        if title:
            title = v3.TitleV30(value=title)  # noqa: F405
            subtitle = v3.SubtitleV30(value=subtitle) if subtitle else None  # noqa: F405
            translated_title = (
                v3.TranslatedTitleV30(
                    value=translated_title, language_code=translated_title_language_code
                )
                if translated_title and translated_title_language_code
                else None
            )
            rec.title = v3.WorkTitleV30(
                title=title, subtitle=subtitle, translated_title=translated_title
            )  # noqa: F405

        if journal_title:
            rec.journal_title = v3.TitleV30(value=journal_title)  # noqa: F405

        if short_description:
            rec.short_description = short_description

        if citation_type and citation:
            rec.citation = v3.Citation(
                citation_type=citation_type.replace("_", "-").lower(), citation_value=citation
            )  # noqa: F405

        if work_type:
            rec.type = work_type.replace("_", "-").lower()

        if publication_date.as_orcid_dict():
            rec.publication_date = publication_date.as_orcid_dict()

        external_ids = []

        if grant_data_list:
            external_ids = [
                v3.ExternalIDV30(  # noqa: F405
                    external_id_type=gdl.get("grant_type")
                    if gdl.get("grant_type")
                    else "grant_number",
                    external_id_value=gdl.get("grant_number"),
                    external_id_url=v3.UrlV30(value=gdl.get("grant_url"))
                    if gdl.get("grant_url")
                    else None,
                    external_id_relationship=gdl.get("grant_relationship")
                    .replace("_", "-")
                    .lower()
                    if gdl.get("grant_relationship")
                    else "self",
                )
                for gdl in grant_data_list
            ]

        if external_ids:
            rec.external_ids = v3.ExternalIDsV30(external_id=external_ids)  # noqa: F405

        if url:
            rec.url = v3.UrlV30(value=url)  # noqa: F405

        if language_code:
            rec.language_code = language_code

        if country:
            rec.country = v3.CountryV30(value=country)  # noqa: F405

        if put_code:
            rec.put_code = put_code

        if visibility:
            rec.visibility = visibility.replace("_", "-").lower()

        try:
            api_call = self.update_workv3 if put_code else self.create_workv3

            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            app.logger.info(
                f"For {self.user} the ORCID record was {'updated' if put_code else 'created'} from {self.org}"
            )
            created = not bool(put_code)
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

        except (ApiException, v3.rest.ApiException) as apiex:
            if apiex.status == 404:
                app.logger.exception(
                    f"For {self.user} encountered exception, So updating related put_code"
                )
            raise apiex
        except Exception as ex:
            app.logger.exception(f"For {self.user} encountered exception")
            raise ex
        else:
            return (put_code, orcid, created)

    def create_or_update_affiliation(
        self,
        affiliation=None,
        role=None,
        course_or_role=None,
        department=None,
        org_name=None,
        # NB! affiliation_record has 'organisation' field for organisation name
        organisation=None,
        city=None,
        region=None,
        country=None,
        disambiguated_id=None,
        disambiguation_source=None,
        start_date=None,
        end_date=None,
        put_code=None,
        initial=False,
        visibility=None,
        url=None,
        display_index=None,
        id=None,
        grant_data_list=None,
        *args,
        **kwargs,
    ):
        """Create or update affiliation record of a user.

        :param initial: the affiliation entry created while handlind ORCID authorizastion call back.

        Returns tuple (put-code, ORCID iD, created), where created is True if a new entry
        was created, otherwise - False.
        """
        if not department:
            department = None
        if not role:
            role = None
        if not region:
            region = None
        if not self.org.region:
            self.org.region = None

        if affiliation is None:
            app.logger.warning("Missing affiliation value.")
            raise Exception("Missing affiliation value.")

        if initial:
            put_code = self.is_emp_or_edu_record_present(affiliation)
            if put_code:
                return put_code, self.user.orcid, False

        organisation_address = v3.OrganizationAddressV30(
            city=city or self.org.city,
            country=country or self.org.country,
            region=region or self.org.region,
        )

        if disambiguation_source:
            disambiguation_source = disambiguation_source.upper()
        elif self.org.disambiguation_source:
            disambiguation_source = self.org.disambiguation_source.upper()

        disambiguated_organization_details = (
            v3.DisambiguatedOrganizationV30(
                disambiguated_organization_identifier=disambiguated_id
                or self.org.disambiguated_id,
                disambiguation_source=disambiguation_source,
            )
            if disambiguation_source
            else None
        )

        rec = {
            Affiliation.DST: v3.DistinctionV30,
            Affiliation.EDU: v3.EducationV30,
            Affiliation.EMP: v3.EmploymentV30,
            Affiliation.MEM: v3.MembershipV30,
            Affiliation.POS: v3.InvitedPositionV30,
            Affiliation.QUA: v3.QualificationV30,
            Affiliation.SER: v3.ServiceV30,
        }.get(affiliation)()
        if not rec:
            app.logger.info(
                f"For {self.user} not able to determine affiliaton type with {self.org}"
            )
            raise Exception(
                f"Unsupported affiliation type '{affiliation}' for {self.user} affiliaton type with {self.org}"
            )
        rec.organization = v3.OrganizationV30(
            name=organisation or org_name or self.org.name,
            address=organisation_address,
            disambiguated_organization=disambiguated_organization_details,
        )

        if put_code:
            rec.put_code = put_code

        if visibility:
            rec.visibility = visibility.lower()

        if display_index:
            rec.display_index = display_index

        if url:
            rec.url = v3.UrlV30(value=url)  # noqa: F405

        rec.department_name = department
        rec.role_title = role or course_or_role

        if start_date and not start_date.is_null:
            rec.start_date = start_date.as_orcid_dict()
        if end_date and not end_date.is_null:
            rec.end_date = end_date.as_orcid_dict()

        external_ids = []
        if id:
            external_ids = [
                v3.ExternalIDV30(  # noqa: F405
                    external_id_type=eid.type,
                    external_id_value=eid.value,
                    external_id_url=v3.UrlV30(value=eid.url) if eid.url else None,
                    external_id_relationship=eid.relationship.replace("_", "-").lower()
                    if eid.relationship
                    else "self",
                )
                for eid in AffiliationExternalId.select()
                .where(AffiliationExternalId.record_id == id)
                .order_by(AffiliationExternalId.id)
            ]
        elif grant_data_list:
            external_ids = [
                v3.ExternalIDV30(  # noqa: F405
                    external_id_type=gdl.get("grant_type")
                    if gdl.get("grant_type")
                    else "grant_number",
                    external_id_value=gdl.get("grant_number"),
                    external_id_url=v3.UrlV30(value=gdl.get("grant_url"))
                    if gdl.get("grant_url")
                    else None,
                    external_id_relationship=gdl.get("grant_relationship")
                    .replace("_", "-")
                    .lower()
                    if gdl.get("grant_relationship")
                    else "self",
                )
                for gdl in grant_data_list
            ]
        if external_ids:
            rec.external_ids = v3.ExternalIDsV30(external_id=external_ids)  # noqa: F405

        try:
            if affiliation == Affiliation.EMP:
                api_call = self.update_employmentv3 if put_code else self.create_employmentv3
            elif affiliation == Affiliation.DST:
                api_call = self.update_distinctionv3 if put_code else self.create_distinctionv3
            elif affiliation == Affiliation.MEM:
                api_call = self.update_membershipv3 if put_code else self.create_membershipv3
            elif affiliation == Affiliation.SER:
                api_call = self.update_servicev3 if put_code else self.create_servicev3
            elif affiliation == Affiliation.QUA:
                api_call = self.update_qualificationv3 if put_code else self.create_qualificationv3
            elif affiliation == Affiliation.POS:
                api_call = (
                    self.update_invited_positionv3 if put_code else self.create_invited_positionv3
                )
            else:
                api_call = self.update_educationv3 if put_code else self.create_educationv3
            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            app.logger.info(
                f"For {self.user} the ORCID record was {'updated' if put_code else 'created'} from {self.org}"
            )
            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                    visibility = None
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid
                visibility = (
                    json.loads(resp.data).get("visibility") if hasattr(resp, "data") else None
                )

        except (ApiException, v3.rest.ApiException) as apiex:
            app.logger.exception(f"For {self.user} encountered exception: {apiex}")
            raise apiex
        except Exception as ex:
            app.logger.exception(f"For {self.user} encountered exception")
            raise ex
        else:
            return (put_code, orcid, created, visibility)

    def create_or_update_researcher_url(
        self,
        name=None,
        value=None,
        display_index=None,
        orcid=None,
        put_code=None,
        visibility=None,
        *args,
        **kwargs,
    ):
        """Create or update researcher url record of a user."""
        rec = v3.ResearcherUrlV30()  # noqa: F405

        if name:
            rec.url_name = name
        if value:
            rec.url = v3.UrlV30(value=value)  # noqa: F405
        if visibility:
            rec.visibility = visibility.replace("_", "-").lower()
        if put_code:
            rec.put_code = put_code
        if display_index:
            rec.display_index = display_index

        try:
            api_call = self.edit_researcher_urlv3 if put_code else self.create_researcher_urlv3
            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                    visibility = None
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid
                visibility = (
                    json.loads(resp.data).get("visibility") if hasattr(resp, "data") else None
                )

        except (ApiException, v3.rest.ApiException) as apiex:
            app.logger.exception(f"For {self.user} encountered exception: {apiex}")
            raise apiex
        except Exception as ex:
            app.logger.exception(f"For {self.user} encountered exception")
            raise ex
        else:
            return (put_code, orcid, created, visibility)

    def create_or_update_other_name(
        self,
        content=None,
        value=None,
        display_index=None,
        orcid=None,
        put_code=None,
        visibility=None,
        *args,
        **kwargs,
    ):
        """Create or update other name record of a user."""
        rec = v3.OtherNameV30()  # noqa: F405

        if put_code:
            rec.put_code = put_code
        content = content or value
        if content:
            rec.content = content
        if visibility:
            rec.visibility = visibility.replace("_", "-").lower()
        if display_index:
            rec.display_index = display_index

        try:
            api_call = self.edit_other_namev3 if put_code else self.create_other_namev3
            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                    visibility = None
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid
                visibility = (
                    json.loads(resp.data).get("visibility") if hasattr(resp, "data") else None
                )

        except (ApiException, v3.rest.ApiException) as apiex:
            app.logger.exception(f"For {self.user} encountered exception: {apiex}")
            raise apiex
        except Exception as ex:
            app.logger.exception(f"For {self.user} encountered exception")
            raise ex
        else:
            return (put_code, orcid, created, visibility)

    def create_or_update_address(
        self,
        country=None,
        value=None,
        display_index=None,
        orcid=None,
        put_code=None,
        visibility=None,
        *args,
        **kwargs,
    ):
        """Create or update address record of an user."""
        rec = v3.AddressV30()  # noqa: F405

        if put_code:
            rec.put_code = put_code
        country = country or value
        if country:
            rec.country = v3.CountryV30(value=country)  # noqa: F405
        if visibility:
            rec.visibility = visibility.replace("_", "-").lower()
        if display_index:
            rec.display_index = display_index

        try:
            api_call = self.edit_addressv3 if put_code else self.create_addressv3
            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                    visibility = None
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid
                visibility = (
                    json.loads(resp.data).get("visibility") if hasattr(resp, "data") else None
                )

        except (ApiException, v3.rest.ApiException) as apiex:
            app.logger.exception(f"For {self.user} encountered exception: {apiex}")
            raise apiex
        except Exception as ex:
            app.logger.exception(f"For {self.user} encountered exception")
            raise ex
        else:
            return (put_code, orcid, created, visibility)

    def create_or_update_person_external_id(
        self,
        type=None,
        value=None,
        url=None,
        relationship=None,
        display_index=None,
        orcid=None,
        put_code=None,
        visibility=None,
        *args,
        **kwargs,
    ):
        """Create or update person external identifier record of an user."""
        rec = v3.PersonExternalIdentifierV30()  # noqa: F405

        if put_code:
            rec.put_code = put_code
        if type:
            rec.external_id_type = type.lower()
        if value:
            rec.external_id_value = value
        if url:
            rec.external_id_url = v3.UrlV30(value=url)  # noqa: F405
        if relationship:
            rec.external_id_relationship = relationship.replace("_", "-").lower()
        if visibility:
            rec.visibility = visibility.replace("_", "-").lower()
        if display_index:
            rec.display_index = display_index

        try:
            api_call = (
                self.edit_external_identifierv3 if put_code else self.create_external_identifierv3
            )
            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                    visibility = None
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid
                visibility = (
                    json.loads(resp.data).get("visibility") if hasattr(resp, "data") else None
                )

        except (ApiException, v3.rest.ApiException) as apiex:
            app.logger.exception(f"For {self.user} encountered exception: {apiex}")
            raise apiex
        except Exception as ex:
            app.logger.exception(f"For {self.user} encountered exception")
            raise ex
        else:
            return (put_code, orcid, created, visibility)

    def create_or_update_keyword(
        self,
        content=None,
        value=None,
        display_index=None,
        orcid=None,
        put_code=None,
        visibility=None,
        *args,
        **kwargs,
    ):
        """Create or update Keyword record of a user."""
        rec = v3.KeywordV30()  # noqa: F405

        if put_code:
            rec.put_code = put_code

        content = content or value
        if content:
            rec.content = content
        if visibility:
            rec.visibility = visibility.replace("_", "-").lower()
        if display_index:
            rec.display_index = display_index

        try:
            api_call = self.edit_keywordv3 if put_code else self.create_keywordv3
            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                    visibility = None
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid
                visibility = (
                    json.loads(resp.data).get("visibility") if hasattr(resp, "data") else None
                )

        except (ApiException, v3.rest.ApiException) as apiex:
            app.logger.exception(f"For {self.user} encountered exception: {apiex}")
            raise apiex
        except Exception as ex:
            app.logger.exception(f"For {self.user} encountered exception")
            raise ex
        else:
            return (put_code, orcid, created, visibility)

    def get_webhook_access_token(self):
        """Retrieve the ORCID webhook access tonke and store it."""
        pass

    def register_webhook(self, user=None, orcid=None):
        """Register a webhook for the given ORCID ID or user."""
        pass

    def sync_profile(self, task, user, access_token):
        """Synchronize the user profile."""
        self.set_config(user=user, org=self.org, access_token=access_token)
        profile = self.get_record()

        if not profile:
            Log.create(task=task, message=f"The user {user} doesn't have ORCID profile.")
            return

        for k, s in [["educations", "education-summary"], ["employments", "employment-summary"]]:
            for e in (
                ss.get(s)
                for ag in profile.get("activities-summary", k, "affiliation-group", default=[])
                for ss in ag.get("summaries", default=[])
            ):
                source = e.get("source")
                if not source:
                    continue

                if source.get("source-client-id", "path") == self.org.orcid_client_id:
                    do = e.get("organization", "disambiguated-organization")
                    if not (
                        do
                        and do.get("disambiguated-organization-identifier")
                        and do.get("disambiguation-source")
                    ):
                        e["organization"]["disambiguated-organization"] = {
                            "disambiguated-organization-identifier": self.org.disambiguated_id,
                            "disambiguation-source": self.org.disambiguation_source,
                        }
                        api_call = (
                            self.update_employmentv3
                            if k == "employments"
                            else self.update_educationv3
                        )

                        try:
                            api_call(orcid=user.orcid, put_code=e.get("put-code"), body=e)
                            Log.create(task=task, message=f"Successfully update entry: {e}.")
                        except Exception as ex:
                            Log.create(task=task, message=f"Failed to update the entry: {ex}.")

    def get_keywords(self):
        """Retrieve all the keywords of a record."""
        resp, status, _ = self.api_client.call_api(
            f"/{self.version}/{self.user.orcid}/keywords",
            "GET",
            header_params={"Accept": self.content_type},
            auth_settings=["orcid_auth"],
            _preload_content=False,
        )
        return json.loads(resp.data) if status == 200 else None

    def get_section(self, section_type):
        """Retrieve researcher profile section by the section type."""
        method_name = {
            "MEM": "view_membershipsv3",
            "SER": "view_servicesv3",
            "QUA": "view_qualificationsv3",
            "POS": "view_invited_positionsv3",
            "ADR": "view_addressesv3",
            "DST": "view_distinctionsv3",
            "EDU": "view_educationsv3",
            "EMP": "view_employmentsv3",
            "EXR": "view_external_identifiersv3",
            "FUN": "view_fundingsv3",
            "KWR": "view_keywordsv3",
            "ONR": "view_other_namesv3",
            "PRR": "view_peer_reviewsv3",
            "RUR": "view_researcher_urlsv3",
            "WOR": "view_worksv3",
        }[section_type]
        return getattr(self, method_name)(self.user.orcid, _preload_content=False)

    def delete_section(self, section_type, put_code):
        """Delete a section from the researcher profile."""
        method_name = {
            "MEM": "delete_membershipv3",
            "SER": "delete_servicev3",
            "QUA": "delete_qualificationv3",
            "POS": "delete_invited_positionv3",
            "DST": "delete_distinctionv3",
            "ADR": "delete_addressv3",
            "EDU": "delete_educationv3",
            "EMP": "delete_employmentv3",
            "EXR": "delete_external_identifierv3",
            "FUN": "delete_fundingv3",
            "KWR": "delete_keywordv3",
            "ONR": "delete_other_namev3",
            "PRR": "delete_peer_reviewv3",
            "RUR": "delete_researcher_urlv3",
            "WOR": "delete_workv3",
        }[section_type]
        return getattr(self, method_name)(self.user.orcid, put_code)

    def get(self, path=None):
        """Execute 'GET' request."""
        return self.execute("GET", path)

    def post(self, path, body=None):
        """Execute 'GET' request."""
        return self.execute("POST", path, body)

    def put(self, path, body=None):
        """Execute 'PUT' request."""
        return self.execute("PUT", path, body)

    def delete(self, path):
        """Execute 'DELETE' request."""
        return self.execute("DELETE", path)

    def execute(self, method, path, body=None):
        """Execute the given request."""
        headers = {"Accept": self.content_type}
        if method != "GET":
            headers["Content-Type"] = self.content_type
        try:
            if path and path.startswith("http"):
                url = urlparse(path).path
            else:
                url = f"/{self.version}/{self.user.orcid}"
                if path:
                    url += "/" + path
            resp, *_ = self.api_client.call_api(
                url,
                method,
                header_params=headers,
                response_type=self.content_type,
                auth_settings=["orcid_auth"],
                body=body,
                _preload_content=False,
            )
        except (ApiException, v3.rest.ApiException) as ex:
            if ex.status == 401:
                orcid_token = self.get_token()
                if orcid_token:
                    orcid_token.delete_instance()
                else:
                    app.logger.exception("Exception occurred while retrieving ORCID Token")
            else:
                app.logger.error(f"ApiException Occurred: {ex}")
            raise

        if resp.data:
            resp.json = json.loads(resp.data.decode(), object_pairs_hook=NestedDict)
        return resp


class MemberAPI(MemberAPIMixin, MemberAPIV20Api):
    """ORCID Mmeber API extension."""

    pass


class MemberAPIV3(MemberAPIMixin, v3.api.DevelopmentMemberAPIV30Api):
    """ORCID Mmeber API V3 extension."""

    def __init__(self, org=None, user=None, access_token=None, *args, **kwargs):
        """Overwrite the default host."""
        super().__init__(
            org=org, user=user, access_token=access_token, version="v3.0", *args, **kwargs
        )
        self.api_client.configuration.host = host

    def new_organisation(
        self,
        name=None,
        city=None,
        country=None,
        region=None,
        disambiguated_id=None,
        disambiguation_source=None,
    ):
        """Create an organisation object."""
        return v3.OrganizationV30(
            name=name,
            address=v3.OrganizationAddressV30(city=city, country=country, region=region)
            if (city or country or region)
            else None,
            disambiguated_organization=v3.DisambiguatedOrganizationV30(
                disambiguated_organization_identifier=disambiguated_id,
                disambiguation_source=disambiguation_source,
            )
            if disambiguated_id
            else None,
        )

    def new_hosts(self, hosts=None):
        """Create a resource hosts object."""
        return (
            v3.ResearchResourceHostsV30(organization=[self.new_organisation(**h) for h in hosts])
            if hosts
            else None
        )

    def new_resoucre_item(self, name=None, type=None, hosts=None, external_ids=None, url=None):
        """Create a resource item object."""
        return v3.ResearchResourceItemV30(
            resource_name=name,
            resource_type=type,
            hosts=self.new_hosts(hosts),
            external_ids=self.new_exeternal_ids(external_ids),
            url=url,
        )

    def new_exeternal_ids(self, external_ids):
        """Create an external ids object."""
        return (
            v3.ExternalIDsV30(
                external_id=[
                    v3.ExternalIDV30(
                        external_id_type=eid.get("type"),
                        external_id_value=eid.get("value"),
                        external_id_url=eid.get("url"),
                        external_id_relationship=eid.get("relationship"),
                    )
                    for eid in external_ids
                    if (eid.get("value") and eid.get("type"))
                ]
            )
            if external_ids
            else None
        )

    def create_or_update_resource(
        self,
        put_code=None,
        # Proposal:
        title=None,
        translated_title=None,
        translated_title_language=None,
        hosts=None,
        external_ids=None,
        start_date=None,
        end_date=None,
        url=None,
        # Resource items:
        items=None,
        display_index=None,
        visibility=None,
        *args,
        **kwargs,
    ):
        """Create or update research resource."""
        rec = v3.ResearchResourceV30(
            source=self.source,
            visibility=visibility,
            put_code=put_code,
            display_index=display_index,
        )

        rec.proposal = v3.ResearchResourceProposalV30(
            title=v3.ResearchResourceTitleV30(
                title=v3.TitleV30(value=title),
                translated_title=v3.TranslatedTitleV30(
                    value=translated_title, language_code=translated_title_language
                )
                if translated_title
                else None,
            ),
            hosts=v3.ResearchResourceHostsV30(
                organization=[self.new_organisation(**h) for h in hosts]
            )
            if hosts
            else None,
            external_ids=self.new_exeternal_ids(external_ids),
            start_date=start_date,
            end_date=end_date,
            url=url,
        )

        rec.resource_item = [self.new_resoucre_item(**ri) for ri in items] if items else None

        try:
            api_call = (
                self.update_research_resourcev3 if put_code else self.create_research_resourcev3
            )
            params = dict(orcid=self.user.orcid, body=rec, _preload_content=False)
            if put_code:
                params["put_code"] = put_code
            resp = api_call(**params)
            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                    visibility = None
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid
                visibility = (
                    json.loads(resp.data).get("visibility") if hasattr(resp, "data") else None
                )

        except (ApiException, v3.rest.ApiException) as apiex:
            app.logger.exception(f"For {self.user} encountered exception: {apiex}")
            raise apiex
        except Exception as ex:
            app.logger.exception(f"For {self.user} encountered exception")
            raise ex
        else:
            return (put_code, orcid, created, visibility)


# yapf: disable
from orcid_api import *  # noqa: F401,E402,F403,F405

api_client.RESTClientObject = OrcidRESTClientObject  # noqa: F405
v3.rest.RESTClientObject = OrcidRESTClientObjectV3  # noqa: F405
