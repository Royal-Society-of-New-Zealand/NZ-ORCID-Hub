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
from orcid_api_v3.models.title_v30_rc2 import TitleV30Rc2  # noqa: F401,E501
from orcid_api_v3.models.translated_title_v30_rc2 import TranslatedTitleV30Rc2  # noqa: F401,E501


class ResearchResourceTitleV30Rc2(object):
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
        'title': 'TitleV30Rc2',
        'translated_title': 'TranslatedTitleV30Rc2'
    }

    attribute_map = {
        'title': 'title',
        'translated_title': 'translated-title'
    }

    def __init__(self, title=None, translated_title=None):  # noqa: E501
        """ResearchResourceTitleV30Rc2 - a model defined in Swagger"""  # noqa: E501
        self._title = None
        self._translated_title = None
        self.discriminator = None
        if title is not None:
            self.title = title
        if translated_title is not None:
            self.translated_title = translated_title

    @property
    def title(self):
        """Gets the title of this ResearchResourceTitleV30Rc2.  # noqa: E501


        :return: The title of this ResearchResourceTitleV30Rc2.  # noqa: E501
        :rtype: TitleV30Rc2
        """
        return self._title

    @title.setter
    def title(self, title):
        """Sets the title of this ResearchResourceTitleV30Rc2.


        :param title: The title of this ResearchResourceTitleV30Rc2.  # noqa: E501
        :type: TitleV30Rc2
        """

        self._title = title

    @property
    def translated_title(self):
        """Gets the translated_title of this ResearchResourceTitleV30Rc2.  # noqa: E501


        :return: The translated_title of this ResearchResourceTitleV30Rc2.  # noqa: E501
        :rtype: TranslatedTitleV30Rc2
        """
        return self._translated_title

    @translated_title.setter
    def translated_title(self, translated_title):
        """Sets the translated_title of this ResearchResourceTitleV30Rc2.


        :param translated_title: The translated_title of this ResearchResourceTitleV30Rc2.  # noqa: E501
        :type: TranslatedTitleV30Rc2
        """

        self._translated_title = translated_title

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
        if issubclass(ResearchResourceTitleV30Rc2, dict):
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
        if not isinstance(other, ResearchResourceTitleV30Rc2):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
