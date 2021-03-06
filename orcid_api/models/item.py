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


class Item(object):
    """
    NOTE: This class is auto generated by the swagger code generator program.
    Do not edit the class manually.
    """
    def __init__(self, put_code=None, item_type=None, item_name=None, external_id=None):
        """
        Item - a model defined in Swagger

        :param dict swaggerTypes: The key is attribute name
                                  and the value is attribute type.
        :param dict attributeMap: The key is attribute name
                                  and the value is json key in definition.
        """
        self.swagger_types = {
            'put_code': 'str',
            'item_type': 'str',
            'item_name': 'str',
            'external_id': 'ExternalID'
        }

        self.attribute_map = {
            'put_code': 'put-code',
            'item_type': 'item-type',
            'item_name': 'item-name',
            'external_id': 'external-id'
        }

        self._put_code = put_code
        self._item_type = item_type
        self._item_name = item_name
        self._external_id = external_id

    @property
    def put_code(self):
        """
        Gets the put_code of this Item.

        :return: The put_code of this Item.
        :rtype: str
        """
        return self._put_code

    @put_code.setter
    def put_code(self, put_code):
        """
        Sets the put_code of this Item.

        :param put_code: The put_code of this Item.
        :type: str
        """

        self._put_code = put_code

    @property
    def item_type(self):
        """
        Gets the item_type of this Item.

        :return: The item_type of this Item.
        :rtype: str
        """
        return self._item_type

    @item_type.setter
    def item_type(self, item_type):
        """
        Sets the item_type of this Item.

        :param item_type: The item_type of this Item.
        :type: str
        """
        allowed_values = ["EDUCATION", "EMPLOYMENT", "FUNDING", "PEER_REVIEW", "WORK"]
        if item_type not in allowed_values:
            raise ValueError(
                "Invalid value for `item_type` ({0}), must be one of {1}"
                .format(item_type, allowed_values)
            )

        self._item_type = item_type

    @property
    def item_name(self):
        """
        Gets the item_name of this Item.

        :return: The item_name of this Item.
        :rtype: str
        """
        return self._item_name

    @item_name.setter
    def item_name(self, item_name):
        """
        Sets the item_name of this Item.

        :param item_name: The item_name of this Item.
        :type: str
        """
        if item_name is None:
            raise ValueError("Invalid value for `item_name`, must not be `None`")

        self._item_name = item_name

    @property
    def external_id(self):
        """
        Gets the external_id of this Item.

        :return: The external_id of this Item.
        :rtype: ExternalID
        """
        return self._external_id

    @external_id.setter
    def external_id(self, external_id):
        """
        Sets the external_id of this Item.

        :param external_id: The external_id of this Item.
        :type: ExternalID
        """
        if external_id is None:
            raise ValueError("Invalid value for `external_id`, must not be `None`")

        self._external_id = external_id

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
        if not isinstance(other, Item):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """
        Returns true if both objects are not equal
        """
        return not self == other
