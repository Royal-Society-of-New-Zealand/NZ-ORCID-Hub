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
from orcid_api_v3.models.external_i_ds_v30_rc1 import ExternalIDsV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.fuzzy_date_v30_rc1 import FuzzyDateV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.research_resource_hosts_v30_rc1 import ResearchResourceHostsV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.research_resource_title_v30_rc1 import ResearchResourceTitleV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.url_v30_rc1 import UrlV30Rc1  # noqa: F401,E501


class ResearchResourceProposalV30Rc1(object):
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
        'title': 'ResearchResourceTitleV30Rc1',
        'hosts': 'ResearchResourceHostsV30Rc1',
        'external_ids': 'ExternalIDsV30Rc1',
        'start_date': 'FuzzyDateV30Rc1',
        'end_date': 'FuzzyDateV30Rc1',
        'url': 'UrlV30Rc1'
    }

    attribute_map = {
        'title': 'title',
        'hosts': 'hosts',
        'external_ids': 'external-ids',
        'start_date': 'start-date',
        'end_date': 'end-date',
        'url': 'url'
    }

    def __init__(self, title=None, hosts=None, external_ids=None, start_date=None, end_date=None, url=None):  # noqa: E501
        """ResearchResourceProposalV30Rc1 - a model defined in Swagger"""  # noqa: E501
        self._title = None
        self._hosts = None
        self._external_ids = None
        self._start_date = None
        self._end_date = None
        self._url = None
        self.discriminator = None
        if title is not None:
            self.title = title
        if hosts is not None:
            self.hosts = hosts
        if external_ids is not None:
            self.external_ids = external_ids
        if start_date is not None:
            self.start_date = start_date
        if end_date is not None:
            self.end_date = end_date
        if url is not None:
            self.url = url

    @property
    def title(self):
        """Gets the title of this ResearchResourceProposalV30Rc1.  # noqa: E501


        :return: The title of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :rtype: ResearchResourceTitleV30Rc1
        """
        return self._title

    @title.setter
    def title(self, title):
        """Sets the title of this ResearchResourceProposalV30Rc1.


        :param title: The title of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :type: ResearchResourceTitleV30Rc1
        """

        self._title = title

    @property
    def hosts(self):
        """Gets the hosts of this ResearchResourceProposalV30Rc1.  # noqa: E501


        :return: The hosts of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :rtype: ResearchResourceHostsV30Rc1
        """
        return self._hosts

    @hosts.setter
    def hosts(self, hosts):
        """Sets the hosts of this ResearchResourceProposalV30Rc1.


        :param hosts: The hosts of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :type: ResearchResourceHostsV30Rc1
        """

        self._hosts = hosts

    @property
    def external_ids(self):
        """Gets the external_ids of this ResearchResourceProposalV30Rc1.  # noqa: E501


        :return: The external_ids of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :rtype: ExternalIDsV30Rc1
        """
        return self._external_ids

    @external_ids.setter
    def external_ids(self, external_ids):
        """Sets the external_ids of this ResearchResourceProposalV30Rc1.


        :param external_ids: The external_ids of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :type: ExternalIDsV30Rc1
        """

        self._external_ids = external_ids

    @property
    def start_date(self):
        """Gets the start_date of this ResearchResourceProposalV30Rc1.  # noqa: E501


        :return: The start_date of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :rtype: FuzzyDateV30Rc1
        """
        return self._start_date

    @start_date.setter
    def start_date(self, start_date):
        """Sets the start_date of this ResearchResourceProposalV30Rc1.


        :param start_date: The start_date of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :type: FuzzyDateV30Rc1
        """

        self._start_date = start_date

    @property
    def end_date(self):
        """Gets the end_date of this ResearchResourceProposalV30Rc1.  # noqa: E501


        :return: The end_date of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :rtype: FuzzyDateV30Rc1
        """
        return self._end_date

    @end_date.setter
    def end_date(self, end_date):
        """Sets the end_date of this ResearchResourceProposalV30Rc1.


        :param end_date: The end_date of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :type: FuzzyDateV30Rc1
        """

        self._end_date = end_date

    @property
    def url(self):
        """Gets the url of this ResearchResourceProposalV30Rc1.  # noqa: E501


        :return: The url of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :rtype: UrlV30Rc1
        """
        return self._url

    @url.setter
    def url(self, url):
        """Sets the url of this ResearchResourceProposalV30Rc1.


        :param url: The url of this ResearchResourceProposalV30Rc1.  # noqa: E501
        :type: UrlV30Rc1
        """

        self._url = url

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
        if issubclass(ResearchResourceProposalV30Rc1, dict):
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
        if not isinstance(other, ResearchResourceProposalV30Rc1):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
