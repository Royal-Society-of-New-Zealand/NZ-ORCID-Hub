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
from orcid_api_v3.models.distinctions_summary_v30 import DistinctionsSummaryV30  # noqa: F401,E501
from orcid_api_v3.models.educations_summary_v30 import EducationsSummaryV30  # noqa: F401,E501
from orcid_api_v3.models.employments_summary_v30 import EmploymentsSummaryV30  # noqa: F401,E501
from orcid_api_v3.models.fundings_v30 import FundingsV30  # noqa: F401,E501
from orcid_api_v3.models.invited_positions_v30 import InvitedPositionsV30  # noqa: F401,E501
from orcid_api_v3.models.last_modified_date_v30 import LastModifiedDateV30  # noqa: F401,E501
from orcid_api_v3.models.memberships_v30 import MembershipsV30  # noqa: F401,E501
from orcid_api_v3.models.peer_reviews_v30 import PeerReviewsV30  # noqa: F401,E501
from orcid_api_v3.models.qualifications_v30 import QualificationsV30  # noqa: F401,E501
from orcid_api_v3.models.research_resources_v30 import ResearchResourcesV30  # noqa: F401,E501
from orcid_api_v3.models.services_v30 import ServicesV30  # noqa: F401,E501
from orcid_api_v3.models.works_summary_v30 import WorksSummaryV30  # noqa: F401,E501


