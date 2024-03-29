# coding: utf-8

"""
    ORCID Member

    No description provided (generated by Swagger Codegen https://github.com/swagger-api/swagger-codegen)

    OpenAPI spec version: Latest
    
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


from pprint import pformat
from six import iteritems
import re


class ContributorAttributes(object):
    """
    NOTE: This class is auto generated by the swagger code generator program.
    Do not edit the class manually.
    """
    def __init__(self, contributor_sequence=None, contributor_role=None):
        """
        ContributorAttributes - a model defined in Swagger

        :param dict swaggerTypes: The key is attribute name
                                  and the value is attribute type.
        :param dict attributeMap: The key is attribute name
                                  and the value is json key in definition.
        """
        self.swagger_types = {
            'contributor_sequence': 'str',
            'contributor_role': 'str'
        }

        self.attribute_map = {
            'contributor_sequence': 'contributor-sequence',
            'contributor_role': 'contributor-role'
        }

        self._contributor_sequence = contributor_sequence
        self._contributor_role = contributor_role

    @property
    def contributor_sequence(self):
        """
        Gets the contributor_sequence of this ContributorAttributes.

        :return: The contributor_sequence of this ContributorAttributes.
        :rtype: str
        """
        return self._contributor_sequence

    @contributor_sequence.setter
    def contributor_sequence(self, contributor_sequence):
        """
        Sets the contributor_sequence of this ContributorAttributes.

        :param contributor_sequence: The contributor_sequence of this ContributorAttributes.
        :type: str
        """
        allowed_values = ["FIRST", "ADDITIONAL"]
        if contributor_sequence not in allowed_values:
            raise ValueError(
                "Invalid value for `contributor_sequence` ({0}), must be one of {1}"
                .format(contributor_sequence, allowed_values)
            )

        self._contributor_sequence = contributor_sequence

    @property
    def contributor_role(self):
        """
        Gets the contributor_role of this ContributorAttributes.

        :return: The contributor_role of this ContributorAttributes.
        :rtype: str
        """
        return self._contributor_role

    @contributor_role.setter
    def contributor_role(self, contributor_role):
        """
        Sets the contributor_role of this ContributorAttributes.

        :param contributor_role: The contributor_role of this ContributorAttributes.
        :type: str
        """
        allowed_values = ["AUTHOR", "ASSIGNEE", "EDITOR", "CHAIR_OR_TRANSLATOR", "CO_INVESTIGATOR", "CO_INVENTOR", "GRADUATE_STUDENT", 
        "OTHER_INVENTOR", "PRINCIPAL_INVESTIGATOR", "POSTDOCTORAL_RESEARCHER", "SUPPORT_STAFF",
        "http://credit.niso.org/contributor-roles/conceptualization/", "http://credit.niso.org/contributor-roles/data-curation/", 
        "http://credit.niso.org/contributor-roles/formal-analysis/", "http://credit.niso.org/contributor-roles/funding-acquisition/", 
        "http://credit.niso.org/contributor-roles/investigation/", "http://credit.niso.org/contributor-roles/methodology/", 
        "http://credit.niso.org/contributor-roles/project-administration/", "http://credit.niso.org/contributor-roles/resources/", 
        "http://credit.niso.org/contributor-roles/software/", "http://credit.niso.org/contributor-roles/supervision/", 
        "http://credit.niso.org/contributor-roles/validation/", "http://credit.niso.org/contributor-roles/visualization/", 
        "http://credit.niso.org/contributor-roles/writing-original-draft/", "http://credit.niso.org/contributor-roles/writing-review-editing/"]
        if contributor_role not in allowed_values:
            raise ValueError(
                "Invalid value for `contributor_role` ({0}), must be one of {1}"
                .format(contributor_role, allowed_values)
            )

        self._contributor_role = contributor_role

    def to_dict(self):
        """
        Returns the model properties as a dict
        """
        result = {}

        for attr, _ in iteritems(self.swagger_types):
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

        return result

    def to_str(self):
        """
        Returns the string representation of the model
        """
        return pformat(self.to_dict())

    def __repr__(self):
        """
        For `print` and `pprint`
        """
        return self.to_str()

    def __eq__(self, other):
        """
        Returns true if both objects are equal
        """
        if not isinstance(other, ContributorAttributes):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """
        Returns true if both objects are not equal
        """
        return not self == other
