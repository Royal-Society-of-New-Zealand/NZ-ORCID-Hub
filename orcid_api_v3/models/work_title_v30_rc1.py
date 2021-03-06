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
from orcid_api_v3.models.subtitle_v30_rc1 import SubtitleV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.title_v30_rc1 import TitleV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.translated_title_v30_rc1 import TranslatedTitleV30Rc1  # noqa: F401,E501


class WorkTitleV30Rc1(object):
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
        'title': 'TitleV30Rc1',
        'subtitle': 'SubtitleV30Rc1',
        'translated_title': 'TranslatedTitleV30Rc1'
    }

    attribute_map = {
        'title': 'title',
        'subtitle': 'subtitle',
        'translated_title': 'translated-title'
    }

    def __init__(self, title=None, subtitle=None, translated_title=None):  # noqa: E501
        """WorkTitleV30Rc1 - a model defined in Swagger"""  # noqa: E501
        self._title = None
        self._subtitle = None
        self._translated_title = None
        self.discriminator = None
        if title is not None:
            self.title = title
        if subtitle is not None:
            self.subtitle = subtitle
        if translated_title is not None:
            self.translated_title = translated_title

    @property
    def title(self):
        """Gets the title of this WorkTitleV30Rc1.  # noqa: E501


        :return: The title of this WorkTitleV30Rc1.  # noqa: E501
        :rtype: TitleV30Rc1
        """
        return self._title

    @title.setter
    def title(self, title):
        """Sets the title of this WorkTitleV30Rc1.


        :param title: The title of this WorkTitleV30Rc1.  # noqa: E501
        :type: TitleV30Rc1
        """

        self._title = title

    @property
    def subtitle(self):
        """Gets the subtitle of this WorkTitleV30Rc1.  # noqa: E501


        :return: The subtitle of this WorkTitleV30Rc1.  # noqa: E501
        :rtype: SubtitleV30Rc1
        """
        return self._subtitle

    @subtitle.setter
    def subtitle(self, subtitle):
        """Sets the subtitle of this WorkTitleV30Rc1.


        :param subtitle: The subtitle of this WorkTitleV30Rc1.  # noqa: E501
        :type: SubtitleV30Rc1
        """

        self._subtitle = subtitle

    @property
    def translated_title(self):
        """Gets the translated_title of this WorkTitleV30Rc1.  # noqa: E501


        :return: The translated_title of this WorkTitleV30Rc1.  # noqa: E501
        :rtype: TranslatedTitleV30Rc1
        """
        return self._translated_title

    @translated_title.setter
    def translated_title(self, translated_title):
        """Sets the translated_title of this WorkTitleV30Rc1.


        :param translated_title: The translated_title of this WorkTitleV30Rc1.  # noqa: E501
        :type: TranslatedTitleV30Rc1
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
        if issubclass(WorkTitleV30Rc1, dict):
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
        if not isinstance(other, WorkTitleV30Rc1):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
