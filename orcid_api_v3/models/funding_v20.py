# coding: utf-8

"""
    ORCID Member

    No description provided (generated by Swagger Codegen https://github.com/swagger-api/swagger-codegen)  # noqa: E501

    OpenAPI spec version: Latest
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

import pprint
import re  # noqa: F401

import six
from orcid_api_v3.models.amount_v20 import AmountV20  # noqa: F401,E501
from orcid_api_v3.models.created_date_v20 import CreatedDateV20  # noqa: F401,E501
from orcid_api_v3.models.external_i_ds_v20 import ExternalIDsV20  # noqa: F401,E501
from orcid_api_v3.models.funding_contributors_v20 import FundingContributorsV20  # noqa: F401,E501
from orcid_api_v3.models.funding_title_v20 import FundingTitleV20  # noqa: F401,E501
from orcid_api_v3.models.fuzzy_date_v20 import FuzzyDateV20  # noqa: F401,E501
from orcid_api_v3.models.last_modified_date_v20 import LastModifiedDateV20  # noqa: F401,E501
from orcid_api_v3.models.organization_defined_funding_sub_type_v20 import OrganizationDefinedFundingSubTypeV20  # noqa: F401,E501
from orcid_api_v3.models.organization_v20 import OrganizationV20  # noqa: F401,E501
from orcid_api_v3.models.source_v20 import SourceV20  # noqa: F401,E501
from orcid_api_v3.models.url_v20 import UrlV20  # noqa: F401,E501


class FundingV20(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """
    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        'created_date': 'CreatedDateV20',
        'last_modified_date': 'LastModifiedDateV20',
        'source': 'SourceV20',
        'put_code': 'int',
        'path': 'str',
        'type': 'str',
        'organization_defined_type': 'OrganizationDefinedFundingSubTypeV20',
        'title': 'FundingTitleV20',
        'short_description': 'str',
        'amount': 'AmountV20',
        'url': 'UrlV20',
        'start_date': 'FuzzyDateV20',
        'end_date': 'FuzzyDateV20',
        'external_ids': 'ExternalIDsV20',
        'contributors': 'FundingContributorsV20',
        'organization': 'OrganizationV20',
        'visibility': 'str'
    }

    attribute_map = {
        'created_date': 'created-date',
        'last_modified_date': 'last-modified-date',
        'source': 'source',
        'put_code': 'put-code',
        'path': 'path',
        'type': 'type',
        'organization_defined_type': 'organization-defined-type',
        'title': 'title',
        'short_description': 'short-description',
        'amount': 'amount',
        'url': 'url',
        'start_date': 'start-date',
        'end_date': 'end-date',
        'external_ids': 'external-ids',
        'contributors': 'contributors',
        'organization': 'organization',
        'visibility': 'visibility'
    }

    def __init__(self, created_date=None, last_modified_date=None, source=None, put_code=None, path=None, type=None, organization_defined_type=None, title=None, short_description=None, amount=None, url=None, start_date=None, end_date=None, external_ids=None, contributors=None, organization=None, visibility=None):  # noqa: E501
        """FundingV20 - a model defined in Swagger"""  # noqa: E501
        self._created_date = None
        self._last_modified_date = None
        self._source = None
        self._put_code = None
        self._path = None
        self._type = None
        self._organization_defined_type = None
        self._title = None
        self._short_description = None
        self._amount = None
        self._url = None
        self._start_date = None
        self._end_date = None
        self._external_ids = None
        self._contributors = None
        self._organization = None
        self._visibility = None
        self.discriminator = None
        if created_date is not None:
            self.created_date = created_date
        if last_modified_date is not None:
            self.last_modified_date = last_modified_date
        if source is not None:
            self.source = source
        if put_code is not None:
            self.put_code = put_code
        if path is not None:
            self.path = path
        self.type = type
        if organization_defined_type is not None:
            self.organization_defined_type = organization_defined_type
        self.title = title
        if short_description is not None:
            self.short_description = short_description
        if amount is not None:
            self.amount = amount
        if url is not None:
            self.url = url
        if start_date is not None:
            self.start_date = start_date
        if end_date is not None:
            self.end_date = end_date
        if external_ids is not None:
            self.external_ids = external_ids
        if contributors is not None:
            self.contributors = contributors
        self.organization = organization
        if visibility is not None:
            self.visibility = visibility

    @property
    def created_date(self):
        """Gets the created_date of this FundingV20.  # noqa: E501


        :return: The created_date of this FundingV20.  # noqa: E501
        :rtype: CreatedDateV20
        """
        return self._created_date

    @created_date.setter
    def created_date(self, created_date):
        """Sets the created_date of this FundingV20.


        :param created_date: The created_date of this FundingV20.  # noqa: E501
        :type: CreatedDateV20
        """

        self._created_date = created_date

    @property
    def last_modified_date(self):
        """Gets the last_modified_date of this FundingV20.  # noqa: E501


        :return: The last_modified_date of this FundingV20.  # noqa: E501
        :rtype: LastModifiedDateV20
        """
        return self._last_modified_date

    @last_modified_date.setter
    def last_modified_date(self, last_modified_date):
        """Sets the last_modified_date of this FundingV20.


        :param last_modified_date: The last_modified_date of this FundingV20.  # noqa: E501
        :type: LastModifiedDateV20
        """

        self._last_modified_date = last_modified_date

    @property
    def source(self):
        """Gets the source of this FundingV20.  # noqa: E501


        :return: The source of this FundingV20.  # noqa: E501
        :rtype: SourceV20
        """
        return self._source

    @source.setter
    def source(self, source):
        """Sets the source of this FundingV20.


        :param source: The source of this FundingV20.  # noqa: E501
        :type: SourceV20
        """

        self._source = source

    @property
    def put_code(self):
        """Gets the put_code of this FundingV20.  # noqa: E501


        :return: The put_code of this FundingV20.  # noqa: E501
        :rtype: int
        """
        return self._put_code

    @put_code.setter
    def put_code(self, put_code):
        """Sets the put_code of this FundingV20.


        :param put_code: The put_code of this FundingV20.  # noqa: E501
        :type: int
        """

        self._put_code = put_code

    @property
    def path(self):
        """Gets the path of this FundingV20.  # noqa: E501


        :return: The path of this FundingV20.  # noqa: E501
        :rtype: str
        """
        return self._path

    @path.setter
    def path(self, path):
        """Sets the path of this FundingV20.


        :param path: The path of this FundingV20.  # noqa: E501
        :type: str
        """

        self._path = path

    @property
    def type(self):
        """Gets the type of this FundingV20.  # noqa: E501


        :return: The type of this FundingV20.  # noqa: E501
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this FundingV20.


        :param type: The type of this FundingV20.  # noqa: E501
        :type: str
        """
        if type is None:
            raise ValueError("Invalid value for `type`, must not be `None`")  # noqa: E501
        allowed_values = ["GRANT", "CONTRACT", "AWARD", "SALARY_AWARD"]  # noqa: E501
        if type not in allowed_values:
            raise ValueError(
                "Invalid value for `type` ({0}), must be one of {1}"  # noqa: E501
                .format(type, allowed_values)
            )

        self._type = type

    @property
    def organization_defined_type(self):
        """Gets the organization_defined_type of this FundingV20.  # noqa: E501


        :return: The organization_defined_type of this FundingV20.  # noqa: E501
        :rtype: OrganizationDefinedFundingSubTypeV20
        """
        return self._organization_defined_type

    @organization_defined_type.setter
    def organization_defined_type(self, organization_defined_type):
        """Sets the organization_defined_type of this FundingV20.


        :param organization_defined_type: The organization_defined_type of this FundingV20.  # noqa: E501
        :type: OrganizationDefinedFundingSubTypeV20
        """

        self._organization_defined_type = organization_defined_type

    @property
    def title(self):
        """Gets the title of this FundingV20.  # noqa: E501


        :return: The title of this FundingV20.  # noqa: E501
        :rtype: FundingTitleV20
        """
        return self._title

    @title.setter
    def title(self, title):
        """Sets the title of this FundingV20.


        :param title: The title of this FundingV20.  # noqa: E501
        :type: FundingTitleV20
        """
        if title is None:
            raise ValueError("Invalid value for `title`, must not be `None`")  # noqa: E501

        self._title = title

    @property
    def short_description(self):
        """Gets the short_description of this FundingV20.  # noqa: E501


        :return: The short_description of this FundingV20.  # noqa: E501
        :rtype: str
        """
        return self._short_description

    @short_description.setter
    def short_description(self, short_description):
        """Sets the short_description of this FundingV20.


        :param short_description: The short_description of this FundingV20.  # noqa: E501
        :type: str
        """

        self._short_description = short_description

    @property
    def amount(self):
        """Gets the amount of this FundingV20.  # noqa: E501


        :return: The amount of this FundingV20.  # noqa: E501
        :rtype: AmountV20
        """
        return self._amount

    @amount.setter
    def amount(self, amount):
        """Sets the amount of this FundingV20.


        :param amount: The amount of this FundingV20.  # noqa: E501
        :type: AmountV20
        """

        self._amount = amount

    @property
    def url(self):
        """Gets the url of this FundingV20.  # noqa: E501


        :return: The url of this FundingV20.  # noqa: E501
        :rtype: UrlV20
        """
        return self._url

    @url.setter
    def url(self, url):
        """Sets the url of this FundingV20.


        :param url: The url of this FundingV20.  # noqa: E501
        :type: UrlV20
        """

        self._url = url

    @property
    def start_date(self):
        """Gets the start_date of this FundingV20.  # noqa: E501


        :return: The start_date of this FundingV20.  # noqa: E501
        :rtype: FuzzyDateV20
        """
        return self._start_date

    @start_date.setter
    def start_date(self, start_date):
        """Sets the start_date of this FundingV20.


        :param start_date: The start_date of this FundingV20.  # noqa: E501
        :type: FuzzyDateV20
        """

        self._start_date = start_date

    @property
    def end_date(self):
        """Gets the end_date of this FundingV20.  # noqa: E501


        :return: The end_date of this FundingV20.  # noqa: E501
        :rtype: FuzzyDateV20
        """
        return self._end_date

    @end_date.setter
    def end_date(self, end_date):
        """Sets the end_date of this FundingV20.


        :param end_date: The end_date of this FundingV20.  # noqa: E501
        :type: FuzzyDateV20
        """

        self._end_date = end_date

    @property
    def external_ids(self):
        """Gets the external_ids of this FundingV20.  # noqa: E501


        :return: The external_ids of this FundingV20.  # noqa: E501
        :rtype: ExternalIDsV20
        """
        return self._external_ids

    @external_ids.setter
    def external_ids(self, external_ids):
        """Sets the external_ids of this FundingV20.


        :param external_ids: The external_ids of this FundingV20.  # noqa: E501
        :type: ExternalIDsV20
        """

        self._external_ids = external_ids

    @property
    def contributors(self):
        """Gets the contributors of this FundingV20.  # noqa: E501


        :return: The contributors of this FundingV20.  # noqa: E501
        :rtype: FundingContributorsV20
        """
        return self._contributors

    @contributors.setter
    def contributors(self, contributors):
        """Sets the contributors of this FundingV20.


        :param contributors: The contributors of this FundingV20.  # noqa: E501
        :type: FundingContributorsV20
        """

        self._contributors = contributors

    @property
    def organization(self):
        """Gets the organization of this FundingV20.  # noqa: E501


        :return: The organization of this FundingV20.  # noqa: E501
        :rtype: OrganizationV20
        """
        return self._organization

    @organization.setter
    def organization(self, organization):
        """Sets the organization of this FundingV20.


        :param organization: The organization of this FundingV20.  # noqa: E501
        :type: OrganizationV20
        """
        if organization is None:
            raise ValueError("Invalid value for `organization`, must not be `None`")  # noqa: E501

        self._organization = organization

    @property
    def visibility(self):
        """Gets the visibility of this FundingV20.  # noqa: E501


        :return: The visibility of this FundingV20.  # noqa: E501
        :rtype: str
        """
        return self._visibility

    @visibility.setter
    def visibility(self, visibility):
        """Sets the visibility of this FundingV20.


        :param visibility: The visibility of this FundingV20.  # noqa: E501
        :type: str
        """
        allowed_values = ["LIMITED", "REGISTERED_ONLY", "PUBLIC", "PRIVATE"]  # noqa: E501
        if visibility not in allowed_values:
            raise ValueError(
                "Invalid value for `visibility` ({0}), must be one of {1}"  # noqa: E501
                .format(visibility, allowed_values)
            )

        self._visibility = visibility

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value
        if issubclass(FundingV20, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, FundingV20):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
