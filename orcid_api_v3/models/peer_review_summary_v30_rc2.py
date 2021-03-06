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
from orcid_api_v3.models.created_date_v30_rc2 import CreatedDateV30Rc2  # noqa: F401,E501
from orcid_api_v3.models.external_i_ds_v30_rc2 import ExternalIDsV30Rc2  # noqa: F401,E501
from orcid_api_v3.models.fuzzy_date_v30_rc2 import FuzzyDateV30Rc2  # noqa: F401,E501
from orcid_api_v3.models.last_modified_date_v30_rc2 import LastModifiedDateV30Rc2  # noqa: F401,E501
from orcid_api_v3.models.organization_v30_rc2 import OrganizationV30Rc2  # noqa: F401,E501
from orcid_api_v3.models.source_v30_rc2 import SourceV30Rc2  # noqa: F401,E501
from orcid_api_v3.models.url_v30_rc2 import UrlV30Rc2  # noqa: F401,E501


class PeerReviewSummaryV30Rc2(object):
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
        'created_date': 'CreatedDateV30Rc2',
        'last_modified_date': 'LastModifiedDateV30Rc2',
        'source': 'SourceV30Rc2',
        'reviewer_role': 'str',
        'external_ids': 'ExternalIDsV30Rc2',
        'review_url': 'UrlV30Rc2',
        'review_type': 'str',
        'completion_date': 'FuzzyDateV30Rc2',
        'review_group_id': 'str',
        'convening_organization': 'OrganizationV30Rc2',
        'visibility': 'str',
        'put_code': 'int',
        'path': 'str',
        'display_index': 'str'
    }

    attribute_map = {
        'created_date': 'created-date',
        'last_modified_date': 'last-modified-date',
        'source': 'source',
        'reviewer_role': 'reviewer-role',
        'external_ids': 'external-ids',
        'review_url': 'review-url',
        'review_type': 'review-type',
        'completion_date': 'completion-date',
        'review_group_id': 'review-group-id',
        'convening_organization': 'convening-organization',
        'visibility': 'visibility',
        'put_code': 'put-code',
        'path': 'path',
        'display_index': 'display-index'
    }

    def __init__(self, created_date=None, last_modified_date=None, source=None, reviewer_role=None, external_ids=None, review_url=None, review_type=None, completion_date=None, review_group_id=None, convening_organization=None, visibility=None, put_code=None, path=None, display_index=None):  # noqa: E501
        """PeerReviewSummaryV30Rc2 - a model defined in Swagger"""  # noqa: E501
        self._created_date = None
        self._last_modified_date = None
        self._source = None
        self._reviewer_role = None
        self._external_ids = None
        self._review_url = None
        self._review_type = None
        self._completion_date = None
        self._review_group_id = None
        self._convening_organization = None
        self._visibility = None
        self._put_code = None
        self._path = None
        self._display_index = None
        self.discriminator = None
        if created_date is not None:
            self.created_date = created_date
        if last_modified_date is not None:
            self.last_modified_date = last_modified_date
        if source is not None:
            self.source = source
        if reviewer_role is not None:
            self.reviewer_role = reviewer_role
        if external_ids is not None:
            self.external_ids = external_ids
        if review_url is not None:
            self.review_url = review_url
        if review_type is not None:
            self.review_type = review_type
        if completion_date is not None:
            self.completion_date = completion_date
        self.review_group_id = review_group_id
        self.convening_organization = convening_organization
        if visibility is not None:
            self.visibility = visibility
        if put_code is not None:
            self.put_code = put_code
        if path is not None:
            self.path = path
        if display_index is not None:
            self.display_index = display_index

    @property
    def created_date(self):
        """Gets the created_date of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The created_date of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: CreatedDateV30Rc2
        """
        return self._created_date

    @created_date.setter
    def created_date(self, created_date):
        """Sets the created_date of this PeerReviewSummaryV30Rc2.


        :param created_date: The created_date of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: CreatedDateV30Rc2
        """

        self._created_date = created_date

    @property
    def last_modified_date(self):
        """Gets the last_modified_date of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The last_modified_date of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: LastModifiedDateV30Rc2
        """
        return self._last_modified_date

    @last_modified_date.setter
    def last_modified_date(self, last_modified_date):
        """Sets the last_modified_date of this PeerReviewSummaryV30Rc2.


        :param last_modified_date: The last_modified_date of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: LastModifiedDateV30Rc2
        """

        self._last_modified_date = last_modified_date

    @property
    def source(self):
        """Gets the source of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The source of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: SourceV30Rc2
        """
        return self._source

    @source.setter
    def source(self, source):
        """Sets the source of this PeerReviewSummaryV30Rc2.


        :param source: The source of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: SourceV30Rc2
        """

        self._source = source

    @property
    def reviewer_role(self):
        """Gets the reviewer_role of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The reviewer_role of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: str
        """
        return self._reviewer_role

    @reviewer_role.setter
    def reviewer_role(self, reviewer_role):
        """Sets the reviewer_role of this PeerReviewSummaryV30Rc2.


        :param reviewer_role: The reviewer_role of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: str
        """
        allowed_values = ["REVIEWER", "EDITOR", "MEMBER", "CHAIR", "ORGANIZER"]  # noqa: E501
        if reviewer_role not in allowed_values:
            raise ValueError(
                "Invalid value for `reviewer_role` ({0}), must be one of {1}"  # noqa: E501
                .format(reviewer_role, allowed_values)
            )

        self._reviewer_role = reviewer_role

    @property
    def external_ids(self):
        """Gets the external_ids of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The external_ids of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: ExternalIDsV30Rc2
        """
        return self._external_ids

    @external_ids.setter
    def external_ids(self, external_ids):
        """Sets the external_ids of this PeerReviewSummaryV30Rc2.


        :param external_ids: The external_ids of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: ExternalIDsV30Rc2
        """

        self._external_ids = external_ids

    @property
    def review_url(self):
        """Gets the review_url of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The review_url of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: UrlV30Rc2
        """
        return self._review_url

    @review_url.setter
    def review_url(self, review_url):
        """Sets the review_url of this PeerReviewSummaryV30Rc2.


        :param review_url: The review_url of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: UrlV30Rc2
        """

        self._review_url = review_url

    @property
    def review_type(self):
        """Gets the review_type of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The review_type of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: str
        """
        return self._review_type

    @review_type.setter
    def review_type(self, review_type):
        """Sets the review_type of this PeerReviewSummaryV30Rc2.


        :param review_type: The review_type of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: str
        """
        allowed_values = ["REVIEW", "EVALUATION"]  # noqa: E501
        if review_type not in allowed_values:
            raise ValueError(
                "Invalid value for `review_type` ({0}), must be one of {1}"  # noqa: E501
                .format(review_type, allowed_values)
            )

        self._review_type = review_type

    @property
    def completion_date(self):
        """Gets the completion_date of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The completion_date of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: FuzzyDateV30Rc2
        """
        return self._completion_date

    @completion_date.setter
    def completion_date(self, completion_date):
        """Sets the completion_date of this PeerReviewSummaryV30Rc2.


        :param completion_date: The completion_date of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: FuzzyDateV30Rc2
        """

        self._completion_date = completion_date

    @property
    def review_group_id(self):
        """Gets the review_group_id of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The review_group_id of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: str
        """
        return self._review_group_id

    @review_group_id.setter
    def review_group_id(self, review_group_id):
        """Sets the review_group_id of this PeerReviewSummaryV30Rc2.


        :param review_group_id: The review_group_id of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: str
        """
        if review_group_id is None:
            raise ValueError("Invalid value for `review_group_id`, must not be `None`")  # noqa: E501

        self._review_group_id = review_group_id

    @property
    def convening_organization(self):
        """Gets the convening_organization of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The convening_organization of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: OrganizationV30Rc2
        """
        return self._convening_organization

    @convening_organization.setter
    def convening_organization(self, convening_organization):
        """Sets the convening_organization of this PeerReviewSummaryV30Rc2.


        :param convening_organization: The convening_organization of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: OrganizationV30Rc2
        """
        if convening_organization is None:
            raise ValueError("Invalid value for `convening_organization`, must not be `None`")  # noqa: E501

        self._convening_organization = convening_organization

    @property
    def visibility(self):
        """Gets the visibility of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The visibility of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: str
        """
        return self._visibility

    @visibility.setter
    def visibility(self, visibility):
        """Sets the visibility of this PeerReviewSummaryV30Rc2.


        :param visibility: The visibility of this PeerReviewSummaryV30Rc2.  # noqa: E501
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
    def put_code(self):
        """Gets the put_code of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The put_code of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: int
        """
        return self._put_code

    @put_code.setter
    def put_code(self, put_code):
        """Sets the put_code of this PeerReviewSummaryV30Rc2.


        :param put_code: The put_code of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: int
        """

        self._put_code = put_code

    @property
    def path(self):
        """Gets the path of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The path of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: str
        """
        return self._path

    @path.setter
    def path(self, path):
        """Sets the path of this PeerReviewSummaryV30Rc2.


        :param path: The path of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: str
        """

        self._path = path

    @property
    def display_index(self):
        """Gets the display_index of this PeerReviewSummaryV30Rc2.  # noqa: E501


        :return: The display_index of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :rtype: str
        """
        return self._display_index

    @display_index.setter
    def display_index(self, display_index):
        """Sets the display_index of this PeerReviewSummaryV30Rc2.


        :param display_index: The display_index of this PeerReviewSummaryV30Rc2.  # noqa: E501
        :type: str
        """

        self._display_index = display_index

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
        if issubclass(PeerReviewSummaryV30Rc2, dict):
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
        if not isinstance(other, PeerReviewSummaryV30Rc2):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
