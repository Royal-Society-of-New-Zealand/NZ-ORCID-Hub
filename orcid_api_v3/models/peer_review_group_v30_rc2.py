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
from orcid_api_v3.models.external_i_ds_v30_rc2 import ExternalIDsV30Rc2  # noqa: F401,E501
from orcid_api_v3.models.last_modified_date_v30_rc2 import LastModifiedDateV30Rc2  # noqa: F401,E501
from orcid_api_v3.models.peer_review_duplicate_group_v30_rc2 import PeerReviewDuplicateGroupV30Rc2  # noqa: F401,E501


class PeerReviewGroupV30Rc2(object):
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
        'external_ids': 'ExternalIDsV30Rc2',
        'peer_review_group': 'list[PeerReviewDuplicateGroupV30Rc2]'
    }

    attribute_map = {
        'last_modified_date': 'last-modified-date',
        'external_ids': 'external-ids',
        'peer_review_group': 'peer-review-group'
    }

    def __init__(self, last_modified_date=None, external_ids=None, peer_review_group=None):  # noqa: E501
        """PeerReviewGroupV30Rc2 - a model defined in Swagger"""  # noqa: E501
        self._last_modified_date = None
        self._external_ids = None
        self._peer_review_group = None
        self.discriminator = None
        if last_modified_date is not None:
            self.last_modified_date = last_modified_date
        if external_ids is not None:
            self.external_ids = external_ids
        if peer_review_group is not None:
            self.peer_review_group = peer_review_group

    @property
    def last_modified_date(self):
        """Gets the last_modified_date of this PeerReviewGroupV30Rc2.  # noqa: E501


        :return: The last_modified_date of this PeerReviewGroupV30Rc2.  # noqa: E501
        :rtype: LastModifiedDateV30Rc2
        """
        return self._last_modified_date

    @last_modified_date.setter
    def last_modified_date(self, last_modified_date):
        """Sets the last_modified_date of this PeerReviewGroupV30Rc2.


        :param last_modified_date: The last_modified_date of this PeerReviewGroupV30Rc2.  # noqa: E501
        :type: LastModifiedDateV30Rc2
        """

        self._last_modified_date = last_modified_date

    @property
    def external_ids(self):
        """Gets the external_ids of this PeerReviewGroupV30Rc2.  # noqa: E501


        :return: The external_ids of this PeerReviewGroupV30Rc2.  # noqa: E501
        :rtype: ExternalIDsV30Rc2
        """
        return self._external_ids

    @external_ids.setter
    def external_ids(self, external_ids):
        """Sets the external_ids of this PeerReviewGroupV30Rc2.


        :param external_ids: The external_ids of this PeerReviewGroupV30Rc2.  # noqa: E501
        :type: ExternalIDsV30Rc2
        """

        self._external_ids = external_ids

    @property
    def peer_review_group(self):
        """Gets the peer_review_group of this PeerReviewGroupV30Rc2.  # noqa: E501


        :return: The peer_review_group of this PeerReviewGroupV30Rc2.  # noqa: E501
        :rtype: list[PeerReviewDuplicateGroupV30Rc2]
        """
        return self._peer_review_group

    @peer_review_group.setter
    def peer_review_group(self, peer_review_group):
        """Sets the peer_review_group of this PeerReviewGroupV30Rc2.


        :param peer_review_group: The peer_review_group of this PeerReviewGroupV30Rc2.  # noqa: E501
        :type: list[PeerReviewDuplicateGroupV30Rc2]
        """

        self._peer_review_group = peer_review_group

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
        if issubclass(PeerReviewGroupV30Rc2, dict):
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
        if not isinstance(other, PeerReviewGroupV30Rc2):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