class ActivitiesSummaryV30(object):
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
        'distinctions': 'DistinctionsSummaryV30',
        'educations': 'EducationsSummaryV30',
        'employments': 'EmploymentsSummaryV30',
        'fundings': 'FundingsV30',
        'invited_positions': 'InvitedPositionsV30',
        'memberships': 'MembershipsV30',
        'peer_reviews': 'PeerReviewsV30',
        'qualifications': 'QualificationsV30',
        'research_resources': 'ResearchResourcesV30',
        'services': 'ServicesV30',
        'works': 'WorksSummaryV30',
        'path': 'str'
    }

    attribute_map = {
        'last_modified_date': 'last-modified-date',
        'distinctions': 'distinctions',
        'educations': 'educations',
        'employments': 'employments',
        'fundings': 'fundings',
        'invited_positions': 'invited-positions',
        'memberships': 'memberships',
        'peer_reviews': 'peer-reviews',
        'qualifications': 'qualifications',
        'research_resources': 'research-resources',
        'services': 'services',
        'works': 'works',
        'path': 'path'
    }

    def __init__(self, last_modified_date=None, distinctions=None, educations=None, employments=None, fundings=None, invited_positions=None, memberships=None, peer_reviews=None, qualifications=None, research_resources=None, services=None, works=None, path=None):  # noqa: E501
        """ActivitiesSummaryV30 - a model defined in Swagger"""  # noqa: E501
        self._last_modified_date = None
        self._distinctions = None
        self._educations = None
        self._employments = None
        self._fundings = None
        self._invited_positions = None
        self._memberships = None
        self._peer_reviews = None
        self._qualifications = None
        self._research_resources = None
        self._services = None
        self._works = None
        self._path = None
        self.discriminator = None
        if last_modified_date is not None:
            self.last_modified_date = last_modified_date
        if distinctions is not None:
            self.distinctions = distinctions
        if educations is not None:
            self.educations = educations
        if employments is not None:
            self.employments = employments
        if fundings is not None:
            self.fundings = fundings
        if invited_positions is not None:
            self.invited_positions = invited_positions
        if memberships is not None:
            self.memberships = memberships
        if peer_reviews is not None:
            self.peer_reviews = peer_reviews
        if qualifications is not None:
            self.qualifications = qualifications
        if research_resources is not None:
            self.research_resources = research_resources
        if services is not None:
            self.services = services
        if works is not None:
            self.works = works
        if path is not None:
            self.path = path

    @property
    def last_modified_date(self):
        """Gets the last_modified_date of this ActivitiesSummaryV30.  # noqa: E501


        :return: The last_modified_date of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: LastModifiedDateV30
        """
        return self._last_modified_date

    @last_modified_date.setter
    def last_modified_date(self, last_modified_date):
        """Sets the last_modified_date of this ActivitiesSummaryV30.


        :param last_modified_date: The last_modified_date of this ActivitiesSummaryV30.  # noqa: E501
        :type: LastModifiedDateV30
        """

        self._last_modified_date = last_modified_date

    @property
    def distinctions(self):
        """Gets the distinctions of this ActivitiesSummaryV30.  # noqa: E501


        :return: The distinctions of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: DistinctionsSummaryV30
        """
        return self._distinctions

    @distinctions.setter
    def distinctions(self, distinctions):
        """Sets the distinctions of this ActivitiesSummaryV30.


        :param distinctions: The distinctions of this ActivitiesSummaryV30.  # noqa: E501
        :type: DistinctionsSummaryV30
        """

        self._distinctions = distinctions

    @property
    def educations(self):
        """Gets the educations of this ActivitiesSummaryV30.  # noqa: E501


        :return: The educations of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: EducationsSummaryV30
        """
        return self._educations

    @educations.setter
    def educations(self, educations):
        """Sets the educations of this ActivitiesSummaryV30.


        :param educations: The educations of this ActivitiesSummaryV30.  # noqa: E501
        :type: EducationsSummaryV30
        """

        self._educations = educations

    @property
    def employments(self):
        """Gets the employments of this ActivitiesSummaryV30.  # noqa: E501


        :return: The employments of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: EmploymentsSummaryV30
        """
        return self._employments

    @employments.setter
    def employments(self, employments):
        """Sets the employments of this ActivitiesSummaryV30.


        :param employments: The employments of this ActivitiesSummaryV30.  # noqa: E501
        :type: EmploymentsSummaryV30
        """

        self._employments = employments

    @property
    def fundings(self):
        """Gets the fundings of this ActivitiesSummaryV30.  # noqa: E501


        :return: The fundings of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: FundingsV30
        """
        return self._fundings

    @fundings.setter
    def fundings(self, fundings):
        """Sets the fundings of this ActivitiesSummaryV30.


        :param fundings: The fundings of this ActivitiesSummaryV30.  # noqa: E501
        :type: FundingsV30
        """

        self._fundings = fundings

    @property
    def invited_positions(self):
        """Gets the invited_positions of this ActivitiesSummaryV30.  # noqa: E501


        :return: The invited_positions of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: InvitedPositionsV30
        """
        return self._invited_positions

    @invited_positions.setter
    def invited_positions(self, invited_positions):
        """Sets the invited_positions of this ActivitiesSummaryV30.


        :param invited_positions: The invited_positions of this ActivitiesSummaryV30.  # noqa: E501
        :type: InvitedPositionsV30
        """

        self._invited_positions = invited_positions

    @property
    def memberships(self):
        """Gets the memberships of this ActivitiesSummaryV30.  # noqa: E501


        :return: The memberships of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: MembershipsV30
        """
        return self._memberships

    @memberships.setter
    def memberships(self, memberships):
        """Sets the memberships of this ActivitiesSummaryV30.


        :param memberships: The memberships of this ActivitiesSummaryV30.  # noqa: E501
        :type: MembershipsV30
        """

        self._memberships = memberships

    @property
    def peer_reviews(self):
        """Gets the peer_reviews of this ActivitiesSummaryV30.  # noqa: E501


        :return: The peer_reviews of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: PeerReviewsV30
        """
        return self._peer_reviews

    @peer_reviews.setter
    def peer_reviews(self, peer_reviews):
        """Sets the peer_reviews of this ActivitiesSummaryV30.


        :param peer_reviews: The peer_reviews of this ActivitiesSummaryV30.  # noqa: E501
        :type: PeerReviewsV30
        """

        self._peer_reviews = peer_reviews

    @property
    def qualifications(self):
        """Gets the qualifications of this ActivitiesSummaryV30.  # noqa: E501


        :return: The qualifications of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: QualificationsV30
        """
        return self._qualifications

    @qualifications.setter
    def qualifications(self, qualifications):
        """Sets the qualifications of this ActivitiesSummaryV30.


        :param qualifications: The qualifications of this ActivitiesSummaryV30.  # noqa: E501
        :type: QualificationsV30
        """

        self._qualifications = qualifications

    @property
    def research_resources(self):
        """Gets the research_resources of this ActivitiesSummaryV30.  # noqa: E501


        :return: The research_resources of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: ResearchResourcesV30
        """
        return self._research_resources

    @research_resources.setter
    def research_resources(self, research_resources):
        """Sets the research_resources of this ActivitiesSummaryV30.


        :param research_resources: The research_resources of this ActivitiesSummaryV30.  # noqa: E501
        :type: ResearchResourcesV30
        """

        self._research_resources = research_resources

    @property
    def services(self):
        """Gets the services of this ActivitiesSummaryV30.  # noqa: E501


        :return: The services of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: ServicesV30
        """
        return self._services

    @services.setter
    def services(self, services):
        """Sets the services of this ActivitiesSummaryV30.


        :param services: The services of this ActivitiesSummaryV30.  # noqa: E501
        :type: ServicesV30
        """

        self._services = services

    @property
    def works(self):
        """Gets the works of this ActivitiesSummaryV30.  # noqa: E501


        :return: The works of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: WorksSummaryV30
        """
        return self._works

    @works.setter
    def works(self, works):
        """Sets the works of this ActivitiesSummaryV30.


        :param works: The works of this ActivitiesSummaryV30.  # noqa: E501
        :type: WorksSummaryV30
        """

        self._works = works

    @property
    def path(self):
        """Gets the path of this ActivitiesSummaryV30.  # noqa: E501


        :return: The path of this ActivitiesSummaryV30.  # noqa: E501
        :rtype: str
        """
        return self._path

    @path.setter
    def path(self, path):
        """Sets the path of this ActivitiesSummaryV30.


        :param path: The path of this ActivitiesSummaryV30.  # noqa: E501
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
        if issubclass(ActivitiesSummaryV30, dict):
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
        if not isinstance(other, ActivitiesSummaryV30):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other