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
from orcid_api_v3.models.created_date_v30_rc1 import CreatedDateV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.external_i_ds_v30_rc1 import ExternalIDsV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.fuzzy_date_v30_rc1 import FuzzyDateV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.last_modified_date_v30_rc1 import LastModifiedDateV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.organization_v30_rc1 import OrganizationV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.source_v30_rc1 import SourceV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.url_v30_rc1 import UrlV30Rc1  # noqa: F401,E501


class DistinctionSummaryV30Rc1(object):
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
        'created_date': 'CreatedDateV30Rc1',
        'last_modified_date': 'LastModifiedDateV30Rc1',
        'source': 'SourceV30Rc1',
        'put_code': 'int',
        'department_name': 'str',
        'role_title': 'str',
        'start_date': 'FuzzyDateV30Rc1',
        'end_date': 'FuzzyDateV30Rc1',
        'organization': 'OrganizationV30Rc1',
        'url': 'UrlV30Rc1',
        'external_ids': 'ExternalIDsV30Rc1',
        'display_index': 'str',
        'visibility': 'str',
        'path': 'str'
    }

    attribute_map = {
        'created_date': 'created-date',
        'last_modified_date': 'last-modified-date',
        'source': 'source',
        'put_code': 'put-code',
        'department_name': 'department-name',
        'role_title': 'role-title',
        'start_date': 'start-date',
        'end_date': 'end-date',
        'organization': 'organization',
        'url': 'url',
        'external_ids': 'external-ids',
        'display_index': 'display-index',
        'visibility': 'visibility',
        'path': 'path'
    }

    def __init__(self, created_date=None, last_modified_date=None, source=None, put_code=None, department_name=None, role_title=None, start_date=None, end_date=None, organization=None, url=None, external_ids=None, display_index=None, visibility=None, path=None):  # noqa: E501
        """DistinctionSummaryV30Rc1 - a model defined in Swagger"""  # noqa: E501
        self._created_date = None
        self._last_modified_date = None
        self._source = None
        self._put_code = None
        self._department_name = None
        self._role_title = None
        self._start_date = None
        self._end_date = None
        self._organization = None
        self._url = None
        self._external_ids = None
        self._display_index = None
        self._visibility = None
        self._path = None
        self.discriminator = None
        if created_date is not None:
            self.created_date = created_date
        if last_modified_date is not None:
            self.last_modified_date = last_modified_date
        if source is not None:
            self.source = source
        if put_code is not None:
            self.put_code = put_code
        if department_name is not None:
            self.department_name = department_name
        if role_title is not None:
            self.role_title = role_title
        if start_date is not None:
            self.start_date = start_date
        if end_date is not None:
            self.end_date = end_date
        if organization is not None:
            self.organization = organization
        if url is not None:
            self.url = url
        if external_ids is not None:
            self.external_ids = external_ids
        if display_index is not None:
            self.display_index = display_index
        if visibility is not None:
            self.visibility = visibility
        if path is not None:
            self.path = path

    @property
    def created_date(self):
        """Gets the created_date of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The created_date of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: CreatedDateV30Rc1
        """
        return self._created_date

    @created_date.setter
    def created_date(self, created_date):
        """Sets the created_date of this DistinctionSummaryV30Rc1.


        :param created_date: The created_date of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: CreatedDateV30Rc1
        """

        self._created_date = created_date

    @property
    def last_modified_date(self):
        """Gets the last_modified_date of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The last_modified_date of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: LastModifiedDateV30Rc1
        """
        return self._last_modified_date

    @last_modified_date.setter
    def last_modified_date(self, last_modified_date):
        """Sets the last_modified_date of this DistinctionSummaryV30Rc1.


        :param last_modified_date: The last_modified_date of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: LastModifiedDateV30Rc1
        """

        self._last_modified_date = last_modified_date

    @property
    def source(self):
        """Gets the source of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The source of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: SourceV30Rc1
        """
        return self._source

    @source.setter
    def source(self, source):
        """Sets the source of this DistinctionSummaryV30Rc1.


        :param source: The source of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: SourceV30Rc1
        """

        self._source = source

    @property
    def put_code(self):
        """Gets the put_code of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The put_code of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: int
        """
        return self._put_code

    @put_code.setter
    def put_code(self, put_code):
        """Sets the put_code of this DistinctionSummaryV30Rc1.


        :param put_code: The put_code of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: int
        """

        self._put_code = put_code

    @property
    def department_name(self):
        """Gets the department_name of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The department_name of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: str
        """
        return self._department_name

    @department_name.setter
    def department_name(self, department_name):
        """Sets the department_name of this DistinctionSummaryV30Rc1.


        :param department_name: The department_name of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: str
        """

        self._department_name = department_name

    @property
    def role_title(self):
        """Gets the role_title of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The role_title of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: str
        """
        return self._role_title

    @role_title.setter
    def role_title(self, role_title):
        """Sets the role_title of this DistinctionSummaryV30Rc1.


        :param role_title: The role_title of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: str
        """

        self._role_title = role_title

    @property
    def start_date(self):
        """Gets the start_date of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The start_date of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: FuzzyDateV30Rc1
        """
        return self._start_date

    @start_date.setter
    def start_date(self, start_date):
        """Sets the start_date of this DistinctionSummaryV30Rc1.


        :param start_date: The start_date of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: FuzzyDateV30Rc1
        """

        self._start_date = start_date

    @property
    def end_date(self):
        """Gets the end_date of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The end_date of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: FuzzyDateV30Rc1
        """
        return self._end_date

    @end_date.setter
    def end_date(self, end_date):
        """Sets the end_date of this DistinctionSummaryV30Rc1.


        :param end_date: The end_date of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: FuzzyDateV30Rc1
        """

        self._end_date = end_date

    @property
    def organization(self):
        """Gets the organization of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The organization of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: OrganizationV30Rc1
        """
        return self._organization

    @organization.setter
    def organization(self, organization):
        """Sets the organization of this DistinctionSummaryV30Rc1.


        :param organization: The organization of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: OrganizationV30Rc1
        """

        self._organization = organization

    @property
    def url(self):
        """Gets the url of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The url of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: UrlV30Rc1
        """
        return self._url

    @url.setter
    def url(self, url):
        """Sets the url of this DistinctionSummaryV30Rc1.


        :param url: The url of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: UrlV30Rc1
        """

        self._url = url

    @property
    def external_ids(self):
        """Gets the external_ids of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The external_ids of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: ExternalIDsV30Rc1
        """
        return self._external_ids

    @external_ids.setter
    def external_ids(self, external_ids):
        """Sets the external_ids of this DistinctionSummaryV30Rc1.


        :param external_ids: The external_ids of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: ExternalIDsV30Rc1
        """

        self._external_ids = external_ids

    @property
    def display_index(self):
        """Gets the display_index of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The display_index of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: str
        """
        return self._display_index

    @display_index.setter
    def display_index(self, display_index):
        """Sets the display_index of this DistinctionSummaryV30Rc1.


        :param display_index: The display_index of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: str
        """

        self._display_index = display_index

    @property
    def visibility(self):
        """Gets the visibility of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The visibility of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: str
        """
        return self._visibility

    @visibility.setter
    def visibility(self, visibility):
        """Sets the visibility of this DistinctionSummaryV30Rc1.


        :param visibility: The visibility of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: str
        """
        allowed_values = ["LIMITED", "REGISTERED_ONLY", "PUBLIC", "PRIVATE"]  # noqa: E501
        if visibility not in allowed_values:
            raise ValueError(
                "Invalid value for `visibility` ({0}), must be one of {1}"  # noqa: E501
                .format(visibility, allowed_values)
            )

        self._visibility = visibility

    @property
    def path(self):
        """Gets the path of this DistinctionSummaryV30Rc1.  # noqa: E501


        :return: The path of this DistinctionSummaryV30Rc1.  # noqa: E501
        :rtype: str
        """
        return self._path

    @path.setter
    def path(self, path):
        """Sets the path of this DistinctionSummaryV30Rc1.


        :param path: The path of this DistinctionSummaryV30Rc1.  # noqa: E501
        :type: str
        """

        self._path = path

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
        if issubclass(DistinctionSummaryV30Rc1, dict):
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
        if not isinstance(other, DistinctionSummaryV30Rc1):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
