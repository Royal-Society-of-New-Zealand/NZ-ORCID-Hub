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
from orcid_api_v3.models.affiliation_group_v30_rc2_invited_position_summary_v30_rc2 import AffiliationGroupV30Rc2InvitedPositionSummaryV30Rc2  # noqa: F401,E501
from orcid_api_v3.models.last_modified_date_v30_rc2 import LastModifiedDateV30Rc2  # noqa: F401,E501


class InvitedPositionsV30Rc2(object):
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
        'last_modified_date': 'LastModifiedDateV30Rc2',
        'affiliation_group': 'list[AffiliationGroupV30Rc2InvitedPositionSummaryV30Rc2]',
        'path': 'str'
    }

    attribute_map = {
        'last_modified_date': 'last-modified-date',
        'affiliation_group': 'affiliation-group',
        'path': 'path'
    }

    def __init__(self, last_modified_date=None, affiliation_group=None, path=None):  # noqa: E501
        """InvitedPositionsV30Rc2 - a model defined in Swagger"""  # noqa: E501
        self._last_modified_date = None
        self._affiliation_group = None
        self._path = None
        self.discriminator = None
        if last_modified_date is not None:
            self.last_modified_date = last_modified_date
        if affiliation_group is not None:
            self.affiliation_group = affiliation_group
        if path is not None:
            self.path = path

    @property
    def last_modified_date(self):
        """Gets the last_modified_date of this InvitedPositionsV30Rc2.  # noqa: E501


        :return: The last_modified_date of this InvitedPositionsV30Rc2.  # noqa: E501
        :rtype: LastModifiedDateV30Rc2
        """
        return self._last_modified_date

    @last_modified_date.setter
    def last_modified_date(self, last_modified_date):
        """Sets the last_modified_date of this InvitedPositionsV30Rc2.


        :param last_modified_date: The last_modified_date of this InvitedPositionsV30Rc2.  # noqa: E501
        :type: LastModifiedDateV30Rc2
        """

        self._last_modified_date = last_modified_date

    @property
    def affiliation_group(self):
        """Gets the affiliation_group of this InvitedPositionsV30Rc2.  # noqa: E501


        :return: The affiliation_group of this InvitedPositionsV30Rc2.  # noqa: E501
        :rtype: list[AffiliationGroupV30Rc2InvitedPositionSummaryV30Rc2]
        """
        return self._affiliation_group

    @affiliation_group.setter
    def affiliation_group(self, affiliation_group):
        """Sets the affiliation_group of this InvitedPositionsV30Rc2.


        :param affiliation_group: The affiliation_group of this InvitedPositionsV30Rc2.  # noqa: E501
        :type: list[AffiliationGroupV30Rc2InvitedPositionSummaryV30Rc2]
        """

        self._affiliation_group = affiliation_group

    @property
    def path(self):
        """Gets the path of this InvitedPositionsV30Rc2.  # noqa: E501


        :return: The path of this InvitedPositionsV30Rc2.  # noqa: E501
        :rtype: str
        """
        return self._path

    @path.setter
    def path(self, path):
        """Sets the path of this InvitedPositionsV30Rc2.


        :param path: The path of this InvitedPositionsV30Rc2.  # noqa: E501
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
        if issubclass(InvitedPositionsV30Rc2, dict):
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
        if not isinstance(other, InvitedPositionsV30Rc2):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
