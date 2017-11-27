# -*- coding: utf-8 -*-
"""
Swagger generated client 'monkey-patch' for logging API requests.

isort:skip_file
"""

from .config import ORCID_API_BASE, SCOPE_READ_LIMITED, SCOPE_ACTIVITIES_UPDATE, ORCID_BASE_URL
from flask_login import current_user
from .models import (OrcidApiCall, Affiliation, OrcidToken, FundingContributor as FundingCont, User
                     as UserModel, ExternalId as ExternalIdModel)
from orcid_api import (configuration, rest, api_client, MemberAPIV20Api, SourceClientId,
                            Source, OrganizationAddress, DisambiguatedOrganization, Employment,
                            Education, Organization)
from orcid_api.rest import ApiException
from time import time
from urllib.parse import urlparse
from . import app
import json

url = urlparse(ORCID_API_BASE)
configuration.host = url.scheme + "://" + url.hostname


class OrcidRESTClientObject(rest.RESTClientObject):
    """REST Client with call logging."""

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
                put_code=put_code)
        except Exception:
            app.logger.exception("Failed to create API call log entry.")
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

    def __init__(self, org=None, user=None, access_token=None, *args, **kwargs):
        """Set up the configuration with the access token given to the org. by the user."""
        super().__init__(*args, **kwargs)
        self.set_config(org, user)

    def set_config(self, org=None, user=None, access_token=None):
        """Set up clietn configuration."""
        global configuration
        if org is None:
            org = user.organisation
        self.org = org
        self.user = user
        if access_token is None:
            try:
                orcid_token = OrcidToken.get(
                    user_id=user.id,
                    org_id=org.id,
                    scope=SCOPE_READ_LIMITED[0] + "," + SCOPE_ACTIVITIES_UPDATE[0])
            except Exception as ex:
                app.logger.exception("Exception occured while retriving ORCID Token")
                return None

            configuration.access_token = orcid_token.access_token
        else:
            configuration.access_token = access_token

        url = urlparse(ORCID_BASE_URL)
        self.source_clientid = SourceClientId(
            host=url.hostname,
            path=org.orcid_client_id,
            uri="http://" + url.hostname + "/client/" + org.orcid_client_id)

        self.source = Source(
            source_orcid=None, source_client_id=self.source_clientid, source_name=org.name)

    def get_record(self):
        """Fetch record details. (The generated one is broken)."""
        header_params = {
            "Accept":
            self.api_client.select_header_content_type([
                'application/vnd.orcid+xml; qs=5', 'application/orcid+xml; qs=3',
                'application/xml', 'application/vnd.orcid+json; qs=4',
                'application/orcid+json; qs=2', 'application/json'
            ])
        }
        try:
            resp, code, headers = self.api_client.call_api(
                f"/v2.0/{self.user.orcid}",
                "GET",
                header_params=header_params,
                response_type=None,
                auth_settings=["orcid_auth"],
                _preload_content=False)
        except ApiException as ex:
            if ex.status == 401:
                try:
                    orcid_token = OrcidToken.get(
                        user_id=self.user.id,
                        org_id=self.org.id,
                        scope=SCOPE_READ_LIMITED[0] + "," + SCOPE_ACTIVITIES_UPDATE[0])
                    orcid_token.delete_instance()
                except Exception as ex:
                    app.logger.exception("Exception occured while retriving ORCID Token")
                    return None
            app.logger.error(f"ApiException Occured: {ex}")
            return None

        if code != 200:
            app.logger.error(f"Failed to retrieve ORDIC profile. Code: {code}.")
            app.logger.info(f"Headers: {headers}")
            app.logger.info(f"Body: {resp.data.decode()}")
            return None

        return json.loads(resp.data.decode())

    def is_emp_or_edu_record_present(self, affiliation_type):
        """Determine if there is already an affiliation record for the user.

        Returns:
            Either False or put-code, if there is an affiliation record.

        """
        try:
            if affiliation_type == Affiliation.EMP:
                resp = self.view_employments(self.user.orcid, _preload_content=False)
            else:
                resp = self.view_educations(self.user.orcid, _preload_content=False)

            if resp:
                data = json.loads(resp.data)
                records = data.get("employment-summary"
                                   if affiliation_type == Affiliation.EMP else "education-summary")
                for r in records:
                    if ("source-client-id" in r["source"] and
                            self.org.orcid_client_id == r["source"]["source-client-id"]["path"]):
                        app.logger.info(f"For {self.user} there is {affiliation_type!s} "
                                        "present on ORCID profile.")
                        return r["put-code"]

        except ApiException as apiex:
            app.logger.error(
                f"For {self.user} while checking for employment and education records, Encountered Exception: {apiex}"
            )
            return False
        except Exception:
            app.logger.exception("Failed to verify presence of employment or education record.")
            return False
        return False

    def create_or_update_funding(self, task_by_user, *args, **kwargs):
        """Create or update funding record of a user."""
        fr = task_by_user.funding_record
        fc = task_by_user.funding_record.funding_contributor

        if not fr.title:
            title = None

        city = fr.city
        country = fr.country
        region = fr.region
        disambiguated_id = fr.disambiguated_org_identifier
        disambiguation_source = fr.disambiguation_source
        org_name = fr.org_name
        funding_type = fr.type

        put_code = fc.put_code

        if not city:
            city = None
        if not region:
            region = None
        if not self.org.state:
            self.org.state = None

        organisation_address = OrganizationAddress(
            city=city or self.org.city,
            country=country or self.org.country,
            region=region or self.org.state)

        disambiguated_organization_details = DisambiguatedOrganization(
            disambiguated_organization_identifier=disambiguated_id or self.org.disambiguated_id,
            disambiguation_source=disambiguation_source or self.org.disambiguation_source)
        rec = Funding()  # noqa: F405

        rec.organization = Organization(
            name=org_name or self.org.name,
            address=organisation_address,
            disambiguated_organization=disambiguated_organization_details)

        organization_defined_type = fr.organization_defined_type
        title = Title(value=fr.title)  # noqa: F405
        translated_title = None
        if fr.translated_title:
            translated_title = TranslatedTitle(value=fr.translated_title)  # noqa: F405
        short_description = fr.short_description
        amount = fr.amount
        currency_code = fr.currency
        start_date = fr.start_date
        end_date = fr.end_date

        rec.source = self.source
        rec.type = funding_type
        rec.organization_defined_type = organization_defined_type
        rec.title = FundingTitle(title=title, translated_title=translated_title)  # noqa: F405
        rec.short_description = short_description
        rec.amount = Amount(value=amount, currency_code=currency_code)  # noqa: F405

        if put_code:
            rec.put_code = put_code

        if start_date:
            rec.start_date = start_date.as_orcid_dict()
        if end_date:
            rec.end_date = end_date.as_orcid_dict()
        funding_contributors = FundingCont.select().where(FundingCont.funding_record_id == fr.id)

        funding_contributor_list = []
        for f in funding_contributors:
            contributor_from_user_table = UserModel.get(UserModel.email == f.email)
            path = None
            uri = None
            host = None
            credit_name = None
            contributor_orcid = None
            if f.name:
                credit_name = CreditName(value=f.name)  # noqa: F405
            elif contributor_from_user_table and contributor_from_user_table.name:
                credit_name = CreditName(value=contributor_from_user_table.name)  # noqa: F405

            if contributor_from_user_table and contributor_from_user_table.orcid:
                path = contributor_from_user_table.orcid
            elif f.orcid:
                path = f.orcid

            if path:
                url = urlparse(ORCID_BASE_URL)
                uri = "http://" + url.hostname + "/" + path
                host = url.hostname
                contributor_orcid = ContributorOrcid(uri=uri, path=path, host=host)  # noqa: F405
            # As Contributor email is by default private so, we are not sending it in funding payload
            # contributor_email = ContributorEmail(value=f.email)  # noqa: F405
            contributor_attributes = FundingContributorAttributes(  # noqa: F405
                contributor_role=f.role.upper())

            funding_contributor_list.append(
                FundingContributor(  # noqa: F405
                    contributor_orcid=contributor_orcid,
                    credit_name=credit_name,
                    contributor_attributes=contributor_attributes))

        rec.contributors = FundingContributors(contributor=funding_contributor_list)  # noqa: F405
        external_id_list = []

        external_ids = ExternalIdModel.select().where(ExternalIdModel.funding_record_id == fr.id)

        for exi in external_ids:
            # Orcid is expecting external type as 'grant_number'
            external_id_type = exi.type if exi.type else "grant_number"
            external_id_value = exi.value
            external_id_url = None
            if exi.url:
                external_id_url = Url(value=exi.url)  # noqa: F405
            # Setting the external id relationship as 'SELF' by default, it can be either SELF/PART_OF
            external_id_relationship = exi.relationship.upper() if exi.relationship else "SELF"
            external_id_list.append(
                ExternalID(  # noqa: F405
                    external_id_type=external_id_type,
                    external_id_value=external_id_value,
                    external_id_url=external_id_url,
                    external_id_relationship=external_id_relationship))

        rec.external_ids = ExternalIDs(external_id=external_id_list)  # noqa: F405

        try:
            api_call = self.update_funding if put_code else self.create_funding

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
                    fc.put_code = put_code
                    fc.save()
                except:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid

        except ApiException as ex:
            if ex.status == 404:
                fc.put_code = None
                fc.save()
                app.logger.exception(
                    f"For {self.user} encountered exception, So updating related put_code")
            raise ex
        except:
            app.logger.exception(f"For {self.user} encountered exception")
        else:
            return (put_code, orcid, created)

    def create_or_update_affiliation(
            self,
            affiliation=None,
            role=None,
            department=None,
            org_name=None,
            # NB! affiliation_record has 'organisation' field for organisation name
            organisation=None,
            city=None,
            state=None,
            region=None,
            country=None,
            disambiguated_id=None,
            disambiguation_source=None,
            start_date=None,
            end_date=None,
            put_code=None,
            initial=False,
            *args,
            **kwargs):
        """Create or update affiliation record of a user.

        :param initial: the affiliation entry created while handlind ORCID authorizastion call back.

        Returns tuple (put-code, ORCID iD, created), where created is True if a new entry
        was created, otherwise - False.
        """
        if not department:
            department = None
        if not role:
            role = None
        if not state:
            state = None
        if not region:
            region = None
        if not self.org.state:
            self.org.state = None

        if affiliation is None:
            app.logger.warning("Missing affiliation value.")
            raise Exception("Missing affiliation value.")

        if initial:
            put_code = self.is_emp_or_edu_record_present(affiliation)
            if put_code:
                return put_code, self.user.orcid, False

        organisation_address = OrganizationAddress(
            city=city or self.org.city,
            country=country or self.org.country,
            region=state or region or self.org.state)

        disambiguated_organization_details = DisambiguatedOrganization(
            disambiguated_organization_identifier=disambiguated_id or self.org.disambiguated_id,
            disambiguation_source=disambiguation_source or self.org.disambiguation_source)

        if affiliation == Affiliation.EMP:
            rec = Employment()
        elif affiliation == Affiliation.EDU:
            rec = Education()
        else:
            app.logger.info(
                f"For {self.user} not able to determine affiliaton type with {self.org}")
            raise Exception(
                f"Unsupported affiliation type '{affiliation}' for {self.user} affiliaton type with {self.org}"
            )

        rec.source = self.source
        rec.organization = Organization(
            name=organisation or org_name or self.org.name,
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
            if affiliation == Affiliation.EMP:
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
            created = not bool(put_code)
            # retrieve the put-code from response Location header:
            if resp.status == 201:
                location = resp.headers.get("Location")
                try:
                    orcid, put_code = location.split("/")[-3::2]
                    put_code = int(put_code)
                except Exception:
                    app.logger.exception("Failed to get ORCID iD/put-code from the response.")
                    raise Exception("Failed to get ORCID iD/put-code from the response.")
            elif resp.status == 200:
                orcid = self.user.orcid

        except Exception:
            app.logger.exception(f"For {self.user} encountered exception")
        else:
            return (put_code, orcid, created)


# yapf: disable
from orcid_api import *  # noqa: F401,F403,F405

api_client.RESTClientObject = OrcidRESTClientObject  # noqa: F405
