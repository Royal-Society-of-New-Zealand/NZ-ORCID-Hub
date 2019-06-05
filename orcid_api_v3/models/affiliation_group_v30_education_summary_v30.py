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
from orcid_api_v3.models.education_summary_v30 import EducationSummaryV30  # noqa: F401,E501
from orcid_api_v3.models.external_i_ds_v30 import ExternalIDsV30  # noqa: F401,E501
from orcid_api_v3.models.last_modified_date_v30 import LastModifiedDateV30  # noqa: F401,E501


class AffiliationGroupV30EducationSummaryV30(object):
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
        'last_modified_date': 'LastModifiedDateV30',
        'external_ids': 'ExternalIDsV30',
        'summaries': 'list[EducationSummaryV30]'
    }

    attribute_map = {
        'last_modified_date': 'last-modified-date',
        'external_ids': 'external-ids',
        'summaries': 'summaries'
    }

    def __init__(self, last_modified_date=None, external_ids=None, summaries=None):  # noqa: E501
        """AffiliationGroupV30EducationSummaryV30 - a model defined in Swagger"""  # noqa: E501
        self._last_modified_date = None
        self._external_ids = None
        self._summaries = None
        self.discriminator = None
        if last_modified_date is not None:
            self.last_modified_date = last_modified_date
        if external_ids is not None:
            self.external_ids = external_ids
        if summaries is not None:
            self.summaries = summaries

    @property
    def last_modified_date(self):
        """Gets the last_modified_date of this AffiliationGroupV30EducationSummaryV30.  # noqa: E501


        :return: The last_modified_date of this AffiliationGroupV30EducationSummaryV30.  # noqa: E501
        :rtype: LastModifiedDateV30
        """
        return self._last_modified_date

    @last_modified_date.setter
    def last_modified_date(self, last_modified_date):
        """Sets the last_modified_date of this AffiliationGroupV30EducationSummaryV30.


        :param last_modified_date: The last_modified_date of this AffiliationGroupV30EducationSummaryV30.  # noqa: E501
        :type: LastModifiedDateV30
        """

        self._last_modified_date = last_modified_date

    @property
    def external_ids(self):
        """Gets the external_ids of this AffiliationGroupV30EducationSummaryV30.  # noqa: E501


        :return: The external_ids of this AffiliationGroupV30EducationSummaryV30.  # noqa: E501
        :rtype: ExternalIDsV30
        """
        return self._external_ids

    @external_ids.setter
    def external_ids(self, external_ids):
        """Sets the external_ids of this AffiliationGroupV30EducationSummaryV30.


        :param external_ids: The external_ids of this AffiliationGroupV30EducationSummaryV30.  # noqa: E501
        :type: ExternalIDsV30
        """

        self._external_ids = external_ids

    @property
    def summaries(self):
        """Gets the summaries of this AffiliationGroupV30EducationSummaryV30.  # noqa: E501


        :return: The summaries of this AffiliationGroupV30EducationSummaryV30.  # noqa: E501
        :rtype: list[EducationSummaryV30]
        """
        return self._summaries

    @summaries.setter
    def summaries(self, summaries):
        """Sets the summaries of this AffiliationGroupV30EducationSummaryV30.


        :param summaries: The summaries of this AffiliationGroupV30EducationSummaryV30.  # noqa: E501
        :type: list[EducationSummaryV30]
        """

        self._summaries = summaries

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
        if issubclass(AffiliationGroupV30EducationSummaryV30, dict):
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
        if not isinstance(other, AffiliationGroupV30EducationSummaryV30):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
