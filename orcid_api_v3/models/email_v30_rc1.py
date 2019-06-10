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
from orcid_api_v3.models.last_modified_date_v30_rc1 import LastModifiedDateV30Rc1  # noqa: F401,E501
from orcid_api_v3.models.source_v30_rc1 import SourceV30Rc1  # noqa: F401,E501


class EmailV30Rc1(object):
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
        'email': 'str',
        'path': 'str',
        'visibility': 'str',
        'verified': 'bool',
        'primary': 'bool',
        'put_code': 'int'
    }

    attribute_map = {
        'created_date': 'created-date',
        'last_modified_date': 'last-modified-date',
        'source': 'source',
        'email': 'email',
        'path': 'path',
        'visibility': 'visibility',
        'verified': 'verified',
        'primary': 'primary',
        'put_code': 'put-code'
    }

    def __init__(self, created_date=None, last_modified_date=None, source=None, email=None, path=None, visibility=None, verified=None, primary=None, put_code=None):  # noqa: E501
        """EmailV30Rc1 - a model defined in Swagger"""  # noqa: E501
        self._created_date = None
        self._last_modified_date = None
        self._source = None
        self._email = None
        self._path = None
        self._visibility = None
        self._verified = None
        self._primary = None
        self._put_code = None
        self.discriminator = None
        if created_date is not None:
            self.created_date = created_date
        if last_modified_date is not None:
            self.last_modified_date = last_modified_date
        if source is not None:
            self.source = source
        if email is not None:
            self.email = email
        if path is not None:
            self.path = path
        if visibility is not None:
            self.visibility = visibility
        if verified is not None:
            self.verified = verified
        if primary is not None:
            self.primary = primary
        if put_code is not None:
            self.put_code = put_code

    @property
    def created_date(self):
        """Gets the created_date of this EmailV30Rc1.  # noqa: E501


        :return: The created_date of this EmailV30Rc1.  # noqa: E501
        :rtype: CreatedDateV30Rc1
        """
        return self._created_date

    @created_date.setter
    def created_date(self, created_date):
        """Sets the created_date of this EmailV30Rc1.


        :param created_date: The created_date of this EmailV30Rc1.  # noqa: E501
        :type: CreatedDateV30Rc1
        """

        self._created_date = created_date

    @property
    def last_modified_date(self):
        """Gets the last_modified_date of this EmailV30Rc1.  # noqa: E501


        :return: The last_modified_date of this EmailV30Rc1.  # noqa: E501
        :rtype: LastModifiedDateV30Rc1
        """
        return self._last_modified_date

    @last_modified_date.setter
    def last_modified_date(self, last_modified_date):
        """Sets the last_modified_date of this EmailV30Rc1.


        :param last_modified_date: The last_modified_date of this EmailV30Rc1.  # noqa: E501
        :type: LastModifiedDateV30Rc1
        """

        self._last_modified_date = last_modified_date

    @property
    def source(self):
        """Gets the source of this EmailV30Rc1.  # noqa: E501


        :return: The source of this EmailV30Rc1.  # noqa: E501
        :rtype: SourceV30Rc1
        """
        return self._source

    @source.setter
    def source(self, source):
        """Sets the source of this EmailV30Rc1.


        :param source: The source of this EmailV30Rc1.  # noqa: E501
        :type: SourceV30Rc1
        """

        self._source = source

    @property
    def email(self):
        """Gets the email of this EmailV30Rc1.  # noqa: E501


        :return: The email of this EmailV30Rc1.  # noqa: E501
        :rtype: str
        """
        return self._email

    @email.setter
    def email(self, email):
        """Sets the email of this EmailV30Rc1.


        :param email: The email of this EmailV30Rc1.  # noqa: E501
        :type: str
        """

        self._email = email

    @property
    def path(self):
        """Gets the path of this EmailV30Rc1.  # noqa: E501


        :return: The path of this EmailV30Rc1.  # noqa: E501
        :rtype: str
        """
        return self._path

    @path.setter
    def path(self, path):
        """Sets the path of this EmailV30Rc1.


        :param path: The path of this EmailV30Rc1.  # noqa: E501
        :type: str
        """

        self._path = path

    @property
    def visibility(self):
        """Gets the visibility of this EmailV30Rc1.  # noqa: E501


        :return: The visibility of this EmailV30Rc1.  # noqa: E501
        :rtype: str
        """
        return self._visibility

    @visibility.setter
    def visibility(self, visibility):
        """Sets the visibility of this EmailV30Rc1.


        :param visibility: The visibility of this EmailV30Rc1.  # noqa: E501
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
    def verified(self):
        """Gets the verified of this EmailV30Rc1.  # noqa: E501


        :return: The verified of this EmailV30Rc1.  # noqa: E501
        :rtype: bool
        """
        return self._verified

    @verified.setter
    def verified(self, verified):
        """Sets the verified of this EmailV30Rc1.


        :param verified: The verified of this EmailV30Rc1.  # noqa: E501
        :type: bool
        """

        self._verified = verified

    @property
    def primary(self):
        """Gets the primary of this EmailV30Rc1.  # noqa: E501


        :return: The primary of this EmailV30Rc1.  # noqa: E501
        :rtype: bool
        """
        return self._primary

    @primary.setter
    def primary(self, primary):
        """Sets the primary of this EmailV30Rc1.


        :param primary: The primary of this EmailV30Rc1.  # noqa: E501
        :type: bool
        """

        self._primary = primary

    @property
    def put_code(self):
        """Gets the put_code of this EmailV30Rc1.  # noqa: E501


        :return: The put_code of this EmailV30Rc1.  # noqa: E501
        :rtype: int
        """
        return self._put_code

    @put_code.setter
    def put_code(self, put_code):
        """Sets the put_code of this EmailV30Rc1.


        :param put_code: The put_code of this EmailV30Rc1.  # noqa: E501
        :type: int
        """

        self._put_code = put_code

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
        if issubclass(EmailV30Rc1, dict):
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
        if not isinstance(other, EmailV30Rc1):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other