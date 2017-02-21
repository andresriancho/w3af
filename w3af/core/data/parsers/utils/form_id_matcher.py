"""
form_id_matcher.py

Copyright 2017 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import re
import json


FORM_ID_FORMAT_ERROR = '''\
The provided form-id JSON is incorrect. Form ids must be JSON objects with the
following structure:

{"action":"/products/.*",
 "inputs": ["comment"],
 "attributes": {"class": "comments-form"},
 "hosted_at_url": "/products/.*"}

Any of the top level object attributes can be missing but no extra top level
attributes are allowed. Also, the types associated with each key needs to match
the example above.

Note that the values for "action" and "hosted_at_url" need to be valid regular
expressions.

Please read the documentation for more details and examples on how to configure
the form-id setting.
'''


class FormIDMatcher(object):
    """
    This class describes the form attributes that the user wants to match.

    In most cases this class is constructed from user-configured json object
    such as:

        {"action":"/products/.*",
         "inputs": ["comment"],
         "method": "get",
         "attributes": {"class": "comments-form"},
         "hosted_at_url": "/products/.*"}

    And then used in a call to FormID.match(...)

    :see: https://github.com/andresriancho/w3af/issues/15161
    """

    ALLOWED_ATTRS = ['action', 'inputs', 'attributes', 'hosted_at_url',
                     'method']

    def __init__(self, action=None, inputs=None, attributes=None,
                 hosted_at_url=None, method=None):
        """
        :param action: Regular expression object matching URL where
                       the form is sent
        :param inputs: A list with the names of the form parameters
        :param attributes: The form tag attributes as seen in the HTML
        :param hosted_at_url: Regular expression object matching URL
                              where the form should
        :param method: The HTTP method used to submit the form
        """
        self.verify_data_types(action, inputs, attributes, hosted_at_url,
                               method)

        self.action = action
        self.inputs = inputs
        self.attributes = attributes
        self.hosted_at_url = hosted_at_url
        self.method = method

    def verify_data_types(self, action, inputs, attributes, hosted_at_url,
                          method):
        """
        Strict attribute type checking to make sure we get what we expect from
        all the callers

        :param action: URL where the form is sent
        :param inputs: A list with the names of the form parameters
        :param attributes: The form tag attributes as seen in the HTML
        :param hosted_at_url: The URL where the form appeared
        :return: True if all attributes match our requirements, otherwise an
                 exception is raised
        """
        if action is not None:
            if not isinstance(action, re._pattern_type):
                raise ValueError(FORM_ID_FORMAT_ERROR)

        if inputs is not None:
            if not isinstance(inputs, list):
                raise ValueError(FORM_ID_FORMAT_ERROR)

            for input_name in inputs:
                if not isinstance(input_name, basestring):
                    raise ValueError(FORM_ID_FORMAT_ERROR)

        if attributes is not None:
            if not isinstance(attributes, dict):
                raise ValueError(FORM_ID_FORMAT_ERROR)

            for k, v in attributes.iteritems():
                if not isinstance(k, basestring):
                    raise ValueError(FORM_ID_FORMAT_ERROR)

                if not isinstance(v, basestring):
                    raise ValueError(FORM_ID_FORMAT_ERROR)

        if hosted_at_url is not None:
            if not isinstance(hosted_at_url, re._pattern_type):
                raise ValueError(FORM_ID_FORMAT_ERROR)

        if method is not None:
            if not isinstance(method, basestring):
                raise ValueError(FORM_ID_FORMAT_ERROR)

        return True

    def to_dict(self):
        """
        :return: This object as a dict which can be easily serialized as json
        """
        data = {}

        for unmodified in ['inputs', 'attributes', 'method']:
            if self.__dict__[unmodified] is not None:
                data[unmodified] = self.__dict__[unmodified]

        if self.action is not None:
            data['action'] = self.action.pattern

        if self.hosted_at_url is not None:
            data['hosted_at_url'] = self.hosted_at_url.pattern

        return data

    @classmethod
    def from_json(cls, json_string):
        """
        This is a "constructor" for the FormID class.

        Users configure form-ids as JSON objects in the configuration, we need to
        parse this here to convert them to FormIDs

        :param json_string: A user provided string which should be in json format
        :return: A FormIDMatcher object
        """
        # For now we just let the exception generated by invalid json raise without
        # any handling
        json_data = json.loads(json_string)

        # Strict input checks are done in __init__ -> verify_data_types
        return cls.from_json_list_data(json_data)

    @classmethod
    def from_json_list_data(cls, json_list_item):
        """
        This is a "constructor" for the FormID class.

        Users configure form-ids as JSON objects in the configuration, we need to
        parse this here to convert them to FormIDs

        :param json_list_item: A user provided python object which we use to build
                               the FormIDMatcher
        :return: A FormIDMatcher object
        """
        # Check the root JSON object format
        if not isinstance(json_list_item, dict):
            raise ValueError(FORM_ID_FORMAT_ERROR)

        action = json_list_item.get('action', None)
        inputs = json_list_item.get('inputs', None)
        attributes = json_list_item.get('attributes', None)
        hosted_at_url = json_list_item.get('hosted_at_url', None)
        method = json_list_item.get('method', None)

        for json_attr in json_list_item:
            if json_attr not in cls.ALLOWED_ATTRS:
                raise ValueError(FORM_ID_FORMAT_ERROR)

        # User configured action and hosted_at_url must be valid regular expressions
        if action is not None:
            try:
                action = re.compile(action)
            except:
                raise ValueError(FORM_ID_FORMAT_ERROR)

        if hosted_at_url is not None:
            try:
                hosted_at_url = re.compile(hosted_at_url)
            except:
                raise ValueError(FORM_ID_FORMAT_ERROR)

        # Strict input checks are done in __init__ -> verify_data_types
        return cls(action, inputs, attributes, hosted_at_url, method)

    def __str__(self):
        return '<FormIDMatcher: %s>' % self.__dict__
